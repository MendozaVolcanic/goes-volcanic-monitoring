r"""S22a: detector propio por sectores con persistencia, frente a lo que VOLCAT mostro de Nevados de Chillan.
Implementa criterio_2026-11-24.md (commit 7c59431, empujado antes de medir).

Por que asi: la firma de la pluma en 11 - 12 um es debil (S20b ~ -1 K en un pixel, H29 -0,37 K lejos del crater) y
buscar el pixel mas bajo no alcanza (S21e). La cola baja de un sector (8 pixeles, el tamano de un objeto de VOLCAT)
promedia ruido; compararla con los otros sectores del mismo cuadro evita la linea base por pixel (no hay tardes
despejadas); exigir dos cuadros seguidos imita el seguimiento con que VOLCAT sostiene sus objetos.

Uso: python -I s22a_medir.py pruebas | seco | poder | medir | figura
  seco y poder solo leen dias placebo; medir exige resultados/seco.json y resultados/poder.json.
"""
import csv
import json
import os
import sys
import time
import warnings
from datetime import datetime, timedelta

import numpy as np

sys.stdout.reconfigure(encoding="utf-8")
warnings.simplefilter("ignore", RuntimeWarning)
AQUI = os.path.dirname(os.path.abspath(__file__))
OV = os.path.abspath(os.path.join(AQUI, "..", ".."))
RES = os.path.join(os.path.dirname(AQUI), "resultados")
FIG = os.path.join(os.path.dirname(AQUI), "figuras")
CACHE = r"D:\goes_notas\s22\s22a"
sys.path.insert(0, os.path.join(OV, "h24_pulsos_reav", "scripts"))
sys.path.insert(0, os.path.join(OV, "h29_pluma_0811", "scripts"))
import h24_medir as H24  # noqa: E402  (cargar, despejada = E1)
import h29_comun as C29  # noqa: E402  (grilla, cota, crater, Planck)

# ---------- parametros del criterio (§2, §3) ----------
T0, NDIAS, NY, NX = H24.T0, H24.NDIAS, H24.NY, H24.NX
CRATER_PX = (42, 46)
R_IN, R_OUT, R_CTRL = 4.0, 40.0, 45.0
PAR_K, COTA_M, MIN_PAR = 0.5, 300.0, 20
NSEC, NCOLA, MIN_SEC = 12, 8, 9
W_U, W_U2, MIN_POOL, MIN_DIAS, MAX_FRAC_DIA, PCT_U = 6, 12, 60, 6, 0.25, 5.0
FA_MAX = 0.05
N_POD, SEMILLA, R_INY, N_INY = 200, 0, 20.0, 8
FIRMAS = (0.33, 0.97)
R_MIN, REP_MIN = 0.50, 0.75
GAP_EP, MARGEN_EP = 6, 3            # 60 min entre cuadros del episodio; +-30 min de margen

PLACEBO_TXT = ["2026-10-23", "2026-10-26", "2026-10-31", "2026-11-01", "2026-11-02", "2026-11-03", "2026-11-04",
               "2026-11-05", "2026-11-09", "2026-11-15", "2026-11-17", "2026-11-19", "2026-11-20", "2026-11-21"]
FRAMES_CALOR = os.path.join(OV, "calor_rayos", "resultados", "frames_calor.csv")
VOLCAT_EV_CSV = r"D:\goes_notas\s19\h28\resultados\prueba\eventos_chillan_cuadros.csv"
NACIMIENTOS = [("2026-11-13", "19:00"), ("2026-11-14", "12:40"), ("2026-11-14", "16:30"), ("2026-11-18", "10:10")]
VERDAD_FINA = [("2026-10-25", "14:20", (43, 44)), ("2026-10-25", "14:30", (43, 44)),
               ("2026-11-08", "14:40", (44, 46)), ("2026-11-08", "14:50", (44, 46))]
DIAS_EXTRA = ["2026-11-13", "2026-11-16", "2026-11-18"]       # archivos de evento sin P (informativo)


