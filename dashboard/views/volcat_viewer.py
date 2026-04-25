"""Pagina VOLCAT: productos pre-procesados por SSEC/CIMSS.

Dos APIs distintas:
- RealEarth API (https://realearth.ssec.wisc.edu): Ash RGB + SO2 RGB Full Disk +
  Volcanic Ash Advisories como overlay.
- VOLCAT portal API (https://volcano.ssec.wisc.edu/imagery): productos
  cuantitativos por sector — Ash Height (km), Ash Loading (g/m²), Ash
  Probability, Ash Reff (radio efectivo de partícula).
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
from src.fetch.volcat_api import (
    VOLCANO_TO_SECTOR, get_sector_for_volcano, volcat_latest,
)
from src.volcanos import CATALOG, PRIORITY_VOLCANOES, get_volcano

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
            marker=dict(size=4, color=C_ACCENT, symbol="triangle-up",
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


# ── VOLCAT portal: productos por sector (Ash Height, Loading, Probability, Reff) ──

# Cada producto tiene 4 campos:
#   label_es: nombre en dropdown (con unidad)
#   short:    descripcion corta (1 linea, para badge debajo del selector)
#   icon:     icono visual para cheat-sheet
#   long:     panel interpretativo extendido (Markdown) usado en expander
VOLCAT_PRODUCTS = {
    "Ash_Height": {
        "label_es": "Altura de pluma (km AMSL)",
        "short":    "Altura del tope de la pluma sobre el nivel del mar. Más alto = más energético.",
        "icon":     "⬆",
        "long":     """
- **Unidad**: km sobre el nivel del mar (AMSL).
- **Algoritmo**: Pavolonis et al. 2013 — ajuste simultáneo de
  temperatura del tope, espesor óptico y radio efectivo contra
  forward model RTM. Tc → altura usando perfil GFS de temperatura.
- **Precisión**: ±1-2 km en plumas opacas, ±3-4 km en plumas
  delgadas (τ<0.5) o sobre cirrus.
- **Limitación**: si pluma transparente al IR, subestima. Si hay
  nube meteo debajo, también subestima. Cruzar con Ash RGB.
""",
    },
    "Ash_Loading": {
        "label_es": "Carga columnar (g/m²)",
        "short":    "Cuántos gramos de ceniza por m² hay en la columna. Más alto = pluma más densa.",
        "icon":     "⚖",
        "long":     """
- **Unidad**: g/m² (carga columnar de masa de ceniza).
- **Uso**: integrar sobre área de pluma → tonelaje total.
  Combinado con velocidad → tasa de emisión (MER, kg/s).
- **Limitación**: solo cuantificable cuando hay detección estable
  y τ moderado (0.3-2). Plumas opacas saturan; delgadas tienen
  ruido alto.
""",
    },
    "Ash_Probability": {
        "label_es": "Probabilidad de ceniza (%)",
        "short":    "Confianza de que el píxel sea ceniza real (no cirrus/polvo). Filtro recomendado: >60%.",
        "icon":     "✓",
        "long":     """
- **Unidad**: 0-100%.
- **Uso**: confianza de que el píxel contiene ceniza volcánica
  vs cirrus / dust del desierto / nube de hielo.
- **Tip operativo**: usar como filtro sobre Ash_Height y
  Ash_Loading. Solo confiar en valores con probability > 60-70%.
""",
    },
    "Ash_Reff": {
        "label_es": "Radio efectivo (μm)",
        "short":    "Tamaño típico de partícula. <5 μm = fino (transporte largo). >10 μm = grueso (cae cerca).",
        "icon":     "●",
        "long":     """
- **Unidad**: μm (radio efectivo de partícula).
- **Uso**: indicador del modo de eyección. Finas (Reff < 5 μm)
  → eyección violenta + transporte largo. Gruesas (Reff > 10 μm)
  → eyección débil o cerca del cráter.
- **Limitación**: requiere asunción de composición (silicato).
  Basáltica vs riolítica tienen propiedades ópticas distintas.
