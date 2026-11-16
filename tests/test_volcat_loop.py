"""Loop animado de VOLCAT: ventana de cuadros, huecos y armado del GIF/MP4.

Por que importa: el loop muestra como evoluciona la pluma (hacia donde va,
si crece o se corta). Un loop que rellena un cuadro faltante repitiendo el
anterior le dice al geologo que la pluma "se quedo quieta" 30 minutos cuando
en realidad SSEC no publico nada. Y un loop sin hora, sin escala o sin barra
de color es un archivo que nadie puede leer cuando lo encuentra suelto en un
informe. Estas pruebas fijan las dos cosas: no se inventa, y cada cuadro se
explica solo.
"""

import io
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

import src.fetch.volcat_api as va

UTC = timezone.utc


def _frames_sinteticos(fin: datetime, n: int, saltar=()):
    """Lista como la que devuelve SSEC: cada 10 min, a los :x0:30."""
    out = []
    for i in range(n):
        dt = fin - timedelta(minutes=10 * (n - 1 - i))
        if dt in saltar:
            continue
        s = dt.strftime("%Y-%m-%d_%H-%M-%S")
        out.append({
            "datetime": s,
            "filename": f"/data/x/GOES-19.ABI.{s}.Ash_Height.Chile_Central_2_km.png",
            "annot": None,
        })
    return out


FIN = datetime(2026, 11, 15, 13, 10, 30, tzinfo=UTC)


# ── Ventana de cuadros ─────────────────────────────────────────────────────

def test_ventana_toma_solo_las_ultimas_horas_en_orden():
    """SSEC entrega ~30 dias (4000+ cuadros); el loop usa solo la ventana."""
    frames = _frames_sinteticos(FIN, 30 * 144)
    sel = va.seleccionar_ventana(frames, horas=2)
    assert len(sel) == 12
    assert [f["dt"] for f in sel] == sorted(f["dt"] for f in sel)
    assert sel[-1]["dt"] == FIN


def test_ventana_respeta_un_fin_explicito():
    frames = _frames_sinteticos(FIN, 200)
    fin = FIN - timedelta(hours=5)
    sel = va.seleccionar_ventana(frames, horas=1, fin=fin)
    assert len(sel) == 6
    assert sel[-1]["dt"] == fin


def test_huecos_lista_los_cuadros_que_ssec_no_publico():
    faltan = {FIN - timedelta(minutes=30), FIN - timedelta(minutes=40)}
    frames = _frames_sinteticos(FIN, 12, saltar=faltan)
    sel = va.seleccionar_ventana(frames, horas=2)
    huecos = va.huecos_en_ventana([f["dt"] for f in sel],
                                  inicio=FIN - timedelta(hours=2), fin=FIN)
    assert sorted(huecos) == sorted(faltan)


def test_sin_huecos_no_inventa_faltantes():
    frames = _frames_sinteticos(FIN, 12)
    sel = va.seleccionar_ventana(frames, horas=2)
    assert va.huecos_en_ventana([f["dt"] for f in sel],
                                inicio=FIN - timedelta(hours=2), fin=FIN) == []


class _Resp:
    def __init__(self, status, payload):
        self.status_code = status
        self._p = payload

    def json(self):
        return self._p


class _Sesion:
    def __init__(self, resp=None, exc=None):
        self.resp, self.exc = resp, exc

    def get(self, *a, **k):
        if self.exc:
            raise self.exc
        return self.resp


def test_ssec_caido_se_reporta_como_error_y_no_como_calma(monkeypatch):
    """Si SSEC no responde, el loop lo dice: no es lo mismo que 'sin ceniza'."""
    monkeypatch.setattr(va, "_get_session",
                        lambda: _Sesion(exc=ConnectionError("timeout")))
    r = va.volcat_ventana("Chile_Central_2_km", "ABI", "Ash_Height", horas=2)
    assert r["ok"] is False
    assert r["frames"] == []
    assert "SSEC" in r["error"]


