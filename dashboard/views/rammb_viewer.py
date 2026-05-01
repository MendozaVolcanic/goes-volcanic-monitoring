"""Pagina RAMMB Slider: animacion de imagenes GOES-19 en tiempo real.

Muestra loops animados de los ultimos N scans del satelite GOES-19,
con 3 escopos: Nacional (Chile completo), Por zona volcanica, Por volcan.

Fuente: slider.cira.colostate.edu (CIRA/CSU + NOAA/RAMMB).
"""

import base64
import io
import logging
import zipfile
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import plotly.graph_objects as go
import streamlit as st
from PIL import Image as PILImage, ImageDraw, ImageFont

from dashboard.style import (
    C_ACCENT, C_ASH, C_SO2,
    header, info_panel, kpi_card, refresh_info_badge,
)
from dashboard.utils import fmt_both, fmt_both_long, fmt_chile, parse_rammb_ts
from src.config import CHILE_BOUNDS, VOLCANIC_ZONES
from src.fetch.rammb_slider import (
    CHILE_REPROJECTED_BOUNDS, CHILE_TILE_BOUNDS, CHILE_TILES_Z2, PRODUCTS,
    ZOOM_ZONE, ZOOM_VOLCAN, VOLCANO_RADIUS_DEG,
    fetch_animation_frames, fetch_frame_for_bounds,
    get_latest_timestamps, reproject_to_latlon, ts_to_parts,
)
# NOTA: src.fetch.animation_cache se importa LAZY dentro de _fetch_via_cache
# y _scope_id_from_bounds_key. Importarlo top-level activa el gotcha
# "KeyError: 'dashboard.style'" en Streamlit Cloud entre deploys (ver CLAUDE.md).
from src.fetch.wind_data import fetch_wind_point
from src.volcanos import CATALOG, PRIORITY_VOLCANOES, get_priority, get_volcano

logger = logging.getLogger(__name__)

FRAME_OPTIONS = {
    "1 hora (6 frames)": 6,
    "2 horas (12 frames)": 12,
    "3 horas (18 frames)": 18,
}

PRODUCT_LABELS = {
    "geocolor":    "GeoColor",
    "eumetsat_ash": "Ash RGB",
    "jma_so2":     "SO2",
    "split_window_difference_10_3-12_3": "BTD",
}

ZONE_LABELS = {
    "norte":   "Zona Norte",
    "centro":  "Zona Centro",
    "sur":     "Zona Sur",
    "austral": "Zona Austral",
}


def _frame_label(ts: str) -> str:
    """'20260424122000' -> '2026-04-24 12:20 UTC (08:20 CLT)'"""
    dt = parse_rammb_ts(ts)
    return fmt_both_long(dt)


def _img_to_b64(arr: np.ndarray) -> str:
    buf = io.BytesIO()
    PILImage.fromarray(arr).save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


