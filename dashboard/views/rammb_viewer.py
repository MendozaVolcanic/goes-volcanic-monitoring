"""Pagina RAMMB Slider: animacion de imagenes GOES-19 en tiempo real.

Muestra loops animados de los ultimos N scans del satelite GOES-19,
permitiendo observar el movimiento de plumas de ceniza y pulsos eruptivos.

Fuente: slider.cira.colostate.edu (CIRA/CSU + NOAA/RAMMB).
"""

import base64
import io
import logging

import numpy as np
import plotly.graph_objects as go
import streamlit as st
from PIL import Image as PILImage

from dashboard.style import (
    C_ACCENT, C_ASH, C_SO2,
    header, info_panel, kpi_card, refresh_info_badge,
)
from dashboard.utils import fmt_both, fmt_both_long, parse_rammb_ts
from src.config import CHILE_BOUNDS
from src.fetch.rammb_slider import (
    CHILE_REPROJECTED_BOUNDS, CHILE_TILE_BOUNDS, CHILE_TILES_Z2, PRODUCTS,
    fetch_animation_frames, get_latest_timestamps, reproject_to_latlon, ts_to_parts,
)
from src.volcanos import CATALOG, get_priority

logger = logging.getLogger(__name__)

FRAME_OPTIONS = {
    "1 hora (6 frames)": 6,
    "2 horas (12 frames)": 12,
    "3 horas (18 frames)": 18,
}

PRODUCT_LABELS = {
    "geocolor":    "GeoColor",
    "eumetsat_ash": "Ash RGB",
    "jma_so2":     "SO2",
    "split_window_difference_10_3-12_3": "BTD",
}


def _ts_to_display(ts: str) -> str:
    """Timestamp 14-dígitos → 'YYYY-MM-DD HH:MM UTC (HH:MM CLT)'"""
    dt = parse_rammb_ts(ts)
    return fmt_both_long(dt)


def _img_to_b64(arr: np.ndarray) -> str:
    """Numpy array → base64 PNG."""
    buf = io.BytesIO()
    PILImage.fromarray(arr).save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


def _make_volcano_scatter(bounds: dict):
    """Scatter de volcanes prioritarios dentro de los bounds."""
    vis = [v for v in get_priority()
           if bounds["lat_min"] <= v.lat <= bounds["lat_max"]
           and bounds["lon_min"] <= v.lon <= bounds["lon_max"]]
    if not vis:
        vis = [v for v in CATALOG
               if CHILE_BOUNDS["lat_min"] <= v.lat <= CHILE_BOUNDS["lat_max"]
               and CHILE_BOUNDS["lon_min"] <= v.lon <= CHILE_BOUNDS["lon_max"]][:15]
    return go.Scatter(
        x=[v.lon for v in vis],
        y=[v.lat for v in vis],
        mode="markers+text",
        marker=dict(size=7, color=C_ACCENT, symbol="triangle-up",
                    line=dict(width=1, color="white")),
        text=[v.name for v in vis],
        textposition="top center",
        textfont=dict(size=8, color="rgba(255,255,255,0.8)"),
        name="Volcanes",
        hovertext=[f"<b>{v.name}</b><br>{v.elevation:,} m" for v in vis],
        hoverinfo="text",
        showlegend=False,
    )


