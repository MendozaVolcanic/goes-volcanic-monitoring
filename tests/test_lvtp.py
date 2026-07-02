"""Tests del fetcher LVTPF — perfil T(z) del PROPIO GOES-19 (ABI-L2-LVTPF).

Por qué existe (geología → pipeline): el mapeo Teff→altura de la pluma necesita
un perfil vertical T(z). Hoy lo da GFS (Open-Meteo), que validamos contra
radiosondas (RMSE 0.3–1.1 K en 5–12 km). LVTPF es la MISMA cantidad medida por
el propio satélite (101 niveles, clear-sky), y sirve como **perfil alternativo /
cross-check independiente** del GFS.

Piezas PURAS (sin red, deterministas):
- ``_std_atm_height``   : altura geopotencial de la atmósfera estándar (anclaje).
- ``_hypsometric_heights``: T(p) → z(p) por integración hipsométrica (LVTPF NO
  trae altura geopotencial, hay que derivarla — es la física nueva del módulo).
- ``_clear_sky_profile`` : mediana del perfil sobre píxeles de cielo claro
  (DQF_Overall==0 & DQF_Retrieval==0), ignorando los píxeles bajo pluma (DQF 4).
- ``_build_profile``     : ensambla el dict con la MISMA forma que
  ``fetch_gfs_profile`` (drop-in para ``altitudes_from_bt``/``height_from_temp``).

Los tests de RED (s3fs anon contra ``noaa-goes19``) hacen ``pytest.skip`` si S3
no está accesible.
"""

import functools
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))


@functools.lru_cache(maxsize=1)
def _s3_ok() -> bool:
    """¿S3 anónimo + producto LVTPF accesible? (para skip de los tests de red)."""
    try:
        import s3fs
        s3 = s3fs.S3FileSystem(anon=True)
        s3.ls("noaa-goes19/ABI-L2-LVTPF/", detail=False)
        return True
    except Exception:
        return False


# ── Atmósfera estándar (anclaje del absoluto AMSL) ─────────────────────────

def test_std_atm_height_known_points():
    """US Std Atmosphere 1976 (troposfera): valores canónicos.

    A 1013.25 hPa → 0 m; a ~226.32 hPa → ~11000 m (tope de la troposfera std).
    Estos dos puntos fijan la fórmula usada como ancla del integrador.
    """
    from src.fetch.goes_lvtp import _std_atm_height

    assert abs(_std_atm_height(1013.25)) < 1.0            # nivel del mar
    assert abs(_std_atm_height(226.32) - 11000.0) < 60.0  # tropopausa std


def test_hypsometric_isothermal_matches_barometric():
    """Integración hipsométrica de una atmósfera ISOTERMA = fórmula barométrica.

    Con T constante, el espesor entre dos niveles es Δz = (R_d·T/g)·ln(p1/p2).
    Verifica que las DIFERENCIAS de altura entre niveles coinciden con esa
    analítica (independiente del anclaje, que solo desplaza el absoluto).
    """
    from src.fetch.goes_lvtp import _hypsometric_heights, _RD, _G0

    p = np.array([1000.0, 500.0, 250.0, 100.0])   # descendente = hacia arriba
    T = np.full_like(p, 250.0)
    z = _hypsometric_heights(p, T)

    assert np.all(np.diff(z) > 0)                  # monótona creciente
    for i in range(1, len(p)):
        exp = (_RD / _G0) * 250.0 * np.log(p[i - 1] / p[i])
        assert abs((z[i] - z[i - 1]) - exp) < 1.0, (i, z[i] - z[i - 1], exp)


def test_hypsometric_recovers_std_atmosphere():
    """Si alimentamos el PERFIL de temperatura de la atmósfera estándar, el
    integrador debe recuperar las alturas estándar (round-trip físico)."""
    from src.fetch.goes_lvtp import _hypsometric_heights, _std_atm_height

    # Perfil std troposférico: T = 288.15 - 0.0065·z_std(p).
    p = np.array([1000.0, 850.0, 700.0, 500.0, 300.0, 250.0])
    z_std = np.array([_std_atm_height(pi) for pi in p])
    T = 288.15 - 0.0065 * z_std

    z = _hypsometric_heights(p, T)
    # Recupera z_std dentro de ~50 m (error de discretización del trapecio).
    assert np.max(np.abs(z - z_std)) < 60.0, np.max(np.abs(z - z_std))


# ── Perfil de cielo claro (mediana sobre píxeles buenos) ───────────────────

