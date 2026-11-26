r"""S30b, post hoc (no decide nada; escrito después de ver el resultado del criterio).

Por qué: el anillo de S26a disparó en 2026 casi sólo en las tajadas 4 a 6 (120° a 210°, SE a SSO), en cuadros P, N y
"otro". Si en 2025, sin pluma, también dispara hacia allá, la coincidencia de rumbo con VOLCAT puede ser el sesgo del
detector cruzado con el rumbo habitual de la pluma. Y el oráculo del anillo quedó en p_D = 0,0118 con la semilla 0,
pegado al umbral: se mira cuánto depende de la semilla (lección S28b sobre S28a).

1. Tajadas de los disparos del anillo en el ensayo en seco de 2025 a p* 4,75 (cada día sin sí mismo, s26a_medir).
2. p_D del anillo y de su oráculo con las semillas 1 a 20 (B = 9.999 cada una).

Uso: python -I -B s30b_posthoc.py   (escribe resultados/s30b_posthoc.json)
"""
import json
import os
import sys
from collections import Counter

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import s30b_medir as S30  # noqa: E402

sys.path.insert(0, os.path.join(S30.OV, "s26a_combinado", "scripts"))


def tajadas_2025():
    import s26a_medir as U
    X = U.Partes()
    sec = X.seco(4.75)
    c = Counter()
    for d, (F, ev) in enumerate(sec["a"]):
        for s in np.flatnonzero(F):
            c[int(X.A.KR[d, s])] += 1
    return dict(sorted(c.items()))


def semillas():
    T = S30.leer_tabla()
    hP, items, orc = {}, [], []
    cache = {}

    def H(dia, s):
        if (dia, s) not in cache:
            st, h = S30.huella(dia, s) if 0 <= s < 144 else ("fuera", None)
            cache[(dia, s)] = S30.Huella(h) if st == "ok" else None
        return cache[(dia, s)]

    for dia in sorted(T):
        for s in sorted(T[dia]):
            if T[dia][s]["clase"] == "P" and H(dia, s) is not None:
                hP[(dia, s)] = H(dia, s)
    don = {}
    for (dia, s), hu in hP.items():
        don.setdefault(dia, []).append(hu)
        items.append((dia, hu, S30.disparos(T[dia], s)))
        hn = H(dia, s - 1) or H(dia, s + 1)
        if hn is not None:
            orc.append((dia, hu, S30.oraculo_disparos(hn)))
    out = {"anillo": [], "oraculo_anillo": []}
    for sem in range(1, 21):
        rng = np.random.default_rng(sem)
        out["anillo"].append(S30.prueba(items, "a", don, rng, usar_R=False)["D"]["p"])
        out["oraculo_anillo"].append(S30.prueba(orc, "a", don, rng, usar_R=False)["D"]["p"])
        print(sem, out["anillo"][-1], out["oraculo_anillo"][-1], flush=True)
    out["oraculo_anillo_bajo_0_01"] = sum(p <= 0.01 for p in out["oraculo_anillo"])
    return out


if __name__ == "__main__":
    res = {"rotulo": "POST HOC: no decide; escrito después de ver el resultado del criterio"}
    res["semillas_1_20"] = semillas()
    res["tajadas_disparo_anillo_2025_seco_p475"] = tajadas_2025()
    print(json.dumps(res["tajadas_disparo_anillo_2025_seco_p475"]), flush=True)
    json.dump(res, open(os.path.join(S30.RES, "s30b_posthoc.json"), "w", encoding="utf-8"), ensure_ascii=False,
              indent=1)
