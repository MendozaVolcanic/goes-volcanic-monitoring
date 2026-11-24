r"""S21e, diagnostico de cobertura del ensayo en seco (despues del seco, sin leer los positivos): por que hay tan
pocos cuadros placebo despejados que se puedan evaluar entre 12:20 y 16:50 UTC. Cuenta, por cuadro despejado, la
fraccion de Z con M1 y con B. Uso: python -I s21e_diag_cobertura.py
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import s21e_medir as S  # noqa: E402

M, E1, _ = S.cargar()
det = S.Detector(M.bt11, M.btd, E1)
filas = []
for d in S.PLACEBO:
    for x in range(S.slot("12:20"), S.slot("16:50") + 1):
        if not E1[d, x]:
            continue
        m1 = det.m1_cuadro(d, x)
        b = det.base(x)[0]
        Dv = m1 - b
        filas.append((S.fecha(d), S.hhmm(x), np.isfinite(m1).mean(), np.isfinite(b).mean(), np.isfinite(Dv).mean()))
print("cuadros placebo E1 en 12:20-16:50:", len(filas))
for f in filas:
    print(f"{f[0]} {f[1]}  M1 {f[2]:.2f}  B {f[3]:.2f}  D {f[4]:.2f}")
bs = [np.isfinite(det.base(x)[0]).mean() for x in range(S.slot("12:20"), S.slot("16:50") + 1)]
print("fraccion de Z con B por cuadro de 12:20 a 16:50:", [round(v, 2) for v in bs])
