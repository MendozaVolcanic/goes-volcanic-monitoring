r"""S31g: acercamiento de color verdadero (10 m) a +-4 km del crater, 25-11 y su referencia del 23-11, con la mascara
de S20b. Solo para leer la forma de lo que sale del crater; no cambia la mascara ni el rotulo de la regla.

Uso: python -I -B s31g_s2_zoom.py
"""
import math
import os
import sys

import numpy as np

sys.stdout.reconfigure(encoding="utf-8")
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import s31g_s2_25nov as G  # noqa: E402

C, P = G.C, G.P


def main():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    m = 4000.0
    hoy = G.tci(P.item_e84(G.OBJ_ID), medio_m=m)
    ref = G.tci(P.item_e84("S2B_19HBV_20261123_0_L2A"), medio_m=m)
    fig, ax = plt.subplots(1, 2, figsize=(16, 8), constrained_layout=True)
    ext = [-4, 4, -4, 4]
    for j, (t, a) in enumerate((("25-11 14:43 UTC (Sentinel-2C)", hoy), ("23-11 14:53 UTC (Sentinel-2B, referencia)", ref))):
        ax[j].imshow(np.clip(a.astype(float) * 1.0, 0, 255).astype("uint8"), extent=ext)
        ax[j].plot(0, 0, "^", mfc="none", mec="yellow", ms=12)
        tt = np.linspace(0, 2 * math.pi, 200)
        ax[j].plot(np.sin(tt), np.cos(tt), "y:", lw=0.8)
        ax[j].set_title(f"Color verdadero 10 m, {t}")
        ax[j].set_xlabel("km al E del crater")
        ax[j].set_ylabel("km al N")
    fig.suptitle("Nevados de Chillan, +-4 km del crater (triangulo). Circulo: 1 km")
    fig.savefig(os.path.join(os.path.dirname(AQUI), "figuras", "s2_2026-11-25_zoom.png"), dpi=70)


if __name__ == "__main__":
    main()
