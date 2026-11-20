"""Etapa 2: SECO propio entrenado con VOLCAT como etiqueta, validado dejando una jornada afuera.

Uso: python e2_clasificador.py <salida.txt>
Criterio: docs/own_volcat/reproducir_volcat/criterio_E2_2026-11-20.md. Lee <TRABAJO>/feat_e2/*.npz.

Cadena (SECO Parte 1 y 2, todo lo publico; lo que no es publico se aprende de VOLCAT):
1. Probabilidad por pixel: Bayes ingenuo con los tres clasificadores de SECO 1 Tabla 3 que ABI tiene siempre
   (eps_tot x beta_tot(12/11) x beta_tot(8,5/11); eps_tot x beta_opaque(12/11) x beta_opaque(8,5/11);
   eps_tot x beta_tot(12/11) x beta_tot(7,3/11)), bins de SECO 1, prior 0,1 %. Solo pixeles que pasan los
   prefiltros reciben probabilidad.
2. Miembros de objeto: pixeles con probabilidad (A6 con carga de ceniza < 1 g/m2, supuesta en todos).
3. Objetos: componentes conexas (8 vecinos). Bandera CF (SECO 2 sec. 4.3). Robustez RR (SECO 2 Tabla 3 y
   ec. 4) con histograma de 8 dimensiones armado con el entrenamiento.
4. Seleccion: Tabla 4 de SECO 2 completa (filas generales y V50/V10/V5 por distancia del centro al crater).
5. Deteccion del scan: un objeto seleccionado con al menos un pixel a <= 10 km del crater.
Variante informativa (no decide): bosque aleatorio con todas las variables por pixel.
"""
import os, sys, glob, pickle
import numpy as np
from datetime import timedelta
from scipy import ndimage

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import comun_h11 as C  # noqa: E402

FEAT = os.path.join(C.TRABAJO, "feat_e2")
PRIOR = 0.001
NY, NX = C.LAT.shape

# ---------------------------------------------------------------- bins (SECO 1 sec. 4.2 y Tabla 3)
B_EPS = np.array([0.01, 0.03, 0.10, 0.20, 0.50, 0.90])
B_B12 = np.arange(-0.10, 1.95 + 1e-9, 0.05)
B_B85 = np.arange(-0.10, 1.90 + 1e-9, 0.10)
CLASIF = (("e11", "bt12", "bt85"), ("e11", "bo12", "bo85"), ("e11", "bt12", "bt73"))
BINS = {"e11": B_EPS, "bt12": B_B12, "bo12": B_B12, "bt85": B_B85, "bo85": B_B85, "bt73": B_B85}
# Tabla 3 de SECO 2 (estado de 8 dimensiones para la robustez)
T3 = {"btclr11": [160, 250, 270, 290], "e11": [0.00, 0.05, 0.08, 0.10, 0.20, 0.40, 0.60, 0.80],
      "btsd": [0.00, 0.50, 1.00, 2.00, 5.00, 10.00],
      "btd": [-50, -25, -2.5, -2.0, -1.5, -1.0, -0.75, -0.5, -0.25, -0.10, 0.0, 0.25, 0.50, 1.00],
      "btd85_12": [-50, -25, -1.5, -1.25, -1.0, -0.75, -0.5, -0.25, 0.0, 0.25, 0.5],
      "bt73": [0.00, 0.10, 1.50, 1.80, 2.00], "bt85": [0.00, 0.10, 0.80, 0.90, 1.00, 1.50, 1.80, 2.00],
      "P": [0, 10, 50, 90, 99, 99.9, 99.99, 99.999, 99.9999, 99.999999]}
