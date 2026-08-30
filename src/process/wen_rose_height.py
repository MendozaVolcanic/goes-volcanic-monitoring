# ════════════════════════════════════════════════════════════════════
# FICHA SDA · wen_rose_height.py  ·  SDA: Monitoreo Volcánico GOES-19 · ID: SDA-GOES-01
# Objetivo      : corregir la altura de pluma por semitransparencia (el número propio principal, INDICATIVO)
# Lógica        : con 2 canales (11/12 µm) se separa cuánto del brillo viene del suelo a través de la ceniza y cuánto del tope
# Modelo/método : inversión radiativa simple (grid-search del residuo), sin ML
# Datos entrada : BT GOES-19 C11/C14/C15 (+C16 opcional) + perfil GFS + BT de cielo claro de la escena — SIN datos personales
# Variables     : β (microfísica, banda 0.55-0.95 → incertidumbre), Ts (fondo cálido), umbrales de confianza
# Limitaciones  : sesgo IR −0.4..−0.8 km; banda fiable 3-12 km; NO mide gas/SO₂; banda ancha en ceniza fina (honesto)
# Refs/datos    : Wen & Rose 1994; Pavolonis 2010; Saint 2024; audit jul-2026 (F1/F2)
# Ficha completa: docs/FICHA_SDA_GOES.md
# ════════════════════════════════════════════════════════════════════
"""Altura del tope de pluma por **Wen & Rose 1994** — corrección de emisividad de
2 canales (11/12 µm) sobre el BT-matching (Fase 3b del VOLCAT propio).

Por qué (geología → pipeline): el BT-matching (Fase 3a) supone el tope **opaco**
(`Tc ≈ BT 11 µm`) y por eso **subestima** plumas semi-transparentes — el satélite
ve el suelo cálido *a través* de la ceniza fina, así que la BT observada es más
cálida que el tope real. Wen-Rose usa la diferencia espectral entre 11 y 12 µm
(la ceniza silicatada absorbe distinto: BTD 11−12 < 0) para **despejar
simultáneamente la temperatura del tope y la transparencia**, separando la
contribución del suelo. El resultado es un `Tc` más frío y correcto → altura más
alta. Es la física de VOLCAT/Pavolonis 2013 en versión reducida (sin optimal
estimation ni RTM).

Modelo (aproximación no-scattering, `ε = 1 − t`), por banda i ∈ {11≡C14, 12≡C15}:

    I_i = (1 − t_i)·B_i(Tc) + t_i·B_i(Ts)
    t12 = t11^β        (acople de canales; β = 0.9 silicato andesita-dacita)

donde `B_i` es la radiancia de Planck de la banda (coeficientes del NetCDF L1b) y
`Ts` la BT de fondo (cielo claro). Se despeja `Tc` y luego se mapea a altitud con
``gfs_profile.altitudes_from_bt`` (REUSADO de Fase 2). **Garantía:** `Tc ≤ BT11`
siempre → la altura Wen-Rose **≥** BT-matching; el Δ es la corrección.

INDICATIVO. VOLCAT/SSEC sigue siendo el primario cuantitativo. NO da altura a
plumas de gas/SO₂ (transparentes en 11 µm). Detalle en
``docs/own_volcat/FASE3B_WENROSE.md``.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional, Union

import numpy as np

# Reuso EXACTO de la conversión radiancia↔BT (Fase 3b mezcla radiancias) y del
# mapeo Teff→altitud robusto a inversiones (Fase 2) → producción y tests comparten.
from src.fetch.gfs_profile import altitudes_from_bt  # noqa: F401  (re-export + uso)
from src.process.brightness_temp import planck_rad_from_bt

logger = logging.getLogger(__name__)

BT85_BAND = 11             # 8.4 µm (máscara tri-espectral)
BT11_BAND = 14             # 11.2 µm (ventana, canal "4" de Wen-Rose)
BT12_BAND = 15             # 12.3 µm (canal "5" de Wen-Rose)
CO2_BAND = 16              # 13.3 µm (CO₂) — chequeo INDEPENDIENTE de semi-transp.
CO2_SEMITRANSP_MIN = 0.5   # BTD(11−13.3) ≥ esto ⇒ consistente con semitransp. (ver co2_verdict)
# El test CO₂ es DEGENERADO para topes bajos (audit jul-2026, verificado): una
# pluma OPACA a 4 km da BTD(11−13.3) ≈ +8..14 K (media columna de CO₂ queda
# encima, con aire frío) — indistinguible de una fina a 10 km (+10..15 K). El
# árbitro solo discrimina cuando el tope candidato es ALTO (poca columna de CO₂
# encima → opaca daría BTD chico). Gate por la cota BT-matching:
CO2_ARBITER_MIN_COTA_KM = 7.0
HETERO_WARN_K = 25.0       # spread (p90−p10) de cielo claro ≥ esto ⇒ fondo heterogéneo

# β = τ12/τ11 (acople t12 = t11^β) — la MISMA cantidad física que el β(12,11) de
# Pavolonis 2010 (verificado: sec θ cancela en el ratio). Procedencia REAL de los
# valores (fix F2, audit jul-2026 — la vieja cita "β=0.9, Wen-Rose Fig.1" era
# FANTASMA: ese paper no define β): Pavolonis 2010 Fig.3/Tabla 2, andesita
# r_eff 1-12 µm → β(12,11) ≈ 0.45 (1 µm) … 0.564 (2 µm) … ~1.0 (12 µm).
# Central 0.7 ≈ r_eff 4-5 µm (medio microfísico); el rango barrido cubre de
# ceniza fina distal a gruesa proximal. β NO se mide dentro del solver
# (circularidad verificada); el β medido por beta_ratios solo genera un flag.
BETA_SILICATE = 0.7        # β central (r_eff ~4-5 µm, andesita)
BETA_RANGE = (0.55, 0.95)  # fina distal … gruesa proximal → banda del tope
MIN_CLEAR_PX = 40          # mínimo de píxeles claros para estimar Ts de la escena
CLEAR_SKY_PCTL = 92        # percentil cálido = BT de superficie (cielo claro)
DELTA_WARN_KM = 5.0        # corrección Wen-Rose ≥ esto → flag (Ts/muestra sospechosos)
BAND_WIDE_KM = 3.0         # banda β ≥ esto → degrada la confianza
# Banda de altura donde el retrieval IR de 2 canales es fiable (Saint et al. 2024,
# JGR: fuera de 3-12 km el contraste tope-superficie o la relación T(z) hacen que
# la altura no discrimine bien). Fuera de la banda: degradar confianza + flag.
RELIABLE_BAND_KM = (3.0, 12.0)
# Detector de mal-condicionamiento: span de Tc cuyo residuo queda dentro de
# RES_TOL del mínimo. El span crece con la transparencia; el corte cae en
# t≈0.6 ⇄ τ≈0.5 — el régimen donde la literatura (Wen-Rose, Pavolonis) dice que
# el retrieval deja de ser confiable. Calibrado con forward-model sintético.
RES_TOL = 0.003            # residuo: Tc que ajustan "casi igual de bien" (transmisividad)
TC_SPAN_MAX = 60.0         # span de Tc dentro de RES_TOL ≥ esto ⇒ mal-condicionado (τ≲0.5)
# Piso de terreno: cuánto puede quedar el tope BAJO la cumbre antes de avisar.
# La tolerancia NO es cortesía: el retrieval IR tiene un sesgo conocido de
# −0.4..−0.8 km (subestima) y el perfil GFS tiene su propio error de altitud, así
# que un tope 300 m bajo el cráter es ruido esperable, no un absurdo físico.
SUMMIT_TOL_KM = 0.8


def below_summit_flag(top_km, summit_km=None, tol_km: float = SUMMIT_TOL_KM):
    """¿El tope reportado quedó **bajo la cumbre del propio volcán**?

    Por qué (geología antes que código): una pluma nace en el cráter, así que su
    tope no puede estar por debajo de la cumbre — es imposible, no improbable.
    Sin embargo nada en la cadena lo impide: ``altitudes_from_bt`` mapea la BT
    contra el perfil GFS **sobre el nivel del mar**, sin saber que abajo hay un
    edificio volcánico de 5 km. Con fondo frío (nieve, nube baja, noche de
    invierno en el altiplano) o con la máscara enganchada en cirros, el mapeo
    devuelve altitudes de aire troposférico bajo que en Láscar (cumbre 5592 m)
    llegaron a caer ~4 km bajo el cráter. Ese número no es "un poco malo": es
    señal de que la escena no es una pluma o de que el Ts está mal.

    **Marca, no clampea.** Un clamp a la cumbre convertiría un retrieval roto en
    un número plausible y silencioso — justo lo que el turno no puede detectar.
    Preferimos que el tope siga siendo el que el retrieval calculó y que el
    aviso viaje al lado.

    Args:
        top_km:    tope reportado (km sobre el nivel del mar). None → sin aviso.
        summit_km: cumbre del volcán (km s.n.m., ``Volcano.elevation/1000``).
                   **None ⇒ no se evalúa el piso** (comportamiento histórico).
        tol_km:    margen por el sesgo IR conocido (ver ``SUMMIT_TOL_KM``).

    Returns:
        str con el aviso, o None si no aplica / no hay dato. Función PURA.
    """
    if top_km is None or summit_km is None:
        return None
    if top_km >= summit_km - tol_km:
        return None
    return (f"tope bajo la cumbre: {top_km:.1f} km vs cráter {summit_km:.1f} km "
            f"(−{summit_km - top_km:.1f} km) — físicamente imposible para una "
            "pluma; revisá Ts/máscara antes de usar el número")


def in_reliable_band(top_km) -> bool:
    """¿El tope cae en la banda donde el retrieval IR de 2 canales es fiable
    (``RELIABLE_BAND_KM``, Saint et al. 2024)? None → tratado como fuera. PURA."""
    if top_km is None:
        return False
    return RELIABLE_BAND_KM[0] <= top_km <= RELIABLE_BAND_KM[1]


def wen_rose_confidence(mask_px: int, band_width_km, ts_is_clear_sky: bool,
                        top_km=None) -> str:
    """Confianza **INDICATIVA** del tope Wen-Rose. Nunca devuelve "alta": es un
    producto indicativo, el cuantitativo validado sigue siendo VOLCAT.

    Degrada por (a) pocos píxeles de ceniza → estadístico ruidoso; (b) banda de
    incertidumbre por β ancha → microfísica mal restringida; (c) Ts de fallback
    (GFS, no observado) → fondo cálido peor estimado; (d) tope **fuera de la banda
    fiable 3-12 km** (Saint et al. 2024) → la altura no discrimina bien.
    Función PURA.
    """
    if mask_px < 5:
        return "muy baja"
    score = 2
    if mask_px < 15:
        score -= 1
    if band_width_km is not None and band_width_km > BAND_WIDE_KM:
        score -= 1
    if not ts_is_clear_sky:
        score -= 1
    if top_km is not None and not in_reliable_band(top_km):
        score -= 1
    return "media" if score >= 2 else ("baja" if score == 1 else "muy baja")


def reliability_flags(top_km, co2_btd, near_tropopause: bool) -> list:
    """Flags de fiabilidad basados en la literatura (Saint 2024, Pavolonis 2020),
    sobre el tope ya calculado. Función PURA (fácil de unit-testear).

    - **Fuera de 3-12 km**: bajo 3 km el contraste tope-superficie es insuficiente;
      sobre ~12 km (cerca/encima de la tropopausa) el retrieval IR **subestima
      sistemáticamente** porque en la estratósfera T sube con z (Saint 2024).
    - **Régimen opaco + alto** (CO₂ dice pluma opaca y el tope toca la tropopausa):
      ceniza gruesa/ópticamente espesa (reff>10µm, típica recién eruptada) **borra
      la firma 11/12 µm** (Mie) → la altura es una **cota inferior**, puede
      subestimar plumas altas (Saint 2024, validado en Puyehue 2011).
    """
    flags = []
    if top_km is not None and top_km < RELIABLE_BAND_KM[0]:
        flags.append(f"tope < {RELIABLE_BAND_KM[0]:.0f} km: contraste tope-superficie "
                     "bajo, altura poco fiable (Saint 2024)")
    elif top_km is not None and top_km > RELIABLE_BAND_KM[1]:
        flags.append(f"tope > {RELIABLE_BAND_KM[1]:.0f} km: cerca/sobre la tropopausa, "
                     "posible subestimación sistemática (T sube en estratósfera)")
    if (near_tropopause and co2_btd is not None and co2_btd < CO2_SEMITRANSP_MIN):
        flags.append("régimen opaco+alto: ceniza gruesa/espesa puede borrar la firma "
                     "11/12 µm → tope es cota inferior, puede subestimar (Saint 2024)")
    return flags


# ── Solver puro (sin red) ───────────────────────────────────────────────────

def clear_sky_bt(bt11_window, ash_mask, percentile: float = CLEAR_SKY_PCTL,
                 min_clear: int = MIN_CLEAR_PX, ring_px: int = 6) -> Optional[float]:
    """BT de **cielo claro** de la escena = percentil cálido de los píxeles
    finitos **no-ceniza** en BT(11 µm).

    Es la "Ts" del modelo de Wen-Rose: la BT que el satélite ve sobre el suelo,
    ya en el marco radiométrico de ABI (atmósfera incluida). El percentil alto
    (no el máximo) descarta píxeles calientes espurios; excluir la ceniza evita
    contaminar con la propia pluma fría.

    **#3 Ts local** (mejora 2026-06-28): prioriza el **anillo de píxeles claros
    alrededor de la pluma** (dilatación de la máscara, ``ring_px``) en vez del
    percentil de TODA la ventana — el entorno inmediato representa mejor el fondo
    bajo la pluma que terrenos lejanos (clave en volcanes costeros / con gradiente
    de relieve, donde un Ts global mezcla mar y tierra). Cae al percentil global
    si el anillo no tiene suficientes píxeles. Devuelve None si tampoco el global
    alcanza ``min_clear`` (pluma llena el encuadre → fallback GFS). Función PURA.
    """
    bt = np.asarray(bt11_window, dtype="float64")
    ash = np.asarray(ash_mask, dtype=bool)
    finite = np.isfinite(bt)
    # Anillo local alrededor de la pluma (si hay ceniza y scipy disponible).
    if ash.any() and ring_px > 0:
        try:
            from scipy.ndimage import binary_dilation
            ring = binary_dilation(ash, iterations=ring_px) & ~ash & finite
            if int(ring.sum()) >= min_clear:
                return float(np.percentile(bt[ring], percentile))
        except Exception:
            pass
    clear = finite & ~ash
    if int(clear.sum()) < min_clear:
        return None
    return float(np.percentile(bt[clear], percentile))


def clear_sky_heterogeneity(bt11_window, ash_mask) -> Optional[float]:
    """Spread (p90−p10, K) de la BT de cielo claro de la ventana — indicador de
    **heterogeneidad del fondo**. Alto ⇒ terreno mixto (costa: mar+tierra, o
    gradiente de relieve fuerte) ⇒ un Ts escalar es poco confiable y la
    corrección Wen-Rose puede sesgarse. Devuelve None si no hay claros. PURA.
    """
    bt = np.asarray(bt11_window, dtype="float64")
    clear = np.isfinite(bt) & ~np.asarray(ash_mask, dtype=bool)
    if int(clear.sum()) < 10:
        return None
    vals = bt[clear]
    return float(np.percentile(vals, 90) - np.percentile(vals, 10))


def co2_semitransparency(bt11, bt133, ash_mask) -> Optional[float]:
    """Observable BTD(11−13.3 µm) sobre la pluma — insumo del árbitro CO₂.

    Por qué (geología → pipeline): el 13.3 µm cae en una banda de absorción de
    CO₂, así que su radiancia viene de **más arriba** en la atmósfera que la
    ventana de 11 µm. Sobre una pluma **semi-transparente**, el 11 µm ve más
    suelo cálido por debajo (ventana) que el 13.3 µm → ``BT(11)−BT(13.3) > 0``.

    **LÍMITE FÍSICO (audit jul-2026, verificado):** el observable es DEGENERADO
    para topes bajos — una pluma **opaca** cuyo tope queda debajo del pico de la
    función de peso del 13.3 µm también da BTD grande (+8..14 K a 4 km: media
    columna de CO₂ queda encima con aire frío). "Opaca ⇒ BTD≈0" solo vale con el
    tope cerca de la tropopausa. Por eso este valor NO se interpreta solo:
    :func:`co2_verdict` aplica el gate de altura antes de concluir nada.

    Devuelve la **mediana de BTD(11−13.3)** sobre los píxeles de ceniza (K), o
    None si no hay 13.3 µm o píxeles válidos. Función PURA.
    """
    if bt133 is None:
        return None
    bt11 = np.asarray(bt11, dtype="float64")
    bt133 = np.asarray(bt133, dtype="float64")
    m = (np.asarray(ash_mask, dtype=bool) & np.isfinite(bt11)
         & np.isfinite(bt133))
    if not m.any():
        return None
    return float(np.median(bt11[m] - bt133[m]))


def co2_verdict(co2_btd, cota_km) -> Optional[str]:
    """Veredicto del árbitro CO₂, honesto respecto de su degeneración física.

    - ``None``: sin dato (no se bajó C16 o sin píxeles).
    - ``"no_discrimina"``: la cota es BAJA (< ``CO2_ARBITER_MIN_COTA_KM``) → el
      BTD(11−13.3) no distingue "fina y alta" de "OPACA y baja" (ambas dan
      +8..15 K) — no se concluye nada en ningún sentido.
    - ``"consistente_semitransp"``: cota alta y BTD grande → CONSISTENTE con
      semitransparencia (no la *confirma*: sigue habiendo ambigüedad residual).
    - ``"opaca_alta"``: cota alta y BTD chico → pluma opaca con tope alto (el
      único caso donde el BTD chico es informativo).

    Función PURA (unit-testeable). (Fix F1, audit jul-2026.)
    """
    if co2_btd is None:
        return None
    if cota_km is None or cota_km < CO2_ARBITER_MIN_COTA_KM:
        return "no_discrimina"
    return ("consistente_semitransp" if co2_btd >= CO2_SEMITRANSP_MIN
            else "opaca_alta")


def solve_tc_grid(bt11, bt12, ts_k, coef11, coef12, beta: float = BETA_SILICATE,
                  tc_floor_k: float = 180.0, n_grid: int = 220):
    """Despeje Wen-Rose de la temperatura del tope `Tc` por píxel (vectorizado).

    Para cada píxel busca el `Tc ∈ [tc_floor, BT11]` que mejor satisface el
    acople de canales ``t12(Tc) = t11(Tc)^β``, donde
    ``t_i(Tc) = (I_i − B_i(Tc)) / (B_i(Ts) − B_i(Tc))`` es la transmisividad
    implícita. Se usa **búsqueda en grilla del mínimo residuo** (no bisección):
    es robusta a la tangencia del residuo en plumas finas (donde la señal de 2
    canales es débil y la solución, poco sensible) y no necesita bracketing.

    ``coef11``/``coef12`` = ``(fk1, fk2, bc1, bc2)`` de cada banda (del NetCDF).
    ``ts_k`` puede ser escalar (BT de cielo claro) o array.

    Devuelve ``(tc, solved, well_constrained)``:
      - ``tc``: temperatura del tope (K). En píxeles **no resueltos** cae al
        **supuesto opaco** ``Tc = BT11`` (= BT-matching); NaN donde la BT es NaN.
      - ``solved``: bool — True solo donde el píxel es candidato semitransparente
        (ceniza BTD<0 sobre fondo cálido Ts>BT11) y hubo solución física.
      - ``well_constrained``: bool — True donde el dato **restringe** el Tc (el
        residuo tiene mínimo agudo). En plumas muy finas (t≈1) el residuo queda
        casi plano → el Tc no está restringido → False (la corrección es ruido,
        el caller debe revertir esos píxeles a la cota). ⊆ ``solved``.
        **OJO — este criterio NO es autosuficiente y no puede usarse solo**
        (audit ago-2026, §3.3): mide el *ancho* del mínimo, no el *residual*.
        Un ajuste malo con mínimo angosto (p. ej. el despeje saturando en
        ``tc_floor_k``=180 K) sale marcado True. Lo que salva al sistema es
        :func:`_revert_unreliable`, 40 líneas más abajo: esas saturaciones
        clampean en la tropopausa y ahí ``reliable`` pasa a False, así que el
        tope vuelve a la cota conservadora. El hallazgo se **refutó como bug**
        porque un barrido β_true 0.45–1.00 × t11 0.15–0.9 no produjo ni un tope
        alto espurio marcado como confiable. Consecuencia práctica: **nunca
        consumir ``well_constrained`` sin pasar por ``_revert_unreliable``**, ni
        exportarlo fuera del módulo, o el guard deja de existir.
    Función PURA.
    """
    bt11 = np.asarray(bt11, dtype="float64")
    bt12 = np.asarray(bt12, dtype="float64")
    ts = np.asarray(ts_k, dtype="float64")

    # Radiancias: observadas (I) y de fondo/cielo-claro (Bs).
    I11 = planck_rad_from_bt(bt11, *coef11)
    I12 = planck_rad_from_bt(bt12, *coef12)
    Bs11 = planck_rad_from_bt(ts, *coef11)
    Bs12 = planck_rad_from_bt(ts, *coef12)

    finite = np.isfinite(bt11) & np.isfinite(bt12)
    btd = np.where(finite, bt11 - bt12, 0.0)
    # Candidato Wen-Rose: ceniza (absorción inversa BTD<0) sobre fondo MÁS CÁLIDO
    # que lo observado (sin contraste no hay nada que corregir).
    elig = finite & (ts > bt11 + 0.5) & (btd < 0.0)

    hi = np.where(finite, bt11, tc_floor_k + 1.0)        # límite opaco Tc=BT11

    # Grilla normalizada u∈[0,1] → Tc por píxel en [floor, BT11].
    u = np.linspace(0.0, 1.0, n_grid).reshape((n_grid,) + (1,) * bt11.ndim)
    Tc_grid = tc_floor_k + u * (hi - tc_floor_k)         # (n_grid, *shape)

    B11 = planck_rad_from_bt(Tc_grid, *coef11)
    B12 = planck_rad_from_bt(Tc_grid, *coef12)
    with np.errstate(divide="ignore", invalid="ignore"):
        t11 = (I11 - B11) / (Bs11 - B11)
        t12 = (I12 - B12) / (Bs12 - B12)
        t11c = np.clip(t11, 1e-9, 1.0)
        resid = np.abs(t12 - np.power(t11c, beta))
    # Descartar hipótesis con transmisividades fuera de rango físico [0,1].
    bad = ((~np.isfinite(resid)) | (t11 < -0.05) | (t11 > 1.05)
           | (t12 < -0.05) | (t12 > 1.20))
    resid = np.where(bad, np.inf, resid)

    idx = np.argmin(resid, axis=0)                       # mejor Tc por píxel
    Tc = np.take_along_axis(Tc_grid, idx[None], axis=0)[0]
    min_res = np.take_along_axis(resid, idx[None], axis=0)[0]

    # ¿Cuán BIEN restringe el dato el Tc? Span del intervalo de Tc cuyo residuo
    # queda dentro de RES_TOL del mínimo. Pluma muy fina (t≈1) → el acople β
    # apenas depende de Tc → residuo casi plano → span ancho → Tc no confiable.
    within = resid <= (min_res[None] + RES_TOL)
    tc_hi = np.where(within, Tc_grid, -np.inf).max(axis=0)
    tc_lo = np.where(within, Tc_grid, np.inf).min(axis=0)
    tc_span = tc_hi - tc_lo

    solved = elig & np.isfinite(min_res)
    well_constrained = solved & np.isfinite(tc_span) & (tc_span <= TC_SPAN_MAX)
    Tc = np.where(solved, Tc, hi)                        # fallback opaco = BT11
    Tc = np.where(finite, Tc, np.nan)
    return Tc, solved, well_constrained


# ── Orquestación (con red) ──────────────────────────────────────────────────

def _top_stats(field_km, valid, alt_m, trop, percentile=95):
    """Tope (percentil) + máx sobre los píxeles NO 'capped' en la tropopausa
    (cirros mal detectados / overshooting no deben fijar el tope). Misma semántica
    que bt_matching_height. Devuelve (top_km, top_max_km, n_capped, all_capped)."""
    capped = (valid & (alt_m >= trop["z_m"] - 1.0)) if trop else np.zeros_like(valid)
    n_capped = int(np.sum(capped))
    clean = valid & ~capped
    if int(clean.sum()) > 0:
        vals = field_km[clean]
        return (float(np.percentile(vals, percentile)), float(vals.max()),
                n_capped, False)
    trop_km = trop["z_m"] / 1000.0 if trop else None
    return (trop_km, trop_km, n_capped, True)


def _revert_unreliable(tc, bt11, well_constrained, profile, trop):
    """Revierte a la cota (BT11) los píxeles cuya corrección Wen-Rose NO es
    confiable, por DOS modos de falla:
      - **mal-condicionado**: el dato no restringe el Tc (``well_constrained``
        False; residuo plano en plumas finas);
      - **runaway**: la corrección saturó en la tropopausa (el despeje empujó el
        Tc al cap frío → altura implausible para una detección chica).
    Es la mejora #1 de honestidad: en vez de reportar un Tc frío espurio, esos
    píxeles vuelven a la cota (BT-matching), conservadora. Overshooting real es
    raro y, si lo hubiera, sería en pluma densa que ACHA/VOLCAT capturan.
    Devuelve ``(tc_reliable, reliable_mask)``. PURA.
    """
    alt = altitudes_from_bt(tc, profile)
    # RIESGO LATENTE (audit ago-2026, §3.2 — refutado HOY, no para siempre):
    # sin tropopausa el umbral pasa a +inf y el guard de runaway se apaga
    # ENTERO — sólo sobrevive el filtro de mal-condicionamiento, y una
    # corrección saturada se reportaría como tope confiable, sin flags.
    # Se refutó como bug porque el ÚNICO proveedor cableado es Open-Meteo
    # (scene.acquire_ash_scene) y su API no devuelve nulls: verificado sobre
    # Láscar, 72 h × 19 niveles, 0 nulls en T y Z, incluidos los nueve niveles
    # 400–70 hPa que harían falta para que `_tropopause` diera None. El modo de
    # falla realista (perfil caído entero) ya lo corta el guard "sin perfil GFS".
    # **El día que se cablee LVTP, GRIB o cualquier otro proveedor de perfil,
    # revisar ESTE guard ANTES de conectarlo**: un perfil con niveles altos
    # faltantes reabre el agujero.
    z_trop = trop["z_m"] if trop else np.inf
    reliable = (np.asarray(well_constrained, dtype=bool) & np.isfinite(alt)
                & (alt < z_trop - 1.0))
    return np.where(reliable, tc, bt11), reliable


def _wr_top_for_beta(bt11, bt12, ts_k, c11, c12, beta, mask, profile, trop,
                     percentile):
    """Tope p95 Wen-Rose para un β dado — para barrer el rango de microfísica y
    construir la banda de incertidumbre del tope. Revierte los píxeles no
    confiables a la cota (igual que el solve principal). Devuelve km o None."""
    tc, _, wc = solve_tc_grid(bt11, bt12, ts_k, c11, c12, beta=beta)
    tc, _ = _revert_unreliable(tc, bt11, wc, profile, trop)
    alt = altitudes_from_bt(tc, profile)
    valid = mask & np.isfinite(alt)
    field = np.where(valid, alt, np.nan) / 1000.0
    return _top_stats(field, valid, alt, trop, percentile)[0]


def wen_rose_top_height(
    dt: datetime,
    volcano: Union[str, object],
    radius_deg: float = 0.75,
    percentile: float = 95,
    beta: float = BETA_SILICATE,
    summit_km: Optional[float] = None,
) -> dict:
    """Altura del tope por Wen-Rose para un volcán en un instante.

    Pipeline: ventana geos desde C14 → baja C11/C14/C15 del mismo scan (con sus
    coeficientes Planck) → máscara de ceniza → Ts de cielo claro (fallback GFS
    skin-T) → despeje Tc (Wen-Rose) → mapea a altitud por el perfil GFS. Devuelve
    el tope Wen-Rose **y** el de BT-matching del MISMO scan (mismos píxeles) para
    cross-validación directa.

    Returns dict con ``status`` (ok/no_plume/no_data) y, si ok: ``top_km`` (p95
    Wen-Rose), ``top_bt_matching_km`` (p95 opaco), ``delta_km`` (corrección),
    ``ts_k``/``ts_source``, ``beta``, ``n_corrected`` (píxeles realmente
    corregidos), ``field_km`` (Wen-Rose) y ``field_bt_km``, además de
    ``mask_px``, ``so2_px/min``, ``scan_dt``, ``lat``/``lon``, ``tropopause_km``.

    ``summit_km`` (km s.n.m.) activa el **piso de terreno**: si el tope cae bajo
    la cumbre del volcán se agrega un flag y ``below_summit=True``, pero el
    número NO se toca (ver :func:`below_summit_flag`). Default ``None`` ⇒ no se
    evalúa, comportamiento idéntico al histórico para todo call-site existente.
    La cumbre del catálogo viaja siempre en ``summit_km_catalog`` (informativa,
    sin efecto sobre el retrieval) para que la pantalla pueda mostrar el tope
    contra el cráter aunque el piso esté apagado.
    """
    from src.fetch.goes_s3 import _scan_start, download_band_at, open_band
    from src.process.brightness_temp import rad_to_bt
    from src.process.scene import acquire_ash_scene

    source = ("Wen-Rose 1994 (corrección emisividad 2 canales 11/12µm → Tc) → "
              "perfil GFS T(z) · INDICATIVO · corrige el BT-matching en plumas "
              "semitransparentes · independiente de SSEC")

    # Adquisición común (bandas del mismo scan + máscara + SO₂ + perfil GFS);
    # los guards de honestidad viven en scene.acquire_ash_scene. Wen-Rose sí
    # necesita los coeficientes Planck: mezcla RADIANCIAS, no temperaturas.
    scene = acquire_ash_scene(dt, volcano, radius_deg, with_coefs=True,
                              source=source, label="Wen-Rose")
    if isinstance(scene, dict):
        return scene

    bts, coefs, mask = scene.bts, scene.coefs, scene.mask
    scan_dt, ref = scene.scan_dt, scene.ref_dt
    y0, y1, x0, x1 = scene.window
    profile = scene.profile

    # ── C16 (13.3 µm CO₂) OPCIONAL: chequeo independiente de semi-transparencia ──
    # No es requerido (graceful si falta o cae en otro scan); +1 banda SOLO en este
    # retrieval, no en el pipeline NRT (por eso C16 vive en EXTENDED_IR_BANDS, fuera
    # de VOLCANIC_BANDS). Confirma/desmiente la corrección Wen-Rose con física
    # distinta (CO₂-slicing cualitativo). Ver co2_semitransparency().
    bt133 = None
    try:
        p16 = download_band_at(ref, CO2_BAND)
        if p16 is not None and _scan_start(p16.name) == scan_dt:
            with open_band(p16) as ds16:
                bt133 = rad_to_bt(ds16.isel(y=slice(y0, y1),
                                            x=slice(x0, x1))).load().values
    except Exception as e:
        logger.warning("Wen-Rose C16 (opcional): %s", e)
    co2_btd = co2_semitransparency(bts[14], bt133, mask)

    # ── Temperatura de superficie (Ts) sobre el perfil GFS ya adquirido ──
    n_clear = int((np.isfinite(bts[14]) & ~mask).sum())
    bg_spread = clear_sky_heterogeneity(bts[14], mask)   # #3 heterogeneidad del fondo
    ts_k = clear_sky_bt(bts[14], mask)
    ts_source = "cielo claro (escena)"
    if ts_k is None:
        ts_k = profile.get("skin_temp_K")
        ts_source = "GFS skin-T (Open-Meteo)"
    if ts_k is None and profile.get("levels"):
        ts_k = profile["levels"][0]["T_K"]      # último recurso: nivel superficie
        ts_source = "GFS nivel superficie"

    trop = profile.get("tropopause")
    trop_km = trop["z_m"] / 1000.0 if trop else None

    out = scene.base_out(percentile, source)
    # Cumbre del catálogo: puramente informativa (el piso se evalúa sólo si el
    # caller pasa summit_km). Volcano.elevation está en metros.
    _elev = getattr(scene.volcano, "elevation", None)
    out.update({
        "summit_km_catalog": (float(_elev) / 1000.0 if _elev is not None else None),
        "beta": beta,
        "ts_k": (float(ts_k) if ts_k is not None else None), "ts_source": ts_source,
        "co2_semitransp_btd": co2_btd, "bg_spread_k": bg_spread,
    })

    # ── β-ratios de composición (Pavolonis 2010): confirma SILICATO vs hielo/agua ──
    # Independiente del BTD (usa el 8.5 µm, que el despeje 11/12 no usa). Modo
    # β_tropo: T_ref = tropopausa; clear-sky por banda de la escena como proxy de
    # R_clr (simplificación del RTM que no tenemos). Clasifica por cercanía a los
    # anclas verificados de la Tabla 2 de Pavolonis 2010. INDICATIVO.
    comp = None
    if trop is not None and BT85_BAND in coefs and BT12_BAND in coefs \
            and int(mask.sum()) > 0:
        try:
            from src.process.beta_ratios import beta_composition
            clr11 = clear_sky_bt(bts[BT85_BAND], mask)
            clr14 = (ts_k if ts_source == "cielo claro (escena)"
                     else clear_sky_bt(bts[14], mask))
            clr15 = clear_sky_bt(bts[BT12_BAND], mask)
            if None not in (clr11, clr14, clr15):
                comp = beta_composition(
                    bts[BT85_BAND], bts[14], bts[BT12_BAND], trop["T_K"],
                    clr11, clr14, clr15, coefs[BT85_BAND], coefs[14],
                    coefs[BT12_BAND], ash_mask=mask)
        except Exception as e:
            logger.warning("β-ratios composición: %s", e)
    out["composition"] = comp

    # Si no hay Ts utilizable, Wen-Rose no puede correr → degradar a BT-matching
    # puro (todo opaco) con una nota; igual reportamos el campo BT.
    alt_bt = altitudes_from_bt(bts[14], profile)
    field_bt = np.where(mask & np.isfinite(alt_bt), alt_bt, np.nan) / 1000.0

    if ts_k is None:
        tc = bts[14]
        solved = np.zeros(bts[14].shape, dtype=bool)
        well_constrained = solved
        out["ts_note"] = "sin Ts → Wen-Rose degradado a BT-matching"
    else:
        tc, solved, well_constrained = solve_tc_grid(
            bts[14], bts[15], float(ts_k), coefs[14], coefs[15], beta=beta)

    # #1 Guard de honestidad: las correcciones NO confiables (mal-condicionadas o
    # saturadas en la tropopausa) revierten a la cota en vez de aportar un Tc frío
    # espurio que infla el tope. Solo las confiables llevan la corrección Wen-Rose.
    tc_top, reliable = _revert_unreliable(tc, bts[14], well_constrained, profile,
                                          trop)
    alt_wr = altitudes_from_bt(tc_top, profile)
    ash = mask & np.isfinite(alt_wr)
    field_wr = np.where(ash, alt_wr, np.nan) / 1000.0
    valid = np.isfinite(np.where(ash, alt_wr, np.nan))
    n = int(valid.sum())
    n_corrected = int(np.sum(mask & reliable))
    n_reverted = int(np.sum(mask & solved & ~reliable))

    out.update({
        "field_km": field_wr, "field_bt_km": field_bt,
        "mask_px": n, "n_corrected": n_corrected, "n_reverted": n_reverted,
    })

    if n == 0:
        out.update({"status": "no_plume", "top_km": None, "top_bt_matching_km": None,
                    "top_max_km": None, "delta_km": None, "n_capped": 0,
                    "all_capped": False})
        return out

    # Tope Wen-Rose y BT-matching sobre los MISMOS píxeles de ceniza (excluyendo
    # los 'capped' en la tropopausa).
    top_wr, top_wr_max, n_capped, all_capped = _top_stats(
        field_wr, valid, alt_wr, trop, percentile)
    valid_bt = mask & np.isfinite(alt_bt)
    top_bt, _, _, _ = _top_stats(field_bt, valid_bt, alt_bt, trop, percentile)
    delta = (top_wr - top_bt) if (top_wr is not None and top_bt is not None) else None

    # ── #1 Banda de incertidumbre por la microfísica (β ∈ BETA_RANGE) ────
    # β fija la razón de absorción 12/11; no la medimos (haría falta retrieval de
    # radio efectivo). En vez de fingir un número exacto, barremos el rango del
    # silicato andesítico (Pavolonis 2010 Fig.3: β(12,11) ~0.45-1.0 para r_eff
    # 1-12 µm; barremos 0.55-0.95) y reportamos el tope como banda. Solo si hubo
    # corrección real (con todo opaco, β no cambia nada → banda degenerada).
    top_lo = top_hi = top_wr
    if ts_k is not None and n_corrected > 0 and top_wr is not None:
        band = [_wr_top_for_beta(bts[14], bts[15], float(ts_k), coefs[14],
                                 coefs[15], b, mask, profile, trop, percentile)
                for b in BETA_RANGE]
        band = [t for t in band if t is not None] + [top_wr]
        top_lo, top_hi = min(band), max(band)
    # Veredicto del árbitro CO₂ con gate de altura (fix F1, audit jul-2026): el
    # BTD(11−13.3) solo discrimina con cota ALTA; con cota baja una pluma opaca
    # da el mismo BTD que una fina → "no_discrimina", sin conclusión.
    verdict = co2_verdict(co2_btd, top_bt)
    # Si hubo píxeles REVERTIDOS (corrección no confiable) y el CO₂ es
    # CONSISTENTE con semitransparencia (cota alta + BTD grande), el tope real
    # puede estar entre la cota y la tropopausa → el extremo SUPERIOR de la banda
    # es la tropopausa (incertidumbre honesta de un lado; el headline sigue
    # siendo la cota conservadora). Con cota baja NO se extiende: sería inventar
    # techo con un observable degenerado.
    if (n_reverted > 0 and trop_km is not None and top_hi is not None
            and verdict == "consistente_semitransp"):
        top_hi = max(top_hi, trop_km)
    band_width = (top_hi - top_lo) if (top_hi is not None
                                       and top_lo is not None) else None

    # ── #2 Guards de honestidad: corrección o Ts sospechosos ─────────────
    flags = []
    if n_reverted > 0:
        if verdict == "consistente_semitransp":
            extra = (" — el tope real PODRÍA ser mayor (CO₂ consistente con "
                     "semitransparencia; no la confirma)")
        elif verdict == "no_discrimina":
            extra = (" — el CO₂ no discrimina a esta altura (fina-alta y "
                     "opaca-baja dan el mismo BTD)")
        else:
            extra = ""
        flags.append(f"{n_reverted}/{n} píxeles con magnitud NO restringida "
                     f"(pluma fina o corrección saturada en tropopausa) → "
                     f"revertidos a la cota{extra}")
    if delta is not None and delta >= DELTA_WARN_KM:
        flags.append(f"corrección grande (+{delta:.1f} km): verificá Ts y nº de píxeles")
    if ts_source != "cielo claro (escena)":
        flags.append(f"Ts de fallback ({ts_source}): fondo cálido no observado")
    elif n_clear < 4 * MIN_CLEAR_PX:
        flags.append(f"Ts con pocos píxeles claros ({n_clear}): fondo poco robusto")
    if bg_spread is not None and bg_spread >= HETERO_WARN_K:
        flags.append(f"fondo heterogéneo (spread {bg_spread:.0f} K: costa/relieve): "
                     "Ts poco confiable, la corrección puede sesgarse")
    # #4: el CO₂ como árbitro inverso — SOLO informativo con cota alta (BTD chico
    # implica opaca únicamente cuando el tope está alto; ver co2_verdict).
    if n_corrected > 0 and verdict == "opaca_alta":
        flags.append(f"CO₂ 13.3µm sugiere pluma opaca de tope alto (BTD 11−13.3 ≈ "
                     f"{co2_btd:.1f} K): corrección Wen-Rose poco justificada")
    # F2 (audit jul-2026): β medido por composición como selector CUALITATIVO —
    # NUNCA dentro del solver (circularidad exacta verificada: Tc=tropopausa se
    # vuelve raíz del acople). β(12,11) < 0.7 ⇒ ceniza fina (r_eff ≲ 4 µm) ⇒ la
    # corrección real es MENOR que la del β central ⇒ el tope probablemente cae
    # en la mitad BAJA de la banda reportada.
    if (n_corrected > 0 and comp is not None
            and comp.get("beta_12_11") is not None
            and comp["beta_12_11"] < BETA_SILICATE):
        flags.append(f"β(12,11) medido ≈ {comp['beta_12_11']:.2f} (ceniza fina): "
                     "el tope probablemente en la mitad BAJA de la banda")

    # Flags de fiabilidad de la literatura (banda 3-12 km; régimen opaco+alto).
    near_trop = (top_wr is not None and trop_km is not None
                 and top_wr >= trop_km - 3.0)
    flags.extend(reliability_flags(top_wr, co2_btd, near_trop))
    # Piso de terreno: una pluma no puede tener el tope bajo su propio cráter.
    # Se MARCA, no se clampea — un clamp silencioso volvería plausible un
    # retrieval roto (audit ago-2026, C3).
    summit_msg = below_summit_flag(top_wr, summit_km)
    if summit_msg:
        flags.append(summit_msg)
    # β-ratios de composición: si NO clasifica como silicato, la detección BTD
    # puede ser falso positivo (cirros/hielo) — aviso independiente (Pavolonis 2010).
    if comp is not None and comp.get("is_ash") is False:
        flags.append(f"β-ratios sugieren composición '{comp['composition']}' "
                     f"(no silicato): posible falso positivo de ceniza")

    out["co2_verdict"] = verdict
    out["summit_km"] = summit_km
    out["below_summit"] = (summit_msg is not None) if summit_km is not None else None

    confidence = wen_rose_confidence(n, band_width,
                                     ts_source == "cielo claro (escena)",
                                     top_km=top_wr)

    out.update({
        "status": "ok",
        "top_km": top_wr, "top_max_km": top_wr_max,
        "top_km_lo": top_lo, "top_km_hi": top_hi, "band_width_km": band_width,
        "top_bt_matching_km": top_bt, "delta_km": delta,
        "n_capped": n_capped, "all_capped": all_capped,
        "n_clear": n_clear, "confidence": confidence, "flags": flags,
    })
    return out
