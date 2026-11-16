"""El Comparador ofrece todo el catalogo, con los prioritarios primero.

Por que (nov-2026): el Comparador solo ofrecia los 8 volcanes prioritarios.
Para comparar contra una anomalia vista en otro visor (Lastarria, por
ejemplo) hacia falta cualquier volcan, como en Replay y en la grilla.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def test_opciones_cubren_el_catalogo_con_prioritarios_primero():
    from dashboard.views.comparador import opciones_volcan
    from src.volcanos import CATALOG, PRIORITY_VOLCANOES
    ops = opciones_volcan()
    assert set(ops) == {v.name for v in CATALOG}
    assert len(ops) == len(set(ops))
    prior = [v.name for v in CATALOG if v.name in PRIORITY_VOLCANOES]
    assert ops[:len(prior)] == prior
    assert "Lastarria" in ops


def test_ningun_selector_del_comparador_se_limita_a_los_prioritarios():
    src = (Path(__file__).parent.parent / "dashboard" / "views"
           / "comparador.py").read_text(encoding="utf-8")
    assert "options=PRIORITY_VOLCANOES" not in src
    assert "in PRIORITY_VOLCANOES if" not in src


def test_cada_nombre_ofrecido_abre_su_propio_volcan():
    """get_volcano busca por coincidencia parcial: con todo el catalogo en el
    selector, un nombre contenido en otro abriria el volcan equivocado."""
    from dashboard.views.comparador import opciones_volcan
    from src.volcanos import get_volcano
    for nombre in opciones_volcan():
        assert get_volcano(nombre).name == nombre
