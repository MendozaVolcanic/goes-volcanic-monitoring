r"""S31h: detector de la corona cercana (4 a 15 km del cráter) con regla propia. Implementa criterio_2026-11-27.md de
esta carpeta (commit 6ef64c4, empujado antes de calcular un solo disparo de la corona).

Por qué: el anillo congelado (4 a 40 km) marca el rumbo de la pluma de VOLCAT pero a 22 a 33 km (S31c), donde la
cordillera alta atrae su cola sin pluma (S31d); medir cada píxel contra su temporada quita esa preferencia, pero la cola
de 8 de una tajada de 66 a 74 píxeles igual esquiva el vértice cercano (S31e §3). Aquí se mira sólo el tramo de 4 a 15 km
donde VOLCAT dibuja la pluma anclada: doce tajadas de 30° con 8 a 10 píxeles cada una, cada píxel llevado a su cuantil
propio de 2025 (T1), media de los 3 más bajos, umbral a la misma falsa alarma que el congelado en 2025. Se mide falsa
alarma en 2024, sesgo de rumbo en 2025, alcance en los P de VOLCAT y si marca el tramo y el rumbo de la huella anclada
más que un píxel cualquiera de la corona (nulo Gc, calibrado con lo que el detector elige sin pluma), con R y D de S31c.

Ningún script congelado se toca: todo se importa sin cambios. Lee cubos de D: y PNG de VOLCAT (licencia SSEC: nada de
eso va al repo). Escribe resultados/s31h_resultado.json y resultados/s31h_por_cuadro.csv (sólo cifras) y en
D:\goes_notas\s31\s31h\ los cubos de z, las tablas de disparos y el registro.

Uso: python -I -B s31h_medir.py pruebas | medir
"""
import csv
import hashlib
import json
import math
import os
import shutil
import sys
import time
import warnings
from collections import defaultdict

import numpy as np
from scipy.special import ndtri

sys.stdout.reconfigure(encoding="utf-8")
warnings.simplefilter("ignore")
AQUI = os.path.dirname(os.path.abspath(__file__))
OV = os.path.abspath(os.path.join(AQUI, "..", ".."))
RES = os.path.join(os.path.dirname(AQUI), "resultados")
for sub in ("s23_fondo_2025", "s25b_fondo_2024", "s26a_combinado", "s31d_sesgo_se", "s31c_dos_coronas",
            "s31e_anillo_pixel"):
    sys.path.insert(0, os.path.join(OV, sub, "scripts"))
import s23_medir as S  # noqa: E402
import s26a_medir as A26  # noqa: E402
import s31d_medir as D31  # noqa: E402
import s31c_medir as C31  # noqa: E402
import s31e_medir as E31  # noqa: E402
B, M = S.B, S.M
S30 = C31.S30
assert D31.M is M and C31.M is M and E31.M is M and A26.B is B

TRAB = r"D:\goes_notas\s31\s31h"
MIN_LIBRE_GB = 6.0

# ---------- parámetros del criterio ----------
CORTE_KM = 15.0                                   # §1
CI = np.flatnonzero(M.AD < CORTE_KM)              # posiciones de la corona dentro del anillo (0..NA-1)
NC = len(CI)                                      # 107
SEC_C = M.SEC[CI]
TAJ = [np.flatnonzero(SEC_C == k) for k in range(M.NSEC)]
GRID_C = M.AP[CI]                                 # índices planos de la grilla ABI
CORONA_F = np.zeros(M.NY * M.NX, bool)
CORONA_F[GRID_C] = True
MIEMBROS_C = [GRID_C[TAJ[k]] for k in range(M.NSEC)]
MIN_VAL, NBAJOS, MIN_TAJ = 5, 3, 9                # §3
W_POZO, MIN_POZO_PIX = 9, 20                      # §2
P_CONG = 4.75
FA_CONG_DIA, FA_CONG_GLOBAL = E31.FA_CONG_DIA, E31.FA_CONG_GLOBAL
P_GRID = E31.P_GRID
SE = (4, 5, 6)
N_BOOT, SEMILLA, N_E1 = 10_000, 0, 2000
MARGEN, MIN_DISP, MIN_DIAS_DISP = 0.10, 30, 5
FA24_MAX = 0.05
P_MAX, MIN_P, MIN_DIAS, MIN_FRAC, MIN_CONF = 0.01, 10, 3, 0.25, 1000
B_MC, ENUM_MAX = C31.B_MC, C31.ENUM_MAX
N_INY_C = 4                                       # §9, poder sintético
REPRO_TRAMO = {"px_cerca": 6, "rumbo_lejos": 12, "n": 23, "oraculo_px_cerca": 41, "oraculo_n": 87,
               "pG_px_cerca": 0.9397, "pR_px_cerca": 0.0012, "pR_rumbo_lejos": 0.0068}
REPRO_P26 = (23, 54)
VARS = ("T1", "Rc")
SECF, DISTF, AMASK = C31.SECF, C31.DISTF, C31.AMASK
assert NC == 107 and [len(t) for t in TAJ] == [9, 8, 10, 8, 10, 8, 8, 10, 8, 10, 10, 8]
assert np.array_equal(np.sort(GRID_C), np.flatnonzero(C31.CERCA))


# ---------- escala propia (§2) ----------
def transformar_c(X, P):
    """X (m, NC) residuos de la corona; P (n, NC) su pozo de 2025. T1 con pozo de la tajada de la corona si n < 20.
    Devuelve Z (m, NC) y cuántos píxeles válidos usaron el pozo de la tajada."""
    X = np.atleast_2d(np.asarray(X, np.float32))
    fin = np.isfinite(P)
    n = fin.sum(0)
    ok = n >= MIN_POZO_PIX
    tk = [np.sort(P[:, TAJ[k]][fin[:, TAJ[k]]]) for k in range(M.NSEC)]
    Z = np.full(X.shape, np.nan, np.float32)
    nb = 0
    for j, x in enumerate(X):
        val = np.isfinite(x)
        lt = (P < x).sum(0)
        eq = (P == x).sum(0)
        z = ndtri((lt + 0.5 * eq + 0.5) / (n + 1.0))
        for i in np.flatnonzero(val & ~ok):
            v = tk[SEC_C[i]]
            a, b = np.searchsorted(v, x[i], "left"), np.searchsorted(v, x[i], "right")
            z[i] = ndtri((a + 0.5 * (b - a) + 0.5) / (len(v) + 1.0)) if len(v) else np.nan
            nb += 1
        z[~val] = np.nan
        Z[j] = z
    return Z, nb


