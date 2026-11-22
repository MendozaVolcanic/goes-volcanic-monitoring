# H20a (S17): qué significan los campos por píxel de los archivos de evento de VOLCAT, y cómo se lee Chillán con eso. Informe, 22-11-2026

Criterio escrito antes de medir: `criterio_2026-11-22.md`, commit `cb03f34`. Reglas congeladas con la mitad
de los cuadros antes de abrir la otra mitad: `regla_congelada.md`, commit `0dcde6a`. Todo lo decidido
después de ver datos está rotulado "post hoc" en la sección 6.

Todos los archivos nombrados sin ruta completa están en `docs/own_volcat/h20a_campos_evento/` del
repositorio. Ningún archivo de SSEC está en el repositorio.

## 1. Para geólogo

**El problema.** De Nevados de Chillán sólo tenemos los archivos de evento que VOLCAT publica: una grilla
chica por cuadro con la huella del objeto y unos pocos campos por píxel. Dos de esos campos se llaman
"fuerza de la firma espectral de ceniza" (uno con todos los canales, otro sólo con infrarrojo térmico). H14
los leyó suponiendo que 1 significa firma fuerte, pero no sabía qué eran. El atributo del propio archivo
no ayuda: dice "indicador de ambigüedad espectral", que se puede leer al revés.

**Lo que se hizo.** El caso de prueba de Fuego (03-06-2018) trae archivos de evento con el mismo formato
que los de Chillán y, al lado, todas las salidas intermedias de VOLCAT para la misma grilla. Se puso cada
campo del archivo de evento encima de las salidas intermedias, píxel por píxel, para ver con cuál calza.

**Lo que resultó, en palabras.**

1. **La "fuerza de firma" total es la probabilidad de ceniza que VOLCAT publica.** No es un indicador
   aparte: es el mismo número, idéntico hasta el último decimal, en los 36.774 píxeles de Fuego y en los 13
   de San Cristóbal. La escala va en el sentido que H14 supuso: 1 es probabilidad alta de ceniza.
2. **La "fuerza de firma de onda larga" es la probabilidad de píxel infrarroja.** Es la salida de las
   tablas de probabilidad de píxel que el proyecto ya reproduce, antes de cualquier paso de objeto. También
   calza exacto.
3. **La huella del evento no es "donde la probabilidad es alta".** La huella es el grupo de alerta completo
   (el objeto que VOLCAT decidió seguir). En la columna de Fuego, el 82 % de los píxeles de la huella tiene
   probabilidad publicada menor que 0,05. Que un píxel esté en la huella dice que pertenece al objeto, no
   que tenga señal.
4. **"Tiempo de residencia" y "distancia recorrida" no miden el viaje de la ceniza.** Un píxel con tiempo
   0 es un píxel sin enlace con el cuadro anterior, y ahí la distancia es simplemente la distancia al
   volcán. Para los demás píxeles los valores se acumulan por los enlaces del seguimiento entre cuadros. En
   Chillán (14-11, 22:00 UTC) dan 112 a 193 km de "distancia recorrida" para un objeto que está a 12 km o
   menos del cráter, y tiempos mayores que la edad del evento. No sirven como distancia ni como edad de la
   pluma.

**Qué dice eso de Chillán.** Leídos con ese significado, los 60 archivos de Chillán dicen tres cosas:

- En el infrarrojo, VOLCAT mismo le da a esos píxeles probabilidad casi cero: 99,3 % de los 767 píxeles
  bajo 0,05 y ninguno sobre 0,5. Esto coincide con lo que dan nuestras tablas reproducidas. No es que
  nosotros no veamos algo que VOLCAT sí ve en el píxel: VOLCAT tampoco lo ve en el píxel.
- La probabilidad que VOLCAT publica también es baja en la mayor parte: 78 % de los 769 píxeles bajo 0,05.
  Sube sobre 0,5 en 94 píxeles (12 %), casi todos del evento largo del 14-11 y sobre todo con el sol bajo
  (72 de los 94 con cenit solar entre 70° y 85°). De noche no sube nunca.
- De noche la probabilidad publicada es exactamente igual a la infrarroja (112 de 127 píxeles idénticos
  bit a bit; de día, 0 de 640). Es lo que se espera si de día VOLCAT agrega canales solares y de noche no.

