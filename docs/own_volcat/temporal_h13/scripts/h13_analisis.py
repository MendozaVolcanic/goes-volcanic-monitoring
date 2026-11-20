"""H13: pareo, variables temporales, AUC con bootstrap por jornada y veredicto (criterio_H13_2026-11-20.md).

Uso: python h13_analisis.py <salida.txt>
Lee <H13DIR>/feat/*.npz (h13_feat.py). Funciones de AUC copiadas de h11_analisis.py (auc, boot_dia, bloque)
con la regla "separa" de H11. Guarda los pares en <H13DIR>/pares_h13.pkl.
"""
import os, sys, pickle
import numpy as np
from datetime import timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import h13_comun as H  # noqa: E402
C = H.C
import rt_e2 as E  # noqa: E402
import huella_png as HP  # noqa: E402
import e2_features as EF  # noqa: E402
from h11_analisis import auc  # noqa: E402

EF.PNGDIRS = EF.PNGDIRS + [H.PNG13]
YS, XS = np.nonzero(E.REG)
NPX = len(YS)
BASE = ("bt11", "btd", "e11", "bt12", "bt85", "bt73")
NOMBRE = {"bt11": "BT11", "btd": "BTD(11-12)", "e11": "eps(11)", "bt12": "beta(12/11)", "bt85": "beta(8,5/11)",
          "bt73": "beta(7,3/11)"}
SIGNO = {"bt11": -1, "btd": -1, "e11": +1, "bt12": -1, "bt85": +1, "bt73": +1}   # lado de la pluma
ES_BETA_BASE = {"bt12", "bt85", "bt73"}
VARS_T = [f"{f}_{b}" for b in BASE for f in ("d1", "d3", "p")]
VARS_S = [f"x_{b}" for b in BASE]
LADO = {}
for b in BASE:
    LADO[f"d1_{b}"] = LADO[f"d3_{b}"] = LADO[f"x_{b}"] = SIGNO[b]; LADO[f"p_{b}"] = 1
ES_BETA = {v for v in VARS_T + VARS_S if v.split("_", 1)[1] in ES_BETA_BASE}

_feat = {}


def feat(dt):
    if dt not in _feat:
        p = os.path.join(H.FEAT13, H.k(dt) + ".npz")
        _feat[dt] = dict(np.load(p, allow_pickle=True)) if os.path.exists(p) else None
    return _feat[dt]


def temporales(t):
    """Variables de un cuadro y temporales por pixel del disco (vector de NPX) para el cuadro t. None si falta algo."""
    F = [feat(t - i * H.M10) for i in range(4)]
    if any(f is None for f in F):
        return None
    out = {}
    for b in BASE:
        X = np.stack([np.asarray(f[b], float) for f in F])          # X[0] = t, X[1] = t-10, ...
        out[f"x_{b}"] = X[0]
        out[f"d1_{b}"] = X[0] - X[1]
        with np.errstate(all="ignore"):
            out[f"d3_{b}"] = X[0] - np.nanmedian(X[1:4], axis=0) if b in ES_BETA_BASE else X[0] - np.median(X[1:4], axis=0)
            if b in ES_BETA_BASE:
                v = np.isfinite(X[1:4]).sum(0) == 0
                out[f"d3_{b}"][v] = np.nan
            d = X[0:3] - X[1:4]                                       # tres cambios de un paso
            lado = (SIGNO[b] * d) > 0
            nv = np.isfinite(d).sum(0)
            out[f"p_{b}"] = np.where(nv > 0, np.where(np.isfinite(d), lado, False).sum(0) / np.maximum(nv, 1), np.nan)
    return out


def huella_full(t):
    """Ceniza VOLCAT en la grilla completa y huella (ceniza a <= 50 km) antes de recortar al disco."""
    ash, fuente = EF.etiqueta(t, "pos")
    return ash.astype(bool), fuente


def mediana_bt11(t, hv_disco):
    f = feat(t)
    if f is None:
        return None
    v = np.asarray(f["bt11"], float)[hv_disco]
    v = v[np.isfinite(v)]
    return float(np.median(v)) if len(v) else None


