r"""Vuelta 3: el exceso de nuestro ε(11) en nube tenue. Aplica `criterio_vuelta3_eps11_2026-11-21.md` (commit
1bd1d85, antes de este script) en los cuadros 6 a 10: prueba de las candidatas C1 (ángulo), C2 (nube negra) y C3
(cielo despejado del mar), reporte con la base (V1, N1, S0, H1) y sensibilidad de la probabilidad a ±0,015 en ε(11).

Uso: python -I vuelta3_eps11.py
"""
import json
import os
import sys

import numpy as np
from scipy.stats import spearmanr

sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import vuelta2_beta as V2  # noqa: E402

CS, E, R = V2.CS, V2.CS.E, V2.R
RT, HNUBE = 6371.0, 16.0
TRAMOS = ((0.05, 0.1), (0.1, 0.2), (0.2, 0.3), (0.3, 0.5), (0.5, 0.9))


def corr_h2o(eps, tpw):
    c = np.where(tpw > 2.5, 0.2, np.where(tpw > 1.5, 0.05, 0.0))
    return np.where(np.isfinite(eps) & (eps < V2.EMAX_H2O), c, 0.0)


def por_cuadro(c):
    """Arreglos 1D del cuadro: implícitos de C1, C2, C3 y la base."""
    f = lambda x: np.asarray(x, float).ravel()  # noqa: E731
    mu, ev, tpw = f(c.mu), f(c.ev), f(V2.TPW[c.h])
    with np.errstate(all="ignore"):
        e14s = 1 - (1 - ev) ** (1 / mu)
        bsin = f(c.bv12) - corr_h2o(ev, tpw)
        e15s = 1 - (1 - e14s) ** bsin
    rad = {b: f(CS.E.rad(c.d, c.obs[b], b)) for b in (14, 15)}
    rc = {b: f(CS.E.rad(c.d, c.clr[b], b)) for b in (14, 15)}
    rb = {b: f(CS.E.rad(c.d, c.tcld["N1"], b)) for b in (14, 15)}
    our15 = CS.LV.emisividad(rad[15], rc[15], rb[15])
    with np.errstate(all="ignore"):
        brec = np.log1p(-our15) / np.log1p(-e14s)                        # C1
        tcld = CS.bt_de_rad(rc[14] + (rad[14] - rc[14]) / e14s, c.d, 14)  # C2
        d14 = CS.bt_de_rad((rad[14] - e14s * rb[14]) / (1 - e14s), c.d, 14) - f(c.clr[14])  # C3
        d15 = CS.bt_de_rad((rad[15] - e15s * rb[15]) / (1 - e15s), c.d, 15) - f(c.clr[15])
    sz = np.degrees(np.arccos(mu))
    szh = np.degrees(np.arcsin(np.sin(np.radians(sz)) * RT / (RT + HNUBE)))
    e14, b12, _ = V2.entradas(c, "H1", "S0")
    return {"ev": ev, "mu": mu, "tpw": tpw, "bsin": bsin, "brec": brec, "tcld": tcld, "tn1": f(c.tcld["N1"]),
            "d14": d14, "d15": d15, "sz": sz, "dcos16": np.cos(np.radians(szh)) - mu,
            "e14": f(e14), "b12": f(b12), "bv12": f(c.bv12)}


def sensibilidad(cs, delta, modo):
    ENT, AG, V, M = [], [], [], []
    for c in cs:
        A = {k: np.array(v, float) for k, v in c.A.items()}
        ev = A["eps"]
        tpw = np.asarray(V2.TPW[c.h], float).ravel()
        mu = np.asarray(c.mu, float).ravel()
        sel = np.isfinite(ev) & (ev >= 0.1) & (ev < 0.2)
        evn = ev.copy()
        evn[sel] = ev[sel] + delta
        if modo == "b":
            with np.errstate(all="ignore"):
                l0 = np.log1p(-(1 - (1 - ev) ** (1 / mu)))
                l1 = np.log1p(-(1 - (1 - evn) ** (1 / mu)))
                k = np.where(sel, l0 / l1, 1.0)
            b12sin = A["b_tot"] - corr_h2o(ev, tpw)
            A["b_tot"] = np.where(sel, b12sin * k + corr_h2o(evn, tpw), A["b_tot"])
            for key in ("b73", "b85"):
                A[key] = np.where(sel, A[key] * k, A[key])
        A["eps"] = evn
        ENT.append(A); AG.append(c.agua); V.append(c.verdad); M.append(sel)
    ent = {k: np.concatenate([e[k] for e in ENT]) for k in ENT[0]}
    agua, v, sel = map(np.concatenate, (AG, V, M))
    cond85 = ~((ent["eps"] < 0.1) & (ent["b85"] > 1.05) & (ent["b85"] < 2.0))
    p = CS.LV.prob(R.logit_regla(R.contribuciones(ent, agua, r2=True), ent, r1=True, cond85=cond85))
    ok = sel & np.isfinite(p) & np.isfinite(v)
    d = np.abs(p[ok] - v[ok])
    a, b = p[ok] >= 0.5, v[ok] >= 0.5
    return {"n": int(ok.sum()), "n_volcat_ge05": int(b.sum()), "dP_abs_mediana": float(np.median(d)),
            "dP_abs_p95": float(np.percentile(d, 95)), "frac_dP_gt_005": float(np.mean(d > 0.05)),
            "frac_cruza_05": float(np.mean(a != b)), "ge05_que_se_pierden": int((b & ~a).sum()),
            "lt05_que_pasan": int((~b & a).sum())}


