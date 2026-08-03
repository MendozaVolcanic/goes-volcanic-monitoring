# Registro para el paper — retrieval indicativo de altura de pluma desde GOES-19 (open source)

> **Documento vivo.** Registra métodos, decisiones, validaciones y lecciones en
> formato pre-paper. Actualizar con cada avance sustantivo (regla: si cambia el
> método o hay una validación nueva, se anota acá EN LA SESIÓN, no después).
> Working title: *"An open-source, uncertainty-aware volcanic plume height
> retrieval chain from GOES-19 ABI for operational monitoring in Chile"*.

## 1. Motivación (por qué existe esto)

- SERNAGEOMIN/OVDAS vigila 43 volcanes (RNVV). El producto cuantitativo de
  referencia (VOLCAT, Pavolonis 2013) llega vía un único host (SSEC) con
  latencia 30-50 min y caídas intermitentes → riesgo operacional.
- Objetivo: una cadena de altura de pluma **propia, NRT (~13 min), de código
  libre**, honesta sobre su incertidumbre ("INDICATIVO"), que complemente — no
  reemplace — al VOLCAT.
- Novedad frente a lo publicado: no es un retrieval nuevo, es una **cadena
  operacional mínima y auditable** (sin RTM, sin optimal estimation) con
  cuantificación de incertidumbre explícita y guards de honestidad, corriendo
  sobre infraestructura gratuita (AWS S3 público + Open-Meteo + GitHub Actions
  + HF Spaces). El ángulo de paper: *qué se puede lograr (y qué no) sin el
  stack pesado de las agencias*, con validación contra ACHA/VOLCAT.

## 2. Métodos (cadena completa, con referencias)

| Etapa | Método | Ref. física | Módulo |
|---|---|---|---|
| Detección de ceniza | BTD split-window (11.2−12.3 < −1 K) + tri-espectral 8.4 µm | Prata 1989; ATBD GOES-R VolAsh v3.0 | `src/process/ash_detection.py` |
| Adquisición de escena (común a 3a/3b y a la referencia externa) | Ventana geos desde C14 → C11/C14/C15 del **mismo scan** → máscara + contexto SO₂ (+ perfil GFS). Criterios de degradación (no reportar): banda ausente, bbox fuera del disco, bandas de scans distintos, sin perfil | — (guards propios; ver §5 C1) | `src/process/scene.py` |
| Perfil T(z) + tropopausa | GFS vía Open-Meteo pressure levels; tropopausa = punto frío 6-20 km; rama monótona (envolvente fría) para inversiones | — | `src/fetch/gfs_profile.py` |
| Perfil T(z) alternativo (cross-check) | LVTPF del PROPIO GOES-19 (sondeo IR ABI, 101 niveles); mediana de cielo claro del entorno (DQF_Overall==0 & DQF_Retrieval==0); z(p) derivada por integración hipsométrica anclada a ISA | producto NOAA ABI-L2-LVTPF; ec. hipsométrica | `src/fetch/goes_lvtp.py` |
| Altura cota (3a) | BT-matching: BT(11 µm) del tope → T(z) → z. Cota inferior | estándar | `src/process/bt_matching_height.py` |
| Altura corregida (3b) | Wen-Rose 2 canales: I_i=(1−t_i)B_i(Tc)+t_i·B_i(Ts), t12=t11^β; grid-argmin del residuo \|t12−t11^β\| en Tc∈[180 K, BT11]; Ts = BT de cielo claro de la escena (p92 de píxeles no-ceniza) | Wen & Rose 1994 (modelo); Pavolonis 2010 (β) | `src/process/wen_rose_height.py` |
| Composición (β-ratios) | ε=(R−R_clr)/(B(T_trop)−R_clr); β=ln(1−ε₁)/ln(1−ε₂); clasificación por cercanía a anclas Tabla 2 (ceniza 0.564/0.705, hielo 1.07/0.836, agua 1.21/0.981) | Pavolonis 2010 (modo β_tropo) | `src/process/beta_ratios.py` |
| Árbitro CO₂ | BTD(11−13.3) con **gate de altura** (solo discrimina con cota ≥ 7 km; ver §5 F1) | Menzel 1983 (heritage); audit propio | `co2_verdict` en wen_rose |
| Altura por viento (3c) | Advección del centroide entre 2 scans → perfil de viento GFS → z; requiere cizalla ≥8 m/s; banda de ambigüedad ±8 m/s (= RMSE del viento GFS, no ±3 optimista); guards de advección implausible (>60 m/s), **advección casi nula con cizalla fuerte → pluma adjunta al cráter (`adv_ambiguous`)**, **desajuste del mejor nivel > 8 m/s → ningún viento de la columna explica la advección (`adv_inconsistent`)**, viento viejo (>3 h) y mismo-scan | Pavolonis et al. 2020 (idea) | `src/process/wind_shear_height.py` (no en producción aún) |
| Referencia externa | ACHA NOAA (ABI-L2-ACHA2KMF ∩ máscara de ceniza) | Heidinger OE | `src/process/acha_plume_height.py` |
| Parallax (georef) | Corre la pluma hacia el subsatélite Δ = h·tan(θ_zenit) (1er orden); ~1 km/km a −40°S. **h es AMSL/elipsoide** (el mismo datum de `field_km`; restar el terreno subcorrige ~50% sobre los Andes). NO cambia el tope, solo su posición en el mapa | Vicente et al. 2002; geometría geos | `src/process/parallax.py` |

