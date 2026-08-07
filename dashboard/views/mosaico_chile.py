"""Mosaico Modo Guardia: 5 volcanes prioritarios x 3 productos.

FILOSOFIA: barrer de un golpe de vista los volcanes que el turno mira todos
los dias, y hacerlo con los TRES RGB a la vez — Ash detecta ceniza, SO2
detecta el gas y GeoColor da el contexto visible. Una fila por volcan, una
columna por producto. Sin numeros, sin alertas: el experto ve los 15 cuadros
y decide si algo merece zoom.

Por que 5 y no 8 (pedido OVDAS, ago-2026): con 3 productos, 8 filas no entran
en pantalla y cada panel queda demasiado chico para distinguir una pluma. Los
5 estan en config.MOSAICO_VOLCANOES; para cualquier otro volcan del catalogo
esta el sub-tab "Volcan (3 productos)".

Auto-refresh 60s. Cada celda usa el ultimo scan de SU producto.
"""

import logging
from datetime import datetime, timezone

import numpy as np
import plotly.graph_objects as go
import streamlit as st

try:
    from dashboard.style import volcano_marker
    from dashboard.utils import fmt_chile, parse_rammb_ts
    from src.fetch.rammb_slider import (
        fetch_frame_robust, get_latest_timestamps, ZOOM_VOLCAN, ZOOM_ZONE,
    )
    from dashboard.map_helpers import RGB_PRODUCTS
    from src.volcanos import get_volcano
except Exception:
    # Streamlit Cloud hot-reload race condition: retry import dentro de funciones.
    # Si esto se ejecuta, hay un bug — log y reraise para que Streamlit muestre el error.
    import logging as _logging
    _logging.exception("Cross-package import fallo top-level — gotcha Streamlit Cloud")
    raise

logger = logging.getLogger(__name__)

REFRESH_SECONDS = 60
ROTATION_SECONDS = 10
# Radio del bbox por volcan en el mosaico. Canonical en src/config
# (MOSAICO_RADIUS_DEG). Fallback hardcoded por si Streamlit Cloud
# falla el import cross-package durante hot-reload (gotcha CLAUDE.md).
try:
    from src.config import MOSAICO_RADIUS_DEG as RADIUS_DEG
except Exception:
    RADIUS_DEG = 0.5  # ver src/config.py para canonical
# Los 5 volcanes del mosaico. Canonical en src/config (MOSAICO_VOLCANOES).
try:
    from src.config import MOSAICO_VOLCANOES
except Exception:
    MOSAICO_VOLCANOES = ["Nevados de Chillan", "Villarrica", "Calbuco",
                         "Llaima", "Puyehue-Cordon Caulle"]
# Orden de rotación del Modo Sala (arranca en GeoColor, el más legible de un
# vistazo). Los labels y recetas salen de map_helpers.RGB_PRODUCTS.
PRODUCT_LIST_TV = ["geocolor", "eumetsat_ash", "jma_so2"]


@st.cache_data(ttl=30, show_spinner=False)
def _recent_timestamps(product: str, n: int = 5) -> list[str]:
    """Ultimos N timestamps. Cache 30s."""
    return get_latest_timestamps(product, n=n)


def _volcano_frame_with_fallback(product: str, timestamps: list[str],
                                  lat: float, lon: float
                                  ) -> tuple[np.ndarray | None, str | None, int]:
    """Fallback de ts + zoom: zoom=4 -> zoom=3 si zoom=4 falla.

    RAMMB intermitentemente no sirve algunos productos en zoom=4.
    Devuelve (img, ts_usado, zoom_usado). zoom=0 si todo fallo.

    Bbox asimetrico (lon expandido por 1/cos_lat) para que la imagen
    descargada cubra una region cuadrada en km — coincide con el plot.
    """
    cos_lat = max(0.1, float(np.cos(np.radians(lat))))
    half_lon = RADIUS_DEG / cos_lat
    bounds = {
        "lat_min": lat - RADIUS_DEG, "lat_max": lat + RADIUS_DEG,
        "lon_min": lon - half_lon, "lon_max": lon + half_lon,
    }
    return fetch_frame_robust(
        product, timestamps, bounds,
        zoom_preferred=ZOOM_VOLCAN, zoom_fallback=ZOOM_ZONE,
    )