**Comparación con San Cristóbal**, el único evento de pluma o bocanada del paquete de Fuego. Chillán no se
le parece en lo que importa. En San Cristóbal la mitad de los píxeles sí tiene señal infrarroja (6 de 13
con probabilidad infrarroja de 0,5 o más; la diferencia de temperatura de brillo de 11 menos 12 µm está
2,3 K bajo la de píxeles vecinos de igual temperatura) y VOLCAT sube la probabilidad publicada del objeto
a una mediana de 0,97. En Chillán no hay señal infrarroja en ningún píxel (la misma diferencia está sólo
0,4 a 0,8 K bajo el control) y la probabilidad publicada se queda baja en 55 de los 60 cuadros. Chillán se
parece más al **nacimiento del evento de nube convectiva de Fuego**: objeto de pocos píxeles pegado al
cráter, probabilidad publicada cero en todos sus píxeles y calor detectado en el volcán.

**Conclusión práctica.** En Chillán VOLCAT publica objetos, no probabilidades altas. Lo que hay que
explicar ya no es "por qué VOLCAT da probabilidad alta donde nosotros no", porque no la da: es "por qué
VOLCAT abre y mantiene un objeto de alerta en píxeles a los que él mismo asigna probabilidad casi cero".
Esa decisión está en el paso de objeto y de seguimiento, y los archivos de evento no traen las variables
que la toman.

**Números principales.**

| Qué | Fuego (columna, 26 cuadros) | San Cristóbal (1 cuadro) | Chillán (60 cuadros) |
|---|---|---|---|
| Píxeles de huella con valor | 36.774 | 13 | 769 |
| Probabilidad publicada de 0,5 o más | 18,0 % | 9 de 13 | 12,2 % (94) |
| Probabilidad publicada menor que 0,05 | 81,8 % | 1 de 13 | 78,3 % (602) |
| Probabilidad infrarroja de 0,5 o más | 16 píxeles (0,04 %) | 6 de 13 | 0 de 767 |
| Probabilidad infrarroja máxima | 0,984 | 0,934 | 0,417 |
| Publicada mayor que infrarroja en más de 0,05 | 6.679 | 11 de 13 | 167 |

## 2. Veredicto contra el criterio

| Regla | Elección (Fuego 17:16 a 20:16) | Validación (Fuego 20:31 a 23:31 y San Cristóbal) | Veredicto |
|---|---|---|---|
| R1. `ash_spectral_signature_strength` = probabilidad publicada `ash_probability` | 100 % de 11.194 a menos de 0,01; diferencia máxima 0; soporte Jaccard 1,000; nulos 88,8 % y 70,9 % | 100 % de 25.580; diferencia máxima 0; Jaccard 1,000; nulo corrido 97,0 %, nulo previo 87,6 %. San Cristóbal 13 de 13, nulo 42,9 % | **CONFIRMADO**, con una salvedad: el nulo corrido de validación (97,0 %) supera el umbral escrito de 90 %. Ver abajo |
| R2. `..._lwir_only` = probabilidad de píxel infrarroja `ash_probability_IR` | 100 % de 11.162; diferencia máxima 0; nulos 99,3 % y 98,7 % | 100 % de 25.419; diferencia máxima 0; nulos 99,4 % y 98,8 %. San Cristóbal 13 de 13, nulo 25,0 % | **CONFIRMADO por identidad exacta y nulo post hoc. Por la letra del criterio previo sería SOSPECHA** (el nulo escrito no discrimina en Fuego y San Cristóbal tiene 13 píxeles) |
| R3. Huella = grupo de alerta | Jaccard 1,000 con el grupo de nube convectiva en 13 de 13 cuadros | Jaccard 1,000 con la unión de grupo de ceniza y grupo convectivo en 13 de 13; San Cristóbal: 13 de 13 en el grupo de ceniza | Identidad **por construcción**. La regla congelada decía "grupo convectivo"; lo correcto es la unión de los dos grupos |
| R4. `residence_time` múltiplo del intervalo entre imágenes y acotado por la edad del rasgo | Paso 0,25 h; 100 % menor o igual a la edad; máximo igual a la edad en 13 de 13 cuadros | Paso 0,25 h; 99,6 % menor o igual a la edad (umbral 99 %); máximo igual a la edad en 5 de 13 cuadros (umbral: todos) | **Parcial.** CONFIRMADO: cuantizado por el intervalo entre imágenes. SOSPECHA: acotado por la edad (falla en Chillán). No cumple: máximo igual a la edad |
| R5. `distance_traveled` = distancia al volcán con paralaje corregido cuando el tiempo es 0 | 39 de 39 | 263 de 263 en Fuego, 13 de 13 en San Cristóbal | **CONFIRMADO** para tiempo 0. La segunda mitad (mayor o igual que la distancia al volcán en los demás) **no cumple**: 51,9 % en validación |
| R6. El archivo de evento lleva el salto de log-odds de H19 (C11) | Sin píxeles con salto mayor que 5 | 0 de 115 píxeles con salto del evento a menos de 0,05 del salto del L2; San Cristóbal 0 de 6 | **No cumple.** El archivo no trae `ash_probability_subset`, y la probabilidad infrarroja no la reemplaza |
| Candidatos "1 menos probabilidad" (lectura "ambigüedad") | 0 % | no medidos de nuevo | Descartados |

