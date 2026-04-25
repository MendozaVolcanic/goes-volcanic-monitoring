"""Modo Guardia: vista full-screen para sala de operaciones SERNAGEOMIN.

Diseno: una pantalla, un proposito. Ash RGB Chile + hot spots overlay +
serie de tiempo del volcan prioritario activo. Auto-refresh 60s — si hay
scan nuevo en RAMMB, se ve sin tocar nada.

NO toca las vistas existentes. Tab independiente para validar antes de
mover features a las views principales.

Decisiones:
- Refresco 60s: chequea si hay timestamp nuevo (request liviano JSON).
  Solo re-renderiza imagen si cambio. RAMMB cadencia real es 10 min asi
  que mas frecuente seria gastar requests sin info nueva.
- Volcan default Villarrica (mas activo historicamente). Selector para
  cambiar manual si turno detecta actividad en otro lado.
- Layout grande, contraste alto, font grande — pensado para verse desde
  el otro lado de la sala.
"""

import logging
from datetime import datetime, timezone

import numpy as np
import plotly.graph_objects as go
import streamlit as st

from dashboard.utils import fmt_chile, parse_rammb_ts
from src.fetch.goes_fdcf import HotSpot, fetch_latest_hotspots
from src.fetch.rammb_slider import (
    CHILE_REPROJECTED_BOUNDS, CHILE_TILES_Z2,
    fetch_stitched_frame, get_latest_timestamps, reproject_to_latlon,
)
from src.fetch.timeseries import fetch_volcano_timeseries
from src.volcanos import PRIORITY_VOLCANOES, get_volcano

logger = logging.getLogger(__name__)

REFRESH_SECONDS = 60
DEFAULT_VOLCANO = "Villarrica"
TIMESERIES_HOURS = 6  # ventana de la serie en la pantalla


# ── Cache helpers ────────────────────────────────────────────────────

@st.cache_data(ttl=30, show_spinner=False)
def _latest_ts() -> str | None:
    """Timestamp mas reciente Ash RGB. Cache 30s — liviano (~1 KB JSON)."""
    times = get_latest_timestamps("eumetsat_ash", n=1)
    return times[0] if times else None


@st.cache_data(ttl=7200, show_spinner=False)
def _ash_chile_frame(ts: str) -> dict | None:
    """Frame Chile completo Ash RGB para un timestamp dado.

    Cache 2h por ts: una vez bajado un scan no se vuelve a pedir nunca.
    """
    img = fetch_stitched_frame(
        "eumetsat_ash", ts, zoom=2,
        tile_rows=CHILE_TILES_Z2["rows"], tile_cols=CHILE_TILES_Z2["cols"],
    )
    if img is None:
        return None
    img = reproject_to_latlon(img, col_start=678, row_start=1356)
    dt = parse_rammb_ts(ts)
    return {"image": img, "dt": dt, "bounds": CHILE_REPROJECTED_BOUNDS}


@st.cache_data(ttl=300, show_spinner=False)
def _hotspots_chile() -> tuple[list[HotSpot], datetime | None]:
    """Hot spots FDCF en bbox Chile. Cache 5 min."""
    chile_bbox = {
        "lat_min": CHILE_REPROJECTED_BOUNDS["lat_min"],
        "lat_max": CHILE_REPROJECTED_BOUNDS["lat_max"],
        "lon_min": CHILE_REPROJECTED_BOUNDS["lon_min"],
        "lon_max": CHILE_REPROJECTED_BOUNDS["lon_max"],
    }
    try:
        return fetch_latest_hotspots(bounds=chile_bbox, hours_back=1)
    except Exception as e:
        logger.warning("hotspots fallo: %s", e)
        return [], None


@st.cache_data(ttl=600, show_spinner=False)
def _volcano_series(volcan: str) -> list:
    """Serie 6h ash% para el volcan seleccionado. Cache 10 min."""
    v = get_volcano(volcan)
    if v is None:
        return []
    n_frames = TIMESERIES_HOURS * 6  # 6 scans/h
    try:
        return fetch_volcano_timeseries(
            v.lat, v.lon, "eumetsat_ash", n_frames=n_frames,
        )
    except Exception as e:
        logger.warning("series %s fallo: %s", volcan, e)
        return []


# ── Render principal ─────────────────────────────────────────────────

