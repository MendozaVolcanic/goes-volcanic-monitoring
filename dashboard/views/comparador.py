"""Comparador unificado: 3 modos en una sola vista.

Modos:
  1. Antes / Despues — mismo volcan, 2 timestamps. Detecta cambios temporales.
  2. 2 Volcanes — 2 volcanes, mismo timestamp. Compara estados simultaneos.
  3. Diff Temporal — mismo volcan, sustraccion |img(t2) - img(t1)|. Resalta
     cambios pixel a pixel (zonas brillantes = cambio fuerte).

Filosofia operacional: el experto compara dos imagenes mentalmente todo el
tiempo. Esta vista lo hace explicito y reproducible. Sin metricas
automaticas — el ojo del volcanologo decide.

Uso:
  - Antes/Despues: detectar plumas que aparecieron en las ultimas N horas.
  - 2 Volcanes: cross-check entre volcanes vecinos (¿hay nube comun? ¿algo
    afecta a ambos? ¿solo a uno?).
  - Diff Temporal: alertar visualmente sobre que pixeles cambiaron — util
    cuando los dos frames se ven similares pero hay cambio sutil.
"""

import logging
from datetime import datetime, timezone

import numpy as np
import plotly.graph_objects as go
import streamlit as st

from dashboard.utils import fmt_chile, parse_rammb_ts
from src.fetch.rammb_slider import (
    fetch_frame_for_bounds, fetch_frame_robust,
    get_latest_timestamps, ZOOM_VOLCAN, ZOOM_ZONE,
)
from src.volcanos import PRIORITY_VOLCANOES, get_volcano

logger = logging.getLogger(__name__)

RADIUS_DEG = 0.35  # ~38 km, mismo que Modo Guardia Volcan
N_TIMESTAMPS = 36  # ultimas 6h (cadencia 10 min)

PRODUCT_OPTIONS = {
    "eumetsat_ash": "Ash RGB",
    "geocolor": "GeoColor",
    "jma_so2": "SO2 RGB",
}


# ── Cache helpers ────────────────────────────────────────────────────

@st.cache_data(ttl=120, show_spinner=False)
def _list_timestamps(product: str, n: int = N_TIMESTAMPS) -> list[str]:
    """Lista los ultimos N timestamps disponibles. Cache 2 min."""
    return get_latest_timestamps(product, n=n)


def _frame_robust(product: str, ts_target: str, all_timestamps: list[str],
                  lat: float, lon: float
                  ) -> tuple[np.ndarray | None, str | None, int]:
    """Busca el frame para `ts_target`. Si falla, prueba ts adyacentes y zoom=3.

    El comparador requiere un timestamp especifico (no el mas reciente),
    pero queremos robustez: si el ts pedido no tiene tile, probamos
    ±2 timestamps cerca del pedido. Y zoom=3 si zoom=4 no carga.
    """
    # Construir lista priorizando el ts pedido, luego sus vecinos cronologicos
    if ts_target not in all_timestamps:
        ordered_ts = [ts_target] + all_timestamps
    else:
        idx = all_timestamps.index(ts_target)
        # ts pedido + vecinos: -1, +1, -2, +2
        nearby = [ts_target]
        for delta in (-1, 1, -2, 2):
            j = idx + delta
            if 0 <= j < len(all_timestamps):
                nearby.append(all_timestamps[j])
        ordered_ts = nearby

    bounds = {
        "lat_min": lat - RADIUS_DEG, "lat_max": lat + RADIUS_DEG,
        "lon_min": lon - RADIUS_DEG, "lon_max": lon + RADIUS_DEG,
    }
    return fetch_frame_robust(
        product, ordered_ts, bounds,
        zoom_preferred=ZOOM_VOLCAN, zoom_fallback=ZOOM_ZONE,
    )


# ── Helpers viz ──────────────────────────────────────────────────────

