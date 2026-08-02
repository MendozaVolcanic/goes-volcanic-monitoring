# ════════════════════════════════════════════════════════════════════
# FICHA SDA · wind_shear_height.py  ·  SDA: Monitoreo Volcánico GOES-19 · ID: SDA-GOES-01
# Objetivo      : estimar altura de pluma por el viento que la mueve — árbitro independiente del método térmico (NO en producción aún)
# Lógica        : la pluma se mueve al viento de SU altura: el desplazamiento entre 2 scans revela a qué altura está
# Modelo/método : reglas determinísticas: advección del centroide vs perfil de viento GFS
# Datos entrada : máscaras de ceniza GOES-19 (2 scans) + perfil de viento GFS (Open-Meteo) — SIN datos personales
# Variables     : advección observada (u,v), cizalla mínima 8 m/s, banda de ambigüedad ±8 m/s (RMSE viento GFS), guards de advección implausible/nula y viento viejo
# Limitaciones  : requiere cizalla Y banda estrecha (≤8 km); pluma adjunta → adv_ambiguous, banda ancha → band_unconstrained; validado en Láscar: pluma chica no restringe
# Refs/datos    : Pavolonis et al. 2020 (idea); guards del audit jul-2026
# Ficha completa: docs/FICHA_SDA_GOES.md
# ════════════════════════════════════════════════════════════════════
"""Altura del tope de pluma por **cizalla de viento** — árbitro INDEPENDIENTE del
método térmico (Fase 3c del VOLCAT propio, idea de Pavolonis et al. 2020).

Por qué (geología → pipeline): una pluma volcánica se advecta horizontalmente al
viento que sopla **a su altura**. Si medimos el desplazamiento de la pluma entre
dos scans consecutivos de GOES (Δt ~10 min) obtenemos su **velocidad de advección
observada**; buscando en el **perfil vertical de viento GFS** la altitud cuyo
viento (u,v) mejor coincide con esa advección, obtenemos una estimación de altura
**totalmente independiente** de la temperatura de brillo (Wen-Rose/BT-matching).

Es un cross-check ortogonal: donde el método térmico y el de viento coinciden, la
confianza sube. Limitación clave (Pavolonis 2020): **requiere cizalla vertical**.
Si el viento es casi uniforme con la altura, cualquier altitud coincide y el
método NO discrimina — se reporta ``discriminates=False`` y no se da altura.

INDICATIVO. VOLCAT/SSEC sigue siendo el primario. Este módulo aún NO se cablea al
dashboard: necesita validación en un evento real de 2 scans con pluma en
movimiento (igual que Wen-Rose se validó en Láscar) antes de producción.
"""

from __future__ import annotations

import logging
import math
from datetime import datetime, timedelta, timezone
from typing import Optional, Union

import numpy as np

logger = logging.getLogger(__name__)

