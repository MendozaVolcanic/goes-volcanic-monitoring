# H28, paso 1: la regla propuesta y el criterio con que se la va a juzgar

Escrito el 23-11-2026 por la sesión S19f. Se commitea **antes** de abrir cualquier log de la segunda
mitad de Fuego (19:01 a 23:46 UTC), cualquier log de Mauna Loa, o un segundo archivo de evento de
Chillán. El commit de este archivo es la prueba del orden.

## 0. Qué se sabía de los datos de prueba al escribir esto

- **Fuego, segunda mitad:** no abrí ningún log. Por el informe de H19 (leído después de commitear el
  paso 0) sé tres cosas de esa mitad: que "Temporal selection criteria met for ash" aparece 342
  veces en el paquete entero, que la nube convectiva deja de existir desde las 22:16, y que a las
  23:31 hay una pluma de San Cristóbal conservada con `Time Trend Count: 13` y clasificada
  `Old Volcanic Feature` con índice de historia 15.
- **Mauna Loa:** sólo nombres y tamaños de archivo.
- **Chillán:** los nombres de los 60 archivos (y por lo tanto las horas publicadas y sus huecos), los
  escalares de un archivo (14-11 19:00 UTC, edad 150 min, primera detección 16:30) y la cadena de su
  JSON (15 cuadros desde las 16:30, o sea que la cadena cruza el hueco de las 17:10). Por el informe
  de H20a sé además, en agregado, que la probabilidad publicada pasa de 0,5 en 94 de 769 píxeles,
  casi todos del evento largo del 14-11 y con sol bajo, y nunca de noche.

## 1. La regla propuesta (deducida en Kirishima completo y en Fuego de 14:01 a 18:46 UTC)

VOLCAT publica un objeto de ceniza por una de tres puertas. Ninguna usa la probabilidad del píxel.

### Puerta A: nacimiento por pluma o bocanada anclada a un volcán

- **A1 (anclaje).** En cada cuadro, VOLCAT arma plumas candidatas uniendo objetos espectrales con
  volcanes de su base (bloque `CONSTRUCT_VOLCANIC_PLUMES`, plumas "fuertes" y "débiles"). El renglón
  resumen de cada volcán trae dos números. En el ajuste, las plumas débiles con `MATCH` tienen los dos
  números sobre 1/3 en 9 de 10 casos, y ninguna de las 70 sin `MATCH` los tiene. No sé qué miden
  esos dos números; es una regularidad, no una regla leída.
- **A2 (contraste).** La candidata pasa por pruebas de contraste contra su entorno. Las 12 candidatas
  eliminadas del ajuste menos una fallan la prueba "detailed spatial contrast testing without
  distance check". Las 2 aceptadas la pasan.
- **A3 (tamaño o tendencia).** La única eliminada que pasa A2 tiene 7 píxeles, todos con tendencia
  temporal. Las 2 aceptadas tienen 8 y 9. Con tres casos no se distingue un mínimo de 8 píxeles de
  un mínimo de 8 píxeles con tendencia temporal.
- Una pluma aceptada se publica con alerta (`New Volcanic Feature`, o `Old Volcanic Feature` si la
  historia de alertas ya tenía ese volcán), y abre una cadena nueva en los archivos de evento.

### Puerta B: seguimiento del cuadro anterior ("Temporal selection criteria met")

- **B1 (sólo contra el cuadro anterior).** La comparación con la historia se hace contra el rasgo
  publicado en la imagen anterior, no contra rasgos más viejos.
- **B2 (ley de distancia).** Un objeto del cuadro entra a la comparación fina si está a no más de
  `0,0500 km/s × Δt` del rasgo anterior, donde Δt es el tiempo entre las dos imágenes (3 km por
  minuto: 7,6 km a 2,5 min; 15 km a 5 min; 30 km a 10 min; 45 km a 15 min), o si ya viene enlazado
  píxel a píxel con él (`Kd Group` mayor que 0). El umbral "refinado" es un tercio:
  `Δt / 60` km con Δt en segundos.
