r"""Vuelta 2, EXPLORACIÓN cuadros 1 a 5 (no decide): distribución del β(12/11) de VOLCAT en nube tenue, su relación
con el sesgo de BTD y el salto de Δβ en εtot = 0,25. Base V1, N1, S0. Escribe ../resultados/explorar_beta_1a5.txt.
"""
import os, sys
import numpy as np
from scipy.stats import spearmanr
sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import cielo_sesgo as CS  # noqa: E402

lin = []
P = lambda *a: lin.append(" ".join(str(x) for x in a))  # noqa: E731
R = {k: [] for k in ("ev", "bv", "bo", "bias")}
for h in CS.E.ELIGE:
    c = CS.Cuadro(h)
    _, b12, _ = c.eps("V1", "N1", "S0")
    R["ev"].append(c.ev.ravel()); R["bv"].append(c.bv12.ravel()); R["bo"].append(b12.ravel())
    R["bias"].append(((c.clr[14] - c.clr[15]) - (c.obs[14] - c.obs[15])).ravel())
R = {k: np.concatenate(v) for k, v in R.items()}
ok = np.isfinite(R["ev"]) & np.isfinite(R["bv"]) & np.isfinite(R["bo"])
s = ok & (R["ev"] >= 0.05) & (R["ev"] < 0.2)
bv, bo, bias = R["bv"][s], R["bo"][s], R["bias"][s]
P("0,05 <= eps_VOLCAT < 0,2, n =", s.sum())
P("beta VOLCAT p1/5/25/50/75/95/99:", np.percentile(bv, [1, 5, 25, 50, 75, 95, 99]).round(3))
P("beta nuestro p1/5/25/50/75/95/99:", np.percentile(bo, [1, 5, 25, 50, 75, 95, 99]).round(3))
v, n = np.unique(np.round(bv, 3), return_counts=True)
P("valor de beta VOLCAT mas frecuente:", v[np.argmax(n)], "con", n.max(), "pixeles (", round(n.max() / len(bv) * 100, 2), "%)")
P("spearman(sesgo BTD despejado-observado, beta): VOLCAT", round(spearmanr(bias, bv).correlation, 3),
  " nuestro", round(spearmanr(bias, bo).correlation, 3))
P("Delta beta (VOLCAT - nuestro) por franja de eps_VOLCAT:")
for lo in np.arange(0.05, 0.37, 0.02):
    q = ok & (R["ev"] >= lo) & (R["ev"] < lo + 0.02)
    d = R["bv"][q] - R["bo"][q]
    P(f"  [{lo:.2f},{lo + .02:.2f}) n={q.sum():6d} med {np.median(d):+.3f} p25 {np.percentile(d, 25):+.3f} p75 {np.percentile(d, 75):+.3f}")
with open(os.path.join(os.path.dirname(HERE), "resultados", "explorar_beta_1a5.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(lin) + "\n")
print("\n".join(lin))
