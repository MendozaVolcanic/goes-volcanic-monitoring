"""Regla para medir hasta donde llega la ceniza.

El operador necesita leer "la pluma ya esta a 60 km al este del crater" sobre la
imagen, sin calcular a mano grados de longitud que a 40 S valen 85 km y a 18 S
valen 106 km. Por eso la grilla del volcan dibuja en km centrados en el crater:
una linea trazada encima se mide en km directamente (plotly lo hace en el
navegador, sin recargar la pagina).

Estas pruebas fijan tres cosas que, rotas, dan una cifra falsa en pantalla:
la conversion grados -> km (WGS84, no una esfera de 111 km), el error de medir
en un plano local frente a la distancia real, y que la conversion de la figura
mueva TODO lo dibujado (imagen, volcan, anillos, hot spots, rotulos) por igual.
"""

import ast
from pathlib import Path

import numpy as np
import plotly.graph_objects as go
import pytest

ROOT = Path(__file__).resolve().parents[1]
LIVE = ROOT / "dashboard" / "views" / "live_viewer.py"


# -- grados -> km ---------------------------------------------------------

def test_largo_de_un_grado_coincide_con_wgs84():
    """Valores de tabla WGS84: en el ecuador 110.574 km por grado de latitud y
    111.320 por grado de longitud; a 45 grados, 111.132 y 78.847."""
    from dashboard.regla import km_por_grado_lat, km_por_grado_lon

    assert km_por_grado_lat(0.0) == pytest.approx(110.574, abs=0.002)
    assert km_por_grado_lon(0.0) == pytest.approx(111.320, abs=0.002)
    assert km_por_grado_lat(-45.0) == pytest.approx(111.132, abs=0.002)
    assert km_por_grado_lon(-45.0) == pytest.approx(78.847, abs=0.002)


def test_el_crater_queda_en_el_origen():
    from dashboard.regla import a_km

    x, y = a_km(-39.42, -71.93, lat0=-39.42, lon0=-71.93)
    assert (x, y) == (0.0, 0.0)


def test_un_grado_al_norte_mide_un_grado_de_meridiano():
    from dashboard.regla import a_km, km_por_grado_lat

    x, y = a_km(-38.42, -71.93, lat0=-39.42, lon0=-71.93)
    assert x == 0.0
    assert y == pytest.approx(km_por_grado_lat(-39.42))


@pytest.mark.parametrize("lat0", [-18.0, -40.0, -55.0])
@pytest.mark.parametrize("radio_deg,tolerancia", [(1.0, 0.007), (3.0, 0.015)])
def test_medir_desde_el_crater_se_desvia_poco_de_la_distancia_real(
        lat0, radio_deg, tolerancia):
    """El plano local es una aproximacion: lo que se declara en pantalla
    (menos de 1,5 % hasta 3 grados de radio) tiene que ser cierto en todo
    Chile, del norte a la zona austral."""
    from dashboard.regla import a_km, distancia_km

    g = np.linspace(-radio_deg, radio_deg, 25)
    peor = 0.0
    for dla in g:
        for dlo in g:
            if dla == 0 and dlo == 0:
                continue
            x, y = a_km(lat0 + dla, -72.0 + dlo, lat0=lat0, lon0=-72.0)
            real = distancia_km(lat0, -72.0, lat0 + dla, -72.0 + dlo)
            peor = max(peor, abs(np.hypot(x, y) - real) / real)
    assert peor < tolerancia


def test_distancia_real_de_un_caso_conocido():
    """Villarrica -> Llaima: unos 83 km (0,73 grados de latitud y 0,2 de
    longitud). Si la formula estuviera mal (grados sin pasar a radianes, radio
    equivocado) esto cambia por ordenes."""
    from dashboard.regla import distancia_km

    d = distancia_km(-39.42, -71.93, -38.69, -71.73)
    assert 80 < d < 85


# -- anillos y barra --------------------------------------------------------

@pytest.mark.parametrize("radio_km,esperado", [
    (39.0, [5, 10, 25, 50]),      # radio por defecto de la grilla (0.35)
    (111.0, [10, 25, 50, 100]),   # 1 grado
    (333.0, [50, 100, 200, 300]), # 3 grados: siguiendo una pluma lejana
])
def test_los_anillos_crecen_con_el_encuadre(radio_km, esperado):
    """Con anillos fijos de 5 a 50 km, al abrir el radio a 3 grados para seguir
    la pluma los anillos quedaban apinados en el centro y no median nada."""
    from dashboard.regla import radios_anillos_km

    assert radios_anillos_km(radio_km) == esperado


@pytest.mark.parametrize("ancho_km,esperado", [
    (78.0, 20), (222.0, 50), (666.0, 200), (4300.0, 1000),
])
def test_la_barra_de_escala_usa_un_largo_redondo(ancho_km, esperado):
    from dashboard.regla import largo_barra_km

    assert largo_barra_km(ancho_km) == esperado