def test_ventana_con_huecos_no_rellena(monkeypatch):
    """Los cuadros devueltos son los reales; los faltantes van aparte."""
    faltan = {FIN - timedelta(minutes=50)}
    payload = {"endtime": _frames_sinteticos(FIN, 12, saltar=faltan),
               "coordinates": {"PROJECTION": "CE"}}
    monkeypatch.setattr(va, "_get_session",
                        lambda: _Sesion(resp=_Resp(200, payload)))
    r = va.volcat_ventana("Chile_Central_2_km", "ABI", "Ash_Height", horas=2)
    assert r["ok"] is True
    assert len(r["frames"]) == 11
    assert r["faltantes"] == sorted(faltan)
    f0 = r["frames"][0]
    assert f0["image_url"].startswith(va.BASE)
    assert f0["latlon_url"] and f0["coords"] == {"PROJECTION": "CE"}
    assert f0["dt"].tzinfo is not None


# ── Rotulos de cada cuadro ────────────────────────────────────────────────

try:  # el modulo aun puede no existir: que fallen las pruebas, no la coleccion
    from dashboard import volcat_loop as vl  # noqa: E402
except ImportError:
    vl = None


def test_rotulo_lleva_hora_utc_y_hora_de_chile():
    s = vl.rotulo_hora(datetime(2026, 11, 15, 13, 10, 30, tzinfo=UTC))
    assert "2026-11-15 13:10 UTC" in s
    assert "10:10" in s and "Chile" in s and "UTC-3" in s
    invierno = vl.rotulo_hora(datetime(2026, 7, 15, 13, 10, tzinfo=UTC))
    assert "09:10" in invierno and "UTC-4" in invierno


def test_aviso_de_salto_solo_cuando_faltan_cuadros():
    t = FIN
    assert vl.aviso_salto(t - timedelta(minutes=10), t) is None
    assert vl.aviso_salto(None, t) is None
    s = vl.aviso_salto(t - timedelta(minutes=30), t)
    assert s is not None and "30 min" in s and "2 cuadros" in s


def test_barra_de_escala_es_redonda_y_mide_lo_que_dice():
    from dashboard.regla import km_por_grado_lon
    view = {"lat_min": -40.0, "lat_max": -38.0,
            "lon_min": -73.0, "lon_max": -71.0}
    km, px = vl.barra_escala(view, ancho_px=600)
    ancho_km = 2.0 * km_por_grado_lon(-39.0)
    assert km in (1, 2, 5, 10, 20, 50, 100, 200, 500)
    assert km <= ancho_km / 3
    assert px == pytest.approx(km / ancho_km * 600, rel=1e-6)


# ── Recorte y composicion ─────────────────────────────────────────────────

def _png_sector(w=200, h=100, punto=None, color=(255, 0, 0)):
    from PIL import Image
    im = Image.new("RGB", (w, h), (40, 40, 40))
    if punto:
        im.putpixel(punto, color)
    buf = io.BytesIO()
    im.save(buf, format="PNG")
    return buf.getvalue()


def test_recorte_ubica_el_pixel_en_su_lat_lon():
    # Sector 20x10 grados a 0.1 grado/px. Pixel rojo en lon -70.05, lat -35.05.
    bounds = {"lat_min": -40.0, "lat_max": -30.0,
              "lon_min": -80.0, "lon_max": -60.0}
    png = _png_sector(punto=(99, 49))
    view = {"lat_min": -36.0, "lat_max": -34.0,
            "lon_min": -71.0, "lon_max": -69.0}
    im = vl.recortar_encuadre(png, bounds, view)
    assert im.size == (20, 20)
    assert im.getpixel((9, 9)) == (255, 0, 0)


def test_recorte_fuera_del_sector_rellena_oscuro_sin_romper():
    bounds = {"lat_min": -40.0, "lat_max": -30.0,
              "lon_min": -80.0, "lon_max": -60.0}
    view = {"lat_min": -41.0, "lat_max": -39.0,
            "lon_min": -61.0, "lon_max": -59.0}
    im = vl.recortar_encuadre(_png_sector(), bounds, view)
    assert im is not None
    assert im.getpixel((im.width - 1, im.height - 1)) == vl.FONDO_FUERA


def _villarrica():
    from src.volcanos import get_volcano
    return get_volcano("Villarrica")


