"""Señal por volcán "VOLCAT detecta un objeto anclado al cráter" (nov-2026).

Por qué existe, antes que el cómo: nuestro detector split-window no ve las
plumas débiles de Chillán que VOLCAT (SSEC/CIMSS) sí dibuja, y no se puede
reproducir VOLCAT. Se usa como capa de detección. El peligro de una capa así
es doble: que un "VOLCAT no dibujó nada" por falla de SSEC se lea como calma,
y que un sistema meteorológico pintado por VOLCAT se lea como pluma. Estas
pruebas cuidan las dos cosas, más la georreferencia que ancla cada volcán.

La georreferencia se comprobó el 19-11-2026 contra la capa de volcanes de SSEC
(VOLCANOES.CYAN): los 44 volcanes chilenos caen a 0 a 2 píxeles del marcador
de SSEC, incluidos los 9 del sector estereográfico polar.
"""
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

FIX = Path(__file__).parent / "fixtures" / "volcat_ash_height_strip.png"
NARANJA = (255, 160, 1)      # bloque 3-4 km
AZUL = (3, 0, 255)           # bloque 10-12 km
AHORA = datetime(2026, 11, 19, 13, 0, tzinfo=timezone.utc)

# Georef tal cual la entrega SSEC (listado del 19-11-2026).
CE_CENTRAL = {"PROJECTION": "CE", "REF_LON": 289, "ORIGIN_LAT": -31.8007698059082,
              "ORIGIN_LON": 278.9210815429688, "EQ_RADIUS": 206264.796875,
              "SCALE_FACTOR": 72.80000305175781, "OFFSET_X": 0, "OFFSET_Y": 36}
PS_SUR = {"PROJECTION": "PS", "SECOND_REF_LAT": -60, "REF_LON": 292,
          "ORIGIN_LAT": -39.8007698059082, "ORIGIN_LON": 277.2214965820312,
          "EQ_RADIUS": 6378137, "ECCENT": 0.08181919157505035,
          "SCALE_FACTOR": 2240, "NH_HEMISPHERE": 0, "OFFSET_X": 0,
          "OFFSET_Y": 36}
CHILLAN = (-36.86, -71.38)
HUDSON = (-45.90, -72.97)


def _png(pintar=None, alto=821, ancho=1000):
    """Cuadro VOLCAT sintético: mapa gris + tira de leyenda real abajo."""
    strip = np.asarray(Image.open(FIX).convert("RGB"), dtype="float64")
    img = np.full((alto, ancho, 3), 90.0)
    img[alto - strip.shape[0]:] = strip[:, :ancho]
    if pintar:
        pintar(img)
    return img


# ── georreferencia ──────────────────────────────────────────────────────────

def test_georef_ce_chillan_cae_en_su_pixel_y_mide_el_pixel_en_km():
    """SCALE_FACTOR CE está en segundos de arco (EQ_RADIUS = 206264,8), no en
    km: tomarlo como km daría un píxel de 72,8 km."""
    from src.process.volcat_deteccion import georef_pixel
    g = georef_pixel(CE_CENTRAL, *CHILLAN)
    assert (g["row"], g["col"]) == (286, 480)
    assert g["px_km"] == pytest.approx(2.248, abs=0.01)
    assert g["px_km_ew"] == pytest.approx(
        g["px_km"] * np.cos(np.radians(CHILLAN[0])))


def test_georef_ps_hudson_cae_donde_ssec_pone_su_marcador():
    """Chile_South_2_km es estereográfica polar: un cálculo lineal en grados
    corre el volcán decenas de km. (298, 449) es el píxel del marcador de
    Hudson en la capa de volcanes de SSEC del 19-11-2026."""
    from src.process.volcat_deteccion import georef_pixel
    g = georef_pixel(PS_SUR, *HUDSON)
    assert abs(g["row"] - 298) <= 1 and abs(g["col"] - 449) <= 1
    # SCALE_FACTOR PS son metros en el plano (2.240 m), fiel a -60°; a -46°
    # el píxel en el terreno es algo menor.
    assert 1.9 < g["px_km"] < 2.24 and 1.9 < g["px_km_ew"] < 2.24


