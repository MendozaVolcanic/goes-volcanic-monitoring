"""Tests Fase 0 — altura del tope de pluma INDICATIVA (ACHA NOAA + máscara ceniza).

Cubre las dos piezas nuevas:
- ``src.fetch.goes_acha``: fetcher del producto NOAA ``ABI-L2-ACHA2KMF``
  (Cloud Top Height 2 km), recorte geos a bounds y filtro DQF.
- ``src.process.acha_plume_height``: intersección de la altura ACHA con NUESTRA
  máscara de ceniza tri-espectral, y el resumen del tope (p95/max).

Los tests de RED (s3fs anon contra ``noaa-goes19``) hacen ``pytest.skip`` si S3
no está accesible — así nunca rompen la suite en un runner offline, pero
verifican el contrato real cuando hay red (como pide el plan Fase 0). La lógica
pura (index-bbox geos, resumen del tope) se testea SIN red, determinística.
"""

import functools
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

# Grilla ABI fixed-grid 2 km real (verificada contra el NetCDF: x crece W→E,
# y DECRECE N→S, span ±0.15184399 rad, 5424 px). La usamos en los tests sin red
# para ejercitar el index-bbox geos con la misma geometría que el dato real.
_ABI_HALF = 0.15184399
_ABI_N = 5424


def _abi_xy():
    x = np.linspace(-_ABI_HALF, _ABI_HALF, _ABI_N).astype("float32")
    y = np.linspace(_ABI_HALF, -_ABI_HALF, _ABI_N).astype("float32")  # N→S
    return x, y


@functools.lru_cache(maxsize=1)
def _s3_ok() -> bool:
    """¿S3 anónimo accesible? (para skip de los tests de red).

    Cacheado: `skipif` lo evalúa una vez por decorador (en colección), así que
    sin cache haría 2 round-trips de red en CADA `pytest` — incluso al correr
    solo los tests puros. Con lru_cache es 1 sola llamada por sesión.
    """
    try:
        import s3fs
        s3 = s3fs.S3FileSystem(anon=True)
        s3.ls("noaa-goes19/ABI-L2-ACHA2KMF/", detail=False)
        return True
    except Exception:
        return False


# ── Lógica pura: index-bbox geos (sin red) ────────────────────────────────

def test_geos_index_bbox_villarrica_window():
    """_geos_index_bbox: una caja ±0.75° en torno a Villarrica debe dar una
    ventana CHICA (no el disco entero) que, reproyectada, CONTIENE la caja."""
    from src.fetch.goes_acha import _geos_index_bbox, _window_latlon

    x, y = _abi_xy()
    vlat, vlon = -39.42, -71.93   # Villarrica
    pad = 0.75
    bounds = {"lat_min": vlat - pad, "lat_max": vlat + pad,
              "lon_min": vlon - pad, "lon_max": vlon + pad}

    win = _geos_index_bbox(x, y, bounds, sat_lon=-75.0, H=35786023.0)
    assert win is not None
    y0, y1, x0, x1 = win
    # Ventana acotada (no el disco completo) y bien ordenada.
    assert 0 <= y0 < y1 <= _ABI_N
    assert 0 <= x0 < x1 <= _ABI_N
    assert (y1 - y0) < 400 and (x1 - x0) < 400, (y1 - y0, x1 - x0)

    # Reproyectada, la ventana debe cubrir el bbox pedido (con margen de 1 px).
    lat, lon = _window_latlon(x[x0:x1], y[y0:y1], sat_lon=-75.0, H=35786023.0)
    assert np.nanmin(lat) <= bounds["lat_min"] and np.nanmax(lat) >= bounds["lat_max"]
    assert np.nanmin(lon) <= bounds["lon_min"] and np.nanmax(lon) >= bounds["lon_max"]
    # El centro del volcán cae dentro del rango lat/lon de la ventana.
    assert np.nanmin(lat) <= vlat <= np.nanmax(lat)
    assert np.nanmin(lon) <= vlon <= np.nanmax(lon)


def test_geos_index_bbox_off_disk_returns_none():
    """Un bbox fuera del disco GOES (otro hemisferio) → None, no una ventana."""
    from src.fetch.goes_acha import _geos_index_bbox

    x, y = _abi_xy()
    bounds = {"lat_min": 40.0, "lat_max": 45.0, "lon_min": 100.0, "lon_max": 105.0}
    assert _geos_index_bbox(x, y, bounds, sat_lon=-75.0, H=35786023.0) is None


