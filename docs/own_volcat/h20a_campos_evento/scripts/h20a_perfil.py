"""H20a, tarea 2: perfil por cuadro de los archivos de evento, con los campos ya calibrados en Fuego
(S = probabilidad publicada P; SL = probabilidad de pixel infrarroja P_IR). Lee SOLO archivos de evento:
los 60 de Chillan, el de San Cristobal y los 26 de Fuego (referencia). Mismo codigo para los tres.

Uso: python -I h20a_perfil.py
Escribe resultados/perfil_por_cuadro.csv, perfil_por_evento.json, esquema.json y transferencia_chillan.json.
No escribe grillas.

Comprobacion de transferencia agregada post hoc (antes de calcularla): comparar, cuadro a cuadro, la
fraccion de la huella con S >= 0,2 y >= 0,5 del archivo de evento con la fraccion de la huella con
probabilidad >= 20 % y >= 50 % que PR 85 decodifico del PNG Ash_Probability del sitio de VOLCAT
(docs/own_volcat/sitio_volcat/resultados/por_cuadro.csv). Es una fuente independiente de la misma version
(v3r4). Limite conocido: el PNG tiene un desfase de georreferencia de cerca de 1 pixel (H14).
"""
import os
import sys
import csv
import glob
import json
import numpy as np
import netCDF4 as nc
from scipy import ndimage, stats
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from h20a_comun import EV_FUEGO, EV_CHILLAN, RES, arr, hav, logit

sys.stdout.reconfigure(encoding="utf-8")
USADAS = ["ash_spectral_signature_strength", "ash_spectral_signature_strength_lwir_only", "residence_time",
          "distance_traveled", "event_idx", "feature_age", "minimum_volcano_distance",
          "maximum_volcano_distance", "brightness_temperature_4micron", "brightness_temperature_8micron",
          "brightness_temperature_11micron", "brightness_temperature_12micron", "latitude", "longitude",
          "pc_latitude", "pc_longitude", "ash_cloud_height", "mean_feature_solar_zenith_angle",
          "volcano_thermal_activity", "event_type", "feature_area"]


def esquema(path):
    ds = nc.Dataset(path)
    out = {}
    for k in USADAS:
        if k not in ds.variables:
            out[k] = None
            continue
        v = ds[k]
        out[k] = {"dtype": str(v.dtype), "dims": list(v.dimensions),
                  "long_name": getattr(v, "long_name", None), "units": getattr(v, "units", None)}
    glob_ = {a: str(ds.getncattr(a)) for a in ("history", "production_site", "production_environment", "platform")
             if a in ds.ncattrs()}
    ds.close()
    return out, glob_


def eventos_json(path_nc):
    base = os.path.basename(path_nc)[:-3] + ".json"
    for cand in (os.path.join(os.path.dirname(path_nc), "json", base), path_nc[:-3] + ".json"):
        if os.path.exists(cand):
            j = json.load(open(cand, encoding="utf-8"))
            ev = {}
            for v in j.get("VOLCANOES", []):
                for eid, lst in v.get("EVENTS", {}).items():
                    for e in lst:
                        ev[int(e.get("EVENT_IDX", 0))] = {"event_id": eid, "estado": e.get("EVENT_STATUS")}
            return ev
    return {}


def control_bt11(hue, excl, bt11, campos, k=5, lejos=3, dmax=1.0):
    """Por cada pixel de la huella, los k pixeles fuera de la huella, a mas de `lejos` pixeles de ella y con
    BT11 mas parecida (|dif| <= dmax K). Devuelve la mediana de (huella - control) de cada campo y n."""
    dist = ndimage.distance_transform_cdt(~excl, metric="chessboard")
    cand = (dist > lejos) & np.isfinite(bt11)
    for c in campos.values():
        cand &= np.isfinite(c)
    cy, cx = np.nonzero(cand)
    if cy.size < k:
        return {n: None for n in campos}, 0
    cb = bt11[cy, cx]
    orden = np.argsort(cb)
    cb_o = cb[orden]
    difs = {n: [] for n in campos}
    usados = 0
    for y, x in zip(*np.nonzero(hue)):
        b = bt11[y, x]
        if not np.isfinite(b) or any(not np.isfinite(c[y, x]) for c in campos.values()):
            continue
        i = np.searchsorted(cb_o, b)
        lo, hi = max(0, i - k), min(cb_o.size, i + k)
        sel = orden[lo:hi]
        sel = sel[np.argsort(np.abs(cb[sel] - b))][:k]
        sel = sel[np.abs(cb[sel] - b) <= dmax]
        if sel.size == 0:
            continue
        usados += 1
        for n, c in campos.items():
            difs[n].append(c[y, x] - np.mean(c[cy[sel], cx[sel]]))
    return {n: (float(np.median(v)) if v else None) for n, v in difs.items()}, usados


