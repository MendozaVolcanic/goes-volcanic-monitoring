"""Figura del informe: Chillán noche a noche (fracción de cuadros visibles con >= 10 MW contra máximo MIROVA) y
VRP ABI contra MIROVA por pasada. Lee resultados/noches.csv y resultados/cuadro_contra_pasada.csv.
Uso: python -I vn_figura.py
"""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

RES = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "resultados")
n = pd.read_csv(os.path.join(RES, "noches.csv"), parse_dates=["noche"])
pp = pd.read_csv(os.path.join(RES, "cuadro_contra_pasada.csv"))
ch = n[n.sitio == "Nevados de Chillan"].sort_values("noche")

fig, (a, b) = plt.subplots(1, 2, figsize=(13, 4.2), gridspec_kw=dict(width_ratios=[2.3, 1]))
f = np.where(ch.con_dato, ch.n10 / ch.n_vis.where(ch.n_vis > 0), np.nan)
col = np.where(ch.enc, "#c0392b", "#7f8c8d")
a.bar(ch.noche, f, color=col, width=0.8, label="fracción de cuadros visibles con ≥ 10 MW (rojo: noche encendida)")
sd = ch[~ch.con_dato]
a.scatter(sd.noche, np.full(len(sd), -0.05), marker="x", color="#7f8c8d", s=14, label="sin dato (nube)")
a.axhline(0.25, color="#c0392b", lw=0.8, ls=":")
a.set_ylim(-0.1, 1.05)
a.set_ylabel("fracción de cuadros")
a2 = a.twinx()
a2.plot(ch.noche, ch.mirova_max, "o", color="#2c3e50", ms=3.5, label="MIROVA, máx nocturno (MW)")
a2.axhline(10, color="#2c3e50", lw=0.6, ls="--")
a2.set_ylabel("MIROVA (MW)")
a.axvspan(pd.Timestamp("2026-10-20"), pd.Timestamp("2026-11-19"), color="#f1c40f", alpha=0.15,
          label="periodo de H17 (dentro de muestra)")
a.set_title("Nevados de Chillán, indicador nocturno ABI 3,9 µm contra MIROVA")
h1, l1 = a.get_legend_handles_labels()
h2, l2 = a2.get_legend_handles_labels()
a.legend(h1 + h2, l1 + l2, fontsize=7, loc="upper left")
v = pp[pp.visible]
b.scatter(v.mirova, v.abi, s=12, color="#2c3e50")
m = max(v.mirova.max(), v.abi.max()) * 1.05
b.plot([0, m], [0, m], color="#7f8c8d", lw=0.8)
b.set_xlabel("MIROVA por pasada (MW)")
b.set_ylabel("ABI, cuadro a ≤ 15 min (MW)")
b.set_title("Cuadro contra pasada (cráter visible)")
fig.tight_layout()
fig.savefig(os.path.join(RES, "vn_chillan.png"), dpi=130)
print("ok")
