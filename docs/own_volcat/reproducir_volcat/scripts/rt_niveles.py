"""H11: cielo despejado y nube negra por nivel con el modelo de H3, por pixel. Uso: python rt_niveles.py [n_procesos]

Por que: SECO (Parte 1, ec. 1 y 2) compara la radiancia observada con dos extremos, el cielo despejado R_clr y
una nube negra R_cld(p) = B(T(p))*t_ac(p) + R_ac(p) a cierta presion: en la tropopausa para eps_tot y beta_tot,
en el nivel donde eps llega a 0,98 para beta_opaque. Las pruebas H3 y beta73 usaron B(T_tropo) sin la atmosfera
de arriba; aqui se calcula entera, espectralmente, y se convoluciona con la SRF de cada banda.

No cambia la fisica de rt.py (capas, LUT, continuo, emisividad fija): copia su camino ascendente y agrega
la nube en cada borde de capa. Guarda un npz por (par, rol) en RTDIR, reanudable.
"""
import os, sys, time
import numpy as np
from multiprocessing import Pool
from scipy.interpolate import RegularGridInterpolator

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import comun_h11 as C  # noqa: E402
rt = C.rt
NB = len(rt.PTOP)      # 33 bordes superiores de capa (1000 ... 1 hPa)
_M = None


def modelo():
    global _M
    if _M is None:
        _M = rt.Modelo()
    return _M


def radiancias_pixel(plev, T, q, o3, psfc, tskin, sec, completo=True):
    """R_clr por banda y, si completo, R_cld en los 33 bordes superiores de capa (NaN bajo la superficie) y T del borde."""
    M = modelo()
    capas = M.capas(plev, T, q, o3, psfc)
    tc = M.tau_capas(capas)
    tau_up = np.cumsum([t for t, _ in tc][::-1], axis=0)[::-1] * sec
    tr_base = np.exp(-tau_up)
    tr_top = np.vstack([tr_base[1:], np.ones((1, len(M.nu)))])
    Bl = rt.lbl.planck(M.nu, np.array([tt for _, tt in tc]))
    contrib = Bl * (tr_top - tr_base)
    L_atm = contrib.sum(0)
    td = np.cumsum([t for t, _ in tc], axis=0) * 1.66
    tr_dtop = np.exp(-td); tr_dbase = np.vstack([np.ones((1, len(M.nu))), tr_dtop[:-1]])
    L_down = (Bl * (tr_dbase - tr_dtop)).sum(0)
    Bs = rt.lbl.planck(M.nu, np.array(tskin))
    rclr = np.zeros(4); rcld = np.full((NB, 4), np.nan); tb = np.full(NB, np.nan)
    srf = [M.srf[b] for b in rt.BANDS]
    for j, b in enumerate(rt.BANDS):
        e = rt.EMIS[b]
        Lnu = L_atm + tr_base[0] * (e * Bs + (1 - e) * L_down)
        rclr[j] = (srf[j] * Lnu).sum() / srf[j].sum()
    if completo:
        lp = np.log(plev)
        above = np.cumsum(contrib[::-1], axis=0)[::-1]          # above[i] = emision de capas i..n-1
        above = np.vstack([above[1:], np.zeros((1, len(M.nu)))])  # emision sobre el tope de la capa i
        for i, (l, *_r) in enumerate(capas):
            ptop = rt.PTOP[l]
            Tt = float(np.interp(np.log(ptop), lp[::-1], T[::-1]))
            Rnu = rt.lbl.planck(M.nu, np.array(Tt)) * tr_top[i] + above[i]
            tb[l] = Tt
            for j in range(4):
                rcld[l, j] = (srf[j] * Rnu).sum() / srf[j].sum()
    return rclr, rcld, tb


def _i2(g, f, la, lo):
    r = RegularGridInterpolator((g["lat"][::-1], g["lon"]), f[::-1, :], bounds_error=False, fill_value=None)
    return r(np.column_stack([la, lo]))


def tarea(args):
    out, dt, ys, xs, full = args
    if os.path.exists(out):
        return out, "ya"
    g = dict(np.load(C.path_gfs(dt)))
    la, lo = C.LAT[ys, xs], C.LON[ys, xs]
    np_ = len(g["p"])
    T = np.stack([_i2(g, g["T"][i], la, lo) for i in range(np_)], 1)
    q = np.stack([_i2(g, g["q"][i], la, lo) for i in range(np_)], 1)
    o3 = np.stack([_i2(g, g["o3"][i], la, lo) for i in range(np_)], 1)
    ps, ts = _i2(g, g["psfc"], la, lo), _i2(g, g["tskin"], la, lo)
    pt, tt = _i2(g, g["ptropo"], la, lo), _i2(g, g["ttropo"], la, lo)
    n = len(ys); RC = np.zeros((n, 4)); RD = np.full((n, NB, 4), np.nan); TB = np.full((n, NB), np.nan)
    t0 = time.time()
    for i in range(n):
        RC[i], RD[i], TB[i] = radiancias_pixel(g["p"], T[i], q[i], o3[i], ps[i], ts[i], C.SEC[ys[i], xs[i]], bool(full[i]))
    tmp = out + ".tmp.npz"
    np.savez(tmp, ys=ys, xs=xs, full=full, rclr=RC, rcld=RD, tb=TB, ptropo=pt, ttropo=tt, psfc=ps, tskin=ts,
             zsfc=_i2(g, g["zsfc"], la, lo), gfs=os.path.basename(C.path_gfs(dt)))
    os.replace(tmp, out)
    return out, f"{n} px {time.time() - t0:.0f} s"


def tareas():
    T = []
    for p in C.pares():
        z = C.zonas(p["hv"], p["ash"])
        fullm = z["h"] | z["an"]; allm = fullm | z["cf"]
        ys, xs = np.nonzero(allm); full = fullm[ys, xs]
        for rol in ("pos", "ctrl"):
            dt = C.dtk(p[rol])
            if C.path_escena(dt) is None or C.path_gfs(dt) is None:
                print("FALTA", p["pos"], rol, "escena" if C.path_escena(dt) is None else "gfs", flush=True)
                continue
            T.append((os.path.join(C.RTDIR, f"{p['pos']}_{rol}.npz"), dt, ys, xs, full))
    return T


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 8
    T = tareas()
    T.sort(key=lambda t: len(t[2]))
    print("tareas", len(T), "pixeles", sum(len(t[2]) for t in T), flush=True)
    with Pool(n) as pool:
        for out, msg in pool.imap_unordered(tarea, T):
            print(os.path.basename(out), msg, flush=True)
