# H28 (S19f): la regla con que VOLCAT sigue un objeto entre cuadros, leída de sus logs y probada en datos que no se usaron para deducirla. Informe, 23-11-2026

**Veredicto de la prueba 1 (logs): SE SOSTIENE EN PARTE.** La ley de distancia del seguimiento es
exacta en los cuatro casos y en tres satélites. La condición de parecido que propuse no es la de
VOLCAT. **Veredicto de la prueba 2 (Chillán): COMPATIBLE**, con 51 de 56 continuaciones explicadas
(91 %) y tres comprobaciones que fallaron por la letra.

Orden de los commits, que es la prueba de que el criterio se escribió antes de medir:
`8b34e36` inventario e hipótesis inicial (antes de leer los informes previos), `8f0ac51` regla y
criterio (antes de abrir los datos de prueba), `9b718f2` enmienda 1 (error de mi lector, antes de
abrir los datos de prueba). Lo decidido después de ver los datos de prueba está rotulado **post hoc**.

Los archivos nombrados sin ruta completa están en
`C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\Goes\.claude\worktrees\xenodochial-pare-413fc0\docs\own_volcat\h28_regla_seguimiento\`
(en el repositorio: `docs/own_volcat/h28_regla_seguimiento/`).

**Qué está en el repositorio y qué no.** En el repositorio quedan los scripts, las evaluaciones
agregadas (`eval_*.json`, `*_resumen.json`, `posthoc.json`), la tabla de atrasos de producción y el
listado de NOAA. Las tablas que transcriben fila por fila líneas de los logs o campos de los archivos
de evento de SSEC **no están en el repositorio porque transcriben datos de SSEC de licencia
restringida** (decisión de Nicolás, 23-11-2026). Están en `D:\goes_notas\s19\h28\resultados\`, con la
misma estructura de carpetas (`ajuste`, `prueba`, `posthoc`): 26 archivos CSV, más las cuatro
evaluaciones completas con sus filas de detalle.

## 1. Para geólogo

**La pregunta.** VOLCAT publicó 60 cuadros con pluma de Nevados de Chillán entre el 13 y el
18-11-2026, en píxeles a los que él mismo da probabilidad de ceniza casi nula. ¿Qué regla lo hace
publicar?

**De dónde salió la respuesta.** Los paquetes de prueba de SSEC no traen el programa, pero sí el
registro que el programa escribe cuadro a cuadro. Ese registro imprime, para cada objeto que
compara con el cuadro anterior, la distancia, el umbral que usó y si lo aceptó. Leí esos números en
Kirishima y en la primera mitad de Fuego, escribí la regla, y después la probé en la segunda mitad
de Fuego y en Mauna Loa (otro volcán, otro satélite, otra cadencia), que no había abierto.

**La regla, en palabras.** VOLCAT publica un objeto por dos puertas distintas, y ninguna mira la
probabilidad de ceniza del píxel.

1. **Puerta de nacimiento.** Un objeto pegado a un volcán de su base se publica como "pluma o
   bocanada" si contrasta lo suficiente con su entorno inmediato (una prueba de forma y de borde, no
   de firma de ceniza). De 14 candidatas en los datos de ajuste aceptó 2. Esta puerta quedó leída
   sólo a medias (ver más abajo).
2. **Puerta de seguimiento.** En la imagen siguiente a una en que publicó algo, VOLCAT busca
   cualquier objeto que esté a no más de **3 km por cada minuto transcurrido** del rasgo anterior
   (30 km si pasaron 10 minutos, 60 km si pasaron 20) y lo hereda como continuación del mismo
   evento. Para ese camino tiene apagados los filtros de ruido, de emisividad, de uniformidad y de
   tamaño mínimo: basta un píxel. No pide que el objeto nuevo se superponga al anterior. Lo publica
   sin alerta nueva, pero escribe el archivo de evento igual.

Dicho como fenómeno: una vez que VOLCAT "vio" algo sobre el cráter, lo que publica en los cuadros
siguientes no es una nueva detección de ceniza, es la continuación de esa primera. La cadena dura
mientras haya algún objeto de su lista dentro del radio, y ese radio crece con el tiempo entre
imágenes. En disco completo (10 min) el radio es 16 veces más área que en el sector de Japón
(2,5 min).

**Cuánto de Chillán explica.**

- De los 60 cuadros, **56 son continuaciones y 4 son nacimientos**. Son cuatro cadenas: 13-11 desde
  las 19:00 (11 cuadros, tipo nube convectiva volcánica), 14-11 desde las 12:40 (7 cuadros), 14-11
  desde las 16:30 (41 cuadros, más de 7 horas) y 18-11 a las 10:10 (1 cuadro).
- **51 de las 56 continuaciones (91 %)** tienen publicado el cuadro inmediatamente anterior y su
  huella está dentro del radio de la regla. Quedan explicadas por la puerta de seguimiento.
- **Las otras 5 continuaciones** vienen después de un cuadro que falta (13-11 19:10 y 20:10; 14-11
  17:10, 20:20 y 23:20). Las cinco imágenes GOES existen en el archivo de NOAA, así que por la letra
  de mi criterio esas 5 no quedan explicadas. Lo que encontré después (post hoc): los cinco huecos
  ocurren justo después de los cinco únicos cuadros que VOLCAT produjo con 30 o 31 minutos de
  atraso; ninguno de los otros 55 llega a 30 (el máximo es 28). VOLCAT en tiempo real se salta una
  imagen cuando va 30 minutos atrasado y sigue desde la anterior. Con esa lectura las 56
  continuaciones siguen a la imagen anterior que VOLCAT procesó.
- **Los 4 nacimientos no se pueden evaluar** con los archivos de evento: la puerta de nacimiento
  decide con el contraste contra el entorno, que el archivo no trae.

**Lo que esto significa para un detector propio.** Para copiar lo que VOLCAT publica en Chillán hay
que copiar dos cosas distintas. La segunda (el seguimiento) es simple y está medida: un radio de
3 km por minuto alrededor de lo último publicado, sin exigir señal. El 93 % de los cuadros publicados
son continuaciones de ese tipo, pero el seguimiento no es una detección: hereda lo que haya decidido la primera. La primera (el
nacimiento) es la que decide si hay o no hay evento, y de ella sólo confirmé una condición necesaria.

**Lo que queda sin explicar.**

1. **La puerta de nacimiento completa.** Sé que la candidata tiene que pasar la prueba de contraste
   detallada (se cumplió en las 2 aceptadas del ajuste y en la única aceptada de la prueba), pero no
   sé qué más pide. Y mi umbral de anclaje (objeto a 4 km o menos del cráter al nacer) falló: dos de
   los cuatro nacimientos de Chillán están a 8,5 y 12,5 km.
2. **La condición exacta dentro del radio.** Propuse "se superpone al rasgo anterior o se le parece
   en emisividad". En la segunda mitad de Fuego, 103 de 341 objetos de ceniza aceptados no cumplían
   ninguna de las dos. El registro distingue dos subcriterios, "(1)" y "(2)"; el segundo acepta
   objetos sin superposición. No pude leer qué pide cada uno. En la práctica, 341 de 351 objetos de
   ceniza dentro del radio fueron aceptados (97 %).
3. **Por qué se corta una cadena.** En Kirishima se cortó en el primer cuadro sin objeto dentro del
   radio. En Chillán no hay registro para comprobarlo.
4. **Cómo sube la probabilidad publicada** dentro de un objeto seguido. En Chillán, 89 de los 90
   píxeles con probabilidad publicada alta y probabilidad infrarroja casi nula están en
   continuaciones, pero 1 está en un nacimiento (18-11 10:10, sol a 82,5° del cenit). No es sólo el
   seguimiento.
5. **La cadena del 13-11** nace por otra puerta (nube convectiva volcánica, con anomalía térmica),
   que no deduje.

## 2. Números

### 2.1 Datos y reparto

| Conjunto | Caso | Cuadros | Para qué |
|---|---|---|---|
| Ajuste | Kirishima 02-07-2025 (Himawari-9, 2,5 min) | 25 | deducir |
| Ajuste | Fuego 03-06-2018, 14:01 a 18:46 UTC (GOES-16, 15 min) | 20 | deducir |
| Prueba 1 | Fuego 19:01 a 23:46 UTC | 20 | probar, con la decisión impresa en el log |
| Prueba 1 | Mauna Loa 28-11-2022 (GOES-17 CONUS, 5 min) | 10 | probar, otro volcán y otra cadencia |
| Prueba 2 | Chillán 13 al 18-11-2026 (GOES-19, 10 min) | 60 | consecuencias en archivos de evento |

### 2.2 Prueba 1, con el evaluador tal como estaba al commitear el criterio

| Prueba | Fuego, segunda mitad | Mauna Loa | Resultado |
|---|---|---|---|
| T1 umbral = 0,0500 km/s × Δt | 2.685 de 2.685 filas | 305 de 305 (Δt de 282 a 328 s, umbrales de 14,1 a 16,4 km) | cumple |
| T1 umbral refinado = Δt/60 km | 2.088 de 2.123 (98,4 %) | 296 de 296 | **no cumple en Fuego por la letra** (ver 2.3) |
| T2 rama lejana si y sólo si fuera del umbral y sin enlace | 2.523 de 2.540 (99,3 %); 0 filas lejanas aceptadas | 305 de 305 | cumple |
| T3 aceptado si y sólo si solapa o se parece en emisividad | exactitud balanceada 0,83 (ceniza 0,77; hielo 0,99); 101 aceptados sin ninguna de las dos | 5 filas, 5 aciertos, **sin poder** | **no cumple** |
| T4a pluma aceptada pasó el contraste detallado | 1 aceptada (San Cristóbal 23:31), lo pasó | 0 plumas, sin dato | condición necesaria confirmada con 1 caso |
| T5 enlace de píxeles implica "Old Volcanic Feature" | 26 grupos, 0 en contra | 4 grupos, 1 en contra | **no cumple** (ya refutada en el ajuste, enmienda 1) |
| T6 sólo contra la imagen anterior | 2.685 de 2.685 (Δt de 896 a 931 s) | 305 de 305 | cumple |

Placebo de T3 (marca barajada dentro de cada cuadro, 1.000 veces): mediana 0,62, percentil 95 0,71.
La regla da 0,83: está sobre el azar pero bajo el 0,90 exigido.

Control de integridad (líneas contadas por búsqueda de texto contra filas de la tabla): igual en
los cuatro casos (por ejemplo, Fuego segunda mitad: 383 líneas de criterio cumplido, 2.685 objetos
comparados, 26 `KEEPING`, 42 clasificaciones).

Exploratorias: T4b (aceptada si pasa el contraste y tiene 8 píxeles o más) acierta el único caso de
prueba. T7 (anclaje con los dos números del resumen sobre 1/3) no tuvo ningún `MATCH` débil en la
prueba: sin poder.

### 2.3 Por qué T1 "no cumple por la letra" y qué dice el dato (post hoc)

El 1,6 % que falla en Fuego son objetos comparados contra **dos** rasgos históricos a la vez, algo
que no ocurre en los datos de ajuste. Mi lector guardaba un renglón por objeto y juntaba el tiempo de
una comparación con el umbral refinado de la otra. Rehecho por par objeto y rasgo
(`scripts/h28_pares_historia.py`, con su propio control: 2.982 líneas `Hist Idx` por texto, 2.982
pares):

| Caso | Pares | Umbral = 0,05 × Δt | Refinado = Δt/60 | Δt (s) | Umbral (km) |
|---|---|---|---|---|---|
| Kirishima | 31 | 31 | 26 de 26 | 143 a 156 | 7,2 a 7,8 |
| Fuego, primera mitad | 651 | 651 | 589 de 589 | 899 a 931 | 45,0 a 46,5 |
| Fuego, segunda mitad | 2.982 | 2.982 | 2.232 de 2.232 | 896 a 931 | 44,8 a 46,5 |
| Mauna Loa | 305 | 305 | 296 de 296 | 282 a 328 | 14,1 a 16,4 |

La ley es exacta en 3.969 de 3.969 comparaciones, con el tiempo entre imágenes variando de 143 a
931 s. En Mauna Loa el umbral cambia cuadro a cuadro siguiendo al tiempo (14,1 km a 282 s, 16,4 km a
328 s), que es lo que distingue "depende del tiempo" de "depende del sensor o del tamaño del píxel".

Por par, T2 baja a 2.790 de 2.830 (98,6 %): 39 pares aceptados a la rama cercana estando fuera del
umbral y sin enlace de píxeles, y 1 par de la rama lejana aceptado. Todos en la segunda mitad de
Fuego, con la nube ya dispersa y rasgos históricos de miles de km². La regla de rama por distancia
no es completa para rasgos grandes.

**Cómo se llega al veredicto.** Leído sin el arreglo, T1 falla y el criterio diría "no se sostiene".
El arreglo es del instrumento (emparejar bien las líneas), no del umbral ni de la regla, y la parte
principal de T1 (el umbral de distancia) dio 100 % antes de cualquier arreglo. Con T1 y T2
cumpliendo y T3 no, el criterio dice **"se sostiene en parte: la ley de distancia es real pero el
parecido mínimo no es el que propuse"**. Quien no acepte el arreglo debe leer "no se sostiene por la
letra, con la ley de distancia en 100 % de las filas".

### 2.4 Lo que el dato de prueba mostró que yo no había propuesto (post hoc)

- El registro numera el criterio cumplido: "(1)" y "(2)". Sobre las 403 comparaciones
  aceptadas de los cuatro casos (347 de ceniza, 56 de nube convectiva): ceniza "(1)" 158 con solape y 46 sin; ceniza "(2)" 2 con solape y 141 sin. El subcriterio
  (2) es el que acepta objetos que no se superponen al rasgo anterior.
- Objetos de ceniza dentro del radio que fueron aceptados: 341 de 351 en la segunda mitad de Fuego,
  5 de 5 en Kirishima. Para la nube convectiva (hielo): 42 de 63 y 10 de 44. El seguimiento es mucho
  más permisivo con objetos de ceniza que con objetos de nube convectiva.
- Clasificación: en los 42 grupos de ceniza de los cuatro casos, `New Volcanic Feature` si y sólo
  si el grupo no tiene índice de historia (42 de 42).

### 2.5 Prueba 2: los 60 cuadros de Chillán (`resultados/prueba/eventos_chillan_resumen.json`)

Control positivo en Kirishima, donde el log dice la verdad: el script marca nacimientos a las 20:17
y 20:47 y continuaciones de 20:50 a 21:00, igual que el log
(`resultados/ajuste/eventos_kirishima_resumen.json`).

| Prueba | Resultado en Chillán | Por la letra |
|---|---|---|
| C0 lectura de la cadena | edad igual a la diferencia de tiempos en los 60; identificador del JSON igual en los 60; área por píxel 5,97 km² | cumple |
| C1 la cadena no salta cuadros | 51 de 56 con el cuadro anterior publicado; 5 saltan un cuadro cuya imagen GOES existe (`resultados/posthoc/chillan_huecos_s3.txt`) | **no cumple en 5** |
| C2 huella dentro de 0,05 km/s × Δt | 56 de 56; máximo 18,0 km contra 30 km | cumple (sin poder para refutar, como dice el criterio) |
| C3 huella comparte píxel con la anterior | 49 de 56 | informativa |
| C4 nacimiento a 4 km o menos del cráter | 2 de 4 (1,2 y 2,8 km sí; 8,5 y 12,5 km no) | **no cumple** |
| C5 probabilidad alta sin señal infrarroja sólo en continuaciones | 89 de 90 píxeles; 1 en el nacimiento del 18-11 10:10; los 4 nacimientos son de día | **no cumple por 1 píxel** |

Continuaciones explicadas por la puerta de seguimiento: 51 de 56 (91,1 %), sobre el 90 % que pedía
el criterio: **COMPATIBLE**.

Cadenas (`D:\goes_notas\s19\h28\resultados\prueba\eventos_chillan_cuadros.csv`, fuera del repositorio):

| Nace (UTC) | Tipo | Cuadros | Distancia mínima al cráter al nacer | Lo que se ve |
|---|---|---|---|---|
| 13-11 19:00 | `VCB` | 11 | 1,2 km | 5 píxeles al nacer; después un solo píxel durante 2 h |
| 14-11 12:40 | `ASHPLUMEPUFF` | 7 | 8,5 km | ninguna continuación comparte píxel con la anterior; saltos de 2 a 18 km por cuadro; distancia al cráter 8,5; 2,9; 1,8; 7,8; 23,5; 45,8; 27,1 km |
| 14-11 16:30 | `ASHPLUMEPUFF` | 41 | 2,8 km | 7 h 10 min; crece de 3 a 67 píxeles; desde las 22:50 se aleja del cráter (14,6 a 55,9 km) |
| 18-11 10:10 | `ASHPLUMEPUFF` | 1 | 12,5 km | un cuadro |

Huecos y atraso de producción, post hoc (`resultados/posthoc/chillan_atraso.csv`): atraso = hora de
creación del archivo menos hora de la imagen. Los 5 cuadros seguidos de un hueco tienen atraso de
30, 30, 31, 30 y 31 min. Los otros 55 tienen mediana 23 min y máximo 28 min; ninguno llega a 30.

### 2.6 Lo que se leyó de la puerta de nacimiento (ajuste, 14 candidatas)

`D:\goes_notas\s19\h28\resultados\ajuste\kirishima_plumas.csv` y
`D:\goes_notas\s19\h28\resultados\ajuste\fuego_ajuste_plumas.csv` (fuera del repositorio).

- 12 eliminadas, 2 aceptadas (Kirishima 20:17:30 y 20:47:30). Las 2 aceptadas pasan "detailed
  spatial contrast testing without distance check"; 11 de las 12 eliminadas la fallan.
- La eliminada que la pasa (Kirishima 20:45:00) tiene 7 píxeles; las aceptadas, 8 y 9.
- Las dos aceptadas tienen probabilidad mediana de píxel 2,40 % y 0,01 % y salen con
  `Alert Confidence: HIGH`.
- Plumas "fuertes" de Fuego: 4 con `MATCH` seguidas de `ELIMINATING STRONG PLUME BECAUSE OF LACK OF
  ACTIVITY`. Existe una condición de actividad del volcán para ese camino; no la leí.
- La única aceptada de la prueba (San Cristóbal 23:31, 13 píxeles) pasa el contraste, tiene los 13
  píxeles con tendencia temporal robusta y `Min Plume Distance` 8,1, o sea que el anclaje no exige
  estar sobre el cráter.

## 3. Lo que podría estar equivocado

1. **Leí un registro, no el programa.** La ley de distancia es lo que el registro imprime como
   umbral, y coincide en 3.969 de 3.969 casos; pero qué hace VOLCAT con ese umbral cuando el rasgo es
   grande lo vi fallar en 40 pares. No sé si la versión de producción de GOES-19 (v3r4) usa las mismas
   constantes que los paquetes de prueba (v3p9). Los logs traen encabezados de rutina fechados en 2017.
2. **Chillán no tiene registro.** "Compatible" quiere decir que los 60 cuadros no contradicen la
   regla, no que se haya visto a VOLCAT aplicarla allí. C2 no puede fallar para una pluma pegada a
   un volcán. La única comprobación con poder (C1) falló en 5 cuadros por la letra, y la explicación
   del atraso es posterior a ver el dato: es una coincidencia de 5 sobre 5 contra 0 sobre 55, no una
   prueba de que VOLCAT se salte imágenes.
3. **El 91 % está a un cuadro del umbral.** Con 50 de 56 habría sido 89 % y "compatible en parte".
4. **La segunda mitad de Fuego no es independiente de la primera**: es la misma nube, más tarde.
   Mauna Loa sí es independiente, pero aporta 305 comparaciones y sólo 5 dentro del radio.
5. **La mayoría de las filas con las que deduje el parecido mínimo eran de nube convectiva** (44 de
   50). Lo extendí a ceniza sin tener un solo caso de ceniza rechazada, y eso fue lo que falló.
6. **Mi lector tuvo dos errores** (grupos de hielo que pisaban a los de ceniza, encontrado antes de
   la prueba; emparejamiento de comparaciones dobles, encontrado en la prueba). El control de
   integridad cuenta líneas, no comprueba que cada número esté en la columna correcta. Puede haber
   un tercero.
7. **Conocimiento previo de los datos de prueba**, declarado en `01_REGLA_Y_CRITERIO.md` sección 0:
   sabía que la cadena del 14-11 cruzaba el hueco de las 17:10 y conocía el agregado de H20a sobre
   los píxeles de probabilidad alta.
8. **La cadena del 14-11 12:40** (saltos de hasta 18 km sin píxel compartido, alejándose y volviendo)
   se puede leer como seguimiento que se engancha en objetos sin relación o como una bocanada
   arrastrada por el viento a 15 a 30 m/s. Con los archivos de evento no se distingue.

## 4. Comparación con los informes previos

Leídos después de commitear la hipótesis inicial.

- **H20c** contó la línea "Temporal selection criteria met for ash" y concluyó que no se identificó
  la regla. Coincido en el conteo (0 a las 20:17 y 20:47; 1 por cuadro desde las 20:50). H28 agrega
  los números de esa regla.
- **H20c dice que la subida de probabilidad empieza cuando VOLCAT empieza a seguir.** En el archivo
  de evento de Kirishima de las 20:47 (nacimiento, sin seguimiento) la probabilidad publicada ya no
  es la infrarroja: un píxel con infrarroja 0,01 se publica con 0,41, y tres con infrarroja 0,99 a
  1,00 se publican con 0,00. Y en Chillán hay 1 píxel subido en un nacimiento. La subida fuerte sí
  viene con el seguimiento (89 de 90 píxeles en Chillán), pero no es sólo eso.
- **H19** contó 342 veces la línea de criterio temporal para ceniza en Fuego. Mi conteo da 1 en la
  primera mitad y 341 en la segunda: coincide.
- **H20a** concluyó que en Chillán "VOLCAT publica objetos, no probabilidades altas" y que la
  decisión está en el paso de objeto y de seguimiento. H28 lo cuantifica: 56 de 60 cuadros son
  seguimiento.
- **H14** ya había visto que la cadena del 13-11 es de tipo `VCB`. Coincido.
- No encontré en esos informes ninguna afirmación que mis datos contradigan de plano.

## 5. Seguimientos (no hechos aquí)

1. **Etna y Fukutoku.** Sus logs no están en disco. El de Etna son 97 MB de logs, eventos y alertas
   dentro de un paquete de 7,2 GB que se puede leer en flujo sin extraer el resto. Serviría para
   tener más nacimientos de pluma (aquí hubo 3 aceptadas en total) y casos de ceniza rechazada
   dentro del radio.
2. **Los subcriterios (1) y (2)** y la condición de actividad de las plumas fuertes: preguntas
   concretas para el correo a Pavolonis, junto con si el sistema en tiempo real se salta imágenes al
   llegar a 30 min de atraso.
3. **`history/volcat_history.hdf` de Fuego** (963 MB) no se abrió. Puede traer los campos por píxel
   que el seguimiento hereda, incluida la probabilidad.
4. **Para H26 (seguidor propio):** los números que VOLCAT usa son 0,0500 km/s de radio amplio y
   0,0167 km/s de radio refinado, contra la imagen anterior procesada, con los filtros de objeto
   apagados. No miré el trabajo de H26.
5. Mi lector no entiende todas las ramas del registro (152 pares de la segunda mitad de Fuego no
   traen línea de rama). No afecta a T1; sí limita T2 y T3.

## 6. Cómo reproducirlo

Python 3.12 con `netCDF4`, `numpy`, `pandas`. Los datos de SSEC no están en el repositorio; las
rutas son las de este computador.

```
cd C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\Goes\.claude\worktrees\xenodochial-pare-413fc0\docs\own_volcat\h28_regla_seguimiento
set T=D:\goes_notas\s19\h28\tablas
set K=D:\goes_notas\s17\paquetes\kirsh\kirsh_h9-japan_july2025_r20260709-volcat-code-ancil\reference_data\logs
set F=D:\goes_notas\s16\modo_dia\fuego\fuego_goes16-fulldisk_june2018_r20260709-volcat-code-ancil\reference_data\logs
set M=D:\goes_cache\volcat_test_mauna_loa\ext\mauna-loa_g17-conus_nov2022_r20260709-volcat-code-ancil\reference_data\logs

