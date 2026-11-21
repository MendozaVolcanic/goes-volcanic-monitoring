r"""Vuelta 4: aplica `criterio_vuelta4_sesgo_objeto_2026-11-21.md` (commit b0b519e). Por cuadro (10): fracción de
píxeles tenues (0,05 <= ε < 0,3) dentro de objeto (`Ash_Object_Mask` > 0) y mediana del desfase implícito de C14
(vuelta 3) dentro y fuera de objeto. Junta con vuelta4_ashobj.json (venv_hdf4) y decide.
Uso: python -I vuelta4_sesgo_objeto.py
"""
import json, os, sys
import numpy as np
sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import vuelta3_eps11 as V3  # noqa: E402
CS = V3.CS
RES = CS.RES
obj = json.load(open(os.path.join(RES, "vuelta4_ashobj.json"), encoding="utf-8"))
out = {"criterio": "docs/own_volcat/lut_h15/cielo_sesgo/criterio_vuelta4_sesgo_objeto_2026-11-21.md (commit b0b519e)",
       "por_cuadro": {}}
T_in, T_out, N_thin, N_in = [], [], 0, 0
for h in CS.E.HORAS:
    c = CS.Cuadro(h)
    X = V3.por_cuadro(c)
    om = np.asarray(c.d["geocatDIAGS1__Ash_Object_Mask"], float).ravel()
    thin = np.isfinite(X["ev"]) & (X["ev"] >= 0.05) & (X["ev"] < 0.3) & np.isfinite(X["d14"])
    inn = thin & (om > 0)
    out_ = thin & ~(om > 0)
    r = {"pixeles_tenues": int(thin.sum()), "tenues_en_objeto": int(inn.sum()),
         "frac_tenues_en_objeto": float(inn.sum() / thin.sum()),
         "d14_mediana_en_objeto": float(np.median(X["d14"][inn])) if inn.any() else None,
         "d14_mediana_fuera": float(np.median(X["d14"][out_])),
         **obj[h]}
    out["por_cuadro"][h] = r
    N_thin += thin.sum(); N_in += inn.sum()
    T_in.append(X["d14"][inn]); T_out.append(X["d14"][out_])
    print(h, r["pixeles_tenues"], r["tenues_en_objeto"], round(r["d14_mediana_fuera"], 2), r["d14_mediana_en_objeto"], flush=True)
ti, to = np.concatenate(T_in), np.concatenate(T_out)
cond_a = all(v["objetos_con_bias_valid_pixels_gt0"] == 0 and v["ASHOBJ_Mean_Bt14_Bias_Env_no_relleno"] == 0
             for v in out["por_cuadro"].values())
frac = float(N_in / N_thin)
med_fuera = float(np.median(to))
cond_b = frac < 0.10 and med_fuera <= -0.5
out["total"] = {"frac_tenues_en_objeto": frac, "d14_mediana_fuera": med_fuera,
                "d14_mediana_en_objeto": float(np.median(ti)) if len(ti) else None, "n_en_objeto": int(len(ti)),
                "n_fuera": int(len(to))}
out["condicion_a_ningun_objeto_con_sesgo_BT14"] = bool(cond_a)
out["condicion_b_desfase_fuera_de_objetos"] = bool(cond_b)
out["hipotesis_descartada"] = bool(cond_a or cond_b)
with open(os.path.join(RES, "vuelta4_sesgo_objeto.json"), "w", encoding="utf-8") as f:
    json.dump(out, f, indent=1, ensure_ascii=False)
print(json.dumps({k: out[k] for k in ("total", "condicion_a_ningun_objeto_con_sesgo_BT14",
                                      "condicion_b_desfase_fuera_de_objetos", "hipotesis_descartada")}, indent=1))
