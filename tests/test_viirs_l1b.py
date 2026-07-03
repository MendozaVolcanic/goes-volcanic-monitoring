"""Tests del fetcher de gránulos VIIRS L1b (parseo de nombre + emparejamiento).

El parseo del token de gránulo VIIRS (``.A{YYYYDDD}.{HHMM}.``) y el emparejamiento
L1b↔GEO son PUROS (sin red ni credenciales). La descarga real requiere earthaccess
+ credenciales Earthdata → los tests de red hacen skip.
"""
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.fetch.viirs_l1b import (MOD_PRODUCTS, _atoken_dt, _atoken_key)


def test_atoken_dt_parses_granule_name():
    """Token .A2024228.0618. → 2024-08-15 06:18 UTC (día del año 228 de 2024)."""
    name = "VNP02MOD.A2024228.0618.002.2024228123456.nc"
    dt = _atoken_dt(name)
    assert dt == datetime(2024, 8, 15, 6, 18, tzinfo=timezone.utc)


def test_atoken_key_matches_l1b_and_geo():
    """L1b y GEO del mismo scan comparten el token A → misma clave de emparejamiento."""
    l1b = "VNP02MOD.A2026183.0618.002.2026183200000.nc"
    geo = "VNP03MOD.A2026183.0618.002.2026183200500.nc"
    assert _atoken_key(l1b) == _atoken_key(geo) == "2026183.0618"


def test_atoken_none_on_bad_name():
    assert _atoken_dt("sin_token.nc") is None
    assert _atoken_key("sin_token.nc") is None


def test_atoken_dt_leap_day():
    """Día 60 de 2024 (bisiesto) = 29-feb."""
    assert _atoken_dt("VJ102MOD.A2024060.1200.002.nc") == datetime(
        2024, 2, 29, 12, 0, tzinfo=timezone.utc)


def test_mod_products_cover_three_satellites():
    """Los tres VIIRS (SNPP/NOAA20/NOAA21) tienen su par L1b/GEO M-band."""
    assert set(MOD_PRODUCTS) == {"SNPP", "NOAA20", "NOAA21"}
    for l1b, geo in MOD_PRODUCTS.values():
        assert "02MOD" in l1b and "03MOD" in geo


if __name__ == "__main__":
    test_atoken_dt_parses_granule_name()
    test_atoken_key_matches_l1b_and_geo()
    test_atoken_none_on_bad_name()
    test_atoken_dt_leap_day()
    test_mod_products_cover_three_satellites()
    print("OK — viirs_l1b puro")
