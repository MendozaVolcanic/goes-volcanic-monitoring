"""CSS y estilos globales del dashboard."""

import streamlit as st

CUSTOM_CSS = """
<style>
/* ── Header con gradiente ── */
.main-header {
    background: linear-gradient(135deg, #1a1f2e 0%, #2d1b3d 50%, #1a2e1f 100%);
    padding: 1.5rem 2rem;
    border-radius: 12px;
    margin-bottom: 1.5rem;
    border: 1px solid rgba(255,255,255,0.08);
}
.main-header h1 {
    margin: 0;
    font-size: 1.8rem;
    background: linear-gradient(90deg, #ff6b6b, #ffa07a);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
.main-header p {
    margin: 0.3rem 0 0 0;
    color: #8899aa;
    font-size: 0.9rem;
}

/* ── KPI Cards ── */
.kpi-card {
    background: linear-gradient(145deg, #1a1f2e, #1e2538);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 10px;
    padding: 1rem 1.2rem;
    text-align: center;
    transition: transform 0.2s;
}
.kpi-card:hover {
    transform: translateY(-2px);
    border-color: rgba(255,107,107,0.3);
}
.kpi-value {
    font-size: 2rem;
    font-weight: 700;
    color: #ff6b6b;
    line-height: 1.2;
}
.kpi-label {
    font-size: 0.8rem;
    color: #8899aa;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-top: 0.3rem;
}

/* ── Status badge ── */
.status-badge {
    display: inline-block;
    padding: 0.2rem 0.7rem;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 0.03em;
}
.status-ok { background: rgba(39,174,96,0.2); color: #27ae60; border: 1px solid rgba(39,174,96,0.3); }
.status-warn { background: rgba(243,156,18,0.2); color: #f39c12; border: 1px solid rgba(243,156,18,0.3); }
.status-alert { background: rgba(231,76,60,0.2); color: #e74c3c; border: 1px solid rgba(231,76,60,0.3); }

/* ── Info panel ── */
.info-panel {
    background: #1a1f2e;
    border-left: 3px solid #ff6b6b;
    border-radius: 0 8px 8px 0;
    padding: 1rem 1.2rem;
    margin: 1rem 0;
    font-size: 0.9rem;
    color: #ccc;
}

/* ── Volcano card ── */
.volcano-card {
    background: linear-gradient(145deg, #1a1f2e, #1e2538);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 10px;
    padding: 1.2rem;
    margin-bottom: 0.8rem;
}
.volcano-card h3 {
    margin: 0 0 0.5rem 0;
    color: #fafafa;
    font-size: 1.1rem;
}
.volcano-card .detail {
    color: #8899aa;
    font-size: 0.85rem;
    line-height: 1.6;
}

/* ── Leyenda colores Ash RGB ── */
.legend-row {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin: 0.3rem 0;
    font-size: 0.85rem;
}
.legend-swatch {
    width: 16px;
    height: 16px;
    border-radius: 3px;
    border: 1px solid rgba(255,255,255,0.15);
    flex-shrink: 0;
}

/* ── Mejorar sidebar ── */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0e1117 0%, #141926 100%);
    border-right: 1px solid rgba(255,255,255,0.05);
}

/* ── Mejorar tabs ── */
.stTabs [data-baseweb="tab-list"] {
    gap: 0.5rem;
}
.stTabs [data-baseweb="tab"] {
    background: #1a1f2e;
    border-radius: 8px 8px 0 0;
    border: 1px solid rgba(255,255,255,0.06);
    padding: 0.5rem 1.2rem;
}

/* ── Mejorar metrics ── */
[data-testid="stMetric"] {
    background: linear-gradient(145deg, #1a1f2e, #1e2538);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 10px;
    padding: 0.8rem 1rem;
}

/* ── Botón primary ── */
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #e74c3c, #c0392b);
    border: none;
    font-weight: 600;
}
</style>
"""


def inject_css():
    """Inyectar CSS global."""
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def header(title: str, subtitle: str = ""):
    """Renderizar header con gradiente."""
    sub_html = f"<p>{subtitle}</p>" if subtitle else ""
    st.markdown(
        f'<div class="main-header"><h1>{title}</h1>{sub_html}</div>',
        unsafe_allow_html=True,
    )


def kpi_card(value, label: str):
    """Renderizar una KPI card."""
    st.markdown(
        f'<div class="kpi-card">'
        f'<div class="kpi-value">{value}</div>'
        f'<div class="kpi-label">{label}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


def info_panel(text: str):
    """Renderizar panel informativo."""
    st.markdown(f'<div class="info-panel">{text}</div>', unsafe_allow_html=True)


def ash_legend():
    """Renderizar leyenda de colores Ash RGB."""
    items = [
        ("#d63031", "Ceniza volcánica"),
        ("#00b894", "Dioxido de azufre (SO2)"),
        ("#fdcb6e", "Mezcla ceniza + SO2"),
        ("#a8c8e8", "Superficie terrestre"),
        ("#6d5c4e", "Nubes meteorologicas"),
        ("#2d3436", "Cirrus alto / espacio"),
    ]
    html = ""
    for color, label in items:
        html += (
            f'<div class="legend-row">'
            f'<div class="legend-swatch" style="background:{color}"></div>'
            f'<span>{label}</span>'
            f'</div>'
        )
    st.markdown(html, unsafe_allow_html=True)
