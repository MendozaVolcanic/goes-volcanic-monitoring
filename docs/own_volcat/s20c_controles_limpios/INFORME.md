# S20c: controles limpios para las pruebas pareadas (23-11-2026)

Criterio `criterio_2026-11-23.md` (commit `b06c711`), enmiendas 1 y 2 con sus ensayos en seco (commit `5f295a5`),
ambos subidos antes de medir. Medición: `scripts/s20c_medir.py medir`; salidas en `resultados/s20c_resumen.txt`,
`s20c_resultado.json`, `s20c_por_cuadro.csv`, `medir.log`. Lo marcado "post hoc" se calculó después de medir y no
decide nada.

## 1. Respuesta corta, para geólogo

**La pregunta.** Las pruebas pareadas que no encontraron firma infrarroja de la pluma de Chillán (paso 2, H3, β73,
VAAC de Londres, H13, y H11 y H12, que heredan los pares de H3 y β73), ¿salieron "sin firma" porque sus controles
"sin pluma" también tenían pluma?

**Lo que se encontró antes de medir: por qué los controles caían en días activos.** Los días en que VOLCAT publica
Chillán son los días despejados. Por la tarde, la máscara de nubes de NOAA (ACMF) da cielo despejado sobre el llano
y la precordillera en 57 a 67 % de los cuadros de los días positivos, y en sólo 4 a 7 % de los cuadros de los días
sin actividad, tanto de fines de septiembre como de noviembre. Además, los cuadros despejados de antes de la actividad
(21-09 al 21-10) están, aun el más parecido, **9 K más fríos** en BT11 que los positivos a la misma hora (nieve y
sol de fin de invierno).
Con la regla vieja, "BT11 parecida a 3 K y mismo minuto", el único control posible era otro día despejado de
noviembre, y esos eran días con el volcán activo. **La contaminación de MET-01 no fue mala suerte: la regla la
imponía.** Por eso tampoco se puede repetir esa regla con días limpios (cobertura de 3 a 27 %).

**La medición.** En su lugar: cada cuadro despejado (positivo o no) contra la línea base de su propio píxel en los
días limpios (21-09 al 21-10), y la temporada restada con cuadros despejados de días sin actividad de fines de octubre
y noviembre (placebo), a ±60 min.

- **En las seis pruebas la BTD de la huella queda bajo el placebo**, hacia la ceniza: entre −0,23 y −0,42 K. En las
  tres pruebas válidas (H3, H13 y H11/H12) esa diferencia es **0,15 a 0,25 K mayor** que la que daba el control
  original. Equivale a una capa de ε ≈ 0,13 a 0,16 sobre toda la huella, del orden de lo que midió H29 lejos del
  cráter (f·ε ≈ 0,12).
- **No alcanza la regla.** p = 0,072 (H3), 0,066 (H13) y 0,054 (H11/H12), con poder de 6 a 16 % para la capa de
  referencia (ε 0,10). Veredicto: **SIN PODER** en las tres. Paso 2, β73 y Londres quedaron **INVÁLIDAS** desde el
  ensayo en seco: tienen tres días positivos despejados y casi ningún día libre despejado a esas horas, así que la
  permutación no tiene con qué variar.
- **Los controles viejos se parecen a los positivos, no a los días libres.** Puestos en el lugar del positivo, los
  controles originales también quedan bajo el placebo (BTD −0,10 a −0,22 K; p 0,05 a 0,23). Con la huella comparada
  contra su anillo en el mismo cuadro (sensibilidad que cancela sola la temporada: en los días libres da 0,0 K), los
  positivos quedan 0,35 a 0,38 K bajo su anillo (p ≤ 0,001 en las tres válidas) y los controles originales, 0,06 a
  0,27 K en BTD y 1,7 a 4,0 K más fríos en BT11 (p 0,001 en H3 y H11/H12).
- **El cambio en 10 min (la variable de H13) sigue en el azar** con controles limpios (ΔBTD y ΔBT11, p de dos colas
  0,33 a 0,89).

**En una frase:** el resultado apunta a que los controles viejos estaban contaminados (con días limpios la diferencia
crece, en el sentido de la ceniza, en las seis pruebas, y los controles viejos se comportan como positivos), pero con
estos pocos días despejados la prueba principal no tiene poder para afirmarlo con la regla escrita antes; el "sin
firma" de esas pruebas **no puede leerse como ausencia de firma**, y tampoco queda demostrado lo contrario.

## 2. Qué se hizo y por qué

### 2.1 Positivos, huellas y pozos

