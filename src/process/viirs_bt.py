# ════════════════════════════════════════════════════════════════════
# FICHA SDA · viirs_bt.py · SDA: Monitoreo Volcánico GOES-19 · ID: SDA-GOES-01
# Objetivo      : leer y calibrar las bandas térmicas VIIRS 750m (M15 11µm, M16 12µm) para el retrieval de altura propio a mayor resolución que el ABI
# Lógica        : radiancia → temperatura de brillo (LUT del NetCDF, o inversión de Planck); recorte de swath por bbox del volcán
# Modelo/método : calibración determinística (LUT/Planck) — MISMO patrón que VRP Chile (reusado con atribución)
# Datos entrada : VNP02MOD/VJ102MOD (radiancia) + VNP03MOD/VJ103MOD (geolocalización) de NASA — SIN datos personales
# Variables     : BT(M15), BT(M16), lat/lon, sensor_zenith; flags de saturación y fill
# Limitaciones  : polar (swath, ~2 pasadas/día); satura ~423K; hereda quality-flags bit-2; VIIRS NO tiene canal CO2 13.3µm del ABI
# Refs/datos    : VIIRS L1B User Guide (Aug 2021); calibración clonada de VRP Chile pipeline/process_viirs_mod.py
# Ficha completa: docs/FICHA_SDA_GOES.md
# ════════════════════════════════════════════════════════════════════
"""Lectura y calibración de las bandas térmicas VIIRS 750 m (bandas M).

Por qué (geología → pipeline): el retrieval de altura de pluma del ABI está topado
a 2 km (techo del sondeador IR geoestacionario). VIIRS, polar, ve las mismas bandas
térmicas a **750 m** — 3× más fino. Este módulo lee y calibra las dos bandas que
necesita el split-window de Wen-Rose:
- **M15 (10.763 µm)** ≈ el 11 µm del ABI (canal "limpio").
- **M16 (12.013 µm)** ≈ el 12 µm del ABI (canal "sucio", absorción de vapor).

La diferencia M15−M16 da la corrección de emisividad de Wen-Rose, igual que la
11−12 del ABI. (VIIRS **no** tiene el canal CO₂ 13.3 µm del ABI → sin árbitro CO₂;
lo suple el 8.55 µm M14 para el tri-espectral, como en el ABI.)

La geolocalización viene del gránulo VNP03MOD (arrays lat/lon del swath, no una
grilla regular): se trabaja en espacio de swath y se recorta con máscara bbox
(haversine no hace falta para un bbox cuadrado). El fetch está en
``src/fetch/viirs_l1b.py``.

**Calibración clonada de VRP Chile** (`pipeline/process_viirs_mod.py`, madura y
validada en NRT): LUT del propio NetCDF (``M##_brightness_temperature_lut``) con
inversión de Planck como fallback + manejo de scale/offset, DN de flag y quality-
flags de saturación (bit-2). Acá se agrega **M16** (VRP Chile solo leía M13/M15).
"""

from __future__ import annotations

import logging
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)

# Longitudes de onda de las bandas M térmicas (µm). M15/M16 del ABI-análogo 11/12.
BAND_LAMBDA_UM = {"M13": 4.050, "M14": 8.550, "M15": 10.763, "M16": 12.013}

# DN reservados a flags (Missing_EV, Bowtie_Deleted, Cal_Fail, Fill) → NaN.
FLAG_DNS = frozenset({65532, 65533, 65534, 65535})

# Techo de saturación por banda (K) — arriba de esto el retrieval es basura.
BT_SAT_K = {"M13": 634.0, "M15": 423.0, "M16": 423.0}

# Constantes de Planck (mismas que VRP Chile / el ABI): C1 en W·µm⁴/(m²·sr), C2 en µm·K.
_C1 = 1.191042e8
_C2 = 14388.0
_SAT_BIT_MASK = 0b100     # quality_flags bit-2 = saturación (VIIRS L1B UserGuide C.1)


def planck_bt(rad, lambda_um: float):
    """Temperatura de brillo (K) desde radiancia espectral por inversión de Planck.
    PURA, vectorizada. NaN donde la radiancia es ≤0 o NaN."""
    rad = np.asarray(rad, dtype="float64")
    with np.errstate(invalid="ignore", divide="ignore"):
        bt = _C2 / (lambda_um * np.log(_C1 / (rad * lambda_um ** 5) + 1.0))
    return np.where(np.isfinite(rad) & (rad > 0), bt, np.nan)


