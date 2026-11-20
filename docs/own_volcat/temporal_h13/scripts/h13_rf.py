"""H13, variante informativa (no decide): bosque aleatorio de la etapa 2 con y sin las variables temporales.

Uso: python h13_rf.py <salida.txt>
Mismo bosque, umbral y deteccion que e2_clasificador.correr_rf (300 arboles, hojas >= 20, clases balanceadas,
umbral por pliegue = el mas bajo de 0,50 a 0,99 con <= 2 % de falsa alarma en el propio entrenamiento,
deteccion = >= 2 pixeles conexos sobre el umbral con uno a <= 10 km), dejando una jornada afuera.
Corre dos veces sobre el MISMO conjunto: (1) variables de la etapa 2; (2) etapa 2 + 18 temporales.
Positivos: cuadros anclados. Negativos: todos los cuadros candidatos a control (limpios, con historia).
"Mismo dia" (solo prueba): scans de las secuencias sin objeto VOLCAT a <= 50 km.
"""
import os, sys, pickle
import numpy as np
from scipy import ndimage

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import h13_comun as H  # noqa: E402
import h13_analisis as A  # noqa: E402
import e2_clasificador as EC  # noqa: E402

VARS_E2 = EC.VARS_RF


def conjunto():
    anc = set(H.anclados())
    neg = set()
    for t in anc:
        neg |= set(H.candidatos(t))
    mismo = {t for t in H.ventana_pos() if t not in anc and t not in neg}
    S = []
    for t, tipo in [(t, "pos") for t in sorted(anc)] + [(t, "neg") for t in sorted(neg)] + [(t, "mismo_dia") for t in sorted(mismo)]:
        f = A.feat(t)
        if f is None:
            continue
        lab = np.asarray(f["lab"])
        if tipo != "pos" and (lab != 0).any():
            continue                       # sin etiqueta limpia (objeto no anclado o sin registro): fuera
        T = A.temporales(t)
        if T is None:
            continue
        z = {k: f[k] for k in VARS_E2 if k != "dist"}
        z.update({"ys": f["ys"], "xs": f["xs"], "dist": f["dist"], "ash": lab == 1, "tipo": tipo, "kk": H.k(t),
                  "jor": H.jornada(t)})
        z.update({v: T[v] for v in A.VARS_T})
        S.append(z)
    return S


def correr(S, vars_, seed=0):
    from sklearn.ensemble import RandomForestClassifier
    def X_de(z):  # noqa: E306
        X = np.stack([np.asarray(z[k], float) for k in vars_], 1)
        return np.where(np.isfinite(X), X, -999.0)
    jors = sorted({z["jor"] for z in S if z["tipo"] == "pos"} | {z["jor"] for z in S if z["tipo"] == "neg"})
    res = []; rng = np.random.default_rng(seed)
    for j in jors:
        tr = [z for z in S if z["jor"] != j and z["tipo"] in ("pos", "neg")]; te = [z for z in S if z["jor"] == j]
        Xp = np.concatenate([X_de(z)[z["ash"]] for z in tr if z["tipo"] == "pos"])
        Xn = np.concatenate([X_de(z) for z in tr if z["tipo"] == "neg"])
        if len(Xn) > 400000:
            Xn = Xn[rng.choice(len(Xn), 400000, replace=False)]
        X = np.concatenate([Xp, Xn]); y = np.r_[np.ones(len(Xp)), np.zeros(len(Xn))]
        rf = RandomForestClassifier(300, min_samples_leaf=20, class_weight="balanced", n_jobs=8, random_state=seed).fit(X, y)
        negs = [z for z in tr if z["tipo"] == "neg"]
        pn = [rf.predict_proba(X_de(z))[:, 1] for z in negs]
        thr = 0.99
        for t in np.arange(0.50, 1.0, 0.01):
            if np.mean([EC.det_rf(z, p, t)[0] for z, p in zip(negs, pn)]) <= 0.02:
                thr = t; break
        for z in te:
            p = rf.predict_proba(X_de(z))[:, 1]; det, keep = EC.det_rf(z, p, thr)
            ash = EC.grid(z, z["ash"].astype(float), 0) > 0; ashd = ndimage.binary_dilation(ash, np.ones((3, 3), bool))
            d30 = EC.grid(z, z["dist"], np.inf) <= 30
            res.append({"kk": z["kk"], "jor": j, "tipo": z["tipo"], "det": det, "thr": thr,
                        "mios30": int((keep & d30).sum()), "coinc30": int((keep & d30 & ashd).sum())})
        print("RF", len(vars_), "vars, jornada", j, "umbral", round(thr, 2), "det",
              {tp: sum(r["det"] for r in res if r["jor"] == j and r["tipo"] == tp) for tp in ("pos", "neg", "mismo_dia")}, flush=True)
    return res


def resumen(res, nombre):
    txt, ok = EC.vara([r for r in res if r["tipo"] in ("pos", "neg")], nombre)
    txt = txt.replace("  3 manto 16-11: 0/0 = nan (pide <= 0,10) -> False", "  3 manto 16-11: no evaluado (sin secuencias del 16-11)")
    md = [r for r in res if r["tipo"] == "mismo_dia"]
    pj = {}
    for r in md:
        pj.setdefault(r["jor"], [0, 0]); pj[r["jor"]][0] += int(r["det"]); pj[r["jor"]][1] += 1
    txt += (f"\n  mismo dia sin objeto (solo informa): {sum(r['det'] for r in md)}/{len(md)} detectados; por jornada "
            + "; ".join(f"{j} {a}/{b}" for j, (a, b) in sorted(pj.items())))
    pos = [r for r in res if r["tipo"] == "pos"]; neg = [r for r in res if r["tipo"] == "neg"]
    sens = np.mean([r["det"] for r in pos]); fa = np.mean([r["det"] for r in neg])
    maxj = max([sum(r["det"] for r in neg if r["jor"] == j) for j in {r["jor"] for r in neg}] or [0])
    co = sum(r["coinc30"] for r in pos) / max(sum(r["mios30"] for r in pos), 1)
    cumple3 = sens >= 0.5 and fa <= 0.02 and maxj <= 3 and co >= 0.5
    txt += f"\n  cumple los 3 criterios evaluables (1, 2 y 4): {cumple3}"
    return txt


if __name__ == "__main__":
    S = conjunto()
    cab = (f"scans {len(S)}: " + str({t: sum(1 for z in S if z['tipo'] == t) for t in ('pos', 'neg', 'mismo_dia')})
           + f"; jornadas con negativos {len({z['jor'] for z in S if z['tipo'] == 'neg'})}")
    print(cab, flush=True)
    r1 = correr(S, VARS_E2); r2 = correr(S, tuple(VARS_E2) + tuple(A.VARS_T))
    pickle.dump({"e2": r1, "e2_temporal": r2}, open(os.path.join(H.H13DIR, "rf_h13.pkl"), "wb"))
    txt = "\n".join([cab, resumen(r1, "Bosque con variables de la etapa 2 (18)"),
                     resumen(r2, "Bosque con etapa 2 + 18 temporales (36)")])
    open(sys.argv[1], "w", encoding="utf-8").write(txt)
    print(txt)
