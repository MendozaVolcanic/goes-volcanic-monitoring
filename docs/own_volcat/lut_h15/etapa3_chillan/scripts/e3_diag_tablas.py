r"""H15 etapa 3, posterior (no decide): qué tabla frena la probabilidad en la huella.

Por qué: la huella tiene β(12/11) mediano 0,88 (lado ceniza) y aun así P mediana ~4e-4. Se recalcula, con las
entradas guardadas en e3_pixeles.csv.gz (banda S0), la contribución en log-odds de cada una de las 7 tablas (con R1,
R2 y R3 aplicadas como en la cadena). Aproximación declarada: β(8,5/11) opaco no se guardó en el CSV y su tabla se
omite aquí (en la cadena sí entró).
Salida: resultados/e3_diag_tablas.txt. Uso: python -I e3_diag_tablas.py
"""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import e3_comun as K  # noqa: E402
import nt_comun as N  # noqa: E402
import nt_regla as NR  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")


def main():
    d = pd.read_csv(os.path.join(K.RES, "e3_pixeles.csv.gz"))
    d = d[(d.banda == "S0") & (d.valido == 1)]
    lin = []
    for rol in ("h", "c"):
        x = d[d.rol == rol]
        ent = {k: x[k].to_numpy(float) for k in ("eps", "b_tot", "b73", "b85", "b_op")}
        n = len(x)
        ent.update(b85op=np.full(n, np.nan), b_low=np.full(n, np.nan), b_mid=np.full(n, np.nan),
                   btd=np.zeros(n), btclr=np.full(n, 280.0))
        agua = np.zeros(n, bool)
        Cm = NR.contribuciones(ent, agua, r2=True)
        e73 = NR.eps73(ent)
        usa73 = np.isfinite(e73) & (e73 >= 0.1)
        c85 = ~((ent["eps"] < 0.1) & (ent["b85"] > 1.05) & (ent["b85"] < 2.0))
        Cm[:, NR.J73] = np.where(usa73, Cm[:, NR.J73], 0.0)
        for j in NR.J85:
            Cm[:, j] = np.where(c85, Cm[:, j], 0.0)
        L = N.L0 + Cm.sum(1)
        lin.append(f"rol {rol}: n {n}  prior log-odds {N.L0:.2f}  suma mediana {np.median(Cm.sum(1)):.2f}  "
                   f"logit final mediano {np.median(L):.2f}  usa 7,3 {usa73.mean():.3f}  usa 8,5 {c85.mean():.3f}")
        for j, nom in enumerate(N.NOMBRES):
            c = Cm[:, j]
            lin.append(f"   {nom:40s} p10 {np.percentile(c, 10):+7.2f}  p50 {np.median(c):+7.2f}  p90 {np.percentile(c, 90):+7.2f}")
    open(os.path.join(K.RES, "e3_diag_tablas.txt"), "w", encoding="utf-8").write("\n".join(lin) + "\n")
    print("\n".join(lin))


if __name__ == "__main__":
    main()
