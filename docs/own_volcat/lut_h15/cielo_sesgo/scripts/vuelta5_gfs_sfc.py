r"""Vuelta 5: temperatura de superficie y TPW del GFS del paquete (2 tiempos) a npz en D:. Corre en venv_hdf4.
Uso: D:\goes_notas\busqueda_2026-11-20\venv_hdf4\Scripts\python.exe -I vuelta5_gfs_sfc.py
"""
import glob, os
import numpy as np
from pyhdf.SD import SD
SRC = r"D:\goes_cache\volcat_test_mauna_loa\ext\mauna-loa_g17-conus_nov2022_r20260709-volcat-code-ancil\ancillary\gfs_hdf"
g = {}
for f in sorted(glob.glob(os.path.join(SRC, "gfs.*.hdf"))):
    sd = SD(f); b = os.path.basename(f)
    g[b + "|tsfc"] = np.asarray(sd.select("surface temperature")[:], "float32")
    g[b + "|tpw"] = np.asarray(sd.select("total precipitable water")[:], "float32")
np.savez_compressed(r"D:\goes_cache\cielo_sesgo\gfs_sfc.npz", **g)
print("ok", list(g))
