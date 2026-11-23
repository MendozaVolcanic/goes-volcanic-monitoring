r"""S20c: implementa criterio_2026-11-23.md (commit b06c711); DISENO v1, descartado por el ensayo en seco (ver enmienda_1). Controles limpios para las pruebas pareadas viejas.

Pregunta: con controles tomados antes de toda actividad (21-09 al 21-10), mismo minuto, mismos pixeles y misma regla
de pareo, y la temporada restada con dias de noviembre sin actividad (placebo), la BTD de la huella VOLCAT se aparta
de lo que dan los dias sin pluma? Si se aparta y con el control original no, el control viejo estaba contaminado.

Por que asi: se cambia una sola cosa respecto de las pruebas viejas (el pozo de controles), para que el resultado se
pueda atribuir a eso. La temporada se corrige con un placebo que pasa por el mismo procedimiento con la misma huella
y a la misma hora; el nulo permuta bloques de dia (todos los cuadros de un dia positivo se cambian por un dia placebo
vecino), porque los cuadros de un mismo dia no son independientes.

Modos: `seco` (ensayo en seco: falsa alarma, poder y cobertura; nunca lee BTD del dia positivo ni del control
original) y `medir` (todo). Insumos de solo lectura en D: (cubos y ACMF de H23 y H24, GFS, PNG de VOLCAT).
Uso: python -I s20c_medir.py seco|medir
"""
import csv
import json
import os
import sys
from datetime import datetime, timedelta

import numpy as np
from scipy.stats import rankdata

sys.stdout.reconfigure(encoding="utf-8")
AQUI = os.path.dirname(os.path.abspath(__file__))
OV = os.path.abspath(os.path.join(AQUI, "..", ".."))
RES = os.path.join(os.path.dirname(AQUI), "resultados")
sys.path.insert(0, os.path.join(OV, "h24_pulsos_reav", "scripts"))
sys.path.insert(0, os.path.join(OV, "h29_pluma_0811", "scripts"))
sys.path.insert(0, AQUI)
import h24_medir as H  # noqa: E402  (cargar, despejada, gfs_t, Planck, EXCLUIDOS)
import h29_comun as C29  # noqa: E402  (decodificador del PNG con el corrimiento de H14)
import s20c_pares as SP  # noqa: E402

# ---------- parametros del criterio ----------
T0 = H.T0                                   # 21-09-2026
NDIAS, NY, NX = H.NDIAS, H.NY, H.NX
NPIX = NY * NX
LIMPIO = list(range(0, 31))                 # 21-09 al 21-10
EXCL = {(datetime.strptime(s, "%Y-%m-%d") - T0).days for s in H.EXCLUIDOS}
PLACEBO = [d for d in range(31, NDIAS) if d not in EXCL]
TOL_K = 3.0
MIN_PX = 3
N_VEC, MIN_PLAC = 7, 4
N_NULO, N_FA, N_PODER = 2000, 500, 500
SEMILLA = 20261123
EPS = [0.05, 0.10, 0.15, 0.30]
BETA = 0.70
Z_TOPE = 4500.0
R_KM = 50.0
CRATER_PX = (42, 46)
UMBRAL_DIF = 0.10
STORE = r"D:\goes_notas\s20\s20c"
H3_HUE = r"D:\goes_notas\local_f3a7d295\h12_datos\extra\h3_meta\huellas_h3.npz"
B73_HUE = r"D:\goes_notas\local_f3a7d295\h12_datos\extra\b73_meta\huellas_b73.npz"
PRUEBAS = ["paso2", "H3", "beta73", "VAAC", "H13", "H11_H12"]
VARS = ["btd", "bt11", "dbtd", "dbt11"]
COLA = {"btd": "baja", "bt11": "baja", "dbtd": "dos", "dbt11": "dos"}


def dia_slot(dt):
    return (dt - T0).days, dt.hour * 6 + dt.minute // 10


def fecha(d):
    return f"{T0 + timedelta(days=d):%d-%m}"


