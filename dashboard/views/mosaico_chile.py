"""Mosaico Chile: los 8 volcanes prioritarios en grilla 4x2.

FILOSOFIA: barrer todo Chile en un golpe de vista. Una mini-imagen
Ash RGB por volcan, zoom volcan, sin numeros, sin alertas. El experto
ve los 8 cuadros y decide si algo merece zoom adicional.

Auto-refresh 60s. Cada miniatura usa el ultimo scan disponible.
"""

import logging
from datetime import datetime, timezone

import numpy as np
import plotly.graph_objects as go
import streamlit as st

try:
    from dashboard.style import volcano_marker
    from dashboard.utils import fmt_chile, parse_rammb_ts
    from src.fetch.rammb_slider import (
        fetch_frame_robust, get_latest_timestamps, ZOOM_VOLCAN, ZOOM_ZONE,
    )
    from src.volcanos import PRIORITY_VOLCANOES, get_volcano
except Exception:
    # Streamlit Cloud hot-reload race condition: retry import dentro de funciones.
    # Si esto se ejecuta, hay un bug — log y reraise para que Streamlit muestre el error.
    import logging as _logging
    _logging.exception("Cross-package import fallo top-level — gotcha Streamlit Cloud")
    raise

logger = logging.getLogger(__name__)

REFRESH_SECONDS = 60
ROTATION_SECONDS = 10
# Radio del bbox por volcan en el mosaico. Canonical en src/config
# (MOSAICO_RADIUS_DEG). Fallback hardcoded por si Streamlit Cloud
# falla el import cross-package durante hot-reload (gotcha CLAUDE.md).
try:
    from src.config import MOSAICO_RADIUS_DEG as RADIUS_DEG
except Exception:
    RADIUS_DEG = 0.5  # ver src/config.py para canonical
PRODUCT_LIST_TV = ["geocolor", "eumetsat_ash", "jma_so2"]

PRODUCT_OPTIONS = {
    "eumetsat_ash": "Ash RGB",
    "geocolor": "GeoColor",
    "jma_so2": "SO2 RGB",
}


@st.cache_data(ttl=30, show_spinner=False)
def _recent_timestamps(product: str, n: int = 5) -> list[str]:
    """Ultimos N timestamps. Cache 30s."""
    return get_latest_timestamps(product, n=n)


def _volcano_frame_with_fallback(product: str, timestamps: list[str],
                                  lat: float, lon: float
                                  ) -> tuple[np.ndarray | None, str | None, int]:
    """Fallback de ts + zoom: zoom=4 -> zoom=3 si zoom=4 falla.

    RAMMB intermitentemente no sirve algunos productos en zoom=4.
    Devuelve (img, ts_usado, zoom_usado). zoom=0 si todo fallo.

    Bbox asimetrico (lon expandido por 1/cos_lat) para que la imagen
    descargada cubra una region cuadrada en km — coincide con el plot.
    """
    cos_lat = max(0.1, float(np.cos(np.radians(lat))))
    half_lon = RADIUS_DEG / cos_lat
    bounds = {
        "lat_min": lat - RADIUS_DEG, "lat_max": lat + RADIUS_DEG,
        "lon_min": lon - half_lon, "lon_max": lon + half_lon,
    }
    return fetch_frame_robust(
        product, timestamps, bounds,
        zoom_preferred=ZOOM_VOLCAN, zoom_fallback=ZOOM_ZONE,
    )


def _array_to_data_url(arr):
    # Lazy import (gotcha Streamlit Cloud — ver CLAUDE.md).
    from dashboard.map_helpers import array_to_data_url
    return array_to_data_url(arr)



RING_RADII_KM = [5, 10, 25, 50]


def _circle_points(lat0: float, lon0: float, radius_km: float, n: int = 48):
    theta = np.linspace(0, 2 * np.pi, n)
    dlat = (radius_km / 111.0) * np.cos(theta)
    dlon = (radius_km / (111.0 * float(np.cos(np.radians(lat0))))) * np.sin(theta)
    return (lat0 + dlat).tolist(), (lon0 + dlon).tolist()