# Tabla 4 de SECO 2: min, max, med, obj, CF, RR4ct, RR4fr, RR3ct, RR3fr, RR2ct, RR2fr, RR1ct, RR1fr, zona
INF = np.inf
T4 = [(25, INF, 0, 80, 2, 4, 0, 14, 0, 0, 0, 0, 0, None), (25, INF, 80, 0, 2, 4, 0, 14, 0, 0, 0, 0, 0, None),
      (250, INF, 0, 80, 2, 0, .01, 0, 0, 0, 0, 0, 0, None), (250, INF, 80, 0, 2, 0, .01, 0, 0, 0, 0, 0, 0, None),
      (100, INF, 0, 80, 2, 0, .005, 0, .01, 0, 0, 0, 0, None), (100, INF, 80, 0, 2, 0, .005, 0, .01, 0, 0, 0, 0, None),
      (5000, INF, 20, 99, 2, -1, -.1, -1, -.1, 10, 0, 3000, 0, None),
      (250, INF, 0, 80, 0, 100, 0, 0, 0, 0, 0, 0, 0, None), (250, INF, 80, 0, 0, 100, 0, 0, 0, 0, 0, 0, 0, None),
      (500, INF, 0, 80, 0, 0, 0, 500, 0, 0, 0, 0, 0, None), (500, INF, 80, 0, 0, 0, 0, 500, 0, 0, 0, 0, 0, None),
      (100, 1000, 80, 80, 2, -1, -.1, 0, .01, 0, .0133, 0, .05, None),
      (250, 500, 0, 80, 2, 0, 0, 0, .0055, 0, .0133, 0, .05, None), (250, 500, 80, 0, 2, 0, 0, 0, .0055, 0, .0133, 0, .05, None),
      (100, 250, 0, 80, 2, 0, .005, 0, .01, 0, 0, 0, 0, None), (100, 250, 80, 0, 2, 0, .005, 0, .01, 0, 0, 0, 0, None),
      (25, 250, 0, 80, 2, 0, 0, 0, 0, 0, .0133, 0, .05, None), (25, 250, 80, 0, 2, 0, 0, 0, 0, 0, .0133, 0, .05, None),
      (15, 25, 80, 80, 2, 4, 0, 14, 0, 0, 0, 0, 0, None), (10, 25, 80, 80, 2, 0, 0, 0, 0, 0, .0133, 0, .05, None),
      (10, 25, 80, 0, 3, -1, -.1, -1, -.1, 0, .25, 0, .5, 50), (10, 25, 80, 80, 3, -1, -.1, -1, -.1, 0, .10, 0, .5, 50),
      (0, 10, 80, 0, 3, -1, -.1, -1, -.1, 0, .25, 0, .5, 50), (0, 10, 80, 80, 3, -1, -.1, -1, -.1, 0, .10, 0, .5, 50),
      (10, 25, 0, 80, 3, 0, 0, 0, 0, 0, .0133, 0, .05, 10), (10, 25, 80, 0, 3, 0, 0, 0, 0, 0, .0133, 0, .05, 10),
      (0, 10, 80, 0, 3, 0, 0, 0, 0, 0, .0133, 0, .05, 5), (0, 10, 0, 80, 3, 0, 0, 0, 0, 0, .0133, 0, .05, 5)]


def jornada(dt):
    return f"{dt - timedelta(hours=3):%Y%m%d}"


# ---------------------------------------------------------------- datos
def cargar():
    S = []
    for f in sorted(glob.glob(os.path.join(FEAT, "*.npz"))):
        kk = os.path.basename(f)[:13]; dt = C.dtk(kk)
        z = dict(np.load(f, allow_pickle=True)); tipo = str(z["tipo"])
        if tipo == "neg" and not C._limpio(dt):
            continue                       # negativo a menos de 60 min de un objeto VOLCAT: fuera (criterio)
        z["kk"] = kk; z["dt"] = dt; z["tipo"] = tipo; z["jor"] = jornada(dt)
        S.append(z)
    return S


def idx(v, edges):
    """Bin con limites de inicio; NaN e invalidos al primer bin (SECO 1)."""
    v = np.where(np.isfinite(v), v, -np.inf)
    return np.clip(np.searchsorted(edges, v, side="right") - 1, 0, len(edges) - 1)


