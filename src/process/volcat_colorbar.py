"""Reverse-mapping del colorbar QUEMADO de VOLCAT Ash_Height (km AMSL).

Por qué (y la advertencia honesta): VOLCAT/SSEC sirve la altura como PNG con el
número **quemado** en una escala de color (arcoíris), no como NetCDF con el float.
Para tener una **referencia de magnitud absoluta** con la que cruzar nuestro
retrieval propio (Wen-Rose/BT-matching), reconstruimos el valor desde el color.

**Esto es FRÁGIL e INDICATIVO** (±1-2 km extra): depende de la paleta SSEC (si la
cambian, se rompe), de la dirección/rango del colorbar y de aislar bien los
píxeles de altura de los overlays del mapa. Se usa SOLO como cross-check de
validación, NUNCA como número operacional. El camino robusto para ground truth es
el feed NetCDF de CIMSS (ver ALTURA_COLUMNA_INVESTIGACION.md §4).

Estas son las piezas PURAS (sin red): extraer la barra arcoíris, armar el LUT
color→km, y mapear píxeles a altura por color más cercano (con una distancia de
color que sirve de filtro: los overlays, lejos del arcoíris, quedan afuera).
"""
from __future__ import annotations

from typing import Optional

import numpy as np

VOLCAT_HEIGHT_VMIN = 0.0    # km AMSL — extremo bajo del colorbar Ash/Dust Height
VOLCAT_HEIGHT_VMAX = 20.0   # km AMSL — extremo alto (label "20" del strip SSEC)
COLOR_MATCH_MAX = 40.0      # distancia RGB máx a la paleta para contar como altura


def extract_rainbow_bar(strip_rgb, sat_min: float = 0.25):
    """Encontrar la barra arcoíris dentro de la mitad derecha del strip inferior
    del PNG VOLCAT (donde está la escala de altura). Toma la **fila más saturada**
    (la barra) y devuelve sus columnas saturadas (el gradiente, ordenado
    izquierda→derecha) como ``(N, 3)`` float, o None si no la encuentra. PURA.
    """
    a = np.asarray(strip_rgb, dtype="float64")
    mx, mn = a.max(2), a.min(2)
    with np.errstate(invalid="ignore", divide="ignore"):
        sat = np.where(mx > 0, (mx - mn) / mx, 0.0)
    row = int(np.argmax(sat.mean(1)))
    cols = np.where(sat[row] > sat_min)[0]
    if len(cols) < 20:
        return None
    return a[row, cols.min():cols.max() + 1]


def build_height_lut(bar_rgb, vmin: float = VOLCAT_HEIGHT_VMIN,
                     vmax: float = VOLCAT_HEIGHT_VMAX, low_at_left: bool = True):
    """LUT color→altura desde la barra arcoíris. ``low_at_left``: True si el
    extremo IZQUIERDO de la barra es ``vmin`` (km bajos). Devuelve
    ``(lut_rgb (N,3), lut_val (N,))``. PURA.
    """
    bar = np.asarray(bar_rgb, dtype="float64")
    n = len(bar)
    frac = np.arange(n) / max(n - 1, 1)
    if not low_at_left:
        frac = frac[::-1]
    return bar, vmin + (vmax - vmin) * frac


def reverse_map_heights(rgb, lut_rgb, lut_val):
    """Mapear cada píxel RGB a altura por **color más cercano** en el LUT.
    Devuelve ``(val (M,), color_dist (M,))``: la altura y la distancia de color
    (calidad del match — grande ⇒ el píxel NO es del arcoíris, p.ej. un overlay,
    y debe descartarse con ``COLOR_MATCH_MAX``). PURA.
    """
    px = np.asarray(rgb, dtype="float64").reshape(-1, 3)
    lut = np.asarray(lut_rgb, dtype="float64")
    # distancia euclídea RGB a cada entrada del LUT (M,N)
    d = np.sqrt(((px[:, None, :] - lut[None, :, :]) ** 2).sum(2))
    idx = d.argmin(1)
    return np.asarray(lut_val)[idx], d.min(1)


def heights_from_plume(rgb_pixels, lut_rgb, lut_val,
                       match_max: float = COLOR_MATCH_MAX) -> Optional[dict]:
    """Estadísticos de altura sobre un conjunto de píxeles candidatos: reverse-map
    + filtro por distancia de color (descarta overlays). Devuelve dict
    ``{p95_km, max_km, median_km, n_matched, n_in}`` o None si nada matchea. PURA.
    """
    vals, dist = reverse_map_heights(rgb_pixels, lut_rgb, lut_val)
    ok = dist <= match_max
    if not ok.any():
        return None
    v = vals[ok]
    return {
        "p95_km": float(np.percentile(v, 95)), "max_km": float(v.max()),
        "median_km": float(np.median(v)), "n_matched": int(ok.sum()),
        "n_in": int(len(vals)),
    }
