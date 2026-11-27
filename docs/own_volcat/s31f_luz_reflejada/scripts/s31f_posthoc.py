r"""S31f, POST HOC (escrito después de ver la medida; no cambia ningún veredicto).

Dos preguntas que salieron al mirar la tabla por cuadro:
1. Cada banda por separado: en la huella, C02 se aparta "hacia la ceniza" (U_C02 > 0) y C05 al revés (U_C05 < 0) en
   casi todos los cuadros. ¿Eso es propio de los días de VOLCAT o lo hace el mismo lugar cualquier día despejado de 2026
   (nulo N) o de 2024 (nulo Y)? ¿Y más que la misma escena mirada en otro rumbo (nulo R)?
2. ¿Cuánto cambia toda la zona despejada de 0 a 15 km respecto de 2025 (ρ − B, no estandarizado), por año y banda? Eso
   separa el cambio de superficie o de instrumento (GOES-16 en 2024) de lo que pasa sólo en la huella.

Mismos cubos, misma base, mismas nubes y mismas huellas que s31f_medir.py (importado sin cambios). Nulos por día,
B = 99.999, semilla 2. Sólo cifras a resultados/s31f_posthoc.json.
Uso: python -I -B s31f_posthoc.py
"""
import json
import os
import sys
import time

import numpy as np

sys.stdout.reconfigure(encoding="utf-8")
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import s31f_medir as M  # noqa: E402

B_PH, SEM_PH = 99999, 2


