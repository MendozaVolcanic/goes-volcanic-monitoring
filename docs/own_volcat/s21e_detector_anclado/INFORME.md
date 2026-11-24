# S21e: detector de ceniza anclado al cráter, sin saber dónde mirar. Informe, 24-11-2026

Criterio `criterio_2026-11-24.md` (commit `6f51c96`, 02:14), enmienda 1 antes de medir
`enmienda_1_antes_de_medir_2026-11-24.md` y código (commit `c3fc8d7`, 02:20), ensayo en seco con los placebo solos
(commit `e52b935`, 02:21), los tres empujados antes de calcular S en los cuadros positivos. Código en
`C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\Goes\.claude\worktrees\kind-saha-d5da8b\docs\own_volcat\s21e_detector_anclado\scripts\s21e_medir.py`;
salidas en
`C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\Goes\.claude\worktrees\kind-saha-d5da8b\docs\own_volcat\s21e_detector_anclado\resultados\`
(`seco.json`, `s21e_resultado.json`, `composicion_U.json`, logs); figura en
`C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\Goes\.claude\worktrees\kind-saha-d5da8b\docs\own_volcat\s21e_detector_anclado\figuras\mapa_D_positivos.png`.

**Resultado en una línea: INVÁLIDA por la regla.** El ensayo en seco da falsa alarma media 0,33 (más que 0,10). La
causa no es el detector sino el cielo: a media mañana hay sólo 35 cuadros placebo despejados en 14 días, de tres
días, y uno (04-11) pone 25 de los 32 que fijan el umbral. Con los números que igual se midieron, ninguno de los dos
eventos dispara, y el poder a −0,97 K es 0,07 a 0,22: **aunque el seco hubiera pasado, la prueba habría quedado SIN
PODER**. La firma de un píxel (−1 K) no se distingue, a esta escala de nulo, del mínimo de 65 píxeles sin pluma.

## 1. El fenómeno, antes de los números

La ceniza fina hace que el píxel se vea más frío en 12 µm que en 11 µm (la BTD, 11 − 12 µm, baja). En S20b, con la
huella de la pluma medida por Landsat 8 (25-10) y Sentinel-2 (08-11), el píxel más cubierto bajó 0,97 K y 1,46 K
contra su propia historia despejada. Pero eso fue mirando **el** píxel que el satélite fino señalaba.

Un detector operativo no sabe cuál píxel mirar. Revisa los 65 píxeles a 12 km o menos del cráter (sin el bloque de
3 × 3 del cráter) y se queda con el más bajo. El problema es estadístico, no físico: entre 65 píxeles con ruido, el
más bajo siempre está bajo aunque no haya pluma. En días sin actividad y cielo despejado, a media mañana, ese
mínimo, tomado en pares de cuadros seguidos, tiene mediana −0,71 K y percentil 5 de −0,82 a −0,90 K, y en dos
cuadros sueltos del 26-10 llegó a −1,28 y −1,59 K. Una pluma que baja un
píxel 1 K queda apenas en el borde de ese ruido.

Además, el umbral sale de días despejados sin actividad a la misma hora, y en octubre y noviembre de 2026 casi no
los hay a media mañana: 26-10, 02-11 y 04-11 son los únicos con cuadros despejados entre 12:20 y 16:50 UTC. El 04-11
estuvo despejado toda la mañana y domina el umbral. Con tan pocos días, sacar uno cambia el umbral entero; eso es lo
que el ensayo en seco castiga.

## 2. Veredicto por la regla

| Paso | Resultado | Fuente |
|---|---|---|
| Ensayo en seco (§6), ventana 12:20 a 16:50 UTC | **Falsa alarma media 0,33**: 26-10 dispara 2 de 2, 02-11 0 de 5, 04-11 0 de 2 (los otros 25 cuadros del 04-11 quedan sin umbral al sacarlo); 11 días sin cuadros. 2 disparos en 9 cuadros | `resultados/seco.json` |
| Veredicto | **INVÁLIDA** (§5: falsa alarma mayor que 0,10) | `resultados/s21e_resultado.json` |

Lo medido igual (no decide; se informa porque la pregunta importa y el seco no lo pudo validar):

| Evento, cuadro | E1 | S (K) | U (K), ventana, n | Dispara | Mínimo de Z | Localiza | D en el píxel de verdad |
|---|---|---|---|---|---|---|---|
| 25-10 14:20 | despejado | −1,001 | −1,087, ±120 min, 32 | no | (44, 44), 8,6 km | a 1 píxel | −0,759 K (2.º de 65) |
| 25-10 14:30 | despejado | −1,042 | −1,087, ±120 min, 32 | no | (44, 43), 9,8 km | a 1 píxel | −0,905 K (2.º de 65) |
| 08-11 14:40 | despejado | −0,852 | −1,289, ±120 min, 32 | no | (41, 51), 10,0 km | no (5 píxeles) | −0,774 K (2.º de 64) |
| 08-11 14:50 | despejado | −0,894 | −1,290, ±120 min, 31 | no | (44, 47), 7,7 km | a 1 píxel | sin D (M1 sin 20 pares) |

| Evento | S del evento | p (nulo de pares) | Dispara | Localiza | Cumple |
|---|---|---|---|---|---|
| 25-10 | −1,042 K | **0,000** (0 de 28 pares, 12:20 a 16:30; p5 del nulo −0,82 K) | no | no | no |
| 08-11 | −0,894 K | 0,074 (2 de 27 pares, 12:40 a 16:50; p5 −0,90 K) | no | no | no |

Poder por cuadro positivo (200 inyecciones, semilla 0, con reposición sobre 31 o 32 cuadros; 8 a 13 inyecciones
cayeron en un píxel sin D):

| Cuadro | −0,97 K | −1,46 K |
|---|---|---|
| 25-10 14:20 | 0,215 | 0,785 |
| 25-10 14:30 | 0,175 | 0,710 |
| 08-11 14:40 | 0,070 | 0,485 |
| 08-11 14:50 | 0,075 | 0,505 |

**Si el seco hubiera pasado:** ninguno cumple y el poder a −0,97 K (el menor de los cuatro, 0,07; el mayor, 0,215)
queda muy bajo 0,8: **SIN PODER**. Ni con la firma del 08-11 (−1,46 K) llega a 0,8.

Lectura del 25-10: el p de 0,000 dice que el par de cuadros del 25-10 está más bajo que todos los pares placebo
consecutivos, y el mínimo cae al lado del píxel de verdad, en (44, 44) y (44, 43), un píxel al sur, que es donde
S20b ponía la pluma con la altura más 1 km (variante `f_mas`). Pero el umbral de cuadro sueltos lo fijan los dos
cuadros bajos del 26-10 (12:50 y 13:40, no consecutivos, por eso no entran al nulo de pares), y el 25-10 no los
alcanza. El 08-11 queda dentro del ruido: su mínimo de 14:40 está a 10 km, en otra parte.

## 3. Informativo (no decide)

- **Disparo por hora en los placebo** (umbral sin el propio día): en cuadros despejados, 21 de 244 (0,086); en
  cuadros nublados, 618 de 1.120 (0,55). Entre las 17:00 y las 22:59 UTC casi no hay umbral (no hay tardes
  despejadas, el mismo hueco de H23 y H24). El detector sólo tiene sentido con cielo despejado: una nube baja la BTD
  de cualquier píxel.
- **Los 60 cuadros con archivo de evento de VOLCAT** (13, 14 y 18-11): 29 despejados por E1, 43 evaluados, 18 con
  umbral; disparan 16 de 18 (8 de 8 despejados, 8 de 10 nublados). Los umbrales de la tarde salen de un solo día: a
  las 19:20 los 21 cuadros son del 04-11.
- **Los 4 nacimientos de VOLCAT.** Predicción escrita antes: no disparan. **Falla en los 3 evaluables:** 14-11 12:40
  (nublado, S −1,15 contra U −0,93, mínimo en (44, 49) a 9,7 km), 14-11 16:30 (despejado, S −1,41 contra U −1,04,
  mínimo en (41, 44) a 4,8 km; U de 27 cuadros, 22 del 04-11) y 18-11 10:10 (nublado, S −0,67 contra U −0,57, mínimo
  en (40, 44) a 6,2 km). El 13-11 19:00 no se evalúa (69 % de Z con D). Dos de los tres son cuadros nublados, donde
  los placebo disparan 55 % de las veces, así que no dicen nada de ceniza. El 14-11 16:30 despejado es el único
  limpio, con un umbral de un día y medio.
- **Pulsos del OVDAS (H24).** Mañana (E1 a E4, E6 a E8): 70 cuadros, todos con umbral, disparan 6 (0,086, la misma
  tasa que los placebo despejados), en 4 episodios. Tarde (E5, E9 a E14): 82 cuadros, 67 evaluados, sólo 23 con
  umbral; disparan 10 (E5 5 de 9, E13 5 de 6), con umbrales de 1 a 2 días.
- **Mapa de D en los cuatro positivos:** `figuras/mapa_D_positivos.png`. El 25-10 se ve una mancha de D negativa
  al SO y O del cráter (filas 42 a 44, columnas 41 a 44), con el mínimo al lado del píxel de verdad; el 08-11 no hay
  estructura clara alrededor del píxel de verdad, y el mínimo de 14:40 queda al E.

### Post hoc (mirado después del veredicto, no se usa para nada)

En el episodio E4 del 25-10 (pulso del REAV desde 14:44), los cuadros de 14:40, 14:50 y 15:00 disparan con S −1,68,
−1,92 y −1,41 K (U −1,29 y −1,15), con el mínimo en (44, 43) y (44, 42), a 10 y 11 km al OSO del cráter. Es la
dirección de la franja de Landsat (eje 252,5° en S21a1). Diez a treinta minutos después de la pasada de Landsat, el
mínimo de Z se corre hacia el OSO y baja más que cualquier placebo despejado de esa ventana. Sugiere que la pluma
del 25-10 creció y se alejó después de las 14:34; habría que probarlo con un criterio escrito antes, no con esta
lectura.

## 4. Lo que puede estar mal

- **El umbral descansa en tres días, y en dos cuadros.** U a las horas de los positivos es el percentil 5 de 31 o 32
  valores; con esos n, el percentil 5 cae entre el 2.º y el 3.º más bajo, y esos son 26-10 13:40 (−1,59 K), 04-11
  16:40 (−1,30 K) y 26-10 12:50 (−1,28 K). Por eso U salta de −1,09 a −1,29 K entre las 14:30 y las 14:40. Con más
  días despejados el umbral puede subir o bajar; el veredicto INVÁLIDA es justamente eso.
- **No se sabe qué son los dos cuadros bajos del 26-10.** El 26-10 no está en ninguna lista de actividad (REAV,
  VOLCAT, VCB), pero eso no prueba que no hubiera una bocanada. Si la hubo, el nulo está contaminado y el umbral es
  demasiado exigente. No se revisó.
- **El control del pareo a más de 15 km pierde píxeles altos.** El 08-11 14:50 el píxel de verdad no tiene 20 pares
  con su BT11 y su cota fuera de los 15 km, y queda sin D; en S20b sí lo tenía (el control excluía sólo la huella).
  Pasa en 0 a 2 de los 65 píxeles de Z en los positivos y en 4 a 7 % de las inyecciones del poder.
- **E1 mira el terreno bajo, no la cumbre.** Un cuadro "despejado" puede tener nube en Z; eso también puede explicar
  los cuadros bajos del 26-10 y los disparos de la tarde.
- **El cráter en (42, 46)** está a 1,82 km de la coordenada; el píxel más cercano es (41, 46). Los dos quedan en el
  bloque excluido; Z se mide desde la coordenada (enmienda 1, §2).
- **Dos eventos, de mañana, despejados.** Aunque hubiera pasado, no diría nada de tarde ni con nubes (§8 del
  criterio). Sin VIIRS y sin 1,6 µm.

## 5. Qué deja esto

La pregunta operativa queda sin decidir por falta de nulo, pero los números que sí se midieron apuntan a lo que
esperaba el criterio (PARCIAL o NO DETECTA): la firma de −1 K de un píxel no sale sola del ruido de buscarla en 65
píxeles (poder 0,07 a 0,22). Para −1,46 K el poder sube a 0,49 a 0,79. Un detector propio necesitaría o una firma
más grande (plumas más gruesas o más cuadros por evento), o un nulo con muchos más días despejados de mañana (el
verano), o reducir dónde buscar sin saber la respuesta (por ejemplo, el sector a sotavento del GFS, criterio aparte).
