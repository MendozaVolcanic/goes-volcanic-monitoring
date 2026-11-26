r"""F2 (S28b): AGUANTA de S25b con el día como unidad: intervalo de FA24 por remuestreo de días y tasa por franja.

Por qué: AGUANTA pide FA24 (media por día) <= 0,05 y ninguna franja de 3 h con tasa > 0,10; es una cifra puntual sin
intervalo, y los disparos de 2024 vienen en pocas noches (top 5 = 100 % de los nocturnos). Remuestreo de días con
reposición (20.000, semilla 0) sobre por_dia de s25b_resultado.json; percentil 97,5 de FA24 contra 0,05.
Uso: python -I f2_s25b_dias.py
"""
import json
import os
import sys

import numpy as np

sys.stdout.reconfigure(encoding="utf-8")
OV = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
J = json.load(open(os.path.join(OV, "s25b_fondo_2024", "resultados", "s25b_resultado.json"), encoding="utf-8"))
out = {}
for v in ("S23a", "S23b"):
    pd = [(x["disparos"], x["evaluados"]) for x in J["b"][v]["por_dia"] if x["evaluados"]]
    fr = np.array([a / b for a, b in pd])
    rng = np.random.default_rng(0)
    bs = np.array([fr[rng.integers(0, len(fr), len(fr))].mean() for _ in range(20000)])
    out[v] = {"dias_con_evaluados": len(pd), "FA24_media_por_dia": round(float(fr.mean()), 4),
              "IC95": [round(float(np.percentile(bs, 2.5)), 4), round(float(np.percentile(bs, 97.5)), 4)],
              "frac_replicas_sobre_0.05": float((bs > 0.05).mean()),
              "dias_con_disparo": int(sum(1 for a, _ in pd if a)), "max_fa_dia": round(float(fr.max()), 3)}
    print(v, out[v])
json.dump(out, open(r"D:\goes_notas\s28\s28b\f2\s25b_dias.json", "w", encoding="utf-8"), indent=1)
