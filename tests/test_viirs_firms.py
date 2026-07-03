"""Tests del fetcher de hot spots térmicos VIIRS 375 m vía NASA FIRMS.

FIRMS = Fire Information for Resource Management System: publica las anomalías
térmicas de MODIS/VIIRS como PUNTOS (lat,lon,FRP,T_brillo,confianza). Detecta
cualquier fuente de calor intensa, incluidos hot spots volcánicos → análogo polar
(375 m, ~2×/día) de nuestros hot spots FDCF de GOES (geo, 2 km, 10 min). Útil para
volcanes australes sin monitoreo GOES dedicado.

El parseo del CSV, el área y la URL son PUROS (sin red ni MAP_KEY). El llamado real
requiere un MAP_KEY gratis (env `FIRMS_MAP_KEY`) → hace skip si no está.
"""
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.fetch.viirs_firms import (_bbox_to_area, _build_area_url,
                                    _parse_firms_csv, fetch_viirs_firms_hotspots)

_SAMPLE_CSV = (
    "latitude,longitude,bright_ti4,scan,track,acq_date,acq_time,satellite,"
    "instrument,confidence,version,bright_ti5,frp,daynight\n"
    "-45.903,-72.968,331.2,0.38,0.36,2026-07-02,0618,N,VIIRS,n,2.0NRT,295.1,7.4,D\n"
    "-45.910,-72.960,367.0,0.38,0.36,2026-07-02,0618,N,VIIRS,h,2.0NRT,301.0,52.1,D\n"
)


def test_bbox_to_area_order_wsen():
    """FIRMS 'area' va en orden West,South,East,North (lon_min,lat_min,lon_max,lat_max)."""
    b = {"lat_min": -46.5, "lat_max": -45.3, "lon_min": -73.6, "lon_max": -72.4}
    assert _bbox_to_area(b) == "-73.6,-46.5,-72.4,-45.3"


def test_parse_firms_csv_basic():
    """Parsea el CSV VIIRS a dicts con los campos clave y tipos correctos."""
    rows = _parse_firms_csv(_SAMPLE_CSV)
    assert len(rows) == 2
    r = rows[1]
    assert abs(r["lat"] - (-45.910)) < 1e-9 and abs(r["lon"] - (-72.960)) < 1e-9
    assert r["frp_mw"] == 52.1
    assert r["bright_ti4_k"] == 367.0 and r["bright_ti5_k"] == 301.0
    assert r["confidence"] == "h"
    assert r["acq_date"] == "2026-07-02" and r["daynight"] == "D"
    assert r["satellite"] == "N"


def test_parse_firms_csv_header_only_is_empty():
    """CSV solo con header (sin detecciones) → lista vacía, no error."""
    header = _SAMPLE_CSV.splitlines()[0] + "\n"
    assert _parse_firms_csv(header) == []


def test_parse_firms_csv_non_csv_is_empty():
    """Respuesta que no es CSV (ej. 'Invalid MAP_KEY') → lista vacía."""
    assert _parse_firms_csv("Invalid MAP_KEY.") == []
    assert _parse_firms_csv("") == []


def test_parse_firms_csv_skips_malformed_rows():
    """Filas con columnas faltantes o no numéricas se saltan sin romper."""
    bad = (_SAMPLE_CSV.splitlines()[0] + "\n"
           + "-45.9,-72.9,xxx,0.3,0.3,2026-07-02,0618,N,VIIRS,n,2.0NRT,295,NaNval,D\n"
           + "sololat\n")
    rows = _parse_firms_csv(bad)
    assert rows == []      # la fila con FRP no-numérico y la corta se descartan


def test_build_area_url_structure():
    """La URL sigue /api/area/csv/{key}/{source}/{area}/{days}[/{date}]."""
    b = {"lat_min": -46.5, "lat_max": -45.3, "lon_min": -73.6, "lon_max": -72.4}
    url = _build_area_url("KEY123", "VIIRS_SNPP_NRT", b, days=2, when="2026-07-01")
    assert url.endswith("/api/area/csv/KEY123/VIIRS_SNPP_NRT/-73.6,-46.5,-72.4,-45.3/2/2026-07-01")
    url2 = _build_area_url("KEY123", "VIIRS_NOAA20_NRT", b, days=1)
    assert url2.endswith("/VIIRS_NOAA20_NRT/-73.6,-46.5,-72.4,-45.3/1")


def test_fetch_returns_none_without_map_key(monkeypatch):
    """Sin MAP_KEY (ni arg ni env) → None con log claro, sin tocar la red."""
    monkeypatch.delenv("FIRMS_MAP_KEY", raising=False)
    b = {"lat_min": -46.5, "lat_max": -45.3, "lon_min": -73.6, "lon_max": -72.4}
    assert fetch_viirs_firms_hotspots(b) is None


@pytest.mark.skipif(not os.environ.get("FIRMS_MAP_KEY"),
                    reason="FIRMS_MAP_KEY no seteado (clave gratis de NASA FIRMS)")
def test_fetch_viirs_firms_live():
    """Con MAP_KEY real: consulta un área amplia de Chile y devuelve lista (posible
    vacía) de hot spots bien formados."""
    b = {"lat_min": -56.0, "lat_max": -17.0, "lon_min": -76.0, "lon_max": -66.0}
    hs = fetch_viirs_firms_hotspots(b, days=1)
    assert hs is not None and isinstance(hs, list)
    for h in hs[:5]:
        assert "lat" in h and "lon" in h and "frp_mw" in h


if __name__ == "__main__":
    test_bbox_to_area_order_wsen()
    test_parse_firms_csv_basic()
    test_parse_firms_csv_header_only_is_empty()
    test_parse_firms_csv_non_csv_is_empty()
    test_parse_firms_csv_skips_malformed_rows()
    test_build_area_url_structure()
    print("OK — viirs_firms puro")
