"""Serie temporal intradía de FRP (Fire Radiative Power) por volcán — la
fortaleza ÚNICA de GOES frente a MODIS/VIIRS.

Por qué existe este módulo (el "por qué" antes que el "cómo"):

GOES es geoestacionario → ve el MISMO punto cada 10 min (~144 scans/día).
MODIS/VIIRS son polares → 2-4 pasadas/día. Para *magnitud* y *sensibilidad*
térmica los polares ganan (375 m–1 km vs ~2 km en nadir, peor aún en el sur
de Chile por el ángulo oblicuo). Pero para la *evolución temporal* de un
evento efusivo —el encendido y la escalada entre pasadas polares— GOES no
tiene rival. Este módulo construye esa curva intradía de FRP que MODIS/VIIRS
no puede dar.

Limitación física honesta: el algoritmo FDCF rara vez dispara sobre volcanes
chilenos (0-3 hotspots en todo Chile por scan; las explosivas con ceniza fría
NO calientan el pixel). Así que esta serie es CERO la mayor parte del tiempo
y "se enciende" sólo durante actividad efusiva con lava expuesta (típico:
Villarrica, Láscar). Eso es exactamente cuando la cadencia de 10 min importa.

Dos piezas:
- ``sum_frp_per_volcano``: agregación PURA (suma de FRP en MW dentro de un
  radio de cada volcán). Testeable sin red.
- ``fetch_scan_sliced``: lee el FDCF más cercano a un ``dt`` recortando el grid
  fijo ABI al sub-bloque que cubre Chile → ~1 s/scan en vez de ~15 s. Desde el
  audit ago-2026 el recorte lo hace ``goes_fdcf.extract_hotspots`` para TODOS
  los lectores; esto quedó como alias con el default ``CHILE_BBOX``.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional

import numpy as np

# El lector de FDCF (selección de gránulo + recorte por bbox + armado de
# HotSpot) vive en goes_fdcf: acá sólo se agrega por volcán y por día.
# `_chile_xy_index_range` se conserva como alias por compatibilidad.
from src.fetch.goes_fdcf import (
    fetch_hotspots_at_time,
    xy_index_range as _chile_xy_index_range,  # noqa: F401 (alias histórico)
)

logger = logging.getLogger(__name__)

# Bbox Chile + márgenes vecinos cubiertos por GOES-19.
CHILE_BBOX = {
    "lat_min": -56, "lat_max": -17,
    "lon_min": -76, "lon_max": -66,
}


def sum_frp_per_volcano(
    hotspots: list,
    volcanoes: list,
    radius_km: float = 50.0,
) -> tuple[dict[str, float], dict[str, int]]:
    """Suma de FRP (MW) y conteo de hotspots ≤``radius_km`` de cada volcán.

    Args:
        hotspots:  lista de HotSpot (o cualquier objeto con .lat/.lon/.frp_mw).
        volcanoes: lista de Volcano (objetos con .name/.lat/.lon).
        radius_km: radio de atribución. 50 km da margen para el error de
                   geolocalización de GOES en el sur (vista oblicua).

    Returns:
        (frp_by_name, count_by_name) — dos dicts {nombre_volcán: valor}.
        frp en MW (float, redondeado a 1 decimal), count en pixeles (int).

    Nota: un hotspot puede contar para más de un volcán si ambos están
    dentro del radio (volcanes vecinos). Es intencional — preferimos no
    perder señal por desambiguar de más con la resolución gruesa de GOES.
    """
    frp_by_name: dict[str, float] = {}
    count_by_name: dict[str, int] = {}
    for v in volcanoes:
        total_frp = 0.0
        n = 0
        cos_lat = float(np.cos(np.radians(v.lat)))
        for h in hotspots:
            dlat = (h.lat - v.lat) * 111.0
            dlon = (h.lon - v.lon) * 111.0 * cos_lat
            d = float(np.hypot(dlat, dlon))
            if d <= radius_km:
                total_frp += float(getattr(h, "frp_mw", 0.0) or 0.0)
                n += 1
        frp_by_name[v.name] = round(total_frp, 1)
        count_by_name[v.name] = n
    return frp_by_name, count_by_name


def daily_rollup(scans: list) -> dict:
    """Roll-up diario derivado de los scans de 10 min (para el heatmap semanal).

    Métrica por (día, volcán): **número de scans con detección** (≥1 hotspot
    ≤radio). Es una medida de *persistencia* — cuántos intervalos de ~10 min
    tuvieron señal térmica ese día. Distingue un blip de 1 scan de actividad
    sostenida, cosa que el conteo de pixeles de un solo scan NO podía hacer.

    Args:
        scans: lista de dicts {"t": iso, "frp": {...}, "n": {...}} como los que
               guarda build_frp_timeline (campo "n" = conteo de hotspots).

    Returns:
        {"YYYY-MM-DD": {"Villarrica": 8, "Lascar": 2, ...}, ...}
        Sólo incluye volcanes con ≥1 scan con detección ese día.
    """
    out: dict[str, dict[str, int]] = {}
    for s in scans:
        day = str(s.get("t", ""))[:10]
        if not day:
            continue
        d = out.setdefault(day, {})
        for name, n in s.get("n", {}).items():
            if n and n > 0:
                d[name] = d.get(name, 0) + 1
    return out


def fetch_scan_sliced(
    dt: datetime,
    bounds: Optional[dict] = None,
    high_conf_only: bool = False,
) -> tuple[list, Optional[datetime]]:
    """Lee el FDCF más cercano a ``dt`` recortado a la región de Chile.

    Alias delgado: desde el audit ago-2026 el recorte por bbox vive en
    ``goes_fdcf.extract_hotspots`` y lo usan **todos** los lectores, no sólo la
    timeline. Lo único propio de acá es el default ``CHILE_BBOX`` — el barrido
    intradía siempre quiere la franja del país, nunca el disco entero.

    Returns:
        (hotspots, scan_dt_real) — ([], None) si no encuentra archivo.
    """
    return fetch_hotspots_at_time(dt, bounds or CHILE_BBOX,
                                  high_conf_only=high_conf_only)
