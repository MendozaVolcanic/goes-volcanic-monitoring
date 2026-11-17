# Plan: validar la MAGNITUD de la altura propia contra VOLCAT

Estado: **paso 0 hecho** (16-11-2026): 989 archivos, 112 MB, 0 errores, en
`data/raw/volcat_validacion/` con `manifiesto.json` (URL, bytes, sha256) y `eventos.json`.
Script: `scripts/harvest_volcat_validacion.py`. **Paso 1 hecho** (16-11-2026, §3.1 abajo).
**Paso 2 hecho** (16-11-2026, §3.2). **Revisión a ojo previa al paso 3 hecha** (§3.3):
encontró un umbral mal dimensionado que hay que corregir antes del paso 3. Pasos 3 a 6 sin empezar.

## 1. Por qué

Hasta hoy la altura propia (BT-matching, Wen-Rose, ACHA ∩ ceniza) solo se validó en
**comportamiento**: sube cuando debe, se rinde cuando no puede. El número absoluto nunca se
comparó contra otra medición, porque en las plumas chilenas finas ni ACHA ni VOLCAT
detectan nada. Lo que sí está validado es la conversión temperatura → altura (GFS contra
radiosondas: ≤ 60 m entre 5 y 12 km). Falta saber si la **temperatura del tope** que
leemos es la correcta, y eso solo se ve con una pluma densa que VOLCAT sí mida.

VOLCAT no es la verdad: es otro retrieval (Pavolonis 2013), validado contra CALIPSO en la
literatura. Que coincidamos con VOLCAT dice que leemos la misma física; no que ambos
acierten.

## 2. Qué se midió el 16-11-2026 (hechos que fijan el diseño)

1. **El API de VOLCAT guarda 30 días rodantes.** `get_list` con `daterange:180` devuelve
   igual solo del 17-10 al 16-11 (unos 4.300 cuadros por sector ABI, cada 10 min). Un
   evento de hace más de un mes **no tiene VOLCAT** contra qué comparar. Los datos GOES
   (L1b y ACHA en S3) y el GFS archivado no tienen ese límite.
2. **Hay plumas limpias dentro de la ventana.** Sondeo de 1 cuadro cada 3 h en 6 sectores
   (caja de ±0,3° en el centro del sector, que es el volcán):

   | Evento (UTC) | Lo que se ve en el cuadro VOLCAT | Vence en el API |
   |---|---|---|
   | Reventador 07-11 20:50 | pluma compacta anclada al volcán, colores de 7 a 11 km | ~07-12 |
   | Sabancaya 01-11 00:30 a 06:30 | pluma compacta, ~7 a 8 km (cumbre ~6 km) | ~01-12 |
   | Sabancaya 26-10 09:30 y 28-10 09:30 | objetos verdes compactos en el volcán (revisado a ojo) | ~25-11 y ~27-11 |
   | Cotopaxi 25-10 17:40 | objeto verde compacto (revisado a ojo) | ~24-11 |
   | Cotopaxi 25-10 20:50 | objeto azul (~10 a 11 km) entre nubes meteorológicas frías: **dudoso** | ~24-11 |
   | Ruiz 23-10 14:50 y Sabancaya 17-10 14:50 | un solo píxel: **no sirven** (cosechados igual, por si la ventana muestra más) | vencidos o casi |
   | **Nevados de Chillán 08-11 13:20 a 21:40** | pulsos anclados al cráter, deriva al SE; lectura de ~2,4 a ~6,5 km (pico 20:10 a 20:30) | ~08-12 |

   Chillán es el único caso chileno y el único volcán del catálogo propio, pero no
   tiene sector dedicado: cae en `Chile_Central_2_km` (píxel de ~2 km). Revisado a ojo
   (16:30 y 20:30 UTC): objeto compacto que nace en el cráter. **Muchos píxeles salen
   rojos, ~2 km s.n.m., por debajo de la cumbre (3.212 m).** Un tope que sale del
   cráter no puede estar bajo la cumbre: o VOLCAT subestima la pluma fina (el fondo
   cálido contamina el IR) o la lectura inversa del rojo falla. El paso 1 tiene que
   separar las dos causas antes de usar este caso como referencia.
   **Resuelto en el paso 1: era la lectura.** En el sector de 2 km el color viene
   mezclado con el gris del fondo y la lectura vieja lo mandaba a bloques bajos. Con la
   lectura nueva, 13 de 64 cuadros tienen tope firme y siempre es de **3 a 4 km**, sobre
   la cumbre; el pulso de 5 a 6 km (20:20 a 20:30) es de 1 a 2 píxeles y queda solo
   como máximo crudo.

