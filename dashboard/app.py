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
              /* Garantizar que el boton de salir quede por encima del
                 contenido y siempre clickeable en cualquier vista */
              [data-testid="stButton"] {
                position: relative !important;
                z-index: 9999 !important;
              }
              [data-testid="stButton"] > button {
                pointer-events: auto !important;
              }
            </style>
            """,
            unsafe_allow_html=True,
        )
        # Salir fullscreen: helper hace clear+set query_params.
        # Pasamos los params actuales SALVO fullscreen.
        from dashboard.map_helpers import render_top_navigation_button
        _qp_keep = {k: v for k, v in st.query_params.items() if k != "fullscreen"}
        _qs = "&".join(f"{k}={v}" for k, v in _qp_keep.items())
        if not _qs:
            _qs = "vista=operacional"  # fallback si no hay nada
        render_top_navigation_button(
            "✖ Salir fullscreen",
            _qs,
            key="btn_exit_fs",
        )

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
    # ── Build version marker (verifica que Streamlit Cloud sirve la version
    # actual del repo, no una vieja cacheada). Si no ves este texto despues
    # de un push, la app sigue dormant y hay que hacer Reboot manual.
    BUILD_SHA = "build-2026-05-21-volcat-reorder-zona"
    st.caption(f"🔖 `{BUILD_SHA}`")
    st.markdown("---")

    # ── Permalinks: leer ?vista= de la URL ───────────────────────
    # Mapa: query param 'vista' -> entry visible en el sidebar.
    # Permite compartir https://...?vista=guardia&volcan=Lascar
    # NOTA: '4 Zonas Full Screen' eliminada del menu — su funcionalidad
    # vive embebida en Modo Guardia → sub-tab 'Por Zona Volcánica' (mismo
    # codigo en zonas_fullscreen.py, que Guardia importa). Slug 'zonas'
    # se redirige a guardia abajo para no romper bookmarks.
    PAGE_OPTIONS = [
        "🌎 Vista Operacional", "🛡 Modo Guardia",
        "🔀 Comparador",
        "🚨 Modo Evento", "📅 Heatmap actividad",
        "🔁 Replay reciente", "📅 Backfill historico",
        "🌡 Ash + BTD (temperaturas K)", "📏 VOLCAT (altura pluma)",
        "🎞 Loops descargables", "📈 Series de tiempo",
    ]
    PAGE_SLUGS = {
        "operacional": "🌎 Vista Operacional",
        "guardia": "🛡 Modo Guardia",
        "comparador": "🔀 Comparador", "evento": "🚨 Modo Evento",
        "heatmap": "📅 Heatmap actividad",
        "replay": "🔁 Replay reciente",
        "backfill": "📅 Backfill historico",
        "ash": "🌡 Ash + BTD (temperaturas K)",
        "volcat": "📏 VOLCAT (altura pluma)",
        "loops": "🎞 Loops descargables",
        "series": "📈 Series de tiempo",
    }
    qp = st.query_params
    # Compat: redirigir slugs viejos sin romper bookmarks/permalinks
    _SLUG_REDIRECTS = {
        "zonas": "guardia",       # 4 Zonas Full Screen → sub-tab de Guardia
        "live": "operacional",    # 🔴 En Vivo → 🌎 Vista Operacional
        "animacion": "loops",     # Animacion RAMMB → 🎞 Loops descargables
    }
    _curr = qp.get("vista")
    if _curr in _SLUG_REDIRECTS:
        st.query_params["vista"] = _SLUG_REDIRECTS[_curr]
        qp = st.query_params

    # BUG histórico (mayo 2026): `index=initial_idx` en st.radio SOLO
    # se aplica en el PRIMER render. En reruns posteriores Streamlit usa
    # `st.session_state["nav_page"]` que persiste con el ULTIMO click.
    # Consecuencia: deep-linking (?vista=evento), browser back/forward,
    # o cualquier cambio de URL programatico NO actualizaba el radio.
    #
    # FIX (intento 2, definitivo): solo sincronizar URL -> session_state
    # cuando la URL cambio EXTERNAMENTE entre dos renders consecutivos
    # (ej. deep link, browser back/forward, redirect). Si la URL no
    # cambio, dejar que session_state gane — eso preserva el click del
    # usuario en el radio (que ocurre ANTES de que el bottom de app.py
    # escriba la URL nueva).
    #
    # El intento 1 sincronizaba EN CADA RERUN, creando un feedback loop
    # que anulaba todos los clicks del sidebar (se restauraba el valor
    # viejo de URL antes de que la escritura de URL tomara efecto).
    _url_vista = qp.get("vista", "").lower()
    _last_url_vista = st.session_state.get("__last_url_vista", "")
    if _url_vista != _last_url_vista and _url_vista in PAGE_SLUGS:
        # URL cambio externamente — adoptar la URL como verdad.
        st.session_state["nav_page"] = PAGE_SLUGS[_url_vista]
    # Marcar URL conocida para el proximo rerun. Hacerlo SIEMPRE (no solo
    # cuando cambio) para que la primera vez tambien quede registrada.
    st.session_state["__last_url_vista"] = _url_vista

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
    # st.link_button (anchor HTML interno de Streamlit) en vez de
    # <a target="_top"> manual: el iframe sandbox de Streamlit Cloud
    # bloquea target="_top" en muchos casos, dejando el boton
    # inclickeable. link_button funciona porque Streamlit lo renderiza
    # con la logica de navegacion correcta para su iframe.
    st.markdown("---")
    if _slug_for_page:
        st.link_button(
            "🖥 Modo Pantalla Completa",
            url=f"?vista={_slug_for_page}&fullscreen=1",
            type="primary", width='stretch',
        )
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
    with st.expander("📋 Por hacer", expanded=False):
        st.markdown(
            "<div style='font-size:0.74rem; color:#7a8a9a; line-height:1.5;'>"
            "<b style='color:#aabbcc;'>Mirror en otro proveedor</b> "
            "<span style='color:#556677;'>(prioridad alta)</span><br>"
            "Levantar copia del dashboard en HuggingFace Spaces o Render para "
            "redundancia. Si Streamlit Cloud cae, el mirror sigue. Ambos se "
            "actualizan solos desde el mismo repo. Costo: $0 en HF Spaces "
            "(16 GB RAM, 2 vCPU, free).<br>"
            "<i style='color:#556677;'>Por que un mirror funciona: corre en "
            "otra maquina, otro OS, version de Python que vos elegis. Bugs "
            "de infra de Streamlit Cloud (como el race condition de Python "
            "3.14 que causo los crashes de mayo 2026) no afectan el mirror.</i>"
            "<br><br>"
            "<b style='color:#aabbcc;'>Otras ideas</b><br>"
            "&bull; Auto-spawn del cron de animation_cache cuando GOES "
            "publica nuevo scan (en vez de cada hora fija).<br>"
            "&bull; Alertas Telegram/email cuando hot spot supera umbral.<br>"
            "&bull; Export PDF de Modo Evento con un click.<br>"
            "&bull; Mirror del dataset en S3 propio (independencia total de "
            "RAMMB)."
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
if page == "🌎 Vista Operacional":
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
elif page == "🔁 Replay reciente":
    from dashboard.views.replay_reciente import render
    render()
elif page == "📅 Backfill historico":
    from dashboard.views.backfill_viewer import render
    render()
elif page == "🌡 Ash + BTD (temperaturas K)":
    from dashboard.views.ash_viewer import render
    render()
elif page == "📏 VOLCAT (altura pluma)":
    from dashboard.views.volcat_viewer import render
    render()
elif page == "🎞 Loops descargables":
    from dashboard.views.rammb_viewer import render
    render()
elif page == "📈 Series de tiempo":
    from dashboard.views.timeseries_viewer import render
    render()
