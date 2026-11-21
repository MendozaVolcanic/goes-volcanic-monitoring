"""H14, camino C1: anatomia de los archivos de evento VOLCAT GOES-19 de Nevados de Chillan (GVP 357070).

Criterio: docs/own_volcat/eventos_h14/criterio_H14_2026-11-21.md (subido antes de abrir ningun NetCDF).

Lee SOLO los 60 NetCDF y JSON de evento (ruta H14_EVENTOS, default D:\\goes_notas\\busqueda_2026-11-20\\
volcat_eventos_357070) y escribe numeros derivados por cuadro y por evento en resultados/. No copia grillas:
los archivos son de acceso restringido (ver LEEME.md de la carpeta de datos).

Uso:  python -I h14_eventos.py
"""
import sys, os, glob, json, csv
import numpy as np
import netCDF4 as nc
from scipy import ndimage

sys.stdout.reconfigure(encoding="utf-8")

D = os.environ.get("H14_EVENTOS", r"D:\goes_notas\busqueda_2026-11-20\volcat_eventos_357070")
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "resultados")
os.makedirs(OUT, exist_ok=True)
CRATER = (-36.863, -71.377)
FIRMA_CERO, FIRMA_ALTA = 0.05, 0.5
FILL_TIEMPO = -2.0e9