**Cuantificación de incertidumbre (la contribución central del paper):**
1. Banda por microfísica: β barrido en (0.55, 0.95) → tope como [lo, hi].
2. Guard de mal-condicionamiento: span de Tc con residuo ≈ mínimo > 60 K ⇒
   corrección revertida a la cota (píxel "no restringido").
3. Confianza discreta (nunca "alta") degradada por: nº de píxeles, ancho de
   banda, Ts de fallback, tope fuera de la banda fiable 3-12 km (Saint 2024).
4. Flags de régimen: opaco+alto (colapso Mie), fondo heterogéneo, β medido
   fino (⇒ mitad baja de la banda), SO₂-sin-ceniza (sin altura válida).

## 3. Validaciones (casos reales, con números)

| Caso | Resultado | Interpretación |
|---|---|---|
| Popocatépetl 2026-06-26 | BT-matching 9.2 km vs ACHA 10.3 km (Δ−1.1) | cota inferior se comporta como tal |
| Láscar 2026-06-27 09:50 | BT-matching 6.8 → Wen-Rose 10.4 km (Δ+3.6; 8/8 px corregidos; Ts=268 K cielo claro; banda β 7.9–13.6 km) · ACHA=no_plume | la corrección de emisividad sube el tope en semitransparente; el método rescata casos sin retrieval L2; banda honesta domina el número |
| Chillán 2026-06-27 (pluma SO₂) | BTD nunca cruza −1 K → no_plume; SO₂ −3.2 K | correcto: gas transparente en 11 µm NO recibe altura (límite documentado) |
| Láscar (wind-shear targeted) | advección 151 m/s (imposible) + viento a 41 h → **inputs rotos detectados** → guards MAX_ADV_MS/MAX_WIND_AGE_H | validación negativa útil: reveló 2 modos de fallo |
| **Láscar 2026-06-27 09:00–10:20 (wind-shear con GFS de ARCHIVO)** | con el viento CORRECTO del día (ya no "41 h off"), 5 scans dan `top` caótico (0.9→4.4→3.2→23.9→7.5 km) y **banda = columna entera** (0.2–23.9 km) casi siempre | **validación negativa que reveló un hueco de honestidad**: `discriminates` (cizalla ≥8) es necesario pero NO suficiente → nuevo guard `band_unconstrained` (banda >8 km ⇒ sin altura). Confirma que el árbitro necesita una pluma **grande y coherente**; la de Láscar es chica y su centroide se mueve por ruido, no por advección |
| Suite | >200 tests (round-trips de física + orquestación end-to-end sintética con anti-band-swap) | forward∘inverse = identidad pineada; swap de bandas ahora rompe la suite |
| **GFS vs radiosondas (4 estaciones chilenas, 2026-07-01 12Z)** | **T(z) en 5–12 km: RMSE 0.3–1.1 K, bias ≤0.4 K ⇒ ≤60 m de error de altura equivalente** (Pto Montt, Antofagasta, Sto Domingo, Pta Arenas; `scripts/validate_gfs_vs_radiosonde.py`) | el mapeo Tc→altura queda validado contra medición real — el perfil NO es el eslabón débil |
| Viento GFS vs radiosondas (ídem) | RMSE vectorial 8–17 m/s en 1–15 km | insumo de calibración del árbitro de cizalla: su tolerancia de ambigüedad (3 m/s) es optimista — recalibrar durante la validación con evento real |
| **LVTPF (propio GOES) vs GFS** (4 volcanes, 2026-07-02 05:20Z; `scripts/compare_lvtp_vs_gfs.py`) | **T(z) 5–12 km: RMSE medio 0.66 K (0.34–0.98), bias −0.53 K**; mapeo Tc→altura para BT 220–230 K concuerda dentro de **±0.2 km**; divergencia solo en/sobre la tropopausa (BT 215 K, +1.3 km en Villarrica/Chillán) — región ya marcada no fiable (>12 km) | **dos perfiles independientes (satélite propio vs modelo) concuerdan al mismo nivel que GFS concuerda con la radiosonda ⇒ la altura queda doblemente respaldada.** Sesgo frío sistemático ~0.5 K de LVTPF vs GFS (posible bias del sondeador IR / anclaje hipsométrico), a documentar. LVTPF sirve como cross-check NRT sin depender de Open-Meteo |

