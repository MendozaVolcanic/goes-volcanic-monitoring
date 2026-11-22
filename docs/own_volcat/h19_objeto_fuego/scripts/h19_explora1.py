"""H19, exploracion en el BLOQUE DE ELECCION (17:16 a 20:16): conjuntos y candidatas de identidad.
Uso: python -I h19_explora1.py REF [hora ...]   (por defecto, el bloque de eleccion)
Se niega a correr sobre cuadros de validacion salvo con --validacion (solo tras congelar la regla)."""
import sys
import os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from h19_io import ruta, leer, PIX, OBJ, DB, ELECCION, VALIDACION

args = [a for a in sys.argv[1:] if not a.startswith("--")]
ref = args[0]
horas = args[1:] or ELECCION
if any(h in VALIDACION for h in horas) and "--validacion" not in sys.argv:
    sys.exit("cuadro de validacion: no se abre antes de congelar la regla")


def mascara_lista(O, pre, sel):
    """Imagen booleana con los pixeles de los objetos seleccionados (indices 1-based, X=columna, Y=linea)."""
    size = O[pre + "Object_Size"].astype(int)
    fin = np.cumsum(size)
    ini = fin - size
    x = O[pre + "Object_X_Index"].astype(int) - 1
    y = O[pre + "Object_Y_Index"].astype(int) - 1
    m = np.zeros((601, 601), bool)
    ido = np.full((601, 601), -1, int)
    for k in range(len(size)):
        ido[y[ini[k]:fin[k]], x[ini[k]:fin[k]]] = k
        if sel[k]:
            m[y[ini[k]:fin[k]], x[ini[k]:fin[k]]] = True
    return m, ido


def jac(a, b):
    u = (a | b).sum()
    return (a & b).sum() / u if u else float("nan")


def igual(a, b, m, tol=0.01):
    ok = m & np.isfinite(a) & np.isfinite(b)
    n = m.sum()
    return ((np.abs(a - b) <= tol) & ok).sum() / n if n else float("nan")


for h in horas:
    L2 = leer(ruta(ref, "L2", h))
    S1 = leer(ruta(ref, "L2S1", h), ["vcat_vcbdet_9_13_ashprop_ash_probability",
                                      "vcat_vcbdet_9_13_ashprop_Ice_Object_Mask",
                                      "vcat_vcbdet_9_13_ashprop_object_id"])
    D1 = leer(ruta(ref, "DIAGS1", h), [PIX + "Ash_Object_Mask", PIX + "cloud_emissivity_ch14_tot"])
    A = leer(ruta(ref, "ASHOBJ", h), escalar=False)
    I = leer(ruta(ref, "ICEOBJ", h), escalar=False)
    P = L2[PIX + "ash_probability"]
    Ps = L2[PIX + "ash_probability_subset"]
    Pir = L2[PIX + "ash_probability_IR"]
    Psw = L2[PIX + "ash_probability_SW_IR"]
    Pvcb = S1["vcat_vcbdet_9_13_ashprop_ash_probability"]
    ag = L2["Ash_Group_Id_2d"] > 0
    ig = L2["Ice_Group_Id_2d"] > 0
    V = np.isfinite(P)
    Vs = np.isfinite(Ps)
    mA, idA = mascara_lista(A, "ASHOBJ_", A["Mask" + DB] > 0)
    mI, idI = mascara_lista(I, "ICEOBJ_", I["Mask" + DB] > 0)
    allA = idA >= 0
    allI = idI >= 0
    aom = D1[PIX + "Ash_Object_Mask"]
    iom = S1["vcat_vcbdet_9_13_ashprop_Ice_Object_Mask"]
    print("=== %s  V=%d Vs=%d ag=%d ig=%d ag&ig=%d ag|ig=%d  objA sel=%d/%d pix=%d  objI sel=%d/%d pix=%d" % (
        h, V.sum(), Vs.sum(), ag.sum(), ig.sum(), (ag & ig).sum(), (ag | ig).sum(),
        (A["Mask" + DB] > 0).sum(), len(A["Mask" + DB]), mA.sum(),
        (I["Mask" + DB] > 0).sum(), len(I["Mask" + DB]), mI.sum()))
    print("  Jaccard: V~ag|ig %.4f  V~ig %.4f  V~ag %.4f  Vs~V %.4f  ag~listaA %.4f  ig~listaI %.4f  ag~(listaA|listaI) %.4f" % (
        jac(V, ag | ig), jac(V, ig), jac(V, ag), jac(Vs, V), jac(ag, mA), jac(ig, mI), jac(ag, mA | mI)))
    print("  ag dentro de: listaA %.3f, todosA %.3f, listaI %.3f, todosI %.3f ; Ash_Object_Mask valores en ag: %s ; Ice_Object_Mask en ig: %s" % (
        (ag & mA).sum() / max(ag.sum(), 1), (ag & allA).sum() / max(ag.sum(), 1),
        (ag & mI).sum() / max(ag.sum(), 1), (ag & allI).sum() / max(ag.sum(), 1),
        dict(zip(*[x.tolist() for x in np.unique(aom[ag], return_counts=True)])),
        dict(zip(*[x.tolist() for x in np.unique(iom[ig], return_counts=True)]))))
    for nom, m in [("V", V), ("V&ag", V & ag), ("V&~ag", V & ~ag), ("V&P>=.5", V & (P >= 0.5))]:
        if m.sum() == 0:
            continue
        print("  [%s n=%d] P=subset %.3f  P=IR %.3f  P=SWIR %.3f  P=max(IR,SWIR) %.3f  P=Pvcb %.3f | subset=IR %.3f subset=SWIR %.3f subset=max %.3f subset=Pvcb %.3f | alto: P %.3f sub %.3f IR %.3f SW %.3f vcb %.3f" % (
            nom, m.sum(), igual(P, Ps, m), igual(P, Pir, m), igual(P, Psw, m), igual(P, np.fmax(Pir, Psw), m),
            igual(P, Pvcb, m), igual(Ps, Pir, m), igual(Ps, Psw, m), igual(Ps, np.fmax(Pir, Psw), m), igual(Ps, Pvcb, m),
            (P[m] >= .5).mean(), (Ps[m] >= .5).mean(), (Pir[m] >= .5).mean(), (Psw[m] >= .5).mean(),
            (np.nan_to_num(Pvcb[m], nan=-1) >= .5).mean()))
