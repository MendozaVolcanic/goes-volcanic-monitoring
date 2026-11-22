# H19 (S17): el paso de objeto de VOLCAT inferido del caso de Fuego. Informe, 22-11-2026

**Veredicto contra el criterio escrito de antemano: reproduce en parte.** En la columna convectiva de Fuego
se encontró una regla simple que explica la probabilidad alta que VOLCAT publica, y esa regla se cumplió en
cuadros que no se usaron para elegirla. La regla deja de servir cuando la nube convectiva desaparece (desde
las 22:16 UTC) y no alcanza a nubes tenues. Nada de esto se aplicó a Chillán.

Criterio: `criterio_2026-11-22.md`, commit c62b60a (antes de medir). Reglas congeladas: `regla_congelada.md`,
commit c10abe7 (antes de abrir los cuadros de validación).

## 1. Para geólogo

**El fenómeno.** El 3 de junio de 2018 Fuego produjo una columna eruptiva que llegó a la tropopausa (16 km)
y se extendió como una nube espesa y fría (200 K). Vista desde el satélite, esa nube no tiene la firma
infrarroja clásica de la ceniza: es opaca, igual que una nube de tormenta. Aun así VOLCAT publica en ella
probabilidad de ceniza cercana a 1. La pregunta era cómo.

**Lo que se encontró, en palabras.**

1. VOLCAT primero reconoce la columna como una **nube convectiva volcánica**: un objeto de nube fría que
   crece más rápido de lo normal, a 6 km de un volcán con anomalía térmica. Lo reconoce una vez (17:16 UTC)
   y después lo sigue de cuadro en cuadro. Esa parte no usa ninguna firma de ceniza.
2. Dentro de esa nube convectiva, VOLCAT arma objetos de ceniza con píxeles que no pasarían ninguna prueba
   de ceniza por sí solos. Los acepta por dos razones que el propio log declara: porque se solapan con la
   nube convectiva del cuadro actual, o porque vienen siguiéndose desde el cuadro anterior. La tabla de
   probabilidad de objeto, que reprodujimos en H16, les da probabilidad casi cero y no interviene.
3. Dentro de esos objetos, la probabilidad publicada es alta en los píxeles que son a la vez **opacos y
   oscuros**: emisividad total a 11 µm de 0,90 o más y reflectancia visible (0,65 µm) entre 10 % y 50 %.
   Una nube de agua o hielo así de opaca es brillante (más de 50 %). Una nube opaca que además es oscura es
   una nube cargada de ceniza. Esa es la física que VOLCAT usa en la columna, y no es una firma infrarroja.
4. `ash_probability_subset` es la variable donde VOLCAT guarda ese resultado: vale casi 1 en los píxeles
   opacos y oscuros de un grupo y casi 0 en los demás. La probabilidad publicada es esa misma variable en
   el 96 % de los píxeles altos.
5. Cuando la nube convectiva deja de existir como tal (desde las 22:16), VOLCAT sigue publicando el grupo de
   ceniza por seguimiento entre cuadros. Ahí la probabilidad alta aparece en otra parte de la nube: píxeles
   menos opacos (emisividad cercana a 0,56) con razón β(12/11) menor que 1, que es la señal de ceniza en el
   infrarrojo. La regla de "opaco y oscuro" no explica esos píxeles.
6. El único evento de tipo pluma o bocanada (`ASHPLUMEPUFF`) del paquete es de otro volcán, San Cristóbal
   (Nicaragua), a las 23:31: 13 píxeles tenues (emisividad 0,25 a 0,28). Ahí VOLCAT publica probabilidad
   mediana 0,97 donde su probabilidad de píxel infrarroja tiene mediana 0,04. No había anomalía térmica en
   ese volcán. El log dice que el objeto se conservó por su patrón en el espacio y en el tiempo.

**Qué significa para Chillán, sin haberlo aplicado.** La regla que se pudo demostrar exige una nube opaca
(emisividad ≥ 0,90). La pluma de Chillán tiene emisividad mediana 0,16, así que esa regla no puede ser la que
actúa allá. Los dos casos de este paquete que sí tocan nubes tenues o semitransparentes (San Cristóbal y la
fase tardía de Fuego) muestran lo mismo: VOLCAT sube la probabilidad de los píxeles de un objeto que ya
seleccionó por su comportamiento en el tiempo. Son 13 y 118 píxeles. Alcanza para describirlo, no para
inferir la regla.

