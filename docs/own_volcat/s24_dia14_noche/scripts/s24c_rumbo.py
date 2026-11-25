r"""S24c: regla de persistencia de rumbo. Implementa criterio_S24c_2026-11-25.md (commit d11eab8, antes de calibrar).

Por qué: la pluma es débil en 11 menos 12 µm pero sostiene su rumbo durante horas (el viento la empuja al mismo lado);
el ruido del suelo y del cielo cambia de tajada de un cuadro a otro. S23b pide cruzar un umbral exigente dos cuadros
seguidos; S24c pide un umbral más blando y que 4 de los últimos 6 cuadros (una hora) caigan en el mismo arco de 90°.

Uso: python -I s24c_rumbo.py pruebas | calibrar | desarrollo | medir [--vistazo]
  calibrar   ensayo en seco y poder en 2025 (año sin pluma) para P_B en 10, 15, 20, 25, 30; elige el mayor con
             falsa alarma media por día <= 0,05 (criterio §2). Escribe resultados/s24c_calibracion.json.
  desarrollo R contra los P de VOLCAT de 2026 ya mirados (post hoc, no decide).
  medir      días nuevos desde el 25-11, UNA vez, en la misma corrida que s23b_confirmar.py medir (criterio §4).
"""
import csv
import hashlib
import json
import os
import sys
from datetime import datetime, timedelta

import numpy as np
from scipy import stats

sys.stdout.reconfigure(encoding="utf-8")
AQUI = os.path.dirname(os.path.abspath(__file__))
OV = os.path.abspath(os.path.join(AQUI, "..", ".."))
RES = os.path.join(os.path.dirname(AQUI), "resultados")
sys.path.insert(0, os.path.join(OV, "s23_fondo_2025", "scripts"))
import s23_medir as S  # noqa: E402
import s23b_confirmar as CB  # noqa: E402  (días nuevos: clases, cubo, mínimos del §6; sin cambios)
B, M = S.B, S.M

CALIB = os.path.join(RES, "s24c_calibracion.json")
PCTS = (10.0, 15.0, 20.0, 25.0, 30.0)
VENT, NMIN = 6, 4                     # últimos 6 cuadros (s-5 a s), al menos 4 bajo el umbral blando en un arco
PB_CONGELADO = None                   # se fija en el commit que registra la calibración (criterio §3)


# ---------- regla ----------
def umbral_pct(D, excl, pct):
    """Detector.umbral de s23_medir con otro percentil (mismas ventanas, mínimos y reparto entre días)."""
    ds, ss, vs = [], [], []
    for d in D.DIASR:
        if d == excl:
            continue
        x = np.flatnonzero(D.NULR[d] & np.isfinite(D.SR[d]))
        ds += [d] * len(x)
        ss += list(x)
        vs += list(D.SR[d, x])
    ds, ss, vs = np.array(ds), np.array(ss), np.array(vs)
    U = [None] * 144
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
                U[s] = float(np.percentile(vs[m], pct))
                break
    return U


def en_arco(ks, k_s):
    """¿Hay al menos NMIN tajadas de ks dentro de un arco de 3 tajadas vecinas que también contenga k_s?"""
    for c in range(M.NSEC):
        if not M.vecinos(c, k_s):
            continue
        if sum(1 for k in ks if M.vecinos(k, c)) >= NMIN:
            return True
    return False


def disparos_rumbo(Sm, Km, d, U):
    """F y evaluado de un día; la ventana de las 00:00 a 00:40 toma los últimos cuadros del día anterior."""
    F = np.zeros(144, bool)
    ev = np.zeros(144, bool)

    def bajo(dd, s):
        if dd < 0 or U[s] is None or not np.isfinite(Sm[dd, s]):
            return None
        return int(Km[dd, s]) if Sm[dd, s] <= U[s] else -1

    for s in range(144):
        if U[s] is None or not np.isfinite(Sm[d, s]):
            continue
        ev[s] = True
        if Sm[d, s] > U[s]:
            continue
        ks = []
        for j in range(VENT):
            x = s - j
            dd, x = (d, x) if x >= 0 else (d - 1, x + 144)
            b = bajo(dd, x)
            if b is not None and b >= 0:
                ks.append(b)
        F[s] = en_arco(ks, int(Km[d, s]))
    return F, ev


