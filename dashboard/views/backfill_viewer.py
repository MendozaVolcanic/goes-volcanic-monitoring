"""Backfill historico — visualizacion de eventos pasados con todos los productos.

Lee de un GitHub Release `backfill-<DATE>-<VOLCAN>` generado por
`scripts/build_backfill.py`. Cada release contiene PNGs por
(timestamp, producto, scope) + manifest.json.

Caso de uso: revisar Lascar 8-feb-2026 entre 10:36 y 19:00 UTC con
GeoColor, Ash RGB, SO2, BTD, hotspots y VOLCAT en grilla por timestamp.

Para crear un nuevo backfill: correr el script localmente (~5 min) o
via GitHub Action workflow_dispatch, y subir el contenido de
`out_backfill/` al release con tag `backfill-<DATE>-<VOLCAN>`.
"""

from __future__ import annotations

import io
import json
import logging
from datetime import datetime
from typing import Optional

import numpy as np
import plotly.graph_objects as go
import requests
import streamlit as st
from PIL import Image

try:
    from dashboard.style import header
except Exception:
    # Streamlit Cloud hot-reload race condition: retry import dentro de funciones.
    # Si esto se ejecuta, hay un bug — log y reraise para que Streamlit muestre el error.
    import logging as _logging
    _logging.exception("Cross-package import fallo top-level — gotcha Streamlit Cloud")
    raise

logger = logging.getLogger(__name__)

# Lista de releases disponibles. Para agregar uno nuevo, sumar tag al dict.
# El default abajo apunta al primer test (Lascar 8-feb-2026).
AVAILABLE_BACKFILLS = {
    "Villarrica 7-jun-2026 (07:30-10:30 UTC) — pulso": "backfill-2026-06-07-villarrica",
    "Lascar 8-feb-2026 (10:36-19:00 UTC)": "backfill-2026-02-08-lascar",
}

CDN_OWNER = "MendozaVolcanic"
CDN_REPO = "goes-volcanic-monitoring"

PRODUCT_LABELS = {
    "geocolor": "GeoColor",
    "eumetsat_ash": "Ash RGB",
    "jma_so2": "SO2 RGB",
    "split_window_difference_10_3-12_3": "BTD (split-window)",
    "volcat": "VOLCAT (SSEC)",
}

# Tabla de info por producto — lo que el usuario puede esperar ver
PRODUCT_INFO = {
    "geocolor": "Color real mejorado. Solo dia. Util para ver pluma visible y contexto.",
    "eumetsat_ash": "Detecta ceniza. Pluma de ceniza = rojo/magenta. Dia y noche.",
    "jma_so2": "Pluma de SO2 = verde brillante. Indica desgasificacion fresca.",
    "split_window_difference_10_3-12_3": "Diferencia termica BT11-BT12. Negativo = ceniza fina (Prata 1989).",
    "volcat": "Producto NOAA/SSEC con altura de pluma cuantitativa (km AMSL).",
}


def _release_url(tag: str, asset: str) -> str:
    return (f"https://github.com/{CDN_OWNER}/{CDN_REPO}"
            f"/releases/download/{tag}/{asset}")


@st.cache_data(ttl=3600, show_spinner=False)
def _fetch_manifest(tag: str) -> dict | None:
    try:
        r = requests.get(_release_url(tag, "manifest.json"), timeout=15)
        if r.status_code != 200:
            return None
        return r.json()
    except Exception as e:
        logger.warning("manifest %s: %s", tag, e)
        return None


@st.cache_data(ttl=3600, show_spinner=False)
def _fetch_hotspots_json(tag: str, asset: str) -> list[dict]:
    """Bajar JSON de hotspots de un (scope, ts). Devuelve lista de dicts."""
    try:
        r = requests.get(_release_url(tag, asset), timeout=10)
        if r.status_code != 200:
            return []
        data = r.json()
        return data.get("hotspots", [])
    except Exception as e:
        logger.warning("hotspots json %s: %s", asset, e)
        return []


@st.cache_data(ttl=3600, show_spinner=False)
def _fetch_png(tag: str, asset: str, keep_alpha: bool = False) -> np.ndarray | None:
    try:
        r = requests.get(_release_url(tag, asset), timeout=20)
        if r.status_code != 200:
            return None
        img = Image.open(io.BytesIO(r.content))
        mode = "RGBA" if keep_alpha else "RGB"
        img = img.convert(mode)
        return np.array(img)
    except Exception as e:
        logger.warning("png %s: %s", asset, e)
        return None


