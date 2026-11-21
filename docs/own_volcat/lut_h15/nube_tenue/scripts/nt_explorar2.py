r"""Nube tenue, exploración 2 (SÓLO cuadros 1 a 5, nivel A; no decide).

(a) Tramo 0,2 a 0,5: ¿la omisión de la tabla β(12/11) × β(7,3/11) la decide la emisividad de la banda de 7,3 µm?
    La tabla trae MIN_73EMISS_TOT = 0,1 y EMISS10_TOT_MIN_8511_PREDICTORS = 0,05 (ch10 de ABI = 7,3 µm). ε(7,3) se
    despeja de β(7,3/11) y εtot(11) de VOLCAT: β = ln(1 − ε73)/ln(1 − ε11)  →  ε73 = 1 − (1 − ε11)^β.
(b) Tramo < 0,2: búsqueda amplia. εtot reemplazado por el centro de cualquier casillero, β(12/11) total
    reemplazado por cualquier casillero, y cualquier subconjunto de las 8 tablas.
Salida: ../resultados/nt_explorar2.txt
"""
import itertools
import os
import sys

import numpy as np

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nt_comun as N  # noqa: E402

LV, E = N.LV, N.E
out = open(os.path.join(N.RES, "nt_explorar2.txt"), "w", encoding="utf-8")


def p(*a):
    print(*a); print(*a, file=out, flush=True)


ent, agua, v, q = N.cargar(E.ELIGE)
lv = N.logit(v)
sat = N.no_saturado(v)
BTD = [t for t in LV.IR_S1 if t[0] == "EMISS14_TOT_BTD1112_IR"][0]
TAB = N.SIETE + [BTD]
C = np.stack([N.contrib(ent, agua, t) for t in TAB], 1)
L7 = N.L0 + C[:, :7].sum(1)
mal = sat & (np.abs(L7 - lv) >= 1e-3)
j73 = N.NOMBRES.index("BETA1112_TOT_BETA7311_TOT_IR")
j85 = [N.NOMBRES.index("BETA1112_TOT_BETA8511_TOT_IR"), N.NOMBRES.index("BETA1112_OPAQUE_BETA8511_OPAQUE_IR")]
sin73 = np.abs(L7 - C[:, j73] - lv) < 1e-3
with np.errstate(all="ignore"):
    e73 = 1 - (1 - ent["eps"]) ** ent["b73"]

p("(a) Tramo 0,2 a 0,5, no saturados, β(7,3/11) finito")
s = sat & (ent["eps"] >= 0.2) & (ent["eps"] < 0.5) & np.isfinite(ent["b73"])
ex7 = s & ~mal
exs = s & mal & sin73
p(f"  exactos con 7 tablas: {ex7.sum()}, exactos sólo sin la de 7,3: {exs.sum()}, otros: {(s & mal & ~sin73).sum()}")
for nom, m in (("exactos con 7", ex7), ("exactos sin 7,3", exs)):
    p(f"  ε73 en {nom}: p0/p1/p5/p50/p95/p99/p100 {np.nanpercentile(e73[m], [0, 1, 5, 50, 95, 99, 100]).round(4)}")
for u in (0.08, 0.09, 0.095, 0.1, 0.105, 0.11):
    pred = e73 < u
    p(f"  umbral ε73 < {u}: separa exactos-con-7 (pred falso) {np.mean(~pred[ex7]):.4f}, "
      f"exactos-sin-7,3 (pred verdadero) {np.mean(pred[exs]):.4f}")

# Regla A: tabla 7,3 sólo si ε73 >= 0,1 ; tabla(s) 8,5 sólo si ε73 >= 0,05 (ensayo)
def regla(C, e73, u73=0.1, u85=None, ent=ent):
    use73 = np.isfinite(e73) & (e73 >= u73)
    L = N.L0 + C[:, :7].sum(1) - np.where(use73, 0, C[:, j73])
    if u85 is not None:
        use85 = np.isfinite(e73) & (e73 >= u85)
        for j in j85:
            L = L - np.where(use85, 0, C[:, j])
    return L

