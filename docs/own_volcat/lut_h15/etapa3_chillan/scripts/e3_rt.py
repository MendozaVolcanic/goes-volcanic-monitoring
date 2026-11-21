r"""H15 etapa 3: cielo despejado con corrección por cota y nube negra en el punto frío, por hora GFS.

Por qué así:
- Cielo despejado: el modelo de H3 (rt_niveles.radiancias_pixel, sin cambios) se corre en nodos cada 6 píxeles
  (~15 km; el GFS es de 0,25°, así que el perfil no cambia más fino) para SEIS cotas de superficie (0 a 3,5 km).
  En cada cota la superficie se baja o sube por el perfil del GFS (hipsométrica con Tv) y la temperatura de piel
  conserva su diferencia con el aire del GFS en su propia superficie (al estilo CLAVR-x: se lleva la superficie a
  la cota fina con el perfil del modelo). Después cada píxel toma su cota del modelo de elevación (e3_dem.py)
  interpolando entre cotas. Es la corrección por cota que C2b vio en VOLCAT (Mauna Loa, −2,7 a −6,5 K/km).
- Nube negra de εtot y β: temperatura del punto más frío del perfil del GFS (p >= 10 hPa), sin atmósfera encima
  (variante N1 de cielo_sesgo, la que calza en nube espesa en Mauna Loa). No necesita el modelo: se evalúa con la
  Planck de banda de la L1b en e3_cadena.py.
- β opaco (dos tablas de VOLCAT lo usan): la nube negra con atmósfera encima por nivel (rcld de 33 niveles, corrida
  completa a la superficie del GFS), igual que H11 (h11_analisis.beta_opaco). No validado contra VOLCAT.
- Agua precipitable por cota (corrección de vapor de β, cielo_sesgo vuelta 2).

Salida: E3_DIR\rt\gfs_YYYYmmddHH.npz. Uso: python -I e3_rt.py [n_procesos]   (reanudable)
"""
import os
import sys
import time
from multiprocessing import Pool

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import e3_comun as K  # noqa: E402
import h13_comun as H  # noqa: E402
import rt_niveles as R  # noqa: E402
import e3_bajar as B  # noqa: E402

C = H.C
NY, NX = C.LAT.shape
PASO = 6
NODY = np.unique(np.r_[np.arange(0, NY, PASO), NY - 1])
NODX = np.unique(np.r_[np.arange(0, NX, PASO), NX - 1])
ZK = np.array([0.0, 700.0, 1400.0, 2100.0, 2800.0, 3500.0])      # cotas de superficie (m)
RD, GR, EPSV = 287.05, 9.80665, 0.608


def alturas(p, T, q, psfc, zsfc):
    """Altura geopotencial (m) de cada nivel de presión, integrando la hipsométrica desde (psfc, zsfc) hacia
    arriba y hacia abajo con Tv. Los niveles bajo la superficie del GFS usan los valores extrapolados del propio
    GFS. Devuelve z (n,) en el orden de p."""
    tv = T * (1 + EPSV * q)
    o = np.argsort(-p)                      # de mayor a menor presión
    ps, ts = p[o], tv[o]
    lp = np.log(ps)
    tvs = np.interp(np.log(psfc), lp[::-1], ts[::-1])
    z = np.empty(len(ps))
    # nivel de referencia: la superficie
    for i in range(len(ps)):
        # integra entre psfc y ps[i] con Tv media lineal en ln p (trapecio en 20 pasos)
        x = np.linspace(np.log(psfc), lp[i], 21)
        tvx = np.interp(x, lp[::-1], ts[::-1])
        z[i] = zsfc - RD / GR * np.trapezoid(tvx, x)
    out = np.empty(len(p)); out[o] = z
    return out, tvs


def tarea(h):
    out = os.path.join(K.RT, f"gfs_{h:%Y%m%d%H}.npz")
    if os.path.exists(out):
        return out, "ya"
    pg = B.path_gfs(h)
    if pg is None:
        return out, "sin_gfs"
    g = dict(np.load(pg))
    yy, xx = np.meshgrid(NODY, NODX, indexing="ij")
    ys, xs = yy.ravel(), xx.ravel()
    la, lo = C.LAT[ys, xs], C.LON[ys, xs]
    npl = len(g["p"])
    T = np.stack([R._i2(g, g["T"][i], la, lo) for i in range(npl)], 1)
    q = np.stack([R._i2(g, g["q"][i], la, lo) for i in range(npl)], 1)
    o3 = np.stack([R._i2(g, g["o3"][i], la, lo) for i in range(npl)], 1)
    ps, ts = R._i2(g, g["psfc"], la, lo), R._i2(g, g["tskin"], la, lo)
    pt, zs = R._i2(g, g["ptropo"], la, lo), R._i2(g, g["zsfc"], la, lo)
    p = np.asarray(g["p"], float)
    n = len(ys); nk = len(ZK)
    RC0 = np.zeros((n, 4)); RD_ = np.full((n, R.NB, 4), np.nan)
    RCK = np.full((n, nk, 4), np.nan); TPW = np.full((n, nk), np.nan); TSK = np.full((n, nk), np.nan)
    PSK = np.full((n, nk), np.nan); TCP = np.full(n, np.nan)
    t0 = time.time()
    estrat = p >= 10.0
    for i in range(n):
        sec = C.SEC[ys[i], xs[i]]
        RC0[i], RD_[i], _tb = R.radiancias_pixel(p, T[i], q[i], o3[i], ps[i], ts[i], sec, True)
        TCP[i] = T[i][estrat].min()
        z, _ = alturas(p, T[i], q[i], ps[i], zs[i])
        o = np.argsort(z)
        lpz = np.log(p[o])
        tair_sfc = np.interp(np.log(ps[i]), np.log(p[::-1]), T[i][::-1])
        for k, zk in enumerate(ZK):
            lpk = np.interp(zk, z[o], lpz)       # extrapola constante fuera del rango: se recorta abajo
            pk = float(np.exp(lpk))
            tair_k = np.interp(lpk, np.log(p[::-1]), T[i][::-1])
            tsk = ts[i] + (tair_k - tair_sfc)
            PSK[i, k], TSK[i, k] = pk, tsk
            RCK[i, k] = R.radiancias_pixel(p, T[i], q[i], o3[i], pk, tsk, sec, False)[0]
            # agua precipitable (cm) sobre la superficie a la cota k: (1/g) ∫ q dp, p en Pa; kg m-2 = mm
            m = p <= pk
            pp = np.r_[pk, p[m]]; qq = np.r_[np.interp(lpk, np.log(p[::-1]), q[i][::-1]), q[i][m]]
            TPW[i, k] = -np.trapezoid(qq, pp * 100.0) / GR / 10.0
    tmp = out + ".tmp.npz"
    np.savez(tmp, nody=NODY, nodx=NODX, zk=ZK, rclr0=RC0, rcld=RD_, rclrk=RCK, tpwk=TPW, tskk=TSK, psk=PSK,
             tcp=TCP, ptropo=pt, zsfc=zs, psfc=ps, tskin=ts, gfs=os.path.basename(pg))
    os.replace(tmp, out)
    return out, f"{n} nodos {time.time() - t0:.0f} s"


if __name__ == "__main__":
    npr = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    hs = B.horas()
    print("horas", len(hs), "nodos", len(NODY) * len(NODX), flush=True)
    with Pool(npr) as pool:
        for o, msg in pool.imap_unordered(tarea, hs):
            print(os.path.basename(o), msg, flush=True)
