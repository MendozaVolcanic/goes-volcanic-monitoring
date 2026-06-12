"""CSS y estilos globales del dashboard.

Principios de visualizacion aplicados (data-visualization skill):
- Paleta colorblind-safe (#0077BB, #33BBEE, #009988, #EE7733, #CC3311)
- Titulos como insights, no descripciones
- Maximos 5-7 colores por grafico
- Anotaciones directas en datos clave
"""

import streamlit as st

# ── Paleta colorblind-safe (Tol bright) ──────────────────────────
# Ref: Paul Tol's colorblind-safe qualitative palette
COLORS = {
    "blue":    "#0077BB",
    "cyan":    "#33BBEE",
    "teal":    "#009988",
    "orange":  "#EE7733",
    "red":     "#CC3311",
    "magenta": "#EE3377",
    "grey":    "#BBBBBB",
}

# Colores semanticos para el dashboard
C_ASH = "#CC3311"       # ceniza = rojo
C_SO2 = "#009988"       # SO2 = teal
C_CLEAR = "#0077BB"     # sin ceniza = azul
C_WARN = "#EE7733"      # warning = naranja
C_ACCENT = "#33BBEE"    # accent = cyan
C_MUTED = "#667788"     # texto secundario

# Zonas volcanicas
ZONE_HEX = {
    "norte":  "#CC3311",
    "centro": "#EE7733",
    "sur":    "#009988",
    "austral":"#0077BB",
}

# Colorscale BTD divergente (colorblind-safe)
BTD_COLORSCALE = [
    [0.0, "#CC3311"],   # muy negativo = ceniza
    [0.25, "#EE7733"],  # ligeramente negativo
    [0.5,  "#f5f5f5"],  # neutro
    [0.75, "#33BBEE"],  # positivo
    [1.0,  "#0077BB"],  # muy positivo = nubes met.
]

# Colorscale confianza (secuencial)
CONF_COLORSCALE = [
    [0.0,  "rgba(14,17,23,0.9)"],  # ninguna
    [0.33, "#EE7733"],              # baja
    [0.66, "#CC3311"],              # media
    [1.0,  "#880000"],              # alta
]


