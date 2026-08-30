# Altura de pluma propia en la vista de volcán — Implementation Plan

**Goal:** Que la altura de tope calculada por nosotros (Wen-Rose / BT-matching / ACHA) esté disponible en la vista de volcán de Vista Operacional, sin bloquear la grilla ni gastar 78 MB cuando no hay nada que medir.

**Architecture:** Una **tira de medición debajo de la grilla**, no un 5º panel de imagen. Es un `@st.fragment` **sin `run_every`**, que se dispara solo cuando hay hot spot NOAA FDCF en el encuadre y ofrece un botón explícito el resto del tiempo. Reusa los wrappers cacheados que ya existen en `volcat_viewer`.

---

## Los tres hechos que fijan el diseño

**1. El retrieval cuesta ~78 MB y ~90 s por escena.** Medido contra S3 con caché frío (ago-2026): C11 25.8 MB / 35.4 s, C14 25.9 MB / 25.8 s, C15 25.6 MB / 28.7 s, más el perfil GFS y el gránulo ACHA. Eso descarta un panel con `run_every`: a cadencia de 10 min serían ~11 GB/día por usuario.

**2. El disparador por color NO funciona.** El plan original proponía `_ash_red_fraction_v2` (`src/fetch/timeseries.py:63`) como gatillo barato. Medido sobre los 8 volcanes prioritarios **sin actividad reportada**, en los dos encuadres:

| Encuadre | Rango observado | Mediana |
|---|---|---|
| Grilla (radio 0.35°, zoom 4) | 9.9 – 95.5 % | 76 % |
| Timeseries (radio 1.0°, zoom 3) | 18.7 – 70.3 % | ~56 % |

Con cualquier umbral absoluto dispara siempre o nunca. La causa está en el propio docstring de la función: es *color-based*, no un retrieval radiativo. Filtra cirros y nieve, pero lo que queda sigue siendo superficie y nubes. Coherente con que **nadie en el repo la compare nunca contra un umbral** — sólo se grafica como serie, donde importa la variación, no el valor.

**3. El disparador elegido es hot spot FDCF, con botón siempre disponible.** Los hot spots ya están en memoria (el panel de Ash RGB los baja, caché 300 s), son validados externamente por NOAA, y `CLAUDE.md` los privilegia explícitamente.

Su límite, que hay que decir en pantalla: **detectan anomalía térmica en el cráter, no pluma**. Una erupción freática —Villarrica, Chillán— puede dar columna de ceniza importante sin hot spot. Por eso el botón queda siempre disponible: el caso freático lo dispara el ojo del operador, que es coherente con la filosofía del proyecto ("el dashboard muestra el dato, la interpretación queda al experto").

## Por qué es una TIRA y no un 5º panel

La grilla se afinó midiendo: en fullscreen son 4 paneles en una fila, 462×505 px, y los cuatro entran en 1080p con 26 px de margen. Un 5º elemento rompe eso — deja un huérfano en una segunda fila y devuelve el problema del scroll que acabamos de arreglar.

Y no es del mismo tipo: los 4 paneles son **mapas**; esto es un **número con su incertidumbre**. Va debajo, a lo ancho, como la fila de KPIs que ya usa la página VOLCAT.

## Honestidades que la tira TIENE que mostrar

- **Sólo mide ceniza IR-opaca.** Validado contra la pluma de Chillán del 27-jun: a una pluma de gas/SO₂ el retrieval le da un tope *bajo el cráter*. Un resultado por debajo de la cota del volcán significa **"no encontró ceniza IR-opaca"**, no "la pluma es baja". Sin ese aviso, un operador lee un número físicamente imposible como si fuera una medición.
- **Sin firma de ceniza es el estado esperado**, igual que en el panel VOLCAT.
- **El costo, antes de gastarlo**: el botón dice que baja ~78 MB y tarda ~90 s.

---

## File Structure

| Archivo | Responsabilidad | Acción |
|---|---|---|
| `dashboard/views/modo_guardia_volcan.py` | La tira: fragment sin `run_every`, disparo, presentación | **Modificar** |
| `dashboard/views/live_viewer.py` | Vista Operacional activa la tira | **Modificar** |
| `tests/test_altura_en_grilla.py` | Invariantes del disparo, el costo y las honestidades | **Crear** |
| `docs/FICHA_SDA_GOES.md` | Ficha SDA: la vista pasa a mostrar una magnitud calculada | **Modificar** |
| `CLAUDE.md` | El patrón del disparo por condición | **Modificar** |

---

## Task 1: La tira de altura

