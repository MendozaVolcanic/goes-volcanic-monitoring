r"""S31j POST HOC (después de la medida única de s31j_medir.py, corrida 2): nada de esto decide.

1. Curva del umbral c en 2026: para cada c de la grilla, Sens_P, FA_N (media por día) y el nulo D, con la compuerta de
   calor y el seguimiento del criterio; al lado la FA de 2025 sin compuerta (tabla de calibración). ¿Hay algún c con el
   que el espejo publique más en P que en N?
3. Lo mismo que 1 pero sólo entre cuadros EVALUABLES de 15:00 a 23:50 UTC (las horas de los P), para separar la nube
   (los días sin VOLCAT son más nublados, S31f) de lo que hace el espejo: P, N de 2026 y todo 2025 sin compuerta.
2. z mínima de los píxeles del anillo a <= 10 km del cráter, en cuadros P, N y otro de 2026 y en 2025 a las mismas horas:
   ¿el objeto anclado es más raro cuando VOLCAT dibuja? Medianas por día y AUC P contra N con los días como bloques.
Lee D:\goes_notas\s31\s31j\z_T1.npz y noches_chillan.csv (escritos por la medida). Escribe resultados/s31j_posthoc.json.
Uso: python -I -B s31j_posthoc.py
"""
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import s31j_medir as J  # noqa: E402

B, M = J.B, J.M