def armar_pares(ref_lag=0):
    """Pareo: candidato con mediana de BT11 de la huella (en t - ref_lag min) mas cercana, |dif| <= 3 K."""
    P, desc = [], []
    for t in H.anclados():
        ash, fuente = huella_full(t)
        hv_full = ash & (HP.DIST <= 50)
        nfuera = int((hv_full & ~E.REG).sum())
        hv = hv_full & E.REG
        if hv.sum() < 3:
            desc.append((H.k(t), "huella<3px_en_disco", int(hv_full.sum()))); continue
        z = C.zonas(hv, ash)
        hd, ad = hv[YS, XS], (z["an"] & E.REG)[YS, XS]
        Tp = temporales(t)
        if Tp is None:
            desc.append((H.k(t), "pos_sin_historia", 0)); continue
        lag = timedelta(minutes=ref_lag)
        m0 = mediana_bt11(t - lag, hd)
        if m0 is None:
            desc.append((H.k(t), "pos_sin_bt11_ref", 0)); continue
        best = None; ncand = 0
        for c in H.candidatos(t):
            if any(feat(c - i * H.M10) is None for i in range(4)):
                continue
            ncand += 1
            mc = mediana_bt11(c - lag, hd)
            if mc is None:
                continue
            if best is None or abs(mc - m0) < abs(best[1]):
                best = (c, mc - m0)
        if best is None or abs(best[1]) > 3.0:
            desc.append((H.k(t), "sin_control", ncand)); continue
        Tc = temporales(best[0])
        sza = C.sza(t)
        P.append({"pos": H.k(t), "ctrl": H.k(best[0]), "dbt11": best[1], "ncand": ncand, "dia": H.jornada(t),
                  "estrato": "noche" if sza >= 80 else "dia", "npx": int(hv.sum()), "nfuera": nfuera,
                  "nan": int(ad.sum()), "fuente": fuente,
                  "pos_v": {"h": {v: Tp[v][hd] for v in VARS_T + VARS_S}, "an": {v: Tp[v][ad] for v in VARS_T + VARS_S}},
                  "ctrl_v": {"h": {v: Tc[v][hd] for v in VARS_T + VARS_S}, "an": {v: Tc[v][ad] for v in VARS_T + VARS_S}}})
    return P, desc


def pool(R, met, zona):
    x = np.concatenate([r["pos_v"][zona][met] for r in R]) * LADO[met]
    y = np.concatenate([r["ctrl_v"][zona][met] for r in R]) * LADO[met]
    return x, y


def boot_dia(R, met, n=2000, seed=0, q=(2.5, 97.5)):
    rng = np.random.default_rng(seed); dias = sorted({r["dia"] for r in R})
    U = [[r for r in R if r["dia"] == d] for d in dias]; v = []
    for _ in range(n):
        sel = [x for i in rng.integers(0, len(U), len(U)) for x in U[i]]
        v.append(auc(*pool(sel, met, "h")))
    v = np.array(v); v = v[np.isfinite(v)]
    return tuple(float(np.percentile(v, p)) for p in q) if len(v) else (np.nan, np.nan)


def bloque(R, met, boot=True):
    x, y = pool(R, met, "h")
    nx, ny = int(np.isfinite(x).sum()), int(np.isfinite(y).sum())
    if met in ES_BETA and (nx < 20 or ny < 20):
        return {"met": met, "medible": False, "A": np.nan, "nx": nx, "ny": ny, "sep": False}
    A = auc(x, y); Aan = auc(*pool(R, met, "an"))
    lo, hi = boot_dia(R, met) if boot else (np.nan, np.nan)
    dias = sorted({r["dia"] for r in R})
    pd = [(d, auc(*pool([r for r in R if r["dia"] == d], met, "h"))) for d in dias]
    dpos = sum(1 for _, a in pd if np.isfinite(a) and a > 0.5)
    sep = bool(A >= 0.70 and lo > 0.55 and (A - Aan) >= 0.10 and dpos >= 2)
    return {"met": met, "medible": True, "A": A, "lo": lo, "hi": hi, "Aan": Aan, "dpos": dpos, "ndias": len(pd),
            "pd": pd, "sep": sep, "nx": nx, "ny": ny,
            "med": (float(np.nanmedian(x) * LADO[met]) if nx else np.nan, float(np.nanmedian(y) * LADO[met]) if ny else np.nan)}


def linea(b):
    if not b["medible"]:
        return f"  {b['met']:9s} no medible (validos {b['nx']}/{b['ny']})"
    return (f"  {b['met']:9s} AUC={b['A']:.3f} IC95dia=[{b['lo']:.3f},{b['hi']:.3f}] anillo={b['Aan']:.3f} "
            f"h-an={b['A'] - b['Aan']:+.3f} dias>0,5={b['dpos']}/{b['ndias']} | mediana pos/ctrl "
            f"{b['med'][0]:+.3f}/{b['med'][1]:+.3f} (n {b['nx']}/{b['ny']}) | SEPARA={b['sep']}")


def estratos(R, met):
    out = {}
    for e in ("dia", "noche"):
        S = [r for r in R if r["estrato"] == e]
        if not S:
            out[e] = (0, np.nan); continue
        x, y = pool(S, met, "h")
        ok = not (met in ES_BETA and (np.isfinite(x).sum() < 20 or np.isfinite(y).sum() < 20))
        out[e] = (len(S), auc(x, y) if ok else np.nan)
    return out


