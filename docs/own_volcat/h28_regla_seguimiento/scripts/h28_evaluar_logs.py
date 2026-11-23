# -*- coding: utf-8 -*-
"""H28: evalua la regla de 01_REGLA_Y_CRITERIO.md (pruebas T1 a T7) sobre las tablas que
sacan h28_parse_logs.py y h28_match_volcan.py, y corre el control de integridad contra el
log crudo (conteo de lineas por busqueda de texto, independiente del lector).

Uso:
  python -I h28_evaluar_logs.py <carpeta_tablas> <etiqueta> <carpeta_logs> <cadencia_s> [hora_min hora_max]

Imprime un JSON con el resultado de cada prueba. No decide nada del dashboard.
"""
import glob
import json
import os
import re
import sys

import numpy as np
import pandas as pd


def bal_acc(y, p):
    y = np.asarray(y)
    p = np.asarray(p)
    pos, neg = y == 1, y == 0
    if pos.sum() == 0 or neg.sum() == 0:
        return None
    return float(0.5 * ((p[pos] == 1).mean() + (p[neg] == 0).mean()))


def main():
    tdir, tag, logdir, cad = sys.argv[1], sys.argv[2], sys.argv[3], float(sys.argv[4])
    files = sorted(glob.glob(os.path.join(logdir, "geocatASHOBJ.*.A?_I?_H?_S?.log")))
    if len(sys.argv) >= 7:
        pat = re.compile(r"\.(\d{6})\.A[YN]_")
        files = [f for f in files if sys.argv[5] <= pat.search(os.path.basename(f)).group(1) <= sys.argv[6]]
    out = {"caso": tag, "cuadros": len(files)}

    def rd(n):
        return pd.read_csv(os.path.join(tdir, tag + "_" + n + ".csv"))

    H, P, G = rd("historia"), rd("plumas"), rd("grupos")

    # ---- control de integridad: conteo por texto contra filas de tabla
    cnt = {"met": 0, "g2o": 0, "keep": 0, "elim": 0, "clasif": 0}
    for f in files:
        for l in open(f, errors="replace"):
            if l.startswith("Temporal selection criteria met"):
                cnt["met"] += 1
            elif "HISTORY_GROUP2OBJECT>>" in l:
                cnt["g2o"] += 1
            elif "OBJECT_GROUPING_CONTRAST_ASH" in l and " : KEEPING" in l:
                cnt["keep"] += 1
            elif "OBJECT_GROUPING_CONTRAST_ASH" in l and " : ELIMINATING" in l:
                cnt["elim"] += 1
            elif l.startswith("Group classification:"):
                cnt["clasif"] += 1
    tab = {"met": int(H.criterio_cumplido.sum()) if len(H) else 0, "g2o": len(H),
           "keep": int((P.veredicto == "KEEPING").sum()) if len(P) else 0,
           "elim": int((P.veredicto == "ELIMINATING").sum()) if len(P) else 0,
           "clasif": int(G.clasificacion.notna().sum()) if len(G) and "clasificacion" in G else 0}
    out["integridad"] = {"texto": cnt, "tabla": tab, "igual": cnt == tab}

    if len(H):
        h = H.dropna(subset=["Time diff(s)", "Dist Thresh(km)"]).copy()
        out["filas_historia_sin_linea_hist"] = int(len(H) - len(h))
        # ---- T1 ley de distancia
        d1 = (h["Dist Thresh(km)"] - 0.05 * h["Time diff(s)"]).abs()
        ok1 = d1 <= 0.08
        hr = h.dropna(subset=["Refined Dist Threshold(km)"])
        d2 = (hr["Refined Dist Threshold(km)"] - hr["Time diff(s)"] / 60.0).abs()
        ok2 = d2 <= 0.02
        out["T1"] = {"filas": len(h), "frac_ok_umbral": float(ok1.mean()), "max_dif_km": float(d1.max()),
                     "filas_refinado": len(hr), "frac_ok_refinado": float(ok2.mean()) if len(hr) else None,
                     "max_dif_ref_km": float(d2.max()) if len(hr) else None,
                     "time_diff_valores": {str(k): int(v) for k, v in h["Time diff(s)"].round(-1).value_counts().head(8).items()},
                     "umbral_valores": {str(k): int(v) for k, v in h["Dist Thresh(km)"].value_counts().head(8).items()},
                     "cumple": bool(ok1.mean() >= 0.99 and (len(hr) == 0 or ok2.mean() >= 0.99))}
        # ---- T2 rama por distancia
        h["rama"] = h["rama"].astype(str)
        sel = h["rama"].isin(["1", "3"])
        lejos_pred = (h["Dist(km)"] > h["Dist Thresh(km)"]) & ~(h["Kd Group"] > 0)
        es3 = h["rama"] == "3"
        ok = (lejos_pred == es3)[sel]
        out["T2"] = {"filas": int(sel.sum()), "frac_ok": float(ok.mean()) if len(ok) else None,
                     "rama3": int(es3.sum()), "rama1": int((h["rama"] == "1").sum()),
                     "otras_ramas": {str(k): int(v) for k, v in h["rama"].value_counts().items() if k not in ("1", "3")},
                     "rama3_con_criterio": int(h[es3].criterio_cumplido.sum()),
                     "cumple": bool(len(ok) and ok.mean() >= 0.99 and h[es3].criterio_cumplido.sum() == 0)}
        # ---- T3 parecido minimo
        r = h[(h["rama"] == "1") & (h["Selection Opt"] == 0)].copy()
        r["pred"] = ((r["Overlap Frac"] > 0) | (r["Emiss Sim"] > 0)).astype(int)
        t3 = {"filas": len(r), "cumplen": int(r.criterio_cumplido.sum()),
              "no_cumplen": int((r.criterio_cumplido == 0).sum())}
        for fase, sub in r.groupby("fase"):
            t3["fase_" + str(fase)] = {"filas": len(sub), "cumplen": int(sub.criterio_cumplido.sum()),
                                       "aciertos": int((sub.pred == sub.criterio_cumplido).sum()),
                                       "exactitud_balanceada": bal_acc(sub.criterio_cumplido, sub.pred)}
        ba = bal_acc(r.criterio_cumplido, r.pred)
        t3["exactitud_balanceada"] = ba
        t3["confusion"] = {"cumple_pred1": int(((r.criterio_cumplido == 1) & (r.pred == 1)).sum()),
                           "cumple_pred0": int(((r.criterio_cumplido == 1) & (r.pred == 0)).sum()),
                           "nocumple_pred1": int(((r.criterio_cumplido == 0) & (r.pred == 1)).sum()),
                           "nocumple_pred0": int(((r.criterio_cumplido == 0) & (r.pred == 0)).sum())}
        poder = t3["cumplen"] >= 5 and t3["no_cumplen"] >= 5
        t3["con_poder"] = bool(poder)
        rng = np.random.default_rng(28)
        plc = []
        grupos = [g.index.values for _, g in r.groupby("hora")]
        yv = r.criterio_cumplido.copy()
        for _ in range(1000):
            y = yv.copy()
            for idx in grupos:
                y.loc[idx] = rng.permutation(yv.loc[idx].values)
            b = bal_acc(y, r.pred)
            if b is not None:
                plc.append(b)
        t3["placebo_mediana"] = float(np.median(plc)) if plc else None
        t3["placebo_p95"] = float(np.percentile(plc, 95)) if plc else None
        t3["cumple"] = (bool(ba is not None and ba >= 0.90) if poder else "sin poder")
        out["T3"] = t3
        # ---- T6 solo el cuadro anterior
        okc = h["Time diff(s)"].between(0.9 * cad, 1.1 * cad)
        out["T6"] = {"filas": len(h), "frac_ok": float(okc.mean()), "min": float(h["Time diff(s)"].min()),
                     "max": float(h["Time diff(s)"].max()), "cumple": bool(okc.mean() >= 0.99)}
    else:
        for k in ("T1", "T2", "T3", "T6"):
            out[k] = {"filas": 0, "cumple": "sin dato"}

    # ---- T4 plumas
    pl = P[P.tipo == "plume"] if len(P) else P
    if len(pl):
        keep = pl[pl.veredicto == "KEEPING"]
        elim = pl[pl.veredicto == "ELIMINATING"]
        t4 = {"plumas": len(pl), "keeping": len(keep), "eliminating": len(elim),
              "sin_veredicto": int((~pl.veredicto.isin(["KEEPING", "ELIMINATING"])).sum()),
              "keeping_con_contraste_ok": int((keep.contraste_sin_dist == "PASSED").sum()),
              "eliminating_con_contraste_ok": int((elim.contraste_sin_dist == "PASSED").sum())}
        t4["T4a_cumple"] = ("sin dato" if len(keep) == 0 else bool((keep.contraste_sin_dist == "PASSED").all()))
        pix = pl.obj_pix_total if "obj_pix_total" in pl else pd.Series(np.nan, index=pl.index)
        pred = ((pl.contraste_sin_dist == "PASSED") & (pix >= 8)).astype(int)
        y = (pl.veredicto == "KEEPING").astype(int)
        t4["T4b_aciertos"] = int((pred == y).sum())
        t4["T4b_exactitud_balanceada"] = bal_acc(y, pred)
        cols = [c for c in ["hora", "veredicto", "vol_idx", "bulk", "contraste_sin_dist", "contraste_con_dist",
                            "ruido_nube", "obj_pix_total", "Time Trend Count", "Robust Time Trend Count",
                            "New Emission Count", "BTD Bullseye Count", "Dynamic Corr Count",
                            "Spatial/Spectral Corr Count", "Min Plume Distance", "msgs"] if c in pl.columns]
        t4["detalle"] = json.loads(pl[cols].to_json(orient="records"))
        out["T4"] = t4
    else:
        out["T4"] = {"plumas": 0, "T4a_cumple": "sin dato"}

    # ---- T5 clasificacion
    if len(G) and "clasificacion" in G:
        g = G.dropna(subset=["clasificacion"]).copy()
        out["clasificados_por_tipo"] = {str(k): int(v) for k, v in g.tipo.value_counts().items()}
        g = g[g.tipo == "ash"]
        hist_na = g["History Index"].isna()
        kd = g["cl K-d Overlap Count"].fillna(0)
        viejo = g.clasificacion.str.startswith("Old")
        nuevo = g.clasificacion.str.startswith("New")
        mal = int(((kd > 0) & ~viejo).sum())
        out["T5"] = {"grupos": len(g), "old": int(viejo.sum()), "new": int(nuevo.sum()),
                     "con_kd": int((kd > 0).sum()), "new_con_kd": int((nuevo & (kd > 0)).sum()), "contradicen": mal,
                     "posthoc_new_sii_sin_historia": int((nuevo == hist_na).sum()),
                     "detalle": json.loads(g[[c for c in ["hora", "clasificacion", "History Index", "Time Diff(s)", "pix", "en_rasgo_previo_n", "cl Time Trend Count", "cl K-d Overlap Count"] if c in g.columns]].to_json(orient="records")),
                     "otras_clases": {str(k): int(v) for k, v in g.clasificacion[~viejo & ~nuevo].value_counts().items()},
                     "cumple": ("sin dato" if len(g) == 0 else bool(mal == 0))}
    else:
        out["T5"] = {"grupos": 0, "cumple": "sin dato"}

    # ---- T7 anclaje (exploratoria)
    mp = os.path.join(tdir, tag + "_match.csv")
    if os.path.exists(mp):
        M = pd.read_csv(mp)
        w = M[(M.seccion == "weak") & M.v1.notna() & M.match.notna()]
        if len(w):
            pred = ((w.v1 > 1 / 3) & (w.v2 > 1 / 3)).astype(int)
            out["T7"] = {"filas": len(w), "match": int(w.match.sum()), "aciertos": int((pred == w.match).sum()),
                         "exactitud_balanceada": bal_acc(w.match.astype(int), pred)}
        s = M[(M.seccion == "strong")]
        out["plumas_fuertes"] = {"match": int((s.match == 1).sum()), "no_match": int((s.match == 0).sum()),
                                 "eliminadas_por_falta_de_actividad": int(s.volcan.astype(str).str.contains("falta de actividad").sum())}
    print(json.dumps(out, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
