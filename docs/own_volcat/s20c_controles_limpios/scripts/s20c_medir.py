r"""S20c, diseno 2: implementa criterio_2026-11-23.md con las enmiendas 1 y 2 antes de medir (E1 al 60 %, +-60 min).

Pregunta: con la linea base tomada antes de toda actividad (21-09 al 21-10, cuadros despejados por la ACMF, mismo
minuto, mismos pixeles) y la temporada restada con cuadros despejados de dias de noviembre sin actividad (placebo),
la BTD de la huella VOLCAT se aparta de lo que dan los dias sin pluma? Si se aparta y con el control original no,
el control viejo estaba contaminado.

Por que este diseno y no el pareo de las pruebas viejas: el ensayo en seco del diseno 1 (s20c_medir_v1_pareo.py)
mostro que los positivos estan ~9 K mas tibios que cualquier cuadro despejado del pozo limpio a la misma hora
(temporada), asi que "BT11 parecida a 3 K" no se cumple con dias limpios (cobertura 3 a 27 %), y que los dias placebo
estan despejados en solo 3 a 9 % de esos minutos (el placebo "cualquier cielo" media nubes). Aqui:
- cada cuadro que hace de positivo, de placebo o de control original tiene que estar despejado (regla E1 de la ACMF);
- el control es la linea base limpia del propio pixel (mediana de los dias limpios despejados en s - 1, s y s + 1),
  sin pareo por BT11 (el pareo es justo lo que llevo a los controles a dias activos, MET-01 y MET-02);
- la temporada la mide el placebo: cuadros despejados de los 14 dias libres a +-30 min, contra su propia linea base.

Modos: `seco` (falsa alarma, poder y cobertura; no lee BTD ni BT11 del dia positivo ni del control original) y
`medir`. Uso: python -I s20c_medir.py seco|medir
"""
import csv
import json
import os
import sys
import warnings
from datetime import datetime, timedelta

import numpy as np
from scipy.stats import rankdata

sys.stdout.reconfigure(encoding="utf-8")
warnings.simplefilter("ignore", RuntimeWarning)
AQUI = os.path.dirname(os.path.abspath(__file__))
OV = os.path.abspath(os.path.join(AQUI, "..", ".."))
RES = os.path.join(os.path.dirname(AQUI), "resultados")
sys.path.insert(0, os.path.join(OV, "h24_pulsos_reav", "scripts"))
sys.path.insert(0, os.path.join(OV, "h29_pluma_0811", "scripts"))
sys.path.insert(0, AQUI)
import h24_medir as H  # noqa: E402  (cargar, despejada, gfs_t, Planck, EXCLUIDOS)
import h29_comun as C29  # noqa: E402  (decodificador del PNG con el corrimiento de H14)
import s20c_pares as SP  # noqa: E402

# ---------- parametros (criterio + enmienda 1) ----------
T0 = H.T0
NDIAS, NY, NX = H.NDIAS, H.NY, H.NX
NPIX = NY * NX
LIMPIO = list(range(0, 31))                 # 21-09 al 21-10
EXCL = {(datetime.strptime(s, "%Y-%m-%d") - T0).days for s in H.EXCLUIDOS}
PLACEBO = [d for d in range(31, NDIAS) if d not in EXCL]
MIN_PX = 3
MIN_DIAS_BASE = 3                           # linea base: >= 3 dias limpios despejados con dato en el pixel
FRAC_E1 = 0.60                              # enmienda 2: regla E1 con 60 % del terreno bajo despejado (no 80 %)
W_BASE = 6                                  # enmienda 2: linea base con +-6 cuadros (+-60 min)
SLOT_PLAC = 6                               # enmienda 2: placebo a +-6 cuadros (+-60 min)
MIN_PLAC_FR, MIN_PLAC_DIAS = 3, 2           # referencia placebo: >= 3 cuadros de >= 2 dias
MIN_UNIDADES, MIN_DIAS_POS = 10, 2          # menos que esto: SIN COBERTURA
MIN_NULO_VALIDAS, MIN_NULO_DISTINTOS = 1000, 50   # enmienda 2: nulo degenerado = INVALIDA
N_NULO, N_FA, N_PODER = 2000, 500, 500
SEMILLA = 20261123
EPS = [0.05, 0.10, 0.15, 0.30]
BETA = 0.70
Z_TOPE = 4500.0
R_KM = 50.0
CRATER_PX = (42, 46)
UMBRAL_DIF = 0.10
H3_HUE = r"D:\goes_notas\local_f3a7d295\h12_datos\extra\h3_meta\huellas_h3.npz"
B73_HUE = r"D:\goes_notas\local_f3a7d295\h12_datos\extra\b73_meta\huellas_b73.npz"
PRUEBAS = ["paso2", "H3", "beta73", "VAAC", "H13", "H11_H12"]