def arranque(P):
    """Cuadros de arranque (regla H7: el cuadro VOLCAT anterior publicado, a 10 o 20 min, sin objeto a <= 50 km)
    y los 2 cuadros anclados que les siguen."""
    anc = H.anclados(); sel = set()
    for i, t in enumerate(anc):
        prev = C._INV.get(t - H.M10) or C._INV.get(t - 2 * H.M10)
        if prev is None or prev["n50"] == 0:
            for j in range(i, min(i + 3, len(anc))):
                sel.add(H.k(anc[j]))
    return [p for p in P if p["pos"] in sel]


def informe(P, desc, titulo, boot=True):
    L = [f"=== {titulo}", f"pares {len(P)} | jornadas {len({p['dia'] for p in P})} | "
         f"dia {sum(p['estrato'] == 'dia' for p in P)} noche {sum(p['estrato'] == 'noche' for p in P)}"]
    res = {}
    L.append("-- variables temporales (deciden)")
    for v in VARS_T:
        b = bloque(P, v, boot); b["estr"] = estratos(P, v); res[v] = b
        L.append(linea(b) + "  | estratos " + " ".join(f"{e} n={n} AUC={a:.3f}" for e, (n, a) in b["estr"].items()))
    L.append("-- un solo cuadro X(t), referencia (no decide)")
    for v in VARS_S:
        b = bloque(P, v, boot); res[v] = b; L.append(linea(b))
    return L, res


def veredicto(P, res):
    if len(P) < 30 or len({p["dia"] for p in P}) < 4:
        return "NO CONCLUYENTE (menos de 30 pares o menos de 4 jornadas)", []
    sep = []
    for v in VARS_T:
        b = res[v]
        if b["sep"] and all(a > 0.5 for (n, a) in b["estr"].values() if n >= 10 and np.isfinite(a)):
            sep.append(v)
    if sep:
        return "H13 SE SOSTIENE (separan: " + ", ".join(sep) + ")", sep
    mx = max((res[v]["A"] for v in VARS_T if res[v]["medible"]), default=np.nan)
    if not (mx >= 0.60):
        return f"H13 SE FALSA (AUC maximo de las 18 variables temporales = {mx:.3f} < 0,60)", []
    return f"NO CONCLUYENTE (AUC maximo {mx:.3f} >= 0,60 pero ninguna variable separa con la regla de H11)", []


if __name__ == "__main__":
    out = sys.argv[1]
    P, desc = armar_pares(0)
    pickle.dump({"P": P, "desc": desc}, open(os.path.join(H.H13DIR, "pares_h13.pkl"), "wb"))
    L = [f"H13 cambio entre cuadros consecutivos. Cuadros anclados {len(H.anclados())}; pares ok {len(P)}; descartados {len(desc)}"]
    from collections import Counter
    L.append("  descartes: " + str(Counter(d[1] for d in desc)))
    for d in desc:
        L.append(f"    {d}")
    L.append(f"  pixeles de huella a <= 50 km fuera del disco de 40 km: {sum(p['nfuera'] for p in P)} "
             f"(dentro: {sum(p['npx'] for p in P)})")
    L.append(f"  |dif BT11| de los pares: mediana {np.median([abs(p['dbt11']) for p in P]):.2f} K; "
             f"candidatos con historia por cuadro: mediana {np.median([p['ncand'] for p in P]):.0f}")
    L.append("  por jornada: " + "; ".join(f"{d} {sum(p['dia'] == d for p in P)}" for d in sorted({p['dia'] for p in P})))
    L.append("  pares: " + "; ".join(f"{p['pos']}->{p['ctrl']} ({p['dbt11']:+.1f} K, {p['npx']} px, {p['estrato']})" for p in P))
    Lm, res = informe(P, desc, "Principal (pareo por BT11 en t)")
    L += Lm
    ver, sep = veredicto(P, res)
    L.append("VEREDICTO: " + ver)
    for v in sep:
        lo, hi = boot_dia(P, v, q=(0.15, 99.85))
        L.append(f"  multiplicidad {v}: IC 99,7 % = [{lo:.3f}, {hi:.3f}] -> sobrevive: {lo > 0.55}")
    # sensibilidades
    P30, d30 = armar_pares(30)
    Ls, r30 = informe(P30, d30, "Sensibilidad (a): pareo por BT11 de la huella en t - 30 min (no decide)")
    L += Ls + ["  veredicto que daria: " + veredicto(P30, r30)[0]]
    Pa = arranque(P)
    La, ra = informe(Pa, [], "Sensibilidad (b): solo cuadros de arranque y sus 2 siguientes (no decide)")
    L += La + ["  veredicto que daria: " + veredicto(Pa, ra)[0]]
    txt = "\n".join(L)
    open(out, "w", encoding="utf-8").write(txt)
    print(txt)