## 4. Fuentes de datos (todas gratuitas, verificadas)

GOES-19 ABI L1b (S3 `noaa-goes19`, C07/11/13/14/15 + C10/16 on-demand) ·
ABI-L2-ACHA2KMF, FDCF · VOLCAT/SSEC (PNG) · Open-Meteo GFS (T(z), viento,
skin-T) · **radiosondas Wyoming YA integradas como validador** (endpoint
`/wsgi/`, 4 estaciones; `scripts/validate_gfs_vs_radiosonde.py`).

**LVTPF — INTEGRADO (jul-2026):** `src/fetch/goes_lvtp.py` (`fetch_lvtp_profile`)
baja el gránulo `ABI-L2-LVTPF` (`LVT(y,x,pressure)` en K, **101 niveles** vs 19
de Open-Meteo, grilla 10 km 1086², misma proyección geos → reusa
`_geos_index_bbox`; 45 MB/gránulo cada 10 min), recorta el entorno del volcán,
arma el perfil de **cielo claro** (mediana de píxeles `DQF_Overall==0 &
DQF_Retrieval==0`; bajo la pluma `DQF_Overall==4` → ignorados, análogo al
clear-sky Ts) y **deriva la altura geopotencial por integración hipsométrica**
(LVTPF NO trae z; se ancla al absoluto AMSL con la atmósfera estándar en el
nivel base — offset constante ~0.1 km). Salida drop-in de `fetch_gfs_profile`.
Validado como cross-check del GFS (ver §3). 10 tests (`tests/test_lvtp.py`).

