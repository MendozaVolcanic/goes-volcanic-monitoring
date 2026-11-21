r"""Piezas comunes del frente cielo_lrc: carga de cuadros (reutiliza cielo_sesgo), LRC por filtro de gradiente,
y recálculo de ε(11) al nadir con observación, cielo despejado o nube negra reemplazados.

nt_regla.py (commit af0e8ca) se lee de D:\goes_cache\cielo_lrc\nt (no está en el repo).
"""
import os
import sys

import numpy as np
from scipy.ndimage import distance_transform_edt, maximum_filter, median_filter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), "cielo_sesgo", "scripts"))
import cielo_sesgo  # noqa: E402,F401  (fija lut_volcat y etapa2_validar del worktree, como en cielo_sesgo)
sys.path.insert(1, r"D:\goes_cache\cielo_lrc\nt\docs\own_volcat\lut_h15\nube_tenue\scripts")
import nt_regla  # noqa: E402,F401  (queda en caché para vuelta2_beta)
import vuelta2_beta as V2  # noqa: E402
import vuelta3_eps11 as V3  # noqa: E402

CS, E, LV = V2.CS, V2.CS.E, V2.CS.LV
RES = os.path.join(os.path.dirname(HERE), "resultados")
TRAMOS_EPS = ((0.05, 0.2), (0.2, 0.5))
DIST = ((0, 2), (2, 5), (5, 10), (10, 20), (20, 10 ** 9))
VEC8 = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]


def lrc(campo, stop=0.7, vmin=0.0, vmax=1.0, max_pasos=500):
    """Centro radiativo local (ATBD ACM de GOES-R, sec. 'LRC'): desde cada píxel válido se sube por el vecino de
    mayor valor (dirección del gradiente) hasta que el gradiente se invierte o se alcanza `stop`. Devuelve (fila,
    columna) del LRC; −1 donde no está definido. Píxeles con valor >= stop son su propio LRC."""
    ny, nx = campo.shape
    val = np.where(np.isfinite(campo), campo, -np.inf)
    pad = np.pad(val, 1, constant_values=-np.inf)
    vec = np.stack([pad[1 + dy:1 + dy + ny, 1 + dx:1 + dx + nx] for dy, dx in VEC8])
    k = np.argmax(vec, axis=0)
    vmaxn = np.max(vec, axis=0)
    dy = np.array([v[0] for v in VEC8])[k]
    dx = np.array([v[1] for v in VEC8])[k]
    rr, cc = np.indices(campo.shape)
    # siguiente paso: al vecino mayor si es mayor que el propio y el propio < stop; si no, se queda
    sube = (vmaxn > val) & (val < stop)
    nr = np.where(sube, rr + dy, rr)
    nc = np.where(sube, cc + dx, cc)
    valido = np.isfinite(campo) & (campo > vmin) & (campo < vmax) | (np.isfinite(campo) & (campo >= stop))
    r, c = rr.copy(), cc.copy()
    for _ in range(max_pasos):
        r2, c2 = nr[r, c], nc[r, c]
        if np.array_equal(r2, r) and np.array_equal(c2, c):
            break
        r, c = r2, c2
    r = np.where(valido, r, -1)
    c = np.where(valido, c, -1)
    return r, c


def tomar(campo, r, c):
    out = np.full(campo.shape, np.nan)
    ok = r >= 0
    out[ok] = campo[r[ok], c[ok]]
    return out


def eps_nadir(c, obs14=None, clr14=None, tcld=None):
    """ε(11) al nadir (V1) con la nube negra N1, reemplazando lo que se pase."""
    o = c.obs[14] if obs14 is None else obs14
    k = c.clr[14] if clr14 is None else clr14
    t = c.tcld["N1"] if tcld is None else tcld
    e = LV.emisividad(E.rad(c.d, o, 14), E.rad(c.d, k, 14), E.rad(c.d, t, 14))
    with np.errstate(all="ignore"):
        return 1 - (1 - e) ** c.mu


def eps_oblicuo_de(c, e_nadir):
    with np.errstate(all="ignore"):
        return 1 - (1 - e_nadir) ** (1 / c.mu)


def distancia_espesa(c):
    espesa = np.isfinite(c.ev) & (c.ev >= 0.5)
    return distance_transform_edt(~espesa)


def resumen(ev, e, dist):
    """Para píxeles con εtot de VOLCAT en 0,05 a 0,5: fracción dentro de 0,01 y Δε mediana por tramo; Δε mediana
    por distancia a nube espesa (sólo 0,05 a 0,3)."""
    out = {}
    for lo, hi in TRAMOS_EPS:
        s = np.isfinite(ev) & np.isfinite(e) & (ev >= lo) & (ev < hi)
        de = e[s] - ev[s]
        out[f"eps_{lo}_{hi}"] = {"n": int(s.sum()), "frac_le_001": float(np.mean(np.abs(de) <= 0.01)),
                                 "deps_mediana": float(np.median(de))}
    s0 = np.isfinite(ev) & np.isfinite(e) & (ev >= 0.05) & (ev < 0.3)
    pd = {}
    for a, b in DIST:
        q = s0 & (dist >= a) & (dist < b)
        if q.sum() > 100:
            pd[f"{a}_{b if b < 10**9 else 'inf'}"] = {"n": int(q.sum()), "deps_mediana": float(np.median(e[q] - ev[q]))}
    out["tenue_0.05_0.3_por_distancia"] = pd
    return out