CUSTOM_CSS = """
<style>
/* ══════════════════════════════════════════════
   GOES Volcanic Monitor — Dark Volcanic Theme
   ══════════════════════════════════════════════ */

/* ── Global ── */
/* Compactar padding superior para maximizar area de mapas */
.block-container { padding-top: 0.6rem !important; padding-bottom: 1rem !important; }
.stApp { background: #0a0d14; }

/* Reducir el gap por defecto entre stVerticalBlock children — Streamlit
   pone 1rem entre cada widget que se acumula en paginas largas */
div[data-testid="stVerticalBlock"] > div { gap: 0.55rem !important; }

/* ── Header ── (super-compacto: ~50% menos altura que original) */
.main-header {
    background: linear-gradient(135deg, #0f1520 0%, #161d2e 50%, #1a1225 100%);
    padding: 0.35rem 0.9rem;
    border-radius: 6px;
    margin-bottom: 0.35rem;
    border: 1px solid rgba(204,51,17,0.15);
    border-left: 3px solid #CC3311;
    box-shadow: 0 2px 10px rgba(204,51,17,0.05), 0 1px 2px rgba(0,0,0,0.25);
    position: relative;
    overflow: hidden;
    display: flex;
    align-items: baseline;
    gap: 0.7rem;
    flex-wrap: wrap;
}
.main-header::before {
    content: "";
    position: absolute;
    top: 0; right: 0;
    width: 140px; height: 100%;
    background: radial-gradient(ellipse at top right, rgba(204,51,17,0.06) 0%, transparent 70%);
    pointer-events: none;
}
.main-header h1 {
    margin: 0;
    font-size: 0.95rem;
    color: #f5f5f7;
    font-weight: 800;
    letter-spacing: -0.02em;
}
.main-header p {
    margin: 0;
    color: #778899;
    font-size: 0.7rem;
    letter-spacing: 0.01em;
}

/* ── Widget labels compactos ── */
.stCheckbox label p,
.stRadio label p {
    font-size: 0.8rem !important;
}
.stRadio [role="radiogroup"] label p {
    font-size: 0.8rem !important;
}
div[data-testid="stWidgetLabel"] p {
    font-size: 0.78rem !important;
}
/* Expander — cubrir varias versiones de Streamlit */
details[data-testid="stExpander"] summary,
details[data-testid="stExpander"] summary p,
details[data-testid="stExpander"] summary span,
div[data-testid="stExpander"] summary,
div[data-testid="stExpander"] summary p,
[data-testid="stExpanderToggleIcon"] + * ,
.streamlit-expanderHeader,
.streamlit-expanderHeader p,
details summary,
details summary p {
    font-size: 0.8rem !important;
    font-weight: 500 !important;
}
details[data-testid="stExpander"] summary {
    padding-top: 0.4rem !important;
    padding-bottom: 0.4rem !important;
    min-height: 0 !important;
}

/* ── KPI Cards ── (super-compactado: ~65% menos altura que original) */
.kpi-card {
    background: linear-gradient(180deg, #111822 0%, #0e1319 100%);
    border: 1px solid rgba(255,255,255,0.05);
    border-radius: 7px;
    padding: 0.35rem 0.6rem;
    text-align: center;
    box-shadow: 0 1px 4px rgba(0,0,0,0.18);
    transition: transform 0.15s ease, box-shadow 0.15s ease;
}
.kpi-card:hover {
    transform: translateY(-1px);
    box-shadow: 0 3px 10px rgba(0,0,0,0.28);
}
.kpi-value {
    font-size: 1.1rem;
    font-weight: 900;
    color: #f0f2f5;
    line-height: 1.0;
    font-variant-numeric: tabular-nums;
    letter-spacing: -0.02em;
}
.kpi-label {
    font-size: 0.58rem;
    color: #5a6a7a;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-top: 0.1rem;
    font-weight: 500;
}
.kpi-delta {
    font-size: 0.62rem;
    margin-top: 0.05rem;
    font-weight: 700;
    letter-spacing: 0.02em;
}
.kpi-delta.positive { color: #009988; }
.kpi-delta.negative { color: #CC3311; }
.kpi-delta.neutral  { color: #556677; }

/* ── Status banner ── (compactado) */
.status-banner {
    border-radius: 0 6px 6px 0;
    padding: 0.4rem 0.9rem;
    margin: 0.4rem 0;
    font-size: 0.82rem;
    color: #dde;
    display: flex;
    align-items: center;
    justify-content: space-between;
}
.status-banner.ok {
    background: linear-gradient(90deg, rgba(0,153,136,0.12) 0%, rgba(10,13,20,0.95) 100%);
    border-left: 4px solid #009988;
}
.status-banner.warn {
    background: linear-gradient(90deg, rgba(238,119,51,0.12) 0%, rgba(10,13,20,0.95) 100%);
    border-left: 4px solid #EE7733;
}
.status-banner.alert {
    background: linear-gradient(90deg, rgba(204,51,17,0.15) 0%, rgba(10,13,20,0.95) 100%);
    border-left: 4px solid #CC3311;
    animation: pulse-alert 2s ease-in-out infinite;
}
@keyframes pulse-alert {
    0%, 100% { box-shadow: 0 0 0 0 rgba(204,51,17,0); }
    50% { box-shadow: 0 0 12px 2px rgba(204,51,17,0.15); }
}

/* ── Info panel ── (super-compacto) */
.info-panel {
    background: linear-gradient(135deg, #111822 0%, #0e1319 100%);
    border-left: 3px solid #0077BB;
    border-radius: 0 7px 7px 0;
    padding: 0.5rem 0.85rem;
    margin: 0.3rem 0;
    font-size: 0.78rem;
    color: #99aabb;
    line-height: 1.45;
    box-shadow: 0 1px 4px rgba(0,0,0,0.16);
}

/* ── Volcano card ── (compactado) */
.volcano-card {
    background: linear-gradient(135deg, #111822 0%, #0e1319 100%);
    border: 1px solid rgba(255,255,255,0.05);
    border-radius: 8px;
    padding: 0.7rem 1rem;
    margin-bottom: 0.5rem;
    box-shadow: 0 1px 8px rgba(0,0,0,0.22);
}
.volcano-card h3 {
    margin: 0 0 0.35rem 0;
    color: #f0f2f5;
    font-size: 0.95rem;
    font-weight: 800;
}
.volcano-card .detail {
    color: #7a8a9a;
    font-size: 0.78rem;
    line-height: 1.55;
}

/* ── Ash legend ── (compactado) */
.legend-container {
    background: linear-gradient(180deg, #111822 0%, #0e1319 100%);
    border: 1px solid rgba(255,255,255,0.05);
    border-radius: 8px;
    padding: 0.55rem 0.75rem;
    box-shadow: 0 1px 6px rgba(0,0,0,0.18);
}
.legend-title {
    font-size: 0.68rem;
    color: #5a6a7a;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin-bottom: 0.35rem;
    font-weight: 700;
    padding-bottom: 0.25rem;
    border-bottom: 1px solid rgba(255,255,255,0.04);
}
.legend-row {
    display: flex;
    align-items: center;
    gap: 0.45rem;
    margin: 0.25rem 0;
    font-size: 0.78rem;
    color: #99aabb;
}
.legend-swatch {
    width: 14px;
    height: 14px;
    border-radius: 3px;
    border: 1px solid rgba(255,255,255,0.08);
    flex-shrink: 0;
    box-shadow: 0 1px 2px rgba(0,0,0,0.3);
}

/* ── Sidebar ── */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #080b10 0%, #0c0f16 100%) !important;
    border-right: 1px solid rgba(204,51,17,0.1);
}
section[data-testid="stSidebar"] .stRadio > div {
    gap: 2px;
}
section[data-testid="stSidebar"] .stRadio label {
    padding: 0.5rem 0.8rem !important;
    border-radius: 6px;
    transition: background 0.15s ease;
}
section[data-testid="stSidebar"] .stRadio label:hover {
    background: rgba(204,51,17,0.08);
}

/* ── Tabs ── (compactado) */
.stTabs [data-baseweb="tab-list"] {
    gap: 3px;
    border-bottom: 1px solid rgba(255,255,255,0.04);
}
.stTabs [data-baseweb="tab"] {
    background: rgba(17,24,34,0.6);
    border-radius: 6px 6px 0 0;
    border: 1px solid rgba(255,255,255,0.03);
    border-bottom: none;
    padding: 0.35rem 0.95rem;
    font-size: 0.8rem;
    font-weight: 500;
    transition: background 0.15s ease;
}
.stTabs [data-baseweb="tab"]:hover {
    background: rgba(204,51,17,0.06);
}
.stTabs [aria-selected="true"] {
    background: rgba(204,51,17,0.1) !important;
    border-color: rgba(204,51,17,0.2) !important;
    font-weight: 700 !important;
}

/* ── Metrics nativos ── (compactado) */
[data-testid="stMetric"] {
    background: #111822;
    border: 1px solid rgba(255,255,255,0.04);
    border-radius: 8px;
    padding: 0.45rem 0.7rem;
}
[data-testid="stMetricValue"] { font-size: 1.2rem !important; }
[data-testid="stMetricLabel"] { font-size: 0.7rem !important; }
[data-testid="stMetricDelta"] { font-size: 0.7rem !important; }

/* ── Boton primary ── */
.stButton > button[kind="primary"],
.stButton > button[data-testid="stBaseButton-primary"] {
    background: linear-gradient(135deg, #CC3311 0%, #aa2200 100%) !important;
    border: none !important;
    font-weight: 700;
    letter-spacing: 0.03em;
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(204,51,17,0.25);
    transition: all 0.2s ease;
}
.stButton > button[kind="primary"]:hover,
.stButton > button[data-testid="stBaseButton-primary"]:hover {
    background: linear-gradient(135deg, #dd4422 0%, #CC3311 100%) !important;
    box-shadow: 0 4px 16px rgba(204,51,17,0.35);
    transform: translateY(-1px);
}

/* ── Selectbox / Input ── */
.stSelectbox > div > div,
.stMultiSelect > div > div {
    background: #111822 !important;
    border-color: rgba(255,255,255,0.06) !important;
    border-radius: 8px;
}

/* ── Expander ── */
.streamlit-expanderHeader {
    background: #111822;
    border-radius: 8px;
    font-weight: 600;
}

/* ── Dividers ── */
hr {
    border-color: rgba(255,255,255,0.04) !important;
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: #0a0d14; }
::-webkit-scrollbar-thumb { background: #1a2030; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #253040; }
</style>
"""


