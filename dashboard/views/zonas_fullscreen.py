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


@st.cache_data(ttl=900, show_spinner=False)
def _zone_frame_cached(product: str, timestamps: tuple, zone_key: str,
                       uniform: bool):
    """Frame RGB de una zona, CACHEADO (imagen ya reproyectada).

    fetch_frame_robust NO está cacheado: cada aparición del slot re-descargaba
    (~12s frío) y re-reproyectaba (~2s) las 4 zonas. Acá cacheamos el resultado
    keyed por (product, timestamps, zona, uniform). Como `timestamps` incluye
    el último scan (via _recent_ts, ttl 30s), la cache se invalida sola cuando
    llega un scan nuevo -> sin staleness. Repetidas apariciones = instantáneas.
    """
    bounds = (_uniform_aspect_bounds()[zone_key] if uniform
              else VOLCANIC_ZONES[zone_key])
    return fetch_frame_robust(
        product, list(timestamps), bounds,
        zoom_preferred=ZOOM_ZONE, zoom_fallback=ZOOM_ZONE - 1)


def _array_to_data_url(arr):
    # Lazy import (gotcha Streamlit Cloud — ver CLAUDE.md).
    from dashboard.map_helpers import array_to_data_url
    return array_to_data_url(arr)



def _zone_fig(img: np.ndarray | None, zone_key: str, label: str,
              hotspots: list[HotSpot], height: int = 720,
              show_volcanoes: bool = True, time_label: str = "",
              bounds_override: dict | None = None):
    # bounds_override: bounds custom (ej. los de aspect UNIFORME del TV, para
    # que las 4 zonas se vean del mismo tamano). Si None, usa la zona estandar.
    bounds = bounds_override or VOLCANIC_ZONES[zone_key]
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
    # constrain="domain": CLAVE para llenar el espacio. Con scaleanchor (aspecto
    # bloqueado) + un contenedor de otra proporcion, el solver de Plotly por
    # default ENCOGE el area de datos y la centra (quedaba 215x489 en una caja
    # de 380x689 = 56% ancho / 70% alto desperdiciado). Con constrain="domain"
    # Plotly llena el 100% de la dimension mayor (altura) y centra en la otra.
    # Combinado con bounds de aspecto UNIFORME (todas las zonas 0.439), las 4
    # quedan ~302x689: identicas entre si Y +40% mas grandes. (2026-06-08)
    fig.update_xaxes(range=[bounds["lon_min"], bounds["lon_max"]],
                     showgrid=False, visible=False, constrain="domain")
    fig.update_yaxes(range=[bounds["lat_min"], bounds["lat_max"]],
                     showgrid=False, visible=False,
                     scaleanchor="x", scaleratio=1.0 / cos_lat,
                     constrain="domain")
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

# ── VOLCAT en 4 zonas (igualar el grid RGB Norte/Centro/Sur/Austral) ──
# VOLCAT_ZONAS_4=True  -> 4 columnas. 'Sur' se ACOTA a -46..-36 y 'Austral'
#   toma la franja -56..-46 (ambos del sector Chile_South, recorte distinto via
#   view-bounds). Render por RECORTE georef (plotly), para que Austral != Sur.
# VOLCAT_ZONAS_4=False -> comportamiento previo: 3 zonas con el render que diga
#   VOLCAT_TV_RENDER (ssec_overlay clasico por defecto). Flag de revert. (jun 2026)
#
# REVERTIDO a False (jun 2026): el modo 4 zonas RECORTABA el sector (Austral no
# existe en VOLCAT -> recorte de Chile_South) y las imagenes se veian "cortadas"
# vs el original. Volvemos a las 3 zonas con la imagen SSEC completa. Si se
# quiere reintentar 4 zonas, hay que mejorar el encuadre del recorte primero.
VOLCAT_ZONAS_4 = False

VOLCAT_VIEW_4 = {
    "Norte":   {"lat_min": -28.0, "lat_max": -15.5, "lon_min": -71.5, "lon_max": -66.5},
    "Centro":  {"lat_min": -39.0, "lat_max": -28.0, "lon_min": -73.0, "lon_max": -68.0},
    "Sur":     {"lat_min": -46.0, "lat_max": -36.0, "lon_min": -77.0, "lon_max": -70.0},
    "Austral": {"lat_min": -56.0, "lat_max": -45.5, "lon_min": -77.0, "lon_max": -70.0},
}


def _volcat_zone_specs():
    """Specs de zonas VOLCAT: lista de (zona, sector, instr, view_bounds).

    Si VOLCAT_ZONAS_4 -> 4 zonas con recorte (view_bounds por zona, Austral =
    recorte austral de Chile_South). Si no -> 3 zonas con view_bounds None
    (cae al render ssec_overlay clasico). Fuente unica para todos los grids
    VOLCAT por zona (TV rotacion, sub-tab Modo Guardia).
    """
    from src.fetch.volcat_api import ZONE_TO_SECTOR, ZONE_TO_SECTOR_4
    if VOLCAT_ZONAS_4:
        return [(z, s, i, VOLCAT_VIEW_4[z])
                for z, (s, i) in ZONE_TO_SECTOR_4.items()]
    return [(z, s, i, None) for z, (s, i) in ZONE_TO_SECTOR.items()]


