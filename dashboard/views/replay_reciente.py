"""Replay reciente — vista de eventos volcánicos en últimos 28 días.

Reemplaza el "Replay Calbuco 2015" porque GOES-13 archive no esta en
RAMMB. En su lugar usamos datos REALES recientes de GOES-19 archive
(retencion ~28 dias en RAMMB) sobre volcanes con actividad continua:

- **Sangay (Ecuador)**: -2.005°, -78.341°. Casi continuo 2024-2026.
  Hot spots diarios, plumas frecuentes. Cobertura GOES-19 excelente.
- **Reventador (Ecuador)**: -0.077°, -77.66°. Explosiones diarias.
- **Sabancaya (Perú)**: -15.78°, -71.85°. Explosiones diarias documentadas.
- **Lascar (Chile)**: -23.37°, -67.73°. Hot spots térmicos esporádicos.

Caso de uso: probar TODA la plataforma actual (Ash RGB / hot spots NOAA /
altura VOLCAT / BTD / detección tri-espectral) sobre actividad volcánica
real reciente. Si encontrás un día con buena pluma, ese timestamp puede
ser el "evento de prueba" canónico para el equipo.

Por que NO Calbuco 2015:
- RAMMB no archiva GOES-13.
- VOLCAT operacional desde 2018.
- Hot spots FDCF tampoco existian.
- Calbuco vale para Wen-Rose 1994 historicamente — vista separada
  (todavia pendiente).
"""

import logging
from datetime import datetime, timedelta, timezone

import numpy as np
import plotly.graph_objects as go
import streamlit as st

from dashboard.style import header
from dashboard.utils import fmt_chile, parse_rammb_ts
from src.fetch.rammb_slider import (
    fetch_frame_robust, get_latest_timestamps, ZOOM_VOLCAN, ZOOM_ZONE,
)
from src.volcanos import CATALOG, get_volcano

logger = logging.getLogger(__name__)

# Volcanes activos para replay — incluye Chile + países vecinos cubiertos
# por GOES-19 con actividad reciente confirmada
ACTIVE_VOLCANOES = [
    {"name": "Sangay (Ecuador)", "rationale": "Actividad casi continua. Hot spots diarios."},
    {"name": "Reventador (Ecuador)", "rationale": "Explosiones diarias. Pluma frecuente."},
    {"name": "Sabancaya (Perú)", "rationale": "1-3 explosiones/día documentadas."},
    {"name": "Villarrica", "rationale": "Lago de lava activo. Hot spots térmicos."},
    {"name": "Láscar", "rationale": "Hot spots térmicos esporádicos."},
    {"name": "Copahue", "rationale": "Emisión sostenida de SO2."},
]

PRODUCTS = {
    "eumetsat_ash": "Ash RGB",
    "geocolor": "GeoColor",
    "jma_so2": "SO2 RGB",
}

RADIUS_DEG = 0.4


@st.cache_data(ttl=300, show_spinner=False)
def _list_timestamps(product: str, n: int = 200) -> list[str]:
    """Lista hasta N timestamps del producto. RAMMB archive ~28 dias."""
    return get_latest_timestamps(product, n=n)