def _array_to_data_url(arr):
    # Lazy import (gotcha Streamlit Cloud — ver CLAUDE.md).
    from dashboard.map_helpers import array_to_data_url
    return array_to_data_url(arr)



RING_RADII_KM = [5, 10, 25, 50]


def _circle_points(lat0: float, lon0: float, radius_km: float, n: int = 48):
    theta = np.linspace(0, 2 * np.pi, n)
    dlat = (radius_km / 111.0) * np.cos(theta)
    dlon = (radius_km / (111.0 * float(np.cos(np.radians(lat0))))) * np.sin(theta)
    return (lat0 + dlat).tolist(), (lon0 + dlon).tolist()


def _render_mini(img: np.ndarray | None, lat: float, lon: float, name: str,
                 height: int = 420, show_rings: bool = False,
                 target_width_px: int | None = None,
                 zoom_used: int | None = None,
                 hires_render: str | None = None,
                 hires_sun_alt: float | None = None):
    """Mini-plot cuadrado con bbox compensado por latitud.

    `height` se usa solo si `target_width_px=None`. Si se pasa width,
    el height se calcula como `width * cos_lat` para que el plot llene
    el container sin barras negras arriba/abajo (porque scaleanchor
    requiere proporcion exacta entre x e y en pantalla).
    """
    fig = go.Figure()
    cos_lat = max(0.1, float(np.cos(np.radians(lat))))
    # Si nos pasaron target_width_px, derivamos height para que el plot
    # llene el container sin espacio negro. Usamos un cos_lat MEDIANO
    # (no el del volcan especifico) porque sino las miniaturas de
    # diferente latitud quedan con altura distinta y desalinean el grid.
    # 0.78 = mediana de los 8 priority volcanos (~lat -38°).
    # Lascar (lat -23, cos=0.92) tendra pequena banda lateral pero el
    # grid queda alineado fila a fila.
    if target_width_px is not None:
        MEDIAN_COS_LAT_PRIORITY = 0.78
        height = max(200, int(target_width_px * MEDIAN_COS_LAT_PRIORITY))
    # span en km equivalente: RADIUS_DEG * 111 km. Lon en grados se expande
    # por 1/cos_lat para preservar el mismo span en km horizontal.
    half_lat = RADIUS_DEG
    half_lon = RADIUS_DEG / cos_lat
    bounds = {
        "lat_min": lat - half_lat, "lat_max": lat + half_lat,
        "lon_min": lon - half_lon, "lon_max": lon + half_lon,
    }
    if img is not None:
        fig.add_layout_image(
            source=_array_to_data_url(img),
            xref="x", yref="y",
            x=bounds["lon_min"], y=bounds["lat_max"],
            sizex=2 * half_lon, sizey=2 * half_lat,
            sizing="stretch", layer="below",
        )
    # Anillos de distancia (debajo del marcador) + label de km
    if show_rings:
        for r_km in RING_RADII_KM:
            lats, lons = _circle_points(lat, lon, r_km)
            fig.add_trace(go.Scatter(
                x=lons, y=lats, mode="lines",
                line=dict(color="rgba(255,255,255,0.35)", width=0.8, dash="dot"),
                hoverinfo="skip", showlegend=False,
            ))
            # Label "{r_km} km" justo arriba del cruce norte de cada anillo
            fig.add_annotation(
                x=lon, y=lat + (r_km / 111.0),
                text=f"{r_km}", showarrow=False,
                font=dict(size=8, color="rgba(255,255,255,0.75)"),
                bgcolor="rgba(0,0,0,0.55)", borderpad=1,
            )
    fig.add_trace(go.Scatter(
        x=[lon], y=[lat], mode="markers",
        marker=volcano_marker("zone"),
        hovertemplate=f"<b>{name}</b><extra></extra>",
        showlegend=False,
    ))
    fig.update_xaxes(range=[bounds["lon_min"], bounds["lon_max"]],
                     showgrid=False, visible=False)
    fig.update_yaxes(range=[bounds["lat_min"], bounds["lat_max"]],
                     showgrid=False, visible=False,
                     scaleanchor="x", scaleratio=1.0 / cos_lat)
    # Nombre del volcan: annotation EN COORDENADAS DE DATOS (no paper).
    # Si fuera paper, scaleanchor empuja el text al espacio negro afuera
    # de la imagen. En coords de datos, queda siempre adentro del bbox
    # visible — esquina sup-izq de la imagen real.
    fig.add_annotation(
        x=bounds["lon_min"], y=bounds["lat_max"],
        xref="x", yref="y",
        text=f"<b>{name}</b>", showarrow=False,
        font=dict(size=12, color="#ffffff"),
        bgcolor="rgba(0,0,0,0.65)", borderpad=3,
        xanchor="left", yanchor="top",
        xshift=4, yshift=-4,
    )
    # Badge de zoom usado + tipo de render (esquina inferior derecha):
    #   -2 = hi-res mono 0.5 km/px (cyan), -1 = hi-res color 1 km/px (azul),
    #    4 = RAMMB max (verde),  3 = RAMMB fallback (naranja).
    # Para hi-res, distinguir explicitamente VIS vs IR — clave porque a sol
    # bajo el pipeline cae a IR pseudo-color y la imagen se ve sepia/amarillo
    # (confuso si el usuario espera color real).
    if zoom_used is not None and zoom_used != 0:
        if zoom_used == -2:
            badge_color = "#00ddff"
            badge_text = "HI-RES MONO · 0.5km/px (4×)"
            if hires_sun_alt is not None:
                badge_text += f" · ☀{hires_sun_alt:.0f}°"
        elif zoom_used == -1:
            # Render: visible_color (TrueColor), ir_pseudo (sol bajo -> IR), o None
            if hires_render == "ir_pseudo":
                badge_color = "#ffaa55"  # naranja: alerta visible no disponible
                badge_text = "HI-RES IR · 1km/px"
                if hires_sun_alt is not None:
                    badge_text += f" · ☀{hires_sun_alt:.0f}° (noche/twilight)"
            elif hires_render == "visible_color":
                badge_color = "#33aaff"
                badge_text = "HI-RES VIS · 1km/px"
                if hires_sun_alt is not None:
                    badge_text += f" · ☀{hires_sun_alt:.0f}°"
            else:
                badge_color = "#33aaff"
                badge_text = "HI-RES NOAA · 1km/px"
        elif zoom_used >= 4:
            badge_color = "#3fb950"
            badge_text = f"z={zoom_used} · 1.7km/px"
        else:
            badge_color = "#ff9933"
            kmpx = {3: "3.4", 2: "6.8"}.get(zoom_used, "?")
            badge_text = f"z={zoom_used} · {kmpx}km/px"
        fig.add_annotation(
            x=bounds["lon_max"], y=bounds["lat_min"],
            xref="x", yref="y",
            text=badge_text,
            showarrow=False,
            font=dict(size=9, color=badge_color),
            bgcolor="rgba(0,0,0,0.7)", borderpad=2,
            xanchor="right", yanchor="bottom",
            xshift=-3, yshift=3,
        )
    fig.update_layout(
        height=height, margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor="#0a0e14", plot_bgcolor="#0a0e14",
    )
    if img is None:
        fig.add_annotation(
            text="sin datos",
            xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False,
            font=dict(color="#556", size=11),
        )
    return fig


