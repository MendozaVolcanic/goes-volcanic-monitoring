"""Tests de ORQUESTACIÓN (Ola 4 del audit jul-2026) — sin red, con monkeypatch.

Cierra el gap T1 del audit: `wen_rose_top_height` (~300 líneas) solo se testeaba
con volcán inexistente ("intercambiar los coeficientes de banda pasaría la suite").
Acá se construye una ESCENA SINTÉTICA completa (suelo cálido + pluma forward-
modelada con verdad conocida) servida por mocks de S3/GFS, y se verifica el
resultado end-to-end. También los guards del árbitro de viento (T2, nacidos del
fallo real de Láscar) y los helpers puros (_revert_unreliable, _top_stats,
beta_composition con máscara de producción).
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

# Coeficientes Planck ABI reales, DISTINTOS por banda (sin eso el test no
# detectaría un swap de bandas — el punto del gap T1).
COEF11 = (13634.3, 1493.5, 0.40000, 0.99910)   # C11 8.4 µm
COEF14 = (8510.22, 1286.67, 0.07635, 0.99964)  # C14 11.2 µm
COEF15 = (6454.62, 1173.03, 0.16640, 0.99931)  # C15 12.3 µm
COEFS = {11: COEF11, 14: COEF14, 15: COEF15}

SCAN_DT = datetime(2026, 7, 1, 12, 0, tzinfo=timezone.utc)
N = 24                       # escena 24×24 px
PLUME = (slice(8, 16), slice(8, 16))   # bloque de pluma 8×8 = 64 px

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


def _bt_from_rad(rad, coef):
    fk1, fk2, bc1, bc2 = coef
    t_eff = fk2 / np.log(fk1 / np.asarray(rad, dtype="float64") + 1.0)
    return (t_eff - bc1) / bc2


def _forward_bt(tc, t, ts, coef):
    """BT observada de pluma semitransparente: I = (1−t)B(Tc) + t·B(Ts)."""
    i = (1 - t) * planck_rad_from_bt(tc, *coef) + t * planck_rad_from_bt(ts, *coef)
    return float(_bt_from_rad(i, coef))


def _scene_bts():
    """Escena sintética con verdad conocida: suelo 292 K + pluma (Tc=228,
    t11=0.35, β=0.7 = el central del solver)."""
    tc_true, t11, ts, beta = 228.0, 0.35, 292.0, 0.7
    t12 = t11 ** beta
    bt = {b: np.full((N, N), ts) for b in (11, 14, 15)}
    bt[14][PLUME] = _forward_bt(tc_true, t11, ts, COEF14)
    bt[15][PLUME] = _forward_bt(tc_true, t12, ts, COEF15)
    # C11 (8.4 µm): 10 K más fría que C14 sobre la pluma para pasar el test
    # tri-espectral: (bt11−bt14)+(bt15−bt14) = (−10)+(+7.55) = −2.45 < 0.
    bt[11][PLUME] = bt[14][PLUME] - 10.0
    return bt, tc_true


def _band_ds(bt2d, coef):
    """Dataset L1b mínimo que rad_to_bt/_coefs esperan."""
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


@pytest.fixture()
def synthetic_s3(monkeypatch):
    """Mockea S3 (download/open/scan), geos y GFS con la escena sintética."""
    import src.fetch.goes_acha as goes_acha
    import src.fetch.gfs_profile as gfs_profile
    import src.fetch.goes_s3 as goes_s3

    bts, tc_true = _scene_bts()
    datasets = {b: _band_ds(bts[b], COEFS[b]) for b in (11, 14, 15)}

    def fake_download(dt, band, **kw):
        return None if band not in datasets else Path(f"OR_fake_C{band:02d}.nc")

    @contextlib.contextmanager
    def fake_open(path):
        band = int(str(path.name)[9:11])
        yield datasets[band]

    from src.volcanos import get_volcano
    v = get_volcano("Lascar")
    lat2d, lon2d = np.meshgrid(
        np.linspace(v.lat + 0.4, v.lat - 0.4, N),
        np.linspace(v.lon - 0.4, v.lon + 0.4, N), indexing="ij")

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


def test_wen_rose_orchestration_end_to_end(synthetic_s3):
    """EL test del gap T1: escena sintética completa → la orquestación detecta la
    pluma, corrige por semitransparencia y reporta el paquete de honestidad."""
    from src.process.wen_rose_height import wen_rose_top_height

    r = wen_rose_top_height(SCAN_DT, "Lascar", radius_deg=0.6)
    assert r["status"] == "ok", r.get("reason", r["status"])
    # detectó la pluma (64 px del bloque)
    assert r["mask_px"] == 64, r["mask_px"]
    # corrigió por semitransparencia: Wen-Rose SUBE sobre la cota
    assert r["n_corrected"] > 0
    assert r["top_km"] > r["top_bt_matching_km"], (r["top_km"],
                                                   r["top_bt_matching_km"])
    # el Tc verdadero (228 K → ~9.2 km en el perfil) queda DENTRO de la banda β
    assert r["top_km_lo"] <= 9.3 and r["top_km_hi"] >= 9.0, \
        (r["top_km_lo"], r["top_km_hi"])
    # Ts vino del cielo claro de la escena (~292 K)
    assert r["ts_source"] == "cielo claro (escena)"
    assert abs(r["ts_k"] - 292.0) < 1.5, r["ts_k"]
    # paquete de honestidad presente
    assert r["confidence"] in ("media", "baja", "muy baja")
    assert r["co2_verdict"] is None          # sin C16 en el mock
    assert isinstance(r["flags"], list)
    assert r["composition"] is not None and r["composition"]["n_px"] == 64


def test_wen_rose_orchestration_detects_band_swap(synthetic_s3, monkeypatch):
    """Anti-regresión del gap T1 textual ('swap de coefs pasaría la suite'):
    si C14 y C15 llegan INTERCAMBIADAS, el BTD se invierte y NO debe haber
    detección de ceniza (no_plume) — la suite ahora lo nota."""
    import src.fetch.goes_s3 as goes_s3
    from src.process.wen_rose_height import wen_rose_top_height

    real_open = goes_s3.open_band

    @contextlib.contextmanager
    def swapped_open(path):
        name = str(path.name)
        swapped = name.replace("C14", "Cxx").replace("C15", "C14").replace(
            "Cxx", "C15")
        with real_open(Path(swapped)) as ds:
            yield ds

    monkeypatch.setattr(goes_s3, "open_band", swapped_open)
    r = wen_rose_top_height(SCAN_DT, "Lascar", radius_deg=0.6)
    assert r["status"] == "no_plume", r["status"]


# ── Guards del árbitro de viento (T2 — nacidos del fallo real de Láscar) ────

def _wind_mask(lat_c, lon_c):
    """(mask, lat, lon, scan_dt) con centroide en (lat_c, lon_c)."""
    lat = np.full((2, 2), lat_c)
    lon = np.full((2, 2), lon_c)
    return (np.ones((2, 2), dtype=bool), lat, lon, SCAN_DT)


def test_wind_guard_max_advection(monkeypatch):
    """Centroide que salta 1° en 10 min (185 m/s, imposible) → no_data."""
    import src.process.wind_shear_height as ws
    from datetime import timedelta

    cur = _wind_mask(-23.0, -67.7)
    prev = (np.ones((2, 2), dtype=bool), np.full((2, 2), -24.0),
            np.full((2, 2), -67.7), SCAN_DT - timedelta(minutes=10))
    monkeypatch.setattr(ws, "_ash_mask_at",
                        lambda dt, v, r: cur if dt >= SCAN_DT else prev)
    r = ws.wind_shear_top_height(SCAN_DT, "Lascar", radius_deg=0.6)
    assert r["status"] == "no_data" and "implausible" in r["reason"], r


def test_wind_guard_old_profile(monkeypatch):
    """Perfil de viento a 6 h del scan (fuera de ventana) → no_data."""
    import src.fetch.gfs_profile as gfs
    import src.process.wind_shear_height as ws
    from datetime import timedelta

    cur = _wind_mask(-23.0, -67.7)
    prev = (np.ones((2, 2), dtype=bool), np.full((2, 2), -23.108),
            np.full((2, 2), -67.7), SCAN_DT - timedelta(minutes=10))  # ~20 m/s
    monkeypatch.setattr(ws, "_ash_mask_at",
                        lambda dt, v, r: cur if dt >= SCAN_DT else prev)
    monkeypatch.setattr(gfs, "fetch_gfs_wind_profile",
                        lambda lat, lon, dt=None: {
                            "levels": [{"z_m": z, "u_ms": 10.0, "v_ms": 0.0}
                                       for z in (2000, 6000, 10000)],
                            "valid_time": "2026-07-01T06:00"})   # 6 h off
    r = ws.wind_shear_top_height(SCAN_DT, "Lascar", radius_deg=0.6)
    assert r["status"] == "no_data" and "ventana" in r["reason"], r


def test_wind_guard_unparseable_valid_time(monkeypatch):
    """valid_time no parseable → rechaza (NO asume perfil fresco). Fix C2."""
    import src.fetch.gfs_profile as gfs
    import src.process.wind_shear_height as ws
    from datetime import timedelta

    cur = _wind_mask(-23.0, -67.7)
    prev = (np.ones((2, 2), dtype=bool), np.full((2, 2), -23.108),
            np.full((2, 2), -67.7), SCAN_DT - timedelta(minutes=10))
    monkeypatch.setattr(ws, "_ash_mask_at",
                        lambda dt, v, r: cur if dt >= SCAN_DT else prev)
    monkeypatch.setattr(gfs, "fetch_gfs_wind_profile",
                        lambda lat, lon, dt=None: {
                            "levels": [{"z_m": z, "u_ms": 10.0, "v_ms": 0.0}
                                       for z in (2000, 6000, 10000)],
                            "valid_time": "garbage"})
    r = ws.wind_shear_top_height(SCAN_DT, "Lascar", radius_deg=0.6)
    assert r["status"] == "no_data" and "parseable" in r["reason"], r


# ── Helpers puros de wen_rose (T4/T5) ────────────────────────────────────────

def test_revert_unreliable_three_modes():
    """(a) mal-condicionado → revierte a BT11; (b) runaway a tropopausa →
    revierte; (c) confiable en troposfera media → conserva el Tc corregido."""
    from src.process.wen_rose_height import _revert_unreliable

    trop = PROFILE["tropopause"]
    tc = np.array([240.0, 219.0, 240.0])       # 219 K < tropopausa → runaway
    bt11 = np.array([260.0, 260.0, 260.0])
    wc = np.array([False, True, True])
    tc_out, reliable = _revert_unreliable(tc, bt11, wc, PROFILE, trop)
    assert not reliable[0] and tc_out[0] == 260.0      # (a)
    assert not reliable[1] and tc_out[1] == 260.0      # (b) saturó en trop
    assert reliable[2] and tc_out[2] == 240.0          # (c)


def test_top_stats_capped_semantics():
    """Los píxeles 'capped' en la tropopausa no fijan el tope; todos capped →
    devuelve la tropopausa con all_capped=True."""
    from src.process.wen_rose_height import _top_stats

    trop = PROFILE["tropopause"]
    alt = np.array([8000.0, 9000.0, 11999.5])          # el 3º pegado a la trop
    field = alt / 1000.0
    valid = np.ones(3, dtype=bool)
    top, top_max, n_capped, all_capped = _top_stats(field, valid, alt, trop)
    assert n_capped == 1 and not all_capped
    assert top_max == 9.0                               # el capped no fija el máx
    alt2 = np.full(3, 11999.9)
    top2, _, n2, all2 = _top_stats(alt2 / 1000, valid, alt2, trop)
    assert all2 and n2 == 3 and top2 == 12.0


def test_beta_composition_production_mask():
    """T6: beta_composition con la ash_mask de PRODUCCIÓN (subconjunto): la
    clasificación sale de los píxeles enmascarados, no de toda la escena."""
    from src.process.beta_ratios import beta_composition

    t_ref, clr = 210.0, 290.0

    def synth(eps, coef):
        b_ref = planck_rad_from_bt(t_ref, *coef)
        r_clr = planck_rad_from_bt(clr, *coef)
        return float(_bt_from_rad(eps * b_ref + (1 - eps) * r_clr, coef))

    e11 = 0.70
    ln11 = np.log(1 - e11)
    # bloque A = ceniza (β 0.564/0.705), bloque B = hielo (1.07/0.836)
    bt11 = np.full((2, 2), np.nan)
    bt14 = np.full((2, 2), np.nan)
    bt15 = np.full((2, 2), np.nan)
    for (i, j), (b12, b85) in {(0, 0): (0.564, 0.705),
                               (1, 1): (1.07, 0.836)}.items():
        bt14[i, j] = synth(e11, COEF14)
        bt15[i, j] = synth(1 - np.exp(b12 * ln11), COEF15)
        bt11[i, j] = synth(1 - np.exp(b85 * ln11), COEF11)
    mask_ash = np.zeros((2, 2), dtype=bool); mask_ash[0, 0] = True
    mask_ice = np.zeros((2, 2), dtype=bool); mask_ice[1, 1] = True
    r_a = beta_composition(bt11, bt14, bt15, t_ref, clr, clr, clr,
                           COEF11, COEF14, COEF15, ash_mask=mask_ash)
    r_i = beta_composition(bt11, bt14, bt15, t_ref, clr, clr, clr,
                           COEF11, COEF14, COEF15, ash_mask=mask_ice)
    assert r_a["composition"] == "ceniza" and r_a["n_px"] == 1
    assert r_i["composition"] == "hielo" and r_i["is_ash"] is False