- Positivos: los pares de cada prueba leídos de sus salidas crudas (`scripts/s20c_pares.py`,
  `resultados/pares_originales.csv`): paso 2, 46; H3, 37; β73, 49; Londres, 45; H13, 72. H11/H12 = H3 ∪ β73 (prioridad
  H3, como `comun_h11.pares()`), 66.
- **Huellas rehechas** para todos con el decodificador de H29 y el corrimiento de H14 (1 fila al N, 1 columna al O),
  porque las del paso 2 y Londres no quedaron guardadas y las de H3 y β73 traen el corrimiento de MET-03. Píxeles a
  50 km o menos del cráter, **sin el bloque de 3 × 3 del cráter** (42, 46): el cráter estaba frío antes del 24-10 y
  caliente después, y ese cambio no es pluma. Las huellas guardadas de H3 y β73 entran como sensibilidad S3.
- Pozo limpio: 21-09 al 21-10, antes del primer VOLCAT y del VCB del 22-10. Placebo: los 14 días del 22-10 al 21-11
  que H24 no excluye (23, 26 y 31-10; 01 a 05, 09, 15, 17, 19, 20 y 21-11).
- Sólo 11 y 12 µm (los únicos canales de los cubos de septiembre y octubre).

### 2.2 Dos diseños descartados en seco (sin leer resultados)

1. **Diseño 1, la regla vieja con el pozo cambiado** (`seco_v1_pareo.*`, `diag_cobertura_v1.log`): el mejor control
   limpio queda a 9 K de BT11 del positivo (cuartiles 8 y 12 K) y más frío; cobertura 3 a 27 %. Los días placebo
   están despejados en 3 a 9 % de esos minutos, así que un placebo "cualquier cielo" mide nubes.
2. **Diseño 2 con la regla E1 al 80 %** (`seco_v2a_E1_80.*`, `diag_acmf_v2.log`): 0 a 3 unidades por prueba.
   La enmienda 2 eligió la menor relajación que da 10 unidades y 2 días en las seis pruebas: **E1 al 60 % y ventana
   de ±60 min** (`diag_acmf_ventana.log`), más una regla de nulo degenerado (menos de 1.000 réplicas válidas o menos
   de 50 valores distintos invalida la prueba).

### 2.3 Diseño medido

- Anomalía de un cuadro despejado: mediana sobre la huella de [v − línea base del píxel], con la línea base = mediana
  de los cuadros despejados del pozo limpio a ±60 min (3 días o más por píxel).
- Referencia de la temporada: mediana de la misma anomalía en los cuadros despejados de los 14 días libres a ±60 min
  (3 cuadros o más, de 2 días o más).
- S = mediana sobre los positivos de (anomalía del positivo − referencia).
- Nulo: 2.000 réplicas que cambian cada día positivo entero por un día libre sorteado.
- Control positivo: capa de ε 0,05 a 0,30 a 4,5 km (T del GFS), β 0,70, pintada en esos días libres y pasada por todo
  el procedimiento.
- E_orig: la diferencia contra el control que eligió la prueba vieja, sobre las mismas unidades.
- Chequeo C: el control original (si cae en día activo) en el lugar del positivo.

## 3. Resultados

### 3.1 Ensayo en seco final (antes de medir)

| Prueba | Unidades (de) | Días | Falsa alarma | Nulo: válidas / distintos | Poder ε 0,05 / 0,10 / 0,15 / 0,30 | Estado |
|---|---|---|---|---|---|---|
| Paso 2 | 11 (38) | 3 | 0,000 | 283 / 2 | artefacto | INVÁLIDA, nulo degenerado |
| H3 | 12 (34) | 3 | 0,038 | 1.411 / 72 | 0,10 / 0,06 / 0,14 / 0,95 | válida |
| β73 | 13 (43) | 3 | 0,000 | 967 / 13 | 0,18 / 0,43 / 0,92 / 1,00 | INVÁLIDA, nulo degenerado |
| VAAC de Londres | 11 (40) | 3 | 0,000 | 967 / 13 | 0,18 / 0,57 / 0,92 / 1,00 | INVÁLIDA, nulo degenerado |
| H13 | 30 (66) | 5 | 0,000 | 1.431 / 88 | 0,06 / 0,07 / 0,18 / 1,00 | válida |
| H11/H12 | 24 (60) | 5 | 0,059 | 1.587 / 136 | 0,11 / 0,16 / 0,65 / 1,00 | válida |

### 3.2 Principal: BTD (11 − 12 µm)

