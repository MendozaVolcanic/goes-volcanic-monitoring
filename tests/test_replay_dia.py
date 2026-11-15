"""Replay de un dia: los 4 productos juntos y reproduccion continua.

Por que existe (15-11-2026, pedido de Nicolas): el Replay mostraba un
producto a la vez y habia que apretar ▶ scan por scan. Para comparar contra
una anomalia vista en otro visor hace falta ver GeoColor, Ash RGB, SO2 y
VOLCAT del MISMO scan lado a lado, y poder pasar el dia entero de corrido.

Dos reglas de honestidad que estas pruebas sostienen:
- Un producto sin imagen en un scan queda vacio y dice por que. Nunca se
  rellena con el scan vecino: eso mostraria una pluma quieta que nadie vio.
- La reproduccion corre en el navegador (frames de plotly). La barra de
  escala y la regla tienen que seguir ahi en todos los cuadros.
"""

import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from dashboard import replay_dia as rd

UTC = timezone.utc
LAT0, LON0 = -25.167, -68.507
BOUNDS = {"lat_min": LAT0 - 0.4, "lat_max": LAT0 + 0.4,
          "lon_min": LON0 - 0.4, "lon_max": LON0 + 0.4}


def _img(color):
    a = np.zeros((20, 20, 3), dtype=np.uint8)
    a[:] = color
    return a


def _cuadro(slot, faltan=(), motivo="RAMMB no publicó este scan"):
    imgs, motivos = {}, {}
    for pid in rd.PANELES:
        if pid in faltan:
            imgs[pid] = None
            motivos[pid] = motivo
        else:
            imgs[pid] = _img((10, 200, 30))
    return {"slot": slot, "imgs": imgs, "motivos": motivos}


# ── Linea de tiempo ──────────────────────────────────────────────────

def test_el_slot_de_10_min_une_rammb_y_volcat():
    """RAMMB rotula el scan 15:30:21 y VOLCAT el mismo scan 15:30:30: los
    dos caen en el slot 15:30."""
    assert rd.slot_de_ts("20261114153021") == "202611141530"
    assert rd.slot_de_dt(datetime(2026, 11, 14, 15, 30, 30, tzinfo=UTC)) == \
        "202611141530"
    assert rd.dt_de_slot("202611141530") == datetime(2026, 11, 14, 15, 30,
                                                     tzinfo=UTC)


def test_la_linea_de_tiempo_es_la_union_de_los_productos():
    listas = {"geocolor": ["20261114153021", "20261114154021"],
              "eumetsat_ash": ["20261114153021", "20261114154021"],
              "jma_so2": ["20261114154021", "20261114155021"]}
    assert rd.linea_de_tiempo(listas) == [
        "202611141530", "202611141540", "202611141550"]


def test_un_producto_sin_ese_scan_queda_vacio_no_toma_el_vecino():
    listas = {"geocolor": ["20261114153021", "20261114154021"],
              "jma_so2": ["20261114154021"]}
    slots = rd.linea_de_tiempo(listas)
    par = rd.emparejar(listas, slots)
    assert par["202611141530"] == {"geocolor": "20261114153021",
                                   "jma_so2": None}
    assert par["202611141540"]["jma_so2"] == "20261114154021"


def test_volcat_se_empareja_por_slot():
    frames = [{"dt": datetime(2026, 11, 14, 15, 30, 30, tzinfo=UTC), "n": 1},
              {"dt": datetime(2026, 11, 14, 15, 50, 30, tzinfo=UTC), "n": 2}]
    m = rd.volcat_por_slot(frames, ["202611141530", "202611141540",
                                    "202611141550"])
    assert m["202611141530"]["n"] == 1
    assert m["202611141540"] is None
    assert m["202611141550"]["n"] == 2


# ── Figura ───────────────────────────────────────────────────────────

def _fig(cuadros, **kw):
    return rd.figura_dia(cuadros, LAT0, LON0, BOUNDS, **kw)


