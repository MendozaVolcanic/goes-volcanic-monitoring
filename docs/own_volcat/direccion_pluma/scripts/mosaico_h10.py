"""H10: mosaico de control visual (descriptivo, no decide). Recorte de +-30 km del PNG VOLCAT alrededor del
crater con la cruz del crater, la flecha de la direccion REAV y la huella decodificada en contorno, y al lado
la BT11,2 de la escena L1b del mismo slot (si esta en cache). Uso: python -I mosaico_h10.py SLOT [SLOT ...]
(SLOT = YYYYmmdd_HHMM). Salida: h10/mosaico_h10.png"""
import os, sys, math
from datetime import datetime
import numpy as np
from PIL import Image
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import comun_h10 as C  # noqa: E402
import direccion_volcat_h10 as D  # noqa: E402

slots = [datetime.strptime(s, "%Y%m%d_%H%M") for s in sys.argv[1:]]
az_reav = {f"{s:%Y%m%d}": a for s, a in ((C.P(e[2]), e[5]) for e in C.EP) if a is not None}
fig, axs = plt.subplots(len(slots), 2, figsize=(8, 3.6 * len(slots)))
axs = np.atleast_2d(axs)
r0 = int(round((C.LAT0 - C.CLAT) / C.DP)); c0 = int(round((C.CLON - C.LON0) / C.DP)); R = int(round(30 / 111 / C.DP))
for i, s in enumerate(slots):
    r = C.INV.get(s); ax = axs[i, 0]
    if r is not None and C.png_path(r["fn"]):
        a = np.asarray(Image.open(C.png_path(r["fn"])).convert("RGB"))
        d = D.decodificar(C.png_path(r["fn"]))
        ax.imshow(a[r0 - R:r0 + R + 1, c0 - R:c0 + R + 1], extent=(-R - .5, R + .5, R + .5, -R - .5))
        if d is not None and d["hv"].any():
            ax.contour(np.arange(-R, R + 1), np.arange(-R, R + 1), d["hv"][r0 - R:r0 + R + 1, c0 - R:c0 + R + 1].astype(float), [0.5], colors="cyan", linewidths=0.8)
    ax.plot(0, 0, "w+", ms=12, mew=2)
    ax.add_patch(plt.Circle((0, 0), 10 / 111 / C.DP / math.cos(0), fill=False, ec="w", ls=":"))
    az = az_reav.get(f"{s:%Y%m%d}")
    if az is not None:
        L = 8
        ax.annotate("", xy=(L * math.sin(math.radians(az)), -L * math.cos(math.radians(az))), xytext=(0, 0), arrowprops=dict(color="yellow", width=1.5))
    ax.set_title(f"VOLCAT {s:%d-%m %H:%M} UTC (flecha: REAV)", fontsize=8); ax.set_xticks([]); ax.set_yticks([])
    sc = C.escena(s); ax2 = axs[i, 1]
    if sc is not None:
        im = ax2.pcolormesh(C.XE, C.YN, sc["b14"], cmap="gray_r", shading="auto")
        ax2.plot(0, 0, "r+", ms=12, mew=2); ax2.set_aspect("equal"); ax2.set_xlim(-30, 30); ax2.set_ylim(-30, 30)
        plt.colorbar(im, ax=ax2, fraction=0.046)
    ax2.set_title("BT11,2 (K), km desde el crater, geometria ABI", fontsize=8)
plt.tight_layout(); out = os.path.join(C.WORK, "mosaico_h10.png"); plt.savefig(out, dpi=90); print(out)