def _array_to_data_url(arr: np.ndarray) -> str:
    import base64
    import io
    from PIL import Image
    img = Image.fromarray(arr.astype(np.uint8))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def _plot_frame(img: np.ndarray | None, lat: float, lon: float,
                volcan_name: str, title: str, height: int = 580):
    fig = go.Figure()
    bounds_box = {
        "lat_min": lat - RADIUS_DEG, "lat_max": lat + RADIUS_DEG,
        "lon_min": lon - RADIUS_DEG, "lon_max": lon + RADIUS_DEG,
    }
    if img is not None:
        fig.add_layout_image(
            source=_array_to_data_url(img),
            xref="x", yref="y",
            x=bounds_box["lon_min"], y=bounds_box["lat_max"],
            sizex=2 * RADIUS_DEG, sizey=2 * RADIUS_DEG,
            sizing="stretch", layer="below",
        )
    fig.add_trace(go.Scatter(
        x=[lon], y=[lat], mode="markers",
        marker=dict(symbol="triangle-up", size=14, color="#00ffff",
                    line=dict(color="white", width=1.5)),
        hovertemplate=f"<b>{volcan_name}</b><extra></extra>",
        showlegend=False,
    ))
    cos_lat = max(0.1, float(np.cos(np.radians(lat))))
    fig.update_xaxes(range=[bounds_box["lon_min"], bounds_box["lon_max"]],
                     showgrid=False, visible=False)
    fig.update_yaxes(range=[bounds_box["lat_min"], bounds_box["lat_max"]],
                     showgrid=False, visible=False,
                     scaleanchor="x", scaleratio=1.0 / cos_lat)
    fig.update_layout(
        title=dict(text=title, font=dict(size=12, color="#e0e0e0"), x=0.02),
        height=height, margin=dict(l=0, r=0, t=28, b=0),
        paper_bgcolor="#0a0e14", plot_bgcolor="#0a0e14",
    )
    if img is None:
        fig.add_annotation(
            text="Sin imagen disponible",
            xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False,
            font=dict(color="#7a8a9a", size=14),
        )
    return fig


def _compute_diff(img1: np.ndarray, img2: np.ndarray) -> np.ndarray:
    """|img2 - img1| en cada canal, normalizado a uint8.

    Resalta zonas que cambiaron entre los dos frames. Pixeles que se
    mantuvieron iguales aparecen oscuros (cerca de cero); pixeles que
    cambiaron mucho aparecen brillantes (cerca de 255).

    Las imagenes deben tener mismo tamaño. Si difieren se redimensiona
    img1 a la forma de img2.
    """
    if img1.shape != img2.shape:
        from PIL import Image as PILImage
        h, w = img2.shape[:2]
        img1 = np.array(PILImage.fromarray(img1).resize((w, h)))
    a = img1.astype(np.int16)
    b = img2.astype(np.int16)
    diff = np.abs(b - a).astype(np.uint8)
    return diff


def _plot_diff(diff: np.ndarray, lat: float, lon: float, volcan_name: str,
               title: str, height: int = 700):
    """Plot del diff con realce — fondo oscuro, cambios brillantes."""
    # Realzar contraste: gamma + amplificacion
    enhanced = np.clip(diff.astype(np.float32) * 2.2, 0, 255).astype(np.uint8)
    return _plot_frame(enhanced, lat, lon, volcan_name, title, height=height)


# ── UI Helpers ───────────────────────────────────────────────────────

def _ts_format(ts: str) -> str:
    """20260425221000 -> '22:10 UTC (25-Apr)'."""
    try:
        dt = parse_rammb_ts(ts)
        return dt.strftime("%H:%M UTC (%d-%b)")
    except Exception:
        return ts


def _ts_age_label(ts: str, now: datetime) -> str:
    try:
        dt = parse_rammb_ts(ts)
        age_min = int((now - dt).total_seconds() / 60)
        if age_min < 60:
            return f"hace {age_min} min"
        h = age_min // 60
        m = age_min % 60
        return f"hace {h}h {m}min"
    except Exception:
        return "—"


