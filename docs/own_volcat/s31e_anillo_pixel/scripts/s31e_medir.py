r"""S31e: el anillo de S26a con cada píxel medido contra su propia temporada de 2025. Implementa
criterio_2026-11-26.md de esta carpeta (commit bc8bde2, empujado antes de calcular un solo disparo del anillo nuevo).

Por qué: S31d mostró que el anillo prefiere el SE en 2025, sin pluma, porque los píxeles altos de la cordillera tienen
por sí solos colas de BTD más hondas; restar la línea base iguala el promedio de cada píxel pero no cuánto se aparta. Aquí
cada residuo se pasa a "qué tan raro es para ese píxel a esa hora" (T1: cuantil normal de su percentil en su propio pozo
de 2025; T2, sensibilidad: z robusto) y el resto del anillo queda igual. El umbral se fija a la misma falsa alarma que
el congelado en 2025. Se mide falsa alarma en 2024, sesgo de rumbo en 2025 y 2024, alcance en los P de VOLCAT y, con el
método de S31c, si marca el tramo de 4 a 15 km.

El anillo congelado y sus scripts no se tocan: todo se importa sin cambios. Lee los cubos de D: y, para el tramo, los PNG
de VOLCAT (licencia SSEC: nada de eso va al repo). Escribe resultados/s31e_resultado.json y resultados/s31e_por_cuadro.csv
(sólo cifras) y en D:\goes_notas\s31\s31e\ las tablas de disparos y los cubos transformados.

Uso: python -I -B s31e_medir.py pruebas | medir
"""
import csv
import hashlib
import json
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
for sub in ("s23_fondo_2025", "s25b_fondo_2024", "s26a_combinado", "s31d_sesgo_se", "s31c_dos_coronas"):
    sys.path.insert(0, os.path.join(OV, sub, "scripts"))
import s23_medir as S  # noqa: E402
import s26a_medir as A26  # noqa: E402
import s31d_medir as D31  # noqa: E402
import s31c_medir as C31  # noqa: E402
B, M = S.B, S.M
S30 = C31.S30
assert D31.M is M and C31.M is M and A26.B is B

TRAB = r"D:\goes_notas\s31\s31e"
MIN_LIBRE_GB = 6.0

# ---------- parámetros del criterio ----------
W_POZO = 9                                   # §2: ±90 min
MIN_POZO_PIX = 20                            # §2: si no, pozo de la tajada
P_CONG = 4.75                                # p* del anillo congelado (S26a)
FA_CONG_DIA, FA_CONG_GLOBAL = 0.03998573325864734, 0.0376226826608506      # §3, s26a_seco.json a 4,75
P_GRID = [6.0 - 0.25 * i for i in range(17)]                                 # 6,00 a 2,00
SE = (4, 5, 6)
N_BOOT, SEMILLA = 10_000, 0
X_CONG = {"2025": 0.43905415713196033, "2024": 0.5144044321329639}          # S31d, exceso sobre E1
MARGEN, X_PARCIAL, X_PEOR = 0.10, 0.22, 0.54
MIN_DISP, MIN_DIAS_DISP = 30, 5
# comprobación de código (§6)
REPRO_2025 = {0: 9, 1: 10, 2: 1, 4: 41, 5: 13, 6: 35, 7: 16, 8: 6, 9: 1, 10: 4, 11: 2}
REPRO_2024 = {0: 7, 1: 1, 4: 14, 6: 14, 11: 2}
REPRO_E1_2025 = 0.2058733790999237
REPRO_P26 = (23, 54)
REPRO_TRAMO = {"px_cerca": 6, "rumbo_lejos": 12, "n": 23, "oraculo_px_cerca": 41, "oraculo_n": 87}

VARS = ("ID", "T1", "T2")
SECK = [np.flatnonzero(M.SEC == k) for k in range(M.NSEC)]
DISTA = C31.DISTF[M.AP]                      # km al cráter de cada píxel del anillo