def _composite_volcat(volcat_rgba: np.ndarray | None,
                      base_rgb: np.ndarray | None) -> np.ndarray | None:
    """Componer VOLCAT (RGBA con transparencia) sobre GeoColor.

    Si no hay base, devuelve VOLCAT con bg gris para que no salga negro.
    Si VOLCAT es None, devuelve base.
    """
    if volcat_rgba is None:
        return base_rgb
    if volcat_rgba.shape[-1] != 4:
        return volcat_rgba  # ya es RGB
    if base_rgb is None:
        # Fallback: bg gris oscuro tipo mapa de noche
        h, w = volcat_rgba.shape[:2]
        base_rgb = np.full((h, w, 3), 30, dtype=np.uint8)
    # Resize base si shape difiere
    if base_rgb.shape[:2] != volcat_rgba.shape[:2]:
        from PIL import Image as PILImage
        base_pil = PILImage.fromarray(base_rgb).resize(
            (volcat_rgba.shape[1], volcat_rgba.shape[0]), PILImage.LANCZOS,
        )
        base_rgb = np.array(base_pil)
    # Alpha composite
    alpha = volcat_rgba[..., 3:4].astype(np.float32) / 255.0
    fg = volcat_rgba[..., :3].astype(np.float32)
    bg = base_rgb.astype(np.float32)
    out = (fg * alpha + bg * (1 - alpha)).astype(np.uint8)
    return out


def _array_to_data_url(arr):
    # Lazy import (gotcha Streamlit Cloud — ver CLAUDE.md).
    from dashboard.map_helpers import array_to_data_url
    return array_to_data_url(arr)



def _ts_to_label(ts: str) -> str:
    """'20260208104021' -> '2026-02-08 10:40:21 UTC'."""
    try:
        dt = datetime.strptime(ts, "%Y%m%d%H%M%S")
        return dt.strftime("%Y-%m-%d %H:%M:%S UTC")
    except Exception:
        return ts


def _add_hotspots_overlay(fig: go.Figure, hotspots: list[dict]) -> None:
    """Agregar marcadores diamante rojos por hotspot. Tamaño por FRP."""
    if not hotspots:
        return
    lats = [h["lat"] for h in hotspots]
    lons = [h["lon"] for h in hotspots]
    sizes = [float(8 + min(16, np.sqrt(max(0.0, h.get("frp_mw", 0))) * 1.6))
             for h in hotspots]
    labels = [f"{h.get('temp_k', 0):.0f}K · FRP {h.get('frp_mw', 0):.1f}MW "
              f"({h.get('confidence', '?')})" for h in hotspots]
    fig.add_trace(go.Scatter(
        x=lons, y=lats, mode="markers",
        marker=dict(symbol="diamond", size=sizes, color="#ff3300",
                    line=dict(color="white", width=1)),
        text=labels, hoverinfo="text", showlegend=False,
        name=f"Hot spots ({len(hotspots)})",
    ))


def _render_product_panel(arr: np.ndarray | None, bounds: dict,
                           label: str, height: int = 360,
                           hotspots: list[dict] | None = None) -> go.Figure:
    fig = go.Figure()
    if arr is not None:
        fig.add_layout_image(
            source=_array_to_data_url(arr),
            xref="x", yref="y",
            x=bounds["lon_min"], y=bounds["lat_max"],
            sizex=bounds["lon_max"] - bounds["lon_min"],
            sizey=bounds["lat_max"] - bounds["lat_min"],
            sizing="stretch", layer="below",
        )
    cos_lat = max(0.1, float(np.cos(np.radians(
        (bounds["lat_min"] + bounds["lat_max"]) / 2
    ))))
    fig.update_xaxes(range=[bounds["lon_min"], bounds["lon_max"]],
                     showgrid=False, visible=False)
    fig.update_yaxes(range=[bounds["lat_min"], bounds["lat_max"]],
                     showgrid=False, visible=False,
                     scaleanchor="x", scaleratio=1.0 / cos_lat)
    # Title como overlay para no perder pixeles arriba
    fig.add_annotation(
        x=bounds["lon_min"], y=bounds["lat_max"],
        xref="x", yref="y",
        text=f"<b>{label}</b>", showarrow=False,
        font=dict(size=12, color="#ffffff"),
        bgcolor="rgba(0,0,0,0.65)", borderpad=3,
        xanchor="left", yanchor="top",
        xshift=4, yshift=-4,
    )
    # Hotspots overlay (siempre encima de la imagen)
    _add_hotspots_overlay(fig, hotspots or [])
    fig.update_layout(
        height=height, margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor="#0a0e14", plot_bgcolor="#0a0e14",
    )
    if arr is None:
        fig.add_annotation(
            text="sin datos", xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False, font=dict(color="#556", size=12),
        )
    return fig


