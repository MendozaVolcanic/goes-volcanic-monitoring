r"""S20b, controles POST HOC de la prueba 1 (escritos despues de ver SEÑAL en M1 y M2; no cambian el veredicto, dicen
si se puede creer).

(a) Especificidad de M1: una capa GRIS (eps12 = eps11, sin firma de ceniza) que enfria el pixel, pintada en los dias
    base, da tambien una BTD pareada baja? El pareo por BT11 cambia de pares cuando el pixel se enfria; si la capa gris
    produce p <= 0,05 tan seguido como la ceniza, M1 no separa ceniza de un simple enfriamiento.
(b) Serie del pixel de mayor f: M1 y M2 en cada dia despejado del cubo (E1, cuadro o +-10 min), para ver si el valor
    del evento es parte de una tendencia de la temporada.
(c) Placebo de cumbre: p contra los corrimientos en que el pixel de mayor f cae en un pixel de cota a +-300 m de la
    real (otras cumbres de la ventana), no en cualquier lugar.

Uso: python -I s20b_posthoc.py
"""
import json
import os
import sys

import numpy as np

sys.stdout.reconfigure(encoding="utf-8")
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import s20b_medir as X  # noqa: E402

M29, H24, S = X.M29, X.H24, X.S


def main():
    r14, r15, X.ACM, co14, co15 = H24.cargar()
    X.DESP = H24.despejada("chillan", X.ACM)
    alturas = sorted({round(float(np.load(os.path.join(S.TRABAJO, f"mascara_{d}.npz"))["H"]) + dz)
                      for d in X.EVENTOS for dz in (-1000, 0, 1000)})
    M = M29.Medidor(r14, r15, co14, co15, H24.gfs_t(np.array(alturas, float)), alturas)
    out = {}
    for dia in X.EVENTOS:
        filas = X.elegir_cuadro(dia)
        s = X.slot(filas[0]["cuadro"])
        d0 = X.dia_idx(dia)
        P = X.Prueba(M, dia)
        corr = P.corrimientos()[::X.PASO_CORR]
        nul, tablas = X.nulos_y_tablas(P, dia, s, corr)
        r = {"cuadro": filas[0]["cuadro"]}
        # (a) capa gris contra capa de ceniza (beta 0,7), mismas f y eps
        for nom_beta, beta in (("ceniza_beta_0.7", 0.7), ("gris_beta_1.0", 1.0)):
            M29.BETA = beta
            sp = X.seco_y_potencia(P, nul, tablas, [0.3, 0.5, 0.9])
            r[nom_beta] = {m: {"potencia_p05": sp[m]["potencia"], "D_esperado": sp[m]["senal_esperada_D"]}
                           for m in ("M1", "M2")}
        M29.BETA = 0.7
        # (b) serie del pixel de mayor f
        j = int(np.argmax(P.w))
        pm = int(P.pix[j])
        serie = []
        for d in range(H24.NDIAS):
            sl = [x for x in (s - 1, s, s + 1) if X.DESP[d, x]] if d != d0 else [s]
            if not sl:
                continue
            v = np.array([M.medir(d, x, pm, P.ex4, P.ex1, hk=P.hk) for x in sl], float)
            serie.append({"dia": X.nombre(d), "evento": d == d0, "excluido_H24": bool(H24.DIA_EXCL[d]),
                          "otro_evento": X.nombre(d) in X.EVENTOS and d != d0,
                          "M1": round(float(np.nanmedian(v[:, 0])), 3), "M2": round(float(np.nanmedian(v[:, 1])), 3),
                          "BT11": round(float(np.nanmedian([M.bt11[d, x, pm] for x in sl])), 2)})
        r["serie_pixel_mayor_f"] = {"fila": int(X.FILA[pm]), "col": int(X.COL[pm]), "f": round(float(P.w[j]), 3),
                                    "dias": serie}
        # (c) placebo de cumbre
        K_ev = X.tabla_k(P, d0, [s], corr)
        D = X.anomalia(K_ev, list(tablas.values()))
        z0 = float(S.ZDEM.ravel()[pm])
        sel = [b for b, c in enumerate(corr)
               if abs(float(S.ZDEM[X.FILA[pm] + c[0], X.COL[pm] + c[1]]) - z0) <= 300.0]
        r["placebo_cumbre"] = {"cota_pixel_m": round(z0), "corrimientos_misma_cota": len(sel)}
        for i, m in ((0, "M1"), (1, "M2")):
            cs = D[1:, i][sel]
            cs = cs[np.isfinite(cs)]
            r["placebo_cumbre"][m] = {"D_real": round(float(D[0, i]), 3), "n": int(len(cs)),
                                      "p": round(float((cs <= D[0, i]).mean()), 4) if len(cs) else None,
                                      "p5_p50": [round(float(x), 3) for x in np.percentile(cs, [5, 50])] if len(cs) else None}
        out[dia] = r
        print(dia, json.dumps({k: v for k, v in r.items() if k != "serie_pixel_mayor_f"}, ensure_ascii=False), flush=True)
    with open(os.path.join(X.RES, "posthoc.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
