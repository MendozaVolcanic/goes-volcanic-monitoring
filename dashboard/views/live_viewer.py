"""Pagina En Vivo: imagen GOES-19 mas reciente con auto-refresh.

Muestra el ultimo scan disponible de RAMMB/CIRA en 3 productos simultaneos:
GeoColor (visual), Ash RGB y SO2. Se actualiza automaticamente cada 10 minutos.

El objetivo es que siempre muestre lo mas reciente posible — equivalente
a tener el slider.cira.colostate.edu abierto en un tab.
"""

import logging
from datetime import datetime, timezone

import numpy as np
import plotly.graph_objects as go
import streamlit as st

try:
    # Botones PNG / GeoTIFF: viven en dashboard/exports.py porque los
    # comparte la grilla de volcan (modo_guardia_volcan). Una vista no
    # importa de otra vista solo para bajar un archivo.
    from dashboard.exports import download_buttons
    from dashboard.map_helpers import add_chile_border, render_compact_legend
    from dashboard.style import (C_ACCENT, header, info_panel, kpi_card,
                                 refresh_info_badge, volcano_marker)
    from dashboard.utils import (
        fmt_both_long, fmt_chile, now_utc, parse_rammb_ts, utc_to_chile,
    )
    from src.config import VOLCANIC_ZONES
    from src.fetch.rammb_slider import (
        CHILE_REPROJECTED_BOUNDS, CHILE_TILE_BOUNDS, CHILE_TILES_Z2, PRODUCTS,
        fetch_stitched_frame, fetch_frame_for_bounds,
        get_latest_timestamps, reproject_to_latlon,
        ZOOM_ZONE,
    )
    from src.fetch.wind_data import WIND_LEVELS, fetch_wind_grid, fetch_wind_diagnostic
    from src.fetch.goes_fdcf import fetch_latest_hotspots, HotSpot
    from src.volcanos import CATALOG, get_priority, PRIORITY_VOLCANOES
except Exception:
    # Streamlit Cloud hot-reload race condition: retry import dentro de funciones.
    # Si esto se ejecuta, hay un bug — log y reraise para que Streamlit muestre el error.
    import logging as _logging
    _logging.exception("Cross-package import fallo top-level — gotcha Streamlit Cloud")
    raise

logger = logging.getLogger(__name__)

# Productos a mostrar en la vista en vivo
LIVE_PRODUCTS = [
    ("geocolor",      "GeoColor",   "#4a9eff"),
    ("eumetsat_ash",  "Ash RGB",    "#ff6644"),
    ("jma_so2",       "SO2",        "#44dd88"),
]

# Construir PRODUCT_LABELS desde PRODUCTS (ya importado arriba)
PRODUCT_LABELS = {k: v.split("(")[0].strip() for k, v in PRODUCTS.items()}


# Versión de reproyección — cambiar si se modifica cfac/bounds para invalidar caché
_REPROJECT_VERSION = "v2"


@st.cache_data(ttl=15, show_spinner=False)
def _get_latest_ts(product: str) -> str | None:
    """Consultar el timestamp del scan mas reciente (cache 15s — liviano).

    TTL corto para detectar el nuevo scan rapido. RAMMB publica 3-5 min
    despues del fin del scan de GOES-19. Con fragment cada 60s y cache 15s,
    la latencia de deteccion tras publicacion es ≤ 60s en el peor caso.

    El JSON de latest_times.json (~1 KB) trae cache-buster en la URL asi
    que cada miss va directo al origen — evita que un CDN/proxy intermedio
    nos sirva una version stale.
    """
    times = get_latest_timestamps(product, n=1)
    return times[0] if times else None


@st.cache_data(ttl=7200, show_spinner=False)
def _fetch_frame_for_ts(product: str, ts: str, _v: str = _REPROJECT_VERSION) -> dict | None:
    """Descargar y reprojectar un scan especifico (cache 2h por timestamp).

    La clave incluye el timestamp → cada nuevo scan tiene su propia entrada.
    Un scan ya procesado nunca se re-descarga aunque el usuario refresque.
    """
    img = fetch_stitched_frame(
        product, ts,
        zoom=2,
        tile_rows=CHILE_TILES_Z2["rows"],
        tile_cols=CHILE_TILES_Z2["cols"],
    )
    if img is None:
        return None
    img = reproject_to_latlon(img, col_start=678, row_start=1356)
    dt = parse_rammb_ts(ts)
    return {
        "ts": ts,
        "dt": dt,
        "image": img,
        "bounds": CHILE_REPROJECTED_BOUNDS,
        "label_utc": dt.strftime("%Y-%m-%d %H:%M UTC"),
        "label_local": fmt_chile(dt),
    }


def _fetch_latest_frame(product: str) -> dict | None:
    """Obtener el frame mas reciente: primero el ts (cache 90s), luego la imagen (cache 2h)."""
    ts = _get_latest_ts(product)
    if not ts:
        return None
    return _fetch_frame_for_ts(product, ts)


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


@st.cache_data(ttl=7200, show_spinner=False)
def _fetch_zone_frame(
    product: str, ts: str, zone_key: str,
    _v: str = _REPROJECT_VERSION,
) -> np.ndarray | None:
    """Descargar frame para una zona volcánica a zoom=3 (cache 2h por ts+zona)."""
    bounds = VOLCANIC_ZONES[zone_key]
    return fetch_frame_for_bounds(product, ts, bounds, zoom=ZOOM_ZONE)


@st.cache_data(ttl=15, show_spinner=False)
def _fetch_latest_ts_all() -> dict:
    """Obtener timestamps mas recientes de todos los productos (cache 15s).

    Llama get_latest_timestamps directamente (NO via _get_latest_ts) para
    evitar llamadas anidadas entre funciones @st.cache_data, que Streamlit
    no soporta y causa 'Error running app' en Streamlit Cloud.

    Retorna tambien "polled_at" — el epoch UTC en el que esta consulta
    efectivamente llego a RAMMB. Esto permite distinguir "no hay scan nuevo
    porque RAMMB no publico" vs "no hay scan nuevo porque estamos sirviendo
    cache viejo". El campo queda dentro del dict cacheado, asi que refleja
    la ultima consulta REAL al origen (no el tiempo de ejecucion actual).
    """
    import time as _t
    result = {"_polled_at": _t.time()}
    for prod, _, _ in LIVE_PRODUCTS:
        times = get_latest_timestamps(prod, n=1)
        if times:
            dt = parse_rammb_ts(times[0])
            result[prod] = {
                "ts": times[0],
                "utc": dt.strftime("%H:%M UTC"),
                "local": fmt_chile(dt),
            }
        else:
            result[prod] = None
    return result


