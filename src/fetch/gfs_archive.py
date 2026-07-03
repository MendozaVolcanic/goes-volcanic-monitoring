"""Perfil GFS **archivado** (T(z) y viento) desde GRIB2 por byte-range.

Por qué existe (validación histórica): Open-Meteo devuelve ``null`` en los niveles
de presión pasados, así que no sirve para validar eventos viejos (Láscar 27-jun con
el viento correcto, Calbuco 2015). El análisis GFS SÍ está archivado indefinidamente
en el bucket público ``noaa-gfs-bdp-pds`` (verificado desde ``gfs.20210101``), pero
en **GRIB2**: cada gránulo pesa ~508 MB.

Cómo evitamos bajar 508 MB: cada archivo GRIB2 trae un ``.idx`` de texto (~0.2 KB)
que lista, por registro, el **offset de byte** donde empieza:

    num:offset:d=YYYYMMDDHH:VAR:LEVEL:anl:

El fin de un registro es ``(offset del siguiente − 1)``. Con eso pedimos por
**HTTP Range** solo los registros que necesitamos (TMP/HGT/UGRD/VGRD en los niveles
de presión de interés, ~1 MB c/u) → ~40–60 MB en vez de 508. Los concatenamos (los
mensajes GRIB2 son auto-delimitados) y los decodifica ``eccodes`` en una pasada.

**Dependencia opcional:** el decode necesita ``eccodes`` (binario GRIB2). NO va en
el deploy de la app — el dashboard y los crons no importan este módulo. Se instala
solo en la máquina de validación con ``pip install -e ".[archive]"``. El import de
``eccodes`` está DENTRO de la función de red (guardado) para que importar este
módulo no falle sin él.

Salida: **misma forma** que ``src/fetch/gfs_profile.py`` (``fetch_gfs_profile`` y
``fetch_gfs_wind_profile``) → drop-in para ``altitudes_from_bt`` / el árbitro de
viento en los scripts de validación histórica.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

# Reusa la definición de niveles y la tropopausa (punto frío) del perfil NRT, para
# que el perfil archivado sea comparable 1:1 con el de Open-Meteo.
from src.fetch.gfs_profile import GFS_LEVELS_HPA, _tropopause

logger = logging.getLogger(__name__)

S3_BUCKET = "noaa-gfs-bdp-pds"
_EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)
_CYCLE_S = 6 * 3600           # GFS corre cada 6 h (00/06/12/18Z)


# ── Helpers puros (sin red, sin eccodes) ────────────────────────────────────

def _parse_idx(text: str) -> list:
    """Parsear el ``.idx`` de un GRIB2 GFS → lista de registros con rango de bytes.

    Cada registro: ``{"num", "offset"/"start", "end", "date", "var", "level"}``.
    ``end`` = ``(offset del siguiente − 1)``; el ÚLTIMO registro queda con
    ``end=None`` (el fetcher lo resuelve con el tamaño del archivo). Función PURA.
    """
    recs = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split(":")
        if len(parts) < 5:
            continue
        recs.append({
            "num": int(parts[0]),
            "start": int(parts[1]),
            "date": parts[2][2:] if parts[2].startswith("d=") else parts[2],
            "var": parts[3],
            "level": parts[4],
            "end": None,
        })
    for i in range(len(recs) - 1):
        recs[i]["end"] = recs[i + 1]["start"] - 1
    return recs


def _level_to_hpa(level: str) -> Optional[float]:
    """``"500 mb"`` → 500.0; niveles no isobáricos (surface, msl, m AGL) → None."""
    s = level.strip()
    if not s.endswith(" mb"):
        return None
    try:
        return float(s[:-3])
    except ValueError:
        return None


def _cycle_for(dt: datetime) -> tuple:
    """Ciclo GFS 6-horario (00/06/12/18Z) más cercano a ``dt``.

    Devuelve ``(yyyymmdd, hh, cycle_dt, gap_min)``. Redondea al múltiplo de 6 h más
    próximo — 23:00 cae en 00Z del día siguiente, no en 18Z. Función PURA.
    """
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    secs = (dt - _EPOCH).total_seconds()
    cdt = _EPOCH + timedelta(seconds=round(secs / _CYCLE_S) * _CYCLE_S)
    gap = abs((dt - cdt).total_seconds()) / 60.0
    return cdt.strftime("%Y%m%d"), cdt.strftime("%H"), cdt, gap


def _grid_index(lat0: float, lon0: float, dx: float, dy: float, ni: int,
                tlat: float, tlon: float) -> int:
    """Índice PLANO del punto (tlat,tlon) en la grilla regular lat/lon del mensaje.

    GFS escanea desde (lat0=90N, lon0=0E) con lat decreciente y lon creciente.
    ``lon`` se normaliza a [0,360). Función PURA (para testear el mapeo sin decode).
    """
    tlon %= 360.0
    lon0 %= 360.0
    j = round((lat0 - tlat) / dy)
    i = round(((tlon - lon0) % 360.0) / dx) % ni
    return int(j * ni + i)


# ── Red + eccodes (aislado; import guardado) ────────────────────────────────

def _load_idx(s3, cdt: datetime):
    """(records, grib_key, size) del gránulo f000 del ciclo ``cdt``, o None."""
    y, h = cdt.strftime("%Y%m%d"), cdt.strftime("%H")
    base = f"{S3_BUCKET}/gfs.{y}/{h}/atmos"
    grib = f"{base}/gfs.t{h}z.pgrb2.0p25.f000"
    try:
        txt = s3.cat(grib + ".idx").decode()
        size = int(s3.info(grib)["size"])
    except Exception:
        return None
    return _parse_idx(txt), grib, size


def _read_range(s3, grib: str, start: int, end: int, retries: int = 4) -> bytes:
    """Un byte-range ``[start, end]`` (inclusive) como GET independiente, con
    reintento. Cada registro va por su propia request (no una conexión sostenida):
    un corte transitorio de red — habitual bajando decenas de MB de S3 — reintenta
    ese registro en vez de tumbar todo el perfil.
    """
    last = None
    for attempt in range(retries):
        try:
            return s3.cat_file(grib, start=start, end=end + 1)  # end exclusivo en fsspec
        except Exception as e:            # transitorio: EndpointConnectionError, timeout
            last = e
            logger.warning("GFS archive range [%d,%d] intento %d: %s",
                           start, end, attempt + 1, e)
    raise last


def _collect_raw(s3, grib: str, size: int, recs: list, needed: list):
    """Byte-range de cada (var, level) de ``needed`` presente en ``recs``.

    Devuelve ``(got, raw)``: ``got`` = lista de claves efectivamente bajadas (en
    orden), ``raw`` = sus mensajes GRIB2 concatenados. Cada registro es un GET
    independiente con reintento (robusto a caídas transitorias de red).
    """
    idx = {(r["var"], r["level"]): r for r in recs}
    got, raw = [], bytearray()
    for key in needed:
        r = idx.get(key)
        if r is None:
            continue
        end = r["end"] if r["end"] is not None else size - 1
        raw += _read_range(s3, grib, r["start"], end)
        got.append(key)
    return got, bytes(raw)


def _decode_values_at_point(raw: bytes, tlat: float, tlon: float) -> list:
    """Valor en (tlat,tlon) de cada mensaje GRIB2 de ``raw``, EN ORDEN.

    Escribe los mensajes a un archivo temporal y los itera con eccodes (una pasada).
    El i-ésimo valor corresponde al i-ésimo mensaje = i-ésima clave de ``got``.
    """
    import os
    import tempfile
    import uuid

    import eccodes

    tmpf = os.path.join(tempfile.gettempdir(), f"gfsarch_{uuid.uuid4().hex}.grib2")
    with open(tmpf, "wb") as fh:
        fh.write(raw)
    out = []
    try:
        with open(tmpf, "rb") as fh:
            while True:
                gid = eccodes.codes_grib_new_from_file(fh)
                if gid is None:
                    break
                try:
                    ni = eccodes.codes_get(gid, "Ni")
                    lat0 = eccodes.codes_get(gid, "latitudeOfFirstGridPointInDegrees")
                    lon0 = eccodes.codes_get(gid, "longitudeOfFirstGridPointInDegrees")
                    dx = eccodes.codes_get(gid, "iDirectionIncrementInDegrees")
                    dy = eccodes.codes_get(gid, "jDirectionIncrementInDegrees")
                    vals = eccodes.codes_get_values(gid)
                    out.append(float(vals[_grid_index(lat0, lon0, dx, dy, ni,
                                                       tlat, tlon)]))
                finally:
                    eccodes.codes_release(gid)
    finally:
        try:
            os.remove(tmpf)
        except OSError:
            pass       # eccodes puede retener el archivo un instante en Windows
    return out


def _resolve(s3, dt: datetime):
    """Cargar el idx del ciclo más cercano a ``dt``; si falta, el ciclo anterior.

    Devuelve ``(recs, grib, size, cycle_dt, gap_min)`` o None.
    """
    _, _, cdt, gap = _cycle_for(dt)
    got = _load_idx(s3, cdt)
    if got is not None:
        recs, grib, size = got
        return recs, grib, size, cdt, gap
    prev = cdt - timedelta(seconds=_CYCLE_S)
    got = _load_idx(s3, prev)
    if got is not None:
        recs, grib, size = got
        return recs, grib, size, prev, abs((dt - prev).total_seconds()) / 60.0
    return None


def fetch_gfs_profile_archive(
    lat: float, lon: float, dt: Optional[datetime] = None
) -> Optional[dict]:
    """Perfil T(z) del GFS ARCHIVADO en (lat,lon) al ciclo más cercano a ``dt``.

    Salida idéntica a ``fetch_gfs_profile``: ``{"levels": [{p_hPa, z_m, T_K}...],
    "tropopause", "skin_temp_K", "lat", "lon", "valid_time", "time_gap_min",
    "source"}``. None si faltan deps, no hay gránulo o quedan <3 niveles.
    """
    try:
        import s3fs
    except ImportError as e:
        logger.error("s3fs no disponible: %s", e)
        return None
    if dt is None:
        dt = datetime.now(timezone.utc)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    s3 = s3fs.S3FileSystem(anon=True)
    res = _resolve(s3, dt)
    if res is None:
        logger.warning("GFS archive: sin gránulo para %s", dt.isoformat())
        return None
    recs, grib, size, cdt, gap = res

    needed = []
    for p in GFS_LEVELS_HPA:
        needed += [("TMP", f"{p} mb"), ("HGT", f"{p} mb")]
    needed.append(("TMP", "surface"))     # skin-T (fallback Wen-Rose), best-effort
    try:
        got, raw = _collect_raw(s3, grib, size, recs, needed)
        vals = _decode_values_at_point(raw, lat, lon)
    except Exception as e:
        logger.exception("GFS archive decode T(z): %s", e)
        return None
    vmap = dict(zip(got, vals))

    levels = []
    for p in GFS_LEVELS_HPA:
        t = vmap.get(("TMP", f"{p} mb"))
        z = vmap.get(("HGT", f"{p} mb"))
        if t is None or z is None:
            continue
        levels.append({"p_hPa": p, "z_m": float(z), "T_K": float(t)})
    levels.sort(key=lambda d: d["z_m"])
    if len(levels) < 3:
        return None

    skin = vmap.get(("TMP", "surface"))
    return {
        "levels": levels,
        "tropopause": _tropopause(levels),
        "skin_temp_K": float(skin) if skin is not None else None,
        "lat": lat, "lon": lon,
        "valid_time": cdt.strftime("%Y-%m-%dT%H:%M"),
        "time_gap_min": round(gap, 1),
        "source": "GFS archive (noaa-gfs-bdp-pds, f000 analysis, GRIB2 byte-range)",
    }


def fetch_gfs_wind_profile_archive(
    lat: float, lon: float, dt: Optional[datetime] = None
) -> Optional[dict]:
    """Perfil de viento (u,v) del GFS ARCHIVADO. Salida idéntica a
    ``fetch_gfs_wind_profile``: ``{"levels": [{p_hPa, z_m, u_ms, v_ms}...], "lat",
    "lon", "valid_time", "time_gap_min", "source"}``. None si faltan deps/datos.
    """
    try:
        import s3fs
    except ImportError as e:
        logger.error("s3fs no disponible: %s", e)
        return None
    if dt is None:
        dt = datetime.now(timezone.utc)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    s3 = s3fs.S3FileSystem(anon=True)
    res = _resolve(s3, dt)
    if res is None:
        logger.warning("GFS archive viento: sin gránulo para %s", dt.isoformat())
        return None
    recs, grib, size, cdt, gap = res

    needed = []
    for p in GFS_LEVELS_HPA:
        needed += [("UGRD", f"{p} mb"), ("VGRD", f"{p} mb"), ("HGT", f"{p} mb")]
    try:
        got, raw = _collect_raw(s3, grib, size, recs, needed)
        vals = _decode_values_at_point(raw, lat, lon)
    except Exception as e:
        logger.exception("GFS archive decode viento: %s", e)
        return None
    vmap = dict(zip(got, vals))

    levels = []
    for p in GFS_LEVELS_HPA:
        u = vmap.get(("UGRD", f"{p} mb"))
        v = vmap.get(("VGRD", f"{p} mb"))
        z = vmap.get(("HGT", f"{p} mb"))
        if u is None or v is None or z is None:
            continue
        levels.append({"p_hPa": p, "z_m": float(z),
                       "u_ms": float(u), "v_ms": float(v)})
    levels.sort(key=lambda d: d["z_m"])
    if len(levels) < 3:
        return None

    return {
        "levels": levels, "lat": lat, "lon": lon,
        "valid_time": cdt.strftime("%Y-%m-%dT%H:%M"),
        "time_gap_min": round(gap, 1),
        "source": "GFS archive wind (noaa-gfs-bdp-pds, f000 analysis, GRIB2 byte-range)",
    }
