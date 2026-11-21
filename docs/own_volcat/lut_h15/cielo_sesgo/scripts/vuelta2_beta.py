r"""Vuelta 2: β(12/11) en nube tenue. Aplica `criterio_vuelta2_beta_2026-11-21.md` (commit 2db5d46, antes de este
script). Base V1 (ε al nadir), N1 (punto frío GFS). H1 = corrección por vapor de la tabla de VOLCAT
(+0,2 si TPW > 2,5 cm, +0,05 si 1,5 < TPW ≤ 2,5, sólo con εtot < 0,25). Elige S en los cuadros 1 a 5 con
0,25 ≤ ε_VOLCAT < 0,5, valida en 6 a 10 y calcula el nivel B con las reglas del frente 1 (nt_regla.py, PR 75,
commit af0e8ca, copia de lectura en D:\goes_cache\cielo_sesgo\nt).

Uso: python -I vuelta2_beta.py   (antes: extraer_tpw.py en venv_hdf4 y gfs_punto_frio.py)
"""
import json
import os
import sys

import numpy as np

sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import cielo_sesgo as CS  # noqa: E402

NT = r"D:\goes_cache\cielo_sesgo\nt\docs\own_volcat\lut_h15\nube_tenue\scripts"
sys.path.insert(1, NT)
import nt_regla as R  # noqa: E402

E = CS.E
TPW = dict(np.load(r"D:\goes_cache\cielo_sesgo\tpw.npz"))
EMAX_H2O = 0.25


def h2o(beta, eps, tpw):
    corr = np.where(tpw > 2.5, 0.2, np.where(tpw > 1.5, 0.05, 0.0))
    return np.where(np.isfinite(eps) & (eps < EMAX_H2O), beta + corr, beta)


def entradas(c, H, S):
    e14, b12, b73 = c.eps("V1", "N1", CS.s4(S))
    if H == "H1":
        b12 = h2o(b12, e14, TPW[c.h])
    return e14, b12, b73


def comparar(cs, H, S, lo, hi, hi_incl=False):
    E14, EV, B12, BV, B73, BV73 = [], [], [], [], [], []
    for c in cs:
        e14, b12, b73 = entradas(c, H, S)
        sel = np.isfinite(c.ev) & np.isfinite(e14) & (c.ev >= lo) & ((c.ev <= hi) if hi_incl else (c.ev < hi))
        E14.append(e14[sel]); EV.append(c.ev[sel]); B12.append(b12[sel]); BV.append(c.bv12[sel])
        B73.append(b73[sel]); BV73.append(c.bv73[sel])
    e14, ev, b12, bv, b73, bv73 = map(np.concatenate, (E14, EV, B12, BV, B73, BV73))
    de = e14 - ev
    k = np.isfinite(b12) & np.isfinite(bv)
    db = b12[k] - bv[k]
    k73 = np.isfinite(b73) & np.isfinite(bv73)
    db73 = b73[k73] - bv73[k73]
    pct = lambda x: [float(v) for v in np.percentile(x, [5, 50, 95])] if len(x) else []  # noqa: E731
    return {"n": int(len(de)), "frac_eps_le_001": float(np.mean(np.abs(de) <= 0.01)), "deps_p05_p50_p95": pct(de),
            "n_beta": int(k.sum()), "frac_b1211_le_002": float(np.mean(np.abs(db) <= 0.02)) if len(db) else None,
            "db1211_p05_p50_p95": pct(db),
            "frac_b7311_le_002": float(np.mean(np.abs(db73) <= 0.02)) if len(db73) else None}


def nivel_B(cs, H, S):
    ENT, AG, V, EV = [], [], [], []
    for c in cs:
        e14, b12, b73 = entradas(c, H, S)
        B = dict(c.A)
        B["eps"], B["b_tot"], B["b73"] = e14.ravel(), b12.ravel(), b73.ravel()
        ENT.append(B); AG.append(c.agua); V.append(c.verdad); EV.append(c.A["eps"])
    ent = {k: np.concatenate([e[k] for e in ENT]) for k in ENT[0]}
    agua, v, ev = map(np.concatenate, (AG, V, EV))
    cond85 = ~((ent["eps"] < 0.1) & (ent["b85"] > 1.05) & (ent["b85"] < 2.0))
    C2 = R.contribuciones(ent, agua, r2=True)
    p = CS.LV.prob(R.logit_regla(C2, ent, r1=True, cond85=cond85))
    out = {"todo": {**E.metricas(p, v), "cumpliria_regla_etapa2": E.cumple(E.metricas(p, v))}}
    for lo, hi in ((0.0, 0.2), (0.2, 0.5), (0.5, 1.01)):
        s = (ev >= lo) & (ev < hi)
        out[f"eps_{lo}_{hi}"] = E.metricas(p[s], v[s])
    return out


