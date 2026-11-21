r"""Nube tenue, exploración 6 (SÓLO cuadros 1 a 5, nivel A; no decide).

La exploración 5 mostró que en εtot < 0,2 (sin tablas de 8,5) VOLCAT − (tot + op [+ low + mid]) es una constante por
casillero de εtot: +2,4089 en [0,03; 0,10) y −0,0985 en [0,01; 0,03) (y εtot < 0,01 se comporta como el primer
casillero). Aquí se calcula, para cada tabla y superficie agua, el factor que queda al sumar (marginalizar) los ejes
que no son εtot: m(εtot) = ln(ΣA / ΣC). Si la constante es suma de algunos m, la regla es "la tabla cuyo β falta o
no se usa entra con su marginal de εtot".
Salida: ../resultados/nt_explorar6.txt
"""
import itertools
import os
import sys

import numpy as np

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nt_comun as N  # noqa: E402

LV = N.LV
out = open(os.path.join(N.RES, "nt_explorar6.txt"), "w", encoding="utf-8")


def p(*a):
    print(*a); print(*a, file=out, flush=True)


T = N.tablas()
TODAS = LV.IR_S1 + LV.IR_8511
objetivo = {0: -0.0985, 1: 2.4089}
M = {}
for sup in ("WATER", "LAND"):
    p(f"Superficie {sup}: marginal de εtot ln(ΣA/ΣC) por casillero 0..5")
    for base, ejes in TODAS:
        A, C = T.par(base, sup)
        A = A.reshape(A.shape[:len(ejes)]); C = C.reshape(C.shape[:len(ejes)])
        ie = [k for k, (e, _) in enumerate(ejes) if e == "eps"][0]
        ax = tuple(k for k in range(len(ejes)) if k != ie)
        m = np.log(A.sum(axis=ax)) - np.log(C.sum(axis=ax))
        M[(sup, base)] = m
        p(f"  {base:40s} " + " ".join(f"{x:+.4f}" for x in m))
        # para la tabla de BTD, además marginal sólo sobre BTD (queda εtot × BT11 despejado)
        if "BTD" in base:
            m2 = np.log(A.sum(axis=0)) - np.log(C.sum(axis=0))   # (eps, btclr)
            for j in range(m2.shape[1]):
                p(f"     BTD marginalizada, btclr bin {j}: " + " ".join(f"{x:+.4f}" for x in m2[:, j]))

p("\nCombinaciones de marginales (agua) que dan el objetivo en los casilleros 0 y 1 (tolerancia 1e-3):")
nombres = [b for b, _ in TODAS]
for r in range(1, 5):
    for comb in itertools.combinations(nombres, r):
        for signos in itertools.product([1, -1], repeat=r):
            s0 = sum(sg * M[("WATER", b)][0] for sg, b in zip(signos, comb))
            s1 = sum(sg * M[("WATER", b)][1] for sg, b in zip(signos, comb))
            if abs(s0 - objetivo[0]) < 1e-3 and abs(s1 - objetivo[1]) < 1e-3:
                p(f"  {r}: " + " ".join(f"{'+' if sg>0 else '-'}{b}" for sg, b in zip(signos, comb)))
out.close()
