r"""S20c: cobertura (solo ACMF) segun ventana horaria W de la linea base y del placebo (+-W cuadros) y el umbral FRAC
de la regla E1. Unidad valida = positivo despejado + base con >= 3 dias limpios despejados + placebo con >= 3 cuadros
de >= 2 dias. No lee BT ni BTD."""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.argv = ["x"]
import s20c_medir as S
import h24_medir as H
r14, r15, acm, co14, co15 = H.cargar()
la, lo, h = H.SITIOS["chillan"]
d = H.hav(H.LAT, H.LON, la - 0.93 * h / 1000.0 / 111.2, lo)
bajo = np.where((d >= 10.0) & (d <= 30.0) & (H.ZDEM < 1300.0))[0]
fr = (acm[:, :, bajo] <= 1).mean(2)
QQ, _ = S.cuadros("principal")
for FRAC in (0.8, 0.6):
    claro = fr >= FRAC
    for W in (1, 3, 6, 9):
        fila = []
        for p in S.PRUEBAS:
            ok = 0; dias = set()
            for q in QQ[p]:
                s = q["s"]
                if not claro[q["D"], s]:
                    continue
                rng = [ss for ss in range(s - W, s + W + 1) if 0 <= ss < 144]
                nb = len({dd for dd in S.LIMPIO for ss in rng if claro[dd, ss]})
                pf = [(j, ss) for j in S.PLACEBO for ss in rng if claro[j, ss]]
                if nb >= 3 and len(pf) >= 3 and len({j for j, _ in pf}) >= 2:
                    ok += 1; dias.add(q["D"])
            fila.append(f"{p}:{ok}/{len(QQ[p])}({len(dias)}d)")
        print(f"FRAC {FRAC} W +-{W*10:3d} min |", " ".join(fila))
