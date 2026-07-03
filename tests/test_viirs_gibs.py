"""Tests del fetcher de imagen VIIRS pre-georreferenciada (NASA GIBS WMS).

Por qué (geología → pipeline): para volcanes SIN monitoreo GOES dedicado (varios
patagónicos), VIIRS aporta imagen 375 m + anomalías térmicas ~2×/día. GIBS ya
reproyecta los gránulos polares → pedimos por bbox+fecha con un WMS GetMap, sin
tocar la geometría polar cruda. Es un complemento, NO se mezcla con la cadena ABI.

La construcción de bbox/URL es PURA (sin red). El GetMap real hace skip si no hay
red (como los demás fetchers).
"""
import sys
from datetime import date
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.fetch.viirs_gibs import (LAYERS, _bbox, _default_date, _getmap_params,
                                   _coverage_frac)


def test_bbox_axis_order_lat_lon():
    """WMS 1.3.0 EPSG:4326 usa orden (minLat,minLon,maxLat,maxLon)."""
    b = _bbox(-45.9, -72.97, 0.6)
    assert b["lat_min"] == -46.5 and b["lat_max"] == -45.3
    assert round(b["lon_min"], 2) == -73.57 and round(b["lon_max"], 2) == -72.37


def test_getmap_params_bbox_string():
    """El BBOX del GetMap va en orden lat,lon (no lon,lat) para EPSG:4326 v1.3.0."""
    b = _bbox(-45.9, -72.97, 0.6)
    p = _getmap_params("truecolor", b, "2026-07-01", size=512)
    assert p["REQUEST"] == "GetMap" and p["VERSION"] == "1.3.0"
    assert p["CRS"] == "EPSG:4326"
    assert p["LAYERS"] == LAYERS["truecolor"]
    assert p["BBOX"] == "-46.5,-73.57,-45.3,-72.37"
    assert p["WIDTH"] == 512 and p["HEIGHT"] == 512
    assert p["TIME"] == "2026-07-01"


def test_getmap_unknown_layer_raises():
    b = _bbox(-45.9, -72.97, 0.6)
    with pytest.raises(KeyError):
        _getmap_params("no_existe", b, "2026-07-01")


def test_default_date_is_a_date_string():
    """Default = ayer UTC (hoy puede no estar compuesto aún). Formato YYYY-MM-DD."""
    d = _default_date()
    assert len(d) == 10 and d[4] == "-" and d[7] == "-"
    date.fromisoformat(d)   # parsea → válido


def test_coverage_frac():
    """Fracción de píxeles no-negros (0 = sin pasada / overlay vacío; 1 = cubierto)."""
    import numpy as np
    black = np.zeros((4, 4, 3), dtype="uint8")
    assert _coverage_frac(black) == 0.0
    full = np.full((4, 4, 3), 100, dtype="uint8")
    assert _coverage_frac(full) == 1.0
    half = black.copy(); half[:2] = 100
    assert abs(_coverage_frac(half) - 0.5) < 1e-9


def test_layers_presets_exist():
    """Los presets clave están definidos y apuntan a capas VIIRS de GIBS."""
    for k in ("truecolor", "truecolor_snpp", "thermal", "daynight"):
        assert k in LAYERS and "VIIRS" in LAYERS[k]


# ── Contrato del dato real (RED, skip si no hay) ───────────────────────────

def _net_ok() -> bool:
    try:
        import requests
        r = requests.get("https://gibs.earthdata.nasa.gov/wms/epsg4326/best/wms.cgi",
                         params={"SERVICE": "WMS", "REQUEST": "GetCapabilities"},
                         timeout=15)
        return r.status_code == 200
    except Exception:
        return False


@pytest.mark.skipif(not _net_ok(), reason="GIBS no accesible")
def test_fetch_viirs_image_patagonia():
    """Bajar True Color de un volcán patagónico (Hudson): devuelve imagen RGB
    georreferenciada con las bounds pedidas."""
    from src.fetch.viirs_gibs import fetch_viirs_image
    r = fetch_viirs_image(-45.90, -72.97, layer="truecolor", pad_deg=0.6, size=256)
    if r is None:
        pytest.skip("GIBS sin respuesta")
    img = r["image"]
    assert img.ndim == 3 and img.shape[2] == 3
    assert img.shape[0] == 256 and img.shape[1] == 256
    assert r["bounds"]["lat_min"] < -45.9 < r["bounds"]["lat_max"]
    assert 0.0 <= r["coverage_frac"] <= 1.0
    assert r["source"].startswith("VIIRS")


if __name__ == "__main__":
    test_bbox_axis_order_lat_lon()
    test_getmap_params_bbox_string()
    test_getmap_unknown_layer_raises()
    test_default_date_is_a_date_string()
    test_coverage_frac()
    test_layers_presets_exist()
    print("OK — viirs_gibs puro")
