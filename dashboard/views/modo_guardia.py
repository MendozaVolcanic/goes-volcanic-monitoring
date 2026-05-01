"""Modo Guardia: vista full-screen para sala de operaciones SERNAGEOMIN.

FILOSOFIA: Mostrar imagen lo mas limpia posible. NO inventar metricas
automaticas — el experto aplica su criterio sobre el dato crudo. Esto
sigue la linea de NASA Worldview, RAMMB Slider, Himawari Realtime.

Auto-refresh 60s — si hay scan nuevo en RAMMB, se ve sin tocar nada.

NO toca las vistas existentes. Tab independiente para validar antes de
mover features a las views principales.

Decisiones:
- Refresco 60s: chequea si hay timestamp nuevo (request liviano JSON).
  Solo re-renderiza imagen si cambio. RAMMB cadencia real es 10 min asi
  que mas frecuente seria gastar requests sin info nueva.
- Volcan default Villarrica (mas activo historicamente). Selector para
  cambiar manual.
- KPIs: solo datos validados externamente (edad de scan, hot spots
  NOAA FDCF). NO calculamos % de ceniza propio — la receta EUMETSAT
  RGB tiene falsos positivos enormes con cirros y nieve sobre Andes.
"""

import logging
from datetime import datetime, timezone

import numpy as np
import plotly.graph_objects as go
import streamlit as st

from dashboard.map_helpers import add_chile_border
from dashboard.utils import fmt_chile, parse_rammb_ts
from src.fetch.goes_fdcf import HotSpot, fetch_latest_hotspots
from src.fetch.rammb_slider import (
    CHILE_REPROJECTED_BOUNDS, CHILE_TILES_Z2,
    fetch_stitched_frame, get_latest_timestamps, reproject_to_latlon,
)
from src.volcanos import PRIORITY_VOLCANOES, get_volcano

logger = logging.getLogger(__name__)

REFRESH_SECONDS = 60
ROTATION_SECONDS = 10
DEFAULT_VOLCANO = "Villarrica"

# Productos disponibles en sub-tab Chile (mismo set que sub-tab Zonas).
CHILE_PRODUCT_OPTIONS = {
    "eumetsat_ash": "Ash RGB",
    "geocolor": "GeoColor",
    "jma_so2": "SO2 RGB",
}
CHILE_PRODUCT_LIST = list(CHILE_PRODUCT_OPTIONS.keys())


# ── Cache helpers ────────────────────────────────────────────────────

@st.cache_data(ttl=30, show_spinner=False)
def _latest_ts(product: str = "eumetsat_ash") -> str | None:
    """Timestamp mas reciente para el producto. Cache 30s (~1 KB JSON)."""
    times = get_latest_timestamps(product, n=1)
    return times[0] if times else None


