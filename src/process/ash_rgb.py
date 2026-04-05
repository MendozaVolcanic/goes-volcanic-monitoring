"""Generación de composite Ash RGB desde bandas ABI.

Receta RAMMB/CIRA para detección de ceniza volcánica y SO2.
Funciona día y noche (solo bandas IR).

Ref: https://rammb.cira.colostate.edu/training/visit/quick_guides/GOES_Ash_RGB.pdf

Componentes:
    Red:   BT(12.3um) - BT(11.2um)   → rango [-6.7, 2.6] K
    Green: BT(11.2um) - BT(8.4um)    → rango [-6.0, 6.3] K
    Blue:  BT(10.35um)               → rango [243.6, 302.4] K

Interpretación:
    - Rojo/Magenta = ceniza volcánica
    - Verde brillante = SO2
    - Amarillo = mezcla ceniza + SO2
"""

import numpy as np
import xarray as xr

from src.config import ASH_RGB


def normalize(data: np.ndarray, vmin: float, vmax: float) -> np.ndarray:
    """Normalizar datos al rango [0, 1] con clipping."""
    return np.clip((data - vmin) / (vmax - vmin), 0, 1)


def generate_ash_rgb(
    bt11: xr.DataArray,
    bt13: xr.DataArray,
    bt14: xr.DataArray,
    bt15: xr.DataArray,
) -> np.ndarray:
    """Generar imagen Ash RGB desde temperaturas de brillo.

    Args:
        bt11: BT banda 11 (8.4 um) en K
        bt13: BT banda 13 (10.35 um) en K
        bt14: BT banda 14 (11.2 um) en K
        bt15: BT banda 15 (12.3 um) en K

    Returns:
        Array numpy (H, W, 3) con valores RGB en [0, 1].
    """
    # Red: B15 - B14 (espesor óptico)
    red_data = bt15.values - bt14.values
    red = normalize(red_data, *ASH_RGB["red"]["range"])

    # Green: B14 - B11 (fase/tamaño partícula)
    green_data = bt14.values - bt11.values
    green = normalize(green_data, *ASH_RGB["green"]["range"])

    # Blue: B13 (temperatura de superficie)
    blue = normalize(bt13.values, *ASH_RGB["blue"]["range"])

    # Stack RGB
    rgb = np.dstack([red, green, blue])

    # Enmascarar pixeles sin datos
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
