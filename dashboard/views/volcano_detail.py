"""Página Detalle Volcán: Vista zoom de un volcán específico."""

from datetime import datetime, timedelta, timezone

import numpy as np
import plotly.graph_objects as go
import streamlit as st

from src.config import PROCESSED_DIR
from src.process.pipeline import process_ash_rgb
from src.volcanos import CATALOG, PRIORITY_VOLCANOES, get_volcano


def render():
    st.title("Detalle de Volcán")

    # ── Selector de volcán ──
    col1, col2 = st.columns([2, 1])

    with col1:
        # Prioritarios primero, luego el resto
        priority_names = [v.name for v in CATALOG if v.name in PRIORITY_VOLCANOES]
        other_names = [v.name for v in CATALOG if v.name not in PRIORITY_VOLCANOES]
        all_names = priority_names + ["---"] + other_names
        selected = st.selectbox("Seleccionar volcán", all_names, index=0)

    if selected == "---":
        st.info("Selecciona un volcán de la lista")
        return

    volcano = get_volcano(selected)
    if volcano is None:
        st.error(f"Volcán '{selected}' no encontrado")
        return

    with col2:
        roi_size = st.slider("Tamaño ROI (grados)", 0.5, 5.0, 2.0, 0.5)

    # ── Info del volcán ──
    st.markdown(f"""
    **{volcano.name}** | {volcano.elevation} m | {volcano.region} | Zona {volcano.zone}
    | Coords: {volcano.lat:.2f}°S, {abs(volcano.lon):.2f}°W
    | Ranking SERNAGEOMIN: {volcano.ranking if volcano.ranking > 0 else 'Sin ranking'}
    """)

    # ── Bounds centrados en el volcán ──
    bounds = {
        "lat_min": volcano.lat - roi_size,
        "lat_max": volcano.lat + roi_size,
        "lon_min": volcano.lon - roi_size,
        "lon_max": volcano.lon + roi_size,
    }

    # ── Obtener datos ──
    fetch = st.button("Descargar Ash RGB para este volcán", type="primary")

    if fetch:
        with st.spinner(f"Descargando GOES-19 para {volcano.name}..."):
            try:
                now = datetime.now(timezone.utc)
                dt = now - timedelta(minutes=30)
                dt = dt.replace(minute=(dt.minute // 10) * 10, second=0, microsecond=0)

                data = process_ash_rgb(dt, bounds=bounds, save=False)

                # ── Ash RGB ──
                st.subheader("Ash RGB")
                fig = go.Figure()

                img_uint8 = (np.clip(data["ash_rgb"], 0, 1) * 255).astype(np.uint8)
                fig.add_trace(go.Image(
                    z=img_uint8,
                    x0=data["lon"].min(),
                    dx=(data["lon"].max() - data["lon"].min()) / data["ash_rgb"].shape[1],
                    y0=data["lat"].max(),
                    dy=-(data["lat"].max() - data["lat"].min()) / data["ash_rgb"].shape[0],
                ))

                # Marcador del volcán
                fig.add_trace(go.Scatter(
                    x=[volcano.lon],
                    y=[volcano.lat],
                    mode="markers+text",
                    marker=dict(size=12, color="cyan", symbol="triangle-up",
                                line=dict(width=2, color="white")),
                    text=[volcano.name],
                    textposition="top center",
                    textfont=dict(size=12, color="white"),
                    name=volcano.name,
                ))

                fig.update_layout(
                    title=f"Ash RGB - {volcano.name} - {data['timestamp']}",
                    xaxis_title="Longitud",
                    yaxis_title="Latitud",
                    height=600,
                    template="plotly_dark",
                    yaxis=dict(scaleanchor="x", scaleratio=1),
                )
                st.plotly_chart(fig, use_container_width=True)

                # ── BTD ──
                st.subheader("BTD Split-Window")
                btd = data["btd"]
                fig2 = go.Figure()
                fig2.add_trace(go.Heatmap(
                    z=btd,
                    x=np.linspace(data["lon"].min(), data["lon"].max(), btd.shape[1]),
                    y=np.linspace(data["lat"].max(), data["lat"].min(), btd.shape[0]),
                    colorscale="RdBu_r",
                    zmin=-5, zmax=5,
                    colorbar=dict(title="BTD (K)"),
                ))
                fig2.add_trace(go.Scatter(
                    x=[volcano.lon], y=[volcano.lat],
                    mode="markers",
                    marker=dict(size=10, color="lime", symbol="triangle-up"),
                    name=volcano.name,
                ))
                fig2.update_layout(
                    title=f"BTD (11.2-12.3 um) - {volcano.name}",
                    height=600, template="plotly_dark",
                    yaxis=dict(scaleanchor="x", scaleratio=1),
                )
                st.plotly_chart(fig2, use_container_width=True)

                # ── Estadísticas ──
                st.subheader("Estadísticas")
                valid_btd = btd[~np.isnan(btd)]
                conf = data["ash_confidence"]

                c1, c2, c3, c4 = st.columns(4)
                c1.metric("BTD mínimo", f"{np.nanmin(btd):.1f} K")
                c2.metric("BTD medio", f"{np.nanmean(valid_btd):.1f} K")
                c3.metric("Pixeles ceniza (BTD<-1K)", f"{np.sum(valid_btd < -1)}")
                c4.metric("Confianza alta", f"{np.sum(conf == 3)}")

            except Exception as e:
                st.error(f"Error: {e}")
    else:
        st.markdown("""
        Presiona el botón para descargar la imagen GOES-19 más reciente
        centrada en este volcán.

        Se generará:
        - **Ash RGB** zoom al volcán
        - **BTD Split-Window** para detección de ceniza
        - **Estadísticas** del área
        """)