**GFS-archive — HECHO (jul-03):** `src/fetch/gfs_archive.py` baja el perfil GFS
**archivado** (T(z) y viento) del bucket público `noaa-gfs-bdp-pds` (≥2021
verificado) por **byte-range GRIB2**: cada gránulo pesa 508 MB pero el `.idx` de
texto da el offset de cada registro → bajamos solo TMP/HGT/UGRD/VGRD en los 19
niveles de interés (~38–57 MB) y los decodifica `eccodes`. Salida **drop-in** de
`fetch_gfs_profile`/`fetch_gfs_wind_profile`. Destraba la validación de eventos
históricos (Open-Meteo da null en niveles pasados). Verificado en vivo sobre
Láscar: 19 niveles, tropopausa 16.5 km/206 K, jet 33 m/s en 400 hPa; solapamiento
con Open-Meteo reproduce el perfil NRT ya validado vs radiosondas. `eccodes` es
**dep opcional** (extra `.[archive]` en pyproject), NO va en el deploy de la app.
9 tests (`tests/test_gfs_archive.py`); script `scripts/validate_gfs_archive.py`.

## 5. Lecciones de la auditoría adversarial (material de paper: robustez)

El desarrollo usó un loop **auditoría multi-agente → verificación adversarial
independiente → fix**. Dos hallazgos confirmados que cambiaron el método
(sección "lessons learned" del paper — el proceso ES parte de la contribución):

- **F1 — degeneración del test CO₂:** BTD(11−13.3) grande no distingue "fina y
  alta" (+10..15 K) de "OPACA y baja" (+8..14 K a 4 km): el observable solo
  discrimina con tope alto. Fix: `co2_verdict` con gate de cota ≥ 7 km y
  lenguaje "consistente con" (nunca "confirma"). Implicancia general: los
  confirmadores IR de un solo umbral absoluto tienden a confirmar de más.
- **F2 — procedencia del β:** la literatura operativa hereda "β≈0.9 silicato"
  sin procedencia (Wen & Rose 1994 no define β — cita fantasma detectada); la
  misma cantidad física en Pavolonis 2010 va de 0.45 a ~1.0 con r_eff. Fix:
  β central 0.7, banda (0.55, 0.95), β medido solo como flag cualitativo.
  **Anti-fix documentado:** alimentar el β medido (modo β_tropo) al solver es
  circular de forma exacta (Tc=tropopausa se vuelve raíz) — verificado antes
  de implementarlo.
- **F-Láscar — el ancho de banda es el verdadero discriminador del árbitro de
  viento:** al validar sobre Láscar 27-jun con el viento correcto (GFS de
  archivo), el árbitro devolvía `status=ok` con un tope puntual que saltaba
  caóticamente entre scans (0.9→23.9 km), mientras la banda de ambigüedad cubría
  toda la columna. El test de cizalla (`discriminates`, spread ≥ 8 m/s) daba True
  —hay cizalla en el perfil— pero la advección de una pluma chica es consistente
  con casi cualquier altitud. Fix: guard `band_unconstrained` (banda > 8 km ⇒ sin
  altura). Implicancia general: en un árbitro geométrico, la existencia de la
  señal discriminante (cizalla) no garantiza que el observable la restrinja; hay
  que medir el ANCHO de la solución, no solo su existencia. También validó, por
  la negativa, que el método necesita una pluma grande y coherente.
- **F3 — selección de gránulo en el borde de hora (reproducibilidad de la
  validación histórica):** un 2º bug hunt multi-agente (jul-2026) halló que los
  5 fetchers S3 (`goes_s3`, `frp_timeline`, `goes_fdcf`, `goes_acha`,
  `goes_lvtp`) elegían el "scan más cercano a `dt`" listando solo la carpeta
  horaria de `dt` con la previa como *fallback* — nunca la hora SIGUIENTE. En un
  borde de hora (p.ej. `dt`=HH:56, cuyo vecino real es (HH+1):00) eso selecciona
  un gránulo temporalmente más lejano y sesga el frame usado para altura/ceniza,
  o mal-atribuye el FRP a un bucket de 10 min adyacente. Fix: helper único
  `src/fetch/granule_select.py` que elige el de menor \|Δt\| sobre la **unión**
  `[dt-1h, dt, dt+1h]` (puro, testeado sin red). Implicancia para el paper:
  al reportar casos de validación por fecha/hora, la cadena ahora garantiza el
  gránulo verdaderamente más cercano al instante objetivo.
