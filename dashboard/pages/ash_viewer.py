"""Página Ash RGB Viewer: Visualización de ceniza volcánica y SO2."""

import logging
from datetime import datetime, timedelta, timezone

import numpy as np
import plotly.graph_objects as go
import streamlit as st

from src.config import CHILE_BOUNDS, VOLCANIC_ZONES
from src.process.pipeline import (
    get_latest_processed,
    load_processed,
    process_ash_rgb,
)
from src.volcanos import CATALOG, get_by_zone, get_priority

logger = logging.getLogger(__name__)


def _create_ash_rgb_figure(rgb: np.ndarray, lat: np.ndarray, lon: np.ndarray,
                           title: str, volcanoes=None) -> go.Figure:
    """Crear figura Plotly con Ash RGB y volcanes superpuestos."""
    fig = go.Figure()

    # Ash RGB como imagen
    # Convertir a uint8 para plotly
    img_uint8 = (np.clip(rgb, 0, 1) * 255).astype(np.uint8)

    fig.add_trace(go.Image(
        z=img_uint8,
        x0=lon.min(),
        dx=(lon.max() - lon.min()) / rgb.shape[1],
        y0=lat.max(),
        dy=-(lat.max() - lat.min()) / rgb.shape[0],
    ))

    # Superponer volcanes
    if volcanoes:
        # Filtrar volcanes dentro del bounds de la imagen
        v_in_bounds = [
            v for v in volcanoes
            if lat.min() <= v.lat <= lat.max() and lon.min() <= v.lon <= lon.max()
        ]
        if v_in_bounds:
            fig.add_trace(go.Scatter(
                x=[v.lon for v in v_in_bounds],
                y=[v.lat for v in v_in_bounds],
                mode="markers+text",
                marker=dict(size=8, color="cyan", symbol="triangle-up", line=dict(width=1, color="white")),
                text=[v.name for v in v_in_bounds],
                textposition="top center",
                textfont=dict(size=9, color="white"),
                name="Volcanes",
                hovertext=[f"{v.name} ({v.elevation}m)" for v in v_in_bounds],
            ))

    fig.update_layout(
        title=title,
        xaxis_title="Longitud",
        yaxis_title="Latitud",
        height=700,
        template="plotly_dark",
        yaxis=dict(scaleanchor="x", scaleratio=1),
        showlegend=True,
    )

    return fig


def _create_btd_figure(btd: np.ndarray, lat: np.ndarray, lon: np.ndarray,
                        volcanoes=None) -> go.Figure:
    """Crear heatmap de BTD split-window."""
    fig = go.Figure()

    fig.add_trace(go.Heatmap(
        z=btd,
        x=np.linspace(lon.min(), lon.max(), btd.shape[1]),
        y=np.linspace(lat.max(), lat.min(), btd.shape[0]),
        colorscale=[
            [0.0, "red"],       # BTD muy negativo = ceniza
            [0.3, "yellow"],    # BTD ligeramente negativo
            [0.5, "white"],     # BTD = 0
            [0.7, "lightblue"], # BTD positivo
            [1.0, "blue"],      # BTD muy positivo = nubes meteorológicas
        ],
        zmin=-5,
        zmax=5,
        colorbar=dict(title="BTD (K)", ticksuffix=" K"),
        hovertemplate="Lat: %{y:.2f}<br>Lon: %{x:.2f}<br>BTD: %{z:.2f} K<extra></extra>",
    ))

    # Volcanes
    if volcanoes:
        v_in = [v for v in volcanoes
                if lat.min() <= v.lat <= lat.max() and lon.min() <= v.lon <= lon.max()]
        if v_in:
            fig.add_trace(go.Scatter(
                x=[v.lon for v in v_in],
                y=[v.lat for v in v_in],
                mode="markers",
                marker=dict(size=7, color="lime", symbol="triangle-up",
                            line=dict(width=1, color="black")),
                text=[v.name for v in v_in],
                hovertemplate="%{text}<extra></extra>",
                name="Volcanes",
            ))

    fig.update_layout(
        title="BTD Split-Window (11.2 - 12.3 um) | Rojo = posible ceniza",
        xaxis_title="Longitud",
        yaxis_title="Latitud",
        height=700,
        template="plotly_dark",
        yaxis=dict(scaleanchor="x", scaleratio=1),
    )

    return fig


def _create_confidence_figure(conf: np.ndarray, lat: np.ndarray, lon: np.ndarray,
                               volcanoes=None) -> go.Figure:
    """Crear mapa de confianza de detección de ceniza."""
    fig = go.Figure()

    fig.add_trace(go.Heatmap(
        z=conf,
        x=np.linspace(lon.min(), lon.max(), conf.shape[1]),
        y=np.linspace(lat.max(), lat.min(), conf.shape[0]),
        colorscale=[
            [0.0, "rgba(0,0,0,0)"],   # 0 = sin ceniza (transparente)
            [0.33, "#fee08b"],          # 1 = baja confianza
            [0.66, "#fc8d59"],          # 2 = media confianza
            [1.0, "#d73027"],           # 3 = alta confianza
        ],
        zmin=0,
        zmax=3,
        colorbar=dict(
            title="Confianza",
            tickvals=[0, 1, 2, 3],
            ticktext=["Ninguna", "Baja", "Media", "Alta"],
        ),
    ))

    if volcanoes:
        v_in = [v for v in volcanoes
                if lat.min() <= v.lat <= lat.max() and lon.min() <= v.lon <= lon.max()]
        if v_in:
            fig.add_trace(go.Scatter(
                x=[v.lon for v in v_in],
                y=[v.lat for v in v_in],
                mode="markers+text",
                marker=dict(size=7, color="cyan", symbol="triangle-up"),
                text=[v.name for v in v_in],
                textposition="top center",
                textfont=dict(size=8, color="white"),
                name="Volcanes",
            ))

    fig.update_layout(
        title="Confianza Detección de Ceniza (0=ninguna, 3=alta)",
        xaxis_title="Longitud",
        yaxis_title="Latitud",
        height=700,
        template="plotly_dark",
        yaxis=dict(scaleanchor="x", scaleratio=1),
    )

    return fig


