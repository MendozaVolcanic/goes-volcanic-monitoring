# Grilla 2×2 de productos en la vista de volcán — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Que al seleccionar un volcán en Vista Operacional aparezcan GeoColor, Ash RGB, SO₂ y VOLCAT **los cuatro a la vez** en una grilla 2×2 que llena la ventana, cada panel refrescándose con su propia cadencia.

**Architecture:** Se **extiende** `dashboard/views/modo_guardia_volcan.py`, que ya hace 3 productos lado a lado, en vez de construir una grilla nueva en `live_viewer.py`. Hoy `_live_panel` es UN fragment que baja y redibuja los 3 productos juntos; se parte en un fragment por panel (`_panel_rammb`, `_panel_volcat`) más un compositor sin decorador (`volcan_grid`) que arma el 2×2. El 4º panel reusa `zonas_fullscreen._render_volcat_zoom_tv`, que ya resuelve sector, baja el frame SSEC y arma el plotly con las dos barras de color. El tab "🔬 Volcán" de `live_viewer` deja de tener botón "Cargar volcán" y sub-tabs, y pasa a llamar a `volcan_grid`.

**Tech Stack:** Streamlit (`st.fragment(run_every=…)`, `st.columns`), Plotly, numpy, RAMMB SLIDER, VOLCAT/SSEC RealEarth, NOAA FDCF, GFS.

---

## Por qué así (leer antes de tocar código)

**1. Una sola implementación.** `modo_guardia_volcan._live_panel` ya compone 3 productos con leyenda por columna, hot spots, viento y captura PNG. Construir la grilla de nuevo en `live_viewer` deja dos copias que se desincronizan — es el patrón que ya mordió a este repo con el preámbulo triplicado (`src/process/scene.py`) y con los tres caminos del marcador de volcán.

**2. Un fragment por panel, y cada fragment consulta su propio timestamp.** Está documentado en `live_viewer.py:564-575`: los argumentos de un fragment con `run_every` quedan **congelados** en el último full-rerun. Un panel que reciba `ts` como argumento nunca vería un scan nuevo. Cada panel pide su timestamp adentro.

**3. Cadencias distintas porque los datos llegan distinto.** Los tres RAMMB y VOLCAT son todos ABI 10 min, pero VOLCAT pasa por el procesamiento de SSEC y publica más tarde. Poll de 60 s para RAMMB, 120 s para VOLCAT: no tiene sentido pegarle al API de SSEC al mismo ritmo.

**4. VOLCAT casi siempre va a estar vacío, y eso es información.** `resolve_volcat_sector` nunca devuelve `None`, así que los 43 volcanes tienen panel. Pero sólo **Copahue, Calbuco y Planchón-Peteroa** tienen sector dedicado (250-500 m); los otros caen en un regional de 2 km. Y VOLCAT sólo dibuja cuando detecta ceniza. El panel tiene que decir *cuál sector está usando* y *que no hay pluma detectada*, no quedarse en blanco.

**5. El 5º panel (altura propia) queda fuera de esta tanda, con el slot preparado.** Medido contra S3 con caché frío (ago-2026): C11 25.8 MB / 35.4 s, C14 25.9 MB / 25.8 s, C15 25.6 MB / 28.7 s → **~78 MB y ~90 s por escena**, más GFS y el gránulo ACHA. Con cadencia de 10 min eso es del orden de 11 GB/día por usuario para concluir casi siempre "no hay ceniza". Cuando entre, va **disparado por condición**, no por poll: `_ash_red_fraction_v2` (`src/fetch/timeseries.py:63`) corre sobre el Ash RGB que el panel de al lado ya tiene en memoria (costo ≈ 0, filtra cirros y nieve) y sólo si supera umbral se baja la escena. Ojo: `CLAUDE.md` prohíbe **reportar** métricas automáticas de color de Ash RGB (30-60% de falsos positivos por cirros/nieve en invierno). Usarlo como **disparador** no viola esa regla — un falso positivo cuesta 90 s de descarga, no un número equivocado en pantalla. Que nadie lo convierta después en un "% de ceniza" mostrado.

## Cómo se testea en este repo

Las vistas Streamlit no se renderizan headless. Los tests existentes usan dos técnicas, y este plan sigue las mismas:

- **Análisis estático (AST/regex) sobre el fuente de la vista** — `tests/test_legend_coverage.py`, `tests/test_marker_sizes.py`.
- **Unidad sobre funciones puras** que devuelven un `go.Figure` o un dict, sin contexto de Streamlit — `_render_product` califica.

No inventar un harness de Streamlit.

---

## File Structure

| Archivo | Responsabilidad | Acción |
|---|---|---|
| `dashboard/views/modo_guardia_volcan.py` | Grilla de productos por volcán: composición, fragments por panel, overlays, captura | **Modificar** — es el corazón del cambio |
| `dashboard/views/modo_guardia.py` | Los dos llamadores de la grilla: sub-tab Volcán y slot TV del Modo Sala | **Modificar** — `:574` y `:771` |
| `dashboard/views/live_viewer.py` | Vista Operacional: el tab Volcán delega en la grilla compartida | **Modificar** — sacar botón + sub-tabs (líneas 1316-1420) |
| `tests/test_volcan_grid.py` | Invariantes de la grilla: 4 paneles, un fragment por panel, cadencias, leyenda VOLCAT | **Crear** |
| `tests/test_legend_coverage.py` | Ya exige leyenda por producto; debe seguir verde | — |
| `tests/test_marker_sizes.py` | Ya cubre el marcador; no se toca | — |
| `CLAUDE.md` | Patrón nuevo: grilla compartida + fragment por panel | **Modificar** |
| `INTEGRATION.md` | `last_updated` + producto nuevo en la vista operacional | **Modificar** |

