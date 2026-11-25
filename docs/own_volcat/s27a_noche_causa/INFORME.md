# S27a: ¿qué dispara de noche en 2026, pluma diaria, depósito de ceniza o nieve distinta? Informe, 25-11-2026

Criterio `criterio_2026-11-25.md` (commit `2c7af2b`) y su enmienda 1 (GFS de 1°, commit `85856a4`), los dos empujados
antes de cruzar un solo disparo con el viento. Código `scripts/s27a_viento.py` (viento), `scripts/s27a_medir.py`
(medida), `scripts/s27a_lado_a_lado.py` (videos). Resultado completo en `resultados/s27a_resultado.json`; la tabla de
cuadros nocturnos con disparo en `D:\goes_notas\s27\s27a\cuadros_noche_2026.csv`. Ningún día posterior al 24-11.

**En una línea: ninguna de las tres causas queda en pie por su regla.** El depósito queda descartado (no dura la noche
ni se ve de día). La nieve no se decide (Antuco dispara menos que en 2025 y Longaví apenas más). La pluma no se puede
probar con la prueba que escribí: puse un umbral de poder que, con 60 corrimientos, era imposible de cumplir (error
mío). Leído después: los disparos nocturnos **no siguen al viento** y caen siempre en los mismos píxeles de la
cumbre.

## 1. Para geólogo

**El fenómeno.** De noche, la zona de 0 a 4 km del cráter dispara en el 18 % de los cuadros de 2026 y en el 4 % de
2025 (175 de 961 contra 60 de 1.453). De los 179 cuadros nocturnos con disparo fuera de VOLCAT, 175 son de la zona y
4 del anillo: el exceso de noche vive en la cumbre. S26b descartó el calor. Aquí se probaron las otras tres
candidatas con la huella que cada una deja.

**Pluma: los píxeles que disparan no siguen al viento.** Una pluma de 3 a 6 km tiene que quedar a sotavento y moverse
cuando el viento cambia. Para cada disparo se corrigió la posición de sus píxeles por paralaje a 4,5 km y se comparó
su rumbo desde el cráter con el viento del GFS en esa capa (96 cuadros de 21 noches con viento de 3 m/s o más). El
acuerdo medio salió **C = −0,43**: los píxeles quedan en promedio del lado contrario al viento. Pero eso es la
geometría: la zona está centrada en el cráter real y, corregida por paralaje, mira casi sólo al norte, mientras el
viento sopla hacia el E y SE (mediana 124°). Con el viento de otras noches, el mismo cálculo da −0,52 de mediana:
**el viento real no ordena los disparos mejor que el viento de una noche cualquiera** (p = 0,34). Una pluma ideal en
la misma geometría sí lo haría (C = +0,77, ningún corrimiento la iguala).

Lo que se ve noche a noche (post hoc) es lo contrario de una pluma que deriva: los mismos dos píxeles, (43,46) y
(43,47), disparan con viento hacia 342° (08-11, calma), hacia 99° (14-11) y hacia 125° (12-11). En septiembre y
comienzos de octubre dispara otro, (41,46), a 1,2 km al norte del cráter, con viento hacia 117° a 154° de 14 a 23 m/s
(27-09, 05-10, 07-10), donde una pluma no puede estar.

**Depósito: no.** Un piso de ceniza en el suelo es fijo: dispararía toda la noche y se vería igual de día con cielo
despejado. En las noches con 12 o más cuadros evaluados, la mediana de cuadros con disparo es **7 %**; las rachas de
disparo duran una mediana de 2 cuadros (20 min), con máximo de 20 (3 h 20 min). En los tres píxeles que más disparan,
la anomalía de la BTD contra 2025 es de −0,24 K de noche y −0,20 K de tarde con cielo despejado: un corrimiento leve y
parejo, no la firma de un depósito (el criterio pedía −0,3 K o menos de día). Además los píxeles dominantes cambian
entre la primera y la segunda mitad (sólo comparten (43,47)).

