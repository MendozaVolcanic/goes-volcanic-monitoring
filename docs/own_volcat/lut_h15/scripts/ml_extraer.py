r"""Etapa 2 de C3 (H15): pasa a npz las entradas y la verdad del caso de Mauna Loa (sin calcular nada).

Por qué un paso aparte: sólo venv_hdf4 lee HDF4 (pyhdf) y no tiene scipy. Aquí sólo se lee, se aplica la escala
de cada SDS (scaling_method 1 = entero * scale_factor + add_offset) y el relleno pasa a NaN. Igual que
mauna_loa_c2b/scripts/c2b_extraer.py, con las variables que pide la etapa 2.

Uso: D:\goes_notas\busqueda_2026-11-20\venv_hdf4\Scripts\python.exe -I ml_extraer.py <paquete> <salida>
"""
import glob
import os
import sys

import numpy as np
from pyhdf.SD import SD, SDC

sys.stdout.reconfigure(encoding="utf-8")
P = "vcat_ashdet_pix_2_7_10_11_13_14_15_"
VARS = {
    "geocatL1": ["pixel_latitude", "pixel_longitude", "pixel_solar_zenith_angle", "pixel_satellite_zenith_angle",
                 "pixel_surface_type", "channel_7_brightness_temperature", "channel_10_brightness_temperature",
                 "channel_11_brightness_temperature", "channel_14_brightness_temperature",
                 "channel_15_brightness_temperature"],
    "geocatRTM": ["channel_7_brightness_temperature_clear", "channel_10_brightness_temperature_clear",
                  "channel_11_brightness_temperature_clear", "channel_14_brightness_temperature_clear",
                  "channel_15_brightness_temperature_clear", "nwp_x_index", "nwp_y_index"],
    "geocatL2": [P + "ash_probability", P + "ash_probability_IR", P + "ash_probability_SW_IR",
                 P + "ash_probability_subset", "pixel_surface_type", "Ash_Group_Id_2d"],
    "geocatDIAGS1": [P + v for v in (
        "cloud_emissivity_ch14_tot", "cloud_beta_1112_tot", "cloud_beta_1112_opaque",
        "cloud_beta_1112_tot_multi_low", "cloud_beta_1112_tot_multi_mid", "cloud_beta_1112_tot_multi_nwp",
        "cloud_beta_8511_tot", "cloud_beta_8511_opaque", "cloud_beta_7311_tot", "lower_cloud_idx",
        "Ash_Object_Mask")] + ["vcat_ashdet_obj_2_7_10_11_13_14_15_Robust_Pixel_Flag"],
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


def main(paq, out):
    os.makedirs(out, exist_ok=True)
    ref = os.path.join(paq, "reference_data")
    # GFS: temperatura de tropopausa (para la nube negra del nivel B), dos tiempos
    g = {}
    for f in sorted(glob.glob(os.path.join(paq, "ancillary", "gfs_hdf", "gfs.*.hdf"))):
        sd = SD(f, SDC.READ)
        g[os.path.basename(f)] = np.asarray(sd.select("tropopause temperature")[:], "float32")
        sd.end()
    np.savez_compressed(os.path.join(out, "gfs_ttropo.npz"), **g)
    horas = sorted(os.path.basename(f).split(".")[-2]
                   for f in glob.glob(os.path.join(ref, "l1_data", "geocatL1.*.hdf")))
    for h in horas:
        d = {}
        for tipo, vs in VARS.items():
            f = glob.glob(os.path.join(ref, CARPETA[tipo], f"{tipo}.GOES-17.CONUS.2022332.{h}.hdf"))
            sd = SD(f[0], SDC.READ)
            for v in vs:
                d[f"{tipo}__{v.replace(P, '')}"] = leer(sd, v)
            if tipo == "geocatL1":
                for k in ("fk1_planck", "fk2_planck", "bc1_planck", "bc2_planck", "channel_wavenumber"):
                    d[k] = np.asarray(sd.select(k)[:], "float64").ravel()
                d["channel_central_wavelength"] = np.asarray(sd.select("channel_central_wavelength")[:], "float64")
            sd.end()
        np.savez_compressed(os.path.join(out, f"ml_{h}.npz"), **d)
        print(h, len(d), "variables", flush=True)
    print("gfs:", list(g))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
