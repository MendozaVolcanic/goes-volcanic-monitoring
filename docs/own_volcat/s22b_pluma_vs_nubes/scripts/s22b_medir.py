r"""S22b: el detector por tajadas de S22a sin bordes de nube, con compuerta de cielo, línea base por píxel despejada y
nulo = cuadros N de VOLCAT. Implementa criterio_2026-11-24.md (commit 6af2d27, empujado antes de medir días nuevos).

Por qué así (detalle en el criterio): el 15-11 S22a disparaba en el borde entre nubes sobre Chile y el lado
argentino despejado; cerca de una nube, el pareo por BT11 y el contraste de humedad entre los dos lados de la
divisoria bajan la BTD sin ceniza. Por eso se borran las nubes dinámicas y sus vecinos, el detector se calla si más
de la mitad del anillo está nublado, a cada píxel se le resta lo que suele marcar con cielo despejado a esa hora, y el
umbral sale de cuadros en que VOLCAT no mostró nada (no de días placebo, que eran casi todos nublados).

Uso: python -I s22b_medir.py pruebas | cubo_nuevo | seco | poder | desarrollo | confirmar
  seco, poder y desarrollo sólo usan días hasta el 21-11 (ya mirados); confirmar exige resultados/seco.json y
  resultados/poder.json, y escribe primero la falsa alarma de los días nuevos y después el recuerdo.
"""
import csv
import glob
import json
import os
import sys
import time
import warnings
from datetime import datetime, timedelta

import numpy as np
from scipy import ndimage, stats

sys.stdout.reconfigure(encoding="utf-8")
warnings.simplefilter("ignore", RuntimeWarning)
AQUI = os.path.dirname(os.path.abspath(__file__))
OV = os.path.abspath(os.path.join(AQUI, "..", ".."))
RES = os.path.join(os.path.dirname(AQUI), "resultados")
sys.path.insert(0, os.path.join(OV, "s22a_detector_sectores", "scripts"))
sys.path.insert(0, os.path.join(OV, "h24_pulsos_reav", "scripts"))
sys.path.insert(0, os.path.join(OV, "h29_pluma_0811", "scripts"))
import s22a_medir as M  # noqa: E402  (anillo, tajadas, M1, estadístico, persistencia: sin cambios)
import h24_medir as H24  # noqa: E402  (cargar, despejada = E1)
import h29_comun as C29  # noqa: E402  (Planck)

TRAB = r"D:\goes_notas\s22\s22b"          # cachés derivados (no son datos de SSEC)
NDEV = H24.NDIAS                          # 62 días: 21-09 a 21-11 (desarrollo)
NUEVOS = ["2026-11-22", "2026-11-23", "2026-11-24"]
ND = NDEV + len(NUEVOS)
FRAMES_CALOR = os.path.join(OV, "calor_rayos", "resultados", "frames_calor.csv")
CLASES_NUEVAS = os.path.join(RES, "volcat_clases_22a24nov.csv")

# ---------- parámetros del criterio (§2, §3) ----------
G_MAX = 0.5               # compuerta: fracción máxima del anillo con nube dinámica
COSTUMBRE = 0.5           # nublado de costumbre: ACM 2-3 en >= 50 % de los cuadros N despejados por E1
W_BASE, MIN_BASE = 9, 8   # línea base: +-90 min, mínimo 8 valores por píxel
VENTANAS_U = (6, 12, 18)  # +-60, +-120, +-180 min
MIN_POZO, MIN_DIAS_U, MAX_FRAC_U, PCT_U = 40, 5, 0.35, 5.0
FA_MAX = 0.05
N_POD, SEMILLA = 200, 0
FIRMAS = (0.33, 0.97)
R_MIN, P_MAX, MIN_P_NUEVO, MIN_N_NUEVO = 0.50, 0.05, 5, 50
K3 = np.ones((3, 3), bool)


def fecha(d):
    return f"{M.T0 + timedelta(days=int(d)):%Y-%m-%d}"


def dia_idx(s):
    return (datetime.strptime(s, "%Y-%m-%d") - M.T0).days


# ---------- datos ----------
def _dev_npy(nombre):
    return os.path.join(TRAB, f"dev_{nombre}.npy")


