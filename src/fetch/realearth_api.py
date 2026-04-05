"""Cliente para la API RealEarth de SSEC/CIMSS.

Accede a productos GOES-19 pre-procesados por SSEC, incluyendo
Ash RGB, SO2 RGB, y Volcanic Ash Advisories.

API pública sin autenticación.
Ref: https://realearth.ssec.wisc.edu/api/
"""

import io
import logging
from datetime import datetime

import numpy as np
import requests

from src.config import CACHE_DIR, CHILE_BOUNDS

logger = logging.getLogger(__name__)

BASE_URL = "https://realearth.ssec.wisc.edu/api"
TIMEOUT = 30

# Productos GOES-19 disponibles en RealEarth
REALEARTH_PRODUCTS = {
    # Full Disk (cobertura global, incluye Chile)
    "ash_rgb": "G19-ABI-FD-ash",
    "so2_rgb": "G19-ABI-FD-so2",
    # Volcanic Ash Advisories (vectores GeoJSON)
    "vaa": "VAA",
}

_session = None


def _get_session() -> requests.Session:
    """Session HTTP con retry."""
    global _session
    if _session is None:
        _session = requests.Session()
        _session.headers.update({"User-Agent": "GOES-VolcanicMonitor/1.0"})
    return _session


def get_latest_time(product_key: str) -> str | None:
    """Obtener el timestamp más reciente de un producto.

    Args:
        product_key: Clave del producto (e.g., 'ash_rgb', 'so2_rgb').

    Returns:
        String con timestamp (formato YYYYMMDD.HHMMSS) o None.
    """
    product_id = REALEARTH_PRODUCTS.get(product_key)
    if not product_id:
        logger.error("Producto desconocido: %s", product_key)
        return None

    try:
        resp = _get_session().get(
            f"{BASE_URL}/latest",
            params={"products": product_id},
            timeout=TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get(product_id)
    except Exception as e:
        logger.error("Error obteniendo latest time para %s: %s", product_key, e)
        return None


def fetch_image(
    product_key: str,
    bounds: dict | None = None,
    width: int = 900,
    height: int = 1100,
    time: str | None = None,
) -> np.ndarray | None:
    """Descargar imagen de producto como array numpy RGBA.

    Args:
        product_key: Clave del producto ('ash_rgb', 'so2_rgb').
        bounds: Dict con lat_min, lat_max, lon_min, lon_max.
        width: Ancho de la imagen en pixeles.
        height: Alto de la imagen en pixeles.
        time: Timestamp específico (formato YYYYMMDD.HHMMSS).

    Returns:
        Array numpy (H, W, 4) RGBA o None si falla.
    """
    from PIL import Image

    product_id = REALEARTH_PRODUCTS.get(product_key)
    if not product_id:
        logger.error("Producto desconocido: %s", product_key)
        return None

    if bounds is None:
        bounds = CHILE_BOUNDS

    # API usa formato: bounds=S,W,N,E
    bounds_str = f"{bounds['lat_min']},{bounds['lon_min']},{bounds['lat_max']},{bounds['lon_max']}"

    params = {
        "products": product_id,
        "bounds": bounds_str,
        "width": width,
        "height": height,
    }
    if time:
        params["time"] = time

    try:
        resp = _get_session().get(
            f"{BASE_URL}/image",
            params=params,
            timeout=TIMEOUT,
        )
        resp.raise_for_status()

        img = Image.open(io.BytesIO(resp.content))
        arr = np.array(img.convert("RGBA"))

        logger.info(
            "Fetched %s: %dx%d (%d KB)",
            product_key, arr.shape[1], arr.shape[0],
            len(resp.content) // 1024,
        )
        return arr

    except Exception as e:
        logger.error("Error descargando imagen %s: %s", product_key, e)
        return None


def fetch_vaa_geojson() -> dict | None:
    """Descargar Volcanic Ash Advisories como GeoJSON.

    Returns:
        Dict GeoJSON con polígonos de advisories, o None.
    """
    try:
        resp = _get_session().get(
            f"{BASE_URL}/shapes",
            params={"products": REALEARTH_PRODUCTS["vaa"]},
            timeout=TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()

        if data and "features" in data:
            logger.info("VAA: %d features", len(data["features"]))
        return data

    except Exception as e:
        logger.error("Error descargando VAA GeoJSON: %s", e)
        return None


def fetch_available_times(product_key: str, limit: int = 24) -> list[str]:
    """Obtener timestamps disponibles para un producto.

    Args:
        product_key: Clave del producto.
        limit: Número máximo de timestamps a retornar.

    Returns:
        Lista de timestamps (más reciente primero).
    """
    product_id = REALEARTH_PRODUCTS.get(product_key)
    if not product_id:
        return []

    try:
        resp = _get_session().get(
            f"{BASE_URL}/times",
            params={"products": product_id},
            timeout=TIMEOUT,
        )
        resp.raise_for_status()
        times = resp.json()
        if isinstance(times, list):
            return sorted(times, reverse=True)[:limit]
        return []
    except Exception as e:
        logger.error("Error obteniendo times para %s: %s", product_key, e)
        return []


def search_products(query: str = "volcano") -> list[dict]:
    """Buscar productos disponibles en RealEarth.

    Args:
        query: Término de búsqueda.

    Returns:
        Lista de dicts con id y name de productos.
    """
    try:
        resp = _get_session().get(
            f"{BASE_URL}/products",
            params={"search": query},
            timeout=TIMEOUT,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.error("Error buscando productos: %s", e)
        return []
