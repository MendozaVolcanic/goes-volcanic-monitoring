r"""S29b, paso de datos: BTD (11,2 menos 12,3 µm) de todos los píxeles de la ventana en oct-nov 2024 (GOES-16), desde
la bajada de S25b (D:\goes_notas\s25\s25b_2024\l1b), y los atributos de geometría de un NetCDF de GOES-16 (2024) y uno
de GOES-19 (2025).

Por qué aparte: el cubo de S25b sólo guardó BT11, ACM y M1 del anillo; la zona del cráter (S25a) compara cada píxel
consigo mismo y necesita la BTD de sus 11 píxeles y de los controles regionales. Armar el cubo no calcula nada de la
zona: lee radiancias, las pasa a temperatura de brillo con el Planck de GOES-16 y guarda.

Uso: python -I s29b_cubo.py cubo | geometria
"""
import json
import os
import sys
import time
from datetime import datetime

import numpy as np

sys.stdout.reconfigure(encoding="utf-8")
AQUI = os.path.dirname(os.path.abspath(__file__))
OV = os.path.abspath(os.path.join(AQUI, "..", ".."))
RES = os.path.join(os.path.dirname(AQUI), "resultados")
sys.path.insert(0, os.path.join(OV, "s23_fondo_2025", "scripts"))
sys.path.insert(0, os.path.join(OV, "s25a_crater", "scripts"))
import s25a_medir as Z  # noqa: E402  (_leer: el mismo lector de S25a, sin cambios)

DATOS = r"D:\goes_notas\s25\s25b_2024"
TRAB = r"D:\goes_notas\s29\s29b"
T0 = datetime(2024, 9, 21)
ND = 62


def cubo():
    os.makedirs(TRAB, exist_ok=True)
    t = time.time()
    btd, acm, inst = Z._leer(DATOS, T0, ND)
    np.save(os.path.join(TRAB, "r24_btd.npy"), btd)
    np.save(os.path.join(TRAB, "r24_acm.npy"), acm)
    inst["segundos"] = round(time.time() - t)
    json.dump(inst, open(os.path.join(TRAB, "cubo_2024.json"), "w", encoding="utf-8"), indent=1)
    print("2024:", json.dumps(inst), flush=True)


def _atributos(bucket, dt):
    import h5py
    import s3fs
    fs = s3fs.S3FileSystem(anon=True)
    p = f"{bucket}/ABI-L1b-RadF/{dt:%Y}/{dt.timetuple().tm_yday:03d}/{dt:%H}/"
    k = [x for x in fs.ls(p) if "C14_" in x][0]
    out = {"archivo": k.split("/")[-1]}
    with fs.open(k, "rb", block_size=2**16, cache_type="readahead") as fo, h5py.File(fo, "r") as f:
        a = f["goes_imager_projection"].attrs
        for n in ("longitude_of_projection_origin", "perspective_point_height", "semi_major_axis", "semi_minor_axis"):
            out[n] = float(np.ravel(a[n])[0])
        for v in ("nominal_satellite_subpoint_lon", "nominal_satellite_subpoint_lat", "nominal_satellite_height"):
            if v in f:
                out[v] = float(np.ravel(f[v][()])[0])
        for v in ("x", "y"):
            d = f[v]
            out[f"{v}_scale_factor"] = float(np.ravel(d.attrs["scale_factor"])[0])
            out[f"{v}_add_offset"] = float(np.ravel(d.attrs["add_offset"])[0])
    return out


def geometria():
    g16 = _atributos("noaa-goes16", datetime(2024, 10, 15, 6))
    g19 = _atributos("noaa-goes19", datetime(2025, 10, 15, 6))
    os.makedirs(RES, exist_ok=True)
    json.dump({"goes16_2024": g16, "goes19_2025": g19}, open(os.path.join(RES, "geometria_atributos.json"), "w",
                                                             encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps({"goes16_2024": g16, "goes19_2025": g19}, indent=1))


if __name__ == "__main__":
    {"cubo": cubo, "geometria": geometria}[sys.argv[1]]()
