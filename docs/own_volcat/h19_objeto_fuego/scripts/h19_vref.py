"""H19: contribucion de la tabla publica EMISS14_TOT_VREF_DAY (emisividad total a 11 um x reflectancia
a 0,65 um) al log-odds de ceniza, por pixel. Reusa el lector de tablas de H15 (lut_h15/scripts/lut_volcat.py).
La tabla es densidad conjunta P(eps, ref2 | clase, angulo de dispersion); la contribucion es
log(densidad ceniza) - log(densidad nube)."""
import os
import sys
import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, "..", "..", "lut_h15", "scripts"))
import lut_volcat as LV  # noqa: E402

LV.EJES["ref2"] = (0.0, 10.0, 11)     # REF2_MIN/DB_PIX, 11 bins, en %
L0 = np.log(LV.PRIOR / (1 - LV.PRIOR))
_T = None


def tablas():
    global _T
    if _T is None:
        _T = LV.Tablas()
    return _T


def angulo(sz, vz, raz, conv="+"):
    s, v, r = np.radians(sz), np.radians(vz), np.radians(raz)
    sg = 1.0 if conv == "+" else -1.0
    c = -np.cos(s) * np.cos(v) + sg * np.sin(s) * np.sin(v) * np.cos(r)
    return np.degrees(np.arccos(np.clip(c, -1, 1)))


def vref(eps, ref2, agua, theta, base="EMISS14_TOT_VREF_DAY"):
    """Devuelve (contribucion en log-odds, mascara de uso, indice eps, indice ref2)."""
    ie, ue = LV.indice(eps, "eps", "b")
    ir, ur = LV.indice(ref2, "ref2", "b")
    sc = np.where(np.isfinite(theta), (theta >= 90).astype(int), -1)
    uso = ue & ur & (sc >= 0)
    out = np.zeros(len(eps))
    for sup, msk in (("WATER", agua), ("LAND", ~agua)):
        A, C = tablas().par(base, sup)
        A = A.reshape(A.shape[:3]); C = C.reshape(C.shape[:3])
        sel = msk & uso
        if sel.any():
            key = (ir[sel], ie[sel], sc[sel])
            out[sel] = np.log(A[key]) - np.log(C[key])
    return out, uso, ie, ir


def sig(L):
    return 1.0 / (1.0 + np.exp(-np.clip(L, -700, 700)))


def logit(p):
    p = np.clip(p, 1e-300, 1 - 1e-16)
    return np.log(p) - np.log1p(-p)
