r"""H18, diagnóstico POSTERIOR 2 (no decide): ¿fuera de la pluma, la P de día de VOLCAT es exactamente su P IR?

Si lo es, en este caso VOLCAT no aplica tablas de día en su probabilidad de píxel y la pluma recibe P alta por otra
vía (objeto o columna convectiva), y las tablas de día no se pueden validar con él. Mide, en píxeles de día:
igualdad exacta (|Δ logit| < 1e-3) entre P y P_IR, por clase de P, y la relación con ash_probability_subset.
"""
import glob
import json
import os
import sys

import numpy as np

sys.stdout.reconfigure(encoding="utf-8")
NPZ = r"D:\goes_notas\s16\modo_dia\npz"
RES = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "resultados")


def lg(x):
    x = np.clip(x, 1e-15, 1 - 1e-15)
    return np.log(x / (1 - x))


P, PIR, PSUB, GR, SZ = [], [], [], [], []
for f in sorted(glob.glob(os.path.join(NPZ, "fu_*.npz"))):
    d = np.load(f)
    sz = d["geocatL1__pixel_solar_zenith_angle"].ravel().astype(float)
    p = d["geocatL2__ash_probability"].ravel().astype(float)
    s = np.isfinite(p) & np.isfinite(sz)
    P.append(p[s]); SZ.append(sz[s])
    PIR.append(d["geocatL2__ash_probability_IR"].ravel()[s].astype(float))
    PSUB.append(d["geocatL2__ash_probability_subset"].ravel()[s].astype(float))
    g = d["geocatL2__Ash_Group_Id_2d"].ravel()[s].astype(float)
    GR.append(np.isfinite(g) & (g > 0))
P, PIR, PSUB, GR, SZ = map(np.concatenate, (P, PIR, PSUB, GR, SZ))
out = {}
for reg, m in (("dia", SZ < 85), ("terminador_85_91", (SZ >= 85) & (SZ < 91)), ("noche", SZ >= 91)):
    ok = m & np.isfinite(PIR)
    ex = np.abs(lg(P) - lg(PIR)) < 1e-3
    r = {"n": int(ok.sum())}
    for nom, c in (("P_lt_05", P < 0.5), ("P_ge_05", P >= 0.5)):
        s = ok & c
        r[nom] = {"n": int(s.sum()), "frac_P_igual_PIR": float(np.mean(ex[s])) if s.any() else None,
                  "frac_en_objeto": float(np.mean(GR[s])) if s.any() else None,
                  "frac_P_igual_Psub": float(np.mean(np.abs(lg(P[s]) - lg(PSUB[s])) < 1e-3)) if s.any() else None}
    out[reg] = r
json.dump(out, open(os.path.join(RES, "fu_diag_igualdad.json"), "w"), indent=1)
print(json.dumps(out, indent=1))
