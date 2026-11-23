# -*- coding: utf-8 -*-
"""H28: tabla de la construccion de plumas ancladas a un volcan (CONSTRUCT_VOLCANIC_PLUMES).
Por cada volcan evaluado en cada cuadro guarda los dos numeros del renglon resumen
("<nombre>  v1  v2"), cuantos objetos se evaluaron, el mejor FINAL y si hubo MATCH.

La salida transcribe lineas de log de SSEC: va FUERA del repositorio
(D:/goes_notas/s19/h28/tablas/). No commitearla.

Uso: python -I h28_match_volcan.py <carpeta_logs> <salida.csv> <etiqueta> [hora_min hora_max]
No decide nada del dashboard: ordena lo que el log de SSEC imprime.
"""
import csv, glob, os, re, sys
NUM = r"[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?"
HEAD = re.compile(r"^\s+(\d+)\s+(\S.*?\S)\s+(\d+)\s+(\d+)\s*$")
SUMM = re.compile(r"^\s{3,}([A-Za-z].*?\S)\s+(" + NUM + r")\s+(" + NUM + r")\s*$")

def run(path, tag):
    hora = re.search(r"\.(\d{6})\.A[YN]_", os.path.basename(path)).group(1)
    rows, sec, cur, names = [], None, None, {}
    recs = {}  # (sec, idx) -> list of FINAL tuples
    for l in open(path, errors="replace"):
        l = l.rstrip("\n")
        if "Looking for strong plumes" in l: sec = "strong"; continue
        if "Looking for weak plumes" in l: sec = "weak"; continue
        if "Assessing objects without volcanoes (ASH)" in l: sec = None; continue
        if sec is None: continue
        m = HEAD.match(l)
        if m and not l.strip().replace(" ", "").isdigit():
            cur = (sec, m.group(1)); names[m.group(1)] = m.group(2)
            recs.setdefault(cur, []); continue
        s = l.strip()
        if s.startswith("FINAL:") and cur:
            recs[cur].append([float(x) for x in re.findall(NUM, s)]); continue
        m = SUMM.match(l)
        if m and not s.startswith(("Overlap", "FINAL", "MATCH", "NO MATCH")):
            idx = [k for k, v in names.items() if v == m.group(1)]
            rows.append({"caso": tag, "hora": hora, "seccion": sec, "volcan": m.group(1), "vol_idx": idx[-1] if idx else "",
                         "v1": float(m.group(2)), "v2": float(m.group(3)), "match": ""}); continue
        if s.startswith("MATCH:") or s.startswith("NO MATCH:"):
            v = re.findall(NUM, s)
            hit = False
            for r in rows:
                if r["hora"] == hora and r["seccion"] == sec and r["vol_idx"] == v[0] and r["match"] == "":
                    r["match"] = int(s.startswith("MATCH:")); r["m_resto"] = " ".join(v[1:]); hit = True
            if not hit:
                rows.append({"caso": tag, "hora": hora, "seccion": sec, "volcan": names.get(v[0], ""), "vol_idx": v[0],
                             "v1": "", "v2": "", "match": int(s.startswith("MATCH:")), "m_resto": " ".join(v[1:])})
        if "LACK OF ACTIVITY" in s:
            rows.append({"caso": tag, "hora": hora, "seccion": sec, "volcan": "(eliminada por falta de actividad)", "vol_idx": "", "v1": "", "v2": "", "match": "", "m_resto": ""})
    for r in rows:
        f = recs.get((r["seccion"], r["vol_idx"]), [])
        r["n_obj"] = len(f)
        if f:
            r["max_final2"] = max(x[1] for x in f); r["max_final4"] = max(x[3] for x in f); r["sum_flag5"] = sum(x[4] for x in f)
    return rows

def main():
    files = sorted(glob.glob(os.path.join(sys.argv[1], "geocatASHOBJ.*.A?_I?_H?_S?.log")))
    if len(sys.argv) >= 6:
        files = [f for f in files if sys.argv[4] <= re.search(r"\.(\d{6})\.A[YN]_", os.path.basename(f)).group(1) <= sys.argv[5]]
    rows = []
    for f in files: rows += run(f, sys.argv[3])
    keys = ["caso", "hora", "seccion", "volcan", "vol_idx", "v1", "v2", "match", "m_resto", "n_obj", "max_final2", "max_final4", "sum_flag5"]
    with open(sys.argv[2], "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=keys); w.writeheader(); [w.writerow(r) for r in rows]
    print(sys.argv[3], len(files), "cuadros", len(rows), "renglones")
if __name__ == "__main__": main()
