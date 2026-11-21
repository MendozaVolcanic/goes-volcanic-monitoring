r"""Nube tenue, exploración 1 (SÓLO cuadros 1 a 5, nivel A; no decide).

Pregunta: en cada píxel donde las 7 tablas no dan exacto el logit de VOLCAT, ¿qué cambio discreto lo explica?
Candidatos: (1) omitir cualquier subconjunto de las 7 tablas, o agregar la de εtot × BTD; (2) correr el casillero de
εtot en todas las tablas; (3) correr el casillero de β de una tabla. Exacto = |Δ logit| < 1e-3.
Salida: ../resultados/nt_explorar1.txt
"""
import itertools
import os
import sys

import numpy as np

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nt_comun as N  # noqa: E402

LV, E = N.LV, N.E
out = open(os.path.join(N.RES, "nt_explorar1.txt"), "w", encoding="utf-8")


def p(*a):
    print(*a); print(*a, file=out, flush=True)


ent, agua, v, q = N.cargar(E.ELIGE)
lv = N.logit(v)
sat = N.no_saturado(v)
BTD = [t for t in LV.IR_S1 if t[0] == "EMISS14_TOT_BTD1112_IR"][0]
TAB = N.SIETE + [BTD]
C = np.stack([N.contrib(ent, agua, t) for t in TAB], 1)        # (npx, 8)
L7 = N.L0 + C[:, :7].sum(1)
dl = L7 - lv
mal = sat & (np.abs(dl) >= 1e-3)
ie = np.searchsorted(LV.EPS_EDGES, ent["eps"], side="right") - 1
p(f"cuadros 1-5: píxeles {len(v)}, no saturados {sat.sum()}, no exactos con 7 tablas {mal.sum()}")
for lo, hi in ((0, 0.2), (0.2, 0.5), (0.5, 1.01)):
    s = sat & (ent["eps"] >= lo) & (ent["eps"] < hi)
    p(f"  eps [{lo},{hi}): no saturados {s.sum()}, no exactos {np.mean(mal[s]):.3f}")

# (1) subconjuntos: incluir/excluir cada una de las 8 tablas
p("\n(1) Subconjuntos de tablas (8 = 7 + BTD). Para cada píxel no exacto, ¿existe un subconjunto exacto?")
masks = np.array(list(itertools.product([0, 1], repeat=8)), float)  # (256, 8)
Ls = N.L0 + C[mal] @ masks.T                                         # (nmal, 256)
ok = np.abs(Ls - lv[mal][:, None]) < 1e-3
p(f"  explicados por algún subconjunto: {ok.any(1).mean():.3f}")
cnt = ok.sum(0)
o = np.argsort(-cnt)[:12]
for k in o:
    falt = [N.NOMBRES[j] if j < 7 else "BTD" for j in range(8) if masks[k, j] == 0 and j < 7]
    extra = " + BTD" if masks[k, 7] == 1 else ""
    p(f"  {cnt[k]:6d} ({cnt[k]/mal.sum():.3f})  omite {falt}{extra}")
# el mismo análisis separado por tramo de eps
for lo, hi in ((0, 0.2), (0.2, 0.5)):
    s = (ent["eps"][mal] >= lo) & (ent["eps"][mal] < hi)
    p(f"  eps [{lo},{hi}): n={s.sum()} explicados por algún subconjunto {ok[s].any(1).mean():.3f}")
    c2 = ok[s].sum(0); o2 = np.argsort(-c2)[:6]
    for k in o2:
        falt = [N.NOMBRES[j] for j in range(7) if masks[k, j] == 0]
        p(f"     {c2[k]:6d} ({c2[k]/max(s.sum(),1):.3f}) omite {falt}{' + BTD' if masks[k,7] else ''}")

# (2) εtot corrido en todas las tablas
p("\n(2) Casillero de εtot corrido en las 7 tablas")
for d in (-2, -1, 1, 2):
    e2 = dict(ent)
    # se reemplaza eps por el centro del bin corrido
    edges = LV.EPS_EDGES
    j = np.clip(ie + d, 0, len(edges) - 2)
    e2["eps"] = np.where(np.isfinite(ent["eps"]), 0.5 * (edges[j] + edges[j + 1]), np.nan)
    Cd = np.stack([N.contrib(e2, agua, t) for t in N.SIETE], 1)
    Ld = N.L0 + Cd.sum(1)
    okd = np.abs(Ld - lv) < 1e-3
    p(f"  corrimiento {d:+d}: exactos entre no exactos {okd[mal].mean():.3f}; "
      f"eps<0,2 {okd[mal & (ent['eps']<0.2)].mean():.3f}; 0,2-0,5 {okd[mal & (ent['eps']>=0.2) & (ent['eps']<0.5)].mean():.3f}")

# (3) β corrido en una tabla
p("\n(3) Casillero de β corrido en UNA tabla (las demás igual)")
for j, (base, ejes) in enumerate(N.SIETE):
    for eje, var in ejes:
        if eje == "eps":
            continue
        lo, db, nb = LV.EJES[eje]
        mejor = []
        for d in (-3, -2, -1, 1, 2, 3):
            r = {var: ent[var] + d * db}
            cj = N.contrib(ent, agua, (base, ejes), reemplazo=r)
            Lj = L7 - C[:, j] + cj
            okj = np.abs(Lj - lv) < 1e-3
            mejor.append((okj[mal].mean(), d))
        f, d = max(mejor)
        p(f"  {base:40s} {var:6s} mejor corrimiento {d:+d}: explica {f:.3f} de los no exactos")

# Valores frecuentes del residuo y su relación con la contribución de cada tabla
p("\nResiduo dL (7 tablas menos VOLCAT) más frecuentes, con la contribución media de cada tabla en esos píxeles")
vals, cnt = np.unique(np.round(dl[mal], 2), return_counts=True)
for k in np.argsort(-cnt)[:12]:
    s = mal & (np.round(dl, 2) == vals[k])
    cs = " ".join(f"{np.median(C[s, j]):+.2f}" for j in range(8))
    p(f"  dL={vals[k]:+.2f} n={cnt[k]:5d}  eps med {np.median(ent['eps'][s]):.3f}  b73 NaN {np.mean(~np.isfinite(ent['b73'][s])):.2f}"
      f"  contrib [{cs}]")
p("  orden de contrib:", N.NOMBRES + ["BTD"])
out.close()
