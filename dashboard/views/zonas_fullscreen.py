"""Vista 4 Zonas Full Screen — máxima densidad visual.

Las 4 zonas volcánicas (Norte, Centro, Sur, Austral) en grilla 2×2,
ocupando toda la pantalla. Selector de producto único para las 4.

Diseño:
- Header mínimo: titulo + selector producto + status banner
- CSS oculta el padding default de Streamlit
- Cada zona es un mapa de ~700 px de altura
- 2x2 grid → uso pantalla casi total

Caso de uso: barrer las 4 zonas en paralelo, comparar evolución entre
norte y sur, ver dispersión de plumas a escala continental.

Filosofía: como Modo Guardia pero con MAS densidad visual y solo Chile,
sin distractores.
"""

import logging
from datetime import datetime, timezone

import numpy as np
import plotly.graph_objects as go
import streamlit as st

try:
    from dashboard.map_helpers import add_chile_border
    from dashboard.utils import fmt_chile, parse_rammb_ts
    from src.config import VOLCANIC_ZONES
    from src.fetch.goes_fdcf import HotSpot, fetch_latest_hotspots
    from src.fetch.rammb_slider import (
        fetch_frame_robust, get_latest_timestamps, ZOOM_ZONE,
    )
    from src.volcanos import CATALOG
except Exception:
    # Streamlit Cloud hot-reload race condition: retry import dentro de funciones.
    # Si esto se ejecuta, hay un bug — log y reraise para que Streamlit muestre el error.
    import logging as _logging
    _logging.exception("Cross-package import fallo top-level — gotcha Streamlit Cloud")
    raise

logger = logging.getLogger(__name__)

REFRESH_SECONDS = 60
ROTATION_SECONDS = 15

PRODUCT_OPTIONS = {
    "eumetsat_ash": "Ash RGB",
    "geocolor": "GeoColor",
    "jma_so2": "SO2 RGB",
}
PRODUCT_LIST = list(PRODUCT_OPTIONS.keys())

ZONE_LABELS = {
    "norte":   "Zona Norte",
    "centro":  "Zona Centro",
    "sur":     "Zona Sur",
    "austral": "Zona Austral",
}

ZONE_COLORS = {
    "norte":   "#CC3311",
    "centro":  "#EE7733",
    "sur":     "#009988",
    "austral": "#0077BB",
}


@st.cache_data(ttl=30, show_spinner=False)
def _recent_ts(product: str, n: int = 3) -> list[str]:
    return get_latest_timestamps(product, n=n)


@st.cache_data(ttl=300, show_spinner=False)
def _hotspots_zone(zone_key: str) -> tuple[list[HotSpot], datetime | None]:
    bounds = VOLCANIC_ZONES[zone_key]
    try:
        return fetch_latest_hotspots(bounds=bounds, hours_back=1)
    except Exception:
        return [], None


def _array_to_data_url(arr):
    # Lazy import (gotcha Streamlit Cloud — ver CLAUDE.md).
    from dashboard.map_helpers import array_to_data_url
    return array_to_data_url(arr)



