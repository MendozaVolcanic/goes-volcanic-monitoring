"""H19, exploracion en el BLOQUE DE ELECCION: la P publicada como filtro espacial de subset.
Uso: python h19_explora6.py NPZ_DIR"""
import sys
import os
import numpy as np
from scipy import ndimage as ndi
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from h19_comun import cargar, f, PIX, ELECCION, guardia

npz = sys.argv[1]
guardia(ELECCION)


def img(d, v, fill=np.nan):
    a = np.full((601, 601), fill, float)
    a[d["iy"], d["ix"]] = v
    return a


tot = {}
ej = []
for h in ELECCION:
    d = cargar(npz, h)
    P = img(d, f(d, PIX + "ash_probability")); S = img(d, f(d, PIX + "ash_probability_subset"))
    V = np.isfinite(P)
    if V.sum() < 100:
        continue
    S0 = np.where(np.isfinite(S), S, 0.0)
    n3 = ndi.uniform_filter(np.isfinite(S).astype(float), 3, mode="constant")
    cands = {
        "subset": S,
        "media3x3 (fuera=0)": ndi.uniform_filter(S0, 3, mode="constant"),
        "media3x3 (solo validos)": ndi.uniform_filter(S0, 3, mode="constant") / np.where(n3 > 0, n3, np.nan),
        "media5x5 (solo validos)": ndi.uniform_filter(S0, 5, mode="constant") / np.where(ndi.uniform_filter(np.isfinite(S).astype(float), 5, mode="constant") > 0, ndi.uniform_filter(np.isfinite(S).astype(float), 5, mode="constant"), np.nan),
        "mediana3x3 (fuera=0)": ndi.median_filter(S0, 3, mode="constant"),
        "min3x3 (fuera=0)": ndi.minimum_filter(S0, 3, mode="constant"),
        "min cruz (fuera=0)": ndi.minimum_filter(S0, footprint=ndi.generate_binary_structure(2, 1), mode="constant"),
        "min(subset, media3x3 validos)": np.fmin(S, ndi.uniform_filter(S0, 3, mode="constant") / np.where(n3 > 0, n3, np.nan)),
    }
    for nom, q in cands.items():
        a = tot.setdefault(nom, [0, 0, 0, 0, 0])
        a[0] += V.sum(); a[1] += (np.abs(q - P)[V] <= 0.01).sum()
        hi = V & (P >= .5); a[2] += hi.sum(); a[3] += (hi & (q >= .5)).sum(); a[4] += (V & (q >= .5)).sum()
    if h == "190100":
        dif = V & (np.abs(P - S) > 0.01)
        ys, xs = np.nonzero(dif)
        for y, x in list(zip(ys, xs))[:6]:
            ej.append((y, x, P[y, x], np.round(S[y - 2:y + 3, x - 2:x + 3], 3), np.round(P[y - 1:y + 2, x - 1:x + 2], 3)))
print("candidata  n  frac|dif|<=0.01  sensibilidad(P>=.5)  precision")
for nom, a in tot.items():
    print("%-32s %6d  %.4f  %.4f  %.4f" % (nom, a[0], a[1] / a[0], a[3] / max(a[2], 1), a[3] / max(a[4], 1)))
for e in ej:
    print("pixel", e[0], e[1], "P=%.4f" % e[2]); print(" subset 5x5:\n", e[3]); print(" P 3x3:\n", e[4])
