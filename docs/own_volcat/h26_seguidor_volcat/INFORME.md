# H26 (S19b): copiar la decisión de VOLCAT en Nevados de Chillán y medir su costo. Informe, 23-11-2026

> **Esto copia una regla, no mide ceniza.** Un acierto habría dicho que reproducimos la decisión de VOLCAT, no que
> hubiera ceniza en esos píxeles.

**Veredicto con la regla escrita antes de medir: SIN PODER.** El control positivo (una pluma sintética anclada de
−3 K inyectada en días sin VOLCAT) se recuperó en 10 de 20 tramos, y la regla pedía 18. Con ese veredicto la prueba
no puede declarar "no copia" con todas las de la ley. La concordancia observada, en cambio, queda lejos de cualquier
lectura favorable: el seguidor recupera **12 de los 769 píxeles** que VOLCAT publicó (1,6 %), con IoU mediano 0,000
en los 60 cuadros de evento. Además se dispara en 7,7 % de los cuadros de los días sin VOLCAT y en 28 % de los de
Antuco sin compuerta.

Criterio: `criterio_2026-11-23.md`, commit `95d6171`, subido antes de correr el seguidor. Enmienda post hoc 1
(diagnóstico del control positivo, escrita antes de calcularlo): `enmienda_posthoc_1_2026-11-23.md`, commit
`6ac919e`. Por qué se hizo: `../RESPUESTA_S18_lo_que_vio_volcat.md`, camino (b). Nada de esto toca `src/` ni el
dashboard.

## 1. Para geólogo

**La pregunta.** Las pruebas anteriores dejaron establecido que VOLCAT no ve la pluma de Chillán en el píxel (su
propia probabilidad infrarroja es menor que 0,05 en 762 de 767 píxeles, H20a). Lo que publica sale de una decisión
sobre un objeto: nace pegado a un cráter con calor, se acepta porque persiste entre cuadros y después se sigue
aunque se despegue del cráter (H14, H19, H20c). Si copiamos esa decisión con nuestros datos de GOES-19, ¿marcamos
los mismos píxeles que VOLCAT y cuánto nos cuesta en falsas alarmas?

**El seguidor, en palabras.** En cada cuadro de 10 minutos, un píxel es candidato si está al menos 1 K más frío en
11 µm que su propia historia despejada a la misma hora y su diferencia 11 − 12 µm bajó al menos 0,5 K (los umbrales
de H17, fijados antes y sin tocar). Los candidatos contiguos forman objetos. El seguidor:

- abre una pista sólo si el cráter tuvo calor de noche (≥ 10 MW a 3,9 µm) en las 24 horas previas;
- exige un objeto chico pegado al cráter que aparezca en dos cuadros seguidos (el criterio temporal);
- desde ahí sigue cualquier objeto que toque al del cuadro anterior, aunque ya no esté pegado al cráter.

Es la secuencia que se le vio a VOLCAT en Kirishima y Fuego, aplicada a la radiancia que tenemos.

**Lo que salió.**

1. **No marca lo que VOLCAT marca.** De los 60 cuadros de evento VOLCAT del 13, 14 y 18-11, el seguidor dispara en
   9 (15 %) y recupera 12 de 769 píxeles de la huella. Los 12 son de un solo tramo: 19:30 a 19:50 UTC del 14-11.
   En los 100 cuadros en que el PNG de VOLCAT muestra un objeto anclado (13 días con VOLCAT), dispara en 5.
2. **Cuesta lo mismo donde no hay nada.** En los 16 días sin VOLCAT que tienen línea base, dispara en 78 de 1.007
   cuadros (7,7 %), repartidos en 5 días. Es **más** que en los días con VOLCAT (4,0 %): no hay asociación, la tasa
   es la del fondo. En las dos cumbres sin actividad, sin la compuerta de calor (que en Chillán está prendida casi
   siempre desde el 24-10), dispara en 28 % de los cuadros de Antuco y 20 % de los de Longaví, en 23 y 22 de 29 días.
   Con su propia compuerta baja a 7,1 % y 3,4 %: la compuerta filtra, pero filtra en las cumbres que no tienen
   calor, no en Chillán.
