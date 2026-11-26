r"""V208: ¿de qué días sale el nublado de costumbre de 2026 congelado (estat_2026.npy) y qué días cubren las clases de
VOLCAT que usan S23, S25a y S26a?

Sólo lee: los dos CSV de clases del repo, los cubos de desarrollo de D:\goes_notas\s22\s22b (21-09 a 21-11-2026, días
ya vistos) y el estat congelado. No corre el detector.

  1. Cobertura de días de las clases (`s22b_medir.clases()`: frames_calor.csv más volcat_clases_22a24nov.csv).
  2. Rehace el nublado de costumbre con el mismo bloque de `s23_medir.Detector.__init__` (ref="2026N", líneas 141 a
     156) y lo compara con el congelado por hash: si coincide, la procedencia queda probada y se sabe de qué días sale.
  3. Informativo: el mismo cálculo con TODOS los cuadros despejados por E1 de los 62 días (sin pedir clase N de
     VOLCAT, como se hace con 2025) y cuántos píxeles-hora cambian respecto del congelado, en la grilla y en el anillo.

Uso: python -I -B v208_estat.py
"""
import hashlib
import json
import os
import sys
from datetime import timedelta

import numpy as np

sys.stdout.reconfigure(encoding="utf-8")
AQUI = os.path.dirname(os.path.abspath(__file__))
OV = os.path.abspath(os.path.join(AQUI, "..", "..", ".."))
sys.path.insert(0, os.path.join(OV, "s23_fondo_2025", "scripts"))
import s23_medir as S  # noqa: E402
B, M, H24 = S.B, S.M, S.H24
ESTAT = r"D:\goes_notas\s23\s23b\estat_2026.npy"


def costumbre(acm, usar, dias):
    e1 = H24.despejada("chillan", acm)
    sel = [(d, s) for d in dias for s in range(144) if usar[d, s] and e1[d, s]]
    nub = np.array([(acm[d, s] >= 2) & (acm[d, s] <= 3) for d, s in sel])
    ss = np.array([s for _, s in sel])
    est = np.zeros((144, S.NPIX), bool)
    ncos = np.zeros(144, int)
    for s in range(144):
        dd = np.abs(ss - s) % 144
        dd = np.minimum(dd, 144 - dd)
        for w in B.COSTUMBRE_VENT:
            m = dd <= w
            if m.sum() >= B.MIN_COSTUMBRE:
                est[s] = nub[m].mean(0) >= B.COSTUMBRE
                ncos[s] = int(m.sum())
                break
    return est, ncos, sel


def main():
    out = {}
    CL = B.clases()
    con = [d for d in range(B.ND) if (CL[d] != "").any()]
    out["dias_del_arreglo_de_clases"] = [B.fecha(0), B.fecha(B.ND - 1), B.ND]
    out["dias_con_alguna_clase"] = len(con)
    out["dias_con_clase"] = [B.fecha(d) for d in con]
    out["dias_sin_clase"] = [B.fecha(d) for d in range(B.ND) if d not in con]
    out["conteo_clases"] = {c: int((CL == c).sum()) for c in ("P", "N", "otro")}
    out["P_primer_y_ultimo_dia"] = [B.fecha(min(d for d in range(B.ND) if (CL[d] == "P").any())),
                                    B.fecha(max(d for d in range(B.ND) if (CL[d] == "P").any()))]
    print("clases: de", out["dias_del_arreglo_de_clases"], "con clase", len(con), "días; sin clase",
          len(out["dias_sin_clase"]), "días")
    print("días con clase:", out["dias_con_clase"][0], "a", out["dias_con_clase"][-1])
    print("días sin clase:", out["dias_sin_clase"][0], "a", out["dias_sin_clase"][-1], "(no contiguos:",
          [x for x in out["dias_sin_clase"] if x > "2026-10-19"], ")")
    # 2. rehacer el congelado
    _, acm26, _ = B.cargar_dev()
    NUL = CL[:B.NDEV] == "N"
    DIASR = [d for d in range(B.NDEV) if (CL[d] != "").any()]
    est, ncos, sel = costumbre(acm26, NUL, DIASR)
    cong = np.load(ESTAT)
    h1, h2 = hashlib.sha256(est.tobytes()).hexdigest(), hashlib.sha256(cong.tobytes()).hexdigest()
    dsel = sorted({d for d, _ in sel})
    out["rehecho_igual_al_congelado"] = bool(h1 == h2 and np.array_equal(est, cong))
    out["sha_rehecho"], out["sha_congelado"] = h1[:16], h2[:16]
    out["dias_de_la_referencia_DIASR"] = len(DIASR)
    out["dias_que_aportan_cuadros"] = [len(dsel), B.fecha(dsel[0]), B.fecha(dsel[-1])]
    out["cuadros_N_despejados_usados"] = len(sel)
    out["cuadros_por_hora_min_max"] = [int(ncos.min()), int(ncos.max())]
    out["pixeles_hora_de_costumbre"] = int(est.sum())
    print("rehecho == congelado:", out["rehecho_igual_al_congelado"], h1[:16], h2[:16])
    print("días de referencia (con clase, dentro de 21-09 a 21-11):", len(DIASR), "; aportan cuadros:", out["dias_que_aportan_cuadros"],
          "; cuadros N despejados:", len(sel), "; por hora mín/máx:", out["cuadros_por_hora_min_max"],
          "; píxeles-hora:", out["pixeles_hora_de_costumbre"])
    # 3. informativo: con los 62 días y todos los cuadros despejados (sin clase de VOLCAT)
    hay = (acm26 != 255).any(2)
    est62, ncos62, sel62 = costumbre(acm26, hay, list(range(B.NDEV)))
    dif = est62 != cong
    ap = np.zeros(S.NPIX, bool)
    ap[M.AP] = True
    out["alternativa_62_dias_todos_los_despejados"] = {
        "cuadros": len(sel62), "dias": len({d for d, _ in sel62}), "pixeles_hora_de_costumbre": int(est62.sum()),
        "pixeles_hora_que_cambian": int(dif.sum()), "de": int(dif.size),
        "en_el_anillo_cambian": int(dif[:, ap].sum()), "anillo_pixeles_hora": int(dif[:, ap].size),
        "congelado_en_anillo": int(cong[:, ap].sum()), "alternativa_en_anillo": int(est62[:, ap].sum())}
    print("alternativa con los 62 días:", out["alternativa_62_dias_todos_los_despejados"])
    json.dump(out, open(os.path.join(AQUI, "..", "V301_salidas", "v208_estat.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
