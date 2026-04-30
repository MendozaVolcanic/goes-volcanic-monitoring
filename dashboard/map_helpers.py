"""Helpers compartidos para mapas Plotly del dashboard.

Centraliza overlays comunes (frontera Chile, anillos de distancia, etc.)
que cualquier vista puede invocar sin duplicar codigo.
"""

import plotly.graph_objects as go

from src.borders import get_chile_outline_xy


def add_chile_border(fig: go.Figure, color: str = "rgba(255,255,255,0.55)",
                     width: float = 1.2, dash: str = "solid") -> go.Figure:
    """Agrega el contorno de Chile como linea sobre el mapa.

    Por default linea blanca semi-transparente — visible sobre fondos
    oscuros (Ash RGB, GeoColor noche, BTD heatmap) sin tapar el dato.
    """
    lons, lats = get_chile_outline_xy()
    fig.add_trace(go.Scatter(
        x=lons, y=lats, mode="lines",
        line=dict(color=color, width=width, dash=dash),
        hoverinfo="skip", showlegend=False, name="Chile border",
    ))
    return fig
