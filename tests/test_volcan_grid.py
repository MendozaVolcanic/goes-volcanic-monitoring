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
    # cuatro exactos: un 5to obliga a decidir el layout a mano (hoy sale de
    # _resolve_per_row: 4 en una fila en fullscreen, 2x2 en modo normal)
    assert len(GRID_PANELS) == 4


def test_volcat_pollea_mas_lento_que_rammb():
    """VOLCAT pasa por el procesamiento de SSEC y publica despues del scan ABI.

    Se lee del DECORADOR, no de una constante suelta: es el decorador el que
    gobierna el poll de verdad, y un campo declarativo aparte se desincroniza
    sin que nadie se entere.
    """
    from dashboard.views.modo_guardia_volcan import (RAMMB_REFRESH_S,
                                                     VOLCAT_REFRESH_S)

    assert _fragment_run_every(VIEW, "_panel_rammb") == "f'{RAMMB_REFRESH_S}s'"
    assert _fragment_run_every(VIEW, "_panel_volcat") == "f'{VOLCAT_REFRESH_S}s'"
    assert VOLCAT_REFRESH_S > RAMMB_REFRESH_S
    # la cadencia del satelite es 10 min: pollear mas rapido que 30 s solo
    # suma carga sin traer un scan nuevo
    assert RAMMB_REFRESH_S >= 30


def test_cada_panel_tiene_leyenda_declarable():
    """Guard del guard de test_legend_coverage: aca exigimos ademas que la
    clave del producto exista en el catalogo de leyendas."""
    from dashboard.map_helpers import _PRODUCT_LABELS_TV
    from dashboard.views.modo_guardia_volcan import GRID_PANELS

    for p in GRID_PANELS:
        assert p["id"] in _PRODUCT_LABELS_TV, p["id"]


