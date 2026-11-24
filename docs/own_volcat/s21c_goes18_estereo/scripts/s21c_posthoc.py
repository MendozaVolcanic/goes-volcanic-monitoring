r"""S21c, POST HOC (escrito despues de ver que la prueba A salio SIN PODER; no cambia el veredicto).

El estadistico del criterio (suma de |dR| del mayor componente) queda dominado por cambios de escena de 100 o mas
pixeles en 10 min, y una columna de 4 a 5 px no lo mueve. Aqui se normaliza cada pixel de S contra su propia
historia en los pares nulos (mediana y MAD de dR en ese pixel), y se usan dos estadisticos:
- Z4: media de los 4 |z| mas grandes de S (generico, cualquier rasgo chico).
- Zcol: |media de z| sobre los pixeles de la columna vertical del REAV de ese pulso (filtro adaptado al rasgo
  buscado; tiene sentido solo cerca del inicio).
Mismos nulos, mismos pares, misma inyeccion y misma regla de p que el criterio. Salida: resultados/posthoc.json/.txt
"""
import json
import os
import sys
from datetime import datetime, timedelta

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import s21c_comun as K  # noqa: E402
import s21c_medir as MX  # noqa: E402

LOG = []


def log(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    LOG.append(s)


def dR(x):
    Rt, Rp, dq = x
    d = Rt - Rp
    ok = np.isfinite(d) & dq
    d = d - np.nanmedian(d[ok])
    d[~ok] = np.nan
    return d


def main():
    acm = MX.e1_por_cuadro()
    out = {}
    for sat in (18, 19):
        c = MX.cuadro(sat, datetime(2026, 10, 28, 17, 30))
        f0, c0 = c[2], c[3]
        b, _ = MX.sesgo(sat)
        S = MX.region_S(sat, f0, c0, b)
        # pares nulos (misma regla que prueba_A)
        pares = []
        for i in range(46):
            t = datetime(2026, 10, 28, 15, 0) + timedelta(minutes=10 * i)
            if MX.en_pulso(t):
                continue
            x = MX.par(sat, t, S)
            if x is not None and not isinstance(x, str):
                pares.append(("a", t, x))
        for d in MX.DIAS_CTRL:
            for i in range(52):
                t = d.replace(hour=14) + timedelta(minutes=10 * i)
                if t.hour > 22 or (t.hour == 22 and t.minute > 30):
                    break
                fa, fb = acm.get(t), acm.get(t - timedelta(minutes=10))
                if fa is None or fb is None or fa < 0.8 or fb < 0.8:
                    continue
                x = MX.par(sat, t, S)
                if x is not None and not isinstance(x, str):
                    pares.append(("b", t, x))
        D = np.stack([dR(x) for _, _, x in pares])
        mu = np.nanmedian(D, 0)
        sg = 1.4826 * np.nanmedian(np.abs(D - mu), 0)
        sg = np.where(sg > 0, sg, np.nan)

        def z(d):
            return (d - mu) / sg

        def Z4(d):
            v = np.abs(z(d)[S])
            v = np.sort(v[np.isfinite(v)])
            return float(v[-4:].mean())

        res = {"n_nulo": len(pares), "sigma_px_mediana_S": float(np.nanmedian(sg[S])), "pulsos": {}}
        nZ4 = np.array([Z4(dR(x)) for _, _, x in pares])
        log(f"GOES-{sat}: {len(pares)} pares nulos; sigma por pixel en S (mediana) {np.nanmedian(sg[S]):.4f}; "
            f"Z4 nulo mediana {np.median(nZ4):.2f}, p95 {np.percentile(nZ4, 95):.2f}, max {nZ4.max():.2f}")
        for nom, (ini, H) in MX.PULSOS.items():
            col = MX.columna(sat, f0, c0, b, H) & np.isfinite(sg)
            nZc = np.array([abs(np.nanmean(z(dR(x))[col])) for _, _, x in pares])
            cands = sorted(t for t in [datetime(2026, 10, 28, 15, 0) + timedelta(minutes=10 * i) for i in range(47)]
                           if MX.mirada(18, t) >= ini)[:2]
            fila = {}
            for rot, t in (("pre", cands[0] - timedelta(minutes=10)), ("post1", cands[0]), ("post2", cands[1])):
                x = MX.par(sat, t, S)
                if x is None or isinstance(x, str):
                    fila[rot] = None
                    continue
                d = dR(x)
                a, bb = Z4(d), abs(np.nanmean(z(d)[col]))
                fila[rot] = {"t": f"{t:%H:%M}", "Z4": round(a, 2), "p_Z4": round(MX.pval(a, nZ4), 4),
                             "Zcol": round(float(bb), 2), "p_Zcol": round(MX.pval(bb, nZc), 4)}
            # poder con la misma inyeccion (columna de 1 px hasta el tope del REAV), por c y signo
            pod = {}
            for nomb, sig in (("oscura", -1), ("clara", 1)):
                pod[nomb] = {}
                for cc in MX.C_INY:
                    d4 = dc = 0
                    for _, _, (Rt, Rp, dq) in pares:
                        Ri = Rt.copy()
                        Ri[MX.columna(sat, f0, c0, b, H)] += sig * cc
                        d = dR((Ri, Rp, dq))
                        d4 += MX.pval(Z4(d), nZ4) <= 0.05
                        dc += MX.pval(abs(np.nanmean(z(d)[col])), nZc) <= 0.05
                    pod[nomb][str(cc)] = (round(d4 / len(pares), 2), round(dc / len(pares), 2))
            c80 = {}
            for k in (0, 1):
                nm = ("Z4", "Zcol")[k]
                c80[nm] = {s: next((float(cc) for cc, v in pod[s].items() if v[k] >= 0.8), None) for s in pod}
            res["pulsos"][nom] = {"cuadros": fila, "poder": pod, "c80": c80}
            log(f"  {nom}: {fila}; c80 {c80}")
        out[f"g{sat}"] = res
    base = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "resultados")
    with open(os.path.join(base, "posthoc.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1, ensure_ascii=False)
    with open(os.path.join(base, "posthoc.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(LOG) + "\n")


if __name__ == "__main__":
    main()
