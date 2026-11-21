r"""Nube tenue (H15, frente 1): utilidades comunes.

Por qué existe: los scripts de exploración (cuadros 1 a 5) y el de validación (cuadros 6 a 10) tienen que armar las
mismas entradas de nivel A (ε y β de VOLCAT) y las mismas contribuciones por tabla, para que la regla que se elige
mirando 1 a 5 sea exactamente la que se mide en 6 a 10.

Base: la variante posterior de 7 tablas IR sin la de εtot × BTD (etapa2_posterior.py, "S2sinBTD"), modo 'b' (β
fuera de eje recortado al bin extremo, NaN se omite), densidades conjuntas. Motor: ../../scripts/lut_volcat.py.
"""
import os
import sys

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
H15 = os.path.dirname(os.path.dirname(AQUI))
sys.path.insert(0, os.path.join(H15, "scripts"))
import lut_volcat as LV  # noqa: E402
import etapa2_validar as E  # noqa: E402

RES = os.path.join(os.path.dirname(AQUI), "resultados")
SIETE = [t for t in LV.IR_S1 + LV.IR_8511 if t[0] != "EMISS14_TOT_BTD1112_IR"]
NOMBRES = [t[0] for t in SIETE]
L0 = np.log(LV.PRIOR / (1 - LV.PRIOR))
_T = None


def tablas():
    global _T
    if _T is None:
        _T = LV.Tablas()
    return _T


def cargar(horas):
    """Nivel A de los cuadros pedidos, concatenado. Devuelve (ent, agua, verdad, cuadro)."""
    gfs = dict(np.load(os.path.join(E.ML, "gfs_ttropo.npz")))
    ENT, AG, V, Q = [], [], [], []
    for h in horas:
        A, _B, agua, v = E.cuadro(h, gfs)
        d = np.load(os.path.join(E.ML, f"ml_{h}.npz"))
        A = dict(A)
        A["bt10"] = d["geocatL1__channel_10_brightness_temperature"].astype(float).ravel()
        A["bt14"] = d["geocatL1__channel_14_brightness_temperature"].astype(float).ravel()
        A["bt15"] = d["geocatL1__channel_15_brightness_temperature"].astype(float).ravel()
        A["clr10"] = d["geocatRTM__channel_10_brightness_temperature_clear"].astype(float).ravel()
        A["clr14"] = d["geocatRTM__channel_14_brightness_temperature_clear"].astype(float).ravel()
        A["clr15"] = d["geocatRTM__channel_15_brightness_temperature_clear"].astype(float).ravel()
        A["b_nwp"] = d["geocatDIAGS1__cloud_beta_1112_tot_multi_nwp"].astype(float).ravel()
        A["lower_idx"] = d["geocatDIAGS1__lower_cloud_idx"].astype(float).ravel()
        ENT.append(A); AG.append(agua); V.append(v); Q.append(np.full(len(v), int(h)))
    ent = {k: np.concatenate([e[k] for e in ENT]) for k in ENT[0]}
    return ent, np.concatenate(AG), np.concatenate(V), np.concatenate(Q)


def contrib(ent, agua, tabla, modo="b", reemplazo=None):
    """Contribución en log-odds de UNA tabla por píxel (0 donde no entra). reemplazo: dict var -> arreglo, para
    probar otra entrada en esa tabla sola."""
    e = dict(ent)
    if reemplazo:
        e.update(reemplazo)
    LV.CONJUNTOS["_1"] = [tabla]
    L, n = LV.log_odds(tablas(), "_1", e, agua, modo=modo, comb="J")
    return L - L0


def logit(v):
    with np.errstate(all="ignore"):
        return np.log(v / (1 - v))


def no_saturado(v):
    return np.isfinite(v) & (v > 1e-6) & (v < 1 - 1e-6)
