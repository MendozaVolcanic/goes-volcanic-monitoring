r"""Nube tenue, exploración 3 (SÓLO cuadros 1 a 5, nivel A; no decide).

Con la regla R1 ya hallada (tabla β(12/11) × β(7,3/11) sólo si ε(7,3) >= 0,1):
(a) Tramo < 0,2: ¿qué valor de β(12/11) total haría exacto cada píxel (reemplazándolo en todas las tablas que lo
    usan)? Y ¿se parece al β que da la relación de la tabla con el sesgo de BTD,
    β = 0,8896 − 0,2046 · sesgo, sesgo = BTD(11−12) observada − BTD de cielo despejado (COEFF_BETA1112_TOT_FCT1,
    rango de sesgo 0,5 a 2 K)?
(b) Resto de 8,5 µm en 0,2 a 0,5: qué variable separa los píxeles que piden omitir las dos tablas de β(8,5/11).
Salida: ../resultados/nt_explorar3.txt
"""
import os
import sys

import numpy as np

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nt_comun as N  # noqa: E402

LV, E = N.LV, N.E
out = open(os.path.join(N.RES, "nt_explorar3.txt"), "w", encoding="utf-8")


def p(*a):
    print(*a); print(*a, file=out, flush=True)


ent, agua, v, q = N.cargar(E.ELIGE)
lv = N.logit(v)
sat = N.no_saturado(v)
with np.errstate(all="ignore"):
    e73 = 1 - (1 - ent["eps"]) ** ent["b73"]
j73 = N.NOMBRES.index("BETA1112_TOT_BETA7311_TOT_IR")
j85 = [N.NOMBRES.index("BETA1112_TOT_BETA8511_TOT_IR"), N.NOMBRES.index("BETA1112_OPAQUE_BETA8511_OPAQUE_IR")]
use73 = np.isfinite(e73) & (e73 >= 0.1)


def L_R1(Cm):
    return N.L0 + Cm.sum(1) - np.where(use73, 0, Cm[:, j73])


C = np.stack([N.contrib(ent, agua, t) for t in N.SIETE], 1)
L1 = L_R1(C)
ok1 = np.abs(L1 - lv) < 1e-3
btd_clr = ent["clr14"] - ent["clr15"]
sesgo = ent["btd"] - btd_clr
b_fct = 0.8896 - 0.2046 * sesgo

# (a) β(12/11) total requerido, por casillero
s = sat & (ent["eps"] < 0.2)
p(f"(a) eps<0,2 no saturados: {s.sum()}; exactos con R1: {ok1[s].mean():.4f}")
lo, db, nb = LV.EJES["b1112"]
req = np.zeros((s.sum(), nb), bool)
for b in range(nb):
    r = {"b_tot": np.full(len(v), lo + (b + 0.5) * db)}
    Cb = C.copy()
    for j, (base, ejes) in enumerate(N.SIETE):
        if any(var == "b_tot" for _, var in ejes):
            Cb[:, j] = N.contrib(ent, agua, N.SIETE[j], reemplazo=r)
    req[:, b] = (np.abs(L_R1(Cb) - lv) < 1e-3)[s]
alguno = req.any(1)
p(f"  con algún casillero de β total (en las tablas que lo usan): {alguno.mean():.4f}")
nreq = req.sum(1)
p(f"  número de casilleros que sirven: p50 {np.median(nreq[alguno]) if alguno.any() else 'nan'}")
ib_vol = np.floor((ent["b_tot"][s] - lo) / db + 1e-9)
ib_fct = np.floor((b_fct[s] - lo) / db + 1e-9)
primero = np.where(alguno, req.argmax(1), -1)
p(f"  β de VOLCAT en eps<0,2: p5/50/95 {np.nanpercentile(ent['b_tot'][s], [5, 50, 95]).round(3)}")
p(f"  sesgo BTD en eps<0,2: p5/50/95 {np.nanpercentile(sesgo[s], [5, 50, 95]).round(3)}")
p(f"  β_fct: p5/50/95 {np.nanpercentile(b_fct[s], [5, 50, 95]).round(3)}")
if alguno.any():
    sirve_fct = np.array([req[i, int(ib_fct[i])] if 0 <= ib_fct[i] < nb else False for i in range(len(ib_fct))])
    p(f"  el casillero de β_fct es uno de los que sirven: {sirve_fct.mean():.4f}")
    p("  casillero requerido (primero) menos casillero de VOLCAT, distribución:")
    d = (primero - ib_vol)[alguno]
    vals, cnt = np.unique(d, return_counts=True)
    p("   ", list(zip(vals.astype(int).tolist(), cnt.tolist()))[:20])

