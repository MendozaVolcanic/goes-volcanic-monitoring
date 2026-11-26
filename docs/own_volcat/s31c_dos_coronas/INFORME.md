**Veredicto: SÓLO LEJOS. Cuando el anillo del detector S26a dispara a la hora de una pluma de VOLCAT, marca hacia el lado de la pluma pero a 22 a 33 km del cráter, y en el tramo de 4 a 15 km donde VOLCAT dibuja la pluma anclada cae menos que un píxel cualquiera de la misma tajada (6 de 23 cuadros contra 38 % esperado al azar; p_G 0,94). El control positivo sí lo distingue (VOLCAT un cuadro antes: 47 % contra 16 %, p_G 0,0001). El detector no ve el tramo que ve VOLCAT; ve algo más lejos al SE a la misma hora. Es desarrollo sobre días ya vistos.**

# S31c: el anillo en dos coronas. ¿El detector marca el tramo cercano que dibuja VOLCAT, o sólo lejos? Informe, 26-11-2026

Criterio `criterio_2026-11-26.md`, commit `d3c9461` (empujado a las 15:13 UTC del 26-11, antes de calcular un disparo
por corona) y anexo §8 en `eab5486` (también antes de medir: la primera corrida se paró en la comprobación de código,
ver §4). Código `scripts/s31c_medir.py` (con prueba sintética `pruebas`). Cifras en `resultados/s31c_resultado.json` y
`resultados/s31c_por_cuadro.csv`. Huellas en la grilla ABI (derivadas de PNG de SSEC) y registro de las dos corridas en
`D:\goes_notas\s31\s31c\`, fuera del repo. Sólo días hasta el 24-11; nada de `s23b_confirmar.py`, `s30a_confirmar.py` ni
del CSV de días nuevos. Medida una vez.

## 1. Para geólogo

**La pregunta.** S30b mostró que el anillo del detector (4 a 40 km del cráter, tajadas de 30°) dispara hacia el lado
donde VOLCAT dibuja la pluma de Chillán, y vio de paso que lo hace lejos: sus píxeles a 26 a 32 km, la huella de VOLCAT
anclada al cráter hasta 9 a 15 km. Si el detector ve la misma columna que VOLCAT, debería marcar también donde VOLCAT
la dibuja, junto al cráter. Aquí se partió el anillo en dos coronas, 4 a 15 km y 15 a 40 km, sin tocar el detector:
sólo se miró a qué distancia caen los 8 píxeles que forman su estadístico (la "cola baja" de la tajada que dispara).

**Por qué hacía falta un nulo nuevo.** La corona cercana es chica (8 a 10 de los ~70 píxeles de cada tajada), pero un
puñado de píxeles puestos al azar en la tajada cae a menudo en ella, y la huella anclada de VOLCAT, dilatada un píxel
por la incertidumbre de georreferencia, cubre buena parte de esa corona en su tajada. Girar la huella alrededor del
cráter (el nulo de S30b) sólo vuelve a preguntar por el rumbo. Por eso se agregó un nulo que conserva el rumbo y
desordena la distancia: cada día, cada píxel del disparo se cambia por otro de su misma tajada (el mismo cambio para
todos los cuadros del día). Pregunta si el detector marca el tramo de VOLCAT más que un píxel cualquiera del mismo lado.

**Lo que salió.**

- **El detector marca el lado de la pluma, pero lejos.** En 12 de 23 cuadros P tiene píxeles en la corona de 15 a 40 km
  con la tajada a ±30° del rumbo de la pluma de VOLCAT; con la huella girada, el 16 % (p 0,007, exacto). La mediana de
  sus píxeles está a 28 km (22 a 33 km según el cuadro); la huella anclada llega, en mediana, a 10 km.
- **En el tramo donde VOLCAT dibuja, cae menos que al azar.** En 6 de 23 cuadros algún píxel del detector cae a 4 a
  15 km dentro de la huella (26 %). Un píxel cualquiera de la misma tajada lo haría en el 38 % (p_G 0,94): el detector
  aparta sus píxeles del tramo cercano justamente cuando hay pluma. Contra la huella girada esos 6 sí son más de lo
  esperado (3 %, p 0,001), pero eso es otra vez el rumbo.
- **La prueba tenía con qué ver el tramo.** El control positivo, un "detector" que marca donde VOLCAT dibujó la pluma un
  cuadro antes, cae en el tramo cercano en 41 de 87 cuadros contra 16 % al azar en la tajada (p_G 0,0001). Si el
  detector siguiera la columna que VOLCAT sigue, este nulo lo habría mostrado.
- **Lo mismo se ve sin pruebas.** De los píxeles del detector en los cuadros P, el 7,8 % cae a menos de 15 km, cuando la
  geometría da 12,8 %; en sus disparos de 2026 sin clase de VOLCAT, el 17 %, y en los N, el 12,5 %. Con pluma de VOLCAT,
  el detector mira más lejos.
- **Ni de día ni con toda la ceniza cambia.** De día (20 P, 3 días) el resultado es el mismo. Con la huella de toda la
  ceniza a 40 km, incluidos los pedazos desprendidos que VOLCAT dibuja lejos (el 08-11 a 23 a 39 km), el detector cae
  en esa ceniza lejana en 10 de 23 cuadros, pero un píxel cualquiera de la tajada lo haría en el 45 %: tampoco más que
  al azar. Ahí, sin embargo, el control positivo también falla (p_G 0,93): la ceniza desprendida cubre tanto de la
  tajada que el nulo no distingue nada, así que **no se puede decir** si el detector ve esos pedazos lejanos.
- **De noche**: 3 cuadros de un día, NO DECIDIBLE por construcción.

**Lectura.** El detector y VOLCAT disparan a la misma hora y hacia el mismo lado, pero no en el mismo tramo: VOLCAT
dibuja la columna pegada al cráter y el detector marca 15 a 20 km más allá. Lo que el detector ve al SE lejano puede
ser la pluma ya diluida (una hipótesis física razonable y sin medir: junto al cráter la pluma es densa y opaca, y la
firma de ceniza en 11 menos 12 µm sólo aparece cuando la nube se vuelve semitransparente; los nacimientos de Chillán
ya tenían BTD de cero o más, S21) o algo que no es la pluma: S30b mostró que el anillo prefería el SE en 2025, sin
pluma. Esta prueba no separa esas dos. Lo que sí deja claro es que el detector no reproduce el tramo que VOLCAT dibuja,
y que su coincidencia con VOLCAT es de hora y de rumbo, no de posición.

## 2. Cifras por el criterio (huella anclada, titular; semilla 0, B = 9.999; R exacto con 20.736 combinaciones)

| Medida | Coinciden (de 23 P, 4 días) | Al azar en la tajada (G) | Huella girada (R) | Huella de otro día (D) |
|---|---|---|---|---|
| Píxel en el tramo cercano (4 a 15 km) | 6 (0,26) | 0,38; p 0,94 | 0,03; p 0,0012 | 0,16; p 0,22 |
| Píxel en el tramo lejano (15 a 40 km) | 2 (0,09) | 0,05; p 0,26 | 0,01; p 0,083 | 0,07; p 0,44 |
| Rumbo en la corona cercana | 9 (0,39) | no aplica | 0,12; p 0,010 | 0,22; p 0,12 |
| **Rumbo en la corona lejana** | **12 (0,52)** | no aplica | **0,16; p 0,0068** | 0,32; p 0,14 |

Control positivo (oráculo de S30b, 87 P en 6 días): píxel en el tramo cercano 41 (0,47), G 0,16 p 0,0001, R 0,15 p
0,0007, D 0,25 p 0,017; oráculo de tajada de S30b p_R 0,0001. Veredicto por §5: el oráculo pasa G (hay poder), el
detector no pasa G en la corona cercana (p 0,94) y sí pasa R en el rumbo lejano (p 0,0068) con el oráculo de tajada
pasando R: **SÓLO LEJOS**.

| Periodo | P (días) | Píxel cercano: T, p_G, p_R | Rumbo lejano: T, p_R | Oráculo cercano p_G | Veredicto |
|---|---|---|---|---|---|
| Todo | 23 (4) | 6, 0,94, 0,0012 | 12, 0,0068 | 0,0001 | **SÓLO LEJOS** |
| Día | 20 (3) | 5, 0,97, 0,0069 | 11, 0,0093 | 0,0001 | SÓLO LEJOS |
| Noche | 3 (1) | 1, 0,60, 0,17 | 1, 0,25 | 1,0 | NO DECIDIBLE (pocos) |

Huella de toda la ceniza a 40 km (secundaria, no decide):

| Medida | Coinciden (de 23) | G | R | D | Oráculo G |
|---|---|---|---|---|---|
| Píxel cercano | 10 (0,43) | 0,49; p 0,79 | 0,05; p 0,0006 | 0,22; p 0,065 | p 0,0001 |
| Píxel lejano | 10 (0,43) | 0,45; p 0,82 | 0,04; p 0,0069 | 0,24; p 0,12 | p 0,93 (sin poder) |
| Rumbo cercano | 14 (0,61) | | 0,12; p 0,0023 | 0,27; p 0,0053 | |
| Rumbo lejano | 17 (0,74) | | 0,16; p 0,0019 | 0,41; p 0,037 | |

El esquema de §5 aplicado a esta huella también da SÓLO LEJOS, y "marca lejos donde VOLCAT dibuja ceniza desprendida"
no se cumple (p_G 0,82), pero con el oráculo sin poder en esa medida no se lee como un no. El rumbo cercano pasa D (p
0,0053) en esta secundaria: es una de unas veinte pruebas secundarias (seis medidas con dos o tres nulos cada una), sin corrección por comparaciones múltiples, y no decide.

Por día (huella anclada; P evaluados, cuadros con píxel en el tramo cercano, con rumbo lejano; píxeles del detector a
menos de 15 km sobre el total):

| Día | P | Píxel cercano | Rumbo lejano | Píxeles a < 15 km |
|---|---|---|---|---|
| 28-10 | 8 | 3 | 6 | 5 de 83 |
| 29-10 | 3 | 1 | 1 | 9 de 24 |
| 08-11 | 9 | 2 | 5 | 13 de 152 |
| 11-11 | 3 | 0 | 0 | 0 de 24 |

Descriptivo (sin nulo): píxeles del detector a menos de 15 km, geometría 12,8 %; en la unión de los P evaluados 27 de
283 (9,5 %); por cuadro de disparo en 2026 hasta el 24-11, P 10 de 128 (7,8 %), N 7 de 56 (12,5 %), sin clase 40 de
232 (17,2 %). Mediana de la distancia de los píxeles del detector por cuadro P: 27,9 km (21,9 a 32,6); distancia máxima
de la huella anclada en el anillo: mediana 9,7 km.

**Comprobaciones de código:** la tabla de S26a reproduce 63 de 93 (unión), 23 de 54 (anillo) y 42 de 93 (zona); las
funciones de S30b sobre los mismos P dan 12, 7 y 12 de 23 y p_R exacto 0,0041 (ver §4); todos los píxeles de `cola_a`
están en el anillo y en su tajada; prueba sintética (`s31c_medir.py pruebas`) en verde: G conserva tajada y rumbo, es
inyectiva y deja en la corona cercana el 15 % de una cola que estaba entera ahí.

**Expectativa escrita antes (criterio §7) contra lo que salió:** acerté en el titular (SÓLO LEJOS), en que `px_cerca`
quedaría cerca de los 7 de S30b (salió 6) sin superar al azar dentro de la tajada, y en que el oráculo pasaría G. No
esperaba que el detector cayera en el tramo cercano **menos** que al azar (0,26 contra 0,38), ni que con toda la ceniza
el oráculo perdiera el poder en la corona lejana. Esperaba `px_lejos` con toda la ceniza sólo el 08-11: coincidió 8
veces ese día y 2 el 28-10.

## 3. Post hoc

Nada. No se corrió ninguna variante después de ver el resultado.

## 4. Lo que pasó con la primera corrida

La primera corrida (`D:\goes_notas\s31\s31c\medir_corrida1_parada.log`) se detuvo en la comprobación de código, antes
de cualquier cifra por corona: el p_R de S30b por tajada salió 0,0041 y no 0,0037. La causa es de S30b: con 20.736
combinaciones su regla (exacto sólo hasta 20.000) lo mandó a Monte Carlo, aunque su informe dice "exacto". El exacto es
0,0041; el 0,0037 cabe en el error de Monte Carlo. El criterio heredó el rótulo y se contradecía; el anexo §8 lo dejó
exacto hasta 12^4 antes de medir. No cambia ningún rótulo de S30b (0,0041 sigue bajo 0,01).

## 5. Lo que sigue

- **¿Qué es lo que el detector ve lejos?** Es la pregunta que queda. Dos caminos con datos que ya existen: (a) las
  cámaras del OVDAS, en los días 28-10 y 08-11, para ver si la pluma llega a 25 a 30 km al SE a esa hora; (b) la verdad
  de alta resolución (Sentinel-2, Landsat, S20b) en algún paso con disparo lejano. Criterio antes, como siempre.
- **Para la confirmación en días nuevos** (retenida con el gatillo v2): esta prueba no la toca. Pero si la unión
  confirma, este resultado dice cómo leerla: el anillo llega a la hora y al lado de la pluma, no al tramo que VOLCAT
  dibuja.

## 6. Lo que no puede decir

Que lo marcado lejos sea ceniza o no lo sea; la altura; nada de días posteriores al 24-11. Es desarrollo: los 23 P ya
los habían mirado S26a y S30b. VOLCAT no es verdad de terreno: dibuja el tramo que su algoritmo sigue, y puede no
dibujar la pluma diluida lejos. El nulo G supone que cualquier píxel de la tajada podría estar en la cola; si el terreno
o el pareo por cota apartan por sí mismos la corona cercana de la cola, G lo atribuye al detector, pero en los disparos
sin clase la corona cercana no está apartada (17 % contra 12,8 % de la geometría), así que no parece ser eso.