# ── Modos ────────────────────────────────────────────────────────────

def _mode_antes_despues(now: datetime):
    """Mismo volcan, 2 timestamps lado a lado."""
    cols = st.columns([1.5, 1, 1, 1])
    with cols[0]:
        volcan_name = st.selectbox(
            "Volcán",
            options=PRIORITY_VOLCANOES,
            index=0, key="comp_ad_volcan",
        )
    with cols[1]:
        product = st.selectbox(
            "Producto",
            options=list(PRODUCT_OPTIONS.keys()),
            format_func=lambda k: PRODUCT_OPTIONS[k],
            index=0, key="comp_ad_prod",
        )
    timestamps = _list_timestamps(product)
    if len(timestamps) < 2:
        st.error("No hay suficientes timestamps disponibles.")
        return
    timestamps_chrono = list(reversed(timestamps))  # mas viejo primero
    labels_chrono = [_ts_format(t) for t in timestamps_chrono]
    with cols[2]:
        idx_a = st.selectbox(
            "ANTES",
            options=list(range(len(timestamps_chrono))),
            format_func=lambda i: labels_chrono[i],
            index=0, key="comp_ad_idx_a",
        )
    with cols[3]:
        idx_b = st.selectbox(
            "DESPUÉS",
            options=list(range(len(timestamps_chrono))),
            format_func=lambda i: labels_chrono[i],
            index=len(timestamps_chrono) - 1, key="comp_ad_idx_b",
        )

    v = get_volcano(volcan_name)
    if v is None:
        st.error("Volcán no encontrado.")
        return

    ts_a = timestamps_chrono[idx_a]
    ts_b = timestamps_chrono[idx_b]
    all_ts = timestamps  # original API order (most-recent first)
    img_a, used_ts_a, zoom_a = _frame_robust(product, ts_a, all_ts, v.lat, v.lon)
    img_b, used_ts_b, zoom_b = _frame_robust(product, ts_b, all_ts, v.lat, v.lon)

    def _flag(used_ts, target_ts, used_zoom):
        flags = []
        if used_ts and used_ts != target_ts:
            flags.append("ts cercano")
        if used_zoom == ZOOM_ZONE:
            flags.append("zoom 3")
        return " ⚠ " + ", ".join(flags) if flags else ""

    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(
            _plot_frame(img_a, v.lat, v.lon, v.name,
                        f"⏪ ANTES · {_ts_format(ts_a)} · {_ts_age_label(ts_a, now)}"
                        + _flag(used_ts_a, ts_a, zoom_a),
                        height=620),
            use_container_width=True,
            config={"displayModeBar": False},
        )
    with c2:
        st.plotly_chart(
            _plot_frame(img_b, v.lat, v.lon, v.name,
                        f"⏩ DESPUÉS · {_ts_format(ts_b)} · {_ts_age_label(ts_b, now)}"
                        + _flag(used_ts_b, ts_b, zoom_b),
                        height=620),
            use_container_width=True,
            config={"displayModeBar": False},
        )

    delta_min = 0
    try:
        delta_min = int((parse_rammb_ts(ts_b) - parse_rammb_ts(ts_a)).total_seconds() / 60)
    except Exception:
        pass
    st.caption(
        f"📌 {v.name} · {PRODUCT_OPTIONS[product]} · "
        f"intervalo {delta_min} min ({delta_min // 60}h {delta_min % 60}min) · "
        f"zoom volcán ~38 km radio."
    )


