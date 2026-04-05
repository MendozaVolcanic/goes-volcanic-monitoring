"""Pipeline de procesamiento: descarga → BT → Ash RGB → crop → cache.

Orquesta todo el flujo desde AWS S3 hasta imágenes listas para el dashboard.
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from src.config import CHILE_BOUNDS, PROCESSED_DIR, VOLCANIC_BANDS
from src.fetch.goes_s3 import download_band, download_fdc, get_latest_time, open_band
from src.process.ash_detection import compute_ash_confidence, compute_btd_split_window
from src.process.ash_rgb import generate_ash_rgb, generate_so2_indicator
from src.process.brightness_temp import rad_to_bt
from src.process.geo import crop_to_bounds, get_lat_lon

logger = logging.getLogger(__name__)


def _save_image(rgb: np.ndarray, path: Path) -> None:
    """Guardar array RGB como PNG."""
    from PIL import Image

    # Convertir de [0,1] float a [0,255] uint8
    img_data = (np.clip(rgb, 0, 1) * 255).astype(np.uint8)
    img = Image.fromarray(img_data)
    img.save(str(path))
    logger.info("Saved: %s (%dx%d)", path.name, img.width, img.height)


def _save_array(data: np.ndarray, path: Path) -> None:
    """Guardar array numpy comprimido."""
    np.savez_compressed(str(path), data=data)


def process_ash_rgb(
    dt: datetime,
    bounds: dict | None = None,
    save: bool = True,
) -> dict:
    """Pipeline completo: descarga bandas → Ash RGB + BTD + SO2.

    Args:
        dt: Datetime UTC de la imagen deseada.
        bounds: Bounding box para crop. Default: Chile completo.
        save: Si guardar imágenes a disco.

    Returns:
        Dict con:
            - ash_rgb: array (H,W,3) normalizado [0,1]
            - btd: array (H,W) en K
            - ash_confidence: array (H,W) valores 0-3
            - so2: array (H,W) en K
            - lat, lon: arrays 2D
            - timestamp: str ISO
            - paths: dict de paths guardados
    """
    if bounds is None:
        bounds = CHILE_BOUNDS

    # 1. Descargar bandas necesarias (11, 13, 14, 15)
    logger.info("Downloading bands for %s...", dt.strftime("%Y-%m-%d %H:%M UTC"))
    needed_bands = [11, 13, 14, 15]
    band_paths = {}
    for b in needed_bands:
        path = download_band(dt, b)
        if path is None:
            raise FileNotFoundError(f"Could not download band {b} for {dt}")
        band_paths[b] = path

    # 2. Abrir y convertir a BT
    logger.info("Computing brightness temperatures...")
    datasets = {b: open_band(p) for b, p in band_paths.items()}
    bts = {b: rad_to_bt(ds) for b, ds in datasets.items()}

    # 3. Calcular geolocalización (usar band 14 como referencia)
    logger.info("Computing geolocation...")
    lat, lon = get_lat_lon(datasets[14])

    # 4. Crop a la región de interés
    logger.info("Cropping to bounds...")
    bt_crops = {}
    lat_crop = lon_crop = None
    for b in needed_bands:
        data_crop, lat_c, lon_c = crop_to_bounds(bts[b], lat, lon, bounds)
        bt_crops[b] = data_crop
        if lat_crop is None:
            lat_crop = lat_c
            lon_crop = lon_c

    if lat_crop is None or lat_crop.size == 0:
        raise ValueError("No data within bounds after cropping")

    # 5. Generar productos
    logger.info("Generating Ash RGB...")
    import xarray as xr

    # Wrap crops as DataArrays for the processing functions
    bt11_da = xr.DataArray(bt_crops[11], dims=["y", "x"])
    bt13_da = xr.DataArray(bt_crops[13], dims=["y", "x"])
    bt14_da = xr.DataArray(bt_crops[14], dims=["y", "x"])
    bt15_da = xr.DataArray(bt_crops[15], dims=["y", "x"])

    ash_rgb = generate_ash_rgb(bt11_da, bt13_da, bt14_da, bt15_da)

    logger.info("Computing BTD and ash detection...")
    btd = compute_btd_split_window(bt14_da, bt15_da)
    confidence = compute_ash_confidence(bt11_da, bt14_da, bt15_da)
    so2 = generate_so2_indicator(bt11_da, bt14_da)

    # 6. Guardar
    ts_str = dt.strftime("%Y%m%d_%H%M")
    paths = {}
    if save:
        PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
        ash_path = PROCESSED_DIR / f"ash_rgb_{ts_str}.png"
        _save_image(ash_rgb, ash_path)
        paths["ash_rgb"] = str(ash_path)

        btd_path = PROCESSED_DIR / f"btd_{ts_str}.npz"
        _save_array(btd.values, btd_path)
        paths["btd"] = str(btd_path)

        conf_path = PROCESSED_DIR / f"ash_confidence_{ts_str}.npz"
        _save_array(confidence.values, conf_path)
        paths["ash_confidence"] = str(conf_path)

        geo_path = PROCESSED_DIR / f"geo_{ts_str}.npz"
        np.savez_compressed(str(geo_path), lat=lat_crop, lon=lon_crop)
        paths["geo"] = str(geo_path)

        # Metadata
        meta = {
            "timestamp": dt.isoformat(),
            "bounds": bounds,
            "shape": list(ash_rgb.shape[:2]),
            "bands_used": needed_bands,
            "products": list(paths.keys()),
        }
        meta_path = PROCESSED_DIR / f"meta_{ts_str}.json"
        meta_path.write_text(json.dumps(meta, indent=2))
        paths["meta"] = str(meta_path)

    # Cerrar datasets
    for ds in datasets.values():
        ds.close()

    return {
        "ash_rgb": ash_rgb,
        "btd": btd.values,
        "ash_confidence": confidence.values,
        "so2": so2.values,
        "lat": lat_crop,
        "lon": lon_crop,
        "timestamp": dt.isoformat(),
        "paths": paths,
    }


def get_latest_processed() -> dict | None:
    """Buscar el último resultado procesado en disco.

    Returns:
        Dict con metadata y paths, o None si no hay datos.
    """
    meta_files = sorted(PROCESSED_DIR.glob("meta_*.json"), reverse=True)
    if not meta_files:
        return None

    meta = json.loads(meta_files[0].read_text())
    ts_str = meta_files[0].stem.replace("meta_", "")

    # Verificar que los archivos asociados existen
    result = {"meta": meta, "paths": {}, "timestamp": meta["timestamp"]}
    for product in ["ash_rgb", "btd", "ash_confidence", "geo"]:
        if product == "ash_rgb":
            p = PROCESSED_DIR / f"{product}_{ts_str}.png"
        else:
            p = PROCESSED_DIR / f"{product}_{ts_str}.npz"
        if p.exists():
            result["paths"][product] = str(p)

    return result


def load_processed(info: dict) -> dict:
    """Cargar datos procesados desde disco.

    Args:
        info: Dict retornado por get_latest_processed().

    Returns:
        Dict con arrays numpy cargados.
    """
    from PIL import Image

    result = {"timestamp": info["timestamp"], "meta": info["meta"]}
    paths = info["paths"]

    if "ash_rgb" in paths:
        img = Image.open(paths["ash_rgb"])
        result["ash_rgb"] = np.array(img).astype(np.float32) / 255.0

    if "btd" in paths:
        result["btd"] = np.load(paths["btd"])["data"]

    if "ash_confidence" in paths:
        result["ash_confidence"] = np.load(paths["ash_confidence"])["data"]

    if "geo" in paths:
        geo = np.load(paths["geo"])
        result["lat"] = geo["lat"]
        result["lon"] = geo["lon"]

    return result
