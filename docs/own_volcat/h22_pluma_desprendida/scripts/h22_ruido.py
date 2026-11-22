r"""H22, tarea 1: estructura del ruido de fondo ANTES de probar la pluma. Solo dias sin objeto VOLCAT (placebo), a
las mismas horas del evento (16:30 a 23:40 UTC), en los pixeles que la pluma del 14-11 cruza. De los archivos de
evento usa solo la posicion de la huella (event_idx), ninguna temperatura.

Mide: (1) variantes de linea base; (2) media, dispersion y descomposicion del residuo dBT11, dBTD, beta;
(3) autocorrelacion espacial y temporal; (4) dependencia con la cota; (5) ruido del estadistico de la prueba
(huella real puesta en dias sin evento, contra el control pareado).

Escribe resultados/ruido_*.csv y resultados/ruido_resumen.json. Uso: python -I h22_ruido.py
"""
import json
import os
import sys
from datetime import datetime

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import h22_comun as C  # noqa: E402
import h22_prueba as Q  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
CLARO_K = -3.0      # un pixel cuenta como "despejado" si dBT11 >= -3 K
R = {}


def sd_rob(x):
    x = x[np.isfinite(x)]
    return float(1.4826 * np.median(np.abs(x - np.median(x)))) if len(x) else np.nan


def desc(x):
    x = np.asarray(x, "float64")
    x = x[np.isfinite(x)]
    if len(x) == 0:
        return dict(n=0)
    return dict(n=int(len(x)), media=round(float(x.mean()), 3), mediana=round(float(np.median(x)), 3),
                sd=round(float(x.std()), 3), sd_robusta=round(sd_rob(x), 3),
                p05=round(float(np.percentile(x, 5)), 3), p95=round(float(np.percentile(x, 95)), 3))


def corr(a, b):
    g = np.isfinite(a) & np.isfinite(b)
    if g.sum() < 30:
        return np.nan
    return float(np.corrcoef(a[g], b[g])[0, 1])