---

## Task 1: `_render_product` acepta altura

Hoy la altura está clavada en `height=620`. En un 2×2 que llena la ventana cada panel necesita la suya.

**Files:**
- Modify: `dashboard/views/modo_guardia_volcan.py:294-298` (firma) y `:383` (layout)
- Test: `tests/test_volcan_grid.py`

- [ ] **Step 1: Escribir el test que falla**

Crear `tests/test_volcan_grid.py`:

```python
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
```

- [ ] **Step 2: Correr el test y verificar que falla**

```bash
python -m pytest tests/test_volcan_grid.py::test_render_product_honra_la_altura_pedida -v
```

Esperado: FAIL con `TypeError: _render_product() got an unexpected keyword argument 'height'`.

- [ ] **Step 3: Implementar**

En `dashboard/views/modo_guardia_volcan.py`, cambiar la firma (líneas 294-298) a:

```python
def _render_product(img: np.ndarray | None, bounds: dict, product_label: str,
                    volcan_lat: float, volcan_lon: float, volcan_name: str,
                    hotspots: list[HotSpot] | None = None,
                    show_wind: bool = False, wind_data: dict | None = None,
                    show_rings: bool = False,
                    height: int = 620):
```

y en el `update_layout` (línea ~383) reemplazar `height=620,` por `height=height,`.

- [ ] **Step 4: Correr el test y verificar que pasa**

```bash
python -m pytest tests/test_volcan_grid.py -v
```

Esperado: PASS.

- [ ] **Step 5: Commit**

```bash
git add tests/test_volcan_grid.py dashboard/views/modo_guardia_volcan.py
git commit -m "refactor(guardia-volcan): _render_product acepta altura por panel"
```

---

## Task 2: Descriptor de los 4 paneles y sus cadencias

**Files:**
- Modify: `dashboard/views/modo_guardia_volcan.py:53-66` (bloque de constantes)
- Test: `tests/test_volcan_grid.py`

- [ ] **Step 1: Escribir el test que falla**

Agregar a `tests/test_volcan_grid.py`:

```python
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
```

- [ ] **Step 2: Correr y verificar que falla**

```bash
python -m pytest tests/test_volcan_grid.py -v
```

Esperado: FAIL con `ImportError: cannot import name 'GRID_PANELS'`.

- [ ] **Step 3: Implementar**

En `dashboard/views/modo_guardia_volcan.py`, después del bloque `PRODUCTS` (línea 66), agregar:

```python
# ── Grilla 2x2 de la vista de volcan ─────────────────────────────────
#
# Los 4 productos de IMAGEN que tenemos, juntos en pantalla. En una emergencia
# el operador no puede ir tab por tab: la secuencia de lectura es GeoColor
# (hay columna?) -> Ash RGB (es ceniza?) -> SO2 (es gas fresco?) -> VOLCAT
# (que altura?), y por eso ese es el orden de la grilla.
#
# `refresh_s` es el poll de CADA panel, no un refresh global. Los cuatro son
# ABI 10 min, pero VOLCAT publica despues porque pasa por el procesamiento de
# SSEC: pegarle cada 60 s es gasto sin dato nuevo.
#
# `kind` decide el renderer: "rammb" pasa por fetch_volcan_product (que ya trae
# el switch hi-res de GeoColor); "volcat" reusa el panel del Modo Sala.
RAMMB_REFRESH_S = 60
VOLCAT_REFRESH_S = 120

GRID_PANELS = [
    {"id": "geocolor",     "label": "GeoColor",
     "recipe": "Visible mejorado (CIRA) · hi-res 0.5 km de dia",
     "kind": "rammb", "refresh_s": RAMMB_REFRESH_S},
    {"id": "eumetsat_ash", "label": "Ash RGB",
     "recipe": "EUMETSAT B15-B14 / B14-B11 / B13",
     "kind": "rammb", "refresh_s": RAMMB_REFRESH_S},
    {"id": "jma_so2",      "label": "SO2 RGB",
     "recipe": "JMA B07-B09 / B09-B11",
     "kind": "rammb", "refresh_s": RAMMB_REFRESH_S},
    {"id": "volcat",       "label": "VOLCAT · altura de pluma",
     "recipe": "SSEC/CIMSS (Pavolonis 2013) · solo dibuja si detecta ceniza",
     "kind": "volcat", "refresh_s": VOLCAT_REFRESH_S},
]

# El MODO SALA (slot `tv=volcan`) se queda con los 3 de RAMMB en UNA fila: se
# proyecta en la sala de turno y su llamador arma a mano una leyenda de 3
# columnas que tiene que calzar con el grid de abajo (modo_guardia.py:771).
# Es una VISTA de GRID_PANELS, no una copia: si cambia una receta o una
# cadencia, cambia en los dos lados a la vez.
GRID_PANELS_TV = [p for p in GRID_PANELS if p["kind"] == "rammb"]

# Alto por panel en la grilla 2x2. Fullscreen reparte la ventana entre 2 filas;
# el modo normal deja el panel mas bajo para que entren las dos filas sin
# scroll en un portatil.
PANEL_HEIGHT_NORMAL = 380
PANEL_HEIGHT_FULLSCREEN = 460
```

Las constantes `RAMMB_REFRESH_S` / `VOLCAT_REFRESH_S` van aparte y **antes** de `GRID_PANELS` porque el decorador `@st.fragment` se evalúa al importar el módulo: no puede leer `GRID_PANELS` por índice en tiempo de llamada. Referenciarlas desde el dict evita dos fuentes de verdad.

- [ ] **Step 4: Correr y verificar que pasa**

```bash
python -m pytest tests/test_volcan_grid.py -v
```

