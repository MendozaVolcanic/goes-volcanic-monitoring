"""Test del retrieval de altura Wen-Rose sobre bandas VIIRS (M15/M16, 750 m).

Round-trip cerrado: sintetizo BT(M15) y BT(M16) de un tope a una temperatura Tc
conocida con el MISMO modelo forward de Wen-Rose (mezcla de radiancias de 2 canales
con t12=t11^β) y verifico que ``viirs_top_from_bt`` recupera la altitud de ese Tc
vía el perfil. Prueba que reusar el solver band-agnostic con los coeficientes de
Planck de VIIRS es físicamente consistente. PURO, sin red ni token.
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.process.brightness_temp import planck_rad_from_bt
from src.process.viirs_wen_rose import viirs_planck_coefs, viirs_top_from_bt


def _synth_profile():
    """Perfil T(z) lineal: superficie 290 K @1 km, lapse -6.5 K/km hasta la
    tropopausa 212 K @13 km. Formato de fetch_gfs_profile."""
    levels = []
    for z in range(1000, 13001, 1000):
        T = 290.0 - 6.5 * (z - 1000) / 1000.0
        levels.append({"p_hPa": 1000 - z / 20, "z_m": float(z), "T_K": float(T)})
    trop = min(levels, key=lambda l: l["T_K"])
    return {"levels": levels, "tropopause": trop}


def _bt_from_rad(rad, coef):
    """Inversa de planck_rad_from_bt con bc1=0,bc2=1: BT = fk2/ln(fk1/rad+1)."""
    fk1, fk2, bc1, bc2 = coef
    return (fk2 / np.log(fk1 / rad + 1.0) - bc1) / bc2


def test_viirs_planck_coefs_sane():
    """Coefs de M15 físicamente plausibles (ν≈929 cm⁻¹ → fk2≈1337)."""
    fk1, fk2, bc1, bc2 = viirs_planck_coefs("M15")
    assert abs(fk2 - 1337.0) < 5.0
    assert fk1 > 0 and bc1 == 0.0 and bc2 == 1.0
    # M16 (12µm) tiene menor número de onda → menor fk2 que M15 (11µm).
    assert viirs_planck_coefs("M16")[1] < fk2


def test_wen_rose_viirs_roundtrip():
    """Tope a Tc=235 K (≈9.5 km) sintetizado con β=0.7 y una pluma moderadamente
    opaca (t11=0.3) → el retrieval recupera la altura dentro de ±0.7 km.

    Nota: se usa t11=0.3 a propósito. Para plumas MUY semitransparentes (t11≳0.5)
    el Wen-Rose de 2 canales tiene una segunda raíz fría espuria y los guards
    (well_constrained / revert a la cota) la rechazan — el mismo comportamiento
    honesto que en el ABI (validado en `test_wen_rose.py`)."""
    prof = _synth_profile()
    c15 = viirs_planck_coefs("M15")
    c16 = viirs_planck_coefs("M16")

    Tc_true, Ts, t11, beta = 235.0, 285.0, 0.3, 0.7
    t12 = t11 ** beta
    # Mezcla Wen-Rose: I = (1-t)·B(Tc) + t·B(Ts) por canal.
    rad11 = (1 - t11) * planck_rad_from_bt(Tc_true, *c15) + t11 * planck_rad_from_bt(Ts, *c15)
    rad12 = (1 - t12) * planck_rad_from_bt(Tc_true, *c16) + t12 * planck_rad_from_bt(Ts, *c16)
    bt11 = np.array([[_bt_from_rad(rad11, c15)]])
    bt12 = np.array([[_bt_from_rad(rad12, c16)]])
    # Semitransparente: BTD 11-12 debe ser negativo (12µm ve más superficie cálida).
    assert bt11[0, 0] < bt12[0, 0]

    # Altitud verdadera de Tc en el perfil.
    z_true = np.interp(Tc_true, [l["T_K"] for l in reversed(prof["levels"])],
                       [l["z_m"] for l in reversed(prof["levels"])]) / 1000.0

    r = viirs_top_from_bt(bt11, bt12, Ts, prof, mask=np.array([[True]]))
    assert r is not None and r["top_km"] is not None
    # Recupera la altura del Tc verdadero — la prueba central del método.
    assert abs(r["top_km"] - z_true) < 0.7, (r["top_km"], z_true)
    # La banda β se computó (valores finitos). Nota: el "bracketing" central∈banda
    # es propiedad del dato REAL; en este sintético exacto-en-β=0.7, resolver con
    # β=0.55/0.95 degrada (raíz distinta), así que solo verificamos que existe.
    assert r["band_lo_km"] is not None and r["band_hi_km"] is not None
    assert r["n_px"] == 1


def test_viirs_top_empty_mask_none():
    """Sin píxeles de ceniza → None (no explota)."""
    prof = _synth_profile()
    r = viirs_top_from_bt(np.array([[250.0]]), np.array([[251.0]]), 285.0, prof,
                          mask=np.array([[False]]))
    assert r is None


if __name__ == "__main__":
    test_viirs_planck_coefs_sane()
    test_wen_rose_viirs_roundtrip()
    test_viirs_top_empty_mask_none()
    print("OK — viirs_wen_rose round-trip")
