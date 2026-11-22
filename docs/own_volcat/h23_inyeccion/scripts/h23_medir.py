r"""H23: inyeccion y recuperacion. Implementa el criterio_2026-11-22.md con la enmienda post hoc 1
(enmienda_posthoc_1_2026-11-22.md): escena despejada segun la mascara de nubes de NOAA en el terreno bajo del
volcan (E1), linea base del mismo pixel con los otros dias despejados del bloque (E2), poblaciones A, B y C (E3),
todos los dias del bloque como dias de prueba (E4); detectores D1 a D5 (§5), metricas por celda (§6),
comprobaciones de instrumento I4 a I6 y controles (§7), y las secundarias S1 a S4 (§8) como en el criterio.

Por que asi: la pregunta es cuanta ceniza hace falta para ganarle al fondo real de la cumbre. El fondo real se
toma de los mismos pixeles en escenas sin inyectar; la capa se pinta con I' = (1 - e) I + e B(T_tope) sobre la
radiancia observada, de modo que el ruido, el terreno y el tiempo atmosferico son los reales.

Salidas (resultados\): h23_celdas.csv (una fila por celda), h23_instrumento.json, h23_controles.json,
h23_eventos.json. Uso: python -I h23_medir.py
"""
import csv
import glob
import json
import os
import sys
import warnings
from datetime import datetime, timedelta

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import h23_comun as K  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
RES = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "resultados")
NP_ = K.NY * K.NX
LAT, LON = (np.load(K.LATLON)[k].ravel() for k in ("lat", "lon"))
ZDEM = np.load(K.DEM)["zdem"].ravel()

EPS = [0.0, 0.05, 0.10, 0.15, 0.20, 0.30, 0.50, 0.90]
ALTURAS = [3000.0, 4000.0, 5000.0]
Z_CONTROL = 10000.0
BETA, BETAS_SENS = 0.70, [0.55, 0.95]
MIN_DIAS_REF = 3                                # dias despejados distintos que pide la linea base (E2)
UMBRAL_DESPEJADO, FRAC_DESPEJADO = -5.0, 0.80   # D1 del oraculo (poblacion C); fraccion de terreno bajo despejado (E1)
MIN_N, MIN_DIAS, NBOOT = 500, 8, 2000
DET = ["D1", "D2", "D3", "D4", "D5"]
ESPEJO = {"D1", "D2", "D4"}        # se evalua en los dos sentidos (criterio §5, "Signo")
# Dias de prueba (indice de dia dentro del bloque) y dia excluido en Chillan (marca VCB del 22-10)
PRUEBA = {"oct": (0, 32), "nov": (0, 20)}        # E4: todos los dias del bloque
EXCLUIDO = {("oct", "chillan"): [31]}
FUERA_DE_BASE = {"oct": (31,), "nov": ()}     # dias del bloque que no entran a la linea base (22-10, marca VCB)
EVENTOS = [("2026-11-13 19:00", "2026-11-13 21:00"), ("2026-11-14 12:40", "2026-11-14 13:40"),
           ("2026-11-14 16:30", "2026-11-14 23:40"), ("2026-11-18 10:10", "2026-11-18 10:10")]
rng = np.random.default_rng(23)


# ---------- datos ----------
def cargar(bloque):
    z = np.load(os.path.join(K.H23, f"cubo_{bloque}.npz"))
    co = {14: z["co14"], 15: z["co15"]}
    return z["rad14"].reshape(-1, NP_), z["rad15"].reshape(-1, NP_), co, datetime.strptime(str(z["t0"]), "%Y-%m-%d")


def cargar_acm(bloque, nt, t0):
    """Mascara de nubes de NOAA (ACM de 4 niveles) por cuadro y pixel; 255 donde no hay archivo."""
    f = os.path.join(K.H23, f"acm_{bloque}.npz")
    if os.path.exists(f):
        return np.load(f)["acm"]
    acm = np.full((nt, NP_), 255, "uint8")
    for i in range(nt):
        g = os.path.join(K.H23, "acm", K.clave(t0 + timedelta(minutes=10 * i)) + ".npz")
        if os.path.exists(g):
            with np.load(g) as z:
                acm[i] = z["acm"].ravel()
    np.savez_compressed(f, acm=acm)
    return acm


