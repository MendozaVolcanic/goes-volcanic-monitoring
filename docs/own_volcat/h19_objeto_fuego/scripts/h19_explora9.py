"""H19, exploracion en el BLOQUE DE ELECCION: afinar las reglas antes de congelar.
(a) codigo 5 de Ash_Object_Mask dentro del grupo convectivo; (b) regla de historia para el objeto convectivo;
(c) regla de contacto para objetos de ceniza; (d) variantes de la regla de pixel. Uso: python h19_explora9.py NPZ_DIR"""
import sys
import os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from h19_comun import cargar, f, PIX, TRK, ELECCION, guardia
import h19_reglas as R

npz = sys.argv[1]
guardia(ELECCION)
prev_truth = None
tot = {}
for h in ELECCION:
    d = cargar(npz, h)
    P = f(d, PIX + "ash_probability"); S = f(d, PIX + "ash_probability_subset")
    eps = f(d, PIX + "cloud_emissivity_ch14_tot"); r2 = f(d, "p__channel_2_reflectance")
    bop = f(d, PIX + "cloud_beta_1112_opaque")
    ag = d["p__Ash_Group_Id_2d"] > 0; ig = d["p__Ice_Group_Id_2d"] > 0
    aom = d[PIX + "Ash_Object_Mask"]
    cia = np.nan_to_num(f(d, TRK + "count_in_ash"), nan=0)
    pig = d["prev__ig"] if "prev__ig" in d else np.zeros(len(ig), bool)
    c5 = aom == 5
    print("%s (a) en ig: codigo5 %d | count_in_ash>0 %d | ambos %d | prev_ig %d, codigo5 y prev_ig %d ; fuera de ig: codigo5 %d, count_in_ash>0 %d ; eps mediana c5 %.2f, c0 %.2f" % (
        h, (ig & c5).sum(), (ig & (cia > 0)).sum(), (ig & c5 & (cia > 0)).sum(), (ig & pig).sum(), (ig & c5 & pig).sum(),
        (~ig & c5).sum(), (~ig & (cia > 0)).sum(),
        np.nanmedian(eps[ig & c5]) if (ig & c5).any() else np.nan, np.nanmedian(eps[ig & (aom == 0)]) if (ig & (aom == 0)).any() else np.nan))
    # (b) historia con el grupo verdadero anterior
    selI = d["I__Mask"] > 0
    k, sol = R.elegir_vcb(d, prev_truth)
    print("   (b) objeto convectivo verdadero: %s ; predicho por historia: %d ; solapes>0: %d" % (np.nonzero(selI)[0].tolist(), k, (sol > 0).sum()))
    # (c) contacto con el objeto convectivo verdadero
    vimg = np.zeros((601, 601), bool)
    m = np.isin(d["idI"], np.nonzero(selI)[0]) & (d["idI"] >= 0)
    vimg[d["iy"][m], d["ix"][m]] = True
    toca = R.objetos_ceniza_que_tocan(d, vimg)
    selA = d["A__Mask"] > 0
    nA = np.bincount(d["idA"][d["idA"] >= 0], minlength=len(selA))
    print("   (c) objetos de ceniza: sel %d, tocan %d, TP %d FP %d FN %d ; pixeles FP %d FN %d" % (
        selA.sum(), toca.sum(), (toca & selA).sum(), (toca & ~selA).sum(), (~toca & selA).sum(), nA[toca & ~selA].sum(), nA[~toca & selA].sum()))
    # (d) reglas de pixel
    dia_tierra = (f(d, "p__pixel_solar_zenith_angle") < 85) & (d["p__pixel_surface_type"] != 0) & np.isfinite(P)
    alto = dia_tierra & (P >= .5)
    osc = R.oscuro_opaco(eps, r2)
    for nom, pr in (("nula SW_IR", f(d, PIX + "ash_probability_SW_IR") >= .5),
                    ("oscuro-opaco en V", osc), ("oscuro-opaco en ag", osc & ag),
                    ("oscuro-opaco y b1112op>1.05 en V", osc & (bop > R.B1112_OP_MIN)),
                    ("oscuro-opaco y b1112op>1.00 en V", osc & (bop > 1.0)),
                    ("identidad subset", S >= .5)):
        pr = pr & dia_tierra
        a = tot.setdefault(nom, [0, 0, 0, []])
        a[0] += alto.sum(); a[1] += (pr & alto).sum(); a[2] += pr.sum()
        if alto.sum() >= 20:
            a[3].append(((pr & alto).sum() / alto.sum(), (pr & alto).sum() / max(pr.sum(), 1)))
    gi = np.zeros((601, 601), bool); gi[d["iy"][ig], d["ix"][ig]] = True
    prev_truth = gi
print("\n(d) regla de pixel en eleccion: altos, sensibilidad, precision, cuadros con ambas >= 0.8")
for nom, a in tot.items():
    print("  %-34s altos %d  sens %.4f  prec %.4f  cuadros ok %d de %d" % (
        nom, a[0], a[1] / max(a[0], 1), a[1] / max(a[2], 1), sum(1 for s, p in a[3] if s >= .8 and p >= .8), len(a[3])))
