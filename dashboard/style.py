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
/* ── Header ── */
.main-header {
    background: linear-gradient(135deg, #111620 0%, #1a1f2e 100%);
    padding: 1.5rem 2rem;
    border-radius: 10px;
    margin-bottom: 1.5rem;
    border: 1px solid rgba(255,255,255,0.06);
    border-left: 4px solid #CC3311;
}
.main-header h1 {
    margin: 0;
    font-size: 1.6rem;
    color: #fafafa;
    font-weight: 700;
    letter-spacing: -0.02em;
}
.main-header p {
    margin: 0.4rem 0 0 0;
    color: #667788;
    font-size: 0.85rem;
}

/* ── KPI Cards ── */
.kpi-card {
    background: #141926;
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 8px;
    padding: 1rem 1rem;
    text-align: center;
}
.kpi-value {
    font-size: 1.8rem;
    font-weight: 800;
    color: #fafafa;
    line-height: 1.2;
    font-variant-numeric: tabular-nums;
}
.kpi-label {
    font-size: 0.72rem;
    color: #667788;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin-top: 0.25rem;
}
.kpi-delta {
    font-size: 0.75rem;
    margin-top: 0.2rem;
    font-weight: 600;
}
.kpi-delta.positive { color: #009988; }
.kpi-delta.negative { color: #CC3311; }
.kpi-delta.neutral  { color: #667788; }

/* ── Info panel ── */
.info-panel {
    background: #141926;
    border-left: 3px solid #0077BB;
    border-radius: 0 8px 8px 0;
    padding: 1rem 1.2rem;
    margin: 1rem 0;
    font-size: 0.88rem;
    color: #aabbcc;
    line-height: 1.6;
}

/* ── Volcano card ── */
.volcano-card {
    background: #141926;
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 8px;
    padding: 1.2rem 1.4rem;
    margin-bottom: 0.8rem;
}
.volcano-card h3 {
    margin: 0 0 0.5rem 0;
    color: #fafafa;
    font-size: 1.05rem;
    font-weight: 700;
}
.volcano-card .detail {
    color: #8899aa;
    font-size: 0.82rem;
    line-height: 1.7;
}

/* ── Ash legend ── */
.legend-container {
    background: #141926;
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 8px;
    padding: 0.8rem 1rem;
}
.legend-title {
    font-size: 0.75rem;
    color: #667788;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin-bottom: 0.5rem;
    font-weight: 600;
}
.legend-row {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin: 0.35rem 0;
    font-size: 0.82rem;
    color: #aabbcc;
}
.legend-swatch {
    width: 14px;
    height: 14px;
    border-radius: 3px;
    border: 1px solid rgba(255,255,255,0.1);
    flex-shrink: 0;
}

/* ── Sidebar ── */
section[data-testid="stSidebar"] {
    background: #0c0f16;
    border-right: 1px solid rgba(255,255,255,0.04);
}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] { gap: 4px; }
.stTabs [data-baseweb="tab"] {
    background: #141926;
    border-radius: 6px 6px 0 0;
    border: 1px solid rgba(255,255,255,0.04);
    padding: 0.5rem 1.2rem;
    font-size: 0.85rem;
}

/* ── Metrics nativos ── */
[data-testid="stMetric"] {
    background: #141926;
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 8px;
    padding: 0.6rem 0.8rem;
}

/* ── Boton primary ── */
.stButton > button[kind="primary"] {
    background: #CC3311;
    border: none;
    font-weight: 600;
    letter-spacing: 0.02em;
}
.stButton > button[kind="primary"]:hover {
    background: #aa2200;
}
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
