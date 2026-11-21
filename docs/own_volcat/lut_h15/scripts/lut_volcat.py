r"""C3 (H15): probabilidad de ceniza por píxel con las tablas reales de VOLCAT para ABI (lectura de LECTURA_LUT.md).

Por qué existe: es la parte de VOLCAT que nuestro SECO propio (etapa 2 del 20-11) tuvo que inventar, entrenándola
con Chillán. Aquí se usan las densidades de ceniza y de nube que VOLCAT mismo trae en su tabla de píxel
(GOESR_ASH_pixel_probability_LUT_Jan11_2017_142740.hdf), exportadas por lut_exportar.py a
D:\goes_cache\lut_h15\lut_pixel.npz (fuera del repo).

Qué hace: para cada píxel busca la casilla de cada clasificador (εtot y β, BTD o εp(3,9)), toma la razón de
densidades ceniza/nube y las combina por Bayes ingenuo con el prior leído en la tabla (0,001). Lo que la tabla no
dice (combinación conjunta o condicional, qué hacer con un β fuera de eje, qué tablas entran) va como parámetro;
la etapa 2 lo elige contra la probabilidad publicada por VOLCAT en el caso de Mauna Loa.

Bins: el bin i cubre [MIN + i*DB, MIN + (i+1)*DB) (convención HISTOGRAM de IDL, que da exactamente el número de
bins de cada tabla). εtot y BT11 despejado usan sus bordes leídos.
"""
import numpy as np

LUT_NPZ = r"D:\goes_cache\lut_h15\lut_pixel.npz"
PRIOR = 0.001                                     # PIXEL_ASH_PROB_CLIMO, leído
EPS_EDGES = np.array([0.01, 0.03, 0.10, 0.20, 0.50, 0.90, 1.00])     # EMISS14_TOT_BINS_FULL_PIX
BTCLR_EDGES = np.array([160.0, 255.0, 260.0, 265.0, 270.0, 400.0])  # BT14_CLR_BINS_FULL_PIX
EJES = {                                          # (MIN, DB, NBINS) leídos; BTD inferido (ver LECTURA §3)
    "b1112": (-0.10, 0.05, 42),
    "b8511": (-0.10, 0.10, 21),
    "b7311": (-0.10, 0.10, 21),
    "ems7": (0.80, 0.05, 25),
    "btd": (-3.0, 0.25, 33),
}

# Clasificadores: nombre base de la tabla y variables de cada eje en orden numpy (inverso del dblarr de IDL).
# 'eps' y 'btclr' son ejes con bordes; los demás son ejes lineales de EJES. El último eje (cos_satzen) mide 1.
IR_S1 = [
    ("EMISS14_TOT_BETA1112_TOT_IR", [("b1112", "b_tot"), ("eps", "eps")]),
    ("EMISS14_TOT_BETA1112_OPAQUE_IR", [("b1112", "b_op"), ("eps", "eps")]),
    ("EMISS14_TOT_BETA1112_TOT_MULTI_LOW_IR", [("b1112", "b_low"), ("eps", "eps")]),
    ("EMISS14_TOT_BETA1112_TOT_MULTI_MID_IR", [("b1112", "b_mid"), ("eps", "eps")]),
    ("EMISS14_TOT_BTD1112_IR", [("btd", "btd"), ("eps", "eps"), ("btclr", "btclr")]),
    ("BETA1112_TOT_BETA7311_TOT_IR", [("b7311", "b73"), ("b1112", "b_tot"), ("eps", "eps")]),
]
IR_8511 = [
    ("BETA1112_TOT_BETA8511_TOT_IR", [("b8511", "b85"), ("b1112", "b_tot"), ("eps", "eps")]),
    ("BETA1112_OPAQUE_BETA8511_OPAQUE_IR", [("b8511", "b85op"), ("b1112", "b_op"), ("eps", "eps")]),
]
NOCHE = [
    ("BETA1112_TOT_EMS7_NIGHT", [("ems7", "ems7"), ("b1112", "b_tot"), ("eps", "eps")]),
    ("BETA1112_OPAQUE_EMS7_NIGHT", [("ems7", "ems7"), ("b1112", "b_op"), ("eps", "eps")]),
    ("BETA1112_TOT_MULTI_LOW_EMS7_NIGHT", [("ems7", "ems7"), ("b1112", "b_low"), ("eps", "eps")]),
    ("BETA1112_TOT_MULTI_MID_EMS7_NIGHT", [("ems7", "ems7"), ("b1112", "b_mid"), ("eps", "eps")]),
    ("BTD1112_EMS7_NIGHT", [("ems7", "ems7"), ("btd", "btd"), ("eps", "eps"), ("btclr", "btclr")]),
    ("BETA1112_TOT_BETA7311_TOT_NIGHT", [("b7311", "b73"), ("b1112", "b_tot"), ("eps", "eps")]),
]
CONJUNTOS = {"S1": IR_S1, "S2": IR_S1 + IR_8511, "S3": NOCHE}


