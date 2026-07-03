"""Tests de la calibración y recorte de bandas térmicas VIIRS 750 m (M15/M16).

Base del retrieval de altura VIIRS: leer las bandas M (11/12 µm) → temperatura de
brillo (LUT o Planck) y recortar el swath al bbox del volcán. Todo PURO/local: la
calibración se ejercita con un HDF5 sintético (LUT y scale/offset+Planck), sin red
ni gránulo real. Requiere h5py (ya es dep de Goes).
"""
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.process.viirs_bt import (BAND_LAMBDA_UM, crop_roi, planck_bt,
                                   read_mod_bt, read_mod_geo, roi_mask_bbox)

_C1, _C2 = 1.191042e8, 14388.0


def _planck_forward(bt_k, lam):
    """Radiancia espectral de un cuerpo negro a bt_k (inversa de planck_bt)."""
    return _C1 / (lam ** 5 * (np.exp(_C2 / (lam * bt_k)) - 1.0))


def test_planck_bt_roundtrip():
    """BT → radiancia (Planck fwd) → planck_bt debe recuperar la BT."""
    lam = BAND_LAMBDA_UM["M15"]
    for bt in (220.0, 260.0, 300.0):
        rad = _planck_forward(bt, lam)
        assert abs(planck_bt(rad, lam) - bt) < 1e-4, bt


def test_planck_bt_invalid_radiance_is_nan():
    """Radiancia ≤0 o NaN → NaN (no explota)."""
    lam = BAND_LAMBDA_UM["M16"]
    out = planck_bt(np.array([0.0, -1.0, np.nan, 5.0]), lam)
    assert np.isnan(out[0]) and np.isnan(out[1]) and np.isnan(out[2])
    assert np.isfinite(out[3])


def test_roi_mask_bbox_selects_center():
    """La máscara toma solo los píxeles dentro del bbox del volcán."""
    lat = np.array([[-23.0, -23.4, -23.8], [-24.2, -23.37, -22.9]])
    lon = np.array([[-67.0, -67.73, -68.5], [-67.73, -67.73, -67.73]])
    m = roi_mask_bbox(lat, lon, -23.37, -67.73, half_km=25.0)
    # ~25 km ≈ 0.225° lat. El centro exacto (-23.37,-67.73) entra; -22.9 (~52km) no.
    assert m[1, 1] == True
    assert m[1, 2] == False       # -22.9 está a >25 km en lat


def test_crop_roi_returns_pixels_in_bbox():
    """crop_roi devuelve arrays 1-D de los píxeles del bbox + n_px; None si vacío."""
    lat = np.array([[-23.37, -23.40], [-30.0, -30.0]])
    lon = np.array([[-67.73, -67.70], [-67.73, -67.73]])
    bt = {"M15": np.array([[260.0, 261.0], [270.0, 271.0]]),
          "M16": np.array([[258.0, 259.0], [268.0, 269.0]])}
    geo = {"lat": lat, "lon": lon, "sensor_zenith": np.zeros((2, 2))}
    r = crop_roi(bt, geo, -23.37, -67.73, half_km=25.0)
    assert r is not None and r["n_px"] == 2         # solo la fila superior
    assert set(np.round(r["M15"])) == {260.0, 261.0}
    assert r["lat"].shape == (2,)
    # Fuera del disco → None
    assert crop_roi(bt, geo, 40.0, 100.0, half_km=25.0) is None


# ── HDF5 sintético: ejercita LUT y Planck sin red ──────────────────────────

def _write_synth_l1b(path, *, use_lut: bool):
    """Escribe un VNP02MOD mínimo: M15/M16 con LUT o con scale/offset."""
    import h5py
    with h5py.File(path, "w") as f:
        obs = f.create_group("observation_data")
        # DN 4x4; un píxel de flag (65535) y el resto valores medios.
        for band, lam in (("M15", 10.763), ("M16", 12.013)):
            dn = np.array([[100, 200, 300, 65535],
                           [150, 250, 350, 400],
                           [120, 220, 320, 420],
                           [130, 230, 330, 430]], dtype="uint16")
            d = obs.create_dataset(band, data=dn)
            if use_lut:
                # LUT: mapea DN→BT lineal 180..330 K sobre 0..65535.
                lut = np.linspace(180.0, 330.0, 65536).astype("float32")
                obs.create_dataset(f"{band}_brightness_temperature_lut", data=lut)
            else:
                # scale/offset → radiancia; elegidos para dar BT plausible.
                rad0 = _planck_forward(260.0, lam)
                d.attrs["scale_factor"] = rad0 / 250.0
                d.attrs["add_offset"] = 0.0


def test_read_mod_bt_lut_path(tmp_path):
    """Camino LUT: DN→BT por tabla; el DN de flag (65535) → NaN."""
    p = tmp_path / "VNP02MOD.synth.nc"
    _write_synth_l1b(p, use_lut=True)
    bt = read_mod_bt(p, bands=("M15", "M16"))
    assert set(bt) == {"M15", "M16"}
    assert bt["M15"].shape == (4, 4)
    assert np.isnan(bt["M15"][0, 3])          # DN 65535 = flag → NaN
    # DN 100 → ~180+150*100/65535 ≈ 180.23 K (monótono creciente con DN)
    assert 180.0 <= bt["M15"][0, 0] <= 181.0
    assert bt["M15"][0, 1] > bt["M15"][0, 0]


def test_read_mod_bt_planck_path(tmp_path):
    """Camino scale/offset + Planck: sin LUT, calibra por radiancia."""
    p = tmp_path / "VNP02MOD.synth2.nc"
    _write_synth_l1b(p, use_lut=False)
    bt = read_mod_bt(p, bands=("M15",))
    assert "M15" in bt
    finite = bt["M15"][np.isfinite(bt["M15"])]
    assert finite.size > 0
    assert np.all((finite > 150.0) & (finite < 340.0))   # rango físico


def test_read_mod_geo(tmp_path):
    """read_mod_geo devuelve lat/lon con fill→NaN."""
    import h5py
    p = tmp_path / "VNP03MOD.synth.nc"
    with h5py.File(p, "w") as f:
        g = f.create_group("geolocation_data")
        g.create_dataset("latitude", data=np.array([[-23.37, -999.9]], dtype="float32"))
        g.create_dataset("longitude", data=np.array([[-67.73, -67.70]], dtype="float32"))
    geo = read_mod_geo(p)
    assert abs(geo["lat"][0, 0] - (-23.37)) < 1e-3
    assert np.isnan(geo["lat"][0, 1])          # -999.9 < -90 → NaN


if __name__ == "__main__":
    test_planck_bt_roundtrip()
    test_planck_bt_invalid_radiance_is_nan()
    test_roi_mask_bbox_selects_center()
    test_crop_roi_returns_pixels_in_bbox()
    print("OK — viirs_bt puro (los de HDF5 corren con pytest+tmp_path)")
