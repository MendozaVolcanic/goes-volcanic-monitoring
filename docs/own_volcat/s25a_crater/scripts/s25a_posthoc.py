r"""S25a, revisión POST HOC (no cambia el veredicto del criterio): robustez de lo medido por `s25a_medir.py medir`.
- sin cada día: R y pN quitando un día con P;
- de día (12 a 24 UTC) y de noche (00 a 12 UTC) por separado, porque los N de 2026 disparan sobre todo de noche;
- qué píxeles de la zona hacen los disparos.
Lee D:\goes_notas\s25\s25a\tabla_2026.csv. Sólo usa R y pN (P contra N de 2026), que no necesitan rehacer el azar
de 2025.
Uso: python -I s25a_posthoc.py
"""
import csv
import json
import os
import sys
from collections import Counter

import numpy as np
from scipy import stats

sys.stdout.reconfigure(encoding="utf-8")
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import s25a_medir as Z  # noqa: E402
B, M = Z.B, Z.M


def cargar():
    F, EV, CL = {}, {}, {}
    with open(os.path.join(Z.TRAB, "tabla_2026.csv"), encoding="utf-8") as f:
        for r in csv.DictReader(f):
            k = (r["dia"], M.slot(r["hora"]))
            F[k], EV[k], CL[k] = r["F"] == "1", r["evaluado"] == "1", r["clase"]
    return F, EV, CL


def alc(F, k):
    d, s = k
    return any(F.get((d, x), False) for x in (s - 1, s, s + 1))


def medida(F, EV, CL, filtro):
    P = [(k, alc(F, k)) for k in CL if CL[k] == "P" and EV[k] and filtro(k)]
    N = [(k, alc(F, k)) for k in CL if CL[k] == "N" and EV[k] and filtro(k)]
    psl = {k[1] for k, _ in P}
    cerca = [a for k, a in N if any(M.dslot(k[1], x) <= 6 for x in psl)]
    te, th = len(P), sum(a for _, a in P)
    pN = (float(stats.fisher_exact([[th, te - th], [sum(cerca), len(cerca) - sum(cerca)]], alternative="greater")[1])
          if te and cerca else None)
    return {"P_evaluados": te, "P_alcanzados": int(th), "R": th / te if te else None,
            "N_cerca": len(cerca), "N_cerca_alcanzados": int(sum(cerca)),
            "tasa_N_cerca": sum(cerca) / len(cerca) if cerca else None, "pN": pN}


def main():
    F, EV, CL = cargar()
    dias_P = sorted({k[0] for k in CL if CL[k] == "P"})
    out = {"nota": "POST HOC: no cambia el veredicto del criterio.",
           "todo": medida(F, EV, CL, lambda k: True),
           "de_dia_12_24_UTC": medida(F, EV, CL, lambda k: k[1] >= 72),
           "de_noche_00_12_UTC": medida(F, EV, CL, lambda k: k[1] < 72),
           "sin_cada_dia": {d: medida(F, EV, CL, lambda k, d=d: k[0] != d) for d in dias_P}}
    # tasa de disparo en todos los cuadros evaluados de 2026 (con y sin clase), por mitad del día
    ev = [k for k in EV if EV[k]]
    out["tasa_disparo_2026"] = {
        "dia_12_24": float(np.mean([F[k] for k in ev if k[1] >= 72])),
        "noche_00_12": float(np.mean([F[k] for k in ev if k[1] < 72]))}
    with open(os.path.join(Z.TRAB, "tabla_2026.csv"), encoding="utf-8") as f:
        filas = [r for r in csv.DictReader(f) if r["F"] == "1"]
    c = Counter()
    for r in filas:
        for j in (r["px1"], r["px2"]):
            p = int(Z.ZONA[int(j)])
            c[f"({p // M.NX},{p % M.NX}) {Z.C29.DIST.ravel()[p]:.1f} km"] += 1
    out["pixeles_en_disparos"] = dict(c.most_common())
    out["P_por_mitad"] = {"dia": sum(1 for k in CL if CL[k] == "P" and k[1] >= 72),
                          "noche": sum(1 for k in CL if CL[k] == "P" and k[1] < 72)}
    json.dump(out, open(os.path.join(os.path.dirname(AQUI), "resultados", "s25a_posthoc.json"), "w",
                        encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps(out, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
