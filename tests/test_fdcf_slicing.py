"""Tests del recorte de FDCF por bbox (ola 2 del audit ago-2026).

Por qué importa (el "por qué" antes que el "cómo"): el FDCF full-disk son
cuatro variables de 5424×5424 (~380 MB de churn, ~15 s por scan). Los seis
consumidores del dashboard piden un bbox chico —un volcán, una zona— pero el
lector materializaba el disco entero igual. `frp_timeline.fetch_scan_sliced` ya
demostraba el recorte ~15× más rápido, pero solo lo usaba la timeline.

Lo que se prueba acá es lo único que importa para poder compartir el camino
rápido: **recortar no cambia el resultado**. Los hotspots que salen del
sub-bloque tienen que ser exactamente los que salían del disco entero filtrado
por el mismo bbox.
"""
import sys
from pathlib import Path

import numpy as np
import pytest
import xarray as xr

sys.path.insert(0, str(Path(__file__).parent.parent))

pytest.importorskip("pyproj")

H = 35786023.0
SAT_LON = -75.0
GRID = 400                       # grilla sintética 400×400 sobre Chile

CHILE = {"lat_min": -56, "lat_max": -17, "lon_min": -76, "lon_max": -66}
# Dos hotspots con FRP distinto para pinear también el orden de salida.
VILLARRICA = (-39.42, -71.93, 10, 120.0)     # lat, lon, Mask, FRP MW
LASCAR = (-23.37, -67.73, 14, 30.0)          # baja confianza (Mask 14)


def _proj():
    from pyproj import Proj
    return Proj(proj="geos", lon_0=SAT_LON, h=H, ellps="GRS80", sweep="x")


def _fdcf_ds():
    """NetCDF FDCF sintético: grilla geos que cubre Chile con 2 píxeles calientes.

    Fondo Mask=50 (no-fire) y Power=NaN, como un scan real sin incendios.
    El eje y va descendente, igual que en los archivos ABI.
    """
    p = _proj()
    lons = [CHILE["lon_min"], CHILE["lon_max"]] * 2
    lats = [CHILE["lat_min"]] * 2 + [CHILE["lat_max"]] * 2
    xm, ym = p(lons, lats)
    x_rad = np.linspace(min(xm) / H - 0.002, max(xm) / H + 0.002, GRID)
    y_rad = np.linspace(max(ym) / H + 0.002, min(ym) / H - 0.002, GRID)

    mask = np.full((GRID, GRID), 50, dtype="uint8")
    power = np.full((GRID, GRID), np.nan)
    temp = np.full((GRID, GRID), np.nan)
    area = np.full((GRID, GRID), np.nan)

    for lat, lon, m_v, frp in (VILLARRICA, LASCAR):
        xm1, ym1 = p(lon, lat)
        c = int(np.argmin(np.abs(x_rad - xm1 / H)))
        r = int(np.argmin(np.abs(y_rad - ym1 / H)))
        mask[r, c] = m_v
        power[r, c] = frp
        temp[r, c] = 350.0
        area[r, c] = 1.5

    return xr.Dataset(
        {"Mask": (("y", "x"), mask), "Power": (("y", "x"), power),
         "Temp": (("y", "x"), temp), "Area": (("y", "x"), area),
         "goes_imager_projection": ((), 0, {
             "longitude_of_projection_origin": SAT_LON,
             "perspective_point_height": H})},
        coords={"x": x_rad, "y": y_rad})


def test_slicing_matches_full_disk():
    """EL test del refactor: el sub-bloque da EXACTAMENTE los mismos hotspots
    que leer el disco entero y filtrar después."""
    from src.fetch.goes_fdcf import extract_hotspots

    ds = _fdcf_ds()
    box = {"lat_min": -40.0, "lat_max": -38.8,
           "lon_min": -72.6, "lon_max": -71.3}

    sliced = extract_hotspots(ds, bounds=box)
    full = extract_hotspots(ds, bounds=box, allow_slice=False)

    assert len(sliced) == 1, [h.to_dict() for h in sliced]
    assert [h.to_dict() for h in sliced] == [h.to_dict() for h in full]
    h = sliced[0]
    assert h.frp_mw == 120.0 and h.confidence == "high"
    assert abs(h.lat - VILLARRICA[0]) < 0.15 and abs(h.lon - VILLARRICA[1]) < 0.15


def test_slicing_reads_only_the_sub_block():
    """Con bbox chico NO se materializa el full-disk: el bloque leído tiene que
    ser una fracción del grid (es el punto de la optimización, no un detalle)."""
    import src.fetch.goes_fdcf as fdcf

    ds = _fdcf_ds()
    seen = []
    real = fdcf._read_block

    def spy(dset, name, rng):
        out = real(dset, name, rng)
        seen.append(out.shape)
        return out

    fdcf._read_block = spy
    try:
        hs = fdcf.extract_hotspots(ds, bounds={"lat_min": -40.0, "lat_max": -38.8,
                                               "lon_min": -72.6, "lon_max": -71.3})
    finally:
        fdcf._read_block = real

    assert len(hs) == 1
    assert seen, "no se leyó ninguna variable"
    for shape in seen:
        assert shape[0] * shape[1] < GRID * GRID / 4, shape


def test_no_bounds_reads_everything():
    """Sin bbox el comportamiento no cambia: full-disk y los dos hotspots,
    ordenados por FRP descendente."""
    from src.fetch.goes_fdcf import extract_hotspots

    hs = extract_hotspots(_fdcf_ds(), bounds=None)
    assert [h.frp_mw for h in hs] == [120.0, 30.0]
    assert [h.confidence for h in hs] == ["high", "low"]


def test_high_conf_only_filters_low_confidence():
    """high_conf_only deja fuera el Mask 14 (baja confianza) — mismo criterio
    con y sin recorte."""
    from src.fetch.goes_fdcf import extract_hotspots

    ds = _fdcf_ds()
    for kw in ({}, {"bounds": CHILE}):
        hs = extract_hotspots(ds, high_conf_only=True, **kw)
        assert [h.mask for h in hs] == [10], (kw, [h.mask for h in hs])


def test_bbox_outside_disk_returns_none_window():
    """Un bbox fuera del disco no rompe: la ventana es None y el lector cae al
    camino full (que después filtra y devuelve vacío)."""
    from src.fetch.goes_fdcf import xy_index_range

    ds = _fdcf_ds()
    rng = xy_index_range(ds["x"].values, ds["y"].values, SAT_LON,
                         {"lat_min": 40, "lat_max": 50,
                          "lon_min": 100, "lon_max": 110})
    assert rng is None


def test_frp_timeline_alias_still_works():
    """`fetch_scan_sliced` quedó como alias delgado: su helper de rango sigue
    exportado (lo importan la timeline y sus tests)."""
    from src.fetch.frp_timeline import _chile_xy_index_range
    from src.fetch.goes_fdcf import xy_index_range

    assert _chile_xy_index_range is xy_index_range