3. **Trampa: el PNG de VOLCAT pinta también falsas detecciones de escala sinóptica.**
   Sabancaya y Ubinas el 03-11 y el 16-11, y Copahue el 16-11 a la misma hora, salen
   con el sector casi entero coloreado a 13 a 20 km (cuadro del 16-11 09:50 revisado a
   ojo: un manto que cubre todo el sector, no una pluma). Contar píxeles con color de la
   escala no basta: hay que quedarse con el **objeto conectado al volcán**.
4. ~~La lectura inversa del colorbar subestima los colores azules.~~ **Corregido en el
   paso 1: era al revés.** En Reventador 07-11 la pluma es mayormente verde oscuro
   (7 a 8 km) y solo el tope es azul; el p95 bajo venía de esa mezcla. La lectura lineal
   en realidad **sobreestimaba** hasta 10 %: estiraba 0 a 20 km sobre la parte saturada de
   la barra, que termina en 18 km (el bloque 18 a 20 es negro).

## 3. Pasos

**Paso 0: cosechar ya los cuadros que vencen (urgente, ~15 min).** Bajar los PNG Ash_Height
de cada evento candidato, ±3 h cada 10 min, más el JSON de coordenadas del sector, a
`data/raw/volcat_validacion/` (ya está en `.gitignore`). Unos 36 cuadros de ~220 KB por
evento, ~50 MB en total. Sin esto, los dos primeros candidatos de Sabancaya y Cotopaxi se
pierden en ~8 días. Es reversible y no toca código de producción.

**Paso 1: lectura inversa confiable.** En `src/process/volcat_colorbar.py`:
- quedarse con el objeto coloreado **conectado al píxel del volcán** (componente conexa) y
  descartar el cuadro si el objeto llena más de una fracción del sector (el umbral es
  nuestro, no de la literatura: va declarado como tal);
- medir el error de la lectura por cada color de la barra (la barra es discreta, de 1 km
  por color, así que la resolución de la referencia es ~1 km) y corregir la subestimación
  del azul. Con TDD, sobre cuadros reales guardados en el paso 0.

**3.1 Resultado del paso 1 (16-11-2026).** `volcat_object_heights` en
`src/process/volcat_colorbar.py`, usado por `volcat_height_at`; 17 pruebas nuevas, todas
verificadas por mutación (8 mutaciones, 8 atrapadas):
- la barra se lee como bloques con intervalo: 1 km por color de 0 a 10 km y 2 km arriba
  (10-12, 12-14, 14-16, 16-18; el 18-20 es negro y no se distingue del fondo). El tope se
  informa como intervalo, no como número con decimales;
- cada píxel: color exacto primero; si no, separación "color + gris". Si dos intervalos
  explican el mismo color, el píxel no se usa. En sectores de 2 km, **1-2 km y 2-3 km no
  se pueden separar** (rojo y salmón diluidos en gris dan el mismo color): es un límite del
  producto, no del código;
- solo cuenta el objeto que toca el volcán en un radio de 10 km (paralaje de GOES-East);
  un objeto de más del 5 % del sector es un manto sinóptico y se rechaza (los tres del
  16-11 quedan fuera: 68, 49 y 29 %);
- el tope exige 3 píxeles del bloque; el máximo crudo se informa aparte.

Pendiente que el paso 2 resuelve: en los sectores dedicados el volcán **no** está en el
centro del cuadro (Reventador a ~14 km, Cotopaxi a ~11 km del centro), así que hacen falta
sus coordenadas GVP para anclar el objeto.

