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


def _texto_en_pantalla(path: Path, name: str) -> str:
    """Todo el texto que la funcion `name` le PONE DELANTE al operador.

    Junta los literales de cadena que viajan como argumento de una llamada a
    `st.*` (st.info, st.warning, st.caption, st.button, st.markdown, ...),
    incluidas las partes constantes de las f-strings.

    POR QUE no basta con leer el fuente entero de la funcion (que es lo que
    hacia la primera version de estos tests): el DOCSTRING tambien es fuente.
    Verificado por mutacion (ago-2026): sacando "IR-opaca", "gas/SO2" y el
    costo de los `st.info` / `st.button` —o sea, de todo lo que el operador
    llega a leer— y dejandolos solo en el docstring, los tres tests seguian en
    VERDE. Un aviso que vive unicamente en el docstring no le avisa a nadie.
    """
    src = path.read_text(encoding="utf-8")
    tree = ast.parse(src)
    fn = next((n for n in ast.walk(tree)
               if isinstance(n, ast.FunctionDef) and n.name == name), None)
    if fn is None:
        raise AssertionError(f"no existe la funcion {name} en {path.name}")
    trozos: list[str] = []
    for nodo in ast.walk(fn):
        if not isinstance(nodo, ast.Call):
            continue
        f = nodo.func
        if not (isinstance(f, ast.Attribute) and getattr(f.value, "id", "") == "st"):
            continue
        for arg in list(nodo.args) + [k.value for k in nodo.keywords]:
            for sub in ast.walk(arg):
                if isinstance(sub, ast.Constant) and isinstance(sub.value, str):
                    trozos.append(sub.value)
                elif isinstance(sub, ast.Name):
                    # `ALTURA_COSTO_TXT` interpolado en una f-string: el texto
                    # real vive en la constante del modulo, y sustituirlo aca
                    # deja el assert mirando lo que el operador ve de verdad.
                    trozos.append(_constante_modulo(src, sub.id) or "")
    return " ".join(trozos)


def _constante_modulo(src: str, nombre: str) -> str | None:
    """Valor de una constante de modulo `NOMBRE = "..."`, si es una cadena."""
    for nodo in ast.parse(src).body:
        if (isinstance(nodo, ast.Assign)
                and any(getattr(t, "id", None) == nombre for t in nodo.targets)
                and isinstance(nodo.value, ast.Constant)
                and isinstance(nodo.value.value, str)):
            return nodo.value.value
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


def _cuerpo_sin_docstring(path: Path, name: str) -> ast.Module:
    """Cuerpo de una funcion top-level SIN su docstring.

    POR QUE: `_func_source` devuelve el segmento entero, prosa incluida, asi que
    un `assert "X" in cuerpo` lo satisface el DOCSTRING. Verificado por mutacion
    (ago-2026): la version anterior de los dos tests de disparo pasaba con
    `auto = False` clavado y con el boton metido dentro del `if` del hot spot,
    porque el docstring nombra `_hotspots_volcan` y "boton".
    """
    src = path.read_text(encoding="utf-8")
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            cuerpo = list(node.body)
            if (cuerpo and isinstance(cuerpo[0], ast.Expr)
                    and isinstance(cuerpo[0].value, ast.Constant)
                    and isinstance(cuerpo[0].value.value, str)):
                cuerpo = cuerpo[1:]
            return ast.Module(body=cuerpo, type_ignores=[])
    raise AssertionError(f"no existe la funcion {name} en {path.name}")


def _asignaciones(mod: ast.AST) -> dict[str, list[ast.AST]]:
    """nombre -> valores que se le asignan (desarmando targets de tupla)."""
    out: dict[str, list[ast.AST]] = {}
    for nodo in ast.walk(mod):
        if not isinstance(nodo, (ast.Assign, ast.AnnAssign)):
            continue
        targets = (nodo.targets if isinstance(nodo, ast.Assign)
                   else [nodo.target])
        if nodo.value is None:
            continue
        for t in targets:
            elts = t.elts if isinstance(t, (ast.Tuple, ast.List)) else [t]
            for e in elts:
                if isinstance(e, ast.Name):
                    out.setdefault(e.id, []).append(nodo.value)
    return out


