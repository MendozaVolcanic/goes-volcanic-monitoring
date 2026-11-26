r"""F2 (S28b): ¿el MIXTO de día de S28a depende de la semilla del remuestreo?

Por qué: el veredicto MIXTO de día exige el límite inferior del IC95 de R de Antuco > 1, y publicado da 1,04952 con
semilla 0. Un percentil 2,5 de 2.000 réplicas tiene error de Monte Carlo; si con otras semillas cae bajo 1 en una
fracción apreciable, el rótulo lo decide la semilla y no el dato.

Lee los CSV por cuadro de S28a (D:\goes_notas\s28\s28a\cuadros_<vecina>_<año>.csv), arma (disparos, evaluados) por
día con la misma regla (`s28a_medir.por_dia`, período día = 12:00 a 23:50 UTC) y repite `razon` con semillas 0 a 199.
Control: con semilla 0 tiene que reproducir el IC publicado.
Uso: python -I f2_s28a_semillas.py
"""
import csv
import json
import os
import sys
from collections import defaultdict
from datetime import date, timedelta

import numpy as np

sys.stdout.reconfigure(encoding="utf-8")
T = r"D:\goes_notas\s28\s28a"
N_BOOT = 2000
DIA = set(range(72, 144))
NOCHE = set(range(18, 54))


def por_dia(sitio, año, rango):
    c = defaultdict(lambda: [0, 0])
    dias = set()
    with open(os.path.join(T, f"cuadros_{sitio}_{año}.csv"), encoding="utf-8") as f:
        for r in csv.DictReader(f):
            h, m = map(int, r["hora"].split(":"))
            s = h * 6 + m // 10
            dias.add(r["dia"])
            if s in rango and r["ev_u"] == "1":
                c[r["dia"]][0] += int(r["F_u"])
                c[r["dia"]][1] += 1
    return c, dias


def razon(c25, c26, semilla):
    rng = np.random.default_rng(semilla)
    Rs = []
    for _ in range(N_BOOT):
        a = c25[rng.integers(0, len(c25), len(c25))].sum(0)
        b = c26[rng.integers(0, len(c26), len(c26))].sum(0)
        if a[1] and b[1] and a[0]:
            Rs.append((b[0] / b[1]) / (a[0] / a[1]))
    return np.percentile(Rs, [2.5, 97.5])


def main():
    out = {}
    for sitio in ("antuco", "longavi"):
        for per, rg in (("dia", DIA), ("noche", NOCHE)):
            arr = {}
            for año in ("2025", "2026"):
                c, dias = por_dia(sitio, año, rg)
                # s28a remuestrea TODOS los días de la ventana (62 en 2025, 65 en 2026), también los sin evaluados
                nd = 62 if año == "2025" else 65
                t0 = date(int(año), 9, 21)
                arr[año] = np.array([c[(t0 + timedelta(days=i)).isoformat()] for i in range(nd)], float)
            F25, E25 = arr["2025"].sum(0)
            F26, E26 = arr["2026"].sum(0)
            R = (F26 / E26) / (F25 / E25)
            los = [razon(arr["2025"], arr["2026"], s)[0] for s in range(200)]
            his = [razon(arr["2025"], arr["2026"], s)[1] for s in range(1)]
            out[f"{sitio}_{per}"] = {"2025": [int(F25), int(E25)], "2026": [int(F26), int(E26)], "R": round(R, 5),
                                     "IC_semilla0": [round(los[0], 5), round(his[0], 5)],
                                     "dias_2025": len(arr["2025"]), "dias_2026": len(arr["2026"]),
                                     "lo_min": round(min(los), 4), "lo_max": round(max(los), 4),
                                     "frac_semillas_lo_menor_que_1": round(float(np.mean(np.array(los) <= 1)), 3)}
            print(sitio, per, json.dumps(out[f"{sitio}_{per}"]), flush=True)
    json.dump(out, open(r"D:\goes_notas\s28\s28b\f2\s28a_semillas.json", "w", encoding="utf-8"), indent=1)


if __name__ == "__main__":
    main()
