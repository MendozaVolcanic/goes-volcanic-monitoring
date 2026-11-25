r"""S23a, sensibilidad POST HOC (mirada después del veredicto; no lo cambia ni reemplaza la regla).

Lo que motivó mirarla: 70 de 100 cuadros P de 2026 quedan sin evaluar por tener menos de 9 tajadas válidas, porque
con el nublado de costumbre de 2025 la máscara de NOAA marca como nube "dinámica" la nieve de 2026 (de día la máscara
usa reflectancia y la nieve parece nube; la nieve de un año no es la del otro). Aquí cada año usa su propio nublado de
costumbre: 2025 para la referencia (como la regla) y el de S22b (cuadros N despejados de 2026) para 2026. La línea
base y el umbral siguen saliendo sólo de 2025. El nublado de costumbre no resta nada al píxel: sólo decide qué píxel
se borra, así que usar el de 2026 no mete la pluma en la base.

Escribe resultados/sensibilidad_costumbre_2026.json. Uso: python -I s23_sensibilidad.py
"""
import json
import os
import sys

import numpy as np
from scipy import stats

sys.stdout.reconfigure(encoding="utf-8")
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import s23_medir as S  # noqa: E402
B, M = S.B, S.M

if __name__ == "__main__":
    D26 = S.Detector(ref="2026N", con_blanco=False)
    D = S.Detector(ref="2025", con_blanco=True, estat_blanco=D26.ESTAT)
    _, sl25, al25, _ = S._seco_2025(D)
    r25 = S.azar_por_hora(sl25, al25)
    U, _ = D.umbral(None)
    P, N, por_dia = [], [], []
    for d in range(B.ND):
        F, ev = S.disparos(D.ST, D.KT, d, U)
        for s in np.flatnonzero(ev):
            a = B.alcanzado(F, ev, s)[1]
            if D.CLT[d, s] == "P":
                P.append((d, s, a))
            elif D.CLT[d, s] == "N":
                N.append((d, s, a))
        Ps = np.flatnonzero(D.CLT[d] == "P")
        if len(Ps):
            pe = [a for dd, s, a in P if dd == d]
            por_dia.append({"dia": B.fecha(d), "P": int(len(Ps)), "P_evaluados": len(pe), "P_alcanzados": int(sum(pe)),
                            "disparos_del_dia": int(F.sum()), "tajadas": np.bincount(D.KT[d][F], minlength=12).tolist()})
    te, th = len(P), int(sum(a for *_, a in P))
    p25 = S.poisson_binomial_cola([r25[s] for _, s, _ in P], th) if te else None
    # contra N de 2026: Fisher con los N evaluados a +-60 min de algún P evaluado (pozo, no por hora)
    psl = {s for _, s, _ in P}
    cerca = [a for _, s, a in N if any(M.dslot(s, x) <= S.W_AZAR for x in psl)]
    pN = float(stats.fisher_exact([[th, te - th], [int(sum(cerca)), len(cerca) - int(sum(cerca))]],
                                  alternative="greater")[1]) if te and cerca else None
    sin = {}
    for dia in sorted({B.fecha(d) for d, _, _ in P}):
        q = [x for x in P if B.fecha(x[0]) != dia]
        h = int(sum(a for *_, a in q))
        sin[dia] = {"P_evaluados": len(q), "P_alcanzados": h,
                    "p25": S.poisson_binomial_cola([r25[s] for _, s, _ in q], h) if q else None}
    out = {"nota": "POST HOC: cada año con su nublado de costumbre; base y umbral de 2025. No cambia el veredicto.",
           "P_evaluados": te, "P_alcanzados": th, "R": th / te if te else None,
           "E25": float(sum(r25[s] for _, s, _ in P)), "p25": p25,
           "N_2026_cerca_de_P": len(cerca), "N_2026_cerca_alcanzados": int(sum(cerca)), "pN_fisher": pN,
           "N_2026_evaluados": len(N), "r_N_2026": float(np.mean([a for *_, a in N])) if N else None,
           "por_dia": por_dia, "sin_cada_dia": sin}
    json.dump(out, open(os.path.join(S.RES, "sensibilidad_costumbre_2026.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(json.dumps(out, ensure_ascii=False, indent=1))
