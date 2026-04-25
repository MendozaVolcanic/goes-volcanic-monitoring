"""Modo Guardia VOLCAN: zoom a un volcan, 3 productos lado a lado.

FILOSOFIA: igual que Modo Guardia (Chile) — solo imagen, sin metricas
automaticas. Aca el zoom es del volcan (~30 km radio) y mostramos 3
composiciones distintas para que el experto compare:

  1. Ash RGB (EUMETSAT receta) — tipico para detectar ceniza
  2. GeoColor — visible/IR, util de dia
  3. SO2 (JMA receta) — destaca SO2 en plumas frescas

Hot spots NOAA FDCF dentro del bbox se overlayean en la primera vista.

Auto-refresh 60s. Sin %, sin alertas.
"""

import logging
from datetime import datetime, timezone

import numpy as np
import plotly.graph_objects as go
import streamlit as st

from dashboard.utils import fmt_chile, parse_rammb_ts
from src.fetch.goes_fdcf import HotSpot, fetch_latest_hotspots
from src.fetch.rammb_slider import (
    fetch_frame_for_bounds, get_latest_timestamps, ZOOM_VOLCAN,
)
from src.volcanos import PRIORITY_VOLCANOES, get_volcano

logger = logging.getLogger(__name__)

REFRESH_SECONDS = 60
DEFAULT_VOLCANO = "Villarrica"
RADIUS_DEG = 0.35  # ~38 km — un volcan + sus alrededores


PRODUCTS = [
    ("eumetsat_ash", "Ash RGB", "EUMETSAT B15-B14 / B14-B11 / B13"),
    ("geocolor", "GeoColor", "Visible mejorado (CIRA)"),
    ("jma_so2", "SO2 RGB", "JMA B07-B09 / B09-B11"),
]


@st.cache_data(ttl=30, show_spinner=False)
def _latest_ts(product: str) -> str | None:
    times = get_latest_timestamps(product, n=1)
    return times[0] if times else None


@st.cache_data(ttl=7200, show_spinner=False)
def _frame(product: str, ts: str, lat_min: float, lat_max: float,
           lon_min: float, lon_max: float) -> np.ndarray | None:
    bounds = {"lat_min": lat_min, "lat_max": lat_max,
              "lon_min": lon_min, "lon_max": lon_max}
    try:
        return fetch_frame_for_bounds(product, ts, bounds, zoom=ZOOM_VOLCAN)
    except Exception as e:
        logger.warning("frame %s %s fallo: %s", product, ts, e)
        return None


@st.cache_data(ttl=300, show_spinner=False)
def _hotspots_volcan(lat_min: float, lat_max: float,
                     lon_min: float, lon_max: float
                     ) -> tuple[list[HotSpot], datetime | None]:
    bounds = {"lat_min": lat_min, "lat_max": lat_max,
              "lon_min": lon_min, "lon_max": lon_max}
    try:
        return fetch_latest_hotspots(bounds=bounds, hours_back=1)
    except Exception as e:
        logger.warning("hotspots fallo: %s", e)
        return [], None


def _array_to_data_url(arr: np.ndarray) -> str:
    import base64
    import io
    from PIL import Image
    img = Image.fromarray(arr.astype(np.uint8))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def _render_product(img: np.ndarray | None, bounds: dict, product_label: str,
                    volcan_lat: float, volcan_lon: float, volcan_name: str,
                    hotspots: list[HotSpot] | None = None):
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
    # Triangulo crater
    fig.add_trace(go.Scatter(
        x=[volcan_lon], y=[volcan_lat], mode="markers",
        marker=dict(symbol="triangle-up", size=16, color="#00ffff",
                    line=dict(color="white", width=1.5)),
        hovertemplate=f"<b>{volcan_name}</b><br>%{{x:.3f}}, %{{y:.3f}}<extra></extra>",
        showlegend=False,
    ))
    # Hotspots si vinieron
    if hotspots:
        lats = [h.lat for h in hotspots]
        lons = [h.lon for h in hotspots]
        labels = [f"{h.temp_k:.0f}K · FRP {h.frp_mw:.1f}MW" for h in hotspots]
        fig.add_trace(go.Scatter(
            x=lons, y=lats, mode="markers",
            marker=dict(symbol="diamond", size=10, color="#ff3300",
                        line=dict(color="white", width=1)),
            text=labels, hoverinfo="text", showlegend=False,
        ))
    fig.update_xaxes(range=[bounds["lon_min"], bounds["lon_max"]],
                     showgrid=False, visible=False)
    fig.update_yaxes(range=[bounds["lat_min"], bounds["lat_max"]],
                     showgrid=False, visible=False, scaleanchor="x", scaleratio=1)
    fig.update_layout(
        title=dict(text=product_label, font=dict(size=13, color="#e0e0e0"), x=0.02),
        height=380, margin=dict(l=0, r=0, t=30, b=0),
        paper_bgcolor="#0a0e14", plot_bgcolor="#0a0e14",
    )
    if img is None:
        fig.add_annotation(
            text="Sin imagen disponible",
            xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False,
            font=dict(color="#7a8a9a", size=14),
        )
    return fig