def dia_idx(s):
    return (datetime.strptime(s, "%Y-%m-%d") - T0).days


def fecha(d):
    return f"{T0 + timedelta(days=d):%Y-%m-%d}"


def slot(hhmm):
    h, m = hhmm.split(":")
    return int(h) * 6 + int(m) // 10


def hhmm(s):
    return f"{s // 6:02d}:{s % 6 * 10:02d}"


def dslot(a, b):
    x = abs(a - b) % 144
    return min(x, 144 - x)


PLACEBO = [dia_idx(s) for s in PLACEBO_TXT]

# ---------- geometria (§2) ----------
LAT, LON = C29.LAT, C29.LON
DIST = C29.DIST
_x = (LON - C29.CRATER[1]) * 111.32 * np.cos(np.radians(C29.CRATER[0]))   # km al este (solo para acimut y rayo)
_y = (LAT - C29.CRATER[0]) * 110.57                                       # km al norte
AZ = (np.degrees(np.arctan2(_x, _y)) + 360.0) % 360.0
BLOQUE = np.zeros((NY, NX), bool)
BLOQUE[CRATER_PX[0] - 1:CRATER_PX[0] + 2, CRATER_PX[1] - 1:CRATER_PX[1] + 2] = True
AMASK = (DIST >= R_IN) & (DIST <= R_OUT) & ~BLOQUE
AP = np.flatnonzero(AMASK.ravel())
NA = len(AP)
SEC = (AZ.ravel()[AP] // 30).astype(int) % NSEC
NPS = np.bincount(SEC, minlength=NSEC)
CTRL = np.flatnonzero((DIST > R_CTRL).ravel())
ZDEM = C29.ZDEM.ravel()
# control de cada pixel del anillo con su cota (fijo); el pareo por BT11 se hace en cada cuadro
CTRL_COTA = [CTRL[np.abs(ZDEM[CTRL] - ZDEM[p]) <= COTA_M] for p in AP]
AX, AY, AD = _x.ravel()[AP], _y.ravel()[AP], DIST.ravel()[AP]


def m1_cuadro(bt, bd):
    """M1 de los pixeles del anillo en un cuadro (bt, bd: BT11 y BTD planos)."""
    out = np.full(NA, np.nan, np.float32)
    okb = np.isfinite(bt) & np.isfinite(bd)
    for i, p in enumerate(AP):
        if not okb[p]:
            continue
        c = CTRL_COTA[i]
        c = c[okb[c]]
        sel = c[np.abs(bt[c] - bt[p]) <= PAR_K]
        if len(sel) >= MIN_PAR:
            out[i] = bd[p] - np.median(bd[sel])
    return out


def estadistico(m1):
    """(S, k*, n sectores validos). S NaN si hay menos de 9 sectores validos."""
    Q = np.full(NSEC, np.nan)
    for k in range(NSEC):
        v = m1[SEC == k]
        v = v[np.isfinite(v)]
        if len(v) >= 0.5 * NPS[k] and len(v) >= NCOLA:
            Q[k] = np.sort(v)[:NCOLA].mean()
    nv = int(np.isfinite(Q).sum())
    if nv < MIN_SEC:
        return np.nan, -1, nv
    k = int(np.nanargmin(Q))
    return float(Q[k] - np.nanmedian(Q)), k, nv


def vecinos(a, b):
    x = abs(a - b) % NSEC
    return min(x, NSEC - x) <= 1


# ---------- datos y cache ----------
_BT = {}


def cargar_bt():
    if not _BT:
        t = time.time()
        r14, r15, acm, co14, co15 = H24.cargar()
        _BT["E1"] = H24.despejada("chillan", acm)
        _BT["bt11"] = C29.bt_de_rad(r14.astype("float64"), co14).astype("float32")
        del r14
        _BT["btd"] = (_BT["bt11"] - C29.bt_de_rad(r15.astype("float64"), co15)).astype("float32")
        del r15
        print(f"cubos cargados en {time.time() - t:.0f} s")
    return _BT


def m1_dias(dias, nombre):
    """M1 (dias, 144, NA) de una lista de dias, con cache en D: (derivado de los cubos, no es dato de SSEC)."""
    os.makedirs(CACHE, exist_ok=True)
    fn = os.path.join(CACHE, f"m1_{nombre}.npz")
    if os.path.exists(fn):
        z = np.load(fn)
        if list(z["dias"]) == list(dias):
            return z["m1"]
    B = cargar_bt()
    out = np.full((len(dias), 144, NA), np.nan, np.float32)
    t = time.time()
    for j, d in enumerate(dias):
        for s in range(144):
            out[j, s] = m1_cuadro(B["bt11"][d, s], B["btd"][d, s])
        print(f"  M1 {fecha(d)} ({j + 1}/{len(dias)}) {time.time() - t:.0f} s", flush=True)
    np.savez_compressed(fn, m1=out, dias=np.array(dias))
    return out


def tabla_S(m1):
    S = np.full(m1.shape[:2], np.nan)
    K = np.full(m1.shape[:2], -1, int)
    for j in range(m1.shape[0]):
        for s in range(144):
            S[j, s], K[j, s], _ = estadistico(m1[j, s])
    return S, K


# ---------- umbral (§3) ----------
def umbrales(Splac, excl=None):
    """U por hora (144) con los placebo menos el dia `excl` (indice en PLACEBO). None si la hora no cumple."""
    U, info = [None] * 144, [None] * 144
    for s in range(144):
        for w in (W_U, W_U2):
            vals, dias = [], []
            for j in range(len(PLACEBO)):
                if j == excl:
                    continue
                for x in range(144):
                    if dslot(x, s) <= w and np.isfinite(Splac[j, x]):
                        vals.append(Splac[j, x])
                        dias.append(j)
            n = len(vals)
            if n == 0:
                continue
            cnt = np.bincount(dias, minlength=len(PLACEBO))
            if n >= MIN_POOL and (cnt > 0).sum() >= MIN_DIAS and cnt.max() / n <= MAX_FRAC_DIA:
                U[s] = float(np.percentile(vals, PCT_U))
                info[s] = {"ventana_min": 10 * w, "n": n, "dias": int((cnt > 0).sum()),
                           "frac_max_dia": round(float(cnt.max() / n), 3)}
                break
    return U, info


def disparos(S, K, U):
    """F (dias, 144) para una serie de dias consecutivos en el calendario o no: el cuadro anterior de s = 0 es el
    ultimo del dia anterior en la misma tabla solo si ese dia es el anterior en el calendario (prev[j])."""
    F = np.zeros(S.shape, bool)
    ev = np.zeros(S.shape, bool)
    for j in range(S.shape[0]):
        for s in range(144):
            if U[s] is None or not np.isfinite(S[j, s]):
                continue
            ev[j, s] = True
            if s == 0:
                continue                      # sin cuadro anterior en la misma serie: no dispara (conservador)
            if U[s - 1] is None or not np.isfinite(S[j, s - 1]):
                continue
            F[j, s] = S[j, s] <= U[s] and S[j, s - 1] <= U[s - 1] and vecinos(K[j, s], K[j, s - 1])
    return F, ev


def disparos_continuos(S, K, U, dias):
    """Como disparos(), pero enlaza s = 0 con el dia anterior si esta en la tabla."""
    F, ev = disparos(S, K, U)
    pos = {d: j for j, d in enumerate(dias)}
    for j, d in enumerate(dias):
        jp = pos.get(d - 1)
        if jp is None or not ev[j, 0] or U[143] is None or not np.isfinite(S[jp, 143]):
            continue
        F[j, 0] = S[j, 0] <= U[0] and S[jp, 143] <= U[143] and vecinos(K[j, 0], K[jp, 143])
    return F, ev


# ---------- pruebas ----------
def pruebas(con_datos=False):
    assert NA > 700 and (AD >= R_IN).all() and (AD <= R_OUT).all() and not BLOQUE.ravel()[AP].any()
    assert not np.intersect1d(AP, CTRL).size and (DIST.ravel()[CTRL] > R_CTRL).all()
    assert (NPS >= 50).all(), NPS
    assert len(PLACEBO) == 14 and not (set(PLACEBO) & {dia_idx(s) for s in H24.EXCLUIDOS})
    # acimut: un pixel al norte del crater da ~0 grados, uno al este ~90
    assert AZ[CRATER_PX[0] - 10, CRATER_PX[1]] < 10 or AZ[CRATER_PX[0] - 10, CRATER_PX[1]] > 350
    assert 80 < AZ[CRATER_PX[0], CRATER_PX[1] + 10] < 100
    assert vecinos(0, 11) and vecinos(3, 4) and not vecinos(0, 2) and dslot(2, 140) == 6
    # estadistico: un sector con 8 pixeles bajados en a baja Q en a exacto si esos 8 eran la cola
    rng = np.random.default_rng(3)
    m = rng.normal(0, 0.2, NA).astype(np.float32)
    S0, k0, nv = estadistico(m)
    assert nv == NSEC
    k = 5
    idx = np.flatnonzero(SEC == k)[:NCOLA]
    m2 = m.copy()
    m2[idx] -= 3.0
    S2, k2, _ = estadistico(m2)
    assert k2 == k and S2 < S0 - 1.0
    # sector con menos de la mitad de pixeles validos queda fuera; con 3 sectores fuera, S vacio (9 validos minimo)
    m3 = m.copy()
    for kk in (0, 1, 2, 3):
        m3[SEC == kk] = np.nan
    assert np.isnan(estadistico(m3)[0])
    # persistencia: dispara solo con dos cuadros seguidos bajo U y sectores vecinos
    S = np.array([[0.0, -2.0, -2.0, -2.0] + [0.0] * 140])
    K = np.array([[0, 3, 4, 9] + [0] * 140])
    F, ev = disparos(S, K, [-1.0] * 144)
    assert F[0, 2] and not F[0, 1] and not F[0, 3] and ev[0, 1]
    # rayo: los 8 pixeles del rayo a 90 grados estan al este y a <= 20 km
    sel = pixeles_rayo(90.0)
    assert len(sel) == N_INY and (AD[sel] <= R_INY).all() and (np.abs(AZ.ravel()[AP][sel] - 90) < 45).all()
    n = 9
    if con_datos:
        B = cargar_bt()
        # M1 vectorizado contra la definicion directa en pixeles al azar
        comp, fin = 0, 0
        for d, s in [(40, 30), (45, 100), (50, 80)]:
            bt, bd = B["bt11"][d, s], B["btd"][d, s]
            mm = m1_cuadro(bt, bd)
            for i in rng.choice(NA, 20, replace=False):
                p = AP[i]
                ok = np.isfinite(bt) & np.isfinite(bd)
                sel = ok.copy()
                sel[:] = False
                sel[CTRL] = True
                sel &= ok & (np.abs(ZDEM - ZDEM[p]) <= COTA_M) & (np.abs(bt - bt[p]) <= PAR_K)
                ref = bd[p] - np.median(bd[sel]) if (sel.sum() >= MIN_PAR and ok[p]) else np.nan
                assert (np.isnan(ref) and np.isnan(mm[i])) or abs(ref - mm[i]) < 1e-5, (d, s, i, ref, mm[i])
                comp += 1
                fin += int(np.isfinite(ref))
        assert fin > comp // 2
        print(f"M1 = definicion directa en {comp} pixeles-cuadro ({fin} con valor)")
        n += 1
    print(f"pruebas OK ({n} de {n}); anillo {NA} pixeles, control {len(CTRL)}, pixeles por sector {NPS.tolist()}")


def pixeles_rayo(az):
    """Los 8 pixeles del anillo a <= 20 km mas cercanos al rayo de acimut `az` desde el crater (§3, poder)."""
    ux, uy = np.sin(np.radians(az)), np.cos(np.radians(az))
    t = AX * ux + AY * uy
    perp = np.where(t >= 0, np.abs(AX * uy - AY * ux), np.hypot(AX, AY))
    perp = np.where(AD <= R_INY, perp, np.inf)
    return np.argsort(perp)[:N_INY]


# ---------- ensayo en seco (§3) ----------
def seco():
    m1 = m1_dias(PLACEBO, "placebo")
    S, K = tabla_S(m1)
    E1 = cargar_bt()["E1"]
    np.savez_compressed(os.path.join(CACHE, "S_placebo.npz"), S=S, K=K)
    por_dia, filas = [], []
    for j, d in enumerate(PLACEBO):
        U, _ = umbrales(S, excl=j)
        F, ev = disparos(S[j:j + 1], K[j:j + 1], U)
        F, ev = F[0], ev[0]
        n = int(ev.sum())
        por_dia.append({"dia": fecha(d), "evaluados": n, "disparos": int(F.sum()),
                        "fa": (float(F.sum() / n) if n else None)})
        for s in range(144):
            if ev[s]:
                filas.append((s // 18, bool(E1[d, s]), bool(F[s])))
    fas = [x["fa"] for x in por_dia if x["fa"] is not None]
    fa = float(np.mean(fas))
    por_hora = {}
    for b in range(8):
        v = [f for h, _, f in filas if h == b]
        por_hora[f"{3 * b:02d}-{3 * b + 2:02d} UTC"] = {"n": len(v), "fa": (float(np.mean(v)) if v else None)}
    por_e1 = {}
    for e in (True, False):
        v = [f for _, ee, f in filas if ee == e]
        por_e1["despejado" if e else "nublado"] = {"n": len(v), "fa": (float(np.mean(v)) if v else None)}
    U, info = umbrales(S)
    sin_u = [hhmm(s) for s in range(144) if U[s] is None]
    out = {"fa_media": fa, "fa_max": FA_MAX, "aprobado": fa <= FA_MAX, "por_dia": por_dia, "por_hora": por_hora,
           "por_E1": por_e1, "horas_sin_umbral": sin_u,
           "U_por_hora": {hhmm(s): (None if U[s] is None else round(U[s], 4)) for s in range(144)},
           "U_info": {hhmm(s): info[s] for s in range(144)},
           "S_placebo_resumen": {"n": int(np.isfinite(S).sum()), "p5": float(np.nanpercentile(S, 5)),
                                 "mediana": float(np.nanmedian(S))}}
    os.makedirs(RES, exist_ok=True)
    json.dump(out, open(os.path.join(RES, "seco.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps({k: out[k] for k in ("fa_media", "aprobado", "por_hora", "por_E1", "horas_sin_umbral")},
                     ensure_ascii=False, indent=1))
    for x in por_dia:
        print(x)


# ---------- poder (§3) ----------
def poder():
    m1 = m1_dias(PLACEBO, "placebo")
    S, K = tabla_S(m1)
    Uex = [umbrales(S, excl=j)[0] for j in range(len(PLACEBO))]
    pares = [(j, s) for j in range(len(PLACEBO)) for s in range(1, 144)
             if Uex[j][s] is not None and Uex[j][s - 1] is not None and np.isfinite(S[j, s]) and np.isfinite(S[j, s - 1])]
    rng = np.random.default_rng(SEMILLA)
    out = {"pares_disponibles": len(pares)}
    elegidos = rng.choice(len(pares), N_POD, replace=len(pares) < N_POD)
    azs = rng.uniform(0, 360, N_POD)
    for a in FIRMAS:
        hits = 0
        for e, az in zip(elegidos, azs):
            j, s = pares[e]
            sel = pixeles_rayo(az)
            ksec = int(az // 30) % NSEC
            res = []
            for x in (s - 1, s):
                mm = m1[j, x].copy()
                mm[sel] -= a                 # M1 baja en a exacto: el control esta a > 45 km, el rayo a <= 20 km
                res.append(estadistico(mm))
            (S1, k1, _), (S2, k2, _) = res
            U = Uex[j]
            if (np.isfinite(S1) and np.isfinite(S2) and S1 <= U[s - 1] and S2 <= U[s] and vecinos(k1, k2)
                    and vecinos(k2, ksec)):
                hits += 1
        out[f"{a:.2f}"] = hits / N_POD
        print(f"poder a {a:.2f} K: {hits / N_POD:.3f}")
    json.dump(out, open(os.path.join(RES, "poder.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)


# ---------- lo que mostro VOLCAT ----------
def cuadros_P():
    P = {}
    with open(FRAMES_CALOR, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["clase"] == "P":
                d, h = r["dt"][:10], r["dt"][11:16]
                P.setdefault(d, []).append(slot(h))
    return {d: sorted(v) for d, v in P.items()}


def clases_por_cuadro():
    c = {}
    with open(FRAMES_CALOR, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            c[(r["dt"][:10], slot(r["dt"][11:16]))] = r["clase"]
    return c


def episodios(slots):
    eps, cur = [], [slots[0]]
    for x in slots[1:]:
        if x - cur[-1] <= GAP_EP:
            cur.append(x)
        else:
            eps.append(cur)
            cur = [x]
    eps.append(cur)
    return eps


def alcanzado(F, ev, j, s):
    """(evaluable, alcanzado) de un cuadro P en (j, s): evaluable si el cuadro tiene S y umbral."""
    if not ev[j, s]:
        return False, False
    return True, bool(F[j, max(0, s - 1):min(144, s + 2)].any())


# ---------- medir (§4, §5, §6) ----------
def medir():
    seco_ = json.load(open(os.path.join(RES, "seco.json"), encoding="utf-8"))
    pod = json.load(open(os.path.join(RES, "poder.json"), encoding="utf-8"))
    P = cuadros_P()
    dias_v = sorted(P)
    dias_act = sorted({dia_idx(d) for d in dias_v + DIAS_EXTRA} | {dia_idx(d) - 1 for d in dias_v + DIAS_EXTRA})
    dias_act = [d for d in dias_act if d not in PLACEBO]
    m1p = m1_dias(PLACEBO, "placebo")
    Sp, Kp = tabla_S(m1p)
    m1a = m1_dias(dias_act, "actividad")
    Sa, Ka = tabla_S(m1a)
    np.savez_compressed(os.path.join(CACHE, "S_actividad.npz"), S=Sa, K=Ka, dias=np.array(dias_act))
    E1 = cargar_bt()["E1"]
    U, _ = umbrales(Sp)
    Fa, eva = disparos_continuos(Sa, Ka, U, dias_act)
    pos = {d: j for j, d in enumerate(dias_act)}

    # recuerdo por cuadro y por episodio
    por_dia, n_ev, n_hit, eps_tot, eps_hit = [], 0, 0, 0, 0
    detalle_P = []
    for d in dias_v:
        j = pos[dia_idx(d)]
        e_d = h_d = 0
        for s in P[d]:
            e, h = alcanzado(Fa, eva, j, s)
            e_d += e
            h_d += h
            detalle_P.append({"dia": d, "hora": hhmm(s), "evaluable": e, "alcanzado": h,
                              "E1": bool(E1[dia_idx(d), s]), "S": _r(Sa[j, s]), "U": _r(U[s]), "k": int(Ka[j, s])})
        eps = episodios(P[d])
        eh = 0
        for ep in eps:
            a, b = max(0, ep[0] - MARGEN_EP), min(143, ep[-1] + MARGEN_EP)
            eh += bool(Fa[j, a:b + 1].any())
        eps_tot += len(eps)
        eps_hit += eh
        n_ev += e_d
        n_hit += h_d
        por_dia.append({"dia": d, "P": len(P[d]), "evaluables": e_d, "alcanzados": h_d,
                        "R": (h_d / e_d if e_d else None), "episodios": len(eps), "episodios_alcanzados": eh})
    R = n_hit / n_ev if n_ev else float("nan")
    R_ep = eps_hit / eps_tot

    # nulo: las mismas horas trasladadas a cada placebo (U sin ese dia)
    nulo, nulo_dia = [], {d: [] for d in dias_v}
    for jp in range(len(PLACEBO)):
        Uj, _ = umbrales(Sp, excl=jp)
        Fp, evp = disparos(Sp, Kp, Uj)
        e_t = h_t = 0
        for d in dias_v:
            e_d = h_d = 0
            for s in P[d]:
                e, h = alcanzado(Fp, evp, jp, s)
                e_d += e
                h_d += h
            nulo_dia[d].append(h_d / e_d if e_d else np.nan)
            e_t += e_d
            h_t += h_d
        nulo.append(h_t / e_t if e_t else np.nan)
    nulo = np.array(nulo)
    p = (1 + int(np.sum(nulo >= R))) / (1 + len(nulo))
    for x in por_dia:
        v = np.array(nulo_dia[x["dia"]])
        v = v[np.isfinite(v)]
        x["R_azar_mediana"] = (float(np.median(v)) if len(v) else None)
        x["p_dia"] = ((1 + int(np.sum(v >= x["R"]))) / (1 + len(v)) if (x["R"] is not None and len(v)) else None)

    seco_ok = seco_["aprobado"]
    pod33 = pod["0.33"]
    if not seco_ok:
        ver = "INVÁLIDA"
    elif p <= 1 / 15 + 1e-9:
        ver = "LLEGA A VOLCAT" if (R >= R_MIN and R_ep >= REP_MIN) else "PARCIAL"
    else:
        ver = "NO LLEGA" if pod33 >= 0.8 else "SIN PODER"

    # recuerdo por E1
    porE1 = {}
    for e1 in (True, False):
        v = [x for x in detalle_P if x["evaluable"] and x["E1"] == e1]
        porE1["despejado" if e1 else "nublado"] = {"n": len(v), "alcanzados": sum(x["alcanzado"] for x in v)}

    # informativo
    clases = clases_por_cuadro()
    tasa_clase = {}
    for (d, s), c in clases.items():
        if c == "P" or dia_idx(d) not in pos:
            continue
        j = pos[dia_idx(d)]
        if eva[j, s]:
            t = tasa_clase.setdefault(c, [0, 0])
            t[0] += 1
            t[1] += int(Fa[j, s])
    tasa_clase = {c: {"n": v[0], "disparos": v[1], "tasa": v[1] / v[0]} for c, v in tasa_clase.items()}
    fina = []
    for d, h, px in VERDAD_FINA:
        j, s = pos.get(dia_idx(d)), slot(h)
        az_v = float(AZ[px])
        if j is None:
            continue
        fina.append({"dia": d, "hora": h, "F": bool(Fa[j, s]), "S": _r(Sa[j, s]), "U": _r(U[s]), "k": int(Ka[j, s]),
                     "sector_de_la_verdad": int(az_v // 30), "acimut_verdad": round(az_v, 1),
                     "k_contiene_verdad_o_vecino": bool(Ka[j, s] >= 0 and vecinos(int(Ka[j, s]), int(az_v // 30)))})
    nac = []
    for d, h in NACIMIENTOS:
        j, s = pos.get(dia_idx(d)), slot(h)
        nac.append({"dia": d, "hora": h, "evaluado": bool(eva[j, s]), "F": bool(Fa[j, s]), "S": _r(Sa[j, s]),
                    "U": _r(U[s])})
    ev60 = {"n": 0, "evaluados": 0, "disparos": 0}
    if os.path.exists(VOLCAT_EV_CSV):
        with open(VOLCAT_EV_CSV, encoding="utf-8") as f:
            for r in csv.DictReader(f):
                try:
                    dtv = datetime.utcfromtimestamp(int(r["t_inicio"]))     # inicio del scan, epoch UTC
                except (KeyError, ValueError):
                    continue
                d = (dtv - T0).days
                s = dtv.hour * 6 + dtv.minute // 10
                ev60["n"] += 1
                if d in pos and eva[pos[d], s]:
                    ev60["evaluados"] += 1
                    ev60["disparos"] += int(Fa[pos[d], s])
    serie_0811 = []
    j8 = pos[dia_idx("2026-11-08")]
    for s in range(72, 144):
        serie_0811.append({"hora": hhmm(s), "S": _r(Sa[j8, s]), "U": _r(U[s]), "k": int(Ka[j8, s]),
                           "F": bool(Fa[j8, s]), "E1": bool(E1[dia_idx("2026-11-08"), s]),
                           "VOLCAT_P": s in P.get("2026-11-08", [])})
    out = {"veredicto": ver, "R": R, "R_ep": R_ep, "cuadros_P_evaluables": n_ev, "cuadros_P_alcanzados": n_hit,
           "episodios": eps_tot, "episodios_alcanzados": eps_hit, "p": p, "R_azar": [_r(x) for x in nulo],
           "seco_fa": seco_["fa_media"], "poder": pod, "por_dia": por_dia, "por_E1": porE1,
           "detalle_P": detalle_P, "tasa_otras_clases_dias_actividad": tasa_clase, "verdad_fina": fina,
           "nacimientos": nac, "cuadros_evento_volcat": ev60, "serie_0811": serie_0811}
    json.dump(out, open(os.path.join(RES, "s22a_resultado.json"), "w", encoding="utf-8"), ensure_ascii=False,
              indent=1)
    print(json.dumps({k: out[k] for k in ("veredicto", "R", "R_ep", "cuadros_P_evaluables", "cuadros_P_alcanzados",
                                          "episodios", "episodios_alcanzados", "p", "R_azar", "seco_fa", "poder",
                                          "por_E1", "tasa_otras_clases_dias_actividad", "verdad_fina", "nacimientos",
                                          "cuadros_evento_volcat")}, ensure_ascii=False, indent=1))
    for x in por_dia:
        print(x)


def _r(x):
    return None if (x is None or not np.isfinite(x)) else round(float(x), 4)


# ---------- figura del 08-11 ----------
def figura():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    r = json.load(open(os.path.join(RES, "s22a_resultado.json"), encoding="utf-8"))
    ser = r["serie_0811"]
    x = np.arange(len(ser))
    S = np.array([np.nan if v["S"] is None else v["S"] for v in ser])
    U = np.array([np.nan if v["U"] is None else v["U"] for v in ser])
    fig, ax = plt.subplots(figsize=(12, 4.2))
    ax.plot(x, S, ".-", color="0.25", lw=1, label="S (cola baja del sector menos la mediana de sectores)")
    ax.plot(x, U, "-", color="tab:blue", lw=1.5, label="umbral U (percentil 5, días placebo)")
    for i, v in enumerate(ser):
        if v["VOLCAT_P"]:
            ax.axvspan(i - 0.5, i + 0.5, color="tab:orange", alpha=0.25, lw=0)
        if v["F"]:
            ax.plot(i, S[i], "v", color="tab:red", ms=8)
        if not v["E1"]:
            ax.plot(i, np.nanmax(S) + 0.05, "|", color="0.6", ms=6)
    ax.plot([], [], "s", color="tab:orange", alpha=0.4, label="VOLCAT con pluma en el cráter (P)")
    ax.plot([], [], "v", color="tab:red", label="disparo del detector")
    ax.plot([], [], "|", color="0.6", label="cuadro nublado por E1")
    ax.set_xticks(x[::6])
    ax.set_xticklabels([v["hora"] for v in ser][::6])
    ax.set_xlabel("hora UTC, 08-11-2026 (Chile UTC-3)")
    ax.set_ylabel("S (K)")
    ax.set_title("S22a: detector por sectores frente a VOLCAT, Nevados de Chillán, 08-11-2026")
    ax.legend(fontsize=8, loc="lower left")
    os.makedirs(FIG, exist_ok=True)
    fn = os.path.join(FIG, "serie_0811.png")
    fig.tight_layout()
    fig.savefig(fn, dpi=130)
    print(fn)


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "pruebas"
    {"pruebas": lambda: pruebas(con_datos="--datos" in sys.argv), "seco": seco, "poder": poder, "medir": medir,
     "figura": figura}[cmd]()
