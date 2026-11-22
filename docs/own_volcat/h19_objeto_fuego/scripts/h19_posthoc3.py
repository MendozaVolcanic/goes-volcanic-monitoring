"""H19, POST HOC (no decide): en los cuadros 22:46 a 23:31, pixeles donde la P publicada supera a subset.
Salto en log-odds (valores repetidos) y que variable de seguimiento lo acompana. Uso: python h19_posthoc3.py NPZ_DIR --validacion"""
import sys
import os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from h19_comun import cargar, f, PIX, OBJ, TRK, VALIDACION, guardia
import h19_vref as VR

npz = sys.argv[1]
guardia(VALIDACION)
sal, y, X = [], [], {}
vars_ = [TRK + "Btd1112_Time_Diff", TRK + "Btd8511_Time_Diff", TRK + "Bt11_Time_Diff", TRK + "Bt73_Time_Diff",
         TRK + "ash_probability_IR_prev", TRK + "displacement_distance", TRK + "count_in_ash",
         TRK + "Btd_Trend_Obj_Size_Ash", TRK + "NN_Obj_Size_Ash", TRK + "NN_Robust_Count_Ash",
         OBJ + "Contrast_Rgb1112_8511_11", OBJ + "Btd8511_Btd1112_Corr", PIX + "cloud_emissivity_ch14_tot",
         PIX + "ash_probability_IR", PIX + "cloud_beta_1112_tot"]
for h in VALIDACION[9:]:
    d = cargar(npz, h)
    P = f(d, PIX + "ash_probability"); S = f(d, PIX + "ash_probability_subset")
    V = np.isfinite(P)
    sube = V & (P - S > 0.01)
    sal += np.round((VR.logit(P) - VR.logit(S))[sube], 2).tolist()
    y += sube[V].tolist()
    for k in vars_:
        X.setdefault(k, []).extend(f(d, k)[V].tolist())
y = np.array(y, bool)
u, c = np.unique(sal, return_counts=True)
print("pixeles con P valida %d ; con P > subset %d" % (len(y), y.sum()))
print("saltos de log-odds (valor redondeado: veces):", dict(zip(u.tolist(), c.tolist())))


def auc(x, yy):
    ok = np.isfinite(x)
    x, yy = x[ok], yy[ok]
    r = np.argsort(np.argsort(x, kind="stable"), kind="stable").astype(float)
    uu, inv = np.unique(x, return_inverse=True)
    s = np.zeros(len(uu)); cc = np.zeros(len(uu))
    np.add.at(s, inv, r); np.add.at(cc, inv, 1)
    r = (s / cc)[inv]
    n1 = yy.sum(); n0 = len(yy) - n1
    return (r[yy].sum() - n1 * (n1 - 1) / 2) / (n1 * n0) if n1 and n0 else np.nan


for k in vars_:
    x = np.array(X[k], float)
    print("  AUC %.3f  %-60s mediana sube %.4g  no sube %.4g" % (auc(x, y), k.replace("p__vcat_", ""), np.nanmedian(x[y]), np.nanmedian(x[~y])))