def test_modo_sala_conserva_su_fila_de_tres():
    """El slot `tv=volcan` se PROYECTA en la sala de turno y su leyenda de 3
    columnas se arma en modo_guardia.py. Si la grilla le cambia el ORDEN por
    debajo, la leyenda rotula "Ash RGB" sobre el panel GeoColor.

    Por eso la sala conserva su orden historico (Ash primero), distinto al
    orden de lectura de emergencia de la grilla 2x2.
    """
    from dashboard.views.modo_guardia_volcan import (GRID_PANELS,
                                                     GRID_PANELS_TV)

    # Este literal ES el orden que la sala tiene interiorizado, no un detalle
    # de implementacion: hasta ago-2026 se comparaba contra la lista `PRODUCTS`,
    # que era la segunda fuente de verdad que este trabajo borro. Al quedarse
    # sin donde compararse, el orden se pinea aca a mano y a proposito —
    # cambiarlo es una decision operativa, no un refactor.
    assert [p["id"] for p in GRID_PANELS_TV] == ["eumetsat_ash", "geocolor",
                                                 "jma_so2"]
    ids_tv = [p["id"] for p in GRID_PANELS_TV]
    # y NO el de la grilla 2x2: si algun dia coinciden, que sea una decision
    assert ids_tv != [p["id"] for p in GRID_PANELS if p["kind"] == "rammb"]
    # identidad, no igualdad: `in` sobre dicts compara CONTENIDO, asi que una
    # copia literal a mano pasaria el test y romperia la fuente unica
    for p in GRID_PANELS_TV:
        assert any(p is q for q in GRID_PANELS)


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
    """Cada panel necesita su propia cadencia y su propio rerun PARCIAL.

    Streamlit serializa los reruns de fragment en el script runner de la
    sesion: un fragment colgado en una llamada de red igual bloquea a los
    demas. Lo que gana un fragment por panel es cadencia independiente (RAMMB
    a 60 s, VOLCAT a 120 s) y que el rerun de uno no redibuje la pagina
    entera — no aislamiento de fallas.
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


def test_todos_los_volcanes_del_catalogo_tienen_sector_volcat():
    """El panel VOLCAT no puede quedar en blanco para ningun volcan del RNVV.

    resolve_volcat_sector cae al sector regional por LATITUD cuando no hay uno
    dedicado, asi que nunca devuelve None. Si alguien cambia los umbrales de
    latitud y deja un hueco, se cae aca.
    """
    from src.fetch.volcat_api import resolve_volcat_sector
    from src.volcanos import CATALOG

    for v in CATALOG:
        sector, instr = resolve_volcat_sector(v)
        assert sector and instr, v.name


def test_la_etiqueta_de_sector_distingue_dedicado_de_regional():
    """Solo Copahue, Calbuco y Planchon-Peteroa tienen sector dedicado. El
    resto cae en un regional, donde la pluma se ve mas gruesa: si el rotulo no
    lo dice, una altura de 2 km de grilla se lee con confianza de 250 m."""
    from dashboard.views.modo_guardia_volcan import etiqueta_sector_volcat

    assert "dedicado" in etiqueta_sector_volcat("Copahue_250_m")
    assert "dedicado" in etiqueta_sector_volcat("Calbuco_1_km")
    assert "regional 2 km" in etiqueta_sector_volcat("Chile_South_2_km")
    # y la resolucion sale del nombre, no de un literal clavado en "2 km"
    assert "regional 5 km" in etiqueta_sector_volcat("Argentina_5_km")


def test_el_panel_volcat_usa_la_etiqueta_de_sector():
    cuerpo = _func_source(VIEW, "_panel_volcat")
    assert "etiqueta_sector_volcat" in cuerpo


def test_el_panel_volcat_explica_que_vacio_es_normal():
    """VOLCAT solo dibuja cuando detecta ceniza. Sin decirlo, un operador lee
    el panel vacio como 'se cayo el servicio' — y en una emergencia eso manda
    a buscar un problema que no existe."""
    cuerpo = _func_source(VIEW, "_panel_volcat")
    assert re.search(r"no es una falla|no detecta ceniza", cuerpo)


def test_el_panel_volcat_pone_su_leyenda():
    """_render_volcat_zoom_tv esta en la lista DELEGATED de
    test_legend_coverage: delega la leyenda en quien lo llama. Ese llamador
    somos nosotros."""
    cuerpo = _func_source(VIEW, "_panel_volcat")
    assert re.search(r'render_compact_legend\(\s*["\']volcat["\']', cuerpo)


def test_el_compositor_no_es_fragment():
    """Streamlit no permite fragments anidados: el que arma la grilla y llama
    a los paneles NO puede llevar decorador."""
    assert _fragment_run_every(VIEW, "volcan_grid") is None


def test_el_layout_lo_decide_el_encuadre_disponible():
    """La escena es CUADRADA (+-radio en lat y lon), asi que en una pantalla
    16:9 la dimension que escasea es el ALTO.

    En fullscreen, apilar dos filas parte justo esa dimension: medido a
    1920x1080, la imagen quedaba en ~245 px de lado con ~700 px de ancho VACIO
    al costado de cada panel. Cuatro columnas gastan el ancho, que sobra, y la
    imagen sube a ~462 px de lado (2.1x). En modo normal hay sidebar, el ancho
    baja a ~1400 px y ahi el 2x2 vuelve a ganar.

    Se pinea el COMPORTAMIENTO, no el valor del default: el default es None y
    lo que importa es a que resuelve en cada caso.
    """
    import inspect

    from dashboard.views.modo_guardia_volcan import (_resolve_per_row,
                                                     volcan_grid)

    assert _resolve_per_row(None, fullscreen=True) == 4
    assert _resolve_per_row(None, fullscreen=False) == 2
    # un per_row explicito manda: el slot de sala pide 3 porque su leyenda de
    # 3 columnas la arma el llamador
    assert _resolve_per_row(3, fullscreen=True) == 3
    assert _resolve_per_row(2, fullscreen=False) == 2

    sig = inspect.signature(volcan_grid)
    assert sig.parameters["per_row"].default is None   # -> lo decide el modo
    assert sig.parameters["panels"].default is None    # -> GRID_PANELS


def test_el_alto_de_la_sala_no_paga_el_cromo_de_la_pagina():
    """El slot `tv=volcan` no tiene tabs, toolbars ni badges arriba: su primer
    plot arranca en y=165 contra y~505 de la pagina. Descontarle el cromo de
    la pagina le sacaria ~350 px de imagen a la pared por nada."""
    from dashboard.views.modo_guardia_volcan import (GRID_CHROME_PAGE_PX,
                                                     GRID_CHROME_TV_PX)

    assert GRID_CHROME_TV_PX < GRID_CHROME_PAGE_PX


def test_la_grilla_recorre_los_paneles_declarados():
    """Sin hardcodear: agregar un panel a GRID_PANELS debe bastar."""
    cuerpo = _func_source(VIEW, "volcan_grid")
    assert "GRID_PANELS" in cuerpo
    assert "_panel_rammb" in cuerpo and "_panel_volcat" in cuerpo


GUARDIA = (Path(__file__).parent.parent / "dashboard" / "views"
           / "modo_guardia.py")


def test_modo_guardia_no_quedo_importando_una_funcion_que_no_existe():
    """_live_panel se fue en el refactor. Sus DOS llamadores en modo_guardia
    tienen que haber migrado, o la vista revienta con ImportError en runtime
    —y como el import es perezoso, no lo atrapa el smoke test de imports."""
    src = GUARDIA.read_text(encoding="utf-8")
    assert "modo_guardia_volcan import _live_panel" not in src
    assert src.count("volcan_grid") >= 2


def test_la_leyenda_de_sala_sale_del_mismo_orden_que_el_grid():
    """El slot `tv=volcan` se PROYECTA en la sala de turno. Su leyenda de 3
    columnas y el grid de abajo tienen que recorrer la MISMA lista, o la
    leyenda rotula un producto encima de otro.

    Antes eran dos literales separados (`["eumetsat_ash", "geocolor",
    "jma_so2"]` en modo_guardia y el orden de PRODUCTS en el panel): calzaban
    por casualidad.
    """
    src = GUARDIA.read_text(encoding="utf-8")
    assert "GRID_PANELS_TV" in src
    # el literal viejo ya no gobierna la leyenda
    assert '["eumetsat_ash", "geocolor", "jma_so2"]' not in src


def test_vista_operacional_no_esconde_productos_en_subtabs():
    """En emergencia no se navega tab por tab.

    El tab Volcan tenia `st.tabs(SUBTAB_LABELS)` (un producto a la vez) y un
    boton "Cargar volcan" antes de mostrar nada. Los dos se van: la grilla
    carga sola y muestra los 4 juntos.
    """
    src = LIVE.read_text(encoding="utf-8")
    assert "_v_geo, _v_ash, _v_so2 = st.tabs" not in src
    assert "btn_cargar_volc" not in src


def test_vista_operacional_reusa_la_grilla_compartida():
    """Una sola implementacion: si se duplica en live_viewer, las dos copias se
    desincronizan (paso con el preambulo de scene.py y con los tres caminos del
    marcador de volcan)."""
    src = LIVE.read_text(encoding="utf-8")
    assert "from dashboard.views.modo_guardia_volcan import volcan_grid" in src
    assert "volcan_grid(" in src


def test_el_radio_es_ajustable_y_llega_a_todos_los_paneles():
    """Una pluma de ceniza en emergencia viaja cientos de km: la vista de
    volcan no puede quedar clavada en +-0.35 grados (~38 km).

    Y el radio tiene que llegar a las CUATRO funciones que arman bbox, o los
    paneles se desalinean entre si y la grilla deja de leerse como una escena.
    """
    import inspect

    from dashboard.views import modo_guardia_volcan as MGV

    # `_tira_altura_propia` arma bbox igual que los paneles: es la ventana que
    # se le pide a S3 para el retrieval de altura. Con la constante clavada,
    # la altura se calcularia sobre un encuadre distinto al que se ve arriba.
    for nombre in ("volcan_grid", "_grid_header", "_panel_rammb",
                   "_panel_volcat", "_capture_button", "_tira_altura_propia"):
        sig = inspect.signature(getattr(MGV, nombre))
        assert "radius_deg" in sig.parameters, nombre
        assert sig.parameters["radius_deg"].default == MGV.RADIUS_DEG, nombre


def test_el_slider_de_radio_vuelve_a_vista_operacional():
    """La regresion concreta: al migrar a la grilla se perdio el slider."""
    src = LIVE.read_text(encoding="utf-8")
    assert 'key="vg_radius"' in src
    assert "radius_deg=_vg_radius" in src


def test_los_cuatro_paneles_encuadran_con_el_mismo_radio():
    """Si un solo lugar se queda con la constante, ese panel sale mas cerrado
    que los otros tres y se ve al toque en pantalla. Ningun bbox de la grilla
    puede seguir armandose con RADIUS_DEG literal.

    Lee VIEW (modo_guardia_volcan.py), que es donde viven los bbox de la
    grilla. Apuntaba a GUARDIA (modo_guardia.py), que no tiene ni un
    RADIUS_DEG ni un _crop_centered: el bucle quedaba vacio y los dos asserts
    pasaban por construccion (falso verde, ago-2026)."""
    src = VIEW.read_text(encoding="utf-8")
    for linea in src.splitlines():
        if "lat_min" in linea and "lat_max" in linea:
            assert "RADIUS_DEG" not in linea, linea.strip()
    # el crop del hi-res GeoColor tampoco (usaba la constante)
    assert "_crop_centered(h_arr, RADIUS_DEG" not in src


def _volcan_grid_call(path: Path, marca: str) -> ast.Call:
    """Llamada a volcan_grid que contiene `marca` entre sus keywords."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if (isinstance(node, ast.Call)
                and getattr(node.func, "id", "") == "volcan_grid"
                and marca in ast.unparse(node)):
            return node
    raise AssertionError(f"no hay llamada a volcan_grid con {marca}")


