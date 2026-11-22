r"""H23: lee resultados\h23_celdas.csv y aplica la regla del criterio (§6 y §7): controles, veredicto por celda en
la cumbre de Chillan, e minimo detectable, y las tablas de las secundarias. Escribe resultados\h23_resumen.txt,
h23_veredicto.json y las figuras. No calcula nada nuevo sobre los datos de GOES.
Uso: python -I h23_resumen.py
"""
import json
import os
import sys

import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")
RES = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "resultados")
TRAMOS = {0: "00 a 06 UTC (21 a 03 Chile)", 1: "06 a 12 UTC (03 a 09 Chile)", 2: "12 a 18 UTC (09 a 15 Chile)",
          3: "18 a 24 UTC (15 a 21 Chile)"}
DET = ["D1", "D2", "D3", "D4", "D5"]
out = []


def p(*a):
    s = " ".join(str(x) for x in a)
    print(s)
    out.append(s)


def e_min(g, col="auc", umbral=0.80):
    """Primer cruce del umbral en la grilla de e (interpolacion lineal). g: filas de una celda, e > 0."""
    g = g[g.eps > 0].sort_values("eps")
    e, v = g.eps.values, g[col].values
    if not len(e):
        return "SIN DATO"
    if v[0] >= umbral:
        return f"<= {e[0]:.2f}"
    for i in range(1, len(e)):
        if v[i] >= umbral:
            return f"{e[i - 1] + (umbral - v[i - 1]) * (e[i] - e[i - 1]) / (v[i] - v[i - 1]):.2f}"
    return "> 0.90"