@pytest.mark.parametrize("coords", [
    {}, {"PROJECTION": "CE"}, {"PROJECTION": "XYZ", "ORIGIN_LAT": 0,
                               "ORIGIN_LON": 0, "SCALE_FACTOR": 1},
    {**CE_CENTRAL, "EQ_RADIUS": 0},
])
def test_georef_inutilizable_devuelve_none(coords):
    from src.process.volcat_deteccion import georef_pixel
    assert georef_pixel(coords, *CHILLAN) is None


# ── lectura del cuadro ──────────────────────────────────────────────────────

def test_pluma_anclada_en_chillan_se_lee_con_area_en_km2():
    from src.process.volcat_deteccion import leer_objeto_anclado

    def pluma(img):
        img[286:289, 480:488] = NARANJA          # 24 px de 3-4 km
    r = leer_objeto_anclado(_png(pluma), CE_CENTRAL, *CHILLAN)
    assert r["motivo"] == "tope" and (r["top_lo_km"], r["top_hi_km"]) == (3, 4)
    assert r["area_km2"] == pytest.approx(24 * 2.248 * 2.248 * 0.8004, rel=0.01)


def test_pluma_anclada_en_hudson_se_lee_en_el_sector_polar():
    from src.process.volcat_deteccion import leer_objeto_anclado

    def pluma(img):
        img[298:301, 449:457] = NARANJA
    r = leer_objeto_anclado(_png(pluma), PS_SUR, *HUDSON)
    assert r["motivo"] == "tope" and r["n"] == 24


def test_la_clasificacion_compartida_da_lo_mismo_que_la_propia():
    """El dashboard clasifica el cuadro UNA vez por sector y ancla cada volcán
    sobre esa clasificación: tiene que dar lo mismo que clasificar cada vez."""
    from src.process.volcat_colorbar import clasificar_mapa
    from src.process.volcat_deteccion import leer_objeto_anclado

    def pluma(img):
        img[286:289, 480:488] = NARANJA
        img[100:103, 600:620] = AZUL
    img = _png(pluma)
    mapa = clasificar_mapa(img)
    assert (leer_objeto_anclado(img, CE_CENTRAL, *CHILLAN, mapa=mapa)
            == leer_objeto_anclado(img, CE_CENTRAL, *CHILLAN))


def _pedazo_y_sistema(img):
    """Chillán 16-11 08:30 UTC en chico: un pedazo que sale del cráter hacia
    el oeste (filas 286-288, columnas 470-488, 57 px; el disco de 10 km son
    4 px alrededor de la columna 480) y, separado por TRES columnas (467 a
    469, el negro de 18-20 km que no se puede leer; Taapaca 19-11 12:30 UTC
    quedaba a 3 px del sistema), el sistema del que es parte, que no toca el
    disco."""
    img[286:289, 470:489] = AZUL               # pedazo anclado, 57 px
    img[200:600, 100:467] = AZUL               # sistema, fuera del disco


def test_un_pedazo_de_un_sistema_grande_no_se_lee_como_pluma():
    from src.process.volcat_deteccion import evaluar_senal, leer_objeto_anclado
    r = leer_objeto_anclado(_png(_pedazo_y_sistema), CE_CENTRAL, *CHILLAN)
    assert r.get("motivo") == "manto" and r["n"] == 57 + 400 * 367, r
    s = evaluar_senal(r, AHORA - timedelta(minutes=40), ahora=AHORA)
    assert s["estado"] == "extenso"


