"""H19, POST HOC (no decide): fase sin nube convectiva (22:16 a 23:31). Relacion entre la P publicada,
subset, IR y SW_IR en los pixeles de P alta, y banderas de historia. Uso: python h19_posthoc2.py NPZ_DIR --validacion"""
import sys
import os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from h19_comun import cargar, f, PIX, OBJ, TRK, VALIDACION, guardia
import h19_vref as VR

np.set_printoptions(linewidth=220, suppress=True, precision=3)
npz = sys.argv[1]
guardia(VALIDACION)


def cuenta(a):
    u, c = np.unique(a, return_counts=True)
    return dict(zip(u.tolist(), c.tolist()))


for h in VALIDACION[7:]:
    d = cargar(npz, h)
    P = f(d, PIX + "ash_probability"); S = f(d, PIX + "ash_probability_subset")
    IR = f(d, PIX + "ash_probability_IR"); SW = f(d, PIX + "ash_probability_SW_IR")
    V = np.isfinite(P); hi = V & (P >= .5); bajo = V & ~hi
    dif = V & (np.abs(P - S) > 0.01)
    print("%s V=%d altos=%d  P!=subset %d (P>subset %d)  P==IR %d  P==SW %d  P==max(IR,SW,subset) %d" % (
        h, V.sum(), hi.sum(), dif.sum(), (dif & (P > S)).sum(), (V & (np.abs(P - IR) <= 1e-6)).sum(),
        (V & (np.abs(P - SW) <= 1e-6)).sum(), (V & (np.abs(P - np.fmax(np.fmax(IR, SW), S)) <= 1e-6)).sum()))
    if hi.sum():
        lp = VR.logit(P)[hi]
        print("   altos: logit(P)-logit(IR)", np.percentile(lp - VR.logit(IR)[hi], [0, 25, 50, 75, 100]),
              " logit(P)-logit(subset)", np.percentile(lp - VR.logit(S)[hi], [0, 25, 50, 75, 100]))
        print("   valores de P distintos %d ; objetos %d ; History_Flag_Det_Out altos %s bajos %s ; Robust_Pixel_Flag altos %s bajos %s" % (
            len(np.unique(np.round(P[hi], 4))), len(np.unique(d["idA"][hi])),
            cuenta(d[OBJ + "History_Flag_Det_Out"][hi]), cuenta(d[OBJ + "History_Flag_Det_Out"][bajo]),
            cuenta(d[OBJ + "Robust_Pixel_Flag"][hi]), cuenta(d[OBJ + "Robust_Pixel_Flag"][bajo])))
        print("   History_Flag_Det_In altos %s bajos %s ; tendencia BTD(11-12) altos med %.2f bajos med %.2f ; IR previa altos med %.3g bajos med %.3g" % (
            cuenta(d[OBJ + "History_Flag_Det_In"][hi]), cuenta(d[OBJ + "History_Flag_Det_In"][bajo]),
            np.nanmedian(f(d, TRK + "Btd1112_Time_Diff")[hi]), np.nanmedian(f(d, TRK + "Btd1112_Time_Diff")[bajo]),
            np.nanmedian(f(d, TRK + "ash_probability_IR_prev")[hi]), np.nanmedian(f(d, TRK + "ash_probability_IR_prev")[bajo])))