**Números principales (validación, 13 cuadros de 20:31 a 23:31 UTC).**

| Qué | Resultado |
|---|---|
| Píxeles de día sobre tierra con probabilidad publicada | 25.432, de ellos 2.260 con P ≥ 0,5 |
| Regla nula (tabla de píxel de día) | recupera 0 de 2.260 |
| Regla "opaco y oscuro dentro del grupo" | recupera 2.187 de 2.260 (96,8 %); precisión 98,1 % |
| La misma regla, sólo mientras hay nube convectiva (20:31 a 22:01) | 2.185 de 2.185; precisión 98,1 % |
| La misma regla, sin nube convectiva (22:16 a 23:31) | 2 de 75 |
| Placebo (mismos umbrales con datos del cuadro anterior) | sensibilidad 58,9 %, precisión 45,5 % |

## 2. Respuestas a las tres preguntas

### Pregunta 1. Qué es `ash_probability_subset` y cómo se calcula

- **CONFIRMADO: dónde tiene valor.** Sólo dentro de los grupos de alerta. En los 13 cuadros de elección y
  en los 13 de validación el conjunto de píxeles con valor coincide con el de la probabilidad publicada
  (Jaccard 1,00) y con la unión de los grupos de ceniza y de nube convectiva (Jaccard de 0,970 a 1,000).
- **CONFIRMADO, como regla empírica para grupos de nube convectiva: cuánto vale.** Casi 1 si el píxel es
  opaco y oscuro, casi 0 si no. Elección: 4.788 de 4.788 píxeles opacos y oscuros con subset ≥ 0,5, y 0 de
  6.406 de los demás (máximo 0,0015). Validación: subset predicho (1 o 0) queda a menos de 0,01 del valor
  real en el 99,97 % de 25.593 píxeles. El placebo da 90,4 %, bajo el umbral de 95 %.
- **CONFIRMADO: los umbrales son de VOLCAT.** No se ajustaron. 0,90 es el borde del último bin de emisividad
  de la tabla pública de píxel. 10 y 50 son los atributos `DARK_PIXEL_REF2_MIN` y `DARK_PIXEL_REF2_MAX` de
  esa misma tabla. Un árbol de decisión sin esa información encontró 0,90 y 50,0 por su cuenta.
- **SIN DATO: el cálculo que produce el valor.** La tabla pública de emisividad por reflectancia
  (`EMISS14_TOT_VREF_DAY`) no lo produce: con ella la probabilidad queda bajo 0,01 en esos píxeles. Tampoco se
  sabe cómo se calculan los valores bajos de subset: en elección, en los píxeles del grupo de ceniza que no
  son opacos y oscuros, subset coincide con la probabilidad IR en 46 % y con la SW_IR en 22 %.
- **SOSPECHA: el nombre.** Los objetos de `geocatASHOBJ` traen `Probability_Subset_Median`, una caja
  `Latitude_Minimum_Subset` y un conteo `Dark_Pixel_Count`. Es razonable que "subset" sea el subconjunto de
  píxeles oscuros del objeto. Ningún log lo dice.

Una advertencia que pide el criterio: decir "P = subset" es una identidad y no explica nada. Lo que explica
es la regla de opaco y oscuro, que usa sólo emisividad y reflectancia.

### Pregunta 2. Qué predice la probabilidad alta en un píxel sin firma de ceniza

- **CONFIRMADO por el log y por los datos: la pertenencia a un grupo de nube convectiva volcánica.** El log
  de cada cuadro con evento dice `Grouping objects associated with vcbs`, `Seeding groups based on overlap
  with vcb in current image` y `Seeding groups based on kd tracking` (24 cuadros). En elección los 48 objetos
  de ceniza seleccionados, de 5.770, son exactamente los que caen dentro del grupo de nube convectiva.
- **CONFIRMADO: la tabla de objeto no decide.** La probabilidad de objeto (`Feature_Prob`) de los objetos
  seleccionados tiene mediana 4·10⁻¹⁵ en elección y entre 3·10⁻¹⁹ y 2·10⁻¹⁷ en validación.
- **CONFIRMADO: dentro del grupo decide "opaco y oscuro"** mientras existe la nube convectiva (tabla de la
  sección 1).