def test_el_slot_de_sala_conserva_su_alto():
    """El slot `tv=volcan` se proyecta 24/7 en la sala de turno.

    Al migrarlo a la grilla se le omitio `fullscreen`, asi que caia en
    PANEL_HEIGHT_NORMAL (380) cuando en main usaba el default de
    `_render_product` (620): 39% menos de alto en la pared. En ese camino el
    query param `fullscreen` SIEMPRE vale "1" (lo setea `_go_tv`), asi que la
    llamada tiene que pasarlo fijo.
    """
    from dashboard.views.modo_guardia_volcan import _panel_height

    call = _volcan_grid_call(GUARDIA, "GRID_PANELS_TV")
    kw = {k.arg: ast.unparse(k.value) for k in call.keywords}
    assert kw.get("fullscreen") == "True", kw

    # y con una sola fila (los 3 de RAMMB) el alto no baja del historico
    assert _panel_height(True, 1) >= 620
    # dos filas reparten la ventana, no pueden pedir 620 cada una
    assert _panel_height(True, 2) < _panel_height(True, 1)
    assert _panel_height(False, 2) == 380


def _hires_scene(monkeypatch, now):
    """Escena hi-res fresca de radio 0.5° + ruta RAMMB mockeada (sin red)."""
    import src.fetch.hires_cache as hires_cache
    from dashboard.views import modo_guardia_volcan as MGV

    arr = np.zeros((100, 100, 3), dtype=np.uint8)
    info = {"radius_deg": 0.5, "render": "visible_color",
            "scan_dt_iso": now.isoformat(),
            "scan_ts": now.strftime("%Y%m%d%H%M%S")}
    monkeypatch.setattr(hires_cache, "fetch_hires_for_volcano",
                        lambda name, mode="color": (arr, info))
    ts = now.strftime("%Y%m%d%H%M%S")
    monkeypatch.setattr(MGV, "_recent_timestamps", lambda p, n=3: [ts])
    monkeypatch.setattr(
        MGV, "_frame_with_fallback",
        lambda *a, **k: (np.zeros((4, 4, 3), dtype=np.uint8), ts,
                         MGV.ZOOM_VOLCAN))
    return MGV


