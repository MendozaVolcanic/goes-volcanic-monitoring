"""Geolocalización y recorte de datos GOES ABI.

Convierte coordenadas de proyección fija GOES (rad) a lat/lon
y recorta a la región de interés (Chile).

Ref: GOES-R PUG Volume 3, Section 4.2.8
"""

import numpy as np
import xarray as xr


def get_lat_lon(ds: xr.Dataset) -> tuple[np.ndarray, np.ndarray]:
    """Calcular latitud/longitud desde la proyección fija GOES.

    La proyección GOES usa coordenadas en radianes desde el punto subsatélite.
    Esta función las convierte a lat/lon WGS84.

    Args:
        ds: Dataset ABI con variables 'x', 'y', 'goes_imager_projection'.

    Returns:
        Tupla (lat, lon) como arrays 2D en grados.
    """
    proj = ds["goes_imager_projection"]

    # Parámetros de proyección
    lon_0 = float(proj.attrs["longitude_of_projection_origin"])
    H = float(proj.attrs["perspective_point_height"]) + float(
        proj.attrs["semi_major_axis"]
    )
    r_eq = float(proj.attrs["semi_major_axis"])
    r_pol = float(proj.attrs["semi_minor_axis"])

    # Coordenadas en radianes
    x = ds["x"].values
    y = ds["y"].values
    xx, yy = np.meshgrid(x, y)

    # Conversión a lat/lon (fórmulas GOES-R PUG)
    lambda_0 = np.radians(lon_0)

    a = np.sin(xx) ** 2 + np.cos(xx) ** 2 * (
        np.cos(yy) ** 2 + (r_eq / r_pol) ** 2 * np.sin(yy) ** 2
    )
    b = -2 * H * np.cos(xx) * np.cos(yy)
    c = H**2 - r_eq**2

    # Discriminante
    disc = b**2 - 4 * a * c
    # Pixeles fuera del disco terrestre
    valid = disc >= 0

    r_s = np.full_like(disc, np.nan)
    r_s[valid] = (-b[valid] - np.sqrt(disc[valid])) / (2 * a[valid])

    s_x = r_s * np.cos(xx) * np.cos(yy)
    s_y = -r_s * np.sin(xx)
    s_z = r_s * np.cos(xx) * np.sin(yy)

    lat = np.degrees(
        np.arctan(
            (r_eq / r_pol) ** 2 * s_z / np.sqrt((H - s_x) ** 2 + s_y**2)
        )
    )
    lon = np.degrees(lambda_0 - np.arctan(s_y / (H - s_x)))

    return lat, lon


def crop_to_bounds(
    data: xr.DataArray,
    lat: np.ndarray,
    lon: np.ndarray,
    bounds: dict,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Recortar datos a un bounding box geográfico.

    Args:
        data: DataArray 2D con los datos a recortar.
        lat: Array 2D de latitudes.
        lon: Array 2D de longitudes.
        bounds: Dict con lat_min, lat_max, lon_min, lon_max.

    Returns:
        Tupla (data_crop, lat_crop, lon_crop) como arrays 2D.
    """
    mask = (
        (lat >= bounds["lat_min"])
        & (lat <= bounds["lat_max"])
        & (lon >= bounds["lon_min"])
        & (lon <= bounds["lon_max"])
    )

    # Encontrar bounding box en coordenadas de pixel
    rows = np.any(mask, axis=1)
    cols = np.any(mask, axis=0)

    if not rows.any() or not cols.any():
        return np.array([]), np.array([]), np.array([])

    r_min, r_max = np.where(rows)[0][[0, -1]]
    c_min, c_max = np.where(cols)[0][[0, -1]]

    data_crop = data.values[r_min : r_max + 1, c_min : c_max + 1]
    lat_crop = lat[r_min : r_max + 1, c_min : c_max + 1]
    lon_crop = lon[r_min : r_max + 1, c_min : c_max + 1]

    return data_crop, lat_crop, lon_crop
