# β(7,3/11) en episodios nuevos de Chillán: ¿se repite el indicio de H3?

Corrida del 19-11-2026. Criterio escrito y commiteado antes de bajar la primera escena L1b
(commit 3c217f7): `docs/own_volcat/beta73/criterio_beta73_2026-11-19.md`. Salida cruda con todas las
tablas: `docs/own_volcat/beta73/beta73_resultado.txt`. Scripts: `docs/own_volcat/beta73/scripts/`.

**Veredicto según el criterio:**

- **Noche y crepúsculo (el estrato que decide): NO CONCLUYENTE.** La huella VOLCAT sí sale con β(7,3/11)
  más alta que el control (AUC 0,82), pero el anillo sin ceniza que la rodea sale igual o más alto
  (AUC 0,90), y sólo 1 de los 3 días va en la dirección del indicio.
- **Día (extensión): SE FALSA.** AUC 0,41, IC 95 % [0,15; 0,63].

Lectura práctica (diagnóstico posterior, no decide): lo que separa la noche positiva de la de control es
la humedad de toda la escena, no la pluma. La banda de 7,3 µm distingue días húmedos de días secos, y esa
diferencia es de 5 a 15 K, mucho más grande que lo que la pluma de Chillán podría aportar.

## 1. La física: qué se buscaba y qué lo podía confundir

La banda C10 (7,3 µm) está en el ala de la banda de vapor de agua y encima de la banda ν3 del SO2. Una
pluma de Chillán lleva vapor de agua y SO2 a una altura donde el GFS no los pone, y los dos absorben
mucho a 7,3 µm y casi nada a 11,2 µm. Si la pluma está, C10 cae más que C14 respecto de su cielo
despejado, y la profundidad óptica efectiva a 7,3 µm supera a la de 11 µm: β(7,3/11) = τ(7,3)/τ(11)
mayor que 1, o Δτ = τ(7,3) − τ(11) mayor que cero. Eso es lo que H3 creyó ver, después de su criterio,
en dos tandas nocturnas del 28 y 29-10.

El problema es que C10 es, ante todo, un sensor de humedad de la troposfera media. Un día más húmedo
enfría C10 en toda la escena, haya pluma o no. El control pareado por BT11 empareja la temperatura de la
superficie (C14), no la humedad que ve C10. Por eso el criterio exigió que el efecto estuviera en la
huella y NO en el anillo de 2 a 6 píxeles que la rodea en la misma escena: si el anillo, sin ceniza
VOLCAT, muestra lo mismo, el efecto es del día y no de la pluma.

## 2. Qué se midió

**Episodios fuera de muestra.** Todos los cuadros VOLCAT de Chillán con objeto anclado al cráter (regla
de `paso4_analisis.py`: objeto de 4 a 500 px que toca el disco de 10 km, sin manto) entre el 20-10 y el
19-11, excluidos completos el 28 y el 29-10 (misma secuencia eruptiva y mismo tiempo que el indicio) y el
16-11 (manto). SSEC lista días desde el 03-10 pero sólo tiene cuadros desde el 20-10. Quedaron 68
cuadros: 7 de noche o crepúsculo (cenit solar ≥ 80°; 22-10, 10-11 y 14-11) y 61 de día (siete días).

**Control.** Para cada positivo, el día a ±10 días, al mismo minuto, sin ceniza VOLCAT a 50 km o menos
en ese cuadro ni a ±60 min, cuya mediana de BT11 sobre la huella queda más cerca (sólo C14), con
|ΔBT11| ≤ 3 K. Quedaron **49 pares**: los 7 nocturnos y 42 diurnos; 17 cuadros diurnos sin control y 2
con menos de 3 píxeles de huella (lista en la salida cruda).