def celdas(z, clas):
    a, b, c = clas
    ia, ib, ic = idx(z[a], BINS[a]), idx(z[b], BINS[b]), idx(z[c], BINS[c])
    return (ia * len(BINS[b]) + ib) * len(BINS[c]) + ic


def ncel(clas):
    return int(np.prod([len(BINS[k]) for k in clas]))


def entrenar(S):
    """Histogramas por clasificador: pixeles con prefiltro, positivos = ceniza VOLCAT en scans positivos,
    negativos = todo el disco en scans negativos."""
    H = []
    for clas in CLASIF:
        hp = np.zeros(ncel(clas)); hn = np.zeros(ncel(clas))
        for z in S:
            m = z["pre"].astype(bool)
            if z["tipo"] == "pos":
                c = celdas(z, clas)[m & z["ash"]]; hp += np.bincount(c, minlength=len(hp))
            elif z["tipo"] == "neg":
                c = celdas(z, clas)[m]; hn += np.bincount(c, minlength=len(hn))
        Np, Nn = max(hp.sum(), 1), max(hn.sum(), 1)
        lr = ((hp + 0.5) / Np) / ((hn + 0.5) / Nn)
        lr[(hp + hn) < 5] = 1.0             # celdas casi vacias: vuelve al prior (SECO 1)
        H.append(lr)
    return H


def prob(z, H):
    odds = np.full(len(z["e11"]), PRIOR / (1 - PRIOR))
    for clas, lr in zip(CLASIF, H):
        odds = odds * lr[celdas(z, clas)]
    p = 100 * odds / (1 + odds)
    return np.where(z["pre"].astype(bool), p, np.nan)


def estado8(z, P):
    keys = ("btclr11", "e11", "btsd", "btd", "btd85_12", "bt73", "bt85")
    s = np.zeros(len(P), np.int64)
    for k in keys:
        s = s * len(T3[k]) + idx(z[k], np.array(T3[k], float))
    return s * len(T3["P"]) + idx(np.nan_to_num(P, nan=0.0), np.array(T3["P"], float))


def robustez_tabla(S, Hs):
    """RR por estado de 8 dimensiones (ec. 4), con la probabilidad del modelo sobre el propio entrenamiento."""
    na, no = {}, {}
    for z, H in zip(S, Hs):
        P = prob(z, H); s = estado8(z, P)
        if z["tipo"] == "pos":
            u, c = np.unique(s[z["ash"]], return_counts=True)
            for a, b in zip(u, c):
                na[a] = na.get(a, 0) + b
        elif z["tipo"] == "neg":
            u, c = np.unique(s, return_counts=True)
            for a, b in zip(u, c):
                no[a] = no.get(a, 0) + b
    RR = {}
    for st in set(na) | set(no):
        a, o = na.get(st, 0), no.get(st, 0); r = o / (a + o)
        if a > 5 and o == 0:
            v = 4
        elif (a > 1 and o < 2) or (a > 5 and o < 50 and r < 0.01) or (a > 5 and o < 10 and r < 0.10):
            v = 3
        elif (a > 0 and o < 10) or (a > 5 and 50 <= o < 100 and r < 0.01) or (a > 5 and 10 <= o < 50 and r < 0.10):
            v = 2
        elif (a > 0 and o < 100) or (a > 5 and o < 500 and r < 0.50):
            v = 1
        else:
            v = 0
        RR[st] = v
    return RR


# ---------------------------------------------------------------- objetos y seleccion
def grid(z, v, fill=np.nan):
    g = np.full((NY, NX), fill, dtype=float); g[z["ys"], z["xs"]] = v; return g


