"""Modo Guardia VOLCAN: zoom a un volcan, sus 4 productos a la vez.

FILOSOFIA: igual que Modo Guardia (Chile) — solo imagen, sin metricas
automaticas. Aca el zoom es del volcan (~30 km radio) y mostramos los 4
productos de imagen A LA VEZ, en el orden en que se lee una emergencia
(pedido de operaciones, ago-2026: no se puede ir producto por producto):

  1. GeoColor — visible/IR: hay columna?
  2. Ash RGB (EUMETSAT receta) — es ceniza?
  3. SO2 (JMA receta) — es gas fresco?
  4. VOLCAT (SSEC/CIMSS) — que altura tiene la pluma?

`volcan_grid` es la FUENTE UNICA de esta vista: la comparten el sub-tab
Volcan del Modo Guardia y el slot `tv=volcan` del Modo Sala (que pide los 3
de RAMMB en una fila, con su propio orden y su propia leyenda).

Hot spots NOAA FDCF dentro del bbox se overlayean solo sobre el Ash RGB.

Overlays opt-in (toggles en barra superior):
- Viento GFS direccional (300/500/850 hPa) sobre el crater
- Anillos de distancia 5/10/25/50 km

Captura PNG del momento actual: boton de descarga construye una imagen
compuesta con los 3 productos RAMMB + header de timestamp/coords/viento
(VOLCAT queda fuera: su PNG se baja aparte, con su barra de color).

Cada panel tiene su propio poll (RAMMB 60 s, VOLCAT 120 s). Sin %, sin alertas.
"""

import io
import logging
from datetime import datetime, timezone

import numpy as np
import plotly.graph_objects as go
import streamlit as st

try:
    # WIND_LEVELS_VIZ: CANONICO en map_helpers, compartido con la leyenda
    # compacta (con una copia por vista, la leyenda podria mentir).
    from dashboard.exports import download_buttons
    from dashboard.map_helpers import WIND_LEVELS_VIZ
    from dashboard.style import volcano_marker
    from dashboard.utils import fmt_chile, parse_rammb_ts
    from src.fetch.goes_fdcf import HotSpot, fetch_latest_hotspots
    from src.fetch.rammb_slider import (
        fetch_frame_for_bounds, fetch_frame_robust,
        get_latest_timestamps, ZOOM_VOLCAN, ZOOM_ZONE,
    )
    from src.fetch.wind_data import fetch_wind_point
    from src.volcanos import PRIORITY_VOLCANOES, get_volcano
except Exception:
    # Streamlit Cloud hot-reload race condition: retry import dentro de funciones.
    # Si esto se ejecuta, hay un bug — log y reraise para que Streamlit muestre el error.
    import logging as _logging
    _logging.exception("Cross-package import fallo top-level — gotcha Streamlit Cloud")
    raise

logger = logging.getLogger(__name__)

DEFAULT_VOLCANO = "Villarrica"
RADIUS_DEG = 0.35  # ~38 km — un volcan + sus alrededores

# Hi-res L1b para el panel GeoColor: usamos el cache 0.5 km/px SOLO cuando el
# render es visible diurno (de noche el modo color cae a IR pseudo 2 km, peor
# que el GeoColor nocturno de RAMMB con luces de ciudad). Y solo si está fresco.
HIRES_MAX_AGE_MIN = 90

# ── Grilla 2x2 de la vista de volcan ─────────────────────────────────
#
# Los 4 productos de IMAGEN que tenemos, juntos en pantalla. En una emergencia
# el operador no puede ir tab por tab: la secuencia de lectura es GeoColor
# (hay columna?) -> Ash RGB (es ceniza?) -> SO2 (es gas fresco?) -> VOLCAT
# (que altura?), y por eso ese es el orden de la grilla.
#
# La CADENCIA de cada panel vive en RAMMB_REFRESH_S / VOLCAT_REFRESH_S, no en
# este dict: el decorador @st.fragment necesita el numero en un nombre legible
# en su propia linea, no agarrado por indice de una lista de abajo. Un campo
# `refresh_s` aca sería decorativo — el poll de verdad lo gobierna el
# decorador — asi que no lo declaramos, para no dar a entender que cambiarlo
# cambia algo.
#
# `kind` decide el renderer: "rammb" pasa por fetch_volcan_product (que ya trae
# el switch hi-res de GeoColor); "volcat" reusa el panel del Modo Sala.
RAMMB_REFRESH_S = 60
VOLCAT_REFRESH_S = 120

GRID_PANELS = [
    {"id": "geocolor",     "label": "GeoColor",
     "recipe": "Visible mejorado (CIRA) · hi-res 0.5 km de dia",
     "kind": "rammb"},
    {"id": "eumetsat_ash", "label": "Ash RGB",
     "recipe": "EUMETSAT B15-B14 / B14-B11 / B13",
     "kind": "rammb"},
    {"id": "jma_so2",      "label": "SO2 RGB",
     "recipe": "JMA B07-B09 / B09-B11",
     "kind": "rammb"},
    {"id": "volcat",       "label": "VOLCAT · altura de pluma",
     "recipe": "SSEC/CIMSS (Pavolonis 2013) · solo dibuja si detecta ceniza",
     "kind": "volcat"},
]

# El MODO SALA (slot `tv=volcan`) se queda con los 3 de RAMMB en UNA fila.
#
# OJO con el ORDEN: es distinto al de GRID_PANELS a proposito. La grilla 2x2
# ordena por secuencia de lectura de emergencia (GeoColor primero: hay columna?).
# La sala de turno conserva su orden historico —Ash RGB primero— porque su
# leyenda de 3 columnas se arma en modo_guardia.py y la gente de turno ya tiene
# esa pared interiorizada. Cambiarselo sin que nadie lo pida rotularia
# "Ash RGB" sobre el panel GeoColor.
#
# Esta lista es tambien la que compone el PNG del rotador TV
# (`zonas_fullscreen._volcan_zoom_png`), que antes iteraba una segunda lista
# `PRODUCTS` con los mismos campos. Eran dos fuentes de verdad de lo que se
# rotula encima de un mapa de ceniza, y los textos YA habian divergido.
#
# Son los MISMOS objetos que GRID_PANELS (no copias): si cambia una receta,
# cambia en los dos lados a la vez.
_PANEL_POR_ID = {p["id"]: p for p in GRID_PANELS}
GRID_PANELS_TV = [_PANEL_POR_ID[pid]
                  for pid in ("eumetsat_ash", "geocolor", "jma_so2")]

# Alto por panel. En modo normal (2x2) el panel va bajo para que entren las
# dos filas sin scroll en un portatil.
#
# OJO: en fullscreen estos numeros son solo el alto INICIAL de la figura
# Plotly. El alto que se ve lo manda el CSS de `_inject_fullscreen_css`
# (`calc(100vh …)`), porque un alto fijo en px no puede "ocupar la ventana":
# el servidor no sabe cuanto mide la pantalla del operador.
PANEL_HEIGHT_NORMAL = 380
PANEL_HEIGHT_FULLSCREEN = 460
# Una sola fila (los 4 productos en fullscreen, o los 3 del slot `tv=volcan`)
# no reparte la ventana con nadie: conserva el alto historico que tenia el
# default de `_render_product`. Pasarle el de 2 filas le sacaba 39% del alto
# a la pared que se proyecta 24/7 en la sala de turno.
PANEL_HEIGHT_TV_ROW = 620

