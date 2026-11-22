r"""H22: figuras del informe, solo con las tablas de resultados/ (numeros por cuadro o por grupo; ninguna grilla de
SSEC). Uso: python -I h22_figuras.py
"""
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

AQUI = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(os.path.dirname(AQUI), "resultados")
FIG = os.path.join(os.path.dirname(AQUI), "figuras")
os.makedirs(FIG, exist_ok=True)
sys.stdout.reconfigure(encoding="utf-8")
CLAROS = (20261027, 20261104, 20261106)


def fig_ruido():
    e = pd.read_csv(os.path.join(RES, "ruido_autocorr_espacial.csv"))
    t = pd.read_csv(os.path.join(RES, "ruido_autocorr_temporal.csv"))
    fig, ax = plt.subplots(1, 2, figsize=(10, 3.8))
    lags = [int(c[2:-2]) for c in e.columns if c.startswith("r_")]
    for _, r in e.iterrows():
        claro = r.cielo != "todo"
        nom = ("ΔBT11" if r.medida == "d11" else "ΔBTD") + (", cuadros despejados" if claro else ", todo el cielo")
        ax[0].plot([2 * L for L in lags], [r[f"r_{L}px"] for L in lags], "-o" if claro else "--o", ms=3,
                   color="C3" if r.medida == "d11" else "C0", alpha=1 if claro else 0.5, label=nom)
    ax[0].axhline(0, color="k", lw=0.5)
    ax[0].set_xlabel("separación entre píxeles (km)")
    ax[0].set_ylabel("correlación del residuo")
    ax[0].set_title("Espacial (días sin evento, media del cuadro quitada)", fontsize=9)
    ax[0].legend(fontsize=7)
    for med, col in (("d11", "C3"), ("dbtd", "C0")):
        s = t[(t.medida == med) & (t.desfase_min <= 120)]
        ax[1].plot(s.desfase_min, s.r_local, "-o", ms=3, color=col, label=("ΔBT11" if med == "d11" else "ΔBTD") + ", media local quitada")
        ax[1].plot(s.desfase_min, s.r, "--o", ms=3, color=col, alpha=0.5, label=("ΔBT11" if med == "d11" else "ΔBTD") + ", sin quitar")
    ax[1].set_xlabel("desfase (minutos)")
    ax[1].set_title("Temporal (píxeles que la pluma cruza)", fontsize=9)
    ax[1].set_ylim(0, 1)
    ax[1].legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "ruido_autocorrelacion.png"), dpi=130)
    plt.close(fig)


def fig_prueba():
    pc = pd.read_csv(os.path.join(RES, "pluma_por_cuadro.csv"))
    pc = pc[pc.zona == "lejos"].copy()
    pc["hora"] = pc.cuadro.str[9:]
    pl = pd.read_csv(os.path.join(RES, "ruido_estadistico_placebo_por_cuadro.csv"), dtype={"hora": str})
    pl = pl[pl.grupo == "lejos, todo"]
    horas = list(pc.hora)
    x = {h: i for i, h in enumerate(horas)}
    cp = pd.read_csv(os.path.join(RES, "control_positivo.csv"))
    fig, ax = plt.subplots(1, 3, figsize=(13, 3.9))
    for a, col, nom, zs, zn in ((ax[0], "D_d11", "ΔBT11: píxel menos control despejado (K)", -1.5, -0.5),
                                (ax[1], "D_dbtd", "ΔBTD: píxel menos control despejado (K)", -0.3, -0.15)):
        s = pl[pl.hora.isin(horas)]
        otros = s[~s.dia.isin(CLAROS)]
        cl = s[s.dia.isin(CLAROS)]
        a.scatter([x[h] - 0.12 for h in otros.hora], otros[col], s=10, color="0.75", label="días sin evento, cielo cubierto o parcial")
        a.scatter([x[h] + 0.12 for h in cl.hora], cl[col], s=18, color="C0", label="días sin evento, despejados (27-10, 04-11, 06-11)")
        a.scatter([x[h] for h in pc.hora], pc[col], s=60, color="C3", marker="D", zorder=5, label="14-11, píxeles publicados a más de 30 km")
        for h, n in zip(pc.hora, pc.n):
            a.annotate(str(n), (x[h], a.get_ylim()[0]), fontsize=6, ha="center", va="bottom")
        a.axhline(0, color="k", lw=0.5)
        a.axhline(zs, color="C3", lw=0.8, ls="--")
        a.axhline(zn, color="C2", lw=0.8, ls="--")
        a.axvspan(x["2300"] - 0.5, len(horas) - 0.5, color="0.92", zorder=0)
        a.set_xticks(range(len(horas)))
        a.set_xticklabels([f"{h[:2]}:{h[2:]}" for h in horas], fontsize=7)
        a.set_xlabel("hora UTC del cuadro (fondo gris: entorno nublado, no decide)", fontsize=8)
        a.set_title(nom, fontsize=9)
        a.legend(fontsize=6, loc="lower left" if col == "D_d11" else "upper left")
    ax[0].set_ylim(-14, 5)
    ax[1].set_ylim(-0.6, 0.9)
    for tn, ls in ((255.0, "-o"), (270.0, "--s")):
        s = cp[cp.tnube == tn]
        ax[2].plot(-s["20261114_enfria"], s["20261114_D_d11"], ls, ms=3, color="C3", label=f"ΔBT11, capa a {tn:.0f} K")
        ax[2].plot(-s["20261114_enfria"], s["20261114_D_dbtd"] * 5, ls, ms=3, color="C0", label=f"ΔBTD × 5, capa a {tn:.0f} K")
    ax[2].axhline(-1.5, color="C3", lw=0.8, ls="--")
    ax[2].axhline(-0.3 * 5, color="C0", lw=0.8, ls=":")
    ax[2].set_xlim(0, 6)
    ax[2].set_ylim(-6, 2)
    ax[2].set_xlabel("enfriamiento inyectado en los píxeles lejanos del 14-11 (K)", fontsize=8)
    ax[2].set_title("Control positivo: respuesta del estadístico", fontsize=9)
    ax[2].legend(fontsize=6)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "prueba_pluma_lejana.png"), dpi=130)
    plt.close(fig)


if __name__ == "__main__":
    fig_ruido()
    fig_prueba()
    print("figuras en", FIG)
