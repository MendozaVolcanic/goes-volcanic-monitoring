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

from src.process.geo import bbox_indices, crop_to_bounds, get_lat_lon


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

    # Solo el pixel (row=1, col=1): lat=-40 (in [-42,-38]) y lon=-72 (in [-73,-71]).
    # Aserta el CONTENIDO real del crop, no una tautologia sobre literales.
    assert data_c.shape == (1, 1), data_c.shape
    assert data_c[0, 0] == 4  # data[1,1] = 4
    assert lat_c[0, 0] == -40 and lon_c[0, 0] == -72


def test_crop_empty_when_no_overlap():
    """Si el bbox no intersecta los datos, devolver arrays vacios sin crash."""
    lat = np.array([[-45, -40], [-45, -40]])
    lon = np.array([[-75, -75], [-72, -72]])
    data = xr.DataArray(np.arange(4).reshape(2, 2))

    bounds = {"lat_min": 10, "lat_max": 20, "lon_min": 10, "lon_max": 20}
    data_c, lat_c, lon_c = crop_to_bounds(data, lat, lon, bounds)

    assert data_c.size == 0


def test_bbox_indices_exclusive_and_coupled():
    """bbox_indices: r1/c1 EXCLUSIVOS, None sin overlap, y acoplado a crop.

    El pipeline hace pan_crop = refls[2][2*r0:2*r1, ...] confiando en que
    r1/c1 son exclusivos (estilo slice). Si alguien los volviera inclusivos,
    crop_to_bounds seguiria pareciendo correcto pero el pan_crop quedaria 2px
    corto -> misregistro silencioso. Este test ancla el contrato exclusivo.
    """
    # Grilla 4x4: lat por fila, lon por columna.
    lat = np.array([[-44.0]*4, [-42.0]*4, [-40.0]*4, [-38.0]*4])
    lon = np.tile(np.array([-75.0, -73.0, -71.0, -69.0]), (4, 1))
    bounds = {"lat_min": -43, "lat_max": -39, "lon_min": -74, "lon_max": -70}
    # filas con lat en [-43,-39]: -42 (1), -40 (2) -> r0=1, r1=3 (exclusivo)
    # cols con lon en [-74,-70]: -73 (1), -71 (2) -> c0=1, c1=3 (exclusivo)
    idx = bbox_indices(lat, lon, bounds)
    assert idx == (1, 3, 1, 3), idx
    r0, r1, c0, c1 = idx
    # Exclusivo: el conteo de pixeles = r1-r0 (no r1-r0+1)
    assert (r1 - r0, c1 - c0) == (2, 2)
    # Acoplado: crop_to_bounds devuelve EXACTAMENTE ese shape
    data = xr.DataArray(np.arange(16).reshape(4, 4))
    data_c, _, _ = crop_to_bounds(data, lat, lon, bounds)
    assert data_c.shape == (r1 - r0, c1 - c0)
    # None si no hay overlap
    assert bbox_indices(lat, lon, {"lat_min": 10, "lat_max": 20,
                                   "lon_min": 10, "lon_max": 20}) is None


if __name__ == "__main__":
    test_subsatellite_point()
    test_off_disk_pixels_are_nan()
    test_grid_shape_matches_meshgrid()
    test_chile_is_within_disk()
    test_crop_to_bounds_basic()
    test_crop_empty_when_no_overlap()
    test_bbox_indices_exclusive_and_coupled()
    print("OK — geo tests passed")