# ---------- la corrección (§2) ----------
def transformar(X, P):
    """X (m, NA) residuos; P (n, NA) pozo de referencia del mismo píxel. Devuelve Z1 (T1), Z2 (T2) y el número de
    píxeles válidos que usaron el pozo de la tajada en T1 y en T2."""
    X = np.atleast_2d(np.asarray(X, np.float32))
    fin = np.isfinite(P)
    n = fin.sum(0)
    med = np.nanmedian(P, 0)
    mad = 1.4826 * np.nanmedian(np.abs(P - med), 0)
    ok1 = n >= MIN_POZO_PIX
    ok2 = ok1 & (mad > 0)
    tk = []
    for k in range(M.NSEC):
        v = np.sort(P[:, SECK[k]][fin[:, SECK[k]]])
        if len(v):
            mk = float(np.median(v))
            tk.append((v, mk, 1.4826 * float(np.median(np.abs(v - mk)))))
        else:
            tk.append((v, np.nan, np.nan))
    Z1 = np.full(X.shape, np.nan, np.float32)
    Z2 = np.full(X.shape, np.nan, np.float32)
    nb1 = nb2 = 0
    for j, x in enumerate(X):
        val = np.isfinite(x)
        lt = (P < x).sum(0)
        eq = (P == x).sum(0)
        z1 = ndtri((lt + 0.5 * eq + 0.5) / (n + 1.0))
        z2 = (x - med) / np.where(mad > 0, mad, np.nan)
        for i in np.flatnonzero(val & ~ok1):
            v, _, _ = tk[M.SEC[i]]
            a, b = np.searchsorted(v, x[i], "left"), np.searchsorted(v, x[i], "right")
            z1[i] = ndtri((a + 0.5 * (b - a) + 0.5) / (len(v) + 1.0)) if len(v) else np.nan
            nb1 += 1
        for i in np.flatnonzero(val & ~ok2):
            _, mk, dk = tk[M.SEC[i]]
            z2[i] = (x[i] - mk) / dk if dk > 0 else np.nan
            nb2 += 1
        z1[~val] = np.nan
        z2[~val] = np.nan
        Z1[j], Z2[j] = z1, z2
    return Z1, Z2, nb1, nb2


def est(z):
    """S y k* con la función del detector, sin cambios."""
    s, k, _ = M.estadistico(z)
    return s, k


def cola(z, k):
    """Los 8 píxeles (índices de la grilla) de z más bajo en la tajada k (como s26a_medir.cola_anillo)."""
    idx = SECK[k]
    v = z[idx]
    o = np.argsort(np.where(np.isfinite(v), v, np.inf))[:M.NCOLA]
    return M.AP[idx[o]]


# ---------- los tres años ----------
def filas_pozo(gate, dias):
    """Por hora s, los (día, hora) de 2025 a ±90 min que pasan la compuerta."""
    out = {}
    for s in range(144):
        out[s] = np.array([(dd, x) for dd in dias for x in range(144) if M.dslot(x, s) <= W_POZO and gate[dd, x]],
                          int).reshape(-1, 2)
    return out


def anio_2025(D):
    """S, k* y z de 2025 por variante, cada día con su base y su pozo sin ese día."""
    t = time.time()
    NR = len(D.DIASR)
    FP = filas_pozo(D.GATER, D.DIASR)
    Z = {v: np.full((NR, 144, M.NA), np.nan, np.float32) for v in VARS}
    SS = {v: np.full((NR, 144), np.nan) for v in VARS}
    KK = {v: np.full((NR, 144), -1, int) for v in VARS}
    nb = [0, 0]
    for d in D.DIASR:
        R = D.mmR - D.base(d)[None]
        for s in range(144):
            if not D.GATER[d, s]:
                continue
            f = FP[s]
            f = f[f[:, 0] != d]
            z1, z2, b1, b2 = transformar(R[d, s][None], R[f[:, 0], f[:, 1]])
            nb[0] += b1
            nb[1] += b2
            for v, z in (("ID", R[d, s]), ("T1", z1[0]), ("T2", z2[0])):
                Z[v][d, s] = z
                SS[v][d, s], KK[v][d, s] = est(z)
        print(f"  2025 día {d + 1}/{NR} ({time.time() - t:.0f} s)", flush=True)
    return Z, SS, KK, nb


def blanco(D, mm, gate):
    """S, k* y z de un año blanco (2026 o 2024) con la base y el pozo de los 62 días de 2025."""
    t = time.time()
    B0 = D.base(None)
    R0 = D.mmR - B0[None]
    FP = filas_pozo(D.GATER, D.DIASR)
    nd = mm.shape[0]
    R = mm - B0[None]
    Z = {v: np.full((nd, 144, M.NA), np.nan, np.float32) for v in VARS}
    SS = {v: np.full((nd, 144), np.nan) for v in VARS}
    KK = {v: np.full((nd, 144), -1, int) for v in VARS}
    nb = [0, 0]
    for s in range(144):
        dd = np.flatnonzero(gate[:, s])
        if not len(dd):
            continue
        f = FP[s]
        z1, z2, b1, b2 = transformar(R[dd, s], R0[f[:, 0], f[:, 1]])
        nb[0] += b1
        nb[1] += b2
        for j, d in enumerate(dd):
            for v, z in (("ID", R[d, s]), ("T1", z1[j]), ("T2", z2[j])):
                Z[v][d, s] = z
                SS[v][d, s], KK[v][d, s] = est(z)
        if s % 24 == 0:
            print(f"  blanco hora {s}/144 ({time.time() - t:.0f} s)", flush=True)
    return Z, SS, KK, nb


# ---------- umbral, disparos y falsa alarma ----------
def umbral(D, SR, p, excl):
    D.SR = SR
    D._U = {}
    B.PCT_U = p
    U, _ = D.umbral(excl)
    return U


