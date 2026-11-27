r"""S31i: por qué la zona del cráter dispara de día en la cumbre de Antuco (sin pluma) y cambia de un año a otro.
Implementa criterio_2026-11-27.md de esta carpeta (commit 097b10d, empujado antes de cruzar un disparo con cualquier
covariable).

Por qué así: cada candidata deja otra huella en la cumbre. Una nube baja (a) brilla a 1,6 µm, donde la nieve es oscura
y la roca intermedia; una superficie despejada con otra nieve que la de 2025 (b) no brilla a 1,6 µm más que en los
días comunes; un disparo que ponen los controles lejanos (c) se ve en la cuenta de S = Ā menos C̄. Los disparos salen
de la regla de la zona de S25a puesta en Antuco por S27a (`s27a_medir.Zona`, sin cambio, percentil 4,75); aquí sólo se
mira qué hay en la cumbre cuando disparan. El nulo permuta días dentro de cada año (el día es la unidad).

Uso: python -I -B s31i_medir.py pruebas | optica | medir
  pruebas  comprobación de código: conteos de día de la zona de Antuco publicados por S28a y S29b.
  optica   tabla de reflectancias y clases por cuadro y cumbre (D:\goes_notas\s31\s31i\optica_<año>.npz).
  medir    M1 a M4 del criterio; escribe resultados/s31i_resultado.json.
"""
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
sys.path.insert(0, os.path.join(OV, "s27a_noche_causa", "scripts"))
import s27a_medir as Q  # noqa: E402

Z, B, H24, C29, U = Q.Z, Q.B, Q.H24, Q.C29, Q.U
TRAB = r"D:\goes_notas\s31\s31i"
L1B = os.path.join(TRAB, "l1b")
PSTAR = 4.75
DIA = range(72, 144)
ND = 62
T0 = {2024: datetime(2024, 9, 21), 2025: datetime(2025, 9, 21), 2026: datetime(2026, 9, 21)}
SITIOS = {"antuco": (-37.41, -71.35), "longavi": (-36.19, -71.16), "chillan": C29.CRATER}
WIN0 = (4497, 2820)                       # h23_comun.WIN: fila y columna 0 de la ventana común en la grilla de 2 km
FRANJA0 = (4504, 2856)                    # s31i_bajar.WIN2
TS_MAX, TS_FS = 70.0, 60.0
N_NIEVE, R3_NIEVE, R5_NUBE, N_NUBE = 0.40, 0.15, 0.25, 0.40
FRAC_NUBE = 0.25
VENT_REF, VENT_FS25 = 10, 3
MIN_FS = 6
B_PERM, SEMILLA, N_BOOT = 1999, 0, 2000
ALFA_LADO = 0.005
MIN_DIAS, MIN_DIAS_AÑO = 8, 3
REPRO = {2026: (138, 1467), 2024: (176, 2273), 2025: (62, 2410)}


# ---------- cubos ----------
def cubos(año):
    if año == 2025:
        btd = np.asarray(np.load(Z._npy("r25_btd"), mmap_mode="r"))
        acm = np.load(Z._npy("r25_acm"))
        bt = np.load(r"D:\goes_notas\s23\s23a\r25_bt11.npy", mmap_mode="r")
        est = Z.costumbre(acm, np.isfinite(btd[:, :, Z.ZONA[0]]))
    elif año == 2024:
        btd = np.load(r"D:\goes_notas\s29\s29b\r24_btd.npy")
        acm = np.load(r"D:\goes_notas\s29\s29b\r24_acm.npy")
        bt = np.load(r"D:\goes_notas\s25\s25b_2024\cubo\r24_bt11.npy", mmap_mode="r")
        est = Z.costumbre(acm, np.isfinite(btd[:, :, Z.ZONA[0]]))
    else:
        btd = np.concatenate([np.load(os.path.join(B.TRAB, "dev_btd.npy")), np.load(Z._npy("n26_btd"))])
        acm = np.concatenate([np.load(os.path.join(B.TRAB, "dev_acm.npy")),
                              np.load(os.path.join(B.TRAB, "nuevo_acm.npy"))])
        bt = np.load(os.path.join(B.TRAB, "dev_bt11.npy"), mmap_mode="r")
        est = np.load(U.ESTAT26)
        import hashlib
        assert hashlib.sha256(est.tobytes()).hexdigest()[:16] == U.SHA_ESTAT26, "estat_2026 no es el congelado"
    return btd, acm, bt, est


