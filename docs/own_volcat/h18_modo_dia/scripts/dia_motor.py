r"""H18: probabilidad de ceniza por píxel con las tablas de DÍA de VOLCAT (y las IR validadas de noche).

Por qué existe: en S15 sólo se usaron las tablas IR, validadas de noche sobre mar (Mauna Loa), aunque los 60
cuadros de Chillán son de día. Este motor agrega las tablas `_DAY_` (con `NRAT` = ρ(3,9)/ρ(0,65) y con ρ(0,65)),
leídas en LECTURA_DIA.md: densidades conjuntas condicionales al ángulo de dispersión (cada rebanada suma 1).

Qué hace: para cada tabla busca la casilla del píxel y devuelve su contribución en log-odds (log densidad ceniza
menos log densidad nube). Las sumas por variante y el prior (0,001) los arma quien llama. Ejes y bordes: los de
lut_h15/scripts/lut_volcat.py más NRAT (0 a 1,2 cada 0,1, 13 bins), ρ(0,65) en % (0 a 100 cada 10, 11 bins) y
ángulo de dispersión (0-90, 90-180°). Modo 'b' (fuera de eje se recorta al bin extremo; NaN, la tabla no entra).
Reglas de nube tenue del PR 75: R1 (β(7,3/11) sólo con ε(7,3) >= 0,1), R2 (β multicapa ausente al primer bin),
R3 (β(8,5/11) fuera si εtot < 0,1 y 1,05 < β(8,5/11) < 2).
"""
import os
import sys

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, "..", "..", "lut_h15", "scripts"))
import lut_volcat as LV  # noqa: E402

LV.EJES["nrat"] = (0.0, 0.1, 13)      # NRAT_MIN/DB_PIX, 13 bins (leído)
LV.EJES["ref2"] = (0.0, 10.0, 11)     # REF2_MIN/DB_PIX, 11 bins (leído), en %
L0 = np.log(LV.PRIOR / (1 - LV.PRIOR))
RELLENO = -999.0

# (nombre de tabla, ejes en orden numpy sin el de ángulo ni cos_satzen, ¿lleva ángulo?)
IR = [
    ("EMISS14_TOT_BETA1112_TOT_IR", [("b1112", "b_tot"), ("eps", "eps")]),
    ("EMISS14_TOT_BETA1112_OPAQUE_IR", [("b1112", "b_op"), ("eps", "eps")]),
    ("EMISS14_TOT_BETA1112_TOT_MULTI_LOW_IR", [("b1112", "b_low"), ("eps", "eps")]),
    ("EMISS14_TOT_BETA1112_TOT_MULTI_MID_IR", [("b1112", "b_mid"), ("eps", "eps")]),
    ("BETA1112_TOT_BETA7311_TOT_IR", [("b7311", "b73"), ("b1112", "b_tot"), ("eps", "eps")]),
    ("BETA1112_TOT_BETA8511_TOT_IR", [("b8511", "b85"), ("b1112", "b_tot"), ("eps", "eps")]),
    ("BETA1112_OPAQUE_BETA8511_OPAQUE_IR", [("b8511", "b85op"), ("b1112", "b_op"), ("eps", "eps")]),
]


def dia(nr):
    """Tablas de día con NRAT ('NRAT' o 'NRAT_LRC'); var de NRAT = 'nrat' o 'nrat_lrc'."""
    v = "nrat" if nr == "NRAT" else "nrat_lrc"
    return {
        "beta": [
            (f"BETA1112_TOT_{nr}_DAY", [("nrat", v), ("b1112", "b_tot"), ("eps", "eps")]),
            (f"BETA1112_OPAQUE_{nr}_DAY", [("nrat", v), ("b1112", "b_op"), ("eps", "eps")]),
            (f"BETA1112_TOT_MULTI_LOW_{nr}_DAY", [("nrat", v), ("b1112", "b_low"), ("eps", "eps")]),
            (f"BETA1112_TOT_MULTI_MID_{nr}_DAY", [("nrat", v), ("b1112", "b_mid"), ("eps", "eps")]),
        ],
        "btd": [(f"BTD1112_{nr}_DAY", [("nrat", v), ("btd", "btd"), ("eps", "eps"), ("btclr", "btclr")])],
    }


DIA_73 = ("BETA1112_TOT_BETA7311_TOT_DAY", [("b7311", "b73"), ("b1112", "b_tot"), ("eps", "eps")])
DIA_85 = [("BETA1112_TOT_BETA8511_TOT_DAY", [("b8511", "b85"), ("b1112", "b_tot"), ("eps", "eps")]),
          ("BETA1112_OPAQUE_BETA8511_OPAQUE_DAY", [("b8511", "b85op"), ("b1112", "b_op"), ("eps", "eps")])]
