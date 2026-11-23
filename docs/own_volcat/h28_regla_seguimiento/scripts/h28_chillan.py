# -*- coding: utf-8 -*-
"""H28, prueba 2: consecuencias de la regla de seguimiento visibles en archivos de evento
de VOLCAT (pruebas C0 a C5 de 01_REGLA_Y_CRITERIO.md).

Uso:
  python -I h28_chillan.py <carpeta_eventos> <patron_nc> <cadencia_s> <tabla_cuadros.csv> <resumen.json>

  <patron_nc>  por ejemplo "VOLCAT-FD-vid357070_*.nc" (Chillan) o "VOLCAT-JP-vid282090_*.nc"
               (Kirishima, control positivo: el log dice cuales son nacimientos).

Escribe <tabla_cuadros.csv> (un renglon por cuadro con campos del archivo de evento: va
FUERA del repositorio, en D:/goes_notas/s19/h28/resultados/, porque transcribe datos de
SSEC de licencia restringida) y <resumen.json> (conteos propios: ese si se commitea).

FICHA SDA (Res. CPLT 372): este script no clasifica ni decide nada del dashboard. Lee
archivos de evento publicados por SSEC/CIMSS y cuenta si son compatibles con una regla
propuesta. Datos de entrada con licencia restringida: no se suben al repositorio.
"""
import glob
import json
import os
import re
import sys

import netCDF4 as nc
import numpy as np
import pandas as pd

R = 6371.0


