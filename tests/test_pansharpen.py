"""Tests del pan-sharpening del GeoColor hi-res (1 km -> 0.5 km/px).

Fenomeno: B2 (rojo 0.64um) tiene 0.5 km/px nativo; B1/B3 solo 1 km. El
true-color a 1 km tira ese factor 2. El pan-sharpening (High-Pass
Modulation) toma el COLOR del RGB 1 km y le inyecta el DETALLE de alta
frecuencia de B2 a 0.5 km -> nitidez 0.5 km sin shift de color (el detalle
es de media cero).

Estos tests son sinteticos (numpy puro, sin descargar GOES). Verifican el
CONTRATO de `true_color_rgb(..., pan=...)`:
  - resolucion: salida al grid de pan (≈2x lineal de las bandas LR)
  - backward-compat: sin pan, comportamiento 1 km identico al anterior
  - color preservado: detalle media-cero no corre el balance de color
  - detalle inyectado: una estructura fina en pan ausente en LR aparece
"""

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.process.geocolor_lite import true_color_rgb


def _lr_bands(hl=24, wl=20):
    """Tres bandas LR suaves (gradientes), reflectancia [0,1]. Deterministico."""
    yy, xx = np.mgrid[0:hl, 0:wl].astype(np.float32)
    b1 = (0.2 + 0.5 * xx / wl).astype(np.float32)              # azul: gradiente horiz
    b2 = (0.3 + 0.4 * yy / hl).astype(np.float32)              # rojo: gradiente vert
    b3 = (0.25 + 0.3 * (xx + yy) / (hl + wl)).astype(np.float32)  # NIR: diagonal
    return b1, b2, b3


def _nn_upsample2x(arr):
    """Upsample nearest 2x (para construir un pan 'sin detalle nuevo')."""
    return np.repeat(np.repeat(arr, 2, axis=0), 2, axis=1)


def test_pansharpen_doubles_resolution():
    """Con pan a 2x, la salida tiene el shape de pan (0.5 km/px). EL test clave."""
    b1, b2, b3 = _lr_bands(24, 20)
    pan = _nn_upsample2x(b2)  # (48, 40), reflectancia
    out = true_color_rgb(b1, b2, b3, pan=pan)
    assert out.shape == (48, 40, 3), out.shape
    assert out.dtype == np.uint8
    assert out.min() >= 0 and out.max() <= 255


def test_pansharpen_none_is_backward_compatible():
    """Sin pan: shape y dtype del comportamiento 1 km de siempre (no rompe historic)."""
    b1, b2, b3 = _lr_bands(24, 20)
    out = true_color_rgb(b1, b2, b3)
    assert out.shape == (24, 20, 3), out.shape
    assert out.dtype == np.uint8


def test_pansharpen_zero_detail_preserves_color():
    """pan constante -> detalle = 0 -> salida = color LR re-escalado (brillo preservado).

    El detalle es de media cero (high-pass): un pan plano no debe cambiar el
    balance de color global. Comparamos la media por canal con el RGB LR
    re-escalado al mismo tamano.
    """
    b1, b2, b3 = _lr_bands(24, 20)
    pan = np.full((48, 40), 0.5, dtype=np.float32)  # campo plano
    out = true_color_rgb(b1, b2, b3, pan=pan)
    lr = true_color_rgb(b1, b2, b3)  # uint8 (24,20,3)

    out_mean = out.reshape(-1, 3).mean(axis=0)
    lr_mean = lr.reshape(-1, 3).mean(axis=0)
    # Tolerancia generosa: el resize bilineal y el clip pueden mover algun
    # nivel, pero el balance de color NO debe correrse (sin detalle).
    assert np.allclose(out_mean, lr_mean, atol=12), (out_mean, lr_mean)


def test_pansharpen_injects_high_frequency():
    """Un patron fino en pan (ausente en LR) debe subir la varianza local de la salida.

    Construyo pan = B2_upsampled + tablero de ajedrez fino. El RGB LR
    re-escalado (nearest) NO tiene ese detalle; el pan-sharpened SI ->
    desviacion estandar mayor.
    """
    b1, b2, b3 = _lr_bands(24, 20)
    base = _nn_upsample2x(b2)
    checker = np.indices((48, 40)).sum(axis=0) % 2  # 0/1 alternado por pixel
    pan = np.clip(base + 0.25 * checker, 0, 1).astype(np.float32)

    out = true_color_rgb(b1, b2, b3, pan=pan).astype(np.float64)
    # Referencia: LR re-escalado nearest, SIN inyeccion de detalle.
    lr = true_color_rgb(b1, b2, b3).astype(np.float64)
    plain = _nn_upsample2x(lr)

    assert out.std() > plain.std() + 1.0, (out.std(), plain.std())


