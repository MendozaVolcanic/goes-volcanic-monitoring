"""Pagina Detalle Volcan: vista zoom de un volcan especifico."""

from datetime import datetime, timedelta, timezone

import numpy as np
import plotly.graph_objects as go
import streamlit as st

from dashboard.style import (
    BTD_COLORSCALE, C_ACCENT, C_ASH, C_SO2,
    header, info_panel, kpi_card,
)
from src.process.pipeline import process_ash_rgb
from src.volcanos import CATALOG, PRIORITY_VOLCANOES, get_volcano


def _volcano_info_card(v):
    is_priority = v.name in PRIORITY_VOLCANOES
    badge = (
        '<span style="background:rgba(204,51,17,0.15); color:#CC3311; '
        'padding:2px 8px; border-radius:12px; font-size:0.7rem; '
        'font-weight:600; margin-left:8px;">PRIORITARIO</span>'
        if is_priority else ""
    )
    st.markdown(f"""
    <div class="volcano-card">
        <h3>{v.name}{badge}</h3>
        <div class="detail">
            <b>Elevacion:</b> {v.elevation:,} m &nbsp;&middot;&nbsp;
            <b>Zona:</b> {v.zone.title()} &nbsp;&middot;&nbsp;
            <b>Region:</b> {v.region}<br>
            <b>Coords:</b> {v.lat:.3f}, {v.lon:.3f} &nbsp;&middot;&nbsp;
            <b>Ranking:</b> {f'#{v.ranking}' if v.ranking else '—'}
        </div>
    </div>
    """, unsafe_allow_html=True)


def _base_layout(title, height=580):
    return dict(
        title=dict(text=title, font=dict(size=13, color="#ccc")),
        xaxis_title="Longitud", yaxis_title="Latitud",
        height=height, template="plotly_dark",
        yaxis=dict(scaleanchor="x", scaleratio=1),
        margin=dict(t=40, b=35, l=50, r=20),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    )


def render():
    header(
        "Detalle de Volcan",
        "Ash RGB y BTD centrado en un volcan — datos GOES-19 en tiempo casi-real",
    )

    # ── Selector ──
    col_sel, col_roi = st.columns([3, 1])

    with col_sel:
        priority_names = [f"★ {v.name}" for v in CATALOG if v.name in PRIORITY_VOLCANOES]
        other_names = [v.name for v in CATALOG if v.name not in PRIORITY_VOLCANOES]
        all_names = priority_names + other_names
        selected = st.selectbox("Seleccionar volcan", all_names, index=0)
        clean_name = selected.replace("★ ", "")

    volcano = get_volcano(clean_name)
    if volcano is None:
        st.error(f"Volcan '{clean_name}' no encontrado")
        return

    with col_roi:
        roi_size = st.slider("ROI (grados)", 0.5, 5.0, 2.0, 0.5)

    _volcano_info_card(volcano)

    bounds = {
        "lat_min": volcano.lat - roi_size,
        "lat_max": volcano.lat + roi_size,
        "lon_min": volcano.lon - roi_size,
        "lon_max": volcano.lon + roi_size,
    }

    st.markdown("<div style='height:0.2rem'></div>", unsafe_allow_html=True)
    fetch = st.button(
        f"Descargar imagen para {volcano.name}",
        type="primary",
    )

    if not fetch:
        info_panel(
            f"Presiona el boton para descargar la imagen GOES-19 mas reciente "
            f"centrada en <b>{volcano.name}</b> (ROI {roi_size*2:.0f}° x {roi_size*2:.0f}°)."
        )
        return

    with st.spinner(f"Descargando GOES-19 para {volcano.name}..."):
        try:
            now = datetime.now(timezone.utc)
            dt = now - timedelta(minutes=30)
            dt = dt.replace(minute=(dt.minute // 10) * 10, second=0, microsecond=0)
            data = process_ash_rgb(dt, bounds=bounds, save=False)
        except Exception as e:
            st.error(f"Error: {e}")
            return

    # ── Analisis ──
    btd = data["btd"]
    conf = data["ash_confidence"]
    valid_btd = btd[~np.isnan(btd)]
    ash_px = int(np.sum(valid_btd < -1))
    conf_hi = int(np.sum(conf == 3))

    # Titulo insight
    if conf_hi > 5:
        insight = f"Ceniza detectada cerca de {volcano.name} — {conf_hi} pixeles confianza alta"
    elif ash_px > 10:
        insight = f"{ash_px} pixeles con posible ceniza en el entorno de {volcano.name}"
    else:
        insight = f"Sin ceniza detectada en el entorno de {volcano.name}"

    detail_status = "ok" if ash_px == 0 else ("alert" if conf_hi > 5 else "warn")
    status_icon = "&#10003;" if ash_px == 0 else "&#9888;"
    st.markdown(
        f'<div class="status-banner {detail_status}">'
        f'<b>{status_icon} {insight}</b>'
        f'<span style="color:#556677; font-size:0.78rem;">{data["timestamp"]}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # ── KPIs ──
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        kpi_card(f"{np.nanmin(btd):.1f}", "BTD min (K)")
    with k2:
        kpi_card(f"{np.nanmean(valid_btd):.1f}", "BTD medio (K)")
    with k3:
        kpi_card(str(ash_px), "Pixeles ceniza",
                 delta="BTD < -1K", delta_type="negative" if ash_px > 0 else "neutral")
    with k4:
        kpi_card(str(conf_hi), "Confianza alta",
                 delta_type="negative" if conf_hi > 0 else "neutral")

    st.markdown("<div style='height:0.3rem'></div>", unsafe_allow_html=True)

    # ── Graficos ──
    tab1, tab2 = st.tabs(["Ash RGB", "BTD Split-Window"])

    volcano_marker = dict(
        x=[volcano.lon], y=[volcano.lat],
        mode="markers+text",
        marker=dict(size=13, color=C_ACCENT, symbol="triangle-up",
                    line=dict(width=2, color="white")),
        text=[volcano.name],
        textposition="top center",
        textfont=dict(size=11, color="white"),
        name=volcano.name,
    )

    with tab1:
        img = (np.clip(data["ash_rgb"], 0, 1) * 255).astype(np.uint8)
        fig = go.Figure()
        fig.add_trace(go.Image(
            z=img,
            x0=float(data["lon"].min()),
            dx=(float(data["lon"].max()) - float(data["lon"].min())) / data["ash_rgb"].shape[1],
            y0=float(data["lat"].max()),
            dy=-(float(data["lat"].max()) - float(data["lat"].min())) / data["ash_rgb"].shape[0],
        ))
        fig.add_trace(go.Scatter(**volcano_marker))
        fig.update_layout(**_base_layout(f"Ash RGB — {volcano.name}"))
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        fig2 = go.Figure()
        fig2.add_trace(go.Heatmap(
            z=btd[::-1, :],
            x=np.linspace(float(data["lon"].min()), float(data["lon"].max()), btd.shape[1]),
            y=np.linspace(float(data["lat"].min()), float(data["lat"].max()), btd.shape[0]),
            colorscale=BTD_COLORSCALE,
            zmin=-5, zmax=5,
            colorbar=dict(title="K", thickness=12, len=0.6),
        ))
        fig2.add_trace(go.Scatter(**volcano_marker))
        btd_title = f"BTD — {ash_px} pixeles bajo umbral ceniza (-1K)" if ash_px else f"BTD — sin ceniza detectada"
        fig2.update_layout(**_base_layout(btd_title))
        st.plotly_chart(fig2, use_container_width=True)
