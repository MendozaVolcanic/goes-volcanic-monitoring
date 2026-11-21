r"""Extrae total_precipitable_water de geocatDIAGS1 (Mauna Loa, 10 cuadros) a npz en D:. Corre en venv_hdf4.

Por qué: la tabla de píxel de VOLCAT trae una corrección por vapor de agua de β(12/11)
(X_COND_BETA1112_TOT_H20_CORRECTION_FCT = −999; 1,5; 2,5 con INTERCEPT = 0; 0,05; 0,2), y el candidato a X es el
agua precipitable por píxel que VOLCAT guarda en su paso de píxel.
Uso: D:\goes_notas\busqueda_2026-11-20\venv_hdf4\Scripts\python.exe -I extraer_tpw.py
"""
import glob, os
import numpy as np
from pyhdf.SD import SD

SRC = r"D:\goes_cache\volcat_test_mauna_loa\ext\mauna-loa_g17-conus_nov2022_r20260709-volcat-code-ancil\reference_data\diag_data"
OUT = r"D:\goes_cache\cielo_sesgo\tpw.npz"
g = {}
for f in sorted(glob.glob(os.path.join(SRC, "geocatDIAGS1.*.hdf"))):
    sd = SD(f)
    nm = [k for k in sd.datasets() if k.endswith("total_precipitable_water")][0]
    x = sd.select(nm)
    a = x.attributes()
    d = np.asarray(x[:], "float64")
    if a.get("scaling_method", 0) == 1:
        fill = a.get("_FillValue")
        bad = d == fill
        d = d * a["scale_factor"] + a["add_offset"]
        d[bad] = np.nan
    else:
        d[d == a.get("_FillValue", -999.0)] = np.nan
    h = os.path.basename(f).split(".")[-2]
    g[h] = d
    print(h, nm, a.get("units"), np.nanpercentile(d, [1, 50, 99]))
np.savez_compressed(OUT, **g)
print("ok", OUT)