# -- conversion de la figura ----------------------------------------------

def _figura_en_grados(lat0=-39.42, lon0=-71.93, r=0.5):
    fig = go.Figure()
    fig.add_layout_image(
        source="data:image/png;base64,AAAA", xref="x", yref="y",
        x=lon0 - r, y=lat0 + r, sizex=2 * r, sizey=2 * r,
        sizing="stretch", layer="below",
    )
    fig.add_trace(go.Scatter(
        x=[lon0], y=[lat0], mode="markers",
        hovertemplate="<b>V</b><br>%{x:.3f}, %{y:.3f}<extra></extra>",
    ))
    # linea con cortes (asi viene la frontera de Chile)
    fig.add_trace(go.Scatter(x=[lon0, None, lon0 + r], y=[lat0, None, lat0],
                             mode="lines"))
    fig.add_annotation(x=lon0 + r, y=lat0, text="50 km", showarrow=False)
    fig.add_annotation(x=0.5, y=0.5, xref="paper", yref="paper", text="hora",
                       showarrow=False)
    fig.update_xaxes(range=[lon0 - r, lon0 + r])
    fig.update_yaxes(range=[lat0 - r, lat0 + r], scaleanchor="x",
                     scaleratio=1.3)
    return fig


def test_la_figura_pasa_entera_a_km():
    """Imagen, marcador, lineas, rotulos y ejes se mueven con la MISMA
    conversion; si uno queda en grados, se dibuja a cientos de km de donde
    esta y la regla mide contra un fondo corrido."""
    from dashboard.regla import figura_en_km, km_por_grado_lat, km_por_grado_lon

    lat0, lon0, r = -39.42, -71.93, 0.5
    fig = figura_en_km(_figura_en_grados(lat0, lon0, r), lat0, lon0)
    kx, ky = km_por_grado_lon(lat0), km_por_grado_lat(lat0)

    img = fig.layout.images[0]
    assert img.x == pytest.approx(-r * kx)
    assert img.y == pytest.approx(r * ky)
    assert img.sizex == pytest.approx(2 * r * kx)
    assert img.sizey == pytest.approx(2 * r * ky)

    assert list(fig.data[0].x) == [0.0] and list(fig.data[0].y) == [0.0]
    # los cortes de linea se conservan
    assert fig.data[1].x[1] is None and fig.data[1].y[1] is None
    assert fig.data[1].x[2] == pytest.approx(r * kx)

    ann_datos, ann_papel = fig.layout.annotations
    assert ann_datos.x == pytest.approx(r * kx) and ann_datos.y == pytest.approx(0)
    assert (ann_papel.x, ann_papel.y) == (0.5, 0.5)

    assert fig.layout.xaxis.range == pytest.approx((-r * kx, r * kx))
    assert fig.layout.yaxis.range == pytest.approx((-r * ky, r * ky))
    # en km un km horizontal y uno vertical miden lo mismo en pantalla
    assert fig.layout.yaxis.scaleratio == 1


def test_el_tooltip_sigue_mostrando_coordenadas_geograficas():
    """El marcador del volcan mostraba lon/lat con %{x}/%{y}; en km esos
    tokens dirian '0.000, 0.000'. Tienen que seguir dando grados."""
    from dashboard.regla import figura_en_km

    fig = figura_en_km(_figura_en_grados(), -39.42, -71.93)
    tr = fig.data[0]
    assert "%{x" not in tr.hovertemplate and "%{y" not in tr.hovertemplate
    lat, lon = tr.customdata[0]
    assert (lat, lon) == (-39.42, -71.93)


def test_la_regla_mide_en_km_en_el_navegador():
    from dashboard.regla import activar_regla

    fig = activar_regla(go.Figure(), decimales=1)
    assert fig.layout.dragmode == "drawline"
    assert fig.layout.newshape.label.texttemplate == "%{length:.1f} km"


def test_la_barra_de_escala_queda_dentro_del_encuadre():
    from dashboard.regla import agregar_barra_escala

    fig = agregar_barra_escala(go.Figure(), (-40.0, 40.0), (-40.0, 40.0))
    textos = [a.text for a in fig.layout.annotations]
    assert any(t.endswith(" km") for t in textos)
    for s in fig.layout.shapes:
        for v in (s.x0, s.x1):
            assert -40.0 <= v <= 40.0
        for v in (s.y0, s.y1):
            assert -40.0 <= v <= 40.0


