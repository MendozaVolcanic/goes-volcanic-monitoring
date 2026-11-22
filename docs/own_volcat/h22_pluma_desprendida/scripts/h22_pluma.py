r"""H22, tarea 2: la prueba de la pluma del 14-11 (evento ASHPLUMEPUFF de las 16:30 UTC), segun
criterio_2026-11-22.md. Usa las mismas funciones que la medicion de ruido (h22_prueba.py).

Pasos: (1) instrumento; (2) pixeles publicados (event_idx >= 0) contra su linea base y contra los controles
pareados, por distancia al crater, estado del cielo del entorno y cenit solar; (3) placebo temporal: la misma huella
en los dias sin evento; (4) placebo espacial: la huella corrida dentro del 14-11; (5) control positivo: capa
semitransparente sintetica inyectada en los mismos pixeles; (6) veredicto con la regla del criterio.

Escribe en resultados/ solo numeros por cuadro o por grupo (sin posiciones ni grillas). La tabla por pixel queda en
D:\goes_notas\s17\h22 (trae campos de SSEC, no va al repo). Uso: python -I h22_pluma.py
"""
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import h22_comun as C  # noqa: E402
import h22_prueba as Q  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
pd.set_option("display.width", 250)
pd.set_option("display.max_columns", 60)
DIA = os.environ.get("H22_DIA", "20261114")   # otro dia = ensayo en seco del codigo sobre un dia sin evento
# Regla del criterio (fijada con la medicion de ruido, antes de mirar la pluma)
SENAL = {"d11": (-1.5, 0.7), "dbtd": (-0.3, 0.7)}     # senal: D <= umbral y AUC >= umbral
NULA = {"d11": (-0.5, 0.6), "dbtd": (-0.15, 0.6)}     # sin senal: D > umbral y AUC < umbral
ESPACIAL_MAX = 0.05                                    # y a lo mas 5 % de las huellas corridas igual de extremas
INY_E = (0.005, 0.01, 0.02, 0.03, 0.05, 0.10, 0.15, 0.20, 0.50, 1.0)
INY_T = (255.0, 270.0)
INY_BETA = 0.7
INY_OBLIGATORIA_K = -2.0                               # la menor inyeccion con enfriamiento mediano <= -2 K debe verse
MIN_N = 20


def zona(m, D, auc):
    if not (np.isfinite(D) and np.isfinite(auc)):
        return "SIN DATO"
    if D <= SENAL[m][0] and auc >= SENAL[m][1]:
        return "senal"
    if D > NULA[m][0] and auc < NULA[m][1]:
        return "nula"
    return "gris"


def r3(v):
    return None if v is None or not np.isfinite(v) else round(float(v), 3)


def lineas_grupo(nom, ev, plac, pre):
    out = []
    for m in ("d11", "dbtd", "beta", "dbtd8"):
        if ev[f"n_{m}"] == 0:
            out.append(f"   {m:6s} SIN DATO (ningun pixel con valor y control)")
            continue
        Dp = sorted(round(p[f"D_{m}"], 2) for p in plac if np.isfinite(p[f"D_{m}"]) and p[f"n_{m}"] >= MIN_N)
        Ap = sorted(round(p[f"auc_{m}"], 2) for p in plac if np.isfinite(p[f"auc_{m}"]) and p[f"n_{m}"] >= MIN_N)
        z = f" zona {zona(m, ev[f'D_{m}'], ev[f'auc_{m}'])}" if m in SENAL and pre == "" else ""
        out.append(f"   {m:6s} n {ev[f'n_{m}']:4d} mediana {ev[f'med_{m}']:+.3f} | D {ev[f'D_{m}']:+.3f} AUC {ev[f'auc_{m}']:.3f}{z}"
                   f" | placebo por dia: D {Dp} AUC {Ap}")
    return out