Esperado: PASS (4 tests).

- [ ] **Step 5: Commit**

```bash
git add tests/test_volcan_grid.py dashboard/views/modo_guardia_volcan.py
git commit -m "feat(guardia-volcan): descriptor de los 4 paneles con cadencia propia"
```

---

## Task 3: Un fragment por panel RAMMB

Hoy `_live_panel` es UN fragment que baja los 3 productos juntos: si RAMMB tarda en SO₂, se frena el redibujo de Ash RGB — justo el producto que se mira en una emergencia.

**Files:**
- Modify: `dashboard/views/modo_guardia_volcan.py` (agregar `_panel_rammb` antes de `_live_panel`)
- Test: `tests/test_volcan_grid.py`

- [ ] **Step 1: Escribir el test que falla**

Agregar a `tests/test_volcan_grid.py`:

```python
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
```

- [ ] **Step 2: Correr y verificar que falla**

```bash
python -m pytest tests/test_volcan_grid.py -v -k "fragment or timestamp"
```

Esperado: FAIL con `assert None is not None`.

- [ ] **Step 3: Implementar**

Agregar en `dashboard/views/modo_guardia_volcan.py`, justo antes de `_live_panel`:

```python
@st.fragment(run_every=f"{RAMMB_REFRESH_S}s")
def _panel_rammb(prod_id: str, label: str, recipe: str, volcan_name: str,
                 show_wind: bool, show_rings: bool, height: int):
    """Un panel RAMMB con su propio poll.

    NO recibe timestamp ni imagen por argumento: los args de un fragment con
    `run_every` quedan congelados en el ultimo full-rerun (ver
    live_viewer.py:564-575), asi que un `ts` pasado desde afuera nunca
    detectaria un scan nuevo. `fetch_volcan_product` consulta adentro, y su
    cache (TTL 7200 s por ts) evita la re-descarga.
    """
    v = get_volcano(volcan_name)
    if v is None:
        st.error(f"Volcan {volcan_name} no esta en el catalogo.")
        return

    bounds = {
        "lat_min": v.lat - RADIUS_DEG, "lat_max": v.lat + RADIUS_DEG,
        "lon_min": v.lon - RADIUS_DEG, "lon_max": v.lon + RADIUS_DEG,
    }
    now = datetime.now(timezone.utc)

    # Hot spots SOLO sobre Ash RGB: son el dato termico, y ponerlos en los tres
    # paneles triplica el ruido sin agregar informacion.
    hs = None
    if prod_id == "eumetsat_ash":
        hs, _ = _hotspots_volcan(bounds["lat_min"], bounds["lat_max"],
                                 bounds["lon_min"], bounds["lon_max"])
    wind = _wind_at_volcano(v.lat, v.lon) if show_wind else {}

    from dashboard.map_helpers import render_compact_legend
    render_compact_legend(
        prod_id, height_px=30,
        symbols=(("volcano",)
                 + (("hotspot",) if prod_id == "eumetsat_ash" else ())
                 + (("rings",) if show_rings else ())
                 + (("wind",) if (show_wind and wind) else ())),
    )

    img, ts_label = fetch_volcan_product(
        prod_id, v.name, v.lat, v.lon, bounds, now)
    st.plotly_chart(
        _render_product(img, bounds, f"{label} · {ts_label}",
                        v.lat, v.lon, v.name,
                        hotspots=hs, show_wind=show_wind, wind_data=wind,
                        show_rings=show_rings, height=height),
        width='stretch',
        config={"displayModeBar": False, "responsive": True},
        key=f"vgrid_{prod_id}_{volcan_name}",
    )
    st.markdown(
        f"<div style='font-size:0.7rem; color:#556; margin-top:-0.5rem;'>"
        f"{recipe}</div>",
        unsafe_allow_html=True,
    )
```

- [ ] **Step 4: Correr y verificar**

```bash
python -m pytest tests/test_volcan_grid.py -v -k timestamp
```

Esperado: PASS el de timestamps. El de fragments sigue fallando por `_panel_volcat` (Task 4).

- [ ] **Step 5: Commit**

```bash
git add tests/test_volcan_grid.py dashboard/views/modo_guardia_volcan.py
git commit -m "feat(guardia-volcan): un fragment por panel RAMMB con poll propio"
```

---

## Task 4: Panel VOLCAT

Reusa `zonas_fullscreen._render_volcat_zoom_tv`, que ya resuelve sector, baja el frame SSEC y arma el plotly con las dos barras de color. Import perezoso entre vistas: es el patrón ya usado en `modo_guardia._mosaico_subtab`.

**Files:**
- Modify: `dashboard/views/modo_guardia_volcan.py` (agregar `_panel_volcat` después de `_panel_rammb`)
- Test: `tests/test_volcan_grid.py`

- [ ] **Step 1: Escribir el test que falla**

Agregar a `tests/test_volcan_grid.py`:

```python
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


def test_el_panel_volcat_dice_que_sector_usa():
    """Solo Copahue, Calbuco y Planchon-Peteroa tienen sector dedicado; el
    resto cae en un regional de 2 km, donde la pluma se ve mucho mas gruesa.
    El operador tiene que saber cual esta mirando antes de sacar conclusiones
    de la altura."""
    cuerpo = _func_source(VIEW, "_panel_volcat")
    assert "resolve_volcat_sector" in cuerpo
    assert "sector" in cuerpo


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
```

- [ ] **Step 2: Correr y verificar que falla**

```bash
python -m pytest tests/test_volcan_grid.py -v -k volcat
```

Esperado: el de `CATALOG` pasa; los tres de `_panel_volcat` fallan con `AssertionError: no existe la funcion _panel_volcat`.

