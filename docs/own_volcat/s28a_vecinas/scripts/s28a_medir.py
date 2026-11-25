r"""S28a: ¿cuánto dispara el detector S26a (zona del cráter O anillo, percentil 4,75) en volcanes tranquilos de la
misma ventana, Antuco y Longaví, en oct-nov 2026 comparado con 2025? Implementa criterio_2026-11-25.md (commit
39da17b, empujado antes de calcular un solo disparo del anillo o de la unión en las vecinas).

Por qué: en Chillán todo 2026 tiene pluma, así que su falsa alarma de 2026 no se puede medir ahí. Las vecinas no
tienen pluma en ningún año: si con la misma regla (cada una con su propio fondo de 2025) disparan en 2026 lo mismo que
en 2025, la falsa alarma de desarrollo de S26a (4,9 %) vale también en 2026.

Qué se generaliza y qué no: la zona es la de S27a tal cual (`s27a_medir.Zona`, `zona_de`). El anillo es la regla de
`s22a_medir` + `s23_medir.Detector` con la geometría de la vecina; la única regla nueva es que se sacan las tajadas
que miran a Chillán (algún píxel a menos de 45 km de su cráter, la frontera que el método ya usa para sus controles) y
el mínimo de tajadas válidas se escala al 75 %. Antes de leer una vecina, el código generalizado tiene que reproducir
el anillo de Chillán (S, tajadas, seco 269 de 5.499, tabla_2026.csv) y la zona de las vecinas (S27a).

Uso: python -I s28a_medir.py pruebas | m1 | medir
  m1     calcula el M1 del anillo completo de cada vecina en 2025 y 2026 (caché en D:\goes_notas\s28\s28a) y
         comprueba el M1 generalizado contra el caché de Chillán en tres días.
  medir  comprobación de código y medida (resultados/s28a_resultado.json; cuadros en D:).
"""
import csv
import json
import math
import os
import sys
import time
import warnings
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime, timedelta

import numpy as np

sys.stdout.reconfigure(encoding="utf-8")
warnings.simplefilter("ignore", RuntimeWarning)
AQUI = os.path.dirname(os.path.abspath(__file__))
OV = os.path.abspath(os.path.join(AQUI, "..", ".."))
RES = os.path.join(os.path.dirname(AQUI), "resultados")
sys.path.insert(0, os.path.join(OV, "s27a_noche_causa", "scripts"))
import s27a_medir as Q  # noqa: E402   (Zona, zona_de y viento de S27a; importa s26a, s23, s25a, s22b, s22a)

U, S, Z = Q.U, Q.S, Q.Z
B, M, H24, C29 = Q.B, Q.M, Q.H24, Q.C29
TRAB = r"D:\goes_notas\s28\s28a"
# ---------- parámetros del criterio ----------
PSTAR = 4.75
R_EXCL = 45.0                                       # §3: tajadas con un píxel a < 45 km de Chillán, fuera
FRAC_SEC = 0.75                                     # §3: 9 de 12 en Chillán
SITIOS = {"antuco": (-37.41, -71.35), "longavi": (-36.19, -71.16)}      # h23_comun.SITIOS
RUMBO_DESDE_CHILLAN = {"antuco": 178.0, "longavi": 15.0}               # §6
SEMI_VIENTO, VMIN = 45.0, 3.0
NOCHE, DIA, TODO = U.NOCHE, U.DIA, range(144)
PERIODOS = {"noche": NOCHE, "dia": DIA, "dia_completo": TODO}
N_BOOT, SEMILLA, MIN_EVAL = 2000, 0, 300
R_SOSTIENE = 1.5
T0_25, NR = S.T0R, S.NR                             # 21-09-2025, 62 días
T0_26, ND26 = datetime(2026, 9, 21), B.ND           # 21-09 a 24-11-2026, 65 días
assert ND26 == 65 and T0_26 + timedelta(days=ND26 - 1) == datetime(2026, 11, 24), "sólo hasta el 24-11 (§2)"
TABLA_S26A = Q.TABLA_S26A
S27A_ZONA = {"antuco": {"noche": ((62, 1476), (14, 1128)), "dia": ((62, 2410), (138, 1467))},
             "longavi": {"noche": ((58, 1518), (63, 979)), "dia": ((72, 2889), (53, 1665))}}
