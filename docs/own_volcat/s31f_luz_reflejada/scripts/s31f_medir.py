r"""S31f: ¿la reflectancia de C02 (0,64 µm) y C05 (1,6 µm), medida en cada píxel contra sí mismo a la misma fecha y hora
de 2025, se aparta dentro de la huella anclada de VOLCAT y en la zona de 0 a 15 km del cráter de Nevados de Chillán?
Implementa criterio_2026-11-27.md (commit 741acb4, anexo c6df303, los dos empujados antes de calcular una reflectancia).

Por qué así: sobre nieve una pluma con ceniza oscurece el rojo y aclara 1,6 µm (el hielo absorbe a 1,6 µm y la ceniza
no); sobre roca oscurece las dos. Cada píxel se compara con su propia mediana de 2025 (±7 días, ±20 min) para sacar el
relieve y el sol, y el signo que esperaría la ceniza sale del modelo de S21b sobre la base de ese píxel. La nieve y el
depósito de 2026 no son de 2025: por eso el nulo que pesa compara el mismo lugar y la misma hora en otros días de 2026
(nulo N), y todos los nulos mueven días enteros (S28b).

Lee las ventanas de D:\goes_notas\s31\s31f\l1b\ (s31f_bajar.py), las huellas de S30b (D:\goes_notas\s30\s30b\
huellas.npz, material de SSEC: nada de eso va al repo) y la tabla de clases de S26a. Escribe al repo sólo cifras:
resultados/s31f_resultado.json y resultados/s31f_por_cuadro.csv. Lo intermedio, en D:\goes_notas\s31\s31f\.

Uso: python -I -B s31f_medir.py
"""
import csv
import json
import os
import sys
import time
import warnings
from collections import defaultdict
from datetime import datetime, timedelta

import numpy as np
from scipy import ndimage

sys.stdout.reconfigure(encoding="utf-8")
warnings.simplefilter("ignore", RuntimeWarning)
AQUI = os.path.dirname(os.path.abspath(__file__))
OV = os.path.abspath(os.path.join(AQUI, "..", ".."))
RES = os.path.join(os.path.dirname(AQUI), "resultados")
sys.path.insert(0, AQUI)
sys.path.insert(0, os.path.join(OV, "s21b_reflejadas", "scripts"))
sys.path.insert(0, os.path.join(OV, "s30b_huella_volcat", "scripts"))
import s31f_bajar as BJ  # noqa: E402
import s21b_comun as K21  # noqa: E402  (sol, hora_fila, Banda, hora_chillan, RHO_P, T_PLUMA: sin cambios)
import s30b_medir as S30  # noqa: E402  (rotar, huellas y grilla del detector)

C29 = S30.C29
L1B = BJ.OUT
TRAB = r"D:\goes_notas\s31\s31f"
TABLA = r"D:\goes_notas\s26\s26a\tabla_2026.csv"
CALOR = os.path.join(OV, "calor_rayos", "resultados", "frames_calor.csv")
HUELLAS = r"D:\goes_notas\s30\s30b\huellas.npz"
ULTIMO_DIA = "2026-11-24"

# ---------- parámetros del criterio ----------
SZA_MAX = 70.0                      # §1
DIAS_BASE, SLOT_BASE, MIN_BASE = 7, 2, 8          # §1, §4.2
SIG_PISO, ZCLIP = 0.01, 5.0         # §4.2, §4.3
RHO05_NUBE, DRHO05_NUBE, DBT_NUBE = 0.25, 0.10, 6.0   # §4.1
E_MIN = 0.01                        # §4.4
FR_ZONA, FR_HUELLA, R_ZONA = 0.70, 0.50, 15.0     # §4
TOP_Z = 0.10                        # §4 zona
B_MC, SEMILLA, P_MAX = 99999, 0, 0.01             # §5
N_POD, SEM_POD, B_POD, F_POD, F_INF, POD_MIN = 200, 1, 9999, 0.25, 0.10, 0.8   # §6
MIN_P, MIN_DIAS = 10, 3             # §7
RHO_P = {"C02": K21.RHO_P["C02"], "C05": K21.RHO_P["C05"]}
T_P = K21.T_PLUMA
NIEVE_B05, NIEVE_B02 = 0.15, 0.40   # §8

