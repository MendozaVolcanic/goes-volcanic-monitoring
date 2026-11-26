r"""F2 (S28b): el rótulo "14-11 ALCANZADO" de S25a con el día como unidad.

Por qué: S25a §4 pide para el 14-11 >= 3 P alcanzados y p25 <= 0,01, con p25 por cuadro (Poisson binomial). Los 31 P
evaluados del 14-11 son UN día: con el día como unidad, el azar es la fracción de días de 2025 que alcanzarían al menos
lo mismo en esas horas, y con 62 días su p mínimo es 1/63 = 0,0159 > 0,01 (inalcanzable). Aquí se cuenta cuántos días
de 2025 (cada uno con su base y umbral sin sí mismo) alcanzan >= los observados en las horas de los P del 14-11.
Uso: python -I f2_dia14.py  (lee cubos_f2.npz)
"""
import os
import sys

import numpy as np

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import f2_bloques as FB  # noqa: E402

Z = np.load(os.path.join(FB.SAL, "cubos_f2.npz"))
CL = Z["CL"]
d14 = 54                                       # 21-09 + 54 días = 14-11
ev26, A26 = Z["ev26_z500"], Z["A26_z500"]
sl = np.flatnonzero((CL[d14] == "P") & ev26[d14])
T = int(A26[d14, sl].sum())
V25 = FB.tabla(Z["ev25_z500"], Z["A25_z500"])
dias = np.flatnonzero(np.isfinite(V25).any(1))
Xs = np.array([np.nansum(V25[d, sl]) for d in dias])
cub = np.array([np.isfinite(V25[d, sl]).mean() for d in dias])
print(f"14-11: P evaluados {len(sl)}, alcanzados {T}")
print(f"días de 2025 con algún evaluado: {len(dias)}; piso del p por día 1/(n+1) = {1 / (len(dias) + 1):.4f}")
print(f"días de 2025 con >= {T} alcanzados en esas horas: {(Xs >= T).sum()}; máximo {Xs.max():.0f}; "
      f"p por día = {(1 + (Xs >= T).sum()) / (1 + len(dias)):.4f}; cobertura media de las horas {cub.mean():.2f}")
print("distribución de alcanzados por día de 2025 (ordenada, top 8):", sorted(Xs.tolist())[-8:])