def inject_css():
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def inject_reconnect_watchdog():
    """Watchdog JS que auto-recarga la app si Streamlit cae en 'Connection error'.

    EL PROBLEMA: 'Cached ForwardMsg MISS' es un error fatal del cliente de
    Streamlit — cuando el servidor se reinicia (sleep/wake de Streamlit Cloud,
    o la race del importlib de Python 3.14, misma familia que el KeyError
    documentado en CLAUDE.md), el navegador queda referenciando hashes de
    mensajes que ya no existen ni en cliente ni en servidor. Streamlit NO se
    auto-recupera: muestra el diálogo y el websocket queda muerto.

    LA SOLUCIÓN: un iframe invisible (components.html) cuyo JS sobrevive a la
    caída del websocket (es HTML estático, no depende del servidor). Cada 1.5s
    inspecciona el documento PADRE (el frame de la app) buscando el diálogo de
    error; si persiste > GRACE_MS, recarga el frame de la app.

    POR QUÉ window.parent.location.reload() y NO top:
      El sandbox de Streamlit Cloud bloquea navegar el TOP-frame (5 intentos
      fallidos documentados en map_helpers.py:122). Pero recargar el frame de
      la APP (el parent del component iframe) es la misma operación que el
      <a target="_self"> que SÍ funciona — no es top-nav. En Hugging Face (sin
      iframe) parent == la pestaña, también funciona.

    Anti-loop: backoff por sessionStorage (no recarga más de 1 vez cada
    BACKOFF_MS) — si el servidor está caído de verdad, no martillea reloads.
    """
    # Defensivo: components.html es la UNICA API que ejecuta JS (iframe), pero
    # esta deprecada (removal anunciado post 2026-06-01). Si algun dia no esta,
    # degradamos SIN watchdog en vez de crashear la app entera (esto corre en el
    # top-level de app.py en cada carga).
    try:
        import streamlit.components.v1 as components
    except Exception:
        return
    try:
        components.html(
            """
        <script>
        (function(){
          var GRACE_MS = 8000;     // error visible este tiempo antes de recargar
          var BACKOFF_MS = 60000;  // como mucho 1 recarga cada 60s (anti-loop)
          var POLL_MS = 1500;
          var errorSince = null;

          function parentDoc(){
            try { return window.parent.document; } catch(e){ return null; }
          }
          function hasConnError(doc){
            if(!doc) return false;
            // Solo miramos diálogos/status (barato) — el error fatal es un modal.
            var nodes;
            try {
              nodes = doc.querySelectorAll(
                '[role="dialog"], [data-testid="stConnectionStatus"]');
            } catch(e){ return false; }
            var txt = '';
            for (var i=0; i<nodes.length; i++){ txt += (nodes[i].innerText || ''); }
            return /Failed to process a Websocket message/i.test(txt)
                || /Cached ForwardMsg/i.test(txt)
                || (/Connection error/i.test(txt) && /Websocket/i.test(txt));
          }
          function tryReload(){
            var now = Date.now(), last = 0;
            try { last = parseInt(sessionStorage.getItem('goesReloadAt')||'0',10); } catch(e){}
            if (now - last < BACKOFF_MS) return;   // backoff
            try { sessionStorage.setItem('goesReloadAt', String(now)); } catch(e){}
            // Recargar el frame de la APP (parent), NO el top (sandbox lo bloquea).
            try { window.parent.location.reload(); return; } catch(e){}
            try { window.location.reload(); } catch(e){}
          }
          setInterval(function(){
            var doc = parentDoc();
            if (hasConnError(doc)){
              if (errorSince === null) errorSince = Date.now();
              else if (Date.now() - errorSince > GRACE_MS) tryReload();
            } else {
              errorSince = null;
            }
          }, POLL_MS);
        })();
        </script>
        """,
            height=0,
        )
    except Exception:
        # Nunca dejar que el watchdog rompa el render principal.
        pass


