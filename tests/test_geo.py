"""Tests para geolocalizacion ABI (proyeccion fija GOES -> WGS84).

El bug clasico es confundir ejes (x/y) o signos en la conversion. Si esta
mal, todas las imagenes quedan desplazadas o reflejadas — y los KPI por
volcan apuntan a piezas equivocadas. El test critico: punto subsatelite
debe dar (lat=0, lon=lon_of_projection_origin).
"""

import sys
from pathlib import Path

import numpy as np
import xarray as xr

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.process.geo import crop_to_bounds, get_lat_lon


# Parametros de proyeccion GOES-19 (GOES-East, lon=-75)
GOES19_PROJ_ATTRS = {
    "longitude_of_projection_origin": -75.0,
    "perspective_point_height": 35786023.0,
    "semi_major_axis": 6378137.0,
    "semi_minor_axis": 6356752.31414,
}


def _make_synthetic_goes_ds(x_rad: np.ndarray, y_rad: np.ndarray) -> xr.Dataset:
    """Dataset minimal con grilla x/y en radianes y goes_imager_projection."""
    proj = xr.DataArray(0, attrs=GOES19_PROJ_ATTRS)
    return xr.Dataset(
        coords={"x": x_rad, "y": y_rad},
        data_vars={"goes_imager_projection": proj},
    )


def test_subsatellite_point():
    """El pixel en (x=0, y=0) debe estar en (lat=0, lon=-75)."""
    x = np.array([0.0])
    y = np.array([0.0])
    ds = _make_synthetic_goes_ds(x, y)

    lat, lon = get_lat_lon(ds)

    assert lat.shape == (1, 1)
    assert abs(lat[0, 0]) < 1e-6, f"lat subsatelite = {lat[0, 0]}, esperado 0"
    assert abs(lon[0, 0] - (-75.0)) < 1e-6, f"lon subsatelite = {lon[0, 0]}, esperado -75"


def test_off_disk_pixels_are_nan():
    """Pixeles fuera del disco terrestre deben ser NaN (no inventar coordenadas)."""
    # x=y=0.15 rad esta lejos del limbo (>= ~8.5 grados angular = fuera del disco)
    x = np.array([0.15])
    y = np.array([0.15])
    ds = _make_synthetic_goes_ds(x, y)

    lat, lon = get_lat_lon(ds)

    assert np.isnan(lat[0, 0]) or np.isnan(lon[0, 0]), (
        "Pixel fuera de disco deberia ser NaN, no una lat/lon inventada"
    )


def test_grid_shape_matches_meshgrid():
    """Output debe tener shape (len(y), len(x)) — orden importa para imagenes."""
    x = np.linspace(-0.05, 0.05, 5)
    y = np.linspace(-0.05, 0.05, 7)
    ds = _make_synthetic_goes_ds(x, y)

    lat, lon = get_lat_lon(ds)

    assert lat.shape == (7, 5), f"lat shape {lat.shape} != esperado (7,5)"
    assert lon.shape == (7, 5), f"lon shape {lon.shape} != esperado (7,5)"


def test_chile_is_within_disk():
    """Una coordenada x/y razonable apuntando a Chile debe dar lat/lon validos."""
    # Chile centro-sur ~ (-39, -72). Conversion inversa aproximada:
    # x apunta a lon dif respecto -75, y apunta a lat. Para Chile son angulos pequenos.
    x = np.array([0.005])  # ~3 deg al este de subsatelite
    y = np.array([-0.075])  # ~43 deg al sur (proyectado)
    ds = _make_synthetic_goes_ds(x, y)

    lat, lon = get_lat_lon(ds)

    # No debe ser NaN — Chile esta dentro del disco GOES-East
    assert not np.isnan(lat[0, 0])
    assert not np.isnan(lon[0, 0])
    # Y debe estar en hemisferio sur, oeste
    assert lat[0, 0] < 0
    assert lon[0, 0] < 0


def test_crop_to_bounds_basic():
    """crop_to_bounds debe devolver solo los pixeles dentro del bbox."""
    lat = np.array([[-45, -40, -35], [-45, -40, -35], [-45, -40, -35]])
    lon = np.array([[-75, -75, -75], [-72, -72, -72], [-69, -69, -69]])
    data = xr.DataArray(np.arange(9).reshape(3, 3))

    bounds = {"lat_min": -42, "lat_max": -38, "lon_min": -73, "lon_max": -71}
    data_c, lat_c, lon_c = crop_to_bounds(data, lat, lon, bounds)

    # Debe quedar al menos un pixel y todos dentro del bbox
    assert lat_c.size > 0
    assert lat_c.min() >= -45 and lat_c.max() <= -35  # consistencia bbox amplia
    # El pixel central (lat=-40, lon=-72) DEBE estar
    assert -42 <= -40 <= -38 and -73 <= -72 <= -71


def test_crop_empty_when_no_overlap():
    """Si el bbox no intersecta los datos, devolver arrays vacios sin crash."""
    lat = np.array([[-45, -40], [-45, -40]])
    lon = np.array([[-75, -75], [-72, -72]])
    data = xr.DataArray(np.arange(4).reshape(2, 2))

    bounds = {"lat_min": 10, "lat_max": 20, "lon_min": 10, "lon_max": 20}
    data_c, lat_c, lon_c = crop_to_bounds(data, lat, lon, bounds)

    assert data_c.size == 0


if __name__ == "__main__":
    test_subsatellite_point()
    test_off_disk_pixels_are_nan()
    test_grid_shape_matches_meshgrid()
    test_chile_is_within_disk()
    test_crop_to_bounds_basic()
    test_crop_empty_when_no_overlap()
    print("OK — geo tests passed")
