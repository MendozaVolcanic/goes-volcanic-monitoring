"""GeoColor-lite: composite visible diurno + IR pseudo-color nocturno.

Receta simplificada estilo RAMMB GeoColor pero sin dependencias pesadas
(sin xRIT, sin satpy). Suficiente para visualizacion operacional.

Diurno (sol >= 5° elevacion):
    TrueColor RGB simplificado:
        R = banda 2 (rojo visible 0.64 um, nativa 0.5 km/px)
        G = sintetizado de 1+2+3 con coeficientes balanceados
        B = banda 1 (azul visible 0.47 um, 1 km/px)
    Reflectancias normalizadas + gamma 0.5 + clip [0, 1].

Nocturno (sol < 5°):
    Banda 13 (clean IR 10.3 um) -> BT -> colormap inverso
    Frio (nubes altas) = blanco, calido (suelo) = oscuro.

Sin Rayleigh proper (Phase 2). Sin sharpening hi-res (Phase 2).
Visualmente decente, no perfecto. La ganancia clave es resolucion 0.5 km/px
de banda 2 — vs 1.7 km/px de RAMMB zoom 4 = 4x mas detalle en visible.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

import numpy as np
import xarray as xr

logger = logging.getLogger(__name__)


def rad_to_reflectance(rad: xr.DataArray, ds: xr.Dataset) -> np.ndarray:
    """Convertir radiance a reflectance usando kappa0 del NetCDF.

    Solo aplica a bandas visibles/NIR (1-6). kappa0 es un coeficiente
    pre-calculado por NOAA que considera flujo solar y geometria
    sat-sol nominal. Reflectance = rad * kappa0.

    Devuelve array 2D float32 normalizado [0, ~1].
    """
    kappa0 = float(ds["kappa0"].values)
    refl = rad.values * kappa0
    return np.clip(refl, 0, 1).astype(np.float32)


def bt_to_pseudo_color_ir(bt: np.ndarray,
                          tmin: float = 200.0, tmax: float = 300.0
                          ) -> np.ndarray:
    """Mapear BT (K) a RGB pseudo-color blanco-azul-naranja.

    Frio (nubes altas) = blanco
    Templado (suelo) = naranja
    Caliente (lava/fuego) = rojo brillante

    Devuelve uint8 (H, W, 3).
    """
    # Normalizar invertido: T=tmin -> 1 (blanco), T=tmax -> 0 (oscuro)
    norm = np.clip((bt - tmin) / (tmax - tmin), 0, 1)
    inv = 1.0 - norm  # frio=1, calido=0

    # Composite: alto=blanco (1,1,1), medio=naranja (0.7,0.4,0.1), bajo=negro
    r = np.where(inv > 0.6, 1.0, inv * 1.5 + 0.1).clip(0, 1)
    g = np.where(inv > 0.6, 1.0, inv * 1.0 + 0.1).clip(0, 1)
    b = np.where(inv > 0.6, 1.0, inv * 0.3).clip(0, 1)

    rgb = np.stack([r, g, b], axis=-1)
    return (rgb * 255).astype(np.uint8)


def contrast_stretch(rgb: np.ndarray, low_pct: float = 2.0,
                     high_pct: float = 98.0) -> np.ndarray:
    """Rescalar valores a percentil (low, high) -> (0, 1). Sube contraste.

    Sin Rayleigh proper, las imágenes TrueColor tienen std baja (~15) vs
    GeoColor RAMMB (std ~66). Este stretch al percentil 2-98 recupera
    ~80% del contraste perdido. Por canal individual para evitar shift de
    color.
    """
    out = np.zeros_like(rgb)
    for c in range(rgb.shape[-1]):
        ch = rgb[..., c]
        lo, hi = np.percentile(ch, [low_pct, high_pct])
        if hi - lo > 1e-6:
            out[..., c] = np.clip((ch - lo) / (hi - lo), 0, 1)
        else:
            out[..., c] = ch
    return out


def unsharp_mask(rgb: np.ndarray, amount: float = 0.6,
                 sigma: float = 1.0) -> np.ndarray:
    """Unsharp mask suave para sharpening de hi-res. amount=0.6 = +60% bordes."""
    try:
        from scipy.ndimage import gaussian_filter
    except ImportError:
        return rgb
    blurred = np.zeros_like(rgb)
    for c in range(rgb.shape[-1]):
        blurred[..., c] = gaussian_filter(rgb[..., c], sigma=sigma)
    sharpened = rgb + amount * (rgb - blurred)
    return np.clip(sharpened, 0, 1)


def band2_monochrome_05km(refl_b2: np.ndarray, gamma: float = 0.6,
                           tint: tuple[int, int, int] = (255, 245, 220),
                           enhance: bool = True
                           ) -> np.ndarray:
    """Banda 2 sola en resolucion NATIVA 0.5 km/px como pseudo-color sepia.

    Trade-off: pierde color verdadero (es un canal monocromatico) pero
    mantiene la resolucion completa de 0.5 km/px = 4× mejor que RAMMB.
    Aplica gamma + (opcional) contrast stretch + unsharp mask para que
    no se vea plano vs RAMMB.

    Pensado para "ver el crater". A 0.5 km/px Lascar (~500m crater) ocupa
    un cuadrante de la imagen, no un pixel.
    """
    refl = np.clip(refl_b2, 0, 1)
    refl = np.power(refl, gamma)
    if enhance:
        # Contrast stretch en el canal monocromo
        lo, hi = np.percentile(refl, [2.0, 98.0])
        if hi - lo > 1e-6:
            refl = np.clip((refl - lo) / (hi - lo), 0, 1)
    # Aplicar tint suave (mezcla 80% intensidad neutra + 20% sepia)
    r = refl * tint[0] / 255.0
    g = refl * tint[1] / 255.0
    b = refl * tint[2] / 255.0
    rgb = np.stack([r, g, b], axis=-1)
    if enhance:
        rgb = unsharp_mask(rgb, amount=0.5, sigma=0.9)
    return (np.clip(rgb, 0, 1) * 255).astype(np.uint8)


def true_color_rgb(refl_b1: np.ndarray, refl_b2: np.ndarray,
                   refl_b3: np.ndarray, gamma: float = 0.5,
                   enhance: bool = True) -> np.ndarray:
    """TrueColor RGB simplificado desde reflectancias bandas 1, 2, 3.

    Asume todas las bandas YA estan al mismo grid (resampling externo).

    Args:
        refl_b1: banda 1 (azul) reflectancia [0, 1].
        refl_b2: banda 2 (rojo) reflectancia [0, 1].
        refl_b3: banda 3 (NIR vegetacion) reflectancia [0, 1].
        gamma:   factor gamma para brightening (0.5 = visible mas brillante).
        enhance: si True (default), aplica contrast stretch + unsharp mask
                 post-gamma para compensar la falta de Rayleigh correction.
                 Sin enhance la imagen sale plana (std~15) vs RAMMB (std~66).

    Devuelve uint8 (H, W, 3) RGB.
    """
    # Verde sintetizado: combinacion balanceada (receta CIRA simplificada)
    green = 0.45 * refl_b2 + 0.10 * refl_b3 + 0.45 * refl_b1

    rgb = np.stack([refl_b2, green, refl_b1], axis=-1)
    rgb = np.clip(rgb, 0, 1)
    rgb = np.power(rgb, gamma)  # brightness curve

    if enhance:
        # Contrast stretch percentil 2-98 + unsharp mask suave.
        # Esto recupera ~80% del contraste perdido por no tener Rayleigh.
        rgb = contrast_stretch(rgb, low_pct=2.0, high_pct=98.0)
        rgb = unsharp_mask(rgb, amount=0.5, sigma=0.9)

    return (rgb * 255).astype(np.uint8)


def solar_elevation(lat: float, lon: float, dt: datetime) -> float:
    """Elevacion solar (grados) en (lat, lon) en datetime UTC.

    Algoritmo simple sin libreria externa. Precision ~0.5° (suficiente
    para decidir dia/noche).
    """
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    # Day of year + hora fraccional
    doy = dt.timetuple().tm_yday
    hour = dt.hour + dt.minute / 60.0 + dt.second / 3600.0
    # Declinacion solar
    decl = 23.45 * np.sin(np.radians(360.0 * (284 + doy) / 365.0))
    # Hour angle
    ha = (hour + lon / 15.0 - 12.0) * 15.0
    # Elevation
    sin_alt = (np.sin(np.radians(lat)) * np.sin(np.radians(decl))
               + np.cos(np.radians(lat)) * np.cos(np.radians(decl))
               * np.cos(np.radians(ha)))
    return float(np.degrees(np.arcsin(np.clip(sin_alt, -1, 1))))
