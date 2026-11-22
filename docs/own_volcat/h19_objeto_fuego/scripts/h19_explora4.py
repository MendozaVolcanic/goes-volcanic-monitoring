"""H19, exploracion en el BLOQUE DE ELECCION: subset contra la tabla EMISS14_TOT_VREF_DAY sola y
sumada a otras probabilidades de pixel. Uso: python h19_explora4.py NPZ_DIR"""
import sys
import os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from h19_comun import cargar, f, PIX, ELECCION, guardia
import h19_vref as VR

npz = sys.argv[1]
guardia(ELECCION)
acc = {}
tab = {}
for h in ELECCION:
    d = cargar(npz, h)
    P = f(d, PIX + "ash_probability"); S = f(d, PIX + "ash_probability_subset")
    IR = f(d, PIX + "ash_probability_IR"); SW = f(d, PIX + "ash_probability_SW_IR")
    eps = f(d, PIX + "cloud_emissivity_ch14_tot"); r2 = f(d, "p__channel_2_reflectance")
    agua = d["p__pixel_surface_type"] == 0
    ag = d["p__Ash_Group_Id_2d"] > 0
    V = np.isfinite(S)
    for conv in "+-":
        th = VR.angulo(f(d, "p__pixel_solar_zenith_angle"), f(d, "p__pixel_satellite_zenith_angle"),
                       f(d, "p__pixel_relative_azimuth_angle"), conv)
        c, uso, ie, ir = VR.vref(eps, r2, agua, th)
        cands = {"sig(L0+vref)": VR.sig(VR.L0 + c),
                 "sig(logit(SW)+vref)": VR.sig(VR.logit(SW) + c),
                 "sig(logit(IR)+vref)": VR.sig(VR.logit(IR) + c),
                 "SW": SW, "IR": IR}
        for nom, q in cands.items():
            for zona, m in (("V", V), ("ag", V & ag), ("V sin ag", V & ~ag)):
                a = acc.setdefault((conv, nom, zona), [0, 0, 0, 0])
                a[0] += m.sum()
                a[1] += (np.abs(q - S)[m] <= 0.01).sum()
                a[2] += ((q >= .5) & (S >= .5) & m).sum()
                a[3] += ((q >= .5) != (S >= .5))[m].sum()
        if conv == "+":
            m = V & ag
            for a_, b_, s_, c_ in zip(ie[m], ir[m], S[m], c[m]):
                t = tab.setdefault((int(a_), int(b_)), [])
                t.append((s_, c_))
            sc = (th >= 90)
            print(h, "angulo de dispersion en V: min %.1f max %.1f ; frac >=90: %.3f" % (np.nanmin(th[V]), np.nanmax(th[V]), sc[V].mean()))
print("\nconv candidata zona n  frac|dif|<=0.01  ambos_altos  discrepan_en_alto")
for (conv, nom, zona), a in sorted(acc.items()):
    print("%s %-22s %-9s %6d  %.4f  %5d  %5d" % (conv, nom, zona, a[0], a[1] / max(a[0], 1), a[2], a[3]))
print("\nDentro del grupo de ceniza, por casilla (bin eps, bin ref2): n, mediana subset, frac subset>=.5, vref (log-odds)")
for k in sorted(tab):
    s = np.array([x[0] for x in tab[k]]); c = np.array([x[1] for x in tab[k]])
    print("  eps_bin %d ref2_bin %2d  n=%5d  med subset %.3g  frac alto %.3f  vref min %.2f max %.2f  sig(L0+vref) %.3g" % (
        k[0], k[1], len(s), np.median(s), (s >= .5).mean(), c.min(), c.max(), VR.sig(VR.L0 + np.median(c))))
