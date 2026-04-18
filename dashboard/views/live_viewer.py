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
from src.fetch.rammb_slider import (
    CHILE_REPROJECTED_BOUNDS, CHILE_TILE_BOUNDS, CHILE_TILES_Z2, PRODUCTS,
    fetch_stitched_frame, get_latest_timestamps, reproject_to_latlon,
)
from src.fetch.wind_data import WIND_LEVELS, fetch_wind_grid
from src.volcanos import CATALOG, get_priority

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


@st.cache_data(ttl=90, show_spinner=False)
def _get_latest_ts(product: str) -> str | None:
    """Consultar el timestamp del scan mas reciente (cache 90s — liviano).

    Cache corto porque solo llama a un JSON pequeño en RAMMB.
    El resultado cambia cada ~10 minutos cuando GOES publica un nuevo scan.
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


@st.cache_data(ttl=90, show_spinner=False)
def _fetch_latest_ts_all() -> dict:
    """Obtener timestamps mas recientes de todos los productos (cache 90s)."""
    result = {}
    for prod, _, _ in LIVE_PRODUCTS:
        ts = _get_latest_ts(prod)
        if ts:
            dt = parse_rammb_ts(ts)
            result[prod] = {
                "ts": ts,
                "utc": dt.strftime("%H:%M UTC"),
                "local": fmt_chile(dt),
            }
        else:
            result[prod] = None
    return result


def _make_fig(img: np.ndarray, bounds: dict, title: str) -> go.Figure:
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


@st.fragment(run_every="10m")
def _live_content():
    """Contenido principal — se refresca automaticamente cada 10 min.

    Logica de cache en dos capas:
      1. _get_latest_ts(product)     TTL=90s  → consulta liviana del timestamp
      2. _fetch_frame_for_ts(p, ts)  TTL=2h   → descarga pesada, clave = timestamp
    El fragment re-corre cada 10 min, detecta el nuevo ts y descarga solo si cambio.
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
            st.rerun(scope="fragment")

    st.markdown("<div style='height:0.3rem'></div>", unsafe_allow_html=True)

    # ── Controles de viento ────────────────────────────────────────────────
    show_wind = st.checkbox("Mostrar vectores de viento (GFS)", value=False, key="live_wind")
    if show_wind:
        wind_level = st.selectbox("Nivel", list(WIND_LEVELS.keys()), index=1, key="live_wind_level")
    else:
        wind_level = "500 hPa"

    # ── Tabs por producto ──────────────────────────────────────────────────
    tab1, tab2, tab3 = st.tabs(["🌍 GeoColor", "🌋 Ash RGB", "🟢 SO2"])

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
            st.plotly_chart(fig, use_container_width=True)

            st.markdown(
                f'<div style="font-size:0.75rem; color:#445566; margin-top:0.3rem;">'
                f'{notas.get(prod_id, "")}'
                f'</div>',
                unsafe_allow_html=True,
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