**La salvedad de R1 y R2, dicha completa.** El punto 3 del criterio pedía que el acuerdo cayera a 90 % o
menos al correr el campo un píxel o al usar el cuadro anterior. En una nube donde la probabilidad vale casi
0 o casi 1 en zonas grandes, correr un píxel no cambia casi nada, y ese nulo no puede fallar aunque la
identidad sea cierta. El umbral estaba mal pensado para campos planos. Lo que sostiene el veredicto:

- La identidad es exacta, no aproximada: la diferencia máxima es 0 en precisión simple, en todos los
  píxeles de los dos bloques.
- Nulo informativo (post hoc, decidido antes de abrir la validación): en los píxeles donde el candidato
  cambió más de 0,05 respecto del cuadro anterior, el campo del evento coincide con el valor actual en
  100 % y con el anterior en 0 %. Para R1 son 2.333 píxeles en elección y 2.452 en validación. Para R2 son
  119 y 194.
- Píxeles discordantes entre candidatos: entre publicada y `subset`, 513, 123 y 12 píxeles (elección,
  validación, San Cristóbal), todos del lado de la publicada. Entre infrarroja y SW_IR, 58, 67 y 6
  píxeles, todos del lado de la infrarroja.
- San Cristóbal, donde los campos sí varían de píxel a píxel, cumple el nulo escrito (42,9 % y 25,0 %),
  pero con 13 píxeles.

R2 descansa en menos píxeles informativos que R1: sólo 22 píxeles tienen probabilidad infrarroja de 0,5 o
más (6 en elección, 10 en validación, 6 en San Cristóbal) y 222 la tienen sobre 0,01.

**Expectativa escrita de antemano:** S = P y SL = P_IR. Acertó en las dos.

## 3. Las tres tareas

### Tarea 1. Qué es cada campo por píxel

- **`ash_spectral_signature_strength`: CONFIRMADO, es `ash_probability` del L2** (la probabilidad
  publicada, ya pasada por el paso de objeto). También en el archivo de gránulo 601 x 601: 100 % de 11.194
  y de 25.593 píxeles, soporte idéntico.
- **`ash_spectral_signature_strength_lwir_only`: CONFIRMADO con la salvedad de arriba, es
  `ash_probability_IR`.** Sólo tiene valor dentro de la huella.
- **`event_idx`: por construcción, el grupo de alerta** (grupo de ceniza, grupo de nube convectiva o su
  unión). Un archivo puede traer hasta 3 eventos (21:31 a 22:46 en Fuego).
- **`residence_time`: SOSPECHA.** Tiempo acumulado por los enlaces del seguimiento, en pasos del intervalo
  entre imágenes (0,25 h en Fuego, 0,1667 h en Chillán). Vale 0 en un píxel sin enlace con el cuadro
  anterior. No es edad de la ceniza: en el evento largo de Chillán supera la edad del evento en 649 de 728
  píxeles, hasta 1,6 veces.
- **`distance_traveled`: CONFIRMADO sólo para tiempo 0** (distancia al volcán con la posición corregida
  por paralaje: 302 de 302 en Fuego, 13 de 13 en San Cristóbal, 17 de 17 en Chillán). Para tiempo mayor
  que 0, la fórmula de acumulación es **SIN DATO**. No es la distancia al volcán ni el desplazamiento del
  seguimiento (`displacement_distance`, 0,1 % o menos).
- **`ash_mass_loading`: igual al L2** (100 %, nulo 1,0 a 1,3 %). **`ash_cloud_height`: la altura del L2
  truncada a 0,01 km** (100 % entre menos 0,01 y 0). **`effective_radius_of_ash`: no coincide** con
  `ash_effective_radius` (8 a 18 %); no se investigó.