- **CONFIRMADO por el log: después decide el seguimiento entre cuadros.** `Temporal selection criteria met
  for ash` aparece 342 veces. Los parámetros del criterio temporal anulan los filtros de emisividad y de
  ruido (`Minimum ash object count (temporal criteria): 0`, `Maximum ash object median tot emiss (temporal
  criteria): 1.01`).
- **NO REPRODUCE: nuestra regla de pertenencia.** "Objeto de ceniza que toca al objeto convectivo" acierta
  150 de 252 objetos (59,5 %) con precisión 96,8 %. Mientras hay nube convectiva acierta 149 de 152. Sin ella,
  1 de 100. El placebo (marca barajada entre objetos) da F1 de 0,08 de mediana y 0,14 de máximo, contra 0,74.
- **SOSPECHA (análisis posterior, no decide): en la fase tardía la probabilidad sube por un término
  aditivo.** En 118 píxeles de 22:46 a 23:31 la probabilidad publicada supera a subset. El salto en log-odds
  toma pocos valores repetidos (12,74; 16,37; 17,07; 18,27; 18,96), como si saliera de una tabla. Esos
  píxeles tienen emisividad mediana 0,56 contra 0,80 del resto, y β(12/11) mediana 0,87 contra 1,00.

### Pregunta 3. Pluma o bocanada, y anomalía térmica

- **CONFIRMADO: en este paquete hay un solo evento `ASHPLUMEPUFF`** (San Cristóbal, 23:31) y 26 cuadros con
  evento `VCB` en Fuego. Todo lo que sigue sobre pluma o bocanada sale de un caso.
- **CONFIRMADO por el log: el camino existe con parámetros propios.** `Maximum ash object median tot emiss
  (plume/puff criteria): 0.50`, `Minimum ash object count (plume/puff criteria): 1`, `Noisy ash object
  threshold (plume/puff criteria): 0.25`, `Non-uniform ash object threshold (plume/puff criteria): 0.75`,
  `Weak plume option for ash: 4`. Hay una búsqueda de plumas fuertes y otra de plumas débiles por volcán.
- **CONFIRMADO por el log: por qué se conservó el objeto de San Cristóbal.** `Feature FAILED bulk spatial
  contrast testing`, luego `Feature PASSED detailed spatial contrast testing` y `KEEPING plume with robust
  space and/or time pattern`, con `Time Trend Count: 13`, `Robust Time Trend Frac: 1.000`, `BTD Bullseye
  Count: 13`, `New Emission Count: 3`. El objeto tiene 13 píxeles.
- **CONFIRMADO: en ese objeto la probabilidad publicada no es la de píxel.** Publicada: mediana 0,97, 9 de 13
  píxeles con P ≥ 0,5. IR: mediana 0,04, 6 de 13. Subset: mediana 0,04. Tabla de día: máximo 0,09. La
  probabilidad de objeto es 0,038. Emisividad de 0,25 a 0,28; BTD 11 − 12 µm de +1,7 a +2,5 K; cenit solar 82°.
- **CONFIRMADO para este evento: no hubo anomalía térmica en el volcán.** No hay objeto caliente a menos de
  0,4° de San Cristóbal. Las anomalías térmicas de ese cuadro son de Fuego y Masaya. Por lo tanto la anomalía
  térmica no es condición necesaria del camino de pluma o bocanada en esta versión.
- **CONFIRMADO por la alerta: la anomalía térmica entra en el tipo y la prioridad del evento `VCB`.** Los dos
  nacimientos (17:16 y 21:31) dicen `Fuego(5.8 km) [Thermal Anomaly Present]`, `Type of Volcanic Event:
  Potential vCb and Recent Strong Thermal Anomaly`, `Identification Method: Cloud Growth Anomaly (CGA)`.
- **SIN DATO: si la anomalía térmica es condición para declarar la nube convectiva.** Hay dos nacimientos y
  los dos tienen anomalía térmica. No hay un caso sin ella para comparar.
- **SIN DATO: la regla que sube la probabilidad en el objeto de pluma.** Trece píxeles no alcanzan.

## 3. Veredicto por hipótesis

