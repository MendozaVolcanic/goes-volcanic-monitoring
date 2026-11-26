r"""F2 (S28b): P contra N del MISMO día (informativo, no es la regla de ningún criterio).

Por qué: pN (S25a, S26a) junta los N de todos los días a la misma hora. Si la zona dispara casi todo el día en los días
con pluma (estado del día) y poco en los otros, pN mide "día con VOLCAT contra día sin VOLCAT", no "cuadro con VOLCAT
contra cuadro sin VOLCAT". Aquí, dentro de cada día con P: alcanzados en P evaluados contra alcanzados en N evaluados
del mismo día, y Mantel-Haenszel por día (la hora queda mezclada: los N del mismo día están a >= 70 min de un P).
Uso: python -I f2_mismo_dia.py  (lee cubos_f2.npz)
"""
import json
import os
import sys
from datetime import date, timedelta

import numpy as np
from scipy import stats

sys.stdout.reconfigure(encoding="utf-8")
Z = np.load(r"D:\goes_notas\s28\s28b\f2\cubos_f2.npz")
CL = Z["CL"]
out = {}
VAR = [(n, k, v) for n, k in (("S25a", "z500"), ("S26a_desarrollo", "u475"), ("S23b_desarrollo", "a500"))
       for v in ("todo_el_dia", "N_a_3h_de_un_P")]
for nom0, k, var in VAR:
    nom = f"{nom0}_{var}"
    ev, A = Z[f"ev26_{k}"], Z[f"A26_{k}"]
    tabs, filas = [], []
    for d in range(CL.shape[0]):
        mP, mN = (CL[d] == "P") & ev[d], (CL[d] == "N") & ev[d]
        if not mP.any():
            continue
        if var == "N_a_3h_de_un_P":                       # quita la mezcla de horas: sólo N a <= 3 h de algún P
            ps = np.flatnonzero(mP)
            cerca = np.array([np.abs(ps - x).min() <= 18 for x in range(144)])
            mN = mN & cerca
        a, b = int(A[d][mP].sum()), int(mP.sum())
        c, e = int(A[d][mN].sum()), int(mN.sum())
        filas.append({"dia": (date(2026, 9, 21) + timedelta(days=d)).isoformat(), "P": [a, b], "N_mismo_dia": [c, e]})
        if e:
            tabs.append(np.array([[a, b - a], [c, e - c]]))
    num = den = sa = se = sv = 0.0
    for t in tabs:
        (a, b), (c, e) = t
        n = t.sum()
        if n < 2:
            continue
        num += a * e / n
        den += b * c / n
        sa += a
        se += (a + b) * (a + c) / n
        sv += (a + b) * (c + e) * (a + c) * (b + e) / (n * n * (n - 1))
    chi = (abs(sa - se) - 0.5) ** 2 / sv if sv else float("nan")
    out[nom] = {"por_dia": filas, "OR_MH": round(num / den, 3) if den else None,
                "p_MH_bilateral": float(stats.chi2.sf(chi, 1)), "estratos": len(tabs),
                "alcanzados_P_observados_vs_esperados": [sa, round(se, 2)]}
    print(nom, "OR_MH", out[nom]["OR_MH"], "p", out[nom]["p_MH_bilateral"])
    if var == "N_a_3h_de_un_P":
        for f in filas:
            print("   ", f)
json.dump(out, open(r"D:\goes_notas\s28\s28b\f2\mismo_dia.json", "w", encoding="utf-8"), indent=1)