def dia_slot(dt):
    return (dt - T0).days, dt.hour * 6 + dt.minute // 10


def fecha(d):
    return f"{T0 + timedelta(days=d):%d-%m}"


# ---------- huellas ----------
CRATER_BLOQUE = np.zeros((NY, NX), bool)
CRATER_BLOQUE[CRATER_PX[0] - 1:CRATER_PX[0] + 2, CRATER_PX[1] - 1:CRATER_PX[1] + 2] = True
CERCA = C29.DIST <= R_KM


def huella_png(fn, con_crater=False):
    ok, mid, barra = C29.decodifica_png(fn)
    if not barra:
        return None
    ash, _ = C29.a_abi(ok, mid)
    m = ash & CERCA
    if not con_crater:
        m &= ~CRATER_BLOQUE
    return m


def anillo(F):
    """Pixeles a 2 a 5 pixeles (Chebyshev) de F, fuera de F y del bloque del crater, a <= 50 km."""
    from scipy.ndimage import binary_dilation
    est = np.ones((3, 3), bool)
    return binary_dilation(F, est, iterations=5) & ~binary_dilation(F, est, iterations=1) & ~CRATER_BLOQUE & CERCA


def cuadros(variante):
    """Por prueba: lista de {pos, ctrl, D, s, Dc, sc, F, R}. Huella del PNG (o la guardada, en S3)."""
    idx = SP.indice_png()
    h3g = dict(np.load(H3_HUE)) if variante == "S3" else None
    b7g = dict(np.load(B73_HUE)) if variante == "S3" else None
    cache, out = {}, {p: [] for p in PRUEBAS}
    descartados = {p: 0 for p in PRUEBAS}
    for prueba, p, c in SP.pares():
        if variante == "S3" and prueba in ("H3", "beta73"):
            k = f"{p:%Y%m%d_%H%M}" if prueba == "H3" else "h_" + f"{p:%Y%m%d_%H%M}"
            g = h3g if prueba == "H3" else b7g
            F = g[k].astype(bool) & CERCA & ~CRATER_BLOQUE if k in g else None
        else:
            ck = (p, variante == "S4")
            if ck not in cache:
                cache[ck] = huella_png(idx[p], con_crater=(variante == "S4")) if p in idx else None
            F = cache[ck]
        if F is None or F.sum() < MIN_PX:
            descartados[prueba] += 1
            continue
        D, s = dia_slot(p)
        Dc, sc = dia_slot(c)
        out[prueba].append({"pos": p, "ctrl": c, "D": D, "s": s, "Dc": Dc, "sc": sc, "F": F, "R": anillo(F)})
    vistos = {q["pos"] for q in out["H3"]}
    out["H11_H12"] = list(out["H3"]) + [q for q in out["beta73"] if q["pos"] not in vistos]
    return out, descartados


