# ════════════════════════════════════════════════════════════════════
# FICHA SDA · volcat_colorbar.py · SDA: Monitoreo Volcánico GOES-19 · ID: SDA-GOES-01
# Objetivo      : leer la altura VOLCAT del PNG de SSEC como REFERENCIA de validación de la altura propia (no se muestra al operador)
# Lógica        : barra por bloques discretos → color de cada píxel (exacto, o separado de un fondo gris) → objeto que toca el volcán → intervalo del tope
# Modelo/método : determinístico (componentes conexas + mínimos cuadrados de 2 incógnitas por color), sin ML
# Datos entrada : PNG Ash_Height de VOLCAT (SSEC/CIMSS, público), SIN datos personales
# Variables     : radio de anclaje 10 km, manto > 5 % del sector, tope ≥ 3 px, tolerancias de color (umbrales nuestros, declarados abajo)
# Limitaciones  : la barra es discreta (1 km hasta 10 km, 2 km arriba); en sectores de 2 km 1-2 y 2-3 km no se separan; depende de la paleta SSEC
# Refs/datos    : Pavolonis et al. 2013 (VOLCAT); medición propia 16-11-2026 sobre 989 cuadros
# Ficha completa: docs/FICHA_SDA_GOES.md (§C)
# ════════════════════════════════════════════════════════════════════
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

import math

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


# ════════════════════════════════════════════════════════════════════════════
# Lectura por BLOQUES y por OBJETO anclado al volcán (paso 1 del plan de
# validación de magnitud, nov-2026). Reemplaza al LUT lineal de arriba en
# `volcat_height_at`; las funciones viejas quedan por compatibilidad.
#
# Por qué: medido el 16-11-2026 sobre cuadros reales
# (docs/own_volcat/PLAN_VALIDACION_MAGNITUD.md):
#   * la barra NO es un degradado: son bloques planos de 1 km hasta 10 km y de
#     2 km arriba. El LUT lineal estiraba 0..20 km sobre la parte saturada, que
#     termina en 18 km (el bloque 18-20 es negro), y leía hasta 10 % alto
#     (el azul de 10-12 km salía 12,2);
#   * en los sectores regionales de 2 km el color viene MEZCLADO con el gris del
#     fondo IR (remuestreo de SSEC): el color de barra más cercano a un naranja
#     apagado no es el naranja;
#   * los cuadros con falsa detección sinóptica pintan medio sector; contar
#     píxeles de color en una caja no los distingue de una pluma.
# ════════════════════════════════════════════════════════════════════════════

BIN_SAME_TOL = 6.0     # suma |ΔRGB| para seguir dentro del mismo bloque (el interior
                       # de un bloque es plano; entre bloques vecinos la diferencia es > 50)
BIN_MIN_PX = 12        # un bloque mide ≥ 19 px; las transiciones, 1 a 2 px
BIN_SAT_MIN = 0.25     # saturación mínima de un bloque (el café 0-1 km tiene 0,57)
EXACT_TOL = 8.0        # distancia RGB para "color exacto de la barra" (medido ≤ 7)
UNMIX_RES_MAX = 10.0   # residuo RGB máximo del ajuste color + gris (umbral nuestro)
UNMIX_ALPHA_MIN = 0.35  # fracción mínima de color de barra en un píxel mezclado (nuestro)
SEED_RADIUS_KM = 10.0  # el objeto tiene que tocar este disco alrededor del volcán (nuestro):
                       # cubre el paralaje de GOES-East (0,4 a 1,5 km al sur por km de
                       # altura en Chile) para topes de ~6 km, más un píxel de georef
MAX_SECTOR_FRAC = 0.05  # objeto > 5 % del mapa ⇒ manto sinóptico, no pluma (nuestro;
                        # medido: plumas ≤ 1,7 %, mantos del 16-11 de 12 a 49 %)