- [ ] **Step 3: Implementar**

Agregar en `dashboard/views/modo_guardia_volcan.py`, después de `_panel_rammb`:

```python
@st.fragment(run_every=f"{VOLCAT_REFRESH_S}s")
def _panel_volcat(volcan_name: str, height: int):
    """Panel VOLCAT: altura de pluma cuantitativa de SSEC/CIMSS.

    Reusa `zonas_fullscreen._render_volcat_zoom_tv` (import perezoso entre
    vistas, mismo patron que modo_guardia._mosaico_subtab): ese helper ya
    resuelve el sector, baja el frame y arma el plotly con las dos barras de
    color. Duplicarlo aca seria una tercera copia de la misma logica.

    Dos honestidades que el panel TIENE que mostrar:
    - Que sector esta usando. Solo Copahue, Calbuco y Planchon-Peteroa tienen
      sector dedicado (250-500 m); los otros 40 caen en un regional de 2 km,
      donde la pluma se ve mucho mas gruesa y la altura es mas incierta.
    - Que el panel vacio es lo NORMAL: VOLCAT solo dibuja cuando detecta
      ceniza.
    """
    from dashboard.map_helpers import render_compact_legend
    from src.fetch.volcat_api import resolve_volcat_sector

    v = get_volcano(volcan_name)
    if v is None:
        st.error(f"Volcan {volcan_name} no esta en el catalogo.")
        return

    sector, _instr = resolve_volcat_sector(v)
    dedicado = sector not in ("Chile_North_2_km", "Chile_Central_2_km",
                              "Chile_South_2_km", "Argentina_5_km")
    render_compact_legend("volcat", height_px=30, symbols=("volcano",))
    st.markdown(
        f"<div style='font-size:0.7rem; color:#7a8a9a; margin-bottom:0.2rem;'>"
        f"Sector <b>{sector.replace('_', ' ')}</b>"
        f"{' (dedicado)' if dedicado else ' (regional 2 km)'}"
        f" · sin dibujo = VOLCAT no detecta ceniza, no es una falla</div>",
        unsafe_allow_html=True,
    )

    from dashboard.views.zonas_fullscreen import _render_volcat_zoom_tv
    _render_volcat_zoom_tv(volcan_name, height=height, pad=RADIUS_DEG)
```

- [ ] **Step 4: Correr y verificar que pasa**

```bash
python -m pytest tests/test_volcan_grid.py -v -k "volcat or fragment"
```

Esperado: PASS.

- [ ] **Step 5: Commit**

```bash
git add tests/test_volcan_grid.py dashboard/views/modo_guardia_volcan.py
git commit -m "feat(guardia-volcan): panel VOLCAT como 4to producto de la grilla"
```

---

## Task 5: El compositor 2×2

**Files:**
- Modify: `dashboard/views/modo_guardia_volcan.py:529-643` (reemplazar `_live_panel`) y `:707` (llamada en `render()`)
- Test: `tests/test_volcan_grid.py`

- [ ] **Step 1: Escribir el test que falla**

Agregar a `tests/test_volcan_grid.py`:

```python
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
```

- [ ] **Step 2: Correr y verificar que falla**

```bash
python -m pytest tests/test_volcan_grid.py -v -k "compositor or grilla"
```

Esperado: FAIL con `AssertionError: no existe la funcion volcan_grid`.

- [ ] **Step 3: Implementar**

Reemplazar la definición completa de `_live_panel` (líneas 529-643, incluido su decorador `@st.fragment`) por estas tres funciones:

