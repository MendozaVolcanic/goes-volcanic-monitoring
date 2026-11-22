"""H19, analisis POST HOC (despues de abrir validacion; no decide el veredicto).
(1) metricas de las reglas congeladas separando la fase con nube convectiva (hasta 22:01) y la fase sin ella
    (22:16 a 23:31); (2) en la fase sin nube convectiva: que predice la seleccion de objetos de ceniza
    (solape con el grupo de ceniza anterior) y de donde sale la P alta; (3) evento de San Cristobal 23:31.
Uso: python h19_posthoc.py NPZ_DIR SALIDA_JSON --validacion"""
import sys
import os
import json
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from h19_comun import cargar, f, PIX, TRK, HORAS, VALIDACION, guardia
import h19_reglas as R

npz, salida = sys.argv[1], sys.argv[2]
guardia(VALIDACION)
F1 = VALIDACION[:7]      # 20:31 a 22:01
F2 = VALIDACION[7:]      # 22:16 a 23:31
out = {}


def q(x):
    x = np.asarray(x, float)
    x = x[np.isfinite(x)]
    return [round(float(v), 4) for v in np.percentile(x, [0, 25, 50, 75, 100])] if len(x) else []


for nom, bloque in (("fase_con_nube_convectiva", F1), ("fase_sin_nube_convectiva", F2)):
    C = np.zeros(3); S_ = np.zeros(3); H = np.zeros(3); H4 = np.zeros(3); Hw = np.zeros(3); K = np.zeros(3)
    tipos = {}
    alt = {"n": 0, "P_igual_subset": 0, "P_igual_IR": 0, "oscuro_opaco": 0, "IR_alta": 0, "eps": [], "ref2": [], "btd": [], "aom": {}}
    selobj = {"n": 0, "eps_med": [], "tam": [], "Feature_Prob": [], "Time_Trend_Count": [], "frac_aom": {}}
    for h in bloque:
        d = cargar(npz, h)
        i = HORAS.index(h)
        dp = cargar(npz, HORAS[i - 1]); d4 = cargar(npz, HORAS[i - 4])
        P = f(d, PIX + "ash_probability"); S = f(d, PIX + "ash_probability_subset"); IR = f(d, PIX + "ash_probability_IR")
        eps = f(d, PIX + "cloud_emissivity_ch14_tot"); r2 = f(d, "p__channel_2_reflectance")
        btd = f(d, "p__channel_14_brightness_temperature") - f(d, "p__channel_15_brightness_temperature")
        aom = d[PIX + "Ash_Object_Mask"]
        dt = np.isfinite(P) & (f(d, "p__pixel_solar_zenith_angle") < 85) & (d["p__pixel_surface_type"] != 0)
        alto = dt & (P >= .5)
        osc = R.oscuro_opaco(eps, r2)
        C += [(osc & alto).sum(), (osc & dt).sum(), alto.sum()]
        S_ += [((S >= .5) & alto).sum(), ((S >= .5) & dt).sum(), alto.sum()]
        alt["n"] += int(alto.sum()); alt["P_igual_subset"] += int((np.abs(P - S)[alto] <= 0.01).sum())
        alt["P_igual_IR"] += int((np.abs(P - IR)[alto] <= 0.01).sum()); alt["oscuro_opaco"] += int((osc & alto).sum())
        alt["IR_alta"] += int((alto & (IR >= .5)).sum())
        na = alto & ~osc
        alt["eps"] += eps[na].tolist(); alt["ref2"] += r2[na].tolist(); alt["btd"] += btd[na].tolist()
        for c_, n_ in zip(*np.unique(aom[na], return_counts=True)):
            alt["aom"][int(c_)] = alt["aom"].get(int(c_), 0) + int(n_)
        # seleccion de objetos de ceniza por historia: algun pixel sobre el grupo de ceniza del cuadro anterior
        selA = d["A__Mask"] > 0
        n = len(selA)
        ido = d["idA"]; ok = ido >= 0
        nA = np.bincount(ido[ok], minlength=n).astype(float)

        def solapa(dprev):
            g = np.zeros((601, 601), bool)
            m = (dprev["p__Ash_Group_Id_2d"] > 0) | (dprev["p__Ice_Group_Id_2d"] > 0)
            g[dprev["iy"][m], dprev["ix"][m]] = True
            return np.bincount(ido[ok], weights=g[d["iy"], d["ix"]][ok].astype(float), minlength=n) > 0

        hp = solapa(dp); hp4 = solapa(d4)
        H += [(hp & selA).sum(), hp.sum(), selA.sum()]; H4 += [(hp4 & selA).sum(), hp4.sum(), selA.sum()]
        Hw += [nA[hp & selA].sum(), nA[hp].sum(), nA[selA].sum()]
        # seguimiento k-d de VOLCAT: todos los pixeles del objeto con vecinos previos dentro de ceniza
        cia = np.nan_to_num(f(d, TRK + "count_in_ash"), nan=0) > 0
        kd = (np.bincount(ido[ok], weights=cia[ok].astype(float), minlength=n) / np.maximum(nA, 1)) >= 0.5
        K += [(kd & selA).sum(), kd.sum(), selA.sum()]
        selobj["n"] += int(selA.sum())
        for k in np.nonzero(selA)[0]:
            m = ido == k
            selobj["eps_med"].append(float(np.nanmedian(eps[m]))); selobj["tam"].append(int(m.sum()))
            selobj["Feature_Prob"].append(float(d["A__Feature_Prob"][k])); selobj["Time_Trend_Count"].append(float(d["A__Time_Trend_Count"][k]))
            c_ = int(np.bincount(aom[m].astype(int)).argmax())
            selobj["frac_aom"][c_] = selobj["frac_aom"].get(c_, 0) + 1

    def pr(a):
        return {"TP": int(a[0]), "predichos": int(a[1]), "positivos": int(a[2]),
                "sens": round(float(a[0] / a[2]), 4) if a[2] else None, "prec": round(float(a[0] / a[1]), 4) if a[1] else None}

    out[nom] = {"cuadros": bloque, "C_principal": pr(C), "identidad_subset": pr(S_),
                "altos": {k: (q(v) if isinstance(v, list) else v) for k, v in alt.items()},
                "objetos_ceniza_sel": {"n": selobj["n"], "eps_mediana_cuantiles": q(selobj["eps_med"]), "tam_cuantiles": q(selobj["tam"]),
                                       "Feature_Prob_cuantiles": [float("%.3g" % v) for v in np.percentile(selobj["Feature_Prob"], [0, 50, 90, 100])] if selobj["n"] else [],
                                       "codigo_Ash_Object_Mask_dominante": selobj["frac_aom"]},
                "historia_solape_grupo_anterior": pr(H), "historia_por_pixeles": pr(Hw), "placebo_4_cuadros": pr(H4),
                "seguimiento_kd_count_in_ash": pr(K)}