MAP_FRAC = 0.92        # el mapa ocupa el 92 % superior del PNG; abajo, la leyenda
TOP_MIN_AREA_KM2 = 12.0  # área mínima de un bloque para fijar el tope (nuestro):
                         # 3 píxeles IR de ABI de 2 km. Es un área del SENSOR, no
                         # una cuenta de píxeles del PNG: en un sector de 250 m un
                         # píxel IR son ~7 x 7 del PNG, y "3 píxeles del PNG"
                         # (0,2 km²) dejaba pasar ruido de 16 a 18 km (Sabancaya
                         # 26-10). Se pasa a píxeles del PNG con top_min_px.


def top_min_px(px_km: float, px_km_ew: float) -> int:
    """Píxeles del PNG que suman TOP_MIN_AREA_KM2, redondeado hacia arriba.

    ``px_km`` es el lado N-S del píxel y ``px_km_ew`` el E-O; en la grilla CE de
    SSEC el E-O es px_km·cos(lat). Hacia arriba: 2,97 píxeles de Chillán (sector
    de 2 km) son 3, no 2, porque con 2 el bloque no llega al área.
    """
    return math.ceil(TOP_MIN_AREA_KM2 / (px_km * px_km_ew))


def _saturation(a):
    mx, mn = a.max(-1), a.min(-1)
    with np.errstate(invalid="ignore", divide="ignore"):
        return np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-9), 0.0)


def palette_bins(strip_rgb) -> Optional[list]:
    """Bloques de la barra Ash_Height: lista de ``{rgb, lo_km, hi_km}`` de
    izquierda a derecha, o None si no hay barra. PURA.

    La escala sale de la propia barra, no de constantes: los diez primeros
    bloques son de 1 km, así que la mediana de la distancia entre sus inicios
    da los px por km (22 en los PNG de nov-2026) y el borde izquierdo del
    primero es 0 km. Cada borde se redondea al km entero: las etiquetas de la
    barra (0, 2, ..., 20) caen justo en los bordes de bloque.
    """
    a = np.asarray(strip_rgb, dtype="float64")
    sat_fila = _saturation(a).mean(1)
    if sat_fila.max() < BIN_SAT_MIN:
        return None
    # El borde de la barra va sombreado (medido: la fila de arriba sale ~10 %
    # más oscura). La mediana de las filas de la barra da el color interior,
    # que es el que SSEC pinta en el mapa.
    filas = sat_fila >= 0.9 * sat_fila.max()
    r = np.median(a[filas], axis=0)
    runs, start = [], 0
    for i in range(1, len(r) + 1):
        if i == len(r) or np.abs(r[i] - r[start]).sum() > BIN_SAME_TOL:
            runs.append((start, i - 1))
            start = i
    pl = [(s, e) for s, e in runs
          if e - s + 1 >= BIN_MIN_PX and _saturation(r[s]) >= BIN_SAT_MIN]
    if len(pl) < 10:
        return None
    starts = np.array([s for s, _ in pl[:10]], dtype="float64")
    ppk = float(np.median(np.diff(starts)))
    if ppk <= 0:
        return None
    x0 = pl[0][0]
    return [{"rgb": r[s].copy(),
             "lo_km": int(round((s - x0) / ppk)),
             "hi_km": int(round((e + 1 - x0) / ppk))} for s, e in pl]


