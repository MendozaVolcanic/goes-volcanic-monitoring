"""H20a: exploracion sobre la tabla por pixel de la huella (hecha por h20a_medir.py).
Uso: python -I h20a_explora.py BLOQUE CASO   (p. ej. eleccion fuego_vcb)
Se niega a abrir validacion si no existe regla_congelada.md. Salida por pantalla (se guarda en resultados/).
"""
import os
import sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from h20a_comun import logit

sys.stdout.reconfigure(encoding="utf-8")
FUERA = os.environ.get("H20A_FUERA", r"D:\goes_notas\s17\h20a")
TOL = 0.01


def fr(a, b, m, tol=TOL):
    ok = m & np.isfinite(a) & np.isfinite(b)
    return int(ok.sum()), (float((np.abs(a[ok] - b[ok]) < tol).mean()) if ok.any() else float("nan"))


def q(x, ps=(0, 5, 25, 50, 75, 95, 100)):
    x = x[np.isfinite(x)]
    if x.size == 0:
        return "n=0"
    return "n=%d " % x.size + " ".join("p%d=%.4g" % (p, np.percentile(x, p)) for p in ps)


def main(bloque, caso):
    aqui = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if bloque == "validacion" and not os.path.exists(os.path.join(aqui, "regla_congelada.md")):
        sys.exit("No abro validacion: falta regla_congelada.md")
    T = dict(np.load(os.path.join(FUERA, "pix_%s_%s.npz" % (bloque, caso))))
    S, SL, P, PIR, PSW, PSB = T["S"], T["SL"], T["P"], T["P_IR"], T["P_SWIR"], T["P_sub"]
    todo = np.ones(S.shape, bool)
    print("#### %s %s: %d pixeles de huella, %d cuadros" % (bloque, caso, S.size, len(set(T["hora"]))))
    print("S :", q(S))
    print("SL:", q(SL))
    print("fraccion S>=0.5: %.4f ; SL>=0.5: %.4f ; S<0.05: %.4f ; SL<0.05: %.4f" % (
        np.nanmean(S >= 0.5), np.nanmean(SL[np.isfinite(SL)] >= 0.5), np.nanmean(S < 0.05),
        np.nanmean(SL[np.isfinite(SL)] < 0.05)))
    print("\n-- 1. huella sin valor")
    for n, F in (("S", S), ("SL", SL)):
        m = ~np.isfinite(F)
        print("  sin %s: %d ; de ellos P con valor %d, P_IR con valor %d, P_SWIR con valor %d, grupo ceniza>0 %d" % (
            n, m.sum(), np.isfinite(P[m]).sum(), np.isfinite(PIR[m]).sum(), np.isfinite(PSW[m]).sum(),
            (np.nan_to_num(T["grupo"][m]) > 0).sum()))
    print("\n-- 2. S: P contra P_sub en los pixeles donde difieren en mas de 0,05")
    d = np.abs(P - PSB) > 0.05
    print("  discordantes: %d ; S~P: %s ; S~P_sub: %s" % (d.sum(), fr(S, P, d), fr(S, PSB, d)))
    d = np.abs(P - T["P_prev"]) > 0.05
    print("  nulo informativo (P cambia >0,05 respecto del cuadro previo): %d ; S~P: %s ; S~P_previo: %s" % (
        d.sum(), fr(S, P, d), fr(S, T["P_prev"], d)))
    print("  max|S-P| = %.3g" % np.nanmax(np.abs(S - P)))
    print("\n-- 3. SL: P_IR contra los demas donde difieren en mas de 0,05")
    for n, C in (("P_SWIR", PSW), ("P", P), ("P_sub", PSB), ("P_IR_previo", T["P_IR_prev"]),
                 ("obj_Feature_Prob", T["obj_Feature_Prob"]), ("obj_Probability_Mean_IR", T["obj_Probability_Mean_IR"])):
        d = np.abs(PIR - C) > 0.05
        print("  vs %-24s discordantes %6d ; SL~P_IR: %s ; SL~%s: %s" % (n, d.sum(), fr(SL, PIR, d), n, fr(SL, C, d)))
    print("  max|SL-P_IR| = %.3g ; pixeles con P_IR>0,01: %d ; con P_IR>=0,5: %d" % (
        np.nanmax(np.abs(SL - PIR)), (PIR > 0.01).sum(), (PIR >= 0.5).sum()))
    print("  P_IR (TRK ash_probability_IR_prev) contra SL:", fr(SL, T["P_IR_prev_trk"], todo))
    print("\n-- 4. salto de log-odds")
    jS = logit(S) - logit(SL)
    jP = logit(P) - logit(PSB)
    jPI = logit(P) - logit(PIR)
    sub = P > PSB + 1e-6
    print("  pixeles con P > P_sub: %d" % sub.sum())
    print("  P_sub ~ P_IR en esos pixeles:", fr(PSB, PIR, sub), "; P_sub ~ P_SWIR:", fr(PSB, PSW, sub))
    ok = sub & np.isfinite(jS) & np.isfinite(jP)
    print("  logit(S)-logit(SL) contra logit(P)-logit(P_sub), |dif|<0,05: n=%d frac=%.4f" % (
        ok.sum(), (np.abs(jS[ok] - jP[ok]) < 0.05).mean() if ok.any() else float("nan")))
    okl = sub & np.isfinite(logit(PSB)) & np.isfinite(logit(PIR))
    print("  en P>P_sub, |logit(P_sub)-logit(P_IR)|<0,05: n=%d frac=%.4f ; |logit(P_sub)-logit(P_SWIR)|<0,05: frac=%.4f" % (
        okl.sum(), (np.abs(logit(PSB) - logit(PIR))[okl] < 0.05).mean() if okl.any() else float("nan"),
        (np.abs(logit(PSB) - logit(PSW))[okl & np.isfinite(logit(PSW))] < 0.05).mean() if okl.any() else float("nan")))
    H19 = (12.74, 16.37, 17.07, 18.27, 18.96)
    print("  pixeles con salto a menos de 0,01 de los valores de H19 %s: salto L2 %s ; salto evento %s" % (
        H19, [int((np.abs(jP[sub] - v) < 0.01).sum()) for v in H19],
        [int((np.abs(jS[sub] - v) < 0.01).sum()) for v in H19]))
    alto = sub & (jP > 5)
    print("  pixeles con salto L2 > 5: %d ; de ellos salto evento a menos de 0,05 del salto L2: %d ; S>=0,5: %d ; SL<0,5: %d" % (
        alto.sum(), (np.abs(jS - jP)[alto] < 0.05).sum(), (S[alto] >= 0.5).sum(), (SL[alto] < 0.5).sum()))
    print("  salto logit(S)-logit(SL), todos:", q(jS[np.isfinite(jS)]))
    v, c = np.unique(np.round(jS[sub & np.isfinite(jS)], 2), return_counts=True)
    o = np.argsort(-c)[:12]
    print("  valores mas repetidos del salto evento (redondeo 0,01) en P>P_sub:", [(float(v[i]), int(c[i])) for i in o])
    v, c = np.unique(np.round(jP[sub & np.isfinite(jP)], 2), return_counts=True)
    o = np.argsort(-c)[:12]
    print("  valores mas repetidos del salto L2 logit(P)-logit(P_sub):", [(float(v[i]), int(c[i])) for i in o])
    print("  pixeles con S > SL + 0,05: %d ; con S < SL - 0,05: %d ; |S-SL|<=0,05: %d" % (
        (S > SL + 0.05).sum(), (S < SL - 0.05).sum(), (np.abs(S - SL) <= 0.05).sum()))
    print("\n-- 5. distance_traveled y residence_time")
    D, R = T["dist_trav"], T["res_time"]
    print("  dist_trav:", q(D))
    print("  res_time :", q(R))
    print("  huella sin dist: %d ; sin tiempo: %d" % ((~np.isfinite(D)).sum(), (~np.isfinite(R)).sum()))
    for n, C in (("d_nominal", T["d_nominal"]), ("d_pc", T["d_pc"]), ("desplaz", T["desplaz"]),
                 ("desplaz_ash", T["desplaz_ash"])):
        ok = np.isfinite(D) & np.isfinite(C)
        if ok.sum() < 3:
            print("  dist vs %s: n=%d" % (n, ok.sum()))
            continue
        cerca = np.abs(D[ok] - C[ok]) <= np.maximum(1.0, 0.02 * np.abs(C[ok]))
        print("  dist vs %-12s n=%d dentro de max(1 km, 2%%): %.4f ; mediana(D-C)=%.3f ; p5..p95 (D-C)= %.2f..%.2f ; r=%.4f" % (
            n, ok.sum(), cerca.mean(), np.median(D[ok] - C[ok]), np.percentile(D[ok] - C[ok], 5),
            np.percentile(D[ok] - C[ok], 95), np.corrcoef(D[ok], C[ok])[0, 1]))
    ok = np.isfinite(D) & np.isfinite(R) & (R > 0)
    v = D[ok] / R[ok] / 3.6
    print("  rapidez dist/tiempo (m/s):", q(v))
    for h in sorted(set(T["hora"])):
        m = (T["hora"] == h)
        mk = m & ok
        vv = D[mk] / R[mk] / 3.6
        if h in (sorted(set(T["hora"]))[::3]):
            print("   cuadro %06d n=%4d edad=%.0f min ; tiempo min/med/max h: %.2f/%.2f/%.2f ; dist min/med/max km: %.1f/%.1f/%.1f ; rapidez p5/p50/p95: %s ; d_pc max %.1f" % (
                h, m.sum(), np.nanmax(T["feature_age"][m]), np.nanmin(R[m]), np.nanmedian(R[m]), np.nanmax(R[m]),
                np.nanmin(D[m]), np.nanmedian(D[m]), np.nanmax(D[m]),
                "/".join("%.1f" % np.percentile(vv, p) for p in (5, 50, 95)) if vv.size else "-",
                np.nanmax(T["d_pc"][m])))
    print("\n-- 5b. reglas de trayectoria")
    edad_h = T["feature_age"] / 60.0
    okR = np.isfinite(R)
    paso = np.unique(np.round(R[okR], 4))
    dif = np.diff(paso)
    print("  valores distintos de res_time: %d ; paso minimo entre valores: %s h" % (
        paso.size, "%.4f" % dif.min() if dif.size else "-"))
    print("  res_time <= edad del rasgo (+0,01 h): %.4f ; res_time == edad: %.4f ; res_time == 0: %.4f" % (
        np.mean(R[okR] <= edad_h[okR] + 0.01), np.mean(np.abs(R[okR] - edad_h[okR]) < 0.01), np.mean(R[okR] == 0)))
    por = [(h, np.nanmax(R[T["hora"] == h]), np.nanmax(edad_h[T["hora"] == h])) for h in sorted(set(T["hora"]))]
    print("  cuadros con max(res_time) == edad: %d de %d" % (sum(abs(a - b) < 0.01 for _, a, b in por), len(por)))
    for nombre, m in (("res_time == 0", R == 0), ("res_time > 0", R > 0)):
        for n, C in (("d_nominal", T["d_nominal"]), ("d_pc", T["d_pc"])):
            ok = m & np.isfinite(D) & np.isfinite(C)
            if ok.sum() == 0:
                print("  %s: dist vs %s n=0" % (nombre, n))
                continue
            cerca = np.abs(D[ok] - C[ok]) <= np.maximum(1.0, 0.02 * np.abs(C[ok]))
            print("  %-14s dist vs %-9s n=%5d dentro de max(1 km, 2%%): %.4f ; D>=C-1: %.4f ; mediana(D-C)=%.2f" % (
                nombre, n, ok.sum(), cerca.mean(), np.mean(D[ok] >= C[ok] - 1.0), np.median(D[ok] - C[ok])))
    dh0 = T["h_ev"] - T["h_l2"]
    print("  h_ev - h_l2 dentro de (-0,0101, 0]: %.4f" % np.mean((dh0 > -0.0101) & (dh0 <= 1e-6)))
    print("\n-- 6. altura y radio efectivo del evento contra el L2")
    dh = T["h_ev"] - T["h_l2"]
    print("  h_ev - h_l2:", q(dh), "; iguales (<=0,0051): %.4f" % np.mean(np.abs(dh[np.isfinite(dh)]) <= 0.0051))
    print("  h_ev sin valor: %d ; h_l2 sin valor: %d" % ((~np.isfinite(T["h_ev"])).sum(), (~np.isfinite(T["h_l2"])).sum()))
    print("  carga evento - carga L2:", q(T["carga_ev"] - T["carga_l2"]))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
