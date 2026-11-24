r"""S23a: el detector de S22b (con enmienda 1) con la referencia sacada de oct-nov 2025, un año sin pluma.
Implementa criterio_2026-11-24.md (commit 1594187, empujado antes de abrir un solo cuadro de 2025).

Por qué: desde julio de 2026 Chillán tiene pluma todos los días (Nicolás, cámaras del OVDAS). S22b armó su línea base
por píxel, su nublado de costumbre y su umbral con cuadros de 2026 en que VOLCAT no dibujó nada, y esos cuadros tenían
pluma: la base ya traía la pluma restada y el umbral quedaba en la cola de días con pluma. Aquí la regla es la misma
(se importa sin cambios) y la referencia sale de 2025, misma estación, mismo satélite y misma grilla.

Uso: python -I s23_medir.py pruebas | cubo | reproducir | seco | poder | medir
  cubo        arma BT11, BTD, ACM y M1 de 2025 desde los npz bajados por s22d_bajar_2025.py y corre I1 a I4.
  reproducir  comprobación de código: con la referencia de S22b (cuadros N de 2026) tiene que dar su ensayo en seco.
  seco, poder dentro de 2025 (cada día sin sí mismo); medir: los P de VOLCAT de 2026 contra el azar de 2025 y de 2026.
"""
import json
import os
import sys
import time
import warnings
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime, timedelta

import numpy as np
from scipy import stats

sys.stdout.reconfigure(encoding="utf-8")
warnings.simplefilter("ignore", RuntimeWarning)
AQUI = os.path.dirname(os.path.abspath(__file__))
OV = os.path.abspath(os.path.join(AQUI, "..", ".."))
RES = os.path.join(os.path.dirname(AQUI), "resultados")
sys.path.insert(0, os.path.join(OV, "s22b_pluma_vs_nubes", "scripts"))
import s22b_medir as B  # noqa: E402  (dinamica, borde, alcanzado, clases, parámetros de S22b: sin cambios)
M, H24, C29 = B.M, B.H24, B.C29

REF = r"D:\goes_notas\s22\s22d_2025"      # bajada de 2025 (C14, C15, ACMF por cuadro)
TRAB = r"D:\goes_notas\s23\s23a"          # cachés derivados (no son datos de SSEC)
T0R, NR = datetime(2025, 9, 21), 62       # 21-09-2025 a 21-11-2025, la misma ventana que 2026
NPIX = M.NY * M.NX
W_AZAR = 6                                # azar por hora: +-60 min (§4)
NOCHE = range(18, 54)                     # 03:00 a 08:50 UTC (I4)
I1_MIN, I3_MIN, I4_MIN = 0.90, 0.999, 0.90


# ---------- cubo de 2025 e instrumento (§3) ----------
def _npy(nombre):
    return os.path.join(TRAB, f"r25_{nombre}.npy")


def _m1_dia(args):
    bt, bd = args
    return np.array([M.m1_cuadro(bt[s], bd[s]) if np.isfinite(bt[s]).any() else np.full(M.NA, np.nan, np.float32)
                     for s in range(144)], np.float32)


