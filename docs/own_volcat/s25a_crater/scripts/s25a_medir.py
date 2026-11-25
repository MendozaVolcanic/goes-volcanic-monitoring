r"""S25a: regla para la zona de 0 a 4 km del cráter de Nevados de Chillán, que ningún anillo mira.
Implementa criterio_2026-11-25.md (commit 1306fb5, empujado antes de calcular un solo valor de BTD en la zona).

Por qué así: en la cumbre el par por cota y BT11 del M1 de S22a no vale (relieve propio, calor desde el 24-10), así que
cada píxel se compara consigo mismo a la misma hora en oct-nov 2025 (año tranquilo), se le resta lo que cambió en toda
la región (controles lejanos de su cota) y el cuadro se resume con los dos píxeles más bajos: el píxel caliente sube
la BTD y nunca es el mínimo, así que no puede fabricar un disparo.

Uso: python -I s25a_medir.py pruebas | cubo | medir
  cubo   arma BTD y ACM de todos los píxeles de 2025 (desde la bajada de S22d) y de 22 a 24-11-2026, con I1 a I3.
  medir  ensayo en seco y poder en 2025, después los P de VOLCAT de 2026. Escribe resultados/s25a_resultado.json y
         la tabla por cuadro de 2026 en D: (para los videos).
Lo grande queda en D:\goes_notas\s25\s25a; al repo sólo van cifras.
"""
import csv
import json
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
RES = os.path.join(os.path.dirname(AQUI), "resultados")
sys.path.insert(0, os.path.join(OV, "s23_fondo_2025", "scripts"))
import s23_medir as S  # noqa: E402  (poisson_binomial_cola, azar_por_hora, W_AZAR)
B, M, H24, C29 = S.B, S.M, S.H24, S.C29

TRAB = r"D:\goes_notas\s25\s25a"
REF = S.REF                               # D:\goes_notas\s22\s22d_2025
T0R, NR = S.T0R, S.NR                     # 21-09-2025, 62 días
NPIX = S.NPIX
ESTAT26 = r"D:\goes_notas\s23\s23b\estat_2026.npy"
SHA_ESTAT26 = "e0f093eb6e441cc4"

# ---------- parámetros del criterio (§1, §2) ----------
ZONA = np.flatnonzero(((C29.DIST < 4.0) | M.BLOQUE).ravel())     # 11 píxeles
R_CTRL, COTA_M, MIN_CTRL = 45.0, 300.0, 20
MIN_ZONA, NBAJOS = 6, 2
SECO_MAX = 0.05
R_MIN, P25_MAX, PN_MAX, MIN_P_EVAL = 0.25, 0.01, 0.05, 10
DIA14_MIN, DIA14_P = 3, 0.01
FIRMAS, N_POD, SEMILLA, N_INY = (0.33, 0.97), 200, 0, 2
ZDEM = C29.ZDEM.ravel()
CTRL = np.flatnonzero((C29.DIST > R_CTRL).ravel())
CTRL_P = [np.flatnonzero(np.abs(ZDEM[CTRL] - ZDEM[p]) <= COTA_M) for p in ZONA]   # índices dentro de CTRL


def _npy(n):
    return os.path.join(TRAB, f"{n}.npy")


