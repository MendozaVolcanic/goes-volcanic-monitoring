"""Descarga de datos GOES-19 desde AWS S3.

Accede al bucket noaa-goes19 sin credenciales.
Descarga bandas L1b individuales y productos L2 (MCMIPF, FDCF).
"""

import logging
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

logger = logging.getLogger(__name__)

# Filesystem S3 sin credenciales
_fs = None


def _get_fs() -> s3fs.S3FileSystem:
    """Obtener filesystem S3 (singleton)."""
    global _fs
    if _fs is None:
        _fs = s3fs.S3FileSystem(anon=True)
    return _fs


def _time_to_s3_path(product: str, dt: datetime) -> str:
    """Convertir datetime a ruta S3 GOES."""
    doy = dt.timetuple().tm_yday
    return f"{GOES_BUCKET}/{product}/{dt.year}/{doy:03d}/{dt.hour:02d}/"


def list_files(product: str, dt: datetime) -> list[str]:
    """Listar archivos disponibles para un producto y hora."""
    fs = _get_fs()
    path = _time_to_s3_path(product, dt)
    try:
        return sorted(fs.ls(path))
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
    filename = remote_path.split("/")[-1]

    local_path = RAW_DIR / filename
    if use_cache and local_path.exists():
        logger.debug("Cache hit: %s", filename)
        return local_path

    logger.info("Downloading band %d: %s", band, filename)
    fs = _get_fs()
    fs.get(remote_path, str(local_path))
    return local_path


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

    remote_path = files[-1]
    filename = remote_path.split("/")[-1]

    local_path = RAW_DIR / filename
    if use_cache and local_path.exists():
        return local_path

    logger.info("Downloading MCMIPF: %s", filename)
    fs = _get_fs()
    fs.get(remote_path, str(local_path))
    return local_path


def download_fdc(dt: datetime, use_cache: bool = True) -> Path | None:
    """Descargar producto FDCF (Fire/Hot Spot Detection)."""
    files = list_files(PRODUCTS["fdc"], dt)
    if not files:
        return None

    remote_path = files[-1]
    filename = remote_path.split("/")[-1]

    local_path = RAW_DIR / filename
    if use_cache and local_path.exists():
        return local_path

    logger.info("Downloading FDCF: %s", filename)
    fs = _get_fs()
    fs.get(remote_path, str(local_path))
    return local_path


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
