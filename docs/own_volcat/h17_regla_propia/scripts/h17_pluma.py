r"""H17 etapa 2: con calor en el cráter (compuerta de 24 h de la etapa 1), objetos chicos anclados al cráter con
umbrales relajados sobre una línea base temporal del mismo píxel. Criterio:
docs/own_volcat/h17_regla_propia/criterio_H17_2026-11-21.md §4.

Entrada: D:\goes_cache\h17\calor.pkl (h17_calor.py), cachés L1b (h17_comun.indice), clases de cuadro de H9
(calor_rayos/resultados/frames_calor.csv), huella event_idx ubicada por la etapa 3 (D:, no va al repo).
Escribe (repo): resultados/pluma_por_cuadro.csv (sin posiciones de huella), resultados/h17_pluma_resultado.txt.
Uso: python -I h17_pluma.py
"""
import os
import sys
import glob
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
from scipy import ndimage

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import h17_comun as K  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
AQUI = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(os.path.dirname(AQUI), "resultados")
FRAMES_H9 = os.path.join(os.path.dirname(os.path.dirname(AQUI)), "calor_rayos", "resultados", "frames_calor.csv")
SEMILLA, NBOOT = 20261121, 2000
DIST = K.dist_cumbre("chillan")
Z = DIST <= 6.0
DOM = DIST <= 30.0
OCHO = np.ones((3, 3), int)
VARIANTES = {   # nombre: (umbral ΔBT11, umbral ΔBTD, compuerta)
    "decide": (-1.0, -0.5, "24h"),
    "sin_compuerta": (-1.0, -0.5, None),
    "estricta": (-2.0, -1.0, "24h"),
    "compuerta_scan": (-1.0, -0.5, "scan"),
}


def cargar_ir(idx):
    cs = sorted(c for c in idx if 14 in idx[c] and 15 in idx[c])
    T = [datetime.strptime(c, "%Y%m%d_%H%M") for c in cs]
    b11 = np.full((len(cs),) + K.LAT.shape, np.nan, "float32")
    btd = np.full_like(b11, np.nan)
    for i, c in enumerate(cs):
        r14, co14 = K.banda(idx, c, 14)
        r15, co15 = K.banda(idx, c, 15)
        b14 = K.bt(r14, co14)
        b11[i] = b14
        btd[i] = b14 - K.bt(r15, co15)
    return cs, np.array(T), b11, btd


def base(i, T, b11, btd):
    """Índices de la línea base de i (criterio §4.2) y (B11, Bd)."""
    t = T[i]
    dtod = np.abs(((np.array([x.hour * 60 + x.minute for x in T]) - (t.hour * 60 + t.minute)) + 720) % 1440 - 720)
    sel = np.nonzero((T >= t - timedelta(days=6)) & (T <= t - timedelta(hours=3)) & (dtod <= 90))[0]
    if len(sel) < 5:
        return sel, None, None
    with np.errstate(all="ignore"):
        B11 = np.nanpercentile(b11[sel], 75, axis=0)
        desp = b11[sel] >= B11 - 2.0
        Bd = np.nanmedian(np.where(desp, btd[sel], np.nan), axis=0)
    return sel, B11, Bd


def objetos(cand):
    lab, n = ndimage.label(cand & DOM, structure=OCHO)
    out = []
    for j in range(1, n + 1):
        m = lab == j
        out.append(dict(n=int(m.sum()), anclado=bool((m & Z).any()), mask=m))
    return out


def huellas():
    z = np.load(K.E3INV)
    h = {}
    for kk in z.files:
        c, v = kk.split("__")
        h.setdefault(c, {})[v] = z[kk]
    return {c: (d["wy"].astype(int), d["wx"].astype(int)) for c, d in h.items()}


def boot_dias(df, col, rng):
    dias = np.array(sorted(df.fecha.unique()))
    g = {d: x for d, x in df.groupby("fecha")}
    vals = []
    for _ in range(NBOOT):
        s = pd.concat([g[d] for d in rng.choice(dias, len(dias))])
        P, N = s[s.pos], s[s.neg]
        if len(P) and len(N):
            vals.append(P[col].mean() - N[col].mean())
    return np.percentile(vals, [2.5, 97.5]) if vals else (np.nan, np.nan)


