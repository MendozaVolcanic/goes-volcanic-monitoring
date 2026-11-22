"""H19: validacion de las reglas congeladas (regla_congelada.md) en el bloque 20:31 a 23:31, con placebos,
regla nula y tramos de emisividad. Uso: python h19_validar.py NPZ_DIR SALIDA_JSON --validacion
Con --eleccion corre lo mismo en el bloque de eleccion (para comparar)."""
import sys
import os
import json
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from h19_comun import cargar, f, PIX, HORAS, ELECCION, VALIDACION, SIN_EVENTO, guardia
import h19_reglas as R

npz, salida = sys.argv[1], sys.argv[2]
BLOQUE = ELECCION if "--eleccion" in sys.argv else VALIDACION
guardia(BLOQUE)
rng = np.random.default_rng(19)
EPS_TRAMOS = [(-1, 0.3), (0.3, 0.5), (0.5, 0.8), (0.8, 0.9), (0.9, 1.01)]


def a_img(d, mask):
    g = np.zeros((601, 601), bool)
    g[d["iy"][mask], d["ix"][mask]] = True
    return g


def campo_img(d, v):
    g = np.full((601, 601), np.nan)
    g[d["iy"], d["ix"]] = v
    return g


def pr(tp, npred, npos):
    return {"TP": int(tp), "predichos": int(npred), "positivos": int(npos),
            "sens": float(tp / npos) if npos else None, "prec": float(tp / npred) if npred else None}


def f1(tp, npred, npos):
    return 2 * tp / (npred + npos) if (npred + npos) else 0.0


out = {"bloque": BLOQUE, "cuadros": {}}
ac = {k: np.zeros(3) for k in ("C_principal", "C_secundaria", "nula_SW_IR", "nula_IR", "identidad_subset",
                                "placebo_C_cuadro_anterior", "cadena_completa", "cadena_objeto_verdadero")}
B = np.zeros(2); Bp = np.zeros(2)
inst = np.zeros(4)
tramos = {str(t): np.zeros(3) for t in EPS_TRAMOS}
Dn = np.zeros(3); Dn_p = np.zeros(3); Dc = np.zeros(3); Dc_w = np.zeros(3); Dch = np.zeros(3); Dch_w = np.zeros(3)
perm_f1 = np.zeros(1000); perm_tp = np.zeros(1000); perm_np = np.zeros(1000)
cuadros_ok = {k: [] for k in ac}
jac = {}
objs = []
cache = {}


def carga(h):
    if h not in cache:
        cache[h] = cargar(npz, h)
    return cache[h]


