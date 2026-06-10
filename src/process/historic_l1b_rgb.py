"""Generación de productos volcánicos desde L1b GOES-19 para fechas históricas.

Motivo (el "por qué"): RAMMB/CIRA SLIDER solo archiva ~9-10 meses de frames.
El bucket S3 `noaa-goes19` guarda las bandas L1b crudas de forma indefinida
(desde abril 2025, cuando GOES-19 pasó a GOES-East). Por eso, cuando RAMMB no
tiene un frame para una fecha, podemos REGENERAR el producto desde las bandas
L1b con el mismo motor de procesamiento que usa el NRT (Planck → BT → recetas).

Una sola función `fetch_l1b_rgb(product, dt, bounds)` cubre los 4 productos del
backfill, devolviendo un RGB uint8 (H, W, 3) ya recortado al bbox:

  - "geocolor"                               → TrueColor aprox. diurno (bandas
        1/2/3, geocolor_lite) + IR pseudo-color nocturno (banda 13). NO es el
        GeoColor de CIRA (sin Rayleigh, sin night-lights) — es una aproximación
        de color real suficiente para ver pluma visible y contexto.
  - "eumetsat_ash"                           → Ash RGB RAMMB/CIRA (bandas
        11/13/14/15). Mismo motor que la detección de ceniza propia.
  - "jma_so2"                                → Ash/SO2 RGB (bandas 11/14/15),
        SO2 resaltado en verde.
  - "split_window_difference_10_3-12_3"      → BTD split-window (bandas 14/15)
        mapeado a un colormap divergente (negativo = ceniza, Prata 1989).

Es el mismo pipeline que `src/process/pipeline.py` y `hires_pipeline.py`, pero
empaquetado por-producto para usarse como FALLBACK frame-a-frame en el backfill.
"""

from __future__ import annotations

import logging
import threading
from datetime import datetime, timedelta, timezone

import numpy as np
import xarray as xr

from src.config import RAW_DIR
from src.fetch.goes_s3 import _get_fs, list_band_files, open_band
from src.process.ash_detection import compute_btd_split_window
from src.process.ash_rgb import generate_ash_rgb, generate_ash_so2_rgb
from src.process.brightness_temp import rad_to_bt
from src.process.geo import crop_to_bounds, get_lat_lon
from src.process.geocolor_lite import (
    bt_to_pseudo_color_ir, rad_to_reflectance, solar_elevation, true_color_rgb,
)

logger = logging.getLogger(__name__)

# Bandas L1b necesarias por producto (sin contar el fallback nocturno de geocolor)
PRODUCT_BANDS: dict[str, list[int]] = {
    "geocolor": [1, 2, 3],                          # + 13 de noche
    "eumetsat_ash": [11, 13, 14, 15],               # Ash RGB CIRA
    "jma_so2": [11, 14, 15],                         # Ash/SO2 RGB
    "split_window_difference_10_3-12_3": [14, 15],  # BTD
}

DAY_NIGHT_THRESHOLD_DEG = 5.0

# Locks por-archivo: el backfill llama fetch_l1b_rgb desde varios threads
# (productos/scopes en paralelo) y distintos productos comparten bandas (14 va
# en ash, so2 y btd). Sin esto, dos threads bajarían el MISMO full-disk a la vez
# sobre el mismo path → archivo corrupto. Con el lock, el segundo cae al cache.
_DL_LOCKS: dict[str, threading.Lock] = {}
_DL_LOCKS_GUARD = threading.Lock()


def _lock_for(filename: str) -> threading.Lock:
    with _DL_LOCKS_GUARD:
        lk = _DL_LOCKS.get(filename)
        if lk is None:
            lk = threading.Lock()
            _DL_LOCKS[filename] = lk
        return lk


def _parse_scan_start(remote_path: str) -> datetime | None:
    """Hora de inicio del scan desde el nombre `..._sYYYYDDDHHMMSSm_...`."""
    fname = remote_path.split("/")[-1]
    try:
        i = fname.index("_s") + 2
        ts = fname[i:i + 13]  # YYYYDDDHHMMSS
        year = int(ts[:4]); doy = int(ts[4:7])
        hh = int(ts[7:9]); mm = int(ts[9:11]); ss = int(ts[11:13])
        return (datetime(year, 1, 1, hh, mm, ss, tzinfo=timezone.utc)
                + timedelta(days=doy - 1))
    except Exception:
        return None


