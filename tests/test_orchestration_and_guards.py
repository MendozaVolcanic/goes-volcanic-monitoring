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
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.process.brightness_temp import planck_rad_from_bt

# La escena sintética (bandas forward-modeladas, coeficientes Planck reales
# DISTINTOS por banda, perfil GFS y el fixture `synthetic_s3`) vive en
# tests/conftest.py — la comparten los tres retrievals de altura.
from conftest import (COEF11, COEF14, COEF15, PROFILE, SCAN_DT,  # noqa: F401
                      bt_from_rad as _bt_from_rad)


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