for u85 in (None, 0.05):
    LA = regla(C, e73, 0.1, u85)
    okA = np.abs(LA - lv) < 1e-3
    p(f"  Regla ε73 >= 0,1 para 7,3" + ("" if u85 is None else f" y ε73 >= {u85} para 8,5") +
      f": exactos no saturados por tramo  <0,2 {okA[sat & (ent['eps']<0.2)].mean():.4f}  "
      f"0,2-0,5 {okA[sat & (ent['eps']>=0.2) & (ent['eps']<0.5)].mean():.4f}  >=0,5 {okA[sat & (ent['eps']>=0.5)].mean():.4f}")
# Los que siguen sin calzar en 0,2-0,5: ¿qué los distingue? (8,5)
LA = regla(C, e73, 0.1)
resto = sat & (ent["eps"] >= 0.2) & (ent["eps"] < 0.5) & (np.abs(LA - lv) >= 1e-3)
sin85 = np.abs(LA - C[:, j85].sum(1) - lv) < 1e-3
p(f"  resto en 0,2-0,5 tras regla 7,3: {resto.sum()}; de ellos se arreglan quitando las dos de 8,5: {np.mean(sin85[resto]):.3f}")
for k in ("b85", "b85op", "b_tot", "b_op", "eps", "btd"):
    p(f"   {k:6s} resto(sin85 ok) p5/50/95 {np.nanpercentile(ent[k][resto & sin85], [5, 50, 95]).round(3)}  "
      f"exactos 0,2-0,5 {np.nanpercentile(ent[k][s & ~resto], [5, 50, 95]).round(3)}")
p(f"   ε73 resto(sin85 ok) {np.nanpercentile(e73[resto & sin85], [0, 5, 50, 95, 100]).round(4)}; NaN {np.mean(~np.isfinite(e73[resto & sin85])):.3f}")

# (b) Tramo < 0,2
p("\n(b) Tramo < 0,2: búsqueda εtot × β(12/11) total × subconjunto de 8 tablas")
s2 = sat & (ent["eps"] < 0.2)
idx = np.where(s2)[0]
sub = {k: (x[idx] if isinstance(x, np.ndarray) and x.shape == agua.shape else x) for k, x in ent.items()}
ag = agua[idx]; lvs = lv[idx]
masks = np.array(list(itertools.product([0, 1], repeat=8)), float)
edges = LV.EPS_EDGES
eps_ops = [("orig", None)] + [(f"bin{b}", 0.5 * (edges[b] + edges[b + 1])) for b in range(6)]
lo, db, nb = LV.EJES["b1112"]
bt_ops = [("orig", None)] + [(f"b{b}", lo + (b + 0.5) * db) for b in range(nb)]
mejor = np.zeros(len(idx), bool)
conteo = {}
for en, ev in eps_ops:
    for bn, bv in bt_ops:
        r = {}
        if ev is not None:
            r["eps"] = np.where(np.isfinite(sub["eps"]), ev, np.nan)
        if bv is not None:
            r["b_tot"] = np.full(len(idx), bv)
        Cx = np.stack([N.contrib(sub, ag, t, reemplazo=r) for t in TAB], 1)
        ok = np.abs(N.L0 + Cx @ masks.T - lvs[:, None]) < 1e-3
        anyok = ok.any(1)
        mejor |= anyok
        for k in np.where(ok.sum(0) > 0)[0]:
            conteo[(en, bn, k)] = int(ok[:, k].sum())
p(f"  n={len(idx)}; explicados por alguna combinación: {mejor.mean():.4f}")
for (en, bn, k), c in sorted(conteo.items(), key=lambda x: -x[1])[:25]:
    usa = [(N.NOMBRES[j] if j < 7 else "BTD") for j in range(8) if masks[k, j] == 1]
    p(f"   {c:6d} ({c/len(idx):.3f}) eps={en} b_tot={bn} usa {usa}")
out.close()