# ---------- estadístico (§3) ----------
def est_lote(Z):
    """Z (m, NC). Devuelve S (m), K (m) y Q (m, 12)."""
    Z = np.atleast_2d(Z)
    m = Z.shape[0]
    Q = np.full((m, M.NSEC), np.nan)
    for k in range(M.NSEC):
        v = Z[:, TAJ[k]]
        nv = np.isfinite(v).sum(1)
        q = np.sort(np.where(np.isfinite(v), v, np.inf), 1)[:, :NBAJOS].mean(1)
        Q[:, k] = np.where(nv >= MIN_VAL, q, np.nan)
    nval = np.isfinite(Q).sum(1)
    ok = nval >= MIN_TAJ
    S_ = np.full(m, np.nan)
    K = np.full(m, -1, int)
    if ok.any():
        Qo = Q[ok]
        k = np.nanargmin(Qo, 1)
        S_[ok] = Qo[np.arange(len(Qo)), k] - np.nanmedian(Qo, 1)
        K[ok] = k
    return S_, K, Q


def est(z):
    s, k, _ = est_lote(z[None])
    return float(s[0]), int(k[0])


def cola_c(z, k):
    """Los 3 píxeles (índices planos) de z más bajo en la tajada k de la corona."""
    idx = TAJ[k]
    v = z[idx]
    o = np.argsort(np.where(np.isfinite(v), v, np.inf))[:NBAJOS]
    return GRID_C[idx[o]]


# ---------- los tres años ----------
def anio_2025(D):
    t = time.time()
    NR = len(D.DIASR)
    FP = E31.filas_pozo(D.GATER, D.DIASR)
    Z = {v: np.full((NR, 144, NC), np.nan, np.float32) for v in VARS}
    SS = {v: np.full((NR, 144), np.nan) for v in VARS}
    KK = {v: np.full((NR, 144), -1, int) for v in VARS}
    nb = 0
    for d in D.DIASR:
        R = (D.mmR - D.base(d)[None])[:, :, CI]
        for s in range(144):
            if not D.GATER[d, s]:
                continue
            f = FP[s]
            f = f[f[:, 0] != d]
            z1, b1 = transformar_c(R[d, s][None], R[f[:, 0], f[:, 1]])
            nb += b1
            Z["T1"][d, s], Z["Rc"][d, s] = z1[0], R[d, s]
        for v in VARS:
            SS[v][d], KK[v][d], _ = est_lote(Z[v][d])
        if d % 10 == 0:
            print(f"  2025 día {d + 1}/{NR} ({time.time() - t:.0f} s)", flush=True)
    return Z, SS, KK, nb


def blanco(D, mm, gate):
    t = time.time()
    B0 = D.base(None)
    R0 = (D.mmR - B0[None])[:, :, CI]
    FP = E31.filas_pozo(D.GATER, D.DIASR)
    nd = mm.shape[0]
    R = (mm - B0[None])[:, :, CI]
    Z = {v: np.full((nd, 144, NC), np.nan, np.float32) for v in VARS}
    SS = {v: np.full((nd, 144), np.nan) for v in VARS}
    KK = {v: np.full((nd, 144), -1, int) for v in VARS}
    nb = 0
    for s in range(144):
        dd = np.flatnonzero(gate[:, s])
        if not len(dd):
            continue
        f = FP[s]
        z1, b1 = transformar_c(R[dd, s], R0[f[:, 0], f[:, 1]])
        nb += b1
        Z["T1"][dd, s] = z1
        Z["Rc"][dd, s] = R[dd, s]
        if s % 36 == 0:
            print(f"  blanco hora {s}/144 ({time.time() - t:.0f} s)", flush=True)
    for v in VARS:
        for d in range(nd):
            SS[v][d], KK[v][d], _ = est_lote(Z[v][d])
            SS[v][d][~gate[d]] = np.nan
            KK[v][d][~gate[d]] = -1
    return Z, SS, KK, nb


# ---------- nulos y prueba (§5) ----------
def mapa_w(rng, pix_dia, miembros, pesos):
    """Como s31c_medir.mapa_G, con los miembros de cada tajada y pesos opcionales (sorteo sin reponer)."""
    por_k = defaultdict(list)
    for p in sorted(pix_dia):
        por_k[int(SECF[p])].append(p)
    mapa = {}
    for k in sorted(por_k):
        orig = por_k[k]
        if pesos is None:
            dest = rng.permutation(miembros[k])[:len(orig)]
        else:
            w = pesos[k]
            dest = rng.choice(miembros[k], size=len(orig), replace=False, p=w / w.sum())
        mapa.update(zip(orig, (int(x) for x in dest)))
    return mapa


def colocaciones(pix_dia, miembros):
    c = 1
    por_k = defaultdict(int)
    for p in pix_dia:
        por_k[int(SECF[p])] += 1
    for k, m in por_k.items():
        c *= math.comb(len(miembros[k]), m)
    return c