class ZonaX(Q.Zona):
    """Q.Zona sin cambio en la regla; además guarda lo que el criterio descompone (§3): término regional, base de la
    zona y anomalía de BT11 con la misma base y los mismos controles."""

    def correr_x(self, r25, rT, sitio):
        btd25, acm25, bt25, est25 = r25
        btdT, acmT, btT, estT = rT
        self.correr(btd25, acm25, est25, btdT, acmT, estT, sitio)
        hay25 = np.isfinite(btd25[:, :, self.zona[0]])
        FD25, DIN25 = self.nubes(acm25, est25)
        G25 = FD25 <= B.G_MAX
        USA25 = G25 & H24.despejada(sitio, acm25) & hay25
        bctrl = Z.base(btd25, USA25, self.ctrl)
        self.C25 = self.regional(btd25, DIN25, bctrl)
        self.Z25 = np.ascontiguousarray(btd25[:, :, self.zona])
        IZ = np.arange(len(self.zona))
        self.BZ = np.array([Z.base(self.Z25, USA25, IZ, excl=d) for d in range(self.Z25.shape[0])])
        FDT, DINT = self.nubes(acmT, estT)
        self.CT = self.regional(btdT, DINT, bctrl)
        self.ZT = btdT[:, :, self.zona]
        # BT11 (§3, Y11): misma base (USA25), mismos controles y misma nube dinámica
        n = min(btT.shape[0], btdT.shape[0])
        bt25 = np.asarray(bt25)
        bzb = Z.base(np.ascontiguousarray(bt25[:, :, self.zona]), USA25, IZ)
        bcb = Z.base(bt25, USA25, self.ctrl)
        btT_ = np.asarray(btT[:n])
        CbT = self.regional(btT_, DINT[:n], bcb)
        self.Y11T = np.nanmean(btT_[:, :, self.zona] - bzb[None] - CbT, 2)
        self.ACMT = ((acmT[:, :, self.zona] >= 2) & (acmT[:, :, self.zona] <= 3)).mean(2)
        self.ACMT[(acmT[:, :, self.zona] == 255).all(2)] = np.nan
        return self


def zona_sitio(sitio):
    if sitio == "chillan":
        return Z.ZONA, Q.M.AP, Z.CTRL
    zona, anillo, ctrl, _ = Q.zona_de(*SITIOS[sitio])
    return zona, anillo, ctrl


def correr(sitio, año, r25, rT):
    zona, anillo, ctrl = zona_sitio(sitio)
    zv = ZonaX(sitio, zona, anillo, ctrl).correr_x(r25, rT, sitio)
    sec, bla = zv.disparos(PSTAR)
    return zv, sec, bla


def cuenta_dia(lista, nd=None):
    lista = lista if nd is None else lista[:nd]
    return (sum(int(F[DIA].sum()) for F, _ in lista), sum(int(ev[DIA].sum()) for _, ev in lista))


def pruebas():
    t = time.time()
    r25 = cubos(2025)
    out = {}
    for año in (2026, 2024):
        rT = cubos(año)
        zv, sec, bla = correr("antuco", año, r25, rT)
        out[año] = cuenta_dia(bla)
        if año == 2026:
            out[2025] = cuenta_dia(sec)
        print(año, out[año], f"{time.time() - t:.0f} s", flush=True)
    ok = all(tuple(out[a]) == REPRO[a] for a in REPRO)
    print("comprobación", "OK" if ok else "FALLA", out, flush=True)
    return ok


# ---------- óptica ----------
def zenit_solar(dt, lat, lon):
    """Ángulo cenital solar (grados), algoritmo de NOAA (Spencer), error ~0,1°."""
    doy = dt.timetuple().tm_yday
    hr = dt.hour + dt.minute / 60 + dt.second / 3600
    g = 2 * np.pi / 365 * (doy - 1 + (hr - 12) / 24)
    eqt = 229.18 * (0.000075 + 0.001868 * np.cos(g) - 0.032077 * np.sin(g) - 0.014615 * np.cos(2 * g)
                    - 0.040849 * np.sin(2 * g))
    dec = (0.006918 - 0.399912 * np.cos(g) + 0.070257 * np.sin(g) - 0.006758 * np.cos(2 * g)
           + 0.000907 * np.sin(2 * g) - 0.002697 * np.cos(3 * g) + 0.00148 * np.sin(3 * g))
    tst = hr * 60 + eqt + 4 * lon
    ha = np.radians(tst / 4 - 180)
    la = np.radians(lat)
    c = np.sin(la) * np.sin(dec) + np.cos(la) * np.cos(dec) * np.cos(ha)
    return np.degrees(np.arccos(np.clip(c, -1, 1)))