3. **Por qué el control positivo falla, y qué dice eso.** Una pluma sintética de 6 píxeles y −3 K se recupera
   limpia cuando el cielo de fondo está despejado: en Chillán, los 10 tramos que pasan tienen IoU 0,84 a 1,00 en los
   cuadros 3 y 4. Falla en los demás por dos razones medidas (enmienda 1):
   - **la nube del fondo se traga la pluma**: la escena ya tiene muchos candidatos (nubes que enfrían 11 µm respecto
     del día despejado) y la pluma inyectada queda dentro de un objeto grande. Con más de 70 píxeles no nace la
     pista; con más de 200, no se sigue. En Chillán pasa en 7 de los 10 tramos fallidos: en 6 la pluma queda dentro
     de un objeto de 74 a 428 píxeles y en 1 el objeto (22 píxeles) no alcanza a nacer;
   - **la máscara arrastra otros objetos seguidos**: el seguidor ve la pluma, pero también sigue objetos de ruido
     vecinos y el IoU cae a 0,09 y 0,10 (2 tramos);
   - **el fondo está más tibio que su base**: ni restando 3 K el píxel queda 1 K bajo su línea base (1 tramo).
   En Antuco y Longaví pasan 7 de 20, por las mismas causas. La falla es del fondo de la cordillera en la
   primavera, no del seguidor: donde el cielo está despejado, el seguidor ve y localiza una pluma de −3 K.

**Qué significa para la pregunta de Nicolás** ("¿podemos detectar lo que vio VOLCAT?"):

- **Copiar la decisión de VOLCAT con nuestras radiancias no da los mismos píxeles.** No es un problema de la regla
  temporal ni del seguimiento, porque esas partes funcionan con una pluma sintética en cielo despejado. El problema
  está en la entrada: los píxeles que VOLCAT publica no son candidatos para nuestro seguidor, porque no están más
  fríos ni más bajos en 11 − 12 µm que su propio día despejado (H17 ya los había encontrado 1,3 K más tibios). Si la
  huella de VOLCAT tuviera una firma como la del control positivo, esperaríamos recuperar del orden de la mitad de
  sus píxeles; recuperamos 1,6 %.
- **Lo que elige los píxeles de VOLCAT no es infrarrojo.** Sale de su extracción de objetos (`ASHPLUMEPUFF`,
  "SECO+"), que no es pública. Sin ella, cualquier copia nuestra tiene que inventar los candidatos, y las dos formas
  que probamos fallan. La de frío (R1) no ve la huella. La de "cualquier cambio" (R2) arma objetos demasiado grandes
  en este fondo y casi nunca dispara: 0 de 60 eventos.
- **Lo único que "concuerda" es la geometría.** Una máscara fija, el círculo de 6 km alrededor de la cumbre corrida
  por paralaje y encendida cuando hay calor (R0), recupera 50 % de los píxeles de VOLCAT. Le va igual de bien con la
  huella reflejada en 180° (IoU tolerante 0,76 contra 0,73), así que lo que concuerda es la cercanía al cráter, no
  la forma. Y R0 se dispara en 52 % de los cuadros de los días sin VOLCAT. Esto confirma, con otra prueba, que los
  objetos de VOLCAT en Chillán son casi siempre chicos y pegados al cráter (H14).
- Mi estimación de S18 para este camino era "5 % o menos de un seguidor útil". Con lo medido, la mantengo.

## 2. Comprobaciones de instrumento y controles

| | Pide | Medido |
|---|---|---|
| I1 cobertura | 60 cuadros de evento con C14, C15 y base | 60 de 60 |
| I2 alineación de la huella | mediana de \|BT11 nuestra − BT11 del evento\| ≤ 0,5 K | 0,050 K (p90 0,054 K, 769 píxeles) |
| I3 rango | 180 a 330 K | 215,4 a 322,2 K |
| Nulo no degenerado | el seguidor dispara alguna vez en un control | sí (Antuco y Longaví) |
| Control positivo | ≥ 18 de 20 tramos con disparo en los cuadros 3 y 4 e IoU tolerante ≥ 0,5 | **10 de 20: FALLA** |