def _llama_a(llamadas: set, funcion: str) -> bool:
    """`funcion` se compara por PREFIJO, no por igualdad.

    Por que: el fetch de hot spots tiene mas de una puerta —`_hotspots_volcan`
    y su envoltorio `_hotspots_volcan_seguro`, que atrapa el fallo de FDCF sin
    perder el testigo `scan_dt`— y van a poder aparecer mas. Lo que este test
    vigila es que el disparo dependa del HOT SPOT, no de cual de las puertas se
    use; con igualdad exacta, envolver la llamada rompia el test sin que el
    comportamiento cambiara. (audit 2026-08-30)
    """
    return any(str(l).startswith(funcion) for l in llamadas)


def _derivados_de(asigs: dict, funcion: str) -> set:
    """Nombres cuyo valor sale (directa o transitivamente) de `funcion(...)`.

    Es la parte que un substring no puede hacer: distingue `auto = bool(hotspots)`
    —que depende del retorno de `_hotspots_volcan`— de `auto = False`, que no
    depende de nada aunque el archivo siga nombrando la funcion mas arriba.
    """
    derivados: set = set()
    cambio = True
    while cambio:
        cambio = False
        for nombre, valores in asigs.items():
            if nombre in derivados:
                continue
            for v in valores:
                llamadas = {getattr(n.func, "id", getattr(n.func, "attr", ""))
                            for n in ast.walk(v) if isinstance(n, ast.Call)}
                nombres = {n.id for n in ast.walk(v)
                           if isinstance(n, ast.Name)}
                if _llama_a(llamadas, funcion) or (nombres & derivados):
                    derivados.add(nombre)
                    cambio = True
                    break
    return derivados


def _es_st_button(nodo: ast.AST) -> bool:
    return (isinstance(nodo, ast.Call) and isinstance(nodo.func, ast.Attribute)
            and nodo.func.attr == "button"
            and getattr(nodo.func.value, "id", "") == "st")


def _gatillo(mod: ast.Module) -> tuple[ast.BoolOp, set]:
    """(BoolOp que decide si se corre el retrieval, nombres del hot spot).

    Se localiza por FORMA, no por nombre de variable: la unica expresion
    booleana del cuerpo que contiene un `st.button(...)`. Asi el test sobrevive
    a que se renombre `correr`, pero no a que el boton deje de ser una rama.
    """
    asigs = _asignaciones(mod)
    hs = _derivados_de(asigs, "_hotspots_volcan")
    boolops = [n for n in ast.walk(mod) if isinstance(n, ast.BoolOp)
               and any(_es_st_button(s) for s in ast.walk(n))]
    assert len(boolops) == 1, (
        "el disparo tiene que ser UNA expresion booleana con el boton como "
        f"rama; encontradas {len(boolops)}. Si el boton quedo dentro de un "
        "`if`, el caso freatico no tiene como dispararse.")
    return boolops[0], hs