def cargar_dev():
    """BT11, BTD, ACM y M1 de 21-09 a 21-11 (cubos de H23/H24 y caché de M1 de S22a, completado aquí)."""
    if not all(os.path.exists(_dev_npy(n)) for n in ("bt11", "btd", "acm", "m1")):
        r14, r15, acm, co14, co15 = H24.cargar()
        bt11 = C29.bt_de_rad(r14.astype("float64"), co14).astype("float32")
        btd = (bt11 - C29.bt_de_rad(r15.astype("float64"), co15)).astype("float32")
        np.save(_dev_npy("bt11"), bt11)
        np.save(_dev_npy("btd"), btd)
        np.save(_dev_npy("acm"), acm)
        np.save(_dev_npy("co"), np.array([co14, co15]))
        m1 = np.full((NDEV, 144, M.NA), np.nan, np.float32)
        hecho = np.zeros(NDEV, bool)
        for nom in ("placebo", "actividad"):
            z = np.load(os.path.join(M.CACHE, f"m1_{nom}.npz"))
            for j, d in enumerate(z["dias"]):
                m1[d] = z["m1"][j]
                hecho[d] = True
        for d in np.flatnonzero(~hecho):
            for s in range(144):
                m1[d, s] = M.m1_cuadro(bt11[d, s], btd[d, s])
        np.save(_dev_npy("m1"), m1)
    return (np.load(_dev_npy("bt11"), mmap_mode="r"), np.load(_dev_npy("acm")), np.load(_dev_npy("m1")))


def cubo_nuevo():
    """Arma BT11, BTD, ACM y M1 de los días nuevos desde los npz bajados (s22b_bajar.py), con las comprobaciones de
    instrumento de h23_cubo.py: mismo inicio de scan en C14 y C15 (I2), BT11 en rango y cuadros no congelados (I3).
    La cobertura (I1) se informa hasta el último cuadro con archivo."""
    n = len(NUEVOS) * 144
    r = {b: np.full((n, M.NY * M.NX), np.nan, "float32") for b in (14, 15)}
    acm = np.full((n, M.NY * M.NX), 255, "uint8")
    co = {14: [], 15: []}
    t0 = datetime.strptime(NUEVOS[0], "%Y-%m-%d")
    pres, scan_dist, ult = 0, 0, -1
    for i in range(n):
        dt = t0 + timedelta(minutes=10 * i)
        f = os.path.join(TRAB, "l1b", f"{dt:%Y%m%d_%H%M}.npz")
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
        g = os.path.join(TRAB, "acm", f"{dt:%Y%m%d_%H%M}.npz")
        if os.path.exists(g):
            with np.load(g) as z:
                acm[i] = z["acm"].ravel()
    cof = {b: np.median(np.array(co[b]), 0) for b in (14, 15)}
    co_dev = np.load(_dev_npy("co"))
    bt11 = C29.bt_de_rad(r[14].astype("float64"), cof[14]).astype("float32")
    btd = (bt11 - C29.bt_de_rad(r[15].astype("float64"), cof[15])).astype("float32")
    hay = np.isfinite(bt11).any(1)
    cong = sum(1 for i in range(1, n) if hay[i] and hay[i - 1] and np.array_equal(r[14][i], r[14][i - 1], equal_nan=True))
    v = bt11[np.isfinite(bt11)]
    inst = {"cuadros_hasta_el_ultimo": ult + 1, "presentes": pres, "cobertura": pres / max(ult + 1, 1),
            "ultimo": f"{t0 + timedelta(minutes=10 * ult):%Y-%m-%d %H:%M}", "scan_distinto": scan_dist,
            "congelados": cong, "bt11_en_rango": float(((v > 180) & (v < 330)).mean()),
            "planck_igual_a_desarrollo": bool(np.max(np.abs(cof[14] / co_dev[0] - 1)) < 1e-5
                                              and np.max(np.abs(cof[15] / co_dev[1] - 1)) < 1e-5),
            "acm_presentes": int((acm != 255).any(1).sum())}
    inst["falla"] = [k for k, ok in (("I1", inst["cobertura"] >= 0.95), ("I2", scan_dist == 0),
                                     ("I3", inst["bt11_en_rango"] >= 0.999 and cong == 0)) if not ok]
    m1 = np.full((n, M.NA), np.nan, np.float32)
    for i in range(n):
        if hay[i]:
            m1[i] = M.m1_cuadro(bt11[i], btd[i])
    np.save(os.path.join(TRAB, "nuevo_bt11.npy"), bt11.reshape(len(NUEVOS), 144, -1))
    np.save(os.path.join(TRAB, "nuevo_acm.npy"), acm.reshape(len(NUEVOS), 144, -1))
    np.save(os.path.join(TRAB, "nuevo_m1.npy"), m1.reshape(len(NUEVOS), 144, -1))
    os.makedirs(RES, exist_ok=True)
    json.dump(inst, open(os.path.join(RES, "instrumento_nuevo.json"), "w", encoding="utf-8"), indent=1)
    print(json.dumps(inst, indent=1))


