"""Replay histórico Calbuco 2015 — primer evento de prueba.

Volcán Calbuco entró en erupción el 22-abr-2015 ~21:04 UTC con un primer
pulso explosivo (~21 km altura confirmada). Segundo pulso 23-abr-2015
~03:54 UTC. Este es el evento canónico para validar:
  - Receta Ash RGB sobre pluma confirmada
  - BTD split-window (B14-B15)
  - Detección VOLCAT (ya disponía SSEC datos NRT? — operacional desde 2018,
    asi que Calbuco 2015 NO tiene VOLCAT)
  - Estimación de altura de columna (Pavolonis si fuera 2018+, Wen-Rose 1994
    fallback histórico)

Fuente intentada: **RAMMB CIRA Slider archive de GOES-13** (sat=goes-13).
GOES-13 fue el GOES-East operacional 2010-2017, posicion -75°W.
Cadencia Full Disk era 30 min (cada :00 y :30 nominal).

Si RAMMB no conserva el archivo GOES-13 hay dos fallbacks:
  - Bundlear PNGs estáticos en `data/historic/calbuco_2015/` (manual)
  - Ofrecer un script `scripts/fetch_calbuco_2015.py` para que el usuario lo
    corra una vez con credenciales NOAA S3 si los necesitara

Esta vista es el **MVP**: prueba el fetch, si falla muestra mensaje claro
con próximos pasos.
"""

import io
import logging
from pathlib import Path

import numpy as np
import plotly.graph_objects as go
import requests
import streamlit as st
from PIL import Image as PILImage

from dashboard.style import header

logger = logging.getLogger(__name__)

# Calbuco coords + bbox de la pluma observada (cubre desde Puerto Montt
# hasta el Atlantico siguiendo dispersion E)
CALBUCO_LAT = -41.33
CALBUCO_LON = -72.62
PLUME_BOUNDS = {
    "lat_min": -45.0, "lat_max": -38.0,
    "lon_min": -75.0, "lon_max": -65.0,
}

# Timestamps clave del evento (UTC). GOES-13 cadencia Full Disk 30 min,
# scans se publicaban con offset variable. Probamos varios candidatos.
KEY_EVENTS = [
    {
        "label": "Pre-erupción (22-Apr 20:30 UTC)",
        "ts_candidates": ["20150422203000", "20150422210000"],
        "description": "Día calmo previo. Volcán visible sin pluma.",
    },
    {
        "label": "PULSO 1 — explosivo (22-Apr 21:30 UTC)",
        "ts_candidates": ["20150422213000", "20150422220000"],
        "description": "Pluma de ~21 km penetrando estratósfera. Color "
                       "rojo intenso en Ash RGB sobre la zona del cráter.",
    },
    {
        "label": "Dispersión inicial (22-Apr 23:30 UTC)",
        "ts_candidates": ["20150422233000", "20150423000000"],
        "description": "Nube dispersándose hacia el este por viento "
                       "estratosférico (>200 km/h en 100 hPa).",
    },
    {
        "label": "PULSO 2 — fase reactivada (23-Apr 04:00 UTC)",
        "ts_candidates": ["20150423040000", "20150423043000"],
        "description": "Segundo pulso explosivo ~04:00 UTC, ~15 km altura.",
    },
    {
        "label": "Madrugada post-pulso 2 (23-Apr 09:00 UTC)",
        "ts_candidates": ["20150423090000", "20150423093000"],
        "description": "Pluma de ambos pulsos sobre Argentina.",
    },
]

PRODUCTS = {
    "geocolor": "GeoColor",
    "eumetsat_ash": "Ash RGB",
    "jma_so2": "SO2 RGB",
}

# RAMMB CIRA Slider URLs históricos
SLIDER_BASE = "https://slider.cira.colostate.edu"
GOES13_SAT = "goes-13"
SECTOR_HIST = "full_disk"

# Cache local en disco (más persistente que st.cache_data)
LOCAL_CACHE_DIR = Path(__file__).parent.parent.parent / "data" / "historic" / "calbuco_2015"


def _local_cache_path(product: str, ts: str, zoom: int, row: int, col: int) -> Path:
    return LOCAL_CACHE_DIR / f"{product}_{ts}_z{zoom}_r{row}_c{col}.png"