for h in BLOQUE:
    d = carga(h)
    i = HORAS.index(h)
    dp = carga(HORAS[i - 1])
    d4 = carga(HORAS[i - 4])
    P = f(d, PIX + "ash_probability"); S = f(d, PIX + "ash_probability_subset")
    IR = f(d, PIX + "ash_probability_IR"); SW = f(d, PIX + "ash_probability_SW_IR")
    eps = f(d, PIX + "cloud_emissivity_ch14_tot"); r2 = f(d, "p__channel_2_reflectance")
    bop = f(d, PIX + "cloud_beta_1112_opaque")
    ag = d["p__Ash_Group_Id_2d"] > 0; ig = d["p__Ice_Group_Id_2d"] > 0
    V = np.isfinite(P); Vs = np.isfinite(S)
    dt = V & (f(d, "p__pixel_solar_zenith_angle") < 85) & (d["p__pixel_surface_type"] != 0)
    alto = dt & (P >= .5)
    c = {"V": int(V.sum()), "ag": int(ag.sum()), "ig": int(ig.sum()), "dia_tierra": int(dt.sum()), "altos": int(alto.sum())}
    # instrumento
    inst += [dt.sum(), alto.sum(), (alto & (SW >= .5)).sum(), (alto & (IR >= .5)).sum()]
    # A
    u = (V | ag | ig).sum()
    c["jaccard_V_grupos"] = float((V & (ag | ig)).sum() / u) if u else None
    c["jaccard_Vsubset_V"] = float((V & Vs).sum() / (V | Vs).sum()) if (V | Vs).sum() else None
    # B
    osc = R.oscuro_opaco(eps, r2)
    B += [Vs.sum(), (np.abs(osc.astype(float) - S)[Vs] <= 0.01).sum()]
    epsp = campo_img(dp, f(dp, PIX + "cloud_emissivity_ch14_tot"))[d["iy"], d["ix"]]
    r2p = campo_img(dp, f(dp, "p__channel_2_reflectance"))[d["iy"], d["ix"]]
    oscp = R.oscuro_opaco(epsp, r2p)
    Bp += [Vs.sum(), (np.abs(oscp.astype(float) - S)[Vs] <= 0.01).sum()]
    # D-nube: un paso adelante, por cada grupo del cuadro anterior
    selI = d["I__Mask"] > 0
    nI = np.bincount(d["idI"][d["idI"] >= 0], minlength=len(selI))

    def predice_nube(dprev):
        gid = dprev["p__Ice_Group_Id_2d"]
        pred = np.zeros(len(selI), bool)
        for g in np.unique(gid[gid > 0]):
            k, _ = R.elegir_vcb(d, a_img(dprev, gid == g))
            if k >= 0:
                pred[k] = True
        return pred

    predI = predice_nube(dp); predI4 = predice_nube(d4)
    Dn += [(predI & selI).sum(), predI.sum(), selI.sum()]
    Dn_p += [(predI4 & selI).sum(), predI4.sum(), selI.sum()]
    c["nube"] = {"verdaderos": np.nonzero(selI)[0].tolist(), "predichos": np.nonzero(predI)[0].tolist(),
                 "placebo_4_cuadros": np.nonzero(predI4)[0].tolist(),
                 "grupos_previos": int(len(np.unique(dp["p__Ice_Group_Id_2d"][dp["p__Ice_Group_Id_2d"] > 0]))),
                 "grupos_actuales_nube": int(len(np.unique(d["p__Ice_Group_Id_2d"][ig]))),
                 "grupos_actuales_ceniza": int(len(np.unique(d["p__Ash_Group_Id_2d"][ag])))}
    # D-ceniza
    selA = d["A__Mask"] > 0
    nA = np.bincount(d["idA"][d["idA"] >= 0], minlength=len(selA)).astype(float)
    okI = d["idI"] >= 0
    vimg_true = a_img(d, okI & np.isin(d["idI"], np.nonzero(selI)[0]))
    vimg_pred = a_img(d, okI & np.isin(d["idI"], np.nonzero(predI)[0]))
    toca = R.objetos_ceniza_que_tocan(d, vimg_true)
    toca_ch = R.objetos_ceniza_que_tocan(d, vimg_pred)
    Dc += [(toca & selA).sum(), toca.sum(), selA.sum()]
    Dc_w += [nA[toca & selA].sum(), nA[toca].sum(), nA[selA].sum()]
    Dch += [(toca_ch & selA).sum(), toca_ch.sum(), selA.sum()]
    Dch_w += [nA[toca_ch & selA].sum(), nA[toca_ch].sum(), nA[selA].sum()]
    for j in range(1000):
        pm = rng.permutation(toca)
        perm_tp[j] += (pm & selA).sum(); perm_np[j] += pm.sum()
    c["ceniza"] = {"sel": int(selA.sum()), "tocan": int(toca.sum()), "TP": int((toca & selA).sum()),
                   "FP": int((toca & ~selA).sum()), "FN": int((~toca & selA).sum()),
                   "pix_FP": int(nA[toca & ~selA].sum()), "pix_FN": int(nA[~toca & selA].sum())}
    # objetos de ceniza seleccionados: emisividad mediana y fraccion de P alta
    for k in np.nonzero(selA)[0]:
        m = d["idA"] == k
        objs.append({"cuadro": h, "obj": int(k), "n": int(m.sum()), "grupo": int(d["A__Group_Id"][k]),
                     "eps_mediana": float(np.nanmedian(eps[m])), "ref2_mediana": float(np.nanmedian(r2[m])),
                     "frac_P_alta": float((P[m] >= .5).mean()), "frac_oscuro_opaco": float(osc[m].mean()),
                     "en_grupo_nube": float(ig[m].mean()), "toca": bool(toca[k]),
                     "Feature_Prob": float(d["A__Feature_Prob"][k]), "lat": float(d["A__Latitude_Radiative_Center"][k]),
                     "lon": float(d["A__Longitude_Radiative_Center"][k])})
    # C y variantes
    en_obj_pred = (d["idA"] >= 0) & toca_ch[np.clip(d["idA"], 0, None)]
    en_obj_true = (d["idA"] >= 0) & toca[np.clip(d["idA"], 0, None)]
    preds = {"C_principal": osc & dt, "C_secundaria": osc & (bop > 1.0) & dt, "nula_SW_IR": (SW >= .5) & dt,
             "nula_IR": (IR >= .5) & dt, "identidad_subset": (S >= .5) & dt, "placebo_C_cuadro_anterior": oscp & dt,
             "cadena_completa": osc & en_obj_pred, "cadena_objeto_verdadero": osc & en_obj_true}
    dt_all = (f(d, "p__pixel_solar_zenith_angle") < 85) & (d["p__pixel_surface_type"] != 0)
    for k, p_ in preds.items():
        if k.startswith("cadena"):
            p_ = p_ & dt_all
        ac[k] += [(p_ & alto).sum(), p_.sum(), alto.sum()]
        if alto.sum() >= 20:
            cuadros_ok[k].append((h, float((p_ & alto).sum() / alto.sum()), float((p_ & alto).sum() / max(p_.sum(), 1))))
    c["C_principal"] = pr((preds["C_principal"] & alto).sum(), preds["C_principal"].sum(), alto.sum())
    for t in EPS_TRAMOS:
        m = alto & (eps >= t[0]) & (eps < t[1])
        tramos[str(t)] += [m.sum(), (m & preds["C_principal"]).sum(), (dt & (eps >= t[0]) & (eps < t[1])).sum()]
    out["cuadros"][h] = c