def _make_fig(img: np.ndarray, bounds: dict, title: str,
              highlight_volcano=None, volc_layer: str = "Prioritarios (8)") -> go.Figure:
    """Crear figura Plotly con imagen georeferenciada y volcanes.

    volc_layer: "Prioritarios (8)" | "Todos (43+)" | "Ninguno".
    """
    import base64, io
    from PIL import Image as PILImage

    lat_min = bounds["lat_min"]
    lat_max = bounds["lat_max"]
    lon_min = bounds["lon_min"]
    lon_max = bounds["lon_max"]

    buf = io.BytesIO()
    PILImage.fromarray(img).save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode()

    # Volcanes visibles en el area segun el layer elegido
    if volc_layer == "Ninguno":
        vis = []
    elif volc_layer == "Todos (43+)":
        vis = [v for v in CATALOG
               if lat_min <= v.lat <= lat_max and lon_min <= v.lon <= lon_max]
    else:  # Prioritarios (8)
        vis = [v for v in get_priority()
               if lat_min <= v.lat <= lat_max and lon_min <= v.lon <= lon_max]
        if not vis:
            vis = [v for v in CATALOG
                   if lat_min <= v.lat <= lat_max and lon_min <= v.lon <= lon_max][:15]

    # Si hay un volcan resaltado (vista zoom), excluirlo de la lista general
    # para evitar marcador + etiqueta duplicados.
    if highlight_volcano is not None:
        vis = [v for v in vis if v.name != highlight_volcano.name]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=[lon_min, lon_max], y=[lat_min, lat_max],
        mode="markers", marker=dict(opacity=0),
        showlegend=False, hoverinfo="skip",
    ))
    fig.add_layout_image(
        source=f"data:image/png;base64,{b64}",
        xref="x", yref="y",
        x=lon_min, y=lat_max,
        xanchor="left", yanchor="top",
        sizex=lon_max - lon_min,
        sizey=lat_max - lat_min,
        sizing="stretch", layer="below",
    )
    if vis:
        fig.add_trace(go.Scatter(
            x=[v.lon for v in vis], y=[v.lat for v in vis],
            mode="markers+text",
            marker=volcano_marker("wide", color=C_ACCENT),
            text=[v.name for v in vis],
            textposition="top center",
            textfont=dict(size=7, color="rgba(255,255,255,0.75)"),
            name="Volcanes",
            hovertext=[
                f"<b>{v.name}</b><br>{v.elevation:,} m<br>"
                f"<span style='color:#aaa; font-size:10px;'>"
                f"Triangulo = coord. real (WGS84). El pico puede verse "
                f"desplazado ~1-3 km en la imagen por paralaje GOES-19 "
                f"(mayor para volcanes altos).</span>"
                for v in vis
            ],
            hoverinfo="text", showlegend=False,
        ))

    # Marcador resaltado para volcán seleccionado (vista zoom)
    if highlight_volcano is not None:
        fig.add_trace(go.Scatter(
            x=[highlight_volcano.lon], y=[highlight_volcano.lat],
            mode="markers+text",
            marker=volcano_marker("focus", color="#ff4444"),
            text=[highlight_volcano.name],
            textposition="top center",
            textfont=dict(size=10, color="white", family="Arial Black"),
            name=highlight_volcano.name,
            hovertext=f"<b>{highlight_volcano.name}</b><br>{highlight_volcano.elevation:,} m",
            hoverinfo="text", showlegend=False,
        ))

    # Frontera de Chile — overlay en todos los mapas para referencia
    # geografica clara (linea blanca semi-transparente).
    add_chile_border(fig)

    # Mapas grandes — el contenido es el mapa, no metadata. Margenes
    # chicos para aprovechar pantalla. Altura default 760 (era 640).
    fig.update_layout(
        title=dict(text=title, font=dict(size=12, color="#99aabb")),
        xaxis_title="Longitud", yaxis_title="Latitud",
        height=760, template="plotly_dark",
        yaxis=dict(scaleanchor="x", scaleratio=1,
                   range=[lat_min - 0.5, lat_max + 0.5]),
        xaxis=dict(range=[lon_min - 0.5, lon_max + 0.5]),
        margin=dict(t=30, b=30, l=40, r=15),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    return fig


@st.cache_data(ttl=3600, show_spinner=False)
def _fetch_wind_cached(level: str) -> list:
    """Obtener grilla de viento GFS (cache 1 hora)."""
    return fetch_wind_grid(level=level)


@st.cache_data(ttl=300, show_spinner=False)
def _fetch_hotspots_cached(
    lat_min: float, lat_max: float, lon_min: float, lon_max: float,
) -> tuple[list[dict], str | None]:
    """Hot spots FDCF NOAA en bbox (cache 5 min — el scan tambien dura 10).

    Retorna lista de dicts (no HotSpot dataclass) para que sean cacheables
    por Streamlit. Tambien el timestamp del scan como string ISO.
    """
    bounds = {"lat_min": lat_min, "lat_max": lat_max,
              "lon_min": lon_min, "lon_max": lon_max}
    hotspots, scan_dt = fetch_latest_hotspots(bounds=bounds, hours_back=2)
    ts_str = scan_dt.isoformat() if scan_dt else None
    return [h.to_dict() for h in hotspots], ts_str


def _add_hotspots(fig, hotspots: list[dict], scan_label: str | None = None) -> None:
    """Agregar hot spots NOAA FDCF como scatter sobre el plot.

    Color por confianza:
      high  → rojo intenso (#ff2244)
      saturated → naranja (#ff8800) — pixel saturado, FRP probable underestimado
      low   → amarillo claro (#ffcc44)

    Tamaño ∝ log(FRP) — los focos mas intensos se ven mas grandes.
    """
    if not hotspots:
        return

    color_map = {
        "high": "#ff2244",
        "saturated": "#ff8800",
        "low": "#ffcc44",
        "unknown": "#aa6688",
    }

    import math
    sizes = [
        max(8, min(28, 8 + 4 * math.log10(max(h.get("frp_mw", 1.0), 1.0))))
        for h in hotspots
    ]
    colors = [color_map.get(h.get("confidence", "unknown"), "#aa6688")
              for h in hotspots]

    label_suffix = f" · scan {scan_label}" if scan_label else ""
    hover = [
        f"<b>Hot spot NOAA FDCF</b>{label_suffix}<br>"
        f"FRP: <b>{h.get('frp_mw', 0):.1f} MW</b><br>"
        f"T: {h.get('temp_k', 0):.1f} K<br>"
        f"Area sub-pixel: {h.get('area_km2', 0):.2f} km²<br>"
        f"Coord: {h.get('lat', 0):.3f}°, {h.get('lon', 0):.3f}°<br>"
        f"<i>Confianza: {h.get('confidence', '?')}</i>"
        for h in hotspots
    ]

    fig.add_trace(go.Scatter(
        x=[h["lon"] for h in hotspots],
        y=[h["lat"] for h in hotspots],
        mode="markers",
        marker=dict(
            size=sizes,
            color=colors,
            symbol="circle",
            line=dict(width=1.2, color="white"),
            opacity=0.9,
        ),
        name="Hot spots NOAA FDCF",
        hovertext=hover, hoverinfo="text",
        showlegend=True,
    ))


def _add_wind_arrows(
    fig,
    wind_data: list,
    scale: float = 0.03,
    color: str = "rgba(255,230,80,0.95)",
    level_label: str = "500 hPa",
) -> None:
    """Agregar vectores de viento como flechas de anotacion Plotly.

    scale: grados de desplazamiento por km/h de viento.
           0.03 → viento de 50 km/h = flecha de 1.5 grados.
    color: amarillo brillante para contraste sobre Ash RGB / GeoColor.
    """
    if not wind_data:
        return

    import plotly.graph_objects as go
    # Marcador de inicio de cada vector (punto amarillo pequeno)
    fig.add_trace(go.Scatter(
        x=[w["lon"] for w in wind_data],
        y=[w["lat"] for w in wind_data],
        mode="markers",
        marker=dict(size=3, color=color,
                    line=dict(width=0.6, color="rgba(0,0,0,0.6)")),
        name=f"Viento {level_label} (GFS)",
        hovertext=[f"<b>{w['speed']:.0f} km/h</b> @ {w['direction']:.0f}°"
                   for w in wind_data],
        hoverinfo="text",
        showlegend=True,
    ))

    for w in wind_data:
        lon0 = w["lon"]
        lat0 = w["lat"]
        lon_tip = lon0 + w["u"] * scale
        lat_tip = lat0 + w["v"] * scale
        fig.add_annotation(
            x=lon_tip, y=lat_tip,
            ax=lon0,   ay=lat0,
            xref="x", yref="y",
            axref="x", ayref="y",
            arrowhead=3,
            arrowsize=1.0,
            arrowwidth=1.6,
            arrowcolor=color,
            text="",
            showarrow=True,
            standoff=0,
            startstandoff=0,
            hovertext=f"<b>{w['speed']:.0f} km/h</b> @ {w['direction']:.0f}°",
        )


def _reloj_chile():
    """Mostrar reloj UTC + hora Chile en tiempo real."""
    now = now_utc()
    utc_str = now.strftime("%H:%M:%S UTC")
    ch_str = fmt_chile(now)
    date_str = now.strftime("%d %b %Y")
    st.markdown(
        f'<div style="text-align:center; padding:0.35rem 0.5rem; '
        f'background:rgba(17,24,34,0.6); border-radius:6px; '
        f'border:1px solid rgba(100,120,140,0.2); line-height:1.2;">'
        f'<div style="font-size:0.62rem; color:#556677; text-transform:uppercase; '
        f'letter-spacing:0.1em;">{date_str}</div>'
        f'<div style="font-size:1.25rem; font-weight:700; color:#e8eaf0; '
        f'font-family:monospace; letter-spacing:0.04em;">{utc_str}</div>'
        f'<div style="font-size:0.82rem; color:#99aabb; font-family:monospace;">'
        f'{ch_str} <span style="color:#445566; font-size:0.7rem;">Chile</span></div>'
        f'</div>',
        unsafe_allow_html=True,
    )


@st.fragment(run_every="60s")
def _health_banner():
    """Banner ancho con codigo de color segun edad del scan mas reciente.

    Este fragment es el POLLER de 60s de la vista En Vivo. Re-consulta los
    timestamps (cacheado 15s) por su cuenta — NO recibe ts_all como argumento,
    porque los args de un run_every fragment quedan CONGELADOS en el último
    full-rerun y nunca detectarían un scan nuevo. Al final, si llegó un scan
    nuevo, dispara st.rerun(scope="app") para refrescar los mapas (que viven
    fuera del fragment, con sus selectores preservados por key). Así se restaura
    el auto-refresh que se perdió al mover el decorator desde _live_content
    (jun 2026 — bug del audit).

    ✅ verde (<15 min): sistema operativo, GOES + RAMMB OK
    ⚠ amarillo (15-30 min): latencia elevada, probablemente RAMMB lento
    ❌ rojo (>30 min): datos atrasados, RAMMB caido o hueco en publicacion

    El user veia 30+ min a veces — este banner explicita la causa
    (es RAMMB, no nosotros) sin que tenga que adivinar.
    """
    ts_all = _fetch_latest_ts_all()  # fresco cada 60s (cacheado 15s)
    # CONSOLIDADO (jun 2026): esta tira ÚNICA reemplaza al banner de estado +
    # la caja "Último scan" + el "Hora del scan" de la barra de auto-refresh.
    # Antes la hora/edad del scan aparecía en 3 bloques distintos. Ahora todo
    # vive acá: estado (color por edad) · reloj · scan por producto · edad de
    # consulta. Corre cada 60s -> se mantiene fresco.
    most_recent_dt = None
    for prod, _label, _c in LIVE_PRODUCTS:
        info = ts_all.get(prod)
        if info and info.get("ts"):
            try:
                dt = parse_rammb_ts(info["ts"])
                if most_recent_dt is None or dt > most_recent_dt:
                    most_recent_dt = dt
            except Exception:
                pass

    now = datetime.now(timezone.utc)
    if most_recent_dt is None:
        color = "#ff4444"; bg = "rgba(255,68,68,0.10)"; icon = "❌"
        msg = "Sin datos de RAMMB"; sub = "reintentando"
        tip = "RAMMB/CIRA no respondió. Reintentando en el próximo ciclo."
    else:
        age_min = int((now - most_recent_dt).total_seconds() / 60)
        if age_min < 15:
            color = "#3fb950"; bg = "rgba(63,185,80,0.08)"; icon = "✅"
            msg = "Sistema operativo"; sub = f"último scan hace {age_min} min"
            tip = "GOES-19 + RAMMB/CIRA al día."
        elif age_min < 30:
            color = "#d29922"; bg = "rgba(210,153,34,0.10)"; icon = "⚠"
            msg = "Latencia elevada"
            sub = f"último scan hace {age_min} min · RAMMB lento"
            tip = ("RAMMB/CIRA está lento. No es problema nuestro — "
                   "esperá el próximo ciclo.")
        else:
            color = "#ff4444"; bg = "rgba(255,68,68,0.10)"; icon = "❌"
            msg = "Datos atrasados"
            sub = f"último scan hace {age_min} min"
            tip = ("RAMMB/CIRA aparentemente caído o con hueco en publicación. "
                   "Cruzar con status.cira.colostate.edu o usar VOLCAT (SSEC).")

    # Reloj (UTC + Chile) — se refresca con el fragment (cada 60s).
    utc_str = now.strftime("%H:%M:%S UTC")
    ch_str = fmt_chile(now)

    # Edad del polling propio (cuando NUESTRO servidor consultó RAMMB).
    import time as _time_mod
    _polled_at = ts_all.get("_polled_at", _time_mod.time())
    _polling_age = int(_time_mod.time() - _polled_at)
    poll_extra = (f" · ⚠ sesión dormida {_polling_age}s"
                  if _polling_age > 120 else "")

    # Scan por producto, compacto (pueden diferir: ej. SO2 va un scan atrás).
    prods_html = ""
    for prod, label, pcolor in LIVE_PRODUCTS:
        info = ts_all.get(prod)
        if info:
            prods_html += (
                f"<span style='margin-right:0.7rem; white-space:nowrap;'>"
                f"<span style='color:{pcolor};'>■</span> "
                f"<b style='color:#c0ccd8;'>{label}</b> "
                f"<span style='color:#99aabb; font-family:monospace;'>"
                f"{info['utc']}</span></span>")
        else:
            prods_html += (f"<span style='margin-right:0.7rem; color:#556;'>"
                           f"{label} —</span>")

    st.markdown(
        f"<div style='border-left:4px solid {color}; background:{bg}; "
        f"padding:0.45rem 0.9rem; border-radius:6px; margin-bottom:0.5rem; "
        f"display:flex; align-items:center; gap:0.9rem; flex-wrap:wrap;'>"
        # Estado (color por edad)
        f"<span style='font-size:1.25rem;' title=\"{tip}\">{icon}</span>"
        f"<div style='min-width:120px;'>"
        f"<div style='color:{color}; font-weight:700; font-size:0.92rem; "
        f"line-height:1.15;'>{msg}</div>"
        f"<div style='color:#9aaabb; font-size:0.7rem;'>{sub}</div></div>"
        f"<span style='color:#33414f;'>│</span>"
        # Reloj
        f"<div style='line-height:1.15;'>"
        f"<div style='font-size:1.0rem; color:#e8eaf0; font-family:monospace; "
        f"font-weight:700;'>{utc_str}</div>"
        f"<div style='font-size:0.7rem; color:#99aabb; font-family:monospace;'>"
        f"{ch_str} <span style='color:#556;'>Chile</span></div></div>"
        f"<span style='color:#33414f;'>│</span>"
        # Scan por producto
        f"<div style='font-size:0.78rem; line-height:1.3;'>"
        f"<div style='font-size:0.56rem; color:#556677; text-transform:uppercase; "
        f"letter-spacing:0.06em;'>Último scan · RAMMB/CIRA</div>"
        f"<div>{prods_html}</div></div>"
        # Edad de consulta (derecha)
        f"<span style='margin-left:auto; color:#667788; font-size:0.66rem; "
        f"white-space:nowrap;' title='Hora en que tu sesión consultó RAMMB. Si "
        f"el scan es viejo pero esto es reciente, RAMMB aún no publicó el nuevo.'>"
        f"consultado hace {_polling_age}s{poll_extra}</span>"
        f"</div>",
        unsafe_allow_html=True,
    )

    # AUTO-REFRESH de los mapas: si llegó un scan NUEVO desde el ciclo anterior,
    # rerun de TODA la app -> _live_content se re-ejecuta y los mapas bajan el
    # frame nuevo (clave de cache = ts); los selectores se preservan por key.
    # Se dispara solo cuando hay scan nuevo (~cada 10 min), no cada 60s. Restaura
    # el auto-refresh prometido sin resetear toggles/tabs. (jun 2026)
    _sig = tuple((p, (ts_all.get(p) or {}).get("ts")) for p, _l, _c in LIVE_PRODUCTS)
    _prev = st.session_state.get("__live_scan_sig")
    st.session_state["__live_scan_sig"] = _sig
    if _prev is not None and _sig != _prev and any(s for _p, s in _sig):
        st.rerun(scope="app")


def _live_content():
    """Contenido principal — se refresca automaticamente cada 60s.

    Logica:
      - run_every=60s: barato (consulta ts via cache TTL=30s).
      - Si ts no cambio, el cache devuelve el frame sin re-descarga.
      - Si ts cambio (nuevo scan en RAMMB), descarga el nuevo frame.
    Latencia de deteccion del nuevo scan: <= 90s desde que aparece en RAMMB.

    Cache en dos capas:
      1. _get_latest_ts(product)     TTL=30s  → consulta liviana del timestamp
      2. _fetch_frame_for_ts(p, ts)  TTL=2h   → descarga pesada, clave = timestamp
    """

    # ── Health banner (fragment poller 60s: refresca estado + dispara rerun
    # de la app cuando hay scan nuevo -> mapas al día). ──
    _health_banner()
    ts_all = _fetch_latest_ts_all()

    # NOTA (jun 2026): el reloj, la caja "Último scan" (3 productos) y el botón
    # refresh vivían acá en 3 columnas separadas. El reloj y los tiempos de scan
    # se CONSOLIDARON en la tira única de _health_banner (arriba) para matar la
    # redundancia. El botón refresh bajó a la fila del contador de auto-refresh.

    # ── Indicador de auto-refresh con contador regresivo ──────────────────
    # Calcula el proximo scan esperado: ultimo ts + 10 min + ~4 min latencia RAMMB.
    # El JS en el browser decrementa un contador cada segundo sin re-run del server.
    from datetime import timedelta as _td
    import streamlit.components.v1 as _stc

    _ref_ts = None
    for _p in LIVE_PRODUCTS:
        _t = ts_all.get(_p[0])
        if _t:
            _ref_ts = _t["ts"]
            break

    if _ref_ts:
        _dt_last = parse_rammb_ts(_ref_ts)
        # GOES-19 Full Disk: scan cada 10 min. RAMMB publica ~4 min despues.
        _dt_next = _dt_last + _td(minutes=10) + _td(minutes=4)
        _target_iso = _dt_next.strftime("%Y-%m-%dT%H:%M:%SZ")
        _last_iso   = _dt_last.strftime("%H:%M UTC")
    else:
        _target_iso = ""
        _last_iso   = "—"

    # Epoch (ms) en que el servidor ejecuto este fragment — base para el
    # contador de "proximo chequeo" (60s despues).
    _now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)

    _countdown_html = (
        f"""
        <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                    font-size:0.8rem; color:#99aabb; padding:0.3rem 0.8rem;
                    background:rgba(17,24,34,0.5);
                    border-radius:6px; border:1px solid rgba(74,158,255,0.2);
                    display:flex; align-items:center; gap:0.9rem; flex-wrap:wrap;">
          <span>
            <span style="color:#3fb950; font-size:1rem;">●</span>
            <b style="color:#c0ccd8;">Auto-refresh</b>
          </span>
          <span style="color:#556677;">|</span>
          <span>Proximo chequeo al servidor en
            <b id="cd_poll" style="color:#3fb950; font-family:monospace;
                                    font-size:1.05rem; padding-left:0.3rem;">
              --
            </b>
          </span>
          <span style="color:#556677;">|</span>
          <span>Proximo scan estimado en
            <b id="cd_next" style="color:#4a9eff; font-family:monospace;
                                    font-size:1.05rem; padding-left:0.3rem;">
              --:--
            </b>
          </span>
        </div>
        <script>
          (function() {{
            // Contador 1: polling al servidor (60s)
            const pollStart = {_now_ms};
            const elPoll = document.getElementById("cd_poll");
            function tickPoll() {{
              if (!elPoll) return;
              const elapsed = Math.floor((Date.now() - pollStart) / 1000);
              const left = Math.max(0, 60 - elapsed);
              elPoll.textContent = left + " s";
              if (left <= 5) elPoll.style.color = "#d29922";
            }}

            // Contador 2: proximo scan de GOES-19 en RAMMB
            const target = new Date("{_target_iso}");
            const elNext = document.getElementById("cd_next");
            function tickNext() {{
              if (!elNext || isNaN(target.getTime())) return;
              let diff = Math.floor((target - new Date()) / 1000);
              if (diff <= 0) {{
                const wait = -diff;
                const m = Math.floor(wait / 60);
                const s = wait % 60;
                elNext.textContent = "esperando... (+" + m + "m " +
                                     String(s).padStart(2,"0") + "s)";
                elNext.style.color = "#d29922";
                return;
              }}
              const m = Math.floor(diff / 60);
              const s = diff % 60;
              elNext.textContent = m + "m " + String(s).padStart(2,"0") + "s";
            }}

            tickPoll(); tickNext();
            setInterval(function() {{ tickPoll(); tickNext(); }}, 1000);
          }})();
        </script>
        """
    )

    # Barra de auto-refresh (izq) + botón refresh compacto (der), en una fila.
    col_cd, col_rf = st.columns([7, 0.9])
    with col_cd:
        _stc.html(_countdown_html, height=42)
    with col_rf:
        if st.button("🔄", width='stretch', key="live_refresh_btn",
                     help="Consultar RAMMB ahora y cargar el scan más reciente"):
            _get_latest_ts.clear()
            _fetch_latest_ts_all.clear()
            st.rerun()

    # ── Controles de viento ────────────────────────────────────────────────
    # Alturas estandar ISA (Standard Atmosphere) para referencia.
    # Son aproximadas — la altura real a cada nivel de presion varia con
    # temperatura y latitud (±200-500 m), pero sirve como guia operativa.
    WIND_ALTITUDES = {
        "300 hPa": "≈ 9.2 km",
        "500 hPa": "≈ 5.5 km",
        "850 hPa": "≈ 1.5 km",
    }
    # Toolbar compacto. Se ensancha la columna del nivel de viento para que
    # el texto "300 hPa — ≈ 9.2 km" entre completo, y el boton de retry
    # alineado con su selector via gap entre sub-columnas.
    col_w1, col_w2, col_hs, col_vl = st.columns([0.9, 1.9, 1.2, 2.2])
    with col_w1:
        show_wind = st.toggle("💨 Viento (GFS)",
                              value=False, key="live_wind",
                              help="Vectores de viento GFS via Open-Meteo.")
    with col_w2:
        if show_wind:
            sub_a, sub_b = st.columns([5, 1])
            with sub_a:
                wind_level = st.selectbox(
                    "Nivel",
                    list(WIND_LEVELS.keys()),
                    index=1,
                    key="live_wind_level",
                    format_func=lambda k: f"{k} · {WIND_ALTITUDES.get(k, '')}",
                    label_visibility="collapsed",
                )
            with sub_b:
                # Espaciador top para alinear vertical con selectbox
                st.markdown("<div style='height:0.15rem'></div>",
                            unsafe_allow_html=True)
                if st.button("🔄", key="retry_wind",
                             help="Limpiar cache y volver a pedir"):
                    _fetch_wind_cached.clear()
                    st.rerun()
        else:
            wind_level = "500 hPa"
    with col_hs:
        show_hotspots = st.toggle(
            "🔥 Hot spots FDCF",
            value=False, key="live_hotspots",
            help=(
                "Puntos calientes NOAA FDCF (L2 ABI, cada 10 min). "
                "Erupciones con cenizas frías pueden NO disparar hot spots — "
                "cruzar con Ash RGB."
            ),
        )
    with col_vl:
        volc_layer = st.radio(
            "Volcanes",
            ["Prioritarios (8)", "Todos (43+)", "Ninguno"],
            index=0, horizontal=True, key="live_volc_layer",
            label_visibility="collapsed",
            help=(
                "Catálogo SERNAGEOMIN. El triángulo marca coord real WGS84. "
                "Paralaje GOES-19 puede desplazar el pico 1-3 km al este "
                "(mayor para volcanes altos)."
            ),
        )

    # ── Tabs ──────────────────────────────────────────────────────────────
    # Sub-tabs por producto (GeoColor/Ash/SO2) replican estructura de Nacional
    # en Zona y Volcan tambien -> consistencia UX.
    tab_nacional, tab4, tab5 = st.tabs([
        "🌎 Nacional",
        "🗺️ Por Zona Volcánica",
        "🔬 Volcán",
    ])

    # Etiquetas reusadas para sub-tabs en las 3 vistas (consistencia).
    SUBTAB_LABELS = ["🌍 GeoColor", "🌋 Ash RGB", "🟢 SO2"]
    SUBTAB_PRODS  = ["geocolor", "eumetsat_ash", "jma_so2"]

    notas = {
        "geocolor":    "Color real mejorado (dia). Ideal para ver columnas eruptivas y plumas.",
        "eumetsat_ash":"Ash RGB (EUMETSAT): ceniza = rojo/magenta, nubes = cyan/blanco.",
        "jma_so2":     "Indicador SO2 (JMA): nube de dioxido de azufre = verde brillante.",
    }

    # Leyendas de interpretacion por producto (ash / so2).
    # Ver CLAUDE.md: receta RAMMB/CIRA + Prata (1989) para Ash RGB,
    # canal 8.4 um (B09) para indicador SO2 (JMA).
    LEYENDAS_HTML = {
        "eumetsat_ash": """
        <details style="margin-top:0.4rem; background:rgba(17,24,34,0.55);
                        border:1px solid rgba(255,102,68,0.3); border-radius:8px;
                        padding:0.5rem 0.8rem;">
          <summary style="cursor:pointer; font-weight:700; color:#ff8866;
                          font-size:0.88rem;">
            Como leer Ash RGB — que colores indican ceniza
          </summary>
          <div style="font-size:0.82rem; color:#c0ccd8; line-height:1.7;
                      margin-top:0.5rem;">
            <b style="color:#ff8866;">Receta RGB (EUMETSAT/RAMMB)</b><br>
            R = BT(12.3) - BT(11.2) &nbsp;·&nbsp;
            G = BT(11.2) - BT(8.6) &nbsp;·&nbsp;
            B = BT(11.2)
            <table style="width:100%; margin-top:0.6rem; border-collapse:collapse;
                          font-size:0.8rem;">
              <tr style="background:rgba(255,255,255,0.04);">
                <th style="text-align:left; padding:0.3rem 0.5rem;">Color</th>
                <th style="text-align:left; padding:0.3rem 0.5rem;">Interpretacion</th>
              </tr>
              <tr>
                <td style="padding:0.25rem 0.5rem;
                           color:#ff4466; font-weight:700;">Rojo / magenta</td>
                <td style="padding:0.25rem 0.5rem;">
                  <b>Ceniza volcanica</b> (BTD 11-12 &lt; 0, firma Prata).
                  Tambien polvo del desierto.
                </td>
              </tr>
              <tr style="background:rgba(255,255,255,0.02);">
                <td style="padding:0.25rem 0.5rem;
                           color:#ffaa33; font-weight:700;">Naranja / amarillo</td>
                <td style="padding:0.25rem 0.5rem;">
                  Ceniza mezclada con gas/SO2 o nubes delgadas frias.
                </td>
              </tr>
              <tr>
                <td style="padding:0.25rem 0.5rem;
                           color:#3fb950; font-weight:700;">Verde</td>
                <td style="padding:0.25rem 0.5rem;">
                  <b>SO2</b> (absorcion fuerte a 8.6 um baja G).
                </td>
              </tr>
              <tr style="background:rgba(255,255,255,0.02);">
                <td style="padding:0.25rem 0.5rem;
                           color:#4a9eff; font-weight:700;">Cyan / celeste</td>
                <td style="padding:0.25rem 0.5rem;">
                  Nubes de hielo (cirrus, topes de convectivas).
                </td>
              </tr>
              <tr>
                <td style="padding:0.25rem 0.5rem;
                           color:#e6edf3; font-weight:700;">Blanco</td>
                <td style="padding:0.25rem 0.5rem;">
                  Nubes espesas frias (cumulonimbos).
                </td>
              </tr>
              <tr style="background:rgba(255,255,255,0.02);">
                <td style="padding:0.25rem 0.5rem;
                           color:#667788; font-weight:700;">Negro / gris oscuro</td>
                <td style="padding:0.25rem 0.5rem;">
                  Superficie caliente sin nubes (noche despejada).
                </td>
              </tr>
            </table>
            <div style="margin-top:0.6rem; font-size:0.76rem; color:#8899aa;
                        border-top:1px solid rgba(255,255,255,0.08);
                        padding-top:0.4rem;">
              <b style="color:#ffaa66;">Tip operativo:</b>
              busca <i>manchas rojo/magenta en movimiento</i> saliendo de un volcan
              conocido. Si la mancha persiste en varios scans consecutivos y se
              desplaza con el viento, es ceniza real. Nubes finas de cirrus
              tambien pueden verse rojizas cerca de amanecer/atardecer — siempre
              cruzar con GeoColor y hot spots FDCF.
            </div>
            <div style="margin-top:0.5rem; font-size:0.72rem; color:#667788;
                        line-height:1.6;">
              <b style="color:#8899aa;">Fuentes:</b><br>
              &bull; <a href="https://resources.eumetrain.org/rgb_quick_guides/quick_guides/VolcanicAshRGB.pdf"
                       target="_blank" style="color:#4a9eff;">EUMETRAIN Volcanic Ash RGB Quick Guide (PDF)</a><br>
              &bull; <a href="https://rammb.cira.colostate.edu/training/visit/quick_guides/QuickGuide_GOESR_AshRGB_final.pdf"
                       target="_blank" style="color:#4a9eff;">RAMMB/CIRA GOES-R Ash RGB Quick Guide (PDF)</a><br>
              &bull; <a href="https://www.nature.com/articles/340691a0"
                       target="_blank" style="color:#4a9eff;">Prata 1989, Nature 340:691 — BTD 11-12 µm split-window</a><br>
              &bull; <a href="https://user.eumetsat.int/resources/user-guides/dust-rgb-quick-guide"
                       target="_blank" style="color:#4a9eff;">EUMETSAT Dust/Ash RGB User Guide</a>
            </div>
          </div>
        </details>
        """,
        "jma_so2": """
        <details style="margin-top:0.4rem; background:rgba(17,24,34,0.55);
                        border:1px solid rgba(68,221,136,0.3); border-radius:8px;
                        padding:0.5rem 0.8rem;">
          <summary style="cursor:pointer; font-weight:700; color:#44dd88;
                          font-size:0.88rem;">
            Como leer SO2 (JMA) — que colores indican dioxido de azufre
          </summary>
          <div style="font-size:0.82rem; color:#c0ccd8; line-height:1.7;
                      margin-top:0.5rem;">
            <b style="color:#44dd88;">Receta JMA (basada en canal 7.3 y 8.4 um)</b><br>
            El SO2 absorbe fuertemente a 8.6 um. El producto resalta la
            diferencia BT(7.3) - BT(8.6) y BT(8.6) - BT(11.2).
            <table style="width:100%; margin-top:0.6rem; border-collapse:collapse;
                          font-size:0.8rem;">
              <tr style="background:rgba(255,255,255,0.04);">
                <th style="text-align:left; padding:0.3rem 0.5rem;">Color</th>
                <th style="text-align:left; padding:0.3rem 0.5rem;">Interpretacion</th>
              </tr>
              <tr>
                <td style="padding:0.25rem 0.5rem;
                           color:#3fe08f; font-weight:700;">Verde intenso</td>
                <td style="padding:0.25rem 0.5rem;">
                  <b>Nube de SO2 densa</b> (firma clara).
                  Tipico de erupciones explosivas y desgasificacion activa.
                </td>
              </tr>
              <tr style="background:rgba(255,255,255,0.02);">
                <td style="padding:0.25rem 0.5rem;
                           color:#aaff55; font-weight:700;">Verde amarillento</td>
                <td style="padding:0.25rem 0.5rem;">
                  SO2 mezclado con ceniza o cenizas con azufre.
                </td>
              </tr>
              <tr>
                <td style="padding:0.25rem 0.5rem;
                           color:#ff4466; font-weight:700;">Rojo / rosado</td>
                <td style="padding:0.25rem 0.5rem;">
                  <b>Ceniza</b> (misma firma termica que Ash RGB).
                </td>
              </tr>
              <tr style="background:rgba(255,255,255,0.02);">
                <td style="padding:0.25rem 0.5rem;
                           color:#4a9eff; font-weight:700;">Azul / cyan</td>
                <td style="padding:0.25rem 0.5rem;">
                  Nubes meteorologicas (hielo, agua).
                </td>
              </tr>
              <tr>
                <td style="padding:0.25rem 0.5rem;
                           color:#667788; font-weight:700;">Gris / marron</td>
                <td style="padding:0.25rem 0.5rem;">
                  Superficie sin senal volcanica.
                </td>
              </tr>
            </table>
            <div style="margin-top:0.6rem; font-size:0.76rem; color:#8899aa;
                        border-top:1px solid rgba(255,255,255,0.08);
                        padding-top:0.4rem;">
              <b style="color:#55ddaa;">Tip operativo:</b>
              el SO2 es mas <i>persistente</i> que la ceniza (vida media en
              troposfera ~2-4 dias vs ceniza que cae en horas). Una pluma
              verde sin rojo suele ser desgasificacion pasiva (fumarolas activas).
              Verde + rojo juntos = erupcion explosiva reciente. Verifica
              concentraciones reales con TROPOMI/Sentinel-5P (UV, mas sensible).
            </div>
            <div style="margin-top:0.5rem; font-size:0.72rem; color:#667788;
                        line-height:1.6;">
              <b style="color:#8899aa;">Fuentes:</b><br>
              &bull; <a href="https://www.data.jma.go.jp/mscweb/data/monitoring/gms_rgb_en.html"
                       target="_blank" style="color:#4a9eff;">JMA RGB Training — Himawari SO2 Product</a><br>
              &bull; <a href="https://rammb.cira.colostate.edu/training/visit/quick_guides/Quick_Guide_SO2_RGB.pdf"
                       target="_blank" style="color:#4a9eff;">RAMMB/CIRA SO2 RGB Quick Guide (PDF)</a><br>
              &bull; <a href="https://slider.cira.colostate.edu"
                       target="_blank" style="color:#4a9eff;">RAMMB/CIRA SLIDER (fuente de las imagenes)</a><br>
              &bull; <a href="https://sentinel.esa.int/web/sentinel/user-guides/sentinel-5p-tropomi"
                       target="_blank" style="color:#4a9eff;">TROPOMI/Sentinel-5P — validacion UV independiente</a>
            </div>
          </div>
        </details>
        """,
    }

    # ── Tab nacional: los 3 productos apilados ────────────────────────────
    with tab_nacional:
        # Sub-pestanas por producto (consistencia con Zona/Volcan).
        _sub_geo, _sub_ash, _sub_so2 = st.tabs(SUBTAB_LABELS)
        sub_tabs = dict(zip(SUBTAB_PRODS, [_sub_geo, _sub_ash, _sub_so2]))

        # Descargar viento una sola vez (compartido por los 3 productos).
        wind_data_cached = None
        wind_error = None
        if show_wind:
            wind_data_cached = _fetch_wind_cached(WIND_LEVELS[wind_level])
            if not wind_data_cached:
                wind_error = fetch_wind_diagnostic(WIND_LEVELS[wind_level])

        # Hot spots NOAA FDCF — compartidos por los 3 productos en vista Nacional.
        # Bbox: el de la imagen reprojectada (CHILE_REPROJECTED_BOUNDS).
        hotspots_nacional = []
        hotspots_scan_ts = None
        if show_hotspots:
            with st.spinner("Cargando hot spots NOAA FDCF..."):
                _b = CHILE_REPROJECTED_BOUNDS
                hotspots_nacional, hotspots_scan_ts = _fetch_hotspots_cached(
                    _b["lat_min"], _b["lat_max"], _b["lon_min"], _b["lon_max"],
                )
            _ts_short = (hotspots_scan_ts[11:16] + " UTC"
                         if hotspots_scan_ts else "—")
            if hotspots_nacional:
                st.caption(
                    f"🔥 {len(hotspots_nacional)} hot spot(s) NOAA FDCF detectado(s) "
                    f"en Chile (scan {_ts_short}). Mas info en hover de cada punto."
                )
            else:
                st.caption(
                    f"🔥 Sin hot spots FDCF en Chile en este scan ({_ts_short}). "
                    "Es lo normal: el algoritmo solo detecta superficies muy "
                    "calientes (lava expuesta, incendios, no cenizas frías)."
                )

        for prod_id, prod_label, _ in LIVE_PRODUCTS:
            with sub_tabs[prod_id]:
                # Paso 1 — timestamp (liviano, cache 90s)
                ts = _get_latest_ts(prod_id)
                if ts is None:
                    st.error(f"No se pudo obtener timestamp de {prod_label}.")
                    continue

                # Paso 2 — imagen (pesado, cache 2h por timestamp)
                with st.spinner(f"Cargando {prod_label} · {ts[8:10]}:{ts[10:12]} UTC..."):
                    frame = _fetch_frame_for_ts(prod_id, ts)

                if frame is None:
                    st.error(f"No se pudo descargar {prod_label}.")
                    continue

                bounds = frame.get("bounds", CHILE_TILE_BOUNDS)
                title = (
                    f"{prod_label} — GOES-19 · "
                    f"{frame['label_utc']}  ({frame['label_local']} Chile)"
                )
                fig = _make_fig(frame["image"], bounds, title, volc_layer=volc_layer)
                if show_wind:
                    if wind_data_cached:
                        _add_wind_arrows(fig, wind_data_cached, level_label=wind_level)
                        st.caption(
                            f"🌬 {len(wind_data_cached)} vectores de viento GFS a {wind_level} "
                            f"(flechas amarillas; largo ∝ velocidad)"
                        )
                    elif wind_error:
                        st.warning(
                            f"No se pudieron obtener vectores de viento a {wind_level}. "
                            f"Open-Meteo status={wind_error['status']}. "
                            f"Respuesta: {wind_error['response'][:200]}"
                        )
                if show_hotspots and hotspots_nacional:
                    _add_hotspots(
                        fig, hotspots_nacional,
                        scan_label=(hotspots_scan_ts[11:16] + " UTC"
                                    if hotspots_scan_ts else None),
                    )

                fig.update_layout(
                    height=820,
                    xaxis=dict(range=[bounds["lon_min"], bounds["lon_max"]],
                               autorange=False),
                    yaxis=dict(range=[bounds["lat_min"], bounds["lat_max"]],
                               autorange=False, scaleanchor="x", scaleratio=1),
                    margin=dict(t=40, b=35, l=45, r=15),
                )
                render_compact_legend(
                    prod_id,
                    symbols=("volcano",)
                            + (("hotspot",)
                               if (show_hotspots and hotspots_nacional) else ()),
                )
                st.plotly_chart(fig, width='stretch')

                # Botones de descarga (PNG con timestamp + GeoTIFF georeferenciado)
                _dl_label = (
                    f"GOES-19 {prod_label} - Chile - "
                    f"{frame['label_utc']} ({frame['label_local']} CL)"
                )
                download_buttons(
                    frame["image"],
                    bounds=bounds,
                    base_filename=f"goes19_{prod_id}_chile_{ts}",
                    label_overlay=_dl_label,
                    prod_label=prod_label,
                    key_prefix=f"dl_nacional_{prod_id}",
                )

                st.markdown(
                    f'<div style="font-size:0.75rem; color:#445566; margin-top:0.3rem;">'
                    f'{notas.get(prod_id, "")}'
                    f'</div>',
                    unsafe_allow_html=True,
                )

                # Leyenda interpretativa (solo Ash RGB y SO2).
                if prod_id in LEYENDAS_HTML:
                    st.markdown(LEYENDAS_HTML[prod_id], unsafe_allow_html=True)

    # ── Tab 4: Por Zona Volcánica — sub-tabs por producto (auto-carga 4 zonas) ──
    with tab4:
        _z_geo, _z_ash, _z_so2 = st.tabs(SUBTAB_LABELS)
        zona_sub_tabs = dict(zip(SUBTAB_PRODS, [_z_geo, _z_ash, _z_so2]))

        for prod_zona, sub_tab_z in zona_sub_tabs.items():
            with sub_tab_z:
                ts_zona = _get_latest_ts(prod_zona)
                if ts_zona is None:
                    st.error(f"No se pudo obtener timestamp de {PRODUCT_LABELS.get(prod_zona, prod_zona)}.")
                    continue

                st.markdown(
                    f'<div style="font-size:0.9rem; color:#c0ccd8; margin-bottom:0.4rem; '
                    f'padding:0.3rem 0.6rem; background:rgba(17,24,34,0.5); '
                    f'border-radius:6px; border-left:3px solid #4a9eff;">'
                    f'<b>{PRODUCT_LABELS.get(prod_zona, prod_zona)}</b> · Scan '
                    f'<b style="font-family:monospace;">{ts_zona[8:10]}:{ts_zona[10:12]} UTC</b>'
                    f'<span style="color:#667788; font-size:0.74rem; margin-left:0.5rem;">'
                    f'· Zoom=3 (~3.4 km/px) · 4 zonas en paralelo</span></div>',
                    unsafe_allow_html=True,
                )

                row1_col1, row1_col2 = st.columns(2)
                row2_col1, row2_col2 = st.columns(2)
                zone_cols = {
                    "norte":   row1_col1,
                    "centro":  row1_col2,
                    "sur":     row2_col1,
                    "austral": row2_col2,
                }
                # Descarga paralela de las 4 zonas. Cache 2h por (prod, ts, zona)
                # asi que cambiar de sub-tab no re-descarga si ya se vio.
                from concurrent.futures import ThreadPoolExecutor
                with st.spinner(
                    f"Descargando 4 zonas para {PRODUCT_LABELS.get(prod_zona, prod_zona)}..."
                ):
                    with ThreadPoolExecutor(max_workers=4) as ex:
                        futures = {
                            zk: ex.submit(_fetch_zone_frame, prod_zona, ts_zona, zk)
                            for zk in zone_cols
                        }
                        zone_imgs = {zk: f.result() for zk, f in futures.items()}

                for zone_key, col in zone_cols.items():
                    with col:
                        img_zona = zone_imgs[zone_key]
                        if img_zona is None:
                            st.error(f"Sin datos para {ZONE_LABELS[zone_key]}")
                            continue
                        zone_bounds = VOLCANIC_ZONES[zone_key]
                        zone_title = (
                            f'<b style="color:{ZONE_COLORS[zone_key]};">'
                            f'{ZONE_LABELS[zone_key]}</b>'
                        )
                        st.markdown(zone_title, unsafe_allow_html=True)
                        # Sin titulo en el plot (la zona ya aparece en el
                        # markdown de arriba). Esto evita que titulos largos
                        # tipo 'eumetsat_ash' wrappen y achiquen el plot
                        # respecto a 'geocolor' (titulo corto).
                        fig_z = _make_fig(
                            img_zona, zone_bounds, "",
                            volc_layer=volc_layer,
                        )
                        if show_hotspots:
                            _hs_zona, _hs_ts_z = _fetch_hotspots_cached(
                                zone_bounds["lat_min"], zone_bounds["lat_max"],
                                zone_bounds["lon_min"], zone_bounds["lon_max"],
                            )
                            if _hs_zona:
                                _add_hotspots(
                                    fig_z, _hs_zona,
                                    scan_label=(_hs_ts_z[11:16] + " UTC"
                                                if _hs_ts_z else None),
                                )
                        # Viento: el bug era que solo se aplicaba en Volcan,
                        # no en Zona. Filtrar por bbox de la zona y agregar.
                        if show_wind and wind_data_cached:
                            _wind_z = [w for w in wind_data_cached
                                       if zone_bounds["lat_min"] <= w["lat"] <= zone_bounds["lat_max"]
                                       and zone_bounds["lon_min"] <= w["lon"] <= zone_bounds["lon_max"]]
                            if _wind_z:
                                _add_wind_arrows(fig_z, _wind_z, level_label=wind_level)
                        # Mapas mas grandes: 640 -> 760 px y margenes mas chicos
                        fig_z.update_layout(
                            height=760,
                            margin=dict(l=10, r=10, t=30, b=10),
                        )
                        render_compact_legend(prod_zona,
                                              symbols=("volcano",))
                        st.plotly_chart(fig_z, width='stretch')

                        # Descarga PNG + GeoTIFF por zona
                        _dt_zona = parse_rammb_ts(ts_zona)
                        _zona_label = (
                            f"GOES-19 {PRODUCT_LABELS.get(prod_zona, prod_zona)} - "
                            f"{ZONE_LABELS[zone_key]} - "
                            f"{_dt_zona.strftime('%Y-%m-%d %H:%M UTC')}"
                            f" ({fmt_chile(_dt_zona)} CL)"
                        )
                        download_buttons(
                            img_zona,
                            bounds=zone_bounds,
                            base_filename=(f"goes19_{prod_zona}_{zone_key}_"
                                           f"{ts_zona}"),
                            label_overlay=_zona_label,
                            prod_label=ZONE_LABELS[zone_key],
                            key_prefix=f"dl_zona_{zone_key}_{prod_zona}",
                        )

                # Leyenda interpretativa debajo del grid 2x2.
                if prod_zona in LEYENDAS_HTML:
                    st.markdown(LEYENDAS_HTML[prod_zona], unsafe_allow_html=True)

    # ── Tab 5: Volcán — los 4 productos a la vez ──────────────────────────
    # Delega en `modo_guardia_volcan.volcan_grid`, la MISMA grilla que usan el
    # sub-tab Volcán del Modo Guardia y el slot tv=volcan del Modo Sala. Antes
    # esto era un botón "Cargar volcán" + 3 sub-tabs: dos clics por producto,
    # justo lo que no se puede hacer con un volcán en crisis. Import perezoso
    # (gotcha de hot-reload de Streamlit, documentado en la cabecera del módulo).
    with tab5:
        from dashboard.views.modo_guardia_volcan import volcan_grid

        col_vsel, col_vrad, col_vw, col_vr = st.columns([2.2, 1.2, 1, 1])
        with col_vsel:
            priority_names = [v.name for v in CATALOG
                              if v.name in PRIORITY_VOLCANOES]
            other_names = [v.name for v in CATALOG
                           if v.name not in priority_names]
            volc_options = [f"★ {n}" for n in priority_names] + other_names
            sel_raw = st.selectbox("Volcán", volc_options, index=0,
                                   key="volc_sel")
            sel_name = sel_raw.replace("★ ", "")
        with col_vrad:
            # El radio manda sobre los 4 paneles a la vez (parametro de
            # volcan_grid). Sin esto la vista queda clavada en el radio de
            # Modo Guardia (~38 km) y una pluma que ya se desplazo se sale
            # del cuadro justo cuando hay que seguirla.
            _vg_radius = st.slider(
                "Radio (°)", 0.35, 3.0, 0.35, 0.05, key="vg_radius",
                help="±radio en grados lat/lon (~111 km por grado). Súbelo "
                     "para seguir una pluma que ya se alejó del cráter.")
        with col_vw:
            _vg_wind = st.toggle("💨 Viento", value=False, key="vg_wind",
                                 help="Vectores GFS 300/500/850 hPa sobre el "
                                      "cráter. Cache 1h.")
        with col_vr:
            _vg_rings = st.toggle("⊙ Anillos", value=False, key="vg_rings",
                                  help="Anillos 5/10/25/50 km desde el cráter.")

        volcan_grid(
            sel_name,
            show_wind=_vg_wind,
            show_rings=_vg_rings,
            enable_capture=True,
            fullscreen=st.query_params.get("fullscreen") == "1",
            radius_deg=_vg_radius,
        )

    st.markdown(
        '<div style="font-size:0.72rem; color:#334455; margin-top:1rem; '
        'border-top:1px solid rgba(100,120,140,0.1); padding-top:0.5rem;">'
        'Auto-refresh cada 10 min · Boton 🔄 para forzar actualizacion inmediata · '
        'Fuente: <a href="https://slider.cira.colostate.edu" target="_blank" '
        'style="color:#556677;">RAMMB/CIRA Slider</a> (Colorado State University)'
        '</div>',
        unsafe_allow_html=True,
    )


def render():
    # Manual: expander colapsado al INICIO. Ver dashboard/manuals.py.
    from dashboard.manuals import render_manual
    render_manual("operacional")
    # CSS para compactar top — el header de Streamlit y el padding superior
    # comen mucho espacio vertical y empujan el toolbar fuera de la vista.
    st.markdown(
        """
        <style>
          [data-testid="stHeader"] { background: rgba(0,0,0,0); height: 0; }
          .block-container { padding-top: 0.6rem !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )
    # Header: titulo y subtitulo compactos. Removido "Auto-refresh 10 min" del
    # subtitulo — la info de refresh esta en la badge live (con countdown
    # real cada segundo). Tampoco mostramos el banner verde redundante.
    header(
        "En Vivo — GOES-19 Tiempo Real",
        "slider.cira.colostate.edu · GOES-19 Full Disk · RAMMB/CIRA",
    )

    # refresh_info_badge mostraba badge "↻ por sesion · Tip..." + expander
    # "Como se actualizan los datos". El badge era redundante con la badge
    # live (Auto-refresh + countdown). El expander de detalle se mantiene
    # adentro de _live_content para quien quiera mas info.
    _live_content()
