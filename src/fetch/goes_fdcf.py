"""Cliente para producto NOAA L2 FDCF (Fire/Hot spot Characterization, Full Disk).

FDCF es producto pre-procesado por NOAA del Advanced Baseline Imager (ABI) que
identifica píxeles calientes (incendios + actividad volcánica) usando algoritmo
multi-banda (3.9 µm, 11 µm, 12 µm) con calibración dinámica.

Variables clave del NetCDF:
- ``Mask``  (5424×5424 uint8): clasificación de píxel
    - 10/11 = fuego de buena calidad, alta confianza
    - 12/13 = fuego con saturación
    - 14/15 = fuego de baja confianza
    - 30+   = nube / sin datos / fuera del disco
- ``Power`` (float32): potencia radiativa del fuego en MW
- ``Temp``  (float32): temperatura de brillo del píxel caliente, K
- ``Area``  (float32): área de superficie afectada, km² (sub-pixel)
- ``DQF``   (uint8): flag de calidad del dato

Cadencia FDCF Full Disk: cada 10 min (sigue al scan de GOES-19).
Latencia: ~6-8 min después del fin del scan (más que RAMMB).

Para volcanes chilenos los hotspots típicos son **muy pocos por scan** (0-3
en todo Chile). El algoritmo FDCF está optimizado para incendios forestales —
algunas erupciones efusivas como Villarrica las detecta bien (cuando hay
lava expuesta), pero erupciones explosivas con cenizas frías NO disparan
hotspots térmicos.

Cross-check con VRP (MODIS/VIIRS) sigue siendo necesario para validar.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)

# Cuál es el archivo S3 para FDCF Full Disk
S3_BUCKET = "noaa-goes19"
S3_PRODUCT = "ABI-L2-FDCF"

# Categorías de Mask que consideramos "hotspot real"
# (10-15 son detecciones; 30+ son nube/no-fire/sin-datos)
HOTSPOT_MASK_VALUES = {10, 11, 12, 13, 14, 15}

# Subset de mask values con alta confianza (sin saturacion ni baja conf)
HIGH_CONF_MASK = {10, 11}


@dataclass
class HotSpot:
    """Un punto detectado como caliente en un scan FDCF."""
    lat: float
    lon: float
    frp_mw: float            # Fire Radiative Power, MW
    temp_k: float            # Temperatura de brillo, K
    area_km2: float          # Sub-pixel area
    mask: int                # categoria FDCF
    confidence: str          # 'high' | 'medium' | 'low' | 'saturated'

    def to_dict(self) -> dict:
        return {
            "lat": self.lat, "lon": self.lon,
            "frp_mw": self.frp_mw, "temp_k": self.temp_k,
            "area_km2": self.area_km2,
            "mask": self.mask, "confidence": self.confidence,
        }


def _parse_scan_time(s3_path: str) -> Optional[datetime]:
    """Extraer datetime UTC del nombre del archivo NOAA.

    Nombre tipico:
        OR_ABI-L2-FDCF-M6_G19_s20261151200216_e20261151209524_c20261151210037.nc
                                 ^^^^^^^^^^^^^^^
                                 s = start time
                                 yyyy=2026 doy=115 hh=12 mm=00 ss=21
    """
    try:
        name = s3_path.split("/")[-1]
        token = [t for t in name.split("_") if t.startswith("s") and len(t) >= 14][0]
        yyyy = int(token[1:5])
        doy  = int(token[5:8])
        hh   = int(token[8:10])
        mm   = int(token[10:12])
        ss   = int(token[12:14])
        # 1 enero del año + (doy - 1) dias da el dia correcto.
        # Ej: 2026 doy=115 -> 25 abril 2026
        base = datetime(yyyy, 1, 1, hh, mm, ss, tzinfo=timezone.utc)
        return base + timedelta(days=doy - 1)
    except Exception as e:
        logger.warning("No pude parsear timestamp de %s: %s", s3_path, e)
        return None


def _confidence_from_mask(mask: int) -> str:
    if mask in (10, 11):
        return "high"
    if mask in (12, 13):
        return "saturated"
    if mask in (14, 15):
        return "low"
    return "unknown"


def _list_recent_files(s3, hours_back: int = 1) -> list[str]:
    """Listar archivos FDCF recientes (ultimas N horas)."""
    now = datetime.now(timezone.utc)
    keys = []
    for h in range(hours_back + 1):
        t = now - timedelta(hours=h)
        prefix = (
            f"{S3_BUCKET}/{S3_PRODUCT}/"
            f"{t.year}/{t.timetuple().tm_yday:03d}/{t.hour:02d}/"
        )
        try:
            keys.extend(s3.ls(prefix))
        except FileNotFoundError:
            continue
        except Exception as e:
            logger.warning("Listando %s: %s", prefix, e)
    # Ordenar por nombre (los archivos NOAA llevan timestamp en el nombre)
    keys.sort(reverse=True)
    return keys


def _abi_to_latlon(
    x_rad: np.ndarray, y_rad: np.ndarray, sat_lon: float = -75.0,
) -> tuple[np.ndarray, np.ndarray]:
    """Convertir coords ABI fixed grid (radianes) a lat/lon.

    Las coords x/y del ABI son angulos visto desde el satelite (sweep mode 'x').
    Usamos pyproj GEOS para reproyectar.
    """
    try:
        from pyproj import Proj
    except ImportError:
        logger.error("pyproj requerido para reproyectar FDCF")
        return np.zeros_like(x_rad), np.zeros_like(y_rad)

    h = 35786023.0
    p = Proj(proj="geos", lon_0=sat_lon, h=h, ellps="GRS80", sweep="x")

    # x/y radianes → metros
    x_m = x_rad * h
    y_m = y_rad * h
    lon, lat = p(x_m, y_m, inverse=True)
    return lat, lon


def fetch_latest_hotspots(
    bounds: Optional[dict] = None,
    high_conf_only: bool = False,
    hours_back: int = 1,
) -> tuple[list[HotSpot], Optional[datetime]]:
    """Bajar el FDCF más reciente y devolver hotspots filtrados por bbox.

    Args:
        bounds:           dict con lat_min/lat_max/lon_min/lon_max para filtrar.
                          None = no filtra (devuelve hotspots globales).
        high_conf_only:   Si True, solo Mask ∈ {10, 11}. Default False
                          (incluye baja confianza y saturados, marcados aparte).
        hours_back:       Cuántas horas atrás buscar si no encuentra archivos
                          en la hora actual. Default 1.

    Returns:
        (hotspots, scan_dt) — lista de HotSpot y datetime del scan.
        Si no encuentra nada, ([], None).
    """
    try:
        import s3fs
        import xarray as xr
    except ImportError as e:
        logger.error("s3fs/xarray no disponible: %s", e)
        return [], None

    s3 = s3fs.S3FileSystem(anon=True)
    keys = _list_recent_files(s3, hours_back=hours_back)
    if not keys:
        logger.warning("FDCF: no hay archivos en las ultimas %dh", hours_back)
        return [], None

    latest = keys[0]
    logger.info("FDCF: leyendo %s", latest)

    try:
        with s3.open(latest, "rb") as f:
            ds = xr.open_dataset(f, engine="h5netcdf")
            mask = ds["Mask"].values
            power = ds["Power"].values
            temp = ds["Temp"].values
            area = ds["Area"].values
            x_rad = ds["x"].values
            y_rad = ds["y"].values
            # sat_lon del proyectado
            sat_lon = float(
                ds["goes_imager_projection"].attrs.get(
                    "longitude_of_projection_origin", -75.0
                )
            )
            # Time del scan — parsear del nombre del archivo (mas robusto que
            # decodificar variable 't' en J2000 segundos)
            scan_dt = _parse_scan_time(latest)
    except Exception as e:
        logger.exception("Error leyendo FDCF %s: %s", latest, e)
        return [], None

    # ── Filtrar mascara por categoria fire ───────────────────────────────
    valid_mask_set = HIGH_CONF_MASK if high_conf_only else HOTSPOT_MASK_VALUES
    hot_idx = np.isin(mask, list(valid_mask_set)) & np.isfinite(power)
    if not hot_idx.any():
        return [], scan_dt

    rows, cols = np.where(hot_idx)
    # x_rad es 1D (cols), y_rad es 1D (rows). Hacer meshgrid solo para los
    # indices encontrados — mucho mas barato que sacar full grid.
    x_pts = x_rad[cols]
    y_pts = y_rad[rows]
    lats, lons = _abi_to_latlon(x_pts, y_pts, sat_lon=sat_lon)

    # Filtrar por bbox si pidieron
    if bounds is not None:
        keep = (
            (lats >= bounds["lat_min"]) & (lats <= bounds["lat_max"]) &
            (lons >= bounds["lon_min"]) & (lons <= bounds["lon_max"])
        )
        if not keep.any():
            return [], scan_dt
        rows = rows[keep]; cols = cols[keep]
        lats = lats[keep]; lons = lons[keep]

    hotspots = []
    for i in range(len(rows)):
        r, c = int(rows[i]), int(cols[i])
        m_v = int(mask[r, c])
        hotspots.append(HotSpot(
            lat=float(lats[i]),
            lon=float(lons[i]),
            frp_mw=float(power[r, c]) if np.isfinite(power[r, c]) else 0.0,
            temp_k=float(temp[r, c]) if np.isfinite(temp[r, c]) else 0.0,
            area_km2=float(area[r, c]) if np.isfinite(area[r, c]) else 0.0,
            mask=m_v,
            confidence=_confidence_from_mask(m_v),
        ))

    # Ordenar por FRP descendente (los mas intensos arriba)
    hotspots.sort(key=lambda h: h.frp_mw, reverse=True)
    return hotspots, scan_dt
