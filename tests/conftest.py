"""Escena sintética compartida por los tests de orquestación de altura.

Vive acá (y no dentro de un test) porque los TRES retrievals de altura
—Wen-Rose, BT-matching y ACHA— ahora comparten la misma adquisición
(``src/process/scene.py``), así que los tres se prueban contra la misma escena
con verdad conocida: suelo cálido de 292 K + un bloque de pluma forward-modelada
(Tc=228 K, transmisividad t11=0.35, β=0.7).

Los coeficientes Planck son REALES y DISTINTOS por banda: sin eso, intercambiar
dos bandas pasaría la suite (era el gap T1 del audit jul-2026).
"""
import contextlib
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pytest
import xarray as xr

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.process.brightness_temp import planck_rad_from_bt

COEF11 = (13634.3, 1493.5, 0.40000, 0.99910)   # C11 8.4 µm
COEF14 = (8510.22, 1286.67, 0.07635, 0.99964)  # C14 11.2 µm
COEF15 = (6454.62, 1173.03, 0.16640, 0.99931)  # C15 12.3 µm
COEFS = {11: COEF11, 14: COEF14, 15: COEF15}

SCAN_DT = datetime(2026, 7, 1, 12, 0, tzinfo=timezone.utc)
N = 24                                  # escena 24×24 px
PLUME = (slice(8, 16), slice(8, 16))    # bloque de pluma 8×8 = 64 px

PROFILE = {
    "levels": [
        {"p_hPa": 1000, "z_m": 100.0, "T_K": 295.0},
        {"p_hPa": 850, "z_m": 1500.0, "T_K": 285.0},
        {"p_hPa": 500, "z_m": 5600.0, "T_K": 252.0},
        {"p_hPa": 300, "z_m": 9200.0, "T_K": 228.0},
        {"p_hPa": 200, "z_m": 12000.0, "T_K": 220.0},
        {"p_hPa": 100, "z_m": 16300.0, "T_K": 224.0},
    ],
    "tropopause": {"p_hPa": 200, "z_m": 12000.0, "T_K": 220.0},
    "skin_temp_K": 293.0,
    "valid_time": "2026-07-01T12:00",
}


def bt_from_rad(rad, coef):
    fk1, fk2, bc1, bc2 = coef
    t_eff = fk2 / np.log(fk1 / np.asarray(rad, dtype="float64") + 1.0)
    return (t_eff - bc1) / bc2


def forward_bt(tc, t, ts, coef):
    """BT observada de pluma semitransparente: I = (1−t)B(Tc) + t·B(Ts)."""
    i = (1 - t) * planck_rad_from_bt(tc, *coef) + t * planck_rad_from_bt(ts, *coef)
    return float(bt_from_rad(i, coef))


def scene_bts():
    """Escena sintética con verdad conocida: suelo 292 K + pluma (Tc=228,
    t11=0.35, β=0.7 = el central del solver)."""
    tc_true, t11, ts, beta = 228.0, 0.35, 292.0, 0.7
    t12 = t11 ** beta
    bt = {b: np.full((N, N), ts) for b in (11, 14, 15)}
    bt[14][PLUME] = forward_bt(tc_true, t11, ts, COEF14)
    bt[15][PLUME] = forward_bt(tc_true, t12, ts, COEF15)
    # C11 (8.4 µm): 10 K más fría que C14 sobre la pluma para pasar el test
    # tri-espectral: (bt11−bt14)+(bt15−bt14) = (−10)+(+7.55) = −2.45 < 0.
    bt[11][PLUME] = bt[14][PLUME] - 10.0
    return bt, tc_true


def band_ds(bt2d, coef):
    """Dataset L1b mínimo que rad_to_bt/planck_coefs esperan."""
    fk1, fk2, bc1, bc2 = coef
    rad = planck_rad_from_bt(bt2d, *coef)
    return xr.Dataset({
        "Rad": (("y", "x"), rad),
        "planck_fk1": ((), fk1), "planck_fk2": ((), fk2),
        "planck_bc1": ((), bc1), "planck_bc2": ((), bc2),
        "goes_imager_projection": ((), 0, {
            "longitude_of_projection_origin": -75.0,
            "perspective_point_height": 35786023.0}),
    }, coords={"x": np.arange(N, dtype="float64"),
               "y": np.arange(N, dtype="float64")})


def scene_latlon():
    """Grilla lat/lon 2D centrada en Láscar, del tamaño de la escena."""
    from src.volcanos import get_volcano
    v = get_volcano("Lascar")
    return np.meshgrid(
        np.linspace(v.lat + 0.4, v.lat - 0.4, N),
        np.linspace(v.lon - 0.4, v.lon + 0.4, N), indexing="ij")


@pytest.fixture()
def synthetic_s3(monkeypatch):
    """Mockea S3 (download/open/scan), geos y GFS con la escena sintética."""
    import src.fetch.gfs_profile as gfs_profile
    import src.fetch.goes_acha as goes_acha
    import src.fetch.goes_s3 as goes_s3

    bts, tc_true = scene_bts()
    datasets = {b: band_ds(bts[b], COEFS[b]) for b in (11, 14, 15)}

    def fake_download(dt, band, **kw):
        return None if band not in datasets else Path(f"OR_fake_C{band:02d}.nc")

    @contextlib.contextmanager
    def fake_open(path):
        band = int(str(path.name)[9:11])
        yield datasets[band]

    lat2d, lon2d = scene_latlon()

    monkeypatch.setattr(goes_s3, "download_band_at", fake_download)
    monkeypatch.setattr(goes_s3, "open_band", fake_open)
    monkeypatch.setattr(goes_s3, "_scan_start", lambda name: SCAN_DT)
    monkeypatch.setattr(goes_acha, "_geos_index_bbox",
                        lambda x, y, bounds, **kw: (0, N, 0, N))
    monkeypatch.setattr(goes_acha, "_window_latlon",
                        lambda xw, yw, **kw: (lat2d, lon2d))
    monkeypatch.setattr(gfs_profile, "fetch_gfs_profile",
                        lambda lat, lon, dt=None: PROFILE)
    return tc_true
