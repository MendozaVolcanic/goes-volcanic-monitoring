r"""S27a: ¿qué dispara de noche en 2026, pluma diaria, depósito de ceniza o nieve distinta? Implementa
criterio_2026-11-25.md (commit 2c7af2b, empujado antes de cruzar un solo disparo con el viento).

Por qué así: cada causa deja otra huella. Una pluma va a sotavento a su altura y se mueve con el viento (prueba P);
una temporada de nieve distinta afecta igual a las cumbres vecinas sin pluma (prueba N, Antuco y Longaví con la misma
regla de la zona); un depósito es un piso fijo, toda la noche y también de día (prueba D). El detector es el de S26a
tal cual (percentil 4,75); aquí sólo se miran sus disparos.

Uso: python -I s27a_medir.py medir      (escribe resultados/s27a_resultado.json y D:\goes_notas\s27\s27a\cuadros_*.csv)
"""
import csv
import json
import math
import os
import sys
import time
import warnings
from datetime import datetime, timedelta

import numpy as np
from scipy import stats

sys.stdout.reconfigure(encoding="utf-8")
warnings.simplefilter("ignore", RuntimeWarning)
AQUI = os.path.dirname(os.path.abspath(__file__))
OV = os.path.abspath(os.path.join(AQUI, "..", ".."))
REPO = os.path.abspath(os.path.join(OV, "..", ".."))
RES = os.path.join(os.path.dirname(AQUI), "resultados")
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(OV, "s26a_combinado", "scripts"))
import s26a_medir as U  # noqa: E402   (Partes, el detector unión de S26a, sin cambios)
from src.process.parallax import parallax_shift  # noqa: E402

S, Z = U.S, U.Z
B, M, H24, C29 = U.B, U.M, U.H24, U.C29
TRAB = r"D:\goes_notas\s27\s27a"
GFS = os.path.join(TRAB, "gfs")
PSTAR = 4.75
NOCHE = list(U.NOCHE)                              # 03:00 a 08:50 UTC
DIA_D4 = range(90, 126)                            # 15:00 a 20:50 UTC
T0_26, T0_25 = datetime(2026, 9, 21), S.T0R
SAT_LON = -75.2
CLAT_W, CLON_W = -36.8677, -71.3793                # punto del viento (H10, S22c)
CLAT, CLON = C29.CRATER
KX, KY = 111.32 * math.cos(math.radians(CLAT)), 110.57
ZCAPA = np.round(np.arange(3.0, 6.0 + 1e-9, 0.1), 2)
H_REF, H_SENS = 4.5, (3.5, 5.5)
VMIN, RMIN = 3.0, 1.0
KMIN = 3
MIN_CUADROS_P, MIN_NOCHES_P = 30, 8
SITIOS = {"antuco": (-37.41, -71.35), "longavi": (-36.19, -71.16)}
LATF, LONF = C29.LAT.ravel(), C29.LON.ravel()
NPIX = LATF.size
TABLA_S26A = r"D:\goes_notas\s26\s26a\tabla_2026.csv"


# ---------- geometría ----------
def plano(lat, lon):
    return (np.asarray(lon) - CLON) * KX, (np.asarray(lat) - CLAT) * KY


def corregidos(pix, h_km):
    """Posición (x este, y norte, km desde el cráter) de los píxeles corregida por paralaje a h_km."""
    la, lo = parallax_shift(LATF[pix], LONF[pix], h_km * 1000.0, sat_lon=SAT_LON)
    return plano(la, lo)


_POS = {}


def pos(h_km):
    if h_km not in _POS:
        _POS[h_km] = corregidos(np.arange(NPIX), h_km)
    return _POS[h_km]


def rumbo_centroide(pix, h_km):
    x, y = pos(h_km)
    cx, cy = x[pix].mean(), y[pix].mean()
    return (math.degrees(math.atan2(cx, cy)) + 360.0) % 360.0, math.hypot(cx, cy)


