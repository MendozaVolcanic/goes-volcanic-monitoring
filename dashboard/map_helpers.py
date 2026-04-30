"""Helpers compartidos para mapas Plotly del dashboard.

Centraliza overlays comunes (frontera Chile, anillos de distancia, etc.)
que cualquier vista puede invocar sin duplicar codigo.

NOTA: las coordenadas de Chile estan inline aca (no importadas de
src.borders) para evitar problemas de import en Streamlit Cloud
(cache stale entre deploys). El modulo src.borders sigue existiendo
por si otro proyecto del ecosistema lo necesita.
"""

import plotly.graph_objects as go


# Costa Pacífica (oeste) — Arica → Cabo de Hornos
_COAST = [
    (-17.50, -70.40), (-18.20, -70.34), (-18.50, -70.32), (-19.00, -70.30),
    (-19.61, -70.20), (-20.21, -70.16), (-20.80, -70.18), (-21.41, -70.06),
    (-22.10, -70.10), (-22.46, -70.27), (-23.10, -70.40), (-23.65, -70.40),
    (-24.50, -70.50), (-25.41, -70.50), (-26.36, -70.62), (-27.05, -70.85),
    (-27.39, -70.96), (-28.45, -71.27), (-29.20, -71.30), (-29.95, -71.35),
    (-30.50, -71.50), (-31.15, -71.61), (-31.90, -71.50), (-32.45, -71.45),
    (-33.04, -71.61), (-33.60, -71.85), (-34.22, -71.92), (-34.85, -72.20),
    (-35.55, -72.65), (-36.20, -72.95), (-36.82, -73.18), (-37.30, -73.40),
    (-37.85, -73.50), (-38.50, -73.45), (-39.27, -73.24), (-39.90, -73.18),
    (-40.58, -73.12), (-41.20, -73.00), (-41.47, -72.94), (-42.00, -73.30),
    (-42.50, -73.83), (-43.10, -73.95), (-43.78, -74.05), (-44.50, -74.20),
    (-45.40, -74.35), (-46.10, -75.00), (-46.79, -75.65), (-47.40, -75.70),
    (-48.07, -75.55), (-48.90, -75.40), (-49.97, -75.36), (-50.80, -74.50),
    (-51.62, -73.84), (-52.45, -71.95), (-53.20, -71.50), (-53.79, -70.99),
    (-54.50, -70.80), (-55.07, -70.60), (-55.50, -69.50), (-55.97, -67.27),
]

# Frontera Andina (este) — sur a norte: Tierra del Fuego -> frontera Peru
_BORDER = [
    (-54.91, -68.36), (-53.00, -68.50), (-52.16, -68.59), (-51.66, -72.48),
    (-51.00, -72.90), (-50.00, -73.20), (-49.30, -73.40), (-48.69, -73.50),
    (-47.90, -73.10), (-47.20, -72.62), (-46.50, -72.20), (-45.92, -71.82),
    (-45.10, -71.50), (-44.40, -71.10), (-43.70, -71.50), (-43.10, -71.85),
    (-42.50, -71.70), (-42.05, -71.65), (-41.30, -71.75), (-40.56, -71.85),
    (-39.80, -71.50), (-39.20, -71.32), (-38.50, -71.25), (-37.95, -71.18),
    (-37.30, -71.00), (-36.60, -70.85), (-35.80, -70.50), (-34.95, -70.05),
    (-34.20, -69.90), (-33.42, -69.83), (-32.75, -70.00), (-32.10, -70.05),
    (-31.30, -70.10), (-30.50, -70.10), (-29.80, -69.95), (-29.00, -69.90),
    (-28.10, -69.50), (-27.20, -69.40), (-26.30, -69.10), (-25.50, -68.85),
    (-24.50, -68.30), (-23.50, -67.30), (-23.00, -67.50), (-22.30, -67.90),
    (-21.70, -68.05), (-21.20, -68.20), (-20.50, -68.50), (-19.85, -68.70),
    (-19.20, -68.85), (-18.50, -69.05), (-17.90, -69.30), (-17.50, -69.50),
]


def add_chile_border(fig: go.Figure, color: str = "rgba(255,255,255,0.65)",
                     width: float = 1.4, dash: str = "solid") -> go.Figure:
    """Agrega el contorno de Chile (costa + frontera Andina) como 2 lineas.

    Dos traces independientes que NO se conectan entre si — evita el "salto"
    diagonal del poligono cerrado anterior.
    """
    coast_lons = [pt[1] for pt in _COAST]
    coast_lats = [pt[0] for pt in _COAST]
    border_lons = [pt[1] for pt in _BORDER]
    border_lats = [pt[0] for pt in _BORDER]
    line_style = dict(color=color, width=width, dash=dash)
    fig.add_trace(go.Scatter(
        x=coast_lons, y=coast_lats, mode="lines",
        line=line_style,
        hoverinfo="skip", showlegend=False, name="Costa Pacifica",
    ))
    fig.add_trace(go.Scatter(
        x=border_lons, y=border_lats, mode="lines",
        line=line_style,
        hoverinfo="skip", showlegend=False, name="Frontera Andina",
    ))
    return fig
