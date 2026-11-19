"""beta73: senales por pixel (E principal, M sensibilidad), AUC huella y anillo, bootstrap por escena,
decision segun criterio_beta73_2026-11-19.md. Uso: python metricas_b73.py senales | tablas

senales: calcula y guarda senales_b73.pkl (por par: valores de huella y anillo, positivo y control, E y M).
tablas : lee el pkl y aplica las reglas (no recalcula nada fisico).

eps(l) = [R_obs - R_clr] / [B_l(T_tropo) - R_clr]; tau = -ln(1 - eps).
beta73 = tau(C10)/tau(C14) con compuerta eps(C14) >= 0,02; dtau73 = tau(C10) - tau(C14) sin compuerta.
Reutiliza rt.py de H3 (modelo M, LUT y MT_CKD de la carpeta de H3) sin editarlo.
"""
import sys as _s, os as _o
_s.path.insert(0, _o.path.dirname(_o.path.abspath(__file__)))
import os, sys, json, pickle
from datetime import datetime
import numpy as np
from scipy import ndimage
from scipy.interpolate import RegularGridInterpolator
from scipy.stats import rankdata
import comun_b73 as C
sys.path.insert(0, C.H3)
import rt  # noqa: E402  (H3: modelo radiativo, cenit satelital, Planck con coeficientes L1b)
from fetch_gfs_b73 import archivo  # noqa: E402

ll = np.load(os.path.join(C.DET, "latlon.npz")); LAT, LON = ll["lat"], ll["lon"]
SEC = 1.0 / np.cos(np.radians(rt.cenit_satelital(LAT, LON)))
RTC = os.path.join(C.HERE, "rt_cache_b73.pkl")
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
        _gfs[h] = dict(np.load(os.path.join(C.HERE, "gfs", f"gfs_{h:%Y%m%d%H}.npz")))
    return _gfs[h]


def _i2(g, f, la, lo):
    r = RegularGridInterpolator((g["lat"][::-1], g["lon"]), f[::-1, :], bounds_error=False, fill_value=None)
    return r(np.column_stack([la, lo]))


def ttropo(dt, ys, xs):
    g = gfs(dt)
    return _i2(g, g["ttropo"], LAT[ys, xs], LON[ys, xs])


def rclr_M(dt, ys, xs):
    tag = tuple(rt.EMIS[b] for b in rt.BANDS)
    g = gfs(dt); need = [(y, x) for y, x in zip(ys, xs) if (C.k(dt), int(y), int(x), tag) not in _rtc]
    if need:
        ny, nx = np.array([a for a, _ in need]), np.array([b for _, b in need])
        la, lo = LAT[ny, nx], LON[ny, nx]
        T = np.stack([_i2(g, g["T"][i], la, lo) for i in range(len(g["p"]))], 1)
        q = np.stack([_i2(g, g["q"][i], la, lo) for i in range(len(g["p"]))], 1)
        o3 = np.stack([_i2(g, g["o3"][i], la, lo) for i in range(len(g["p"]))], 1)
        ps, ts = _i2(g, g["psfc"], la, lo), _i2(g, g["tskin"], la, lo)
        M = modelo()
        for i, (y, x) in enumerate(need):
            _rtc[(C.k(dt), int(y), int(x), tag)] = M.radiancia(g["p"], T[i], q[i], o3[i], ps[i], ts[i], SEC[y, x], rt.EMIS)
        tmp = RTC + ".tmp"; pickle.dump(_rtc, open(tmp, "wb")); os.replace(tmp, RTC)
    return {b: np.array([_rtc[(C.k(dt), int(y), int(x), tag)][b] for y, x in zip(ys, xs)]) for b in rt.BANDS}


def senales(scn, dt, ys, xs, version, E=None):
    tt = ttropo(dt, ys, xs)
    if version == "M":
        Rc = rclr_M(dt, ys, xs)
    else:
        Rc = {b: rt.rad_de_bt(E[b][ys, xs], scn["co"][b]) for b in rt.BANDS}
    with np.errstate(all="ignore"):
        e = {b: (scn["rad"][b][ys, xs] - Rc[b]) / (rt.rad_de_bt(tt, scn["co"][b]) - Rc[b]) for b in (10, 14)}
        val = (e[10] < 1) & (e[14] < 1) & np.isfinite(e[10]) & np.isfinite(e[14])
        t10, t14 = -np.log(1 - e[10]), -np.log(1 - e[14])
        gate = e[14] >= 0.02
        beta = np.where(val & gate, t10 / t14, np.nan)
        dtau = np.where(val, t10 - t14, np.nan)
    return {"e14": e[14], "e10": e[10], "gate": gate, "beta": beta, "dtau": dtau, "tt": tt}


