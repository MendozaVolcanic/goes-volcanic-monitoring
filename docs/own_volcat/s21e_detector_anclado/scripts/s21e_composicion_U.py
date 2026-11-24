r"""S21e, informativo despues de medir: de que dias placebo sale U a las horas de los positivos, de los nacimientos
de VOLCAT y de los cuadros de VOLCAT y de pulsos que disparan (ventana, n y cuadros por dia). Sirve para ver si un
dia domina el umbral (criterio §3). Uso: python -I s21e_composicion_U.py
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import s21e_medir as S  # noqa: E402

M, E1, _ = S.cargar()
det = S.Detector(M.bt11, M.btd, E1)
S.preparar(det, S.POZO)
S.preparar(det, S.PLACEBO)
out = {}
for h in ["10:10", "11:20", "12:40", "13:00", "14:20", "14:50", "16:30", "19:20", "22:40", "23:30"]:
    u = S.umbral(det, S.slot(h))
    out[h] = {"U": None if u["U"] is None else round(u["U"], 3), "ventana_min": u["ventana_min"], "n": u["n"],
              "por_dia": u["por_dia"]}
    print(h, json.dumps(out[h]))
json.dump(out, open(os.path.join(S.RES, "composicion_U.json"), "w", encoding="utf-8"), indent=1)

# los cuatro S mas bajos de cada grupo que da U a las horas de los positivos (con dia y hora)
bajos = {}
for h in ["14:20", "14:30", "14:40", "14:50"]:
    u = S.umbral(det, S.slot(h))
    v = sorted((det.S(d, x)[0], S.fecha(d), S.hhmm(x)) for d, x in u["pool"])[:4]
    bajos[h] = [[round(a, 3), b, c] for a, b, c in v]
    print(h, "U", round(u["U"], 3), "mas bajos", bajos[h])
out["mas_bajos_positivos"] = bajos
json.dump(out, open(os.path.join(S.RES, "composicion_U.json"), "w", encoding="utf-8"), indent=1)