def _zone_fig(img: np.ndarray | None, zone_key: str, label: str,
              hotspots: list[HotSpot], height: int = 720,
              show_volcanoes: bool = True, time_label: str = ""):
    bounds = VOLCANIC_ZONES[zone_key]
    fig = go.Figure()
    if img is not None:
        fig.add_layout_image(
            source=_array_to_data_url(img),
            xref="x", yref="y",
            x=bounds["lon_min"], y=bounds["lat_max"],
            sizex=bounds["lon_max"] - bounds["lon_min"],
            sizey=bounds["lat_max"] - bounds["lat_min"],
            sizing="stretch", layer="below",
        )

    # Volcanes en la zona como triangulos + labels
    if show_volcanoes:
        zone_volcs = [v for v in CATALOG
                      if bounds["lat_min"] <= v.lat <= bounds["lat_max"]
                      and bounds["lon_min"] <= v.lon <= bounds["lon_max"]
                      and v.zone != "test"]
        if zone_volcs:
            fig.add_trace(go.Scatter(
                x=[v.lon for v in zone_volcs],
                y=[v.lat for v in zone_volcs],
                mode="markers+text",
                marker=dict(symbol="triangle-up", size=10, color="#00ffff",
                            line=dict(color="white", width=1)),
                text=[v.name for v in zone_volcs],
                textposition="middle right",
                textfont=dict(size=9, color="rgba(255,255,255,0.85)"),
                hovertext=[f"<b>{v.name}</b><br>{v.elevation:,} m" for v in zone_volcs],
                hoverinfo="text", showlegend=False,
            ))

    # Hot spots NOAA FDCF
    if hotspots:
        labels_hs = [f"{h.temp_k:.0f}K · FRP {h.frp_mw:.1f}MW ({h.confidence})"
                     for h in hotspots]
        fig.add_trace(go.Scatter(
            x=[h.lon for h in hotspots],
            y=[h.lat for h in hotspots],
            mode="markers",
            marker=dict(symbol="diamond", size=12, color="#ff3300",
                        line=dict(color="white", width=1)),
            text=labels_hs, hoverinfo="text", showlegend=False,
        ))

    # Frontera de Chile (overlay)
    add_chile_border(fig)

    # Aspect ratio correcto en km (mismo fix que modo_guardia_volcan)
    cos_lat = max(0.1, float(np.cos(np.radians(
        (bounds["lat_min"] + bounds["lat_max"]) / 2
    ))))
    fig.update_xaxes(range=[bounds["lon_min"], bounds["lon_max"]],
                     showgrid=False, visible=False)
    fig.update_yaxes(range=[bounds["lat_min"], bounds["lat_max"]],
                     showgrid=False, visible=False,
                     scaleanchor="x", scaleratio=1.0 / cos_lat)
    # Title como annotation EN COORDS DE DATOS para no perder pixeles
    # arriba del plot. Igual estrategia que mosaico — scaleanchor empuja
    # paper-anchored al espacio negro afuera.
    # Label de zona + hora (UTC/local) debajo, en una sola annotation con
    # fondo para que se lea sobre la imagen.
    _txt = f"<b>{label}</b>"
    if time_label:
        _txt += (f"<br><span style='font-size:11px; color:#dfe6ee;'>"
                 f"{time_label}</span>")
    fig.add_annotation(
        x=bounds["lon_min"], y=bounds["lat_max"],
        xref="x", yref="y",
        text=_txt, showarrow=False, align="left",
        font=dict(size=14, color=ZONE_COLORS[zone_key]),
        bgcolor="rgba(0,0,0,0.65)", borderpad=4,
        xanchor="left", yanchor="top",
        xshift=4, yshift=-4,
    )
    fig.update_layout(
        height=height, margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor="#0a0e14", plot_bgcolor="#0a0e14",
        # autosize=True: en conjunto con config={"responsive": True}
        # hace que plotly se auto-ajuste cuando el iframe es resizeado
        # via CSS (caso TV mode con `height: calc(100vh - 56px)`).
        autosize=True,
    )
    if img is None:
        fig.add_annotation(text="Sin imagen", xref="paper", yref="paper",
                           x=0.5, y=0.5, showarrow=False,
                           font=dict(color="#7a8a9a", size=14))
    return fig


# ── FEATURE FLAG: modo de render de VOLCAT por zona ──────────────────
# "ssec_overlay"   = imagen SSEC tal cual (con su titulo, grilla y TODOS
#                    los volcanes del overlay de SSEC). Es el despliegue
#                    "clasico" (muchos volcanes). ACTIVO por defecto.
# "plotly_volcanes"= render propio con plotly: mapa recortado (sin titulo
#                    ni colorbar) + SOLO nuestros volcanes (los mismos que
#                    las RGB) + frontera de Chile. Mas limpio y consistente.
#
# Para cambiar de modo basta editar esta constante y redeployar — ambos
# renders conviven en el codigo. (mayo 2026)
VOLCAT_TV_RENDER = "ssec_overlay"

# Encuadre (rango de ejes) por zona VOLCAT — ajustado a la franja chilena
# para no mostrar tanto oceano. La imagen SSEC cubre mas area; plotly hace
# zoom a estos bounds. 'Sur' extiende hasta austral (Chile_South lo cubre).
VOLCAT_VIEW = {
    "Norte":  {"lat_min": -28.0, "lat_max": -15.5, "lon_min": -71.5, "lon_max": -66.5},
    "Centro": {"lat_min": -39.0, "lat_max": -28.0, "lon_min": -73.0, "lon_max": -68.0},
    "Sur":    {"lat_min": -56.0, "lat_max": -36.0, "lon_min": -77.0, "lon_max": -70.0},
}


