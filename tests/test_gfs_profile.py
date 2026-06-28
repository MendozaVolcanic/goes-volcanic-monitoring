"""Tests Fase 2 — perfil vertical GFS T(z) + tropopausa + mapeo Teff→altura.

Lógica pura (parseo, tropopausa, interpolación) testeada determinística; el fetch
contra Open-Meteo hace ``pytest.skip`` si la API no responde.
"""
import functools
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))


@functools.lru_cache(maxsize=1)
def _openmeteo_ok() -> bool:
    try:
        import requests
        r = requests.get("https://api.open-meteo.com/v1/forecast",
                         params={"latitude": -36.8, "longitude": -71.4,
                                 "hourly": "temperature_500hPa",
                                 "forecast_days": 1, "models": "gfs_seamless"},
                         timeout=12)
        return r.status_code == 200
    except Exception:
        return False


# ── Parseo del perfil (sin red) ────────────────────────────────────────────

def test_parse_profile_celsius_to_kelvin_and_sorted():
    """_parse_profile: °C→K, ordenado por altura, descarta niveles con None."""
    from src.fetch.gfs_profile import _parse_profile

    hourly = {
        "temperature_850hPa": [10.0], "geopotential_height_850hPa": [1500.0],
        "temperature_500hPa": [-20.0], "geopotential_height_500hPa": [5600.0],
        "temperature_300hPa": [-45.0], "geopotential_height_300hPa": [9200.0],
        # nivel con dato faltante → se descarta
        "temperature_200hPa": [None], "geopotential_height_200hPa": [11800.0],
    }
    levels = _parse_profile(hourly, 0)
    assert [l["p_hPa"] for l in levels] == [850, 500, 300]   # ordenado por z asc
    assert abs(levels[0]["T_K"] - 283.15) < 1e-6             # 10°C → 283.15 K
    assert abs(levels[0]["z_m"] - 1500.0) < 1e-6
    assert all(l["T_K"] > 200 for l in levels)               # todo en K


def test_tropopause_is_cold_point():
    """_tropopause: punto frío entre 6 y 20 km."""
    from src.fetch.gfs_profile import _tropopause

    levels = [
        {"p_hPa": 850, "z_m": 1500.0, "T_K": 283.0},
        {"p_hPa": 500, "z_m": 5600.0, "T_K": 253.0},
        {"p_hPa": 300, "z_m": 9200.0, "T_K": 228.0},
        {"p_hPa": 200, "z_m": 11800.0, "T_K": 218.0},   # más frío (tropopausa)
        {"p_hPa": 100, "z_m": 16300.0, "T_K": 222.0},   # estratosfera (sube)
    ]
    trop = _tropopause(levels)
    assert trop["z_m"] == 11800.0 and trop["T_K"] == 218.0


# ── Mapeo Teff→altura (sin red) ────────────────────────────────────────────

def _synthetic_profile():
    levels = [
        {"p_hPa": 1000, "z_m": 100.0, "T_K": 288.0},     # superficie
        {"p_hPa": 850, "z_m": 1500.0, "T_K": 279.0},
        {"p_hPa": 500, "z_m": 5600.0, "T_K": 252.0},
        {"p_hPa": 300, "z_m": 9200.0, "T_K": 228.0},
        {"p_hPa": 200, "z_m": 12000.0, "T_K": 220.0},    # tropopausa
        {"p_hPa": 100, "z_m": 16300.0, "T_K": 224.0},    # estratosfera
    ]
    return {"levels": levels,
            "tropopause": {"p_hPa": 200, "z_m": 12000.0, "T_K": 220.0}}


def test_height_from_temp_interpolates():
    """height_from_temp: una BT en el rango troposférico interpola la altitud."""
    from src.fetch.gfs_profile import height_from_temp

    prof = _synthetic_profile()
    # T=240 K cae entre 300hPa(228K,9200m) y 500hPa(252K,5600m).
    res = height_from_temp(240.0, prof)
    assert res is not None and res["capped"] is None
    # interpolación lineal z vs T entre (252K,5600m) y (228K,9200m):
    # frac = (240-252)/(228-252)=0.5 → z = 5600 + 0.5*(9200-5600) = 7400 m
    assert abs(res["z_m"] - 7400.0) < 50.0, res