**Files:**
- Modify: `dashboard/views/modo_guardia_volcan.py`
- Test: `tests/test_altura_en_grilla.py`

### Step 1: Tests que fallan

```python
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

VIEW = (Path(__file__).parent.parent / "dashboard" / "views"
        / "modo_guardia_volcan.py")


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
    cuerpo = _func_source(VIEW, "_tira_altura_propia")
    assert re.search(r"78\s*MB|~?90\s*s", cuerpo)


def test_la_tira_dice_que_solo_mide_ceniza_ir_opaca():
    """Validado contra la pluma de Chillan del 27-jun: a una pluma de gas/SO2
    el retrieval le da un tope BAJO el crater. Un numero por debajo de la cota
    significa 'no encontro ceniza IR-opaca', no 'la pluma es baja'. Sin ese
    aviso, un operador lee un imposible fisico como una medicion."""
    cuerpo = _func_source(VIEW, "_tira_altura_propia")
    assert re.search(r"IR-opaca|IR opaca", cuerpo)
    assert re.search(r"gas|SO2|SO₂", cuerpo)


def test_la_tira_no_la_usa_la_pared_de_la_sala():
    """El Modo Sala se proyecta sin nadie mirando. Una descarga de 78 MB
    disparada sola ahi no la ve venir nadie, y el slot no tiene quien aprete el
    boton."""
    from dashboard.views.modo_guardia_volcan import volcan_grid

    sig = inspect.signature(volcan_grid)
    assert sig.parameters["mostrar_altura"].default is False, (
        "por defecto apagada: la enciende quien la puede atender")
```

### Step 2: Correr y ver fallar

```bash
python -m pytest tests/test_altura_en_grilla.py -v
```

### Step 3: Implementar

En `dashboard/views/modo_guardia_volcan.py`, después de `_panel_volcat`:

