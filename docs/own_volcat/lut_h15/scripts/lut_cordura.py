r"""Etapa 1 de C3 (H15): comprobación de cordura de la lectura de la LUT de píxel.

Razón de densidades ceniza/nube por bin de beta(12/11) total y de eps_tot en la tabla IR
EMISS14_TOT_BETA1112_TOT_IR, y marginales de la tabla de BTD para justificar su eje.
Lee D:\\goes_cache\lut_h15\lut_pixel.npz (de lut_exportar.py). python -I.
"""
import sys

import numpy as np

sys.stdout.reconfigure(encoding="utf-8")
z = np.load(r"D:\\goes_cache\lut_h15\lut_pixel.npz")
EPS = [0.01, 0.03, 0.10, 0.20, 0.50, 0.90, 1.00]
for sup in ("LAND", "WATER"):
    a = z[f"EMISS14_TOT_BETA1112_TOT_IR_ASH_{sup}_PIX"][:, :, 0]
    c = z[f"EMISS14_TOT_BETA1112_TOT_IR_CLD_{sup}_PIX"][:, :, 0]
    print(f"== {sup}: razón ASH/CLD, filas = bin de beta(12/11) total, columnas = bin de eps_tot")
    print("beta_bin        " + " ".join(f"[{EPS[j]:.2f},{EPS[j+1]:.2f})" for j in range(6)))
    for i in range(42):
        b0 = -0.1 + 0.05 * i
        print(f"[{b0:5.2f},{b0+0.05:5.2f})  " + " ".join(f"{a[i, j] / c[i, j]:12.4g}" for j in range(6)))
    print(f"piso ceniza {a.min():.4g}  piso nube {c.min():.4g}")
    for cl in ("ASH", "CLD"):
        t = z[f"EMISS14_TOT_BTD1112_IR_{cl}_{sup}_PIX"]
        m = t.sum(axis=(1, 2, 3))
        print(f"marginal BTD (33 bins, -3 a 5 cada 0,25) {cl}: " + " ".join(f"{v:.3f}" for v in m))
