"""Modo Guardia VOLCAN: zoom a un volcan, 3 productos lado a lado.

FILOSOFIA: igual que Modo Guardia (Chile) — solo imagen, sin metricas
automaticas. Aca el zoom es del volcan (~30 km radio) y mostramos 3
composiciones distintas para que el experto compare:

  1. Ash RGB (EUMETSAT receta) — tipico para detectar ceniza
  2. GeoColor — visible/IR, util de dia
  3. SO2 (JMA receta) — destaca SO2 en plumas frescas

Hot spots NOAA FDCF dentro del bbox se overlayean en la primera vista.

Overlays opt-in (toggles en barra superior):
- Viento GFS direccional (300/500/850 hPa) sobre el crater
- Anillos de distancia 5/10/25/50 km

Captura PNG del momento actual: boton de descarga construye una imagen
compuesta con los 3 productos + header de timestamp/coords/viento.

Auto-refresh 60s. Sin %, sin alertas.
"""

import io
import logging
from datetime import datetime, timezone

import numpy as np
import plotly.graph_objects as go
import streamlit as st

from dashboard.utils import fmt_chile, parse_rammb_ts
from src.fetch.goes_fdcf import HotSpot, fetch_latest_hotspots
from src.fetch.rammb_slider import (
    fetch_frame_for_bounds, get_latest_timestamps, ZOOM_VOLCAN,
)
from src.fetch.wind_data import fetch_wind_point
from src.volcanos import PRIORITY_VOLCANOES, get_volcano

logger = logging.getLogger(__name__)

REFRESH_SECONDS = 60
DEFAULT_VOLCANO = "Villarrica"
RADIUS_DEG = 0.35  # ~38 km — un volcan + sus alrededores

PRODUCTS = [
    ("eumetsat_ash", "Ash RGB", "EUMETSAT B15-B14 / B14-B11 / B13"),
    ("geocolor", "GeoColor", "Visible mejorado (CIRA)"),
    ("jma_so2", "SO2 RGB", "JMA B07-B09 / B09-B11"),
]

# Niveles de presion para overlay viento, con color
WIND_LEVELS_VIZ = [
    ("300hPa", "300 hPa (~9 km)", "#ff4444"),    # plumas explosivas altas
    ("500hPa", "500 hPa (~5.5 km)", "#ffaa44"),  # circulacion media
    ("850hPa", "850 hPa (~1.5 km)", "#44dd88"),  # capa limite
]

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
                          ) -> tuple[np.ndarray | None, str | None]:
    """Prueba el ts mas reciente; si no carga, baja al previo. Hasta len(ts) intentos.

    Mismo patron que en mosaico_chile.py — RAMMB a veces tarda en publicar
    tiles para zoom=4 en algunos productos aunque latest_times.json ya
    apunte al nuevo scan.
    """
    for ts in timestamps:
        img = _frame(product, ts, lat_min, lat_max, lon_min, lon_max)
        if img is not None:
            return img, ts
    return None, None


@st.cache_data(ttl=300, show_spinner=False)
def _hotspots_volcan(lat_min: float, lat_max: float,
                     lon_min: float, lon_max: float
                     ) -> tuple[list[HotSpot], datetime | None]:
    bounds = {"lat_min": lat_min, "lat_max": lat_max,
              "lon_min": lon_min, "lon_max": lon_max}
    try:
        return fetch_latest_hotspots(bounds=bounds, hours_back=1)
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


# ── Conversion array a data URL ──────────────────────────────────────

def _array_to_data_url(arr: np.ndarray) -> str:
    import base64
    from PIL import Image
    img = Image.fromarray(arr.astype(np.uint8))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


# ── Render por producto ──────────────────────────────────────────────