# Cromo (px) que NO es imagen cuando la grilla va en fullscreen, medido en el
# DOM a 1920x1080 (ago-2026). Son dos situaciones distintas:
#   - PAGINA (Vista Operacional, sub-tab del Modo Guardia): arriba del primer
#     panel van el boton Salir, el badge de latencia, la barra de auto-refresh,
#     los toggles, la barra de tabs, la toolbar del volcan y la cabecera. El
#     primer plot arranca en y=505..549 segun el alto de cada leyenda.
#   - SALA (`tv=volcan`): no hay nada de eso, el primer plot arranca en y=165.
#     Con el cromo de pagina la pared perderia ~350 px de imagen por nada.
# Y por cada fila se suman la leyenda compacta, la linea de receta y el gap.
# Son una ESTIMACION. Si sobra o falta, el panel queda un poco mas alto o mas
# bajo, nunca una fila bajo el fold: `min-height` frena la division.
GRID_CHROME_PAGE_PX = 470
GRID_CHROME_TV_PX = 100
GRID_CHROME_ROW_PX = 105
# De esos 105, la leyenda compacta se lleva 64 (medido en el DOM a 1920x1080).
# El slot de sala la apaga (`show_legend=False`, pone la suya como overlay
# arriba del grid), y si el reparto no se entera sigue reservando esos 64 px.
#
# OJO con lo que esto gana y lo que NO: a 3 columnas la IMAGEN no crece, porque
# el que manda es el ancho (medido: Lascar 540x588 px, Hudson —el mas austral,
# donde el scaleratio 1/cos(lat) mas estira— 412x592, los dos muy por debajo
# del alto disponible). Lo que se corrige es el encuadre: sin esto el grid
# queda empujado contra el borde de arriba y la pared proyectada termina con
# una franja muerta de ~100 px abajo, en vez de la escena centrada.
GRID_CHROME_LEGEND_PX = 64


def _row_chrome_px(con_leyenda: bool) -> int:
    """Cromo vertical por fila de la grilla, en px."""
    return GRID_CHROME_ROW_PX - (0 if con_leyenda else GRID_CHROME_LEGEND_PX)

# Anillos de distancia (km)
RING_RADII_KM = [5, 10, 25, 50]


# ── Cache helpers ────────────────────────────────────────────────────

@st.cache_data(ttl=30, show_spinner=False)
def _recent_timestamps(product: str, n: int = 3) -> list[str]:
    """Ultimos N timestamps para fallback si el mas reciente no tiene tile."""
    return get_latest_timestamps(product, n=n)


@st.cache_data(ttl=7200, show_spinner=False)
def _frame(product: str, ts: str, lat_min: float, lat_max: float,
           lon_min: float, lon_max: float) -> np.ndarray | None:
    bounds = {"lat_min": lat_min, "lat_max": lat_max,
              "lon_min": lon_min, "lon_max": lon_max}
    try:
        return fetch_frame_for_bounds(product, ts, bounds, zoom=ZOOM_VOLCAN)
    except Exception as e:
        logger.warning("frame %s %s fallo: %s", product, ts, e)
        return None


def _frame_with_fallback(product: str, timestamps: list[str],
                          lat_min: float, lat_max: float,
                          lon_min: float, lon_max: float
                          ) -> tuple[np.ndarray | None, str | None, int]:
    """Fallback de ts + fallback de zoom (zoom=4 -> zoom=3).

    RAMMB intermitentemente no sirve eumetsat_ash / jma_so2 en zoom=4.
    Esta funcion delega en fetch_frame_robust que cubre los 2 fallbacks.
    Devuelve (img, ts_usado, zoom_usado). zoom=0 si todo fallo.
    """
    bounds = {"lat_min": lat_min, "lat_max": lat_max,
              "lon_min": lon_min, "lon_max": lon_max}
    return fetch_frame_robust(
        product, timestamps, bounds,
        zoom_preferred=ZOOM_VOLCAN, zoom_fallback=ZOOM_ZONE,
    )


@st.cache_data(ttl=300, show_spinner=False)
def _hotspots_volcan(lat_min: float, lat_max: float,
                     lon_min: float, lon_max: float
                     ) -> tuple[list[HotSpot], datetime | None]:
    bounds = {"lat_min": lat_min, "lat_max": lat_max,
              "lon_min": lon_min, "lon_max": lon_max}
    try:
        hs, dt = fetch_latest_hotspots(bounds=bounds, hours_back=1)
        from dashboard.map_helpers import filter_hotspots_near_volcanoes
        return filter_hotspots_near_volcanoes(hs), dt
    except Exception as e:
        logger.warning("hotspots fallo: %s", e)
        return [], None


@st.cache_data(ttl=3600, show_spinner=False)
def _wind_at_volcano(lat: float, lon: float) -> dict[str, dict]:
    """Viento en los 3 niveles para una coord. Cache 1h (GFS publica c/6h)."""
    out = {}
    for level_id, _label, _color in WIND_LEVELS_VIZ:
        w = fetch_wind_point(lat, lon, level=level_id)
        if w is not None:
            out[level_id] = w
    return out


# ── Helpers geometricos ──────────────────────────────────────────────

def _circle_points(lat0: float, lon0: float, radius_km: float,
                   n: int = 64) -> tuple[list[float], list[float]]:
    """Devuelve (lats, lons) de un circulo geodesico aproximado."""
    theta = np.linspace(0, 2 * np.pi, n)
    dlat = (radius_km / 111.0) * np.cos(theta)
    dlon = (radius_km / (111.0 * float(np.cos(np.radians(lat0))))) * np.sin(theta)
    lats = (lat0 + dlat).tolist()
    lons = (lon0 + dlon).tolist()
    return lats, lons


def _wind_arrow_endpoints(lat0: float, lon0: float, u_kmh: float, v_kmh: float,
                          arrow_len_deg: float = 0.18
                          ) -> tuple[list[float], list[float]]:
    """Punto inicial y final de la flecha en (lat,lon).

    La longitud visual es proporcional a la velocidad: ~arrow_len_deg para
    50 km/h. La direccion sigue la convencion meteorologica (u positivo =
    hacia el Este, v positivo = hacia el Norte).
    """
    speed = float(np.hypot(u_kmh, v_kmh))
    if speed < 1e-3:
        return [lon0, lon0], [lat0, lat0]
    # Normalizar direccion
    ux = u_kmh / speed
    vy = v_kmh / speed
    # Escalar longitud por velocidad (saturada en 100 km/h)
    scale = arrow_len_deg * min(speed / 50.0, 2.0)
    lon_end = lon0 + ux * scale / float(np.cos(np.radians(lat0)))
    lat_end = lat0 + vy * scale
    return [lon0, lon_end], [lat0, lat_end]


# ── Hi-res GeoColor (switch día/noche, mejor vista cuando aplica) ─────

