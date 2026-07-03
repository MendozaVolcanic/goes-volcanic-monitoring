"""Imagen VIIRS pre-georreferenciada desde NASA GIBS (WMS GetMap).

Por qué existe (geología → pipeline): GOES-19 cubre todo Chile pero a 2 km, y
varios volcanes patagónicos (Hudson, Chaitén, Melimoyu, Corcovado…) no tienen
sector VOLCAT ni monitoreo dedicado. VIIRS (Suomi-NPP / NOAA-20 / NOAA-21, polares)
da imagen a 375 m y anomalías térmicas ~2 ventanas/día — grueso en cadencia, fino
en espacio: el complemento natural del ABI para esos volcanes.

Por qué GIBS y no los gránulos crudos: VIIRS es polar (gránulos con geolocalización
propia, bowtie, ángulo de vista variable). Reproyectar eso nosotros sería un
segundo pipeline geométrico completo. **NASA GIBS ya lo hace** y sirve las capas
como WMS/WMTS georreferenciadas → pedimos por bbox+fecha con un solo GetMap y
recibimos un PNG listo. Cero manejo de geometría polar. (Decisión jul-2026: NO
construimos pipeline VIIRS propio; ver `docs/paper/REGISTRO_PAPER.md §9`.)

Alcance: imagen/térmico INDICATIVO para vistas, **separado de la cadena ABI NRT**
(no se mezcla en el dashboard de altura/ceniza). No es un retrieval cuantitativo.

Fuente: `https://gibs.earthdata.nasa.gov/wms/epsg4326/best/wms.cgi` (sin auth).
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

logger = logging.getLogger(__name__)

GIBS_WMS = "https://gibs.earthdata.nasa.gov/wms/epsg4326/best/wms.cgi"
TIMEOUT = 30

# Presets de capa GIBS relevantes para volcanes. NOAA-20 es el VIIRS más reciente
# con serie completa; SNPP como respaldo. El térmico 375 m es un OVERLAY (píxeles
# solo donde hay anomalía). DayNightBand sirve para pulsos incandescentes nocturnos.
LAYERS = {
    "truecolor":      "VIIRS_NOAA20_CorrectedReflectance_TrueColor",
    "truecolor_snpp": "VIIRS_SNPP_CorrectedReflectance_TrueColor",
    "thermal":        "VIIRS_SNPP_Thermal_Anomalies_375m_All",
    "daynight":       "VIIRS_SNPP_DayNightBand_ENCC",
}


def _default_date() -> str:
    """Fecha por defecto = AYER UTC (el mosaico de hoy puede no estar compuesto).
    Formato ISO ``YYYY-MM-DD`` que espera el parámetro TIME de GIBS."""
    return (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")


def _bbox(lat: float, lon: float, pad_deg: float) -> dict:
    """Caja ±``pad_deg`` alrededor del volcán. PURA."""
    return {"lat_min": lat - pad_deg, "lat_max": lat + pad_deg,
            "lon_min": lon - pad_deg, "lon_max": lon + pad_deg}


def _getmap_params(layer: str, bbox: dict, when: str, size: int = 512) -> dict:
    """Parámetros del WMS GetMap. PURA (testeable sin red).

    OJO — WMS **1.3.0** con EPSG:4326 usa orden de ejes **(lat, lon)**: el BBOX va
    ``minLat,minLon,maxLat,maxLon`` (un error acá saca una imagen del lugar
    equivocado sin fallar). ``layer`` se resuelve contra ``LAYERS`` (KeyError si no
    existe → falla ruidoso, no capa vacía silenciosa).
    """
    layer_id = LAYERS[layer]
    return {
        "SERVICE": "WMS", "REQUEST": "GetMap", "VERSION": "1.3.0",
        "LAYERS": layer_id, "CRS": "EPSG:4326",
        "BBOX": (f"{bbox['lat_min']:g},{bbox['lon_min']:g},"
                 f"{bbox['lat_max']:g},{bbox['lon_max']:g}"),
        "WIDTH": size, "HEIGHT": size, "FORMAT": "image/png", "TIME": when,
    }


def _coverage_frac(img) -> float:
    """Fracción de píxeles no-negros. PURA. Para True Color, 0 = la pasada no cubrió
    la caja ese día; para el térmico, la fracción con anomalía detectada."""
    import numpy as np
    a = np.asarray(img)
    if a.ndim == 3:
        a = a.sum(axis=2)
    return float((a > 10).mean())


def fetch_viirs_image(
    lat: float, lon: float, when: Optional[str] = None,
    layer: str = "truecolor", pad_deg: float = 0.6, size: int = 512,
) -> Optional[dict]:
    """Imagen VIIRS georreferenciada sobre (lat,lon) para una fecha, vía GIBS WMS.

    Args:
        lat, lon:  centro (grados). ``when``: fecha ``YYYY-MM-DD`` (default ayer UTC).
        layer:     clave de ``LAYERS`` (truecolor / truecolor_snpp / thermal / daynight).
        pad_deg:   medio ancho de la caja. ``size``: px de lado.

    Returns:
        dict ``{image (H×W×3 uint8), bounds, layer, layer_id, date, coverage_frac,
        source}`` o None si faltan deps / falla la red / la respuesta no es imagen
        (p.ej. XML de excepción del servicio).
    """
    try:
        import io

        import numpy as np
        import requests
        from PIL import Image
    except ImportError as e:
        logger.error("deps no disponibles (requests/PIL/numpy): %s", e)
        return None

    when = when or _default_date()
    bbox = _bbox(lat, lon, pad_deg)
    try:
        params = _getmap_params(layer, bbox, when, size=size)
    except KeyError:
        logger.error("capa VIIRS desconocida: %s (válidas: %s)", layer, list(LAYERS))
        return None

    try:
        r = requests.get(GIBS_WMS, params=params, timeout=TIMEOUT)
        r.raise_for_status()
    except Exception as e:
        logger.warning("GIBS GetMap (%s, %s,%s): %s", layer, lat, lon, e)
        return None
    # GIBS devuelve XML (ServiceException) con 200 si algo está mal → no es imagen.
    if "image" not in r.headers.get("content-type", ""):
        logger.warning("GIBS no devolvió imagen para %s (%s)", layer,
                       r.headers.get("content-type"))
        return None

    try:
        img = np.asarray(Image.open(io.BytesIO(r.content)).convert("RGB"))
    except Exception as e:
        logger.warning("no pude decodificar la imagen GIBS: %s", e)
        return None

    return {
        "image": img,
        "bounds": bbox,
        "layer": layer,
        "layer_id": LAYERS[layer],
        "date": when,
        "coverage_frac": _coverage_frac(img),
        "source": f"VIIRS via NASA GIBS ({LAYERS[layer]})",
    }