# ventana S31f dentro de la del detector (83 x 94, origen 4497, 2820)
R0, C0 = BJ.WIN2["y0"] - 4497, BJ.WIN2["x0"] - 2820
NW = BJ.WIN2["y1"] - BJ.WIN2["y0"]
assert NW == BJ.WIN2["x1"] - BJ.WIN2["x0"] == 29
FAC = {"C02": 4, "C05": 2}
DISTW = C29.DIST[R0:R0 + NW, C0:C0 + NW]
ZONA2 = (DISTW <= R_ZONA).ravel()


def hijos(m2, b):
    """Máscara de 2 km (29*29) -> máscara de la banda (sub-píxeles anidados)."""
    f = FAC[b]
    return np.repeat(np.repeat(m2.reshape(NW, NW), f, 0), f, 1).ravel()


def a_padre(v, b, fn):
    """Valores de la banda -> 2 km, reduciendo los f x f hijos con fn (axis)."""
    f = FAC[b]
    return fn(v.reshape(-1, NW, f, NW, f), axis=(2, 4)).reshape(v.shape[:-1] + (NW * NW,))


ZONA_B = {b: hijos(ZONA2, b) for b in FAC}


def slot_dt(dia, s):
    return datetime.strptime(dia, "%Y-%m-%d") + timedelta(minutes=10 * s)


# ---------- lectura de ventanas ----------
_GEO = {}


def geo(z):
    if not _GEO:
        for b in ("C02", "C05"):
            _GEO[b] = K21.Banda(b, z[f"{b}_x"], z[f"{b}_y"])
    else:
        for b in ("C02", "C05"):
            assert np.allclose(_GEO[b].x, z[f"{b}_x"]) and np.allclose(_GEO[b].y, z[f"{b}_y"]), "grilla distinta"
    return _GEO


def leer(dt):
    """(rho02, rho05, bt11) aplanados o None."""
    p = os.path.join(L1B, f"{dt:%Y%m%d_%H%M}.npz")
    if not os.path.exists(p):
        return None
    with np.load(p) as z:
        g = geo(z)
        out = []
        for b in ("C02", "C05"):
            rad = z[f"{b}_rad"].astype("float64")
            tf = K21.hora_fila(z[f"{b}_tb"], g[b])
            t0 = tf[0].replace(hour=0, minute=0, second=0, microsecond=0)
            horas = np.array([(t - t0).total_seconds() / 3600 for t in tf])[:, None]
            cz = np.cos(np.radians(K21.sol(tf[0], g[b].lat, g[b].lon, horas)[0]))
            rho = z[f"{b}_kappa0"] * rad / cz
            rho[cz < 0.05] = np.nan
            out.append(rho.ravel().astype("float32"))
        bt = C29.bt_de_rad(z["C14_rad"].astype("float64"), z["C14_co"])
        out.append(bt.ravel().astype("float32"))
    return out


def cubo(anio, d0, d1, slots):
    dias = []
    d = datetime.strptime(d0, "%Y-%m-%d")
    while d <= datetime.strptime(d1, "%Y-%m-%d"):
        dias.append(f"{d:%Y-%m-%d}")
        d += timedelta(days=1)
    nd, ns = len(dias), len(slots)
    R = {"C02": np.full((nd, ns, (NW * 4) ** 2), np.nan, "float32"),
         "C05": np.full((nd, ns, (NW * 2) ** 2), np.nan, "float32"),
         "BT": np.full((nd, ns, NW * NW), np.nan, "float32")}
    falta = 0
    for i, dia in enumerate(dias):
        for j, s in enumerate(slots):
            r = leer(slot_dt(dia, s))
            if r is None:
                falta += 1
                continue
            R["C02"][i, j], R["C05"][i, j], R["BT"][i, j] = r
    print(f"cubo {anio}: {nd} días x {ns} casillas, faltan {falta}", flush=True)
    return dias, R, falta


