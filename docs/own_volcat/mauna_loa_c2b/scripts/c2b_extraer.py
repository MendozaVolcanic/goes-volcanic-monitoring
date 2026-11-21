"""C2b, paso 1: pasa a npz las variables de los HDF4 del caso de Mauna Loa que usa la medicion (sin calcular nada).

Por que un paso aparte: el unico python con pyhdf que funciona (venv_hdf4) no tiene scipy ni PIL; la medicion
(c2b_medir.py) corre en Anaconda. Aqui solo se lee, se aplica la escala de cada SDS (scaling_method 1 = entero
* scale_factor + add_offset) y se ponen en NaN los valores de relleno.

Uso: <venv_hdf4>\\python -I c2b_extraer.py <carpeta reference_data> <carpeta salida npz>
"""
import os, sys, glob, json
sys.stdout.reconfigure(encoding="utf-8")
import numpy as np  # noqa: E402
from pyhdf.SD import SD, SDC  # noqa: E402

VARS = {
    "geocatL1": ["pixel_latitude", "pixel_longitude", "pixel_satellite_zenith_angle", "pixel_solar_zenith_angle",
                 "channel_7_brightness_temperature", "channel_14_brightness_temperature",
                 "channel_15_brightness_temperature"],
    "geocatRTM": ["channel_7_brightness_temperature_clear", "channel_14_brightness_temperature_clear",
                  "channel_15_brightness_temperature_clear", "channel_14_surface_emissivity", "nwp_x_index", "nwp_y_index"],
    "geocatL2": ["vcat_ashdet_pix_2_7_10_11_13_14_15_ash_probability", "vcat_ashdet_pix_2_7_10_11_13_14_15_ash_probability_IR",
                 "vcat_ashprop_13_14_15_16_cloud_emissivity_ch14_tot", "vcat_ashprop_13_14_15_16_ash_emissivity",
                 "vcat_ashprop_13_14_15_16_Ash_Beta", "Ash_Group_Id_2d"],
    "geocatDIAGS1": ["vcat_ashdet_pix_2_7_10_11_13_14_15_cloud_emissivity_ch14_tot",
                     "vcat_ashdet_pix_2_7_10_11_13_14_15_cloud_beta_1112_tot",
                     "vcat_ashdet_pix_2_7_10_11_13_14_15_Ash_Object_Mask",
                     "vcat_ashdet_obj_2_7_10_11_13_14_15_Bt14_Bias_Env_Per75",
                     "vcat_ashdet_obj_2_7_10_11_13_14_15_Robust_Pixel_Flag"],
}
CARPETA = {"geocatL1": "l1_data", "geocatRTM": "rtm_data", "geocatL2": "l2_data", "geocatDIAGS1": "diag_data"}
ATR_NAV = ["X_Offset_Nav", "Y_Offset_Nav", "X_Scale_Nav", "Y_Scale_Nav", "First_Line_Processed", "Last_Line_Processed",
           "First_Element_Processed", "Last_Element_Processed", "Projection_Longitude", "Subsatellite_Longitude",
           "Satellite_Height", "Original_NumberOfLines", "Original_NumberOfElements", "Percentage_Night"]


def leer(sd, nombre):
    ds = sd.select(nombre); a = np.asarray(ds[:]); at = ds.attributes()
    fill = at.get("_FillValue")
    malo = (a == fill) if fill is not None else np.zeros(a.shape, bool)
    a = a.astype("float64")
    if at.get("scaling_method", 0) == 1:
        a = a * at["scale_factor"] + at["add_offset"]
    a[malo] = np.nan
    return a.astype("float32")


def main(ref, out):
    os.makedirs(out, exist_ok=True)
    horas = sorted(os.path.basename(f).split(".")[-2] for f in glob.glob(os.path.join(ref, "l1_data", "geocatL1.*.hdf")))
    for h in horas:
        d, meta = {}, {}
        for tipo, vs in VARS.items():
            f = glob.glob(os.path.join(ref, CARPETA[tipo], f"{tipo}.GOES-17.CONUS.2022332.{h}.hdf"))
            if not f:
                print("falta", tipo, h); continue
            sd = SD(f[0], SDC.READ)
            for v in vs:
                d[f"{tipo}__{v}"] = leer(sd, v)
            if tipo == "geocatL1":
                at = sd.attributes()
                meta = {k: (float(at[k]) if not isinstance(at[k], str) else at[k]) for k in ATR_NAV}
                for k in ("fk1_planck", "fk2_planck", "bc1_planck", "bc2_planck"):
                    d[k] = np.asarray(sd.select(k)[:], "float64").ravel()
            sd.end()
        np.savez_compressed(os.path.join(out, f"c2b_{h}.npz"), meta=json.dumps(meta), **d)
        print(h, len(d), "variables", flush=True)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