def _crop_centered(arr: np.ndarray, frac: float) -> np.ndarray:
    """Recorta el centro de una imagen a una fracción lineal (0<frac<=1).

    El cache hi-res cubre radio 0.5°; esta vista zooma a 0.35°. Como ambos
    están centrados en el volcán y usan el mismo factor cos(lat) en lon, el
    recorte central por frac=0.35/0.5 alinea exacto con los bounds de la vista
    → drop-in del frame RAMMB, sin tocar la geometría del render ni la captura.
    """
    frac = max(0.05, min(1.0, frac))
    h, w = arr.shape[:2]
    rh, rw = int(round(h * frac)), int(round(w * frac))
    r0, c0 = (h - rh) // 2, (w - rw) // 2
    return arr[r0:r0 + rh, c0:c0 + rw]


def _hires_age_min(info: dict, now: datetime) -> int | None:
    """Edad en minutos del scan hi-res respecto a `now` (None si no parsea)."""
    iso = (info or {}).get("scan_dt_iso")
    if not iso:
        return None
    try:
        dt = datetime.fromisoformat(iso)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return int((now - dt).total_seconds() / 60)
    except Exception:
        return None


# ── Conversion array a data URL ──────────────────────────────────────

def _array_to_data_url(arr):
    # Lazy import (gotcha Streamlit Cloud — ver CLAUDE.md).
    from dashboard.map_helpers import array_to_data_url
    return array_to_data_url(arr)


def _zoom_res_label(zoom: int) -> str:
    """Resolucion aproximada (km/px) por nivel de zoom RAMMB.

    Sirve para que TODOS los productos muestren su resolucion (no solo cuando
    hubo fallback). ~ es nominal en ecuador; en Chile austral es algo peor por
    la geometria GOES. ZOOM_VOLCAN=4 ~1.7, ZOOM_ZONE=3 ~3.4, ZOOM_CHILE=2 ~5.1.
    """
    return {ZOOM_VOLCAN: "~1.7 km/px", ZOOM_ZONE: "~3.4 km/px",
            2: "~5.1 km/px"}.get(zoom, "")


def fetch_volcan_product(prod_id: str, volcano_name: str,
                         lat: float, lon: float, bounds: dict,
                         now: datetime) -> tuple[np.ndarray | None, str]:
    """Imagen + etiqueta de un producto centrado en el volcán.

    Encapsula el SWITCH de "mejor vista posible" para reusar desde la página
    completa Y desde la rotación del Modo Sala TV:
    - GeoColor: hi-res L1b visible (≈0.5 km/px true color pan-sharpened)
      cuando hay render diurno fresco; si no, RAMMB GeoColor (mejor de noche).
    - Ash / SO2: siempre RAMMB (son IR 2 km, no hay ganancia de resolución).

    Devuelve (img, ts_label). img=None si no hay nada disponible.
    """
    # 1) GeoColor → intentar hi-res primero (solo visible diurno y fresco)
    if prod_id == "geocolor":
        try:
            from src.fetch.hires_cache import fetch_hires_for_volcano
            h_arr, h_info = fetch_hires_for_volcano(volcano_name, mode="color")
        except Exception:
            h_arr, h_info = None, None
        age = _hires_age_min(h_info, now) if h_info else None
        # El radio EFECTIVO sale de los bounds, no de la constante: con radio
        # ajustable los dos pueden diferir, y recortar por la constante dejaria
        # el panel GeoColor mas cerrado que los otros tres.
        r_view = (bounds["lat_max"] - bounds["lat_min"]) / 2.0
        r = float((h_info or {}).get("radius_deg") or 0.5)
        # El cache hi-res cubre un radio fijo (~0.5°). Si la vista pide MAS que
        # eso no hay que estirarlo: la imagen se pintaria sobre un bbox que no
        # cubre y mentiria la georreferencia. En ese caso cae a RAMMB, que baja
        # los tiles que hagan falta.
        if (h_arr is not None and h_info
                and h_info.get("render") == "visible_color"
                and age is not None and age <= HIRES_MAX_AGE_MIN
                and r > 0 and r_view <= r):
            img = _crop_centered(h_arr, r_view / r)
            hhmm = h_info.get("scan_ts", "")[8:12]
            t_utc = f"{hhmm[:2]}:{hhmm[2:]}" if len(hhmm) == 4 else "?"
            try:
                _sdt = datetime.fromisoformat(h_info.get("scan_dt_iso", ""))
                t_str = f"{t_utc} UTC · {fmt_chile(_sdt)}"
            except Exception:
                t_str = f"{t_utc} UTC"
            return img, (f"{t_str} (hace {age} min) · hi-res L1b ~0.5 km/px "
                         f"(visible, pan-sharp)")

    # 2) RAMMB (Ash, SO2, y GeoColor nocturno / sin hi-res)
    img = None
    ts_label = "—"
    timestamps = _recent_timestamps(prod_id, n=3)
    if timestamps:
        img, used_ts, used_zoom = _frame_with_fallback(
            prod_id, timestamps,
            bounds["lat_min"], bounds["lat_max"],
            bounds["lon_min"], bounds["lon_max"],
        )
        if used_ts:
            try:
                ts_dt = parse_rammb_ts(used_ts)
                age = int((now - ts_dt).total_seconds() / 60)
                ts_label = (f"{ts_dt.strftime('%H:%M')} UTC · "
                            f"{fmt_chile(ts_dt)} (hace {age} min)")
                # Mostrar SIEMPRE la resolucion del zoom usado (antes solo
                # aparecia en fallback -> GeoColor, que suele usar el zoom
                # preferido, no la mostraba; Ash/SO2 si). (jun 2026)
                res = _zoom_res_label(used_zoom)
                if res:
                    ts_label += f" · {res}"
                flags = []
                if used_ts != timestamps[0]:
                    flags.append("scan previo")
                if used_zoom < ZOOM_VOLCAN:
                    flags.append("zoom reducido")
                if flags:
                    ts_label += " ⚠ " + ", ".join(flags)
            except Exception:
                ts_label = used_ts
    return img, ts_label



# ── Render por producto ──────────────────────────────────────────────

