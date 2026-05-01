"""Mosaico Chile: los 8 volcanes prioritarios en grilla 4x2.

FILOSOFIA: barrer todo Chile en un golpe de vista. Una mini-imagen
Ash RGB por volcan, zoom volcan, sin numeros, sin alertas. El experto
ve los 8 cuadros y decide si algo merece zoom adicional.

Auto-refresh 60s. Cada miniatura usa el ultimo scan disponible.
"""

import logging
from datetime import datetime, timezone

import numpy as np
import plotly.graph_objects as go
import streamlit as st

from dashboard.utils import fmt_chile, parse_rammb_ts
from src.fetch.rammb_slider import (
    fetch_frame_robust, get_latest_timestamps, ZOOM_VOLCAN, ZOOM_ZONE,
)
from src.volcanos import PRIORITY_VOLCANOES, get_volcano

logger = logging.getLogger(__name__)

REFRESH_SECONDS = 60
ROTATION_SECONDS = 10
# Radio del bbox por volcan en el mosaico. 0.5° (~55 km lado-medio) maximiza
# pixeles reales RAMMB zoom=4 por miniatura sin perder identificacion del crater.
# Antes era 0.35° (~38 km) -> mas zoom perceptual pero solo ~22x22 px reales
# que se estiraban a 420 px de pantalla (upscale 19x, look pixelado).
# 0.5° -> ~32x32 px reales, upscale 13x, mejor balance contexto/detalle.
RADIUS_DEG = 0.5
PRODUCT_LIST_TV = ["geocolor", "eumetsat_ash", "jma_so2"]

PRODUCT_OPTIONS = {
    "eumetsat_ash": "Ash RGB",
    "geocolor": "GeoColor",
    "jma_so2": "SO2 RGB",
}


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


def _array_to_data_url(arr: np.ndarray) -> str:
    import base64
    import io
    from PIL import Image
    img = Image.fromarray(arr.astype(np.uint8))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


RING_RADII_KM = [5, 10, 25, 50]


def _circle_points(lat0: float, lon0: float, radius_km: float, n: int = 48):
    theta = np.linspace(0, 2 * np.pi, n)
    dlat = (radius_km / 111.0) * np.cos(theta)
    dlon = (radius_km / (111.0 * float(np.cos(np.radians(lat0))))) * np.sin(theta)
    return (lat0 + dlat).tolist(), (lon0 + dlon).tolist()


def _render_mini(img: np.ndarray | None, lat: float, lon: float, name: str,
                 height: int = 420, show_rings: bool = False):
    """Mini-plot cuadrado con bbox compensado por latitud.

    Antes el bbox era ±RADIUS_DEG en ambas dimensiones; con
    `scaleratio=1/cos_lat` los volcanes a alta latitud (Villarrica -39°)
    quedaban con padding lateral mientras los de baja latitud (Lascar -23°)
    llenaban toda la caja. Fix: expandir el rango de lon por 1/cos_lat
    para que la imagen visible sea siempre ~cuadrada en pantalla.
    """
    fig = go.Figure()
    cos_lat = max(0.1, float(np.cos(np.radians(lat))))
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
        marker=dict(symbol="triangle-up", size=12, color="#00ffff",
                    line=dict(color="white", width=1)),
        hovertemplate=f"<b>{name}</b><extra></extra>",
        showlegend=False,
    ))
    fig.update_xaxes(range=[bounds["lon_min"], bounds["lon_max"]],
                     showgrid=False, visible=False)
    fig.update_yaxes(range=[bounds["lat_min"], bounds["lat_max"]],
                     showgrid=False, visible=False,
                     scaleanchor="x", scaleratio=1.0 / cos_lat)
    fig.update_layout(
        title=dict(text=f"<b>{name}</b>", font=dict(size=12, color="#e0e0e0"), x=0.02),
        height=height, margin=dict(l=0, r=0, t=25, b=0),
        paper_bgcolor="#0a0e14", plot_bgcolor="#0a0e14",
    )
    if img is None:
        fig.add_annotation(
            text="sin datos",
            xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False,
            font=dict(color="#556", size=11),
        )
    return fig


