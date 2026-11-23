# -*- coding: utf-8 -*-
"""H28: analisis POSTERIORES a la prueba (no deciden el veredicto; estan aqui para que se
puedan repetir).

  1. T1 y T2 por PAR objeto / grupo historico (arreglo del emparejamiento del lector),
     con control de integridad (lineas "Hist Idx" contadas por texto contra pares).
  2. Fraccion de objetos de ceniza dentro del alcance que cumplen el criterio temporal.
  3. Los dos subcriterios "(1)" y "(2)" de "Temporal selection criteria met".
  4. Chillan: atraso de produccion de cada archivo (hora de creacion menos hora de la
     imagen) contra los huecos de la cadena, y saltos de la cadena del 14-11 12:40.

Lee las tablas de pares de <carpeta_tablas> (fuera del repositorio, en
D:/goes_notas/s19/h28/tablas/). Escribe solo conteos y la tabla de atrasos (hora de imagen y
minutos de atraso), que son propios y si se commitean.

Uso:
  python -I h28_posthoc.py <carpeta_tablas> <carpeta_eventos_chillan> <salida.json> \
         <logs_kirishima> <logs_fuego> <logs_mauna_loa>
"""
import glob
import json
import os
import re
import sys

import pandas as pd


def cuenta_hist(logdir, lo=None, hi=None):
    pat = re.compile(r"\.(\d{6})\.A[YN]_")
    n = 0
    for f in sorted(glob.glob(os.path.join(logdir, "geocatASHOBJ.*.A?_I?_H?_S?.log"))):
        h = pat.search(os.path.basename(f)).group(1)
        if lo and not (lo <= h <= hi):
            continue
        for l in open(f, errors="replace"):
            if l.startswith("Hist Idx:"):
                n += 1
    return n


def main():
    T, evdir, salida = sys.argv[1], sys.argv[2], sys.argv[3]
    logs = {"kirishima": (sys.argv[4], None, None), "fuego_ajuste": (sys.argv[5], "140000", "185959"),
            "fuego_prueba": (sys.argv[5], "190000", "235959"), "mauna_loa": (sys.argv[6], None, None)}
    out = {"pares": {}, "ceniza_en_alcance": {}, "subcriterios": {}}
    todos = []
    for caso, (ld, lo, hi) in logs.items():
        p = pd.read_csv(os.path.join(T, caso + "_pares.csv"))
        p["rama"] = p.rama.fillna(-1).astype(int)
        d1 = (p.umbral_km - 0.05 * p.dt_s).abs()
        pr = p.dropna(subset=["umbral_ref_km"])
        d2 = (pr.umbral_ref_km - pr.dt_s / 60).abs()
        q = p[p.rama > 0]
        lejos = (q.dist_km > q.umbral_km) & ~(q.kd_group > 0)
        out["pares"][caso] = {"pares": len(p), "lineas_hist_idx_por_texto": cuenta_hist(ld, lo, hi),
                              "T1_umbral_ok": int((d1 <= 0.08).sum()), "T1_refinado_n": len(pr),
                              "T1_refinado_ok": int((d2 <= 0.02).sum()),
                              "dt_min_s": float(p.dt_s.min()), "dt_max_s": float(p.dt_s.max()),
                              "umbral_min_km": float(p.umbral_km.min()), "umbral_max_km": float(p.umbral_km.max()),
                              "pares_con_rama": len(q), "pares_sin_rama": int((p.rama < 0).sum()),
                              "T2_ok": int((lejos == (q.rama == 3)).sum()),
                              "rama3_que_cumple": int(q[q.rama == 3].cumple.sum()),
                              "rama1_lejos_sin_enlace": int(((q.rama == 1) & lejos).sum())}
        # objetos (no pares): un objeto cumple si cumple en alguno de sus pares
        p["key"] = p.hora.astype(str) + "_" + p.fase + "_" + p.obj.astype(str)
        o = p.groupby("key").agg(fase=("fase", "first"), sel=("sel_opt", "first"), cumple=("cumple", "max"),
                                 r1=("rama", lambda s: int((s == 1).sum())), ov=("overlap", "max"),
                                 em=("emiss_sim", "max")).reset_index()
        a = o[(o.sel == 0) & (o.r1 > 0)]
        for fase, sub in a.groupby("fase"):
            out["ceniza_en_alcance"][caso + "_" + fase] = {
                "objetos_en_rama_1": len(sub), "cumplen": int(sub.cumple.sum()),
                "cumplen_sin_solape_ni_emisividad": int(((sub.cumple == 1) & ~((sub.ov > 0) | (sub.em > 0))).sum()),
                "no_cumplen_con_solape_o_emisividad": int(((sub.cumple == 0) & ((sub.ov > 0) | (sub.em > 0))).sum())}
        todos.append(p)
    P = pd.concat(todos, ignore_index=True)
    m = P[P.cumple == 1].copy()
    m["n"] = m.cumple_txt.str.extract(r"\((\d+)\)")[0]
    m["tipo"] = m.cumple_txt.str.extract(r"for (\w+)")[0]
    m["solapa"] = m.overlap > 0
    for (tipo, n, sol), sub in m.groupby(["tipo", "n", "solapa"]):
        out["subcriterios"]["%s (%s) %s" % (tipo, n, "con solape" if sol else "sin solape")] = len(sub)

    # ---- Chillan: atraso de produccion y huecos
    rows = []
    for f in sorted(glob.glob(os.path.join(evdir, "VOLCAT-FD-vid357070_*.nc"))):
        b = os.path.basename(f)
        s = re.search(r"_s(\d{13})", b).group(1)
        c = re.search(r"_c(\d{13})", b).group(1)
        ts = pd.Timestamp("%s-%s-%s %s:%s:%s" % (s[:4], s[4:6], s[6:8], s[8:10], s[10:12], s[12:14]))
        tc = pd.Timestamp("%s-%s-%s %s:%s:%s" % (c[:4], c[4:6], c[6:8], c[8:10], c[10:12], c[12:14]))
        rows.append({"imagen": ts, "atraso_min": round((tc - ts).total_seconds() / 60, 1)})
    t = pd.DataFrame(rows)
    sig = (t.imagen.shift(-1) - t.imagen).dt.total_seconds()
    t["hueco_despues"] = sig == 1200
    t["fin_de_cadena"] = ~(sig <= 1200)
    t.assign(imagen=t.imagen.dt.strftime("%d-%m %H:%M")).to_csv(os.path.join(os.path.dirname(salida), "chillan_atraso.csv"), index=False)
    resto = t[~t.hueco_despues]
    out["chillan_atraso"] = {"cuadros_seguidos_de_hueco": int(t.hueco_despues.sum()),
                             "atraso_de_esos_min": t[t.hueco_despues].atraso_min.tolist(),
                             "atraso_max_del_resto_min": float(resto.atraso_min.max()),
                             "atraso_mediana_del_resto_min": float(resto.atraso_min.median()),
                             "resto_con_atraso_ge_30": int((resto.atraso_min >= 30).sum()), "resto_n": len(resto)}
    json.dump(out, open(salida, "w"), indent=1, ensure_ascii=False)
    print(json.dumps(out, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
