"""Pagina VOLCAT: productos pre-procesados por SSEC/CIMSS via RealEarth API.

Muestra Ash RGB y SO2 RGB generados por SSEC para GOES-19,
y Volcanic Ash Advisories (VAA) como overlay.
"""

import logging

import numpy as np
import plotly.graph_objects as go
import streamlit as st

from dashboard.style import (
    C_ACCENT, C_ASH, C_SO2,
    ash_legend, ash_so2_legend, header, info_panel, kpi_card, refresh_info_badge,
)
from dashboard.utils import fmt_chile
from src.config import CHILE_BOUNDS, VOLCANIC_ZONES
from src.fetch.realearth_api import (
    fetch_image,
    fetch_vaa_geojson,
    get_latest_time,
)
from src.volcanos import CATALOG

logger = logging.getLogger(__name__)

ZONE_OPTIONS = {
    "Chile completo": CHILE_BOUNDS,
    "Zona Norte": VOLCANIC_ZONES["norte"],
    "Zona Centro": VOLCANIC_ZONES["centro"],
    "Zona Sur": VOLCANIC_ZONES["sur"],
    "Zona Austral": VOLCANIC_ZONES["austral"],
}


def _fig_ssec_image(img_rgba, bounds, title, volcanoes):
    """Mostrar imagen SSEC como go.Image con volcanes."""
    fig = go.Figure()

    lat_min = bounds["lat_min"]
    lat_max = bounds["lat_max"]
    lon_min = bounds["lon_min"]
    lon_max = bounds["lon_max"]

    import base64, io
    from PIL import Image as PILImage

    # Convertir RGBA a RGB
    rgb = img_rgba[:, :, :3].copy()
    alpha = img_rgba[:, :, 3:4].astype(np.float32) / 255.0
    rgb = (rgb.astype(np.float32) * alpha).astype(np.uint8)

    buf = io.BytesIO()
    PILImage.fromarray(rgb).save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode()

    # Scatter invisible para fijar el dominio del eje
    fig.add_trace(go.Scatter(
        x=[lon_min, lon_max], y=[lat_min, lat_max],
        mode="markers", marker=dict(opacity=0), showlegend=False,
        hoverinfo="skip",
    ))

    # Imagen georeferenciada con add_layout_image (respeta eje Y geográfico)
    fig.add_layout_image(
        source=f"data:image/png;base64,{b64}",
        xref="x", yref="y",
        x=lon_min, y=lat_max,
        xanchor="left", yanchor="top",
        sizex=lon_max - lon_min,
        sizey=lat_max - lat_min,
        sizing="stretch",
        layer="below",
    )

    # Volcano markers
    lat_arr = np.array([lat_min, lat_max])
    lon_arr = np.array([lon_min, lon_max])
    vis = [v for v in volcanoes
           if lat_min <= v.lat <= lat_max and lon_min <= v.lon <= lon_max]
    if vis:
        fig.add_trace(go.Scatter(
            x=[v.lon for v in vis], y=[v.lat for v in vis],
            mode="markers+text",
            marker=dict(size=6, color=C_ACCENT, symbol="triangle-up",
                        line=dict(width=0.8, color="white")),
            text=[v.name for v in vis],
            textposition="top center",
            textfont=dict(size=8, color="rgba(255,255,255,0.7)"),
            name="Volcanes",
            hovertext=[f"{v.name} ({v.elevation:,} m)" for v in vis],
            hoverinfo="text",
        ))

    fig.update_layout(
        title=dict(text=title, font=dict(size=14, color="#ccc")),
        xaxis_title="Longitud", yaxis_title="Latitud",
        height=700, template="plotly_dark",
        yaxis=dict(scaleanchor="x", scaleratio=1),
        margin=dict(t=45, b=40, l=50, r=20),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    )
    return fig


def _parse_timestamp(ts_str):
    """Convertir timestamp SSEC (YYYYMMDD.HHMMSS) a legible con hora local."""
    if not ts_str:
        return "—"
    try:
        from datetime import datetime, timezone
        date_part = ts_str.split(".")[0]
        time_part = ts_str.split(".")[1] if "." in ts_str else "000000"
        utc_str = f"{date_part[:4]}-{date_part[4:6]}-{date_part[6:8]} {time_part[:2]}:{time_part[2:4]} UTC"
        # Agregar hora local Chile
        dt = datetime(
            int(date_part[:4]), int(date_part[4:6]), int(date_part[6:8]),
            int(time_part[:2]), int(time_part[2:4]),
            tzinfo=timezone.utc,
        )
        ch_str = fmt_chile(dt)
        return f"{utc_str}  ({ch_str} Chile)"
    except Exception:
        return ts_str