def _build_animation(frames: list[dict], bounds: dict) -> go.Figure:
    """Construir figura Plotly animada con los frames."""
    lat_min = bounds["lat_min"]
    lat_max = bounds["lat_max"]
    lon_min = bounds["lon_min"]
    lon_max = bounds["lon_max"]

    volc_scatter = _make_volcano_scatter(bounds)

    plotly_frames = []
    for i, f in enumerate(frames):
        b64 = _img_to_b64(f["image"])
        plotly_frames.append(go.Frame(
            data=[
                go.Scatter(x=[lon_min, lon_max], y=[lat_min, lat_max],
                           mode="markers", marker=dict(opacity=0),
                           showlegend=False, hoverinfo="skip"),
                volc_scatter,
            ],
            layout=go.Layout(
                images=[dict(
                    source=f"data:image/png;base64,{b64}",
                    xref="x", yref="y",
                    x=lon_min, y=lat_max,
                    xanchor="left", yanchor="top",
                    sizex=lon_max - lon_min,
                    sizey=lat_max - lat_min,
                    sizing="stretch",
                    layer="below",
                )],
                title_text=f["label"],
            ),
            name=str(i),
        ))

    # Frame inicial
    b64_first = _img_to_b64(frames[0]["image"])
    fig = go.Figure(
        data=[
            go.Scatter(x=[lon_min, lon_max], y=[lat_min, lat_max],
                       mode="markers", marker=dict(opacity=0),
                       showlegend=False, hoverinfo="skip"),
            volc_scatter,
        ],
        layout=go.Layout(
            images=[dict(
                source=f"data:image/png;base64,{b64_first}",
                xref="x", yref="y",
                x=lon_min, y=lat_max,
                xanchor="left", yanchor="top",
                sizex=lon_max - lon_min,
                sizey=lat_max - lat_min,
                sizing="stretch",
                layer="below",
            )],
            title=dict(text=frames[0]["label"], font=dict(size=13, color="#ccc")),
            xaxis_title="Longitud",
            yaxis_title="Latitud",
            yaxis=dict(scaleanchor="x", scaleratio=1,
                       range=[lat_min - 1, lat_max + 1]),
            xaxis=dict(range=[lon_min - 1, lon_max + 1]),
            height=700,
            template="plotly_dark",
            margin=dict(t=60, b=80, l=50, r=20),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            updatemenus=[dict(
                type="buttons",
                showactive=False,
                y=0,
                x=0.5,
                xanchor="center",
                yanchor="top",
                pad=dict(t=10),
                buttons=[
                    dict(
                        label="▶ Play",
                        method="animate",
                        args=[None, dict(
                            frame=dict(duration=800, redraw=True),
                            fromcurrent=True,
                            transition=dict(duration=0),
                        )],
                    ),
                    dict(
                        label="⏸ Pausa",
                        method="animate",
                        args=[[None], dict(
                            frame=dict(duration=0, redraw=False),
                            mode="immediate",
                            transition=dict(duration=0),
                        )],
                    ),
                ],
            )],
            sliders=[dict(
                active=0,
                currentvalue=dict(
                    prefix="Frame: ",
                    font=dict(size=11, color="#aaa"),
                ),
                pad=dict(t=50, b=10),
                steps=[dict(
                    method="animate",
                    args=[[str(i)], dict(
                        frame=dict(duration=0, redraw=True),
                        mode="immediate",
                        transition=dict(duration=0),
                    )],
                    label=f["label"][-8:-4],  # HH:MM
                ) for i, f in enumerate(frames)],
            )],
        ),
        frames=plotly_frames,
    )

    return fig


# Versión de reproyección — cambiar si se modifica cfac/bounds para invalidar caché
_REPROJECT_VERSION = "v2"


@st.cache_data(ttl=600, show_spinner=False)
def _fetch_cached(product: str, n_frames: int, _v: str = _REPROJECT_VERSION) -> list[dict]:
    """Descargar frames con cache de 10 minutos."""
    frames = fetch_animation_frames(
        product=product,
        n_frames=n_frames,
        zoom=2,
        tile_rows=CHILE_TILES_Z2["rows"],
        tile_cols=CHILE_TILES_Z2["cols"],
    )
    for frame in frames:
        frame["image"] = reproject_to_latlon(frame["image"], col_start=678, row_start=1356)
        frame["bounds"] = CHILE_REPROJECTED_BOUNDS
    return frames


@st.cache_data(ttl=300, show_spinner=False)
def _fetch_latest_ts(product: str) -> str:
    """Obtener timestamp más reciente (cache 5 min)."""
    times = get_latest_timestamps(product, n=1)
    return _ts_to_display(times[0]) if times else "—"


