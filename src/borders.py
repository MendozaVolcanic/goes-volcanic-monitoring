"""Frontera de Chile simplificada como secuencia de (lat, lon).

Coordenadas extraidas de Natural Earth 110m simplificado, suficientes
para identificar visualmente Chile en mapas con la resolucion de
GOES-19 (~2 km/px). Para resolucion mayor usar `naturalearth-lowres`
de geopandas (dep pesada — no agregamos por ahora).

NO incluye:
- Antartica chilena (irrelevante para volcanes monitoreados)
- Islas oceanicas (Pascua, Juan Fernandez)

Cubre desde Arica (~-17.5°) hasta Cabo de Hornos (~-56°), con la
costa Pacifica + frontera con Argentina/Bolivia/Peru.
"""

# Lista de (lat, lon) recorriendo el contorno de Chile continental
# en sentido horario (norte → sur por el este, sur → norte por la costa).
# Resolucion ~50 puntos — suficiente para visualizar.
CHILE_OUTLINE = [
    # Costa norte → sur (Pacifico)
    (-17.50, -70.40),  # Arica
    (-18.50, -70.32),
    (-19.61, -70.20),  # Iquique
    (-20.21, -70.16),
    (-21.41, -70.06),
    (-22.46, -70.27),  # Mejillones
    (-23.65, -70.40),  # Antofagasta
    (-25.41, -70.50),
    (-26.36, -70.62),  # Chañaral
    (-27.39, -70.96),
    (-28.45, -71.27),  # Caldera/Bahia Inglesa
    (-29.95, -71.35),  # Coquimbo
    (-31.15, -71.61),
    (-32.45, -71.45),
    (-33.04, -71.61),  # Valparaiso
    (-34.22, -71.92),
    (-35.55, -72.65),
    (-36.82, -73.18),  # Concepcion
    (-37.85, -73.50),
    (-39.27, -73.24),  # Valdivia
    (-40.58, -73.12),
    (-41.47, -72.94),  # Puerto Montt
    (-42.50, -73.83),  # Chiloe oeste
    (-43.78, -74.05),
    (-45.40, -74.35),
    (-46.79, -75.65),
    (-48.07, -75.55),
    (-49.97, -75.36),
    (-51.62, -73.84),
    (-52.45, -71.95),
    (-53.79, -70.99),
    (-55.07, -70.60),
    (-55.97, -67.27),  # Cabo de Hornos / Tierra del Fuego sur
    # Frontera este (con Argentina, sur → norte)
    (-54.91, -68.36),
    (-52.16, -68.59),  # Estrecho de Magallanes
    (-51.66, -72.48),
    (-50.00, -73.20),
    (-48.69, -73.50),
    (-47.20, -72.62),
    (-45.92, -71.82),
    (-44.40, -71.10),
    (-43.10, -71.85),
    (-42.05, -71.65),
    (-40.56, -71.85),
    (-39.20, -71.32),
    (-37.95, -71.18),
    (-36.60, -70.85),
    (-34.95, -70.05),  # Volcan Maipo
    (-33.42, -69.83),  # Aconcagua
    (-32.10, -70.05),
    (-30.50, -70.10),
    (-29.00, -69.90),
    (-27.20, -69.40),
    (-25.50, -68.85),
    (-23.50, -67.30),  # Salar de Atacama
    (-22.30, -67.90),
    (-21.20, -68.20),
    (-19.85, -68.70),
    (-18.50, -69.05),
    (-17.50, -69.50),
    # Cierre frontera norte (con Peru/Bolivia)
    (-17.50, -70.40),
]


def get_chile_outline_xy() -> tuple[list[float], list[float]]:
    """Devuelve (lons, lats) listas paralelas para usar en Plotly Scatter."""
    lons = [pt[1] for pt in CHILE_OUTLINE]
    lats = [pt[0] for pt in CHILE_OUTLINE]
    return lons, lats