def _bounds(lat, lon, r):
    return {"lat_min": lat - r, "lat_max": lat + r,
            "lon_min": lon - r, "lon_max": lon + r}


def test_el_hires_solo_se_usa_si_cubre_el_bbox_pedido(monkeypatch):
    """El guard `r_view <= r` de fetch_volcan_product es una cuestion de
    GEORREFERENCIA, no de estetica.

    El cache hi-res de GeoColor cubre ~0.5° alrededor del crater. Si la vista
    pide 2°, `_crop_centered` clampea la fraccion a 1.0 y devuelve la imagen de
    0.5° ENTERA, que el llamador pinta estirada sobre el bbox de 2°: la pluma
    queda dibujada a 4x de donde esta. Ahi hay que caer a RAMMB, que si baja
    los tiles del area pedida.
    """
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc)
    MGV = _hires_scene(monkeypatch, now)
    lat, lon = -23.37, -67.73

    # radio 0.35° (el de Modo Guardia): cabe en el cache -> usa hi-res
    _img, label = MGV.fetch_volcan_product(
        "geocolor", "Lascar", lat, lon, _bounds(lat, lon, 0.35), now)
    assert "hi-res L1b" in label, label

    # radio 2° (siguiendo una pluma lejos del crater): NO cabe -> RAMMB
    _img2, label2 = MGV.fetch_volcan_product(
        "geocolor", "Lascar", lat, lon, _bounds(lat, lon, 2.0), now)
    assert "hi-res L1b" not in label2, label2