def classify_pixels(rgb, bins) -> dict:
    """Bloque de altura de cada píxel. PURA.

    1) color EXACTO de la barra (distancia ≤ EXACT_TOL): ese bloque, alpha = 1.
       Va primero porque la mezcla con negro hace colineales a colores de la
       barra (el verde oscuro 7-8 km es 0,4 x el verde claro 6-7 km).
    2) si no, separación ``px ≈ alpha·color + gris`` (el remuestreo de SSEC mezcla
       la pluma con el fondo IR, que es gris). Se acepta el bloque de menor
       residuo si el residuo ≤ UNMIX_RES_MAX, alpha ≥ UNMIX_ALPHA_MIN y ningún
       OTRO intervalo ajusta igual de bien (si dos ajustan, el píxel es ambiguo
       y se descarta: no elegimos nosotros).

    Devuelve arrays ``lo_km``, ``hi_km``, ``alpha``, ``ok`` (bool).
    """
    px = np.asarray(rgb, dtype="float64").reshape(-1, 3)
    P = np.array([b["rgb"] for b in bins], dtype="float64")
    lo = np.array([b["lo_km"] for b in bins])
    hi = np.array([b["hi_km"] for b in bins])
    n = len(px)
    out_lo = np.full(n, -1)
    out_hi = np.full(n, -1)
    alpha = np.zeros(n)
    ok = np.zeros(n, bool)

    d = np.sqrt(((px[:, None, :] - P[None]) ** 2).sum(-1))
    k = d.argmin(1)
    exact = d[np.arange(n), k] <= EXACT_TOL
    out_lo[exact], out_hi[exact] = lo[k[exact]], hi[k[exact]]
    alpha[exact], ok[exact] = 1.0, True

    rest = np.where(~exact)[0]
    if len(rest):
        y = px[rest]                                     # (m,3)
        pp = (P * P).sum(1)                              # (K,)
        sp = P.sum(1)                                    # (K,)
        py = y @ P.T                                     # (m,K)
        sy = y.sum(1)[:, None]                           # (m,1)
        det = 3.0 * pp - sp ** 2                         # (K,)
        with np.errstate(invalid="ignore", divide="ignore"):
            a_ = (3.0 * py - sp * sy) / det              # alpha por bloque
            b_ = (pp * sy - sp * py) / det               # gris por bloque
        fit = a_[:, :, None] * P[None] + b_[:, :, None]  # (m,K,3)
        res = np.sqrt(((y[:, None, :] - fit) ** 2).sum(-1))
        valid = ((a_ >= UNMIX_ALPHA_MIN) & (a_ <= 1.05) & (b_ >= -5.0)
                 & (res <= UNMIX_RES_MAX))
        res_v = np.where(valid, res, np.inf)
        kb = res_v.argmin(1)
        m_idx = np.arange(len(rest))
        good = np.isfinite(res_v[m_idx, kb])
        # ambiguo: otro bloque con OTRO intervalo también explica el color, con
        # CUALQUIER proporción de color (no sólo ≥ alpha mínimo). Caso Chillán
        # 08-11: (139,88,86) es café puro (0-1 km) o rojo 1-2 km muy diluido.
        alt = (a_ > 0.05) & (a_ <= 1.05) & (b_ >= -5.0) & (res <= UNMIX_RES_MAX)
        otro = alt & (lo[None, :] != lo[kb][:, None])
        good &= ~otro.any(1)
        g = rest[good]
        out_lo[g], out_hi[g] = lo[kb[good]], hi[kb[good]]
        alpha[g] = a_[m_idx[good], kb[good]]
        ok[g] = True
    return {"lo_km": out_lo, "hi_km": out_hi, "alpha": alpha, "ok": ok}


def _etiquetas(m, gap_px: int):
    """Componentes conexas (8 vecinos) de ``m`` dilatada con un disco de radio
    ``gap_px`` (sin dilatar si es 0). Devuelve ``(lab, n)``."""
    from scipy import ndimage
    if gap_px > 0:
        yy, xx = np.mgrid[-gap_px:gap_px + 1, -gap_px:gap_px + 1]
        m = ndimage.binary_dilation(m, structure=(yy ** 2 + xx ** 2 <= gap_px ** 2))
    return ndimage.label(m, structure=np.ones((3, 3), int))


