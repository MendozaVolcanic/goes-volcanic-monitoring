r"""C3 (H15) etapa 2, diagnóstico POSTERIOR (no decide): ¿dónde se separa nuestra probabilidad de la de VOLCAT?

Sólo cuadros 1 a 5 (los de elección), nivel A, variante elegida (S2, b, J). Compara el log-odds nuestro con el
logit de la probabilidad de VOLCAT, por tipo de píxel.
"""
import os, sys
import numpy as np
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lut_volcat as LV  # noqa: E402
import etapa2_validar as E  # noqa: E402

T = LV.Tablas()
gfs = dict(np.load(os.path.join(E.ML, "gfs_ttropo.npz")))
rows = []
for h in E.ELIGE:
    A, B, agua, v = E.cuadro(h, gfs)
    L, n = LV.log_odds(T, "S2", A, agua, modo="b", comb="J")
    d = np.load(os.path.join(E.ML, f"ml_{h}.npz"))
    extra = {k: d[f"geocatDIAGS1__{k}"].astype(float).ravel() for k in ("lower_cloud_idx", "Ash_Object_Mask")}
    extra["Robust_Pixel_Flag"] = d["geocatDIAGS1__vcat_ashdet_obj_2_7_10_11_13_14_15_Robust_Pixel_Flag"].astype(float).ravel()
    extra["sw"] = d["geocatL2__ash_probability_SW_IR"].astype(float).ravel()
    extra["fin"] = d["geocatL2__ash_probability"].astype(float).ravel()
    rows.append((A, agua, v, L, n, extra))
cat = lambda f: np.concatenate([f(r) for r in rows])  # noqa: E731
L = cat(lambda r: r[3]); v = cat(lambda r: r[2]); n = cat(lambda r: r[4]); agua = cat(lambda r: r[1])
A = {k: cat(lambda r, k=k: r[0][k]) for k in rows[0][0]}
X = {k: cat(lambda r, k=k: r[5][k]) for k in rows[0][5]}
p = LV.prob(L)
ok = np.isfinite(v)
dif = np.abs(p - v) > 0.05
print("pixeles validos", ok.sum(), "con |dif|>0,05:", (ok & dif).sum())
with np.errstate(all="ignore"):
    lv = np.log(v / (1 - v))
dl = L - lv
sat = ok & (v > 1e-6) & (v < 1 - 1e-6)
print("logit no saturado:", sat.sum(), "dL mediana", np.median(dl[sat]), "p05/p95", np.percentile(dl[sat], [5, 95]))
print("frac |dL|<1e-3 (no saturados):", np.mean(np.abs(dl[sat]) < 1e-3))
bad = sat & (np.abs(dl) > 1e-2)
print("no saturados con |dL|>0,01:", bad.sum())
vals, cnt = np.unique(np.round(dl[bad], 2), return_counts=True)
o = np.argsort(-cnt)[:15]
print("dL más frecuentes entre los distintos:", list(zip(vals[o], cnt[o])))
for nombre, m in [("todos", ok), ("distintos", ok & dif)]:
    print(f"== {nombre}: n={m.sum()}")
    for k in ("eps", "b_tot", "b_op", "b_low", "b_mid", "b73", "b85", "b85op", "btd"):
        x = A[k][m]
        print(f"  {k:6s} NaN {np.mean(~np.isfinite(x)):.3f}  p5/50/95 {np.nanpercentile(x,[5,50,95]).round(3) if np.isfinite(x).any() else '-'}")
    print("  agua", agua[m].mean().round(3), " clasificadores usados", np.unique(n[m], return_counts=True))
    for k, x in X.items():
        x = x[m]; f = np.isfinite(x)
        print(f"  {k}: finitos {f.mean():.3f}", np.unique(np.round(x[f], 2), return_counts=True) if k in ("lower_cloud_idx", "Ash_Object_Mask", "Robust_Pixel_Flag") and f.any() else (np.nanpercentile(x, [5, 50, 95]).round(3) if f.any() else ""))
# ¿VOLCAT alto y nuestra baja, o al revés?
m1 = ok & (v >= 0.5) & (p < 0.5); m2 = ok & (v < 0.5) & (p >= 0.5)
print("VOLCAT>=0,5 y nuestra<0,5:", m1.sum(), " al revés:", m2.sum())
for nombre, m in (("V alto/nuestra baja", m1), ("V baja/nuestra alta", m2)):
    print(nombre, "dL p5/50/95", np.percentile(dl[m & sat], [5, 50, 95]).round(2) if (m & sat).any() else "", " v p50", np.median(v[m]).round(3), " p p50", np.median(p[m]).round(4))
    for k in ("eps", "b_tot", "b_op", "b_low", "b_mid", "b73", "b85", "btd"):
        x = A[k][m]; print(f"   {k:6s} NaN {np.mean(~np.isfinite(x)):.3f}  p5/50/95 {np.nanpercentile(x,[5,50,95]).round(3) if np.isfinite(x).any() else '-'}")
