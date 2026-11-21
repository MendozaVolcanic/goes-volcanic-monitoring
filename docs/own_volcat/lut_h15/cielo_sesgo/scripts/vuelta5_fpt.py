r"""Vuelta 5, prueba 4: estado del plano focal (loop heat pipe de GOES-17) en las L1b C14 y C15 del paquete y
DQF en el dominio. Escribe ../resultados/vuelta5_fpt.json.
"""
import glob, json, os
import netCDF4
import numpy as np
IN = r"D:\goes_cache\volcat_test_mauna_loa\ext\mauna-loa_g17-conus_nov2022_r20260709-volcat-code-ancil\input"
out = {}
for ch in (13, 14, 15):
    for f in sorted(glob.glob(os.path.join(IN, f"OR_ABI-L1b-RadC-M6C{ch}_G17_*.nc"))):
        ds = netCDF4.Dataset(f)
        k = os.path.basename(f)[27:38]
        dqf = ds["DQF"][:].filled(255)
        out.setdefault(f"C{ch}", {})[k] = {
            "focal_plane_temperature_threshold_exceeded_count": int(ds["focal_plane_temperature_threshold_exceeded_count"][:]),
            "maximum_focal_plane_temperature": float(ds["maximum_focal_plane_temperature"][:]),
            "focal_plane_temperature_threshold_increasing": float(ds["focal_plane_temperature_threshold_increasing"][:]),
            "dqf_frac_no_cero": float(np.mean(dqf != 0))}
res = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "resultados", "vuelta5_fpt.json")
json.dump(out, open(res, "w", encoding="utf-8"), indent=1)
for ch, v in out.items():
    print(ch, list(v.values())[0], "...", list(v.values())[-1])