def main():
    C = {h: CS.Cuadro(h) for h in E.HORAS}
    c15 = [C[h] for h in E.ELIGE]
    c610 = [C[h] for h in E.VALIDA]
    out = {"criterio": "docs/own_volcat/lut_h15/cielo_sesgo/criterio_vuelta2_beta_2026-11-21.md (commit 2db5d46)",
           "nt_regla": "PR 75, analisis/h15-nube-tenue, commit af0e8ca"}
    out["tpw_cm_p1_p50_p99"] = {h: [float(x) for x in np.nanpercentile(TPW[h], [1, 50, 99])] for h in E.HORAS}

    Ss = ["S0"]
    for tipo, masc, q in [("G", m, q) for m in ("M1", "M2") for q in (25, 50, 75)] + [("L", "M1", 50), ("L", "M2", 50)]:
        Ss.append((tipo, masc, q, (14, 15), "B2"))
    p1 = {}
    for S in Ss:
        p1[CS.nombre_S(S)] = comparar(c15, "H1", S, 0.25, 0.5)
        print("eleccion S", CS.nombre_S(S), round(p1[CS.nombre_S(S)]["frac_b1211_le_002"], 4), flush=True)
    orden = {"S0": 0, "G": 1, "L": 2}
    mejor = max(m["frac_b1211_le_002"] for m in p1.values())
    cand = [k for k, m in p1.items() if m["frac_b1211_le_002"] >= mejor - 0.002]
    sel = min(cand, key=lambda k: orden[k.split("_")[0]])
    S = next(s for s in Ss if CS.nombre_S(s) == sel)
    out["eleccion_S_cuadros_1a5_eps_0.25_0.5_H1"] = p1
    out["S_elegida"] = sel
    print("S elegida:", sel, flush=True)

    val = {}
    for H in ("H1", "H0"):
        for nom, lo, hi, inc in (("0.05_0.2", 0.05, 0.2, False), ("0.2_0.25", 0.2, 0.25, False),
                                 ("0.25_0.5", 0.25, 0.5, False), ("0.5_0.9", 0.5, 0.9, True),
                                 ("0.05_0.9", 0.05, 0.9, True)):
            val[f"{H}_{nom}"] = comparar(c610, H, S, lo, hi, inc)
    out["validacion_cuadros_6a10"] = val
    pr = val["H1_0.05_0.2"]
    out["cumple_principal_beta_0.05_0.2"] = bool(pr["frac_b1211_le_002"] >= 0.80)
    g = val["H1_0.05_0.9"]
    out["cumple_regla_vuelta1"] = bool(g["frac_eps_le_001"] >= 0.80 and g["frac_b1211_le_002"] >= 0.80)
    for k, m in val.items():
        print(k, m["n"], round(m["frac_eps_le_001"], 3), round(m["frac_b1211_le_002"] or 0, 3),
              [round(x, 3) for x in m["db1211_p05_p50_p95"]], flush=True)

    out["nivelB_NT_H1_S"] = nivel_B(c610, "H1", S)
    out["nivelB_NT_H0_S0"] = nivel_B(c610, "H0", "S0")
    for k in ("nivelB_NT_H1_S", "nivelB_NT_H0_S0"):
        print(k, {t: {y: (round(z, 3) if isinstance(z, float) else z) for y, z in m.items()
                      if y in ("n", "n_volcat_ge05", "frac_dif_le_005", "kappa_05", "frac_ge05_recuperada")}
                  for t, m in out[k].items()}, flush=True)
    with open(os.path.join(CS.RES, "vuelta2_beta.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1, ensure_ascii=False)
    print("ok", os.path.join(CS.RES, "vuelta2_beta.json"))


if __name__ == "__main__":
    main()
