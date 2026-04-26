"""Loop animado continuo de un volcan: 12 frames ultimas 2h, auto-play loop.

A diferencia de rammb_viewer (Animacion) que requiere boton 'Cargar' y permite
varias duraciones/scopes, esta vista esta hardcoded para uso operacional rapido:
  - 12 frames (2h ventana)
  - Zoom volcan (~38km radio)
  - Auto-play infinito
  - Sin slider de tiempo (solo mira)

Uso tipico: dejar la tab abierta para ver evolucion en vivo. La animacion
re-fetcha cuando cambia el volcan o el producto.
"""

import logging
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import plotly.graph_objects as go
import streamlit as st

from dashboard.utils import parse_rammb_ts
from src.fetch.rammb_slider import (
    fetch_frame_for_bounds, get_latest_timestamps,
    ZOOM_VOLCAN, ZOOM_ZONE,
)
from src.volcanos import PRIORITY_VOLCANOES, get_volcano

logger = logging.getLogger(__name__)

LOOP_FRAMES = 12  # 12 * 10 min = 2h
LOOP_RADIUS_DEG = 0.35
PRODUCT_OPTIONS = {
    "eumetsat_ash": "Ash RGB",
    "geocolor": "GeoColor",
    "jma_so2": "SO2 RGB",
}


def _frame_label(ts: str) -> str:
    """20260425221000 -> '22:10 UTC'."""
    try:
        dt = parse_rammb_ts(ts)
        return dt.strftime("%H:%M UTC")
    except Exception:
        return ts


@st.cache_data(ttl=600, show_spinner=False)
def _fetch_loop_frames(product: str, lat: float, lon: float, n: int = LOOP_FRAMES,
                       zoom: int = ZOOM_VOLCAN) -> list[dict]:
    """Bajar N frames recientes para el bbox del volcan. Cache 10 min.

    Sigue el mismo patron que _fetch_bounds_frames de rammb_viewer:
      1. get_latest_timestamps(product, n=N)
      2. fetch_frame_for_bounds para cada ts en paralelo
      3. Filtrar None y ordenar viejo->nuevo
    """
    bounds = {
        "lat_min": lat - LOOP_RADIUS_DEG, "lat_max": lat + LOOP_RADIUS_DEG,
        "lon_min": lon - LOOP_RADIUS_DEG, "lon_max": lon + LOOP_RADIUS_DEG,
    }
    timestamps = get_latest_timestamps(product, n=n)
    if not timestamps:
        return []

    def _one(ts):
        try:
            return ts, fetch_frame_for_bounds(product, ts, bounds, zoom=zoom)
        except Exception:
            return ts, None

    out = []
    with ThreadPoolExecutor(max_workers=6) as ex:
        results = list(ex.map(_one, timestamps))
    for ts, img in results:
        if img is None:
            continue
        out.append({
            "ts": ts,
            "label": f"{_frame_label(ts)} · loop",
            "image": img,
            "bounds": bounds,
        })
    out.sort(key=lambda f: f["ts"])
    return out


def _img_to_b64(arr: np.ndarray) -> str:
    import base64
    import io
    from PIL import Image
    img = Image.fromarray(arr.astype(np.uint8))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