**Cielo despejado.** E (principal): por píxel, mediana de las 3 escenas más tibias en BT11 entre los
candidatos del mismo minuto (8 a 17 escenas por cuadro). M (sensibilidad): el modelo línea por línea de
H3 con GFS 0,25°, sin recortes de temperatura fuera de la LUT. Datos: 641 escenas L1b de GOES-19 (C10,
C11, C14, C15, ventana de 83 × 94 píxeles), 350 de ellas nuevas; coeficientes Planck de cada NetCDF.

**Métrica.** β73 = τ(C10)/τ(C14) con la compuerta ε(C14) ≥ 0,02, que con el cielo E resultó medible en
los dos estratos (57 y 47 píxeles de noche), así que por la regla declarada decide β73 y no Δτ73. AUC
de la huella del positivo contra los mismos píxeles del control, IC 95 % por bootstrap por escena (2000
remuestreos), y la misma AUC en el anillo.

## 3. Resultados

Estrato N (noche y crepúsculo), por par, cielo E salvo la última columna:

| Positivo (UTC) | Control | ΔBT11 (K) | Px | AUC β73 huella | AUC Δτ73 huella | AUC β73 anillo | AUC β73 (M) |
|---|---|---|---|---|---|---|---|
| 22-10 01:50 | 01-11 | +2,54 | 8 | 0,25 | 0,11 | 0,35 | 0,88 |
| 10-11 22:30 | 01-11 | +0,13 | 14 | 0,65 | 0,97 | 0,98 | 0,92 |
| 10-11 22:40 | 04-11 | −0,44 | 6 | 0,69 | 0,03 | 0,83 | 0,11 |
| 10-11 22:50 | 07-11 | +1,80 | 6 | 1,00 | 1,00 | 1,00 | 0,67 |
| 10-11 23:00 | 07-11 | +0,17 | 6 | 1,00 | 1,00 | 1,00 | 0,73 |
| 10-11 23:20 | 07-11 | 0,00 | 7 | 1,00 | 1,00 | 1,00 | 0,87 |
| 14-11 22:40 | 08-11 | +0,10 | 29 | no medible (control sin píxeles que pasen la compuerta) | 1,00 | no medible | 1,00 |

Por episodio (día y estrato), cielo E salvo las dos últimas columnas:

| Estrato | Día | Pares | Px | AUC β73 huella | AUC β73 anillo | AUC Δτ73 | AUC β73 (M) | AUC anillo (M) |
|---|---|---|---|---|---|---|---|---|
| N | 22-10 | 1 | 8 | 0,25 | 0,35 | 0,11 | 0,88 | 0,92 |
| N | 10-11 | 5 | 39 | 0,89 | 0,97 | 0,86 | 0,77 | 0,75 |
| N | 14-11 | 1 | 29 | no medible | no medible | 1,00 | 1,00 | 0,98 |
| D | 24-10 | 1 | 4 | 0,00 | 0,35 | 0,50 | 0,12 | 0,10 |
| D | 25-10 | 1 | 12 | no medible | 0,00 | 0,01 | 0,00 | 0,23 |
| D | 07-11 | 1 | 4 | no medible | 0,00 | 0,00 | 0,00 | 0,00 |
| D | 08-11 | 9 | 78 | 0,00 | 0,00 | 0,06 | 0,15 | 0,20 |
| D | 10-11 | 7 | 80 | 0,51 | 0,49 | 0,68 | 0,74 | 0,52 |
| D | 11-11 | 2 | 9 | no medible | no medible | 0,15 | 0,00 | 0,22 |
| D | 14-11 | 21 | 259 | 0,11 | 0,41 | 0,19 | 0,49 | 0,40 |

Agrupado por estrato:

| Estrato, cielo | Pares (días) | AUC β73 huella | IC 95 % escena | IC 95 % por día (informativo) | AUC anillo | Huella − anillo | AUC Δτ73 | Veredicto |
|---|---|---|---|---|---|---|---|---|
| **N, E (decide)** | 7 (3) | **0,817** | [0,617; 0,972] | [0,250; 0,887] | **0,895** | **−0,078** | 0,776 | **NO CONCLUYENTE** |
| D, E | 42 (7) | 0,414 | [0,150; 0,626] | [0,075; 0,529] | 0,489 | −0,075 | 0,276 | **SE FALSA** |
| D sin 14-11, E | 21 (6) | 0,456 | [0,171; 0,687] | [0,000; 0,542] | 0,488 | −0,032 | 0,355 | no concluyente |
| N, M | 7 (3) | 0,867 | [0,632; 0,952] | [0,766; 0,998] | 0,830 | +0,037 | 0,460 | no concluyente |
| D, M | 42 (7) | 0,451 | [0,268; 0,613] | [0,143; 0,643] | 0,369 | +0,083 | 0,423 | se falsa |

## 4. Veredicto según el criterio

Estrato N, cielo E, β73 (medible: 57 y 47 píxeles, 6 pares aportan):

- AUC huella ≥ 0,70: **sí** (0,817).
- Límite inferior del IC 95 % > 0,55: **sí** (0,617).
- AUC huella − AUC anillo ≥ 0,10: **no** (−0,078). El anillo sin ceniza separa más que la huella.
- AUC huella > 0,5 en al menos 2 días: **no** (sólo 10-11; 22-10 da 0,25 y en 14-11 β73 no es medible
  porque en el control ningún píxel pasa la compuerta). Aunque el 14-11 se contara a favor, la condición
  del anillo sigue fallando y el veredicto no cambia.
- Falsación (límite superior del IC < 0,65): no (0,972).

**NO CONCLUYENTE.** Estrato D: límite superior del IC 0,626 < 0,65, **SE FALSA** (extensión diurna; no
cambia el veredicto nocturno). Atribución: con el cielo M el resultado es el mismo (noche no concluyente
por el anillo, día falsado), así que no depende del cielo elegido.

Hay que leer el 0,817 con cuidado: 5 de los 7 pares son de una sola noche (10-11), y 3 de esos 5 usan el
mismo control (07-11). El IC por escena trata los cuadros consecutivos como independientes y queda
angosto; el IC por día, que no decide, va de 0,25 a 0,89.

## 5. Diagnóstico posterior (no decide; se calculó después de las tablas)

**La noche del 10-11 es más húmeda en toda la escena.** Positivo menos control, mediana de
BT10 − BT14 (K) en la huella, en el anillo y lejos (a más de 20 píxeles, unos 40 km, de cualquier ceniza
VOLCAT), y agua precipitable del GFS sobre 600 hPa en el cráter:

| Par N | Huella | Anillo | Lejos | Agua precipitable 100 a 600 hPa (mm), positivo / control |
|---|---|---|---|---|
| 22-10 01:50 contra 01-11 | +2,70 | +1,26 | −3,66 | 0,79 / 1,32 |
| 10-11 22:30 contra 01-11 | −2,80 | −8,81 | −9,65 | 2,39 / 1,19 |
| 10-11 22:40 contra 04-11 | −0,49 | −2,21 | −4,71 | 2,39 / 1,41 |
| 10-11 22:50 a 23:20 contra 07-11 | −6,8 a −7,0 | −6,3 a −6,9 | −7,9 a −8,2 | 2,39 / 0,78 |
| 14-11 22:40 contra 08-11 | −5,19 | −5,20 | +1,20 | 1,15 / 0,45 |

El 10-11 tenía tres veces más vapor sobre 600 hPa que el 07-11, y C10 cae lo mismo a 40 km de la pluma
que encima de ella. En los 49 pares, la diferencia de humedad del GFS y la de BT10 − BT14 lejos de la
huella van juntas (Spearman ρ = −0,58, p = 1,4e-5). C10 está midiendo el tiempo, no la pluma. El único
par donde el exceso queda cerca del volcán y no lejos es el 14-11 22:40 (huella y anillo −5,2 K, lejos
+1,2 K); es un cuadro solo y no alcanza para decir nada.

