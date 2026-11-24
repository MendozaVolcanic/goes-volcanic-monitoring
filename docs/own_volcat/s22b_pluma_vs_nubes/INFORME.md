# S22b: separar la pluma de Nevados de Chillán de los bordes de nube. Informe, 24-11-2026

Criterio `criterio_2026-11-24.md` (commit `6af2d27`, 16:39 UTC) y enmienda 1 `enmienda_1_2026-11-24.md` (commit
`922ea31`), los dos empujados antes de calcular nada en los días nuevos. Código en
`C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\Goes\.claude\worktrees\agent-a717009ec169a622a\docs\own_volcat\s22b_pluma_vs_nubes\scripts\`
(`s22b_medir.py`, `s22b_bajar.py`, `s22b_volcat_clases.py`, `s22b_volcat_bajar.py`, `s22b_lado_a_lado.py`);
resultados en
`C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\Goes\.claude\worktrees\agent-a717009ec169a622a\docs\own_volcat\s22b_pluma_vs_nubes\resultados\`.
Datos nuevos y cachés (derivados, nada de SSEC al repo) en `D:\goes_notas\s22\s22b\`.

**Resultado en una línea: NO DECIDIBLE en recuerdo, porque VOLCAT no mostró pluma de Chillán del 22-11 al 24-11
16:10 UTC; en esos días nuevos el detector no disparó nunca (0 de 200 cuadros sin VOLCAT evaluados), y ya no dispara
el 15-11.** Lo hace callándose cuando hay nubes, y el precio es alto: también pierde casi todo el 14-11 y baja el
08-11 de 10 a 4 de 13 cuadros.

## 1. Para geólogo

**El fenómeno que confundía al detector.** La pluma tenue de Chillán baja la diferencia entre los canales de 11 y
12 µm en unas décimas de grado. Al lado de una nube pasan dos cosas que producen lo mismo sin ceniza: un píxel a
medio nublar queda más frío y se compara con píxeles de otra naturaleza; y cuando hay nubes sobre Chile el aire del
lado chileno es húmedo y el del lado argentino seco (foehn), y la humedad sube esa diferencia en la superficie
despejada. Resultado: la franja seca al este de la divisoria, justo donde va la pluma con viento del NO, parece
"ceniza". Eso es lo que el video de S22a mostró el 15-11.

**El hallazgo que cambia la lectura de S22a.** Con la máscara de nubes de NOAA medí qué tan nublado estaba el
anillo de 4 a 40 km alrededor del cráter. Los cuadros con pluma de VOLCAT eran casi todos **despejados** (mediana 8 % del
anillo con nube que no es nieve), y los 14 días placebo de S22a eran tardes **nubladas** (mediana 77 %; sólo 17 % de
sus cuadros de tarde tienen la mitad del anillo despejado). Del 20-10 al 19-11, las únicas tardes despejadas sin
actividad conocida son el 04-11 y pocas más. S22a comparaba, sin saberlo, cielo limpio con pluma contra cielo
nublado sin ella, y el 15-11 disparó por las nubes.

**Qué cambió en el detector.**

1. Borra las nubes que cambian (no la nieve que la máscara marca siempre a esa hora) y su borde de un píxel.
2. Se calla si más de la mitad del anillo está nublado: dice "no evaluable por nubes", que no es "sin pluma".
3. A cada píxel le resta lo que suele marcar con cielo despejado a esa hora (suelo, nieve, emisividad).
4. El umbral sale de cuadros en que VOLCAT no mostró nada, cualquier día, en vez de los días placebo nublados.

**Lo que pasa ahora en cada día.**

- **15-11 (VOLCAT limpio):** el detector no habla en ningún cuadro de la tarde: el anillo tiene de 69 a 96 % de nube dinámica de 12 a 24 UTC.
  Ya no dispara. Ojo: no es que "vea que no hay pluma"; es que se niega a mirar con nubes. La hipótesis de Nicolás
  (pluma bajo nubes ese día) no se puede juzgar con este detector.
- **08-11:** sigue disparando en la tajada SE (120° a 150°), donde VOLCAT pinta la pluma, pero menos: 3 disparos y
  4 de 13 cuadros de VOLCAT alcanzados (S22a: 23 disparos y 10 de 13). No medí qué parte de la regla le quita
  señal (umbral de tardes despejadas, línea base o ambos); queda dicho como pendiente.
- **14-11:** casi lo pierde. De 33 cuadros de VOLCAT, 15 son evaluables y ninguno se alcanza (S22a: 13 de 31). Ese
  día hay nubes dispersas (11 a 28 % del anillo desde las 19:00): al borrar sus bordes quedan 5 a 8 tajadas válidas,
  menos de las 9 que pide el cuadro; de 17:00 a 18:30, con el anillo limpio, S queda en −0,35 a −0,61 K, sin llegar
  al umbral (−0,68 a −0,75 K).
- **Días nuevos (22, 23 y 24-11 hasta 16:40 UTC), que nadie miró al elegir la regla:** VOLCAT no muestra pluma en el
  cráter en ningún cuadro (sólo 41 cuadros "otro": algo de ceniza a menos de 50 km, sin objeto anclado, el 22-11 de
  14:10 a 17:00 y de 19:00 a 21:00 y el 24-11 de 09:50 a 11:50). El 22-11 fue una tarde despejada (todos los cuadros
  pasan la compuerta) y el detector no disparó ni una vez; el 23-11 de tarde ningún cuadro se pudo evaluar por nubes (no habla); el 24-11 no
  disparó. 0 disparos en 389 cuadros.

**Lectura honesta.** El detector ya no confunde el borde de nube con pluma, y en tres días nuevos no dio una sola
falsa alarma. Pero no sabemos si todavía ve la pluma: los días nuevos no tuvieron pluma de VOLCAT, y en desarrollo
el recuerdo bajó (13 de 54 cuadros evaluables, contra 7 % de alcance al azar en cuadros sin VOLCAT). El poder para
una firma lejana de 0,33 K es 0,045: con esa firma, el detector casi nunca la vería. Lo que sí vería es una firma de
0,97 K como la de junto al cráter (poder 0,735).

## 2. Veredicto por la regla

| Paso | Resultado | Fuente |
|---|---|---|
| Instrumento días nuevos | 389 de 389 cuadros (22-11 00:00 a 24-11 16:40 UTC), mismo scan en C14 y C15, sin congelados, BT11 en rango, Planck igual al desarrollo | `resultados/instrumento_nuevo.json` |
| Clase VOLCAT nueva | regla P/N/otro reimplementada; 555 de 555 cuadros iguales a `frames_calor.csv` en 28-10, 10, 11 y 14-11 | `scripts/s22b_volcat_clases.py validar` |
| Ensayo en seco con el criterio literal | 0,058 (INVÁLIDA); sin umbral de 13:50 a 21:00 UTC | `resultados/corrida_criterio_literal/` |
| Ensayo en seco con la enmienda 1 | **Aprobado**: 0,032 por cuadro (media por día), 0,036 en el pozo; todas las horas con umbral. Un día alto: 05-11, 19 de 60 (0,32) | `resultados/seco.json` |
| Poder (8 píxeles en un rayo a 4 a 20 km, dos cuadros) | 0,045 a 0,33 K; 0,735 a 0,97 K (738 pares de 16 días) | `resultados/poder.json` |
| Falsa alarma en días nuevos | **0 de 200** cuadros N evaluados (22-11: 0/96; 23-11: 0/43; 24-11: 0/61) | `resultados/confirmacion_fa.json` |
| Recuerdo en días nuevos | 0 cuadros P (VOLCAT no mostró pluma en el cráter) | `resultados/s22b_resultado.json` |
| Veredicto | **NO DECIDIBLE (recuerdo)** | idem |

## 3. Desarrollo con la regla fija (días ya mirados; informa, no decide)

| Día | Cuadros P | Evaluables | Alcanzados | No evaluables por nubes | Disparos del día (tajada) |
|---|---|---|---|---|---|
| 22-10, 24-10, 25-10 | 1, 1, 4 | 0 | 0 | 1, 0, 0 | 0 |
| 28-10 | 26 | 17 | 4 | 0 | 2 (60° a 90°) |
| 29-10 | 6 | 3 | 3 | 0 | 4 (SE y SSE) |
| 07-11 | 1 | 1 | 0 | 0 | 0 |
| **08-11** | 13 | 13 | **4** | 0 | 3 (SE) |
| 10-11 | 12 | 2 | 0 | 4 | 0 |
| 11-11 | 3 | 3 | 2 | 0 | 5 (SE y S) |
| **14-11** | 33 | 15 | **0** | 2 | 1 (90° a 120°) |
| Total | 100 | 54 | 13 (0,24) | | |

Cuadros N evaluados alcanzados por azar: 56 de 797 (0,07); Fisher unilateral p = 0,0002 (orientativo, los cuadros
seguidos no son independientes). Episodios: 4 de 13. Los cuadros que no se evalúan no son sólo por la compuerta:
también por borrar bordes de nube, que deja tajadas con menos de la mitad de sus píxeles.

## 4. Controles pedidos

- **De qué días sale el nulo.** S22a: 14 días placebo, 13 nublados de tarde. S22b: cuadros N de 31 días con clase de
  VOLCAT; los que se evalúan vienen sobre todo de días despejados con actividad (07-11: 94, 08-11: 77, 28-10: 68,
  29-10: 66) y de 25-10, 04-11, 05-11, 09-11 (55 a 61 cada uno). De tarde el pozo es chico: a las 18:00 y 20:00 UTC
  el umbral necesita ±180 min (81 y 60 cuadros, 7 y 9 días). Detalle por hora en `seco.json`
  (`composicion_nulo_por_hora`, `U_info`).
- **Línea base por píxel sólo con cuadros despejados por E1:** así se armó (§2.4 del criterio).
- **Sesgo de la tajada SE:** **no se fue.** En los cuadros N evaluados la tajada SE sigue siendo la más baja en 18 %
  (esperado 8 %); en los días nuevos, 18 % el 22-11, 30 % el 23-11 y 7 % el 24-11. Separar las nubes no lo explica
  todo. Queda abierto si es superficie que la base no captura (hay pocas tardes despejadas para armarla) o gas y
  ceniza fina permanentes a sotavento: Chillán desgasifica casi a diario y el viento dominante lleva al SE.
- **Nacimientos de VOLCAT:** no se usaron para nada.
- **Ensayo en seco antes de positivos y poder por inyección:** hechos en desarrollo; en los días nuevos se escribió
  la falsa alarma antes del recuerdo (`confirmacion_fa.json`).

## 5. Videos lado a lado (visualización, fuera del repo por la licencia de SSEC)

En `C:\Users\nmend\Downloads\`: `s22b_lado_a_lado_volcat_vs_detector_chillan_2026-11-08_10min.mp4`, `..._2026-11-14_10min.mp4`,
`..._2026-11-15_10min.mp4`, `..._2026-11-22_10min.mp4`, `..._2026-11-23_10min.mp4`, `..._2026-11-24_10min.mp4`
(12:00 a 23:50 UTC; el 24-11 de 12:00 a 16:40). En celeste translúcido, la nube y el borde que el detector no usa;
en rojo, los 8 píxeles de la tajada cuando dispara; en el texto, "no evaluable por nubes" cuando se calla.

### Post hoc (mirado después del veredicto, no decide)

- **22-11, 15:10 a 15:50 UTC: VOLCAT dibuja una bocanada chica que se aleja del cráter hacia el ESE** (1 a 5
  píxeles, a 18, 22 a 27 y 34 a 36 km, acimut 112° a 119°), sin objeto anclado, por eso es clase "otro" y no entra
  al recuerdo. Cielo limpio (2 a 5 % de nube dinámica). El detector mira hacia allá: su tajada mínima es la de 90° a
  120° o la de 120° a 150° en esos cuadros, pero S (−0,29 a −0,49 K) no llega al umbral (−0,58 a −0,68 K). Es el
  mismo cuadro que el 14-11: apunta bien y le falta señal. Además hay 1 píxel a 10 km y 141° a las 20:00.
- **24-11, 12:00 a 14:20 UTC:** VOLCAT dibuja ceniza a 80 a 144 km al E y NE, fuera del anillo del detector (40 km);
  no es de Chillán en el cráter.

## 6. Lo que puede estar mal

- **La regla se eligió mirando el desarrollo**, y hubo una enmienda después de ver el ensayo en seco (declarada: el
  criterio decía "nublado de costumbre a cualquier hora" y el dato del desarrollo era de tarde; de día la máscara de
  NOAA confunde la nieve con nube). Todo lo de §3 es desarrollo.
- **La confirmación sólo probó falsa alarma.** Tres días sin pluma de VOLCAT no dicen si el detector la ve.
- **El nulo usa cuadros N de días con actividad.** Si Chillán emitía algo que VOLCAT no vio, el umbral sube y la falsa
  alarma también (en contra del detector). El 05-11 dispara 19 de 60 cuadros sin VOLCAT: no se revisó qué hay.
- **La compuerta es un cuchillo de dos filos:** callarse con nubes evita el 15-11, pero también deja sin evaluar 46
  de 100 cuadros de VOLCAT en desarrollo, y la pluma de verdad puede ir sobre nubes.
- **Poder bajo** a 0,33 K: el detector no llega a la firma lejana de H29.
- **La máscara de nubes de NOAA** es otro producto que puede fallar (nieve, cumbres); se usa sólo para callar al
  detector y para borrar bordes, no para decidir que hay pluma.

## 7. Qué deja esto

1. Lección de método para todo lo que siga: **comparar con días del mismo cielo.** Un nulo de días nublados no sirve
   para juzgar tardes despejadas; S22a lo hizo sin saberlo.
2. El detector propio, con esta regla, no da falsas alarmas en tres días nuevos, pero ve menos de la pluma conocida.
   Para saber si sirve hace falta un día nuevo **con** pluma de VOLCAT en tarde despejada: la próxima vez que VOLCAT
   muestre Chillán, guardar sus PNG (SSEC guarda unos 30 días) y correr `s22b_medir.py confirmar` sin cambiar nada.
3. El sesgo de la tajada SE sigue abierto y merece prueba propia: ¿superficie o desgasificación permanente a
   sotavento?

### Verdad de cámaras del OVDAS para el 05-11 (Nicolás, 24-11, después de los veredictos)

Nicolás revisó las cámaras del OVDAS: el 05-11 el viento iba hacia Argentina y **la pluma se desplazó todo el día
hacia el E**. Consecuencias, todas post hoc:

- El 05-11 **no era un día sin actividad**: estaba entre los placebo de S21e, S22a y S22b. VOLCAT no lo marcó.
- Los disparos de S22b ese día (20 cuadros, de noche, hacia el SE, el NO y el O) **son errores**: ninguno apunta al E.
- Con la regla de S22a, de día y casi todo nublado por E1, las tajadas del E (60° a 120°) quedan entre las 3 más
  bajas en 8 de 10 horas con dato, pero débiles (−0,1 a −0,26 K bajo la mediana; −0,56 K a las 20:00 UTC): una
  señal que ningún umbral alcanzó.
- El 04-11, el día "tranquilo" de referencia, las tajadas del E son también las más bajas en casi todas las horas
  despejadas (−0,2 a −0,6 K). O el E tiene un sesgo propio, o el 04-11 también tuvo pluma hacia el E. Sin cámaras
  no se distingue. **La suposición de que los días placebo no tenían pluma queda en duda para todo noviembre.**