# ---------- viento ----------
def _bil(campo, la, lo, LAT_, LON_):
    i = np.interp(la, LAT_[::-1], np.arange(len(LAT_))[::-1])
    j = np.interp(lo, LON_, np.arange(len(LON_)))
    i0, j0 = int(np.floor(i)), int(np.floor(j))
    di, dj = i - i0, j - j0
    return ((1 - di) * (1 - dj) * campo[..., i0, j0] + di * (1 - dj) * campo[..., i0 + 1, j0]
            + (1 - di) * dj * campo[..., i0, j0 + 1] + di * dj * campo[..., i0 + 1, j0 + 1])


_HORA = {}


def hora(h):
    """(u, v) medios de la capa 3 a 6 km y T700 (K) en el punto del viento, o None si falta el archivo."""
    if h not in _HORA:
        fn = os.path.join(GFS, f"gfst1_{h:%Y%m%d%H}.npz")
        if not os.path.exists(fn):
            _HORA[h] = None
        else:
            d = np.load(fn)
            u = _bil(d["u"], CLAT_W, CLON_W, d["lat"], d["lon"])
            v = _bil(d["v"], CLAT_W, CLON_W, d["lat"], d["lon"])
            z = _bil(d["z"], CLAT_W, CLON_W, d["lat"], d["lon"]) / 1000.0
            t = _bil(d["t"], CLAT_W, CLON_W, d["lat"], d["lon"])
            o = np.argsort(z)
            _HORA[h] = (float(np.interp(ZCAPA, z[o], u[o]).mean()), float(np.interp(ZCAPA, z[o], v[o]).mean()),
                        float(t[list(d["p_t"]).index(700.0)]))
    return _HORA[h]


def viento(dt, horas):
    """(θw hacia donde sopla, V, T700) lineal entre las dos horas bajadas que rodean dt; None si falta una."""
    hs = [dt.replace(hour=x, minute=0) for x in horas]
    ant = [h for h in hs if h <= dt]
    pos_ = [h for h in hs if h >= dt]
    if not ant or not pos_:
        return None
    h0, h1 = ant[-1], pos_[0]
    p0, p1 = hora(h0), hora(h1)
    if p0 is None or p1 is None:
        return None
    w = 0.0 if h1 == h0 else (dt - h0).total_seconds() / (h1 - h0).total_seconds()
    u, v, t = ((1 - w) * a + w * b for a, b in zip(p0, p1))
    return (math.degrees(math.atan2(u, v)) + 360.0) % 360.0, math.hypot(u, v), t


def viento_noche(t0, nd):
    """W[d, j] = (θw, V, T700) para los cuadros nocturnos j de NOCHE; NaN si falta."""
    W = np.full((nd, len(NOCHE), 3), np.nan)
    for d in range(nd):
        for j, s in enumerate(NOCHE):
            r = viento(t0 + timedelta(days=d, minutes=10 * s), (3, 6, 9))
            if r is not None:
                W[d, j] = r
    return W


# ---------- prueba P ----------
def prueba_P(eventos, W, h_km=H_REF):
    """eventos: lista de (d, j, pix). Devuelve C, n, noches, p del corrimiento de días, curva de giro."""
    nd = W.shape[0]
    obs = [(d, j) + rumbo_centroide(np.asarray(p), h_km) for d, j, p in eventos]
    obs = [(d, j, th, r) for d, j, th, r in obs if r >= RMIN]

    def C_de(k=0, phi=0.0):
        c, n, noches = [], 0, set()
        for d, j, th, _ in obs:
            dd = (d + k) % nd
            tw, V = W[dd, j, 0], W[dd, j, 1]
            if not np.isfinite(tw) or V < VMIN:
                continue
            c.append(math.cos(math.radians(th - tw - phi)))
            noches.add(d)
        return (float(np.mean(c)) if c else np.nan), len(c), len(noches)
    C0, n0, no0 = C_de()
    nulos = [C_de(k)[0] for k in range(KMIN, nd - KMIN + 1)]
    nulos = [x for x in nulos if np.isfinite(x)]
    p = (1 + sum(x >= C0 for x in nulos)) / (1 + len(nulos)) if np.isfinite(C0) else None
    giro = {int(f): round(C_de(0, f)[0], 4) for f in range(0, 360, 30)}
    return {"C": None if not np.isfinite(C0) else round(C0, 4), "cuadros": n0, "noches": no0,
            "eventos_con_r_min": len(obs), "p_corrimiento": p, "n_corrimientos": len(nulos),
            "nulo_p50_p95": [round(float(np.percentile(nulos, q)), 4) for q in (50, 95)] if nulos else None,
            "giro_C_por_phi": giro, "giro_max_phi": max(giro, key=giro.get)}