| Prueba | S (K) | p | E_orig (K) | S − E_orig | AUC orig → corregido | Chequeo C (K, p) | Veredicto |
|---|---|---|---|---|---|---|---|
| H3 | −0,355 | 0,072 | −0,187 | −0,17 | 0,29 → 0,14 | −0,10 (0,23) | **SIN PODER** |
| H13 | −0,417 | 0,066 | −0,268 | −0,15 | 0,33 → 0,15 | −0,22 (0,053) | **SIN PODER** |
| H11/H12 | −0,334 | 0,054 | −0,086 | −0,25 | 0,41 → 0,22 | −0,18 (0,059) | **SIN PODER** |
| Paso 2 | −0,235 | (nulo degenerado) | −0,170 | −0,07 | 0,37 → 0,24 | 0,00 | INVÁLIDA |
| β73 | −0,312 | (nulo degenerado) | +0,059 | −0,37 | 0,53 → 0,28 | −0,29 | INVÁLIDA |
| VAAC de Londres | −0,232 | (nulo degenerado) | −0,204 | −0,03 | 0,35 → 0,28 | −0,09 | INVÁLIDA |

p de Holm sobre las seis: 0,21 en las tres válidas. AUC = P(positivo > control) por píxel; bajo 0,5 es hacia la
ceniza. "Corregido" = 0,5 + AUC contra la línea base − (AUC del placebo − 0,5). Las seis filas comparten positivos.

**Lectura de cada columna.**
- **Temporada.** El placebo queda **+0,10 a +0,21 K** sobre la línea base limpia (en noviembre la BTD despejada de esos
  píxeles es más alta que a fines de septiembre); los positivos quedan entre +0,02 y −0,29 K. Sin restar la
  temporada, la señal se esconde: por eso el AUC "contra días limpios" solo (0,21 a 0,54) dice poco.
- **E_orig.** Con la huella corregida y sólo cuadros despejados, los pares viejos ya daban la BTD del positivo 0,09 a
  0,27 K bajo su control en H3, H13 y H11/H12 (AUC 0,29 a 0,41). Ninguna de esas pruebas usaba la BTD como variable
  decisora (H3 usaba ε y razones β; H13, cambios en 10 min; H12, BTD contra cielo modelado), así que no es una
  contradicción con sus informes: es una diferencia que estaba y no se miró así.
- **Por día** (H11/H12, `s20c_por_cuadro.csv`): 28-10 −0,37 K, 29-10 −0,45, 08-11 −0,42, 14-11 −0,31 y 10-11 −0,04.
  No lo hace un solo día.
- **Equivalencia** (post hoc, `posthoc_equivalencia.json`): la mediana de S con una capa pintada en días libres es
  −0,23 a −0,26 K para ε 0,10 y −0,37 a −0,39 K para ε 0,15. Lo observado (−0,33 a −0,42 K) corresponde a ε ≈ 0,13 a
  0,16 sobre toda la huella.

### 3.3 Sensibilidades (informativas)

| Variante | H3 | H13 | H11/H12 | Lectura |
|---|---|---|---|---|
| S1, huella contra anillo, BTD | −0,36 (p 0,0007) | −0,38 (p 0,0007) | −0,35 (p 0,0006) | El placebo da −0,02 a 0,00 K: el anillo cancela la temporada. Positivos bajo el anillo en las tres |
| S1, chequeo C (controles viejos) | −0,27 (p 0,001) | −0,06 (p 0,18) | −0,15 (p 0,001) | Los controles viejos también |
| S1, huella contra anillo, BT11 | −1,6 (p 0,13) | −2,6 (p 0,0007) | −1,6 (p 0,085) | Huella más fría que el anillo |
| S1, chequeo C, BT11 | −4,0 (p 0,001) | −1,7 (p 0,12) | −3,3 (p 0,001) | Controles viejos aún más fríos que su anillo |
| S2, sin exigir despejado | +0,20 | 0,00 | +0,09 | Domina la nube, como predijo el ensayo en seco: no es medición |
| S3, huellas guardadas (sin corrimiento) | −0,33 (p 0,072) | igual a la principal | −0,21 (p 0,057) | Con la huella corrida 1 píxel la señal se diluye en β73 (−0,04) |
| S4, con el cráter | −0,42 (p 0,072) | −0,49 (p 0,0007) | −0,39 (p 0,0497) | Algo más fuerte con el cráter dentro |
| S5, ΔBTD y ΔBT11 (cambio en 10 min) | −0,07 / −0,03 | −0,04 / +0,02 | −0,06 / −0,03 | En el azar (p de dos colas 0,33 a 0,89) |
| S5, BT11 | +5,6 | +3,4 | +5,6 | Los positivos están más tibios que los placebos despejados (p de la cola alta 0,05 a 0,18): la selección de días despejados y tibios que mostró el seco; no es pluma |