BT85_BAND = 11
BT11_BAND = 14
BT12_BAND = 15
M_PER_DEG_LAT = 111320.0    # metros por grado de latitud (WGS84 aprox.)
MIN_SHEAR_MS = 8.0          # cizalla mínima (spread de viento) para discriminar
# Tolerancia de mismatch para la banda de ambigüedad. Antes 3 m/s (optimista): la
# validación con radiosondas (jul-2026, scripts/validate_gfs_vs_radiosonde.py)
# midió que el viento GFS tiene RMSE VECTORIAL 8–17 m/s en 1–15 km. Con una banda
# de ±3 m/s alrededor del mejor nivel, cualquier nivel cuyo viento diste <3 m/s del
# observado se marcaba "ambiguo", PERO el propio viento del modelo ya erra ≥8 m/s →
# la banda subestimaba la incertidumbre real (mismo sesgo que el β de F2). La atamos
# al piso de ruido del viento (= MIN_SHEAR_MS): dos niveles cuyo viento difiere menos
# que ese ruido NO son distinguibles. Es el EXTREMO INFERIOR del RMSE medido (hasta
# 17 m/s), así que la banda reportada es una COTA INFERIOR de la ambigüedad real.
AMB_TOL_MS = 8.0
# Advección casi nula: una pluma en emisión CONTINUA queda anclada al cráter (se
# realimenta desde abajo) → su centroide no se mueve aunque haya viento fuerte
# arriba. Ese caso es INDISTINGUIBLE por advección de una pluma real en un nivel
# calmo, y el árbitro le asignaría el nivel de viento nulo (altura baja FALSA; F3
# del audit jul-2026). Si adv < esto y ADEMÁS hay cizalla fuerte, se rechaza.
MIN_ADV_MS = 3.0
# Ancho máximo de la banda de ambigüedad para que la altura sea USABLE. Revelado
# al validar en Láscar 27-jun 2026 con el viento CORRECTO (GFS de archivo): en 5
# scans seguidos la banda cubría casi toda la columna (0.2–23.9 km) y el valor
# puntual saltaba caótico (0.9→4.4→3.2→23.9→7.5 km). Con cizalla presente el test
# `discriminates` (cizalla ≥ 8) daba True, pero la advección observada de una pluma
# chica/incoherente es consistente con casi cualquier altitud → NO restringe nada.
# `discriminates` es necesario pero NO suficiente: el ancho de banda es la medida
# real. Si la banda supera esto, se reporta `band_unconstrained` (sin altura), no
# un `ok` engañoso. (mismo espíritu de honestidad que los guards F1/F2/adjunta.)
MAX_BAND_KM = 8.0
# Desajuste máximo del MEJOR nivel para aceptar el matching. `argmin` siempre devuelve
# un nivel: sin este umbral, una advección que ningún viento de la columna explica
# (p.ej. 35 m/s observados con máximo de 20 m/s en el perfil) igual salía como `ok`.
# Se ata al mismo piso de ruido del viento GFS que la banda de ambigüedad (AMB_TOL_MS):
# si el residuo del mejor nivel supera el error propio del modelo, no hay detección.
MAX_MISMATCH_MS = AMB_TOL_MS
# Guards revelados al validar en Láscar 27-jun (2026): plumas chicas cambian sus
# píxeles detectados entre scans → el centroide "salta" y da advección espuria; y
# fuera de la ventana de forecast el perfil de viento queda viejo (día equivocado).
MAX_ADV_MS = 60.0          # advección > esto ⇒ tracking de centroide poco fiable
MAX_WIND_AGE_H = 3.0       # perfil de viento a > esto del scan ⇒ no usar (viejo)


# ── Núcleo puro (sin red) ───────────────────────────────────────────────────

def plume_centroid(mask, lat, lon) -> Optional[tuple]:
    """Centroide (lat, lon) de los píxeles de ceniza. None si la máscara vacía.
    Función PURA."""
    m = np.asarray(mask, dtype=bool)
    if not m.any():
        return None
    return (float(np.asarray(lat)[m].mean()), float(np.asarray(lon)[m].mean()))


def advection_uv(lat0, lon0, lat1, lon1, dt_s: float) -> tuple:
    """Velocidad de advección (u este, v norte) en m/s desde el desplazamiento del
    centroide entre t0 y t1 (dt_s segundos). Función PURA.

    dx = Δlon · (m/°) · cos(lat) ; dy = Δlat · (m/°). u=dx/dt, v=dy/dt.
    """
    if dt_s == 0:
        return (0.0, 0.0)
    latm = math.radians((lat0 + lat1) / 2.0)
    dx = (lon1 - lon0) * M_PER_DEG_LAT * math.cos(latm)   # este (m)
    dy = (lat1 - lat0) * M_PER_DEG_LAT                     # norte (m)
    return (dx / dt_s, dy / dt_s)


def wind_implied_height(u_obs, v_obs, levels, min_shear_ms: float = MIN_SHEAR_MS,
                        amb_tol_ms: float = AMB_TOL_MS) -> Optional[dict]:
    """Altitud cuyo viento GFS mejor coincide con la advección observada.

    ``levels`` = lista de ``{z_m, u_ms, v_ms}`` (de ``fetch_gfs_wind_profile``).
    Devuelve ``{z_m, mismatch_ms, shear_ms, discriminates, z_lo_m, z_hi_m}`` o
    None si <2 niveles. ``discriminates=False`` si la cizalla (spread del viento
    respecto al mejor nivel) es menor que ``min_shear_ms`` → sin poder de
    discriminación (viento casi uniforme). La banda [z_lo, z_hi] son las altitudes
    cuyo mismatch queda dentro de ``amb_tol_ms`` del mínimo (ambigüedad honesta).
    Función PURA.
    """
    levels = levels or []
    if len(levels) < 2:
        return None
    z = np.array([l["z_m"] for l in levels], dtype="float64")
    u = np.array([l["u_ms"] for l in levels], dtype="float64")
    v = np.array([l["v_ms"] for l in levels], dtype="float64")
    mis = np.hypot(u - u_obs, v - v_obs)
    k = int(np.argmin(mis))
    best_z, best_mis = float(z[k]), float(mis[k])
    shear = float(np.hypot(u - u[k], v - v[k]).max())
    near = mis <= best_mis + amb_tol_ms
    return {
        "z_m": best_z, "mismatch_ms": best_mis, "shear_ms": shear,
        "discriminates": bool(shear >= min_shear_ms),
        "z_lo_m": float(z[near].min()), "z_hi_m": float(z[near].max()),
    }