def seco(D, SR, KR, p):
    """2025, cada día con el umbral sin ese día: lista de (F, ev) por día."""
    return [S.disparos(SR, KR, d, umbral(D, SR, p, d)) for d in D.DIASR]


def lista_disparos(FE):
    return [(d, int(s)) for d, (F, _) in enumerate(FE) for s in np.flatnonzero(F)]


def boot_media(dif, rng):
    dif = np.asarray(dif, float)
    xs = dif[rng.integers(0, len(dif), (N_BOOT, len(dif)))].mean(1)
    return float(dif.mean()), [float(x) for x in np.percentile(xs, [2.5, 97.5])]


def boot_razon(num, den, rng):
    num, den = np.asarray(num, float), np.asarray(den, float)
    i = rng.integers(0, len(num), (N_BOOT, len(num)))
    xs = num[i].sum(1) / den[i].sum(1)
    return float(num.sum() / den.sum()), [float(x) for x in np.percentile(xs, [2.5, 97.5])]


def rot_ic(ic):
    return "MEJORA" if ic[1] < 0 else ("PEOR" if ic[0] > 0 else "IGUAL")


def e1_cuadro(mask, semilla):
    """p1 de s31d_medir.modelos_cuadro (máscara real, ruido igual), con el mismo sorteo."""
    rng = np.random.default_rng(semilla)
    Zr = rng.standard_normal((D31.N_MC, M.NA))
    Zr[:, ~mask] = np.nan
    return D31.p_se_cola(*D31.estadistico_lote(Zr)[:2])


def sesgo(disp, Zv, KR, etiqueta):
    """disp: (d, s). Cuota SE, E1, exceso con IC por días y rótulo del criterio §7."""
    t = time.time()
    filas = []
    for d, s in disp:
        filas.append((d, int(KR[d, s]), e1_cuadro(np.isfinite(Zv[d, s]), 1000 * d + s)))
    dias = sorted({d for d, *_ in filas})
    O = [sum(k in SE for dd, k, _ in filas if dd == d) for d in dias]
    N = [sum(1 for dd, *_ in filas if dd == d) for d in dias]
    E = [sum(e for dd, _, e in filas if dd == d) for d in dias]
    out = {"disparos": len(filas), "dias": len(dias), "tajadas": np.bincount([k for _, k, _ in filas], minlength=12).tolist()}
    if not filas:
        out["rotulo"] = "NO DECIDIBLE"
        return out
    x, lo, hi = D31.bootstrap_exceso(O, N, E, np.random.default_rng(SEMILLA))
    out.update({"cuota_SE": sum(O) / sum(N), "E1": sum(E) / sum(N), "exceso": x, "IC95": [lo, hi]})
    if len(filas) < MIN_DISP or len(dias) < MIN_DIAS_DISP:
        r = "NO DECIDIBLE"
    elif lo <= 0 <= hi and abs(x) <= MARGEN:
        r = "MEJORA"
    elif hi < 0 and x <= -MARGEN:
        r = "SOBRECORRIGE"
    elif x <= X_PARCIAL:
        r = "MEJORA PARCIAL"
    elif x >= X_PEOR:
        r = "PEOR"
    else:
        r = "IGUAL"
    out["rotulo"] = r
    print(f"  sesgo {etiqueta}: {len(filas)} disparos, cuota SE {out['cuota_SE']:.3f}, E1 {out['E1']:.3f}, "
          f"X {x:.3f} [{lo:.3f}, {hi:.3f}] {r} ({time.time() - t:.0f} s)", flush=True)
    return out


def distancias(disp, Zv, KR):
    km = [DISTA[np.searchsorted(M.AP, cola(Zv[d, s], int(KR[d, s])))] for d, s in disp]
    if not km:
        return {}
    a = np.concatenate(km)
    return {"px": int(len(a)), "mediana_km": round(float(np.median(a)), 1),
            "cuartiles_km": [round(float(x), 1) for x in np.percentile(a, [25, 75])],
            "frac_4_15km": round(float((a < 15).mean()), 4)}


# ---------- tramo (método de S31c, sin cambios) ----------
_H = {}


def H(dia, s):
    key = (dia, s)
    if key not in _H:
        st, h = S30.huella(dia, s) if 0 <= s < 144 else ("fuera", None)
        _H[key] = S30.Huella(h) if st == "ok" else None
    return _H[key]


def tabla_2026(CL, FE, SS, KK, Zv):
    T = defaultdict(dict)
    for d in range(B.ND):
        F, ev = FE[d]
        for s in range(144):
            c = ";".join(str(i) for i in cola(Zv[d, s], int(KK[d, s]))) if F[s] else ""
            T[B.fecha(d)][s] = {"clase": CL[d, s], "ev_a": str(int(ev[s])), "F_a": str(int(F[s])),
                                "S_a": SS[d, s], "k_a": str(int(KK[d, s])), "cola_a": c}
    return T