class Tablas:
    def __init__(self, path=LUT_NPZ):
        z = np.load(path)
        self.t = {k: z[k] for k in z.files if k.endswith("_PIX")}

    def par(self, base, sup):
        return self.t[f"{base}_ASH_{sup}_PIX"], self.t[f"{base}_CLD_{sup}_PIX"]


def indice(x, eje, modo):
    """Índice de bin y máscara de uso. modo 'a': fuera de eje o NaN al primer bin; 'b': recorta al bin extremo
    (NaN se omite); 'c': fuera de eje o NaN se omite."""
    x = np.asarray(x, float)
    if eje == "eps":
        i = np.searchsorted(EPS_EDGES, x, side="right") - 1
        dentro = np.isfinite(x) & (x >= EPS_EDGES[0]) & (x <= EPS_EDGES[-1])
        i = np.where(x == EPS_EDGES[-1], len(EPS_EDGES) - 2, i)
        n = len(EPS_EDGES) - 1
    elif eje == "btclr":
        i = np.searchsorted(BTCLR_EDGES, x, side="right") - 1
        dentro = np.isfinite(x) & (x >= BTCLR_EDGES[0]) & (x < BTCLR_EDGES[-1])
        n = len(BTCLR_EDGES) - 1
    else:
        lo, db, n = EJES[eje]
        with np.errstate(invalid="ignore"):
            i = np.floor((x - lo) / db + 1e-9)
        i = np.where(np.isfinite(i), i, -1).astype(int)
        dentro = np.isfinite(x) & (i >= 0) & (i < n)
    i = np.where(np.isfinite(x), i, -1).astype(int)
    if modo == "a":
        return np.where(dentro, i, 0), np.ones(x.shape, bool)
    if modo == "b":
        return np.clip(i, 0, n - 1), np.isfinite(x)
    return np.clip(i, 0, n - 1), dentro


def log_odds(T, conjunto, entradas, agua, modo="a", comb="J"):
    """Log-odds posterior por píxel. entradas: dict de arreglos 1D (eps, b_tot, b_op, b_low, b_mid, b73, b85,
    b85op, btd, btclr, ems7). agua: bool 1D. comb: 'J' conjuntas tal cual; 'C1' condicional por εtot y factor de
    εtot una vez; 'C0' condicional sin factor de εtot. Devuelve (L, n_clasificadores_usados)."""
    npx = len(agua)
    L = np.full(npx, np.log(PRIOR / (1 - PRIOR)))
    nuso = np.zeros(npx, int)
    eps_factor_hecho = False
    for base, ejes in CONJUNTOS[conjunto]:
        idx, uso = [], np.ones(npx, bool)
        for eje, var in ejes:
            i, u = indice(entradas[var], eje, modo)
            idx.append(i)
            uso &= u
        ie = [k for k, (eje, _) in enumerate(ejes) if eje == "eps"][0]
        for sup, msk in (("WATER", agua), ("LAND", ~agua)):
            A, C = T.par(base, sup)
            A = A.reshape(A.shape[:len(ejes)])
            C = C.reshape(C.shape[:len(ejes)])
            sel = msk & uso
            if not sel.any():
                continue
            key = tuple(ix[sel] for ix in idx)
            if comb == "J":
                r = np.log(A[key]) - np.log(C[key])
            else:
                ax = tuple(k for k in range(len(ejes)) if k != ie)
                mA = A.sum(axis=ax)
                mC = C.sum(axis=ax)
                ei = idx[ie][sel]
                r = (np.log(A[key]) - np.log(mA[ei])) - (np.log(C[key]) - np.log(mC[ei]))
                if comb == "C1" and not eps_factor_hecho:
                    r = r + np.log(mA[ei]) - np.log(mC[ei])
            L[sel] += r
            nuso[sel] += 1
        if comb == "C1":
            eps_factor_hecho = True
    return L, nuso


def prob(L):
    return 1.0 / (1.0 + np.exp(-np.clip(L, -700, 700)))


# Física de SECO 1 (ec. 1 y 2): emisividad contra cielo despejado y nube negra; razón beta.
def planck_rad(bt, fk1, fk2, bc1, bc2):
    """BT (K) a radiancia con los coeficientes de Planck del archivo (convención GOES-R/GEOCAT)."""
    teff = bc1 + bc2 * bt
    return fk1 / np.expm1(fk2 / teff)


def emisividad(r_obs, r_clr, r_cld):
    with np.errstate(all="ignore"):
        return (r_obs - r_clr) / (r_cld - r_clr)


def beta(e_a, e_11):
    with np.errstate(all="ignore"):
        ok = (e_a < 1) & (e_11 < 1) & (e_11 != 0)
        return np.where(ok, np.log1p(-e_a) / np.log1p(-e_11), np.nan)