def cubo(nproc=6):
    os.makedirs(TRAB, exist_ok=True)
    n = NR * 144
    r = {b: np.full((n, NPIX), np.nan, "float32") for b in (14, 15)}
    acm = np.full((n, NPIX), 255, "uint8")
    co = {14: [], 15: []}
    pres, scan_dist, n_acm = 0, 0, 0
    for i in range(n):
        dt = T0R + timedelta(minutes=10 * i)
        f = os.path.join(REF, "l1b", f"{dt:%Y%m%d_%H%M}.npz")
        if os.path.exists(f):
            with np.load(f) as z:
                s14, s15 = str(z["key14"]).split("_s")[1][:14], str(z["key15"]).split("_s")[1][:14]
                if s14 != s15 or s14[:11] != f"{dt:%Y}{dt.timetuple().tm_yday:03d}{dt:%H%M}":
                    scan_dist += 1                       # I2: el cuadro se descarta
                else:
                    for b in (14, 15):
                        r[b][i] = z[f"rad{b}"].ravel()
                        co[b].append(z[f"co{b}"])
                    pres += 1
        g = os.path.join(REF, "acm", f"{dt:%Y%m%d_%H%M}.npz")
        if os.path.exists(g):
            with np.load(g) as z:
                acm[i] = z["acm"].ravel()
                n_acm += 1
    cof = {b: np.median(np.array(co[b]), 0) for b in (14, 15)}
    bt11 = C29.bt_de_rad(r[14].astype("float64"), cof[14]).astype("float32")
    btd = (bt11 - C29.bt_de_rad(r[15].astype("float64"), cof[15])).astype("float32")
    hay = np.isfinite(bt11).any(1)
    cong = sum(1 for i in range(1, n) if hay[i] and hay[i - 1] and np.array_equal(r[14][i], r[14][i - 1], equal_nan=True))
    v = bt11[np.isfinite(bt11)]
    co26 = np.load(os.path.join(B.TRAB, "dev_co.npy"))
    # I4: misma grilla. BT11 media de noches despejadas por E1, 2025 contra 2026
    acmR = acm.reshape(NR, 144, NPIX)
    e1R = H24.despejada("chillan", acmR)
    bt26, acm26, _ = B.cargar_dev()
    e1T = H24.despejada("chillan", acm26)
    btR = bt11.reshape(NR, 144, NPIX)
    selR = [(d, s) for d in range(NR) for s in NOCHE if e1R[d, s] and hay[d * 144 + s]]
    selT = [(d, s) for d in range(B.NDEV) for s in NOCHE if e1T[d, s]]
    mR = np.nanmean(np.array([btR[d, s] for d, s in selR]), 0) if selR else np.full(NPIX, np.nan)
    mT = np.nanmean(np.array([np.asarray(bt26[d, s]) for d, s in selT]), 0) if selT else np.full(NPIX, np.nan)
    ok = np.isfinite(mR) & np.isfinite(mT)
    corr = float(np.corrcoef(mR[ok], mT[ok])[0, 1]) if ok.sum() > 100 else float("nan")
    inst = {"cuadros": n, "l1b_presentes": pres, "cobertura_l1b": pres / n, "acm_presentes": n_acm,
            "cobertura_acm": n_acm / n, "scan_distinto_descartados": scan_dist, "congelados": cong,
            "bt11_en_rango": float(((v > 180) & (v < 330)).mean()) if v.size else 0.0,
            "planck_dif_rel_max_c14": float(np.max(np.abs(cof[14] / co26[0] - 1))),
            "planck_dif_rel_max_c15": float(np.max(np.abs(cof[15] / co26[1] - 1))),
            "I4_noches_2025": len(selR), "I4_noches_2026": len(selT), "I4_correlacion": corr}
    inst["falla"] = [k for k, okk in (("I1", inst["cobertura_l1b"] >= I1_MIN and inst["cobertura_acm"] >= I1_MIN),
                                      ("I3", inst["bt11_en_rango"] >= I3_MIN and cong == 0),
                                      ("I4", np.isfinite(corr) and corr >= I4_MIN)) if not okk]
    os.makedirs(RES, exist_ok=True)
    json.dump(inst, open(os.path.join(RES, "instrumento_2025.json"), "w", encoding="utf-8"), indent=1)
    print(json.dumps(inst, indent=1), flush=True)
    t = time.time()
    btd3 = btd.reshape(NR, 144, NPIX)
    with ProcessPoolExecutor(nproc) as ex:
        m1 = np.array(list(ex.map(_m1_dia, [(btR[d], btd3[d]) for d in range(NR)])), np.float32)
    print(f"M1 de 2025 en {time.time() - t:.0f} s", flush=True)
    np.save(_npy("acm"), acmR)
    np.save(_npy("m1"), m1)
    np.save(_npy("bt11"), btR)