| Hipótesis | Umbral del criterio | Resultado en validación | Veredicto |
|---|---|---|---|
| H19-A, soporte | Jaccard ≥ 0,99 en cada cuadro | mínimo 0,970; 4 de 13 cuadros bajo 0,99 | no cumple el umbral; se cumple de forma aproximada |
| H19-B, valor de subset | ≥ 95 % a menos de 0,01 | 99,97 %; placebo 90,4 % | reproduce (nivel 1) |
| H19-C, probabilidad publicada | sensibilidad y precisión ≥ 90 % en total, y ≥ 80 % en 11 de 13 cuadros | 96,8 % y 98,1 % en total; 7 de los 9 cuadros con 20 o más píxeles altos | parcial: cumple el total, no cumple por cuadro |
| H19-D, objetos de ceniza | precisión y sensibilidad ≥ 90 % | 96,8 % y 59,5 % por objeto; 99,7 % y 73,1 % por píxel | no reproduce |
| H19-D, objeto convectivo | lo mismo | 8 de 10, con 10 predichos | SIN DATO (menos de 20 casos); el placebo de 4 cuadros da 7 de 10 |
| Regla nula | a vencer | 0 de 2.260 (tabla de día); 13 de 2.260 (tabla IR) | vencida |
| Alcance en emisividad < 0,3 | ≥ 30 píxeles altos y sensibilidad ≥ 90 % | 9 píxeles altos, 0 recuperados | SIN DATO, y la regla no puede alcanzarlos por construcción |

Notas sobre el veredicto:

- El criterio de H19-C por cuadro quedó mal escrito: pide 11 de 13 cuadros pero sólo cuenta los que tienen 20
  o más píxeles altos, y de esos hay 9. Con cualquiera de las dos lecturas (11 cuadros, o la misma proporción)
  el resultado es "no cumple". Los dos cuadros que fallan son 22:46 y 23:01, de la fase sin nube convectiva.
- El placebo de historia para el objeto convectivo casi iguala a la regla real. El criterio ya lo preveía: la
  nube casi no se mueve en una hora, así que esta prueba no demuestra que la regla dependa del orden temporal.
- La separación en "fase con nube convectiva" y "fase sin ella" se hizo después de ver la validación. Es un
  análisis posterior. No cambia el veredicto. Sirve para ubicar dónde falla la regla.
- En los 14 cuadros sin evento la regla de historia no selecciona nada, pero eso es trivial: no tiene criterio
  de nacimiento.
- Una aclaración que no estaba en el archivo de reglas congeladas y se decidió antes de correr la validación:
  cuando hay varios grupos de nube convectiva en el cuadro anterior, la regla de historia se aplica a cada uno.

## 4. Comprobación del instrumento

- Mi lector de HDF4 recuperó exactamente los conteos establecidos por otra vía en el PR 89: 25.432 píxeles de
  día sobre tierra con probabilidad publicada en validación, 2.260 con P ≥ 0,5, 0 de ellos con
  `ash_probability_SW_IR` ≥ 0,5 y 13 con `ash_probability_IR` ≥ 0,5.
- Los grupos cambian de cuadro a cuadro: el grupo de nube convectiva va de 7 píxeles (17:16) a 3.683 (22:01).
- La regla nula corre con el mismo código que la regla candidata y da 0.

## 5. Evidencia por conclusión y cómo podría estar equivocada

**"Opaco y oscuro dentro del grupo" explica la probabilidad alta en la columna.**
Evidencia: `resultados/eleccion_explora3.txt`, `eleccion_explora5.txt`, `validacion.txt`.
Podría estar equivocada así: (a) emisividad y reflectancia podrían ser sólo sustitutos de la variable real;
en la columna, temperatura de brillo, altura y emisividad van juntas, y el árbol eligió primero la
temperatura a 11 µm (207,6 K). (b) Sólo se probó dentro de grupos de un mismo evento, de día, con cenit solar
bajo; no se sabe qué hace VOLCAT de noche, donde no hay reflectancia. (c) Los cuadros de validación son la
continuación de los de elección sobre la misma nube; no es un caso independiente.

**La pertenencia viene de la nube convectiva y del seguimiento.**
Evidencia: líneas de log citadas, `resultados/eleccion_explora8.txt`, `validacion.txt`, `posthoc.json`.
Podría estar equivocada así: nuestra regla de contacto es una aproximación de lo que el log llama solape y
seguimiento k-d; falla en la fase tardía, de modo que la parte de seguimiento está leída del log y no
reproducida.

