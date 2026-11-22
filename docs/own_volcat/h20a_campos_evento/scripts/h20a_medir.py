"""H20a: mide los candidatos declarados en el criterio para los campos por pixel del archivo de evento.

Uso: python -I h20a_medir.py eleccion
     python -I h20a_medir.py validacion     (se niega si no existe regla_congelada.md)

Escribe resultados/<bloque>_medir.json (numeros resumidos) y, fuera del repo, la tabla por pixel de la
huella en D:\\goes_notas\\s17\\h20a\\pix_<bloque>.npz.
"""
import os
import sys
import json
import numpy as np
import netCDF4 as nc
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from h20a_comun import (eventos_fuego, granulos_fuego, cargar_l2, anterior, ventana, recorte, arr, hav,
                        jaccard, RES, ELECCION, VALIDACION)

sys.stdout.reconfigure(encoding="utf-8")
TOL = 0.01
DESP = [(-1, 0), (1, 0), (0, -1), (0, 1)]
FUERA = os.environ.get("H20A_FUERA", r"D:\goes_notas\s17\h20a")
PROB = {"P": "L2__PIX_ash_probability", "P_IR": "L2__PIX_ash_probability_IR",
        "P_SWIR": "L2__PIX_ash_probability_SW_IR", "P_sub": "L2__PIX_ash_probability_subset"}
OBJ_CONST = ["Probability_Median", "Probability_Subset_Median", "Probability_Mean", "Probability_Mean_IR",
             "Feature_Prob", "Feature_Prob_IR", "Feature_Prob_Loose", "Feature_Prob_IR_Loose"]
EXTRA = {"emis_tot": "DIAGS1__PIX_cloud_emissivity_ch14_tot", "ref2": "L1__channel_2_reflectance",
         "solzen": "L2__pixel_solar_zenith_angle", "mask": "DIAGS1__PIX_Ash_Object_Mask",
         "grupo": "L2__Ash_Group_Id_2d", "robusto": "DIAGS1__OBJ_Robust_Pixel_Flag",
         "hist_in": "DIAGS1__OBJ_History_Flag_Det_In", "hist_out": "DIAGS1__OBJ_History_Flag_Det_Out",
         "desplaz": "DIAG__TRK_displacement_distance", "desplaz_ash": "DIAG__TRK_displacement_distance_in_ash",
         "viento_vcb": "L2S1__VCB_cloud_wind_speed", "bt11": "L1__channel_14_brightness_temperature",
         "bt12": "L1__channel_15_brightness_temperature", "beta1112": "DIAGS1__PIX_cloud_beta_1112_tot",
         "h_l2": "L2__PROP_ash_top_height", "carga_l2": "L2__PROP_ash_mass_loading",
         "reff_l2": "L2__PROP_ash_effective_radius", "grupo_conv": "L2__Ice_Group_Id_2d",
         "satzen": "L2__pixel_satellite_zenith_angle", "P_vcb": "L2S1__VCB_ash_probability",
         "emis_prop": "L2__PROP_cloud_emissivity_ch14_tot", "bt85": "L1__channel_11_brightness_temperature",
         "bt39": "L1__channel_7_brightness_temperature", "P_IR_prev_trk": "DIAG__TRK_ash_probability_IR_prev"}


class Cuenta:
    """Acumula n y aciertos del candidato real y de sus nulos."""
    def __init__(self):
        self.d = {}

    def suma(self, clave, x, y, m):
        ok = m & np.isfinite(x) & np.isfinite(y)
        n = int(ok.sum())
        c = int((np.abs(x[ok] - y[ok]) < TOL).sum())
        a = self.d.setdefault(clave, [0, 0])
        a[0] += n
        a[1] += c

    def frac(self, clave):
        n, c = self.d.get(clave, [0, 0])
        return n, (c / n if n else float("nan"))


def obj_a_pixel(L, nombre):
    ido = L["idA"]
    v = np.asarray(L["A__" + nombre]).astype("f8")
    out = np.full(ido.shape, np.nan)
    m = ido >= 0
    out[m] = v[ido[m]]
    out[out <= -900] = np.nan
    return out