@st.cache_data(ttl=7200, show_spinner=False)
def _chile_frame(product: str, ts: str) -> dict | None:
    """Frame Chile completo para producto+ts. Cache 2h: scan no se re-baja."""
    img = fetch_stitched_frame(
        product, ts, zoom=2,
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


def _nearest_hotspot(hotspots: list[HotSpot], lat: float, lon: float
                     ) -> tuple[HotSpot | None, float]:
    """Hotspot mas cercano al volcan + distancia en km. Devuelve (None, inf) si lista vacia."""
    if not hotspots:
        return None, float("inf")
    best, best_d = None, float("inf")
    for h in hotspots:
        dlat = (h.lat - lat) * 111.0
        dlon = (h.lon - lon) * 111.0 * float(np.cos(np.radians(lat)))
        d = float(np.hypot(dlat, dlon))
        if d < best_d:
            best, best_d = h, d
    return best, best_d


# ── Render ───────────────────────────────────────────────────────────

def _array_to_data_url(arr: np.ndarray) -> str:
    """numpy uint8 (H,W,3) -> data URL para Plotly layout_image."""
    import base64
    import io
    from PIL import Image
    img = Image.fromarray(arr.astype(np.uint8))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def _hotspot_marker_size(frp_mw: float) -> float:
    """Tamano de marker proporcional a FRP. Min 8 (FRP=0), max ~24 (FRP>=200 MW).

    Escala raiz cuadrada para que un FRP de 50 MW destaque vs 5 MW sin que
    100 MW se salga de pantalla. Validado contra eventos Sangay/Reventador.
    """
    return float(8 + min(16, np.sqrt(max(0.0, frp_mw)) * 1.6))


def _add_distance_rings(fig, lat: float, lon: float,
                        radii_km: tuple[int, ...] = (5, 10, 25, 50)) -> None:
    """Dibuja anillos de distancia alrededor de (lat, lon). Util para medir
    largo de pluma y dispersion. Compensa estiramiento longitudinal.
    """
    cos_lat = max(0.1, float(np.cos(np.radians(lat))))
    theta = np.linspace(0, 2 * np.pi, 60)
    for r_km in radii_km:
        dlat = (r_km / 111.0) * np.sin(theta)
        dlon = (r_km / 111.0 / cos_lat) * np.cos(theta)
        fig.add_trace(go.Scatter(
            x=lon + dlon, y=lat + dlat, mode="lines",
            line=dict(color="rgba(0,255,255,0.35)", width=1, dash="dot"),
            hoverinfo="skip", showlegend=False,
        ))
        # Label de la distancia arriba del anillo (norte del crater)
        fig.add_annotation(
            x=lon, y=lat + (r_km / 111.0), text=f"{r_km} km",
            showarrow=False, font=dict(size=9, color="rgba(0,255,255,0.6)"),
            bgcolor="rgba(0,0,0,0.4)", borderpad=1,
        )


def _render_chile_with_hotspots(frame: dict, hotspots: list[HotSpot],
                                 volcan_name: str, product: str,
                                 show_rings: bool = False):
    """Imshow Chile producto + hot spots (size por FRP) + marker volcan + rings."""
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
    v = get_volcano(volcan_name)
    if v is not None:
        if show_rings:
            _add_distance_rings(fig, v.lat, v.lon)
        fig.add_trace(go.Scatter(
            x=[v.lon], y=[v.lat], mode="markers+text",
            marker=dict(symbol="triangle-up", size=18, color="#00ffff",
                        line=dict(color="white", width=2)),
            text=[volcan_name], textposition="top center",
            textfont=dict(size=14, color="#00ffff"), name=volcan_name,
            hovertemplate=f"<b>{volcan_name}</b><br>Lat {v.lat}<br>Lon {v.lon}<extra></extra>",
        ))
    if hotspots:
        lats = [h.lat for h in hotspots]
        lons = [h.lon for h in hotspots]
        sizes = [_hotspot_marker_size(h.frp_mw) for h in hotspots]
        temps = [f"{h.temp_k:.0f} K · FRP {h.frp_mw:.1f} MW ({h.confidence})"
                 for h in hotspots]
        fig.add_trace(go.Scatter(
            x=lons, y=lats, mode="markers",
            marker=dict(symbol="diamond", size=sizes, color="#ff3300",
                        line=dict(color="white", width=1)),
            text=temps, hoverinfo="text",
            name=f"Hot spots NOAA ({len(hotspots)}) — size = FRP",
        ))

    # Frontera de Chile (overlay en blanco semi-transparente)
    add_chile_border(fig)

    fig.update_xaxes(range=[b["lon_min"], b["lon_max"]],
                     showgrid=False, title="")
    fig.update_yaxes(range=[b["lat_min"], b["lat_max"]],
                     showgrid=False, title="", scaleanchor="x", scaleratio=1)
    fig.update_layout(
        height=900, margin=dict(l=0, r=0, t=5, b=0),
        paper_bgcolor="#0a0e14", plot_bgcolor="#0a0e14",
        font=dict(color="#e0e0e0", size=13),
        legend=dict(bgcolor="rgba(10,14,20,0.7)", bordercolor="#334",
                    borderwidth=1, x=0.02, y=0.02),
    )
    return fig


@st.fragment(run_every=f"{REFRESH_SECONDS}s")
def _live_panel(volcan_name: str, product: str = "eumetsat_ash",
                show_rings: bool = False):
    """Fragment con auto-refresh — solo este bloque se re-renderiza cada 60s."""
    ts = _latest_ts(product)
    if not ts:
        st.error("RAMMB no respondio. Reintentando en 60s…")
        return

    frame = _chile_frame(product, ts)
    hotspots, _hs_dt = _hotspots_chile()
    v = get_volcano(volcan_name)

    now = datetime.now(timezone.utc)

    # ── Status banner global con edad de scan ──
    if frame is not None:
        age_min = int((now - frame["dt"]).total_seconds() / 60)
        if age_min < 15:
            bnr_color, bnr_msg = "#3fb950", f"Scan hace {age_min} min · OK"
        elif age_min < 30:
            bnr_color, bnr_msg = "#d29922", f"Scan hace {age_min} min · RAMMB lento"
        else:
            bnr_color, bnr_msg = "#ff4444", f"Scan hace {age_min} min · datos atrasados"
    else:
        bnr_color, bnr_msg = "#888", "Sin scan disponible"
    st.markdown(
        f"<div style='background:#0f1418; border-left:4px solid {bnr_color}; "
        f"padding:0.4rem 0.8rem; border-radius:4px; margin-bottom:0.4rem; "
        f"display:flex; justify-content:space-between;'>"
        f"<span style='color:#e0e0e0;'>{CHILE_PRODUCT_OPTIONS.get(product, product)} · "
        f"Chile completo · seguimiento {volcan_name}</span>"
        f"<span style='color:{bnr_color}; font-weight:600;'>{bnr_msg}</span>"
        f"</div>",
        unsafe_allow_html=True,
    )

    # ── Header KPIs (todos basados en datos validados externamente) ──
    c1, c2, c3, c4 = st.columns(4)

    # KPI 1: edad del ultimo scan
    if frame is not None:
        scan_age_min = (now - frame["dt"]).total_seconds() / 60
        scan_color = "#44dd88" if scan_age_min < 15 else "#ffaa44" if scan_age_min < 30 else "#ff4444"
        scan_label = f"hace {int(scan_age_min)} min"
    else:
        scan_color = "#888"
        scan_label = "sin datos"
    with c1:
        st.markdown(
            f"<div style='background:#0f1418; border-left:4px solid {scan_color}; "
            f"padding:0.8rem 1rem; border-radius:4px;'>"
            f"<div style='font-size:0.7rem; color:#7a8a9a; text-transform:uppercase; "
            f"letter-spacing:0.1em;'>Ultimo scan GOES-19</div>"
            f"<div style='font-size:1.6rem; font-weight:700; color:{scan_color};'>"
            f"{scan_label}</div></div>",
            unsafe_allow_html=True,
        )

    # KPI 2: hot spots Chile (producto NOAA FDCF, validado)
    n_hs = len(hotspots)
    hs_color = "#ff4444" if n_hs > 0 else "#44dd88"
    with c2:
        st.markdown(
            f"<div style='background:#0f1418; border-left:4px solid {hs_color}; "
            f"padding:0.8rem 1rem; border-radius:4px;'>"
            f"<div style='font-size:0.7rem; color:#7a8a9a; text-transform:uppercase; "
            f"letter-spacing:0.1em;'>Hot spots Chile (NOAA FDCF)</div>"
            f"<div style='font-size:1.6rem; font-weight:700; color:{hs_color};'>"
            f"{n_hs}</div></div>",
            unsafe_allow_html=True,
        )

    # KPI 3: distancia al hot spot mas cercano del volcan seleccionado
    nearest_hs, dist_km = _nearest_hotspot(hotspots, v.lat, v.lon) if v else (None, float("inf"))
    if nearest_hs is not None and dist_km < 100:
        nh_color = "#ff4444" if dist_km < 10 else "#ffaa44" if dist_km < 30 else "#44dd88"
        nh_label = f"{dist_km:.0f} km"
        nh_sub = f"T={nearest_hs.temp_k:.0f}K, FRP {nearest_hs.frp_mw:.1f}MW"
    else:
        nh_color = "#44dd88"
        nh_label = "sin hotspots"
        nh_sub = "≤100 km del volcán"
    with c3:
        st.markdown(
            f"<div style='background:#0f1418; border-left:4px solid {nh_color}; "
            f"padding:0.8rem 1rem; border-radius:4px;'>"
            f"<div style='font-size:0.7rem; color:#7a8a9a; text-transform:uppercase; "
            f"letter-spacing:0.1em;'>{volcan_name} — hot spot mas cercano</div>"
            f"<div style='font-size:1.6rem; font-weight:700; color:{nh_color};'>"
            f"{nh_label}</div>"
            f"<div style='font-size:0.7rem; color:#556;'>{nh_sub}</div></div>",
            unsafe_allow_html=True,
        )

    # KPI 4: hora UTC / Chile
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

    # ── Mapa principal Chile + hotspots ──
    if frame is not None:
        st.plotly_chart(
            _render_chile_with_hotspots(frame, hotspots, volcan_name, product,
                                         show_rings=show_rings),
            use_container_width=True,
            config={"displayModeBar": False},
        )
    else:
        st.warning(f"Imagen {CHILE_PRODUCT_OPTIONS.get(product, product)} "
                    "no disponible en este ciclo.")

    # ── Footer info ──
    st.markdown(
        f"<div style='text-align:right; color:#445566; font-size:0.75rem; "
        f"margin-top:0.5rem;'>"
        f"Auto-refresh cada {REFRESH_SECONDS}s · GOES-19 cadencia real 10 min · "
        f"render @ {now.strftime('%H:%M:%S')} UTC<br>"
        f"<i>Imagenes Ash RGB y hot spots NOAA FDCF — sin metricas automaticas. "
        f"La interpretacion queda al criterio del experto.</i></div>",
        unsafe_allow_html=True,
    )


@st.fragment(run_every=f"{ROTATION_SECONDS}s")
def _rotating_chile_tv(volcan_name: str, show_rings: bool = True,
                        session_key: str = "tv_chile_rot_idx"):
    """Modo Sala Chile: rota productos cada 10s sobre Chile completo.

    chrome=False: solo el mapa, sin banners (TV puro). Leyenda compacta
    arriba que cambia con el producto.
    """
    if session_key not in st.session_state:
        st.session_state[session_key] = 0
    idx = st.session_state[session_key] % len(CHILE_PRODUCT_LIST)
    current = CHILE_PRODUCT_LIST[idx]
    st.session_state[session_key] = (idx + 1) % len(CHILE_PRODUCT_LIST)

    ts = _latest_ts(current)
    frame = _chile_frame(current, ts) if ts else None
    hotspots, _ = _hotspots_chile()

    from dashboard.map_helpers import render_compact_legend, render_scan_status_badge
    render_compact_legend(
        current,
        extra_left=("<span style='color:#ff6644; font-weight:700; "
                    "margin-right:0.4rem;'>🔄</span>"),
        extra_right=render_scan_status_badge(
            frame["dt"] if frame else None, ROTATION_SECONDS,
        ),
    )

    if not ts:
        st.error("RAMMB no respondió.")
        return
    if frame is None:
        st.warning(f"Imagen {CHILE_PRODUCT_OPTIONS[current]} no disponible.")
        return
    fig = _render_chile_with_hotspots(frame, hotspots, volcan_name, current,
                                       show_rings=show_rings)
    # Modo Sala: usar todo el alto disponible
    fig.update_layout(height=920, margin=dict(l=0, r=0, t=2, b=0))
    st.plotly_chart(fig, use_container_width=True,
                    config={"displayModeBar": False})


def _chile_subtab():
    """Sub-tab Chile: live panel con selector volcan + producto + anillos + boton sala."""
    cols = st.columns([1.6, 1.0, 1.0, 1.5])
    with cols[0]:
        volcan = st.selectbox(
            "Volcan a monitorear",
            options=PRIORITY_VOLCANOES,
            index=PRIORITY_VOLCANOES.index(DEFAULT_VOLCANO)
            if DEFAULT_VOLCANO in PRIORITY_VOLCANOES else 0,
            label_visibility="collapsed",
            key="mg_chile_selector",
        )
    with cols[1]:
        product = st.selectbox(
            "Producto",
            options=list(CHILE_PRODUCT_OPTIONS.keys()),
            format_func=lambda k: CHILE_PRODUCT_OPTIONS[k],
            index=0, key="mg_chile_product",
            label_visibility="collapsed",
        )
    with cols[2]:
        show_rings = st.toggle(
            "⊙ Anillos", value=False, key="mg_chile_rings",
            help="Anillos 5/10/25/50 km alrededor del volcan seleccionado. "
                 "Util para medir largo de pluma en escala continental.",
        )
    with cols[3]:
        if st.button("🖥 Modo Sala · Chile (rotando productos)",
                     key="btn_sala_chile", type="primary",
                     use_container_width=True):
            _activate_tv("chile", volcan=volcan)
    _live_panel(volcan, product=product, show_rings=show_rings)


def _activate_tv(tv_value: str, **extra):
    """Setea query_params para entrar en modo TV puro y rerun.

    Mas confiable que <a target='_top'> con URLs relativas dentro del
    iframe sandbox de Streamlit Cloud.
    """
    st.query_params["vista"] = "guardia"
    st.query_params["fullscreen"] = "1"
    st.query_params["tv"] = tv_value
    for k, v in extra.items():
        st.query_params[k] = v
    st.rerun()


def _mosaico_subtab():
    """Sub-tab Mosaico: 8 prioritarios en grid 4x2."""
    from dashboard.views.mosaico_chile import _live_panel as mosaico_panel
    if st.button(
        "🖥 Modo Sala · Mosaico (rotando productos cada 10s)",
        key="btn_tv_mosaico", type="primary", use_container_width=False,
    ):
        _activate_tv("mosaico")
    mosaico_panel()


def _zonas_subtab():
    """Sub-tab Por Zona Volcánica: las 4 zonas. Boton TV puro = sin chrome."""
    from dashboard.views.zonas_fullscreen import (
        _grid_4_zonas, _rotating_grid_4_zonas, PRODUCT_OPTIONS, ROTATION_SECONDS,
    )

    # Boton activar TV puro — st.button con callback (mas confiable que <a>
    # con URLs relativas dentro del iframe sandbox de Streamlit Cloud)
    if st.button(
        "🖥 Modo Sala (4 zonas, rotando productos cada 10s)",
        key="btn_tv_zonas", type="primary", use_container_width=False,
    ):
        _activate_tv("1")
    st.caption(
        "Modo Sala = solo los 4 mapas a pantalla completa rotando productos. "
        "Sin header, sin sub-tabs, sin toolbar. Pensado para monitor 24/7. "
        "Botón ✖ arriba a la izquierda para salir."
    )

    # Modo normal con toolbar completa (no TV puro)
    cols = st.columns([1.2, 1.0, 1.2, 1.0, 1.0])
    with cols[0]:
        rotate = st.toggle(
            f"🔄 Auto-rotate ({ROTATION_SECONDS}s)", value=False, key="mg_zonas_rotate",
            help="Cicla GeoColor → Ash → SO2 cada 10s. Util para preview "
                 "de lo que se vera en el monitor de sala antes de mandarlo "
                 "a TV puro.",
        )
    with cols[1]:
        if not rotate:
            product = st.selectbox(
                "Producto",
                options=list(PRODUCT_OPTIONS.keys()),
                format_func=lambda k: PRODUCT_OPTIONS[k],
                index=0, key="mg_zonas_product",
                label_visibility="collapsed",
            )
        else:
            product = "eumetsat_ash"  # ignorado en rotate
            st.markdown(
                "<div style='color:#888; padding-top:0.5rem; font-size:0.8rem;'>"
                "(rotando)</div>",
                unsafe_allow_html=True,
            )
    with cols[2]:
        layout = st.radio(
            "Layout",
            ["1×4 (TV)", "2×2"],
            index=0, key="mg_zonas_layout",
            horizontal=True,
            label_visibility="collapsed",
        )
    with cols[3]:
        show_volc = st.toggle("🔺 Volcanes", value=True, key="mg_zonas_volc")
    with cols[4]:
        show_hs = st.toggle("🔥 Hot spots", value=True, key="mg_zonas_hs")

    layout_key = "1x4" if layout.startswith("1×4") else "2x2"
    height = 820 if layout_key == "1x4" else 720
    if rotate:
        _rotating_grid_4_zonas(show_volc, show_hs,
                                layout=layout_key, height=height,
                                session_key="mg_zonas_rot_idx")
    else:
        _grid_4_zonas(product, show_volc, show_hs,
                      layout=layout_key, height=height)


def _volcan_subtab():
    """Sub-tab Volcan: zoom volcan con 3 productos + viento + anillos + captura."""
    from dashboard.views.modo_guardia_volcan import _live_panel as volcan_panel
    # Toolbar
    cols = st.columns([2, 1, 1, 1, 1])
    with cols[0]:
        volcan = st.selectbox(
            "Volcan",
            options=PRIORITY_VOLCANOES,
            index=PRIORITY_VOLCANOES.index(DEFAULT_VOLCANO)
            if DEFAULT_VOLCANO in PRIORITY_VOLCANOES else 0,
            label_visibility="collapsed",
            key="mg_volcan_selector",
        )
    # Boton TV puro volcan (lleva el volcan seleccionado en query_params)
    if st.button(
        f"🖥 Modo Sala · {volcan} (3 productos)",
        key="btn_tv_volcan", type="primary", use_container_width=False,
    ):
        _activate_tv("volcan", volcan=volcan)
    with cols[1]:
        show_wind = st.toggle(
            "💨 Viento", value=False, key="mg_wind",
            help="Vectores GFS en 300/500/850 hPa sobre el crater. Cache 1h.",
        )
    with cols[2]:
        show_rings = st.toggle(
            "⊙ Anillos", value=True, key="mg_rings",
            help="Anillos de distancia 5/10/25/50 km desde el crater. "
                 "Útil para medir largo de pluma volcánica.",
        )
    with cols[3]:
        enable_capture = st.toggle(
            "📸 Captura", value=False, key="mg_capture",
            help="Boton de descarga PNG del momento actual.",
        )
    with cols[4]:
        st.markdown(
            "<div style='font-size:0.7rem; color:#556; padding-top:0.5rem;'>"
            "Refresh 60s</div>",
            unsafe_allow_html=True,
        )
    volcan_panel(volcan, show_wind, show_rings, enable_capture)


def render():
    """Entry point para app.py — Modo Guardia unificado con sub-tabs.

    Modo especial TV puro: se SKIPEA el header de modo guardia y los
    st.tabs. Solo se renderiza el grid elegido a pantalla completa.

    URL params:
      ?tv=1       o ?tv=zonas    -> 4 zonas rotando productos (default)
      ?tv=chile&volcan=X         -> Chile completo rotando productos + anillos
                                    alrededor del volcan seleccionado
      ?tv=mosaico                -> 8 prioritarios rotando productos + anillos
      ?tv=volcan&volcan=X        -> 1 volcan con 3 productos (sin rotacion,
                                    los 3 productos ya estan lado a lado)
    """
    tv_mode = st.query_params.get("tv", "")
    if tv_mode:
        # CSS para compactar el boton de salir + eliminar padding
        # excedente (espacio negro arriba que reportaba el user).
        st.markdown(
            """
            <style>
              .block-container {
                padding-top: 0.2rem !important;
                padding-bottom: 0.2rem !important;
              }
              [data-testid="stButton"] > button {
                padding: 0.15rem 0.6rem !important;
                font-size: 0.72rem !important;
                min-height: unset !important;
                height: 26px !important;
                line-height: 1 !important;
                border-radius: 4px !important;
              }
              [data-testid="stHorizontalBlock"] {
                gap: 0.1rem !important;
                margin-bottom: 0 !important;
                margin-top: 0 !important;
                padding: 0 !important;
              }
              /* Colapsa gap entre filas verticales — clave para grids 4x2 */
              [data-testid="stVerticalBlock"] {
                gap: 0.1rem !important;
                padding: 0 !important;
              }
              /* Plotly chart container sin padding */
              [data-testid="stPlotlyChart"] {
                margin: 0 !important;
                padding: 0 !important;
              }
              /* Element container compacto — padding 0 y sin margin */
              .element-container, [data-testid="element-container"],
              [data-testid="stElementContainer"] {
                margin: 0 !important;
                padding: 0 !important;
                min-height: 0 !important;
              }
              /* Wrapper interno de columnas (el div que contiene cada plot) */
              [data-testid="stColumn"], [data-testid="column"] {
                padding: 0 !important;
                gap: 0 !important;
              }
              /* Block container general */
              .block-container > div {
                gap: 0.1rem !important;
              }
              /* iframe de plotly sin border */
              iframe[title="streamlit_plotly"] {
                margin: 0 !important;
              }
            </style>
            """,
            unsafe_allow_html=True,
        )
        # Single boton compacto "✖ Salir" que limpia TV + fullscreen
        # (vuelve a Modo Guardia normal de un solo click).
        c_exit, c_spacer = st.columns([1, 14])
        with c_exit:
            if st.button("✖ Salir", key="btn_exit_tv",
                         help="Salir del modo TV puro y fullscreen",
                         use_container_width=True):
                st.query_params.clear()
                st.query_params["vista"] = "guardia"
                st.rerun()
        if tv_mode == "chile":
            volcan_name = st.query_params.get("volcan", DEFAULT_VOLCANO)
            _rotating_chile_tv(volcan_name, show_rings=True)
            return
        elif tv_mode == "mosaico":
            from dashboard.views.mosaico_chile import _grid_fragment_tv
            _grid_fragment_tv()
            return
        elif tv_mode == "volcan":
            from dashboard.views.modo_guardia_volcan import _live_panel as volcan_panel
            from dashboard.map_helpers import render_compact_legend, render_scan_status_badge
            volcan_name = st.query_params.get("volcan", "Villarrica")
            # Leyenda combinada: muestra los 3 productos uno al lado del otro
            # en una sola fila — coincide con el grid de 3 columnas debajo.
            # En el ultimo (jma_so2) inyectamos el badge scan-status para
            # que aparezca a la derecha sin pisar las leyendas.
            cols = st.columns(3)
            ts = _latest_ts("eumetsat_ash")
            scan_dt = parse_rammb_ts(ts) if ts else None
            for i, (col, prod) in enumerate(zip(cols,
                    ["eumetsat_ash", "geocolor", "jma_so2"])):
                with col:
                    render_compact_legend(
                        prod, height_px=34,
                        extra_right=render_scan_status_badge(
                            scan_dt, REFRESH_SECONDS,
                        ) if i == 2 else "",
                    )
            volcan_panel(volcan_name, show_wind=False, show_rings=True,
                         enable_capture=False)
            return
        else:  # default = zonas
            from dashboard.views.zonas_fullscreen import _rotating_grid_4_zonas
            _rotating_grid_4_zonas(
                show_volcanoes=True, show_hotspots=True,
                layout="1x4", height=900,
                session_key="tv_zonas_rot_idx", chrome=False,
            )
            return

    st.markdown(
        """
        <style>
          [data-testid="stHeader"] { background: rgba(0,0,0,0); height: 0; }
          .block-container { padding-top: 0.6rem !important; padding-bottom: 1rem !important; }
          /* Optimizacion de gaps en sub-tabs (no solo TV).
             Levemente menos agresivo que TV para preservar legibilidad
             del header/toolbar pero sin desperdicio entre filas de grid. */
          [data-testid="stHorizontalBlock"] { gap: 0.3rem !important; }
          [data-testid="stPlotlyChart"] { margin: 0 !important; padding: 0 !important; }
          [data-testid="stElementContainer"] { margin-bottom: 0.2rem !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        "<div style='display:flex; align-items:center; justify-content:space-between; "
        "padding-bottom:0.4rem; border-bottom:2px solid #223; margin-bottom:0.6rem;'>"
        "<div style='font-size:1.6rem; font-weight:800; color:#ff6644;'>"
        "🛡 MODO GUARDIA</div>"
        "<div style='font-size:0.85rem; color:#7a8a9a;'>"
        "Sala de operaciones · GOES-19 · Sin métricas automáticas</div></div>",
        unsafe_allow_html=True,
    )

    sub_chile, sub_zonas, sub_mosaico, sub_volcan, sub_loop = st.tabs([
        "🌎 Chile (vista nacional)",
        "🗺 Por Zona Volcánica",
        "🗺 Mosaico 8 prioritarios",
        "🔬 Volcán (3 productos)",
        "🎞 Loop 2h",
    ])
    with sub_chile:
        _chile_subtab()
    with sub_zonas:
        _zonas_subtab()
    with sub_mosaico:
        _mosaico_subtab()
    with sub_volcan:
        _volcan_subtab()
    with sub_loop:
        from dashboard.views.loop_volcan import render_subtab as loop_panel
        loop_panel()
