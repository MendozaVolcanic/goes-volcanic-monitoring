"""β-ratios de composición (Pavolonis 2010) — confirmación INDICATIVA de que la
pluma es **silicato (ceniza)** y no hielo/agua, complementaria a la detección BTD.

Por qué (geología → pipeline): el BTD 11−12 detecta la "absorción inversa" de la
ceniza, pero es sensible a la temperatura de superficie, el vapor de agua y la
emisividad del suelo. El β-ratio (Pavolonis 2010, Ec. 3) convierte las radiancias
a **emisividad efectiva** y su razón depende **solo de la microfísica** de la nube
→ discrimina composición (ceniza vs hielo vs agua) con mucha más robustez,
especialmente en nubes ópticamente delgadas.

    β(λ1, λ2) = ln[1 − ε(λ1)] / ln[1 − ε(λ2)]        (11 µm en el denominador)
    ε(λ)      = [R_obs(λ) − R_clr(λ)] / [B_λ(T_ref) − R_clr(λ)]

**Alcance honesto (lo que SÍ y NO es):** implementamos el modo **β_tropo** del
paper — ``T_ref`` = temperatura de la **tropopausa** (la referencia "sin
información de tope" que Pavolonis usa) — con nuestra **BT de cielo claro de la
escena como proxy de R_clr** (simplificación: el paper usa un RTM clear-sky
Hannon 1996 + emisividad SeeBor, que NO tenemos — misma brecha RTM que Fase 4).
La clasificación es por **cercanía a los 3 puntos ancla VERIFICADOS de la Tabla 2**
de Pavolonis 2010 (no umbrales inventados; Part I no publica cortes operacionales,
eso es Part II). Por eso es **INDICATIVO** y confirma composición, NO reemplaza la
detección `detect_ash_enhanced`. No separa ceniza de polvo (el paper lo advierte).
"""

from __future__ import annotations

from typing import Optional

import numpy as np

from src.process.brightness_temp import planck_rad_from_bt

# Puntos ancla β VERIFICADOS de la Tabla 2 de Pavolonis (2010) — efectivos por
# composición (β(8.5,11), β(12,11)). Son representativos, NO límites de corte.
BETA_ANCHORS = {
    "ceniza": {"b85_11": 0.705, "b12_11": 0.564},   # andesita, r_eff 2 µm
    "hielo":  {"b85_11": 0.836, "b12_11": 1.07},    # placa, r_eff 20 µm
    "agua":   {"b85_11": 0.981, "b12_11": 1.21},    # r_eff 10 µm
}
EPS_FLOOR = 1e-4
EPS_CEIL = 1.0 - 1e-6


def cloud_emissivity(bt_obs, t_ref_k, bt_clr, coef):
    """Emisividad efectiva ε(λ) (Pavolonis 2010, Ec. 2, modo β_tropo simplificado):

        ε = (R_obs − R_clr) / (B_λ(T_ref) − R_clr)

    ``bt_obs``/``bt_clr`` = BT observada / de cielo claro en la banda λ (K);
    ``t_ref_k`` = temperatura de referencia (tropopausa); ``coef`` = (fk1,fk2,bc1,
    bc2) de la banda. Devuelve ε recortada a (0,1). Función PURA, vectorizada.
    """
    R_obs = planck_rad_from_bt(np.asarray(bt_obs, dtype="float64"), *coef)
    R_clr = planck_rad_from_bt(np.asarray(bt_clr, dtype="float64"), *coef)
    B_ref = planck_rad_from_bt(np.asarray(t_ref_k, dtype="float64"), *coef)
    denom = B_ref - R_clr
    with np.errstate(divide="ignore", invalid="ignore"):
        eps = np.where(np.abs(denom) > 1e-12, (R_obs - R_clr) / denom, np.nan)
    return np.clip(eps, EPS_FLOOR, EPS_CEIL)


def beta_ratio(eps_num, eps_den):
    """β = ln(1 − ε_num) / ln(1 − ε_den) (Pavolonis 2010, Ec. 3). PURA."""
    eps_num = np.clip(np.asarray(eps_num, dtype="float64"), EPS_FLOOR, EPS_CEIL)
    eps_den = np.clip(np.asarray(eps_den, dtype="float64"), EPS_FLOOR, EPS_CEIL)
    with np.errstate(divide="ignore", invalid="ignore"):
        num = np.log(1.0 - eps_num)
        den = np.log(1.0 - eps_den)
        return np.where(np.abs(den) > 1e-12, num / den, np.nan)


def classify_composition(b12_11, b85_11) -> Optional[dict]:
    """Clasifica un par (β(12,11), β(8.5,11)) por **cercanía euclídea** al ancla
    más próximo de la Tabla 2 (ceniza/hielo/agua). Devuelve
    ``{"label", "distance", "is_ash"}`` o None si algún β es NaN. PURA.
    """
    if b12_11 is None or b85_11 is None or not (np.isfinite(b12_11)
                                                and np.isfinite(b85_11)):
        return None
    best, best_d = None, np.inf
    for label, a in BETA_ANCHORS.items():
        d = float(np.hypot(b12_11 - a["b12_11"], b85_11 - a["b85_11"]))
        if d < best_d:
            best, best_d = label, d
    return {"label": best, "distance": round(best_d, 3), "is_ash": best == "ceniza"}


def beta_composition(bt85, bt11, bt12, t_tropo_k, clr85, clr11, clr12,
                     coef85, coef11, coef12, ash_mask=None) -> Optional[dict]:
    """β-ratios medianos sobre los píxeles de ceniza + clasificación de composición.

    ``bt85/bt11/bt12`` arrays de BT (K); ``clr*`` = BT de cielo claro por banda;
    ``t_tropo_k`` = temperatura de la tropopausa; ``coef*`` = coeficientes Planck;
    ``ash_mask`` = dónde promediar (default: donde las 3 BT son finitas).

    Devuelve ``{"beta_12_11", "beta_85_11", "composition", "is_ash", "n_px"}`` o
    None si no hay píxeles. Usa las MEDIANAS (robustas) sobre la pluma. PURA.
    """
    bt85 = np.asarray(bt85, dtype="float64")
    bt11 = np.asarray(bt11, dtype="float64")
    bt12 = np.asarray(bt12, dtype="float64")
    if ash_mask is None:
        ash_mask = np.isfinite(bt85) & np.isfinite(bt11) & np.isfinite(bt12)
    ash_mask = np.asarray(ash_mask, dtype=bool) & np.isfinite(bt85) & \
        np.isfinite(bt11) & np.isfinite(bt12)
    if int(ash_mask.sum()) == 0:
        return None
    e11 = cloud_emissivity(bt11[ash_mask], t_tropo_k, clr11, coef11)
    e12 = cloud_emissivity(bt12[ash_mask], t_tropo_k, clr12, coef12)
    e85 = cloud_emissivity(bt85[ash_mask], t_tropo_k, clr85, coef85)
    b12_11 = beta_ratio(e12, e11)
    b85_11 = beta_ratio(e85, e11)
    b12_med = float(np.nanmedian(b12_11)) if np.isfinite(b12_11).any() else None
    b85_med = float(np.nanmedian(b85_11)) if np.isfinite(b85_11).any() else None
    comp = classify_composition(b12_med, b85_med)
    return {
        "beta_12_11": (round(b12_med, 3) if b12_med is not None else None),
        "beta_85_11": (round(b85_med, 3) if b85_med is not None else None),
        "composition": (comp["label"] if comp else None),
        "is_ash": (comp["is_ash"] if comp else None),
        "n_px": int(ash_mask.sum()),
    }