def _render_product(img: np.ndarray | None, bounds: dict, product_label: str,
                    volcan_lat: float, volcan_lon: float, volcan_name: str,
                    hotspots: list[HotSpot] | None = None,
                    show_wind: bool = False, wind_data: dict | None = None,
                    show_rings: bool = False,
                    height: int = 620):
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

    # Anillos de distancia (debajo de marcadores y vientos)
    if show_rings:
        for r_km in RING_RADII_KM:
            lats, lons = _circle_points(volcan_lat, volcan_lon, r_km)
            fig.add_trace(go.Scatter(
                x=lons, y=lats, mode="lines",
                line=dict(color="rgba(255,255,255,0.4)", width=1, dash="dot"),
                hoverinfo="skip", showlegend=False,
            ))
            # Etiqueta del radio en el lado este
            fig.add_annotation(
                x=lons[16], y=lats[16],   # ~ 90 grados (este)
                text=f"{r_km} km", showarrow=False,
                font=dict(color="rgba(255,255,255,0.7)", size=9),
                bgcolor="rgba(10,14,20,0.6)", borderpad=2,
            )

    # Triangulo crater
    fig.add_trace(go.Scatter(
        x=[volcan_lon], y=[volcan_lat], mode="markers",
        marker=volcano_marker("focus"),
        hovertemplate=f"<b>{volcan_name}</b><br>%{{x:.3f}}, %{{y:.3f}}<extra></extra>",
        showlegend=False,
    ))

    # Hotspots (solo si vinieron — en general solo sobre Ash)
    if hotspots:
        lats = [h.lat for h in hotspots]
        lons = [h.lon for h in hotspots]
        labels = [f"{h.temp_k:.0f}K · FRP {h.frp_mw:.1f}MW" for h in hotspots]
        fig.add_trace(go.Scatter(
            x=lons, y=lats, mode="markers",
            marker=dict(symbol="diamond", size=10, color="#ff3300",
                        line=dict(color="white", width=1)),
            text=labels, hoverinfo="text", showlegend=False,
        ))

    # Vectores de viento (solo en la primera columna por defecto)
    if show_wind and wind_data:
        for level_id, level_label, color in WIND_LEVELS_VIZ:
            w = wind_data.get(level_id)
            if w is None:
                continue
            xs, ys = _wind_arrow_endpoints(volcan_lat, volcan_lon, w["u"], w["v"])
            fig.add_trace(go.Scatter(
                x=xs, y=ys, mode="lines",
                line=dict(color=color, width=3),
                hovertemplate=(
                    f"<b>{level_label}</b><br>"
                    f"{w['speed']:.0f} km/h desde {w['direction']:.0f}°<extra></extra>"
                ),
                showlegend=False,
            ))
            # Punta de flecha
            fig.add_trace(go.Scatter(
                x=[xs[1]], y=[ys[1]], mode="markers",
                marker=dict(symbol="arrow", size=14, color=color,
                            angle=float(np.degrees(np.arctan2(w["u"], w["v"]))),
                            line=dict(color="white", width=1)),
                hoverinfo="skip", showlegend=False,
            ))

    # scaleratio = 1/cos(lat) hace que 1 km en x = 1 km en y en pixeles,
    # por lo que un circulo geometrico (en km) se ve como circulo visual.
    # Sin esto los anillos aparecen aplastados como ovalos.
    cos_lat = max(0.1, float(np.cos(np.radians(volcan_lat))))
    fig.update_xaxes(range=[bounds["lon_min"], bounds["lon_max"]],
                     showgrid=False, visible=False)
    fig.update_yaxes(range=[bounds["lat_min"], bounds["lat_max"]],
                     showgrid=False, visible=False,
                     scaleanchor="x", scaleratio=1.0 / cos_lat)
    fig.update_layout(
        title=dict(text=product_label, font=dict(size=13, color="#e0e0e0"), x=0.02),
        height=height, margin=dict(l=0, r=0, t=28, b=0),
        paper_bgcolor="#0a0e14", plot_bgcolor="#0a0e14",
    )
    if img is None:
        fig.add_annotation(
            text="Sin imagen disponible",
            xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False,
            font=dict(color="#7a8a9a", size=14),
        )
    return fig


# ── Captura PNG ──────────────────────────────────────────────────────

def _load_font(size: int):
    """Carga una fuente con cobertura Unicode (acentos, ñ).

    Prueba varios paths comunes en Linux (Streamlit Cloud) y Windows.
    DejaVuSans tiene cobertura Unicode amplia y viene en casi cualquier
    sistema; arial.ttf solo en Windows. Fallback a default si todo falla.
    """
    from PIL import ImageFont
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",   # Streamlit Cloud
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "DejaVuSans.ttf",
        "C:/Windows/Fonts/arial.ttf",
        "arial.ttf",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            continue
    return ImageFont.load_default()


