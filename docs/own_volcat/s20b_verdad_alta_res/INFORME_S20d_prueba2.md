# S20d: prueba 2 de S20b, ventana partida a 100 y 70 m sobre Nevados de Chillán. Informe, 23-11-2026

Criterio: `criterio_2026-11-23.md` §3 (commit `4126049`) y su enmienda `enmienda_1_s20d_antes_de_medir_2026-11-23.md`
(commit `8f782ee`), empujados antes de medir. Medida: commit `ebdd59f`. Script `scripts/s20d_ventana_partida.py`,
salidas `resultados/s20d_resultado.json` y `s20d_medir.log`; ensayo en seco `resultados/s20d_seco.json`. Controles
post hoc: `scripts/s20d_posthoc.py`, `resultados/s20d_posthoc.json` y `.log`, figuras `figuras/s20d_landsat_btd.png` y
`figuras/s20d_ecostress_btd_pareada.png`. Datos en `D:\goes_notas\s20b\descargas\`.

- **Veredicto por la regla escrita (Landsat 8, 25-10, 100 m): SIN FIRMA.** La pluma sí se ve en el térmico
  (T1 = −3,3 K, p 0,003), pero su ventana partida pareada da T2 = −0,09 K (p 0,23), lejos de los −0,84 K que daría
  una capa de ceniza con ese contraste.
- **Ese veredicto es un artefacto del control, y los controles post hoc lo muestran sin ambigüedad.** La máscara de
  reflectancia marca sólo un tercio de la pluma. El resto quedó dentro del control, y el núcleo de la pluma, al
  parearse por temperatura, se comparó con pluma. Sacando del control el sector de la pluma, **T2 = −1,54 K, más bajo
  que los 2.022 corrimientos**, y el mismo lugar el 17-10 sin pluma da +0,23 K. En la imagen cruda la pluma es una
  mancha de 11 − 12 µm de −2 a −3 K al oeste-suroeste del cráter que no existe el 17-10 (figura).
- **Lectura:** a 100 m la pluma del 25-10 tiene una firma de ventana partida fuerte y negativa, la de la ceniza. La
  firma que GOES-19 vio en la prueba 1 no necesita la mezcla de superficies para explicarse. Es una conclusión post
  hoc: el veredicto formal sigue siendo SIN FIRMA hasta que una prueba con el control corregido escrito antes lo
  confirme (§6).
- **ECOSTRESS (sin veredicto):** el 08-11 a las 19:28, sobre la huella ancha de VOLCAT, no hay BTD negativa (contra el
  17-10 sale +0,20 K). El 25-10 a las 17:35 hay 28 km² de BTD pareada bajo −1 K entre 180 y 210° (sur-suroeste),
  hasta 20 km del cráter; la referencia no cubre ese sector.

## 1. El fenómeno, antes de los números

En la mañana del 25-10 Landsat 8 pasó a las 14:34 UTC sobre una franja translúcida que salía del cráter hacia el
oeste-suroeste. La prueba 1 la ubicó por reflectancia (la ceniza ensucia la nieve en 1,6 µm) y vio que GOES-19 baja
cerca de 1 K en 11 − 12 µm en el píxel que la contiene. Quedaba una duda: en un píxel de 2 km la diferencia 11 − 12
puede bajar por mezclar superficies distintas (nieve, roca, bosque), sin que la pluma tenga firma propia. Mirando la
misma pluma con el térmico de Landsat, que ve celdas de 100 m, esa mezcla desaparece.

Lo que se ve (figura `s20d_landsat_btd.png`):

- **En 10,9 µm** la pluma enfría la nieve unos 3 K: la nieve bajo la franja está a 271 K y la de su alrededor, a la
  misma cota, a 274 K. Con la temperatura del aire a 4,3 km (265 K, GFS), eso es una capa que tapa cerca del 40 % de
  la radiación del suelo (ε11 ≈ 0,38).
- **En 10,9 − 12,0 µm** la pluma es una mancha de −2 a −3 K, de al menos 9 km de largo hacia el oeste-suroeste (sigue fuera del recuadro), mucho más
  ancha que lo que marcó la regla de reflectancia (contorno verde). La nieve de alrededor está en −0,4 K. El 17-10, a
  la misma hora y sin pluma, ese lugar está en +0,05 K.
- **Una nube de agua o de hielo común da 11 − 12 µm positiva** (absorbe más en 12 µm). La ceniza silicatada absorbe
  más en 11 µm y da negativa. Lo que se ve es negativo y fuerte.

## 2. Resultado por la regla (criterio §3.2 y enmienda 1)

Máscara de reflectancia erosionada 3 celdas: 283 celdas de 30 m (0,25 km²). T1 = contraste en 10,9 µm contra el
anillo de 300 a 1.000 m a igual cota. T2 = BTD menos la de nieve control con la misma BT10 (±0,5 K) y la misma cota
(±150 m). p = fracción de 2.077 corrimientos de la máscara con T igual o más bajo.

| | 25-10 (decide) | 17-10, mismo lugar sin pluma (control de sitio) |
|---|---|---|
| T1 (nulo, percentiles 5 y 95) | **−3,33 K**, p 0,003 (−1,32; +2,09) | −0,36 K, p 0,26 |
| T2 (nulo, percentiles 5 y 95) | **−0,09 K**, p_bajo 0,23 (−0,33; +0,26) | +0,21 K, p_bajo 0,85 |
| BTD cruda, pluma / control (medianas) | −1,94 / −0,38 K | +0,05 / −0,08 K |
| ε11 desde T1; BTD de ceniza esperada | 0,38; −0,84 K (T_tope 265,5 K, T_sup 274,2 K) | |
| Fmask en la pluma | 100 % nieve, 0 % nube | 100 % nieve, 0 % nube |
| Veredicto | **SIN FIRMA** (hay contraste, p_bajo > 0,20 y T2 sobre la mitad de lo esperado) | no baja nada |

- Informativo, erosión 2 (535 celdas): T2 = −0,85 K, p 0 de 1.812, que habría sido FIRMA DE CENIZA.
- Informativo, evento menos 17-10 en la máscara y en cada corrimiento (enmienda §2.1): D(T1) = −2,97 K (p 0 de 2.073);
  D(T2) = −0,30 K (p 0,19) con erosión 3 y −1,03 K (p 0) con erosión 2.

Que la erosión cambie T2 de −0,09 a −0,85 K, con la misma pluma y la misma BTD cruda en las dos máscaras (−1,94 K), fue
la señal de que algo en el pareo no andaba.

## 3. Controles post hoc (escritos después de ver el resultado; no cambian el veredicto)

**(a) Por capa, del borde al núcleo.** La BTD cruda es la misma en todas las capas (−1,7 a −2,0 K); T2 no:

| Capa | Celdas | BT10 | BTD cruda | T2 25-10 | T2 17-10 |
|---|---|---|---|---|---|
| borde (0 a 1) | 795 | 274,5 K | −1,72 K | −1,08 K | +0,16 K |
| 1 a 2 | 427 | 273,1 K | −1,93 K | −1,25 K | +0,20 K |
| 2 a 3 | 252 | 272,4 K | −1,96 K | −1,26 K | +0,16 K |
| 3 a 4 | 137 | 271,9 K | −1,96 K | −1,07 K | +0,20 K |
| 4 a 5 | 75 | 271,4 K | −1,96 K | −0,05 K | +0,27 K |
| núcleo (5 o más) | 71 | 271,1 K | −1,93 K | +0,14 K | +0,17 K |

El T2 se derrumba justo cuando la BT10 baja de unos 271,5 K, no cuando cambia la BTD.

**(b) Con qué se parea el núcleo.** A la cota del núcleo (2.037 m ±150 m), la nieve control con BT10 entre 270 y
272 K son 109 celdas, **todas en el sector de la pluma** (oeste-suroeste, 2 a 12 km), con BTD de −2,12 K. El 17-10 hay
2.718 celdas de nieve a esa temperatura, ninguna en ese sector, con BTD de −0,57 K. Esas 109 celdas son pluma que la
regla de reflectancia no marcó: está fría y tiene la misma BTD que la pluma. El núcleo, que es lo más frío de la
pluma, sólo encuentra pares ahí, y se compara consigo mismo. Fuera de ese extremo el control está limpio: de las
102.767 celdas control que parean con alguna celda del núcleo, 5 % están en el sector.

**(c) Control sin el sector de la pluma** (azimut 200 a 290°, 2 a 12 km):

| | 25-10 | 17-10 |
|---|---|---|
| T2, erosión 3 | **−1,54 K**, p 0 de 2.022 (nulo −0,28; +0,24); 107 de 283 celdas con par | +0,23 K, p_bajo 0,87 |
| T2, erosión 2 | **−1,52 K**, p 0 de 1.791 | +0,21 K, p_bajo 0,85 |

Sin el sector, las celdas más frías del núcleo quedan sin par (176 de 283) y T2 se mide con las demás. Con este control
la regla habría dado FIRMA DE CENIZA.

**(d) Cuánto más ancha es la pluma en el térmico.** Nieve con BTD 1 K o más bajo la mediana del control, a 2 a 15 km:

| | En el sector de la pluma | Fuera del sector |
|---|---|---|
| 25-10 | 4,76 km² (21 % de la nieve del sector) | 0,18 km² |
| 17-10 | 0,15 km² | 3,26 km² |

La máscara de reflectancia mide 1,59 km²: **la pluma en la nieve es unas tres veces lo que ve la regla de
reflectancia**, y sigue sobre el bosque, que aquí no se cuenta. Esto calza con lo que dejó abierto la prueba 1: el
25-10 la señal en el píxel de GOES era tres veces mayor que la que permitía la fracción medida (INFORME §3, punto 3).

**Magnitud.** Con ε11 = 0,38 y 8,8 K entre la superficie y el tope, el modelo simple de capa de ceniza con β = 0,7 da
−0,84 K; lo medido sin contaminar es −1,5 K, casi el doble. El modelo es una capa única, lineal y con β fijo; un β más
bajo (ceniza más fina o de otra composición) o una capa más fría que el GFS a 4,3 km dan más. No se ajustó nada.

## 4. ECOSTRESS (lectura con regla fija, sin veredicto)

Bandas 4 y 5 (10,5 y 12,0 µm, longitudes del propio archivo), versión 002, sólo celdas con calidad 0 y sin nube ni agua.

**08-11, 19:28 UTC, sobre la huella de VOLCAT de 19:20** (10 píxeles con un píxel alrededor, llevados al suelo con su
altura de 2,5 o 3,5 km: 267 km², 2,9 a 30 km del cráter):

| | T1 | T2 |
|---|---|---|
| Crudo (559 corrimientos) | −0,85 K, p_bajo 0,03 | −0,01 K, p_bajo 0,45 |
| 08-11 menos 17-10 20:42, celdas válidas los dos días (26.920 de 54.579; 82 corrimientos) | **−0,97 K**, p_bajo 0,04 | **+0,20 K**, p_alto 0 |
| Versión 003, lo mismo | −0,96 K, p_bajo 0,01 | +0,17 K, p_alto 0 |

La huella es un poco más fría que su alrededor y, en 11 − 12 µm, va hacia arriba, no hacia la ceniza. Pero es una
máscara de 267 km² hecha con píxeles de 2 km, en la que la pluma, si está, ocupa una parte chica; la referencia es
otro día, a otra hora (20:42 contra 19:28) y cubre la mitad de la huella. **No sirve para decir que la pluma de la tarde
del 08-11 no tiene ceniza**; sólo que, a escala de la huella entera, no hay ventana partida negativa.

**25-10, 17:35 UTC, mapa de BTD pareada a 2 a 25 km** (figura `s20d_ecostress_btd_pareada.png`): 144 regiones de
0,1 km² o más bajo −1 K, 77 km² en total (6,8 % de las celdas). La más grande, de 17 km², está a 12,8 km hacia 199°;
otras de 4, 3 y 2 km² hacia 204 a 211°, a 3,6, 20 y 17 km. Por sector de 30°: **28 km² entre 180 y 210°** y 12 km²
entre 150 y 180°; en el oeste-suroeste de la mañana (225 a 270°) sólo 0,9 km². La referencia del 17-10 20:42 tiene
31 regiones y 6,4 km² (3,2 % de las celdas), pero **sólo cubre la mitad noreste del disco**: el sector sur-suroeste no
tiene comparación. El REAV decía sureste (135°) para el episodio de 16:23 a 21:16 de ese día. Es descriptivo: el
mapa tiene también bandas de relieve (crestas rojas y azules) en todas direcciones, y no decide nada.

## 5. Qué significa

1. **La ceniza de Chillán sí tiene ventana partida negativa cuando el píxel la resuelve.** A 100 m, la pluma de la
   mañana del 25-10 deja −1,5 K de 11 − 12 µm contra la nieve de igual temperatura y cota, y −2 a −3 K en crudo. El
   mismo lugar sin pluma da +0,2 K. Agua líquida da positivo.
2. **La firma que GOES-19 vio en la prueba 1 viene de la pluma, no de la mezcla de superficies.** En el píxel de 2 km
   la pluma cubre una fracción y la firma se diluye a cerca de 1 K, que es lo medido. La pregunta de por qué el IR de
   2 km casi no la ve se contesta por el tamaño del píxel y lo delgado de la capa, no por falta de firma de ceniza.
3. **La regla de reflectancia subestima la pluma unas tres veces.** La franja translúcida sobre nieve sólo se marca
   donde ensucia lo suficiente el 1,6 µm; en el térmico se ve entera. Es lo que la prueba 1 sospechó del 25-10.
4. **Para medir la ventana partida de una pluma, el control no puede estar en su camino.** El pareo por BT es correcto
   (la BTD de la nieve depende de su temperatura) pero lleva a comparar lo más frío de la pluma con su propia cola no
   marcada. Es MET-01 en miniatura: el control "sin pluma" tenía pluma.

## 6. Lo que puede estar mal

- **El sector excluido en (c) lo elegí mirando la figura** (azimut 200 a 290°, 2 a 12 km). Es ancho y no está ajustado
  al borde de la mancha, pero es post hoc. La salida limpia es una prueba nueva con el control fuera de un sector
  fijado antes por la geometría (dirección de la pluma por reflectancia o por el viento del GFS, con un margen), en
  otra pasada de Landsat con pluma sobre nieve.
- **Una sola escena.** Es una mañana, una pluma, 283 celdas de 30 m (unas 25 celdas independientes del TIRS de
  100 m). La señal es grande (−1,5 K contra un nulo de ±0,25 K) y se repite en todas las capas del borde, pero es un
  caso.
- **Hielo muy fino.** Cristales de hielo muy chicos pueden dar 11 − 12 µm levemente negativa; con dos bandas no se
  separa del todo. A 4,3 km el aire está a −8 °C. Lo medido (−1,5 a −3 K) es más de lo que se suele atribuir a hielo,
  pero no lo descarto con este dato.
- **Banda 11 de Landsat 8.** Tiene un residuo de luz parásita de gran escala; se mide en pares dentro de 15 km, donde
  ese residuo es casi constante, y el control de sitio (Landsat 9, otro sensor) no muestra nada en ese lugar.
- **ECOSTRESS** no decide: la máscara del 08-11 es demasiado gruesa para la pregunta, y la referencia del 25-10 no
  cubre el sector donde está la señal.

## 7. Siguiente paso

Repetir la prueba 2 con el control corregido escrito antes de medir, en otra pasada de Landsat 8 o 9 con pluma sobre
nieve (Chillán tiene pasada a las 14:34 UTC cada 8 días). Regla propuesta: control fuera de un sector de ±45° alrededor
del eje de la pluma, a 2 a 12 km, con el eje sacado de la máscara de reflectancia; el resto igual. Si da FIRMA DE
CENIZA, la conclusión de §5 deja de ser post hoc.
