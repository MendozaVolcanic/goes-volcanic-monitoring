"""Helpers compartidos para mapas Plotly del dashboard.

Centraliza overlays comunes (frontera Chile, anillos de distancia, etc.)
que cualquier vista puede invocar sin duplicar codigo.
"""

import plotly.graph_objects as go

from src.borders import get_chile_lines


def add_chile_border(fig: go.Figure, color: str = "rgba(255,255,255,0.65)",
                     width: float = 1.4, dash: str = "solid") -> go.Figure:
    """Agrega el contorno de Chile (costa + frontera Andina) como 2 lineas.

    Antes era un polígono cerrado que generaba un "salto" visualmente.
    Ahora son dos traces independientes que no conectan entre sí.
    Línea blanca semi-transparente — visible sobre fondos oscuros sin
    tapar el dato.
    """
    (coast_lons, coast_lats), (border_lons, border_lats) = get_chile_lines()
    line_style = dict(color=color, width=width, dash=dash)
    fig.add_trace(go.Scatter(
        x=coast_lons, y=coast_lats, mode="lines",
        line=line_style,
        hoverinfo="skip", showlegend=False, name="Costa Pacífica",
    ))
    fig.add_trace(go.Scatter(
        x=border_lons, y=border_lats, mode="lines",
        line=line_style,
        hoverinfo="skip", showlegend=False, name="Frontera Andina",
    ))
    return fig