# ¿Y omitir tablas de εtot × β con R1? (eps<0,2): exhaustivo sobre las 6 tablas usables (7,3 fuera)
import itertools
masks = np.array(list(itertools.product([0, 1], repeat=7)), float)
Ls = N.L0 + C[s] @ masks.T
ok = np.abs(Ls - lv[s][:, None]) < 1e-3
p(f"  subconjuntos de las 7 (sin cambiar entradas): explican {ok.any(1).mean():.4f}")

# ¿la diferencia es un factor común? residuo dL vs nº de tablas usadas y vs eps
dl = (L1 - lv)[s]
p("  residuo dL (R1 − VOLCAT) en eps<0,2 por bin de eps:")
ie = np.searchsorted(LV.EPS_EDGES, ent["eps"][s], side="right") - 1
for b in range(-1, 3):
    m = ie == b
    if m.any():
        p(f"   bin {b}: n={m.sum()} dL p5/50/95 {np.percentile(dl[m], [5, 50, 95]).round(3)}  "
          f"logitV p5/50/95 {np.percentile(lv[s][m], [5, 50, 95]).round(3)}  L1 p50 {np.median(L1[s][m]):.3f}")
# ¿VOLCAT en eps<0,2 es función de pocas variables? valores distintos de P
vals, cnt = np.unique(np.round(v[s], 6), return_counts=True)
p(f"  valores distintos de P_VOLCAT en eps<0,2: {len(vals)}; los 10 más frecuentes:")
for k in np.argsort(-cnt)[:10]:
    m = np.round(v[s], 6) == vals[k]
    p(f"   P={vals[k]:.6f} n={cnt[k]} eps p50 {np.median(ent['eps'][s][m]):.3f} b_tot p50 {np.nanmedian(ent['b_tot'][s][m]):.3f} "
      f"b_op p50 {np.nanmedian(ent['b_op'][s][m]):.3f} sesgo p50 {np.nanmedian(sesgo[s][m]):.2f} agua {agua[s][m].mean():.2f}")

# (b) resto de 8,5 en 0,2-0,5
s2 = sat & (ent["eps"] >= 0.2) & (ent["eps"] < 0.5)
resto = s2 & ~ok1
sin85 = np.abs(L1 - C[:, j85].sum(1) - lv) < 1e-3
A_ = resto & sin85
B_ = s2 & ok1
p(f"\n(b) 0,2-0,5: resto {resto.sum()}, se arreglan sin 8,5: {A_.sum()}")
for k, x in (("b85", ent["b85"]), ("b85op", ent["b85op"]), ("b_tot", ent["b_tot"]), ("b_op", ent["b_op"]),
             ("eps", ent["eps"]), ("e73", e73), ("sesgo", sesgo), ("btd", ent["btd"]), ("lower_idx", ent["lower_idx"]),
             ("b_low", ent["b_low"]), ("b_nwp", ent["b_nwp"])):
    p(f"   {k:9s} sin85 p0/5/50/95/100 {np.nanpercentile(x[A_], [0, 5, 50, 95, 100]).round(3)} NaN {np.mean(~np.isfinite(x[A_])):.2f} | "
      f"exactos {np.nanpercentile(x[B_], [0, 5, 50, 95, 100]).round(3)} NaN {np.mean(~np.isfinite(x[B_])):.2f}")
out.close()
