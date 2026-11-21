r"""C3 (H15) etapa 2, diagnóstico POSTERIOR (no decide): con las 7 tablas IR sin BTD (modo b), ¿qué explica los
píxeles que no salen exactos? Cuadros 1 a 5, nivel A. Compara dL con la contribución de cada tabla y con
contribuciones en bins vecinos (eje corrido), y describe los píxeles no exactos.
"""
import os, sys
import numpy as np
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lut_volcat as LV  # noqa: E402
import etapa2_validar as E  # noqa: E402

T = LV.Tablas()
gfs = dict(np.load(os.path.join(E.ML, "gfs_ttropo.npz")))
siete = [t for t in LV.IR_S1 + LV.IR_8511 if t[0] != "EMISS14_TOT_BTD1112_IR"]
L0 = np.log(LV.PRIOR / (1 - LV.PRIOR))
Ls, V, C, ENT = [], [], [], []
for h in E.ELIGE:
    A, B, agua, v = E.cuadro(h, gfs)
    LV.CONJUNTOS["_7"] = siete
    L, _ = LV.log_odds(T, "_7", A, agua, modo="b", comb="J")
    cols = []
    for t in siete:
        LV.CONJUNTOS["_1"] = [t]
        l1, _ = LV.log_odds(T, "_1", A, agua, modo="b", comb="J")
        cols.append(l1 - L0)
    Ls.append(L); V.append(v); C.append(np.stack(cols, 1)); ENT.append({**A, "agua": agua})
L = np.concatenate(Ls); v = np.concatenate(V); C = np.concatenate(C)
ent = {k: np.concatenate([e[k] for e in ENT]) for k in ENT[0]}
with np.errstate(all="ignore"):
    lv = np.log(v / (1 - v))
sat = np.isfinite(v) & (v > 1e-6) & (v < 1 - 1e-6)
dl = L - lv
mal = sat & (np.abs(dl) >= 1e-3)
print("no saturados", sat.sum(), "no exactos", mal.sum())
for j, t in enumerate(siete):
    # ¿dL igual a la contribución de esta tabla (la tabla sobra en ese píxel)?
    print(f"{t[0]:40s} dL==+contrib: {np.mean(np.abs(dl[mal] - C[mal, j]) < 1e-3):.3f}")
for k in ("eps", "b_tot", "b_op", "b_low", "b_mid", "b73", "b85", "b85op", "btd"):
    x = ent[k]
    print(f"{k:6s} exactos p5/50/95 {np.nanpercentile(x[sat & ~mal], [5, 50, 95]).round(3)}  "
          f"no exactos {np.nanpercentile(x[mal], [5, 50, 95]).round(3)}  NaN no exactos {np.mean(~np.isfinite(x[mal])):.3f}")
# ¿en qué bin de eps y de beta caen los no exactos?
ie = np.searchsorted(LV.EPS_EDGES, ent["eps"], side="right") - 1
for b in range(-1, 7):
    m = sat & (ie == b)
    if m.any():
        print(f"bin eps {b}: n={m.sum()} frac no exacta {np.mean(np.abs(dl[m]) >= 1e-3):.3f}")
fuera = lambda x, lo, hi: (x < lo) | (x >= hi) | ~np.isfinite(x)  # noqa: E731
for k, lo, hi in (("b_tot", -0.1, 2.0), ("b_op", -0.1, 2.0), ("b_low", -0.1, 2.0), ("b_mid", -0.1, 2.0),
                  ("b73", -0.1, 2.0), ("b85", -0.1, 2.0), ("b85op", -0.1, 2.0)):
    f = fuera(ent[k], lo, hi)
    print(f"{k:6s} fuera de eje: entre exactos {np.mean(f[sat & ~mal]):.3f}  entre no exactos {np.mean(f[mal]):.3f}")
vals, cnt = np.unique(np.round(dl[mal], 2), return_counts=True)
o = np.argsort(-cnt)[:10]
print("dL frecuentes:", list(zip(vals[o].tolist(), cnt[o].tolist())))

# Separación: ¿en bin de eps >= 3 los no exactos son los que tienen algún beta NaN o fuera de eje?
algun_nan = np.zeros(len(dl), bool)
for k in ("b_low", "b_mid", "b73", "b85op", "b_op"):
    x = ent[k]
    algun_nan |= ~np.isfinite(x) | (x < -0.1) | (x >= 2.0)
for b in (3, 4):
    m = sat & (ie == b)
    print(f"bin eps {b}: no exactos con algún beta NaN/fuera {np.mean(algun_nan[m & mal]):.3f}; "
          f"exactos con algún beta NaN/fuera {np.mean(algun_nan[m & ~mal]):.3f}; "
          f"no exacto entre los que tienen todo válido {np.mean(mal[m & ~algun_nan]):.3f} (n={int((m & ~algun_nan).sum())})")
m = sat & (ie <= 2)
print(f"eps < 0,2: con todo válido n={int((m & ~algun_nan).sum())}, no exacto {np.mean(mal[m & ~algun_nan]):.3f}")

# Dentro de eps 0,2 a 0,5 y con todo válido: fracción no exacta por tramo de eps
m = sat & (ie == 3) & ~algun_nan
for lo in np.arange(0.20, 0.50, 0.02):
    s = m & (ent["eps"] >= lo) & (ent["eps"] < lo + 0.02)
    if s.any():
        print(f"eps [{lo:.2f},{lo+0.02:.2f}): n={int(s.sum()):6d} no exacto {np.mean(mal[s]):.3f}")
