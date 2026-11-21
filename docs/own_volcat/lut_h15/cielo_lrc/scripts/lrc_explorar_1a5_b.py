r"""EXPLORACIÓN 2 (cuadros 1 a 5, no decide). Dos preguntas sobre la salida de lrc_explorar_1a5.py:
(1) ¿Alguna candidata explica la variación píxel a píxel del exceso de ε? Regresión del exceso (nuestro − VOLCAT)
    sobre lo que cada candidata cambia (nuestro − candidata), en nube tenue 0,05 <= εtot < 0,3: ρ de Spearman y
    pendiente (una candidata que explicara todo daría pendiente ~1 y ρ alto).
(2) Techo: con el mejor cielo despejado CONSTANTE (desfase mediano lejos de nube espesa, > 20 px, de estos mismos
    cuadros), ¿cuánto de la nube tenue entra en 0,01, y qué gradiente con la distancia queda?
Escribe ../resultados/lrc_explorar_1a5_b.json.
"""
import json
import os
import sys

import numpy as np
from scipy.stats import spearmanr

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import comun as C  # noqa: E402
import lrc_explorar_1a5 as X1  # noqa: E402

NOMBRES = ("a_lrc_clr", "c_max3", "c_max5", "d_med3", "d_clr_suave", "d_clr_vec", "d_nwc21", "d_nwc21_min")


def main():
    acc, EV, DI, D14, CU = {}, [], [], [], []
    cuadros = [C.CS.Cuadro(h) for h in C.E.ELIGE]
    for c in cuadros:
        cand, _ = X1.candidatas(c)
        for n, v in cand.items():
            acc.setdefault(n, []).append(v.ravel())
        EV.append(c.ev.ravel()); DI.append(C.distancia_espesa(c).ravel())
        D14.append(C.V3.por_cuadro(c)["d14"])
    ev, dist, d14 = map(np.concatenate, (EV, DI, D14))
    A = {n: np.concatenate(v) for n, v in acc.items()}
    base = A["base"]
    s0 = np.isfinite(ev) & (ev >= 0.05) & (ev < 0.3) & np.isfinite(base)
    exceso = base - ev
    out = {"cuadros": C.E.ELIGE, "regresion_exceso_sobre_cambio_candidata": {}}
    for n in NOMBRES:
        cam = base - A[n]
        q = s0 & np.isfinite(cam)
        x, y = cam[q], exceso[q]
        pend = float(np.polyfit(x, y, 1)[0]) if np.std(x) > 0 else float("nan")
        out["regresion_exceso_sobre_cambio_candidata"][n] = {
            "n": int(q.sum()), "rho": float(spearmanr(x, y).correlation), "pendiente": pend,
            "cambio_mediano": float(np.median(x)), "exceso_mediano": float(np.median(y))}
    # (2) techo con cielo despejado constante
    lejos = s0 & np.isfinite(d14) & (dist > 20)
    k = float(np.median(d14[lejos]))
    E2, EVa, DIa = [], [], []
    for c in cuadros:
        E2.append(C.eps_nadir(c, clr14=c.clr[14] + k).ravel())
    e2 = np.concatenate(E2)
    out["techo_cielo_constante"] = {"desfase_K_aplicado_mediana_lejos_gt20px": k, **C.resumen(ev, e2, dist)}
    with open(os.path.join(C.RES, "lrc_explorar_1a5_b.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1, ensure_ascii=False)
    print(json.dumps(out, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
