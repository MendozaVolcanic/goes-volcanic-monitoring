r"""F1 (S28b): la comparación B1 de S24 con la misma selección en los dos años.

S24 (criterio §3, B1) compara la tasa nocturna de 2025 SIN las noches con 3 disparos o más ("noches comunes") contra
la tasa de TODO 2026. La selección por el resultado se aplica sólo a un año. Aquí se recalcula con el código de S24
sin cambios (Detector de s23_medir, regla S23b, estat_2026 congelado), sólo con días ya mirados (2026 hasta el
24-11; ningún día posterior), y se compara también 2025 comunes contra 2026 comunes.
Salida: D:\goes_notas\s28\s28b\f1\s24_comunes_simetrico.json
"""
import hashlib
import json
import os
import sys

import numpy as np
from scipy import stats

AQUI = os.path.dirname(os.path.abspath(__file__))
OV = os.path.abspath(os.path.join(AQUI, "..", "..", ".."))
sys.path.insert(0, os.path.join(OV, "s24_dia14_noche", "scripts"))
import s24_medir as T  # noqa: E402

S, B = T.S, T.B
OUT = r"D:\goes_notas\s28\s28b\f1\s24_comunes_simetrico.json"

estat = np.load(T.ESTAT)
assert hashlib.sha256(estat.tobytes()).hexdigest()[:16] == T.SHA_ESTAT
assert B.ND == 65 and B.fecha(B.ND - 1) == "2026-11-24", B.fecha(B.ND - 1)
D = S.Detector(ref="2025", con_blanco=True, estat_blanco=estat)
U0, _ = D.umbral(None)
n26, f26 = {}, {}
for d in range(B.ND):
    F, ev = S.disparos(D.ST, D.KT, d, U0)
    sl = [s for s in T.NOCHE if ev[s]]
    n26[B.fecha(d)], f26[B.fecha(d)] = len(sl), int(sum(F[s] for s in sl))
n25, f25 = {}, {}
for d in D.DIASR:
    Ud, _ = D.umbral(d)
    F, ev = S.disparos(D.SR, D.KR, d, Ud)
    sl = [s for s in T.NOCHE if ev[s]]
    n25[d], f25[d] = len(sl), int(sum(F[s] for s in sl))
com25 = [d for d in n25 if f25[d] < T.COMUN_MAX]
com26 = [d for d in n26 if f26[d] < T.COMUN_MAX]
a = (sum(f25[d] for d in com25), sum(n25[d] for d in com25))
b_todo = (sum(f26.values()), sum(n26.values()))
b_com = (sum(f26[d] for d in com26), sum(n26[d] for d in com26))


def fisher(x, y):
    return float(stats.fisher_exact([[x[0], x[1] - x[0]], [y[0], y[1] - y[0]]], alternative="two-sided")[1])


out = {"2025_comunes": a, "2026_todo": b_todo, "2026_comunes": b_com,
       "noches_2026_excluidas": {k: (f26[k], n26[k]) for k in n26 if f26[k] >= T.COMUN_MAX},
       "p_S24_tal_cual_comunes25_vs_todo26": fisher(a, b_todo),
       "p_simetrico_comunes25_vs_comunes26": fisher(a, b_com),
       "razon_tal_cual": (b_todo[0] / b_todo[1]) / (a[0] / a[1]),
       "razon_simetrica": (b_com[0] / b_com[1]) / (a[0] / a[1])}
os.makedirs(os.path.dirname(OUT), exist_ok=True)
json.dump(out, open(OUT, "w", encoding="utf-8"), indent=1)
print(json.dumps(out, indent=1))
