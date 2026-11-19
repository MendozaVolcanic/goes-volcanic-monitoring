"""H3 pasos 3 y 4: error del modelo en pixeles despejados del control (ANTES de mirar la huella), luego
compuerta G, AUC de eps11 y de las beta, por caso y agrupado, en las versiones M (modelada) y E (empirica).
Criterio: criterio_H3_cielo_modelado_2026-11-19.md. Uso: python h3_metricas.py error | metricas
"""
import sys as _s, os as _o
_s.path.insert(0, _o.path.dirname(_o.path.abspath(__file__)))  # modulos propios, explicito (python -I)
import os, sys, json, pickle
import numpy as np
from scipy import ndimage
from scipy.interpolate import RegularGridInterpolator
from scipy.stats import mannwhitneyu
import comun_h3 as C
import rt
from fetch_gfs import archivo

HERE = C.HERE
PAREO = json.load(open(os.path.join(HERE, "pareo.json")))
SEC = 1.0 / np.cos(np.radians(rt.cenit_satelital(C.LAT, C.LON)))
RTC = os.path.join(HERE, "rt_cache.pkl")
_rtc = pickle.load(open(RTC, "rb")) if os.path.exists(RTC) else {}
_mod = None
_gfs = {}


def modelo():
    global _mod
    if _mod is None:
        _mod = rt.Modelo()
    return _mod


def gfs(dt):
    h = archivo(dt)[0]
    if h not in _gfs:
        _gfs[h] = dict(np.load(os.path.join(HERE, "gfs", f"gfs_{h:%Y%m%d%H}.npz")))
    return _gfs[h]


def _i2(g, f, la, lo):
    """Bilineal en la grilla GFS (lat descendente en el archivo)."""
    # bounds_error=False, fill_value=None: extrapolacion lineal para las ultimas columnas de la ventana (lon > -70,25, hasta -70,20)
    r = RegularGridInterpolator((g["lat"][::-1], g["lon"]), f[::-1, :], bounds_error=False, fill_value=None)
    return r(np.column_stack([la, lo]))


def campos_pixel(g, ys, xs):
    la, lo = C.LAT[ys, xs], C.LON[ys, xs]
    T = np.stack([_i2(g, g["T"][i], la, lo) for i in range(len(g["p"]))], 1)
    q = np.stack([_i2(g, g["q"][i], la, lo) for i in range(len(g["p"]))], 1)
    o3 = np.stack([_i2(g, g["o3"][i], la, lo) for i in range(len(g["p"]))], 1)
    return T, q, o3, _i2(g, g["psfc"], la, lo), _i2(g, g["tskin"], la, lo), _i2(g, g["ttropo"], la, lo)


def ttropo(dt, ys, xs):
    g = gfs(dt)
    return _i2(g, g["ttropo"], C.LAT[ys, xs], C.LON[ys, xs])


def rclr_M(dt, ys, xs, emis=None):
    """Radiancia de cielo despejado modelada por pixel (dict banda -> array), con cache en disco."""
    emis = emis or rt.EMIS
    tag = tuple(emis[b] for b in rt.BANDS)
    g = gfs(dt); need = [(y, x) for y, x in zip(ys, xs) if (C.k(dt), y, x, tag) not in _rtc]
    if need:
        ny, nx = np.array([a for a, _ in need]), np.array([b for _, b in need])
        T, q, o3, ps, ts, _ = campos_pixel(g, ny, nx)
        M = modelo()
        for i, (y, x) in enumerate(need):
            _rtc[(C.k(dt), y, x, tag)] = M.radiancia(g["p"], T[i], q[i], o3[i], ps[i], ts[i], SEC[y, x], emis)
        pickle.dump(_rtc, open(RTC, "wb"))
    return {b: np.array([_rtc[(C.k(dt), y, x, tag)][b] for y, x in zip(ys, xs)]) for b in rt.BANDS}


def eps(Robs, Rclr, Bt):
    with np.errstate(all="ignore"):
        return (Robs - Rclr) / (Bt - Rclr)


