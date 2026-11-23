r"""H29, POST HOC: a que pluma (f, eps) equivale el M1 observado. Se pinta cada (f, eps) en los pixeles lejanos de
los dias nulos donde la capa es visible y se mide el cambio de M1 (pintado menos sin pintar), mediana por pixel-cuadro.
Salida: resultados/equivalencia.json. Uso: python -I h29_equivalencia.py
"""
import json, os, sys
import numpy as np
sys.stdout.reconfigure(encoding="utf-8")
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import h29_comun as C  # noqa: E402
import h29_medir as X  # noqa: E402

r14, r15, acm, co14, co15 = X.H24.cargar()
hu = X.huellas("h14")
pc = X.poblacion(hu, X.LEJOS_KM, 1e9)
alt = sorted({round(h * 1000) for _, _, h in pc} | {3000})
M = X.Medidor(r14, r15, co14, co15, X.H24.gfs_t([float(a) for a in alt]), alt)
ex4, ex1, _ = X.mascaras_excl(hu)
out = {}
for fe in (0.02, 0.05, 0.1, 0.2, 0.3, 0.5):
    d1, d2 = [], []
    for d in X.NULOS:
        for s, p, hk in pc:
            Tt = M.Tgfs[d, s, alt.index(round(hk * 1000))]
            if not (np.isfinite(Tt) and M.bt11[d, s, p] > Tt + 3):
                continue
            a = M.medir(d, s, p, ex4[s], ex1[s])
            b = M.medir(d, s, p, ex4[s], ex1[s], iny=(1.0, fe), hk=hk)
            if np.isfinite(a[0]) and np.isfinite(b[0]):
                d1.append(b[0] - a[0])
            if np.isfinite(a[1]) and np.isfinite(b[1]):
                d2.append(b[1] - a[1])
    out[f"capa_uniforme_eps_{fe}"] = {"dM1_mediana_K": round(float(np.median(d1)), 3), "dM2_mediana_K": round(float(np.median(d2)), 3), "n": len(d1)}
    print(fe, out[f"capa_uniforme_eps_{fe}"], flush=True)
json.dump(out, open(os.path.join(C.RES, "equivalencia.json"), "w", encoding="utf-8"), indent=1)
