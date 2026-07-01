# Fase 3b — Retrieval de altura Wen & Rose 1994 (corrección de emisividad 2 canales)

**Fecha:** 2026-06-28 · **Estado:** diseño + implementación
**Depende de:** Fase 2 (`src/fetch/gfs_profile.py`, perfil GFS T(z)) y Fase 3a
(`src/process/bt_matching_height.py`, BT-matching). **Mantiene** VOLCAT/SSEC como
primario cuantitativo; esto es **INDICATIVO**.

---

## 1. Por qué (geología → pipeline)

El BT-matching (Fase 3a) asume que el tope de la pluma es **opaco** en 11 µm: toma
`Tc ≈ BT(11 µm)` y la mapea al perfil GFS. Eso es correcto para plumas densas, pero
en plumas **semi-transparentes** (las primeras horas, los bordes, plumas finas) el
satélite **ve a través** de la ceniza hasta el suelo cálido de abajo, así que la BT
observada es **más cálida** que el tope real → BT-matching **subestima** la altura
(es cota inferior).

Wen & Rose (1994) corrige eso usando **dos canales** (11 y 12 µm): la ceniza
silicatada absorbe distinto en cada uno (absorción inversa, BTD 11−12 < 0), y esa
diferencia espectral permite **despejar simultáneamente la temperatura del tope (Tc)
y la transparencia (t)**, separando la contribución del suelo cálido. El resultado es
un **Tc más frío y más correcto** → altura **más alta** que el BT-matching. Es la
misma física que VOLCAT/Pavolonis 2013 usa, en versión reducida (sin optimal
estimation ni RTM).

---

## 2. Las ecuaciones (del paper, `WenRose_1994_VolcanicCloudParticles.pdf`)

**Eq. (1)** — radiancia observada a través de nube semi-transparente parcial (Ac =
fracción cubierta):

    I_i = (1 − Ac)·B(Ts) + Ac·( ε_i·B(Tc) + t_i·B(Ts) )

**Eq. (2)** — caso operacional, cobertura completa pero semi-transparente (Ac = 1),
con reflectividad de scattering R_i y `ε = 1 − R − t`:

    I_i = (1 − R_i)·B(Tc) + t_i·( B(Ts) − B(Tc) )

**Aproximación no-scattering** (R_i ≈ 0 ⇒ ε_i = 1 − t_i), que es la que implementamos
(estándar Prata 1989b / Yamanouchi; es lo precocinado en `ALTURA_COLUMNA_INVESTIGACION.md`):

    I_i = (1 − t_i)·B_i(Tc) + t_i·B_i(Ts)        i ∈ {11≡C14, 12≡C15}

- `B_i(T)` = radiancia de Planck de la banda i a temperatura T. Usamos los
  coeficientes **fk1/fk2/bc1/bc2 del NetCDF L1b** (más exactos que la fórmula
  monocromática Eq. 5 del paper) vía `brightness_temp.planck_rad_from_bt`.
- `t_i` = transmisividad de la nube (0 = opaca, 1 = transparente). `ε_i = 1 − t_i`.

**Acople de canales** (reduce 2 incógnitas de transparencia a 1):

    t12 = t11^β ,   β central = 0.7 · banda barrida (0.55, 0.95)

> **Procedencia de β (corregida en audit jul-2026):** β = τ12/τ11 es la MISMA
> cantidad que el β(12,11) de **Pavolonis 2010** (Fig. 3/Tabla 2: andesita
> r_eff 1–12 µm → β ≈ 0.45…1.0; ceniza fina 2 µm = 0.564; el central 0.7 ≈
> r_eff 4-5 µm). La cita anterior "β=0.9 (Wen-Rose Fig.1)" era **fantasma** —
> Wen & Rose 1994 no definen β (usan LUT de Mie; la parametrización t5=t4^β es
> del linaje cirrus Inoue/Parol). β < 1 codifica la **absorción inversa** de la
> ceniza (ε11 > ε12 → BTD 11−12 < 0). β NO se mide dentro del solver
> (circularidad verificada: con β medido en modo β_tropo, Tc=tropopausa se
> vuelve raíz exacta); el β(12,11) medido por `beta_ratios` solo genera un flag
> cualitativo ("ceniza fina → tope en la mitad baja de la banda").

