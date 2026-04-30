"""Helpers compartidos para mapas Plotly del dashboard.

Centraliza overlays comunes (frontera Chile, anillos de distancia, etc.)
que cualquier vista puede invocar sin duplicar codigo.

NOTA: las coordenadas de Chile estan inline aca (no importadas de
src.borders) para evitar problemas de import en Streamlit Cloud
(cache stale entre deploys). El modulo src.borders sigue existiendo
por si otro proyecto del ecosistema lo necesita.
"""

import plotly.graph_objects as go


def _interp_segments(pts: list[tuple[float, float]], n_extra: int = 2
                      ) -> list[tuple[float, float]]:
    """Linea mas suave: agrega `n_extra` puntos interpolados entre
    cada par consecutivo. Para n_extra=2 triplica la densidad."""
    out = []
    for i in range(len(pts) - 1):
        a, b = pts[i], pts[i + 1]
        out.append(a)
        for k in range(1, n_extra + 1):
            t = k / (n_extra + 1)
            out.append((
                a[0] + t * (b[0] - a[0]),
                a[1] + t * (b[1] - a[1]),
            ))
    out.append(pts[-1])
    return out


# Costa Pacifica (oeste) — Arica -> Cabo de Hornos
# Coords actualizados con mas precision basados en Natural Earth 50m.
# Densidad ~2x previa, especialmente en patagonia donde la costa es
# muy irregular (fjordos, peninsulas).
_COAST = [
    (-17.50, -70.32), (-17.95, -70.30), (-18.48, -70.32), (-19.00, -70.27),
    (-19.61, -70.20), (-20.20, -70.18), (-20.55, -70.18), (-20.95, -70.13),
    (-21.43, -70.06), (-22.05, -70.18), (-22.45, -70.30), (-23.10, -70.41),
    (-23.65, -70.40), (-24.10, -70.45), (-24.50, -70.50), (-25.10, -70.50),
    (-25.41, -70.50), (-26.05, -70.65), (-26.36, -70.62), (-26.92, -70.82),
    (-27.39, -70.96), (-28.00, -71.20), (-28.45, -71.27), (-29.05, -71.32),
    (-29.65, -71.32), (-29.95, -71.35), (-30.50, -71.50), (-30.93, -71.55),
    (-31.40, -71.62), (-31.90, -71.50), (-32.20, -71.55), (-32.45, -71.45),
    (-32.78, -71.50), (-33.04, -71.61), (-33.45, -71.78), (-33.90, -72.00),
    (-34.40, -72.05), (-34.95, -72.25), (-35.45, -72.50), (-35.90, -72.85),
    (-36.45, -72.95), (-36.82, -73.05), (-37.15, -73.30), (-37.55, -73.45),
    (-38.10, -73.45), (-38.65, -73.50), (-39.00, -73.30), (-39.27, -73.25),
    (-39.65, -73.20), (-40.00, -73.20), (-40.30, -73.10), (-40.75, -73.10),
    (-41.20, -73.00), (-41.50, -73.00), (-41.85, -73.50), (-42.20, -73.70),
    (-42.50, -73.85), (-42.90, -73.95), (-43.40, -74.00), (-43.85, -74.10),
    (-44.40, -74.25), (-44.95, -74.30), (-45.45, -74.40), (-45.95, -74.65),
    (-46.40, -75.00), (-46.85, -75.45), (-47.30, -75.55), (-47.85, -75.55),
    (-48.30, -75.50), (-48.85, -75.40), (-49.40, -75.40), (-50.00, -75.30),
    (-50.50, -75.10), (-50.90, -74.50), (-51.30, -74.10), (-51.65, -73.85),
    (-52.05, -73.30), (-52.45, -72.45), (-52.80, -72.10), (-53.20, -71.50),
    (-53.55, -71.20), (-53.85, -70.95), (-54.20, -70.80), (-54.55, -70.80),
    (-54.90, -70.65), (-55.15, -70.40), (-55.45, -69.30), (-55.75, -68.10),
    (-55.97, -67.27),
]

# Frontera Andina (este, con Argentina/Bolivia/Peru)
# Sur a norte: Tierra del Fuego -> frontera Peru
_BORDER = [
    (-54.95, -68.36), (-54.50, -68.30), (-53.90, -68.45), (-53.40, -68.50),
    (-52.85, -68.55), (-52.40, -68.55), (-52.10, -68.85), (-52.00, -69.50),
    (-51.85, -70.50), (-51.70, -71.50), (-51.55, -72.50), (-51.20, -72.85),
    (-50.65, -73.10), (-50.05, -73.25), (-49.40, -73.40), (-48.75, -73.40),
    (-48.10, -73.20), (-47.50, -72.85), (-46.95, -72.55), (-46.40, -72.30),
    (-45.85, -71.90), (-45.30, -71.70), (-44.75, -71.40), (-44.30, -71.20),
    (-43.85, -71.50), (-43.40, -71.80), (-42.95, -71.90), (-42.45, -71.80),
    (-42.00, -71.80), (-41.50, -71.80), (-41.00, -71.85), (-40.50, -71.80),
    (-39.95, -71.55), (-39.50, -71.45), (-39.10, -71.35), (-38.65, -71.30),
    (-38.20, -71.25), (-37.75, -71.15), (-37.30, -71.05), (-36.85, -70.95),
    (-36.30, -70.80), (-35.85, -70.55), (-35.40, -70.40), (-34.95, -70.10),
    (-34.45, -70.00), (-33.95, -69.90), (-33.45, -69.85), (-32.95, -69.95),
    (-32.40, -70.00), (-31.85, -70.05), (-31.30, -70.10), (-30.75, -70.15),
    (-30.20, -70.05), (-29.65, -69.95), (-29.10, -69.90), (-28.55, -69.65),
    (-28.00, -69.45), (-27.45, -69.40), (-26.85, -69.20), (-26.30, -69.05),
    (-25.75, -68.95), (-25.10, -68.55), (-24.45, -68.30), (-23.85, -67.90),
    (-23.35, -67.20), (-22.85, -67.20), (-22.45, -67.40), (-22.05, -67.85),
    (-21.65, -68.00), (-21.20, -68.20), (-20.75, -68.35), (-20.30, -68.50),
    (-19.85, -68.65), (-19.45, -68.75), (-19.05, -68.85), (-18.55, -69.05),
    (-18.10, -69.20), (-17.65, -69.45), (-17.50, -69.50),
]


def add_chile_border(fig: go.Figure, color: str = "rgba(255,255,255,0.65)",
                     width: float = 1.4, dash: str = "solid",
                     smooth: bool = True) -> go.Figure:
    """Agrega el contorno de Chile (costa + frontera Andina) como 2 lineas.

    smooth=True (default): interpola 2 puntos extra entre cada par para
    suavizar los segmentos rectos y evitar look "jagged" en mapas
    grandes. Triplica la densidad: ~60 -> ~180 puntos por linea.
    """
    coast = _interp_segments(_COAST, n_extra=2) if smooth else _COAST
    border = _interp_segments(_BORDER, n_extra=2) if smooth else _BORDER
    coast_lons = [pt[1] for pt in coast]
    coast_lats = [pt[0] for pt in coast]
    border_lons = [pt[1] for pt in border]
    border_lats = [pt[0] for pt in border]
    # NOTA: shape='spline' rompe en algunas versiones Plotly/Streamlit Cloud.
    # Usamos shape='linear' (default) — la densidad de puntos ya da curvas
    # visualmente suaves sin necesidad de spline.
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