# ---------- base, nubes y apartamiento ----------
class Base25:
    def __init__(self, dias, R):
        self.dias = {d: i for i, d in enumerate(dias)}
        self.R = R
        self.slot = {s: j for j, s in enumerate(BJ.SLOTS_B)}

    def ventana(self, dia, s, excluir=False):
        d = datetime.strptime("2025" + dia[4:], "%Y-%m-%d")
        ii = [self.dias[f"{d + timedelta(days=k):%Y-%m-%d}"] for k in range(-DIAS_BASE, DIAS_BASE + 1)
              if not (excluir and k == 0)]
        jj = [self.slot[s + k] for k in range(-SLOT_BASE, SLOT_BASE + 1)]
        return {b: self.R[b][ii][:, jj].reshape(len(ii) * len(jj), -1) for b in ("C02", "C05", "BT")}

    @staticmethod
    def nube(r05, bt, b05raw, p75):
        agua = a_padre(((r05 > RHO05_NUBE) & (r05 - b05raw > DRHO05_NUBE)).astype("int8"), "C05", np.max) > 0
        return agua | (bt < p75 - DBT_NUBE)

    def objetivo(self, dia, s, rho02, rho05, bt, excluir=False):
        """dict con B, sig, u por banda, despejado por píxel de 2 km (o None si no hay datos)."""
        if not np.isfinite(rho05).any():
            return None
        W = self.ventana(dia, s, excluir)
        b05raw = np.nanmedian(W["C05"], 0)
        p75 = np.nanpercentile(W["BT"], 75, axis=0)
        nubW = self.nube(W["C05"], W["BT"], b05raw, p75)                 # (n, 841)
        out = {"nube": self.nube(rho05[None], bt[None], b05raw, p75)[0]}
        ok2 = ~out["nube"] & np.isfinite(bt)
        for b, rho in (("C02", rho02), ("C05", rho05)):
            v = np.where(hijos_mat(nubW, b), np.nan, W[b])
            n = np.isfinite(v).sum(0)
            B = np.nanmedian(v, 0)
            sig = np.maximum(1.4826 * np.nanmedian(np.abs(v - B), 0), SIG_PISO)
            B[n < MIN_BASE] = np.nan
            out[f"B{b}"], out[f"S{b}"], out[f"R{b}"] = B.astype("float32"), sig.astype("float32"), rho
            ok2 &= a_padre(np.isfinite(B).astype("float32"), b, np.mean) >= 0.5
        out["ok2"] = ok2
        for b in ("C02", "C05"):
            out[f"U{b}"] = apartamiento(b, out[f"R{b}"], out[f"B{b}"], out[f"S{b}"], ok2)
        return out


def hijos_mat(m, b):
    f = FAC[b]
    n = m.shape[0]
    return np.repeat(np.repeat(m.reshape(n, NW, NW), f, 1), f, 2).reshape(n, -1)


def direccion(b, B):
    x = RHO_P[b] - (1 - T_P) * B
    e = np.sign(x)
    e[np.abs(x) < E_MIN] = 0
    return e


def apartamiento(b, rho, B, sig, ok2):
    z = np.clip((rho - B) / sig, -ZCLIP, ZCLIP)
    u = direccion(b, B) * z
    u[~hijos(ok2, b) | ~np.isfinite(rho) | ~np.isfinite(B)] = np.nan
    return u.astype("float32")


def zona_eval(o, sza):
    return o is not None and sza < SZA_MAX and o["ok2"][ZONA2].mean() >= FR_ZONA


def valor_Z(o):
    vs = []
    for b in ("C02", "C05"):
        u = o[f"U{b}"][ZONA_B[b]]
        u = np.sort(u[np.isfinite(u)])[::-1]
        if not len(u):
            return np.nan
        vs.append(u[:int(np.ceil(TOP_Z * len(u)))].mean())
    return float(np.mean(vs))


def valor_U(o, m2):
    """U de una huella dilatada m2 (bool 841) en el objetivo o; nan si no se evalúa."""
    ok = m2 & o["ok2"]
    if m2.sum() == 0 or ok.sum() / m2.sum() < FR_HUELLA:
        return np.nan
    vs = []
    for b in ("C02", "C05"):
        u = o[f"U{b}"][hijos(ok, b)]
        vs.append(np.nanmean(u))
    return float(np.mean(vs)) if np.all(np.isfinite(vs)) else np.nan


