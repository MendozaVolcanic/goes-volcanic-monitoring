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
    sin, geo_sin = _componer(con_barra=False)
    con, geo_con = _componer(con_barra=True)
    assert con.width > sin.width
    x0, y0 = geo_con["mapa_xy"]
    w, h = geo_con["mapa_px"]
    # A la derecha del mapa hay pixeles de la barra (magenta).
    derecha = con.crop((x0 + w, y0, con.width, y0 + h))
    assert (200, 0, 200) in [c for _n, c in derecha.getcolors(1 << 20)]


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
    res = vv._armar_loop_volcat(v, {"frames": frames}, "Altura", 1.0,
                                "Chile Central 2 km (regional 2 km)", fps=2)
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
    for (x0, y0, x1, y1) in geo["rotulos"]:
        se_tocan = x0 < bx1 and bx0 < x1 and y0 < by1 and by0 < y1
        assert not se_tocan, ((x0, y0, x1, y1), geo["barra_rect"])
