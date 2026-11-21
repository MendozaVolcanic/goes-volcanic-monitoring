r"""C3 (H15) etapa 2, diagnóstico POSTERIOR (no decide): la tabla de BTD sólo con BTD en [LUT_MIN_VALID, LUT_MAX_VALID]
(-5 y 0 K, leídos en la tabla). Cuadros 1 a 5, nivel A, las otras 7 tablas IR (S2) en modo b.
Prueba ejes del BTD y bordes de la compuerta; informa la fracción de logit exacto (|dL| < 1e-3).
"""
import os, sys
import numpy as np
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lut_volcat as LV  # noqa: E402
import etapa2_validar as E  # noqa: E402

T = LV.Tablas()
gfs = dict(np.load(os.path.join(E.ML, "gfs_ttropo.npz")))
resto = [t for t in LV.IR_S1 + LV.IR_8511 if t[0] != "EMISS14_TOT_BTD1112_IR"]
btdt = [t for t in LV.IR_S1 if t[0] == "EMISS14_TOT_BTD1112_IR"]
L0 = np.log(LV.PRIOR / (1 - LV.PRIOR))
Ls, Bs, V, BTD = [], {}, [], []
ejes = {"-3a5_0.25": (-3.0, 0.25, 33), "-5a3_0.25": (-5.0, 0.25, 33), "-8a0_0.25": (-8.0, 0.25, 33),
        "-4a4_0.25": (-4.0, 0.25, 33)}
for h in E.ELIGE:
    A, B, agua, v = E.cuadro(h, gfs)
    LV.CONJUNTOS["_r"] = resto
    L, _ = LV.log_odds(T, "_r", A, agua, modo="b", comb="J")
    Ls.append(L); V.append(v); BTD.append(A["btd"])
    LV.CONJUNTOS["_b"] = btdt
    for k, ej in ejes.items():
        LV.EJES["btd"] = ej
        Lb, _ = LV.log_odds(T, "_b", A, agua, modo="b", comb="J")
        Bs.setdefault(k, []).append(Lb - L0)
LV.EJES["btd"] = (-3.0, 0.25, 33)
L = np.concatenate(Ls); v = np.concatenate(V); btd = np.concatenate(BTD)
with np.errstate(all="ignore"):
    lv = np.log(v / (1 - v))
sat = np.isfinite(v) & (v > 1e-6) & (v < 1 - 1e-6)
print("no saturados", sat.sum(), " sin tabla BTD exacto:", np.mean(np.abs(L - lv)[sat] < 1e-3).round(4))
for k in ejes:
    rb = np.concatenate(Bs[k])
    for lo, hi, inc in [(-5, 0, "[]"), (-5, 0, "[)"), (-25, 0, "[)"), (-5, 0.0, "(]"), (-1e9, 0, "[]")]:
        g = (btd >= lo) & ((btd <= hi) if inc[1] == "]" else (btd < hi))
        Lt = L + np.where(g, rb, 0.0)
        ex = np.abs(Lt - lv) < 1e-3
        print(f"eje {k:10s} compuerta {inc[0]}{lo},{hi}{inc[1]}: exacto {ex[sat].mean():.4f}  "
              f"(en BTD<0: {ex[sat & (btd < 0)].mean():.4f}, n={int((sat & (btd < 0)).sum())}; en BTD>=0: {ex[sat & (btd >= 0)].mean():.4f})")
ex7 = np.abs(L - lv) < 1e-3
print(f"sin tabla BTD, exacto en BTD<0: {ex7[sat & (btd < 0)].mean():.4f} (n={int((sat & (btd < 0)).sum())}); "
      f"en BTD>=0: {ex7[sat & (btd >= 0)].mean():.4f}")
