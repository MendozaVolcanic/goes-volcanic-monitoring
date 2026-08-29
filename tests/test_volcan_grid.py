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

    Por eso la sala conserva el orden historico de PRODUCTS (Ash primero),
    distinto al orden de lectura de emergencia de la grilla 2x2.
    """
    from dashboard.views.modo_guardia_volcan import (GRID_PANELS,
                                                     GRID_PANELS_TV, PRODUCTS)

    ids_tv = [p["id"] for p in GRID_PANELS_TV]
    assert ids_tv == ["eumetsat_ash", "geocolor", "jma_so2"]
    # el orden de la sala es el de PRODUCTS, que es lo que hoy se proyecta
    assert ids_tv == [pid for pid, _l, _r in PRODUCTS]
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


def test_la_grilla_es_2x2_por_default():
    """El encuadre del volcan es cuadrado (+-RADIUS_DEG en lat y lon). Cuatro
    paneles en una fila los deja angostos y desperdician el alto de la
    ventana, que es justo lo que se quiere aprovechar en una emergencia.

    El default tiene que ser 2: el Modo Sala pide 3 explicitamente, y si el
    default se corriera a 3 o 4 la vista operacional cambiaria sin que nadie
    lo pida.
    """
    import inspect

    from dashboard.views.modo_guardia_volcan import volcan_grid

    sig = inspect.signature(volcan_grid)
    assert sig.parameters["per_row"].default == 2
    assert sig.parameters["panels"].default is None  # -> GRID_PANELS


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

    for nombre in ("volcan_grid", "_grid_header", "_panel_rammb",
                   "_panel_volcat", "_capture_button"):
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
    puede seguir armandose con RADIUS_DEG literal."""
    src = GUARDIA.read_text(encoding="utf-8")
    for linea in src.splitlines():
        if "lat_min" in linea and "lat_max" in linea:
            assert "RADIUS_DEG" not in linea, linea.strip()
    # el crop del hi-res GeoColor tampoco (usaba la constante)
    assert "_crop_centered(h_arr, RADIUS_DEG" not in src
