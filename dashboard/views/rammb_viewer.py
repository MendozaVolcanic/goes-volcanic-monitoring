"""Pagina RAMMB Slider: animacion de imagenes GOES-19 en tiempo real.

Muestra loops animados de los ultimos N scans del satelite GOES-19,
con 3 escopos: Nacional (Chile completo), Por zona volcanica, Por volcan.

Fuente: slider.cira.colostate.edu (CIRA/CSU + NOAA/RAMMB).
"""

import base64
import io
import logging
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import plotly.graph_objects as go
import streamlit as st
from PIL import Image as PILImage

from dashboard.style import (
    C_ACCENT, C_ASH, C_SO2,
    header, info_panel, kpi_card, refresh_info_badge,
)
from dashboard.utils import fmt_both, fmt_both_long, fmt_chile, parse_rammb_ts
from src.config import CHILE_BOUNDS, VOLCANIC_ZONES
from src.fetch.rammb_slider import (
    CHILE_REPROJECTED_BOUNDS, CHILE_TILE_BOUNDS, CHILE_TILES_Z2, PRODUCTS,
    ZOOM_ZONE, ZOOM_VOLCAN, VOLCANO_RADIUS_DEG,
    fetch_animation_frames, fetch_frame_for_bounds,
    get_latest_timestamps, reproject_to_latlon, ts_to_parts,
)
from src.volcanos import CATALOG, PRIORITY_VOLCANOES, get_priority, get_volcano

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

ZONE_LABELS = {
    "norte":   "Zona Norte",
    "centro":  "Zona Centro",
    "sur":     "Zona Sur",
    "austral": "Zona Austral",
}


def _frame_label(ts: str) -> str:
    """'20260424122000' -> '2026-04-24 12:20 UTC (08:20 CLT)'"""
    dt = parse_rammb_ts(ts)
    return fmt_both_long(dt)


def _img_to_b64(arr: np.ndarray) -> str:
    buf = io.BytesIO()
    PILImage.fromarray(arr).save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


def _volcano_scatter(bounds: dict, highlight=None) -> go.Scatter:
    """Scatter de volcanes visibles dentro de los bounds."""
    vis = [v for v in get_priority()
           if bounds["lat_min"] <= v.lat <= bounds["lat_max"]
           and bounds["lon_min"] <= v.lon <= bounds["lon_max"]]
    if not vis:
        vis = [v for v in CATALOG
               if bounds["lat_min"] <= v.lat <= bounds["lat_max"]
               and bounds["lon_min"] <= v.lon <= bounds["lon_max"]][:20]
    if not vis:
        return None
    return go.Scatter(
        x=[v.lon for v in vis], y=[v.lat for v in vis],
        mode="markers+text",
        marker=dict(size=4, color=C_ACCENT, symbol="triangle-up",
                    line=dict(width=0.6, color="white")),
        text=[v.name for v in vis],
        textposition="top center",
        textfont=dict(size=7, color="rgba(255,255,255,0.8)"),
        name="Volcanes",
        hovertext=[f"<b>{v.name}</b><br>{v.elevation:,} m" for v in vis],
        hoverinfo="text", showlegend=False,
    )