def pruebas():
    assert en_arco([4, 4, 5, 3], 4) and en_arco([4, 5, 5, 6], 5) and not en_arco([3, 4, 6, 7], 4)
    assert en_arco([11, 0, 0, 1], 0) and not en_arco([4, 4, 5, 3], 8)
    Sm = np.full((2, 144), 1.0)
    Km = np.zeros((2, 144), int)
    U = [0.0] * 144
    for s, k in zip(range(20, 26), (4, 9, 5, 4, 1, 3)):           # 4 bajo en el arco 3-5: dispara en 25
        Sm[1, s], Km[1, s] = -1, k
    Sm[1, 21] = Sm[1, 24] = 1.0                                     # los de tajada 9 y 1 no estaban bajo
    F, ev = disparos_rumbo(Sm, Km, 1, U)
    assert F[25] and not F[22] and not F[24] and ev.all()
    Sm[1, 23] = 1.0                                                 # quedan 3: no dispara
    F, _ = disparos_rumbo(Sm, Km, 1, U)
    assert not F[25]
    for s in (140, 141, 142):                                       # cruce de medianoche
        Sm[0, s], Km[0, s] = -1, 6
    Sm[1, 0], Km[1, 0] = -1, 6
    F, _ = disparos_rumbo(Sm, Km, 1, U)
    assert F[0]
    print("pruebas OK")


# ---------- calibración en 2025 (§2) ----------
def _seco(D, pct):
    por_dia, slots, alc = [], [], []
    for d in D.DIASR:
        U = umbral_pct(D, d, pct)
        F, ev = disparos_rumbo(D.SR, D.KR, d, U)
        n = int(ev.sum())
        if n:
            por_dia.append(float(F.sum() / n))
        for s in np.flatnonzero(ev):
            slots.append(s)
            alc.append(B.alcanzado(F, ev, s)[1])
    return float(np.mean(por_dia)), np.array(slots), np.array(alc)


