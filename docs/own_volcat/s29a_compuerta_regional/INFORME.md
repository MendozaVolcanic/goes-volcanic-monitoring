# S29a: qué hace disparar a la cumbre de Antuco de día, y compuerta regional para S26a. Informe, 26-11-2026

**Parte 1 (comprobación óptica): NINGUNA DE LAS TRES SE SOSTIENE; la nieve va al revés.** En 2026 la cumbre de
Antuco tiene más nieve que en 2025, no menos, sin nieve más sucia, y sólo uno de cuatro días de disparo con paso
cercano muestra nube en la zona. **Parte 2 (compuerta regional): NO CONCLUYENTE.** Lo regional existe (p 0,015, el
mínimo posible), y la compuerta conserva ALCANZA (52 de 93) y borra más falsas alarmas que aciertos. Pero con la
medida que fijé antes la diferencia no sale del ruido. Post hoc, en 2025 anula el 61 % de las falsas alarmas diurnas
de Chillán contra el 17 % de los aciertos de 2026.

Documentos escritos y empujados antes de mirar: `parte1_expectativas_2026-11-25.md` (commit `c42190c`) y
`criterio_2026-11-25.md` (commit `d5510a5`). Código en `scripts/`; resultados en `resultados/`; lo grande en
`D:\goes_notas\s29\s29a\`. Ningún día posterior al 24-11-2026.

## 1. Para geólogo

### Parte 1: ¿por qué la cumbre de Antuco dispara más de día en 2026?

**La pregunta.** S28a vio que la zona de 0 a 4 km de la cumbre de Antuco, que no tiene pluma, dispara de día casi
cuatro veces más en oct-nov 2026 que en 2025. Antes de mirar escribí tres explicaciones posibles: (1) menos nieve y
más roca al sol, (2) ceniza o polvo sobre la nieve, (3) cúmulos o nube baja que la máscara de GOES no marca. Esperaba
la primera.

**Lo que se ve.** Se midieron 244 escenas Sentinel-2 y Landsat 8/9 de las tres cumbres entre el 21-09 y el 21-11 de
2025 y entre el 21-09 y el 24-11 de 2026, en un círculo de 4 km alrededor de cada cumbre (la zona del detector).

- **La nieve va al revés.** En 2026 la cumbre de Antuco está mucho más nevada que en la misma fecha de 2025: a
  mediados de noviembre de 2025 la nieve cubría 21 a 35 % de la zona y en 2026 cubre 68 a 71 %. En 45 de 50 pares
  por fecha 2026 tiene al menos 0,15 más de nieve; en ninguno tiene menos. La temporada de 2026 va unas cuatro semanas
  atrasada. Longaví también tiene más nieve en 2026 (mediana +0,17) y no subió sus disparos. Chillán tiene casi la
  misma nieve los dos años (+0,02). Comparar `figuras/antuco_2025-11-12_sentinel-2a.jpg` (media cumbre descubierta)
  con `figuras/antuco_2026-11-11_landsat-9.jpg` (cono entero nevado).
- **No hay nieve más sucia.** La nieve oscurecida (NDSI alto con verde entre 0,3 y 0,6) es algo menor en 2026
  (mediana −0,06). En el visible no hay ceniza de Chillán sobre Antuco.
- **Nube: sólo el 10-11.** De los cuatro días de 2026 en que Antuco disparó a menos de 1 h de un paso (29-10, 08-11,
  10-11, 11-11), sólo el 10-11 tiene nube en la zona: cúmulos de agua sobre el flanco NO a las 14:43 UTC, el 18 % de
  la zona según la máscara (bajo el 20 % que pedí), con disparos de 13:50 a 14:30 y de 15:20 a 15:40
  (`figuras/antuco_2026-11-10_sentinel-2b.jpg`). Ese mismo paso muestra a Longaví rodeado por una capa de nube baja que
  deja asomar sólo el cono (`figuras/longavi_2026-11-10_sentinel-2b.jpg`). El 11-11, en cambio, la zona de Antuco
  dispara de 14:20 a 15:20 con el cielo limpio a las 14:28 (Landsat 9), y el 08-11 también está limpio.

**Lectura.** La explicación que esperaba (menos nieve, roca al sol) está refutada: la superficie de 2026 es más
blanca, no más oscura. La ceniza tampoco aparece. La nube baja explica bien el 10-11, el día más fuerte y el que
juntó a las tres cumbres, pero no el 11-11 ni el 08-11. Lo que sí cambia, y mucho, es que **la cumbre de Antuco de
2026 no es la superficie con que se armó su base de 2025**: la base por píxel y por hora salió de una cumbre a medio
descubrir, y en 2026 la misma cumbre está cubierta. Por la regla escrita antes eso no cuenta como explicación (el
óptico no dice el signo del efecto sobre la BTD 11 a 12 µm). Pero apunta a que la falsa alarma de una zona de cumbre
depende de la nieve del año, y Chillán, con la nieve parecida en los dos años, es justo la cumbre donde menos debería
pesar.

**Límite.** Sentinel-2 y Landsat pasan a las 14:30 a 14:55 UTC. La mayoría de los disparos son de tarde y una nube de
las 18:00 no se ve en una imagen de media mañana. El anillo de 4 a 40 km (el 29-10 de Antuco es casi todo anillo)
queda fuera de las ventanas de 5 km.

### Parte 2: anular los disparos de Chillán que ocurren a la vez que los de una cumbre sin pluma

**La idea.** Una pluma es de un volcán. Si a la misma hora disparan también Antuco o Longaví, que no tienen pluma, lo
más probable es que el disparo de Chillán sea lo mismo que el de ellas (la tarde, una capa de nube, el sol sobre la
nieve), no pluma. La regla (S26a+G): de 12:00 a 23:50 UTC, un disparo de Chillán se anula si Antuco o Longaví
disparan en el mismo cuadro, el anterior o el siguiente.

**Lo regional existe.** En 2026 las dos cumbres sin pluma disparan juntas de día en 23 cuadros. Corriendo una de las
dos series a otro día, el promedio es 2,9 y el máximo de 64 réplicas es 11 (p 0,015, el mínimo que permiten 64
réplicas). En 2025 pasa algo parecido (16 contra 4,2; p 0,065).

**Lo que cuesta.** S26a+G conserva el rótulo de S26a: **52 de 93 cuadros P de VOLCAT** (antes 63; R 0,56; ALCANZA,
desarrollo). Los 11 aciertos perdidos son del 14-11 (7), 28-10 (3) y 08-11 (1). El 10-11 no pierde ninguno, y es el
mejor ejemplo de lo que la compuerta busca: Chillán dispara de 15:40 a 19:40 UTC a la par con Antuco (13:50 a 20:40) y
Longaví (16:00 a 19:50), y la compuerta anula esos disparos; los cuadros de VOLCAT de Chillán empiezan a las 21:30,
cuando las vecinas ya se apagaron, y ahí los disparos de Chillán quedan.

**Lo que limpia.** En las dos cumbres sin pluma de 2026, usando la otra como compuerta, se anula el 22 % de los
disparos diurnos (46 de 210). En Chillán se pierde el 17 % de los aciertos. La compuerta borra algo más de lo que
debe que de lo que no, pero con sólo 6 días de Chillán con aciertos el intervalo de la diferencia va de −0,23 a
+0,34. Por la regla escrita antes: **NO CONCLUYENTE**. La medida que elegí es floja por construcción: Longaví casi no
dispara, así que como compuerta de Antuco apenas toca su exceso (el R de Antuco con compuerta queda en 2,70).

**Lo que se vio después y pesa (post hoc).** En 2025, el año sin pluma, la compuerta abre sólo en el 10 % de los
cuadros diurnos de Chillán y **anula 64 de sus 105 falsas alarmas diurnas (61 %)**: 29 de 38 el 14-11-2025, 14 de 18
el 18-11, 10 de 10 el 27-10, 8 de 11 el 13-11. Con vecinas de otro día anularía 6,5 (p 0,016, el mínimo). La falsa
alarma de 2025 de S26a baja de 4,9 % a 3,7 %, y la de día de 3,9 % a 1,5 %. Contra el 17 % de aciertos perdidos, la
diferencia es +0,43 (intervalo 0,08 a 0,65). En 2026, de los cuadros de día fuera de VOLCAT con disparo, la compuerta
anula 18 de 32. Dicho en una frase: **la mayor parte de lo que Chillán dispara de día sin pluma lo disparan también
sus vecinas**, y la compuerta lo saca a un costo de uno de cada seis aciertos. Ésa es la señal de una buena candidata,
pero la vi después de fijar la regla de decisión y no puede cambiar el veredicto.

**Para S26a.** El detector sigue siendo S26a: no hay criterio de confirmación de S26a+G (el criterio §6 lo pide sólo
si sale CANDIDATA). Lo que sí deja esto es una propuesta concreta para la coordinadora y Nicolás: medir S26a+G en los
días nuevos como cuarta medida informativa, con criterio escrito antes (usando f_FA25 y el nulo de corrimiento, que
son las medidas que sí separan), o reformularla como pregunta nueva con fondo de 2024 (S25b dejó el cubo en D:) para
medir la falsa alarma con compuerta fuera de muestra.

## 2. Cifras

### Parte 1 (`resultados/s29a_optico_lectura.json`, `resultados/s29a_optico_escenas.csv`)

Escenas con nube < 0,10 en la zona y dato completo; pares 2026 contra 2025 a ±10 días de la fecha del año.

| Cumbre | Escenas 2026 / 2025 | Pares | Diferencia de nieve (mediana) | Pares con ≥ 0,15 más / menos nieve en 2026 | Diferencia de nieve oscurecida | Pares con ≥ 0,15 más sucia |
|---|---|---|---|---|---|---|
| Antuco | 11 / 18 | 50 | +0,33 | 45 / 0 | −0,06 | 0 |
| Longaví | 14 / 22 | 97 | +0,17 | 54 / 4 | −0,05 | 0 |
| Chillán | 11 / 22 | 72 | +0,02 | 2 / 0 | −0,01 | 0 |

Días de disparo de la unión con paso a menos de 1 h (nube en la zona según SCL o QA; regla: ≥ 0,20):

| Cumbre | Paso (UTC) | Disparos a 1 h | Nube en la zona | Nube a 4 a 5 km |
|---|---|---|---|---|
| Antuco | 07-10-2025 14:29 L9 | 1 (zona) | 0,00 | 0,01 |
| Antuco | 29-10-2026 14:53 S2C | 10 (anillo) | 0,00 | 0,00 |
| Antuco | 08-11-2026 14:53 S2C | 2 (zona) | 0,00 | 0,00 |
| Antuco | 10-11-2026 14:43 S2B | 8 (zona) | 0,18 | 0,18 |
| Antuco | 11-11-2026 14:28 L9 | 7 (zona) | 0,01 | 0,01 |
| Longaví | 05-11-2025 14:42 S2B | 1 (zona) | 0,02 | 0,00 |
| Longaví | 07-11-2025 14:34 L8 | 3 (zona) | 0,55 | 0,35 |
| Longaví | 07-11-2026 14:42 S2A | 1 (anillo) | 0,01 | 0,02 |

Lectura por la regla (§1 de las expectativas): explicación 1 no (2026 con más nieve en 45 de 50 pares), 2 no (ningún
par más sucio), 3 no en la mayoría (1 de 4 días de Antuco 2026 con nube, y bajo el 20 %). Resultado: ninguna de las
tres que el óptico ve.

### Parte 2 (`resultados/s29a_resultado.json`, `resultados/s29a_posthoc.json`)

Comprobaciones antes de leer: los cuadros de las vecinas dan los totales de S28a (noche y día, 2025 y 2026); Chillán
recalculado da el seco 269 / 5.499 y 0 diferencias con `tabla_2026.csv` (disparo, evaluación y clase de VOLCAT).

| | S26a | S26a+G |
|---|---|---|
| P de VOLCAT alcanzados (2026) | 63 / 93 (R 0,677) | 52 / 93 (R 0,559) |
| p25; pN | 6e-53; 2e-22 | 6e-45; 1e-18 |
| Días con alcance | 6 | 6 |
| Rótulo | ALCANZA (desarrollo) | ALCANZA (desarrollo) |
| Seco 2025, global | 269 / 5.499 (4,9 %) | 205 / 5.499 (3,7 %) |
| Seco 2025, de día | 105 / 2.704 (3,9 %) | 41 / 2.704 (1,5 %) |
| N de 2026 de día con disparo | 32 / 594 | 14 / 594 |

| Medida del criterio | Valor |
|---|---|
| M4 sincronía Antuco y Longaví, día 2026 | 23 cuadros; nulo media 2,9, máx 11 de 64; **p 0,015** (mínimo 1/65) |
| M4 informativo, 2025 | 16; nulo media 4,2, máx 22 de 61; p 0,065 |
| M4 informativo, aciertos perdidos por Chillán | 11; nulo media 3,0 (0 a 24); p 0,077 |
| M3 f_FA26 (vecinas, la otra como compuerta) | 46 / 210 = 0,219 |
| f_P (aciertos perdidos) | 11 / 63 = 0,175 |
| M5 d = f_FA26 − f_P | +0,044; IC 95 % −0,23 a +0,34 |
| **Veredicto** | **NO CONCLUYENTE** |

M3 (R = tasa 2026 / tasa 2025, de día; intervalo por remuestreo de días): Antuco sin compuerta 2,64 (1,05 a 8,98), con
Longaví como compuerta 2,70 (1,05 a 11,5); Longaví sin compuerta 0,80 (0,22 a 2,18), con Antuco 0,56 (0,21 a 1,39).

Sensibilidades (no deciden):

| Variante | P alcanzados | f_P | f_FA26 | Seco 2025 global |
|---|---|---|---|---|
| Ventana 0 (mismo cuadro) | 62 | 0,016 | 0,181 | 4,0 % |
| Ventana ±3 cuadros | 40 | 0,365 | 0,276 | 3,5 % |
| Las dos vecinas a la vez | 63 | 0,000 | n/a | 4,7 % |
| Todo el día (también de noche) | 52 | 0,175 | 0,151 | 2,3 % |
| Sólo Antuco | 54 | 0,143 | 0,219 | 3,9 % |
| Sólo Longaví | 61 | 0,032 | 0,219 | 4,5 % |

La ventana de un solo cuadro conserva casi todos los aciertos (62) y aún anula 18 % de los disparos de las vecinas.
Lo anoto, pero no lo puedo usar: lo elegiría por haberlo visto.

Post hoc: compuerta abierta en el 10,1 % de los cuadros diurnos evaluados de 2025, el 17,0 % de 2026 y el 28,4 % de
los P de 2026 (las tardes de pluma son también tardes regionales). f_FA25 0,61 (64 de 105) contra nulo 6,5 de 105
(máx 29 de 61; p 0,016); d25 = f_FA25 − f_P = +0,43 (0,08 a 0,65).

Lo que esperaba (criterio §7) contra lo que salió: esperaba NO SIRVE, con 10 a 20 aciertos perdidos y f_FA26 parecido
o menor que f_P. Salieron 11 perdidos (en el borde bajo) y f_FA26 algo mayor que f_P. Acerté en que la sincronía es
real y en el 14-11; me equivoqué en el 10-11, que no pierde nada.

## 3. Lo que sigue

- **Decisión de la coordinadora S28 y de Nicolás**: si S26a+G entra a la confirmación en días nuevos como cuarta
  medida informativa (después de S23b, S25a y S26a, sin tocarlas), con un criterio nuevo escrito antes, o se mide
  primero fuera de muestra con el cubo de 2024 de S25b.
- **Antuco de tarde**: los pasos de media mañana no ven la tarde. Una cámara del OVDAS o de la DGA hacia Antuco o
  Longaví la tarde del 10-11 diría si hubo cúmulos en las cumbres a la hora de los disparos.
- **Nieve y base**: la falsa alarma de una zona de cumbre parece depender de cuánta nieve tenga el año comparado con
  el de su base. Para Chillán la nieve de 2025 y 2026 es parecida, así que no lo afecta hoy, pero sí lo haría en un
  año de nieve distinta.

## 4. Lo que no puede decir

Que un disparo anulado no fuera pluma (VOLCAT es la única referencia y también ve pluma en tardes regionales); qué
signo tiene el efecto de la nieve sobre la BTD de la zona; nada del anillo de las vecinas en el óptico; nada de las
tardes (pasos a las 14:30 a 14:55 UTC); nada de días posteriores al 24-11.
