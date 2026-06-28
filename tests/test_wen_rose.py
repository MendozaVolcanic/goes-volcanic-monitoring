"""Tests Fase 3b — retrieval de altura Wen & Rose 1994 (corrección de emisividad
2 canales 11/12 µm) sobre el BT-matching.

Lo central es un **round-trip de forward-model**: elijo una temperatura de tope
Tc y una transparencia t conocidas, sintetizo las BT que el satélite vería
(mezcla de radiancia de la nube + suelo cálido visto a través de ella), y
verifico que el solver recupera Tc. Eso pinea la física del despeje sin depender
de la red. El camino con red (bandas L1b + GFS) hace skip si S3/Open-Meteo fallan.
"""
import functools
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.process.brightness_temp import planck_rad_from_bt

# Coeficientes Planck reales de GOES ABI — DISTINTOS por banda para que el BTD
# 11−12 lleve información espectral (sin eso no hay despeje de 2 canales).
COEF14 = (8510.22, 1286.67, 0.07635, 0.99964)   # C14 11.2 µm
COEF15 = (6454.62, 1173.03, 0.16640, 0.99931)   # C15 12.3 µm


@functools.lru_cache(maxsize=1)
def _net_ok() -> bool:
    try:
        import s3fs
        s3fs.S3FileSystem(anon=True).ls("noaa-goes19/ABI-L1b-RadF/", detail=False)
        return True
    except Exception:
        return False


def _bt_from_rad(rad, coef):
    """Inversa local de planck_rad_from_bt (radiancia → BT) para sintetizar las
    BT observadas en el test. Espejo exacto de rad_to_bt."""
    fk1, fk2, bc1, bc2 = coef
    rad = np.asarray(rad, dtype="float64")
    t_eff = fk2 / np.log(fk1 / rad + 1.0)
    return (t_eff - bc1) / bc2


def _synthesize_observed(tc_k, t11, ts_k, beta=0.9):
    """Forward-model Wen-Rose: dado el tope (Tc, t11) sobre suelo a Ts, devolver
    (bt11, bt12) que el satélite mediría. t12 = t11^β (acople de canales)."""
    t12 = t11 ** beta
    b11_c = planck_rad_from_bt(tc_k, *COEF14)
    b11_s = planck_rad_from_bt(ts_k, *COEF14)
    b12_c = planck_rad_from_bt(tc_k, *COEF15)
    b12_s = planck_rad_from_bt(ts_k, *COEF15)
    i11 = (1 - t11) * b11_c + t11 * b11_s
    i12 = (1 - t12) * b12_c + t12 * b12_s
    return _bt_from_rad(i11, COEF14), _bt_from_rad(i12, COEF15)


# ── Solver puro (sin red) ───────────────────────────────────────────────────

def test_solve_tc_recovers_forward_modeled_pixel():
    """EL test clave: forward-model con Tc=228 K, t=0.45, Ts=292 K → el solver
    debe recuperar Tc dentro de la resolución de grilla."""
    from src.process.wen_rose_height import solve_tc_grid

    tc_true, t11_true, ts = 228.0, 0.45, 292.0
    bt11, bt12 = _synthesize_observed(tc_true, t11_true, ts)
    # la pluma es genuinamente semitransparente: la BT observada es MÁS CÁLIDA
    # que el tope real (ve el suelo a través de la ceniza) y BTD 11−12 < 0.
    assert bt11 > tc_true + 5, (bt11, tc_true)
    assert bt11 - bt12 < 0, (bt11, bt12)

    tc, solved, _ = solve_tc_grid(np.array([bt11]), np.array([bt12]), ts,
                               COEF14, COEF15, beta=0.9)
    assert bool(solved[0]), "debió resolver un píxel semitransparente claro"
    assert abs(tc[0] - tc_true) < 2.0, (tc[0], tc_true)
    # corrección real: el Tc recuperado es MÁS FRÍO que la BT observada
    assert tc[0] < bt11 - 3, (tc[0], bt11)


def test_solve_tc_recovers_range_of_transparencies():
    """Recupera Tc en un rango de transparencias (vectorizado, varios píxeles)."""
    from src.process.wen_rose_height import solve_tc_grid

    ts = 290.0
    tcs = np.array([215.0, 225.0, 235.0, 245.0])
    t11s = np.array([0.30, 0.45, 0.60, 0.75])
    bt11, bt12 = _synthesize_observed(tcs, t11s, ts)
    tc, solved, _ = solve_tc_grid(bt11, bt12, ts, COEF14, COEF15, beta=0.9)
    assert solved.all(), solved
    np.testing.assert_allclose(tc, tcs, atol=2.0)