def _download_band_nearest(dt: datetime, band: int, use_cache: bool = True):
    """Descargar la banda L1b cuyo scan es MÁS CERCANO a `dt`.

    El `download_band` de goes_s3 toma `files[-1]` (el último scan de la hora),
    lo cual para un backfill rompe la evolución temporal: todos los ts de una
    misma hora caerían en el mismo scan (~:50). Acá listamos la hora pedida ±1h
    y elegimos el scan con menor gap al timestamp objetivo.

    Devuelve un Path local (descargado/cacheado) o None.
    """
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    candidates: list[str] = []
    for h_off in (-1, 0, 1):
        candidates.extend(list_band_files(dt + timedelta(hours=h_off), band))
    if not candidates:
        logger.warning("L1b banda %d: sin archivos cerca de %s", band, dt.isoformat())
        return None

    best, best_gap = None, None
    for rp in candidates:
        sdt = _parse_scan_start(rp)
        if sdt is None:
            continue
        gap = abs((sdt - dt).total_seconds())
        if best_gap is None or gap < best_gap:
            best, best_gap = rp, gap
    if best is None:
        return None

    filename = best.split("/")[-1]
    local_path = RAW_DIR / filename
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    if use_cache and local_path.exists():
        return local_path
    # Serializar la descarga de este archivo entre threads (ver _DL_LOCKS).
    with _lock_for(filename):
        if use_cache and local_path.exists():
            return local_path  # otro thread lo bajó mientras esperábamos
        logger.info("L1b banda %d: descargando %s (gap %.0fs)", band, filename,
                    best_gap or 0)
        _get_fs().get(best, str(local_path))
    return local_path


def _downsample_2x(arr: np.ndarray) -> np.ndarray:
    """Downsample 2x (block-mean) — banda 2 (0.5km) → 1km para alinear con 1/3."""
    h, w = arr.shape[:2]
    h2, w2 = h // 2, w // 2
    return arr[:h2 * 2, :w2 * 2].reshape(h2, 2, w2, 2).mean(axis=(1, 3))


def _btd_to_rgb(btd: np.ndarray, vmin: float = -4.0, vmax: float = 4.0
                ) -> np.ndarray:
    """Mapear BTD split-window (K) a un colormap divergente azul↔rojo.

    Negativo (ceniza de silicatos, Prata 1989) → rojo. Cero → gris neutro.
    Positivo (nubes meteo de hielo/agua) → azul. NaN → negro (espacio/borde).
    """
    norm = np.clip((btd - vmin) / (vmax - vmin), 0, 1)  # 0=ash, 1=meteo
    nan = np.isnan(btd)
    # Interpolación lineal entre rojo (0), gris (0.5) y azul (1).
    r = np.where(norm < 0.5, 1.0, 1.0 - (norm - 0.5) * 2.0)
    b = np.where(norm < 0.5, norm * 2.0, 1.0)
    g = 1.0 - np.abs(norm - 0.5) * 2.0  # pico gris-claro en el centro
    g = 0.3 + g * 0.5
    rgb = np.clip(np.dstack([r, g, b]), 0, 1)
    rgb[nan] = 0.0
    return (rgb * 255).astype(np.uint8)


def _ir_product(product: str, dt: datetime, bounds: dict) -> np.ndarray | None:
    """Productos IR (ash/so2/btd): bandas 2km, mismo grid, crop directo."""
    bands = PRODUCT_BANDS[product]
    paths = {}
    for b in bands:
        p = _download_band_nearest(dt, b)
        if p is None:
            logger.warning("L1b %s: falta banda %d", product, b)
            return None
        paths[b] = p
    datasets = {b: open_band(p) for b, p in paths.items()}
    try:
        bts = {b: rad_to_bt(ds) for b, ds in datasets.items()}
        # lat/lon desde la primera banda (todas comparten grid 2km)
        ref = bands[0]
        lat, lon = get_lat_lon(datasets[ref])
        crops = {}
        for b in bands:
            c, _, _ = crop_to_bounds(bts[b], lat, lon, bounds)
            crops[b] = c
        if any(crops[b].size == 0 for b in bands):
            logger.warning("L1b %s: bbox sin datos tras crop", product)
            return None
        das = {b: xr.DataArray(crops[b], dims=["y", "x"]) for b in bands}

        if product == "eumetsat_ash":
            rgb = generate_ash_rgb(das[11], das[13], das[14], das[15])
        elif product == "jma_so2":
            rgb = generate_ash_so2_rgb(das[11], das[14], das[15])
        elif product == "split_window_difference_10_3-12_3":
            btd = compute_btd_split_window(das[14], das[15])
            return _btd_to_rgb(btd.values)
        else:
            return None
        return (np.clip(rgb, 0, 1) * 255).astype(np.uint8)
    finally:
        for ds in datasets.values():
            ds.close()


