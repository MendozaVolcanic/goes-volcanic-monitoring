r"""F2 (S28b): ¿cuánto cumple el p25 por cuadro de las confirmaciones congeladas en días de 2026 SIN VOLCAT?

Por qué: las tres confirmaciones (S23b, S25a, S26a) se miden una vez, con al menos 20 P en al menos 2 días nuevos, y su
p25 (Poisson binomial por cuadro, umbral 0,01) supone cuadros independientes. Con 2 días, todo lo que pasa en el día
(pluma diaria, depósito, nieve) se cuenta 20 veces como si fueran 20 sorteos. Placebo: se toman 2 patrones de horas de P
reales del desarrollo (pares de días con >= 20 P evaluados en total) y se ponen en 2 días de 2026 sin P de VOLCAT (con
clase); el alcanzado de cada "P" es el del cuadro evaluado más cercano a ±60 min (0 si no hay). Se cuenta la fracción
de placebo que cumple p25 <= 0,01 (=> PARCIAL o más) y p25 <= 0,01 con R >= umbral de R de cada criterio.
Es informativo: los días sin P de 2026 tienen pluma diaria según Nicolás; el placebo dice qué tan seguido el p25 por
cuadro "confirma" un día de 2026 cualquiera, no un día sin pluma.
Uso: python -I f2_placebo_confirmacion.py  (lee cubos_f2.npz)
"""
import itertools
import json
import os
import sys

import numpy as np

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import f2_bloques as FB  # noqa: E402

S = FB.S
Z = np.load(os.path.join(FB.SAL, "cubos_f2.npz"))
CL = Z["CL"]
out = {}
for nom, k, rmin in (("S23b", "a500", 0.40), ("S25a_conf", "z500", 0.25), ("S26a_conf", "u475", 0.40)):
    ev25, A25, ev26, A26 = Z[f"ev25_{k}"], Z[f"A25_{k}"], Z[f"ev26_{k}"], Z[f"A26_{k}"]
    r25 = S.azar_por_hora([s for d in range(62) for s in np.flatnonzero(ev25[d])],
                          [A25[d, s] for d in range(62) for s in np.flatnonzero(ev25[d])])
    V26 = FB.tabla(ev26, A26)
    pat = {d: np.flatnonzero((CL[d] == "P") & ev26[d]) for d in range(CL.shape[0]) if ((CL[d] == "P") & ev26[d]).any()}
    pares = [(a, b) for a, b in itertools.combinations(pat, 2) if len(pat[a]) + len(pat[b]) >= 20]
    sinP = [d for d in range(CL.shape[0]) if (CL[d] != "").any() and not (CL[d] == "P").any() and np.isfinite(V26[d]).any()]
    rng = np.random.default_rng(0)
    n1 = n2 = 0
    R = 4000
    for _ in range(R):
        a, b = pares[rng.integers(len(pares))]
        d1, d2 = rng.choice(sinP, 2, replace=False)
        sl = [(d1, s) for s in pat[a]] + [(d2, s) for s in pat[b]]
        v = np.array([V26[d, s] for d, s in sl])
        v = np.where(np.isfinite(v), v, 0.0)
        T = int(v.sum())
        p = S.poisson_binomial_cola([r25[s] for _, s in sl], T)
        n1 += p <= 0.01
        n2 += (p <= 0.01) and T / len(sl) >= rmin
    out[nom] = {"pares_de_patrones": len(pares), "dias_sin_P": len(sinP), "replicas": R,
                "frac_p25_le_0.01": round(n1 / R, 4), "frac_p25_le_0.01_y_R_ok": round(n2 / R, 4)}
    print(nom, out[nom], flush=True)
json.dump(out, open(os.path.join(FB.SAL, "placebo_confirmacion.json"), "w", encoding="utf-8"), indent=1)
