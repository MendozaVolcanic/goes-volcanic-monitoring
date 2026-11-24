r"""S21b prueba 1, controles POST HOC (escritos despues de ver el veredicto SIN PODER; no lo cambian).

Por que: la regla dio SIN PODER porque el nulo de toda la ventana (145 por 70 km) tiene una cola larga, y en el mapa de
C05 hay una mancha clara justo sobre la huella. Tres preguntas:
 (a) nulo local: con los corrimientos a menos de 15 km del crater (la zona que revisa la regla de nubes), cuanto vale p
     y cuanto el poder;
 (b) altura: si la mancha es pluma en el aire, S debe ser maximo con la huella puesta a la altura de la pluma (4,3 km);
     si es ceniza depositada en la nieve, a la cota del suelo (cada celda en su cota del DEM). Es el discriminador mas
     limpio entre pluma y deposito, porque GOES ve la pluma corrida 0,93 km al sur por km de altura;
 (c) serie: reflectancia media en la huella en todas las mananas despejadas bajadas (antes y despues del 25-10) y en los
     cuadros de 14:00 a 15:00 del 25-10.
Uso: python -I s21b_posthoc1.py  -> ../resultados/posthoc1.json, posthoc1.log, ../figuras/posthoc1_altura.png
"""
import json
import os
import sys
from datetime import datetime

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import s21b_comun as C  # noqa: E402
import s21b_prueba1 as P1  # noqa: E402

AQUI = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(AQUI, "resultados")
FIG = os.path.join(AQUI, "figuras")
DEM = r"D:\goes_notas\s20b\dem_local.npy"
R_LOCAL = 15.0
LOG = []