def _render_volcat_zone_cell(zona, sector, instr, view_bounds, product,
                             height):
    """Render de UNA celda VOLCAT (dentro de su columna ya abierta).

    view_bounds dado  -> recorte georef con plotly (_volcat_map_only +
        _volcat_zone_fig), encuadrado a `view_bounds`. Asi Austral (recorte
        sur de Chile_South) se ve distinto de Sur. Modo de 4 zonas.
    view_bounds None  -> render ssec_overlay clasico (st.image de la imagen
        SSEC completa). Modo de 3 zonas (revert).
    """
    from dashboard.views.volcat_viewer import (
        _volcat_dt_obj, _volcat_image_bytes, _volcat_image_with_overlays,
        _volcat_latest_cached, _volcat_map_only,
    )
    from dashboard.utils import fmt_both

    try:
        meta = _volcat_latest_cached(sector, instr, product)
    except Exception:
        meta = None
    if not meta:
        st.markdown(
            f"<div style='color:#ff6644; font-weight:800;'>Zona {zona}</div>"
            f"<div style='color:#7a8a9a; padding:2rem 0; text-align:center;'>"
            f"VOLCAT sin frame</div>", unsafe_allow_html=True)
        return
    dt = _volcat_dt_obj(meta.get("datetime"))
    time_label = fmt_both(dt) if dt else ""

    if view_bounds is not None:
        data = _volcat_map_only(meta["image_url"], meta.get("latlon_url"),
                                meta.get("coords") or {})
        if not data:
            st.markdown(
                f"<div style='color:#ff6644; font-weight:800;'>Zona {zona}"
                f"</div><div style='color:#7a8a9a; padding:2rem 0; "
                f"text-align:center;'>VOLCAT sin frame</div>",
                unsafe_allow_html=True)
            return
        st.plotly_chart(
            _volcat_zone_fig(data["png"], data["bounds"], view_bounds,
                             f"Zona {zona}", time_label, height),
            width='stretch',
            config={"displayModeBar": False, "responsive": True},
            key=f"volcat4_{zona}_{product}",
        )
    else:  # ssec_overlay clasico (3 zonas)
        st.markdown(
            f"<div style='font-weight:800; color:#ff6644; font-size:0.95rem; "
            f"margin-bottom:0.2rem;'>Zona {zona} <span style='color:#aabbc8; "
            f"font-weight:400; font-size:0.78rem;'>· {time_label}</span></div>",
            unsafe_allow_html=True)
        img = _volcat_image_with_overlays(
            meta["image_url"], meta.get("volcanoes_url"),
            meta.get("latlon_url"))
        if img:
            st.image(img, width='stretch')
    # Colorbar del producto.
    leg = _volcat_image_bytes(meta["legend_url"])
    if leg:
        st.image(leg, width='stretch')


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
    """Render de las zonas VOLCAT (altura de pluma) en fila, para el Modo
    Sala TV. 4 zonas con VOLCAT_ZONAS_4 (Austral=recorte sur), 3 si no.

    El modo lo decide la constante VOLCAT_TV_RENDER (feature flag):
    - "ssec_overlay": imagen SSEC clasica (titulo, grilla, todos los
      volcanes de SSEC) via st.image. Despliegue por defecto actual.
    - "plotly_volcanes": render propio con plotly, mapa recortado +
      nuestros volcanes + frontera. Mas limpio (activable mas adelante).
    """
    specs = _volcat_zone_specs()
    cols = st.columns(len(specs))
    for col, (zona, sector, instr, view_bounds) in zip(cols, specs):
        with col:
            _render_volcat_zone_cell(zona, sector, instr, view_bounds,
                                     "Ash_Height", height)


