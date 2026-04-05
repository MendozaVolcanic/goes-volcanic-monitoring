"""Pagina Detalle Volcan: vista zoom de un volcan especifico."""

from datetime import datetime, timedelta, timezone

import numpy as np
import plotly.graph_objects as go
import streamlit as st

from dashboard.style import header, kpi_card, info_panel
from src.process.pipeline import process_ash_rgb
from src.volcanos import CATALOG, PRIORITY_VOLCANOES, get_volcano


ZONE_LABELS = {
    "norte": "Norte",
    "centro": "Centro",
    "sur": "Sur",
    "austral": "Austral",
}


def _volcano_info_card(v):
    """Renderizar card con informacion del volcan."""
    is_priority = v.name in PRIORITY_VOLCANOES
    badge = (
        '<span style="background:rgba(231,76,60,0.2); color:#e74c3c; '
        'padding:2px 8px; border-radius:12px; font-size:0.7rem; '
        'font-weight:600; margin-left:8px;">PRIORITARIO</span>'
        if is_priority else ""
    )
    ranking_text = f"#{v.ranking}" if v.ranking else "—"

    st.markdown(f"""
    <div class="volcano-card">
        <h3>{v.name}{badge}</h3>
        <div class="detail">
            <b>Elevacion:</b> {v.elevation:,} m &nbsp;|&nbsp;
            <b>Zona:</b> {ZONE_LABELS.get(v.zone, v.zone)} &nbsp;|&nbsp;
            <b>Region:</b> {v.region}<br>
            <b>Coordenadas:</b> {v.lat:.3f}°S, {abs(v.lon):.3f}°W &nbsp;|&nbsp;
            <b>Ranking SERNAGEOMIN:</b> {ranking_text}
        </div>
    </div>
    """, unsafe_allow_html=True)


def render():
    header(
        "Detalle de Volcan",
        "Ash RGB y deteccion de ceniza centrada en un volcan especifico",
    )

    # ── Selector ──
    col_sel, col_roi = st.columns([3, 1])

    with col_sel:
        priority_names = [f"⭐ {v.name}" for v in CATALOG if v.name in PRIORITY_VOLCANOES]
        other_names = [v.name for v in CATALOG if v.name not in PRIORITY_VOLCANOES]
        all_names = priority_names + other_names

        selected = st.selectbox("Seleccionar volcan", all_names, index=0)
        # Limpiar prefijo estrella
        clean_name = selected.replace("⭐ ", "")

    volcano = get_volcano(clean_name)
    if volcano is None:
        st.error(f"Volcan '{clean_name}' no encontrado")
        return

    with col_roi:
        roi_size = st.slider("ROI (grados)", 0.5, 5.0, 2.0, 0.5)

    # ── Info card ──
    _volcano_info_card(volcano)

    # ── Bounds ──
    bounds = {
        "lat_min": volcano.lat - roi_size,
        "lat_max": volcano.lat + roi_size,
        "lon_min": volcano.lon - roi_size,
        "lon_max": volcano.lon + roi_size,
    }

    # ── Botón descarga ──
    st.markdown("<div style='height:0.3rem'></div>", unsafe_allow_html=True)
    fetch = st.button(
        f"Descargar Ash RGB para {volcano.name}",
        type="primary",
        use_container_width=False,
    )

    if not fetch:
        info_panel(
            f"Presiona el boton para descargar la imagen GOES-19 mas reciente "
            f"centrada en <b>{volcano.name}</b> ({roi_size*2:.0f}° x {roi_size*2:.0f}°)."
            f"<br>Se generara Ash RGB, BTD split-window y estadisticas del area."
        )
        return

    # ── Procesar ──
    with st.spinner(f"Descargando GOES-19 para {volcano.name}..."):
        try:
            now = datetime.now(timezone.utc)
            dt = now - timedelta(minutes=30)
            dt = dt.replace(minute=(dt.minute // 10) * 10, second=0, microsecond=0)
            data = process_ash_rgb(dt, bounds=bounds, save=False)
        except Exception as e:
            st.error(f"Error: {e}")
            return

    st.toast(f"Procesado: {data['timestamp']}", icon="✅")

    # ── KPIs ──
    btd = data["btd"]
    conf = data["ash_confidence"]
    valid_btd = btd[~np.isnan(btd)]

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        kpi_card(f"{np.nanmin(btd):.1f} K", "BTD minimo")
    with k2:
        kpi_card(f"{np.nanmean(valid_btd):.1f} K", "BTD medio")
    with k3:
        kpi_card(str(int(np.sum(valid_btd < -1))), "Pixeles ceniza")
    with k4:
        kpi_card(str(int(np.sum(conf == 3))), "Confianza alta")

    st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

    # ── Ash RGB + BTD side by side ──
    tab1, tab2 = st.tabs(["Ash RGB", "BTD Split-Window"])

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
        fig.add_trace(go.Scatter(
            x=[volcano.lon], y=[volcano.lat],
            mode="markers+text",
            marker=dict(size=14, color="#00fff7", symbol="triangle-up",
                        line=dict(width=2, color="white")),
            text=[volcano.name],
            textposition="top center",
            textfont=dict(size=12, color="white"),
            name=volcano.name,
        ))
        fig.update_layout(
            title=dict(text=f"Ash RGB — {volcano.name} — {data['timestamp']}",
                       font=dict(size=14)),
            xaxis_title="Longitud", yaxis_title="Latitud",
            height=600, template="plotly_dark",
            yaxis=dict(scaleanchor="x", scaleratio=1),
            margin=dict(t=40, b=40, l=50, r=20),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        fig2 = go.Figure()
        fig2.add_trace(go.Heatmap(
            z=btd,
            x=np.linspace(float(data["lon"].min()), float(data["lon"].max()), btd.shape[1]),
            y=np.linspace(float(data["lat"].max()), float(data["lat"].min()), btd.shape[0]),
            colorscale=[
                [0.0, "#b71c1c"], [0.2, "#e53935"], [0.4, "#ffca28"],
                [0.5, "#fafafa"], [0.6, "#81d4fa"], [0.8, "#1565c0"], [1.0, "#0d47a1"],
            ],
            zmin=-5, zmax=5,
            colorbar=dict(title="BTD (K)", thickness=15),
        ))
        fig2.add_trace(go.Scatter(
            x=[volcano.lon], y=[volcano.lat],
            mode="markers",
            marker=dict(size=12, color="#00ff88", symbol="triangle-up",
                        line=dict(width=2, color="#000")),
            name=volcano.name,
        ))
        fig2.update_layout(
            title=dict(text=f"BTD (11.2 - 12.3 um) — {volcano.name}",
                       font=dict(size=14)),
            height=600, template="plotly_dark",
            yaxis=dict(scaleanchor="x", scaleratio=1),
            margin=dict(t=40, b=40, l=50, r=20),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig2, use_container_width=True)
