"""H9, parte rayos (H9d): destellos GLM a <= 30 km (y <= 20 km) del crater real de Chillan en la ventana
[t - 30 min, t + 10 min] de cada cuadro VOLCAT. Criterio: docs/own_volcat/calor_rayos/criterio_H9_calor_rayos_2026-11-19.md.

Fuente: historia de docs/data/glm_latest.json de Lightning-v1 (fetch_glm_lightning_v1.py). No usa el campo `time`
de cada destello (desfase int16 sin escalar en Lightning-v1) ni sus conteos inner/outer (centro de "Nevados de
Chillan" en las coordenadas de Antuco): fecha cada destello con la interseccion de las ventanas
[scan - ventana, scan] de las versiones que lo listan y recalcula la distancia al crater real.
Salida: resultados/h9_rayos_resultado.txt, resultados/glm_destellos_chillan.csv
Uso: python analisis_rayos.py
"""
import os, json
from datetime import datetime, timedelta, timezone
from collections import defaultdict
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(os.path.dirname(HERE), "resultados"); os.makedirs(RES, exist_ok=True)
SCR = r"C:\Users\nmend\AppData\Local\Temp\claude\11c46882e3e16008\ea70ca80-5f81-4c66-8568-aa962b07902e\scratchpad"
GLM = os.path.join(SCR, "glm", "glm_versiones.jsonl")
B73 = r"C:\Users\nmend\AppData\Local\Temp\claude\f4710304fa6a9a5b\6cc950d4-5fd7-4e45-a0af-882008093b90\scratchpad\b73"
VLAT, VLON = -36.86, -71.38
RNG = np.random.default_rng(20261119)
NBOOT = 2000