def paso_senales():
    HU = np.load(os.path.join(C.HERE, "huellas_b73.npz"))
    PA = json.load(open(os.path.join(C.HERE, "pareo_b73.json")))
    out = []
    for p in PA:
        if p["estado"] != "ok":
            continue
        dp = datetime.strptime(p["pos"], "%Y%m%d_%H%M"); dc = datetime.strptime(p["ctrl"], "%Y%m%d_%H%M")
        hv = HU["h_" + p["pos"]]; ash = HU["a_" + p["pos"]]
        ring = ndimage.binary_dilation(hv, np.ones((13, 13), bool)) & ~ndimage.binary_dilation(hv, np.ones((3, 3), bool)) & ~ash
        ys, xs = np.nonzero(hv); ry, rx = np.nonzero(ring)
        i40 = np.random.default_rng(1).choice(len(ry), min(40, len(ry)), replace=False)
        E, nE = C.empirica(dp)
        if E is None:
            print(p["pos"], "E sin 5 candidatos con escena:", nE, flush=True)
            out.append({**p, "E_ok": False, "nE": nE}); continue
        sp, sc = C.load(dp), C.load(dc)
        r = {**p, "E_ok": True, "nE": nE, "dia": p["pos"][:8]}
        for v in ("E", "M"):
            rys, rxs = (ry, rx) if v == "E" else (ry[i40], rx[i40])
            r[v] = {"hp": senales(sp, dp, ys, xs, v, E), "hc": senales(sc, dc, ys, xs, v, E),
                    "rp": senales(sp, dp, rys, rxs, v, E), "rc": senales(sc, dc, rys, rxs, v, E)}
        r["btd_pos"] = float(np.nanmedian(sp[14][hv] - sp[15][hv])); r["btd_ctrl"] = float(np.nanmedian(sc[14][hv] - sc[15][hv]))
        out.append(r)
        print("senales", p["pos"], p["estrato"], "ctrl", p["ctrl"], "nE", nE, "px", len(ys), "anillo", len(ry), flush=True)
        tmp = os.path.join(C.HERE, "senales_b73.pkl.tmp"); pickle.dump(out, open(tmp, "wb")); os.replace(tmp, os.path.join(C.HERE, "senales_b73.pkl"))
    print("recortes de T en la LUT (modelo M):", getattr(_mod, "recortes", 0) if _mod is not None else 0)


# ---------------------------------------------------------------- tablas y decision

def auc(x, y):
    x = np.asarray(x, float); y = np.asarray(y, float); x = x[np.isfinite(x)]; y = y[np.isfinite(y)]
    if len(x) == 0 or len(y) == 0:
        return np.nan
    r = rankdata(np.concatenate([x, y]))
    return (r[:len(x)].sum() - len(x) * (len(x) + 1) / 2) / (len(x) * len(y))


def pool(pares, v, met, zona):
    a = "hp" if zona == "h" else "rp"; b = "hc" if zona == "h" else "rc"
    x = np.concatenate([p[v][a][met] for p in pares]) if pares else np.array([])
    y = np.concatenate([p[v][b][met] for p in pares]) if pares else np.array([])
    return x, y


def medible_beta(pares, v):
    x, y = pool(pares, v, "beta", "h")
    aport = sum(1 for p in pares if np.isfinite(p[v]["hp"]["beta"]).any() and np.isfinite(p[v]["hc"]["beta"]).any())
    return np.isfinite(x).sum() >= 20 and np.isfinite(y).sum() >= 20 and aport >= 3, int(np.isfinite(x).sum()), int(np.isfinite(y).sum()), aport


def boot(pares, v, met, grupos=None, n=2000, seed=0):
    rng = np.random.default_rng(seed)
    if grupos is None:
        unidades = [[p] for p in pares]
    else:
        ds = sorted({p["dia"] for p in pares}); unidades = [[p for p in pares if p["dia"] == d] for d in ds]
    vals = []
    for _ in range(n):
        sel = [q for i in rng.integers(0, len(unidades), len(unidades)) for q in unidades[i]]
        vals.append(auc(*pool(sel, v, met, "h")))
    vals = np.array(vals); vals = vals[np.isfinite(vals)]
    return (float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5))) if len(vals) else (np.nan, np.nan)


