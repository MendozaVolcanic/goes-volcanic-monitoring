r"""Revision H17 (S19e, criterio ../criterio_2026-11-23.md §3.1 y §4): ¿la linea base temporal de H17 cayo en nube?

Reutiliza sin cambios las funciones de h17_pluma.py (cargar_ir, base, objetos, huellas, boot_dias, VARIANTES) y
rehace la etapa 2 con cuatro bases: "orig" (la de H17, linea base roja: tiene que reproducir sus numeros),
"desp" (solo cuadros de la base en escena despejada segun ACMF; decide), "nub" (solo nublados; control
positivo, solo cuadros de evento) y "azar" (subconjunto al azar del mismo tamano que "desp"; nulo medido).
Escribe (repo) ../resultados/rev_h17_resultado.txt y rev_h17_por_cuadro.csv (sin posiciones de huella).
Uso, desde scripts\: python -I rev_h17.py
"""
import glob
import os
import sys
from datetime import datetime

import numpy as np
import pandas as pd
from scipy import ndimage

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
sys.path.insert(1, os.path.join(os.path.dirname(os.path.dirname(AQUI)), "h17_regla_propia", "scripts"))
import rev_comun as R  # noqa: E402
import h17_comun as K  # noqa: E402
import h17_pluma as P17  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
RES = os.path.join(os.path.dirname(AQUI), "resultados")
SEMILLA = 20261123
MIN_BASE = 5


def bases(sel, b11, btd, sub):
    """(B11, Bd) con la regla de h17_pluma.base, pero sobre el subconjunto sub de los indices de la base."""
    s = sel[sub]
    if len(s) < MIN_BASE:
        return None, None
    with np.errstate(all="ignore"):
        B11 = np.nanpercentile(b11[s], 75, axis=0)
        desp = b11[s] >= B11 - 2.0
        Bd = np.nanmedian(np.where(desp, btd[s], np.nan), axis=0)
    return B11, Bd


def evaluar(i, b11, btd, B11, Bd, g24, hu, rng, pix, c, var):
    d11, dd = b11[i] - B11, btd[i] - Bd
    u11, ud, _ = P17.VARIANTES["decide"]
    cand = (d11 <= u11) & (dd <= ud)
    ok = [o for o in P17.objetos(cand) if o["anclado"] and 1 <= o["n"] <= 70]
    out = {f"det_{var}": bool(g24 and ok)}
    if hu is not None:
        lejos = ndimage.distance_transform_edt(~hu) >= 4
        valid = lejos & np.isfinite(b11[i]) & np.isfinite(d11) & np.isfinite(dd)
        for y, x in zip(*np.nonzero(hu)):
            pool = np.nonzero(valid & (np.abs(b11[i] - b11[i][y, x]) <= 0.5))
            if len(pool[0]) == 0 or not np.isfinite(d11[y, x]) or not np.isfinite(dd[y, x]):
                continue
            k_ = rng.choice(len(pool[0]), min(5, len(pool[0])), replace=False)
            pix.append(dict(var=var, cuadro=c, rol="h", cand=bool(cand[y, x]), d11=float(d11[y, x]), dd=float(dd[y, x])))
            for j in k_:
                yy, xx = pool[0][j], pool[1][j]
                pix.append(dict(var=var, cuadro=c, rol="c", cand=bool(cand[yy, xx]), d11=float(d11[yy, xx]),
                                dd=float(dd[yy, xx])))
    return out


def veredicto_e2(e, col, rng):
    P, N = e[e.pos], e[e.neg]
    pod, far = P[col].mean(), N[col].mean()
    lo, hi = P17.boot_dias(e.assign(**{col: e[col].astype(float)}), col, rng)
    if pod >= 0.5 and far <= 0.05 and lo > 0:
        v = "cumple"
    elif lo > 0:
        v = "separa pero no sirve"
    else:
        v = "no separa del fondo"
    return pod, far, lo, hi, len(P), len(N), v


