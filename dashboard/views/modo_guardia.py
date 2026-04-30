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
DEFAULT_VOLCANO = "Villarrica"


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
    if hotspots:
        lats = [h.lat for h in hotspots]
        lons = [h.lon for h in hotspots]
        temps = [f"{h.temp_k:.0f} K, FRP {h.frp_mw:.1f} MW ({h.confidence})"
                 for h in hotspots]
        fig.add_trace(go.Scatter(
            x=lons, y=lats, mode="markers",
            marker=dict(symbol="diamond", size=12, color="#ff3300",
                        line=dict(color="white", width=1)),
            text=temps, hoverinfo="text", name=f"Hot spots NOAA ({len(hotspots)})",
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
def _live_panel(volcan_name: str):
    """Fragment con auto-refresh — solo este bloque se re-renderiza cada 60s."""
    ts = _latest_ts()
    if not ts:
        st.error("RAMMB no respondio. Reintentando en 60s…")
        return

    frame = _ash_chile_frame(ts)
    hotspots, _hs_dt = _hotspots_chile()
    v = get_volcano(volcan_name)

    now = datetime.now(timezone.utc)

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

    # ── Mapa principal Ash + hotspots ──
    if frame is not None:
        st.plotly_chart(
            _render_ash_with_hotspots(frame, hotspots, volcan_name),
            use_container_width=True,
            config={"displayModeBar": False},
        )
    else:
        st.warning("Imagen Ash RGB no disponible en este ciclo.")

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


def _chile_subtab():
    """Sub-tab Chile: el live panel original con selector de volcan."""
    cols = st.columns([3, 1])
    with cols[1]:
        volcan = st.selectbox(
            "Volcan a monitorear",
            options=PRIORITY_VOLCANOES,
            index=PRIORITY_VOLCANOES.index(DEFAULT_VOLCANO)
            if DEFAULT_VOLCANO in PRIORITY_VOLCANOES else 0,
            label_visibility="collapsed",
            key="mg_chile_selector",
        )
    _live_panel(volcan)


def _mosaico_subtab():
    """Sub-tab Mosaico: 8 prioritarios en grid 4x2."""
    from dashboard.views.mosaico_chile import _live_panel as mosaico_panel
    # Boton TV puro mosaico
    st.markdown(
        '<a href="?vista=guardia&fullscreen=1&tv=mosaico" target="_self" '
        'style="display:inline-block; '
        'background:linear-gradient(135deg, #CC3311, #EE7733); '
        'color:white; padding:0.5rem 1rem; border-radius:6px; '
        'text-decoration:none; font-weight:700; font-size:0.9rem; '
        'margin-bottom:0.6rem;">'
        '🖥 Activar TV puro · Mosaico (rotando productos cada 10s)</a>',
        unsafe_allow_html=True,
    )
    mosaico_panel()


def _zonas_subtab():
    """Sub-tab Por Zona Volcánica: las 4 zonas. Boton TV puro = sin chrome."""
    from dashboard.views.zonas_fullscreen import (
        _grid_4_zonas, _rotating_grid_4_zonas, PRODUCT_OPTIONS, ROTATION_SECONDS,
    )

    # Boton de "Activar TV puro" — navega a ?tv=1 que oculta TODO el chrome
    # (header modo guardia + sub-tabs + toolbar). Solo se ven las imagenes.
    st.markdown(
        '<a href="?vista=guardia&fullscreen=1&tv=1" target="_self" '
        'style="display:inline-block; '
        'background:linear-gradient(135deg, #CC3311, #EE7733); '
        'color:white; padding:0.5rem 1rem; border-radius:6px; '
        'text-decoration:none; font-weight:700; font-size:0.9rem; '
        'margin-bottom:0.6rem;">'
        '🖥 Activar TV puro (rotando productos cada 10s)</a>',
        unsafe_allow_html=True,
    )
    st.caption(
        "TV puro = solo los 4 mapas a pantalla completa rotando productos. "
        "Sin header, sin sub-tabs, sin toolbar. Pensado para monitor 24/7. "
        "Botón ✖ arriba a la derecha para salir."
    )

    # Modo normal con toolbar completa (no TV puro)
    cols = st.columns([1.0, 1.2, 1.0, 1.0])
    with cols[0]:
        product = st.selectbox(
            "Producto",
            options=list(PRODUCT_OPTIONS.keys()),
            format_func=lambda k: PRODUCT_OPTIONS[k],
            index=0, key="mg_zonas_product",
            label_visibility="collapsed",
        )
    with cols[1]:
        layout = st.radio(
            "Layout",
            ["1×4 (TV)", "2×2"],
            index=0, key="mg_zonas_layout",
            horizontal=True,
            label_visibility="collapsed",
        )
    with cols[2]:
        show_volc = st.toggle("🔺 Volcanes", value=True, key="mg_zonas_volc")
    with cols[3]:
        show_hs = st.toggle("🔥 Hot spots", value=True, key="mg_zonas_hs")

    layout_key = "1x4" if layout.startswith("1×4") else "2x2"
    height = 820 if layout_key == "1x4" else 720
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
    # Boton TV puro volcan (lleva el volcan seleccionado en URL)
    st.markdown(
        f'<a href="?vista=guardia&fullscreen=1&tv=volcan&volcan={volcan}" '
        f'target="_self" '
        f'style="display:inline-block; '
        f'background:linear-gradient(135deg, #CC3311, #EE7733); '
        f'color:white; padding:0.4rem 0.9rem; border-radius:6px; '
        f'text-decoration:none; font-weight:700; font-size:0.85rem; '
        f'margin-bottom:0.4rem;">'
        f'🖥 Activar TV puro · {volcan} (3 productos)</a>',
        unsafe_allow_html=True,
    )
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
      ?tv=mosaico                -> 8 prioritarios rotando productos + anillos
      ?tv=volcan&volcan=X        -> 1 volcan con 3 productos (sin rotacion,
                                    los 3 productos ya estan lado a lado)
    """
    tv_mode = st.query_params.get("tv", "")
    if tv_mode:
        # Boton "Salir TV puro" en esquina sup. IZQUIERDA (right tapaba dev tools)
        st.markdown(
            '<a href="?vista=guardia&fullscreen=0&tv=" target="_self" '
            'style="position:fixed; top:8px; left:8px; z-index:1000; '
            'background:rgba(0,0,0,0.65); color:#ff6644; padding:6px 12px; '
            'border-radius:4px; text-decoration:none; font-size:0.78rem; '
            'border:1px solid #ff6644;">✖ Salir TV puro</a>',
            unsafe_allow_html=True,
        )
        if tv_mode == "mosaico":
            from dashboard.views.mosaico_chile import _grid_fragment_tv
            _grid_fragment_tv()
            return
        elif tv_mode == "volcan":
            from dashboard.views.modo_guardia_volcan import _live_panel as volcan_panel
            from dashboard.map_helpers import render_compact_legend
            volcan_name = st.query_params.get("volcan", "Villarrica")
            # Leyenda combinada: muestra los 3 productos uno al lado del otro
            # en una sola fila — coincide con el grid de 3 columnas debajo.
            cols = st.columns(3)
            for col, prod in zip(cols, ["eumetsat_ash", "geocolor", "jma_so2"]):
                with col:
                    render_compact_legend(prod, height_px=34)
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
