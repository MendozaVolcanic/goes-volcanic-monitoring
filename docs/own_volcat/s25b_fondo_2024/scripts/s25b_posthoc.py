r"""S25b, POST HOC (mirado después de los veredictos; no los cambia): ¿cuánto azar le asigna 2024 a los cuadros de VOLCAT
que la candidata S23b alcanza en 2026?

Por qué: el p25 de S23b (sensibilidad_costumbre_2026.json) estima el azar por hora con el ensayo en seco de 2025, que es
dentro de la muestra (cada día con la base sin sí mismo). S25b mostró que fuera de la muestra el mismo detector dispara
menos. Si el azar de 2025 estaba inflado, el p25 de S23b era conservador; aquí se recalcula con el azar por hora de 2024
(versión S23b: base y umbral de 2025, costumbre de 2024), sin tocar la regla ni los cuadros de 2026.
Escribe resultados/posthoc_azar_2024.json. Uso: python -I s25b_posthoc.py
"""
import json
import os
import sys

import numpy as np

sys.stdout.reconfigure(encoding="utf-8")
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import s25b_medir as X  # noqa: E402
S, B, M = X.S, X.B, X.M

if __name__ == "__main__":
    D26 = S.Detector(ref="2026N", con_blanco=False)                       # costumbre de 2026 (la de S23b)
    D = S.Detector(ref="2025", con_blanco=True, estat_blanco=D26.ESTAT)   # S23b sobre 2026, igual que s23_sensibilidad
    D24 = X._detector_2024()
    _, sl25, al25, _ = S._seco_2025(D)
    r25 = S.azar_por_hora(sl25, al25)
    U, _ = D.umbral(None)
    # azar de 2024: versión S23b aplicada a 2024
    acm24, m124 = np.load(X._npy24("acm")), np.load(X._npy24("m1"))
    B0 = D.base(None)
    S24, K24, _, _ = X.aplicar(D, acm24, m124, D24.ESTAT, lambda d: B0)
    sl24, al24, dias24 = [], [], {}
    for d in range(X.ND):
        F, ev = S.disparos(S24, K24, d, U)
        for s in np.flatnonzero(ev):
            sl24.append(s)
            al24.append(B.alcanzado(F, ev, s)[1])
        if F.any():
            dias24[f"{X.T0 + X.timedelta(days=d):%Y-%m-%d}"] = [
                {"hora": M.hhmm(int(s)), "tajada_grados": f"{30 * int(K24[d, s])}-{30 * int(K24[d, s]) + 30}",
                 "S": S._r(S24[d, s]), "U": S._r(U[s])} for s in np.flatnonzero(F)]
    r24 = S.azar_por_hora(sl24, al24)
    P = []
    for d in range(B.ND):
        F, ev = S.disparos(D.ST, D.KT, d, U)
        for s in np.flatnonzero(ev):
            if D.CLT[d, s] == "P":
                P.append((d, s, B.alcanzado(F, ev, s)[1]))
    te, th = len(P), int(sum(a for *_, a in P))
    out = {"nota": "POST HOC: no cambia ningún veredicto de S23 ni de S25b.",
           "P_evaluados": te, "P_alcanzados": th,
           "E25": float(sum(r25[s] for _, s, _ in P)), "p25": S.poisson_binomial_cola([r25[s] for _, s, _ in P], th),
           "E24": float(sum(r24[s] for _, s, _ in P)), "p24": S.poisson_binomial_cola([r24[s] for _, s, _ in P], th),
           "r_global_2025": float(np.mean(al25)), "r_global_2024": float(np.mean(al24)),
           "disparos_2024_S23b_por_dia": dias24,
           "r_por_hora":{f"{h:02d}": {"r25": S._r(r25[6 * h]), "r24": S._r(r24[6 * h])} for h in range(24)}}
    json.dump(out, open(os.path.join(X.RES, "posthoc_azar_2024.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps({k: v for k, v in out.items() if k not in ("r_por_hora", "disparos_2024_S23b_por_dia")},
                     ensure_ascii=False, indent=1))
    for dia, v in dias24.items():
        print(dia, [(x["hora"], x["tajada_grados"]) for x in v])