@st.fragment(run_every=f"{REFRESH_SECONDS}s")
def _grid_fragment(product: str):
    """Solo el grid se auto-refresca cada 60s. El selector queda afuera."""
    timestamps = _recent_timestamps(product, n=5)
    now = datetime.now(timezone.utc)
    if not timestamps:
        st.error("RAMMB no respondió. Reintentá en unos segundos.")
        return

    ts = timestamps[0]
    try:
        scan_dt = parse_rammb_ts(ts)
        age_min = int((now - scan_dt).total_seconds() / 60)
        scan_label = f"{scan_dt.strftime('%H:%M UTC')} (hace {age_min} min)"
    except Exception:
        scan_label = ts

    rings_str = " / ".join(str(r) for r in RING_RADII_KM)
    st.markdown(
        f"<div style='background:#0f1418; border-left:4px solid #ff6644; "
        f"padding:0.6rem 1rem; border-radius:4px; margin-bottom:0.8rem; "
        f"display:flex; justify-content:space-between; align-items:center;'>"
        f"<div style='color:#e0e0e0;'>{PRODUCT_OPTIONS[product]} · "
        f"8 volcanes prioritarios &middot; "
        f"<span style='color:#9aaabb; font-size:0.85rem;'>"
        f"⊙ anillos {rings_str} km desde el crater</span></div>"
        f"<div style='color:#9aaabb; font-size:0.85rem;'>Scan {scan_label} · "
        f"render {now.strftime('%H:%M:%S')} UTC</div></div>",
        unsafe_allow_html=True,
    )

    # Grid 2 filas x 4 columnas
    fallback_ts = 0
    fallback_zoom = 0
    rows = [PRIORITY_VOLCANOES[:4], PRIORITY_VOLCANOES[4:8]]
    for row_volcanos in rows:
        cols = st.columns(4)
        for i, name in enumerate(row_volcanos):
            v = get_volcano(name)
            if v is None:
                continue
            img, used_ts, used_zoom = _volcano_frame_with_fallback(
                product, timestamps, v.lat, v.lon,
            )
            if used_ts and used_ts != ts:
                fallback_ts += 1
            if used_zoom == ZOOM_ZONE:
                fallback_zoom += 1
            with cols[i]:
                st.plotly_chart(
                    _render_mini(img, v.lat, v.lon, name, show_rings=True),
                    use_container_width=True,
                    config={"displayModeBar": False},
                )

    notes = []
    if fallback_ts:
        notes.append(f"{fallback_ts} con scan previo")
    if fallback_zoom:
        notes.append(f"{fallback_zoom} en zoom 3 (RAMMB no sirvió zoom 4)")
    if notes:
        st.caption("ℹ " + " · ".join(notes))


@st.fragment(run_every=f"{ROTATION_SECONDS}s")
def _grid_fragment_tv(session_key: str = "tv_mosaico_rot_idx"):
    """Modo TV puro: 8 prioritarios en grid 4x2, paneles grandes,
    rotando productos GeoColor -> Ash -> SO2 cada 10s, con anillos.

    Sin chrome (toolbar, banner status). Solo etiqueta minimal flotante.
    """
    import io
    import base64
    if session_key not in st.session_state:
        st.session_state[session_key] = 0
    idx = st.session_state[session_key] % len(PRODUCT_LIST_TV)
    current = PRODUCT_LIST_TV[idx]
    next_idx = (idx + 1) % len(PRODUCT_LIST_TV)
    st.session_state[session_key] = next_idx

    # Leyenda compacta interpretativa en el espacio negro superior.
    # Cambia con el producto rotante.
    from dashboard.map_helpers import render_compact_legend
    render_compact_legend(
        current,
        extra_left=(f"<span style='color:#ff6644; font-weight:700; "
                    f"margin-right:0.2rem;'>🔄 Mosaico 8 ·</span>"),
    )

    timestamps = _recent_timestamps(current, n=5)
    if not timestamps:
        st.error("RAMMB no respondió.")
        return

    # Grid 2 filas x 4 columnas, paneles grandes (450 px)
    rows = [PRIORITY_VOLCANOES[:4], PRIORITY_VOLCANOES[4:8]]
    for row_volcanos in rows:
        cols = st.columns(4)
        for i, name in enumerate(row_volcanos):
            v = get_volcano(name)
            if v is None:
                continue
            img, _, _ = _volcano_frame_with_fallback(
                current, timestamps, v.lat, v.lon,
            )
            with cols[i]:
                st.plotly_chart(
                    _render_mini(img, v.lat, v.lon, name,
                                 height=450, show_rings=True),
                    use_container_width=True,
                    config={"displayModeBar": False},
                )


def _live_panel():
    """Selector de producto + grid con auto-refresh."""
    product = st.selectbox(
        "Producto",
        options=list(PRODUCT_OPTIONS.keys()),
        format_func=lambda k: PRODUCT_OPTIONS[k],
        index=0, key="mosaico_product",
    )
    _grid_fragment(product)
    st.markdown(
        "<div style='text-align:center; color:#445566; font-size:0.75rem; "
        "margin-top:0.8rem; padding-top:0.5rem; border-top:1px solid #223;'>"
        "<i>Sin metricas automaticas. Si algo llama la atencion en una "
        "miniatura, ir a 'Modo Guardia → Volcán' para ver con detalle.</i></div>",
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
        "8 prioritarios · Ash RGB · zoom volcan</div></div>",
        unsafe_allow_html=True,
    )
    _live_panel()