def vecinos(D):
    """N(D): los 7 dias placebo mas cercanos en fecha a D (empates: el anterior), sin D."""
    c = [j for j in PLACEBO if j != D]
    return sorted(c, key=lambda j: (abs(j - D), j))[:N_VEC]


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
    d1 = binary_dilation(F, est, iterations=1)
    d5 = binary_dilation(F, est, iterations=5)
    return d5 & ~d1 & ~CRATER_BLOQUE & CERCA


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
        self.claro = H.despejada("chillan", acm)            # (NDIAS, 144)
        self.Ttope = H.gfs_t([Z_TOPE])[:, :, 0]             # (NDIAS, 144)

    def t(self, d, s):
        return d * 144 + s

    def campo(self, var, d, s, px, iny=None):
        """Valores de la variable en (d, s) sobre px; iny = eps pinta la capa en (d, s) (y no en s - 1)."""
        t = self.t(d, s)
        if iny is None:
            b11, bd = self.bt11[t, px].astype(float), self.btd[t, px].astype(float)
        else:
            eps = iny
            Tt = self.Ttope[d, s]
            e12 = 1 - (1 - eps) ** BETA
            I14 = (1 - eps) * self.r14[t, px].astype(float) + eps * H.rad_de_bt(Tt, self.co14)
            I15 = (1 - e12) * self.r15[t, px].astype(float) + e12 * H.rad_de_bt(Tt, self.co15)
            b11 = H.bt_de_rad(I14, self.co14)
            bd = b11 - H.bt_de_rad(I15, self.co15)
        if var == "btd":
            return bd
        if var == "bt11":
            return b11
        if t == 0:
            return np.full(len(px), np.nan)
        if var == "dbtd":
            return bd - self.btd[t - 1, px].astype(float)
        return b11 - self.bt11[t - 1, px].astype(float)


# ---------- motor ----------
class Motor:
    """Diferencias de un cuadro contra su control limpio, con cache de las medianas de pareo del pozo limpio."""

    def __init__(self, D, par="huella", gate=True):
        self.D, self.par, self.gate = D, par, gate
        self._cand = {}

    def candidatos(self, s, pxpar):
        k = (s, pxpar.tobytes())
        if k not in self._cand:
            out = []
            for d in LIMPIO:
                if self.gate and not self.D.claro[d, s]:
                    continue
                v = self.D.bt11[self.D.t(d, s), pxpar]
                if np.isfinite(v).sum() >= MIN_PX:
                    out.append((d, float(np.nanmedian(v))))
            self._cand[k] = out
        return self._cand[k]

    def control(self, x, s, F, R, iny=None):
        """Dia limpio elegido para (x, s) y la diferencia de pareo; None si no hay a <= 3 K."""
        pxpar = np.flatnonzero(R if self.par == "anillo" else F)
        if self.par == "anillo" or iny is None:
            v = self.D.bt11[self.D.t(x, s), pxpar].astype(float)
        else:
            v = self.D.campo("bt11", x, s, pxpar, iny=iny)
        if np.isfinite(v).sum() < MIN_PX:
            return None, np.nan
        mx = float(np.nanmedian(v))
        cand = self.candidatos(s, pxpar)
        if not cand:
            return None, np.nan
        d, m = min(cand, key=lambda c: abs(c[1] - mx))
        return (d, m - mx) if abs(m - mx) <= TOL_K else (None, m - mx)

    def delta(self, var, x, s, F, R, iny=None, pix=False):
        """Mediana sobre F de v(x, s) - v(c, s), c el control limpio. Con pix=True devuelve tambien los pixeles."""
        c, dif = self.control(x, s, F, R, iny=iny)
        if c is None:
            return (np.nan, None, None, None) if pix else np.nan
        px = np.flatnonzero(F)
        a = self.D.campo(var, x, s, px, iny=iny)
        b = self.D.campo(var, c, s, px)
        ok = np.isfinite(a) & np.isfinite(b)
        if ok.sum() < MIN_PX:
            return (np.nan, None, None, None) if pix else np.nan
        val = float(np.median(a[ok] - b[ok]))
        return (val, a[ok], b[ok], c) if pix else val