def test_wen_rose_colder_than_bt_matching():
    """La corrección sube la altura: Tc_WenRose ≤ BT11_obs siempre (cota), y
    estrictamente menor en semitransparentes → altura mayor que BT-matching."""
    from src.process.wen_rose_height import solve_tc_grid

    ts = 295.0
    bt11, bt12 = _synthesize_observed(np.array([220.0]), np.array([0.4]), ts)
    tc, _, _ = solve_tc_grid(bt11, bt12, ts, COEF14, COEF15, beta=0.9)
    assert tc[0] <= bt11[0] + 1e-6
    assert tc[0] < bt11[0] - 3.0   # mejora apreciable


def test_opaque_pixel_falls_back_to_bt():
    """Píxel ~opaco (t≈0 → BTD≈0): sin información de 2 canales, el solver debe
    caer al supuesto opaco Tc≈BT11 (= BT-matching), no inventar un Tc frío."""
    from src.process.wen_rose_height import solve_tc_grid

    ts = 295.0
    bt11, bt12 = _synthesize_observed(np.array([230.0]), np.array([0.02]), ts)
    tc, solved, _ = solve_tc_grid(bt11, bt12, ts, COEF14, COEF15, beta=0.9)
    # opaco → BT11 ≈ Tc real, y el retrieval no debe alejarse mucho de BT11
    assert abs(tc[0] - bt11[0]) < 3.0, (tc[0], bt11[0])


def test_positive_btd_not_ash_fallback_opaque():
    """BTD 11−12 > 0 (hielo/nube meteo, no ceniza): no es candidato Wen-Rose →
    fallback opaco (Tc = BT11), solved=False."""
    from src.process.wen_rose_height import solve_tc_grid

    bt11 = np.array([250.0])
    bt12 = np.array([248.0])     # BTD = +2 K → no ceniza
    tc, solved, _ = solve_tc_grid(bt11, bt12, 295.0, COEF14, COEF15, beta=0.9)
    assert not bool(solved[0])
    assert abs(tc[0] - bt11[0]) < 1e-6   # opaco exacto


def test_surface_not_warmer_fallback():
    """Si Ts no es más cálido que la BT observada (no hay fondo cálido que
    corregir), fallback opaco — no se puede despejar."""
    from src.process.wen_rose_height import solve_tc_grid

    bt11, bt12 = _synthesize_observed(np.array([260.0]), np.array([0.4]), 290.0)
    # Ts frío (= la propia BT): sin contraste no hay solución
    tc, solved, _ = solve_tc_grid(bt11, bt12, float(bt11[0]) - 1.0,
                               COEF14, COEF15, beta=0.9)
    assert not bool(solved[0])


def test_nan_pixels_propagate_and_dont_crash():
    """NaN en la BT → no resuelto, sin excepción."""
    from src.process.wen_rose_height import solve_tc_grid

    bt11 = np.array([np.nan, 230.0])
    bt12 = np.array([np.nan, 232.0])
    tc, solved, _ = solve_tc_grid(bt11, bt12, 295.0, COEF14, COEF15, beta=0.9)
    assert not bool(solved[0])
    assert bool(solved[1])


# ── clear_sky_bt (Ts de la escena, sin red) ─────────────────────────────────

def test_clear_sky_bt_picks_warm_background():
    """Percentil cálido de los píxeles finitos NO-ceniza = BT de cielo claro.
    Ignora la pluma fría (enmascarada) y la nube meteo fría (no enmascarada)."""
    from src.process.wen_rose_height import clear_sky_bt

    bt = np.concatenate([
        np.full(200, 291.0),   # suelo cálido (fondo claro)
        np.full(40, 250.0),    # nube meteo fría (no ceniza)
        np.full(60, 220.0),    # pluma de ceniza (enmascarada)
    ]).reshape(30, 10)
    mask = np.zeros(bt.shape, dtype=bool)
    mask.ravel()[240:300] = True    # los últimos 60 = ceniza
    ts = clear_sky_bt(bt, mask, percentile=92)
    assert ts is not None and ts > 285.0, ts


def test_clear_sky_bt_too_few_clear_returns_none():
    """Casi todo es ceniza (< MIN_CLEAR_PX claros) → None (usar fallback GFS)."""
    from src.process.wen_rose_height import clear_sky_bt

    bt = np.full((10, 10), 220.0)
    mask = np.ones(bt.shape, dtype=bool)
    mask.ravel()[:5] = False   # solo 5 claros
    assert clear_sky_bt(bt, mask) is None


def test_clear_sky_heterogeneity():
    """Spread p90−p10 del fondo: bajo si es uniforme, alto si hay mar+tierra."""
    from src.process.wen_rose_height import clear_sky_heterogeneity

    nomask = np.zeros((20, 20), dtype=bool)
    uniform = np.full((20, 20), 290.0)
    uniform[0, 0] = 289.0   # apenas variación
    assert clear_sky_heterogeneity(uniform, nomask) < 5.0
    # mitad mar (275 K) + mitad tierra (295 K) → spread grande
    mixed = np.full((20, 20), 295.0)
    mixed[:10, :] = 275.0
    assert clear_sky_heterogeneity(mixed, nomask) > 15.0
    # sin claros → None
    assert clear_sky_heterogeneity(uniform, np.ones((20, 20), dtype=bool)) is None


