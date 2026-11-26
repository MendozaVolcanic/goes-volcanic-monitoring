r"""S31e, POST HOC (escrito después de ver la medida de s31e_medir.py; no decide nada).

1. Dónde y cuándo dispara el anillo T1 en 2026 (hasta el 24-11): la medida mostró que dispara en el 7,2 % de los
   cuadros N de VOLCAT contra 0,7 % del congelado, y hacia el W y NW. Se cuentan disparos por día, clase, mitad del día y
   tajada, en la tabla del anillo T1 de D:\goes_notas\s31\s31e\tabla_2026_T1.csv.
2. Cuánto debería caer la cola de 8 en el tramo de 4 a 15 km sin pluma: en los disparos de 2025, la fracción de píxeles
   válidos de la tajada del disparo que están a menos de 15 km (lo que daría un píxel cualquiera de la tajada, como el
   nulo G de S31c), contra la fracción observada en la cola, para el congelado y para T1.

Uso: python -I -B s31e_posthoc.py
"""
import csv
import json
import os
import sys
from collections import Counter, defaultdict

import numpy as np

sys.stdout.reconfigure(encoding="utf-8")
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import s31e_medir as E  # noqa: E402

S, B, M = E.S, E.B, E.M
CERCA_A = E.DISTA < 15.0


def parte1():
    filas = list(csv.DictReader(open(os.path.join(E.TRAB, "tabla_2026_T1.csv"), encoding="utf-8")))
    fil0 = {(r["dia"], r["hora"]): r for r in csv.DictReader(open(S30_TABLA(), encoding="utf-8"))}
    disp = [r for r in filas if r["F_a"] == "1"]
    por_dia = defaultdict(Counter)
    for r in disp:
        c = r["clase"] or "sin_clase"
        por_dia[r["dia"]][c] += 1
        por_dia[r["dia"]]["noche" if int(r["hora"][:2]) < 12 else "dia"] += 1
    taj = Counter(int(r["k_a"]) for r in disp)
    ev = Counter((r["clase"] or "sin_clase") for r in filas if r["ev_a"] == "1")
    fc = Counter((r["clase"] or "sin_clase") for r in disp)
    cong = Counter((r["clase"] or "sin_clase") for r in fil0.values() if r["F_a"] == "1")
    oeste = [r for r in disp if int(r["k_a"]) in (7, 8, 9, 10, 11)]
    return {"disparos": len(disp), "por_clase": dict(fc), "evaluados_por_clase": dict(ev),
            "congelado_por_clase": dict(cong), "tajadas": [taj[k] for k in range(12)],
            "dias_con_disparo": len(por_dia), "por_dia": {d: dict(c) for d, c in sorted(por_dia.items())},
            "W_NW_210a360": {"n": len(oeste), "dias": len({r["dia"] for r in oeste}),
                             "noche": sum(int(r["hora"][:2]) < 12 for r in oeste)}}


def S30_TABLA():
    return E.S30.TABLA


def parte2():
    est26 = np.load(E.A26.ESTAT26)
    D = S.Detector(ref="2025", con_blanco=False)
    del est26
    z = np.load(os.path.join(E.TRAB, "S_K_T1.npz"))
    out = {}
    for var in ("ID", "T1"):
        if var == "ID":
            SR, KR, p = D.SR, D.KR, E.P_CONG
        else:
            SR, KR, p = z["S25"], z["K25"], 5.0
        FE = [S.disparos(SR, KR, d, E.umbral(D, SR, p, d)) for d in D.DIASR]
        esp, obs_n, n = [], 0, 0
        for d, s in E.lista_disparos(FE):
            k = int(KR[d, s])
            r = D.mmR[d, s] - D.base(d)[s]
            val = np.isfinite(r) & (M.SEC == k)
            esp.append(CERCA_A[val].mean())
            if var == "ID":
                c = E.cola(r, k)
                obs_n += int((E.C31.DISTF[c] < 15).sum())
                n += len(c)
        out[var] = {"disparos": len(esp), "frac_cerca_esperada_pixel_cualquiera": round(float(np.mean(esp)), 4)}
        if var == "ID":
            out[var]["frac_cerca_cola_observada"] = round(obs_n / n, 4)
    return out


if __name__ == "__main__":
    res = {"rotulo": "POST HOC: escrito después de ver s31e_resultado.json; no decide",
           "parte1_T1_2026": parte1()}
    print(json.dumps(res, ensure_ascii=False, indent=1), flush=True)
    res["parte2_cola_cercana_2025"] = parte2()
    print(json.dumps(res["parte2_cola_cercana_2025"], ensure_ascii=False, indent=1))
    json.dump(res, open(os.path.join(E.RES, "s31e_posthoc.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1,
              default=E._json)
