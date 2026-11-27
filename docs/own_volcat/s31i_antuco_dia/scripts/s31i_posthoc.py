r"""S31i, POST HOC (no decide; escrito después de leer resultados/s31i_resultado.json).

Por qué: la medida dijo que, cuando la cumbre de Antuco dispara de día, no hay más nube que a la misma hora de otros
días ni más cielo despejado: los días que disparan parecen días comunes. Pero la nieve de la cumbre (con GOES mismo,
0,86 y 1,6 µm) es 0,81 en 2024 y 2026 contra 0,63 en 2025, el año de la base. Eso apunta a un corrimiento de todo el
año: si la cumbre entera tiene otra BTD a la misma hora porque tiene otra nieve, el umbral del percentil 4,75 de 2025
se cruza más seguido con cualquier vaivén del día. Aquí se mira si eso se ve:
  1. la mediana diaria de S (y de Ā, la anomalía propia) de día, por año, en Antuco, Longaví y Chillán (2024 y 2025;
     Antuco y Longaví también 2026; Chillán 2026 tiene pluma y queda fuera);
  2. la nieve de la cumbre por año en las tres (fs, como en el criterio §3);
  3. S por hora (¿el corrimiento crece con el sol?);
  4. el corrimiento contra la nieve en los cinco pares cumbre-año.

Uso: python -I -B s31i_posthoc.py      (escribe resultados/s31i_posthoc.json; ~15 min)
"""
import json
import os
import sys
import time

import numpy as np
from scipy import stats

sys.stdout.reconfigure(encoding="utf-8")
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import s31i_medir as W  # noqa: E402

DIA = list(W.DIA)


def resumen_dias(S, A, F, E):
    """Mediana por día de S y de Ā (cuadros de día evaluados) y tasa diaria."""
    S_d, A_d, tasa = [], [], []
    for d in range(W.ND):
        m = E[d, 72:] & np.isfinite(S[d, 72:])
        if m.sum() >= 20:
            S_d.append(np.median(S[d, 72:][m]))
            A_d.append(np.nanmedian(A[d, 72:][m]))
            tasa.append(F[d, 72:].sum() / m.sum())
    return np.array(S_d), np.array(A_d), np.array(tasa)


def anom_propia(Z, bz, P):
    """Ā por cuadro: media de la anomalía propia (BTD menos base) de los dos píxeles que hacen S."""
    nd = Z.shape[0]
    out = np.full((nd, 144), np.nan)
    for d in range(nd):
        bd = bz[d] if bz.ndim == 3 else bz
        a = Z[d] - bd
        for s in range(144):
            p1, p2 = P[d, s]
            if p1 >= 0:
                out[d, s] = (a[s, p1] + a[s, p2]) / 2
    return out


def main():
    t = time.time()
    OPT = {a: np.load(os.path.join(W.TRAB, f"optica_{a}.npz")) for a in (2024, 2025, 2026)}
    r25 = W.cubos(2025)
    out = {"rotulo": "POST HOC: no decide; se escribió después de leer s31i_resultado.json"}
    casos = (("antuco", (2024, 2026)), ("longavi", (2024, 2026)), ("chillan", (2024,)))
    for sitio, años in casos:
        res = {}
        for año in años:
            zv, sec, bla = W.correr(sitio, año, r25, W.cubos(año))
            F, E = W.matrices(bla)
            S = zv.ST[:W.ND]
            A = anom_propia(zv.ZT[:W.ND], zv.bz, zv.PT[:W.ND])
            Sd, Ad, tasa = resumen_dias(S, A, F, E)
            res[str(año)] = {"S_dia_mediana": W._r(np.median(Sd)), "A_dia_mediana": W._r(np.median(Ad)),
                             "dias": int(Sd.size), "tasa_dia": W._r(F[:, 72:].sum() / E[:, 72:].sum()),
                             "S_por_hora": [W._r(np.nanmedian(np.where(E[:, 6 * h:6 * h + 6],
                                                                       S[:, 6 * h:6 * h + 6], np.nan)), 3)
                                            for h in range(12, 24)]}
            if "2025" not in res:
                F5, E5 = W.matrices(sec)
                A5 = anom_propia(zv.Z25, zv.BZ, zv.PR)
                Sd5, Ad5, _ = resumen_dias(zv.SR, A5, F5, E5)
                res["2025"] = {"S_dia_mediana": W._r(np.median(Sd5)), "A_dia_mediana": W._r(np.median(Ad5)),
                               "dias": int(Sd5.size), "tasa_dia": W._r(F5[:, 72:].sum() / E5[:, 72:].sum()),
                               "S_por_hora": [W._r(np.nanmedian(np.where(E5[:, 6 * h:6 * h + 6],
                                                                         zv.SR[:, 6 * h:6 * h + 6], np.nan)), 3)
                                              for h in range(12, 24)]}
                res["S_dias_2025"] = Sd5.tolist()
            res[f"S_dias_{año}"] = Sd.tolist()
            # Mann-Whitney por días: ¿el año entero corrido respecto de 2025?
            u = stats.mannwhitneyu(Sd, np.array(res["S_dias_2025"]), alternative="less")
            res[str(año)]["MW_menor_que_2025_p"] = W._r(u.pvalue)
            print(sitio, año, json.dumps(res[str(año)])[:300], f"{time.time() - t:.0f} s", flush=True)
        for año in (2024, 2025, 2026):
            fs = W.fs_dia(OPT[año][f"{sitio}_fnieve"], OPT[año][f"{sitio}_ts"])
            res.setdefault(str(año), {})["fs_media"] = W._r(np.nanmean(fs))
        for k in [k for k in res if k.startswith("S_dias_")]:
            res[k] = [W._r(v, 3) for v in res[k]]
        out[sitio] = res
    pares = []
    for sitio, años in casos:
        r = out[sitio]
        for año in años:
            pares.append({"cumbre": sitio, "año": año,
                          "dS": W._r(r[str(año)]["S_dia_mediana"] - r["2025"]["S_dia_mediana"]),
                          "dfs": W._r(r[str(año)]["fs_media"] - r["2025"]["fs_media"]),
                          "razon_tasa": W._r(r[str(año)]["tasa_dia"] / r["2025"]["tasa_dia"])})
    out["pares"] = pares
    print(json.dumps(pares), flush=True)
    json.dump(out, open(os.path.join(W.RES, "s31i_posthoc.json"), "w", encoding="utf-8"), ensure_ascii=False,
              indent=1)


if __name__ == "__main__":
    main()