def test_el_disparo_automatico_es_por_hot_spot():
    """La fraccion de rojo del Ash RGB NO sirve de gatillo: medido sobre los 8
    prioritarios sin actividad da 9.9-95.5% (mediana 76%) en el encuadre de la
    grilla. Cualquier umbral absoluto dispara siempre o nunca.

    El gatillo es el hot spot FDCF: ya esta en memoria, lo valida NOAA, y
    CLAUDE.md lo privilegia.

    LIMITE CONOCIDO (mismo que documenta test_legend_coverage): las vistas
    Streamlit no se renderizan headless, asi que no se puede ejecutar la tira
    con y sin hot spot y mirar si dispara. Lo que si se puede pinear es el flujo
    de DATOS: que la rama automatica del disparo dependa del retorno de
    `_hotspots_volcan` y no de una constante. Eso es lo que mata la mutacion
    `auto = False`, que la version por substring dejaba en verde.
    """
    mod = _cuerpo_sin_docstring(VIEW, "_tira_altura_propia")
    asigs = _asignaciones(mod)
    hs = _derivados_de(asigs, "_hotspots_volcan")
    assert hs, ("el cuerpo (no el docstring) tiene que llamar a "
                "_hotspots_volcan y usar su resultado")

    gatillo, _ = _gatillo(mod)
    assert isinstance(gatillo.op, ast.Or), (
        "tiene que ser un `or`: con `and` el boton no alcanza solo y el caso "
        "freatico se queda sin medir")

    # La rama AUTOMATICA es la que no es el boton, y tiene que depender del hot
    # spot. `auto = False` no depende de nada -> rojo.
    auto = [v for v in gatillo.values if not _es_st_button(v)]
    assert auto, "el `or` perdio su rama automatica"
    for rama in auto:
        usados = {n.id for n in ast.walk(rama) if isinstance(n, ast.Name)}
        llamadas = {getattr(n.func, "id", getattr(n.func, "attr", ""))
                    for n in ast.walk(rama) if isinstance(n, ast.Call)}
        assert (usados & hs) or _llama_a(llamadas, "_hotspots_volcan"), (
            f"la rama automatica {ast.unparse(rama)!r} no depende del hot "
            f"spot: quedo clavada, o el gatillo cambio de fuente")

    # y la metrica de color sigue descartada — sobre el CODIGO, no el docstring
    codigo = ast.unparse(mod)
    assert "_ash_red_fraction" not in codigo, (
        "la metrica de color no sirve de gatillo — ver el plan")


def test_el_boton_queda_disponible_sin_hot_spot():
    """El caso freatico (Villarrica, Chillan) da columna de ceniza SIN hot
    spot. Si el unico disparo fuera automatico, ese caso quedaria sin medir.

    Se pinea la SEMANTICA de cortocircuito, no el texto: el boton tiene que ser
    una rama del `or` a la DERECHA de la rama automatica, de modo que Python lo
    evalue —y Streamlit lo dibuje— exactamente cuando NO hay hot spot. Y no
    puede estar anidado bajo ningun `if` que dependa del hot spot: ahi seria
    justo el bug que este test vino a atrapar.
    """
    mod = _cuerpo_sin_docstring(VIEW, "_tira_altura_propia")
    gatillo, hs = _gatillo(mod)

    botones = [n for n in ast.walk(mod) if _es_st_button(n)]
    assert len(botones) == 1, f"esperaba un solo st.button, hay {len(botones)}"
    boton = botones[0]

    # 1) es rama del or, y NO la primera: el cortocircuito lo salta cuando la
    #    rama automatica ya es verdadera, y lo dibuja cuando no hay hot spot.
    assert any(_es_st_button(v) for v in gatillo.values[1:]), (
        "el boton tiene que ser la rama derecha del `or`: "
        f"{ast.unparse(gatillo)}")
    assert not _es_st_button(gatillo.values[0]), (
        "con el boton primero, se dibuja siempre y el hot spot deja de "
        "disparar nada")

    # 2) no vive dentro de ningun `if` que mire el hot spot (la mutacion que la
    #    version por substring dejaba en verde).
    for nodo in ast.walk(mod):
        if not isinstance(nodo, ast.If):
            continue
        test_nombres = {n.id for n in ast.walk(nodo.test)
                        if isinstance(n, ast.Name)}
        test_llamadas = {getattr(n.func, "id", getattr(n.func, "attr", ""))
                         for n in ast.walk(nodo.test) if isinstance(n, ast.Call)}
        if not ((test_nombres & hs) or _llama_a(test_llamadas, "_hotspots_volcan")):
            continue
        anidados = [x for cuerpo in (nodo.body, nodo.orelse)
                    for s in cuerpo for x in ast.walk(s) if _es_st_button(x)]
        assert boton not in anidados, (
            f"el boton quedo dentro de `if {ast.unparse(nodo.test)}`: sin hot "
            "spot no hay como pedir el calculo, y la columna freatica se "
            "queda sin altura")