def poder_P(evaluados, W):
    """Pluma ideal: en cada cuadro nocturno evaluado con viento >= 3 m/s, los dos píxeles de la zona más cerca de la
    recta del cráter con rumbo θw, a 1 a 8 km a lo largo."""
    x, y = pos(H_REF)
    zx, zy = x[Z.ZONA], y[Z.ZONA]
    ev = []
    for d, j in evaluados:
        tw, V = W[d, j, 0], W[d, j, 1]
        if not np.isfinite(tw) or V < VMIN:
            continue
        ux, uy = math.sin(math.radians(tw)), math.cos(math.radians(tw))
        a = zx * ux + zy * uy
        perp = np.abs(zx * uy - zy * ux)
        ok = np.flatnonzero((a >= 1.0) & (a <= 8.0))
        if len(ok) < 2:
            continue
        o = ok[np.argsort(perp[ok])[:2]]
        ev.append((d, j, list(Z.ZONA[o])))
    return prueba_P(ev, W)


# ---------- la zona generalizada (prueba N y comprobación) ----------
class Zona:
    """La regla de la zona de S25a puesta en un volcán cualquiera: zona, anillo de compuerta y controles propios."""

    def __init__(self, nombre, zona, anillo, ctrl):
        self.nombre, self.zona, self.anillo, self.ctrl = nombre, zona, anillo, ctrl
        zd = C29.ZDEM.ravel()
        self.ctrl_p = [np.flatnonzero(np.abs(zd[ctrl] - zd[p]) <= Z.COTA_M) for p in zona]

    def nubes(self, acm, est):
        nd_ = acm.shape[0]
        FD = np.full((nd_, 144), np.nan)
        DIN = np.zeros((nd_, 144, len(self.ctrl)), bool)
        for d in range(nd_):
            for s in range(144):
                if not (acm[d, s] != 255).any():
                    continue
                nd = B.dinamica(acm[d, s], est[s])
                FD[d, s] = nd[self.anillo].mean()
                DIN[d, s] = nd[self.ctrl]
        return FD, DIN

    def regional(self, btd, DIN, bctrl):
        nd_ = btd.shape[0]
        C = np.full((nd_, 144, len(self.zona)), np.nan, np.float32)
        for d in range(nd_):
            a = btd[d][:, self.ctrl] - bctrl
            a[DIN[d]] = np.nan
            for j, idx in enumerate(self.ctrl_p):
                sub = a[:, idx]
                n = np.isfinite(sub).sum(1)
                C[d, :, j] = np.where(n >= Z.MIN_CTRL, np.nanmedian(sub, 1), np.nan)
        return C

    def correr(self, btd25, acm25, est25, btd26, acm26, est26, sitio):
        hay25 = np.isfinite(btd25[:, :, self.zona[0]])
        FD25, DIN25 = self.nubes(acm25, est25)
        G25 = FD25 <= B.G_MAX
        USA25 = G25 & H24.despejada(sitio, acm25) & hay25
        bctrl = Z.base(btd25, USA25, self.ctrl)
        C25 = self.regional(btd25, DIN25, bctrl)
        Z25 = np.ascontiguousarray(btd25[:, :, self.zona])
        IZ = np.arange(len(self.zona))
        BZ = np.array([Z.base(Z25, USA25, IZ, excl=d) for d in range(Z25.shape[0])])
        self.SR, self.PR = Z.tabla_S(Z25, C25, BZ, G25)
        self.bz = Z.base(Z25, USA25, IZ)
        FD26, DIN26 = self.nubes(acm26, est26)
        C26 = self.regional(btd26, DIN26, bctrl)
        G26 = FD26 <= B.G_MAX
        Z26 = btd26[:, :, self.zona]
        self.ST, self.PT = Z.tabla_S(Z26, C26, self.bz, G26)
        self.A26 = Z26 - self.bz[None] - C26              # anomalía por píxel (prueba D4)
        self.G26, self.E126 = G26, H24.despejada(sitio, acm26)
        return self

    def disparos(self, p=PSTAR):
        B.PCT_U = p
        UL = [Z.umbral(self.SR, excl=d) for d in range(self.SR.shape[0])]
        sec = [Z.disparos(self.SR, d, UL[d], UL[d - 1] if d else None) for d in range(self.SR.shape[0])]
        Ut = Z.umbral(self.SR)
        bla = [Z.disparos(self.ST, d, Ut) for d in range(self.ST.shape[0])]
        return sec, bla


