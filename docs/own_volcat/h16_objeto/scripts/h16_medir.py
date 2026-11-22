r"""H16 §5: métricas y regla del criterio (criterio_2026-11-21.md) sobre resultados/chillan_objetos.csv.

Unidad: el cuadro. F_h = fracción de cuadros con P_obj de la huella >= 0,8; F_c = promedio por cuadro de la
fracción de sus controles con P_obj >= 0,8; AUC pareado = por cuadro, fracción de controles bajo la huella (empate
0,5), promediada. IC 95 % por bootstrap de eventos y de cuadros dentro de cada evento (2.000 réplicas, semilla fija).
Regla (S0 decide): separa si F_h >= 0,5, F_h - F_c >= 0,3 y AUC >= 0,75; no separa si F_h < 0,2 o AUC < 0,6.
Escribe resultados/chillan_metricas.json y chillan_metricas.txt.
Uso: python -I h16_medir.py
"""
import json
import os
import sys

import numpy as np
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")
RES = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "resultados")
U, NB, SEM = 0.8, 2000, 20261121


def por_cuadro(d, col):
    out = []
    for (c, e), g in d.groupby(["cuadro", "evento"]):
        h = g[g.rol == "h"][col]
        k = g[g.rol != "h"][col].to_numpy()
        if not len(h) or not len(k):
            continue
        ph = float(h.iloc[0])
        out.append(dict(cuadro=c, evento=e, p_h=ph, fc=float((k >= U).mean()),
                        auc=float(((ph > k).sum() + 0.5 * (ph == k).sum()) / len(k)), pc_med=float(np.median(k)),
                        n_px=int(g[g.rol == "h"].n_px.iloc[0])))
    return pd.DataFrame(out)


def resumen(t):
    return {"n_cuadros": int(len(t)), "F_h": float((t.p_h >= U).mean()), "F_c": float(t.fc.mean()),
            "AUC": float(t.auc.mean()), "P_med_huella": float(t.p_h.median()), "P_med_ctrl": float(t.pc_med.median()),
            "P_max_huella": float(t.p_h.max())}


def ic(t, rng):
    evs = sorted(t.evento.unique())
    r = {"F_h": [], "AUC": [], "dF": []}
    for _ in range(NB):
        partes = []
        for e in rng.choice(evs, len(evs), replace=True):
            te = t[t.evento == e]
            partes.append(te.iloc[rng.integers(0, len(te), len(te))])
        b = pd.concat(partes)
        s = resumen(b)
        r["F_h"].append(s["F_h"]); r["AUC"].append(s["AUC"]); r["dF"].append(s["F_h"] - s["F_c"])
    return {k: [float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))] for k, v in r.items()}


def regla(s):
    if s["F_h"] >= 0.5 and s["F_h"] - s["F_c"] >= 0.3 and s["AUC"] >= 0.75:
        return "separa"
    if s["F_h"] < 0.2 or s["AUC"] < 0.6:
        return "no separa"
    return "no concluyente"


def main():
    d = pd.read_csv(os.path.join(RES, "chillan_objetos.csv"))
    rng = np.random.default_rng(SEM)
    res, txt = {}, []
    for banda in ("S0", "S1", "S2"):
        for col in ("P_obj", "P_obj_sd0"):
            t = por_cuadro(d[d.banda == banda], col)
            s = resumen(t)
            s["categoria"] = regla(s)
            s["IC95"] = ic(t, rng)
            s["por_evento"] = {int(e): resumen(g) for e, g in t.groupby("evento")}
            s["decide"] = banda == "S0" and col == "P_obj"
            res[f"{banda}_{col}"] = s
            txt.append(f"{banda} {col:10s} F_h {s['F_h']:.3f} F_c {s['F_c']:.3f} AUC {s['AUC']:.3f} "
                       f"IC_AUC {s['IC95']['AUC'][0]:.3f}-{s['IC95']['AUC'][1]:.3f} Pmed_h {s['P_med_huella']:.3g} "
                       f"Pmed_c {s['P_med_ctrl']:.3g} Pmax_h {s['P_max_huella']:.3g} -> {s['categoria']}"
                       + ("  [DECIDE]" if s["decide"] else ""))
    json.dump(res, open(os.path.join(RES, "chillan_metricas.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    open(os.path.join(RES, "chillan_metricas.txt"), "w", encoding="utf-8").write("\n".join(txt) + "\n")
    print("\n".join(txt))


if __name__ == "__main__":
    main()
