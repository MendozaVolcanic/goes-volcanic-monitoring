"""Tests del contrato de anidamiento ABI + super-bbox del pipeline hi-res.

Este es el test que faltaba (hallazgo critico del review): la logica mas
load-bearing de TODO el pan-sharpening —que el indice 1km k mapea a 0.5km
2k,2k+1 (EXACTAMENTE 2×), que 2km mapea via //4, y que el modo color recorta
sub-regiones (no full-disk)— no estaba bloqueada por ningun test. Una
regresion (cambiar //4 por //2, soltar el *2) saldria verde y solo se veria
como ghosting sutil en la imagen, invisible para CI.

Layer 1: aritmetica pura del anidamiento (rapida, documenta el contrato).
Layer 2: integracion con datasets sinteticos ANIDADOS en memoria
(monkeypatch de download_band/open_band) -> corre build_hires_for_scopes y
verifica que la salida color es EXACTAMENTE 2× el recorte 1km (=> 0.5 km/px),
y que dia=visible_color / noche=ir_pseudo.
"""

import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pytest
import xarray as xr

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.process.geo import bbox_indices, get_lat_lon

CLAT, CLON = -39.42, -71.93  # Villarrica
H = 35786023.0
PROJ_ATTRS = {
    "longitude_of_projection_origin": -75.0,
    "perspective_point_height": H,
    "semi_major_axis": 6378137.0,
    "semi_minor_axis": 6356752.31414,
}


# ── Layer 1: aritmetica pura del anidamiento ──────────────────────────

def test_nesting_arithmetic_contract():
    """1km idx k <-> 0.5km 2k,2k+1 ; 2km via //4. Con super-bbox mult-de-4."""
    for r0, r1 in [(0, 8), (4, 16), (12, 40), (100, 240)]:
        assert r0 % 4 == 0 and r1 % 4 == 0, "super-bbox debe ser mult de 4"
        # 1km sub-region = super // 2
        a1, b1 = r0 // 2, r1 // 2
        # pan derivado como 2× los indices 1km cubre EXACTAMENTE el rango 0.5km
        assert 2 * a1 == r0 and 2 * b1 == r1
        assert (2 * b1 - 2 * a1) == (r1 - r0)        # pan = 2× filas 1km
        # 2km sub-region = super // 4 ; 1km = 2× conteo 2km
        a2, b2 = r0 // 4, r1 // 4
        assert (b1 - a1) == 2 * (b2 - a2)


# ── Layer 2: integracion con datasets sinteticos anidados ─────────────

def _geos_center_rad():
    """(x,y) en radianes del subpunto geos para (CLON, CLAT)."""
    from pyproj import Proj
    p = Proj(proj="geos", lon_0=-75.0, h=H, ellps="GRS80", sweep="x")
    xm, ym = p(CLON, CLAT)
    return xm / H, ym / H


def _make_band_ds(x_rad, y_rad, rad, *, visible):
    """Dataset L1b sintetico minimal (Rad + coords + proj + coef)."""
    dvars = {
        "Rad": (("y", "x"), rad.astype(np.float32)),
        "goes_imager_projection": xr.DataArray(0, attrs=PROJ_ATTRS),
    }
    if visible:
        dvars["kappa0"] = 1.0  # reflectance = Rad * 1
    else:
        # Planck para BT ~200-300 K desde Rad positiva.
        dvars.update({"planck_fk1": 2.0e4, "planck_fk2": 1.3e3,
                      "planck_bc1": 0.5, "planck_bc2": 0.9995})
    return xr.Dataset(dvars, coords={"x": x_rad, "y": y_rad})


