"""H19, exploracion en el BLOQUE DE ELECCION: dentro de los pixeles oscuro-opacos del grupo de ceniza,
que separa los pixeles donde la P publicada queda por debajo de subset. Uso: python h19_explora7.py NPZ_DIR"""
import sys
import os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from h19_comun import cargar, f, PIX, PROP, ELECCION, guardia
from sklearn.tree import DecisionTreeClassifier, export_text

npz = sys.argv[1]
guardia(ELECCION)
X, Y, G, PV, names = [], [], [], [], None
for h in ELECCION:
    d = cargar(npz, h)
    P = f(d, PIX + "ash_probability"); S = f(d, PIX + "ash_probability_subset")
    ag = d["p__Ash_Group_Id_2d"] > 0
    m = ag & (S >= .5)
    if m.sum() == 0:
        continue
    if names is None:
        names = [k for k in d if k.startswith("p__") and d[k].dtype.kind in "fiu" and "Group_Id" not in k
                 and "pixel_l" not in k and "nwp_" not in k and "scan" not in k
                 and not k.endswith("ash_probability") and "x_idx" not in k and "y_idx" not in k
                 and "object_x" not in k and "object_y" not in k and "object_id" not in k]
    X.append(np.column_stack([np.nan_to_num(f(d, k)[m], nan=-999.0) for k in names]))
    Y.append((np.abs(P - S)[m] > 0.01).astype(int)); G.append(np.full(m.sum(), ELECCION.index(h))); PV.append(P[m])
X = np.vstack(X); Y = np.concatenate(Y); G = np.concatenate(G); PV = np.concatenate(PV)
corta = [n.replace("p__vcat_", "") for n in names]
print("n=%d  con P<subset: %d" % (len(Y), Y.sum()))
u, c = np.unique(np.round(PV[Y == 1], 4), return_counts=True)
o = np.argsort(-c)[:15]
print("valores de P mas repetidos entre los rebajados:", list(zip(u[o].tolist(), c[o].tolist())), " distintos:", len(u))


def auc(x, y):
    r = np.argsort(np.argsort(x, kind="stable"), kind="stable").astype(float)
    uu, inv = np.unique(x, return_inverse=True)
    s = np.zeros(len(uu)); cc = np.zeros(len(uu))
    np.add.at(s, inv, r); np.add.at(cc, inv, 1)
    r = (s / cc)[inv]
    n1 = y.sum(); n0 = len(y) - n1
    return (r[y == 1].sum() - n1 * (n1 - 1) / 2) / (n1 * n0)


res = sorted(((abs(auc(X[:, j], Y) - .5), auc(X[:, j], Y), corta[j], np.median(X[Y == 1, j]), np.median(X[Y == 0, j]))
              for j in range(X.shape[1])), reverse=True)
for d_, a, n, m1, m0 in res[:25]:
    print("  AUC %.3f %-62s med rebajado %.4g  med igual %.4g" % (a, n, m1, m0))
tr = (G % 2 == 0); te = ~tr
for depth in (1, 2, 3):
    t = DecisionTreeClassifier(max_depth=depth, min_samples_leaf=10, random_state=19).fit(X[tr], Y[tr])
    pr = t.predict(X[te])
    print("profundidad %d: acierto %.4f (base %.4f) sens %.3f prec %.3f" % (depth, (pr == Y[te]).mean(), 1 - Y[te].mean(),
          (pr[Y[te] == 1] == 1).mean(), (Y[te][pr == 1] == 1).mean() if (pr == 1).sum() else np.nan))
    print(export_text(t, feature_names=corta, max_depth=depth))