# ── La leyenda no se pinta dos veces en la pared ──────────────────────
#
# El slot `tv=volcan` del Modo Sala arma SU propia fila de 3 leyendas (una por
# columna, derivada de GRID_PANELS_TV) y ademas cada panel pintaba la suya
# adentro: dos tiras identicas, ~60 px de alto en una pantalla proyectada donde
# cada pixel es imagen de satelite que el operador no ve.

ZONAS = (Path(__file__).parent.parent / "dashboard" / "views"
         / "zonas_fullscreen.py")

VIEWS_DIR = Path(__file__).parent.parent / "dashboard" / "views"


def _func_node(path: Path, name: str) -> ast.FunctionDef:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    raise AssertionError(f"no existe la funcion {name} en {path.name}")


def _llamadas(node, nombre: str) -> list[ast.Call]:
    out = []
    for n in ast.walk(node):
        if not isinstance(n, ast.Call):
            continue
        f = n.func
        if (isinstance(f, ast.Attribute) and f.attr == nombre) or (
                isinstance(f, ast.Name) and f.id == nombre):
            out.append(n)
    return out


def test_el_panel_dibuja_su_leyenda_salvo_que_el_llamador_ya_la_puso():
    """`show_legend` apaga la leyenda del panel, y por DEFECTO esta prendida.

    El default importa tanto como el flag: `_panel_rammb` se llama desde tres
    vistas y solo una (la sala) pone su propia fila. Si el default fuera False,
    las otras dos quedarian mostrando Ash RGB sin decir que significa cada
    color — que es justo el agujero que test_legend_coverage vino a tapar.
    """
    import inspect

    from dashboard.views.modo_guardia_volcan import _panel_rammb, volcan_grid

    for fn in (_panel_rammb, volcan_grid):
        params = inspect.signature(fn).parameters
        assert "show_legend" in params, fn.__name__
        assert params["show_legend"].default is True, fn.__name__

    # la unica leyenda del panel vive DENTRO del `if show_legend`: si quedara
    # suelta, el flag no apagaria nada y la pared seguiria con dos tiras.
    panel = _func_node(VIEW, "_panel_rammb")
    total = _llamadas(panel, "render_compact_legend")
    assert len(total) == 1, "una sola leyenda por panel"
    guardadas = [
        c for n in ast.walk(panel) if isinstance(n, ast.If)
        and any(isinstance(x, ast.Name) and x.id == "show_legend"
                for x in ast.walk(n.test))
        for b in n.body for c in _llamadas(b, "render_compact_legend")
    ]
    assert len(guardadas) == 1, "la leyenda del panel no esta bajo show_legend"

    # y el compositor lo PROPAGA: si se queda con el flag sin pasarlo, el slot
    # de sala lo pide y no pasa nada.
    assert "show_legend=show_legend" in _func_source(VIEW, "volcan_grid")