```python
# Costo REAL de una escena, medido contra S3 con cache frio (ago-2026):
# C11 25.8 MB / 35.4 s + C14 25.9 MB / 25.8 s + C15 25.6 MB / 28.7 s, mas el
# perfil GFS y el granulo ACHA. Va en pantalla antes de gastarlo.
ALTURA_COSTO_TXT = "~78 MB y ~90 s"


@st.fragment
def _tira_altura_propia(volcan_name: str, radius_deg: float = RADIUS_DEG):
    """Altura de tope calculada por nosotros, debajo de la grilla.

    Es una TIRA y no un 5º panel: los otros cuatro son mapas y esto es un
    numero con su incertidumbre. Ademas la grilla se afino midiendo (4 en una
    fila que entran justo en 1080p); un quinto elemento devuelve el scroll que
    acabamos de sacar.

    Fragment SIN `run_every`: el fragment existe para que apretar el boton no
    re-renderice los cuatro mapas, no para auto-refrescar. El retrieval cuesta
    ALTURA_COSTO_TXT por escena.

    DISPARO: automatico si hay hot spot NOAA FDCF en el encuadre (ya esta en
    memoria, cache 300 s, lo valida NOAA); boton explicito el resto del tiempo.
    El hot spot detecta anomalia termica en el crater, NO pluma: una erupcion
    freatica puede dar columna de ceniza sin ninguno, y ese caso lo dispara el
    operador.
    """
    v = get_volcano(volcan_name)
    if v is None:
        return

    bounds = {
        "lat_min": v.lat - radius_deg, "lat_max": v.lat + radius_deg,
        "lon_min": v.lon - radius_deg, "lon_max": v.lon + radius_deg,
    }
    hotspots, _ = _hotspots_volcan(bounds["lat_min"], bounds["lat_max"],
                                   bounds["lon_min"], bounds["lon_max"])

    st.markdown(
        "<div style='margin-top:0.6rem; padding-top:0.5rem; "
        "border-top:1px solid #223; font-size:0.85rem; color:#9aaabb;'>"
        "<b style='color:#e6edf3;'>Altura de tope · cálculo propio</b> "
        "<span style='font-size:0.75rem;'>independiente de SSEC — "
        "Wen-Rose + BT-matching + ACHA</span></div>",
        unsafe_allow_html=True,
    )

    key = f"altura_{volcan_name}_{radius_deg:.2f}"
    auto = bool(hotspots)
    if auto:
        st.caption(
            f"▶ Disparado automáticamente: {len(hotspots)} hot spot(s) NOAA "
            f"FDCF en el encuadre. El hot spot marca anomalía térmica en el "
            f"cráter, no pluma — el retrieval dirá si hay ceniza que medir.")
    correr = auto or st.button(
        "Calcular altura de tope",
        key=f"btn_{key}",
        help=f"Baja las bandas L1b del scan y resuelve el tope. Cuesta "
             f"{ALTURA_COSTO_TXT}. Sin hot spot no se dispara solo: una "
             f"erupción freática puede dar columna sin anomalía térmica.")

    if not correr:
        st.caption(
            f"Sin hot spot en el encuadre. Si ves columna en los mapas de "
            f"arriba, apretá el botón — el cálculo cuesta {ALTURA_COSTO_TXT}.")
        return

    from dashboard.views.volcat_viewer import _acha_plume_cached, _wenrose_cached
    bucket = (datetime.now(timezone.utc).strftime("%Y%m%d%H")
              + f"{datetime.now(timezone.utc).minute // 10}")
    with st.spinner(f"Bajando bandas L1b + perfil GFS ({ALTURA_COSTO_TXT})..."):
        wr = _wenrose_cached(v.name, radius_deg, bucket)
        acha = _acha_plume_cached(v.name, radius_deg, bucket)

    _render_altura(v, wr, acha)


def _render_altura(v, wr: dict | None, acha: dict | None):
    """Presenta el resultado de los 3 métodos con sus honestidades.

    La honestidad que NO se puede omitir: estos retrievals sólo miden ceniza
    **IR-opaca**. A una pluma de gas/SO₂ le dan un tope por debajo del cráter
    (validado contra Chillán, 27-jun). Un número bajo la cota del volcán
    significa "no encontró ceniza IR-opaca", no "la pluma es baja".
    """
    wr_ok = bool(wr) and wr.get("status") == "ok"
    acha_ok = bool(acha) and acha.get("status") == "ok"

    if not (wr_ok or acha_ok):
        st.info(
            "Sin firma de ceniza IR-opaca en el encuadre → no hay tope que "
            "reportar. **Es el estado esperado sin pluma activa.** Ojo: una "
            "pluma de gas/SO₂ tampoco da tope por este camino; para eso mirá "
            "el indicador SO₂ de la grilla.")
        return

    cima_km = (v.elevation or 0) / 1000.0
    cols = st.columns(4)
    with cols[0]:
        kpi_card(f"{wr['top_km']:.1f} km" if wr_ok else "—",
                 "Wen-Rose · corregido")
    with cols[1]:
        bt = wr.get("top_bt_matching_km") if wr_ok else None
        kpi_card(f"{bt:.1f} km" if bt is not None else "—",
                 "BT-matching · cota")
    with cols[2]:
        kpi_card(f"{acha['top_km']:.1f} km" if acha_ok else "—",
                 "ACHA NOAA · p95")
    with cols[3]:
        kpi_card(f"{cima_km:.1f} km", f"Cima de {v.name}")

    topes = [r["top_km"] for r, ok in ((wr, wr_ok), (acha, acha_ok))
             if ok and r.get("top_km") is not None]
    if topes and max(topes) < cima_km:
        st.warning(
            f"Todos los topes quedan **bajo la cima** ({cima_km:.1f} km). Eso "
            "NO significa que la pluma sea baja: significa que el retrieval no "
            "encontró ceniza IR-opaca. Es lo típico de una pluma de gas/SO₂ "
            "(validado contra Chillán, 27-jun-2026).")
```

### Step 4: Verificar

```bash
python -m pytest tests/test_altura_en_grilla.py -v
```

## Task 2: Enchufarla en `volcan_grid` y en Vista Operacional

`volcan_grid` recibe `mostrar_altura: bool = False` y llama a `_tira_altura_propia(volcan_name, radius_deg)` después de la grilla y antes del footer. **Default `False`**: la enciende quien la puede atender.

- **Vista Operacional** (`live_viewer.py`, tab Volcán): `mostrar_altura=True`.
- **Modo Guardia** sub-tab Volcán: `mostrar_altura=True`.
- **Slot `tv=volcan` del Modo Sala**: **NO**. Se proyecta sin nadie mirando; una descarga de 78 MB disparada sola ahí no la ve venir nadie, y no hay quien apriete el botón.

## Task 3: Ficha SDA y documentación

La vista pasa a mostrar una **magnitud física calculada** (altura de tope), así que aplica la convención de `GUIA_MAESTRA_TRANSPARENCIA_ALGORITMICA.md`: cabecera FICHA SDA en el código nuevo y `docs/FICHA_SDA_GOES.md` al día **en el mismo commit**.

En `CLAUDE.md`, el patrón: retrieval caro → disparo por condición barata y validada externamente, nunca por poll ni por una métrica de color.
