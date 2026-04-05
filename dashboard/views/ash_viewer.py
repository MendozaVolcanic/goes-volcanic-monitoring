"""Pagina Ash RGB Viewer: visualizacion de ceniza volcanica y SO2."""

import logging
from datetime import datetime, timedelta, timezone

import numpy as np
import plotly.graph_objects as go
import streamlit as st

from dashboard.style import (
    BTD_COLORSCALE, CONF_COLORSCALE, SO2_COLORSCALE,
    C_ACCENT, C_ASH, C_SO2,
    ash_legend, ash_so2_legend, btd_legend, so2_legend,
    header, info_panel, kpi_card,
)
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


def _volcano_markers(fig, lat, lon, volcanoes):
    """Agregar marcadores de volcanes al grafico."""
    vis = [v for v in volcanoes
           if lat.min() <= v.lat <= lat.max() and lon.min() <= v.lon <= lon.max()]
    if not vis:
        return
    fig.add_trace(go.Scatter(
        x=[v.lon for v in vis], y=[v.lat for v in vis],
        mode="markers+text",
        marker=dict(size=6, color=C_ACCENT, symbol="triangle-up",
                    line=dict(width=0.8, color="white")),
        text=[v.name for v in vis],
        textposition="top center",
        textfont=dict(size=8, color="rgba(255,255,255,0.7)"),
        name="Volcanes",
        hovertext=[f"{v.name} ({v.elevation:,} m)" for v in vis],
        hoverinfo="text",
    ))


def _base_layout(title, height=680):
    return dict(
        title=dict(text=title, font=dict(size=14, color="#ccc")),
        xaxis_title="Longitud", yaxis_title="Latitud",
        height=height, template="plotly_dark",
        yaxis=dict(scaleanchor="x", scaleratio=1),
        margin=dict(t=45, b=40, l=50, r=20),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    )


def _fig_ash_rgb(rgb, lat, lon, insight_title, volcanoes):
    img = (np.clip(rgb, 0, 1) * 255).astype(np.uint8)
    fig = go.Figure()
    fig.add_trace(go.Image(
        z=img,
        x0=float(lon.min()), dx=(float(lon.max()) - float(lon.min())) / rgb.shape[1],
        y0=float(lat.max()), dy=-(float(lat.max()) - float(lat.min())) / rgb.shape[0],
    ))
    _volcano_markers(fig, lat, lon, volcanoes)
    fig.update_layout(**_base_layout(insight_title))
    return fig


def _fig_btd(btd, lat, lon, insight_title, volcanoes):
    fig = go.Figure()
    # Flip z verticalmente y usar y creciente para evitar auto-reverse de Plotly
    fig.add_trace(go.Heatmap(
        z=btd[::-1, :],
        x=np.linspace(float(lon.min()), float(lon.max()), btd.shape[1]),
        y=np.linspace(float(lat.min()), float(lat.max()), btd.shape[0]),
        colorscale=BTD_COLORSCALE,
        zmin=-5, zmax=5,
        colorbar=dict(title="K", thickness=12, len=0.6,
                      tickvals=[-4, -2, -1, 0, 2, 4],
                      ticktext=["-4", "-2", "-1", "0", "2", "4"]),
        hovertemplate="(%{x:.2f}, %{y:.2f})<br>BTD: %{z:.2f} K<extra></extra>",
    ))
    _volcano_markers(fig, lat, lon, volcanoes)
    fig.update_layout(**_base_layout(insight_title))
    return fig


def _fig_confidence(conf, lat, lon, insight_title, volcanoes):
    fig = go.Figure()
    fig.add_trace(go.Heatmap(
        z=conf[::-1, :],
        x=np.linspace(float(lon.min()), float(lon.max()), conf.shape[1]),
        y=np.linspace(float(lat.min()), float(lat.max()), conf.shape[0]),
        colorscale=CONF_COLORSCALE,
        zmin=0, zmax=3,
        colorbar=dict(
            title="Nivel", thickness=12, len=0.6,
            tickvals=[0, 1, 2, 3],
            ticktext=["—", "Baja", "Media", "Alta"],
        ),
    ))
    _volcano_markers(fig, lat, lon, volcanoes)
    fig.update_layout(**_base_layout(insight_title))
    return fig