def _volcat_zone_fig(img_bytes, sector_bounds, view_bounds, zona_label,
                     time_label, height):
    """Renderiza una imagen VOLCAT con plotly, georeferenciada al sector
    SSEC, con NUESTROS volcanes (CATALOG) y la frontera de Chile encima —
    mismos volcanes que las vistas RGB, sin el overlay sobrecargado de SSEC
    ni las grids. Eje recortado a `view_bounds` (franja chilena)."""
    import base64
    fig = go.Figure()
    if img_bytes:
        b64 = base64.b64encode(img_bytes).decode()
        fig.add_layout_image(
            source=f"data:image/png;base64,{b64}",
            xref="x", yref="y",
            x=sector_bounds["lon_min"], y=sector_bounds["lat_max"],
            sizex=sector_bounds["lon_max"] - sector_bounds["lon_min"],
            sizey=sector_bounds["lat_max"] - sector_bounds["lat_min"],
            sizing="stretch", layer="below",
        )
    # Nuestros volcanes dentro del encuadre (los MISMOS que las RGB).
    vis = [v for v in CATALOG
           if view_bounds["lat_min"] <= v.lat <= view_bounds["lat_max"]
           and view_bounds["lon_min"] <= v.lon <= view_bounds["lon_max"]
           and v.zone != "test"]
    if vis:
        fig.add_trace(go.Scatter(
            x=[v.lon for v in vis], y=[v.lat for v in vis],
            mode="markers+text",
            marker=dict(symbol="triangle-up", size=9, color="#00ffff",
                        line=dict(color="white", width=1)),
            text=[v.name for v in vis], textposition="middle right",
            textfont=dict(size=9, color="rgba(255,255,255,0.9)"),
            hovertext=[f"{v.name} ({v.elevation:,} m)" for v in vis],
            hoverinfo="text", showlegend=False,
        ))
    add_chile_border(fig)
    cos_lat = max(0.1, float(np.cos(np.radians(
        (view_bounds["lat_min"] + view_bounds["lat_max"]) / 2))))
    fig.update_xaxes(range=[view_bounds["lon_min"], view_bounds["lon_max"]],
                     showgrid=False, visible=False)
    fig.update_yaxes(range=[view_bounds["lat_min"], view_bounds["lat_max"]],
                     showgrid=False, visible=False,
                     scaleanchor="x", scaleratio=1.0 / cos_lat)
    _txt = f"<b>{zona_label}</b>"
    if time_label:
        _txt += (f"<br><span style='font-size:11px; color:#dfe6ee;'>"
                 f"{time_label}</span>")
    fig.add_annotation(
        x=view_bounds["lon_min"], y=view_bounds["lat_max"], xref="x", yref="y",
        text=_txt, showarrow=False, align="left",
        font=dict(size=14, color="#ff6644"),
        bgcolor="rgba(0,0,0,0.65)", borderpad=4,
        xanchor="left", yanchor="top", xshift=4, yshift=-4,
    )
    fig.update_layout(
        height=height, margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor="#0a0e14", plot_bgcolor="#0a0e14", autosize=True,
    )
    return fig


def _render_volcat_zonas_tv(height: int):
    """Render de las 3 zonas VOLCAT (altura de pluma) en fila, para el
    Modo Sala TV.

    El modo lo decide la constante VOLCAT_TV_RENDER (feature flag):
    - "ssec_overlay": imagen SSEC clasica (titulo, grilla, todos los
      volcanes de SSEC) via st.image. Despliegue por defecto actual.
    - "plotly_volcanes": render propio con plotly, mapa recortado +
      nuestros volcanes + frontera. Mas limpio (activable mas adelante).
    """
    from dashboard.views.volcat_viewer import (
        _volcat_latest_cached, _volcat_map_only, _volcat_image_with_overlays,
        _volcat_dt_obj,
    )
    from dashboard.utils import fmt_both
    from src.fetch.volcat_api import ZONE_TO_SECTOR

    cols = st.columns(len(ZONE_TO_SECTOR))
    for col, (zona, (sector, instr)) in zip(cols, ZONE_TO_SECTOR.items()):
        with col:
            try:
                meta = _volcat_latest_cached(sector, instr, "Ash_Height")
            except Exception:
                meta = None
            if not meta:
                st.markdown(
                    f"<div style='color:#ff6644; font-weight:800;'>Zona {zona}"
                    f"</div><div style='color:#7a8a9a; padding:2rem 0; "
                    f"text-align:center;'>VOLCAT sin frame</div>",
                    unsafe_allow_html=True,
                )
                continue
            dt = _volcat_dt_obj(meta.get("datetime"))
            time_label = fmt_both(dt) if dt else ""

            if VOLCAT_TV_RENDER == "plotly_volcanes":
                data = _volcat_map_only(
                    meta["image_url"], meta.get("latlon_url"),
                    meta.get("coords") or {})
                if not data:
                    st.markdown(
                        f"<div style='color:#7a8a9a; padding:2rem 0; "
                        f"text-align:center;'>VOLCAT sin frame</div>",
                        unsafe_allow_html=True)
                    continue
                sb = data["bounds"]
                vb = {
                    "lat_min": sb["lat_min"], "lat_max": sb["lat_max"],
                    "lon_min": max(sb["lon_min"], -76.0),
                    "lon_max": min(sb["lon_max"], -66.0),
                }
                st.plotly_chart(
                    _volcat_zone_fig(data["png"], sb, vb, f"Zona {zona}",
                                     time_label, height),
                    width='stretch',
                    config={"displayModeBar": False, "responsive": True},
                )
            else:  # "ssec_overlay" — imagen SSEC clasica (muchos volcanes)
                st.markdown(
                    f"<div style='display:flex; justify-content:space-between; "
                    f"align-items:baseline; background:rgba(10,14,20,0.92); "
                    f"padding:0.2rem 0.6rem; border-radius:4px 4px 0 0; "
                    f"border-left:3px solid #ff6644;'>"
                    f"<span style='color:#ff6644; font-weight:800; "
                    f"font-size:0.95rem;'>Zona {zona}</span>"
                    f"<span style='color:#aabbc8; font-size:0.78rem;'>"
                    f"{time_label or 'sin hora'}</span></div>",
                    unsafe_allow_html=True,
                )
                img = _volcat_image_with_overlays(
                    meta["image_url"], meta.get("volcanoes_url"),
                    meta.get("latlon_url"))
                if img:
                    st.image(img, width='stretch')
                else:
                    st.markdown(
                        "<div style='color:#7a8a9a; padding:2rem 0; "
                        "text-align:center;'>VOLCAT sin frame</div>",
                        unsafe_allow_html=True)


