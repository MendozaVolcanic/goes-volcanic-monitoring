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