# ---------- datos ----------
class Datos:
    def __init__(self):
        r14, r15, acm, co14, co15 = H.cargar()
        self.co14, self.co15 = co14, co15
        self.r14 = r14.reshape(NDIAS * 144, NPIX)
        self.r15 = r15.reshape(NDIAS * 144, NPIX)
        self.bt11 = np.empty_like(self.r14)
        self.btd = np.empty_like(self.r14)
        for i in range(0, self.r14.shape[0], 1440):
            b11 = H.bt_de_rad(self.r14[i:i + 1440].astype("float64"), co14)
            b12 = H.bt_de_rad(self.r15[i:i + 1440].astype("float64"), co15)
            self.bt11[i:i + 1440] = b11
            self.btd[i:i + 1440] = b11 - b12
        la, lo, h = H.SITIOS["chillan"]                     # regla E1 de H24 con el umbral de la enmienda 2
        dd = H.hav(H.LAT, H.LON, la - 0.93 * h / 1000.0 / 111.2, lo)
        bajo = np.where((dd >= 10.0) & (dd <= 30.0) & (H.ZDEM < 1300.0))[0]
        self.frac_claro = (acm[:, :, bajo] <= 1).mean(2)
        self.claro = self.frac_claro >= FRAC_E1             # (NDIAS, 144)
        self.Ttope = H.gfs_t([Z_TOPE])[:, :, 0]             # (NDIAS, 144)

    def campo(self, var, d, s, px, iny=None):
        """Variable en (d, s) sobre px. iny = eps pinta la capa en (d, s), no en s - 1."""
        t = d * 144 + s
        if iny is None:
            b11, bd = self.bt11[t, px].astype(float), self.btd[t, px].astype(float)
        else:
            Tt = self.Ttope[d, s]
            e12 = 1 - (1 - iny) ** BETA
            I14 = (1 - iny) * self.r14[t, px].astype(float) + iny * H.rad_de_bt(Tt, self.co14)
            I15 = (1 - e12) * self.r15[t, px].astype(float) + e12 * H.rad_de_bt(Tt, self.co15)
            b11 = H.bt_de_rad(I14, self.co14)
            bd = b11 - H.bt_de_rad(I15, self.co15)
        if var == "btd":
            return bd
        if var == "bt11":
            return b11
        if t == 0:
            return np.full(len(px), np.nan)
        return (bd - self.btd[t - 1, px]) if var == "dbtd" else (b11 - self.bt11[t - 1, px])

    def campo_t(self, var, tl, px):
        tl = np.asarray(tl)
        if var == "btd":
            return self.btd[np.ix_(tl, px)].astype(float)
        if var == "bt11":
            return self.bt11[np.ix_(tl, px)].astype(float)
        a = self.btd if var == "dbtd" else self.bt11
        return (a[np.ix_(tl, px)] - a[np.ix_(tl - 1, px)]).astype(float)


class Motor:
    """Anomalia de un cuadro contra la linea base limpia del pixel. modo: 'huella' (mediana sobre F de la anomalia)
    o 'anillo' (S1: anomalia de F menos anomalia del anillo, en el mismo cuadro). gate_x: el cuadro que hace de
    positivo, placebo o control original tiene que estar despejado (E1)."""

    def __init__(self, D, modo="huella", gate_x=True):
        self.D, self.modo, self.gate_x = D, modo, gate_x
        self._base = {}

    def base(self, var, s, px):
        k = (var, s, px.tobytes())
        if k not in self._base:
            tl, dias = [], []
            for d in LIMPIO:
                for ss in range(s - W_BASE, s + W_BASE + 1):
                    if 0 <= ss < 144 and self.D.claro[d, ss]:
                        tl.append(d * 144 + ss)
                        dias.append(d)
            if not tl:
                self._base[k] = np.full(len(px), np.nan)
            else:
                v = self.D.campo_t(var, tl, px)
                dias = np.array(dias)
                nd = np.zeros(len(px), int)
                for d in np.unique(dias):
                    nd += np.isfinite(v[dias == d]).any(0)
                b = np.nanmedian(v, 0)
                b[nd < MIN_DIAS_BASE] = np.nan
                self._base[k] = b
        return self._base[k]

    def delta(self, var, x, s, F, R, iny=None, pix=False):
        nada = (np.nan, None, None) if pix else np.nan
        if self.gate_x and not self.D.claro[x, s]:
            return nada
        px = np.flatnonzero(F)
        a = self.D.campo(var, x, s, px, iny=iny)
        b = self.base(var, s, px)
        ok = np.isfinite(a) & np.isfinite(b)
        if ok.sum() < MIN_PX:
            return nada
        val = float(np.median(a[ok] - b[ok]))
        if self.modo == "anillo":
            pr = np.flatnonzero(R)
            ar = self.D.campo(var, x, s, pr)
            br = self.base(var, s, pr)
            okr = np.isfinite(ar) & np.isfinite(br)
            if okr.sum() < MIN_PX:
                return nada
            val -= float(np.median(ar[okr] - br[okr]))
        return (val, a[ok], b[ok]) if pix else val


