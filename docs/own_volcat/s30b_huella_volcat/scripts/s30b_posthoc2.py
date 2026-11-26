r"""S30b, post hoc 2 (no decide; escrito después de ver las figuras).

Por qué: el criterio (§1) toma como huella sólo los objetos de VOLCAT anclados (con algún píxel a 10 km o menos del
cráter). En las figuras del 08-11 y del 11-11 la huella anclada es un píxel pegado al cráter, mientras S26a describía
la pluma de esos días a 15 a 40 km al SSE: si VOLCAT la dibuja desprendida, el criterio la dejó fuera. Aquí se repite
la medida con la huella = TODA la ceniza de VOLCAT a 40 km o menos del cráter (anclada o no), mismos nulos, semilla 0.
También: distancia al cráter de los píxeles disparados del anillo contra la de la huella en los cuadros que coinciden.

Uso: python -I -B s30b_posthoc2.py   (escribe resultados/s30b_posthoc2.json)
"""
import json
import os
import sys
from collections import defaultdict

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import s30b_medir as S30  # noqa: E402

C29, M = S30.C29, S30.M


def huella_40(dia, s):
    ash, err = S30.G.png_volcat(dia, s)
    if ash is None:
        return err, None
    h = np.flatnonzero((ash & (C29.DIST <= 40.0)).ravel())
    return ("ok" if len(h) else "vacía"), h


def correr(fh):
    T = S30.leer_tabla()
    cache = {}

    def H(dia, s):
        if (dia, s) not in cache:
            st, h = fh(dia, s) if 0 <= s < 144 else ("fuera", None)
            cache[(dia, s)] = S30.Huella(h) if st == "ok" else None
        return cache[(dia, s)]

    items, orc, don, dist = [], [], defaultdict(list), []
    for dia in sorted(T):
        for s in sorted(T[dia]):
            if T[dia][s]["clase"] != "P" or H(dia, s) is None:
                continue
            hu = H(dia, s)
            di = S30.disparos(T[dia], s)
            don[dia].append(hu)
            items.append((dia, hu, di))
            hn = H(dia, s - 1) or H(dia, s + 1)
            if hn is not None:
                orc.append((dia, hu, S30.oraculo_disparos(hn)))
            c = S30.coincide(hu, di)
            if c.get("a"):
                ring = hu.h[S30.AMASK[hu.h]]
                dist.append({"dia": dia, "hora": M.hhmm(s),
                             "km_disparo_mediana": round(float(np.median(S30.DISTF[di["Ca"]])), 1),
                             "km_huella_anillo_max": round(float(S30.DISTF[ring].max()), 1)})
    out = {}
    rng = np.random.default_rng(0)
    for clave, usaR in (("u", True), ("a", True), ("z", False)):
        r = S30.prueba(items, clave, don, rng, usar_R=usaR)
        o = S30.prueba(orc, clave, don, rng, usar_R=usaR)
        r["veredicto_si_fuera_criterio"] = S30.veredicto(r, o, clave)
        out[clave] = {"detector": r, "oraculo": o}
        print(clave, r["T"], r["n"], r.get("R", {}).get("p"), r["D"]["p"], "| oráculo", o["T"], o["n"],
              o.get("R", {}).get("p"), o["D"]["p"], "|", r["veredicto_si_fuera_criterio"], flush=True)
    return out, dist


if __name__ == "__main__":
    res = {"rotulo": "POST HOC: huella = toda la ceniza a <= 40 km; no decide"}
    res["toda_la_ceniza_40km"], _ = correr(huella_40)
    _, res["distancias_anclada"] = correr(S30.huella)
    for x in res["distancias_anclada"]:
        print(x)
    json.dump(res, open(os.path.join(S30.RES, "s30b_posthoc2.json"), "w", encoding="utf-8"), ensure_ascii=False,
              indent=1, default=lambda x: x.item() if hasattr(x, "item") else str(x))
