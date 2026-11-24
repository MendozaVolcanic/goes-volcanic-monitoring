r"""S21a2, descripcion de la mascara antes de medir (solo reflectancia y geometria; no lee GOES).

De donde sale la suma de f de la poblacion de S20b en cada pasada: componentes conexas de la mascara (ya corrida por
paralaje del sensor fino), con su area, distancia minima y del centroide al crater, azimut, fraccion de sus celdas a
3 celdas o menos de terreno sin nieve de referencia (borde de nieve) y cuanto aportan a la poblacion (f >= 0,02 fuera
del bloque del crater) y al bloque. Tambien la variante informativa "nucleo" de la enmienda 1: solo componentes con
su celda mas cercana a <= R km del crater, R = 4, 5, 6 y 8 km.

Uso: python -I s21a2_componentes.py   (despues de `s21a2_correr.py preparar`)
"""
import json
import math
import os
import sys

import numpy as np
from scipy import ndimage

sys.stdout.reconfigure(encoding="utf-8")
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(AQUI, "..", "..", "s20b_verdad_alta_res", "scripts")))
import s20b_comun as C  # noqa: E402

C.TRABAJO = r"D:\goes_notas\s21\a2"
RES = os.path.join(os.path.dirname(AQUI), "resultados")
F_PESO = 0.02


def main():
    area = C.area_pixel_km2()
    d = C.hav(C.GLAT, C.GLON, *C.CRATER)
    out = {}
    for dia in ("2026-10-29", "2026-11-13"):
        z = np.load(os.path.join(C.TRABAJO, f"mascara_{dia}.npz"))
        pl, H, bl, nieve = z["pluma_vista"], float(z["H"]), z["bloque"], z["nieve"]
        pob = (z["f"] >= F_PESO) & ~bl
        lab, n = ndimage.label(pl, structure=np.ones((3, 3)))
        tam = ndimage.sum(pl, lab, range(1, n + 1))
        dmin = ndimage.minimum(d, lab, range(1, n + 1))
        borde = ndimage.binary_dilation(~nieve, iterations=3)
        comps = []
        for i in np.argsort(-tam)[:15]:
            m = lab == i + 1
            fi = C.acumular(m, H) / area
            e, nn = C.GX[m].mean() - C.CX, C.GY[m].mean() - C.CY
            comps.append({"km2": round(float(tam[i]) * C.RES_M ** 2 / 1e6, 3), "dmin_km": round(float(dmin[i]), 1),
                          "dcentroide_km": round(math.hypot(e, nn) / 1000, 1),
                          "azimut": round(math.degrees(math.atan2(e, nn)) % 360),
                          "frac_borde_nieve": round(float(borde[m].mean()), 2),
                          "suma_f_en_poblacion": round(float(fi[pob].sum()), 3),
                          "f_en_bloque": round(float(fi[bl].sum()), 3)})
        nucleo = {}
        for R in (4, 5, 6, 8):
            keep = np.zeros(n + 1, bool)
            keep[1:] = dmin <= R
            m = keep[lab]
            r = {"km2": round(float(m.sum()) * C.RES_M ** 2 / 1e6, 3), "componentes": int(keep.sum())}
            for etq, hh in (("H", H), ("H-1km", H - 1000), ("H+1km", H + 1000)):
                f = C.acumular(m, hh) / area
                p = (f >= F_PESO) & ~bl
                r[etq] = {"suma_f_poblacion": round(float(f[p].sum()), 3), "pixeles": int(p.sum()),
                          "f_max_fuera_bloque": round(float(f[~bl].max()), 3), "f_bloque": round(float(f[bl].sum()), 3)}
            nucleo[f"R{R}km"] = r
        out[dia] = {"componentes_total": int(n), "suma_f_poblacion_regla": round(float(z["f"][pob].sum()), 3),
                    "mayores_15": comps, "nucleo": nucleo}
        print(dia, json.dumps({"n": n, "nucleo": {k: v["H"] for k, v in nucleo.items()}}, ensure_ascii=False))
    with open(os.path.join(RES, "componentes.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