@st.cache_data(ttl=120, show_spinner=False)
def _hires_for_volcano_cached(volcano_name: str, mode: str = "color"):
    """Wrapper cacheado del fetch hi-res. Cache 2 min para no spamear."""
    from src.fetch.hires_cache import fetch_hires_for_volcano
    return fetch_hires_for_volcano(volcano_name, mode=mode)


@st.fragment(run_every=f"{REFRESH_SECONDS}s")
def _grid_fragment(use_hires: bool = False, hires_mode: str = "color"):
    """Grid 5 volcanes × 3 productos, auto-refresh cada 60s.

    Una FILA por volcán y una COLUMNA por producto (Ash / GeoColor / SO2),
    igual que el sub-tab "Volcán (3 productos)" pero para los 5 volcanes que
    el turno mira a diario. Antes eran 8 volcanes × 1 producto seleccionable:
    con 3 productos, 8 filas no entran en pantalla y cada panel queda
    demasiado chico para distinguir una pluma. (pedido OVDAS, ago-2026)
    """
    now = datetime.now(timezone.utc)
    # Timestamps por producto: cada RGB de RAMMB publica a su propio ritmo, así
    # que pedir uno solo y reusarlo forzaría fallbacks innecesarios.
    ts_by_prod = {pid: _recent_timestamps(pid, n=5) for pid, _l, _r in RGB_PRODUCTS}
    if not any(ts_by_prod.values()):
        st.error("RAMMB no respondió. Reintentá en unos segundos.")
        return

    ref_ts = ts_by_prod.get("eumetsat_ash") or next(
        (t for t in ts_by_prod.values() if t), [])
    try:
        scan_dt = parse_rammb_ts(ref_ts[0])
        age_min = int((now - scan_dt).total_seconds() / 60)
        scan_label = f"{scan_dt.strftime('%H:%M UTC')} (hace {age_min} min)"
    except Exception:
        scan_label = ref_ts[0] if ref_ts else "—"

    rings_str = " / ".join(str(r) for r in RING_RADII_KM)
    st.markdown(
        f"<div style='background:#0f1418; border-left:4px solid #ff6644; "
        f"padding:0.6rem 1rem; border-radius:4px; margin-bottom:0.8rem; "
        f"display:flex; justify-content:space-between; align-items:center;'>"
        f"<div style='color:#e0e0e0;'>{len(MOSAICO_VOLCANOES)} prioritarios "
        f"× 3 productos &middot; "
        f"<span style='color:#9aaabb; font-size:0.85rem;'>"
        f"⊙ anillos {rings_str} km desde el crater</span></div>"
        f"<div style='color:#9aaabb; font-size:0.85rem;'>Scan {scan_label} · "
        f"render {now.strftime('%H:%M:%S')} UTC</div></div>",
        unsafe_allow_html=True,
    )

    # Una leyenda por columna, alineada con el grid (mismo patrón que el
    # sub-tab "Volcán (3 productos)"). Los anillos van siempre en el mosaico;
    # hot spots no se dibujan acá.
    from dashboard.map_helpers import render_compact_legend
    _leg_cols = st.columns(3)
    for _c, (_pid, _lbl, _rec) in zip(_leg_cols, RGB_PRODUCTS):
        with _c:
            render_compact_legend(_pid, height_px=32,
                                  symbols=("volcano", "rings"))

    # ── Descarga PARALELA de las 15 celdas ───────────────────────────
    # En serie son 15 requests RAMMB encadenados (~20 s con cache fría); el
    # pool las resuelve en ~el tiempo de la más lenta. fetch_frame_robust es
    # thread-safe (mismo patrón que el grid de 4 zonas).
    from concurrent.futures import ThreadPoolExecutor

    fallback_ts = 0
    fallback_zoom = 0
    hires_used = 0
    hires_fallback = 0

    volcs = [(n, get_volcano(n)) for n in MOSAICO_VOLCANOES]
    volcs = [(n, v) for n, v in volcs if v is not None]
    jobs = [(n, v, pid) for n, v in volcs for pid, _l, _r in RGB_PRODUCTS]

    def _one(job):
        name, v, pid = job
        # Hi-res sólo aplica al panel GeoColor: el cache NOAA es color real /
        # IR, no tiene equivalente de las recetas Ash ni SO2.
        if use_hires and pid == "geocolor":
            arr, info = _hires_for_volcano_cached(name, mode=hires_mode)
            if arr is not None:
                return job, arr, None, (-2 if hires_mode == "mono_05km" else -1), info
        tss = ts_by_prod.get(pid) or []
        if not tss:
            return job, None, None, 0, None
        img, used_ts, used_zoom = _volcano_frame_with_fallback(
            pid, tss, v.lat, v.lon)
        return job, img, used_ts, used_zoom, None

    with ThreadPoolExecutor(max_workers=6) as ex:
        results = {(n, pid): (img, uts, uz, info)
                   for (n, _v, pid), img, uts, uz, info in ex.map(_one, jobs)}

    for name, v in volcs:
        cols = st.columns(3)
        for i, (pid, label, recipe) in enumerate(RGB_PRODUCTS):
            img, used_ts, used_zoom, hires_info = results.get(
                (name, pid), (None, None, 0, None))
            if hires_info is not None or used_zoom in (-1, -2):
                hires_used += 1
            elif use_hires and pid == "geocolor":
                hires_fallback += 1
            tss = ts_by_prod.get(pid) or []
            if used_ts and tss and used_ts != tss[0]:
                fallback_ts += 1
            if used_zoom == ZOOM_ZONE:
                fallback_zoom += 1
            with cols[i]:
                st.plotly_chart(
                    # La fila ya identifica al volcán: sólo la primera celda
                    # repite el nombre, las otras dos llevan el producto. Así
                    # un panel suelto nunca queda sin decir QUÉ es.
                    _render_mini(img, v.lat, v.lon,
                                 f"{name} · {label}" if i == 0 else label,
                                 # De este valor sale el ALTO (× cos lat); el
                                 # ANCHO lo pone el contenedor, así que pasarse
                                 # deja banda negra arriba y abajo. Se mantiene
                                 # el 380 histórico: el panel igual queda más
                                 # grande que antes porque son 3 columnas en
                                 # vez de 4.
                                 target_width_px=380, show_rings=True,
                                 zoom_used=used_zoom,
                                 hires_render=(hires_info or {}).get("render"),
                                 hires_sun_alt=(hires_info or {}).get("sun_alt")),
                    width='stretch',
                    config={"displayModeBar": False},
                    key=f"mosaico_{name}_{pid}",
                )
                st.markdown(
                    f"<div style='font-size:0.68rem; color:#556; "
                    f"margin-top:-0.6rem;'>{recipe}</div>",
                    unsafe_allow_html=True,
                )

    if use_hires:
        # Distinguir 3 casos al user: todo OK / parcial fallback / TODO fallback
        if hires_used == 0:
            # Caso especial mono_05km: el workflow del cron OOMs en runner
            # GH free porque banda 2 nativa (21696×21696) requiere ~7 GB RAM
            # solo para get_lat_lon. Por eso el cache mono esta SIEMPRE vacio
            # y siempre cae a RAMMB. El user no nota diferencia con RAMMB
            # normal — por eso un mensaje explicito.
            if hires_mode == "mono_05km":
                st.warning(
                    "⚠ **Hi-res mono (0.5 km/px) NO disponible actualmente** — el "
                    "workflow falla por OOM en runner GH free (banda 2 nativa "
                    "requiere ~7 GB RAM). Lo que ves es **RAMMB fallback**. "
                    "Para activar el modo mono real: correr `python scripts/build_hires_cache.py "
                    "--mode mono_05km` desde el localhost del observatorio (más RAM)."
                )
            else:
                st.warning(
                    f"⚠ **Hi-res color sin datos disponibles** "
                    f"({hires_fallback}/{len(MOSAICO_VOLCANOES)} paneles GeoColor "
                    "cayeron a RAMMB). El cache puede estar viejo o el cron tardó. "
                    "Re-trigger del workflow `hires_visible_cache.yml` en GitHub Actions."
                )
        else:
            st.caption(
                f"🔬 Hi-res NOAA activo (sólo GeoColor) · {hires_used}/"
                f"{len(MOSAICO_VOLCANOES)} paneles con hi-res, "
                f"{hires_fallback} con RAMMB")

    notes = []
    if fallback_ts:
        notes.append(f"{fallback_ts} con scan previo")
    if fallback_zoom:
        notes.append(f"{fallback_zoom} en zoom 3 (RAMMB no sirvió zoom 4)")
    if notes:
        st.caption("ℹ " + " · ".join(notes))


