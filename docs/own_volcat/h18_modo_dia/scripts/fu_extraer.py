r"""H18 etapa 1: pasa a npz las entradas y la verdad del caso de día de Fuego (GOES-16, 03-06-2018), sin calcular nada.

Por qué un paso aparte: sólo venv_hdf4 lee HDF4 (pyhdf). Igual que lut_h15/scripts/ml_extraer.py (Mauna Loa), con
las variables de día que pide el criterio: reflectancias de los canales 2 (0,65 µm) y 7 (3,9 µm), ángulo azimutal
relativo, `ref_rat_nir_lrc` y las cuatro probabilidades de geocatL2. Relleno a NaN, escala aplicada.

Uso: D:\goes_notas\busqueda_2026-11-20\venv_hdf4\Scripts\python.exe -I fu_extraer.py <reference_data> <salida>
Salida fuera del repo (datos de SSEC).
"""
import glob
import os
import sys

import numpy as np
from pyhdf.SD import SD, SDC

sys.stdout.reconfigure(encoding="utf-8")
P = "vcat_ashdet_pix_2_7_10_11_13_14_15_"
GEO = ["pixel_latitude", "pixel_longitude", "pixel_solar_zenith_angle", "pixel_satellite_zenith_angle",
       "pixel_relative_azimuth_angle", "pixel_surface_type", "pixel_ecosystem_type"]
VARS = {
    "geocatL1": GEO + ["channel_2_reflectance", "channel_7_reflectance", "channel_7_emissivity"]
    + [f"channel_{c}_brightness_temperature" for c in (7, 10, 11, 14, 15)],
    "geocatRTM": [f"channel_{c}_brightness_temperature_clear" for c in (7, 10, 11, 14, 15)]
    + ["channel_14_surface_emissivity", "nwp_x_index", "nwp_y_index"],
    "geocatL2": [P + "ash_probability", P + "ash_probability_IR", P + "ash_probability_SW_IR",
                 P + "ash_probability_subset", "Ash_Group_Id_2d"],
    "geocatDIAGS1": [P + v for v in (
        "cloud_emissivity_ch14_tot", "cloud_beta_1112_tot", "cloud_beta_1112_opaque",
        "cloud_beta_1112_tot_multi_low", "cloud_beta_1112_tot_multi_mid", "cloud_beta_1112_tot_multi_nwp",
        "cloud_beta_8511_tot", "cloud_beta_8511_opaque", "cloud_beta_7311_tot", "lower_cloud_idx",
        "ref_rat_nir_lrc", "total_precipitable_water", "Ash_Object_Mask")],
}
CARPETA = {"geocatL1": "l1_data", "geocatRTM": "rtm_data", "geocatL2": "l2_data", "geocatDIAGS1": "diag_data"}


def leer(sd, nombre):
    ds = sd.select(nombre)
    a = np.asarray(ds[:])
    at = ds.attributes()
    fill = at.get("_FillValue")
    malo = (a == fill) if fill is not None else np.zeros(a.shape, bool)
    a = a.astype("float64")
    if at.get("scaling_method", 0) == 1:
        a = a * at["scale_factor"] + at["add_offset"]
    a[malo] = np.nan
    return a.astype("float32")


def main(ref, out):
    os.makedirs(out, exist_ok=True)
    horas = sorted(os.path.basename(f).split(".")[-2]
                   for f in glob.glob(os.path.join(ref, "l1_data", "geocatL1.*.hdf")))
    for h in horas:
        d = {}
        for tipo, vs in VARS.items():
            f = glob.glob(os.path.join(ref, CARPETA[tipo], f"{tipo}.GOES-16.Full_Disk.2018154.{h}.hdf"))
            if not f:
                print("falta", tipo, h)
                continue
            sd = SD(f[0], SDC.READ)
            for v in vs:
                d[f"{tipo}__{v.replace(P, '')}"] = leer(sd, v)
            if tipo == "geocatL1":
                for k in ("fk1_planck", "fk2_planck", "bc1_planck", "bc2_planck", "channel_wavenumber"):
                    d[k] = np.asarray(sd.select(k)[:], "float64").ravel()
            sd.end()
        np.savez_compressed(os.path.join(out, f"fu_{h}.npz"), **d)
        print(h, len(d), "variables", flush=True)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