```python
@st.fragment(run_every=f"{RAMMB_REFRESH_S}s")
def _grid_header(volcan_name: str, show_wind: bool):
    """Cabecera: nombre, coords, viento, conteo de hot spots, hora de render.

    Fragment aparte y liviano: se refresca al ritmo de RAMMB sin arrastrar el
    redibujo de los cuatro mapas.
    """
    v = get_volcano(volcan_name)
    if v is None:
        return
    bounds = {
        "lat_min": v.lat - RADIUS_DEG, "lat_max": v.lat + RADIUS_DEG,
        "lon_min": v.lon - RADIUS_DEG, "lon_max": v.lon + RADIUS_DEG,
    }
    now = datetime.now(timezone.utc)
    hotspots, _ = _hotspots_volcan(bounds["lat_min"], bounds["lat_max"],
                                   bounds["lon_min"], bounds["lon_max"])
    wind = _wind_at_volcano(v.lat, v.lon) if show_wind else {}
    wind_summary = ""
    if wind:
        bits = []
        for level_id, _label, _c in WIND_LEVELS_VIZ:
            w = wind.get(level_id)
            if w:
                bits.append(
                    f"{level_id} {w['speed']:.0f} km/h@{w['direction']:.0f}°")
        if bits:
            wind_summary = " · " + " · ".join(bits)
    st.markdown(
        f"<div style='background:#0f1418; border-left:4px solid #ff6644; "
        f"padding:0.7rem 1rem; border-radius:4px; margin-bottom:0.8rem;'>"
        f"<div style='display:flex; justify-content:space-between; "
        f"align-items:center;'>"
        f"<div><span style='font-size:1.4rem; font-weight:800; color:#ff6644;'>"
        f"{v.name}</span> &nbsp;"
        f"<span style='color:#7a8a9a; font-size:0.85rem;'>"
        f"{v.region} · elev {v.elevation} m · {v.lat}°, {v.lon}°{wind_summary}"
        f"</span></div>"
        f"<div style='font-size:0.85rem; color:#9aaabb;'>"
        f"Hot spots {len(hotspots)} · Render {now.strftime('%H:%M:%S')} UTC / "
        f"{fmt_chile(now)}</div></div></div>",
        unsafe_allow_html=True,
    )


def _capture_button(v, show_wind: bool):
    """Boton de captura PNG con los 3 productos RAMMB + header.

    Re-pide las imagenes a `fetch_volcan_product`, que las sirve de su cache
    (TTL 7200 s por ts) — no hace falta compartir estado entre los fragments.
    VOLCAT queda fuera de la captura: su PNG se descarga aparte desde su propio
    panel, con su barra de color.
    """
    now = datetime.now(timezone.utc)
    bounds = {
        "lat_min": v.lat - RADIUS_DEG, "lat_max": v.lat + RADIUS_DEG,
        "lon_min": v.lon - RADIUS_DEG, "lon_max": v.lon + RADIUS_DEG,
    }
    hotspots, _ = _hotspots_volcan(bounds["lat_min"], bounds["lat_max"],
                                   bounds["lon_min"], bounds["lon_max"])
    wind = _wind_at_volcano(v.lat, v.lon) if show_wind else {}
    captured = []
    for prod_id, label, _recipe in PRODUCTS:
        img, ts_label = fetch_volcan_product(
            prod_id, v.name, v.lat, v.lon, bounds, now)
        captured.append((label, img, ts_label))
    try:
        png_bytes = _build_capture_png(
            v.name, v.lat, v.lon, v.elevation, v.region,
            captured, wind, len(hotspots), now,
        )
        st.download_button(
            label="📸 Descargar captura PNG (este momento)",
            data=png_bytes,
            file_name=f"{v.name}_{now.strftime('%Y%m%d_%H%M')}_UTC.png",
            mime="image/png",
            width='stretch',
        )
    except Exception as e:
        st.warning(f"No se pudo construir captura: {e}")


def volcan_grid(volcan_name: str, show_wind: bool = False,
                show_rings: bool = False, enable_capture: bool = False,
                fullscreen: bool = False, panels: list | None = None,
                per_row: int = 2, show_header: bool = True):
    """Grilla de productos del volcan, todos a la vez.

    FUENTE UNICA de esta vista — la usan el sub-tab Volcan del Modo Guardia,
    el tab Volcan de Vista Operacional y el slot `tv=volcan` del Modo Sala.
    No duplicarla.

    NO lleva @st.fragment: Streamlit no permite fragments anidados y los
    paneles de adentro ya son fragments, cada uno con su cadencia. Este nivel
    solo compone, y se re-ejecuta en el full-rerun (cambio de volcan o toggle).

    Default 2x2 y no una fila de 4 porque el encuadre es cuadrado
    (+-RADIUS_DEG en lat y lon): cuatro columnas dejan cada mapa angosto y
    desperdician el alto de la ventana.

    `panels` y `per_row` existen para el MODO SALA, que se proyecta en la sala
    de turno con su propia leyenda de 3 columnas armada por el llamador
    (modo_guardia.py:771). Ese slot sigue con los 3 RAMMB en una fila: cambiarle
    el layout por debajo le desalinearia la leyenda. `show_header=False` ahi
    mismo, porque el rotador TV ya pone su propia cabecera.
    """
    v = get_volcano(volcan_name)
    if v is None:
        st.error(f"Volcan {volcan_name} no esta en el catalogo.")
        return

    panels = GRID_PANELS if panels is None else panels
    height = PANEL_HEIGHT_FULLSCREEN if fullscreen else PANEL_HEIGHT_NORMAL
    if show_header:
        _grid_header(volcan_name, show_wind)

    filas = [panels[i:i + per_row] for i in range(0, len(panels), per_row)]
    for fila in filas:
        cols = st.columns(per_row)
        for col, panel in zip(cols, fila):
            with col:
                if panel["kind"] == "volcat":
                    _panel_volcat(volcan_name, height=height)
                else:
                    _panel_rammb(panel["id"], panel["label"], panel["recipe"],
                                 volcan_name, show_wind, show_rings, height)

    if enable_capture:
        _capture_button(v, show_wind)

    st.markdown(
        "<div style='text-align:center; color:#445566; font-size:0.75rem; "
        "margin-top:1rem; padding-top:0.5rem; border-top:1px solid #223;'>"
        "<i>Sin metricas automaticas — el dashboard muestra el dato. "
        "La interpretacion queda al experto.</i></div>",
        unsafe_allow_html=True,
    )
```

Finalmente, en `render()` (línea 707) reemplazar:

```python
    _live_panel(volcan, show_wind, show_rings, enable_capture)
```

por:

```python
    volcan_grid(volcan, show_wind, show_rings, enable_capture,
                fullscreen=st.query_params.get("fullscreen") == "1")
```

y en la cabecera de `render()` (línea ~660) cambiar el subtítulo
`"Zoom volcan · 3 productos lado a lado · GOES-19"` por
`"Zoom volcan · 4 productos en grilla · GOES-19 + VOLCAT"`.

- [ ] **Step 4: Correr el archivo entero más el guard de leyendas**

```bash
python -m pytest tests/test_volcan_grid.py tests/test_legend_coverage.py -v
```

Esperado: PASS todo. `test_legend_coverage` verde confirma que la vista sigue explicando cada producto que pinta.

- [ ] **Step 5: Commit**

```bash
git add tests/test_volcan_grid.py dashboard/views/modo_guardia_volcan.py
git commit -m "feat(guardia-volcan): grilla 2x2 reemplaza las 3 columnas"
```

---

## Task 6: Los dos llamadores de Modo Guardia

`_live_panel` desaparece en la Task 5, y **`modo_guardia.py` lo importa en dos lugares**. Si se saltea este paso, Modo Guardia revienta con `ImportError` en producción:

