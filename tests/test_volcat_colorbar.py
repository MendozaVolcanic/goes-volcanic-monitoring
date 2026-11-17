"""Lectura inversa del PNG VOLCAT Ash_Height por BLOQUES y por OBJETO anclado.

Medido el 16-11-2026 sobre cuadros reales (docs/own_volcat/PLAN_VALIDACION_MAGNITUD.md):
  * la barra es de bloques planos: 1 km por color hasta 10 km, 2 km por color
    arriba; el borde de la barra va sombreado, así que el color se lee en sus
    filas interiores; las etiquetas 0..20
    van cada 44 px, el 0 en el borde izquierdo del bloque café;
  * la lectura lineal vieja estiraba 0..20 km sobre la parte SATURADA de la barra,
    que termina en 18 km (el bloque 18-20 es negro), y leía hasta 10 % alto;
  * en los sectores regionales (2 km) el color viene MEZCLADO con el gris del
    fondo IR, así que el color más cercano de la barra no es el correcto;
  * los cuadros con falsa detección sinóptica pintan del 12 al 49 % del sector
    en el objeto que toca el volcán; las plumas reales, hasta 1,7 %.

La fixture es la tira de leyenda de un PNG real (idéntica en los 4 sectores
comparados): sin red, sin datos crudos.
"""
from pathlib import Path

import numpy as np
from PIL import Image

FIX = Path(__file__).parent / "fixtures" / "volcat_ash_height_strip.png"

# (lo, hi) km esperados, de izquierda a derecha, leídos de las etiquetas.
BLOQUES_ESPERADOS = [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 6), (6, 7), (7, 8),
                     (8, 9), (9, 10), (10, 12), (12, 14), (14, 16), (16, 18)]

NARANJA = np.array([254.0, 166.0, 0.0])      # bloque 3-4 km
AZUL = np.array([4.0, 0.0, 255.0])           # bloque 10-12 km
VERDE_OSCURO = np.array([1.0, 101.0, 1.0])   # bloque 7-8 km


def _strip():
    return np.asarray(Image.open(FIX).convert("RGB"), dtype="float64")


def _bins():
    from src.process.volcat_colorbar import palette_bins
    return palette_bins(_strip())


# ── la barra ────────────────────────────────────────────────────────────────

def test_la_barra_real_se_lee_como_bloques_con_intervalo():
    bins = _bins()
    assert bins is not None
    assert [(b["lo_km"], b["hi_km"]) for b in bins] == BLOQUES_ESPERADOS


def test_el_azul_es_10_a_12_km_y_no_12_2():
    """La lectura lineal vieja daba 12,2 km al azul (el centro real es 11)."""
    bins = _bins()
    azul = min(bins, key=lambda b: np.linalg.norm(b["rgb"] - AZUL))
    assert (azul["lo_km"], azul["hi_km"]) == (10, 12)


