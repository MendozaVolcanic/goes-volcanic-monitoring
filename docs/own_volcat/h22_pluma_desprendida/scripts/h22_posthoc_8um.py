r"""H22, POST HOC (decidido despues de ver la pluma; no forma parte del criterio ni del veredicto).

La medida exploratoria dBTD(8,4 - 11,2) salio mas baja en los pixeles lejanos que en sus controles, fuera del rango
de los 3 dias placebo. Como esos pixeles tambien salieron mas TIBIOS que sus controles, primero hay que descartar
que sea el suelo tibio. Aqui se repite la comparacion con un control que ademas tiene el mismo dBT11 (+- 0,5 K),
en el 14-11, en los dias placebo despejados y con la huella corrida dentro del 14-11.

Escribe resultados/posthoc_8um.json. Uso: python -I h22_posthoc_8um.py
"""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import h22_comun as C  # noqa: E402
import h22_prueba as Q  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
DIA = "20261114"
HORAS = ("1930", "2220", "2230", "2240", "2250")       # cuadros que deciden (criterio, seccion 3)
DIAS_CL = ("20261027", "20261104", "20261106")         # dias placebo despejados (salida de h22_pluma.py)
D11_K = 0.5


def medir8(P, i, wy, wx, excl, igual_d11):
    """(diferencias pixel - mediana de controles, rangos) de dBTD(8,4 - 11,2) con el control D, opcionalmente
    pareado ademas por dBT11 +- 0,5 K."""
    B11, Bd, Bd8, _ = P.base(i)
    d11 = P.b14[i] - B11
    d8 = P.btd8[i] - Bd8
    val = np.isfinite(d8) & np.isfinite(d11) & ~excl & (d11 >= Q.CLARO_K)
    difs, rangos = [], []
    for y, x in zip(wy, wx):
        pool = val & (np.abs(C.ZDEM - C.ZDEM[y, x]) <= Q.DZ_M) & (np.abs(B11 - B11[y, x]) <= Q.DB11_K)
        if igual_d11:
            pool &= np.abs(d11 - d11[y, x]) <= D11_K
        if pool.sum() < Q.MIN_CTRL or not np.isfinite(d8[y, x]):
            continue
        v = d8[pool]
        difs.append(d8[y, x] - np.median(v))
        rangos.append((v > d8[y, x]).mean() + 0.5 * (v == d8[y, x]).mean())
    return difs, rangos


def grupo(P, HU, dia, igual_d11, corr=(0, 0), horas=HORAS, lejos=True):
    forma = C.LAT.shape
    D, R, por_cuadro = [], [], {}
    for c, h in HU.items():
        if c[9:] not in horas:
            continue
        i = P.pos.get(f"{dia}_{c[9:]}")
        if i is None or P.base(i) is None or not np.isfinite(P.b11[i]).all():
            continue
        m = (C.DIST[h["wy"], h["wx"]] > 30) == lejos
        if not m.any():
            continue
        d, r = medir8(P, i, h["wy"][m] + corr[0], h["wx"][m] + corr[1], Q.exclusion(HU, c, forma), igual_d11)
        D += d
        R += r
        if d:
            por_cuadro[c[9:]] = (len(d), round(float(np.median(d)), 3), round(float(np.mean(r)), 3))
    if len(D) < 20:
        return dict(n=len(D), D=np.nan, auc=np.nan, por_cuadro=por_cuadro)
    return dict(n=len(D), D=float(np.median(D)), auc=float(np.mean(R)), por_cuadro=por_cuadro)