def test_sin_union_el_mismo_pedazo_pasaba_por_pluma():
    """Línea base roja: con la lectura de un cuadro sin unión (la de
    validación), el pedazo mide 57 px (~230 km²) y sería 'detecta'."""
    from src.process.volcat_colorbar import volcat_object_heights
    from src.process.volcat_deteccion import georef_pixel
    g = georef_pixel(CE_CENTRAL, *CHILLAN)
    r = volcat_object_heights(_png(_pedazo_y_sistema), g["row"], g["col"],
                              px_km=g["px_km"], px_km_ew=g["px_km_ew"])
    assert r["n"] == 57


def test_la_union_no_ancla_un_sistema_que_no_toca_el_crater():
    """La dilatación no inventa anclaje: un sistema que empieza justo afuera
    del disco de 10 km (1 px), sin píxel adentro, no se atribuye al volcán,
    aunque dilatado sí lo tocaría."""
    from src.process.volcat_deteccion import georef_pixel, leer_objeto_anclado
    g = georef_pixel(CE_CENTRAL, *CHILLAN)
    seed = int(round(10.0 / g["px_km"]))      # 4 px

    def cerca(img):
        img[g["row"] + seed + 1:g["row"] + seed + 40, 300:700] = AZUL
    r = leer_objeto_anclado(_png(cerca), CE_CENTRAL, *CHILLAN)
    assert r["motivo"] == "sin_objeto", r


def test_la_union_va_en_km_y_no_en_pixeles_del_cuadro():
    """6 km son 3 píxeles en un sector de 2 km y 22 en uno de 250 m: el
    hueco de un sistema roto mide lo mismo en el terreno en los dos."""
    from src.process.volcat_colorbar import volcat_object_heights
    from src.process.volcat_deteccion import UNION_GAP_KM
    assert UNION_GAP_KM == 6.0

    def separado_20px(img):
        # pedazo que sale del cráter (401, 500) hacia el sur y pasa el disco
        # de anclaje (36 px en 250 m, 4 px en 2 km); el otro bloque empieza
        # 20 px más abajo, fuera del disco en las dos escalas.
        img[400:441, 500:508] = NARANJA        # 41 x 8 = 328 px
        img[461:490, 450:600] = NARANJA        # 29 x 150 px
    img = _png(separado_20px, alto=850)
    # 250 m: 6 km = 22 px de unión, el hueco de 20 px (5,5 km) se cierra
    r250 = volcat_object_heights(img, 401, 500, px_km=0.2768, px_km_ew=0.22,
                                 gap_km=UNION_GAP_KM)
    # 2 km: 6 km = 3 px de unión, el hueco de 20 px (45 km) no se cierra
    r2 = volcat_object_heights(img, 401, 500, px_km=2.248, px_km_ew=1.8,
                               gap_km=UNION_GAP_KM)
    assert r250["n"] == 328 + 29 * 150, r250
    assert r2["n"] == 328, r2


def test_la_etiqueta_por_cuadro_da_lo_mismo_que_la_de_cada_volcan():
    """Con `mapa` la unión se etiqueta una vez por cuadro y se reutiliza."""
    from src.process.volcat_colorbar import clasificar_mapa
    from src.process.volcat_deteccion import leer_objeto_anclado
    img = _png(_pedazo_y_sistema)
    mapa = clasificar_mapa(img)
    a = leer_objeto_anclado(img, CE_CENTRAL, *CHILLAN, mapa=mapa)
    b = leer_objeto_anclado(img, CE_CENTRAL, *CHILLAN, mapa=mapa)  # memo
    assert a == b == leer_objeto_anclado(img, CE_CENTRAL, *CHILLAN)
    assert list(mapa["_etiquetas"]) == [3]


def test_sin_georef_la_lectura_lo_dice():
    from src.process.volcat_deteccion import leer_objeto_anclado
    r = leer_objeto_anclado(_png(), {}, *CHILLAN)
    assert r["motivo"] == "sin_georef"


# ── estados ─────────────────────────────────────────────────────────────────

def _lect(motivo, area=None, **kw):
    d = {"motivo": motivo, "note": f"nota {motivo}"}
    if area is not None:
        d["area_km2"] = area
    d.update(kw)
    return d


