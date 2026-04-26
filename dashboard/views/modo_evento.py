"""Modo Evento — vista focalizada para crisis volcánica activa.

Filosofia: cuando hay un evento volcánico activo (erupción confirmada,
incremento de hot spots, alerta SERNAGEOMIN), el operador no quiere
navegar 6 tabs. Quiere UNA pantalla con TODO sobre ese volcán.

Layout: cabecera grande con el nombre del volcán + countdown desde
'inicio del evento' (que el usuario marca con un botón). Abajo:
imagen Ash RGB grande, tabla de hot spots NOAA recientes, viento GFS,
mini animación, estado VOLCAT si hay altura.

Usar via permalink: ?vista=evento&volcan=Villarrica para arrancar
inmediatamente sobre ese volcán (compartible por mail/Slack al equipo).
"""

import logging
from datetime import datetime, timedelta, timezone

import numpy as np
import plotly.graph_objects as go
import streamlit as st

from dashboard.utils import fmt_chile, parse_rammb_ts
from src.fetch.goes_fdcf import HotSpot, fetch_latest_hotspots
from src.fetch.rammb_slider import (
    fetch_frame_robust, get_latest_timestamps, ZOOM_VOLCAN, ZOOM_ZONE,
)
from src.fetch.wind_data import fetch_wind_point
from src.volcanos import PRIORITY_VOLCANOES, get_volcano

logger = logging.getLogger(__name__)

REFRESH_SECONDS = 60
RADIUS_DEG = 0.4
EVENT_BBOX_KM = 50  # radio para hot spots considerados del evento

PRODUCTS_GRID = [
    ("eumetsat_ash", "🌋 Ash RGB", "#ff6644"),
    ("geocolor", "🌍 GeoColor", "#4a9eff"),
    ("jma_so2", "🟢 SO2 RGB", "#44dd88"),
]


@st.cache_data(ttl=30, show_spinner=False)
def _recent_ts(product: str, n: int = 3) -> list[str]:
    return get_latest_timestamps(product, n=n)


@st.cache_data(ttl=300, show_spinner=False)
def _hotspots_volcan(lat: float, lon: float):
    bounds = {
        "lat_min": lat - 0.6, "lat_max": lat + 0.6,
        "lon_min": lon - 0.6, "lon_max": lon + 0.6,
    }
    try:
        hs, dt = fetch_latest_hotspots(bounds=bounds, hours_back=2)
    except Exception:
        return [], None
    # Filtro radio real
    out = []
    for h in hs:
        dlat = (h.lat - lat) * 111.0
        dlon = (h.lon - lon) * 111.0 * float(np.cos(np.radians(lat)))
        d = float(np.hypot(dlat, dlon))
        if d <= EVENT_BBOX_KM:
            out.append((h, d))
    return out, dt


@st.cache_data(ttl=3600, show_spinner=False)
def _wind_volcan(lat: float, lon: float) -> dict:
    out = {}
    for level in ("300hPa", "500hPa", "850hPa"):
        w = fetch_wind_point(lat, lon, level=level)
        if w:
            out[level] = w
    return out


def _array_to_data_url(arr: np.ndarray) -> str:
    import base64
    import io
    from PIL import Image
    img = Image.fromarray(arr.astype(np.uint8))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def _ash_fig(img: np.ndarray | None, lat: float, lon: float, label: str,
             height: int = 580):
    fig = go.Figure()
    bounds = {
        "lat_min": lat - RADIUS_DEG, "lat_max": lat + RADIUS_DEG,
        "lon_min": lon - RADIUS_DEG, "lon_max": lon + RADIUS_DEG,
    }
    if img is not None:
        fig.add_layout_image(
            source=_array_to_data_url(img),
            xref="x", yref="y",
            x=bounds["lon_min"], y=bounds["lat_max"],
            sizex=2 * RADIUS_DEG, sizey=2 * RADIUS_DEG,
            sizing="stretch", layer="below",
        )
    fig.add_trace(go.Scatter(
        x=[lon], y=[lat], mode="markers",
        marker=dict(symbol="triangle-up", size=18, color="#00ffff",
                    line=dict(color="white", width=2)),
        showlegend=False, hoverinfo="skip",
    ))
    cos_lat = max(0.1, float(np.cos(np.radians(lat))))
    fig.update_xaxes(range=[bounds["lon_min"], bounds["lon_max"]],
                     showgrid=False, visible=False)
    fig.update_yaxes(range=[bounds["lat_min"], bounds["lat_max"]],
                     showgrid=False, visible=False,
                     scaleanchor="x", scaleratio=1.0 / cos_lat)
    fig.update_layout(
        title=dict(text=label, font=dict(size=12, color="#e0e0e0")),
        height=height, margin=dict(l=0, r=0, t=28, b=0),
        paper_bgcolor="#0a0e14", plot_bgcolor="#0a0e14",
    )
    if img is None:
        fig.add_annotation(text="Sin imagen", xref="paper", yref="paper",
                           x=0.5, y=0.5, showarrow=False,
                           font=dict(color="#7a8a9a", size=14))
    return fig


