"""H9, parte calor: anomalia BT7 - BT14 en el crater de Chillan contra anillo, H9a (momento), H9b (contexto),
H9c (arranque de tramos). Criterio: docs/own_volcat/calor_rayos/criterio_H9_calor_rayos_2026-11-19.md.

Entrada: cache de fetch_c07.py (radiancia C07 y C14 por ventana + Planck de cada NetCDF), inventario VOLCAT de b73,
lat/lon de la ventana del detector. Salida: resultados/frames_calor.csv y resultados/h9_calor_resultado.txt.
Uso: python analisis_calor.py
"""
import os, sys, json
from datetime import datetime, timedelta
from collections import defaultdict
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(os.path.dirname(HERE), "resultados"); os.makedirs(RES, exist_ok=True)
SCR = r"D:\goes_notas\scratch_rescate_2026-11-21\h9_calor_rayos_11c46882"
CACHE = os.path.join(SCR, "c07cache")
DET = r"D:\goes_notas\local_f3a7d295\cache_rescatada\reproducir_volcat"
B73 = r"D:\goes_cache\h13\shim\b73"

# Catalogo del proyecto (src/volcanos.py): lat, lon, altura de cumbre en m
SITIOS = {"chillan": (-36.86, -71.38, 3212), "antuco": (-37.41, -71.35, 2979), "longavi": (-36.19, -71.16, 3242)}
ZONA_KM, ANI0, ANI1 = 6.0, 8.0, 14.0
VIS_K = 4.0
RNG = np.random.default_rng(20261119)
NBOOT = 2000

ll = np.load(os.path.join(DET, "latlon.npz")); LAT, LON = ll["lat"], ll["lon"]