def render():
    header(
        "VOLCAT — Productos SSEC/CIMSS",
        "Imagenes pre-procesadas por la Universidad de Wisconsin via RealEarth API &middot; GOES-19",
    )

    refresh_info_badge(context="general")

    # ── Controles ──
    c1, c2 = st.columns([1.5, 1])
    with c1:
        zone_key = st.selectbox("Region", list(ZONE_OPTIONS.keys()), index=0,
                                key="volcat_zone")
    with c2:
        st.markdown("<div style='height:1.6rem'></div>", unsafe_allow_html=True)
        fetch = st.button("Obtener imagenes SSEC", type="primary",
                          use_container_width=True)

    bounds = ZONE_OPTIONS[zone_key]

    if not fetch:
        # Show info + latest timestamps
        col_info, col_ts = st.columns([2, 1])
        with col_info:
            info_panel(
                "<b>Productos VOLCAT via RealEarth API</b><br><br>"
                "Esta pagina muestra imagenes Ash RGB y SO2 RGB generadas directamente "
                "por SSEC/CIMSS (Universidad de Wisconsin), los creadores del sistema VOLCAT.<br><br>"
                "A diferencia de nuestros productos propios (pagina Ash RGB Viewer), estas "
                "imagenes son procesadas por SSEC con algoritmos avanzados de calibracion "
                "y composicion de color optimizados.<br><br>"
                "<b>Fuente:</b> RealEarth API (publico, sin autenticacion)<br>"
                "<b>Retencion:</b> ~28 dias en el portal"
            )
        with col_ts:
            ash_ts = get_latest_time("ash_rgb")
            so2_ts = get_latest_time("so2_rgb")
            st.markdown(
                f'<div class="legend-container">'
                f'<div class="legend-title">Ultima imagen disponible</div>'
                f'<div style="font-size:0.82rem; color:#99aabb; line-height:2;">'
                f'<b>Ash RGB:</b> {_parse_timestamp(ash_ts)}<br>'
                f'<b>SO2 RGB:</b> {_parse_timestamp(so2_ts)}'
                f'</div></div>',
                unsafe_allow_html=True,
            )
        return

    # ── Fetch images ──
    ash_img = None
    so2_img = None
    vaa = None

    with st.spinner("Descargando productos SSEC (Ash RGB + SO2 RGB + VAA)..."):
        ash_ts = get_latest_time("ash_rgb")
        so2_ts = get_latest_time("so2_rgb")

        ash_img = fetch_image("ash_rgb", bounds=bounds, time=ash_ts)
        so2_img = fetch_image("so2_rgb", bounds=bounds, time=so2_ts)
        vaa = fetch_vaa_geojson()

    # ── Status banner ──
    products_ok = sum(1 for x in [ash_img, so2_img] if x is not None)
    vaa_count = len(vaa.get("features", [])) if vaa else 0

    ts_display = _parse_timestamp(ash_ts)
    st.markdown(
        f'<div class="status-banner ok">'
        f'<b>&#10003; {products_ok}/2 productos descargados — '
        f'{vaa_count} VAA activos globalmente</b>'
        f'<span style="color:#556677; font-size:0.78rem;">{ts_display}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # ── KPIs ──
    k1, k2, k3 = st.columns(3)
    with k1:
        kpi_card("SSEC", "Fuente de datos")
    with k2:
        kpi_card(ts_display.split(" ")[1] if " " in ts_display else "—", "Hora UTC")
    with k3:
        kpi_card(str(vaa_count), "VAA activos",
                 delta="global" if vaa_count > 0 else "",
                 delta_type="negative" if vaa_count > 0 else "neutral")

    st.markdown("<div style='height:0.4rem'></div>", unsafe_allow_html=True)

    # ── Tabs ──
    tab1, tab2, tab3 = st.tabs(["Ash RGB (SSEC)", "SO2 RGB (SSEC)", "VAA Advisories"])

    with tab1:
        col_img, col_leg = st.columns([5, 1.2])
        with col_img:
            if ash_img is not None:
                fig = _fig_ssec_image(
                    ash_img, bounds,
                    f"Ash RGB — SSEC/CIMSS GOES-19 ({ts_display})",
                    CATALOG,
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.error("No se pudo descargar la imagen Ash RGB de SSEC")
        with col_leg:
            ash_legend()

    with tab2:
        col_img2, col_leg2 = st.columns([5, 1.2])
        with col_img2:
            if so2_img is not None:
                fig = _fig_ssec_image(
                    so2_img, bounds,
                    f"SO2 RGB — SSEC/CIMSS GOES-19 ({_parse_timestamp(so2_ts)})",
                    CATALOG,
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.error("No se pudo descargar la imagen SO2 RGB de SSEC")
        with col_leg2:
            ash_so2_legend()

    with tab3:
        if vaa and vaa.get("features"):
            st.markdown(
                f'<div class="status-banner warn">'
                f'<b>&#9888; {vaa_count} Volcanic Ash Advisory(ies) activos globalmente</b>'
                f'</div>',
                unsafe_allow_html=True,
            )

            for feat in vaa["features"]:
                props = feat.get("properties", {})
                name = props.get("name", props.get("title", "Sin nombre"))
                desc = props.get("description", "")

                st.markdown(
                    f'<div class="volcano-card">'
                    f'<h3>{name}</h3>'
                    f'<div class="detail">{desc}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
        else:
            info_panel(
                "<b>Sin Volcanic Ash Advisories activos.</b><br>"
                "Los VAA son emitidos por los VAACs (Volcanic Ash Advisory Centers) "
                "cuando se detecta ceniza volcanica en la atmosfera que puede afectar "
                "la aviacion. La ausencia de VAA indica condiciones normales."
            )
