r"""S21c, paso 0 del criterio (§4): verifica la navegacion de GOES-18 y GOES-19 contra el terreno.

Simula el C02 de cada satelite con la banda roja de Sentinel-2 del 16-10 (grilla local de S20b, 30 m, +-20 km),
llevando cada celda al pixel donde la ve el satelite a la altura del DEM, y busca el corrimiento que maximiza la
correlacion con el C02 real (16-10 14:40 y 28-10 14:40). Salida: resultados/registro.json y registro.txt.
"""
import json
import os
import sys
from datetime import datetime

import numpy as np
from pyproj import Transformer
from scipy import ndimage

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import s21c_comun as K  # noqa: E402

S2 = r"D:\goes_notas\s20b\S2C_19HBV_20261016_0_L2A.npz"
DEM = r"D:\goes_notas\s20b\dem_local.npy"
CRATER_S20B = (-36.863, -71.377)          # centro de la grilla local de S20b (s20b_comun.CRATER)
RES_M, MEDIO_M = 30.0, 20000.0
CUADROS = [datetime(2026, 10, 16, 14, 40), datetime(2026, 10, 28, 14, 40)]


def grilla():
    t = Transformer.from_crs(4326, "EPSG:32719", always_xy=True)
    cx, cy = t.transform(CRATER_S20B[1], CRATER_S20B[0])
    n = int(2 * MEDIO_M / RES_M)
    xx = cx - MEDIO_M + (np.arange(n) + 0.5) * RES_M
    yy = cy + MEDIO_M - (np.arange(n) + 0.5) * RES_M
    gx, gy = np.meshgrid(xx, yy)
    inv = Transformer.from_crs("EPSG:32719", 4326, always_xy=True)
    glon, glat = inv.transform(gx, gy)
    return glat, glon


def simular(sat, glat, glon, h, val, fila0, col0, n=81):
    r, c = K.a_pixel(sat, glat, glon, h)
    ri, ci = np.rint(r - fila0).astype(int), np.rint(c - col0).astype(int)
    ok = (ri >= 0) & (ri < n) & (ci >= 0) & (ci < n) & np.isfinite(val)
    suma, cuenta = np.zeros((n, n)), np.zeros((n, n))
    np.add.at(suma, (ri[ok], ci[ok]), val[ok])
    np.add.at(cuenta, (ri[ok], ci[ok]), 1)
    img = np.where(cuenta > 0, suma / np.maximum(cuenta, 1), np.nan)
    # relleno de huecos chicos y suavizado (respuesta del detector aproximada, gaussiana de 0,5 px)
    cob = cuenta >= max(5, np.percentile(cuenta[cuenta > 0], 10) * 0.3)
    base = np.where(cob, img, 0.0)
    w = ndimage.gaussian_filter(cob.astype(float), 0.5)
    sim = ndimage.gaussian_filter(base, 0.5) / np.where(w > 0, w, np.nan)
    return sim, cob


def correlacion(sim, cob, real, paso=0.25, rango=6.0):
    mejor = (-2, 0, 0)
    tabla = []
    for dr in np.arange(-rango, rango + 1e-9, paso):
        for dc in np.arange(-rango, rango + 1e-9, paso):
            s = ndimage.shift(np.nan_to_num(sim), (dr, dc), order=1, mode="constant", cval=np.nan)
            m = ndimage.shift(cob.astype(float), (dr, dc), order=1, mode="constant", cval=0) > 0.99
            m &= np.isfinite(real) & np.isfinite(s)
            if m.sum() < 200:
                continue
            rr = np.corrcoef(s[m], real[m])[0, 1]
            tabla.append((dr, dc, rr))
            if rr > mejor[0]:
                mejor = (rr, dr, dc)
    return mejor, tabla


if __name__ == "__main__":
    glat, glon = grilla()
    z = np.load(S2)
    red = np.where(z["valido"] & ~z["nube"], z["red"], np.nan).astype(float)
    dem = np.load(DEM).astype(float)
    out, lineas = {}, []
    for sat in (18, 19):
        for dt in CUADROS:
            f = np.load(K.ruta_cuadro(sat, dt))
            real = f["rad"].astype(float) * float(f["kappa0"])
            real[f["dqf"] != 0] = np.nan
            fila0, col0 = int(f["fila0"]), int(f["col0"])
            res = {}
            for nombre, h in (("dem", dem), ("plano_3200", np.full_like(dem, 3200.0))):
                sim, cob = simular(sat, glat, glon, h, red, fila0, col0)
                (rr, dr, dc), _ = correlacion(sim, cob, real)
                res[nombre] = {"r": round(float(rr), 3), "dfila": float(dr), "dcol": float(dc),
                               "pix_cubiertos": int(cob.sum())}
                if nombre == "dem":
                    np.savez_compressed(os.path.join(K.TRABAJO, f"registro_sim_g{sat}_{dt:%Y%m%d_%H%M}.npz"),
                                        sim=sim, cob=cob, real=real)
            out[f"g{sat}_{dt:%Y%m%d_%H%M}"] = res
            lineas.append(f"GOES-{sat} {dt:%d-%m %H:%M}: con DEM r {res['dem']['r']}, corrimiento "
                          f"({res['dem']['dfila']:+.2f} filas, {res['dem']['dcol']:+.2f} col); terreno plano a 3,2 km "
                          f"r {res['plano_3200']['r']} ({res['plano_3200']['dfila']:+.2f}, {res['plano_3200']['dcol']:+.2f}); "
                          f"pixeles cubiertos {res['dem']['pix_cubiertos']}")
        a, b = out[f"g{sat}_20261016_1440"]["dem"], out[f"g{sat}_20261028_1440"]["dem"]
        dif = float(np.hypot(a["dfila"] - b["dfila"], a["dcol"] - b["dcol"]))
        ok = a["r"] >= 0.6 and b["r"] >= 0.6 and dif <= 1.0
        out[f"g{sat}_veredicto"] = {"verificada": bool(ok), "diferencia_px": round(dif, 2),
                                    "sesgo_filas": b["dfila"], "sesgo_col": b["dcol"]}
        lineas.append(f"GOES-{sat}: navegacion {'VERIFICADA' if ok else 'NO VERIFICADA'} (diferencia entre cuadros "
                      f"{dif:.2f} px); sesgo usado (28-10): {b['dfila']:+.2f} filas, {b['dcol']:+.2f} col")
    print("\n".join(lineas))
    base = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "resultados")
    with open(os.path.join(base, "registro.txt"), "w", encoding="utf-8") as fo:
        fo.write("\n".join(lineas) + "\n")
    with open(os.path.join(base, "registro.json"), "w", encoding="utf-8") as fo:
        json.dump(out, fo, indent=1)