**3.2 Resultado del paso 2 (16-11-2026).** `src/volcanos_validacion.py`: Reventador
(GVP 352010; -0,077, -77,656; 3.562 m), Cotopaxi (352050; -0,677, -78,436; 5.911 m) y
Sabancaya (354006; -15,787, -71,857; 5.960 m), del WFS oficial del GVP (la web
volcano.si.edu da 403 a clientes automáticos). Fuera del catálogo operacional. Ruiz se
descartó (un solo píxel). Dos hallazgos:
- **Bug del paso 1 corregido:** `SCALE_FACTOR` de SSEC está en segundos de arco
  (`EQ_RADIUS` = 206.264,8 = segundos de arco por radián), no en km. Se usaba como km y
  el radio de anclaje quedaba en 1 píxel. La prueba sintética pasaba porque repetía el
  mismo supuesto; ahora usa la georef real de `Chile_Central_2_km`.
- **Anclaje con coordenadas GVP:** Sabancaya ancla bien (01-11: 46 de 67 cuadros, tope
  6 a 8 km, 0,5 a 2 km sobre la cumbre; 28-10: 22 de 34). Chillán: 13 de 64, 3 a 4 km.
  **Reventador ancla mal** (3 a 9 de ~35 por evento) y **Cotopaxi** ancla mal con topes de
  12 a 18 km; Sabancaya 26-10 tiene 5 cuadros con 16 a 18 km. Hay que mirarlos a ojo
  antes del paso 3 (¿pluma desprendida, objeto meteorológico, o el radio de 10 km?).

**3.3 Revisión a ojo de los anclajes raros (16-11-2026, antes del paso 3).** Recortes
alrededor del volcán con el disco de 10 km dibujado, cuadro por cuadro:

- **Reventador 07-11: ancla poco porque la pluma es un pulso, no por la lectura.** VOLCAT
  no dibuja nada hasta las 20:40; de 20:40 a 21:00 hay una pluma compacta que nace en el
  borde sur del disco (4 a 9 km del cráter) con tope de 7 a 10 km; a las 21:10 ya se
  desprendió (20 km al sur) y a las 21:30 quedan 2 píxeles a 50 km. Tres cuadros firmes es
  lo que el evento da. Además hay ~8.600 píxeles de color fijos en todos los cuadros, lejos
  del volcán (90 km o más), que el anclaje ya deja fuera.
- **Cotopaxi 25-10 19:40 a 20:20 (topes de 12 a 18 km): probable convección, se excluye.**
  El objeto (núcleo magenta 14 a 16 km, borde azul) no nace en el cráter: aparece a las
  19:00 y 19:30 unos 13 a 20 km al NE, crece, cruza sobre el volcán hacia el SW y a las
  20:30 está 20 km al SSW; a las 21:10 hay una celda fría grande justo encima del volcán.
  Es la hora de máxima convección en Ecuador (15 h local). Un tope de 14 a 16 km de
  Cotopaxi sería una erupción mayor; no hay comprobación independiente aquí, así que el
  caso queda fuera de la comparación y declarado como tal. El anclaje de 10 km no lo
  atrapa porque el objeto pasa por encima del cráter. El cuadro de las 17:20 (6 a 7 km,
  objeto chico al E de la cumbre de 5,9 km) es plausible pero es uno solo.
- **Sabancaya 26-10 11:50 a 13:10 (topes de 16 a 18 km): ruido, y destapa un umbral mal
  dimensionado.** Son 1 a 4 píxeles IR sueltos (bloques de ~2 km) morados y magenta sobre
  un fondo IR oscuro, es decir CÁLIDO. Un tope real a 16 km en el trópico estaría a
  ~200 K y se vería blanco en el IR de fondo. El tope pasó porque `TOP_MIN_PX = 3` cuenta
  píxeles del PNG: en un sector de 250 m un píxel IR de ABI (~2 km) son ~7 x 7 píxeles del
  PNG, así que "3 píxeles" son 0,2 km², una fracción de un píxel del satélite. En Chillán
  (sector de 2 km) los mismos 3 píxeles son ~15 km². **Corrección pendiente (antes del
  paso 3, con TDD y mutación):** el mínimo del tope tiene que ser un ÁREA en píxeles del
  sensor (p. ej. 3 píxeles IR de 2 km, ~12 km², umbral nuestro), convertida a píxeles del
  PNG con `px_km`. Revisar después qué cuadros de Sabancaya 01-11 quedan: los primeros de
  7 a 8 km (03:00 a 03:20, 148 a 170 píxeles del PNG, ~11 a 13 km²) quedan justo en el
  borde. Va en la ficha SDA en el mismo commit.