def auc(a, b):
    a = np.asarray(a, float)
    b = np.asarray(b, float)
    a, b = a[np.isfinite(a)], b[np.isfinite(b)]
    if not len(a) or not len(b):
        return float("nan")
    r = rankdata(np.concatenate([a, b]))
    return float((r[:len(a)].sum() - len(a) * (len(a) + 1) / 2) / (len(a) * len(b)))


# ---------- cuadros por prueba ----------
def cuadros(variante):
    """Lista por prueba de dicts {pos, ctrl, D, s, Dc, sc, F, R}. La huella sale del PNG (o la guardada en S3)."""
    idx = SP.indice_png()
    pares = SP.pares()
    h3g = dict(np.load(H3_HUE)) if variante == "S3" else None
    b7g = dict(np.load(B73_HUE)) if variante == "S3" else None
    cache = {}
    out = {p: [] for p in PRUEBAS}
    descartados = {p: 0 for p in PRUEBAS}
    for prueba, p, c in pares:
        F = None
        if variante == "S3" and prueba == "H3":
            k = f"{p:%Y%m%d_%H%M}"
            F = h3g[k].astype(bool) & CERCA & ~CRATER_BLOQUE if k in h3g else None
        elif variante == "S3" and prueba == "beta73":
            k = "h_" + f"{p:%Y%m%d_%H%M}"
            F = b7g[k].astype(bool) & CERCA & ~CRATER_BLOQUE if k in b7g else None
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
    # H11/H12: union de H3 y beta73, con prioridad H3
    vistos = {q["pos"] for q in out["H3"]}
    out["H11_H12"] = list(out["H3"]) + [q for q in out["beta73"] if q["pos"] not in vistos]
    return out, descartados


# ---------- tablas por cuadro ----------
def tablas(M, Q, var, seco, eps_list=()):
    """Para cada cuadro: delta en sus 7 vecinos placebo, delta inyectada en cada vecino por eps, y (si no es seco)
    delta del positivo, del control original (chequeo C) y la diferencia con el control original (E_orig)."""
    filas = []
    for q in Q:
        D, s, F, R = q["D"], q["s"], q["F"], q["R"]
        N = vecinos(D)
        f = {"q": q, "N": N, "plac": np.array([M.delta(var, j, s, F, R) for j in N])}
        f["iny"] = {e: np.array([M.delta(var, j, s, F, R, iny=e) for j in N]) for e in eps_list}
        c_pos, dif_pos = M.control(D, s, F, R)
        f["cubre"] = c_pos is not None
        f["dif_par"] = dif_pos
        if not seco:
            v, a, b, c = M.delta(var, D, s, F, R, pix=True)
            f["pos"], f["pos_a"], f["pos_b"], f["c_limpio"] = v, a, b, c
            px = np.flatnonzero(F)
            a0 = M.D.campo(var, D, s, px)
            b0 = M.D.campo(var, q["Dc"], q["sc"], px)
            ok = np.isfinite(a0) & np.isfinite(b0)
            f["orig"] = float(np.median(a0[ok] - b0[ok])) if ok.sum() >= MIN_PX else np.nan
            f["orig_a"], f["orig_b"] = a0[ok], b0[ok]
            # chequeo C: el control original en el lugar del positivo
            Nc = [j for j in vecinos(q["Dc"]) if j != q["Dc"]]
            f["Nc"] = Nc
            f["C"] = M.delta(var, q["Dc"], q["sc"], F, R)
            f["C_plac"] = np.array([M.delta(var, j, q["sc"], F, R) for j in Nc])
            # pixeles de placebo para el AUC
            pa, pb = [], []
            for j in N:
                vv, aa, bb, _ = M.delta(var, j, s, F, R, pix=True)
                if aa is not None:
                    pa.append(aa)
                    pb.append(bb)
            f["plac_a"] = np.concatenate(pa) if pa else np.array([])
            f["plac_b"] = np.concatenate(pb) if pb else np.array([])
        filas.append(f)
    return filas


def med_ok(v, n_min):
    v = v[np.isfinite(v)]
    return float(np.median(v)) if len(v) >= n_min else np.nan