def anchored_object(mask, row: int, col: int, seed_radius_px: int,
                    gap_px: int = 0, etiquetas=None):
    """Componentes conexas (8 vecinos) de ``mask`` que tocan el disco de radio
    ``seed_radius_px`` alrededor de (row, col), o None si ninguna lo toca. PURA.

    Una nube que no toca el volcán no se le atribuye: es conservador (un pulso
    ya desprendido queda afuera) pero no confunde nubes vecinas con la pluma.

    ``gap_px`` > 0 une los pedazos separados por huecos de hasta ese radio
    antes de etiquetar (dilatación con un disco), y devuelve sólo los píxeles
    ORIGINALES del sistema unido. Por qué: un sistema grande sale roto al
    decodificarlo, porque el bloque de 18 a 20 km de la barra es negro (no se
    separa del suelo caliente, también negro en el IR) y los píxeles mezclados
    ambiguos se descartan. Medido el 19-11-2026 en Chillán 16-11 de 08:30 a
    09:30 UTC: sin unir, el objeto anclado medía 8 a 49 km² (una "pluma"); con
    un píxel de unión era el sistema de ~87.000 a 102.000 km² que estaba al
    lado. Un píxel ANCLADO sigue siendo obligatorio: la unión no ancla nada que
    no toque el disco.

    ``etiquetas``: ``_etiquetas(mask, gap_px)`` ya calculadas para este cuadro.
    La dilatación y el etiquetado no dependen del volcán: con ``mapa`` en
    ``volcat_object_heights`` se hacen una vez por cuadro, no una por volcán.
    """
    m = np.asarray(mask, bool)
    lab, n = etiquetas if etiquetas is not None else _etiquetas(m, gap_px)
    if n == 0:
        return None
    H, W = m.shape
    r0, r1 = max(0, row - seed_radius_px), min(H, row + seed_radius_px + 1)
    c0, c1 = max(0, col - seed_radius_px), min(W, col + seed_radius_px + 1)
    if r1 <= r0 or c1 <= c0:
        return None
    yy, xx = np.mgrid[r0:r1, c0:c1]
    disco = (yy - row) ** 2 + (xx - col) ** 2 <= seed_radius_px ** 2
    # Sólo anclan los píxeles de color REALES dentro del disco: la dilatación
    # no puede inventar un anclaje.
    ids = np.unique(lab[r0:r1, c0:c1][disco & m[r0:r1, c0:c1]])
    ids = ids[ids > 0]
    if len(ids) == 0:
        return None
    return np.isin(lab, ids) & m


def clasificar_mapa(img_rgb) -> Optional[dict]:
    """Bloque de altura de cada píxel del MAPA de un PNG Ash_Height. PURA.

    Es la parte cara de la lectura y no depende del volcán: la señal del
    dashboard la hace una vez por cuadro y ancla después cada volcán del sector
    (``volcat_object_heights(..., mapa=...)``). Devuelve ``{ok, lo_km, hi_km,
    alpha}`` (arrays del alto del mapa, el 92 % superior del PNG) o None si no
    hay barra que leer.
    """
    a = np.asarray(img_rgb, dtype="float64")
    H = a.shape[0]
    hmap = int(MAP_FRAC * H)
    bins = palette_bins(a[hmap:])
    if bins is None:
        return None
    m = a[:hmap]
    cand = _saturation(m) >= 0.2
    okmask = np.zeros(cand.shape, bool)
    lo_map = np.full(cand.shape, -1)
    hi_map = np.full(cand.shape, -1)
    al_map = np.zeros(cand.shape)
    if cand.any():
        c = classify_pixels(m[cand], bins)
        okmask[cand], lo_map[cand] = c["ok"], c["lo_km"]
        hi_map[cand], al_map[cand] = c["hi_km"], c["alpha"]
    return {"ok": okmask, "lo_km": lo_map, "hi_km": hi_map, "alpha": al_map}


