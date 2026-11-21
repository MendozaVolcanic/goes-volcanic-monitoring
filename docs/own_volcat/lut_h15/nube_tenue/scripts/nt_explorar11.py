r"""Nube tenue, exploración 11 (SÓLO cuadros 1 a 5, nivel A; no decide).

Dentro de εtot < 0,1: tabla cruzada de los píxeles informativos (las tablas de 8,5 aportan) que VOLCAT evalúa con
8,5 ("con") o sin 8,5 ("sin"), por franjas de β(8,5/11) total y opaco, para ver si la omisión fuera de la franja
1,05 a 2,0 sigue otra variable de la tabla. También ε(8,5) = 1 − (1 − εtot)^β85.
Salida: ../resultados/nt_explorar11.txt
"""
import os
import sys

import numpy as np

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nt_comun as N  # noqa: E402
import nt_regla as R  # noqa: E402

LV, E = N.LV, N.E
out = open(os.path.join(N.RES, "nt_explorar11.txt"), "w", encoding="utf-8")


def p(*a):
    print(*a); print(*a, file=out, flush=True)


ent, agua, v, q = N.cargar(E.ELIGE)
lv = N.logit(v)
sat = N.no_saturado(v)
eps = ent["eps"]
C2 = R.contribuciones(ent, agua, r2=True)
c85 = C2[:, R.J85].sum(1)
inf = sat & (np.abs(c85) > 1e-3)
L12 = R.logit_regla(C2, ent, r1=True)
con = inf & (np.abs(L12 - lv) < 1e-3)
sin = inf & (np.abs(L12 - c85 - lv) < 1e-3) & ~con
cortes = [-np.inf, 0.0, 0.5, 0.8, 1.0, 1.05, 1.2, 1.5, 2.0, np.inf]
for nomv, x in (("b85", ent["b85"]), ("b85op", ent["b85op"])):
    for tn, a, b in (("eps<0,1", 0, 0.1), ("eps 0,1-0,2", 0.1, 0.2), ("eps 0,2-0,5", 0.2, 0.5)):
        s = (eps >= a) & (eps < b)
        p(f"{nomv} en {tn}:")
        for i in range(len(cortes) - 1):
            k = s & (x >= cortes[i]) & (x < cortes[i + 1])
            p(f"   [{cortes[i]:+.2f},{cortes[i+1]:+.2f}): con {(k & con).sum():6d}  sin {(k & sin).sum():6d}")
with np.errstate(all="ignore"):
    e85 = 1 - (1 - eps) ** ent["b85"]
s = eps < 0.1
p("ε85 en eps<0,1: con p0/5/50/95/100", np.nanpercentile(e85[s & con], [0, 5, 50, 95, 100]).round(4),
  " sin", np.nanpercentile(e85[s & sin], [0, 5, 50, 95, 100]).round(4))
fuera = s & ~((ent["b85"] > 1.05) & (ent["b85"] < 2.0))
p(f"eps<0,1 fuera de la franja: con {(fuera & con).sum()} sin {(fuera & sin).sum()}")
for k, x in (("eps", eps), ("b85", ent["b85"]), ("b85op", ent["b85op"]), ("b_tot", ent["b_tot"]), ("b_op", ent["b_op"]),
             ("btd", ent["btd"]), ("bt10-clr10", ent["bt10"] - ent["clr10"]), ("e85", e85)):
    p(f"   {k:10s} fuera/con {np.nanpercentile(x[fuera & con], [0, 5, 50, 95, 100]).round(3)} | fuera/sin {np.nanpercentile(x[fuera & sin], [0, 5, 50, 95, 100]).round(3)}")
out.close()