def test_clear_sky_profile_uses_only_good_pixels():
    """_clear_sky_profile: mediana por nivel SOLO sobre píxeles clear-sky.

    Píxel bajo pluma (DQF_Overall==4) y píxel con retrieval no-convergente
    (DQF_Retrieval==1) se ignoran; el NaN de un nivel de un píxel bueno no
    contamina la mediana de ese nivel.
    """
    from src.fetch.goes_lvtp import _clear_sky_profile

    p = np.array([1000.0, 500.0, 250.0])
    lvt = np.full((2, 2, 3), np.nan)
    lvt[0, 0] = [280.0, 250.0, 220.0]   # clear bueno
    lvt[1, 1] = [282.0, 252.0, np.nan]  # clear bueno, pero NaN en 250 hPa
    lvt[0, 1] = [999.0, 999.0, 999.0]   # bajo pluma (se ignora entero)
    lvt[1, 0] = [270.0, 240.0, 210.0]   # retrieval malo (se ignora entero)

    dqf_o = np.array([[0, 4], [0, 0]])   # [0,1]=bajo pluma
    dqf_r = np.array([[0, 0], [1, 0]])   # [1,0]=no convergente

    p_out, t_out, n = _clear_sky_profile(lvt, dqf_o, dqf_r, p, min_clear=1)
    assert n == 2                                    # dos píxeles clear
    # 1000 hPa: mediana de {280,282}=281 ; 500: {250,252}=251 ; 250: solo 220.
    assert np.allclose(p_out, [1000.0, 500.0, 250.0])
    assert abs(t_out[0] - 281.0) < 1e-9
    assert abs(t_out[1] - 251.0) < 1e-9
    assert abs(t_out[2] - 220.0) < 1e-9


def test_clear_sky_profile_all_cloudy_returns_none():
    """Ventana enteramente bajo pluma / mala → no hay perfil (None)."""
    from src.fetch.goes_lvtp import _clear_sky_profile

    p = np.array([1000.0, 500.0, 250.0])
    lvt = np.full((2, 2, 3), 250.0)
    dqf_o = np.full((2, 2), 4)   # todos "insufficient clear pixels"
    dqf_r = np.zeros((2, 2))
    assert _clear_sky_profile(lvt, dqf_o, dqf_r, p) is None


def test_clear_sky_profile_drops_subsurface_and_junk_levels():
    """Niveles bajo MSL (p>1013.25) y T no-física se descartan del perfil."""
    from src.fetch.goes_lvtp import _clear_sky_profile

    p = np.array([1100.0, 1000.0, 500.0, 250.0])   # 1100 hPa = bajo MSL
    lvt = np.full((1, 1, 4), np.nan)
    lvt[0, 0] = [300.0, 280.0, 999.0, 220.0]        # 999 K = basura → fuera
    dqf_o = np.zeros((1, 1))
    dqf_r = np.zeros((1, 1))
    p_out, t_out, n = _clear_sky_profile(lvt, dqf_o, dqf_r, p, min_clear=1)
    assert n == 1
    assert 1100.0 not in p_out                       # sub-MSL descartado
    assert 500.0 not in p_out                         # T basura descartada
    assert list(p_out) == [1000.0, 250.0]


# ── Ensamblado del dict (misma forma que fetch_gfs_profile) ────────────────

def test_build_profile_shape_matches_gfs():
    """_build_profile: dict con levels[{p_hPa,z_m,T_K}] ordenados por z +
    tropopausa (punto frío, misma definición que GFS) → drop-in del mapeo."""
    from src.fetch.goes_lvtp import _build_profile

    p = np.array([1000.0, 850.0, 700.0, 500.0, 300.0, 250.0, 200.0, 150.0, 100.0])
    T = np.array([288.0, 280.0, 270.0, 252.0, 228.0, 222.0, 219.0, 220.0, 224.0])
    prof = _build_profile(p, T, lat=-39.4, lon=-71.9,
                          valid_time="2026-07-02T05:10", n_clear_px=42,
                          scan_dt=datetime(2026, 7, 2, 5, 10, tzinfo=timezone.utc),
                          source_key="k")
    assert prof is not None
    levels = prof["levels"]
    assert all({"p_hPa", "z_m", "T_K"} <= set(l) for l in levels)
    zs = [l["z_m"] for l in levels]
    assert zs == sorted(zs)                         # ordenados por altura
    assert prof["tropopause"] is not None
    # punto frío ~200 hPa (219 K) — la tropopausa cae ahí, no en 100 hPa.
    assert abs(prof["tropopause"]["T_K"] - 219.0) < 1e-6
    assert prof["source"].startswith("LVTPF")
    assert prof["skin_temp_K"] is None              # LVTPF no aporta skin-T