def senales(scn, dt, ys, xs, version, E=None):
    """eps(lambda) sin recortar y beta por pixel. version 'M' o 'E'."""
    tt = ttropo(dt, ys, xs)
    if version == "M":
        Rc = rclr_M(dt, ys, xs)
    else:
        Rc = {b: rt.rad_de_bt(E[b][ys, xs], scn["co"][b]) for b in rt.BANDS}
    e = {b: eps(scn["rad"][b][ys, xs], Rc[b], rt.rad_de_bt(tt, scn["co"][b])) for b in rt.BANDS}
    gate = e[14] >= 0.02
    beta = {}
    with np.errstate(all="ignore"):
        for b in (15, 11, 10):
            v = np.log(1 - e[b]) / np.log(1 - e[14])
            beta[b] = np.where(gate & (e[b] < 1) & (e[14] < 1), v, np.nan)
    return e, gate, beta, tt


def auc(x, y):
    x = np.asarray(x, float); y = np.asarray(y, float); x = x[np.isfinite(x)]; y = y[np.isfinite(y)]
    if len(x) == 0 or len(y) == 0:
        return np.nan
    return mannwhitneyu(x, y).statistic / (len(x) * len(y))


def pares_ok():
    from datetime import datetime
    return [(p["caso"], datetime.strptime(p["pos"], "%Y%m%d_%H%M"), datetime.strptime(p["ctrl"], "%Y%m%d_%H%M"))
            for p in PAREO if p["estado"] == "ok"]


def paso_error(nmax=60, seed=0):
    """Error del modelo: control, pixeles con |BT11 - E11| < 2 K y a > 5 px de la huella (no se mira la huella
    del positivo mas que para excluir su vecindad)."""
    rng = np.random.default_rng(seed)
    filas = []
    for caso, dp, dc in pares_ok():
        hv = C.HUE[C.k(dp)]
        lejos = ~ndimage.binary_dilation(hv, np.ones((11, 11), bool))
        E, _ = C.empirica(caso, dp)
        sc = C.load(dc)
        m = lejos & (np.abs(sc[14] - E[14]) < 2.0) & np.all([np.isfinite(sc[b]) for b in rt.BANDS], 0)
        ys, xs = np.nonzero(m)
        if len(ys) > nmax:
            i = rng.choice(len(ys), nmax, replace=False); ys, xs = ys[i], xs[i]
        Rc = rclr_M(dc, ys, xs)
        for j in range(len(ys)):
            filas.append([caso, C.k(dc)] + [float(sc[b][ys[j], xs[j]] - rt.bt_de_rad(Rc[b][j], sc["co"][b])) for b in rt.BANDS])
        print("error", caso, C.k(dc), len(ys), flush=True)
    return filas


def paso_sens(nmax=20, de=-0.03, seed=0):
    """Sensibilidad a la emisividad de superficie: misma seleccion de pixeles de control (primeros nmax por
    escena), modelo con emisividad nominal y con emisividad + de en las cuatro bandas. Devuelve dBT por banda."""
    rng = np.random.default_rng(seed); alt = {b: rt.EMIS[b] + de for b in rt.BANDS}; d = []
    for caso, dp, dc in pares_ok():
        hv = C.HUE[C.k(dp)]
        lejos = ~ndimage.binary_dilation(hv, np.ones((11, 11), bool))
        E, _ = C.empirica(caso, dp); sc = C.load(dc)
        m = lejos & (np.abs(sc[14] - E[14]) < 2.0) & np.all([np.isfinite(sc[b]) for b in rt.BANDS], 0)
        ys, xs = np.nonzero(m)
        if len(ys) > 60:
            i = rng.choice(len(ys), 60, replace=False); ys, xs = ys[i], xs[i]
        ys, xs = ys[:nmax], xs[:nmax]
        R0 = rclr_M(dc, ys, xs); R1 = rclr_M(dc, ys, xs, alt)
        d.append(np.array([rt.bt_de_rad(R1[b], sc["co"][b]) - rt.bt_de_rad(R0[b], sc["co"][b]) for b in rt.BANDS]).T)
    d = np.vstack(d)
    return {b: (float(np.median(d[:, i])), float(d[:, i].min()), float(d[:, i].max())) for i, b in enumerate(rt.BANDS)}, len(d)