def subpix(pix):
    """Índices (fila, columna) en la franja de 1 km de los cuatro subpíxeles de cada píxel de 2 km (índice plano)."""
    r, c = np.unravel_index(pix, C29.LAT.shape)
    R = WIN0[0] + r - FRANJA0[0]
    Cc = WIN0[1] + c - FRANJA0[1]
    rr = np.concatenate([2 * R, 2 * R, 2 * R + 1, 2 * R + 1])
    cc = np.concatenate([2 * Cc, 2 * Cc + 1, 2 * Cc, 2 * Cc + 1])
    return rr, cc


def clases(r3, r5):
    n = (r3 - r5) / (r3 + r5)
    nieve = (n >= N_NIEVE) & (r3 >= R3_NIEVE)
    nube = (r5 >= R5_NUBE) & (n < N_NUBE)
    return nieve, nube


def anillo_4_10(sitio):
    la, lo = SITIOS[sitio]
    d = C29.hav(C29.LAT, C29.LON, la, lo).ravel()
    zona = zona_sitio(sitio)[0]
    return np.setdiff1d(np.flatnonzero((d >= 4.0) & (d <= 10.0)), zona)


def optica():
    J2000 = datetime(2000, 1, 1, 12)
    geo = {}
    for s in SITIOS:
        zona = zona_sitio(s)[0]
        geo[s] = (subpix(zona), subpix(anillo_4_10(s)), float(C29.LAT.ravel()[zona].mean()),
                  float(C29.LON.ravel()[zona].mean()))
    for año in (2024, 2025, 2026):
        t = time.time()
        campos = ("X5", "X3", "ts", "fnube", "fnieve", "fnube_anillo")
        T = {f"{s}_{k}": np.full((ND, 144), np.nan, np.float32) for s in SITIOS for k in campos}
        hay = np.zeros((ND, 144), bool)
        for d in range(ND):
            for sl in range(72, 137, 2):
                dt = T0[año] + timedelta(days=d, minutes=10 * sl)
                fn = os.path.join(L1B, f"{dt:%Y%m%d_%H%M}.npz")
                if not os.path.exists(fn):
                    continue
                f = np.load(fn)
                tm = J2000 + timedelta(seconds=float(np.mean(f["C05_tb"])))
                R3 = f["C03_rad"] * f["C03_kappa0"]
                R5 = f["C05_rad"] * f["C05_kappa0"]
                hay[d, sl] = True
                for s, ((zr, zc), (ar, ac), la, lo) in geo.items():
                    ts = zenit_solar(tm, la, lo)
                    T[f"{s}_ts"][d, sl] = ts
                    if ts > TS_MAX:
                        continue
                    mu = np.cos(np.radians(ts))
                    r3, r5 = R3[zr, zc] / mu, R5[zr, zc] / mu
                    if not (np.isfinite(r3).all() and np.isfinite(r5).all()):
                        continue
                    nv, nb = clases(r3, r5)
                    T[f"{s}_X5"][d, sl] = r5.mean()
                    T[f"{s}_X3"][d, sl] = r3.mean()
                    T[f"{s}_fnube"][d, sl] = nb.mean()
                    T[f"{s}_fnieve"][d, sl] = nv.mean()
                    a3, a5 = R3[ar, ac] / mu, R5[ar, ac] / mu
                    ok = np.isfinite(a3) & np.isfinite(a5)
                    if ok.any():
                        T[f"{s}_fnube_anillo"][d, sl] = clases(a3[ok], a5[ok])[1].mean()
        np.savez_compressed(os.path.join(TRAB, f"optica_{año}.npz"), hay=hay, **T)
        print(año, "cuadros", int(hay.sum()), f"{time.time() - t:.0f} s", flush=True)


# ---------- medidas ----------
def matrices(lista):
    F = np.array([f for f, _ in lista[:ND]])
    E = np.array([e for _, e in lista[:ND]])
    return F, E


def ref_local(X, E):
    """ref(d, s): mediana de X en la casilla s de los otros días a ±10 días, sólo cuadros evaluados (§3)."""
    R = np.full(X.shape, np.nan)
    Xe = np.where(E, X, np.nan)
    for d in range(X.shape[0]):
        idx = [k for k in range(max(0, d - VENT_REF), min(X.shape[0], d + VENT_REF + 1)) if k != d]
        R[d] = np.nanmedian(Xe[idx], 0)
    return X - R


