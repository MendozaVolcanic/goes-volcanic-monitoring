"""Perfil vertical de temperatura y altura geopotencial (GFS vía Open-Meteo).

Por qué importa (geología → pipeline): el retrieval de altura de pluma NO mide
la altura directo — mide una **temperatura efectiva del tope** (Teff ≈ la BT del
tope opaco) y la convierte a kilómetros buscándola dentro de un **perfil vertical
de temperatura T(z)** del modelo meteorológico. Sin ese perfil, cualquier
"altura" que calculemos es solo una cota. Este módulo aporta el perfil — la pieza
que habilita la conversión Teff→altura propia (Fase 2 del VOLCAT propio), de la
que dependen el BT-matching (Fase 3a) y cualquier método posterior.

Fuente: **Open-Meteo pressure-level API** (modelo GFS), la misma API pública sin
autenticación que ya usamos para el viento (``src/fetch/wind_data.py``). Devuelve
temperatura (°C → la pasamos a K) y altura geopotencial (m) por nivel de presión.
Cero dependencias nuevas. GFS se actualiza cada 6 h; la resolución vertical es
gruesa (~19 niveles) → producto INDICATIVO.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

import numpy as np
import requests

logger = logging.getLogger(__name__)

OPENMETEO_URL = "https://api.open-meteo.com/v1/forecast"
TIMEOUT = 15

# Niveles de presión GFS (hPa), de superficie a estratosfera baja. Open-Meteo
# expone temperature_<N>hPa y geopotential_height_<N>hPa para cada uno.
GFS_LEVELS_HPA = [1000, 975, 950, 925, 900, 850, 800, 700, 600, 500, 400, 300,
                  250, 200, 150, 100, 70, 50, 30]


def _parse_profile(hourly: dict, hour_idx: int) -> list[dict]:
    """Construir el perfil ordenado por altura desde la respuesta Open-Meteo.

    Cada nivel: ``{"p_hPa", "z_m", "T_K"}``. Convierte °C→K y descarta niveles
    con datos faltantes (None o índice fuera de rango). Función PURA.
    """
    levels = []
    for p in GFS_LEVELS_HPA:
        t_list = hourly.get(f"temperature_{p}hPa") or []
        z_list = hourly.get(f"geopotential_height_{p}hPa") or []
        if hour_idx >= len(t_list) or hour_idx >= len(z_list):
            continue
        t_c, z_m = t_list[hour_idx], z_list[hour_idx]
        if t_c is None or z_m is None:
            continue
        levels.append({"p_hPa": p, "z_m": float(z_m), "T_K": float(t_c) + 273.15})
    levels.sort(key=lambda d: d["z_m"])
    return levels


def _tropopause(levels: list[dict]) -> Optional[dict]:
    """Tropopausa ≈ **punto frío** (T mínima) entre ~6 y 20 km.

    Definición simple y robusta para un perfil grueso (GFS por niveles): basta
    para acotar el mapeo Teff→altura (no se interpola por encima de la
    tropopausa). No es la definición WMO de tasa de lapso, pero para un producto
    INDICATIVO el punto frío es defendible y estable.
    """
    cand = [l for l in levels if 6000 <= l["z_m"] <= 20000]
    if not cand:
        return None
    return min(cand, key=lambda l: l["T_K"])


def fetch_gfs_profile(
    lat: float, lon: float, dt: Optional[datetime] = None
) -> Optional[dict]:
    """Perfil GFS T(z) + tropopausa en (lat, lon) a la hora más cercana a ``dt``.

    Args:
        lat, lon: punto (grados decimales).
        dt:       instante UTC objetivo (default: ahora). Se elige la hora del
                  forecast más cercana.

    Returns:
        dict con ``levels`` (lista ordenada por altura de {p_hPa, z_m, T_K}),
        ``tropopause`` (dict o None), ``lat``/``lon``, ``valid_time`` (ISO),
        ``source``. None si la API falla o no hay datos.
    """
    if dt is None:
        dt = datetime.now(timezone.utc)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    hourly_vars = ",".join(
        f"temperature_{p}hPa,geopotential_height_{p}hPa" for p in GFS_LEVELS_HPA
    )
    # surface_temperature = skin-T radiativa de GFS (no la T2m del aire). Es el
    # FALLBACK de fondo cálido para el retrieval Wen-Rose (Fase 3b) cuando la
    # escena no tiene suficientes píxeles de cielo claro para estimar Ts. Ver
    # docs/own_volcat/FASE3B_WENROSE.md §3 (por qué skin-T y no GOES LST).
    hourly_vars += ",surface_temperature"
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": hourly_vars,
        "forecast_days": 1,
        "past_days": 2,           # permite datar scans recientes (hasta ~2 días)
        "models": "gfs_seamless",
        "timezone": "UTC",
    }
    try:
        r = requests.get(OPENMETEO_URL, params=params, timeout=TIMEOUT)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        logger.warning("Open-Meteo perfil (%s,%s): %s", lat, lon, e)
        return None

    hourly = data.get("hourly", {})
    times = hourly.get("time") or []
    if not times:
        return None

    # Elegir el índice de la hora más cercana a dt + medir el gap real.
    def _gap_s(ts: str) -> float:
        try:
            t = datetime.strptime(ts, "%Y-%m-%dT%H:%M").replace(tzinfo=timezone.utc)
            return abs((t - dt).total_seconds())
        except Exception:
            return float("inf")

    target = dt.strftime("%Y-%m-%dT%H:00")
    hour_idx = times.index(target) if target in times else min(
        range(len(times)), key=lambda i: _gap_s(times[i]))
    gap_min = _gap_s(times[hour_idx]) / 60.0

    # Si dt cae FUERA de la ventana del forecast (past_days/forecast_days), el
    # "más cercano" puede estar a días → avisamos pero devolvemos igual: el perfil
    # T(z) varía poco día a día y el producto es INDICATIVO. El caller ve el gap.
    if gap_min > 180:
        logger.warning("GFS perfil (%s,%s): hora más cercana a %d min de dt",
                       lat, lon, int(gap_min))

    levels = _parse_profile(hourly, hour_idx)
    if len(levels) < 3:
        return None

    # Skin-T (°C→K) de la hora elegida; None si Open-Meteo no la trae.
    skin_list = hourly.get("surface_temperature") or []
    skin_k = None
    if hour_idx < len(skin_list) and skin_list[hour_idx] is not None:
        skin_k = float(skin_list[hour_idx]) + 273.15

    return {
        "levels": levels,
        "tropopause": _tropopause(levels),
        "skin_temp_K": skin_k,
        "lat": lat,
        "lon": lon,
        "valid_time": times[hour_idx],
        "time_gap_min": round(gap_min, 1),
        "source": "GFS (Open-Meteo pressure levels)",
    }


def _monotone_tropo_branch(profile: dict) -> list[dict]:
    """Rama troposférica (superficie → tropopausa) con T **estrictamente
    decreciente**.

    GFS sub-tropical de invierno chileno suele tener **inversiones** (capa
    cálida sobre superficie fría, o inversión de subsidencia a ~3 km): T(z) NO
    es monótona en la troposfera. Recorremos de superficie hacia arriba y
    conservamos un nivel solo si es MÁS FRÍO que el último conservado (descarta
    los niveles de inversión, quedándonos con el de menor altitud) → "envolvente
    fría". Así el mapeo BT→altitud queda monótono, vectorizable con ``np.interp``
    y con semántica de **cota inferior** (la primera altitud donde el aire llega
    a esa temperatura), en vez del bug de ``argsort(T)`` que mezcla altitudes a
    través de la inversión. (review jun 2026)
    """
    levels = (profile or {}).get("levels") or []
    if not levels:
        return []
    trop = (profile or {}).get("tropopause")
    z_trop = trop["z_m"] if trop else levels[-1]["z_m"]
    kept: list[dict] = []
    for l in levels:
        if l["z_m"] > z_trop:
            break
        if not kept or l["T_K"] < kept[-1]["T_K"]:
            kept.append(l)
    return kept


def altitudes_from_bt(bt, profile: dict) -> np.ndarray:
    """Mapear un array de BT(11 µm) a altitud (m) vía el perfil T(z). PURA,
    vectorizada y robusta a inversiones.

    Usa la rama monótona ``_monotone_tropo_branch`` + ``np.interp`` (clampa a los
    extremos → BT más fría que la tropopausa cae en la tropopausa; más cálida que
    la superficie, en la superficie). Es la MISMA lógica que ``height_from_temp``
    (que ahora es su envoltura escalar) → producción y test comparten código.
    NaN donde la BT es NaN.
    """
    bt = np.asarray(bt, dtype="float64")
    kept = _monotone_tropo_branch(profile or {})
    if len(kept) < 2:
        return np.full(bt.shape, np.nan)
    T = np.array([l["T_K"] for l in kept], dtype="float64")   # estricta decreciente
    Z = np.array([l["z_m"] for l in kept], dtype="float64")   # ascendente
    # np.interp necesita xp ascendente → invertir (T asc, Z desc).
    out = np.interp(bt, T[::-1], Z[::-1])
    return np.where(np.isfinite(bt), out, np.nan)


def height_from_temp(temp_k: float, profile: dict) -> Optional[dict]:
    """Mapear una temperatura de brillo del tope (Teff) a altitud vía T(z).

    Envoltura escalar de :func:`altitudes_from_bt` (misma lógica de la rama
    monótona) que además etiqueta el caso de cota:

    Returns:
        dict ``{"z_m", "capped"}`` o None. ``capped``:
          - ``None``: interpolación dentro de la troposfera.
          - ``"surface"``: Teff más cálida que la superficie → cota en superficie.
          - ``"tropopause"``: Teff más fría que la tropopausa → cota en la
            tropopausa (posible overshooting o cirros mal detectados; este método
            no resuelve por encima).
    """
    kept = _monotone_tropo_branch(profile or {})
    if len(kept) < 2:
        return None
    z_surf, T_surf = kept[0]["z_m"], kept[0]["T_K"]
    z_trop, T_trop = kept[-1]["z_m"], kept[-1]["T_K"]
    if temp_k >= T_surf:
        return {"z_m": z_surf, "capped": "surface"}
    if temp_k <= T_trop:
        return {"z_m": z_trop, "capped": "tropopause"}
    z = float(altitudes_from_bt(np.array([temp_k]), profile)[0])
    return {"z_m": z, "capped": None}