def clases():
    """Clase VOLCAT (dia, slot): 'P', 'N', 'otro' o '' (sin PNG)."""
    CL = np.full((ND, 144), "", object)
    for fn in (FRAMES_CALOR, CLASES_NUEVAS):
        if not os.path.exists(fn):
            continue
        with open(fn, encoding="utf-8") as f:
            for r in csv.DictReader(f):
                d, s = dia_idx(r["dt"][:10]), M.slot(r["dt"][11:16])
                if 0 <= d < ND:
                    CL[d, s] = r["clase"]
    return CL


class Datos:
    """Todo lo que la regla necesita, para los 62 días de desarrollo y los nuevos si están armados."""

    def __init__(self, con_nuevos=False):
        t = time.time()
        bt11, acm, m1 = cargar_dev()
        self.acm = np.full((ND, 144, M.NY * M.NX), 255, "uint8")
        self.acm[:NDEV] = acm
        self.m1 = np.full((ND, 144, M.NA), np.nan, np.float32)
        self.m1[:NDEV] = m1
        self.bt_dev = bt11
        self.con_nuevos = con_nuevos
        if con_nuevos:
            self.acm[NDEV:] = np.load(os.path.join(TRAB, "nuevo_acm.npy"))
            self.m1[NDEV:] = np.load(os.path.join(TRAB, "nuevo_m1.npy"))
        self.E1 = H24.despejada("chillan", self.acm)
        self.CL = clases()
        self.DEV = [d for d in range(NDEV) if (self.CL[d] != "").any()]     # días de desarrollo con clase VOLCAT
        self.NUL = self.CL == "N"
        self.NUL[NDEV:] = False if not con_nuevos else self.NUL[NDEV:]
        # nublado de costumbre: sólo con cuadros N despejados por E1 del desarrollo
        sel = [(d, s) for d in self.DEV for s in range(144) if self.NUL[d, s] and self.E1[d, s]]
        a = np.array([self.acm[d, s] for d, s in sel])
        self.ESTAT = ((a >= 2) & (a <= 3)).mean(0) >= COSTUMBRE
        self.n_costumbre = len(sel)
        # nube dinámica, borde y compuerta
        self.FD = np.zeros((ND, 144))
        self.mm = self.m1.copy()
        for d in range(ND):
            for s in range(144):
                nd = dinamica(self.acm[d, s], self.ESTAT)
                self.FD[d, s] = nd[M.AP].mean() if (self.acm[d, s] != 255).any() else np.nan
                self.mm[d, s][borde(nd)[M.AP]] = np.nan
        self.GATE = self.FD <= G_MAX
        print(f"datos listos en {time.time() - t:.0f} s; días de desarrollo con clase: {len(self.DEV)}; "
              f"cuadros para nublado de costumbre: {self.n_costumbre}", flush=True)
        self._B, self._U = {}, {}
        self.S = np.full((ND, 144), np.nan)
        self.K = np.full((ND, 144), -1, int)
        for d in range(ND):
            if d >= NDEV and not con_nuevos:
                continue
            B = self.base(d if d in self.DEV else None)
            for s in range(144):
                if self.GATE[d, s]:
                    self.S[d, s], self.K[d, s], _ = M.estadistico(self.mm[d, s] - B[s])
        print(f"S calculado en {time.time() - t:.0f} s", flush=True)

    def base(self, excl):
        """Línea base por píxel (144, NA) con cuadros N despejados por E1 que pasan la compuerta, sin el día excl."""
        if excl in self._B:
            return self._B[excl]
        B = np.full((144, M.NA), np.nan, np.float32)
        pozo = [(d, x) for d in self.DEV if d != excl for x in range(144)
                if self.NUL[d, x] and self.E1[d, x] and self.GATE[d, x]]
        for s in range(144):
            rows = [self.mm[d, x] for d, x in pozo if M.dslot(x, s) <= W_BASE]
            if len(rows) >= MIN_BASE:
                R = np.array(rows)
                n = np.isfinite(R).sum(0)
                B[s] = np.where(n >= MIN_BASE, np.nanmedian(R, 0), np.nan)
        self._B[excl] = B
        return B

    def umbral(self, excl):
        """U por hora (144) con los cuadros N evaluados del desarrollo, sin el día excl."""
        if excl in self._U:
            return self._U[excl]
        ds, ss, vs = [], [], []
        for d in self.DEV:
            if d == excl:
                continue
            x = np.flatnonzero(self.NUL[d] & np.isfinite(self.S[d]))
            ds += [d] * len(x)
            ss += list(x)
            vs += list(self.S[d, x])
        ds, ss, vs = np.array(ds), np.array(ss), np.array(vs)
        U, info = [None] * 144, [None] * 144
        for s in range(144):
            dd = np.abs(ss - s) % 144
            dd = np.minimum(dd, 144 - dd)
            for w in VENTANAS_U:
                m = dd <= w
                n = int(m.sum())
                if n < MIN_POZO:
                    continue
                _, cnt = np.unique(ds[m], return_counts=True)
                if len(cnt) >= MIN_DIAS_U and cnt.max() / n <= MAX_FRAC_U:
                    U[s] = float(np.percentile(vs[m], PCT_U))
                    info[s] = {"ventana_min": 10 * w, "n": n, "dias": int(len(cnt)),
                               "frac_max_dia": round(float(cnt.max() / n), 3)}
                    break
        self._U[excl] = (U, info)
        return U, info

    def disparos(self, d, U, S=None, K=None):
        """F y evaluado de un día; el cuadro anterior a las 00:00 es el último del día anterior."""
        S = self.S if S is None else S
        K = self.K if K is None else K
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


