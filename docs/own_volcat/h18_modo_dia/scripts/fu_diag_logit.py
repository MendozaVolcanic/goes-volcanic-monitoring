r"""H18, diagnóstico POSTERIOR 3 (no decide): en píxeles de día con P_VOLCAT baja y no saturada (1e-12 < P < 0,5),
¿alguna de las 96 variantes reproduce el log-odds de VOLCAT exacto (|Δ logit| < 1e-3)? Es la única parte del caso
donde la probabilidad publicada sale de las tablas de píxel. Elige en la primera mitad, mide en la segunda.
"""
import json
import os
import sys

import numpy as np

sys.stdout.reconfigure(encoding="utf-8")
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import dia_motor as M  # noqa: E402
import fu_validar as V  # noqa: E402

comp = json.load(open(os.path.join(V.RES, "fu_comprobaciones.json")))
con_dia = [x["hora"] for x in comp["cuadros"] if x["n_dia"] > 0]


def lg(x):
    with np.errstate(all="ignore"):
        return np.log(x / (1 - x))


def evalua(horas):
    ent, ag, v, vir, sz, vz, ra, q = V.cargar(horas)
    PC = V.piezas_conv(ent, ag, sz, vz, ra)
    s = (v > 1e-12) & (v < 0.5) & ~ag
    r = {}
    for var in V.VARIANTES:
        L = M.logit_variante(PC[var[0]], *var[1:])
        d = np.abs(L[s] - lg(v[s]))
        r[V.nombre(var)] = {"n": int(s.sum()), "frac_exacta": float(np.mean(d < 1e-3)),
                            "frac_dentro_01": float(np.mean(d < 0.1)), "mediana_abs": float(np.median(d))}
    dir_ = np.abs(lg(vir[s]) - lg(v[s]))
    r["_P_IR_de_VOLCAT"] = {"n": int(s.sum()), "frac_exacta": float(np.mean(dir_ < 1e-3)),
                            "frac_dentro_01": float(np.mean(dir_ < 0.1)), "mediana_abs": float(np.nanmedian(dir_))}
    return r


r1 = evalua(con_dia[:13])
orden = sorted((k for k in r1 if not k.startswith("_")), key=lambda k: -r1[k]["frac_exacta"])
mejor = orden[0]
r2 = evalua(con_dia[13:])
out = {"eleccion_top10": {k: r1[k] for k in orden[:10]}, "referencia_IR_1a": r1["_P_IR_de_VOLCAT"],
       "mejor": mejor, "validacion_mejor": r2[mejor], "referencia_IR_2a": r2["_P_IR_de_VOLCAT"]}
json.dump(out, open(os.path.join(V.RES, "fu_diag_logit.json"), "w"), indent=1)
print(json.dumps(out, indent=1))
