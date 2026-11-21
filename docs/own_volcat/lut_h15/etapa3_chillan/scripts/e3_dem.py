r"""H15 etapa 3: cota del terreno vista por cada píxel de la ventana (para corregir el cielo despejado por cota).

Por qué: C2b (Mauna Loa) mostró que el cielo despejado de VOLCAT baja con la cota fina de cada píxel dentro de la
celda del GFS; el nuestro usa la superficie del GFS (0,25°), que pone la cumbre de Chillán a 1,5 a 1,9 km y la deja
7 a 9 K más tibia (H11). Aquí cada celda del modelo de elevación Terrarium (zoom 9, ~250 m) se proyecta CON su
altura sobre la grilla fija del ABI de GOES-19 (paralaje: a 3 km de altura el terreno aparece ~1 píxel más lejos
del satélite) y se promedia por píxel. Misma geometría que mauna_loa_c2b/scripts/c2b_medir.py.

Comprobación previa: las lat/lon de la ventana a altura 0 tienen que volver a su fila y columna.
Salida: E3_DIR\dem_ventana.npz (zdem, m; n de celdas por píxel). Uso: python -I e3_dem.py
"""
import glob
import json
import os
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import e3_comun as K  # noqa: E402
import h13_comun as H  # noqa: E402
import fetch_e2 as F  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
C = H.C
# Proyección del ABI full disk 2 km de GOES-19 (atributos de goes_imager_projection y de x / y en la L1b RadF)
G = dict(a=6378137.0, b=6356752.31414, h=35786023.0, lon0=-75.0,
         x_sc=5.6e-05, x_of=-0.151844, y_sc=-5.6e-05, y_of=0.151844)


def escaneo(lat, lon, h):
    a, b = G["a"], G["b"]; e2 = 1 - (b / a) ** 2
    la = np.radians(lat); dl = np.radians(lon - G["lon0"])
    N = a / np.sqrt(1 - e2 * np.sin(la) ** 2)
    X = (N + h) * np.cos(la) * np.cos(dl); Y = (N + h) * np.cos(la) * np.sin(dl); Z = (N * (1 - e2) + h) * np.sin(la)
    sx, sy, sz = G["h"] + a - X, -Y, Z
    return np.arcsin(-sy / np.sqrt(sx ** 2 + sy ** 2 + sz ** 2)), np.arctan(sz / sx)


def fila_col(lat, lon, h):
    x, y = escaneo(lat, lon, h)
    return (y - G["y_of"]) / G["y_sc"] - F.WIN["y0"], (x - G["x_of"]) / G["x_sc"] - F.WIN["x0"]


def dem():
    lat, lon, el = [], [], []
    for f in sorted(glob.glob(os.path.join(K.DEM, "t9_*.png"))):
        _, x, y = os.path.basename(f)[:-4].split("_"); x, y = int(x), int(y)
        a = np.asarray(Image.open(f).convert("RGB"), "float64")
        e = a[..., 0] * 256 + a[..., 1] + a[..., 2] / 256 - 32768
        j, i = np.meshgrid(np.arange(256), np.arange(256))
        n = 2 ** 9
        lo = (x + (j + 0.5) / 256) / n * 360 - 180
        la = np.degrees(np.arctan(np.sinh(np.pi * (1 - 2 * (y + (i + 0.5) / 256) / n))))
        lat.append(la.ravel()); lon.append(lo.ravel()); el.append(e.ravel())
    return np.concatenate(lat), np.concatenate(lon), np.concatenate(el)


def main():
    ny, nx = C.LAT.shape
    r0, c0 = fila_col(C.LAT, C.LON, 0.0)
    iy, ix = np.mgrid[0:ny, 0:nx]
    err = float(np.nanmax(np.hypot(r0 - iy, c0 - ix)))
    print("comprobacion geometria: error maximo (pixeles) a altura 0 =", round(err, 4))
    assert err < 0.05, "la proyeccion no reproduce la ventana"
    la, lo, el = dem()
    el = np.maximum(el, 0.0)                      # mar a 0 m
    r, c = fila_col(la, lo, el)
    r, c = np.round(r).astype(int), np.round(c).astype(int)
    ok = (r >= 0) & (r < ny) & (c >= 0) & (c < nx)
    s = np.zeros((ny, nx)); n = np.zeros((ny, nx))
    np.add.at(s, (r[ok], c[ok]), el[ok]); np.add.at(n, (r[ok], c[ok]), 1)
    z = np.where(n > 0, s / np.maximum(n, 1), np.nan)
    np.savez_compressed(os.path.join(K.E3DIR, "dem_ventana.npz"), zdem=z, n=n)
    d = np.hypot((C.LAT - K.CRATER[0]) * 111.2, (C.LON - K.CRATER[1]) * 89.0)
    j = np.unravel_index(np.argmin(d), d.shape)
    res = {"error_geometria_px": round(err, 4), "celdas_por_pixel_min": int(n.min()), "celdas_por_pixel_med": float(np.median(n)),
           "pixeles_sin_dem": int((n == 0).sum()), "zdem_pixel_crater_m": round(float(z[j]), 0),
           "zdem_max_10km_m": round(float(np.nanmax(z[d <= 10])), 0),
           "zdem_p50_ventana_m": round(float(np.nanmedian(z)), 0)}
    json.dump(res, open(os.path.join(K.RES, "dem_ventana.json"), "w"), indent=1)
    print(res)


if __name__ == "__main__":
    main()
