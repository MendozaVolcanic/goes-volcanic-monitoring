r"""Nube tenue: cuánto aporta R2 (β multicapa ausente evaluado en el primer casillero), por casillero de εtot y
superficie. Es lo que VOLCAT suma al log-odds de ceniza en un píxel sin nube inferior identificada, aparte de lo que
digan los demás predictores. Posterior, no decide; sirve para leer qué implica la regla en tierra (Chillán) aunque
en Mauna Loa (98,7 % mar) sólo se validó en agua.
Salida: ../resultados/nt_r2_empuje.txt
"""
import os
import sys

import numpy as np

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nt_comun as N  # noqa: E402

LV = N.LV
T = N.tablas()
with open(os.path.join(N.RES, "nt_r2_empuje.txt"), "w", encoding="utf-8") as f:
    def p(*a):
        print(*a); print(*a, file=f)
    ed = LV.EPS_EDGES
    p("Aporte en log-odds de MULTI_LOW + MULTI_MID con β en el primer casillero, por casillero de εtot")
    p("casillero εtot: " + " | ".join(f"[{ed[i]:.2f},{ed[i+1]:.2f})" for i in range(6)))
    for sup in ("WATER", "LAND"):
        tot = np.zeros(6)
        for base in ("EMISS14_TOT_BETA1112_TOT_MULTI_LOW_IR", "EMISS14_TOT_BETA1112_TOT_MULTI_MID_IR"):
            A, C = T.par(base, sup)
            r = np.log(A[0, :, 0]) - np.log(C[0, :, 0])
            tot += r
            p(f"  {sup:5s} {base[-12:]:12s}: " + " | ".join(f"{x:+.3f}" for x in r))
        p(f"  {sup:5s} suma        : " + " | ".join(f"{x:+.3f}" for x in tot) + "   (factor sobre la razón de odds: "
          + ", ".join(f"{np.exp(x):.2f}" for x in tot) + ")")
