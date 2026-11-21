r"""H15 etapa 3: métricas y regla de decisión del criterio (criterio_2026-11-21.md, commit 617f531).

Lee resultados/e3_pixeles.csv.gz (e3_cadena.py) y escribe resultados/e3_metricas.json y e3_metricas.txt.
Por banda (S0, S1, S2 deciden; Tm5, Tp5 informan) y variante (V0 decide; V1, V2 informan):
  F_h, F_c (P >= 0,5; cada píxel de huella pesa 1), AUC pareado (empates 0,5), medianas de P,
  IC 95 % por bootstrap jerárquico (eventos y cuadros dentro de cada evento, 2.000 réplicas, semilla fija).
Uso: python -I e3_medir.py
"""
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import e3_comun as K  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
U = 0.5
NB = 2000
DECIDEN = ["S0", "S1", "S2"]


def por_huella(df, col):
    """Una fila por píxel de huella con controles: P huella, F_c del píxel, score AUC del píxel."""
    h = df[df.rol == "h"].set_index("id_huella")
    c = df[df.rol == "c"]
    g = c.groupby("id_huella")[col]
    fc = g.apply(lambda s: float((s >= U).mean()))
    ph = h[col]

    def score(s):
        p = ph[s.name]
        return float(((p > s).sum() + 0.5 * (p == s).sum()) / len(s))
    sc = g.apply(score)
    mc = g.median()
    out = pd.DataFrame({"p_h": ph.loc[sc.index], "fc": fc, "auc": sc, "pc_med": mc})
    out["evento"] = h.loc[sc.index, "evento"].values
    out["cuadro"] = h.loc[sc.index, "cuadro"].values
    out["eps_h"] = h.loc[sc.index, "eps"].values
    return out


def resumen(t):
    return {"n_huella": int(len(t)), "F_h": float((t.p_h >= U).mean()), "F_c": float(t.fc.mean()),
            "AUC": float(t.auc.mean()), "P_med_huella": float(t.p_h.median()), "P_med_ctrl": float(t.pc_med.median()),
            "P_p90_huella": float(t.p_h.quantile(0.9))}


def bootstrap(t, rng):
    evs = sorted(t.evento.unique())
    grupos = {e: {c: g for c, g in t[t.evento == e].groupby("cuadro")} for e in evs}
    res = {"F_h": [], "F_c": [], "AUC": [], "dF": []}
    for _ in range(NB):
        partes = []
        for e in rng.choice(evs, len(evs), replace=True):
            cs = list(grupos[e])
            for c in rng.choice(cs, len(cs), replace=True):
                partes.append(grupos[e][c])
        b = pd.concat(partes)
        fh, fc = float((b.p_h >= U).mean()), float(b.fc.mean())
        res["F_h"].append(fh); res["F_c"].append(fc); res["AUC"].append(float(b.auc.mean())); res["dF"].append(fh - fc)
    return {k: [round(float(np.percentile(v, 2.5)), 4), round(float(np.percentile(v, 97.5)), 4)] for k, v in res.items()}


def categoria(r, ic):
    if r["F_h"] >= 0.50 and r["AUC"] >= 0.70 and ic["AUC"][0] > 0.50:
        return "separa"
    if r["AUC"] < 0.60 or r["F_h"] < 0.20:
        return "no separa"
    return "no concluyente"


def main():
    df = pd.read_csv(os.path.join(K.RES, "e3_pixeles.csv.gz"))
    h0 = df[(df.rol == "h") & (df.banda == "S0")]
    pareo = {"huella_total": int(len(h0)), "con_control": int((h0.n_ctrl > 0).sum()),
             "tol_05": int((h0.tol == 0.5).sum()), "tol_10": int((h0.tol == 1.0).sum()),
             "controles": int(((df.rol == "c") & (df.banda == "S0")).sum())}
    out = {"pareo": pareo, "bandas": {}}
    lineas = [f"pareo: {pareo}"]
    for s in ["S0", "S1", "S2", "Tm5", "Tp5"]:
        d = df[df.banda == s]
        out["bandas"][s] = {}
        for v in ("p_v0", "p_v1", "p_v2"):
            t = por_huella(d, v)
            r = resumen(t)
            ic = bootstrap(t, np.random.default_rng(20261121))
            r["IC95"] = ic
            r["categoria"] = categoria(r, ic)
            r["valido_huella"] = float(d[(d.rol == "h")].valido.mean())
            r["valido_ctrl"] = float(d[(d.rol == "c")].valido.mean())
            r["por_evento"] = {int(e): resumen(g) for e, g in t.groupby("evento")}
            tr = pd.cut(t.eps_h, [-np.inf, 0.1, 0.2, 0.5, np.inf], labels=["<0.1", "0.1-0.2", "0.2-0.5", ">=0.5"])
            r["por_tramo_eps"] = {str(k): resumen(g) for k, g in t.groupby(tr, observed=True)}
            out["bandas"][s][v] = r
            lineas.append(f"{s} {v}: F_h {r['F_h']:.3f} F_c {r['F_c']:.3f} AUC {r['AUC']:.3f} "
                          f"IC_AUC {ic['AUC']} IC_dF {ic['dF']} Pmed_h {r['P_med_huella']:.2e} -> {r['categoria']}")
    cats = [out["bandas"][s]["p_v0"]["categoria"] for s in DECIDEN]
    out["veredicto"] = {"categorias_S0_S1_S2": cats,
                        "robusto": len(set(cats)) == 1,
                        "texto": cats[0] if len(set(cats)) == 1 else "depende del cielo despejado de 11 um no publico",
                        "tierra_Tm5_Tp5": [out["bandas"][s]["p_v0"]["categoria"] for s in ("Tm5", "Tp5")]}
    lineas.append(f"VEREDICTO: {out['veredicto']}")
    json.dump(out, open(os.path.join(K.RES, "e3_metricas.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    open(os.path.join(K.RES, "e3_metricas.txt"), "w", encoding="utf-8").write("\n".join(lineas) + "\n")
    print("\n".join(lineas))


if __name__ == "__main__":
    main()