def prueba(items, donantes, rng, miembros, pesos, uniforme_extra=False):
    """Copia de s31c_medir.prueba con el nulo de posición parametrizado (miembros y pesos). Con miembros =
    s31c_medir.MIEMBROS, pesos None y uniforme_extra False hace exactamente las mismas llamadas al generador que
    s31c_medir.prueba. La clave del nulo de posición es 'G' (como en S31c); con uniforme_extra, se agrega 'Gu'."""
    MED, NUL = C31.MEDIDAS, C31.NULOS
    dias = sorted({d for d, _, _ in items})
    nd, n = len(dias), len(items)
    idx = {d: i for i, d in enumerate(dias)}
    obs = [C31.coincide(hu, dp) for _, hu, dp in items]
    out = {"n": n, "dias": dias, "medidas": {}}
    if not n:
        return out
    res = {m: {"T": int(sum(o[m] for o in obs)), "frac": sum(o[m] for o in obs) / n} for m in MED}
    tab = {m: np.zeros((nd, 12), int) for m in MED}
    for d, hu, dp in items:
        for j in range(12):
            c = C31.coincide(hu, dp, j)
            for m in MED:
                tab[m][idx[d], j] += c[m]
    confR = 12 ** nd
    J = None if confR <= ENUM_MAX else rng.integers(0, 12, size=(B_MC, nd))
    for m in MED:
        T = res[m]["T"]
        if J is None:
            tot = np.zeros(1, int)
            for i in range(nd):
                tot = (tot[:, None] + tab[m][i][None, :]).ravel()
            p, met = float((tot >= T).mean()), f"exacto ({confR} combinaciones)"
        else:
            tot = tab[m][np.arange(nd)[None, :], J].sum(1)
            p, met = float((1 + (tot >= T).sum()) / (B_MC + 1)), f"Monte Carlo B={B_MC}"
        res[m]["R"] = {"p": p, "frac_esperada": float(tot.mean()) / n, "configuraciones": confR,
                       "decide": confR >= MIN_CONF, "metodo": met}
    pix_dia = defaultdict(set)
    for d, _, dp in items:
        pix_dia[d].update(int(p) for p in dp[0])
    confG = int(np.prod([float(colocaciones(pix_dia[d], miembros)) for d in dias]))

    def nulo_pos(pw, clave):
        totG = {m: np.zeros(B_MC, int) for m in MED if "G" in NUL[m]}
        for b in range(B_MC):
            mapas = {d: mapa_w(rng, pix_dia[d], miembros, pw) for d in dias}
            for d, hu, dp in items:
                c = C31.coincide(hu, dp, 0, mapas[d])
                for m in totG:
                    totG[m][b] += c[m]
        for m, tot in totG.items():
            res[m][clave] = {"p": float((1 + (tot >= res[m]["T"]).sum()) / (B_MC + 1)),
                             "frac_esperada": float(tot.mean()) / n, "colocaciones": confG,
                             "decide": nd >= MIN_DIAS and confG >= MIN_CONF, "metodo": f"Monte Carlo B={B_MC}",
                             "pesos": "uniforme" if pw is None else "disparos de 2025 + 1"}

    nulo_pos(pesos, "G")
    cand = {d: [x for x in sorted(donantes) if x != d] for d in dias}
    confD = int(np.prod([len(cand[d]) for d in dias], dtype=float))
    totD = {m: np.zeros(B_MC, int) for m in MED}
    for b in range(B_MC):
        don = {d: cand[d][rng.integers(len(cand[d]))] for d in dias}
        for d, hu, dp in items:
            lst = donantes[don[d]]
            c = C31.coincide(lst[rng.integers(len(lst))], dp)
            for m in MED:
                totD[m][b] += c[m]
    for m in MED:
        res[m]["D"] = {"p": float((1 + (totD[m] >= res[m]["T"]).sum()) / (B_MC + 1)),
                       "frac_esperada": float(totD[m].mean()) / n, "configuraciones_dia": confD,
                       "decide": confD >= MIN_CONF, "metodo": f"Monte Carlo B={B_MC}"}
    if uniforme_extra:
        nulo_pos(None, "Gu")
    out["medidas"] = res
    return out


def oraculo_c(hn):
    """Píxeles del oráculo en la corona: los de la huella vecina en su tajada con más píxeles en la corona."""
    ring = hn.h[CORONA_F[hn.h]]
    if not len(ring):
        return None
    k = int(np.argmax(np.bincount(SECF[ring], minlength=12)))
    pix = ring[SECF[ring] == k]
    return pix.astype(int), np.full(len(pix), k, int)


def veredicto(r, o, sesgo_rot):
    """Criterio §8 (r y o con medidas renombradas px y rumbo)."""
    if r["n"] < MIN_P or len(r["dias"]) < MIN_DIAS:
        return "NO DECIDIBLE (pocos cuadros o días)"
    if not o.get("medidas"):
        return "SIN PODER (el oráculo no tiene cuadros)"
    og = o["medidas"]["px"]["G"]
    if og["p"] > P_MAX or not og["decide"]:
        return "SIN PODER (el oráculo no pasa Gc en px)"
    pc, ru = r["medidas"]["px"], r["medidas"]["rumbo"]
    gc_ok = pc["G"]["decide"] and pc["G"]["p"] <= P_MAX
    r_ok = pc["R"]["p"] <= P_MAX
    if gc_ok and r_ok:
        v = "VE EL TRAMO" if pc["frac"] >= MIN_FRAC else "VE EL TRAMO, PARCIAL"
        if pc["D"]["decide"] and pc["D"]["p"] <= P_MAX and o["medidas"]["px"]["D"]["p"] <= P_MAX:
            v += ", y sigue a esta pluma"
        else:
            v += ", sin separar esta pluma de la de otro día"
        if sesgo_rot == "SESGO SE":
            v += ", con rumbo que la corona ya prefería sin pluma"
        return v
    if pc["G"]["p"] > P_MAX and pc["R"]["p"] > P_MAX and ru["R"]["p"] > P_MAX:
        return "NO SE APARTA"
    pasa = [x for x, ok in (("px con Gc", gc_ok), ("px con R", r_ok), ("rumbo con R", ru["R"]["p"] <= P_MAX)) if ok]
    return "NO DECIDIBLE (pasa sólo " + (", ".join(pasa) if pasa else "un nulo que no decide") + ")"


def renombrar(r):
    if r.get("medidas"):
        r["medidas"] = {"px": r["medidas"]["px_cerca"], "rumbo": r["medidas"]["rumbo_cerca"]}
    return r