# ── Orquestación (con red) — NO cablear al dashboard sin validación real ─────

def _ash_mask_at(dt: datetime, v, radius_deg: float):
    """(mask, lat, lon, scan_dt) de ceniza para un volcán en un instante. None si
    no hay datos. Reusa los helpers de bajo nivel (mismo patrón que wen_rose)."""
    from src.config import (GOES19_PERSPECTIVE_POINT_HEIGHT as _H,
                            GOES19_SAT_LON as _SLON)
    from src.fetch.goes_acha import _geos_index_bbox, _window_latlon
    from src.fetch.goes_s3 import _scan_start, download_band_at, open_band
    from src.process.ash_detection import detect_ash_enhanced
    from src.process.brightness_temp import rad_to_bt
    import xarray as xr

    bounds = {"lat_min": v.lat - radius_deg, "lat_max": v.lat + radius_deg,
              "lon_min": v.lon - radius_deg, "lon_max": v.lon + radius_deg}
    p14 = download_band_at(dt, BT11_BAND)
    if p14 is None:
        return None
    try:
        with open_band(p14) as ds14:
            x, y = ds14["x"].values, ds14["y"].values
            proj = ds14["goes_imager_projection"].attrs
            sat_lon = float(proj.get("longitude_of_projection_origin", _SLON))
            H = float(proj.get("perspective_point_height", _H))
            win = _geos_index_bbox(x, y, bounds, sat_lon=sat_lon, H=H)
            if win is None:
                return None
            y0, y1, x0, x1 = win
            bt14 = rad_to_bt(ds14.isel(y=slice(y0, y1), x=slice(x0, x1))).load().values
            xw, yw = x[x0:x1], y[y0:y1]
    except Exception as e:
        logger.exception("wind-shear C14: %s", e)
        return None
    scan_dt = _scan_start(p14.name)
    ref = scan_dt or dt
    lat, lon = _window_latlon(xw, yw, sat_lon=sat_lon, H=H)
    bts = {14: bt14}
    band_scans = {14: scan_dt}
    for b in (BT85_BAND, BT12_BAND):
        pb = download_band_at(ref, b)
        if pb is None:
            return None
        band_scans[b] = _scan_start(pb.name)
        try:
            with open_band(pb) as dsb:
                bts[b] = rad_to_bt(dsb.isel(y=slice(y0, y1),
                                            x=slice(x0, x1))).load().values
        except Exception:
            return None
    # Guard (fix C1, audit jul-2026): las 3 bandas deben ser del MISMO scan —
    # con S3 a medio subir, mezclar scans da una máscara de ceniza espuria →
    # centroide falso → advección inventada que puede pasar MAX_ADV_MS. Mismo
    # guard que wen_rose_height.
    scans = {s for s in band_scans.values() if s is not None}
    if len(scans) > 1:
        logger.warning("wind-shear: bandas de scans distintos: %s", band_scans)
        return None

    def _da(a):
        return xr.DataArray(a, dims=("y", "x"))

    mask = detect_ash_enhanced(_da(bts[11]), _da(bts[14]), _da(bts[15])).values
    return mask, lat, lon, scan_dt


