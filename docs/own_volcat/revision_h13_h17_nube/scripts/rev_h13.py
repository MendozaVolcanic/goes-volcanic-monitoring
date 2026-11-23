r"""Revision H13 (S19e, criterio ../criterio_2026-11-23.md §3.2): ¿los pares de H13 cayeron en cielos distintos?

Lee los 72 pares de H13 (D:\goes_cache\h13\pares_h13.pkl, con las variables por pixel ya calculadas), mira la
mascara de nubes de NOAA en los cuatro cuadros (t, t-10, t-20, t-30 min) del positivo y del control, y rehace el
AUC de las 18 variables temporales en los pares "despejado" (los ocho cuadros en escena despejada) y, como lectura,
en los pares "mismo cielo". Funciones auc, pool, boot_dia, bloque, estratos y veredicto copiadas SIN CAMBIOS de
temporal_h13/scripts/h13_analisis.py (y auc de reproducir_volcat/scripts/h11_analisis.py) para no importar su
cadena de dependencias. Nulo: 2.000 subconjuntos al azar del mismo tamano (semilla 20261123).
Escribe (repo) ../resultados/rev_h13_resultado.txt. Uso, desde scripts\: python -I rev_h13.py
"""
import os
import pickle
import sys
from datetime import datetime, timedelta

import numpy as np
from scipy.stats import rankdata

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import rev_comun as R  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
RES = os.path.join(os.path.dirname(AQUI), "resultados")
PARES = r"D:\goes_cache\h13\pares_h13.pkl"
SEMILLA, NNULO = 20261123, 2000

BASE = ("bt11", "btd", "e11", "bt12", "bt85", "bt73")
SIGNO = {"bt11": -1, "btd": -1, "e11": +1, "bt12": -1, "bt85": +1, "bt73": +1}
ES_BETA_BASE = {"bt12", "bt85", "bt73"}
VARS_T = [f"{f}_{b}" for b in BASE for f in ("d1", "d3", "p")]
LADO = {}
for b in BASE:
    LADO[f"d1_{b}"] = LADO[f"d3_{b}"] = LADO[f"x_{b}"] = SIGNO[b]
    LADO[f"p_{b}"] = 1
ES_BETA = {v for v in VARS_T if v.split("_", 1)[1] in ES_BETA_BASE}


def auc(x, y):
    x = np.asarray(x, float); y = np.asarray(y, float); x = x[np.isfinite(x)]; y = y[np.isfinite(y)]
    if len(x) == 0 or len(y) == 0:
        return np.nan
    r = rankdata(np.concatenate([x, y]))
    return (r[:len(x)].sum() - len(x) * (len(x) + 1) / 2) / (len(x) * len(y))


def pool(R_, met, zona):
    x = np.concatenate([r["pos_v"][zona][met] for r in R_]) * LADO[met]
    y = np.concatenate([r["ctrl_v"][zona][met] for r in R_]) * LADO[met]
    return x, y


def boot_dia(R_, met, n=2000, seed=0, q=(2.5, 97.5)):
    rng = np.random.default_rng(seed); dias = sorted({r["dia"] for r in R_})
    U = [[r for r in R_ if r["dia"] == d] for d in dias]; v = []
    for _ in range(n):
        sel = [x for i in rng.integers(0, len(U), len(U)) for x in U[i]]
        v.append(auc(*pool(sel, met, "h")))
    v = np.array(v); v = v[np.isfinite(v)]
    return tuple(float(np.percentile(v, p)) for p in q) if len(v) else (np.nan, np.nan)


def bloque(R_, met, boot=True):
    x, y = pool(R_, met, "h")
    nx, ny = int(np.isfinite(x).sum()), int(np.isfinite(y).sum())
    if met in ES_BETA and (nx < 20 or ny < 20):
        return {"met": met, "medible": False, "A": np.nan, "nx": nx, "ny": ny, "sep": False}
    A = auc(x, y); Aan = auc(*pool(R_, met, "an"))
    lo, hi = boot_dia(R_, met) if boot else (np.nan, np.nan)
    dias = sorted({r["dia"] for r in R_})
    pd_ = [(d, auc(*pool([r for r in R_ if r["dia"] == d], met, "h"))) for d in dias]
    dpos = sum(1 for _, a in pd_ if np.isfinite(a) and a > 0.5)
    sep = bool(A >= 0.70 and lo > 0.55 and (A - Aan) >= 0.10 and dpos >= 2)
    return {"met": met, "medible": True, "A": A, "lo": lo, "hi": hi, "Aan": Aan, "dpos": dpos, "ndias": len(pd_),
            "sep": sep, "nx": nx, "ny": ny}


def estratos(R_, met):
    out = {}
    for e in ("dia", "noche"):
        S = [r for r in R_ if r["estrato"] == e]
        if not S:
            out[e] = (0, np.nan); continue
        x, y = pool(S, met, "h")
        ok = not (met in ES_BETA and (np.isfinite(x).sum() < 20 or np.isfinite(y).sum() < 20))
        out[e] = (len(S), auc(x, y) if ok else np.nan)
    return out


def veredicto(P, res):
    if len(P) < 30 or len({p["dia"] for p in P}) < 4:
        return "NO CONCLUYENTE (menos de 30 pares o menos de 4 jornadas)", [], np.nan
    sep = [v for v in VARS_T if res[v]["sep"] and all(a > 0.5 for (n, a) in res[v]["estr"].values()
                                                     if n >= 10 and np.isfinite(a))]
    mx = max((res[v]["A"] for v in VARS_T if res[v]["medible"]), default=np.nan)
    if sep:
        return "H13 SE SOSTIENE (separan: " + ", ".join(sep) + ")", sep, mx
    if not (mx >= 0.60):
        return f"H13 SE FALSA (AUC maximo de las 18 variables temporales = {mx:.3f} < 0,60)", [], mx
    return f"NO CONCLUYENTE (AUC maximo {mx:.3f} >= 0,60 pero ninguna variable separa)", [], mx