def estadistico_real(filas, clave="pos", plac="plac"):
    d = []
    for f in filas:
        x = f.get(clave, np.nan)
        m = med_ok(f[plac], MIN_PLAC)
        if np.isfinite(x) and np.isfinite(m):
            d.append(x - m)
    return (float(np.median(d)) if d else np.nan), len(d), d


def replicas(filas, n, rng, iny=None, dia="D", plac="plac"):
    """S de n replicas del nulo de bloques de dia. iny = eps usa la delta inyectada del dia sorteado."""
    dias = sorted({f["q"][dia] for f in filas})
    vec = {}
    for f in filas:
        vec.setdefault(f["q"][dia], f["N"] if plac == "plac" else f["Nc"])
    S = np.full(n, np.nan)
    for r in range(n):
        elegido = {D: rng.integers(len(vec[D])) for D in dias}
        d = []
        for f in filas:
            k = elegido[f["q"][dia]]
            arr = f[plac]
            x = (f["iny"][iny] if iny is not None else arr)[k]
            otros = np.delete(arr, k)
            m = med_ok(otros, MIN_PLAC - 1)
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
    idx = [i for i, p in enumerate(ps) if np.isfinite(p)]
    orden = sorted(idx, key=lambda i: ps[i])
    out = [np.nan] * len(ps)
    acum = 0.0
    for r, i in enumerate(orden):
        acum = max(acum, min(1.0, (len(orden) - r) * ps[i]))
        out[i] = acum
    return out


