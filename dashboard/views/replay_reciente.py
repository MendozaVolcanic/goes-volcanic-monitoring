"""Replay por fecha: cualquier volcan, cualquier dia que RAMMB conserve.

Para que sirve: revisar despues lo que mostro GOES-19 sobre un volcan en un
dia y una ventana horaria elegidos (por ejemplo, el SO2 de Lastarria del
14-11-2026), recorriendo los scans de a uno.

Como lista los scans (nov-2026): pide a RAMMB `<fecha>_by_hour.json` del dia
elegido, NO "los ultimos N". `latest_times.json` corta en 100 scans (unas
16 h), asi que la version anterior, que pedia 200 y prometia 28 dias, en
realidad cubria menos de un dia.

Cuanto conserva RAMMB (medido el 15-11-2026 para jma_so2, eumetsat_ash y
geocolor): un tramo continuo reciente (desde 01-09-2026, 76 dias) y, antes,
dias sueltos hasta jul-2025, algunos de los cuales ya no tienen imagenes
aunque sigan en la lista. La vista calcula ese limite en cada visita desde
`available_dates.json` y lo dice en pantalla; un dia que no esta se informa
como tal y nunca se reemplaza por otro.

No decide nada: muestra la imagen RAMMB del scan elegido. La lectura (hay
pluma, es ceniza, es SO2) queda al geologo de turno.
"""

import logging
from datetime import date, datetime, timedelta, timezone

import streamlit as st

try:
    from dashboard.style import header
    from dashboard.utils import CHILE_TZ, parse_rammb_ts, utc_to_chile
    from src.fetch.rammb_slider import (
        fetch_frame_robust, get_latest_timestamps, ZOOM_VOLCAN, ZOOM_ZONE,
    )
    from src.volcanos import CATALOG, get_volcano
    # Listado por fecha (nov-2026). `get_latest_timestamps` de arriba ya no
    # se usa aca: queda importado solo para no chocar con el PR 34, que
    # reescribe esa misma linea; se quita cuando ambos esten en main.
    from src.fetch.historic_rammb import (
        ESTADO_NO_CONSERVADO, ESTADO_PARCIAL, ESTADO_SIN_RESPUESTA,
        archive_span, fetch_available_dates, list_local_day,
        local_window_utc, tile_available,
    )
except Exception:
    # Streamlit Cloud hot-reload race condition: retry import dentro de funciones.
    # Si esto se ejecuta, hay un bug — log y reraise para que Streamlit muestre el error.
    import logging as _logging
    _logging.exception("Cross-package import fallo top-level — gotcha Streamlit Cloud")
    raise

logger = logging.getLogger(__name__)

# Sugerencias, no la lista: volcanes con actividad frecuente donde casi
# siempre hay algo que ver. Van primero en el selector; el resto del catalogo
# viene despues.
ACTIVE_VOLCANOES = [
    {"name": "Sangay (Ecuador)", "rationale": "Actividad casi continua. Hot spots diarios."},
    {"name": "Reventador (Ecuador)", "rationale": "Explosiones diarias. Pluma frecuente."},
    {"name": "Sabancaya (Perú)", "rationale": "1-3 explosiones/día documentadas."},
    {"name": "Villarrica", "rationale": "Lago de lava activo. Hot spots térmicos."},
    {"name": "Lascar", "rationale": "Hot spots térmicos esporádicos."},
    {"name": "Copahue", "rationale": "Emisión sostenida de SO2."},
]

PRODUCTS = {
    "eumetsat_ash": "Ash RGB",
    "geocolor": "GeoColor",
    "jma_so2": "SO2 RGB",
}

# Canonical en src/config (REPLAY_RADIUS_DEG). Fallback hardcoded por
# si Streamlit Cloud falla el import durante hot-reload (gotcha CLAUDE.md).
try:
    from src.config import REPLAY_RADIUS_DEG as RADIUS_DEG
except Exception:
    RADIUS_DEG = 0.4  # ver src/config.py

# Radios ofrecidos (grados). 0.4 es el encuadre historico de la vista; 3
# grados alcanza para seguir una pluma larga.
RADIOS_DEG = [0.25, 0.4, 0.75, 1.0, 1.5, 2.0, 3.0]


