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


def planck_rad_from_bt(bt, fk1: float, fk2: float, bc1: float, bc2: float):
    """Planck **directo** (BT en K → radiancia ABI), inverso exacto de
    :func:`rad_to_bt`.

        T_eff = bc1 + bc2 · BT
        Rad   = fk1 / (exp(fk2 / T_eff) − 1)

    Por qué existe: el retrieval de altura Wen-Rose (Fase 3b) mezcla
    **radiancias** de dos canales (no temperaturas de brillo) para despejar la
    temperatura del tope corrigiendo emisividad — la mezcla lineal de Planck NO
    es lineal en BT, así que hay que ir a radiancia, operar, y volver. Esta es la
    pieza forward que faltaba (``rad_to_bt`` solo hace la inversa).

    Función PURA y vectorizada: acepta escalar o ``np.ndarray`` y devuelve el
    mismo shape. Usar los coeficientes ``fk1/fk2/bc1/bc2`` del MISMO NetCDF L1b
    del que salió la BT (son por-banda) para que forward∘inversa = identidad.
    """
    bt = np.asarray(bt, dtype="float64")
    t_eff = bc1 + bc2 * bt
    return fk1 / (np.exp(fk2 / t_eff) - 1.0)