def _poder(D, pct, rng):
    casos = []
    for d in D.DIASR:
        U = umbral_pct(D, d, pct)
        for s in range(VENT - 1, 144):
            if all(U[x] is not None and np.isfinite(D.SR[d, x]) for x in range(s - VENT + 1, s + 1)):
                casos.append((d, s))
    el = rng.choice(len(casos), B.N_POD, replace=len(casos) < B.N_POD)
    azs = rng.uniform(0, 360, B.N_POD)
    out = {}
    cacheU = {}
    for a in B.FIRMAS:
        hits = 0
        for e, az in zip(el, azs):
            d, s = casos[e]
            U = cacheU.setdefault(d, umbral_pct(D, d, pct))
            Bd = D.base(d)
            sel = M.pixeles_rayo(az)
            ksec = int(az // 30) % M.NSEC
            ks, ultimo = [], False
            for x in range(s - VENT + 1, s + 1):
                v = D.mmR[d, x] - Bd[x]
                v[sel] -= a
                Sx, kx, _ = M.estadistico(v)
                b = np.isfinite(Sx) and Sx <= U[x] and M.vecinos(kx, ksec)
                if b:
                    ks.append(kx)
                ultimo = b if x == s else ultimo
            hits += bool(ultimo and en_arco(ks, ks[-1]))
        out[f"{a:.2f}"] = hits / B.N_POD
    return out


def calibrar():
    D = S.Detector(ref="2025", con_blanco=False)
    tabla = {}
    for pct in PCTS:
        fa, _, _ = _seco(D, pct)
        tabla[f"{pct:g}"] = {"fa_media_por_dia": round(fa, 4)}
        print(f"P_B {pct:g}: seco {fa:.4f}", flush=True)
    ok = [p for p in PCTS if tabla[f"{p:g}"]["fa_media_por_dia"] <= B.FA_MAX]
    pb = max(ok) if ok else None
    out = {"criterio": "criterio_S24c_2026-11-25.md (d11eab8)", "seco_por_PB": tabla, "P_B": pb,
           "abandonada": pb is None}
    if pb is not None:
        out["poder"] = _poder(D, pb, np.random.default_rng(B.SEMILLA))
        U, _ = D.umbral(None)
        Ub = umbral_pct(D, None, pb)
        out["U_S23b_vs_U_b"] = {M.hhmm(s): [S._r(U[s]), S._r(Ub[s])] for s in range(0, 144, 12)}
        # comprobación de código: umbral_pct a 5 reproduce Detector.umbral
        U5 = umbral_pct(D, None, B.PCT_U)
        assert all((a is None and b is None) or abs(a - b) < 1e-12 for a, b in zip(U5, U)), "umbral_pct no reproduce"
    os.makedirs(RES, exist_ok=True)
    json.dump(out, open(CALIB, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps(out, ensure_ascii=False, indent=1))


# ---------- medidas ----------
def _resumen(Sm, Km, CL, dias_idx, U, r25, fecha):
    P, N, por_dia = [], [], []
    for d in dias_idx:
        F, ev = disparos_rumbo(Sm, Km, d, U)
        for s in np.flatnonzero(ev):
            a = B.alcanzado(F, ev, s)[1]
            if CL[d, s] == "P":
                P.append((d, s, a))
            elif CL[d, s] == "N":
                N.append((d, s, a))
        Ps = np.flatnonzero(CL[d] == "P")
        if len(Ps) or F.any():
            pe = [a for dd, _, a in P if dd == d]
            por_dia.append({"dia": fecha(d), "P": int(len(Ps)), "P_evaluados": len(pe), "P_alcanzados": int(sum(pe)),
                            "disparos": int(F.sum()), "tajadas": np.bincount(Km[d][F], minlength=12).tolist(),
                            "horas": [M.hhmm(s) for s in np.flatnonzero(F)]})
    te, th = len(P), int(sum(a for *_, a in P))
    p25 = S.poisson_binomial_cola([r25[s] for _, s, _ in P], th) if te else None
    psl = {s for _, s, _ in P}
    cerca = [a for _, s, a in N if any(M.dslot(s, x) <= S.W_AZAR for x in psl)]
    pN = (float(stats.fisher_exact([[th, te - th], [int(sum(cerca)), len(cerca) - int(sum(cerca))]],
                                   alternative="greater")[1]) if te and cerca else None)
    return {"P_evaluados": te, "P_alcanzados": th, "R": th / te if te else None,
            "E25": float(sum(r25[s] for _, s, _ in P)), "p25": p25, "N_cerca_de_P": len(cerca),
            "N_cerca_alcanzados": int(sum(cerca)), "pN": pN, "N_evaluados": len(N),
            "dias_con_P_evaluado": len({d for d, _, _ in P}), "por_dia": por_dia}


def _pb():
    cal = json.load(open(CALIB, encoding="utf-8"))
    assert PB_CONGELADO is not None and cal["P_B"] == PB_CONGELADO, "P_B no congelado o distinto de la calibración"
    return PB_CONGELADO


def desarrollo():
    pb = json.load(open(CALIB, encoding="utf-8"))["P_B"]
    estat = np.load(CB.ESTAT)
    assert hashlib.sha256(estat.tobytes()).hexdigest()[:16] == CB.SHA_ESTAT
    D = S.Detector(ref="2025", con_blanco=True, estat_blanco=estat)
    _, sl, al = _seco(D, pb)
    r25 = S.azar_por_hora(sl, al)
    U = umbral_pct(D, None, pb)
    out = _resumen(D.ST, D.KT, D.CLT, range(B.ND), U, r25, B.fecha)
    out["nota"] = "POST HOC: días de 2026 ya mirados; no decide (criterio S24c §3)."
    out["P_B"] = pb
    json.dump(out, open(os.path.join(RES, "s24c_desarrollo.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps({k: v for k, v in out.items() if k != "por_dia"}, ensure_ascii=False, indent=1))
    for x in out["por_dia"]:
        print(x["dia"], x["P"], x["P_evaluados"], x["P_alcanzados"], x["disparos"], x["tajadas"])


def medir(vistazo=False):
    pb = _pb()
    with open(CB.CLASES, encoding="utf-8") as f:
        filas = list(csv.DictReader(f))
    ult = max(datetime.strptime(x["dt"][:10], "%Y-%m-%d") for x in filas)
    dias = [CB.ARRANQUE + timedelta(days=i) for i in range((ult - CB.ARRANQUE).days + 1)]
    CL = np.full((len(dias), 144), "", object)
    for x in filas:
        CL[(datetime.strptime(x["dt"][:10], "%Y-%m-%d") - CB.ARRANQUE).days, M.slot(x["dt"][11:16])] = x["clase"]
    nP, dP = int((CL == "P").sum()), int(((CL == "P").any(1)).sum())
    if (nP < CB.MIN_P or dP < CB.MIN_DIAS_P) and not vistazo:
        print(f"criterio S23b §6: {nP} P en {dP} días nuevos; hacen falta {CB.MIN_P} en {CB.MIN_DIAS_P}. No se mide.")
        return
    estat = np.load(CB.ESTAT)
    assert hashlib.sha256(estat.tobytes()).hexdigest()[:16] == CB.SHA_ESTAT
    bt, acm, m1, inst = CB._cubo(dias)
    D = S.Detector(ref="2025", con_blanco=False)
    FD, mm = D._nubes(acm, m1, estat)
    B0 = D.base(None)
    Sx = np.full(CL.shape, np.nan)
    Kx = np.full(CL.shape, -1, int)
    for d in range(len(dias)):
        for s in range(144):
            if FD[d, s] <= B.G_MAX:
                Sx[d, s], Kx[d, s], _ = M.estadistico(mm[d, s] - B0[s])
    _, sl, al = _seco(D, pb)
    r25 = S.azar_por_hora(sl, al)
    U = umbral_pct(D, None, pb)
    out = _resumen(Sx, Kx, CL, range(1, len(dias)), U, r25, lambda d: f"{dias[d]:%Y-%m-%d}")
    te, R, p25, pN = out["P_evaluados"], out["R"], out["p25"], out["pN"]
    if inst["falla"]:
        ver = "INVÁLIDA"
    elif te < CB.MIN_P_EVAL or out["dias_con_P_evaluado"] < 2:
        ver = "NO DECIDIBLE"
    elif p25 <= CB.P25_MAX and R >= CB.R_MIN and pN is not None and pN <= CB.PN_MAX:
        ver = "CONFIRMA"
    elif p25 <= CB.P25_MAX:
        ver = "PARCIAL"
    else:
        ver = "NO CONFIRMA"
    out = {"veredicto": ver if not vistazo else f"VISTAZO (no decide): {ver}", "P_B": pb, "instrumento": inst,
           "P_total": nP, "dias_con_P": dP, **out}
    nombre = "s24c_vistazo.json" if vistazo else "s24c_resultado.json"
    json.dump(out, open(os.path.join(RES, nombre), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps(out, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    c = sys.argv[1]
    if c == "medir":
        medir(vistazo="--vistazo" in sys.argv)
    else:
        {"pruebas": pruebas, "calibrar": calibrar, "desarrollo": desarrollo}[c]()
