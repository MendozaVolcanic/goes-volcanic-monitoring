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

from dashboard.style import C_ACCENT, header, info_panel, kpi_card
from dashboard.utils import (
    fmt_both_long, fmt_chile, now_utc, parse_rammb_ts, utc_to_chile,
)
from src.config import VOLCANIC_ZONES
from src.fetch.rammb_slider import (
    CHILE_REPROJECTED_BOUNDS, CHILE_TILE_BOUNDS, CHILE_TILES_Z2, PRODUCTS,
    fetch_stitched_frame, fetch_frame_for_bounds,
    get_latest_timestamps, reproject_to_latlon,
    ZOOM_ZONE, ZOOM_VOLCAN, VOLCANO_RADIUS_DEG,
)
from src.fetch.wind_data import WIND_LEVELS, fetch_wind_grid
from src.volcanos import CATALOG, get_priority, get_volcano, PRIORITY_VOLCANOES

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


@st.cache_data(ttl=30, show_spinner=False)
def _get_latest_ts(product: str) -> str | None:
    """Consultar el timestamp del scan mas reciente (cache 30s — liviano).

    TTL corto para detectar el nuevo scan rapido (RAMMB publica 3-5 min
    despues del fin del scan de GOES-19; latencia de deteccion ≤ 30s + 60s
    del fragment = max ~90s desde que aparece).
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


@st.cache_data(ttl=7200, show_spinner=False)
def _fetch_volcano_frame(
    product: str, ts: str, volcano_name: str,
    radius: float = VOLCANO_RADIUS_DEG,
    _v: str = _REPROJECT_VERSION,
) -> tuple[np.ndarray | None, int]:
    """Descargar frame centrado en un volcan (zoom=4 con fallback a zoom=3).

    Returns:
        (img, zoom_usado). Si falla todo, (None, 0).
    """
    v = get_volcano(volcano_name)
    if v is None:
        return None, 0
    bounds = {
        "lat_min": v.lat - radius,
        "lat_max": v.lat + radius,
        "lon_min": v.lon - radius,
        "lon_max": v.lon + radius,
    }
    # Intento 1: zoom=4 (~1.7 km/px). RAMMB no siempre tiene zoom=4 para
    # todos los productos/timestamps — puede tardar mas en publicarse.
    img = fetch_frame_for_bounds(product, ts, bounds, zoom=ZOOM_VOLCAN)
    if img is not None:
        return img, ZOOM_VOLCAN
    # Intento 2: fallback a zoom=3 (~3.4 km/px), siempre disponible.
    img = fetch_frame_for_bounds(product, ts, bounds, zoom=ZOOM_ZONE)
    if img is not None:
        return img, ZOOM_ZONE
    return None, 0


@st.cache_data(ttl=30, show_spinner=False)
def _fetch_latest_ts_all() -> dict:
    """Obtener timestamps mas recientes de todos los productos (cache 90s).

    Llama get_latest_timestamps directamente (NO via _get_latest_ts) para
    evitar llamadas anidadas entre funciones @st.cache_data, que Streamlit
    no soporta y causa 'Error running app' en Streamlit Cloud.
    """
    result = {}
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


def _make_fig(img: np.ndarray, bounds: dict, title: str, highlight_volcano=None) -> go.Figure:
    """Crear figura Plotly con imagen georeferenciada y volcanes."""
    import base64, io
    from PIL import Image as PILImage

    lat_min = bounds["lat_min"]
    lat_max = bounds["lat_max"]
    lon_min = bounds["lon_min"]
    lon_max = bounds["lon_max"]

    buf = io.BytesIO()
    PILImage.fromarray(img).save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode()

    # Volcanes visibles en el area
    vis = [v for v in get_priority()
           if lat_min <= v.lat <= lat_max and lon_min <= v.lon <= lon_max]
    if not vis:
        vis = [v for v in CATALOG
               if lat_min <= v.lat <= lat_max and lon_min <= v.lon <= lon_max][:15]

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
            marker=dict(size=6, color=C_ACCENT, symbol="triangle-up",
                        line=dict(width=1, color="white")),
            text=[v.name for v in vis],
            textposition="top center",
            textfont=dict(size=8, color="rgba(255,255,255,0.75)"),
            name="Volcanes",
            hovertext=[f"<b>{v.name}</b><br>{v.elevation:,} m" for v in vis],
            hoverinfo="text", showlegend=False,
        ))

    # Marcador resaltado para volcán seleccionado (vista zoom)
    if highlight_volcano is not None:
        fig.add_trace(go.Scatter(
            x=[highlight_volcano.lon], y=[highlight_volcano.lat],
            mode="markers+text",
            marker=dict(size=14, color="#ff4444", symbol="triangle-up",
                        line=dict(width=2, color="white")),
            text=[highlight_volcano.name],
            textposition="top center",
            textfont=dict(size=10, color="white", family="Arial Black"),
            name=highlight_volcano.name,
            hovertext=f"<b>{highlight_volcano.name}</b><br>{highlight_volcano.elevation:,} m",
            hoverinfo="text", showlegend=False,
        ))

    fig.update_layout(
        title=dict(text=title, font=dict(size=12, color="#99aabb")),
        xaxis_title="Longitud", yaxis_title="Latitud",
        height=640, template="plotly_dark",
        yaxis=dict(scaleanchor="x", scaleratio=1,
                   range=[lat_min - 0.5, lat_max + 0.5]),
        xaxis=dict(range=[lon_min - 0.5, lon_max + 0.5]),
        margin=dict(t=40, b=40, l=50, r=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    return fig


@st.cache_data(ttl=3600, show_spinner=False)
def _fetch_wind_cached(level: str) -> list:
    """Obtener grilla de viento GFS (cache 1 hora)."""
    return fetch_wind_grid(level=level)


def _add_wind_arrows(
    fig,
    wind_data: list,
    scale: float = 0.03,
    color: str = "rgba(160,200,255,0.80)",
    level_label: str = "500 hPa",
) -> None:
    """Agregar vectores de viento como flechas de anotacion Plotly.

    scale: grados de desplazamiento por km/h de viento.
           0.03 → viento de 50 km/h = flecha de 1.5 grados.
    """
    if not wind_data:
        return

    import plotly.graph_objects as go
    fig.add_trace(go.Scatter(
        x=[None], y=[None], mode="lines",
        line=dict(color=color, width=2),
        name=f"Viento {level_label} (GFS)",
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
            arrowhead=2,
            arrowsize=0.9,
            arrowwidth=1.5,
            arrowcolor=color,
            text="",
            showarrow=True,
            hovertext=f"<b>{w['speed']:.0f} km/h</b> @ {w['direction']:.0f}°",
        )


def _reloj_chile():
    """Mostrar reloj UTC + hora Chile en tiempo real."""
    now = now_utc()
    utc_str = now.strftime("%H:%M:%S UTC")
    ch_str = fmt_chile(now)
    date_str = now.strftime("%d %b %Y")
    st.markdown(
        f'<div style="text-align:center; padding:0.6rem; '
        f'background:rgba(17,24,34,0.6); border-radius:8px; '
        f'border:1px solid rgba(100,120,140,0.2);">'
        f'<div style="font-size:0.68rem; color:#556677; text-transform:uppercase; '
        f'letter-spacing:0.1em;">{date_str}</div>'
        f'<div style="font-size:1.6rem; font-weight:700; color:#e8eaf0; '
        f'font-family:monospace; letter-spacing:0.05em;">{utc_str}</div>'
        f'<div style="font-size:1rem; color:#99aabb; font-family:monospace;">'
        f'{ch_str} <span style="color:#445566; font-size:0.75rem;">Chile</span></div>'
        f'</div>',
        unsafe_allow_html=True,
    )


@st.fragment(run_every="60s")
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

    # ── Fila superior: reloj · estado · botón refresh ─────────────────────
    col_clock, col_status, col_btn = st.columns([1, 2, 0.6])

    with col_clock:
        _reloj_chile()

    with col_status:
        ts_all = _fetch_latest_ts_all()
        status_html = (
            '<div style="padding:0.5rem 0.8rem; background:rgba(17,24,34,0.6); '
            'border-radius:8px; border:1px solid rgba(100,120,140,0.2);">'
            '<div style="font-size:0.68rem; color:#556677; text-transform:uppercase; '
            'letter-spacing:0.08em; margin-bottom:0.4rem;">'
            'Ultimo scan disponible · RAMMB/CIRA</div>'
        )
        for prod, label, color in LIVE_PRODUCTS:
            info = ts_all.get(prod)
            if info:
                status_html += (
                    f'<div style="font-size:0.82rem; line-height:1.9;">'
                    f'<span style="color:{color}; font-weight:700;">■</span> '
                    f'<b style="color:#c0ccd8;">{label}</b> '
                    f'<span style="color:#99aabb; font-family:monospace;">{info["utc"]}</span>'
                    f'<span style="color:#5a6a7a; font-size:0.75rem; margin-left:0.5rem;">'
                    f'({info["local"]} Chile)</span>'
                    f'</div>'
                )
            else:
                status_html += (
                    f'<div style="font-size:0.82rem; color:#445566;">'
                    f'<b>{label}</b> — no disponible</div>'
                )
        status_html += '</div>'
        st.markdown(status_html, unsafe_allow_html=True)

    with col_btn:
        st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
        if st.button("🔄 Actualizar", use_container_width=True, key="live_refresh_btn",
                     help="Consultar RAMMB ahora mismo e cargar el scan mas reciente"):
            # Invalidar solo el cache liviano de timestamps.
            # Los frames ya descargados (cache 2h por ts) se conservan.
            _get_latest_ts.clear()
            _fetch_latest_ts_all.clear()
            st.rerun()

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

    _stc.html(
        f"""
        <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                    font-size:0.88rem; color:#99aabb; padding:0.5rem 0.9rem;
                    background:rgba(17,24,34,0.5);
                    border-radius:8px; border:1px solid rgba(74,158,255,0.2);
                    display:flex; align-items:center; gap:1.1rem; flex-wrap:wrap;">
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
          <span title="Timestamp que GOES-19 grabo en el nombre del archivo de RAMMB (inicio del scan). NO es la hora en que lo vimos nosotros.">
            Hora del scan (RAMMB):
            <b style="color:#e6edf3; font-family:monospace;">{_last_iso}</b>
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
        """,
        height=55,
    )

    # ── Controles de viento ────────────────────────────────────────────────
    # Alturas estandar ISA (Standard Atmosphere) para referencia.
    # Son aproximadas — la altura real a cada nivel de presion varia con
    # temperatura y latitud (±200-500 m), pero sirve como guia operativa.
    WIND_ALTITUDES = {
        "300 hPa": "≈ 9.2 km · plumas altas (erupciones explosivas)",
        "500 hPa": "≈ 5.5 km · circulacion media (mas usado)",
        "850 hPa": "≈ 1.5 km · capa limite / plumas bajas",
    }
    show_wind = st.checkbox("Mostrar vectores de viento (GFS)", value=False, key="live_wind")
    if show_wind:
        wind_level = st.selectbox(
            "Nivel de presion",
            list(WIND_LEVELS.keys()),
            index=1,
            key="live_wind_level",
            format_func=lambda k: f"{k}  —  {WIND_ALTITUDES.get(k, '')}",
            help=(
                "La altura es aproximada (atmosfera estandar ISA). "
                "Varia ±200-500 m segun temperatura y latitud."
            ),
        )
    else:
        wind_level = "500 hPa"

    # ── Tabs ──────────────────────────────────────────────────────────────
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🌍 GeoColor", "🌋 Ash RGB", "🟢 SO2",
        "🗺️ Por Zonas", "🔬 Volcán",
    ])

    notas = {
        "geocolor":    "Color real mejorado (dia). Ideal para ver columnas eruptivas y plumas.",
        "eumetsat_ash":"Ash RGB (EUMETSAT): ceniza = rojo/magenta, nubes = cyan/blanco.",
        "jma_so2":     "Indicador SO2 (JMA): nube de dioxido de azufre = verde brillante.",
    }

    for tab, (prod_id, prod_label, _) in zip([tab1, tab2, tab3], LIVE_PRODUCTS):
        with tab:
            # Paso 1 — timestamp (liviano, cache 90s)
            ts = _get_latest_ts(prod_id)
            if ts is None:
                st.error(f"No se pudo obtener timestamp de {prod_label}. Verifica conexion.")
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
            fig = _make_fig(frame["image"], bounds, title)
            if show_wind:
                wind_data = _fetch_wind_cached(WIND_LEVELS[wind_level])
                _add_wind_arrows(fig, wind_data, level_label=wind_level)
            # Forzar rango y altura grande para maxima visibilidad
            fig.update_layout(
                height=820,
                xaxis=dict(range=[bounds["lon_min"], bounds["lon_max"]],
                           autorange=False),
                yaxis=dict(range=[bounds["lat_min"], bounds["lat_max"]],
                           autorange=False, scaleanchor="x", scaleratio=1),
                margin=dict(t=40, b=35, l=45, r=15),
            )
            st.plotly_chart(fig, use_container_width=True)

            st.markdown(
                f'<div style="font-size:0.75rem; color:#445566; margin-top:0.3rem;">'
                f'{notas.get(prod_id, "")}'
                f'</div>',
                unsafe_allow_html=True,
            )

    # ── Tab 4: Por Zonas (lazy: solo carga al presionar boton) ────────────
    with tab4:
        prod_zona = st.selectbox(
            "Producto", ["geocolor", "eumetsat_ash", "jma_so2"],
            format_func=lambda k: PRODUCT_LABELS.get(k, k),
            key="zona_product",
        )
        # Lazy loading: evita descargar 4 reproyecciones en cada auto-refresh
        # (Streamlit ejecuta el codigo de TODOS los tabs, esten visibles o no).
        cargar_zonas = st.button(
            "Cargar 4 zonas volcanicas (zoom=3)",
            key="btn_cargar_zonas", type="primary",
        )
        if not cargar_zonas and not st.session_state.get("zonas_cargadas"):
            st.info(
                "Presiona el boton para descargar las 4 zonas volcanicas "
                "(Norte, Centro, Sur, Austral) a zoom=3."
            )
        else:
            st.session_state["zonas_cargadas"] = True
            ts_zona = _get_latest_ts(prod_zona)
            if ts_zona is None:
                st.error("No se pudo obtener timestamp. Verifica conexion.")
            else:
                st.markdown(
                    f'<div style="font-size:1.05rem; color:#c0ccd8; margin-bottom:0.6rem; '
                    f'padding:0.4rem 0.7rem; background:rgba(17,24,34,0.5); '
                    f'border-radius:6px; border-left:3px solid #4a9eff;">'
                    f'Scan: <b style="color:#e6edf3; font-family:monospace; font-size:1.15rem;">'
                    f'{ts_zona[8:10]}:{ts_zona[10:12]} UTC</b>'
                    f'<span style="color:#667788; font-size:0.82rem; margin-left:0.7rem;">'
                    f'· Zoom=3 (~3.4 km/px) · Descarga en paralelo</span></div>',
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
                for zone_key, col in zone_cols.items():
                    with col:
                        with st.spinner(f"{ZONE_LABELS[zone_key]}..."):
                            img_zona = _fetch_zone_frame(prod_zona, ts_zona, zone_key)
                        if img_zona is None:
                            st.error(f"Sin datos para {ZONE_LABELS[zone_key]}")
                            continue
                        zone_bounds = VOLCANIC_ZONES[zone_key]
                        zone_title = (
                            f'<b style="color:{ZONE_COLORS[zone_key]};">'
                            f'{ZONE_LABELS[zone_key]}</b>'
                        )
                        st.markdown(zone_title, unsafe_allow_html=True)
                        fig_z = _make_fig(
                            img_zona, zone_bounds,
                            f"{ZONE_LABELS[zone_key]} · {prod_zona} · zoom=3",
                        )
                        fig_z.update_layout(height=640)
                        st.plotly_chart(fig_z, use_container_width=True)

    # ── Tab 5: Volcán zoom=4 ───────────────────────────────────────────────
    with tab5:
        col_vsel, col_vprod, col_vrad = st.columns([2, 1.2, 1])
        with col_vsel:
            priority_names = [v.name for v in CATALOG if v.name in
                              [p for p in PRIORITY_VOLCANOES]]
            other_names    = [v.name for v in CATALOG if v.name not in priority_names]
            volc_options   = (
                [f"★ {n}" for n in priority_names] + other_names
            )
            sel_raw = st.selectbox("Volcán", volc_options, index=0, key="volc_sel")
            sel_name = sel_raw.replace("★ ", "")
        with col_vprod:
            prod_volc = st.selectbox(
                "Producto", ["geocolor", "eumetsat_ash", "jma_so2"],
                format_func=lambda k: PRODUCT_LABELS.get(k, k),
                key="volc_product",
            )
        with col_vrad:
            radius = st.slider("Radio (°)", 0.5, 3.0, VOLCANO_RADIUS_DEG, 0.5,
                               key="volc_radius",
                               help="±radio en grados lat/lon (~111 km por grado)")

        # Lazy loading: zoom=4 descarga 9-16 tiles, solo bajo demanda
        cargar_volc = st.button(
            f"Cargar zoom=4 para volcan seleccionado",
            key="btn_cargar_volc", type="primary",
        )
        if not cargar_volc and not st.session_state.get("volc_cargado"):
            st.info(
                "Presiona el boton para descargar la vista zoom=4 "
                "(~1.7 km/px) del volcan seleccionado."
            )
        else:
            st.session_state["volc_cargado"] = True
            ts_volc = _get_latest_ts(prod_volc)
            volcano = get_volcano(sel_name)

            if volcano is None:
                st.error(f"Volcan '{sel_name}' no encontrado en el catalogo.")
            elif ts_volc is None:
                st.error("No se pudo obtener timestamp.")
            else:
                volc_bounds = {
                    "lat_min": volcano.lat - radius,
                    "lat_max": volcano.lat + radius,
                    "lon_min": volcano.lon - radius,
                    "lon_max": volcano.lon + radius,
                }
                with st.spinner(
                    f"Cargando para {volcano.name} "
                    f"({ts_volc[8:10]}:{ts_volc[10:12]} UTC)..."
                ):
                    img_volc, zoom_used = _fetch_volcano_frame(
                        prod_volc, ts_volc, sel_name, radius,
                    )

                if img_volc is None or zoom_used == 0:
                    st.error(
                        f"RAMMB no tiene tiles de **{prod_volc}** ni en zoom=4 "
                        f"ni en zoom=3 para el scan {ts_volc[8:10]}:{ts_volc[10:12]} UTC. "
                        "Prueba con otro producto o espera el siguiente scan."
                    )
                else:
                    km_per_px = 1.7 if zoom_used == ZOOM_VOLCAN else 3.4
                    zoom_label = (f"Zoom=4 (~1.7 km/px)" if zoom_used == ZOOM_VOLCAN
                                  else f"Zoom=3 (~3.4 km/px, zoom 4 no disponible)")
                    st.markdown(
                        f'<div style="font-size:1.05rem; color:#c0ccd8; margin-bottom:0.6rem; '
                        f'padding:0.4rem 0.7rem; background:rgba(17,24,34,0.5); '
                        f'border-radius:6px; border-left:3px solid #CC3311;">'
                        f'<b style="color:#e6edf3; font-size:1.15rem;">{volcano.name}</b>'
                        f'<span style="color:#99aabb; margin-left:0.6rem;">'
                        f'{volcano.lat:.2f}°, {volcano.lon:.2f}° · '
                        f'{volcano.elevation:,} m</span><br>'
                        f'Scan: <b style="color:#e6edf3; font-family:monospace; font-size:1.15rem;">'
                        f'{ts_volc[8:10]}:{ts_volc[10:12]} UTC</b>'
                        f'<span style="color:#667788; font-size:0.82rem; margin-left:0.7rem;">'
                        f'· {zoom_label}</span></div>',
                        unsafe_allow_html=True,
                    )
                    fig_v = _make_fig(
                        img_volc, volc_bounds,
                        f"{volcano.name} · {prod_volc} · "
                        f"±{radius}° ({radius*111:.0f} km)",
                        highlight_volcano=volcano,
                    )
                    fig_v.update_layout(height=700)
                    st.plotly_chart(fig_v, use_container_width=True)

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
    header(
        "En Vivo — GOES-19 Tiempo Real",
        "Ultimo scan disponible · Auto-refresh 10 min · RAMMB/CIRA Slider",
    )

    st.markdown(
        '<div class="status-banner ok">'
        '<b>&#128994; En vivo — se actualiza automaticamente cada 10 minutos</b>'
        '<span style="color:#556677; font-size:0.78rem;">slider.cira.colostate.edu · GOES-19 Full Disk</span>'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

    _live_content()