def _build_capture_png(volcan_name: str, volcan_lat: float, volcan_lon: float,
                       elevation: int, region: str,
                       product_imgs: list[tuple[str, np.ndarray | None, str]],
                       wind_data: dict, hotspots_count: int,
                       generated_utc: datetime,
                       radius_deg: float = RADIUS_DEG) -> bytes:
    """Compone una imagen A4-landscape con los 3 productos + header.

    No usa kaleido (evitamos dep ~80MB). Hace composite directo con PIL.
    Las imagenes de cada producto llenan el panel (no thumbnail tiny).
    """
    from PIL import Image, ImageDraw

    # Lienzo: 1800x1200 px (~A4 landscape 150 DPI)
    W, H = 1800, 1200
    canvas = Image.new("RGB", (W, H), color=(10, 14, 20))
    draw = ImageDraw.Draw(canvas)

    f_title = _load_font(38)
    f_sub = _load_font(22)
    f_small = _load_font(18)
    f_label = _load_font(24)

    # Header
    draw.text((40, 30), volcan_name, fill=(255, 102, 68), font=f_title)
    draw.text((40, 80),
              f"{region} · {volcan_lat:.3f}°, {volcan_lon:.3f}° · "
              f"elev {elevation} m",
              fill=(180, 180, 200), font=f_sub)
    # El ENCUADRE va impreso: el radio es ajustable, y sin el nadie puede decir
    # despues a que escena corresponde este PNG cuando aparece en un informe.
    draw.text((40, 115),
              f"Captura UTC: {generated_utc.strftime('%Y-%m-%d %H:%M:%S')} · "
              f"Encuadre {etiqueta_encuadre(radius_deg)} · "
              f"Hot spots NOAA en bbox: {hotspots_count}",
              fill=(150, 160, 180), font=f_small)

    # Viento (esquina derecha)
    wind_x = W - 520
    draw.text((wind_x, 30), "Viento GFS sobre el cráter",
              fill=(220, 220, 220), font=f_sub)
    y = 65
    if wind_data:
        for level_id, label, color_hex in WIND_LEVELS_VIZ:
            w = wind_data.get(level_id)
            color = tuple(int(color_hex[i:i+2], 16) for i in (1, 3, 5))
            if w:
                txt = f"{label}: {w['speed']:.0f} km/h desde {w['direction']:.0f}°"
            else:
                txt = f"{label}: sin dato"
            draw.text((wind_x, y), txt, fill=color, font=f_small)
            y += 28
    else:
        draw.text((wind_x, y), "(viento no solicitado — activá toggle 💨)",
                  fill=(120, 120, 140), font=f_small)

    # 3 productos — calcular anchos para que llenen 95% del lienzo
    margin_x = 40
    gap = 25
    panel_w = (W - 2 * margin_x - 2 * gap) // 3   # ~573 px
    panel_h = 880
    x0 = margin_x
    y0 = 200

    # Area util para la imagen dentro del panel (despues del header del panel)
    inner_pad = 10
    label_h = 70  # header del panel (label + ts_label)
    img_box_w = panel_w - 2 * inner_pad
    img_box_h = panel_h - label_h - inner_pad

    for i, (label, img_arr, ts_label) in enumerate(product_imgs):
        x = x0 + i * (panel_w + gap)
        # Fondo del panel
        draw.rectangle([x, y0, x + panel_w, y0 + panel_h],
                       fill=(15, 20, 28), outline=(50, 60, 80), width=2)
        # Header del panel
        draw.text((x + inner_pad, y0 + 8), label,
                  fill=(255, 102, 68), font=f_label)
        draw.text((x + inner_pad, y0 + 42), ts_label,
                  fill=(140, 150, 170), font=f_small)
        # Imagen llenando area util preservando aspect ratio
        if img_arr is not None:
            img = Image.fromarray(img_arr.astype(np.uint8))
            iw, ih = img.size
            scale = min(img_box_w / iw, img_box_h / ih)
            new_w = max(1, int(iw * scale))
            new_h = max(1, int(ih * scale))
            img = img.resize((new_w, new_h), Image.LANCZOS)
            ix = x + inner_pad + (img_box_w - new_w) // 2
            iy = y0 + label_h + (img_box_h - new_h) // 2
            canvas.paste(img, (ix, iy))
        else:
            txt = "sin imagen disponible"
            tw = draw.textlength(txt, font=f_label)
            draw.text((x + (panel_w - tw) // 2, y0 + panel_h // 2),
                      txt, fill=(120, 120, 140), font=f_label)

    # Footer
    draw.text((40, H - 50),
              "GOES-19 · RAMMB/CIRA · NOAA FDCF · Open-Meteo GFS · "
              "SERNAGEOMIN · goesvolcanic.streamlit.app",
              fill=(100, 110, 130), font=f_small)
    draw.text((40, H - 25),
              "Imagen sin métricas automáticas. La interpretación queda al experto.",
              fill=(100, 110, 130), font=f_small)

    out = io.BytesIO()
    canvas.save(out, format="PNG", optimize=True)
    return out.getvalue()


# ── Render principal ─────────────────────────────────────────────────

@st.fragment(run_every=f"{RAMMB_REFRESH_S}s")
def _panel_rammb(prod_id: str, label: str, recipe: str, volcan_name: str,
                 show_wind: bool, show_rings: bool, height: int,
                 radius_deg: float = RADIUS_DEG, show_legend: bool = True):
    """Un panel RAMMB con su propio poll.

    NO recibe timestamp ni imagen por argumento: los args de un fragment con
    `run_every` quedan congelados en el ultimo full-rerun (ver
    live_viewer.py:564-575), asi que un `ts` pasado desde afuera nunca
    detectaria un scan nuevo. `fetch_volcan_product` consulta adentro, y su
    cache (TTL 7200 s por ts) evita la re-descarga.

    `show_legend=False` es para el slot `tv=volcan` del Modo Sala, que ya
    dibuja SU fila de 3 leyendas (una por columna, overlay `tv=True`) antes de
    llamar a la grilla. Prendida en los dos lados, la pared proyectada gastaba
    dos tiras identicas —~60 px de alto— en decir lo mismo, y ahi cada pixel
    es imagen de satelite que el operador no ve. Por defecto va PRENDIDA: los
    otros dos llamadores (Vista Operacional y sub-tab de Modo Guardia) no
    ponen ninguna leyenda propia.
    """
    v = get_volcano(volcan_name)
    if v is None:
        st.error(f"Volcan {volcan_name} no esta en el catalogo.")
        return

    bounds = {
        "lat_min": v.lat - radius_deg, "lat_max": v.lat + radius_deg,
        "lon_min": v.lon - radius_deg, "lon_max": v.lon + radius_deg,
    }
    now = datetime.now(timezone.utc)

    # Hot spots SOLO sobre Ash RGB: son el dato termico, y ponerlos en los tres
    # paneles triplica el ruido sin agregar informacion.
    hs = None
    if prod_id == "eumetsat_ash":
        hs, _ = _hotspots_volcan(bounds["lat_min"], bounds["lat_max"],
                                 bounds["lon_min"], bounds["lon_max"])
    wind = _wind_at_volcano(v.lat, v.lon) if show_wind else {}

    if show_legend:
        from dashboard.map_helpers import render_compact_legend
        render_compact_legend(
            prod_id, height_px=30,
            symbols=(("volcano",)
                     + (("hotspot",) if prod_id == "eumetsat_ash" else ())
                     + (("rings",) if show_rings else ())
                     + (("wind",) if (show_wind and wind) else ())),
        )

    img, ts_label = fetch_volcan_product(
        prod_id, v.name, v.lat, v.lon, bounds, now)
    st.plotly_chart(
        _render_product(img, bounds, f"{label} · {ts_label}",
                        v.lat, v.lon, v.name,
                        hotspots=hs, show_wind=show_wind, wind_data=wind,
                        show_rings=show_rings, height=height),
        width='stretch',
        config={"displayModeBar": False, "responsive": True},
        # El radio va en la key: dos renders del mismo volcan a radios
        # distintos son figuras distintas, y con la key compartida Plotly
        # reusaria el estado (zoom/pan) de la anterior.
        key=f"vgrid_{prod_id}_{volcan_name}_{radius_deg:.2f}",
    )
    st.markdown(
        f"<div style='font-size:0.7rem; color:#556; margin-top:-0.5rem;'>"
        f"{recipe}</div>",
        unsafe_allow_html=True,
    )


def etiqueta_sector_volcat(sector: str) -> str:
    """Rotulo del sector VOLCAT: cual es y con que resolucion de grilla.

    El operador tiene que saber si esta mirando un sector DEDICADO (250-500 m,
    solo Copahue, Calbuco y Planchon-Peteroa) o el REGIONAL que le toca por
    latitud, donde la pluma se ve mucho mas gruesa y la altura es mas incierta.
    Sin ese rotulo, una altura de sector regional se lee con la confianza de
    una de sector dedicado.

    La resolucion sale del nombre del sector, no de un literal: asi un sector
    nuevo (o el de 5 km de Argentina) no queda rotulado con un numero que no
    le corresponde.
    """
    from src.fetch.volcat_api import _REGIONAL_SECTORS

    nombre = sector.replace("_", " ")
    if sector not in _REGIONAL_SECTORS:
        return f"{nombre} (dedicado)"
    res = sector.rsplit("_", 2)[-2:]          # ("2", "km") / ("5", "km")
    return f"{nombre} (regional {' '.join(res)})"


@st.fragment(run_every=f"{VOLCAT_REFRESH_S}s")
def _panel_volcat(volcan_name: str, height: int,
                  radius_deg: float = RADIUS_DEG):
    """Panel VOLCAT: altura de pluma cuantitativa de SSEC/CIMSS.

    Reusa `zonas_fullscreen._render_volcat_zoom_tv` (import perezoso entre
    vistas, mismo patron que modo_guardia._mosaico_subtab): ese helper ya
    resuelve el sector, baja el frame y arma el plotly con las dos barras de
    color. Duplicarlo aca seria una tercera copia de la misma logica.

    Dos honestidades que el panel TIENE que mostrar:
    - Que sector esta usando (via `etiqueta_sector_volcat`). Solo Copahue,
      Calbuco y Planchon-Peteroa tienen sector dedicado; los otros 40 caen en
      un regional, donde la pluma se ve mucho mas gruesa y la altura es mas
      incierta.
    - Que el panel vacio es lo NORMAL: VOLCAT solo dibuja cuando detecta
      ceniza.
    """
    from dashboard.map_helpers import render_compact_legend
    from src.fetch.volcat_api import resolve_volcat_sector

    v = get_volcano(volcan_name)
    if v is None:
        st.error(f"Volcan {volcan_name} no esta en el catalogo.")
        return

    sector, _instr = resolve_volcat_sector(v)
    render_compact_legend("volcat", height_px=30, symbols=("volcano",))
    st.markdown(
        f"<div style='font-size:0.7rem; color:#7a8a9a; margin-bottom:0.2rem;'>"
        f"Sector <b>{etiqueta_sector_volcat(sector)}</b>"
        f" · sin dibujo = VOLCAT no detecta ceniza, no es una falla</div>",
        unsafe_allow_html=True,
    )

    from dashboard.views.zonas_fullscreen import _render_volcat_zoom_tv
    _render_volcat_zoom_tv(volcan_name, height=height, pad=radius_deg)


@st.fragment(run_every=f"{RAMMB_REFRESH_S}s")
def _grid_header(volcan_name: str, show_wind: bool,
                 radius_deg: float = RADIUS_DEG):
    """Cabecera: nombre, coords, viento, conteo de hot spots, hora de render.

    Fragment aparte y liviano: se refresca al ritmo de RAMMB sin arrastrar el
    redibujo de los cuatro mapas.
    """
    v = get_volcano(volcan_name)
    if v is None:
        return
    bounds = {
        "lat_min": v.lat - radius_deg, "lat_max": v.lat + radius_deg,
        "lon_min": v.lon - radius_deg, "lon_max": v.lon + radius_deg,
    }
    now = datetime.now(timezone.utc)
    hotspots, _ = _hotspots_volcan(bounds["lat_min"], bounds["lat_max"],
                                   bounds["lon_min"], bounds["lon_max"])
    wind = _wind_at_volcano(v.lat, v.lon) if show_wind else {}
    wind_summary = ""
    if wind:
        bits = []
        for level_id, _label, _c in WIND_LEVELS_VIZ:
            w = wind.get(level_id)
            if w:
                bits.append(
                    f"{level_id} {w['speed']:.0f} km/h@{w['direction']:.0f}°")
        if bits:
            wind_summary = " · " + " · ".join(bits)
    st.markdown(
        f"<div style='background:#0f1418; border-left:4px solid #ff6644; "
        f"padding:0.7rem 1rem; border-radius:4px; margin-bottom:0.8rem;'>"
        f"<div style='display:flex; justify-content:space-between; "
        f"align-items:center;'>"
        f"<div><span style='font-size:1.4rem; font-weight:800; color:#ff6644;'>"
        f"{v.name}</span> &nbsp;"
        f"<span style='color:#7a8a9a; font-size:0.85rem;'>"
        f"{v.region} · elev {v.elevation} m · {v.lat}°, {v.lon}°{wind_summary}"
        f"</span></div>"
        f"<div style='font-size:0.85rem; color:#9aaabb;'>"
        f"Hot spots {len(hotspots)} · Render {now.strftime('%H:%M:%S')} UTC / "
        f"{fmt_chile(now)}</div></div></div>",
        unsafe_allow_html=True,
    )


# ── Trazabilidad del encuadre ────────────────────────────────────────
#
# Con el radio ajustable (0.35-3 grados) dos capturas del MISMO minuto a radios
# distintos son indistinguibles por nombre y por contenido. Estas imagenes
# terminan en informes de un SDA: quien las mire despues tiene que poder decir
# a que encuadre corresponden sin volver al dashboard. Por eso el radio va en
# el nombre del archivo Y sobre-impreso en la imagen.
#
# Todo en ASCII a proposito: el label se dibuja con PIL sobre el PNG y tambien
# viaja como tag del GeoTIFF, y ahi los grados / mas-menos tipograficos
# dependen de que fuente encontro el sistema.

def etiqueta_encuadre(radius_deg: float) -> str:
    """Encuadre legible: medio-lado en grados y su equivalente en km.

    Los km importan mas que los grados para leer una pluma: 1 grado de latitud
    son ~111 km, y esa es la escala mental del turno.
    """
    return f"+/-{radius_deg:.2f} deg (~{radius_deg * 111:.0f} km)"


def sufijo_encuadre(radius_deg: float) -> str:
    """Fragmento del encuadre apto para nombre de archivo (r0p35)."""
    return "r" + f"{radius_deg:.2f}".replace(".", "p")


def _slug(texto: str) -> str:
    """Nombre de volcan -> token de archivo sin acentos ni espacios."""
    acentos = str.maketrans("áéíóúñÁÉÍÓÚÑ", "aeiounAEIOUN")
    limpio = texto.translate(acentos).lower().replace(" ", "-")
    return "".join(c for c in limpio if c.isalnum() or c in "-_")


def _download_expander(v, radius_deg: float = RADIUS_DEG):
    """PNG + GeoTIFF por producto, en un expander CERRADO.

    Por que existe: antes de migrar a la grilla, el tab Volcan ofrecia este par
    de botones por producto, y es la unica via para llevar el encuadre de un
    volcan a QGIS. Al migrar se perdio.

    Por que cerrado: la grilla se mira en una emergencia. Seis botones sueltos
    abajo le comen alto a los mapas, que es lo que importa. Quien necesita el
    archivo lo abre.

    Por que solo los 3 de RAMMB: VOLCAT NO va. Su panel es un PNG que compone
    SSEC/CIMSS, no tenemos el array georreferenciado detras, y fabricarle un
    GeoTIFF seria inventar una georreferencia que no controlamos — un archivo
    que abre en QGIS y ubica la pluma donde nosotros supusimos, no donde SSEC
    la puso. Su PNG se baja de su propio panel, con su barra de color.

    Las imagenes salen de `fetch_volcan_product`, que las sirve de su cache
    (igual que `_capture_button`): abrir el expander no dispara descargas.
    """
    now = datetime.now(timezone.utc)
    bounds = {
        "lat_min": v.lat - radius_deg, "lat_max": v.lat + radius_deg,
        "lon_min": v.lon - radius_deg, "lon_max": v.lon + radius_deg,
    }
    encuadre = etiqueta_encuadre(radius_deg)
    with st.expander("⬇ Descargar por producto (PNG / GeoTIFF para QGIS)",
                     expanded=False):
        st.caption(
            f"Encuadre {encuadre} centrado en {v.name}. El PNG lleva el "
            "timestamp y el encuadre impresos; el GeoTIFF va limpio, "
            "georreferenciado en EPSG:4326."
        )
        for panel in GRID_PANELS_TV:
            img, ts_label = fetch_volcan_product(
                panel["id"], v.name, v.lat, v.lon, bounds, now)
            if img is None:
                st.caption(f"{panel['label']}: sin imagen disponible")
                continue
            download_buttons(
                img,
                bounds=bounds,
                base_filename=(
                    f"goes19_{panel['id']}_{_slug(v.name)}_"
                    f"{now.strftime('%Y%m%d_%H%M')}Z_"
                    f"{sufijo_encuadre(radius_deg)}"
                ),
                label_overlay=(f"GOES-19 {panel['label']} - {v.name} "
                               f"({encuadre}) - {ts_label}"),
                prod_label=panel["label"],
                # El radio entra en la key: dos radios son dos widgets. Si no,
                # Streamlit reusa el primero y el boton baja el encuadre viejo.
                key_prefix=(f"dlvg_{panel['id']}_{_slug(v.name)}_"
                            f"{sufijo_encuadre(radius_deg)}"),
            )


def _capture_button(v, show_wind: bool, radius_deg: float = RADIUS_DEG):
    """Boton de captura PNG con los 3 productos RAMMB + header.

    Re-pide las imagenes a `fetch_volcan_product`, que las sirve de su cache
    (TTL 7200 s por ts) — no hace falta compartir estado entre los fragments.
    VOLCAT queda fuera de la captura: su PNG se descarga aparte desde su propio
    panel, con su barra de color.
    """
    now = datetime.now(timezone.utc)
    bounds = {
        "lat_min": v.lat - radius_deg, "lat_max": v.lat + radius_deg,
        "lon_min": v.lon - radius_deg, "lon_max": v.lon + radius_deg,
    }
    hotspots, _ = _hotspots_volcan(bounds["lat_min"], bounds["lat_max"],
                                   bounds["lon_min"], bounds["lon_max"])
    wind = _wind_at_volcano(v.lat, v.lon) if show_wind else {}
    captured = []
    for panel in GRID_PANELS_TV:
        img, ts_label = fetch_volcan_product(
            panel["id"], v.name, v.lat, v.lon, bounds, now)
        captured.append((panel["label"], img, ts_label))
    try:
        png_bytes = _build_capture_png(
            v.name, v.lat, v.lon, v.elevation, v.region,
            captured, wind, len(hotspots), now, radius_deg,
        )
        st.download_button(
            label="📸 Descargar captura PNG (este momento)",
            data=png_bytes,
            # El encuadre va en el nombre: dos capturas del mismo minuto a
            # radios distintos no pueden pisarse en la carpeta de descargas.
            file_name=(f"{_slug(v.name)}_{now.strftime('%Y%m%d_%H%M')}_UTC_"
                       f"{sufijo_encuadre(radius_deg)}.png"),
            mime="image/png",
            width='stretch',
        )
    except Exception as e:
        st.warning(f"No se pudo construir captura: {e}")


def _resolve_per_row(per_row: int | None, fullscreen: bool) -> int:
    """Cuantas columnas usa la grilla cuando el llamador no lo dice.

    EL LAYOUT DEPENDE DEL ENCUADRE DISPONIBLE, NO DEL GUSTO. La escena es
    CUADRADA (±radio en lat y lon), asi que en una pantalla 16:9 la dimension
    que escasea es el ALTO. Dos filas lo parten en dos: medido a 1920x1080, la
    imagen quedaba en ~245 px de lado con ~700 px de ancho VACIO al costado de
    cada panel. Cuatro columnas gastan el ancho, que es lo que sobra, y la
    imagen sube a ~462 px de lado — 2.1x mas grande, que es justo el objetivo
    (ver mejor la anomalia).

    En modo normal hay sidebar y el ancho baja a ~1400 px: ahi las cuatro
    columnas quedan mas chicas que el 2x2 (~350 contra 380 px de lado) y el
    2x2 vuelve a ganar.

    Un `per_row` explicito se respeta tal cual: el slot de sala pide 3 porque
    su leyenda de 3 columnas la arma el llamador.
    """
    if per_row is not None:
        return per_row
    return 4 if fullscreen else 2


def _panel_height(fullscreen: bool, filas: int) -> int:
    """Alto inicial en px de cada figura Plotly de la grilla.

    En fullscreen el alto final lo pone el CSS, pero Plotly necesita arrancar
    con uno: si arranca muy bajo, el primer paint se ve achatado hasta que
    `responsive` lo refita.

    UNA fila es el slot de sala: no reparte la ventana con nadie y conserva el
    alto historico. DOS o mas filas se reparten el alto, asi que cada panel
    arranca mas bajo.
    """
    if not fullscreen:
        return PANEL_HEIGHT_NORMAL
    return PANEL_HEIGHT_TV_ROW if filas <= 1 else PANEL_HEIGHT_FULLSCREEN


def _inject_fullscreen_css(filas: int, con_cabecera: bool = True,
                           con_leyenda: bool = True) -> None:
    """CSS que hace que la grilla ocupe la ventana del operador.

    POR QUE: el pedido de operaciones fue "que ocupen todo el espacio que
    puedan". Un alto fijo en px no puede cumplirlo — el servidor no sabe si
    enfrente hay un portatil o la pared de la sala. Medido a 1920x1080, la
    segunda fila arrancaba en y=1258: el operador veia 2 de 4 productos sin
    scrollear. Mismo patron que el grid de 4 zonas del Modo Sala.

    Dos cosas separadas:
    1. El alto por panel = (ventana - cromo) / filas. Va acotado a los
       contenedores CON KEY de la grilla (`st-key-vgrid_*`,
       `st-key-tvvolcatzoom_*`) y NO a todo `stPlotlyChart`: en Vista
       Operacional los tabs Nacional y Zona estan en el DOM aunque esten
       ocultos, y un selector global les cambiaria el alto de sus mapas.
    2. Achicar el cromo, que era la mayor parte del problema (~697 px antes
       de la primera imagen). Se esconde SOLO lo que no se lee proyectado —
       la guia de interpretacion y el titulo decorativo — y se comprimen los
       gaps de 16 px entre bloques. Nada de esto saca funcionalidad: fuera de
       fullscreen la vista queda igual.
    """
    base = GRID_CHROME_PAGE_PX if con_cabecera else GRID_CHROME_TV_PX
    alto = (f"calc((100vh - {base + _row_chrome_px(con_leyenda) * filas}px)"
            f" / {filas})")
    st.markdown(
        f"""
        <style>
          /* 1) cromo que no se lee en una pared proyectada */
          [data-testid="stExpander"], .main-header {{ display: none !important; }}
          /* los gaps de Streamlit suman >100 px antes del primer panel */
          [data-testid="stVerticalBlock"] {{ gap: 0.4rem !important; }}
          /* 2) la ventana repartida entre las filas que haya */
          /* La cadena ENTERA: el contenedor con key, el frame de pantalla
             completa y el chart. Streamlit le clava al contenedor el alto que
             pidio la figura, asi que achicar solo el chart deja un hueco del
             alto viejo y la segunda fila igual arranca bajo el fold. */
          [class*="st-key-vgrid_"],
          [class*="st-key-vgrid_"] [data-testid="stFullScreenFrame"],
          [class*="st-key-vgrid_"] [data-testid="stPlotlyChart"],
          [class*="st-key-vgrid_"] [data-testid="stPlotlyChart"] > div,
          [class*="st-key-tvvolcatzoom_"],
          [class*="st-key-tvvolcatzoom_"] [data-testid="stFullScreenFrame"],
          [class*="st-key-tvvolcatzoom_"] [data-testid="stPlotlyChart"],
          [class*="st-key-tvvolcatzoom_"] [data-testid="stPlotlyChart"] > div {{
            height: {alto} !important;
            min-height: 180px !important;
          }}
          /* Streamlit le pone `flex: 0 0 460px` al contenedor con key, y en
             una columna flex el flex-basis GANA sobre height: sin esto el
             hueco del alto viejo queda igual y la 2a fila sigue bajo el
             fold, aunque el chart de adentro ya mida bien. */
          [class*="st-key-vgrid_"],
          [class*="st-key-tvvolcatzoom_"] {{
            flex: 0 0 {alto} !important;
          }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def volcan_grid(volcan_name: str, show_wind: bool = False,
                show_rings: bool = False, enable_capture: bool = False,
                fullscreen: bool = False, panels: list | None = None,
                per_row: int | None = None, show_header: bool = True,
                radius_deg: float = RADIUS_DEG, show_legend: bool = True):
    """Grilla de productos del volcan, todos a la vez.

    FUENTE UNICA de esta vista — la usan el sub-tab Volcan del Modo Guardia,
    el tab Volcan de Vista Operacional y el slot `tv=volcan` del Modo Sala.
    No duplicarla.

    NO lleva @st.fragment: Streamlit no permite fragments anidados y los
    paneles de adentro ya son fragments, cada uno con su cadencia. Este nivel
    solo compone, y se re-ejecuta en el full-rerun (cambio de volcan o toggle).

    El layout sale de `_resolve_per_row`: 4 en una fila en fullscreen, 2x2 en
    modo normal. Depende del encuadre disponible, no del gusto — la escena es
    cuadrada, asi que en 16:9 lo que escasea es el alto y apilar filas parte
    justo la dimension que falta.

    `panels` y `per_row` existen para el MODO SALA, que se proyecta en la sala
    de turno con su propia leyenda de 3 columnas armada por el llamador. Ese
    slot sigue con los 3 RAMMB en una fila y en SU orden (Ash primero):
    cambiarle el layout por debajo le desalinearia la leyenda.
    `show_header=False` ahi mismo, porque el rotador TV ya pone su cabecera, y
    `show_legend=False` por lo mismo: la sala arma su fila de 3 leyendas antes
    de llamar aca, y prendidas en los dos lados la pared gastaba dos tiras
    identicas en decir lo mismo. Solo llega a `_panel_rammb`: `_panel_volcat`
    no lo recibe porque el unico llamador que apaga leyendas es el slot de
    sala, y ese usa `GRID_PANELS_TV`, que NO incluye VOLCAT — darle el flag
    seria un parametro que nadie puede poner en False.

    `radius_deg` lo ajusta la Vista Operacional: una pluma de ceniza en
    emergencia viaja cientos de km y a RADIUS_DEG (~38 km) se sale del cuadro
    a los pocos minutos. Va a los CUATRO paneles y a la cabecera desde aca —
    si un solo lugar se quedara con la constante, ese panel encuadraria
    distinto y la grilla dejaria de leerse como una sola escena.
    """
    v = get_volcano(volcan_name)
    if v is None:
        st.error(f"Volcan {volcan_name} no esta en el catalogo.")
        return

    panels = GRID_PANELS if panels is None else panels
    per_row = _resolve_per_row(per_row, fullscreen)
    filas = [panels[i:i + per_row] for i in range(0, len(panels), per_row)]
    height = _panel_height(fullscreen, len(filas))
    # En fullscreen el alto lo reparte el CSS entre las filas que haya: es la
    # unica forma de "ocupar la ventana" sin saber cuanto mide (mismo patron
    # que el grid de 4 zonas del Modo Sala, modo_guardia.py). `show_header`
    # distingue la pagina (que arrastra tabs y toolbars) de la sala (que no
    # tiene nada arriba).
    if fullscreen:
        _inject_fullscreen_css(len(filas), con_cabecera=show_header,
                               con_leyenda=show_legend)
    if show_header:
        _grid_header(volcan_name, show_wind, radius_deg=radius_deg)

    for fila in filas:
        cols = st.columns(per_row)
        for col, panel in zip(cols, fila):
            with col:
                if panel["kind"] == "volcat":
                    _panel_volcat(volcan_name, height=height,
                                  radius_deg=radius_deg)
                else:
                    _panel_rammb(panel["id"], panel["label"], panel["recipe"],
                                 volcan_name, show_wind, show_rings, height,
                                 radius_deg=radius_deg,
                                 show_legend=show_legend)

    if enable_capture:
        _capture_button(v, show_wind, radius_deg=radius_deg)
        # Debajo de la captura compuesta: el archivo por producto, incluido el
        # GeoTIFF que se usa para analizar el evento en QGIS.
        _download_expander(v, radius_deg=radius_deg)

    st.markdown(
        "<div style='text-align:center; color:#445566; font-size:0.75rem; "
        "margin-top:1rem; padding-top:0.5rem; border-top:1px solid #223;'>"
        "<i>Sin metricas automaticas — el dashboard muestra el dato. "
        "La interpretacion queda al experto.</i></div>",
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
        "padding-bottom:0.6rem; border-bottom:2px solid #223; margin-bottom:0.8rem;'>"
        "<div style='font-size:1.5rem; font-weight:800; color:#ff6644;'>"
        "🛡 MODO GUARDIA — VOLCAN</div>"
        "<div style='font-size:0.85rem; color:#7a8a9a;'>"
        "Zoom volcan · 4 productos a la vez · GOES-19</div></div>",
        unsafe_allow_html=True,
    )

    # Toolbar: selector + 3 toggles + boton de captura
    cols = st.columns([2, 1, 1, 1, 1])
    with cols[0]:
        volcan = st.selectbox(
            "Volcan",
            options=PRIORITY_VOLCANOES,
            index=PRIORITY_VOLCANOES.index(DEFAULT_VOLCANO)
            if DEFAULT_VOLCANO in PRIORITY_VOLCANOES else 0,
            label_visibility="collapsed",
            key="modoguardiavolcan_selector",
        )
    with cols[1]:
        show_wind = st.toggle(
            "💨 Viento",
            value=False,
            help="Vectores GFS en 300/500/850 hPa sobre el crater. "
                 "Cache 1h.",
            key="mgv_wind",
        )
    with cols[2]:
        show_rings = st.toggle(
            "⊙ Anillos",
            value=False,
            help="Anillos de distancia 5/10/25/50 km desde el crater. "
                 "Calibra el ojo para estimar tamaños.",
            key="mgv_rings",
        )
    with cols[3]:
        enable_capture = st.toggle(
            "📸 Captura",
            value=False,
            help="Mostrar boton de descarga PNG con header de timestamp + "
                 "coords + viento. Util para mandar a colega o adjuntar a informe.",
            key="mgv_capture",
        )
    with cols[4]:
        st.markdown(
            "<div style='font-size:0.7rem; color:#556; padding-top:0.5rem;'>"
            f"RAMMB {RAMMB_REFRESH_S}s · VOLCAT {VOLCAT_REFRESH_S}s</div>",
            unsafe_allow_html=True,
        )

    volcan_grid(volcan, show_wind, show_rings, enable_capture,
                fullscreen=st.query_params.get("fullscreen") == "1")
