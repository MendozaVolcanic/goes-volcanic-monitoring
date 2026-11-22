"""H20a: pasa a npz (fuera del repo) las grillas 601 x 601 del L2 de Fuego que se comparan con los
archivos de evento. No calcula acuerdos. Solo lee los HDF4 del paquete de SSEC.

Uso: venv_hdf4 python -I h20a_extraer.py REF SALIDA
  REF    = carpeta reference_data del paquete de Fuego
  SALIDA = carpeta fuera del repo (D:\\goes_notas\\s17\\h20a\\l2)
"""
import sys
import os
import numpy as np
from pyhdf.SD import SD, SDC

HORAS = ["%02d%02d00" % (h, m) for h in range(14, 24) for m in (1, 16, 31, 46)]
PIX = "vcat_ashdet_pix_2_7_10_11_13_14_15_"
OBJ = "vcat_ashdet_obj_2_7_10_11_13_14_15_"
TRK = "vcat_tracking_2_5_7_10_11_13_14_15_"
PROP = "vcat_ashprop_13_14_15_16_"
VCB = "vcat_vcbdet_9_13_ashprop_"
DB = "_Volcat_Alert_Volcano_Database_Oct8_2021_145852"

CAPAS = {
    "L2": ["pixel_latitude", "pixel_longitude", "pixel_solar_zenith_angle", "pixel_satellite_zenith_angle",
           "pixel_surface_type", "Ash_Group_Id_2d", "Ice_Group_Id_2d",
           PIX + "ash_probability", PIX + "ash_probability_IR", PIX + "ash_probability_SW_IR",
           PIX + "ash_probability_subset",
           PROP + "ash_top_height", PROP + "ash_mass_loading", PROP + "ash_effective_radius",
           PROP + "cloud_emissivity_ch14_tot", PROP + "Ash_Retv_Qf", PROP + "ash_emissivity",
           PROP + "Ash_Beta"],
    "L2S1": [TRK + "neighbor_range", TRK + "time_diff_images", TRK + "min_idx_in_ash",
             VCB + "cloud_wind_speed", VCB + "ash_probability", VCB + "pixel_time"],
    "DIAG": [TRK + "displacement_distance", TRK + "displacement_distance_in_ash",
             TRK + "ash_probability_IR_prev", TRK + "Btd1112_Time_Diff", TRK + "count_in_ash",
             TRK + "Dist_Diff_In_Out_Ash"],
    "DIAGS1": [PIX + "Ash_Object_Mask", PIX + "cloud_emissivity_ch14_tot", PIX + "cloud_beta_1112_tot",
               OBJ + "Robust_Pixel_Flag", OBJ + "History_Flag_Det_In", OBJ + "History_Flag_Det_Out"],
    "L1": ["channel_7_brightness_temperature", "channel_11_brightness_temperature",
           "channel_13_brightness_temperature", "channel_14_brightness_temperature",
           "channel_15_brightness_temperature", "channel_2_reflectance"],
}
SUB = {"L2": "l2_data", "L2S1": "l2_data", "ASHOBJ": "l2_data", "DIAG": "diag_data",
       "DIAGS1": "diag_data", "L1": "l1_data"}


def ruta(ref, tipo, hora):
    return os.path.join(ref, SUB[tipo], "geocat%s.GOES-16.Full_Disk.2018154.%s.hdf" % (tipo, hora))


def leer(path, nombres=None, escalar=True):
    """dict nombre -> array. Aplica scale_factor y add_offset y pone NaN en el relleno."""
    sd = SD(path, SDC.READ)
    out = {}
    todos = sd.datasets()
    for n in (nombres or todos.keys()):
        if n not in todos:
            print("  AVISO: falta", n, "en", os.path.basename(path), flush=True)
            continue
        ds = sd.select(n)
        a = np.asarray(ds.get())
        at = ds.attributes()
        if escalar:
            fill = at.get("_FillValue", None)
            sf = at.get("scale_factor", None)
            off = at.get("add_offset", 0.0)
            if a.dtype.kind == "f":
                a = a.astype("f8")
                a[(a <= -900) | ~np.isfinite(a)] = np.nan
                if fill is not None:
                    a[a == fill] = np.nan
            elif sf is not None and (sf != 1 or off != 0) and a.dtype.kind in "iu":
                m = (a == fill) if fill is not None else np.zeros(a.shape, bool)
                a = a.astype("f8") * sf + off
                a[m] = np.nan
        out[n] = a
    sd.end()
    return out


def corto(n):
    for pre, c in ((PIX, "PIX_"), (OBJ, "OBJ_"), (TRK, "TRK_"), (PROP, "PROP_"), (VCB, "VCB_")):
        if n.startswith(pre):
            return c + n[len(pre):]
    return n


def main(ref, out):
    os.makedirs(out, exist_ok=True)
    for h in HORAS:
        d = {}
        for tipo, nombres in CAPAS.items():
            D = leer(ruta(ref, tipo, h), nombres)
            for k, a in D.items():
                if a.ndim == 3:
                    a = a[:, :, 0]
                d[tipo + "__" + corto(k)] = a.astype(np.float32) if a.dtype.kind == "f" else a
        # objetos y grupos de geocatASHOBJ, sin escalar (enteros y float tal cual)
        A = leer(ruta(ref, "ASHOBJ", h), escalar=False)
        size = A["ASHOBJ_Object_Size"].astype(int)
        fin = np.cumsum(size)
        ini = fin - size
        x = A["ASHOBJ_Object_X_Index"].astype(int) - 1
        y = A["ASHOBJ_Object_Y_Index"].astype(int) - 1
        ido = np.full((601, 601), -1, np.int32)
        for k in range(len(size)):
            ido[y[ini[k]:fin[k]], x[ini[k]:fin[k]]] = k
        d["idA"] = ido
        for k, a in A.items():
            kk = k.replace("ASHOBJ_", "").replace(DB, "")
            if "Object_X_Index" in kk or "Object_Y_Index" in kk or "Vert" in kk:
                continue
            d["A__" + kk] = a
        np.savez_compressed(os.path.join(out, "l2_%s.npz" % h), **d)
        print(h, "variables", len(d), "objetos", len(size), flush=True)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