def hav(lat1, lon1, lat2, lon2):
    p1, p2 = np.radians(lat1), np.radians(lat2)
    a = np.sin((p2 - p1) / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(np.radians(lon2 - lon1) / 2) ** 2
    return 2 * 6371.0 * np.arcsin(np.sqrt(a))


def arr(ds, k):
    """Variable como float con NaN en relleno (netCDF4 aplica scale_factor y add_offset)."""
    v = ds[k][:]
    return np.ma.filled(np.ma.asarray(v).astype("float64"), np.nan)


def esc(ds, k, i=0):
    """Valor i de una variable por objeto, None si es relleno."""
    v = np.ma.asarray(ds[k][:]).ravel()[i]
    return None if np.ma.is_masked(v) else round(float(v), 3)


def stats(x, pre):
    """Mediana, p90, maximo, fraccion >= 0,5 y < 0,05 de la firma en un subconjunto de pixeles."""
    x = x[np.isfinite(x)]
    if x.size == 0:
        return {f"{pre}_n": 0, f"{pre}_med": None, f"{pre}_p90": None, f"{pre}_max": None,
                f"{pre}_fge05": None, f"{pre}_flt005": None}
    return {f"{pre}_n": int(x.size), f"{pre}_med": round(float(np.median(x)), 5),
            f"{pre}_p90": round(float(np.percentile(x, 90)), 5), f"{pre}_max": round(float(x.max()), 5),
            f"{pre}_fge05": round(float((x >= FIRMA_ALTA).mean()), 4),
            f"{pre}_flt005": round(float((x < FIRMA_CERO).mean()), 4)}


def med(x):
    x = x[np.isfinite(x)]
    return None if x.size == 0 else round(float(np.median(x)), 3)


def json_de(fn):
    j = json.load(open(os.path.join(D, "json", os.path.basename(fn)[:-3] + ".json"), encoding="utf-8"))
    ev = {}
    for v in j["VOLCANOES"]:
        for eid, lst in v["EVENTS"].items():
            for e in lst:
                ev[int(e["EVENT_IDX"])] = {"event_id": eid, "tipo": e["EVENT_TYPE"], "estado": e["EVENT_STATUS"],
                                           "inicio_1a_det": e["START_COVERAGE_TIME_INITIAL"],
                                           "feature_id": e["FEATURE_ID"], "feature_id_ini": e["FEATURE_ID_INITIAL"]}
    return ev


def cuadro(fn):
    ds = nc.Dataset(fn)
    lat, lon = arr(ds, "latitude"), arr(ds, "longitude")
    plat, plon = arr(ds, "pc_latitude"), arr(ds, "pc_longitude")
    ei = np.asarray(ds["event_idx"][:]).astype(int)
    sig, sigl = arr(ds, "ash_spectral_signature_strength"), arr(ds, "ash_spectral_signature_strength_lwir_only")
    b11, b12 = arr(ds, "brightness_temperature_11micron"), arr(ds, "brightness_temperature_12micron")
    hgt, mass, reff = arr(ds, "ash_cloud_height"), arr(ds, "ash_mass_loading"), arr(ds, "effective_radius_of_ash")
    rt, dtr = arr(ds, "residence_time"), arr(ds, "distance_traveled")
    dist = hav(lat, lon, *CRATER); pdist = hav(plat, plon, *CRATER)
    publicado = ei >= 0
    ta = ds["volcano_thermal_activity"]
    calor = {k: (None if float(ta.getncattr(k)) < FILL_TIEMPO else round(float(ta.getncattr(k)), 3))
             for k in ("time_since_0MW", "time_since_10MW", "time_since_100MW", "time_since_1000MW")}
    evj = json_de(fn)
    nev = len(ds.dimensions["number_of_events"])
    filas = []
    for k in range(nev):
        m = ei == k
        if not m.any():
            continue
        # borde = distancia de tablero 1 al pixel no publicado mas cercano; interior >= 2
        dborde = ndimage.distance_transform_cdt(m, metric="chessboard")
        borde, interior = m & (dborde == 1), m & (dborde >= 2)
        # anillo 3 a 6 px de la huella, sin pixeles publicados de ningun objeto y sin relleno
        dfuera = ndimage.distance_transform_cdt(~m, metric="chessboard")
        anillo = (~publicado) & (dfuera >= 3) & (dfuera <= 6) & np.isfinite(b11) & np.isfinite(b12)
        cerca = m & (dist <= 10.0); lejos = m & (dist > 10.0)
        btd = b11 - b12
        r = {"archivo": os.path.basename(fn), "inicio_scan": ds.getncattr("time_coverage_start"),
             "event_idx": k, **evj.get(k, {}),
             "feature_age_min": esc(ds, "feature_age", k),
             "min_volcano_distance_km": esc(ds, "minimum_volcano_distance", k),
             "n_px": int(m.sum()), "n_borde": int(borde.sum()), "n_interior": int(interior.sum()),
             "n_cerca10": int(cerca.sum()), "dist_min_km": round(float(dist[m].min()), 1),
             "dist_med_km": round(float(np.median(dist[m])), 1), "dist_max_km": round(float(dist[m].max()), 1),
             "paralaje_dist_min_km": (round(float(np.nanmin(pdist[m])), 1) if np.isfinite(pdist[m]).any() else None),
             "sza_med": esc(ds, "mean_feature_solar_zenith_angle", k), "area_km2": esc(ds, "feature_area", k)}
        r.update(stats(sig[m], "sig")); r.update(stats(sigl[m], "sigL"))
        r.update(stats(sig[cerca], "sig_cerca10")); r.update(stats(sig[lejos], "sig_lejos10"))
        r.update(stats(sigl[cerca], "sigL_cerca10"))
        r.update(stats(sig[borde], "sig_borde")); r.update(stats(sig[interior], "sig_interior"))
        # proxy por pixel de "recien incorporado" (DESVIACION: feature_age es escalar por objeto)
        rtm = rt[m]
        if np.isfinite(rtm).any():
            rmin = np.nanmin(rtm); nuevo = m & np.isfinite(rt) & (rt <= rmin + 1e-6)
            r["rt_min_h"] = round(float(rmin), 3); r["rt_med_h"] = med(rtm)
            r.update(stats(sig[nuevo], "sig_rtmin"))
        else:
            r["rt_min_h"] = None; r["rt_med_h"] = None; r.update(stats(np.array([]), "sig_rtmin"))
        r["dtrav_med_km"] = med(dtr[m])
        r.update({"bt11_huella": med(b11[m]), "bt11_anillo": med(b11[anillo]),
                  "btd_huella": med(btd[m]), "btd_anillo": med(btd[anillo]), "n_anillo": int(anillo.sum()),
                  "btd_frac_neg": round(float((btd[m] < 0).mean()), 4),
                  "hgt_med_km": med(hgt[m]), "mass_med_gm2": med(mass[m]), "reff_med_um": med(reff[m])})
        r["dbtd_huella_menos_anillo"] = (None if r["btd_huella"] is None or r["btd_anillo"] is None
                                         else round(r["btd_huella"] - r["btd_anillo"], 3))
        r["dbt11_huella_menos_anillo"] = (None if r["bt11_huella"] is None or r["bt11_anillo"] is None
                                          else round(r["bt11_huella"] - r["bt11_anillo"], 3))
        r.update({f"calor_{k2}": v for k2, v in calor.items()})
        for red in ("eni", "wwlln", "gld360", "glm"):
            for q in ("total_lightning_stroke_count", "near_vent_lightning_stroke_count",
                      "total_environmental_lightning_stroke_count"):
                v = np.ma.asarray(ds[f"{q}_{red}"][:]).ravel()[k]
                r[f"rayos_{q.split('_lightning')[0]}_{red}"] = None if np.ma.is_masked(v) else int(v)
        filas.append((r, {"sig": sig[m], "sigL": sigl[m], "cerca": sig[cerca], "lejos": sig[lejos]}))
    ds.close()
    return filas


def main():
    fs = sorted(glob.glob(os.path.join(D, "*.nc")))
    print("NetCDF:", len(fs))
    todas = []
    for f in fs:
        todas += cuadro(f)
    filas = [r for r, _ in todas]
    cols = list(dict.fromkeys(c for r in filas for c in r))
    with open(os.path.join(OUT, "por_cuadro.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols); w.writeheader(); w.writerows(filas)

    # ---- por evento (event_id del JSON)
    eventos = {}
    for r, px in todas:
        eventos.setdefault(r.get("event_id"), []).append((r, px))
    ev_filas, primeros = [], []
    for eid, lst in eventos.items():
        lst.sort(key=lambda t: t[0]["inicio_scan"])
        ini = lst[0][0]["inicio_1a_det"]
        # primer cuadro = inicio de scan igual (+-5 min) a la primera deteccion del JSON
        from datetime import datetime
        t0 = datetime.strptime(ini, "%Y-%m-%dT%H:%M:%SZ")
        p = [t for t in lst if abs((datetime.strptime(t[0]["inicio_scan"], "%Y-%m-%dT%H:%M:%SZ") - t0).total_seconds()) <= 300]
        primero = p[0] if p else None
        resto = [t for t in lst if t is not primero]
        e = {"event_id": eid, "tipo": lst[0][0].get("tipo"), "n_cuadros": len(lst), "inicio_1a_det": ini,
             "ultimo_scan": lst[-1][0]["inicio_scan"], "primer_cuadro_disponible": primero is not None,
             "tipos_en_serie": "|".join(sorted({t[0].get("tipo") for t in lst}))}
        if primero:
            r0, px0 = primero
            e.update({"pc_archivo": r0["archivo"], "pc_n_px": r0["n_px"], "pc_feature_age": r0["feature_age_min"],
                      "pc_dist_min_km": r0["dist_min_km"], "pc_n_cerca10": r0["n_cerca10"]})
            e.update(stats(px0["sig"], "pc_sig")); e.update(stats(px0["sigL"], "pc_sigL"))
            e.update(stats(px0["cerca"], "pc_sig_cerca10")); e.update(stats(px0["lejos"], "pc_sig_lejos10"))
            primeros.append(e)
        if resto:
            e.update(stats(np.concatenate([t[1]["sig"] for t in resto]), "resto_sig"))
            e.update(stats(np.concatenate([t[1]["sigL"] for t in resto]), "resto_sigL"))
            e.update(stats(np.concatenate([t[1]["cerca"] for t in resto]), "resto_sig_cerca10"))
        ev_filas.append(e)
    cols = list(dict.fromkeys(c for r in ev_filas for c in r))
    with open(os.path.join(OUT, "por_evento.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols); w.writeheader(); w.writerows(ev_filas)

    # ---- regla de decision (criterio)
    n_ev = len(ev_filas); n_pc = len(primeros)
    con_firma = [e["event_id"] for e in primeros if (e["pc_sig_fge05"] or 0) > 0.5]
    falsada = n_pc > 0 and len(con_firma) > n_pc / 2
    nucleo = [e["event_id"] for e in primeros
              if e["pc_sig_cerca10_med"] is not None and e["pc_sig_cerca10_med"] >= 0.5
              and (e["pc_sig_lejos10_med"] is None or e["pc_sig_lejos10_med"] < 0.05)]
    allsig = np.concatenate([t[1]["sig"] for t in todas]); allsigL = np.concatenate([t[1]["sigL"] for t in todas])
    allc = np.concatenate([t[1]["cerca"] for t in todas])
    res = {"n_cuadros": len(fs), "n_objetos_cuadro": len(filas), "n_eventos": n_ev,
           "n_primeros_cuadros_disponibles": n_pc, "primeros_con_firma_mayoritaria": con_firma,
           "condicion_falsacion_cumplida": bool(falsada),
           "veredicto": ("contradice H14 en esta muestra" if falsada else "compatible con H14, sin fuerza para sostenerla")
           if n_ev < 10 else ("H14 falsada" if falsada else "H14 sostenida"),
           "nucleo_con_firma_en": nucleo, "lectura_nucleo": "nucleo con firma" if len(nucleo) > n_pc / 2 else "sin nucleo con firma",
           "global_todos_px": {**stats(allsig, "sig"), **stats(allsigL, "sigL")},
           "global_cerca10": stats(allc, "sig_cerca10"),
           "tipos_evento": {e["event_id"]: e["tipo"] for e in ev_filas}}
    json.dump(res, open(os.path.join(OUT, "resumen.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps(res, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
