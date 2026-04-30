"""Catálogo de volcanes activos de Chile para monitoreo GOES.

Fuente: SERNAGEOMIN Red Nacional de Vigilancia Volcánica (RNVV)
Coordenadas: WGS84
Ranking de peligrosidad: SERNAGEOMIN 2019
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Volcano:
    name: str
    lat: float
    lon: float
    elevation: int  # metros
    region: str     # región administrativa
    zone: str       # zona volcánica (norte, centro, sur, austral)
    ranking: int    # ranking SERNAGEOMIN (1=mayor peligro). 0=sin ranking


# 43 volcanes monitoreados por SERNAGEOMIN (RNVV)
# Ordenados norte a sur
CATALOG = [
    # ── Zona Norte (ZVN/ZVC) ──
    Volcano("Taapaca", -18.10, -69.50, 5860, "Arica y Parinacota", "norte", 0),
    Volcano("Parinacota", -18.17, -69.14, 6348, "Arica y Parinacota", "norte", 0),
    Volcano("Guallatiri", -18.42, -69.09, 6071, "Arica y Parinacota", "norte", 15),
    Volcano("Isluga", -19.15, -68.83, 5550, "Tarapacá", "norte", 18),
    Volcano("Irruputuncu", -20.73, -68.56, 5163, "Tarapacá", "norte", 22),
    Volcano("Olca", -20.95, -68.48, 5407, "Tarapacá", "norte", 0),
    Volcano("Aucanquilcha", -21.22, -68.47, 6176, "Antofagasta", "norte", 0),
    Volcano("Ollagüe", -21.30, -68.18, 5868, "Antofagasta", "norte", 25),
    Volcano("San Pedro", -21.88, -68.40, 6145, "Antofagasta", "norte", 0),
    Volcano("Putana", -22.57, -67.85, 5890, "Antofagasta", "norte", 23),
    Volcano("Láscar", -23.37, -67.73, 5592, "Antofagasta", "norte", 4),
    Volcano("Lastarria", -25.17, -68.50, 5697, "Atacama", "norte", 0),
    Volcano("Ojos del Salado", -27.12, -68.54, 6893, "Atacama", "norte", 0),
    # Andes Centrales — frontera Chile/Argentina (RNVV monitorea todos)
    Volcano("Tupungatito", -33.40, -69.80, 5640, "Metropolitana", "centro", 0),
    Volcano("Tupungato", -33.36, -69.77, 6570, "Metropolitana", "centro", 0),
    Volcano("Marmolejo", -33.73, -69.88, 6108, "Metropolitana", "centro", 0),
    Volcano("San José", -33.78, -69.90, 5856, "Metropolitana", "centro", 0),
    Volcano("Maipo", -34.16, -69.83, 5264, "Metropolitana", "centro", 0),
    Volcano("Tinguiririca", -34.81, -70.35, 4280, "O'Higgins", "centro", 0),
    Volcano("Nevado de Longaví", -36.19, -71.16, 3242, "Maule", "centro", 19),

    # ── Zona Central-Sur (ZVS) ──
    Volcano("Descabezado Grande", -35.58, -70.75, 3953, "Maule", "centro", 10),
    Volcano("Cerro Azul / Quizapu", -35.65, -70.76, 3788, "Maule", "centro", 0),
    Volcano("Planchón-Peteroa", -35.24, -70.57, 4107, "Maule", "centro", 12),
    Volcano("Laguna del Maule", -36.02, -70.49, 3092, "Maule", "centro", 7),
    Volcano("Nevados de Chillán", -36.86, -71.38, 3212, "Ñuble", "centro", 5),
    Volcano("Antuco", -37.41, -71.35, 2979, "Biobío", "centro", 14),
    Volcano("Copahue", -37.85, -71.17, 2997, "Biobío", "centro", 6),
    Volcano("Callaqui", -37.92, -71.45, 3164, "Biobío", "centro", 17),
    Volcano("Lonquimay", -38.38, -71.59, 2865, "Araucanía", "sur", 9),
    Volcano("Llaima", -38.69, -71.73, 3125, "Araucanía", "sur", 2),
    Volcano("Sollipulli", -38.97, -71.52, 2282, "Araucanía", "sur", 11),
    Volcano("Villarrica", -39.42, -71.93, 2847, "Araucanía", "sur", 1),
    Volcano("Quetrupillán", -39.50, -71.70, 2360, "Araucanía", "sur", 16),
    Volcano("Lanín", -39.64, -71.50, 3747, "Araucanía", "sur", 0),
    Volcano("Mocho-Choshuenco", -39.93, -72.03, 2422, "Los Ríos", "sur", 8),
    Volcano("Puyehue-Cordón Caulle", -40.59, -72.12, 2236, "Los Ríos", "sur", 3),
    Volcano("Casablanca / Antillanca", -40.77, -72.15, 1990, "Los Lagos", "sur", 0),
    Volcano("Osorno", -41.10, -72.49, 2652, "Los Lagos", "sur", 13),
    Volcano("Calbuco", -41.33, -72.61, 2003, "Los Lagos", "sur", 3),
    Volcano("Yate", -41.76, -72.40, 2187, "Los Lagos", "sur", 0),
    Volcano("Hornopirén", -41.87, -72.43, 1572, "Los Lagos", "sur", 0),
    Volcano("Huequi", -42.38, -72.58, 1318, "Los Lagos", "sur", 20),
    Volcano("Michinmahuida", -42.79, -72.44, 2404, "Los Lagos", "sur", 21),
    Volcano("Chaitén", -42.83, -72.65, 1122, "Los Lagos", "sur", 3),

    # ── Zona Austral (ZVA) ──
    Volcano("Corcovado", -43.19, -72.08, 2300, "Los Lagos", "austral", 0),
    Volcano("Melimoyu", -44.08, -72.87, 2400, "Aysén", "austral", 0),
    Volcano("Mentolat", -44.70, -73.08, 1660, "Aysén", "austral", 0),
    Volcano("Hudson", -45.90, -72.97, 1905, "Aysén", "austral", 3),
    Volcano("Lautaro", -49.02, -73.55, 3607, "Magallanes", "austral", 24),

    # ── TEMPORALES para testing de productos ceniza/SO2 ──
    # (volcanes activos fuera de Chile — eliminar cuando ya no se necesiten)
    Volcano("Kīlauea (Hawái)", 19.42, -155.29, 1247, "Hawaii USA", "test", 0),
    Volcano("Popocatépetl (México)", 19.02, -98.62, 5426, "México", "test", 0),
    # Volcanes muy activos en cobertura GOES-19 — utiles para replay
    # con datos reales recientes (RAMMB archive ultimos 28 dias).
    Volcano("Sangay (Ecuador)", -2.005, -78.341, 5286, "Ecuador", "test", 0),
    Volcano("Reventador (Ecuador)", -0.077, -77.66, 3562, "Ecuador", "test", 0),
    Volcano("Sabancaya (Perú)", -15.78, -71.85, 5976, "Peru", "test", 0),
]

# Volcanes prioritarios (matching VRP Chile + alta actividad reciente)
PRIORITY_VOLCANOES = [
    "Villarrica", "Láscar", "Copahue", "Puyehue-Cordón Caulle",
    "Calbuco", "Nevados de Chillán", "Llaima", "Hudson",
]


def get_volcano(name: str) -> Volcano | None:
    """Buscar volcán por nombre (case-insensitive, partial match)."""
    name_lower = name.lower()
    for v in CATALOG:
        if name_lower in v.name.lower():
            return v
    return None


def get_by_zone(zone: str) -> list[Volcano]:
    """Obtener volcanes por zona (norte, centro, sur, austral)."""
    return [v for v in CATALOG if v.zone == zone]


def get_priority() -> list[Volcano]:
    """Obtener volcanes prioritarios."""
    return [v for v in CATALOG if v.name in PRIORITY_VOLCANOES]


def get_bounds(volcanoes: list[Volcano], padding_deg: float = 0.5) -> dict:
    """Calcular bounding box para una lista de volcanes."""
    lats = [v.lat for v in volcanoes]
    lons = [v.lon for v in volcanoes]
    return {
        "lat_min": min(lats) - padding_deg,
        "lat_max": max(lats) + padding_deg,
        "lon_min": min(lons) - padding_deg,
        "lon_max": max(lons) + padding_deg,
    }
