"""H3: arma la LUT de coeficientes de absorcion (rt.construir_lut). Rejilla de T por capa: rango de la capa en
el primer archivo GFS (28-10 23Z, caja de 10x10 nodos) +-25 K, 11 valores (paso ~5 K). Despues se verifica que
todas las escenas usadas caigan dentro (h3_metricas cuenta los recortes)."""
import sys as _s, os as _o
_s.path.insert(0, _o.path.dirname(_o.path.abspath(__file__)))  # modulos propios, explicito (python -I)
import os, time
import numpy as np
import rt

HERE = os.path.dirname(os.path.abspath(__file__))
g = np.load(os.path.join(HERE, "gfs", "gfs_2026102823.npz"))
p = g["p"]; T = g["T"].reshape(len(p), -1)
Tl = np.vstack([T[:1], T])                 # nivel 1050 = T(1000) (extrapolacion constante)
tmin = [min(Tl[l].min(), Tl[l + 1].min()) - 25 for l in range(rt.NL)]
tmax = [max(Tl[l].max(), Tl[l + 1].max()) + 25 for l in range(rt.NL)]
t0 = time.time()
out = rt.construir_lut(tmin, tmax, nT=11)
z = np.load(out)
print("LUT", out, z["kh"].shape, "lineas por molecula (H2O, CO2, O3, N2O, CH4):", z["nlin"], f"{time.time()-t0:.0f}s")