def _fig_so2(so2, lat, lon, insight_title, volcanoes):
    fig = go.Figure()
    # Invertir SO2 para colorscale: más negativo = más SO2 = color más intenso
    so2_display = -so2  # flip sign so higher = more SO2
    fig.add_trace(go.Heatmap(
        z=so2_display[::-1, :],
        x=np.linspace(float(lon.min()), float(lon.max()), so2.shape[1]),
        y=np.linspace(float(lat.min()), float(lat.max()), so2.shape[0]),
        colorscale=SO2_COLORSCALE,
        zmin=-1, zmax=8,
        colorbar=dict(
            title="K", thickness=12, len=0.6,
            tickvals=[0, 3, 5, 8],
            ticktext=["0", "-3", "-5", "-8"],
        ),
        hovertemplate="(%{x:.2f}, %{y:.2f})<br>SO2 index: -%{z:.1f} K<extra></extra>",
    ))
    _volcano_markers(fig, lat, lon, volcanoes)
    fig.update_layout(**_base_layout(insight_title))
    return fig


def _compute_insight(btd_arr, conf_arr):
    """Generar titulo-insight basado en los datos (no descripcion generica)."""
    valid = ~np.isnan(btd_arr)
    ash_px = int(np.sum(btd_arr[valid] < -1.0)) if valid.any() else 0
    total_px = int(np.sum(valid)) if valid.any() else 0
    conf_high = int(np.sum(conf_arr == 3)) if conf_arr.size else 0

    if conf_high > 50:
        return f"Ceniza detectada — {conf_high:,} pixeles con confianza alta", "alert"
    if ash_px > 100:
        return f"{ash_px:,} pixeles con posible ceniza (BTD < -1K)", "warn"
    if ash_px > 0:
        return f"Sin actividad significativa — {ash_px} pixeles con BTD < -1K", "ok"
    return "Sin deteccion de ceniza en la region", "ok"


