"""H19, exploracion en el BLOQUE DE ELECCION: dentro del grupo de ceniza, que variable 2D separa
los pixeles con P publicada alta de los de P baja. Barre todas las variables 2D de L2, L2S1, DIAG, DIAGS1,
L1 y RTM. Uso: python -I h19_explora2.py REF hora [hora...]"""
import sys
import os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from h19_io import ruta, leer, PIX, VALIDACION

ref = sys.argv[1]
horas = [a for a in sys.argv[2:] if not a.startswith("--")]
if any(h in VALIDACION for h in horas) and "--validacion" not in sys.argv:
    sys.exit("cuadro de validacion: no se abre antes de congelar la regla")


def auc(x, y):
    ok = np.isfinite(x)
    x, y = x[ok], y[ok]
    if y.sum() == 0 or (~y).sum() == 0:
        return float("nan"), ok.sum()
    r = np.argsort(np.argsort(x, kind="stable"), kind="stable").astype(float)
    # empates: rango medio
    u, inv = np.unique(x, return_inverse=True)
    s = np.zeros(len(u)); c = np.zeros(len(u))
    np.add.at(s, inv, r); np.add.at(c, inv, 1)
    r = (s / c)[inv]
    n1 = y.sum(); n0 = (~y).sum()
    return (r[y].sum() - n1 * (n1 - 1) / 2) / (n1 * n0), ok.sum()


for h in horas:
    L2 = leer(ruta(ref, "L2", h))
    P = L2[PIX + "ash_probability"]
    ag = L2["Ash_Group_Id_2d"] > 0
    alto = (P >= 0.5)[ag]
    print("=== %s pixeles en grupo de ceniza %d, altos %d" % (h, ag.sum(), alto.sum()))
    qs = np.nanpercentile(P[ag][alto], [0, 5, 25, 50, 75, 95, 100]) if alto.sum() else []
    print("  cuantiles de P alta:", np.round(qs, 4), " P==1 exacto:", (P[ag] == 1).sum(),
          " P baja cuantiles:", np.round(np.nanpercentile(P[ag][~alto], [50, 95, 100]), 6))
    res = []
    for tipo in ["L2", "L2S1", "DIAG", "DIAGS1", "L1", "RTM"]:
        D = L2 if tipo == "L2" else leer(ruta(ref, tipo, h))
        for k, a in D.items():
            if a.ndim == 3:
                capas = [(k + "[%d]" % i, a[:, :, i]) for i in range(a.shape[2])]
            elif a.shape == (601, 601):
                capas = [(k, a)]
            else:
                continue
            for nom, b in capas:
                x = b[ag].astype(float)
                x[x <= -900] = np.nan
                a_, n = auc(x, alto)
                if np.isfinite(a_):
                    res.append((abs(a_ - 0.5), a_, n, tipo, nom, np.nanmedian(x[alto]) if np.isfinite(x[alto]).any() else np.nan,
                                np.nanmedian(x[~alto]) if np.isfinite(x[~alto]).any() else np.nan))
    res.sort(reverse=True)
    for d, a_, n, tipo, nom, m1, m0 in res[:45]:
        print("  AUC %.3f n=%d %-6s %-70s med alto %.4g  med bajo %.4g" % (a_, n, tipo, nom.replace("vcat_", ""), m1, m0))
