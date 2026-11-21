r"""Nube tenue, exploración 7 (SÓLO cuadros 1 a 5, nivel A; no decide).

Hipótesis desde la exploración 5: cuando VOLCAT no tiene β multicapa (b_low o b_mid NaN, no hay nube inferior
identificada) no omite esa tabla: la evalúa con un β de reemplazo fijo. El desfase constante por casillero de εtot
(+2,4089 en [0,03; 0,10), −0,0985 en [0,01; 0,03)) sería la suma de las dos tablas multicapa en ese casillero de β.
Aquí: para cada casillero k de β, la contribución de MULTI_LOW + MULTI_MID con β = k, por casillero de εtot, y se
busca k que dé el desfase. Luego se mide cuántos píxeles de εtot < 0,2 quedan exactos con esa regla, con y sin las
tablas de 8,5 µm y 7,3 µm.
Salida: ../resultados/nt_explorar7.txt
"""
import itertools
import os
import sys

import numpy as np

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nt_comun as N  # noqa: E402

LV, E = N.LV, N.E
out = open(os.path.join(N.RES, "nt_explorar7.txt"), "w", encoding="utf-8")


def p(*a):
    print(*a); print(*a, file=out, flush=True)


T = N.tablas()
lo, db, nb = LV.EJES["b1112"]
for sup in ("WATER", "LAND"):
    r = {}
    for base in ("EMISS14_TOT_BETA1112_TOT_MULTI_LOW_IR", "EMISS14_TOT_BETA1112_TOT_MULTI_MID_IR",
                 "EMISS14_TOT_BETA1112_TOT_IR", "EMISS14_TOT_BETA1112_OPAQUE_IR"):
        A, C = T.par(base, sup)
        r[base] = (np.log(A[..., 0]) - np.log(C[..., 0]))     # (42 β, 6 eps)
    s = r["EMISS14_TOT_BETA1112_TOT_MULTI_LOW_IR"] + r["EMISS14_TOT_BETA1112_TOT_MULTI_MID_IR"]
    p(f"{sup}: low+mid por casillero de β (filas con |s[:,1] − 2,4089| < 0,01 o |s[:,0] + 0,0985| < 0,01)")
    for k in range(nb):
        marca = ""
        if abs(s[k, 1] - 2.4089) < 0.01 or abs(s[k, 0] + 0.0985) < 0.01:
            marca = "  <=="
        if sup == "WATER" or marca:
            p(f"  k={k:2d} β=[{lo + k*db:+.2f},{lo+(k+1)*db:+.2f}) low " + " ".join(f"{x:+.3f}" for x in r['EMISS14_TOT_BETA1112_TOT_MULTI_LOW_IR'][k])
              + " | mid " + " ".join(f"{x:+.3f}" for x in r['EMISS14_TOT_BETA1112_TOT_MULTI_MID_IR'][k]) + marca)
out.close()