def _ev(lectura, edad_min=40, error=None):
    from src.process.volcat_deteccion import evaluar_senal
    return evaluar_senal(lectura, AHORA - timedelta(minutes=edad_min),
                         ahora=AHORA, error=error)


def test_sin_cuadro_no_es_sin_deteccion():
    """SSEC caído: nunca "sin detección". Ausencia de dato no es calma."""
    from src.process.volcat_deteccion import evaluar_senal
    s = evaluar_senal(None, None, ahora=AHORA,
                      error="SSEC no respondió o no publicó cuadros del sector")
    assert s["estado"] == "no_disponible" and "SSEC" in s["motivo"]


def test_un_error_manda_sobre_cualquier_lectura():
    """Si quien llama sabe que algo falló, una lectura vieja no lo tapa."""
    s = _ev(_lect("sin_objeto"), error="no se pudo leer el cuadro VOLCAT")
    assert s["estado"] == "no_disponible"
    assert s["motivo"] == "no se pudo leer el cuadro VOLCAT"


def test_png_que_no_bajo_es_no_disponible_aunque_haya_hora():
    s = _ev(None, error="no se pudo bajar el cuadro VOLCAT")
    assert s["estado"] == "no_disponible" and s["edad_min"] == 40


@pytest.mark.parametrize("motivo", ["sin_barra", "fuera", "sin_georef", None,
                                    "algo_nuevo"])
def test_lectura_que_no_se_pudo_hacer_es_no_disponible(motivo):
    assert _ev(_lect(motivo))["estado"] == "no_disponible"


def test_sin_objeto_con_cuadro_al_dia_es_el_estado_normal():
    assert _ev(_lect("sin_objeto"), edad_min=40)["estado"] == "sin_deteccion"


def test_sin_objeto_con_cuadro_viejo_es_atrasado():
    """El límite es el de `alerta_edad` para VOLCAT (120 min): SSEC tarda 30 a
    50 min por diseño, y eso no es una caída."""
    from src.process.volcat_deteccion import VOLCAT_ATRASO_MIN
    assert VOLCAT_ATRASO_MIN == 120
    assert _ev(_lect("sin_objeto"), edad_min=119)["estado"] == "sin_deteccion"
    assert _ev(_lect("sin_objeto"), edad_min=120)["estado"] == "atrasado"


def test_pluma_tipica_de_chillan_es_deteccion():
    """La pluma anclada más grande de Chillán del 01 al 16-11 midió ~270 km²."""
    s = _ev(_lect("tope", 270.0, top_lo_km=3, top_hi_km=5))
    assert s["estado"] == "detecta"
    assert (s["top_lo_km"], s["top_hi_km"]) == (3, 5)


def test_deteccion_vieja_sigue_siendo_deteccion_con_su_edad():
    """Como un hot spot: el dato existe y se muestra, con su hora."""
    s = _ev(_lect("tope", 270.0), edad_min=300)
    assert s["estado"] == "detecta" and s["edad_min"] == 300


def test_objeto_sin_tope_fijo_tambien_es_deteccion():
    """Objeto anclado de 16 km² con píxeles repartidos en varios bloques: no
    fija un tope, pero VOLCAT dibujó algo que toca el cráter."""
    s = _ev(_lect("sin_tope", 16.0))
    assert s["estado"] == "detecta" and s["top_lo_km"] is None


def test_ruido_bajo_tres_pixeles_ir_no_es_deteccion():
    from src.process.volcat_deteccion import AREA_MIN_KM2
    assert AREA_MIN_KM2 == 12.0
    assert _ev(_lect("sin_tope", 11.9))["estado"] == "sin_deteccion"
    assert _ev(_lect("tope", 12.0))["estado"] == "detecta"


def test_ruido_viejo_tambien_es_atrasado():
    assert _ev(_lect("sin_tope", 4.0), edad_min=200)["estado"] == "atrasado"