def test_el_borde_sombreado_de_la_barra_no_cambia_el_color_del_bloque():
    """El borde de la barra es ~10 % más oscuro y puede quedar tan o más saturado
    que el interior. Si el color del bloque saliera de la fila MÁS saturada
    (la lectura vieja), el naranja del mapa (interior) ya no calzaría exacto."""
    from src.process.volcat_colorbar import _saturation, palette_bins
    s = _strip()
    sat = _saturation(s).mean(1)
    filas = np.where(sat >= 0.9 * sat.max())[0]
    borde = s[filas[0] - 1:filas[0]].copy()
    # más oscuro y apenas más saturado: le gana a cualquier fila interior
    borde[:] = np.clip(s[filas[len(filas) // 2]] * 0.9 - 3.0, 0, 255)
    s2 = np.vstack([s[:filas[0] - 1], borde, s[filas[0]:]])
    naranja = next(b for b in palette_bins(s2) if b["lo_km"] == 3)
    assert np.linalg.norm(naranja["rgb"] - np.array([255.0, 162.0, 0.0])) < 4


def test_sin_barra_no_inventa_bloques():
    from src.process.volcat_colorbar import palette_bins
    assert palette_bins(np.full((40, 600, 3), 200.0)) is None


# ── cada píxel ──────────────────────────────────────────────────────────────

def test_color_exacto_de_la_barra():
    from src.process.volcat_colorbar import classify_pixels
    r = classify_pixels(np.array([AZUL, VERDE_OSCURO]), _bins())
    assert r["ok"].all()
    assert list(r["lo_km"]) == [10, 7] and list(r["hi_km"]) == [12, 8]
    assert np.allclose(r["alpha"], 1.0)


def test_verde_oscuro_casi_exacto_no_se_confunde_con_verde_claro():
    """(2,99,2) es 0,4 x verde claro; por mezcla con negro daría 6-7 km."""
    from src.process.volcat_colorbar import classify_pixels
    r = classify_pixels(np.array([[2.0, 99.0, 2.0]]), _bins())
    assert r["ok"][0] and (r["lo_km"][0], r["hi_km"][0]) == (7, 8)


def test_naranja_mezclado_con_fondo_gris_sigue_siendo_3_a_4_km():
    """Caso Chillán 08-11 (sector regional): el color más cercano falla, la
    separación color + gris no."""
    from src.process.volcat_colorbar import classify_pixels, reverse_map_heights
    from src.process.volcat_colorbar import build_height_lut, extract_rainbow_bar
    px = 0.6 * NARANJA + 0.4 * np.array([60.0, 60.0, 60.0])
    r = classify_pixels(px[None, :], _bins())
    assert r["ok"][0]
    assert (r["lo_km"][0], r["hi_km"][0]) == (3, 4)
    assert abs(r["alpha"][0] - 0.6) < 0.05
    # y la lectura vieja, sobre la misma tira, NO lo ponía en 3-4 km
    s = _strip()
    lut_rgb, lut_val = build_height_lut(extract_rainbow_bar(s[:, int(0.48 * s.shape[1]):]))
    vieja, _ = reverse_map_heights(px[None, :], lut_rgb, lut_val)
    assert not (3.0 <= vieja[0] < 4.0)


def test_gris_apenas_rojizo_es_ambiguo_y_no_se_lee_como_0_a_1_km():
    """Chillán 08-11 19:00: (139,88,86) es café puro (0-1 km) o un rojo de 1-2 km
    muy diluido en gris. Los dos lo explican: no se decide por nosotros."""
    from src.process.volcat_colorbar import classify_pixels
    r = classify_pixels(np.array([[139.0, 88.0, 86.0]]), _bins())
    assert not r["ok"][0]


def test_gris_y_cian_no_son_altura():
    from src.process.volcat_colorbar import classify_pixels
    r = classify_pixels(np.array([[120.0, 120.0, 120.0], [0.0, 255.0, 255.0]]), _bins())
    assert not r["ok"].any()


# ── el objeto anclado al volcán ─────────────────────────────────────────────

def test_solo_cuenta_el_objeto_que_toca_el_volcan():
    from src.process.volcat_colorbar import anchored_object
    m = np.zeros((60, 60), bool)
    m[30:33, 30:40] = True     # nace en el volcán (30, 30)
    m[5:8, 5:8] = True         # otra nube, lejos
    obj = anchored_object(m, 30, 30, seed_radius_px=2)
    assert obj is not None and obj.sum() == 30 and not obj[5:8, 5:8].any()


def test_objeto_lejos_del_volcan_no_se_atribuye():
    from src.process.volcat_colorbar import anchored_object
    m = np.zeros((60, 60), bool)
    m[50:53, 50:53] = True
    assert anchored_object(m, 30, 30, seed_radius_px=2) is None


def _cuadro_sintetico(alto=400, ancho=1000):
    """Mapa gris + tira de leyenda real abajo, con la geometría del PNG VOLCAT
    (el mapa termina al 92 % del alto)."""
    s = _strip()
    H = int(round(s.shape[0] / (1 - 0.92))) if alto is None else alto
    img = np.full((H, ancho, 3), 90.0)
    img[H - s.shape[0]:, :, :] = s[:, :ancho]
    return img, int(0.92 * H)


def test_pluma_compacta_da_el_intervalo_del_tope():
    from src.process.volcat_colorbar import volcat_object_heights
    img, hmap = _cuadro_sintetico(alto=850)
    img[400:440, 500:560] = VERDE_OSCURO     # cuerpo 7-8 km, ~188 km²
    img[400:415, 560:575] = AZUL             # tope 10-12 km, 225 px, ~17,6 km²
    r = volcat_object_heights(img, 401, 500, px_km=0.28)
    assert "note" not in r
    assert (r["top_lo_km"], r["top_hi_km"]) == (10, 12)
    assert r["n"] == 40 * 60 + 15 * 15


def test_dos_pixeles_sueltos_no_fijan_el_tope():
    """Chillán 08-11 20:10: 2 píxeles de 16-18 km en un objeto de 2 a 4 km.
    Sector de 2 km (Chile_Central_2_km, píxel de 2,25 x 1,80 km a -36,9°)."""
    from src.process.volcat_colorbar import volcat_object_heights
    img, _ = _cuadro_sintetico(alto=850)
    img[400:404, 500:520] = VERDE_OSCURO     # 80 px de 7-8 km
    img[400, 520:522] = AZUL                 # 2 px de 10-12 km, ~8 km²
    r = volcat_object_heights(img, 401, 500, px_km=2.248, px_km_ew=1.799)
    assert (r["top_lo_km"], r["top_hi_km"]) == (7, 8)
    assert r["max_lo_km"] == 10


def test_tope_minimo_es_un_area_del_sensor_no_pixeles_del_png():
    """El mínimo del tope son ~12 km² (3 píxeles IR de 2 km de ABI, umbral
    nuestro), pasados a píxeles del PNG con el tamaño de su píxel. En un sector
    de 2 km a la latitud de Chillán son 3 píxeles (4,04 km² cada uno; 'floor'
    daría 2); en uno de 250 m a la de Sabancaya son 163 (0,0737 km²)."""
    from src.process.volcat_colorbar import TOP_MIN_AREA_KM2, top_min_px
    assert TOP_MIN_AREA_KM2 == 12.0
    assert top_min_px(2.248, 1.799) == 3
    assert top_min_px(0.2768, 0.2663) == 163
    assert top_min_px(2.0, 2.0) == 3            # justo 12 km² cuenta como firme
    assert top_min_px(2.0, 1.9) == 4            # 3,16 px: con 3 no llega al área
    assert top_min_px(50.0, 50.0) == 1          # nunca menos de un píxel


def test_ruido_de_250m_bajo_un_pixel_ir_no_fija_el_tope():
    """Sabancaya 26-10 11:50 a 13:10: píxeles IR sueltos de 16 a 18 km en un
    sector de 250 m. 100 píxeles del PNG son ~7,4 km²: menos que 3 píxeles IR.
    Con el umbral viejo (3 píxeles del PNG = 0,2 km²) fijaban el tope."""
    from src.process.volcat_colorbar import volcat_object_heights
    img, _ = _cuadro_sintetico(alto=850)
    img[400:440, 500:560] = VERDE_OSCURO     # cuerpo 7-8 km
    img[400:410, 560:570] = AZUL             # 100 px de 10-12 km
    r = volcat_object_heights(img, 401, 500, px_km=0.2768, px_km_ew=0.2663)
    assert (r["top_lo_km"], r["top_hi_km"]) == (7, 8), r
    assert r["max_lo_km"] == 10


def test_el_area_usa_el_ancho_este_oeste_del_pixel():
    """En la grilla CE el píxel mide px_km N-S pero px_km·cos(lat) E-O. A 60°
    el área es la mitad: 200 px de 0,28 x 0,14 km (7,8 km²) no fijan el tope,
    aunque con px_km² (15,7 km²) sí lo harían."""
    from src.process.volcat_colorbar import volcat_object_heights
    img, _ = _cuadro_sintetico(alto=850)
    img[400:440, 500:560] = VERDE_OSCURO
    img[400:410, 560:580] = AZUL             # 200 px de 10-12 km
    r = volcat_object_heights(img, 401, 500, px_km=0.28, px_km_ew=0.14)
    assert (r["top_lo_km"], r["top_hi_km"]) == (7, 8), r


def test_manto_del_tamano_del_sector_no_es_pluma():
    """Caso Sabancaya/Ubinas/Copahue 16-11 09:50: un manto que toca el volcán."""
    from src.process.volcat_colorbar import volcat_object_heights
    img, hmap = _cuadro_sintetico(alto=850)
    img[100:600, 100:900] = AZUL
    r = volcat_object_heights(img, 300, 500, px_km=0.28)
    assert r.get("sector_wide") is True and "note" in r


def test_sin_objeto_en_el_volcan_lo_dice():
    from src.process.volcat_colorbar import volcat_object_heights
    img, _ = _cuadro_sintetico(alto=850)
    img[100:104, 100:104] = AZUL
    r = volcat_object_heights(img, 400, 500, px_km=0.28)
    assert "note" in r and "top_lo_km" not in r
