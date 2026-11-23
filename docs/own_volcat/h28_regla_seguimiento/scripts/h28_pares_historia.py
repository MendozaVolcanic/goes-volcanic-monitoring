# -*- coding: utf-8 -*-
"""H28 (post hoc, arreglo de instrumento): tabla de PARES objeto / grupo historico.

h28_parse_logs.py guarda un renglon por objeto. En la segunda mitad de Fuego un objeto se
compara contra dos grupos historicos (dos lineas "Hist Idx" con su linea "N>>" cada una) y el
renglon por objeto mezclaba el tiempo de un par con el umbral refinado del otro. Aqui cada par
es un renglon, con la marca "Temporal selection criteria met" puesta en el par tras el cual se
imprime.

Uso: python -I h28_pares_historia.py <carpeta_logs> <salida.csv> <etiqueta> [hora_min hora_max]
"""
import csv, glob, os, re, sys
NUM = r"[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?"

def kv(line):
    return {m.group(1).strip(): m.group(2) for m in re.finditer(r"([A-Za-z][A-Za-z0-9 /_\-\(\)\^=\+\.]*?):\s*(" + NUM + r"|NA)", line)}

def main():
    files = sorted(glob.glob(os.path.join(sys.argv[1], "geocatASHOBJ.*.A?_I?_H?_S?.log")))
    pat = re.compile(r"\.(\d{6})\.A[YN]_")
    if len(sys.argv) >= 6:
        files = [f for f in files if sys.argv[4] <= pat.search(os.path.basename(f)).group(1) <= sys.argv[5]]
    rows = []
    for f in files:
        hora = pat.search(os.path.basename(f)).group(1)
        fase, obj, par = "", None, None
        for l in open(f, errors="replace"):
            s = l.strip()
            mf = re.search(r"Assessing objects (?:with|without) volcanoes \((\w+)\)", l)
            if mf: fase = mf.group(1)
            if s.startswith("VOLCAT_HISTORY_UTILS:HISTORY_GROUP2OBJECT>>"):
                obj = kv(s.split(">>", 1)[1]); par = None
            elif obj is not None and s.startswith("Hist Idx:"):
                d = kv(s)
                par = {"caso": sys.argv[3], "hora": hora, "fase": fase, "obj": obj.get("Obj Id"), "sel_opt": obj.get("Selection Opt"),
                       "explosive_frac": obj.get("Explosive Frac"), "area": obj.get("Area(km^2)"), "count": obj.get("Count"),
                       "kd_group": obj.get("Kd Group"), "hist_idx": d.get("Hist Idx"), "dt_s": d.get("Time diff(s)"),
                       "dist_km": d.get("Dist(km)"), "umbral_km": d.get("Dist Thresh(km)"), "dentro_poligono": d.get("Inside Polygon (0=NO)"),
                       "rama": "", "cumple": 0, "cumple_txt": ""}
                rows.append(par)
            elif par is not None and re.match(r"\d+>>", s):
                par["rama"] = s.split(">>")[0]
                d = kv(s.split(">>", 1)[1])
                for a, b in (("Refined Dist(km)", "ref_km"), ("Refined Dist Threshold(km)", "umbral_ref_km"), ("Out of Range Count", "fuera_rango"),
                             ("Area Hist(km^2)", "area_hist"), ("Group Id", "group_id"), ("Selection Opt", "sel_opt_hist"),
                             ("Overlap Frac", "overlap"), ("Emiss Sim", "emiss_sim"), ("Reff Sim", "reff_sim"), ("Beta85 Sim", "beta85_sim")):
                    if a in d:
                        try:
                            par[b] = d[a] if abs(float(d[a])) < 1e30 else ""
                        except ValueError:
                            par[b] = ""
            elif s.startswith("Temporal selection criteria met") and par is not None:
                par["cumple"] = 1; par["cumple_txt"] = s
            elif s.startswith("geocat>>") and "HISTORY_GROUP2OBJECT" not in s and "APPLY_OBJECT_CRITERIA" not in s:
                obj = None; par = None
    keys = []
    for r in rows:
        for k in r:
            if k not in keys: keys.append(k)
    with open(sys.argv[2], "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=keys); w.writeheader(); [w.writerow(r) for r in rows]
    print(sys.argv[3], len(files), "cuadros", len(rows), "pares", sum(r["cumple"] for r in rows), "cumplen")

if __name__ == "__main__":
    main()