def _array_to_data_url(arr: np.ndarray) -> str:
    import base64
    import io
    from PIL import Image
    img = Image.fromarray(arr.astype(np.uint8))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def _plot_frame(img: np.ndarray | None, lat: float, lon: float,
                volcan_name: str, title: str, height: int = 720):
    fig = go.Figure()
    bounds = {
        "lat_min": lat - RADIUS_DEG, "lat_max": lat + RADIUS_DEG,
        "lon_min": lon - RADIUS_DEG, "lon_max": lon + RADIUS_DEG,
    }
    if img is not None:
        fig.add_layout_image(
            source=_array_to_data_url(img),
            xref="x", yref="y",
            x=bounds["lon_min"], y=bounds["lat_max"],
            sizex=2 * RADIUS_DEG, sizey=2 * RADIUS_DEG,
            sizing="stretch", layer="below",
        )
    fig.add_trace(go.Scatter(
        x=[lon], y=[lat], mode="markers+text",
        marker=dict(symbol="triangle-up", size=18, color="#00ffff",
                    line=dict(color="white", width=2)),
        text=[volcan_name], textposition="top center",
        textfont=dict(color="#00ffff", size=12),
        showlegend=False, hoverinfo="skip",
    ))
    cos_lat = max(0.1, float(np.cos(np.radians(lat))))
    fig.update_xaxes(range=[bounds["lon_min"], bounds["lon_max"]],
                     showgrid=False, visible=False)
    fig.update_yaxes(range=[bounds["lat_min"], bounds["lat_max"]],
                     showgrid=False, visible=False,
                     scaleanchor="x", scaleratio=1.0 / cos_lat)
    fig.update_layout(
        title=dict(text=title, font=dict(size=12, color="#e0e0e0")),
        height=height, margin=dict(l=0, r=0, t=30, b=0),
        paper_bgcolor="#0a0e14", plot_bgcolor="#0a0e14",
    )
    if img is None:
        fig.add_annotation(text="Sin imagen", xref="paper", yref="paper",
                           x=0.5, y=0.5, showarrow=False,
                           font=dict(color="#7a8a9a", size=14))
    return fig