def _annotated_pil(arr: np.ndarray, label: str, max_width: int = 1200) -> PILImage.Image:
    """Convertir frame numpy a PIL con timestamp + branding sobre-impreso.

    Reduce ancho a max_width para que el GIF no quede gigante. Mantiene
    aspect ratio. Fontsize escala con el ancho final.
    """
    img = PILImage.fromarray(arr).convert("RGB")
    if img.width > max_width:
        scale = max_width / img.width
        new_size = (max_width, int(img.height * scale))
        img = img.resize(new_size, PILImage.LANCZOS)

    draw = ImageDraw.Draw(img)
    # Tamano de fuente proporcional al ancho. ~2.2% del ancho es legible.
    fs = max(12, int(img.width * 0.022))
    try:
        # Fuente truetype no esta garantizada en Streamlit Cloud. Fallback.
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", fs)
    except Exception:
        try:
            font = ImageFont.truetype("arial.ttf", fs)
        except Exception:
            font = ImageFont.load_default()

    # Banner negro semi-transparente abajo con el label
    pad = max(6, fs // 3)
    bbox = draw.textbbox((0, 0), label, font=font)
    text_h = bbox[3] - bbox[1]
    band_h = text_h + pad * 2
    y0 = img.height - band_h
    # Cinta negra
    overlay = PILImage.new("RGBA", img.size, (0, 0, 0, 0))
    odraw = ImageDraw.Draw(overlay)
    odraw.rectangle([0, y0, img.width, img.height], fill=(0, 0, 0, 180))
    img = PILImage.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(img)
    draw.text((pad, y0 + pad), label, fill=(255, 255, 255), font=font)

    # Branding arriba a la derecha (chiquito)
    brand = "GOES-19 / RAMMB-CIRA"
    bbbox = draw.textbbox((0, 0), brand, font=font)
    bw = bbbox[2] - bbbox[0]
    draw.text((img.width - bw - pad, pad), brand,
              fill=(180, 200, 220), font=font)
    return img


def _build_gif(frames: list[dict], duration_ms: int = 700) -> bytes:
    """Construir GIF animado a partir de los frames.

    Cada frame trae timestamp + marca sobre-impresa. Loop infinito.
    """
    pil_frames = [_annotated_pil(f["image"], f["label"]) for f in frames]
    if not pil_frames:
        return b""
    buf = io.BytesIO()
    pil_frames[0].save(
        buf, format="GIF",
        save_all=True,
        append_images=pil_frames[1:],
        duration=duration_ms,
        loop=0,             # 0 = loop infinito
        optimize=True,
        disposal=2,
    )
    return buf.getvalue()


def _build_mp4(frames: list[dict], fps: float = 1.5) -> bytes:
    """Construir MP4 H.264 a partir de los frames (con timestamp impreso).

    H.264 + yuv420p es el codec mas compatible (PowerPoint, navegadores,
    mac/windows/linux, Quicktime). Mucho mas liviano que GIF (~20-50% del
    tamano) y mejor calidad.

    Requiere imageio-ffmpeg (trae binario static).

    fps por defecto 1.5 (cada scan dura ~0.66s en el video). Subir a 4-6 fps
    para playback mas rapido.
    """
    try:
        import imageio.v2 as iio
    except Exception as e:
        logger.error("imageio no disponible: %s", e)
        return b""

    pil_frames = [_annotated_pil(f["image"], f["label"]) for f in frames]
    if not pil_frames:
        return b""

    # H.264 requiere dimensiones PARES. Padear si es necesario.
    arrs = []
    for pf in pil_frames:
        a = np.asarray(pf)
        h, w = a.shape[:2]
        new_h = h + (h % 2)
        new_w = w + (w % 2)
        if (new_h, new_w) != (h, w):
            padded = np.zeros((new_h, new_w, 3), dtype=a.dtype)
            padded[:h, :w] = a
            a = padded
        arrs.append(a)

    # imageio escribe a archivo — usamos un tempfile y leemos los bytes.
    import tempfile
    import os
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
            tmp_path = tmp.name
        # macro_block_size=1 evita que imageio fuerce dimension multiplo de 16
        # (tendria que padear de mas y la imagen quedaria con borde negro grande).
        # quality=8 es calidad alta sin ser absurda en tamano.
        writer = iio.get_writer(
            tmp_path,
            format="FFMPEG",
            mode="I",
            fps=fps,
            codec="libx264",
            quality=8,
            pixelformat="yuv420p",
            macro_block_size=1,
            ffmpeg_log_level="error",
        )
        try:
            for arr in arrs:
                writer.append_data(arr)
        finally:
            writer.close()
        with open(tmp_path, "rb") as f:
            return f.read()
    except Exception as e:
        logger.exception("Error construyendo MP4: %s", e)
        return b""
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except OSError:
                pass


def _build_zip_frames(frames: list[dict], product_label: str,
                      scope_label: str) -> bytes:
    """ZIP con (1) PNGs originales sin overlay, (2) manifest.csv con metadata."""
    if not frames:
        return b""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        # Manifest CSV
        lines = ["frame,timestamp_utc,filename,lat_min,lat_max,lon_min,lon_max"]
        for i, f in enumerate(frames):
            ts = f["ts"]
            fn = f"frame_{i:02d}_{ts}.png"
            b = f["bounds"]
            lines.append(
                f"{i},{ts},{fn},"
                f"{b['lat_min']:.4f},{b['lat_max']:.4f},"
                f"{b['lon_min']:.4f},{b['lon_max']:.4f}"
            )
            # PNG sin overlay (mas util para reanalisis en QGIS/python)
            img_buf = io.BytesIO()
            PILImage.fromarray(f["image"]).save(img_buf, format="PNG")
            zf.writestr(fn, img_buf.getvalue())
        zf.writestr("manifest.csv", "\n".join(lines))
        # README breve
        readme = (
            f"GOES-19 animation export\n"
            f"========================\n"
            f"Product : {product_label}\n"
            f"Scope   : {scope_label}\n"
            f"Frames  : {len(frames)}\n"
            f"Span    : {frames[0]['ts']} -> {frames[-1]['ts']} (UTC)\n\n"
            f"Source: RAMMB/CIRA Slider (slider.cira.colostate.edu)\n"
            f"Each PNG es la imagen reprojectada a lat/lon regular.\n"
            f"Bounds geograficos por frame en manifest.csv.\n"
        )
        zf.writestr("README.txt", readme)
    return buf.getvalue()


def _volcano_scatter(bounds: dict, highlight=None) -> go.Scatter:
    """Scatter de volcanes visibles dentro de los bounds."""
    vis = [v for v in get_priority()
           if bounds["lat_min"] <= v.lat <= bounds["lat_max"]
           and bounds["lon_min"] <= v.lon <= bounds["lon_max"]]
    if not vis:
        vis = [v for v in CATALOG
               if bounds["lat_min"] <= v.lat <= bounds["lat_max"]
               and bounds["lon_min"] <= v.lon <= bounds["lon_max"]][:20]
    if not vis:
        return None
    return go.Scatter(
        x=[v.lon for v in vis], y=[v.lat for v in vis],
        mode="markers+text",
        marker=dict(size=4, color=C_ACCENT, symbol="triangle-up",
                    line=dict(width=0.6, color="white")),
        text=[v.name for v in vis],
        textposition="top center",
        textfont=dict(size=7, color="rgba(255,255,255,0.8)"),
        name="Volcanes",
        hovertext=[f"<b>{v.name}</b><br>{v.elevation:,} m" for v in vis],
        hoverinfo="text", showlegend=False,
    )


@st.cache_data(ttl=3600, show_spinner=False)
def _wind_for_volcano(lat: float, lon: float) -> dict[str, dict]:
    """Viento GFS en 3 niveles para el centro del volcan. Cache 1h."""
    out = {}
    for level_id in ("300hPa", "500hPa", "850hPa"):
        w = fetch_wind_point(lat, lon, level=level_id)
        if w is not None:
            out[level_id] = w
    return out


def _wind_arrow_traces(center_lat: float, center_lon: float,
                        wind_data: dict, bounds: dict) -> list:
    """Crea traces de viento para overlayar en una animacion estatica.

    Las flechas se renderizan UNA vez (no cambian con los frames porque
    GFS se actualiza cada 6h y la animacion suele ser <3h).
    """
    if not wind_data:
        return []
    LEVEL_VIZ = [
        ("300hPa", "300 hPa", "#ff4444"),
        ("500hPa", "500 hPa", "#ffaa44"),
        ("850hPa", "850 hPa", "#44dd88"),
    ]
    traces = []
    # Escala: longitud proporcional a la velocidad (saturada en 100 km/h)
    bbox_w = bounds["lon_max"] - bounds["lon_min"]
    arrow_len_deg = bbox_w * 0.18
    cos_lat = max(0.1, float(np.cos(np.radians(center_lat))))
    for level_id, label, color in LEVEL_VIZ:
        w = wind_data.get(level_id)
        if w is None:
            continue
        speed = float(np.hypot(w["u"], w["v"]))
        if speed < 1e-3:
            continue
        ux = w["u"] / speed
        vy = w["v"] / speed
        scale = arrow_len_deg * min(speed / 50.0, 2.0)
        lon_end = center_lon + ux * scale / cos_lat
        lat_end = center_lat + vy * scale
        # Linea cuerpo
        traces.append(go.Scatter(
            x=[center_lon, lon_end], y=[center_lat, lat_end],
            mode="lines",
            line=dict(color=color, width=3),
            name=f"{label} {speed:.0f} km/h",
            hovertemplate=(
                f"<b>{label}</b><br>"
                f"{w['speed']:.0f} km/h desde {w['direction']:.0f}°<extra></extra>"
            ),
        ))
        # Punta
        traces.append(go.Scatter(
            x=[lon_end], y=[lat_end], mode="markers",
            marker=dict(symbol="arrow", size=14, color=color,
                        angle=float(np.degrees(np.arctan2(w["u"], w["v"]))),
                        line=dict(color="white", width=1)),
            hoverinfo="skip", showlegend=False,
        ))
    return traces


def _build_animation(frames: list[dict], bounds: dict, height: int = 700,
                      wind_data: dict | None = None,
                      wind_center: tuple[float, float] | None = None) -> go.Figure:
    """Construir figura Plotly animada con los frames (mas antiguo -> mas reciente).

    Si se pasa wind_data + wind_center, agrega flechas de viento (300/500/850 hPa)
    como traces estaticos visibles en todos los frames de la animacion.
    """
    lat_min = bounds["lat_min"]
    lat_max = bounds["lat_max"]
    lon_min = bounds["lon_min"]
    lon_max = bounds["lon_max"]

    volc_scatter = _volcano_scatter(bounds)
    base_traces = [
        go.Scatter(x=[lon_min, lon_max], y=[lat_min, lat_max],
                   mode="markers", marker=dict(opacity=0),
                   showlegend=False, hoverinfo="skip"),
    ]
    if volc_scatter is not None:
        base_traces.append(volc_scatter)
    # Viento overlay (estatico — visible en todos los frames)
    if wind_data and wind_center:
        base_traces.extend(_wind_arrow_traces(
            wind_center[0], wind_center[1], wind_data, bounds,
        ))

    plotly_frames = []
    for i, f in enumerate(frames):
        b64 = _img_to_b64(f["image"])
        plotly_frames.append(go.Frame(
            data=base_traces,
            layout=go.Layout(
                images=[dict(
                    source=f"data:image/png;base64,{b64}",
                    xref="x", yref="y",
                    x=lon_min, y=lat_max,
                    xanchor="left", yanchor="top",
                    sizex=lon_max - lon_min,
                    sizey=lat_max - lat_min,
                    sizing="stretch", layer="below",
                )],
                title_text=f["label"],
            ),
            name=str(i),
        ))

    b64_first = _img_to_b64(frames[0]["image"])
    # Slider steps: mostrar HH:MM UTC y CLT
    slider_steps = []
    for i, f in enumerate(frames):
        dt = parse_rammb_ts(f["ts"])
        slider_steps.append(dict(
            method="animate",
            args=[[str(i)], dict(
                frame=dict(duration=0, redraw=True),
                mode="immediate", transition=dict(duration=0),
            )],
            label=dt.strftime("%H:%M"),
        ))

    fig = go.Figure(
        data=base_traces,
        layout=go.Layout(
            images=[dict(
                source=f"data:image/png;base64,{b64_first}",
                xref="x", yref="y",
                x=lon_min, y=lat_max,
                xanchor="left", yanchor="top",
                sizex=lon_max - lon_min,
                sizey=lat_max - lat_min,
                sizing="stretch", layer="below",
            )],
            title=dict(text=frames[0]["label"], font=dict(size=13, color="#ccc")),
            xaxis_title="Longitud", yaxis_title="Latitud",
            yaxis=dict(scaleanchor="x", scaleratio=1,
                       range=[lat_min, lat_max]),
            xaxis=dict(range=[lon_min, lon_max]),
            height=height,
            template="plotly_dark",
            margin=dict(t=55, b=75, l=50, r=20),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            updatemenus=[dict(
                type="buttons", showactive=False,
                y=0, x=0.5, xanchor="center", yanchor="top",
                pad=dict(t=10),
                buttons=[
                    dict(label="▶ Play", method="animate",
                         args=[None, dict(
                             frame=dict(duration=800, redraw=True),
                             fromcurrent=True, transition=dict(duration=0),
                         )]),
                    dict(label="⏸ Pausa", method="animate",
                         args=[[None], dict(
                             frame=dict(duration=0, redraw=False),
                             mode="immediate", transition=dict(duration=0),
                         )]),
                ],
            )],
            sliders=[dict(
                active=0,
                currentvalue=dict(prefix="UTC: ",
                                  font=dict(size=11, color="#aaa")),
                pad=dict(t=50, b=10),
                steps=slider_steps,
            )],
        ),
        frames=plotly_frames,
    )
    return fig


# Versión de reproyección — cambiar si se modifica cfac/bounds para invalidar caché
# v3 (2026-05-01): fix sat_lon GOES-19 -75.2 -> -75.0 (offset ~17 km al sur).
_REPROJECT_VERSION = "v3"


# ── Cache + delta-fetch helper ────────────────────────────────────────────
# Combina frames pre-bajados por el GH Action (release `animations-rolling`)
# con los ultimos N que el cron todavia no pesco. Reduce latencia de 60-120s
# a ~10s para los scopes pre-bajados (Nacional, 4 zonas, 8 prioritarios).
# Si no hay manifest o el scope no esta cacheado, devuelve None y el llamador
# debe caer al flujo on-demand puro.

@st.cache_data(ttl=300, show_spinner=False)
def _fetch_via_cache(scope_id: str, product: str, n_frames: int,
                     _v: str = _REPROJECT_VERSION) -> list[dict] | None:
    """Bajar N frames combinando cache de release + delta de RAMMB.

    1. Lee manifest del release.
    2. Pide latest N timestamps a RAMMB.
    3. Descarga del CDN los que estan cacheados (rapido, paralelo).
    4. Devuelve lista de (ts, image_array). Los faltantes se delegan al
       caller para que use el fetcher on-demand especifico (que ya conoce
       bounds/zoom/reproyeccion correctos para el scope).

    Devuelve estructura: {"cached": {ts: arr}, "missing": [ts, ...],
                          "all_ts": [ts, ...]}
    o None si el scope no esta en el cache (caer a flujo legacy).
    """
    # Lazy import (gotcha Streamlit Cloud — ver CLAUDE.md).
    from src.fetch.animation_cache import fetch_cached_frames, fetch_manifest
    manifest = fetch_manifest()
    if manifest is None:
        return None
    cached_ts_list = manifest.get("scopes", {}).get(scope_id, {}).get(product, [])
    if not cached_ts_list:
        return None
    cached_set = set(cached_ts_list)

    latest = get_latest_timestamps(product, n=n_frames)
    if not latest:
        return None

    to_fetch_from_cache = [ts for ts in latest if ts in cached_set]
    missing = [ts for ts in latest if ts not in cached_set]

    cached_frames = fetch_cached_frames(scope_id, product, to_fetch_from_cache)
    return {"cached": cached_frames, "missing": missing, "all_ts": sorted(latest)}


def _assemble_frames(cache_result: dict, missing_loader,
                     bounds_for_label: dict) -> list[dict]:
    """Une frames cacheados + frames bajados on-demand en lista ordenada.

    `missing_loader(ts) -> np.ndarray | None` baja un frame nuevo de RAMMB
    con los bounds/zoom apropiados para el scope.
    """
    out: list[dict] = []
    cached = cache_result["cached"]
    for ts in cache_result["all_ts"]:
        if ts in cached:
            arr = cached[ts]
        else:
            arr = missing_loader(ts)
            if arr is None:
                continue
        out.append({
            "ts": ts,
            "label": _frame_label(ts),
            "image": arr,
            "bounds": bounds_for_label,
        })
    return out


@st.cache_data(ttl=600, show_spinner=False)
def _fetch_chile_frames(product: str, n_frames: int,
                        _v: str = _REPROJECT_VERSION) -> list[dict]:
    """Animacion Chile completo (zoom=2 reprojectado).

    Intenta cache + delta primero; si no hay cache cae al flujo completo.
    """
    sid = scope_id_nacional()
    cache_result = _fetch_via_cache(sid, product, n_frames)
    if cache_result is not None:
        def _on_demand(ts: str):
            img = fetch_frame_for_bounds(
                product, ts, CHILE_REPROJECTED_BOUNDS, zoom=2,
            )
            # fetch_frame_for_bounds ya reproyecta → no aplicar de nuevo.
            return img
        frames = _assemble_frames(cache_result, _on_demand, CHILE_REPROJECTED_BOUNDS)
        if frames:
            return frames
        # cache vacio raro -> caer abajo

    # Flujo legacy (sin cache)
    frames = fetch_animation_frames(
        product=product, n_frames=n_frames, zoom=2,
        tile_rows=CHILE_TILES_Z2["rows"], tile_cols=CHILE_TILES_Z2["cols"],
    )
    for f in frames:
        f["image"] = reproject_to_latlon(f["image"], col_start=678, row_start=1356)
        f["bounds"] = CHILE_REPROJECTED_BOUNDS
        f["label"] = _frame_label(f["ts"])
    return frames


def _scope_id_from_bounds_key(bounds_key: str) -> str | None:
    """Mapear bounds_key del viewer a scope_id del cache.

    Convencion: el viewer pasa "z:<zone>" para zona, "v:<volcan>" para volcan
    a zoom 4, "vz3:<volcan>" para volcan con fallback a zoom 3. Solo los
    primeros dos formatos tienen cache pre-bajado (zona y volcan@zoom4).
    """
    # Lazy import (gotcha Streamlit Cloud — ver CLAUDE.md).
    from src.fetch.animation_cache import scope_id_volcan, scope_id_zona
    if bounds_key.startswith("z:"):
        return scope_id_zona(bounds_key[2:])
    if bounds_key.startswith("v:"):
        return scope_id_volcan(bounds_key[2:])
    # vz3: y otros -> sin cache
    return None


@st.cache_data(ttl=600, show_spinner=False)
def _fetch_bounds_frames(product: str, n_frames: int, zoom: int,
                         bounds_key: str, bounds_tuple: tuple,
                         _v: str = _REPROJECT_VERSION) -> list[dict]:
    """Animacion generica para un bbox arbitrario (zona o volcan).

    bounds_key/bounds_tuple son redundantes solo para hacer la key hashable.
    Si el scope esta pre-bajado, usa cache + delta-fetch (rapido). Si no,
    cae al flujo on-demand puro.
    """
    bounds = {
        "lat_min": bounds_tuple[0], "lat_max": bounds_tuple[1],
        "lon_min": bounds_tuple[2], "lon_max": bounds_tuple[3],
    }

    # Intento cache + delta
    scope_id = _scope_id_from_bounds_key(bounds_key)
    if scope_id is not None:
        cache_result = _fetch_via_cache(scope_id, product, n_frames)
        if cache_result is not None:
            def _on_demand(ts: str):
                return fetch_frame_for_bounds(product, ts, bounds, zoom=zoom)
            frames = _assemble_frames(cache_result, _on_demand, bounds)
            if frames:
                return frames

    # Flujo legacy: descarga paralela de todos los frames.
    timestamps = get_latest_timestamps(product, n=n_frames)
    if not timestamps:
        return []

    def _one(ts):
        img = fetch_frame_for_bounds(product, ts, bounds, zoom=zoom)
        return ts, img

    out = []
    with ThreadPoolExecutor(max_workers=6) as ex:
        results = list(ex.map(_one, timestamps))
    for ts, img in results:
        if img is None:
            continue
        out.append({
            "ts": ts,
            "label": _frame_label(ts),
            "image": img,
            "bounds": bounds,
        })
    out.sort(key=lambda f: f["ts"])
    return out


@st.cache_data(ttl=300, show_spinner=False)
def _fetch_latest_ts_label(product: str) -> str:
    times = get_latest_timestamps(product, n=1)
    return _frame_label(times[0]) if times else "—"


def render():
    header(
        "Animacion RAMMB/CIRA — GOES-19",
        "Loops de los ultimos scans &middot; Nacional, por zona o por volcan",
    )
    refresh_info_badge(context="animation")

    # ── Controles (compactado: 1 fila con Producto + Duracion + Cobertura + Boton) ─
    # Wind overlay toggle — fuera del session_state de fetch para que cambiar
    # el toggle solo redibuje la figura sin re-bajar frames.
    wind_col, _spacer = st.columns([1, 5])
    with wind_col:
        show_wind = st.toggle(
            "💨 Viento overlay (GFS)",
            value=False, key="anim_wind_overlay",
            help="Vectores GFS 300/500/850 hPa sobre el centro del bbox. "
                 "Util para predecir hacia donde irá la pluma. "
                 "Cache 1h (GFS publica c/6h).",
        )
    c1, c2, c3, c4 = st.columns([1.2, 1.2, 1.8, 0.95])
    with c1:
        product = st.selectbox(
            "Producto",
            options=list(PRODUCT_LABELS.keys()),
            format_func=lambda k: PRODUCT_LABELS[k],
            index=0, key="rammb_product",
        )
    with c2:
        duration_label = st.selectbox(
            "Duracion",
            options=list(FRAME_OPTIONS.keys()),
            index=1, key="rammb_duration",
        )
    with c3:
        scope = st.radio(
            "Cobertura",
            ["Nacional (Chile)", "Por zona volcanica", "Por volcan"],
            index=0, horizontal=True, key="anim_scope",
        )
    with c4:
        st.markdown("<div style='height:1.2rem'></div>", unsafe_allow_html=True)
        fetch_btn = st.button("Cargar animacion", type="primary",
                              use_container_width=True)

    zone_key = None
    volc_name = None
    radius = VOLCANO_RADIUS_DEG

    if scope == "Por zona volcanica":
        zone_key = st.selectbox(
            "Zona",
            list(ZONE_LABELS.keys()),
            format_func=lambda k: ZONE_LABELS[k],
            index=2, key="anim_zone",
        )
    elif scope == "Por volcan":
        cv1, cv2 = st.columns([2, 1])
        with cv1:
            priority_names = [v.name for v in CATALOG if v.name in PRIORITY_VOLCANOES]
            other_names    = [v.name for v in CATALOG if v.name not in priority_names]
            volc_options   = [f"★ {n}" for n in priority_names] + other_names
            sel_raw = st.selectbox("Volcan", volc_options, index=0, key="anim_volc")
            volc_name = sel_raw.replace("★ ", "")
        with cv2:
            radius = st.slider("Radio (°)", 0.5, 3.0, VOLCANO_RADIUS_DEG, 0.5,
                               key="anim_radius")

    n_frames = FRAME_OPTIONS[duration_label]
    latest_ts_label = _fetch_latest_ts_label(product)

    # ── Info panel inicial ────────────────────────────────────────────────
    if not fetch_btn and "anim_frames" not in st.session_state:
        col_info, col_ts = st.columns([2, 1])
        with col_info:
            info_panel(
                "<b>Animacion de pulsos eruptivos</b><br><br>"
                "Descarga los ultimos N scans de GOES-19 y los muestra como loop.<br>"
                "Eleginado <b>Cobertura</b> podes ver todo Chile, una zona volcanica "
                "especifica, o hacer zoom a un volcan individual.<br><br>"
                "<b>GeoColor</b>: color real mejorado (solo dia).<br>"
                "<b>Ash RGB</b>: deteccion de ceniza (dia y noche). Ceniza = rojo/magenta.<br>"
                "<b>SO2</b>: dioxido de azufre = verde brillante.<br>"
                "<b>BTD</b>: diferencia termica split-window, mas sensible a ceniza fina."
                "<br><br>"
                "<b>&#9889; Como funciona la velocidad</b><br>"
                "Un proceso automatico (GitHub Actions) corre cada hora y pre-descarga "
                "los ultimos 12h de frames para los escopos mas usados "
                "(Nacional, las 4 zonas, y los 8 volcanes prioritarios marcados con &#9733;). "
                "Cuando pedis una animacion de esos escopos, el dashboard usa esos frames "
                "cacheados y solo baja de RAMMB los <b>ultimos ~6 frames</b> que el cron "
                "todavia no pesco (los del ultima hora). Resultado: <b>~10 segundos</b> "
                "en vez de 60-120s, y siempre con los frames mas recientes incluidos.<br>"
                "Para volcanes no prioritarios o radios distintos del default, se baja "
                "todo on-demand (lento, ~60-120s)."
            )
        with col_ts:
            st.markdown(
                f'<div class="legend-container">'
                f'<div class="legend-title">Ultima imagen disponible</div>'
                f'<div style="font-size:0.8rem; color:#99aabb; margin-top:0.4rem;">'
                f'<b>{PRODUCT_LABELS[product]}</b><br>'
                f'<span style="font-size:0.78rem;">{latest_ts_label}</span>'
                f'</div></div>',
                unsafe_allow_html=True,
            )
        return

    # ── Guardar seleccion en session_state al presionar el boton ──────────
    if fetch_btn:
        st.session_state["anim_frames"] = True
        st.session_state["anim_sel"] = dict(
            product=product, n=n_frames, scope=scope,
            zone=zone_key, volc=volc_name, radius=radius,
        )

    sel = st.session_state.get("anim_sel", dict(
        product=product, n=n_frames, scope=scope,
        zone=zone_key, volc=volc_name, radius=radius,
    ))

    # ── Determinar bounds + zoom segun scope ──────────────────────────────
    scope_sel = sel["scope"]
    scope_label = ""
    height = 700
    try:
        if scope_sel == "Nacional (Chile)":
            with st.spinner(f"Descargando {sel['n']} scans nacionales..."):
                frames = _fetch_chile_frames(sel["product"], sel["n"])
            scope_label = "Chile completo"
            height = 700
        elif scope_sel == "Por zona volcanica":
            zk = sel["zone"] or "sur"
            zb = VOLCANIC_ZONES[zk]
            bt = (zb["lat_min"], zb["lat_max"], zb["lon_min"], zb["lon_max"])
            with st.spinner(f"Descargando {sel['n']} scans de {ZONE_LABELS[zk]}..."):
                frames = _fetch_bounds_frames(
                    sel["product"], sel["n"], ZOOM_ZONE, f"z:{zk}", bt,
                )
            scope_label = ZONE_LABELS[zk]
            height = 640
        else:  # Por volcan
            vname = sel["volc"]
            v = get_volcano(vname) if vname else None
            if v is None:
                st.error(f"Volcan '{vname}' no encontrado.")
                return
            r = sel["radius"]
            vb = {
                "lat_min": v.lat - r, "lat_max": v.lat + r,
                "lon_min": v.lon - r, "lon_max": v.lon + r,
            }
            bt = (vb["lat_min"], vb["lat_max"], vb["lon_min"], vb["lon_max"])
            with st.spinner(f"Descargando {sel['n']} scans zoom para {v.name}..."):
                frames = _fetch_bounds_frames(
                    sel["product"], sel["n"], ZOOM_VOLCAN, f"v:{v.name}", bt,
                )
                if not frames:
                    # Fallback a zoom=3 si zoom=4 no esta disponible
                    frames = _fetch_bounds_frames(
                        sel["product"], sel["n"], ZOOM_ZONE, f"vz3:{v.name}", bt,
                    )
            scope_label = f"{v.name} (±{r}°)"
            height = 720
    except Exception as e:
        logger.exception("anim error")
        st.error(f"Error descargando: {e}")
        return

    if not frames:
        st.error("No se pudieron descargar frames. Verifica conexion o "
                 "prueba otro producto/scope.")
        return

    # ── KPIs (ahora con hora local ademas de UTC) ─────────────────────────
    dt_first = parse_rammb_ts(frames[0]["ts"])
    dt_last  = parse_rammb_ts(frames[-1]["ts"])
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        kpi_card(str(len(frames)), "Frames cargados")
    with k2:
        kpi_card(
            dt_first.strftime("%H:%M"),
            "Inicio",
            delta=fmt_chile(dt_first),
        )
    with k3:
        kpi_card(
            dt_last.strftime("%H:%M"),
            "Fin",
            delta=fmt_chile(dt_last),
        )
    with k4:
        kpi_card(f"{len(frames)*10} min", "Ventana")

    st.markdown("<div style='height:0.3rem'></div>", unsafe_allow_html=True)

    # Status banner con scope + hora UTC+CLT
    st.markdown(
        f'<div class="status-banner ok">'
        f'<b>&#10003; {len(frames)} frames &middot; '
        f'{PRODUCT_LABELS[sel["product"]]} &middot; {scope_label}</b>'
        f'<span style="color:#556677; font-size:0.78rem;">'
        f'{latest_ts_label}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div style="font-size:0.78rem; color:#556677; margin:0.3rem 0 0.5rem 0;">'
        'Controles: presioná <b>▶ Play</b> arriba a la izquierda del plot · '
        'slider inferior (UTC) para navegar frame por frame · '
        '<i>atajos de teclado pendientes — sesión dedicada futura</i> '
        '(refactor de la animación a Streamlit-state, ~300 LOC)</div>',
        unsafe_allow_html=True,
    )

    bounds = frames[0]["bounds"]
    # Si toggle viento esta on, fetch en el centro del bbox
    wind_data = None
    wind_center = None
    if st.session_state.get("anim_wind_overlay", False):
        cx = (bounds["lon_min"] + bounds["lon_max"]) / 2
        cy = (bounds["lat_min"] + bounds["lat_max"]) / 2
        wind_data = _wind_for_volcano(cy, cx)
        wind_center = (cy, cx)
    fig = _build_animation(frames, bounds, height=height,
                           wind_data=wind_data, wind_center=wind_center)
    st.plotly_chart(fig, use_container_width=True)

    # ── Descargas ─────────────────────────────────────────────────────────
    # Generamos los binarios solo on-demand (lazy) via expander para no
    # consumir CPU/memoria en cada rerun de Streamlit. Una animacion GIF de
    # 12 frames ~5-15 MB, un ZIP de PNGs originales ~10-30 MB.
    st.markdown(
        '<div style="height:0.4rem; border-top:1px solid rgba(100,120,140,0.15); '
        'margin-top:0.6rem; padding-top:0.4rem;"></div>',
        unsafe_allow_html=True,
    )
    with st.expander("⬇ Descargar animacion / frames", expanded=False):
        st.markdown(
            '<div style="font-size:0.78rem; color:#8899aa; margin-bottom:0.5rem;">'
            'Generar el archivo toma 5-20 s la primera vez (queda cacheado en sesion). '
            '<b>MP4 (H.264)</b>: video estandar, mejor calidad, ~3-5x mas chico que GIF, '
            'compatible con PowerPoint/navegadores. '
            '<b>GIF</b>: imagen animada, ideal para mail/Slack/PDF (loop infinito). '
            '<b>ZIP</b>: PNGs originales sin overlay + <code>manifest.csv</code> con bounds, '
            'pensado para reanalisis en QGIS o Python.'
            '</div>',
            unsafe_allow_html=True,
        )

        # Slug para el nombre de archivo (UTC del primer y ultimo frame)
        prod_slug = sel["product"].replace("_", "-")
        scope_slug = (
            scope_label.lower()
            .replace(" ", "-").replace("(", "").replace(")", "")
            .replace("±", "r").replace(",", "").replace("°", "deg")
            .replace("á", "a").replace("é", "e").replace("í", "i")
            .replace("ó", "o").replace("ú", "u").replace("ñ", "n")
        )
        ts_first = frames[0]["ts"][:12]
        ts_last  = frames[-1]["ts"][:12]
        base_name = f"goes19_{prod_slug}_{scope_slug}_{ts_first}_{ts_last}"

        # FPS selector compartido (afecta solo MP4; el GIF mantiene 700ms/frame).
        fps = st.slider(
            "FPS del video MP4 (frames por segundo)",
            min_value=1.0, max_value=8.0, value=1.5, step=0.5,
            key="anim_fps",
            help=(
                "Velocidad de reproduccion del MP4. 1.5 fps = cada scan "
                "(10 min reales) dura ~0.66s en el video. "
                "Subir a 4-6 fps para playback mas rapido."
            ),
        )

        col_m, col_g, col_z = st.columns(3)

        with col_m:
            st.markdown(
                '<div style="font-size:0.78rem; color:#c0ccd8; '
                'font-weight:700; margin-bottom:0.2rem;">MP4 (recomendado)</div>',
                unsafe_allow_html=True,
            )
            # Re-generar si cambia FPS — usamos fps en la session_state key
            if st.button("Generar MP4", key="gen_mp4",
                         use_container_width=True):
                with st.spinner("Construyendo MP4 (H.264)..."):
                    mp4_bytes = _build_mp4(frames, fps=fps)
                    if mp4_bytes:
                        st.session_state["_mp4_bytes"] = mp4_bytes
                        st.session_state["_mp4_name"] = (
                            f"{base_name}_{fps:.1f}fps.mp4"
                        )
                    else:
                        st.error(
                            "No se pudo generar MP4. Si esto pasa en Streamlit "
                            "Cloud, revisar que imageio-ffmpeg este instalado. "
                            "Mientras tanto podes usar el GIF."
                        )
            if "_mp4_bytes" in st.session_state and st.session_state["_mp4_bytes"]:
                size_mb = len(st.session_state["_mp4_bytes"]) / 1024 / 1024
                st.download_button(
                    f"⬇ {st.session_state['_mp4_name']} ({size_mb:.1f} MB)",
                    data=st.session_state["_mp4_bytes"],
                    file_name=st.session_state["_mp4_name"],
                    mime="video/mp4",
                    key="dl_mp4",
                    use_container_width=True,
                )

        with col_g:
            st.markdown(
                '<div style="font-size:0.78rem; color:#c0ccd8; '
                'font-weight:700; margin-bottom:0.2rem;">GIF</div>',
                unsafe_allow_html=True,
            )
            if st.button("Generar GIF", key="gen_gif",
                         use_container_width=True):
                with st.spinner("Construyendo GIF..."):
                    st.session_state["_gif_bytes"] = _build_gif(frames)
                    st.session_state["_gif_name"] = f"{base_name}.gif"
            if "_gif_bytes" in st.session_state and st.session_state["_gif_bytes"]:
                size_mb = len(st.session_state["_gif_bytes"]) / 1024 / 1024
                st.download_button(
                    f"⬇ {st.session_state['_gif_name']} ({size_mb:.1f} MB)",
                    data=st.session_state["_gif_bytes"],
                    file_name=st.session_state["_gif_name"],
                    mime="image/gif",
                    key="dl_gif",
                    use_container_width=True,
                )

        with col_z:
            st.markdown(
                '<div style="font-size:0.78rem; color:#c0ccd8; '
                'font-weight:700; margin-bottom:0.2rem;">ZIP de frames</div>',
                unsafe_allow_html=True,
            )
            if st.button("Generar ZIP", key="gen_zip",
                         use_container_width=True):
                with st.spinner("Construyendo ZIP..."):
                    st.session_state["_zip_bytes"] = _build_zip_frames(
                        frames, PRODUCT_LABELS[sel["product"]], scope_label,
                    )
                    st.session_state["_zip_name"] = f"{base_name}.zip"
            if "_zip_bytes" in st.session_state and st.session_state["_zip_bytes"]:
                size_mb = len(st.session_state["_zip_bytes"]) / 1024 / 1024
                st.download_button(
                    f"⬇ {st.session_state['_zip_name']} ({size_mb:.1f} MB)",
                    data=st.session_state["_zip_bytes"],
                    file_name=st.session_state["_zip_name"],
                    mime="application/zip",
                    key="dl_zip",
                    use_container_width=True,
                )

        st.markdown(
            '<div style="font-size:0.72rem; color:#667788; line-height:1.5; '
            'margin-top:0.5rem; border-top:1px solid rgba(100,120,140,0.15); '
            'padding-top:0.4rem;">'
            f'<b>{len(frames)} frames</b> &middot; '
            f'{PRODUCT_LABELS[sel["product"]]} &middot; '
            f'<b>Scope:</b> {scope_label} &middot; '
            f'<b>UTC:</b> {ts_first} → {ts_last}'
            '</div>',
            unsafe_allow_html=True,
        )

    st.markdown(
        '<div style="font-size:0.72rem; color:#445566; margin-top:0.5rem;">'
        'Tiles de <a href="https://slider.cira.colostate.edu/?sat=goes-19&sec=full_disk" '
        'target="_blank" style="color:#667788;">RAMMB/CIRA Slider</a> '
        '(Colorado State University).'
        '</div>',
        unsafe_allow_html=True,
    )
