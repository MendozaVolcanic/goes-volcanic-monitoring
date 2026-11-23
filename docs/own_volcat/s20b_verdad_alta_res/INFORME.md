# S20b: verdad de alta resolución sobre Nevados de Chillán. Informe, 23-11-2026

Criterio: `criterio_2026-11-23.md`, commit `4126049`, empujado antes de medir. Medida: commit `2f2aa63`. Scripts en
`scripts/`, salidas en `resultados/`, máscaras en `figuras/`. Datos pesados en `D:\goes_notas\s20b\`.

- **Prueba 1 (TER-01 y TER-02), huella fina en el píxel de GOES-19: SEÑAL**, los dos días, en la BTD pareada (M1) y
  en la BT11 contra su anillo (M2). Pasa los tres controles post hoc.
- **Prueba 2 (ventana partida a 100 y 70 m): PENDIENTE.** El acceso a Earthdata falla (401) y el nivel 1 de Landsat
  pide cuenta USGS; se preguntó a Nicolás. El criterio ya está escrito (§3 del criterio).

## 1. El fenómeno, antes de los números

Las dos pasadas finas muestran una pluma chica y bien delimitada, a la misma hora en que GOES-19 mira:

- **25-10, 14:34 UTC (Landsat 8).** Una franja translúcida que sale hacia el oeste-suroeste (centroide a 4,6 km, a
  253°), de 1,5 a 2 km de ancho, que cruza la nieve y sigue sobre el bosque. El REAV decía sureste para ese día; el
  VAAC, suroeste. La sombra no sirve para medir la altura porque la franja corre casi paralela a ella; se usa la del
  VAAC, 4,3 km.
- **08-11, 14:53 UTC (Sentinel-2).** Una bocanada compacta de unos 2,5 km pegada al cráter por el sur (centroide a
  1,6 km, a 207°). Su sombra cae 1,35 km hacia el suroeste: la bocanada está 2,4 km sobre el terreno, a **4,7 km de
  altura**, lo mismo que dijo el VAAC (FL150 = 4,6 km) con un método que no tiene nada que ver.

En la grilla de GOES, después de corregir la paralaje (la pluma a 4,3 o 4,7 km aparece unos 2 km más al sur que el
suelo que tiene debajo), **la pluma llena a lo más el 18 % de un píxel el 25-10 y el 43 % de uno el 08-11.** Es lo
que se sospechaba: del tamaño de un píxel o menos.

La pregunta era si un objeto así deja algo en ese píxel. Lo deja: el píxel más cubierto queda **cerca de 1 K más bajo
en la diferencia 11 − 12 µm** que los píxeles de igual temperatura y cota, y **4 a 9 K más frío que su anillo**,
comparado con lo que ese mismo píxel hace en los días despejados sin evento. Ningún otro día despejado del cubo, ni
siquiera los días con actividad, deja ese píxel tan bajo en la diferencia 11 − 12 µm.

## 2. Resultado por la regla del criterio

Decide: altura de la tabla 1.2 del criterio y el cuadro más cercano. p = fracción de corrimientos de la huella con
una anomalía igual o más baja (1.182 corrimientos el 25-10, 1.062 el 08-11). D está en unidades de "píxel lleno"
(la pendiente k contra f, menos su línea base despejada).

| Evento, cuadro | M1 (BTD pareada): D, p | M2 (BT11 contra anillo): D, p | Veredicto M1 / M2 |
|---|---|---|---|
| 25-10, 14:30 (decide) | −6,32 K; p < 0,001 (0 de 1.182) | −21,9 K; p 0,005 | **SEÑAL / SEÑAL** |
| 25-10, H − 1 km / H + 1 km | p < 0,001 / p < 0,001 | p 0,003 / p 0,009 | SEÑAL / SEÑAL en las dos |
| 25-10, 14:20 (informativo) | p 0,002 | p 0,003 | SEÑAL / SEÑAL |
| 08-11, 14:40 (decide) | −1,89 K; p 0,011 | −19,6 K; p < 0,001 | **SEÑAL / SEÑAL** |
| 08-11, H − 1 km / H + 1 km | p 0,026 / p 0,007 | p 0,001 / p < 0,001 | SEÑAL / SEÑAL en las dos |
| 08-11, 14:50 (informativo) | −3,61 K; p < 0,001 | −24,5 K; p < 0,001 | SEÑAL / SEÑAL |

Ensayo en seco: 0 de 6 días base con p ≤ 0,05, en M1 y en M2, los dos eventos (el criterio declaraba inválida la
prueba con 2 o más). Potencia de la referencia (ε11 = 0,5) en M1: 0,33 el 25-10 y 1,00 el 08-11. Por la regla, SEÑAL
no depende de la potencia; la potencia baja del 25-10 sólo dice que una pluma de la fracción medida y ε = 0,5 no
habría alcanzado, y la señal medida es más grande que eso (§3).

En kelvin, en el píxel más cubierto (lo que se puede comparar con un satélite):

| | 25-10, píxel (43, 44), f = 0,18 | 08-11, píxel (44, 46), f = 0,43 |
|---|---|---|
| M1 del evento contra su mediana en días despejados | −1,39 contra −0,42: **−0,97 K** | −1,32 contra −0,48: **−0,84 K** (14:50: −1,46 K) |
| M1 esperado con ε11 = 0,5 (criterio §1.4) | −0,30 K | −0,85 K |
| M2 del evento contra su mediana en días despejados | −8,4 contra −4,6: **−3,8 K** | −10,4 contra −3,1: **−7,3 K** (14:50: −9,4 K) |
| M2 esperado con ε11 = 0,5 | −1,4 K | −3,6 K |

## 3. Qué significa

1. **Con la huella puesta donde de verdad está, GOES-19 sí ve la pluma de la mañana en el píxel de al lado del
   cráter.** Es la primera vez que la ubicación de la pluma no sale de VOLCAT ni de un REAV. H24 no vio firma en los
   pulsos de la mañana del 25-10 buscando hacia el sureste (dirección del REAV), en un sector de ±30° entre 4 y 25 km;
   a la hora de Landsat la pluma iba al oeste-suroeste y su parte sobre nieve estaba a unos 4 a 5 km del cráter.
2. **El 08-11 la firma en la diferencia 11 − 12 µm calza con ceniza tenue.** La bocanada cubre 43 % del píxel y el
   píxel baja 0,84 K: es lo que da una capa con ε11 ≈ 0,5 y la relación de ceniza (β = 0,7). La BT11 baja el doble
   de lo esperado para esa capa (−7,3 K contra −3,6 K): la bocanada es más fría u opaca de lo supuesto, o la sombra
   que proyecta enfría el suelo del píxel vecino. Ninguna de las dos cosas cambia la firma espectral (§4, control a).
3. **El 25-10 la señal es tres veces mayor que la que permite la máscara.** La máscara sólo ve la pluma sobre nieve
   (73 % del píxel) y la franja sigue sobre el bosque. Es probable que la fracción real sea mayor que 0,18; por eso la
   D "de píxel lleno" del 25-10 (−6,3 K) no se puede leer como la BTD de la ceniza, sino como un límite de la
   máscara.
4. **VOLCAT no dibujó esa bocanada a la hora de la medida.** El 08-11 VOLCAT no tiene ningún píxel en la ventana a las
   14:40 ni a las 14:50, y a las 15:00 marca tres que incluyen los dos píxeles de la bocanada (huella del PNG de SSEC
   leída en D:, sólo se informa el conteo). Para el 25-10 no hay PNG en la copia local.
5. **Lo que esto no dice.** No hay aún un detector: la señal es de un píxel, de unos 1 K, y aparece sólo porque se
   sabía dónde mirar y porque cada píxel se compara contra su propia historia despejada (el píxel de la cumbre tiene
   una BTD pareada de −0,4 a −0,8 K todos los días despejados, que no es pluma). Son dos mañanas despejadas; las
   tardes, que es cuando VOLCAT más dibuja, no tienen pasada fina salvo ECOSTRESS.

## 4. Controles post hoc (escritos después de ver la señal; no cambian el veredicto)

Script `scripts/s20b_posthoc.py`, salida `resultados/posthoc.json` y `posthoc.log`.

- **(a) ¿Es la firma espectral o sólo el enfriamiento?** M1 empareja por BT11, así que un píxel que se enfría cambia
  de pares. Pinté en los días base una capa **gris** (igual emisividad en 11 y 12 µm) con la misma f y la misma
  temperatura: M1 casi no se mueve (D −0,06 a −0,41 K contra −1,2 a −2,1 K de la capa de ceniza) y su potencia es 0
  de 6 (salvo 1 de 6 con ε = 0,9 el 25-10). M2 se mueve igual con las dos. **M1 responde a la firma de ceniza, no al
  enfriamiento**; la sombra de la pluma, que enfría sin firma espectral, no explica M1.
- **(b) ¿Es la temporada?** Serie del píxel más cubierto en todos los días despejados del cubo (12 y 13 días,
  incluidos los excluidos por actividad): el valor de M1 del evento es **el más bajo de todos** los dos días (25-10:
  −1,39 contra −0,00 a −0,80; 08-11: −1,32 contra +0,00 a −0,81). M2 tiene otros días casi tan fríos: el 13-11, día con
  bocanadas según Sentinel-2 (TER-03), da −11,7 con M1 en 0,0.
- **(c) ¿Es cualquier cumbre?** Restringiendo los corrimientos a los que ponen el píxel más cubierto sobre otro píxel
  de la misma cota (±300 m; 370 y 267 corrimientos): M1 p < 0,003 el 25-10 y p 0,023 el 08-11; M2 p 0,014 y 0,004.

## 5. Lo que puede estar mal

- **Dos eventos, un píxel dominante en cada uno.** Todo el peso está en (43, 44) y (44, 46). Son píxeles vecinos del
  bloque del cráter; el calor de la colada sube BT11 y BTD, o sea, va en contra de la señal, no a favor.
- **El diseño cambió dos veces antes de medir** (está en el criterio): los días base tuvieron que ser los despejados
  (la ACMF marca nublada la cumbre nevada casi siempre) y el nulo pasó de rango temporal a espacio-temporal porque con
  6 días el rango no controla la falsa alarma. Ningún cambio se hizo después de ver el evento.
- **Seis días base**, de fines de septiembre a principios de noviembre, con la nieve en retroceso. Los corrimientos
  comparten la misma línea base, así que lo estacional se cancela salvo que afecte sólo a esa cumbre; la serie (b) no
  muestra tendencia en M1.
- **f es un mínimo** (sólo pluma sobre nieve) y la hora del barrido de Chillán es una estimación (±2 min) a 4 a 5
  min de la pasada fina.
- **Los controles son post hoc.** Los pedí yo después de ver SEÑAL; su resultado es favorable, pero no es lo mismo que
  un control escrito antes.

## 6. Prueba 2: estado

Criterio en §3 del criterio. Datos localizados, sin bajar: HLS L30 del 25-10 (B10 y B11 como temperatura de brillo
de Landsat) y ECOSTRESS L1CT_RAD del 25-10 17:35 y 08-11 19:28 (teselas 19HBV, 23 a 42 MB por pasada; el catálogo
lista `radiance_1` a `radiance_5`, falta ver cuáles traen dato). Bloqueo: el `_netrc` de Earthdata está vencido
(REGISTRO_CREDENCIALES fila 2) y el nivel 1 de USGS pide cuenta ERS. Lo que importa de la prueba 2 después de la
prueba 1: si a 100 m la franja del 25-10 tiene diferencia 11 − 12 µm negativa, la firma que vio GOES es de la ceniza
y no de la mezcla de superficies dentro del píxel.
