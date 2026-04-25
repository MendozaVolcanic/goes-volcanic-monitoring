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


def _build_animation(frames: list[dict], bounds: dict, height: int = 700) -> go.Figure:
    """Construir figura Plotly animada con los frames (mas antiguo -> mas reciente)."""
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
_REPROJECT_VERSION = "v2"


@st.cache_data(ttl=600, show_spinner=False)
def _fetch_chile_frames(product: str, n_frames: int,
                        _v: str = _REPROJECT_VERSION) -> list[dict]:
    """Animacion Chile completo (zoom=2 reprojectado)."""
    frames = fetch_animation_frames(
        product=product, n_frames=n_frames, zoom=2,
        tile_rows=CHILE_TILES_Z2["rows"], tile_cols=CHILE_TILES_Z2["cols"],
    )
    for f in frames:
        f["image"] = reproject_to_latlon(f["image"], col_start=678, row_start=1356)
        f["bounds"] = CHILE_REPROJECTED_BOUNDS
        f["label"] = _frame_label(f["ts"])
    return frames


@st.cache_data(ttl=600, show_spinner=False)
def _fetch_bounds_frames(product: str, n_frames: int, zoom: int,
                         bounds_key: str, bounds_tuple: tuple,
                         _v: str = _REPROJECT_VERSION) -> list[dict]:
    """Animacion generica para un bbox arbitrario (zona o volcan).

    bounds_key/bounds_tuple son redundantes solo para hacer la key hashable.
    """
    bounds = {
        "lat_min": bounds_tuple[0], "lat_max": bounds_tuple[1],
        "lon_min": bounds_tuple[2], "lon_max": bounds_tuple[3],
    }
    timestamps = get_latest_timestamps(product, n=n_frames)
    if not timestamps:
        return []
    # Descarga paralela de los N frames (cada uno stitchea varios tiles).
    # Speedup ~N/4 para N frames, limitado por max_workers.
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
    # Mas antiguo -> mas reciente
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

    # ── Controles ─────────────────────────────────────────────────────────
    c1, c2, c3 = st.columns([1.5, 1.2, 1])
    with c1:
        product = st.selectbox(
            "Producto",
            options=list(PRODUCT_LABELS.keys()),
            format_func=lambda k: PRODUCT_LABELS[k],
            index=0, key="rammb_product",
        )
    with c2:
        duration_label = st.selectbox(
            "Duracion del loop",
            options=list(FRAME_OPTIONS.keys()),
            index=1, key="rammb_duration",
        )
    with c3:
        st.markdown("<div style='height:1.6rem'></div>", unsafe_allow_html=True)
        fetch_btn = st.button("Cargar animacion", type="primary",
                              use_container_width=True)

    # Scope selector (Nacional / Zona / Volcan)
    scope = st.radio(
        "Cobertura",
        ["Nacional (Chile)", "Por zona volcanica", "Por volcan"],
        index=0, horizontal=True, key="anim_scope",
    )

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
                    sel["product"], sel["n"], ZOOM_ZONE, zk, bt,
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
        'Presiona <b>▶ Play</b> para ver la animacion. Slider inferior '
        '(UTC) navega frame a frame. Cada etiqueta del titulo muestra UTC + hora Chile.'
        '</div>',
        unsafe_allow_html=True,
    )

    bounds = frames[0]["bounds"]
    fig = _build_animation(frames, bounds, height=height)
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
            'Generar el archivo toma 5-15 s la primera vez (queda cacheado en sesion). '
            '<b>GIF</b>: animacion con timestamp impreso, ideal para reportes/PDF. '
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

        col_g, col_z, col_info = st.columns([1, 1, 1.5])

        with col_g:
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
            if st.button("Generar ZIP de frames", key="gen_zip",
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

        with col_info:
            st.markdown(
                '<div style="font-size:0.72rem; color:#667788; line-height:1.5; '
                'padding-top:0.3rem;">'
                f'<b>{len(frames)} frames</b> &middot; '
                f'{PRODUCT_LABELS[sel["product"]]}<br>'
                f'<b>Scope:</b> {scope_label}<br>'
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