def main():
    P = C.Pila()
    print("cuadros en la pila", len(P.cs), "; descartados por relleno en la ventana:", P.descartados)
    HU = Q.huellas_evento()
    dias = Q.dias_placebo(P)
    slots = sorted({c[9:] for c in HU})
    print("cuadros del evento", len(HU), "horas", slots[0], "a", slots[-1])
    print("dias placebo", len(dias), dias)
    forma = C.LAT.shape
    corredor = np.zeros(forma, bool)
    for h in HU.values():
        corredor[h["wy"], h["wx"]] = True
    lejos = corredor & (C.DIST > 30)
    cerca = corredor & (C.DIST <= 30)
    dom = C.DIST <= 100
    print("corredor (union de huellas):", int(corredor.sum()), "px; a <= 30 km:", int(cerca.sum()), "; a > 30 km:",
          int(lejos.sum()), "; dominio <= 100 km:", int(dom.sum()))
    print("cota m: cerca mediana %.0f (%.0f a %.0f); lejos mediana %.0f (%.0f a %.0f)" % (
        np.median(C.ZDEM[cerca]), C.ZDEM[cerca].min(), C.ZDEM[cerca].max(),
        np.median(C.ZDEM[lejos]), C.ZDEM[lejos].min(), C.ZDEM[lejos].max()))
    R["geometria"] = dict(n_corredor=int(corredor.sum()), n_cerca=int(cerca.sum()), n_lejos=int(lejos.sum()),
                          cota_cerca=[float(np.median(C.ZDEM[cerca])), float(C.ZDEM[cerca].min()), float(C.ZDEM[cerca].max())],
                          cota_lejos=[float(np.median(C.ZDEM[lejos])), float(C.ZDEM[lejos].min()), float(C.ZDEM[lejos].max())],
                          dias_placebo=dias, horas=[slots[0], slots[-1]])
    cuadros = [(d, s, P.pos.get(f"{d}_{s}")) for d in dias for s in slots]
    cuadros = [(d, s, i) for d, s, i in cuadros if i is not None]
    print("cuadros placebo en la pila:", len(cuadros), "de", len(dias) * len(slots))

    # ---- 1. variantes de linea base (dBT11 y dBTD en el corredor, dias placebo) ----
    print("\n== 1. Variantes de linea base (corredor, dias placebo, todas las horas del evento) ==")
    filas = []
    for nom, kw in (("H17: P75, +-90 min, 6 d", dict(tod=90, pct=75, dias=6)),
                    ("P75, +-20 min, 6 d", dict(tod=20, pct=75, dias=6)),
                    ("P50, +-20 min, 6 d", dict(tod=20, pct=50, dias=6)),
                    ("P90, +-20 min, 6 d", dict(tod=20, pct=90, dias=6)),
                    ("P75, +-20 min, 3 d", dict(tod=20, pct=75, dias=3)),
                    ("P75, +-10 min, 6 d", dict(tod=10, pct=75, dias=6))):
        a11, abt = [], []
        for d, s, i in cuadros:
            an = P.anomalias(i, **kw)
            if an is None:
                continue
            a11.append(an[0][corredor])
            abt.append(an[1][corredor])
        a11, abt = np.concatenate(a11), np.concatenate(abt)
        cl = a11 >= CLARO_K
        f = dict(variante=nom, n=len(a11), frac_despejado=round(float(cl.mean()), 3),
                 d11_mediana=round(float(np.nanmedian(a11)), 2), d11_sd_rob=round(sd_rob(a11), 2),
                 d11_claro_mediana=round(float(np.nanmedian(a11[cl])), 2), d11_claro_sd=round(float(np.nanstd(a11[cl])), 2),
                 dbtd_claro_mediana=round(float(np.nanmedian(abt[cl])), 3), dbtd_claro_sd=round(float(np.nanstd(abt[cl])), 3),
                 dbtd_sd_rob=round(sd_rob(abt), 3))
        filas.append(f)
        print(f)
    pd.DataFrame(filas).to_csv(os.path.join(C.RES, "ruido_variantes_base.csv"), index=False)
    P._base.clear()

    # ---- campos de anomalia de todos los cuadros placebo (variante elegida = constantes de h22_comun) ----
    A = {}
    for d, s, i in cuadros:
        an = P.anomalias(i)
        if an is not None:
            A[(d, s)] = an
    print("\ncuadros placebo con linea base:", len(A))
    nom = dict(d11=0, dbtd=1, dbtd8=2, beta=3)

    # ---- 2. distribucion y descomposicion, por banda de distancia y bloque horario ----
    print("\n== 2. Residuo por pixel-cuadro (dias placebo) ==")
    bloques = {"16:30-19:50": ("1630", "1950"), "20:00-21:50": ("2000", "2150"), "22:00-23:40": ("2200", "2340")}
    filas = []
    for zona, mk in (("cerca <=30 km", cerca), ("lejos >30 km", lejos)):
        for bl, (h0, h1) in list(bloques.items()) + [("todas", ("1630", "2340"))]:
            ks = [k for k in A if h0 <= k[1] <= h1]
            d11 = np.array([A[k][0][mk] for k in ks])        # (cuadros, pixeles)
            claro = d11 >= CLARO_K
            for med in ("d11", "dbtd", "dbtd8", "beta"):
                x = np.array([A[k][nom[med]][mk] for k in ks])
                f = dict(zona=zona, horas=bl, medida=med, cielo="todo", **desc(x))
                if med != "beta":
                    # descomposicion: modo comun del cuadro, sesgo persistente del pixel, resto
                    mc = np.nanmean(x, axis=1)
                    sp = np.nanmean(x - mc[:, None], axis=0)
                    resto = x - mc[:, None] - sp[None, :]
                    f.update(sd_modo_comun_cuadro=round(float(np.nanstd(mc)), 3),
                             sd_sesgo_pixel=round(float(np.nanstd(sp)), 3), sd_resto=round(float(np.nanstd(resto)), 3))
                else:
                    f["frac_con_dato"] = round(float(np.isfinite(x).mean()), 3)
                filas.append(f)
                xc = np.where(claro, x, np.nan)
                f2 = dict(zona=zona, horas=bl, medida=med, cielo="despejado (dBT11>=-3K)", **desc(xc))
                if med != "beta":
                    mc = np.nanmean(xc, axis=1)
                    sp = np.nanmean(xc - mc[:, None], axis=0)
                    resto = xc - mc[:, None] - sp[None, :]
                    f2.update(sd_modo_comun_cuadro=round(float(np.nanstd(mc)), 3),
                              sd_sesgo_pixel=round(float(np.nanstd(sp)), 3), sd_resto=round(float(np.nanstd(resto)), 3))
                f2["frac"] = round(float(claro.mean()), 3)
                filas.append(f2)
    t2 = pd.DataFrame(filas)
    t2.to_csv(os.path.join(C.RES, "ruido_distribucion.csv"), index=False)
    pd.set_option("display.width", 250)
    print(t2[t2.horas.isin(["todas", "22:00-23:40"])].to_string(index=False))

    # ---- 3a. autocorrelacion espacial (dominio <= 100 km, quitando la media del cuadro) ----
    print("\n== 3a. Autocorrelacion espacial (dominio <= 100 km del crater, media del cuadro quitada) ==")
    lags = (1, 2, 3, 4, 6, 8, 12, 16, 24, 32)
    filas = []
    for med in ("d11", "dbtd"):
        for cielo in ("todo", "cuadros despejados (>=90 % del dominio con dBT11>=-3K)"):
            num = {L: 0.0 for L in lags}
            den = {L: 0.0 for L in lags}
            nfr = 0
            for k, an in A.items():
                x = an[nom[med]].astype("float64")
                if cielo != "todo" and (an[0][dom] >= CLARO_K).mean() < 0.9:
                    continue
                nfr += 1
                a = np.where(dom, x, np.nan)
                a = a - np.nanmean(a)
                for L in lags:
                    for p, q in ((a[:, :-L], a[:, L:]), (a[:-L, :], a[L:, :])):
                        g = np.isfinite(p) & np.isfinite(q)
                        num[L] += float((p[g] * q[g]).sum())
                        den[L] += float(0.5 * ((p[g] ** 2).sum() + (q[g] ** 2).sum()))
            f = dict(medida=med, cielo=cielo, cuadros=nfr, **{f"r_{L}px": round(num[L] / den[L], 3) if den[L] else np.nan for L in lags})
            filas.append(f)
            print(f)
    pd.DataFrame(filas).to_csv(os.path.join(C.RES, "ruido_autocorr_espacial.csv"), index=False)

    # ---- 3b. autocorrelacion temporal (pixeles del corredor) ----
    print("\n== 3b. Autocorrelacion temporal (pixeles del corredor; 'local' = media del corredor del cuadro quitada) ==")
    filas = []
    for med in ("d11", "dbtd"):
        for lag in (10, 20, 30, 60, 120, 1440):
            a, b, al, bl_ = [], [], [], []
            for (d, s), an in A.items():
                t = datetime.strptime(d + s, "%Y%m%d%H%M")
                t2_ = t + pd.Timedelta(minutes=lag)
                k2 = (t2_.strftime("%Y%m%d"), t2_.strftime("%H%M"))
                if k2 not in A:
                    continue
                x, y = an[nom[med]][corredor].astype("float64"), A[k2][nom[med]][corredor].astype("float64")
                a.append(x); b.append(y)
                al.append(x - np.nanmean(x)); bl_.append(y - np.nanmean(y))
            if not a:
                continue
            f = dict(medida=med, desfase_min=lag, pares_de_cuadros=len(a), r=round(corr(np.concatenate(a), np.concatenate(b)), 3),
                     r_local=round(corr(np.concatenate(al), np.concatenate(bl_)), 3))
            filas.append(f)
            print(f)
    pd.DataFrame(filas).to_csv(os.path.join(C.RES, "ruido_autocorr_temporal.csv"), index=False)

    # ---- 4. dependencia con la cota dentro del cuadro (dominio <= 100 km, pixeles despejados) ----
    print("\n== 4. Pendiente del residuo con la cota, por cuadro (K por km; dominio <= 100 km, pixeles despejados) ==")
    filas = []
    z = C.ZDEM / 1000.0
    for (d, s), an in A.items():
        g = dom & (an[0] >= CLARO_K) & np.isfinite(an[1])
        if g.sum() < 500:
            continue
        f = dict(dia=d, hora=s, n=int(g.sum()))
        for med in ("d11", "dbtd"):
            x = an[nom[med]][g].astype("float64")
            p = np.polyfit(z[g], x, 1)
            f[f"pend_{med}"] = float(p[0])
            f[f"r_{med}"] = float(np.corrcoef(z[g], x)[0, 1])
        filas.append(f)
    t4 = pd.DataFrame(filas)
    t4.to_csv(os.path.join(C.RES, "ruido_pendiente_cota.csv"), index=False)
    for med in ("d11", "dbtd"):
        print(med, "pendiente K/km: mediana %.3f, sd entre cuadros %.3f, p05 %.3f, p95 %.3f; |r| mediana %.2f" % (
            t4[f"pend_{med}"].median(), t4[f"pend_{med}"].std(), t4[f"pend_{med}"].quantile(.05),
            t4[f"pend_{med}"].quantile(.95), t4[f"r_{med}"].abs().median()))
    R["pendiente_cota"] = {med: dict(mediana=float(t4[f"pend_{med}"].median()), sd=float(t4[f"pend_{med}"].std()),
                                     r_abs_mediana=float(t4[f"r_{med}"].abs().median())) for med in ("d11", "dbtd")}

    # ---- 5. estado del cielo en el entorno de la huella (dias placebo y 14-11; no toca pixeles publicados) ----
    print("\n== 5. Cielo del entorno de la huella: fraccion despejada (dBT11 >= -3 K) a 4-12 px, por cuadro ==")
    filas = []
    for d in dias + ["20261114"]:
        for c in HU:
            i = P.pos.get(f"{d}_{c[9:]}")
            if i is None or P.base(i) is None:
                continue
            filas.append(dict(dia=d, hora=c[9:], f_t=Q.cielo_entorno(P, i, Q.anillo(HU, c, forma)),
                              f_l=Q.cielo_entorno(P, i, Q.anillo(HU, c, forma, solo_lejos=True))))
    F = pd.DataFrame(filas)
    F.round(3).to_csv(os.path.join(C.RES, "ruido_cielo_entorno.csv"), index=False)
    g = F.groupby("dia").agg(cuadros=("f_t", "size"), entorno_ge05=("f_t", lambda s: int((s >= Q.ENTORNO_MIN).sum())),
                             cuadros_con_lejos=("f_l", lambda s: int(s.notna().sum())),
                             entorno_lejos_ge05=("f_l", lambda s: int((s >= Q.ENTORNO_MIN).sum())),
                             f_t_mediana=("f_t", "median"), f_l_mediana=("f_l", "median"))
    print(g.round(2).to_string())
    e = F[(F.dia == "20261114") & F.f_l.notna()]
    print("14-11, cuadros con pixeles a > 30 km:", {h: round(v, 2) for h, v in zip(e.hora, e.f_l)})
    R["cielo_entorno"] = g.round(3).reset_index().to_dict("records")

    # ---- 6. ruido del estadistico de la prueba: huella real en dias placebo, control pareado ----
    print("\n== 6. Estadistico de la prueba en dias placebo (huella real del 14-11 puesta en cada dia sin evento) ==")
    T = pd.concat([t for t in (Q.tabla_dia(P, HU, d) for d in dias) if t is not None], ignore_index=True)
    T.to_pickle(os.path.join(C.H22, "placebo_pixeles.pkl"))
    print("pixeles-cuadro placebo:", len(T), "; sin control despejado suficiente:", int(T.c_d11.isna().sum()),
          "; controles despejados por pixel: mediana", int(T.n_ctrl.median()), "p05", int(T.n_ctrl.quantile(.05)))
    filas, filas_c = [], []
    G = Q.grupos(T)
    for g, mk in G.items():
        for d, s in T[mk].groupby("dia"):
            for pre in ("", "A_", "B_"):
                filas.append(dict(grupo=g, control=pre or "D_", dia=d, cuadros=s.hora.nunique(), **Q.resumen(s, pre=pre)))
        for (d, h), s in T[mk].groupby(["dia", "hora"]):
            if len(s) >= 5:
                filas_c.append(dict(grupo=g, dia=d, hora=h, **Q.resumen(s)))
    t5 = pd.DataFrame(filas)
    t5c = pd.DataFrame(filas_c)
    t5.to_csv(os.path.join(C.RES, "ruido_estadistico_placebo_por_dia.csv"), index=False)
    t5c.to_csv(os.path.join(C.RES, "ruido_estadistico_placebo_por_cuadro.csv"), index=False)
    res5 = {}

    def q(x, p):
        return float(x.quantile(p))

    for g in G:
        for pre in ("D_", "A_", "B_"):
            s = t5[(t5.grupo == g) & (t5.control == pre) & (t5.n >= 20)]
            if len(s) == 0:
                continue
            linea = [f"[{g} | control {pre[0]}] dias (n>=20) {len(s)}, n/dia {int(s.n.median())}"]
            for m in ("d11", "dbtd", "beta"):
                D, auc = s[f"D_{m}"].dropna(), s[f"auc_{m}"].dropna()
                if len(D) == 0:
                    linea.append(f"\n     {m}: SIN DATO")
                    continue
                res5[f"{g} | {pre[0]} | {m}"] = dict(dias=int(len(D)), D=[round(float(v), 3) for v in sorted(D)],
                                                    auc=[round(float(v), 3) for v in sorted(auc)],
                                                    n_mediana=float(s[f"n_{m}"].median()))
                linea.append(f"\n     {m}: n {int(s[f'n_{m}'].median())} | D por dia {np.round(sorted(D), 2).tolist()} | AUC por dia {np.round(sorted(auc), 2).tolist()}")
            if pre == "D_":
                linea.append(f"\n     fraccion fria (> 3 K bajo el control) por dia {np.round(sorted(s.frio.dropna()), 2).tolist()}")
                sc = t5c[t5c.grupo == g]
                if len(sc) >= 5:
                    res5[f"{g} | por cuadro"] = dict(cuadros=int(len(sc)),
                                                    D_d11=[q(sc.D_d11, p) for p in (.05, .5, .95)], D_d11_sd=float(sc.D_d11.std()),
                                                    auc_d11=[q(sc.auc_d11, p) for p in (.05, .5, .95)],
                                                    D_dbtd=[q(sc.D_dbtd, p) for p in (.05, .5, .95)], D_dbtd_sd=float(sc.D_dbtd.std()),
                                                    auc_dbtd=[q(sc.auc_dbtd, p) for p in (.05, .5, .95)])
                    linea.append(f"\n     por cuadro ({len(sc)} cuadros con >= 5 px): D_d11 p05 {q(sc.D_d11, .05):+.2f} p50 {q(sc.D_d11, .5):+.2f} p95 {q(sc.D_d11, .95):+.2f} sd {sc.D_d11.std():.2f}"
                                 f" | AUC_d11 p05 {q(sc.auc_d11, .05):.2f} p95 {q(sc.auc_d11, .95):.2f}"
                                 f" | D_dbtd p05 {q(sc.D_dbtd, .05):+.3f} p50 {q(sc.D_dbtd, .5):+.3f} p95 {q(sc.D_dbtd, .95):+.3f} sd {sc.D_dbtd.std():.3f}"
                                 f" | AUC_dbtd p05 {q(sc.auc_dbtd, .05):.2f} p95 {q(sc.auc_dbtd, .95):.2f}")
            print("".join(linea))
    R["estadistico_placebo"] = res5
    json.dump(R, open(os.path.join(C.RES, "ruido_resumen.json"), "w", encoding="utf-8"), indent=1)


if __name__ == "__main__":
    main()