def _render_mini(img: np.ndarray | None, lat: float, lon: float, name: str,
                 height: int = 420, show_rings: bool = False,
                 target_width_px: int | None = None,
                 zoom_used: int | None = None,
                 hires_render: str | None = None,
                 hires_sun_alt: float | None = None):
    """Mini-plot cuadrado con bbox compensado por latitud.

    `height` se usa solo si `target_width_px=None`. Si se pasa width,
    el height se calcula como `width * cos_lat` para que el plot llene
    el container sin barras negras arriba/abajo (porque scaleanchor
    requiere proporcion exacta entre x e y en pantalla).
    """
    fig = go.Figure()
    cos_lat = max(0.1, float(np.cos(np.radians(lat))))
    # Si nos pasaron target_width_px, derivamos height para que el plot
    # llene el container sin espacio negro. Usamos un cos_lat MEDIANO
    # (no el del volcan especifico) porque sino las miniaturas de
    # diferente latitud quedan con altura distinta y desalinean el grid.
    # 0.78 = mediana de los 8 priority volcanos (~lat -38°).
    # Lascar (lat -23, cos=0.92) tendra pequena banda lateral pero el
    # grid queda alineado fila a fila.
    if target_width_px is not None:
        MEDIAN_COS_LAT_PRIORITY = 0.78
        height = max(200, int(target_width_px * MEDIAN_COS_LAT_PRIORITY))
    # span en km equivalente: RADIUS_DEG * 111 km. Lon en grados se expande
    # por 1/cos_lat para preservar el mismo span en km horizontal.
    half_lat = RADIUS_DEG
    half_lon = RADIUS_DEG / cos_lat
    bounds = {
        "lat_min": lat - half_lat, "lat_max": lat + half_lat,
        "lon_min": lon - half_lon, "lon_max": lon + half_lon,
    }
    if img is not None:
        fig.add_layout_image(
            source=_array_to_data_url(img),
            xref="x", yref="y",
            x=bounds["lon_min"], y=bounds["lat_max"],
            sizex=2 * half_lon, sizey=2 * half_lat,
            sizing="stretch", layer="below",
        )
    # Anillos de distancia (debajo del marcador) + label de km
    if show_rings:
        for r_km in RING_RADII_KM:
            lats, lons = _circle_points(lat, lon, r_km)
            fig.add_trace(go.Scatter(
                x=lons, y=lats, mode="lines",
                line=dict(color="rgba(255,255,255,0.35)", width=0.8, dash="dot"),
                hoverinfo="skip", showlegend=False,
            ))
            # Label "{r_km} km" justo arriba del cruce norte de cada anillo
            fig.add_annotation(
                x=lon, y=lat + (r_km / 111.0),
                text=f"{r_km}", showarrow=False,
                font=dict(size=8, color="rgba(255,255,255,0.75)"),
                bgcolor="rgba(0,0,0,0.55)", borderpad=1,
            )
    fig.add_trace(go.Scatter(
        x=[lon], y=[lat], mode="markers",
        marker=volcano_marker("zone"),
        hovertemplate=f"<b>{name}</b><extra></extra>",
        showlegend=False,
    ))
    fig.update_xaxes(range=[bounds["lon_min"], bounds["lon_max"]],
                     showgrid=False, visible=False)
    fig.update_yaxes(range=[bounds["lat_min"], bounds["lat_max"]],
                     showgrid=False, visible=False,
                     scaleanchor="x", scaleratio=1.0 / cos_lat)
    # Nombre del volcan: annotation EN COORDENADAS DE DATOS (no paper).
    # Si fuera paper, scaleanchor empuja el text al espacio negro afuera
    # de la imagen. En coords de datos, queda siempre adentro del bbox
    # visible — esquina sup-izq de la imagen real.
    fig.add_annotation(
        x=bounds["lon_min"], y=bounds["lat_max"],
        xref="x", yref="y",
        text=f"<b>{name}</b>", showarrow=False,
        font=dict(size=12, color="#ffffff"),
        bgcolor="rgba(0,0,0,0.65)", borderpad=3,
        xanchor="left", yanchor="top",
        xshift=4, yshift=-4,
    )
    # Badge de zoom usado + tipo de render (esquina inferior derecha):
    #   -2 = hi-res mono 0.5 km/px (cyan), -1 = hi-res color 1 km/px (azul),
    #    4 = RAMMB max (verde),  3 = RAMMB fallback (naranja).
    # Para hi-res, distinguir explicitamente VIS vs IR — clave porque a sol
    # bajo el pipeline cae a IR pseudo-color y la imagen se ve sepia/amarillo
    # (confuso si el usuario espera color real).
    if zoom_used is not None and zoom_used != 0:
        if zoom_used == -2:
            badge_color = "#00ddff"
            badge_text = "HI-RES MONO · 0.5km/px (4×)"
            if hires_sun_alt is not None:
                badge_text += f" · ☀{hires_sun_alt:.0f}°"
        elif zoom_used == -1:
            # Render: visible_color (TrueColor), ir_pseudo (sol bajo -> IR), o None
            if hires_render == "ir_pseudo":
                badge_color = "#ffaa55"  # naranja: alerta visible no disponible
                badge_text = "HI-RES IR · 1km/px"
                if hires_sun_alt is not None:
                    badge_text += f" · ☀{hires_sun_alt:.0f}° (noche/twilight)"
            elif hires_render == "visible_color":
                badge_color = "#33aaff"
                badge_text = "HI-RES VIS · 1km/px"
                if hires_sun_alt is not None:
                    badge_text += f" · ☀{hires_sun_alt:.0f}°"
            else:
                badge_color = "#33aaff"
                badge_text = "HI-RES NOAA · 1km/px"
        elif zoom_used >= 4:
            badge_color = "#3fb950"
            badge_text = f"z={zoom_used} · 1.7km/px"
        else:
            badge_color = "#ff9933"
            kmpx = {3: "3.4", 2: "6.8"}.get(zoom_used, "?")
            badge_text = f"z={zoom_used} · {kmpx}km/px"
        fig.add_annotation(
            x=bounds["lon_max"], y=bounds["lat_min"],
            xref="x", yref="y",
            text=badge_text,
            showarrow=False,
            font=dict(size=9, color=badge_color),
            bgcolor="rgba(0,0,0,0.7)", borderpad=2,
            xanchor="right", yanchor="bottom",
            xshift=-3, yshift=3,
        )
    fig.update_layout(
        height=height, margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor="#0a0e14", plot_bgcolor="#0a0e14",
    )
    if img is None:
        fig.add_annotation(
            text="sin datos",
            xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False,
            font=dict(color="#556", size=11),
        )
    return fig


