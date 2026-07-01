"""Tests β-ratios de composición (Pavolonis 2010) — confirmación INDICATIVA de que
la pluma es silicato (ceniza) vs hielo/agua.

Round-trip: sintetizo un píxel con emisividades ε(λ) conocidas bajo el modelo
β_tropo (T_ref = tropopausa), y verifico que el módulo recupera los β y clasifica
la composición contra los anclas VERIFICADOS de la Tabla 2. Lógica pura.
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.process.beta_ratios import (BETA_ANCHORS, beta_composition, beta_ratio,
                                      classify_composition, cloud_emissivity)
from src.process.brightness_temp import planck_rad_from_bt

# Coeficientes Planck reales de GOES ABI — 3 bandas DISTINTAS (8.5/11/12 µm).
COEF11 = (13634.3, 1493.5, 0.40000, 0.99910)   # C11 8.4 µm
COEF14 = (8510.22, 1286.67, 0.07635, 0.99964)  # C14 11.2 µm
COEF15 = (6454.62, 1173.03, 0.16640, 0.99931)  # C15 12.3 µm


def _bt_from_rad(rad, coef):
    fk1, fk2, bc1, bc2 = coef
    rad = np.asarray(rad, dtype="float64")
    t_eff = fk2 / np.log(fk1 / rad + 1.0)
    return (t_eff - bc1) / bc2


def _synth_bt(eps, t_ref_k, clr_bt_k, coef):
    """BT observada de un píxel con emisividad ε bajo β_tropo:
    R_obs = ε·B(T_ref) + (1−ε)·R_clr. Inversa exacta de cloud_emissivity."""
    B_ref = planck_rad_from_bt(t_ref_k, *coef)
    R_clr = planck_rad_from_bt(clr_bt_k, *coef)
    R_obs = eps * B_ref + (1 - eps) * R_clr
    return float(_bt_from_rad(R_obs, coef))


def test_beta_ratio_analytic():
    """β = ln(1−ε_num)/ln(1−ε_den) exacto."""
    b = beta_ratio(0.493, 0.700)
    assert abs(float(b) - (np.log(1 - 0.493) / np.log(1 - 0.700))) < 1e-9


def test_cloud_emissivity_roundtrip():
    """Sintetizo BT con ε=0.6 y cloud_emissivity la recupera."""
    t_ref, clr = 210.0, 290.0
    bt = _synth_bt(0.6, t_ref, clr, COEF14)
    e = float(cloud_emissivity(np.array([bt]), t_ref, np.array([clr]), COEF14)[0])
    assert abs(e - 0.6) < 1e-3, e


def test_classify_anchors_to_themselves():
    """Cada punto ancla de la Tabla 2 clasifica a su propia composición."""
    for label, a in BETA_ANCHORS.items():
        c = classify_composition(a["b12_11"], a["b85_11"])
        assert c["label"] == label, (label, c)
    assert classify_composition(None, 0.7) is None
    assert classify_composition(np.nan, 0.7) is None


def test_beta_composition_recovers_ash():
    """Píxel sintetizado con los β de ceniza (Tabla 2) → composition='ceniza'."""
    t_ref, clr = 210.0, 290.0
    # ε que reproducen β(12,11)=0.564 y β(8.5,11)=0.705 con ε(11)=0.70:
    e11 = 0.70
    ln11 = np.log(1 - e11)
    e12 = 1 - np.exp(0.564 * ln11)
    e85 = 1 - np.exp(0.705 * ln11)
    bt11 = _synth_bt(e11, t_ref, clr, COEF14)
    bt12 = _synth_bt(e12, t_ref, clr, COEF15)
    bt85 = _synth_bt(e85, t_ref, clr, COEF11)
    r = beta_composition(np.array([bt85]), np.array([bt11]), np.array([bt12]),
                         t_ref, clr, clr, clr, COEF11, COEF14, COEF15)
    assert r is not None
    assert abs(r["beta_12_11"] - 0.564) < 0.03, r
    assert abs(r["beta_85_11"] - 0.705) < 0.03, r
    assert r["composition"] == "ceniza" and r["is_ash"] is True


def test_beta_composition_recovers_ice():
    """Píxel con los β de hielo (Tabla 2) → composition='hielo', is_ash=False."""
    t_ref, clr = 210.0, 290.0
    e11 = 0.70
    ln11 = np.log(1 - e11)
    e12 = 1 - np.exp(1.07 * ln11)     # β(12,11)=1.07 (hielo)
    e85 = 1 - np.exp(0.836 * ln11)    # β(8.5,11)=0.836
    bt11 = _synth_bt(e11, t_ref, clr, COEF14)
    bt12 = _synth_bt(e12, t_ref, clr, COEF15)
    bt85 = _synth_bt(e85, t_ref, clr, COEF11)
    r = beta_composition(np.array([bt85]), np.array([bt11]), np.array([bt12]),
                         t_ref, clr, clr, clr, COEF11, COEF14, COEF15)
    assert r["composition"] == "hielo" and r["is_ash"] is False, r


def test_beta_composition_empty_returns_none():
    """Sin píxeles válidos → None (no excepción)."""
    nan = np.full((2, 2), np.nan)
    assert beta_composition(nan, nan, nan, 210.0, 290, 290, 290,
                            COEF11, COEF14, COEF15) is None


if __name__ == "__main__":
    test_beta_ratio_analytic()
    test_cloud_emissivity_roundtrip()
    test_classify_anchors_to_themselves()
    test_beta_composition_recovers_ash()
    test_beta_composition_recovers_ice()
    test_beta_composition_empty_returns_none()
    print("OK — tests β-ratios passed")
