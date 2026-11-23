r"""Revision H17 (S19e): pregunta 2 del instrumento (criterio §4) calculada aparte, porque en la corrida de
rev_h17.py del 23-11 salio NaN por un error de codigo (np.median sobre cuadros sin BT11 en el terreno bajo; ya
corregido a nanmedian en rev_h17.py). Ademas, una lectura post hoc que NO decide: POD y FAR de la variante decide
con base despejada, restringidos a cuadros t en escena despejada (positivos y negativos en el mismo cielo).
Escribe ../resultados/rev_q2_resultado.txt. Uso, desde scripts\: python -I rev_q2.py
"""
import os
import sys

import numpy as np
import pandas as pd

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
sys.path.insert(1, os.path.join(os.path.dirname(os.path.dirname(AQUI)), "h17_regla_propia", "scripts"))
import rev_comun as R  # noqa: E402
import h17_comun as K  # noqa: E402
import h17_pluma as P17  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
RES = os.path.join(os.path.dirname(AQUI), "resultados")

cs, T, b11, _ = P17.cargar_ir(K.indice())
est = [R.estado(c) for c in cs]
hay = np.array([x[0] for x in est])
esc = np.array([x[2] for x in est])
with np.errstate(all="ignore"):
    bt_bajo = np.array([np.nanmedian(b11[i][R.BAJO]) if np.isfinite(b11[i][R.BAJO]).any() else np.nan
                        for i in range(len(cs))])
horas = np.array([t.hour for t in T])
L = ["Pregunta 2 del instrumento (BT11 mediana del terreno bajo, escena despejada menos no despejada, por hora UTC)",
     f"cuadros {len(cs)}, sin BT11 en el terreno bajo {int(np.isnan(bt_bajo).sum())}"]
dif = []
for h in range(24):
    a, b = bt_bajo[(horas == h) & esc], bt_bajo[(horas == h) & hay & ~esc]
    a, b = a[np.isfinite(a)], b[np.isfinite(b)]
    if len(a) >= 5 and len(b) >= 5:
        dif.append(float(np.median(a) - np.median(b)))
        L.append(f"  {h:02d} UTC: despejada {np.median(a):.1f} K (n {len(a)}), no despejada {np.median(b):.1f} K "
                 f"(n {len(b)}), dif {dif[-1]:+.2f} K")
q2 = float(np.median(dif))
L.append(f"mediana por hora = {q2:+.2f} K en {len(dif)} horas (pide >= +3 K) -> {'PASA' if q2 >= 3 else 'FALLA'}")

df = pd.read_csv(os.path.join(RES, "rev_h17_por_cuadro.csv"), parse_dates=["fecha"])
L.append("\nLectura post hoc (NO decide): variante decide, cuadros t en escena despejada")
rng = np.random.default_rng(20261121)
for v in ("orig", "desp"):
    col = f"det_{v}"
    e = df[df[f"con_{v}"].fillna(False).astype(bool) & (df.pos | df.neg) & df.escena_t].copy()
    e[col] = e[col].fillna(False).astype(bool)
    P, N = e[e.pos], e[e.neg]
    lo, hi = P17.boot_dias(e.assign(**{col: e[col].astype(float)}), col, rng)
    L.append(f"  {v:5s} POD {P[col].mean():.3f} (n {len(P)})  FAR {N[col].mean():.3f} (n {len(N)})  "
             f"POD-FAR IC95 [{lo:.3f}; {hi:.3f}]")
open(os.path.join(RES, "rev_q2_resultado.txt"), "w", encoding="utf-8").write("\n".join(L) + "\n")
print("\n".join(L))