def main(bloque):
    horas = ELECCION if bloque == "eleccion" else VALIDACION
    aqui = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if bloque == "validacion" and not os.path.exists(os.path.join(aqui, "regla_congelada.md")):
        sys.exit("No abro validacion: falta regla_congelada.md")
    casos = [("fuego_vcb", h, f) for h, f in eventos_fuego("342090") if h in horas]
    if bloque == "validacion":
        casos += [("san_cristobal", h, f) for h, f in eventos_fuego("344020")]
    res = {"bloque": bloque, "tol": TOL, "casos": {}}
    pix = {}
    for caso in sorted(set(c[0] for c in casos)):
        cu = Cuenta()
        sop = {}
        tabla = {}
        porcuadro = []
        for _, h, f in [c for c in casos if c[0] == caso]:
            ds = nc.Dataset(f)
            L = cargar_l2(h)
            Lp = cargar_l2(anterior(h))
            f0, c0, dlat, dlon, n = ventana(ds, L["L2__pixel_latitude"].astype("f8"),
                                           L["L2__pixel_longitude"].astype("f8"))
            assert dlat <= 1e-4 and dlon <= 1e-4, (h, dlat, dlon)
            ny, nx = ds["latitude"].shape
            rc = lambda a, df=0, dc=0: recorte(np.asarray(a).astype("f8"), f0, c0, ny, nx, df, dc)
            idx = np.ma.filled(ds["event_idx"][:], -1).astype(int)
            hue = idx >= 0
            S = arr(ds, "ash_spectral_signature_strength")
            SL = arr(ds, "ash_spectral_signature_strength_lwir_only")
            campos = {"S": S, "SL": SL}
            fila = {"hora": h, "n_huella": int(hue.sum()), "ids_evento": sorted(set(idx[hue].tolist()))}
            for nf, F in campos.items():
                fila["%s_n_valor" % nf] = int(np.isfinite(F).sum())
                fila["%s_n_valor_fuera_huella" % nf] = int((np.isfinite(F) & ~hue).sum())
                fila["%s_n_huella_sin_valor" % nf] = int((~np.isfinite(F) & hue).sum())
                for nc_, k in PROB.items():
                    C = rc(L[k])
                    for sufijo, cand in (("", C), ("1-", 1.0 - C)):
                        cl = "%s|%s%s" % (nf, sufijo, nc_)
                        cu.suma(cl, F, cand, hue)
                        for i, (df, dc) in enumerate(DESP):
                            Cs = rc(L[k], df, dc)
                            cu.suma(cl + "|corr%d" % i, F, Cs if not sufijo else 1.0 - Cs, hue)
                        Cp = rc(Lp[k])
                        cu.suma(cl + "|previo", F, Cp if not sufijo else 1.0 - Cp, hue)
                    a = sop.setdefault("%s|%s" % (nf, nc_), [0, 0])
                    fa, fb = np.isfinite(F), np.isfinite(C)
                    a[0] += int((fa & fb).sum())
                    a[1] += int((fa | fb).sum())
                for no in OBJ_CONST:
                    cu.suma("%s|obj:%s" % (nf, no), F, rc(obj_a_pixel(L, no)), hue)
            # huella contra grupo (por construccion)
            g = rc(L["L2__Ash_Group_Id_2d"])
            gid = sorted(set(g[hue & np.isfinite(g)].astype(int).tolist()))
            fila["grupos_en_huella"] = gid
            ga = np.nan_to_num(g, nan=0) > 0
            gi = np.nan_to_num(rc(L["L2__Ice_Group_Id_2d"]), nan=0) > 0
            fila["jaccard_huella_grupo_ceniza"] = jaccard(hue, ga)
            fila["jaccard_huella_grupo_conv"] = jaccard(hue, gi)
            fila["jaccard_huella_union"] = jaccard(hue, ga | gi)
            fila["huella_en_ceniza_conv_ambos_ninguno"] = [int((hue & ga & ~gi).sum()), int((hue & gi & ~ga).sum()),
                                                           int((hue & ga & gi).sum()), int((hue & ~ga & ~gi).sum())]
            fila["grupo_fuera_huella_ceniza_conv"] = [int((ga & ~hue).sum()), int((gi & ~hue).sum())]
            # controles positivos adicionales
            for ne, kl, tol in (("ash_cloud_height", "L2__PROP_ash_top_height", 0.0051),
                                ("ash_mass_loading", "L2__PROP_ash_mass_loading", 0.001),
                                ("effective_radius_of_ash", "L2__PROP_ash_effective_radius", 0.0051)):
                x, y = arr(ds, ne), rc(L[kl])
                ok = hue & np.isfinite(x) & np.isfinite(y)
                a = sop.setdefault("ctrl|" + ne, [0, 0, 0, 0])
                a[0] += int(ok.sum())
                a[1] += int((np.abs(x[ok] - y[ok]) <= tol * np.maximum(1.0, np.abs(y[ok]) if "loading" in ne else 1.0)).sum())
                ys = rc(L[kl], 0, 1)
                oks = hue & np.isfinite(x) & np.isfinite(ys)
                a[2] += int(oks.sum())
                a[3] += int((np.abs(x[oks] - ys[oks]) <= tol * np.maximum(1.0, np.abs(ys[oks]) if "loading" in ne else 1.0)).sum())
            # tabla por pixel de la huella (fuera del repo)
            vi = ds["volcano_info"]
            vlat, vlon = float(vi.getncattr("latitude")), float(vi.getncattr("longitude"))
            la, lo = arr(ds, "latitude"), arr(ds, "longitude")
            pla, plo = arr(ds, "pc_latitude"), arr(ds, "pc_longitude")
            t = {"hora": np.full(int(hue.sum()), int(h)), "S": S[hue], "SL": SL[hue],
                 "idx": idx[hue], "iy": np.nonzero(hue)[0] + f0, "ix": np.nonzero(hue)[1] + c0,
                 "dist_trav": arr(ds, "distance_traveled")[hue], "res_time": arr(ds, "residence_time")[hue],
                 "d_nominal": hav(vlat, vlon, la, lo)[hue], "d_pc": hav(vlat, vlon, pla, plo)[hue],
                 "h_ev": arr(ds, "ash_cloud_height")[hue], "carga_ev": arr(ds, "ash_mass_loading")[hue],
                 "feature_age": np.full(int(hue.sum()), float(np.ma.filled(ds["feature_age"][:], np.nan).ravel()[0])),
                 "idA": rc(L["idA"])[hue]}
            for nc_, k in PROB.items():
                t[nc_] = rc(L[k])[hue]
                t[nc_ + "_prev"] = rc(Lp[k])[hue]
            for ne, k in EXTRA.items():
                t[ne] = rc(L[k])[hue]
            for no in OBJ_CONST:
                t["obj_" + no] = rc(obj_a_pixel(L, no))[hue]
            for k, v in t.items():
                tabla.setdefault(k, []).append(np.asarray(v, "f8"))
            fila["event_type"] = [str(q) for q in ds["event_type"][:]]
            fila["feature_age_min"] = [float(q) for q in np.ma.filled(ds["feature_age"][:], np.nan).ravel()]
            porcuadro.append(fila)
            ds.close()
        tabla = {k: np.concatenate(v) for k, v in tabla.items()}
        pix[caso] = tabla
        out = {"n_cuadros": len(porcuadro), "por_cuadro": porcuadro, "candidatos": {}, "soporte": {},
               "controles": {}}
        for cl in sorted(k for k in cu.d if k.count("|") == 1):
            n, fr = cu.frac(cl)
            nulo_corr = max(cu.frac(cl + "|corr%d" % i)[1] for i in range(4)) if (cl + "|corr0") in cu.d else None
            nulo_prev = cu.frac(cl + "|previo")[1] if (cl + "|previo") in cu.d else None
            out["candidatos"][cl] = {"n": n, "acuerdo": fr, "nulo_corrido_max": nulo_corr, "nulo_previo": nulo_prev}
        for k, a in sop.items():
            if k.startswith("ctrl|"):
                out["controles"][k[5:]] = {"n": a[0], "acuerdo": a[1] / a[0] if a[0] else None,
                                           "nulo_corrido_n": a[2], "nulo_corrido": a[3] / a[2] if a[2] else None}
            else:
                out["soporte"][k] = {"interseccion": a[0], "union": a[1], "jaccard": a[0] / a[1] if a[1] else None}
        res["casos"][caso] = out
        np.savez_compressed(os.path.join(FUERA, "pix_%s_%s.npz" % (bloque, caso)), **tabla)
    # archivo de granulo: S en toda la grilla 601 x 601
    cu = Cuenta()
    sop = {}
    for h, f in granulos_fuego():
        if h not in horas:
            continue
        ds = nc.Dataset(f)
        L = cargar_l2(h)
        S = arr(ds, "ash_spectral_signature_strength")
        m = np.isfinite(S)
        for nc_, k in PROB.items():
            C = L[k].astype("f8")
            cu.suma("Sg|" + nc_, S, C, m)
            a = sop.setdefault("Sg|" + nc_, [0, 0])
            a[0] += int((m & np.isfinite(C)).sum())
            a[1] += int((m | np.isfinite(C)).sum())
        g = np.nan_to_num(L["L2__Ash_Group_Id_2d"].astype("f8"), nan=0) > 0
        a = sop.setdefault("Sg|grupo_ceniza", [0, 0])
        a[0] += int((m & g).sum())
        a[1] += int((m | g).sum())
        ds.close()
    res["granulo"] = {"candidatos": {k: {"n": cu.frac(k)[0], "acuerdo": cu.frac(k)[1]} for k in cu.d},
                      "soporte": {k: {"interseccion": a[0], "union": a[1],
                                      "jaccard": a[0] / a[1] if a[1] else None} for k, a in sop.items()}}
    with open(os.path.join(RES, "%s_medir.json" % bloque), "w", encoding="utf-8") as fo:
        json.dump(res, fo, indent=1, default=float)
    # resumen por pantalla
    for caso, out in res["casos"].items():
        print("==", bloque, caso, "cuadros", out["n_cuadros"],
              "pixeles huella", sum(r["n_huella"] for r in out["por_cuadro"]))
        print("  huella sin valor S/SL:", sum(r["S_n_huella_sin_valor"] for r in out["por_cuadro"]),
              sum(r["SL_n_huella_sin_valor"] for r in out["por_cuadro"]),
              "| valor fuera de huella S/SL:", sum(r["S_n_valor_fuera_huella"] for r in out["por_cuadro"]),
              sum(r["SL_n_valor_fuera_huella"] for r in out["por_cuadro"]))
        print("  jaccard huella vs grupo ceniza / conv / union (min por cuadro): %.4f %.4f %.4f" % tuple(
            min(r[k] for r in out["por_cuadro"]) for k in
            ("jaccard_huella_grupo_ceniza", "jaccard_huella_grupo_conv", "jaccard_huella_union")))
        print("  huella en [solo ceniza, solo conv, ambos, ninguno]:", np.sum(
            [r["huella_en_ceniza_conv_ambos_ninguno"] for r in out["por_cuadro"]], axis=0).tolist(),
            "| grupo fuera de huella [ceniza, conv]:", np.sum(
            [r["grupo_fuera_huella_ceniza_conv"] for r in out["por_cuadro"]], axis=0).tolist())
        print("  tipos: %s; ids: %s" % (

            sorted(set(sum((r["event_type"] for r in out["por_cuadro"]), []))),
            sorted(set(sum((r["ids_evento"] for r in out["por_cuadro"]), [])))))
        for cl, v in out["candidatos"].items():
            print("  %-34s n=%6d acuerdo=%.4f nulo_corr=%s nulo_prev=%s" % (
                cl, v["n"], v["acuerdo"],
                "-" if v["nulo_corrido_max"] is None else "%.4f" % v["nulo_corrido_max"],
                "-" if v["nulo_previo"] is None else "%.4f" % v["nulo_previo"]))
        for k, v in out["soporte"].items():
            print("  soporte %-14s jaccard=%.4f" % (k, v["jaccard"]))
        for k, v in out["controles"].items():
            print("  control %-24s n=%6d acuerdo=%s nulo=%s" % (k, v["n"], v["acuerdo"], v["nulo_corrido"]))
    print("== granulo")
    for k, v in res["granulo"]["candidatos"].items():
        print("  %-12s n=%7d acuerdo=%.4f" % (k, v["n"], v["acuerdo"]))
    for k, v in res["granulo"]["soporte"].items():
        print("  soporte %-18s jaccard=%.4f" % (k, v["jaccard"]))


if __name__ == "__main__":
    main(sys.argv[1])