@st.cache_data(ttl=120, show_spinner=False)
def _hires_for_volcano_cached(volcano_name: str, mode: str = "color"):
    """Wrapper cacheado del fetch hi-res. Cache 2 min para no spamear."""
    from src.fetch.hires_cache import fetch_hires_for_volcano
    return fetch_hires_for_volcano(volcano_name, mode=mode)


@st.fragment(run_every=f"{REFRESH_SECONDS}s")
def _grid_fragment(product: str, use_hires: bool = False,
                   hires_mode: str = "color"):
    """Solo el grid se auto-refresca cada 60s. El selector queda afuera."""
    timestamps = _recent_timestamps(product, n=5)
    now = datetime.now(timezone.utc)
    if not timestamps:
        st.error("RAMMB no respondió. Reintentá en unos segundos.")
        return

    ts = timestamps[0]
    try:
        scan_dt = parse_rammb_ts(ts)
        age_min = int((now - scan_dt).total_seconds() / 60)
        scan_label = f"{scan_dt.strftime('%H:%M UTC')} (hace {age_min} min)"
    except Exception:
        scan_label = ts

    rings_str = " / ".join(str(r) for r in RING_RADII_KM)
    st.markdown(
        f"<div style='background:#0f1418; border-left:4px solid #ff6644; "
        f"padding:0.6rem 1rem; border-radius:4px; margin-bottom:0.8rem; "
        f"display:flex; justify-content:space-between; align-items:center;'>"
        f"<div style='color:#e0e0e0;'>{PRODUCT_OPTIONS[product]} · "
        f"8 volcanes prioritarios &middot; "
        f"<span style='color:#9aaabb; font-size:0.85rem;'>"
        f"⊙ anillos {rings_str} km desde el crater</span></div>"
        f"<div style='color:#9aaabb; font-size:0.85rem;'>Scan {scan_label} · "
        f"render {now.strftime('%H:%M:%S')} UTC</div></div>",
        unsafe_allow_html=True,
    )

    # Grid 2 filas x 4 columnas
    fallback_ts = 0
    fallback_zoom = 0
    hires_used = 0
    hires_fallback = 0
    rows = [PRIORITY_VOLCANOES[:4], PRIORITY_VOLCANOES[4:8]]
    for row_volcanos in rows:
        cols = st.columns(4)
        for i, name in enumerate(row_volcanos):
            v = get_volcano(name)
            if v is None:
                continue

            # Intento hi-res primero si toggle activo
            img = None
            used_zoom = 0  # 0 = RAMMB normal con zoom 4
            hires_render = None  # 'visible_color' | 'visible_mono' | 'ir_pseudo' | None
            hires_sun_alt = None
            if use_hires:
                hires_arr, hires_info = _hires_for_volcano_cached(name, mode=hires_mode)
                if hires_arr is not None:
                    img = hires_arr
                    # -2 = mono_05km (4× zoom), -1 = color 1km/px
                    used_zoom = -2 if hires_mode == "mono_05km" else -1
                    if hires_info:
                        hires_render = hires_info.get("render")
                        hires_sun_alt = hires_info.get("sun_alt")
                    hires_used += 1
                else:
                    hires_fallback += 1

            # Fallback a RAMMB si no hi-res
            if img is None:
                img, used_ts, used_zoom = _volcano_frame_with_fallback(
                    product, timestamps, v.lat, v.lon,
                )
                if used_ts and used_ts != ts:
                    fallback_ts += 1
                if used_zoom == ZOOM_ZONE:
                    fallback_zoom += 1
            with cols[i]:
                st.plotly_chart(
                    _render_mini(img, v.lat, v.lon, name,
                                 target_width_px=380, show_rings=True,
                                 zoom_used=used_zoom,
                                 hires_render=hires_render,
                                 hires_sun_alt=hires_sun_alt),
                    width='stretch',
                    config={"displayModeBar": False},
                )

    if use_hires:
        # Distinguir 3 casos al user: todo OK / parcial fallback / TODO fallback
        if hires_used == 0:
            # Caso especial mono_05km: el workflow del cron OOMs en runner
            # GH free porque banda 2 nativa (21696×21696) requiere ~7 GB RAM
            # solo para get_lat_lon. Por eso el cache mono esta SIEMPRE vacio
            # y siempre cae a RAMMB. El user no nota diferencia con RAMMB
            # normal — por eso un mensaje explicito.
            if hires_mode == "mono_05km":
                st.warning(
                    "⚠ **Hi-res mono (0.5 km/px) NO disponible actualmente** — el "
                    "workflow falla por OOM en runner GH free (banda 2 nativa "
                    "requiere ~7 GB RAM). Lo que ves es **RAMMB fallback**. "
                    "Para activar el modo mono real: correr `python scripts/build_hires_cache.py "
                    "--mode mono_05km` desde el localhost del observatorio (más RAM)."
                )
            else:
                st.warning(
                    f"⚠ **Hi-res color sin datos disponibles** ({hires_fallback}/8 "
                    "fallback a RAMMB). El cache puede estar viejo o el cron tardó. "
                    "Re-trigger del workflow `hires_visible_cache.yml` en GitHub Actions."
                )
        else:
            st.caption(f"🔬 Hi-res NOAA activo · {hires_used}/8 usaron hi-res, "
                       f"{hires_fallback}/8 fallback a RAMMB")

    notes = []
    if fallback_ts:
        notes.append(f"{fallback_ts} con scan previo")
    if fallback_zoom:
        notes.append(f"{fallback_zoom} en zoom 3 (RAMMB no sirvió zoom 4)")
    if notes:
        st.caption("ℹ " + " · ".join(notes))