def hav(la, lo):
    p1, p2 = np.radians(VLAT), np.radians(la)
    a = np.sin((p2 - p1) / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(np.radians(lo - VLON) / 2) ** 2
    return 2 * 6371.0 * np.arcsin(np.sqrt(a))


def ts(s):
    return datetime.fromisoformat(s).astimezone(timezone.utc).replace(tzinfo=None)


def cargar():
    vers = []
    for l in open(GLM, encoding="utf-8"):
        r = json.loads(l)
        if r.get("http") == 404 or not r.get("scan_utc"):
            continue
        vers.append(r)
    vers.sort(key=lambda r: r["scan_utc"])
    return vers


def main():
    vers = cargar()
    L = []
    p = lambda *a: L.append(" ".join(str(x) for x in a))
    ok = [v for v in vers if not v.get("error") and v.get("chillan") is not None]
    p("H9 rayos, salida cruda.", datetime.now().strftime("%Y-%m-%d %H:%M"))
    p("versiones de glm_latest.json bajadas", len(vers), "| sin error y con entrada de Chillan", len(ok))
    p("ventanas declaradas:", sorted({v.get("window") for v in vers}), "| fuentes:", sorted({str(v.get("source")) for v in vers}))
    p("centro usado por Lightning-v1 para 'Nevados de Chillan':", sorted({(v["chillan"]["lat"], v["chillan"]["lon"]) for v in ok}))
    # intervalos cubiertos
    iv = sorted((ts(v["scan_utc"]) - timedelta(minutes=v.get("window") or 15), ts(v["scan_utc"])) for v in ok)
    merged = []
    for a, b in iv:
        if merged and a <= merged[-1][1] + timedelta(minutes=2):
            merged[-1][1] = max(merged[-1][1], b)
        else:
            merged.append([a, b])
    huecos = [(merged[i][1], merged[i + 1][0]) for i in range(len(merged) - 1)]
    tot = sum(((b - a) for a, b in huecos), timedelta())
    p(f"tramos continuos de cobertura {len(merged)}; huecos {len(huecos)}, suma {tot}; mayores:",
      [(f"{a:%m-%d %H:%M}", f"{b:%m-%d %H:%M}") for a, b in sorted(huecos, key=lambda x: x[0] - x[1])[:8]])

    def cubierto(a, b):
        for x, y in merged:
            if x <= a and b <= y:
                return True
        return False

    # destellos unicos con intervalo de hora
    fl = {}
    for v in ok:
        s = ts(v["scan_utc"]); w = timedelta(minutes=v.get("window") or 15)
        for f in v["chillan"].get("flash_positions") or []:
            key = (round(f["lat"], 5), round(f["lon"], 5), f.get("energy_j"), f.get("area_m2"))
            a, b = s - w, s
            if key in fl:
                fa, fb = fl[key]; fl[key] = (max(fa, a), min(fb, b))
            else:
                fl[key] = (a, b)
    rows = []
    for (la, lo, e, ar), (a, b) in fl.items():
        rows.append(dict(lat=la, lon=lo, energia_j=e, area_m2=ar, desde=a, hasta=b, d_km=float(hav(la, lo))))
    D = pd.DataFrame(rows)
    if len(D):
        D = D.sort_values("desde"); D.to_csv(os.path.join(RES, "glm_destellos_chillan.csv"), index=False, float_format="%.5g")
    p("destellos unicos listados por Lightning-v1 para la entrada de Chillan:", len(D))
    for lim in (100, 50, 30, 20):
        sub = D[D.d_km <= lim] if len(D) else D
        p(f"  a <= {lim} km del crater real: {len(sub)}" + (f" | dias: {sorted({str(x.date()) for x in sub.desde})}" if len(sub) else ""))
    p("  intervalo de hora de cada destello (mediana del ancho, min):",
      float(np.median([(b - a).total_seconds() / 60 for a, b in zip(D.desde, D.hasta)])) if len(D) else "sin destellos")

    # cuadros
    a = json.load(open(os.path.join(B73, "inv_local.json"))) + json.load(open(os.path.join(B73, "inv_new.json")))
    INV = {datetime.fromisoformat(r["t"]).replace(tzinfo=None, second=0): r for r in a}

    def limpio(dt):
        r = INV.get(dt)
        if r is None or not r["barra"] or r["manto"] or r["n50"] > 0:
            return False
        for m in range(-60, 61, 10):
            q = INV.get(dt + timedelta(minutes=m))
            if q is not None and (q["n50"] > 0 or q["manto"]):
                return False
        return True

    pos = [t for t, r in INV.items() if r["barra"] and r["anc"] and not r["manto"]]
    neg = [t for t in INV if limpio(t)]

    def rayo(t, lim):
        a_, b_ = t - timedelta(minutes=30), t + timedelta(minutes=10)
        if not len(D):
            return False
        s = D[(D.d_km <= lim) & (D.desde <= b_) & (D.hasta >= a_)]
        return len(s) > 0

    for lim in (30, 20):
        pc = [t for t in pos if cubierto(t - timedelta(minutes=30), t + timedelta(minutes=10))]
        nc = [t for t in neg if cubierto(t - timedelta(minutes=30), t + timedelta(minutes=10))]
        rp = {t: rayo(t, lim) for t in pc}; rn = {t: rayo(t, lim) for t in nc}
        tag = "DECIDE" if lim == 30 else "sensibilidad"
        p(f"\n=== H9d radio {lim} km ({tag}) ===")
        p(f"  positivos {len(pos)}, cubiertos {len(pc)} ({len(pc) / len(pos):.0%}); con rayo {sum(rp.values())}")
        p(f"  negativos limpios {len(neg)}, cubiertos {len(nc)}; con rayo {sum(rn.values())} ({sum(rn.values()) / max(len(nc), 1):.2%})")
        # pareo por minuto UTC +-10 dias
        nb = defaultdict(list)
        for t in nc:
            nb[t.strftime("%H:%M")].append(t)
        dif_dia = defaultdict(list)
        for t in pc:
            cs = [u for u in nb[t.strftime("%H:%M")] if u.date() != t.date() and abs((u - t).days) <= 10]
            if cs:
                dif_dia[t.date()].append((float(rp[t]), float(np.mean([rn[u] for u in cs]))))
        allp = [x for v in dif_dia.values() for x in v]
        if allp:
            tp = np.mean([x[0] for x in allp]); tc = np.mean([x[1] for x in allp])
            keys = list(dif_dia); bo = []
            for _ in range(NBOOT):
                smp = [x for i in RNG.integers(0, len(keys), len(keys)) for x in dif_dia[keys[i]]]
                bo.append(np.mean([x[0] - x[1] for x in smp]))
            lo, hi = np.percentile(bo, [2.5, 97.5])
            p(f"  pareados: {len(allp)} positivos en {len(keys)} dias; tasa positivos {tp:.3f}, controles {tc:.3f}; diferencia IC95 [{lo:.3f}; {hi:.3f}]")
        else:
            tp = tc = 0; lo = 0
        frac = sum(rp.values()) / max(len(pc), 1)
        if len(pc) < 0.8 * len(pos):
            v = "no concluyente (cobertura < 80 %)"
        elif frac < 0.05:
            v = "se falsa (< 5 % de los positivos cubiertos con rayo)"
        elif frac >= 0.30 and tp >= 3 * tc and lo > 0:
            v = "apoya"
        else:
            v = "no concluyente"
        p(f"  VEREDICTO H9d ({lim} km): {v}")
    txt = "\n".join(L)
    open(os.path.join(RES, "h9_rayos_resultado.txt"), "w", encoding="utf-8").write(txt)
    print(txt)


if __name__ == "__main__":
    main()