def _build_animation(frames: list[dict], bounds: dict, height: int = 700) -> go.Figure:
    """Construir figura Plotly animada con los frames (mas antiguo -> mas reciente)."""
    lat_min = bounds["lat_min"]
    lat_max = bounds["lat_max"]
    lon_min = bounds["lon_min"]
    lon_max = bounds["lon_max"]

    volc_scatter = _volcano_scatter(bounds)
    base_traces = [
        go.Scatter(x=[lon_min, lon_max], y=[lat_min, lat_max],
                   mode="markers", marker=dict(opacity=0),
                   showlegend=False, hoverinfo="skip"),
    ]
    if volc_scatter is not None:
        base_traces.append(volc_scatter)

    plotly_frames = []
    for i, f in enumerate(frames):
        b64 = _img_to_b64(f["image"])
        plotly_frames.append(go.Frame(
            data=base_traces,
            layout=go.Layout(
                images=[dict(
                    source=f"data:image/png;base64,{b64}",
                    xref="x", yref="y",
                    x=lon_min, y=lat_max,
                    xanchor="left", yanchor="top",
                    sizex=lon_max - lon_min,
                    sizey=lat_max - lat_min,
                    sizing="stretch", layer="below",
                )],
                title_text=f["label"],
            ),
            name=str(i),
        ))

    b64_first = _img_to_b64(frames[0]["image"])
    # Slider steps: mostrar HH:MM UTC y CLT
    slider_steps = []
    for i, f in enumerate(frames):
        dt = parse_rammb_ts(f["ts"])
        slider_steps.append(dict(
            method="animate",
            args=[[str(i)], dict(
                frame=dict(duration=0, redraw=True),
                mode="immediate", transition=dict(duration=0),
            )],
            label=dt.strftime("%H:%M"),
        ))

    fig = go.Figure(
        data=base_traces,
        layout=go.Layout(
            images=[dict(
                source=f"data:image/png;base64,{b64_first}",
                xref="x", yref="y",
                x=lon_min, y=lat_max,
                xanchor="left", yanchor="top",
                sizex=lon_max - lon_min,
                sizey=lat_max - lat_min,
                sizing="stretch", layer="below",
            )],
            title=dict(text=frames[0]["label"], font=dict(size=13, color="#ccc")),
            xaxis_title="Longitud", yaxis_title="Latitud",
            yaxis=dict(scaleanchor="x", scaleratio=1,
                       range=[lat_min, lat_max]),
            xaxis=dict(range=[lon_min, lon_max]),
            height=height,
            template="plotly_dark",
            margin=dict(t=55, b=75, l=50, r=20),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            updatemenus=[dict(
                type="buttons", showactive=False,
                y=0, x=0.5, xanchor="center", yanchor="top",
                pad=dict(t=10),
                buttons=[
                    dict(label="▶ Play", method="animate",
                         args=[None, dict(
                             frame=dict(duration=800, redraw=True),
                             fromcurrent=True, transition=dict(duration=0),
                         )]),
                    dict(label="⏸ Pausa", method="animate",
                         args=[[None], dict(
                             frame=dict(duration=0, redraw=False),
                             mode="immediate", transition=dict(duration=0),
                         )]),
                ],
            )],
            sliders=[dict(
                active=0,
                currentvalue=dict(prefix="UTC: ",
                                  font=dict(size=11, color="#aaa")),
                pad=dict(t=50, b=10),
                steps=slider_steps,
            )],
        ),
        frames=plotly_frames,
    )
    return fig


# Versión de reproyección — cambiar si se modifica cfac/bounds para invalidar caché
_REPROJECT_VERSION = "v2"


@st.cache_data(ttl=600, show_spinner=False)
def _fetch_chile_frames(product: str, n_frames: int,
                        _v: str = _REPROJECT_VERSION) -> list[dict]:
    """Animacion Chile completo (zoom=2 reprojectado)."""
    frames = fetch_animation_frames(
        product=product, n_frames=n_frames, zoom=2,
        tile_rows=CHILE_TILES_Z2["rows"], tile_cols=CHILE_TILES_Z2["cols"],
    )
    for f in frames:
        f["image"] = reproject_to_latlon(f["image"], col_start=678, row_start=1356)
        f["bounds"] = CHILE_REPROJECTED_BOUNDS
        f["label"] = _frame_label(f["ts"])
    return frames


@st.cache_data(ttl=600, show_spinner=False)
def _fetch_bounds_frames(product: str, n_frames: int, zoom: int,
                         bounds_key: str, bounds_tuple: tuple,
                         _v: str = _REPROJECT_VERSION) -> list[dict]:
    """Animacion generica para un bbox arbitrario (zona o volcan).

    bounds_key/bounds_tuple son redundantes solo para hacer la key hashable.
    """
    bounds = {
        "lat_min": bounds_tuple[0], "lat_max": bounds_tuple[1],
        "lon_min": bounds_tuple[2], "lon_max": bounds_tuple[3],
    }
    timestamps = get_latest_timestamps(product, n=n_frames)
    if not timestamps:
        return []
    # Descarga paralela de los N frames (cada uno stitchea varios tiles).
    # Speedup ~N/4 para N frames, limitado por max_workers.
    def _one(ts):
        img = fetch_frame_for_bounds(product, ts, bounds, zoom=zoom)
        return ts, img

    out = []
    with ThreadPoolExecutor(max_workers=6) as ex:
        results = list(ex.map(_one, timestamps))
    for ts, img in results:
        if img is None:
            continue
        out.append({
            "ts": ts,
            "label": _frame_label(ts),
            "image": img,
            "bounds": bounds,
        })
    # Mas antiguo -> mas reciente
    out.sort(key=lambda f: f["ts"])
    return out