# ---------- ensayo en seco ----------
def seco():
    Dt = Datos()
    QQ, desc = cuadros("principal")
    res = {"criterio": "criterio_2026-11-23.md (commit b06c711); DISENO v1, descartado por el ensayo en seco (ver enmienda_1)", "placebo": [fecha(d) for d in PLACEBO],
           "limpio": f"{fecha(LIMPIO[0])} a {fecha(LIMPIO[-1])}", "descartados_huella<3px": desc, "pruebas": {}}
    for gate, nombre in ((True, "principal"), (False, "S2_sin_ACMF")):
        M = Motor(Dt, par="huella", gate=gate)
        for prueba in PRUEBAS:
            Q = QQ[prueba]
            filas = tablas(M, Q, "btd", seco=True, eps_list=EPS)
            rng = np.random.default_rng(SEMILLA)
            nulo = replicas(filas, N_NULO, rng)
            fa = []
            for r in range(N_FA):
                otros = np.delete(nulo, r)
                fa.append(p_colas(nulo[r], otros)[0] <= 0.05)
            poder = {}
            for e in EPS:
                Si = replicas(filas, N_PODER, np.random.default_rng(SEMILLA + int(e * 1000)), iny=e)
                poder[str(e)] = float(np.mean([p_colas(x, nulo)[0] <= 0.05 for x in Si if np.isfinite(x)]))
            nplac = [int(np.isfinite(f["plac"]).sum()) for f in filas]
            cubre = [f["cubre"] and n >= MIN_PLAC for f, n in zip(filas, nplac)]
            d = {"cuadros": len(Q), "dias_positivos": sorted({fecha(q["D"]) for q in Q}),
                 "cobertura": float(np.mean(cubre)) if cubre else 0.0,
                 "cubiertos": int(np.sum(cubre)),
                 "placebos_validos_mediana": float(np.median(nplac)) if nplac else 0.0,
                 "falsa_alarma": float(np.mean(fa)), "poder": poder,
                 "nulo_mediana": float(np.nanmedian(nulo)), "nulo_p05": float(np.nanpercentile(nulo, 5)),
                 "nulo_p95": float(np.nanpercentile(nulo, 95))}
            res["pruebas"].setdefault(prueba, {})[nombre] = d
            print(nombre, prueba, json.dumps({k: v for k, v in d.items() if k != "dias_positivos"}), flush=True)
    # decision de fallback y validez, por prueba
    for prueba, d in res["pruebas"].items():
        p = d["principal"]
        usa = "principal" if p["cobertura"] >= 0.5 else "S2_sin_ACMF"
        d["medicion_principal"] = usa
        d["valida"] = d[usa]["falsa_alarma"] <= 0.10
    os.makedirs(RES, exist_ok=True)
    json.dump(res, open(os.path.join(RES, "seco.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print({k: (v["medicion_principal"], v["valida"]) for k, v in res["pruebas"].items()})


# ---------- medicion ----------
def veredicto(S, E, p_baja, p_alta, poder):
    if not np.isfinite(S):
        return "SIN DATO"
    if p_baja <= 0.05:
        return "CONTROL CONTAMINADO" if S <= E - UMBRAL_DIF else "SEÑAL QUE YA ESTABA"
    if p_alta <= 0.05 and S > 0:
        return "SIGNO CONTRARIO"
    return "NO ERA ESO" if poder >= 0.80 else "SIN PODER"


def medir_variante(Dt, variante, var, seco_res, eps_list=(), filas_csv=None):
    par = "anillo" if variante == "S1" else "huella"
    QQ, desc = cuadros(variante if variante in ("S3", "S4") else "principal")
    out = {}
    for prueba in PRUEBAS:
        usa = seco_res["pruebas"][prueba]["medicion_principal"]
        gate = not (variante == "S2" or (variante != "S2" and usa == "S2_sin_ACMF"))
        M = Motor(Dt, par=par, gate=gate)
        Q = QQ[prueba]
        filas = tablas(M, Q, var, seco=False, eps_list=eps_list)
        S, n, d = estadistico_real(filas)
        nulo = replicas(filas, N_NULO, np.random.default_rng(SEMILLA))
        pb, pa = p_colas(S, nulo)
        E = med_ok(np.array([f["orig"] for f in filas]), 1)
        # chequeo C, con su propio nulo
        filasC = [f for f in filas if f["q"]["Dc"] in EXCL]
        SC, nC, _ = estadistico_real(filasC, clave="C", plac="C_plac")
        nuloC = replicas(filasC, N_NULO, np.random.default_rng(SEMILLA + 7), dia="Dc", plac="C_plac") if filasC else np.array([])
        pCb, pCa = p_colas(SC, nuloC)
        cat = lambda k: np.concatenate([f[k] for f in filas if f.get(k) is not None and len(f[k])]) if filas else np.array([])  # noqa: E731
        A_orig = auc(cat("orig_a"), cat("orig_b"))
        A_lim = auc(cat("pos_a"), cat("pos_b"))
        A_pla = auc(cat("plac_a"), cat("plac_b"))
        r = {"cuadros": len(Q), "validos": n, "S": S, "p_baja": pb, "p_alta": pa, "E_orig": E,
             "nulo_p05": float(np.nanpercentile(nulo, 5)), "nulo_p95": float(np.nanpercentile(nulo, 95)),
             "C_S": SC, "C_n": nC, "C_p_baja": pCb, "C_p_alta": pCa,
             "AUC_orig": A_orig, "AUC_limpio": A_lim, "AUC_placebo": A_pla,
             "AUC_corregido": 0.5 + A_lim - A_pla if np.isfinite(A_lim) and np.isfinite(A_pla) else np.nan,
             "control_ACMF": gate, "pareo": par,
             "dias_control_limpio": sorted({fecha(f["c_limpio"]) for f in filas if f.get("c_limpio") is not None})}
        if eps_list:
            r["poder"] = {}
            for e in eps_list:
                Si = replicas(filas, N_PODER, np.random.default_rng(SEMILLA + int(e * 1000)), iny=e)
                r["poder"][str(e)] = float(np.mean([p_colas(x, nulo)[0] <= 0.05 for x in Si if np.isfinite(x)]))
        out[prueba] = r
        if filas_csv is not None:
            for f in filas:
                q = f["q"]
                filas_csv.append({"variante": variante, "var": var, "prueba": prueba,
                                  "pos": f"{q['pos']:%Y-%m-%d %H:%M}", "ctrl_orig": f"{q['ctrl']:%Y-%m-%d %H:%M}",
                                  "npx": int(q["F"].sum()),
                                  "ctrl_limpio": fecha(f["c_limpio"]) if f.get("c_limpio") is not None else "",
                                  "dif_pareo_K": round(f["dif_par"], 3) if np.isfinite(f["dif_par"]) else "",
                                  "delta_pos": f["pos"], "placebo_mediana": med_ok(f["plac"], MIN_PLAC),
                                  "placebos_validos": int(np.isfinite(f["plac"]).sum()), "delta_orig": f["orig"],
                                  "delta_ctrl_orig_C": f["C"]})
        print(variante, var, prueba, json.dumps({k: (round(v, 4) if isinstance(v, float) else v)
                                                 for k, v in r.items() if k != "dias_control_limpio"}), flush=True)
    return out, desc


def medir():
    seco_res = json.load(open(os.path.join(RES, "seco.json"), encoding="utf-8"))
    Dt = Datos()
    res = {"criterio": "criterio_2026-11-23.md (commit b06c711); DISENO v1, descartado por el ensayo en seco (ver enmienda_1)", "variantes": {}}
    filas_csv = []
    principal, desc = medir_variante(Dt, "principal", "btd", seco_res, eps_list=EPS, filas_csv=filas_csv)
    ps = [principal[p]["p_baja"] for p in PRUEBAS]
    for p, ph in zip(PRUEBAS, holm(ps)):
        r = principal[p]
        r["p_holm"] = ph
        r["veredicto"] = veredicto(r["S"], r["E_orig"], r["p_baja"], r["p_alta"], r["poder"]["0.1"])
        if not seco_res["pruebas"][p]["valida"]:
            r["veredicto"] = "INVÁLIDA"
    res["variantes"]["principal_btd"] = principal
    res["descartados_huella<3px"] = desc
    for var in ("bt11", "dbtd", "dbt11"):
        res["variantes"][f"S5_{var}"], _ = medir_variante(Dt, "principal", var, seco_res, filas_csv=filas_csv)
    res["variantes"]["S1_anillo_btd"], _ = medir_variante(Dt, "S1", "btd", seco_res, filas_csv=filas_csv)
    res["variantes"]["S1_anillo_bt11"], _ = medir_variante(Dt, "S1", "bt11", seco_res, filas_csv=filas_csv)
    res["variantes"]["S2_sin_ACMF_btd"], _ = medir_variante(Dt, "S2", "btd", seco_res, filas_csv=filas_csv)
    res["variantes"]["S3_huella_guardada_btd"], _ = medir_variante(Dt, "S3", "btd", seco_res, filas_csv=filas_csv)
    res["variantes"]["S4_con_crater_btd"], _ = medir_variante(Dt, "S4", "btd", seco_res, filas_csv=filas_csv)
    os.makedirs(RES, exist_ok=True)
    json.dump(res, open(os.path.join(RES, "s20c_resultado.json"), "w", encoding="utf-8"), indent=1,
              ensure_ascii=False, default=float)
    with open(os.path.join(RES, "s20c_por_cuadro.csv"), "w", newline="", encoding="utf-8") as fo:
        w = csv.DictWriter(fo, list(filas_csv[0].keys()))
        w.writeheader()
        w.writerows(filas_csv)
    resumen(res)


def resumen(res):
    L = ["S20c: controles limpios. Criterio: criterio_2026-11-23.md (commit b06c711); DISENO v1, descartado por el ensayo en seco (ver enmienda_1)", ""]
    for nombre, v in res["variantes"].items():
        L.append(f"== {nombre}")
        for p in PRUEBAS:
            r = v[p]
            s = (f"  {p:8s} cuadros {r['cuadros']:3d} validos {r['validos']:3d} | S {r['S']:+.3f} K p_baja {r['p_baja']:.4f} "
                 f"p_alta {r['p_alta']:.4f} | E_orig {r['E_orig']:+.3f} | nulo [{r['nulo_p05']:+.3f}, {r['nulo_p95']:+.3f}] | "
                 f"C {r['C_S']:+.3f} (n {r['C_n']}, p {r['C_p_baja']:.3f}) | AUC orig {r['AUC_orig']:.3f} limpio "
                 f"{r['AUC_limpio']:.3f} placebo {r['AUC_placebo']:.3f} corr {r['AUC_corregido']:.3f}")
            if "poder" in r:
                s += " | poder " + " ".join(f"{k}:{x:.2f}" for k, x in r["poder"].items())
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