def hav(lat, lon, la0, lo0):
    p1, p2 = np.radians(la0), np.radians(lat)
    a = np.sin((p2 - p1) / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(np.radians(lon - lo0) / 2) ** 2
    return 2 * 6371.0 * np.arcsin(np.sqrt(a))


MASK = {}
for s, (la, lo, h) in SITIOS.items():
    la_c = la - 0.93 * h / 1000.0 / 111.2       # paralaje: la cumbre aparece 0,93 h km mas al sur
    d = hav(LAT, LON, la_c, lo)
    MASK[s] = (d <= ZONA_KM, (d >= ANI0) & (d <= ANI1))


def bt(rad, co):
    fk1, fk2, bc1, bc2 = co
    with np.errstate(invalid="ignore", divide="ignore"):
        return (fk2 / np.log(fk1 / rad + 1.0) - bc1) / bc2


def inventario():
    a = json.load(open(os.path.join(B73, "inv_local.json"))) + json.load(open(os.path.join(B73, "inv_new.json")))
    out = {}
    for r in a:
        out[datetime.fromisoformat(r["t"]).replace(tzinfo=None, second=0)] = r
    return out


INV = inventario()


def es_pos(r):
    return bool(r["barra"]) and bool(r["anc"]) and not r["manto"]


def limpio(dt):
    r = INV.get(dt)
    if r is None or not r["barra"] or r["manto"] or r["n50"] > 0:
        return False
    for m in range(-60, 61, 10):
        q = INV.get(dt + timedelta(minutes=m))
        if q is not None and (q["n50"] > 0 or q["manto"]):
            return False
    return True


def medir():
    filas = []; n_sin = 0; n_falla = 0
    for dt in sorted(INV):
        p = os.path.join(CACHE, f"{dt:%Y%m%d_%H%M}.npz")
        r = INV[dt]
        base = dict(dt=dt, sza=r["sza"], clase="P" if es_pos(r) else ("N" if limpio(dt) else "otro"),
                    n_anc=len(r["anc"]), leido=False)
        if not os.path.exists(p):
            if os.path.exists(p[:-4] + ".sin_key"):
                n_sin += 1
            else:
                n_falla += 1
            filas.append(base); continue
        z = np.load(p)
        t7 = bt(z["rad7"].astype("float64"), z["co7"]); t14 = bt(z["rad14"].astype("float64"), z["co14"])
        t7[z["dqf7"] > 1] = np.nan; t14[z["dqf14"] > 1] = np.nan
        d = t7 - t14
        base["leido"] = True
        base["sat7"] = int((z["dqf7"] == 1).sum())
        for s, (zm, rm) in MASK.items():
            dz, dr = d[zm], d[rm]
            ok = np.isfinite(dz).sum() >= 3 and np.isfinite(dr).sum() >= 10
            base[f"A_{s}"] = float(np.nanmax(dz) - np.nanmedian(dr)) if ok else np.nan
            base[f"A7_{s}"] = float(np.nanmax(t7[zm]) - np.nanmedian(t7[rm])) if ok else np.nan
            base[f"V_{s}"] = float(np.nanmedian(t14[zm])) if np.isfinite(t14[zm]).sum() >= 3 else np.nan
        filas.append(base)
    df = pd.DataFrame(filas).set_index("dt")
    return df, n_sin, n_falla


def visibilidad(df, s, thr):
    """Vref = mediana de los 3 V mas altos del mismo minuto UTC en +-7 dias; visible si V >= Vref - thr."""
    v = df[f"V_{s}"]
    hm = df.index.strftime("%H:%M")
    vis = pd.Series(False, index=df.index)
    for key, idx in df.groupby(hm).groups.items():
        sub = v.loc[idx].dropna()
        for t in idx:
            if not np.isfinite(v.loc[t]):
                continue
            w = sub[(sub.index >= t - timedelta(days=7)) & (sub.index <= t + timedelta(days=7))]
            ref = np.median(np.sort(w.values)[-3:])
            vis.loc[t] = v.loc[t] >= ref - thr
    return vis


def pares(df, visC):
    """Para cada positivo visible en Chillan: negativos limpios visibles en Chillan del mismo minuto UTC, +-10 dias."""
    neg = df.index[(df.clase == "N") & visC]
    neg_by = defaultdict(list)
    for t in neg:
        neg_by[t.strftime("%H:%M")].append(t)
    out = {}
    for t in df.index[(df.clase == "P") & visC]:
        c = [u for u in neg_by[t.strftime("%H:%M")] if u.date() != t.date() and abs((u - t).days) <= 10]
        if c:
            out[t] = c
    return out


def auc_de(df, pr, s, vis_s):
    """AUC promedio por positivo y por dia, usando solo pares visibles tambien en el sitio s."""
    por_pos = {}
    for t, cs in pr.items():
        if not vis_s.loc[t] or not np.isfinite(df.at[t, f"A_{s}"]):
            continue
        a = df.at[t, f"A_{s}"]
        cc = np.array([df.at[u, f"A_{s}"] for u in cs if vis_s.loc[u] and np.isfinite(df.at[u, f"A_{s}"])])
        if len(cc) == 0:
            continue
        por_pos[t] = ((cc < a).sum() + 0.5 * (cc == a).sum()) / len(cc)
    if not por_pos:
        return None
    dias = defaultdict(list)
    for t, v in por_pos.items():
        dias[t.date()].append(v)
    auc = float(np.mean(list(por_pos.values())))
    keys = list(dias)
    boots = []
    for _ in range(NBOOT):
        smp = [dias[keys[i]] for i in RNG.integers(0, len(keys), len(keys))]
        boots.append(np.mean([x for d in smp for x in d]))
    lo, hi = np.percentile(boots, [2.5, 97.5])
    return dict(auc=auc, lo=float(lo), hi=float(hi), n_pos=len(por_pos), n_dias=len(keys),
                por_dia={str(k): (round(float(np.mean(v)), 3), len(v)) for k, v in sorted(dias.items())})


def veredicto_a(rc, ra, rl):
    if rc is None or rc["n_pos"] < 8 or rc["n_dias"] < 3:
        return "no concluyente (menos de 8 positivos visibles o de 3 dias)"
    mc = max(r["auc"] if r else 0.5 for r in (ra, rl))
    if rc["auc"] <= 0.60:
        return "se falsa (AUC <= 0,60)"
    if mc >= rc["auc"] - 0.05:
        return "se falsa (el efecto aparece igual en un control)"
    dias_ok = sum(1 for v, _ in rc["por_dia"].values() if v > 0.5)
    if (rc["auc"] >= 0.70 and rc["lo"] >= 0.55 and dias_ok >= 2 / 3 * rc["n_dias"]
            and mc <= 0.60 and rc["auc"] - mc >= 0.15):
        return "apoya"
    return "no concluyente"


def main():
    df, n_sin, n_falla = medir()
    df.to_csv(os.path.join(RES, "frames_calor.csv"), float_format="%.3f")
    L = []
    p = lambda *a: L.append(" ".join(str(x) for x in a))
    leidos = df[df.leido]
    p("H9 calor, salida cruda.", datetime.now().strftime("%Y-%m-%d %H:%M"))
    p("cuadros del inventario", len(df), "| leidos C07+C14", len(leidos), "| sin scan en S3", n_sin, "| sin leer (falla o pendiente)", n_falla)
    p("positivos", int((df.clase == "P").sum()), "leidos", int((leidos.clase == "P").sum()),
      "| negativos limpios", int((df.clase == "N").sum()), "leidos", int((leidos.clase == "N").sum()))
    p("pixeles con DQF=1 en C07 (posible saturacion) en todo el set:", int(leidos.sat7.sum()))
    p("pixeles por zona/anillo:", {s: (int(m[0].sum()), int(m[1].sum())) for s, m in MASK.items()})
    N = df.sza >= 80
    for thr in (VIS_K, 2.0, 8.0):
        vis = {s: visibilidad(df, s, thr) & df.leido for s in SITIOS}
        tag = "DECIDE" if thr == VIS_K else "sensibilidad"
        p(f"\n=== visibilidad {thr:.0f} K ({tag}) ===")
        for est, m in (("N (noche y crepusculo, decide)", N), ("D (dia, extension)", ~N)):
            for c in ("P", "N"):
                sel = (df.clase == c) & m & df.leido
                p(f"  {est} clase {c}: leidos {int(sel.sum())}, crater visible {int((sel & vis['chillan']).sum())}")
        for est, m in (("N", N), ("D", ~N)):
            pr = pares(df, vis["chillan"] & m)
            r = {s: auc_de(df, pr, s, vis[s]) for s in SITIOS}
            p(f"  H9a estrato {est}: positivos con al menos un control {len(pr)}, controles por positivo (mediana) "
              f"{int(np.median([len(v) for v in pr.values()])) if pr else 0}")
            for s in SITIOS:
                rr = r[s]
                if rr is None:
                    p(f"    {s}: sin pares"); continue
                p(f"    {s}: AUC {rr['auc']:.3f} [{rr['lo']:.3f}; {rr['hi']:.3f}] positivos {rr['n_pos']} dias {rr['n_dias']}")
                if s == "chillan":
                    p(f"      por dia (AUC, n): {rr['por_dia']}")
            p(f"    VEREDICTO H9a estrato {est}: {veredicto_a(r['chillan'], r['antuco'], r['longavi'])}")
            # medianas descriptivas
            P_ = [t for t in pr]; C_ = sorted({u for v in pr.values() for u in v})
            p(f"    mediana A Chillan positivos {np.nanmedian(df.loc[P_, 'A_chillan']) if P_ else np.nan:.2f} K"
              f" | controles {np.nanmedian(df.loc[C_, 'A_chillan']) if C_ else np.nan:.2f} K"
              f" | A7 positivos {np.nanmedian(df.loc[P_, 'A7_chillan']) if P_ else np.nan:.2f} K"
              f" | controles {np.nanmedian(df.loc[C_, 'A7_chillan']) if C_ else np.nan:.2f} K")
        if thr != VIS_K:
            continue
        # H9b contexto
        nv = {s: N & vis[s] for s in SITIOS}
        ctrl = np.concatenate([df.loc[nv["antuco"], "A_antuco"].dropna().values, df.loc[nv["longavi"], "A_longavi"].dropna().values])
        T99 = float(np.percentile(ctrl, 99))
        p(f"\n=== H9b contexto: T99 de Antuco+Longavi (N visibles, {len(ctrl)} valores) = {T99:.2f} K ===")
        for s in SITIOS:
            v = df.loc[nv[s], f"A_{s}"].dropna()
            p(f"  {s}: cuadros N visibles {len(v)}, mediana A {v.median():.2f} K, p90 {v.quantile(.9):.2f}, fraccion > T99 {(v > T99).mean():.3f}")
        sub = df.loc[nv["chillan"], ["A_chillan", "clase"]].dropna(subset=["A_chillan"])
        noche = (sub.index - timedelta(hours=12)).date
        g = sub.groupby(noche)
        F = {k: ((gg.A_chillan > T99).mean(), len(gg)) for k, gg in g}
        F6 = {k: v for k, v in F.items() if v[1] >= 6}
        on = sum(1 for v in F6.values() if v[0] >= 0.5)
        p(f"  noches con >= 6 cuadros N visibles: {len(F6)}; con F >= 0,5: {on} ({on / max(len(F6), 1):.0%})")
        p("  CONTEXTO", "ENCENDIDO" if len(F6) and on >= 0.75 * len(F6) else "NO ENCENDIDO (segun la regla)")
        dpos = sorted({t.date() for t in df.index[df.clase == "P"]})
        prev = {d - timedelta(days=1) for d in dpos} | {(t - timedelta(hours=12)).date() for t in df.index[(df.clase == "P") & N]}
        fa = [v[0] for k, v in F6.items() if k in prev]; fb = [v[0] for k, v in F6.items() if k not in prev]
        p(f"  F mediana en noches que preceden o contienen positivos: {np.median(fa) if fa else np.nan:.2f} (n={len(fa)}); demas: {np.median(fb) if fb else np.nan:.2f} (n={len(fb)})")
        p("  F por noche (fecha de la tarde, F, n):", {str(k): (round(float(v[0]), 2), v[1]) for k, v in sorted(F.items())})
        # H9c arranques
        visC = vis["chillan"]
        A = df["A_chillan"].where(visC)
        hm = df.index.strftime("%H:%M")
        negv = df.index[(df.clase == "N") & visC]
        base = pd.Series(np.nan, index=df.index)
        negA = df.loc[negv, "A_chillan"]
        neg_by = defaultdict(list)
        for t in negv:
            neg_by[t.strftime("%H:%M")].append(t)
        for t in df.index[visC & df.A_chillan.notna()]:
            cs = [u for u in neg_by[t.strftime("%H:%M")] if u != t and abs((u - t).total_seconds()) <= 7 * 86400]
            if len(cs) >= 3:
                base.loc[t] = np.median(negA.loc[cs].values)
        Ap = A - base
        thr95 = float(np.nanpercentile(Ap.loc[negv].values, 95))
        def subida(t0):
            w = Ap[(Ap.index >= t0 - timedelta(minutes=60)) & (Ap.index <= t0)].dropna()
            return None if len(w) == 0 else bool(w.max() > thr95)
        pos = sorted(df.index[df.clase == "P"])
        tramos = []
        for t in pos:
            if tramos and (t - tramos[-1][-1]) <= timedelta(minutes=30):
                tramos[-1].append(t)
            else:
                tramos.append([t])
        res = [(tr[0], len(tr), subida(tr[0])) for tr in tramos]
        con = [r for r in res if r[2] is not None]
        fr = sum(r[2] for r in con) / max(len(con), 1)
        bs = [subida(t) for t in negv]; bs = [b for b in bs if b is not None]
        tb = sum(bs) / max(len(bs), 1)
        p(f"\n=== H9c arranques: umbral p95 de A' en negativos = {thr95:.2f} K ===")
        p(f"  tramos {len(tramos)}, con dato visible en la hora previa {len(con)}, con subida {sum(r[2] for r in con)} ({fr:.0%}); tasa base {tb:.0%} sobre {len(bs)} negativos")
        for t0, n, s in res:
            p(f"    {t0:%Y-%m-%d %H:%M} UTC, {n} cuadros, cenit {df.at[t0, 'sza']:.0f}, subida: {s}")
        if fr >= 0.5 and fr >= 2 * tb:
            p("  LECTURA H9c: los arranques coinciden con subida de calor")
        elif fr <= tb + 0.10:
            p("  LECTURA H9c: los arranques NO coinciden con subida de calor")
        else:
            p("  LECTURA H9c: intermedio, no concluyente")
    txt = "\n".join(L)
    open(os.path.join(RES, "h9_calor_resultado.txt"), "w", encoding="utf-8").write(txt)
    print(txt)


if __name__ == "__main__":
    main()