# ── Guard de mal-condicionamiento (sin red) ─────────────────────────────────

def test_underconstrained_thin_plume_flagged():
    """Pluma MUY fina (t≈0.9): el dato no restringe el Tc (residuo plano) →
    well_constrained False. Pluma densa (t≈0.3): mínimo agudo → True. Es el
    guard que evita reportar un Tc frío espurio (el +10.9 km que vimos)."""
    from src.process.wen_rose_height import solve_tc_grid

    ts = 295.0
    bt11_d, bt12_d = _synthesize_observed(np.array([225.0]), np.array([0.30]), ts)
    bt11_t, bt12_t = _synthesize_observed(np.array([225.0]), np.array([0.90]), ts)
    _, sol_d, wc_d = solve_tc_grid(bt11_d, bt12_d, ts, COEF14, COEF15)
    _, sol_t, wc_t = solve_tc_grid(bt11_t, bt12_t, ts, COEF14, COEF15)
    assert bool(sol_d[0]) and bool(wc_d[0]), "pluma densa debe quedar bien restringida"
    assert bool(sol_t[0]) and not bool(wc_t[0]), "pluma fina NO debe quedar restringida"


# ── Chequeo CO₂ 13.3µm de semi-transparencia (sin red) ──────────────────────

def test_co2_semitransparency_indicator():
    """BTD(11−13.3) > 0 sobre la ceniza ⇒ semitransparente; ≈0 ⇒ opaca."""
    from src.process.wen_rose_height import (CO2_SEMITRANSP_MIN,
                                             co2_semitransparency)

    mask = np.array([[True, True, False]])
    # semitransparente: 11µm ve el suelo cálido, 13.3µm (CO2) no
    bt11 = np.array([[250.0, 252.0, 290.0]])
    bt133 = np.array([[243.0, 244.0, 270.0]])
    v = co2_semitransparency(bt11, bt133, mask)
    assert v is not None and v > CO2_SEMITRANSP_MIN, v   # ~8 K

    # opaca: 11 y 13.3 ven el mismo tope frío
    bt11o = np.array([[221.0, 220.0, 290.0]])
    bt133o = np.array([[220.5, 220.0, 268.0]])
    vo = co2_semitransparency(bt11o, bt133o, mask)
    assert vo is not None and vo < CO2_SEMITRANSP_MIN, vo  # ~0.5

    # sin 13.3µm → None; sin píxeles de ceniza → None
    assert co2_semitransparency(bt11, None, mask) is None
    assert co2_semitransparency(bt11, bt133, np.zeros_like(mask, dtype=bool)) is None


# ── Confianza INDICATIVA (sin red) ──────────────────────────────────────────

def test_wen_rose_confidence_levels():
    """Confianza nunca 'alta'; degrada por pocos px, banda β ancha o Ts fallback."""
    from src.process.wen_rose_height import wen_rose_confidence

    # buen caso: muchos px, banda angosta, Ts de cielo claro → media (máx posible)
    assert wen_rose_confidence(40, 1.0, True) == "media"
    # pocos px → baja
    assert wen_rose_confidence(10, 1.0, True) == "baja"
    # muy pocos px → muy baja (corta de entrada)
    assert wen_rose_confidence(3, 0.5, True) == "muy baja"
    # banda ancha degrada
    assert wen_rose_confidence(40, 4.0, True) == "baja"
    # Ts de fallback degrada
    assert wen_rose_confidence(40, 1.0, False) == "baja"
    # combinación de penalizaciones → muy baja
    assert wen_rose_confidence(40, 4.0, False) == "muy baja"


# ── Orquestación (short-circuit sin red) ────────────────────────────────────

def test_wen_rose_unknown_volcano_no_data():
    """Volcán inexistente → no_data sin tocar la red."""
    from src.process.wen_rose_height import wen_rose_top_height

    r = wen_rose_top_height(datetime.now(timezone.utc), "NoExisteXYZ")
    assert r["status"] == "no_data"


if __name__ == "__main__":
    test_solve_tc_recovers_forward_modeled_pixel()
    test_solve_tc_recovers_range_of_transparencies()
    test_wen_rose_colder_than_bt_matching()
    test_opaque_pixel_falls_back_to_bt()
    test_positive_btd_not_ash_fallback_opaque()
    test_surface_not_warmer_fallback()
    test_nan_pixels_propagate_and_dont_crash()
    test_clear_sky_bt_picks_warm_background()
    test_clear_sky_bt_too_few_clear_returns_none()
    print("OK — tests puros Wen-Rose passed")