python -I scripts\h28_parse_logs.py %K% %T% kirishima
python -I scripts\h28_parse_logs.py %F% %T% fuego_ajuste 140000 185959
python -I scripts\h28_parse_logs.py %F% %T% fuego_prueba 190000 235959
python -I scripts\h28_parse_logs.py %M% %T% mauna_loa
python -I scripts\h28_match_volcan.py %F% %T%\fuego_prueba_match.csv fuego_prueba 190000 235959
python -I scripts\h28_evaluar_logs.py %T% fuego_prueba %F% 900 190000 235959
python -I scripts\h28_evaluar_logs.py %T% mauna_loa %M% 300
python -I scripts\h28_pares_historia.py %F% %T%\fuego_prueba_pares.csv fuego_prueba 190000 235959
python -I scripts\h28_chillan.py D:\goes_notas\busqueda_2026-11-20\volcat_eventos_357070 "VOLCAT-FD-vid357070_*.nc" 600 D:\goes_notas\s19\h28\resultados\prueba\eventos_chillan_cuadros.csv resultados\prueba\eventos_chillan_resumen.json
python -I scripts\h28_posthoc.py %T% D:\goes_notas\busqueda_2026-11-20\volcat_eventos_357070 resultados\posthoc\posthoc.json %K% %F% %M%
```

Los otros casos de `h28_match_volcan.py` y `h28_pares_historia.py` se corren igual cambiando la
carpeta, la etiqueta y el rango de horas. Las tablas de trabajo quedan en
`D:\goes_notas\s19\h28\tablas\` (2 MB) y sus copias en `D:\goes_notas\s19\h28\resultados\`. Ninguna de
las dos carpetas va al repositorio, porque transcriben datos de SSEC. Para que el evaluador escriba
las filas de detalle de T4 y T5 hay que poner la variable de entorno `H28_DETALLE=1`; lo que se
commitea va sin ellas.
