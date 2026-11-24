# S21b: bandas reflejadas de GOES-19 sobre Nevados de Chillán. Informe, 24-11-2026

Criterio: `criterio_2026-11-24.md`, commit `36be2bc`, empujado antes de bajar un solo cuadro. Scripts en `scripts/`,
salidas en `resultados/`, figuras en `figuras/`. Ventanas de L1b (C02, C05 y C06, 317 cuadros, 35 MB) en
`D:\goes_notas\s21\b\l1b\`.

**Veredictos por la regla escrita:**

- **Prueba 1 (franja de Landsat del 25-10 14:34, en la grilla de C02, C05 y C06): SIN PODER en las tres bandas.** S
  da entre 2,6 y 2,9 veces lo esperado en las tres, pero p 0,07 a 0,12 contra el nulo espacial de toda la ventana, y la
  pluma de Landsat pintada sobre los días base no supera ese nulo en ninguno (poder 0 de 3). Falsas alarmas en seco: 0
  de 3.
- **Prueba 2 (pulsos de la tarde del 28-10, E10, E11, E12): SIN SEÑAL en los tres pulsos; episodio NO
  CONCLUYENTE**, porque el poder del diseño es 0,03 a 0,05 (la regla pide 0,8 para poder decir DESCARTA).

Lo que se ve, separado de la regla (post hoc, §3 y §5): a 1,6 µm hay una mancha clara sobre la huella proyectada que
sube y baja en 30 minutos el 25-10, mientras los días base se quedan planos. Y las tardes de control no estaban
despejadas en la cumbre: E1 no ve los cúmulos de cordillera.

## 1. El fenómeno, antes de los números

Sobre nieve, una pluma con ceniza se ve distinto según la banda. En el rojo (C02) la nieve es muy clara y la pluma la
oscurece. A 1,6 µm (C05) la nieve absorbe y queda oscura, y la pluma, que dispersa parejo, se ve clara. Landsat 8 lo
mostró el 25-10 a las 14:34 dentro de la franja: rojo 0,63 a 0,41, 1,6 µm 0,01 a 0,12, 2,2 µm 0,01 a 0,10.

GOES-19 mira Chillán desde el norte con 43° de cenital, así que la pluma a 4,3 km aparece unos 4 km al sur de su
vertical, sobre otro fondo. El visible de 0,5 km es del tamaño de la franja: un píxel de C02 queda cubierto hasta el
83 % por ella, uno de C05 hasta el 44 % y uno de C06 hasta el 19 % (el mismo 18 % que midió S20b en el infrarrojo).

La pregunta de la prueba 1 era si esa franja cambia la reflectancia de GOES en esos píxeles más de lo que cambian solos
de un día despejado a otro. La de la prueba 2, si los pulsos de la tarde del 28-10 (los que VOLCAT marcó) dejan un
rasgo que sale del cráter entre el cuadro de antes y el de después.

## 2. Prueba 1 por la regla

Cuadro 14:30 (Chillán mirado a las 14:38:39, 4 min después de Landsat). La regla de nubes descartó el 27-09 (45 % de
los píxeles de C05 a 15 km con ρ05 > 0,30); quedaron 15, 16 y 17-10. S = amplitud de la anomalía en unidades de lo
esperado por el modelo fijado con Landsat (1 = todo, 0 = nada). p = fracción de corrimientos de la huella, con fondo
comparable, que dan S igual o mayor.

| Banda | Píxeles en la huella | S | p (corrimientos) | Falsas alarmas en seco | Poder (P entero / mitad) | Veredicto |
|---|---|---|---|---|---|---|
| C02 (0,5 km) | 40 | +2,72 | 0,071 (17.821) | 0 de 3 | 0 de 3 / 0 de 3 | **SIN PODER** |
| C05 (1 km) | 25 | +2,63 | 0,123 (1.901) | 0 de 3 | 0 de 3 / 0 de 3 | **SIN PODER** |
| C06 (2 km) | 16 | +2,90 | 0,074 (856) | 0 de 3 | 0 de 3 / 0 de 3 | **SIN PODER** |

Informativos (no deciden): 14:20 da S de 2,2 a 3,8 con p 0,08 a 0,13; 14:40, S de 1,4 a 2,9 con p 0,06 a 0,20;
H − 1 km y H + 1 km, p de 0,05 a 0,31. Con 02-11 y 04-11 sumados a la base (5 días, dos después del 24-10), **C05 da
SEÑAL (p 0,003) y C06 SEÑAL (p < 0,001)**, C02 no (p 0,022, sobre 0,017). Ese caso no decide porque esos dos días
pueden tener ceniza en la nieve, y el 02-11 tiene nube en el píxel más cubierto de C05 (ρ05 0,30).

En el píxel más cubierto de C05 (f 0,44): 25-10 14:30 ρ05 = 0,134; días base 0,077, 0,075, 0,086. La anomalía es
+0,058 y el modelo esperaba +0,030. A las 14:20 es +0,092 y a las 14:40 +0,026. En el de C02 (f 0,83) el fondo que
ve GOES es mixto (ρ02 0,24, no nieve limpia), el modelo esperaba −0,013 y se midió +0,018; a las 14:40, −0,055.

**Por qué SIN PODER.** El nulo usa toda la ventana bajada (de Longaví a Antuco, 145 por 70 km), y en ella hay nubes en
algún día base lejos del cráter: una huella corrida sobre una nube de un día base da S grandes (p95 del nulo 4,2 en
C02 y 10,3 en C05). Con eso, ni la pluma de Landsat entera, pintada sobre cada día base, alcanza p ≤ 0,017. La regla
de nubes del criterio sólo miraba 15 km alrededor del cráter, y el nulo no se limitó a esa zona. Es un defecto del
diseño, no del dato: queda dicho así y no se arregla el veredicto.

## 3. Prueba 1, controles post hoc (escritos después de ver SIN PODER; no cambian el veredicto)

Script `scripts/s21b_posthoc1.py`, salida `resultados/posthoc1.json` y `posthoc1.log`, figura
`figuras/posthoc1_altura.png`.

- **(a) Nulo dentro de 15 km del cráter** (la zona que revisa la regla de nubes): C02 p 0,033 (696 corrimientos,
  poder 0,67); C05 p < 0,014, ningún corrimiento iguala la S real, pero son sólo 72 (bajo el mínimo de 200 que puso el
  criterio, y poder 0 de 3 con 2 días de base); C06 p < 0,07 con 14 corrimientos. No alcanza para cambiar nada: es
  la misma prueba con un nulo elegido después.
- **(b) ¿Pluma en el aire o ceniza en la nieve?** Si la mancha fuera depósito, S sería máximo con la huella puesta en
  la cota del suelo. Con la huella en el suelo, S es 1,5 a 2,5; puesta en el aire, sube a 4,1 a 4,7 en 5 a 5,5 km en las
  tres bandas. Apunta al aire, pero la curva es ancha y ruidosa (S ≥ 1,5 en todas las alturas), así que no separa
  limpio.
- **(c) La serie es lo más claro.** Reflectancia a 1,6 µm media en la huella (puesta a 4,3 km), de 14:00 a 15:00:

| Día | 14:00 | 14:10 | 14:20 | 14:30 | 14:40 | 14:50 | 15:00 |
|---|---|---|---|---|---|---|---|
| 15-10 | 0,088 | 0,095 | 0,091 | 0,099 | 0,096 | 0,101 | 0,101 |
| 16-10 | 0,091 | 0,092 | 0,096 | 0,099 | 0,099 | 0,098 | 0,110 |
| 17-10 | 0,094 | 0,099 | 0,109 | 0,113 | 0,119 | 0,116 | 0,110 |
| **25-10** | **0,133** | **0,160** | **0,167** | **0,148** | **0,126** | **0,117** | **0,120** |
| 04-11 (antes de las nubes) | 0,088 | 0,086 | 0,092 | 0,098 | 0,140 | 0,237 | 0,303 |

  Los días base suben 0,01 a 0,02 en la hora (el sol). El 25-10 sube a 0,167 a las 14:20 y baja a 0,117 a las 14:50:
  cambia 0,05 en media hora. Ceniza depositada en la nieve no hace eso. El 04-11, después de toda la actividad de
  octubre, el mismo lugar vuelve a 0,088 a 0,098 antes de que lleguen las nubes: no quedó un depósito que se vea a
  1,6 µm (o lo tapó nieve nueva; no se sabe). En C02 el lugar donde cae la sombra (la huella en su cota de suelo) pasa
  de 0,47 a 0,50 en los días base a 0,25 a 0,36 el 25-10, y se aclara en la hora; la sombra de la pluma cae casi
  encima de su vertical esa mañana (sol del NE, 35° de cenital).

Lectura: algo que está en el aire sobre la huella de Landsat aclara el píxel de 1,6 µm en +0,05 a +0,09 a las 14:10 a
14:30 y se diluye después. Es lo esperable de la franja que Landsat vio a las 14:34, entre el pulso de las 13:15 y la
serie que empieza a las 14:44. Es post hoc, con 3 días base y un nulo que la regla no pidió.

## 4. Prueba 2 por la regla

T = el sector de 30° (de 24, alrededor del cráter aparente, de 1 a 10 km) que más cambia entre el cuadro de antes del
pulso (R) y el de después (P), descontado el cambio parejo del anillo. Nulo: pares de cuadros igual de separados en las
tardes despejadas por E1 del 21-09, 17-10 y 04-11.

| Pulso | R → P (Chillán mirado) | Nulo | C02: T, p | C05: T, p | Antuco / Longaví | Poder del pulso | Veredicto |
|---|---|---|---|---|---|---|---|
| E10, 17:38, 2.200 m | 17:28:39 → 17:48:39 | 39 pares, ±120 min | 0,027; 0,90 | 0,009; 0,88 | p ≥ 0,97 | 0,00 (0,03 contra los n) | SIN SEÑAL |
| E11, 20:32, 2.440 m | 20:28:39 → 20:38:39 | 52 pares, ±90 min | 0,029; 0,98 | 0,025; 0,87 | p = 1 | 0,03 | SIN SEÑAL |
| E12, 21:49, 2.020 m | 21:38:39 → 21:58:39 | 45 pares, ±120 min | 0,057; 0,89 | 0,062; 0,72 | p ≥ 0,61 | 0,05 | SIN SEÑAL |

**Episodio del 28-10: NO CONCLUYENTE** (0 de 3 con SEÑAL; 0 de 3 con poder ≥ 0,8). Ningún cuadro informativo (17:30,
20:40, 21:40, 22:00) baja de p 0,56.

El 28-10 cambia **menos** entre cuadros que las tardes de control: su T está bajo la mediana del nulo (0,07 en C02).
La franja del 25-10 pintada en los pares nulos da T de 0,06 a 0,11 de mediana, dentro de ese nulo.

## 5. Prueba 2, controles post hoc (no cambian el veredicto)

Script `scripts/s21b_posthoc2.py`, salida `resultados/posthoc2.json` y `posthoc2.log`.

- **(a) Las tardes de control tienen nubes en la cumbre.** En 33 de 39, 48 de 52 y 42 de 45 pares nulos, más del 1 %
  del anillo de Chillán tiene ρ05 > 0,30 (nube de agua; la nieve no pasa de 0,15 a 1,6 µm). El 28-10 tiene 0 a 2 %.
  E1 mira el terreno bajo de 10 a 30 km y no ve los cúmulos de cordillera. Es la misma lección que S20c en el
  infrarrojo, ahora en reflejado: **los días "despejados" de control no lo están donde importa**, y de tarde, antes
  del 24-10, casi no hay tardes limpias en la cumbre (quedan 3 a 6 pares sin nube, que no alcanzan para un p).
- **(b) Nulo del mismo día.** Con todos los pares del 28-10 de 16:00 a 22:30 igual de separados, los pares de los
  pulsos quedan en el puesto 26 y 28 de 38 (E10), 16 y 12 de 39 (E11), 12 y 9 de 38 (E12) en C02 y C05. Los cambios
  más grandes de la tarde son entre 21:30 y 22:10, con el sol bajo, y Antuco también los tiene. Pero este nulo
  tampoco tiene poder: la franja pintada supera su percentil 95 sólo en 12 a 27 % de los casos.

Lectura: con un promedio por sectores de 30°, una franja de 1,2 km llena un tercio del sector, y de tarde, con el sol
moviéndose 2 a 3° entre cuadros sobre laderas de nieve, el sector cambia lo mismo sin pluma. La prueba 2 no puede
decir si los pulsos dejan rasgo en reflejado. Las figuras (`figuras/prueba2_pulsos.png`) muestran en E11 y E12, en
C05, una franja hacia el sur del cráter (rumbo 180° a 195°, el de la paralaje de una columna); con este diseño es del
tamaño del ruido y no se lee como hallazgo.

## 6. Correcciones de implementación, después de medir

- **Cuadros sin luz.** El nulo de E12 incluía cuadros de las 22:50 a 23:00 del 21-09, después de la puesta del sol,
  sin reflectancia: el script se detuvo. Se excluyen los cuadros con menos de la mitad del anillo con dato
  (`con_luz`). Afecta sólo a qué pares nulos existen.
- **Poder con 39 pares.** El criterio dice "contra los demás pares nulos": con 39 pares, dejar uno fuera da un p
  mínimo de 1/39 = 0,0256, sobre 0,025, y el poder de E10 da 0 por construcción. Se informa además contra los n pares
  sin pintar (0,03 en E10); no cambia nada.
- **f de C06 contra S20b.** La suma de f es la misma (0,268); el máximo difiere 0,005 (0,186 contra 0,181) por cómo se
  calcula el área del píxel. Lat/lon de la grilla calza con la de H23 a 1e-5°.
- **Hora de barrido.** El L1b sólo trae inicio y fin; interpolando lineal por fila, Chillán se mira 8 min 20 s después
  del minuto nominal; S19 dio 8 min 39 s por tabla de franjas. Ningún cuadro de la tabla de §4 cambia.
- Falta un cuadro (21-09 18:40, sin C06 en el bucket).

## 7. Qué significa

1. **La pregunta de la mañana sigue abierta por diseño, no por dato.** La mancha de 1,6 µm sobre la huella existe, es
   del tamaño que el modelo predice (dos veces más) y cambia en media hora como una pluma; la regla no la pudo
   aceptar porque el nulo de toda la ventana estaba contaminado por nubes de los días base. Sumado a S20b (firma de
   −1 K en 11 − 12 µm en el píxel vecino), GOES-19 ve algo de la pluma del 25-10 en dos regiones del espectro cuando
   se sabe dónde mirar.
2. **La banda de 1,6 µm es la que sirve sobre nieve**, como decía Schmit 2005: en C05 la anomalía tiene el signo y el
   tamaño esperados. En C02 el fondo que ve GOES detrás de la pluma es mixto (nieve y roca), y la señal cambia de signo
   de un píxel al otro: el visible de 0,5 km no es una ventaja automática.
3. **Las tardes del 28-10 no se pueden decidir con controles de otros días**: no hay tardes limpias en la cumbre antes
   del 24-10. Eso cierra el camino "mismo cuadro, otro día" para la tarde, en IR (S20c) y ahora en reflejado.
4. **Nada de esto es todavía un detector.** Es una medida en una huella conocida.

## 8. Lo que puede estar mal

- **Tres días base** para la mañana, todos de mediados de octubre, con el sol 3° más bajo que el 25-10. La subida de
  0,01 a 0,02 por hora de los días base es del sol; el 25-10 sube y baja 0,05 en media hora, que el sol no hace.
- **El modelo de pluma** sale de Landsat de superficie al nadir; GOES mide techo de atmósfera a 43° y con otra
  dispersión. Por eso S = 2,6 a 2,9 no se lee como "la pluma es 2,7 veces más densa": puede ser geometría.
- **La pluma se mueve entre 14:34 (Landsat) y 14:38 (GOES)**, y es una franja continua que se renueva, no un objeto
  fijo. La huella de Landsat es la mejor posición disponible, no la exacta.
- **Los controles post hoc los pedí yo después de ver el resultado.** La serie (c) es la más difícil de fabricar
  (no tiene ningún parámetro elegido), pero sigue siendo post hoc.

## 9. Lo siguiente

- Repetir la prueba 1 con el **nulo limitado a la zona revisada por la regla de nubes**, escrito antes, en otra pasada
  Landsat o Sentinel-2 con pluma sobre nieve (08-11 14:53 y 13-11 tienen escena; 29-10 también). Barato: ventanas de
  35 MB.
- Para la tarde, un estadístico **a escala de píxel y con la huella dada por otra fuente** (GOES-18 en estéreo, S21c;
  o el PNG de VOLCAT en la carpeta de notas), no un promedio de sectores sin dirección. Y controles con la cumbre
  limpia medida en C05, no en E1.
- El verano (`h24_verano/REGISTRO_PROSPECTIVO.md`) sigue siendo la ocasión de tardes limpias.