- `modo_guardia.py:574` — sub-tab **Volcán**: pasa a la grilla 2×2 completa.
- `modo_guardia.py:771` — slot **`tv=volcan` del Modo Sala**, el que se proyecta en la sala de turno. Se queda con los 3 de RAMMB en una fila, porque el llamador arma a mano una leyenda de 3 columnas que tiene que calzar con el grid de abajo, y además pone su propia cabecera.

**Files:**
- Modify: `dashboard/views/modo_guardia.py:572-574` y `:770-772`
- Test: `tests/test_volcan_grid.py`

- [ ] **Step 1: Escribir el test que falla**

Agregar a `tests/test_volcan_grid.py`:

```python
GUARDIA = (Path(__file__).parent.parent / "dashboard" / "views"
           / "modo_guardia.py")


def test_modo_guardia_no_quedo_importando_una_funcion_que_no_existe():
    """_live_panel se fue en el refactor. Sus DOS llamadores en modo_guardia
    tienen que haber migrado, o la vista revienta con ImportError en runtime
    —y como el import es perezoso, no lo atrapa el smoke test de imports."""
    src = GUARDIA.read_text(encoding="utf-8")
    assert "modo_guardia_volcan import _live_panel" not in src
    assert src.count("import volcan_grid") == 2


def test_el_slot_tv_pide_su_layout_explicito():
    """El Modo Sala se PROYECTA: su leyenda de 3 columnas la arma el llamador y
    tiene que calzar con el grid. Por eso pasa panels= y per_row= explicitos en
    vez de heredar el default 2x2."""
    src = GUARDIA.read_text(encoding="utf-8")
    assert "GRID_PANELS_TV" in src
    assert "per_row=3" in src
```

- [ ] **Step 2: Correr y verificar que falla**

```bash
python -m pytest tests/test_volcan_grid.py -v -k "modo_guardia or slot_tv"
```

Esperado: FAIL en los dos.

- [ ] **Step 3: Implementar**

En `dashboard/views/modo_guardia.py`, línea 574, reemplazar:

```python
    from dashboard.views.modo_guardia_volcan import _live_panel as volcan_panel
```

por:

```python
    from dashboard.views.modo_guardia_volcan import volcan_grid
```

y más abajo en `_volcan_subtab`, la llamada `volcan_panel(volcan, show_wind, show_rings, enable_capture)` por:

```python
    volcan_grid(volcan, show_wind, show_rings, enable_capture,
                fullscreen=st.query_params.get("fullscreen") == "1")
```

En la línea 771 (slot TV), reemplazar:

```python
            from dashboard.views.modo_guardia_volcan import _live_panel as volcan_panel
```

por:

```python
            from dashboard.views.modo_guardia_volcan import (GRID_PANELS_TV,
                                                             volcan_grid)
```

y la llamada de la línea 792-793 —**conservando sus argumentos actuales**, que no son los defaults: el slot TV va con anillos prendidos y sin captura—

```python
            volcan_panel(volcan_name, show_wind=False, show_rings=True,
                         enable_capture=False)
```

por:

```python
            # Modo Sala: los 3 de RAMMB en UNA fila y sin cabecera propia.
            # La leyenda de 3 columnas la arma este llamador unas lineas mas
            # arriba y tiene que calzar con el grid; VOLCAT no entra aca porque
            # tiene su propio slot en la rotacion, con su barra de color.
            volcan_grid(volcan_name, show_wind=False, show_rings=True,
                        enable_capture=False, panels=GRID_PANELS_TV,
                        per_row=3, show_header=False)
```

- [ ] **Step 4: Correr y verificar**

```bash
python -m pytest tests/test_volcan_grid.py tests/test_smoke.py -v
```

Esperado: PASS.

- [ ] **Step 5: Verificar el Modo Sala a ojo**

El import del slot TV es perezoso, así que ningún test de import lo cubre. Hay que abrirlo:

```bash
streamlit run dashboard/app.py --server.headless true --server.port 8503
```

Abrir `http://localhost:8503/?vista=guardia&fullscreen=1&tv=volcan&volcan=Villarrica` y confirmar que siguen siendo **3 paneles en una fila**, con la leyenda de 3 columnas alineada encima.

- [ ] **Step 6: Commit**

```bash
git add tests/test_volcan_grid.py dashboard/views/modo_guardia.py
git commit -m "refactor(guardia): los dos llamadores migran a volcan_grid"
```

---

## Task 7: Vista Operacional delega en la grilla

Hoy el tab "🔬 Volcán" pide apretar **Cargar volcán** y después ofrece 3 sub-tabs — dos clics por producto, exactamente el problema a resolver.

**Files:**
- Modify: `dashboard/views/live_viewer.py:1316-1420`
- Test: `tests/test_volcan_grid.py`

- [ ] **Step 1: Escribir el test que falla**

Agregar a `tests/test_volcan_grid.py`:

```python
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
```

- [ ] **Step 2: Correr y verificar que falla**

```bash
python -m pytest tests/test_volcan_grid.py -v -k operacional
```

Esperado: FAIL en los dos.

- [ ] **Step 3: Implementar**

En `dashboard/views/live_viewer.py`, reemplazar TODO el bloque del tab 5 (desde el comentario `# ── Tab 5: Volcán zoom=4 …` en la línea 1316 hasta el final de ese bloque, línea ~1420) por:

