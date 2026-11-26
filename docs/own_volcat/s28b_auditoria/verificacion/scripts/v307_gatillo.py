r"""V307: el gatillo cuenta cuadros P (20 en 2 días), y el veredicto exige 10 P EVALUADOS en 2 días. ¿Qué tan seguido el
gatillo se cumpliría con menos de 10 P evaluados o con P evaluados de un solo día (NO DECIDIBLE)?

No corre el detector. Usa sólo las tablas por día ya publicadas del desarrollo (días ya vistos, hasta el 14-11-2026):
  anillo (regla S23b, percentil 5): s23_fondo_2025/resultados/sensibilidad_costumbre_2026.json
  zona (S25a) y unión (S26a a p* 4,75): s26a_combinado/resultados/s26a_desarrollo.json  (zona a p*; evaluados no
  dependen del percentil)
Para cada día con P del desarrollo tomado como "primer día nuevo", acumula días en orden hasta que el gatillo se cumple
(>= 20 P en >= 2 días) y cuenta los P evaluados y sus días para cada regla.

Uso: python -I -B v307_gatillo.py
"""
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
AQUI = os.path.dirname(os.path.abspath(__file__))
OV = os.path.abspath(os.path.join(AQUI, "..", "..", ".."))
MIN_P, MIN_DIAS, MIN_EVAL = 20, 2, 10

an = json.load(open(os.path.join(OV, "s23_fondo_2025", "resultados", "sensibilidad_costumbre_2026.json"),
                    encoding="utf-8"))
de = json.load(open(os.path.join(OV, "s26a_combinado", "resultados", "s26a_desarrollo.json"), encoding="utf-8"))
tab = {}
for x in an["por_dia"]:
    tab[x["dia"]] = {"P": x["P"], "anillo": x["P_evaluados"]}
for x in de["por_dia"]:
    if x["P"]:
        tab.setdefault(x["dia"], {"P": x["P"]})
        tab[x["dia"]]["zona"] = x["zona"]["P_evaluados"]
        tab[x["dia"]]["union"] = x["union"]["P_evaluados"]
dias = sorted(tab)
print("día        P  eval_anillo  eval_zona  eval_unión")
for d in dias:
    print(d, f"{tab[d]['P']:3d} {tab[d].get('anillo', 0):6d} {tab[d].get('zona', 0):10d} {tab[d].get('union', 0):10d}")
tot = {k: sum(tab[d].get(k, 0) for d in dias) for k in ("P", "anillo", "zona", "union")}
print("total     ", tot, "fracción evaluada:", {k: round(tot[k] / tot["P"], 3) for k in ("anillo", "zona", "union")})
print()
print("primer día nuevo -> día en que se cumple el gatillo; P del gatillo; P evaluados (días) por regla; veredicto forzado")
nd = {"anillo": 0, "zona": 0, "union": 0}
n = 0
for i, d0 in enumerate(dias):
    P, dP, j = 0, 0, i
    while j < len(dias) and not (P >= MIN_P and dP >= MIN_DIAS):
        P += tab[dias[j]]["P"]
        dP += 1
        j += 1
    if not (P >= MIN_P and dP >= MIN_DIAS):
        print(d0, "-> el gatillo no se cumple con los días que quedan")
        continue
    n += 1
    fila = []
    for k in ("anillo", "zona", "union"):
        ev = sum(tab[x].get(k, 0) for x in dias[i:j])
        de_ = sum(1 for x in dias[i:j] if tab[x].get(k, 0))
        no = ev < MIN_EVAL or de_ < 2
        nd[k] += no
        fila.append(f"{k} {ev} ({de_} d){' NO DECIDIBLE' if no else ''}")
    print(d0, "->", dias[j - 1], f"; {P} P en {dP} días;", "; ".join(fila))
print()
print(f"arranques en que el gatillo se cumple: {n}; NO DECIDIBLE forzado: {nd}")
