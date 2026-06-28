"""Altura del tope de pluma por **Wen & Rose 1994** — corrección de emisividad de
2 canales (11/12 µm) sobre el BT-matching (Fase 3b del VOLCAT propio).

Por qué (geología → pipeline): el BT-matching (Fase 3a) supone el tope **opaco**
(`Tc ≈ BT 11 µm`) y por eso **subestima** plumas semi-transparentes — el satélite
ve el suelo cálido *a través* de la ceniza fina, así que la BT observada es más
cálida que el tope real. Wen-Rose usa la diferencia espectral entre 11 y 12 µm
(la ceniza silicatada absorbe distinto: BTD 11−12 < 0) para **despejar
simultáneamente la temperatura del tope y la transparencia**, separando la
contribución del suelo. El resultado es un `Tc` más frío y correcto → altura más
alta. Es la física de VOLCAT/Pavolonis 2013 en versión reducida (sin optimal
estimation ni RTM).

Modelo (aproximación no-scattering, `ε = 1 − t`), por banda i ∈ {11≡C14, 12≡C15}:

    I_i = (1 − t_i)·B_i(Tc) + t_i·B_i(Ts)
    t12 = t11^β        (acople de canales; β = 0.9 silicato andesita-dacita)

donde `B_i` es la radiancia de Planck de la banda (coeficientes del NetCDF L1b) y
`Ts` la BT de fondo (cielo claro). Se despeja `Tc` y luego se mapea a altitud con
``gfs_profile.altitudes_from_bt`` (REUSADO de Fase 2). **Garantía:** `Tc ≤ BT11`
siempre → la altura Wen-Rose **≥** BT-matching; el Δ es la corrección.

INDICATIVO. VOLCAT/SSEC sigue siendo el primario cuantitativo. NO da altura a
plumas de gas/SO₂ (transparentes en 11 µm). Detalle en
``docs/own_volcat/FASE3B_WENROSE.md``.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional, Union

import numpy as np

# Reuso EXACTO de la conversión radiancia↔BT (Fase 3b mezcla radiancias) y del
# mapeo Teff→altitud robusto a inversiones (Fase 2) → producción y tests comparten.
from src.fetch.gfs_profile import altitudes_from_bt  # noqa: F401  (re-export + uso)
from src.process.brightness_temp import planck_rad_from_bt

logger = logging.getLogger(__name__)

BT85_BAND = 11             # 8.4 µm (máscara tri-espectral)
BT11_BAND = 14             # 11.2 µm (ventana, canal "4" de Wen-Rose)
BT12_BAND = 15             # 12.3 µm (canal "5" de Wen-Rose)
CO2_BAND = 16              # 13.3 µm (CO₂) — chequeo INDEPENDIENTE de semi-transp.
CO2_SEMITRANSP_MIN = 0.5   # BTD(11−13.3) ≥ esto sobre la ceniza ⇒ semitransparente

BETA_SILICATE = 0.9        # razón de prof. óptica 12/11 — andesita-dacita chilena
BETA_RANGE = (0.85, 0.95)  # rango de β del silicato → banda de incertidumbre del tope
MIN_CLEAR_PX = 40          # mínimo de píxeles claros para estimar Ts de la escena
CLEAR_SKY_PCTL = 92        # percentil cálido = BT de superficie (cielo claro)
DELTA_WARN_KM = 5.0        # corrección Wen-Rose ≥ esto → flag (Ts/muestra sospechosos)
BAND_WIDE_KM = 3.0         # banda β ≥ esto → degrada la confianza


def wen_rose_confidence(mask_px: int, band_width_km, ts_is_clear_sky: bool) -> str:
    """Confianza **INDICATIVA** del tope Wen-Rose. Nunca devuelve "alta": es un
    producto indicativo, el cuantitativo validado sigue siendo VOLCAT.

    Degrada por (a) pocos píxeles de ceniza → estadístico ruidoso; (b) banda de
    incertidumbre por β ancha → microfísica mal restringida; (c) Ts de fallback
    (GFS, no observado) → fondo cálido peor estimado. Función PURA.
    """
    if mask_px < 5:
        return "muy baja"
    score = 2
    if mask_px < 15:
        score -= 1
    if band_width_km is not None and band_width_km > BAND_WIDE_KM:
        score -= 1
    if not ts_is_clear_sky:
        score -= 1
    return "media" if score >= 2 else ("baja" if score == 1 else "muy baja")


# ── Solver puro (sin red) ───────────────────────────────────────────────────

def clear_sky_bt(bt11_window, ash_mask, percentile: float = CLEAR_SKY_PCTL,
                 min_clear: int = MIN_CLEAR_PX) -> Optional[float]:
    """BT de **cielo claro** de la escena = percentil cálido de los píxeles
    finitos **no-ceniza** de la ventana en BT(11 µm).

    Es la "Ts" del modelo de Wen-Rose: la BT que el satélite ve sobre el suelo,
    ya en el marco radiométrico de ABI (atmósfera incluida). El percentil alto
    (no el máximo) descarta píxeles calientes espurios; excluir la máscara de
    ceniza evita contaminar con la propia pluma fría. Devuelve None si hay menos
    de ``min_clear`` píxeles claros (pluma llena el encuadre → usar fallback GFS).
    Función PURA.
    """
    bt = np.asarray(bt11_window, dtype="float64")
    clear = np.isfinite(bt) & ~np.asarray(ash_mask, dtype=bool)
    if int(clear.sum()) < min_clear:
        return None
    return float(np.percentile(bt[clear], percentile))


def co2_semitransparency(bt11, bt133, ash_mask) -> Optional[float]:
    """Chequeo INDEPENDIENTE de semi-transparencia con el canal CO₂ (13.3 µm).

    Por qué (geología → pipeline): el 13.3 µm cae en una banda de absorción de
    CO₂, así que su radiancia viene de **más arriba** en la atmósfera que la
    ventana de 11 µm. Sobre una pluma **semi-transparente**, el 11 µm ve más
    suelo cálido por debajo (ventana) que el 13.3 µm (el CO₂ lo absorbe) →
    ``BT(11) − BT(13.3) > 0``. Sobre una pluma **opaca** ambos ven el tope frío →
    diferencia ≈ 0. Es decir: confirma, con física distinta al despeje Wen-Rose,
    si la corrección de emisividad estaba justificada (un guard contra
    sobre-corregir un tope que en realidad era opaco).

    Devuelve la **mediana de BTD(11−13.3)** sobre los píxeles de ceniza (K), o
    None si no hay 13.3 µm o píxeles válidos. Función PURA.
    """
    if bt133 is None:
        return None
    bt11 = np.asarray(bt11, dtype="float64")
    bt133 = np.asarray(bt133, dtype="float64")
    m = (np.asarray(ash_mask, dtype=bool) & np.isfinite(bt11)
         & np.isfinite(bt133))
    if not m.any():
        return None
    return float(np.median(bt11[m] - bt133[m]))


def solve_tc_grid(bt11, bt12, ts_k, coef11, coef12, beta: float = BETA_SILICATE,
                  tc_floor_k: float = 180.0, n_grid: int = 220):
    """Despeje Wen-Rose de la temperatura del tope `Tc` por píxel (vectorizado).

    Para cada píxel busca el `Tc ∈ [tc_floor, BT11]` que mejor satisface el
    acople de canales ``t12(Tc) = t11(Tc)^β``, donde
    ``t_i(Tc) = (I_i − B_i(Tc)) / (B_i(Ts) − B_i(Tc))`` es la transmisividad
    implícita. Se usa **búsqueda en grilla del mínimo residuo** (no bisección):
    es robusta a la tangencia del residuo en plumas finas (donde la señal de 2
    canales es débil y la solución, poco sensible) y no necesita bracketing.

    ``coef11``/``coef12`` = ``(fk1, fk2, bc1, bc2)`` de cada banda (del NetCDF).
    ``ts_k`` puede ser escalar (BT de cielo claro) o array.

    Devuelve ``(tc, solved)``:
      - ``tc``: temperatura del tope (K). En píxeles **no resueltos** cae al
        **supuesto opaco** ``Tc = BT11`` (= BT-matching); NaN donde la BT es NaN.
      - ``solved``: bool — True solo donde el píxel es candidato semitransparente
        (ceniza BTD<0 sobre fondo cálido Ts>BT11) y hubo solución física.
    Función PURA.
    """
    bt11 = np.asarray(bt11, dtype="float64")
    bt12 = np.asarray(bt12, dtype="float64")
    ts = np.asarray(ts_k, dtype="float64")

    # Radiancias: observadas (I) y de fondo/cielo-claro (Bs).
    I11 = planck_rad_from_bt(bt11, *coef11)
    I12 = planck_rad_from_bt(bt12, *coef12)
    Bs11 = planck_rad_from_bt(ts, *coef11)
    Bs12 = planck_rad_from_bt(ts, *coef12)

    finite = np.isfinite(bt11) & np.isfinite(bt12)
    btd = np.where(finite, bt11 - bt12, 0.0)
    # Candidato Wen-Rose: ceniza (absorción inversa BTD<0) sobre fondo MÁS CÁLIDO
    # que lo observado (sin contraste no hay nada que corregir).
    elig = finite & (ts > bt11 + 0.5) & (btd < 0.0)

    hi = np.where(finite, bt11, tc_floor_k + 1.0)        # límite opaco Tc=BT11

    # Grilla normalizada u∈[0,1] → Tc por píxel en [floor, BT11].
    u = np.linspace(0.0, 1.0, n_grid).reshape((n_grid,) + (1,) * bt11.ndim)
    Tc_grid = tc_floor_k + u * (hi - tc_floor_k)         # (n_grid, *shape)

    B11 = planck_rad_from_bt(Tc_grid, *coef11)
    B12 = planck_rad_from_bt(Tc_grid, *coef12)
    with np.errstate(divide="ignore", invalid="ignore"):
        t11 = (I11 - B11) / (Bs11 - B11)
        t12 = (I12 - B12) / (Bs12 - B12)
        t11c = np.clip(t11, 1e-9, 1.0)
        resid = np.abs(t12 - np.power(t11c, beta))
    # Descartar hipótesis con transmisividades fuera de rango físico [0,1].
    bad = ((~np.isfinite(resid)) | (t11 < -0.05) | (t11 > 1.05)
           | (t12 < -0.05) | (t12 > 1.20))
    resid = np.where(bad, np.inf, resid)

    idx = np.argmin(resid, axis=0)                       # mejor Tc por píxel
    Tc = np.take_along_axis(Tc_grid, idx[None], axis=0)[0]
    min_res = np.take_along_axis(resid, idx[None], axis=0)[0]

    solved = elig & np.isfinite(min_res)
    Tc = np.where(solved, Tc, hi)                        # fallback opaco = BT11
    Tc = np.where(finite, Tc, np.nan)
    return Tc, solved


# ── Orquestación (con red) ──────────────────────────────────────────────────

def _bounds_for(v, r: float) -> dict:
    return {"lat_min": v.lat - r, "lat_max": v.lat + r,
            "lon_min": v.lon - r, "lon_max": v.lon + r}


def _coefs(ds) -> tuple:
    return (float(ds["planck_fk1"].values), float(ds["planck_fk2"].values),
            float(ds["planck_bc1"].values), float(ds["planck_bc2"].values))


def _top_stats(field_km, valid, alt_m, trop, percentile=95):
    """Tope (percentil) + máx sobre los píxeles NO 'capped' en la tropopausa
    (cirros mal detectados / overshooting no deben fijar el tope). Misma semántica
    que bt_matching_height. Devuelve (top_km, top_max_km, n_capped, all_capped)."""
    capped = (valid & (alt_m >= trop["z_m"] - 1.0)) if trop else np.zeros_like(valid)
    n_capped = int(np.sum(capped))
    clean = valid & ~capped
    if int(clean.sum()) > 0:
        vals = field_km[clean]
        return (float(np.percentile(vals, percentile)), float(vals.max()),
                n_capped, False)
    trop_km = trop["z_m"] / 1000.0 if trop else None
    return (trop_km, trop_km, n_capped, True)


def _wr_top_for_beta(bt11, bt12, ts_k, c11, c12, beta, mask, profile, trop,
                     percentile):
    """Tope p95 Wen-Rose para un β dado — para barrer el rango de microfísica y
    construir la banda de incertidumbre del tope. Devuelve km o None."""
    tc, _ = solve_tc_grid(bt11, bt12, ts_k, c11, c12, beta=beta)
    alt = altitudes_from_bt(tc, profile)
    valid = mask & np.isfinite(alt)
    field = np.where(valid, alt, np.nan) / 1000.0
    return _top_stats(field, valid, alt, trop, percentile)[0]


def wen_rose_top_height(
    dt: datetime,
    volcano: Union[str, object],
    radius_deg: float = 0.75,
    percentile: float = 95,
    beta: float = BETA_SILICATE,
) -> dict:
    """Altura del tope por Wen-Rose para un volcán en un instante.

    Pipeline: ventana geos desde C14 → baja C11/C14/C15 del mismo scan (con sus
    coeficientes Planck) → máscara de ceniza → Ts de cielo claro (fallback GFS
    skin-T) → despeje Tc (Wen-Rose) → mapea a altitud por el perfil GFS. Devuelve
    el tope Wen-Rose **y** el de BT-matching del MISMO scan (mismos píxeles) para
    cross-validación directa.

    Returns dict con ``status`` (ok/no_plume/no_data) y, si ok: ``top_km`` (p95
    Wen-Rose), ``top_bt_matching_km`` (p95 opaco), ``delta_km`` (corrección),
    ``ts_k``/``ts_source``, ``beta``, ``n_corrected`` (píxeles realmente
    corregidos), ``field_km`` (Wen-Rose) y ``field_bt_km``, además de
    ``mask_px``, ``so2_px/min``, ``scan_dt``, ``lat``/``lon``, ``tropopause_km``.
    """
    from src.config import (GOES19_PERSPECTIVE_POINT_HEIGHT as _H,
                            GOES19_SAT_LON as _SLON)
    from src.fetch.gfs_profile import fetch_gfs_profile
    from src.fetch.goes_acha import _geos_index_bbox, _window_latlon
    from src.fetch.goes_s3 import _scan_start, download_band_at, open_band
    from src.process.ash_detection import detect_ash_enhanced
    from src.process.brightness_temp import rad_to_bt

    source = ("Wen-Rose 1994 (corrección emisividad 2 canales 11/12µm → Tc) → "
              "perfil GFS T(z) · INDICATIVO · corrige el BT-matching en plumas "
              "semitransparentes · independiente de SSEC")

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

    # ── Ventana geos + coef Planck de C14 ────────────────────────────────
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
            coef14 = _coefs(ds14)
            bt14 = rad_to_bt(ds14.isel(y=slice(y0, y1), x=slice(x0, x1))).load().values
            xw, yw = x[x0:x1], y[y0:y1]
    except Exception as e:
        logger.exception("Wen-Rose C14: %s", e)
        return {"status": "no_data", "reason": "error leyendo C14",
                "volcano": v.name, "bounds": bounds, "source": source}

    scan_dt = _scan_start(p14.name)
    ref = scan_dt or dt
    lat, lon = _window_latlon(xw, yw, sat_lon=sat_lon, H=H)

    # ── C11/C15 del MISMO scan (C15 con sus coef) ────────────────────────
    bts = {14: bt14}
    coefs = {14: coef14}
    band_scans = {14: scan_dt}
    for b in (BT85_BAND, BT12_BAND):
        pb = download_band_at(ref, b)
        if pb is None:
            return {"status": "no_data", "reason": f"sin banda C{b:02d}",
                    "volcano": v.name, "bounds": bounds, "scan_dt": scan_dt,
                    "source": source}
        band_scans[b] = _scan_start(pb.name)
        try:
            with open_band(pb) as dsb:
                if b == BT12_BAND:
                    coefs[b] = _coefs(dsb)
                bts[b] = rad_to_bt(dsb.isel(y=slice(y0, y1),
                                            x=slice(x0, x1))).load().values
        except Exception as e:
            logger.exception("Wen-Rose C%02d: %s", b, e)
            return {"status": "no_data", "reason": f"error leyendo C{b:02d}",
                    "volcano": v.name, "bounds": bounds, "scan_dt": scan_dt,
                    "source": source}

    # Las 3 bandas deben ser del MISMO scan (igual guard que bt_matching).
    scans = {s for s in band_scans.values() if s is not None}
    if len(scans) > 1:
        logger.warning("Wen-Rose: bandas de scans distintos: %s", band_scans)
        return {"status": "no_data",
                "reason": "bandas C11/C14/C15 de scans distintos (S3 incompleto)",
                "volcano": v.name, "bounds": bounds, "scan_dt": scan_dt,
                "source": source}

    import xarray as xr

    def _da(a):
        return xr.DataArray(a, dims=("y", "x"))

    mask = detect_ash_enhanced(_da(bts[11]), _da(bts[14]), _da(bts[15])).values

    # ── C16 (13.3 µm CO₂) OPCIONAL: chequeo independiente de semi-transparencia ──
    # No es requerido (graceful si falta o cae en otro scan); +1 banda SOLO en este
    # retrieval, no en el pipeline NRT (por eso C16 vive en EXTENDED_IR_BANDS, fuera
    # de VOLCANIC_BANDS). Confirma/desmiente la corrección Wen-Rose con física
    # distinta (CO₂-slicing cualitativo). Ver co2_semitransparency().
    bt133 = None
    try:
        p16 = download_band_at(ref, CO2_BAND)
        if p16 is not None and _scan_start(p16.name) == scan_dt:
            with open_band(p16) as ds16:
                bt133 = rad_to_bt(ds16.isel(y=slice(y0, y1),
                                            x=slice(x0, x1))).load().values
    except Exception as e:
        logger.warning("Wen-Rose C16 (opcional): %s", e)
    co2_btd = co2_semitransparency(bts[14], bt133, mask)

    # Contexto SO2 (igual criterio que bt_matching / acha) para el dashboard.
    try:
        from src.config import SO2_INDICATOR_THRESHOLD as _SO2_THR
    except Exception:
        _SO2_THR = -3.0
    so2 = bts[11] - bts[14]
    so2_finite = np.isfinite(so2)
    so2_px = int(np.sum(so2_finite & (so2 < _SO2_THR)))
    so2_min = float(np.nanmin(so2)) if so2_finite.any() else None

    # ── Perfil GFS + temperatura de superficie (Ts) ──────────────────────
    profile = fetch_gfs_profile(v.lat, v.lon, ref)
    if profile is None:
        return {"status": "no_data", "reason": "sin perfil GFS (Open-Meteo)",
                "volcano": v.name, "bounds": bounds, "scan_dt": scan_dt,
                "so2_px": so2_px, "so2_min": so2_min, "source": source}

    n_clear = int((np.isfinite(bts[14]) & ~mask).sum())
    ts_k = clear_sky_bt(bts[14], mask)
    ts_source = "cielo claro (escena)"
    if ts_k is None:
        ts_k = profile.get("skin_temp_K")
        ts_source = "GFS skin-T (Open-Meteo)"
    if ts_k is None and profile.get("levels"):
        ts_k = profile["levels"][0]["T_K"]      # último recurso: nivel superficie
        ts_source = "GFS nivel superficie"

    trop = profile.get("tropopause")
    trop_km = trop["z_m"] / 1000.0 if trop else None
    now = datetime.now(timezone.utc)
    latency_min = (now - scan_dt).total_seconds() / 60.0 if scan_dt else None

    out = {
        "volcano": v.name, "bounds": bounds, "lat": lat, "lon": lon,
        "scan_dt": scan_dt, "latency_min": latency_min, "percentile": percentile,
        "source": source, "tropopause_km": trop_km, "beta": beta,
        "ts_k": (float(ts_k) if ts_k is not None else None), "ts_source": ts_source,
        "profile_time": profile.get("valid_time"),
        "so2_px": so2_px, "so2_min": so2_min, "co2_semitransp_btd": co2_btd,
    }

    # Si no hay Ts utilizable, Wen-Rose no puede correr → degradar a BT-matching
    # puro (todo opaco) con una nota; igual reportamos el campo BT.
    alt_bt = altitudes_from_bt(bts[14], profile)
    field_bt = np.where(mask & np.isfinite(alt_bt), alt_bt, np.nan) / 1000.0

    if ts_k is None:
        tc = bts[14]
        solved = np.zeros(bts[14].shape, dtype=bool)
        out["ts_note"] = "sin Ts → Wen-Rose degradado a BT-matching"
    else:
        tc, solved = solve_tc_grid(bts[14], bts[15], float(ts_k),
                                   coefs[14], coefs[15], beta=beta)

    alt_wr = altitudes_from_bt(tc, profile)
    ash = mask & np.isfinite(alt_wr)
    field_wr = np.where(ash, alt_wr, np.nan) / 1000.0
    valid = np.isfinite(np.where(ash, alt_wr, np.nan))
    n = int(valid.sum())
    n_corrected = int(np.sum(mask & solved))

    out.update({
        "field_km": field_wr, "field_bt_km": field_bt,
        "mask_px": n, "n_corrected": n_corrected,
    })

    if n == 0:
        out.update({"status": "no_plume", "top_km": None, "top_bt_matching_km": None,
                    "top_max_km": None, "delta_km": None, "n_capped": 0,
                    "all_capped": False})
        return out

    # Tope Wen-Rose y BT-matching sobre los MISMOS píxeles de ceniza (excluyendo
    # los 'capped' en la tropopausa).
    top_wr, top_wr_max, n_capped, all_capped = _top_stats(
        field_wr, valid, alt_wr, trop, percentile)
    valid_bt = mask & np.isfinite(alt_bt)
    top_bt, _, _, _ = _top_stats(field_bt, valid_bt, alt_bt, trop, percentile)
    delta = (top_wr - top_bt) if (top_wr is not None and top_bt is not None) else None

    # ── #1 Banda de incertidumbre por la microfísica (β ∈ BETA_RANGE) ────
    # β fija la razón de absorción 12/11; no la medimos (haría falta retrieval de
    # radio efectivo). En vez de fingir un número exacto, barremos el rango del
    # silicato (0.85-0.95) y reportamos el tope como banda. Solo si hubo
    # corrección real (con todo opaco, β no cambia nada → banda degenerada).
    top_lo = top_hi = top_wr
    if ts_k is not None and n_corrected > 0 and top_wr is not None:
        band = [_wr_top_for_beta(bts[14], bts[15], float(ts_k), coefs[14],
                                 coefs[15], b, mask, profile, trop, percentile)
                for b in BETA_RANGE]
        band = [t for t in band if t is not None] + [top_wr]
        top_lo, top_hi = min(band), max(band)
    band_width = (top_hi - top_lo) if (top_hi is not None
                                       and top_lo is not None) else None

    # ── #2 Guards de honestidad: corrección o Ts sospechosos ─────────────
    flags = []
    if delta is not None and delta >= DELTA_WARN_KM:
        flags.append(f"corrección grande (+{delta:.1f} km): verificá Ts y nº de píxeles")
    if ts_source != "cielo claro (escena)":
        flags.append(f"Ts de fallback ({ts_source}): fondo cálido no observado")
    elif n_clear < 4 * MIN_CLEAR_PX:
        flags.append(f"Ts con pocos píxeles claros ({n_clear}): fondo poco robusto")
    # #4: el CO₂ (13.3µm) es un árbitro INDEPENDIENTE. Si dice que la pluma es
    # opaca (BTD 11−13.3 chico) pero Wen-Rose igual corrigió, la corrección es
    # sospechosa de ser ruido (no semi-transparencia real).
    if (n_corrected > 0 and co2_btd is not None
            and co2_btd < CO2_SEMITRANSP_MIN):
        flags.append(f"CO₂ 13.3µm sugiere pluma ~opaca (BTD 11−13.3 ≈ {co2_btd:.1f} K): "
                     "corrección Wen-Rose poco confirmada")

    confidence = wen_rose_confidence(n, band_width,
                                     ts_source == "cielo claro (escena)")

    out.update({
        "status": "ok",
        "top_km": top_wr, "top_max_km": top_wr_max,
        "top_km_lo": top_lo, "top_km_hi": top_hi, "band_width_km": band_width,
        "top_bt_matching_km": top_bt, "delta_km": delta,
        "n_capped": n_capped, "all_capped": all_capped,
        "n_clear": n_clear, "confidence": confidence, "flags": flags,
    })
    return out
