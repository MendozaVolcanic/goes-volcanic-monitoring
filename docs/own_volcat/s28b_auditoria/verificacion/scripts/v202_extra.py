r"""V202/V204/V205 (verificador, S28b): segunda pasada sobre los mismos disparos por cuadro
(D:\goes_notas\s28\s28b\v202\cubos_v202.npz), para cerrar lo que la primera dejó abierto:

A. 205: el p por día con la corrección +1 (la observación entra a su propio nulo, como en toda permutación), con las
   variantes de qué días de 2025 cuentan (todos los 62 aunque no se evalúen, los que evalúan algo, los que evalúan la
   mitad o el 80 % del patrón). Sin +1 un p de 0 sólo dice "más que toda combinación vista".
B. 205: pN con el día como conglomerado por dos caminos más: linealización (razón de proporciones con días como
   conglomerados, t con días con P menos 1 grados de libertad) y Mann-Whitney entre días.
C. 204: P contra N dentro del día sólo de tarde (12 a 24 UTC), porque las clases P y N de VOLCAT nunca conviven a la
   misma hora de un día (N es "nada en +-60 min"), y los N del mismo día son sobre todo de noche.
D. 202: el 14-11 con todas las variantes de días de 2025, también con +1.

Uso: python -I -B v202_extra.py
"""
import importlib.util
import io
import json
import os
import sys

import numpy as np
from scipy import stats

AQUI = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("v202_analisis", os.path.join(AQUI, "v202_analisis.py"))
A = importlib.util.module_from_spec(spec)
_real = sys.stdout
sys.stdout = io.TextIOWrapper(io.BytesIO(), encoding="utf-8")   # el análisis base ya quedó en analisis.log; aquí se reusan sus funciones
spec.loader.exec_module(A)
sys.stdout = _real
sys.stdout.reconfigure(encoding="utf-8")
CL, ND, DETS = A.CL, A.ND, A.DETS
Zo, Un, An, S23 = A.Zo, A.Un, A.An, A.S23
OUT = {}


def vals_ref(D, ref, g, variante, excluir=None):
    """Valores del patrón g en los días de referencia. Variantes: 'todos62' (todo día, no evaluado cuenta 0; sólo 2025),
    'crudo' (días con algún cuadro evaluado, no evaluado cuenta 0), 'cob0.5', 'cob0.8', 'cob1.0' (fracción por n)."""
    if ref == "2025":
        Ar, er = D.A25, D.ev25
    else:
        Ar, er = D.A26 & D.N, D.N
    if variante == "todos62":
        return np.array([int(Ar[d, g].sum()) for d in range(Ar.shape[0]) if d != excluir])
    if variante == "crudo":
        return A.valores(Ar, er, g, "crudo", excluir=excluir)[0]
    return A.valores(Ar, er, g, "escala", float(variante[3:]), excluir=excluir)[0]


def p_dia(D, ref, variante, unidad="dia", mas1=True, sin_dia=None):
    pats = [p for p in D.patrones(unidad) if p[0] != sin_dia]
    obs = sum(a for *_, a in pats)
    listas, nref = [], []
    for d, g, a in pats:
        v = vals_ref(D, ref, g, variante, excluir=d if ref != "2025" else None)
        nref.append(int(len(v)))
        if mas1:
            v = np.append(v, a)
        listas.append(v.astype(int))
    if any(len(v) == 0 for v in listas):
        return {"p": None, "dias_ref_por_patron": nref}
    return {"p": A.conv_p(listas, obs), "obs": obs, "dias_ref_por_patron": nref}


# ---------------------------------------------------------------- A. p por día con +1
a = {}
for nom, D in (("S23a anillo", S23), ("S25a zona", Zo), ("S26a unión", Un)):
    x = {}
    for ref in ("2025", "N2026"):
        for var in (("todos62",) if ref == "2025" else ()) + ("crudo", "cob0.5", "cob0.8"):
            for unidad in ("dia", "episodio"):
                r1 = p_dia(D, ref, var, unidad, mas1=True)
                r0 = p_dia(D, ref, var, unidad, mas1=False)
                x[f"{ref}_{unidad}_{var}"] = {"p_con_mas1": r1["p"], "p_sin_mas1": r0["p"], "dias_ref_por_patron": r1["dias_ref_por_patron"]}
    a[nom] = x