out["instrumento"] = {"dia_tierra_con_P": int(inst[0]), "altos": int(inst[1]), "altos_con_SW_IR_alta": int(inst[2]),
                      "altos_con_IR_alta": int(inst[3])}
out["A_jaccard_min"] = min(c["jaccard_V_grupos"] for c in out["cuadros"].values() if c["jaccard_V_grupos"] is not None)
out["A_cuadros_bajo_0.99"] = [h for h, c in out["cuadros"].items() if c["jaccard_V_grupos"] is not None and c["jaccard_V_grupos"] < 0.99]
out["B"] = {"n": int(B[0]), "frac_dentro_0.01": float(B[1] / B[0]), "placebo_frac": float(Bp[1] / Bp[0])}
out["C"] = {}
for k, a in ac.items():
    r = pr(*a)
    r["cuadros_con_20_altos"] = len(cuadros_ok[k])
    r["cuadros_ambas_ge_0.8"] = sum(1 for _, s, p in cuadros_ok[k] if s >= .8 and p >= .8)
    r["por_cuadro"] = cuadros_ok[k]
    out["C"][k] = r
out["tramos_eps"] = {k: {"altos": int(v[0]), "recuperados": int(v[1]), "pixeles_dia_tierra": int(v[2]),
                         "sens": float(v[1] / v[0]) if v[0] else None} for k, v in tramos.items()}
out["D_nube"] = {"un_paso": pr(*Dn), "placebo_4_cuadros": pr(*Dn_p)}
pf = np.array([f1(perm_tp[j], perm_np[j], Dc[2]) for j in range(1000)])
out["D_ceniza"] = {"objeto_verdadero": pr(*Dc), "objeto_verdadero_por_pixeles": pr(*Dc_w),
                   "encadenada": pr(*Dch), "encadenada_por_pixeles": pr(*Dch_w),
                   "F1": f1(*Dc), "placebo_F1_mediana": float(np.median(pf)), "placebo_F1_max": float(pf.max())}
out["objetos_ceniza_seleccionados"] = objs
# cuadros sin evento: que selecciona la regla y que selecciona VOLCAT
se = {}
for h in SIN_EVENTO:
    d = carga(h)
    i = HORAS.index(h)
    npred = 0
    if i > 0:
        dp = carga(HORAS[i - 1])
        gid = dp["p__Ice_Group_Id_2d"]
        for g in np.unique(gid[gid > 0]):
            k, _ = R.elegir_vcb(d, a_img(dp, gid == g))
            npred += int(k >= 0)
    se[h] = {"regla_nube": npred, "volcat_nube": int((d["I__Mask"] > 0).sum()), "volcat_ceniza": int((d["A__Mask"] > 0).sum())}
out["sin_evento"] = se
json.dump(out, open(salida, "w"), indent=1)

print("INSTRUMENTO:", out["instrumento"])
print("A: Jaccard minimo %.4f ; cuadros bajo 0.99: %s" % (out["A_jaccard_min"], out["A_cuadros_bajo_0.99"]))
print("B: n=%d frac |dif|<=0.01 = %.4f ; placebo (cuadro anterior) %.4f" % (out["B"]["n"], out["B"]["frac_dentro_0.01"], out["B"]["placebo_frac"]))
for k, r in out["C"].items():
    print("C %-28s TP %5d pred %5d altos %5d sens %s prec %s ; cuadros ok %d de %d" % (
        k, r["TP"], r["predichos"], r["positivos"], "%.4f" % r["sens"] if r["sens"] is not None else "NA",
        "%.4f" % r["prec"] if r["prec"] is not None else "NA", r["cuadros_ambas_ge_0.8"], r["cuadros_con_20_altos"]))
print("   por cuadro (principal):", [(h, round(s, 3), round(p, 3)) for h, s, p in out["C"]["C_principal"]["por_cuadro"]])
print("TRAMOS eps:", out["tramos_eps"])
print("D-nube:", out["D_nube"])
print("D-ceniza:", {k: v for k, v in out["D_ceniza"].items()})
for h, c in out["cuadros"].items():
    print("  ", h, "V %d ag %d ig %d jac %.4f | nube %s | ceniza %s" % (c["V"], c["ag"], c["ig"], c["jaccard_V_grupos"] or -1, c["nube"], c["ceniza"]))
print("SIN EVENTO:", se)
print("OBJETOS de ceniza seleccionados con eps mediana < 0.8:")
for o in objs:
    if o["eps_mediana"] < 0.8:
        print("  ", o)