def log(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    LOG.append(s)


def f_suelo(banda, mask):
    """f con cada celda de la mascara puesta en su cota del DEM (deposito en la nieve)."""
    dem = np.load(DEM)
    g = C._GEO[banda]
    r, c, ok = g.indices(C.GLAT[mask], C.GLON[mask], dem[mask].astype(float))
    out = np.zeros(g.shape)
    np.add.at(out, (r[ok], c[ok]), C.CELDA_KM2)
    return out / g.area


def corr_local(f, A, B, banda, geo):
    """Como P1.corrimientos, pero solo corrimientos cuyo centroide (ponderado por f) cae a <= 15 km del crater."""
    e, n = geo[banda].km_desde(C.CRATER[0], C.CRATER[1], 0.0)
    ny, nx = f.shape
    rr, cc = np.nonzero(f > 0)
    fv = f[rr, cc]
    S0, E0 = P1.S_de(C.esperado(fv, B[rr, cc], banda), A[rr, cc])
    rc, ccn = np.average(rr, weights=fv), np.average(cc, weights=fv)
    reales = set(zip(rr.tolist(), cc.tolist()))
    out = []
    for dr in range(-rr.min(), ny - rr.max()):
        for dc in range(-cc.min(), nx - cc.max()):
            if dr == 0 and dc == 0:
                continue
            i, j = int(round(rc + dr)), int(round(ccn + dc))
            if np.hypot(e[i, j], n[i, j]) > R_LOCAL:
                continue
            r2, c2 = rr + dr, cc + dc
            if any((a, b) in reales for a, b in zip(r2.tolist(), c2.tolist())):
                continue
            Bv, Av = B[r2, c2], A[r2, c2]
            if not (np.isfinite(Bv).all() and np.isfinite(Av).all()):
                continue
            S, E = P1.S_de(C.esperado(fv, Bv, banda), Av)
            if 0.5 * E0 <= E <= 2.0 * E0:
                out.append(S)
    return S0, np.array(out)


def main():
    m = np.load(C.MASCARA)
    H = float(m["H"])
    ev = P1.cuadro("2026-10-25", "14:30")
    geo = C._GEO
    base = {d: P1.cuadro(d, "14:30") for d in ["2026-10-15", "2026-10-16", "2026-10-17"]}   # los que paso la regla
    out = {"a_nulo_local": {}, "b_altura": {}, "c_serie": {}}

    log("== (a) nulo local (corrimientos a <= 15 km del crater), cuadro 14:30, 3 dias base")
    for b in P1.BANDAS:
        f = geo[b].fraccion(m["pluma"], H)
        B = np.nanmedian(np.stack([r[b] for r in base.values()]), 0)
        A = ev[b] - B
        S0, nul = corr_local(f, A, B, b, geo)
        p = float(np.mean(nul >= S0))
        pod = []
        for dd, r in base.items():
            otros = [x for k, x in base.items() if k != dd]
            Bo = np.nanmedian(np.stack([x[b] for x in otros]), 0)
            Ao = r[b] - Bo + C.esperado(f, Bo, b)
            S2, n2 = corr_local(f, Ao, Bo, b, geo)
            pod.append(float(np.mean(n2 >= S2)) <= P1.ALFA and S2 > 0)
        out["a_nulo_local"][b] = {"S": round(S0, 3), "p": round(p, 4), "n": int(len(nul)),
                                  "S_nulo_p50_p95": [round(float(x), 3) for x in np.percentile(nul, [50, 95])],
                                  "poder": round(float(np.mean(pod)), 2)}
        log(f"  {b}: S {S0:+.3f} p {p:.4f} (n {len(nul)}), nulo p50/p95 "
            f"{out['a_nulo_local'][b]['S_nulo_p50_p95']}, poder {out['a_nulo_local'][b]['poder']}")

    log("== (b) S contra la altura a la que se pone la huella (nulo local); 'suelo' = cada celda en su cota")
    alturas = [("suelo", None)] + [(f"{h:.1f} km", h * 1000) for h in (2.5, 3.0, 3.5, 4.0, 4.267, 4.5, 5.0, 5.5, 6.0)]
    for b in P1.BANDAS:
        B = np.nanmedian(np.stack([r[b] for r in base.values()]), 0)
        A = ev[b] - B
        fila = {}
        for nom, h in alturas:
            f = f_suelo(b, m["pluma"]) if h is None else geo[b].fraccion(m["pluma"], h)
            S0, nul = corr_local(f, A, B, b, geo)
            fila[nom] = {"S": round(S0, 3), "p": round(float(np.mean(nul >= S0)), 4), "n": int(len(nul))}
        out["b_altura"][b] = fila
        log(f"  {b}: " + "  ".join(f"{k}: S {v['S']:+.2f} p {v['p']:.3f}" for k, v in fila.items()))

    log("== (c) reflectancia media ponderada por f en la huella (H de S20b) y su anomalia contra la mediana base")
    dias = ["2026-09-27", "2026-10-15", "2026-10-16", "2026-10-17", "2026-10-25", "2026-11-02", "2026-11-04"]
    horas = ["14:00", "14:10", "14:20", "14:30", "14:40", "14:50", "15:00"]
    for b in ("C02", "C05", "C06"):
        f = geo[b].fraccion(m["pluma"], H)
        fs = f_suelo(b, m["pluma"])
        w, ws = f / f.sum(), fs / fs.sum()
        serie = {}
        for d in dias:
            for hh in horas:
                r = P1.cuadro(d, hh)
                if r is None:
                    continue
                serie[f"{d} {hh}"] = [round(float(np.nansum(w * r[b])), 4), round(float(np.nansum(ws * r[b])), 4)]
        out["c_serie"][b] = serie
        log(f"  {b} [huella a H, huella en el suelo]:")
        for d in dias:
            v = [serie.get(f"{d} {hh}") for hh in horas]
            log(f"    {d}: " + " ".join("-" if x is None else f"{x[0]:.3f}/{x[1]:.3f}" for x in v))

    json.dump(out, open(os.path.join(RES, "posthoc1.json"), "w", encoding="utf8"), ensure_ascii=False, indent=1)
    open(os.path.join(RES, "posthoc1.log"), "w", encoding="utf8").write("\n".join(LOG) + "\n")

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(6, 3.6))
    xs = [3.1] + [h for _, h in [(0, 2.5), (0, 3.0), (0, 3.5), (0, 4.0), (0, 4.267), (0, 4.5), (0, 5.0), (0, 5.5),
                                 (0, 6.0)]]
    for b, col in zip(P1.BANDAS, ("C0", "C3", "C2")):
        ys = [v["S"] for v in out["b_altura"][b].values()]
        ax.plot(xs[1:], ys[1:], "o-", color=col, label=b)
        ax.plot(xs[0], ys[0], "s", color=col, mfc="none")
    ax.axvline(4.267, color="k", ls=":", lw=0.8)
    ax.axhline(1, color="0.5", lw=0.6)
    ax.axhline(0, color="0.5", lw=0.6)
    ax.set_xlabel("altura a la que se pone la huella (km sobre el elipsoide); cuadrado = cada celda en su cota")
    ax.set_ylabel("S (1 = lo esperado)")
    ax.set_title("Post hoc (b): ¿la mancha está a la altura de la pluma o en el suelo?", fontsize=9)
    ax.legend(fontsize=8)
    ax.tick_params(labelsize=8)
    ax.xaxis.label.set_size(7)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "posthoc1_altura.png"), dpi=80)


if __name__ == "__main__":
    main()