- **Campo que lleve el salto de log-odds: no existe en el archivo de evento.** El salto de H19 es entre la
  probabilidad publicada y `ash_probability_subset`. El archivo de evento no trae `subset`. La diferencia
  de log-odds entre S y SL es otra cosa (publicada contra infrarroja) y no reproduce el salto en ninguno de
  los 115 píxeles de la fase tardía ni en los 6 de San Cristóbal. Dato nuevo para H19: en San Cristóbal el
  salto del L2 toma dos valores, 4,56 (7 píxeles) y 8,60 (6 píxeles); en la elección de Fuego vale 0,11 en
  los 805 píxeles donde la publicada supera a `subset`.
- **Campo por píxel que marque por qué se seleccionó el objeto: SIN DATO.** Ninguno de los 23 campos por
  píxel lo trae.

### Tarea 2. Chillán contra San Cristóbal

La lectura de Chillán supone que v3r4 define los campos como v3p9. Eso es **SOSPECHA** bien apoyada, no
confirmada (sección 4).

| | San Cristóbal `ASHPLUMEPUFF` 23:31 | Chillán `VCB` 13-11 | Chillán `ASHPLUMEPUFF` 14-11 12:40 | Chillán `ASHPLUMEPUFF` 14-11 16:30 | Chillán `ASHPLUMEPUFF` 18-11 |
|---|---|---|---|---|---|
| Cuadros | 1 | 11 | 7 | 41 | 1 |
| Píxeles por cuadro | 13 | 1 a 5 | 1 a 6 | 3 a 67 | 4 |
| Primer cuadro: distancia al volcán | 17,7 a 28,5 km | 1,2 a 6,2 km | 8,5 a 13,4 km | 2,8 a 6,2 km | 12,5 a 17,8 km |
| Primer cuadro: edad y tiempo de residencia | 0 y 0 | 0 y 0 | 0 y 0 | 0 y 0 | 0 y 0 |
| Probabilidad infrarroja: máxima; píxeles de 0,5 o más | 0,934; 6 de 13 | 0,000; 0 de 15 | 0,001; 0 de 22 | 0,417; 0 de 726 | 0,002; 0 de 4 |
| Probabilidad publicada: máxima; píxeles de 0,5 o más | 1,000; 9 de 13 | 0,051; 0 de 15 | 0,046; 0 de 22 | 1,000; 93 de 728 | 0,665; 1 de 4 |
| BT11 menos BT12, huella menos control de igual BT11 | menos 2,32 K | menos 0,39 K | menos 0,76 K | menos 0,41 K | menos 0,64 K |
| Calor declarado en el volcán | no | sí (0 y 10 MW, mismo día) | sí | no (campo vacío) | sí |
| Qa: mediana infrarroja menor que 0,5 | sí | 11 de 11 cuadros | 7 de 7 | 41 de 41 | 1 de 1 |
| Qb: probabilidad publicada subida | sí | 1 de 11 cuadros | 2 de 7 | 2 de 41 | 0 de 1 |

- **CONFIRMADO como lectura de los archivos (condicionada a la transferencia): Chillán publica
  probabilidad baja.** Infrarroja: 762 de 767 píxeles bajo 0,05, ninguno de 0,5 o más. Publicada: 602 de
  769 bajo 0,05, 94 de 0,5 o más.
- **SOSPECHA: Chillán difiere de San Cristóbal.** Por la regla del criterio (mismas respuestas en Qa y Qb
  en la mayoría de los cuadros) los cuatro eventos de Chillán difieren: Qa igual, Qb distinta (subida en 5
  de 60 cuadros). Difiere además en que San Cristóbal sí tiene señal infrarroja en la mitad de sus
  píxeles. Es una comparación contra un solo evento de referencia, de 13 píxeles.
- **SOSPECHA: se parecen en cómo nacen.** Los cinco eventos nacen como objeto chico con edad 0 y todos
  sus píxeles con tiempo 0 (ninguno enlazado al cuadro anterior). Los archivos no dicen por qué criterio.
- **SOSPECHA: el `VCB` de Chillán se parece al nacimiento del `VCB` de Fuego.** Fuego 17:16: 7 píxeles a
  5,9 a 13,2 km, probabilidad publicada máxima 0,000, calor declarado. Chillán 13-11 19:00: 5 píxeles a
  1,2 a 6,2 km, probabilidad publicada máxima 0,0004, calor declarado.
