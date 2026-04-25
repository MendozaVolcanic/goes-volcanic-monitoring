"""Series temporales de intensidad de señal por volcán.

Idea: para cada uno de los últimos N scans RAMMB del producto Ash RGB
(o SO2), computar una métrica escalar de "qué tan activa está la firma
de ceniza/SO2 en el área del volcán". Plotear N puntos vs tiempo.

La métrica que usamos es el **% de píxeles con firma de ceniza** dentro de
un radio del volcán. Para Ash RGB EUMETSAT, "firma de ceniza" = píxeles
con red dominante (R > G y R > B y R > umbral). Esa receta es proxy
imperfecta pero rápida y consistente entre scans.

Para análisis geofísico riguroso conviene usar BTD < umbral (Prata 1989)
desde L1b — eso es más caro y se deja para una v2 (TODO).

Cadencia: 6 frames por hora. 24h = 144 frames. Bajamos en paralelo,
cada frame ~150-300ms. Con 8 workers = ~3-5s para 24h.
"""

from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import numpy as np

from src.fetch.rammb_slider import (
    fetch_frame_for_bounds, get_latest_timestamps, ZOOM_VOLCAN, ZOOM_ZONE,
)

logger = logging.getLogger(__name__)


@dataclass
class TimeSeriesPoint:
    ts: str                     # YYYYMMDDhhmmss
    dt: datetime                # UTC
    metric: float               # valor (% pixeles, MW, etc.)
    available: bool             # True si fetch ok


def _ash_red_fraction(img: np.ndarray) -> float:
    """% de pixeles con dominancia roja (proxy de firma de ceniza Ash RGB).

    Filtros:
      - canal R > 100 (suficientemente brillante)
      - R > G + 15 (rojo dominante sobre verde)
      - R > B + 15 (rojo dominante sobre azul)
    """
    if img is None or img.size == 0:
        return 0.0
    r = img[:, :, 0].astype(np.int16)
    g = img[:, :, 1].astype(np.int16)
    b = img[:, :, 2].astype(np.int16)
    mask_red = (r > 100) & (r > g + 15) & (r > b + 15)
    # Excluir pixeles totalmente negros (no-data del relleno de tile)
    valid = (r + g + b) > 30
    n_valid = int(valid.sum())
    if n_valid == 0:
        return 0.0
    return float(mask_red.sum()) / float(n_valid) * 100.0


def _so2_green_fraction(img: np.ndarray) -> float:
    """% de pixeles con verde dominante (proxy de SO2 RGB JMA)."""
    if img is None or img.size == 0:
        return 0.0
    r = img[:, :, 0].astype(np.int16)
    g = img[:, :, 1].astype(np.int16)
    b = img[:, :, 2].astype(np.int16)
    mask_green = (g > 100) & (g > r + 15) & (g > b + 15)
    valid = (r + g + b) > 30
    n_valid = int(valid.sum())
    if n_valid == 0:
        return 0.0
    return float(mask_green.sum()) / float(n_valid) * 100.0


METRIC_FN = {
    "eumetsat_ash": _ash_red_fraction,
    "jma_so2":      _so2_green_fraction,
}

METRIC_LABEL = {
    "eumetsat_ash": "% píxeles con firma de ceniza (R dominante)",
    "jma_so2":      "% píxeles con firma SO2 (G dominante)",
}


def fetch_volcano_timeseries(
    volcano_lat: float,
    volcano_lon: float,
    product: str = "eumetsat_ash",
    n_frames: int = 36,           # 36 = 6 horas
    radius_deg: float = 1.0,
    max_workers: int = 8,
    zoom: int = ZOOM_ZONE,
) -> list[TimeSeriesPoint]:
    """Series de N puntos para un volcán (lat/lon).

    Args:
        volcano_lat, volcano_lon: coords del vent.
        product: 'eumetsat_ash' o 'jma_so2'.
        n_frames: cantidad de scans RAMMB. 36 = 6h, 144 = 24h.
        radius_deg: radio del bbox alrededor del volcán (default 1° ≈ 111 km).
        zoom: nivel zoom RAMMB. 3 = ~3.4 km/px, 4 = ~1.7 km/px (mas pesado).

    Returns:
        Lista de puntos ordenados de mas antiguo a mas reciente.
    """
    fn = METRIC_FN.get(product)
    if fn is None:
        raise ValueError(f"Producto sin metrica: {product}")

    timestamps = get_latest_timestamps(product, n=n_frames)
    if not timestamps:
        return []

    bounds = {
        "lat_min": volcano_lat - radius_deg, "lat_max": volcano_lat + radius_deg,
        "lon_min": volcano_lon - radius_deg, "lon_max": volcano_lon + radius_deg,
    }

    def _one(ts: str) -> TimeSeriesPoint:
        from src.fetch.rammb_slider import ts_to_parts
        from dashboard.utils import parse_rammb_ts
        try:
            img = fetch_frame_for_bounds(product, ts, bounds, zoom=zoom)
            if img is None:
                return TimeSeriesPoint(ts, parse_rammb_ts(ts), 0.0, False)
            metric = fn(img)
            return TimeSeriesPoint(ts, parse_rammb_ts(ts), metric, True)
        except Exception as e:
            logger.warning("Frame %s falló: %s", ts, e)
            return TimeSeriesPoint(ts, parse_rammb_ts(ts), 0.0, False)

    points: list[TimeSeriesPoint] = []
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futures = {ex.submit(_one, ts): ts for ts in timestamps}
        for fut in as_completed(futures):
            points.append(fut.result())

    points.sort(key=lambda p: p.ts)
    return points
