"""Generación de composites Ash RGB y Ash/SO2 RGB desde bandas ABI.

Recetas para detección de ceniza volcánica y SO2.
Funcionan día y noche (solo bandas IR).

Ash RGB (RAMMB/CIRA):
    Red:   BT(12.3um) - BT(11.2um)   → rango [-6.7, 2.6] K
    Green: BT(11.2um) - BT(8.4um)    → rango [-6.0, 6.3] K
    Blue:  BT(10.35um)               → rango [243.6, 302.4] K

Ash/SO2 RGB (8.5-11-12, EUMETSAT-adapted):
    Red:   BT(11.2um) - BT(12.3um)   → rango [-4.0, 2.0] K
    Green: BT(8.4um) - BT(11.2um)    → rango [-4.0, 5.0] K
    Blue:  BT(11.2um)                → rango [243.0, 303.0] K

Refs:
    RAMMB/CIRA: https://rammb.cira.colostate.edu/training/visit/quick_guides/GOES_Ash_RGB.pdf
    EUMETSAT Ash RGB: https://resources.eumetrain.org/data/4/410/print_5.htm
"""

import numpy as np
import xarray as xr

from src.config import ASH_RGB, ASH_SO2_RGB


def normalize(data: np.ndarray, vmin: float, vmax: float) -> np.ndarray:
    """Normalizar datos al rango [0, 1] con clipping."""
    return np.clip((data - vmin) / (vmax - vmin), 0, 1)


def generate_ash_rgb(
    bt11: xr.DataArray,
    bt13: xr.DataArray,
    bt14: xr.DataArray,
    bt15: xr.DataArray,
) -> np.ndarray:
    """Generar imagen Ash RGB (RAMMB/CIRA) desde temperaturas de brillo.

    Args:
        bt11: BT banda 11 (8.4 um) en K
        bt13: BT banda 13 (10.35 um) en K
        bt14: BT banda 14 (11.2 um) en K
        bt15: BT banda 15 (12.3 um) en K

    Returns:
        Array numpy (H, W, 3) con valores RGB en [0, 1].
    """
    red_data = bt15.values - bt14.values
    red = normalize(red_data, *ASH_RGB["red"]["range"])

    green_data = bt14.values - bt11.values
    green = normalize(green_data, *ASH_RGB["green"]["range"])

    blue = normalize(bt13.values, *ASH_RGB["blue"]["range"])

    rgb = np.dstack([red, green, blue])

    mask = np.isnan(bt14.values)
    rgb[mask] = 0

    return rgb


def generate_ash_so2_rgb(
    bt11: xr.DataArray,
    bt14: xr.DataArray,
    bt15: xr.DataArray,
) -> np.ndarray:
    """Generar imagen Ash/SO2 RGB (8.5-11-12) desde temperaturas de brillo.

    Optimizado para distinguir ceniza de SO2 usando la banda 8.4 um.
    La banda 8.4 um tiene absorción por SO2, por lo que el canal verde
    discrimina SO2 sin contaminación solar (a diferencia del RGB con 3.9 um).

    Ref: EUMETSAT Ash RGB adapted for ABI bands.

    Args:
        bt11: BT banda 11 (8.4 um) en K
        bt14: BT banda 14 (11.2 um) en K
        bt15: BT banda 15 (12.3 um) en K

    Returns:
        Array numpy (H, W, 3) con valores RGB en [0, 1].
    """
    # Red: BT(11.2) - BT(12.3) → reverse absorption (ceniza = negativo)
    red_data = bt14.values - bt15.values
    red = normalize(red_data, *ASH_SO2_RGB["red"]["range"])

    # Green: BT(8.4) - BT(11.2) → SO2 absorption (SO2 = muy negativo → invertido)
    green_data = bt11.values - bt14.values
    green = normalize(green_data, *ASH_SO2_RGB["green"]["range"])

    # Blue: BT(11.2) → temperatura de superficie/nube
    blue = normalize(bt14.values, *ASH_SO2_RGB["blue"]["range"])

    rgb = np.dstack([red, green, blue])

    mask = np.isnan(bt14.values)
    rgb[mask] = 0

    return rgb


def generate_so2_indicator(
    bt11: xr.DataArray,
    bt14: xr.DataArray,
) -> xr.DataArray:
    """Calcular indicador de SO2 basado en BTD(8.4-11.2).

    SO2 absorbe fuertemente en 8.4um, causando BT(8.4) << BT(11.2).
    Un valor muy negativo indica presencia de SO2.

    Args:
        bt11: BT banda 11 (8.4 um)
        bt14: BT banda 14 (11.2 um)

    Returns:
        DataArray con diferencia BT(8.4) - BT(11.2). Valores < -3K sugieren SO2.
    """
    so2 = bt11 - bt14
    so2.attrs = {
        "long_name": "SO2 Indicator (BT8.4 - BT11.2)",
        "units": "K",
        "threshold": "< -3 K suggests SO2 presence",
    }
    return so2