def estrato(pares, v, nombre):
    L = []
    ok, nx, ny, ap = medible_beta(pares, v)
    met = "beta" if ok else "dtau"
    dias = sorted({p["dia"] for p in pares})
    L.append(f"-- {nombre} [{v}]: pares={len(pares)} dias={len(dias)} ({', '.join(dias)}) | beta73 medible: {ok} (px {nx}/{ny}, pares que aportan {ap}) -> metrica que decide: {met}")
    if not pares:
        return L, None
    Ah = auc(*pool(pares, v, met, "h")); Ar = auc(*pool(pares, v, met, "r"))
    lo, hi = boot(pares, v, met); lod, hid = boot(pares, v, met, grupos="dia")
    xh, yh = pool(pares, v, met, "h")
    L.append(f"   AUC huella={Ah:.3f} IC95 escena=[{lo:.3f}, {hi:.3f}] (IC95 por dia, informativo [{lod:.3f}, {hid:.3f}]) | AUC anillo={Ar:.3f} | huella-anillo={Ah-Ar:+.3f}"
             f" | medianas huella pos/ctrl {np.nanmedian(xh):+.3f}/{np.nanmedian(yh):+.3f} (n {np.isfinite(xh).sum()}/{np.isfinite(yh).sum()})")
    pd_ = []
    for d in dias:
        pp = [p for p in pares if p["dia"] == d]
        pd_.append((d, auc(*pool(pp, v, met, "h")), len(pp)))
    L.append("   AUC huella por dia: " + "; ".join(f"{d} {a:.3f} (pares {n})" for d, a, n in pd_))
    otra = "dtau" if met == "beta" else "beta"
    xo, yo = pool(pares, v, otra, "h")
    L.append(f"   informativo: AUC {otra}={auc(xo, yo):.3f} (n {np.isfinite(xo).sum()}/{np.isfinite(yo).sum()}); AUC eps14={auc(*pool(pares, v, 'e14', 'h')):.3f};"
             f" G huella pos/ctrl={np.mean(np.concatenate([p[v]['hp']['gate'] for p in pares])):.3f}/{np.mean(np.concatenate([p[v]['hc']['gate'] for p in pares])):.3f}")
    # decision
    n_ok = len(pares) >= 5 and len(dias) >= 2
    pos_dias = sum(1 for _, a, _ in pd_ if np.isfinite(a) and a > 0.5)
    if not n_ok:
        ver = f"NO CONCLUYENTE (muestra: {len(pares)} pares, {len(dias)} dias; minimo 5 y 2)"
    elif Ah >= 0.70 and lo > 0.55 and (Ah - Ar) >= 0.10 and pos_dias >= 2:
        ver = "SE SOSTIENE"
    elif hi < 0.65:
        ver = "SE FALSA"
    else:
        ver = "NO CONCLUYENTE"
    L.append(f"   condiciones: AUC>=0,70 {Ah >= 0.70}; IC_inf>0,55 {lo > 0.55}; huella-anillo>=0,10 {(Ah - Ar) >= 0.10}; dias con AUC>0,5 = {pos_dias} de {len(pd_)}; IC_sup<0,65 {hi < 0.65}")
    L.append(f"   VEREDICTO {nombre} [{v}]: {ver}")
    return L, ver


def paso_tablas():
    S = pickle.load(open(os.path.join(C.HERE, "senales_b73.pkl"), "rb"))
    PA = json.load(open(os.path.join(C.HERE, "pareo_b73.json")))
    pares = [p for p in S if p.get("E_ok")]
    L = ["== Pares por cuadro (estrato, positivo, control, dBT11, n px, nE, medianas E huella pos/ctrl de dtau73 y beta73, G_E pos/ctrl, BTD pos/ctrl)"]
    for p in pares:
        e = p["E"]
        L.append(f"{p['estrato']} {p['pos']} {p['ctrl']} {p['dbt11']:+.2f} {p['n_px']} {p['nE']} | dtau {np.nanmedian(e['hp']['dtau']):+.3f}/{np.nanmedian(e['hc']['dtau']):+.3f}"
                 f" beta {np.nanmedian(e['hp']['beta']) if np.isfinite(e['hp']['beta']).any() else np.nan:+.2f}/{np.nanmedian(e['hc']['beta']) if np.isfinite(e['hc']['beta']).any() else np.nan:+.2f}"
                 f" G {e['hp']['gate'].mean():.2f}/{e['hc']['gate'].mean():.2f} | BTD {p['btd_pos']:+.2f}/{p['btd_ctrl']:+.2f}")
    for p in PA:
        if p["estado"] != "ok":
            L.append(f"aparte: {p['estrato']} {p['pos']} {p['estado']} " + (f"dBT11={p['dbt11']:+.2f}" if p.get("dbt11") is not None else ""))
    for p in S:
        if not p.get("E_ok", True):
            L.append(f"aparte: {p['estrato']} {p['pos']} sin cielo E (candidatos con escena {p['nE']})")
    ver = {}
    for v in ("E", "M"):
        L.append(f"\n==== Cielo {v} ({'principal, decide' if v == 'E' else 'sensibilidad, no decide'})")
        for nombre, sel in (("Estrato N (noche y crepusculo)", lambda p: p["estrato"] == "N"),
                            ("Estrato D (dia, extension)", lambda p: p["estrato"] == "D"),
                            ("Estrato D sin 14-11 (sensibilidad)", lambda p: p["estrato"] == "D" and p["dia"] != "20261114")):
            l, vv = estrato([p for p in pares if sel(p)], v, nombre); L += l; ver[(v, nombre)] = vv
    return "\n".join(L), ver


if __name__ == "__main__":
    if sys.argv[1] == "senales":
        paso_senales()
    else:
        txt, _ = paso_tablas()
        print(txt)
