# H23: ¿cuál es la capa de ceniza más tenue que GOES-19 puede ver sobre la cumbre de Chillán? Informe, 22-11-2026 (S17)

> **Esto es una cota, no una validación.** Se pintó una capa de ceniza inventada sobre escenas reales de GOES-19
> y se midió si los detectores la recuperan contra el fondo real. Es en parte circular: la capa inyectada usa
> nuestra propia física de emisividad y de β, la misma con que después se la busca, y nuestra reconstrucción del
> cielo despejado nunca se validó a nivel B (κ 0,31 a 0,33, PR 76). Por eso el cielo despejado no se modeló: sale
> del mismo píxel en otros días. El resultado dice cuánta señal hace falta para ganarle al fondo real. No dice que
> una pluma real se comporte como la capa inyectada.

**Veredicto con la regla escrita antes de medir.** La afirmación "no se puede ver en el infrarrojo a 2 km" queda
**FALSADA en parte**: con cielo despejado, una capa de emisividad 0,15 con tope a **5 km** se recupera sobre la
cumbre de noche, de madrugada y en la mañana (AUC 0,91 a 0,95), y a **4 km** sólo en la mañana (AUC 0,88). El
detector que lo logra es la diferencia 11 − 12 µm contra la línea base del propio píxel. La afirmación **se
sostiene** a 3 km en todo horario y a 4 km de noche. Entre las 15 y las 21 h de Chile queda **SIN DATO**.

**Lo que más importa para Chillán.** En las horas de los eventos reales de noviembre, ese mismo detector no se
mueve: la pluma real queda **bajo** el límite (SOSPECHA, §7). E integrar en el tiempo no baja el límite (§6).

Criterio (antes de medir): `criterio_2026-11-22.md`, commit `b77a83c`. Dos enmiendas post hoc, las dos commiteadas
antes de calcular un número de detección: `enmienda_posthoc_1_2026-11-22.md` (commit `0d29020`) y
`enmienda_posthoc_2_2026-11-22.md` (commit `722fba5`). Resultados: commit `01b50d9` y siguientes.

