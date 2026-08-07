"""El mosaico de Modo Guardia son 5 volcanes × 3 productos.

Por qué (pedido OVDAS, ago-2026): antes eran los 8 de `PRIORITY_VOLCANOES` con
UN producto seleccionable. El turno mira siempre los mismos 5 y necesita ver
los tres RGB a la vez — Ash detecta la ceniza, SO2 el gas, GeoColor da el
contexto visible; mirarlos de a uno obliga a cambiar el selector tres veces
por volcán. Con 8 filas × 3 productos nada entra en pantalla, así que la lista
se acortó a propósito.

Estos tests fijan las dos decisiones que un refactor podría deshacer sin que
nadie note: QUÉ volcanes y que sean los TRES productos.
"""
import ast
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

VIEW = Path(__file__).parent.parent / "dashboard" / "views" / "mosaico_chile.py"

ESPERADOS = ["Nevados de Chillan", "Villarrica", "Calbuco", "Llaima",
             "Puyehue-Cordon Caulle"]


def test_mosaico_volcanoes_son_los_cinco_del_turno():
    """La lista es canónica en src/config y resuelve contra el catálogo real
    (un nombre mal escrito daría una celda vacía, no un error)."""
    from src.config import MOSAICO_VOLCANOES
    from src.volcanos import get_volcano

    assert MOSAICO_VOLCANOES == ESPERADOS, MOSAICO_VOLCANOES
    for name in MOSAICO_VOLCANOES:
        v = get_volcano(name)
        assert v is not None, f"{name} no está en el catálogo"
        assert v.name == name, f"{name} resuelve a {v.name}"


def test_mosaico_es_subconjunto_de_prioritarios():
    """Acortar la lista no puede meter un volcán que no sea prioritario: el
    mosaico es un recorte del set de vigilancia, no una lista aparte."""
    from src.config import MOSAICO_VOLCANOES
    from src.volcanos import PRIORITY_VOLCANOES

    fuera = set(MOSAICO_VOLCANOES) - set(PRIORITY_VOLCANOES)
    assert not fuera, fuera
    assert len(MOSAICO_VOLCANOES) < len(PRIORITY_VOLCANOES)


def test_mosaico_muestra_los_tres_productos():
    """La vista itera RGB_PRODUCTS (los 3), no un producto seleccionado."""
    from dashboard.map_helpers import RGB_PRODUCTS
    import dashboard.views.mosaico_chile as mosaico

    assert [p[0] for p in RGB_PRODUCTS] == ["eumetsat_ash", "geocolor",
                                            "jma_so2"]
    assert mosaico.RGB_PRODUCTS is RGB_PRODUCTS
    assert mosaico.MOSAICO_VOLCANOES == ESPERADOS


def test_el_grid_ya_no_recibe_un_producto():
    """`_grid_fragment` no toma `product`: si volviera a tomarlo, es que
    alguien reintrodujo el selector de un solo producto."""
    tree = ast.parse(VIEW.read_text(encoding="utf-8"))
    fn = next(n for n in tree.body
              if isinstance(n, ast.FunctionDef) and n.name == "_grid_fragment")
    args = [a.arg for a in fn.args.args]
    assert "product" not in args, args
    assert args == ["cell_px", "use_hires", "hires_mode"], args


def test_tamano_de_celda_es_elegible_y_creciente():
    """El alto de la celda lo elige el operador: el óptimo depende del ANCHO
    de su pantalla y Streamlit no expone el viewport.

    Medido en vivo con 3 columnas: si el alto queda por debajo del ancho de
    columna sobran franjas negras a los lados; si lo supera, Plotly RECORTA el
    frame (a 620 px sobre una columna de 373 se perdían 110 px de imagen). Por
    eso los tres pasos y no un valor fijo.
    """
    import dashboard.views.mosaico_chile as mosaico

    vals = list(mosaico.CELL_SIZES.values())
    assert vals == sorted(vals) and len(vals) == 3, mosaico.CELL_SIZES
    assert mosaico.DEFAULT_CELL_SIZE in mosaico.CELL_SIZES
    # el default tiene que ser mayor que el tamaño viejo de 4 columnas (380)
    assert mosaico.CELL_SIZES[mosaico.DEFAULT_CELL_SIZE] > 380


def test_el_producto_hires_solo_aplica_a_geocolor():
    """El cache hi-res de NOAA es color real / IR: no existe para las recetas
    Ash ni SO2. Pedirlo para esas columnas mostraría la banda equivocada."""
    src = VIEW.read_text(encoding="utf-8")
    assert 'if use_hires and pid == "geocolor":' in src


def test_las_celdas_tienen_key_estable():
    """15 plotly_chart en la misma página necesitan `key` propio; sin él
    Streamlit los colapsa y el grid se re-dibuja entero en cada refresh."""
    src = VIEW.read_text(encoding="utf-8")
    assert 'key=f"mosaico_{name}_{pid}"' in src