def auc(a, b):
    a, b = np.asarray(a, float), np.asarray(b, float)
    a, b = a[np.isfinite(a)], b[np.isfinite(b)]
    if not len(a) or not len(b):
        return float("nan")
    r = rankdata(np.concatenate([a, b]))
    return float((r[:len(a)].sum() - len(a) * (len(a) + 1) / 2) / (len(a) * len(b)))


# ---------- tablas por unidad ----------
def unidad(M, var, dia, slot, F, R, eps_list, leer_x, excluir=()):
    """dia, slot: el cuadro que hace de positivo. Placebo: cuadros despejados de los dias libres (sin `excluir`) a
    +-30 min (sin gate: el mismo slot), cada uno contra su linea base. near[j] = el del slot mas cercano por dia."""
    u = {"dia": dia, "slot": slot, "plac": {}, "near": {}}
    slots = range(slot - SLOT_PLAC, slot + SLOT_PLAC + 1) if M.gate_x else [slot]
    for j in PLACEBO:
        if j == dia or j in excluir:
            continue
        lst = []
        for ss in sorted(slots, key=lambda z: (abs(z - slot), z)):
            if not 0 <= ss < 144:
                continue
            v, a, b = M.delta(var, j, ss, F, R, pix=True)
            if np.isfinite(v):
                lst.append(v)
                if j not in u["near"]:
                    u["near"][j] = {"s": ss, "v": v, "a": a, "b": b,
                                    "iny": {e: M.delta(var, j, ss, F, R, iny=e) for e in eps_list}}
        if lst:
            u["plac"][j] = lst
    u["claro_x"] = bool(M.D.claro[dia, slot])
    if leer_x:
        v, a, b = M.delta(var, dia, slot, F, R, pix=True)
        u["x"], u["xa"], u["xb"] = v, a, b
    return u


def ref(u, sin=None):
    v = [x for j, l in u["plac"].items() if j != sin for x in l]
    nd = sum(1 for j in u["plac"] if j != sin)
    return float(np.median(v)) if len(v) >= MIN_PLAC_FR and nd >= MIN_PLAC_DIAS else np.nan


def real(us):
    d = [u["x"] - ref(u) for u in us if np.isfinite(u.get("x", np.nan)) and np.isfinite(ref(u))]
    return (float(np.median(d)) if d else np.nan), len(d)


def replicas(us, n, rng, iny=None):
    """Nulo de bloques de dia: cada dia que hace de positivo se reemplaza entero por un dia libre sorteado."""
    dias = sorted({u["dia"] for u in us})
    S = np.full(n, np.nan)
    for r in range(n):
        el = {D: PLACEBO[rng.integers(len(PLACEBO))] for D in dias}
        d = []
        for u in us:
            j = el[u["dia"]]
            if j not in u["near"]:
                continue
            x = u["near"][j]["v"] if iny is None else u["near"][j]["iny"][iny]
            m = ref(u, sin=j)
            if np.isfinite(x) and np.isfinite(m):
                d.append(x - m)
        if d:
            S[r] = np.median(d)
    return S


def p_colas(S, nulo):
    nulo = nulo[np.isfinite(nulo)]
    if not np.isfinite(S) or not len(nulo):
        return np.nan, np.nan
    return (1 + (nulo <= S).sum()) / (1 + len(nulo)), (1 + (nulo >= S).sum()) / (1 + len(nulo))


def holm(ps):
    idx = sorted([i for i, p in enumerate(ps) if np.isfinite(p)], key=lambda i: ps[i])
    out, acum = [np.nan] * len(ps), 0.0
    for r, i in enumerate(idx):
        acum = max(acum, min(1.0, (len(idx) - r) * ps[i]))
        out[i] = acum
    return out


def poder_y_fa(us, nulo, eps_list):
    fa = [p_colas(nulo[r], np.delete(nulo, r))[0] <= 0.05 for r in range(min(N_FA, len(nulo))) if np.isfinite(nulo[r])]
    pod = {}
    for e in eps_list:
        Si = replicas(us, N_PODER, np.random.default_rng(SEMILLA + int(e * 1000)), iny=e)
        pod[str(e)] = float(np.mean([p_colas(x, nulo)[0] <= 0.05 for x in Si if np.isfinite(x)]))
    return float(np.mean(fa)) if fa else np.nan, pod