def render():
    header(
        "Animacion RAMMB/CIRA — GOES-19 en tiempo real",
        "Loop animado de los ultimos scans &middot; slider.cira.colostate.edu &middot; Full Disk cada 10 min",
    )

    refresh_info_badge(context="animation")

    # ── Controles ──
    c1, c2, c3 = st.columns([1.5, 1.2, 1])
    with c1:
        product = st.selectbox(
            "Producto",
            options=list(PRODUCT_LABELS.keys()),
            format_func=lambda k: PRODUCT_LABELS[k],
            index=0,
            key="rammb_product",
        )
    with c2:
        duration_label = st.selectbox(
            "Duracion del loop",
            options=list(FRAME_OPTIONS.keys()),
            index=1,
            key="rammb_duration",
        )
    with c3:
        st.markdown("<div style='height:1.6rem'></div>", unsafe_allow_html=True)
        fetch_btn = st.button("Cargar animacion", type="primary", use_container_width=True)

    n_frames = FRAME_OPTIONS[duration_label]

    # Mostrar timestamp más reciente sin descargar imágenes
    latest_ts = _fetch_latest_ts(product)

    # ── Info panel inicial ──
    if not fetch_btn and "rammb_frames" not in st.session_state:
        col_info, col_ts = st.columns([2, 1])
        with col_info:
            info_panel(
                "<b>Animacion de pulsos eruptivos</b><br><br>"
                "Esta pagina descarga los ultimos N scans del satelite GOES-19 "
                "y los muestra como un loop animado. Permite observar el desarrollo "
                "temporal de plumas de ceniza, nubes de SO2 y columnas eruptivas.<br><br>"
                "<b>GeoColor</b>: Color real mejorado (solo dia). Ideal para ver columnas eruptivas.<br>"
                "<b>Ash RGB</b>: Deteccion de ceniza (dia y noche). Ceniza = rojo/magenta.<br>"
                "<b>SO2</b>: Dioxido de azufre. Nube de SO2 = verde brillante.<br>"
                "<b>BTD</b>: Diferencia termica split-window. Mas sensible a ceniza fina."
            )
        with col_ts:
            st.markdown(
                f'<div class="legend-container">'
                f'<div class="legend-title">Ultima imagen disponible</div>'
                f'<div style="font-size:0.85rem; color:#99aabb; margin-top:0.4rem;">'
                f'<b>{PRODUCT_LABELS[product]}</b><br>'
                f'<span style="font-size:0.78rem;">{latest_ts}</span>'
                f'</div></div>',
                unsafe_allow_html=True,
            )
        return

    # ── Cargar frames ──
    if fetch_btn:
        st.session_state["rammb_product_sel"] = product
        st.session_state["rammb_nframes"] = n_frames
        # Invalidar cache anterior si cambió producto
        _fetch_cached.clear()

    sel_product = st.session_state.get("rammb_product_sel", product)
    sel_n = st.session_state.get("rammb_nframes", n_frames)

    with st.spinner(f"Descargando {sel_n} scans GOES-19 ({PRODUCT_LABELS[sel_product]})..."):
        frames = _fetch_cached(sel_product, sel_n)

    if not frames:
        st.error("No se pudieron descargar frames. Verifica conexion a internet.")
        return

    # ── KPIs ──
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        kpi_card(str(len(frames)), "Frames cargados")
    with k2:
        kpi_card(frames[0]["label"][-9:-4], "Frame inicial (UTC)")
    with k3:
        kpi_card(frames[-1]["label"][-9:-4], "Frame final (UTC)")
    with k4:
        kpi_card(f"{len(frames)*10} min", "Ventana temporal")

    st.markdown("<div style='height:0.3rem'></div>", unsafe_allow_html=True)

    # ── Status ──
    st.markdown(
        f'<div class="status-banner ok">'
        f'<b>&#10003; {len(frames)} frames &middot; {PRODUCT_LABELS[sel_product]} &middot; '
        f'RAMMB/CIRA GOES-19</b>'
        f'<span style="color:#556677; font-size:0.78rem;">{latest_ts}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # ── Animacion ──
    st.markdown(
        '<div style="font-size:0.8rem; color:#556677; margin:0.3rem 0 0.5rem 0;">'
        'Presiona <b>▶ Play</b> para ver la animacion. Usa el slider inferior para '
        'navegar frame a frame.</div>',
        unsafe_allow_html=True,
    )

    bounds = frames[0].get("bounds", CHILE_TILE_BOUNDS)
    fig = _build_animation(frames, bounds)
    st.plotly_chart(fig, use_container_width=True)

    # ── Nota sobre RAMMB Slider ──
    st.markdown(
        '<div style="font-size:0.75rem; color:#445566; margin-top:0.5rem;">'
        'Tiles de <a href="https://slider.cira.colostate.edu/?sat=goes-19&sec=full_disk" '
        'target="_blank" style="color:#667788;">RAMMB/CIRA Slider</a> '
        '(Colorado State University). Zoom interactivo disponible en el enlace.'
        '</div>',
        unsafe_allow_html=True,
    )