def test_objeto_mas_grande_que_toda_pluma_medida_es_extenso():
    """Chillán 16-11: un sistema de ~126.000 km² pasó el 5 % del sector de
    2 km y daba tope de 16 a 18 km. No se descarta: se marca aparte."""
    from src.process.volcat_deteccion import AREA_EXTENSO_KM2
    assert AREA_EXTENSO_KM2 == 2000.0
    assert _ev(_lect("tope", 2000.0))["estado"] == "detecta"
    s = _ev(_lect("tope", 2000.1, top_lo_km=16, top_hi_km=18))
    assert s["estado"] == "extenso" and s["top_lo_km"] == 16


def test_manto_del_sector_es_extenso_y_lo_marca():
    s = _ev(_lect("manto", 300000.0, frac_sector=0.09, sector_wide=True))
    assert s["estado"] == "extenso" and s["manto"] is True


def test_extenso_viejo_no_pasa_a_atrasado():
    assert _ev(_lect("manto", 9e4, frac_sector=0.2), edad_min=500)["estado"] == "extenso"


# ── presentación ────────────────────────────────────────────────────────────

def _estado(estado, **kw):
    from dashboard.map_helpers import estado_volcat
    base = {"estado": estado, "edad_min": 40, "area_km2": None,
            "top_lo_km": None, "top_hi_km": None, "frac_sector": None,
            "manto": False, "motivo": None,
            "etiqueta_sector": "Chile Central 2 km (regional 2 km)"}
    base.update(kw)
    return estado_volcat(base)


def test_solo_sin_deteccion_es_verde():
    from dashboard.map_helpers import COLOR_CALMA
    verdes = [e for e in ("detecta", "extenso", "sin_deteccion", "atrasado",
                          "no_disponible")
              if _estado(e, area_km2=100.0)["color"] == COLOR_CALMA]
    assert verdes == ["sin_deteccion"]


def test_no_disponible_es_gris_y_dice_que_no_descarta_ceniza():
    from dashboard.map_helpers import COLOR_SIN_DATO
    e = _estado("no_disponible", motivo="SSEC no respondió")
    assert e["color"] == COLOR_SIN_DATO and e["verificado"] is False
    assert "No descarta ceniza" in e["detalle"] and "SSEC no respondió" in e["detalle"]


def test_todo_estado_nombra_el_sector_y_la_edad():
    for est in ("detecta", "extenso", "sin_deteccion", "atrasado"):
        d = _estado(est, area_km2=100.0, edad_min=47)["detalle"]
        assert "regional 2 km" in d, est
        assert "47 min" in d, est


def test_deteccion_da_area_tope_y_avisa_si_el_cuadro_esta_atrasado():
    d = _estado("detecta", area_km2=270.0, top_lo_km=3, top_hi_km=4,
                edad_min=150)["detalle"]
    assert "270 km²" in d and "3 a 4 km" in d and "atrasada" in d


def test_las_areas_llevan_punto_de_miles_sin_tocar_la_puntuacion():
    """Bug visto en la app: el reemplazo de coma por punto de miles se comía
    también la coma que seguía a "km²" ("2.320 km². más que...")."""
    d = _estado("extenso", area_km2=2320.4)["detalle"]
    assert "2.320 km², más que toda pluma medida (umbral 2.000 km²)" in d


def test_extenso_pide_revisar_el_loop_y_no_lo_llama_pluma():
    e = _estado("extenso", area_km2=2835.0)
    assert "revisa el loop" in e["detalle"] and "sistema meteorológico" in e["detalle"]
    m = _estado("extenso", area_km2=3e5, frac_sector=0.09, manto=True)
    assert "manto del 9 % del sector" in m["detalle"]


def test_el_aviso_de_fuente_dice_quien_detecta_y_que_no_es_alerta():
    from dashboard.map_helpers import AVISO_VOLCAT_FUENTE as A
    for frase in ("SSEC/CIMSS", "experimental", "no validada por nosotros",
                  "No es una alerta del OVDAS"):
        assert frase in A