def main():
    z = np.load(os.path.join(J.TRAB, "z_T1.npz"))
    Z25, Z26 = z["Z25"], z["Z26"]
    ev25, ev26 = np.isfinite(Z25).any(2), np.isfinite(Z26).any(2)
    CL = B.clases()
    no = pd.read_csv(os.path.join(J.TRAB, "noches_chillan.csv"), dtype={"noche": str})
    no["enc"] = no.enc.astype(str) == "True"
    G26 = J.compuerta_calor(no, J.T0_26, Z26.shape[0])
    res = {"rotulo": "POST HOC: después de la medida; no decide"}
    tab = json.load(open(os.path.join(J.RES, "s31j_resultado.json"), encoding="utf-8"))["calibracion"][
        "tabla_sin_compuerta_2025"]
    P, N = CL == "P", (CL == "N") & ev26
    curva = []
    for c in J.C_GRID:
        pub, tipo, _ = J.espejo(Z26, ev26, G26, c)
        fr = [(pub[d] & N[d]).sum() / N[d].sum() for d in range(CL.shape[0]) if N[d].any()]
        nd = J.nulo_D(pub, CL, np.random.default_rng(J.SEMILLA))
        fila = {"c": c, "Sens_P": int((P & pub).sum()), "P_nac": int((P & (tipo == 1)).sum()),
                "FA_N_media_dia": float(np.mean(fr)), "FA_N_global": float((pub & N).sum() / N.sum()),
                "p_D": nd["p"], "Tstar_media": nd["Tstar_media"], "FA25_sin_compuerta_media_dia": tab[f"{c:+.2f}"]["media_dia"]}
        curva.append(fila)
        print(json.dumps(fila), flush=True)
    res["curva_c"] = curva
    tarde = np.zeros((1, 144), bool)
    tarde[0, 90:144] = True
    sin = np.ones_like(ev25)
    tarde_tab = []
    for c in J.C_GRID:
        pub, _, _ = J.espejo(Z26, ev26, G26, c)
        p25, _, _ = J.espejo(Z25, ev25, sin, c)
        mP, mN, m25 = P & ev26 & tarde, N & tarde, ev25 & tarde
        fN = [(pub[d] & mN[d]).sum() / mN[d].sum() for d in range(CL.shape[0]) if mN[d].sum() >= 6]
        f25 = [(p25[d] & m25[d]).sum() / m25[d].sum() for d in range(Z25.shape[0]) if m25[d].sum() >= 6]
        fila = {"c": c, "P_tarde_eval": int(mP.sum()), "P_tarde_pub": int((pub & mP).sum()),
                "N_tarde_media_dia": float(np.mean(fN)), "N_tarde_dias": len(fN), "N_tarde_global": float((pub & mN).sum() / mN.sum()),
                "a2025_tarde_media_dia": float(np.mean(f25)), "a2025_tarde_dias": len(f25)}
        tarde_tab.append(fila)
        print("tarde", json.dumps(fila), flush=True)
    res["curva_c_tarde_evaluables"] = tarde_tab
    # 2. z mínima anclada
    a10 = J.AD <= J.ANCLA_KM

    def zmin(Z, d, s):
        v = Z[d, s][a10]
        return float(np.nanmin(v)) if np.isfinite(v).any() else np.nan
    filas = []
    for d in range(Z26.shape[0]):
        for s in range(144):
            if CL[d, s] in ("P", "N", "otro") and ev26[d, s]:
                filas.append((d, s, CL[d, s], zmin(Z26, d, s)))
    df = pd.DataFrame(filas, columns=["d", "s", "clase", "zmin"]).dropna()
    horasP = sorted(set(df[df.clase == "P"].s))
    z25 = [zmin(Z25, d, s) for d in range(Z25.shape[0]) for s in horasP if ev25[d, s]]
    z25 = np.array([x for x in z25 if np.isfinite(x)])
    res["zmin_10km"] = {cl: {"n": int((df.clase == cl).sum()), "mediana": float(df[df.clase == cl].zmin.median()),
                             "p10": float(df[df.clase == cl].zmin.quantile(0.1)),
                             "frac_bajo_-3": float((df[df.clase == cl].zmin <= -3).mean())} for cl in ("P", "N", "otro")}
    res["zmin_10km"]["2025_horas_P"] = {"n": len(z25), "mediana": float(np.median(z25)),
                                        "p10": float(np.percentile(z25, 10)), "frac_bajo_-3": float((z25 <= -3).mean())}
    # AUC P contra N, solo horas de día con P (12 a 23 UTC), y medianas por día
    dfh = df[df.s.isin(horasP)]
    p, n = dfh[dfh.clase == "P"].zmin.values, dfh[dfh.clase == "N"].zmin.values
    auc = float(((p[:, None] < n[None, :]).sum() + 0.5 * (p[:, None] == n[None, :]).sum()) / (len(p) * len(n)))
    res["auc_P_mas_bajo_que_N_horas_P"] = {"auc": auc, "nP": len(p), "nN": len(n)}
    # bootstrap por días de P y de N
    rng = np.random.default_rng(0)
    dP = {d: g.zmin.values for d, g in dfh[dfh.clase == "P"].groupby("d")}
    dN = {d: g.zmin.values for d, g in dfh[dfh.clase == "N"].groupby("d")}
    kp, kn = list(dP), list(dN)
    bs = []
    for _ in range(2000):
        pp = np.concatenate([dP[k] for k in rng.choice(kp, len(kp))])
        nn = np.concatenate([dN[k] for k in rng.choice(kn, len(kn))])
        bs.append(((pp[:, None] < nn[None, :]).sum() + 0.5 * (pp[:, None] == nn[None, :]).sum()) / (len(pp) * len(nn)))
    res["auc_P_mas_bajo_que_N_horas_P"]["ic95_dias"] = [float(x) for x in np.percentile(bs, [2.5, 97.5])]
    res["zmin_P_por_dia"] = {B.fecha(int(d)): [round(float(np.median(v)), 2), len(v)] for d, v in dP.items()}
    print(json.dumps({k: res[k] for k in ("zmin_10km", "auc_P_mas_bajo_que_N_horas_P")}, ensure_ascii=False))
    print(json.dumps(res["zmin_P_por_dia"]))
    json.dump(res, open(os.path.join(J.RES, "s31j_posthoc.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1,
              default=J._json)


if __name__ == "__main__":
    main()
