"""H19: utilidades comunes para los scripts de analisis sobre los npz (Python normal, sin pyhdf)."""
import os
import sys
import numpy as np

PIX = "p__vcat_ashdet_pix_2_7_10_11_13_14_15_"
OBJ = "p__vcat_ashdet_obj_2_7_10_11_13_14_15_"
TRK = "p__vcat_tracking_2_5_7_10_11_13_14_15_"
VCB = "p__vcat_vcbdet_9_13_ashprop_"
PROP = "p__vcat_ashprop_13_14_15_16_"

HORAS = ["%02d%02d00" % (h, m) for h in range(14, 24) for m in (1, 16, 31, 46)]
ELECCION = HORAS[13:26]      # 17:16 a 20:16
VALIDACION = HORAS[26:39]    # 20:31 a 23:31
SIN_EVENTO = HORAS[:13] + HORAS[39:]


def guardia(horas, argv=None):
    argv = sys.argv if argv is None else argv
    if any(h in VALIDACION for h in horas) and "--validacion" not in argv:
        sys.exit("bloque de validacion: no se abre antes de congelar la regla (usar --validacion despues)")


def cargar(npz_dir, h):
    z = np.load(os.path.join(npz_dir, "h19_%s.npz" % h))
    return {k: z[k] for k in z.files}


def f(d, k):
    a = d[k].astype("f8")
    a[(a <= -900) | ~np.isfinite(a)] = np.nan
    return a