- **G1 — un guard duplicado es un guard sin probar (ola 2, audit ago-2026):** el
  preámbulo de adquisición estaba escrito tres veces (wen_rose / bt_matching /
  acha) y con él los criterios de "no reportar". El guard de mismo-scan (C1,
  jun-2026) nació en ACHA y se replicó a mano a los otros dos; el audit encontró
  que **ninguna de las tres copias tenía test** —el fixture sintético pineaba
  `_scan_start` a una constante, así que la rama nunca se ejecutaba—. Se unificó
  en `src/process/scene.py` y se pineó con un test que falla si se desactiva el
  guard (verificado por mutación). Los métodos NO cambiaron: la suite completa
  (212 tests previos) pasa sin modificar un solo assert, y los 19 tests nuevos
  cubren guards + orquestación de `bt_matching_top_height` y `plume_top_height`,
  que hasta ahora solo se probaban con un volcán inexistente. Implicancia para
  la reproducibilidad: los criterios de degradación del retrieval son ahora
  auditables en un único archivo, no inferidos de tres copias divergentes.

## 6. Open source / reproducibilidad

- Repo público: `MendozaVolcanic/goes-volcanic-monitoring` (GitHub).
- **Licencia: Apache-2.0** (decisión del autor, jul-2026; LICENSE en la raíz,
  declarada en pyproject.toml y README). El README decía "MIT" sin archivo —
  corregido. Nota: si SERNAGEOMIN reclama copyright institucional, ajustar el
  titular en la documentación (la licencia no cambia).
- Deps 100% pip (sin RTM Fortran); deploy reproducible (Dockerfile + HF Space).
- Scripts de validación reproducibles: `scripts/validate_fase3b.py`, `_fase3c.py`.
- Datos crudos: buckets AWS públicos sin credenciales → cualquier grupo puede
  reproducir los casos de la §3 con fecha/hora.

## 7. Límites declarados (sección "limitations" ya redactada)

Resolución 2 km (techo físico IR ABI) · sesgo IR sistemático −0.4..−0.8 km ·
banda fiable 3-12 km · sin altura para plumas de gas/SO₂ · parallax de georef
corregido a 1er orden (Δ = h·tanθ, ~1 km/km a −40°S; `parallax.py`; falta
cablearlo al render del mapa) · sin RTM (β_tropo aproximado con clear-sky de
escena) · wind-shear con banda de
ambigüedad recalibrada al RMSE del viento GFS (±8 m/s) y guard de pluma adjunta
(`adv_ambiguous`) implementados, pero el NÚMERO aún sin validar en evento real.

## 8. Candidatos a trabajo futuro (ya scopeados)

CO₂-slicing por cociente de radiancias (Menzel 1983) como Fase 3d · ~~perfil
LVTPF del propio GOES~~ (HECHO, §4) · ~~validación con radiosondas Wyoming~~
(HECHA, §3) · ~~GFS archivado para validación histórica~~ (HECHO, §4) ·
~~corrección de parallax de 1er orden (h·tanθ)~~ (HECHO, §2/§7 — falta cablear
al mapa) · fetcher de mesoescala ABI (`ABI-L1b-RadM`, 1 min) cuando un sector
meso cae sobre un volcán objetivo — para detección de inicio y loops RGB, NO
para la altura (ver §9) · libRadtran para training data
(Fase 4, solo con justificación) · cablear LVTPF al dashboard como cross-check
visible del perfil GFS (opcional, junto a la tab "Altura propia").

## 9. Resolución y cadencia — el techo del ABI y el diseño operacional

