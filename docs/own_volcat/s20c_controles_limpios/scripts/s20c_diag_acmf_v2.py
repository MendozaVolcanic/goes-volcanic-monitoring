r"""S20c: diagnostico del ensayo en seco del diseno 2 (solo ACMF, regla E1; no lee BT ni BTD).
Por positivo: dias limpios despejados en s-1..s+1 (linea base) y cuadros/dias placebo despejados a +-30 min.
Y la fraccion despejada E1 por hora UTC en cada pozo, para ver si el cuello es la hora del dia."""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.argv = ["x"]
import s20c_medir as S
import h24_medir as H
r14, r15, acm, co14, co15 = H.cargar()
claro = H.despejada("chillan", acm)
QQ, _ = S.cuadros("principal")
for p in S.PRUEBAS:
    nb, npf, npd, cx = [], [], [], []
    for q in QQ[p]:
        s = q["s"]
        nb.append(len({d for d in S.LIMPIO for ss in (s-1, s, s+1) if 0 <= ss < 144 and claro[d, ss]}))
        fr = [(j, ss) for j in S.PLACEBO for ss in range(s-3, s+4) if 0 <= ss < 144 and claro[j, ss]]
        npf.append(len(fr)); npd.append(len({j for j, _ in fr})); cx.append(claro[q["D"], s])
    nb, npf, npd = map(np.array, (nb, npf, npd))
    print(f"{p:8s} n {len(nb)} | dias base med {np.median(nb):.0f} (>=3: {np.mean(nb>=3):.2f}) | placebo cuadros med {np.median(npf):.0f}, dias med {np.median(npd):.0f} (ref ok: {np.mean((npf>=3)&(npd>=2)):.2f}) | pos claro {np.mean(cx):.2f}")
horas = np.arange(144) // 6
for nombre, dd in (("limpio", S.LIMPIO), ("placebo", S.PLACEBO), ("positivos", sorted({q['D'] for q in QQ['H11_H12'] + QQ['paso2']}))):
    f = claro[dd].mean(0)
    print(nombre, " ".join(f"{h:02d}:{f[horas==h].mean():.2f}" for h in range(24)))
# sin exigir 80 %: fraccion media de terreno bajo despejado
la, lo, h = H.SITIOS["chillan"]
d = H.hav(H.LAT, H.LON, la - 0.93 * h / 1000.0 / 111.2, lo)
bajo = np.where((d >= 10.0) & (d <= 30.0) & (H.ZDEM < 1300.0))[0]
fr = (acm[:, :, bajo] <= 1).mean(2)
for nombre, dd in (("limpio", S.LIMPIO), ("placebo", S.PLACEBO)):
    print(nombre, "fraccion despejada media 15-21 UTC:", round(float(fr[dd][:, 90:132].mean()), 2), "| pixeles terreno bajo:", len(bajo))
