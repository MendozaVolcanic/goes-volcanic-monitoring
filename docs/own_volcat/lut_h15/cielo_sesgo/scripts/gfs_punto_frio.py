r"""Punto más frío del perfil de temperatura del GFS del paquete Mauna Loa (variante N1). Corre en venv_hdf4.

Uso: D:\goes_notas\busqueda_2026-11-20\venv_hdf4\Scripts\python.exe -I gfs_punto_frio.py
Escribe D:\goes_cache\lut_h15\cielo_sesgo\gfs_punto_frio.npz (una grilla 361 × 720 por archivo GFS).
"""
import glob, os
import numpy as np
from pyhdf.SD import SD

SRC = r"D:\goes_cache\volcat_test_mauna_loa\ext\mauna-loa_g17-conus_nov2022_r20260709-volcat-code-ancil\ancillary\gfs_hdf"
OUT = r"D:\goes_cache\lut_h15\cielo_sesgo\gfs_punto_frio.npz"
g = {}
for f in sorted(glob.glob(os.path.join(SRC, "gfs.*.hdf"))):
    sd = SD(f)
    T = np.asarray(sd.select("temperature")[:], "float32")   # (361, 720, 26)
    g[os.path.basename(f)] = T.min(axis=-1)
    print(os.path.basename(f), T.shape)
np.savez_compressed(OUT, **g)
print("ok", OUT)
