r"""Inventario de las variables LRC y de vecindad de geocatDIAGS1 (10 cuadros). Corre en venv_hdf4.

Uso: D:\goes_notas\busqueda_2026-11-20\venv_hdf4\Scripts\python.exe -I lrc_hdf.py
Escribe ../resultados/lrc_hdf.json (sólo conteos y percentiles, nada del paquete) y guarda los campos 2D en
D:\goes_cache\cielo_lrc\diags_extra_<hora>.npz para los scripts siguientes.
"""
import glob, json, os
import numpy as np
from pyhdf.SD import SD

B = r"D:\goes_cache\volcat_test_mauna_loa\ext\mauna-loa_g17-conus_nov2022_r20260709-volcat-code-ancil\reference_data\diag_data"
OUT = r"D:\goes_cache\cielo_lrc"
out = {}
for f in sorted(glob.glob(os.path.join(B, "geocatDIAGS1.*.hdf"))):
    h = os.path.basename(f).split(".")[-2]
    sd = SD(f)
    nombres = sorted(sd.datasets().keys())
    r = {"variables_con_lrc_en_el_nombre": [n for n in nombres if "lrc" in n.lower()]}
    guardar = {}
    for n in nombres:
        x = sd.select(n)[:].astype(float)
        v = x[(x > -998) & np.isfinite(x)]
        r[n.replace("vcat_ashdet_pix_2_7_10_11_13_14_15_", "pix_").replace("vcat_ashdet_obj_2_7_10_11_13_14_15_", "obj_")] = {
            "validos": int(v.size), "p5_p50_p95": [float(q) for q in np.percentile(v, [5, 50, 95])] if v.size else []}
        guardar[n.split("15_")[-1]] = x
    np.savez_compressed(os.path.join(OUT, f"diags_extra_{h}.npz"), **guardar)
    out[h] = r
    print(h, r["variables_con_lrc_en_el_nombre"], r.get("pix_ref_rat_nir_lrc"))
res = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "resultados", "lrc_hdf.json")
with open(res, "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=1)
print("ok", res)
