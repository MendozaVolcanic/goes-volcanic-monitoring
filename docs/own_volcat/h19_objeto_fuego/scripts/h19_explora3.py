"""H19, exploracion en el BLOQUE DE ELECCION: (a) donde P difiere de subset, (b) arbol de decision
para subset alto dentro del grupo. Uso: python h19_explora3.py NPZ_DIR"""
import sys
import os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from h19_comun import cargar, f, PIX, OBJ, TRK, VCB, PROP, ELECCION, guardia
from sklearn.tree import DecisionTreeClassifier, export_text

npz = sys.argv[1]
horas = ELECCION
guardia(horas)
X, Y, G, names = [], [], [], None
for h in horas:
    d = cargar(npz, h)
    P = f(d, PIX + "ash_probability"); S = f(d, PIX + "ash_probability_subset")
    IR = f(d, PIX + "ash_probability_IR"); SW = f(d, PIX + "ash_probability_SW_IR")
    ag = d["p__Ash_Group_Id_2d"] > 0
    ig = d["p__Ice_Group_Id_2d"] > 0
    V = np.isfinite(P)
    aom = d[PIX + "Ash_Object_Mask"]
    dif = V & (np.abs(P - S) > 0.01)
    print("=== %s V=%d ag=%d  P!=subset %d (P<subset %d, P>subset %d); en esos: P=SW %d, P=IR %d, P<0.5 %d, subset>=0.5 %d ; codigos Ash_Object_Mask en diferencias %s ; en ag %s ; en V fuera de ag %s" % (
        h, V.sum(), ag.sum(), dif.sum(), (dif & (P < S)).sum(), (dif & (P > S)).sum(),
        (dif & (np.abs(P - SW) <= 1e-6)).sum(), (dif & (np.abs(P - IR) <= 1e-6)).sum(), (dif & (P < .5)).sum(),
        (dif & (S >= .5)).sum(),
        dict(zip(*[x.tolist() for x in np.unique(aom[dif], return_counts=True)])),
        dict(zip(*[x.tolist() for x in np.unique(aom[ag], return_counts=True)])),
        dict(zip(*[x.tolist() for x in np.unique(aom[V & ~ag], return_counts=True)]))))
    # subset fuera del grupo de ceniza y dentro
    for nom, m in (("ag", ag), ("V sin ag", V & ~ag)):
        if m.sum():
            print("    [%s] subset=SW %.3f subset=IR %.3f subset=max %.3f subset>=.5 %.3f ; subset alto y SW<.5: %d" % (
                nom, (np.abs(S - SW)[m] <= 1e-6).mean(), (np.abs(S - IR)[m] <= 1e-6).mean(),
                (np.abs(S - np.fmax(IR, SW))[m] <= 1e-6).mean(), (S[m] >= .5).mean(), (m & (S >= .5) & (SW < .5)).sum()))
    if names is None:
        names = [k for k in d if k.startswith("p__") and d[k].dtype.kind in "fiu"
                 and "ash_probability" not in k.replace(TRK, "") and "Group_Id" not in k
                 and "pixel_l" not in k and "idx" not in k and "nwp_" not in k and "scan" not in k
                 and "object_x" not in k and "object_y" not in k and "object_id" not in k]
    m = ag
    X.append(np.column_stack([np.nan_to_num(f(d, k)[m], nan=-999.0) for k in names]))
    Y.append((S[m] >= 0.5).astype(int)); G.append(np.full(m.sum(), horas.index(h)))
X = np.vstack(X); Y = np.concatenate(Y); G = np.concatenate(G)
print("\nArbol para subset>=0.5 dentro del grupo de ceniza. n=%d, positivos=%d, variables=%d" % (len(Y), Y.sum(), len(names)))
corta = [n.replace("p__vcat_", "") for n in names]
for depth in (1, 2, 3):
    # entrena en cuadros pares del bloque de eleccion, mide en impares (ambos dentro de eleccion)
    tr = (G % 2 == 0); te = ~tr
    t = DecisionTreeClassifier(max_depth=depth, min_samples_leaf=20, random_state=19).fit(X[tr], Y[tr])
    print("profundidad %d: acierto en cuadros impares de eleccion %.4f (base %.4f)" % (depth, t.score(X[te], Y[te]), max(Y[te].mean(), 1 - Y[te].mean())))
    print(export_text(t, feature_names=corta, max_depth=depth))
imp = sorted(zip(t.feature_importances_, corta), reverse=True)[:8]
print("importancias:", [(round(a, 3), b) for a, b in imp])