""",
    },
}


def _volcat_cheatsheet_html() -> str:
    """Mini cheat-sheet de los 4 productos VOLCAT como chips visuales.

    Pensado para ir arriba del selector — el usuario ve los 4 productos
    de un vistazo antes de elegir.
    """
    chips = []
    for k, p in VOLCAT_PRODUCTS.items():
        chips.append(
            f'<div style="background:rgba(17,24,34,0.55); '
            f'border:1px solid rgba(100,120,140,0.2); '
            f'border-radius:6px; padding:0.35rem 0.6rem; '
            f'font-size:0.72rem; line-height:1.35; flex:1; min-width:160px;">'
            f'<div style="color:#c0ccd8; font-weight:700; margin-bottom:0.1rem;">'
            f'<span style="color:#4a9eff;">{p["icon"]}</span> '
            f'{p["label_es"]}'
            f'</div>'
            f'<div style="color:#7a8a99; font-size:0.7rem;">{p["short"]}</div>'
            f'</div>'
        )
    return (
        '<div style="display:flex; gap:0.4rem; flex-wrap:wrap; margin:0.3rem 0 0.5rem 0;">'
        + "".join(chips) + '</div>'
    )


@st.cache_data(ttl=300, show_spinner=False)
def _volcat_latest_cached(sector: str, instr: str, image_type: str) -> dict | None:
    """Cache 5 min — el VOLCAT publica cada 10 min con scan ABI."""
    return volcat_latest(sector, instr=instr, image_type=image_type)


@st.cache_data(ttl=600, show_spinner=False)
def _volcat_image_bytes(image_url: str) -> bytes:
    """Descargar PNG raw del VOLCAT (cache 10 min por URL — la URL incluye timestamp)."""
    import requests
    try:
        r = requests.get(image_url, timeout=30)
        r.raise_for_status()
        return r.content
    except Exception as e:
        logger.warning("Error bajando %s: %s", image_url, e)
        return b""


def _parse_volcat_dt(s: str | None) -> str:
    """'2026-04-25_17-20-30' -> '2026-04-25 17:20 UTC (...CL)'."""
    if not s:
        return "—"
    try:
        from datetime import datetime, timezone
        d, t = s.split("_")
        hh, mm, ss = t.split("-")
        dt = datetime(*map(int, d.split("-")), int(hh), int(mm), int(ss),
                      tzinfo=timezone.utc)
        return f"{dt.strftime('%Y-%m-%d %H:%M UTC')} ({fmt_chile(dt)} Chile)"
    except Exception:
        return s


def _render_height_section(key_suffix: str = "tab") -> None:
    """Render del bloque Altura/Loading/Probability/Reff.

    Reutilizado en la tab dedicada (cuando se hizo fetch del RGB) y en la
    pantalla inicial (cuando no se hizo fetch — porque la altura no requiere
    descarga pesada).
    """
    # Bajada compacta — solo lo esencial, fuentes en expander al final.
    st.markdown(
        '<div style="font-size:0.78rem; color:#8899aa; margin-bottom:0.2rem;">'
        '<b style="color:#c0ccd8;">VOLCAT</b> · SSEC/CIMSS · Pavolonis 2013 '
        '(optimal estimation 3-canal IR) · cadencia 10 min ABI + refuerzo MODIS/VIIRS'
        '</div>',
        unsafe_allow_html=True,
    )

    # Cheat-sheet con los 4 productos antes del selector — ayuda a elegir.
    st.markdown(_volcat_cheatsheet_html(), unsafe_allow_html=True)

    priority_names = [v.name for v in CATALOG if v.name in PRIORITY_VOLCANOES
                      and v.name in VOLCANO_TO_SECTOR]
    other_names    = [v.name for v in CATALOG if v.name in VOLCANO_TO_SECTOR
                      and v.name not in priority_names]
    volc_options   = [f"★ {n}" for n in priority_names] + other_names

    cv1, cv2 = st.columns([1.5, 1.5])
    with cv1:
        sel_raw = st.selectbox(
            "Volcán", volc_options, index=0,
            key=f"volcat_height_volcano_{key_suffix}",
            help="★ = volcán prioritario (con sector dedicado en VOLCAT)",
        )
        volc_name_h = sel_raw.replace("★ ", "")
    with cv2:
        # Tooltip ampliado en el selectbox + descripción inline debajo.
        help_text = "\n".join(
            f"• {p['icon']} {p['label_es']}: {p['short']}"
            for p in VOLCAT_PRODUCTS.values()
        )
        prod_h = st.selectbox(
            "Producto VOLCAT",
            list(VOLCAT_PRODUCTS.keys()),
            format_func=lambda k: VOLCAT_PRODUCTS[k]["label_es"],
            index=0, key=f"volcat_height_product_{key_suffix}",
            help=help_text,
        )

    # Descripción visible del producto seleccionado (inline, destacado).
    sel_meta = VOLCAT_PRODUCTS[prod_h]
    st.markdown(
        f'<div style="background:rgba(74,158,255,0.08); '
        f'border-left:3px solid #4a9eff; padding:0.4rem 0.7rem; '
        f'border-radius:0 6px 6px 0; margin:0.3rem 0; '
        f'font-size:0.78rem; line-height:1.45;">'
        f'<span style="color:#4a9eff; font-weight:700;">'
        f'{sel_meta["icon"]} {sel_meta["label_es"]}</span> '
        f'<span style="color:#aabbc8;">— {sel_meta["short"]}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

    sector_info = get_sector_for_volcano(volc_name_h)
    if not sector_info:
        st.error(
            f"El volcán '{volc_name_h}' no tiene sector VOLCAT mapeado todavía. "
            "Avisame para agregarlo a `src/fetch/volcat_api.py::VOLCANO_TO_SECTOR`."
        )
        return

    sector, instr = sector_info
    with st.spinner(
        f"Consultando VOLCAT para {volc_name_h} (sector {sector}, {prod_h})..."
    ):
        meta = _volcat_latest_cached(sector, instr, prod_h)

    if meta is None:
        st.warning(
            f"VOLCAT no devolvió frames recientes para sector "
            f"**{sector}** producto **{prod_h}** instr **{instr}**. "
            "Posibles causas: scan ABI atrasado, sector con cobertura "
            "intermitente, o el producto solo está disponible cuando "
            "VOLCAT detecta una pluma activa (Ash_Loading/Reff suelen "
            "ser nulos sin erupción). Probá Ash_Probability como "
            "indicador siempre disponible."
        )
        return

    ts_h = _parse_volcat_dt(meta.get("datetime"))
    kh1, kh2, kh3 = st.columns(3)
    with kh1:
        kpi_card(volc_name_h, "Volcán")
    with kh2:
        kpi_card(sector.replace("_", " "), "Sector VOLCAT")
    with kh3:
        short_ts = meta.get("datetime", "—").split("_")[-1].replace("-", ":")
        kpi_card(short_ts[:5] + " UTC" if len(short_ts) >= 5 else "—",
                 "Hora del scan")

    col_im, col_lg = st.columns([4, 1.4])
    with col_im:
        img_bytes = _volcat_image_bytes(meta["image_url"])
        if img_bytes:
            st.image(
                img_bytes,
                caption=(
                    f"{sel_meta['label_es']} — "
                    f"{volc_name_h} ({sector.replace('_', ' ')}) — {ts_h}"
                ),
                use_container_width=True,
            )
            st.download_button(
                f"⬇ Descargar PNG VOLCAT ({len(img_bytes)//1024} KB)",
                data=img_bytes,
                file_name=(
                    f"volcat_{prod_h.lower()}_{sector.lower()}_"
                    f"{(meta.get('datetime') or 'latest').replace(':', '-')}.png"
                ),
                mime="image/png",
                key=f"dl_volcat_height_{prod_h}_{sector}_{key_suffix}",
                use_container_width=True,
            )
        else:
            st.error("No se pudo descargar la imagen.")
            st.caption(f"URL: {meta.get('image_url', '?')}")

    with col_lg:
        st.markdown("<b style='font-size:0.78rem; color:#8899aa;'>Colorbar</b>",
                    unsafe_allow_html=True)
        leg_bytes = _volcat_image_bytes(meta["legend_url"])
        if leg_bytes:
            st.image(leg_bytes, use_container_width=True)
        else:
            st.caption("(sin leyenda)")

    # Panel interpretativo: usa el campo "long" de cada producto.
    with st.expander(
        f"Cómo leer {sel_meta['label_es']} (detalle técnico)", expanded=False,
    ):
        st.markdown(sel_meta["long"])

    st.markdown(
        f'<div style="font-size:0.72rem; color:#445566; margin-top:0.7rem;">'
        f'Ver en el portal SSEC: '
        f'<a href="https://volcano.ssec.wisc.edu/imagery/view/'
        f'#sector:{sector}::instr:{instr}::sat:all'
        f'::image_type:{prod_h}::endtime:latest::daterange:2880" '
        f'target="_blank" style="color:#667788;">abrir en VOLCAT viewer →</a>'
        f'</div>',
        unsafe_allow_html=True,
    )


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
        st.markdown("<div style='height:1.2rem'></div>", unsafe_allow_html=True)
        fetch = st.button("Obtener imagenes SSEC", type="primary",
                          use_container_width=True)

    bounds = ZONE_OPTIONS[zone_key]

    if not fetch:
        # Mostrar info panel + tab de Altura (que es independiente del fetch
        # pesado de RGB Full Disk).
        col_info, col_ts = st.columns([2, 1])
        with col_info:
            info_panel(
                "<b>Productos VOLCAT via SSEC/CIMSS</b><br><br>"
                "<b>Ash RGB / SO2 RGB</b> (Full Disk via RealEarth API): "
                "apretá <i>Obtener imagenes SSEC</i> arriba para descargarlas. "
                "Pesado, ~10s.<br><br>"
                "<b>Altura de pluma / Loading / Probability / Reff</b> "
                "(VOLCAT portal por sector): <b>disponible directo abajo</b>, "
                "no necesita el botón. Algoritmo Pavolonis 2013 "
                "(optimal estimation), ±1-2 km de error en plumas opacas.<br><br>"
                "<b>Fuente:</b> RealEarth + VOLCAT portal (publico, sin auth)<br>"
                "<b>Retencion:</b> ~28 dias"
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

        # Tab Altura (independiente — no requiere fetch pesado)
        st.markdown("---")
        st.markdown(
            "### 📏 Altura de pluma VOLCAT (disponible siempre)",
            unsafe_allow_html=True,
        )
        _render_height_section(key_suffix="standalone")
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

    st.markdown("<div style='height:0.2rem'></div>", unsafe_allow_html=True)

    # ── Tabs ──
    tab1, tab2, tab_height, tab3 = st.tabs([
        "Ash RGB (SSEC)",
        "SO2 RGB (SSEC)",
        "📏 Altura de pluma (VOLCAT)",
        "VAA Advisories",
    ])

    def _ssec_png_download(img_rgba, filename: str, button_label: str, key: str):
        """Boton de descarga para imagen SSEC (RGBA -> PNG con alpha aplicado)."""
        if img_rgba is None:
            return
        import io as _io
        from PIL import Image as _PIL
        rgb = img_rgba[:, :, :3].copy()
        alpha = img_rgba[:, :, 3:4].astype(np.float32) / 255.0
        rgb = (rgb.astype(np.float32) * alpha).astype(np.uint8)
        buf = _io.BytesIO()
        _PIL.fromarray(rgb).save(buf, format="PNG", optimize=True)
        png = buf.getvalue()
        size_kb = len(png) / 1024
        size_str = f"{size_kb/1024:.1f} MB" if size_kb >= 1024 else f"{size_kb:.0f} KB"
        st.download_button(
            f"⬇ {button_label} ({size_str})",
            data=png, file_name=filename, mime="image/png",
            key=key, use_container_width=True,
        )

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
                _ssec_png_download(
                    ash_img,
                    filename=f"volcat_ssec_ash_rgb_{ash_ts or 'latest'}.png",
                    button_label="Descargar Ash RGB SSEC (PNG)",
                    key="dl_volcat_ash",
                )
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
                _ssec_png_download(
                    so2_img,
                    filename=f"volcat_ssec_so2_rgb_{so2_ts or 'latest'}.png",
                    button_label="Descargar SO2 RGB SSEC (PNG)",
                    key="dl_volcat_so2",
                )
            else:
                st.error("No se pudo descargar la imagen SO2 RGB de SSEC")
        with col_leg2:
            ash_so2_legend()

    # ── TAB: Altura de pluma VOLCAT (Pavolonis 2013, ±1-2 km) ──
    with tab_height:
        _render_height_section(key_suffix="tab")

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