def objetos(z, P, RR, E11):
    memb = grid(z, np.isfinite(P).astype(float), 0) > 0
    lab, n = ndimage.label(memb, structure=np.ones((3, 3), int))
    if n == 0:
        return [], lab
    Pg = grid(z, P); bb = grid(z, z["btclr11"] - z["bt11"]); bt11 = grid(z, z["bt11"])
    rr = grid(z, np.array([RR.get(s, 0) for s in estado8(z, P)], float), 0)
    dist = grid(z, z["dist"], np.inf); reg = grid(z, np.ones(len(P)), 0) > 0
    out = []
    for i in range(1, n + 1):
        m = lab == i; size = int(m.sum()); pv = Pg[m]
        low = m & (Pg < 10)
        bobj = np.nanmean(bb[low]) if low.any() else np.nanmean(bb[m])
        ring = ndimage.binary_dilation(m, np.ones((25, 25), bool)) & ~memb & reg
        if E11 is not None:
            ring &= bt11 >= E11 - 3.0
        benv = np.nanmean(bb[ring]) if ring.any() else np.nan
        if np.isfinite(bobj) and np.isfinite(benv):
            d = bobj - benv; cf = 3 if (bobj > 18 or d > 6) else 2 if d > 4 else 1 if d > 2 else 0
        else:
            cf = 0
        r = rr[m]; cy, cx = ndimage.center_of_mass(m)
        dc = float(dist[int(round(cy)), int(round(cx))])
        out.append({"i": i, "size": size, "med": float(np.nanmedian(pv)), "cf": cf, "dcen": dc,
                    "dmin": float(dist[m].min()),
                    "ct": [int((r >= k).sum()) for k in (4, 3, 2, 1)], "fr": [float((r >= k).mean()) for k in (4, 3, 2, 1)]})
    return out, lab


def seleccion(o):
    for (mn, mx, med, obj, cf, c4, f4, c3, f3, c2, f2, c1, f1, zona) in T4:
        if zona is not None and not (o["dcen"] <= zona):
            continue
        if obj > 0:            # probabilidad de objeto no reproducible (criterio): filas que la exigen no se cumplen
            continue
        if not (o["size"] > mn and o["size"] <= mx and o["med"] > med and o["cf"] >= cf):
            continue
        ct, fr = o["ct"], o["fr"]
        if ct[0] > c4 and fr[0] > f4 and ct[1] > c3 and fr[1] > f3 and ct[2] > c2 and fr[2] > f2 and ct[3] > c1 and fr[3] > f1:
            return True
    return False


def empirico(S, z):
    """Cielo empirico para la prueba de nube del anillo: 3 escenas negativas mas tibias de otras jornadas
    a +-30 min del mismo minuto UTC del dia; mediana. Con menos de 5, sin filtro."""
    t = z["dt"].hour * 60 + z["dt"].minute
    cand = [w for w in S if w["tipo"] == "neg" and w["jor"] != z["jor"] and abs((w["dt"].hour * 60 + w["dt"].minute) - t) <= 30]
    if len(cand) < 5:
        return None
    st = np.stack([grid(w, w["bt11"]) for w in cand]); st = np.where(np.isfinite(st), st, -1e9)
    return np.median(np.sort(st, axis=0)[::-1][:3], axis=0)


# ---------------------------------------------------------------- validacion
def correr(S):
    jors = sorted({z["jor"] for z in S})
    res = []
    for j in jors:
        tr = [z for z in S if z["jor"] != j and z["tipo"] != "manto"]
        te = [z for z in S if z["jor"] == j]
        H = entrenar(tr); RR = robustez_tabla(tr, [H] * len(tr))
        for z in te:
            P = prob(z, H); objs, lab = objetos(z, P, RR, empirico(S, z))
            sel = [o for o in objs if seleccion(o)]
            anc = [o for o in sel if o["dmin"] <= 10]
            mios = np.zeros((NY, NX), bool)
            for o in sel:
                mios |= lab == o["i"]
            ash = grid(z, z["ash"].astype(float), 0) > 0
            ashd = ndimage.binary_dilation(ash, np.ones((3, 3), bool))
            d30 = grid(z, z["dist"], np.inf) <= 30
            res.append({"kk": z["kk"], "jor": j, "tipo": z["tipo"], "det": len(anc) > 0, "n_obj": len(objs), "n_sel": len(sel),
                        "pre_ash": float(np.mean(z["pre"][z["ash"]])) if z["ash"].any() else np.nan,
                        "n_pre": int(z["pre"].sum()), "mios30": int((mios & d30).sum()), "coinc30": int((mios & d30 & ashd).sum()),
                        "obj_anc": [(o["size"], round(o["med"], 2), o["cf"], o["ct"]) for o in objs if o["dmin"] <= 10][:5]})
        print("jornada", j, "test", len(te), "detecciones", sum(r["det"] for r in res if r["jor"] == j), flush=True)
    return res


