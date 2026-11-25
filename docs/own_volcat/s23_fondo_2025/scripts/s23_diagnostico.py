r"""S23a, diagnóstico POST HOC (mirado después del veredicto; no lo cambia).

Tres preguntas que dejó la medida:
1. ¿Por qué cuadros P sin nubes quedan sin evaluar (28-10: 26 P, 0 evaluados, 0 por nubes)? Se separan las causas
   posibles por cuadro: compuerta, píxeles borrados por nube dinámica con el nublado de costumbre de 2025 contra el de
   2026 (S22b), píxeles sin línea base de 2025, y tajadas válidas que quedan.
2. ¿Cuánto vale pN de verdad? Cuántos cuadros N de 2026 evaluados hay a ±60 min de cada P evaluado, y cuántos
   alcanzados: con pocos, un azar estimado en 0 es degenerado.
3. ¿Depende todo de un día? Recuerdo y p25 dejando fuera cada día con P evaluados.
Uso: python -I s23_diagnostico.py
"""
import json
import os
import sys

import numpy as np

sys.stdout.reconfigure(encoding="utf-8")
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import s23_medir as S  # noqa: E402
B, M = S.B, S.M


def tajadas_validas(v):
    n = 0
    for k in range(M.NSEC):
        x = v[M.SEC == k]
        x = x[np.isfinite(x)]
        n += int(len(x) >= 0.5 * M.NPS[k] and len(x) >= M.NCOLA)
    return n


if __name__ == "__main__":
    D = S.Detector(ref="2025", con_blanco=True)
    D26 = S.Detector(ref="2026N", con_blanco=False)        # sólo para el nublado de costumbre de S22b
    U, _ = D.umbral(None)
    B0 = D.base(None)
    FF = {d: S.disparos(D.ST, D.KT, d, U) for d in range(B.ND)}
    filas = []
    for d in range(B.ND):
        for s in np.flatnonzero(D.CLT[d] == "P"):
            m1 = np.load(os.path.join(B.TRAB, "dev_m1.npy"), mmap_mode="r")[d, s] if d < B.NDEV else None
            nd25 = B.dinamica(D.acmT[d, s], D.ESTAT[s])
            nd26 = B.dinamica(D.acmT[d, s], D26.ESTAT[s])
            con_m1 = np.isfinite(np.asarray(m1)) if m1 is not None else np.zeros(M.NA, bool)
            v = D.mmT[d, s] - B0[s]
            filas.append({"dia": B.fecha(d), "hora": M.hhmm(s), "evaluado": bool(FF[d][1][s]),
                          "alcanzado": bool(B.alcanzado(*FF[d], s)[1]) if FF[d][1][s] else None,
                          "nube_dinamica_2025": S._r(D.FDT[d, s]), "nube_dinamica_si_costumbre_2026": S._r(nd26[M.AP].mean()),
                          "frac_anillo_con_M1": S._r(con_m1.mean()),
                          "frac_borrada_por_nube_2025": S._r(B.borde(nd25)[M.AP].mean()),
                          "frac_borrada_si_costumbre_2026": S._r(B.borde(nd26)[M.AP].mean()),
                          "frac_sin_base_2025": S._r(np.isnan(B0[s]).mean()),
                          "tajadas_validas": tajadas_validas(v), "U": S._r(U[s]), "S": S._r(D.ST[d, s])})
    # 2) pN: N de 2026 evaluados alrededor de cada P evaluado
    Nsl, Nal = [], []
    for d in range(B.ND):
        F, ev = FF[d]
        for s in np.flatnonzero(ev & (D.CLT[d] == "N")):
            Nsl.append(s)
            Nal.append(B.alcanzado(F, ev, s)[1])
    Nsl, Nal = np.array(Nsl), np.array(Nal)
    alrededor = []
    for f in filas:
        if not f["evaluado"]:
            continue
        s = M.slot(f["hora"])
        dd = np.abs(Nsl - s) % 144
        dd = np.minimum(dd, 144 - dd) <= S.W_AZAR
        alrededor.append({"dia": f["dia"], "hora": f["hora"], "N_alrededor": int(dd.sum()),
                          "N_alcanzados": int(Nal[dd].sum())})
    # 3) dejando fuera cada día
    _, sl25, al25, _ = S._seco_2025(D)
    r25 = S.azar_por_hora(sl25, al25)
    ev_P = [(f["dia"], M.slot(f["hora"]), f["alcanzado"]) for f in filas if f["evaluado"]]
    sin_dia = {}
    for dia in sorted({x[0] for x in ev_P}):
        q = [x for x in ev_P if x[0] != dia]
        h = sum(a for *_, a in q)
        sin_dia[dia] = {"P_evaluados": len(q), "P_alcanzados": h,
                        "p25": S.poisson_binomial_cola([r25[s] for _, s, _ in q], h) if q else None}
    out = {"nota": "POST HOC, no cambia el veredicto", "por_cuadro_P": filas, "N_2026_alrededor_de_P": alrededor,
           "sin_cada_dia": sin_dia,
           "resumen_no_evaluados": {
               "P": len(filas), "evaluados": sum(f["evaluado"] for f in filas),
               "no_eval_compuerta": sum((not f["evaluado"]) and f["nube_dinamica_2025"] is not None
                                        and f["nube_dinamica_2025"] > B.G_MAX for f in filas),
               "no_eval_pocas_tajadas": sum((not f["evaluado"]) and f["tajadas_validas"] < M.MIN_SEC for f in filas)}}
    json.dump(out, open(os.path.join(S.RES, "diagnostico_posthoc.json"), "w", encoding="utf-8"), ensure_ascii=False,
              indent=1)
    print(json.dumps(out["resumen_no_evaluados"], ensure_ascii=False))
    print(json.dumps(out["sin_cada_dia"], ensure_ascii=False))
    for f in filas:
        if f["dia"] in ("2026-10-28", "2026-11-14", "2026-11-08") and f["hora"][-1] == "0":
            print(f)
    print(alrededor)
