r"""Vuelta 3, EXPLORACIÓN cuadros 1 a 5 (no decide): el desfase del cielo despejado de 11 µm (C14) que haría
coincidir nuestro ε(11) oblicuo con el de VOLCAT (llevado al oblicuo con cos θ del píxel), con nube negra N1.
¿Con qué se ordena: ángulo, agua precipitable, ε, posición, celda GFS, BT despejada, BT observada?
Escribe ../resultados/explorar_c14_1a5.txt.
"""
import os, sys
import numpy as np
from scipy.stats import spearmanr
sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import vuelta2_beta as V2  # noqa: E402
CS = V2.CS
lin = []
P = lambda *a: lin.append(" ".join(str(x) for x in a))  # noqa: E731
K = ("d14", "ev", "sz", "tpw", "row", "col", "clr", "obs", "cell", "d15", "fr")
R = {k: [] for k in K}
for i, h in enumerate(CS.E.ELIGE):
    c = CS.Cuadro(h)
    with np.errstate(all="ignore"):
        e14s = 1 - (1 - c.ev) ** (1 / c.mu)
        out = {}
        for b, e in ((14, e14s), (15, 1 - (1 - e14s) ** np.where(c.ev < 0.25, c.bv12 - 0.2, c.bv12))):
            ro = CS.E.rad(c.d, c.obs[b], b); rb = CS.E.rad(c.d, c.tcld["N1"], b)
            out[b] = CS.bt_de_rad((ro - e * rb) / (1 - e), c.d, b) - c.clr[b]
    rr, cc = np.indices(CS.SH)
    iy = c.d["geocatRTM__nwp_y_index"].astype(int); ix = c.d["geocatRTM__nwp_x_index"].astype(int)
    for k, v in (("d14", out[14]), ("ev", c.ev), ("sz", np.degrees(np.arccos(c.mu))), ("tpw", V2.TPW[h]),
                 ("row", rr), ("col", cc), ("clr", c.clr[14]), ("obs", c.obs[14]), ("cell", iy * 1000 + ix),
                 ("d15", out[15]), ("fr", np.full(CS.SH, i))):
        R[k].append(np.asarray(v, float).ravel())
R = {k: np.concatenate(v) for k, v in R.items()}
s = np.isfinite(R["d14"]) & np.isfinite(R["ev"]) & (R["ev"] >= 0.05) & (R["ev"] < 0.3)
P("0,05 <= eps < 0,3, n =", s.sum())
P("desfase implicito C14 (despejado VOLCAT - geocatRTM), K, p5/25/50/75/95:", np.percentile(R["d14"][s], [5, 25, 50, 75, 95]).round(2))
P("desfase implicito C15, K, p5/25/50/75/95:", np.percentile(R["d15"][s][np.isfinite(R["d15"][s])], [5, 25, 50, 75, 95]).round(2))
for k in ("sz", "tpw", "ev", "row", "col", "clr", "obs"):
    P(f"  spearman(d14, {k}) = {spearmanr(R['d14'][s], R[k][s]).correlation:+.3f}")
# por celda GFS: ¿constante dentro de la celda?
cells = R["cell"][s]; d = R["d14"][s]
u, inv = np.unique(cells, return_inverse=True)
med = np.array([np.median(d[inv == j]) for j in range(len(u))])
cnt = np.bincount(inv)
resid = d - med[inv]
P("celdas GFS con pixeles:", len(u), " sd entre medianas de celda (celdas >= 50 px):", np.std(med[cnt >= 50]).round(3),
  " sd del residuo dentro de celda:", np.std(resid).round(3), " sd total:", np.std(d).round(3))
P("d14 por franja de angulo (mediana):")
for a, b in ((20, 28), (28, 31), (31, 34), (34, 37), (37, 45)):
    q = s & (R["sz"] >= a) & (R["sz"] < b)
    if q.sum() > 100:
        P(f"  theta [{a},{b}) n={q.sum()} d14 med {np.median(R['d14'][q]):+.2f}  tpw med {np.median(R['tpw'][q]):.2f}  BTclr med {np.median(R['clr'][q]):.1f}")
P("d14 por franja de tpw (mediana):")
for a, b in ((4, 4.6), (4.6, 4.9), (4.9, 5.2), (5.2, 5.5), (5.5, 6.5)):
    q = s & (R["tpw"] >= a) & (R["tpw"] < b)
    if q.sum() > 100:
        P(f"  tpw [{a},{b}) n={q.sum()} d14 med {np.median(R['d14'][q]):+.2f}  theta med {np.median(R['sz'][q]):.1f}")
P("d14 por cuadro:", [round(float(np.median(R["d14"][s & (R["fr"] == i)])), 2) for i in range(5)])
with open(os.path.join(os.path.dirname(HERE), "resultados", "explorar_c14_1a5.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(lin) + "\n")
print("\n".join(lin))

# ¿Campo suave o ruido de píxel? Diferencia entre vecinos horizontales del desfase, en el cuadro 1.
c = CS.Cuadro(CS.E.ELIGE[0])
with np.errstate(all="ignore"):
    e14s = 1 - (1 - c.ev) ** (1 / c.mu)
    ro = CS.E.rad(c.d, c.obs[14], 14); rb = CS.E.rad(c.d, c.tcld["N1"], 14)
    d2 = CS.bt_de_rad((ro - e14s * rb) / (1 - e14s), c.d, 14) - c.clr[14]
m = np.isfinite(d2) & (c.ev >= 0.05) & (c.ev < 0.3)
pair = m[:, :-1] & m[:, 1:]
dif = (d2[:, 1:] - d2[:, :-1])[pair]
P("\ncuadro 1: |d14 vecino - d14| mediana", np.median(np.abs(dif)).round(3), " sd d14", np.std(d2[m]).round(3),
  " -> razon", (np.median(np.abs(dif)) / np.std(d2[m])).round(2), "(~1,1 si ruido blanco, ~0 si campo suave)")
dob = (c.obs[14][:, 1:] - c.obs[14][:, :-1])[pair]
P("  spearman(diferencia de d14 entre vecinos, diferencia de BT14 obs entre vecinos):", round(spearmanr(dif, dob).correlation, 3))
with open(os.path.join(os.path.dirname(HERE), "resultados", "explorar_c14_1a5.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(lin) + "\n")
print("\n".join(lin[-2:]))
