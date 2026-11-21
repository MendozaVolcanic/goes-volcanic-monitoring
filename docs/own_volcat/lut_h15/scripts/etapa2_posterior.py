r"""C3 (H15) etapa 2, POSTERIOR (no decide): la variante que sugiere el diagnóstico (7 tablas IR, sin la de BTD,
modo b, conjuntas) medida en los cuadros 6 a 10 con la regla del criterio, por tramo de εtot; y la figura de un
cuadro (09:41) con la probabilidad de VOLCAT, la nuestra y su diferencia.
"""
import json, os, sys
import numpy as np
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lut_volcat as LV  # noqa: E402
import etapa2_validar as E  # noqa: E402

T = LV.Tablas()
gfs = dict(np.load(os.path.join(E.ML, "gfs_ttropo.npz")))
LV.CONJUNTOS["S2sinBTD"] = [t for t in LV.IR_S1 + LV.IR_8511 if t[0] != "EMISS14_TOT_BTD1112_IR"]
out = {}
for nivel in ("A", "B"):
    P, V, EPS = [], [], []
    for h in E.VALIDA:
        A, B, agua, v = E.cuadro(h, gfs)
        ent = A if nivel == "A" else B
        L, _ = LV.log_odds(T, "S2sinBTD", ent, agua, modo="b", comb="J")
        P.append(LV.prob(L)); V.append(v); EPS.append(A["eps"])
    p, v, e = map(np.concatenate, (P, V, EPS))
    m = E.metricas(p, v)
    out[f"nivel{nivel}_todo"] = {**m, "cumpliria": E.cumple(m)}
    for lo, hi in ((0.0, 0.2), (0.2, 0.5), (0.5, 1.01)):
        s = (e >= lo) & (e < hi)
        out[f"nivel{nivel}_eps_{lo}_{hi}"] = E.metricas(p[s], v[s])
with open(os.path.join(E.RES, "etapa2_posterior_sin_btd.json"), "w", encoding="utf-8") as f:
    json.dump(out, f, indent=1, ensure_ascii=False)
for k, m in out.items():
    print(k, {x: (round(y, 3) if isinstance(y, float) else y) for x, y in m.items()
              if x in ("n", "n_volcat_ge05", "frac_dif_le_005", "kappa_05", "frac_ge05_recuperada", "cumpliria")})

# Figura: cuadro 09:41, nivel A, variante elegida por el criterio (S2,b,J) y la posterior sin BTD
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
h = "094100"
A, B, agua, v = E.cuadro(h, gfs)
sh = (301, 500)
pc, _ = LV.log_odds(T, "S2", A, agua, modo="b", comb="J")
ps, _ = LV.log_odds(T, "S2sinBTD", A, agua, modo="b", comb="J")
fig, ax = plt.subplots(2, 2, figsize=(12, 7.5), constrained_layout=True)
im = ax[0, 0].imshow(v.reshape(sh), vmin=0, vmax=1, cmap="magma"); ax[0, 0].set_title("VOLCAT ash_probability_IR")
ax[0, 1].imshow(LV.prob(pc).reshape(sh), vmin=0, vmax=1, cmap="magma"); ax[0, 1].set_title("Nuestra, variante del criterio (8 tablas)")
d1 = (LV.prob(pc) - v).reshape(sh); d2 = (LV.prob(ps) - v).reshape(sh)
im2 = ax[1, 0].imshow(d1, vmin=-1, vmax=1, cmap="RdBu_r"); ax[1, 0].set_title("Nuestra (8 tablas) menos VOLCAT")
ax[1, 1].imshow(d2, vmin=-1, vmax=1, cmap="RdBu_r"); ax[1, 1].set_title("Posterior: sin tabla de BTD (7) menos VOLCAT")
fig.colorbar(im, ax=ax[0, :], shrink=0.8, label="probabilidad")
fig.colorbar(im2, ax=ax[1, :], shrink=0.8, label="diferencia")
for a in ax.ravel():
    a.set_xticks([]); a.set_yticks([])
fig.suptitle("Mauna Loa, GOES-17, 28-11-2022 09:41 UTC (noche). Nivel A: εtot y β de VOLCAT; tablas de VOLCAT leídas por nosotros")
fig.savefig(os.path.join(E.RES, "etapa2_mapa_094100.png"), dpi=90)
print("figura ok")
