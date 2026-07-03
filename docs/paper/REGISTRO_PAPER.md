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
| Perfil T(z) + tropopausa | GFS vía Open-Meteo pressure levels; tropopausa = punto frío 6-20 km; rama monótona (envolvente fría) para inversiones | — | `src/fetch/gfs_profile.py` |
| Perfil T(z) alternativo (cross-check) | LVTPF del PROPIO GOES-19 (sondeo IR ABI, 101 niveles); mediana de cielo claro del entorno (DQF_Overall==0 & DQF_Retrieval==0); z(p) derivada por integración hipsométrica anclada a ISA | producto NOAA ABI-L2-LVTPF; ec. hipsométrica | `src/fetch/goes_lvtp.py` |
| Altura cota (3a) | BT-matching: BT(11 µm) del tope → T(z) → z. Cota inferior | estándar | `src/process/bt_matching_height.py` |
| Altura corregida (3b) | Wen-Rose 2 canales: I_i=(1−t_i)B_i(Tc)+t_i·B_i(Ts), t12=t11^β; grid-argmin del residuo \|t12−t11^β\| en Tc∈[180 K, BT11]; Ts = BT de cielo claro de la escena (p92 de píxeles no-ceniza) | Wen & Rose 1994 (modelo); Pavolonis 2010 (β) | `src/process/wen_rose_height.py` |
| Composición (β-ratios) | ε=(R−R_clr)/(B(T_trop)−R_clr); β=ln(1−ε₁)/ln(1−ε₂); clasificación por cercanía a anclas Tabla 2 (ceniza 0.564/0.705, hielo 1.07/0.836, agua 1.21/0.981) | Pavolonis 2010 (modo β_tropo) | `src/process/beta_ratios.py` |
| Árbitro CO₂ | BTD(11−13.3) con **gate de altura** (solo discrimina con cota ≥ 7 km; ver §5 F1) | Menzel 1983 (heritage); audit propio | `co2_verdict` en wen_rose |
| Altura por viento (3c) | Advección del centroide entre 2 scans → perfil de viento GFS → z; requiere cizalla ≥8 m/s; banda de ambigüedad ±8 m/s (= RMSE del viento GFS, no ±3 optimista); guards de advección implausible (>60 m/s), **advección casi nula con cizalla fuerte → pluma adjunta al cráter, `adv_ambiguous`**, viento viejo (>3 h) y mismo-scan | Pavolonis et al. 2020 (idea) | `src/process/wind_shear_height.py` (no en producción aún) |
| Referencia externa | ACHA NOAA (ABI-L2-ACHA2KMF ∩ máscara de ceniza) | Heidinger OE | `src/process/acha_plume_height.py` |

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
| Suite | 140 tests (round-trips de física + orquestación end-to-end sintética con anti-band-swap) | forward∘inverse = identidad pineada; swap de bandas ahora rompe la suite |
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
Archivo GFS AWS `noaa-gfs-bdp-pds` (≥2021, byte-range) pendiente para
validación histórica.

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
banda fiable 3-12 km · sin altura para plumas de gas/SO₂ · sin corrección de
parallax en georef (~1.2 km por km de altura a −40°S; hallazgo F4, pendiente) ·
sin RTM (β_tropo aproximado con clear-sky de escena) · wind-shear con banda de
ambigüedad recalibrada al RMSE del viento GFS (±8 m/s) y guard de pluma adjunta
(`adv_ambiguous`) implementados, pero el NÚMERO aún sin validar en evento real.

## 8. Candidatos a trabajo futuro (ya scopeados)

CO₂-slicing por cociente de radiancias (Menzel 1983) como Fase 3d · ~~perfil
LVTPF del propio GOES~~ (HECHO, §4) · ~~validación con radiosondas Wyoming~~
(HECHA, §3) · corrección de parallax de 1er orden (h·tanθ) · libRadtran para
training data (Fase 4, solo con justificación) · cablear LVTPF al dashboard
como cross-check visible del perfil GFS (opcional, junto a la tab "Altura
propia").
