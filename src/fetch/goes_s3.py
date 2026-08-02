"""Descarga de datos GOES-19 desde AWS S3.

Accede al bucket noaa-goes19 sin credenciales.
Descarga bandas L1b individuales y productos L2 (MCMIPF, FDCF).
"""

import logging
import os
import threading
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import s3fs
import xarray as xr

from src.config import (
    CACHE_DIR,
    GOES_BUCKET,
    PRODUCTS,
    RAW_DIR,
    VOLCANIC_BANDS,
)
from src.fetch.granule_select import get_s3, nearest_granule_key

logger = logging.getLogger(__name__)

# Filesystem S3 sin credenciales
_fs = None


def _get_fs() -> s3fs.S3FileSystem:
    """Obtener filesystem S3 (singleton).

    Delega en `granule_select.get_s3`, que fija `listings_expiry_time`: sin eso el
    `DirCache` de s3fs NUNCA expira y el listado de la hora en curso queda congelado
    para todo el proceso — en el deploy de larga vida, el "scan más reciente" podía
    quedar hasta ~1 h atrasado presentándose como vigente. (audit ago-2026)
    """
    global _fs
    if _fs is None:
        _fs = get_s3()
    return _fs


# Reintentos de S3: la conexión a noaa-goes19 se cae de forma INTERMITENTE
# (EndpointConnectionError, read timeout) al bajar/listar muchos objetos seguidos
# — sin retry, un corte transitorio tumbaba una descarga NRT o un barrido entero
# (mismo patrón que el fetcher GFS-archive). FileNotFoundError NO se reintenta: es
# "el objeto no existe", no un fallo de red.
_S3_RETRIES = 4


def _retry_s3(fn, *args, what: str = "", **kwargs):
    """Ejecutar una operación S3 reintentando fallos TRANSITORIOS de red.

    Propaga ``FileNotFoundError`` de inmediato (no es transitorio). Tras agotar los
    reintentos, relanza la última excepción. Función utilitaria (testeable con un
    ``fn`` falso que falla N veces).
    """
    last = None
    for attempt in range(_S3_RETRIES):
        try:
            return fn(*args, **kwargs)
        except FileNotFoundError:
            raise
        except Exception as e:
            last = e
            logger.warning("S3 %s intento %d/%d: %s", what or getattr(fn, "__name__", "op"),
                           attempt + 1, _S3_RETRIES, e)
    raise last


# Locks por-archivo para descarga ATÓMICA. Antes download_band/mcmip/fdc hacían
# fs.get() directo sobre el path final (s3fs escribe in-place, sin tmp+rename) y
# luego use_cache lo daba por válido por el solo hecho de existir. Con descargas
# PARALELAS del mismo scan (grid de 4 zonas, hilo productor, hires_pipeline) dos
# hilos escribían el MISMO archivo a la vez -> NetCDF corrupto o medio escrito
# tomado como cache. Ahora: lock por filename + download a tmp único + os.replace
# atómico (solo si terminó OK). (fix audit jun 2026)
_DL_LOCKS: dict[str, threading.Lock] = {}
_DL_LOCKS_GUARD = threading.Lock()


def _lock_for(name: str) -> threading.Lock:
    with _DL_LOCKS_GUARD:
        lk = _DL_LOCKS.get(name)
        if lk is None:
            lk = threading.Lock()
            _DL_LOCKS[name] = lk
        return lk


def _download_cached(remote_path: str, use_cache: bool = True) -> Path:
    """Descarga atómica y thread-safe de un objeto S3 a RAW_DIR.

    Devuelve el Path local. Lock por filename + tmp+os.replace -> sin corrupción
    con descargas concurrentes del mismo archivo.
    """
    filename = remote_path.split("/")[-1]
    local_path = RAW_DIR / filename
    if use_cache and local_path.exists():
        return local_path
    with _lock_for(filename):
        if use_cache and local_path.exists():
            return local_path  # otro hilo la bajó mientras esperábamos
        RAW_DIR.mkdir(parents=True, exist_ok=True)
        tmp = local_path.with_name(f"{filename}.part-{uuid.uuid4().hex[:8]}")
        try:
            # Reintento en la descarga: un corte transitorio a mitad de un scan no
            # debe abortar (la .get reescribe el tmp; el os.replace atómico solo
            # ocurre si terminó OK). FileNotFoundError (no existe) no se reintenta.
            _retry_s3(_get_fs().get, remote_path, str(tmp), what=f"get {filename}")
            os.replace(str(tmp), str(local_path))
        finally:
            try:
                if tmp.exists():
                    tmp.unlink()
            except Exception:
                pass
    return local_path


def _time_to_s3_path(product: str, dt: datetime) -> str:
    """Convertir datetime a ruta S3 GOES."""
    doy = dt.timetuple().tm_yday
    return f"{GOES_BUCKET}/{product}/{dt.year}/{doy:03d}/{dt.hour:02d}/"


