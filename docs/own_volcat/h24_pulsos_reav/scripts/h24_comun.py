# H24: copia de h23_comun.py con otra carpeta y otro bloque de dias.
r"""H23: piezas comunes. Ventana L1b del detector (83 x 94 pixeles de 2 km, la misma de H13 a H20), rutas y
conversiones de Planck. Todo lo que H23 escribe va a H23_DIR (por defecto D:\goes_notas\s18\h24); los caches de
otras pruebas se leen y no se tocan. Nada de esto toca src/ ni el dashboard.
"""
import os
from datetime import datetime, timedelta

import numpy as np

H23 = os.environ.get("H24_DIR", r"D:\goes_notas\s18\h24")
L1B = os.path.join(H23, "l1b")
GFS = os.path.join(H23, "gfs")
# Ventana del detector (window.json de reproducir_volcat): filas y columnas de la grilla fija ABI full disk 2 km
WIN = dict(y0=4497, y1=4580, x0=2820, x1=2914)
NY, NX = WIN["y1"] - WIN["y0"], WIN["x1"] - WIN["x0"]
# Insumos de solo lectura hechos por otras pruebas (no se modifican)
LATLON = r"D:\goes_notas\local_f3a7d295\cache_rescatada\reproducir_volcat\latlon.npz"
DEM = r"D:\goes_cache\etapa3_chillan\dem_ventana.npz"   # cota media por pixel con paralaje (H15 etapa 3, e3_dem.py)
# Catalogo del proyecto (src/volcanos.py): lat, lon, cumbre en m
SITIOS = {"chillan": (-36.86, -71.38, 3212), "antuco": (-37.41, -71.35, 2979), "longavi": (-36.19, -71.16, 3242)}

# Bloques de dias, decididos antes de medir y solo por cobertura (criterio, punto 3)
BLOQUE_OCT = (datetime(2026, 10, 24), datetime(2026, 10, 31))   # H24: hueco entre los cubos de H23
BLOQUE_NOV = BLOQUE_OCT   # H24: no se usa


def dias(bloque):
    d = bloque[0]
    while d <= bloque[1]:
        yield d
        d += timedelta(days=1)


def clave(dt):
    return f"{dt:%Y%m%d_%H%M}"


def bt_de_rad(rad, co):
    fk1, fk2, bc1, bc2 = co
    with np.errstate(invalid="ignore", divide="ignore"):
        return (fk2 / np.log(fk1 / rad + 1.0) - bc1) / bc2


def rad_de_bt(T, co):
    fk1, fk2, bc1, bc2 = co
    return fk1 / np.expm1(fk2 / (bc1 + bc2 * np.asarray(T, float)))


def hav(lat, lon, la0, lo0):
    p1, p2 = np.radians(la0), np.radians(lat)
    a = np.sin((p2 - p1) / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(np.radians(lon - lo0) / 2) ** 2
    return 2 * 6371.0 * np.arcsin(np.sqrt(a))