def resumen_error(filas, titulo):
    lines = [f"== {titulo}: obs - modelo (K) en pixeles despejados de control"]
    arr = np.array([f[2:] for f in filas], float); cs = np.array([f[0] for f in filas])
    for nombre, sel in [("todos", np.ones(len(cs), bool))] + [(f"caso {c}", cs == c) for c in (1, 2, 3)]:
        if sel.sum() == 0:
            continue
        a = arr[sel]
        s = " ".join(f"C{b}: med {np.median(a[:, i]):+.2f} desv {np.std(a[:, i]):.2f} (1,48MAD {1.4826*np.median(np.abs(a[:, i]-np.median(a[:, i]))):.2f})"
                     for i, b in enumerate(rt.BANDS))
        lines.append(f"{nombre} n={sel.sum()} | {s}")
    return "\n".join(lines)


def paso_metricas():
    res = {"M": {}, "E": {}}
    por_cuadro = []
    for caso, dp, dc in pares_ok():
        hv = C.HUE[C.k(dp)]; ys, xs = np.nonzero(hv)
        ring = ndimage.binary_dilation(hv, np.ones((13, 13), bool)) & ~ndimage.binary_dilation(hv, np.ones((3, 3), bool))
        ry, rx = np.nonzero(ring)
        if len(ry) > 40:   # metrica secundaria: muestra fija de 40 px del anillo (costo del modelo, declarado)
            i = np.random.default_rng(1).choice(len(ry), 40, replace=False); ry, rx = ry[i], rx[i]
        E, nE = C.empirica(caso, dp)
        sp, sc = C.load(dp), C.load(dc)
        for v in ("M", "E"):
            ep, gp, bp, ttp = senales(sp, dp, ys, xs, v, E)
            ec, gc, bc, ttc = senales(sc, dc, ys, xs, v, E)
            er, gr, br, _ = senales(sp, dp, ry, rx, v, E)
            d = res[v].setdefault(caso, {k: [] for k in ("e_p", "e_c", "g_p", "g_c", "e_r", "b_p15", "b_c15", "b_r15",
                                                          "b_p11", "b_c11", "b_r11", "b_p10", "b_c10", "b_r10", "invalid")})
            d["e_p"] += list(ep[14]); d["e_c"] += list(ec[14]); d["e_r"] += list(er[14])
            d["g_p"] += list(gp); d["g_c"] += list(gc)
            for b in (15, 11, 10):
                d[f"b_p{b}"] += list(bp[b]); d[f"b_c{b}"] += list(bc[b]); d[f"b_r{b}"] += list(br[b])
            d["invalid"].append(int(np.sum(gp & ~np.isfinite(bp[10]))) + int(np.sum(gc & ~np.isfinite(bc[10]))))
            por_cuadro.append((v, caso, C.k(dp), C.k(dc), len(ys), float(gp.mean()), float(gc.mean()),
                               float(np.median(ep[14])), float(np.median(ec[14])), float(np.median(ttp)), float(np.median(ttc)),
                               float(np.median(sp[14][hv] - sp[15][hv])), float(np.median(sc[14][hv] - sc[15][hv])),
                               {b: float(np.median(ep[b])) for b in (15, 11, 10)}, nE))
        print("metricas", caso, C.k(dp), flush=True)
    return res, por_cuadro


