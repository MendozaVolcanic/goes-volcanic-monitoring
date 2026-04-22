"""Datos de viento GFS via OpenMeteo para visualizacion de trayectorias.

Obtiene viento en niveles de presion (300, 500, 850 hPa) sobre una
grilla regular en Chile para overlay sobre mapas de ceniza/SO2.

API: open-meteo.com (publica, sin autenticacion, modelos GFS/ECMWF).
GFS se actualiza cada 6 horas; la cache de Streamlit se renueva cada hora.

Convencion meteorologica de viento:
  direction=0   → viento viene del Norte (se mueve hacia el Sur)
  direction=90  → viento viene del Este  (se mueve hacia el Oeste)
  u = -speed * sin(direction)   [positivo = hacia el Este]
  v = -speed * cos(direction)   [positivo = hacia el Norte]
"""

import logging
import math
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone

import requests

logger = logging.getLogger(__name__)

OPENMETEO_URL = "https://api.open-meteo.com/v1/forecast"
TIMEOUT = 12

# Grilla sobre Chile y zona volcanica sudamericana
# 10 latitudes × 5 longitudes = 50 puntos
WIND_LATS = [-17, -21, -25, -29, -33, -37, -41, -45, -49, -53]
WIND_LONS = [-79, -75, -71, -67, -63]

# Niveles de presion disponibles.
# Open-Meteo cambio la convencion en 2025: ahora usa "wind_speed_<N>hPa"
# (antes "windspeed_<N>hpa"). El formato viejo devuelve HTTP 400.
WIND_LEVELS = {
    "300 hPa": "300hPa",   # ~9 km — plumas altas (erupciones explosivas)
    "500 hPa": "500hPa",   # ~5.5 km — circulacion media (mas comun)
    "850 hPa": "850hPa",   # ~1.5 km — capa limite / plumas bajas
}
DEFAULT_LEVEL = "500hPa"


def fetch_wind_point(lat: float, lon: float, level: str = DEFAULT_LEVEL) -> dict | None:
    """Obtener viento en un punto para la hora UTC actual (GFS).

    Args:
        lat:   Latitud en grados decimales.
        lon:   Longitud en grados decimales.
        level: Nivel de presion (e.g. '500hpa', '850hpa', '300hpa').

    Returns:
        Dict con lat, lon, speed (km/h), direction (grados), u, v, o None si falla.
    """
    params = {
        "latitude":     lat,
        "longitude":    lon,
        "hourly":       f"wind_speed_{level},wind_direction_{level}",
        "forecast_days": 1,
        "models":       "gfs_seamless",
        "timezone":     "UTC",
        "wind_speed_unit": "kmh",
    }
    try:
        r = requests.get(OPENMETEO_URL, params=params, timeout=TIMEOUT)
        r.raise_for_status()
        data = r.json()
        hourly = data.get("hourly", {})

        now_hour = datetime.now(timezone.utc).hour
        speed     = hourly.get(f"wind_speed_{level}", [None] * 24)[now_hour]
        direction = hourly.get(f"wind_direction_{level}", [None] * 24)[now_hour]

        if speed is None or direction is None:
            return None

        dir_rad = math.radians(direction)
        u_kmh = -speed * math.sin(dir_rad)   # positivo = hacia el Este
        v_kmh = -speed * math.cos(dir_rad)   # positivo = hacia el Norte

        return {
            "lat":       lat,
            "lon":       lon,
            "speed":     round(speed, 1),
            "direction": round(direction, 1),
            "u":         u_kmh,
            "v":         v_kmh,
        }
    except Exception as e:
        logger.debug("OpenMeteo (%s, %s) lvl=%s: %s", lat, lon, level, e)
        return None


def fetch_wind_grid(
    lats: list[float] | None = None,
    lons: list[float] | None = None,
    level: str = DEFAULT_LEVEL,
) -> list[dict]:
    """Obtener viento para una grilla de puntos en paralelo.

    Args:
        lats:  Lista de latitudes. Default: WIND_LATS (Chile).
        lons:  Lista de longitudes. Default: WIND_LONS (Chile).
        level: Nivel de presion.

    Returns:
        Lista de dicts con datos de viento, ordenada por (lat, lon).
        Puntos con error son omitidos silenciosamente.
    """
    if lats is None:
        lats = WIND_LATS
    if lons is None:
        lons = WIND_LONS

    points = [(lat, lon) for lat in lats for lon in lons]
    results = []

    with ThreadPoolExecutor(max_workers=12) as ex:
        futures = {
            ex.submit(fetch_wind_point, lat, lon, level): (lat, lon)
            for lat, lon in points
        }
        for fut in as_completed(futures):
            result = fut.result()
            if result is not None:
                results.append(result)

    return sorted(results, key=lambda w: (w["lat"], w["lon"]))