# ---------- el detector con referencia y blanco separados ----------
class Detector:
    """Referencia (de donde salen costumbre, base y umbral) y blanco (2026, donde se mide), en arreglos aparte.

    ref='2025': todos los cuadros de 2025 son referencia (año tranquilo; no hay clases de VOLCAT y no hacen falta).
    ref='2026N': la referencia de S22b (cuadros N de VOLCAT de los días de desarrollo de 2026); sólo para comprobar
    que este código reproduce el ensayo en seco de S22b."""

    def __init__(self, ref="2025", con_blanco=True):
        t = time.time()
        self.CLT = B.clases()                                  # (65, 144) clases VOLCAT de 2026
        bt26, acm26, m126 = B.cargar_dev()
        if ref == "2025":
            self.acmR, self.m1R = np.load(_npy("acm")), np.load(_npy("m1"))
            self.NULR = np.isfinite(self.m1R).any(2)
            self.DIASR = list(range(NR))
        else:
            self.acmR, self.m1R = acm26, m126
            self.NULR = self.CLT[:B.NDEV] == "N"
            self.DIASR = [d for d in range(B.NDEV) if (self.CLT[d] != "").any()]
        self.ref = ref
        self.E1R = H24.despejada("chillan", self.acmR)
        # nublado de costumbre por hora (enmienda 1 de S22b), sólo con la referencia
        sel = [(d, s) for d in self.DIASR for s in range(144) if self.NULR[d, s] and self.E1R[d, s]]
        nub = np.array([(self.acmR[d, s] >= 2) & (self.acmR[d, s] <= 3) for d, s in sel])
        ss = np.array([s for _, s in sel])
        self.ESTAT = np.zeros((144, NPIX), bool)
        self.n_costumbre = np.zeros(144, int)
        for s in range(144):
            dd = np.abs(ss - s) % 144
            dd = np.minimum(dd, 144 - dd)
            for w in B.COSTUMBRE_VENT:
                m = dd <= w
                if m.sum() >= B.MIN_COSTUMBRE:
                    self.ESTAT[s] = nub[m].mean(0) >= B.COSTUMBRE
                    self.n_costumbre[s] = int(m.sum())
                    break
        self.FDR, self.mmR = self._nubes(self.acmR, self.m1R)
        self.GATER = self.FDR <= B.G_MAX
        self._B, self._U = {}, {}
        # S de la referencia: cada día con la base sin ese día (como S22b)
        self.SR = np.full((len(self.acmR), 144), np.nan)
        self.KR = np.full((len(self.acmR), 144), -1, int)
        for d in self.DIASR:
            Bd = self.base(d)
            for s in range(144):
                if self.GATER[d, s]:
                    self.SR[d, s], self.KR[d, s], _ = M.estadistico(self.mmR[d, s] - Bd[s])
        print(f"referencia {ref} lista en {time.time() - t:.0f} s; costumbre por hora: mín {self.n_costumbre.min()}, "
              f"máx {self.n_costumbre.max()} cuadros", flush=True)
        if con_blanco:
            acmT = np.full((B.ND, 144, NPIX), 255, "uint8")
            m1T = np.full((B.ND, 144, M.NA), np.nan, np.float32)
            acmT[:B.NDEV], m1T[:B.NDEV] = acm26, m126
            acmT[B.NDEV:] = np.load(os.path.join(B.TRAB, "nuevo_acm.npy"))
            m1T[B.NDEV:] = np.load(os.path.join(B.TRAB, "nuevo_m1.npy"))
            self.acmT = acmT
            self.E1T = H24.despejada("chillan", acmT)
            self.FDT, self.mmT = self._nubes(acmT, m1T)
            self.GATET = self.FDT <= B.G_MAX
            B0 = self.base(None)
            self.ST = np.full((B.ND, 144), np.nan)
            self.KT = np.full((B.ND, 144), -1, int)
            for d in range(B.ND):
                for s in range(144):
                    if self.GATET[d, s]:
                        self.ST[d, s], self.KT[d, s], _ = M.estadistico(self.mmT[d, s] - B0[s])
            print(f"blanco 2026 listo en {time.time() - t:.0f} s", flush=True)

    def _nubes(self, acm, m1):
        FD = np.full(acm.shape[:2], np.nan)
        mm = m1.copy()
        for d in range(acm.shape[0]):
            for s in range(144):
                if not (acm[d, s] != 255).any():
                    continue
                nd = B.dinamica(acm[d, s], self.ESTAT[s])
                FD[d, s] = nd[M.AP].mean()
                mm[d, s][B.borde(nd)[M.AP]] = np.nan
        return FD, mm

    def base(self, excl):
        if excl in self._B:
            return self._B[excl]
        Bs = np.full((144, M.NA), np.nan, np.float32)
        pozo = [(d, x) for d in self.DIASR if d != excl for x in range(144)
                if self.NULR[d, x] and self.E1R[d, x] and self.GATER[d, x]]
        for s in range(144):
            rows = [self.mmR[d, x] for d, x in pozo if M.dslot(x, s) <= B.W_BASE]
            if len(rows) >= B.MIN_BASE:
                R = np.array(rows)
                n = np.isfinite(R).sum(0)
                Bs[s] = np.where(n >= B.MIN_BASE, np.nanmedian(R, 0), np.nan)
        self._B[excl] = Bs
        return Bs

    def umbral(self, excl):
        if excl in self._U:
            return self._U[excl]
        ds, ss, vs = [], [], []
        for d in self.DIASR:
            if d == excl:
                continue
            x = np.flatnonzero(self.NULR[d] & np.isfinite(self.SR[d]))
            ds += [d] * len(x)
            ss += list(x)
            vs += list(self.SR[d, x])
        ds, ss, vs = np.array(ds), np.array(ss), np.array(vs)
        U, info = [None] * 144, [None] * 144
        for s in range(144):
            dd = np.abs(ss - s) % 144
            dd = np.minimum(dd, 144 - dd)
            for w in B.VENTANAS_U:
                m = dd <= w
                n = int(m.sum())
                if n < B.MIN_POZO:
                    continue
                _, cnt = np.unique(ds[m], return_counts=True)
                if len(cnt) >= B.MIN_DIAS_U and cnt.max() / n <= B.MAX_FRAC_U:
                    U[s] = float(np.percentile(vs[m], B.PCT_U))
                    info[s] = {"ventana_min": 10 * w, "n": n, "dias": int(len(cnt)),
                               "frac_max_dia": round(float(cnt.max() / n), 3)}
                    break
        self._U[excl] = (U, info)
        return U, info