def hav(lat1, lon1, lat2, lon2):
    p1, p2 = np.radians(lat1), np.radians(lat2)
    a = np.sin((p2 - p1) / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(np.radians(lon2 - lon1) / 2) ** 2
    return 2 * R * np.arcsin(np.sqrt(a))


def epoch_from_name(name):
    m = re.search(r"_s(\d{4})(\d{2})(\d{2})(\d{2})(\d{2})(\d{2})\d_", name)
    return int(pd.Timestamp("%s-%s-%s %s:%s:%s" % m.groups(), tz="UTC").timestamp())


def main():
    d, pat, cad, sal_tabla, sal_resumen = sys.argv[1], sys.argv[2], float(sys.argv[3]), sys.argv[4], sys.argv[5]
    files = sorted(glob.glob(os.path.join(d, pat)))
    rows, huellas = [], []
    for f in files:
        ds = nc.Dataset(f)
        ds.set_auto_mask(False)
        ei = ds["event_idx"][:]
        m = ei >= 0
        lat, lon = ds["latitude"][:][m], ds["longitude"][:][m]
        ppub = ds["ash_spectral_signature_strength"][:][m].astype(float)
        pir = ds["ash_spectral_signature_strength_lwir_only"][:][m].astype(float)
        nev = len(ds["feature_area"][:])
        r = {"archivo": os.path.basename(f), "t_inicio": epoch_from_name(os.path.basename(f)), "n_eventos": nev,
             "tipo": str(ds["event_type"][0]), "feature_id": int(ds["feature_id"][0]),
             "first_feature_id": int(ds["first_detection_feature_id"][0]),
             "edad_min": float(ds["feature_age"][0]),
             "t_medio": int(ds["mean_feature_time"][0]), "t_medio_primera": int(ds["first_detection_mean_feature_time"][0]),
             "t_inicio_primera": int(ds["first_detection_full_image_start_time"][0]),
             "primera_txt": str(ds["time_coverage_start_first_detection"][0]),
             "area_km2": float(ds["feature_area"][0]), "dmin_volcan_km": float(ds["minimum_volcano_distance"][0]),
             "dmax_volcan_km": float(ds["maximum_volcano_distance"][0]),
             "cenit_solar": float(ds["mean_feature_solar_zenith_angle"][0]), "n_pix": int(m.sum()),
             "pix_ppub_ge05": int((ppub >= 0.5).sum()), "pix_subida": int(((ppub >= 0.5) & (pir < 0.05)).sum()),
             "pix_pir_ge05": int((pir >= 0.5).sum()), "ppub_max": float(ppub.max()) if m.any() else np.nan,
             "pir_max": float(pir.max()) if m.any() else np.nan}
        va = ds["volcano_thermal_activity"]
        for a in ("time_since_0MW", "time_since_10MW", "time_since_100MW"):
            v = float(va.getncattr(a))
            r["calor_" + a] = v if -1e6 < v < 1e6 else np.nan
        # identificador de cadena del JSON hermano, si existe
        jf = os.path.join(d, "json", r["archivo"].replace(".nc", ".json"))
        if not os.path.exists(jf):
            jf = f.replace(".nc", ".json")
        if os.path.exists(jf):
            ev = json.load(open(jf))["VOLCANOES"][0]["EVENTS"]
            r["json_ids"] = ";".join(ev.keys())
            r["json_largo"] = ";".join(str(len(v)) for v in ev.values())
        rows.append(r)
        huellas.append((lat, lon))
        ds.close()
    T = pd.DataFrame(rows)
    T["hora"] = pd.to_datetime(T.t_inicio, unit="s").dt.strftime("%d-%m %H:%M")

    # ---- C0 control de lectura
    edad_calc = (T.t_medio - T.t_medio_primera) / 60.0
    T["edad_calc_min"] = edad_calc
    c0_edad = bool(((T.edad_min - edad_calc).abs() <= 0.05).all())
    if "json_ids" in T:
        id_esp = "ID-" + pd.to_datetime(T.t_inicio_primera, unit="s").dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        T["json_ok"] = [e in str(j) for e, j in zip(id_esp, T.json_ids)]
        c0_json = bool(T.json_ok.all())
    else:
        c0_json = None
    # control de huella: n_pix * area de pixel dentro de un factor 2 del area declarada
    T["area_por_pix"] = T.area_km2 / T.n_pix
    huella_ok = bool(T.area_por_pix.between(T.area_por_pix.median() / 2, T.area_por_pix.median() * 2).all())

    # ---- cadenas
    T["nacimiento"] = T.edad_min.abs() < 0.05
    T["cadena"] = T.t_inicio_primera
    T["tiene_anterior"] = False
    T["dt_anterior_s"] = np.nan
    T["dist_huella_anterior_km"] = np.nan
    T["pix_compartidos"] = np.nan
    for i, r in T.iterrows():
        if r.nacimiento:
            continue
        # cuadro anterior de la misma cadena: el mas reciente con t < t_i
        prev = T[(T.cadena == r.cadena) & (T.t_inicio < r.t_inicio)]
        if len(prev) == 0:
            continue
        j = prev.t_inicio.idxmax()
        dt = r.t_inicio - T.t_inicio[j]
        T.loc[i, "dt_anterior_s"] = dt
        T.loc[i, "tiene_anterior"] = bool(abs(dt - cad) <= 0.15 * cad)
        la, lo = huellas[i]
        lb, lob = huellas[j]
        dd = hav(la[:, None], lo[:, None], lb[None, :], lob[None, :])
        T.loc[i, "dist_huella_anterior_km"] = float(dd.min())
        T.loc[i, "pix_compartidos"] = int((dd.min(axis=1) < 0.5).sum())
    cont = T[~T.nacimiento]
    nac = T[T.nacimiento]

    res = {"cuadros": len(T), "nacimientos": int(len(nac)), "continuaciones": int(len(cont)),
           "cadenas": int(T.cadena.nunique()),
           "C0": {"edad_ok": c0_edad, "json_ok": c0_json, "huella_ok": huella_ok,
                  "area_por_pix_mediana": float(T.area_por_pix.median()),
                  "cumple": bool(c0_edad and (c0_json in (True, None)))},
           "tipos": T.tipo.value_counts().to_dict(), "n_eventos_por_archivo": T.n_eventos.value_counts().to_dict()}
    sin_ant = cont[~cont.tiene_anterior]
    res["C1"] = {"continuaciones": int(len(cont)), "con_cuadro_anterior": int(cont.tiene_anterior.sum()),
                 "sin_cuadro_anterior": [{"hora": h, "dt_s": float(x), "cadena": pd.to_datetime(c, unit="s").strftime("%d-%m %H:%M")}
                                         for h, x, c in zip(sin_ant.hora, sin_ant.dt_anterior_s, sin_ant.cadena)]}
    c2 = cont.dropna(subset=["dist_huella_anterior_km"])
    lim = 0.05 * c2.dt_anterior_s
    res["C2"] = {"evaluadas": int(len(c2)), "dentro": int((c2.dist_huella_anterior_km <= lim).sum()),
                 "dist_max_km": float(c2.dist_huella_anterior_km.max()) if len(c2) else None,
                 "cumple": bool(len(c2) and (c2.dist_huella_anterior_km <= lim).all())}
    res["C3"] = {"evaluadas": int(len(c2)), "con_pixel_compartido": int((c2.pix_compartidos > 0).sum())}
    res["C4"] = {"nacimientos": int(len(nac)), "dmin_km": [round(float(x), 2) for x in nac.dmin_volcan_km],
                 "horas": list(nac.hora), "dentro_4km": int((nac.dmin_volcan_km <= 4.0).sum()),
                 "cumple": bool(len(nac) and (nac.dmin_volcan_km <= 4.0).all())}
    res["C5"] = {"pix_subida_total": int(T.pix_subida.sum()), "en_nacimientos": int(nac.pix_subida.sum()),
                 "en_continuaciones": int(cont.pix_subida.sum()),
                 "cuadros_con_subida": int((T.pix_subida > 0).sum()),
                 "nacimientos_de_dia": int((nac.cenit_solar < 85).sum()),
                 "nacimientos_cenit": [round(float(x), 1) for x in nac.cenit_solar],
                 "continuaciones_de_dia": int((cont.cenit_solar < 85).sum()),
                 "continuaciones_de_dia_con_subida": int(((cont.cenit_solar < 85) & (cont.pix_subida > 0)).sum())}
    res["C5"]["cumple"] = ("sin poder" if res["C5"]["nacimientos_de_dia"] == 0 or res["C5"]["pix_subida_total"] == 0
                           else bool(res["C5"]["en_nacimientos"] == 0))
    expl = cont[cont.tiene_anterior & (cont.dist_huella_anterior_km <= 0.05 * cont.dt_anterior_s)]
    res["explicadas_por_B"] = {"continuaciones": int(len(cont)), "explicadas": int(len(expl)),
                               "fraccion": float(len(expl) / len(cont)) if len(cont) else None}
    T.drop(columns=["archivo"]).to_csv(sal_tabla, index=False)
    json.dump(res, open(sal_resumen, "w"), indent=1, ensure_ascii=False)
    print(json.dumps(res, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