DIA_VREF = ("EMISS14_TOT_VREF_DAY", [("ref2", "ref2"), ("eps", "eps")])

_T = None


def tablas():
    global _T
    if _T is None:
        _T = LV.Tablas()
    return _T


def contrib(ent, agua, tabla, scat=None):
    """Contribución en log-odds de UNA tabla (0 donde no entra). scat: índice 0/1 del ángulo (tablas _DAY_)."""
    base, ejes = tabla
    n = len(agua)
    idx, uso = [], np.ones(n, bool)
    for eje, var in ejes:
        i, u = LV.indice(ent[var], eje, "b")
        idx.append(i)
        uso &= u
    if scat is not None:
        idx.append(scat)
        uso &= scat >= 0
    out = np.zeros(n)
    for sup, msk in (("WATER", agua), ("LAND", ~agua)):
        A, C = tablas().par(base, sup)
        k = len(ejes) + (1 if scat is not None else 0)
        A = A.reshape(A.shape[:k])
        C = C.reshape(C.shape[:k])
        sel = msk & uso
        if sel.any():
            key = tuple(ix[sel] for ix in idx)
            out[sel] = np.log(A[key]) - np.log(C[key])
    return out


def angulo_dispersion(sz, vz, raz, conv):
    """conv '+': cosΘ = −cosθs cosθv + sinθs sinθv cosφ ; '−': con −sinθs sinθv cosφ."""
    s, v, r = np.radians(sz), np.radians(vz), np.radians(raz)
    sg = 1.0 if conv == "+" else -1.0
    c = -np.cos(s) * np.cos(v) + sg * np.sin(s) * np.sin(v) * np.cos(r)
    return np.degrees(np.arccos(np.clip(c, -1, 1)))


def scat_idx(theta):
    return np.where(np.isfinite(theta), (theta >= 90).astype(int), -1)


def preparar(ent):
    """Aplica R2 (β multicapa ausente al primer bin) y devuelve ε(7,3) y la condición R3."""
    e = dict(ent)
    for k in ("b_low", "b_mid"):
        e[k] = np.where(np.isfinite(e[k]), e[k], RELLENO)
    with np.errstate(all="ignore"):
        e73 = 1 - (1 - e["eps"]) ** e["b73"]
    usa73 = np.isfinite(e73) & (e73 >= 0.1)                                   # R1
    usa85 = ~((e["eps"] < 0.1) & (e["b85"] > 1.05) & (e["b85"] < 2.0))        # R3
    return e, usa73, usa85


def piezas(ent, agua, scat):
    """Contribuciones por grupo de tablas, con R1 a R3 aplicadas. Devuelve dict grupo -> arreglo."""
    e, usa73, usa85 = preparar(ent)
    P = {}
    ir = [contrib(e, agua, t) for t in IR]
    P["ir"] = ir[0] + ir[1] + ir[2] + ir[3] + np.where(usa73, ir[4], 0) + np.where(usa85, ir[5] + ir[6], 0)
    for nr in ("NRAT", "NRAT_LRC"):
        g = dia(nr)
        P[f"beta_{nr}"] = sum(contrib(e, agua, t, scat) for t in g["beta"])
        P[f"btd_{nr}"] = sum(contrib(e, agua, t, scat) for t in g["btd"])
    P["d73"] = np.where(usa73, contrib(e, agua, DIA_73, scat), 0)
    P["d85"] = np.where(usa85, sum(contrib(e, agua, t, scat) for t in DIA_85), 0)
    P["vref"] = contrib(e, agua, DIA_VREF, scat)
    return P


def logit_variante(P, n, d, k, v, i):
    """n in {'n1','n2','n3'}; d,k,v,i in {0,1}. β(12/11) × β(7,3/11) de día entra siempre en las de día."""
    nrs = {"n1": ["NRAT"], "n2": ["NRAT_LRC"], "n3": ["NRAT", "NRAT_LRC"]}[n]
    L = L0 + P["d73"]
    for nr in nrs:
        L = L + P[f"beta_{nr}"] + (P[f"btd_{nr}"] if d else 0)
    if k:
        L = L + P["d85"]
    if v:
        L = L + P["vref"]
    if i:
        L = L + P["ir"]
    return L


def prob(L):
    return 1.0 / (1.0 + np.exp(-np.clip(L, -700, 700)))