def main():
    t0 = time.time()
    import csv
    from collections import defaultdict
    clase = defaultdict(dict)
    with open(M.TABLA, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            h, mi = map(int, r["hora"].split(":"))
            clase[r["dia"]][h * 6 + mi // 10] = r["clase"]
    sza_c = {}
    with open(M.CALOR, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            sza_c[r["dt"][:16]] = float(r["sza"])
    zh = np.load(M.HUELLAS)
    P = []
    for k in sorted(zh.files):
        dia, s = k.rsplit("_", 1)
        s = int(s)
        if sza_c.get(f"{dia} {s // 6:02d}:{s % 6 * 10:02d}", 999) < M.SZA_MAX:
            P.append((dia, s, zh[k]))
    slotsP = M.BJ.SLOTS_P
    diasP = sorted({p[0] for p in P})
    diasN = [d for d in sorted(clase) if "2026-10-21" <= d <= M.ULTIMO_DIA and "P" not in clase[d].values()
             and sum(clase[d].get(s, "") in ("N", "otro") for s in slotsP) >= 0.8 * len(slotsP)]
    d25, R25, _ = M.cubo(2025, *M.BJ.PERIODOS[1][1:3], M.BJ.SLOTS_B)
    d26, R26, _ = M.cubo(2026, *M.BJ.PERIODOS[2][1:3], slotsP)
    d24, R24, _ = M.cubo(2024, *M.BJ.PERIODOS[0][1:3], slotsP)
    base = M.Base25(d25, R25)
    jP = {s: j for j, s in enumerate(slotsP)}
    cache = {}

    def obj(anio, dia, s):
        k = (anio, dia, s)
        if k not in cache:
            dd, R = (d26, R26) if anio == 2026 else (d24, R24)
            i, j = dd.index(dia), jP[s]
            o = base.objetivo(dia, s, R["C02"][i, j], R["C05"][i, j], R["BT"][i, j])
            sz = sza_c.get(f"{dia} {s // 6:02d}:{s % 6 * 10:02d}") if (dia in diasP and anio == 2026) else None
            sz = M.sza_crater(M.slot_dt(dia, s)) if sz is None else sz
            ev = o is not None and sz < M.SZA_MAX \
                and o["ok2"][M.ZONA2].mean() >= M.FR_ZONA
            cache[k] = o if ev else None
        return cache[k]

    Pinfo = [dict(dia=d, s=s, dil=M.mascaras(h)[0]) for d, s, h in P]
    idx = {d: [i for i, p in enumerate(Pinfo) if p["dia"] == d] for d in diasP}

    def ub(o, m2, b):
        if o is None:
            return np.nan
        ok = m2 & o["ok2"]
        if m2.sum() == 0 or ok.sum() / m2.sum() < M.FR_HUELLA:
            return np.nan
        return float(np.nanmean(o[f"U{b}"][M.hijos(ok, b)]))

    def md(v):
        v = np.array(v, float)
        return float(np.nanmean(v)) if np.isfinite(v).any() else np.nan

    rng = np.random.default_rng(SEM_PH)
    out = {"nota": "POST HOC: escrito después de ver la medida; no cambia ningún veredicto", "bandas": {}}
    for b in ("C02", "C05"):
        TU = {d: md([ub(obj(2026, d, Pinfo[i]["s"]), Pinfo[i]["dil"][0], b) for i in idx[d]]) for d in diasP}
        dU = [d for d in diasP if np.isfinite(TU[d])]
        T = float(np.mean([TU[d] for d in dU]))
        VR = [np.array([md([ub(obj(2026, d, Pinfo[i]["s"]), Pinfo[i]["dil"][j], b) for i in idx[d]])
                        for j in range(12)]) for d in dU]
        VN = [np.array([md([ub(obj(2026, n, Pinfo[i]["s"]), Pinfo[i]["dil"][0], b) for i in idx[d]])
                        for n in diasN]) for d in dU]
        VY = [np.array([md([ub(obj(2024, y, Pinfo[i]["s"]), Pinfo[i]["dil"][0], b) for i in idx[d]])
                        for y in d24]) for d in dU]
        res = dict(T=round(T, 4), por_dia={d: round(TU[d], 4) for d in dU},
                   N_evaluables_por_dia={d: int(np.isfinite(v).sum()) for d, v in zip(dU, VN)},
                   N_valores_por_dia={d: [round(x, 3) for x in v[np.isfinite(v)]] for d, v in zip(dU, VN)})
        for nom, V in (("R", VR), ("N", VN), ("Y", VY)):
            nl = M.mc_mean(V, rng, B_PH)
            p, n = M.pval(T, nl)
            pi, _ = M.pval(-T, -nl)          # cola de abajo: ¿se aparta CONTRA la ceniza más que el nulo?
            res[f"p_{nom}_arriba"] = round(p, 5)
            res[f"p_{nom}_abajo"] = round(pi, 5)
            res[f"n_{nom}"] = n
            res[f"null_{nom}_p1_p50_p99"] = [round(float(np.nanpercentile(nl, q)), 4) for q in (1, 50, 99)]
        out["bandas"][b] = res
        print(b, json.dumps(res, ensure_ascii=False)[:900], flush=True)

    # 2. cambio de toda la zona despejada (ρ − B), por año y banda, en las casillas de los P
    zona = {}
    for nom, anio, dias in (("2026_P", 2026, diasP), ("2026_N", 2026, diasN), ("2024", 2024, d24)):
        acc = {b: [] for b in ("C02", "C05")}
        for d in dias:
            for s in sorted({p["s"] for p in Pinfo}):
                o = obj(anio, d, s)
                if o is None:
                    continue
                for b in ("C02", "C05"):
                    sel = M.hijos(o["ok2"] & M.ZONA2, b)
                    v = (o[f"R{b}"] - o[f"B{b}"])[sel]
                    acc[b].append(float(np.nanmedian(v)))
        zona[nom] = {b: dict(cuadros=len(v), mediana=round(float(np.median(v)), 4),
                             p10=round(float(np.percentile(v, 10)), 4), p90=round(float(np.percentile(v, 90)), 4))
                     for b, v in acc.items() if v}
        print(nom, zona[nom], flush=True)
    out["zona_rho_menos_B"] = zona
    with open(os.path.join(M.RES, "s31f_posthoc.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print("listo", f"{time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
