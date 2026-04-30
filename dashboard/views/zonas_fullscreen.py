"""Vista 4 Zonas Full Screen — máxima densidad visual.

Las 4 zonas volcánicas (Norte, Centro, Sur, Austral) en grilla 2×2,
ocupando toda la pantalla. Selector de producto único para las 4.

Diseño:
- Header mínimo: titulo + selector producto + status banner
- CSS oculta el padding default de Streamlit
- Cada zona es un mapa de ~700 px de altura
- 2x2 grid → uso pantalla casi total

Caso de uso: barrer las 4 zonas en paralelo, comparar evolución entre
norte y sur, ver dispersión de plumas a escala continental.

Filosofía: como Modo Guardia pero con MAS densidad visual y solo Chile,
sin distractores.
"""

import logging
from datetime import datetime, timezone

import numpy as np
import plotly.graph_objects as go
import streamlit as st

from dashboard.map_helpers import add_chile_border
from dashboard.utils import fmt_chile, parse_rammb_ts
from src.config import VOLCANIC_ZONES
from src.fetch.goes_fdcf import HotSpot, fetch_latest_hotspots
from src.fetch.rammb_slider import (
    fetch_frame_robust, get_latest_timestamps, ZOOM_ZONE,
)
from src.volcanos import CATALOG

logger = logging.getLogger(__name__)

REFRESH_SECONDS = 60

PRODUCT_OPTIONS = {
    "eumetsat_ash": "Ash RGB",
    "geocolor": "GeoColor",
    "jma_so2": "SO2 RGB",
}

ZONE_LABELS = {
    "norte":   "Zona Norte",
    "centro":  "Zona Centro",
    "sur":     "Zona Sur",
    "austral": "Zona Austral",
}

ZONE_COLORS = {
    "norte":   "#CC3311",
    "centro":  "#EE7733",
    "sur":     "#009988",
    "austral": "#0077BB",
}


@st.cache_data(ttl=30, show_spinner=False)
def _recent_ts(product: str, n: int = 3) -> list[str]:
    return get_latest_timestamps(product, n=n)


@st.cache_data(ttl=300, show_spinner=False)
def _hotspots_zone(zone_key: str) -> tuple[list[HotSpot], datetime | None]:
    bounds = VOLCANIC_ZONES[zone_key]
    try:
        return fetch_latest_hotspots(bounds=bounds, hours_back=1)
    except Exception:
        return [], None


def _array_to_data_url(arr: np.ndarray) -> str:
    import base64
    import io
    from PIL import Image
    img = Image.fromarray(arr.astype(np.uint8))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def _zone_fig(img: np.ndarray | None, zone_key: str, label: str,
              hotspots: list[HotSpot], height: int = 720,
              show_volcanoes: bool = True):
    bounds = VOLCANIC_ZONES[zone_key]
    fig = go.Figure()
    if img is not None:
        fig.add_layout_image(
            source=_array_to_data_url(img),
            xref="x", yref="y",
            x=bounds["lon_min"], y=bounds["lat_max"],
            sizex=bounds["lon_max"] - bounds["lon_min"],
            sizey=bounds["lat_max"] - bounds["lat_min"],
            sizing="stretch", layer="below",
        )

    # Volcanes en la zona como triangulos
    if show_volcanoes:
        zone_volcs = [v for v in CATALOG
                      if bounds["lat_min"] <= v.lat <= bounds["lat_max"]
                      and bounds["lon_min"] <= v.lon <= bounds["lon_max"]
                      and v.zone != "test"]
        if zone_volcs:
            fig.add_trace(go.Scatter(
                x=[v.lon for v in zone_volcs],
                y=[v.lat for v in zone_volcs],
                mode="markers",
                marker=dict(symbol="triangle-up", size=10, color="#00ffff",
                            line=dict(color="white", width=1)),
                text=[f"<b>{v.name}</b><br>{v.elevation:,} m" for v in zone_volcs],
                hoverinfo="text", showlegend=False,
            ))

    # Hot spots NOAA FDCF
    if hotspots:
        labels_hs = [f"{h.temp_k:.0f}K · FRP {h.frp_mw:.1f}MW ({h.confidence})"
                     for h in hotspots]
        fig.add_trace(go.Scatter(
            x=[h.lon for h in hotspots],
            y=[h.lat for h in hotspots],
            mode="markers",
            marker=dict(symbol="diamond", size=12, color="#ff3300",
                        line=dict(color="white", width=1)),
            text=labels_hs, hoverinfo="text", showlegend=False,
        ))

    # Frontera de Chile (overlay)
    add_chile_border(fig)

    # Aspect ratio correcto en km (mismo fix que modo_guardia_volcan)
    cos_lat = max(0.1, float(np.cos(np.radians(
        (bounds["lat_min"] + bounds["lat_max"]) / 2
    ))))
    fig.update_xaxes(range=[bounds["lon_min"], bounds["lon_max"]],
                     showgrid=False, visible=False)
    fig.update_yaxes(range=[bounds["lat_min"], bounds["lat_max"]],
                     showgrid=False, visible=False,
                     scaleanchor="x", scaleratio=1.0 / cos_lat)
    fig.update_layout(
        title=dict(text=label, font=dict(size=14, color=ZONE_COLORS[zone_key]),
                   x=0.02),
        height=height, margin=dict(l=0, r=0, t=32, b=0),
        paper_bgcolor="#0a0e14", plot_bgcolor="#0a0e14",
    )
    if img is None:
        fig.add_annotation(text="Sin imagen", xref="paper", yref="paper",
                           x=0.5, y=0.5, showarrow=False,
                           font=dict(color="#7a8a9a", size=14))
    return fig