def test_build_profile_feeds_altitudes_from_bt():
    """El perfil LVTPF debe funcionar como entrada de altitudes_from_bt
    (contrato de interoperabilidad con la cadena de altura existente)."""
    from src.fetch.goes_lvtp import _build_profile
    from src.fetch.gfs_profile import altitudes_from_bt

    p = np.array([1000.0, 700.0, 500.0, 300.0, 250.0, 200.0, 150.0])
    T = np.array([288.0, 270.0, 252.0, 228.0, 222.0, 219.0, 221.0])
    prof = _build_profile(p, T, lat=-39.4, lon=-71.9,
                          valid_time="t", n_clear_px=10, scan_dt=None, source_key="k")
    # Una BT de 228 K (≈ 300 hPa) debe mapear a una altura troposférica plausible.
    z = float(altitudes_from_bt(np.array([228.0]), prof)[0])
    assert 7000.0 < z < 11000.0, z


# ── Contrato del dato real (RED) ───────────────────────────────────────────

@pytest.mark.skipif(not _s3_ok(), reason="S3 noaa-goes19/LVTPF no accesible")
def test_lvtp_granule_contract():
    """Bajar un gránulo LVTPF reciente y verificar el contrato: LVT(y,x,pressure)
    en K, 1086², 101 niveles, DQF_Overall con flag 0=good y 4=under-plume."""
    from datetime import timedelta

    import s3fs
    import xarray as xr

    from src.fetch.goes_lvtp import S3_BUCKET, S3_PRODUCT

    s3 = s3fs.S3FileSystem(anon=True)
    now = datetime.now(timezone.utc)
    keys = []
    for h in range(12):
        t = now - timedelta(hours=h)
        prefix = (f"{S3_BUCKET}/{S3_PRODUCT}/{t.year}/"
                  f"{t.timetuple().tm_yday:03d}/{t.hour:02d}/")
        try:
            ls = sorted(s3.ls(prefix))
        except FileNotFoundError:
            continue
        if ls:
            keys = ls
            break
    if not keys:
        pytest.skip("sin gránulos LVTPF en las últimas 12 h")

    with s3.open(keys[-1], "rb") as f:
        ds = xr.open_dataset(f, engine="h5netcdf")
        assert "LVT" in ds.data_vars
        assert ds["LVT"].dims == ("y", "x", "pressure")
        assert ds["LVT"].shape == (1086, 1086, 101), ds["LVT"].shape
        assert ds["LVT"].attrs.get("units") == "K"
        assert ds["pressure"].attrs.get("units") == "hPa"
        assert "DQF_Overall" in ds.data_vars and "DQF_Retrieval" in ds.data_vars


@pytest.mark.skipif(not _s3_ok(), reason="S3 noaa-goes19/LVTPF no accesible")
def test_fetch_lvtp_profile_villarrica():
    """fetch_lvtp_profile devuelve un perfil clear-sky físico sobre un volcán,
    con la misma forma que fetch_gfs_profile."""
    from src.fetch.goes_lvtp import fetch_lvtp_profile

    prof = fetch_lvtp_profile(-39.42, -71.93)   # Villarrica
    if prof is None:
        pytest.skip("LVTPF sin gránulo reciente / sin píxeles claros")

    levels = prof["levels"]
    assert len(levels) >= 5
    zs = [l["z_m"] for l in levels]
    assert zs == sorted(zs)
    Ts = [l["T_K"] for l in levels]
    assert all(150.0 < t < 330.0 for t in Ts)     # rango físico
    assert prof["tropopause"] is not None
    assert prof["n_clear_px"] >= 1
    assert prof["source"].startswith("LVTPF")


if __name__ == "__main__":
    test_std_atm_height_known_points()
    test_hypsometric_isothermal_matches_barometric()
    test_hypsometric_recovers_std_atmosphere()
    test_clear_sky_profile_uses_only_good_pixels()
    test_clear_sky_profile_all_cloudy_returns_none()
    test_clear_sky_profile_drops_subsurface_and_junk_levels()
    test_build_profile_shape_matches_gfs()
    test_build_profile_feeds_altitudes_from_bt()
    print("OK — tests puros LVTPF passed (los de red corren con pytest)")
