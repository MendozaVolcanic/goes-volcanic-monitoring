r"""Validación fuera de muestra del indicador nocturno de VRP a 3,9 µm (criterio_2026-11-22.md §2 a §4).

Lee  D:\goes_cache\vrp_nocturno\l1b\*.npz (vn_bajar.py), D:\goes_cache\vrp_nocturno\mirova\*.json (salida publicada de
     VRP Chile) y, si existe, D:\goes_cache\vrp_nocturno\fdcf.csv (vn_fdcf.py).
Escribe resultados/cuadros.csv, resultados/noches.csv, resultados/vn_resultado.txt y D:\...\cuadros.pkl.
Uso: python -I vn_medir.py
"""
import os
import sys
import glob
import json
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vn_comun as K  # noqa: E402
from vn_bajar import SITIOS  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
RES = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "resultados")
MIR = os.path.join(K.OUT, "mirova")
MIR_NOMBRE = {"Nevados de Chillan": "NevadosDeChillan", "Lascar": "Lascar", "Lastarria": "Lastarria",
              "Isluga": "Isluga", "Tupungatito": "Tupungatito", "Planchon-Peteroa": "PlanchonPeteroa",
              "Copahue": "Copahue", "Llaima": "Llaima", "Villarrica": "Villarrica",
              "Puyehue-Cordon Caulle": "PuyehueCordonCaulle", "Chaiten": "Chaiten"}
U = 10.0                      # MW, decide
U5 = 5.0                      # MW, informativo
INICIO = datetime(2026, 9, 1).date()
H17_0, H17_1 = datetime(2026, 10, 20).date(), datetime(2026, 11, 19).date()


def noche(t):
    """Clave de la noche: 18:00 UTC de D-1 a 12:00 UTC de D -> D (criterio §2.1)."""
    return (t + timedelta(hours=6)).date()