OUT["A_p_por_dia"] = a
# S23a: el 08-11 solo, contra los días de 2025 a sus horas
d08 = (A.datetime(2026, 11, 8) - A.T26).days
g08 = np.flatnonzero(S23.P[d08])
h08 = int(S23.A26[d08, g08].sum())
x = {"P_evaluados": int(len(g08)), "alcanzados": h08, "horas": f"{A.hhmm(g08[0])} a {A.hhmm(g08[-1])} UTC"}
for var in ("todos62", "crudo", "cob0.5", "cob0.8", "cob1.0"):
    v = vals_ref(S23, "2025", g08, var)
    x[var] = {"dias": int(len(v)), "max": int(v.max()), "dias_ge_obs": int((v >= h08).sum()),
              "p_rango": float((1 + (v >= h08).sum()) / (1 + len(v)))}
ne = S23.ev25[:, g08].sum(1)
hh = S23.A25[:, g08].sum(1)
x["top_2025"] = [f"{A.f25(d)} {int(hh[d])}/{int(ne[d])}" for d in np.argsort(-hh)[:5]]
m = ne >= 7
x["beta_binomial_cola_8_de_13"] = A.betabin_cola(hh[m], ne[m], h08, len(g08))[0]
OUT["A_S23a_08_11_solo"] = x

# ---------------------------------------------------------------- B. pN con días como conglomerados
b = {}
for nom, D in (("S25a zona", Zo), ("S26a unión", Un), ("S26a anillo a p*", An)):
    dP, sP = np.nonzero(D.P)
    psl = sorted(set(sP.tolist()))
    cerca_h = np.array([any(A.dslot(s, y) <= A.W_AZAR for y in psl) for s in range(144)])
    Nc = D.N & cerca_h[None, :]
    aP, nP = (D.A26 & D.P).sum(1).astype(float), D.P.sum(1).astype(float)
    aN, nN = (D.A26 & Nc).sum(1).astype(float), Nc.sum(1).astype(float)
    RP, RN = aP.sum() / nP.sum(), aN.sum() / nN.sum()
    u = (aP - RP * nP) / nP.sum() - (aN - RN * nN) / nN.sum()
    dias = (nP + nN) > 0
    Dn = int(dias.sum())
    var = Dn / (Dn - 1) * float((u[dias] ** 2).sum())
    t = (RP - RN) / np.sqrt(var)
    gl = int((nP > 0).sum()) - 1
    # entre días: tasa de cada día con P (en sus P) contra tasa de cada día sin P (en sus N cercanos, mínimo 6 cuadros)
    tp = (aP / np.maximum(nP, 1))[nP > 0]
    sinP = (nP == 0) & (nN >= 6)
    tn = (aN / np.maximum(nN, 1))[sinP]
    mw = stats.mannwhitneyu(tp, tn, alternative="greater")
    conP = nP > 0
    b[nom] = {"R_P": f"{int(aP.sum())}/{int(nP.sum())}", "R_N_cerca": f"{int(aN.sum())}/{int(nN.sum())}",
              "fisher_por_cuadro": float(stats.fisher_exact([[aP.sum(), nP.sum() - aP.sum()], [aN.sum(), nN.sum() - aN.sum()]],
                                                            alternative="greater")[1]),
              "dias_con_P": int(conP.sum()), "dias_con_N_cerca": int((nN > 0).sum()),
              "N_cerca_en_dias_con_P": f"{int(aN[conP].sum())}/{int(nN[conP].sum())}",
              "N_cerca_en_dias_sin_P": f"{int(aN[~conP].sum())}/{int(nN[~conP].sum())}",
              "conglomerado_t": round(float(t), 2), "gl": gl, "p_conglomerado": float(stats.t.sf(t, gl)),
              "tasas_dias_con_P": [round(float(v), 2) for v in tp], "dias_sin_P_con_6_N_cerca": int(sinP.sum()),
              "dias_sin_P_con_tasa_mayor_que_0": int((tn > 0).sum()), "dias_sin_P_tasa_max": round(float(tn.max()), 2),
              "dias_sin_P_tasas_altas": [f"{A.f26(d)} {int(aN[d])}/{int(nN[d])}" for d in np.flatnonzero(sinP) if aN[d] / nN[d] >= 0.25],
              "p_mann_whitney_entre_dias": float(mw.pvalue)}
    # lo mismo sacando cada día con P (¿descansa en un día?)
    sin = {}
    for x_ in np.flatnonzero(nP > 0):
        k = dias & (np.arange(ND) != x_)
        rp, rn = aP[k].sum() / nP[k].sum(), aN[k].sum() / nN[k].sum()
        uu = (aP[k] - rp * nP[k]) / nP[k].sum() - (aN[k] - rn * nN[k]) / nN[k].sum()
        tt = (rp - rn) / np.sqrt(k.sum() / (k.sum() - 1) * float((uu ** 2).sum()))
        sin[A.f26(x_)] = {"R_P": f"{int(aP[k].sum())}/{int(nP[k].sum())}", "R_N": round(float(rn), 3),
                          "p_conglomerado": float(stats.t.sf(tt, gl - 1))}
    b[nom]["sin_cada_dia_p_conglomerado"] = sin