# ---------- sesgo de rumbo (§5 b) ----------
def e1_cuadro(mask, semilla):
    rng = np.random.default_rng(semilla)
    Zr = rng.standard_normal((N_E1, NC))
    Zr[:, ~mask] = np.nan
    s, k, _ = est_lote(Zr)
    ok = np.isfinite(s)
    return float(np.isin(k[ok], SE).mean()) if ok.any() else np.nan, np.bincount(k[ok], minlength=12) / max(ok.sum(), 1)


def sesgo(disp, Z, K, etiqueta):
    t = time.time()
    filas, hist_e = [], np.zeros(12)
    for d, s in disp:
        e, h = e1_cuadro(np.isfinite(Z[d, s]), 1000 * d + s)
        filas.append((d, int(K[d, s]), e))
        hist_e += h
    dias = sorted({d for d, *_ in filas})
    out = {"disparos": len(filas), "dias": len(dias),
           "tajadas": np.bincount([k for _, k, _ in filas], minlength=12).tolist(),
           "tajadas_esperadas_E1": [round(float(x), 2) for x in hist_e]}
    if not filas:
        out["rotulo"] = "NO DECIDIBLE"
        return out
    O = [sum(k in SE for dd, k, _ in filas if dd == d) for d in dias]
    N = [sum(1 for dd, *_ in filas if dd == d) for d in dias]
    E = [sum(e for dd, _, e in filas if dd == d) for d in dias]
    x, lo, hi = D31.bootstrap_exceso(O, N, E, np.random.default_rng(SEMILLA))
    out.update({"cuota_SE": sum(O) / sum(N), "E1": sum(E) / sum(N), "exceso": x, "IC95": [lo, hi]})
    if len(filas) < MIN_DISP or len(dias) < MIN_DIAS_DISP:
        r = "NO DECIDIBLE"
    elif lo <= 0 <= hi and abs(x) <= MARGEN:
        r = "SIN SESGO SE"
    elif lo > 0:
        r = "SESGO SE"
    else:
        r = "INTERMEDIO"
    out["rotulo"] = r
    print(f"  sesgo {etiqueta}: {len(filas)} disparos en {len(dias)} días, cuota SE {out['cuota_SE']:.3f}, "
          f"E1 {out['E1']:.3f}, X {x:.3f} [{lo:.3f}, {hi:.3f}] {r} ({time.time() - t:.0f} s)", flush=True)
    return out


def distancias(grid_idx):
    if not len(grid_idx):
        return {}
    a = DISTF[np.asarray(grid_idx, int)]
    return {"px": int(len(a)), "mediana_km": round(float(np.median(a)), 1),
            "cuartiles_km": [round(float(x), 1) for x in np.percentile(a, [25, 75])],
            "frac_menos_9_7km": round(float((a < 9.7).mean()), 4)}


# ---------- tramo (§5 d) ----------
def tabla_2026(CL, FE, SS, KK, Z):
    T = defaultdict(dict)
    for d in range(B.ND):
        F, ev = FE[d]
        for s in range(144):
            c = ";".join(str(i) for i in cola_c(Z[d, s], int(KK[d, s]))) if F[s] else ""
            T[B.fecha(d)][s] = {"clase": CL[d, s], "ev_a": str(int(ev[s])), "F_a": str(int(F[s])),
                                "S_a": SS[d, s], "k_a": str(int(KK[d, s])), "cola_a": c}
    return T


def tramo(T, pesos, etiqueta, rng_semilla=SEMILLA):
    t = time.time()
    rng = np.random.default_rng(rng_semilla)
    P = [(d, s) for d in sorted(T) for s in sorted(T[d]) if T[d][s]["clase"] == "P"]
    donantes, items, orcs = defaultdict(list), [], []
    for d, s in P:
        hu = E31.H(d, s)
        if hu is None:
            continue
        donantes[d].append(hu)
        dp = C31.disparo_px(T[d], s)
        if dp is not None:
            items.append((d, hu, dp, s))
        hn = E31.H(d, s - 1) or E31.H(d, s + 1)
        if hn is not None:
            od = oraculo_c(hn)
            if od is not None:
                orcs.append((d, hu, od, s))
    out = {}
    sel = {"todo": lambda s: True, "dia": lambda s: s >= 72, "noche": lambda s: s < 72}
    for per, f in sel.items():
        its = [(d, hu, dp) for d, hu, dp, s in items if f(s)]
        ois = [(d, hu, dp) for d, hu, dp, s in orcs if f(s)]
        r = renombrar(prueba(its, donantes, rng, MIEMBROS_C, pesos, uniforme_extra=True))
        o = renombrar(prueba(ois, donantes, rng, MIEMBROS_C, pesos, uniforme_extra=True))
        out[per] = {"detector": r, "oraculo": o}
        fmt = {m: (v["T"], v.get("G", {}).get("p"), v.get("Gu", {}).get("p"), v["R"]["p"], v["D"]["p"])
               for m, v in r.get("medidas", {}).items()}
        fmo = {m: (v["T"], v.get("G", {}).get("p"), v["R"]["p"]) for m, v in o.get("medidas", {}).items()}
        print(f"  tramo {etiqueta} {per}: n {r['n']} días {r.get('dias')} | (T, pGc, pG, pR, pD) {fmt}", flush=True)
        print(f"     oráculo n {o['n']}: {fmo} ({time.time() - t:.0f} s)", flush=True)
    out["P_con_huella"] = sum(len(v) for v in donantes.values())
    out["dias_con_huella"] = len(donantes)
    out["evaluados"] = len(items)
    out["km_px_disparo_P"] = distancias(np.concatenate([dp[0] for *_, dp, _ in items])) if items else {}
    out["_items"] = [(d, s) for d, _, _, s in items]
    return out


# ---------- poder sintético (§9) ----------
def pix_rayo_c(az):
    ux, uy = np.sin(np.radians(az)), np.cos(np.radians(az))
    ax, ay = M.AX[CI], M.AY[CI]
    t = ax * ux + ay * uy
    perp = np.where(t >= 0, np.abs(ax * uy - ay * ux), np.inf)
    return np.argsort(perp)[:N_INY_C]