def _build_loop_figure(frames: list[dict], v, height: int = 720) -> go.Figure:
    if not frames:
        return None
    bounds = frames[0]["bounds"]
    lon_min, lon_max = bounds["lon_min"], bounds["lon_max"]
    lat_min, lat_max = bounds["lat_min"], bounds["lat_max"]
    cos_lat = max(0.1, float(np.cos(np.radians(v.lat))))

    base_traces = [
        go.Scatter(x=[lon_min, lon_max], y=[lat_min, lat_max],
                   mode="markers", marker=dict(opacity=0),
                   showlegend=False, hoverinfo="skip"),
        go.Scatter(x=[v.lon], y=[v.lat], mode="markers",
                   marker=dict(symbol="triangle-up", size=14, color="#00ffff",
                               line=dict(color="white", width=1.5)),
                   showlegend=False, hovertemplate=f"<b>{v.name}</b><extra></extra>"),
    ]

    plotly_frames = []
    for i, f in enumerate(frames):
        b64 = _img_to_b64(f["image"])
        plotly_frames.append(go.Frame(
            data=base_traces,
            layout=go.Layout(
                images=[dict(
                    source=f"data:image/png;base64,{b64}",
                    xref="x", yref="y",
                    x=lon_min, y=lat_max,
                    xanchor="left", yanchor="top",
                    sizex=lon_max - lon_min, sizey=lat_max - lat_min,
                    sizing="stretch", layer="below",
                )],
                title_text=f["label"],
            ),
            name=str(i),
        ))

    b64_first = _img_to_b64(frames[0]["image"])
    fig = go.Figure(
        data=base_traces,
        layout=go.Layout(
            images=[dict(
                source=f"data:image/png;base64,{b64_first}",
                xref="x", yref="y",
                x=lon_min, y=lat_max,
                xanchor="left", yanchor="top",
                sizex=lon_max - lon_min, sizey=lat_max - lat_min,
                sizing="stretch", layer="below",
            )],
            title=dict(text=frames[0]["label"], font=dict(size=12, color="#ccc")),
            xaxis=dict(range=[lon_min, lon_max], showgrid=False, visible=False),
            yaxis=dict(range=[lat_min, lat_max], showgrid=False, visible=False,
                       scaleanchor="x", scaleratio=1.0 / cos_lat),
            height=height,
            margin=dict(t=40, b=10, l=10, r=10),
            paper_bgcolor="#0a0e14", plot_bgcolor="#0a0e14",
            updatemenus=[dict(
                type="buttons", showactive=False,
                y=1.02, x=0.0, xanchor="left", yanchor="bottom",
                pad=dict(t=0, l=0),
                buttons=[
                    dict(label="▶ Play", method="animate",
                         args=[None, dict(
                             frame=dict(duration=600, redraw=True),
                             fromcurrent=True, transition=dict(duration=0),
                             mode="immediate", loop=True,
                         )]),
                    dict(label="⏸ Pause", method="animate",
                         args=[[None], dict(
                             frame=dict(duration=0, redraw=False),
                             mode="immediate", transition=dict(duration=0),
                         )]),
                ],
            )],
        ),
        frames=plotly_frames,
    )
    return fig


def render_subtab():
    """Sub-tab Loop 2h — selector volcan + producto + animacion auto-play."""
    cols = st.columns([2, 1, 1])
    with cols[0]:
        volcan_name = st.selectbox(
            "Volcán", options=PRIORITY_VOLCANOES,
            index=0, key="loop_volcan",
        )
    with cols[1]:
        product = st.selectbox(
            "Producto",
            options=list(PRODUCT_OPTIONS.keys()),
            format_func=lambda k: PRODUCT_OPTIONS[k],
            index=0, key="loop_product",
        )
    with cols[2]:
        st.markdown(
            "<div style='font-size:0.75rem; color:#7a8a9a; padding-top:0.5rem;'>"
            f"{LOOP_FRAMES} frames · ventana 2h · auto-loop</div>",
            unsafe_allow_html=True,
        )

    v = get_volcano(volcan_name)
    if v is None:
        st.error("Volcán no encontrado.")
        return

    with st.spinner(f"Bajando {LOOP_FRAMES} frames de {v.name}…"):
        frames = _fetch_loop_frames(product, v.lat, v.lon)
        # Fallback zoom 3 si nada cargó
        if not frames:
            frames = _fetch_loop_frames(product, v.lat, v.lon, zoom=ZOOM_ZONE)
            if frames:
                st.caption(f"⚠ Frames cargados en zoom 3 (RAMMB no sirvió zoom 4 para {PRODUCT_OPTIONS[product]}).")

    if not frames:
        st.error("No se pudieron bajar frames. Probá otro producto o volcán.")
        return

    fig = _build_loop_figure(frames, v, height=720)
    if fig is None:
        st.error("No se pudo construir animación.")
        return

    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    try:
        ts_first = parse_rammb_ts(frames[0]["ts"])
        ts_last = parse_rammb_ts(frames[-1]["ts"])
        st.caption(
            f"📌 {v.name} · {PRODUCT_OPTIONS[product]} · "
            f"{len(frames)} frames · "
            f"{ts_first.strftime('%H:%M')} → {ts_last.strftime('%H:%M UTC')} · "
            f"presioná ▶ Play para auto-loop continuo · cache 10 min"
        )
    except Exception:
        pass


def render():
    """Entry point standalone (cuando se llama desde Modo Guardia → Loop 2h)."""
    render_subtab()