def _render_volcat_one_zona_tv(zona: str, sector: str, instr: str, height: int):
    """Render de UNA sola zona VOLCAT, en grande y centrada, para la
    rotacion del Modo Sala TV (una zona a la vez, no las 3 juntas)."""
    from dashboard.views.volcat_viewer import (
        _volcat_latest_cached, _volcat_map_only, _volcat_image_with_overlays,
        _volcat_dt_obj,
    )
    from dashboard.utils import fmt_both

    try:
        meta = _volcat_latest_cached(sector, instr, "Ash_Height")
    except Exception:
        meta = None
    if not meta:
        st.markdown(
            f"<div style='color:#7a8a9a; text-align:center; padding:3rem;'>"
            f"VOLCAT Zona {zona} — sin frame disponible</div>",
            unsafe_allow_html=True)
        return
    dt = _volcat_dt_obj(meta.get("datetime"))
    time_label = fmt_both(dt) if dt else ""
    # SIN columnas laterales: antes la imagen iba en una columna central del
    # ~46% del ancho -> se limitaba por ancho y NO llenaba el alto. Ahora usa
    # todo el ancho disponible; el CSS del TV la escala por max-height
    # (calc(100vh)) centrada -> aprovecha todo el alto de la pantalla. (jun 2026)
    if VOLCAT_TV_RENDER == "plotly_volcanes":
        data = _volcat_map_only(meta["image_url"], meta.get("latlon_url"),
                                meta.get("coords") or {})
        if data:
            sb = data["bounds"]
            vb = {"lat_min": sb["lat_min"], "lat_max": sb["lat_max"],
                  "lon_min": max(sb["lon_min"], -76.0),
                  "lon_max": min(sb["lon_max"], -66.0)}
            st.plotly_chart(
                _volcat_zone_fig(data["png"], sb, vb, f"Zona {zona}",
                                 time_label, height),
                width='stretch',
                config={"displayModeBar": False, "responsive": True},
                # key fijo por zona -> update in-place, sin parpadeo.
                key=f"tvvolcat_{zona}")
    else:  # ssec_overlay
        img = _volcat_image_with_overlays(
            meta["image_url"], meta.get("volcanoes_url"),
            meta.get("latlon_url"))
        if img:
            st.image(img, width='stretch')


# ── Rotacion del Modo Sala TV con TIEMPOS MIXTOS ─────────────────────
# RGB (GeoColor/Ash/SO2) -> 15s cada uno, mostrando las 4 zonas en grid.
# VOLCAT -> rota entre sus 3 zonas, 10s cada una, UNA en grande.
# Como los tiempos difieren (15 vs 10), el fragment corre cada 5s (el comun
# divisor) y cada slot ocupa N ticks: RGB = 3 ticks (15s), VOLCAT = 2 ticks
# (10s). (jun 2026)
RGB_SECONDS = 15
VOLCAT_SECONDS = 10
TICK_SECONDS = 5