def test_geos_index_bbox_on_disk_off_array_returns_none():
    """bbox ON-disk pero fuera del rango de los arrays x/y dados → None.

    Pinea la 2ª rama de None (xsel/ysel vacío), distinta del off-disk. Villarrica
    (lon −71.93, al ESTE del subsatélite −75) proyecta a x>0; si solo damos la
    mitad OESTE del grid (x<0), el bbox cae on-disk pero off-array."""
    from src.fetch.goes_acha import _geos_index_bbox

    x, y = _abi_xy()
    x_west = x[x < 0]   # solo media oeste del fixed grid
    bounds = {"lat_min": -40.17, "lat_max": -38.67,
              "lon_min": -72.68, "lon_max": -71.18}   # Villarrica ±0.75°
    assert _geos_index_bbox(x_west, y, bounds, sat_lon=-75.0, H=35786023.0) is None


# ── Lógica pura: resumen del tope (sin red) ────────────────────────────────

def test_plume_top_stats_basic():
    """_plume_top_stats: p95/max/conteo SOLO sobre píxeles de ceniza con HT
    finita; en metros de entrada, km de salida."""
    from src.process.acha_plume_height import _plume_top_stats

    # HT en metros (5 px). Máscara marca 4; el 2º píxel de ceniza tiene HT NaN
    # (ACHA sin retrieval) → no debe contar.
    height_m = np.array([[1000.0, np.nan, 8000.0, 9000.0, 12000.0]])
    mask = np.array([[True, True, True, True, False]])  # último NO es ceniza

    s = _plume_top_stats(height_m, mask, percentile=95)
    assert s["mask_px"] == 3                      # px 0,2,3 (el 1 es NaN, el 4 no-ceniza)
    assert abs(s["top_max_km"] - 9.0) < 1e-9      # max de {1,8,9} km
    # p95 entre 1,8,9 km — cerca del máximo, > 8 km.
    assert 8.0 < s["top_km"] <= 9.0
    # field_km: NaN salvo en píxeles de ceniza con HT válida.
    assert np.isnan(s["field_km"][0, 1]) and np.isnan(s["field_km"][0, 4])
    assert abs(s["field_km"][0, 2] - 8.0) < 1e-9


def test_plume_top_stats_empty_mask():
    """Sin píxeles de ceniza válidos → mask_px=0 y tope None (no excepción)."""
    from src.process.acha_plume_height import _plume_top_stats

    height_m = np.array([[5000.0, 6000.0]])
    mask = np.array([[False, False]])
    s = _plume_top_stats(height_m, mask, percentile=95)
    assert s["mask_px"] == 0
    assert s["top_km"] is None and s["top_max_km"] is None
    assert s["field_km"].shape == height_m.shape
    assert np.isnan(s["field_km"]).all()


def test_plume_top_stats_single_pixel():
    """1 solo píxel de ceniza (caso de inicio de pluma): p95 == max == ese valor."""
    from src.process.acha_plume_height import _plume_top_stats

    s = _plume_top_stats(np.array([[7000.0]]), np.array([[True]]), percentile=95)
    assert s["mask_px"] == 1
    assert abs(s["top_km"] - 7.0) < 1e-9 and abs(s["top_max_km"] - 7.0) < 1e-9


def test_plume_top_stats_shape_mismatch_crops():
    """Guard defensivo: shapes distintos → recorta a la mín común sin romper."""
    from src.process.acha_plume_height import _plume_top_stats

    height = np.array([[1000.0, 2000.0, 3000.0, 4000.0]])  # (1,4)
    mask = np.array([[True, True, True]])                   # (1,3)
    s = _plume_top_stats(height, mask, percentile=95)
    assert s["field_km"].shape == (1, 3)                    # recortado
    assert s["mask_px"] == 3
    assert abs(s["top_max_km"] - 3.0) < 1e-9


def test_apply_quality_dqf_and_range():
    """_apply_quality: pin del contrato científico (DQF keep {0,1,4} + clamp).

    El opaque (4) se CONSERVA (fiable para plumas densas); attempted (2) y bad
    (3) se descartan; alturas fuera de [0, 20000] m → NaN. Sin red.
    """
    from src.fetch.goes_acha import _apply_quality

    ht = np.array([[100.0, 5000.0, 9000.0, 30000.0, -50.0, 8000.0]])
    dqf = np.array([[0, 2, 4, 0, 1, 3]])
    out = _apply_quality(ht, dqf, keep_dqf={0, 1, 4})
    assert out[0, 0] == 100.0           # DQF 0 (good), en rango → conserva
    assert np.isnan(out[0, 1])          # DQF 2 (attempted) → descarta
    assert out[0, 2] == 9000.0          # DQF 4 (opaque) → CONSERVA
    assert np.isnan(out[0, 3])          # 30000 m > 20000 → clamp
    assert np.isnan(out[0, 4])          # -50 m < 0 → clamp
    assert np.isnan(out[0, 5])          # DQF 3 (bad) → descarta


