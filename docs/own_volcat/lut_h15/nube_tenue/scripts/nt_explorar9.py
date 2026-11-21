r"""Nube tenue, exploración 9 (SÓLO cuadros 1 a 5, nivel A; no decide).

¿Qué decide si VOLCAT usa las tablas de β(8,5/11)? Con R1+R2 aplicadas, se toman los píxeles donde esas tablas
aportan (|contrib| > 1e-3) y que quedan exactos con ellas (clase 0) o sólo sin ellas (clase 1). Un árbol de decisión
poco profundo (sólo para ver qué variable corta y dónde; la regla final tiene que tener sentido físico) y, para el
mejor corte de cada variable sola, su exactitud.
Salida: ../resultados/nt_explorar9.txt
"""
import os
import sys

import numpy as np

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nt_comun as N  # noqa: E402
import nt_regla as R  # noqa: E402

LV, E = N.LV, N.E
out = open(os.path.join(N.RES, "nt_explorar9.txt"), "w", encoding="utf-8")


def p(*a):
    print(*a); print(*a, file=out, flush=True)


ent, agua, v, q = N.cargar(E.ELIGE)
lv = N.logit(v)
sat = N.no_saturado(v)
e73 = R.eps73(ent)
C2 = R.contribuciones(ent, agua, r2=True)
L = R.logit_regla(C2, ent, r1=True)
c85 = C2[:, R.J85].sum(1)
inf = sat & (np.abs(c85) > 1e-3)
con = inf & (np.abs(L - lv) < 1e-3)
sin = inf & (np.abs(L - c85 - lv) < 1e-3) & ~con
m = con | sin
y = sin[m].astype(int)
with np.errstate(all="ignore"):
    F = {
        "eps": ent["eps"], "e73(falta=-1)": np.where(np.isfinite(e73), e73, -1), "b85": ent["b85"], "b85op": ent["b85op"],
        "b_tot": ent["b_tot"], "b_op": ent["b_op"], "btd": ent["btd"], "b_low(falta=-1)": np.where(np.isfinite(ent["b_low"]), ent["b_low"], -1),
        "b_mid(falta=-1)": np.where(np.isfinite(ent["b_mid"]), ent["b_mid"], -1),
        "bt10-clr10": ent["bt10"] - ent["clr10"], "bt14-clr14": ent["bt14"] - ent["clr14"], "btclr": ent["btclr"],
        "sesgo_btd": ent["btd"] - (ent["clr14"] - ent["clr15"]), "bt14": ent["bt14"],
        "b85-b_tot": ent["b85"] - ent["b_tot"],
    }
X = np.stack([F[k][m] for k in F], 1)
p(f"píxeles informativos: con 8,5 {con.sum()}, sólo sin 8,5 {sin.sum()}")
from sklearn.tree import DecisionTreeClassifier, export_text  # noqa: E402
for prof in (1, 2, 3, 4):
    t = DecisionTreeClassifier(max_depth=prof, random_state=0).fit(X, y)
    p(f"\nÁrbol profundidad {prof}: exactitud {t.score(X, y):.4f}")
    p(export_text(t, feature_names=list(F), decimals=4))
p("Mejor corte de una sola variable:")
for k, x in F.items():
    xs = x[m]
    mejor = (0, None, None)
    for u in np.unique(np.nanpercentile(xs, np.linspace(0.5, 99.5, 200))):
        for lado in ("<", ">="):
            pred = (xs < u) if lado == "<" else (xs >= u)
            acc = np.mean(pred == y)
            if acc > mejor[0]:
                mejor = (acc, u, lado)
    p(f"   {k:16s} sin 8,5 si {k} {mejor[2]} {mejor[1]:.4f}: exactitud {mejor[0]:.4f}")
out.close()
