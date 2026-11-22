"""H19, exploracion en el BLOQUE DE ELECCION: pertenencia de objetos al grupo de alerta.
Uso: python h19_explora8.py NPZ_DIR"""
import sys
import os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from h19_comun import cargar, f, PIX, ELECCION, guardia
from h19_objetos import tabla_objetos

npz = sys.argv[1]
guardia(ELECCION)
np.set_printoptions(linewidth=220, suppress=True, precision=3)
TA, TI = [], []
for h in ELECCION:
    d = cargar(npz, h)
    a = tabla_objetos(d, "A__", "idA"); i = tabla_objetos(d, "I__", "idI")
    a["fr"] = np.full(len(a["n"]), ELECCION.index(h)); i["fr"] = np.full(len(i["n"]), ELECCION.index(h))
    TA.append(a); TI.append(i)
    aom = d[PIX + "Ash_Object_Mask"]; ag = d["p__Ash_Group_Id_2d"] > 0; ig = d["p__Ice_Group_Id_2d"] > 0
    ina = d["idA"] >= 0
    print("%s  codigos Ash_Object_Mask: en objetos ASHOBJ %s | en ig %s | pixeles de ig que no estan en ningun objeto ASHOBJ: %d de %d" % (
        h, dict(zip(*[x.tolist() for x in np.unique(aom[ina], return_counts=True)])),
        dict(zip(*[x.tolist() for x in np.unique(aom[ig], return_counts=True)])), (ig & ~ina).sum(), ig.sum()))


def junta(T):
    ks = set(T[0])
    for t in T:
        ks &= set(t)
    return {k: np.concatenate([t[k] for t in T]) for k in ks}


for nom, T in (("ASHOBJ", junta(TA)), ("ICEOBJ", junta(TI))):
    sel = T["sel"]
    print("\n== %s: objetos %d, seleccionados %d (pixeles sel %d de %d)" % (nom, len(sel), sel.sum(), T["n"][sel].sum(), T["n"].sum()))
    for k in sorted(T):
        if k in ("sel", "fr", "grupo"):
            continue
        x = T[k]
        s1 = x[sel]; s0 = x[~sel]
        with np.errstate(all="ignore"):
            print("  %-28s sel: min %.3g med %.3g max %.3g (nan %d) | no sel: p50 %.3g p99 %.3g max %.3g  | no sel >= min(sel): %d" % (
                k, np.nanmin(s1) if np.isfinite(s1).any() else np.nan, np.nanmedian(s1) if np.isfinite(s1).any() else np.nan,
                np.nanmax(s1) if np.isfinite(s1).any() else np.nan, (~np.isfinite(s1)).sum(),
                np.nanpercentile(s0, 50) if np.isfinite(s0).any() else np.nan, np.nanpercentile(s0, 99) if np.isfinite(s0).any() else np.nan,
                np.nanmax(s0) if np.isfinite(s0).any() else np.nan,
                (s0 >= np.nanmin(s1)).sum() if np.isfinite(s1).any() else -1))
    for regla, pred in (("frac_ig>=0.5", T["frac_ig"] >= 0.5), ("frac_ig>0", T["frac_ig"] > 0),
                        ("frac_prev_ig>=0.5", T["frac_prev_ig"] >= 0.5), ("frac_prev_ag>0", T["frac_prev_ag"] > 0),
                        ("frac_iom>=0.5", T["frac_iom"] >= 0.5)):
        tp = (pred & sel).sum(); fp = (pred & ~sel).sum(); fn = (~pred & sel).sum()
        w = T["n"]
        print("  regla %-18s TP %d FP %d FN %d  prec %.3f sens %.3f | por pixeles: prec %.3f sens %.3f" % (
            regla, tp, fp, fn, tp / max(tp + fp, 1), tp / max(tp + fn, 1),
            w[pred & sel].sum() / max(w[pred].sum(), 1), w[pred & sel].sum() / max(w[sel].sum(), 1)))
    if nom == "ICEOBJ":
        for fr in range(13):
            m = (T["fr"] == fr)
            s = m & sel
            print("   cuadro %s: sel n=%s frac_prev_ig=%s ; no sel con frac_prev_ig>0: %d (max n %s)" % (
                ELECCION[fr], T["n"][s], T["frac_prev_ig"][s], (m & ~sel & (T["frac_prev_ig"] > 0)).sum(),
                T["n"][m & ~sel & (T["frac_prev_ig"] > 0)].max() if (m & ~sel & (T["frac_prev_ig"] > 0)).any() else 0))