def main():
    P = C.Pila()
    HU = Q.huellas_evento()
    dias = Q.dias_placebo(P)
    out = {"dia": DIA, "dias_placebo": dias, "regla": dict(senal=SENAL, nula=NULA, espacial_max=ESPACIAL_MAX)}
    RES = C.RES if DIA == "20261114" else os.path.join(C.H22, f"ensayo_{DIA}")
    os.makedirs(RES, exist_ok=True)
    h0 = next(iter(HU.values()))
    print("unidades VOLCAT (masa, altura):", h0["unidades"], "; T de tropopausa del objeto (mediana de cuadros):",
          round(float(np.median([h["ttrop"] for h in HU.values()])), 1), "K")

    # ---------- 1. instrumento ----------
    print("== 1. Instrumento ==")
    n_h = sum(len(h["wy"]) for h in HU.values())
    fin = sum(int(np.isfinite(P.b14[P.pos[c]][h["wy"], h["wx"]]).sum() + np.isfinite(P.b15[P.pos[c]][h["wy"], h["wx"]]).sum())
              for c, h in HU.items())
    dif = np.concatenate([P.b14[P.pos[c]][h["wy"], h["wx"]] - h["bt11_ev"] for c, h in HU.items()])
    print(f"pixeles publicados {n_h}; valores L1b finitos {fin} de {2 * n_h}; BT11 L1b menos BT11 del archivo de evento en la "
          f"huella: mediana {np.median(dif):+.3f} K, max |dif| {np.max(np.abs(dif)):.3f} K")
    out["instrumento"] = dict(n_huella=n_h, l1b_finitos=fin, bt11_dif_mediana=r3(np.median(dif)),
                              bt11_dif_max=r3(np.max(np.abs(dif))))

    # ---------- 2. pluma y 3. placebo temporal ----------
    T = Q.tabla_dia(P, HU, DIA, con_extra=True)
    T.to_pickle(os.path.join(C.H22, f"pluma_pixeles_{DIA}.pkl"))
    PL = {d: Q.tabla_dia(P, HU, d) for d in dias}
    PL = {d: t for d, t in PL.items() if t is not None}
    horas_dec = sorted(T[T.lejos & T.elegible].hora.unique())
    print(f"\n== 2. Pluma 14-11: {len(T)} pixeles-cuadro en {T.cuadro.nunique()} cuadros; a > 30 km: {int(T.lejos.sum())} ==")
    print("cuadros con pixeles lejanos y entorno >= 50 % despejado (deciden):", horas_dec,
          "; pixeles:", int((T.lejos & T.elegible).sum()))
    out["horas_deciden"] = horas_dec

    def G(t):
        g = Q.grupos(t)
        g = {"DECIDE: lejos, entorno despejado, cuadros del evento": t.lejos & t.elegible & t.hora.isin(horas_dec), **g}
        return g

    filas = []
    res_grupo = {}
    for g in G(T):
        s = T[G(T)[g]]
        if len(s) == 0:
            continue
        print(f"\n[{g}] n {len(s)} en {s.cuadro.nunique()} cuadros; cenit {s.sza.min():.1f} a {s.sza.max():.1f}; distancia mediana "
              f"{s.dist.median():.1f} km; cota mediana {s.z.median():.0f} m; BT11 mediana {s.bt11.median():.2f} K; "
              f"entorno despejado {np.where(s.lejos, s.f_l, s.f_t).min():.2f} a {np.where(s.lejos, s.f_l, s.f_t).max():.2f}")
        print(f"   VOLCAT: P publicada >= 0,5 en {(s.S >= 0.5).mean():.1%}; P IR maxima {s.SL.max():.3f}; masa mediana "
              f"{s.masa.median():.3f} (n {int(s.masa.notna().sum())}); altura mediana {s.alt.median():.2f} (n {int(s.alt.notna().sum())})")
        fila = dict(grupo=g, n=len(s), cuadros=int(s.cuadro.nunique()), sza_min=r3(s.sza.min()), sza_max=r3(s.sza.max()),
                    dist_mediana=r3(s.dist.median()), cota_mediana=r3(s.z.median()), bt11_mediana=r3(s.bt11.median()),
                    S_ge05=r3((s.S >= 0.5).mean()), SL_max=r3(s.SL.max()), masa_mediana=r3(s.masa.median()),
                    alt_mediana=r3(s.alt.median()))
        for pre in ("", "A_", "B_"):
            ev = Q.resumen(s, pre=pre)
            plac = [Q.resumen(t[G(t)[g]], pre=pre) for t in PL.values() if G(t)[g].sum() >= MIN_N]
            print(f"  control {pre[0] if pre else 'D'} (dias placebo con >= {MIN_N} px: {len(plac)})"
                  + (f"; fraccion fria {ev.get('frio', np.nan):.2f}, placebo {sorted(round(p["frio"], 2) for p in plac if np.isfinite(p.get("frio", np.nan)))}" if pre == "" else ""))
            for ln in lineas_grupo(g, ev, plac, pre):
                print(ln)
            k = pre or "D_"
            for m in ("d11", "dbtd", "beta", "dbtd8"):
                fila.update({f"{k}n_{m}": ev[f"n_{m}"], f"{k}D_{m}": r3(ev[f"D_{m}"]), f"{k}auc_{m}": r3(ev[f"auc_{m}"]),
                             f"{k}med_{m}": r3(ev[f"med_{m}"]),
                             f"{k}plac_D_{m}": sorted(r3(p[f"D_{m}"]) for p in plac if np.isfinite(p[f"D_{m}"]) and p[f"n_{m}"] >= MIN_N),
                             f"{k}plac_auc_{m}": sorted(r3(p[f"auc_{m}"]) for p in plac if np.isfinite(p[f"auc_{m}"]) and p[f"n_{m}"] >= MIN_N)})
            if pre == "":
                fila["frio"] = r3(ev.get("frio", np.nan))
                fila["plac_frio"] = sorted(round(p["frio"], 3) for p in plac if np.isfinite(p.get("frio", np.nan)))
                res_grupo[g] = ev
        filas.append(fila)
    json.dump(filas, open(os.path.join(RES, "pluma_por_grupo.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)

    # por cuadro (sin posiciones)
    pc = []
    for c, s in T.groupby("cuadro"):
        for nom, ss in (("cerca", s[~s.lejos]), ("lejos", s[s.lejos])):
            if len(ss):
                r = Q.resumen(ss)
                rb = Q.resumen(ss, pre="B_")
                pc.append(dict(cuadro=c, zona=nom, sza=round(float(ss.sza.iloc[0]), 1), n=len(ss),
                               entorno_despejado=r3(ss.f_l.iloc[0] if nom == "lejos" else ss.f_t.iloc[0]),
                               dist_mediana=round(float(ss.dist.median()), 1), bt11=round(float(ss.bt11.median()), 2),
                               d11_mediana=r3(ss.d11.median()), dbtd_mediana=r3(ss.dbtd.median()), btd_mediana=r3(ss.btd.median()),
                               n_ctrl_D=r["n_d11"], D_d11=r3(r["D_d11"]), auc_d11=r3(r["auc_d11"]), frio=r3(r.get("frio", np.nan)),
                               D_dbtd=r3(r["D_dbtd"]), auc_dbtd=r3(r["auc_dbtd"]), n_beta=r["n_beta"], D_beta=r3(r["D_beta"]),
                               B_D_dbtd=r3(rb["D_dbtd"]), B_auc_dbtd=r3(rb["auc_dbtd"])))
    PC = pd.DataFrame(pc)
    PC.to_csv(os.path.join(RES, "pluma_por_cuadro.csv"), index=False)
    print("\nPor cuadro, pixeles a > 30 km:")
    print(PC[PC.zona == "lejos"].drop(columns=["zona"]).to_string(index=False))

    # ---------- 4. placebo espacial (poblacion que decide) ----------
    print("\n== 4. Placebo espacial: huella lejana de los cuadros que deciden, corrida dentro del 14-11 ==")
    forma = C.LAT.shape
    HUd = {c: h for c, h in HU.items() if c[9:] in horas_dec}
    lej = {c: (h["wy"][C.DIST[h["wy"], h["wx"]] > 30], h["wx"][C.DIST[h["wy"], h["wx"]] > 30]) for c, h in HUd.items()}
    excl = {c: Q.exclusion(HU, c, forma) for c in HUd}
    corr = []
    for dy in range(-40, 41, 3):
        for dx in range(-40, 41, 3):
            ok = (dy, dx) != (0, 0)
            for c, (wy, wx) in lej.items():
                y, x = wy + dy, wx + dx
                if y.min() < 0 or x.min() < 0 or y.max() >= forma[0] or x.max() >= forma[1] or excl[c][y, x].any():
                    ok = False
                    break
            if ok:
                corr.append((dy, dx))
    print("corrimientos validos:", len(corr))
    dec = "DECIDE: lejos, entorno despejado, cuadros del evento"
    dias_cl = [d for d, t in PL.items() if G(t)[dec].sum() >= MIN_N and Q.resumen(t[G(t)[dec]]).get("frio", 1.0) < 0.5]
    print("dias placebo con entorno despejado en los cuadros que deciden y huella no cubierta por nube:", dias_cl)
    esp = []
    for dy, dx in corr:
        t = Q.tabla_dia(P, HUd, DIA, solo_lejos=True, corr=(dy, dx), todas=HU)
        f = dict(dist_px=round(float(np.hypot(dy, dx)), 1), **Q.resumen(t, ("d11", "dbtd")))
        # sesgo propio del lugar: el mismo corrimiento en los dias placebo despejados
        pl = []
        for d in dias_cl:
            tp = Q.tabla_dia(P, HUd, d, solo_lejos=True, corr=(dy, dx), todas=HU)
            pl.append(Q.resumen(tp[tp.elegible], ("d11", "dbtd")))
        for m in ("d11", "dbtd"):
            v = [x[f"D_{m}"] for x in pl if np.isfinite(x[f"D_{m}"])]
            f[f"sesgo_{m}"] = float(np.median(v)) if v else np.nan
            f[f"DiD_{m}"] = f[f"D_{m}"] - f[f"sesgo_{m}"]
        esp.append(f)
    E = pd.DataFrame(esp)
    E.to_csv(os.path.join(RES, "placebo_espacial.csv"), index=False)
    ev = res_grupo[dec]
    plac_ev = [Q.resumen(PL[d][G(PL[d])[dec]]) for d in dias_cl]
    out["placebo_espacial"] = {"corrimientos": len(corr), "dias_sesgo": dias_cl}
    frac_esp, supera_temporal = {}, {}
    for m in ("d11", "dbtd"):
        Dp = [x[f"D_{m}"] for x in plac_ev]
        Ap = [x[f"auc_{m}"] for x in plac_ev]
        did0 = ev[f"D_{m}"] - float(np.median(Dp)) if Dp else np.nan
        supera_temporal[m] = bool(Dp and ev[f"D_{m}"] < min(Dp) and ev[f"auc_{m}"] > max(Ap))
        d, dd = E[f"D_{m}"].dropna(), E[f"DiD_{m}"].dropna()
        f_D = float((d <= ev[f"D_{m}"]).mean())
        f_did = float((dd <= did0).mean()) if len(dd) and np.isfinite(did0) else np.nan
        f_s = float(((E[f"D_{m}"] <= SENAL[m][0]) & (E[f"auc_{m}"] >= SENAL[m][1])).mean())
        frac_esp[m] = f_did
        out["placebo_espacial"][m] = dict(n=int(len(d)), D_p05_p50_p95=[r3(d.quantile(q)) for q in (.05, .5, .95)],
                                          DiD_p05_p50_p95=[r3(dd.quantile(q)) for q in (.05, .5, .95)] if len(dd) else None,
                                          DiD_evento=r3(did0), frac_DiD_menor_igual=r3(f_did), frac_D_menor_igual=r3(f_D),
                                          frac_en_zona_senal=r3(f_s), placebo_temporal_D=[r3(v) for v in sorted(Dp)],
                                          placebo_temporal_auc=[r3(v) for v in sorted(Ap)], supera_temporal=supera_temporal[m])
        print(f"   {m}: {len(d)} corrimientos; D sin corregir p05 {d.quantile(.05):+.2f} p50 {d.median():+.2f} p95 {d.quantile(.95):+.2f}; "
              f"fraccion en zona de senal sin ser pluma {f_s:.3f}; fraccion con D <= evento {f_D:.3f}")
        if len(dd):
            print(f"      corregido por el sesgo del lugar (DiD): p05 {dd.quantile(.05):+.2f} p50 {dd.median():+.2f} p95 {dd.quantile(.95):+.2f}; "
                  f"evento DiD {did0:+.3f}; fraccion de corrimientos con DiD <= evento: {f_did:.3f}")
        print(f"      placebo temporal en la huella real (dias despejados): D {np.round(sorted(Dp), 2).tolist()} AUC {np.round(sorted(Ap), 2).tolist()}; "
              f"el evento queda fuera de ese rango hacia el lado de ceniza: {supera_temporal[m]}")

    # ---------- 5. control positivo ----------
    print("\n== 5. Control positivo: capa sintetica (beta 0,7) en los pixeles lejanos de los cuadros que deciden ==")
    dias_cp = dias_cl
    cp = []
    for tn in INY_T:
        for e in INY_E:
            f = dict(tnube=tn, e11=e)
            for d in dias_cp + [DIA]:
                t = Q.tabla_dia(P, HUd, d, iny=(e, tn, INY_BETA), solo_lejos=True, todas=HU)
                t = t[t.elegible]
                ori = (PL[d] if d != DIA else T)
                ori = ori[ori.lejos & ori.elegible & ori.hora.isin(horas_dec)]
                r = Q.resumen(t, ("d11", "dbtd", "beta"))
                f[f"{d}_enfria"] = r3(np.median(t.bt11.values - ori.bt11.values))
                f[f"{d}_dbtd"] = r3(np.median(t.btd.values - ori.btd.values))
                f[f"{d}_D_d11"], f[f"{d}_auc_d11"] = r3(r["D_d11"]), r3(r["auc_d11"])
                f[f"{d}_D_dbtd"], f[f"{d}_auc_dbtd"] = r3(r["D_dbtd"]), r3(r["auc_dbtd"])
                f[f"{d}_zona_d11"] = zona("d11", r["D_d11"], r["auc_d11"])
                f[f"{d}_zona_dbtd"] = zona("dbtd", r["D_dbtd"], r["auc_dbtd"])
                f[f"{d}_n_beta"], f[f"{d}_D_beta"] = r["n_beta"], r3(r["D_beta"])
            f["enfria_mediana"] = r3(np.median([f[f"{d}_enfria"] for d in dias_cp])) if dias_cp else None
            f["detecta_d11"] = int(sum(f[f"{d}_zona_d11"] == "senal" for d in dias_cp))
            f["detecta_dbtd"] = int(sum(f[f"{d}_zona_dbtd"] == "senal" for d in dias_cp))
            f["dias"] = len(dias_cp)
            cp.append(f)
            print(f"T nube {tn:.0f} K, e11 {e:<5}: enfriamiento mediano {f['enfria_mediana']} K; detecta por dBT11 en {f['detecta_d11']} de "
                  f"{len(dias_cp)} dias placebo, por dBTD en {f['detecta_dbtd']}; sobre el 14-11: enfria {f[f'{DIA}_enfria']} K, "
                  f"D_d11 {f[f'{DIA}_D_d11']} AUC {f[f'{DIA}_auc_d11']} zona {f[f'{DIA}_zona_d11']}; D_dbtd {f[f'{DIA}_D_dbtd']} "
                  f"AUC {f[f'{DIA}_auc_dbtd']} zona {f[f'{DIA}_zona_dbtd']}; beta n {f[f'{DIA}_n_beta']} D {f[f'{DIA}_D_beta']}")
    CP = pd.DataFrame(cp)
    CP.to_csv(os.path.join(RES, "control_positivo.csv"), index=False)
    ob = CP[CP.enfria_mediana <= INY_OBLIGATORIA_K]
    cp_ok = bool(len(ob) and len(dias_cp) and (ob.detecta_d11 == ob.dias).all() and (ob[f"{DIA}_zona_d11"] == "senal").all())
    oblig = ob[["tnube", "e11", "enfria_mediana", "detecta_d11", "detecta_dbtd", "dias", f"{DIA}_zona_d11", f"{DIA}_zona_dbtd"]].to_dict("records")
    minimo = {}
    for m in ("d11", "dbtd"):
        ok = CP[(CP[f"detecta_{m}"] == CP.dias) & (CP[f"{DIA}_zona_{m}"] == "senal")]
        minimo[m] = {float(tn): ok[ok.tnube == tn].sort_values("e11")[["e11", "enfria_mediana", f"{DIA}_dbtd"]].head(1).to_dict("records")
                     for tn in INY_T}
    print("inyecciones obligatorias (enfriamiento mediano <= -2 K):", oblig)
    print("menor inyeccion detectada en todos los dias placebo despejados y en el dia de la prueba:", minimo)
    print("CONTROL POSITIVO:", "pasa" if cp_ok else "NO pasa")
    out["control_positivo"] = dict(pasa=cp_ok, obligatorias=oblig, minimo_detectado=minimo, dias=dias_cp)

    # ---------- 6. veredicto ----------
    z = {m: zona(m, ev[f"D_{m}"], ev[f"auc_{m}"]) for m in SENAL}
    senal = [m for m in SENAL if z[m] == "senal" and supera_temporal[m]]
    confirmada = [m for m in senal if frac_esp.get(m, 1.0) <= ESPACIAL_MAX]
    if ev["n_d11"] < MIN_N:
        ver = "SIN DATO: menos de 20 pixeles lejanos con control despejado"
    elif confirmada:
        ver = "senal IR medible a mas de 30 km (CONFIRMADO) en: " + ", ".join(confirmada)
    elif senal:
        ver = "senal IR a mas de 30 km (SOSPECHA: no supera el placebo espacial) en: " + ", ".join(senal)
    elif all(v == "nula" for v in z.values()) and cp_ok:
        ver = "sin senal IR medible a mas de 30 km (dBT11 y dBTD en zona nula; control positivo aprobado)"
    elif all(v == "nula" for v in z.values()):
        ver = "no concluyente: zona nula, pero el control positivo no pasa (la prueba no tiene potencia demostrada)"
    else:
        ver = "no concluyente: " + ", ".join(f"{m} en zona {v}" for m, v in z.items()) + \
              "; supera el placebo temporal: " + ", ".join(f"{m} {supera_temporal[m]}" for m in SENAL) + \
              "; fraccion espacial DiD " + ", ".join(f"{m} {frac_esp.get(m, np.nan):.3f}" for m in SENAL)
    out["veredicto"] = ver
    out["decide"] = {k: (r3(v) if isinstance(v, float) else v) for k, v in ev.items()}
    out["zonas"] = z
    print("\nVEREDICTO:", ver)
    json.dump(out, open(os.path.join(RES, "veredicto.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False,
              default=lambda o: o.item() if hasattr(o, "item") else str(o))


if __name__ == "__main__":
    main()