def render():
    from dashboard.manuals import render_manual
    render_manual("backfill")
    header(
        "📅 Backfill historico — eventos pasados",
        "Revision dia/hora de productos GOES-19 sobre eventos volcanicos archivados",
    )

    # ── Selector de evento ────────────────────────────────────────────
    cols = st.columns([2, 1])
    with cols[0]:
        sel_label = st.selectbox(
            "Evento", list(AVAILABLE_BACKFILLS.keys()),
            index=0, key="bf_event",
        )
        tag = AVAILABLE_BACKFILLS[sel_label]

    with cols[1]:
        st.markdown(
            f"<div style='font-size:0.78rem; color:#7a8a9a; padding-top:0.5rem;'>"
            f"Release: <code>{tag}</code></div>",
            unsafe_allow_html=True,
        )

    manifest = _fetch_manifest(tag)
    if manifest is None:
        st.error(
            f"No pude leer el manifest de `{tag}`. Posibles causas:\n"
            "- El release no existe todavia (correr `scripts/build_backfill.py` y "
            "subir contenido de `out_backfill/` al release con ese tag).\n"
            "- Conectividad con GitHub Releases."
        )
        st.code(
            f"# Para crear el release:\n"
            f"python scripts/build_backfill.py --date 2026-02-08 "
            f"--start 10:36 --end 19:00 --volcan Lascar --zone norte "
            f"--include-volcat\n"
            f"gh release create {tag} --title '{sel_label}' --notes 'Backfill auto'\n"
            f"gh release upload {tag} out_backfill/*",
            language="bash",
        )
        return

    # ── Info del evento ───────────────────────────────────────────────
    n_ts = len(manifest.get("timestamps_target", []))
    scopes = list(manifest.get("scopes", {}).keys())
    st.markdown(
        f"<div style='background:#0f1418; border-left:4px solid #ff6644; "
        f"padding:0.6rem 1rem; border-radius:4px; margin-bottom:0.8rem;'>"
        f"<b>{manifest['volcan']}</b> &middot; {manifest['date']} "
        f"&middot; {manifest['start']}-{manifest['end']} UTC<br>"
        f"<span style='font-size:0.85rem; color:#aabbcc;'>"
        f"{n_ts} timestamps cada 10 min &middot; {len(scopes)} scopes "
        f"({', '.join(scopes)})</span></div>",
        unsafe_allow_html=True,
    )

    # ── Selector de scope (volcan vs zona) ────────────────────────────
    scope_labels = {sid: sid.replace("__", " · ").replace("_", " ").title()
                    for sid in scopes}
    sel_scope = st.radio(
        "Vista", scopes, format_func=lambda s: scope_labels[s],
        index=0, horizontal=True, key="bf_scope",
    )
    scope_data = manifest["scopes"][sel_scope]
    bounds = scope_data["bounds"]

    # ── Slider de timestamp (deslizá para ver la evolución temporal) ──
    timestamps = manifest["timestamps_target"]
    idx = st.slider(
        "Timestamp (deslizá para ver la evolución)", 0, len(timestamps) - 1,
        0, 1, format="%d", label_visibility="collapsed", key="bf_ts_idx",
    )
    ts = timestamps[idx]
    st.markdown(
        f"<div style='font-size:0.95rem; color:#e0e0e0; margin-bottom:0.4rem;'>"
        f"<b>Timestamp {idx + 1}/{len(timestamps)}:</b> {_ts_to_label(ts)}"
        f"</div>",
        unsafe_allow_html=True,
    )

    # ── Productos + toggle hotspots ───────────────────────────────────
    cols_prod = st.columns([3, 1])
    with cols_prod[0]:
        products_in_manifest = manifest.get("products_rammb", [])
        show_products = st.multiselect(
            "Productos a mostrar",
            products_in_manifest + ["volcat"],
            default=products_in_manifest + ["volcat"],
            format_func=lambda p: PRODUCT_LABELS.get(p, p),
            key="bf_products",
        )
    with cols_prod[1]:
        # Solo mostrar toggle si el manifest dice que hay hotspots
        has_hs = bool(scope_data.get("hotspots_ts"))
        show_hotspots = st.toggle(
            "🔥 Hot spots overlay", value=has_hs,
            disabled=not has_hs, key="bf_hotspots",
            help=("Hotspots NOAA FDCF historicos overlay sobre cada producto. "
                  "Diamantes rojos, tamano = FRP. Disponibles solo si el "
                  "backfill se construyo con --include-hotspots.") if has_hs
                 else "No hay hotspots en este backfill (re-correr con --include-hotspots)",
        )

    # Cargar hotspots para este (scope, ts) si toggle activo
    hotspots_for_ts: list[dict] = []
    if show_hotspots and has_hs:
        hs_asset = f"{sel_scope}__hotspots__{ts}.json"
        hotspots_for_ts = _fetch_hotspots_json(tag, hs_asset)

    if not show_products:
        st.info("Selecciona al menos un producto.")
        return

    # ── Grid de productos ─────────────────────────────────────────────
    n_products = len(show_products)
    cols_per_row = min(3, n_products)
    n_rows = (n_products + cols_per_row - 1) // cols_per_row

    # Pre-fetch en paralelo no es trivial con st.cache_data. Cargamos
    # serial pero las fetch siguientes (al cambiar slider) se cachean.
    # Pre-cargar GeoColor del scope+ts si tenemos VOLCAT en lista — lo usaremos
    # como base para componer el overlay VOLCAT (que es transparente fuera
    # de pixeles con ceniza).
    geo_for_volcat = None
    if "volcat" in show_products:
        geo_asset = f"{sel_scope}__geocolor__{ts}.png"
        geo_for_volcat = _fetch_png(tag, geo_asset, keep_alpha=False)

    for r in range(n_rows):
        cols = st.columns(cols_per_row)
        for c in range(cols_per_row):
            i = r * cols_per_row + c
            if i >= n_products:
                break
            prod = show_products[i]
            with cols[c]:
                if prod == "volcat":
                    # VOLCAT es overlay transparente — componer sobre GeoColor.
                    asset = f"{sel_scope}__volcat__{ts}.png"
                    volcat_rgba = _fetch_png(tag, asset, keep_alpha=True)
                    arr = _composite_volcat(volcat_rgba, geo_for_volcat)
                    label = "VOLCAT (overlay sobre GeoColor)"
                else:
                    asset = f"{sel_scope}__{prod}__{ts}.png"
                    arr = _fetch_png(tag, asset)
                    label = PRODUCT_LABELS.get(prod, prod)
                fig = _render_product_panel(arr, bounds, label, height=360,
                                             hotspots=hotspots_for_ts)
                st.plotly_chart(fig, width='stretch',
                                config={"displayModeBar": False})

    # ── Panel info ────────────────────────────────────────────────────
    with st.expander("ℹ Que muestra cada producto"):
        for p in show_products:
            st.markdown(
                f"**{PRODUCT_LABELS.get(p, p)}**: "
                f"{PRODUCT_INFO.get(p, 'Sin descripcion.')}"
            )

    # ── Workflow info ─────────────────────────────────────────────────
    with st.expander("⚙ Crear backfill de otra fecha"):
        st.markdown(
            "Para revisar otro evento historico, corre el script de backfill "
            "(o lanza el GitHub Action workflow_dispatch correspondiente) y "
            "sube el resultado a un nuevo release. Despues agrega el tag al "
            "diccionario `AVAILABLE_BACKFILLS` en este archivo:\n\n"
            "```bash\n"
            "python scripts/build_backfill.py \\\n"
            "    --date 2026-XX-XX --start HH:MM --end HH:MM \\\n"
            "    --volcan Villarrica --zone sur \\\n"
            "    --include-volcat\n"
            "gh release create backfill-2026-XX-XX-villarrica \\\n"
            "    --title 'Villarrica YYYY-MM-DD' --notes 'Backfill manual'\n"
            "gh release upload backfill-2026-XX-XX-villarrica out_backfill/*\n"
            "```"
        )
