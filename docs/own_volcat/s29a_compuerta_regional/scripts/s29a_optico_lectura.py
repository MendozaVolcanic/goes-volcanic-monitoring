r"""S29a parte 1, lectura por la regla escrita antes (parte1_expectativas_2026-11-25.md §1):

1. Nieve 2026 contra 2025 en pares por fecha del año (±10 días), con escenas casi sin nube en la zona (nube < 0,10 y
   dato completo): diferencia de la fracción de nieve y de nieve oscurecida.
2. Nube en la zona en los días de disparo de la unión de cada vecina (S28a) con paso de Sentinel-2 o Landsat a menos de
   1 h de un cuadro que disparó.

Lee resultados/s29a_optico_escenas.csv y D:\goes_notas\s28\s28a\cuadros_<vecina>_<año>.csv.
Uso: python -I s29a_optico_lectura.py   (escribe resultados/s29a_optico_lectura.json)
"""
import csv
import json
import os
import sys
from datetime import datetime

import numpy as np

sys.stdout.reconfigure(encoding="utf-8")
AQUI = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(os.path.dirname(AQUI), "resultados")
CUADROS = r"D:\goes_notas\s28\s28a\cuadros_{}_{}.csv"
NUBE_MAX, PAR_DIAS, DIF, NUBE_DISPARO, VENTANA_MIN = 0.10, 10, 0.15, 0.20, 60


def escenas():
    with open(os.path.join(RES, "s29a_optico_escenas.csv"), encoding="utf-8") as f:
        filas = list(csv.DictReader(f))
    for r in filas:
        r["t"] = datetime.strptime(r["dia"] + r["hora"], "%Y-%m-%d%H:%M")
        for k in ("dato_zona", "nube_zona", "nieve", "nieve_sucia", "suelo", "nube_4a5km"):
            r[k] = float(r[k]) if r[k] not in ("", None) else np.nan
    return filas


def pares(filas, sitio):
    mx = max(r["dato_zona"] for r in filas if r["sitio"] == sitio)
    ok = [r for r in filas if r["sitio"] == sitio and r["nube_zona"] < NUBE_MAX and r["dato_zona"] >= 0.9 * mx]
    a25 = [r for r in ok if r["año"] == "2025"]
    a26 = [r for r in ok if r["año"] == "2026"]
    out = []
    for b in a26:
        doy = b["t"].timetuple().tm_yday
        cerca = [a for a in a25 if abs(a["t"].timetuple().tm_yday - doy) <= PAR_DIAS]
        for a in cerca:
            out.append({"2026": f"{b['dia']} {b['plataforma']}", "2025": f"{a['dia']} {a['plataforma']}",
                        "nieve_2026": b["nieve"], "nieve_2025": a["nieve"], "dif_nieve": round(b["nieve"] - a["nieve"], 4),
                        "dif_nieve_sucia": round(b["nieve_sucia"] - a["nieve_sucia"], 4)})
    d = np.array([p["dif_nieve"] for p in out])
    ds = np.array([p["dif_nieve_sucia"] for p in out])
    return {"pares": len(out), "escenas_2026": len(a26), "escenas_2025": len(a25),
            "dif_nieve_mediana": round(float(np.median(d)), 4) if len(d) else None,
            "pares_2026_con_menos_nieve_015": int((d <= -DIF).sum()), "pares_2026_con_mas_nieve_015": int((d >= DIF).sum()),
            "dif_nieve_sucia_mediana": round(float(np.median(ds)), 4) if len(ds) else None,
            "pares_2026_mas_sucia_015": int((ds >= DIF).sum()), "detalle": out}


def disparos(sitio, año):
    F = []
    with open(CUADROS.format(sitio, año), encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["F_u"] == "1":
                F.append((datetime.strptime(r["dia"] + r["hora"], "%Y-%m-%d%H:%M"), r["F_z"] == "1", r["F_a"] == "1"))
    return F


def nube_en_disparo(filas, sitio):
    out = []
    for año in ("2025", "2026"):
        F = disparos(sitio, año)
        for r in filas:
            if r["sitio"] != sitio or r["año"] != año:
                continue
            cerca = [(t, z, a) for t, z, a in F if abs((t - r["t"]).total_seconds()) <= VENTANA_MIN * 60]
            if cerca:
                out.append({"dia": r["dia"], "hora": r["hora"], "plataforma": r["plataforma"],
                            "nube_zona": r["nube_zona"], "nube_4a5km": r["nube_4a5km"],
                            "disparos_a_1h": len(cerca), "de_la_zona": sum(z for _, z, _ in cerca),
                            "del_anillo": sum(a for _, _, a in cerca),
                            "horas": sorted({t.strftime("%H:%M") for t, _, _ in cerca}),
                            "nube_ge_020": bool(r["nube_zona"] >= NUBE_DISPARO)})
    return out


def main():
    filas = escenas()
    out = {"regla": "parte1_expectativas_2026-11-25.md (c42190c)", "nieve": {}, "nube_en_disparo": {}}
    for s in ("antuco", "longavi", "chillan"):
        out["nieve"][s] = pares(filas, s)
        if s != "chillan":
            out["nube_en_disparo"][s] = nube_en_disparo(filas, s)
    json.dump(out, open(os.path.join(RES, "s29a_optico_lectura.json"), "w", encoding="utf-8"), ensure_ascii=False,
              indent=1)
    for s, v in out["nieve"].items():
        print(s, {k: v[k] for k in v if k != "detalle"})
    for s, v in out["nube_en_disparo"].items():
        for x in v:
            print(s, x)


if __name__ == "__main__":
    main()
