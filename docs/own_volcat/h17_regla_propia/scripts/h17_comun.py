r"""H17: piezas comunes. Ventana L1b (la del detector, 83 x 94 pixeles de 2 km, y0=4497 x0=2820), lat/lon, cachés
existentes de solo lectura (H9: C07+C14; H3, beta73, E2, H13, etapa 3: C10/C11/C14/C15) y el caché propio de H17
(D:\goes_cache\h17\l1b, bandas que faltaban). Nada de esto toca src/ ni el dashboard.
"""
import os
import glob
import json

import numpy as np

H17 = os.environ.get("H17_DIR", r"D:\goes_cache\h17")
L1B17 = os.path.join(H17, "l1b")
DET = r"D:\goes_notas\local_f3a7d295\cache_rescatada\reproducir_volcat"
WIN = json.load(open(os.path.join(DET, "window.json")))
_ll = np.load(os.path.join(DET, "latlon.npz"))
LAT, LON = _ll["lat"], _ll["lon"]
B73 = r"D:\goes_cache\h13\shim\b73"
EVDIR = r"D:\goes_notas\busqueda_2026-11-20\volcat_eventos_357070"
E3INV = r"D:\goes_cache\etapa3_chillan\inventario.npz"
C07H9 = r"D:\goes_notas\scratch_rescate_2026-11-21\h9_calor_rayos_11c46882\c07cache"
CACHES_IR = [r"D:\goes_cache\h13\cache", r"D:\goes_cache\h13\shim\h3\cache", r"D:\goes_cache\h13\shim\b73\cache",
             r"D:\goes_cache\h13\shim\rv\cache_e2", r"D:\goes_cache\etapa3_chillan\l1b"]

# Catalogo del proyecto (src/volcanos.py, igual que H9): lat, lon, cumbre en m
SITIOS = {"chillan": (-36.86, -71.38, 3212), "antuco": (-37.41, -71.35, 2979), "longavi": (-36.19, -71.16, 3242)}


def k(dt):
    return f"{dt:%Y%m%d_%H%M}"


def indice():
    """{clave: {banda: ruta}} con todo lo que hay en disco. El caché propio de H17 manda sobre los demás."""
    idx = {}
    for f in glob.glob(os.path.join(L1B17, "*.npz")):
        c = os.path.basename(f)[:13]
        with np.load(f) as z:
            for n in z.files:
                if n.startswith("rad"):
                    idx.setdefault(c, {})[int(n[3:])] = f
    for f in glob.glob(os.path.join(C07H9, "*.npz")):
        c = os.path.basename(f)[:13]
        for b in (7, 14):
            idx.setdefault(c, {}).setdefault(b, f)
    for d in CACHES_IR:
        for f in glob.glob(os.path.join(d, "*.npz")):
            c = os.path.basename(f)[:13]
            for b in (10, 11, 14, 15):
                idx.setdefault(c, {}).setdefault(b, f)
    return idx


def bt(rad, co):
    fk1, fk2, bc1, bc2 = co
    with np.errstate(invalid="ignore", divide="ignore"):
        return (fk2 / np.log(fk1 / rad + 1.0) - bc1) / bc2


def banda(idx, c, b):
    """(radiancia, coeficientes Planck del NetCDF) de la banda b del cuadro c, o None."""
    f = idx.get(c, {}).get(b)
    if f is None:
        return None
    with np.load(f) as z:
        return z[f"rad{b}"].astype("float64"), tuple(float(x) for x in z[f"co{b}"])


def hav(lat, lon, la0, lo0):
    p1, p2 = np.radians(la0), np.radians(lat)
    a = np.sin((p2 - p1) / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(np.radians(lon - lo0) / 2) ** 2
    return 2 * 6371.0 * np.arcsin(np.sqrt(a))


def dist_cumbre(sitio):
    """km a la cumbre corrida por paralaje (ABI navega al elipsoide: 0,93 km al sur por km de altura, como H9)."""
    la, lo, h = SITIOS[sitio]
    return hav(LAT, LON, la - 0.93 * h / 1000.0 / 111.2, lo)


def area_pixel():
    """km² por pixel desde la grilla lat/lon (igual que H16)."""
    R = 6371.0
    la, lo = np.radians(LAT), np.radians(LON)
    dly, dlx = np.gradient(la)
    doy, dox = np.gradient(lo)
    c = np.cos(la)
    return np.abs(R * dlx * R * c * doy - R * c * dox * R * dly)