En S1 los nulos de paso 2, β73 y Londres son los mismos degenerados de la principal; sus p no se leen.

## 4. Veredicto por prueba

| Prueba | ¿Sube la diferencia con controles limpios? |
|---|---|
| **H3** | Sube en el sentido de la ceniza (−0,19 → −0,36 K; AUC 0,29 → 0,14), p 0,072, poder 0,06: **SIN PODER** |
| **H13** (BTD) | Sube (−0,27 → −0,42 K; AUC 0,33 → 0,15), p 0,066, poder 0,07: **SIN PODER** |
| **H13** (su variable, el cambio en 10 min) | **No sube**: ΔBTD −0,04 K, p de dos colas 0,49; sin poder medido para esta variable |
| **H11 y H12** | Sube (−0,09 → −0,33 K; AUC 0,41 → 0,22), p 0,054, poder 0,16: **SIN PODER** |
| **Paso 2** | Descripción: −0,17 → −0,24 K. **INVÁLIDA** (nulo degenerado) |
| **β73** | Descripción: +0,06 → −0,31 K. **INVÁLIDA** (nulo degenerado) |
| **VAAC de Londres** | Descripción: −0,20 → −0,23 K. **INVÁLIDA** (nulo degenerado) |

Ninguna prueba cumple CONTROL CONTAMINADO (p ≤ 0,05 y S ≤ E_orig − 0,10 K) ni NO ERA ESO (azar con poder ≥ 0,80).
Las tres válidas cumplen la segunda mitad de CONTROL CONTAMINADO (S ≤ E_orig − 0,10 K) y quedan a p 0,054 a 0,072 de
la primera.

## 5. Lo que esto no dice, y explicaciones que compiten

- **No dice que sea ceniza.** La huella más fría y con BTD más baja que su anillo, en días activos (positivos y
  controles viejos) y no en días libres, también la daría una nube orográfica sobre la cumbre en tardes despejadas, o
  cualquier cosa que VOLCAT siga desde el cráter. Es la misma reserva de H29.
- **Cuadros de tarde y noche.** Las unidades válidas son casi todas de 20:40 a 01:20 UTC (17:40 a 22:20 de Chile); los
  positivos de mediodía se cayeron porque no hay días libres despejados a esas horas. El resultado habla del
  atardecer y la noche, no del mediodía.
- **E1 al 60 %.** Con 40 % de terreno bajo nublado, puede haber nube que la regla no ve. Se aplica igual a positivos,
  placebos y línea base.
- **Días libres no es lo mismo que sin pluma.** Si los días placebo tenían emisión no documentada, S se achica: el
  sesgo va contra encontrar señal.
- **No repite las variables de 8,5 µm, 7,3 µm ni solares** de las pruebas viejas (no hay cubos de esas bandas en
  septiembre y octubre).

## 6. Qué sigue

- Para que la prueba tenga poder hacen falta **más días positivos despejados** con días libres despejados cerca. El
  verano (registro de H24, `h24_verano/REGISTRO_PROSPECTIVO.md`) es la ocasión: más tardes despejadas en los dos lados.
- Con lo que hay, la comparación **huella contra anillo** (S1) es la que cancela la temporada sin placebo y es la que
  separa; si se quiere usar como prueba, escribirla como criterio nuevo y probarla en un evento que no se haya mirado,
  con control de nube orográfica (por ejemplo, la misma comparación en Antuco y Longaví en los mismos cuadros).
- El 10-11 es el único día que no da diferencia; vale mirarlo con la cámara del OVDAS.

## 7. Archivos

- Scripts: `scripts/s20c_pares.py`, `s20c_medir.py` (diseño medido), `s20c_medir_v1_pareo.py` (diseño 1, descartado),
  `s20c_diag_cobertura_v1.py`, `s20c_diag_acmf_v2.py`, `s20c_diag_acmf_ventana.py`, `s20c_posthoc_equivalencia.py`.
- Datos de entrada (sólo lectura, en D:): cubos y ACMF de H23 y H24, GFS de H23 y H24, PNG de VOLCAT. Nada se bajó y
  nada de SSEC entra al repositorio: las huellas se leen del PNG en D: y sólo se guardan conteos y diferencias.