def main():
    rng_az = np.random.default_rng(SEMILLA)
    idx = K.indice()
    cal = pd.read_pickle(os.path.join(K.H17, "calor.pkl"))
    ch = cal[cal.sitio == "chillan"].set_index("dt").sort_index()
    t10 = ch.index[ch.T10.fillna(False).astype(bool)]
    cs, T, b11, btd = P17.cargar_ir(idx)
    print("cuadros C14+C15", len(cs), flush=True)
    h9 = pd.read_csv(P17.FRAMES_H9, parse_dates=["dt"]).set_index("dt")
    evs = {datetime.strptime(os.path.basename(f).split("_s")[1][:12], "%Y%m%d%H%M")
           for f in glob.glob(os.path.join(K.EVDIR, "*.nc"))}
    HU = P17.huellas()
    est = [R.estado(c) for c in cs]
    hay = np.array([x[0] for x in est])
    fbajo = np.array([x[1] for x in est])
    esc = np.array([x[2] for x in est])
    fcum = np.array([x[3] for x in est])
    print("con ACMF", int(hay.sum()), "escena despejada", int(esc.sum()), flush=True)

    # Pregunta 2 del instrumento: el terreno bajo tiene que estar >= 3 K mas tibio en escenas despejadas (por hora UTC)
    bt_bajo = np.array([np.nanmedian(b11[i][R.BAJO]) for i in range(len(cs))])
    horas = np.array([t.hour for t in T])
    dif_h = []
    for h in range(24):
        a, b = bt_bajo[(horas == h) & esc], bt_bajo[(horas == h) & hay & ~esc]
        if len(a) >= 5 and len(b) >= 5:
            dif_h.append(float(np.nanmedian(a) - np.nanmedian(b)))
    q2 = float(np.median(dif_h)) if dif_h else np.nan

    filas, pix = [], []
    rngs = {v: np.random.default_rng(20261121) for v in ("orig", "desp", "nub", "azar")}
    for i, c in enumerate(cs):
        t = T[i]
        clase = h9.clase.get(t, "fuera")
        es_ev = t in evs
        sel, B11o, Bdo = P17.base(i, T, b11, btd)
        g24 = bool(((t10 >= t - P17.timedelta(hours=24)) & (t10 <= t)).any())
        sza = float(ch.sza.get(t, np.nan))
        fila = dict(cuadro=c, fecha=t.date(), clase=clase, evento=es_ev, pos=es_ev or clase == "P",
                    neg=(clase == "N") and not es_ev, sza=sza, n_base=len(sel), acm_t=bool(hay[i]),
                    fbajo_t=fbajo[i], escena_t=bool(esc[i]), fcumbre_t=fcum[i])
        if B11o is None:
            fila["con_orig"] = False
            filas.append(fila)
            continue
        sd = esc[sel]
        fila.update(con_orig=True, n_desp=int(sd.sum()), F17=float(1 - sd.mean()),
                    dias_desp=len({T[j].date() for j in sel[sd]}))
        hu = None
        if es_ev and c in HU:
            wy, wx = HU[c]
            hu = np.zeros(K.LAT.shape, bool)
            hu[wy, wx] = True
            fila["huella_acm_t"] = float((R.acm(c)[hu] <= 1).mean()) if hay[i] else np.nan
            ab = [R.acm(cs[j]) for j in sel if hay[j]]
            fila["huella_acm_base"] = float(np.mean([(a[hu] <= 1).mean() for a in ab])) if ab else np.nan
        subs = {"orig": np.ones(len(sel), bool), "desp": sd, "nub": ~sd}
        az = np.zeros(len(sel), bool)
        if sd.sum() >= MIN_BASE:
            az[rng_az.choice(len(sel), int(sd.sum()), replace=False)] = True
        subs["azar"] = az
        for v, sub in subs.items():
            if v == "nub" and hu is None:
                continue
            B11, Bd = (B11o, Bdo) if v == "orig" else bases(sel, b11, btd, sub)
            fila[f"con_{v}"] = B11 is not None
            if B11 is None:
                continue
            fila.update(evaluar(i, b11, btd, B11, Bd, g24, hu, rngs[v], pix, c, v))
        filas.append(fila)
        if i % 200 == 0:
            print(i, "/", len(cs), flush=True)

    df = pd.DataFrame(filas)
    df["periodo"] = np.where(df.sza >= 90, "noche", np.where(df.sza < 80, "dia", "crepusculo"))
    df.to_csv(os.path.join(RES, "rev_h17_por_cuadro.csv"), index=False)
    px = pd.DataFrame(pix)
    px.to_pickle(os.path.join(R.SALIDA, "rev_h17_pixeles.pkl"))

    L = []
    p = lambda *a: L.append(" ".join(str(x) for x in a))  # noqa: E731
    p("Revision H17 (S19e), base temporal contra la mascara de nubes de NOAA. Generado",
      datetime.now().strftime("%Y-%m-%d %H:%M"))
    p("cuadros C14+C15", len(cs), "| con ACMF", int(hay.sum()), "| sin ACMF", int((~hay).sum()),
      "| escena despejada", int(esc.sum()), f"({esc.mean():.3f})")
    p(f"Q2 instrumento: BT11 mediana del terreno bajo, despejado menos no despejado, mediana por hora UTC "
      f"= {q2:+.2f} K en {len(dif_h)} horas (pide >= +3 K) -> {'PASA' if q2 >= 3 else 'FALLA'}")
    ev = df[df.evento & df.con_orig]
    b = df[df.con_orig]
    p(f"F17 (fraccion de la base en escena NO despejada): todos los cuadros con base n {len(b)}, mediana "
      f"{b.F17.median():.3f}, p90 {b.F17.quantile(0.9):.3f}; cuadros con F17 > 0,75: {(b.F17 > 0.75).mean():.3f}")
    p(f"   60 cuadros de evento con base: {len(ev)}; F17 mediana {ev.F17.median():.3f}, p90 {ev.F17.quantile(0.9):.3f}; "
      f"con F17 > 0,75: {int((ev.F17 > 0.75).sum())} de {len(ev)} -> base sospechosa de nube: "
      f"{(ev.F17 > 0.75).sum() > len(ev) / 2}")
    p(f"   eventos con base despejada (>= {MIN_BASE} cuadros): {int(ev.con_desp.fillna(False).sum())} de {len(ev)}; "
      f"dias distintos en la base despejada (mediana) {ev.dias_desp.median():.0f}")
    p(f"   huella en el cuadro t: fraccion ACM despejada media {ev.huella_acm_t.mean():.3f}; en los cuadros de la "
      f"base {ev.huella_acm_base.mean():.3f} | cumbre en t (eventos) {ev.fcumbre_t.mean():.3f} | escena t despejada "
      f"en eventos {ev.escena_t.mean():.3f}, en negativos {df[df.neg].escena_t.mean():.3f}")

    p("\n== Huella event_idx de los cuadros de evento, por base (pareo BT11 +-0,5 K, mismo cuadro) ==")
    med = {}
    for v in ("orig", "desp", "nub", "azar"):
        s = px[px["var"] == v] if len(px) else px
        if not len(s):
            p(v, "sin pixeles")
            continue
        H, C = s[s.rol == "h"], s[s.rol == "c"]
        med[v] = H.d11.median()
        p(f"{v:5s} cuadros {s.cuadro.nunique()} | huella n {len(H)}: candidatos {H.cand.mean():.3f}, mediana dBT11 "
          f"{H.d11.median():+.2f} K, dBTD {H.dd.median():+.2f} K | controles n {len(C)}: candidatos {C.cand.mean():.3f}, "
          f"dBT11 {C.d11.median():+.2f} K, dBTD {C.dd.median():+.2f} K")
    # control positivo y nulo, sobre los mismos cuadros
    if len(px):
        comunes = set(px[px["var"] == "desp"].cuadro) & set(px[px["var"] == "nub"].cuadro)
        H = px[(px.rol == "h") & px.cuadro.isin(comunes)]
        dn = H[H["var"] == "nub"].d11.median()
        dd_ = H[H["var"] == "desp"].d11.median()
        p(f"control positivo (cuadros con base nublada y despejada, n {len(comunes)}): mediana dBT11 huella "
          f"nublada {dn:+.2f} K, despejada {dd_:+.2f} K, diferencia {dn - dd_:+.2f} K (pide >= +1 K) -> "
          f"{'PASA' if dn - dd_ >= 1 else 'SIN PODER'}")
        if "azar" in med:
            p(f"nulo medido (azar, mismo tamano que desp): {med['azar']:+.2f} K contra H17 +1,28 K; |dif| "
              f"{abs(med['azar'] - 1.28):.2f} K (pide <= 0,3 K) -> {'PASA' if abs(med['azar'] - 1.28) <= 0.3 else 'FALLA'}")

    p("\n== Etapa 2, variante decide, por base ==")
    rng = np.random.default_rng(20261121)
    for v in ("orig", "desp", "azar"):
        col = f"det_{v}"
        e = df[df[f"con_{v}"].fillna(False).astype(bool) & (df.pos | df.neg)].copy()
        e[col] = e[col].fillna(False).astype(bool)
        if not len(e) or not e.pos.any() or not e.neg.any():
            p(v, "sin datos")
            continue
        pod, far, lo, hi, nP, nN, ver = veredicto_e2(e, col, rng)
        p(f"{v:5s} POD {pod:.3f} (n {nP})  FAR {far:.3f} (n {nN})  POD-FAR IC95 [{lo:.3f}; {hi:.3f}]  -> {ver}")
    open(os.path.join(RES, "rev_h17_resultado.txt"), "w", encoding="utf-8").write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
