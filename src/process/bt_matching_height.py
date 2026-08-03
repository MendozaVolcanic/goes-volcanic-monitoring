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
from datetime import datetime
from typing import Union

import numpy as np

# El mapeo BT→altitud (robusto a inversiones) vive junto al perfil GFS; lo
# re-exportamos para que PRODUCCIÓN y TESTS usen exactamente la misma función.
from src.fetch.gfs_profile import altitudes_from_bt  # noqa: F401  (re-export + uso)

logger = logging.getLogger(__name__)

BT11_BAND = 14             # 11.2 µm = C14, la ventana del BT-matching


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
    from src.process.scene import acquire_ash_scene

    source = ("BT-matching (BT 11µm del tope de ceniza → perfil GFS T(z)) · "
              "INDICATIVO (típ. cota inferior) · independiente de SSEC y ACHA")

    # Adquisición común (bandas del mismo scan + máscara + SO₂ + perfil GFS);
    # los guards de honestidad viven en scene.acquire_ash_scene.
    scene = acquire_ash_scene(dt, volcano, radius_deg, source=source,
                              label="BT-matching")
    if isinstance(scene, dict):
        return scene

    profile = scene.profile
    mask = scene.mask

    # ── Mapeo BT→altitud ─────────────────────────────────────────────────
    alt_m = altitudes_from_bt(scene.bts[BT11_BAND], profile)
    ash_alt = np.where(mask & np.isfinite(alt_m), alt_m, np.nan)
    field_km = ash_alt / 1000.0
    valid = np.isfinite(ash_alt)
    n = int(valid.sum())

    trop = profile.get("tropopause")
    trop_km = trop["z_m"] / 1000.0 if trop else None

    out = scene.base_out(percentile, source)
    out.update({"field_km": field_km, "mask_px": n})
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