def _geocolor_product(dt: datetime, bounds: dict) -> np.ndarray | None:
    """GeoColor aprox.: TrueColor diurno (1/2/3) o IR pseudo-color nocturno (13)."""
    lat_c = (bounds["lat_min"] + bounds["lat_max"]) / 2
    lon_c = (bounds["lon_min"] + bounds["lon_max"]) / 2
    sun_alt = solar_elevation(lat_c, lon_c, dt)
    is_day = sun_alt >= DAY_NIGHT_THRESHOLD_DEG

    if is_day:
        paths = {}
        for b in (1, 2, 3):
            p = _download_band_nearest(dt, b)
            if p is None:
                logger.warning("L1b geocolor: falta banda visible %d", b)
                is_day = False
                break
            paths[b] = p
        if is_day:
            datasets = {b: open_band(p) for b, p in paths.items()}
            try:
                refl = {b: rad_to_reflectance(datasets[b]["Rad"], datasets[b])
                        for b in (1, 2, 3)}
                refl[2] = _downsample_2x(refl[2])  # 0.5km → 1km
                lat, lon = get_lat_lon(datasets[1])
                b1, _, _ = crop_to_bounds(xr.DataArray(refl[1], dims=["y", "x"]),
                                          lat, lon, bounds)
                b2, _, _ = crop_to_bounds(xr.DataArray(refl[2], dims=["y", "x"]),
                                          lat, lon, bounds)
                b3, _, _ = crop_to_bounds(xr.DataArray(refl[3], dims=["y", "x"]),
                                          lat, lon, bounds)
                if b2.size == 0:
                    logger.warning("L1b geocolor: bbox sin datos visibles")
                    return None
                return true_color_rgb(b1, b2, b3)
            finally:
                for ds in datasets.values():
                    ds.close()

    # Noche (o sin visibles): IR pseudo-color desde banda 13.
    p13 = _download_band_nearest(dt, 13)
    if p13 is None:
        logger.warning("L1b geocolor: sin banda 13 para fallback nocturno")
        return None
    ds13 = open_band(p13)
    try:
        bt = rad_to_bt(ds13)
        lat, lon = get_lat_lon(ds13)
        crop, _, _ = crop_to_bounds(bt, lat, lon, bounds)
        if crop.size == 0:
            return None
        return bt_to_pseudo_color_ir(crop)
    finally:
        ds13.close()


def fetch_l1b_rgb(product: str, dt: datetime, bounds: dict) -> np.ndarray | None:
    """RGB uint8 (H, W, 3) de un producto, regenerado desde L1b GOES-19.

    Args:
        product: clave RAMMB del producto ('geocolor', 'eumetsat_ash',
                 'jma_so2', 'split_window_difference_10_3-12_3').
        dt:      datetime UTC objetivo (se elige el scan L1b más cercano).
        bounds:  dict lat_min/lat_max/lon_min/lon_max del bbox a recortar.

    Returns:
        Array RGB uint8, o None si no hay datos / producto desconocido / error.
    """
    if product not in PRODUCT_BANDS:
        logger.warning("fetch_l1b_rgb: producto desconocido '%s'", product)
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    try:
        if product == "geocolor":
            return _geocolor_product(dt, bounds)
        return _ir_product(product, dt, bounds)
    except Exception as e:
        logger.exception("fetch_l1b_rgb %s @ %s: %s", product, dt.isoformat(), e)
        return None