def _mode_dos_volcanes(now: datetime):
    """2 volcanes lado a lado, mismo timestamp."""
    cols = st.columns([1, 1, 1, 1])
    with cols[0]:
        v1 = st.selectbox(
            "Volcán 1", options=PRIORITY_VOLCANOES,
            index=0, key="comp_2v_v1",
        )
    with cols[1]:
        v2_options = [v for v in PRIORITY_VOLCANOES if v != v1]
        v2 = st.selectbox(
            "Volcán 2", options=v2_options,
            index=0, key="comp_2v_v2",
        )
    with cols[2]:
        product = st.selectbox(
            "Producto",
            options=list(PRODUCT_OPTIONS.keys()),
            format_func=lambda k: PRODUCT_OPTIONS[k],
            index=0, key="comp_2v_prod",
        )
    timestamps = _list_timestamps(product, n=24)
    if not timestamps:
        st.error("No hay timestamps disponibles.")
        return
    timestamps_chrono = list(reversed(timestamps))
    labels_chrono = [_ts_format(t) for t in timestamps_chrono]
    with cols[3]:
        idx = st.selectbox(
            "Timestamp",
            options=list(range(len(timestamps_chrono))),
            format_func=lambda i: labels_chrono[i],
            index=len(timestamps_chrono) - 1, key="comp_2v_idx",
        )

    ts = timestamps_chrono[idx]
    vo1 = get_volcano(v1)
    vo2 = get_volcano(v2)
    if vo1 is None or vo2 is None:
        st.error("Volcán no encontrado.")
        return

    all_ts = timestamps
    img1, _, _ = _frame_robust(product, ts, all_ts, vo1.lat, vo1.lon)
    img2, _, _ = _frame_robust(product, ts, all_ts, vo2.lat, vo2.lon)

    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(
            _plot_frame(img1, vo1.lat, vo1.lon, vo1.name,
                        f"🌋 {vo1.name} · {_ts_format(ts)}", height=620),
            use_container_width=True,
            config={"displayModeBar": False},
        )
    with c2:
        st.plotly_chart(
            _plot_frame(img2, vo2.lat, vo2.lon, vo2.name,
                        f"🌋 {vo2.name} · {_ts_format(ts)}", height=620),
            use_container_width=True,
            config={"displayModeBar": False},
        )

    dist_km = 111.0 * float(np.hypot(
        (vo1.lat - vo2.lat),
        (vo1.lon - vo2.lon) * float(np.cos(np.radians((vo1.lat + vo2.lat) / 2))),
    ))
    st.caption(
        f"📌 Comparación simultánea · {PRODUCT_OPTIONS[product]} · "
        f"separación {dist_km:.0f} km · "
        f"timestamp {_ts_format(ts)} ({_ts_age_label(ts, now)})."
    )


