r"""Nube tenue: el primer cuadro (09:16), posterior a la validación, no decide.

nt_por_cuadro.txt mostró que todo el residuo de 8,5 µm de la exploración está en el cuadro 09:16, el primero de la
serie. La configuración de VOLCAT trae "Restricted use of 8.5 um for pixel probabilities when no temporal data are
available (0: no restrictions, 1: restrict use under some circumstances, 2: do not use at all)": en el primer cuadro
no hay cuadro anterior. Aquí, sólo en 09:16, qué píxeles evalúa VOLCAT con y sin las tablas de 8,5 µm, y si una
regla simple con los umbrales de la tabla (εtot < 0,1, ε73 < 0,05) los separa.
Salida: ../resultados/nt_cuadro1.txt
"""
import os
import sys

import numpy as np

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nt_comun as N  # noqa: E402
import nt_regla as R  # noqa: E402

E = N.E
ent, agua, v, q = N.cargar(["091600"])
lv = N.logit(v); sat = N.no_saturado(v)
C2 = R.contribuciones(ent, agua, r2=True)
L = R.logit_regla(C2, ent, r1=True)
c85 = C2[:, R.J85].sum(1)
inf = sat & (np.abs(c85) > 1e-3)
con = inf & (np.abs(L - lv) < 1e-3)
sin = inf & (np.abs(L - c85 - lv) < 1e-3) & ~con
e73 = R.eps73(ent); eps = ent["eps"]; b85 = ent["b85"]
falta = ~np.isfinite(e73)
with open(os.path.join(N.RES, "nt_cuadro1.txt"), "w", encoding="utf-8") as f:
    def p(*a):
        print(*a); print(*a, file=f, flush=True)
    p(f"09:16, informativos: con 8,5 {con.sum()}, sin 8,5 {sin.sum()}")
    for ce, cm in (("eps<0,1", eps < 0.1), ("eps>=0,1", eps >= 0.1)):
        for c3, m3 in (("e73>=0,05", ~falta & (e73 >= 0.05)), ("e73<0,05", ~falta & (e73 < 0.05)), ("e73 falta", falta)):
            p(f"  {ce:8s} {c3:10s}: con {(con & cm & m3).sum():6d}  sin {(sin & cm & m3).sum():6d}")
    reglas = {
        "eps<0,1 & franja (R3)": (eps < 0.1) & (b85 > 1.05) & (b85 < 2.0),
        "eps<0,1": eps < 0.1,
        "eps<0,1 o e73<0,05 o falta": (eps < 0.1) | falta | (e73 < 0.05),
        "e73<0,05 o falta": falta | (e73 < 0.05),
    }
    for nom, om in reglas.items():
        p(f"  omite si {nom:28s}: acierta con {np.mean(~om[con]):.4f}  sin {np.mean(om[sin]):.4f}")