def tramo(T, etiqueta):
    """Copia del bucle de s31c_medir.medir para la huella anclada; generador nuevo con semilla 0 y el mismo orden."""
    t = time.time()
    rng = np.random.default_rng(C31.SEMILLA)
    P = [(d, s) for d in sorted(T) for s in sorted(T[d]) if T[d][s]["clase"] == "P"]
    donantes, items, orcs, orc_taj = defaultdict(list), [], [], []
    for d, s in P:
        hu = H(d, s)
        if hu is None:
            continue
        donantes[d].append(hu)
        dp = C31.disparo_px(T[d], s)
        if dp is not None:
            items.append((d, hu, dp, s))
        hn = H(d, s - 1) or H(d, s + 1)
        if hn is not None:
            od = C31.oraculo(hn)
            if od is not None:
                orcs.append((d, hu, od, s))
            orc_taj.append((d, hu, S30.oraculo_disparos(hn), s))
    out = {}
    sel = {"todo": lambda s: True, "dia": lambda s: s >= 72, "noche": lambda s: s < 72}
    for per, f in sel.items():
        its = [(d, hu, dp) for d, hu, dp, s in items if f(s)]
        ois = [(d, hu, dp) for d, hu, dp, s in orcs if f(s)]
        r = C31.prueba(its, donantes, rng)
        o = C31.prueba(ois, donantes, rng)
        ot = S30.prueba([(d, hu, di) for d, hu, di, s in orc_taj if f(s)], "a", donantes, rng, usar_R=True, usar_D=False)
        otp = ot["R"]["p"] if ot.get("R") else 1.0
        r["veredicto"] = C31.veredicto(r, o, otp)
        out[per] = {"detector": r, "oraculo": o, "oraculo_tajada_pR": otp}
        fmt = {m: (v["T"], v.get("G", {}).get("p"), v["R"]["p"], v["D"]["p"]) for m, v in r.get("medidas", {}).items()}
        fmo = {m: (v["T"], v.get("G", {}).get("p")) for m, v in o.get("medidas", {}).items()}
        print(f"  tramo {etiqueta} {per}: n {r['n']} días {len(r.get('dias', []))} | {fmt} | {r['veredicto']}", flush=True)
        print(f"     oráculo n {o['n']}: {fmo} | tajada p_R {otp} ({time.time() - t:.0f} s)", flush=True)
    out["P_con_huella"] = sum(len(v) for v in donantes.values())
    out["evaluados"] = len(items)
    out["km_px_disparo_P"] = distancias_px([dp for *_, dp, _ in items])
    return out


def distancias_px(dps):
    if not dps:
        return {}
    a = C31.DISTF[np.concatenate([dp[0] for dp in dps])]
    return {"px": int(len(a)), "mediana_km": round(float(np.median(a)), 1), "frac_4_15km": round(float((a < 15).mean()), 4)}


def rot_tramo(v):
    if v.startswith("VE EL TRAMO"):
        return "MEJORA"
    if v == "SÓLO LEJOS":
        return "IGUAL"
    return "NO DECIDIBLE"