def test_height_from_temp_caps_at_tropopause_and_surface():
    """BT más fría que la tropopausa → cota en tropopausa; más cálida que la
    superficie → superficie."""
    from src.fetch.gfs_profile import height_from_temp

    prof = _synthetic_profile()
    cold = height_from_temp(210.0, prof)     # < 220 K (tropopausa)
    assert cold["capped"] == "tropopause" and abs(cold["z_m"] - 12000.0) < 1e-6
    warm = height_from_temp(295.0, prof)     # > 288 K (superficie)
    assert warm["capped"] == "surface" and abs(warm["z_m"] - 100.0) < 1e-6


def test_inversion_does_not_pull_altitude_aloft_and_vec_eq_scalar():
    """Con INVERSIÓN térmica (capa cálida a ~3 km), una BT cálida NO debe mapear
    aloft, y el vectorizado (altitudes_from_bt) debe coincidir con el escalar
    (height_from_temp). Pinea el fix del bug argsort(T). (review jun 2026)
    """
    import numpy as np

    from src.fetch.gfs_profile import (_monotone_tropo_branch, altitudes_from_bt,
                                       height_from_temp)

    prof = {
        "levels": [
            {"p_hPa": 1000, "z_m": 100.0, "T_K": 288.0},
            {"p_hPa": 850, "z_m": 1500.0, "T_K": 282.0},
            {"p_hPa": 700, "z_m": 3000.0, "T_K": 285.0},   # INVERSIÓN (más cálido)
            {"p_hPa": 500, "z_m": 5600.0, "T_K": 252.0},
            {"p_hPa": 300, "z_m": 9200.0, "T_K": 228.0},
            {"p_hPa": 200, "z_m": 12000.0, "T_K": 220.0},  # tropopausa
        ],
        "tropopause": {"p_hPa": 200, "z_m": 12000.0, "T_K": 220.0},
    }
    # El nivel de inversión (285 K @ 3000 m) se descarta de la rama monótona.
    kept = _monotone_tropo_branch(prof)
    assert 3000.0 not in [l["z_m"] for l in kept], kept

    # BT=285 K (la T de la inversión) NO debe mapear a 3000 m: cae en la rama
    # baja (entre 288/100 m y 282/1500 m) → < 1500 m, cota inferior.
    s = height_from_temp(285.0, prof)
    assert s["z_m"] < 1500.0, s
    # vectorizado == escalar (misma función subyacente).
    v = altitudes_from_bt(np.array([285.0, 240.0, 210.0]), prof)
    assert abs(v[0] - s["z_m"]) < 1e-6
    assert abs(v[1] - height_from_temp(240.0, prof)["z_m"]) < 1e-6  # ~7400 m
    assert abs(v[2] - 12000.0) < 1e-6                                # cap tropopausa


# ── Fetch en vivo (skip si no hay red) ─────────────────────────────────────

@pytest.mark.skipif(not _openmeteo_ok(), reason="Open-Meteo no accesible")
def test_fetch_gfs_profile_live():
    from src.fetch.gfs_profile import fetch_gfs_profile

    prof = fetch_gfs_profile(-36.86, -71.38)   # Nevados de Chillán
    if prof is None:
        pytest.skip("Open-Meteo sin perfil en este momento")
    levels = prof["levels"]
    assert len(levels) >= 8, levels
    # ordenado por altura, T en K plausible, alturas crecientes
    zs = [l["z_m"] for l in levels]
    assert zs == sorted(zs)
    assert all(180.0 < l["T_K"] < 320.0 for l in levels)
    # tropopausa detectada en rango físico
    if prof.get("tropopause"):
        assert 6000 <= prof["tropopause"]["z_m"] <= 20000


if __name__ == "__main__":
    test_parse_profile_celsius_to_kelvin_and_sorted()
    test_tropopause_is_cold_point()
    test_height_from_temp_interpolates()
    test_height_from_temp_caps_at_tropopause_and_surface()
    print("OK — tests puros GFS profile passed")