**En la fase tardía y en San Cristóbal la probabilidad sube sobre la de píxel.**
Evidencia: `resultados/posthoc.json`, `posthoc2.txt`, `posthoc3.txt`.
Podría estar equivocada así: son análisis posteriores, sobre 118 y 13 píxeles, de un objeto por cuadro. Que
los saltos de log-odds se repitan sugiere una tabla, pero no se identificó cuál. La asociación con β(12/11)
menor que 1 puede ser de esa nube en particular.

**La anomalía térmica no es necesaria para pluma o bocanada.**
Evidencia: alerta y log de 23:31; ningún objeto caliente cerca de San Cristóbal en `geocatHOTOBJ`.
Podría estar equivocada así: es un evento, clasificado `Old Volcanic Feature` con índice de historia 15, es
decir, VOLCAT ya traía ese rasgo en su historial. No se revisó cómo entró al historial.

## 6. Lo que no se pudo determinar

1. Qué cálculo produce el valor casi 1 de subset en un píxel opaco y oscuro.
2. Por qué en 12 % de los píxeles opacos y oscuros la probabilidad publicada queda bajo subset (en elección,
   569 de 4.773 píxeles; en 9 % queda bajo 0,5; tienen β(12/11) más bajo).
3. La regla que sube la probabilidad en objetos seleccionados por historia o por pluma.
4. El criterio de nacimiento de la nube convectiva y el papel exacto de la anomalía térmica en él.
5. Qué significa cada código de `Ash_Object_Mask`. Se observó que el código 5 casi sólo aparece dentro del
   grupo de nube convectiva y el código 2 en el objeto de pluma de San Cristóbal.
6. El contenido de `history/volcat_history.hdf` (963 MB) no se abrió: los campos de seguimiento por píxel y
   los logs alcanzaron para lo que se probó.

## 7. Seguimientos sugeridos (no hechos aquí)

- Los archivos `.pkl` de la carpeta `events` del paquete no se abrieron y conviene no abrirlos nunca con
  `pickle`: deserializarlos ejecuta código.
- El informe del PR 89 dice que la probabilidad publicada es igual a subset en el 77 % de los píxeles altos.
  Con tolerancia 0,01 aquí da 2.180 de 2.260 (96,5 %). La diferencia es de tolerancia o de población. Conviene
  corregir esa cifra o declarar su tolerancia.
- Para Chillán, la prueba que sigue de este resultado es otra y necesita su propio criterio: comprobar si los
  objetos que VOLCAT publica allá muestran el mismo salto de probabilidad sobre la de píxel, usando los
  NetCDF de evento de Chillán que ya están en disco.
- Los paquetes de prueba de Etna y Mauna Loa del mismo release podrían traer más eventos `ASHPLUMEPUFF` con
  salidas intermedias. Con más de un evento se podría inferir la regla de pluma.

## 8. Archivos

Todo bajo `docs/own_volcat/h19_objeto_fuego/`. Ningún archivo de SSEC está en el repositorio.

- `criterio_2026-11-22.md`: criterio previo (commit c62b60a).
- `regla_congelada.md`: reglas elegidas con el bloque de elección (commit c10abe7).
- `scripts/h19_io.py`, `h19_inventario.py`, `h19_estructura.py`, `h19_explora1.py`, `h19_explora2.py`: lectura
  de HDF4 (se corren con `D:\goes_notas\busqueda_2026-11-20\venv_hdf4\Scripts\python.exe -I`).
- `scripts/h19_extraer.py`: pasa los 40 cuadros a npz en `D:\goes_notas\s17\h19\npz\` (108 MB, fuera del repo).
- `scripts/h19_explora3.py` a `h19_explora9.py`: exploración, sólo bloque de elección (se niegan a abrir
  validación).
- `scripts/h19_reglas.py`, `h19_objetos.py`, `h19_vref.py`, `h19_comun.py`: reglas y utilidades.
- `scripts/h19_validar.py`: validación, placebos, regla nula y tramos de emisividad.
- `scripts/h19_posthoc.py`, `h19_posthoc2.py`, `h19_posthoc3.py`: análisis posteriores, rotulados.
- `resultados/`: salidas de texto y JSON de todo lo anterior.