def main():
    d = pd.read_csv(os.path.join(RES, "h23_celdas.csv"))
    ok = d[d.estado == "ok"].copy()
    ver = {}
    ch = ok[(ok.volcan == "chillan") & (ok.bloque == "oct") & (ok.beta == 0.70)]

    p("== 0. Celdas SIN DATO ==")
    sd = d[d.estado == "SIN DATO"]
    p("celdas SIN DATO (cada una es una combinacion de terreno, poblacion, tramo, altura, e y beta):", len(sd))
    if len(sd):
        p(sd.groupby(["bloque", "volcan", "terreno", "pob", "tramo"]).agg(n=("n", "max"), ndias=("ndias", "max")).to_string())

    p("\n== 1. Control positivo: e 0,9 a 10 km, poblacion B, Chillan (pide AUC >= 0,95; D3 >= 0,90) ==")
    cp = ch[(ch.z_km == 10) & (ch.eps == 0.9) & (ch["pob"] == "B")]
    t = cp.pivot_table(index=["terreno", "tramo"], columns="det", values="auc")
    p(t.round(3).to_string())
    pasa = {det: bool((t[det] >= (0.90 if det == "D3" else 0.95)).all()) for det in DET if det in t}
    p("pasa el control positivo:", pasa)
    ver["control_positivo"] = pasa
    validos = [k for k, v in pasa.items() if v]
    p("\n   (informativo) e 0,9 a 4 km, poblacion B:")
    p(ch[(ch.z_km == 4) & (ch.eps == 0.9) & (ch["pob"] == "B")].pivot_table(index=["terreno", "tramo"], columns="det", values="auc").round(3).to_string())

    p("\n== 2. Control nulo (a): e = 0 por la misma tuberia (pide AUC 0,500 +- 0,001 y cambio de BT 0) ==")
    cn = ok[ok.eps == 0]
    p("celdas:", len(cn), " AUC min", cn.auc.min(), "max", cn.auc.max(), " |dBT11| max", cn.dbt11.abs().max(),
      " |dBTD| max", cn.dbtd.abs().max())
    ver["control_nulo_a"] = bool((cn.auc - 0.5).abs().max() <= 0.001 and cn.dbt11.abs().max() == 0)
    pl = json.load(open(os.path.join(RES, "h23_controles.json")))
    p("\n== 2b. Control nulo (b): placebo por mitades de dias, poblacion B (pide que el rango contenga 0,5) ==")
    cont = []
    for terr in ("cumbre", "bajo"):
        for tr, v in pl[f"placebo_{terr}"].items():
            if v == "SIN DATO":
                p(terr, TRAMOS[int(tr)], "SIN DATO")
                continue
            for det, r in v.items():
                c = r["p2_5"] <= 0.5 <= r["p97_5"]
                cont.append(c)
                p(f"{terr:7s} tramo {tr} {det}: mediana {r['mediana']:.3f}, rango 95 % {r['p2_5']:.3f} a {r['p97_5']:.3f}, "
                  f"{r['ndias']} dias, n {r['n']}{'' if c else '  <-- no contiene 0,5'}")
    ver["control_nulo_b_contiene_0_5"] = f"{sum(cont)} de {len(cont)}"

    p("\n== 3. VEREDICTO: cumbre de Chillan, poblacion B, beta 0,70, e 0,15 ==")
    p("   regla: FALSADA si AUC* > 0,80 e IC inferior > 0,70; NO CONCLUYENTE si AUC* > 0,80 e IC inferior <= 0,70")
    v = ch[(ch.terreno == "cumbre") & (ch["pob"] == "B") & (ch.eps == 0.15) & (ch.z_km < 10) & ch.det.isin(validos)]
    filas = []
    for _, r in v.sort_values(["tramo", "z_km", "det"]).iterrows():
        cat = "FALSADA" if (r.auc > 0.80 and r.lo > 0.70) else "NO CONCLUYENTE" if r.auc > 0.80 else "se sostiene"
        filas.append(dict(tramo=int(r.tramo), z_km=r.z_km, det=r.det, auc=round(r.auc, 3), lo=round(r.lo, 3),
                          hi=round(r.hi, 3), sentido=r.sentido, n=int(r.n), ndias=int(r.ndias), categoria=cat))
    vt = pd.DataFrame(filas)
    p(vt.to_string(index=False))
    ver["celdas_e015_cumbre_B"] = filas
    ver["n_falsadas"] = int((vt.categoria == "FALSADA").sum()) if len(vt) else None
    ver["n_no_concluyentes"] = int((vt.categoria == "NO CONCLUYENTE").sum()) if len(vt) else None
    ver["auc_max"] = float(vt.auc.max()) if len(vt) else None
    ver["hi_max"] = float(vt.hi.max()) if len(vt) else None
    ver["tramos_sin_dato"] = sorted(set(range(4)) - set(vt.tramo)) if len(vt) else list(range(4))
    if len(vt):
        sinD5 = vt[vt.det != "D5"]
        if (sinD5.categoria == "FALSADA").any():
            gl = "FALSADA en al menos un regimen con un detector operable"
        elif (vt.categoria == "FALSADA").any():
            gl = "FALSADA solo con D5 (visible en principio, con un detector que conoce la firma)"
        elif (vt.categoria == "NO CONCLUYENTE").any():
            gl = "NO CONCLUYENTE en al menos una celda; ninguna FALSADA"
        elif vt.hi.max() < 0.80:
            gl = "SE SOSTIENE como cota (CONFIRMADO: IC superior < 0,80 en todas las celdas con dato)"
        else:
            gl = "SE SOSTIENE como cota (SOSPECHA: alguna celda con IC superior >= 0,80)"
        ver["veredicto"] = gl
        p("\nVEREDICTO GLOBAL:", gl, "| tramos sin dato:", ver["tramos_sin_dato"])
    vc = ch[(ch.terreno == "cumbre") & (ch["pob"] == "C") & (ch.eps == 0.15) & (ch.z_km < 10) & ch.det.isin(validos)]
    ver["poblacion_C_falsadas"] = int(((vc.auc > 0.80) & (vc.lo > 0.70)).sum())
    ver["poblacion_C_auc_max"] = float(vc.auc.max()) if len(vc) else None
    p("poblacion C (oraculo), e 0,15, cumbre: celdas que falsan", ver["poblacion_C_falsadas"], "de", len(vc), "; AUC* max", ver["poblacion_C_auc_max"])
    va = ch[(ch.terreno == "cumbre") & (ch["pob"] == "A") & (ch.eps == 0.15) & (ch.z_km < 10) & ch.det.isin(validos)]
    p("poblacion A (todo cielo), e 0,15, cumbre: AUC* max", round(va.auc.max(), 3) if len(va) else None)
    vb = ch[(ch.terreno == "bajo") & (ch["pob"] == "B") & (ch.eps == 0.15) & (ch.z_km < 10) & ch.det.isin(validos)]
    p("terreno bajo, poblacion B, e 0,15: celdas con AUC* > 0,80 e IC inf > 0,70:", int(((vb.auc > 0.80) & (vb.lo > 0.70)).sum()),
      "de", len(vb), "; AUC* max", round(vb.auc.max(), 3) if len(vb) else None)

    p("\n== 4. Curva: AUC* por e, cumbre y terreno bajo de Chillan, poblacion B, por tramo y altura ==")
    for terr in ("cumbre", "bajo"):
        g = ch[(ch.terreno == terr) & (ch["pob"] == "B") & (ch.z_km < 10) & (ch.eps > 0)]
        p(f"-- {terr} --")
        p(g.pivot_table(index=["tramo", "z_km", "det"], columns="eps", values="auc").round(3).to_string())

    p("\n== 5. e minimo detectable (AUC* cruza 0,80 | deteccion al 1 % de falsas alarmas cruza 50 %) ==")
    em = []
    for (terr, pob, tramo, z, det), g in ch[ch.z_km < 10].groupby(["terreno", "pob", "tramo", "z_km", "det"]):
        em.append(dict(terreno=terr, pob=pob, tramo=tramo, z_km=z, det=det, e_auc=e_min(g), e_pod1=e_min(g, "pod1", 0.5)))
    em = pd.DataFrame(em)
    for pob in "BAC":
        for col in ("e_auc", "e_pod1"):
            p(f"-- poblacion {pob}, {col} --")
            p(em[em["pob"] == pob].pivot_table(index=["terreno", "tramo", "z_km"], columns="det", values=col, aggfunc="first").to_string())
    ver["e_min"] = em.to_dict("records")

    p("\n== 6. Senal fisica que produce la capa (mediana), poblacion B, e 0,15 ==")
    f = ch[(ch["pob"] == "B") & (ch.eps == 0.15) & (ch.det == "D1") & (ch.z_km < 10)]
    p(f[["terreno", "tramo", "z_km", "n", "ndias", "contraste", "dbt11", "dbtd", "etot_eq"]].sort_values(["terreno", "tramo", "z_km"]).round(3).to_string(index=False))
    ver["senal_e015"] = f[["terreno", "tramo", "z_km", "contraste", "dbt11", "dbtd", "etot_eq"]].round(4).to_dict("records")

    p("\n== 7. S1: integrar en el tiempo (poblacion B), e minimo por AUC* 0,80 ==")
    it = ok[(ok.volcan == "chillan") & ok["pob"].isin(["B", "B_int6", "B_int18"]) & (ok.beta == 0.70) & (ok.z_km < 10) & ok.det.isin(["D1", "D2", "D4"])]
    ei = [dict(terreno=a, pob=b, tramo=c, z_km=z, det=dd, e_auc=e_min(g))
          for (a, b, c, z, dd), g in it.groupby(["terreno", "pob", "tramo", "z_km", "det"])]
    ei = pd.DataFrame(ei)
    p(ei.pivot_table(index=["terreno", "tramo", "z_km", "det"], columns="pob", values="e_auc", aggfunc="first").to_string())
    a15 = it[it.eps == 0.15].pivot_table(index=["terreno", "tramo", "z_km", "det"], columns="pob", values="auc")
    p("-- AUC* a e 0,15 --")
    p(a15.round(3).to_string())
    ver["integracion_auc_e015"] = a15.round(4).reset_index().to_dict("records")

    p("\n== 8. S2: cumbres de control (poblacion B, e 0,15): AUC* por volcan y bloque ==")
    s2 = ok[(ok["pob"] == "B") & (ok.eps == 0.15) & (ok.beta == 0.70) & (ok.z_km < 10)]
    s2 = s2.assign(vb=s2.volcan + "_" + s2.bloque)
    p(s2[s2.terreno == "cumbre"].pivot_table(index=["tramo", "z_km", "det"], columns="vb", values="auc").round(3).to_string())
    p("-- maximo de AUC* por volcan y bloque, cumbre y bajo --")
    p(s2.groupby(["vb", "terreno"]).auc.max().round(3).to_string())
    e2 = [dict(vb=a + "_" + b, terreno=t, tramo=tr, z_km=z, det=dd, e_auc=e_min(g))
          for (a, b, t, tr, z, dd), g in ok[(ok["pob"] == "B") & (ok.beta == 0.70) & (ok.z_km < 10)].groupby(["volcan", "bloque", "terreno", "tramo", "z_km", "det"])]
    e2 = pd.DataFrame(e2)
    p("-- e minimo (AUC* 0,80), cumbre --")
    p(e2[e2.terreno == "cumbre"].pivot_table(index=["tramo", "z_km", "det"], columns="vb", values="e_auc", aggfunc="first").to_string())

    p("\n== 9. S3: sensibilidad a beta (cumbre y bajo de Chillan, poblacion B, e 0,15) ==")
    s3 = ok[(ok.volcan == "chillan") & (ok["pob"] == "B") & (ok.eps == 0.15) & (ok.z_km < 10)]
    p(s3.pivot_table(index=["terreno", "tramo", "z_km", "det"], columns="beta", values="auc").round(3).to_string())

    p("\n== 10. S4: eventos reales en los pixeles de cumbre ==")
    for e in json.load(open(os.path.join(RES, "h23_eventos.json"))):
        p(json.dumps(e, ensure_ascii=False))

    p("\n== 11. S5: cuanto exagera la BTD la forma analitica (cumbre, poblacion B, e 0,15, beta 0,70, detector D2) ==")
    p("   la capa real se ve mas fria que T_tope por el aire de encima (h23_forma_rt.json): la BTD real baja menos.")
    p("   exageracion = correccion / senal inyectada; AUC* corregido = AUC* de D2 interpolado a la emisividad equivalente")
    rt = json.load(open(os.path.join(RES, "h23_forma_rt.json")))["resumen"]
    e11 = 0.15
    e12 = 1 - (1 - e11) ** 0.70
    s5 = []
    cur = ch[(ch.terreno == "cumbre") & (ch["pob"] == "B") & (ch.det == "D2")]
    for _, r in cur[cur.eps == 0.15].sort_values(["tramo", "z_km"]).iterrows():
        if r.z_km >= 10:
            continue
        m = rt[f"{r.z_km:.0f}km"]
        corr = e11 * m["d11"]["mediana"] - e12 * m["d12"]["mediana"]       # K que la BTD real baja de menos
        exag = corr / abs(r.dbtd) if r.dbtd < 0 else float("nan")
        g = cur[(cur.tramo == r.tramo) & (cur.z_km == r.z_km)].sort_values("eps")
        eq = e11 * (1 - exag) if exag == exag else float("nan")
        auc_eq = float(pd.Series(g.auc.values, index=g.eps.values).reindex(sorted(set(g.eps) | {eq})).interpolate("index")[eq]) if eq == eq else float("nan")
        s5.append(dict(tramo=int(r.tramo), z_km=r.z_km, dbtd_inyectada=round(r.dbtd, 3), correccion_K=round(corr, 3),
                       exageracion=round(exag, 3), e_equivalente=round(eq, 3), auc_inyectado=round(r.auc, 3),
                       auc_corregido=round(auc_eq, 3)))
    p(pd.DataFrame(s5).to_string(index=False))
    ver["s5_forma_analitica"] = s5

    open(os.path.join(RES, "h23_resumen.txt"), "w", encoding="utf-8").write("\n".join(out) + "\n")
    json.dump(ver, open(os.path.join(RES, "h23_veredicto.json"), "w"), indent=1, ensure_ascii=False)
    figuras(ch)


