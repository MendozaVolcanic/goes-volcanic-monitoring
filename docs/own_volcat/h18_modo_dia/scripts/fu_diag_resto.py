r"""H18, diagnóstico POSTERIOR 4 (no decide): en los píxeles de P baja donde la mejor variante de día
(NRAT sin LRC + β73 + β85 + VREF; sin BTD ni IR) NO es exacta, ¿qué cambio de UNA pieza los vuelve exactos?
Prueba: quitar cada tabla, quitar cada regla (R1, R2, R3), cambiar NRAT por NRAT_LRC en cada tabla β, agregar BTD.
Todos los cuadros con día; píxeles de tierra con 1e-12 < P_VOLCAT < 0,5.
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
horas = [x["hora"] for x in comp["cuadros"] if x["n_dia"] > 0]
ent, ag, v, vir, sz, vz, ra, q = V.cargar(horas)
s = (v > 1e-12) & (v < 0.5) & ~ag
ent = {k: a[s] for k, a in ent.items()}
ag, v, sz, vz, ra = ag[s], v[s], sz[s], vz[s], ra[s]
lv = np.log(v / (1 - v))
sc = M.scat_idx(M.angulo_dispersion(sz, vz, ra, "+"))
e, usa73, usa85 = M.preparar(ent)
e_sin_r2 = dict(ent)
g1, g2 = M.dia("NRAT"), M.dia("NRAT_LRC")
T = {}
for i, t in enumerate(g1["beta"]):
    T[f"beta{i}_NRAT"] = M.contrib(e, ag, t, sc)
    T[f"beta{i}_NRAT_sinR2"] = M.contrib(e_sin_r2, ag, t, sc)
for i, t in enumerate(g2["beta"]):
    T[f"beta{i}_LRC"] = M.contrib(e, ag, t, sc)
T["btd"] = M.contrib(e, ag, g1["btd"][0], sc)
T["d73"] = M.contrib(e, ag, M.DIA_73, sc)
T["d85a"] = M.contrib(e, ag, M.DIA_85[0], sc)
T["d85b"] = M.contrib(e, ag, M.DIA_85[1], sc)
T["vref"] = M.contrib(e, ag, M.DIA_VREF, sc)


def base(cambio=None):
    parts = {f"beta{i}": T[f"beta{i}_NRAT"] for i in range(4)}
    parts["d73"] = np.where(usa73, T["d73"], 0)
    parts["d85"] = np.where(usa85, T["d85a"] + T["d85b"], 0)
    parts["vref"] = T["vref"]
    if cambio:
        cambio(parts)
    return M.L0 + sum(parts.values())


L0 = base()
ex0 = np.abs(L0 - lv) < 1e-3
malos = ~ex0
cambios = {}
for k in ("beta0", "beta1", "beta2", "beta3", "d73", "d85", "vref"):
    cambios[f"quitar_{k}"] = (lambda kk: (lambda p: p.pop(kk)))(k)
for i in range(4):
    cambios[f"beta{i}_a_LRC"] = (lambda ii: (lambda p: p.__setitem__(f"beta{ii}", T[f"beta{ii}_LRC"])))(i)
    cambios[f"beta{i}_sinR2"] = (lambda ii: (lambda p: p.__setitem__(f"beta{ii}", T[f"beta{ii}_NRAT_sinR2"])))(i)
cambios["sin_R1"] = lambda p: p.__setitem__("d73", T["d73"])
cambios["sin_R3"] = lambda p: p.__setitem__("d85", T["d85a"] + T["d85b"])
cambios["mas_btd"] = lambda p: p.__setitem__("btd", T["btd"])
out = {"n": int(len(v)), "exactos_base": int(ex0.sum()), "no_exactos": int(malos.sum()), "cambios": {}}
for nom, f in cambios.items():
    L = base(f)
    ex = np.abs(L - lv) < 1e-3
    out["cambios"][nom] = {"arregla_de_los_malos": int((ex & malos).sum()), "rompe_de_los_buenos": int((~ex & ex0).sum())}
# Δ logit de los malos: valores más frecuentes
dd = np.round((lv - L0)[malos], 2)
vals, cnt = np.unique(dd, return_counts=True)
o = np.argsort(-cnt)[:10]
out["delta_logit_mas_frecuentes"] = [[float(vals[i]), int(cnt[i])] for i in o]
out["malos_por_tramo_eps"] = {f"{a}-{b}": [int(((ent['eps'] >= a) & (ent['eps'] < b) & malos).sum()),
                                           int(((ent['eps'] >= a) & (ent['eps'] < b)).sum())]
                              for a, b in ((0, 0.1), (0.1, 0.2), (0.2, 0.5), (0.5, 1.01))}
json.dump(out, open(os.path.join(V.RES, "fu_diag_resto.json"), "w"), indent=1)
print(json.dumps(out, indent=1))

# Agregado: ¿los no exactos son los píxeles dentro de un objeto de ceniza de VOLCAT (Ash_Group_Id_2d > 0)?
GR = []
for h in horas:
    d = np.load(os.path.join(V.NPZ, f"fu_{h}.npz"))
    szh = d["geocatL1__pixel_solar_zenith_angle"].ravel()
    vh = d["geocatL2__ash_probability"].ravel()
    sel = (szh < 85) & np.isfinite(vh)
    g = d["geocatL2__Ash_Group_Id_2d"].ravel()[sel].astype(float)
    GR.append(np.isfinite(g) & (g > 0))
GR = np.concatenate(GR)[s]
tab = {"objeto_y_no_exacto": int((GR & malos).sum()), "objeto_y_exacto": int((GR & ex0).sum()),
       "fuera_y_no_exacto": int((~GR & malos).sum()), "fuera_y_exacto": int((~GR & ex0).sum())}
out["objeto_vs_exactitud"] = tab
json.dump(out, open(os.path.join(V.RES, "fu_diag_resto.json"), "w"), indent=1)
print(tab)