Carpeta: `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\Goes\docs\own_volcat\h23_inyeccion\` (mientras
no se fusione el PR, en la copia de trabajo
`C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\Goes\.claude\worktrees\agent-a1c925183efa5bdc2\docs\own_volcat\h23_inyeccion\`).

## 1. Para geólogo

**El fenómeno.** El infrarrojo térmico no ve la ceniza por su color. La ve por dos cosas a la vez. Primero, la
capa tiene que estar **más fría que el suelo que tapa**: si está a la misma temperatura, emite lo mismo que el
suelo y no cambia nada. Segundo, para saber que es ceniza y no una nube de agua, la capa tiene que apagar un poco
más la banda de 11 µm que la de 12 µm, y eso baja la diferencia entre las dos bandas.

En la cumbre de Chillán la primera condición casi no se cumple. El píxel de 2 km que contiene el cráter promedia
terreno entre 2.500 y 2.900 m, con nieve en primavera. Despejado, ese suelo está entre 264 y 274 K. El aire a
3 km está a 269 K: **una pluma a 3 km tiene la temperatura del suelo**. A 4 km el aire está a 263 K y a 5 km a
257 K. Recién ahí la pluma es más fría que la cumbre, por 3 a 7 K a 4 km y por 9 a 14 K a 5 km. En el terreno
bajo (bajo 1.300 m, a 10 a 30 km) el suelo es más tibio y la misma pluma contrasta 7 a 27 K.

**Qué se hizo.** Se tomaron 32 días de escenas reales sin eventos VOLCAT conocidos (21-09 al 23-10-2026, sin el
22-10), cada 10 minutos. En cada píxel se pintó una capa de ceniza de emisividad 0,05 a 0,9 con tope a 3, 4 y 5 km, a la
temperatura que el modelo GFS da para esa altura. Se probaron cinco detectores. Cada uno compara el píxel con su
propia historia a la misma hora en otros días despejados. El fondo contra el que compiten es real: los mismos
píxeles, sin inyectar.

**Lo que salió.** La medida es el AUC: la probabilidad de que un píxel con capa puntúe más "ceniza" que uno sin
capa. 0,5 es azar y 1 es separación perfecta. El criterio fijó 0,80 como umbral.

- **Sobre la cumbre, despejado.** La capa más tenue que se recupera (AUC 0,80) tiene emisividad **0,07 a 0,09
  si está a 5 km**, **0,10 a 0,25 si está a 4 km**, y **0,34 o más (de noche, casi opaca) si está a 3 km**. Si se
  pide algo usable como alarma (detectar la mitad de las veces con 1 % de falsas alarmas), los números suben a
  0,14 a 0,17 a 5 km, 0,27 a 0,38 a 4 km y 0,73 o más a 3 km.
- **Terreno bajo, despejado.** 0,05 a 0,12 (AUC 0,80), y 0,09 a 0,22 como alarma.
- **Qué detector.** Sobre la cumbre, sólo la diferencia 11 − 12 µm contra la línea base del propio píxel. La
  temperatura de 11 µm sola no alcanza ahí: de un día despejado a otro el suelo cambia varios grados, más que lo
  que enfría la capa. En el terreno bajo también sirve el enfriamiento a 11 µm comparado con los vecinos.
- **Con cualquier cielo.** Casi nada. Sin elegir escenas despejadas, la capa de 0,15 a 4 o 5 km no pasa de AUC
  0,71 con ningún detector operable, y sobre la cumbre ni una capa de 0,9 pasa de 0,77. Y la escena estuvo
  despejada sólo en el 13,5 % de los cuadros.
- **Promediar en el tiempo no ayuda.** Promediar 1 hora o 3 horas deja la detección igual. El fondo no es ruido
  que se cancele: es un corrimiento que dura horas. Su causa (masa de aire, humedad) no se midió.
- **Depende de que la ceniza sea "típica".** Si la partícula es gruesa o la pluma es sobre todo agua y gas
  (β cerca de 1), la diferencia 11 − 12 µm casi no se mueve. Sobre la cumbre, la capa de 0,15 queda visible sólo
  a 5 km y a media mañana, por puro enfriamiento.

**Qué significa para Chillán.** "No se puede ver en el infrarrojo" era demasiado amplio. Una pluma de emisividad
0,15 que suba a 5 km se vería, con cielo despejado. Lo que sí queda establecido como cota es más estrecho: **no
se puede ver una pluma que se queda a la altura de la cumbre (3 km, y 4 km de noche), ni una más tenue que 0,07 a
0,25 según la altura, ni ninguna cuando hay nubes.** Las plumas de noviembre calzan ahí: en las horas de los
cuatro eventos VOLCAT, la diferencia 11 − 12 µm de los píxeles de cumbre quedó dentro de su variación normal
(mediana entre −0,12 y +0,12 K, contra un fondo que va de −0,3 a +0,4 K). Una capa de 0,15 a 5 km la habría
bajado 0,45 a 0,60 K en tres de los cuatro eventos. No la bajó. La pluma real fue más tenue que el límite, o más
baja, o las dos cosas.

**Lo que no se pudo medir.** La tarde (15 a 21 h de Chile), que es cuando ocurrió la mayor parte de los eventos:
en octubre casi no hubo tardes despejadas sobre la cordillera y no hay línea base. Y la emisividad de la pluma
real no se conoce por otra vía: lo de arriba es una lectura, no una medición.

## 2. Camino de la prueba (incluye dos correcciones después de ver datos)

1. **Criterio** escrito y subido antes de medir (commit `b77a83c`): detectores, grilla, píxeles, regla de
   decisión, controles y seis comprobaciones de instrumento.
2. **La primera corrida cortó sola.** La comprobación I5 (ciclo diurno de la línea base) falló: 3,9 K donde se
   pedían 8. El script salió antes de inyectar nada. El instrumento estaba bien; la que estaba mal era la línea
   base del criterio (percentil 90 de los 10 días anteriores), que en un periodo tan nublado caía en nube: su
   mínimo en el terreno bajo estaba a las 17 h de Chile, más frío que al amanecer.
3. **Enmienda post hoc 1** (commit `0d29020`), decidida mirando sólo temperatura de brillo cruda y la máscara de
   nubes de NOAA, sin ningún resultado de detección:
   - Escena despejada: al menos 80 % del terreno bajo del volcán despejado según la máscara de NOAA (ACMF).
   - Línea base: mediana del mismo píxel a la misma hora en los otros días del bloque con escena despejada
     (mínimo 3 días).
   - Población que decide (B): escena despejada. Días de prueba: todos los del bloque.
4. **Enmienda post hoc 2** (commit `722fba5`): con la línea base nueva no hay referencia a las 18 UTC (0 a 2 días
   despejados entre las 17 y las 22 UTC), así que I5 se evalúa en la última hora con referencia (16 UTC). Ahí da
   13,1 K. Consecuencia sabida antes de medir: el tramo de la tarde queda SIN DATO.
5. **Medición** con el criterio más las dos enmiendas (commit `01b50d9`).

Los detectores, la física y la grilla de la inyección, las métricas, los mínimos por celda, la regla de decisión
y los controles **no cambiaron**. La dirección de las dos enmiendas favorece a la detección (fondo más limpio):
si sesgan algo, es hacia falsar.

## 3. Comprobaciones de instrumento y controles

| | Comprobación | Pide | Medido | Fuente |
|---|---|---|---|---|
| I1 | Cobertura | ≥ 95 % de los cuadros | octubre 4.727 de 4.752 (99,5 %); noviembre 3.024 de 3.024. Relleno: 0,33 % y 0,07 % de los valores | `resultados/instrumento_oct.json`, `instrumento_nov.json` |
| I2 | Mismo scan en C14 y C15 | 100 % | 0 cuadros con scan distinto | ídem |
| I3 | Rango y vida | ≥ 99,9 % entre 180 y 330 K; 0 cuadros congelados | 100 % (212 a 309 K en octubre, 216 a 322 K en noviembre); 0 congelados. Planck del NetCDF, idéntico en todos los archivos | ídem |
| I4 | Píxeles donde corresponde | correlación referencia de las 06 UTC con cota ≤ −0,6; cumbre ≥ 5 K más fría | −0,935 en 864 píxeles; cumbre 11,5 K más fría | `resultados/h23_instrumento.json` |
| I5 | Ciclo diurno de la referencia | ≥ 8 K en el terreno bajo | 13,1 K entre las 09 y las 16 UTC (enmienda 2); en la cumbre 7,7 K | ídem |
| I6 | BTD de cielo despejado | entre −1 y +4 K | 0,83 K | ídem |
| Control positivo | ε 0,9 a 10 km, población B | AUC ≥ 0,95 (D3 ≥ 0,90) | 1,000 en D1, D2, D4 y D5; 0,985 a 1,000 en D3, en cumbre y terreno bajo, los tres tramos con dato. **Los cinco detectores pasan** | `resultados/h23_resumen.txt` §1 |
| Control nulo (a) | ε = 0 por la misma tubería | AUC 0,500 ± 0,001; cambio de BT 0 | 900 celdas: AUC mínimo 0,5 y máximo 0,5; cambio de BT11 y de BTD 0 | §2 |
| Control nulo (b) | Placebo por mitades de días | que el rango de 95 % contenga 0,5 | lo contiene en las 24 combinaciones. En la cumbre: D1 0,09 a 0,89; D2 0,22 a 0,77; D4 0,07 a 0,89 | §2b |

Lectura del placebo: dos mitades de días sin inyección pueden separarse entre sí con AUC hasta 0,77 en D2. El
fondo cambia de un día a otro casi tanto como lo que mueve una capa de 0,15 a 4 km de noche. Las celdas de D2
que falsan tienen AUC 0,88 a 0,95, por encima de ese rango.

Pruebas de las piezas numéricas con datos sintéticos (AUC contra `sklearn`, cuantiles, inyección con ε 0 y 1):
`scripts/h23_pruebas.py`, 13 de 13.

Cuánto dato hay (Chillán, 21-09 al 23-10, sin el 22-10). Escena despejada en 13,5 % de los cuadros: 17 % de
00 a 06 UTC (11 días con alguno), 20 % de 06 a 12 (11 días), 11 % de 12 a 18 (9 días) y 6 % de 18 a 24 UTC (5
días). Muestras de cumbre: 20.334 con cualquier cielo, 3.366 con escena despejada. Terreno bajo: 467.686 y
77.418.

## 4. Veredicto contra el criterio

Cumbre de Chillán, escena despejada (población B), β 0,70, **ε 0,15**. AUC* e IC 95 % remuestreando días. La
regla: FALSADA si AUC* > 0,80 e IC inferior > 0,70.

| Tramo UTC (Chile) | Altura | D1: BT11 | D2: BTD 11 − 12 | D3: β | D4: doble diferencia | D5: lineal que conoce la firma |
|---|---|---|---|---|---|---|
| 00 a 06 (21 a 03) | 3 km | 0,57 | 0,61 (0,52 a 0,70) | 0,44 | 0,59 | 0,67 |
| | 4 km | 0,56 | 0,77 (0,66 a 0,89) | 0,58 | 0,58 | 0,79 |
| | 5 km | 0,66 | **0,93 (0,81 a 0,98) FALSADA** | 0,69 | 0,69 | **0,93 FALSADA** |
| 06 a 12 (03 a 09) | 3 km | 0,57 | 0,66 (0,56 a 0,76) | 0,41 | 0,60 | 0,68 |
| | 4 km | 0,55 | 0,73 (0,62 a 0,85) | 0,56 | 0,54 | 0,74 |
| | 5 km | 0,65 | **0,91 (0,85 a 0,97) FALSADA** | 0,72 | 0,67 | **0,94 FALSADA** |
| 12 a 18 (09 a 15) | 3 km | 0,53 | 0,68 (0,60 a 0,76) | 0,52 | 0,52 | 0,64 |
| | 4 km | 0,74 | **0,88 (0,79 a 0,95) FALSADA** | 0,75 | 0,67 | **0,85 FALSADA** |
| | 5 km | 0,83 (0,62 a 0,94) no concluyente | **0,95 (0,87 a 0,99) FALSADA** | **0,95 FALSADA** | 0,75 | **0,90 FALSADA** |
| 18 a 24 (15 a 21) | todas | SIN DATO | SIN DATO | SIN DATO | SIN DATO | SIN DATO |

Fuente: `resultados/h23_resumen.txt` §3 y `resultados/h23_veredicto.json`. De noche, a 3 km, el mejor sentido de
D1, D2 y D4 es "más tibio": la capa está 3 a 4 K más tibia que la nieve y entibia el píxel 0,5 a 0,6 K.

**Veredicto global (regla del criterio):** FALSADA en al menos un régimen con un detector operable (D2): 5 km en
los tres tramos con dato y 4 km en la mañana. Se sostiene a 3 km (AUC* máximo 0,68) y a 4 km de noche (0,73 y
0,77; ninguna celda pasa 0,80). Tramo 18 a 24 UTC: SIN DATO (3 días con muestra; el mínimo es 8).

Detección a falsa alarma fija, D2, ε 0,15 en la cumbre: con 1 % de falsas alarmas se detecta el 41 a 53 % de
las capas a 5 km y el 4 a 8 % a 4 km; con 5 %, el 68 a 80 % a 5 km y el 23 a 63 % a 4 km.

Las otras poblaciones (informan):

- **C, oráculo** (además el propio píxel despejado): 12 de 45 celdas falsan; AUC* máximo 0,98. Casi igual a B:
  en estas escenas el píxel de cumbre rara vez tiene nube propia (3.123 de 3.366 muestras).
- **A, todo cielo:** AUC* máximo 0,86 a ε 0,15, pero es D5 a 3 km (y D2 a 3 km, 0,69 a 0,77, en sentido "más
  tibio"): un artefacto de pintar una capa baja y tibia encima de nubes altas y frías, que en la realidad
  quedaría debajo. A 5 km, donde la capa enfría, D2 da 0,53 a 0,59. El tramo 18 a 24 UTC de A tiene sólo los
  cuadros de las 23 UTC.
- **Terreno bajo, B:** 33 de 45 celdas pasan la regla; D2 da 0,86 a 0,99.

## 5. Curva de detección y emisividad mínima detectable

Figuras: `resultados/h23_curva_3km.png`, `h23_curva_4km.png`, `h23_curva_5km.png` (AUC* contra emisividad, por
tramo, cumbre arriba y terreno bajo abajo, con IC por días).

AUC* de D2 en la cumbre, escena despejada, por emisividad inyectada (`resultados/h23_resumen.txt` §4):

| Tramo UTC | Altura | 0,05 | 0,10 | 0,15 | 0,20 | 0,30 | 0,50 | 0,90 |
|---|---|---|---|---|---|---|---|---|
| 00 a 06 | 3 km | 0,54 | 0,58 | 0,61 | 0,63 | 0,65 | 0,62 | 0,82 |
| | 4 km | 0,60 | 0,70 | 0,77 | 0,83 | 0,89 | 0,94 | 0,98 |
| | 5 km | 0,71 | 0,85 | 0,93 | 0,96 | 0,97 | 0,98 | 0,99 |
| 06 a 12 | 3 km | 0,56 | 0,62 | 0,66 | 0,69 | 0,73 | 0,72 | 0,67 |
| | 4 km | 0,58 | 0,66 | 0,73 | 0,78 | 0,83 | 0,87 | 0,98 |
| | 5 km | 0,70 | 0,83 | 0,91 | 0,95 | 0,97 | 0,99 | 1,00 |
| 12 a 18 | 3 km | 0,57 | 0,63 | 0,68 | 0,72 | 0,78 | 0,87 | 0,98 |
| | 4 km | 0,68 | 0,81 | 0,88 | 0,93 | 0,98 | 0,99 | 1,00 |
| | 5 km | 0,76 | 0,89 | 0,95 | 0,98 | 0,99 | 1,00 | 1,00 |

**Emisividad mínima detectable, escena despejada** (`resultados/h23_resumen.txt` §5). Primer número: donde el
AUC* cruza 0,80. Segundo: donde la detección con 1 % de falsas alarmas cruza 50 %. Los tres valores son los
tramos 00 a 06, 06 a 12 y 12 a 18 UTC.

| Terreno | Altura | D2: BTD (AUC 0,80) | D2: BTD (alarma) | D1: BT11 (AUC 0,80) | D4: doble diferencia (AUC 0,80) |
|---|---|---|---|---|---|
| **Cumbre** | 3 km | 0,87 · > 0,90 · 0,34 | > 0,90 · > 0,90 · 0,73 | 0,84 · 0,68 · > 0,90 | 0,53 · 0,51 · > 0,90 |
| | 4 km | 0,17 · 0,25 · 0,10 | 0,38 · 0,35 · 0,27 | > 0,90 · > 0,90 · 0,22 | 0,82 · > 0,90 · 0,40 |
| | 5 km | 0,08 · 0,09 · 0,07 | 0,17 · 0,14 · 0,17 | 0,31 · 0,34 · 0,13 | 0,27 · 0,28 · 0,23 |
| **Terreno bajo** | 3 km | 0,11 · 0,12 · 0,08 | 0,22 · 0,19 · 0,17 | 0,48 · 0,40 · 0,29 | 0,10 · 0,11 · 0,10 |
| | 4 km | 0,07 · 0,07 · 0,06 | 0,14 · 0,12 · 0,13 | 0,27 · 0,21 · 0,21 | 0,06 · 0,06 · 0,08 |
| | 5 km | 0,06 · 0,05 · ≤ 0,05 | 0,11 · 0,09 · 0,11 | 0,20 · 0,15 · 0,16 | ≤ 0,05 · ≤ 0,05 · 0,06 |

Con cualquier cielo (población A), a 4 y 5 km, el máximo de D1 a D4 es 0,65 a ε 0,15 y 0,77 a ε 0,90 sobre la
cumbre; en el terreno bajo, 0,71 y 0,80 (D3). Sólo D3 en el terreno bajo, de noche y a 5 km, cruza 0,80, con
ε 0,86. A 3 km sobre la cumbre algunos cruzan en sentido "más tibio": es el artefacto ya dicho.

**Por qué, en grados.** Señal mediana que produce una capa de ε 0,15, escena despejada
(`resultados/h23_resumen.txt` §6):

| Terreno | Tramo UTC | Altura | Contraste suelo − capa | Cambio de BT11 | Cambio de BTD | εtot equivalente |
|---|---|---|---|---|---|---|
| Cumbre | 00 a 06 | 3 km | −3,0 K | +0,46 K | +0,05 K | −0,014 |
| | | 4 km | +3,2 K | −0,48 K | −0,21 K | 0,014 |
| | | 5 km | +8,6 K | −1,24 K | −0,42 K | 0,035 |
| | 12 a 18 | 3 km | +0,9 K | −0,13 K | −0,15 K | 0,003 |
| | | 4 km | +7,4 K | −1,07 K | −0,41 K | 0,029 |
| | | 5 km | +13,8 K | −1,94 K | −0,64 K | 0,052 |
| Terreno bajo | 00 a 06 | 4 km | +14,7 K | −2,06 K | −0,66 K | 0,049 |
| | 12 a 18 | 4 km | +20,5 K | −2,82 K | −0,92 K | 0,062 |

El fondo sin inyectar de D2 en la cumbre, escena despejada, va de −0,29 a −0,34 K (percentil 5) a +0,32 a
+0,44 K (percentil 95), con mediana 0,00 (`resultados/h23_eventos_extra.json`). Una capa se ve cuando baja la
BTD más que ese ancho: −0,42 K (5 km) sí, −0,21 K (4 km de noche) a medias, +0,05 K (3 km) no. El fondo de D1
es mucho más ancho (−4,9 a +3,0 K de noche), por eso la BT11 sola no sirve en la cumbre.

La última columna importa para leer informes anteriores: una capa de ε 0,15 sobre la cumbre equivale a un εtot
(referido a la tropopausa, el de VOLCAT) de **0,01 a 0,05**. El εtot de 0,06 a 0,16 que la etapa 3 de H15 midió
en la huella no es entonces la emisividad de la pluma: salía contra un cielo despejado modelado que en la cumbre
queda 7 K tibio.

## 6. Medidas secundarias

**S1, integrar en el tiempo: no baja el límite.** AUC* de D2 a ε 0,15 en la cumbre, con el cuadro solo, el
promedio de 1 h y el de 3 h: a 4 km de noche 0,773 · 0,797 · 0,764; a 5 km de noche 0,926 · 0,938 · 0,901; a
4 km en la mañana 0,884 · 0,873 · 0,861. La emisividad mínima a 4 km de noche queda en 0,17 · 0,15 · 0,20. Si
el fondo fuera ruido independiente entre cuadros, promediar 6 cuadros habría llevado el 0,77 a cerca de 0,97
(cuenta mía con ruido gaussiano, no medida).
No lo hace: lo que limita es un corrimiento que dura horas (`resultados/h23_resumen.txt` §7).

**S2, cumbres de control.** Mismo método en Nevado de Longaví y Antuco (`resultados/h23_resumen.txt` §8), D2 a
ε 0,15:

| Cumbre y bloque | 5 km (tramos 00 a 06 · 06 a 12 · 12 a 18 · 18 a 24 UTC) | 4 km |
|---|---|---|
| Chillán, octubre | 0,93 · 0,91 · 0,95 · SIN DATO | 0,77 · 0,73 · 0,88 · SIN DATO |
| Longaví, octubre | 0,94 · 0,93 · 0,91 · SIN DATO | 0,87 · 0,82 · 0,85 · SIN DATO |
| Antuco, octubre | 0,97 · 0,93 · 0,87 · SIN DATO | 0,88 · 0,81 · 0,79 · SIN DATO |
| Longaví, noviembre | 0,88 · 0,85 · 0,89 · 0,87 | 0,71 · 0,66 · 0,81 · 0,78 |
| Antuco, noviembre | 0,80 · 0,84 · 0,78 · 0,80 | 0,62 · 0,65 · 0,71 · 0,70 |

Dos lecturas. (1) Chillán en octubre no detecta peor que las cumbres sin actividad: no hay señal de que su
fondo esté inflado por emisiones propias en los días SIN DATO de VOLCAT. (2) **En noviembre, que es el régimen
de los eventos, se detecta menos**: a 5 km el AUC baja a 0,78 a 0,89 y la detección con 1 % de falsas alarmas
cae a 7 a 35 % (en octubre, 15 a 75 %). El contraste térmico de noviembre no es menor; lo que crece es el ancho
del fondo. Noviembre sí tiene dato de tarde en las cumbres de control: 0,80 a 0,87 a 5 km y 0,70 a 0,78 a 4 km.

**S3, sensibilidad a β** (`resultados/h23_resumen.txt` §9). D2 a ε 0,15 en la cumbre, 5 km: con β 0,55 da 0,94 a
0,98; con 0,70 (la que decide), 0,91 a 0,95; con **0,95, 0,71 a 0,76**. Con β 0,95, D2 ya no pasa 0,80 en
ninguna celda de la cumbre. Lo que queda es el enfriamiento a 11 µm, que no depende de β: a 5 km en la mañana
D3 da 0,91 (IC 0,80 a 0,96) y D1 0,83 (0,62 a 0,94); de noche sólo D5 pasa (0,83). La falsación por la
diferencia 11 − 12 µm vale para ceniza de β 0,70 o menor.

**S4, eventos reales:** §7.

**S5, forma analítica** (`resultados/h23_forma_rt.json`, 28 perfiles GFS del 20 al 23-10, modelo radiativo
propio). Ignorar el aire sobre la capa la deja demasiado tibia: una capa negra se ve 0,32 K más fría a 11 µm y
1,15 K a 12 µm si está a 3 km; 0,13 y 0,63 K a 4 km; 0,05 y 0,37 K a 5 km. Para ε 0,15 eso hace que la BTD
real baje 0,03 K menos a 5 km y 0,05 K menos a 4 km que lo inyectado: la inyección **exagera la señal de BTD
en 5 a 8 % a 5 km y en 12 a 25 % a 4 km** (`resultados/h23_resumen.txt` §11). Va en el sentido de favorecer la
detección. Corrigiendo por esa exageración (AUC* de D2 leído a la emisividad equivalente), las celdas que
falsan siguen sobre 0,80: 5 km queda en 0,91 · 0,89 · 0,94 y 4 km en la mañana en 0,86. A 4 km de noche baja a
0,72 y 0,68.

## 7. ¿La pluma real queda sobre o bajo el límite?

Descriptivo. La primera tabla es la secundaria S4 del criterio; la segunda se agregó **post hoc**, después de
ver el veredicto, para poner los eventos en la escala de la inyección (`scripts/h23_eventos_extra.py`). Los
píxeles son los 6 de cumbre de la regla geométrica, no la huella de VOLCAT (que sale de archivos restringidos y
no se usó). La línea base de noviembre sale de 5 a 9 días despejados, algunos con pulsos del volcán.

| Evento VOLCAT (UTC) | Cuadros con escena despejada | BT11 − línea base | BTD − línea base (mediana; cuartiles) | Contraste con capa a 4 km · 5 km | BTD que habría bajado ε 0,15 a 4 km · 5 km |
|---|---|---|---|---|---|
| 13-11 19:00 a 21:00 | 11 de 13 | +5,3 K | **+0,12 K** (−0,07 a +0,31) | +5,3 · +12,9 K | −0,31 · **−0,60 K** |
| 14-11 12:40 a 13:40 | 0 de 7 | −0,2 K | **−0,03 K** (−0,28 a +0,22) | −5,4 · +1,1 K | +0,13 · −0,15 K |
| 14-11 16:30 a 23:40 | 21 de 44 | +2,8 K | **−0,12 K** (−0,34 a +0,13) | +2,6 · +9,7 K | −0,18 · **−0,46 K** |
| 18-11 10:10 | 0 de 1 | −0,4 K | **−0,04 K** | +4,5 · +9,5 K | −0,26 · **−0,45 K** |

Fuente: `resultados/h23_eventos_extra.json`. Contra el fondo de octubre con cualquier cielo
(`resultados/h23_eventos.json`), la fracción de muestras de evento con BTD bajo el percentil 5 del fondo es 1 %,
0 %, 3 % y 0 % (por azar se espera 5 %).

Lectura:

- En los cuatro eventos la mediana de BTD de la cumbre queda dentro o en el borde de los cuartiles del fondo
  sin pluma (−0,12 a +0,13 K). **No hay corrimiento negativo medible.** Calza con las pruebas anteriores del proyecto.
- En tres eventos una capa de ε 0,15 a 5 km habría bajado la BTD 0,45 a 0,60 K, más que todo el ancho del fondo.
  No pasó. Si la pluma estaba a 5 km, su emisividad efectiva en el píxel fue bastante menor que 0,15: del orden
  de 0,05 o menos en los dos eventos de tarde (ahí una capa de 0,05 ya baja 0,16 a 0,20 K).
- Si estaba a 4 km, la señal esperada de ε 0,15 (−0,18 a −0,31 K) es del tamaño del fondo: no se distingue.
- **El evento del 14-11 en la mañana no se podía ver a ninguna emisividad razonable.** A esa hora el suelo de la
  cumbre estaba a 273 K y el aire a 4 km más tibio que el suelo; a 5 km, 1 K más frío. Una pluma ahí no cambia
  la radiancia.
- La BT11 de la cumbre estuvo 2,8 a 5,3 K **sobre** su línea base en los dos eventos de tarde. No se sabe por
  qué (día más cálido que los de referencia, o menos nieve). No es señal de ceniza: una capa a 4 o 5 km
  enfría.

Conclusión de esta sección: **la pluma real queda bajo el límite por píxel (SOSPECHA).** No es CONFIRMADO porque
la emisividad real no se mide por otra vía, porque los píxeles no son la huella y porque la BTD de un día puede
correrse ±0,3 K sola.

## 8. Evidencia de cada conclusión y cómo podría estar mal

| Conclusión | Estado | Evidencia | Cómo podría estar mal |
|---|---|---|---|
| Con cielo despejado, una capa de ε 0,15 y β 0,70 a 5 km se recupera sobre la cumbre | **CONFIRMADO como cota** | D2: AUC* 0,93 · 0,91 · 0,95, IC inferior 0,81 a 0,87, tres tramos; replicado en Longaví y Antuco en octubre (0,87 a 0,97) | Circular: la firma inyectada es la que el detector busca. La inyección exagera la BTD 5 a 8 %. La capa llena el píxel y es de un solo píxel. La línea base usa días futuros |
| A 4 km sólo en la mañana | **SOSPECHA** | 0,88 (0,79 a 0,95) en 9 días; de noche 0,77 y 0,73 | Pocos días. La forma analítica exagera 12 a 25 % (corregido: 0,86). En noviembre las cumbres de control dan 0,62 a 0,81 |
| A 3 km no se ve; ni casi opaca de noche | **CONFIRMADO** | AUC* 0,61 a 0,68 a ε 0,15; a ε 0,9, D1 da 0,58 en la mañana. Contraste −3,9 a +0,9 K | El GFS puede errar 1 a 2 K la temperatura a 3 km sobre la cordillera; con contraste de ±3 K eso cambia el signo, no el tamaño |
| La BT11 sola no alcanza en la cumbre | **CONFIRMADO** | D1 y D4: emisividad mínima 0,13 a > 0,90 | Una línea base mejor (con el modelo, por masa de aire) podría angostar el fondo de D1 |
| Con cualquier cielo casi no se recupera nada | **CONFIRMADO** para estos detectores | Población A, 4 y 5 km: máximo 0,65 a ε 0,15 y 0,77 a ε 0,90 en la cumbre | La inyección sobre nube alta no es física (la capa quedaría debajo). Un detector con máscara de nubes propia podría rescatar escenas que la de NOAA descarta |
| Integrar en el tiempo no baja el límite | **CONFIRMADO** en estos datos | AUC* igual con 1 h y 3 h | Sólo se probó el promedio simple del mismo detector; no un método que modele el corrimiento del día |
| En noviembre el límite es peor que en octubre | **SOSPECHA** | Controles: 0,78 a 0,89 a 5 km; alarma 7 a 35 % | 11 a 14 días, dos cumbres; referencia de menos días |
| La pluma real de noviembre queda bajo el límite | **SOSPECHA** | BTD en eventos −0,12 a +0,12 K; la capa de 0,15 a 5 km habría dado −0,45 a −0,60 K | Píxeles de cumbre, no la huella. Línea base con días de pulsos. Si la ceniza real es gruesa o con mucha agua (β cerca de 1), la BTD no la ve aunque sea espesa |
| Emisividad de la pluma real | **SIN DATO** | No hay medición independiente | |
| Tarde (15 a 21 h de Chile) en Chillán | **SIN DATO** | 3 días con muestra, el mínimo es 8 | Las cumbres de control en noviembre sí tienen tarde: 0,80 a 0,87 a 5 km |
| VOLCAT del 21-09 al 19-10 en Chillán | **SIN DATO** | El panel revisado parte el 20-10 | Si hubo emisión, ensancha el fondo; los controles no lo muestran |

**La circularidad, en concreto.** (1) La capa inyectada tiene β 0,70 por construcción, y D2 y D3 buscan
justamente β < 1. Con β 0,95 la detección se cae (§6, S3). Esta prueba no puede decir qué β tiene la ceniza de
Chillán. (2) La temperatura del tope viene del GFS, el mismo modelo que antes falló en el terreno de la cumbre;
aquí se usa sólo en el aire libre, no en superficie. El proyecto lo validó contra radiosondas entre 5 y 12 km
(≤ 60 m de altura); a 3 y 4 km sobre la cordillera no está validado. (3) La escena despejada la decide la máscara de NOAA, que en la cumbre misma no sirve (§9), y
la línea base se eligió después de ver datos de instrumento.

**Lo que esta prueba no es.** No es un detector. D2 con esta línea base no se puede operar tal cual: usa días
futuros, pide la escena despejada (13,5 % de los cuadros) y su umbral cambia de un día a otro (placebo). Nada de
esto va al dashboard ni a `src/`.

## 9. Qué cambia y qué queda para seguimiento

- **Para la pregunta de fondo.** "No se ve en el infrarrojo a 2 km" pasa de supuesto a cota con números: el
  límite por píxel sobre la cumbre es ε 0,07 a 0,09 a 5 km, 0,10 a 0,25 a 4 km, y no hay límite útil a 3 km. Las
  plumas de noviembre quedan bajo esa cota (SOSPECHA). La explicación más simple junta dos cosas medidas: plumas
  de 3 a 5 km sobre una cumbre de 3,2 km están casi a la temperatura del suelo, y son tenues.
- **Para la idea de integrar en el tiempo.** Con estos detectores no rinde (S1). El límite es un corrimiento del
  fondo que dura el día, no ruido.
- **Para la lectura de H15 etapa 3.** El εtot de la huella (0,06 a 0,16) no es emisividad de pluma (§5).
- **Para el dashboard:** nada. No se tocó `src/` ni la app.

Seguimientos (no se arreglaron aquí):

1. **La máscara de nubes de NOAA marca nublada la cumbre nevada de Chillán casi siempre.** En los cuatro días
   más despejados del bloque, 0 o 1 de los 6 píxeles de cumbre salen despejados (`resultados/h23_diag_acm.json`).
   Conviene revisarlo antes de usar ACMF o productos que dependen de ella cerca de cumbres con nieve.
2. **Una línea base de 10 días por percentil cae en nube cuando el periodo es nublado.** Le pasó al criterio de
   H23. H17 y H13 usaron líneas base temporales del mismo píxel: vale la pena comprobar si les pasó lo mismo.
3. **Tardes de octubre sin dato.** Para medir la tarde en Chillán haría falta un periodo con más tardes
   despejadas (verano) o aceptar las cumbres de control de noviembre como sustituto.
4. `eccodes` falla si se decodifica desde varios hilos a la vez ("flex scanner internal error"); se decodifica
   en serie (`scripts/h23_gfs.py`).

## 10. Archivos y reproducción

- `criterio_2026-11-22.md`, `enmienda_posthoc_1_2026-11-22.md`, `enmienda_posthoc_2_2026-11-22.md`.
- `scripts\`: `h23_comun.py` (rutas, Planck), `h23_bajar.py` (L1b C14 y C15), `h23_gfs.py` (temperatura del
  aire), `h23_bajar_acm.py` (máscara de NOAA), `h23_cubo.py` (cubos e I1 a I3), `h23_medir.py` (línea base,
  detectores, inyección, celdas, I4 a I6), `h23_resumen.py` (regla, tablas, figuras), `h23_pruebas.py` (pruebas
  numéricas), `h23_forma_rt.py` (S5), `h23_diag_i5.py`, `h23_diag_acm.py`, `h23_diag_ref.py` (diagnósticos de las
  enmiendas), `h23_eventos_extra.py` (§7, post hoc).
- `resultados\`: `h23_celdas.csv` (8.536 filas, una por celda), `h23_resumen.txt`, `h23_veredicto.json`,
  `h23_instrumento.json`, `h23_controles.json`, `h23_eventos.json`, `h23_eventos_extra.json`,
  `h23_forma_rt.json`, las tres figuras, y los diagnósticos de las dos corridas que cortaron
  (`h23_instrumento_corrida1_falla_I5.json`, `h23_instrumento_corrida2_falla_I5_sin_referencia.json`,
  `h23_diag_i5_corrida1.json`, `h23_diag_i5_intento_p90_bloque.json`, `h23_diag_acm.json`,
  `h23_diag_ref_oct_chillan.json`).
- Fuera del repo: `D:\goes_notas\s17\h23\` (761 MB: 7.751 cuadros L1b, 7.738 máscaras, 218 análisis GFS, dos
  cubos). Insumos de sólo lectura de otras pruebas: `D:\goes_cache\etapa3_chillan\dem_ventana.npz` (cota por
  píxel), `D:\goes_notas\local_f3a7d295\cache_rescatada\reproducir_volcat\latlon.npz` (lat y lon de la ventana),
  `D:\goes_cache\h13\gfs\` y el modelo radiativo de H3 (sólo para S5). No se leyó ningún archivo de evento de
  VOLCAT.

Reproducir, desde `docs\own_volcat\h23_inyeccion\scripts\`:

```powershell
python -I h23_bajar.py 12 todo
```

```powershell
python -I h23_gfs.py
```

```powershell
python -I h23_bajar_acm.py 12 todo
```

```powershell
python -I h23_cubo.py oct
```

```powershell
python -I h23_cubo.py nov
```

```powershell
python -I h23_pruebas.py
```

```powershell
python -I h23_medir.py
```

```powershell
python -I h23_resumen.py
```

```powershell
python -I h23_eventos_extra.py
```

S5 pide además `H3_RT_DL=D:\goes_cache\rt` y `H3_RT_LBL=D:\goes_notas\local_f3a7d295\h12_datos\extra\h3_meta\lbl`:

```powershell
python -I h23_forma_rt.py
```