def vara(res, nombre):
    pos = [r for r in res if r["tipo"] == "pos"]; neg = [r for r in res if r["tipo"] == "neg"]; man = [r for r in res if r["tipo"] == "manto"]
    sens = np.mean([r["det"] for r in pos]) if pos else np.nan
    fa = np.mean([r["det"] for r in neg]) if neg else np.nan
    fa_j = {}
    for r in neg:
        fa_j[r["jor"]] = fa_j.get(r["jor"], 0) + int(r["det"])
    maxj = max(fa_j.values()) if fa_j else 0
    fm = np.mean([r["det"] for r in man]) if man else np.nan
    m30 = sum(r["mios30"] for r in pos); c30 = sum(r["coinc30"] for r in pos)
    co = c30 / m30 if m30 else np.nan
    ok = [sens >= 0.5, fa <= 0.02 and maxj <= 3, (fm <= 0.10) if man else False, co >= 0.5 if m30 else False]
    L = [f"== {nombre}",
         f"  1 sensibilidad: {sum(r['det'] for r in pos)}/{len(pos)} = {sens:.3f} (pide >= 0,50) -> {ok[0]}",
         f"  2 falsa alarma: {sum(r['det'] for r in neg)}/{len(neg)} = {fa:.4f} (pide <= 0,02), max por jornada {maxj} (pide <= 3) -> {ok[1]}",
         f"  3 manto 16-11: {sum(r['det'] for r in man)}/{len(man)} = {fm:.3f} (pide <= 0,10) -> {ok[2]}",
         f"  4 coincidencia: {c30}/{m30} = {co:.3f} (pide >= 0,50) -> {ok[3]}",
         f"  CUMPLE: {all(ok)}"]
    pj = {}
    for r in pos:
        pj.setdefault(r["jor"], [0, 0]); pj[r["jor"]][0] += int(r["det"]); pj[r["jor"]][1] += 1
    L.append("  sensibilidad por jornada: " + "; ".join(f"{j} {a}/{b}" for j, a, b in [(k, *v) for k, v in sorted(pj.items())]))
    return "\n".join(L), all(ok)


def diagnostico(res, S):
    pos = [r for r in res if r["tipo"] == "pos"]
    L = ["== Diagnostico de la cadena en los positivos (no decide)"]
    npx = sum(int(z["ash"].sum()) for z in S if z["tipo"] == "pos")
    npre = sum(int(z["pre"][z["ash"]].sum()) for z in S if z["tipo"] == "pos")
    L.append(f"  pixeles de ceniza VOLCAT en el disco de 40 km: {npx}; con prefiltros SECO: {npre} ({npre / max(npx, 1):.3f})")
    L.append(f"  scans positivos con algun objeto (cualquier tamano) a <= 10 km: {sum(1 for r in pos if r['obj_anc'])}/{len(pos)}")
    neg = [z for z in S if z["tipo"] == "neg"]
    fr = np.mean([z["pre"].mean() for z in neg]); L.append(f"  fraccion de pixeles con prefiltros en scans negativos: {fr:.3f}")
    return "\n".join(L)


VARS_RF = ("e11", "e12", "e85", "e73", "bt12", "bo12", "bt85", "bo85", "bt73", "btd", "btd_bias", "btd85_12",
           "btsd", "btclr11", "bt11", "dist", "pre", "a5")


