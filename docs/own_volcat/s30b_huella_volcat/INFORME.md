**Veredicto: MISMO RUMBO, NO SEPARABLE para el anillo (coincide en 12 de 23 cuadros P, 52 %, contra 19 % con la huella girada y 45 % con la huella de otro día); la zona y la unión quedan NO DECIDIBLE (la unión coincide en 51 de 64, 80 %, contra 70 % girada y 64 % de otro día), porque casi toda huella de VOLCAT (86 de 94) toca los píxeles del cráter.**

# S30b: ¿el detector S26a marca donde VOLCAT dibuja la pluma, o sólo a la misma hora? Informe, 26-11-2026

Criterio `criterio_2026-11-26.md` (commit `eef0b0f`), empujado antes de cruzar un solo disparo con una huella. Código
`scripts/s30b_medir.py`; post hoc (no decide) `scripts/s30b_posthoc.py` y `scripts/s30b_posthoc2.py`. Cifras en
`resultados/` (`s30b_resultado.json`, `s30b_por_cuadro.csv`, `s30b_posthoc*.json`). Figuras con la huella de VOLCAT
(material de SSEC, fuera del repo) en `D:\goes_notas\s30\s30b\`. Ningún día posterior al 24-11 y ninguna corrida de
`s23b_confirmar.py`.

## 1. Para geólogo

**La pregunta.** El detector propio S26a (zona de 0 a 4 km del cráter O anillo de 4 a 40 km) "llega" a 63 de los 93
cuadros en que VOLCAT dibujó pluma en Chillán entre el 21-09 y el 24-11. Pero llegar sólo pide disparar a la misma
hora, más o menos un cuadro. Aquí se pregunta si dispara **en el mismo lugar**: en la tajada de 30° por donde VOLCAT
dibuja la pluma (anillo), o en el cráter cuando VOLCAT la dibuja pegada al cráter (zona). Es la diferencia entre "vemos
la pluma" y "vemos que es un día con pluma".

**Lo que hace la pluma de Chillán en estos dos meses.** Las huellas de VOLCAT son chicas (mediana de 8 píxeles
de 2 km, de 1 a 23), están ancladas al cráter (así se definió un cuadro P: objeto a 10 km o menos) y 86 de 94
tocan alguno de los 11 píxeles de la zona. Cuando se alargan, dos de cada tres van entre el E y el S (60 de 90 con
rumbo de 90° a 180°; 44 en la tajada de 120° a 150°), y la mediana de cada día con varios cuadros queda entre 97° y
130°. El viento de primavera las lleva para allá casi todos los días.

**Lo que hace el detector.** El anillo, cuando dispara, marca casi siempre la misma tajada: la de 120° a 150° (SE),
y algunas veces la vecina de 150° a 180°. En 2026 lo hizo así en cuadros con VOLCAT y sin VOLCAT: de 52 disparos del
anillo, 50 cayeron entre 120° y 210°. Y ya lo hacía en 2025, el año sin pluma: en el ensayo en seco, 89 de sus 138
disparos (64 %) cayeron en esas tres tajadas, que son la cuarta parte del círculo. El anillo tiene un lado preferido
por sí mismo (terreno, nubes de sotavento o la forma de su fondo), y ese lado es justo hacia donde va la pluma.

**Lo que salió.**

- **El anillo apunta hacia donde VOLCAT dibuja la pluma.** En 12 de 23 cuadros P en que disparó, la tajada marcada
  contiene huella de VOLCAT. Si se gira la huella de cada día un ángulo al azar alrededor del cráter, coincidiría en
  el 19 % (p = 0,004). El detector no marca un lado cualquiera: marca el lado de la pluma.
- **Pero no más que el lado donde va la pluma cualquier otro día.** Si a cada día se le pone la huella de otro día con
  pluma, coincidiría en el 45 % (p = 0,41). El detector apunta al rumbo habitual de la pluma de Chillán, que es también
  el rumbo de la pluma de cada cuadro, así que con estas plumas no se puede decir si sigue a ésta o al rumbo de
  siempre. Y el control positivo (un "detector" que marca donde VOLCAT dibujó la pluma un cuadro antes) apenas pasa
  ese mismo nulo (p = 0,012 con la semilla escrita; entre 0,009 y 0,014 con otras 20): las plumas de VOLCAT se
  parecen tanto entre días que ni la propia pluma de VOLCAT se distingue bien de la de otro día. De ahí "no separable".
- **Mismo rumbo, distinta distancia.** En los cuadros que coinciden, los píxeles que marca el anillo están a 26 a 32
  km del cráter; la huella anclada de VOLCAT llega a 9 a 15 km. El detector ve el SE lejano y VOLCAT dibuja el tramo
  cercano. Sólo el 08-11, contando también los pedazos de pluma que VOLCAT dibuja desprendidos (post hoc), los dos
  coinciden píxel a píxel a 25 a 40 km.
- **La zona del cráter no se puede juzgar así.** Casi toda huella anclada de VOLCAT toca alguno de los 11 píxeles de
  la zona (41 de 43 cuadros con disparo de la zona; con la huella de otro día, 73 %). Que la zona coincida no
  distingue nada, y ni el control positivo separa (p = 0,10). Esto calza con lo que vio la auditoría S28b: la zona
  mide "día encendido".
- **La unión** coincide en 51 de 64 cuadros (80 %), pero casi todo eso es la zona, que coincide por construcción.
  Girar la huella no mueve a la zona, así que la unión no tiene con qué decidir: NO DECIDIBLE.
- **De noche** sólo hay 3 cuadros P evaluables, de un solo día (29-10): NO DECIDIBLE por construcción.

**Lectura honesta.** Lo que se puede afirmar: cuando el anillo dispara a la hora de una pluma de VOLCAT, lo hace hacia
el lado de la pluma y no a un lado cualquiera. Lo que no se puede afirmar: que vea **esa** pluma y no el lado al que
siempre va la pluma de Chillán (o un rasgo fijo del SE que se enciende con ella), porque el anillo dispara al SE casi
siempre, ya lo hacía en 2025 sin pluma, y las plumas de VOLCAT van al SE casi siempre. Para separar las dos cosas hacen falta días en que la pluma de
VOLCAT vaya hacia otro lado (viento del sur o del este), o mirar la distancia y no sólo el rumbo, que es lo que el
anillo de tajadas no hace.

## 2. Cifras por el criterio (semilla 0, B = 9.999)

| Medida | P evaluados | Coinciden | Girada (nulo R) | Otro día (nulo D) | Oráculo R / D | Veredicto |
|---|---|---|---|---|---|---|
| Unión (titular) | 64 (6 días) | 51 (0,80) | 0,695; p 0,0066 | 0,638; p 0,18 | 0,12 / 0,14 | **NO DECIDIBLE** (oráculo falla R) |
| Anillo | 23 (4 días) | 12 (0,52) | 0,186; p 0,0037 (exacto, 20.736) | 0,454; p 0,41 | 0,0001 / 0,0118 | **MISMO RUMBO, NO SEPARABLE** |
| Zona | 43 (4 días) | 41 (0,95) | no se aplica | 0,728; p 0,15 | no / 0,10 | **NO DECIDIBLE** (oráculo falla D) |
| Día, unión / anillo / zona | 61 / 20 / 42 | 49 / 10 / 40 | p 0,0077 / 0,0087 / no | p 0,19 / 0,46 / 0,15 | | NO DECIDIBLE / MISMO RUMBO, NO SEPARABLE / NO DECIDIBLE |
| Noche, unión / anillo / zona | 3 / 3 / 1 (un día) | 2 / 2 / 1 | | | | NO DECIDIBLE (pocos cuadros y días) |

Secundarias (informativas):

| Medida | Coinciden | Girada | Otro día |
|---|---|---|---|
| Anillo, píxeles (huella dilatada 1 px) | 7 de 23 (0,30) | 0,047; p 0,0013 | 0,247; p 0,40 |
| Anillo, rumbo ±30° | 12 de 23 (0,52) | 0,155; p 0,0064 | 0,320; p 0,13 |
| Zona, píxeles | 42 de 43 | 0,955; p 0,50 | 0,749; p 0,083 |
| Unión, píxeles | 47 de 64 (0,73) | 0,654; p 0,0027 | 0,581; p 0,15 |

Por día (P con huella; evaluados y coincidentes por parte):

| Día | P con huella | Anillo | Zona | Unión |
|---|---|---|---|---|
| 28-10 | 26 | 5 de 8 | 13 de 13 | 17 de 20 |
| 29-10 | 6 | 2 de 3 | 1 de 1 | 2 de 3 |
| 08-11 | 13 | 5 de 9 | | 5 de 9 |
| 10-11 | 12 | | 8 de 9 | 8 de 9 |
| 11-11 | 3 | 0 de 3 | | 0 de 3 |
| 14-11 | 33 | | 19 de 20 | 19 de 20 |
| 07-11 | 1 | | | |

94 de los 100 P tienen PNG; 6 no. Comprobación de código: la tabla de S26a reproduce 63 de 93 (unión), 23 de 54
(anillo) y 42 de 93 (zona).

**Control negativo (cuadros N de los mismos días):** anillo, 0 de 2 coinciden (los dos el 11-11; muy pocos para leer);
zona, 43 de 43 (cualquier disparo de la zona "coincide" con una huella que siempre toca el cráter: rumbo del día);
unión, 109 de 111. El control negativo de la zona y la unión confirma que su coincidencia no dice nada del cuadro.

**Expectativa escrita antes (criterio §7) contra lo que salió:** acerté en el anillo (MISMO RUMBO, NO SEPARABLE) y en
la zona (NO DECIDIBLE), y en la unión dije "MISMO RUMBO, NO SEPARABLE o NO DECIDIBLE": salió NO DECIDIBLE. No esperaba
que el control positivo quedara pegado al umbral del nulo D.

## 3. Post hoc (no decide)

- **Semillas.** El p_D del anillo es estable (0,41 a 0,43 en las semillas 1 a 20). El del oráculo cae entre 0,0094 y
  0,0140: con 4 de 20 semillas pasaría 0,01, y el rótulo del anillo sería MISMO RUMBO HABITUAL en vez de NO SEPARABLE.
  Las dos lecturas dicen lo mismo de lo que importa: el detector no apunta a la pluma de este día más que a la de otro.
- **Huella con toda la ceniza a 40 km** (también la desprendida, que el criterio dejó fuera por no estar anclada): el
  anillo coincide en 16 de 23 (girada 0,001; otro día p 0,33) y el oráculo pasa los dos nulos: MISMO RUMBO HABITUAL.
  Por píxeles, 15 de 23 (girada p 0,0005; otro día p 0,17). Unión y zona, igual que por el criterio.
- **Distancia.** En los 12 cuadros que coinciden por el criterio, la mediana de los píxeles disparados está a 26 a 32
  km del cráter y la huella anclada llega a 9 a 15 km. Con toda la ceniza, el 08-11 VOLCAT dibuja pedazos a 23 a 39 km
  y el anillo marca a 25 a 28 km: es el único día en que los dos ven el mismo tramo.
- **Tajadas del anillo en 2025 (año sin pluma, ensayo en seco a 4,75, cada día sin sí mismo):** 138 disparos; 41 en
  120° a 150°, 13 en 150° a 180°, 35 en 180° a 210° (89, 64 %), 16 en 210° a 240°, 19 entre 0° y 60°, el resto
  disperso. En 2026, 50 de 52 en 120° a 210° (96 %). El lado SE ya era el preferido sin pluma; con pluma lo es casi
  siempre.

## 4. Lo que sigue

- **Días con la pluma hacia otro lado.** Es lo único que separa "esta pluma" de "el rumbo de siempre". Cuando la
  confirmación en días nuevos se mida (después de la enmienda de S30a), contar cuántos P tienen huella fuera de 90° a
  180°: si hay, repetir esta prueba con el criterio congelado.
- **Medir distancia, no sólo rumbo.** El anillo de tajadas junta 4 a 40 km; partirlo en dos coronas (4 a 15 y 15 a
  40 km) diría si el detector ve el tramo que dibuja VOLCAT. Es una regla nueva: criterio antes.
- **La zona no se puede validar contra VOLCAT** por posición: hace falta verdad independiente (cámaras del OVDAS).

## 5. Lo que no puede decir

Que lo marcado sea ceniza; la altura; nada de días posteriores al 24-11. Es desarrollo: los P ya se habían mirado con
el detector (aunque nunca su posición). VOLCAT no es verdad de terreno: dibuja sólo lo que su algoritmo sigue, y la
georreferencia de su PNG tiene 1 píxel de incertidumbre (H14). Que el anillo coincida en rumbo no prueba que vea la
pluma; que no coincida en distancia no prueba que no la vea (VOLCAT puede no dibujar el tramo lejano).