def _try_fetch_tile(product: str, ts: str, zoom: int, row: int, col: int,
                    timeout: int = 15) -> np.ndarray | None:
    """Intenta bajar un tile de RAMMB GOES-13 archive. Cachea local.

    URL: {BASE}/data/imagery/YYYY/MM/DD/goes-13---full_disk/{product}/{ts}/{zoom}/{row}_{col}.png
    """
    # Intentar cache local primero
    cache_path = _local_cache_path(product, ts, zoom, row, col)
    if cache_path.exists():
        try:
            img = PILImage.open(cache_path)
            return np.array(img)
        except Exception:
            pass

    yyyy, mm, dd = ts[:4], ts[4:6], ts[6:8]
    url = (
        f"{SLIDER_BASE}/data/imagery/{yyyy}/{mm}/{dd}"
        f"/{GOES13_SAT}---{SECTOR_HIST}/{product}/{ts}"
        f"/{zoom:02d}/{row:03d}_{col:03d}.png"
    )
    try:
        r = requests.get(url, timeout=timeout)
        r.raise_for_status()
        img = PILImage.open(io.BytesIO(r.content))
        arr = np.array(img)
        # Guardar cache local
        try:
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            img.save(cache_path)
        except Exception as e:
            logger.warning("No se pudo guardar cache: %s", e)
        return arr
    except requests.HTTPError as e:
        if e.response is not None and e.response.status_code == 404:
            return None
        logger.warning("HTTP error %s en GOES-13 fetch: %s", e.response.status_code if e.response else "?", url)
        return None
    except Exception as e:
        logger.warning("Error fetching %s: %s", url, e)
        return None


@st.cache_data(ttl=86400, show_spinner=False)  # 24h cache (datos historicos no cambian)
def _try_fetch_frame_calbuco(product: str, ts: str) -> tuple[np.ndarray | None, str]:
    """Intenta bajar un frame Calbuco para zoom=2 (region sudamerica).

    Returns:
        (img, status_msg). status_msg es "ok", "404" o descripcion error.
    """
    # zoom=2 cubre region grande, 4 tiles típicos sobre Calbuco
    # GOES-13 estaba a -75° (igual que GOES-19 ahora) asi que tiles similares
    zoom = 2
    # Intentar 1 tile central que cubre Sudamerica meridional
    # Para GOES-13 la grilla es 4x4 a zoom=2; row 2-3 col 1-2 cubre Chile
    img = _try_fetch_tile(product, ts, zoom=zoom, row=2, col=1)
    if img is not None:
        return img, "ok"
    return None, "404"


def _build_fig(img: np.ndarray, title: str, height: int = 720) -> go.Figure:
    import base64
    from PIL import Image as PILImg
    pil = PILImg.fromarray(img.astype(np.uint8))
    buf = io.BytesIO()
    pil.save(buf, format="PNG")
    data_url = "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()

    h, w = img.shape[:2]
    fig = go.Figure()
    fig.add_layout_image(
        source=data_url,
        xref="x", yref="y",
        x=0, y=h,
        sizex=w, sizey=h,
        sizing="stretch", layer="below",
    )
    # Marcador Calbuco aproximado (centro del tile, no perfectamente georef
    # porque RAMMB tiles son scan-angle-based, no lat/lon)
    fig.add_trace(go.Scatter(
        x=[w * 0.55], y=[h * 0.55],   # aprox centro del tile sur
        mode="markers+text",
        marker=dict(symbol="triangle-up", size=18, color="#ff6644",
                    line=dict(color="white", width=2)),
        text=["Calbuco"], textposition="top center",
        textfont=dict(color="#ff6644", size=12),
        showlegend=False,
    ))
    fig.update_xaxes(range=[0, w], showgrid=False, visible=False)
    fig.update_yaxes(range=[0, h], showgrid=False, visible=False, scaleanchor="x")
    fig.update_layout(
        title=dict(text=title, font=dict(size=13, color="#e0e0e0")),
        height=height, margin=dict(l=0, r=0, t=30, b=0),
        paper_bgcolor="#0a0e14", plot_bgcolor="#0a0e14",
    )
    return fig