def _view_villarrica():
    v = _villarrica()
    return {"lat_min": v.lat - 1, "lat_max": v.lat + 1,
            "lon_min": v.lon - 1, "lon_max": v.lon + 1}


def _componer(con_barra=True, aviso=None):
    from PIL import Image
    v = _villarrica()
    view = _view_villarrica()
    mapa = Image.new("RGB", (100, 100), (60, 60, 60))
    barra = Image.new("RGB", (40, 300), (200, 0, 200)) if con_barra else None
    return vl.componer_cuadro(
        mapa, view, centro=(v.lat, v.lon),
        dt=FIN, titulo="Villarrica · Altura de ceniza",
        sector_txt="Chile Central 2 km (regional 2 km)",
        barra_color=barra, aviso=aviso, alto_mapa=400,
    )


def test_el_mapa_se_compone_en_proporcion_de_km():
    """Un km horizontal mide lo mismo que uno vertical en el GIF: la barra de
    escala solo es honesta si el mapa no esta estirado."""
    from dashboard.regla import km_por_grado_lat, km_por_grado_lon
    cuadro, geo = _componer(con_barra=False)
    lat = _villarrica().lat
    esperado = 400 * km_por_grado_lon(lat) / km_por_grado_lat(lat)
    assert geo["mapa_px"][1] == 400
    assert geo["mapa_px"][0] == pytest.approx(esperado, abs=1)


def test_la_barra_de_color_va_al_costado_y_no_encima_del_mapa():
    con, geo_con = _componer(con_barra=True)
    x0, y0 = geo_con["mapa_xy"]
    w, h = geo_con["mapa_px"]
    # A la derecha del mapa hay pixeles de la barra (magenta)...
    derecha = con.crop((x0 + w, y0, con.width, y0 + h))
    assert (200, 0, 200) in [c for _n, c in derecha.getcolors(1 << 20)]
    # ...y dentro del mapa ninguno.
    mapa = con.crop((x0, y0, x0 + w, y0 + h))
    assert (200, 0, 200) not in [c for _n, c in mapa.getcolors(1 << 20)]


def test_el_cuadro_marca_el_volcan_en_el_centro():
    cuadro, geo = _componer(con_barra=False)
    x0, y0 = geo["mapa_xy"]
    w, h = geo["mapa_px"]
    cx, cy = x0 + w // 2, y0 + h // 2
    zona = cuadro.crop((cx - 15, cy - 15, cx + 15, cy + 15))
    colores = [c for _n, c in zona.getcolors(1 << 20)]
    assert (0, 255, 255) in colores