def T_dias(F, E, x, perm=None):
    """Medias por día de x en las casillas que disparan del día d, colocadas sobre el día perm[d]."""
    perm = np.arange(F.shape[0]) if perm is None else perm
    Ed, xd = E[perm], x[perm]
    m = F & Ed & np.isfinite(xd)
    n = m.sum(1)
    s = np.where(m, xd, 0).sum(1)
    return s[n > 0] / n[n > 0]


def prueba_perm(bloques, rng):
    """bloques: lista de (F, E, x) por año. T = media de medias por día juntando años; permutación por año."""
    obs = np.concatenate([T_dias(F, E, x) for F, E, x in bloques])
    T = float(obs.mean()) if obs.size else np.nan
    nul = np.empty(B_PERM)
    for b in range(B_PERM):
        v = np.concatenate([T_dias(F, E, x, rng.permutation(F.shape[0])) for F, E, x in bloques])
        nul[b] = v.mean() if v.size else np.nan
    nul = nul[np.isfinite(nul)]
    return {"T": T, "dias": int(obs.size), "p_alto": float((1 + (nul >= T).sum()) / (nul.size + 1)),
            "p_bajo": float((1 + (nul <= T).sum()) / (nul.size + 1)), "replicas": int(nul.size),
            "nulo_mediana": float(np.median(nul)), "nulo_p05_p95": [float(np.percentile(nul, 5)),
                                                                     float(np.percentile(nul, 95))]}


def clase_dias(F, X5, fnube):
    """M2: nublado / despejado / mezclado por día con disparo ópticamente medible."""
    out = {"nublado": 0, "despejado": 0, "mezclado": 0}
    lista = []
    for d in range(F.shape[0]):
        m = F[d] & np.isfinite(X5[d])
        if not m.any():
            continue
        fb = fnube[d][m]
        if (fb >= FRAC_NUBE).sum() > m.sum() / 2:
            c = "nublado"
        elif (fb == 0).sum() > m.sum() / 2:
            c = "despejado"
        else:
            c = "mezclado"
        out[c] += 1
        lista.append((d, c, int(m.sum())))
    return out, lista


def share_dias(zv, F):
    """M3: mediana por día de share = C̄ / (C̄ menos Ā) en los cuadros con disparo (todas las casillas)."""
    a = zv.ZT - zv.bz[None]
    c = zv.CT
    P = zv.PT
    med = []
    for d in range(F.shape[0]):
        v = []
        for s in np.flatnonzero(F[d]):
            p1, p2 = P[d, s]
            if p1 < 0:
                continue
            A_ = (a[d, s, p1] + a[d, s, p2]) / 2
            C_ = (c[d, s, p1] + c[d, s, p2]) / 2
            if np.isfinite(A_) and np.isfinite(C_) and C_ - A_ > 0:
                v.append(C_ / (C_ - A_))
        if v:
            med.append(float(np.median(v)))
    return np.array(med)


def boot_mediana(v, rng):
    if v.size == 0:
        return None
    bs = [np.median(rng.choice(v, v.size)) for _ in range(N_BOOT)]
    return [float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))]


def fs_dia(fnieve, ts):
    out = np.full(fnieve.shape[0], np.nan)
    for d in range(fnieve.shape[0]):
        m = np.isfinite(fnieve[d]) & (ts[d] <= TS_FS)
        if m.sum() >= MIN_FS:
            out[d] = np.percentile(fnieve[d][m], 90)
    return out


def _r(x, k=5):
    if x is None:
        return None
    if isinstance(x, (list, tuple)):
        return [_r(v, k) for v in x]
    return None if not np.isfinite(x) else round(float(x), k)