def render():
    header(
        "🔁 Replay histórico — Calbuco 22-abr-2015",
        "Evento canónico para validar Ash RGB / BTD / detectores. "
        "Pluma confirmada ~21 km · GOES-13 (decommissioned 2018)",
    )

    # Banner contexto
    st.markdown(
        "<div style='background:#221814; border-left:4px solid #ff6644; "
        "padding:0.8rem 1rem; border-radius:4px; margin-bottom:1rem;'>"
        "<b style='color:#ff6644;'>⚠ Replay histórico — datos GOES-13</b><br>"
        "<span style='color:#c0ccd8; font-size:0.85rem;'>"
        "Esta vista intenta recuperar imágenes del archivo RAMMB CIRA "
        "para GOES-13 (operacional 2010-2017). Si RAMMB no conserva el "
        "archivo de esa fecha, los frames aparecerán como 'no disponible'. "
        "En ese caso, ver instrucciones abajo para backfill manual."
        "</span></div>",
        unsafe_allow_html=True,
    )

    # Selector evento + producto
    cols = st.columns([3, 1])
    with cols[0]:
        ev_idx = st.selectbox(
            "Momento del evento",
            options=list(range(len(KEY_EVENTS))),
            format_func=lambda i: KEY_EVENTS[i]["label"],
            index=1,  # default = pulso 1
            key="calbuco_event",
        )
    with cols[1]:
        product = st.selectbox(
            "Producto",
            options=list(PRODUCTS.keys()),
            format_func=lambda k: PRODUCTS[k],
            index=0, key="calbuco_product",  # GeoColor por default (más probable que esté archivado)
        )

    event = KEY_EVENTS[ev_idx]
    st.markdown(
        f"<div style='font-size:0.9rem; color:#b0b8c4; margin:0.3rem 0 0.8rem;'>"
        f"<b>Descripción:</b> {event['description']}</div>",
        unsafe_allow_html=True,
    )

    # Intentar fetch para cada timestamp candidato hasta que uno funcione
    img = None
    used_ts = None
    status_messages = []
    for ts in event["ts_candidates"]:
        with st.spinner(f"Intentando RAMMB GOES-13 archive @ {ts}…"):
            img, status = _try_fetch_frame_calbuco(product, ts)
        status_messages.append(f"{ts}: {status}")
        if img is not None:
            used_ts = ts
            break

    if img is not None:
        st.success(
            f"✅ Imagen recuperada de RAMMB CIRA archive · "
            f"GOES-13 · {PRODUCTS[product]} · {used_ts}"
        )
        fig = _build_fig(
            img,
            f"Calbuco 2015 · {event['label']} · {PRODUCTS[product]} · "
            f"GOES-13 · {used_ts}",
            height=720,
        )
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

        st.caption(
            "ℹ Imagen sin re-georeferenciación a lat/lon. RAMMB sirve tiles en "
            "scan-angle space del satélite. El triángulo marca aproximadamente "
            "donde está Calbuco en el tile (centro-sur). Para análisis "
            "cuantitativo bajar L1b NetCDF de noaa-goes13 S3."
        )
    else:
        st.error(
            "❌ RAMMB no conserva el archivo GOES-13 para esta fecha/producto, "
            "o el sector es distinto al esperado. Esto es esperable — el "
            "archivo histórico de RAMMB se foca en GOES-16/17/18/19 y datos "
            "post-2018 cuando estos satélites entraron en operación."
        )
        with st.expander("🔍 Diagnóstico (timestamps probados)"):
            for msg in status_messages:
                st.code(msg)

        st.markdown("---")
        st.markdown(
            "### Próximos pasos para tener Calbuco 2015 funcional\n"
            "**Opción A — bundlear PNGs públicos** (más rápido):\n"
            "- Descargar imágenes Wikimedia Commons / GVP de Calbuco 2015\n"
            "- Guardar en `data/historic/calbuco_2015/` con nombre estandarizado\n"
            "- Modificar este vista para preferir local antes de RAMMB\n"
            "\n"
            "**Opción B — backfill desde NOAA S3** (correcto, más trabajo):\n"
            "- `s3://noaa-goes13` mantiene L1b NetCDF de toda la operación de GOES-13\n"
            "- Bandas relevantes para Ash RGB: B4 (10.7 µm), B5 (12 µm)  \n"
            "  *(GOES-13 tenía 5 canales IR únicamente)*\n"
            "- Receta Ash RGB EUMETSAT requiere B11/B14/B15 → adaptar a las 5 bandas de GOES-13\n"
            "- ~500 LOC + procesamiento — sesión dedicada\n"
            "\n"
            "**Opción C — usar DOAS / MODIS en lugar de GOES-13**:\n"
            "- MODIS Terra/Aqua tienen archivo más estable y bandas similares a GOES-R\n"
            "- Latencia post-evento mayor pero datos mejores\n"
            "- Requiere fetch desde LAADS DAAC de NASA\n"
        )

    # Footer info evento
    st.markdown("---")
    st.markdown(
        "### 📚 Sobre Calbuco 22-Apr-2015\n\n"
        "- **Pulso 1**: 22-Apr-2015 21:04 UTC (18:04 hora Chile). Columna ~21 km confirmada por radiosondas y radar.\n"
        "- **Pulso 2**: 23-Apr-2015 04:00 UTC. Más bajo, ~15 km.\n"
        "- **Tipo**: subpliniana, cenizas finas con poco SO₂.\n"
        "- **Impacto**: ~6500 evacuados, 4 ciudades afectadas (Ensenada, Río Frío, Cochamó, Hualaihué). Pluma alcanzó Buenos Aires.\n"
        "- **Tras la ciencia**: caso de prueba estándar para algoritmos de detección de cenizas, "
        "altura de columna y dispersión. Citado en Pavolonis et al. 2018, "
        "Romero et al. 2016, y >50 papers post-2015."
    )