def volcan_options() -> list[tuple[str, str]]:
    """(nombre, rotulo) para el selector: sugeridos primero, luego el resto
    del catalogo en su orden. Todos los volcanes del catalogo estan."""
    nombres = {v.name for v in CATALOG}
    out = [(a["name"], f"★ {a['name']}: {a['rationale']}")
           for a in ACTIVE_VOLCANOES if a["name"] in nombres]
    vistos = {n for n, _ in out}
    out += [(v.name, v.name) for v in CATALOG if v.name not in vistos]
    return out


# ── Datos (cache) ────────────────────────────────────────────────────
# Lo que se lista de un dia pasado no cambia; el dia de hoy si (entra un scan
# cada 10 min), por eso el TTL es corto igual.

@st.cache_data(ttl=3600, show_spinner=False)
def _fechas_listadas(product: str):
    return fetch_available_dates(product)


@st.cache_data(ttl=300, show_spinner=False)
def _scans_del_dia(product: str, dia: date, h_ini: int, h_fin: int):
    return list_local_day(product, dia, h_ini, h_fin, CHILE_TZ)


@st.cache_data(ttl=3600, show_spinner=False)
def _hay_imagenes(product: str, ts: str, bounds_key: tuple):
    lat_min, lat_max, lon_min, lon_max = bounds_key
    return tile_available(product, ts, {"lat_min": lat_min, "lat_max": lat_max,
                                        "lon_min": lon_min, "lon_max": lon_max})


def _rotulo_ts(ts: str) -> str:
    """'14-nov 09:50 Chile · 12:50 UTC' (la hora de Chile manda: es la del
    dia elegido)."""
    dt = parse_rammb_ts(ts)
    ch = utc_to_chile(dt)
    return f"{ch:%d-%m %H:%M} Chile · {dt:%H:%M} UTC"


def _texto_archivo(span: dict | None) -> str:
    """Limite real del archivo RAMMB, en palabras."""
    if span is None:
        return ("No se pudo leer la lista de días de RAMMB: no se sabe hasta "
                "dónde llega el archivo. Igual puedes pedir un día.")
    txt = (f"RAMMB conserva **continuo desde el "
           f"{span['continuo_desde']:%d-%m-%Y}** "
           f"({span['dias_continuos']} días, hasta el "
           f"{span['continuo_hasta']:%d-%m-%Y}).")
    if span["sueltos"]:
        tramos = ", ".join(
            f"{a:%d-%m-%Y}" if a == b else f"{a:%d-%m-%Y} a {b:%d-%m-%Y}"
            for a, b in span["sueltos"])
        txt += (f" Antes, solo días sueltos ({tramos}); algunos siguen en la "
                f"lista pero ya no tienen imágenes.")
    return txt


def _mover(key: str, paso: int, n: int):
    """Callback de ◀ ▶: corre el cuadro elegido sin salir de la ventana."""
    st.session_state[key] = min(max(st.session_state.get(key, 0) + paso, 0),
                                n - 1)


