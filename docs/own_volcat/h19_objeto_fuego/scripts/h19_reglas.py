"""H19: reglas candidatas en forma de funciones, usadas igual en eleccion, validacion y placebos.

Regla de pixel (nivel 1): dentro de un grupo, P publicada alta si el pixel es "oscuro y opaco":
    emisividad total a 11 um >= EPS_MIN  y  REF_MIN <= reflectancia a 0,65 um < REF_MAX.
EPS_MIN = 0,90 es el borde del ultimo bin de emisividad de la tabla publica de pixel de VOLCAT.
REF_MIN = 10 y REF_MAX = 50 son los atributos DARK_PIXEL_REF2_MIN y DARK_PIXEL_REF2_MAX de esa tabla.

Reglas de pertenencia (nivel 2):
    nube convectiva volcanica en t = objeto de geocatICEOBJ con mas pixeles sobre el grupo de t-1 (si hay solape);
    grupo de ceniza en t = objetos de geocatASHOBJ que tocan (vecindad de 8) el objeto de nube convectiva."""
import numpy as np
from scipy import ndimage as ndi
from h19_comun import f, PIX

EPS_MIN, REF_MIN, REF_MAX = 0.90, 10.0, 50.0
B1112_OP_MIN = 1.05


def oscuro_opaco(eps, ref2):
    with np.errstate(invalid="ignore"):
        return (eps >= EPS_MIN) & (ref2 >= REF_MIN) & (ref2 < REF_MAX)


def img(d, v, fill):
    a = np.full((601, 601), fill, dtype=np.asarray(v).dtype if fill is not np.nan else float)
    a[d["iy"], d["ix"]] = v
    return a


def elegir_vcb(d, prev_grupo_img):
    """Indice del objeto ICEOBJ con mas pixeles sobre el grupo anterior (imagen booleana), o -1."""
    ido = d["idI"]
    ok = ido >= 0
    n = len(d["I__Object_Id"])
    if n == 0 or prev_grupo_img is None or not prev_grupo_img.any():
        return -1, np.zeros(n)
    en = prev_grupo_img[d["iy"], d["ix"]]
    solape = np.bincount(ido[ok], weights=en[ok].astype(float), minlength=n)
    k = int(np.argmax(solape))
    return (k if solape[k] > 0 else -1), solape


def objetos_ceniza_que_tocan(d, vcb_img):
    """Booleano por objeto ASHOBJ: algun pixel dentro de la dilatacion 3x3 de la imagen del objeto convectivo."""
    n = len(d["A__Object_Id"])
    if n == 0 or vcb_img is None or not vcb_img.any():
        return np.zeros(n, bool)
    dil = ndi.binary_dilation(vcb_img, structure=np.ones((3, 3), bool))
    ido = d["idA"]
    ok = ido >= 0
    toca = dil[d["iy"], d["ix"]]
    return np.bincount(ido[ok], weights=toca[ok].astype(float), minlength=n) > 0
