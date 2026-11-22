r"""H18 etapa 1, lectura: normalización y marginales de las tablas _DAY_ de la LUT de píxel de VOLCAT (ABI).

Lee D:\goes_cache\lut_h15\lut_pixel.npz (exportado por lut_h15/scripts/lut_exportar.py, fuera del repo).
Escribe sólo números derivados (sumas y marginales), nunca la tabla. Ejes en orden numpy (inverso del dblarr IDL):
NRAT (13: 0 a 1,2 cada 0,1), beta1112 (42), eps (6), scatang (2: 0-90, 90-180), cos_satzen (1).
"""
import sys
import numpy as np

sys.stdout.reconfigure(encoding="utf-8")
z = np.load(r"D:\goes_cache\lut_h15\lut_pixel.npz")
EPS = ["0,01-0,03", "0,03-0,10", "0,10-0,20", "0,20-0,50", "0,50-0,90", "0,90-1,00"]
NR = [f"{0.1*i:.1f}" for i in range(13)]

def tab(base, clase, sup):
    a = z[f"{base}_{clase}_{sup}_PIX"]
    return a.reshape(a.shape[:-1])

print("# Marginal de NRAT por clase, tierra (BETA1112_TOT_NRAT_DAY), por bin de εtot y de ángulo de dispersión")
for lrc in ("NRAT", "NRAT_LRC"):
    A = tab(f"BETA1112_TOT_{lrc}_DAY", "ASH", "LAND"); C = tab(f"BETA1112_TOT_{lrc}_DAY", "CLD", "LAND")
    for s in range(2):
        print(f"\n## {lrc}, ángulo de dispersión {'0-90' if s == 0 else '90-180'}°")
        print("εtot | " + " ".join(f"{x:>5}" for x in NR) + " | clase")
        for e in range(6):
            ma = A[:, :, e, s].sum(axis=1); mc = C[:, :, e, s].sum(axis=1)
            print(f"{EPS[e]} | " + " ".join(f"{v/ma.sum():5.2f}" for v in ma) + f" | ceniza (masa {ma.sum():.3f})")
            print(f"{EPS[e]} | " + " ".join(f"{v/mc.sum():5.2f}" for v in mc) + f" | nube   (masa {mc.sum():.3f})")
print("\n# εtot x ρ(0,65) (EMISS14_TOT_VREF_DAY), tierra, razón ceniza/nube por bin (ρ en %, 0 a 110 cada 10)")
A = tab("EMISS14_TOT_VREF_DAY", "ASH", "LAND"); C = tab("EMISS14_TOT_VREF_DAY", "CLD", "LAND")
for s in range(2):
    print(f"## ángulo {'0-90' if s == 0 else '90-180'}°")
    for e in range(6):
        print(f"{EPS[e]} | " + " ".join(f"{A[r, e, s]/C[r, e, s]:8.3g}" for r in range(11)))
print("\n# Razón ceniza/nube en BETA1112_TOT_NRAT_DAY tierra, εtot 0,10-0,20 (tramo de Chillán), ángulo 90-180°")
A = tab("BETA1112_TOT_NRAT_DAY", "ASH", "LAND"); C = tab("BETA1112_TOT_NRAT_DAY", "CLD", "LAND")
for bi, bl in ((16, "β 0,70-0,75"), (18, "β 0,80-0,85"), (21, "β 0,95-1,00")):
    print(bl + " | " + " ".join(f"{A[n, bi, 2, 1]/C[n, bi, 2, 1]:8.3g}" for n in range(13)))
