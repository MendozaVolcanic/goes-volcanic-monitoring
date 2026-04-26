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
        '<div style="text-align:center; padding: 1.5rem 0 0.8rem 0;">'
        '<div style="font-size:3rem; line-height:1;">🌋</div>'
        '<div style="font-size:1.3rem; font-weight:800; margin-top:0.3rem; '
        'background:linear-gradient(135deg, #CC3311, #EE7733);'
        '-webkit-background-clip:text;-webkit-text-fill-color:transparent;">'
        "GOES Monitor</div>"
        '<div style="color:#556677; font-size:0.75rem; margin-top:0.2rem; '
        'letter-spacing:0.1em; text-transform:uppercase;">Chile &middot; 43 volcanes</div>'
        "</div>",
        unsafe_allow_html=True,
    )
    st.markdown("---")

    # ── Permalinks: leer ?vista= de la URL ───────────────────────
    # Mapa: query param 'vista' -> entry visible en el sidebar.
    # Permite compartir https://...?vista=guardia&volcan=Lascar
    PAGE_OPTIONS = [
        "🔴 En Vivo", "🛡 Modo Guardia", "🔀 Comparador",
        "🚨 Modo Evento", "📅 Heatmap actividad",
        "🔁 Replay Calbuco 2015",
        "Mapa General", "Ash RGB Viewer (L1b + BTD)", "VOLCAT (SSEC)",
        "Animacion (RAMMB)", "📈 Series de tiempo",
    ]
    PAGE_SLUGS = {
        "live": "🔴 En Vivo", "guardia": "🛡 Modo Guardia",
        "comparador": "🔀 Comparador", "evento": "🚨 Modo Evento",
        "heatmap": "📅 Heatmap actividad",
        "calbuco": "🔁 Replay Calbuco 2015",
        "mapa": "Mapa General", "ash": "Ash RGB Viewer (L1b + BTD)",
        "volcat": "VOLCAT (SSEC)", "animacion": "Animacion (RAMMB)",
        "series": "📈 Series de tiempo",
    }
    qp = st.query_params
    initial_idx = 0
    if "vista" in qp:
        slug = qp["vista"].lower()
        if slug in PAGE_SLUGS and PAGE_SLUGS[slug] in PAGE_OPTIONS:
            initial_idx = PAGE_OPTIONS.index(PAGE_SLUGS[slug])

    page = st.radio(
        "Navegacion",
        PAGE_OPTIONS,
        index=initial_idx,
        label_visibility="collapsed",
        key="nav_page",
    )

    # Escribir el slug actual a la URL (los demas params se preservan)
    _slug_for_page = next((s for s, p in PAGE_SLUGS.items() if p == page), None)
    if _slug_for_page and qp.get("vista") != _slug_for_page:
        st.query_params["vista"] = _slug_for_page

    st.markdown("---")

    st.markdown(
        '<div style="background:rgba(17,24,34,0.5); border-radius:8px; '
        'padding:0.8rem 1rem; font-size:0.76rem; color:#5a6a7a; line-height:2;">'
        '<div style="font-size:0.68rem; text-transform:uppercase; letter-spacing:0.08em; '
        'color:#445566; font-weight:700; margin-bottom:0.3rem;">Fuente de datos</div>'
        "<b style='color:#7a8a9a;'>Satelite</b> &nbsp;GOES-19 (East)<br>"
        "<b style='color:#7a8a9a;'>Fuente</b> &nbsp;AWS S3 (publico)<br>"
        "<b style='color:#7a8a9a;'>Resolucion</b> &nbsp;2 km (IR)<br>"
        "<b style='color:#7a8a9a;'>Cadencia</b> &nbsp;10 min (Full Disk)<br>"
        "</div>",
        unsafe_allow_html=True,
    )

    st.markdown("---")
    st.markdown(
        '<div style="text-align:center; font-size:0.72rem; color:#445566;">'
        '<a href="https://github.com/MendozaVolcanic/goes-volcanic-monitoring" '
        'style="color:#667788; text-decoration:none;">GitHub</a>'
        " &middot; SERNAGEOMIN<br>"
        '<span style="font-size:0.65rem; color:#334455; margin-top:0.3rem; display:inline-block;">'
        "v1.0 &middot; GOES-19 ABI L1b</span>"
        "</div>",
        unsafe_allow_html=True,
    )

# ── Routing ──────────────────────────────────────────────────────
if page == "🔴 En Vivo":
    from dashboard.views.live_viewer import render
    render()
elif page == "🛡 Modo Guardia":
    from dashboard.views.modo_guardia import render
    render()
elif page == "🔀 Comparador":
    from dashboard.views.comparador import render
    render()
elif page == "🚨 Modo Evento":
    from dashboard.views.modo_evento import render
    render()
elif page == "📅 Heatmap actividad":
    from dashboard.views.heatmap_actividad import render
    render()
elif page == "🔁 Replay Calbuco 2015":
    from dashboard.views.replay_calbuco import render
    render()
elif page == "Mapa General":
    from dashboard.views.overview import render
    render()
elif page == "Ash RGB Viewer (L1b + BTD)":
    from dashboard.views.ash_viewer import render
    render()
elif page == "VOLCAT (SSEC)":
    from dashboard.views.volcat_viewer import render
    render()
elif page == "Animacion (RAMMB)":
    from dashboard.views.rammb_viewer import render
    render()
elif page == "📈 Series de tiempo":
    from dashboard.views.timeseries_viewer import render
    render()
