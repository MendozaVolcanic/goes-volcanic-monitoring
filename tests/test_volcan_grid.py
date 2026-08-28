"""Invariantes de la grilla 2x2 de productos por volcan.

Por que (pedido de operaciones, ago-2026): en una emergencia el operador no
puede ir producto por producto. Los 4 productos de imagen —GeoColor, Ash RGB,
SO2 y VOLCAT— tienen que estar en pantalla A LA VEZ, cada uno refrescandose
cuando le llega su dato.

Las vistas Streamlit no se renderizan headless, asi que igual que
test_legend_coverage.py y test_marker_sizes.py esto mezcla analisis estatico
del fuente con unidad sobre las funciones puras.
"""
import ast
import re
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent))

VIEW = (Path(__file__).parent.parent / "dashboard" / "views"
        / "modo_guardia_volcan.py")
LIVE = (Path(__file__).parent.parent / "dashboard" / "views"
        / "live_viewer.py")


def _func_source(path: Path, name: str) -> str:
    """Fuente de una funcion top-level, para afirmar sobre su cuerpo."""
    src = path.read_text(encoding="utf-8")
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return ast.get_source_segment(src, node) or ""
    raise AssertionError(f"no existe la funcion {name} en {path.name}")


def test_render_product_honra_la_altura_pedida():
    """En un 2x2 cada panel necesita su alto: 620 clavado no sirve."""
    from dashboard.views.modo_guardia_volcan import _render_product

    bounds = {"lat_min": -39.7, "lat_max": -39.0,
              "lon_min": -72.3, "lon_max": -71.6}
    img = np.zeros((8, 8, 3), dtype=np.uint8)

    fig = _render_product(img, bounds, "Ash RGB", -39.42, -71.93, "Villarrica",
                          height=410)
    assert fig.layout.height == 410

    # sin argumento mantiene el default historico (la vista de 3 columnas)
    fig_def = _render_product(img, bounds, "Ash RGB", -39.42, -71.93,
                              "Villarrica")
    assert fig_def.layout.height == 620


def test_la_grilla_declara_los_cuatro_productos():
    """GeoColor + Ash RGB + SO2 + VOLCAT, en ese orden de lectura.

    El orden no es estetico: es la secuencia con la que se lee una emergencia.
    GeoColor (hay columna?) -> Ash RGB (es ceniza?) -> SO2 (es gas fresco?) ->
    VOLCAT (que altura?).
    """
    from dashboard.views.modo_guardia_volcan import GRID_PANELS

    ids = [p["id"] for p in GRID_PANELS]
    assert ids == ["geocolor", "eumetsat_ash", "jma_so2", "volcat"], ids
    # 2x2 exacto: si alguien agrega un 5to hay que decidir el layout a mano
    assert len(GRID_PANELS) == 4


def test_volcat_pollea_mas_lento_que_rammb():
    """VOLCAT pasa por el procesamiento de SSEC y publica despues del scan ABI.

    Pegarle al API de SSEC al mismo ritmo que a RAMMB es gasto sin dato nuevo.
    """
    from dashboard.views.modo_guardia_volcan import GRID_PANELS

    cad = {p["id"]: p["refresh_s"] for p in GRID_PANELS}
    assert cad["volcat"] > cad["eumetsat_ash"]
    # ningun panel por debajo de 30 s: la cadencia del satelite es 10 min,
    # pollear mas rapido solo suma carga sin traer un scan nuevo
    for pid, s in cad.items():
        assert s >= 30, (pid, s)


def test_cada_panel_tiene_leyenda_declarable():
    """Guard del guard de test_legend_coverage: aca exigimos ademas que la
    clave del producto exista en el catalogo de leyendas."""
    from dashboard.map_helpers import _PRODUCT_LABELS_TV
    from dashboard.views.modo_guardia_volcan import GRID_PANELS

    for p in GRID_PANELS:
        assert p["id"] in _PRODUCT_LABELS_TV, p["id"]


def test_modo_sala_conserva_su_fila_de_tres():
    """El slot `tv=volcan` se PROYECTA en la sala de turno y arma su leyenda de
    3 columnas a mano (modo_guardia.py:771). Si la grilla le cambia el layout
    por debajo, la leyenda queda desalineada del grid que explica.

    Por eso el Modo Sala pasa un juego de paneles propio: los 3 de RAMMB, sin
    VOLCAT, en una fila.
    """
    from dashboard.views.modo_guardia_volcan import (GRID_PANELS,
                                                     GRID_PANELS_TV)

    assert [p["id"] for p in GRID_PANELS_TV] == [
        "geocolor", "eumetsat_ash", "jma_so2"]
    # y no es una copia a mano: son los mismos objetos de GRID_PANELS, para que
    # un cambio de receta o cadencia no quede aplicado en una sola de las dos
    for p in GRID_PANELS_TV:
        assert p in GRID_PANELS


def _fragment_run_every(path: Path, func_name: str) -> str | None:
    """run_every declarado en el decorador @st.fragment de `func_name`."""
    src = path.read_text(encoding="utf-8")
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef) or node.name != func_name:
            continue
        for dec in node.decorator_list:
            if not isinstance(dec, ast.Call):
                continue
            for kw in dec.keywords:
                if kw.arg == "run_every":
                    return ast.unparse(kw.value)
    return None


def test_hay_un_fragment_por_panel_no_uno_global():
    """Si un producto se cuelga, los otros tres tienen que seguir refrescando.

    Con un solo fragment global, RAMMB lento en SO2 congelaba el redibujo de
    Ash RGB.
    """
    assert _fragment_run_every(VIEW, "_panel_rammb") is not None
    assert _fragment_run_every(VIEW, "_panel_volcat") is not None


def test_los_paneles_no_reciben_el_timestamp_por_argumento():
    """Gotcha documentado en live_viewer.py:564-575 — los args de un fragment
    con run_every quedan CONGELADOS en el ultimo full-rerun. Un panel que
    reciba `ts` nunca veria un scan nuevo: tiene que pedirlo adentro."""
    src = VIEW.read_text(encoding="utf-8")
    tree = ast.parse(src)
    vistos = 0
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name in (
                "_panel_rammb", "_panel_volcat"):
            vistos += 1
            args = [a.arg for a in node.args.args]
            malos = [a for a in args if a in ("ts", "timestamp", "ts_label",
                                              "scan_ts", "meta", "img")]
            assert not malos, f"{node.name} recibe {malos} por argumento"
    assert vistos == 2, "faltan paneles por revisar"