# ---------- cubos ----------
def _leer(carpeta, t0, ndias, co_fijo=None):
    n = ndias * 144
    r = {b: np.full((n, NPIX), np.nan, "float32") for b in (14, 15)}
    acm = np.full((n, NPIX), 255, "uint8")
    co = {14: [], 15: []}
    pres, scan_dist, n_acm, ult = 0, 0, 0, -1
    for i in range(n):
        dt = t0 + timedelta(minutes=10 * i)
        f = os.path.join(carpeta, "l1b", f"{dt:%Y%m%d_%H%M}.npz")
        if os.path.exists(f):
            with np.load(f) as z:
                s14, s15 = str(z["key14"]).split("_s")[1][:14], str(z["key15"]).split("_s")[1][:14]
                if s14 != s15 or s14[:11] != f"{dt:%Y}{dt.timetuple().tm_yday:03d}{dt:%H%M}":
                    scan_dist += 1
                else:
                    for b in (14, 15):
                        r[b][i] = z[f"rad{b}"].ravel()
                        co[b].append(z[f"co{b}"])
                    pres += 1
                    ult = i
        g = os.path.join(carpeta, "acm", f"{dt:%Y%m%d_%H%M}.npz")
        if os.path.exists(g):
            with np.load(g) as z:
                acm[i] = z["acm"].ravel()
                n_acm += 1
    cof = co_fijo if co_fijo is not None else {b: np.median(np.array(co[b]), 0) for b in (14, 15)}
    bt11 = C29.bt_de_rad(r[14].astype("float64"), cof[14]).astype("float32")
    btd = (bt11 - C29.bt_de_rad(r[15].astype("float64"), cof[15])).astype("float32")
    hay = np.isfinite(bt11).any(1)
    cong = sum(1 for i in range(1, n) if hay[i] and hay[i - 1] and np.array_equal(r[14][i], r[14][i - 1], equal_nan=True))
    v = bt11[np.isfinite(bt11)]
    inst = {"cuadros": n, "l1b_presentes": pres, "cobertura_l1b": pres / n, "acm_presentes": n_acm,
            "cobertura_acm": n_acm / n, "scan_distinto_descartados": scan_dist, "congelados": cong,
            "bt11_en_rango": float(((v > 180) & (v < 330)).mean()) if v.size else 0.0, "ultimo_l1b": ult}
    return btd.reshape(ndias, 144, NPIX), acm.reshape(ndias, 144, NPIX), inst


def cubo():
    os.makedirs(TRAB, exist_ok=True)
    t = time.time()
    btd, acm, inst = _leer(REF, T0R, NR)
    inst["falla"] = [k for k, ok in (("I1", inst["cobertura_l1b"] >= S.I1_MIN and inst["cobertura_acm"] >= S.I1_MIN),
                                     ("I2", True),   # los cuadros de scan distinto se descartan (S23a)
                                     ("I3", inst["bt11_en_rango"] >= S.I3_MIN and inst["congelados"] == 0)) if not ok]
    np.save(_npy("r25_btd"), btd)
    np.save(_npy("r25_acm"), acm)
    print("2025:", json.dumps(inst), f"{time.time() - t:.0f} s", flush=True)
    co26 = np.load(os.path.join(B.TRAB, "dev_co.npy"))
    btdn, _, instn = _leer(B.TRAB, datetime(2026, 11, 22), 3, co_fijo={14: co26[0], 15: co26[1]})
    np.save(_npy("n26_btd"), btdn)
    print("22-24-11-2026:", json.dumps(instn), flush=True)
    os.makedirs(RES, exist_ok=True)
    json.dump({"2025": inst, "2026_22a24nov": instn}, open(os.path.join(RES, "instrumento.json"), "w",
                                                             encoding="utf-8"), indent=1)


# ---------- la regla ----------
def costumbre(acm, usar):
    """Nublado de costumbre por hora (S22b enmienda 1) con los cuadros usar[d, s] despejados por E1."""
    e1 = H24.despejada("chillan", acm)
    sel = [(d, s) for d in range(acm.shape[0]) for s in range(144) if usar[d, s] and e1[d, s]]
    nub = np.array([(acm[d, s] >= 2) & (acm[d, s] <= 3) for d, s in sel])
    ss = np.array([s for _, s in sel])
    est = np.zeros((144, NPIX), bool)
    for s in range(144):
        dd = np.abs(ss - s) % 144
        dd = np.minimum(dd, 144 - dd)
        for w in B.COSTUMBRE_VENT:
            m = dd <= w
            if m.sum() >= B.MIN_COSTUMBRE:
                est[s] = nub[m].mean(0) >= B.COSTUMBRE
                break
    return est