def test_pansharpen_handles_odd_pan_dims():
    """pan con dimensiones impares no debe romper (se recorta a par)."""
    b1, b2, b3 = _lr_bands(24, 20)
    pan = np.full((49, 41), 0.4, dtype=np.float32)
    out = true_color_rgb(b1, b2, b3, pan=pan)
    # Recortado a par; sin crash, shape valido (H,W par, 3 canales)
    assert out.ndim == 3 and out.shape[2] == 3
    assert out.shape[0] % 2 == 0 and out.shape[1] % 2 == 0


def test_pansharpen_no_color_channel_swap():
    """Orden estricto R>G>B con bandas constantes distintas: discrimina un
    swap R<->G (green=0.45*b2+0.10*b3+0.45*b1 quedaria entre R y B)."""
    hl, wl = 16, 16
    b1 = np.full((hl, wl), 0.1, dtype=np.float32)   # azul bajo
    b2 = np.full((hl, wl), 0.9, dtype=np.float32)   # rojo alto
    b3 = np.full((hl, wl), 0.3, dtype=np.float32)   # green = 0.45*.9+.1*.3+.45*.1=.48
    pan = np.full((2 * hl, 2 * wl), 0.9, dtype=np.float32)
    out = true_color_rgb(b1, b2, b3, pan=pan)
    r, g, b = (out[..., 0].mean(), out[..., 1].mean(), out[..., 2].mean())
    # R (b2=0.9) > G (~0.48) > B (b1=0.1), con margen claro -> sin swap.
    assert r > g + 5 and g > b + 5, (r, g, b)


def test_pansharpen_nan_input_finite_no_warning():
    """NaN en pan/banda (fill/off-disk) -> salida uint8 finita SIN RuntimeWarning.

    Antes: un NaN anulaba el stretch de toda la imagen y NaN->uint8 tiraba
    'invalid value encountered in cast'. Ahora nanpercentile + nan_to_num.
    """
    import warnings

    b1, b2, b3 = _lr_bands(24, 20)
    b2 = b2.copy(); b2[3, 3] = np.nan          # NaN en banda
    pan = _nn_upsample2x(b2).copy(); pan[10, 10] = np.nan  # NaN en pan
    with warnings.catch_warnings():
        warnings.simplefilter("error", RuntimeWarning)  # cualquier warn -> falla
        out = true_color_rgb(b1, b2, b3, pan=pan)
    assert out.dtype == np.uint8 and out.shape == (48, 40, 3)
    # uint8 no puede ser NaN; verificamos que el cast produjo valores definidos
    assert out.min() >= 0 and out.max() <= 255


def test_pansharpen_detail_is_zero_mean():
    """El detalle high-pass (pan - box_lowpass) es de media ~cero (contrato).

    Cada bloque 2x2 aporta suma cero (resta de su propia media) -> media global
    ~0. Esto es lo que garantiza que el color/brillo del LR no se corra.
    """
    from src.process.geocolor_lite import _box_lowpass_2x, _stretch_single

    b1, b2, b3 = _lr_bands(24, 20)
    pan = _nn_upsample2x(b2)  # estructura real (no plano)
    pan_disp = _stretch_single(np.power(np.clip(pan, 0, 1), 0.5))
    detail = pan_disp - _box_lowpass_2x(pan_disp)
    assert abs(float(detail.mean())) < 1e-5, detail.mean()


def test_pan_none_survives_without_scipy(monkeypatch):
    """Path pan=None (historico) degrada con gracia si scipy falta (unsharp no-op)."""
    import sys

    monkeypatch.setitem(sys.modules, "scipy", None)
    monkeypatch.setitem(sys.modules, "scipy.ndimage", None)
    b1, b2, b3 = _lr_bands(16, 16)
    out = true_color_rgb(b1, b2, b3)  # usa unsharp_mask -> ImportError -> rgb tal cual
    assert out.shape == (16, 16, 3) and out.dtype == np.uint8


def test_pansharpen_survives_without_pil(monkeypatch):
    """Path pan: si PIL falta, _resize_rgb_bilinear cae a nearest-numpy (sin crash)."""
    import sys

    monkeypatch.setitem(sys.modules, "PIL", None)
    monkeypatch.setitem(sys.modules, "PIL.Image", None)
    b1, b2, b3 = _lr_bands(24, 20)
    pan = _nn_upsample2x(b2)
    out = true_color_rgb(b1, b2, b3, pan=pan)
    assert out.shape == (48, 40, 3) and out.dtype == np.uint8


if __name__ == "__main__":
    test_pansharpen_doubles_resolution()
    test_pansharpen_none_is_backward_compatible()
    test_pansharpen_zero_detail_preserves_color()
    test_pansharpen_injects_high_frequency()
    test_pansharpen_handles_odd_pan_dims()
    test_pansharpen_no_color_channel_swap()
    print("OK — pansharpen tests passed")
