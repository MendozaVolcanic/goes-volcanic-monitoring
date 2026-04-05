"""GOES Volcanic Monitoring Dashboard - Chile.

Dashboard NRT de monitoreo volcánico usando GOES-19 (GOES-East).
Ash RGB, detección de ceniza, SO2, hot spots para 43 volcanes chilenos.

Ejecutar: streamlit run dashboard/app.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
from dashboard.style import inject_css

st.set_page_config(
    page_title="GOES Volcanic Monitor - Chile",
    page_icon="🌋",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_css()

# ── Sidebar ──────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        '<div style="text-align:center; padding: 1rem 0 0.5rem 0;">'
        '<span style="font-size:2.5rem;">🌋</span><br>'
        '<span style="font-size:1.2rem; font-weight:700; '
        'background:linear-gradient(90deg,#ff6b6b,#ffa07a);'
        '-webkit-background-clip:text;-webkit-text-fill-color:transparent;">'
        "GOES Monitor</span><br>"
        '<span style="color:#667; font-size:0.8rem;">Chile - 43 volcanes</span>'
        "</div>",
        unsafe_allow_html=True,
    )
    st.markdown("---")

    page = st.radio(
        "Navegacion",
        ["Mapa General", "Ash RGB Viewer", "Detalle Volcan"],
        index=0,
        label_visibility="collapsed",
    )

    st.markdown("---")

    st.markdown(
        '<div style="font-size:0.78rem; color:#556; line-height:1.8;">'
        "<b>Satelite:</b> GOES-19 (East)<br>"
        "<b>Fuente:</b> AWS S3<br>"
        "<b>Resolucion IR:</b> 2 km<br>"
        "<b>Cadencia:</b> 10 min<br>"
        "</div>",
        unsafe_allow_html=True,
    )

    st.markdown("---")
    st.caption(
        "[GitHub](https://github.com/MendozaVolcanic/goes-volcanic-monitoring)"
        " &middot; SERNAGEOMIN"
    )

# ── Routing ──────────────────────────────────────────────────────
if page == "Mapa General":
    from dashboard.views.overview import render
    render()
elif page == "Ash RGB Viewer":
    from dashboard.views.ash_viewer import render
    render()
elif page == "Detalle Volcan":
    from dashboard.views.volcano_detail import render
    render()
