"""S21c: figuras chicas del informe (en figuras/). Lee D:\\goes_notas\\s21\\c\\medir_mapas.npz y los registros."""
import json
import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import s21c_comun as K  # noqa: E402

AQUI = os.path.dirname(os.path.abspath(__file__))
FIG = os.path.join(AQUI, "..", "figuras")
RES = os.path.join(AQUI, "..", "resultados")
M = np.load(os.path.join(K.TRABAJO, "medir_mapas.npz"))
J = json.load(open(os.path.join(RES, "medir.json"), encoding="utf-8"))
REC = 22          # medio lado del recorte mostrado, px


def crater(sat):
    f0 = J["fila0"][str(sat)]
    b = J["sesgo"][str(sat)]
    r0, c0 = K.a_pixel(sat, *K.VENT, K.CRATER_KM * 1000)
    r1, c1 = K.a_pixel(sat, *K.VENT, (K.CRATER_KM + 2.4) * 1000)
    return (r0 - f0[0] + b[0], c0 - f0[1] + b[1]), (r1 - f0[0] + b[0], c1 - f0[1] + b[1])


def recorte(a, cen):
    r, c = int(round(cen[0])), int(round(cen[1]))
    return a[r - REC:r + REC + 1, c - REC:c + REC + 1], (r - REC, c - REC)


def figura_pulsos():
    for sat in (18, 19):
        (cr, cc), (tr, tc) = crater(sat)
        fig, ax = plt.subplots(4, 6, figsize=(10.5, 7.2))
        for i, nom in enumerate(("E9", "E10", "E11", "E12")):
            for j, rot in enumerate(("pre", "post1", "post2")):
                k = f"g{sat}_{nom}_{rot}"
                fila = J["A"][str(sat)]["pulsos"][nom]["cuadros"][rot]
                for jj, (cual, cmap, vm) in enumerate((("R", "gray", None), ("dR", "RdBu_r", 0.06))):
                    a = ax[i, 2 * j + jj]
                    a.set_xticks([]), a.set_yticks([])
                    if f"{k}_{cual}" not in M.files:
                        a.set_title(f"{nom} {rot}: sin dato", fontsize=7)
                        continue
                    img, (o_r, o_c) = recorte(M[f"{k}_{cual}"], (cr, cc))
                    if cual == "R":
                        a.imshow(img, cmap=cmap, vmin=np.nanpercentile(img, 1), vmax=np.nanpercentile(img, 99))
                        a.set_title(f"{nom} {rot} {fila.get('t')} R", fontsize=7)
                    else:
                        a.imshow(img, cmap=cmap, vmin=-vm, vmax=vm)
                        comp, _ = recorte(M[f"{k}_comp"], (cr, cc))
                        if comp.any():
                            a.contour(comp, levels=[0.5], colors="k", linewidths=0.6)
                        a.set_title(f"dR p={fila.get('p')}", fontsize=7)
                    S, _ = recorte(M[f"S{sat}"], (cr, cc))
                    a.contour(S, levels=[0.5], colors="y", linewidths=0.4)
                    a.plot([cc - o_c, tc - o_c], [cr - o_r, tr - o_r], "-", color="m", lw=0.6)
                    a.plot(cc - o_c, cr - o_r, "^", mfc="none", mec="m", ms=5)
        fig.suptitle(f"GOES-{sat} C02, recorte de {2 * REC + 1} px. Triángulo: cráter; línea magenta: columna de "
                     f"2,4 km; amarillo: región S; negro: componente", fontsize=8)
        fig.tight_layout()
        fig.savefig(os.path.join(FIG, f"pulsos_g{sat}.png"), dpi=80)
        plt.close(fig)


def figura_registro():
    fig, ax = plt.subplots(2, 2, figsize=(6, 6))
    for i, sat in enumerate((18, 19)):
        z = np.load(os.path.join(K.TRABAJO, f"registro_sim_g{sat}_20261028_1440.npz"))
        ax[i, 0].imshow(z["sim"], cmap="gray")
        ax[i, 0].set_title(f"GOES-{sat}: Sentinel-2 16-10 simulado", fontsize=7)
        ax[i, 1].imshow(z["real"], cmap="gray", vmin=np.nanpercentile(z["real"], 1),
                        vmax=np.nanpercentile(z["real"], 99))
        ax[i, 1].set_title(f"GOES-{sat}: C02 28-10 14:40", fontsize=7)
        for a in ax[i]:
            a.set_xticks([]), a.set_yticks([])
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "registro.png"), dpi=80)
    plt.close(fig)


def figura_C():
    fig, ax = plt.subplots(1, 2, figsize=(7, 3.6))
    for i, sat in enumerate((18, 19)):
        p = os.path.join(K.TRABAJO, f"pruebaC_g{sat}.npz")
        if not os.path.exists(p):
            continue
        z = np.load(p)
        (cr, cc), _ = crater(sat)
        img, _ = recorte(z["dR"], (cr, cc))
        P, _ = recorte(z["P0"], (cr, cc))
        ax[i].imshow(img, cmap="RdBu_r", vmin=-0.15, vmax=0.15)
        ax[i].contour(P, levels=[0.5], colors="k", linewidths=0.7)
        ax[i].plot(REC, REC, "^", mfc="none", mec="m", ms=5)
        c = J["C"][f"g{sat}"]["14:30"]
        ax[i].set_title(f"GOES-{sat} 25-10 14:30 menos controles\nA={c.get('A')} p={c.get('p')}", fontsize=7)
        ax[i].set_xticks([]), ax[i].set_yticks([])
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "landsat_25-10.png"), dpi=80)
    plt.close(fig)


if __name__ == "__main__":
    figura_registro()
    figura_pulsos()
    figura_C()