def dinamica(a, estat):
    return ((a >= 2) & (a <= 3)) & ~estat


def borde(nd):
    return ndimage.binary_dilation(nd.reshape(M.NY, M.NX), K3).ravel()


def _r(x):
    return None if (x is None or not np.isfinite(x)) else round(float(x), 4)


def alcanzado(F, ev, s):
    return bool(ev[s]), bool(ev[s] and F[max(0, s - 1):min(144, s + 2)].any())


# ---------- pruebas ----------
def pruebas():
    est = np.zeros(M.NY * M.NX, bool)
    est[5] = True
    a = np.zeros(M.NY * M.NX, "uint8")
    a[[5, 2000]] = 3
    nd = dinamica(a, est)
    assert nd[2000] and not nd[5] and nd.sum() == 1          # la nube de costumbre no cuenta como dinámica
    b = borde(nd)
    r, c = divmod(2000, M.NX)
    assert b.sum() == 9 and b[(r - 1) * M.NX + c - 1] and b[(r + 1) * M.NX + c + 1]
    assert not b[(r + 2) * M.NX + c]                          # el borde es 3 x 3, no más
    # umbral: pozo con un día dominante no cumple; con 5 días parejos sí
    class _D(Datos):
        def __init__(self):
            self.DEV = list(range(6))
            self.NUL = np.zeros((ND, 144), bool)
            self.S = np.full((ND, 144), np.nan)
            self._U = {}
    x = _D()
    x.NUL[:5, 60:70] = True
    x.S[:5, 60:70] = np.arange(50).reshape(5, 10) / 10.0
    U, info = x.umbral(None)
    assert U[65] is not None and info[65]["dias"] == 5 and abs(U[65] - np.percentile(np.arange(50) / 10.0, 5)) < 1e-9
    x._U = {}
    U2, _ = x.umbral(4)                                         # sin un día quedan 40 de 4 días: no cumple
    assert U2[65] is None
    x._U = {}
    x.NUL[5, 60:100] = True
    x.S[5, 60:100] = 0.0
    U3, info3 = x.umbral(None)                                  # a las 14:10 domina un día (69 % a +-180 min): sin U
    assert U3[85] is None and info3[85] is None and U3[65] is not None
    print("pruebas OK (5 de 5)")