def _render_product(img: np.ndarray | None, bounds: dict, product_label: str,
                    volcan_lat: float, volcan_lon: float, volcan_name: str,
                    hotspots: list[HotSpot] | None = None,
                    show_wind: bool = False, wind_data: dict | None = None,
                    show_rings: bool = False):
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
        marker=dict(symbol="triangle-up", size=16, color="#00ffff",
                    line=dict(color="white", width=1.5)),
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
        height=620, margin=dict(l=0, r=0, t=28, b=0),
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
                       generated_utc: datetime) -> bytes:
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
    draw.text((40, 115),
              f"Captura UTC: {generated_utc.strftime('%Y-%m-%d %H:%M:%S')} · "
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

@st.fragment(run_every=f"{REFRESH_SECONDS}s")
def _live_panel(volcan_name: str, show_wind: bool, show_rings: bool,
                enable_capture: bool):
    v = get_volcano(volcan_name)
    if v is None:
        st.error(f"Volcan {volcan_name} no esta en el catalogo.")
        return

    bounds = {
        "lat_min": v.lat - RADIUS_DEG, "lat_max": v.lat + RADIUS_DEG,
        "lon_min": v.lon - RADIUS_DEG, "lon_max": v.lon + RADIUS_DEG,
    }
    now = datetime.now(timezone.utc)

    hotspots, _ = _hotspots_volcan(
        bounds["lat_min"], bounds["lat_max"],
        bounds["lon_min"], bounds["lon_max"],
    )
    wind = _wind_at_volcano(v.lat, v.lon) if show_wind else {}

    # Cabecera info
    wind_summary = ""
    if wind:
        bits = []
        for level_id, label, _c in WIND_LEVELS_VIZ:
            w = wind.get(level_id)
            if w:
                bits.append(f"{level_id} {w['speed']:.0f} km/h@{w['direction']:.0f}°")
        if bits:
            wind_summary = " · " + " · ".join(bits)

    st.markdown(
        f"<div style='background:#0f1418; border-left:4px solid #ff6644; "
        f"padding:0.7rem 1rem; border-radius:4px; margin-bottom:0.8rem;'>"
        f"<div style='display:flex; justify-content:space-between; align-items:center;'>"
        f"<div><span style='font-size:1.4rem; font-weight:800; color:#ff6644;'>"
        f"{v.name}</span> &nbsp;"
        f"<span style='color:#7a8a9a; font-size:0.85rem;'>"
        f"{v.region} · elev {v.elevation} m · {v.lat}°, {v.lon}°{wind_summary}</span></div>"
        f"<div style='font-size:0.85rem; color:#9aaabb;'>"
        f"Hot spots {len(hotspots)} · Render {now.strftime('%H:%M:%S')} UTC / "
        f"{fmt_chile(now)}</div></div></div>",
        unsafe_allow_html=True,
    )

    # Bajar los 3 productos (cache 2h por ts) con fallback a ts previos
    captured = []   # (label, img, ts_label) para captura
    cols = st.columns(3)
    for i, (prod_id, label, recipe) in enumerate(PRODUCTS):
        timestamps = _recent_timestamps(prod_id, n=3)
        img = None
        ts_label = "—"
        used_ts = None
        if timestamps:
            img, used_ts = _frame_with_fallback(
                prod_id, timestamps,
                bounds["lat_min"], bounds["lat_max"],
                bounds["lon_min"], bounds["lon_max"],
            )
            if used_ts:
                try:
                    ts_dt = parse_rammb_ts(used_ts)
                    age = int((now - ts_dt).total_seconds() / 60)
                    ts_label = f"{ts_dt.strftime('%H:%M UTC')} (hace {age} min)"
                    if used_ts != timestamps[0]:
                        ts_label += " ⚠ scan previo"
                except Exception:
                    ts_label = used_ts

        captured.append((label, img, ts_label))

        # Hotspots overlay solo en Ash; viento en los 3 (es info universal)
        hs = hotspots if prod_id == "eumetsat_ash" else None
        full_label = f"{label} · {ts_label}"
        with cols[i]:
            st.plotly_chart(
                _render_product(img, bounds, full_label, v.lat, v.lon, v.name,
                                hotspots=hs, show_wind=show_wind, wind_data=wind,
                                show_rings=show_rings),
                use_container_width=True,
                config={"displayModeBar": False},
            )
            st.markdown(
                f"<div style='font-size:0.7rem; color:#556; margin-top:-0.5rem;'>"
                f"{recipe}</div>",
                unsafe_allow_html=True,
            )

    # Boton de captura
    if enable_capture:
        try:
            png_bytes = _build_capture_png(
                v.name, v.lat, v.lon, v.elevation, v.region,
                captured, wind, len(hotspots), now,
            )
            st.download_button(
                label="📸 Descargar captura PNG (este momento)",
                data=png_bytes,
                file_name=f"{v.name}_{now.strftime('%Y%m%d_%H%M')}_UTC.png",
                mime="image/png",
                use_container_width=True,
            )
        except Exception as e:
            st.warning(f"No se pudo construir captura: {e}")

    # Footer filosofia
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
        "Zoom volcan · 3 productos lado a lado · GOES-19</div></div>",
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
            "Refresh 60s</div>",
            unsafe_allow_html=True,
        )

    _live_panel(volcan, show_wind, show_rings, enable_capture)