def header(title: str, subtitle: str = ""):
    sub_html = (
        f'<span style="color:#445566; font-size:0.9rem;">·</span>'
        f'<p>{subtitle}</p>'
    ) if subtitle else ""
    st.markdown(
        f'<div class="main-header"><h1>{title}</h1>{sub_html}</div>',
        unsafe_allow_html=True,
    )


def kpi_card(value, label: str, delta: str = "", delta_type: str = "neutral"):
    """KPI card con valor, label y delta opcional.

    delta_type: "positive", "negative", "neutral"
    """
    delta_html = ""
    if delta:
        delta_html = f'<div class="kpi-delta {delta_type}">{delta}</div>'
    st.markdown(
        f'<div class="kpi-card">'
        f'<div class="kpi-value">{value}</div>'
        f'<div class="kpi-label">{label}</div>'
        f'{delta_html}'
        f'</div>',
        unsafe_allow_html=True,
    )


def info_panel(text: str):
    st.markdown(f'<div class="info-panel">{text}</div>', unsafe_allow_html=True)


def refresh_info_badge(context: str = "general"):
    """Badge/expander global que explica cadencia de actualizacion.

    Debe ir visible en todas las vistas para que el usuario entienda
    cuanto tarda entre scan y scan y por que.

    context: "live"      = auto-refresh cada 60s (RAMMB Slider tiles).
             "general"   = carga manual; fuente generica GOES-19.
             "animation" = al recargar el animador (RAMMB).
             "volcat"    = productos SSEC/CIMSS (RealEarth + VOLCAT portal).
             "ash"       = L1b crudo de AWS S3 NOAA, procesado por nosotros.

    NOTA (mayo 2026): antes "general" decia "latencia RAMMB" pero lo usan
    vistas que NO consumen RAMMB (Ash=S3 NOAA, VOLCAT=SSEC, Series=FDCF).
    Se agregaron contextos dedicados por fuente para no mentir el origen.
    """
    # Resumen corto en badge inline
    resumen = {
        "live":      ("60 s", "#3fb950", "Polling al servidor cada 60 s; imagen nueva aparece ~3-5 min despues del fin del scan de GOES-19 (ciclo real: 10 min)."),
        "general":   ("manual", "#4a9eff", "Esta vista carga al abrirla o presionar ↻. GOES-19 publica un scan nuevo cada 10 min; sumale unos minutos de latencia de la fuente."),
        "animation": ("por ejecucion", "#d29922", "Genera una animacion con los N ultimos frames disponibles. Reejecuta para traer el frame mas reciente."),
        "volcat":    ("manual", "#4a9eff", "Productos pre-procesados por SSEC/CIMSS (RealEarth + portal VOLCAT). Cadencia ABI 10 min; SSEC publica ~3-6 min despues del scan. Apreta ↻ para el frame mas nuevo."),
        "ash":       ("manual", "#4a9eff", "Baja las 4 bandas L1b crudas de AWS S3 NOAA y las procesa aca (no usa RAMMB). GOES-19 publica cada 10 min + ~2 min de calibracion NOAA."),
        "series":    ("diario", "#3fb950", "Series de hot spots NOAA FDCF + FRP. Un GitHub Action agrega los conteos por volcan 1 vez al dia (02:00 UTC); el dia en curso puede estar incompleto."),
    }
    label, color, detail = resumen.get(context, resumen["general"])
    # Compactado: padding reducido, fuente mas chica, margin-bottom mas chico
    st.markdown(
        f'<div style="display:flex; gap:0.5rem; align-items:center; '
        f'background:rgba(17,24,34,0.55); padding:0.28rem 0.7rem; '
        f'border-radius:6px; border:1px solid rgba(100,120,140,0.2); '
        f'font-size:0.74rem; margin-bottom:0.35rem; line-height:1.35;">'
        f'<span style="color:{color}; font-weight:700;">↻</span>'
        f'<b style="color:#e6edf3;">{label}</b>'
        f'<span style="color:#556677;">·</span>'
        f'<span style="color:#8899aa;">{detail}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )
    # Detalle tecnico completo en expander — DEPENDIENTE DE LA FUENTE.
    # Antes era un texto fijo de la cadena RAMMB que aparecia en TODAS las
    # vistas, incluso VOLCAT (SSEC) y Ash (L1b propio) que NO usan RAMMB.
    # Ahora cada familia de fuente tiene su propia cadena correcta.
    # (mayo 2026)
    _ctx_to_family = {
        "live": "rammb", "animation": "rammb", "general": "rammb",
        "volcat": "ssec", "ash": "self_l1b", "series": "fdcf",
    }
    family = _ctx_to_family.get(context, "rammb")
    _detail = _refresh_detail_html(family)
    with st.expander("Como se actualizan los datos (detalle)"):
        st.markdown(_detail, unsafe_allow_html=True)


def _refresh_detail_html(family: str) -> str:
    """HTML del detalle de actualizacion segun la FUENTE de datos real.

    family:
      "rammb"    -> tiles RGB pre-armados por RAMMB/CIRA (En Vivo, Guardia,
                    Comparador, Loops, Replay).
      "ssec"     -> productos VOLCAT pre-procesados por SSEC/CIMSS.
      "self_l1b" -> bandas L1b crudas de AWS S3 NOAA, procesadas por nosotros
                    (Ash + BTD).
      "fdcf"     -> hot spots L2 FDCF de NOAA (Series de tiempo).
    """
    _wrap = ('<div style="font-size:0.78rem; line-height:1.55; '
             'color:#c0ccd8;">{}</div>')

    if family == "ssec":
        body = """
<b>Cadena de datos — VOLCAT (SSEC/CIMSS)</b><br>
Esta vista NO usa RAMMB. Los productos los pre-procesa la Universidad de
Wisconsin (SSEC/CIMSS) con el algoritmo Pavolonis 2013.

<table style="width:100%; font-size:0.78rem; border-collapse:collapse; margin-top:0.4rem;">
<tr style="color:#8899aa;">
  <th style="text-align:left; padding:2px 6px;">Paso</th>
  <th style="text-align:left; padding:2px 6px;">Tiempo</th>
  <th style="text-align:left; padding:2px 6px;">Que pasa</th></tr>
<tr><td style="padding:2px 6px;">1. Scan del satelite</td>
    <td style="padding:2px 6px;"><b>10 min</b></td>
    <td style="padding:2px 6px;">GOES-19 barre el disco completo</td></tr>
<tr><td style="padding:2px 6px;">2. Calibracion NOAA</td>
    <td style="padding:2px 6px;">1-2 min</td>
    <td style="padding:2px 6px;">El dato bruto se publica en AWS</td></tr>
<tr><td style="padding:2px 6px;">3. Procesamiento SSEC</td>
    <td style="padding:2px 6px;">3-6 min</td>
    <td style="padding:2px 6px;">SSEC corre Pavolonis (deteccion + altura/carga) y publica en RealEarth + portal VOLCAT</td></tr>
<tr><td style="padding:2px 6px;">4. El dashboard consulta</td>
    <td style="padding:2px 6px;">al abrir / ↻</td>
    <td style="padding:2px 6px;">Pedimos el frame mas nuevo a la API de SSEC</td></tr>
<tr><td style="padding:2px 6px;">5. Descarga + dibujo</td>
    <td style="padding:2px 6px;">2-10 s</td>
    <td style="padding:2px 6px;">Bajamos el PNG del producto y lo mostramos</td></tr>
</table>

<b>Total tipico fenomeno -> pantalla:</b> ~13-18 min.<br>
<b>Satelite:</b> preferimos GOES-19 (East); si un sector solo tiene GOES-18 se usa ese.<br>
<b>Como recargar:</b> reabrir la vista, cambiar volcan/zona/producto, o tecla <b>R</b>.<br>
<b>Fuente:</b> <a href="https://volcano.ssec.wisc.edu" target="_blank" style="color:#4a9eff;">VOLCAT portal</a>
+ <a href="https://realearth.ssec.wisc.edu" target="_blank" style="color:#4a9eff;">RealEarth</a> — SSEC/CIMSS, Univ. Wisconsin.
"""
    elif family == "self_l1b":
        body = """
<b>Cadena de datos — Ash + BTD (procesamiento propio)</b><br>
Esta vista NO usa RAMMB ni SSEC: bajamos las bandas crudas y calculamos
todo aca (temperaturas de brillo, BTD split-window y tri-espectral).

<table style="width:100%; font-size:0.78rem; border-collapse:collapse; margin-top:0.4rem;">
<tr style="color:#8899aa;">
  <th style="text-align:left; padding:2px 6px;">Paso</th>
  <th style="text-align:left; padding:2px 6px;">Tiempo</th>
  <th style="text-align:left; padding:2px 6px;">Que pasa</th></tr>
<tr><td style="padding:2px 6px;">1. Scan del satelite</td>
    <td style="padding:2px 6px;"><b>10 min</b></td>
    <td style="padding:2px 6px;">GOES-19 barre el disco completo</td></tr>
<tr><td style="padding:2px 6px;">2. L1b en AWS S3 NOAA</td>
    <td style="padding:2px 6px;">1-2 min</td>
    <td style="padding:2px 6px;">NOAA publica las bandas crudas (radiancias) sin procesar</td></tr>
<tr><td style="padding:2px 6px;">3. Procesamiento propio</td>
    <td style="padding:2px 6px;">10-20 s</td>
    <td style="padding:2px 6px;">Bajamos 4 bandas (~100 MB), radiancia->temperatura (Planck), calculamos BTD</td></tr>
<tr><td style="padding:2px 6px;">4. Render</td>
    <td style="padding:2px 6px;">2-5 s</td>
    <td style="padding:2px 6px;">Dibujamos Ash RGB / BTD / mapa de confianza</td></tr>
</table>

<b>Total tipico fenomeno -> pantalla:</b> ~13-16 min (la descarga L1b es lo mas lento).<br>
<b>Cache:</b> el resultado procesado se guarda ~2 h para no re-descargar.<br>
<b>Como recargar:</b> boton <b>Descargar imagen fresca</b>, o cambiar de region.<br>
<b>Fuente:</b> <a href="https://registry.opendata.aws/noaa-goes/" target="_blank" style="color:#4a9eff;">AWS S3 noaa-goes19</a> — bandas L1b crudas (ABI-L1b-RadF).
"""
    elif family == "fdcf":
        body = """
<b>Cadena de datos — Series de tiempo (hot spots NOAA FDCF)</b><br>
Estas series se arman a partir del producto L2 FDCF de NOAA (deteccion de
focos termicos) y del % de pixeles ash-rojos. NO es una imagen NRT.

<table style="width:100%; font-size:0.78rem; border-collapse:collapse; margin-top:0.4rem;">
<tr style="color:#8899aa;">
  <th style="text-align:left; padding:2px 6px;">Paso</th>
  <th style="text-align:left; padding:2px 6px;">Cadencia</th>
  <th style="text-align:left; padding:2px 6px;">Que pasa</th></tr>
<tr><td style="padding:2px 6px;">1. Producto FDCF L2</td>
    <td style="padding:2px 6px;">10 min</td>
    <td style="padding:2px 6px;">NOAA detecta focos termicos (hot spots + FRP) por scan</td></tr>
<tr><td style="padding:2px 6px;">2. Agregacion diaria</td>
    <td style="padding:2px 6px;">1 vez/dia</td>
    <td style="padding:2px 6px;">Un GitHub Action (02:00 UTC) regenera el JSON de conteos y FRP por volcan</td></tr>
<tr><td style="padding:2px 6px;">3. El dashboard lee</td>
    <td style="padding:2px 6px;">al abrir</td>
    <td style="padding:2px 6px;">Carga el JSON y dibuja las series</td></tr>
</table>

<b>Nota:</b> el dia en curso puede aparecer incompleto hasta que cierra el conteo diario.<br>
<b>Fuente:</b> NOAA GOES-19 <b>ABI-L2-FDCF</b> (Fire/Hot Characterization) via AWS S3.
"""
    else:  # "rammb"
        body = """
<b>Cuanto tarda una imagen nueva en aparecer aca</b>

<table style="width:100%; font-size:0.78rem; border-collapse:collapse;">
<tr style="color:#8899aa;">
  <th style="text-align:left; padding:2px 6px;">Paso</th>
  <th style="text-align:left; padding:2px 6px;">Tiempo</th>
  <th style="text-align:left; padding:2px 6px;">Que pasa</th></tr>
<tr><td style="padding:2px 6px;">1. Scan del satelite</td>
    <td style="padding:2px 6px;"><b>10 min</b></td>
    <td style="padding:2px 6px;">GOES-19 barre el disco completo cada 10 min</td></tr>
<tr><td style="padding:2px 6px;">2. Calibracion NOAA</td>
    <td style="padding:2px 6px;">1-2 min</td>
    <td style="padding:2px 6px;">NOAA publica el dato bruto en la nube (AWS)</td></tr>
<tr><td style="padding:2px 6px;">3. Generacion imagen</td>
    <td style="padding:2px 6px;">2-3 min</td>
    <td style="padding:2px 6px;">RAMMB/CIRA arma los mosaicos RGB que consumimos</td></tr>
<tr><td style="padding:2px 6px;">4. El dashboard chequea</td>
    <td style="padding:2px 6px;">≤ 60 s</td>
    <td style="padding:2px 6px;">Cada minuto preguntamos si hay imagen nueva</td></tr>
<tr><td style="padding:2px 6px;">5. Descarga + dibujo</td>
    <td style="padding:2px 6px;">5-20 s</td>
    <td style="padding:2px 6px;">Bajamos los mosaicos y los reproyectamos al mapa</td></tr>
</table>

<b>Tiempo total entre el fenomeno y verlo aca:</b>
tipico <b>8-10 min</b>, minimo ~4 min, maximo ~15 min.

<b>En que vistas aplica el auto-refresh:</b><br>
&bull; <b>En Vivo</b>: auto-refresh de 60 s. Detecta la imagen nueva solo.<br>
&bull; Resto de vistas RAMMB (Por Volcan, Animacion, Replay): cargan al
  abrir o al presionar un boton; cache 2 h.

<b>Como forzar una recarga inmediata:</b><br>
&bull; Boton <b>↻ Actualizar</b> en En Vivo<br>
&bull; Tecla <b>R</b> en el navegador<br>
&bull; Cambiar el producto o el volcan seleccionado

<b>Fuente:</b> <a href="https://slider.cira.colostate.edu" target="_blank"
style="color:#4a9eff;">RAMMB/CIRA SLIDER</a> — Colorado State University.
"""
    return _wrap.format(body)


def ash_legend():
    """Leyenda Ash RGB con colores calibrados."""
    items = [
        (C_ASH,    "Ceniza volcanica"),
        (C_SO2,    "SO2 (dioxido de azufre)"),
        ("#EE7733","Mezcla ceniza + SO2"),
        ("#8ab4d6","Superficie terrestre"),
        ("#7a6555","Nubes meteorologicas"),
        ("#1a1a2e","Cirrus / espacio"),
    ]
    html = '<div class="legend-container"><div class="legend-title">Interpretacion Ash RGB</div>'
    for color, label in items:
        html += (
            f'<div class="legend-row">'
            f'<div class="legend-swatch" style="background:{color}"></div>'
            f'<span>{label}</span></div>'
        )
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)