- **CONFIRMADO en Fuego: estar en la huella no implica probabilidad alta.** 30.086 de 36.774 píxeles de la
  huella de Fuego tienen probabilidad publicada menor que 0,05.
- Donde Chillán sí tiene probabilidad publicada de 0,5 o más (92 píxeles de día), la infrarroja de esos
  píxeles tiene mediana 0,0012 y la diferencia de log-odds va de 6 a 21. Algo la sube. Los archivos de
  evento no permiten decir si es la tabla de píxel con canal solar o un término del paso de objeto.
  **SIN DATO.** La diferencia de log-odds en Chillán toma 467 valores distintos en 638 píxeles y no cae en
  ninguno de los saltos vistos en el L2 de Fuego; como es contra la infrarroja y no contra `subset`, eso no
  descarta el salto de H19.

### Tarea 3. Lo que sigue sin saberse

1. Si v3r4 define S y SL igual que v3p9. No hay L2 de Chillán para probarlo de frente.
2. Qué regla abre y mantiene un objeto en píxeles con probabilidad casi cero. Es el paso de objeto y de
   seguimiento (H19 leyó en los logs de Fuego los criterios temporales y de pluma). Los archivos de evento
   no traen esas variables.
3. Qué sube la probabilidad publicada de Chillán con el sol bajo: tabla de píxel con canal solar o término
   de objeto.
4. Si el salto de log-odds de H19 actúa en Chillán. No se puede ver sin `subset`.
5. La fórmula de acumulación de `distance_traveled` y `residence_time`, y por qué en Chillán el tiempo
   supera la edad del evento.
6. Qué es `effective_radius_of_ash` del evento respecto del L2.
7. Nada de esto se calibró de noche: Fuego no tiene cuadros de evento nocturnos.

## 4. ¿Se puede leer Chillán (v3r4) con la calibración de Fuego (v3p9)?

No hay prueba directa. Hay cinco comprobaciones indirectas, y las cinco salen compatibles:

1. **Esquema.** Las 21 variables que usa este análisis tienen el mismo tipo, dimensiones, `long_name` y
   unidades en los dos archivos (`resultados/esquema.json`). Fuego declara `VOLCAT v3.9.16`, sitio NCCF,
   ambiente `dev`. Chillán no trae atributo de versión; el nombre del archivo dice `v3r4`, sitio UW-SSEC,
   `Experimental`.
2. **Rango y soporte.** En Chillán S y SL están entre 0 y 1 en los 769 píxeles y no tienen valor fuera de
   la huella, igual que en Fuego.
3. **De noche S es igual a SL.** Obligación escrita en el criterio antes de medir. En los 4 cuadros de
   Chillán con cenit solar de 85° o más, 112 de 127 píxeles tienen S y SL idénticos bit a bit. De día, 0
   de 640. Esto es lo que predice "S es la probabilidad final y SL la infrarroja" y no lo predice una
   lectura arbitraria. Es la comprobación más fuerte de las cinco.
4. **Cuantización del tiempo.** En Chillán `residence_time` va en pasos de 0,1667 h, el intervalo entre
   imágenes de GOES-19, como en Fuego va en pasos de 0,25 h. Y los 17 píxeles con tiempo 0 tienen la
   distancia igual a la distancia al volcán con paralaje corregido.
5. **PNG del sitio (PR 85), fuente independiente de la misma versión.** En 41 cuadros, la fracción de la
   huella con S de 0,2 o más y la fracción con probabilidad de 20 % o más decodificada del PNG
   `Ash_Probability` tienen correlación de rangos de 0,54 (posición nominal) y 0,66 (desfasada un píxel).
   El PNG nunca muestra probabilidad alta en un cuadro donde el archivo de evento no la tiene (0 casos),
   pero el archivo de evento la tiene en 15 a 19 cuadros donde el PNG decodificado no la muestra. La
   concordancia de "hay o no hay" es de 54 a 68 %, bajo el 80 % que me había puesto. Compatible en signo,
   no concluyente. Lo más probable es que el PNG decodificado pierda píxeles (desfase de un píxel y bordes
   mezclados, ya descritos en H14 y PR 85), pero no lo comprobé.

Veredicto de la transferencia: **SOSPECHA** (fuerte por el punto 3).