def maximo(P):
    vals = [bloque(P, v, boot=False)["A"] for v in VARS_T]
    vals = [a for a in vals if np.isfinite(a)]
    return max(vals) if vals else np.nan


def informe(P, titulo, L):
    L.append(f"=== {titulo}: pares {len(P)} | jornadas {len({p['dia'] for p in P})} | dia "
             f"{sum(p['estrato'] == 'dia' for p in P)} noche {sum(p['estrato'] == 'noche' for p in P)}")
    if not P:
        return {}, ("SIN PARES", [], np.nan)
    res = {}
    for v in VARS_T:
        b = bloque(P, v)
        b["estr"] = estratos(P, v)
        res[v] = b
        if b["medible"]:
            L.append(f"  {v:9s} AUC={b['A']:.3f} IC95dia=[{b['lo']:.3f},{b['hi']:.3f}] anillo={b['Aan']:.3f} "
                     f"dias>0,5={b['dpos']}/{b['ndias']} SEPARA={b['sep']}")
        else:
            L.append(f"  {v:9s} no medible ({b['nx']}/{b['ny']})")
    ver = veredicto(P, res)
    L.append("  veredicto con la regla de H13: " + ver[0])
    return res, ver


def k(dt):
    return f"{dt:%Y%m%d_%H%M}"


def tiempos(clave):
    t = datetime.strptime(clave, "%Y%m%d_%H%M")
    return [k(t - timedelta(minutes=m)) for m in (0, 10, 20, 30)]


def main():
    d = pickle.load(open(PARES, "rb"))
    P, desc = d["P"], d["desc"]
    L = [f"Revision H13 (S19e), pares contra la mascara de nubes de NOAA. Generado {datetime.now():%Y-%m-%d %H:%M}"]
    sin_acm = 0
    for p in P:
        ep = [R.estado(c) for c in tiempos(p["pos"])]
        ec = [R.estado(c) for c in tiempos(p["ctrl"])]
        sin_acm += sum(not x[0] for x in ep + ec)
        p["esc_pos"] = [x[2] for x in ep]
        p["esc_ctrl"] = [x[2] for x in ec]
        p["fb_pos"], p["fb_ctrl"] = ep[0][1], ec[0][1]
        p["despejado"] = all(p["esc_pos"]) and all(p["esc_ctrl"])
        p["mismo"] = p["esc_pos"] == p["esc_ctrl"]
    n = len(P)
    F13 = 1 - np.mean([p["mismo"] for p in P])
    L.append(f"pares {n} | cuadros sin ACMF {sin_acm} de {8 * n}")
    L.append(f"escena despejada en t: positivos {np.mean([p['esc_pos'][0] for p in P]):.3f}, controles "
             f"{np.mean([p['esc_ctrl'][0] for p in P]):.3f} | fraccion de terreno bajo despejado en t (mediana): "
             f"positivos {np.nanmedian([p['fb_pos'] for p in P]):.3f}, controles {np.nanmedian([p['fb_ctrl'] for p in P]):.3f}")
    L.append(f"F13 (pares con positivo y control en cielos distintos en algun tiempo): {F13:.3f} "
             f"({sum(not p['mismo'] for p in P)} de {n})")
    L.append(f"pares 'despejado' (8 cuadros despejados): {sum(p['despejado'] for p in P)} | 'mismo cielo': "
             f"{sum(p['mismo'] for p in P)}")

    res0, ver0 = informe(P, "Todos los pares (linea base roja: tiene que dar el maximo 0,582 de H13)", L)

    rng = np.random.default_rng(SEMILLA)
    for nombre, sub in (("despejado", [p for p in P if p["despejado"]]), ("mismo cielo", [p for p in P if p["mismo"]])):
        res, ver = informe(sub, f"Pares '{nombre}' ({'decide' if nombre == 'despejado' else 'lectura'})", L)
        if len(sub) >= 2:
            nulo = [maximo([P[j] for j in rng.choice(n, len(sub), replace=False)]) for _ in range(NNULO)]
            p95 = float(np.nanpercentile(nulo, 95))
            L.append(f"  nulo: maximo de las 18 en {NNULO} subconjuntos al azar de {len(sub)} pares: mediana "
                     f"{np.nanmedian(nulo):.3f}, p95 {p95:.3f}; maximo observado {ver[2]:.3f} -> "
                     f"{'sobre' if ver[2] > p95 else 'dentro de'} el p95")

    # informativo: los cuadros sin control
    sc = [x for x in desc if x[1] == "sin_control"]
    L.append(f"\n== Informativo: {len(sc)} cuadros sin control ==")
    for clave, _, nc in sc:
        t = datetime.strptime(clave, "%Y%m%d_%H%M")
        e0 = R.estado(clave)
        cand = []
        for dd in range(-10, 11):
            u = t + timedelta(days=dd)
            if (u - timedelta(hours=3)).date() == (t - timedelta(hours=3)).date():
                continue
            if datetime(2026, 10, 20) <= u <= datetime(2026, 11, 19, 23, 59):
                cand.append(R.estado(k(u)))
        fr = np.mean([c[2] for c in cand if c[0]]) if any(c[0] for c in cand) else np.nan
        L.append(f"  {clave}: escena del positivo {'despejada' if e0[2] else 'no despejada'} (terreno bajo "
                 f"{e0[1]:.2f}); mismo minuto en +-10 dias: {fr:.2f} de escenas despejadas (n {len(cand)})")
    open(os.path.join(RES, "rev_h13_resultado.txt"), "w", encoding="utf-8").write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