@st.fragment(run_every=f"{REFRESH_SECONDS}s")
def _live_panel(volcan_name: str):
    v = get_volcano(volcan_name)
    if v is None:
        st.error(f"Volcán '{volcan_name}' no encontrado.")
        return

    now = datetime.now(timezone.utc)

    # Inicio del evento (almacenado en session_state)
    event_start_key = f"event_start_{volcan_name}"
    event_started = st.session_state.get(event_start_key)

    # Header: nombre volcán + countdown si hay evento marcado
    countdown_html = ""
    if event_started:
        elapsed = now - event_started
        h = int(elapsed.total_seconds() // 3600)
        m = int((elapsed.total_seconds() % 3600) // 60)
        countdown_html = (
            f"<div style='font-size:0.85rem; color:#ff6644; margin-top:0.2rem;'>"
            f"⏱ Evento marcado hace <b>{h}h {m}min</b> "
            f"({event_started.strftime('%H:%M UTC')} / "
            f"{fmt_chile(event_started)} CL)</div>"
        )

    head_l, head_r = st.columns([3, 1])
    with head_l:
        st.markdown(
            f"<div style='background:linear-gradient(135deg, rgba(255,102,68,0.15), "
            f"rgba(255,102,68,0.05)); border-left:6px solid #ff4444; "
            f"padding:0.9rem 1.2rem; border-radius:6px;'>"
            f"<div style='font-size:2rem; font-weight:900; color:#ff6644; "
            f"line-height:1;'>🚨 {v.name}</div>"
            f"<div style='font-size:0.85rem; color:#9aaabb; margin-top:0.3rem;'>"
            f"{v.region} · elev {v.elevation} m · {v.lat}°, {v.lon}°</div>"
            f"{countdown_html}</div>",
            unsafe_allow_html=True,
        )
    with head_r:
        if event_started:
            if st.button("✖ Cerrar evento", use_container_width=True,
                         key=f"close_evt_{volcan_name}"):
                del st.session_state[event_start_key]
                st.rerun()
        else:
            if st.button("⏱ Marcar inicio del evento", type="primary",
                         use_container_width=True, key=f"start_evt_{volcan_name}"):
                st.session_state[event_start_key] = now
                st.rerun()

    # Bajar datos
    hotspots_with_d, hs_dt = _hotspots_volcan(v.lat, v.lon)
    wind = _wind_volcan(v.lat, v.lon)

    # KPI row
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        n_hs = len(hotspots_with_d)
        kc = "#ff4444" if n_hs > 0 else "#3fb950"
        st.markdown(
            f"<div style='background:#0f1418; border-left:4px solid {kc}; "
            f"padding:0.7rem 0.9rem; border-radius:4px;'>"
            f"<div style='font-size:0.7rem; color:#7a8a9a; text-transform:uppercase;'>"
            f"Hot spots NOAA ≤{EVENT_BBOX_KM} km</div>"
            f"<div style='font-size:1.6rem; font-weight:700; color:{kc};'>{n_hs}</div>"
            f"</div>", unsafe_allow_html=True,
        )
    with k2:
        if hotspots_with_d:
            max_frp = max(h.frp_mw for h, _d in hotspots_with_d)
            max_t = max(h.temp_k for h, _d in hotspots_with_d)
            kc = "#ff4444" if max_frp > 100 else "#d29922" if max_frp > 10 else "#3fb950"
            label = f"{max_frp:.0f} MW"
            sub = f"max T = {max_t:.0f} K"
        else:
            kc = "#888"; label = "—"; sub = "sin hot spot"
        st.markdown(
            f"<div style='background:#0f1418; border-left:4px solid {kc}; "
            f"padding:0.7rem 0.9rem; border-radius:4px;'>"
            f"<div style='font-size:0.7rem; color:#7a8a9a; text-transform:uppercase;'>"
            f"FRP máximo</div>"
            f"<div style='font-size:1.6rem; font-weight:700; color:{kc};'>{label}</div>"
            f"<div style='font-size:0.7rem; color:#556;'>{sub}</div>"
            f"</div>", unsafe_allow_html=True,
        )
    with k3:
        # Viento 500 hPa = nivel típico de plumas medias
        w500 = wind.get("500hPa")
        if w500:
            label = f"{w500['speed']:.0f} km/h"
            sub = f"desde {w500['direction']:.0f}° (500 hPa)"
            kc = "#4a9eff"
        else:
            kc = "#888"; label = "—"; sub = "GFS no respondió"
        st.markdown(
            f"<div style='background:#0f1418; border-left:4px solid {kc}; "
            f"padding:0.7rem 0.9rem; border-radius:4px;'>"
            f"<div style='font-size:0.7rem; color:#7a8a9a; text-transform:uppercase;'>"
            f"Viento dispersión</div>"
            f"<div style='font-size:1.6rem; font-weight:700; color:{kc};'>{label}</div>"
            f"<div style='font-size:0.7rem; color:#556;'>{sub}</div>"
            f"</div>", unsafe_allow_html=True,
        )
    with k4:
        st.markdown(
            f"<div style='background:#0f1418; border-left:4px solid #d29922; "
            f"padding:0.7rem 0.9rem; border-radius:4px;'>"
            f"<div style='font-size:0.7rem; color:#7a8a9a; text-transform:uppercase;'>"
            f"Render UTC / Chile</div>"
            f"<div style='font-size:1.0rem; font-weight:700; color:#e0e0e0;'>"
            f"{now.strftime('%H:%M:%S')} <span style='color:#7a8a9a;'>/</span> "
            f"{fmt_chile(now)}</div></div>", unsafe_allow_html=True,
        )

    # Grilla de 3 productos
    cols = st.columns(3)
    for i, (prod_id, label, _color) in enumerate(PRODUCTS_GRID):
        timestamps = _recent_ts(prod_id, n=3)
        if not timestamps:
            continue
        bounds = {
            "lat_min": v.lat - RADIUS_DEG, "lat_max": v.lat + RADIUS_DEG,
            "lon_min": v.lon - RADIUS_DEG, "lon_max": v.lon + RADIUS_DEG,
        }
        img, used_ts, used_zoom = fetch_frame_robust(
            prod_id, timestamps, bounds,
            zoom_preferred=ZOOM_VOLCAN, zoom_fallback=ZOOM_ZONE,
        )
        ts_label = "—"
        if used_ts:
            try:
                dt = parse_rammb_ts(used_ts)
                age = int((now - dt).total_seconds() / 60)
                ts_label = f"{dt.strftime('%H:%M UTC')} (hace {age}m)"
                if used_zoom == ZOOM_ZONE:
                    ts_label += " ⚠z3"
            except Exception:
                ts_label = used_ts
        with cols[i]:
            st.plotly_chart(
                _ash_fig(img, v.lat, v.lon,
                         f"{label} · {ts_label}", height=460),
                use_container_width=True,
                config={"displayModeBar": False},
            )

    # Tabla hot spots
    if hotspots_with_d:
        st.markdown("#### 🔥 Hot spots NOAA FDCF (≤50 km del cráter)")
        rows = []
        for h, d in sorted(hotspots_with_d, key=lambda x: x[1]):
            rows.append({
                "Distancia": f"{d:.1f} km",
                "T (K)": f"{h.temp_k:.0f}",
                "FRP (MW)": f"{h.frp_mw:.1f}",
                "Confianza": h.confidence,
                "Lat": f"{h.lat:.3f}",
                "Lon": f"{h.lon:.3f}",
            })
        st.dataframe(rows, use_container_width=True, hide_index=True)
        if hs_dt:
            st.caption(
                f"📡 Scan FDCF: {hs_dt.strftime('%Y-%m-%d %H:%M UTC')} · "
                f"hace {int((now - hs_dt).total_seconds() / 60)} min"
            )

    # Footer instrucciones
    st.markdown(
        "<div style='text-align:center; color:#445566; font-size:0.78rem; "
        "margin-top:1rem; padding-top:0.6rem; border-top:1px solid #223;'>"
        "Compartible: copiá la URL de esta pestaña — incluye <b>?vista=evento&volcan=...</b> "
        "para abrir directo en este volcán.</div>",
        unsafe_allow_html=True,
    )


def render():
    st.markdown(
        """
        <style>
          [data-testid="stHeader"] { background: rgba(0,0,0,0); height: 0; }
          .block-container { padding-top: 0.5rem !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        "<div style='display:flex; justify-content:space-between; align-items:center; "
        "padding-bottom:0.4rem; border-bottom:2px solid #223; margin-bottom:0.7rem;'>"
        "<div style='font-size:1.5rem; font-weight:800; color:#ff4444;'>"
        "🚨 MODO EVENTO</div>"
        "<div style='font-size:0.85rem; color:#7a8a9a;'>"
        "Crisis volcánica activa · una pantalla, todo el contexto</div></div>",
        unsafe_allow_html=True,
    )

    # Selector volcán + permalink
    qp = st.query_params
    initial = qp.get("volcan", "Villarrica")
    if initial not in PRIORITY_VOLCANOES:
        initial = "Villarrica"

    cols = st.columns([2, 1])
    with cols[0]:
        volcan = st.selectbox(
            "Volcán en evento",
            options=PRIORITY_VOLCANOES,
            index=PRIORITY_VOLCANOES.index(initial),
            key="evento_volcan",
        )
    with cols[1]:
        st.markdown(
            "<div style='font-size:0.72rem; color:#556; padding-top:0.6rem;'>"
            "Auto-refresh 60s · KPIs + 3 productos + hotspots</div>",
            unsafe_allow_html=True,
        )

    # Sincronizar URL
    if qp.get("volcan") != volcan:
        st.query_params["volcan"] = volcan

    _live_panel(volcan)
