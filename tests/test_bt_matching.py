"""Tests Fase 3a — altura propia por BT-matching (BT11 → perfil GFS T(z)).

Lógica pura (vectorización BT→altitud) determinística; el camino con red
(bandas L1b + perfil GFS) hace skip si S3/Open-Meteo no responden.
"""
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))


def _synthetic_profile():
    return {
        "levels": [
            {"p_hPa": 1000, "z_m": 100.0, "T_K": 288.0},
            {"p_hPa": 850, "z_m": 1500.0, "T_K": 279.0},
            {"p_hPa": 500, "z_m": 5600.0, "T_K": 252.0},
            {"p_hPa": 300, "z_m": 9200.0, "T_K": 228.0},
            {"p_hPa": 200, "z_m": 12000.0, "T_K": 220.0},
            {"p_hPa": 100, "z_m": 16300.0, "T_K": 224.0},
        ],
        "tropopause": {"p_hPa": 200, "z_m": 12000.0, "T_K": 220.0},
    }


def test_altitudes_from_bt_vectorized():
    """altitudes_from_bt: interpola en troposfera, clampa fuera, NaN→NaN."""
    from src.process.bt_matching_height import altitudes_from_bt

    prof = _synthetic_profile()
    bt = np.array([[240.0, 210.0, 295.0, np.nan]])
    alt = altitudes_from_bt(bt, prof)
    # 240 K interpola a ~7400 m (entre 252K/5600m y 228K/9200m)
    assert abs(alt[0, 0] - 7400.0) < 60.0, alt
    # 210 K (< tropopausa 220) → cota tropopausa 12000 m
    assert abs(alt[0, 1] - 12000.0) < 1e-6
    # 295 K (> superficie 288) → cota superficie 100 m
    assert abs(alt[0, 2] - 100.0) < 1e-6
    # NaN → NaN
    assert np.isnan(alt[0, 3])


def test_altitudes_from_bt_empty_profile():
    """Perfil sin troposfera utilizable → todo NaN (no excepción)."""
    from src.process.bt_matching_height import altitudes_from_bt

    alt = altitudes_from_bt(np.array([[250.0]]),
                            {"levels": [{"p_hPa": 500, "z_m": 5600.0, "T_K": 252.0}],
                             "tropopause": None})
    assert np.isnan(alt).all()


def test_bt_matching_unknown_volcano_no_data():
    """Volcán inexistente → no_data sin tocar la red (short-circuit en get_volcano)."""
    from src.process.bt_matching_height import bt_matching_top_height

    r = bt_matching_top_height(datetime.now(timezone.utc), "NoExisteXYZ")
    assert r["status"] == "no_data"


if __name__ == "__main__":
    test_altitudes_from_bt_vectorized()
    test_altitudes_from_bt_empty_profile()
    print("OK — tests puros BT-matching passed")