def _mode_diff_temporal(now: datetime):
    """Mismo volcan, sustraccion |img(t2) - img(t1)|."""
    cols = st.columns([1.4, 1, 1, 1])
    with cols[0]:
        volcan_name = st.selectbox(
            "Volcán", options=PRIORITY_VOLCANOES,
            index=0, key="comp_diff_volcan",
        )
    with cols[1]:
        product = st.selectbox(
            "Producto",
            options=list(PRODUCT_OPTIONS.keys()),
            format_func=lambda k: PRODUCT_OPTIONS[k],
            index=0, key="comp_diff_prod",
        )
    timestamps = _list_timestamps(product)
    if len(timestamps) < 2:
        st.error("No hay suficientes timestamps disponibles.")
        return
    timestamps_chrono = list(reversed(timestamps))
    labels_chrono = [_ts_format(t) for t in timestamps_chrono]
    with cols[2]:
        # Defaults: hace 6h vs ahora, comunes en operacion
        default_a = max(0, len(timestamps_chrono) - 36)
        idx_a = st.selectbox(
            "ANTES", options=list(range(len(timestamps_chrono))),
            format_func=lambda i: labels_chrono[i],
            index=default_a, key="comp_diff_idx_a",
        )
    with cols[3]:
        idx_b = st.selectbox(
            "AHORA", options=list(range(len(timestamps_chrono))),
            format_func=lambda i: labels_chrono[i],
            index=len(timestamps_chrono) - 1, key="comp_diff_idx_b",
        )

    v = get_volcano(volcan_name)
    if v is None:
        st.error("Volcán no encontrado.")
        return

    ts_a = timestamps_chrono[idx_a]
    ts_b = timestamps_chrono[idx_b]
    all_ts = timestamps
    img_a, _, _ = _frame_robust(product, ts_a, all_ts, v.lat, v.lon)
    img_b, _, _ = _frame_robust(product, ts_b, all_ts, v.lat, v.lon)

    if img_a is None or img_b is None:
        st.error("No se pudo bajar uno de los frames (ni en zoom 3 con ts vecinos). "
                 "Probá otro producto o timestamp.")
        return

    diff = _compute_diff(img_a, img_b)

    # 3 paneles: antes / despues / diff (diff ocupando mas espacio)
    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(
            _plot_frame(img_a, v.lat, v.lon, v.name,
                        f"⏪ ANTES · {_ts_format(ts_a)}", height=380),
            use_container_width=True,
            config={"displayModeBar": False},
        )
    with c2:
        st.plotly_chart(
            _plot_frame(img_b, v.lat, v.lon, v.name,
                        f"⏩ AHORA · {_ts_format(ts_b)}", height=380),
            use_container_width=True,
            config={"displayModeBar": False},
        )

    st.markdown(
        "<div style='background:#0f1418; border-left:4px solid #ff6644; "
        "padding:0.6rem 1rem; border-radius:4px; margin:0.5rem 0;'>"
        "<b style='color:#ff6644;'>🔥 DIFF TEMPORAL</b>"
        "<span style='color:#9aaabb; font-size:0.85rem; margin-left:0.6rem;'>"
        "|AHORA − ANTES| amplificado · zonas brillantes = cambio fuerte · "
        "zonas oscuras = sin cambio</span></div>",
        unsafe_allow_html=True,
    )

    delta_min = 0
    try:
        delta_min = int((parse_rammb_ts(ts_b) - parse_rammb_ts(ts_a)).total_seconds() / 60)
    except Exception:
        pass

    st.plotly_chart(
        _plot_diff(diff, v.lat, v.lon, v.name,
                   f"DIFF · {v.name} · Δt = {delta_min // 60}h {delta_min % 60}min "
                   f"({_ts_format(ts_a)} → {_ts_format(ts_b)})",
                   height=700),
        use_container_width=True,
        config={"displayModeBar": False},
    )

    st.caption(
        "ℹ La sustracción se hace en el espacio RGB del producto (no en BT raw). "
        "Cambios espectrales sutiles pueden no aparecer si el RGB ya estaba saturado. "
        "Para análisis cuantitativo usar BTD raw en Ash RGB Viewer."
    )


# ── Render principal ─────────────────────────────────────────────────

def render():
    st.markdown(
        """
        <style>
          [data-testid="stHeader"] { background: rgba(0,0,0,0); height: 0; }
          .block-container { padding-top: 0.6rem !important; padding-bottom: 1rem !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        "<div style='display:flex; align-items:center; justify-content:space-between; "
        "padding-bottom:0.4rem; border-bottom:2px solid #223; margin-bottom:0.6rem;'>"
        "<div style='font-size:1.5rem; font-weight:800; color:#ff6644;'>"
        "🔀 COMPARADOR</div>"
        "<div style='font-size:0.85rem; color:#7a8a9a;'>"
        "Antes/Después · 2 Volcanes · Diff Temporal</div></div>",
        unsafe_allow_html=True,
    )

    now = datetime.now(timezone.utc)
    mode_tabs = st.tabs([
        "⏱ Antes / Después",
        "🌋 2 Volcanes",
        "🔥 Diff Temporal",
    ])
    with mode_tabs[0]:
        _mode_antes_despues(now)
    with mode_tabs[1]:
        _mode_dos_volcanes(now)
    with mode_tabs[2]:
        _mode_diff_temporal(now)