def _render_volcat_one_zona_tv(zona: str, sector: str, instr: str, height: int,
                               view_bounds: dict | None = None):
    """Render de UNA sola zona VOLCAT, en grande y centrada, para la
    rotacion del Modo Sala TV (una zona a la vez).

    view_bounds dado (modo 4 zonas) -> recorte georef plotly a ese encuadre
    (Austral = recorte sur de Chile_South). view_bounds None -> usa el modo
    VOLCAT_TV_RENDER clasico (ssec_overlay por defecto)."""
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
    if view_bounds is not None or VOLCAT_TV_RENDER == "plotly_volcanes":
        data = _volcat_map_only(meta["image_url"], meta.get("latlon_url"),
                                meta.get("coords") or {})
        if data:
            sb = data["bounds"]
            # view_bounds (4 zonas) recorta a la franja de la zona; si no, el
            # encuadre clasico acotado a la franja chilena.
            vb = view_bounds or {
                "lat_min": sb["lat_min"], "lat_max": sb["lat_max"],
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
            # st.image (NO base64 inline): sirve la imagen por URL /media/,
            # que el navegador CACHEA por hash -> al rotar a la misma zona en
            # el proximo ciclo NO re-descarga ni re-parsea ~730KB. Mucho mas
            # fluido que inyectar el data URL en el HTML cada render. El
            # centrado + tamano lo da el CSS del TV (margin auto sobre el
            # contenedor stImage, que toma el ancho de la imagen). (jun 2026)
            st.image(img)


def _compose_volcan_panels(v, radius_deg: float, panels: list, ph: int = 720):
    """Compone los N productos centrados en el volcán en UNA imagen (PIL).

    Por qué imagen y no 3 charts Plotly: en el Modo Sala TV el fragment
    re-renderiza cada 12s y Plotly (con responsive) se 'achicaba' un instante
    en la transición. st.image es estático (sin ResizeObserver) -> sin glitch,
    igual que el slot VOLCAT. Además, 3 paneles lado a lado dan aspecto ~2.2:1
    que llena el TV mejor que 3 cuadrados.

    Dibuja anillos de distancia CIRCULARES (panel km-proporcional: pw=ph·cosφ)
    + triángulo del cráter + hotspots.
    """
    import numpy as np
    from PIL import Image, ImageDraw

    from dashboard.views.modo_guardia_volcan import RING_RADII_KM, _load_font

    cos_lat = max(0.1, float(np.cos(np.radians(v.lat))))
    pw = int(round(ph * cos_lat))            # km-proporcional -> anillos = círculos
    km_per_px = (2 * radius_deg * 111.0) / ph
    label_h = 42
    gap = 8
    b = {"lat_min": v.lat - radius_deg, "lat_max": v.lat + radius_deg,
         "lon_min": v.lon - radius_deg, "lon_max": v.lon + radius_deg}
    lon_span = b["lon_max"] - b["lon_min"]
    lat_span = b["lat_max"] - b["lat_min"]
    f_label = _load_font(20)
    f_small = _load_font(13)
    f_ring = _load_font(12)

    def _xy(lat, lon):
        return ((lon - b["lon_min"]) / lon_span * pw,
                label_h + (b["lat_max"] - lat) / lat_span * ph)

    tiles = []
    for label, img, ts_label, hs in panels:
        tile = Image.new("RGB", (pw, ph + label_h), (10, 14, 20))
        if img is not None:
            pim = Image.fromarray(np.asarray(img, dtype="uint8")).convert("RGB")
            tile.paste(pim.resize((pw, ph)), (0, label_h))
        d = ImageDraw.Draw(tile)
        if img is None:
            d.text((pw // 2 - 36, label_h + ph // 2), "sin imagen",
                   fill=(120, 130, 145), font=f_small)
        cx, cy = pw / 2.0, label_h + ph / 2.0
        for r_km in RING_RADII_KM:
            rpx = r_km / km_per_px
            d.ellipse([cx - rpx, cy - rpx, cx + rpx, cy + rpx],
                      outline=(210, 215, 225), width=1)
            if cy - rpx > label_h + 4:
                d.text((cx + 3, cy - rpx - 2), f"{r_km} km",
                       fill=(210, 215, 225), font=f_ring)
        if hs:
            for h in hs:
                hx, hy = _xy(h.lat, h.lon)
                d.polygon([(hx, hy - 6), (hx + 6, hy), (hx, hy + 6),
                           (hx - 6, hy)], fill=(255, 51, 0),
                          outline=(255, 255, 255))
        d.polygon([(cx, cy - 9), (cx + 8, cy + 6), (cx - 8, cy + 6)],
                  fill=(0, 255, 255), outline=(255, 255, 255))
        d.rectangle([0, 0, pw, label_h], fill=(15, 20, 28))
        d.text((6, 3), label, fill=(255, 102, 68), font=f_label)
        d.text((6, 25), ts_label, fill=(150, 160, 180), font=f_small)
        tiles.append(tile)

    total_w = len(tiles) * pw + (len(tiles) - 1) * gap
    out = Image.new("RGB", (total_w, ph + label_h), (10, 14, 20))
    for i, t in enumerate(tiles):
        out.paste(t, (i * (pw + gap), 0))
    return out


@st.cache_data(ttl=600, show_spinner=False)
def _volcan_zoom_png(volcano_name: str, bucket: str, show_hotspots: bool):
    """Imagen compuesta del zoom (CACHEADA por bucket de tiempo) -> bytes PNG.

    Antes el slot bajaba los 3 productos EN SERIE (~9s) + el manifiesto hi-res
    DENTRO de su ventana de 12s -> la imagen aparecía recién a los ~9s y se veía
    solo ~3s. Ahora:
    - Fetch de los 3 productos EN PARALELO (ThreadPool) -> ~5s en frío.
    - Resultado cacheado por `bucket` (5 min): tras la 1a aparición de cada
      bucket, las siguientes son INSTANTÁNEAS y el slot llena sus 12s.
    """
    import io
    from concurrent.futures import ThreadPoolExecutor
    from datetime import datetime, timezone

    from dashboard.views.modo_guardia_volcan import (
        PRODUCTS, RADIUS_DEG as V_RADIUS, _hotspots_volcan, fetch_volcan_product,
    )
    from src.volcanos import get_volcano

    v = get_volcano(volcano_name)
    if v is None:
        return None
    bounds = {
        "lat_min": v.lat - V_RADIUS, "lat_max": v.lat + V_RADIUS,
        "lon_min": v.lon - V_RADIUS, "lon_max": v.lon + V_RADIUS,
    }
    now = datetime.now(timezone.utc)

    hotspots = []
    if show_hotspots:
        try:
            hotspots, _ = _hotspots_volcan(
                bounds["lat_min"], bounds["lat_max"],
                bounds["lon_min"], bounds["lon_max"])
        except Exception:
            hotspots = []

    def _one(item):
        prod_id, label, _recipe = item
        img, ts_label = fetch_volcan_product(
            prod_id, v.name, v.lat, v.lon, bounds, now)
        return prod_id, label, img, ts_label

    with ThreadPoolExecutor(max_workers=3) as ex:
        results = list(ex.map(_one, PRODUCTS))   # preserva orden de PRODUCTS

    panels = []
    for prod_id, label, img, ts_label in results:
        hs = hotspots if prod_id == "eumetsat_ash" else None
        panels.append((label, img, ts_label, hs))

    composed = _compose_volcan_panels(v, V_RADIUS, panels)
    buf = io.BytesIO()
    composed.save(buf, format="PNG")
    return buf.getvalue()


def _render_volcan_zoom_tv(volcano_name: str, show_hotspots: bool, height: int):
    """Slot TV: zoom a UN volcán, sus 3 productos centrados lado a lado.

    Ash · GeoColor · SO2 centrados en el volcán (radio ~38 km, con anillos de
    distancia). El panel GeoColor hace el SWITCH automático a hi-res L1b
    visible diurno vía fetch_volcan_product (mismo motor que la página
    completa tv=volcan). Ash/SO2 son IR (RAMMB, 2 km nativo).
    """
    # SOLO LEE el PNG ya producido en background (nunca compone en foreground,
    # que con cache frio tardaba ~6s y bloqueaba el fragment). El estilo INLINE
    # del <img> mantiene aspecto (anillos circulares) y mismo ciclo de vida que
    # la imagen -> sin pestaneo. Ver prewarm_tv_caches / _emit_tv_png.
    png = _TV_PRODUCED.get(f"volcan:{volcano_name}")
    if png:
        _emit_tv_png(png)
    else:
        _tv_placeholder(f"Preparando zoom {volcano_name} "
                        f"— se compone en segundo plano…")


# ── Rotacion del Modo Sala TV con CADENCIA UNIFORME ──────────────────
# Todos los slots (GeoColor/Ash/SO2 y cada zona VOLCAT) duran lo mismo. El
# fragment corre cada TV_SLOT_SECONDS y re-renderiza UNA vez por slot, al
# cambiar -> sin parpadeo. Tiempos mixtos (15/10) requerian un tick de 5s
# que causaba el parpadeo, asi que se uniformo. (jun 2026)
# Para cambiar la velocidad de la rotacion, editar SOLO esta constante.
TV_SLOT_SECONDS = 12

# Volcanes con slot de zoom dedicado en la rotacion TV (3 productos centrados,
# con switch hi-res en GeoColor). Agregar nombres del CATALOG para sumar mas.
TV_VOLCAN_ZOOMS = ["Villarrica"]


def _render_tv_status(scan_dt=None, scan_label="scan",
                      ok_min=15, warn_min=30):
    """Panel de estado OVERLAY (esquina superior derecha) del Modo Sala TV:
    reloj actual (UTC + local) y, si se da scan_dt, la edad del ultimo scan
    con color de alerta (verde <ok_min, amarillo <warn_min, rojo si mas).

    Los umbrales son por-producto: RAMMB es ~6-10 min (ok=15/warn=30), pero
    VOLCAT tiene latencia EXTERNA de SSEC ~30-50 min (normal, no es caida) ->
    se pasa ok=60/warn=120 y scan_label='VOLCAT' para no alarmar de mas.
    Util para que el operador 24/7 vea de un vistazo el estado real. (jun 2026)"""
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
        color = "#3fb950" if age < ok_min else "#d29922" if age < warn_min else "#ff4444"
        alert = "" if age < warn_min else " ⚠"
        parts.append(
            f"<div style='color:{color}; font-weight:700; font-size:0.74rem; "
            f"margin-top:2px;'>● {scan_label} hace {age} min{alert}</div>")
    st.markdown(
        f"<div class='tv-status' style='text-align:right;'>{''.join(parts)}</div>",
        unsafe_allow_html=True,
    )


@st.fragment(run_every=f"{TV_SLOT_SECONDS}s")
def _rotating_tv_zonas(show_volcanoes: bool, show_hotspots: bool,
                       height: int = 900, session_key: str = "tv_rot_idx"):
    """Rotacion del Modo Sala TV con CADENCIA UNIFORME (TV_SLOT_SECONDS).

    NO-PARPADEO (jun 2026): el fragment corre cada TV_SLOT_SECONDS (= la
    duracion de un slot), asi RE-RENDERIZA EXACTAMENTE UNA VEZ por slot,
    justo al cambiar. Antes corria cada 5s (tiempos mixtos) y redibujaba el
    grid RGB 3 veces durante sus 15s -> parpadeo. El patron de placeholders
    selectivos NO funciono (Streamlit no renderiza contenido pesado escrito
    en un st.empty desde un fragment run_every). La cadencia uniforme es la
    solucion robusta.
    """
    from dashboard.map_helpers import render_compact_legend

    # Rotacion (12s c/u): 3 RGB (4 zonas grid) + N zonas VOLCAT (1 en grande)
    # + zoom a Villarrica (sus 3 productos centrados, con switch hi-res).
    # VOLCAT: 4 zonas con VOLCAT_ZONAS_4 (Austral=recorte sur), 3 si no.
    _vspecs = _volcat_zone_specs()
    slots: list[tuple] = [("rgb", p, None) for p in PRODUCT_LIST]
    slots += [("volcat", zona, (sector, instr, vb))
              for zona, sector, instr, vb in _vspecs]
    slots += [("volcan", v, None) for v in TV_VOLCAN_ZOOMS]

    # INDICE BASADO EN RELOJ (no en session_state): el slot es funcion del
    # tiempo de pared -> (epoch // TV_SLOT_SECONDS) % N. CLAVE: si el watchdog
    # de reconexion (o cualquier reconnect de Streamlit) RECARGA la pagina, el
    # session_state se borra y con el viejo contador la rotacion VOLVIA a slot 0
    # (Ash RGB) y parecia "trabada". Con reloj, tras una recarga retoma el slot
    # que toca por tiempo -> la rotacion se ve continua igual. (jun 2026)
    from datetime import datetime, timezone
    idx = int(datetime.now(timezone.utc).timestamp()
              // TV_SLOT_SECONDS) % len(slots)
    kind, val, extra = slots[idx]

    scan_dt = None
    status_kwargs = {}
    if kind == "rgb":
        ts_for_status = _recent_ts(val, n=1)
        scan_dt = parse_rammb_ts(ts_for_status[0]) if ts_for_status else None
    elif kind == "volcat":
        # Mostrar la edad REAL del frame VOLCAT (latencia externa SSEC ~40 min,
        # normal). Umbrales propios para no marcarlo en rojo de más.
        sector, instr, _vb = extra
        try:
            from dashboard.views.volcat_viewer import (
                _volcat_dt_obj, _volcat_latest_cached)
            _m = _volcat_latest_cached(sector, instr, "Ash_Height")
            scan_dt = _volcat_dt_obj(_m.get("datetime")) if _m else None
        except Exception:
            scan_dt = None
        status_kwargs = dict(scan_label="VOLCAT", ok_min=60, warn_min=120)
    _render_tv_status(scan_dt, **status_kwargs)  # reloj + edad (overlay der)

    if kind == "rgb":
        render_compact_legend(
            val,
            extra_left="<span style='color:#ff6644; font-weight:700; "
                       "margin-right:0.2rem;'>🔄</span>",
        )
        if TV_ZONAS_RENDER == "image":
            # Imagen compuesta estatica (robusta, sin el bug del 4to panel).
            _render_4_zonas_image_tv(val, show_volcanoes, show_hotspots)
        else:  # "plotly" — path previo (4 charts responsive con stable_keys)
            _render_4_zonas_inner(val, show_volcanoes, show_hotspots,
                                  "1x4", height, minimal=True, stable_keys=True,
                                  uniform_size=True)
    elif kind == "volcan":  # zoom a un volcán — sus 3 productos centrados
        st.markdown(
            f"<div class='tv-legend' style='display:flex; "
            f"justify-content:space-between; align-items:center; "
            f"background:rgba(17,24,34,0.85); padding:0.3rem 0.8rem; "
            f"border-radius:4px; font-size:0.82rem;'>"
            f"<span style='color:#ff6644; font-weight:700;'>🔄 ZOOM {val} · "
            f"Ash · GeoColor · SO2 (centrados, anillos 5/10/25/50 km)</span>"
            f"<span style='color:#8899aa;'>GOES-19 · GeoColor con switch "
            f"hi-res L1b de día</span></div>",
            unsafe_allow_html=True,
        )
        _render_volcan_zoom_tv(val, show_hotspots, height)
    else:  # volcat — una zona en grande
        sector, instr, view_bounds = extra
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
        _render_volcat_one_zona_tv(val, sector, instr, height,
                                   view_bounds=view_bounds)

    # NOTA: antes habia un PRE-FETCH SINCRONO del proximo slot aca. Se quito
    # (jun 2026): bloqueaba el thread del fragment DESPUES del render. El
    # pre-calentamiento ahora vive en prewarm_tv_caches() (hilo daemon, NO
    # bloquea) -> ver abajo.


# ── Productor-consumidor del Modo Sala TV (jun 2026) ─────────────────
# PROBLEMA: el fragment foreground componia el PNG del slot en linea. Con cache
# frio (tras un REINICIO del servidor — el cache de st.cache_data es del proceso,
# un reload no lo enfria pero un restart si), componer eumetsat_ash tardaba ~54s
# (RAMMB falla intermitente en ash -> reintentos). Durante esos 54s el fragment
# no producia salida nueva y, con el override de stale, el frame PREVIO (p.ej.
# SO2) quedaba congelado nitido = "queda mucho tiempo en la misma escena".
#
# SOLUCION: desacoplar computo de display. Un hilo daemon PRODUCTOR computa los
# PNG de cada slot en background y los deja en _TV_PRODUCED; el fragment SOLO LEE
# de ahi (instantaneo, nunca bloquea). Si un slot aun no esta listo (primeros
# ~60s tras un restart), muestra un placeholder y sigue rotando. VOLCAT se sirve
# con plotly desde cache (el productor lo mantiene caliente).
_TV_PRODUCED: dict[str, bytes] = {}
_TV_PRODUCER_STARTED = False
TV_PRODUCER_PERIOD_S = 20  # cada cuanto el productor refresca todos los slots


def _emit_tv_png(png: bytes) -> None:
    """Muestra un PNG LLENANDO el viewport, centrado, sin distorsion.

    CLAVE (fix jun 2026): antes el <img> usaba width/height:auto + max-* -> el
    navegador lo mostraba a su tamano NATIVO (~1246px) sin agrandarlo, asi que
    en una pantalla de sala grande se veia CHICO. Ahora el <img> ocupa el
    viewport completo (100vw x 100vh) y object-fit:contain ESCALA la imagen
    para llenar la dimension mayor preservando el aspecto (sin recorte ni
    deformacion). Mismo ciclo de vida estilo+imagen (inline) -> sin pestaneo."""
    import base64
    b64 = base64.b64encode(png).decode()
    st.markdown(
        f"<img src='data:image/png;base64,{b64}' "
        f"style='display:block; width:100vw; height:calc(100vh - 8px); "
        f"object-fit:contain;'/>",
        unsafe_allow_html=True,
    )


def _tv_placeholder(msg: str) -> None:
    st.markdown(
        f"<div style='color:#d29922; text-align:center; padding:4rem; "
        f"font-size:1.05rem;'>⏳ {msg}</div>",
        unsafe_allow_html=True,
    )


def prewarm_tv_caches(show_hotspots: bool = True, volcan_zooms=None):
    """Arranca (1 vez por proceso) el hilo PRODUCTOR del Modo Sala TV.

    El productor corre en loop cada TV_PRODUCER_PERIOD_S y deja en _TV_PRODUCED
    el PNG de cada slot RGB y de cada zoom de volcan, y mantiene caliente el
    cache de VOLCAT. El fragment foreground solo lee -> nunca bloquea (ver el
    bloque de comentario arriba). Defensivo: cualquier fallo se traga.
    """
    import threading

    global _TV_PRODUCER_STARTED
    if _TV_PRODUCER_STARTED:
        return
    _TV_PRODUCER_STARTED = True
    zooms = volcan_zooms if volcan_zooms is not None else TV_VOLCAN_ZOOMS

    def _rgb_png(product):
        try:
            ts = tuple(_recent_ts(product, n=3))
            if ts:
                png = _compose_4_zonas_png(product, ts, True, show_hotspots)
                if png:
                    _TV_PRODUCED[f"rgb:{product}"] = png
        except Exception:
            pass

    def _produce_once():
        from datetime import datetime, timezone

        # ORDEN: lo RAPIDO primero para que la sala muestre algo en ~10s tras un
        # restart; eumetsat_ash (compose ~54s con cache frio por los reintentos
        # de RAMMB) va AL FINAL para no demorar el resto. Una vez cacheado todo,
        # cada ciclo es instantaneo.
        for product in [p for p in PRODUCT_LIST if p != "eumetsat_ash"]:
            _rgb_png(product)
        # VOLCAT: calentar el render que use el foreground segun el modo.
        # 4 zonas -> recorte georef (_volcat_map_only). 3 zonas (ssec_overlay)
        # -> imagen SSEC completa con overlays (_volcat_image_with_overlays).
        try:
            from dashboard.views.volcat_viewer import (
                _volcat_image_with_overlays, _volcat_latest_cached,
                _volcat_map_only)
            for _zona, sector, instr, _vb in _volcat_zone_specs():
                meta = _volcat_latest_cached(sector, instr, "Ash_Height")
                if not meta:
                    continue
                if VOLCAT_ZONAS_4:
                    _volcat_map_only(meta["image_url"], meta.get("latlon_url"),
                                     meta.get("coords") or {})
                else:
                    _volcat_image_with_overlays(
                        meta["image_url"], meta.get("volcanoes_url"),
                        meta.get("latlon_url"))
        except Exception:
            pass
        # Volcan zoom: PNG compuesto.
        for name in zooms:
            try:
                now = datetime.now(timezone.utc)
                bucket = f"{now:%Y%m%d%H}{(now.minute // 5) * 5:02d}"
                png = _volcan_zoom_png(name, bucket, show_hotspots)
                if png:
                    _TV_PRODUCED[f"volcan:{name}"] = png
            except Exception:
                pass
        # eumetsat_ash al final (el lento).
        if "eumetsat_ash" in PRODUCT_LIST:
            _rgb_png("eumetsat_ash")

    def _producer():
        import time as _time
        while True:
            try:
                _produce_once()
            except Exception:
                pass
            _time.sleep(TV_PRODUCER_PERIOD_S)

    t = threading.Thread(target=_producer, name="tv-producer", daemon=True)
    try:
        from streamlit.runtime.scriptrunner import add_script_run_ctx
        add_script_run_ctx(t)
    except Exception:
        pass
    try:
        t.start()
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
            f"GOES-19 · {len(_volcat_zone_specs())} zonas</span></div>",
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


def _uniform_aspect_bounds() -> dict:
    """Bounds de las 4 zonas ajustados a un MISMO aspect ratio visual.

    Cada zona tiene aspect distinto (lon*cos_lat/lat) por la correccion
    1/cos_lat, asi que en el TV se veian de tamanos muy dispares (Norte
    grande, Austral chica). Aca igualamos el aspect al de la zona mas
    'ancha' (Norte) ENSANCHANDO el lon de las australes (manteniendo el
    centro y la latitud). NO deforma (mantiene scaleanchor) y NO recorta
    volcanes (solo agrega oceano/Argentina a los lados). Con columnas
    iguales, las 4 quedan del MISMO tamano y robustas al redimensionar.
    Cacheado a nivel modulo (los bounds no cambian). (jun 2026)
    """
    global _UNIFORM_BOUNDS_CACHE
    if _UNIFORM_BOUNDS_CACHE is not None:
        return _UNIFORM_BOUNDS_CACHE
    zones = ["norte", "centro", "sur", "austral"]

    def _asp(zb):
        cl = float(np.cos(np.radians((zb["lat_min"] + zb["lat_max"]) / 2)))
        return (zb["lon_max"] - zb["lon_min"]) * cl / (zb["lat_max"] - zb["lat_min"])

    target = max(_asp(VOLCANIC_ZONES[z]) for z in zones)
    out = {}
    for z in zones:
        zb = VOLCANIC_ZONES[z]
        cl = float(np.cos(np.radians((zb["lat_min"] + zb["lat_max"]) / 2)))
        lat_span = zb["lat_max"] - zb["lat_min"]
        lon_span_new = target * lat_span / cl
        lon_c = (zb["lon_min"] + zb["lon_max"]) / 2
        out[z] = {
            "lat_min": zb["lat_min"], "lat_max": zb["lat_max"],
            "lon_min": lon_c - lon_span_new / 2,
            "lon_max": lon_c + lon_span_new / 2,
        }
    _UNIFORM_BOUNDS_CACHE = out
    return out


_UNIFORM_BOUNDS_CACHE: dict | None = None


# ── FEATURE FLAG: render del grid de 4 zonas en el Modo Sala TV ──────
# "image"  = grid de 4 zonas compuesto en UNA imagen PIL estatica (default,
#            jun 2026). Mismo patron robusto que el slot de zoom-volcan: sin
#            ResizeObserver ni Plotly.react, no hay glitch al rotar NI el bug
#            del 4to panel que no montaba con los charts Plotly + stable_keys.
# "plotly" = los 4 charts Plotly responsive con stable_keys (comportamiento
#            previo). Se preserva para revert facil — editar esta constante.
TV_ZONAS_RENDER = "image"


@st.cache_data(ttl=900, show_spinner=False)
def _compose_4_zonas_png(product: str, timestamps: tuple,
                         show_volcanoes: bool, show_hotspots: bool,
                         ph: int = 700) -> bytes | None:
    """Compone las 4 zonas RGB (Norte/Centro/Sur/Austral) en UNA imagen PNG.

    Por que imagen y no 4 charts Plotly: en el Modo Sala TV el fragment
    re-renderiza cada slot y Plotly (con responsive=True + stable_keys) era
    fragil — el 4to panel (austral) a veces no montaba y habia lag/parpadeo en
    la transicion. st.image es estatico (sin ResizeObserver) -> robusto. Mismo
    patron que _compose_volcan_panels (el slot de zoom-volcan ya lo usa).

    Usa bounds de aspect UNIFORME (las 4 zonas del mismo tamano visual) y
    dibuja en PIL: imagen RGB + triangulos de volcanes + diamantes de hotspots
    + header de zona. Cacheado por (product, timestamps, flags) -> apariciones
    repetidas del slot = instantaneas (misma ventaja que _zone_frame_cached).
    """
    import io
    from concurrent.futures import ThreadPoolExecutor

    from PIL import Image, ImageDraw

    from dashboard.views.modo_guardia_volcan import _load_font

    if not timestamps:
        return None
    ub = _uniform_aspect_bounds()
    zones = ["norte", "centro", "sur", "austral"]
    label_h = 38
    gap = 6
    f_zone = _load_font(20)
    f_volc = _load_font(12)

    def _fetch(zk):
        try:
            img, _uts, _uz = _zone_frame_cached(product, timestamps, zk, True)
        except Exception:
            img = None
        hs = []
        if show_hotspots:
            try:
                hs, _ = _hotspots_zone(zk)
            except Exception:
                hs = []
        return zk, img, hs

    with ThreadPoolExecutor(max_workers=4) as ex:
        fetched = {zk: (img, hs) for zk, img, hs in ex.map(_fetch, zones)}

    tiles = []
    for zk in zones:
        img, hs = fetched[zk]
        b = ub[zk]
        lon_span = b["lon_max"] - b["lon_min"]
        lat_span = b["lat_max"] - b["lat_min"]
        cos_lat = max(0.1, float(np.cos(np.radians(
            (b["lat_min"] + b["lat_max"]) / 2))))
        pw = max(120, int(round(ph * lon_span * cos_lat / lat_span)))

        def _xy(lat, lon):
            return ((lon - b["lon_min"]) / lon_span * pw,
                    label_h + (b["lat_max"] - lat) / lat_span * ph)

        tile = Image.new("RGB", (pw, ph + label_h), (10, 14, 20))
        if img is not None:
            pim = Image.fromarray(np.asarray(img, dtype="uint8")).convert("RGB")
            tile.paste(pim.resize((pw, ph)), (0, label_h))
        d = ImageDraw.Draw(tile)
        if img is None:
            d.text((pw // 2 - 30, label_h + ph // 2), "sin imagen",
                   fill=(120, 130, 145), font=f_volc)

        # Volcanes (triangulos cyan + label) — los MISMOS que las vistas RGB.
        if show_volcanoes and img is not None:
            for v in CATALOG:
                if (v.zone != "test"
                        and b["lat_min"] <= v.lat <= b["lat_max"]
                        and b["lon_min"] <= v.lon <= b["lon_max"]):
                    vx, vy = _xy(v.lat, v.lon)
                    d.polygon([(vx, vy - 6), (vx + 5, vy + 4), (vx - 5, vy + 4)],
                              fill=(0, 255, 255), outline=(255, 255, 255))
                    d.text((vx + 6, vy - 6), v.name,
                           fill=(255, 255, 255), font=f_volc)
        # Hot spots (diamantes rojos)
        if hs:
            for h in hs:
                hx, hy = _xy(h.lat, h.lon)
                d.polygon([(hx, hy - 6), (hx + 6, hy), (hx, hy + 6),
                           (hx - 6, hy)], fill=(255, 51, 0),
                          outline=(255, 255, 255))
        # Header de zona
        d.rectangle([0, 0, pw, label_h], fill=(15, 20, 28))
        zc = ZONE_COLORS[zk]
        rgb_c = tuple(int(zc[i:i + 2], 16) for i in (1, 3, 5))
        d.text((6, 7), ZONE_LABELS[zk], fill=rgb_c, font=f_zone)
        tiles.append(tile)

    total_w = sum(t.width for t in tiles) + gap * (len(tiles) - 1)
    out = Image.new("RGB", (total_w, ph + label_h), (10, 14, 20))
    x = 0
    for t in tiles:
        out.paste(t, (x, 0))
        x += t.width + gap
    buf = io.BytesIO()
    out.save(buf, format="PNG")
    return buf.getvalue()


def _render_4_zonas_image_tv(product: str, show_volcanoes: bool,
                             show_hotspots: bool) -> None:
    """Muestra el grid TV de 4 zonas LEYENDO el PNG ya producido en background.

    NUNCA computa en el foreground (eso bloqueaba el fragment ~54s con cache
    frio). Si el productor aun no dejo el PNG (primeros ~60s tras un restart),
    muestra un placeholder y la rotacion sigue. Ver prewarm_tv_caches.
    """
    png = _TV_PRODUCED.get(f"rgb:{product}")
    if png:
        _emit_tv_png(png)
    else:
        _tv_placeholder(f"Preparando {PRODUCT_OPTIONS.get(product, product)} "
                        f"— las 4 zonas se cargan en segundo plano…")


def _render_4_zonas_inner(product: str, show_volcanoes: bool, show_hotspots: bool,
                           layout: str, height: int, minimal: bool = False,
                           stable_keys: bool = False,
                           uniform_size: bool = False):
    """Logica compartida entre _grid_4_zonas y _rotating_grid_4_zonas.

    minimal=True: oculta banner status arriba (modo TV puro).
    stable_keys=True: da un `key` fijo por zona a cada st.plotly_chart -> sin
        parpadeo (update in-place).
    uniform_size=True: usa bounds de aspect UNIFORME (todas las zonas del
        mismo tamano visual) + columnas iguales. Para el Modo Sala TV. (jun 2026)
    """
    zbounds = _uniform_aspect_bounds() if uniform_size else None
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
    # ThreadPoolExecutor con 4 workers -> todas en paralelo, el tiempo total
    # ~= zona mas lenta. fetch_frame_robust es thread-safe.
    from concurrent.futures import ThreadPoolExecutor
    all_zones = [z for row in rows_zones for z in row]

    ts_key = tuple(timestamps)  # hashable para la cache

    def _fetch_one(zone_key: str):
        # Frame CACHEADO (ya reproyectado) -> 2a+ aparición instantánea.
        img_z, used_ts_z, used_zoom_z = _zone_frame_cached(
            product, ts_key, zone_key, bool(zbounds))
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
        # uniform_size: columnas IGUALES (los bounds ya son de aspect uniforme,
        # asi las 4 imagenes salen del mismo tamano). Si no, proporcionales al
        # aspect para que llenen mejor.
        if uniform_size:
            cols = st.columns(len(row_zones))
        else:
            cols = st.columns([
                (VOLCANIC_ZONES[z]["lon_max"] - VOLCANIC_ZONES[z]["lon_min"])
                * max(0.1, float(np.cos(np.radians(
                    (VOLCANIC_ZONES[z]["lat_min"]
                     + VOLCANIC_ZONES[z]["lat_max"]) / 2))))
                / (VOLCANIC_ZONES[z]["lat_max"] - VOLCANIC_ZONES[z]["lat_min"])
                for z in row_zones])
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
                              time_label=time_label,
                              bounds_override=zbounds[zone_key] if zbounds else None),
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
