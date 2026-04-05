"""Pagina Overview: Mapa de Chile con 43 volcanes."""

import pandas as pd
import streamlit as st
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium

from dashboard.style import header, kpi_card
from src.volcanos import CATALOG, PRIORITY_VOLCANOES


ZONE_LABELS = {
    "norte": "Zona Norte",
    "centro": "Zona Centro",
    "sur": "Zona Sur",
    "austral": "Zona Austral",
}

ZONE_COLORS_HEX = {
    "norte": "#e74c3c",
    "centro": "#f39c12",
    "sur": "#27ae60",
    "austral": "#3498db",
}


def _marker_color(v):
    if v.name in PRIORITY_VOLCANOES:
        return "red"
    if 0 < v.ranking <= 10:
        return "orange"
    if v.ranking > 10:
        return "blue"
    return "gray"


def _build_map(volcanoes):
    m = folium.Map(
        location=[-36.0, -71.5],
        zoom_start=5,
        tiles="CartoDB dark_matter",
        control_scale=True,
    )

    for v in volcanoes:
        color = _marker_color(v)
        zone_color = ZONE_COLORS_HEX.get(v.zone, "#888")

        popup_html = f"""
        <div style="font-family:sans-serif; min-width:180px;">
            <h4 style="margin:0 0 6px 0; color:#333;">{v.name}</h4>
            <table style="font-size:12px; color:#555; line-height:1.6;">
                <tr><td><b>Elevacion</b></td><td>{v.elevation:,} m</td></tr>
                <tr><td><b>Region</b></td><td>{v.region}</td></tr>
                <tr><td><b>Zona</b></td><td>
                    <span style="color:{zone_color}; font-weight:600;">
                        {ZONE_LABELS.get(v.zone, v.zone)}
                    </span></td></tr>
                <tr><td><b>Ranking</b></td><td>{v.ranking if v.ranking else '—'}</td></tr>
                <tr><td><b>Coords</b></td><td>{v.lat:.3f}, {v.lon:.3f}</td></tr>
            </table>
        </div>
        """

        folium.CircleMarker(
            location=[v.lat, v.lon],
            radius=8 if v.name in PRIORITY_VOLCANOES else 5,
            color="white",
            weight=1,
            fill=True,
            fill_color=zone_color,
            fill_opacity=0.85,
            popup=folium.Popup(popup_html, max_width=250),
            tooltip=f"{v.name} ({v.elevation:,} m)",
        ).add_to(m)

    # Leyenda
    legend_html = """
    <div style="position:fixed; bottom:25px; left:25px; z-index:1000;
                background:rgba(14,17,23,0.92); padding:12px 16px; border-radius:8px;
                color:#ccc; font-size:12px; border:1px solid rgba(255,255,255,0.08);
                backdrop-filter:blur(8px);">
        <div style="font-weight:700; margin-bottom:6px; color:#fafafa;">Zonas Volcanicas</div>
        <div><span style="color:#e74c3c;">&#9679;</span> Norte</div>
        <div><span style="color:#f39c12;">&#9679;</span> Centro</div>
        <div><span style="color:#27ae60;">&#9679;</span> Sur</div>
        <div><span style="color:#3498db;">&#9679;</span> Austral</div>
        <div style="margin-top:6px; border-top:1px solid rgba(255,255,255,0.1); padding-top:6px;">
            <span style="font-size:14px;">&#9679;</span> = Prioritario
        </div>
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))

    return m


def render():
    header(
        "Red de Volcanes Activos — Chile",
        "43 volcanes monitoreados por SERNAGEOMIN &middot; GOES-19 cada 10 min",
    )

    # ── Filtros ──
    col_filter, col_spacer, col_kpis = st.columns([1.2, 0.1, 3])

    with col_filter:
        zone_filter = st.multiselect(
            "Filtrar por zona",
            options=list(ZONE_LABELS.keys()),
            default=list(ZONE_LABELS.keys()),
            format_func=lambda z: ZONE_LABELS[z],
        )
        show_priority = st.toggle("Solo prioritarios", value=False)

    volcanoes = [v for v in CATALOG if v.zone in zone_filter]
    if show_priority:
        volcanoes = [v for v in volcanoes if v.name in PRIORITY_VOLCANOES]

    with col_kpis:
        k1, k2, k3, k4 = st.columns(4)
        with k1:
            kpi_card(len(volcanoes), "Total volcanes")
        with k2:
            kpi_card(
                len([v for v in volcanoes if v.zone == "norte"]),
                "Zona Norte",
            )
        with k3:
            kpi_card(
                len([v for v in volcanoes if v.zone in ("centro", "sur")]),
                "Centro-Sur",
            )
        with k4:
            kpi_card(
                len([v for v in volcanoes if v.zone == "austral"]),
                "Zona Austral",
            )

    # ── Mapa ──
    st.markdown("<div style='height:0.8rem'></div>", unsafe_allow_html=True)
    m = _build_map(volcanoes)
    st_folium(m, width=None, height=620, returned_objects=[])

    # ── Tabla ──
    with st.expander("Tabla completa de volcanes"):
        df = pd.DataFrame([
            {
                "Nombre": v.name,
                "Elevacion (m)": f"{v.elevation:,}",
                "Zona": ZONE_LABELS.get(v.zone, v.zone),
                "Region": v.region,
                "Ranking": v.ranking if v.ranking else "—",
                "Lat": f"{v.lat:.3f}",
                "Lon": f"{v.lon:.3f}",
                "Prioritario": "Si" if v.name in PRIORITY_VOLCANOES else "",
            }
            for v in volcanoes
        ])
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Prioritario": st.column_config.TextColumn(width="small"),
                "Ranking": st.column_config.TextColumn(width="small"),
            },
        )