def test_el_html_de_la_senal_lleva_el_aviso_de_fuente():
    from dashboard.map_helpers import AVISO_VOLCAT_FUENTE
    from dashboard.volcat_senal import html_senal
    s = {"estado": "detecta", "edad_min": 40, "area_km2": 270.0,
         "top_lo_km": 3, "top_hi_km": 4, "etiqueta_sector": "X (regional 2 km)"}
    for compacto in (True, False):
        assert AVISO_VOLCAT_FUENTE in html_senal(s, compacto=compacto)


# ── capa del dashboard: fallas de SSEC y caché ──────────────────────────────

def _png_bytes(pintar=None):
    import io
    buf = io.BytesIO()
    Image.fromarray(_png(pintar).astype(np.uint8)).save(buf, format="PNG")
    return buf.getvalue()


@pytest.fixture
def ssec(monkeypatch):
    """SSEC simulado: un cuadro por sector, URL distinta por sector, y un
    contador de descargas por URL. `estado["png"]` decide qué baja."""
    import dashboard.views.volcat_viewer as vv
    from dashboard.volcat_senal import _lecturas_sector
    _lecturas_sector.clear()
    estado = {"meta": True, "png": _png_bytes(), "bajadas": {}}

    def latest(sector, instr, image_type):
        if not estado["meta"]:
            return None
        coords = PS_SUR if sector == "Chile_South_2_km" else CE_CENTRAL
        return {"datetime": "2026-11-19_12-20-30",
                "image_url": f"http://ssec/{sector}.png", "coords": coords}

    def bajar(url):
        estado["bajadas"][url] = estado["bajadas"].get(url, 0) + 1
        return estado["png"]
    monkeypatch.setattr(vv, "_volcat_latest_cached", latest)
    monkeypatch.setattr(vv, "_volcat_image_bytes", bajar)
    yield estado
    _lecturas_sector.clear()


def test_ssec_caido_deja_los_44_en_no_disponible_y_ninguno_en_calma(ssec):
    from dashboard.volcat_senal import senales_volcat
    ssec["meta"] = False
    senales = senales_volcat(ahora=AHORA)
    assert len(senales) == 44
    assert {s["estado"] for s in senales.values()} == {"no_disponible"}
    assert all("SSEC" in s["motivo"] for s in senales.values())


def test_un_png_que_no_bajo_no_queda_memorizado(ssec):
    """La falla se lanza dentro de la función cacheada: el refresco siguiente
    reintenta en vez de arrastrar "no disponible" las 2 h del TTL."""
    from dashboard.volcat_senal import senal_volcat
    ssec["png"] = b""
    assert senal_volcat("Nevados de Chillan", ahora=AHORA)["estado"] == "no_disponible"

    def pluma(img):
        img[286:289, 480:488] = NARANJA
    ssec["png"] = _png_bytes(pluma)
    s = senal_volcat("Nevados de Chillan", ahora=AHORA)
    assert s["estado"] == "detecta" and s["edad_min"] == 39
    assert s["etiqueta_sector"] == "Chile Central 2 km (regional 2 km)"


def test_la_grilla_y_el_resumen_nacional_bajan_y_leen_el_cuadro_una_vez(ssec):
    from dashboard.volcat_senal import senal_volcat, senales_volcat
    senal_volcat("Nevados de Chillan", ahora=AHORA)
    senales_volcat(ahora=AHORA)
    senal_volcat("Villarrica", ahora=AHORA)
    assert ssec["bajadas"]["http://ssec/Chile_Central_2_km.png"] == 1


