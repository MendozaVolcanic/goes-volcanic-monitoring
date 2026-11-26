r"""F3 (S28b): barrido de fechas posteriores al 24-11-2026 23:50 UTC en el código, los resultados y los cachés de D:.

Por qué: las tres confirmaciones congeladas (S23b, S25a, S26a) valen sólo si nadie miró el detector en días nuevos.
Una fecha posterior al corte en un script, un resultado o un caché es la huella que habría que explicar.

Sólo lee. Escribe su salida en D:\goes_notas\s28\s28b\f3\barrido_fechas.json y la imprime resumida.
Uso: python -I f3_barrido_fechas.py
"""
import csv
import glob
import io
import json
import os
import re
import sys
from datetime import datetime, timezone

import numpy as np

sys.stdout.reconfigure(encoding="utf-8")
AQUI = os.path.dirname(os.path.abspath(__file__))
OV = os.path.abspath(os.path.join(AQUI, "..", "..", ".."))
SALIDA = r"D:\goes_notas\s28\s28b\f3\barrido_fechas.json"
CORTE = datetime(2026, 11, 25)              # primer día nuevo (el corte es 24-11 23:50 UTC)
CARPETAS = ["s23_fondo_2025", "s24_dia14_noche", "s25a_crater", "s25b_fondo_2024", "s26a_combinado",
            "s26b_noche_crater", "s27a_noche_causa", "s27b_altura_desfase", "s28a_vecinas"]
DEPENDENCIAS = ["s22a_detector_sectores", "s22b_pluma_vs_nubes"]
CACHES = [r"D:\goes_notas\s22", r"D:\goes_notas\s23", r"D:\goes_notas\s25", r"D:\goes_notas\s26",
          r"D:\goes_notas\s27", r"D:\goes_notas\s28\s28a"]

# patrones de fecha: (regex, función que devuelve datetime o None)
MES = {"11": 11, "12": 12}
PATRONES = [
    (re.compile(r"datetime\(\s*2026\s*,\s*(1[12])\s*,\s*(\d{1,2})"), lambda m: (2026, int(m[1]), int(m[2]))),
    (re.compile(r"2026[-/_]?(1[12])[-/_]?(\d{2})(?!\d)"), lambda m: (2026, int(m[1]), int(m[2]))),
    (re.compile(r"(?<!\d)(\d{1,2})[-/](1[12])[-/]2026"), lambda m: (2026, int(m[2]), int(m[1]))),
    (re.compile(r"2026(3[2-6]\d)(?=\d{4})"), lambda m: ("doy", int(m[1]))),      # año + día juliano + HHMM
    (re.compile(r"(?<!\d)(2[5-9]|30)\s*(?:nov|-11\b)", re.I), lambda m: (2026, 11, int(m[1]))),
]


def fecha_de(t):
    if t[0] == "doy":
        return datetime.strptime(f"2026{t[1]:03d}", "%Y%j")
    try:
        return datetime(*t)
    except ValueError:
        return None


def barrer_texto(texto):
    hits = []
    for n, linea in enumerate(texto.splitlines(), 1):
        for rx, f in PATRONES:
            for m in rx.finditer(linea):
                d = fecha_de(f(m))
                if d is not None and d >= CORTE:
                    hits.append({"linea": n, "fecha": f"{d:%Y-%m-%d}", "texto": linea.strip()[:160]})
    return hits


def codigo():
    out = {}
    for c in CARPETAS + DEPENDENCIAS:
        for f in sorted(glob.glob(os.path.join(OV, c, "scripts", "*.py"))):
            t = open(f, encoding="utf-8").read()
            h = barrer_texto(t)
            # además: toda lectura de carpeta por patrón, para revisarla a mano
            g = [{"linea": n, "texto": l.strip()[:160]} for n, l in enumerate(t.splitlines(), 1)
                 if re.search(r"glob\.glob|os\.listdir|os\.scandir|iglob|\.glob\(", l)]
            out[os.path.relpath(f, OV)] = {"fechas_nuevas": h, "lecturas_de_carpeta": g}
    return out


def resultados():
    out = {}
    for c in CARPETAS:
        for f in sorted(glob.glob(os.path.join(OV, c, "resultados", "*"))):
            t = open(f, encoding="utf-8", errors="replace").read()
            h = barrer_texto(t)
            if h:
                out[os.path.relpath(f, OV)] = {"n": len(h), "fechas": sorted({x["fecha"] for x in h}),
                                               "ejemplos": h[:5]}
    return out


RX_NOMBRE = re.compile(r"(2026)[-_]?(1[12])[-_]?(\d{2})")