## 5. Evidencia por conclusión y cómo podría estar equivocada

**S es la probabilidad publicada.**
Evidencia: `resultados/eleccion_medir.json`, `validacion_medir.json`, `eleccion_explora.txt`,
`validacion_explora_fuego.txt`, `validacion_explora_san_cristobal.txt`.
Podría estar equivocada así: (a) en otra versión el campo podría calcularse distinto; Fuego no lo dice.
(b) De noche no hay calibración. (c) No hay otra forma razonable de que dos campos en precisión simple
coincidan bit a bit en 36.787 píxeles, de los cuales 4.785 cambiaron de valor entre cuadros, así que no veo
un modo realista de error dentro de v3p9.

**SL es la probabilidad de píxel infrarroja.**
Evidencia: los mismos archivos.
Podría estar equivocada así: (a) descansa en 222 píxeles con valor sobre 0,01 y 22 con valor de 0,5 o más;
en el resto ambos campos valen casi 0 y cualquier candidato casi nulo calzaría a 0,01 (por eso `Feature_Prob`
por objeto da 99,7 % en elección). La identidad exacta en esos 222 píxeles y los 131 discordantes contra
SW_IR son los que deciden. (b) Lo mismo de versión y de noche.

**La huella es el grupo, no un umbral de probabilidad.**
Evidencia: Jaccard 1,000 en 26 de 26 cuadros de Fuego y en San Cristóbal; S menor que 0,05 en 81,8 % de la
huella de Fuego (`resultados/perfil_por_evento.json`).
Podría estar equivocada así: es una identidad por construcción y no explica cómo se arma el grupo.

**Chillán publica probabilidad baja y no se parece a San Cristóbal.**
Evidencia: `resultados/perfil_por_cuadro.csv`, `perfil_por_evento.json`, `sza_S_SL.json`,
`saltos_chillan.txt`. Los totales calzan con H14 (12,2 % y 78,3 % para S; 99,35 % para SL).
Podría estar equivocada así: (a) si v3r4 definiera S o SL de otro modo, toda la lectura cae. (b) San
Cristóbal es un evento de 13 píxeles con cenit solar de 82°; no es una muestra de eventos de pluma. Dos
de los cuatro eventos de Chillán son de 1 a 6 píxeles. (c) El control emparejado por BT11 usa pocos
píxeles por cuadro (los de la huella) y en la cumbre nevada de Chillán un píxel de igual temperatura puede
ser otra superficie.

**Los campos de trayectoria no miden el viaje de la ceniza.**
Evidencia: sección 5b de las tres salidas `*_explora*.txt`; `perfil_por_cuadro.csv` (Chillán 14-11 22:00:
objeto a 1,1 a 12,0 km del cráter con `distance_traveled` de 112 a 193 km y tiempo de 6,7 a 8,8 h con el
evento de 5,5 h de edad).
Podría estar equivocada así: no identifiqué la fórmula. Puede que el valor sea correcto para otra
definición (por ejemplo viento del modelo por tiempo). Lo confirmado es sólo el caso de tiempo 0.

## 6. Comprobación del instrumento, desviaciones y ajustes post hoc

**Alineación (antes de comparar nada).** Los 26 recortes de evento de Fuego, el de San Cristóbal y los 40
archivos de gránulo calzan con la grilla del L2 con diferencia de latitud y de longitud igual a 0
(`resultados/alineacion.csv`). La ventana del recorte es `x_image_feature_region_bounds` e
`y_image_feature_region_bounds` menos 1600; `x_image_processing_bounds` es la grilla entera (1600 a 2200)
y no sirve para ubicar el recorte.

**Control positivo.** La temperatura de brillo de 11 µm del evento coincide con la del canal 14 del L1 en
100 % de los píxeles (n mínimo 41.412 por cuadro) y, corrida un píxel, en 1,6 % o menos. La lectura no
está muerta ni corrida.

**Lectura contra H19 y H14.** San Cristóbal da publicada mediana 0,9706 y 9 de 13 de 0,5 o más; infrarroja
mediana 0,0428 y 6 de 13: los mismos números de H19 por otra vía. Chillán da los totales de H14.

Ajustes post hoc, en orden:

1. Antes de abrir validación (en `regla_congelada.md`): nulo informativo; forma de informar el soporte de
   SL; tolerancia de altura corregida de redondeo a truncamiento. Mi tolerancia original hizo que el control
   de altura diera 48 %: error mío, no de la lectura.