DIAS_M1_PRUEBA = [("2025", 24), ("2026", 37), ("2026", 63)]   # 15-10-2025, 28-10-2026, 23-11-2026


# ---------- geometría del anillo ----------
class Geo:
    """Anillo de 4 a 40 km de una cumbre, tajadas de 30° y controles; sin las tajadas que miran a Chillán si
    excluir=True. Con la cumbre de Chillán y bloque (42, 46) reproduce s22a_medir (AP, SEC, CTRL)."""

    def __init__(self, nombre, la, lo, excluir=True, bloque=None):
        self.nombre = nombre
        dist = C29.hav(C29.LAT, C29.LON, la, lo)
        i, j = bloque if bloque is not None else np.unravel_index(np.argmin(dist), dist.shape)
        bl = np.zeros_like(dist, bool)
        bl[i - 1:i + 2, j - 1:j + 2] = True
        x = (C29.LON - lo) * 111.32 * np.cos(np.radians(la))
        y = (C29.LAT - la) * 110.57
        az = (np.degrees(np.arctan2(x, y)) + 360.0) % 360.0
        ap = np.flatnonzero(((dist >= M.R_IN) & (dist <= M.R_OUT) & ~bl).ravel())
        sec = (az.ravel()[ap] // 30).astype(int) % M.NSEC
        self.AP_FULL, self.SEC_FULL = ap, sec
        cerca = C29.DIST.ravel()[ap] < R_EXCL
        self.EXCL = sorted(set(sec[cerca].tolist())) if excluir else []
        keep = ~np.isin(sec, self.EXCL)
        self.KEEP = keep                                  # columnas del M1 completo que se usan
        self.AP, self.SEC = ap[keep], sec[keep]
        self.NA = len(self.AP)
        self.NPS = np.bincount(self.SEC, minlength=M.NSEC)
        self.NSEC_USO = M.NSEC - len(self.EXCL)
        self.MIN_SEC = int(math.ceil(FRAC_SEC * self.NSEC_USO))
        ctrl = (C29.DIST > M.R_CTRL) & (dist > M.R_CTRL)
        self.CTRL = np.flatnonzero(ctrl.ravel())
        zd = C29.ZDEM.ravel()
        self.CTRL_COTA = [self.CTRL[np.abs(zd[self.CTRL] - zd[p]) <= M.COTA_M] for p in ap]   # del anillo completo


def m1_cuadro(geo, bt, bd):
    """M1 del anillo COMPLETO (todas las tajadas) en un cuadro: igual a s22a_medir.m1_cuadro."""
    out = np.full(len(geo.AP_FULL), np.nan, np.float32)
    okb = np.isfinite(bt) & np.isfinite(bd)
    for i, p in enumerate(geo.AP_FULL):
        if not okb[p]:
            continue
        c = geo.CTRL_COTA[i]
        c = c[okb[c]]
        sel = c[np.abs(bt[c] - bt[p]) <= M.PAR_K]
        if len(sel) >= M.MIN_PAR:
            out[i] = bd[p] - np.median(bd[sel])
    return out


def estadistico(geo, m1):
    """(S, k*, n tajadas válidas), igual a s22a_medir.estadistico con NPS y mínimo de la geometría."""
    Qk = np.full(M.NSEC, np.nan)
    for k in range(M.NSEC):
        if geo.NPS[k] == 0:
            continue
        v = m1[geo.SEC == k]
        v = v[np.isfinite(v)]
        if len(v) >= 0.5 * geo.NPS[k] and len(v) >= M.NCOLA:
            Qk[k] = np.sort(v)[:M.NCOLA].mean()
    nv = int(np.isfinite(Qk).sum())
    if nv < geo.MIN_SEC:
        return np.nan, -1, nv
    k = int(np.nanargmin(Qk))
    return float(Qk[k] - np.nanmedian(Qk)), k, nv


# ---------- el anillo con referencia 2025 y blanco 2026 (s23_medir.Detector generalizado) ----------
class Anillo:
    def __init__(self, geo, sitio, acmR, m1R_full, estatR, acmT, m1T_full, estatT):
        self.geo = geo
        m1R, m1T = m1R_full[..., geo.KEEP], m1T_full[..., geo.KEEP]
        self.NULR = np.isfinite(m1R).any(2)
        self.DIASR = list(range(acmR.shape[0]))
        self.E1R = H24.despejada(sitio, acmR)
        self.FDR, self.mmR = self._nubes(acmR, m1R, estatR)
        self.GATER = self.FDR <= B.G_MAX
        self._B, self._U = {}, {}
        self.SR = np.full(acmR.shape[:2], np.nan)
        self.KR = np.full(acmR.shape[:2], -1, int)
        for d in self.DIASR:
            Bd = self.base(d)
            for s in range(144):
                if self.GATER[d, s]:
                    self.SR[d, s], self.KR[d, s], _ = estadistico(geo, self.mmR[d, s] - Bd[s])
        self.FDT, self.mmT = self._nubes(acmT, m1T, estatT)
        self.GATET = self.FDT <= B.G_MAX
        B0 = self.base(None)
        self.ST = np.full(acmT.shape[:2], np.nan)
        self.KT = np.full(acmT.shape[:2], -1, int)
        for d in range(acmT.shape[0]):
            for s in range(144):
                if self.GATET[d, s]:
                    self.ST[d, s], self.KT[d, s], _ = estadistico(geo, self.mmT[d, s] - B0[s])

    def _nubes(self, acm, m1, estat):
        FD = np.full(acm.shape[:2], np.nan)
        mm = m1.copy()
        for d in range(acm.shape[0]):
            for s in range(144):
                if not (acm[d, s] != 255).any():
                    continue
                nd = B.dinamica(acm[d, s], estat[s])
                FD[d, s] = nd[self.geo.AP].mean()
                mm[d, s][B.borde(nd)[self.geo.AP]] = np.nan
        return FD, mm

    def base(self, excl):
        """s23_medir.Detector.base con el largo del anillo de esta geometría (el original fija M.NA de Chillán)."""
        if excl in self._B:
            return self._B[excl]
        Bs = np.full((144, self.geo.NA), np.nan, np.float32)
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

    umbral = S.Detector.umbral

    def seco(self):
        self._U = {}
        return [S.disparos(self.SR, self.KR, d, self.umbral(d)[0]) for d in self.DIASR]

    def blanco(self):
        self._U = {}
        Ub = self.umbral(None)[0]
        return [S.disparos(self.ST, self.KT, d, Ub) for d in range(self.ST.shape[0])]


# ---------- cubos ----------
def cubos():
    bt25 = np.load(os.path.join(S.TRAB, "r25_bt11.npy"), mmap_mode="r")
    bd25 = np.load(Z._npy("r25_btd"), mmap_mode="r")
    bt26 = np.concatenate([np.load(os.path.join(B.TRAB, "dev_bt11.npy"), mmap_mode="r"),
                           np.load(os.path.join(B.TRAB, "nuevo_bt11.npy"))])
    bd26 = np.concatenate([np.load(os.path.join(B.TRAB, "dev_btd.npy"), mmap_mode="r"), np.load(Z._npy("n26_btd"))])
    return bt25, bd25, bt26, bd26


_GEO = {}


def _m1_dia(args):
    nombre, bt, bd = args
    g = _GEO.get(nombre)
    if g is None:
        g = _GEO[nombre] = geo_de(nombre, excluir=False)
    return np.array([m1_cuadro(g, bt[s], bd[s]) if np.isfinite(bt[s]).any()
                     else np.full(len(g.AP_FULL), np.nan, np.float32) for s in range(144)], np.float32)


def geo_de(nombre, excluir=True):
    if nombre == "chillan":
        return Geo("chillan", *C29.CRATER, excluir=False, bloque=M.CRATER_PX)
    return Geo(nombre, *SITIOS[nombre], excluir=excluir)


def _m1_ruta(sitio, año):
    return os.path.join(TRAB, f"m1_{sitio}_{año}.npy")


def m1(nproc=6):
    """M1 del anillo completo de cada vecina (2025 y 2026) y comprobación del M1 generalizado en Chillán."""
    os.makedirs(TRAB, exist_ok=True)
    bt25, bd25, bt26, bd26 = cubos()
    t = time.time()
    # comprobación 2 (§4): el M1 generalizado con la geometría de Chillán es el del caché
    ch = geo_de("chillan")
    assert np.array_equal(ch.AP_FULL, M.AP) and np.array_equal(ch.SEC_FULL, M.SEC), "geometría de Chillán distinta"
    assert np.array_equal(ch.CTRL, M.CTRL), "controles de Chillán distintos"
    cache = {"2025": np.load(os.path.join(S.TRAB, "r25_m1.npy"), mmap_mode="r"),
             "2026": np.concatenate([np.load(os.path.join(B.TRAB, "dev_m1.npy"), mmap_mode="r"),
                                     np.load(os.path.join(B.TRAB, "nuevo_m1.npy"))])}
    comp = {}
    for año, d in DIAS_M1_PRUEBA:
        bt, bd = (bt25, bd25) if año == "2025" else (bt26, bd26)
        mio = _m1_dia(("chillan", np.asarray(bt[d]), np.asarray(bd[d])))
        ref = np.asarray(cache[año][d])
        comp[f"{año}-{d}"] = bool(np.array_equal(mio, ref, equal_nan=True))
        print(f"M1 generalizado contra caché, {año} día {d}: {comp[f'{año}-{d}']}", flush=True)
    json.dump(comp, open(os.path.join(TRAB, "m1_comprobacion.json"), "w"))
    if not all(comp.values()):
        sys.exit("el M1 generalizado no reproduce el caché de Chillán: error de código")
    for sitio in SITIOS:
        for año, (bt, bd, nd) in (("2025", (bt25, bd25, NR)), ("2026", (bt26, bd26, ND26))):
            fn = _m1_ruta(sitio, año)
            if os.path.exists(fn):
                continue
            with ProcessPoolExecutor(nproc) as ex:
                out = np.array(list(ex.map(_m1_dia, [(sitio, np.asarray(bt[d]), np.asarray(bd[d])) for d in range(nd)])),
                               np.float32)
            np.save(fn, out)
            print(f"M1 {sitio} {año}: {out.shape}, finitos {np.isfinite(out).mean():.3f}, {time.time() - t:.0f} s",
                  flush=True)


# ---------- conteos y remuestreo ----------
def por_dia(lista, rango, quitar=None):
    """(F, E) por día en el rango de horas; quitar[d, s] True saca el cuadro del conteo (no de la persistencia)."""
    r = np.zeros(144, bool)
    r[list(rango)] = True
    out = []
    for d, (F, ev) in enumerate(lista):
        m = ev & r
        if quitar is not None:
            m = m & ~quitar[d]
        out.append((int((F & m).sum()), int(m.sum())))
    return np.array(out, float).reshape(-1, 2)


def razon(c25, c26, semilla=SEMILLA):
    """Tasas, R = t26/t25 y su intervalo de 95 % por remuestreo de días (§5)."""
    F25, E25 = c25.sum(0)
    F26, E26 = c26.sum(0)
    t25 = F25 / E25 if E25 else np.nan
    t26 = F26 / E26 if E26 else np.nan
    R = t26 / t25 if t25 else np.nan
    rng = np.random.default_rng(semilla)
    Rs = []
    for _ in range(N_BOOT):
        a = c25[rng.integers(0, len(c25), len(c25))].sum(0)
        b = c26[rng.integers(0, len(c26), len(c26))].sum(0)
        if a[1] and b[1] and a[0]:
            Rs.append((b[0] / b[1]) / (a[0] / a[1]))
    lo, hi = (np.percentile(Rs, [2.5, 97.5]) if Rs else (np.nan, np.nan))
    return {"2025": [int(F25), int(E25)], "2026": [int(F26), int(E26)], "tasa_2025": _r(t25), "tasa_2026": _r(t26),
            "R": _r(R), "IC95": [_r(lo), _r(hi)], "replicas_validas": len(Rs)}


def _r(x):
    return None if (x is None or not np.isfinite(x)) else round(float(x), 5)


def union(a, z):
    return [(Fa | Fz, ea | ez) for (Fa, ea), (Fz, ez) in zip(a, z)]


def veredicto(vec, r_ch):
    """vec: {sitio: razon de la unión}; r_ch: R de Chillán (todos los cuadros) del mismo periodo. §5."""
    if any(min(v["2025"][1], v["2026"][1]) < MIN_EVAL for v in vec.values()):
        return "NO DECIDIBLE"
    sube = {s: v["R"] is not None and v["R"] >= R_SOSTIENE and v["IC95"][0] is not None and v["IC95"][0] > 1.0
            for s, v in vec.items()}
    baja = {s: v["R"] is not None and v["R"] <= R_SOSTIENE for s, v in vec.items()}
    if all(baja.values()) and all(v["IC95"][1] is not None and v["IC95"][1] < r_ch for v in vec.values()):
        return "SE SOSTIENE"
    if all(sube.values()):
        return "NO SE SOSTIENE"
    if any(sube.values()) and all(sube[s] or baja[s] for s in vec):
        return "MIXTO (sube " + ", ".join(s for s in vec if sube[s]) + ")"
    return "NO CONCLUYENTE"


# ---------- viento (§6) ----------
def quitar_por_viento(sitio, t0, nd, año):
    """True en los cuadros con viento de 3 a 6 km desde Chillán hacia la vecina (±45°, >= 3 m/s). Noche en los dos
    años; día sólo en 2026. Devuelve también cuántos cuadros quedaron sin viento."""
    q = np.zeros((nd, 144), bool)
    sin = 0
    rumbo = RUMBO_DESDE_CHILLAN[sitio]
    for d in range(nd):
        for s in list(NOCHE) + (list(DIA) if año == "2026" else []):
            dt = t0 + timedelta(days=d, minutes=10 * s)
            if s in NOCHE:
                w = Q.viento(dt, (3, 6, 9))
            elif dt.hour < 21:
                w = Q.viento(dt, (12, 15, 18, 21))
            else:
                h = Q.hora(dt.replace(hour=21, minute=0))
                w = None if h is None else ((math.degrees(math.atan2(h[0], h[1])) + 360.0) % 360.0,
                                            math.hypot(h[0], h[1]), h[2])
            if w is None:
                sin += 1
                continue
            tw, V = w[0], w[1]
            q[d, s] = V >= VMIN and abs((tw - rumbo + 180.0) % 360.0 - 180.0) <= SEMI_VIENTO
    return q, sin


# ---------- medir ----------
def medir():
    os.makedirs(RES, exist_ok=True)
    t = time.time()
    X = U.Partes()
    est25_anillo, est26 = X.A.ESTAT, X.est26
    # ---- comprobación 1 (§4): el anillo generalizado reproduce el de Chillán ----
    ch = geo_de("chillan")
    m1R = np.load(os.path.join(S.TRAB, "r25_m1.npy"))
    m1T = np.concatenate([np.load(os.path.join(B.TRAB, "dev_m1.npy")), np.load(os.path.join(B.TRAB, "nuevo_m1.npy"))])
    acm25 = np.load(Z._npy("r25_acm"))
    acm26 = X.A.acmT
    assert np.array_equal(acm25, X.A.acmR), "ACM de 2025 distinto entre S23a y S25a"
    Ach = Anillo(ch, "chillan", acm25, m1R, est25_anillo, acm26, m1T, est26)
    rep_S = {k: bool(np.array_equal(a, b, equal_nan=True)) for k, (a, b) in
             {"SR": (Ach.SR, X.A.SR), "KR": (Ach.KR, X.A.KR), "ST": (Ach.ST, X.A.ST), "KT": (Ach.KT, X.A.KT)}.items()}
    B.PCT_U = PSTAR
    X.A._U = {}
    sec = X.seco(PSTAR)
    res, _, _ = X.blanco(PSTAR)
    a_sec, a_bla = Ach.seco(), Ach.blanco()
    u_sec = union(a_sec, sec["z"])
    seco_u = U.medidas_seco(u_sec)
    dif = 0
    with open(TABLA_S26A, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            d = (datetime.strptime(r["dia"], "%Y-%m-%d") - T0_26).days
            s = M.slot(r["hora"])
            dif += (int(a_bla[d][0][s]) != int(r["F_a"])) + (int(res[d]["z"][0][s]) != int(r["F_z"]))
    m1c = json.load(open(os.path.join(TRAB, "m1_comprobacion.json")))
    comp = {"anillo_S_y_tajadas": rep_S, "seco_union_chillan": [seco_u["disparos"], seco_u["evaluados"]],
            "diferencias_tabla_2026": dif, "m1_generalizado_3_dias": m1c}
    ok = all(rep_S.values()) and seco_u["disparos"] == 269 and seco_u["evaluados"] == 5499 and dif == 0 \
        and all(m1c.values())
    print("comprobación 1 y 2:", json.dumps(comp), "OK" if ok else "NO REPRODUCE", flush=True)
    if not ok:
        json.dump(comp, open(os.path.join(RES, "s28a_reproduccion_FALLA.json"), "w", encoding="utf-8"), indent=1)
        sys.exit("no reproduce Chillán: error de código, no se lee ninguna vecina")
    del Ach, m1R, m1T
    # Chillán como referencia (§5): unión con todos los cuadros de 2026 y sin los P
    CL = X.CL
    ch_bla = [r["u"] for r in res]
    quitaP = CL == "P"
    ref_ch = {}
    for per, rg in PERIODOS.items():
        c25 = por_dia(u_sec, rg)
        ref_ch[per] = {"todos": razon(c25, por_dia(ch_bla, rg)), "sin_P": razon(c25, por_dia(ch_bla, rg, quitaP))}
    print("Chillán:", json.dumps({p: v["todos"] for p, v in ref_ch.items()}), flush=True)

    # ---- las vecinas ----
    btd25 = np.load(Z._npy("r25_btd"))
    est25_zona = Z.costumbre(acm25, np.isfinite(btd25[:, :, Z.ZONA[0]]))
    btd26 = np.concatenate([np.load(os.path.join(B.TRAB, "dev_btd.npy")), np.load(Z._npy("n26_btd"))])
    vec, geo_info, cuadros = {}, {}, {}
    for sitio, (la, lo) in SITIOS.items():
        zona, anillo, ctrl, _ = Q.zona_de(la, lo)
        zv = Q.Zona(sitio, zona, anillo, ctrl).correr(btd25, acm25, est25_zona, btd26, acm26, est26, sitio)
        z_sec, z_bla = zv.disparos(PSTAR)
        # comprobación 3 (§4): la zona reproduce S27a
        rz = {per: (tuple(int(x) for x in por_dia(z_sec, rg).sum(0)), tuple(int(x) for x in por_dia(z_bla, rg).sum(0)))
              for per, rg in (("noche", NOCHE), ("dia", DIA))}
        if rz != S27A_ZONA[sitio]:
            json.dump({"obtenido": rz, "esperado": S27A_ZONA[sitio]},
                      open(os.path.join(RES, f"s28a_reproduccion_zona_{sitio}_FALLA.json"), "w"), indent=1)
            sys.exit(f"la zona de {sitio} no reproduce S27a: error de código")
        print(f"zona de {sitio} reproduce S27a: {rz}", flush=True)
        m1R = np.load(_m1_ruta(sitio, "2025"))
        m1T = np.load(_m1_ruta(sitio, "2026"))
        out, partes = {}, {}
        for nom, excluir in (("principal", True), ("sin_excluir", False)):
            g = geo_de(sitio, excluir)
            A = Anillo(g, sitio, acm25, m1R, est25_anillo, acm26, m1T, est26)
            B.PCT_U = PSTAR
            a_sec, a_bla = A.seco(), A.blanco()
            partes[nom] = (a_sec, a_bla, A)
            geo_info.setdefault(sitio, {})[nom] = {
                "tajadas_excluidas": g.EXCL, "tajadas_usadas": g.NSEC_USO, "min_tajadas_validas": g.MIN_SEC,
                "pixeles_anillo": g.NA, "pixeles_por_tajada": g.NPS.tolist(), "controles": len(g.CTRL),
                "pixeles_zona": len(zona),
                "anillo_evaluable_2025": _r(np.isfinite(A.SR).mean()), "anillo_evaluable_2026": _r(np.isfinite(A.ST).mean())}
            u_s, u_b = union(a_sec, z_sec), union(a_bla, z_bla)
            out[nom] = {per: {"union": razon(por_dia(u_s, rg), por_dia(u_b, rg)),
                              "anillo": razon(por_dia(a_sec, rg), por_dia(a_bla, rg)),
                              "zona": razon(por_dia(z_sec, rg), por_dia(z_bla, rg))} for per, rg in PERIODOS.items()}
            print(sitio, nom, json.dumps({p: out[nom][p]["union"] for p in PERIODOS}), f"{time.time() - t:.0f} s",
                  flush=True)
        # sensibilidad de viento (§6), con la regla principal
        a_sec, a_bla, A = partes["principal"]
        u_s, u_b = union(a_sec, z_sec), union(a_bla, z_bla)
        q25, sin25 = quitar_por_viento(sitio, T0_25, NR, "2025")
        q26, sin26 = quitar_por_viento(sitio, T0_26, ND26, "2026")
        out["viento"] = {per: razon(por_dia(u_s, rg, q25), por_dia(u_b, rg, q26)) for per, rg in
                         (("noche", NOCHE), ("dia", DIA))}
        out["viento"]["cuadros_quitados"] = {"2025": int(q25.sum()), "2026": int(q26.sum())}
        out["viento"]["cuadros_sin_viento"] = {"2025": sin25, "2026": sin26}
        vec[sitio] = out
        cuadros[sitio] = (u_s, u_b, a_sec, a_bla, z_sec, z_bla, A)
        del m1R, m1T

    # ---- veredicto (§5) ----
    ver = {}
    for per in ("noche", "dia"):
        ver[per] = veredicto({s: vec[s]["principal"][per]["union"] for s in SITIOS}, ref_ch[per]["todos"]["R"])
    # lectura (§5): Chillán 2025 × R de la vecina que más sube
    lectura = {}
    for per in ("noche", "dia"):
        rmax = max(vec[s]["principal"][per]["union"]["R"] for s in SITIOS)
        t25 = ref_ch[per]["todos"]["tasa_2025"]
        lectura[per] = {"R_vecina_max": rmax, "chillan_2025": t25, "chillan_2025_por_R_vecina": _r(t25 * rmax),
                        "chillan_2026_todos": ref_ch[per]["todos"]["tasa_2026"],
                        "chillan_2026_sin_P": ref_ch[per]["sin_P"]["tasa_2026"]}
    resultado = {"criterio": "criterio_2026-11-25.md (39da17b)", "percentil": PSTAR,
                 "dias": {"2025": "21-09 a 21-11-2025 (62, cada día sin sí mismo)",
                          "2026": "21-09 a 24-11-2026 (65, base y umbral de los 62 de 2025)"},
                 "comprobacion": comp, "geometria": geo_info, "chillan": ref_ch, "vecinas": vec,
                 "veredicto": ver, "lectura": lectura}
    json.dump(resultado, open(os.path.join(RES, "s28a_resultado.json"), "w", encoding="utf-8"), ensure_ascii=False,
              indent=1, default=lambda o: o.item() if hasattr(o, "item") else str(o))
    # cuadros por vecina (en D:, para el informe y videos)
    for sitio, (u_s, u_b, a_sec, a_bla, z_sec, z_bla, A) in cuadros.items():
        for año, t0, uu, aa, zz, SS in (("2025", T0_25, u_s, a_sec, z_sec, A.SR), ("2026", T0_26, u_b, a_bla, z_bla,
                                                                                    A.ST)):
            with open(os.path.join(TRAB, f"cuadros_{sitio}_{año}.csv"), "w", encoding="utf-8", newline="") as f:
                w = csv.writer(f)
                w.writerow(["dia", "hora", "ev_u", "F_u", "ev_a", "F_a", "S_a", "ev_z", "F_z"])
                for d in range(len(uu)):
                    for s in range(144):
                        if uu[d][1][s]:
                            w.writerow([f"{t0 + timedelta(days=d):%Y-%m-%d}", M.hhmm(s), 1, int(uu[d][0][s]),
                                        int(aa[d][1][s]), int(aa[d][0][s]), _r(SS[d, s]), int(zz[d][1][s]),
                                        int(zz[d][0][s])])
    print("VEREDICTO:", json.dumps(ver, ensure_ascii=False), flush=True)
    print(f"listo en {time.time() - t:.0f} s", flush=True)


# ---------- pruebas ----------
def pruebas():
    ch = geo_de("chillan")
    assert np.array_equal(ch.AP, M.AP) and np.array_equal(ch.SEC, M.SEC) and ch.MIN_SEC == M.MIN_SEC == 9
    assert np.array_equal(ch.NPS, M.NPS) and np.array_equal(ch.CTRL, M.CTRL)
    rng = np.random.default_rng(1)
    for _ in range(50):
        v = rng.normal(0, 1, ch.NA).astype(np.float32)
        v[rng.random(ch.NA) < 0.2] = np.nan
        a, b = estadistico(ch, v), M.estadistico(v)
        assert (np.isnan(a[0]) and np.isnan(b[0]) or a[0] == b[0]) and a[1:] == b[1:]
    an, lo = geo_de("antuco"), geo_de("longavi")
    assert an.EXCL == [0, 1, 10, 11] and an.MIN_SEC == 6, (an.EXCL, an.MIN_SEC)
    assert lo.EXCL == [5, 6, 7] and lo.MIN_SEC == 7, (lo.EXCL, lo.MIN_SEC)
    assert (C29.DIST.ravel()[an.AP] >= R_EXCL).all() and (C29.DIST.ravel()[lo.AP] >= R_EXCL).all()
    # razon: tasas y R exactos sin remuestreo
    c25 = np.array([[1, 10], [1, 10]], float)
    c26 = np.array([[2, 10], [2, 10]], float)
    r = razon(c25, c26)
    assert r["R"] == 2.0 and r["tasa_2025"] == 0.1
    # veredicto
    v = {"a": {"2025": [1, 400], "2026": [1, 400], "R": 1.0, "IC95": [0.5, 1.4]},
         "b": {"2025": [1, 400], "2026": [1, 400], "R": 1.2, "IC95": [0.8, 1.6]}}
    assert veredicto(v, 2.0) == "SE SOSTIENE" and veredicto(v, 1.5) == "NO CONCLUYENTE"
    v["b"].update(R=2.0, IC95=[1.2, 3.0])
    assert veredicto(v, 2.0).startswith("MIXTO")
    v["a"].update(R=1.6, IC95=[1.1, 2.0])
    assert veredicto(v, 2.0) == "NO SE SOSTIENE"
    v["a"]["2026"] = [1, 200]
    assert veredicto(v, 2.0) == "NO DECIDIBLE"
    # por_dia con quitar
    F = np.zeros(144, bool)
    ev = np.zeros(144, bool)
    ev[20:30] = True
    F[25] = True
    q = np.zeros((1, 144), bool)
    q[0, 25] = True
    assert por_dia([(F, ev)], NOCHE).tolist() == [[1, 10]] and por_dia([(F, ev)], NOCHE, q).tolist() == [[0, 9]]
    print("pruebas OK")


if __name__ == "__main__":
    {"pruebas": pruebas, "m1": m1, "medir": medir}[sys.argv[1]]()