Consecuencia para el paso 3: los casos utilizables son Sabancaya 01-11 (tope de 6 a 7 km
de 23:10 a 02:50 y de 7 a 8 km desde 03:00, pluma de 1 a 2 % del sector que crece sin
cortarse), Sabancaya 28-10 (6 a 7 km, 09:10 a 11:20) y Chillán 08-11 (3 a 4 km).
Reventador 07-11 20:50 y 21:00 (8 a 10 km) como caso secundario.

**Paso 2: volcanes fuera del catálogo.** Chillán ya está en el catálogo. Objetos `Volcano` para Reventador, Sabancaya,
Cotopaxi y Ruiz con coordenadas y cota tomadas del GVP (Smithsonian), citadas, no de memoria.
`acquire_ash_scene` ya acepta un objeto en vez de un nombre.

**Paso 3: correr nuestros tres métodos en cada cuadro.** Mismo scan que el cuadro VOLCAT,
con el **GFS archivado inyectado** (`profile_fn`, PR 36): para eventos de más de 2 días
Open-Meteo ya no tiene el perfil, y sin PR 36 el retrieval habría usado el de otro día.

**Paso 4: comparar.** Por scan, estadísticos del tope (p95 y máximo) del objeto de VOLCAT
contra los nuestros, dentro de la misma caja. No píxel a píxel: así no entra el paralaje
(1 km por km de altura a esas latitudes) ni la grilla distinta de VOLCAT.

**Paso 5: criterio declarado ANTES de ver números.** Propuesta: es consistente si el p95
de VOLCAT cae dentro de **nuestra propia banda β** (`top_km_lo` a `top_km_hi`), que es la
incertidumbre que el retrieval ya declara. Como referencia, sin usarlo de criterio: la
literatura reporta un sesgo IR de −0,4 a −0,8 km (Pavolonis 2020). La decisión del criterio
es tuya.

**Decidido por Nicolás el 16-11-2026, antes de ver ningún número:** un scan es
consistente si el intervalo del tope VOLCAT (`top_lo_km` a `top_hi_km`, el bloque de la
barra) **se cruza** con nuestra banda β (`top_km_lo` a `top_km_hi`). Sin margen extra:
se descartó la variante de ±1 km. Se aplica por método (BT-matching, Wen-Rose, ACHA) y
se reporta cuántos scans cumplen, no un promedio.

**Paso 6: registrar.** `scripts/validate_magnitud.py` reproducible, tabla en
`docs/paper/REGISTRO_PAPER.md` §3 y, si algo cambia la lógica, ficha SDA en el mismo commit.

**Paso 7 (opcional, decisión aparte): cosecha continua.** Un cron que guarde los cuadros
VOLCAT con objeto anclado a volcán en los sectores sudamericanos, para que el próximo
evento no venza a los 30 días. Implica almacenamiento y un workflow nuevo.

## 4. Lo que este plan no resuelve

- No valida contra una medición directa (lidar, radar, observación de pilotos): VOLCAT
  también es un retrieval IR.
- Los eventos son de Ecuador y Perú (trópico). En Chile el perfil y la tropopausa son
  distintos; el resultado se transfiere con esa salvedad.
- Las plumas de gas/SO₂ siguen sin altura por este camino.

## 5. Costo

Paso 0: ~15 min. Pasos 1 a 4: ~2 días. Paso 6: medio día. Las descargas L1b son ~78 MB por
escena (C11, C14, C15), más ~40 MB del GFS archivado por ciclo.