def _render_tv_status(scan_dt=None):
    """Panel de estado OVERLAY (esquina superior derecha) del Modo Sala TV:
    reloj actual (UTC + local) y, si se da scan_dt, la edad del ultimo scan
    con color de alerta (verde <15min, amarillo <30, rojo >30 = RAMMB caido).
    Util para que el operador 24/7 vea de un vistazo si los datos estan
    frescos. (jun 2026)"""
    from datetime import datetime, timezone
    from dashboard.utils import fmt_chile
    now = datetime.now(timezone.utc)
    parts = [
        f"<div style='font-weight:800; color:#e6edf3; font-size:0.92rem; "
        f"line-height:1.1;'>{now.strftime('%H:%M')} UTC</div>",
        f"<div style='color:#8899aa; font-size:0.72rem;'>{fmt_chile(now)}</div>",
    ]
    if scan_dt is not None:
        age = int((now - scan_dt).total_seconds() / 60)
        color = "#3fb950" if age < 15 else "#d29922" if age < 30 else "#ff4444"
        alert = "" if age < 30 else " ⚠"
        parts.append(
            f"<div style='color:{color}; font-weight:700; font-size:0.74rem; "
            f"margin-top:2px;'>● scan hace {age} min{alert}</div>")
    st.markdown(
        f"<div class='tv-status' style='text-align:right;'>{''.join(parts)}</div>",
        unsafe_allow_html=True,
    )


def _rotating_tv_zonas(show_volcanoes: bool, show_hotspots: bool,
                       height: int = 900, session_key: str = "tv_rot_tick"):
    """Setup del Modo Sala TV: crea los placeholders persistentes y arranca
    el fragment de tick.

    CLAVE anti-parpadeo (jun 2026): los placeholders se crean UNA sola vez
    (al entrar al TV; render() no se re-ejecuta, solo el fragment). El
    fragment los actualiza SELECTIVAMENTE: el reloj cada tick (texto liviano)
    y el grid/imagen pesado SOLO cuando el slot cambia. Asi, durante los 3
    ticks de un producto RGB (15s), el contenido NO se re-renderiza -> no
    parpadea. Antes el fragment redibujaba todo cada 5s.
    """
    status_ph = st.empty()
    content_ph = st.empty()
    _tv_tick(status_ph, content_ph, show_volcanoes, show_hotspots,
             height, session_key)