def medir():
    t = time.time()
    os.makedirs(RES, exist_ok=True)
    r25 = cubos(2025)
    res = {"criterio": "097b10d", "percentil": PSTAR, "dias_por_año": ND}
    ZV, FE = {}, {}
    for sitio, años in (("antuco", (2024, 2026)), ("longavi", (2024,)), ("chillan", (2024,))):
        for año in años:
            zv, sec, bla = correr(sitio, año, r25, cubos(año))
            if sitio == "antuco" and año == 2026:
                comp = {"2026_65dias": cuenta_dia(bla), "2025": cuenta_dia(sec)}
            elif sitio == "antuco":
                comp_24 = cuenta_dia(bla)
            ZV[(sitio, año)] = zv
            FE[(sitio, año)] = matrices(bla)
            FE[(sitio, 2025)] = matrices(sec)
            ZV.setdefault((sitio, 2025), zv)
            print(sitio, año, f"{time.time() - t:.0f} s", flush=True)
    comp["2024"] = comp_24
    # la óptica se arma recién cuando termina la bajada (la parte lenta de arriba corre mientras tanto)
    log = os.path.join(TRAB, "bajar.log")
    while "listo" not in open(log, encoding="utf-8", errors="replace").read():
        time.sleep(30)
    optica()
    OPT = {a: np.load(os.path.join(TRAB, f"optica_{a}.npz")) for a in (2024, 2025, 2026)}
    ok = (tuple(comp["2026_65dias"]) == REPRO[2026] and tuple(comp["2024"]) == REPRO[2024]
          and tuple(comp["2025"]) == REPRO[2025])
    res["comprobacion"] = {"conteos": comp, "esperado": {str(k): v for k, v in REPRO.items()}, "ok": ok}
    print("comprobación", ok, comp, flush=True)
    if not ok:
        json.dump(res, open(os.path.join(RES, "s31i_FALLA.json"), "w", encoding="utf-8"), indent=1)
        sys.exit("no reproduce: error de código, no se mide")

    def bloque(sitio, año, var="X5"):
        F, E = FE[(sitio, año)]
        Fd = F.copy()
        Fd[:, :72] = False
        O = OPT[año]
        X = O[f"{sitio}_{var}"].astype(float)
        return Fd, E, ref_local(X, E), O

    out = {}
    for sitio in ("antuco", "longavi", "chillan"):
        años = (2024, 2026, 2025) if sitio == "antuco" else (2024, 2025)
        S = {}
        for año in años:
            Fd, E, x5, O = bloque(sitio, año)
            X5 = O[f"{sitio}_X5"]
            m2, lista = clase_dias(Fd, X5, O[f"{sitio}_fnube"])
            medibles = Fd & np.isfinite(X5)
            S[año] = {"F_dia": int(Fd.sum()), "F_medible": int(medibles.sum()),
                      "dias_con_medible": int(medibles.any(1).sum()), "M2": m2,
                      "M2_dias": [(f"{T0[año] + timedelta(days=d):%Y-%m-%d}", c, n) for d, c, n in lista],
                      "fnube_en_disparo_media": _r(np.nanmean(O[f"{sitio}_fnube"][medibles])),
                      "fnube_anillo_en_disparo_media": _r(np.nanmean(O[f"{sitio}_fnube_anillo"][medibles])),
                      "fnube_evaluados_dia_media": _r(np.nanmean(np.where(E[:, 72:137:2],
                                                                          O[f"{sitio}_fnube"][:, 72:137:2], np.nan))),
                      "hora_disparos_utc": [int(Fd[:, 6 * h:6 * h + 6].sum()) for h in range(24)]}
        out[sitio] = S

    # M1: Antuco, 2024 más 2026 (decide); por año; placebos informativos
    rng = np.random.default_rng(SEMILLA)
    b24, b26 = bloque("antuco", 2024)[:3], bloque("antuco", 2026)[:3]
    m1 = {"2024+2026": prueba_perm([b24, b26], rng), "2024": prueba_perm([b24], rng),
          "2026": prueba_perm([b26], rng)}
    info = {"antuco_2025_seco": prueba_perm([bloque("antuco", 2025)[:3]], rng),
            "longavi_2024": prueba_perm([bloque("longavi", 2024)[:3]], rng),
            "chillan_2024": prueba_perm([bloque("chillan", 2024)[:3]], rng)}
    print("M1", json.dumps(m1), flush=True)

    # M3
    rng3 = np.random.default_rng(SEMILLA)
    sh = {}
    allv = []
    for año in (2024, 2026):
        F, _ = FE[("antuco", año)]
        Fd = F.copy()
        Fd[:, :72] = False
        v = share_dias(ZV[("antuco", año)], Fd)
        allv.append(v)
        sh[str(año)] = {"dias": int(v.size), "share_d": _r(np.median(v)) if v.size else None,
                        "IC95": _r(boot_mediana(v, rng3))}
    v = np.concatenate(allv)
    sh["2024+2026"] = {"dias": int(v.size), "share_d": _r(np.median(v)) if v.size else None,
                       "IC95": _r(boot_mediana(v, rng3))}
    print("M3", json.dumps(sh), flush=True)

    # M4 (lectura): nieve contra 2025, Y11 y ACM en los disparos
    fs = {a: fs_dia(OPT[a]["antuco_fnieve"], OPT[a]["antuco_ts"]) for a in (2024, 2025, 2026)}
    fs25 = np.array([np.nanmedian(fs[2025][max(0, d - VENT_FS25):d + VENT_FS25 + 1]) for d in range(ND)])
    m4 = {"fs_media": {str(a): _r(np.nanmean(fs[a])) for a in fs}}
    rng4 = np.random.default_rng(SEMILLA)
    for año in (2024, 2026):
        F, E = FE[("antuco", año)]
        Fd = F.copy()
        Fd[:, :72] = False
        dfs = fs[año] - fs25
        tasa = np.array([Fd[d].sum() / E[d, 72:].sum() if E[d, 72:].sum() >= 20 else np.nan for d in range(ND)])
        ok = np.isfinite(dfs) & np.isfinite(tasa)
        rho = stats.spearmanr(tasa[ok], dfs[ok]) if ok.sum() >= 5 else None
        zv = ZV[("antuco", año)]
        y = ref_local(zv.Y11T[:ND].astype(float), E)
        ac = ref_local(zv.ACMT[:ND].astype(float), E)
        m4[str(año)] = {"dfs_media": _r(np.nanmean(dfs)), "dfs_dias": int(np.isfinite(dfs).sum()),
                        "spearman_tasa_dfs": None if rho is None else [_r(rho[0]), _r(rho[1]), int(ok.sum())],
                        "Y11_perm": prueba_perm([(Fd, E, y)], rng4),
                        "Y11_en_disparo_media_K": _r(np.nanmean(zv.Y11T[:ND][Fd])),
                        "ACM_perm": prueba_perm([(Fd, E, ac)], rng4),
                        "ACM_en_disparo_media": _r(np.nanmean(zv.ACMT[:ND][Fd]))}
    print("M4", json.dumps(m4), flush=True)

    # veredictos (§5)
    nd_tot = out["antuco"][2024]["dias_con_medible"] + out["antuco"][2026]["dias_con_medible"]
    m2c = {k: out["antuco"][2024]["M2"][k] + out["antuco"][2026]["M2"][k] for k in ("nublado", "despejado", "mezclado")}
    n2 = sum(m2c.values())
    if nd_tot < MIN_DIAS or min(out["antuco"][2024]["dias_con_medible"], out["antuco"][2026]["dias_con_medible"]) \
            < MIN_DIAS_AÑO:
        va = vb = "NO DECIDIBLE"
    else:
        J, a24, a26 = m1["2024+2026"], m1["2024"]["T"], m1["2026"]["T"]
        va = vb = "NO SE SOSTIENE"
        if J["p_alto"] <= ALFA_LADO:
            va = "SE SOSTIENE" if (a24 > 0 and a26 > 0 and m2c["nublado"] >= n2 / 2) else "NO CONCLUYENTE"
        if J["p_bajo"] <= ALFA_LADO:
            vb = "SE SOSTIENE" if (a24 < 0 and a26 < 0 and m2c["despejado"] >= n2 / 2) else "NO CONCLUYENTE"
        if va == vb == "NO SE SOSTIENE" and m2c["nublado"] < n2 / 2 and m2c["despejado"] < n2 / 2:
            va = vb = "MEZCLA"
    if sh["2024+2026"]["dias"] < MIN_DIAS:
        vc = "NO DECIDIBLE"
    elif sh["2024+2026"]["share_d"] > 0.5 and sh["2024"]["share_d"] > 0.5 and sh["2026"]["share_d"] > 0.5:
        vc = "SE SOSTIENE"
    elif sh["2024+2026"]["share_d"] < 0.5:
        vc = "NO SE SOSTIENE"
    else:
        vc = "NO CONCLUYENTE"
    res.update({"por_sitio": {s: {str(a): v for a, v in d.items()} for s, d in out.items()}, "M1": m1,
                "M1_informativo": info, "M2_antuco_2024_2026": m2c, "M3": sh, "M4": m4,
                "veredicto": {"a_nube": va, "b_nieve_roca": vb, "c_regional": vc}})
    print("VEREDICTO", res["veredicto"], f"{time.time() - t:.0f} s", flush=True)
    json.dump(res, open(os.path.join(RES, "s31i_resultado.json"), "w", encoding="utf-8"), ensure_ascii=False,
              indent=1, default=lambda o: o.item() if hasattr(o, "item") else str(o))


if __name__ == "__main__":
    {"pruebas": pruebas, "optica": optica, "medir": medir}[sys.argv[1]]()