**Con el cielo M, β73 separa pero Δτ73 no (0,867 contra 0,460).** Las medianas de β73 con M son menores
que 1 en los dos grupos (0,40 contra −0,02): τ(7,3) es menor que τ(11), lo contrario de lo que haría una
pluma rica en vapor. Con un numerador desplazado hacia abajo, cuando τ(11) crece (y con M crece por el
error del terreno: AUC de ε11 = 0,70) el cociente se acerca a 1 y "sube" sin que C10 haya absorbido más.
Es aritmética de la razón, no vapor.

**En los pares del indicio (28 y 29-10, H3) pasa algo parecido.** Mismo cálculo: las noches positivas eran
más secas que sus controles según el GFS (0,61 a 0,80 mm contra 1,17 a 1,43 mm), y en la huella
BT10 − BT14 quedó entre 0,3 y 1,9 K más TIBIA que lejos (salvo 23:40, 0,3 K más fría), no más fría como
pediría el vapor de la pluma. Una explicación coherente con eso es que el indicio de H3 haya sido el mismo
efecto de la razón con el cielo modelado, pero no se comprobó: es un cálculo hecho después y no se
recalcularon las medianas de β73 de H3.

## 6. Qué deja esta prueba

La β(7,3/11) no explica por qué VOLCAT ve Chillán y nosotros no. De día se falsa, y de noche el efecto
que apareció es de la humedad del día y no de la pluma. A 2 km de resolución, la variación de humedad
entre días enfría o calienta C10 entre 5 y 15 K, y cualquier vapor que aporte la pluma de Chillán queda
enterrado en eso. Para que C10 sirviera habría que modelar el cielo despejado de C10 con la humedad del
mismo día y del mismo lugar mejor que el GFS, y aun así la señal de la pluma tendría que superar el error
de ese modelo.

## 7. Desviaciones del criterio

1. El 14-11 22:40, que en H3 quedó sin control (+3,06 K), aquí tiene control (08-11, +0,10 K) porque la
   regla de candidatos (±10 días, sin ceniza a ±60 min) es otra; está escrita en el criterio.
2. Día del estrato con par pero AUC no medible (14-11 en N con cielo E): contado como "no a favor". Se
   dice arriba que contarlo a favor no cambia el veredicto.
3. Anillo con el cielo M: muestra fija de 40 píxeles por cuadro (semilla 1), por costo del modelo, como en
   H3. Con E se usó el anillo completo.
4. Ceniza del anillo: la máscara VOLCAT a cualquier distancia llevada a la grilla ABI por vecino más
   cercano, misma decodificación que la huella.
5. Bootstrap: AUC agrupada sobre los valores finitos de cada remuestreo; los remuestreos sin valores
   finitos se descartan (ninguno en los estratos que deciden).
6. Perfiles GFS por S3 (rango de bytes); los de 10-11 20 h, 11-11 20 h, 13-11 15 h y 17-11 22 h por el
   filtro de NOMADS, igual que H3, que lo verificó idéntico a S3.

## 8. Archivos

- Criterio: `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\Goes\docs\own_volcat\beta73\criterio_beta73_2026-11-19.md`
- Salida cruda: `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\Goes\docs\own_volcat\beta73\beta73_resultado.txt`
- Scripts: `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\Goes\docs\own_volcat\beta73\scripts\`
  (orden de corrida en `comun_b73.py` y en la nota de la carpeta compartida)
- Carpeta de trabajo (PNG VOLCAT del 20 al 24-10 y 18-19-11, 350 escenas L1b nuevas, perfiles GFS,
  señales por píxel `senales_b73.pkl`):
  `C:\Users\nmend\AppData\Local\Temp\claude\f4710304fa6a9a5b\6cc950d4-5fd7-4e45-a0af-882008093b90\scratchpad\b73\`
  (está en el scratchpad temporal; si se quiere conservar el caché, hay que moverlo).

Las rutas del repo están dadas sobre el checkout principal; mientras el PR no se fusione, viven en la
rama `claude/beta73-episodios-nuevos-f566cb`.
