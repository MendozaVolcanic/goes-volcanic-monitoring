r"""H18 etapa 1, diagnóstico POSTERIOR (no decide; la etapa ya dio NO VALIDA en fu_validar.py).

Pregunta: en los píxeles de día con ash_probability >= 0,5 donde la IR de VOLCAT da ~0, ¿qué valor tiene P, qué
dicen las otras probabilidades y banderas de VOLCAT y cuánto aportan nuestras tablas de día? Todos los cuadros con
día. Sólo números derivados.
"""
import glob
import json
import os
import sys

import numpy as np

sys.stdout.reconfigure(encoding="utf-8")
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import dia_motor as M  # noqa: E402
import fu_validar as V  # noqa: E402

NPZ = V.NPZ
comp = json.load(open(os.path.join(V.RES, "fu_comprobaciones.json")))
horas = [x["hora"] for x in comp["cuadros"] if x["n_dia"] > 0]
out = {}
alto, tot = [], []
for h in horas:
    d = np.load(os.path.join(NPZ, f"fu_{h}.npz"))
    g = lambda k: d[k].astype(float).ravel()  # noqa: E731
    sz = g("geocatL1__pixel_solar_zenith_angle")
    p = g("geocatL2__ash_probability"); pir = g("geocatL2__ash_probability_IR")
    psw = g("geocatL2__ash_probability_SW_IR"); psub = g("geocatL2__ash_probability_subset")
    dia = (sz < 85) & np.isfinite(p)
    a = dia & (p >= 0.5)
    b = dia & (p < 0.5)
    alto.append({"hora": h, "n_alto": int(a.sum()),
                 "p_alto_valores": [float(x) for x in np.unique(np.round(p[a], 4))[:8]],
                 "pir_alto_mediana": float(np.nanmedian(pir[a])) if a.any() else None,
                 "psw_alto_mediana": float(np.nanmedian(psw[a])) if a.any() else None,
                 "psub_alto_mediana": float(np.nanmedian(psub[a])) if a.any() else None,
                 "eps_alto_mediana": float(np.nanmedian(g("geocatDIAGS1__cloud_emissivity_ch14_tot")[a])) if a.any() else None,
                 "btd_alto_mediana": float(np.nanmedian((g("geocatL1__channel_14_brightness_temperature") - g("geocatL1__channel_15_brightness_temperature"))[a])) if a.any() else None,
                 "nrat_lrc_alto_mediana": float(np.nanmedian(g("geocatDIAGS1__ref_rat_nir_lrc")[a])) if a.any() else None,
                 "nrat_lrc_bajo_mediana": float(np.nanmedian(g("geocatDIAGS1__ref_rat_nir_lrc")[b])) if b.any() else None,
                 "objmask_alto": [int(x) for x in np.unique(g("geocatDIAGS1__Ash_Object_Mask")[a][np.isfinite(g("geocatDIAGS1__Ash_Object_Mask")[a])])][:6],
                 "grupo_alto_frac_con_id": float(np.mean(np.isfinite(g("geocatL2__Ash_Group_Id_2d")[a]) & (g("geocatL2__Ash_Group_Id_2d")[a] > 0))) if a.any() else None})
out["por_cuadro"] = alto
# Valores de P en todos los píxeles de día: ¿hay algo entre 0,05 y 0,95?
ps = []
for h in horas:
    d = np.load(os.path.join(NPZ, f"fu_{h}.npz"))
    sz = d["geocatL1__pixel_solar_zenith_angle"].ravel(); p = d["geocatL2__ash_probability"].ravel()
    ps.append(p[(sz < 85) & np.isfinite(p)])
ps = np.concatenate(ps)
out["hist_P_dia"] = {f"{a}-{b}": int(((ps >= a) & (ps < b)).sum()) for a, b in
                     ((0, 1e-6), (1e-6, 0.05), (0.05, 0.5), (0.5, 0.95), (0.95, 0.999), (0.999, 1.01))}
# Cuánto suben nuestras tablas de día en los píxeles altos (log10 de la razón, sin prior), todos los cuadros
ent, ag, v, vir, sz, vz, ra, q = V.cargar(horas)
P = M.piezas(ent, ag, M.scat_idx(M.angulo_dispersion(sz, vz, ra, "+")))
a = v >= 0.5
dec = lambda x: np.log10(np.e) * x  # noqa: E731
out["decadas_en_P_alto_mediana"] = {k: float(np.median(dec(P[k][a]))) for k in P}
out["decadas_en_P_bajo_mediana"] = {k: float(np.median(dec(P[k][~a]))) for k in P}
out["decadas_necesarias_para_P05"] = float(-dec(M.L0))
json.dump(out, open(os.path.join(V.RES, "fu_diag_posterior.json"), "w"), indent=1)
print(json.dumps({k: out[k] for k in ("hist_P_dia", "decadas_en_P_alto_mediana", "decadas_en_P_bajo_mediana", "decadas_necesarias_para_P05")}, indent=1))
for r in alto:
    if r["n_alto"]:
        print(r)
