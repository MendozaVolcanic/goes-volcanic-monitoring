r"""POSTERIOR (no decide), cuadros 1 a 5: residuo de εtot con la mejor combinación sin sesgo (V1, N1, S0), por
tramo de ε y por ángulo cenital; y exponente efectivo k = ln(1 − ε_VOLCAT)/ln(1 − ε_oblicuo nuestro) contra cos θ.
Escribe ../resultados/posterior_residuo.txt.
"""
import os, sys
import numpy as np
sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import cielo_sesgo as CS  # noqa: E402

lin = []
P = lambda *a: lin.append(" ".join(str(x) for x in a))  # noqa: E731
D, EV, SZ, K, MU = [], [], [], [], []
for h in CS.E.ELIGE:
    c = CS.Cuadro(h)
    e1, _, _ = c.eps("V1", "N1", "S0")
    e0, _, _ = c.eps("V0", "N1", "S0")
    with np.errstate(all="ignore"):
        k = np.log1p(-c.ev) / np.log1p(-e0)
    s = np.isfinite(c.ev) & np.isfinite(e1)
    D.append((e1 - c.ev)[s]); EV.append(c.ev[s]); SZ.append(np.degrees(np.arccos(c.mu))[s]); K.append(k[s]); MU.append(c.mu[s])
d, ev, sz, k, mu = map(np.concatenate, (D, EV, SZ, K, MU))
P("V1 N1 S0, cuadros 1 a 5: Δε = nuestro − VOLCAT por tramo de ε_VOLCAT")
for lo, hi in ((0.05, .1), (.1, .2), (.2, .3), (.3, .4), (.4, .5), (.5, .6), (.6, .7), (.7, .8), (.8, .9)):
    q = (ev >= lo) & (ev < hi)
    P(f"  [{lo:.2f},{hi:.2f}) n={q.sum()} p5/50/95 = {np.percentile(d[q], [5, 50, 95]).round(4)}  |Δ|<=0,01: {np.mean(np.abs(d[q]) <= .01):.3f}")
P("Por cenital (0,05 <= ε <= 0,9):")
for a, b in ((20, 28), (28, 31), (31, 34), (34, 37), (37, 45)):
    q = (ev >= .05) & (ev <= .9) & (sz >= a) & (sz < b)
    if q.sum() > 100:
        r = k[q] / mu[q]
        P(f"  θ [{a},{b}) n={q.sum()} Δε med {np.median(d[q]):+.4f}  |Δ|<=0,01 {np.mean(np.abs(d[q]) <= .01):.3f}  k/cosθ p5/50/95 {np.nanpercentile(r, [5, 50, 95]).round(3)}")
with open(os.path.join(os.path.dirname(HERE), "resultados", "posterior_residuo.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(lin) + "\n")
print("\n".join(lin))