**Nieve: no se decide, pero las vecinas no repiten lo de Chillán.** Con la misma regla puesta en Antuco y Longaví,
Antuco dispara de noche **menos** en 2026 que en 2025 (1,2 % contra 4,2 %) y Longaví algo más (6,4 % contra 3,8 %,
razón 1,7, p = 0,002). Chillán va de 4,1 % a 18,2 % (razón 4,4). Una temporada de nieve distinta en toda la zona
tendría que verse en las dos y con un salto parecido: no se ve. La regla pedía las dos en 3 veces o más para "sí" y
las dos en 1,5 o menos para "no"; Longaví quedó en medio. La fracción nocturna de Chillán no se acompaña con la de
Antuco (Spearman 0,23, p = 0,21) ni con la de Longaví (0,16, p = 0,38), ni con la temperatura de 700 hPa (0,03).

**Qué significa.** Lo que dispara de noche en 2026 está pegado a la cumbre, no sigue al viento, va y viene en pulsos
de decenas de minutos a pocas horas, y no aparece en las cumbres vecinas. No es un depósito ni una temporada de nieve
regional. Cabe una pluma que **no se aleja** del cráter: un pulso o una pluma débil sobre el cráter aparece por
paralaje justo en (43,46) y (43,47), la cumbre aparente a 3 a 5 km de altura, sin importar hacia dónde sople, y su
parte que deriva ya es demasiado tenue para el detector. Con píxeles de 2 km esa pluma y la superficie de la cumbre
caen en los mismos píxeles: **GOES no las separa por posición**. Lo de septiembre en (41,46), con viento fuerte y
nube cerca, no calza con pluma (post hoc: con nube dinámica de 20 a 50 % en el anillo la zona dispara en el 27 % de
los cuadros nocturnos; con anillo despejado, en el 16 %, todavía cuatro veces 2025).

## 2. Veredicto por la regla

| Prueba | Resultado | Veredicto |
|---|---|---|
| Comprobación de código | Seco de la unión 2025 269 de 5.499; disparos y píxeles de 2026 iguales a `tabla_2026.csv` (0 diferencias); la zona generalizada reproduce la de S25a exactamente | pasa |
| Viento | 641 horas de GFS 1°, ninguna falta | |
| P, poder (pluma ideal) | C = 0,77; p = 0,0164 (0 de 60 corrimientos la igualan) | **SIN PODER**: el criterio pedía p ≤ 0,01 |
| P, 2026 | C = −0,43 (96 cuadros, 21 noches); nulo mediana −0,52, p95 −0,25; p = 0,34; máximo del giro en 240° | |
| P, 2025 | C = +0,23 (97 cuadros, 11 noches); p = 0,052; máximo del giro en 0° | |
| P, sensibilidad 3,5 / 5,5 km | 2026 p = 0,80 / 0,33; 2025 p = 0,07 / 0,05 | |
| **P** | | **SIN PODER (no decidible)** |
| N, Antuco | 2025 62 de 1.476 (4,2 %); 2026 14 de 1.128 (1,2 %); R 0,30; p 1,0 | |
| N, Longaví | 2025 58 de 1.518 (3,8 %); 2026 63 de 979 (6,4 %); R 1,68; p 0,002 | |
| **N** | | **NO DECIDIBLE** (Antuco no, Longaví intermedio) |
| D2, fijo | Dominantes primera mitad (41,46), (41,45), (43,47); segunda (43,46), (43,47), (43,45): comparten 1 | no cumple |
| D3, toda la noche | Mediana de la fracción por noche 0,07 (31 noches) | no cumple |
| D4, de día | Mediana de A de tarde despejada −0,20 K (452 cuadros), de noche −0,24 K (777) | no cumple |
| **D** | | **DEPÓSITO NO** |

**El error de diseño en P.** Con 65 noches de 2026 y corrimientos de 3 a 62 días hay 60 nulos, así que el p más chico que la prueba
puede dar es 1/61 = 0,0164. Pedí p ≤ 0,01 al poder: inalcanzable para cualquier pluma. La pluma ideal llegó al piso
(ningún corrimiento le gana), así que la prueba sí tenía poder a nivel 0,05. **Leído con ese umbral (post hoc, no es
el veredicto):** 2026 da p = 0,34 > 0,20, que por la tabla del criterio sería **PLUMA NO**. Lo dejo escrito como
lectura, no como resultado.

