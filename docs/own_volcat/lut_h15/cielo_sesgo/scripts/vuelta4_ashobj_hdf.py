r"""Vuelta 4: resumen por cuadro de los campos de sesgo de BT14 de geocatASHOBJ (10 cuadros). Corre en venv_hdf4.

Uso: D:\goes_notas\busqueda_2026-11-20\venv_hdf4\Scripts\python.exe -I vuelta4_ashobj_hdf.py
Escribe ../resultados/vuelta4_ashobj.json (sólo conteos derivados, nada del paquete).
"""
import glob, json, os
import numpy as np
from pyhdf.SD import SD

B = r"D:\goes_cache\volcat_test_mauna_loa\ext\mauna-loa_g17-conus_nov2022_r20260709-volcat-code-ancil\reference_data\l2_data"
CAMPOS = ["ASHOBJ_Mean_Bt14_Bias_Obj", "ASHOBJ_Maximum_Bt14_Bias_Obj", "ASHOBJ_Mean_Bt14_Bias_Env",
          "ASHOBJ_Maximum_Bt14_Bias_Env", "ASHOBJ_Btd1112_Bias_Per50", "ASHOBJ_Ref7_Bt14_Bias_Corr"]
out = {}
for f in sorted(glob.glob(os.path.join(B, "geocatASHOBJ.*.hdf"))):
    h = os.path.basename(f).split(".")[-2]
    sd = SD(f)
    n = len(sd.select("ASHOBJ_Total_Pixels")[:])
    r = {"n_objetos": int(n),
         "pixeles_en_objetos": int(np.sum(np.maximum(sd.select("ASHOBJ_Total_Pixels")[:], 0))),
         "objetos_con_bias_valid_pixels_gt0": int(np.sum(sd.select("ASHOBJ_Total_Bias_Valid_Pixels")[:] > 0)),
         "objetos_con_bias_eligible_pixels_gt0": int(np.sum(sd.select("ASHOBJ_Total_Bias_Eligible_Pixels")[:] > 0))}
    for c in CAMPOS:
        x = sd.select(c)[:]
        r[f"{c}_no_relleno"] = int(np.sum(x > -998))
    g = SD(os.path.join(B, os.path.basename(f).replace("geocatASHOBJ", "geocatL2"))).select("Ash_Group_Id_2d")[:]
    r["Ash_Group_Id_2d_pixeles_validos"] = int(np.sum(g >= 0))
    out[h] = r
    print(h, r)
res = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "resultados", "vuelta4_ashobj.json")
with open(res, "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=1)
print("ok", res)
