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
.block-container { padding-top: 1.5rem !important; }
.stApp { background: #0a0d14; }

/* ── Header ── */
.main-header {
    background: linear-gradient(135deg, #0f1520 0%, #161d2e 50%, #1a1225 100%);
    padding: 1.8rem 2.2rem;
    border-radius: 12px;
    margin-bottom: 1.8rem;
    border: 1px solid rgba(204,51,17,0.15);
    border-left: 5px solid #CC3311;
    box-shadow: 0 4px 24px rgba(204,51,17,0.08), 0 1px 3px rgba(0,0,0,0.3);
    position: relative;
    overflow: hidden;
}
.main-header::before {
    content: "";
    position: absolute;
    top: 0; right: 0;
    width: 200px; height: 100%;
    background: radial-gradient(ellipse at top right, rgba(204,51,17,0.06) 0%, transparent 70%);
    pointer-events: none;
}
.main-header h1 {
    margin: 0;
    font-size: 1.7rem;
    color: #f5f5f7;
    font-weight: 800;
    letter-spacing: -0.03em;
}
.main-header p {
    margin: 0.5rem 0 0 0;
    color: #778899;
    font-size: 0.85rem;
    letter-spacing: 0.01em;
}

/* ── KPI Cards ── */
.kpi-card {
    background: linear-gradient(180deg, #111822 0%, #0e1319 100%);
    border: 1px solid rgba(255,255,255,0.05);
    border-radius: 10px;
    padding: 1.1rem 1rem;
    text-align: center;
    box-shadow: 0 2px 12px rgba(0,0,0,0.25);
    transition: transform 0.15s ease, box-shadow 0.15s ease;
}
.kpi-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(0,0,0,0.35);
}
.kpi-value {
    font-size: 2rem;
    font-weight: 900;
    color: #f0f2f5;
    line-height: 1.15;
    font-variant-numeric: tabular-nums;
    letter-spacing: -0.02em;
}
.kpi-label {
    font-size: 0.7rem;
    color: #5a6a7a;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-top: 0.35rem;
    font-weight: 500;
}
.kpi-delta {
    font-size: 0.75rem;
    margin-top: 0.25rem;
    font-weight: 700;
    letter-spacing: 0.02em;
}
.kpi-delta.positive { color: #009988; }
.kpi-delta.negative { color: #CC3311; }
.kpi-delta.neutral  { color: #556677; }

/* ── Status banner ── */
.status-banner {
    border-radius: 0 8px 8px 0;
    padding: 0.7rem 1.2rem;
    margin: 1rem 0;
    font-size: 0.92rem;
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

/* ── Info panel ── */
.info-panel {
    background: linear-gradient(135deg, #111822 0%, #0e1319 100%);
    border-left: 3px solid #0077BB;
    border-radius: 0 10px 10px 0;
    padding: 1.2rem 1.4rem;
    margin: 1rem 0;
    font-size: 0.88rem;
    color: #99aabb;
    line-height: 1.7;
    box-shadow: 0 2px 8px rgba(0,0,0,0.2);
}

/* ── Volcano card ── */
.volcano-card {
    background: linear-gradient(135deg, #111822 0%, #0e1319 100%);
    border: 1px solid rgba(255,255,255,0.05);
    border-radius: 10px;
    padding: 1.3rem 1.5rem;
    margin-bottom: 1rem;
    box-shadow: 0 2px 12px rgba(0,0,0,0.25);
}
.volcano-card h3 {
    margin: 0 0 0.6rem 0;
    color: #f0f2f5;
    font-size: 1.1rem;
    font-weight: 800;
}
.volcano-card .detail {
    color: #7a8a9a;
    font-size: 0.82rem;
    line-height: 1.8;
}

/* ── Ash legend ── */
.legend-container {
    background: linear-gradient(180deg, #111822 0%, #0e1319 100%);
    border: 1px solid rgba(255,255,255,0.05);
    border-radius: 10px;
    padding: 1rem 1.1rem;
    box-shadow: 0 2px 8px rgba(0,0,0,0.2);
}
.legend-title {
    font-size: 0.72rem;
    color: #5a6a7a;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 0.6rem;
    font-weight: 700;
    padding-bottom: 0.4rem;
    border-bottom: 1px solid rgba(255,255,255,0.04);
}
.legend-row {
    display: flex;
    align-items: center;
    gap: 0.55rem;
    margin: 0.4rem 0;
    font-size: 0.82rem;
    color: #99aabb;
}
.legend-swatch {
    width: 16px;
    height: 16px;
    border-radius: 4px;
    border: 1px solid rgba(255,255,255,0.08);
    flex-shrink: 0;
    box-shadow: 0 1px 3px rgba(0,0,0,0.3);
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

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    gap: 4px;
    border-bottom: 1px solid rgba(255,255,255,0.04);
}
.stTabs [data-baseweb="tab"] {
    background: rgba(17,24,34,0.6);
    border-radius: 8px 8px 0 0;
    border: 1px solid rgba(255,255,255,0.03);
    border-bottom: none;
    padding: 0.55rem 1.3rem;
    font-size: 0.85rem;
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

/* ── Metrics nativos ── */
[data-testid="stMetric"] {
    background: #111822;
    border: 1px solid rgba(255,255,255,0.04);
    border-radius: 10px;
    padding: 0.7rem 0.9rem;
}

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


def header(title: str, subtitle: str = ""):
    sub_html = f"<p>{subtitle}</p>" if subtitle else ""
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