Las dos preguntas del instrumento (criterio §5):

1. *Si lo que mide estuviera roto, ¿la prueba fallaría?* Sólo en parte: el control positivo muestra que el seguidor
   localiza una pluma de −3 K en cielo despejado (10 de 10 tramos limpios en Chillán), pero no en escenas con nubes
   o con fondo tibio, que son la mitad de los tramos. Por eso el veredicto es SIN PODER y no NO COPIA.
2. *Si el instrumento estuviera muerto, ¿se vería distinto?* Sí: I1 a I3 pasan, la huella de VOLCAT y nuestra
   ventana miden la misma BT11 a 0,05 K (apuntan al mismo lugar), y el seguidor dispara en los controles.

## 3. Resultados (`resultados/h26_resumen.json`, `resultados/h26_por_cuadro.csv`)

IoU tolerante: con tolerancia de 1 píxel (criterio §4). "Recuperada": píxeles de la huella VOLCAT dentro de la
máscara dilatada 1 píxel, sobre los 769 de los 60 cuadros. FA: fracción de cuadros con disparo.

| Variante | IoU tol. mediano (exacto) | IoU reflejada | Recuperada | Dispara en eventos | Dispara en clase P | FA Chillán, días sin VOLCAT | FA Antuco | FA Longaví |
|---|---|---|---|---|---|---|---|---|
| **R1 (decide)** | 0,000 (0,000) | 0,000 | 0,016 (12/769) | 0,15 (9/60) | 0,05 (5/100) | 0,077 (78/1.007; 5 de 16 días) | 0,071 | 0,034 |
| R1 sin compuerta | 0,000 (0,000) | 0,000 | 0,016 | 0,15 | 0,05 | 0,139 (7 de 16 días) | **0,278** (23 de 29 días) | 0,197 (22 de 29) |
| R2 "cualquier cambio" | 0,000 | 0,000 | 0,000 | 0,00 | 0,00 | 0,007 | 0,000 | 0,006 |
| R0 círculo de 6 km | 0,729 (0,184) | 0,763 | 0,505 | 0,98 | 0,99 | 0,522 (12 de 16 días) | 0,231 | 0,140 |

FA de Antuco y Longaví en las filas con compuerta: con la compuerta de calor de cada cumbre (informativo); la que
decide es sin compuerta (0,278).

Por evento (R1): el `VCB` del 13-11 (11 cuadros, 15 píxeles): 0 disparos. El 14-11 de las 12:40 (7 cuadros, 22
píxeles): 3 disparos y 0 píxeles recuperados. El 14-11 de las 16:30 (41 cuadros, 728 píxeles): 6 disparos y 12
píxeles, todos entre 19:30 y 19:50 UTC (IoU 0,29, 0,89 y 0,33). El 18-11 (1 cuadro, 4 píxeles): 0 disparos.

Por período (R1): de día 53 cuadros de evento (dispara en 15 %) con FA 7,7 %; crepúsculo 5 (0 %) con FA 7,2 %;
noche 2 (1 de 2) con FA 8,3 %.

## 4. Diagnóstico del control positivo (enmienda 1, no decide; `resultados/h26_diagnostico_cp.log`)

| Sitio | Pasan | Disparan con la pluma en la máscara | Causa de los fallidos |
|---|---|---|---|
| Chillán | 10 de 20 | 12 de 20 | 8 sin disparo (6 con la pluma dentro de un objeto de 74 a 428 px, 1 de 22 px que no nace, 1 con el fondo tibio) y 2 con otras pistas en la máscara (rotuladas "fusión" porque el objeto de la pluma pasa de 6 px) |
| Antuco (compuerta forzada) | 7 de 20 | 10 de 20 | 10 sin disparo, 2 por fusión, 1 por otras pistas |
| Longaví (compuerta forzada) | 7 de 20 | 12 de 20 | 8 sin disparo, 4 por fusión, 1 por otras pistas |

El rótulo "sin disparo" del script (clase a de la enmienda) se asigna antes de mirar el tamaño del objeto. La
columna `n_obj_pluma` muestra que en casi todos esos tramos la pluma quedó dentro de un objeto de más de 70
píxeles: es fusión con la nube del fondo, que impide el nacimiento. Los tramos que pasan tienen IoU 0,6 a 1,0.

