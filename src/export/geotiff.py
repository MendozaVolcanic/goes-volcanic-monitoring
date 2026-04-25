"""Helpers para exportar imagenes GOES como GeoTIFF georeferenciado.

Las imagenes que usamos en el dashboard ya estan reproyectadas a una grilla
lat/lon regular (ver src/fetch/rammb_slider.py::reproject_to_latlon).
Esto significa:

- CRS = EPSG:4326 (WGS84 geografico).
- Cada pixel cubre un dx/dy fijo en grados decimales.
- El bbox geografico es {lat_min, lat_max, lon_min, lon_max}.

Con esa info construimos un Affine y escribimos un GeoTIFF en memoria
usando rasterio MemoryFile. El binario resultante se puede entregar como
download en Streamlit y abre directo en QGIS.
"""

from __future__ import annotations

import io
import logging
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)


def build_geotiff_bytes(
    img: np.ndarray,
    bounds: dict,
    description: Optional[str] = None,
    nodata: Optional[int] = 0,
) -> bytes:
    """Convertir numpy (H,W,3) RGB uint8 a GeoTIFF georeferenciado en EPSG:4326.

    Args:
        img:    Array (H, W, 3) uint8 RGB. La imagen DEBE estar ya
                reproyectada a grilla lat/lon regular (no proyeccion ABI).
        bounds: dict con 'lat_min','lat_max','lon_min','lon_max' (grados).
        description: Tag opcional para metadata GeoTIFF (p.ej. timestamp UTC).
        nodata: Valor a marcar como nodata (default 0 = pixeles negros del
                relleno de tile que no cubre).

    Returns:
        bytes: contenido binario del .tif.
    """
    try:
        import rasterio
        from rasterio.io import MemoryFile
        from rasterio.transform import from_bounds
    except ImportError as e:
        logger.error("rasterio no disponible: %s", e)
        return b""

    if img.ndim != 3 or img.shape[2] not in (3, 4):
        raise ValueError(
            f"Esperaba (H,W,3) o (H,W,4), recibi shape={img.shape}"
        )

    # Si llega RGBA, descartar alpha — los lectores GIS lo manejan
    # pero la mayoria de viewers volcanologicos prefieren 3 bandas.
    if img.shape[2] == 4:
        img = img[:, :, :3]

    h, w = img.shape[:2]
    transform = from_bounds(
        west=bounds["lon_min"],
        south=bounds["lat_min"],
        east=bounds["lon_max"],
        north=bounds["lat_max"],
        width=w,
        height=h,
    )

    profile = {
        "driver":   "GTiff",
        "dtype":    "uint8",
        "count":    3,
        "height":   h,
        "width":    w,
        "crs":      "EPSG:4326",
        "transform": transform,
        "nodata":    nodata,
        "compress":  "DEFLATE",
        "predictor": 2,           # diff predictor para datos byte
        "tiled":     True,
        "blockxsize": 256,
        "blockysize": 256,
        "BIGTIFF":   "IF_SAFER",
    }

    try:
        with MemoryFile() as mem:
            with mem.open(**profile) as dst:
                # rasterio espera (band, H, W) — transponer
                dst.write(img.transpose(2, 0, 1))
                if description:
                    dst.update_tags(description=description)
                dst.update_tags(
                    source="GOES-19 / RAMMB-CIRA via slider.cira.colostate.edu",
                    crs_native="EPSG:4326 (reproyectado desde proyeccion ABI GEOS)",
                )
                # Tag por banda para que QGIS muestre el nombre real
                dst.update_tags(1, name="Red")
                dst.update_tags(2, name="Green")
                dst.update_tags(3, name="Blue")
            return mem.read()
    except Exception as e:
        logger.exception("Error escribiendo GeoTIFF: %s", e)
        return b""


def build_geotiff_from_rgb(
    img_rgb: np.ndarray,
    lat_min: float,
    lat_max: float,
    lon_min: float,
    lon_max: float,
    description: Optional[str] = None,
) -> bytes:
    """Wrapper conveniente con argumentos posicionales en lugar de dict."""
    return build_geotiff_bytes(
        img_rgb,
        bounds={
            "lat_min": lat_min, "lat_max": lat_max,
            "lon_min": lon_min, "lon_max": lon_max,
        },
        description=description,
    )