def wilson(k, n, z=1.96):
    if n == 0:
        return (np.nan, np.nan)
    p = k / n
    d = 1 + z ** 2 / n
    c = (p + z ** 2 / (2 * n)) / d
    h = z * np.sqrt(p * (1 - p) / n + z ** 2 / (4 * n ** 2)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def fr(k, n):
    lo, hi = wilson(k, n)
    return f"{k}/{n} = {k / n:.1%} [IC95 {lo:.1%} a {hi:.1%}]" if n else f"{k}/0 (sin noches)"


def cuadros():
    S = [K.Sitio(n) for n in SITIOS]
    filas = []
    for f in sorted(glob.glob(os.path.join(K.L1B, "*.npz"))):
        c = os.path.basename(f)[:13]
        t = datetime.strptime(c, "%Y%m%d_%H%M")
        with np.load(f) as z:
            if "co7" not in z.files or "co14" not in z.files:
                continue
            co7, co14 = tuple(z["co7"]), tuple(z["co14"])
            for j, s in enumerate(S):
                if f"rad7_{j}" not in z.files or f"rad14_{j}" not in z.files:
                    continue
                vrp, b14, ncal = K.calor(s, z[f"rad7_{j}"].astype("float64"), co7,
                                         z[f"rad14_{j}"].astype("float64"), co14)
                filas.append(dict(cuadro=c, t=t, sitio=s.nombre, vrp=vrp, bt14z=b14, ncal=ncal,
                                  sza=K.sza(t, s.v.lat, s.v.lon)))
    df = pd.DataFrame(filas)
    df["noche"] = df.t.map(noche)
    return df


def visibilidad(df):
    """Criterio §2.2: referencia = p90 de bt14z nocturna de las noches D-7..D-1 (>= 10 cuadros); visible si
    bt14z >= ref - 4 K."""
    df = df.copy()
    df["ref"] = np.nan
    nn = df[(df.sza >= 90) & df.bt14z.notna()]
    for s, g in nn.groupby("sitio"):
        por_noche = {d: x.bt14z.values for d, x in g.groupby("noche")}
        for d in por_noche:
            prev = [por_noche[d - timedelta(days=i)] for i in range(1, 8) if d - timedelta(days=i) in por_noche]
            v = np.concatenate(prev) if prev else np.array([])
            if len(v) >= 10:
                df.loc[(df.sitio == s) & (df.noche == d), "ref"] = np.percentile(v, 90)
    df["nocturno"] = df.sza >= 90
    df["visible"] = df.nocturno & df.ref.notna() & df.vrp.notna() & (df.bt14z >= df.ref - 4.0)
    return df


def noches(df):
    g = df[df.nocturno].groupby(["sitio", "noche"])
    out = g.agg(n_noct=("cuadro", "size"), n_vis=("visible", "sum"),
                evaluable=("ref", lambda x: x.notna().any())).reset_index()
    v = df[df.visible].groupby(["sitio", "noche"])
    k10 = v.vrp.apply(lambda x: int((x >= U).sum())).rename("n10")
    k5 = v.vrp.apply(lambda x: int((x >= U5).sum())).rename("n5")
    vmax = v.vrp.max().rename("vrp_max")
    vmed = v.vrp.median().rename("vrp_med")
    out = out.merge(pd.concat([k10, k5, vmax, vmed], axis=1).reset_index(), on=["sitio", "noche"], how="left")
    out[["n10", "n5"]] = out[["n10", "n5"]].fillna(0).astype(int)
    out["con_dato"] = out.n_vis >= 4
    out["enc"] = out.con_dato & (out.n10 >= 2) & (out.n10 >= 0.25 * out.n_vis)
    out["enc5"] = out.con_dato & (out.n5 >= 2) & (out.n5 >= 0.25 * out.n_vis)
    return out


def mirova():
    """Criterio §3: {sitio: {noche: clase, vrp_max}} y la lista de pasadas consolidadas nocturnas."""
    clase, pasadas = {}, []
    for s, fnom in MIR_NOMBRE.items():
        d = json.load(open(os.path.join(MIR, fnom + ".json"), encoding="utf-8"))
        cons, ocr = {}, {}
        for r in d["records"]:
            if r.get("dia"):
                continue
            t = datetime.strptime(r["datetime_utc"], "%Y-%m-%d %H:%M")
            v = r["VRP_MW"] or 0.0
            n = noche(t)
            tgt = cons if r.get("source") == "consolidado" else ocr
            tgt[n] = max(tgt.get(n, 0.0), v)
            if r.get("source") == "consolidado":
                pasadas.append(dict(sitio=s, t=t, sensor=r["sensor"], vrp_mirova=v))
        rut = set()
        for sensor, ts in d["pasadas_tabla"]["rutina"].items():
            for x in ts:
                t = datetime.strptime(x, "%Y-%m-%d %H:%M")
                if 0 <= t.hour < 10:
                    rut.add(noche(t))
        c = {}
        for n in set(cons) | set(ocr) | rut:
            mc, mo = cons.get(n, 0.0), ocr.get(n, 0.0)
            if mc >= 10:
                c[n] = ("P", mc, mc)
            elif mc >= 1 or mo >= 1:
                c[n] = ("debil", max(mc, mo), mc)
            elif n in rut:
                c[n] = ("Q", max(mc, mo), mc)
        clase[s] = c
    return clase, pd.DataFrame(pasadas)


def main():
    df = visibilidad(cuadros())
    df.to_pickle(os.path.join(K.OUT, "cuadros.pkl"))
    nt = noches(df)
    cl, pas = mirova()
    nt["mirova"] = [cl.get(s, {}).get(n, (None, np.nan, np.nan))[0] for s, n in zip(nt.sitio, nt.noche)]
    nt["mirova_max"] = [cl.get(s, {}).get(n, (None, np.nan, np.nan))[1] for s, n in zip(nt.sitio, nt.noche)]
    nt["fuera"] = (nt.noche >= INICIO) & ~(nt.sitio.isin(K.H17_SITIOS) & (nt.noche >= H17_0) & (nt.noche <= H17_1))
    df.drop(columns=["t"]).round(3).to_csv(os.path.join(RES, "cuadros.csv"), index=False)
    nt.round(3).to_csv(os.path.join(RES, "noches.csv"), index=False)

    L = []
    p = lambda *a: L.append(" ".join(str(x) for x in a))  # noqa: E731
    p("VRP nocturno 3,9 µm, validación fuera de muestra. Generado", datetime.now().strftime("%Y-%m-%d %H:%M"))
    p("cuadros leídos:", df.cuadro.nunique(), "| filas sitio-cuadro:", len(df), "| nocturnas:", int(df.nocturno.sum()),
      "| visibles:", int(df.visible.sum()))
    for s in SITIOS:
        x = nt[(nt.sitio == s) & nt.fuera]
        p(f"  {s:24s} noches fuera de muestra {len(x):3d}, evaluables {int(x.evaluable.sum()):3d}, "
          f"con dato {int(x.con_dato.sum()):3d}, encendidas {int(x.enc.sum()):3d}")

    ch = nt[(nt.sitio == "Nevados de Chillan") & nt.fuera].sort_values("noche")
    P = ch[ch.mirova == "P"]
    inicioP = min((n for n, (c, _, _) in cl["Nevados de Chillan"].items() if c == "P" and n >= INICIO), default=None)
    inicio5 = min((n for n, (_, _, vc) in cl["Nevados de Chillan"].items() if vc >= 5 and n >= INICIO), default=None)
    p("\nInicio informado (MIROVA consolidado nocturno): primera noche >= 10 MW", inicioP,
      "| primera noche >= 5 MW (consolidado)", inicio5)

    p("\n== V1, detección: Chillán, noches P con dato ==")
    Pd = P[P.con_dato]
    for _, r in P.iterrows():
        p(f"  {r.noche} MIROVA {r.mirova_max:.1f} MW | visibles {r.n_vis}/{r.n_noct} | >=10 MW {r.n10} | "
          f"VRP máx {r.vrp_max if pd.notna(r.vrp_max) else float('nan'):.1f} | {'ENCENDIDA' if r.enc else ('sin dato' if not r.con_dato else 'apagada')}")
    v1_ok = len(Pd) >= 5 and Pd.enc.mean() >= 0.70
    p("V1:", fr(int(Pd.enc.sum()), len(Pd)), "->", "no evaluable" if len(Pd) < 5 else ("CUMPLE" if v1_ok else "NO CUMPLE"))

    p("\n== V2, falsa alarma: 7 controles nuevos, noches con dato ==")
    C = nt[nt.sitio.isin(K.CONTROLES) & nt.fuera & nt.con_dato]
    for s in K.CONTROLES:
        x = C[C.sitio == s]
        p(f"  {s:20s} {fr(int(x.enc.sum()), len(x))} | corte 5 MW {int(x.enc5.sum())}")
    peor = C.groupby("sitio").enc.sum().max() if len(C) else 0
    v2_ok = len(C) > 0 and C.enc.mean() <= 0.02 and peor <= 2
    p("V2:", fr(int(C.enc.sum()), len(C)), f"| peor control {peor} noches ->", "CUMPLE" if v2_ok else "NO CUMPLE")
    for _, r in C[C.enc].iterrows():
        p(f"   encendida: {r.sitio} {r.noche} visibles {r.n_vis} >=10 MW {r.n10} VRP máx {r.vrp_max:.1f}")

    p("\n== V3, Chillán antes del encendido (01-09 a la noche previa al inicio, MIROVA < 1 MW) ==")
    pre = ch[(ch.noche < inicio5) & ch.con_dato & ~(ch.mirova.isin(["P", "debil"]))] if inicio5 else ch.iloc[0:0]
    v3_ok = len(pre) > 0 and pre.enc.mean() <= 0.05
    p("V3:", fr(int(pre.enc.sum()), len(pre)), "->", "CUMPLE" if v3_ok else "NO CUMPLE")
    for _, r in pre[pre.enc].iterrows():
        p(f"   encendida: {r.noche} visibles {r.n_vis} >=10 MW {r.n10} VRP máx {r.vrp_max:.1f}")

    p("\n== V4, retardo ==")
    desde = ch[ch.con_dato & (ch.noche >= INICIO)]
    prim = desde[desde.enc].noche.min() if desde.enc.any() else None
    if prim is None or inicioP is None:
        v4_ok = False
        p("V4: sin primera noche encendida o sin inicio informado -> NO CUMPLE")
    else:
        ret = int(((desde.noche > inicioP) & (desde.noche <= prim)).sum()) if prim > inicioP else 0
        v4_ok = prim >= inicio5 and ret <= 3
        p(f"V4: primera encendida {prim}, primera P MIROVA {inicioP}, primera >= 5 MW {inicio5}, retardo {ret} noches "
          f"con dato después de la primera P ->", "CUMPLE" if v4_ok else "NO CUMPLE")

    ver = "VALIDA" if (v1_ok and v2_ok and v3_ok and v4_ok) else "NO VALIDA"
    p("\nVEREDICTO FASE A:", ver, f"(V1 {v1_ok}, V2 {v2_ok}, V3 {v3_ok}, V4 {v4_ok})")

    p("\n== Informativo (no decide) ==")
    p("Chillán fuera de muestra, por clase MIROVA (encendidas / con dato):")
    for c in ("P", "debil", "Q", None):
        x = ch[ch.con_dato & ((ch.mirova == c) if c else ch.mirova.isna())]
        p(f"  {c or 'sin verdad'}: {fr(int(x.enc.sum()), len(x))} | corte 5 MW {int(x.enc5.sum())}")
    p("Chillán, serie por noche (fuera de muestra): noche, MIROVA, visibles, >=10 MW, VRP máx, estado")
    for _, r in ch.iterrows():
        est = "ENC" if r.enc else ("--" if not r.con_dato else "off")
        p(f"  {r.noche} {str(r.mirova or ''):5s} {r.mirova_max if pd.notna(r.mirova_max) else 0:5.1f} | "
          f"{r.n_vis:2d}/{r.n_noct:2d} | {r.n10:2d} | {r.vrp_max if pd.notna(r.vrp_max) else float('nan'):6.1f} | {est}")
    p("Chillán dentro de muestra (20-10 a 19-11, serie B):")
    ins = nt[(nt.sitio == "Nevados de Chillan") & ~nt.fuera & (nt.noche >= INICIO) & nt.con_dato]
    p("  ", fr(int(ins.enc.sum()), len(ins)))
    p("Controles de H17 fuera de su periodo:")
    for s in ("Antuco", "Nevado de Longavi"):
        x = nt[(nt.sitio == s) & nt.fuera & nt.con_dato]
        p(f"  {s}: {fr(int(x.enc.sum()), len(x))}")
    p("Controles nuevos con corte 5 MW:", fr(int(C.enc5.sum()), len(C)))
    p("Activos débiles (límite de detección), encendidas / con dato por clase MIROVA:")
    for s in K.ACTIVOS:
        x = nt[(nt.sitio == s) & nt.fuera & nt.con_dato]
        partes = []
        for c in ("P", "debil", "Q", None):
            y = x[(x.mirova == c) if c else x.mirova.isna()]
            partes.append(f"{c or 'sin'} {int(y.enc.sum())}/{len(y)}")
        mx = x.mirova_max.max()
        p(f"  {s:22s} total {int(x.enc.sum())}/{len(x)} | " + " | ".join(partes) +
          f" | MIROVA máx en esas noches {mx if pd.notna(mx) else 0:.1f} MW | VRP ABI p90 de cuadros visibles "
          f"{df[(df.sitio == s) & df.visible].vrp.quantile(.9):.1f}")
    x = nt[(nt.sitio == "Sangay (Ecuador)") & nt.fuera & nt.con_dato]
    p("Sangay:", fr(int(x.enc.sum()), len(x)), "| corte 5 MW", int(x.enc5.sum()),
      "| VRP mediana de cuadros visibles", round(float(df[(df.sitio == 'Sangay (Ecuador)') & df.visible].vrp.median()), 1))

    p("\nCuadro contra pasada (Chillán, pasadas consolidadas nocturnas fuera de muestra, cuadro ABI a <= 15 min):")
    ca = df[df.sitio == "Nevados de Chillan"].set_index("t").sort_index()
    pr = []
    for _, r in pas[(pas.sitio == "Nevados de Chillan")].iterrows():
        n = noche(r.t)
        if n < INICIO or (H17_0 <= n <= H17_1):
            continue
        if not (0 <= r.t.hour < 10):
            continue
        i = ca.index.get_indexer([r.t], method="nearest")[0]
        if i < 0 or abs((ca.index[i] - r.t).total_seconds()) > 900:
            continue
        q = ca.iloc[i]
        pr.append(dict(t=r.t, sensor=r.sensor, mirova=r.vrp_mirova, abi=q.vrp, visible=bool(q.visible)))
    pr = pd.DataFrame(pr)
    if len(pr):
        for _, r in pr.iterrows():
            p(f"  {r.t:%Y-%m-%d %H:%M} {r.sensor:9s} MIROVA {r.mirova:6.2f} | ABI {r.abi:6.2f} | visible {r.visible}")
        v = pr[pr.visible]
        if len(v) >= 3:
            from scipy.stats import spearmanr
            rho = spearmanr(v.mirova, v.abi)
            fuertes = v[v.mirova >= 5]
            p(f"  visibles: {len(v)}, Spearman {rho.correlation:.2f} (p {rho.pvalue:.3f}); con MIROVA >= 5 MW: "
              f"{len(fuertes)}, mediana ABI/MIROVA {np.median(fuertes.abi / fuertes.mirova) if len(fuertes) else float('nan'):.2f}")
        pr.round(3).to_csv(os.path.join(RES, "cuadro_contra_pasada.csv"), index=False)

    fd = os.path.join(K.OUT, "fdcf.csv")
    if os.path.exists(fd):
        f = pd.read_csv(fd, parse_dates=["t"])
        f["noche"] = f.t.map(noche)
        vis = df[(df.sitio == "Nevados de Chillan") & df.visible][["t"]]
        f = f.merge(vis, on="t")
        fn = f.groupby("noche").agg(fdcf=("n_fuego", lambda x: int((x > 0).sum())), n=("t", "size")).reset_index()
        x = ch[ch.mirova.isin(["P", "debil"]) & ch.con_dato].merge(fn, on="noche", how="left")
        p("\nFDCF en los mismos cuadros visibles de Chillán, noches P y débiles con dato (fuera de muestra):")
        for _, r in x.iterrows():
            p(f"  {r.noche} {r.mirova:5s} {r.mirova_max:5.1f} MW | indicador {'ENC' if r.enc else 'off'} | "
              f"FDCF cuadros con fuego {r.fdcf if pd.notna(r.fdcf) else 'sin FDCF'} de {r.n if pd.notna(r.n) else 0}")
        p("  noches con FDCF >= 1 cuadro:", int((x.fdcf.fillna(0) > 0).sum()), "de", len(x),
          "| noches encendidas (indicador):", int(x.enc.sum()), "de", len(x))
    open(os.path.join(RES, "vn_resultado.txt"), "w", encoding="utf-8").write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