@st.fragment(run_every=f"{ROTATION_SECONDS}s")
def _grid_fragment_tv(session_key: str = "tv_mosaico_rot_idx"):
    """Modo TV puro: los 5 prioritarios en UNA fila, paneles grandes,
    rotando productos GeoColor -> Ash -> SO2 cada 10s, con anillos.

    En la sala se proyecta un producto a la vez y rota: por eso acá los 5
    entran en una sola fila (mas ancho por panel que el viejo grid 4x2) en vez
    de mostrar los 3 productos como hace el panel interactivo.

    Sin chrome (toolbar, banner status). Solo etiqueta minimal flotante.
    """
    if session_key not in st.session_state:
        st.session_state[session_key] = 0
    idx = st.session_state[session_key] % len(PRODUCT_LIST_TV)
    current = PRODUCT_LIST_TV[idx]
    next_idx = (idx + 1) % len(PRODUCT_LIST_TV)
    st.session_state[session_key] = next_idx

    timestamps = _recent_timestamps(current, n=5)
    scan_dt = parse_rammb_ts(timestamps[0]) if timestamps else None

    # Leyenda compacta interpretativa en el espacio negro superior.
    # Cambia con el producto rotante. Status badge a la derecha con scan + refresh.
    from dashboard.map_helpers import render_compact_legend, render_scan_status_badge
    render_compact_legend(
        current, tv=True, symbols=("volcano",),
        extra_left=(f"<span style='color:#ff6644; font-weight:700; "
                    f"margin-right:0.2rem;'>🔄 Mosaico "
                    f"{len(MOSAICO_VOLCANOES)} ·</span>"),
        extra_right=render_scan_status_badge(scan_dt, ROTATION_SECONDS),
    )

    if not timestamps:
        st.error("RAMMB no respondió.")
        return

    # Una fila con los 5, paneles grandes
    rows = [MOSAICO_VOLCANOES]
    for row_volcanos in rows:
        cols = st.columns(len(row_volcanos))
        for i, name in enumerate(row_volcanos):
            v = get_volcano(name)
            if v is None:
                continue
            img, _, used_zoom = _volcano_frame_with_fallback(
                current, timestamps, v.lat, v.lon,
            )
            with cols[i]:
                st.plotly_chart(
                    _render_mini(img, v.lat, v.lon, name,
                                 target_width_px=460, show_rings=True,
                                 zoom_used=used_zoom),
                    width='stretch',
                    config={"displayModeBar": False},
                )


