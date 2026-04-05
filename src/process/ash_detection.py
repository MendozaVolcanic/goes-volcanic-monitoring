"""Detección de ceniza volcánica mediante BTD split-window.

Implementa la técnica clásica de Prata (1989) adaptada para ABI GOES-R.
La ceniza volcánica (silicatos) produce un BTD negativo entre 11.2um y 12.3um,
mientras que nubes de hielo/agua producen BTD positivo.

Ref:
    - Prata, A.J. (1989). Observations of volcanic ash clouds using AVHRR-2.
      Int. J. Remote Sensing, 10(4-5), 751-761.
    - GOES-R ATBD for Volcanic Ash, Version 3.0, July 2012.
"""

import numpy as np
import xarray as xr

from src.config import BTD_ASH_THRESHOLD, BTD_MIN_TEMP, BTD_TRI_THRESHOLD


def compute_btd_split_window(
    bt14: xr.DataArray,
    bt15: xr.DataArray,
) -> xr.DataArray:
    """Calcular BTD split-window: BT(11.2um) - BT(12.3um).

    Interpretación:
        BTD > 0  → nubes meteorológicas (hielo/agua)
        BTD < 0  → posible ceniza volcánica (silicatos)
        BTD << 0 → ceniza volcánica probable

    Args:
        bt14: BT banda 14 (11.2 um) en K
        bt15: BT banda 15 (12.3 um) en K

    Returns:
        DataArray con BTD en Kelvin.
    """
    btd = bt14 - bt15
    btd.attrs = {
        "long_name": "Split-Window BTD (11.2 - 12.3 um)",
        "units": "K",
        "ash_threshold": BTD_ASH_THRESHOLD,
    }
    return btd


def detect_ash_basic(
    bt14: xr.DataArray,
    bt15: xr.DataArray,
) -> xr.DataArray:
    """Detección básica de ceniza: BTD split-window + filtro de temperatura.

    Criterios:
        1. BT(11.2) > 200 K (filtrar pixeles demasiado fríos / espacio)
        2. BT(11.2) - BT(12.3) < -1.0 K (señal de ceniza)

    Returns:
        DataArray booleano (True = posible ceniza).
    """
    btd = bt14 - bt15
    mask = (btd < BTD_ASH_THRESHOLD) & (bt14 > BTD_MIN_TEMP)
    mask.attrs = {
        "long_name": "Volcanic Ash Detection (basic BTD)",
        "method": "split-window",
        "btd_threshold": BTD_ASH_THRESHOLD,
        "min_temp": BTD_MIN_TEMP,
    }
    return mask


def detect_ash_enhanced(
    bt11: xr.DataArray,
    bt14: xr.DataArray,
    bt15: xr.DataArray,
) -> xr.DataArray:
    """Detección mejorada tri-espectral de ceniza.

    Agrega banda 8.4um para reducir falsos positivos.

    Criterios:
        1. BT(11.2) > 200 K
        2. BT(11.2) - BT(12.3) < -1.0 K (split-window)
        3. (BT(8.4) - BT(11.2)) + (BT(12.3) - BT(11.2)) < 0 (tri-espectral)

    Returns:
        DataArray booleano (True = ceniza con alta confianza).
    """
    btd = bt14 - bt15
    btd_tri = (bt11 - bt14) + (bt15 - bt14)

    mask = (
        (bt14 > BTD_MIN_TEMP)
        & (btd < BTD_ASH_THRESHOLD)
        & (btd_tri < BTD_TRI_THRESHOLD)
    )
    mask.attrs = {
        "long_name": "Volcanic Ash Detection (enhanced tri-spectral)",
        "method": "split-window + tri-spectral",
    }
    return mask


def compute_ash_confidence(
    bt11: xr.DataArray,
    bt14: xr.DataArray,
    bt15: xr.DataArray,
) -> xr.DataArray:
    """Calcular nivel de confianza de detección de ceniza (0-3).

    Niveles:
        0 = sin ceniza detectada
        1 = baja confianza (solo BTD < -0.5 K)
        2 = media confianza (BTD < -1.0 K)
        3 = alta confianza (BTD + tri-espectral)

    Returns:
        DataArray con valores 0-3.
    """
    btd = bt14 - bt15
    btd_tri = (bt11 - bt14) + (bt15 - bt14)
    temp_ok = bt14 > BTD_MIN_TEMP

    confidence = xr.zeros_like(bt14, dtype=np.int8)
    confidence = confidence.where(~(temp_ok & (btd < -0.5)), 1)
    confidence = confidence.where(~(temp_ok & (btd < BTD_ASH_THRESHOLD)), 2)
    confidence = confidence.where(
        ~(temp_ok & (btd < BTD_ASH_THRESHOLD) & (btd_tri < BTD_TRI_THRESHOLD)),
        3,
    )
    confidence.attrs = {
        "long_name": "Ash Detection Confidence Level",
        "flag_values": "0=none, 1=low, 2=medium, 3=high",
    }
    return confidence