```python
    # ── Tab 5: Volcán — grilla 2×2 con los 4 productos ────────────────────
    # Delega en `modo_guardia_volcan.volcan_grid`, la MISMA grilla que usa el
    # sub-tab Volcán del Modo Guardia. Antes esto era un botón "Cargar volcán"
    # + 3 sub-tabs: dos clics por producto, justo lo que no se puede hacer con
    # un volcán en crisis. Import perezoso (gotcha de hot-reload de Streamlit
    # Cloud, documentado en la cabecera del módulo).
    with tab5:
        from dashboard.views.modo_guardia_volcan import volcan_grid

        col_vsel, col_vw, col_vr = st.columns([2.4, 1, 1])
        with col_vsel:
            priority_names = [v.name for v in CATALOG
                              if v.name in PRIORITY_VOLCANOES]
            other_names = [v.name for v in CATALOG
                           if v.name not in priority_names]
            volc_options = [f"★ {n}" for n in priority_names] + other_names
            sel_raw = st.selectbox("Volcán", volc_options, index=0,
                                   key="volc_sel")
            sel_name = sel_raw.replace("★ ", "")
        with col_vw:
            _vg_wind = st.toggle("💨 Viento", value=False, key="vg_wind",
                                 help="Vectores GFS 300/500/850 hPa sobre el "
                                      "cráter. Cache 1h.")
        with col_vr:
            _vg_rings = st.toggle("⊙ Anillos", value=False, key="vg_rings",
                                  help="Anillos 5/10/25/50 km desde el cráter.")

        volcan_grid(
            sel_name,
            show_wind=_vg_wind,
            show_rings=_vg_rings,
            enable_capture=True,
            fullscreen=st.query_params.get("fullscreen") == "1",
        )
```

Si al borrar el bloque viejo quedan `SUBTAB_LABELS` / `SUBTAB_PRODS` sin uso en las otras dos pestañas, dejarlos: los usan Nacional (línea ~1083) y Zona (línea ~1203).

- [ ] **Step 4: Correr los tres archivos de guard**

```bash
python -m pytest tests/test_volcan_grid.py tests/test_legend_coverage.py tests/test_marker_sizes.py -v
```

Esperado: PASS todo.

- [ ] **Step 5: Verificar en la app corriendo**

```bash
streamlit run dashboard/app.py --server.headless true --server.port 8503
```

Abrir `http://localhost:8503/?vista=operacional`, ir al tab **🔬 Volcán** y comprobar:
1. Los 4 paneles aparecen **sin apretar ningún botón**.
2. El panel VOLCAT dice qué sector usa y si es dedicado o regional.
3. En `?vista=operacional&fullscreen=1` la grilla ocupa el ancho completo.
4. Cambiar de volcán en el selector actualiza los 4 paneles.

- [ ] **Step 6: Commit**

```bash
git add tests/test_volcan_grid.py dashboard/views/live_viewer.py
git commit -m "feat(operacional): el tab Volcan muestra los 4 productos en grilla"
```

---

## Task 8: Documentación

**Files:**
- Modify: `CLAUDE.md` (sección "Patrones de código")
- Modify: `INTEGRATION.md` (frontmatter `last_updated` + producto)

- [ ] **Step 1: Agregar el patrón a CLAUDE.md**

Insertar en "Patrones de código", después del bullet de la leyenda de producto:

```markdown
- **Grilla de volcán: UNA implementación, un fragment por panel.** `modo_guardia_volcan.volcan_grid(volcan, …)` es la fuente única de la vista "todos los productos de un volcán a la vez" — la usan **tres** llamadores: el sub-tab Volcán del Modo Guardia, el tab 🔬 Volcán de Vista Operacional y el slot `tv=volcan` del Modo Sala. Los paneles, sus cadencias y su orden de lectura salen de `GRID_PANELS`. El slot de sala pasa `panels=GRID_PANELS_TV, per_row=3` explícitos porque se proyecta y su leyenda de 3 columnas la arma el llamador: cambiarle el layout por debajo la desalinea. Dos reglas la sostienen: (1) **el compositor NO lleva `@st.fragment`** — Streamlit no permite fragments anidados y los paneles de adentro ya lo son; (2) **ningún panel recibe timestamp ni imagen por argumento**, porque los args de un fragment con `run_every` quedan congelados en el último full-rerun (ver `live_viewer.py:564-575`) y nunca verían un scan nuevo. `tests/test_volcan_grid.py` falla si se rompe cualquiera de las dos.
- **VOLCAT vacío es el estado NORMAL.** Sólo dibuja cuando detecta ceniza, y sólo Copahue, Calbuco y Planchón-Peteroa tienen sector dedicado (250-500 m) — los otros 40 caen en un regional de 2 km vía `resolve_volcat_sector`. Todo panel VOLCAT tiene que decir qué sector usa y que la ausencia de dibujo no es una falla del servicio.
- **Altura de pluma propia: cara, va disparada por condición.** Medido ago-2026 contra S3 con caché frío: ~78 MB y ~90 s por escena (C11+C14+C15), más GFS y ACHA. No va en un panel con `run_every`. Cuando entre a la grilla, el disparador es `_ash_red_fraction_v2` (`src/fetch/timeseries.py:63`) sobre el Ash RGB que el panel vecino ya tiene en memoria. Ese uso como **gatillo** no contradice la regla de "no inventar métricas de color": un falso positivo por cirros cuesta una descarga, no un número equivocado en pantalla. No convertirlo nunca en un "% de ceniza" mostrado.
```

- [ ] **Step 2: Actualizar INTEGRATION.md**

Poner `last_updated` en la fecha del día y agregar VOLCAT a la lista de productos que la vista operacional expone por volcán.

- [ ] **Step 3: Correr la suite completa**

```bash
python -m pytest tests/ -q
```

Esperado: todo verde. Tarda ~8 min.

- [ ] **Step 4: Commit**

```bash
git add CLAUDE.md INTEGRATION.md
git commit -m "docs: patron de la grilla de volcan + costo del retrieval propio"
```

---

## Riesgos conocidos