def test_la_barra_norte_sur_vale_en_cualquier_latitud():
    """En Nacional y Zona los ejes son grados con aspecto 1:1, asi que un km
    horizontal NO mide lo mismo arriba que abajo del mapa. Un grado de
    meridiano si: la barra va vertical y su largo en grados sale de WGS84."""
    from dashboard.regla import agregar_barra_ns, km_por_grado_lat

    b = {"lat_min": -56.0, "lat_max": -17.0, "lon_min": -76.0, "lon_max": -66.0}
    fig = agregar_barra_ns(go.Figure(), b)
    barra = [s for s in fig.layout.shapes if s.x0 == s.x1][0]
    largo_grados = abs(barra.y1 - barra.y0)
    lat_media = (barra.y0 + barra.y1) / 2
    km = largo_grados * km_por_grado_lat(lat_media)
    texto = [a.text for a in fig.layout.annotations][0]
    assert texto.startswith(f"{round(km)} km")


# -- cableado en la grilla y la vista ------------------------------------

def test_render_product_dibuja_en_km_con_barra_de_escala():
    from dashboard.regla import km_por_grado_lon
    from dashboard.views.modo_guardia_volcan import _render_product

    lat0, lon0, r = -39.42, -71.93, 0.35
    bounds = {"lat_min": lat0 - r, "lat_max": lat0 + r,
              "lon_min": lon0 - r, "lon_max": lon0 + r}
    img = np.zeros((8, 8, 3), dtype=np.uint8)
    fig = _render_product(img, bounds, "Ash RGB", lat0, lon0, "Villarrica")
    assert fig.layout.xaxis.range == pytest.approx(
        (-r * km_por_grado_lon(lat0), r * km_por_grado_lon(lat0)))
    assert fig.layout.dragmode != "drawline"
    assert any(str(a.text).endswith(" km") for a in fig.layout.annotations)

    fig_r = _render_product(img, bounds, "Ash RGB", lat0, lon0, "Villarrica",
                            regla=True)
    assert fig_r.layout.dragmode == "drawline"


def test_la_regla_llega_a_los_paneles_de_la_grilla():
    """Mismo patron que el radio: si un panel no recibe el flag, el operador
    prende la regla y en ese mapa arrastrar sigue haciendo zoom."""
    import inspect

    from dashboard.views import modo_guardia_volcan as MGV

    for nombre in ("volcan_grid", "_panel_rammb", "_panel_volcat"):
        sig = inspect.signature(getattr(MGV, nombre))
        assert "regla" in sig.parameters, nombre
        assert sig.parameters["regla"].default is False, nombre

    arbol = ast.parse((ROOT / "dashboard" / "views" /
                       "modo_guardia_volcan.py").read_text(encoding="utf-8"))
    grid = next(n for n in ast.walk(arbol)
                if isinstance(n, ast.FunctionDef) and n.name == "volcan_grid")
    llamadas = [n for n in ast.walk(grid) if isinstance(n, ast.Call)
                and getattr(n.func, "id", "") in ("_panel_rammb", "_panel_volcat")]
    assert len(llamadas) == 2
    for c in llamadas:
        assert any(k.arg == "regla" for k in c.keywords), c.func.id


@pytest.mark.parametrize("rotulo,titulo,edad", [
    ("11:20 UTC · 08:20 -03 (hace 21 min) ⚠ atrasada · ~1.7 km/px",
     "11:20 UTC · 08:20 -03 ⚠ atrasada · ~1.7 km/px", 21),
    ("11:20 UTC · 08:20 -03 (hace 5 min) · hi-res L1b ~0.5 km/px "
     "(visible, pan-sharp)",
     "11:20 UTC · 08:20 -03 · hi-res L1b ~0.5 km/px (visible, pan-sharp)", 5),
    ("—", "—", None),
])
def test_la_edad_sale_del_titulo_del_mapa(rotulo, titulo, edad):
    """Una linea de la regla vive mientras la figura no cambie. Con
    "(hace N min)" en el titulo, la figura cambiaba cada minuto y la medicion
    se borraba sola al refrescar el panel (visto en la app, nov-2026)."""
    from dashboard.map_helpers import separar_edad

    assert separar_edad(rotulo) == (titulo, edad)


def test_el_panel_rammb_dibuja_un_titulo_estable():
    arbol = ast.parse((ROOT / "dashboard" / "views" /
                       "modo_guardia_volcan.py").read_text(encoding="utf-8"))
    panel = next(n for n in ast.walk(arbol)
                 if isinstance(n, ast.FunctionDef) and n.name == "_panel_rammb")
    llamadas = {getattr(n.func, "id", getattr(n.func, "attr", ""))
                for n in ast.walk(panel) if isinstance(n, ast.Call)}
    assert "separar_edad" in llamadas


def test_vista_operacional_ofrece_la_regla():
    src = LIVE.read_text(encoding="utf-8")
    assert 'key="vg_regla"' in src
    assert "regla=_vg_regla" in src