# ---------- ensayo en seco y composición del nulo (§3) ----------
def seco():
    D = Datos()
    por_dia, filas = [], []
    for d in D.DEV:
        U, _ = D.umbral(d)
        F, ev = D.disparos(d, U)
        m = ev & D.NUL[d]
        n = int(m.sum())
        por_dia.append({"dia": fecha(d), "N": int(D.NUL[d].sum()), "N_compuerta": int((D.NUL[d] & D.GATE[d]).sum()),
                        "N_evaluados": n, "disparos": int((F & m).sum()),
                        "fa": (float((F & m).sum() / n) if n else None)})
        for s in np.flatnonzero(m):
            filas.append((s // 18, bool(D.E1[d, s]), bool(F[s])))
    fas = [x["fa"] for x in por_dia if x["fa"] is not None]
    fa_media = float(np.mean(fas))
    fa_pool = float(np.mean([f for *_, f in filas]))
    por_hora = {}
    for b in range(8):
        v = [f for h, _, f in filas if h == b]
        por_hora[f"{3 * b:02d}-{3 * b + 2:02d} UTC"] = {"n": len(v), "fa": (float(np.mean(v)) if v else None)}
    U, info = D.umbral(None)
    kn = np.concatenate([D.K[d][D.NUL[d] & np.isfinite(D.S[d])] for d in D.DEV])
    # composición del nulo por hora
    comp = {}
    for b in range(8):
        dd = [d for d in D.DEV for s in range(18 * b, 18 * b + 18) if D.NUL[d, s] and np.isfinite(D.S[d, s])]
        u, c = np.unique(dd, return_counts=True)
        comp[f"{3 * b:02d}-{3 * b + 2:02d} UTC"] = {fecha(k)[5:]: int(v) for k, v in zip(u, c)}
    # nube dinámica en los placebo de S22a frente a los P de VOLCAT (lo que motivó la compuerta)
    plac = [M.dia_idx(x) for x in M.PLACEBO_TXT]
    fd_plac = D.FD[plac][:, 72:144].ravel()
    fd_P = np.array([D.FD[d, s] for d in D.DEV for s in range(144) if D.CL[d, s] == "P"])
    out = {"fa_media_por_dia": fa_media, "fa_pozo": fa_pool, "fa_max": FA_MAX, "aprobado": fa_media <= FA_MAX,
           "por_dia": por_dia, "por_hora": por_hora,
           "por_E1": {k: {"n": len(v), "fa": (float(np.mean(v)) if v else None)} for k, v in
                      (("despejado", [f for _, e, f in filas if e]), ("nublado", [f for _, e, f in filas if not e]))},
           "horas_sin_umbral": [M.hhmm(s) for s in range(144) if U[s] is None],
           "U_por_hora": {M.hhmm(s): _r(U[s]) for s in range(144)}, "U_info": {M.hhmm(s): info[s] for s in range(144)},
           "tajada_minimo_en_N": (np.bincount(kn, minlength=12) / len(kn)).round(3).tolist(), "n_N_evaluados": int(len(kn)),
           "composicion_nulo_por_hora": comp,
           "nube_dinamica_placebo_S22a_12a24": {"mediana": float(np.nanmedian(fd_plac)),
                                                "frac_pasa_compuerta": float(np.nanmean(fd_plac <= G_MAX))},
           "nube_dinamica_P_VOLCAT": {"n": int(len(fd_P)), "mediana": float(np.nanmedian(fd_P)),
                                      "max": float(np.nanmax(fd_P))},
           "pixeles_nublados_de_costumbre": int(D.ESTAT[M.AP].sum()),
           "por_tajada_costumbre": np.bincount(M.SEC[D.ESTAT[M.AP]], minlength=12).tolist()}
    os.makedirs(RES, exist_ok=True)
    json.dump(out, open(os.path.join(RES, "seco.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps({k: out[k] for k in ("fa_media_por_dia", "fa_pozo", "aprobado", "por_hora", "por_E1",
                                          "horas_sin_umbral", "tajada_minimo_en_N", "n_N_evaluados",
                                          "nube_dinamica_placebo_S22a_12a24", "nube_dinamica_P_VOLCAT")},
                     ensure_ascii=False, indent=1))
    for x in por_dia:
        print(x)


# ---------- poder (§3) ----------
def poder():
    D = Datos()
    pares = []
    for d in D.DEV:
        U, _ = D.umbral(d)
        for s in range(1, 144):
            if (D.NUL[d, s] and D.NUL[d, s - 1] and U[s] is not None and U[s - 1] is not None
                    and np.isfinite(D.S[d, s]) and np.isfinite(D.S[d, s - 1])):
                pares.append((d, s))
    rng = np.random.default_rng(SEMILLA)
    elegidos = rng.choice(len(pares), N_POD, replace=len(pares) < N_POD)
    azs = rng.uniform(0, 360, N_POD)
    out = {"pares_disponibles": len(pares), "dias_de_los_pares": len({pares[e][0] for e in elegidos})}
    for a in FIRMAS:
        hits = 0
        for e, az in zip(elegidos, azs):
            d, s = pares[e]
            B = D.base(d)
            U, _ = D.umbral(d)
            sel = M.pixeles_rayo(az)
            ksec = int(az // 30) % M.NSEC
            res = []
            for x in (s - 1, s):
                v = D.mm[d, x] - B[x]
                v[sel] -= a                      # los píxeles borrados por nube siguen vacíos
                res.append(M.estadistico(v))
            (S1, k1, _), (S2, k2, _) = res
            if (np.isfinite(S1) and np.isfinite(S2) and S1 <= U[s - 1] and S2 <= U[s] and M.vecinos(k1, k2)
                    and M.vecinos(k2, ksec)):
                hits += 1
        out[f"{a:.2f}"] = hits / N_POD
        print(f"poder a {a:.2f} K: {hits / N_POD:.3f}", flush=True)
    json.dump(out, open(os.path.join(RES, "poder.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)


# ---------- desarrollo con la regla fija (informativo, §5) ----------
def serie(D, d, U, F, ev, s0=72, s1=143):
    return [{"hora": M.hhmm(s), "S": _r(D.S[d, s]), "U": _r(U[s]), "k": int(D.K[d, s]), "F": bool(F[s]),
             "evaluado": bool(ev[s]), "nube_dinamica": _r(D.FD[d, s]), "E1": bool(D.E1[d, s]),
             "VOLCAT": D.CL[d, s]} for s in range(s0, s1 + 1)]


def desarrollo():
    D = Datos()
    por_dia, te, th, ne, nh = [], 0, 0, 0, 0
    series, eps_t, eps_h = {}, 0, 0
    for d in D.DEV:
        U, _ = D.umbral(d)
        F, ev = D.disparos(d, U)
        Ps = np.flatnonzero(D.CL[d] == "P")
        e = h = 0
        for s in Ps:
            a, b = alcanzado(F, ev, s)
            e += a
            h += b
        for s in np.flatnonzero(D.NUL[d]):
            a, b = alcanzado(F, ev, s)
            ne += a
            nh += b
        if len(Ps):
            eps = M.episodios(list(Ps))
            for ep in eps:
                eps_t += 1
                eps_h += bool(F[max(0, ep[0] - 3):min(144, ep[-1] + 4)].any())
            por_dia.append({"dia": fecha(d), "P": int(len(Ps)), "P_evaluables": e, "P_alcanzados": h,
                            "P_no_evaluables_por_nubes": int(sum(not D.GATE[d, s] for s in Ps)),
                            "disparos_del_dia": int(F.sum()),
                            "tajadas_de_los_disparos": np.bincount(D.K[d][F], minlength=12).tolist()})
        te += e
        th += h
        if fecha(d) in ("2026-11-08", "2026-11-14", "2026-11-15"):
            series[fecha(d)] = serie(D, d, U, F, ev)
    tab = [[th, te - th], [nh, ne - nh]]
    p = float(stats.fisher_exact(tab, alternative="greater")[1]) if te and ne else None
    out = {"nota": "DESARROLLO: días ya mirados; la regla se eligió mirándolos. No decide.",
           "P_evaluables": te, "P_alcanzados": th, "R": (th / te if te else None),
           "N_evaluables": ne, "N_alcanzados": nh, "r_N": (nh / ne if ne else None), "p_fisher": p,
           "episodios": eps_t, "episodios_alcanzados": eps_h, "por_dia": por_dia, "series": series}
    json.dump(out, open(os.path.join(RES, "desarrollo.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps({k: v for k, v in out.items() if k != "series"}, ensure_ascii=False, indent=1))


# ---------- confirmación en días nuevos (§4) ----------
def confirmar():
    seco_ = json.load(open(os.path.join(RES, "seco.json"), encoding="utf-8"))
    pod = json.load(open(os.path.join(RES, "poder.json"), encoding="utf-8"))
    inst = json.load(open(os.path.join(RES, "instrumento_nuevo.json"), encoding="utf-8"))
    D = Datos(con_nuevos=True)
    U, _ = D.umbral(None)                          # sólo desarrollo (DEV); los días nuevos no entran al umbral
    nuevos = list(range(NDEV, ND))
    FF = {d: D.disparos(d, U) for d in nuevos}
    # 1) falsa alarma en los cuadros N nuevos (se escribe antes de mirar P)
    nN = fN = 0
    por_dia = []
    for d in nuevos:
        F, ev = FF[d]
        m = ev & D.NUL[d]
        nN += int(m.sum())
        fN += int((F & m).sum())
        con_clase = D.CL[d] != ""
        por_dia.append({"dia": fecha(d), "cuadros_con_clase": int(con_clase.sum()), "N": int(D.NUL[d].sum()),
                        "otro": int((D.CL[d] == "otro").sum()), "P": int((D.CL[d] == "P").sum()),
                        "con_clase_que_pasan_compuerta": int((con_clase & D.GATE[d]).sum()),
                        "N_evaluados": int(m.sum()), "disparos_en_N": int((F & m).sum()),
                        "disparos_todos": int(F.sum()), "tajadas_disparos": np.bincount(D.K[d][F], minlength=12).tolist(),
                        "horas_disparos": [M.hhmm(s) for s in np.flatnonzero(F)]})
    fa = {"N_evaluados": nN, "disparos": fN, "FA_nuevo": (fN / nN if nN else None), "por_dia": por_dia}
    json.dump(fa, open(os.path.join(RES, "confirmacion_fa.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("FALSA ALARMA EN LO NUEVO:", json.dumps(fa, ensure_ascii=False, indent=1), flush=True)
    # 2) recuerdo en P nuevos
    te = th = ne = nh = 0
    for d in nuevos:
        F, ev = FF[d]
        for s in range(144):
            if D.CL[d, s] == "P":
                a, b = alcanzado(F, ev, s)
                te += a
                th += b
            elif D.NUL[d, s]:
                a, b = alcanzado(F, ev, s)
                ne += a
                nh += b
    R = th / te if te else None
    p = float(stats.fisher_exact([[th, te - th], [nh, ne - nh]], alternative="greater")[1]) if te and ne else None
    if not seco_["aprobado"]:
        ver = "INVÁLIDA"
    elif nN >= MIN_N_NUEVO and fa["FA_nuevo"] > FA_MAX:
        ver = "FALSA ALARMA EN LO NUEVO"
    elif te < MIN_P_NUEVO:
        ver = "NO DECIDIBLE (recuerdo)"
    elif p <= P_MAX:
        ver = "CONFIRMA" if R >= R_MIN else "PARCIAL"
    else:
        ver = "NO LLEGA" if pod["0.33"] >= 0.8 else "SIN PODER"
    series = {fecha(d): serie(D, d, U, *FF[d], s0=0, s1=143) for d in nuevos}
    out = {"veredicto": ver, "seco_aprobado": seco_["aprobado"], "seco_fa": seco_["fa_media_por_dia"],
           "poder": pod, "instrumento": inst, "FA_nuevo": fa["FA_nuevo"], "N_evaluados_nuevo": nN,
           "P_evaluables_nuevo": te, "P_alcanzados_nuevo": th, "R_nuevo": R, "r_N_nuevo": (nh / ne if ne else None),
           "p_fisher": p, "por_dia": por_dia, "series": series}
    json.dump(out, open(os.path.join(RES, "s22b_resultado.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps({k: v for k, v in out.items() if k not in ("series", "por_dia")}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    {"pruebas": pruebas, "cubo_nuevo": cubo_nuevo, "seco": seco, "poder": poder, "desarrollo": desarrollo,
     "confirmar": confirmar}[sys.argv[1]]()
