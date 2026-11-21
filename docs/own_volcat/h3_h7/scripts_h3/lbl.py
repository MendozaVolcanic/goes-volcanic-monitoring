"""H3: modelo radiativo propio de cielo despejado, linea por linea (sin dispersion, ETL, plano-paralelo).

Fisica (por que asi): la radiancia que ve el ABI en un canal IR sin nubes es la emision de la superficie
atenuada por la atmosfera mas la emision de cada capa de aire atenuada por lo que tiene encima. Lo que
absorbe en estas cuatro bandas es el vapor de agua (lineas y continuo), el CO2, el O3, el N2O y el CH4.

Piezas y fuentes (declaradas):
- Lineas: HITRAN (hitran.org via HAPI 1.3, sin cuenta), corte S >= 1e-27 cm-1/(molec cm-2) a 296 K,
  perfil Voigt (Humlicek 1982, W4), ancho de Lorentz con gamma_air y n_air (sin auto-ensanchamiento),
  corrimiento delta_air, intensidad escalada con la suma de particion TIPS de HAPI.
  Ala: 25 cm-1 desde el centro. Para H2O se resta el "pedestal" (valor a 25 cm-1), convencion con la que
  esta definido el continuo MT_CKD.
- Continuo de vapor de agua: MT_CKD 4.3 (AER, absco-ref_wv-mt-ckd.nc), propio + foraneo (no el de
  "closure"), con el termino de radiacion. Sin continuo de CO2 ni line mixing (declarado).
- Rejilla espectral: 0,01 cm-1 en tres tramos que cubren las SRF del ABI FM4 (CIMSS/STAR, 10-mar-2016).
"""
import os
import numpy as np
from numba import njit, prange

HERE = os.path.dirname(os.path.abspath(__file__))
# Insumos bajados (continuo MT_CKD y SRF del ABI). Por defecto en ./dl, como los dejo H3; H3_RT_DL apunta a otra
# carpeta con la misma estructura (mtckd/absco-ref_wv-mt-ckd.nc, srf/CHxx.SRF). Se agrego el 21-11-2026 (C2)
# porque la carpeta dl de H3 se borro con su scratchpad; la copia vigente vive en D:\goes_cache\rt.
DL = os.environ.get("H3_RT_DL", os.path.join(HERE, "dl"))
C2 = 1.4387769         # cm K (segunda constante de radiacion, CODATA)
C1 = 1.191042722e-5     # mW m-2 sr-1 cm4 (= RADCN1 de MT_CKD/LBLRTM x 1e7)
KB = 1.380649e-23; CLUZ = 2.99792458e8; AMU = 1.66053906660e-27
TREF = 296.0
DNU = 0.01
TRAMOS = [(753.0, 958.0), (1118.0, 1247.0), (1324.0, 1412.0)]
WING = 25.0


def rejilla():
    return np.concatenate([np.arange(a, b + DNU / 2, DNU) for a, b in TRAMOS])


@njit(cache=True)
def _w4(x, y):
    t = complex(y, -x)
    s = abs(x) + y
    if s >= 15.0:
        w = t * 0.5641896 / (0.5 + t * t)
    elif s >= 5.5:
        u = t * t
        w = t * (1.410474 + u * 0.5641896) / (0.75 + u * (3.0 + u))
    elif y >= 0.195 * abs(x) - 0.176:
        w = (16.4955 + t * (20.20933 + t * (11.96482 + t * (3.778987 + t * 0.5642236)))) / \
            (16.4955 + t * (38.82363 + t * (39.27121 + t * (21.69274 + t * (6.699398 + t)))))
    else:
        u = t * t
        w = np.exp(u) - t * (36183.31 - u * (3321.9905 - u * (1540.787 - u * (219.0313 - u * (
            35.76683 - u * (1.320522 - u * 0.56419)))))) / (32066.6 - u * (24322.84 - u * (
                9022.228 - u * (2186.181 - u * (364.2191 - u * (61.57037 - u * (1.841439 - u)))))))
    return w.real


