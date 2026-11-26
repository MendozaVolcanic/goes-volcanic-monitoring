r"""V201, control del instrumento: el mismo placebo de v201_placebo.py, pero con "alcanzado" sintético e independiente
(cada cuadro evaluado de 2025 alcanzado con probabilidad r25[hora], sin rachas). Si el arnés es sano, aquí el p25 tiene
que rechazar el 1 % o menos (el Poisson binomial es exacto bajo independencia y un p discreto es conservador). Si el
arnés diera más de 1 % aquí, el exceso de v201_placebo.py sería un defecto mío y no de la confirmación.

Además: sobredispersión por día (varianza del número de cuadros alcanzados por día contra la que supone el Poisson
binomial) y los días de 2025 que más rechazan, con sus disparos por hora.
Entrada: D:\goes_notas\s28\s28b\v201\disparos.npz. Ningún día posterior al 24-11-2026.
"""
import os
import sys

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import v201_placebo as V  # noqa: E402

U, S, M = V.U, V.S, V.M
Zf = V.Zf


def main():
    T, pares_t = V.plantillas()
    plant = [np.array([T[a], T[b]]) for a, b in pares_t]
    rng = np.random.default_rng(7)
    d25 = [f"{S.T0R + U.timedelta(days=d):%Y-%m-%d}" for d in range(62)]
    for nom, (k, p, rmin) in V.REGLAS.items():
        F25, E25 = Zf[f"F25_{k}_{p}"], Zf[f"E25_{k}_{p}"]
        A25 = np.array([V.alc_dia(F25[d], E25[d]) for d in range(62)]) & E25
        r62 = U.azar([(F25[d], E25[d]) for d in range(62)])
        print(f"{nom}:")
        # control: alcanzado independiente con la misma tasa por hora y los mismos cuadros evaluados
        for rep in range(3):
            Asint = (rng.random(E25.shape) < np.nan_to_num(r62)[None, :]) & E25
            V.correr(nom, E25, Asint, d25, lambda i, j: r62, plant, f"CONTROL independiente, réplica {rep}")
        # sobredispersión por día
        n_obs = A25.sum(1).astype(float)
        mu = (np.nan_to_num(r62)[None, :] * E25).sum(1)
        var_pb = (np.nan_to_num(r62 * (1 - r62))[None, :] * E25).sum(1)
        con = E25.sum(1) > 0
        print(f"   por día (2025, {int(con.sum())} días con cuadros evaluados): alcanzados observados suma "
              f"{n_obs.sum():.0f}, esperados {mu.sum():.1f}; varianza observada de (obs - esp) "
              f"{np.var((n_obs - mu)[con]):.1f} contra la media de la varianza Poisson binomial {var_pb[con].mean():.2f}"
              f" => razón {np.var((n_obs - mu)[con]) / var_pb[con].mean():.1f}")
        orden = np.argsort(-n_obs)[:6]
        print("   días de 2025 con más cuadros alcanzados: " + "; ".join(
            f"{d25[d]} {int(n_obs[d])} de {int(E25[d].sum())} (esp {mu[d]:.1f}), disparos {int(F25[d].sum())}, horas "
            f"{M.hhmm(int(np.flatnonzero(F25[d])[0]))} a {M.hhmm(int(np.flatnonzero(F25[d])[-1]))}"
            for d in orden if F25[d].any()))
        cero = int((n_obs[con] == 0).sum())
        print(f"   días con 0 alcanzados: {cero} de {int(con.sum())}; los 5 días con más ponen "
              f"{np.sort(n_obs)[-5:].sum() / n_obs.sum():.2f} del total")
        # largo de las rachas de disparo (cuadros seguidos con F)
        rachas = []
        for d in range(62):
            x = np.flatnonzero(F25[d])
            if len(x):
                cortes = np.flatnonzero(np.diff(x) > 1)
                rachas += [len(r) for r in np.split(x, cortes + 1)]
        print(f"   rachas de disparo en 2025: {len(rachas)}, mediana {np.median(rachas):.0f}, máx {max(rachas)}, "
              f"media {np.mean(rachas):.2f} cuadros")


if __name__ == "__main__":
    main()