@st.cache_data(ttl=300, show_spinner=False)
def _fetch_latest_ts_label(product: str) -> str:
    times = get_latest_timestamps(product, n=1)
    return _frame_label(times[0]) if times else "—"


def render():
    header(
        "Animacion RAMMB/CIRA — GOES-19",
        "Loops de los ultimos scans &middot; Nacional, por zona o por volcan",
    )
    refresh_info_badge(context="animation")

    # ── Controles ─────────────────────────────────────────────────────────
    c1, c2, c3 = st.columns([1.5, 1.2, 1])
    with c1:
        product = st.selectbox(
            "Producto",
            options=list(PRODUCT_LABELS.keys()),
            format_func=lambda k: PRODUCT_LABELS[k],
            index=0, key="rammb_product",
        )
    with c2:
        duration_label = st.selectbox(
            "Duracion del loop",
            options=list(FRAME_OPTIONS.keys()),
            index=1, key="rammb_duration",
        )
    with c3:
        st.markdown("<div style='height:1.6rem'></div>", unsafe_allow_html=True)
        fetch_btn = st.button("Cargar animacion", type="primary",
                              use_container_width=True)

    # Scope selector (Nacional / Zona / Volcan)
    scope = st.radio(
        "Cobertura",
        ["Nacional (Chile)", "Por zona volcanica", "Por volcan"],
        index=0, horizontal=True, key="anim_scope",
    )

    zone_key = None
    volc_name = None
    radius = VOLCANO_RADIUS_DEG

    if scope == "Por zona volcanica":
        zone_key = st.selectbox(
            "Zona",
            list(ZONE_LABELS.keys()),
            format_func=lambda k: ZONE_LABELS[k],
            index=2, key="anim_zone",
        )
    elif scope == "Por volcan":
        cv1, cv2 = st.columns([2, 1])
        with cv1:
            priority_names = [v.name for v in CATALOG if v.name in PRIORITY_VOLCANOES]
            other_names    = [v.name for v in CATALOG if v.name not in priority_names]
            volc_options   = [f"★ {n}" for n in priority_names] + other_names
            sel_raw = st.selectbox("Volcan", volc_options, index=0, key="anim_volc")
            volc_name = sel_raw.replace("★ ", "")
        with cv2:
            radius = st.slider("Radio (°)", 0.5, 3.0, VOLCANO_RADIUS_DEG, 0.5,
                               key="anim_radius")

    n_frames = FRAME_OPTIONS[duration_label]
    latest_ts_label = _fetch_latest_ts_label(product)

    # ── Info panel inicial ────────────────────────────────────────────────
    if not fetch_btn and "anim_frames" not in st.session_state:
        col_info, col_ts = st.columns([2, 1])
        with col_info:
            info_panel(
                "<b>Animacion de pulsos eruptivos</b><br><br>"
                "Descarga los ultimos N scans de GOES-19 y los muestra como loop.<br>"
                "Eleginado <b>Cobertura</b> podes ver todo Chile, una zona volcanica "
                "especifica, o hacer zoom a un volcan individual.<br><br>"
                "<b>GeoColor</b>: color real mejorado (solo dia).<br>"
                "<b>Ash RGB</b>: deteccion de ceniza (dia y noche). Ceniza = rojo/magenta.<br>"
                "<b>SO2</b>: dioxido de azufre = verde brillante.<br>"
                "<b>BTD</b>: diferencia termica split-window, mas sensible a ceniza fina."
            )
        with col_ts:
            st.markdown(
                f'<div class="legend-container">'
                f'<div class="legend-title">Ultima imagen disponible</div>'
                f'<div style="font-size:0.8rem; color:#99aabb; margin-top:0.4rem;">'
                f'<b>{PRODUCT_LABELS[product]}</b><br>'
                f'<span style="font-size:0.78rem;">{latest_ts_label}</span>'
                f'</div></div>',
                unsafe_allow_html=True,
            )
        return

    # ── Guardar seleccion en session_state al presionar el boton ──────────
    if fetch_btn:
        st.session_state["anim_frames"] = True
        st.session_state["anim_sel"] = dict(
            product=product, n=n_frames, scope=scope,
            zone=zone_key, volc=volc_name, radius=radius,
        )

    sel = st.session_state.get("anim_sel", dict(
        product=product, n=n_frames, scope=scope,
        zone=zone_key, volc=volc_name, radius=radius,
    ))

    # ── Determinar bounds + zoom segun scope ──────────────────────────────
    scope_sel = sel["scope"]
    scope_label = ""
    height = 700
    try:
        if scope_sel == "Nacional (Chile)":
            with st.spinner(f"Descargando {sel['n']} scans nacionales..."):
                frames = _fetch_chile_frames(sel["product"], sel["n"])
            scope_label = "Chile completo"
            height = 700
        elif scope_sel == "Por zona volcanica":
            zk = sel["zone"] or "sur"
            zb = VOLCANIC_ZONES[zk]
            bt = (zb["lat_min"], zb["lat_max"], zb["lon_min"], zb["lon_max"])
            with st.spinner(f"Descargando {sel['n']} scans de {ZONE_LABELS[zk]}..."):
                frames = _fetch_bounds_frames(
                    sel["product"], sel["n"], ZOOM_ZONE, zk, bt,
                )
            scope_label = ZONE_LABELS[zk]
            height = 640
        else:  # Por volcan
            vname = sel["volc"]
            v = get_volcano(vname) if vname else None
            if v is None:
                st.error(f"Volcan '{vname}' no encontrado.")
                return
            r = sel["radius"]
            vb = {
                "lat_min": v.lat - r, "lat_max": v.lat + r,
                "lon_min": v.lon - r, "lon_max": v.lon + r,
            }
            bt = (vb["lat_min"], vb["lat_max"], vb["lon_min"], vb["lon_max"])
            with st.spinner(f"Descargando {sel['n']} scans zoom para {v.name}..."):
                frames = _fetch_bounds_frames(
                    sel["product"], sel["n"], ZOOM_VOLCAN, f"v:{v.name}", bt,
                )
                if not frames:
                    # Fallback a zoom=3 si zoom=4 no esta disponible
                    frames = _fetch_bounds_frames(
                        sel["product"], sel["n"], ZOOM_ZONE, f"vz3:{v.name}", bt,
                    )
            scope_label = f"{v.name} (±{r}°)"
            height = 720
    except Exception as e:
        logger.exception("anim error")
        st.error(f"Error descargando: {e}")
        return

    if not frames:
        st.error("No se pudieron descargar frames. Verifica conexion o "
                 "prueba otro producto/scope.")
        return

    # ── KPIs (ahora con hora local ademas de UTC) ─────────────────────────
    dt_first = parse_rammb_ts(frames[0]["ts"])
    dt_last  = parse_rammb_ts(frames[-1]["ts"])
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        kpi_card(str(len(frames)), "Frames cargados")
    with k2:
        kpi_card(
            dt_first.strftime("%H:%M"),
            "Inicio",
            delta=fmt_chile(dt_first),
        )
    with k3:
        kpi_card(
            dt_last.strftime("%H:%M"),
            "Fin",
            delta=fmt_chile(dt_last),
        )
    with k4:
        kpi_card(f"{len(frames)*10} min", "Ventana")

    st.markdown("<div style='height:0.3rem'></div>", unsafe_allow_html=True)

    # Status banner con scope + hora UTC+CLT
    st.markdown(
        f'<div class="status-banner ok">'
        f'<b>&#10003; {len(frames)} frames &middot; '
        f'{PRODUCT_LABELS[sel["product"]]} &middot; {scope_label}</b>'
        f'<span style="color:#556677; font-size:0.78rem;">'
        f'{latest_ts_label}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div style="font-size:0.78rem; color:#556677; margin:0.3rem 0 0.5rem 0;">'
        'Presiona <b>▶ Play</b> para ver la animacion. Slider inferior '
        '(UTC) navega frame a frame. Cada etiqueta del titulo muestra UTC + hora Chile.'
        '</div>',
        unsafe_allow_html=True,
    )

    bounds = frames[0]["bounds"]
    fig = _build_animation(frames, bounds, height=height)
    st.plotly_chart(fig, use_container_width=True)

    st.markdown(
        '<div style="font-size:0.72rem; color:#445566; margin-top:0.5rem;">'
        'Tiles de <a href="https://slider.cira.colostate.edu/?sat=goes-19&sec=full_disk" '
        'target="_blank" style="color:#667788;">RAMMB/CIRA Slider</a> '
        '(Colorado State University).'
        '</div>',
        unsafe_allow_html=True,
    )