def main():
    rng = np.random.default_rng(SEMILLA)
    idx = K.indice()
    cal = pd.read_pickle(os.path.join(K.H17, "calor.pkl"))
    ch = cal[cal.sitio == "chillan"].set_index("dt").sort_index()
    t10 = ch.index[ch.T10.fillna(False).astype(bool)]
    cs, T, b11, btd = cargar_ir(idx)
    h9 = pd.read_csv(FRAMES_H9, parse_dates=["dt"]).set_index("dt")
    evs = {datetime.strptime(os.path.basename(f).split("_s")[1][:12], "%Y%m%d%H%M")
           for f in glob.glob(os.path.join(K.EVDIR, "*.nc"))}
    HU = huellas()

    filas, pix = [], []
    for i, c in enumerate(cs):
        t = T[i]
        clase = h9.clase.get(t, "fuera")
        es_ev = t in evs
        pos = es_ev or clase == "P"
        neg = (clase == "N") and not es_ev
        sel, B11, Bd = base(i, T, b11, btd)
        g24 = bool(((t10 >= t - timedelta(hours=24)) & (t10 <= t)).any())
        gsc = bool(t in ch.index and bool(ch.loc[t, "T10"]))
        fila = dict(cuadro=c, dt=t, clase=clase, evento=es_ev, pos=pos, neg=neg, n_base=len(sel),
                    con_base=B11 is not None, g24=g24, gscan=gsc, sza=float(ch.sza.get(t, np.nan)),
                    vrp=float(ch.vrp.get(t, np.nan)))
        if B11 is None:
            filas.append(fila)
            continue
        d11, dd = b11[i] - B11, btd[i] - Bd
        for v, (u11, ud, comp) in VARIANTES.items():
            cand = (d11 <= u11) & (dd <= ud)
            ob = [o for o in objetos(cand) if o["anclado"]]
            ok = [o for o in ob if 1 <= o["n"] <= 70]
            gate = {"24h": g24, "scan": gsc, None: True}[comp]
            fila[f"det_{v}"] = bool(gate and ok)
            fila[f"obj_{v}"] = bool(ok)
            fila[f"npx_{v}"] = max([o["n"] for o in ok], default=0)
            fila[f"ngrande_{v}"] = sum(o["n"] > 70 for o in ob)
            if v == "decide" and es_ev and c in HU:
                wy, wx = HU[c]
                hu = np.zeros(K.LAT.shape, bool)
                hu[wy, wx] = True
                hd = ndimage.binary_dilation(hu, OCHO)
                toca = [o for o in ok if (o["mask"] & hd).any()]
                fila["obj_tocan_huella"] = len(toca)
                fila["n_obj_anclados"] = len(ok)
                fila["frac_huella_cand"] = float(cand[hu].mean())
                fila["n_huella"] = int(hu.sum())
                # controles pareados por BT11 (±0,5 K), mismo cuadro, a >= 4 px de la huella
                lejos = ndimage.distance_transform_edt(~hu) >= 4
                valid = lejos & np.isfinite(b11[i]) & np.isfinite(d11) & np.isfinite(dd)
                for y, x in zip(wy, wx):
                    pool = np.nonzero(valid & (np.abs(b11[i] - b11[i][y, x]) <= 0.5))
                    if len(pool[0]) == 0 or not np.isfinite(d11[y, x]) or not np.isfinite(dd[y, x]):
                        continue
                    k_ = rng.choice(len(pool[0]), min(5, len(pool[0])), replace=False)
                    pix.append(dict(cuadro=c, rol="h", cand=bool(cand[y, x]), d11=float(d11[y, x]),
                                    dd=float(dd[y, x])))
                    for j in k_:
                        yy, xx = pool[0][j], pool[1][j]
                        pix.append(dict(cuadro=c, rol="c", cand=bool(cand[yy, xx]), d11=float(d11[yy, xx]),
                                        dd=float(dd[yy, xx])))
        filas.append(fila)

    df = pd.DataFrame(filas)
    df["fecha"] = df.dt.dt.date
    df["periodo"] = np.where(df.sza >= 90, "noche", np.where(df.sza < 80, "dia", "crepusculo"))
    df.drop(columns=["dt"]).to_csv(os.path.join(RES, "pluma_por_cuadro.csv"), index=False)
    px = pd.DataFrame(pix)
    px.to_pickle(os.path.join(K.H17, "pluma_pixeles.pkl"))

    L = []
    p = lambda *a: L.append(" ".join(str(x) for x in a))  # noqa: E731
    p("H17 etapa 2, objeto chico anclado con compuerta de calor. Generado", datetime.now().strftime("%Y-%m-%d %H:%M"))
    p("cuadros con C14+C15:", len(df), "| con base:", int(df.con_base.sum()),
      "| positivos (P o evento):", int(df.pos.sum()), "con base", int((df.pos & df.con_base).sum()),
      "| negativos N:", int(df.neg.sum()), "con base", int((df.neg & df.con_base).sum()))
    p("eventos VOLCAT con base:", int((df.evento & df.con_base).sum()), "de", int(df.evento.sum()))
    e = df[df.con_base & (df.pos | df.neg)]
    p("compuerta 24 h encendida: positivos", f"{e[e.pos].g24.mean():.3f}", "negativos", f"{e[e.neg].g24.mean():.3f}",
      "| compuerta en el scan: positivos", f"{e[e.pos].gscan.mean():.3f}", "negativos", f"{e[e.neg].gscan.mean():.3f}")

    veredicto = None
    for v in VARIANTES:
        col = f"det_{v}"
        p(f"\n== Variante {v} {VARIANTES[v]} ==")
        for per in ("total", "dia", "crepusculo", "noche"):
            s = e if per == "total" else e[e.periodo == per]
            P, N = s[s.pos], s[s.neg]
            if not len(P) and not len(N):
                continue
            pod = P[col].mean() if len(P) else np.nan
            far = N[col].mean() if len(N) else np.nan
            lo, hi = boot_dias(s, col, rng) if len(P) and len(N) else (np.nan, np.nan)
            p(f"{per:11s} POD {pod:.3f} ({int(P[col].sum())}/{len(P)})  FAR {far:.3f} ({int(N[col].sum())}/{len(N)})"
              f"  POD-FAR IC95 [{lo:.3f}; {hi:.3f}]  objeto anclado sin compuerta: P {P[f'obj_{v}'].mean():.3f}"
              f" N {N[f'obj_{v}'].mean():.3f}")
            if v == "decide" and per == "total":
                if pod >= 0.5 and far <= 0.05 and lo > 0:
                    veredicto = "cumple"
                elif lo > 0:
                    veredicto = "separa pero no sirve"
                else:
                    veredicto = "no separa del fondo"
        dpos = e.groupby("fecha").apply(lambda g: (g.pos.any(), g[col].any(), g.neg.any(), g[g.neg][col].any()),
                                        include_groups=False)
        dv = [d for d, x in dpos.items() if x[0]]
        da = [d for d, x in dpos.items() if x[0] and x[1]]
        dfa = [d for d, x in dpos.items() if (not x[0]) and x[2] and x[3]]
        dn = [d for d, x in dpos.items() if (not x[0]) and x[2]]
        p(f"por día: días con positivo VOLCAT {len(dv)}, con detección nuestra {len(da)}; días sin positivo "
          f"VOLCAT y con negativos evaluados {len(dn)}, con detección nuestra (falsa alarma) {len(dfa)}")
    p("\nVEREDICTO ETAPA 2 (variante decide, total):", veredicto)

    p("\n== Eventos VOLCAT: solapamiento con la huella event_idx (variante decide) ==")
    ev = df[df.evento & df.con_base]
    if len(ev):
        p("cuadros de evento con base:", len(ev), "| con objeto anclado 1-70 px:", int(ev.obj_decide.sum()),
          "| con objeto que toca la huella dilatada 1 px:", int((ev.obj_tocan_huella > 0).sum()),
          "| fracción media de la huella que es candidata:", f"{ev.frac_huella_cand.mean():.3f}")
    if len(px):
        H, C = px[px.rol == "h"], px[px.rol == "c"]
        p(f"por píxel (pareo BT11 ±0,5 K): candidatos en huella {H.cand.mean():.3f} (n {len(H)}) contra controles "
          f"{C.cand.mean():.3f} (n {len(C)}); razón {H.cand.mean() / max(C.cand.mean(), 1e-9):.2f}")
        p(f"   mediana ΔBT11 huella {H.d11.median():.2f} K controles {C.d11.median():.2f} K | mediana ΔBTD huella "
          f"{H.dd.median():.2f} K controles {C.dd.median():.2f} K")
        for c_, g in px.groupby(px.cuadro.str[:8]):
            hh, cc = g[g.rol == "h"], g[g.rol == "c"]
            p(f"   {c_}: huella {hh.cand.mean():.3f} (n {len(hh)}) controles {cc.cand.mean():.3f} | ΔBTD med "
              f"{hh.dd.median():.2f} vs {cc.dd.median():.2f}")
    open(os.path.join(RES, "h17_pluma_resultado.txt"), "w", encoding="utf-8").write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
