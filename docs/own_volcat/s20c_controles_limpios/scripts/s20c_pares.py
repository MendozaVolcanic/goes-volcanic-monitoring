r"""S20c, paso 0 (antes del criterio, no mide nada): junta en una tabla los pares (positivo, control) que usaron las
pruebas pareadas viejas, leidos de sus salidas crudas en el repo, y anota si hay PNG de VOLCAT para el positivo.

Por que: las huellas del paso 2 y del VAAC de Londres no quedaron guardadas; antes de fijar el criterio hay que saber
cuantos positivos se pueden rehacer con el decodificador corregido de H29 (PNG en D:).
El parseo es el mismo que uso el conteo de MET-01 (contar.py del revisor, S20), aplicado a este checkout.

Salida: resultados\pares_originales.csv (prueba, pos, ctrl, png). Uso: python -I s20c_pares.py
"""
import csv
import os
import re
from datetime import datetime

import pandas as pd

AQUI = os.path.dirname(os.path.abspath(__file__))
OV = os.path.abspath(os.path.join(AQUI, "..", ".."))
RES = os.path.join(os.path.dirname(AQUI), "resultados")
PNG_DIRS = [r"D:\goes_cache\h13\png", r"D:\goes_notas\local_f3a7d295\h12_datos\extra\png_e2",
            r"D:\goes_notas\volcat_validacion_copia_2026-11-21\Chile_Central_2_km\frames",
            r"D:\goes_notas\local_f3a7d295\capa_volcat_union\frames_cache"]


def indice_png():
    idx = {}
    rx = re.compile(r"ABI\.(\d{4})-(\d{2})-(\d{2})[._](\d{2})-(\d{2})-\d{2}\.Ash_Height\.Chile_Central_2_km\.png$")
    rx2 = re.compile(r"(\d{4})-(\d{2})-(\d{2})_(\d{2})-(\d{2})-\d{2}\.png$")
    for d in PNG_DIRS:
        if not os.path.isdir(d):
            continue
        for f in os.listdir(d):
            if "_annot" in f:
                continue
            m = rx.search(f) or rx2.search(f)
            if m:
                t = datetime(*[int(x) for x in m.groups()])
                idx.setdefault(t, os.path.join(d, f))
    return idx


def pares():
    out = []
    for ln in open(os.path.join(OV, "pruebas_17_18nov", "resultados", "paso2_resultado.txt"), encoding="utf-8"):
        m = re.match(r"\s+(\d\d)-(\d\d) (\d\d):(\d\d) control dia (\d\d)", ln)
        if m:
            mo, d, h, mi, dc = map(int, m.groups())
            p = datetime(2026, mo, d, h, mi)
            out.append(("paso2", p, p.replace(day=dc)))
    for ln in open(os.path.join(OV, "h3_h7", "h3_resultado.txt"), encoding="utf-8"):
        m = re.match(r"caso \d (\d{8}_\d{4}) .*-> control (\d{4}-\d\d-\d\d) dBT11=\S+ K \[(\w+)\]", ln)
        if m and m.group(3) == "ok":
            p = datetime.strptime(m.group(1), "%Y%m%d_%H%M")
            c = datetime.strptime(m.group(2), "%Y-%m-%d")
            out.append(("H3", p, c.replace(hour=p.hour, minute=p.minute)))
    for ln in open(os.path.join(OV, "beta73", "beta73_resultado.txt"), encoding="utf-8"):
        m = re.match(r"[DN] (\d{8}_\d{4}) (\d{8}_\d{4}) [+-]", ln)
        if m:
            a, b = (datetime.strptime(x, "%Y%m%d_%H%M") for x in m.groups())
            out.append(("beta73", a, b))
    pp = pd.read_csv(os.path.join(OV, "vaac_londres", "resultados", "pares.csv"))
    for a, b in zip(pp.pos, pp.ctrl):
        if isinstance(b, str):
            out.append(("VAAC", datetime.strptime(a, "%Y-%m-%d %H:%M"), datetime.strptime(b, "%Y-%m-%d %H:%M")))
    ln = [x for x in open(os.path.join(OV, "temporal_h13", "resultados", "h13_resultado.txt"), encoding="utf-8")
          if x.startswith("  pares:")][0]
    for a, b in re.findall(r"(\d{8}_\d{4})->(\d{8}_\d{4})", ln):
        out.append(("H13", datetime.strptime(a, "%Y%m%d_%H%M"), datetime.strptime(b, "%Y%m%d_%H%M")))
    return out


if __name__ == "__main__":
    idx = indice_png()
    os.makedirs(RES, exist_ok=True)
    filas = pares()
    with open(os.path.join(RES, "pares_originales.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["prueba", "pos", "ctrl", "png"])
        for pr, p, c in filas:
            w.writerow([pr, f"{p:%Y-%m-%d %H:%M}", f"{c:%Y-%m-%d %H:%M}", idx.get(p, "")])
    df = pd.read_csv(os.path.join(RES, "pares_originales.csv"))
    df["hay_png"] = df.png.notna()
    print(df.groupby("prueba").agg(pares=("pos", "size"), con_png=("hay_png", "sum")))
    print("dias positivos:", sorted(set(df.pos.str[:10])))
    print("sin png:", df[~df.hay_png][["prueba", "pos"]].values.tolist())
