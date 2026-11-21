r"""Nube tenue, exploración 5 (SÓLO cuadros 1 a 5, nivel A; no decide).

Tramo < 0,2, sin tablas de 8,5 µm (la exploración 4 muestra que P no depende de β(8,5/11) ahí). Para los grupos de
igual P se imprime el logit objetivo menos el prior (T) junto a la contribución de cada tabla de εtot × β y la
densidad de ceniza y de nube por separado, para ver qué combinación da T.
Salida: ../resultados/nt_explorar5.txt
"""
import os
import sys

import numpy as np

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nt_comun as N  # noqa: E402

LV, E = N.LV, N.E
out = open(os.path.join(N.RES, "nt_explorar5.txt"), "w", encoding="utf-8")


def p(*a):
    print(*a); print(*a, file=out, flush=True)


ent, agua, v, q = N.cargar(E.ELIGE)
sat = N.no_saturado(v)
s = sat & (ent["eps"] < 0.2)
T = N.logit(v) - N.L0
cuatro = N.SIETE[:4]
C = np.stack([N.contrib(ent, agua, t) for t in cuatro], 1)
lo, db, nb = LV.EJES["b1112"]
bb = lambda x: np.where(np.isfinite(x), np.clip(np.floor((x - lo) / db + 1e-9), 0, nb - 1), -9).astype(int)  # noqa
ie = np.searchsorted(LV.EPS_EDGES, ent["eps"], side="right") - 1
pv = np.round(v, 7)
vals, cnt = np.unique(pv[s], return_counts=True)
p("grupo: n | eps bin | casilleros b_tot b_op b_low b_mid | T | contrib tot op low mid | suma | T − suma")
for k in np.argsort(-cnt)[:40]:
    m = s & (pv == vals[k])
    i = np.where(m)[0][0]
    c = C[i]
    p(f"P={vals[k]:.7f} n={cnt[k]:5d} | e{ie[i]} ({ent['eps'][i]:.3f}) | {bb(ent['b_tot'][i:i+1])[0]:3d} {bb(ent['b_op'][i:i+1])[0]:3d} "
      f"{bb(ent['b_low'][i:i+1])[0]:3d} {bb(ent['b_mid'][i:i+1])[0]:3d} | T={T[i]:+.4f} | "
      + " ".join(f"{x:+.4f}" for x in c) + f" | {c.sum():+.4f} | {T[i]-c.sum():+.4f}")

# Pruebas de combinaciones simples sobre los 4 (subconjuntos) y con el prior duplicado/omitido
import itertools
p("\nSubconjuntos de las 4 tablas εtot × β (sin 8,5 ni 7,3), fracción exacta en eps<0,2:")
for mask in itertools.product([0, 1], repeat=4):
    L = (C[s] * np.array(mask)).sum(1)
    p(f"  {mask}: {np.mean(np.abs(L - T[s]) < 1e-3):.4f}")
out.close()