def r4(x, nd=4):
    return None if x is None or not np.isfinite(x) else round(float(x), nd)


def perfil(path, caso):
    ds = nc.Dataset(path)
    idx = np.ma.filled(ds["event_idx"][:], -1).astype(int)
    S = arr(ds, "ash_spectral_signature_strength")
    SL = arr(ds, "ash_spectral_signature_strength_lwir_only")
    R = arr(ds, "residence_time")
    D = arr(ds, "distance_traveled")
    bt = {k: arr(ds, "brightness_temperature_%smicron" % k) for k in ("4", "8", "11", "12")}
    vi = ds["volcano_info"]
    vlat, vlon = float(vi.getncattr("latitude")), float(vi.getncattr("longitude"))
    dpc = hav(vlat, vlon, arr(ds, "pc_latitude"), arr(ds, "pc_longitude"))
    dnom = hav(vlat, vlon, arr(ds, "latitude"), arr(ds, "longitude"))
    ta = ds["volcano_thermal_activity"]
    term = {k: float(ta.getncattr(k)) for k in ("time_since_0MW", "time_since_10MW", "time_since_100MW",
                                                "time_since_1000MW")}
    evj = eventos_json(path)
    tipos = [str(q) for q in ds["event_type"][:]]
    inicio = str(ds.getncattr("time_coverage_start"))
    filas = []
    todos = idx >= 0
    for k in sorted(set(idx[todos].tolist())):
        hue = idx == k
        n = int(hue.sum())
        esc = lambda v: (lambda a: None if not np.isfinite(a) or a < -900 else float(a))(
            float(np.ma.filled(ds[v][:].astype("f8"), np.nan).ravel()[k]))
        s, sl = S[hue], SL[hue]
        par = np.isfinite(s) & np.isfinite(sl)
        salto = logit(s[par]) - logit(sl[par])
        salto = salto[np.isfinite(salto)]
        r, d = R[hue], D[hue]
        edad = esc("feature_age")
        cero = np.isfinite(r) & (r == 0)
        ctrl, nctrl = control_bt11(hue, todos, bt["11"],
                                   {"btd1112": bt["11"] - bt["12"], "btd8511": bt["8"] - bt["11"],
                                    "btd3911": bt["4"] - bt["11"]})
        f = {"caso": caso, "inicio_scan": inicio, "event_idx": k, "event_id": evj.get(k, {}).get("event_id"),
             "tipo": tipos[k], "n_px": n, "edad_min": r4(edad, 1),
             "dist_min_km": r4(esc("minimum_volcano_distance"), 1),
             "dist_max_km": r4(esc("maximum_volcano_distance"), 1),
             "sza": r4(esc("mean_feature_solar_zenith_angle"), 1),
             "S_n": int(np.isfinite(s).sum()), "S_med": r4(np.nanmedian(s) if np.isfinite(s).any() else None, 5),
             "S_max": r4(np.nanmax(s) if np.isfinite(s).any() else None, 5),
             "S_n_ge05": int((s >= 0.5).sum()), "S_n_ge02": int((s >= 0.2).sum()), "S_n_lt005": int((s < 0.05).sum()),
             "SL_n": int(np.isfinite(sl).sum()),
             "SL_med": r4(np.nanmedian(sl) if np.isfinite(sl).any() else None, 5),
             "SL_max": r4(np.nanmax(sl) if np.isfinite(sl).any() else None, 5),
             "SL_n_ge05": int((sl >= 0.5).sum()), "SL_n_ge02": int((sl >= 0.2).sum()),
             "SL_n_lt005": int((sl < 0.05).sum()),
             "n_S_mayor_SL_005": int((s[par] > sl[par] + 0.05).sum()),
             "n_S_menor_SL_005": int((s[par] < sl[par] - 0.05).sum()),
             "salto_n": int(salto.size), "salto_med": r4(np.median(salto) if salto.size else None, 2),
             "salto_n_ge5": int((salto >= 5).sum()),
             "fuera_rango_S": int(((s < 0) | (s > 1)).sum()), "fuera_rango_SL": int(((sl < 0) | (sl > 1)).sum()),
             "S_fuera_huella": int((np.isfinite(S) & ~todos).sum()), "SL_fuera_huella": int((np.isfinite(SL) & ~todos).sum()),
             "rt_min_h": r4(np.nanmin(r) if np.isfinite(r).any() else None), "rt_med_h": r4(np.nanmedian(r) if np.isfinite(r).any() else None),
             "rt_max_h": r4(np.nanmax(r) if np.isfinite(r).any() else None),
             "rt_n_cero": int(cero.sum()),
             "rt_n_mayor_edad": int((r > (edad or 0) / 60.0 + 0.01).sum()) if edad is not None else None,
             "rt_cero_dist_igual_dpc": int((np.abs(d[cero] - dpc[hue][cero]) <= np.maximum(1.0, 0.02 * dpc[hue][cero])).sum()),
             "rt_cero_dist_igual_dnom": int((np.abs(d[cero] - dnom[hue][cero]) <= np.maximum(1.0, 0.02 * dnom[hue][cero])).sum()),
             "dt_min_km": r4(np.nanmin(d) if np.isfinite(d).any() else None, 1),
             "dt_max_km": r4(np.nanmax(d) if np.isfinite(d).any() else None, 1),
             "n_dt_menor_dpc": int((d < dpc[hue] - 1.0).sum()),
             "h_med_km": r4(np.nanmedian(arr(ds, "ash_cloud_height")[hue]) if np.isfinite(arr(ds, "ash_cloud_height")[hue]).any() else None, 2),
             "bt11_med": r4(np.nanmedian(bt["11"][hue]), 2),
             "btd1112_med": r4(np.nanmedian((bt["11"] - bt["12"])[hue]), 2),
             "ctrl_n": nctrl, "ctrl_dbtd1112": r4(ctrl.get("btd1112"), 3), "ctrl_dbtd8511": r4(ctrl.get("btd8511"), 3),
             "ctrl_dbtd3911": r4(ctrl.get("btd3911"), 3)}
        f.update({k2: (None if v < -900 else v) for k2, v in term.items()})
        filas.append(f)
    ds.close()
    return filas