def _render_ash_with_hotspots(frame: dict, hotspots: list[HotSpot], volcan_name: str):
    """Imshow Ash RGB Chile con triangulos de hotspots + marcador del volcan."""
    img = frame["image"]
    b = frame["bounds"]
    fig = go.Figure()
    fig.add_layout_image(
        source=_array_to_data_url(img),
        xref="x", yref="y",
        x=b["lon_min"], y=b["lat_max"],
        sizex=b["lon_max"] - b["lon_min"],
        sizey=b["lat_max"] - b["lat_min"],
        sizing="stretch", layer="below", opacity=1.0,
    )
    # Marcador volcan seleccionado
    v = get_volcano(volcan_name)
    if v is not None:
        fig.add_trace(go.Scatter(
            x=[v.lon], y=[v.lat], mode="markers+text",
            marker=dict(symbol="triangle-up", size=18, color="#00ffff",
                        line=dict(color="white", width=2)),
            text=[volcan_name], textposition="top center",
            textfont=dict(size=14, color="#00ffff"), name=volcan_name,
            hovertemplate=f"<b>{volcan_name}</b><br>Lat {v.lat}<br>Lon {v.lon}<extra></extra>",
        ))
    # Hot spots
    if hotspots:
        lats = [h.lat for h in hotspots]
        lons = [h.lon for h in hotspots]
        temps = [f"{h.temp_k:.0f} K, FRP {h.frp_mw:.1f} MW ({h.confidence})"
                 for h in hotspots]
        fig.add_trace(go.Scatter(
            x=lons, y=lats, mode="markers",
            marker=dict(symbol="diamond", size=12, color="#ff3300",
                        line=dict(color="white", width=1)),
            text=temps, hoverinfo="text", name=f"Hot spots ({len(hotspots)})",
        ))

    fig.update_xaxes(range=[b["lon_min"], b["lon_max"]],
                     showgrid=False, title="")
    fig.update_yaxes(range=[b["lat_min"], b["lat_max"]],
                     showgrid=False, title="", scaleanchor="x", scaleratio=1)
    fig.update_layout(
        height=620, margin=dict(l=0, r=0, t=10, b=0),
        paper_bgcolor="#0a0e14", plot_bgcolor="#0a0e14",
        font=dict(color="#e0e0e0", size=13),
        legend=dict(bgcolor="rgba(10,14,20,0.7)", bordercolor="#334",
                    borderwidth=1, x=0.02, y=0.02),
    )
    return fig


def _array_to_data_url(arr: np.ndarray) -> str:
    """numpy uint8 (H,W,3) -> data URL para Plotly layout_image."""
    import base64
    import io
    from PIL import Image
    img = Image.fromarray(arr.astype(np.uint8))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def _render_timeseries(points: list, volcan: str):
    """Plot lineal % ash en ventana TIMESERIES_HOURS."""
    avail = [p for p in points if p.available]
    fig = go.Figure()
    if avail:
        xs = [p.dt for p in avail]
        ys = [p.metric * 100 for p in avail]
        fig.add_trace(go.Scatter(
            x=xs, y=ys, mode="lines+markers",
            line=dict(color="#ff6644", width=2),
            marker=dict(size=5, color="#ff6644"),
            fill="tozeroy", fillcolor="rgba(255,102,68,0.18)",
            hovertemplate="%{x|%H:%M UTC}<br>%{y:.1f}%<extra></extra>",
        ))
    fig.update_layout(
        title=dict(
            text=f"<b>{volcan}</b> — % píxeles con firma de ceniza ({TIMESERIES_HOURS}h)",
            font=dict(size=15, color="#e0e0e0"),
        ),
        height=240, margin=dict(l=50, r=20, t=40, b=40),
        paper_bgcolor="#0a0e14", plot_bgcolor="#0a0e14",
        font=dict(color="#e0e0e0"),
        xaxis=dict(title="UTC", gridcolor="#223"),
        yaxis=dict(title="% pixeles", gridcolor="#223", rangemode="tozero"),
    )
    return fig