def disparos(S, K, d, U):
    """F y evaluado de un día (igual a Datos.disparos de S22b); el anterior a las 00:00 es el último del día previo."""
    F = np.zeros(144, bool)
    ev = np.zeros(144, bool)
    for s in range(144):
        if U[s] is None or not np.isfinite(S[d, s]):
            continue
        ev[s] = True
        dp, sp = (d, s - 1) if s else (d - 1, 143)
        if dp < 0 or U[sp] is None or not np.isfinite(S[dp, sp]):
            continue
        F[s] = S[d, s] <= U[s] and S[dp, sp] <= U[sp] and M.vecinos(K[d, s], K[dp, sp])
    return F, ev


def poisson_binomial_cola(ps, k):
    """P(X >= k), X suma de Bernoulli independientes con probabilidades ps (exacta, por convolución)."""
    dist = np.array([1.0])
    for p in ps:
        dist = np.convolve(dist, [1.0 - p, p])
    return float(dist[k:].sum())


def azar_por_hora(slots, alc):
    """r(h) = fracción alcanzada de los cuadros con hora a +-60 min de h (slots, alc: arreglos paralelos)."""
    slots, alc = np.asarray(slots), np.asarray(alc, float)
    r = np.full(144, np.nan)
    for s in range(144):
        dd = np.abs(slots - s) % 144
        dd = np.minimum(dd, 144 - dd)
        m = dd <= W_AZAR
        if m.any():
            r[s] = alc[m].mean()
    return r


def _r(x):
    return None if (x is None or not np.isfinite(x)) else round(float(x), 4)


