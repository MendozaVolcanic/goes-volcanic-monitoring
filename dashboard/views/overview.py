"""Página Overview: Mapa de Chile con 43 volcanes + estado."""

import streamlit as st
import folium
from streamlit_folium import st_folium

from src.volcanos import CATALOG, PRIORITY_VOLCANOES, get_by_zone


# Colores por zona volcánica
ZONE_COLORS = {
    "norte": "#e74c3c",    # rojo
    "centro": "#f39c12",   # naranja
    "sur": "#27ae60",      # verde
    "austral": "#3498db",  # azul
}

# Iconos por ranking de peligrosidad
def _get_icon_color(v):
    """Color del marcador según ranking SERNAGEOMIN."""
    if v.name in PRIORITY_VOLCANOES:
        return "red"
    if v.ranking > 0 and v.ranking <= 10:
        return "orange"
    if v.ranking > 10:
        return "blue"
    return "gray"


def render():
    st.title("Mapa de Volcanes Activos - Chile")
    st.markdown(
        "43 volcanes monitoreados por SERNAGEOMIN | "
        "Datos GOES-19 cada 10 minutos | "
        "Fuente: AWS S3 `noaa-goes19`"
    )

    # ── Filtros ──
    col1, col2 = st.columns([1, 3])
    with col1:
        zone_filter = st.multiselect(
            "Zona volcánica",
            ["norte", "centro", "sur", "austral"],
            default=["norte", "centro", "sur", "austral"],
        )
        show_priority = st.checkbox("Solo prioritarios", value=False)

    # Filtrar volcanes
    volcanoes = [v for v in CATALOG if v.zone in zone_filter]
    if show_priority:
        volcanoes = [v for v in volcanoes if v.name in PRIORITY_VOLCANOES]

    # ── KPIs ──
    with col2:
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Volcanes", len(volcanoes))
        k2.metric("Zona Norte", len([v for v in volcanoes if v.zone == "norte"]))
        k3.metric("Zona Centro-Sur", len([v for v in volcanoes if v.zone in ("centro", "sur")]))
        k4.metric("Zona Austral", len([v for v in volcanoes if v.zone == "austral"]))

    # ── Mapa ──
    m = folium.Map(
        location=[-35.0, -71.0],
        zoom_start=5,
        tiles="CartoDB dark_matter",
    )

    # Agregar volcanes
    for v in volcanoes:
        popup_html = f"""
        <b>{v.name}</b><br>
        Elevación: {v.elevation} m<br>
        Región: {v.region}<br>
        Zona: {v.zone}<br>
        Ranking SERNAGEOMIN: {v.ranking if v.ranking > 0 else 'Sin ranking'}<br>
        Coords: {v.lat:.2f}, {v.lon:.2f}
        """
        folium.Marker(
            location=[v.lat, v.lon],
            popup=folium.Popup(popup_html, max_width=250),
            tooltip=f"{v.name} ({v.elevation}m)",
            icon=folium.Icon(
                color=_get_icon_color(v),
                icon="fire",
                prefix="fa",
            ),
        ).add_to(m)

    # Leyenda
    legend_html = """
    <div style="position: fixed; bottom: 30px; left: 30px; z-index: 1000;
                background: rgba(0,0,0,0.7); padding: 10px; border-radius: 5px;
                color: white; font-size: 12px;">
        <b>Volcanes Chile</b><br>
        <i class="fa fa-circle" style="color:red"></i> Prioritarios (8)<br>
        <i class="fa fa-circle" style="color:orange"></i> Ranking 1-10<br>
        <i class="fa fa-circle" style="color:blue"></i> Ranking 11+<br>
        <i class="fa fa-circle" style="color:gray"></i> Sin ranking
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))

    st_folium(m, width=None, height=650, returned_objects=[])

    # ── Tabla de volcanes ──
    with st.expander("Tabla completa de volcanes", expanded=False):
        import pandas as pd

        df = pd.DataFrame([
            {
                "Nombre": v.name,
                "Lat": v.lat,
                "Lon": v.lon,
                "Elevación (m)": v.elevation,
                "Zona": v.zone,
                "Región": v.region,
                "Ranking": v.ranking if v.ranking > 0 else "-",
                "Prioritario": "Si" if v.name in PRIORITY_VOLCANOES else "",
            }
            for v in volcanoes
        ])
        st.dataframe(df, use_container_width=True, hide_index=True)