def _live_panel():
    """Toolbar + grid con auto-refresh.

    Ya no hay selector de producto: el grid muestra los TRES a la vez (una
    columna cada uno), que es el punto de la vista.
    """
    cols_top = st.columns([3.5, 3])
    with cols_top[0]:
        hires_mode = st.radio(
            "Resolucion",
            ["RAMMB normal", "Hi-res color (1 km/px)",
             "Hi-res mono (0.5 km/px) ⚠"],
            index=0, key="mosaico_hires_mode", horizontal=True,
            help="RAMMB normal: tiles CIRA 1.7 km/px (siempre disponible).\n"
                 "Hi-res color: NOAA L1b TrueColor 1km/px diurno + IR nocturno.\n"
                 "Hi-res mono: NOAA L1b banda 2 sola 0.5 km/px (4x zoom real). "
                 "⚠ ACTUALMENTE NO DISPONIBLE en cloud (OOM workflow GH free) — "
                 "cae a RAMMB normal. Requiere localhost del observatorio.",
        )
    with cols_top[1]:
        if "mono" in hires_mode:
            st.caption("⚠ Mono 0.5km/px no disponible cloud — vas a ver RAMMB. "
                       "Requiere correr local desde el observatorio.")
        elif hires_mode == "Hi-res color (1 km/px)":
            st.caption("ℹ Color 1km/px = TrueColor diurno o IR nocturno · "
                       "1.7x mejor que RAMMB. Aplica sólo a la columna "
                       "GeoColor (Ash y SO2 no tienen equivalente hi-res).")

    use_hires = hires_mode != "RAMMB normal"
    hires_mode_arg = "mono_05km" if "mono" in hires_mode else "color"
    _grid_fragment(use_hires=use_hires, hires_mode=hires_mode_arg)
    st.markdown(
        "<div style='text-align:center; color:#445566; font-size:0.75rem; "
        "margin-top:0.8rem; padding-top:0.5rem; border-top:1px solid #223;'>"
        "<i>Sin metricas automaticas. Si algo llama la atencion en una "
        "celda, ir a 'Modo Guardia → Volcán (3 productos)' para ver ese "
        "volcán con anillos, viento y captura.</i></div>",
        unsafe_allow_html=True,
    )


def render():
    st.markdown(
        """
        <style>
          [data-testid="stHeader"] { background: rgba(0,0,0,0); height: 0; }
          .block-container { padding-top: 1rem !important; padding-bottom: 1rem !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        "<div style='display:flex; align-items:center; justify-content:space-between; "
        "padding-bottom:0.6rem; border-bottom:2px solid #223; margin-bottom:0.6rem;'>"
        "<div style='font-size:1.5rem; font-weight:800; color:#ff6644;'>"
        "🗺 MOSAICO CHILE</div>"
        "<div style='font-size:0.85rem; color:#7a8a9a;'>"
        "5 prioritarios × 3 productos · zoom volcan</div></div>",
        unsafe_allow_html=True,
    )
    _live_panel()