@st.fragment(run_every=f"{REFRESH_SECONDS}s")
def _live_panel(volcan_name: str):
    """Fragment con auto-refresh — solo este bloque se re-renderiza cada 60s."""
    ts = _latest_ts()
    if not ts:
        st.error("RAMMB no respondio. Reintentando en 60s…")
        return

    frame = _ash_chile_frame(ts)
    hotspots, hs_dt = _hotspots_chile()
    series = _volcano_series(volcan_name)

    now = datetime.now(timezone.utc)

    # ── Header KPIs grandes ──
    c1, c2, c3, c4 = st.columns(4)
    if frame is not None:
        scan_dt = frame["dt"]
        scan_age_min = (now - scan_dt).total_seconds() / 60
        scan_color = "#44dd88" if scan_age_min < 15 else "#ffaa44" if scan_age_min < 30 else "#ff4444"
    else:
        scan_age_min = -1
        scan_color = "#888"
    with c1:
        st.markdown(
            f"<div style='background:#0f1418; border-left:4px solid {scan_color}; "
            f"padding:0.8rem 1rem; border-radius:4px;'>"
            f"<div style='font-size:0.7rem; color:#7a8a9a; text-transform:uppercase; "
            f"letter-spacing:0.1em;'>Ultimo scan</div>"
            f"<div style='font-size:1.6rem; font-weight:700; color:{scan_color};'>"
            f"{'hace ' + str(int(scan_age_min)) + ' min' if scan_age_min >= 0 else 'sin datos'}"
            f"</div></div>",
            unsafe_allow_html=True,
        )
    with c2:
        n_hs = len(hotspots)
        hs_color = "#ff4444" if n_hs > 0 else "#44dd88"
        st.markdown(
            f"<div style='background:#0f1418; border-left:4px solid {hs_color}; "
            f"padding:0.8rem 1rem; border-radius:4px;'>"
            f"<div style='font-size:0.7rem; color:#7a8a9a; text-transform:uppercase; "
            f"letter-spacing:0.1em;'>Hot spots Chile</div>"
            f"<div style='font-size:1.6rem; font-weight:700; color:{hs_color};'>{n_hs}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )
    with c3:
        avail = [p for p in series if p.available]
        if avail:
            current = avail[-1].metric * 100
            peak = max(p.metric for p in avail) * 100
            ash_color = "#ff4444" if current > 5 else "#ffaa44" if current > 1 else "#44dd88"
        else:
            current, peak, ash_color = 0, 0, "#888"
        st.markdown(
            f"<div style='background:#0f1418; border-left:4px solid {ash_color}; "
            f"padding:0.8rem 1rem; border-radius:4px;'>"
            f"<div style='font-size:0.7rem; color:#7a8a9a; text-transform:uppercase; "
            f"letter-spacing:0.1em;'>{volcan_name} ash %</div>"
            f"<div style='font-size:1.6rem; font-weight:700; color:{ash_color};'>"
            f"{current:.1f}% <span style='font-size:0.9rem; color:#556;'>"
            f"(pico {peak:.1f}%)</span></div></div>",
            unsafe_allow_html=True,
        )
    with c4:
        st.markdown(
            f"<div style='background:#0f1418; border-left:4px solid #4a9eff; "
            f"padding:0.8rem 1rem; border-radius:4px;'>"
            f"<div style='font-size:0.7rem; color:#7a8a9a; text-transform:uppercase; "
            f"letter-spacing:0.1em;'>Ahora UTC / Chile</div>"
            f"<div style='font-size:1.1rem; font-weight:700; color:#e0e0e0;'>"
            f"{now.strftime('%H:%M:%S')} <span style='color:#7a8a9a;'>/</span> "
            f"{fmt_chile(now)}</div></div>",
            unsafe_allow_html=True,
        )

    # ── Mapa principal Ash + hotspots ──
    if frame is not None:
        st.plotly_chart(
            _render_ash_with_hotspots(frame, hotspots, volcan_name),
            use_container_width=True,
            config={"displayModeBar": False},
        )
    else:
        st.warning("Imagen Ash RGB no disponible en este ciclo.")

    # ── Serie de tiempo ──
    st.plotly_chart(
        _render_timeseries(series, volcan_name),
        use_container_width=True,
        config={"displayModeBar": False},
    )

    # ── Footer info refresco ──
    st.markdown(
        f"<div style='text-align:right; color:#445566; font-size:0.75rem; "
        f"margin-top:0.5rem;'>Auto-refresh cada {REFRESH_SECONDS}s · "
        f"GOES-19 cadencia real 10 min · "
        f"render @ {now.strftime('%H:%M:%S')} UTC</div>",
        unsafe_allow_html=True,
    )


def render():
    """Entry point para app.py."""
    # CSS especifico modo guardia: compacta header, esconde menu hamburguesa
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
        "padding-bottom:0.6rem; border-bottom:2px solid #223;'>"
        "<div style='font-size:1.6rem; font-weight:800; color:#ff6644;'>"
        "🛡 MODO GUARDIA</div>"
        "<div style='font-size:0.85rem; color:#7a8a9a;'>"
        "Sala de operaciones · GOES-19 · Chile</div></div>",
        unsafe_allow_html=True,
    )

    # Selector volcan (fuera del fragment para que no se resetee con el refresh)
    cols = st.columns([3, 1])
    with cols[1]:
        volcan = st.selectbox(
            "Volcan a monitorear",
            options=PRIORITY_VOLCANOES,
            index=PRIORITY_VOLCANOES.index(DEFAULT_VOLCANO)
            if DEFAULT_VOLCANO in PRIORITY_VOLCANOES else 0,
            label_visibility="collapsed",
        )

    _live_panel(volcan)