def test_el_slot_de_sala_apaga_la_leyenda_de_los_paneles():
    """La sala pinta su fila de 3 (con `tv=True`, que es overlay) ANTES del
    grid. Los paneles no tienen que repetirla."""
    tree = ast.parse(GUARDIA.read_text(encoding="utf-8"))
    llamadas = [c for c in _llamadas(tree, "volcan_grid")
                if any(kw.arg == "panels" for kw in c.keywords)]
    assert len(llamadas) == 1, "el slot tv=volcan es el unico que pide panels"
    kw = {k.arg: k.value for k in llamadas[0].keywords}
    assert "show_legend" in kw, "el slot de sala duplica la leyenda"
    assert isinstance(kw["show_legend"], ast.Constant)
    assert kw["show_legend"].value is False


def test_apagar_la_leyenda_solo_vale_si_el_llamador_pone_la_suya():
    """Tapa el agujero que test_legend_coverage NO puede ver.

    Ese test es analisis estatico: le basta con que la funcion CONTENGA una
    llamada a `render_compact_legend`, aunque en runtime quede bajo un `if` que
    nunca se cumple. O sea que `show_legend=False` lo deja verde igual. Este
    guard exige que quien apaga la leyenda del panel dibuje una el mismo.
    """
    for path in sorted(VIEWS_DIR.glob("*.py")):
        src = path.read_text(encoding="utf-8")
        if "show_legend=False" not in src:
            continue
        assert "render_compact_legend" in src, (
            f"{path.stem} apaga la leyenda del panel y no pone ninguna")


def test_volcat_no_lleva_el_flag_porque_la_sala_no_lo_proyecta():
    """YAGNI con evidencia: `_panel_volcat` tambien pinta leyenda, pero el
    unico llamador que apaga leyendas es el slot de sala, y ese usa
    GRID_PANELS_TV, que NO incluye VOLCAT. Darle el flag seria codigo muerto.

    Si algun dia VOLCAT entra a la fila de la sala, este test se pone rojo y
    avisa que ahi si hace falta.
    """
    import inspect

    from dashboard.views.modo_guardia_volcan import (GRID_PANELS_TV,
                                                     _panel_volcat)

    assert "volcat" not in [p["id"] for p in GRID_PANELS_TV]
    assert "show_legend" not in inspect.signature(_panel_volcat).parameters


