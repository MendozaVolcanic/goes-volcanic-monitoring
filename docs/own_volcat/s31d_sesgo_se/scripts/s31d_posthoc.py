r"""S31d, POST HOC (escrito después de ver M1 y M2; no cambia el veredicto del criterio).

Por qué: M2 (cada píxel sorteado por separado de sus propios residuos de 2025) reproduce la cuota SE observada. Eso
dice que la preferencia viaja en la distribución de cada píxel por separado, no en la coherencia dentro del cuadro.
Pero la distribución de un píxel a lo largo de la temporada puede llevar dentro tanto lo fijo (cota, roca, nieve, pocos
controles) como algo atmosférico que se repite muchos días (la estela de sotavento con el viento habitual). Aquí se
parte el pozo del que se sortea:

PH1  pozo sólo de cuadros con el entorno del cráter despejado (E1) contra pozo sólo de cuadros no despejados.
PH2  pozo sólo de cuadros cuyo viento a 700 hPa lleva el sotavento al SE (120° a 210°, >= 5 m/s) contra pozo de
     cuadros con sotavento fuera del SE (>= 5 m/s).
PH3  por tajada: dispersión, percentil 2 y asimetría de los residuos de cada píxel (mediana de la tajada).

Si con pozo de sotavento fuera la cuota SE sigue alta, la cola de los píxeles del SE no la pone el sotavento; si cae,
sí. Uso: python -I -B s31d_posthoc.py   (escribe resultados/s31d_posthoc.json)
"""
import json
import os
import sys

import numpy as np
from scipy import stats

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import s31d_medir as X  # noqa: E402
S, B, M = X.S, X.B, X.M


def p2_pozo(r, pozo, semilla):
    mask = np.isfinite(r)
    rng = np.random.default_rng(semilla)
    Z = np.full((X.N_MC, M.NA), np.nan, np.float32)
    todos = pozo[np.isfinite(pozo)]
    for i in np.flatnonzero(mask):
        v = pozo[:, i]
        v = v[np.isfinite(v)]
        if len(v) < X.MIN_POZO_PIX:
            v = todos
        Z[:, i] = v[rng.integers(0, len(v), X.N_MC)]
    return X.p_se_cola(*X.estadistico_lote(Z)[:2])


def pozo_filtrado(D, d, s, cond):
    Bd = D.base(d)
    filas = [D.mmR[dd, x] - Bd[x] for dd in D.DIASR if dd != d for x in range(144)
             if M.dslot(x, s) <= X.W_POZO and D.GATER[dd, x] and cond(dd, x)]
    return np.array(filas, np.float32)


def clase_viento(dd, x):
    th, v = X.viento(X.hora_sinoptica(dd, x), X.NIVEL)
    if not np.isfinite(th) or v < X.V_MIN:
        return "debil"
    return "SE" if X.en_se(th) else "fuera"


def main():
    B.PCT_U = X.P_STAR
    D = S.Detector(ref="2025", con_blanco=False)
    disp = X.disparos_anio(D.SR, D.KR, D.DIASR, lambda d: D.umbral(d)[0])
    assert len(disp) == 138
    out = {"rotulo": "POST HOC: no decide; escrito después de ver M1 y M2", "cuota_obs": float(np.mean(
        [k in X.SE for *_, k in disp]))}
    conds = {"E1_despejado": lambda dd, x: bool(D.E1R[dd, x]),
             "no_despejado": lambda dd, x: not D.E1R[dd, x],
             "sotavento_SE": lambda dd, x: clase_viento(dd, x) == "SE",
             "sotavento_fuera": lambda dd, x: clase_viento(dd, x) == "fuera"}
    for nom, c in conds.items():
        ps, nfil = [], []
        for d, s, k in disp:
            pz = pozo_filtrado(D, d, s, c)
            nfil.append(len(pz))
            ps.append(p2_pozo(D.mmR[d, s] - D.base(d)[s], pz, 1000 * d + s) if len(pz) >= 20 else np.nan)
        ps = np.array(ps)
        out[f"E2_pozo_{nom}"] = {"E": float(np.nanmean(ps)), "cuadros_con_pozo": int(np.isfinite(ps).sum()),
                                 "filas_pozo_mediana": int(np.median(nfil))}
        print(nom, out[f"E2_pozo_{nom}"], flush=True)
    # PH3: forma de la distribución de cada píxel, por tajada
    R = np.array([D.mmR[d, s] - D.base(d)[s] for d in D.DIASR for s in range(144) if D.GATER[d, s]], np.float32)
    sd = np.nanstd(R, 0)
    p2 = np.nanpercentile(R, 2, axis=0)
    sk = np.array([stats.skew(R[np.isfinite(R[:, i]), i]) if np.isfinite(R[:, i]).sum() > 50 else np.nan
                   for i in range(M.NA)])
    nval = np.isfinite(R).mean(0)
    out["por_tajada"] = [{"k": k, "grados": f"{30 * k}-{30 * k + 30}",
                          "sd_mediana_K": X._r(np.nanmedian(sd[M.SEC == k])),
                          "p2_mediana_K": X._r(np.nanmedian(p2[M.SEC == k])),
                          "asimetria_mediana": X._r(np.nanmedian(sk[M.SEC == k])),
                          "frac_cuadros_con_valor_mediana": X._r(np.nanmedian(nval[M.SEC == k]))}
                         for k in range(M.NSEC)]
    z = M.ZDEM[M.AP]
    ok = np.isfinite(p2)
    out["spearman_p2_vs_cota"] = X._r(stats.spearmanr(p2[ok], z[ok])[0])
    out["spearman_p2_vs_controles"] = X._r(stats.spearmanr(p2[ok], [len(c) for c in np.array(M.CTRL_COTA,
                                                                                               dtype=object)[ok]])[0])
    # PH4: distancia al cráter de los 8 píxeles de la cola de la tajada que dispara (S31c: en 2026 marca a 22 a 33 km)
    dist = []
    for d, s, k in disp:
        r = D.mmR[d, s] - D.base(d)[s]
        idx = np.flatnonzero((M.SEC == k) & np.isfinite(r))
        cola = idx[np.argsort(r[idx])[:M.NCOLA]]
        dist += list(M.AD[cola])
    dist = np.array(dist)
    out["distancia_cola_disparos_2025_km"] = {"mediana": X._r(np.median(dist)), "p25": X._r(np.percentile(dist, 25)),
                                              "p75": X._r(np.percentile(dist, 75)),
                                              "frac_4_a_15": X._r((dist < 15).mean()),
                                              "frac_anillo_4_a_15": X._r((M.AD < 15).mean())}
    json.dump(out, open(os.path.join(X.RES, "s31d_posthoc.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps({k: v for k, v in out.items() if k != "por_tajada"}, ensure_ascii=False, indent=1))
    for t in out["por_tajada"]:
        print(t)


if __name__ == "__main__":
    main()
