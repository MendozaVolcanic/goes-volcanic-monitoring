r"""S29a parte 2, lecturas POST HOC (no están en el criterio; describen, no deciden).

Lo que motivó mirarlas: con la compuerta, Chillán pierde 64 de sus 105 disparos diurnos de 2025 (61 %), mucho más que
el 17 % de los aciertos de 2026. El criterio decide con las vecinas de 2026 (f_FA26) y deja f_FA25 como informativo.

1. ¿Cuánto abre la compuerta por azar? Fracción de cuadros diurnos evaluados de Chillán con la compuerta abierta, en
   2025 y en 2026.
2. Nulo por corrimiento de días para f_FA25: vecinas de 2025 corridas k = 1 a 61 días (61 réplicas, p mínimo 1/62).
3. d25 = f_FA25 − f_P con intervalo por remuestreo de días (2.000, semilla 0), como M5 del criterio.
4. Disparos diurnos de Chillán anulados en 2025, por día.

Lee D:\goes_notas\s29\s29a\chillan_union.npz (escrito por s29a_compuerta.py medir) y los cuadros de S28a.
Uso: python -I s29a_posthoc.py   (escribe resultados/s29a_posthoc.json)
"""
import json
import os
import sys

import numpy as np

sys.stdout.reconfigure(encoding="utf-8")
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import s29a_compuerta as G  # noqa: E402


def main():
    z = np.load(os.path.join(G.TRAB, "chillan_union.npz"))
    F25, e25, F26, e26, CL = z["F25"], z["e25"], z["F26"], z["e26"], z["CL"].astype(object)
    V = {(s, a): G.vecina(s, a) for s in G.VECINAS for a in ("2025", "2026")}
    r = list(G.DIA)
    out = {"rotulo": "POST HOC: no estaba en el criterio; describe, no decide"}
    g25 = G.compuerta_de(V, "2025", G.VECINAS)
    g26 = G.compuerta_de(V, "2026", G.VECINAS)
    out["compuerta_abierta"] = {
        "2025_dia_evaluados": round(float(g25[:, r][e25[:, r]].mean()), 4),
        "2026_dia_evaluados": round(float(g26[:, r][e26[:, r]].mean()), 4),
        "2026_dia_P_evaluados": round(float(g26[:, r][(e26 & (CL == "P"))[:, r]].mean()), 4)}
    obs = int((F25 & g25).sum())
    tot = int(F25[:, r].sum())
    reps = []
    for k in range(1, G.ND["2025"]):
        Vk = {key: ((np.roll(v[0], k, axis=0), v[1]) if key[1] == "2025" else v) for key, v in V.items()}
        reps.append(int((F25 & G.compuerta_de(Vk, "2025", G.VECINAS)).sum()))
    out["f_FA25_nulo"] = {"anulados": obs, "disparos_dia": tot, "f_FA25": round(obs / tot, 4), "replicas": len(reps),
                          "p_minimo": round(1 / (len(reps) + 1), 4),
                          "p": round((1 + sum(x >= obs for x in reps)) / (len(reps) + 1), 4),
                          "replicas_media": round(float(np.mean(reps)), 2), "replicas_max": int(max(reps))}
    # d25 = f_FA25 - f_P
    res = json.load(open(os.path.join(G.RES, "s29a_resultado.json"), encoding="utf-8"))
    pc = np.array([[v["perdidos"], v["alcanzados_antes"]] for v in res["S26a_G"]["por_dia_P"].values()], float)
    pv = np.array([[int((F25[d] & g25[d]).sum()), int(F25[d][r].sum())] for d in range(F25.shape[0])], float)
    fP = pc[:, 0].sum() / pc[:, 1].sum()
    rng = np.random.default_rng(G.SEMILLA)
    ds = []
    for _ in range(G.N_BOOT):
        a = pv[rng.integers(0, len(pv), len(pv))].sum(0)
        b = pc[rng.integers(0, len(pc), len(pc))].sum(0)
        if a[1] and b[1]:
            ds.append(a[0] / a[1] - b[0] / b[1])
    out["d25"] = {"f_FA25": round(obs / tot, 4), "f_P": round(fP, 4), "d": round(obs / tot - fP, 4),
                  "IC95": [round(float(x), 4) for x in np.percentile(ds, [2.5, 97.5])]}
    out["anulados_2025_por_dia"] = {f"{G.T0['2025'] + G.timedelta(days=d):%Y-%m-%d}": [int(a), int(b)]
                                    for d, (a, b) in enumerate(pv) if a}
    json.dump(out, open(os.path.join(G.RES, "s29a_posthoc.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps(out, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