@st.fragment(run_every=f"{REFRESH_SECONDS}s")
def _live_panel(volcan_name: str):
    v = get_volcano(volcan_name)
    if v is None:
        st.error(f"Volcan {volcan_name} no esta en el catalogo.")
        return

    bounds = {
        "lat_min": v.lat - RADIUS_DEG, "lat_max": v.lat + RADIUS_DEG,
        "lon_min": v.lon - RADIUS_DEG, "lon_max": v.lon + RADIUS_DEG,
    }
    now = datetime.now(timezone.utc)

    # Hot spots dentro del bbox (solo overlay sobre Ash RGB)
    hotspots, _ = _hotspots_volcan(
        bounds["lat_min"], bounds["lat_max"],
        bounds["lon_min"], bounds["lon_max"],
    )

    # Cabecera info
    st.markdown(
        f"<div style='background:#0f1418; border-left:4px solid #ff6644; "
        f"padding:0.7rem 1rem; border-radius:4px; margin-bottom:0.8rem;'>"
        f"<div style='display:flex; justify-content:space-between; align-items:center;'>"
        f"<div><span style='font-size:1.4rem; font-weight:800; color:#ff6644;'>"
        f"{v.name}</span> &nbsp;"
        f"<span style='color:#7a8a9a; font-size:0.85rem;'>"
        f"{v.region} · elev {v.elevation} m · {v.lat}°, {v.lon}°</span></div>"
        f"<div style='font-size:0.85rem; color:#9aaabb;'>"
        f"Hot spots {len(hotspots)} · Render {now.strftime('%H:%M:%S')} UTC / "
        f"{fmt_chile(now)}</div></div></div>",
        unsafe_allow_html=True,
    )

    cols = st.columns(3)
    for i, (prod_id, label, recipe) in enumerate(PRODUCTS):
        ts = _latest_ts(prod_id)
        img = None
        ts_label = "—"
        if ts:
            img = _frame(prod_id, ts,
                         bounds["lat_min"], bounds["lat_max"],
                         bounds["lon_min"], bounds["lon_max"])
            try:
                ts_dt = parse_rammb_ts(ts)
                age = int((now - ts_dt).total_seconds() / 60)
                ts_label = f"{ts_dt.strftime('%H:%M UTC')} (hace {age} min)"
            except Exception:
                ts_label = ts

        # Hotspots solo overlay sobre Ash RGB (primera columna)
        hs = hotspots if prod_id == "eumetsat_ash" else None
        full_label = f"{label} · {ts_label}"
        with cols[i]:
            st.plotly_chart(
                _render_product(img, bounds, full_label, v.lat, v.lon, v.name, hs),
                use_container_width=True,
                config={"displayModeBar": False},
            )
            st.markdown(
                f"<div style='font-size:0.7rem; color:#556; margin-top:-0.5rem;'>"
                f"{recipe}</div>",
                unsafe_allow_html=True,
            )

    # Footer filosofia
    st.markdown(
        "<div style='text-align:center; color:#445566; font-size:0.75rem; "
        "margin-top:1rem; padding-top:0.5rem; border-top:1px solid #223;'>"
        "<i>Sin metricas automaticas — el dashboard muestra el dato. "
        "La interpretacion queda al experto.</i></div>",
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
        "padding-bottom:0.6rem; border-bottom:2px solid #223; margin-bottom:0.8rem;'>"
        "<div style='font-size:1.5rem; font-weight:800; color:#ff6644;'>"
        "🛡 MODO GUARDIA — VOLCAN</div>"
        "<div style='font-size:0.85rem; color:#7a8a9a;'>"
        "Zoom volcan · 3 productos lado a lado · GOES-19</div></div>",
        unsafe_allow_html=True,
    )

    cols = st.columns([3, 1])
    with cols[1]:
        volcan = st.selectbox(
            "Volcan",
            options=PRIORITY_VOLCANOES,
            index=PRIORITY_VOLCANOES.index(DEFAULT_VOLCANO)
            if DEFAULT_VOLCANO in PRIORITY_VOLCANOES else 0,
            label_visibility="collapsed",
            key="modoguardiavolcan_selector",
        )

    _live_panel(volcan)
