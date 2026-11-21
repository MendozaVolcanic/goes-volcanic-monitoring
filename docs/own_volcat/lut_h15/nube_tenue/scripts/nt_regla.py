r"""Nube tenue: el motor con las reglas candidatas (lo usan la exploración y la validación, idéntico en ambas).

Base: 7 tablas IR sin εtot × BTD, modo 'b', densidades conjuntas (variante posterior de la etapa 2).
Reglas (cada una se puede encender por separado):
  R1  tabla β(12/11) × β(7,3/11) sólo si ε(7,3) >= U73 (atributo MIN_73EMISS_TOT = 0,1). ε(7,3) se despeja de
      β(7,3/11) y εtot: ε73 = 1 − (1 − εtot)^β73. Si β73 falta, la tabla no entra.
      Por qué físico: con poca emisividad en la banda de vapor (7,3 µm) la nube casi no se ve ahí y β(7,3/11) es
      puro ruido; VOLCAT deja de usar ese predictor.
  R2  β multicapa ausente (no se identificó nube inferior): la tabla entra con el valor de relleno, que el eje
      recorta al PRIMER casillero (β < −0,05), en vez de omitirse.
  R3  tablas de β(8,5/11) sólo si se cumple la condición `cond85` (variantes en la exploración 8).
"""
import numpy as np

import nt_comun as N

LV = N.LV
J73 = N.NOMBRES.index("BETA1112_TOT_BETA7311_TOT_IR")
J85 = [N.NOMBRES.index("BETA1112_TOT_BETA8511_TOT_IR"), N.NOMBRES.index("BETA1112_OPAQUE_BETA8511_OPAQUE_IR")]
RELLENO = -999.0


def eps73(ent):
    with np.errstate(all="ignore"):
        return 1 - (1 - ent["eps"]) ** ent["b73"]


def contribuciones(ent, agua, r2=True):
    e = dict(ent)
    if r2:
        for k in ("b_low", "b_mid"):
            e[k] = np.where(np.isfinite(e[k]), e[k], RELLENO)
    return np.stack([N.contrib(e, agua, t) for t in N.SIETE], 1)


def logit_regla(C, ent, r1=True, u73=0.1, cond85=None):
    """C: contribuciones (npx, 7) de contribuciones(). cond85: None (8,5 siempre) o arreglo bool de uso."""
    L = N.L0 + C.sum(1)
    if r1:
        e73 = eps73(ent)
        usa73 = np.isfinite(e73) & (e73 >= u73)
        L = L - np.where(usa73, 0.0, C[:, J73])
    if cond85 is not None:
        for j in J85:
            L = L - np.where(cond85, 0.0, C[:, j])
    return L
