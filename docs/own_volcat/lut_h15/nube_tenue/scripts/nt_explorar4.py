r"""Nube tenue, exploración 4 (SÓLO cuadros 1 a 5, nivel A; no decide).

Tramo < 0,2. P_VOLCAT toma pocos valores distintos (680 en ~25 mil píxeles): es función de unas pocas entradas en
casilleros. Si se agrupa por valor de P, una entrada que VOLCAT usa debería caer en un solo casillero dentro del
grupo, y una que no usa, en varios. Se cuenta, por grupo, cuántos casilleros distintos ocupa cada entrada.
Salida: ../resultados/nt_explorar4.txt
"""
import os
import sys

import numpy as np

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nt_comun as N  # noqa: E402

LV, E = N.LV, N.E
out = open(os.path.join(N.RES, "nt_explorar4.txt"), "w", encoding="utf-8")


def p(*a):
    print(*a); print(*a, file=out, flush=True)


ent, agua, v, q = N.cargar(E.ELIGE)
sat = N.no_saturado(v)
with np.errstate(all="ignore"):
    e73 = 1 - (1 - ent["eps"]) ** ent["b73"]
sesgo = ent["btd"] - (ent["clr14"] - ent["clr15"])
s = sat & (ent["eps"] < 0.2)


def binlin(x, eje):
    lo, db, n = LV.EJES[eje]
    with np.errstate(invalid="ignore"):
        i = np.floor((x - lo) / db + 1e-9)
    return np.where(np.isfinite(x), np.clip(i, 0, n - 1), -9)


B = {
    "eps": np.searchsorted(LV.EPS_EDGES, ent["eps"], side="right") - 1,
    "eps_fino(0,01)": np.floor(ent["eps"] / 0.01),
    "b_tot": binlin(ent["b_tot"], "b1112"), "b_op": binlin(ent["b_op"], "b1112"),
    "b_low": binlin(ent["b_low"], "b1112"), "b_mid": binlin(ent["b_mid"], "b1112"),
    "b85": binlin(ent["b85"], "b8511"), "b85op": binlin(ent["b85op"], "b8511"),
    "btd(0,25)": binlin(ent["btd"], "btd"),
    "btclr": np.searchsorted(LV.BTCLR_EDGES, ent["btclr"], side="right") - 1,
    "sesgo(0,1)": np.floor(sesgo / 0.1), "sesgo(0,25)": np.floor(sesgo / 0.25),
    "b_nwp": binlin(ent["b_nwp"], "b1112"),
}
pv = np.round(v[s], 7)
vals, cnt = np.unique(pv, return_counts=True)
orden = np.argsort(-cnt)[:30]
p(f"eps<0,2 no saturados: {s.sum()}, valores distintos de P: {len(vals)}")
p("Por grupo (30 más grandes): casilleros distintos que ocupa cada entrada (1 = constante en el grupo)")
p("  " + " ".join(f"{k[:12]:>12s}" for k in B))
tot1 = {k: 0 for k in B}
for k in orden:
    m = pv == vals[k]
    fila = []
    for nom, b in B.items():
        nd = len(np.unique(b[s][m]))
        fila.append(nd)
        tot1[nom] += (nd == 1)
    p(f"P={vals[k]:.7f} n={cnt[k]:5d} " + " ".join(f"{x:12d}" for x in fila))
p("grupos (de 30) con la entrada constante: " + ", ".join(f"{k}={c}" for k, c in tot1.items()))

# Inverso: agrupando por la tupla de casilleros (eps, b_tot, b_op, b85, b85op) ¿P es única?
for claves in (("eps", "b_tot"), ("eps", "b_tot", "b_op"), ("eps", "b_tot", "b_op", "b85", "b85op"),
               ("eps", "b_tot", "b_op", "b85", "b85op", "b_low", "b_mid"),
               ("eps", "b_tot", "b_op", "b85", "b85op", "b_low", "b_mid", "btd(0,25)", "btclr"),
               ("eps_fino(0,01)", "b_tot", "b_op", "b85", "b85op", "b_low", "b_mid")):
    tup = np.stack([B[c][s] for c in claves], 1)
    _, inv = np.unique(tup, axis=0, return_inverse=True)
    inv = inv.ravel()
    # fracción de píxeles cuyo grupo tiene P única
    import collections
    distintos = collections.defaultdict(set)
    for g, x in zip(inv, pv):
        distintos[g].add(x)
    unico = np.array([len(distintos[g]) == 1 for g in inv])
    p(f"tupla {claves}: grupos {inv.max()+1}, píxeles en grupo con P única {unico.mean():.3f}")
out.close()