def sza_crater(dt):
    t = K21.hora_chillan(dt)
    return float(K21.sol(t, C29.CRATER[0], C29.CRATER[1])[0])


# ---------- huellas ----------
def a_ventana(h83):
    m = np.zeros((C29.NY, C29.NX), bool)
    m.flat[h83] = True
    return m[R0:R0 + NW, C0:C0 + NW].ravel(), int(m.sum() - m[R0:R0 + NW, C0:C0 + NW].sum())


def mascaras(h83):
    """[12] huellas dilatadas (giros 0..11) y la sin dilatar, en la ventana S31f."""
    dil, perd = [], 0
    for j in range(12):
        hj = S30.rotar(h83, j)
        mj, p = a_ventana(np.flatnonzero(S30.dilatar(hj)))
        dil.append(mj)
        perd += p
    und, p0 = a_ventana(h83)
    return dil, und, perd + p0


# ---------- nulos ----------
def mc_mean(V, rng, B):
    """V: lista por día de arrays de valores posibles (nan = no evaluado). Devuelve B promedios de un valor al azar
    por día (los nan no entran)."""
    out = np.empty(B)
    picks = [rng.integers(0, len(v), B) for v in V]
    M = np.vstack([v[p] for v, p in zip(V, picks)])
    out[:] = np.nanmean(M, 0)
    return out


def pval(T, null):
    null = null[np.isfinite(null)]
    return float((1 + np.sum(null >= T - 1e-12)) / (len(null) + 1)), int(len(null))