def main():
    P = C.Pila()
    HU = Q.huellas_evento()
    forma = C.LAT.shape
    out = {}
    lej = {c: (h["wy"][C.DIST[h["wy"], h["wx"]] > 30], h["wx"][C.DIST[h["wy"], h["wx"]] > 30])
           for c, h in HU.items() if c[9:] in HORAS}
    excl = {c: Q.exclusion(HU, c, forma) for c in lej}
    corr = []
    for dy in range(-40, 41, 3):
        for dx in range(-40, 41, 3):
            if (dy, dx) != (0, 0) and all(
                    (wy + dy).min() >= 0 and (wx + dx).min() >= 0 and (wy + dy).max() < forma[0] and (wx + dx).max() < forma[1]
                    and not excl[c][wy + dy, wx + dx].any() for c, (wy, wx) in lej.items()):
                corr.append((dy, dx))
    for nom, igual in (("control D", False), ("control D con igual dBT11", True)):
        ev = grupo(P, HU, DIA, igual)
        pl = {d: grupo(P, HU, d, igual) for d in DIAS_CL}
        print(f"\n[{nom}] pixeles lejanos, cuadros que deciden")
        print(f"   14-11: n {ev['n']} D {ev['D']:+.3f} AUC {ev['auc']:.3f}; por cuadro (n, D, AUC): {ev['por_cuadro']}")
        for d, r in pl.items():
            print(f"   placebo {d}: n {r['n']} D {r['D']:+.3f} AUC {r['auc']:.3f}")
        esp, did = [], []
        for s in corr:
            e = grupo(P, HU, DIA, igual, corr=s)
            if not np.isfinite(e["D"]):
                continue
            b = [grupo(P, HU, d, igual, corr=s)["D"] for d in DIAS_CL]
            b = [v for v in b if np.isfinite(v)]
            esp.append((e["D"], e["auc"]))
            if b:
                did.append(e["D"] - float(np.median(b)))
        esp = np.array(esp)
        did = np.array(did)
        did0 = ev["D"] - float(np.median([r["D"] for r in pl.values()]))
        f_D = float((esp[:, 0] <= ev["D"]).mean())
        f_j = float(((esp[:, 0] <= ev["D"]) & (esp[:, 1] >= ev["auc"])).mean())
        f_did = float((did <= did0).mean())
        print(f"   placebo espacial ({len(esp)} corrimientos): D p05 {np.percentile(esp[:, 0], 5):+.3f} p50 {np.median(esp[:, 0]):+.3f} "
              f"p95 {np.percentile(esp[:, 0], 95):+.3f}; fraccion con D <= evento {f_D:.3f}; con D <= evento y AUC >= evento {f_j:.3f}")
        print(f"   corregido por el sesgo del lugar: evento {did0:+.3f}; p05 {np.percentile(did, 5):+.3f} p50 {np.median(did):+.3f}; "
              f"fraccion de corrimientos con valor <= evento {f_did:.3f}")
        # cercanos en los mismos cuadros y en el resto del dia
        ce = grupo(P, HU, DIA, igual, lejos=False, horas=("2220", "2230", "2240", "2250"))
        cp = {d: grupo(P, HU, d, igual, lejos=False, horas=("2220", "2230", "2240", "2250")) for d in DIAS_CL}
        print(f"   cercanos 22:20-22:50: 14-11 n {ce['n']} D {ce['D']:+.3f} AUC {ce['auc']:.3f}; placebo "
              + "; ".join(f"{d} D {r['D']:+.3f} AUC {r['auc']:.3f}" for d, r in cp.items()))
        out[nom] = dict(evento={k: v for k, v in ev.items()}, placebo=pl, n_corrimientos=len(esp),
                        espacial_D_p05_p50_p95=[float(np.percentile(esp[:, 0], q)) for q in (5, 50, 95)],
                        frac_D_menor_igual=f_D, frac_D_y_auc=f_j, DiD_evento=did0, frac_DiD_menor_igual=f_did,
                        cercanos_evento=ce, cercanos_placebo=cp)
    json.dump(out, open(os.path.join(C.RES, "posthoc_8um.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False,
              default=lambda o: o.item() if hasattr(o, "item") else str(o))


if __name__ == "__main__":
    main()
