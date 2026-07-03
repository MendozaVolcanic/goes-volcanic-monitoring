# ════════════════════════════════════════════════════════════════════
# FICHA SDA · viirs_wen_rose.py · SDA: Monitoreo Volcánico GOES-19 · ID: SDA-GOES-01
# Objetivo      : altura de tope de pluma con VIIRS (split-window M15/M16, 750m) — mismo método Wen-Rose que el ABI, 3× más fino
# Lógica        : reusa el solver band-agnostic de wen_rose_height (solve_tc_grid) con los coeficientes de Planck de VIIRS derivados del número de onda
# Modelo/método : Wen & Rose 1994 (2 canales) + banda β de incertidumbre — MISMO código que ABI, distinta banda física
# Datos entrada : BT(M15 10.76µm), BT(M16 12.01µm), Ts de cielo claro, perfil GFS T(z) — SIN datos personales
# Variables     : Tc del tope, banda β (0.55–0.95), tope p95, cota inferior por revert
# Limitaciones  : coeficientes Planck aproximados (bc1=0, bc2=1, sin band-correction); VIIRS sin canal CO2 13.3µm → sin árbitro CO2; polar (~2 pasadas/día)
# Refs/datos    : Wen & Rose 1994; solver clonado de wen_rose_height.py; coefs de central wavenumber (GOES ABI Planck form)
# Ficha completa: docs/FICHA_SDA_GOES.md
# ════════════════════════════════════════════════════════════════════
"""Altura de tope de pluma con VIIRS (split-window de las bandas M, 750 m).

Por qué (geología → pipeline): es el MISMO retrieval Wen-Rose que ya corre sobre el
ABI (``src/process/wen_rose_height.py``), pero alimentado con las bandas térmicas de
VIIRS —M15 (10.763 µm) y M16 (12.013 µm)— que ven a **750 m** en vez de los 2 km del
ABI. El solver ``solve_tc_grid`` ya es **band-agnostic** (recibe los coeficientes de
Planck por argumento), así que reusamos toda la física validada; lo único propio de
VIIRS son sus coeficientes de Planck, que derivamos del número de onda central.

Aproximación declarada: usamos la forma de Planck del ABI (``fk1/fk2/bc1/bc2``) con
``fk1 = c1·ν³``, ``fk2 = c2·ν`` del número de onda central de cada banda M, y
``bc1=0, bc2=1`` (sin corrección de banda). El error de esa aproximación es chico
frente a la incertidumbre de la banda β y al carácter INDICATIVO del producto; para
consistencia forward∘inversa lo que importa es usar los MISMOS coeficientes al ir y
volver de radiancia, cosa que garantizamos.

Diferencia física vs ABI: VIIRS **no tiene** el canal CO₂ 13.3 µm → no hay árbitro
CO₂ (``co2_verdict``). El resto (banda β, revert de píxeles no confiables a la cota,
Ts de cielo claro) se hereda igual. INDICATIVO; VOLCAT/SSEC sigue siendo primario.
"""

from __future__ import annotations

from typing import Optional

import numpy as np

from src.process.viirs_bt import BAND_LAMBDA_UM

# Constantes de Planck en la convención GOES ABI (Rad en mW/(m²·sr·cm⁻¹)):
#   fk1 = c1·ν³,  fk2 = c2·ν   con ν = número de onda central (cm⁻¹).
# Verificado contra el ABI banda 14 (ν≈893 → fk1≈8480, fk2≈1285).
_C1_ABI = 1.191042e-5      # mW/(m²·sr·cm⁻⁴)
_C2_ABI = 1.4387752        # cm·K


def viirs_planck_coefs(band: str) -> tuple:
    """Coeficientes de Planck (fk1, fk2, bc1, bc2) de una banda M VIIRS, derivados
    de su número de onda central. ``bc1=0, bc2=1`` (aprox sin band-correction).
    Compatibles con ``planck_rad_from_bt`` de wen_rose. PURA."""
    nu = 1.0e4 / BAND_LAMBDA_UM[band]          # µm → cm⁻¹
    fk1 = _C1_ABI * nu ** 3
    fk2 = _C2_ABI * nu
    return (fk1, fk2, 0.0, 1.0)


def viirs_top_from_bt(
    bt_m15, bt_m16, ts_k: float, profile: dict, mask,
    percentile: float = 95,
) -> Optional[dict]:
    """Tope de pluma Wen-Rose desde BT(M15), BT(M16) VIIRS + Ts + perfil GFS.

    Reusa ``_wr_top_for_beta`` de wen_rose_height (solver + revert a cota + mapeo
    Tc→altitud) para el β central y los extremos del rango → banda de incertidumbre.

    Args:
        bt_m15, bt_m16: arrays de temperatura de brillo (K) — M15≈11µm, M16≈12µm.
        ts_k:           Ts de cielo claro de la escena (K).
        profile:        perfil GFS ``{levels, tropopause}`` (fetch_gfs_profile).
        mask:           máscara booleana de píxeles de ceniza.
        percentile:     percentil del tope (default p95).

    Returns:
        dict ``{top_km, band_lo_km, band_hi_km, source}`` o None si <1 píxel de
        ceniza o el perfil no sirve. ``top_km`` None si no se pudo estimar.
    """
    from src.process.wen_rose_height import (BETA_RANGE, BETA_SILICATE,
                                             _wr_top_for_beta)

    mask = np.asarray(mask, dtype=bool)
    if not mask.any():
        return None
    trop = (profile or {}).get("tropopause")
    c15 = viirs_planck_coefs("M15")
    c16 = viirs_planck_coefs("M16")

    top = _wr_top_for_beta(bt_m15, bt_m16, ts_k, c15, c16, BETA_SILICATE,
                           mask, profile, trop, percentile)
    band = [_wr_top_for_beta(bt_m15, bt_m16, ts_k, c15, c16, b, mask, profile,
                             trop, percentile) for b in BETA_RANGE]
    band = [x for x in band if x is not None]
    return {
        "top_km": top,
        "band_lo_km": min(band) if band else None,
        "band_hi_km": max(band) if band else None,
        "n_px": int(mask.sum()),
        "source": ("Wen-Rose sobre VIIRS M15/M16 (750 m) · INDICATIVO · sin árbitro "
                   "CO₂ (VIIRS no tiene 13.3 µm)"),
    }
