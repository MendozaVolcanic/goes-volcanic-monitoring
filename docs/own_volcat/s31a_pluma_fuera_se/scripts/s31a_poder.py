r"""S31a, paso 2: piso del p y poder, SÓLO con VOLCAT (sin el detector), antes de escribir un umbral.

Por qué: con el día como unidad (S28b), el p más chico que puede dar un nulo es 1 / (número de colocaciones por días).
Si los días con pluma fuera del SE son pocos, ninguna prueba sobre el anillo puede decidir y no se inventa una.

Calcula, para el estrato de cuadros P con huella fuera de 90° a 180° (definición de S30b, inventario de
s31a_inventario.py):
1. el piso exacto de cada nulo por días (sign flip contra el rumbo SE habitual: 2^n; giro: 12^n; otro día fuera del SE:
   (D-1)^n), con n = días posibles;
2. el control positivo de S30b (oráculo: la tajada con más huella un cuadro antes, si no un cuadro después) sobre el
   mismo estrato, con los tres nulos: si ni VOLCAT contra sí mismo separa, el anillo tampoco podría;
3. la persistencia del rumbo: cuántos cuadros fuera del SE tienen el cuadro vecino también fuera del SE.

Uso: python -I -B s31a_poder.py
"""
import csv
import itertools
import json
import os
import sys

import numpy as np

sys.stdout.reconfigure(encoding="utf-8")
AQUI = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(os.path.dirname(AQUI), "resultados")
SE = (90.0, 180.0)
TAJ_SE = {3, 4, 5}          # tajadas cuyo centro (105°, 135°, 165°) está a ±30° del rumbo SE habitual (135°)
B, SEMILLA = 9999, 0


def leer():
    F = {}
    with open(os.path.join(RES, "s31a_inventario_volcat.csv"), encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["png"] != "ok":
                continue
            h, m = map(int, r["hora"].split(":"))
            s = h * 6 + m // 10
            F[(r["dia"], s)] = r
    return F


def secs(r):
    return {int(x) for x in r["tajadas"].split()} if r["tajadas"] else set()


def fuera(r):
    return r["rumbo"] not in ("", None) and not (SE[0] <= float(r["rumbo"]) <= SE[1])


def oraculo(F, dia, s):
    """Tajada con más huella en el cuadro vecino (s-1, si no s+1), como en S30b §4. None si no hay."""
    for t in (s - 1, s + 1):
        r = F.get((dia, t))
        if r is not None and r["huella_px"] not in ("", "0"):
            return int(r["tajada_moda"]) if r["tajada_moda"] != "" else None   # S30b: sin huella en el anillo no dispara
    return None


def main():
    F = leer()
    P = {k: r for k, r in F.items() if r["clase"] == "P"}
    estr = {k: r for k, r in P.items() if fuera(r)}
    dias_estr = sorted({d for d, _ in estr})
    # días en que el anillo tuvo algún P evaluado (publicado por S30b, INFORME §2 tabla por día): sólo el día, no el cuadro
    dias_anillo_s30b = ["2026-10-28", "2026-10-29", "2026-11-08", "2026-11-11"]
    n_max = len([d for d in dias_estr if d in dias_anillo_s30b])
    D = len(dias_estr)
    pisos = {}
    for n in range(1, n_max + 1):
        pisos[n] = {"sign_flip_contra_SE": 1 / 2 ** n, "giro_12^n": 1 / 12 ** n,
                    "otro_dia_fuera_SE_(D-1)^n": 1 / (D - 1) ** n}
    # persistencia del rumbo
    pers = []
    for (d, s), r in sorted(estr.items()):
        vec = [F.get((d, t)) for t in (s - 1, s + 1)]
        vec = [v for v in vec if v is not None and v["rumbo"] not in ("", None)]
        pers.append({"dia": d, "hora": r["hora"], "rumbo": float(r["rumbo"]), "px_anillo": int(r["huella_px_anillo"]),
                     "dist_max_km": float(r["dist_max_km"]),
                     "vecinos_rumbo": [float(v["rumbo"]) for v in vec],
                     "vecino_fuera_SE": any(fuera(v) for v in vec)})
    # oráculo sobre el estrato: coincide si su tajada está en las tajadas de la huella
    items = []
    for (d, s), r in sorted(estr.items()):
        k = oraculo(F, d, s)
        if k is None:
            continue
        items.append((d, secs(r), k))
    dias_o = sorted({d for d, _, _ in items})
    idx = {d: i for i, d in enumerate(dias_o)}
    T = sum(k in sc for _, sc, k in items)
    T_SE = sum(k in TAJ_SE for _, sc, k in items)
    # nulo de giro exacto
    tab = np.zeros((len(dias_o), 12), int)
    for d, sc, k in items:
        for j in range(12):
            tab[idx[d], j] += ((k - j) % 12) in sc
    tot = np.zeros(1, int)
    for i in range(len(dias_o)):
        tot = (tot[:, None] + tab[i][None, :]).ravel()
    pR = float((tot >= T).mean())
    # nulo de otro día fuera del SE
    rng = np.random.default_rng(SEMILLA)
    pool = {d: [secs(r) for (dd, _), r in estr.items() if dd == d] for d in dias_estr}
    cand = {d: [x for x in dias_estr if x != d] for d in dias_o}
    totD = np.zeros(B, int)
    for b in range(B):
        don = {d: cand[d][rng.integers(len(cand[d]))] for d in dias_o}
        totD[b] = sum(k in pool[don[d]][rng.integers(len(pool[don[d]]))] for d, _, k in items)
    pD = float((1 + (totD >= T).sum()) / (B + 1))
    # contra el SE habitual: sign flip por día de (coincide con su pluma - coincide con el SE habitual)
    dif = np.zeros(len(dias_o))
    for d, sc, k in items:
        dif[idx[d]] += int(k in sc) - int(k in TAJ_SE)
    obs = dif.sum()
    flips = [sum(s * x for s, x in zip(sg, dif)) for sg in itertools.product((1, -1), repeat=len(dias_o))]
    pSE = float(np.mean([f >= obs for f in flips]))
    out = {"estrato": "P con huella anclada fuera de 90° a 180° (S30b)", "cuadros": len(estr), "dias": dias_estr,
           "dias_con_anillo_evaluado_en_S30b": dias_anillo_s30b, "n_dias_max_para_el_anillo": n_max,
           "pisos_por_n": pisos, "persistencia": pers,
           "persistentes": sum(p["vecino_fuera_SE"] for p in pers),
           "oraculo": {"cuadros": len(items), "dias": dias_o, "coincide": T, "en_SE_habitual": T_SE,
                       "p_giro_exacto": pR, "p_otro_dia_fuera_SE": pD, "p_contra_SE_sign_flip": pSE,
                       "piso_sign_flip": 1 / 2 ** len(dias_o)}}
    json.dump(out, open(os.path.join(RES, "s31a_poder.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps({k: v for k, v in out.items() if k != "persistencia"}, ensure_ascii=False, indent=1))
    for p in pers:
        print(p)


if __name__ == "__main__":
    main()