def X_de(z):
    X = np.stack([np.asarray(z[k], float) for k in VARS_RF], 1)
    return np.where(np.isfinite(X), X, -999.0)


def det_rf(z, p, thr):
    m = grid(z, (p > thr).astype(float), 0) > 0
    lab, n = ndimage.label(m, structure=np.ones((3, 3), int))
    dist = grid(z, z["dist"], np.inf); keep = np.zeros_like(m)
    det = False
    for i in range(1, n + 1):
        o = lab == i
        if o.sum() >= 2:
            keep |= o
            if dist[o].min() <= 10:
                det = True
    return det, keep


def correr_rf(S, seed=0):
    """Variante informativa: bosque aleatorio por pixel; umbral por pliegue = el mas bajo que da <= 2 % de
    falsa alarma en los negativos de entrenamiento (prediccion fuera de bolsa por jornada dentro del pliegue
    seria lo ideal; aqui se usa la prediccion sobre el propio entrenamiento, que es optimista para el umbral)."""
    from sklearn.ensemble import RandomForestClassifier
    jors = sorted({z["jor"] for z in S}); res = []
    rng = np.random.default_rng(seed)
    for j in jors:
        tr = [z for z in S if z["jor"] != j and z["tipo"] != "manto"]; te = [z for z in S if z["jor"] == j]
        Xp = np.concatenate([X_de(z)[z["ash"]] for z in tr if z["tipo"] == "pos"])
        Xn = np.concatenate([X_de(z) for z in tr if z["tipo"] == "neg"])
        if len(Xn) > 400000:
            Xn = Xn[rng.choice(len(Xn), 400000, replace=False)]
        X = np.concatenate([Xp, Xn]); y = np.r_[np.ones(len(Xp)), np.zeros(len(Xn))]
        rf = RandomForestClassifier(300, min_samples_leaf=20, class_weight="balanced", n_jobs=6, random_state=seed).fit(X, y)
        negs = [z for z in tr if z["tipo"] == "neg"]
        pn = [rf.predict_proba(X_de(z))[:, 1] for z in negs]
        thr = 0.99
        for t in np.arange(0.50, 1.0, 0.01):
            if np.mean([det_rf(z, p, t)[0] for z, p in zip(negs, pn)]) <= 0.02:
                thr = t; break
        for z in te:
            p = rf.predict_proba(X_de(z))[:, 1]; det, keep = det_rf(z, p, thr)
            ash = grid(z, z["ash"].astype(float), 0) > 0; ashd = ndimage.binary_dilation(ash, np.ones((3, 3), bool))
            d30 = grid(z, z["dist"], np.inf) <= 30
            res.append({"kk": z["kk"], "jor": j, "tipo": z["tipo"], "det": det, "thr": thr,
                        "mios30": int((keep & d30).sum()), "coinc30": int((keep & d30 & ashd).sum()),
                        "auc_px": None})
        print("RF jornada", j, "umbral", round(thr, 2), "det", sum(r["det"] for r in res if r["jor"] == j), "de", len(te), flush=True)
    return res


if __name__ == "__main__":
    S = cargar()
    print("scans", len(S), {t: sum(1 for z in S if z["tipo"] == t) for t in ("pos", "neg", "manto")},
          "jornadas", len({z["jor"] for z in S}), flush=True)
    res = correr(S)
    pickle.dump(res, open(os.path.join(C.TRABAJO, "e2_res.pkl"), "wb"))
    t1, ok = vara(res, "SECO propio, validacion dejando una jornada afuera (decide)")
    rf = correr_rf(S)
    pickle.dump(rf, open(os.path.join(C.TRABAJO, "e2_rf.pkl"), "wb"))
    t2, _ = vara(rf, "Bosque aleatorio, misma validacion (informativo, no decide)")
    txt = "\n".join([f"scans {len(S)}", t1, diagnostico(res, S), t2])
    open(sys.argv[1], "w", encoding="utf-8").write(txt)
    print(txt)