**Despeje** (lo que implementamos): dados `I11, I12` (forward-Planck de las BT
observadas), `Ts` (→ `B_i(Ts)`) y β:

    t_i(Tc) = ( I_i − B_i(Tc) ) / ( B_i(Ts) − B_i(Tc) )            (de la Eq. anterior)
    g(Tc)   = t12(Tc) − [ t11(Tc) ]^β
    resolver  g(Tc) = 0   en  Tc ∈ [T_tropopausa , BT11_obs]

Bisección vectorizada (numpy, determinística). En `Tc = BT11_obs` ⇒ `t11 = 0` (límite
opaco = BT-matching); el root verdadero está más frío. **Si no hay cambio de signo**
(píxel no semi-transparente, BTD ≥ 0, o ruido) → **fallback opaco** `Tc = BT11_obs`
(= BT-matching). Luego `Tc → altitud` con `gfs_profile.altitudes_from_bt` (reusado).

**Garantía física:** `Tc_WenRose ≤ BT11_obs` siempre (la mezcla con el suelo cálido
solo puede subir la BT por encima del Tc real) → la altura Wen-Rose **≥** BT-matching.
El Δ ≥ 0 es la corrección por semi-transparencia.

---

## 3. Fuente de temperatura de superficie (Ts) — decisión

La Eq. (1) define **Ts = "brightness temperature of the surface"** bajo el supuesto de
que la atmósfera sobre/bajo la nube es una **ventana clara** (assumption 3 del paper).
Es decir: Ts es la **BT que el satélite ve en cielo claro**, NO una temperatura de piel
de modelo que requeriría corrección atmosférica. Evaluación de las dos fuentes pedidas:

| Fuente | Veredicto | Razón |
|---|---|---|
| **GOES `ABI-L2-LSTC` (LST)** | ❌ **rechazada** | Es **NaN justo bajo la pluma** (los píxeles nubosos se enmascaran) — falla exactamente donde la necesitamos. Además NaN sobre **océano** (muchos volcanes chilenos son costeros) y agrega un fetcher L2 nuevo. |
| **GFS skin-T (Open-Meteo `surface_temperature`)** | ⚠ **fallback** | Disponible en todos lados incluida bajo la pluma; cero deps nuevas (ya llamamos Open-Meteo). PERO: (a) es la skin-T del **punto de grilla del volcán** (alta elevación → fría, no representa el fondo cálido del entorno); (b) ignora la atenuación atmosférica de la ventana → sesgo cálido de la radiancia de fondo. |
| **BT de cielo claro de la escena** ⭐ | ✅ **primaria** | Es literalmente "la BT de la superficie" del paper: percentil cálido (p92) de los píxeles **finitos no-ceniza** de la ventana en BT(11 µm). Ya está en el marco radiométrico de ABI (atmósfera incluida), cero deps, captura el fondo real que el satélite ve alrededor de la pluma. |

**Implementación:** Ts primaria = BT de cielo claro de la escena; si hay menos de
`MIN_CLEAR_PX` píxeles claros (pluma llena el encuadre) → fallback GFS
`surface_temperature`. Si ninguna da un Ts **más cálido que BT11_obs** en un píxel →
ese píxel cae a fallback opaco (BT-matching). Se reporta cuál fuente se usó.

---

## 4. Módulos

| Archivo | Qué | Tests |
|---|---|---|
| `src/process/brightness_temp.py` | + `planck_rad_from_bt(bt, fk1,fk2,bc1,bc2)` (Planck forward, inverso de `rad_to_bt`), puro | round-trip bt→rad→bt |
| `src/fetch/gfs_profile.py` | + `surface_temperature` en el fetch → `profile["skin_temp_K"]` | parse skin-T |
| `src/process/wen_rose_height.py` | solver puro `solve_tc_grid` + `clear_sky_bt` + orquestación `wen_rose_top_height` (devuelve Wen-Rose **y** BT-matching del MISMO scan) | round-trip forward-model recupera Tc; Wen-Rose ≥ BT-matching; fallback opaco; clear-sky BT; volcán inexistente |
| `dashboard/views/volcat_viewer.py` | Fase 3b en la sección INDICATIVA: el retrieval propio reporta cota (BT-matching) → corregido (Wen-Rose) | — (no unit-tested) |
| `scripts/validate_fase3b.py` | valida Wen-Rose vs ACHA vs BT-matching en el mismo scan (Popocatépetl/Láscar) | — |

