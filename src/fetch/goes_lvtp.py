"""Cliente para el producto NOAA ABI-L2-LVTPF (Legacy Vertical Temperature
Profile, Full Disk) — el perfil vertical de temperatura del **PROPIO GOES-19**.

Por qué importa (geología → pipeline):
El retrieval de altura de pluma no mide altura: mide una temperatura efectiva del
tope (Teff) y la convierte a kilómetros buscándola dentro de un perfil T(z). Ese
perfil hoy lo aporta GFS (Open-Meteo, ``src/fetch/gfs_profile.py``), que validamos
contra radiosondas (RMSE 0.3–1.1 K en 5–12 km ≈ ≤60 m). LVTPF es **la misma
cantidad física medida por el sondeador infrarrojo del propio ABI**, cada 10 min
en el mismo bucket S3 que ya usamos, con 101 niveles de presión (vs 19 de
Open-Meteo). Sirve como **perfil alternativo / cross-check independiente** del
GFS en el mapeo Teff→altura — si ambos coinciden, la altura es más defendible; si
divergen, es una señal de incertidumbre honesta para un producto INDICATIVO.

Contrato del dato (verificado contra el NetCDF vivo, jul-2026):
- ``LVT(y, x, pressure)`` en **K**, grilla 1086×1086 (10 km), 101 niveles de
  presión (``pressure`` en hPa, de 1100 a 0.005). Fill 65535 → NaN por xarray.
- ``DQF_Overall`` (y,x): 0 = ``good_quality``; **4 = ``insufficient_clear_pixels
  _in_field_of_regard``** = píxel bajo nube/pluma. LVTPF es un retrieval de
  **cielo claro**: bajo la pluma no hay perfil. Por eso NO leemos el píxel del
  cráter, sino que tomamos la **mediana del entorno de cielo claro** (análogo al
  Ts de cielo claro del Wen-Rose). Los demás flags (1,2,3,5..10) son inválidos.
- ``DQF_Retrieval`` (y,x): 0 = ``good_retrieval``; el resto (no convergente,
  residuo alto, valor irreal, etc.) se descarta.
- Proyección: ABI fixed grid (geos), ``goes_imager_projection`` idéntica a la de
  ACHA2KMF salvo la resolución (1086 vs 5424 px). Por eso reutilizamos los
  helpers geos de ``goes_acha`` (filtran por VALOR, no por índice → funcionan con
  cualquier resolución).

Limitación clave frente a GFS: LVTPF entrega T(p) pero **NO** altura geopotencial.
La derivamos por **integración hipsométrica** del propio perfil (``_hypsometric_
heights``), anclada al absoluto AMSL con la atmósfera estándar en el nivel base
(el error de anclaje es un desplazamiento constante ~0.1 km, menor que el sesgo
IR sistemático ya documentado de −0.4..−0.8 km). Salida: dict con la MISMA forma
que ``fetch_gfs_profile`` → drop-in para ``altitudes_from_bt``/``height_from_temp``.

Cadencia: 10 min. Latencia: ~13 min (timestamp ``c`` = creación del archivo).
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

import numpy as np

# Helpers geos compartidos (idéntica proyección ABI fixed grid, distinta
# resolución). Reutilizarlos evita duplicar la matemática del recorte + georef.
from src.fetch.goes_acha import (
    _geos_index_bbox,
    _parse_scan_time,
)
# Tropopausa = punto frío 6–20 km, MISMA definición que GFS → cross-check justo.
from src.fetch.gfs_profile import _tropopause

logger = logging.getLogger(__name__)

S3_BUCKET = "noaa-goes19"
S3_PRODUCT = "ABI-L2-LVTPF"

# Constantes físicas de la ecuación hipsométrica (aire seco). Fuente: CODATA /
# atmósfera estándar. R_d = constante del gas para aire seco; g0 = gravedad
# estándar. No hay copia en src/config → se definen acá con procedencia.
_RD = 287.05        # J kg⁻¹ K⁻¹ (aire seco)
_G0 = 9.80665       # m s⁻² (gravedad estándar, definición del geopotencial)

# Atmósfera estándar internacional (ISA/US Std 1976), rama troposférica:
_ISA_T0 = 288.15    # K  (temperatura al nivel del mar)
_ISA_L = 0.0065     # K m⁻¹ (tasa de lapso troposférica)
_ISA_P0 = 1013.25   # hPa (presión al nivel del mar)

# Rango de presión USABLE del perfil: por debajo de MSL (p>1013.25) los niveles
# son extrapolación bajo tierra; por encima de ~10 hPa no aportan a la altura de
# pluma (muy por sobre la tropopausa). Rango físico de T para descartar basura.
_P_MAX_HPA = 1013.25
_P_MIN_HPA = 10.0
_T_MIN_K, _T_MAX_K = 150.0, 330.0

# Píxeles de cielo claro mínimos para un perfil creíble del entorno.
_MIN_CLEAR_PX = 3
# Padding por defecto del bbox alrededor del volcán (grados). A 10 km/px un
# ±0.5° da ~11×11 px de entorno para estimar el perfil de cielo claro.
_PAD_DEG_DEFAULT = 0.5


def _std_atm_height(p_hPa: float) -> float:
    """Altura geopotencial (m) de la atmósfera estándar ISA en la troposfera.

    ``z = (T0/L)·(1 − (p/p0)^(R_d·L/g0))``. Se usa SOLO como ancla absoluta del
    integrador hipsométrico en el nivel base (near-surface, siempre troposférico),
    no como perfil. Pura.
    """
    p = float(p_hPa)
    exponent = _RD * _ISA_L / _G0
    return (_ISA_T0 / _ISA_L) * (1.0 - (p / _ISA_P0) ** exponent)


def _hypsometric_heights(p_hPa: np.ndarray, T_K: np.ndarray) -> np.ndarray:
    """Convertir un perfil T(p) a altura geopotencial z(p) por integración
    hipsométrica. PURA.

    LVTPF no trae altura geopotencial, así que la construimos: entre dos niveles
    ``Δz = (R_d/g0)·T_mean·ln(p_low/p_up)`` (regla del trapecio sobre ln p).
    Se ancla el absoluto AMSL con la atmósfera estándar en el nivel base — el
    anclaje solo desplaza el perfil entero (offset constante), no deforma la
    estructura vertical que gobierna el mapeo Teff→altura.

    Args:
        p_hPa: presiones en hPa, **descendentes** (superficie → arriba).
        T_K:   temperaturas en K, alineadas con ``p_hPa``.

    Returns:
        z_m: altura geopotencial (m), ascendente, misma longitud.
    """
    p = np.asarray(p_hPa, dtype="float64")
    T = np.asarray(T_K, dtype="float64")
    z = np.empty_like(p)
    if p.size == 0:
        return z
    z[0] = _std_atm_height(p[0])
    for i in range(1, p.size):
        t_mean = 0.5 * (T[i - 1] + T[i])
        z[i] = z[i - 1] + (_RD / _G0) * t_mean * np.log(p[i - 1] / p[i])
    return z


def _clear_sky_profile(
    lvt: np.ndarray,
    dqf_overall: np.ndarray,
    dqf_retrieval: np.ndarray,
    pressure_hPa: np.ndarray,
    min_clear: int = _MIN_CLEAR_PX,
) -> Optional[tuple[np.ndarray, np.ndarray, int]]:
    """Mediana del perfil T(p) sobre los píxeles de **cielo claro** de la ventana.

    Contrato científico del fetcher (PURO, testeable sin red):
    - Solo píxeles con ``DQF_Overall==0`` **y** ``DQF_Retrieval==0`` (clear-sky +
      retrieval convergente). Bajo la pluma ``DQF_Overall==4`` → se ignoran, que
      es exactamente la razón de estimar el perfil del ENTORNO, no del cráter.
    - Mediana por nivel ignorando NaN (robusta a huecos de píxel).
    - Descarta niveles bajo MSL (p>1013.25), sobre ~10 hPa, y con mediana de T
      fuera del rango físico (150–330 K).

    Returns:
        ``(p_out, T_out, n_clear)`` con p descendente, o ``None`` si no hay
        suficientes píxeles claros (<3) o ningún nivel válido.
    """
    lvt = np.asarray(lvt, dtype="float64")
    p = np.asarray(pressure_hPa, dtype="float64")
    clear = (np.asarray(dqf_overall) == 0) & (np.asarray(dqf_retrieval) == 0)
    n_clear = int(clear.sum())
    if n_clear < min_clear:
        return None

    # (n_clear, nlev): perfiles de los píxeles claros. Mediana ignorando NaN.
    profiles = lvt[clear]                       # boolean-index sobre (y,x,lev)
    with np.errstate(invalid="ignore"):
        med = np.nanmedian(profiles, axis=0)    # (nlev,)

    # Filtro de niveles: presión usable + T física + finita.
    keep = (
        np.isfinite(med)
        & (p <= _P_MAX_HPA) & (p >= _P_MIN_HPA)
        & (med >= _T_MIN_K) & (med <= _T_MAX_K)
    )
    if keep.sum() < 2:
        return None
    p_out = p[keep]
    T_out = med[keep]
    # Ordenar por presión descendente (superficie → arriba) para el integrador.
    order = np.argsort(-p_out)
    return p_out[order], T_out[order], n_clear


def _build_profile(
    p_hPa: np.ndarray,
    T_K: np.ndarray,
    lat: float,
    lon: float,
    valid_time: str,
    n_clear_px: int,
    scan_dt: Optional[datetime],
    source_key: str,
) -> Optional[dict]:
    """Ensamblar el dict de perfil con la MISMA forma que ``fetch_gfs_profile``
    (drop-in para ``altitudes_from_bt``/``height_from_temp``). PURA.

    Deriva z(p) por integración hipsométrica y ordena los niveles por altura.
    ``skin_temp_K`` es None: LVTPF no aporta skin-T radiativa (ese fallback sigue
    viniendo de GFS en el Wen-Rose). Tropopausa = punto frío (misma def que GFS).
    """
    p = np.asarray(p_hPa, dtype="float64")
    T = np.asarray(T_K, dtype="float64")
    if p.size < 2:
        return None
    z = _hypsometric_heights(p, T)
    levels = [
        {"p_hPa": float(pi), "z_m": float(zi), "T_K": float(ti)}
        for pi, zi, ti in zip(p, z, T)
    ]
    levels.sort(key=lambda d: d["z_m"])
    return {
        "levels": levels,
        "tropopause": _tropopause(levels),
        "skin_temp_K": None,
        "lat": lat,
        "lon": lon,
        "valid_time": valid_time,
        "n_clear_px": n_clear_px,
        "scan_dt": scan_dt,
        "source": "LVTPF (GOES-19 ABI legacy vertical temperature profile)",
        "source_key": source_key,
    }


def fetch_lvtp_profile(
    lat: float,
    lon: float,
    dt: Optional[datetime] = None,
    pad_deg: float = _PAD_DEG_DEFAULT,
) -> Optional[dict]:
    """Perfil T(z) del propio GOES-19 (LVTPF) en el entorno de cielo claro de
    ``(lat, lon)``, a la hora más cercana a ``dt``.

    Baja el gránulo LVTPF más cercano, recorta una ventana ±``pad_deg`` alrededor
    del volcán, arma el perfil de cielo claro (mediana del entorno) y deriva la
    altura geopotencial por integración hipsométrica. Salida drop-in del mapeo
    Teff→altura, para cruzar contra GFS.

    Args:
        lat, lon: punto (grados decimales).
        dt:       instante UTC objetivo (default: ahora).
        pad_deg:  semiancho del bbox de entorno (grados).

    Returns:
        dict como ``fetch_gfs_profile`` + ``n_clear_px``/``scan_dt``/``source_key``,
        o ``None`` si no hay gránulo, el bbox cae fuera del disco, o no hay
        suficientes píxeles de cielo claro en el entorno.
    """
    try:
        import s3fs
        import xarray as xr
    except ImportError as e:
        logger.error("s3fs/xarray no disponible: %s", e)
        return None

    if dt is None:
        dt = datetime.now(timezone.utc)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    bounds = {"lat_min": lat - pad_deg, "lat_max": lat + pad_deg,
              "lon_min": lon - pad_deg, "lon_max": lon + pad_deg}

    s3 = s3fs.S3FileSystem(anon=True)
    keys = _list_lvtp_files(s3, dt) or _list_lvtp_files(s3, dt - timedelta(hours=1))
    if not keys:
        logger.warning("LVTPF: sin gránulos en %s ni hora previa", dt.isoformat())
        return None

    def _delta(k: str) -> float:
        ts = _parse_scan_time(k)
        return float("inf") if ts is None else abs((ts - dt).total_seconds())

    chosen = min(keys, key=_delta)
    scan_dt = _parse_scan_time(chosen)
    logger.info("LVTPF: dt=%s, gránulo: %s", dt.isoformat(), chosen.split("/")[-1])

    try:
        with s3.open(chosen, "rb") as f:
            ds = xr.open_dataset(f, engine="h5netcdf")
            proj = ds["goes_imager_projection"].attrs
            sat_lon = float(proj.get("longitude_of_projection_origin", -75.0))
            H = float(proj.get("perspective_point_height", 35786023.0))
            x = ds["x"].values
            y = ds["y"].values
            win = _geos_index_bbox(x, y, bounds, sat_lon=sat_lon, H=H)
            if win is None:
                logger.warning("LVTPF: bbox %s fuera del disco", bounds)
                return None
            y0, y1, x0, x1 = win
            # Slice LAZY antes de .values → solo lee la ventana (no el disco ni
            # los 101 niveles del full-disk entero).
            lvt = ds["LVT"].isel(
                y=slice(y0, y1), x=slice(x0, x1)).values.astype("float64")
            dqf_o = ds["DQF_Overall"].isel(y=slice(y0, y1), x=slice(x0, x1)).values
            dqf_r = ds["DQF_Retrieval"].isel(y=slice(y0, y1), x=slice(x0, x1)).values
            pressure = ds["pressure"].values.astype("float64")
    except Exception as e:
        logger.exception("Error leyendo LVTPF %s: %s", chosen, e)
        return None

    prof = _clear_sky_profile(lvt, dqf_o, dqf_r, pressure)
    if prof is None:
        logger.warning("LVTPF: sin píxeles de cielo claro suficientes en %s", bounds)
        return None
    p_out, T_out, n_clear = prof

    valid_time = scan_dt.strftime("%Y-%m-%dT%H:%M") if scan_dt else dt.strftime(
        "%Y-%m-%dT%H:%M")
    return _build_profile(p_out, T_out, lat=lat, lon=lon, valid_time=valid_time,
                          n_clear_px=n_clear, scan_dt=scan_dt, source_key=chosen)


def _list_lvtp_files(s3, dt: datetime) -> list[str]:
    """Listar gránulos LVTPF disponibles para una hora UTC (prefijo del producto
    LVTPF; el helper de ACHA apunta a su propio producto)."""
    prefix = (
        f"{S3_BUCKET}/{S3_PRODUCT}/"
        f"{dt.year}/{dt.timetuple().tm_yday:03d}/{dt.hour:02d}/"
    )
    try:
        return sorted(s3.ls(prefix))
    except FileNotFoundError:
        return []
    except Exception as e:
        logger.warning("listing %s: %s", prefix, e)
        return []


def fetch_latest_lvtp_profile(
    lat: float, lon: float, pad_deg: float = _PAD_DEG_DEFAULT
) -> Optional[dict]:
    """Atajo NRT: el perfil LVTPF del gránulo más reciente sobre ``(lat, lon)``."""
    return fetch_lvtp_profile(lat, lon, datetime.now(timezone.utc), pad_deg=pad_deg)
