r"""Revision H13/H17 (S19e): piezas comunes. Mascara de nubes de NOAA (ABI-L2-ACMF) ya bajada por H23 y H24 en la
ventana del detector (y0 4497, x0 2820, 83 x 94), terreno bajo y cumbre de Chillan con la definicion de H23
(h23_medir.grupos), y estado de escena por cuadro. Criterio: ../criterio_2026-11-23.md. Solo lectura de D:.
"""
import os

import numpy as np

ACM_DIRS = [r"D:\goes_notas\s17\h23\acm", r"D:\goes_notas\s18\h24\acm"]
LATLON = r"D:\goes_notas\local_f3a7d295\cache_rescatada\reproducir_volcat\latlon.npz"
DEM = r"D:\goes_cache\etapa3_chillan\dem_ventana.npz"
SALIDA = os.environ.get("REV_DIR", r"D:\goes_notas\s19\revision_h13_h17")
FRAC_DESPEJADO = 0.80          # escena despejada: >= 80 % del terreno bajo con ACM 0 o 1 (H23 E1, H24)
CHILLAN = (-36.86, -71.38, 3212)

_ll = np.load(LATLON)
LAT, LON = _ll["lat"], _ll["lon"]
ZDEM = np.load(DEM)["zdem"]


def hav(lat, lon, la0, lo0):
    p1, p2 = np.radians(la0), np.radians(lat)
    a = np.sin((p2 - p1) / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(np.radians(lon - lo0) / 2) ** 2
    return 2 * 6371.0 * np.arcsin(np.sqrt(a))


def grupos():
    """Igual que h23_medir.grupos('chillan'), en indices 2D."""
    la, lo, h = CHILLAN
    d = hav(LAT, LON, la - 0.93 * h / 1000.0 / 111.2, lo)
    cerca = np.argwhere(d <= 6.0)
    z = ZDEM[cerca[:, 0], cerca[:, 1]]
    cumbre = np.zeros(LAT.shape, bool)
    for y, x in cerca[np.argsort(z)[::-1][:6]]:
        cumbre[y, x] = True
    bajo = (d >= 10.0) & (d <= 30.0) & (ZDEM < 1300.0)
    return cumbre, bajo


CUMBRE, BAJO = grupos()
_cache = {}


def acm(clave):
    """Arreglo ACM (0..3, 255 sin dato) del cuadro, o None si no hay archivo."""
    if clave in _cache:
        return _cache[clave]
    a = None
    for d in ACM_DIRS:
        f = os.path.join(d, clave + ".npz")
        if os.path.exists(f):
            with np.load(f) as z:
                a = z["acm"].copy()
            break
    _cache[clave] = a
    return a


def estado(clave):
    """(hay_acm, frac_bajo_despejado, escena_despejada, frac_cumbre_despejada). Sin archivo = no despejado."""
    a = acm(clave)
    if a is None:
        return False, np.nan, False, np.nan
    desp = a <= 1
    fb = float(desp[BAJO].mean())
    return True, fb, fb >= FRAC_DESPEJADO, float(desp[CUMBRE].mean())
