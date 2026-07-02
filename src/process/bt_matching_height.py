# ════════════════════════════════════════════════════════════════════
# FICHA SDA · bt_matching_height.py  ·  SDA: Monitoreo Volcánico GOES-19 · ID: SDA-GOES-01
# Objetivo      : estimar la altura del tope de pluma (cota inferior) como insumo INDICATIVO
# Lógica        : el tope opaco emite como su temperatura → se busca esa temperatura en el perfil vertical GFS
# Modelo/método : reglas determinísticas: BT(11 µm) → interpolación en T(z)
# Datos entrada : BT GOES-19 + perfil GFS T(z) (Open-Meteo) — SIN datos personales
# Variables     : BT(11 µm) del tope, perfil T(z), tropopausa (cota superior del mapeo)
# Limitaciones  : COTA INFERIOR: subestima plumas semitransparentes; ambiguo con inversiones térmicas (mitigado con rama monótona)
# Refs/datos    : estándar BT-matching; validación en docs/paper/REGISTRO_PAPER.md §3
# Ficha completa: docs/FICHA_SDA_GOES.md
# ════════════════════════════════════════════════════════════════════
"""Altura del tope de pluma por **BT-matching** — propia, independiente de SSEC
Y de NOAA-ACHA (Fase 3a del VOLCAT propio).

Idea (la más simple de las alturas "físicas"): el tope opaco de una pluma emite
como cuerpo gris ≈ negro en la ventana de 11 µm, así que su **temperatura de
brillo BT(11 µm) ≈ la temperatura del tope (Teff)**. Buscando esa temperatura en
el **perfil vertical T(z)** del GFS (``src/fetch/gfs_profile.py``) se obtiene la
altitud del tope. Es el método "3a" del plan.

Honestidad — **típicamente** una cota inferior, NO garantizada:
- Para plumas opacas gruesas sobre fondo cálido y T(z) decreciente, subestima
  (BT más cálida que el tope real → altitud más baja) → cota inferior.
- PERO con **inversión térmica** una BT cálida puede mapear más arriba, o si la
  pluma hace **overshooting** sobre la tropopausa el clampeo no garantiza el
  signo. Por eso es INDICATIVO y se compara contra ACHA/VOLCAT, sin afirmar que
  sea siempre menor. La rama monótona del perfil (``_monotone_tropo_branch``)
  acota el daño de las inversiones.

Ventajas sobre ACHA: no depende del producto NOAA L2 (lo calculamos nosotros
desde L1b + perfil GFS) → control total y trazabilidad. Desventaja: no corrige
emisividad (eso sería Wen-Rose, Fase 3b) ni hace OE (Fase 4).
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Union

import numpy as np

# El mapeo BT→altitud (robusto a inversiones) vive junto al perfil GFS; lo
# re-exportamos para que PRODUCCIÓN y TESTS usen exactamente la misma función.
from src.fetch.gfs_profile import altitudes_from_bt  # noqa: F401  (re-export + uso)

logger = logging.getLogger(__name__)

BT11_BAND = 14             # 11.2 µm = C14, la ventana del BT-matching


def _bounds_for(v, r: float) -> dict:
    return {"lat_min": v.lat - r, "lat_max": v.lat + r,
            "lon_min": v.lon - r, "lon_max": v.lon + r}


def bt_matching_top_height(
    dt: datetime,
    volcano: Union[str, object],
    radius_deg: float = 0.75,
    percentile: float = 95,
) -> dict:
    """Altura del tope de pluma por BT-matching para un volcán en un instante.

    Pipeline: ventana geos desde C14 → baja C11/C14/C15 del mismo scan → máscara
    de ceniza (``detect_ash_enhanced``) → perfil GFS en el volcán → mapea la
    BT(11 µm) de los píxeles de ceniza a altitud → tope p95/max + campo.

    Returns dict con ``status`` (ok/no_plume/no_data) y, si ok: ``top_km`` (p95),
    ``top_max_km``, ``mask_px``, ``field_km``, ``lat``/``lon``, ``scan_dt``,
    ``tropopause_km``, ``n_capped`` (píxeles que tocaron la tropopausa → posible
    overshooting/cota), ``source``.
    """
    from src.config import (GOES19_PERSPECTIVE_POINT_HEIGHT as _H,
                            GOES19_SAT_LON as _SLON)
    from src.fetch.gfs_profile import fetch_gfs_profile
    from src.fetch.goes_acha import _geos_index_bbox, _window_latlon
    from src.fetch.goes_s3 import _scan_start, download_band_at, open_band
    from src.process.ash_detection import detect_ash_enhanced
    from src.process.brightness_temp import rad_to_bt

    source = ("BT-matching (BT 11µm del tope de ceniza → perfil GFS T(z)) · "
              "INDICATIVO (típ. cota inferior) · independiente de SSEC y ACHA")

    if isinstance(volcano, str):
        from src.volcanos import get_volcano
        v = get_volcano(volcano)
    else:
        v = volcano
    if v is None:
        return {"status": "no_data", "reason": "volcán no encontrado",
                "volcano": str(volcano), "source": source}
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    bounds = _bounds_for(v, radius_deg)

    # ── Ventana geos desde la grilla de C14 ──────────────────────────────
    p14 = download_band_at(dt, BT11_BAND)
    if p14 is None:
        return {"status": "no_data", "reason": "sin banda C14",
                "volcano": v.name, "bounds": bounds, "source": source}
    try:
        with open_band(p14) as ds14:
            x = ds14["x"].values
            y = ds14["y"].values
            proj = ds14["goes_imager_projection"].attrs
            sat_lon = float(proj.get("longitude_of_projection_origin", _SLON))
            H = float(proj.get("perspective_point_height", _H))
            win = _geos_index_bbox(x, y, bounds, sat_lon=sat_lon, H=H)
            if win is None:
                return {"status": "no_data", "reason": "bbox fuera del disco",
                        "volcano": v.name, "bounds": bounds, "source": source}
            y0, y1, x0, x1 = win
            bt14 = rad_to_bt(ds14.isel(y=slice(y0, y1), x=slice(x0, x1))).load().values
            xw, yw = x[x0:x1], y[y0:y1]
    except Exception as e:
        logger.exception("BT-matching C14: %s", e)
        return {"status": "no_data", "reason": "error leyendo C14",
                "volcano": v.name, "bounds": bounds, "source": source}

    scan_dt = _scan_start(p14.name)
    ref = scan_dt or dt
    lat, lon = _window_latlon(xw, yw, sat_lon=sat_lon, H=H)

    # ── C11/C15 del MISMO scan para la máscara ───────────────────────────
    bts = {14: bt14}
    band_scans = {14: scan_dt}
    for b in (11, 15):
        pb = download_band_at(ref, b)
        if pb is None:
            return {"status": "no_data", "reason": f"sin banda C{b:02d}",
                    "volcano": v.name, "bounds": bounds, "scan_dt": scan_dt,
                    "source": source}
        band_scans[b] = _scan_start(pb.name)
        try:
            with open_band(pb) as dsb:
                bts[b] = rad_to_bt(dsb.isel(y=slice(y0, y1), x=slice(x0, x1))).load().values
        except Exception as e:
            logger.exception("BT-matching C%02d: %s", b, e)
            return {"status": "no_data", "reason": f"error leyendo C{b:02d}",
                    "volcano": v.name, "bounds": bounds, "scan_dt": scan_dt,
                    "source": source}

    # Las 3 bandas deben ser del MISMO scan (igual guard que acha_plume_height);
    # si S3 tenía un hueco y alguna cayó en un scan vecino, la máscara mezclaría
    # tiempos → degradar a no_data en vez de un misregistro silencioso. (review jun 2026)
    scans = {s for s in band_scans.values() if s is not None}
    if len(scans) > 1:
        logger.warning("BT-matching: bandas de scans distintos: %s", band_scans)
        return {"status": "no_data",
                "reason": "bandas C11/C14/C15 de scans distintos (S3 incompleto)",
                "volcano": v.name, "bounds": bounds, "scan_dt": scan_dt,
                "source": source}

    import xarray as xr

    def _da(a):
        return xr.DataArray(a, dims=("y", "x"))

    mask = detect_ash_enhanced(_da(bts[11]), _da(bts[14]), _da(bts[15])).values

    # Contexto SO2 (mismo criterio que acha_plume_height) para que el dashboard
    # explique una pluma de gas sin ceniza. (ver reference_acha_so2_limit)
    try:
        from src.config import SO2_INDICATOR_THRESHOLD as _SO2_THR
    except Exception:
        _SO2_THR = -3.0
    so2 = bts[11] - bts[14]
    so2_finite = np.isfinite(so2)
    so2_px = int(np.sum(so2_finite & (so2 < _SO2_THR)))
    so2_min = float(np.nanmin(so2)) if so2_finite.any() else None

    # ── Perfil GFS y mapeo BT→altitud ────────────────────────────────────
    profile = fetch_gfs_profile(v.lat, v.lon, ref)
    if profile is None:
        return {"status": "no_data", "reason": "sin perfil GFS (Open-Meteo)",
                "volcano": v.name, "bounds": bounds, "scan_dt": scan_dt,
                "so2_px": so2_px, "so2_min": so2_min, "source": source}

    alt_m = altitudes_from_bt(bts[14], profile)
    ash_alt = np.where(mask & np.isfinite(alt_m), alt_m, np.nan)
    field_km = ash_alt / 1000.0
    valid = np.isfinite(ash_alt)
    n = int(valid.sum())

    trop = profile.get("tropopause")
    trop_km = trop["z_m"] / 1000.0 if trop else None
    now = datetime.now(timezone.utc)
    latency_min = (now - scan_dt).total_seconds() / 60.0 if scan_dt else None

    out = {
        "volcano": v.name, "bounds": bounds, "lat": lat, "lon": lon,
        "scan_dt": scan_dt, "latency_min": latency_min, "percentile": percentile,
        "source": source, "tropopause_km": trop_km,
        "profile_time": profile.get("valid_time"),
        "field_km": field_km, "mask_px": n,
        "so2_px": so2_px, "so2_min": so2_min,
    }
    if n == 0:
        out.update({"status": "no_plume", "top_km": None, "top_max_km": None,
                    "n_capped": 0, "all_capped": False})
        return out

    # Píxeles "capped" en la tropopausa: o overshooting real (raro) o cirros mal
    # detectados pegados al tope frío (común en Chile). NO deben fijar el tope →
    # el p95/max se computa SOBRE los NO capped; n_capped se reporta aparte. Si
    # TODOS están capped, se devuelve la tropopausa con all_capped. (review jun 2026)
    capped = (valid & (alt_m >= trop["z_m"] - 1.0)) if trop else np.zeros_like(valid)
    n_capped = int(np.sum(capped))
    clean = valid & ~capped
    if int(clean.sum()) > 0:
        vals = alt_m[clean]
        out.update({
            "status": "ok",
            "top_km": float(np.percentile(vals, percentile)) / 1000.0,
            "top_max_km": float(vals.max()) / 1000.0,
            "n_capped": n_capped, "all_capped": False,
        })
    else:
        out.update({
            "status": "ok",
            "top_km": trop_km, "top_max_km": trop_km,
            "n_capped": n_capped, "all_capped": True,
        })
    return out