def escena_despejada(volcan, acm):
    """E1: por cuadro, True si al menos 80 % del terreno bajo del volcan esta despejado (ACM 0 o 1) segun NOAA."""
    a = acm[:, grupos(volcan)["bajo"]]
    return (a <= 1).mean(1) >= FRAC_DESPEJADO


def cuantil_ordenado(S, q):
    """Cuantil q a lo largo del eje 0 de S ya ordenado (NaN al final). Devuelve (valor, n validos)."""
    n = np.isfinite(S).sum(0)
    pos = q * np.maximum(n - 1, 0)
    lo = np.floor(pos).astype(int)
    hi = np.minimum(lo + 1, np.maximum(n - 1, 0))
    a = np.take_along_axis(S, lo[None], 0)[0]
    b = np.take_along_axis(S, hi[None], 0)[0]
    return a + (b - a) * (pos - lo), n


def linea_base(bt11, btd, despejada, dias_fuera=()):
    """E2: BT11_ref y BTD_ref de cada pixel y cuadro = mediana a la misma hora (cuadro anterior, mismo y
    siguiente) en los OTROS dias del bloque con la escena despejada. Pide al menos MIN_DIAS_REF dias distintos.
    bt11, btd: (cuadros del bloque, pixeles). Devuelve tambien cuantos dias sostienen cada referencia."""
    nt, npx = bt11.shape
    ref = np.full((nt, npx), np.nan, "float32")
    refd = np.full((nt, npx), np.nan, "float32")
    ndias = np.zeros((nt, npx), "uint8")
    nd = nt // 144
    with np.errstate(invalid="ignore"):
        for t in range(nt):
            idx = np.array([t + 144 * k + j for k in range(-nd, nd + 1) if k != 0 for j in (-1, 0, 1)])
            idx = idx[(idx >= 0) & (idx < nt)]
            idx = idx[despejada[idx] & ~np.isin(idx // 144, dias_fuera)]
            if len(np.unique(idx // 144)) < MIN_DIAS_REF:
                continue
            S, Sd = bt11[idx], btd[idx]
            n = np.zeros(npx, int)
            for d in np.unique(idx // 144):
                n += np.isfinite(S[idx // 144 == d]).any(0)
            r, _ = cuantil_ordenado(np.sort(S, 0), 0.5)
            rd, _ = cuantil_ordenado(np.sort(Sd, 0), 0.5)
            r[n < MIN_DIAS_REF] = np.nan
            rd[n < MIN_DIAS_REF] = np.nan
            ref[t], refd[t], ndias[t] = r, rd, n
    return ref, refd, ndias


def grupos(volcan):
    la, lo, h = K.SITIOS[volcan]
    d = K.hav(LAT, LON, la - 0.93 * h / 1000.0 / 111.2, lo)
    cerca = np.where(d <= 6.0)[0]
    cumbre = cerca[np.argsort(ZDEM[cerca])[::-1][:6]]
    bajo = np.where((d >= 10.0) & (d <= 30.0) & (ZDEM < 1300.0))[0]
    return {"cumbre": cumbre, "bajo": bajo}


def entorno(p):
    d = K.hav(LAT, LON, LAT[p], LON[p])
    return np.where((d >= 6.0) & (d <= 16.0))[0]


def gfs_tope(volcan, tiempos, zs):
    """T del aire (K) a las alturas zs y T de la tropopausa en el volcan, para cada tiempo (interpolacion lineal)."""
    la, lo, _ = K.SITIOS[volcan]
    hs, Tz, Tt = [], [], []
    for f in sorted(glob.glob(os.path.join(K.GFS, "gfs_*.npz"))):
        z = np.load(f)
        fi = (z["lat"][0] - la) / 0.25
        fj = (lo - z["lon"][0]) / 0.25
        i0, j0 = int(np.floor(fi)), int(np.floor(fj))
        wi, wj = fi - i0, fj - j0

        def bil(a):
            return ((1 - wi) * (1 - wj) * a[..., i0, j0] + (1 - wi) * wj * a[..., i0, j0 + 1]
                    + wi * (1 - wj) * a[..., i0 + 1, j0] + wi * wj * a[..., i0 + 1, j0 + 1])
        T, Z = bil(z["T"]), bil(z["Z"])
        assert np.all(np.diff(Z) > 0)
        Tz.append(np.interp(zs, Z, T))
        Tt.append(float(bil(z["ttropo"])))
        hs.append((datetime.strptime(os.path.basename(f)[4:14], "%Y%m%d%H") - datetime(2026, 1, 1)).total_seconds() / 3600)
    hs, Tz, Tt = np.array(hs), np.array(Tz), np.array(Tt)
    th = np.array([(t - datetime(2026, 1, 1)).total_seconds() / 3600 for t in tiempos])
    # sin extrapolar y sin saltar huecos de mas de 6 h
    k = np.searchsorted(hs, th, "right") - 1
    ok = (k >= 0) & (k < len(hs) - 1)
    ok[ok] &= (hs[k[ok] + 1] - hs[k[ok]]) <= 6.0
    top = np.stack([np.where(ok, np.interp(th, hs, Tz[:, i]), np.nan) for i in range(len(zs))], 1)
    return top, np.where(ok, np.interp(th, hs, Tt), np.nan)


# ---------- detectores ----------
def detectores(I14, I15, c):
    """D1, D2, D4, D2 espacial y puntaje D3 (-beta, o -inf si no es valido) para radiancias (t, pixel)."""
    bt11, bt12 = K.bt_de_rad(I14, c["co"][14]), K.bt_de_rad(I15, c["co"][15])
    D1 = bt11 - c["ref11"]
    D2 = (bt11 - bt12) - c["refd"]
    with np.errstate(invalid="ignore", divide="ignore"):
        e11 = (I14 - c["Iref14"]) / (c["Btrop14"] - c["Iref14"])
        e12 = (I15 - c["Iref15"]) / (c["Btrop15"] - c["Iref15"])
        beta = np.log(1 - e12) / np.log(1 - e11)
        ok = (e11 >= 0.02) & (e11 < 1) & (e12 < 1) & (beta >= -0.10) & (beta <= 1.95)
    return {"D1": D1, "D2": D2, "D3": np.where(ok, -beta, -np.inf), "D4": D1 - c["med1"], "D2e": D2 - c["med2"]}


def inyectar(c, eps, iz, beta=BETA):
    e12 = 1 - (1 - eps) ** beta
    I14 = (1 - eps) * c["I14"] + eps * c["Btop14"][:, iz][:, None]
    I15 = (1 - e12) * c["I15"] + e12 * c["Btop15"][:, iz][:, None]
    return I14, I15


def matriz_u(s1, s0, dia, nd):
    """U[a, b] = pares (inyectada del dia a, sin inyectar del dia b) con s1 > s0, mas medio empate."""
    U = np.zeros((nd, nd))
    for b in range(nd):
        S = np.sort(s0[dia == b])
        if not len(S):
            continue
        cnt = 0.5 * (np.searchsorted(S, s1, "left") + np.searchsorted(S, s1, "right"))
        U[:, b] = np.bincount(dia, weights=cnt, minlength=nd)
    return U


def auc_ic(U, n):
    """AUC y su IC 95 % remuestreando dias."""
    auc = U.sum() / n.sum() ** 2
    W = rng.multinomial(len(n), np.ones(len(n)) / len(n), size=NBOOT).astype(float)
    num = np.einsum("ka,ab,kb->k", W, U, W)
    den = (W @ n) ** 2
    b = num[den > 0] / den[den > 0]
    return auc, np.percentile(b, 2.5), np.percentile(b, 97.5)


def fisher(F0, F1, dia):
    """D5: discriminante lineal ajustado en una mitad de los dias y aplicado a la otra (y al reves)."""
    s0, s1 = np.full(len(dia), np.nan), np.full(len(dia), np.nan)
    orden = {d: i for i, d in enumerate(np.unique(dia))}
    par = np.array([orden[d] % 2 for d in dia])
    for f in (0, 1):
        tr, te = par != f, par == f
        if tr.sum() < 50 or te.sum() < 1:
            continue
        m0, m1 = F0[tr].mean(0), F1[tr].mean(0)
        S = 0.5 * (np.cov(F0[tr].T) + np.cov(F1[tr].T)) + 1e-6 * np.eye(F0.shape[1])
        w = np.linalg.solve(S, m1 - m0)
        sd = (F0[tr] @ w).std() or 1.0
        s0[te] = (F0[te] - m0) @ w / sd
        s1[te] = (F1[te] - m0) @ w / sd
    return s0, s1


def medir(s1, s0, dia, espejo):
    """Fila de metricas de una celda. dia ya viene re-indexado 0..nd-1."""
    nd = int(dia.max()) + 1
    n = np.bincount(dia, minlength=nd).astype(float)
    auc, lo, hi = auc_ic(matriz_u(s1, s0, dia, nd), n)
    sentido = "frio"
    if espejo and auc < 0.5:
        auc, lo, hi, sentido = 1 - auc, 1 - hi, 1 - lo, "tibio"
        s1, s0 = -s1, -s0
    pod = [float((s1 > np.quantile(s0, 1 - f, method="higher")).mean()) for f in (0.01, 0.05)]
    return dict(auc=auc, lo=lo, hi=hi, sentido=sentido, pod1=pod[0], pod5=pod[1])


def media_movil(X, n, nmin):
    """Promedio de los ultimos n cuadros (eje 0), NaN si hay menos de nmin validos."""
    ok = np.isfinite(X)
    cs = np.cumsum(np.where(ok, X, 0.0), 0)
    cn = np.cumsum(ok, 0)
    s = cs.copy(); s[n:] -= cs[:-n]
    k = cn.copy(); k[n:] -= cn[:-n]
    with np.errstate(invalid="ignore", divide="ignore"):
        return np.where(k >= nmin, s / k, np.nan)


# ---------- contexto por bloque y volcan ----------
def contexto(bloque, volcan, B):
    """Todo lo necesario para inyectar y detectar en los pixeles objetivo de un volcan (arreglos tiempo x pixel)."""
    g = grupos(volcan)
    P = np.concatenate([g["cumbre"], g["bajo"]])
    terreno = np.array(["cumbre"] * len(g["cumbre"]) + ["bajo"] * len(g["bajo"]))
    anillos = [entorno(p) for p in P]
    U = np.unique(np.concatenate([P] + anillos))        # objetivos y sus entornos: solo ahi se calcula la referencia
    pos = {int(u): i for i, u in enumerate(U)}
    iP = np.array([pos[int(p)] for p in P])
    bt11, btd = B["bt11"][:, U], B["btd"][:, U]
    F = escena_despejada(volcan, B["acm"])
    ref, refd, ndias = linea_base(bt11, btd, F, FUERA_DE_BASE[bloque])
    D1u, D2u = bt11 - ref, btd - refd
    nt = bt11.shape[0]
    c = {"co": B["co"], "P": P, "terreno": terreno, "U": U, "iP": iP, "F": F, "ref_U": ref, "refd_U": refd,
         "I14": B["r14"][:, P].astype("float64"), "I15": B["r15"][:, P].astype("float64"),
         "ref11": ref[:, iP].astype("float64"), "refd": refd[:, iP].astype("float64"), "ndias_ref": ndias[:, iP]}
    med1 = np.full((nt, len(P)), np.nan); med2 = med1.copy()
    with np.errstate(invalid="ignore"), warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        for j, e in enumerate(anillos):
            ie = np.array([pos[int(x)] for x in e])
            d1, d2 = D1u[:, ie], D2u[:, ie]
            nv = np.isfinite(d1).sum(1)
            m1 = np.nanmedian(d1, 1); m2 = np.nanmedian(d2, 1)
            m1[nv < 10] = np.nan; m2[nv < 10] = np.nan
            med1[:, j], med2[:, j] = m1, m2
    c["med1"], c["med2"] = med1, med2
    tiempos = [B["t0"] + timedelta(minutes=10 * i) for i in range(nt)]
    top, trop = gfs_tope(volcan, tiempos, ALTURAS + [Z_CONTROL])
    c["Ttop"], c["Ttrop"], c["tiempos"] = top, trop, tiempos
    for b in (14, 15):
        c[f"Btop{b}"] = K.rad_de_bt(top, B["co"][b])
        c[f"Btrop{b}"] = K.rad_de_bt(trop, B["co"][b])[:, None]
    c["Iref14"] = K.rad_de_bt(c["ref11"], B["co"][14])
    c["Iref15"] = K.rad_de_bt(c["ref11"] - c["refd"], B["co"][15])
    c["dia"] = np.repeat(np.arange(nt) // 144, len(P)).reshape(nt, len(P))
    c["tramo"] = np.repeat((np.arange(nt) % 144) // 36, len(P)).reshape(nt, len(P))
    c["d0"] = detectores(c["I14"], c["I15"], c)
    val = np.isfinite(c["d0"]["D1"]) & np.isfinite(c["d0"]["D2"]) & np.isfinite(med1) & np.isfinite(med2)
    val &= np.isfinite(trop)[:, None] & np.isfinite(top).all(1)[:, None]
    for d in EXCLUIDO.get((bloque, volcan), []):
        val &= c["dia"] != d
    desp = F[:, None]
    c["pob"] = {"A": val, "B": val & desp, "C": val & desp & (c["d0"]["D1"] >= UMBRAL_DESPEJADO)}
    return c


def celdas(bloque, volcan, c, betas, filas, pobs=("A", "B", "C"), alturas=None, eps_lista=EPS):
    """Recorre la grilla de inyeccion y agrega una fila por celda a filas."""
    alturas = list(range(len(ALTURAS))) + [len(ALTURAS)] if alturas is None else alturas
    zs = ALTURAS + [Z_CONTROL]
    bt11_0 = K.bt_de_rad(c["I14"], c["co"][14]); btd_0 = bt11_0 - K.bt_de_rad(c["I15"], c["co"][15])
    for beta in betas:
        for iz in alturas:
            for eps in (eps_lista if iz < len(ALTURAS) else [0.5, 0.9]):
                I14, I15 = inyectar(c, eps, iz, beta)
                d1 = detectores(I14, I15, c)
                bt11_1 = K.bt_de_rad(I14, c["co"][14])
                dbt = bt11_1 - bt11_0
                dbtd = (bt11_1 - K.bt_de_rad(I15, c["co"][15])) - btd_0
                contraste = bt11_0 - c["Ttop"][:, iz][:, None]
                with np.errstate(invalid="ignore", divide="ignore"):
                    etot = eps * (c["I14"] - c["Btop14"][:, iz][:, None]) / (c["I14"] - c["Btrop14"])
                for terr in ("cumbre", "bajo"):
                    mt = (c["terreno"] == terr)[None, :]
                    for pob in pobs:
                        for tramo in range(4):
                            m = c["pob"][pob] & mt & (c["tramo"] == tramo)
                            n = int(m.sum())
                            dias_u, dia = np.unique(c["dia"][m], return_inverse=True)
                            base = dict(bloque=bloque, volcan=volcan, terreno=terr, pob=pob, tramo=tramo,
                                        z_km=zs[iz] / 1000, eps=eps, beta=beta, n=n, ndias=len(dias_u))
                            if n < MIN_N or len(dias_u) < MIN_DIAS:
                                filas.append(dict(base, det="todos", estado="SIN DATO"))
                                continue
                            fis = dict(dbt11=float(np.median(dbt[m])), dbtd=float(np.median(dbtd[m])),
                                       contraste=float(np.median(contraste[m])), etot_eq=float(np.median(etot[m])))
                            F0 = np.stack([c["d0"][k][m] for k in ("D1", "D2", "D4", "D2e")], 1)
                            F1 = np.stack([d1[k][m] for k in ("D1", "D2", "D4", "D2e")], 1)
                            for det in DET:
                                if det == "D5":
                                    s0, s1 = fisher(F0, F1, dia)
                                    if eps == 0:
                                        s1 = s0
                                elif det == "D3":
                                    s0, s1 = c["d0"]["D3"][m], d1["D3"][m]
                                else:
                                    s0, s1 = -c["d0"][det][m], -d1[det][m]
                                ok = np.isfinite(s0) | np.isneginf(s0)
                                r = medir(s1[ok], s0[ok], dia[ok], det in ESPEJO)
                                filas.append(dict(base, det=det, estado="ok", **r, **fis))


def integrar(bloque, volcan, c, filas):
    """S1: promedio de 6 y 18 cuadros con la misma capa en todos (pluma persistente). Poblacion B, beta 0,70."""
    for nfr, nmin in ((6, 5), (18, 15)):
        base0 = {k: media_movil(np.where(c["pob"]["A"], c["d0"][k], np.nan), nfr, nmin) for k in ("D1", "D2", "D4")}
        for iz in range(len(ALTURAS)):
            for eps in EPS[1:]:
                d1 = detectores(*inyectar(c, eps, iz), c)
                iny = {k: media_movil(np.where(c["pob"]["A"], d1[k], np.nan), nfr, nmin) for k in ("D1", "D2", "D4")}
                for terr in ("cumbre", "bajo"):
                    mt = (c["terreno"] == terr)[None, :]
                    for tramo in range(4):
                        m = c["pob"]["B"] & mt & (c["tramo"] == tramo) & np.isfinite(base0["D1"]) & np.isfinite(base0["D4"])
                        n = int(m.sum())
                        dias_u, dia = np.unique(c["dia"][m], return_inverse=True)
                        base = dict(bloque=bloque, volcan=volcan, terreno=terr, pob=f"B_int{nfr}", tramo=tramo,
                                    z_km=ALTURAS[iz] / 1000, eps=eps, beta=BETA, n=n, ndias=len(dias_u))
                        if n < MIN_N or len(dias_u) < MIN_DIAS:
                            filas.append(dict(base, det="todos", estado="SIN DATO"))
                            continue
                        for det in ("D1", "D2", "D4"):
                            r = medir(-iny[det][m], -base0[det][m], dia, True)
                            filas.append(dict(base, det=det, estado="ok", **r))


def placebo(c, terr="cumbre"):
    """Control nulo (b): AUC entre dos mitades de dias al azar, sin inyectar. Poblacion B."""
    out = {}
    mt = (c["terreno"] == terr)[None, :]
    for tramo in range(4):
        m = c["pob"]["B"] & mt & (c["tramo"] == tramo)
        dias_u, dia = np.unique(c["dia"][m], return_inverse=True)
        nd = len(dias_u)
        if m.sum() < MIN_N or nd < MIN_DIAS:
            out[tramo] = "SIN DATO"
            continue
        n = np.bincount(dia, minlength=nd).astype(float)
        out[tramo] = {}
        for det in ("D1", "D2", "D3", "D4"):
            s = c["d0"]["D3"][m] if det == "D3" else -c["d0"][det][m]
            U = matriz_u(s, s, dia, nd)
            a = []
            for _ in range(200):
                g = rng.permutation(nd) < nd // 2
                a.append(U[np.ix_(g, ~g)].sum() / (n[g].sum() * n[~g].sum()))
            out[tramo][det] = dict(mediana=float(np.median(a)), p2_5=float(np.percentile(a, 2.5)),
                                   p97_5=float(np.percentile(a, 97.5)), ndias=nd, n=int(m.sum()))
    return out


def bloque_datos(bloque):
    r14, r15, co, t0 = cargar(bloque)
    bt11 = K.bt_de_rad(r14.astype("float64"), co[14]).astype("float32")
    btd = (bt11 - K.bt_de_rad(r15.astype("float64"), co[15])).astype("float32")
    return dict(r14=r14, r15=r15, co=co, t0=t0, bt11=bt11, btd=btd, acm=cargar_acm(bloque, r14.shape[0], t0))


def instrumento(c):
    """I4 a I6 del criterio sobre la referencia nueva (enmienda E5), con los pixeles de Chillan que la tienen."""
    nd = c["ref_U"].shape[0] // 144
    ref = c["ref_U"].reshape(nd, 144, -1)
    with np.errstate(invalid="ignore"), warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        r06, r09 = (np.nanmedian(ref[:, i], 0) for i in (36, 54))
        refd = float(np.nanmedian(c["refd_U"]))
        cum, baj = c["iP"][c["terreno"] == "cumbre"], c["iP"][c["terreno"] == "bajo"]
        i4b = float(np.nanmedian(r06[cum]) - np.nanmedian(r06[baj]))
        # Enmienda 2: I5 en la ultima hora (12 a 18 UTC) en que al menos la mitad del terreno bajo tiene referencia
        h_tarde, r18 = None, np.full(ref.shape[2], np.nan)
        for h in range(18, 11, -1):
            r = np.nanmedian(ref[:, h * 6], 0)
            if np.isfinite(r[baj]).mean() >= 0.5:
                h_tarde, r18 = h, r
                break
        i5 = float(np.nanmedian(r18[baj] - r09[baj]))
        i5c = float(np.nanmedian(r18[cum] - r09[cum]))
    ok = np.isfinite(r06)
    F = c["F"].reshape(nd, 144)
    out = {"I4_corr_ref06_cota": float(np.corrcoef(r06[ok], ZDEM[c["U"]][ok])[0, 1]) if ok.sum() > 10 else float("nan"),
           "I4_pixeles_con_referencia": int(ok.sum()), "I4_pixeles": int(len(ok)),
           "I4_cumbre_menos_bajo_K": i4b, "I5_hora_tarde_utc": h_tarde, "I5_bajo_tarde_menos_09_K": i5,
           "I5_cumbre_tarde_menos_09_K": i5c,
           "I6_btd_ref_mediana_K": refd,
           "frac_cuadros_con_escena_despejada": float(c["F"].mean()),
           "escena_despejada_por_tramo": {str(tr): dict(frac_cuadros=float(F[:, tr * 36:(tr + 1) * 36].mean()),
                                                         dias_con_alguno=int(F[:, tr * 36:(tr + 1) * 36].any(1).sum()))
                                          for tr in range(4)},
           "frac_muestras_con_referencia": {t: float(np.isfinite(c["ref11"][:, c["terreno"] == t]).mean())
                                            for t in ("cumbre", "bajo")},
           "dias_que_sostienen_la_referencia_mediana": {t: float(np.median(c["ndias_ref"][:, c["terreno"] == t]))
                                                        for t in ("cumbre", "bajo")}}
    falla = []
    if not out["I4_corr_ref06_cota"] <= -0.6 or not out["I4_cumbre_menos_bajo_K"] <= -5:
        falla.append("I4")
    if not out["I5_bajo_tarde_menos_09_K"] >= 8:
        falla.append("I5")
    if not -1 <= out["I6_btd_ref_mediana_K"] <= 4:
        falla.append("I6")
    out["fallas"] = falla
    return out


def eventos(c_nov, c_oct):
    """S4: D1 a D4 en los pixeles de cumbre de Chillan en las horas de los eventos VOLCAT, contra el fondo de
    octubre del mismo tramo (poblacion A, porque en un evento no se elige el cielo)."""
    out = []
    cum_n = (c_nov["terreno"] == "cumbre")
    cum_o = (c_oct["terreno"] == "cumbre")[None, :]
    tn = np.array(c_nov["tiempos"])
    for a, b in EVENTOS:
        ta, tb = datetime.strptime(a, "%Y-%m-%d %H:%M"), datetime.strptime(b, "%Y-%m-%d %H:%M")
        mt = (tn >= ta) & (tn <= tb)
        fila = {"evento": f"{a} a {b[-5:]} UTC", "cuadros": int(mt.sum())}
        for det in ("D1", "D2", "D3", "D4"):
            x = c_nov["d0"][det][mt][:, cum_n]
            x = x[np.isfinite(x) | np.isneginf(x)]
            if not len(x):
                fila[det] = "SIN DATO"
                continue
            tramos = np.unique((np.array([t.hour for t in tn[mt]]) // 6))
            m0 = c_oct["pob"]["A"] & cum_o & np.isin(c_oct["tramo"], tramos)
            f = c_oct["d0"][det][m0]
            if det == "D3":
                fila[det] = dict(n=int(len(x)), frac_valido=float(np.isfinite(x).mean()),
                                 frac_valido_fondo=float(np.isfinite(f).mean()),
                                 frac_beta_bajo_fondo_p5=float((x > np.quantile(f, 0.95, method="higher")).mean()))
            else:
                q = np.quantile(f, [0.05, 0.5, 0.95])
                fila[det] = dict(n=int(len(x)), mediana=float(np.median(x)), fondo_p5=float(q[0]), fondo_p50=float(q[1]),
                                 fondo_p95=float(q[2]), frac_bajo_p5=float((x < q[0]).mean()),
                                 frac_sobre_p95=float((x > q[2]).mean()))
        out.append(fila)
    return out


def main():
    os.makedirs(RES, exist_ok=True)
    filas = []
    B = bloque_datos("oct")
    c = contexto("oct", "chillan", B)
    ins = instrumento(c)
    ins["muestras_chillan"] = {f"{t}_{p}": int((c["pob"][p] & (c["terreno"] == t)[None, :]).sum())
                               for t in ("cumbre", "bajo") for p in "ABC"}
    ins["gfs_Ttop_mediana_K"] = dict(zip(["3km", "4km", "5km", "10km"], np.nanmedian(c["Ttop"], 0).round(2).tolist()))
    ins["gfs_Ttropo_mediana_K"] = float(np.nanmedian(c["Ttrop"]))
    json.dump(ins, open(os.path.join(RES, "h23_instrumento.json"), "w"), indent=1)
    print("INSTRUMENTO", json.dumps(ins, indent=1), flush=True)
    if ins["fallas"]:
        print("FALLA DE INSTRUMENTO: se corta sin veredicto")
        sys.exit(1)
    if "--solo-instrumento" in sys.argv:
        return
    celdas("oct", "chillan", c, [BETA], filas)
    print("celdas chillan oct", len(filas), flush=True)
    celdas("oct", "chillan", c, BETAS_SENS, filas, pobs=("B",), alturas=list(range(len(ALTURAS))))
    integrar("oct", "chillan", c, filas)
    ctl = {"placebo_cumbre": placebo(c, "cumbre"), "placebo_bajo": placebo(c, "bajo")}
    json.dump(ctl, open(os.path.join(RES, "h23_controles.json"), "w"), indent=1)
    c_oct = {k: c[k] for k in ("pob", "terreno", "tramo", "d0")}
    del c
    for v in ("longavi", "antuco"):
        celdas("oct", v, contexto("oct", v, B), [BETA], filas, pobs=("B",), alturas=list(range(len(ALTURAS))))
        print("celdas", v, "oct", len(filas), flush=True)
    del B
    B = bloque_datos("nov")
    for v in ("longavi", "antuco"):
        celdas("nov", v, contexto("nov", v, B), [BETA], filas, pobs=("B",), alturas=list(range(len(ALTURAS))))
        print("celdas", v, "nov", len(filas), flush=True)
    ev = eventos(contexto("nov", "chillan", B), c_oct)
    json.dump(ev, open(os.path.join(RES, "h23_eventos.json"), "w"), indent=1)
    cols = ["bloque", "volcan", "terreno", "pob", "tramo", "z_km", "eps", "beta", "det", "estado", "n", "ndias", "auc",
            "lo", "hi", "sentido", "pod1", "pod5", "dbt11", "dbtd", "contraste", "etot_eq"]
    with open(os.path.join(RES, "h23_celdas.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, cols)
        w.writeheader()
        for r in filas:
            w.writerow({k: (f"{v:.4f}" if isinstance(v, float) else v) for k, v in r.items()})
    print("FIN", len(filas), "filas")


if __name__ == "__main__":
    main()
