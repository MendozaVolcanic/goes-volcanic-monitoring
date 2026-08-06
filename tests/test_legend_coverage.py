"""Toda vista que dibuja un producto satelital explica cómo leerlo.

Por qué (auditoría ago-2026, pedido de operaciones): las leyendas compactas
existían casi sólo en el Modo Sala TV. El dashboard interactivo —el de uso
diario— mostraba Ash RGB, SO2 RGB y GeoColor sin decir qué significa cada
color, y la simbología que el propio dashboard dibuja encima (triángulo del
volcán, diamante del hot spot NOAA, anillos, vectores de viento) no estaba
documentada en NINGUNA vista. El caso que lo destapó: Modo Guardia → "Volcán
(3 productos)", 3 mapas y ninguna leyenda.

Este test es el guard: si una vista nueva pinta un producto y no llama a
`render_compact_legend`, falla acá y no en la sala de turno.
"""
import ast
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

VIEWS = Path(__file__).parent.parent / "dashboard" / "views"

# Vistas cuyas funciones de render NO muestran un producto satelital: son
# gráficos con su propia semántica (ejes rotulados, colorbar propia), donde una
# leyenda de RGB no aplica.
NO_PRODUCT_VIEWS = {"heatmap_actividad", "timeseries_viewer"}

# Funciones que pintan un producto pero delegan la leyenda en su llamador
# (el rotador de TV la pone como overlay para no restarle alto al grid).
DELEGATED = {
    ("zonas_fullscreen", "_render_volcat_zone_cell"),
    ("zonas_fullscreen", "_render_volcat_one_zona_tv"),
    ("zonas_fullscreen", "_render_volcat_zoom_tv"),
    ("volcat_viewer", "_render_acha_indicative_section"),
    ("volcat_viewer", "_render_height_section"),
    ("backfill_viewer", "_render_volcat_height"),
    ("comparador", "_mode_diff_temporal_panel"),
}

PRODUCT_HINTS = ("eumetsat_ash", "jma_so2", "geocolor", "PRODUCTS",
                 "PRODUCT_OPTIONS", "PRODUCT_LABELS", "product")
LEGEND_CALLS = {"render_compact_legend", "ash_legend", "btd_legend",
                "so2_legend", "ash_so2_legend"}


def _call_name(node):
    f = node.func
    if isinstance(f, ast.Attribute):
        return f.attr
    if isinstance(f, ast.Name):
        return f.id
    return ""


def _render_functions(path):
    """(nombre, nº de superficies, nº de leyendas, fuente) por función."""
    src = path.read_text(encoding="utf-8")
    tree = ast.parse(src)
    out = []
    for fn in [n for n in tree.body if isinstance(n, ast.FunctionDef)]:
        nr = nl = 0
        for node in ast.walk(fn):
            if isinstance(node, ast.Call):
                nm = _call_name(node)
                if nm in ("plotly_chart", "image"):
                    nr += 1
                if nm in LEGEND_CALLS:
                    nl += 1
        if nr:
            out.append((fn.name, nr, nl, ast.get_source_segment(src, fn) or ""))
    return out


def test_every_product_view_has_a_legend():
    """Toda función que renderiza un producto satelital llama a una leyenda."""
    missing = []
    for path in sorted(VIEWS.glob("*.py")):
        if path.stem in NO_PRODUCT_VIEWS:
            continue
        for name, _nr, nl, body in _render_functions(path):
            if nl or (path.stem, name) in DELEGATED:
                continue
            if any(h in body for h in PRODUCT_HINTS):
                missing.append(f"{path.stem}.{name}")

    assert not missing, (
        "estas funciones pintan un producto sin leyenda — usar "
        "map_helpers.render_compact_legend():\n  " + "\n  ".join(missing))


def test_compact_legend_declares_known_symbols():
    """Los glifos que piden las vistas existen (un typo dejaría el hueco que
    este trabajo vino a tapar, en silencio)."""
    from dashboard.map_helpers import _symbol_html

    known = {"volcano", "hotspot", "hotspot_frp", "rings", "wind"}
    for key in known:
        assert _symbol_html(key), key
    assert _symbol_html("noexiste") == ""

    # Se parsea el AST: los argumentos `symbols=` llevan paréntesis anidados
    # (`("wind",) if show_wind else ()`) que un regex plano corta por la mitad.
    used = set()
    for path in sorted(VIEWS.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            for kw in node.keywords:
                if kw.arg != "symbols":
                    continue
                # sólo los ELEMENTOS de las tuplas: las cadenas sueltas del
                # `test` de un condicional (`_pid == "eumetsat_ash"`) no son
                # glifos.
                for sub in ast.walk(kw.value):
                    if not isinstance(sub, ast.Tuple):
                        continue
                    for el in sub.elts:
                        if isinstance(el, ast.Constant) and isinstance(el.value, str):
                            used.add(el.value)
    assert used <= known, used - known
    # el trabajo cubrió los cuatro tipos de glifo
    assert used == known, known - used


def test_products_without_color_code_have_a_note_instead_of_swatches():
    """GeoColor es color real: un swatch 'blanco = nubes' sólo gasta la tira.
    Pero de noche NO es color real (IR + luces), y eso sí hay que decirlo."""
    from dashboard.map_helpers import _LEGEND_ITEMS, _PRODUCT_NOTES

    for prod in ("geocolor", "volcat"):
        assert _LEGEND_ITEMS[prod] == [], prod
        assert _PRODUCT_NOTES.get(prod), prod
    assert "noche" in _PRODUCT_NOTES["geocolor"].lower()

    # los productos CON código de color sí llevan swatches
    for prod in ("eumetsat_ash", "jma_so2"):
        assert len(_LEGEND_ITEMS[prod]) >= 3, prod


def test_tv_legend_keeps_its_overlay_class():
    """En Modo Sala la tira es overlay translúcido: sin la clase `tv-legend`
    el CSS de TV no la engancha y le roba alto al grid de mapas."""
    src = (VIEWS.parent / "map_helpers.py").read_text(encoding="utf-8")
    assert 'cls = "compact-legend tv-legend" if tv else "compact-legend"' in src

    # y los call-sites del Modo Sala lo piden explícitamente
    tv_sites = 0
    for path in sorted(VIEWS.glob("*.py")):
        tv_sites += len(re.findall(r"render_compact_legend\([^)]*tv=True",
                                   path.read_text(encoding="utf-8"), re.S))
    assert tv_sites >= 4, tv_sites


def test_wind_colors_are_shared_with_the_overlay():
    """La leyenda del viento usa los MISMOS colores que las flechas del mapa;
    si cada vista mantuviera su copia, la leyenda podría mentir."""
    from dashboard.map_helpers import WIND_LEVELS_VIZ

    assert [c for _l, _lbl, c in WIND_LEVELS_VIZ] == ["#ff4444", "#ffaa44",
                                                      "#44dd88"]
    offenders = [p.stem for p in sorted(VIEWS.glob("*.py"))
                 if re.search(r"^\s*(WIND_LEVELS_VIZ|LEVEL_VIZ)\s*=\s*\[",
                              p.read_text(encoding="utf-8"), re.M)]
    assert not offenders, (
        "definen su propia tabla de niveles de viento en vez de importar la "
        f"canónica de map_helpers: {offenders}")
