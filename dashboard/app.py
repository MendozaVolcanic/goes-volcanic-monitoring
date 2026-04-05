"""GOES Volcanic Monitoring Dashboard - Chile.

Dashboard principal Streamlit para monitoreo volcánico NRT
usando GOES-19 (Ash RGB, BTD, SO2, hot spots).

Ejecutar: streamlit run dashboard/app.py
"""

import sys
from pathlib import Path

# Agregar raíz del proyecto al path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st

st.set_page_config(
    page_title="GOES Volcanic Monitoring - Chile",
    page_icon="🌋",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Sidebar ──────────────────────────────────────────────────────
st.sidebar.title("GOES Volcanic Monitor")
st.sidebar.markdown("**Chile - 43 volcanes**")
st.sidebar.markdown("---")

page = st.sidebar.radio(
    "Navegación",
    ["Mapa General", "Ash RGB Viewer", "Detalle Volcán"],
    index=0,
)

st.sidebar.markdown("---")
st.sidebar.markdown(
    """
    **Fuente:** GOES-19 (GOES-East)
    **Datos:** AWS S3 `noaa-goes19`
    **Resolución:** 2 km IR
    **Cadencia:** 10 min Full Disk
    """
)
st.sidebar.markdown("---")
st.sidebar.caption(
    "[GitHub](https://github.com/MendozaVolcanic/goes-volcanic-monitoring) | SERNAGEOMIN"
)

# ── Pages ────────────────────────────────────────────────────────
if page == "Mapa General":
    from dashboard.pages.overview import render
    render()
elif page == "Ash RGB Viewer":
    from dashboard.pages.ash_viewer import render
    render()
elif page == "Detalle Volcán":
    from dashboard.pages.volcano_detail import render
    render()