@njit(parallel=True, cache=True)
def _kabs(nu, p_atm, T, l_nu, l_S, l_ga, l_na, l_da, l_E, l_mass, l_q, l_ped):
    """k(nu) [cm2/molec] para cada estado (p_atm[s], T[s]). l_q[s, i] = Q(Tref)/Q(T[s]) de la linea i."""
    ns = p_atm.shape[0]; nl = l_nu.shape[0]; ng = nu.shape[0]
    out = np.zeros((ns, ng))
    for s in prange(ns):
        p = p_atm[s]; tt = T[s]
        for i in range(nl):
            v0 = l_nu[i] + l_da[i] * p
            S = l_S[i] * l_q[s, i] * np.exp(-C2 * l_E[i] / tt) / np.exp(-C2 * l_E[i] / TREF) * \
                (1.0 - np.exp(-C2 * l_nu[i] / tt)) / (1.0 - np.exp(-C2 * l_nu[i] / TREF))
            gl = (TREF / tt) ** l_na[i] * l_ga[i] * p
            ad = v0 / CLUZ * np.sqrt(2.0 * KB * tt / (l_mass[i] * AMU))   # ancho Doppler 1/e
            y = gl / ad
            norm = S / (ad * np.sqrt(np.pi))
            ped = 0.0
            if l_ped[i]:
                ped = norm * _w4(WING / ad, y)
            j0 = np.searchsorted(nu, v0 - WING); j1 = np.searchsorted(nu, v0 + WING)
            for j in range(j0, j1):
                v = norm * _w4((nu[j] - v0) / ad, y) - ped
                if v > 0.0:
                    out[s, j] += v
    return out


def kabs(nu, p_hpa, T, L, sel, ped, qfun):
    """Coeficiente de absorcion por molecula (cm2/molec) para las lineas L[sel] en los estados (p, T)."""
    p_atm = np.asarray(p_hpa, float) / 1013.25; T = np.asarray(T, float)
    keys = list(zip(L["M"][sel], L["I"][sel]))
    uniq = sorted(set(keys))
    lq = np.empty((len(T), sel.sum()))
    for (M, I) in uniq:
        m = np.array([k == (M, I) for k in keys])
        q0 = qfun(M, I, TREF)
        for s, tt in enumerate(T):
            lq[s, m] = q0 / qfun(M, I, tt)
    return _kabs(nu, p_atm, T, L["nu"][sel], L["sw"][sel], L["gamma_air"][sel], L["n_air"][sel],
                 L["delta_air"][sel], L["elower"][sel], L["molmass"][sel] / 1.0, lq,
                 np.full(sel.sum(), ped))


def mtckd(nu, p_hpa, T, vmr_h2o, path):
    """Continuo MT_CKD 4.3 por molecula de H2O (cm2/molec), con termino de radiacion. Vectorizado en estados."""
    import netCDF4
    d = netCDF4.Dataset(path)
    w = d["wavenumbers"][:].data; sref = d["self_absco_ref"][:].data; fref = d["for_absco_ref"][:].data
    tex = d["self_texp"][:].data; P0 = float(d["ref_press"][...]); T0 = float(d["ref_temp"][...]); d.close()
    p = np.asarray(p_hpa, float)[:, None]; T = np.asarray(T, float)[:, None]; v = np.asarray(vmr_h2o, float)[:, None]
    rho = (p / P0) * (T0 / T)
    s = sref[None, :] * (T0 / T) ** tex[None, :] * v * rho
    f = fref[None, :] * (1 - v) * rho
    x = w[None, :] * C2 / T
    rad = np.where(x <= 0.01, 0.5 * x * w[None, :], w[None, :] * (1 - np.exp(-x)) / (1 + np.exp(-x)))
    c = (s + f) * rad
    return np.stack([np.interp(nu, w, ci) for ci in c])


def planck(nu, T):
    T = np.asarray(T, float)
    return C1 * nu ** 3 / np.expm1(C2 * nu / T[..., None])


def srf(band, nu):
    """SRF del ABI FM4 (archivo CIMSS/STAR, en cm-1) interpolada a la rejilla; 0 fuera del archivo."""
    p = os.path.join(DL, "srf", f"CH{band:02d}.SRF")
    if not os.path.exists(p):   # mismo archivo con el nombre que trae en CIMSS
        p = os.path.join(DL, "srf", f"ABI_FM4_10Mar2016_CH{band:02d}.SRF")
    a = np.loadtxt(p)
    a = a[np.argsort(a[:, 0])]
    return np.interp(nu, a[:, 0], a[:, 1], left=0.0, right=0.0)