def cobertura(us):
    ok = [u for u in us if u["claro_x"] and np.isfinite(ref(u))]
    return ok, len({u["dia"] for u in ok})


# ---------- ensayo en seco ----------
def seco():
    Dt = Datos()
    QQ, desc = cuadros("principal")
    M = Motor(Dt, "huella", gate_x=True)
    res = {"criterio": "criterio_2026-11-23.md (b06c711) + enmiendas 1 y 2 antes de medir",
           "placebo": [fecha(d) for d in PLACEBO], "limpio": f"{fecha(LIMPIO[0])} a {fecha(LIMPIO[-1])}",
           "descartados_huella<3px": desc, "pruebas": {}}
    for prueba in PRUEBAS:
        us = [unidad(M, "btd", q["D"], q["s"], q["F"], q["R"], EPS, leer_x=False) for q in QQ[prueba]]
        ok, ndias = cobertura(us)
        nulo = replicas(ok, N_NULO, np.random.default_rng(SEMILLA))
        fa, pod = poder_y_fa(ok, nulo, EPS)
        d = {"cuadros": len(us), "positivo_despejado": int(sum(u["claro_x"] for u in us)),
             "unidades_validas": len(ok), "dias_validos": ndias,
             "cobertura": len(ok) / len(us) if us else 0.0,
             "placebo_cuadros_mediana": float(np.median([sum(len(l) for l in u["plac"].values()) for u in ok])) if ok else 0,
             "placebo_dias_mediana": float(np.median([len(u["plac"]) for u in ok])) if ok else 0,
             "falsa_alarma": fa, "poder": pod, "nulo_validas": int(np.isfinite(nulo).sum()),
             "nulo_p05": float(np.nanpercentile(nulo, 5)) if np.isfinite(nulo).any() else np.nan,
             "nulo_p95": float(np.nanpercentile(nulo, 95)) if np.isfinite(nulo).any() else np.nan,
             "nulo_distintos": int(len(np.unique(np.round(nulo[np.isfinite(nulo)], 6))))}
        d["sin_cobertura"] = len(ok) < MIN_UNIDADES or ndias < MIN_DIAS_POS
        d["nulo_degenerado"] = d["nulo_validas"] < MIN_NULO_VALIDAS or d["nulo_distintos"] < MIN_NULO_DISTINTOS
        d["valida"] = (not d["sin_cobertura"]) and (not d["nulo_degenerado"]) and np.isfinite(fa) and fa <= 0.10
        res["pruebas"][prueba] = d
        print(prueba, json.dumps(d), flush=True)
    os.makedirs(RES, exist_ok=True)
    json.dump(res, open(os.path.join(RES, "seco.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)


# ---------- medicion ----------
def veredicto(S, E, pb, pa, poder):
    if not np.isfinite(S):
        return "SIN DATO"
    if pb <= 0.05:
        return "CONTROL CONTAMINADO" if S <= E - UMBRAL_DIF else "SEÑAL QUE YA ESTABA"
    if pa <= 0.05 and S > 0:
        return "SIGNO CONTRARIO"
    return "NO ERA ESO" if poder >= 0.80 else "SIN PODER"


def medir_variante(Dt, nombre, var, modo="huella", gate_x=True, huellas="principal", eps_list=(), filas_csv=None,
                   dos_colas=False):
    QQ, desc = cuadros(huellas)
    M = Motor(Dt, modo, gate_x=gate_x)
    out = {}
    for prueba in PRUEBAS:
        Q = QQ[prueba]
        us = [unidad(M, var, q["D"], q["s"], q["F"], q["R"], eps_list, leer_x=True) for q in Q]
        for u, q in zip(us, Q):
            u["q"] = q
        ok, ndias = cobertura(us) if gate_x else ([u for u in us if np.isfinite(ref(u))], len({u["dia"] for u in us}))
        S, n = real(ok)
        nulo = replicas(ok, N_NULO, np.random.default_rng(SEMILLA))
        pb, pa = p_colas(S, nulo)
        # E_orig: diferencia con el control que eligio la prueba vieja, sobre las mismas unidades validas de S
        eo, oa, ob = [], [], []
        for u in ok:
            if not np.isfinite(u["x"]):
                continue
            q = u["q"]
            px = np.flatnonzero(q["F"])
            a0, b0 = Dt.campo(var, q["D"], q["s"], px), Dt.campo(var, q["Dc"], q["sc"], px)
            g = np.isfinite(a0) & np.isfinite(b0)
            if g.sum() >= MIN_PX:
                eo.append(float(np.median(a0[g] - b0[g])))
                oa.append(a0[g])
                ob.append(b0[g])
        E = float(np.median(eo)) if eo else np.nan
        # chequeo C: el control original (si cae en dia excluido por actividad) en el lugar del positivo
        usC = []
        for q in Q:
            if q["Dc"] in EXCL:
                uc = unidad(M, var, q["Dc"], q["sc"], q["F"], q["R"], (), leer_x=True)
                usC.append(uc)
        okC = [u for u in usC if (u["claro_x"] or not gate_x) and np.isfinite(ref(u))]
        SC, nC = real(okC)
        pCb, pCa = p_colas(SC, replicas(okC, N_NULO, np.random.default_rng(SEMILLA + 7)))
        cat = lambda L: np.concatenate(L) if L else np.array([])  # noqa: E731
        A_orig = auc(cat(oa), cat(ob))
        A_lim = auc(cat([u["xa"] for u in ok if u.get("xa") is not None]),
                    cat([u["xb"] for u in ok if u.get("xb") is not None]))
        A_pla = auc(cat([w["a"] for u in ok for w in u["near"].values()]),
                    cat([w["b"] for u in ok for w in u["near"].values()]))
        r = {"cuadros": len(Q), "unidades_validas": len(ok), "dias_validos": ndias, "S_validos": n,
             "S": S, "p_baja": pb, "p_alta": pa, "p_dos": min(1.0, 2 * min(pb, pa)) if np.isfinite(pb) else np.nan,
             "E_orig": E, "E_orig_n": len(eo),
             "x_menos_base_mediana": float(np.median([u["x"] for u in ok if np.isfinite(u["x"])])) if ok else np.nan,
             "placebo_menos_base_mediana": float(np.median([ref(u) for u in ok])) if ok else np.nan,
             "nulo_p05": float(np.nanpercentile(nulo, 5)) if np.isfinite(nulo).any() else np.nan,
             "nulo_p95": float(np.nanpercentile(nulo, 95)) if np.isfinite(nulo).any() else np.nan,
             "C_S": SC, "C_n": nC, "C_p_baja": pCb, "C_p_alta": pCa,
             "AUC_orig": A_orig, "AUC_limpio": A_lim, "AUC_placebo": A_pla,
             "AUC_corregido": 0.5 + A_lim - A_pla if np.isfinite(A_lim) and np.isfinite(A_pla) else np.nan,
             "dias_positivos": sorted({fecha(u["dia"]) for u in ok})}
        if eps_list:
            fa, pod = poder_y_fa(ok, nulo, eps_list)
            r["falsa_alarma"], r["poder"] = fa, pod
        out[prueba] = r
        if filas_csv is not None:
            for u in us:
                q = u["q"]
                filas_csv.append({"variante": nombre, "prueba": prueba, "pos": f"{q['pos']:%Y-%m-%d %H:%M}",
                                  "ctrl_orig": f"{q['ctrl']:%Y-%m-%d %H:%M}", "npx": int(q["F"].sum()),
                                  "despejado": u["claro_x"], "x_menos_base": u["x"], "placebo_menos_base": ref(u),
                                  "placebo_cuadros": sum(len(l) for l in u["plac"].values()),
                                  "placebo_dias": len(u["plac"])})
        print(nombre, prueba, json.dumps({k: (round(v, 4) if isinstance(v, float) else v) for k, v in r.items()
                                          if k != "dias_positivos"}), flush=True)
    return out, desc


def medir():
    seco_res = json.load(open(os.path.join(RES, "seco.json"), encoding="utf-8"))
    Dt = Datos()
    res = {"criterio": "criterio_2026-11-23.md (b06c711) + enmiendas 1 y 2 antes de medir", "variantes": {}}
    filas = []
    pri, desc = medir_variante(Dt, "principal_btd", "btd", eps_list=EPS, filas_csv=filas)
    for p, ph in zip(PRUEBAS, holm([pri[p]["p_baja"] for p in PRUEBAS])):
        r = pri[p]
        r["p_holm"] = ph
        sd = seco_res["pruebas"][p]
        if sd["sin_cobertura"]:
            r["veredicto"] = "SIN COBERTURA"
        elif not sd["valida"]:
            r["veredicto"] = "INVÁLIDA"
        else:
            r["veredicto"] = veredicto(r["S"], r["E_orig"], r["p_baja"], r["p_alta"], r["poder"]["0.1"])
    res["variantes"]["principal_btd"] = pri
    res["descartados_huella<3px"] = desc
    res["variantes"]["S5_bt11"], _ = medir_variante(Dt, "S5_bt11", "bt11")
    res["variantes"]["S5_dbtd"], _ = medir_variante(Dt, "S5_dbtd", "dbtd")
    res["variantes"]["S5_dbt11"], _ = medir_variante(Dt, "S5_dbt11", "dbt11")
    res["variantes"]["S1_anillo_btd"], _ = medir_variante(Dt, "S1_anillo_btd", "btd", modo="anillo")
    res["variantes"]["S1_anillo_bt11"], _ = medir_variante(Dt, "S1_anillo_bt11", "bt11", modo="anillo")
    res["variantes"]["S2_sin_ACMF_btd"], _ = medir_variante(Dt, "S2_sin_ACMF_btd", "btd", gate_x=False)
    res["variantes"]["S3_huella_guardada_btd"], _ = medir_variante(Dt, "S3_huella_guardada_btd", "btd", huellas="S3")
    res["variantes"]["S4_con_crater_btd"], _ = medir_variante(Dt, "S4_con_crater_btd", "btd", huellas="S4")
    os.makedirs(RES, exist_ok=True)
    json.dump(res, open(os.path.join(RES, "s20c_resultado.json"), "w", encoding="utf-8"), indent=1,
              ensure_ascii=False, default=float)
    with open(os.path.join(RES, "s20c_por_cuadro.csv"), "w", newline="", encoding="utf-8") as fo:
        w = csv.DictWriter(fo, list(filas[0].keys()))
        w.writeheader()
        w.writerows(filas)
    resumen(res)


def resumen(res):
    f = lambda x, n=3: "nan" if x is None or not np.isfinite(x) else f"{x:+.{n}f}"  # noqa: E731
    L = ["S20c: controles limpios. Criterio b06c711 + enmienda 1 (antes de medir)", ""]
    for nombre, v in res["variantes"].items():
        L.append(f"== {nombre}")
        for p in PRUEBAS:
            r = v[p]
            s = (f"  {p:8s} unid {r['unidades_validas']:3d}/{r['cuadros']:3d} dias {r['dias_validos']} | S {f(r['S'])} K "
                 f"p_baja {r['p_baja']:.4f} p_alta {r['p_alta']:.4f} | E_orig {f(r['E_orig'])} (n {r['E_orig_n']}) | "
                 f"pos-base {f(r['x_menos_base_mediana'])} plac-base {f(r['placebo_menos_base_mediana'])} | "
                 f"nulo [{f(r['nulo_p05'])}, {f(r['nulo_p95'])}] | C {f(r['C_S'])} (n {r['C_n']}, p {r['C_p_baja']:.3f}) | "
                 f"AUC orig {r['AUC_orig']:.3f} limpio {r['AUC_limpio']:.3f} plac {r['AUC_placebo']:.3f} "
                 f"corr {r['AUC_corregido']:.3f}")
            if "poder" in r:
                s += f" | FA {r['falsa_alarma']:.3f} poder " + " ".join(f"{k}:{x:.2f}" for k, x in r["poder"].items())
            if "veredicto" in r:
                s += f" | p_holm {r['p_holm']:.4f} | {r['veredicto']}"
            L.append(s)
        L.append("")
    txt = "\n".join(L)
    open(os.path.join(RES, "s20c_resumen.txt"), "w", encoding="utf-8").write(txt)
    print(txt)


if __name__ == "__main__":
    modo = sys.argv[1] if len(sys.argv) > 1 else ""
    if modo == "seco":
        seco()
    elif modo == "medir":
        medir()
    else:
        print(__doc__)