def nubes(acm, est):
    """FD (fracción del anillo con nube dinámica) y la máscara dinámica por cuadro (sin borde: sólo para controles)."""
    nd_, ns = acm.shape[:2]
    FD = np.full((nd_, ns), np.nan)
    DIN = np.zeros((nd_, ns, len(CTRL)), bool)
    for d in range(nd_):
        for s in range(ns):
            if not (acm[d, s] != 255).any():
                continue
            nd = B.dinamica(acm[d, s], est[s])
            FD[d, s] = nd[M.AP].mean()
            DIN[d, s] = nd[CTRL]
    return FD, DIN


def base(btd, usar, pix=None, excl=None):
    """Mediana por píxel y hora (±90 min) de los cuadros usar (despejados por E1 y con compuerta), mín 8 valores."""
    pix = np.arange(NPIX) if pix is None else pix
    Bs = np.full((144, len(pix)), np.nan, np.float32)
    dd_, ss_ = np.nonzero(usar)
    if excl is not None:
        k = dd_ != excl
        dd_, ss_ = dd_[k], ss_[k]
    for s in range(144):
        x = np.abs(ss_ - s) % 144
        m = np.minimum(x, 144 - x) <= B.W_BASE
        if m.sum() < B.MIN_BASE:
            continue
        R = btd[dd_[m], ss_[m]][:, pix]
        n = np.isfinite(R).sum(0)
        Bs[s] = np.where(n >= B.MIN_BASE, np.nanmedian(R, 0), np.nan)
    return Bs


def regional(btd, DIN, bctrl):
    """c_p(t) por píxel de la zona: mediana de la anomalía de los controles de su cota sin nube dinámica (§2.2)."""
    nd_ = btd.shape[0]
    C = np.full((nd_, 144, len(ZONA)), np.nan, np.float32)
    for d in range(nd_):
        a = btd[d][:, CTRL] - bctrl            # (144, nctrl)
        a[DIN[d]] = np.nan
        for j, idx in enumerate(CTRL_P):
            sub = a[:, idx]
            n = np.isfinite(sub).sum(1)
            C[d, :, j] = np.where(n >= MIN_CTRL, np.nanmedian(sub, 1), np.nan)
    return C


def estadistico(A):
    """S y los dos píxeles (índices en ZONA) de un cuadro; NaN si hay menos de 6 píxeles con A."""
    ok = np.isfinite(A)
    if ok.sum() < MIN_ZONA:
        return np.nan, (-1, -1)
    o = np.argsort(np.where(ok, A, np.inf))[:NBAJOS]
    return float(A[o].mean()), (int(o[0]), int(o[1]))


def tabla_S(Z, C, bz, gate):
    """S (nd, 144) y pares (nd, 144, 2) con la base de la zona bz (144, 11) o (nd, 144, 11)."""
    nd_ = Z.shape[0]
    Sx = np.full((nd_, 144), np.nan)
    Px = np.full((nd_, 144, 2), -1, int)
    for d in range(nd_):
        bd = bz[d] if bz.ndim == 3 else bz
        A = Z[d] - bd - C[d]
        for s in range(144):
            if gate[d, s]:
                Sx[d, s], Px[d, s] = estadistico(A[s])
    return Sx, Px


def umbral(Sx, excl=None):
    ds, ss = np.nonzero(np.isfinite(Sx))
    if excl is not None:
        k = ds != excl
        ds, ss = ds[k], ss[k]
    vs = Sx[ds, ss]
    U = [None] * 144
    for s in range(144):
        x = np.abs(ss - s) % 144
        dd = np.minimum(x, 144 - x)
        for w in B.VENTANAS_U:
            m = dd <= w
            n = int(m.sum())
            if n < B.MIN_POZO:
                continue
            _, cnt = np.unique(ds[m], return_counts=True)
            if len(cnt) >= B.MIN_DIAS_U and cnt.max() / n <= B.MAX_FRAC_U:
                U[s] = float(np.percentile(vs[m], B.PCT_U))
                break
    return U


