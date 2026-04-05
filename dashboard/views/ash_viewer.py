"""Pagina Ash RGB Viewer: visualizacion de ceniza volcanica y SO2."""

import logging
from datetime import datetime, timedelta, timezone

import numpy as np
import plotly.graph_objects as go
import streamlit as st

from dashboard.style import ash_legend, header, info_panel, kpi_card
from src.config import CHILE_BOUNDS, VOLCANIC_ZONES
from src.process.pipeline import get_latest_processed, load_processed, process_ash_rgb
from src.volcanos import CATALOG

logger = logging.getLogger(__name__)

ZONE_OPTIONS = {
    "Chile completo": CHILE_BOUNDS,
    "Zona Norte": VOLCANIC_ZONES["norte"],
    "Zona Centro": VOLCANIC_ZONES["centro"],
    "Zona Sur": VOLCANIC_ZONES["sur"],
    "Zona Austral": VOLCANIC_ZONES["austral"],
}


def _fig_ash_rgb(rgb, lat, lon, title, volcanoes=None):
    img = (np.clip(rgb, 0, 1) * 255).astype(np.uint8)
    fig = go.Figure()
    fig.add_trace(go.Image(
        z=img,
        x0=float(lon.min()), dx=(float(lon.max()) - float(lon.min())) / rgb.shape[1],
        y0=float(lat.max()), dy=-(float(lat.max()) - float(lat.min())) / rgb.shape[0],
    ))
    if volcanoes:
        vis = [v for v in volcanoes
               if lat.min() <= v.lat <= lat.max() and lon.min() <= v.lon <= lon.max()]
        if vis:
            fig.add_trace(go.Scatter(
                x=[v.lon for v in vis], y=[v.lat for v in vis],
                mode="markers+text",
                marker=dict(size=7, color="#00fff7", symbol="triangle-up",
                            line=dict(width=1, color="white")),
                text=[v.name for v in vis],
                textposition="top center",
                textfont=dict(size=8, color="rgba(255,255,255,0.8)"),
                name="Volcanes",
                hovertext=[f"{v.name} ({v.elevation:,}m)" for v in vis],
            ))
    fig.update_layout(
        title=dict(text=title, font=dict(size=14)),
        xaxis_title="Longitud", yaxis_title="Latitud",
        height=700, template="plotly_dark",
        yaxis=dict(scaleanchor="x", scaleratio=1),
        margin=dict(t=40, b=40, l=50, r=20),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    )
    return fig


def _fig_btd(btd, lat, lon, volcanoes=None):
    fig = go.Figure()
    fig.add_trace(go.Heatmap(
        z=btd,
        x=np.linspace(float(lon.min()), float(lon.max()), btd.shape[1]),
        y=np.linspace(float(lat.max()), float(lat.min()), btd.shape[0]),
        colorscale=[
            [0.0, "#b71c1c"], [0.2, "#e53935"], [0.4, "#ffca28"],
            [0.5, "#fafafa"], [0.6, "#81d4fa"], [0.8, "#1565c0"], [1.0, "#0d47a1"],
        ],
        zmin=-5, zmax=5,
        colorbar=dict(title="BTD (K)", thickness=15, len=0.7),
        hovertemplate="Lat: %{y:.2f}<br>Lon: %{x:.2f}<br>BTD: %{z:.2f} K<extra></extra>",
    ))
    if volcanoes:
        vis = [v for v in volcanoes
               if lat.min() <= v.lat <= lat.max() and lon.min() <= v.lon <= lon.max()]
        if vis:
            fig.add_trace(go.Scatter(
                x=[v.lon for v in vis], y=[v.lat for v in vis],
                mode="markers", name="Volcanes",
                marker=dict(size=6, color="#00ff88", symbol="triangle-up",
                            line=dict(width=1, color="#000")),
                text=[v.name for v in vis],
                hovertemplate="%{text}<extra></extra>",
            ))
    fig.update_layout(
        title=dict(text="BTD Split-Window (11.2 - 12.3 um)", font=dict(size=14)),
        xaxis_title="Longitud", yaxis_title="Latitud",
        height=700, template="plotly_dark",
        yaxis=dict(scaleanchor="x", scaleratio=1),
        margin=dict(t=40, b=40, l=50, r=20),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    )
    return fig


def _fig_confidence(conf, lat, lon, volcanoes=None):
    fig = go.Figure()
    fig.add_trace(go.Heatmap(
        z=conf,
        x=np.linspace(float(lon.min()), float(lon.max()), conf.shape[1]),
        y=np.linspace(float(lat.max()), float(lat.min()), conf.shape[0]),
        colorscale=[
            [0.0, "rgba(14,17,23,1)"], [0.25, "#fff9c4"],
            [0.5, "#ffb74d"], [0.75, "#e53935"], [1.0, "#b71c1c"],
        ],
        zmin=0, zmax=3,
        colorbar=dict(
            title="Nivel", thickness=15, len=0.7,
            tickvals=[0, 1, 2, 3],
            ticktext=["Ninguna", "Baja", "Media", "Alta"],
        ),
    ))
    if volcanoes:
        vis = [v for v in volcanoes
               if lat.min() <= v.lat <= lat.max() and lon.min() <= v.lon <= lon.max()]
        if vis:
            fig.add_trace(go.Scatter(
                x=[v.lon for v in vis], y=[v.lat for v in vis],
                mode="markers+text", name="Volcanes",
                marker=dict(size=6, color="#00fff7", symbol="triangle-up"),
                text=[v.name for v in vis],
                textposition="top center",
                textfont=dict(size=8, color="rgba(255,255,255,0.7)"),
            ))
    fig.update_layout(
        title=dict(text="Confianza Deteccion de Ceniza", font=dict(size=14)),
        xaxis_title="Longitud", yaxis_title="Latitud",
        height=700, template="plotly_dark",
        yaxis=dict(scaleanchor="x", scaleratio=1),
        margin=dict(t=40, b=40, l=50, r=20),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    )
    return fig