def test_el_cuadro_dibuja_la_barra_de_escala():
    """Una linea blanca continua del largo exacto de la barra. No basta con
    'hay blanco abajo': la frontera Chile-Argentina cruza este encuadre en
    gris muy claro y los nombres de volcanes van en blanco."""
    import numpy as np
    cuadro, geo = _componer(con_barra=False)
    x0, y0 = geo["mapa_xy"]
    w, h = geo["mapa_px"]
    view = _view_villarrica()
    _km, largo_px = vl.barra_escala(view, ancho_px=w)
    a = np.asarray(cuadro.crop((x0, y0 + int(h * 0.75), x0 + w // 2, y0 + h)))
    blanco = (a == 255).all(axis=2)
    mejor = 0
    for fila in blanco:
        run = 0
        for b in fila:
            run = run + 1 if b else 0
            mejor = max(mejor, run)
    assert mejor >= 0.9 * largo_px, (mejor, largo_px)


def test_el_texto_del_cuadro_lleva_hora_sector_y_nota_de_vacio():
    _c, geo = _componer(aviso="salto de 30 min: faltan 2 cuadros antes de este")
    textos = " | ".join(geo["textos"])
    assert "13:10 UTC" in textos and "Chile" in textos
    assert "Chile Central 2 km" in textos
    assert "sin dibujo" in textos
    assert "faltan 2 cuadros" in textos


# ── GIF y MP4 ─────────────────────────────────────────────────────────────

def _cuadros(n):
    from PIL import Image
    return [Image.new("RGB", (64, 48), (i * 40, 0, 0)) for i in range(n)]


def test_gif_tiene_exactamente_los_cuadros_reales():
    from PIL import Image
    gif = vl.armar_gif(_cuadros(3), ms_por_cuadro=500)
    im = Image.open(io.BytesIO(gif))
    assert im.format == "GIF"
    assert im.n_frames == 3
    assert im.info.get("loop") == 0


def test_mp4_es_h264_valido():
    pytest.importorskip("imageio_ffmpeg")
    mp4 = vl.armar_mp4(_cuadros(4), fps=2)
    assert b"ftyp" in mp4[:64]


# ── La vista ──────────────────────────────────────────────────────────────

def test_la_vista_volcat_declara_sector_vacio_y_faltantes():
    """La seccion del loop dice que sector usa, que vacio es normal y que
    cuadros faltan. Se lee el fuente de la funcion, no el modulo entero:
    las mismas palabras en otra seccion de la pagina no deben bastar."""
    import ast
    src = (Path(__file__).parent.parent / "dashboard" / "views"
           / "volcat_viewer.py").read_text(encoding="utf-8")
    tree = ast.parse(src)
    fn = next((n for n in tree.body if isinstance(n, ast.FunctionDef)
               and n.name == "_render_volcat_loop"), None)
    assert fn is not None, "falta _render_volcat_loop en volcat_viewer"
    cuerpo = ast.get_source_segment(src, fn)
    for pieza in ("_volcat_ventana_cached", "etiqueta_sector_volcat",
                  "faltantes", "fallidos", "sin dibujo",
                  "render_compact_legend", "_armar_loop_volcat(",
                  "download_button"):
        assert pieza in cuerpo, f"_render_volcat_loop no usa {pieza}"
    armado = next(n for n in tree.body if isinstance(n, ast.FunctionDef)
                  and n.name == "_armar_loop_volcat")
    cuerpo_armado = ast.get_source_segment(src, armado)
    for pieza in ("armar_gif", "armar_mp4", "aviso_salto", "fallidos"):
        assert pieza in cuerpo_armado, f"_armar_loop_volcat no usa {pieza}"
    # Y la seccion se llama desde la pagina.
    render = next(n for n in tree.body if isinstance(n, ast.FunctionDef)
                  and n.name == "_render_height_section")
    assert "_render_volcat_loop(" in ast.get_source_segment(src, render)


def test_escalar_el_mapa_no_inventa_colores_de_la_paleta():
    """Cada color de VOLCAT es una altura. Interpolar al agrandar crea colores
    intermedios que en la barra se leerian como alturas que nadie midio."""
    from PIL import Image
    im = Image.new("RGB", (10, 10), (0, 0, 255))
    for x in range(5):
        for y in range(10):
            im.putpixel((x, y), (255, 0, 0))
    grande = vl.escalar_mapa(im, 73, 61)
    assert grande.size == (73, 61)
    assert {c for _n, c in grande.getcolors(1 << 20)} <= {(255, 0, 0), (0, 0, 255)}


def test_cuadro_que_ssec_no_entrega_queda_fuera_y_anotado(monkeypatch):
    """SSEC lista 4 cuadros pero uno no baja: el GIF tiene 3 (no se repite
    el anterior en su lugar) y ese cuadro queda en `fallidos` para avisarlo."""
    from PIL import Image
    import dashboard.views.volcat_viewer as vv

    v = _villarrica()
    bounds = {"lat_min": v.lat - 3, "lat_max": v.lat + 3,
              "lon_min": v.lon - 3, "lon_max": v.lon + 3}
    png = _png_sector(w=120, h=120)
    dts = [FIN - timedelta(minutes=10 * i) for i in (3, 2, 1, 0)]
    malo = dts[1]
    frames = [{"dt": d, "image_url": f"u{i}", "latlon_url": None,
               "coords": {}} for i, d in enumerate(dts)]

    def _map_only(url, _ll, _c):
        return {} if url == "u1" else {"png": png, "bounds": bounds}

    monkeypatch.setattr(vv, "_volcat_map_only", _map_only)
    monkeypatch.setattr(vv, "_volcat_colorbar_split_vertical",
                        lambda url: (b"", b""))
    res = vv._armar_loop_volcat(vl.encuadre_volcan(v, 1.0), {"frames": frames},
                                "Altura", "Chile Central 2 km (regional 2 km)",
                                fps=2)
    assert res["fallidos"] == [malo]
    assert res["n"] == 3
    assert Image.open(io.BytesIO(res["gif"])).n_frames == 3


def test_la_frontera_no_se_sale_del_mapa_a_las_bandas_de_texto():
    """Visto en la app (nov-2026): la linea de la frontera seguia de largo
    por la banda de la hora y la tachaba. Lo dibujado sobre el mapa se
    recorta al mapa."""
    cuadro, geo = _componer(con_barra=False)
    x0, y0 = geo["mapa_xy"]
    w, h = geo["mapa_px"]
    bandas = [cuadro.crop((0, 0, cuadro.width, y0)),
              cuadro.crop((0, y0 + h, cuadro.width, cuadro.height))]
    for banda in bandas:
        colores = {c for _n, c in banda.getcolors(1 << 20)}
        assert (236, 240, 250) not in colores
        assert (20, 24, 32) not in colores


def test_todos_los_cuadros_miden_lo_mismo_con_o_sin_aviso():
    """Visto en la app (nov-2026): el cuadro con aviso de salto tenia una
    linea mas de banda, el GIF toma el tamano del primero y el aviso salia
    cortado justo en el cuadro que lo necesitaba."""
    sin, _ = _componer(aviso=None)
    con, _ = _componer(aviso="Salto de 30 min: faltan 2 cuadros antes de este")
    assert sin.size == con.size


def test_ningun_nombre_de_volcan_tapa_la_barra_de_escala():
    """Visto en el GIF de Villarrica (nov-2026): 'Carran-Los Venados' caia
    encima del rotulo '50 km' y no se leia ninguno de los dos."""
    _c, geo = _componer(con_barra=False)
    bx0, by0, bx1, by1 = geo["barra_rect"]
    assert geo["rotulos"], "el encuadre de Villarrica tiene volcanes rotulados"
    assert geo["texto_cabe"]
    for (x0, y0, x1, y1) in geo["rotulos"]:
        se_tocan = x0 < bx1 and bx0 < x1 and y0 < by1 and by0 < y1
        assert not se_tocan, ((x0, y0, x1, y1), geo["barra_rect"])


# ── Loop por zona ─────────────────────────────────────────────────────────

VIEW_NORTE = {"lat_min": -29.5, "lat_max": -16.8,
              "lon_min": -71.5, "lon_max": -66.8}


def test_barra_ns_mide_lo_que_dice_en_la_vertical():
    """En una zona de 12 grados de latitud un km horizontal no vale lo mismo
    arriba que abajo; un grado de meridiano si. Por eso la barra va N-S."""
    from dashboard.regla import km_por_grado_lat
    km, px = vl.barra_escala_ns(VIEW_NORTE, alto_px=800)
    alto_km = 12.7 * km_por_grado_lat((-29.5 - 16.8) / 2)
    assert km in (1, 2, 5, 10, 20, 50, 100, 200, 500)
    assert km <= alto_km / 3
    assert px == pytest.approx(km / alto_km * 800, rel=1e-6)


def _componer_zona():
    from PIL import Image
    enc = vl.encuadre_zona("Norte", VIEW_NORTE)
    mapa = Image.new("RGB", (100, 300), (60, 60, 60))
    return vl.componer_cuadro(
        mapa, enc["view"], centro=enc["centro"], dt=FIN,
        titulo=enc["titulo"] + " · Altura de pluma (km AMSL)",
        sector_txt="Chile North 2 km (regional 2 km)",
        barra=enc["barra"], alto_mapa=600)


def test_la_zona_lleva_barra_vertical_rotulada_n_s():
    import numpy as np
    cuadro, geo = _componer_zona()
    assert "N-S" in geo["barra_txt"]
    x0, y0 = geo["mapa_xy"]
    w, h = geo["mapa_px"]
    _km, largo = vl.barra_escala_ns(VIEW_NORTE, alto_px=h)
    a = np.asarray(cuadro.crop((x0, y0 + h // 2, x0 + w // 3, y0 + h)))
    blanco = (a == 255).all(axis=2)
    mejor = 0
    for col in blanco.T:
        run = 0
        for b in col:
            run = run + 1 if b else 0
            mejor = max(mejor, run)
    assert mejor >= 0.9 * largo, (mejor, largo)


def test_zona_angosta_no_corta_los_textos_ni_deforma_el_mapa():
    """La Norte mide 12,7 x 4,7 grados: el mapa sale angosto. El lienzo se
    ensancha para los textos, pero el mapa conserva su proporcion de km."""
    from dashboard.regla import km_por_grado_lat, km_por_grado_lon
    cuadro, geo = _componer_zona()
    lat = (-29.5 - 16.8) / 2
    esperado = 600 * (4.7 * km_por_grado_lon(lat)) / (12.7 * km_por_grado_lat(lat))
    assert geo["mapa_px"][0] == pytest.approx(esperado, abs=1)
    assert cuadro.width >= vl.ANCHO_MIN_PX
    assert geo["texto_cabe"], "algun texto pasa el borde del cuadro"


def test_encuadres_de_volcan_y_de_zona():
    v = _villarrica()
    ev = vl.encuadre_volcan(v, 0.75)
    assert ev["view"]["lat_max"] == pytest.approx(v.lat + 0.75)
    assert ev["centro"] == (v.lat, v.lon)
    assert ev["barra"] == "ew"
    assert "±0.75°" in ev["titulo"] and "r0.75deg" in ev["archivo"]
    ez = vl.encuadre_zona("Norte", VIEW_NORTE)
    assert ez["barra"] == "ns"
    assert ez["centro"] == pytest.approx(((-29.5 - 16.8) / 2, (-71.5 - 66.8) / 2))
    assert ez["titulo"] == "Zona Norte" and ez["archivo"] == "Zona_Norte"


def test_la_pagina_ofrece_el_loop_tambien_por_zona():
    import ast
    src = (Path(__file__).parent.parent / "dashboard" / "views"
           / "volcat_viewer.py").read_text(encoding="utf-8")
    tree = ast.parse(src)
    render = next(n for n in tree.body if isinstance(n, ast.FunctionDef)
                  and n.name == "_render_height_section")
    cuerpo = ast.get_source_segment(src, render)
    # Llamadas de verdad (AST), no texto: "encuadre_zona(" tambien aparece
    # dentro de "sector_y_encuadre_zona(" y daba verde con la zona apagada.
    llamadas = [n.func.id for n in ast.walk(render)
                if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)]
    assert "encuadre_zona" in llamadas and "encuadre_volcan" in llamadas
    assert llamadas.count("_render_volcat_loop") == 1
    assert "se arma por volcán" not in cuerpo


# ── Medir sobre un cuadro del loop ────────────────────────────────────────

def _geo_sintetico(v, radio=3.0):
    return {"png": _png_sector(w=120, h=120),
            "bounds": {"lat_min": v.lat - radio, "lat_max": v.lat + radio,
                       "lon_min": v.lon - radio, "lon_max": v.lon + radio}}


def test_cuadro_de_volcan_se_mide_en_km_con_la_regla():
    """El GIF no se puede medir; el cuadro elegido se dibuja en km del crater
    con la misma regla de la grilla del volcan."""
    import dashboard.views.volcat_viewer as vv
    from dashboard.regla import km_por_grado_lon
    v = _villarrica()
    enc = vl.encuadre_volcan(v, 1.0)
    fig = vv._figura_medicion(enc, _geo_sintetico(v), (b"", b""), FIN, 500)
    assert fig.layout.dragmode == "drawline"
    x0, x1 = fig.layout.xaxis.range
    assert x1 - x0 == pytest.approx(2 * km_por_grado_lon(v.lat), rel=1e-6)
    textos = [a.text for a in fig.layout.annotations]
    assert any(t.endswith(" km") for t in textos), textos
    # Misma hora que el GIF, no el "10:50 -03" que deja la sigla de tzdata.
    assert any("hora de Chile (UTC-3)" in (t or "") for t in textos), textos


def test_cuadro_de_zona_queda_en_grados_con_barra_ns_y_sin_regla():
    """En una zona la figura sigue en grados (como Nacional y Zona): una
    regla ahi mediria mal en horizontal, asi que no se ofrece."""
    import dashboard.views.volcat_viewer as vv
    v = _villarrica()
    enc = vl.encuadre_zona("Sur", {"lat_min": -42.5, "lat_max": -37.0,
                                   "lon_min": -74.0, "lon_max": -70.5})
    fig = vv._figura_medicion(enc, _geo_sintetico(v, radio=6.0), (b"", b""),
                              FIN, 500)
    assert fig.layout.dragmode != "drawline"
    assert tuple(fig.layout.xaxis.range) == (-74.0, -70.5)
    assert any("N-S" in (a.text or "") for a in fig.layout.annotations)


def test_el_loop_ofrece_medir_sobre_sus_cuadros():
    import ast
    src = (Path(__file__).parent.parent / "dashboard" / "views"
           / "volcat_viewer.py").read_text(encoding="utf-8")
    tree = ast.parse(src)
    fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef)
              and n.name == "_render_volcat_loop")
    cuerpo = ast.get_source_segment(src, fn)
    assert "_figura_medicion(" in cuerpo and '"usados"' in cuerpo


def test_el_gif_conserva_exactos_los_colores_de_la_escala():
    """El GIF tiene 256 colores. Con paleta adaptativa, el fondo IR en grises
    compite por esos cupos y los colores de la escala de altura pueden
    correrse: el pixel de la pluma deja de coincidir con su color en la
    barra, y la altura leida es otra. Los colores de la escala se reservan."""
    import numpy as np
    from PIL import Image
    rng = np.random.default_rng(0)
    arcoiris = [tuple(int(c) for c in rng.integers(0, 256, 3)) for _ in range(40)]
    a = np.zeros((64, 300, 3), dtype=np.uint8)
    for x in range(256):                       # rampa IR de 256 grises
        a[:, x] = x
    for i, c in enumerate(arcoiris):           # bloques de la escala
        a[(i % 8) * 8:(i % 8) * 8 + 8, 256 + (i // 8) * 8:256 + (i // 8) * 8 + 8] = c
    cuadro = Image.fromarray(a)
    gif = vl.armar_gif([cuadro, cuadro], ms_por_cuadro=500,
                       colores_fijos=arcoiris)
    out = np.asarray(Image.open(io.BytesIO(gif)).convert("RGB"))
    for i, c in enumerate(arcoiris):
        y, x = (i % 8) * 8 + 3, 256 + (i // 8) * 8 + 3
        assert tuple(out[y, x]) == c, (i, c, tuple(out[y, x]))


def test_colores_de_la_escala_salen_de_la_barra():
    """Se toman los colores con area (los bloques de la escala), no el
    antialias del texto de los numeros."""
    from PIL import Image, ImageDraw
    barra = Image.new("RGB", (40, 200), (255, 255, 255))
    d = ImageDraw.Draw(barra)
    d.rectangle([0, 0, 15, 99], fill=(255, 0, 255))
    d.rectangle([0, 100, 15, 199], fill=(0, 0, 255))
    d.point((30, 50), fill=(250, 10, 240))     # un pixel suelto de antialias
    cols = vl.colores_de_escala(barra)
    assert (255, 0, 255) in cols and (0, 0, 255) in cols
    assert (250, 10, 240) not in cols


def test_el_loop_le_pasa_al_gif_los_colores_de_su_barra(monkeypatch):
    from PIL import Image, ImageDraw
    import dashboard.views.volcat_viewer as vv
    import dashboard.volcat_loop as mod

    v = _villarrica()
    barra = Image.new("RGB", (30, 120), (255, 255, 255))
    ImageDraw.Draw(barra).rectangle([0, 0, 14, 59], fill=(200, 0, 200))
    buf = io.BytesIO()
    barra.save(buf, format="PNG")
    monkeypatch.setattr(vv, "_volcat_map_only",
                        lambda *a: _geo_sintetico(v))
    monkeypatch.setattr(vv, "_volcat_colorbar_split_vertical",
                        lambda url: (b"", buf.getvalue()))
    visto = {}

    def _espia(cuadros, ms_por_cuadro=500, colores_fijos=None):
        visto["fijos"] = colores_fijos
        return b"GIF"
    monkeypatch.setattr(mod, "armar_gif", _espia)
    frames = [{"dt": FIN, "image_url": "u0", "latlon_url": None, "coords": {}}]
    vv._armar_loop_volcat(vl.encuadre_volcan(v, 1.0), {"frames": frames},
                          "Altura", "Chile Central 2 km (regional 2 km)", fps=2)
    assert (200, 0, 200) in (visto.get("fijos") or [])


# ── Ventanas de dias (pedido 16-11-2026: evolucion de Chillan en 10 dias) ──
#
# SSEC guarda ~30 dias. Un loop de 10 dias con todos los cuadros serian 1440
# descargas de ~0,4 MB: se toma un cuadro por paso (p. ej. uno por hora). Un
# paso sin cuadro publicado queda como faltante, nunca se rellena.

def _con_dt(lista):
    return [{**f, "dt": va._parse_volcat_frame_dt(f["datetime"])} for f in lista]


def test_submuestreo_toma_un_cuadro_real_por_paso():
    frames = _con_dt(_frames_sinteticos(FIN, 6 * 6))   # 6 h, cada 10 min
    inicio = FIN - timedelta(hours=6)
    sel, faltan = va.submuestrear(frames, inicio, FIN, paso_min=60)
    assert [f["dt"] for f in sel] == [FIN - timedelta(hours=h)
                                      for h in range(5, -1, -1)]
    assert faltan == []


def test_submuestreo_usa_un_cuadro_vecino_real_si_falta_el_del_paso():
    """Si SSEC no publico el cuadro justo del paso, sirve otro REAL dentro
    de medio paso (con su propia hora). Si no hay ninguno, es faltante."""
    hueco = FIN - timedelta(hours=2)
    vacio = {FIN - timedelta(hours=4) + timedelta(minutes=m)
             for m in range(-30, 31, 10)}
    frames = _con_dt(_frames_sinteticos(FIN, 6 * 6, saltar={hueco} | vacio))
    inicio = FIN - timedelta(hours=6)
    sel, faltan = va.submuestrear(frames, inicio, FIN, paso_min=60)
    dts = [f["dt"] for f in sel]
    assert hueco not in dts
    assert any(abs(d - hueco) < timedelta(minutes=30) for d in dts)
    assert faltan == [FIN - timedelta(hours=4)]
    assert len(set(dts)) == len(dts)          # ningun cuadro usado dos veces


def test_ventana_de_10_dias_baja_un_cuadro_por_hora(monkeypatch):
    payload = {"endtime": _frames_sinteticos(FIN, 6 * 24 * 12),
               "coordinates": {"PROJECTION": "CE"}}
    monkeypatch.setattr(va, "_get_session",
                        lambda: _Sesion(resp=_Resp(200, payload)))
    r = va.volcat_ventana("Chile_Central_2_km", "ABI", "Ash_Height",
                          horas=240, paso_min=60)
    assert r["ok"] is True
    assert len(r["frames"]) == 240
    assert r["paso_min"] == 60
    assert r["faltantes"] == []
    assert r["fin"] - r["inicio"] == timedelta(days=10)


def test_el_loop_ofrece_10_dias_y_avisa_saltos_segun_el_paso():
    import ast
    import dashboard.views.volcat_viewer as vv
    assert 240 in vv.LOOP_HORAS
    assert vv.LOOP_PASO_MIN[240] >= 60
    # 16 dias: un mes en curso completo hasta su dia 16 (Chillan, nov-2026).
    assert 384 in vv.LOOP_HORAS
    assert vv._rotulo_ventana(384) == "16 días (384 cuadros, 1 por hora)"
    src = Path(vv.__file__).read_text(encoding="utf-8")
    tree = ast.parse(src)
    armado = next(n for n in tree.body if isinstance(n, ast.FunctionDef)
                  and n.name == "_armar_loop_volcat")
    assert "paso_min" in ast.get_source_segment(src, armado)
    # Con un cuadro por hora, una hora entre cuadros no es un salto.
    assert vl.aviso_salto(FIN - timedelta(hours=1), FIN, cadencia_min=60) is None
    assert vl.aviso_salto(FIN - timedelta(hours=3), FIN, cadencia_min=60)