def test_apagar_la_leyenda_le_devuelve_ese_alto_al_encuadre():
    """Sacar la tira duplicada no alcanza si el CSS la sigue reservando.

    En fullscreen el alto de cada panel es `(100vh - cromo) / filas`, y el
    cromo por fila incluye la leyenda compacta. Con `show_legend=False` esa
    tira ya no existe: si el reparto no lo sabe, la pared cambia una tira
    duplicada por una franja muerta del mismo alto, y el grid queda empujado
    contra el borde de arriba en vez de centrado.

    Lo que NO gana (medido, para que nadie lo prometa de nuevo): la imagen no
    crece. A 3 columnas el que manda es el ancho — Lascar 540x588 px, Hudson
    412x592 —, muy por debajo del alto disponible en las dos versiones.
    """
    from dashboard.views.modo_guardia_volcan import (GRID_CHROME_LEGEND_PX,
                                                     GRID_CHROME_ROW_PX,
                                                     _row_chrome_px)

    assert _row_chrome_px(True) == GRID_CHROME_ROW_PX
    assert _row_chrome_px(False) == GRID_CHROME_ROW_PX - GRID_CHROME_LEGEND_PX
    assert GRID_CHROME_LEGEND_PX > 0

    # el CSS de verdad: no alcanza con recibir el flag, tiene que ENTRAR en la
    # cuenta del reparto. Se captura el <style> que se inyecta.
    import dashboard.views.modo_guardia_volcan as MGV

    emitido = []
    orig = MGV.st.markdown
    MGV.st.markdown = lambda cuerpo, **kw: emitido.append(cuerpo)
    try:
        MGV._inject_fullscreen_css(1, con_cabecera=False, con_leyenda=True)
        MGV._inject_fullscreen_css(1, con_cabecera=False, con_leyenda=False)
    finally:
        MGV.st.markdown = orig

    reservado = [int(re.search(r"100vh - (\d+)px", css).group(1))
                 for css in emitido]
    assert reservado[0] - reservado[1] == GRID_CHROME_LEGEND_PX, reservado

    # y el compositor se lo dice al CSS: si `_inject_fullscreen_css` se entera
    # de las filas pero no de la leyenda, el reparto queda con el cromo viejo.
    cuerpo = _func_source(VIEW, "volcan_grid")
    assert re.search(r"_inject_fullscreen_css\(.*?con_leyenda=show_legend",
                     cuerpo, re.S), cuerpo


# ── Una sola fuente de las recetas ───────────────────────────────────


def test_no_quedo_una_segunda_lista_de_productos():
    """`PRODUCTS` convivia con `GRID_PANELS` con los mismos campos, y los
    textos YA habian divergido (la receta de GeoColor decia una cosa en cada
    lista). Dos fuentes de verdad de lo que se rotula sobre un mapa de ceniza.
    """
    src = VIEW.read_text(encoding="utf-8")
    assert not re.search(r"^PRODUCTS\s*=", src, re.M)
    for path in (ZONAS, GUARDIA, LIVE):
        cuerpo = path.read_text(encoding="utf-8")
        assert not re.search(
            r"modo_guardia_volcan import[^)]*\bPRODUCTS\b", cuerpo, re.S), (
            f"{path.stem} sigue importando PRODUCTS de modo_guardia_volcan")


def test_el_png_del_rotador_conserva_el_orden_de_la_sala():
    """El PNG del rotador TV se PROYECTA. Componia sus 3 paneles iterando
    `PRODUCTS`; ahora itera `GRID_PANELS_TV`, que existe justamente para
    conservar ese orden (Ash primero). Los rotulos van dentro del PNG, asi que
    un reordenamiento pone "Ash RGB" sobre el panel GeoColor en la pared.
    """
    from dashboard.views.modo_guardia_volcan import GRID_PANELS_TV

    assert [p["id"] for p in GRID_PANELS_TV] == ["eumetsat_ash", "geocolor",
                                                 "jma_so2"]
    assert [p["label"] for p in GRID_PANELS_TV] == ["Ash RGB", "GeoColor",
                                                    "SO2 RGB"]
    # el `map` ITERA la lista compartida, no una copia local: un literal a mano
    # deja la mencion en un comentario y el orden se va igual.
    compositor = _func_source(ZONAS, "_volcan_zoom_png")
    assert re.search(r"ex\.map\(_one,\s*GRID_PANELS_TV\)", compositor), compositor
    assert "PRODUCTS" not in compositor