def tabla(res, v):
    lines = []
    grupos = [(f"caso {c}", [c]) for c in (1, 2, 3)] + [("AGRUPADO", [1, 2, 3])]
    for nombre, cs in grupos:
        d = {k: sum((res[v][c][k] for c in cs if c in res[v]), []) for k in res[v][cs[0] if cs[0] in res[v] else list(res[v])[0]]}
        if not d["e_p"]:
            lines.append(f"{v} {nombre}: sin datos"); continue
        Gp, Gc = np.mean(d["g_p"]), np.mean(d["g_c"])
        row = f"{v} {nombre:9s} n={len(d['e_p']):4d} G_huella={Gp:.3f} G_ctrl={Gc:.3f} dG={Gp-Gc:+.3f} AUC(e11)={auc(d['e_p'], d['e_c']):.3f}"
        for b, nm in ((15, "b12/11"), (11, "b8,5/11"), (10, "b7,3/11")):
            x = np.array(d[f"b_p{b}"]); y = np.array(d[f"b_c{b}"]); nx, ny = np.isfinite(x).sum(), np.isfinite(y).sum()
            if nx < 20 or ny < 20:
                row += f" {nm}=no medible(n {nx}/{ny})"
            else:
                row += f" {nm}={auc(x, y):.3f}(n {nx}/{ny}, med {np.nanmedian(x):.2f}/{np.nanmedian(y):.2f})"
        row += f" | sec. huella-vs-anillo AUC(e11)={auc(d['e_p'], d['e_r']):.3f}"
        for b, nm in ((15, "b12/11"), (11, "b8,5/11"), (10, "b7,3/11")):
            x = np.array(d[f"b_p{b}"]); y = np.array(d[f"b_r{b}"])
            row += f" {nm}=" + (f"{auc(x, y):.3f}" if (np.isfinite(x).sum() >= 20 and np.isfinite(y).sum() >= 20) else "nm")
        row += f" | beta invalidas (eps_lambda>=1 con compuerta) {sum(d['invalid'])}"
        lines.append(row)
    return "\n".join(lines)


if __name__ == "__main__":
    if sys.argv[1] == "error":
        f = paso_error()
        json.dump(f, open(os.path.join(HERE, "error_modelo.json"), "w"))
        print(resumen_error(f, "Error del modelo M (emisividad nominal)"))
        print("recortes de T en la LUT (interpolaciones fuera de rango):", getattr(modelo(), "recortes", 0))
        s, n = paso_sens()
        print(f"== Sensibilidad a emisividad de superficie -0,03 en las 4 bandas (n={n} px de control): dBT modelo (K) mediana [min, max]")
        print(" ".join(f"C{b}: {v[0]:+.2f} [{v[1]:+.2f}, {v[2]:+.2f}]" for b, v in s.items()))
    elif sys.argv[1] == "metricas":
        res, pc = paso_metricas()
        pickle.dump((res, pc), open(os.path.join(HERE, "metricas.pkl"), "wb"))
        print("== Por cuadro: version caso positivo control n G_pos G_ctrl med_e11_pos med_e11_ctrl Ttropo_pos Ttropo_ctrl BTD_pos BTD_ctrl med_eps(C15,C11,C10)_pos nEscenasE")
        for r in pc:
            print(r[0], r[1], r[2], r[3], r[4], f"{r[5]:.2f} {r[6]:.2f} {r[7]:+.3f} {r[8]:+.3f} {r[9]:.1f} {r[10]:.1f} {r[11]:+.2f} {r[12]:+.2f}",
                  " ".join(f"{v:+.3f}" for v in r[13].values()), r[14])
        print("recortes de T en la LUT:", getattr(modelo(), "recortes", 0))
        print("== Tablas (por caso y agrupado). AUC = P(positivo > control); beta sobre pixeles que pasan la compuerta en su escena")
        for v in ("M", "E"):
            print(tabla(res, v))
        # direccion por caso de cada beta (para la regla 'misma direccion en 2 de 3 casos')
        for v in ("M", "E"):
            for b in (15, 11, 10):
                dirs = []
                for c in (1, 2, 3):
                    if c not in res[v]:
                        dirs.append("sd"); continue
                    x, y = np.array(res[v][c][f"b_p{b}"]), np.array(res[v][c][f"b_c{b}"])
                    dirs.append("nm" if (np.isfinite(x).sum() < 20 or np.isfinite(y).sum() < 20) else f"{auc(x, y):.3f}")
                print(f"{v} beta C{b}/C14 AUC por caso (1,2,3): {dirs}")
