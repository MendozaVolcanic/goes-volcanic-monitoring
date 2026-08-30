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

try:
    from dashboard.map_helpers import add_chile_border
    from dashboard.style import volcano_marker
    from dashboard.utils import fmt_chile, parse_rammb_ts
    from src.fetch.goes_fdcf import HotSpot, fetch_latest_hotspots
    from src.fetch.rammb_slider import (
        CHILE_REPROJECTED_BOUNDS, CHILE_TILES_Z2,
        fetch_stitched_frame, get_latest_timestamps, reproject_to_latlon,
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
ROTATION_SECONDS = 15
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
    # `hotspots_verificados` LANZA si scan_dt is None (FDCF no consultable), y
    # una funcion cacheada que lanza NO guarda resultado: asi el fallo no queda
    # congelado 5 min ni se saltea el scan siguiente. El llamador lo atrapa.
    from dashboard.map_helpers import hotspots_verificados
    return hotspots_verificados(
        *fetch_latest_hotspots(bounds=chile_bbox, hours_back=1))


# nearest_hotspot vive en dashboard.map_helpers. Lazy import (definicion
# local que delega) para evitar el gotcha de Streamlit Cloud:
# `from dashboard.X import Y` top-level falla intermitentemente con
# KeyError/ImportError durante hot-reloads. Ver CLAUDE.md.
def _nearest_hotspot(hotspots, lat, lon):
    from dashboard.map_helpers import nearest_hotspot
    return nearest_hotspot(hotspots, lat, lon)


# ── Render ───────────────────────────────────────────────────────────

from dashboard.map_helpers import array_to_data_url as _array_to_data_url



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
            marker=volcano_marker("focus"),
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

    # constrain="domain" en AMBOS ejes: con scaleanchor y sin esto, el default
    # de Plotly es constrain="range" y ENSANCHA el rango para cumplir el aspecto,
    # ignorando el range que se pide aca. Con el contenedor angosto del primer
    # render la escena se dispara y no vuelve. (audit 2026-08-30)
    fig.update_xaxes(range=[b["lon_min"], b["lon_max"]],
                     showgrid=False, title="", constrain="domain")
    fig.update_yaxes(range=[b["lat_min"], b["lat_max"]],
                     showgrid=False, title="", scaleanchor="x", scaleratio=1,
                     constrain="domain")
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
    from dashboard.map_helpers import FDCFNoVerificable, estado_hotspots
    try:
        hotspots, hs_dt = _hotspots_chile()
    except FDCFNoVerificable:
        # No es "cero hot spots": es que no pudimos preguntar. Se distingue en
        # el KPI de mas abajo, nunca se pinta como calma.
        hotspots, hs_dt = [], None
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

    # ── Header KPIs (3, específicos del volcán). La edad del scan NO se repite
    # acá: ya vive (con color + estado) en el banner de arriba. (jun 2026: dedup)
    c1, c2, c3 = st.columns(3)

    # KPI: hot spots Chile (producto NOAA FDCF, validado).
    # El criterio de color y de que numero mostrar sale de `estado_hotspots`,
    # compartido con las otras vistas: un cero VERDE solo si NOAA miro de
    # verdad. Si el producto no se pudo consultar va gris y con guion, porque
    # ese cero seria ausencia de informacion, no de anomalia termica.
    est_hs = estado_hotspots(hotspots, hs_dt)
    with c1:
        st.markdown(
            f"<div style='background:#0f1418; border-left:4px solid {est_hs['color']}; "
            f"padding:0.8rem 1rem; border-radius:4px;'>"
            f"<div style='font-size:0.7rem; color:#7a8a9a; text-transform:uppercase; "
            f"letter-spacing:0.1em;'>Hot spots Chile (NOAA FDCF)</div>"
            f"<div style='font-size:1.6rem; font-weight:700; color:{est_hs['color']};'>"
            f"{est_hs['valor']}</div>"
            f"<div style='font-size:0.68rem; color:#7a8a9a;'>{est_hs['detalle']}</div>"
            f"</div>",
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
    with c2:
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

    # KPI: hora UTC / Chile
    with c3:
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
    # Leyenda ARRIBA del mapa: el operador la lee antes de mirar la imagen.
    # Hasta ago-2026 esta tira existía sólo en el Modo Sala TV del MISMO mapa.
    from dashboard.map_helpers import render_compact_legend
    render_compact_legend(
        product,
        symbols=("volcano", "hotspot_frp") + (("rings",) if show_rings else ()),
    )
    if frame is not None:
        st.plotly_chart(
            _render_chile_with_hotspots(frame, hotspots, volcan_name, product,
                                         show_rings=show_rings),
            width='stretch',
            config={"displayModeBar": False},
        )
    else:
        st.warning(f"Imagen {CHILE_PRODUCT_OPTIONS.get(product, product)} "
                    "no disponible en este ciclo.")

    # ── Footer info ──
    st.markdown(
        f"<div style='text-align:right; color:#445566; font-size:0.75rem; "
        f"margin-top:0.5rem;'>"
        f"Auto-refresh cada {REFRESH_SECONDS}s · GOES-19 cadencia real 10 min<br>"
        f"<i>Imagenes Ash RGB y hot spots NOAA FDCF — sin metricas automaticas. "
        f"La interpretacion queda al criterio del experto.</i></div>",
        unsafe_allow_html=True,
    )


@st.fragment(run_every=f"{ROTATION_SECONDS}s")
def _rotating_chile_tv(volcan_name: str, show_rings: bool = True,
                        session_key: str = "tv_chile_rot_idx"):
    """Modo Sala Chile: rota productos sobre Chile completo.

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
        current, tv=True,
        symbols=("volcano", "hotspot_frp") + (("rings",) if show_rings else ()),
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
    st.plotly_chart(fig, width='stretch',
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
        # Helper que usa render_html_iframe (st.iframe, con fallback a la
        # API vieja) — iframe interno con JS
        # NO sanitizado) — st.markdown sanitiza onclick, NO funciona.
        from dashboard.map_helpers import render_top_navigation_button
        render_top_navigation_button(
            "🖥 Modo Sala · Chile (rotando productos)",
            f"vista=guardia&fullscreen=1&tv=chile&volcan={volcan}",
            key="btn_sala_chile",
            full_width=True,
        )
    _live_panel(volcan, product=product, show_rings=show_rings)


def _activate_tv(tv_value: str, **extra):
    """Setea query_params para entrar en modo TV puro y rerun.

    NOTA: ya NO se usa desde los botones de Modo Sala (reemplazados por
    anchors HTML con target=_top porque st.button + st.rerun no siempre
    escapa el iframe sandbox de Streamlit Cloud). Se mantiene por compat
    con cualquier otra vista que pudiera importarla.
    """
    st.query_params["vista"] = "guardia"
    st.query_params["fullscreen"] = "1"
    st.query_params["tv"] = tv_value
    for k, v in extra.items():
        st.query_params[k] = v
    st.rerun()


def _mosaico_subtab():
    """Sub-tab Mosaico: los 5 prioritarios x 3 productos (config.MOSAICO_VOLCANOES)."""
    from dashboard.views.mosaico_chile import _live_panel as mosaico_panel
    from dashboard.views.mosaico_chile import ROTATION_SECONDS as ROT_MOSAICO
    from dashboard.map_helpers import render_top_navigation_button
    render_top_navigation_button(
        f"🖥 Modo Sala · Mosaico 5 (rotando productos cada {ROT_MOSAICO}s)",
        "vista=guardia&fullscreen=1&tv=mosaico",
        key="btn_sala_mosaico",
    )
    mosaico_panel()


def _zonas_subtab():
    """Sub-tab Vigilancia diaria: las 4 zonas RGB (Norte/Centro/Sur/Austral).

    El VOLCAT zoom al volcan en alerta (Chillan/Villarrica) vive en la rotacion
    del Modo Sala TV (?tv=1), NO aca — ahi corre junto a los zooms GOES/GeoColor.
    (jun 2026)"""
    from dashboard.views.zonas_fullscreen import (
        _grid_4_zonas, _rotating_grid_4_zonas, PRODUCT_OPTIONS, ROTATION_SECONDS,
    )

    from dashboard.map_helpers import render_top_navigation_button
    render_top_navigation_button(
        f"🖥 Modo Sala (4 zonas, rotando productos cada {ROTATION_SECONDS}s)",
        "vista=guardia&fullscreen=1&tv=1",
        key="btn_sala_zonas",
    )
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
            help=f"Cicla GeoColor → Ash → SO2 cada {ROTATION_SECONDS}s. Util "
                 "para preview de lo que se vera en el monitor de sala antes "
                 "de mandarlo a TV puro.",
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


def _volcat_zonas_subtab():
    """Sub-tab VOLCAT por zona: las zonas regionales con el producto
    cuantitativo VOLCAT (altura/carga/probabilidad/radio) lado a lado.

    Complementa la sub-tab 'Por Zona Volcánica' (que muestra los RGB de
    RAMMB): aquellos DETECTAN la pluma, VOLCAT la CUANTIFICA (Pavolonis
    2013, sobre GOES-19). VOLCAT no tiene sector austral propio (Chile_South
    cubre hasta el extremo sur); con VOLCAT_ZONAS_4 se muestran 4 zonas donde
    'Austral' es un RECORTE sur de Chile_South (ver zonas_fullscreen). El
    número de columnas y el render salen de _volcat_zone_specs (fuente única).
    """
    # Lazy imports (patron del proyecto — evita gotcha de hot-reload en
    # Streamlit Cloud con imports cross-package top-level). El render por celda
    # vive en zonas_fullscreen (fuente unica compartida con el Modo Sala).
    from dashboard.views.volcat_viewer import VOLCAT_PRODUCTS

    st.caption(
        "VOLCAT (SSEC/CIMSS · algoritmo Pavolonis 2013, sobre GOES-19) — "
        "los RGB de la pestaña anterior **detectan** la pluma; VOLCAT la "
        "**cuantifica**: altura del tope (km), carga (g/m²), probabilidad y "
        "tamaño de partícula. Sin erupción activa los productos salen vacíos."
    )

    # Selector de producto VOLCAT (default Altura). Los 4 productos vienen
    # de volcat_viewer.VOLCAT_PRODUCTS (fuente unica).
    prod = st.selectbox(
        "Producto VOLCAT",
        list(VOLCAT_PRODUCTS.keys()),
        format_func=lambda k: VOLCAT_PRODUCTS[k]["label_es"],
        index=0, key="mg_volcat_zona_prod",
    )
    meta_p = VOLCAT_PRODUCTS[prod]
    st.markdown(
        f'<div style="background:rgba(74,158,255,0.08); '
        f'border-left:3px solid #4a9eff; padding:0.35rem 0.7rem; '
        f'border-radius:0 6px 6px 0; margin:0.2rem 0 0.5rem 0; '
        f'font-size:0.78rem;">'
        f'<span style="color:#4a9eff; font-weight:700;">'
        f'{meta_p["icon"]} {meta_p["label_es"]}</span> '
        f'<span style="color:#aabbc8;">— {meta_p["short"]}</span></div>',
        unsafe_allow_html=True,
    )

    # Zonas lado a lado. Con VOLCAT_ZONAS_4 son 4 (Norte/Centro/Sur/Austral,
    # Austral = recorte sur de Chile_South); si no, las 3 clasicas. La fuente
    # unica de specs + render es zonas_fullscreen (compartida con el Modo Sala).
    from dashboard.views.zonas_fullscreen import (
        _prewarm_volcat_specs, _render_volcat_zone_cell, _volcat_zone_specs,
    )
    specs = _volcat_zone_specs()
    # Prefetch PARALELO (audit ago-2026): a diferencia del Modo Sala TV, este sub-tab
    # NO tiene hilo productor calentando las caches, así que las 4 celdas se resolvían
    # en serie — cada una API SSEC (20s) + 2 descargas (30s c/u) con cache fría, o al
    # cambiar de producto en el selector. Calentar en paralelo deja el loop en solo-lectura.
    _prewarm_volcat_specs(specs, product=prod)
    # Simbología del mapa (el código de color cuantitativo lo pone la barra de
    # cada panel, por eso VOLCAT no lleva swatches acá).
    from dashboard.map_helpers import render_compact_legend
    render_compact_legend("volcat", symbols=("volcano",))
    cols = st.columns(len(specs))
    for col, (zona, sector, instr, view_bounds) in zip(cols, specs):
        with col:
            _render_volcat_zone_cell(zona, sector, instr, view_bounds, prod,
                                     height=620)


def _volcan_subtab():
    """Sub-tab Volcan: grilla 2x2 del volcan + viento + anillos + captura."""
    from dashboard.views.modo_guardia_volcan import (RAMMB_REFRESH_S,
                                                     VOLCAT_REFRESH_S,
                                                     volcan_grid)
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
    from dashboard.map_helpers import render_top_navigation_button
    render_top_navigation_button(
        f"🖥 Modo Sala · {volcan} (3 productos)",
        f"vista=guardia&fullscreen=1&tv=volcan&volcan={volcan}",
        key=f"btn_sala_volcan_{volcan}",
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
            # La grilla tiene DOS cadencias (RAMMB 60 s, VOLCAT 120 s):
            # "Refresh 60s" prometia que el panel VOLCAT se actualiza el doble
            # de rapido de lo que se actualiza.
            "<div style='font-size:0.7rem; color:#556; padding-top:0.5rem;'>"
            f"RAMMB {RAMMB_REFRESH_S}s · VOLCAT {VOLCAT_REFRESH_S}s</div>",
            unsafe_allow_html=True,
        )
    volcan_grid(volcan, show_wind, show_rings, enable_capture,
                fullscreen=st.query_params.get("fullscreen") == "1",
                # Sub-tab de pagina: hay operador delante que puede atender la
                # tira de altura propia (y su descarga de ~78 MB). El slot
                # `tv=volcan` de mas abajo NO la lleva.
                mostrar_altura=True)


def render():
    """Entry point para app.py — Modo Guardia unificado con sub-tabs.

    Modo especial TV puro: se SKIPEA el header de modo guardia y los
    st.tabs. Solo se renderiza el grid elegido a pantalla completa.

    URL params:
      ?tv=1       o ?tv=zonas    -> 4 zonas rotando productos (default)
      ?tv=chile&volcan=X         -> Chile completo rotando productos + anillos
                                    alrededor del volcan seleccionado
      ?tv=mosaico                -> los 5 prioritarios rotando productos + anillos
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
              }
              /* Colapsa gap entre filas verticales — clave para grids 4x2 */
              [data-testid="stVerticalBlock"] {
                gap: 0.1rem !important;
              }
              /* Plotly chart container sin padding */
              [data-testid="stPlotlyChart"] {
                margin: 0 !important;
                padding: 0 !important;
              }
              /* Element container compacto. NO usamos min-height:0 ni
                 quitamos padding total porque colapsa contenedores de
                 botones y los hace inclickeables. Solo bajamos margin. */
              [data-testid="stElementContainer"] {
                margin-bottom: 0.1rem !important;
              }
              /* iframe de plotly sin border */
              iframe[title="streamlit_plotly"] {
                margin: 0 !important;
              }
              /* Botones en TV mode: garantizar clickeable y por encima */
              [data-testid="stButton"] {
                position: relative !important;
                z-index: 999 !important;
              }
              [data-testid="stButton"] > button {
                pointer-events: auto !important;
              }
              /* CAUSA RAIZ del 'Salir no clickea' (mayo 2026): el header y
                 toolbar de Streamlit son una franja de ancho completo arriba
                 que, aunque visualmente oculta, CAPTURA los clicks sobre el
                 boton Salir que esta debajo. pointer-events:none los hace
                 transparentes al mouse; ademas ocultamos el status widget
                 'Running/Stop' que se posa sobre el boton. */
              [data-testid="stHeader"],
              [data-testid="stToolbar"] {
                pointer-events: none !important;
              }
              [data-testid="stStatusWidget"] { display: none !important; }
              /* El <a> de Salir por encima de todo y siempre clickeable. */
              [data-testid="stMarkdownContainer"] a {
                position: relative !important;
                z-index: 1000000 !important;
                pointer-events: auto !important;
              }
              /* BOTON SALIR FLOTANTE + AUTO-HIDE (jun 2026): sacamos el
                 boton del flujo (position:fixed) para que NO reste espacio
                 al grid, y lo dejamos semi-transparente hasta que pasas el
                 mouse por la esquina sup-izq. Asi se aprovecha todo el alto
                 y el boton no molesta en la pantalla de sala 24/7. */
              [data-testid="stElementContainer"]:has(a[href="?vista=guardia"]) {
                position: fixed !important;
                top: 2px !important;
                left: 8px !important;
                margin: 0 !important;
                padding: 0 !important;
                z-index: 1000001 !important;
                width: auto !important;
              }
              a[href="?vista=guardia"] {
                opacity: 0.18 !important;
                transition: opacity 0.25s ease !important;
                box-shadow: 0 2px 10px rgba(0,0,0,0.7) !important;
              }
              a[href="?vista=guardia"]:hover { opacity: 1 !important; }
              /* Zona "imán" invisible arriba-izquierda: al acercar el mouse
                 a esa esquina, el boton se hace visible (mejora descubrir-
                 lo sin tener que apuntar al boton casi-invisible). */
              [data-testid="stElementContainer"]:has(a[href="?vista=guardia"]):hover a {
                opacity: 1 !important;
              }
              /* CAUSA DEL 'se oscurece antes de cambiar' (jun 2026): en cada
                 tick del fragment run_every, Streamlit marca el contenido viejo
                 como data-stale="true" y le BAJA la opacity (~0.4) mientras
                 recomputa. Si el recompute tarda mas que el delay (~0.5s) se ve
                 el contenido atenuado. En una pantalla de sala 24/7 eso es el
                 parpadeo principal. Forzamos opacity:1 -> el frame previo se ve
                 NITIDO hasta que el nuevo lo reemplaza de una. */
              [data-testid="stElementContainer"][data-stale="true"],
              [data-testid="stVerticalBlock"][data-stale="true"],
              [data-testid="stHorizontalBlock"][data-stale="true"] {
                opacity: 1 !important;
                transition: none !important;
                filter: none !important;
              }
              /* TRANSICION SUAVE al cambiar de slot: fade-in corto SOLO al
                 montar el contenido nuevo (no en los ticks repetidos por los
                 key estables). Va despues del override de stale para no
                 reintroducir el atenuado del viejo. */
              [data-testid="stPlotlyChart"],
              [data-testid="stImage"],
              [data-testid="stMarkdown"] img {
                animation: tv-fade-in 0.4s ease-out;
              }
              @keyframes tv-fade-in {
                from { opacity: 0.55; }
                to   { opacity: 1; }
              }
            </style>
            """,
            unsafe_allow_html=True,
        )
        from dashboard.map_helpers import render_top_navigation_button
        render_top_navigation_button(
            "✖ Salir",
            "vista=guardia",
            key="btn_exit_tv",
        )
        if tv_mode == "chile":
            volcan_name = st.query_params.get("volcan", DEFAULT_VOLCANO)
            _rotating_chile_tv(volcan_name, show_rings=True)
            return
        elif tv_mode == "mosaico":
            from dashboard.views.mosaico_chile import _grid_fragment_tv
            _grid_fragment_tv()
            return
        elif tv_mode == "volcan":
            from dashboard.views.modo_guardia_volcan import GRID_PANELS_TV, volcan_grid
            from dashboard.map_helpers import render_compact_legend, render_scan_status_badge
            volcan_name = st.query_params.get("volcan", "Villarrica")
            # Leyenda combinada: muestra los 3 productos uno al lado del otro
            # en una sola fila — coincide con el grid de 3 columnas debajo.
            # En el ultimo (jma_so2) inyectamos el badge scan-status para
            # que aparezca a la derecha sin pisar las leyendas.
            cols = st.columns(3)
            ts = _latest_ts("eumetsat_ash")
            scan_dt = parse_rammb_ts(ts) if ts else None
            # La lista sale de GRID_PANELS_TV, la MISMA que recorre el grid
            # de abajo: dos literales separados calzaban por casualidad y
            # cualquier reordenamiento rotulaba un producto encima de otro.
            for i, (col, prod) in enumerate(zip(
                    cols, [p["id"] for p in GRID_PANELS_TV])):
                with col:
                    render_compact_legend(
                        prod, height_px=34, tv=True,
                        symbols=(("volcano", "hotspot", "rings")
                                 if prod == "eumetsat_ash" else ("volcano",)),
                        extra_right=render_scan_status_badge(
                            scan_dt, REFRESH_SECONDS,
                        ) if i == 2 else "",
                    )
            # fullscreen=True FIJO: en este camino el query param siempre
            # vale "1" (lo setea _go_tv) y sin pasarlo la grilla caia en
            # PANEL_HEIGHT_NORMAL, o sea 39% menos de alto en la pared que se
            # proyecta 24/7 en la sala de turno.
            volcan_grid(volcan_name, show_wind=False, show_rings=True,
                        enable_capture=False, panels=GRID_PANELS_TV,
                        per_row=3, show_header=False, fullscreen=True,
                        # La fila de 3 leyendas de arriba ya dice todo lo que
                        # dirian las de adentro: con las dos prendidas la
                        # pared proyectada gastaba ~60 px de alto repitiendose,
                        # y ese alto es imagen de satelite que se pierde.
                        show_legend=False)
            return
        else:  # default = zonas
            # CSS especifico TV 4 zonas: fuerza cada plot a llenar el
            # viewport VERTICAL del browser actual (NO del display
            # fisico de 17280x1080). Soluciona el caso de pantalla
            # operacional gigante donde el browser ocupa solo una
            # franja: el grid se adapta al viewport del browser.
            # `calc(100vh - 56px)` reserva ~56px para la barra de
            # leyenda compacta + boton Salir arriba.
            # Plotly recibe `responsive: True` para refit cuando el
            # iframe cambia de tamaño (resize del browser).
            st.markdown(
                """
                <style>
                  /* TV: la leyenda es OVERLAY translucido sobre el top del
                     mapa (no resta alto), el boton Salir es flotante, asi el
                     grid usa CASI todo el viewport (100vh - 6px). Antes
                     restaba 56px (boton + leyenda en flujo). */
                  [data-testid="stPlotlyChart"],
                  [data-testid="stPlotlyChart"] > div,
                  [data-testid="stPlotlyChart"] iframe {
                    height: calc(100vh - 6px) !important;
                    min-height: 200px !important;
                  }
                  /* La imagen VOLCAT (st.image): el sector SSEC es "cuadrado"
                     (aspect ~1.22), asi que a 100vh de alto solo usaba ~54%
                     del ancho. La agrandamos a ~72vw con estiramiento
                     horizontal MODERADO (cap ~1.3x via min()) para aprovechar
                     el espacio sin deformar de mas. (jun 2026, pedido OVDAS) */
                  /* Imagen VOLCAT (st.image): cadena de contenedores
                     stFullScreenFrame > stImage > stImageContainer > img.
                     El frame full-width permite centrar el stImage (72vw) con
                     margin auto; el stImageContainer DEBE ser 100% o la img
                     queda en su ancho natural (~55%). La img llena 72vw, alto
                     100vh, estiramiento moderado (cap ~1.3x). */
                  /* frame full-width + flex justify-center -> centra el
                     stImage (72vw) de forma robusta (los contenedores heredan
                     el ancho de la imagen, asi que margin auto no alcanzaba).
                     Tambien el stElementContainer por si el frame no es full. */
                  [data-testid="stElementContainer"]:has([data-testid="stImage"]),
                  [data-testid="stFullScreenFrame"] {
                    width: 100% !important;
                    display: flex !important;
                    justify-content: center !important;
                  }
                  [data-testid="stImage"] {
                    width: min(72vw, calc((100vh - 6px) * 1.58)) !important;
                  }
                  [data-testid="stImageContainer"] {
                    width: 100% !important;
                  }
                  [data-testid="stImage"] img {
                    height: calc(100vh - 6px) !important;
                    width: 100% !important;
                    object-fit: fill !important;
                  }
                  .block-container {
                    max-width: 100vw !important;
                    width: 100vw !important;
                    padding-top: 0.1rem !important;
                  }
                  /* LEYENDA OVERLAY: la sacamos del flujo (su contenedor
                     colapsa a 0) y la flotamos translucida sobre la parte
                     superior del grid. Asi "usa la parte de arriba" sin
                     robar alto, como pediste. */
                  [data-testid="stElementContainer"]:has(.tv-legend) {
                    position: absolute !important;
                    top: 4px !important;
                    left: 50% !important;
                    transform: translateX(-50%) !important;
                    z-index: 900 !important;
                    margin: 0 !important;
                    width: auto !important;
                    max-width: 96vw !important;
                  }
                  .tv-legend {
                    opacity: 0.9 !important;
                    margin-bottom: 0 !important;
                    box-shadow: 0 2px 12px rgba(0,0,0,0.6) !important;
                  }
                  /* PANEL DE ESTADO overlay esquina superior DERECHA: reloj
                     actual + edad del scan. Separado de la leyenda (centro)
                     para que no se solapen. */
                  [data-testid="stElementContainer"]:has(.tv-status) {
                    position: fixed !important;
                    top: 4px !important;
                    right: 12px !important;
                    z-index: 1000000 !important;
                    margin: 0 !important;
                    width: auto !important;
                  }
                  .tv-status {
                    background: rgba(10,14,20,0.82) !important;
                    padding: 4px 12px !important;
                    border-radius: 6px !important;
                    border: 1px solid rgba(100,120,140,0.25) !important;
                    box-shadow: 0 2px 12px rgba(0,0,0,0.6) !important;
                  }
                </style>
                """,
                unsafe_allow_html=True,
            )
            # Rotacion uniforme (12s/slot): 3 RGB (4 zonas) + 3 VOLCAT + zoom.
            from dashboard.views.zonas_fullscreen import (
                _rotating_tv_zonas, prewarm_tv_caches,
            )
            # Pre-calentar en BACKGROUND (1 vez/sesion, no bloquea) para que ni
            # el primer ciclo tras un reboot se sienta lento.
            prewarm_tv_caches(show_hotspots=True)
            _rotating_tv_zonas(
                show_volcanoes=True, show_hotspots=True,
                height=900, session_key="tv_rot_tick",
            )
            return

    # Manual: solo en modo normal (no TV — la sala no quiere expanders).
    from dashboard.manuals import render_manual
    render_manual("guardia")

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

    # "Vigilancia diaria" PRIMERA (landing): ya no es solo "por zona" — suma el
    # VOLCAT zoom al volcan en alerta y es lo que responde al dia a dia del
    # observatorio. (reorden + rename jun 2026, pedido OVDAS)
    #
    # El conteo del sub-tab Volcan se DERIVA de GRID_PANELS, no se escribe a
    # mano: el rotulo quedo diciendo "3 productos" durante toda la migracion a
    # `volcan_grid`, que ya pintaba cuatro (VOLCAT entro como 4o panel). Un
    # numero equivocado en el rotulo le hace creer al turno que le falta un
    # producto por mirar. Import perezoso por el gotcha de hot-reload de
    # Streamlit documentado en la cabecera del modulo.
    from dashboard.views.modo_guardia_volcan import GRID_PANELS
    sub_zonas, sub_chile, sub_volcat, sub_mosaico, sub_volcan, sub_loop = st.tabs([
        "🔭 Vigilancia diaria",
        "🌎 Chile (vista nacional)",
        "🌋 VOLCAT por zona",
        "🗺 Mosaico 5 prioritarios",
        f"🔬 Volcán ({len(GRID_PANELS)} productos)",
        "🎞 Loop 2h",
    ])
    with sub_zonas:
        _zonas_subtab()
    with sub_chile:
        _chile_subtab()
    with sub_volcat:
        _volcat_zonas_subtab()
    with sub_mosaico:
        _mosaico_subtab()
    with sub_volcan:
        _volcan_subtab()
    with sub_loop:
        from dashboard.views.loop_volcan import render_subtab as loop_panel
        loop_panel()