def btd_legend():
    """Leyenda BTD split-window."""
    items = [
        (C_ASH,    "BTD < -1 K = posible ceniza"),
        ("#EE7733","BTD -1 a 0 K = ambiguo"),
        ("#f5f5f5","BTD ~ 0 K = neutro"),
        (C_CLEAR,  "BTD > 0 K = nubes meteorologicas"),
    ]
    html = '<div class="legend-container"><div class="legend-title">BTD Split-Window (11.2 - 12.3 um)</div>'
    for color, label in items:
        html += (
            f'<div class="legend-row">'
            f'<div class="legend-swatch" style="background:{color}"></div>'
            f'<span>{label}</span></div>'
        )
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)


def ash_so2_legend():
    """Leyenda Ash/SO2 RGB (8.5-11-12 um)."""
    items = [
        (C_ASH,    "Ceniza volcanica"),
        (C_SO2,    "SO2 (dioxido de azufre)"),
        ("#EE7733","Mezcla ceniza + SO2"),
        ("#334466","Nubes meteorologicas"),
        ("#1a1a2e","Superficie fria / espacio"),
    ]
    html = '<div class="legend-container"><div class="legend-title">Ash/SO2 RGB (8.5 - 11 - 12 um)</div>'
    for color, label in items:
        html += (
            f'<div class="legend-row">'
            f'<div class="legend-swatch" style="background:{color}"></div>'
            f'<span>{label}</span></div>'
        )
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)


def so2_legend():
    """Leyenda indicador SO2."""
    items = [
        ("#660022","< -5 K = SO2 intenso"),
        (C_ASH,    "-5 a -3 K = SO2 probable"),
        ("#EE7733","-3 a -1 K = SO2 posible"),
        ("#334455","> -1 K = sin SO2"),
    ]
    html = '<div class="legend-container"><div class="legend-title">SO2 Index (BT 8.4 - BT 11.2 um)</div>'
    for color, label in items:
        html += (
            f'<div class="legend-row">'
            f'<div class="legend-swatch" style="background:{color}"></div>'
            f'<span>{label}</span></div>'
        )
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)


# Colorscale SO2 (secuencial)
SO2_COLORSCALE = [
    [0.0,  "rgba(14,17,23,0.9)"],  # sin SO2
    [0.3,  "#EE7733"],              # posible
    [0.6,  "#CC3311"],              # probable
    [1.0,  "#660022"],              # intenso
]