def test_plume_top_height_unknown_volcano_no_data():
    """Volcán inexistente → status 'no_data' ANTES de tocar la red (pura).

    Pinea que un fallo de identificación NO se confunde con 'no_plume' (que para
    un SDA de alerta significaría 'sin pluma', semánticamente opuesto)."""
    from src.process.acha_plume_height import plume_top_height

    r = plume_top_height(datetime.now(timezone.utc), "NoExisteVolcanXYZ")
    assert r["status"] == "no_data", r


# ── Contrato del dato real (RED, skip si no hay red) ───────────────────────

@pytest.mark.skipif(not _s3_ok(), reason="S3 noaa-goes19 no accesible")
def test_acha_granule_contract():
    """Bajar un gránulo ACHA2KMF reciente y verificar el contrato del dato:
    HT existe, dims 5424×5424, units 'm', rango físico 0–18000 m."""
    from datetime import timedelta

    import s3fs
    import xarray as xr

    from src.fetch.goes_acha import S3_BUCKET, S3_PRODUCT

    s3 = s3fs.S3FileSystem(anon=True)
    now = datetime.now(timezone.utc)
    keys = []
    for h in range(8):
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
        pytest.skip("sin gránulos ACHA2KMF en las últimas 8 h")

    with s3.open(keys[-1], "rb") as f:
        ds = xr.open_dataset(f, engine="h5netcdf")
        assert "HT" in ds.data_vars, "falta variable HT"
        ht = ds["HT"]
        assert ht.dims == ("y", "x")
        assert ht.shape == (5424, 5424), ht.shape
        assert ht.attrs.get("units") == "m"
        assert "DQF" in ds.data_vars
        vals = ht.values
        finite = np.isfinite(vals)
        assert finite.any(), "HT sin píxeles finitos"
        assert 0.0 <= np.nanmin(vals) and np.nanmax(vals) <= 18000.0, (
            np.nanmin(vals), np.nanmax(vals))


@pytest.mark.skipif(not _s3_ok(), reason="S3 noaa-goes19 no accesible")
def test_fetch_acha_height_at_crops_to_bounds():
    """fetch_acha_height_at recorta a un bbox de volcán y devuelve la ventana
    georreferenciada con HT en metros y DQF aplicado."""
    from src.fetch.goes_acha import fetch_acha_height_at

    vlat, vlon = -39.42, -71.93   # Villarrica
    pad = 0.75
    bounds = {"lat_min": vlat - pad, "lat_max": vlat + pad,
              "lon_min": vlon - pad, "lon_max": vlon + pad}

    res = fetch_acha_height_at(datetime.now(timezone.utc), bounds)
    if res is None:
        pytest.skip("ACHA sin gránulo reciente accesible")

    h = res["height_m"]
    assert h.ndim == 2 and h.size > 0
    # Ventana recortada: mucho más chica que el disco completo.
    assert h.shape[0] < 400 and h.shape[1] < 400, h.shape
    assert res["lat"].shape == h.shape and res["lon"].shape == h.shape
    # lat/lon de la ventana cubren el centro del volcán.
    assert np.nanmin(res["lat"]) <= vlat <= np.nanmax(res["lat"])
    assert np.nanmin(res["lon"]) <= vlon <= np.nanmax(res["lon"])
    # HT válida (no-NaN) dentro de rango físico de nube (0–18 km).
    finite = h[np.isfinite(h)]
    if finite.size:
        assert finite.min() >= 0.0 and finite.max() <= 18000.0
    assert isinstance(res["scan_dt"], datetime)


if __name__ == "__main__":
    test_geos_index_bbox_villarrica_window()
    test_geos_index_bbox_off_disk_returns_none()
    test_geos_index_bbox_on_disk_off_array_returns_none()
    test_plume_top_stats_basic()
    test_plume_top_stats_empty_mask()
    test_plume_top_stats_single_pixel()
    test_plume_top_stats_shape_mismatch_crops()
    test_apply_quality_dqf_and_range()
    test_plume_top_height_unknown_volcano_no_data()
    print("OK — tests puros ACHA passed (los de red corren con pytest)")