def disparos(Sx, d, U, Uprev=None):
    """F y evaluado de un día; el cuadro anterior a las 00:00 es el último del día previo (§2.6)."""
    Uprev = U if Uprev is None else Uprev
    F = np.zeros(144, bool)
    ev = np.zeros(144, bool)
    for s in range(144):
        if U[s] is None or not np.isfinite(Sx[d, s]):
            continue
        ev[s] = True
        dp, sp = (d, s - 1) if s else (d - 1, 143)
        Up = U if s else Uprev
        if dp < 0 or Up[sp] is None or not np.isfinite(Sx[dp, sp]):
            continue
        F[s] = Sx[d, s] <= U[s] and Sx[dp, sp] <= Up[sp]
    return F, ev


def _r(x):
    return None if (x is None or not np.isfinite(x)) else round(float(x), 5)


# ---------- medir ----------
def medir():
    t = time.time()
    btd25 = np.load(_npy("r25_btd"), mmap_mode="r")
    acm25 = np.load(_npy("r25_acm"))
    hay25 = np.isfinite(btd25[:, :, ZONA[0]])
    est25 = costumbre(acm25, hay25)
    FD25, DIN25 = nubes(acm25, est25)
    G25 = FD25 <= B.G_MAX
    E125 = H24.despejada("chillan", acm25)
    USA25 = G25 & E125 & hay25
    btd25 = np.asarray(btd25)
    bctrl = base(btd25, USA25, CTRL)                       # controles: con los 62 días (§2)
    C25 = regional(btd25, DIN25, bctrl)
    print(f"2025 listo en {time.time() - t:.0f} s; cuadros con compuerta {int(G25.sum())}", flush=True)
    # base de la zona y S sin el día que se evalúa
    IZ = np.arange(len(ZONA))
    Z25 = np.ascontiguousarray(btd25[:, :, ZONA])
    BZ = np.array([base(Z25, USA25, IZ, excl=d) for d in range(NR)])        # (62, 144, 11)
    SR, PR = tabla_S(Z25, C25, BZ, G25)
    UL = [umbral(SR, excl=d) for d in range(NR)]
    # ensayo en seco y azar por hora
    sl25, al25, fa_dia, nF, nE, noche = [], [], [], 0, 0, [0, 0]
    for d in range(NR):
        F, ev = disparos(SR, d, UL[d], UL[d - 1] if d else None)
        nF += int(F.sum())
        nE += int(ev.sum())
        if ev.sum():
            fa_dia.append(F.sum() / ev.sum())
        for s in np.flatnonzero(ev):
            sl25.append(s)
            al25.append(B.alcanzado(F, ev, s)[1])
        noche[0] += int(F[18:54].sum())
        noche[1] += int(ev[18:54].sum())
    seco = nF / nE
    r25 = S.azar_por_hora(sl25, al25)
    print(f"seco {seco:.4f} ({nF} de {nE}); media por día {np.mean(fa_dia):.4f}", flush=True)
    # poder por inyección
    rng = np.random.default_rng(SEMILLA)
    pares = [(d, s) for d in range(NR) for s in range(1, 144)
             if np.isfinite(SR[d, s]) and np.isfinite(SR[d, s - 1]) and UL[d][s] is not None and UL[d][s - 1] is not None]
    elig = rng.choice(len(pares), size=min(N_POD, len(pares)), replace=False)
    poder = {}
    for firma in FIRMAS:
        hits = 0
        for i in elig:
            d, s = pares[i]
            px = rng.choice(len(ZONA), size=N_INY, replace=False)
            ok = True
            for x in (s - 1, s):
                A = Z25[d, x] - BZ[d, x] - C25[d, x]
                A = A.copy()
                A[px] -= firma
                v, _ = estadistico(A)
                ok &= bool(np.isfinite(v) and v <= UL[d][x])
            hits += ok
        poder[str(firma)] = hits / len(elig)
    print("poder", poder, flush=True)
    U25 = umbral(SR)

    # ---------- 2026 ----------
    import hashlib
    est26 = np.load(ESTAT26)
    assert hashlib.sha256(est26.tobytes()).hexdigest()[:16] == SHA_ESTAT26, "estat_2026 no es el congelado"
    btd26 = np.concatenate([np.load(os.path.join(B.TRAB, "dev_btd.npy")), np.load(_npy("n26_btd"))])
    acm26 = np.concatenate([np.load(os.path.join(B.TRAB, "dev_acm.npy")), np.load(os.path.join(B.TRAB, "nuevo_acm.npy"))])
    FD26, DIN26 = nubes(acm26, est26)
    G26 = FD26 <= B.G_MAX
    C26 = regional(btd26, DIN26, bctrl)
    bz = base(Z25, USA25, IZ)
    ST, PT = tabla_S(btd26[:, :, ZONA], C26, bz, G26)
    CL = B.clases()
    ND = CL.shape[0]
    assert ND == btd26.shape[0], (ND, btd26.shape)
    P, N, por_dia, eps_t, eps_h = [], [], [], 0, 0
    filas = []
    for d in range(ND):
        F, ev = disparos(ST, d, U25)
        for s in range(144):
            if CL[d, s] or ev[s]:
                filas.append([B.fecha(d), M.hhmm(s), CL[d, s], _r(ST[d, s]), _r(U25[s]) if U25[s] is not None else None,
                              int(F[s]), int(ev[s]), int(PT[d, s, 0]), int(PT[d, s, 1]), _r(FD26[d, s])])
        for s in np.flatnonzero(ev):
            a = B.alcanzado(F, ev, s)[1]
            if CL[d, s] == "P":
                P.append((d, s, a))
            elif CL[d, s] == "N":
                N.append((d, s, a))
        Ps = np.flatnonzero(CL[d] == "P")
        for ep in (M.episodios(list(Ps)) if len(Ps) else []):
            if ev[ep].any():
                eps_t += 1
                eps_h += bool(F[max(0, ep[0] - 3):min(144, ep[-1] + 4)].any())
        if len(Ps) or F.any():
            pe = [a for dd, _, a in P if dd == d]
            por_dia.append({"dia": B.fecha(d), "P": int(len(Ps)), "P_evaluados": len(pe), "P_alcanzados": int(sum(pe)),
                            "N_evaluados": int(sum(1 for dd, *_ in N if dd == d)),
                            "N_con_disparo": int(sum(F[s] for dd, s, _ in N if dd == d)),
                            "disparos": int(F.sum()), "horas_disparos": [M.hhmm(s) for s in np.flatnonzero(F)]})
    te, th = len(P), int(sum(a for *_, a in P))
    p25 = S.poisson_binomial_cola([r25[s] for _, s, _ in P], th) if te else None
    psl = {s for _, s, _ in P}
    cerca = [a for _, s, a in N if any(M.dslot(s, x) <= S.W_AZAR for x in psl)]
    pN = (float(stats.fisher_exact([[th, te - th], [int(sum(cerca)), len(cerca) - int(sum(cerca))]],
                                   alternative="greater")[1]) if te and cerca else None)
    R = th / te if te else None
    dias_alc = len({d for d, _, a in P if a})
    dias_ev = len({d for d, _, _ in P})
    if seco > SECO_MAX:
        ver = "NO SIRVE"
    elif te < MIN_P_EVAL or dias_ev < 2:
        ver = "NO DECIDIBLE"
    elif p25 <= P25_MAX and pN is not None and pN <= PN_MAX and R >= R_MIN and dias_alc >= 2:
        ver = "ALCANZA"
    elif p25 <= P25_MAX:
        ver = "PARCIAL"
    else:
        ver = "NO ALCANZA"
    d14 = B.dia_idx("2026-11-14")
    P14 = [(s, a) for d, s, a in P if d == d14]
    h14 = int(sum(a for _, a in P14))
    p14 = S.poisson_binomial_cola([r25[s] for s, _ in P14], h14) if P14 else None
    ver14 = "14-11 ALCANZADO" if (P14 and h14 >= DIA14_MIN and p14 <= DIA14_P) else "14-11 no alcanzado"
    # tasa de disparo: N de 2026 contra 2025 (pluma diaria o depósito)
    fN = sum(1 for d, s, _ in N if disparos(ST, d, U25)[0][s])
    inst = json.load(open(os.path.join(RES, "instrumento.json"), encoding="utf-8"))
    if inst["2025"]["falla"]:
        ver = "INVÁLIDA"
    out = {"veredicto": ver, "veredicto_14_11": ver14,
           "seco": {"fraccion": seco, "disparos": nF, "evaluados": nE, "media_por_dia": float(np.mean(fa_dia)),
                    "noche_03_09_UTC": {"disparos": noche[0], "evaluados": noche[1]}, "max": SECO_MAX},
           "poder": poder, "cuadros_2025_con_compuerta": int(G25.sum()),
           "umbral_por_hora": {M.hhmm(s): _r(U25[s]) if U25[s] is not None else None for s in range(0, 144, 6)},
           "P_total": int((CL == "P").sum()), "P_evaluados": te, "P_alcanzados": th, "R": R,
           "dias_con_P_evaluado": dias_ev, "dias_con_P_alcanzado": dias_alc,
           "E25": float(sum(r25[s] for _, s, _ in P)), "p25": p25,
           "N_cerca_de_P": len(cerca), "N_cerca_alcanzados": int(sum(cerca)), "pN": pN,
           "N_2026_evaluados": len(N), "N_2026_con_disparo": fN,
           "tasa_N_2026": fN / len(N) if N else None, "tasa_2025": seco,
           "episodios": eps_t, "episodios_alcanzados": eps_h,
           "dia_14_11": {"P_evaluados": len(P14), "P_alcanzados": h14, "p25": p14},
           "por_dia": por_dia}
    os.makedirs(RES, exist_ok=True)
    json.dump(out, open(os.path.join(RES, "s25a_resultado.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    with open(os.path.join(TRAB, "tabla_2026.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["dia", "hora", "clase", "S", "U", "F", "evaluado", "px1", "px2", "FD"])
        w.writerows(filas)
    with open(os.path.join(RES, "s25a_P_por_cuadro.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["dia", "hora", "clase", "S", "U", "F", "evaluado", "px1", "px2", "FD"])
        w.writerows([x for x in filas if x[2] == "P"])
    print(json.dumps({k: v for k, v in out.items() if k != "por_dia"}, ensure_ascii=False, indent=1))


# ---------- pruebas de código ----------
def pruebas():
    assert len(ZONA) == 11, len(ZONA)
    assert all(len(c) >= 200 for c in CTRL_P)
    A = np.array([0.0, -1.0, 2.0, -3.0, np.nan, 1.0, 0.5])
    v, p = estadistico(A)
    assert abs(v - (-2.0)) < 1e-12 and set(p) == {1, 3}
    assert np.isnan(estadistico(np.array([0.0] * 5 + [np.nan] * 6))[0])
    # persistencia: dos cuadros seguidos bajo el umbral, cruzando la medianoche
    Sx = np.zeros((2, 144))
    U = [-1.0] * 144
    Sx[0, 143] = Sx[1, 0] = -2.0
    F, ev = disparos(Sx, 1, U)
    assert F[0] and ev.all() and F.sum() == 1
    Sx[0, 143] = 0.0
    assert not disparos(Sx, 1, U)[0][0]
    # base: excluye el día y exige 8 valores
    btd = np.zeros((3, 144, NPIX), np.float32)
    btd[1] = 5.0
    usar = np.ones((3, 144), bool)
    b = base(btd, usar, ZONA[:2], excl=1)
    assert np.allclose(b, 0.0)
    print("pruebas OK")


if __name__ == "__main__":
    {"pruebas": pruebas, "cubo": cubo, "medir": medir}[sys.argv[1]]()