OUT["B_pN_conglomerados"] = b

# ---------------------------------------------------------------- C. 204 sólo de tarde
c = {}
tarde = np.arange(144) >= 72
for nom, D in (("S25a zona", Zo), ("S26a unión", Un), ("S26a anillo a p*", An), ("S26a zona a p*", DETS["S26a zona a p*"])):
    T, filas = [], []
    for d in range(ND):
        Ps = np.flatnonzero(D.P[d] & tarde)
        Ns = np.flatnonzero(D.N[d] & tarde)
        if not len(Ps):
            continue
        aa, cc = int(D.A26[d, Ps].sum()), int(D.A26[d, Ns].sum()) if len(Ns) else 0
        T.append((aa, len(Ps) - aa, cc, len(Ns) - cc))
        filas.append(f"{A.f26(d)}: P {aa}/{len(Ps)} ({A.hhmm(Ps[0])}-{A.hhmm(Ps[-1])}), N {cc}/{len(Ns)}"
                     + (f" ({A.hhmm(Ns[0])}-{A.hhmm(Ns[-1])})" if len(Ns) else ""))
    r = A.mh(T)
    sin = {}
    for i, f in enumerate(filas):
        q = A.mh(T[:i] + T[i + 1:])
        sin[f[:5]] = [q["OR"], q["IC95"]]
    # días sin P: fracción alcanzada de sus N de tarde
    conP = np.array([D.P[d].any() for d in range(ND)])
    tasas = []
    for d in np.flatnonzero(~conP):
        Ns = np.flatnonzero(D.N[d] & tarde)
        if len(Ns) >= 12:
            tasas.append((A.f26(d), int(D.A26[d, Ns].sum()), int(len(Ns))))
    c[nom] = {"MH_tarde": r, "por_dia_tarde": filas, "MH_tarde_sin_cada_dia": sin,
              "dias_sin_P_con_12_N_de_tarde": len(tasas), "de_ellos_con_algun_alcanzado": [t for t in tasas if t[1] > 0]}
    # dónde caen los N del mismo día: noche (00 a 12 UTC) contra tarde, sólo en días con P
    nn = D.N[conP]
    c[nom]["N_de_dias_con_P_noche_00a12"] = f"{int((D.A26[conP] & nn)[:, ~tarde].sum())}/{int(nn[:, ~tarde].sum())}"
    c[nom]["N_de_dias_con_P_tarde_12a24"] = f"{int((D.A26[conP] & nn)[:, tarde].sum())}/{int(nn[:, tarde].sum())}"
OUT["C_204_tarde"] = c

# ---------------------------------------------------------------- D. 202 con todas las variantes
d14 = (A.datetime(2026, 11, 14) - A.T26).days
g14 = np.flatnonzero(Zo.P[d14])
h14 = int(Zo.A26[d14, g14].sum())
dd = {}
for var in ("todos62", "crudo", "cob0.5", "cob0.8", "cob1.0"):
    v = vals_ref(Zo, "2025", g14, var)
    dd[var] = {"dias": int(len(v)), "max": int(v.max()), "dias_ge_20": int((v >= h14).sum()),
               "p_rango_con_mas1": float((1 + (v >= h14).sum()) / (1 + len(v)))}
dd["dias_2025_con_evaluados_a_cualquier_hora"] = int((Zo.ev25.sum(1) > 0).sum())
dd["dias_2025_evaluados_del_patron"] = sorted(int(x) for x in Zo.ev25[:, g14].sum(1))
OUT["D_202_variantes"] = dd

print(json.dumps(OUT, ensure_ascii=False, indent=1, default=float))
json.dump(OUT, open(os.path.join(A.SAL, "V202_204_205_extra.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1,
          default=float)
