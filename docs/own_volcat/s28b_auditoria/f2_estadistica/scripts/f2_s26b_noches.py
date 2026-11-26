r"""F2 (S28b): E3 de S26b con la noche como unidad, no el cuadro.

Por qué: el veredicto EL CALOR NO EXPLICA pide E3 (i) con p <= 0,01 por Fisher sobre cuadros sumados (S26b §3). Los
disparos de la zona vienen en rachas dentro de la noche; si las 11 noches bajo el límite de 2026 tienen la tasa alta
repartida en pocas noches, el Fisher de cuadros sobrestima la evidencia. Aquí: permutación de etiquetas de año entre
noches (estadístico = tasa de cuadros sumados del grupo 2026, igual que el criterio), 20.000 permutaciones, semilla 0,
y Mann-Whitney unilateral de tasas por noche. Lee D:\goes_notas\s26\s26b\noches_2026.csv y noches_2025.csv (salida de
s26b_medir.py). Control: los totales tienen que dar las cifras de cuadros de s26b_resultado.json (107/310, 118/303,
94/2562).
Uso: python -I f2_s26b_noches.py
"""
import csv
import json
import sys

import numpy as np
from scipy import stats

sys.stdout.reconfigure(encoding="utf-8")
T = r"D:\goes_notas\s26\s26b"
NPERM = 20000


def leer(fn):
    with open(fn, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def perm(g26, g25, rng):
    F = np.array([x[0] for x in g26 + g25], float)
    E = np.array([x[1] for x in g26 + g25], float)
    n = len(g26)
    obs = F[:n].sum() / E[:n].sum()
    cnt = 0
    for _ in range(NPERM):
        i = rng.permutation(len(F))[:n]
        cnt += F[i].sum() / E[i].sum() >= obs
    return obs, (1 + cnt) / (1 + NPERM)


def main():
    n26, n25 = leer(T + r"\noches_2026.csv"), leer(T + r"\noches_2025.csv")
    g25 = [(int(r["disparos"]), int(r["evaluados"])) for r in n25 if int(r["evaluados"])]
    out = {"2025_total": [sum(a for a, _ in g25), sum(b for _, b in g25)], "noches_2025": len(g25)}
    grupos = {"bajo_limite": [r for r in n26 if r["estado_calor"] == "bajo_limite"],
              "epoca_21-09_a_11-10": [r for r in n26 if r["noche"] <= "2026-10-11"]}
    rng = np.random.default_rng(0)
    for nom, rr in grupos.items():
        g26 = [(int(r["disparos"]), int(r["evaluados"])) for r in rr if int(r["evaluados"])]
        obs, p = perm(g26, g25, rng)
        t26 = [a / b for a, b in g26]
        t25 = [a / b for a, b in g25]
        mw = stats.mannwhitneyu(t26, t25, alternative="greater").pvalue
        out[nom] = {"noches": len(g26), "cuadros": [sum(a for a, _ in g26), sum(b for _, b in g26)],
                    "tasa": round(obs, 4), "p_perm_noches": p, "piso_perm": 1 / (1 + NPERM),
                    "p_mannwhitney_tasas": float(mw), "tasas_por_noche": [round(x, 3) for x in sorted(t26)],
                    "fraccion_disparos_top3_noches": round(sorted([a for a, _ in g26])[-3:] and
                                                           sum(sorted([a for a, _ in g26])[-3:]) /
                                                           max(1, sum(a for a, _ in g26)), 3)}
    out["2025_noches_con_disparo"] = sum(1 for a, _ in g25 if a)
    print(json.dumps(out, ensure_ascii=False, indent=1))
    json.dump(out, open(r"D:\goes_notas\s28\s28b\f2\s26b_noches.json", "w", encoding="utf-8"), indent=1)


if __name__ == "__main__":
    main()