def wind_shear_top_height(
    dt: datetime, volcano: Union[str, object], radius_deg: float = 0.75,
    prev_gap_min: int = 10, wind_profile_fn=None,
) -> dict:
    """Altura del tope por cizalla de viento: desplazamiento del centroide de
    ceniza entre el scan en ``dt`` y otro ``prev_gap_min`` minutos antes, cruzado
    con el perfil de viento GFS. INDICATIVO, árbitro independiente del térmico.

    ``wind_profile_fn``: proveedor del perfil de viento ``fn(lat, lon, dt) → dict``
    (mismo contrato que ``fetch_gfs_wind_profile``). Default = Open-Meteo (NRT).
    Para VALIDACIÓN HISTÓRICA, inyectar ``fetch_gfs_wind_profile_archive`` (GFS de
    archivo): Open-Meteo da null/viento viejo en fechas pasadas — ese fue el modo
    de fallo real en Láscar 27-jun (viento a 41 h del scan).

    Returns dict con ``status`` (ok/no_shear/no_plume/adv_ambiguous/
    band_unconstrained/adv_inconsistent/no_data) y, si ok: ``top_km`` (altura implícita),
    ``band_lo_km``/``band_hi_km``, ``adv_speed_ms``, ``mismatch_ms``, ``shear_ms``,
    ``scan_dt``, ``source``. ``band_unconstrained`` reporta la banda cruda sin
    ``top_km`` (la advección no restringe la altura pese a haber cizalla).
    """
    if wind_profile_fn is None:
        from src.fetch.gfs_profile import fetch_gfs_wind_profile
        wind_profile_fn = fetch_gfs_wind_profile
    source = ("Cizalla de viento (advección de la pluma entre 2 scans → perfil de "
              "viento GFS) · INDICATIVO · independiente del método térmico")
    if isinstance(volcano, str):
        from src.volcanos import get_volcano
        v = get_volcano(volcano)
    else:
        v = volcano
    if v is None:
        return {"status": "no_data", "reason": "volcán no encontrado", "source": source}
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    cur = _ash_mask_at(dt, v, radius_deg)
    prev = _ash_mask_at(dt - timedelta(minutes=prev_gap_min), v, radius_deg)
    if cur is None or prev is None:
        return {"status": "no_data", "reason": "sin 2 scans utilizables",
                "volcano": v.name, "source": source}
    c_now = plume_centroid(cur[0], cur[1], cur[2])
    c_prev = plume_centroid(prev[0], prev[1], prev[2])
    if c_now is None or c_prev is None:
        return {"status": "no_plume", "reason": "sin ceniza en algún scan",
                "volcano": v.name, "scan_dt": cur[3], "source": source}

    dt_s = abs((cur[3] - prev[3]).total_seconds()) if (cur[3] and prev[3]) \
        else prev_gap_min * 60.0
    if dt_s <= 0:
        return {"status": "no_data", "reason": "Δt nulo entre scans",
                "volcano": v.name, "source": source}
    u_obs, v_obs = advection_uv(c_prev[0], c_prev[1], c_now[0], c_now[1], dt_s)
    adv_speed = math.hypot(u_obs, v_obs)
    # Guard: advección implausible ⇒ el centroide saltó por ruido de detección
    # (típico en plumas chicas que cambian de píxeles entre scans), no es viento real.
    if adv_speed > MAX_ADV_MS:
        return {"status": "no_data", "volcano": v.name, "scan_dt": cur[3],
                "adv_speed_ms": adv_speed, "source": source,
                "reason": f"advección implausible ({adv_speed:.0f} m/s): tracking de "
                "centroide poco fiable (pluma chica/cambiante)"}

    wp = wind_profile_fn(v.lat, v.lon, cur[3] or dt)
    if wp is None:
        return {"status": "no_data", "reason": "sin perfil de viento GFS",
                "volcano": v.name, "scan_dt": cur[3], "source": source}
    # Guard: perfil de viento viejo (evento fuera de la ventana de forecast de
    # Open-Meteo) ⇒ sería el viento del día equivocado. Rechazar.
    ref_dt = cur[3] or dt
    try:
        wt = datetime.strptime(wp["valid_time"], "%Y-%m-%dT%H:%M").replace(
            tzinfo=timezone.utc)
        age_h = abs((wt - ref_dt).total_seconds()) / 3600.0
    except Exception:
        # Fix C2 (audit jul-2026): un valid_time no parseable NO se trata como
        # "fresco" — si Open-Meteo cambia el formato, asumir edad 0 anularía el
        # guard silenciosamente y se usaría viento del día equivocado. Rechazar.
        return {"status": "no_data", "volcano": v.name, "scan_dt": cur[3],
                "adv_speed_ms": adv_speed, "source": source,
                "reason": f"valid_time del perfil de viento no parseable "
                f"({wp.get('valid_time')!r}): no se puede verificar frescura"}
    if age_h > MAX_WIND_AGE_H:
        return {"status": "no_data", "volcano": v.name, "scan_dt": cur[3],
                "adv_speed_ms": adv_speed, "source": source,
                "reason": f"perfil de viento a {age_h:.0f} h del scan (fuera de la "
                "ventana de forecast): usaría el viento del día equivocado"}
    wh = wind_implied_height(u_obs, v_obs, wp["levels"])
    if wh is None:
        return {"status": "no_data", "reason": "perfil de viento insuficiente",
                "volcano": v.name, "scan_dt": cur[3], "source": source}
    adv_speed = math.hypot(u_obs, v_obs)
    out = {
        "volcano": v.name, "scan_dt": cur[3], "adv_speed_ms": adv_speed,
        "mismatch_ms": wh["mismatch_ms"], "shear_ms": wh["shear_ms"],
        "source": source,
    }
    # Guard de pluma ADJUNTA (F3): advección casi nula CON cizalla fuerte arriba ⇒
    # el centroide está anclado (emisión continua, realimentada desde el cráter),
    # no flotando en aire calmo. El árbitro le daría el nivel de viento nulo →
    # altura baja FALSA. Como la advección sola no distingue "anclada" de "en un
    # nivel calmo real", declinamos dar altura (honestidad, análogo a la
    # degeneración CO₂ de F1). Si NO hay cizalla, cae abajo en no_shear.
    if adv_speed < MIN_ADV_MS and wh["shear_ms"] >= MIN_SHEAR_MS:
        out.update({"status": "adv_ambiguous", "top_km": None,
                    "reason": f"advección casi nula ({adv_speed:.1f} m/s) con "
                    f"cizalla fuerte ({wh['shear_ms']:.0f} m/s): pluma posiblemente "
                    "adjunta al cráter (emisión continua) — indistinguible de un "
                    "nivel calmo, no se asigna altura"})
        return out
    if not wh["discriminates"]:
        out.update({"status": "no_shear", "top_km": None,
                    "reason": f"cizalla insuficiente ({wh['shear_ms']:.0f} m/s): "
                    "el viento no discrimina altura"})
        return out
    # Guard de banda ancha (F-Láscar): hay cizalla, pero la advección observada es
    # consistente con casi toda la columna → la altura NO está restringida. No dar
    # un valor puntual engañoso; reportar la banda cruda y declinar.
    band_lo_km, band_hi_km = wh["z_lo_m"] / 1000.0, wh["z_hi_m"] / 1000.0
    if (band_hi_km - band_lo_km) > MAX_BAND_KM:
        out.update({"status": "band_unconstrained", "top_km": None,
                    "band_lo_km": band_lo_km, "band_hi_km": band_hi_km,
                    "reason": f"banda de ambigüedad demasiado ancha "
                    f"({band_hi_km - band_lo_km:.0f} km): la advección observada "
                    "es consistente con casi toda la columna — altura no restringida "
                    "(típico de pluma chica/incoherente)"})
        return out
    # Guard de matching inconsistente (audit ago-2026, confirmado adversarialmente):
    # `argmin` SIEMPRE devuelve un nivel, aunque el mínimo del residuo esté muy por
    # encima del piso de ruido. Escenario real: advección observada de 35 m/s cuando el
    # viento máximo de TODA la columna es 20 m/s (centroide que salta por ruido de
    # detección, aún bajo MAX_ADV_MS) → el "mejor" nivel tiene mismatch 15 m/s y hasta
    # ahora salía como status ok con altura puntual. Físicamente ningún nivel explica
    # ese movimiento: el mínimo de una función que no baja del ruido NO es una
    # detección. Reusamos AMB_TOL_MS (el piso de ruido del viento GFS, 8 m/s) como
    # umbral: si ni el mejor nivel entra en esa tolerancia, declinamos.
    if wh["mismatch_ms"] > MAX_MISMATCH_MS:
        out.update({"status": "adv_inconsistent", "top_km": None,
                    "band_lo_km": band_lo_km, "band_hi_km": band_hi_km,
                    "reason": f"la advección observada ({adv_speed:.0f} m/s) no es "
                    f"consistente con ningún nivel del perfil (mejor desajuste "
                    f"{wh['mismatch_ms']:.0f} m/s > {MAX_MISMATCH_MS:.0f}): tracking "
                    "espurio o proceso no advectivo — no se asigna altura"})
        return out
    out.update({
        "status": "ok", "top_km": wh["z_m"] / 1000.0,
        "band_lo_km": band_lo_km, "band_hi_km": band_hi_km,
    })
    return out
