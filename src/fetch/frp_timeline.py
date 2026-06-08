"""Serie temporal intradía de FRP (Fire Radiative Power) por volcán — la
fortaleza ÚNICA de GOES frente a MODIS/VIIRS.

Por qué existe este módulo (el "por qué" antes que el "cómo"):

GOES es geoestacionario → ve el MISMO punto cada 10 min (~144 scans/día).
MODIS/VIIRS son polares → 2-4 pasadas/día. Para *magnitud* y *sensibilidad*
térmica los polares ganan (375 m–1 km vs ~2 km en nadir, peor aún en el sur
de Chile por el ángulo oblicuo). Pero para la *evolución temporal* de un
evento efusivo —el encendido y la escalada entre pasadas polares— GOES no
tiene rival. Este módulo construye esa curva intradía de FRP que MODIS/VIIRS
no puede dar.

Limitación física honesta: el algoritmo FDCF rara vez dispara sobre volcanes
chilenos (0-3 hotspots en todo Chile por scan; las explosivas con ceniza fría
NO calientan el pixel). Así que esta serie es CERO la mayor parte del tiempo
y "se enciende" sólo durante actividad efusiva con lava expuesta (típico:
Villarrica, Láscar). Eso es exactamente cuando la cadencia de 10 min importa.

Dos piezas:
- ``sum_frp_per_volcano``: agregación PURA (suma de FRP en MW dentro de un
  radio de cada volcán). Testeable sin red.
- ``fetch_scan_sliced``: lee el FDCF más cercano a un ``dt`` pero recortando
  el grid fijo ABI al sub-bloque que cubre Chile → ~1 s/scan en vez de ~15 s
  del lector full-disk. No toca el path de ``goes_fdcf`` ya probado.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

import numpy as np

# Reusar helpers ya probados de goes_fdcf (no duplicar lógica de parsing/proj).
from src.fetch.goes_fdcf import (
    HIGH_CONF_MASK,
    HOTSPOT_MASK_VALUES,
    HotSpot,
    _abi_to_latlon,
    _confidence_from_mask,
    _H_DEFAULT,
    _list_files_at_hour,
    _parse_scan_time,
    _SAT_LON_DEFAULT,
)

logger = logging.getLogger(__name__)

# Bbox Chile + márgenes vecinos cubiertos por GOES-19.
CHILE_BBOX = {
    "lat_min": -56, "lat_max": -17,
    "lon_min": -76, "lon_max": -66,
}


def sum_frp_per_volcano(
    hotspots: list,
    volcanoes: list,
    radius_km: float = 50.0,
) -> tuple[dict[str, float], dict[str, int]]:
    """Suma de FRP (MW) y conteo de hotspots ≤``radius_km`` de cada volcán.

    Args:
        hotspots:  lista de HotSpot (o cualquier objeto con .lat/.lon/.frp_mw).
        volcanoes: lista de Volcano (objetos con .name/.lat/.lon).
        radius_km: radio de atribución. 50 km da margen para el error de
                   geolocalización de GOES en el sur (vista oblicua).

    Returns:
        (frp_by_name, count_by_name) — dos dicts {nombre_volcán: valor}.
        frp en MW (float, redondeado a 1 decimal), count en pixeles (int).

    Nota: un hotspot puede contar para más de un volcán si ambos están
    dentro del radio (volcanes vecinos). Es intencional — preferimos no
    perder señal por desambiguar de más con la resolución gruesa de GOES.
    """
    frp_by_name: dict[str, float] = {}
    count_by_name: dict[str, int] = {}
    for v in volcanoes:
        total_frp = 0.0
        n = 0
        cos_lat = float(np.cos(np.radians(v.lat)))
        for h in hotspots:
            dlat = (h.lat - v.lat) * 111.0
            dlon = (h.lon - v.lon) * 111.0 * cos_lat
            d = float(np.hypot(dlat, dlon))
            if d <= radius_km:
                total_frp += float(getattr(h, "frp_mw", 0.0) or 0.0)
                n += 1
        frp_by_name[v.name] = round(total_frp, 1)
        count_by_name[v.name] = n
    return frp_by_name, count_by_name


def _chile_xy_index_range(
    x_rad: np.ndarray, y_rad: np.ndarray, sat_lon: float,
    bbox: dict = CHILE_BBOX, margin_rad: float = 0.003,
) -> Optional[tuple[int, int, int, int]]:
    """Índices [c0, c1, r0, r1] del sub-bloque ABI que cubre Chile.

    Proyecta una grilla de puntos del bbox a coords fixed-grid (radianes) y
    busca el rango de columnas (x) y filas (y) que los contienen, con margen.
    Devuelve None si el bbox cae fuera del disco (no debería para Chile).
    """
    try:
        from pyproj import Proj
    except ImportError:
        logger.error("pyproj requerido para recorte de región")
        return None

    h = _H_DEFAULT
    p = Proj(proj="geos", lon_0=sat_lon, h=h, ellps="GRS80", sweep="x")
    lon_grid, lat_grid = np.meshgrid(
        np.linspace(bbox["lon_min"], bbox["lon_max"], 6),
        np.linspace(bbox["lat_min"], bbox["lat_max"], 6),
    )
    x_m, y_m = p(lon_grid.ravel(), lat_grid.ravel())
    x_r = np.asarray(x_m) / h
    y_r = np.asarray(y_m) / h
    finite = np.isfinite(x_r) & np.isfinite(y_r)
    if not finite.any():
        return None
    x_r, y_r = x_r[finite], y_r[finite]
    xmin, xmax = x_r.min() - margin_rad, x_r.max() + margin_rad
    ymin, ymax = y_r.min() - margin_rad, y_r.max() + margin_rad

    c_idx = np.where((x_rad >= xmin) & (x_rad <= xmax))[0]
    r_idx = np.where((y_rad >= ymin) & (y_rad <= ymax))[0]
    if c_idx.size == 0 or r_idx.size == 0:
        return None
    return int(c_idx[0]), int(c_idx[-1]), int(r_idx[0]), int(r_idx[-1])


def fetch_scan_sliced(
    dt: datetime,
    bounds: Optional[dict] = None,
    high_conf_only: bool = False,
) -> tuple[list, Optional[datetime]]:
    """Lee el FDCF más cercano a ``dt`` recortando el grid a la región de Chile.

    Equivalente a ``goes_fdcf.fetch_hotspots_at_time`` pero ~15× más rápido:
    en vez de cargar Mask/Power/Temp/Area full-disk (5424×5424) carga sólo el
    sub-bloque que cubre el bbox. Pensado para barrer muchos scans (timeline).

    Returns:
        (hotspots, scan_dt_real) — ([], None) si no encuentra archivo.
    """
    try:
        import s3fs
        import xarray as xr
    except ImportError as e:
        logger.error("s3fs/xarray no disponible: %s", e)
        return [], None

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    s3 = s3fs.S3FileSystem(anon=True)
    keys = _list_files_at_hour(s3, dt)
    if not keys:
        keys = _list_files_at_hour(s3, dt - timedelta(hours=1))
    if not keys:
        return [], None

    def _delta(k):
        ts = _parse_scan_time(k)
        return float("inf") if ts is None else abs((ts - dt).total_seconds())

    chosen = min(keys, key=_delta)
    try:
        with s3.open(chosen, "rb") as f:
            ds = xr.open_dataset(f, engine="h5netcdf")
            x_rad = ds["x"].values
            y_rad = ds["y"].values
            sat_lon = float(
                ds["goes_imager_projection"].attrs.get(
                    "longitude_of_projection_origin", _SAT_LON_DEFAULT
                )
            )
            box = bounds or CHILE_BBOX
            rng = _chile_xy_index_range(x_rad, y_rad, sat_lon, bbox=box)
            if rng is None:
                # Fallback: leer full (no debería pasar para Chile)
                mask = ds["Mask"].values
                power = ds["Power"].values
                temp = ds["Temp"].values
                area = ds["Area"].values
                xs, ys = x_rad, y_rad
            else:
                c0, c1, r0, r1 = rng
                mask = ds["Mask"][r0:r1 + 1, c0:c1 + 1].values
                power = ds["Power"][r0:r1 + 1, c0:c1 + 1].values
                temp = ds["Temp"][r0:r1 + 1, c0:c1 + 1].values
                area = ds["Area"][r0:r1 + 1, c0:c1 + 1].values
                xs, ys = x_rad[c0:c1 + 1], y_rad[r0:r1 + 1]
            scan_dt = _parse_scan_time(chosen)
    except Exception as e:
        logger.warning("Error leyendo FDCF sliced %s: %s", chosen, e)
        return [], None

    valid = HIGH_CONF_MASK if high_conf_only else HOTSPOT_MASK_VALUES
    hot_idx = np.isin(mask, list(valid)) & np.isfinite(power)
    if not hot_idx.any():
        return [], scan_dt

    rows, cols = np.where(hot_idx)
    lats, lons = _abi_to_latlon(xs[cols], ys[rows], sat_lon=sat_lon)

    box = bounds or CHILE_BBOX
    keep = (
        (lats >= box["lat_min"]) & (lats <= box["lat_max"]) &
        (lons >= box["lon_min"]) & (lons <= box["lon_max"])
    )
    if not keep.any():
        return [], scan_dt
    rows, cols = rows[keep], cols[keep]
    lats, lons = lats[keep], lons[keep]

    hotspots = []
    for i in range(len(rows)):
        r, c = int(rows[i]), int(cols[i])
        m_v = int(mask[r, c])
        hotspots.append(HotSpot(
            lat=float(lats[i]), lon=float(lons[i]),
            frp_mw=float(power[r, c]) if np.isfinite(power[r, c]) else 0.0,
            temp_k=float(temp[r, c]) if np.isfinite(temp[r, c]) else 0.0,
            area_km2=float(area[r, c]) if np.isfinite(area[r, c]) else 0.0,
            mask=m_v, confidence=_confidence_from_mask(m_v),
        ))
    hotspots.sort(key=lambda h: h.frp_mw, reverse=True)
    return hotspots, scan_dt
