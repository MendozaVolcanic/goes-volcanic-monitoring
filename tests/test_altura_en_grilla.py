"""La tira de altura propia: cuando se dispara y que promete.

Por que (sesion ago-30-2026): el retrieval propio de altura cuesta ~78 MB y
~90 s por escena, medido contra S3. No puede ir en un panel que se refresca
solo, y el disparador barato que se penso primero —la fraccion de rojo del Ash
RGB— resulto inservible: da 10-95% en volcanes SIN actividad.
"""
import ast
import inspect
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

VIEWS = Path(__file__).parent.parent / "dashboard" / "views"
VIEW = VIEWS / "modo_guardia_volcan.py"
LIVE = VIEWS / "live_viewer.py"
GUARDIA = VIEWS / "modo_guardia.py"


def _func_source(path: Path, name: str) -> str:
    src = path.read_text(encoding="utf-8")
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return ast.get_source_segment(src, node) or ""
    raise AssertionError(f"no existe la funcion {name} en {path.name}")


def _decorador_fragment(path: Path, name: str):
    """(existe_fragment, run_every) del decorador de `name`."""
    src = path.read_text(encoding="utf-8")
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef) or node.name != name:
            continue
        for dec in node.decorator_list:
            txt = ast.unparse(dec)
            if "fragment" in txt:
                m = re.search(r"run_every\s*=\s*([^,)]+)", txt)
                return True, (m.group(1) if m else None)
        return False, None
    raise AssertionError(f"no existe {name}")


def _llamadas_volcan_grid(path: Path) -> list[ast.Call]:
    """Todas las llamadas a `volcan_grid(...)` de un archivo."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return [n for n in ast.walk(tree)
            if isinstance(n, ast.Call)
            and getattr(n.func, "id", getattr(n.func, "attr", None))
            == "volcan_grid"]


def _kw(call: ast.Call, nombre: str):
    """Valor literal de un kwarg de la llamada, o None si no esta."""
    for kw in call.keywords:
        if kw.arg == nombre:
            return ast.literal_eval(kw.value)
    return None


def test_la_tira_no_se_refresca_sola():
    """El retrieval cuesta ~78 MB y ~90 s. Un `run_every` lo dispararia cada
    ciclo: del orden de 11 GB/dia por usuario para concluir casi siempre que no
    hay ceniza. Fragment SI (para que el boton no re-renderice la grilla
    entera), run_every NO.
    """
    existe, run_every = _decorador_fragment(VIEW, "_tira_altura_propia")
    assert existe, "tiene que ser fragment: si no, el boton rerenderiza todo"
    assert run_every is None, f"no puede auto-refrescarse (run_every={run_every})"


def test_el_disparo_automatico_es_por_hot_spot():
    """La fraccion de rojo del Ash RGB NO sirve de gatillo: medido sobre los 8
    prioritarios sin actividad da 9.9-95.5% (mediana 76%) en el encuadre de la
    grilla. Cualquier umbral absoluto dispara siempre o nunca.

    El gatillo es el hot spot FDCF: ya esta en memoria, lo valida NOAA, y
    CLAUDE.md lo privilegia.
    """
    cuerpo = _func_source(VIEW, "_tira_altura_propia")
    assert "_hotspots_volcan" in cuerpo
    assert "_ash_red_fraction" not in cuerpo, (
        "la metrica de color no sirve de gatillo — ver el plan")


def test_el_boton_queda_disponible_sin_hot_spot():
    """El caso freatico (Villarrica, Chillan) da columna de ceniza SIN hot
    spot. Si el unico disparo fuera automatico, ese caso quedaria sin medir."""
    cuerpo = _func_source(VIEW, "_tira_altura_propia")
    assert "st.button" in cuerpo


def test_la_tira_avisa_el_costo_antes_de_gastarlo():
    """78 MB y 90 s no se gastan a ciegas: el operador tiene que saberlo antes
    de apretar."""
    fuente = VIEW.read_text(encoding="utf-8")
    cuerpo = _func_source(VIEW, "_tira_altura_propia")
    # El texto del costo puede vivir en una constante compartida, pero la
    # funcion tiene que USARLO: sin eso el operador aprieta a ciegas.
    assert re.search(r"78\s*MB", fuente), "el costo medido tiene que estar escrito"
    assert re.search(r"~?90\s*s", fuente)
    assert re.search(r"78\s*MB|~?90\s*s|ALTURA_COSTO_TXT", cuerpo), (
        "la tira tiene que mostrar el costo antes de gastarlo")


def test_la_tira_dice_que_solo_mide_ceniza_ir_opaca():
    """Validado contra la pluma de Chillan del 27-jun: a una pluma de gas/SO2
    el retrieval le da un tope BAJO el crater. Un numero por debajo de la cota
    significa 'no encontro ceniza IR-opaca', no 'la pluma es baja'. Sin ese
    aviso, un operador lee un imposible fisico como una medicion.

    El aviso vive en `_render_altura`, que es quien presenta el numero.
    """
    cuerpo = _func_source(VIEW, "_render_altura")
    assert re.search(r"IR-opaca|IR opaca", cuerpo)
    assert re.search(r"gas|SO2|SO₂", cuerpo)
    assert re.search(r"bajo la cima|bajo el cr[áa]ter|\*\*bajo la cima\*\*",
                     cuerpo), (
        "tiene que avisar explicitamente el caso 'tope bajo la cima'")


def test_la_tira_no_la_usa_la_pared_de_la_sala():
    """El Modo Sala se proyecta sin nadie mirando. Una descarga de 78 MB
    disparada sola ahi no la ve venir nadie, y el slot no tiene quien aprete el
    boton."""
    from dashboard.views.modo_guardia_volcan import volcan_grid

    sig = inspect.signature(volcan_grid)
    assert sig.parameters["mostrar_altura"].default is False, (
        "por defecto apagada: la enciende quien la puede atender")


def test_la_enciende_vista_operacional():
    """Vista Operacional (tab Volcan) tiene operador delante: la enciende."""
    calls = _llamadas_volcan_grid(LIVE)
    assert len(calls) == 1, f"esperaba 1 llamada en live_viewer, hay {len(calls)}"
    assert _kw(calls[0], "mostrar_altura") is True


def test_el_slot_de_sala_la_deja_apagada_y_el_subtab_la_enciende():
    """En modo_guardia.py conviven los dos casos, y se distinguen por `panels`:
    el slot `tv=volcan` es el unico que pasa GRID_PANELS_TV. Ese se proyecta
    sin nadie delante; el sub-tab Volcan si tiene operador.
    """
    calls = _llamadas_volcan_grid(GUARDIA)
    assert len(calls) == 2, f"esperaba 2 llamadas, hay {len(calls)}"
    tv = [c for c in calls
          if any(k.arg == "panels" for k in c.keywords)]
    subtab = [c for c in calls if c not in tv]
    assert len(tv) == 1 and len(subtab) == 1

    assert _kw(tv[0], "mostrar_altura") in (None, False), (
        "la pared de la sala NO puede disparar una descarga de 78 MB sola")
    assert _kw(subtab[0], "mostrar_altura") is True
