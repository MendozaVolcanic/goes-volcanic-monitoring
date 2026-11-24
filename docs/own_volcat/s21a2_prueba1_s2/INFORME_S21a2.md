# S21a2: repetición de la prueba 1 de S20b en Sentinel-2 del 29-10 y del 13-11. Informe, 24-11-2026

Criterio `criterio_2026-11-24.md` (commit `50b534e`) y enmienda `enmienda_1_antes_de_medir_2026-11-24.md` (commit
`631b62c`), los dos empujados antes de leer GOES. Regla de S20b sin cambios (`4126049`); el código que mide es el de
`s20b_verdad_alta_res/scripts/`, sin editar, llamado por `scripts/s21a2_correr.py`, que sólo cambia fechas, hora,
altura de respaldo del VAAC y carpetas. Salidas en `resultados/`, máscaras en `figuras/`, datos en
`D:\goes_notas\s21\a2\`.

**Resultado en una línea: estas dos pasadas no repiten ni contradicen S20b.** La máscara de S20b, aplicada sin
tocarla, marca sobre todo bordes de nieve en fusión a 7 a 16 km del cráter, no la pluma; la pluma visible es chica y
el 29-10 cae entera en el bloque del cráter que la prueba excluye. Por la regla, M1 da SIN PODER los dos días; M2 da
INVÁLIDO el 29-10 y SIN PODER el 13-11.

## 1. El fenómeno, antes de los números

- **29-10, 14:53 UTC (Sentinel-2C, nubosidad 2 %).** Se ve una bocanada blanca chica pegada al cráter por el ESE,
  a menos de 1,1 km del centro (0,3 km² marcados sobre nieve). El VAAC de 12:30Z veía una pluma tenue hacia el ENE. La
  sombra no da altura (no hay sombra marcada: mediana 0,78 contra el máximo de 0,5), así que se usa la del VAAC, 4,3 km.
- **13-11, 14:53 UTC (Sentinel-2B, nubosidad 27 %).** Una nube blanca a 2 a 5 km al NE del cráter, marcada sólo en su
  parte sobre nieve (0,8 km²), que sigue sobre el bosque. Un piloto reportó ceniza a FL130/140 a las 14:29Z y el VAAC
  no la vio en el satélite con cielo parcialmente cubierto. Altura: 4,3 km (tope del reporte del piloto).

La máscara de la regla marca además cientos de manchas angostas en el borde de la nieve, lejos del cráter: es la
nieve que se derrite entre la referencia (3 a 5 días antes) y la pasada. En S20b la pluma dominaba la suma de
fracciones (86 a 94 %); aquí la pluma aporta 3 % (29-10) y 5 % (13-11). Los píxeles de GOES que la regla prueba son,
por lo tanto, píxeles de borde de nieve: el 29-10 un píxel a 14 km al E del cráter, a 1.376 m de cota; el 13-11 seis
píxeles, dos a 6 y 10 km al NO y cuatro a 15 a 18 km al SE (posiciones en la grilla ABI, con la paralaje de 4,3 km). Esto se escribió en la enmienda 1 antes de leer GOES.

## 2. Resultado por la regla (decide: altura de §2 del criterio, cuadro de 14:40)

p = fracción de corrimientos de la huella con D igual o más bajo (1.007 corrimientos el 29-10, 965 a 969 el 13-11).
D en unidades de "píxel lleno". Días base: 10, 15, 16, 17-10, 02 y 04-11 (los seis, los mismos del 08-11 en S20b).

| Pasada, variante, cuadro | M1 (BTD pareada): D, p, potencia, seco | M2 (BT11 contra anillo): D, p, potencia, seco | Veredicto M1 / M2 |
|---|---|---|---|
| 29-10, H, 14:40 (decide) | +3,92 K; p 0,97; 0,50; 0 de 6 | −14,1 K; p 0,067; 0,33; **2 de 6** | **SIN PODER / INVÁLIDO** |
| 29-10, H − 1 km / H + 1 km | p 0,99 / 0,87 | p 0,033 (seco 2 de 6) / p 0,043 (seco 0 de 6) | SIN PODER / INVÁLIDO y SEÑAL |
| 29-10, H, 14:50 (informa) | +5,82 K; p 0,995 | −8,6 K; p 0,17 | SIN PODER / INVÁLIDO |
| 13-11, H, 14:40 (decide) | +3,21 K; p 0,92; 0,67; 0 de 6 | +37,4 K; p 0,99; 0,33; 0 de 6 | **SIN PODER / SIN PODER** |
| 13-11, H − 1 km / H + 1 km | p 0,87 / 0,93 | p 0,996 / 0,97 | SIN PODER / SIN PODER |
| 13-11, H, 14:50 (informa) | +0,74 K; p 0,60 | −14,6 K; p 0,35 | SIN PODER / SIN PODER |

- **29-10, M2 INVÁLIDO.** En el ensayo en seco, 2 de los 6 días base (15-10 y 17-10) dan p ≤ 0,05 sin pintar nada: el
  píxel de borde de nieve contra su anillo varía de un día despejado a otro tanto como una pluma. El criterio declara
  inválida la prueba con 2 o más. Con H + 1 km la población cambia, el seco da 0 de 6 y M2 da SEÑAL (p 0,043); el
  veredicto que decide es el de H, y por la enmienda 1 no se atribuiría a pluma de ninguna forma.
- **13-11, cuadro de 14:40 con nube.** Ese cuadro no está despejado por E1, y el píxel más cubierto tiene BT11 = 248,6 K
  (una nube fría encima; en los días base ese píxel está a 261 a 276 K). M1 no se puede calcular en ese píxel (no hay
  pares de igual BT11). Por eso M2 sube a +37 K en unidades de píxel lleno: el anillo está más frío que el píxel. El
  cuadro de 14:50, despejado por E1, da también SIN PODER.
- **El signo.** M1 queda del lado opuesto a la ceniza en las dos pasadas (D positivo: el píxel tiene la diferencia
  11 − 12 µm más alta que su historia despejada, no más baja).

**Lectura de la repetición (criterio §4 y enmienda §2):** ninguna pasada da SEÑAL ni SIN FIRMA en M1, así que **no
decide**. SIN PODER no es evidencia en contra: dice que en esos píxeles, con la fracción medida, ni una capa de
ceniza de ε11 = 0,5 habría salido significativa en más de la mitad a dos tercios de los días base.

## 3. Controles escritos antes (informativos, no deciden)

`s20b_posthoc.py` sin cambios (`resultados/posthoc.json`):

- **(a) Capa gris contra ceniza.** Igual que en S20b: la capa gris (sin firma espectral) no mueve M1 (potencia 0 de 6,
  D esperado −0,2 a −0,7 K contra −1,1 a −2,5 K de la ceniza). M1 sigue siendo una medida de firma espectral; aquí no
  hubo firma que medir.
- **(b) Serie del píxel más cubierto.** 29-10, píxel (41, 53): M1 del evento −0,41 K, dentro del rango de los otros
  12 días despejados (−1,04 a +0,35 K). 13-11, píxel (46, 52): en el cuadro que decide no hay M1 (nube); M2 −5,1 K, el
  más frío de la serie (−3,8 a +2,4 K), coherente con la nube fría encima.
- **(c) Placebo de cumbre.** 29-10: M1 p 0,97, M2 p 0,043 (376 corrimientos de igual cota). 13-11: M1 p 0,92, M2 p 1,0
  (84). Nada que agregar a lo de §2.

## 4. Qué significa

1. **La prueba 1 de S20b no se pudo repetir en estas pasadas, y no por falta de señal sino por falta de pluma medible
   con esa regla.** La pluma visible del 29-10 está dentro del bloque de 3 × 3 píxeles del cráter que la prueba excluye
   (la colada caliente contamina ese bloque); la del 13-11 aporta un solo píxel con f ≈ 0,12 a 0,14. La variante
   "núcleo" escrita antes de medir (sólo manchas a ≤ 6 km del cráter) da Σ f = 0,03 y 0,16, bajo el mínimo de 0,20:
   SIN DATO.
2. **La máscara de S20b no es una regla transportable.** Funciona cuando la referencia es de pocos días y no hay fusión
   entre medio; en plena primavera marca el borde de la nieve. En S20b la pluma pesaba más que esos bordes y por eso no
   se notó; su propio aviso ya decía que una versión anterior marcaba cambios de nieve. Para la próxima repetición la
   máscara tiene que excluir el borde de la nieve de referencia o exigir que la mancha se vea también como nube en
   color (eso es otra regla y lleva criterio propio).
3. **El control de borde de nieve sale limpio en M1.** Los píxeles de borde de nieve, que sí cambian de superficie entre
   los días base de octubre y la pasada, no dan M1 bajo: D sale positivo, del lado contrario a la ceniza. Eso resta peso
   a la duda de que la SEÑAL de M1 en S20b viniera de la fusión de la nieve. Es una lectura post hoc (la enmienda
   preveía leer SEÑAL como alerta; no previó leer la ausencia como control), y es de dos días.
4. **M2 en borde de nieve es inestable** (INVÁLIDO el 29-10: 2 de 6 días base con p ≤ 0,05 en seco). Si una próxima
   prueba pone píxeles de borde de nieve en la población, M2 no va a poder leerse.

## 5. Lo que puede estar mal

- **Los mismos seis días base de S20b (08-11).** La repetición no tiene línea base independiente.
- **Altura sin sombra.** Las dos pasadas usan 4,27 km del VAAC o del piloto; con la pluma tan pegada al cráter la
  paralaje mueve poco la huella, y la sensibilidad H ± 1 km no cambia los veredictos de M1.
- **Del 10 al 17-10 no hay catálogo de objetos VOLCAT** (empieza el 20-10): un día base puede tener una bocanada que
  nadie registró (MET-01). Sesga D hacia cero.
- **Ya se había visto GOES en dos píxeles de estas fechas** (criterio §6, serie post hoc de S20b): (43, 44) y (44, 46).
  Ninguno quedó en la población nueva.

## 6. Para repetir de verdad

Buscar pasadas Sentinel-2 o Landsat con la pluma sobre nieve a más de 2 km del cráter (fuera del bloque) y con una
referencia anterior sin fusión entre medio; o escribir antes una máscara nueva que no confunda pluma con borde de
nieve y repetir S20b completo (los cuatro días: 25-10, 29-10, 08-11, 13-11) con ella. El invierno 2027 (nieve
estable, sin fusión) es la temporada natural para esta prueba.
