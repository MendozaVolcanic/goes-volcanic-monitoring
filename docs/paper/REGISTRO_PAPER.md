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
| **Magnitud propia vs VOLCAT, 110 scans de 9 eventos (Sabancaya, Reventador, Chillán; oct-nov 2026)** (`scripts/validate_magnitud.py`, criterio y exclusiones commiteados antes de medir) | BT-matching, Wen-Rose y ACHA ∩ ceniza dan tope en **1 de 110 scans**; en ese scan (1 píxel) **0 de 1** se cruza con el bloque VOLCAT (propio 11,2 a 14,8 km contra 7 a 8 km). 109 scans con máscara de ceniza vacía; Sabancaya 01-11: BT11 mín. 264 K, BTD 11-12 mín. -0,56 K dentro de 15 km | **validación negativa**: la magnitud no se pudo contrastar porque la detección BTD < -1 K no ve plumas que VOLCAT mide como semitransparentes de 6 a 8 km; hace falta un caso de ceniza opaca dentro de la ventana de 30 días de VOLCAT (plan §3.7) |
| **Por qué VOLCAT ve Chillán y nosotros no: cielo despejado modelado (H3) y seguimiento (H7), oct-nov 2026** (`docs/own_volcat/h3_h7/`, criterios commiteados antes de medir) | Cálculo línea por línea propio (HITRAN + MT_CKD + SRF ABI + GFS 0,25°), sesgo C14 −0,29 K, dispersión 2,4 K de noche y 8,2 K de día; compuerta ε(11) ≥ 0,02: 90 % huella contra 88 % control pareado (37 pares, 458 px); con cielo empírico 3,5 %. H7: 0 de 3 episodios con señal propia en el primer cuadro | resultado negativo publicable: el cielo modelado con terreno 0,25° pone la cumbre ~1,5 km más baja y la compuerta mide el terreno, no la pluma; la pluma tibia de Chillán no tiene firma IR separable a 2 km |
| **Prueba tolerante del London VAAC (Francis et al. 2012, umbrales de Falconieri et al. 2018) sobre las huellas VOLCAT de Chillán, nov-2026** (`docs/own_volcat/vaac_londres/`, criterio commiteado antes de medir, misma vara del detector del 17-11) | Método completo (pruebas 1 a 5, 10,8 µm = C14, cielo despejado empírico, T_ref 255 K): 2 de 35 cuadros de prueba, 0 de 82 píxeles en la huella, 3 de 120 falsas alarmas; ninguna de 12 configuraciones cumple (C13 y T_ref 215 K tampoco). Sin filtros (pruebas 1 a 3): 83 % de los cuadros con 63 % de falsas alarmas; control pareado por BT C14: 21 % de la huella marcada contra 8 % del mismo lugar sin pluma (C13: 20 % contra 2 %) | resultado negativo publicable: la suma (BT11 − BT12) + (BT11 − BT8,4) baja ~0,4 K en la pluma, sobre todo por el 8,4 µm, pero el suelo volcánico ya la pone en 2 a 3 K y la nieve y las nubes bajo +1,5 K; el filtro β no puede confirmar una pluma tan tibia como el cielo despejado y la coherencia 3 × 3 borra huellas de pocos píxeles. Un método calibrado para nubes distales sobre mar no transfiere a plumas chicas de cráter |
| **β(7,3/11) fuera de muestra en Chillán (indicio nocturno de H3), 20-10 a 19-11-2026** (`docs/own_volcat/beta73/`, criterio commiteado antes de medir) | 49 pares huella VOLCAT contra control pareado por BT11 (7 de noche, 42 de día), cielo despejado empírico. Noche: AUC β73 0,82 [0,62; 0,97] pero anillo sin ceniza 0,90 y 1 de 3 días a favor; día: AUC 0,41 [0,15; 0,63]. Diagnóstico posterior: la noche positiva (10-11) tenía 3 veces más vapor sobre 600 hPa (GFS) y C10 cae igual a 40 km de la pluma; en los 49 pares, ρ = −0,58 entre humedad GFS y BT10 − BT14 lejos de la huella | resultado negativo publicable: noche no concluyente y día falsado. La banda de 7,3 µm a 2 km mide la humedad del día (5 a 15 K entre días), no el vapor de una pluma chica; con cielo modelado, β73 "separa" por aritmética de la razón (Δτ no separa) |
| **H10: dirección de la huella VOLCAT de Chillán contra la pluma vista por el OVDAS, oct-nov 2026** (`docs/own_volcat/direccion_pluma/`, criterio commiteado antes de medir; episodios de 15 REAV y el RAV del 06-11 de SERNAGEOMIN, públicos) | Viento GFS 0,25° al nivel de la columna contra dirección REAV: 3 a 36° en 6 de 7 casos con viento > 3 m/s (62° en uno). Huella VOLCAT (centroide de objetos anclados, con y sin corrección de paralaje): 25-10, 5 escenas, 181° contra REAV SE 135° (Δ 45,5 a 47,4°, borde del umbral de 45°); 28-10, 1 escena, 170° contra REAV NO y viento N (Δ 143 a 170°); 28-10 anochecer y 10-11, huella SE a E con viento NNE a NE. El 27-10 (columnas de 960 a 2.000 m documentadas) VOLCAT no dibujó objeto anclado en 42 cuadros. Señal en el sector REAV contra control pareado por BT11: AUC BTD 0,68 (25-10, 19 escenas) y 0,70 (27-10, 8 escenas), sector opuesto 0,56 a 0,57; ningún píxel con BTD < −1 K | H10 **no concluyente** con dos jornadas; señal en el sector REAV **"tampoco ahí"** (bajo 0,70 por menos de 0,02). La huella queda siempre entre S y E sople hacia donde sople, y la pluma es casi transparente en el split-window también en su sector verdadero. Desviación: sólo escenas L1b ya en disco (ancho de banda) |
| **H9: calor a 3,9 µm y rayos GLM contra las detecciones VOLCAT de Chillán, 20-10 a 19-11-2026** (`docs/own_volcat/calor_rayos/`, criterio commiteado antes de medir) | Anomalía A = (BT3,9 − BT11,2) cráter menos anillo, controles Antuco y Longaví; 1.730 escenas ABI. Momento: noche AUC 0,46 [0,20; 0,64] con 16 positivos en 3 días (se falsa), día 0,61 con controles 0,56 y 0,58 (se falsa). Contexto: 71 % de los cuadros nocturnos despejados de Chillán sobre el p99 de los controles (5,56 K) contra 2 % y 0 %, encendido desde el 24-10. Arranques: 1 de 7 con subida contra 17 % de base. Rayos: 0 de 100 positivos con destello a ≤ 30 km contra 8,8 % de los controles; serie de Lightning-v1 igual a GLM-L2-LCFA crudo (26 de 26) | El calor del cráter es un estado (colada activa), no el gatillo de cada detección; los rayos no participan. Deja un indicador térmico propio que el FDCF no vio, candidato a capa aparte, no a gatillo de ceniza |
| **H11: terreno del cielo despejado, filas de volcán (SECO 2 Tabla 4) y atajo de SO₂ (ec. A5) en Chillán, 22-10 a 14-11-2026** (`docs/own_volcat/reproducir_volcat/`, criterio commiteado antes de medir; lectura de la CDR de VOLCAT 2022 en el mismo directorio) | 66 pares huella VOLCAT contra el mismo lugar y minuto sin pluma (733 píxeles, 10 días), modelo radiativo propio con nube negra por nivel (SECO 1, ec. 1 a 3), 120.944 píxeles calculados directo. Bandera CF ≥ 3: positivos 0,62, controles 0,66; de día 0,71 / 0,83 (el GFS pone la cumbre a 1,5 a 1,9 km y el cielo despejado queda ~9 K más tibio que la cumbre), de noche 0,29 / 0,00. A5: 0 de 733 píxeles en los dos (βtot(7,3/11) mediana ~0,15). βtot(12/11): AUC 0,58 [0,54; 0,64], anillo 0,51. Prefiltros de SECO 1: AUC 0,52 | **No concluyente** según el criterio. De día el error de terreno basta para la bandera de nube que piden las filas de volcán, con o sin pluma; ninguna compuerta espectral pública separa la pluma. Lo que decide en VOLCAT queda en sus PDF no públicas (etapa 2) |
| **Etapa 2: SECO propio entrenado con VOLCAT como etiqueta, Chillán 20-10 a 19-11-2026** (`docs/own_volcat/reproducir_volcat/`, criterio commiteado antes de medir) | 795 scans (100 cuadros VOLCAT anclados en 10 jornadas, 655 sin pluma, 40 del manto del 16-11), disco de 40 km, validación dejando una jornada afuera. Cadena pública de SECO 1 y 2 (prefiltros, Bayes ingenuo con 3 clasificadores, objetos, CF, robustez, Tabla 4) con la probabilidad por píxel entrenada con VOLCAT. Rejilla del modelo radiativo validada contra cálculo directo (p95 0,20 K en C14). SECO propio: 0 de 100 cuadros, 0 de 655 falsas alarmas, 0 de 40 en el manto; probabilidad mediana de los objetos con pluma 1,6 % (máximo 34 %) contra 80 % exigido. Bosque aleatorio (informativo): 38 de 100, falsa alarma 4,3 % (máximo 15 en una jornada), coincidencia 64 % | **No cumple.** Con las plumas de Chillán como entrenamiento la evidencia espectral no pasa de ~16 veces el prior; VOLCAT necesita sus PDF entrenadas con MODIS (no públicas) o una señal temporal no probada aquí |
| **H12: Test 3 original del VAAC de Londres (Francis et al. 2012, ec. 3: BTD < +0,7 K y BTD < BTD_clr − 1,0 K) en Chillán, 22-10 a 14-11-2026** (`docs/own_volcat/reproducir_volcat/`, criterio commiteado antes de medir) | 66 pares de H11 (decide) y 85 pares nuevos de E2 (réplica, corregido tras la revisión), cielo despejado del modelo propio; control de terreno con la huella trasladada a Antuco y Nevado de Longaví (10.458 píxeles más) y al llano. AUC del margen 0,58 [0,54; 0,71], anillo 0,49; cuadros con T3 pluma / control 0,76 / 0,52 (día 0,87 / 0,64; noche 0,36 / 0,07); cumbres 0,35, llano 0,03. Brecha BTD_clr − BTD: 0,85 K con pluma, 0,61 K sin pluma, 0,32 K en cumbres, 0,00 K en el llano. Escenas de E2: objeto T3 anclado en 83 % con pluma y 60 % sin pluma. Filtro β (ec. 5) y 6 de 9 no lo arreglan (6 de 9 por escena: 35 % contra 35 %) | **No concluyente** según el criterio: no separa, y el control de cumbres no tuvo el error de Chillán (BT11 despejado − observado 2 a 3 K contra 8 a 9 K con la misma altura GFS), así que no pudo cerrar "mide el terreno". La brecha que el test exige sobre 1 K ya es ~0,6 K sin pluma en la huella; la pluma agrega ~0,25 K. Con esto quedan probadas las compuertas IR publicadas de VOLCAT y del VAAC de Londres |
| **H13: cambio entre cuadros consecutivos de 10 min en la huella VOLCAT de Chillán, 21-10 a 14-11-2026** (`docs/own_volcat/temporal_h13/`, criterio commiteado antes de medir; datos en `D:\goes_cache\h13\`) | Secuencias ABI completas de los 12 tramos con pluma anclada (±60 min) y 30 min de historia de los días candidatos (1.527 escenas por ventana). 18 variables por píxel: cambio contra el cuadro anterior, contra la mediana de los 3 previos y persistencia del signo, de BT11, BTD(11−12), εtot(11), βtot(12/11), βtot(8,5/11) y βtot(7,3/11), con cielo despejado modelado interpolado en el tiempo. 72 pares huella contra el mismo píxel y minuto en un día sin pluma pareado por BT11 (9 jornadas, 865 px). AUC máximo 0,582 (Δ3 BT11 y Δ3 ε(11)), anillo 0,54 a 0,55; con pareo en t − 30 min, máximo 0,521. 23 de 26 cuadros sin control: todos los candidatos más fríos que el positivo (3 a 10 K). Bosque aleatorio informativo no completado (memoria y disco) | **Se falsa.** Lo temporal no rescata lo que lo espectral no ve: los cambios de 10 a 30 min con pluma son del tamaño de los del cráter sin pluma. Los cuadros con pluma VOLCAT están más tibios en la cumbre que los días sin pluma a la misma hora |
| **H14: anatomía de los archivos de evento VOLCAT GOES-19 de Chillán (firma espectral que informa VOLCAT mismo), 13, 14 y 18-11-2026** (`docs/own_volcat/eventos_h14/`, criterio commiteado antes de medir; archivos de SSEC de acceso restringido, sólo números derivados en el repo) | 60 cuadros, 4 eventos (13-11 `VCB`; 14-11 12:40, 14-11 16:30 y 18-11 `ASHPLUMEPUFF`), 769 píxeles publicados. Primeros cuadros con firma total ≥ 0,5 en la mayoría de los píxeles: 0 de 4 (máximos 0,0004; 0,046; 0,020; 0,67). Firma de onda larga: 99,35 % bajo 0,05, máximo 0,42, también a ≤ 10 km del cráter. Firma total ≥ 0,5 en 12 % de los píxeles, sólo con sol bajo (29 % a 70 a 85° de cenital, 0 % de noche). 0 rayos en 4 redes; calor ≥ 10 MW el mismo día en 3 de 4 aperturas. Nuestra huella del PNG cae 1 fila al S y 1 columna al E de `event_idx` (IoU 0,19 a desfase 0, 0,42 corregido; 48 cuadros del 14-11) | **Compatible con H14, sin fuerza para sostenerla** (4 eventos; hacen falta ≥ 10). VOLCAT abre y sostiene estos eventos sin firma de ceniza en onda larga y sin un núcleo con firma: lo que decide es el objeto y el seguimiento. Supone 1 = firma fuerte (escala sin documentar) |
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
- **G2: el perfil de otro momento no da error, da otra altura (nov-2026):** la
  altura sale de buscar la BT del tope en el T(z) del GFS. Open-Meteo guarda
  sólo ~2 días hacia atrás y, para un scan más viejo, igual devuelve "la hora
  más cercana", que puede ser de otro día; `fetch_gfs_profile` lo registraba en
  el log y la escena lo usaba sin mirar. El árbitro de viento ya rechazaba su
  perfil viejo (`MAX_WIND_AGE_H` = 3 h); el de temperatura no tenía guard. Fix
  en `scene.acquire_ash_scene`: (a) `MAX_PROFILE_AGE_H` = 3 h, medido entre la
  `valid_time` del perfil y el scan, sin confiar en el gap que reporta el
  fetcher; hora ilegible ⇒ no se reporta. 3 h no es una tolerancia física del
  T(z) medida por nosotros: es la misma regla del viento y el semiancho del
  ciclo de 6 h del GFS archivado. (b) `profile_fn` inyectable en BT-matching y
  Wen-Rose, para pasar `gfs_archive.fetch_gfs_profile_archive` en eventos
  viejos (mismo diseño que `wind_profile_fn`). (c) Perfil sin tropopausa ⇒ no
  se reporta: con un segundo proveedor el riesgo latente de la FICHA §B.8.1
  (guard de runaway en +inf) dejaba de estar cubierto por "Open-Meteo no trae
  nulls". En NRT nada cambia: Open-Meteo es horario y el gap queda bajo 30 min.
  Implicancia para el paper: los casos de la §3 se corrieron dentro de las
  48 h de Open-Meteo, así que sus perfiles eran los del día; desde ahora un
  caso histórico sin GFS archivado sale `no_data` en vez de una altura con la
  atmósfera equivocada. Verificado por mutación (desactivar el guard rompe 3
  pruebas; ignorar `profile_fn` rompe 1).

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
(`adv_ambiguous`) implementados, pero el NÚMERO aún sin validar en evento real. · altura de eventos de más de ~2 días sólo con
GFS archivado inyectado (`profile_fn`); sin él el retrieval no reporta (G2).

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
