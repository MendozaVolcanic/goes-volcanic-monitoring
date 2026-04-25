"""Tests para conversion radiancia -> temperatura de brillo (Planck inverso).

Valida que rad_to_bt() recupera la temperatura correcta usando la funcion
de Planck directa como verdad de referencia. Si la inversa esta mal, el
producto Ash RGB y todos los BTD quedan corruptos silenciosamente.
"""

import sys
from pathlib import Path

import numpy as np
import xarray as xr

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.process.brightness_temp import rad_to_bt


# Coeficientes Planck reales de GOES-16 ABI Band 14 (11.2 um) — referencia publica
# Source: GOES-R PUG Vol 3, ejemplos canonicos
FK1_B14 = 8510.22
FK2_B14 = 1286.67
BC1_B14 = 0.07635
BC2_B14 = 0.99964


def planck_forward(bt_kelvin: float, fk1: float, fk2: float, bc1: float, bc2: float) -> float:
    """Planck directo: BT (K) -> radiancia. Usado como ground truth para round-trip."""
    t_eff = bc1 + bc2 * bt_kelvin
    rad = fk1 / (np.exp(fk2 / t_eff) - 1)
    return rad


def _make_synthetic_ds(rad_values: np.ndarray) -> xr.Dataset:
    """Construye Dataset minimal con la estructura que rad_to_bt() espera."""
    return xr.Dataset(
        {
            "Rad": (("y", "x"), rad_values),
            "planck_fk1": ((), FK1_B14),
            "planck_fk2": ((), FK2_B14),
            "planck_bc1": ((), BC1_B14),
            "planck_bc2": ((), BC2_B14),
        }
    )


def test_planck_roundtrip_known_temperatures():
    """Round-trip BT -> Rad -> BT debe recuperar la temperatura original."""
    # Rango realista para nubes volcanicas: muy frias (tope tropopausa) a calidas (sfc)
    bt_input = np.array([[200.0, 220.0, 240.0], [260.0, 280.0, 300.0]])

    rad = np.vectorize(lambda t: planck_forward(t, FK1_B14, FK2_B14, BC1_B14, BC2_B14))(bt_input)

    ds = _make_synthetic_ds(rad)
    bt_recovered = rad_to_bt(ds).values

    np.testing.assert_allclose(bt_recovered, bt_input, rtol=1e-6, atol=1e-4)


def test_planck_negative_radiance_returns_nan():
    """Radiancia negativa o cero (artefacto de calibracion) debe dar NaN, no crash."""
    rad = np.array([[1.0, 0.0, -0.5], [50.0, 100.0, 200.0]])
    ds = _make_synthetic_ds(rad)
    bt = rad_to_bt(ds).values

    assert np.isnan(bt[0, 1])  # rad=0
    assert np.isnan(bt[0, 2])  # rad<0
    assert not np.isnan(bt[0, 0])  # rad valido
    assert not np.isnan(bt[1, 2])


def test_planck_monotonic():
    """Radiancia mayor debe dar temperatura mayor (monotonia fisica)."""
    bts = np.linspace(200, 320, 10)
    rads = np.array([planck_forward(t, FK1_B14, FK2_B14, BC1_B14, BC2_B14) for t in bts])

    # rads debe ser estrictamente creciente
    assert np.all(np.diff(rads) > 0), "Planck no monotonico — algo muy mal"

    ds = _make_synthetic_ds(rads.reshape(1, -1))
    bts_back = rad_to_bt(ds).values.flatten()

    assert np.all(np.diff(bts_back) > 0), "BT recuperada no monotonica"


def test_bt_attrs_preserved():
    """Los coeficientes Planck deben quedar en los attrs del DataArray de salida."""
    rad = np.array([[100.0]])
    ds = _make_synthetic_ds(rad)
    bt = rad_to_bt(ds)

    assert bt.attrs["units"] == "K"
    assert bt.attrs["fk1"] == FK1_B14
    assert bt.attrs["fk2"] == FK2_B14


if __name__ == "__main__":
    test_planck_roundtrip_known_temperatures()
    test_planck_negative_radiance_returns_nan()
    test_planck_monotonic()
    test_bt_attrs_preserved()
    print("OK — Planck tests passed")
