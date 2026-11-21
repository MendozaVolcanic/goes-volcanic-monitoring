r"""Nube tenue: comprobación por cuadro (posterior a la validación, no decide).

La validación dio 99,96 % exacto en εtot < 0,2 en los cuadros 6 a 10, contra 93,6 % en los cuadros 1 a 5 de la
exploración con la misma regla. Para saber si es un artefacto, aquí la regla NT idéntica (nt_validar.cond85) en los
10 cuadros, uno por uno: fracción exacta por tramo y cuántos píxeles no exactos se arreglan quitando las tablas de
8,5 µm (el residuo declarado en el criterio).
Salida: ../resultados/nt_por_cuadro.txt
"""
import os
import sys

import numpy as np

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nt_comun as N  # noqa: E402
import nt_regla as R  # noqa: E402
from nt_validar import cond85  # noqa: E402

E = N.E
with open(os.path.join(N.RES, "nt_por_cuadro.txt"), "w", encoding="utf-8") as f:
    def p(*a):
        print(*a); print(*a, file=f, flush=True)
    p("cuadro | tramo: no saturados, exacta NT, no exactos que se arreglan sin 8,5, no exactos con εtot<0,1 fuera de la franja de β85")
    for h in E.HORAS:
        ent, agua, v, q = N.cargar([h])
        lv = N.logit(v); sat = N.no_saturado(v)
        C2 = R.contribuciones(ent, agua, r2=True)
        c = cond85(ent)
        L = R.logit_regla(C2, ent, r1=True, cond85=c)
        c85 = np.where(c, C2[:, R.J85].sum(1), 0.0)
        ok = np.abs(L - lv) < 1e-3
        arr = np.abs(L - c85 - lv) < 1e-3
        eps = ent["eps"]
        fila = []
        for tn, a, b in (("<0,2", -np.inf, 0.2), ("0,2-0,5", 0.2, 0.5), (">=0,5", 0.5, np.inf)):
            s = sat & (eps >= a) & (eps < b)
            mal = s & ~ok
            fila.append(f"{tn}: {s.sum():6d} {ok[s].mean():.4f} {(mal & arr).sum():5d} {(mal & (eps < 0.1)).sum():5d}")
        p(f"{h} ({'elige' if h in E.ELIGE else 'valida'}) | " + " | ".join(fila))
