"""Tests Fase 3c — árbitro de altura por cizalla de viento (advección de la pluma
entre 2 scans → perfil de viento GFS).

El test central es un round-trip: sintetizo una pluma que se mueve exactamente al
viento de un nivel conocido, y verifico que el árbitro recupera esa altura. Lógica
pura y determinística; el camino con red no se testea (hace skip en integración).
"""
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.process.wind_shear_height import (advection_uv, plume_centroid,
                                           wind_implied_height)

M_PER_DEG = 111320.0


def _sheared_profile():
    """Perfil con cizalla vertical clara (viento distinto por altura)."""
    return [
        {"z_m": 2000.0, "u_ms": 5.0, "v_ms": 0.0},
        {"z_m": 6000.0, "u_ms": 20.0, "v_ms": 5.0},
        {"z_m": 10000.0, "u_ms": -10.0, "v_ms": 25.0},
        {"z_m": 14000.0, "u_ms": 0.0, "v_ms": 40.0},
    ]


def test_plume_centroid():
    """Centroide = media de lat/lon sobre la máscara; vacía → None."""
    lat = np.array([[-38.0, -38.0], [-39.0, -39.0]])
    lon = np.array([[-72.0, -71.0], [-72.0, -71.0]])
    mask = np.array([[False, True], [False, True]])   # los 2 de lon=-71
    c = plume_centroid(mask, lat, lon)
    assert c is not None and abs(c[0] - (-38.5)) < 1e-9 and abs(c[1] - (-71.0)) < 1e-9
    assert plume_centroid(np.zeros((2, 2), bool), lat, lon) is None


def test_advection_uv_recovers_velocity():
    """Desplazamiento conocido → (u,v) correcto."""
    lat0, lon0 = -38.0, -72.0
    u, v = -10.0, 25.0    # m/s
    dt_s = 600.0
    dx, dy = u * dt_s, v * dt_s          # metros
    lat1 = lat0 + dy / M_PER_DEG
    lon1 = lon0 + dx / (M_PER_DEG * math.cos(math.radians(lat0)))
    ur, vr = advection_uv(lat0, lon0, lat1, lon1, dt_s)
    assert abs(ur - u) < 0.05 and abs(vr - v) < 0.05, (ur, vr)


def test_wind_implied_height_roundtrip():
    """La pluma se mueve al viento de 10 km → el árbitro devuelve 10 km."""
    prof = _sheared_profile()
    r = wind_implied_height(-10.0, 25.0, prof)
    assert r is not None
    assert abs(r["z_m"] - 10000.0) < 1e-6, r
    assert r["discriminates"] is True
    assert r["mismatch_ms"] < 0.1


def test_wind_implied_height_no_shear():
    """Viento uniforme (sin cizalla) → no discrimina."""
    flat = [{"z_m": z, "u_ms": 10.0, "v_ms": 0.0}
            for z in (2000, 6000, 10000, 14000)]
    r = wind_implied_height(10.0, 0.0, flat)
    assert r is not None and r["discriminates"] is False
    assert r["shear_ms"] < 1e-6


def test_wind_implied_height_ambiguity_band():
    """La banda [z_lo,z_hi] cubre los niveles con mismatch cercano al mínimo."""
    prof = _sheared_profile()
    # advección entre el nivel de 6 km y 10 km → mejor match uno, banda incluye vecinos
    r = wind_implied_height(5.0, 15.0, prof)
    assert r is not None
    assert r["z_lo_m"] <= r["z_m"] <= r["z_hi_m"]


def test_full_roundtrip_advection_to_height():
    """End-to-end puro: genero un desplazamiento con el viento de 6 km, y el árbitro
    (advección → altura) devuelve 6 km."""
    prof = _sheared_profile()
    lvl = prof[1]                       # 6000 m, viento (20, 5)
    lat0, lon0 = -37.0, -71.5
    dt_s = 600.0
    lat1 = lat0 + (lvl["v_ms"] * dt_s) / M_PER_DEG
    lon1 = lon0 + (lvl["u_ms"] * dt_s) / (M_PER_DEG * math.cos(math.radians(lat0)))
    u, v = advection_uv(lat0, lon0, lat1, lon1, dt_s)
    r = wind_implied_height(u, v, prof)
    assert abs(r["z_m"] - 6000.0) < 1e-6, (u, v, r)
    assert r["discriminates"]


def test_wind_shear_unknown_volcano_no_data():
    """Volcán inexistente → no_data sin red."""
    from src.process.wind_shear_height import wind_shear_top_height
    r = wind_shear_top_height(datetime.now(timezone.utc), "NoExisteXYZ")
    assert r["status"] == "no_data"


if __name__ == "__main__":
    test_plume_centroid()
    test_advection_uv_recovers_velocity()
    test_wind_implied_height_roundtrip()
    test_wind_implied_height_no_shear()
    test_wind_implied_height_ambiguity_band()
    test_full_roundtrip_advection_to_height()
    print("OK — tests puros wind-shear passed")