def main():
    cs = [CS.Cuadro(h) for h in E.VALIDA]
    D = [por_cuadro(c) for c in cs]
    X = {k: np.concatenate([d[k] for d in D]) for k in D[0]}
    ev = X["ev"]
    fin = np.isfinite(ev)
    out = {"criterio": "docs/own_volcat/lut_h15/cielo_sesgo/criterio_vuelta3_eps11_2026-11-21.md (commit 1bd1d85)"}

    # C1
    c1 = {}
    for lo, hi in TRAMOS:
        q = fin & (ev >= lo) & (ev < hi) & np.isfinite(X["brec"]) & np.isfinite(X["bsin"]) & (np.abs(X["bsin"]) > 0.05)
        r = X["brec"][q] / X["bsin"][q] - 1
        c1[f"{lo}_{hi}"] = {"n": int(q.sum()), "mediana_razon_menos_1": float(np.median(r)),
                           "p05": float(np.percentile(r, 5)), "p95": float(np.percentile(r, 95))}
    dcos = np.nanmax(np.abs(X["dcos16"][fin]))
    c1_desc = all(abs(v["mediana_razon_menos_1"]) <= 0.005 for v in c1.values()) and dcos < 0.005
    out["C1_angulo"] = {"por_tramo": c1, "max_abs_dcos_a_16km": float(dcos), "descartada": bool(c1_desc)}

    # C2
    thin = fin & (ev >= 0.05) & (ev < 0.3) & np.isfinite(X["tcld"])
    thick = fin & (ev >= 0.85) & (ev <= 0.98) & np.isfinite(X["tcld"])
    nan_thin = int((fin & (ev >= 0.05) & (ev < 0.3) & ~np.isfinite(X["tcld"])).sum())
    m_thin, m_thick = float(np.median(X["tcld"][thin])), float(np.median(X["tcld"][thick]))
    out["C2_nube_negra"] = {
        "tcld_implicita_tenue_p5_p50_p95": [float(x) for x in np.percentile(X["tcld"][thin], [5, 50, 95])],
        "tcld_implicita_espesa_p5_p50_p95": [float(x) for x in np.percentile(X["tcld"][thick], [5, 50, 95])],
        "tenue_sin_solucion": nan_thin, "n_tenue": int(thin.sum()), "n_espesa": int(thick.sum()),
        "punto_frio_N1_mediana": float(np.median(X["tn1"][thick])),
        "diferencia_medianas_K": m_thin - m_thick, "descartada": bool(abs(m_thin - m_thick) > 10)}

    # C3
    q = fin & (ev >= 0.05) & (ev < 0.3) & np.isfinite(X["d14"]) & np.isfinite(X["d15"])
    md14, md15 = float(np.median(X["d14"][q])), float(np.median(X["d15"][q]))
    r_tpw = float(spearmanr(X["d14"][q], X["tpw"][q]).correlation)
    r_sz = float(spearmanr(X["d14"][q], X["sz"][q]).correlation)
    out["C3_cielo_mar"] = {"n": int(q.sum()), "d14_p5_p50_p95": [float(x) for x in np.percentile(X["d14"][q], [5, 50, 95])],
                           "d15_p5_p50_p95": [float(x) for x in np.percentile(X["d15"][q], [5, 50, 95])],
                           "rho_d14_tpw": r_tpw, "rho_d14_theta": r_sz,
                           "descartada": bool(abs(md15) < 0.2 and md14 <= -0.5 and abs(r_tpw) < 0.2 and abs(r_sz) < 0.3)}
    out["las_tres_descartadas"] = bool(out["C1_angulo"]["descartada"] and out["C2_nube_negra"]["descartada"]
                                       and out["C3_cielo_mar"]["descartada"])

    # Reporte base
    rep = {"eps_por_tramo": {}, "eps_por_theta_0.05_0.3": {}, "beta_H1_por_tramo": {}}
    for lo, hi in TRAMOS:
        s = fin & (ev >= lo) & (ev < hi) & np.isfinite(X["e14"])
        de = X["e14"][s] - ev[s]
        sb = s & np.isfinite(X["b12"]) & np.isfinite(X["bv12"])
        db = X["b12"][sb] - X["bv12"][sb]
        rep["eps_por_tramo"][f"{lo}_{hi}"] = {"n": int(s.sum()), "frac_le_001": float(np.mean(np.abs(de) <= 0.01)),
                                             "mediana": float(np.median(de))}
        rep["beta_H1_por_tramo"][f"{lo}_{hi}"] = {"n": int(sb.sum()), "frac_le_002": float(np.mean(np.abs(db) <= 0.02)),
                                                 "mediana": float(np.median(db))}
    for a, b in ((20, 28), (28, 31), (31, 34), (34, 37), (37, 45)):
        s = fin & (ev >= 0.05) & (ev < 0.3) & (X["sz"] >= a) & (X["sz"] < b) & np.isfinite(X["e14"])
        if s.sum() >= 50:
            de = X["e14"][s] - ev[s]
            rep["eps_por_theta_0.05_0.3"][f"{a}_{b}"] = {"n": int(s.sum()), "frac_le_001": float(np.mean(np.abs(de) <= 0.01)),
                                                        "mediana": float(np.median(de))}
    out["reporte_base_V1_N1_S0_H1"] = rep
    out["nivelB_NT_V1_N1_S0_H1"] = V2.nivel_B(cs, "H1", "S0")

    # Sensibilidad
    sen = {"referencia_nivelA_sin_perturbar": sensibilidad(cs, 0.0, "a")}
    for modo in ("a", "b"):
        for dl in (+0.015, -0.015):
            sen[f"modo_{modo}_{dl:+.3f}"] = sensibilidad(cs, dl, modo)
    out["sensibilidad_eps11_0.1_0.2_nivelA_NT"] = sen

    with open(os.path.join(CS.RES, "vuelta3_eps11.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1, ensure_ascii=False)
    print(json.dumps(out, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