**Honestidad / límites:** sigue siendo INDICATIVO. La aproximación no-scattering
ignora R_i (Mie); β fijo no captura variación de radio efectivo; sobre inversiones de
T el mapeo Tc→altura es ambiguo (heredado de Fase 2, ya mitigado con la rama
monótona). NO compite con VOLCAT como primario. Plumas de **gas/SO₂** siguen sin
altura válida (transparentes en 11 µm → ver `reference_acha_so2_limit`).

---

## 4bis. Robustez / honestidad del número (refinamientos 2026-06-28)

El número Wen-Rose **no se reporta pelado** — un punto exacto engañaría a quien
decide alerta. Cuatro capas:

1. **Banda de incertidumbre por β** (`BETA_RANGE` 0.85–0.95): β fija la microfísica
   y NO la medimos, así que se resuelve `Tc` en los extremos del silicato y se
   reporta el tope como **banda** (`top_km_lo`/`top_km_hi`). En Láscar real la
   banda fue 7.9–13.6 km para un central de 10.4 — la microfísica sola pesa ~6 km.
2. **Confianza INDICATIVA** (`wen_rose_confidence`, nunca "alta"): degrada por
   pocos píxeles, banda ancha o Ts de fallback. (Láscar 8 px → "muy baja".)
3. **Guards de Ts/corrección** (`flags`): avisa si Δ ≥ 5 km (corrección
   implausible), si el Ts vino de fallback GFS, o si hubo pocos píxeles claros.
   Validado: cazó un Δ=+10.9 km (tope pegado a la tropopausa con 6 px).
4. **Árbitro independiente CO₂ 13.3 µm** (`co2_semitransparency`, banda C16 de
   `EXTENDED_IR_BANDS`, descarga OPCIONAL solo en este retrieval): `BTD(11−13.3)`
   sobre la ceniza. Positivo ⇒ semi-transparencia confirmada con física DISTINTA
   al despeje (la corrección era real); ≈0 ⇒ pluma opaca ⇒ corrección sospechosa
   de ruido → flag. Es el primer uso honesto del C16 sin RTM (CO₂-slicing
   cualitativo); la detección ATBD-grade con β-ratios sigue gated por el RTM.
5. **Guard de mal-condicionamiento** (`_revert_unreliable`): cuando el dato NO
   restringe el `Tc` (pluma fina → residuo plano, τ≲0.5 vía span de Tc dentro de
   `RES_TOL`) o la corrección **satura en la tropopausa** (runaway), esos píxeles
   **revierten a la cota** en vez de aportar un Tc frío espurio. Si quedan
   revertidos pero el CO₂ confirma semi-transparencia, la banda se ensancha hasta
   la tropopausa (incertidumbre honesta de un lado) y el headline es la cota.
   Validado: Láscar 28-jun pasó de un engañoso 16.5 km a "cota 5.6 km, banda
   5.6–16.5, el real puede ser mayor".
6. **Ts local + heterogeneidad** (`clear_sky_bt` con anillo, `clear_sky_heterogeneity`):
   el Ts se estima del **anillo de cielo claro alrededor de la pluma** (mejor que
   un percentil de toda la ventana sobre terreno mixto); flag cuando el fondo es
   heterogéneo (costa: mar+tierra) avisando que el Ts es poco confiable.

## 5. Referencias

- **Wen, S. & Rose, W.I. (1994)** *Retrieval of sizes and total masses of particles in
  volcanic clouds using AVHRR bands 4 and 5.* JGR 99(D3):5421-5431. doi:10.1029/93JD03340.
  PDF OA (Michigan Tech GREEN, tras AWS WAF): `WenRose_1994_VolcanicCloudParticles.pdf`.
- Pavolonis (2010) `Pavolonis_2010_CloudCompositionTheory.pdf` — formalismo β/emisividad.
- ATBD GOES-R VolAsh v3.0 — `../ATBD_GOES-R_VolAsh_v3.0_July2012.pdf`.