# ---------- pruebas de código ----------
def pruebas():
    assert abs(poisson_binomial_cola([0.5, 0.5], 1) - 0.75) < 1e-12
    assert abs(poisson_binomial_cola([0.1] * 10, 0) - 1.0) < 1e-12
    p = 0.07
    assert abs(poisson_binomial_cola([p] * 20, 3) - stats.binom.sf(2, 20, p)) < 1e-12
    r = azar_por_hora([0, 1, 143, 72], [1, 0, 1, 0])
    assert abs(r[0] - 2 / 3) < 1e-12 and r[72] == 0 and np.isnan(r[36])
    # disparos: persistencia exige el cuadro anterior bajo umbral y tajada vecina
    S = np.full((2, 144), 1.0)
    K = np.zeros((2, 144), int)
    U = [0.0] * 144
    S[1, 10], S[1, 11], K[1, 11] = -1, -1, 1
    S[1, 20], S[1, 21], K[1, 21] = -1, -1, 6
    S[0, 143], S[1, 0] = -1, -1
    F, ev = disparos(S, K, 1, U)
    assert F[11] and not F[10] and not F[21] and F[0] and ev.all()
    print("pruebas OK (4 de 4)")


# ---------- comprobación de código contra S22b ----------
def reproducir():
    """Con la referencia de S22b, el ensayo en seco tiene que dar el de S22b (resultados/seco.json de S22b)."""
    D = Detector(ref="2026N", con_blanco=False)
    fas = []
    for d in D.DIASR:
        U, _ = D.umbral(d)
        F, ev = disparos(D.SR, D.KR, d, U)
        m = ev & D.NULR[d]
        if m.sum():
            fas.append(float((F & m).sum() / m.sum()))
    s22b = json.load(open(os.path.join(OV, "s22b_pluma_vs_nubes", "resultados", "seco.json"), encoding="utf-8"))
    print(f"seco con referencia 2026N: {np.mean(fas):.6f}; S22b: {s22b['fa_media_por_dia']:.6f}")
    assert abs(np.mean(fas) - s22b["fa_media_por_dia"]) < 1e-9, "no reproduce S22b"
    print("reproduce S22b: OK")