def _calibrate_band(obs, band: str):
    """DN → BT de una banda M leyendo del grupo ``observation_data`` de un VNP02MOD.

    Prioriza el LUT del NetCDF (``{band}_brightness_temperature_lut``); si no está,
    usa scale/offset → radiancia → Planck. Aplica flags (DN reservados), quality-
    flags de saturación (bit-2) y clamp de saturación. Devuelve array float o None
    si la banda no está. Clona el contrato de VRP Chile (process_viirs_mod)."""
    if band not in obs:
        return None
    dn = obs[band][:]
    qf_key = f"{band}_quality_flags"
    qf = obs[qf_key][:] if qf_key in obs else None
    flag_mask = np.isin(dn, list(FLAG_DNS))

    lut_key = f"{band}_brightness_temperature_lut"
    if lut_key in obs:
        lut = obs[lut_key][:]
        bt = lut[dn].astype("float64")
        bt[flag_mask] = np.nan
        bt[bt < 0] = np.nan
    else:
        ds = obs[band]
        scale = float(ds.attrs.get("scale_factor", 1.0))
        offset = float(ds.attrs.get("add_offset", 0.0))
        rad = dn.astype("float64") * scale + offset
        rad[flag_mask] = np.nan
        bt = planck_bt(rad, BAND_LAMBDA_UM[band])

    if qf is not None:
        bt[(qf & _SAT_BIT_MASK) != 0] = np.nan
    sat = BT_SAT_K.get(band)
    if sat is not None:
        bt[bt >= sat - 0.5] = np.nan
    return bt


def read_mod_bt(l1b_path, bands=("M15", "M16")) -> dict:
    """Leer y calibrar bandas térmicas M de un VNP02MOD/VJ102MOD → dict {band: BT(K)}.

    Bandas ausentes se omiten. Requiere h5py."""
    import h5py
    out = {}
    with h5py.File(l1b_path, "r") as f:
        obs = f["observation_data"]
        for b in bands:
            bt = _calibrate_band(obs, b)
            if bt is not None:
                out[b] = bt
    return out


def read_mod_geo(geo_path) -> dict:
    """Leer lat/lon (+ sensor_zenith) del VNP03MOD/VJ103MOD. Fill → NaN. Requiere h5py."""
    import h5py
    with h5py.File(geo_path, "r") as f:
        geo = f["geolocation_data"]
        lat = geo["latitude"][:].astype("float64")
        lon = geo["longitude"][:].astype("float64")
        lat[lat < -90] = np.nan
        lon[lon < -180] = np.nan
        if "sensor_zenith" in geo:
            sz = geo["sensor_zenith"][:].astype("float64")
        elif "satellite_zenith" in geo:
            sz = geo["satellite_zenith"][:].astype("float64")
        else:
            sz = np.zeros_like(lat)
        sz[np.isnan(lat)] = np.nan
    return {"lat": lat, "lon": lon, "sensor_zenith": sz}


def roi_mask_bbox(lat, lon, center_lat: float, center_lon: float,
                  half_km: float):
    """Máscara booleana de un bbox cuadrado de ``half_km`` por lado centrado en el
    volcán, sobre los arrays de swath. PURA (clonada de VRP Chile scan_geometry).

    111 km/° de latitud; longitud escalada por cos(lat) del centro."""
    lat = np.asarray(lat, dtype="float64")
    lon = np.asarray(lon, dtype="float64")
    lat_span_km = (lat - center_lat) * 111.0
    lon_span_km = (lon - center_lon) * 111.0 * np.cos(np.radians(center_lat))
    return (np.abs(lat_span_km) <= half_km) & (np.abs(lon_span_km) <= half_km)


def crop_roi(bt: dict, geo: dict, center_lat: float, center_lon: float,
             half_km: float) -> Optional[dict]:
    """Recortar las bandas + geo al bbox del volcán. Devuelve dict con las bandas
    (arrays 1-D de los píxeles dentro del bbox), ``lat``/``lon``, y ``n_px``. None
    si no hay píxeles dentro (el gránulo no cubre el volcán)."""
    mask = roi_mask_bbox(geo["lat"], geo["lon"], center_lat, center_lon, half_km)
    n = int(np.count_nonzero(mask))
    if n == 0:
        return None
    out = {b: np.asarray(arr)[mask] for b, arr in bt.items()}
    out["lat"] = geo["lat"][mask]
    out["lon"] = geo["lon"][mask]
    out["sensor_zenith"] = geo["sensor_zenith"][mask]
    out["n_px"] = n
    return out