@st.fragment(run_every=f"{ROTATION_SECONDS}s")
def _grid_fragment_tv(session_key: str = "tv_mosaico_rot_idx"):
    """Modo TV puro: 8 prioritarios en grid 4x2, paneles grandes,
    rotando productos GeoColor -> Ash -> SO2 cada 10s, con anillos.

    Sin chrome (toolbar, banner status). Solo etiqueta minimal flotante.
    """
    import io
    import base64
    if session_key not in st.session_state:
        st.session_state[session_key] = 0
    idx = st.session_state[session_key] % len(PRODUCT_LIST_TV)
    current = PRODUCT_LIST_TV[idx]
    next_idx = (idx + 1) % len(PRODUCT_LIST_TV)
    st.session_state[session_key] = next_idx

    timestamps = _recent_timestamps(current, n=5)
    scan_dt = parse_rammb_ts(timestamps[0]) if timestamps else None

    # Leyenda compacta interpretativa en el espacio negro superior.
    # Cambia con el producto rotante. Status badge a la derecha con scan + refresh.
    from dashboard.map_helpers import render_compact_legend, render_scan_status_badge
    render_compact_legend(
        current,
        extra_left=(f"<span style='color:#ff6644; font-weight:700; "
                    f"margin-right:0.2rem;'>🔄 Mosaico 8 ·</span>"),
        extra_right=render_scan_status_badge(scan_dt, ROTATION_SECONDS),
    )

    if not timestamps:
        st.error("RAMMB no respondió.")
        return

    # Grid 2 filas x 4 columnas, paneles grandes (450 px)
    rows = [PRIORITY_VOLCANOES[:4], PRIORITY_VOLCANOES[4:8]]
    for row_volcanos in rows:
        cols = st.columns(4)
        for i, name in enumerate(row_volcanos):
            v = get_volcano(name)
            if v is None:
                continue
            img, _, used_zoom = _volcano_frame_with_fallback(
                current, timestamps, v.lat, v.lon,
            )
            with cols[i]:
                st.plotly_chart(
                    _render_mini(img, v.lat, v.lon, name,
                                 target_width_px=460, show_rings=True,
                                 zoom_used=used_zoom),
                    width='stretch',
                    config={"displayModeBar": False},
                )