# San Cristobal 23:31 (lat 12.70, lon -87.00)
d = cargar(npz, "233100")
lat = f(d, "p__pixel_latitude"); lon = f(d, "p__pixel_longitude")
P = f(d, PIX + "ash_probability")
m = np.isfinite(P) & (np.abs(lat - 12.70) < 0.4) & (np.abs(lon + 87.0) < 0.4)
sc = {"pixeles_con_P": int(m.sum())}
if m.sum():
    eps = f(d, PIX + "cloud_emissivity_ch14_tot")
    btd = f(d, "p__channel_14_brightness_temperature") - f(d, "p__channel_15_brightness_temperature")
    sc.update({"P": q(P[m]), "subset": q(f(d, PIX + "ash_probability_subset")[m]), "IR": q(f(d, PIX + "ash_probability_IR")[m]),
               "SW_IR": q(f(d, PIX + "ash_probability_SW_IR")[m]), "eps_tot": q(eps[m]), "ref2": q(f(d, "p__channel_2_reflectance")[m]),
               "btd_11_12": q(btd[m]), "solzen": q(f(d, "p__pixel_solar_zenith_angle")[m]),
               "P_alta": int((P[m] >= .5).sum()), "IR_alta": int((f(d, PIX + "ash_probability_IR")[m] >= .5).sum()),
               "P_igual_IR": int((np.abs(P - f(d, PIX + "ash_probability_IR"))[m] <= 0.01).sum()),
               "P_igual_subset": int((np.abs(P - f(d, PIX + "ash_probability_subset"))[m] <= 0.01).sum()),
               "codigos_Ash_Object_Mask": {int(a): int(b) for a, b in zip(*np.unique(d[PIX + "Ash_Object_Mask"][m], return_counts=True))},
               "hot_cerca": int((d["idH"][(np.abs(lat - 12.70) < 0.4) & (np.abs(lon + 87.0) < 0.4)] >= 0).sum())})
    ks = np.unique(d["idA"][m]); ks = ks[ks >= 0]
    sc["objetos"] = []
    for k in ks:
        o = {"obj": int(k), "n": int((d["idA"] == k).sum())}
        for c_ in ("Feature_Prob", "Feature_Prob_IR", "Probability_Median", "Probability_Subset_Median", "Emiss14_Tot_Median",
                   "Time_Trend_Count", "New_Emission_Count", "Btd_Bullseye_Count", "Robust_Count_L1", "Robust_Count_L4",
                   "Group_Id", "Mask", "Cmask", "Max_Height", "Total_Area", "Btd1112_Mean", "Dark_Pixel_Count"):
            if "A__" + c_ in d:
                o[c_] = float(d["A__" + c_][k])
        sc["objetos"].append(o)
out["san_cristobal_233100"] = sc
json.dump(out, open(salida, "w"), indent=1)
print(json.dumps(out, indent=1))