def test_el_resumen_lista_todo_lo_que_no_es_normal_incluido_no_disponible():
    from dashboard.volcat_senal import resumen_nacional
    r = resumen_nacional({
        "A": {"volcan": "A", "estado": "sin_deteccion"},
        "B": {"volcan": "B", "estado": "no_disponible"},
        "C": {"volcan": "C", "estado": "detecta"},
    })
    assert [s["volcan"] for s in r["lista"]] == ["B", "C"]
    assert r["cuenta"]["sin_deteccion"] == 1 and r["cuenta"]["atrasado"] == 0


def test_volcat_image_bytes_no_memoriza_una_descarga_fallida(monkeypatch):
    """Antes devolvía b"" desde la función cacheada y el vacío quedaba 2 h."""
    import requests

    import dashboard.views.volcat_viewer as vv
    vv._volcat_image_bytes_cached.clear()
    llamadas = {"n": 0}

    class _R:
        content = b"png"

        def raise_for_status(self):
            pass

    def get(url, timeout=None):
        llamadas["n"] += 1
        if llamadas["n"] == 1:
            raise requests.ConnectionError("caido")
        return _R()
    monkeypatch.setattr(requests, "get", get)
    assert vv._volcat_image_bytes("http://ssec/x.png") == b""
    assert vv._volcat_image_bytes("http://ssec/x.png") == b"png"
    assert vv._volcat_image_bytes("http://ssec/x.png") == b"png"
    assert llamadas["n"] == 2
    vv._volcat_image_bytes_cached.clear()


# ── cableado en las vistas (AST; validado por mutación, ver PR) ─────────────

ROOT = Path(__file__).parent.parent


def _cuerpo(rel, nombre):
    import ast
    src = (ROOT / rel).read_text(encoding="utf-8")
    for node in ast.walk(ast.parse(src)):
        if isinstance(node, ast.FunctionDef) and node.name == nombre:
            # sin docstring: que la palabra esté en el texto no es llamarla
            cuerpo = node.body[1:] if (node.body and isinstance(node.body[0], ast.Expr)
                                       and isinstance(node.body[0].value, ast.Constant)) else node.body
            return node, "\n".join(ast.unparse(n) for n in cuerpo)
    raise AssertionError(f"no existe {nombre} en {rel}")


def _llamadas(codigo):
    import ast
    return {n.func.id if isinstance(n.func, ast.Name) else n.func.attr
            for n in ast.walk(ast.parse(codigo)) if isinstance(n, ast.Call)
            and isinstance(n.func, (ast.Name, ast.Attribute))}


def test_la_cabecera_de_la_grilla_muestra_la_senal_del_volcan():
    _, cuerpo = _cuerpo("dashboard/views/modo_guardia_volcan.py", "_grid_header")
    llamadas = _llamadas(cuerpo)
    assert {"senal_volcat", "html_senal"} <= llamadas, llamadas
    assert "senal_html" in cuerpo.split("st.markdown(")[-1]


def test_volcat_por_zona_muestra_el_resumen_nacional_que_se_refresca_solo():
    _, cuerpo = _cuerpo("dashboard/views/modo_guardia.py", "_volcat_zonas_subtab")
    assert "_senal_volcat_nacional" in _llamadas(cuerpo)
    nodo, cuerpo_n = _cuerpo("dashboard/views/modo_guardia.py",
                             "_senal_volcat_nacional")
    import ast
    run_every = [kw for d in nodo.decorator_list if isinstance(d, ast.Call)
                 for kw in d.keywords if kw.arg == "run_every"]
    assert run_every, "el resumen nacional tiene que refrescarse solo"
    assert {"senales_volcat", "resumen_nacional"} <= _llamadas(cuerpo_n)
    # Usado, no sólo importado: el nombre en el `import` no pone el aviso en
    # pantalla (una mutación que lo sacaba del HTML pasaba con el `in`).
    usos = [n for n in ast.walk(ast.parse(cuerpo_n)) if isinstance(n, ast.Name)
            and n.id == "AVISO_VOLCAT_FUENTE" and isinstance(n.ctx, ast.Load)]
    assert usos, "el resumen nacional tiene que mostrar el aviso de fuente"