- **B3 (parecido mínimo).** De los que entran, cumple el criterio temporal el objeto que solapa algo
  con el rasgo anterior (`Overlap Frac` > 0) o que se le parece algo en emisividad (`Emiss Sim` > 0).
  En el ajuste: 16 de 16 que cumplen y 34 de 34 que no cumplen (sobre objetos con `Selection Opt` 0).
  De esos 50, 44 son objetos de la nube convectiva de Fuego (los evalúa la misma rutina) y 6 son de
  ceniza.
- **B4.** Entre los que cumplen, VOLCAT elige (filtros de vecino más cercano y de polígono) y publica
  el elegido como "spectral feature", clasificado `Old Volcanic Feature`, sin alerta nueva pero con
  archivo de evento. Los filtros de ruido, emisividad, uniformidad y tamaño están apagados para este
  camino en la configuración (juego `temporal criteria`).
- **B5 (la cadena se corta).** Si en un cuadro ningún objeto cumple, el rasgo sale de la comparación
  y el cuadro siguiente no compara nada. Para volver a publicar hay que pasar otra vez por la
  puerta A.

### Puerta C: objeto dentro de una nube convectiva volcánica (sólo Fuego)

Los objetos de ceniza que solapan una nube convectiva volcánica entran con `Selection Opt` 6 y se
agrupan con ella sin criterio temporal. No aplica a Chillán (no hay nube convectiva) y no se prueba.

## 2. Prueba 1: logs que no se usaron para deducir (Fuego 19:01 a 23:46, Mauna Loa completo)

Unidad: una línea de decisión del log. Las tablas salen de `scripts/h28_parse_logs.py` y
`scripts/h28_match_volcan.py` sin tocar; la evaluación sale de `scripts/h28_evaluar_logs.py`.

| Prueba | Qué predice la regla | Cumple si | Falla si |
|---|---|---|---|
| T1 ley de distancia | `Dist Thresh(km)` = 0,0500 × `Time diff(s)` y `Refined Dist Threshold(km)` = `Time diff(s)`/60, en todas las filas | diferencia ≤ 0,08 km y ≤ 0,02 km en 99 % o más de las filas, **en cada caso por separado** | menos de 99 % en cualquiera de los dos casos |
| T2 rama por distancia | fila en rama 3 (lejos) si y sólo si `Dist(km)` > `Dist Thresh(km)` y `Kd Group` ≤ 0; ninguna fila de rama 3 cumple el criterio | 99 % o más de las filas, y 0 filas de rama 3 con criterio cumplido | menos de 99 %, o alguna rama 3 con criterio cumplido |
| T3 parecido mínimo | en filas de rama 1 con `Selection Opt` 0: criterio cumplido si y sólo si `Overlap Frac` > 0 o `Emiss Sim` > 0 | exactitud balanceada ≥ 0,90 con al menos 5 filas de cada clase | exactitud balanceada < 0,90 |
| T4a contraste necesario | toda pluma con `KEEPING` pasó "without distance check" | 100 % de las `KEEPING`, con al menos 1 `KEEPING` | alguna `KEEPING` con esa prueba fallada |
| T5 clasificación | todo grupo de ceniza con `K-d Overlap Count` > 0 se clasifica `Old Volcanic Feature`; todo grupo `New Volcanic Feature` tiene `K-d Overlap Count` = 0 | 100 % de los grupos de ceniza clasificados | algún grupo que lo contradiga |
| T6 sólo el cuadro anterior | `Time diff(s)` de toda fila de historia está entre 0,9 y 1,1 veces la cadencia del caso (900 s Fuego, 300 s Mauna Loa) | 99 % o más de las filas | menos de 99 % |

Exploratorias (se informan, no deciden el veredicto, porque su base en el ajuste es de 3 y 10 casos):

- **T4b:** `KEEPING` si y sólo si pasa "without distance check" y el objeto tiene 8 píxeles o más.
- **T7:** pluma débil con `MATCH` si y sólo si los dos números del renglón resumen son > 1/3.