| Riesgo | Mitigación |
|---|---|
| 4 paneles cargando a la vez en el primer render (antes era 1 a la vez, tras un botón) | Las 3 imágenes RAMMB son PNGs de pocos cientos de KB y `_frame` cachea 7200 s por ts. VOLCAT es un PNG más. Del orden de 1 MB, no de los 78 MB del retrieval propio. |
| Fragments concurrentes pegándole al mismo endpoint | `_recent_timestamps` (TTL 30 s) y `_volcat_latest_cached` (TTL_VOLCAT) absorben la estampida: el segundo panel que pregunta lo mismo lo saca del caché. |
| `_render_volcat_zoom_tv` vive en `zonas_fullscreen` (dependencia cruzada entre vistas) | Import perezoso dentro de la función, patrón ya usado en `modo_guardia._mosaico_subtab`. Si aparece un tercer llamador, ahí conviene moverlo a un `dashboard/panels.py`. |
| El nivel del marcador de volcán en paneles de 380-460 px | Siguen siendo zoom de UN volcán → nivel `focus`, que ya cumple `0.75·size − 2·trazo ≥ 2.0 px`. `tests/test_marker_sizes.py` lo cubre. |
| El slot TV del Modo Sala hereda el 2×2 sin querer | La Task 6 le pasa `panels=GRID_PANELS_TV, per_row=3` explícitos, y `test_el_slot_tv_pide_su_layout_explicito` lo pinea. El import de ese slot es perezoso: ningún test de import lo cubre, por eso la Task 6 incluye abrirlo a ojo. |

---

# Cómo terminó (post-mortem, 2026-08-29)

El plan se ejecutó completo, pero **se desvió en cinco puntos**. Se dejan escritos porque un plan que miente sobre lo que pasó es peor que ninguno.

**1. Las Tasks 5 y 6 se hicieron en un solo commit.** Separarlas dejaba un commit intermedio con `_live_panel` borrado y sus dos llamadores de `modo_guardia.py` rotos: una vista caída en producción. Sacar una función y migrar a quien la llama es un solo cambio.

**2. `GRID_PANELS_TV` tenía el orden equivocado.** El plan lo definía como `[p for p in GRID_PANELS if p["kind"] == "rammb"]`, o sea el orden de lectura de emergencia (GeoColor primero). Pero la leyenda de 3 columnas del Modo Sala itera el orden histórico de `PRODUCTS` (Ash primero). Al migrar el slot `tv=volcan`, **la pared que se proyecta en la sala de turno habría rotulado "Ash RGB" sobre el panel GeoColor**. Lo atrapó la revisión de las Tasks 1-4, antes de llegar a la sala. Ahora el orden de la sala es explícito y su leyenda se deriva de la misma lista que el grid.

**3. El Step 4 de la Task 3 estaba mal.** Decía que `test_los_paneles_no_reciben_el_timestamp_por_argumento` pasaba al terminar esa tarea, pero el test exige `vistos == 2` y `_panel_volcat` recién nace en la Task 4. El test queda en rojo a propósito entre las dos tareas.

**4. Tres tests del plan no probaban nada.** Demostrado mutando el código de producción y viéndolos seguir verdes:
- `assert "sector" in cuerpo` era subconjunto de `"resolve_volcat_sector"`, así que pasaba aunque el panel no mostrara el sector. Reemplazado por `etiqueta_sector_volcat`, una función pura testeada con entradas reales.
- `assert p in GRID_PANELS` compara **contenido** de dicts, no identidad: una copia literal a mano pasaba. Ahora es `any(p is q for q in GRID_PANELS)`.
- El campo `refresh_s` de `GRID_PANELS` era **inerte** — el poll lo gobierna el decorador `@st.fragment`, que lee las constantes de módulo. El campo se borró y el test ahora lee el decorador real vía `_fragment_run_every`.

**5. Faltaba el radio ajustable.** El plan no lo contemplaba, y al migrar el tab de Vista Operacional se perdió el slider de 0.5–3° que ese tab tenía: la vista quedaba clavada en el `RADIUS_DEG = 0.35` (~38 km) de Modo Guardia. Una pluma de ceniza en emergencia viaja cientos de km, así que eso achicaba justo el caso de uso que motivó el plan. Se agregó `radius_deg` como parámetro que se propaga a las cinco funciones que arman bbox.

Al hacerlo apareció un bug de georreferencia que el radio fijo tapaba: el caché hi-res de GeoColor cubre ~0.5° y `_crop_centered` clampea la fracción a 1.0, así que a radio 2° habría pintado la imagen de 0.5° entera sobre un bbox 4× más grande — **la pluma dibujada a 4× de donde está**. El guard `r_view <= r` cae a RAMMB en ese caso.

## Deuda que queda anotada

- **`PRODUCTS` sobrevive** porque `zonas_fullscreen.py:814` la importa para componer el PNG del rotador TV. Quedan dos fuentes de verdad de las recetas hasta que esa vista migre a `GRID_PANELS_TV`.
- **Leyenda duplicada en el slot de sala**: `modo_guardia.py` pinta su fila de 3 leyendas y además cada `_panel_rammb` pinta la suya. Verificado en la app corriendo. Es **preexistente** (el `_live_panel` viejo hacía lo mismo), pero en una pared proyectada son ~30 px de alto desperdiciados. Se arregla con un `show_legend` en `_panel_rammb`, análogo al `show_header` que ya existe.
- **Sin GeoTIFF al zoom de volcán**: el tab viejo ofrecía PNG + GeoTIFF por producto. La grilla ofrece un PNG compuesto. La exportación georreferenciada sigue disponible desde los tabs Nacional y Zona (`live_viewer._download_buttons`), así que no desapareció de la app.
