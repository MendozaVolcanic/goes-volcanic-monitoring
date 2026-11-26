r"""V206 (verificación de S28b): ¿el rótulo MIXTO de día de S28a depende de la semilla del remuestreo de días?

Usa las funciones de s28a_medir.py SIN modificar (por_dia no hace falta: los conteos por día se arman desde los cuadros
que el propio S28a escribió en D:\goes_notas\s28\s28a\cuadros_<sitio>_<año>.csv; razon y veredicto son las del script).
Sólo cambia el argumento `semilla` de razon(). Días: 2025 (62) y 2026 hasta el 24-11 (65). No corre ningún detector.

Uso: python -I -B v206_semilla.py [n_semillas]   (por defecto 200)
"""
import csv
import json
import os
import sys
from datetime import datetime

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
OV = os.path.abspath(os.path.join(AQUI, "..", "..", ".."))
sys.path.insert(0, os.path.join(OV, "s28a_vecinas", "scripts"))
import s28a_medir as V  # noqa: E402

SAL = r"D:\goes_notas\s28\s28b\v201"
PUB = json.load(open(os.path.join(OV, "s28a_vecinas", "resultados", "s28a_resultado.json"), encoding="utf-8"))


def conteos(sitio, año, rango):
    """(F, E) de la unión por día, con todos los días del año (también los que no tienen cuadros evaluados)."""
    t0, nd = (V.T0_25, V.NR) if año == "2025" else (V.T0_26, V.ND26)
    r = set(rango)
    c = np.zeros((nd, 2), float)
    with open(os.path.join(V.TRAB, f"cuadros_{sitio}_{año}.csv"), encoding="utf-8") as f:
        for x in csv.DictReader(f):
            d = (datetime.strptime(x["dia"], "%Y-%m-%d") - t0).days
            assert 0 <= d < nd, x["dia"]
            s = V.M.slot(x["hora"])
            if s in r and x["ev_u"] == "1":
                c[d, 1] += 1
                c[d, 0] += int(x["F_u"])
    return c


def main(nsem):
    assert V.N_BOOT == 2000 and V.SEMILLA == 0
    C = {(s, a, p): conteos(s, a, rg) for s in V.SITIOS for a in ("2025", "2026")
         for p, rg in (("noche", V.NOCHE), ("dia", V.DIA))}
    # 1) el arnés reproduce lo publicado con la semilla del criterio
    for per in ("noche", "dia"):
        vec = {s: V.razon(C[s, "2025", per], C[s, "2026", per]) for s in V.SITIOS}
        for s in V.SITIOS:
            pub = PUB["vecinas"][s]["principal"][per]["union"]
            igual = all(vec[s][k] == pub[k] for k in ("2025", "2026", "R", "IC95", "replicas_validas"))
            print(f"semilla 0, {s} {per}: {vec[s]['2025']} {vec[s]['2026']} R {vec[s]['R']} IC95 {vec[s]['IC95']}"
                  f" | publicado IC95 {pub['IC95']} | {'IGUAL' if igual else 'DISTINTO'}")
            assert igual, "el arnés no reproduce lo publicado"
        ver = V.veredicto(vec, PUB["chillan"][per]["todos"]["R"])
        print(f"semilla 0, veredicto {per}: {ver} | publicado: {PUB['veredicto'][per]}")
        assert ver == PUB["veredicto"][per]
    # 2) sólo cambia la semilla
    filas = []
    for k in range(nsem):
        fila = {"semilla": k}
        for per in ("noche", "dia"):
            vec = {s: V.razon(C[s, "2025", per], C[s, "2026", per], semilla=k) for s in V.SITIOS}
            fila[per] = V.veredicto(vec, PUB["chillan"][per]["todos"]["R"])
            for s in V.SITIOS:
                fila[f"{s}_{per}_lo"], fila[f"{s}_{per}_hi"] = vec[s]["IC95"]
        filas.append(fila)
    for per in ("noche", "dia"):
        cnt = {}
        for f in filas:
            cnt[f[per]] = cnt.get(f[per], 0) + 1
        print(f"{per}: veredictos con {nsem} semillas (0 a {nsem - 1}): {cnt}")
    lo = np.array([f["antuco_dia_lo"] for f in filas])
    print(f"Antuco día, límite inferior del IC95 de R: mín {lo.min():.5f}, p5 {np.percentile(lo, 5):.5f}, "
          f"mediana {np.median(lo):.5f}, p95 {np.percentile(lo, 95):.5f}, máx {lo.max():.5f}; "
          f"<= 1,0 en {int((lo <= 1.0).sum())} de {nsem} ({(lo <= 1.0).mean():.3f})")
    from scipy import stats
    k = int((lo <= 1.0).sum())
    ci = stats.binomtest(k, nsem).proportion_ci(0.95, "exact")
    print(f"intervalo binomial exacto 95 % de esa fracción: {ci.low:.3f} a {ci.high:.3f}")
    # 3) el límite inferior con muchas réplicas (el valor al que apunta el remuestreo): mismo esquema, vectorizado
    c25, c26 = C["antuco", "2025", "dia"], C["antuco", "2026", "dia"]
    rng = np.random.default_rng(12345)
    NB = 400000
    Rs = []
    for _ in range(40):
        a = c25[rng.integers(0, len(c25), (NB // 40, len(c25)))].sum(1)
        b = c26[rng.integers(0, len(c26), (NB // 40, len(c26)))].sum(1)
        ok = (a[:, 1] > 0) & (b[:, 1] > 0) & (a[:, 0] > 0)
        Rs.append((b[ok, 0] / b[ok, 1]) / (a[ok, 0] / a[ok, 1]))
    Rs = np.concatenate(Rs)
    lo_inf = float(np.percentile(Rs, 2.5))
    print(f"Antuco día con {len(Rs)} réplicas (generador aparte, semilla 12345): percentil 2,5 = {lo_inf:.5f}, "
          f"fracción de réplicas con R <= 1: {(Rs <= 1.0).mean():.5f} (el rótulo pide que sea < 0,025)")
    os.makedirs(SAL, exist_ok=True)
    with open(os.path.join(SAL, f"v206_semillas_{nsem}.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(filas[0]))
        w.writeheader()
        w.writerows(filas)
    print("escrito", os.path.join(SAL, f"v206_semillas_{nsem}.csv"))


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 200)