def test_la_tira_avisa_el_costo_antes_de_gastarlo():
    """78 MB y 90 s no se gastan a ciegas: el operador tiene que saberlo antes
    de apretar."""
    fuente = VIEW.read_text(encoding="utf-8")
    assert re.search(r"78\s*MB", fuente), "el costo medido tiene que estar escrito"
    assert re.search(r"~?90\s*s", fuente)
    # Y tiene que llegar A LA PANTALLA, no quedarse en el docstring: el costo
    # puede vivir en ALTURA_COSTO_TXT, pero interpolado en algo que se muestra.
    pantalla = _texto_en_pantalla(VIEW, "_tira_altura_propia")
    assert re.search(r"78\s*MB", pantalla), (
        f"el operador tiene que ver el costo antes de apretar: {pantalla!r}")
    assert re.search(r"~?90\s*s", pantalla)


def test_la_tira_dice_que_solo_mide_ceniza_ir_opaca():
    """Validado contra la pluma de Chillan del 27-jun: a una pluma de gas/SO2
    el retrieval le da un tope BAJO el crater. Un numero por debajo de la cota
    significa 'no encontro ceniza IR-opaca', no 'la pluma es baja'. Sin ese
    aviso, un operador lee un imposible fisico como una medicion.

    El aviso vive en `_render_altura`, que es quien presenta el numero, y se
    mide sobre lo que llega A LA PANTALLA: dejarlo solo en el docstring
    satisfacia la primera version de este test sin avisarle a nadie.
    """
    pantalla = _texto_en_pantalla(VIEW, "_render_altura")
    assert re.search(r"IR-opaca|IR opaca", pantalla), pantalla
    assert re.search(r"gas|SO2|SO₂", pantalla), pantalla
    assert re.search(r"bajo la cima|bajo el cr[áa]ter", pantalla), (
        f"tiene que avisar explicitamente el caso 'tope bajo la cima': {pantalla!r}")


def test_la_tira_no_la_usa_la_pared_de_la_sala():
    """El Modo Sala se proyecta sin nadie mirando. Una descarga de 78 MB
    disparada sola ahi no la ve venir nadie, y el slot no tiene quien aprete el
    boton."""
    from dashboard.views.modo_guardia_volcan import volcan_grid

    sig = inspect.signature(volcan_grid)
    assert sig.parameters["mostrar_altura"].default is False, (
        "por defecto apagada: la enciende quien la puede atender")


def test_la_grilla_dibuja_la_tira_cuando_se_la_piden():
    """El flag no vale nada si `volcan_grid` no lo honra: los llamadores
    pueden pasar `mostrar_altura=True` y la tira no aparecer nunca. Este caso
    sobrevivio a la primera tanda de mutaciones (M10, ago-2026).

    Y la llamada tiene que ir GUARDADA por el flag: sin el `if`, la tira
    apareceria tambien en la pared de la sala.
    """
    tree = ast.parse(VIEW.read_text(encoding="utf-8"))
    grid = next(n for n in ast.walk(tree)
                if isinstance(n, ast.FunctionDef) and n.name == "volcan_grid")

    guardadas = [
        nodo for nodo in ast.walk(grid)
        if isinstance(nodo, ast.If)
        and "mostrar_altura" in ast.unparse(nodo.test)
        and "_tira_altura_propia(" in "".join(
            ast.unparse(s) for s in nodo.body)
    ]
    assert guardadas, (
        "volcan_grid tiene que llamar a _tira_altura_propia bajo `if "
        "mostrar_altura`")
    # El radio tiene que viajar: la tira arma el bbox de la descarga, y con la
    # constante calcularia la altura sobre un encuadre distinto al que se ve.
    llamada = "".join(ast.unparse(s) for s in guardadas[0].body)
    assert "radius_deg=radius_deg" in llamada, llamada


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