@st.fragment(run_every=f"{TICK_SECONDS}s")
def _tv_tick(status_ph, content_ph, show_volcanoes: bool, show_hotspots: bool,
             height: int, session_key: str):
    """Tick cada 5s: avanza el slot, actualiza reloj siempre y el contenido
    pesado SOLO si el slot cambio (RGB 15s = 3 ticks, VOLCAT 10s = 2 ticks)."""
    from src.fetch.volcat_api import ZONE_TO_SECTOR
    from dashboard.map_helpers import render_compact_legend

    rgb_ticks = max(1, RGB_SECONDS // TICK_SECONDS)        # 3
    volcat_ticks = max(1, VOLCAT_SECONDS // TICK_SECONDS)  # 2
    slots: list[tuple] = []
    for p in PRODUCT_LIST:
        slots += [("rgb", p, None)] * rgb_ticks
    for zona, (sector, instr) in ZONE_TO_SECTOR.items():
        slots += [("volcat", zona, (sector, instr))] * volcat_ticks

    if session_key not in st.session_state:
        st.session_state[session_key] = 0
    idx = st.session_state[session_key] % len(slots)
    kind, val, extra = slots[idx]
    st.session_state[session_key] = (idx + 1) % len(slots)

    # Scan dt (solo RGB) para el panel de estado.
    scan_dt = None
    if kind == "rgb":
        ts_for_status = _recent_ts(val, n=1)
        scan_dt = parse_rammb_ts(ts_for_status[0]) if ts_for_status else None

    # RELOJ/ESTADO: cada tick (es texto, no parpadea notoriamente).
    with status_ph.container():
        _render_tv_status(scan_dt)

    # CONTENIDO PESADO: solo cuando el slot CAMBIA -> sin parpadeo intermedio.
    if st.session_state.get("tv_last_slot") != (kind, val):
        st.session_state["tv_last_slot"] = (kind, val)
        with content_ph.container():
            if kind == "rgb":
                render_compact_legend(
                    val,
                    extra_left="<span style='color:#ff6644; font-weight:700; "
                               "margin-right:0.2rem;'>🔄</span>",
                )
                _render_4_zonas_inner(val, show_volcanoes, show_hotspots,
                                      "1x4", height, minimal=True,
                                      stable_keys=True)
            else:  # volcat — una zona en grande
                sector, instr = extra
                st.markdown(
                    f"<div class='tv-legend' style='display:flex; "
                    f"justify-content:space-between; align-items:center; "
                    f"background:rgba(17,24,34,0.85); padding:0.3rem 0.8rem; "
                    f"border-radius:4px; font-size:0.82rem;'>"
                    f"<span style='color:#ff6644; font-weight:700;'>🔄 VOLCAT · "
                    f"Altura de pluma (km AMSL) · Zona {val}</span>"
                    f"<span style='color:#8899aa;'>SSEC/CIMSS · Pavolonis 2013 · "
                    f"GOES-19</span></div>",
                    unsafe_allow_html=True,
                )
                _render_volcat_one_zona_tv(val, sector, instr, height)

    # ── PRE-FETCH del proximo slot DISTINTO (best-effort) ────────────
    try:
        nxt = st.session_state[session_key]
        for j in range(len(slots)):
            nk, nv, ne = slots[(nxt + j) % len(slots)]
            if (nk, nv) == (kind, val):
                continue
            if nk == "rgb":
                _recent_ts(nv, n=3)
            else:
                ns, ni = ne
                from dashboard.views.volcat_viewer import (
                    _volcat_latest_cached, _volcat_image_with_overlays,
                    _volcat_map_only,
                )
                m = _volcat_latest_cached(ns, ni, "Ash_Height")
                if m:
                    if VOLCAT_TV_RENDER == "plotly_volcanes":
                        _volcat_map_only(m["image_url"], m.get("latlon_url"),
                                         m.get("coords") or {})
                    else:
                        _volcat_image_with_overlays(
                            m["image_url"], m.get("volcanoes_url"),
                            m.get("latlon_url"))
            break
    except Exception:
        pass


@st.fragment(run_every=f"{ROTATION_SECONDS}s")
def _rotating_grid_4_zonas(show_volcanoes: bool, show_hotspots: bool,
                            layout: str = "1x4", height: int = 820,
                            session_key: str = "zonas_rot_idx",
                            chrome: bool = True,
                            include_volcat: bool = False):
    """Auto-rotate productos cada 10s en loop: GeoColor -> Ash -> SO2 [-> VOLCAT].

    chrome=True: muestra banner "ROTANDO PRODUCTOS" arriba.
    chrome=False: solo las imágenes, sin banner — modo TV puro.
    include_volcat=True: agrega VOLCAT (altura de pluma, 3 zonas) como 4to
        item de la rotacion. Util para la pantalla de sala 24/7 que no se
        toca manualmente.

    El indice del producto vive en st.session_state.
    """
    # Rotacion: 3 RGB de RAMMB + opcionalmente VOLCAT (altura) como 4to.
    rotation = list(PRODUCT_LIST) + (["volcat"] if include_volcat else [])
    _label = {**PRODUCT_OPTIONS, "volcat": "VOLCAT · Altura de pluma"}

    if session_key not in st.session_state:
        st.session_state[session_key] = 0
    idx = st.session_state[session_key] % len(rotation)
    current = rotation[idx]
    next_idx = (idx + 1) % len(rotation)
    next_product = rotation[next_idx]

    if chrome:
        # Banner de rotacion arriba (modo normal con toolbar)
        st.markdown(
            f"<div style='background:linear-gradient(90deg, rgba(204,51,17,0.2), "
            f"rgba(238,119,51,0.2)); border-left:4px solid #ff6644; "
            f"padding:0.5rem 0.9rem; border-radius:4px; margin-bottom:0.4rem; "
            f"display:flex; justify-content:space-between; align-items:center; "
            f"font-size:0.9rem;'>"
            f"<span style='color:#ff6644; font-weight:700;'>"
            f"🔄 ROTANDO PRODUCTOS · cada {ROTATION_SECONDS}s</span>"
            f"<span style='color:#e0e0e0;'>Mostrando: <b>{_label[current]}</b> "
            f"→ próximo: {_label[next_product]}</span></div>",
            unsafe_allow_html=True,
        )
    elif current == "volcat":
        # Leyenda compacta VOLCAT (no aplica render_compact_legend de RGB).
        st.markdown(
            f"<div style='display:flex; justify-content:space-between; "
            f"align-items:center; background:rgba(17,24,34,0.85); "
            f"padding:0.3rem 0.8rem; border-radius:4px; font-size:0.82rem;'>"
            f"<span style='color:#ff6644; font-weight:700;'>🔄 VOLCAT · "
            f"Altura de pluma (km AMSL)</span>"
            f"<span style='color:#8899aa;'>SSEC/CIMSS · Pavolonis 2013 · "
            f"GOES-19 · 3 zonas</span></div>",
            unsafe_allow_html=True,
        )
    else:
        # Modo TV puro RGB: leyenda compacta interpretativa que cambia con
        # el producto. Status badge a la derecha con scan + refresh.
        from dashboard.map_helpers import render_compact_legend, render_scan_status_badge
        ts_for_status = _recent_ts(current, n=1)
        scan_dt_status = parse_rammb_ts(ts_for_status[0]) if ts_for_status else None
        render_compact_legend(
            current,
            extra_left=(f"<span style='color:#ff6644; font-weight:700; "
                        f"margin-right:0.2rem;'>🔄</span>"),
            extra_right=render_scan_status_badge(scan_dt_status, ROTATION_SECONDS),
        )

    st.session_state[session_key] = next_idx
    if current == "volcat":
        _render_volcat_zonas_tv(height)
    else:
        _render_4_zonas_inner(current, show_volcanoes, show_hotspots, layout, height,
                              minimal=not chrome)


@st.fragment(run_every=f"{REFRESH_SECONDS}s")
def _grid_4_zonas(product: str, show_volcanoes: bool, show_hotspots: bool,
                  layout: str = "2x2", height: int = 720):
    """Renderiza las 4 zonas en grilla.

    layout:
        '2x2'  — 2 filas de 2 columnas (default, balanceado)
        '1x4'  — 1 fila de 4 columnas (monitor 24/7 horizontal)
    height: altura en px de cada plot.
    """
    _render_4_zonas_inner(product, show_volcanoes, show_hotspots, layout, height)


def _render_4_zonas_inner(product: str, show_volcanoes: bool, show_hotspots: bool,
                           layout: str, height: int, minimal: bool = False,
                           stable_keys: bool = False):
    """Logica compartida entre _grid_4_zonas y _rotating_grid_4_zonas.

    minimal=True: oculta banner status arriba (modo TV puro).
    stable_keys=True: da un `key` fijo por zona a cada st.plotly_chart. Asi
        Streamlit ACTUALIZA el chart in-place (Plotly.react) en vez de
        destruirlo y recrearlo en cada tick -> elimina el parpadeo del
        re-render cada 5s del Modo Sala TV. (jun 2026)
    """
    timestamps = _recent_ts(product, n=3)
    if not timestamps:
        if minimal:  # TV: mensaje prolijo, no una caja roja de error
            st.markdown(
                "<div style='color:#d29922; text-align:center; padding:4rem; "
                "font-size:1rem;'>⏳ Esperando a RAMMB/CIRA — "
                "reintentando en el próximo ciclo…</div>",
                unsafe_allow_html=True)
        else:
            st.error("RAMMB no respondió.")
        return

    ts = timestamps[0]
    now = datetime.now(timezone.utc)
    try:
        scan_dt = parse_rammb_ts(ts)
        age_min = int((now - scan_dt).total_seconds() / 60)
    except Exception:
        scan_dt = None
        age_min = -1

    # Banner status
    if age_min < 0:
        bnr_color = "#888"; bnr_msg = "Sin scan disponible"
    elif age_min < 15:
        bnr_color = "#3fb950"; bnr_msg = f"Scan hace {age_min} min · OK"
    elif age_min < 30:
        bnr_color = "#d29922"; bnr_msg = f"Scan hace {age_min} min · RAMMB lento"
    else:
        bnr_color = "#ff4444"; bnr_msg = f"Scan hace {age_min} min · datos atrasados"

    if not minimal:
        st.markdown(
            f"<div style='background:#0f1418; border-left:4px solid {bnr_color}; "
            f"padding:0.4rem 0.8rem; border-radius:4px; margin-bottom:0.4rem; "
            f"display:flex; justify-content:space-between;'>"
            f"<span style='color:#e0e0e0;'>{PRODUCT_OPTIONS[product]} · "
            f"4 zonas en paralelo</span>"
            f"<span style='color:{bnr_color}; font-weight:600;'>{bnr_msg}</span>"
            f"</div>",
            unsafe_allow_html=True,
        )

    # Layout configurable
    if layout == "1x4":
        rows_zones = [["norte", "centro", "sur", "austral"]]
        n_cols = 4
    else:  # default 2x2
        rows_zones = [["norte", "centro"], ["sur", "austral"]]
        n_cols = 2

    # ── Fetch PARALELO de las 4 zonas ────────────────────────────
    # Antes: for serial -> 4 zonas x ~1-2s c/u = 4-8s "una por una"
    # visible al usuario (lo que reporto en HF).
    # Ahora: ThreadPoolExecutor con 4 workers -> todas en paralelo,
    # el tiempo total ~= zona mas lenta. fetch_frame_robust es
    # thread-safe (solo usa vars locales, sin estado compartido).
    from concurrent.futures import ThreadPoolExecutor
    all_zones = [z for row in rows_zones for z in row]

    def _fetch_one(zone_key: str):
        bounds_z = VOLCANIC_ZONES[zone_key]
        img_z, used_ts_z, used_zoom_z = fetch_frame_robust(
            product, timestamps, bounds_z,
            zoom_preferred=ZOOM_ZONE, zoom_fallback=ZOOM_ZONE - 1,
        )
        hotspots_z = []
        if show_hotspots:
            try:
                hotspots_z, _ = _hotspots_zone(zone_key)
            except Exception:
                hotspots_z = []
        return zone_key, img_z, used_ts_z, used_zoom_z, hotspots_z

    results: dict = {}
    with ThreadPoolExecutor(max_workers=4) as ex:
        for zk, img_z, used_ts_z, used_zoom_z, hs_z in ex.map(_fetch_one, all_zones):
            results[zk] = (img_z, used_ts_z, used_zoom_z, hs_z)

    # Hora del scan en UTC + local Chile, para mostrar en cada panel.
    from dashboard.utils import fmt_both
    time_label = fmt_both(scan_dt) if scan_dt else ""

    # ── Render serial (debe correr en thread principal Streamlit) ─
    fallback_count = 0
    for row_zones in rows_zones:
        cols = st.columns(n_cols)
        for i, zone_key in enumerate(row_zones):
            img, used_ts, used_zoom, hotspots = results[zone_key]
            if used_ts and used_ts != ts:
                fallback_count += 1
            if used_zoom < ZOOM_ZONE:
                fallback_count += 1

            label = ZONE_LABELS[zone_key]
            if used_ts and used_ts != ts:
                label += " ⚠ ts cercano"

            with cols[i]:
                st.plotly_chart(
                    _zone_fig(img, zone_key, label, hotspots,
                              height=height, show_volcanoes=show_volcanoes,
                              time_label=time_label),
                    width='stretch',
                    # responsive=True: plotly escucha resize del iframe
                    # y refit el chart. CRITICO para TV mode donde CSS
                    # fuerza `height: calc(100vh - 56px)` — sin esto el
                    # plot quedaria renderizado al `height` python fijo
                    # (820/900) sin importar el viewport real.
                    config={"displayModeBar": False, "responsive": True},
                    key=f"tvgrid_{zone_key}" if stable_keys else None,
                )


def render():
    # CSS agresivo: oculta header Streamlit, padding mínimo, casi full screen
    st.markdown(
        """
        <style>
          [data-testid="stHeader"] { background: rgba(0,0,0,0); height: 0; }
          .block-container {
            padding-top: 0.4rem !important;
            padding-bottom: 0.4rem !important;
            padding-left: 0.6rem !important;
            padding-right: 0.6rem !important;
            max-width: 100% !important;
          }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Header compacto + selectores en 1 linea
    cols = st.columns([1.6, 1.2, 1.0, 1.2, 1.0, 1.0])
    with cols[0]:
        st.markdown(
            "<div style='font-size:1.2rem; font-weight:800; color:#ff6644; "
            "padding-top:0.3rem;'>🗺 4 ZONAS</div>",
            unsafe_allow_html=True,
        )
    with cols[1]:
        rotate = st.toggle(
            "🔄 Auto-rotate (10s)", value=False, key="zonas_rotate",
            help=f"Cicla productos GeoColor → Ash → SO2 → ... cada "
                 f"{ROTATION_SECONDS}s. Ideal para 1 monitor en sala.",
        )
    with cols[2]:
        if not rotate:
            product = st.selectbox(
                "Producto",
                options=list(PRODUCT_OPTIONS.keys()),
                format_func=lambda k: PRODUCT_OPTIONS[k],
                index=0, key="zonas_product",
                label_visibility="collapsed",
            )
        else:
            product = "eumetsat_ash"  # ignorado en modo rotate
            st.markdown(
                "<div style='color:#888; padding-top:0.5rem; font-size:0.8rem;'>"
                "(rotando)</div>",
                unsafe_allow_html=True,
            )
    with cols[3]:
        layout_label = st.radio(
            "Layout",
            ["1×4 (TV)", "2×2"],
            index=0, key="zonas_layout",
            horizontal=True,
            label_visibility="collapsed",
        )
    with cols[4]:
        show_volcanoes = st.toggle(
            "🔺 Volcanes", value=True, key="zonas_volc",
        )
    with cols[5]:
        show_hotspots = st.toggle(
            "🔥 Hot spots", value=True, key="zonas_hs",
        )

    layout_key = "1x4" if layout_label.startswith("1×4") else "2x2"
    height = 820 if layout_key == "1x4" else 720
    if rotate:
        _rotating_grid_4_zonas(show_volcanoes, show_hotspots,
                                layout=layout_key, height=height,
                                session_key="zonas_rot_idx_main")
    else:
        _grid_4_zonas(product, show_volcanoes, show_hotspots,
                      layout=layout_key, height=height)
