# H9: ¿VOLCAT dibuja las plumas de Chillán cuando el cráter se calienta o cuando hay rayos?

Fecha: 19-11-2026. Criterio escrito y commiteado antes del primer número:
`C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\Goes\docs\own_volcat\calor_rayos\criterio_H9_calor_rayos_2026-11-19.md`
(commit 5457499, enmienda de orden de descarga 9c109c3). Salida cruda en
`C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\Goes\docs\own_volcat\calor_rayos\resultados\` y scripts en
`C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\Goes\docs\own_volcat\calor_rayos\scripts\`.

## 1. Respuesta corta, para geólogo

**Veredicto de H9, según el criterio:**

| Parte | Pregunta | Veredicto |
|---|---|---|
| Calor, momento (H9a, decide) | ¿Los cuadros con pluma VOLCAT tienen el cráter más caliente que el mismo minuto de otras noches sin pluma? | **Se falsa** (noche: AUC 0,46 [0,20; 0,64]) |
| Calor, día (H9a, extensión) | Lo mismo de día | **Se falsa** (AUC 0,61, pero los dos volcanes de control dan 0,56 y 0,58) |
| Calor, contexto (H9b) | ¿El cráter está caliente durante el periodo, más que una cumbre sin actividad? | **Sí, encendido**: 71 % de los cuadros nocturnos despejados de Chillán, contra 2 % en Antuco y 0 % en Longaví, desde el 24-10 |
| Calor, arranque (H9c) | ¿Cada tramo de detecciones empieza con una subida de calor? | **No coinciden** (1 de 7 tramos con dato, contra 17 % de tasa base) |
| Rayos (H9d, decide) | ¿Hay destellos GLM a ≤ 30 km del cráter en el cuadro o la media hora previa? | **Se falsa** (0 de 100 cuadros con pluma; 8,8 % en los controles) |

**Qué significa.** Desde el 24-10 el cráter de Chillán está caliente casi todas las noches que se le
ve: a 3,9 µm, un píxel de 2 km sobre el cráter queda 7 K más tibio que su entorno respecto de 11 µm, la
firma de material incandescente que ocupa una fracción pequeña del píxel. Calza con lo que informa el
SERNAGEOMIN para la segunda quincena de octubre (aumento de anomalías térmicas, incandescencia nocturna
en el centro de emisión y en la colada de ~880 m). Si el módulo térmico de VOLCAT ve lo mismo que
nosotros, y debería, porque es más sensible, entonces VOLCAT tiene marcado a Chillán como volcán
térmicamente activo **todo el periodo**, y eso puede explicar un trato especial permanente del cráter.

Pero el calor **no elige el momento**. Las noches con pluma VOLCAT y las noches sin pluma tienen el mismo
calor en el cráter (mediana 7,7 K contra 7,1 K), los tramos de detección no arrancan con una subida, y la
mayoría de las noches calientes no tienen ningún objeto VOLCAT. Los rayos tampoco: hubo tormentas a menos
de 30 km del cráter en diez días del periodo, pero ninguna en los cuadros con pluma.

**Para nuestro detector.** Un "modo volcán activo" gatillado por calor en el cráter es fácil de
reproducir y casi no da falsas alarmas en cumbres sin actividad, pero en Chillán quedaría encendido de
forma continua desde el 24-10. No le daría al detector cuándo mirar, sólo dónde. Y aflojar umbrales
donde mira no sirve, porque esta pluma no tiene señal en el split-window ni en las demás pruebas
espectrales que ya medimos: no hay nada que aflojar. **No se propone ese modo para detectar ceniza.**
Lo que sí deja esta prueba es un indicador térmico propio que ve una colada que el hot spot FDCF de NOAA
no vio (0 % en los scans de H7). Eso vale como capa térmica aparte, no como gatillo de ceniza.

## 2. La física de cada medida

**Calor.** La radiancia de Planck a 3,9 µm crece con la temperatura mucho más rápido que a 11 µm. Un
cráter con lava o material incandescente que cubre una parte pequeña del píxel sube mucho más la BT de
C07 que la de C14. Por eso se mide BT7 − BT14 y no BT7 sola, y se compara con un anillo de 8 a 14 km en
la misma escena, que se lleva la atmósfera y el suelo de ese cuadro:
A = máx en la zona del cráter (≤ 6 km) de (BT7 − BT14) menos la mediana del anillo. La zona está corrida
3 km al sur porque ABI navega al elipsoide y una cumbre de 3,2 km aparece 0,93 km más al sur por cada km
de altura. De día C07 suma sol reflejado, por eso decide la noche. Un cielo nublado sobre el cráter apaga
la señal: esos cuadros quedan fuera como "cráter no visible" (BT14 del cráter más de 4 K bajo el cielo
despejado empírico del mismo minuto en ±7 días), no se cuentan como fríos.

**Rayos.** GLM ve destellos ópticos desde arriba de la nube. Una columna de 0,4 a 2,4 km sobre el cráter
(lo que informan los REAV del periodo) rara vez se electrifica tanto como para que GLM la vea; un destello
cerca del cráter también puede ser una tormenta. Se midió igual porque la pregunta era si VOLCAT pudo
usarlo.

**Controles.** Antuco y Nevado de Longaví, cumbres altas en la misma ventana y sin actividad reportada,
con la misma medida. Si el "calor" de Chillán fuera efecto del terreno alto o de la nieve, aparecería
también ahí.

## 3. Datos y escenas resueltas

- **Cuadros VOLCAT**: 4.116 del sector `Chile_Central_2_km`, 20-10 11:50 al 19-11 12:00 UTC (inventario de
  la prueba β(7,3/11)). 100 positivos (objeto de 4 a 500 px anclado al disco de 10 km, sin manto): 81 de
  día, 11 de crepúsculo y 8 de noche, en 10 días. 3.526 negativos limpios.
- **C07 y C14** leídos por ventana de ABI L1b RadF: **1.730 escenas** (los 100 positivos y 1.383
  negativos limpios); 2 sin scan en S3. La descarga fue más lenta de lo previsto (el enlace hacia S3 se
  compartió con otra sesión y los NetCDF vienen en tiras de 24 × 5.424 píxeles, ~2,6 MB por escena) y
  se cortó a las 20:05 según la enmienda: los niveles que deciden H9a (positivos, su hora previa y los
  mismos minutos UTC en ±10 días) están **completos**; quedaron sin bajar 2.384 cuadros del nivel 3,
  sobre todo noches de noviembre y días fuera de los minutos de los positivos.
- **Cráter visible**, umbral 4 K: noche y crepúsculo, 16 de 19 positivos y 281 de 693 negativos leídos;
  día, 74 de 81 positivos y 114 de 690 negativos. Los negativos de día casi nunca dejan ver el cráter con
  la vara de 4 K (ver §6).
- **GLM**: 8.864 versiones de `glm_latest.json` de Lightning-v1 (una cada ~5 min, ventana de 15 min),
  sin error. Cobertura continua salvo tres huecos que suman 43 min (el mayor, 11-11 20:15 a 20:43, sin
  positivos). 3.477 destellos únicos en su radio; 205 a ≤ 30 km del cráter real, en 10 días.

**Contraste contra la salida cruda.**
- GLM: en dos horas se bajaron los 359 archivos GLM-L2-LCFA de `noaa-goes19` y se contaron los destellos
  con la hora bien escalada. 26-10 22 UTC (la hora con más destellos cerca del cráter): S3 26 y
  Lightning-v1 26 a ≤ 30 km, 81 y 81 en la zona que cubren ambos; cada destello de la serie tiene su par
  en S3 a menos de 50 m y su hora real cae en el intervalo asignado (26 de 26). 14-11 17 UTC (tramo con
  plumas VOLCAT): 0 y 0. **La serie se acepta** (`h9_contraste_glm_s3.txt`).
- BT14 de esta descarga contra la del caché del detector (descarga independiente, mismas escenas):
  diferencia mediana de 7·10⁻⁶ K en 40 escenas.
- Ejemplo de la anomalía: 29-10 01:00 UTC (22:00 del 28-10 en Chile, noche cerrada), píxel más caliente
  en −36,905, −71,38 (5 km al sur del punto del cráter, lo esperado por paralaje y tamaño de píxel):
  BT7 281,1 K, BT14 273,1 K; el anillo da BT7 − BT14 = +0,24 K; A = 7,77 K.

## 4. Resultados

### H9a, ¿el calor marca el momento? (decide la parte calor)

Para cada positivo con cráter visible, los controles son los negativos limpios con cráter visible del
mismo minuto UTC en otros días a ±10 días. AUC = probabilidad de que el positivo tenga más calor que su
control; IC 95 % por remuestreo de días.

| Estrato | Positivos (días) | Controles por positivo | AUC Chillán [IC 95 %] | AUC Antuco | AUC Longaví | Veredicto |
|---|---|---|---|---|---|---|
| Noche y crepúsculo (decide) | 16 (3) | 5 | **0,46 [0,20; 0,64]** | 0,34 | 0,37 | **Se falsa** (AUC ≤ 0,60) |
| Día (extensión) | 62 (7) | 2 | 0,61 [0,44; 0,78] | 0,56 | 0,58 | **Se falsa** (el efecto aparece igual en un control) |

- Noche, por día: 28-10 0,64 (7 positivos), 29-10 0,46 (4), 10-11 0,20 (5). Mediana de A en los
  positivos 7,68 K, en sus controles 7,09 K.
- Sensibilidad de visibilidad (no decide): con 2 K, noche AUC 0,68 [0,33; 0,79] con 10 positivos (no
  concluyente); con 8 K, 0,53 [0,26; 0,67] con 18 positivos (se falsa). De día, 0,61 y 0,50, falsada
  en ambas.
- Advertencia: el IC nocturno llega a 0,64, así que no descarta un efecto chico; lo que sí descarta es que
  el calor sea lo que separa los cuadros con pluma de los sin pluma, que es lo que H9 necesitaba.

### H9b, el calor como contexto

Umbral = percentil 99 de A en Antuco y Longaví de noche (623 valores) = **5,56 K**.

| Sitio | Cuadros nocturnos con cráter visible | Mediana A | Fracción sobre el umbral |
|---|---|---|---|
| Nevados de Chillán | 346 | **7,10 K** | **0,71** |
| Antuco (control) | 320 | 0,70 K | 0,02 |
| Nevado de Longaví (control) | 303 | 0,95 K | 0,00 |

- Noches con al menos 6 cuadros visibles: 10; 9 de ellas con más de la mitad de los cuadros sobre el
  umbral. Según la regla, **contexto encendido**.
- **Cuándo se enciende** (descriptivo): con la vara de 8 K, las noches del 20 al 23-10 dan una mediana de
  0,5 a 2,3 K en Chillán, igual que los controles; desde el 24-10, 5,3 a 7,5 K. La vara de 4 K da lo
  mismo para el 21 y el 24 al 27-10 (las noches del 22 y 23-10 quedan sin cráter visible con 4 K).
  Los primeros cuadros VOLCAT anclados del inventario son el 22-10 (uno, a las 01:50 UTC, con el cráter
  tapado) y el 24-10 (uno, de día). El inventario empieza el 20-10, así que no se puede decir si VOLCAT
  dibujaba algo antes del encendido.
- Las noches que preceden o contienen positivos tienen algo más de fracción caliente (mediana 0,81, 6
  noches) que las demás (0,58, 4 noches). Son 10 noches: no se le da peso.

### H9c, arranque de cada tramo

17 tramos de detecciones (positivos con huecos ≤ 30 min). Sólo 7 tienen cráter visible y línea de base
en la hora previa; 1 de esos 7 muestra subida de calor sobre el p95 de los negativos (4,91 K): el tramo
nocturno del 29-10 a las 00:10 UTC. La tasa base, aplicando la misma regla a 245 negativos, es 17 %.
**14 % contra 17 %: los arranques no coinciden con subidas de calor.** La mayoría de los arranques son de
día y diez quedaron sin dato (nube o sin línea de base por el corte de la descarga).

### H9d, rayos (decide la parte rayos)

| Radio | Positivos con rayo en [t − 30, t + 10] min | Negativos limpios con rayo | Pareados por minuto UTC: positivos / controles | Diferencia [IC 95 %] | Veredicto |
|---|---|---|---|---|---|
| ≤ 30 km (decide) | **0 de 100** | 132 de 3.509 (3,8 %) | 0,000 / 0,088 | −0,09 [−0,13; −0,05] | **Se falsa** |
| ≤ 20 km | 0 de 100 | 95 de 3.509 (2,7 %) | 0,000 / 0,052 | −0,05 [−0,10; −0,02] | Se falsa |

Los días con destellos a ≤ 30 km del cráter fueron 21, 22, 23, 26 y 31-10 y 03, 06, 15, 16 y 17-11.
Sólo el 22-10 tuvo además un cuadro VOLCAT anclado, y no en la misma ventana. El día con más destellos
cerca (26-10, 89) no tuvo ninguno.

## 5. Lectura

1. **El calor está, pero como estado, no como gatillo.** La colada y el cráter de Chillán dan una
   anomalía a 3,9 µm casi continua desde el 24-10, que una cumbre sin actividad no da. Es exactamente el
   tipo de señal que el ATBD de VOLCAT (2025, §2.2) dice que "influye" en la detección. Lo más probable es
   que VOLCAT tenga a Chillán como volcán activo todo el periodo y le aplique ahí sus criterios relajados.
   Eso calza con H2 (trato especial cerca del cráter), que sigue abierta, y le da un mecanismo con fecha
   de encendido. Lo que H9 no explica es **cuándo** dibuja: ni el calor por cuadro ni los rayos separan
   los cuadros con pluma de los sin pluma.
2. **Rayos, fuera.** En este periodo las únicas descargas cerca del cráter vinieron con tormentas en días
   sin plumas VOLCAT. Una columna de pocos km no electrifica lo bastante para GLM.
3. **Lo que queda abierto** es lo que ya estaba en el documento madre: los umbrales por volcán y el
   clasificador de VOLCAT, que no son públicos. H9 agrega una pregunta concreta para el correo a Pavolonis:
   si el módulo térmico tenía a Chillán marcado desde el 24-10 y qué cambia en la detección cuando lo está.

**Para el detector propio.**
- Gatillar un modo "volcán activo" con este calor: no. En Chillán estaría siempre encendido y lo que
  aflojaría (umbral BTD, anomalía de fondo, β) ya se probó sin que la pluma aparezca.
- Indicador térmico propio por volcán: sí vale la pena evaluarlo aparte. Separa limpio un volcán activo de
  dos cumbres de control (71 % contra 2 y 0 % de los cuadros nocturnos) y ve una colada que el FDCF no
  marcó. Antes de llevarlo al dashboard haría falta validarlo en más volcanes y contra VRP Chile o MIROVA,
  y pasar por la ficha SDA.

## 6. Límites declarados

- **Muestra nocturna chica.** 16 positivos visibles en 3 días deciden H9a; el IC es ancho. El veredicto es
  el que da la regla escrita antes, no una prueba de ausencia de todo efecto.
- **Corte de descarga.** H9a está completo. H9b y la tasa base de H9c usan lo bajado al corte: las noches
  del 20 al 28-10 están casi completas; las de noviembre sólo en los minutos de los positivos.
- **Visibilidad.** El cielo despejado empírico (los 3 cuadros más tibios del mismo minuto en ±7 días)
  queda alto en la primera semana y de día; por eso las noches del 20 al 23-10 casi no pasan la vara de
  4 K y sólo 114 de 690 negativos diurnos la pasan. Se informó la sensibilidad a 2 y 8 K; ningún
  veredicto cambia de sentido salvo el nocturno con 2 K, que pasa a no concluyente con 10 positivos.
- **Nuestra medida no es la de VOLCAT.** El módulo térmico de VOLCAT, sus umbrales y su efecto en la
  detección no son públicos. Si fuera mucho más sensible que el nuestro, podría tener variaciones por
  cuadro que no vemos; con el cráter ya sobre el umbral casi siempre, no es lo más probable.
- **Rayos vía Lightning-v1.** Se usó su salida publicada, contrastada con S3. Tiene dos defectos que no
  afectan este resultado porque el método los rodea, pero que conviene corregir en ese proyecto: ubica
  "Nevados de Chillan" en las coordenadas de Antuco (−37,411, −71,352), y el campo `time` de cada destello
  suma el desfase int16 sin su factor de escala (0,00038 s), con horas corridas hasta ~9 h. Sus conteos
  "inner/outer" de Chillán no sirven tal como están.
- Las diapositivas CDR de VOLCAT que mencionan rayos no se verificaron; el ATBD 2025 sólo menciona el
  módulo térmico.

## 7. Archivos

| Archivo | Qué es |
|---|---|
| `criterio_H9_calor_rayos_2026-11-19.md` | Criterio y enmienda, commiteados antes de medir |
| `resultados/h9_calor_resultado.txt` | Salida cruda final de calor (H9a, H9b, H9c), corte de las 20:05 |
| `resultados/h9_calor_resultado_corte1_niveles0y1.txt`, `..._corte2_niveles0a2.txt` | Cortes intermedios, para ver que H9a no cambió al sumar datos |
| `resultados/frames_calor.csv` | A, A7 y BT14 del cráter por cuadro y sitio, con clase VOLCAT y cenit |
| `resultados/h9_rayos_resultado.txt`, `resultados/glm_destellos_chillan.csv` | Salida cruda de rayos y destellos con distancia al cráter real |
| `resultados/h9_contraste_glm_s3.txt` | Contraste contra GLM-L2-LCFA de NOAA |
| `resultados/h9_serie.png` | Calor nocturno por sitio con los cuadros VOLCAT, y destellos por día |
| `scripts/fetch_c07.py`, `fetch_glm_lightning_v1.py`, `analisis_calor.py`, `analisis_rayos.py`, `contraste_glm_s3.py`, `figura_h9.py` | Reproducción completa |

Cachés (fuera del repositorio, se pueden rehacer con los scripts):
`C:\Users\nmend\AppData\Local\Temp\claude\11c46882e3e16008\ea70ca80-5f81-4c66-8568-aa962b07902e\scratchpad\c07cache\`,
`...\scratchpad\glm\` y `...\scratchpad\glm_s3\`, bajo la misma carpeta de scratchpad.
