r"""S31i, lado a lado (criterio §6, no decide): la cumbre de Antuco en luz reflejada a 0,86 µm (C03) y 1,6 µm (C05), y
las clases del criterio (nieve, nube, suelo), en dos días que disparan de día: 06-11-2024 18:40 UTC (despejado) y
10-11-2026 17:00 UTC (nublado), cada uno junto a la misma fecha y hora de 2025, el año de la base.

Por qué: a 0,86 µm la nieve y la nube brillan y la roca es oscura; a 1,6 µm la nieve se apaga y la nube sigue
brillando. Lado a lado se ve qué hay en la cumbre cuando la zona dispara y qué había en 2025.

Uso: python -I -B s31i_lado_a_lado.py   (escribe figuras/s31i_lado_a_lado.png)
"""
import os
import sys
from datetime import datetime, timedelta

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.colors import ListedColormap  # noqa: E402

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import s31i_medir as W  # noqa: E402

FIG = os.path.join(os.path.dirname(AQUI), "figuras")
CASOS = [("2024-11-06 18:40", "despejado, dispara"), ("2025-11-06 18:40", "2025, base"),
         ("2026-11-10 17:00", "nublado, dispara"), ("2025-11-10 17:00", "2025, base")]
J2000 = datetime(2000, 1, 1, 12)


def main():
    os.makedirs(FIG, exist_ok=True)
    zr, zc = W.subpix(W.zona_sitio("antuco")[0])
    r0, r1, c0, c1 = zr.min() - 14, zr.max() + 15, zc.min() - 14, zc.max() + 15
    la, lo = W.SITIOS["antuco"]
    fig, ax = plt.subplots(len(CASOS), 3, figsize=(10, 3.2 * len(CASOS)))
    cmap = ListedColormap(["#8c6d4f", "#e8f4ff", "#ff7f0e"])
    for i, (cuando, rot) in enumerate(CASOS):
        dt = datetime.strptime(cuando, "%Y-%m-%d %H:%M")
        f = np.load(os.path.join(W.L1B, f"{dt:%Y%m%d_%H%M}.npz"))
        tm = J2000 + timedelta(seconds=float(np.mean(f["C05_tb"])))
        mu = np.cos(np.radians(W.zenit_solar(tm, la, lo)))
        r3 = (f["C03_rad"] * f["C03_kappa0"] / mu)[r0:r1, c0:c1]
        r5 = (f["C05_rad"] * f["C05_kappa0"] / mu)[r0:r1, c0:c1]
        nv, nb = W.clases(r3, r5)
        cl = np.where(nb, 2, np.where(nv, 1, 0))
        for j, (img, tit, kw) in enumerate(((r3, "0,86 µm", dict(cmap="gray", vmin=0, vmax=1)),
                                            (r5, "1,6 µm", dict(cmap="gray", vmin=0, vmax=0.5)),
                                            (cl, "clases", dict(cmap=cmap, vmin=0, vmax=2)))):
            a = ax[i, j]
            a.imshow(img, interpolation="nearest", **kw)
            a.scatter(zc - c0, zr - r0, s=6, facecolors="none", edgecolors="red", linewidths=0.6)
            a.set_xticks([])
            a.set_yticks([])
            a.set_title(f"{cuando} UTC, {rot}\n{tit}" if j == 0 else tit, fontsize=8)
    fig.text(0.5, 0.005, "Píxeles de 1 km; círculos rojos: subpíxeles de la zona de Antuco. Clases: café suelo, "
             "celeste nieve, naranjo nube (umbrales del criterio §3).", ha="center", fontsize=8)
    fig.tight_layout(rect=(0, 0.02, 1, 1))
    out = os.path.join(FIG, "s31i_lado_a_lado.png")
    fig.savefig(out, dpi=110)
    print(out)


if __name__ == "__main__":
    main()