def render():
    from dashboard.manuals import render_manual
    render_manual("replay")
    header(
        "🔁 Replay por fecha: actividad real GOES-19",
        "Cualquier volcán del catálogo, el día y la ventana horaria que elijas, "
        "dentro de lo que RAMMB conserva",
    )

    # ── Selectores ──
    opciones = volcan_options()
    rotulos = dict(opciones)
    c1, c2, c3 = st.columns([2.2, 1.2, 1.2])
    with c1:
        volcan_name = st.selectbox(
            "Volcán", [n for n, _ in opciones],
            format_func=lambda n: rotulos[n],
            index=0, key="replay_volcan_nombre",
            help="★ = sugerencias con actividad frecuente. Más abajo está "
                 "todo el catálogo.",
        )
    with c2:
        product = st.selectbox(
            "Producto", list(PRODUCTS.keys()),
            format_func=lambda k: PRODUCTS[k],
            index=0, key="replay_product",
        )
    with c3:
        radio = st.select_slider(
            "Radio (grados)", options=RADIOS_DEG, value=RADIUS_DEG,
            format_func=lambda r: f"{r:g}° (~{r * 111:.0f} km)",
            key="replay_radio",
        )

    hoy_chile = utc_to_chile(datetime.now(timezone.utc)).date()
    fechas = _fechas_listadas(product)
    span = archive_span(fechas) if fechas else None
    # El calendario parte en el dia listado mas viejo; dias del medio que no
    # esten se avisan al elegirlos. Sin lista, se deja un año hacia atras.
    minimo = fechas[0] if fechas else hoy_chile - timedelta(days=365)

    d1, d2 = st.columns([1.2, 2.2])
    with d1:
        dia = st.date_input(
            "Día (hora de Chile)", value=hoy_chile,
            min_value=minimo, max_value=hoy_chile,
            format="DD-MM-YYYY", key="replay_dia",
        )
    with d2:
        h_ini, h_fin = st.slider(
            "Ventana horaria (hora de Chile)", 0, 24, (0, 24),
            format="%d:00", key="replay_ventana",
        )
    if h_fin <= h_ini:
        st.warning("La ventana horaria está vacía: elige un fin mayor que el inicio.")
        return

    ini_utc, fin_utc = local_window_utc(dia, h_ini, h_fin, CHILE_TZ)
    st.caption(
        f"{dia:%d-%m-%Y} de {h_ini:02d}:00 a {h_fin:02d}:00 hora de Chile = "
        f"{ini_utc:%d-%m %H:%M} a {fin_utc:%d-%m %H:%M} UTC. "
        + _texto_archivo(span)
    )

    v = get_volcano(volcan_name)
    if v is None:
        st.error(f"Volcán {volcan_name} no encontrado en catálogo.")
        return

    # ── Scans del dia ──
    with st.spinner("Pidiendo a RAMMB los scans de ese día…"):
        timestamps, estado = _scans_del_dia(product, dia, h_ini, h_fin)
    if estado == ESTADO_SIN_RESPUESTA:
        st.error("RAMMB no respondió: no se sabe si ese día existe. "
                 "Prueba de nuevo en unos segundos.")
        return
    if estado == ESTADO_NO_CONSERVADO:
        st.error(f"RAMMB no conserva el {dia:%d-%m-%Y} para "
                 f"{PRODUCTS[product]}. No se muestra otro día en su lugar. "
                 + _texto_archivo(span))
        return
    if not timestamps:
        st.warning(f"El {dia:%d-%m-%Y} está en RAMMB, pero no hay scans de "
                   f"{PRODUCTS[product]} entre las {h_ini:02d}:00 y las "
                   f"{h_fin:02d}:00 hora de Chile.")
        return
    if estado == ESTADO_PARCIAL:
        st.warning("Una parte del día no respondió en RAMMB: la lista puede "
                   "estar incompleta (faltan scans, no es que no los haya).")

    bounds = {
        "lat_min": v.lat - radio, "lat_max": v.lat + radio,
        "lon_min": v.lon - radio, "lon_max": v.lon + radio,
    }
    # La lista de RAMMB trae dias cuyas imagenes ya se borraron: se prueba un
    # tile del encuadre antes de ofrecer el slider (medido nov-2026).
    muestra = timestamps[len(timestamps) // 2]
    hay = _hay_imagenes(product, muestra, (bounds["lat_min"], bounds["lat_max"],
                                           bounds["lon_min"], bounds["lon_max"]))
    if hay is False:
        st.error(f"RAMMB todavía lista el {dia:%d-%m-%Y}, pero ya borró sus "
                 f"imágenes de {PRODUCTS[product]}: no hay nada que mostrar. "
                 + _texto_archivo(span))
        return
    if hay is None:
        st.warning("No se pudo confirmar que RAMMB tenga las imágenes de ese "
                   "día (sin respuesta). Se intenta igual.")

    st.success(f"📡 {len(timestamps)} scans de {PRODUCTS[product]} en la "
               f"ventana ({_rotulo_ts(timestamps[0])} a "
               f"{_rotulo_ts(timestamps[-1])}).")

    # ── Recorrer cuadros ──
    # La key lleva producto, dia y ventana: con otra lista de scans el indice
    # guardado no significa lo mismo y se vuelve al primer cuadro.
    n = len(timestamps)
    key = f"replay_idx_{product}_{dia:%Y%m%d}_{h_ini}_{h_fin}"
    if st.session_state.get(key, 0) >= n:
        st.session_state[key] = 0
    b1, s, b2 = st.columns([0.6, 8, 0.6])
    with b1:
        st.button("◀", key=f"{key}_ant", on_click=_mover, args=(key, -1, n),
                  help="Scan anterior", width="stretch")
    with b2:
        st.button("▶", key=f"{key}_sig", on_click=_mover, args=(key, 1, n),
                  help="Scan siguiente", width="stretch")
    with s:
        idx = st.select_slider(
            "Scan (mueve el slider o usa ◀ ▶)",
            options=list(range(n)),
            format_func=lambda i: _rotulo_ts(timestamps[i]),
            key=key, label_visibility="collapsed",
        )
    selected_ts = timestamps[idx]

    # Fallback con frames VECINOS del seleccionado, todos del mismo dia y
    # ventana: si un scan no carga, se muestra el adyacente y el rotulo dice
    # cual es. Nunca un frame de otro dia ni uno reciente. (fix audit jun 2026)
    _neighbors = timestamps[max(0, idx - 2):idx + 3]
    _candidates = [selected_ts] + [t for t in _neighbors if t != selected_ts]
    img, used_ts, used_zoom = fetch_frame_robust(
        product, _candidates, bounds,
        zoom_preferred=ZOOM_VOLCAN, zoom_fallback=ZOOM_ZONE,
    )

    regla = st.toggle(
        "📏 Regla", value=False, key="replay_regla",
        help="Arrastra sobre la imagen para medir en km desde donde "
             "quieras. No corrige el paralaje: una pluma alta aparece "
             "corrida hacia el sur (0,4 a 1,5 km por km de altura).",
    )

    # El rotulo lleva la hora del scan que de verdad se dibuja: si el pedido
    # no cargo y entro un vecino, se nombran los dos.
    labels = {idx: _rotulo_ts(used_ts or selected_ts)}
    if used_ts and used_ts != selected_ts:
        labels[idx] += f" (pedido {_rotulo_ts(selected_ts)})"

    label = f"{v.name} · {PRODUCTS[product]} · {labels[idx]}"
    if used_ts and used_ts != selected_ts:
        label += " ⚠ ts cercano"
    if used_zoom == ZOOM_ZONE:
        label += " ⚠ zoom 3"

    from dashboard.map_helpers import render_compact_legend
    render_compact_legend(product, symbols=("volcano",))
    # Mismo panel que la grilla de volcan (Vista Operacional / Modo Guardia):
    # en km alrededor del crater, con barra de escala. Lazy import (gotcha
    # Streamlit Cloud, ver CLAUDE.md).
    from dashboard.views.modo_guardia_volcan import _render_product
    fig = _render_product(img, bounds, label, v.lat, v.lon, v.name,
                          height=720, regla=regla)
    st.plotly_chart(fig, width="stretch",
                    config={"displayModeBar": regla, "displaylogo": False})
    if img is None:
        st.warning("RAMMB no entregó imagen para este scan ni para los "
                   "vecinos. Sin imagen no se puede decir nada del volcán.")

    st.caption(
        "💡 Con ◀ ▶ recorres el día de a un scan (10 min). Para hot spots, "
        "altura VOLCAT o un loop descargable de ese mismo momento, abre "
        "Modo Evento, VOLCAT o Loops."
    )

    with st.expander("📚 Calbuco 2015: caso histórico (sin datos disponibles)"):
        st.markdown(
            "Calbuco 22-Apr-2015 21:04 UTC sigue siendo el evento canónico "
            "para validar **Wen-Rose 1994** (~21 km confirmado por radiosonda). "
            "Pero como GOES-13 archive no está en RAMMB, no podemos hacer "
            "replay con los productos actuales del dashboard.\n\n"
            "**Para usarlo en el futuro** necesitamos:\n"
            "- Backfill desde `s3://noaa-goes13` (5 bandas IR, adaptar la receta Ash RGB)\n"
            "- O bundle de PNGs públicos de archivo en `data/historic/calbuco_2015/`\n\n"
            "Sesión dedicada futura, ~500 LOC."
        )
