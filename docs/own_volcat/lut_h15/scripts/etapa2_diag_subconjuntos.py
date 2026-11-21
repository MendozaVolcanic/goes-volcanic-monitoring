r"""C3 (H15) etapa 2, diagnóstico POSTERIOR (no decide): ¿qué subconjunto de tablas reproduce exacto el logit de
VOLCAT? Sólo cuadros 1 a 5, nivel A. Para cada tabla de IR (con y sin 8,5 µm) y cada modo de fuera de eje, la
contribución log(A/C) por píxel; luego todas las combinaciones de inclusión.
"""
import itertools, os, sys
import numpy as np
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lut_volcat as LV  # noqa: E402
import etapa2_validar as E  # noqa: E402

T = LV.Tablas()
gfs = dict(np.load(os.path.join(E.ML, "gfs_ttropo.npz")))
tablas = LV.IR_S1 + LV.IR_8511
contrib = {m: [] for m in "abc"}
V = []
for h in E.ELIGE:
    A, B, agua, v = E.cuadro(h, gfs)
    V.append(v)
    for modo in "abc":
        cols = []
        for t in tablas:
            LV.CONJUNTOS["_uno"] = [t]
            L, _ = LV.log_odds(T, "_uno", A, agua, modo=modo, comb="J")
            cols.append(L - np.log(LV.PRIOR / (1 - LV.PRIOR)))
        contrib[modo].append(np.stack(cols, 1))
v = np.concatenate(V)
with np.errstate(all="ignore"):
    lv = np.log(v / (1 - v))
sat = np.isfinite(v) & (v > 1e-6) & (v < 1 - 1e-6)
L0 = np.log(LV.PRIOR / (1 - LV.PRIOR))
nombres = [t[0] for t in tablas]
res = []
for modo in "abc":
    C = np.concatenate(contrib[modo])[sat]
    for incl in itertools.product([0, 1], repeat=len(tablas)):
        w = np.array(incl, float)
        L = L0 + C @ w
        res.append((np.mean(np.abs(L - lv[sat]) < 1e-3), modo, incl))
res.sort(reverse=True)
print("pixeles no saturados:", sat.sum())
for f, modo, incl in res[:12]:
    print(f"{f:.4f} modo {modo} incluye: " + ", ".join(n for n, i in zip(nombres, incl) if i))
