"""H19: lectura de los HDF4 de referencia de VOLCAT (Fuego, 03-06-2018).
Solo lee. La carpeta de datos se pasa por argumento; nada del paquete entra al repo."""
import os
import numpy as np
from pyhdf.SD import SD, SDC

HORAS = ["%02d%02d00" % (h, m) for h in range(14, 24) for m in (1, 16, 31, 46)]
PIX = "vcat_ashdet_pix_2_7_10_11_13_14_15_"
OBJ = "vcat_ashdet_obj_2_7_10_11_13_14_15_"
DB = "_Volcat_Alert_Volcano_Database_Oct8_2021_145852"

# Division de cuadros (ver criterio_2026-11-22.md)
ELECCION = ["171600", "173100", "174600", "180100", "181600", "183100", "184600",
            "190100", "191600", "193100", "194600", "200100", "201600"]
VALIDACION = ["203100", "204600", "210100", "211600", "213100", "214600", "220100",
              "221600", "223100", "224600", "230100", "231600", "233100"]


def ruta(ref, tipo, hora):
    sub = {"L2": "l2_data", "L2S1": "l2_data", "ASHOBJ": "l2_data", "HOTOBJ": "l2_data",
           "ICEOBJ": "l2_data", "DIAG": "diag_data", "DIAGS1": "diag_data",
           "L1": "l1_data", "RTM": "rtm_data"}[tipo]
    return os.path.join(ref, sub, "geocat%s.GOES-16.Full_Disk.2018154.%s.hdf" % (tipo, hora))


def leer(path, nombres=None, escalar=True):
    """Devuelve dict nombre -> array. Aplica scale_factor/add_offset y pone NaN en el relleno
    para variables escaladas o float."""
    sd = SD(path, SDC.READ)
    out = {}
    ds_all = sd.datasets()
    for n in (nombres or ds_all.keys()):
        if n not in ds_all:
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


def atributos(path, nombre):
    sd = SD(path, SDC.READ)
    at = dict(sd.select(nombre).attributes())
    sd.end()
    return at