def _build_nested_bands(n1km=200):
    """Construye B2(0.5km), B1/B3(1km), B13(2km) en grilla EXACTAMENTE anidada.

    y_1km[k] = mean(y_05[2k], y_05[2k+1]); y_2km idem desde 1km. B1/B3 = block-
    mean de B2 (1km fisicamente consistente). Devuelve {band: ds}.
    """
    xc, yc = _geos_center_rad()
    d05 = 1.4e-5  # ~0.5 km nominal en rad
    n05 = 2 * n1km
    # 0.5km arrays centrados en el volcan
    x05 = xc + (np.arange(n05) - n05 // 2) * d05
    y05 = yc + (np.arange(n05) - n05 // 2) * d05
    # 1km = block-mean de pares ; 2km = block-mean de 1km
    x1 = x05.reshape(n1km, 2).mean(1)
    y1 = y05.reshape(n1km, 2).mean(1)
    x2 = x1.reshape(n1km // 2, 2).mean(1)
    y2 = y1.reshape(n1km // 2, 2).mean(1)

    # Campo B2 0.5km: gradiente + tablero fino (algo que pan-sharpenear), [0,1]
    yy, xx = np.mgrid[0:n05, 0:n05]
    rad2 = (0.30 + 0.4 * xx / n05 + 0.05 * ((xx + yy) % 2)).clip(0, 1)
    # B1/B3 = block-mean 2x de B2 (1km consistente)
    rad1 = rad2.reshape(n1km, 2, n1km, 2).mean((1, 3))
    # B13 2km: radiancia positiva moderada -> BT ~ templado
    rad13 = np.full((n1km // 2, n1km // 2), 80.0, dtype=np.float32)

    return {
        1: _make_band_ds(x1, y1, rad1, visible=True),
        2: _make_band_ds(x05, y05, rad2, visible=True),
        3: _make_band_ds(x1, y1, rad1, visible=True),
        13: _make_band_ds(x2, y2, rad13, visible=False),
    }


@pytest.fixture
def patched_pipeline(monkeypatch):
    """Monkeypatch download_band/open_band para servir las bandas sinteticas."""
    pytest.importorskip("pyproj")
    import src.process.hires_pipeline as HP
    bands = _build_nested_bands()
    monkeypatch.setattr(HP, "download_band", lambda dt, b, use_cache=True: f"band{b}")
    monkeypatch.setattr(HP, "open_band", lambda path: bands[int(str(path)[4:])])
    return HP, bands


def test_color_output_is_exactly_2x_the_1km_crop(patched_pipeline):
    """DIA color: la imagen es EXACTAMENTE 2× el recorte 1km => 0.5 km/px.

    ESTE es el lock del contrato de co-registro: si alguien suelta el *2 o
    cambia //2 por algo distinto, esta igualdad de shape se rompe.
    """
    HP, bands = patched_pipeline
    day_dt = datetime(2026, 6, 15, 16, 30, tzinfo=timezone.utc)  # sol ~27° Villarrica
    scopes = {"villarrica": {"lat": CLAT, "lon": CLON, "name": "Villarrica"}}
    imgs, meta = HP.build_hires_for_scopes(day_dt, scopes, radius_deg=0.5,
                                           mode="color")
    arr = imgs["villarrica"]
    assert meta["villarrica"]["render"] == "visible_color", meta
    assert arr is not None and arr.ndim == 3 and arr.shape[2] == 3
    assert arr.dtype == np.uint8

    # Shape esperado del recorte 1km para el mismo bbox (grilla 1km de B1).
    lat1, lon1 = get_lat_lon(bands[1])
    bounds = {"lat_min": CLAT - 0.5, "lat_max": CLAT + 0.5,
              "lon_min": CLON - 0.5, "lon_max": CLON + 0.5}
    idx = bbox_indices(lat1, lon1, bounds)
    assert idx is not None
    r0, r1, c0, c1 = idx
    assert arr.shape[:2] == (2 * (r1 - r0), 2 * (c1 - c0)), (
        arr.shape, (r1 - r0, c1 - c0))


def test_color_mode_night_falls_to_ir(patched_pipeline):
    """NOCHE color: cae a IR pseudo-color (2 km), no a visible."""
    HP, _ = patched_pipeline
    night_dt = datetime(2026, 6, 15, 6, 0, tzinfo=timezone.utc)  # sol < 0 Villarrica
    scopes = {"villarrica": {"lat": CLAT, "lon": CLON, "name": "Villarrica"}}
    imgs, meta = HP.build_hires_for_scopes(night_dt, scopes, radius_deg=0.5,
                                           mode="color")
    assert meta["villarrica"]["render"] == "ir_pseudo", meta
    assert imgs["villarrica"] is not None


def test_mono_mode_still_05km(patched_pipeline):
    """mono_05km sigue produciendo imagen 0.5km de dia (no se rompio en el rewrite)."""
    HP, bands = patched_pipeline
    day_dt = datetime(2026, 6, 15, 16, 30, tzinfo=timezone.utc)
    scopes = {"villarrica": {"lat": CLAT, "lon": CLON, "name": "Villarrica"}}
    imgs, meta = HP.build_hires_for_scopes(day_dt, scopes, radius_deg=0.5,
                                           mode="mono_05km")
    assert meta["villarrica"]["render"] == "visible_mono", meta
    arr = imgs["villarrica"]
    assert arr is not None and arr.shape[2] == 3
    # mono es 0.5km nativo: ~2× el recorte 1km del mismo bbox
    lat1, lon1 = get_lat_lon(bands[1])
    bounds = {"lat_min": CLAT - 0.5, "lat_max": CLAT + 0.5,
              "lon_min": CLON - 0.5, "lon_max": CLON + 0.5}
    r0, r1, c0, c1 = bbox_indices(lat1, lon1, bounds)
    assert abs(arr.shape[0] - 2 * (r1 - r0)) <= 2  # 0.5km (tolera even-crop)


if __name__ == "__main__":
    test_nesting_arithmetic_contract()
    print("OK — nesting arithmetic")