def render():
    header(
        "🔁 Replay reciente — actividad real GOES-19",
        "Eventos volcánicos en últimos 28 días · Sangay/Reventador/Sabancaya/Lascar/Villarrica/Copahue",
    )

    # Banner explicativo
    st.markdown(
        "<div style='background:#0f1418; border-left:4px solid #4a9eff; "
        "padding:0.7rem 1rem; border-radius:4px; margin-bottom:0.8rem;'>"
        "<b style='color:#4a9eff;'>📌 Por qué reemplazamos Calbuco 2015</b>"
        "<div style='color:#c0ccd8; font-size:0.85rem; margin-top:0.3rem;'>"
        "Calbuco 2015 es el caso canónico científico, pero <b>RAMMB no archiva "
        "GOES-13</b>, VOLCAT no existía, y FDCF tampoco. Para probar TODA la "
        "plataforma actual usamos eventos recientes en cobertura GOES-19 con "
        "actividad continua. <b>Sangay y Reventador (Ecuador)</b> son ideales: "
        "tienen plumas casi diarias, hot spots NRT, y RAMMB conserva los "
        "últimos ~28 días de tiles."
        "</div></div>",
        unsafe_allow_html=True,
    )

    # Selectores
    cols = st.columns([2, 1.5, 1])
    with cols[0]:
        volcan_options = [v["name"] for v in ACTIVE_VOLCANOES]
        volcan_idx = st.selectbox(
            "Volcán",
            options=range(len(volcan_options)),
            format_func=lambda i: f"{volcan_options[i]} — {ACTIVE_VOLCANOES[i]['rationale']}",
            index=0, key="replay_volcan",
        )
        volcan_name = volcan_options[volcan_idx]
    with cols[1]:
        product = st.selectbox(
            "Producto",
            options=list(PRODUCTS.keys()),
            format_func=lambda k: PRODUCTS[k],
            index=0, key="replay_product",
        )
    with cols[2]:
        st.markdown(
            "<div style='color:#556; padding-top:0.6rem; font-size:0.78rem;'>"
            "Buscando últimos 28 días<br>en RAMMB archive…</div>",
            unsafe_allow_html=True,
        )

    v = get_volcano(volcan_name)
    if v is None:
        st.error(f"Volcán {volcan_name} no encontrado en catálogo.")
        return

    # Listar timestamps disponibles
    with st.spinner("Listando timestamps RAMMB últimos días…"):
        timestamps = _list_timestamps(product, n=200)
    if not timestamps:
        st.error("RAMMB no respondió. Reintentá en unos segundos.")
        return

    st.success(
        f"📡 RAMMB: {len(timestamps)} timestamps disponibles "
        f"(desde {timestamps[-1][:8]} hasta {timestamps[0][:8]})"
    )

    # Slider sobre timestamps (mas viejo izq, mas nuevo der)
    timestamps_chrono = list(reversed(timestamps))
    labels = []
    for ts in timestamps_chrono:
        try:
            dt = parse_rammb_ts(ts)
            labels.append(dt.strftime("%d-%b %H:%M UTC"))
        except Exception:
            labels.append(ts)

    idx = st.select_slider(
        "Timestamp (mover slider para reproducir el evento)",
        options=list(range(len(timestamps_chrono))),
        format_func=lambda i: labels[i],
        value=len(timestamps_chrono) - 1,  # default = mas reciente
        key="replay_idx",
    )

    selected_ts = timestamps_chrono[idx]

    # Bajar y mostrar
    bounds = {
        "lat_min": v.lat - RADIUS_DEG, "lat_max": v.lat + RADIUS_DEG,
        "lon_min": v.lon - RADIUS_DEG, "lon_max": v.lon + RADIUS_DEG,
    }
    img, used_ts, used_zoom = fetch_frame_robust(
        product, [selected_ts] + timestamps[:5], bounds,
        zoom_preferred=ZOOM_VOLCAN, zoom_fallback=ZOOM_ZONE,
    )

    label = f"{v.name} · {PRODUCTS[product]} · {labels[idx]}"
    if used_ts and used_ts != selected_ts:
        label += " ⚠ ts cercano"
    if used_zoom == ZOOM_ZONE:
        label += " ⚠ zoom 3"

    st.plotly_chart(
        _plot_frame(img, v.lat, v.lon, v.name, label, height=720),
        use_container_width=True,
        config={"displayModeBar": False},
    )

    # Tabla de productos disponibles para validar la plataforma
    st.markdown("### ✅ Qué podés validar con este evento")
    rows = [
        {"Producto": "Ash RGB (RAMMB)", "Estado": "✅ Disponible", "Probar": "Pluma roja brillante = ceniza"},
        {"Producto": "GeoColor (RAMMB)", "Estado": "✅ Disponible", "Probar": "Pluma visible/visible-IR"},
        {"Producto": "SO2 RGB (RAMMB)", "Estado": "✅ Disponible", "Probar": "Pluma verde si hay SO2 fresco"},
        {"Producto": "Hot spots NOAA FDCF", "Estado": "✅ Disponible", "Probar": "Lava expuesta o flujos calientes"},
        {"Producto": "Altura VOLCAT (SSEC)", "Estado": "✅ Disponible", "Probar": "Tab VOLCAT — ash height en km"},
        {"Producto": "BTD raw (L1b)", "Estado": "✅ Disponible", "Probar": "Tab Ash RGB Viewer — heatmap K"},
        {"Producto": "Tri-espectral (Pavolonis)", "Estado": "⚠ Parcial", "Probar": "Sólo en VOLCAT por ahora"},
    ]
    st.dataframe(rows, use_container_width=True, hide_index=True)

    st.caption(
        "💡 **Workflow sugerido**: con el slider encontrá un timestamp "
        "donde se vea pluma clara en Ash RGB. Después abrí ese mismo "
        "timestamp en otras vistas (Modo Evento, VOLCAT, Ash RGB Viewer) "
        "para cross-checkear. **Permalink amigable**: copiá la URL — "
        "incluye el volcán seleccionado."
    )

    # Sección Calbuco 2015 (movida abajo, solo info)
    with st.expander("📚 Calbuco 2015 — caso histórico (sin datos disponibles)"):
        st.markdown(
            "Calbuco 22-Apr-2015 21:04 UTC sigue siendo el evento canónico "
            "para validar **Wen-Rose 1994** (~21 km confirmado por radiosonda). "
            "Pero como GOES-13 archive no está en RAMMB, no podemos hacer "
            "replay con los productos actuales del dashboard.\n\n"
            "**Para usarlo en el futuro** necesitamos:\n"
            "- Backfill desde `s3://noaa-goes13` (5 bandas IR — adaptar receta Ash RGB)\n"
            "- O bundle de PNGs públicos de archivo en `data/historic/calbuco_2015/`\n\n"
            "Sesión dedicada futura, ~500 LOC."
        )
