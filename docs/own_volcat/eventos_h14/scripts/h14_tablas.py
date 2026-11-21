"""H14: tablas derivadas para el informe, calculadas SOLO desde resultados/por_cuadro.csv (sin abrir NetCDF).

Lo de aqui es exploratorio (no estaba en el criterio): reparto de la firma total alta segun el angulo cenital
solar del objeto, y contraste huella contra anillo separando objetos pegados al crater de objetos desprendidos
(el anillo de un objeto en la cumbre cae sobre terreno mas bajo y tibio).

Uso:  python -I h14_tablas.py
"""
import sys, os, csv, json
import numpy as np

sys.stdout.reconfigure(encoding="utf-8")
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "resultados")
r = list(csv.DictReader(open(os.path.join(OUT, "por_cuadro.csv"), encoding="utf-8")))
f = lambda x: None if x in ("", None) else float(x)


def pool(rs, col="sig_fge05", n="sig_n"):
    tot = sum(f(x[n]) for x in rs)
    return {"cuadros": len(rs), "pixeles": int(tot),
            "frac_ge05": round(sum(f(x[n]) * f(x[col]) for x in rs) / tot, 4) if tot else None}


bins = [("sza<50", 0, 50), ("50<=sza<70", 50, 70), ("70<=sza<85", 70, 85), ("sza>=85", 85, 999)]
por_sza = {k: {**pool([x for x in r if lo <= f(x["sza_med"]) < hi]),
               "frac_ge05_lwir": pool([x for x in r if lo <= f(x["sza_med"]) < hi], "sigL_fge05", "sigL_n")["frac_ge05"]}
           for k, lo, hi in bins}


def contraste(rs):
    d = [f(x["dbtd_huella_menos_anillo"]) for x in rs if x["dbtd_huella_menos_anillo"]]
    b = [f(x["dbt11_huella_menos_anillo"]) for x in rs if x["dbt11_huella_menos_anillo"]]
    return {"cuadros": len(rs), "dBTD_mediana": round(float(np.median(d)), 3) if d else None,
            "dBTD_min_max": [min(d), max(d)] if d else None,
            "dBT11_mediana": round(float(np.median(b)), 3) if b else None,
            "dBT11_min_max": [min(b), max(b)] if b else None,
            "frac_btd_neg_mediana": round(float(np.median([f(x["btd_frac_neg"]) for x in rs])), 4) if rs else None}


crater = [x for x in r if f(x["dist_min_km"]) <= 10]
lejos = [x for x in r if f(x["dist_min_km"]) >= 20]
res = {"firma_total_alta_por_sza": por_sza,
       "contraste_objeto_en_crater_dist_min_le10": contraste(crater),
       "contraste_objeto_desprendido_dist_min_ge20": contraste(lejos),
       "frames_desprendidos": [x["inicio_scan"][5:16] for x in lejos],
       "tamano_objeto_px": {"mediana": float(np.median([int(x["n_px"]) for x in r])),
                            "min": min(int(x["n_px"]) for x in r), "max": max(int(x["n_px"]) for x in r)},
       "cuadros_con_pixeles_interiores": sum(1 for x in r if x["n_interior"] != "0"),
       "altura_mediana_km_rango": [min(f(x["hgt_med_km"]) for x in r if x["hgt_med_km"]),
                                   max(f(x["hgt_med_km"]) for x in r if x["hgt_med_km"])],
       "calor_lleno_en": [x["inicio_scan"] for x in r if x["calor_time_since_0MW"]],
       "rayos_distintos_de_cero": sum(1 for x in r for k in x if k.startswith("rayos") and x[k] not in ("0", ""))}
json.dump(res, open(os.path.join(OUT, "tablas_informe.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(json.dumps(res, ensure_ascii=False, indent=1))