def test_un_cuadro_muestra_los_cuatro_productos_en_km_sin_animacion():
    fig = _fig([_cuadro("202611141530")])
    refs = sorted((im.xref, im.yref) for im in fig.layout.images)
    assert refs == [("x", "y"), ("x2", "y2"), ("x3", "y3"), ("x4", "y4")]
    # Imagen ubicada en km alrededor del crater (no en grados).
    from dashboard.regla import a_km
    x0, y1 = a_km(BOUNDS["lat_max"], BOUNDS["lon_min"], LAT0, LON0)
    im = fig.layout.images[0]
    assert im.x == pytest.approx(x0)
    assert im.y == pytest.approx(y1)
    assert not fig.frames
    assert not fig.layout.updatemenus


def test_los_paneles_van_en_el_orden_de_la_grilla_de_volcan():
    from dashboard.views.modo_guardia_volcan import GRID_PANELS
    assert list(rd.PANELES) == [p["id"] for p in GRID_PANELS]


def test_el_dia_se_reproduce_con_play_y_un_frame_por_scan():
    cuadros = [_cuadro(s) for s in ("202611141530", "202611141540",
                                    "202611141550")]
    fig = _fig(cuadros, ms_por_cuadro=250)
    assert [f.name for f in fig.frames] == [c["slot"] for c in cuadros]
    botones = fig.layout.updatemenus[0].buttons
    play = botones[0]
    assert play.args[1]["frame"]["duration"] == 250
    assert play.args[1]["frame"]["redraw"] is True
    assert len(fig.layout.sliders[0].steps) == 3


def test_producto_faltante_no_dibuja_imagen_y_dice_por_que():
    cuadros = [_cuadro("202611141530"),
               _cuadro("202611141540", faltan=("jma_so2",))]
    fig = _fig(cuadros)
    f = fig.frames[1]
    refs = {im.xref for im in f.layout.images}
    i_so2 = rd.PANELES.index("jma_so2") + 1
    assert f"x{i_so2}" not in refs
    textos = " ".join(a.text for a in f.layout.annotations)
    assert "RAMMB no publicó este scan" in textos


def test_la_barra_de_escala_sobrevive_a_cada_cuadro():
    """Un frame que trae `annotations` reemplaza la lista entera: si no
    repite el rotulo de la barra, la barra queda sin numero al dar Play."""
    cuadros = [_cuadro("202611141530"), _cuadro("202611141540")]
    fig = _fig(cuadros)
    for f in fig.frames:
        assert sum(" km" in (a.text or "") for a in f.layout.annotations) == 4
    assert sum(s.xref == "x2" for s in fig.layout.shapes) == 2  # halo + linea


def test_la_barra_de_color_de_volcat_esta_en_todos_los_cuadros():
    barra = np.zeros((40, 8, 3), dtype=np.uint8)
    cuadros = [_cuadro("202611141530"), _cuadro("202611141540")]
    fig = _fig(cuadros, barra_volcat=barra)
    i = rd.PANELES.index("volcat") + 1
    dom = f"x{i} domain"
    assert any(im.xref == dom for im in fig.layout.images)
    for f in fig.frames:
        assert any(im.xref == dom for im in f.layout.images)


def test_la_regla_mide_en_km_en_los_cuatro_paneles():
    fig = _fig([_cuadro("202611141530")], regla=True)
    assert fig.layout.dragmode == "drawline"
    assert "km" in fig.layout.newshape.label.texttemplate
    for i in ("", "2", "3", "4"):
        assert fig.layout[f"yaxis{i}"].scaleanchor == f"x{i}"


# ── Barra de escala en un subplot ────────────────────────────────────

def test_barra_de_escala_en_otro_subplot():
    import plotly.graph_objects as go
    from dashboard.regla import agregar_barra_escala
    fig = go.Figure()
    agregar_barra_escala(fig, (-40, 40), (-40, 40), ejes=("x3", "y3"))
    assert {s.xref for s in fig.layout.shapes} == {"x3"}
    assert fig.layout.annotations[0].yref == "y3"


# ── VOLCAT de un dia pasado ──────────────────────────────────────────