def render():
    header(
        "Ash RGB Viewer",
        "Deteccion de ceniza volcanica y SO2 desde GOES-19",
    )

    # ── Controles ──
    c1, c2, c3 = st.columns([1.5, 1, 1])
    with c1:
        zone_key = st.selectbox("Region", list(ZONE_OPTIONS.keys()), index=0)
    with c2:
        use_cached = st.checkbox("Usar cache", value=True)
    with c3:
        st.markdown("<div style='height:1.6rem'></div>", unsafe_allow_html=True)
        fetch_new = st.button("Descargar imagen fresca", type="primary", use_container_width=True)

    bounds = ZONE_OPTIONS[zone_key]

    # ── Obtener datos ──
    data = None

    if fetch_new:
        with st.spinner("Descargando 4 bandas IR desde AWS S3 (~100 MB)..."):
            try:
                now = datetime.now(timezone.utc)
                dt = now - timedelta(minutes=30)
                dt = dt.replace(minute=(dt.minute // 10) * 10, second=0, microsecond=0)
                data = process_ash_rgb(dt, bounds=bounds, save=True)
                st.toast(f"Procesado: {data['timestamp']}", icon="✅")
            except Exception as e:
                st.error(f"Error descargando datos: {e}")
                logger.exception("Error processing ash RGB")
    elif use_cached:
        info = get_latest_processed()
        if info:
            try:
                data = load_processed(info)
            except Exception as e:
                st.warning(f"Error cargando cache: {e}")

    # ── Sin datos → instrucciones ──
    if data is None:
        col_left, col_right = st.columns([2, 1])
        with col_left:
            info_panel(
                "<b>Sin datos en cache.</b> Presiona <b>Descargar imagen fresca</b> "
                "para obtener la ultima imagen GOES-19.<br><br>"
                "Se descargaran 4 bandas infrarrojas (~100 MB) desde AWS S3 "
                "y se generara automaticamente el composite Ash RGB, "
                "el mapa BTD split-window y el mapa de confianza."
            )
        with col_right:
            st.markdown("**Interpretacion Ash RGB**")
            ash_legend()
        return

    # ── Timestamp y KPIs ──
    ts_label = data.get("timestamp", "—")
    btd_arr = data.get("btd", np.array([]))
    conf_arr = data.get("ash_confidence", np.array([]))

    valid = ~np.isnan(btd_arr) if btd_arr.size else np.array([])
    ash_px = int(np.sum(btd_arr[valid] < -1.0)) if valid.any() else 0
    total_px = int(np.sum(valid)) if valid.any() else 0
    conf_high = int(np.sum(conf_arr == 3)) if conf_arr.size else 0
    conf_med = int(np.sum(conf_arr == 2)) if conf_arr.size else 0

    st.caption(f"Imagen: {ts_label} UTC")

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        kpi_card(f"{total_px:,}", "Pixeles validos")
    with k2:
        kpi_card(f"{ash_px:,}", "Posible ceniza (BTD<-1K)")
    with k3:
        kpi_card(str(conf_high), "Confianza alta")
    with k4:
        kpi_card(str(conf_med), "Confianza media")

    st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

    # ── Tabs de visualizacion ──
    tab1, tab2, tab3 = st.tabs(["Ash RGB", "BTD Split-Window", "Confianza Ceniza"])

    volcanoes = CATALOG

    with tab1:
        col_img, col_legend = st.columns([4, 1])
        with col_img:
            if "ash_rgb" in data:
                fig = _fig_ash_rgb(
                    data["ash_rgb"], data["lat"], data["lon"],
                    f"Ash RGB — {ts_label}", volcanoes,
                )
                st.plotly_chart(fig, use_container_width=True)
        with col_legend:
            st.markdown("**Leyenda**")
            ash_legend()

    with tab2:
        if "btd" in data:
            fig = _fig_btd(data["btd"], data["lat"], data["lon"], volcanoes)
            st.plotly_chart(fig, use_container_width=True)
            if ash_px > 0 and total_px > 0:
                pct = 100 * ash_px / total_px
                st.caption(
                    f"Pixeles con BTD < -1 K: **{ash_px:,}** de {total_px:,} ({pct:.3f}%)"
                )

    with tab3:
        if "ash_confidence" in data:
            fig = _fig_confidence(data["ash_confidence"], data["lat"], data["lon"], volcanoes)
            st.plotly_chart(fig, use_container_width=True)