def figuras(ch):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    col = {"D1": "#1f77b4", "D2": "#d62728", "D3": "#2ca02c", "D4": "#9467bd", "D5": "#444444"}
    nom = {"D1": "D1: BT11 contra su línea base", "D2": "D2: BTD (11 − 12 µm) contra su línea base",
           "D3": "D3: β(12/11)", "D4": "D4: BT11, doble diferencia con el entorno",
           "D5": "D5: combinación lineal que conoce la firma (cota)"}
    for z in (3.0, 4.0, 5.0):
        fig, ax = plt.subplots(2, 4, figsize=(15, 6.5), sharex=True, sharey=True)
        for i, terr in enumerate(("cumbre", "bajo")):
            for tr in range(4):
                a = ax[i, tr]
                g = ch[(ch.terreno == terr) & (ch["pob"] == "B") & (ch.z_km == z) & (ch.tramo == tr) & (ch.eps > 0)]
                for det in DET:
                    h = g[g.det == det].sort_values("eps")
                    if not len(h):
                        continue
                    a.plot(h.eps, h.auc, marker="o", ms=3, color=col[det], label=nom[det], lw=1.8 if det != "D5" else 1.2,
                           ls="--" if det == "D5" else "-")
                    a.fill_between(h.eps, h.lo, h.hi, color=col[det], alpha=0.10)
                if not len(g):
                    a.text(0.5, 0.75, "SIN DATO\n(menos de 8 días con\nla escena despejada)", transform=a.transAxes, ha="center")
                a.axhline(0.8, color="k", lw=0.8, ls=":"); a.axvline(0.15, color="gray", lw=0.8, ls=":")
                a.set_xscale("log"); a.set_xticks([0.05, 0.1, 0.15, 0.3, 0.5, 0.9]); a.set_xticklabels(["0,05", "0,1", "0,15", "0,3", "0,5", "0,9"])
                a.set_ylim(0.45, 1.01)
                a.set_title(f"{'Cumbre' if terr == 'cumbre' else 'Terreno bajo'}, {TRAMOS[tr]}", fontsize=9)
                if tr == 0:
                    a.set_ylabel("AUC* (0,5 = azar)")
                if i == 1:
                    a.set_xlabel("emisividad inyectada a 11 µm")
        ax[0, 3].legend(*ax[0, 0].get_legend_handles_labels(), fontsize=8, loc="lower center")
        fig.suptitle(f"H23: recuperación de una capa de ceniza inyectada a {z:.0f} km. Chillán, entorno despejado (población B), "
                     f"fondo 21-09 al 23-10-2026.\nLínea punteada horizontal: AUC 0,80 (umbral del criterio). Vertical: emisividad 0,15. "
                     f"Banda: IC 95 % remuestreando días", fontsize=10)
        fig.tight_layout()
        fig.savefig(os.path.join(RES, f"h23_curva_{z:.0f}km.png"), dpi=110)
        plt.close(fig)


if __name__ == "__main__":
    main()
