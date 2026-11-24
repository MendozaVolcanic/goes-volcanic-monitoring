"""S21c, POST HOC: hoja de contactos de R (C02) del 28-10 para inspeccion visual. Salida en figuras/."""
import os, sys
from datetime import datetime, timedelta
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import s21c_comun as K
import s21c_medir as MX
REC = 16
for sat in (18, 19):
    b, _ = MX.sesgo(sat)
    c = MX.cuadro(sat, datetime(2026, 10, 28, 17, 30))
    r0, c0 = K.a_pixel(sat, *K.VENT, K.CRATER_KM * 1000)
    cr, cc = int(round(r0 - c[2] + b[0])), int(round(c0 - c[3] + b[1]))
    ts = [datetime(2026, 10, 28, 15, 0) + timedelta(minutes=10 * i) for i in range(46)]
    fig, ax = plt.subplots(6, 8, figsize=(12, 9.5))
    for a in ax.ravel():
        a.set_xticks([]); a.set_yticks([])
    for i, t in enumerate(ts):
        x = MX.cuadro(sat, t)
        if x is None:
            continue
        img = x[0][cr - REC:cr + REC + 1, c0 - c[3] - REC if False else cc - REC:cc + REC + 1]
        a = ax.ravel()[i]
        a.imshow(img, cmap="gray", vmin=np.nanpercentile(img, 2), vmax=np.nanpercentile(img, 99.5))
        a.plot(REC, REC, "^", mfc="none", mec="m", ms=4)
        mk = " *" if MX.en_pulso(t) else ""
        a.set_title(f"{t:%H:%M}{mk}", fontsize=7, color="r" if mk else "k")
    fig.suptitle(f"GOES-{sat} C02 28-10, rotulos 15:00 a 22:30 (rojo con *: 0 a 30 min tras un pulso REAV). "
                 f"Recorte {2 * REC + 1} px, contraste por cuadro", fontsize=8)
    fig.tight_layout()
    fig.savefig(os.path.join(os.path.dirname(__file__), "..", "figuras", f"hoja_28-10_g{sat}.png"), dpi=75)
    plt.close(fig)