@st.fragment(run_every=f"{REFRESH_SECONDS}s")
def _grid_4_zonas(product: str, show_volcanoes: bool, show_hotspots: bool,
                  layout: str = "2x2", height: int = 720):
    """Renderiza las 4 zonas en grilla.

    layout:
        '2x2'  — 2 filas de 2 columnas (default, balanceado)
        '1x4'  — 1 fila de 4 columnas (monitor 24/7 horizontal,
                 más zonas visibles en paralelo)
    height: altura en px de cada plot.
    """
    timestamps = _recent_ts(product, n=3)
    if not timestamps:
        st.error("RAMMB no respondió.")
        return

    ts = timestamps[0]
    now = datetime.now(timezone.utc)
    try:
        scan_dt = parse_rammb_ts(ts)
        age_min = int((now - scan_dt).total_seconds() / 60)
    except Exception:
        scan_dt = None
        age_min = -1

    # Banner status
    if age_min < 0:
        bnr_color = "#888"; bnr_msg = "Sin scan disponible"
    elif age_min < 15:
        bnr_color = "#3fb950"; bnr_msg = f"Scan hace {age_min} min · OK"
    elif age_min < 30:
        bnr_color = "#d29922"; bnr_msg = f"Scan hace {age_min} min · RAMMB lento"
    else:
        bnr_color = "#ff4444"; bnr_msg = f"Scan hace {age_min} min · datos atrasados"

    st.markdown(
        f"<div style='background:#0f1418; border-left:4px solid {bnr_color}; "
        f"padding:0.4rem 0.8rem; border-radius:4px; margin-bottom:0.4rem; "
        f"display:flex; justify-content:space-between;'>"
        f"<span style='color:#e0e0e0;'>{PRODUCT_OPTIONS[product]} · "
        f"4 zonas en paralelo</span>"
        f"<span style='color:{bnr_color}; font-weight:600;'>{bnr_msg}</span>"
        f"</div>",
        unsafe_allow_html=True,
    )

    # Layout configurable
    if layout == "1x4":
        rows_zones = [["norte", "centro", "sur", "austral"]]
        n_cols = 4
    else:  # default 2x2
        rows_zones = [["norte", "centro"], ["sur", "austral"]]
        n_cols = 2

    fallback_count = 0
    for row_zones in rows_zones:
        cols = st.columns(n_cols)
        for i, zone_key in enumerate(row_zones):
            bounds = VOLCANIC_ZONES[zone_key]
            img, used_ts, used_zoom = fetch_frame_robust(
                product, timestamps, bounds,
                zoom_preferred=ZOOM_ZONE, zoom_fallback=ZOOM_ZONE - 1,
            )
            if used_ts and used_ts != ts:
                fallback_count += 1
            if used_zoom < ZOOM_ZONE:
                fallback_count += 1

            hotspots = []
            if show_hotspots:
                hotspots, _ = _hotspots_zone(zone_key)

            label = ZONE_LABELS[zone_key]
            if used_ts and used_ts != ts:
                label += " ⚠ ts cercano"

            with cols[i]:
                st.plotly_chart(
                    _zone_fig(img, zone_key, label, hotspots,
                              height=height, show_volcanoes=show_volcanoes),
                    use_container_width=True,
                    config={"displayModeBar": False},
                )


def render():
    # CSS agresivo: oculta header Streamlit, padding mínimo, casi full screen
    st.markdown(
        """
        <style>
          [data-testid="stHeader"] { background: rgba(0,0,0,0); height: 0; }
          .block-container {
            padding-top: 0.4rem !important;
            padding-bottom: 0.4rem !important;
            padding-left: 0.6rem !important;
            padding-right: 0.6rem !important;
            max-width: 100% !important;
          }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Header compacto + selectores en 1 linea
    cols = st.columns([2.0, 1.4, 1.4, 1.2, 1.2])
    with cols[0]:
        st.markdown(
            "<div style='font-size:1.3rem; font-weight:800; color:#ff6644; "
            "padding-top:0.3rem;'>🗺 4 ZONAS — FULL SCREEN</div>",
            unsafe_allow_html=True,
        )
    with cols[1]:
        product = st.selectbox(
            "Producto",
            options=list(PRODUCT_OPTIONS.keys()),
            format_func=lambda k: PRODUCT_OPTIONS[k],
            index=0, key="zonas_product",
            label_visibility="collapsed",
        )
    with cols[2]:
        layout_label = st.radio(
            "Layout",
            ["1×4 (TV)", "2×2"],
            index=0, key="zonas_layout",
            horizontal=True,
            label_visibility="collapsed",
        )
    with cols[3]:
        show_volcanoes = st.toggle(
            "🔺 Volcanes", value=True, key="zonas_volc",
        )
    with cols[4]:
        show_hotspots = st.toggle(
            "🔥 Hot spots", value=True, key="zonas_hs",
        )

    layout_key = "1x4" if layout_label.startswith("1×4") else "2x2"
    height = 820 if layout_key == "1x4" else 720
    _grid_4_zonas(product, show_volcanoes, show_hotspots,
                  layout=layout_key, height=height)