## 5. Lo que podría estar equivocado

- **Los candidatos.** El seguidor sólo puede seguir lo que sus candidatos le entregan. Usamos "más frío y con BTD
  más baja que su día despejado" porque es lo que la física de la ceniza pide en el infrarrojo; VOLCAT usa otra
  extracción, que no conocemos. Otra definición de candidato podría acercarse más, pero tendría que salir de algo
  distinto de la radiancia de 11 y 12 µm, o de las tablas de VOLCAT, que ya probamos (H15, H16).
- **La tolerancia del IoU favorece las máscaras grandes.** R0 saca 0,73 de IoU tolerante con un IoU exacto de 0,18.
  Por eso la regla exige también la fracción recuperada y ganarle a R0 y al reflejo. Para R1 no cambia nada: da 0
  con o sin tolerancia.
- **El control positivo se eligió en cuadros con la compuerta encendida** (428 tramos elegibles). El criterio no lo
  decía: sin esa condición el seguidor no puede disparar por construcción, y el control habría medido la compuerta y
  no el seguidor. Está dicho aquí y no cambia el resultado (10 de 20).
- **Días sin VOLCAT.** Se cuentan desde el catálogo del PNG y los archivos de evento. Un día con una emisión que
  VOLCAT no marcó queda como "sin VOLCAT" y una detección nuestra ahí cuenta como falsa alarma. El volcán emitió casi
  a diario desde el 24-10 (H24 §5). Las cumbres de control no tienen ese problema y dan tasas iguales o mayores.
- **"16 días".** Hay 17 días sin VOLCAT con cuadros IR; el 20-10 no tiene línea base (es el primer día del caché),
  así que se evalúan 16. El número del encargo era correcto por casualidad.

## 6. Qué sigue (propuesta, no hecho)

- Este camino queda cerrado en lo que se puede hacer con datos públicos. Lo que haría falta es la regla de
  extracción de objetos de VOLCAT (`ASHPLUMEPUFF`/SECO+) o su L2 de Chillán, y eso es una pregunta para Pavolonis,
  no una prueba nuestra. Si Nicolás decide escribirle, la pregunta concreta es: qué píxeles entran como candidatos a
  un objeto `ASHPLUMEPUFF` cuando su probabilidad infrarroja es menor que 0,05.
- VOLCAT queda como capa externa en el dashboard, como está hoy (ficha SDA §A.7). Nada de este seguidor debería
  llegar a producción: copia una regla, no mide ceniza, y su tasa de falsas alarmas es la del fondo.

## 7. Archivos

- `criterio_2026-11-23.md` (commit `95d6171`), `enmienda_posthoc_1_2026-11-23.md` (commit `6ac919e`).
- `scripts\h26_seguidor.py` (criterio) y `scripts\h26_diagnostico_cp.py` (enmienda 1). Reutilizan
  `h17_regla_propia\scripts\h17_comun.py` y `h17_pluma.py` (cachés, línea base, Planck del NetCDF), de sólo lectura.
- `resultados\h26_por_cuadro.csv` (sin posiciones de la huella: sólo conteos e IoU), `h26_resumen.json`,
  `h26_corrida.log`, `h26_diagnostico_cp.csv`, `h26_diagnostico_cp.log`.
- Insumos fuera del repo, sólo lectura: cachés L1b de H17 y anteriores en `D:\goes_cache\`, `D:\goes_cache\h17\
  calor.pkl`, huella `event_idx` en `D:\goes_cache\etapa3_chillan\inventario.npz` (de los archivos de evento de
  `D:\goes_notas\busqueda_2026-11-20\volcat_eventos_357070`, licencia restringida). No se bajó nada nuevo ni se
  escribió nada en `D:\goes_notas\s19\h26\`. Ningún archivo de SSEC entra al repo.

Reproducir, desde
`C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\Goes\docs\own_volcat\h26_seguidor_volcat\scripts\`:

```powershell
python -I h26_seguidor.py
```

```powershell
python -I h26_diagnostico_cp.py
```
