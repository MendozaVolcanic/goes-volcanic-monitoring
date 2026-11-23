r"""H29, POST HOC (decidido despues de ver que M1 dio SENAL): comprobaciones de que la BTD baja sea de la pluma.

1. Desglose por cuadro y por pixel de M1 en la poblacion principal (sin posiciones).
2. Serie de tiempo: M1 de las MISMAS posiciones lejanas en cada cuadro de 14:00 a 23:50 del 08-11 y de los dias nulos.
   Si la BTD ya era baja antes de que VOLCAT pusiera pluma ahi (antes de 20:10), el efecto es del lugar o del dia,
   no de la pluma.
3. Nulo B restringido: solo corrimientos que mantienen la huella al E del crater (lado argentino o limitrofe) y a
   distancia parecida, para descartar un gradiente E-O del dia.
Salida: resultados/posthoc.json. Uso: python -I h29_posthoc.py
"""
import json
import os
import sys

import numpy as np

sys.stdout.reconfigure(encoding="utf-8")
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import h29_comun as C  # noqa: E402
import h29_medir as X  # noqa: E402


def main():
    r14, r15, acm, co14, co15 = X.H24.cargar()
    hu = X.huellas("h14")
    pc = X.poblacion(hu, X.LEJOS_KM, 1e9)
    alturas = sorted({round(h * 1000) for _, _, h in pc} | {3000})
    M = X.Medidor(r14, r15, co14, co15, X.H24.gfs_t([float(a) for a in alturas]), alturas)
    ex4, ex1, todas = X.mascaras_excl(hu)
    d0 = X.DIA["2026-11-08"]
    nulos = X.NULOS
    out = {}
    # 1. desglose
    filas = []
    for s, p, hk in pc:
        m1, m2 = M.medir(d0, s, p, ex4[s], ex1[s])
        filas.append({"hora": f"{s // 6:02d}:{s % 6 * 10:02d}", "dist_km": round(float(C.DIST.ravel()[p]), 1),
                      "M1": round(m1, 3), "M2": round(m2, 3), "BT11": round(float(M.bt11[d0, s, p]), 2),
                      "BTD": round(float(M.btd[d0, s, p]), 2), "acm": int(acm[d0, s, p])})
    out["por_pixel_cuadro"] = filas
    v = np.array([f["M1"] for f in filas])
    out["M1_fraccion_negativos"] = round(float(np.mean(v < 0)), 3)
    out["M1_cuartiles"] = [round(float(q), 3) for q in np.percentile(v, [10, 25, 50, 75, 90])]
    # 2. serie de tiempo en las mismas posiciones
    pos = sorted({p for _, p, _ in pc})
    # exclusion de pares: union de huellas a +-20 min del slot (si no hay huella, vacia) y siempre la union del dia
    vacio = np.zeros(C.NY * C.NX, bool)
    serie = []
    for s in range(14 * 6, 24 * 6):
        e4 = ex4.get(s, todas.ravel())
        e1 = ex1.get(s, vacio)
        en_huella = [p for p in pos if s in hu and hu[s][0].ravel()[p]]

        def est(d):
            vals = [M.medir(d, s, p, e4 | todas.ravel() if s not in ex4 else e4, e1)[0] for p in pos]
            vals = np.array([x for x in vals if np.isfinite(x)])
            return float(np.median(vals)) if len(vals) >= 5 else np.nan, len(vals)
        e, n = est(d0)
        en = [est(d)[0] for d in nulos]
        en = [x for x in en if np.isfinite(x)]
        serie.append({"hora": f"{s // 6:02d}:{s % 6 * 10:02d}", "M1_0811": round(e, 3) if np.isfinite(e) else None,
                      "n": n, "pos_en_huella": len(en_huella),
                      "nulo_min": round(min(en), 3) if en else None,
                      "nulo_med": round(float(np.median(en)), 3) if en else None,
                      "bajo_min": bool(np.isfinite(e) and en and e < min(en)),
                      "acm_desp_0811": round(float(np.mean([acm[d0, s, p] <= 1 for p in pos])), 2)})
        print(serie[-1], flush=True)
    out["serie_mismas_posiciones"] = serie
    out["n_posiciones"] = len(pos)
    # 3. nulo B restringido al E del crater
    lon_c = C.CRATER[1]
    cs = X.corrimientos(pc, todas)
    keep = []
    for dr, dc in cs:
        qs = [int((X.FILA[p] + dr) * C.NX + X.COL[p] + dc) for _, p, _ in pc]
        d = C.DIST.ravel()[qs]
        if np.all(C.LON.ravel()[qs] > lon_c) and np.all((d > 25) & (d < 70)):
            keep.append((dr, dc))
    eb = []
    for dr, dc in keep:
        extra = {}
        for s, p, _ in pc:
            q = int((X.FILA[p] + dr) * C.NX + X.COL[p] + dc)
            extra.setdefault(s, np.zeros(C.NY * C.NX, bool))[q] = True
        b = []
        for s, p, _ in pc:
            q = int((X.FILA[p] + dr) * C.NX + X.COL[p] + dc)
            b.append(M.medir(d0, s, q, ex4[s], ex1[s], extra=extra[s])[0])
        b = np.array([x for x in b if np.isfinite(x)])
        eb.append(float(np.median(b)) if len(b) >= X.MIN_PC else np.nan)
    eb = np.array([x for x in eb if np.isfinite(x)])
    E = float(np.median(v))
    out["nulo_B_este"] = {"corrimientos": int(len(eb)), "E_M1": round(E, 3),
                          "p": round(float(np.mean(eb <= E)), 4) if len(eb) else None,
                          "cuartiles": [round(float(q), 3) for q in np.percentile(eb, [5, 25, 50, 75, 95])] if len(eb) else []}
    print(out["nulo_B_este"], out["M1_cuartiles"], out["M1_fraccion_negativos"])
    json.dump(out, open(os.path.join(C.TRABAJO, "posthoc_completo.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    # al repo: sin dist por pixel (las distancias con hora ubicarian la huella); solo agregados
    rep = {k: v for k, v in out.items() if k != "por_pixel_cuadro"}
    rep["por_cuadro"] = {}
    for f in filas:
        rep["por_cuadro"].setdefault(f["hora"], []).append(f["M1"])
    json.dump(rep, open(os.path.join(C.RES, "posthoc.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)


if __name__ == "__main__":
    main()
