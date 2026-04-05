"""Pagina Overview: Mapa de Chile con 43 volcanes."""

import pandas as pd
import streamlit as st
import folium
from streamlit_folium import st_folium

from dashboard.style import ZONE_HEX, header, kpi_card
from src.volcanos import CATALOG, PRIORITY_VOLCANOES


ZONE_LABELS = {
    "norte": "Zona Norte",
    "centro": "Zona Centro",
    "sur": "Zona Sur",
    "austral": "Zona Austral",
}


def _build_map(volcanoes):
    m = folium.Map(
        location=[-36.0, -71.5],
        zoom_start=5,
        tiles="CartoDB dark_matter",
        control_scale=True,
    )

    for v in volcanoes:
        zone_color = ZONE_HEX.get(v.zone, "#888")
        is_priority = v.name in PRIORITY_VOLCANOES
        radius = 9 if is_priority else 5
        weight = 2 if is_priority else 1

        popup_html = f"""
        <div style="font-family:system-ui; min-width:180px;">
            <h4 style="margin:0 0 6px 0; color:#222;">{v.name}</h4>
            <table style="font-size:12px; color:#555; line-height:1.7;">
                <tr><td style="padding-right:10px;"><b>Elevacion</b></td><td>{v.elevation:,} m</td></tr>
                <tr><td><b>Zona</b></td><td style="color:{zone_color}; font-weight:600;">
                    {ZONE_LABELS.get(v.zone, v.zone)}</td></tr>
                <tr><td><b>Region</b></td><td>{v.region}</td></tr>
                <tr><td><b>Ranking</b></td><td>{f'#{v.ranking}' if v.ranking else '—'}</td></tr>
            </table>
        </div>
        """

        folium.CircleMarker(
            location=[v.lat, v.lon],
            radius=radius,
            color="white",
            weight=weight,
            fill=True,
            fill_color=zone_color,
            fill_opacity=0.85,
            popup=folium.Popup(popup_html, max_width=240),
            tooltip=f"{v.name} · {v.elevation:,} m",
        ).add_to(m)

    # Leyenda (colorblind-safe)
    legend_html = """
    <div style="position:fixed; bottom:25px; left:25px; z-index:1000;
                background:rgba(12,15,22,0.92); padding:12px 16px; border-radius:8px;
                color:#aab; font-size:11px; border:1px solid rgba(255,255,255,0.06);
                line-height:1.8;">
        <div style="font-weight:700; margin-bottom:4px; color:#ddd; font-size:12px;">Zonas Volcanicas</div>
        <div><span style="color:#CC3311;">&#9679;</span> Norte (14)</div>
        <div><span style="color:#EE7733;">&#9679;</span> Centro (8)</div>
        <div><span style="color:#009988;">&#9679;</span> Sur (16)</div>
        <div><span style="color:#0077BB;">&#9679;</span> Austral (5)</div>
        <div style="margin-top:5px; border-top:1px solid rgba(255,255,255,0.08);
                    padding-top:5px; color:#889;">
            Grande = prioritario (8)
        </div>
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))

    return m


def render():
    header(
        "Monitoreo de 43 volcanes activos en Chile",
        "Red Nacional de Vigilancia Volcanica &middot; SERNAGEOMIN &middot; GOES-19 Full Disk cada 10 min",
    )

    # ── Filtros + KPIs ──
    col_f, _, col_k = st.columns([1.2, 0.1, 3])

    with col_f:
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

    n_total = len(volcanoes)
    n_norte = len([v for v in volcanoes if v.zone == "norte"])
    n_cs = len([v for v in volcanoes if v.zone in ("centro", "sur")])
    n_aust = len([v for v in volcanoes if v.zone == "austral"])

    with col_k:
        k1, k2, k3, k4 = st.columns(4)
        with k1:
            kpi_card(str(n_total), "Total", delta="8 prioritarios" if not show_priority else "")
        with k2:
            kpi_card(str(n_norte), "Norte")
        with k3:
            kpi_card(str(n_cs), "Centro-Sur")
        with k4:
            kpi_card(str(n_aust), "Austral")

    # ── Mapa ──
    st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
    m = _build_map(volcanoes)
    st_folium(m, width=None, height=600, returned_objects=[])

    # ── Tabla ──
    with st.expander("Tabla completa de volcanes"):
        df = pd.DataFrame([
            {
                "Nombre": v.name,
                "Elevacion (m)": f"{v.elevation:,}",
                "Zona": ZONE_LABELS.get(v.zone, v.zone),
                "Region": v.region,
                "Ranking": f"#{v.ranking}" if v.ranking else "—",
                "Lat": f"{v.lat:.3f}",
                "Lon": f"{v.lon:.3f}",
            }
            for v in volcanoes
        ])
        st.dataframe(df, use_container_width=True, hide_index=True)
