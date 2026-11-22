"""H19, exploracion en el BLOQUE DE ELECCION: de donde sale el VALOR de subset.
Mira log-odds(subset) menos log-odds(IR) y menos log-odds(SW_IR), por zona. Uso: python h19_explora5.py NPZ_DIR"""
import sys
import os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from h19_comun import cargar, f, PIX, ELECCION, guardia
import h19_vref as VR

npz = sys.argv[1]
guardia(ELECCION)
rows = []
for h in ELECCION:
    d = cargar(npz, h)
    P = f(d, PIX + "ash_probability"); S = f(d, PIX + "ash_probability_subset")
    IR = f(d, PIX + "ash_probability_IR"); SW = f(d, PIX + "ash_probability_SW_IR")
    eps = f(d, PIX + "cloud_emissivity_ch14_tot"); r2 = f(d, "p__channel_2_reflectance")
    ag = d["p__Ash_Group_Id_2d"] > 0
    V = np.isfinite(S)
    osc = (eps >= 0.90) & (r2 < 50) & (r2 >= 10)
    for i in np.nonzero(V)[0]:
        rows.append((ELECCION.index(h), ag[i], osc[i], S[i], P[i], IR[i], SW[i], eps[i], r2[i], d["idA"][i]))
R = np.array(rows, float)
fr, ag, osc, S, P, IR, SW, eps, r2, ida = R.T
ag = ag > 0; osc = osc > 0
lS, lI, lW, lP = VR.logit(S), VR.logit(IR), VR.logit(SW), VR.logit(P)
np.set_printoptions(linewidth=200, suppress=True)


def q(x):
    return np.round(np.percentile(x, [0, 5, 25, 50, 75, 95, 100]), 3) if len(x) else []


print("Tabla 2x2 (grupo de ceniza x oscuro-opaco): n, frac subset>=.5, frac P>=.5")
for a in (True, False):
    for o in (True, False):
        m = (ag == a) & (osc == o)
        print("  ag=%s oscuro_opaco=%s n=%d  subset alto %.4f  P alta %.4f  subset==IR %.3f subset==SW %.3f" % (
            a, o, m.sum(), (S[m] >= .5).mean() if m.sum() else np.nan, (P[m] >= .5).mean() if m.sum() else np.nan,
            (np.abs(S - IR)[m] <= 1e-6).mean() if m.sum() else np.nan, (np.abs(S - SW)[m] <= 1e-6).mean() if m.sum() else np.nan))
m = ag & osc
print("\nag y oscuro-opaco: subset==1 exacto %d de %d; subset<1: %d" % ((S[m] == 1).sum(), m.sum(), (m & (S < 1)).sum()))
m2 = m & (S < 1) & (S > 0)
print("  cuantiles subset(<1):", q(S[m2]))
print("  logit(subset)-logit(IR):", q((lS - lI)[m2]))
print("  logit(subset)-logit(SW):", q((lS - lW)[m2]))
print("  IR en esos:", q(IR[m2]), " SW:", q(SW[m2]))
m3 = m & (S == 1)
print("  donde subset==1: IR cuantiles", np.percentile(IR[m3], [0, 50, 100]), " SW", np.percentile(SW[m3], [0, 50, 100]))
m4 = ag & ~osc
print("\nag y NO oscuro-opaco n=%d: logit(subset)-logit(IR):" % m4.sum(), q((lS - lI)[m4]), " -logit(SW):", q((lS - lW)[m4]))
print("  subset==SW %.3f subset==IR %.3f ; subset<min(IR,SW) %.3f ; subset>max %.3f" % (
    (np.abs(S - SW)[m4] <= 1e-9).mean(), (np.abs(S - IR)[m4] <= 1e-9).mean(), (S < np.minimum(IR, SW) - 1e-12)[m4].mean(), (S > np.maximum(IR, SW) + 1e-12)[m4].mean()))
# P contra subset dentro de oscuro-opaco
m5 = ag & osc & (np.abs(P - S) > 0.01)
print("\nP != subset dentro de ag y oscuro-opaco: n=%d ; P cuantiles" % m5.sum(), q(P[m5]), " subset", q(S[m5]))
print("  logit(P)-logit(IR)", q((lP - lI)[m5]), " logit(P)-logit(SW)", q((lP - lW)[m5]))
print("  eps", q(eps[m5]), " ref2", q(r2[m5]))
print("  P==IR %.3f  P==SW %.3f  P==0.5*(algo)? ; por cuadro:" % ((np.abs(P - IR)[m5] <= 1e-6).mean(), (np.abs(P - SW)[m5] <= 1e-6).mean()),
      np.bincount(fr[m5].astype(int), minlength=13))