def main():
    os.makedirs(RES, exist_ok=True)
    fu = sorted(glob.glob(os.path.join(EV_FUEGO, "VOLCAT-FD-vid342090_*.nc")))
    sc = sorted(glob.glob(os.path.join(EV_FUEGO, "VOLCAT-FD-vid344020_*.nc")))
    ch = sorted(glob.glob(os.path.join(EV_CHILLAN, "VOLCAT-FD-vid357070_*.nc")))
    # 1. esquema de las variables usadas, Fuego contra Chillan
    e1, g1 = esquema(sc[0])
    e2, g2 = esquema(ch[0])
    dif = {k: {"fuego": e1[k], "chillan": e2[k]} for k in USADAS if e1[k] != e2[k]}
    json.dump({"globales_fuego": g1, "globales_chillan": g2, "variables_usadas": USADAS,
               "iguales": [k for k in USADAS if e1[k] == e2[k]], "distintas": dif},
              open(os.path.join(RES, "esquema.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print("esquema: %d variables usadas, %d iguales, distintas: %s" % (len(USADAS), len(USADAS) - len(dif), list(dif)))
    print("globales fuego:", g1, "| chillan:", g2)
    # 2. perfil por cuadro
    filas = []
    for caso, lista in (("san_cristobal", sc), ("chillan", ch), ("fuego", fu)):
        for p in lista:
            filas += perfil(p, caso)
    cols = list(filas[0].keys())
    with open(os.path.join(RES, "perfil_por_cuadro.csv"), "w", newline="", encoding="utf-8") as fo:
        w = csv.DictWriter(fo, fieldnames=cols)
        w.writeheader()
        w.writerows(filas)
    # 3. por evento
    ev = {}
    for f in filas:
        clave = "%s|%s|%s" % (f["caso"], f["tipo"], f["event_id"] if f["caso"] != "fuego" else "fuego")
        ev.setdefault(clave, []).append(f)
    resumen = {}
    for clave, fs in ev.items():
        fs = sorted(fs, key=lambda q: q["inicio_scan"])
        tot = lambda k: int(sum(q[k] or 0 for q in fs))
        prim = fs[0]
        cuadros_qa = sum(1 for q in fs if q["SL_med"] is not None and q["SL_med"] < 0.5)
        cuadros_qb = sum(1 for q in fs if (q["S_med"] is not None and q["S_med"] >= 0.5)
                         or (q["salto_n"] and q["salto_n_ge5"] > q["salto_n"] / 2))
        resumen[clave] = {
            "n_cuadros": len(fs), "primer_cuadro": prim["inicio_scan"], "ultimo_cuadro": fs[-1]["inicio_scan"],
            "px_total": tot("n_px"), "px_min": min(q["n_px"] for q in fs), "px_max": max(q["n_px"] for q in fs),
            "px_mediana": float(np.median([q["n_px"] for q in fs])),
            "S_n": tot("S_n"), "S_ge05": tot("S_n_ge05"), "S_ge02": tot("S_n_ge02"), "S_lt005": tot("S_n_lt005"),
            "SL_n": tot("SL_n"), "SL_ge05": tot("SL_n_ge05"), "SL_ge02": tot("SL_n_ge02"), "SL_lt005": tot("SL_n_lt005"),
            "SL_max": max((q["SL_max"] or 0) for q in fs), "S_max": max((q["S_max"] or 0) for q in fs),
            "S_mayor_SL": tot("n_S_mayor_SL_005"), "S_menor_SL": tot("n_S_menor_SL_005"),
            "salto_n": tot("salto_n"), "salto_ge5": tot("salto_n_ge5"),
            "cuadros_Qa_SLmed_lt05": cuadros_qa, "cuadros_Qb_subida": cuadros_qb,
            "fuera_rango": tot("fuera_rango_S") + tot("fuera_rango_SL"),
            "valor_fuera_huella": tot("S_fuera_huella") + tot("SL_fuera_huella"),
            "primer_cuadro_detalle": {k: prim[k] for k in (
                "n_px", "edad_min", "dist_min_km", "dist_max_km", "sza", "S_med", "S_max", "S_n_ge05", "SL_med",
                "SL_max", "SL_n_ge05", "salto_med", "rt_min_h", "rt_max_h", "rt_n_cero", "rt_cero_dist_igual_dpc",
                "h_med_km", "bt11_med", "btd1112_med", "ctrl_n", "ctrl_dbtd1112", "ctrl_dbtd8511", "ctrl_dbtd3911",
                "time_since_0MW", "time_since_10MW", "time_since_100MW", "time_since_1000MW")},
            "edad_min_rango": [min(q["edad_min"] for q in fs), max(q["edad_min"] for q in fs)],
            "rt_cero_px": tot("rt_n_cero"), "rt_cero_dist_igual_dpc": tot("rt_cero_dist_igual_dpc"),
            "rt_cero_dist_igual_dnom": tot("rt_cero_dist_igual_dnom"),
            "rt_mayor_edad_px": tot("rt_n_mayor_edad"), "dt_menor_dpc_px": tot("n_dt_menor_dpc"),
            "ctrl_dbtd1112_mediana_cuadros": r4(np.median([q["ctrl_dbtd1112"] for q in fs if q["ctrl_dbtd1112"] is not None]) if any(q["ctrl_dbtd1112"] is not None for q in fs) else None, 3),
            "ctrl_dbtd8511_mediana_cuadros": r4(np.median([q["ctrl_dbtd8511"] for q in fs if q["ctrl_dbtd8511"] is not None]) if any(q["ctrl_dbtd8511"] is not None for q in fs) else None, 3),
            "cuadros_con_termica_0MW": sum(1 for q in fs if q["time_since_0MW"] is not None),
        }
    json.dump(resumen, open(os.path.join(RES, "perfil_por_evento.json"), "w", encoding="utf-8"), indent=1,
              ensure_ascii=False)
    for clave, r in resumen.items():
        p = r["primer_cuadro_detalle"]
        print("\n== %s: %d cuadros (%s a %s), px %d..%d (mediana %.0f), edad %s min" % (
            clave, r["n_cuadros"], r["primer_cuadro"][5:16], r["ultimo_cuadro"][5:16], r["px_min"], r["px_max"],
            r["px_mediana"], r["edad_min_rango"]))
        print("   S (P publicada): n=%d, >=0,5: %d (%.1f %%), >=0,2: %d, <0,05: %d, max %.3f" % (
            r["S_n"], r["S_ge05"], 100 * r["S_ge05"] / max(r["S_n"], 1), r["S_ge02"], r["S_lt005"], r["S_max"]))
        print("   SL (P_IR): n=%d, >=0,5: %d (%.1f %%), >=0,2: %d, <0,05: %d, max %.3f" % (
            r["SL_n"], r["SL_ge05"], 100 * r["SL_ge05"] / max(r["SL_n"], 1), r["SL_ge02"], r["SL_lt005"], r["SL_max"]))
        print("   S > SL + 0,05: %d ; S < SL - 0,05: %d ; salto >= 5: %d de %d ; cuadros Qa: %d ; cuadros Qb: %d ; fuera de rango: %d ; valor fuera de huella: %d" % (
            r["S_mayor_SL"], r["S_menor_SL"], r["salto_ge5"], r["salto_n"], r["cuadros_Qa_SLmed_lt05"],
            r["cuadros_Qb_subida"], r["fuera_rango"], r["valor_fuera_huella"]))
        print("   tiempo == 0: %d px, de ellos dist == d_pc: %d, dist == d_nominal: %d ; tiempo > edad: %d px ; dist < d_pc: %d px ; control BT11: dBTD11-12 %s K, dBTD8,5-11 %s K ; cuadros con termica: %d" % (
            r["rt_cero_px"], r["rt_cero_dist_igual_dpc"], r["rt_cero_dist_igual_dnom"], r["rt_mayor_edad_px"],
            r["dt_menor_dpc_px"], r["ctrl_dbtd1112_mediana_cuadros"], r["ctrl_dbtd8511_mediana_cuadros"],
            r["cuadros_con_termica_0MW"]))
        print("   primer cuadro:", {k: v for k, v in p.items()})
    # 4. transferencia en Chillan: contra el PNG del sitio (PR 85) y obligaciones internas
    png = os.path.join(os.path.dirname(os.path.dirname(RES)), "sitio_volcat", "resultados", "por_cuadro.csv")
    tr = {"png_csv": os.path.exists(png)}
    chf = [f for f in filas if f["caso"] == "chillan"]
    tr["chillan_px"] = int(sum(f["n_px"] for f in chf))
    tr["fuera_rango"] = int(sum(f["fuera_rango_S"] + f["fuera_rango_SL"] for f in chf))
    tr["valor_fuera_huella"] = int(sum(f["S_fuera_huella"] + f["SL_fuera_huella"] for f in chf))
    noche = [f for f in chf if f["sza"] is not None and f["sza"] >= 85]
    tr["noche_cuadros"] = len(noche)
    tr["noche_px_S_distinto_SL"] = int(sum(f["n_S_mayor_SL_005"] + f["n_S_menor_SL_005"] for f in noche))
    tr["noche_px_par"] = int(sum(f["salto_n"] for f in noche))
    pasos = sorted(set(round(f[k], 4) for f in chf for k in ("rt_min_h", "rt_max_h") if f[k] is not None))
    d = np.diff(pasos)
    tr["rt_paso_min_h"] = r4(d[d > 1e-6].min() if (d > 1e-6).any() else None)
    tr["rt_multiplo_de_10min"] = bool(all(abs(p * 6 - round(p * 6)) < 0.02 for p in pasos))
    if tr["png_csv"]:
        P = {r["inicio_scan"]: r for r in csv.DictReader(open(png, encoding="utf-8"))}
        xs = {"nom20": [], "nom50": [], "desf20": [], "desf50": []}
        ys = {"s20": [], "s50": []}
        usados = 0
        for f in chf:
            r = P.get(f["inicio_scan"])
            if r is None or f["n_px"] < 5 or r["png"] != "True" or int(float(r["px_color_imagen"])) == 0:
                continue
            usados += 1
            ys["s20"].append(f["S_n_ge02"] / f["n_px"])
            ys["s50"].append(f["S_n_ge05"] / f["n_px"])
            xs["nom20"].append(float(r["nom_huella_frac_ge20"]))
            xs["nom50"].append(float(r["nom_huella_frac_ge50"]))
            xs["desf20"].append(float(r["desf_huella_frac_ge20"]))
            xs["desf50"].append(float(r["desf_huella_frac_ge50"]))
        tr["png_cuadros_usados"] = usados
        for a, b in (("s20", "nom20"), ("s20", "desf20"), ("s50", "nom50"), ("s50", "desf50")):
            y, x = np.array(ys[a]), np.array(xs[b])
            rho = stats.spearmanr(y, x).statistic if (y.std() > 0 and x.std() > 0) else float("nan")
            conc = float(np.mean((y > 0) == (x > 0)))
            tr["%s_vs_png_%s" % (a, b)] = {
                "spearman": r4(rho, 3), "concordancia_cero_no_cero": r4(conc, 3),
                "ambos_cero": int(((y == 0) & (x == 0)).sum()), "ambos_no_cero": int(((y > 0) & (x > 0)).sum()),
                "solo_evento": int(((y > 0) & (x == 0)).sum()), "solo_png": int(((y == 0) & (x > 0)).sum()),
                "mediana_evento": r4(np.median(y)), "mediana_png": r4(np.median(x)),
                "max_evento": r4(y.max()), "max_png": r4(x.max())}
    json.dump(tr, open(os.path.join(RES, "transferencia_chillan.json"), "w", encoding="utf-8"), indent=1)
    print("\n== transferencia Chillan:")
    for k, v in tr.items():
        print("  ", k, v)


if __name__ == "__main__":
    main()