def list_files(product: str, dt: datetime) -> list[str]:
    """Listar archivos disponibles para un producto y hora."""
    fs = _get_fs()
    path = _time_to_s3_path(product, dt)
    try:
        return sorted(_retry_s3(fs.ls, path, what=f"ls {path}"))
    except FileNotFoundError:
        logger.warning("No files found at %s", path)
        return []


def list_band_files(dt: datetime, band: int) -> list[str]:
    """Listar archivos L1b para una banda específica."""
    files = list_files(PRODUCTS["L1b_rad"], dt)
    band_str = f"C{band:02d}"
    return [f for f in files if band_str in f.split("/")[-1]]


def download_band(dt: datetime, band: int, use_cache: bool = True) -> Path | None:
    """Descargar una banda L1b GOES para una hora específica.

    Busca el archivo más cercano a la hora solicitada.
    Retorna el path local del archivo descargado.
    """
    files = list_band_files(dt, band)
    if not files:
        # Intentar hora anterior
        files = list_band_files(dt - timedelta(hours=1), band)
    if not files:
        logger.error("No band %d files near %s", band, dt.isoformat())
        return None

    # Tomar el último archivo de la hora (más reciente)
    remote_path = files[-1]
    return _download_cached(remote_path, use_cache)


def _scan_start(remote_path: str) -> datetime | None:
    """Inicio de scan (UTC) desde el nombre L1b: OR_..._sYYYYDDDHHMMSSs_..."""
    name = remote_path.split("/")[-1]
    try:
        i = name.index("_s") + 2
        ts = name[i:i + 13]  # YYYYDDDHHMMSSs
        return datetime(int(ts[:4]), 1, 1, tzinfo=timezone.utc) + timedelta(
            days=int(ts[4:7]) - 1, hours=int(ts[7:9]),
            minutes=int(ts[9:11]), seconds=int(ts[11:13]))
    except Exception:
        return None


def download_band_at(dt: datetime, band: int, use_cache: bool = True) -> Path | None:
    """Descargar la banda del scan MÁS CERCANO a `dt` (no el último de la hora).

    `download_band` toma `files[-1]` (el último de la hora) — correcto para "lo
    más reciente" pero NO para backfill de un timestamp puntual: todos los scans
    de la misma hora darían el mismo archivo. Acá elegimos el scan cuyo
    `_sYYYYDDDHHMMSS` está más cerca de `dt` (RadF escanea cada 10 min).
    """
    # Unión de [dt-1h, dt, dt+1h]: el scan más cercano al borde de hora puede
    # caer en la hora siguiente (HH:56 → (HH+1):00), no solo en la previa.
    best = nearest_granule_key(lambda h: list_band_files(h, band), _scan_start, dt)
    if best is None:
        logger.error("No band %d files near %s", band, dt.isoformat())
        return None
    return _download_cached(best, use_cache)


def download_volcanic_bands(dt: datetime) -> dict[int, Path]:
    """Descargar todas las bandas volcánicas para una hora.

    Retorna dict {band_number: local_path}.
    """
    results = {}
    for band in VOLCANIC_BANDS:
        path = download_band(dt, band)
        if path:
            results[band] = path
    return results


def download_mcmip(dt: datetime, use_cache: bool = True) -> Path | None:
    """Descargar producto MCMIPF (multi-banda, incluye GeoColor)."""
    files = list_files(PRODUCTS["mcmip"], dt)
    if not files:
        return None
    return _download_cached(files[-1], use_cache)


def download_fdc(dt: datetime, use_cache: bool = True) -> Path | None:
    """Descargar producto FDCF (Fire/Hot Spot Detection)."""
    files = list_files(PRODUCTS["fdc"], dt)
    if not files:
        return None
    return _download_cached(files[-1], use_cache)


def open_band(path: Path) -> xr.Dataset:
    """Abrir un archivo L1b NetCDF como xarray Dataset."""
    return xr.open_dataset(path, engine="h5netcdf")


def get_latest_time() -> datetime | None:
    """Obtener el timestamp más reciente disponible en S3."""
    fs = _get_fs()
    now = datetime.now(timezone.utc)
    product = PRODUCTS["L1b_rad"]

    # Intentar las últimas 3 horas
    for hours_ago in range(3):
        dt = now - timedelta(hours=hours_ago)
        path = _time_to_s3_path(product, dt)
        try:
            files = fs.ls(path)
            if files:
                # Extraer timestamp del nombre del archivo más reciente
                latest = sorted(files)[-1]
                fname = latest.split("/")[-1]
                # Formato: OR_..._sYYYYDDDHHMMSSx_...
                s_idx = fname.index("_s") + 2
                ts_str = fname[s_idx : s_idx + 11]  # YYYYDDDHHMMSS
                year = int(ts_str[:4])
                doy = int(ts_str[4:7])
                hour = int(ts_str[7:9])
                minute = int(ts_str[9:11])
                dt_parsed = datetime(year, 1, 1, hour, minute, tzinfo=timezone.utc) + timedelta(days=doy - 1)
                return dt_parsed
        except FileNotFoundError:
            continue
    return None
