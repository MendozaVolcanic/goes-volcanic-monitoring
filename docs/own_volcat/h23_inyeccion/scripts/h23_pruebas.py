r"""H23: pruebas de las piezas numericas de h23_medir.py contra referencias independientes, con datos sinteticos.
No lee ni un dato de GOES. Si alguna falla, sale con codigo 1.

- cuantil_ordenado contra np.nanpercentile.
- AUC por matriz de pares de dias contra sklearn.metrics.roc_auc_score (con empates y con -inf).
- media_movil contra un promedio hecho a mano.
- la inyeccion: con e = 0 no cambia nada; con e = 1 y beta = 1 el pixel queda a T_tope en las dos bandas; el
  signo de la BTD de una capa de ceniza fria (beta < 1) sobre fondo tibio es negativo.
Uso: python -I h23_pruebas.py
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import h23_comun as K  # noqa: E402
import h23_medir as M  # noqa: E402

rng = np.random.default_rng(0)
fallas = []


def comprobar(nombre, ok, detalle=""):
    print(("ok   " if ok else "FALLA"), nombre, detalle)
    if not ok:
        fallas.append(nombre)


# 1. cuantiles con NaN
S = rng.normal(270, 5, (30, 500))
S[rng.random(S.shape) < 0.3] = np.nan
S[:, :5] = np.nan
v, n = M.cuantil_ordenado(np.sort(S, 0), 0.9)
ref = np.full(500, np.nan)
ref[5:] = np.nanpercentile(S[:, 5:], 90, axis=0)
comprobar("cuantil 0,9", np.allclose(v[5:], ref[5:]) and np.isnan(v[:5]).all() and (n[:5] == 0).all())
v, _ = M.cuantil_ordenado(np.sort(S, 0), 0.5)
comprobar("mediana", np.allclose(v[5:], np.nanmedian(S[:, 5:], axis=0)))

# 2. AUC
from sklearn.metrics import roc_auc_score  # noqa: E402
dia = rng.integers(0, 12, 4000)
s0 = np.round(rng.normal(0, 1, 4000), 1)
s1 = np.round(s0 + rng.normal(0.4, 0.5, 4000), 1)
s0[rng.random(4000) < 0.2] = -np.inf
s1[rng.random(4000) < 0.1] = -np.inf
U = M.matriz_u(s1, s0, dia, 12)
nd = np.bincount(dia, minlength=12).astype(float)
auc, lo, hi = M.auc_ic(U, nd)
x = np.concatenate([s1, s0]); x[np.isneginf(x)] = -1e9
ref = roc_auc_score(np.r_[np.ones(4000), np.zeros(4000)], x)
comprobar("AUC contra sklearn", abs(auc - ref) < 1e-9, f"{auc:.6f} vs {ref:.6f}, IC {lo:.3f} a {hi:.3f}")
comprobar("IC contiene el AUC", lo < auc < hi)
r = M.medir(s0.copy(), s0.copy(), dia, True)
comprobar("AUC de lo mismo contra lo mismo = 0,5", abs(r["auc"] - 0.5) < 1e-12, f"{r['auc']:.6f}")
r = M.medir(-s1, -s0, dia, True)
comprobar("espejo", r["sentido"] == "tibio" and abs(r["auc"] - ref) < 1e-9)

# 3. media movil
X = rng.normal(0, 1, (50, 3)); X[10:14, 0] = np.nan
mm = M.media_movil(X, 6, 5)
comprobar("media movil completa", np.isclose(mm[30, 1], X[25:31, 1].mean()))
comprobar("media movil: NaN con menos de 5 validos", np.isnan(mm[13, 0]) and np.isnan(mm[15, 0]))
comprobar("media movil con 5 de 6", np.isclose(mm[18, 0], X[14:19, 0].mean()) and np.isclose(mm[19, 0], X[14:20, 0].mean()))

# 4. inyeccion (coeficientes de Planck de C14 y C15 leidos de un cuadro bajado, es decir, del NetCDF)
import glob  # noqa: E402
with np.load(sorted(glob.glob(os.path.join(K.L1B, "2026*.npz")))[0]) as z0:
    co = {14: z0["co14"], 15: z0["co15"]}
print("Planck C14", co[14], "C15", co[15])
T0 = np.full((4, 2), 285.0)
c = {"co": co, "I14": K.rad_de_bt(T0, co[14]), "I15": K.rad_de_bt(T0 - 1.0, co[15]),
     "Btop14": K.rad_de_bt(np.full((4, 1), 260.0), co[14]), "Btop15": K.rad_de_bt(np.full((4, 1), 260.0), co[15])}
a, b = M.inyectar(c, 0.0, 0)
comprobar("e = 0 no cambia", np.array_equal(a, c["I14"]) and np.array_equal(b, c["I15"]))
a, b = M.inyectar(c, 1.0, 0, beta=1.0)
comprobar("e = 1 deja T_tope", np.allclose(K.bt_de_rad(a, co[14]), 260) and np.allclose(K.bt_de_rad(b, co[15]), 260))
a, b = M.inyectar(c, 0.3, 0, beta=0.7)
d11 = K.bt_de_rad(a, co[14]) - 285.0
dbtd = (K.bt_de_rad(a, co[14]) - K.bt_de_rad(b, co[15])) - 1.0
comprobar("ceniza fria: enfria y baja la BTD", (d11 < 0).all() and (dbtd < 0).all(),
          f"dBT11 {d11[0, 0]:.2f} K, dBTD {dbtd[0, 0]:.2f} K")
comprobar("ida y vuelta de Planck", np.allclose(K.bt_de_rad(K.rad_de_bt(273.15, co[14]), co[14]), 273.15))

print("FALLAS:", fallas if fallas else "ninguna")
sys.exit(1 if fallas else 0)