2. Después de abrir validación: la edad del rasgo se tomaba del evento 0 para todos los píxeles de un
   archivo; con varios eventos por archivo eso estaba mal. Corregido a edad por evento. R4 pasó de 87,6 % a
   99,6 % en "tiempo menor o igual a la edad". No cambia R1 ni R2.
3. Después de ver el perfil de Chillán: comparación con el PNG de PR 85 (el umbral de 80 % y de 0,5 lo
   escribí en el script antes de calcular); tabla de S contra SL por cenit solar (`h20a_sza.py`); valores
   del salto en Chillán (`h20a_saltos_chillan.py`). La igualdad nocturna sí estaba en el criterio.
4. La regla R3 congelada decía "grupo convectivo" para `VCB`. En validación la huella es la unión de
   grupo de ceniza y grupo convectivo. Lo dejo dicho; no cambia nada de lo demás.
5. Las 33 filas de Fuego en el perfil son pares cuadro y evento (26 archivos, algunos con 2 o 3 eventos).

Un aviso de disco durante el trabajo: D: estuvo lleno unos minutos. Los 40 npz que yo había escrito se
revisaron uno por uno (CRC del zip y forma 601 x 601): ninguno dañado.

## 7. Seguimientos sugeridos (no hechos aquí)

1. **Usar SL de Chillán como verdad por píxel de nuestras tablas.** SL es la probabilidad infrarroja de
   VOLCAT en 767 píxeles de Chillán. Comparar ahí nuestra probabilidad reproducida, píxel a píxel, valida
   la reproducción en el caso que importa y no sólo en los casos de prueba.
2. **Usar S menos nuestra tabla de día** en los 92 píxeles de Chillán con probabilidad publicada alta, para
   separar "tabla con canal solar" de "término de objeto" (punto 3 de lo que no se sabe).
3. Corregir en H14 la frase "la escala no está documentada": ahora se sabe qué es cada campo. La conclusión
   de H14 se mantiene y queda más firme.
4. Revisar por qué el PNG decodificado de PR 85 no muestra probabilidad de 20 % o más en 15 a 19 cuadros
   donde el archivo de evento sí la tiene.
5. Los paquetes de Etna y Mauna Loa del mismo release pueden traer más eventos `ASHPLUMEPUFF` con L2 al
   lado. Con ellos se podría calibrar de noche y comparar Chillán con más de un evento.
6. Para el correo a Pavolonis: ya no hace falta preguntar el sentido de la escala. La pregunta útil es qué
   criterio abre y sostiene un objeto cuando la probabilidad publicada de todos sus píxeles es casi cero.

## 8. Archivos y cómo reproducir

Datos, sólo lectura y fuera del repositorio:
`D:\goes_notas\s16\modo_dia\fuego\fuego_goes16-fulldisk_june2018_r20260709-volcat-code-ancil\reference_data\`
y `D:\goes_notas\busqueda_2026-11-20\volcat_eventos_357070\`. Intermedios míos, fuera del repositorio:
`D:\goes_notas\s17\h20a\` (grillas del L2 en npz y tablas por píxel).

```bash
D:\goes_notas\busqueda_2026-11-20\venv_hdf4\Scripts\python.exe -I scripts/h20a_extraer.py <reference_data> D:\goes_notas\s17\h20a\l2
```

```bash
python -I scripts/h20a_alinear.py
```

```bash
python -I scripts/h20a_medir.py eleccion
```

```bash
python -I scripts/h20a_medir.py validacion
```

```bash
python -I scripts/h20a_explora.py validacion fuego_vcb
```

```bash
python -I scripts/h20a_perfil.py
```

```bash
python -I scripts/h20a_sza.py
```

- `scripts/h20a_inventario.py`, `h20a_inventario_hdf.py`: nombres y atributos, sin valores.
- `scripts/h20a_comun.py`: lectura, ventana del recorte, acuerdos.
- `resultados/alineacion.csv`, `eleccion_medir.json`, `validacion_medir.json`, `eleccion_explora.txt`,
  `validacion_explora_fuego.txt`, `validacion_explora_san_cristobal.txt`: tarea 1.
- `resultados/perfil_por_cuadro.csv`, `perfil_por_evento.json`, `esquema.json`,
  `transferencia_chillan.json`, `sza_S_SL.json`, `saltos_chillan.txt`: tarea 2.