def render():
    st.title("Ash RGB Viewer - GOES-19")
    st.markdown(
        "**Rojo/Magenta** = ceniza volcánica | "
        "**Verde brillante** = SO2 | "
        "**Amarillo** = mezcla ceniza+SO2"
    )

    # ── Controles ──
    col1, col2, col3 = st.columns([1, 1, 1])

    with col1:
        zone = st.selectbox(
            "Zona",
            ["Chile completo", "norte", "centro", "sur", "austral"],
            index=0,
        )

    with col2:
        use_cached = st.checkbox("Usar datos en caché", value=True)

    with col3:
        fetch_new = st.button("Descargar datos frescos", type="primary")

    # Determinar bounds
    if zone == "Chile completo":
        bounds = CHILE_BOUNDS
    else:
        bounds = VOLCANIC_ZONES[zone]

    # ── Procesar datos ──
    data = None

    if fetch_new:
        with st.spinner("Descargando bandas GOES-19 desde AWS S3... (~100 MB, puede tomar 1-2 min)"):
            try:
                now = datetime.now(timezone.utc)
                # Ir 30 min atrás para asegurar disponibilidad
                dt = now - timedelta(minutes=30)
                dt = dt.replace(minute=(dt.minute // 10) * 10, second=0, microsecond=0)

                data = process_ash_rgb(dt, bounds=bounds, save=True)
                st.success(f"Procesado: {data['timestamp']}")
            except Exception as e:
                st.error(f"Error: {e}")
                logger.exception("Error processing ash RGB")

    elif use_cached:
        info = get_latest_processed()
        if info:
            try:
                data = load_processed(info)
                st.info(f"Mostrando datos en caché: {data['timestamp']}")
            except Exception as e:
                st.warning(f"Error cargando caché: {e}")
        else:
            st.info(
                "No hay datos en caché. Presiona **Descargar datos frescos** "
                "para obtener la imagen más reciente."
            )

    if data is None:
        # Mostrar placeholder con instrucciones
        st.markdown("""
        ### Cómo usar

        1. Presiona **Descargar datos frescos** para obtener la última imagen GOES-19
        2. Se descargarán 4 bandas IR (~100 MB total) desde AWS S3
        3. Se generará automáticamente:
           - **Ash RGB**: composite que muestra ceniza (rojo) y SO2 (verde)
           - **BTD Split-Window**: diferencia de temperatura para detectar ceniza
           - **Mapa de confianza**: niveles 0-3 de detección de ceniza

        ### Interpretación Ash RGB

        | Color | Significado |
        |-------|------------|
        | Rojo / Magenta | Ceniza volcánica |
        | Verde brillante | SO2 |
        | Amarillo | Mezcla ceniza + SO2 |
        | Azul pálido | Superficie terrestre |
        | Marrón | Nubes meteorológicas |
        """)
        return

    # ── Visualización ──
    volcanoes = CATALOG

    tab1, tab2, tab3 = st.tabs(["Ash RGB", "BTD Split-Window", "Confianza Ceniza"])

    with tab1:
        if "ash_rgb" in data:
            fig = _create_ash_rgb_figure(
                data["ash_rgb"], data["lat"], data["lon"],
                f"Ash RGB - {data['timestamp']}", volcanoes,
            )
            st.plotly_chart(fig, use_container_width=True)

    with tab2:
        if "btd" in data:
            fig = _create_btd_figure(
                data["btd"], data["lat"], data["lon"], volcanoes,
            )
            st.plotly_chart(fig, use_container_width=True)

            # Stats
            btd_arr = data["btd"]
            valid = ~np.isnan(btd_arr)
            if valid.any():
                ash_pixels = np.sum(btd_arr[valid] < -1.0)
                total_pixels = np.sum(valid)
                st.markdown(
                    f"**Pixeles con BTD < -1 K (posible ceniza):** {ash_pixels:,} "
                    f"de {total_pixels:,} ({100*ash_pixels/total_pixels:.2f}%)"
                )

    with tab3:
        if "ash_confidence" in data:
            fig = _create_confidence_figure(
                data["ash_confidence"], data["lat"], data["lon"], volcanoes,
            )
            st.plotly_chart(fig, use_container_width=True)

            # Resumen por nivel
            conf = data["ash_confidence"]
            for level, name, color in [(3, "Alta", "red"), (2, "Media", "orange"), (1, "Baja", "yellow")]:
                count = np.sum(conf == level)
                if count > 0:
                    st.markdown(f":{color}[**Confianza {name}:** {count:,} pixeles]")