def render():
    header(
        "Ash RGB Viewer",
        "Deteccion de ceniza volcanica y SO2 desde GOES-19 (bandas 11, 13, 14, 15)",
    )

    # ── Controles ──
    c1, c2, c3 = st.columns([1.5, 1, 1])
    with c1:
        zone_key = st.selectbox("Region", list(ZONE_OPTIONS.keys()), index=0)
    with c2:
        use_cached = st.checkbox("Usar cache", value=True)
    with c3:
        st.markdown("<div style='height:1.6rem'></div>", unsafe_allow_html=True)
        fetch_new = st.button("Descargar imagen fresca", type="primary",
                              use_container_width=True)

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
    elif use_cached:
        info = get_latest_processed()
        if info:
            try:
                data = load_processed(info)
            except Exception as e:
                st.warning(f"Error cargando cache: {e}")

    # ── Sin datos ──
    if data is None:
        col_l, col_r = st.columns([2, 1])
        with col_l:
            info_panel(
                "<b>Sin datos en cache.</b> Presiona <b>Descargar imagen fresca</b> "
                "para obtener la ultima imagen GOES-19.<br><br>"
                "Se descargaran 4 bandas IR (~100 MB) y se generaran 3 productos: "
                "Ash RGB, BTD split-window y mapa de confianza."
            )
        with col_r:
            ash_legend()
        return

    # ── Analizar datos → titulo insight ──
    btd_arr = data.get("btd", np.array([]))
    conf_arr = data.get("ash_confidence", np.array([]))
    insight_text, status = _compute_insight(btd_arr, conf_arr)

    valid = ~np.isnan(btd_arr) if btd_arr.size else np.array([])
    ash_px = int(np.sum(btd_arr[valid] < -1.0)) if valid.any() else 0
    total_px = int(np.sum(valid)) if valid.any() else 0
    conf_high = int(np.sum(conf_arr == 3)) if conf_arr.size else 0
    conf_med = int(np.sum(conf_arr == 2)) if conf_arr.size else 0
    pct = f"{100*ash_px/total_px:.3f}%" if total_px else "—"

    # Status banner
    status_icons = {"ok": "&#10003;", "warn": "&#9888;", "alert": "&#9888;"}
    st.markdown(
        f'<div class="status-banner {status}">'
        f'<b>{status_icons[status]} {insight_text}</b>'
        f'<span style="color:#556677; font-size:0.78rem;">{data.get("timestamp","")}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # ── KPIs ──
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        kpi_card(f"{total_px:,}", "Pixeles validos")
    with k2:
        kpi_card(f"{ash_px:,}", "BTD < -1K", delta=pct, delta_type="negative" if ash_px > 50 else "neutral")
    with k3:
        kpi_card(str(conf_high), "Confianza alta", delta_type="negative" if conf_high > 0 else "neutral")
    with k4:
        kpi_card(str(conf_med), "Confianza media")

    st.markdown("<div style='height:0.4rem'></div>", unsafe_allow_html=True)

    # ── SO2 stats ──
    so2_arr = data.get("so2", np.array([]))
    so2_px = 0
    if so2_arr.size:
        valid_so2 = ~np.isnan(so2_arr)
        so2_px = int(np.sum(so2_arr[valid_so2] < -3.0)) if valid_so2.any() else 0

    # ── Tabs ──
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Ash RGB", "Ash/SO2 RGB", "BTD Split-Window", "SO2", "Confianza",
    ])

    with tab1:
        col_img, col_leg = st.columns([5, 1.2])
        with col_img:
            if "ash_rgb" in data:
                fig = _fig_ash_rgb(
                    data["ash_rgb"], data["lat"], data["lon"],
                    insight_text, CATALOG,
                )
                st.plotly_chart(fig, use_container_width=True)
        with col_leg:
            ash_legend()

    with tab2:
        col_img2a, col_leg2a = st.columns([5, 1.2])
        with col_img2a:
            if "ash_so2_rgb" in data:
                so2_title = (
                    f"{so2_px} pixeles con SO2 probable (BTD < -3K)"
                    if so2_px > 0
                    else "Sin deteccion de SO2 — imagen Ash/SO2 RGB"
                )
                fig = _fig_ash_rgb(
                    data["ash_so2_rgb"], data["lat"], data["lon"],
                    so2_title, CATALOG,
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                info_panel("Producto Ash/SO2 RGB no disponible en cache. Descarga una imagen fresca.")
        with col_leg2a:
            ash_so2_legend()

    with tab3:
        col_img3, col_leg3 = st.columns([5, 1.2])
        with col_img3:
            if btd_arr.size:
                btd_title = f"{ash_px:,} pixeles con BTD negativo — umbral ceniza: -1 K"
                fig = _fig_btd(btd_arr, data["lat"], data["lon"], btd_title, CATALOG)
                st.plotly_chart(fig, use_container_width=True)
        with col_leg3:
            btd_legend()

    with tab4:
        col_img4, col_leg4 = st.columns([5, 1.2])
        with col_img4:
            if so2_arr.size:
                so2_map_title = (
                    f"{so2_px} pixeles con SO2 (BTD 8.4-11.2 < -3K)"
                    if so2_px > 0
                    else "Sin deteccion de SO2 en la region"
                )
                fig = _fig_so2(so2_arr, data["lat"], data["lon"], so2_map_title, CATALOG)
                st.plotly_chart(fig, use_container_width=True)
            else:
                info_panel("Datos SO2 no disponibles. Descarga una imagen fresca.")
        with col_leg4:
            so2_legend()

    with tab5:
        if conf_arr.size:
            conf_title = (
                f"Ceniza confirmada en {conf_high} pixeles"
                if conf_high > 0
                else "Sin detecciones de confianza alta"
            )
            fig = _fig_confidence(conf_arr, data["lat"], data["lon"], conf_title, CATALOG)
            st.plotly_chart(fig, use_container_width=True)
