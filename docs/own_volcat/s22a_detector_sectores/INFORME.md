# S22a: detector propio por sectores con persistencia, frente a lo que VOLCAT mostró de Nevados de Chillán. Informe, 24-11-2026

Criterio `criterio_2026-11-24.md` (commit `7c59431`, 11:33 UTC), código y pruebas (10 de 10) en el commit siguiente,
ensayo en seco y poder empujados antes de calcular nada en un día con actividad. Código en
`C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\Goes\.claude\worktrees\s22-5a2702\docs\own_volcat\s22a_detector_sectores\scripts\s22a_medir.py`;
salidas en
`C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\Goes\.claude\worktrees\s22-5a2702\docs\own_volcat\s22a_detector_sectores\resultados\`
(`seco.json`, `poder.json`, `s22a_resultado.json`, logs); figura del 08-11 en
`C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\Goes\.claude\worktrees\s22-5a2702\docs\own_volcat\s22a_detector_sectores\figuras\serie_0811.png`.
Caché de M1 (derivado de los cubos, no es dato de SSEC) en `D:\goes_notas\s22\s22a\`.

**Resultado en una línea: SIN PODER por la regla**, con una señal clara el 08-11 que no se puede atribuir todavía a
la pluma. El detector alcanza 36 de 96 cuadros en que VOLCAT mostró pluma en el cráter (R 0,375) y 5 de 13 episodios;
el azar (las mismas horas en días placebo) da 0 en 10 de 14 días, pero el 15-11 da 0,39, así que p = 2/15. El 08-11
alcanza 10 de 13 cuadros, más que los 14 días placebo. El problema: el 15-11, día sin VOLCAT, el detector dispara toda
la tarde **en el mismo sector (SE) y a las mismas horas**.

## 1. Para geólogo

**La idea.** VOLCAT sostiene sus plumas de Chillán siguiendo un objeto de cuadro en cuadro, no por una firma fuerte en
cada imagen. Copiamos esa lógica con nuestra física: alrededor del cráter, en 12 tajadas de 30° entre 4 y 40 km, se
busca la tajada cuyos 8 píxeles más "ceniza" (diferencia 11 − 12 µm más baja que la de píxeles de igual temperatura y
cota del mismo cuadro) se separan de las otras tajadas, y se exige que pase dos cuadros seguidos en la misma tajada o
en una vecina. No necesita tardes despejadas, porque compara cada tajada con las otras de la misma imagen.

**Lo que salió.**

- **El 08-11 el detector ve algo, y lo ve antes que VOLCAT.** Dispara casi sin pausa de 16:30 a 20:50 UTC (13:30 a
  17:50 en Chile), siempre en la tajada de 120° a 150° (SE), que es hacia donde iba la pluma en el loop de VOLCAT.
  VOLCAT pone pluma en el cráter de 17:40 a 21:30. De 13 cuadros de VOLCAT, el detector alcanza 10; ningún día placebo
  llega a eso a esas horas. Calza con H29, que vio la BTD baja en esas posiciones unos 50 min antes que VOLCAT.
- **Pero el 15-11, sin VOLCAT, pasa lo mismo.** Ese día VOLCAT está limpio toda la tarde (ningún píxel suyo a 50 km),
  y el detector dispara 13 veces de 16:00 a 22:50 UTC, 9 de ellas en la misma tajada SE. La tajada SE es además la
  que más veces queda como "la más baja" en todos los cuadros placebo (252 de 1.743, contra unos 145 de media).
- **Lectura honesta:** hay algo al SE, de tarde, que baja la diferencia 11 − 12 µm aunque no haya pluma en VOLCAT. Puede
  ser el terreno al oriente de la divisoria (más seco y caliente de tarde: el suelo desnudo da diferencia negativa, una
  falsa alarma clásica de los detectores de ceniza) o nubes de sotavento. Mientras no se separe ese efecto, el 08-11
  no prueba pluma.
- **Lo que el detector no ve:** las pasadas finas de la mañana (25-10 14:20 y 14:30; 08-11 14:40 y 14:50) no disparan.
  El 25-10 apunta a la tajada correcta (SO, donde Landsat vio la pluma) sin llegar al umbral; el 08-11 apunta al NE,
  no al S de la huella de Sentinel-2. Tampoco disparan los cuatro nacimientos de VOLCAT, como se predijo.

## 2. Veredicto por la regla

| Paso | Resultado | Fuente |
|---|---|---|
| Ensayo en seco | **Aprobado**: falsa alarma media 0,027 por cuadro (máx. 0,05). Por día: 26-10 0,157 y 15-11 0,123; los otros 12, 0 a 0,04. Despejados 0,017, nublados 0,028. Todas las horas con umbral | `resultados/seco.json` |
| Poder (8 píxeles en un rayo a 4 a 20 km, dos cuadros) | 0,010 a 0,33 K; 0,185 a 0,97 K | `resultados/poder.json` |
| Recuerdo por cuadro VOLCAT | **R = 36/96 = 0,375** (umbral 0,50) | `resultados/s22a_resultado.json` |
| Recuerdo por episodio | **5/13 = 0,385** (umbral 0,75) | idem |
| Azar (mismas horas en los 14 placebo) | 0 en 10 días; 0,067 (26-10), 0,05 (20-11), 0,196 (17-11), **0,386 (15-11)**; p = 2/15 = 0,133 | idem |
| Veredicto | **SIN PODER** (p > 1/15 y poder a 0,33 K < 0,8) | idem |

Por día VOLCAT (cuadros P alcanzados / evaluables; p del día contra su propio azar):

| Día | Alcanzados | p del día |
|---|---|---|
| 22-10, 24-10, 07-11 (un cuadro cada uno) | 0/1 | 1 |
| 25-10 | 0/4 | 1 |
| 28-10 | 8/26 | 0,13 |
| 29-10 | 0/6 | 1 |
| **08-11** | **10/13** | **0,067 (sobre los 14 placebo)** |
| 10-11 | 2/10 | 0,13 |
| 11-11 | 3/3 | 0,077 |
| 14-11 | 13/31 | 0,13 |

Por estado de cielo: 30 de 75 cuadros P despejados por E1, 6 de 21 nublados.

## 3. Informativo (no decide)

- **Sector de los disparos.** En los días VOLCAT, casi todo cae en la tajada 4 (120° a 150°): el 08-11, 21 de los 23
  disparos del día; de los cuadros P alcanzados, 12 de 13 el 14-11 y 6 de 8 el 28-10. En los placebo, los disparos del 15-11 son 9 de 13
  en la tajada 4 y los del 20-11 (23:10 a 23:30) 3 de 3; los del 26-10 (04:00 a 13:50) se reparten en 8 tajadas.
- **Otros cuadros de los días con actividad:** dispara en 65 de 1.501 cuadros `N` (0,043) y 32 de 442 `otro` (0,072).
- **Cuadros con archivo de evento de VOLCAT (13 a 18-11):** 8 disparos en 51 evaluados.
- **Nacimientos de VOLCAT:** ninguno dispara (13-11 19:00, 14-11 16:30, 18-11 10:10; 14-11 12:40 sin evaluar).
  Predicción escrita antes: cumplida.
- **Verdad fina (S20b):** ninguno de los cuatro cuadros dispara. 25-10: S −0,34 y −0,41 K contra U −0,58 y −0,61, la
  tajada del mínimo es la de la verdad (210° a 240°). 08-11: S −0,45 y −0,48 contra U −0,61, tajada del mínimo al NE
  (30° a 60°), no la de la verdad (180°, al S).

### Post hoc (mirado después del veredicto)

- El 15-11 de 16:00 a 22:50 UTC VOLCAT da clase `N` en los 37 cuadros (ningún píxel a 50 km en ±60 min) y no hay
  objetos anclados. El detector dispara 13 veces, 9 en la tajada SE. O es un efecto de superficie o de tiempo al SE
  por la tarde, o es una pluma que VOLCAT no vio. No se revisó con imagen fina ni con cámara.
- La tajada SE es la "más baja" en 14 % de los cuadros placebo (lo esperado al azar sería 8 %).

## 4. Lo que puede estar mal

- **El nulo de 14 días placebo lo deciden dos días** (15-11 y 17-11). Con otros placebo el p podría ser 1/15; con un
  día más como el 15-11, peor. Esa fragilidad es la misma de S21e.
- **La comparación entre tajadas supone que ninguna tiene un sesgo propio.** La tajada SE sí lo tiene (post hoc). Un
  detector que reste el comportamiento típico de cada tajada a cada hora quitaría ese sesgo; es criterio aparte.
- **E1 mira el terreno bajo**, no la cumbre ni la tajada; el 08-11 da despejado todo el día.
- **Llegar a VOLCAT no es detectar ceniza** (§0 del criterio). Y las pasadas finas de la mañana no se alcanzan: el
  detector no ve la pluma chica junto al cráter.

## 5. Qué deja esto

Primera vez que un detector propio, sin saber dónde mirar, sigue la tarde del 08-11 casi cuadro a cuadro y en la
dirección de la pluma. Pero dispara igual una tarde sin VOLCAT en la misma dirección. El paso siguiente natural es
quitar el sesgo de cada tajada a cada hora (anomalía de la tajada contra su propia historia placebo, de cualquier
cielo) y probarlo con un criterio nuevo **en días que no se miraron aquí**: del 19-11 en adelante, lo que requiere
cubos GOES nuevos y guardar las imágenes de VOLCAT de esos días antes de que SSEC las borre (guarda unos 30 días).
