"""Hot spots térmicos VIIRS 375 m vía NASA FIRMS (anomalías térmicas como puntos).

Por qué (geología → pipeline): FIRMS (*Fire Information for Resource Management
System*) publica en casi-tiempo-real las detecciones de anomalía térmica de MODIS y
VIIRS como PUNTOS (lat, lon, FRP, temperatura de brillo, confianza). Aunque el
producto se llama "fire", detecta cualquier fuente de calor intensa — **incluidos
los hot spots volcánicos** (lava, domo caliente, lago de lava). Es el análogo POLAR
de nuestros hot spots FDCF de GOES: FDCF es geoestacionario (2 km, cada 10 min);
FIRMS/VIIRS es polar (**375 m**, ~2 ventanas/día). Para volcanes australes sin
sector VOLCAT ni monitoreo GOES dedicado, da una alerta térmica objetiva de alta
resolución cuando el satélite pasa.

Complemento INDICATIVO, separado de la cadena ABI NRT.

Acceso: API pública de FIRMS, requiere un **MAP_KEY gratis** (registrar un email en
https://firms.modaps.eosdis.nasa.gov/api/map_key). Se pasa por argumento o por la
variable de entorno ``FIRMS_MAP_KEY``. Endpoint 'area':
``/api/area/csv/{MAP_KEY}/{SOURCE}/{W,S,E,N}/{días}[/{fecha}]``.
"""

from __future__ import annotations

import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

FIRMS_BASE = "https://firms.modaps.eosdis.nasa.gov/api/area/csv"
TIMEOUT = 30

# Fuentes VIIRS de FIRMS (NRT = near-real-time; SP = standard/histórico). SNPP tiene
# la serie más larga; NOAA-20/21 amplían la constelación (más pasadas/día).
VIIRS_SOURCES = ("VIIRS_SNPP_NRT", "VIIRS_NOAA20_NRT", "VIIRS_NOAA21_NRT")

# Índices de columna del CSV FIRMS (VIIRS). Orden fijo del endpoint 'area'.
_COLS = ("latitude", "longitude", "bright_ti4", "scan", "track", "acq_date",
         "acq_time", "satellite", "instrument", "confidence", "version",
         "bright_ti5", "frp", "daynight")


def _bbox_to_area(bounds: dict) -> str:
    """bbox lat/lon → string 'West,South,East,North' que espera FIRMS. PURA.

    OJO al orden: FIRMS usa (lon_min, lat_min, lon_max, lat_max), NO el
    (lat,lon) del WMS. Un orden equivocado consulta la otra punta del planeta.
    """
    return (f"{bounds['lon_min']:g},{bounds['lat_min']:g},"
            f"{bounds['lon_max']:g},{bounds['lat_max']:g}")


def _build_area_url(map_key: str, source: str, bounds: dict, days: int = 1,
                    when: Optional[str] = None) -> str:
    """URL del endpoint 'area' de FIRMS. PURA. ``when`` (YYYY-MM-DD) = fecha de
    inicio opcional; sin ella, FIRMS devuelve los últimos ``days`` días."""
    area = _bbox_to_area(bounds)
    url = f"{FIRMS_BASE}/{map_key}/{source}/{area}/{int(days)}"
    if when:
        url += f"/{when}"
    return url


def _to_float(s: str):
    try:
        v = float(s)
        # descarta NaN/inf (FIRMS a veces trae strings raros)
        return v if v == v and abs(v) != float("inf") else None
    except (ValueError, TypeError):
        return None


def _parse_firms_csv(text: str) -> list:
    """Parsear el CSV del endpoint 'area' de FIRMS → lista de dicts. PURA.

    Cada hot spot: ``{lat, lon, frp_mw, bright_ti4_k, bright_ti5_k, confidence,
    acq_date, acq_time, satellite, daynight}``. Filas con lat/lon/FRP no numéricos o
    columnas faltantes se descartan. Respuestas que no son CSV (p.ej. el texto
    'Invalid MAP_KEY.') devuelven lista vacía.
    """
    lines = [ln for ln in (text or "").splitlines() if ln.strip()]
    if not lines:
        return []
    header = lines[0].split(",")
    if "latitude" not in header or "longitude" not in header:
        return []                      # no es el CSV esperado (error del servicio)
    idx = {name: header.index(name) for name in _COLS if name in header}
    out = []
    for ln in lines[1:]:
        parts = ln.split(",")
        if len(parts) < len(header):
            continue
        lat = _to_float(parts[idx["latitude"]])
        lon = _to_float(parts[idx["longitude"]])
        frp = _to_float(parts[idx["frp"]]) if "frp" in idx else None
        if lat is None or lon is None or frp is None:
            continue
        out.append({
            "lat": lat, "lon": lon, "frp_mw": frp,
            "bright_ti4_k": _to_float(parts[idx["bright_ti4"]]) if "bright_ti4" in idx else None,
            "bright_ti5_k": _to_float(parts[idx["bright_ti5"]]) if "bright_ti5" in idx else None,
            "confidence": parts[idx["confidence"]] if "confidence" in idx else None,
            "acq_date": parts[idx["acq_date"]] if "acq_date" in idx else None,
            "acq_time": parts[idx["acq_time"]] if "acq_time" in idx else None,
            "satellite": parts[idx["satellite"]] if "satellite" in idx else None,
            "daynight": parts[idx["daynight"]] if "daynight" in idx else None,
        })
    return out


def fetch_viirs_firms_hotspots(
    bounds: dict, days: int = 1, map_key: Optional[str] = None,
    source: str = "VIIRS_SNPP_NRT", when: Optional[str] = None,
) -> Optional[list]:
    """Hot spots térmicos VIIRS 375 m en ``bounds`` desde FIRMS.

    Args:
        bounds:   dict lat_min/lat_max/lon_min/lon_max.
        days:     ventana hacia atrás (1-10) desde hoy o desde ``when``.
        map_key:  clave FIRMS; si None, se lee de ``FIRMS_MAP_KEY`` (env).
        source:   fuente VIIRS (SNPP/NOAA20/NOAA21 NRT).
        when:     fecha de inicio ``YYYY-MM-DD`` (opcional).

    Returns:
        Lista de hot spots (dicts) — posiblemente vacía si no hubo detecciones.
        ``None`` si falta el MAP_KEY o falla la red (distinto de "vacía" = sin calor).
    """
    key = map_key or os.environ.get("FIRMS_MAP_KEY")
    if not key:
        logger.warning("FIRMS: sin MAP_KEY (arg ni env FIRMS_MAP_KEY). Registralo "
                       "gratis en https://firms.modaps.eosdis.nasa.gov/api/map_key")
        return None
    if source not in VIIRS_SOURCES:
        logger.warning("FIRMS: fuente %s no es VIIRS (%s)", source, VIIRS_SOURCES)
    try:
        import requests
    except ImportError as e:
        logger.error("requests no disponible: %s", e)
        return None
    url = _build_area_url(key, source, bounds, days=days, when=when)
    try:
        r = requests.get(url, timeout=TIMEOUT)
        r.raise_for_status()
    except Exception as e:
        logger.warning("FIRMS area (%s): %s", source, e)
        return None
    return _parse_firms_csv(r.text)