# ---------- ensayo en seco y azar por hora en 2025 (§4) ----------
def _seco_2025(D):
    por_dia, slots, alc, filas = [], [], [], []
    for d in D.DIASR:
        U, _ = D.umbral(d)
        F, ev = disparos(D.SR, D.KR, d, U)
        n = int(ev.sum())
        por_dia.append({"dia": f"{T0R + timedelta(days=d):%Y-%m-%d}", "evaluados": n, "disparos": int(F.sum()),
                        "fa": (float(F.sum() / n) if n else None)})
        for s in np.flatnonzero(ev):
            slots.append(s)
            alc.append(B.alcanzado(F, ev, s)[1])
            filas.append((s // 18, bool(F[s]), int(D.KR[d, s])))
    return por_dia, np.array(slots), np.array(alc), filas


def seco():
    D = Detector(ref="2025", con_blanco=False)
    por_dia, slots, alc, filas = _seco_2025(D)
    fas = [x["fa"] for x in por_dia if x["fa"] is not None]
    U, info = D.umbral(None)
    out = {"fa_media_por_dia": float(np.mean(fas)), "fa_max": B.FA_MAX, "aprobado": float(np.mean(fas)) <= B.FA_MAX,
           "evaluados": int(len(slots)), "dias_con_evaluados": len(fas),
           "por_hora": {f"{3 * b:02d}-{3 * b + 2:02d} UTC": {"n": sum(1 for h, *_ in filas if h == b),
                                                           "fa": _r(np.mean([f for h, f, _ in filas if h == b]))
                                                           if any(h == b for h, *_ in filas) else None}
                        for b in range(8)},
           "horas_sin_umbral": [M.hhmm(s) for s in range(144) if U[s] is None],
           "U_por_hora": {M.hhmm(s): _r(U[s]) for s in range(144)}, "U_info": {M.hhmm(s): info[s] for s in range(144)},
           "por_dia": por_dia}
    s22b = json.load(open(os.path.join(OV, "s22b_pluma_vs_nubes", "resultados", "seco.json"), encoding="utf-8"))
    out["U_S22b_por_hora"] = s22b["U_por_hora"]
    os.makedirs(RES, exist_ok=True)
    json.dump(out, open(os.path.join(RES, "seco.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps({k: out[k] for k in ("fa_media_por_dia", "aprobado", "evaluados", "dias_con_evaluados",
                                          "por_hora", "horas_sin_umbral")}, ensure_ascii=False, indent=1))


def poder():
    D = Detector(ref="2025", con_blanco=False)
    pares = []
    for d in D.DIASR:
        U, _ = D.umbral(d)
        for s in range(1, 144):
            if (U[s] is not None and U[s - 1] is not None and np.isfinite(D.SR[d, s]) and np.isfinite(D.SR[d, s - 1])):
                pares.append((d, s))
    rng = np.random.default_rng(B.SEMILLA)
    elegidos = rng.choice(len(pares), B.N_POD, replace=len(pares) < B.N_POD)
    azs = rng.uniform(0, 360, B.N_POD)
    out = {"pares_disponibles": len(pares), "dias_de_los_pares": len({pares[e][0] for e in elegidos})}
    for a in B.FIRMAS:
        hits = 0
        for e, az in zip(elegidos, azs):
            d, s = pares[e]
            Bd = D.base(d)
            U, _ = D.umbral(d)
            sel = M.pixeles_rayo(az)
            ksec = int(az // 30) % M.NSEC
            res = []
            for x in (s - 1, s):
                v = D.mmR[d, x] - Bd[x]
                v[sel] -= a
                res.append(M.estadistico(v))
            (S1, k1, _), (S2, k2, _) = res
            if (np.isfinite(S1) and np.isfinite(S2) and S1 <= U[s - 1] and S2 <= U[s] and M.vecinos(k1, k2)
                    and M.vecinos(k2, ksec)):
                hits += 1
        out[f"{a:.2f}"] = hits / B.N_POD
        print(f"poder a {a:.2f} K: {hits / B.N_POD:.3f}", flush=True)
    json.dump(out, open(os.path.join(RES, "poder.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)


# ---------- medida decisiva en 2026 (§4) ----------
def medir():
    inst = json.load(open(os.path.join(RES, "instrumento_2025.json"), encoding="utf-8"))
    seco_ = json.load(open(os.path.join(RES, "seco.json"), encoding="utf-8"))
    pod = json.load(open(os.path.join(RES, "poder.json"), encoding="utf-8"))
    D = Detector(ref="2025", con_blanco=True)
    _, sl25, al25, filas25 = _seco_2025(D)
    r25 = azar_por_hora(sl25, al25)
    U, _ = D.umbral(None)
    FF = {d: disparos(D.ST, D.KT, d, U) for d in range(B.ND)}
    P, N, todos = [], [], []           # (día, slot, alcanzado)
    for d in range(B.ND):
        F, ev = FF[d]
        for s in np.flatnonzero(ev):
            a = B.alcanzado(F, ev, s)[1]
            todos.append((d, s, a, bool(F[s]), int(D.KT[d, s])))
            if D.CLT[d, s] == "P":
                P.append((d, s, a))
            elif D.CLT[d, s] == "N":
                N.append((d, s, a))
    rN = azar_por_hora([s for _, s, _ in N], [a for *_, a in N])
    te, th = len(P), sum(a for *_, a in P)
    p25 = poisson_binomial_cola([r25[s] for _, s, _ in P], th) if te else None
    pN = poisson_binomial_cola([rN[s] for _, s, _ in P], th) if te else None
    E25 = float(sum(r25[s] for _, s, _ in P))
    EN = float(sum(rN[s] for _, s, _ in P))
    R = th / te if te else None
    # episodios
    eps_t = eps_h = 0
    por_dia = []
    for d in range(B.ND):
        Ps = np.flatnonzero(D.CLT[d] == "P")
        if not len(Ps):
            continue
        F, ev = FF[d]
        for ep in M.episodios(list(Ps)):
            if not ev[ep].any():
                continue
            eps_t += 1
            eps_h += bool(F[max(0, ep[0] - 3):min(144, ep[-1] + 4)].any())
        pe = [(s, a) for dd, s, a in P if dd == d]
        por_dia.append({"dia": B.fecha(d), "P": int(len(Ps)), "P_evaluados": len(pe), "P_alcanzados": sum(a for _, a in pe),
                        "P_no_evaluables_por_nubes": int(sum(not D.GATET[d, s] for s in Ps)),
                        "disparos_del_dia": int(FF[d][0].sum()),
                        "tajadas_de_los_disparos": np.bincount(D.KT[d][FF[d][0]], minlength=12).tolist()})
    fallas = inst["falla"]
    if fallas or not seco_["aprobado"]:
        ver = "INVÁLIDA"
    elif te < B.MIN_P_NUEVO:
        ver = "NO DECIDIBLE"
    elif p25 <= B.P_MAX:
        ver = "CONFIRMA" if R >= B.R_MIN else "PARCIAL"
    else:
        ver = "NO LLEGA" if pod["0.33"] >= 0.8 else "SIN PODER"
    etiqueta = ("SEPARA VOLCAT" if (pN is not None and pN <= B.P_MAX) else "NO SEPARA VOLCAT DEL RESTO DE 2026")
    # informativo: tasa de disparo por franja, 2026 contra 2025, y tajadas de día y de noche
    fr = {}
    for b in range(8):
        v26 = [f for _, s, _, f, _ in todos if s // 18 == b]
        v25 = [f for h, f, _ in filas25 if h == b]
        fr[f"{3 * b:02d}-{3 * b + 2:02d} UTC"] = {"n_2026": len(v26), "F_2026": _r(np.mean(v26)) if v26 else None,
                                               "n_2025": len(v25), "F_2025": _r(np.mean(v25)) if v25 else None}
    taj = {}
    for nom, rng_ in (("dia_12a24", range(72, 144)), ("noche_00a09", range(0, 54))):
        k26 = [k for _, s, _, f, k in todos if f and s in rng_]
        k25 = [k for h, f, k in filas25 if f and h * 18 in rng_]
        taj[nom] = {"2026": np.bincount(k26, minlength=12).tolist(), "2025": np.bincount(k25, minlength=12).tolist()}
    out = {"veredicto": ver, "etiqueta": etiqueta, "instrumento_falla": fallas, "seco_fa": seco_["fa_media_por_dia"],
           "poder": pod, "P_evaluados": te, "P_alcanzados": th, "R": R, "E25": E25, "p25": p25, "EN_2026": EN, "pN": pN,
           "N_2026_evaluados": len(N), "r_N_2026": (float(np.mean([a for *_, a in N])) if N else None),
           "r_2025_global": float(al25.mean()) if len(al25) else None,
           "fisher_P_vs_2025": float(stats.fisher_exact([[th, te - th], [int(al25.sum()), int(len(al25) - al25.sum())]],
                                                        alternative="greater")[1]) if te else None,
           "episodios": eps_t, "episodios_alcanzados": eps_h, "S22b_desarrollo": "R 13 de 54, r_N 0,07",
           "tasa_disparo_por_franja": fr, "tajadas_disparos": taj, "por_dia": por_dia,
           "series": {B.fecha(d): [{"hora": M.hhmm(s), "S": _r(D.ST[d, s]), "U": _r(U[s]), "k": int(D.KT[d, s]),
                                    "F": bool(FF[d][0][s]), "evaluado": bool(FF[d][1][s]),
                                    "nube_dinamica": _r(D.FDT[d, s]), "E1": bool(D.E1T[d, s]), "VOLCAT": D.CLT[d, s]}
                                   for s in range(72, 144)]
                      for d in (B.dia_idx(x) for x in ("2026-10-28", "2026-11-08", "2026-11-10", "2026-11-11",
                                                       "2026-11-14"))}}
    json.dump(out, open(os.path.join(RES, "s23a_resultado.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps({k: v for k, v in out.items() if k not in ("series",)}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    {"pruebas": pruebas, "cubo": cubo, "reproducir": reproducir, "seco": seco, "poder": poder,
     "medir": medir}[sys.argv[1]]()
