"""Diagnostico POSTERIOR (no decide): obs - modelo en C14 sobre los pixeles de huella en las escenas de control,
y altura de superficie GFS interpolada en esos pixeles. Explica por que la compuerta pasa en ambos grupos."""
import sys as _s, os as _o
_s.path.insert(0, _o.path.dirname(_o.path.abspath(__file__)))
import numpy as np, rt, comun_h3 as C, h3_metricas as H
d, z, dist = [], [], []
for caso, dp, dc in H.pares_ok():
    hv = C.HUE[C.k(dp)]; ys, xs = np.nonzero(hv)
    sc = C.load(dc); R = H.rclr_M(dc, ys, xs)
    d += list(sc[14][ys, xs] - rt.bt_de_rad(R[14], sc["co"][14]))
    g = H.gfs(dc); z += list(H._i2(g, g["zsfc"], C.LAT[ys, xs], C.LON[ys, xs]))
d = np.array(d); z = np.array(z)
print(f"Diagnostico posterior: obs-modelo C14 en pixeles de huella, escenas de control: n={len(d)} mediana {np.median(d):+.2f} K, p10 {np.percentile(d,10):+.2f}, p90 {np.percentile(d,90):+.2f}")
print(f"Altura de superficie GFS interpolada en esos pixeles: mediana {np.median(z):.0f} m, rango {z.min():.0f}-{z.max():.0f} m (cumbre real ~3200 m)")