def _live_panel():
    """Selector de producto + grid con auto-refresh."""
    cols_top = st.columns([2, 2.5, 2.5])
    with cols_top[0]:
        product = st.selectbox(
            "Producto",
            options=list(PRODUCT_OPTIONS.keys()),
            format_func=lambda k: PRODUCT_OPTIONS[k],
            index=0, key="mosaico_product",
        )
    with cols_top[1]:
        hires_mode = st.radio(
            "Resolucion",
            ["RAMMB normal", "Hi-res color (1 km/px)",
             "Hi-res mono (0.5 km/px) ⚠"],
            index=0, key="mosaico_hires_mode", horizontal=True,
            help="RAMMB normal: tiles CIRA 1.7 km/px (siempre disponible).\n"
                 "Hi-res color: NOAA L1b TrueColor 1km/px diurno + IR nocturno.\n"
                 "Hi-res mono: NOAA L1b banda 2 sola 0.5 km/px (4x zoom real). "
                 "⚠ ACTUALMENTE NO DISPONIBLE en cloud (OOM workflow GH free) — "
                 "cae a RAMMB normal. Requiere localhost del observatorio.",
        )
    with cols_top[2]:
        if "mono" in hires_mode:
            st.caption("⚠ Mono 0.5km/px no disponible cloud — vas a ver RAMMB. "
                       "Requiere correr local desde el observatorio.")
        elif hires_mode == "Hi-res color (1 km/px)":
            st.caption("ℹ Color 1km/px = TrueColor diurno o IR nocturno · "
                       "1.7x mejor que RAMMB.")

    use_hires = hires_mode != "RAMMB normal"
    hires_mode_arg = "mono_05km" if "mono" in hires_mode else "color"
    _grid_fragment(product, use_hires=use_hires, hires_mode=hires_mode_arg)
    st.markdown(
        "<div style='text-align:center; color:#445566; font-size:0.75rem; "
        "margin-top:0.8rem; padding-top:0.5rem; border-top:1px solid #223;'>"
        "<i>Sin metricas automaticas. Si algo llama la atencion en una "
        "miniatura, ir a 'Modo Guardia → Volcán' para ver con detalle.</i></div>",
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
        "padding-bottom:0.6rem; border-bottom:2px solid #223; margin-bottom:0.6rem;'>"
        "<div style='font-size:1.5rem; font-weight:800; color:#ff6644;'>"
        "🗺 MOSAICO CHILE</div>"
        "<div style='font-size:0.85rem; color:#7a8a9a;'>"
        "8 prioritarios · Ash RGB · zoom volcan</div></div>",
        unsafe_allow_html=True,
    )
    _live_panel()