Esta sección preempta dos preguntas de revisor ("¿por qué 2 km si VOLCAT tiene
sectores de 250 m?" y "¿por qué no más frecuente?") y fija el argumento de
diseño: **el producto compite en cadencia, disponibilidad y honestidad, NO en
resolución** — porque en resolución no hay margen físico que ganar sobre el ABI.

### 9.1 Resolución: la grilla del sector ≠ la resolución nativa del retrieval

- Las bandas IR del ABI que hacen detección de ceniza y altura (C07/11/13/14/15/16,
  3.9–13.3 µm) son **2 km en el nadir** — techo físico del sondeador. Solo la banda
  visible C02 es 0.5 km y C01/03/05 son 1 km, pero el visible NO da altura de ceniza
  (se necesita IR térmico, día y noche). Por lo tanto **toda** altura de ceniza
  derivada del ABI es información de 2 km, sea de SSEC o nuestra.
- Los sectores VOLCAT rotulados "250 m / 500 m / 1 km / 2 km" nombran la **grilla del
  raster de salida**, elegida según el sensor MÁS FINO asignado a ese sector — **no**
  la resolución del retrieval de ceniza. Prueba limpia: `Villarrica_250_m` es
  **VIIRS-only** (sin ABI); el 250 m tiene sentido ahí porque la banda I de VIIRS es
  ~375 m nativa. En cambio `Copahue_250_m` tiene ABI + VIIRS: cuando pasa el VIIRS el
  250 m es real, pero cuando alimenta el ABI su ceniza de 2 km se **re-muestrea** a la
  misma grilla de 250 m para co-registrar con el VIIRS — los píxeles extra son
  interpolación, no información nueva. La altura de ceniza desde ABI sigue siendo de
  2 km cualquiera sea la grilla del raster.
- Nuestra cadena entrega en la grilla nativa 2 km del ABI. Re-muestrear a un raster de
  250 m sería una línea de `interp` (cosmético, cero información nueva) → **no lo
  hacemos, por honestidad**. Para 250 m REAL habría que ingerir VIIRS polar (375 m),
  pero a ~12 h de revisita por satélite — lo que contradice el objetivo NRT.
- **Trade-off central del producto:** resolución espacial (polar, VIIRS 375 m, ~12 h)
  vs cadencia (geo, ABI 2 km, 10 min). Elegimos cadencia: una decisión de alerta
  necesita frescura, no píxeles.

### 9.2 Cadencia: qué permite el ABI (verificado en `noaa-goes19`, jul-2026)

| Modo ABI | Cadencia | Cobertura |
|---|---|---|
| Full Disk (`RadF`, el que usamos) | 10 min (6 scans/h) | hemisferio, incluye Chile |
| CONUS (`RadC`) | 5 min | solo Norteamérica |
| Mesoescala (`RadM1`/`RadM2`) | **1 min** (60 scans/h) | 1000×1000 km, apuntable |

- La cadencia de **1 min existe** en el mismo bucket sin credenciales (10× sobre el
  Full Disk). Pero hay **solo 2 sectores meso** para todo el hemisferio de GOES-East
  y **NOAA decide adónde apuntan**: verificado jul-2026, ambos sobre EE.UU. (M1 sobre
  Indiana, M2 sobre Iowa). Sobre Chile es **oportunista / pedible** (vía VAAC / NOAA
  durante un evento mayor — mismo mecanismo que pedir cobertura de sector VOLCAT).
- **Matiz físico contraintuitivo:** 1 min **rompe** el árbitro de viento — una pluma a
  20 m/s se mueve 12 km en 10 min (6 px, rastreable) pero solo 1.2 km en 1 min (<1 px,
  no rastreable). O sea, más cadencia sirve para **detección de inicio y loops RGB**,
  pero le quita la señal al método de altura por advección. No es universalmente mejor.
- La **latencia** (~13 min) está limitada por cuándo aparece el archivo en S3, no por
  la cadencia: subir la cadencia no baja la latencia.