# ---------- poder sintético (§6, descriptivo) ----------
def poder(D, SRv, pv, var):
    """s23_medir.poder con la firma sumada al residuo antes de transformar (mismos pares y acimutes)."""
    t = time.time()
    SR0 = D.SR0
    pares = []
    U5 = {d: umbral(D, SR0, 5.0, d) for d in D.DIASR}
    for d in D.DIASR:
        U = U5[d]
        for s in range(1, 144):
            if U[s] is not None and U[s - 1] is not None and np.isfinite(SR0[d, s]) and np.isfinite(SR0[d, s - 1]):
                pares.append((d, s))
    rng = np.random.default_rng(B.SEMILLA)
    elegidos = rng.choice(len(pares), B.N_POD, replace=len(pares) < B.N_POD)
    azs = rng.uniform(0, 360, B.N_POD)
    FP = filas_pozo(D.GATER, D.DIASR)
    UV = {}
    out = {"pares": len(pares), "variante": var, "percentil": pv}
    for a in B.FIRMAS:
        hits, hits_se, n_se = 0, 0, 0
        for e, az in zip(elegidos, azs):
            d, s = pares[e]
            if d not in UV:
                UV[d] = umbral(D, SRv, pv, d)
            U = UV[d]
            Bd = D.base(d)
            R = D.mmR - Bd[None] if var != "ID" else None
            sel = M.pixeles_rayo(az)
            ksec = int(az // 30) % M.NSEC
            res = []
            for x in (s - 1, s):
                v = D.mmR[d, x] - Bd[x]
                v[sel] -= a
                if var != "ID":
                    f = FP[x]
                    f = f[f[:, 0] != d]
                    z1, z2, _, _ = transformar(v[None], R[f[:, 0], f[:, 1]])
                    v = z1[0] if var == "T1" else z2[0]
                res.append(M.estadistico(v))
            (S1, k1, _), (S2, k2, _) = res
            h = (np.isfinite(S1) and np.isfinite(S2) and S1 <= U[s - 1] and S2 <= U[s] and M.vecinos(k1, k2)
                 and M.vecinos(k2, ksec))
            hits += h
            n_se += ksec in SE
            hits_se += h and ksec in SE
        out[f"{a:.2f}"] = {"poder": hits / B.N_POD, "poder_rayo_SE": hits_se / n_se if n_se else None,
                           "poder_rayo_fuera_SE": (hits - hits_se) / (B.N_POD - n_se) if B.N_POD > n_se else None}
        print(f"  poder {var} a {a:.2f} K: {out[f'{a:.2f}']} ({time.time() - t:.0f} s)", flush=True)
    return out


# ---------- pruebas de código (§6, punto 5) ----------
def pruebas():
    rng = np.random.default_rng(5)
    P = rng.standard_normal((200, M.NA)).astype(np.float32)
    P[:190, 3] = np.nan                                  # píxel 3 con 10 valores: pozo de su tajada
    P[:, 7] = 0.0                                        # píxel 7 con MAD 0: T2 usa la tajada
    x = np.zeros(M.NA, np.float32)
    x[0] = np.sort(P[:, 0])[49] + 1e-4                   # 50 valores menores en 200 -> u = 50,5 / 201
    x[5] = np.nan
    Z1, Z2, nb1, nb2 = transformar(x[None], P)
    assert abs(Z1[0, 0] - ndtri(50.5 / 201)) < 1e-5, Z1[0, 0]
    assert np.isnan(Z1[0, 5]) and np.isnan(Z2[0, 5])
    k3 = M.SEC[3]
    v = np.sort(P[:, SECK[k3]][np.isfinite(P[:, SECK[k3]])])
    a = np.searchsorted(v, 0.0, "left")
    b = np.searchsorted(v, 0.0, "right")
    assert abs(Z1[0, 3] - ndtri((a + 0.5 * (b - a) + 0.5) / (len(v) + 1))) < 1e-5
    assert nb1 == 1 and nb2 == 2                          # píxel 3 en T1; píxeles 3 y 7 en T2
    med, mad = np.median(P[:, 1]), 1.4826 * np.median(np.abs(P[:, 1] - np.median(P[:, 1])))
    assert abs(Z2[0, 1] - (0 - med) / mad) < 1e-4
    # empate: valor igual a 9 de 30 del pozo
    P2 = np.zeros((30, M.NA), np.float32)
    P2[:9] = 1.0
    P2[9:] = 2.0
    z, _, _, _ = transformar(np.ones((1, M.NA), np.float32), P2)
    assert abs(z[0, 0] - ndtri((0 + 4.5 + 0.5) / 31)) < 1e-6
    # S, k* sobre z = s22a_medir.estadistico; cola dentro de la tajada y en el anillo
    zz = rng.standard_normal(M.NA).astype(np.float32)
    zz[rng.random(M.NA) < 0.2] = np.nan
    s, k = est(zz)
    Sx, Kx, _ = D31.estadistico_lote(zz[None])
    assert abs(s - Sx[0]) < 1e-5 and k == Kx[0]
    c = cola(zz, k)
    assert len(c) == M.NCOLA and all(C31.SECF[p] == k and C31.AMASK[p] for p in c)
    assert np.allclose(np.sort(zz[np.searchsorted(M.AP, c)]), np.sort(zz[SECK[k]][np.isfinite(zz[SECK[k]])])[:8])
    assert rot_ic([-0.2, -0.1]) == "MEJORA" and rot_ic([0.1, 0.2]) == "PEOR" and rot_ic([-0.1, 0.1]) == "IGUAL"
    assert rot_tramo("SÓLO LEJOS") == "IGUAL" and rot_tramo("VE EL TRAMO DE VOLCAT, PARCIAL, sin separar") == "MEJORA"
    assert P_GRID[0] == 6.0 and P_GRID[-1] == 2.0 and 4.75 in P_GRID
    print("pruebas OK")


# ---------- medir ----------
def _json(o):
    return o.item() if hasattr(o, "item") else str(o)


def guardar(res):
    json.dump(res, open(os.path.join(RES, "s31e_resultado.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1,
              default=_json)


def medir():
    t0 = time.time()
    os.makedirs(RES, exist_ok=True)
    os.makedirs(TRAB, exist_ok=True)
    assert shutil.disk_usage("D:\\").free / 1e9 >= MIN_LIBRE_GB, "D: bajo el piso de 6 GB"
    res = {"criterio": "criterio_2026-11-26.md (commit bc8bde2)",
           "rotulo": "DESARROLLO: días de 2024, 2025 y 2026 (hasta el 24-11) ya vistos; nada de esto confirma"}
    est26 = np.load(A26.ESTAT26)
    assert hashlib.sha256(est26.tobytes()).hexdigest()[:16] == A26.SHA_ESTAT26, "estat_2026 no es el congelado"
    D = S.Detector(ref="2025", con_blanco=True, estat_blanco=est26)
    D.SR0, D.KR0 = D.SR.copy(), D.KR.copy()
    assert all(B.fecha(d) <= "2026-11-24" for d in range(B.ND)), "días posteriores al 24-11"
    CL = D.CLT
    # 2024 (costumbre de 2024, como S31d)
    import s25b_medir as X24
    D24 = X24._detector_2024()
    acm24, m124 = np.load(X24._npy24("acm")), np.load(X24._npy24("m1"))
    FD24, mm24 = D._nubes(acm24, m124, D24.ESTAT)
    gate24 = FD24 <= B.G_MAX
    del D24
    print(f"detectores listos ({time.time() - t0:.0f} s)", flush=True)

    Z25, S25, K25, nb25 = anio_2025(D)
    assert np.array_equal(np.isfinite(S25["ID"]), np.isfinite(D.SR0)) and np.allclose(
        S25["ID"][np.isfinite(D.SR0)], D.SR0[np.isfinite(D.SR0)], atol=0, rtol=0), "S de 2025 no es el del detector"
    Z26, S26, K26, nb26 = blanco(D, D.mmT, D.GATET)
    assert np.array_equal(np.nan_to_num(S26["ID"], nan=9e9), np.nan_to_num(D.ST, nan=9e9)), "S de 2026 no es el del detector"
    Z24, S24, K24, nb24 = blanco(D, mm24, gate24)
    res["pozo_de_tajada"] = {"T1": {"2025": nb25[0], "2026": nb26[0], "2024": nb24[0]},
                             "T2": {"2025": nb25[1], "2026": nb26[1], "2024": nb24[1]},
                             "pixeles_validos": {"2025": int(np.isfinite(Z25["ID"]).sum()),
                                                 "2026": int(np.isfinite(Z26["ID"]).sum()),
                                                 "2024": int(np.isfinite(Z24["ID"]).sum())}}
    for v in ("T1", "T2"):
        np.savez_compressed(os.path.join(TRAB, f"S_K_{v}.npz"), S25=S25[v], K25=K25[v], S26=S26[v], K26=K26[v],
                            S24=S24[v], K24=K24[v])
    print(f"transformaciones listas ({time.time() - t0:.0f} s)", flush=True)

    # ---- comprobación de código con la identidad (§6) ----
    rep = {}
    FE = seco(D, S25["ID"], K25["ID"], P_CONG)
    m = A26.medidas_seco(FE)
    d25 = lista_disparos(FE)
    rep["2025"] = {"disparos": len(d25), "tajadas": {int(a): int(b) for a, b in zip(*np.unique(
        [K25["ID"][d, s] for d, s in d25], return_counts=True))}, "fa_media_dia": m["media_por_dia"]}
    U0 = umbral(D, S25["ID"], P_CONG, None)
    d24 = [(d, int(s)) for d in range(mm24.shape[0]) for s in np.flatnonzero(S.disparos(S24["ID"], K24["ID"], d, U0)[0])]
    rep["2024"] = {"disparos": len(d24), "tajadas": {int(a): int(b) for a, b in zip(*np.unique(
        [K24["ID"][d, s] for d, s in d24], return_counts=True))}}
    FE26 = [S.disparos(S26["ID"], K26["ID"], d, U0) for d in range(B.ND)]
    T_id = tabla_2026(CL, FE26, S26["ID"], K26["ID"], Z26["ID"])
    malas = 0
    with open(S30.TABLA, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            q = T_id[r["dia"]][M.slot(r["hora"])]
            malas += (r["F_a"], r["k_a"], r["cola_a"], r["ev_a"]) != (q["F_a"], q["k_a"], q["cola_a"], q["ev_a"])
    Pal = [B.alcanzado(*FE26[d], s) for d in range(B.ND) for s in range(144) if CL[d, s] == "P"]
    rep["2026"] = {"filas_distintas_de_tabla_S26a": malas,
                   "P": (sum(a for e, a in Pal if e), sum(e for e, _ in Pal))}
    rep["E1_2025"] = sesgo(d25, Z25["ID"], K25["ID"], "congelado 2025")
    ok = (rep["2025"]["tajadas"] == REPRO_2025 and abs(rep["2025"]["fa_media_dia"] - FA_CONG_DIA) < 1e-9
          and rep["2024"]["tajadas"] == REPRO_2024 and malas == 0 and rep["2026"]["P"] == REPRO_P26
          and abs(rep["E1_2025"]["E1"] - REPRO_E1_2025) < 1e-9)
    print("comprobación de código:", json.dumps({k: v for k, v in rep.items() if k != "E1_2025"}, ensure_ascii=False),
          "OK" if ok else "NO REPRODUCE", flush=True)
    res["comprobacion"] = rep
    if not ok:
        res["veredicto"] = "INVÁLIDA"
        guardar(res)
        sys.exit("no reproduce el anillo congelado: se para")
    tr_id = tramo(T_id, "congelado")
    b = tr_id["todo"]
    okt = (b["detector"]["n"] == REPRO_TRAMO["n"] and b["detector"]["medidas"]["px_cerca"]["T"] == REPRO_TRAMO["px_cerca"]
           and b["detector"]["medidas"]["rumbo_lejos"]["T"] == REPRO_TRAMO["rumbo_lejos"]
           and b["detector"]["veredicto"] == "SÓLO LEJOS" and b["oraculo"]["n"] == REPRO_TRAMO["oraculo_n"]
           and b["oraculo"]["medidas"]["px_cerca"]["T"] == REPRO_TRAMO["oraculo_px_cerca"]
           and b["oraculo"]["medidas"]["px_cerca"]["G"]["p"] <= C31.P_MAX)
    res["comprobacion"]["tramo_congelado"] = tr_id
    print("comprobación del tramo:", "OK" if okt else "NO REPRODUCE", flush=True)
    if not okt:
        res["veredicto"] = "INVÁLIDA"
        guardar(res)
        sys.exit("no reproduce S31c: se para")
    guardar(res)
    cong = {"FE25": FE, "d25": d25, "d24": d24, "FE26": FE26, "U0": U0}

    # ---- las dos variantes ----
    por_cuadro = []
    for v in ("T1", "T2"):
        tv = time.time()
        out = {"calibracion": []}
        pe = None
        for p in P_GRID:
            m = A26.medidas_seco(seco(D, S25[v], K25[v], p))
            out["calibracion"].append({"pct": p, "fa_media_dia": m["media_por_dia"], "fa_global": m["global"],
                                       "disparos": m["disparos"], "evaluados": m["evaluados"]})
            print(f"  {v} p {p:.2f}: FA día {m['media_por_dia']:.4f} global {m['global']:.4f}", flush=True)
            if m["media_por_dia"] <= FA_CONG_DIA and m["global"] <= FA_CONG_GLOBAL:
                pe = p
                break
        out["p_e"] = pe
        if pe is None:
            out["veredicto"] = "NO SIRVE"
            res[v] = out
            guardar(res)
            continue
        FEv = seco(D, S25[v], K25[v], pe)
        dv25 = lista_disparos(FEv)
        Uv = umbral(D, S25[v], pe, None)
        # (a) falsa alarma 2024
        f_new, f_old, n24 = [], [], []
        for d in range(mm24.shape[0]):
            Fn, en = S.disparos(S24[v], K24[v], d, Uv)
            Fo, eo = S.disparos(S24["ID"], K24["ID"], d, U0)
            assert np.array_equal(en, eo), "los cuadros evaluados de 2024 deberían ser los mismos"
            if en.sum():
                f_new.append(Fn.sum() / en.sum())
                f_old.append(Fo.sum() / eo.sum())
                n24.append((int(Fn.sum()), int(Fo.sum()), int(en.sum())))
        x, ic = boot_media(np.array(f_new) - np.array(f_old), np.random.default_rng(SEMILLA))
        dv24 = [(d, int(s)) for d in range(mm24.shape[0]) for s in np.flatnonzero(S.disparos(S24[v], K24[v], d, Uv)[0])]
        out["fa_2024"] = {"nuevo_media_dia": float(np.mean(f_new)), "congelado_media_dia": float(np.mean(f_old)),
                          "nuevo_global": sum(a for a, _, _ in n24) / sum(c for *_, c in n24),
                          "congelado_global": sum(b_ for _, b_, _ in n24) / sum(c for *_, c in n24),
                          "dif_media_dia": x, "IC95": ic, "rotulo": rot_ic(ic),
                          "nuevo_aguanta_5pct": bool(np.mean(f_new) <= 0.05), "dias": len(f_new)}
        print(f"  {v} FA 2024: {json.dumps(out['fa_2024'])}", flush=True)
        # (b) sesgo
        out["sesgo_2025"] = sesgo(dv25, Z25[v], K25[v], f"{v} 2025")
        out["sesgo_2024"] = sesgo(dv24, Z24[v], K24[v], f"{v} 2024")
        out["distancia_cola_2025"] = {"nuevo": distancias(dv25, Z25[v], K25[v]),
                                      "congelado": distancias(cong["d25"], Z25["ID"], K25["ID"])}
        # (c) alcance en los P de 2026
        FE26v = [S.disparos(S26[v], K26[v], d, Uv) for d in range(B.ND)]
        num, den, filas_p = [], [], []
        alc_n = alc_o = ev_t = 0
        for d in range(B.ND):
            Ps = np.flatnonzero(CL[d] == "P")
            a_n = a_o = e_ = 0
            for s in Ps:
                en, an = B.alcanzado(*FE26v[d], s)
                eo, ao = B.alcanzado(*cong["FE26"][d], s)
                assert en == eo
                if en:
                    e_ += 1
                    a_n += an
                    a_o += ao
                    filas_p.append((d, s, int(ao), int(an)))
            if e_:
                num.append(a_n - a_o)
                den.append(e_)
                alc_n += a_n
                alc_o += a_o
                ev_t += e_
        x, ic = boot_razon(num, den, np.random.default_rng(SEMILLA))
        tasaN = [FE26v[d][0][s] for d in range(B.ND) for s in np.flatnonzero(FE26v[d][1]) if CL[d, s] == "N"]
        tasaN0 = [cong["FE26"][d][0][s] for d in range(B.ND) for s in np.flatnonzero(cong["FE26"][d][1]) if CL[d, s] == "N"]
        r25 = A26.azar(FEv)
        out["alcance_P_2026"] = {"P_evaluados": ev_t, "nuevo_alcanzados": alc_n, "congelado_alcanzados": alc_o,
                                 "dif_por_P": x, "IC95": ic, "rotulo": rot_ic([-ic[1], -ic[0]]),
                                 "dias_P_evaluados": len(den),
                                 "esperado_azar_2025_nuevo": float(sum(r25[s] for _, s, _, _ in filas_p)),
                                 "tasa_disparo_N_2026": {"nuevo": float(np.mean(tasaN)), "congelado": float(np.mean(tasaN0)),
                                                         "n": len(tasaN)}}
        print(f"  {v} alcance P: {json.dumps(out['alcance_P_2026'])}", flush=True)
        d26 = [(d, int(s)) for d in range(B.ND) for s in np.flatnonzero(FE26v[d][0])]
        out["disparos_2026"] = {"n": len(d26), "tajadas": np.bincount([K26[v][d, s] for d, s in d26], minlength=12).tolist(),
                                "distancia_cola": distancias(d26, Z26[v], K26[v])}
        # (d) tramo
        T_v = tabla_2026(CL, FE26v, S26[v], K26[v], Z26[v])
        with open(os.path.join(TRAB, f"tabla_2026_{v}.csv"), "w", encoding="utf-8", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["dia", "hora", "clase", "ev_a", "F_a", "S_a", "k_a", "cola_a"])
            for dia in sorted(T_v):
                for s in range(144):
                    q = T_v[dia][s]
                    w.writerow([dia, M.hhmm(s), q["clase"], q["ev_a"], q["F_a"], D31._r(q["S_a"]), q["k_a"], q["cola_a"]])
        out["tramo"] = tramo(T_v, v)
        out["tramo_rotulo"] = rot_tramo(out["tramo"]["todo"]["detector"]["veredicto"])
        # (poder sintético)
        out["poder"] = {"nuevo": poder(D, S25[v], pe, v)}
        if v == "T1":
            res["poder_congelado"] = poder(D, S25["ID"], P_CONG, "ID")
        # titular de la variante
        rs = out["sesgo_2025"]["rotulo"]
        parte1 = {"MEJORA": "CORRIGE EL SESGO", "MEJORA PARCIAL": "REDUCE EL SESGO", "IGUAL": "NO CORRIGE EL SESGO",
                  "PEOR": "NO CORRIGE EL SESGO", "SOBRECORRIGE": "SOBRECORRIGE EL SESGO",
                  "NO DECIDIBLE": "SESGO NO DECIDIBLE"}[rs]
        parte2 = {"MEJORA": "Y VE EL TRAMO DE VOLCAT", "IGUAL": "PERO SIGUE SÓLO LEJOS",
                  "NO DECIDIBLE": "Y EL TRAMO QUEDA NO DECIDIBLE"}[out["tramo_rotulo"]]
        ver = f"{parte1} {parte2}"
        if out["fa_2024"]["rotulo"] == "PEOR":
            ver += ", CON MÁS FALSA ALARMA EN 2024"
        if out["alcance_P_2026"]["rotulo"] == "PEOR":
            ver += ", PIERDE ALCANCE"
        out["veredicto"] = ver
        res[v] = out
        if v == "T1":
            res["veredicto"] = ver
            por_cuadro = filas_p
        print(f"{v}: {ver} ({time.time() - tv:.0f} s)", flush=True)
        guardar(res)
    # por cuadro P (sólo cifras, sin huellas)
    with open(os.path.join(RES, "s31e_por_cuadro.csv"), "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["dia", "hora", "alcanzado_congelado", "alcanzado_T1"])
        for d, s, ao, an in por_cuadro:
            w.writerow([B.fecha(d), M.hhmm(s), ao, an])
    guardar(res)
    print(f"VEREDICTO (T1): {res.get('veredicto')}; listo en {time.time() - t0:.0f} s", flush=True)


if __name__ == "__main__":
    pruebas() if sys.argv[1:] == ["pruebas"] else medir()