def caches():
    out = {"archivos_con_fecha_nueva_en_el_nombre": {}, "csv_con_fecha_nueva": {}, "npy_forma": {},
           "max_fecha_por_carpeta": {}, "mtime_posterior_al_corte": []}
    corte_mtime = datetime(2026, 11, 25, 0, 0, tzinfo=timezone.utc).timestamp()   # 24-11 23:50 UTC redondeado
    for raiz in CACHES:
        for dirpath, _, files in os.walk(raiz):
            if dirpath.startswith(r"D:\goes_notas\s28\s28b"):
                continue
            fechas = []
            for fn in files:
                p = os.path.join(dirpath, fn)
                m = RX_NOMBRE.search(fn)
                if m:
                    d = fecha_de((2026, int(m[2]), int(m[3])))
                    if d:
                        fechas.append(d)
                        if d >= CORTE:
                            out["archivos_con_fecha_nueva_en_el_nombre"].setdefault(dirpath, []).append(fn)
                try:
                    st = os.stat(p)
                except OSError:
                    continue
                if st.st_mtime >= corte_mtime and not fn.endswith(".png"):
                    out["mtime_posterior_al_corte"].append(
                        [p, datetime.fromtimestamp(st.st_mtime, timezone.utc).strftime("%Y-%m-%d %H:%M:%S"), st.st_size])
                if fn.endswith(".csv") and st.st_size < 200 * 2**20:
                    t = open(p, encoding="utf-8", errors="replace").read()
                    h = barrer_texto(t)
                    if h:
                        out["csv_con_fecha_nueva"][p] = {"n": len(h), "fechas": sorted({x["fecha"] for x in h}),
                                                         "ejemplos": h[:3]}
                if fn.endswith(".json") and st.st_size < 50 * 2**20:
                    t = open(p, encoding="utf-8", errors="replace").read()
                    h = barrer_texto(t)
                    if h:
                        out["csv_con_fecha_nueva"][p] = {"n": len(h), "fechas": sorted({x["fecha"] for x in h}),
                                                         "ejemplos": h[:3]}
                if fn.endswith(".npy"):
                    try:
                        a = np.load(p, mmap_mode="r")
                        out["npy_forma"][p] = [list(a.shape), str(a.dtype)]
                    except Exception as e:  # noqa: BLE001
                        out["npy_forma"][p] = repr(e)[:80]
            if fechas:
                out["max_fecha_por_carpeta"][dirpath] = [f"{min(fechas):%Y-%m-%d}", f"{max(fechas):%Y-%m-%d}",
                                                         len(fechas)]
    return out


if __name__ == "__main__":
    os.makedirs(os.path.dirname(SALIDA), exist_ok=True)
    R = {"corte": "2026-11-24 23:50 UTC", "codigo": codigo(), "resultados": resultados(), "caches": caches()}
    json.dump(R, open(SALIDA, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("== código: scripts con fechas >= 25-11-2026")
    for f, v in R["codigo"].items():
        for h in v["fechas_nuevas"]:
            print(f"  {f}:{h['linea']}  {h['fecha']}  {h['texto']}")
    print("== código: lecturas de carpeta por patrón (revisar a mano)")
    for f, v in R["codigo"].items():
        for h in v["lecturas_de_carpeta"]:
            print(f"  {f}:{h['linea']}  {h['texto']}")
    print("== resultados con fechas >= 25-11-2026")
    for f, v in R["resultados"].items():
        print(f"  {f}: {v['n']} menciones, fechas {v['fechas']}")
    C = R["caches"]
    print("== cachés: archivos con fecha nueva en el nombre (cuenta por carpeta)")
    for d, fs in C["archivos_con_fecha_nueva_en_el_nombre"].items():
        print(f"  {d}: {len(fs)} ({fs[0]} ... {fs[-1]})")
    print("== cachés: csv/json con fechas nuevas")
    for p, v in C["csv_con_fecha_nueva"].items():
        print(f"  {p}: {v['n']} menciones, {v['fechas']}")
    print("== cachés: rango de fechas en nombres por carpeta")
    for d, v in C["max_fecha_por_carpeta"].items():
        print(f"  {d}: {v}")
    print("== cachés: npy (forma)")
    for p, v in C["npy_forma"].items():
        print(f"  {p}: {v}")
    print("== cachés: archivos no PNG con mtime >= 25-11-2026 00:00 UTC:", len(C["mtime_posterior_al_corte"]))
    for p, t, s in sorted(C["mtime_posterior_al_corte"], key=lambda x: x[1]):
        if not re.search(r"\\(l1b|acm)\\", p):
            print(f"  {t}  {s:>12}  {p}")
    n_npz = sum(1 for p, *_ in C["mtime_posterior_al_corte"] if re.search(r"\\(l1b|acm)\\", p))
    print("  (más", n_npz, "npz en carpetas l1b/acm)")
    print("salida:", SALIDA)