def test_volcat_entre_dos_horas_y_hasta_donde_llega_ssec(monkeypatch):
    from src.fetch import volcat_api as va
    lista = [{"datetime": f"2026-11-14_{h:02d}-{m:02d}-30",
              "filename": f"/x/{h}{m}.png"}
             for h in (15, 16) for m in (0, 10, 20, 30, 40, 50)]
    lista.insert(0, {"datetime": "2026-10-16_11-50-30", "filename": "/x/0.png"})
    monkeypatch.setattr(va, "_query_frames_estado",
                        lambda *a, **k: (lista, {"c": 1}, None))
    r = va.volcat_cuadros_entre("Chile_North_2_km", "ABI",
                                datetime(2026, 11, 14, 15, 30, tzinfo=UTC),
                                datetime(2026, 11, 14, 16, 0, tzinfo=UTC))
    assert r["ok"] and r["error"] is None
    assert [f["dt"].minute for f in r["frames"]] == [30, 40, 50]
    assert r["frames"][0]["image_url"].endswith("/x/1530.png")
    assert r["desde"] == datetime(2026, 10, 16, 11, 50, 30, tzinfo=UTC)


def test_volcat_sin_respuesta_no_se_lee_como_sin_ceniza(monkeypatch):
    from src.fetch import volcat_api as va
    monkeypatch.setattr(va, "_query_frames_estado",
                        lambda *a, **k: ([], None, "SSEC no respondio (Timeout)"))
    r = va.volcat_cuadros_entre("Chile_North_2_km", "ABI",
                                datetime(2026, 11, 14, 15, tzinfo=UTC),
                                datetime(2026, 11, 14, 16, tzinfo=UTC))
    assert r["ok"] is False
    assert "no respondio" in r["error"]
    assert r["frames"] == []


# ── Carga en dos etapas ──────────────────────────────────────────────

def _carga_falsa(monkeypatch):
    """RAMMB y VOLCAT falsos que cuentan cuantas veces se piden."""
    from dashboard.views import replay_reciente as rr
    pedidos = {"rammb": 0, "volcat": 0}

    def _rammb(prod, cands, bounds, **kw):
        pedidos["rammb"] += 1
        return _img((1, 2, 3)), cands[0], 3

    def _volcat(meta, bounds):
        pedidos["volcat"] += 1
        return _img((9, 9, 9))

    monkeypatch.setattr(rr, "fetch_frame_robust", _rammb)
    monkeypatch.setattr(rr, "_imagen_volcat", _volcat)
    slots = ["202611141530", "202611141540"]
    par = {s: {p: s + "21" for p in rd.PANELES_RAMMB} for s in slots}
    vmatch = {"202611141530": {"image_url": "u"}, "202611141540": None}
    return rr, pedidos, slots, par, vmatch


def test_reproducir_baja_primero_rammb_y_volcat_solo_si_se_pide(monkeypatch):
    """VOLCAT pesa ~0,55 MB por cuadro (el sector entero): no se baja con
    los tres de RAMMB. Su panel dice que falta cargarlo, y donde SSEC no
    tiene cuadro dice eso otro."""
    rr, pedidos, slots, par, vmatch = _carga_falsa(monkeypatch)
    c = rr._cargar_cuadros(slots, par, vmatch, BOUNDS, {}, None,
                           productos=rd.PANELES_RAMMB)
    assert pedidos == {"rammb": 6, "volcat": 0}
    assert c[0]["motivos"]["volcat"] == rr._VOLCAT_SIN_CARGAR
    assert c[1]["motivos"]["volcat"] == "SSEC no publicó este cuadro"

    c = rr._cargar_cuadros(slots, par, vmatch, BOUNDS, {}, None,
                           productos=("volcat",), base=c)
    assert pedidos == {"rammb": 6, "volcat": 1}
    assert c[0]["imgs"]["volcat"] is not None
    assert "volcat" not in c[0]["motivos"]
    assert c[0]["imgs"]["jma_so2"] is not None   # lo de RAMMB se conserva
    assert c[1]["motivos"]["volcat"] == "SSEC no publicó este cuadro"


# ── La vista ─────────────────────────────────────────────────────────

def test_la_vista_muestra_los_cuatro_y_tiene_reproduccion():
    fuente = (Path(__file__).parent.parent / "dashboard" / "views"
              / "replay_reciente.py").read_text(encoding="utf-8")
    assert "figura_dia(" in fuente
    assert "volcat_cuadros_entre(" in fuente
    # Ya no hay que elegir UN producto.
    assert '"replay_product"' not in fuente