**SIN DATO no es cumple.** Si una prueba no tiene filas de la clase que la haría fallar (por ejemplo,
T3 sin ninguna fila que no cumpla), se informa "sin poder" y no cuenta a favor.

**Veredicto de la prueba 1:**

- **LA REGLA DE SEGUIMIENTO SE SOSTIENE** si T1, T2, T3, T5 y T6 cumplen en los datos de prueba
  (T3 puede quedar "sin poder" en un caso si cumple en el otro).
- **SE SOSTIENE EN PARTE** si T1 y T2 cumplen pero T3 falla o queda sin poder en los dos casos: la
  ley de distancia es real pero el parecido mínimo no es el que propuse.
- **NO SE SOSTIENE** si T1 o T2 fallan.
- La puerta A se juzga aparte con T4a: **CONDICIÓN NECESARIA CONFIRMADA**, **REFUTADA** o **SIN DATO**.

### Las dos preguntas del instrumento, para la prueba 1

1. *Si la regla fuera falsa, ¿la evaluación lo mostraría?* T1: sí. Mauna Loa tiene cadencia de 5 min,
   que no está en el ajuste; si el umbral dependiera del tamaño del píxel, del área del rasgo o de
   una constante, a 300 s no daría 15,0 km. T3: sólo si hay filas de las dos clases; por eso el
   mínimo de 5 por clase y la exactitud balanceada, y además se corre un **placebo**: la misma
   prueba con la marca "cumple" barajada dentro de cada cuadro (1.000 veces, semilla fija) tiene que
   dar exactitud balanceada cerca de 0,5; si el placebo diera 0,9, la prueba no mide nada. T2 y T6
   son casi tautológicas si VOLCAT imprime lo que calcula: sirven para detectar que leí mal, no para
   probar física.
2. *Si leyera mal un campo, ¿se vería distinto?* Control de integridad en el mismo script: el número
   de líneas `Temporal selection criteria met`, `HISTORY_GROUP2OBJECT`, `KEEPING` y `ELIMINATING`
   contadas con una búsqueda de texto independiente del lector tiene que ser igual al número de filas
   de las tablas. Si el lector pierde o duplica bloques, el control lo marca y la evaluación no vale.
   Control positivo: correr la misma evaluación sobre el ajuste tiene que dar lo que dice la
   sección 1 (16 de 16 y 34 de 34).

## 3. Prueba 2: los 60 cuadros de Chillán (sólo archivos de evento)

Chillán no tiene logs. La regla no se puede evaluar línea a línea; se evalúan sus consecuencias
visibles en los archivos de evento. Lectura de campos validada en el ajuste: en los 7 eventos de
Kirishima, `feature_age` vale 0 en los dos nacimientos que el log marca como pluma aceptada (20:17 y
20:47) y 2,55 a 12,53 min en los cinco cuadros que el log marca como seguimiento; el identificador
del JSON cambia en el segundo nacimiento.

Definiciones: **nacimiento** = cuadro con `feature_age` = 0 (primera detección igual a la propia).
**Continuación** = cuadro con `feature_age` > 0. **Cadena** = cuadros con la misma hora de primera
detección.

| Prueba | Qué predice la regla | Cumple si | Falla si |
|---|---|---|---|
| C0 control de lectura | `feature_age` (min) = (`mean_feature_time` menos `first_detection_mean_feature_time`)/60, y la hora de primera detección del NetCDF es la del identificador del JSON | igual en los 60 (tolerancia 0,05 min) | cualquier diferencia: la lectura de la cadena no vale |
| C1 la cadena no salta cuadros (B1 y B5) | toda continuación tiene publicado, en su misma cadena, el cuadro de la imagen GOES inmediatamente anterior | 100 % de las continuaciones, **o** las que no lo tienen caen justo después de una imagen GOES-19 que no existe en el archivo público de NOAA (se comprueba listando `noaa-goes19/ABI-L1b-RadF`) | alguna continuación cuyo cuadro anterior no está publicado aunque la imagen GOES sí existe |
| C2 ley de distancia (B2) | en toda continuación con cuadro anterior, la distancia mínima entre su huella y la huella anterior es ≤ 0,0500 km/s × Δt | 100 % | alguna mayor |
| C3 solape (B3, mitad visible) | se informa en cuántas continuaciones la huella comparte al menos un píxel con la anterior | informativa | informativa |
| C4 anclaje al nacer (A1) | todo nacimiento tiene `minimum_volcano_distance` ≤ 4 km (2 píxeles de 2 km; en Kirishima los dos nacimientos están a 1,25 y 0,92 km) | 100 % de los nacimientos | algún nacimiento a más de 4 km |
| C5 la probabilidad sube sólo con seguimiento | los píxeles con probabilidad publicada ≥ 0,5 y probabilidad infrarroja < 0,05 están sólo en continuaciones | 100 % de esos píxeles, con al menos un nacimiento de día (cenit solar < 85°) entre los 60 | alguno en un nacimiento |