# ---------- principal ----------
def medir():
    t00 = time.time()
    os.makedirs(RES, exist_ok=True)
    # clases y P de día
    clase = defaultdict(dict)
    with open(TABLA, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            assert r["dia"] <= ULTIMO_DIA
            h, mi = map(int, r["hora"].split(":"))
            clase[r["dia"]][h * 6 + mi // 10] = r["clase"]
    sza_c = {}
    with open(CALOR, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            sza_c[r["dt"][:16]] = float(r["sza"])
    zh = np.load(HUELLAS)
    P = []
    for k in sorted(zh.files):
        dia, s = k.rsplit("_", 1)
        s = int(s)
        t = f"{dia} {s // 6:02d}:{s % 6 * 10:02d}"
        if sza_c.get(t, 999) < SZA_MAX:
            P.append((dia, s, zh[k]))
    diasP = sorted({p[0] for p in P})
    print("P de día:", len(P), "en", len(diasP), "días", flush=True)
    assert len(P) == 63 and len(diasP) == 7, "no son los 63 P en 7 días del criterio"
    slotsP = sorted({p[1] for p in P})
    assert slotsP == BJ.SLOTS_P
    diasN = [d for d in sorted(clase) if "2026-10-21" <= d <= ULTIMO_DIA and "P" not in clase[d].values()
             and sum(clase[d].get(s, "") in ("N", "otro") for s in slotsP) >= 0.8 * len(slotsP)]
    print("días N:", len(diasN), flush=True)
    assert len(diasN) == 20

    # cubos
    d25, R25, f25 = cubo(2025, *BJ.PERIODOS[1][1:3], BJ.SLOTS_B)
    d26, R26, f26 = cubo(2026, *BJ.PERIODOS[2][1:3], BJ.SLOTS_P)
    d24, R24, f24 = cubo(2024, *BJ.PERIODOS[0][1:3], BJ.SLOTS_P)
    base = Base25(d25, R25)
    jP = {s: j for j, s in enumerate(BJ.SLOTS_P)}
    j25 = {s: j for j, s in enumerate(BJ.SLOTS_B)}

    cache = {}

    def obj(anio, dia, s):
        key = (anio, dia, s)
        if key not in cache:
            if anio == 2026:
                i, R, j = d26.index(dia), R26, jP[s]
            elif anio == 2024:
                i, R, j = d24.index(dia), R24, jP[s]
            else:
                i, R, j = d25.index(dia), R25, j25[s]
            o = base.objetivo(dia, s, R["C02"][i, j], R["C05"][i, j], R["BT"][i, j], excluir=(anio == 2025))
            cache[key] = o
        return cache[key]

    def sza_de(anio, dia, s):
        if anio == 2026 and dia in diasP:
            return sza_c[f"{dia} {s // 6:02d}:{s % 6 * 10:02d}"]
        return sza_crater(slot_dt(dia, s))

    # huellas en la ventana
    Pinfo, perdidos = [], 0
    for dia, s, h in P:
        dil, und, perd = mascaras(h)
        perdidos += perd
        Pinfo.append(dict(dia=dia, s=s, dil=dil, und=und, npx=int(len(h))))
    print("píxeles de huella (con giros y dilatación) fuera de la ventana:", perdidos, flush=True)

    # valores reales y matrices de nulos
    idx_dia = {d: [i for i, p in enumerate(Pinfo) if p["dia"] == d] for d in diasP}

    def U_en(anio, dia_obj, i, j=0):
        p = Pinfo[i]
        o = obj(anio, dia_obj, p["s"])
        if not zona_eval(o, sza_de(anio, dia_obj, p["s"])):
            return np.nan
        return valor_U(o, p["dil"][j])

    def Z_en(anio, dia_obj, s):
        o = obj(anio, dia_obj, s)
        return valor_Z(o) if zona_eval(o, sza_de(anio, dia_obj, s)) else np.nan

    filas, Ureal, Zreal = [], {}, {}
    for i, p in enumerate(Pinfo):
        o = obj(2026, p["dia"], p["s"])
        u = U_en(2026, p["dia"], i)
        zv = Z_en(2026, p["dia"], p["s"])
        Ureal[i], Zreal[i] = u, zv
        fila = dict(dia=p["dia"], hora=f"{p['s'] // 6:02d}:{p['s'] % 6 * 10:02d}",
                    sza=round(sza_de(2026, p["dia"], p["s"]), 2), huella_px=p["npx"],
                    zona_desp=None if o is None else round(float(o["ok2"][ZONA2].mean()), 3),
                    huella_desp=None if o is None else round(float((p["dil"][0] & o["ok2"]).sum() / p["dil"][0].sum()), 3),
                    U=None if not np.isfinite(u) else round(u, 4), Z=None if not np.isfinite(zv) else round(zv, 4))
        if o is not None and np.isfinite(u):
            ok = p["dil"][0] & o["ok2"]
            for b in ("C02", "C05"):
                fila[f"U_{b}"] = round(float(np.nanmean(o[f"U{b}"][hijos(ok, b)])), 4)
        filas.append(fila)

    def media_dia(vals):
        v = np.array(vals, float)
        return float(np.nanmean(v)) if np.isfinite(v).any() else np.nan

    TU = {d: media_dia([Ureal[i] for i in idx_dia[d]]) for d in diasP}
    TZ = {d: media_dia([Zreal[i] for i in idx_dia[d]]) for d in diasP}
    diasU = [d for d in diasP if np.isfinite(TU[d])]
    diasZ = [d for d in diasP if np.isfinite(TZ[d])]
    nU = int(sum(np.isfinite(Ureal[i]) for i in Ureal))
    nZ = int(sum(np.isfinite(Zreal[i]) for i in Zreal))
    T_U = float(np.mean([TU[d] for d in diasU])) if diasU else np.nan
    T_Z = float(np.mean([TZ[d] for d in diasZ])) if diasZ else np.nan
    print(f"P evaluados huella {nU} en {len(diasU)} días; T_U {T_U:.4f}; zona {nZ} en {len(diasZ)} días; "
          f"T_Z {T_Z:.4f}", flush=True)

    print("matrices de nulos...", flush=True)
    VR = {d: np.array([media_dia([U_en(2026, d, i, j) for i in idx_dia[d]]) for j in range(12)]) for d in diasU}
    VN = {d: np.array([media_dia([U_en(2026, n, i) for i in idx_dia[d]]) for n in diasN]) for d in diasU}
    dias24 = d24
    VY = {d: np.array([media_dia([U_en(2024, y, i) for i in idx_dia[d]]) for y in dias24]) for d in diasU}
    dias25 = [d for d in d25 if "2025-10-21" <= d <= "2025-11-24"]
    ZN = {d: np.array([media_dia([Z_en(2026, n, Pinfo[i]["s"]) for i in idx_dia[d]]) for n in diasN]) for d in diasZ}
    ZY = {d: np.array([media_dia([Z_en(2024, y, Pinfo[i]["s"]) for i in idx_dia[d]]) for y in dias24]) for d in diasZ}
    Z25 = {d: np.array([media_dia([Z_en(2025, e, Pinfo[i]["s"]) for i in idx_dia[d]]) for e in dias25]) for d in diasZ}
    # D: W[i][k] = U del cuadro real i con la huella k (dilatada, sin girar)
    W = {}
    for d in diasU:
        for i in idx_dia[d]:
            o = obj(2026, Pinfo[i]["dia"], Pinfo[i]["s"])
            ev = zona_eval(o, sza_de(2026, Pinfo[i]["dia"], Pinfo[i]["s"]))
            W[i] = np.array([valor_U(o, Pinfo[k]["dil"][0]) if ev else np.nan for k in range(len(Pinfo))])
    print(f"matrices listas {time.time() - t00:.0f}s", flush=True)

    rng = np.random.default_rng(SEMILLA)
    res = {}
    nullR = mc_mean([VR[d] for d in diasU], rng, B_MC)
    nullN = mc_mean([VN[d] for d in diasU], rng, B_MC)
    # D
    nullD = np.empty(B_MC)
    don = {d: [e for e in diasP if e != d] for d in diasU}
    M = np.full((len(diasU), B_MC), np.nan)
    for a, d in enumerate(diasU):
        e_pick = rng.integers(0, len(don[d]), B_MC)
        acc = np.zeros(B_MC)
        cnt = np.zeros(B_MC)
        for i in idx_dia[d]:
            # cada cuadro toma una huella al azar del donante: índice uniforme dentro de los cuadros del donante
            u = rng.random(B_MC)
            vals = np.empty(B_MC)
            for ei, e in enumerate(don[d]):
                sel = e_pick == ei
                kk = np.array(idx_dia[e])[(u[sel] * len(idx_dia[e])).astype(int)]
                vals[sel] = W[i][kk]
            fin = np.isfinite(vals)
            acc[fin] += vals[fin]
            cnt[fin] += 1
        with np.errstate(invalid="ignore"):
            M[a] = np.where(cnt > 0, acc / cnt, np.nan)
    nullD[:] = np.nanmean(M, 0)
    nullY = mc_mean([VY[d] for d in diasU], rng, B_MC)
    for nom, nl in (("R", nullR), ("N", nullN), ("D", nullD), ("Y", nullY)):
        p, n = pval(T_U, nl)
        res[f"p_{nom}"] = p
        res[f"n_{nom}"] = n
        res[f"null_{nom}_p50_p99"] = [round(float(np.nanpercentile(nl, 50)), 4), round(float(np.nanpercentile(nl, 99)), 4)]
    zres = {}
    for nom, Zd in (("N", ZN), ("Y", ZY), ("25", Z25)):
        nl = mc_mean([Zd[d] for d in diasZ], rng, B_MC)
        p, n = pval(T_Z, nl)
        zres[f"p_{nom}"] = p
        zres[f"null_{nom}_p50_p99"] = [round(float(np.nanpercentile(nl, 50)), 4), round(float(np.nanpercentile(nl, 99)), 4)]
    print("huella:", res, "\nzona:", zres, flush=True)

    # control positivo 08-11
    c0811 = None
    if "2026-11-08" in diasU:
        v = VN["2026-11-08"]
        v = v[np.isfinite(v)]
        c0811 = dict(U=round(TU["2026-11-08"], 4), n_N=int(len(v)),
                     p=float((1 + np.sum(v >= TU["2026-11-08"])) / (len(v) + 1)),
                     N_max=round(float(v.max()), 4) if len(v) else None)
        c0811["pasa"] = bool(c0811["p"] <= 0.05)
    print("control 08-11:", c0811, flush=True)

    # poder sintético
    def poder(f):
        rp = np.random.default_rng(SEM_POD)
        okU, okZ, pRs, pNs = 0, 0, [], []
        for rep in range(N_POD):
            Vr, Vn, Vz, Vzn = [], [], [], []
            for d in diasU:
                ds = diasN[rp.integers(0, len(diasN))]
                vals = np.full((len(idx_dia[d]), 12), np.nan)
                zs = []
                for a, i in enumerate(idx_dia[d]):
                    p = Pinfo[i]
                    o = obj(2026, ds, p["s"])
                    if not zona_eval(o, sza_de(2026, ds, p["s"])):
                        continue
                    S = {}
                    und = {b: hijos(p["und"], b) for b in FAC}
                    for b in ("C02", "C05"):
                        rho = o[f"R{b}"].astype("float64").copy()
                        rho[und[b]] += f * (RHO_P[b] - (1 - T_P) * rho[und[b]])
                        S[f"U{b}"] = apartamiento(b, rho, o[f"B{b}"], o[f"S{b}"], o["ok2"])
                    S["ok2"] = o["ok2"]
                    for j in range(12):
                        vals[a, j] = valor_U(S, p["dil"][j])
                    zs.append(valor_Z(S))
                Vr.append(np.nanmean(vals, 0) if np.isfinite(vals).any() else np.full(12, np.nan))
                Vn.append(VN[d][np.array([n != ds for n in diasN])] if d in VN else np.array([np.nan]))
                if d in ZN:
                    Vz.append(np.nanmean(zs) if len(zs) and np.isfinite(zs).any() else np.nan)
                    Vzn.append(ZN[d][np.array([n != ds for n in diasN])])
            Ts = np.nanmean([v[0] for v in Vr])
            pR = pval(Ts, mc_mean(Vr, rp, B_POD))[0]
            pN = pval(Ts, mc_mean(Vn, rp, B_POD))[0]
            pRs.append(pR)
            pNs.append(pN)
            okU += (pR <= P_MAX) and (pN <= P_MAX)
            if Vz:
                Tz = np.nanmean(Vz)
                okZ += pval(Tz, mc_mean(Vzn, rp, B_POD))[0] <= P_MAX
        return dict(f=f, poder_huella=okU / N_POD, poder_zona=okZ / N_POD,
                    pR_med=float(np.median(pRs)), pN_med=float(np.median(pNs)))

    pod = poder(F_POD)
    print("poder f=0,25:", pod, flush=True)
    pod_inf = poder(F_INF)
    print("poder f=0,10 (informativo):", pod_inf, flush=True)

    # descriptivos por banda y superficie
    def desc(pares):
        acc = {f"{b}_{sup}": [] for b in ("C02", "C05") for sup in ("nieve", "mixto")}
        for anio, dia, i in pares:
            p = Pinfo[i]
            o = obj(anio, dia, p["s"])
            if not zona_eval(o, sza_de(anio, dia, p["s"])):
                continue
            ok = p["dil"][0] & o["ok2"]
            if ok.sum() / max(p["dil"][0].sum(), 1) < FR_HUELLA:
                continue
            b05 = o["BC05"]
            b02a5 = a_padre(o["BC02"][None], "C02", np.nanmean)[0]       # a 2 km
            nieve2 = (a_padre(b05[None], "C05", np.nanmean)[0] < NIEVE_B05) & (b02a5 > NIEVE_B02)
            for b in ("C02", "C05"):
                a = (o[f"R{b}"] - o[f"B{b}"])
                for sup, m in (("nieve", nieve2), ("mixto", ~nieve2)):
                    sel = hijos(ok & m, b)
                    v = a[sel]
                    acc[f"{b}_{sup}"].extend(v[np.isfinite(v)].tolist())
        return {k: (None if not v else dict(n=len(v), mediana=round(float(np.median(v)), 4),
                                            p25=round(float(np.percentile(v, 25)), 4),
                                            p75=round(float(np.percentile(v, 75)), 4))) for k, v in acc.items()}

    desc_P = desc([(2026, p["dia"], i) for i, p in enumerate(Pinfo)])
    desc_N = desc([(2026, n, i) for i in range(len(Pinfo)) for n in diasN])
    desc_Y = desc([(2024, y, i) for i in range(len(Pinfo)) for y in dias24])

    # cuadros sin evaluar, por razón y año
    def razones(anio, dias, slots):
        c = defaultdict(int)
        for dia in dias:
            for s in slots:
                o = obj(anio, dia, s)
                if o is None:
                    c["sin_dato"] += 1
                elif sza_de(anio, dia, s) >= SZA_MAX:
                    c["sol"] += 1
                elif o["ok2"][ZONA2].mean() < FR_ZONA:
                    c["nube_o_base"] += 1
                else:
                    c["evaluado"] += 1
        return dict(c)

    sinv = {"2026_N": razones(2026, diasN, slotsP), "2024": razones(2024, dias24, slotsP),
            "2025_seco": razones(2025, dias25, slotsP)}

    # veredictos
    if nU < MIN_P or len(diasU) < MIN_DIAS:
        ver = "NO DECIDIBLE (pocos)"
    elif pod["poder_huella"] < POD_MIN:
        ver = "SIN PODER"
    elif T_U > 0 and res["p_R"] <= P_MAX and res["p_N"] <= P_MAX:
        ver = "VE LA PLUMA" + (", y sigue a esta pluma" if res["p_D"] <= P_MAX else ", sin separar esta pluma de la de otro día") \
              + (", más que un año sin pluma" if res["p_Y"] <= P_MAX else ", sin separarse de un año sin pluma")
    elif res["p_R"] > P_MAX and res["p_N"] > P_MAX:
        ver = "NO SE APARTA"
    else:
        ver = "NO DECIDIBLE"
    if nZ < MIN_P or len(diasZ) < MIN_DIAS:
        verz = "NO DECIDIBLE (pocos)"
    elif pod["poder_zona"] < POD_MIN:
        verz = "SIN PODER"
    elif zres["p_25"] <= P_MAX and zres["p_N"] <= P_MAX:
        verz = "SE APARTA EN LOS P"
    elif zres["p_25"] <= P_MAX and zres["p_N"] > P_MAX:
        verz = "2026 SE APARTA, LOS P NO SE SEPARAN"
    elif zres["p_25"] > P_MAX and zres["p_N"] > P_MAX:
        verz = "NO SE APARTA"
    else:
        verz = "NO DECIDIBLE"
    if zres["p_25"] <= P_MAX and zres["p_Y"] > P_MAX:
        verz += "; el año explica el apartamiento"
    print("VEREDICTO huella:", ver, "| zona:", verz, flush=True)

    out = dict(criterio="criterio_2026-11-27.md (741acb4, anexo c6df303)",
               faltan_cuadros={"2025": f25, "2026": f26, "2024": f24}, px_fuera_ventana=perdidos,
               P_dia=len(P), dias_P=diasP, dias_N=diasN,
               huella=dict(P_evaluados=nU, dias_evaluados=diasU, T_U=T_U, por_dia={d: TU[d] for d in diasP}, **res),
               zona=dict(P_evaluados=nZ, dias_evaluados=diasZ, T_Z=T_Z, por_dia={d: TZ[d] for d in diasP}, **zres),
               control_0811=c0811, poder=pod, poder_informativo=pod_inf,
               descriptivo=dict(P=desc_P, N_mismo_lugar_hora=desc_N, Y2024_mismo_lugar_hora=desc_Y),
               sin_evaluar=sinv, veredicto_huella=ver, veredicto_zona=verz,
               segundos=round(time.time() - t00))
    with open(os.path.join(RES, "s31f_resultado.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1, default=float)
    with open(os.path.join(RES, "s31f_por_cuadro.csv"), "w", encoding="utf-8", newline="") as f:
        cols = ["dia", "hora", "sza", "huella_px", "zona_desp", "huella_desp", "U", "U_C02", "U_C05", "Z"]
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in filas:
            w.writerow({c: r.get(c) for c in cols})
    # matrices para post hoc, en D:
    np.savez_compressed(os.path.join(TRAB, "nulos.npz"), diasU=diasU, diasN=diasN, dias24=dias24, dias25=dias25,
                        **{f"VR_{d}": VR[d] for d in diasU}, **{f"VN_{d}": VN[d] for d in diasU},
                        **{f"VY_{d}": VY[d] for d in diasU}, **{f"ZN_{d}": ZN[d] for d in diasZ},
                        **{f"Z25_{d}": Z25[d] for d in diasZ}, **{f"ZY_{d}": ZY[d] for d in diasZ})
    print("listo", f"{time.time() - t00:.0f}s", flush=True)


if __name__ == "__main__":
    medir()
