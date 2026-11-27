**Veredicto: NO DECIDIBLE (pocos cuadros); falsa alarma 2024 NO AGUANTA; sesgo 2025 SIN SESGO SE. Mirando sólo los 4 a 15 km alrededor del cráter, a la hora en que VOLCAT dibuja la pluma, la corona casi nunca dispara (3 de 52 cuadros, todos la tarde del 08-11), así que no se puede saber si ve el tramo. Además, en oct-nov de 2024, con el volcán tranquilo, dispara cuatro veces más que el anillo congelado, hacia el flanco SE. Y aunque hubiera habido cuadros, la prueba no tenía cómo separar "el tramo" de "el rumbo": con píxeles de 2 km, la huella de VOLCAT dilatada cubre casi la mitad de cada tajada de la corona, y ni VOLCAT un cuadro antes pasa el nulo de posición (p 0,013).**

# S31h: corona cercana (4 a 15 km del cráter) con regla propia. Informe, 27-11-2026

Criterio `criterio_2026-11-27.md` (commit `6ef64c4`, empujado a las 04:18 UTC antes de calcular un solo disparo de la
corona). Script `scripts/s31h_medir.py` (commit `8ca00ff`, 04:22 UTC, antes de medir; arreglo de una línea de impresión
en `6c4d32a`, §4). Post hoc `scripts/s31h_posthoc.py`. Cifras en `resultados/s31h_resultado.json`,
`resultados/s31h_por_cuadro.csv` y `resultados/s31h_posthoc.json`. Cubos de z, tablas de disparos y registros en
`D:\goes_notas\s31\s31h\`. **Desarrollo, no confirmación:** los días de 2024, 2025 y 2026 (hasta el 24-11) ya los
habían visto otras sesiones. Ningún día posterior al 24-11; nada de `s23b_confirmar.py`, `s30a_confirmar.py` ni del CSV
de días nuevos. El detector congelado S26a no se tocó.

## 1. Para geólogo

**La pregunta.** VOLCAT dibuja la pluma diaria de Nevados de Chillán anclada al cráter y la sigue hasta 9 a 15 km,
casi siempre hacia el SE. El anillo congelado del detector propio (4 a 40 km) coincide con VOLCAT en la hora y en el
rumbo, pero marca a 22 a 33 km, sobre la cordillera alta del SE, que sin pluma ya atrae su estadístico (S31c, S31d,
S31e). La pregunta de S31h: si se mira **sólo** el tramo de 4 a 15 km, con una regla hecha para los 8 a 10 píxeles que
caben en cada tajada de 30° y con cada píxel medido contra lo que él mismo vivió en oct-nov 2025, ¿el detector marca la
pluma donde VOLCAT la dibuja, más que un píxel cualquiera de la corona?

**La regla.** La firma buscada es la de siempre: la ceniza semitransparente baja la diferencia de brillo entre 11 y
12 µm (BTD) respecto de lo normal para ese lugar y esa hora. Cada píxel de la corona se pasó a su lugar dentro de su
propia distribución de 2025 a la misma hora (±90 min), en escala normal. Por tajada, la media de los 3 valores más bajos
(lo que una pluma de 2 a 4 km de ancho llena en 8 a 10 píxeles), y se dispara cuando la tajada más baja se aparta de la
mediana de las tajadas dos cuadros seguidos. El umbral quedó en el percentil 6 de 2025 (el tope que el criterio
permitía): con él la corona dispara en 2025 menos que el anillo congelado (2,2 % de los cuadros por día contra 4,0 %).

**Lo que salió.**

- **A la hora de VOLCAT casi no dispara.** De los 100 cuadros P de VOLCAT hasta el 24-11, la corona sólo pudo evaluar
  52, y disparó en 3, los tres el 08-11 entre las 20:10 y las 20:30 UTC. El 28-10 (13 cuadros evaluados) y el 14-11
  (21) dan cero. El anillo congelado alcanzaba 23 de 54.
- **Muchos cuadros de VOLCAT no se pueden mirar.** De los 48 no evaluados, 41 caen porque quedan menos de 5 píxeles
  con valor en 4 o más tajadas de la corona (borde de nube dinámica o pareo fallido). No es algo propio de la hora de la
  pluma: post hoc, los cuadros sin VOLCAT pierden lo mismo (§3). La corona entera rara vez está despejada, y las
  tajadas del SE, por donde va la pluma, son las que más se pierden.
- **El tramo no se puede juzgar.** Con 3 cuadros de un solo día, la regla da NO DECIDIBLE (pocos). Uno de los 3 tiene
  un píxel del disparo dentro de la huella anclada, en su rumbo.
- **Y la prueba no tenía poder para la posición.** El control positivo (VOLCAT un cuadro antes, restringido a la corona)
  cae en la huella 41 de 87 veces, pero un píxel cualquiera de la misma tajada de la corona caería el 42 % de las veces:
  p 0,013 con el nulo calibrado (0,020 con el uniforme), sobre el alfa de 0,01. Con píxeles de unos 2 por 3 km, la huella
  de VOLCAT dilatada un píxel (por la incertidumbre de georreferencia de H14) cubre casi la mitad de una tajada de 8 a 10
  píxeles. Dentro de 15 km, a 2 km de píxel, "dónde dentro de la tajada" no agrega nada a "hacia qué tajada". El rumbo
  sí se puede probar (el oráculo pasa R con p 0,0008), pero la corona no dispara a la hora de VOLCAT para probarlo.
- **En 2024, con el volcán tranquilo, dispara de más.** Fuera de muestra (GOES-16, oct-nov 2024, con la base y el umbral
  de 2025) dispara en el 6,3 % de los cuadros por día, contra 1,5 % del anillo congelado en los mismos días (diferencia
  +4,9 puntos, IC 1,8 a 8,4): NO AGUANTA. Y 78 de sus 108 disparos caen en una sola tajada, la de 120° a 150° (SE). En
  2025, el año de referencia, esa tajada no destacaba y el SE quedaba en lo que da el método solo (26 % contra 17 %,
  SIN SESGO SE). O sea, el flanco SE cercano tiene algo propio que cambia de un año a otro y que la calibración de un
  solo año no se lleva.
- **En 2026 dispara mucho sin VOLCAT.** 13 % de los cuadros N de 2026 (contra 2,2 % de falsa alarma en 2025): 166
  disparos en 19 días, 117 en cuadros N y sólo 1 en un P. De noche, casi todos hacia el SE (120° a 180°: 81 de 127). Puede
  ser la pluma diaria de noche, que VOLCAT no dibuja, o lo mismo que enciende el flanco SE en 2024; con lo medido no se
  separa.
- **La variante de sensibilidad (residuo crudo, sin escala propia) va igual:** 3 de 52, NO AGUANTA en 2024 (7,0 %),
  sesgo 2025 INTERMEDIO, tramo NO DECIDIBLE, y el oráculo tampoco pasa la posición (p 0,031).

**Lectura honesta.** La corona no sirve como detector: no dispara a la hora de la pluma de VOLCAT y sí dispara, hacia el
SE, en un año sin erupción. Esto calza con lo que vienen diciendo S17 (H22, H23), S19i y S31c: junto al cráter la pluma de
Chillán es chica u opaca para la firma 11 menos 12 µm en píxeles de 2 km, y lo que el IR ve cerca del volcán lo domina el
terreno y la nube orográfica. Lo nuevo es de método y vale más allá de esta corona: **con píxeles de 2 km no se puede
preguntar por la posición de la pluma dentro de los primeros 15 km**, porque la huella de VOLCAT (dilatada lo que exige
su georreferencia) ocupa media tajada; esa pregunta necesita resolución más fina (el canal visible C02 de 0,5 km, que mira
S31f) o la verdad de las cámaras del OVDAS.

## 2. Cifras del criterio

| Medida | T1, principal | Rc, sensibilidad |
|---|---|---|
| Comprobación de código (§7) | S del congelado sin un cuadro distinto (hasta 600 al azar de 2025 y 2026); la prueba de S31c reproducida igual con la misma semilla (`px_cerca` 6 de 23, p_G 0,9397, p_R 0,0012; `rumbo_lejos` 12 de 23, p_R 0,0068; oráculo 41 de 87); T1 de la corona igual a la de S31e (diferencia 0,0 en 40 cuadros): **válida** | |
| Percentil fijado en 2025 (§4) | **6,00** (tope de la grilla) | 6,00 |
| Falsa alarma 2025, media por día / global | 0,0222 / 0,0261 (70 disparos en 2.683 cuadros) | 0,0190 / 0,0265 (71) |
| (a) Falsa alarma 2024, media por día (43 días) | 0,0634 (global 0,0611); congelado 0,0148; dif +0,049 (IC 0,018 a 0,084): **NO AGUANTA** | 0,0697; dif +0,055 (IC 0,030 a 0,083): NO AGUANTA |
| (b) Sesgo 2025: disparos, días | 70, 16 | 71, 12 |
| (b) Cuota SE / E₁ / exceso (IC 95 %) | 0,257 / 0,170 / 0,087 (−0,063 a 0,303): **SIN SESGO SE** | 0,310 / 0,189 / 0,121 (−0,008 a 0,378): INTERMEDIO |
| (b) Réplica 2024 | 108 disparos en 18 días; 0,731 / 0,222 / 0,509 (0,382 a 0,647): SESGO SE | 120 en 27 días; 0,150 / 0,231 / −0,081: SIN SESGO SE (pero 84 en la tajada de 300° a 330°) |
| (c) Alcance en P de VOLCAT 2026 | **3 de 52** (IC por días 0 a 0,19), todos el 08-11; congelado 23 de 54 | 3 de 52 |
| (c) P no evaluados (de 100) | 48: 7 por la compuerta, 41 por tajadas inválidas | igual |
| (c) Tasa de disparo en N de 2026 (890) | 13,1 % | 9,3 % |
| (d) P con huella / días | 94 / 7 | 94 / 7 |
| (d) P evaluados (días) | 3 (08-11) | 3 (08-11) |
| (d) `px` | 1 de 3; p_Gc 0,98, p_R 0,25, p_D 0,25 | 1 de 3; p_Gc 1,0 |
| (d) `rumbo` | 1 de 3; p_R 0,25, p_D 0,30 | 1 de 3 |
| (d) Oráculo, `px` (87 P en 6 días) | 41; azar en la tajada 0,42; **p_Gc 0,0129**, p_G 0,0205, p_R 0,0003, p_D 0,0189 | 41; p_Gc 0,0312, p_R 0,0006 |
| (d) Oráculo, `rumbo` | 42; p_R 0,0008, p_D 0,0150 | 42; p_R 0,0008 |
| (d) Tramo (§8) | **NO DECIDIBLE (pocos)**; con más cuadros habría sido SIN PODER (el oráculo no pasa Gc) | NO DECIDIBLE (pocos) |
| **Titular** | **NO DECIDIBLE (pocos cuadros o días); falsa alarma 2024 NO AGUANTA; sesgo 2025 SIN SESGO SE** | NO DECIDIBLE; NO AGUANTA; INTERMEDIO |

Descriptivos (no deciden):

| | T1 | Rc |
|---|---|---|
| Píxeles del disparo en 2025: mediana (cuartiles), fracción a menos de 9,7 km | 11,2 km (8,2 a 13,1), 29 % | 11,0 km (6,9 a 12,1), 35 % |
| Tajadas de los disparos 2025 (0° a 330°, de a 30°) | 0, 5, 4, 17, 13, 4, 1, 6, 0, 11, 8, 1 | 0, 10, 2, 7, 17, 5, 0, 0, 0, 16, 14, 0 |
| Esperado por el método solo (E₁), 2025 | 7,1; 5,1; 9,0; 5,0; 4,0; 2,9; 5,0; 8,7; 4,8; 6,3; 6,5; 5,5 | |
| Tajadas de los disparos 2024 | 0, 0, 3, 2, **78**, 1, 0, 0, 0, 10, 14, 0 | 0, 0, 1, 0, 18, 0, 0, 0, 0, 17, **84**, 0 |
| Disparos 2026 hasta el 24-11 (P, N, sin clase, otra) | 166 (1, 117, 26, 22) en 19 días | 119 (2, 83, 23, 11) |
| Tajadas 2026, de noche / de día | noche 0, 0, 0, 1, 42, 39, 11, 9, 19, 3, 3, 0; día 0, 0, 0, 0, 7, 3, 17, 12, 0, 0, 0, 0 | |
| Poder sintético, firma 0,97 K (rayo SE / fuera) | 0,445 (0,27 / 0,51); congelado (S31e) 0,575 | 0,505 (0,37 / 0,55) |
| Poder sintético, firma 0,33 K | 0,155 | 0,115 |
| Píxeles que usaron el pozo de su tajada | 34 en 2025, 550 en 2026, 588 en 2024 | |

El método solo prefiere un poco las tajadas de 10 píxeles (en E₁ pesan 8,7 a 9,0 contra 2,9 a 5,5 las de 8), porque la
media de los 3 más bajos de 10 valores sale más honda que la de 8. Eso ya está en E₁, que es contra lo que se mide el
sesgo.

## 3. Post hoc (no decide; escrito después de ver la medida)

**Por qué se pierden tantos cuadros (pregunta 1 del post hoc).** De los cuadros de 2026 que pasan la compuerta, la
corona es evaluable en 52 de 93 cuadros P (56 %) y en 890 de 1.659 cuadros N (54 %); la mediana de píxeles sin valor es
23 % en P y 29 % en N. La pluma no esconde la corona más que cualquier otra hora: la corona de 4 a 15 km pierde píxeles
siempre, y sobre todo en el flanco SE (tajadas de 90° a 210° válidas en 45 a 62 % de los cuadros N, contra 66 a 80 % en
el resto). Es la zona por donde VOLCAT dibuja la pluma, así que el detector queda ciego justo ahí la mitad de las veces.

**Dónde dispara en 2024 (pregunta 2).** De sus 108 disparos, 92 son de noche (00:00 a 11:50 UTC) y 62 de esos caen en la
tajada de 120° a 150°. Cuatro noches llevan 65 de los 108: 11-11-2024 (24), 15-10-2024 (16), 14-10-2024 (14) y
05-11-2024 (11). En 2024 el volcán estaba en verde (REAV del 15-11-2024): son noches en que el flanco SE cercano se enfría
o se humedece distinto de lo que fue normal en 2025 (una inversión o aire frío encajonado en la quebrada son candidatos;
sin medir). Con el residuo crudo (Rc) pasa lo mismo, pero en la tajada de 300° a 330° (NW, 78 de noche).

**Dónde dispara en 2026 sin VOLCAT (pregunta 3).** De sus 117 disparos en cuadros N, 106 son de noche, 64 en las tajadas
de 120° a 180°; las noches del 08-11 (27), 05-11 (18), 25-10 (12), 22-11 (10) y 23-11 (8) llevan la mayoría. Es el mismo
patrón que en 2024 (de noche, al SE cercano, concentrado en pocas noches) en un año tranquilo, así que **estos disparos
nocturnos de 2026 no se pueden leer como pluma**: el flanco SE cercano los produce también sin erupción. La noche del
05-11, que S31e también encontró encendida hacia el valle y en la que Nicolás vio la pluma ir al E todo el día, aparece
de nuevo, pero con el antecedente de 2024 no sirve de prueba.

**Lo que esto le dice a la prueba del tramo.** Además de los pocos cuadros, el detector de la corona dispara de noche y
VOLCAT dibuja la pluma casi siempre de día (el oráculo tiene 82 de sus 87 cuadros entre las 12:00 y las 23:50 UTC): la corona y VOLCAT casi no se
cruzan en el reloj. Los únicos 3 cuadros alcanzados (08-11, 20:10 a 20:30 UTC) son de la tarde de un día con pluma larga
al SE.

## 4. Cómo se corrió

Tres corridas del mismo script; sólo la tercera llegó al final. Ninguna cifra cambió entre ellas.

1. **Corrida 1** (desde 04:23 UTC del 27-11, commit `8ca00ff`): el computador se reinició a las 09:34 hora de Chile y
   la cortó después de cargar los detectores ("blanco 2026 listo en 1442 s"), **antes** de la comprobación de código y
   antes de cualquier cifra de la corona. Registro: `D:\goes_notas\s31\s31h\medir_corrida1_cortada_reinicio.log`.
2. **Corrida 2** (12:36 UTC, el mismo commit): pasó la comprobación de código completa, calculó y escribió en el
   registro (a), (b) y (c) de T1, y se cayó en una línea que sólo **imprime** el tramo: la medida `rumbo` no tiene nulo de
   posición y el `print` lo pedía igual (`KeyError: 'G'`). El tramo "todo" ya estaba calculado pero no se alcanzó a
   imprimir ni a guardar. Registro: `D:\goes_notas\s31\s31h\medir_corrida2_cayo_en_print.log`.
3. **Corrida 3** (commit `6c4d32a`, que cambia sólo esa línea de impresión): completa, 1.082 s, sin caídas. Es la misma
   cuenta: mismo código de cálculo y mismas semillas; las líneas de la comprobación de código, la calibración, (a), (b)
   y (c) salieron idénticas, carácter por carácter, a las de la corrida 2 (comprobado con `diff`). Registro:
   `D:\goes_notas\s31\s31h\medir.log`.

El post hoc (`s31h_posthoc.py`) lee los cubos guardados y rearma la referencia de 2025 sólo para el umbral; no cambia
ninguna cifra del criterio. Lo usado en D: es menos de 100 MB; quedan unos 21 GB libres.

## 5. Lo que no puede decir

- Que la corona no vea la pluma: con 3 cuadros de un día el tramo es NO DECIDIBLE, no un "no". Lo que sí dice es que a la
  hora de VOLCAT casi no dispara, y que la prueba de posición dentro de 15 km no tenía poder ni con VOLCAT mismo.
- Qué enciende el flanco SE cercano en 2024 ni qué son los disparos nocturnos hacia el SE de 2026 (pluma de noche,
  terreno, nube orográfica o diferencia entre satélites): post hoc, sin medir.
- Nada de días posteriores al 24-11, ni de ceniza ni de altura. Nada de esto es confirmación.

## 6. Qué sigue (para la coordinadora y Nicolás)

1. **No adoptar la corona cercana IR como detector**, ni en T1 ni en Rc: no dispara a la hora de VOLCAT (3 de 52) y no
   aguanta la falsa alarma fuera de muestra (6,3 % en 2024).
2. **No volver a preguntar por la posición de la pluma dentro de 15 km con píxeles IR de 2 km.** El control positivo no
   pasa el nulo de posición: la pregunta está limitada por la resolución, no por la regla. Si se quiere el tramo cercano,
   es con el visible C02 de 0,5 km (S31f) o con las cámaras del OVDAS.
3. Lo del flanco SE cercano en 2024 (78 de 108 disparos en una tajada) es un aviso para cualquier detector que calibre
   con un solo año: lo que en 2025 era normal para un píxel cercano al volcán no lo es en 2024. Si alguna vez se recalibra
   algo cerca del cráter, con dos años de referencia.