**Lo que cada prueba de Chillán puede y no puede mostrar (preguntas del instrumento):**

- C1 es la única con poder real para refutar. Ya sé que la cadena del 14-11 cruza el hueco de las
  17:10. Si la imagen GOES-19 de las 17:10 existe, C1 **falla** para esa cadena y la regla B1/B5 tal
  como la leí en Kirishima no describe a VOLCAT en producción (o VOLCAT no escribe archivo de evento
  para todo cuadro seguido, o salta imágenes al procesar en tiempo real). Se informa así, sin
  rescate posterior.
- C2 casi no puede fallar: una pluma pegada a un volcán no se mueve 30 km en 10 minutos, exista o no
  la regla. Se informa como comprobación de consistencia y **no cuenta como evidencia a favor**.
- C4 tiene poco poder por la misma razón que C2 (el archivo es del volcán 357070 porque el objeto
  está cerca), pero puede fallar si un nacimiento aparece ya desprendido.
- C5 distingue "sube por seguimiento" de "sube por el ángulo del sol" sólo si hay nacimientos de día
  con sol bajo. Si no los hay, queda sin poder. Conozco el agregado de H20a, no el reparto por cuadro.
- Si leyera mal `event_idx`, las huellas saldrían vacías o del tamaño de la grilla: el script exige
  que el número de píxeles de la huella por el área de píxel (unos 4 a 6 km² en Chillán) esté dentro
  de un factor 2 de `feature_area`.

**Cuánto de Chillán explica la regla (definición fijada ahora):**

- Un cuadro de **continuación** cuenta como **explicado por la puerta B** si cumple C1 y C2.
- Un cuadro de **nacimiento** cuenta como **no evaluable**: la puerta A decide con variables
  (contraste contra el entorno, tendencia temporal por píxel) que el archivo de evento no trae. Sólo
  se informa si es compatible con el anclaje (C4).
- Una continuación que no cumple C1 con imagen GOES existente cuenta como **no explicada**.

**Veredicto de la prueba 2:**

- **COMPATIBLE:** C0 cumple, y 90 % o más de las continuaciones quedan explicadas.
- **COMPATIBLE EN PARTE:** C0 cumple y entre 50 % y 90 % de las continuaciones quedan explicadas.
- **NO COMPATIBLE:** menos de 50 %, o C0 falla.

El nombre es "compatible" y no "confirmada" a propósito: sin logs de Chillán, lo más que estos
archivos pueden decir es que los 60 cuadros no contradicen la regla. La confirmación de la regla está
en la prueba 1.

## 4. Lo que queda fuera

- No se reproduce el seguimiento con datos GOES propios (lo hace H26; no miré su trabajo).
- No se deduce cómo sube la probabilidad publicada dentro de un objeto seguido. En Kirishima vi que
  los valores publicados se heredan entre cuadros a lo largo del enlace de píxeles (0,41, 0,57,
  0,64, 0,72 se repiten en cuadros sucesivos), pero no encontré la fórmula. C5 sólo prueba cuándo
  sube, no cuánto.
- No se abre `history/volcat_history.hdf` de Fuego antes de la prueba 1.
