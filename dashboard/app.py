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

# IMPORTANTE: st.set_page_config debe ser la PRIMERA llamada Streamlit.
# NO podemos llamar st.query_params antes — eso crashea con
# "set_page_config must be the first Streamlit command".
st.set_page_config(
    page_title="GOES Volcanic Monitor - Chile",
    page_icon="🌋",
    layout="wide",
    initial_sidebar_state="expanded",  # CSS lo oculta si ?fullscreen=1
)

inject_css()

# Ahora SI podemos leer query params
_fullscreen = st.query_params.get("fullscreen") == "1"

# CSS extra cuando fullscreen=1: oculta sidebar completamente y maximiza area
if _fullscreen:
    st.markdown(
        """
        <style>
          [data-testid="stSidebar"] { display: none !important; }
          [data-testid="stHeader"] { background: rgba(0,0,0,0); height: 0; }
          .block-container {
            padding: 0.4rem !important;
            max-width: 100% !important;
          }
        </style>
        """,
        unsafe_allow_html=True,
    )
    # Boton SALIR fullscreen — solo se muestra si NO estamos tambien en
    # modo TV puro (en TV puro hay un boton unico "✖ Salir" que limpia
    # ambos params, asi evitamos mostrar 2 botones de salir apilados).
    _tv_active = st.query_params.get("tv", "") in ("1", "mosaico", "volcan")
    if not _tv_active:
        st.markdown(
            """
            <style>
              [data-testid="stButton"] > button[kind="secondary"] {
                padding: 0.15rem 0.6rem !important;
                font-size: 0.72rem !important;
                min-height: unset !important;
                height: 26px !important;
              }
            </style>
            """,
            unsafe_allow_html=True,
        )
        c_exit_fs, c_rest_fs = st.columns([1, 14])
        with c_exit_fs:
            if st.button("✖ Salir fullscreen", key="btn_exit_fs",
                         use_container_width=True):
                if "fullscreen" in st.query_params:
                    del st.query_params["fullscreen"]
                st.rerun()

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
        "🔴 En Vivo", "🛡 Modo Guardia", "🗺 4 Zonas Full Screen",
        "🔀 Comparador",
        "🚨 Modo Evento", "📅 Heatmap actividad",
        "🔁 Replay reciente",
        "Ash RGB Viewer (L1b + BTD)", "VOLCAT (SSEC)",
        "Animacion (RAMMB)", "📈 Series de tiempo",
    ]
    PAGE_SLUGS = {
        "live": "🔴 En Vivo", "guardia": "🛡 Modo Guardia",
        "zonas": "🗺 4 Zonas Full Screen",
        "comparador": "🔀 Comparador", "evento": "🚨 Modo Evento",
        "heatmap": "📅 Heatmap actividad",
        "replay": "🔁 Replay reciente",
        "ash": "Ash RGB Viewer (L1b + BTD)",
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

    # ── Modo Fullscreen ──────────────────────────────────────────
    st.markdown("---")
    fs_link = (
        f'<a href="?vista={_slug_for_page}&fullscreen=1" target="_top" '
        f'style="display:block; text-align:center; '
        f'background:linear-gradient(135deg, #CC3311, #EE7733); '
        f'color:white; padding:0.55rem 0.8rem; border-radius:6px; '
        f'text-decoration:none; font-weight:700; font-size:0.85rem;">'
        f'🖥 Modo Pantalla Completa</a>'
        if _slug_for_page else ""
    )
    st.markdown(fs_link, unsafe_allow_html=True)
    st.caption("Oculta este menú y maximiza el área del mapa. "
               "Botón ✖ arriba a la derecha para salir.")

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
elif page == "🗺 4 Zonas Full Screen":
    from dashboard.views.zonas_fullscreen import render
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
elif page == "🔁 Replay reciente":
    from dashboard.views.replay_reciente import render
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