def poder(D, SRv, KRv, pv, var):
    t = time.time()
    SR0 = D.SR0
    pares = []
    U5 = {d: E31.umbral(D, SR0, 5.0, d) for d in D.DIASR}
    for d in D.DIASR:
        U = U5[d]
        for s in range(1, 144):
            if U[s] is not None and U[s - 1] is not None and np.isfinite(SR0[d, s]) and np.isfinite(SR0[d, s - 1]):
                pares.append((d, s))
    rng = np.random.default_rng(B.SEMILLA)
    elegidos = rng.choice(len(pares), B.N_POD, replace=len(pares) < B.N_POD)
    azs = rng.uniform(0, 360, B.N_POD)
    FP = E31.filas_pozo(D.GATER, D.DIASR)
    UV, RD = {}, {}
    out = {"pares": len(pares), "variante": var, "percentil": pv}
    for a in B.FIRMAS:
        hits, hits_se, n_se = 0, 0, 0
        for e, az in zip(elegidos, azs):
            d, s = pares[e]
            if d not in UV:
                UV[d] = E31.umbral(D, SRv, pv, d)
                RD[d] = (D.mmR - D.base(d)[None])[:, :, CI]
            U, R = UV[d], RD[d]
            sel = pix_rayo_c(az)
            ksec = int(az // 30) % M.NSEC
            res = []
            for x in (s - 1, s):
                v = R[d, x].copy()
                v[sel] -= a
                if var == "T1":
                    f = FP[x]
                    f = f[f[:, 0] != d]
                    v = transformar_c(v[None], R[f[:, 0], f[:, 1]])[0][0]
                res.append(est(v))
            (S1, k1), (S2, k2) = res
            h = bool(np.isfinite(S1) and np.isfinite(S2) and U[s - 1] is not None and U[s] is not None
                     and S1 <= U[s - 1] and S2 <= U[s] and M.vecinos(k1, k2) and M.vecinos(k2, ksec))
            hits += h
            n_se += ksec in SE
            hits_se += h and ksec in SE
        out[f"{a:.2f}"] = {"poder": hits / B.N_POD, "poder_rayo_SE": hits_se / n_se if n_se else None,
                           "poder_rayo_fuera_SE": (hits - hits_se) / (B.N_POD - n_se) if B.N_POD > n_se else None}
        print(f"  poder {var} a {a:.2f} K: {out[f'{a:.2f}']} ({time.time() - t:.0f} s)", flush=True)
    return out


# ---------- pruebas sintéticas (§7, punto 4) ----------
def pruebas():
    rng = np.random.default_rng(3)
    z = rng.standard_normal(NC).astype(np.float32) + 2.0
    k0 = 5
    z[TAJ[k0][:3]] = [-3.0, -2.0, -1.0]
    s, k = est(z)
    _, _, Q = est_lote(z[None])
    assert k == k0 and abs(Q[0, k0] + 2.0) < 1e-6, (k, Q[0, k0])
    assert abs(s - (Q[0, k0] - np.nanmedian(Q[0]))) < 1e-9
    assert set(cola_c(z, k0)) == set(GRID_C[TAJ[k0][:3]])
    z2 = z.copy()
    z2[TAJ[k0][4:]] = np.nan                                     # tajada 5 (8 px) con 4 válidos: no cuenta
    _, _, Q2 = est_lote(z2[None])
    assert np.isnan(Q2[0, k0]) and est(z2)[1] != k0
    z3 = z.copy()
    for kk in range(4):
        z3[TAJ[kk]] = np.nan                                     # 8 tajadas válidas: no se evalúa
    assert np.isnan(est(z3)[0]) and est(z3)[1] == -1
    # T1 de la corona: cuantil conocido y pozo de tajada
    P = rng.standard_normal((200, NC)).astype(np.float32)
    P[:190, 3] = np.nan
    x = np.zeros(NC, np.float32)
    x[0] = np.sort(P[:, 0])[49] + 1e-4
    Zt, nb = transformar_c(x[None], P)
    assert abs(Zt[0, 0] - ndtri(50.5 / 201)) < 1e-5 and nb == 1
    v = np.sort(P[:, TAJ[SEC_C[3]]][np.isfinite(P[:, TAJ[SEC_C[3]]])])
    a, b = np.searchsorted(v, 0.0, "left"), np.searchsorted(v, 0.0, "right")
    assert abs(Zt[0, 3] - ndtri((a + 0.5 * (b - a) + 0.5) / (len(v) + 1))) < 1e-5
    # sorteo Gc: no cambia de tajada, no sale de la corona, no repite; con pesos iguales es la G uniforme
    pix = set(int(p) for p in np.r_[MIEMBROS_C[4][:5], MIEMBROS_C[7][:2], MIEMBROS_C[0][:1]])
    W = [np.arange(len(m), dtype=float) + 1 for m in MIEMBROS_C]
    for _ in range(300):
        mp = mapa_w(rng, pix, MIEMBROS_C, W)
        assert len(set(mp.values())) == len(mp)
        assert all(SECF[a_] == SECF[b_] and CORONA_F[b_] for a_, b_ in mp.items())
    r1, r2 = np.random.default_rng(9), np.random.default_rng(9)
    assert mapa_w(r1, pix, C31.MIEMBROS, None) == C31.mapa_G(r2, pix)
    assert colocaciones({int(MIEMBROS_C[1][0])}, MIEMBROS_C) == 8
    assert colocaciones(pix, MIEMBROS_C) == math.comb(10, 5) * math.comb(10, 2) * math.comb(9, 1)
    # E1 con ruido igual y máscara completa: cuota SE cercana a 3/12
    e, h = e1_cuadro(np.ones(NC, bool), 1)
    assert 0.18 < e < 0.32 and abs(h.sum() - 1) < 1e-9, e
    # rayo: 4 píxeles de la corona del lado del acimut
    for az in (0, 135, 250):
        sel = pix_rayo_c(az)
        d = np.abs((np.degrees(np.arctan2(M.AX[CI][sel], M.AY[CI][sel])) - az + 180) % 360 - 180)
        assert len(sel) == 4 and d.max() < 45, (az, d)
    print("pruebas OK")


# ---------- medir ----------
def _json(o):
    return o.item() if hasattr(o, "item") else str(o)


def guardar(res):
    json.dump(res, open(os.path.join(RES, "s31h_resultado.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1,
              default=_json)


def pesos_2025(disp, Z, K):
    """Pesos de Gc por tajada: veces que cada píxel de la corona fue píxel del disparo en 2025, + 1 (§5 d)."""
    cnt = defaultdict(int)
    for d, s in disp:
        for p in cola_c(Z[d, s], int(K[d, s])):
            cnt[int(p)] += 1
    return [np.array([cnt[int(p)] + 1 for p in MIEMBROS_C[k]], float) for k in range(M.NSEC)], dict(cnt)


def medir():
    t0 = time.time()
    os.makedirs(RES, exist_ok=True)
    os.makedirs(TRAB, exist_ok=True)
    assert shutil.disk_usage("D:\\").free / 1e9 >= MIN_LIBRE_GB, "D: bajo el piso de 6 GB"
    res = {"criterio": "criterio_2026-11-27.md (commit 6ef64c4)",
           "rotulo": "DESARROLLO: días de 2024, 2025 y 2026 (hasta el 24-11) ya vistos; nada de esto confirma",
           "geometria": {"px_corona": NC, "px_por_tajada": [len(t) for t in TAJ]}}
    est26 = np.load(A26.ESTAT26)
    assert hashlib.sha256(est26.tobytes()).hexdigest()[:16] == A26.SHA_ESTAT26, "estat_2026 no es el congelado"
    D = S.Detector(ref="2025", con_blanco=True, estat_blanco=est26)
    D.SR0, D.KR0 = D.SR.copy(), D.KR.copy()
    assert all(B.fecha(d) <= "2026-11-24" for d in range(B.ND)), "días posteriores al 24-11"
    CL = D.CLT
    import s25b_medir as X24
    D24 = X24._detector_2024()
    acm24, m124 = np.load(X24._npy24("acm")), np.load(X24._npy24("m1"))
    FD24, mm24 = D._nubes(acm24, m124, D24.ESTAT)
    gate24 = FD24 <= B.G_MAX
    del D24
    print(f"detectores listos ({time.time() - t0:.0f} s)", flush=True)

    # ---- comprobación de código (§7), antes de calcular nada de la corona ----
    rep = {}
    rng = np.random.default_rng(1)
    B0 = D.base(None)
    m1 = 0
    for d, s in zip(rng.integers(0, len(D.DIASR), 300), rng.integers(0, 144, 300)):
        if D.GATER[d, s]:
            a = M.estadistico(D.mmR[d, s] - D.base(d)[s])[0]
            m1 += not (a == D.SR0[d, s] or (np.isnan(a) and np.isnan(D.SR0[d, s])))
        if D.GATET[d, s]:
            a = M.estadistico(D.mmT[d, s] - B0[s])[0]
            m1 += not (a == D.ST[d, s] or (np.isnan(a) and np.isnan(D.ST[d, s])))
    rep["1_S_congelado_distintos"] = m1
    T_c = S30.leer_tabla()
    P = [(d, s) for d in sorted(T_c) for s in sorted(T_c[d]) if T_c[d][s]["clase"] == "P"]
    don, its, ois = defaultdict(list), [], []
    for d, s in P:
        hu = E31.H(d, s)
        if hu is None:
            continue
        don[d].append(hu)
        dp = C31.disparo_px(T_c[d], s)
        if dp is not None:
            its.append((d, hu, dp))
        hn = E31.H(d, s - 1) or E31.H(d, s + 1)
        if hn is not None:
            od = C31.oraculo(hn)
            if od is not None:
                ois.append((d, hu, od))
    ra = C31.prueba(its, don, np.random.default_rng(C31.SEMILLA))
    rb = prueba(its, don, np.random.default_rng(C31.SEMILLA), C31.MIEMBROS, None)
    iguales = ra["n"] == rb["n"] and ra["dias"] == rb["dias"] and all(
        ra["medidas"][m][k] == rb["medidas"][m][k] for m in C31.MEDIDAS for k in ("T", "frac")) and all(
        ra["medidas"][m][nu][k] == rb["medidas"][m][nu][k] for m in C31.MEDIDAS for nu in ra["medidas"][m]
        if nu in ("G", "R", "D") for k in ("p", "frac_esperada"))
    mc = rb["medidas"]
    orc_T = sum(C31.coincide(hu, dp)["px_cerca"] for _, hu, dp in ois)
    rep["2_prueba"] = {"identica_a_s31c": iguales, "n": rb["n"], "px_cerca": mc["px_cerca"]["T"],
                       "pG_px_cerca": mc["px_cerca"]["G"]["p"], "pR_px_cerca": mc["px_cerca"]["R"]["p"],
                       "rumbo_lejos": mc["rumbo_lejos"]["T"], "pR_rumbo_lejos": mc["rumbo_lejos"]["R"]["p"],
                       "oraculo_n": len(ois), "oraculo_px_cerca": orc_T}
    ok2 = (iguales and rb["n"] == REPRO_TRAMO["n"] and mc["px_cerca"]["T"] == REPRO_TRAMO["px_cerca"]
           and mc["rumbo_lejos"]["T"] == REPRO_TRAMO["rumbo_lejos"]
           and round(mc["px_cerca"]["G"]["p"], 4) == REPRO_TRAMO["pG_px_cerca"]
           and round(mc["px_cerca"]["R"]["p"], 4) == REPRO_TRAMO["pR_px_cerca"]
           and round(mc["rumbo_lejos"]["R"]["p"], 4) == REPRO_TRAMO["pR_rumbo_lejos"]
           and len(ois) == REPRO_TRAMO["oraculo_n"] and orc_T == REPRO_TRAMO["oraculo_px_cerca"])
    # 3: T1 de la corona contra s31e_medir.transformar
    FP = E31.filas_pozo(D.GATER, D.DIASR)
    R0full = D.mmR - B0[None]
    dmax, nchk = 0.0, 0
    for d, s in zip(rng.integers(0, B.ND, 400), rng.integers(0, 144, 400)):
        if nchk >= 40:
            break
        if not D.GATET[d, s]:
            continue
        f = FP[s]
        x = (D.mmT[d, s] - B0[s])[None]
        Pp = R0full[f[:, 0], f[:, 1]]
        ze, _, _, _ = E31.transformar(x, Pp)
        zc, _ = transformar_c(x[:, CI], Pp[:, CI])
        okp = np.isfinite(Pp[:, CI]).sum(0) >= MIN_POZO_PIX
        dd_ = np.abs(ze[0, CI][okp] - zc[0][okp])
        dd_ = dd_[np.isfinite(dd_)]
        if len(dd_):
            dmax = max(dmax, float(dd_.max()))
        assert np.array_equal(np.isfinite(ze[0, CI]), np.isfinite(zc[0]))
        nchk += 1
    rep["3_T1_dif_max"] = dmax
    rep["3_cuadros"] = nchk
    ok = m1 == 0 and ok2 and dmax <= 1e-5 and nchk == 40
    print("comprobación de código:", json.dumps(rep, ensure_ascii=False), "OK" if ok else "NO REPRODUCE", flush=True)
    res["comprobacion"] = rep
    if not ok:
        res["veredicto"] = "INVÁLIDA"
        guardar(res)
        sys.exit("la comprobación de código falla: se para")
    guardar(res)

    # ---- la corona en los tres años ----
    Z25, S25, K25, nb25 = anio_2025(D)
    Z26, S26, K26, nb26 = blanco(D, D.mmT, D.GATET)
    Z24, S24, K24, nb24 = blanco(D, mm24, gate24)
    res["pozo_de_tajada"] = {"2025": nb25, "2026": nb26, "2024": nb24,
                             "pixeles_validos": {"2025": int(np.isfinite(Z25["T1"]).sum()),
                                                 "2026": int(np.isfinite(Z26["T1"]).sum()),
                                                 "2024": int(np.isfinite(Z24["T1"]).sum())}}
    for v in VARS:
        np.savez_compressed(os.path.join(TRAB, f"corona_{v}.npz"), Z25=Z25[v], S25=S25[v], K25=K25[v], Z26=Z26[v],
                            S26=S26[v], K26=K26[v], Z24=Z24[v], S24=S24[v], K24=K24[v])
    print(f"corona lista ({time.time() - t0:.0f} s)", flush=True)
    # congelado de referencia (alcance y falsa alarma de 2024)
    U0 = E31.umbral(D, D.SR0, P_CONG, None)
    FE26c = [S.disparos(D.ST, D.KT, d, U0) for d in range(B.ND)]
    Pal = [B.alcanzado(*FE26c[d], s) for d in range(B.ND) for s in range(144) if CL[d, s] == "P"]
    p26c = (sum(a for e, a in Pal if e), sum(e for e, _ in Pal))
    assert p26c == REPRO_P26, p26c
    S24c = np.full(gate24.shape, np.nan)
    K24c = np.full(gate24.shape, -1, int)
    for d in range(mm24.shape[0]):
        for s in range(144):
            if gate24[d, s]:
                S24c[d, s], K24c[d, s], _ = M.estadistico(mm24[d, s] - B0[s])

    por_cuadro = {}
    for v in VARS:
        tv = time.time()
        out = {"calibracion": []}
        pe = None
        for p in P_GRID:
            m = A26.medidas_seco(E31.seco(D, S25[v], K25[v], p))
            out["calibracion"].append({"pct": p, "fa_media_dia": m["media_por_dia"], "fa_global": m["global"],
                                       "disparos": m["disparos"], "evaluados": m["evaluados"]})
            print(f"  {v} p {p:.2f}: FA día {m['media_por_dia']:.4f} global {m['global']:.4f}", flush=True)
            if m["media_por_dia"] <= FA_CONG_DIA and m["global"] <= FA_CONG_GLOBAL:
                pe = p
                break
        out["p_c"] = pe
        if pe is None:
            out["veredicto"] = "NO SIRVE"
            res[v] = out
            guardar(res)
            continue
        FEv = E31.seco(D, S25[v], K25[v], pe)
        dv25 = E31.lista_disparos(FEv)
        Uv = E31.umbral(D, S25[v], pe, None)
        out["umbral_por_hora"] = {M.hhmm(s): (None if Uv[s] is None else round(Uv[s], 4)) for s in range(0, 144, 6)}
        # (a) falsa alarma 2024
        f_new, f_old, n24 = [], [], []
        for d in range(mm24.shape[0]):
            Fn, en = S.disparos(S24[v], K24[v], d, Uv)
            Fo, eo = S.disparos(S24c, K24c, d, U0)
            if en.sum() and eo.sum():
                f_new.append(Fn.sum() / en.sum())
                f_old.append(Fo.sum() / eo.sum())
                n24.append((int(Fn.sum()), int(en.sum()), int(Fo.sum()), int(eo.sum())))
        x, ic = E31.boot_media(np.array(f_new) - np.array(f_old), np.random.default_rng(SEMILLA))
        dv24 = [(d, int(s)) for d in range(mm24.shape[0]) for s in np.flatnonzero(S.disparos(S24[v], K24[v], d, Uv)[0])]
        md = float(np.mean(f_new))
        out["fa_2024"] = {"media_dia": md, "global": sum(a for a, *_ in n24) / sum(b_ for _, b_, *_ in n24),
                          "congelado_media_dia_mismos_dias": float(np.mean(f_old)), "dif_media_dia": x, "IC95": ic,
                          "dias": len(f_new), "rotulo": "AGUANTA" if md <= FA24_MAX else "NO AGUANTA"}
        print(f"  {v} FA 2024: {json.dumps(out['fa_2024'])}", flush=True)
        # (b) sesgo
        out["sesgo_2025"] = sesgo(dv25, Z25[v], K25[v], f"{v} 2025")
        out["sesgo_2024"] = sesgo(dv24, Z24[v], K24[v], f"{v} 2024")
        out["distancia_disparo_2025"] = distancias(np.concatenate(
            [cola_c(Z25[v][d, s], int(K25[v][d, s])) for d, s in dv25]) if dv25 else [])
        # pesos de Gc
        W, cnt = pesos_2025(dv25, Z25[v], K25[v])
        out["pesos_Gc"] = {"px_con_disparo_2025": len(cnt), "max": max(cnt.values()) if cnt else 0,
                           "por_tajada_min_max": [[int(w.min()), int(w.max())] for w in W]}
        # (c) alcance en los P de 2026
        FE26v = [S.disparos(S26[v], K26[v], d, Uv) for d in range(B.ND)]
        num, den, dias_p = [], [], []
        no_ev = {"compuerta": 0, "tajadas": 0, "sin_s_vecino": 0}
        for d in range(B.ND):
            Ps = np.flatnonzero(CL[d] == "P")
            a_ = e_ = 0
            for s in Ps:
                en, an = B.alcanzado(*FE26v[d], s)
                eo, ao = B.alcanzado(*FE26c[d], s)
                por_cuadro.setdefault((d, s), {"dia": B.fecha(d), "hora": M.hhmm(s), "evaluado_congelado": int(eo),
                                               "alcanzado_congelado": int(ao)})
                por_cuadro[(d, s)][f"evaluado_{v}"] = int(en)
                por_cuadro[(d, s)][f"alcanzado_{v}"] = int(an)
                if en:
                    e_ += 1
                    a_ += an
                elif not D.GATET[d, s]:
                    no_ev["compuerta"] += 1
                elif not np.isfinite(S26[v][d, s]):
                    no_ev["tajadas"] += 1
                else:
                    no_ev["sin_s_vecino"] += 1
            if e_:
                num.append(a_)
                den.append(e_)
                dias_p.append({"dia": B.fecha(d), "P_evaluados": e_, "P_alcanzados": a_})
        x, ic = E31.boot_razon(num, den, np.random.default_rng(SEMILLA))
        tasaN = [FE26v[d][0][s] for d in range(B.ND) for s in np.flatnonzero(FE26v[d][1]) if CL[d, s] == "N"]
        d26 = [(d, int(s)) for d in range(B.ND) for s in np.flatnonzero(FE26v[d][0])]
        cls = defaultdict(int)
        for d, s in d26:
            cls[CL[d, s] or "sin_clase"] += 1
        out["alcance_P_2026"] = {"P_evaluados": int(sum(den)), "P_alcanzados": int(sum(num)), "R": x, "IC95": ic,
                                 "congelado": list(p26c), "P_total": int((CL == "P").sum()), "no_evaluados": no_ev,
                                 "por_dia": dias_p,
                                 "tasa_disparo_N_2026": float(np.mean(tasaN)) if tasaN else None, "N_evaluados": len(tasaN)}
        out["disparos_2026"] = {"n": len(d26), "por_clase": dict(cls),
                                "tajadas_dia": np.bincount([K26[v][d, s] for d, s in d26 if s >= 72], minlength=12).tolist(),
                                "tajadas_noche": np.bincount([K26[v][d, s] for d, s in d26 if s < 72], minlength=12).tolist(),
                                "dias": len({d for d, _ in d26})}
        print(f"  {v} alcance P: {json.dumps(out['alcance_P_2026'], ensure_ascii=False)}", flush=True)
        # (d) tramo y rumbo
        T_v = tabla_2026(CL, FE26v, S26[v], K26[v], Z26[v])
        with open(os.path.join(TRAB, f"tabla_2026_{v}.csv"), "w", encoding="utf-8", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["dia", "hora", "clase", "ev_a", "F_a", "S_a", "k_a", "cola_a"])
            for dia in sorted(T_v):
                for s in range(144):
                    q = T_v[dia][s]
                    w.writerow([dia, M.hhmm(s), q["clase"], q["ev_a"], q["F_a"], D31._r(q["S_a"]), q["k_a"], q["cola_a"]])
        tr = tramo(T_v, W, v)
        for dia, s in tr.pop("_items"):
            c = C31.coincide(E31.H(dia, s), C31.disparo_px(T_v[dia], s))
            q = por_cuadro[(B.dia_idx(dia), s)]
            q[f"px_{v}"], q[f"rumbo_{v}"] = int(c["px_cerca"]), int(c["rumbo_cerca"])
        for per in ("todo", "dia", "noche"):
            tr[per]["veredicto"] = veredicto(tr[per]["detector"], tr[per]["oraculo"], out["sesgo_2025"]["rotulo"])
        out["tramo"] = tr
        print(f"  {v} tramo: {tr['todo']['veredicto']}", flush=True)
        out["poder"] = poder(D, S25[v], K25[v], pe, v)
        ver = (f"{tr['todo']['veredicto']}; falsa alarma 2024 {out['fa_2024']['rotulo']}; "
               f"sesgo 2025 {out['sesgo_2025']['rotulo']}")
        out["veredicto"] = ver
        res[v] = out
        if v == "T1":
            res["veredicto"] = ver
        print(f"{v}: {ver} ({time.time() - tv:.0f} s)", flush=True)
        guardar(res)
    filas = [por_cuadro[k] for k in sorted(por_cuadro)]
    campos = []
    for f in filas:
        campos += [c for c in f if c not in campos]
    with open(os.path.join(RES, "s31h_por_cuadro.csv"), "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=campos)
        w.writeheader()
        w.writerows(filas)
    guardar(res)
    print(f"VEREDICTO (T1): {res.get('veredicto')}; listo en {time.time() - t0:.0f} s", flush=True)


if __name__ == "__main__":
    pruebas() if sys.argv[1:] == ["pruebas"] else medir()