def volcat_object_heights(img_rgb, row: int, col: int, px_km: float,
                          px_km_ew: float | None = None,
                          seed_radius_km: float = SEED_RADIUS_KM,
                          max_sector_frac: float = MAX_SECTOR_FRAC,
                          mapa: dict | None = None,
                          gap_km: float = 0.0) -> dict:
    """Altura VOLCAT del objeto que toca el volcán en un PNG Ash_Height. PURA.

    ``row, col``: píxel del volcán; ``px_km``: lado N-S del píxel y
    ``px_km_ew`` el E-O (por defecto igual a ``px_km``). Devuelve
    ``{top_lo_km, top_hi_km, n_top, p95_mid_km, median_mid_km, n, n_mezclados,
    frac_sector}`` o ``{"note": ...}`` (sin barra, volcán fuera, sin objeto, o
    manto del tamaño del sector, este último con ``sector_wide: True``).

    Toda salida lleva ``motivo``, legible por máquina, para que quien la use no
    tenga que reconocer el texto de ``note``: ``sin_barra``, ``fuera``,
    ``sin_objeto``, ``manto``, ``sin_tope`` (objeto anclado sin un bloque que
    llegue al área mínima) o ``tope``. La señal de detección del dashboard
    (``src/process/volcat_deteccion.py``) decide con él.

    El tope se informa como INTERVALO del bloque más alto (la barra es discreta:
    1 km hasta 10 km, 2 km arriba), no como un número con decimales que no tiene.
    """
    mapa = clasificar_mapa(img_rgb) if mapa is None else mapa
    if mapa is None:
        return {"note": "no se pudo leer la barra de altura del PNG",
                "motivo": "sin_barra"}
    okmask, lo_map = mapa["ok"], mapa["lo_km"]
    hi_map, al_map = mapa["hi_km"], mapa["alpha"]
    hmap, W = okmask.shape
    if not (0 <= row < hmap and 0 <= col < W):
        return {"note": "el volcán cae fuera del mapa del sector",
                "motivo": "fuera"}
    seed = max(1, int(round(seed_radius_km / px_km)))
    gap = max(1, int(round(gap_km / px_km))) if gap_km > 0 else 0
    etq = None
    if mapa is not None:
        cache = mapa.setdefault("_etiquetas", {})
        if gap not in cache:
            cache[gap] = _etiquetas(okmask, gap)
        etq = cache[gap]
    obj = anchored_object(okmask, int(row), int(col), seed, gap_px=gap,
                          etiquetas=etq)
    if obj is None:
        return {"note": "VOLCAT no dibuja ningún objeto que toque el volcán "
                        f"(radio {seed_radius_km:g} km)",
                "motivo": "sin_objeto"}
    frac = float(obj.sum()) / obj.size
    if frac > max_sector_frac:
        return {"note": f"objeto VOLCAT cubre {frac:.0%} del sector: manto "
                        "sinóptico, no una pluma",
                "sector_wide": True, "frac_sector": frac,
                "n": int(obj.sum()), "motivo": "manto"}
    lo_o, hi_o, al_o = lo_map[obj], hi_map[obj], al_map[obj]
    # Tope = bloque más alto que cubre al menos TOP_MIN_AREA_KM2 (3 píxeles IR):
    # menos que eso es ruido del retrieval, no un tope (Chillán 08-11 20:10: 2 px
    # de 16-18 km en un objeto de 2 a 4 km; Sabancaya 26-10: píxeles IR sueltos
    # de 16 a 18 km sobre fondo cálido). El máximo crudo va aparte.
    min_px = top_min_px(px_km, px_km if px_km_ew is None else px_km_ew)
    niveles, cuenta = np.unique(lo_o, return_counts=True)
    firmes = niveles[cuenta >= min_px]
    if len(firmes) == 0:
        return {"note": f"objeto VOLCAT de {int(obj.sum())} píxeles: ningún "
                        f"bloque llega a {TOP_MIN_AREA_KM2:g} km² ({min_px} "
                        "píxeles del cuadro), no fija un tope",
                "n": int(obj.sum()), "max_lo_km": int(lo_o.max()),
                "motivo": "sin_tope"}
    top = firmes.max()
    mid = (lo_o + hi_o) / 2.0
    return {
        "top_lo_km": int(top), "top_hi_km": int(hi_o[lo_o == top].max()),
        "n_top": int((lo_o == top).sum()), "max_lo_km": int(lo_o.max()),
        "p95_mid_km": float(np.percentile(mid, 95)),
        "median_mid_km": float(np.median(mid)),
        "n": int(obj.sum()), "n_mezclados": int((al_o < 1.0).sum()),
        "frac_sector": frac, "motivo": "tope",
    }
