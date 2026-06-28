"""Cliente para producto NOAA L2 ACHA2KMF (ABI Cloud Top Height, 2 km full disk).

ACHA = *ABI Cloud Height Algorithm* (Heidinger, optimal estimation). NOAA lo
publica pre-procesado en el mismo bucket ``noaa-goes19`` que ya usamos. Da la
altura del tope de **cualquier** nube (var ``HT``, en metros). Por sí solo NO
distingue ceniza de nube meteorológica — esa parte la aporta NUESTRA detección
de ceniza tri-espectral (``src.process.ash_detection``). Al intersectar HT con
esa máscara aislamos el **tope de la pluma volcánica**.

Por qué funciona el atajo (geología → pipeline):
- El VOLCAT de SSEC (Pavolonis 2013) no "mide" la altura: retrieva la
  temperatura efectiva del tope (Teff) y la convierte a km con un perfil NWP.
  ACHA hace exactamente ese retrieval de altura de tope de nube, pero ya
  resuelto y servido por NOAA. Reutilizarlo nos da una **altura defendible** a
  ~13 min de latencia (vs 30–50 de SSEC), con CERO dependencias nuevas.
- Es un producto **INDICATIVO**: ACHA es altura de nube genérica, no ceniza-
  específica; sobre plumas semi-transparentes o con nube meteo debajo sesga
  igual que cualquier método de matching IR. No reemplaza al VOLCAT cuantitativo.

Variables clave del NetCDF (``ABI-L2-ACHA2KMF``):
- ``HT``  (5424×5424 float, m): altura del tope de nube, 0 – ~17.6 km. Fill→NaN.
- ``DQF`` (5424×5424 uint8): flag de calidad del retrieval
    - 0 = good_quality, 1 = marginal_quality, 2 = retrieval_attempted,
      3 = bad_quality, 4 = opaque_retrieval.
  Para el **tope de una pluma densa**, ``4`` (opaque) es un retrieval FIABLE
  (la nube opaca tiene emisividad ≈ 1, que es el régimen donde ACHA mejor anda),
  así que lo MANTENEMOS. Descartamos 2 (no convergió del todo) y 3 (malo).

Grilla: GOES-R ABI fixed grid (geos), ``goes_imager_projection``
(lon_origin=−75.0, H=35786023.0) — **idéntica** a ``ABI-L1b-RadF`` 2 km y a
``ABI-L2-FDCF``. Por eso este módulo clona el patrón fetch+georef de
``src/fetch/goes_fdcf.py``, y la ventana de índices que devuelve sirve para
recortar las bandas de ceniza al MISMO encuadre, pixel a pixel.

Cadencia: 10 min. Latencia: ~13 min (timestamp ``c`` = creación del archivo).
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

import numpy as np

# Constantes físicas canónicas desde src/config (con fallback, mismo patrón que
# goes_fdcf.py).
try:
    from src.config import GOES19_PERSPECTIVE_POINT_HEIGHT as _H_DEFAULT
    from src.config import GOES19_SAT_LON as _SAT_LON_DEFAULT
except Exception:
    _SAT_LON_DEFAULT = -75.0
    _H_DEFAULT = 35786023.0

logger = logging.getLogger(__name__)

S3_BUCKET = "noaa-goes19"
S3_PRODUCT = "ABI-L2-ACHA2KMF"

# DQF que CONSERVAMOS (ver docstring): good + marginal + opaque. Se descartan
# 2 (attempted) y 3 (bad). Frozenset para que sea hasheable y default seguro.
DQF_KEEP_DEFAULT = frozenset({0, 1, 4})

# Techo físico de altura de tope: tropopausa + overshoot generoso. Por encima
# de esto el valor es ruido del retrieval → se descarta. (la tropopausa tropical
# ronda 16–17 km; dejamos margen para overshooting tops fuertes.)
HT_MAX_PLAUSIBLE_M = 20000.0


def _apply_quality(ht, dqf, keep_dqf=DQF_KEEP_DEFAULT, ht_max: float = HT_MAX_PLAUSIBLE_M):
    """Aplicar el filtro de calidad DQF + rango físico a la altura ACHA.

    Función PURA (testeable sin red) — es el contrato científico del fetcher:
    se conservan solo los DQF en ``keep_dqf`` (default good/marginal/opaque) y
    se descartan alturas < 0 o > ``ht_max`` (ruido del retrieval). Todo lo
    filtrado queda NaN.
    """
    ht = np.asarray(ht, dtype="float64")
    keep = np.isin(dqf, list(keep_dqf))
    height = np.where(keep, ht, np.nan)
    bad = (height < 0.0) | (height > ht_max)
    return np.where(bad, np.nan, height)


def _parse_scan_time(s3_path: str) -> Optional[datetime]:
    """Extraer datetime UTC del inicio de scan (``_sYYYYDDDHHMMSS``) del nombre
    NOAA. Idéntico a goes_fdcf._parse_scan_time (mismo formato de archivo)."""
    try:
        name = s3_path.split("/")[-1]
        token = [t for t in name.split("_") if t.startswith("s") and len(t) >= 14][0]
        yyyy = int(token[1:5])
        doy = int(token[5:8])
        hh = int(token[8:10])
        mm = int(token[10:12])
        ss = int(token[12:14])
        base = datetime(yyyy, 1, 1, hh, mm, ss, tzinfo=timezone.utc)
        return base + timedelta(days=doy - 1)
    except Exception as e:
        logger.warning("No pude parsear timestamp de %s: %s", s3_path, e)
        return None


def _proj(sat_lon: float, H: float):
    """pyproj Proj geos del ABI fixed grid (sweep='x'), mismo que goes_fdcf."""
    from pyproj import Proj
    return Proj(proj="geos", lon_0=sat_lon, h=H, ellps="GRS80", sweep="x")


def _geos_index_bbox(
    x: np.ndarray,
    y: np.ndarray,
    bounds: dict,
    sat_lon: float = _SAT_LON_DEFAULT,
    H: float = _H_DEFAULT,
    margin_px: int = 2,
) -> Optional[tuple[int, int, int, int]]:
    """Índices ``(y0, y1, x0, x1)`` (y1/x1 exclusivos) que encierran el bbox
    lat/lon sobre la grilla ABI fixed-grid.

    Proyecta hacia adelante (lat/lon → ángulo de scan en radianes) una malla
    densa del borde del bbox — densa porque en geos los meridianos/paralelos se
    curvan y las 4 esquinas no bastan — y busca el rango de índices en los
    arrays 1-D ``x``/``y``. Funciona con cualquier orden de los arrays (x crece,
    y decrece) porque filtra por VALOR, no por posición.

    Devuelve ``None`` si el bbox cae fuera del disco (sin píxeles válidos). Este
    recorte por índices evita construir el meshgrid lat/lon de 5424×5424 entero
    (que ``src.process.geo.get_lat_lon`` sí hace) — barato y de baja memoria.
    """
    p = _proj(sat_lon, H)
    n = 25
    lons = np.linspace(bounds["lon_min"], bounds["lon_max"], n)
    lats = np.linspace(bounds["lat_min"], bounds["lat_max"], n)
    LON, LAT = np.meshgrid(lons, lats)
    xm, ym = p(LON.ravel(), LAT.ravel())          # → metros en el plano geos
    xm = np.asarray(xm, dtype="float64")
    ym = np.asarray(ym, dtype="float64")
    # pyproj marca off-disk con valores enormes (~1e30) o inf.
    good = np.isfinite(xm) & np.isfinite(ym) & (np.abs(xm) < 1e8) & (np.abs(ym) < 1e8)
    if not good.any():
        return None
    xr_ = xm[good] / H                            # metros → radianes (x_m = x_rad·H)
    yr_ = ym[good] / H
    xsel = np.where((x >= xr_.min()) & (x <= xr_.max()))[0]
    ysel = np.where((y >= yr_.min()) & (y <= yr_.max()))[0]
    if xsel.size == 0 or ysel.size == 0:
        return None
    x0 = max(0, int(xsel.min()) - margin_px)
    x1 = min(len(x), int(xsel.max()) + 1 + margin_px)
    y0 = max(0, int(ysel.min()) - margin_px)
    y1 = min(len(y), int(ysel.max()) + 1 + margin_px)
    return y0, y1, x0, x1


def _window_latlon(
    xw: np.ndarray,
    yw: np.ndarray,
    sat_lon: float = _SAT_LON_DEFAULT,
    H: float = _H_DEFAULT,
) -> tuple[np.ndarray, np.ndarray]:
    """Reproyecta una ventana (arrays 1-D x/y en radianes) a lat/lon 2D.

    Solo la ventana recortada → meshgrid chico, no el disco completo. Píxeles
    fuera del disco quedan NaN.
    """
    p = _proj(sat_lon, H)
    XX, YY = np.meshgrid(xw, yw)
    lon, lat = p(XX * H, YY * H, inverse=True)
    lat = np.asarray(lat, dtype="float64")
    lon = np.asarray(lon, dtype="float64")
    lat[~np.isfinite(lat)] = np.nan
    lon[~np.isfinite(lon)] = np.nan
    return lat, lon


def _list_files_at_hour(s3, dt: datetime) -> list[str]:
    """Listar gránulos ACHA2KMF disponibles para una hora UTC específica."""
    prefix = (
        f"{S3_BUCKET}/{S3_PRODUCT}/"
        f"{dt.year}/{dt.timetuple().tm_yday:03d}/{dt.hour:02d}/"
    )
    try:
        return sorted(s3.ls(prefix))
    except FileNotFoundError:
        return []
    except Exception as e:
        logger.warning("listing %s: %s", prefix, e)
        return []


def fetch_acha_height_at(
    dt: datetime,
    bounds: dict,
    keep_dqf=DQF_KEEP_DEFAULT,
) -> Optional[dict]:
    """Bajar el gránulo ACHA2KMF más cercano a ``dt`` y devolver la altura del
    tope de nube recortada a ``bounds`` (bbox lat/lon del volcán).

    Args:
        dt:       datetime UTC del scan deseado (NRT: pasar ``now``).
        bounds:   dict lat_min/lat_max/lon_min/lon_max.
        keep_dqf: conjunto de valores DQF a conservar. Default {0,1,4}
                  (good + marginal + opaque). Los demás → HT = NaN.

    Returns:
        dict con:
          - ``height_m`` (H×W float): altura del tope en m, NaN donde DQF fuera
            de ``keep_dqf``, fill, o fuera de rango físico.
          - ``dqf`` (H×W): DQF recortado (para contexto).
          - ``lat``, ``lon`` (H×W): georef de la ventana.
          - ``bounds``: el bbox pedido.
          - ``window`` (y0,y1,x0,x1): índices del recorte sobre el full disk —
            sirven para recortar las bandas L1b 2 km al MISMO encuadre (grilla
            idéntica).
          - ``scan_dt``: datetime real del gránulo elegido.
          - ``sat_lon``, ``H``: parámetros de proyección leídos del archivo.
          - ``product``, ``source_key``.
        ``None`` si no hay gránulo accesible o el bbox cae fuera del disco.
    """
    try:
        import s3fs
        import xarray as xr
    except ImportError as e:
        logger.error("s3fs/xarray no disponible: %s", e)
        return None

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    s3 = s3fs.S3FileSystem(anon=True)
    keys = _list_files_at_hour(s3, dt)
    if not keys:
        keys = _list_files_at_hour(s3, dt - timedelta(hours=1))
    if not keys:
        logger.warning("ACHA: sin gránulos en %s ni hora previa", dt.isoformat())
        return None

    def _delta(k: str) -> float:
        ts = _parse_scan_time(k)
        return float("inf") if ts is None else abs((ts - dt).total_seconds())

    chosen = min(keys, key=_delta)
    logger.info("ACHA: dt=%s, gránulo: %s", dt.isoformat(), chosen.split("/")[-1])

    try:
        with s3.open(chosen, "rb") as f:
            ds = xr.open_dataset(f, engine="h5netcdf")
            proj = ds["goes_imager_projection"].attrs
            sat_lon = float(proj.get("longitude_of_projection_origin", _SAT_LON_DEFAULT))
            H = float(proj.get("perspective_point_height", _H_DEFAULT))
            x = ds["x"].values
            y = ds["y"].values
            win = _geos_index_bbox(x, y, bounds, sat_lon=sat_lon, H=H)
            if win is None:
                logger.warning("ACHA: bbox %s fuera del disco", bounds)
                return None
            y0, y1, x0, x1 = win
            # Slice LAZY antes de .values → solo lee la ventana del S3.
            ht = ds["HT"].isel(y=slice(y0, y1), x=slice(x0, x1)).values.astype("float64")
            dqf = ds["DQF"].isel(y=slice(y0, y1), x=slice(x0, x1)).values
            xw = x[x0:x1]
            yw = y[y0:y1]
    except Exception as e:
        logger.exception("Error leyendo ACHA %s: %s", chosen, e)
        return None

    scan_dt = _parse_scan_time(chosen)
    lat, lon = _window_latlon(xw, yw, sat_lon=sat_lon, H=H)

    # Filtro de calidad + rango físico → HT defendible (helper puro, testeable).
    height = _apply_quality(ht, dqf, keep_dqf)

    return {
        "height_m": height,
        "dqf": dqf,
        "lat": lat,
        "lon": lon,
        "bounds": bounds,
        "window": (y0, y1, x0, x1),
        "scan_dt": scan_dt,
        "sat_lon": sat_lon,
        "H": H,
        "product": S3_PRODUCT,
        "source_key": chosen,
    }


def fetch_latest_acha_height(bounds: dict, keep_dqf=DQF_KEEP_DEFAULT) -> Optional[dict]:
    """Atajo NRT: la altura ACHA del gránulo más reciente sobre ``bounds``."""
    return fetch_acha_height_at(datetime.now(timezone.utc), bounds, keep_dqf=keep_dqf)