def tasa_noche(lista):
    F = sum(int(F[NOCHE].sum()) for F, _ in lista)
    E = sum(int(ev[NOCHE].sum()) for _, ev in lista)
    return F, E


def frac_por_noche(lista, min_ev=1):
    out = []
    for F, ev in lista:
        e = int(ev[NOCHE].sum())
        out.append(F[NOCHE].sum() / e if e >= min_ev else np.nan)
    return np.array(out)


def zona_de(la, lo):
    dist = C29.hav(C29.LAT, C29.LON, la, lo)
    i, j = np.unravel_index(np.argmin(dist), dist.shape)
    bl = np.zeros_like(dist, bool)
    bl[i - 1:i + 2, j - 1:j + 2] = True
    zona = np.flatnonzero(((dist < 4.0) | bl).ravel())
    anillo = np.flatnonzero(((dist >= M.R_IN) & (dist <= M.R_OUT) & ~bl).ravel())
    ctrl = np.flatnonzero(((C29.DIST > Z.R_CTRL) & (dist > 45.0)).ravel())
    return zona, anillo, ctrl, dist


# ---------- medir ----------
def medir():
    os.makedirs(TRAB, exist_ok=True)
    os.makedirs(RES, exist_ok=True)
    t = time.time()
    capt = []
    orig = Z.tabla_S

    def tabla_S_capt(*a, **k):
        r = orig(*a, **k)
        capt.append(r)
        return r
    Z.tabla_S = tabla_S_capt
    X = U.Partes()
    Z.tabla_S = orig
    PR25 = capt[0][1]                                   # pares de la zona en 2025 (con base sin cada día)
    sec = X.seco(PSTAR)
    res, Ua, Uz = X.blanco(PSTAR)
    CL = X.CL
    # comprobación de código (§2)
    seco_u = U.medidas_seco(sec["u"])
    ok_seco = seco_u["disparos"] == 269 and seco_u["evaluados"] == 5499
    dif = 0
    with open(TABLA_S26A, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            d = (datetime.strptime(r["dia"], "%Y-%m-%d") - T0_26).days
            s = M.slot(r["hora"])
            Fa, Fz = res[d]["a"][0][s], res[d]["z"][0][s]
            p1 = int(Z.ZONA[X.PTz[d, s, 0]]) if X.PTz[d, s, 0] >= 0 else -1
            p2 = int(Z.ZONA[X.PTz[d, s, 1]]) if X.PTz[d, s, 1] >= 0 else -1
            dif += (int(Fa) != int(r["F_a"])) + (int(Fz) != int(r["F_z"])) + (p1 != int(r["px1"])) + (p2 != int(r["px2"]))
    print(f"comprobación: seco {seco_u['disparos']}/{seco_u['evaluados']}, diferencias con tabla_2026 {dif}", flush=True)
    if not ok_seco or dif:
        json.dump({"seco": seco_u, "diferencias": dif}, open(os.path.join(RES, "s27a_reproduccion_FALLA.json"), "w"))
        sys.exit("no reproduce: error de código, no se mide")
    ND26, ND25 = B.ND, Z.NR

    # eventos nocturnos con sus píxeles
    def eventos(año):
        ev, evaluados = [], []
        for d in range(ND26 if año == 2026 else ND25):
            if año == 2026:
                (Fa, eva), (Fz, evz) = res[d]["a"], res[d]["z"]
            else:
                (Fa, eva), (Fz, evz) = sec["a"][d], sec["z"][d]
            for j, s in enumerate(NOCHE):
                if evz[s]:
                    evaluados.append((d, j))
                if año == 2026 and CL[d, s] == "P":       # sólo lo que VOLCAT no marcó (el exceso a explicar)
                    continue
                pix = []
                if Fz[s]:
                    pp = X.PTz[d, s] if año == 2026 else PR25[d, s]
                    pix += [int(Z.ZONA[q]) for q in pp if q >= 0]
                if Fa[s]:
                    if año == 2026:
                        pix += [int(q) for q in U.cola_anillo(X.A, d, s)]
                    else:
                        idx = np.flatnonzero(M.SEC == X.A.KR[d, s])
                        v = (X.A.mmR[d, s] - X.A.base(d)[s])[idx]
                        o = np.argsort(np.where(np.isfinite(v), v, np.inf))[:M.NCOLA]
                        pix += [int(q) for q in M.AP[idx[o]]]
                if pix:
                    ev.append((d, j, pix, bool(Fz[s]), bool(Fa[s])))
        return ev, evaluados
    ev26, eval26 = eventos(2026)
    ev25, eval25 = eventos(2025)
    print(f"eventos nocturnos: 2026 {len(ev26)}, 2025 {len(ev25)}; {time.time() - t:.0f} s", flush=True)
    esperar_viento()
    W26, W25 = viento_noche(T0_26, ND26), viento_noche(T0_25, ND25)
    falta = {"2026": int(np.isnan(W26[..., 0]).sum()), "2025": int(np.isnan(W25[..., 0]).sum())}
    e26 = [(d, j, p) for d, j, p, *_ in ev26]
    e25 = [(d, j, p) for d, j, p, *_ in ev25]
    P = {"poder_pluma_ideal": poder_P(eval26, W26),
         "2026": prueba_P(e26, W26), "2025": prueba_P(e25, W25),
         "2026_solo_zona": prueba_P([(d, j, p[:2]) for d, j, p, fz, fa in ev26 if fz], W26),
         "2026_solo_anillo": prueba_P([(d, j, p[-8:]) for d, j, p, fz, fa in ev26 if fa], W26),
         "sensibilidad_h": {str(h): {"2026": prueba_P(e26, W26, h), "2025": prueba_P(e25, W25, h)} for h in H_SENS},
         "cuadros_nocturnos_sin_viento": falta}
    pod, p26, p25 = P["poder_pluma_ideal"], P["2026"], P["2025"]
    if pod["p_corrimiento"] is None or pod["p_corrimiento"] > 0.01:
        verP = "SIN PODER (no decidible)"
    elif p26["cuadros"] < MIN_CUADROS_P or p26["noches"] < MIN_NOCHES_P:
        verP = "NO DECIDIBLE (pocos cuadros)"
    elif p26["p_corrimiento"] <= 0.05 and p25["p_corrimiento"] is not None and p25["p_corrimiento"] > 0.05 \
            and p26["giro_max_phi"] in (0, 30, 330):
        verP = "PLUMA SÍ"
    elif p26["p_corrimiento"] <= 0.05 and p25["p_corrimiento"] is not None and p25["p_corrimiento"] <= 0.05:
        verP = "NO DECIDIBLE (el viento también ordena 2025)"
    elif p26["p_corrimiento"] > 0.20:
        verP = "PLUMA NO"
    else:
        verP = "NO DECIDIBLE"
    P["veredicto"] = verP
    print("P:", verP, json.dumps({k: P[k] for k in ("2026", "2025")}, default=str), flush=True)

    # ---- N: Antuco y Longaví ----
    btd25 = np.load(Z._npy("r25_btd"))
    acm25 = np.load(Z._npy("r25_acm"))
    est25 = Z.costumbre(acm25, np.isfinite(btd25[:, :, Z.ZONA[0]]))
    btd26 = np.concatenate([np.load(os.path.join(B.TRAB, "dev_btd.npy")), np.load(Z._npy("n26_btd"))])
    acm26 = np.concatenate([np.load(os.path.join(B.TRAB, "dev_acm.npy")),
                            np.load(os.path.join(B.TRAB, "nuevo_acm.npy"))])
    est26 = X.est26
    ch = Zona("chillan", Z.ZONA, M.AP, Z.CTRL).correr(btd25, acm25, est25, btd26, acm26, est26, "chillan")
    repro_z = bool(np.array_equal(ch.SR, X.SRz, equal_nan=True) and np.array_equal(ch.ST, X.STz, equal_nan=True))
    print(f"zona generalizada reproduce la de Partes: {repro_z}; {time.time() - t:.0f} s", flush=True)
    if not repro_z:
        sys.exit("la zona generalizada no reproduce: error de código")
    sch, bch = ch.disparos()
    N = {"chillan_zona": {"2025": tasa_noche(sch), "2026": tasa_noche(bch)}}
    fr_ch = frac_por_noche(bch, 6)
    ctl = {}
    for sitio, (la, lo) in SITIOS.items():
        zona, anillo, ctrl, _ = zona_de(la, lo)
        zv = Zona(sitio, zona, anillo, ctrl).correr(btd25, acm25, est25, btd26, acm26, est26, sitio)
        s_, b_ = zv.disparos()
        F25, E25 = tasa_noche(s_)
        F26, E26 = tasa_noche(b_)
        r25, r26 = F25 / E25 if E25 else np.nan, F26 / E26 if E26 else np.nan
        pf = float(stats.fisher_exact([[F26, E26 - F26], [F25, E25 - F25]], alternative="greater")[1]) if E25 and E26 \
            else None
        fr = frac_por_noche(b_, 6)
        k = np.isfinite(fr) & np.isfinite(fr_ch)
        rho = stats.spearmanr(fr[k], fr_ch[k]) if k.sum() >= 8 else None
        ctl[sitio] = {"pixeles_zona": len(zona), "controles": len(ctrl), "2025": [F25, E25], "2026": [F26, E26],
                      "tasa_2025": r25, "tasa_2026": r26, "R": r26 / r25 if r25 else None, "p_fisher": pf,
                      "spearman_noche_con_chillan": None if rho is None else [float(rho[0]), float(rho[1]), int(k.sum())],
                      "dia_tasa_2025": tasa_dia(s_), "dia_tasa_2026": tasa_dia(b_)}
        print(sitio, json.dumps(ctl[sitio], default=float), flush=True)
    N["controles"] = ctl
    ok_n = all(min(v["2025"][1], v["2026"][1]) >= 300 for v in ctl.values())
    si = all(v["R"] is not None and v["R"] >= 3 and v["p_fisher"] <= 0.01 for v in ctl.values())
    no = all(v["R"] is None or v["R"] <= 1.5 or v["p_fisher"] > 0.05 for v in ctl.values())
    N["veredicto"] = ("NO DECIDIBLE (pocos cuadros)" if not ok_n else "NIEVE SÍ" if si else "NIEVE NO" if no
                      else "NO DECIDIBLE")
    tn = np.array([np.nanmean(W26[d, :, 2]) for d in range(ND26)])
    k = np.isfinite(tn) & np.isfinite(fr_ch)
    N["spearman_chillan_T700"] = [float(x) for x in stats.spearmanr(tn[k], fr_ch[k])] + [int(k.sum())]
    print("N:", N["veredicto"], flush=True)

    # ---- D: depósito ----
    cuenta = np.zeros(len(Z.ZONA), int)
    cuenta_mitad = [np.zeros(len(Z.ZONA), int), np.zeros(len(Z.ZONA), int)]
    corte = (datetime(2026, 10, 23) - T0_26).days
    for d in range(ND26):
        Fz, _ = res[d]["z"]
        for s in NOCHE:
            if Fz[s] and CL[d, s] != "P":
                for q in X.PTz[d, s]:
                    if q >= 0:
                        cuenta[q] += 1
                        cuenta_mitad[int(d >= corte)][q] += 1
    dom = list(np.argsort(-cuenta)[:3])
    dom1, dom2 = (list(np.argsort(-c)[:3]) for c in cuenta_mitad)
    D2 = len(set(dom1) & set(dom2)) >= 2
    frz = frac_por_noche([res[d]["z"] for d in range(ND26)], 12)
    D3_med = float(np.nanmedian(frz))
    D3 = D3_med >= 0.5
    desp = ch.G26 & ch.E126
    A = ch.A26[:, :, dom]                              # (nd, 144, 3)
    noc = [A[d, s] for d in range(ND26) for s in NOCHE if desp[d, s]]
    dia = [A[d, s] for d in range(ND26) for s in DIA_D4 if desp[d, s]]
    med_n = float(np.nanmedian(np.array(noc))) if noc else np.nan
    med_d = float(np.nanmedian(np.array(dia))) if dia else np.nan
    D4 = np.isfinite(med_d) and med_d <= -0.3 and med_d <= med_n + 0.2
    D1 = verP != "PLUMA SÍ"
    verD = ("DEPÓSITO SÍ" if (D1 and D2 and D3 and D4) else "DEPÓSITO NO" if (not D3 and not D4)
            else "NO DECIDIBLE")
    # descriptivo: crecimiento y exposición
    serie = []
    for d in range(ND26):
        v = [A[d, s] for s in NOCHE if desp[d, s]]
        serie.append(float(np.nanmedian(np.array(v))) if v else np.nan)
    serie = np.array(serie)
    k = np.isfinite(serie)
    crec = stats.spearmanr(np.arange(ND26)[k], serie[k]) if k.sum() >= 8 else None
    # exposición: días previos con viento de tarde hacia cada píxel dominante (±45°), por paralaje a h_ref
    x, y = pos(H_REF)
    expo = {}
    for q in dom:
        p = Z.ZONA[q]
        az = (math.degrees(math.atan2(x[p], y[p])) + 360.0) % 360.0
        hacia = []
        for d in range(ND26):
            n_ = 0
            for hh in (12, 15, 18, 21):
                r = hora(T0_26 + timedelta(days=d, hours=hh))
                if r is not None and math.hypot(r[0], r[1]) >= VMIN:
                    tw = (math.degrees(math.atan2(r[0], r[1])) + 360.0) % 360.0
                    n_ += abs((tw - az + 180) % 360 - 180) <= 45
            hacia.append(n_)
        acum = np.cumsum([0] + hacia[:-1])
        serie_p = np.array([np.nanmedian(np.array([ch.A26[d, s, q] for s in NOCHE if desp[d, s]]))
                            if desp[d, NOCHE].any() else np.nan for d in range(ND26)])
        kk = np.isfinite(serie_p)
        r_ = stats.spearmanr(acum[kk], serie_p[kk]) if kk.sum() >= 8 else None
        expo[f"{p // M.NX},{p % M.NX}"] = {"rumbo_desde_crater": round(az, 1), "tardes_hacia": int(sum(hacia)),
                                         "spearman_exposicion_vs_A": None if r_ is None else
                                         [float(r_[0]), float(r_[1]), int(kk.sum())]}
    # duración: rachas de disparo dentro de la noche (unión, fuera de VOLCAT)
    rachas = []
    for d in range(ND26):
        F, _ = res[d]["u"]
        n_ = 0
        for s in NOCHE:
            if F[s] and CL[d, s] != "P":
                n_ += 1
            elif n_:
                rachas.append(n_)
                n_ = 0
        if n_:
            rachas.append(n_)
    D = {"dominantes": [f"{Z.ZONA[q] // M.NX},{Z.ZONA[q] % M.NX}" for q in dom],
         "cuenta_por_pixel": {f"{p // M.NX},{p % M.NX}": int(c) for p, c in zip(Z.ZONA, cuenta)},
         "D1_sin_viento": D1,
         "D2_fijo": {"primera_mitad": [f"{Z.ZONA[q] // M.NX},{Z.ZONA[q] % M.NX}" for q in dom1],
                     "segunda_mitad": [f"{Z.ZONA[q] // M.NX},{Z.ZONA[q] % M.NX}" for q in dom2], "cumple": D2},
         "D3_toda_la_noche": {"mediana_fraccion_por_noche": D3_med, "noches": int(np.isfinite(frz).sum()),
                              "cumple": D3},
         "D4_de_dia": {"mediana_A_dia_15_21UTC": med_d, "mediana_A_noche": med_n, "n_dia": len(dia),
                       "n_noche": len(noc), "cumple": bool(D4)},
         "crecimiento_spearman_fecha_vs_A": None if crec is None else [float(crec[0]), float(crec[1]), int(k.sum())],
         "exposicion": expo,
         "rachas_cuadros": {"n": len(rachas), "mediana": float(np.median(rachas)) if rachas else None,
                            "p90": float(np.percentile(rachas, 90)) if rachas else None,
                            "max": int(max(rachas)) if rachas else None},
         "veredicto": verD}
    print("D:", verD, flush=True)
    out = {"criterio": "criterio_2026-11-25.md (2c7af2b)", "percentil": PSTAR,
           "comprobacion": {"seco_union_2025": [seco_u["disparos"], seco_u["evaluados"]],
                            "diferencias_tabla_2026": dif, "zona_generalizada_reproduce": repro_z},
           "eventos_nocturnos": {"2026_fuera_de_VOLCAT": len(ev26), "2025": len(ev25),
                                 "2026_zona": sum(1 for e in ev26 if e[3]), "2026_anillo": sum(1 for e in ev26 if e[4])},
           "P": P, "N": N, "D": D}
    json.dump(out, open(os.path.join(RES, "s27a_resultado.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1,
              default=lambda o: o.item() if hasattr(o, "item") else str(o))
    # cuadros para el video y el informe (en D:)
    with open(os.path.join(TRAB, "cuadros_noche_2026.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["dia", "hora", "zona", "anillo", "pixeles", "rumbo_obs", "dist_km", "theta_w", "V", "T700"])
        for d, j, pix, fz, fa in ev26:
            th, r = rumbo_centroide(np.asarray(pix), H_REF)
            w.writerow([f"{T0_26 + timedelta(days=d):%Y-%m-%d}", M.hhmm(NOCHE[j]), int(fz), int(fa),
                        ";".join(map(str, pix)), round(th, 1), round(r, 2)] + [round(float(x), 2) for x in W26[d, j]])
    print(f"listo en {time.time() - t:.0f} s", flush=True)


def esperar_viento(quieto_min=10):
    """Espera a que s27a_viento.py termine: todos los archivos, o ninguno nuevo en quieto_min minutos."""
    sys.path.insert(0, AQUI)
    import s27a_viento as V
    faltan = [h for h in V.horas_todo() if not os.path.exists(V.ruta(h))]
    ult, n_ant = time.time(), len(faltan)
    while faltan and time.time() - ult < 60 * quieto_min:
        time.sleep(30)
        faltan = [h for h in faltan if not os.path.exists(V.ruta(h))]
        if len(faltan) < n_ant:
            ult, n_ant = time.time(), len(faltan)
    print(f"viento: faltan {len(faltan)} horas", [f"{h:%Y%m%d%H}" for h in faltan[:10]], flush=True)


def tasa_dia(lista):
    F = sum(int(F[72:144].sum()) for F, _ in lista)
    E = sum(int(ev[72:144].sum()) for _, ev in lista)
    return [F, E]


if __name__ == "__main__":
    {"medir": medir}[sys.argv[1]]()