Lo que no esperaba: en 2025 los disparos nocturnos siguen al viento algo (C = +0,23, p = 0,052, máximo del giro en
0°). Las noches de capa baja de S24 (las que ponen casi todo el disparo de 2025) son nube orográfica, que se ordena
con el viento. Expectativa escrita antes (§4) contra lo que salió: esperaba P sí o no decidible (salió sin poder por
mi umbral), N no (salió no decidible por Longaví), D no por D3 (así fue).

## 3. Lo que puede estar mal

- El GFS de 1° puede errar el viento de la cumbre (S22c lo vio errar una mañana). Un viento malo borra el acople;
  pero la pluma ideal se calculó con ese mismo viento, y lo que deja C negativo es la geometría, no el viento.
- La zona sólo mira, corregida a 4,5 km, el lado norte del cráter. Una pluma que deriva al E o SE sale de la zona a
  los pocos km y la debería ver el anillo, que casi no dispara de noche (4 cuadros). Eso no prueba que no haya pluma
  lejos: el anillo pide una firma que una pluma nocturna diluida quizá no tiene.
- Antuco y Longaví usan la misma regla pero su cumbre es más baja (zona de 1.450 a 2.300 m y 1.640 a 2.800 m contra
  1.950 a 2.870 m en Chillán): la nieve de la cumbre de Chillán puede comportarse distinto.
- D4 compara de tarde con la base de 2025 a la misma hora; una tarde con más sol en un año que en otro mueve A.

## 4. Videos para las cámaras del OVDAS (no deciden)

`C:\Users\nmend\Downloads\s27a_noche_detector_y_viento_chillan_<día>_0300-0850UTC_10min.mp4` para 27-09, 08-11 y 12-11
(00:00 a 05:50 hora de Chile). Izquierda VOLCAT (de noche casi nunca hay imagen); derecha el IR de 11 µm en gris,
amarillo = los dos píxeles de la zona cuando dispara, rojo = anillo, celeste = nube, **flecha verde = viento GFS de 3
a 6 km** (hacia donde sopla) y **cruz rosada = donde GOES ve algo que está a 4,5 km sobre el cráter**.

Qué mirar en las cámaras nocturnas (hora de Chile):

| Noche | Horas (Chile) | Qué marca GOES | Pregunta |
|---|---|---|---|
| 07-11 a 08-11 | 00:00 a 05:50 (25 cuadros) | (43,46) y (43,47), sobre la cumbre aparente; viento casi calmo | ¿hay pluma o pulsos sobre el cráter, aunque no se alejen? |
| 26-09 a 27-09 | 00:00 a 04:40 (23 cuadros) | (41,46), 1,2 km al N del cráter; viento de 23 m/s hacia el SE y mucha nube | ¿hay pluma, o nube sobre la cumbre? |
| 11-11 a 12-11 | 01:40 a 04:30 (15 cuadros) | (43,46) y (43,47); viento hacia el SE, 12 m/s | ¿pluma sobre el cráter que se inclina al SE? |
| 13-11 a 14-11 | 00:00 a 05:50 (16 cuadros) | (43,46) y (43,47); viento hacia el E | idem |
| 04-10 a 05-10 | 00:00 a 03:40 (11 cuadros) | (41,46); viento hacia el SE, 14 m/s | idem 27-09 |

Si las cámaras muestran pluma sobre el cráter las noches de noviembre y nada el 27-09, la lectura queda: en noviembre
la zona ve la pluma pegada al cráter, y lo de septiembre es otra cosa (nube o superficie al norte).

## 5. Lo que sigue

- Las cámaras del OVDAS en esas noches deciden lo que GOES no separa por posición.
- Si se rehace P, con su propio criterio: nulo con más resolución (rotar el viento de cada noche por los cuadros de
  las otras noches a la misma hora, o permutaciones de noches) y umbral de poder que la prueba pueda alcanzar.
- La confirmación de S23b, S25a y S26a en días nuevos sigue esperando a VOLCAT; nada de esta sesión la tocó.
