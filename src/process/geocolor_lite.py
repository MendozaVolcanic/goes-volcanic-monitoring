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

    NaN-safe: usa nanpercentile (un solo NaN de pixel fill/off-disk con
    np.percentile devolvia NaN y ANULABA el stretch de TODO el canal) y
    nan_to_num al final (NaN->0 = negro, convencion de borde del proyecto).
    """
    out = np.zeros_like(rgb)
    for c in range(rgb.shape[-1]):
        ch = rgb[..., c]
        lo, hi = np.nanpercentile(ch, [low_pct, high_pct])
        if np.isfinite(lo) and np.isfinite(hi) and hi - lo > 1e-6:
            out[..., c] = (ch - lo) / (hi - lo)
        else:
            out[..., c] = ch
    return np.clip(np.nan_to_num(out, nan=0.0), 0, 1)


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


def _downsample_mean_2x(arr: np.ndarray) -> np.ndarray:
    """Downsample 2x por bloque-media (anti-alias). Trunca a dims pares. 2D."""
    h, w = arr.shape[:2]
    h2, w2 = h // 2, w // 2
    return arr[:h2 * 2, :w2 * 2].reshape(h2, 2, w2, 2).mean(axis=(1, 3))


def _box_lowpass_2x(arr: np.ndarray) -> np.ndarray:
    """Low-pass a la escala 1 km: downsample-media 2x + re-upsample nearest.

    Devuelve un array de la MISMA forma (par) que `arr`. La diferencia
    `arr - lowpass` aisla el detalle sub-1km (la octava que B1/B3 a 1 km
    no resuelven). Numpy puro: no depende de scipy (no garantizado en el
    runner HF — ver fallback de unsharp_mask).
    """
    h, w = arr.shape[:2]
    h2, w2 = (h // 2) * 2, (w // 2) * 2
    a = arr[:h2, :w2]
    lo = _downsample_mean_2x(a)
    return np.repeat(np.repeat(lo, 2, axis=0), 2, axis=1)


def _stretch_single(ch: np.ndarray, low_pct: float = 2.0,
                    high_pct: float = 98.0) -> np.ndarray:
    """Contrast stretch percentil de un solo canal -> [0, 1]. NaN-safe."""
    if not np.isfinite(ch).any():
        return np.zeros_like(ch)
    lo, hi = np.nanpercentile(ch, [low_pct, high_pct])
    if np.isfinite(lo) and np.isfinite(hi) and hi - lo > 1e-6:
        out = (ch - lo) / (hi - lo)
    else:
        out = ch
    return np.clip(np.nan_to_num(out, nan=0.0), 0, 1)


def _resize_rgb_bilinear(rgb_float: np.ndarray,
                         out_hw: tuple[int, int]) -> np.ndarray:
    """Re-escalar RGB float [0,1] (H,W,3) a (out_h,out_w) bilineal via PIL.

    PIL es dependencia core del proyecto. Lazy import (gotcha Streamlit
    hot-reload, ver CLAUDE.md). Fallback nearest-numpy si PIL faltara.
    Maneja ratios arbitrarios -> no exige que LR sea exactamente 2x del pan.
    """
    out_h, out_w = out_hw
    if rgb_float.shape[:2] == (out_h, out_w):
        return rgb_float
    try:
        from PIL import Image
        u8 = (np.clip(np.nan_to_num(rgb_float, nan=0.0), 0, 1)
              * 255).astype(np.uint8)
        img = Image.fromarray(u8, mode="RGB").resize(
            (out_w, out_h), Image.BILINEAR)  # PIL toma (W, H)
        return np.asarray(img, dtype=np.float32) / 255.0
    except Exception:
        # Fallback degradado pero sin crash: nearest por repeticion/recorte.
        ry = max(1, out_h // rgb_float.shape[0])
        rx = max(1, out_w // rgb_float.shape[1])
        up = np.repeat(np.repeat(rgb_float, ry, axis=0), rx, axis=1)
        return up[:out_h, :out_w]


def _true_color_lr_float(refl_b1: np.ndarray, refl_b2: np.ndarray,
                         refl_b3: np.ndarray, gamma: float, enhance: bool,
                         do_unsharp: bool) -> np.ndarray:
    """Nucleo TrueColor (receta CIRA simplificada) -> RGB float [0,1] (H,W,3).

    Compartido por el camino 1 km (`true_color_rgb` sin pan, do_unsharp=True)
    y por el pan-sharpen (do_unsharp=False: el detalle lo aporta el pan, no
    queremos sharpenear lo borroso de 1 km y despues ampliarlo).
    """
    green = 0.45 * refl_b2 + 0.10 * refl_b3 + 0.45 * refl_b1
    rgb = np.stack([refl_b2, green, refl_b1], axis=-1)
    rgb = np.clip(rgb, 0, 1)
    rgb = np.power(rgb, gamma)  # brightness curve
    if enhance:
        rgb = contrast_stretch(rgb, low_pct=2.0, high_pct=98.0)
        if do_unsharp:
            rgb = unsharp_mask(rgb, amount=0.5, sigma=0.9)
    # nan_to_num: NaN de pixel fill/off-disk -> 0 (negro), salida siempre
    # finita para el cast a uint8. No-op en datos finitos (compat byte-idem).
    return np.nan_to_num(np.clip(rgb, 0, 1), nan=0.0)


def _pansharpen(rgb_lo_float: np.ndarray, pan: np.ndarray, gamma: float,
                enhance: bool, detail_weight: float) -> np.ndarray:
    """High-Pass Modulation: color del RGB 1 km + detalle 0.5 km del pan.

    Args:
        rgb_lo_float: (Hl,Wl,3) [0,1] color a baja resolucion (1 km).
        pan:          (Hh,Wh) reflectancia hi-res (B2 0.5 km) = fuente de detalle.
        detail_weight: ganancia del detalle inyectado (1.0 = nominal).

    Devuelve uint8 (Hh,Wh,3) (pan recortado a dims pares).

    Por que: el detalle `pan - lowpass(pan)` es de media ~cero, asi que agrega
    SOLO bordes/textura sub-1km. La luminancia de salida APROXIMA el pan nativo
    (el resize bilineal y el gamma no-lineal hacen que no sea exacto) y el color
    lo aporta el LR. Asume estructura espacial compartida entre bandas visibles
    (estandar en pan-sharpening true-color: nubes/costa/sombra del cono se ven
    igual en B1/B2/B3, solo cambia la resolucion del muestreo).

    El detalle se clampea al HEADROOM por-pixel (cuanto se puede sumar/restar
    antes de que ALGUN canal sature) y se aplica IGUAL a R/G/B -> la croma se
    preserva exactamente incluso en nube/nieve brillante (sin el shift de tono
    que daria un clip por-canal asimetrico).
    """
    pan = np.asarray(pan, dtype=np.float32)
    h, w = pan.shape[:2]
    h2, w2 = (h // 2) * 2, (w // 2) * 2
    if h2 < 2 or w2 < 2:
        # Tile degenerado (sin par util) -> solo color LR re-escalado, sin
        # detalle. Evita np.percentile sobre array vacio. (no deberia pasar:
        # el caller deriva pan como 2x indices 1km, pero robustez del helper.)
        out = _resize_rgb_bilinear(rgb_lo_float, (max(h2, 1), max(w2, 1)))
        return (np.clip(np.nan_to_num(out, nan=0.0), 0, 1) * 255).astype(np.uint8)
    pan = np.clip(pan[:h2, :w2], 0, 1)

    # 1. Color LR re-escalado al grid del pan (0.5 km).
    rgb_up = np.clip(_resize_rgb_bilinear(rgb_lo_float, (h2, w2)), 0, 1)

    # 2. Detalle hi-res en espacio de display (mismo gamma/stretch que canales).
    pan_disp = np.power(pan, gamma)
    if enhance:
        pan_disp = _stretch_single(pan_disp)
    detail = detail_weight * (pan_disp - _box_lowpass_2x(pan_disp))  # ~media 0

    # 3. Clampear el detalle al headroom por-pixel (sumable antes de que el
    #    canal mas alto sature; restable antes de que el mas bajo llegue a 0)
    #    y aplicarlo IGUAL a los 3 canales -> croma intacta sin clip asimetrico.
    hi_room = 1.0 - rgb_up.max(axis=-1)   # margen positivo (canal mas brillante)
    lo_room = rgb_up.min(axis=-1)         # margen negativo (canal mas oscuro)
    detail = np.minimum(np.maximum(detail, -lo_room), hi_room)

    out = np.clip(rgb_up + detail[..., None], 0, 1)
    return (np.nan_to_num(out, nan=0.0) * 255).astype(np.uint8)


def true_color_rgb(refl_b1: np.ndarray, refl_b2: np.ndarray,
                   refl_b3: np.ndarray, gamma: float = 0.5,
                   enhance: bool = True, pan: "np.ndarray | None" = None,
                   detail_weight: float = 1.0) -> np.ndarray:
    """TrueColor RGB simplificado desde reflectancias bandas 1, 2, 3.

    Asume B1/B2/B3 al mismo grid (resampling externo). Si se pasa `pan`,
    pan-sharpening: el color sale de B1/B2/B3 a 1 km y el detalle de `pan`
    (B2 nativa 0.5 km) -> salida a 0.5 km/px (4x RAMMB) sin shift de color.

    Args:
        refl_b1: banda 1 (azul) reflectancia [0, 1].
        refl_b2: banda 2 (rojo) reflectancia [0, 1] al MISMO grid que b1/b3
                 (1 km; en el camino pan-sharpen es B2 degradada a 1 km).
        refl_b3: banda 3 (NIR vegetacion) reflectancia [0, 1].
        gamma:   factor gamma para brightening (0.5 = visible mas brillante).
        enhance: si True (default), contrast stretch + unsharp (camino 1 km)
                 para compensar la falta de Rayleigh correction. Sin enhance
                 la imagen sale plana (std~15) vs RAMMB (std~66).
        pan:     reflectancia B2 nativa 0.5 km (Hh,Wh ≈ 2x). None = 1 km clasico.
        detail_weight: ganancia del detalle pan inyectado (default 1.0).

    Devuelve uint8 (H, W, 3) RGB. Con pan, (H,W) es el grid del pan.
    """
    if pan is None:
        rgb = _true_color_lr_float(refl_b1, refl_b2, refl_b3, gamma, enhance,
                                   do_unsharp=True)
        return (rgb * 255).astype(np.uint8)
    rgb_lo = _true_color_lr_float(refl_b1, refl_b2, refl_b3, gamma, enhance,
                                  do_unsharp=False)
    return _pansharpen(rgb_lo, pan, gamma, enhance, detail_weight)


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
