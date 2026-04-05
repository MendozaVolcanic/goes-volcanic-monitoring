"""Conversión de radiancias ABI a temperatura de brillo.

Usa los coeficientes Planck incluidos en cada archivo L1b NetCDF.
Ref: GOES-R PUG Volume 3, Section 4.2.8.1
"""

import numpy as np
import xarray as xr


def rad_to_bt(ds: xr.Dataset) -> xr.DataArray:
    """Convertir radiancias ABI L1b a temperatura de brillo (K).

    Aplica la función inversa de Planck con corrección de banda:
        T_eff = fk2 / ln(fk1/L + 1)
        BT = (T_eff - bc1) / bc2

    Args:
        ds: Dataset L1b con variables 'Rad', 'planck_fk1', 'planck_fk2',
            'planck_bc1', 'planck_bc2'.

    Returns:
        DataArray de temperatura de brillo en Kelvin.
    """
    rad = ds["Rad"]
    fk1 = float(ds["planck_fk1"].values)
    fk2 = float(ds["planck_fk2"].values)
    bc1 = float(ds["planck_bc1"].values)
    bc2 = float(ds["planck_bc2"].values)

    # Evitar log(0) o log(negativo)
    rad_safe = rad.where(rad > 0, np.nan)
    t_eff = fk2 / np.log((fk1 / rad_safe) + 1)
    bt = (t_eff - bc1) / bc2

    bt.attrs = {
        "long_name": "Brightness Temperature",
        "units": "K",
        "fk1": fk1,
        "fk2": fk2,
        "bc1": bc1,
        "bc2": bc2,
    }
    return bt
