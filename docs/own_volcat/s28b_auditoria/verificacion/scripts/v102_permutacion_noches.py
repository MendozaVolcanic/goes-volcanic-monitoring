r"""V102 (auditoría S28b), tercer script: la comparación de tasas con la NOCHE como unidad.

Por qué: Fisher sobre cuadros supone cuadros independientes, y los disparos vienen en rachas dentro de una noche
(la regla exige dos cuadros seguidos). Aquí se permuta la etiqueta de año entre noches enteras y se mira la diferencia
de tasas por cuadro. Sólo lee v102_salida.json (conteos por noche ya calculados con el código de S24).

Uso: python -I -B v102_permutacion_noches.py <carpeta con v102_salida.json>
"""
import json
import os
import sys

import numpy as np

sys.stdout.reconfigure(encoding="utf-8")
CARP = sys.argv[1]
o = json.load(open(os.path.join(CARP, "v102_salida.json"), encoding="utf-8"))
N25, N26 = o["por_noche_2025"], o["por_noche_2026"]
T = o["constantes_s24"]["COMUN_MAX"]
N_PERM, SEMILLA = 100000, 0


def prueba(a, b, rng):
    """a, b: listas de (disparos, evaluados) por noche con evaluados > 0. p bilateral de |tasa_b - tasa_a|."""
    f = np.array([x[0] for x in a + b], float)
    n = np.array([x[1] for x in a + b], float)
    na = len(a)
    obs = f[na:].sum() / n[na:].sum() - f[:na].sum() / n[:na].sum()
    ge = 0
    for _ in range(N_PERM):
        i = rng.permutation(len(f))
        d = f[i[na:]].sum() / n[i[na:]].sum() - f[i[:na]].sum() / n[i[:na]].sum()
        ge += abs(d) >= abs(obs) - 1e-15
    return {"noches_a": na, "noches_b": len(b), "tasa_a": f[:na].sum() / n[:na].sum(),
            "tasa_b": f[na:].sum() / n[na:].sum(), "dif_obs": obs, "p_perm_bilateral": (ge + 1) / (N_PERM + 1)}


rng = np.random.default_rng(SEMILLA)
ev = lambda d, cond: [tuple(v) for v in d.values() if v[1] > 0 and cond(v)]  # noqa: E731
res = {
    "regla escrita: 2025 comunes vs 2026 entero": prueba(ev(N25, lambda v: v[0] < T), ev(N26, lambda v: True), rng),
    "simétrica: 2025 comunes vs 2026 comunes": prueba(ev(N25, lambda v: v[0] < T), ev(N26, lambda v: v[0] < T), rng),
    "sin selección: 2025 entero vs 2026 entero": prueba(ev(N25, lambda v: True), ev(N26, lambda v: True), rng),
}
res["nota"] = ("La permutación de la 'regla escrita' NO corrige la selección por resultado de 2025; sólo corrige la "
               "dependencia entre cuadros de una noche. n_perm=%d, semilla=%d" % (N_PERM, SEMILLA))
json.dump(res, open(os.path.join(CARP, "v102_permutacion_noches.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(json.dumps(res, ensure_ascii=False, indent=1))
