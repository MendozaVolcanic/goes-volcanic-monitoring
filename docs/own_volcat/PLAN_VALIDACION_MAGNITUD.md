# Plan: validar la MAGNITUD de la altura propia contra VOLCAT

Estado: **paso 0 hecho** (16-11-2026): 989 archivos, 112 MB, 0 errores, en
`data/raw/volcat_validacion/` con `manifiesto.json` (URL, bytes, sha256) y `eventos.json`.
Script: `scripts/harvest_volcat_validacion.py`. **Paso 1 hecho** (16-11-2026, §3.1 abajo).
**Paso 2 hecho** (16-11-2026, §3.2). **Revisión a ojo previa al paso 3 hecha** (§3.3):
encontró un umbral mal dimensionado, **corregido el 17-11** (§3.3). **Pasos 3 a 6 hechos
(18-11-2026, §3.7): la magnitud no se pudo validar, porque nuestra máscara de ceniza no ve
ninguna de las plumas que VOLCAT mide (109 de 110 scans sin píxeles).**

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

**Corrección hecha (17-11-2026, ficha SDA v2.7).** `TOP_MIN_AREA_KM2 = 12` (umbral nuestro)
y `top_min_px(px_km, px_km_ew)` en `src/process/volcat_colorbar.py`; `volcat_height_at`
pasa el lado E-O del píxel CE (px_km·cos(lat)). 10 mutaciones, todas atrapadas. Sobre los
cuadros guardados:
- Sabancaya 01-11: 03:00 y 03:20 bajan a 6 a 7 km (10,9 y 11,1 km²); 03:10 queda en 7 a
  8 km (12,5 km², justo sobre el borde); desde 03:30 el tope de 7 a 8 km es firme (27 km²
  o más). El salto de 6 a 7 a 7 a 8 km queda en 03:10 a 03:30, no en 03:00.
- Sabancaya 26-10: desaparecen los 16 a 18 km, pero 12:20 a 12:40 dan 12 a 14 km con
  12,5 a 15,2 km² (3 a 4 píxeles IR). Un umbral de 3 píxeles IR no separa ese ruido; el
  evento ya quedaba fuera de la comparación por la revisión a ojo. Subir el umbral es
  decisión de Nicolás (costaría el cuadro de 03:10 del 01-11).
- Chillán 08-11 (sector de 2 km): el mínimo sigue en 3 píxeles, sin cambios.

Consecuencia para el paso 3: los casos utilizables son Sabancaya 01-11 (tope de 6 a 7 km
de 23:10 a 02:50 y de 7 a 8 km desde 03:00, pluma de 1 a 2 % del sector que crece sin
cortarse), Sabancaya 28-10 (6 a 7 km, 09:10 a 11:20) y Chillán 08-11 (3 a 4 km).
Reventador 07-11 20:50 y 21:00 (8 a 10 km) como caso secundario.

**3.4 Chillán a cadencia completa y un manto que el 5 % no atrapa (17-11-2026).** Se
bajaron los 2.181 cuadros publicados de `Chile_Central_2_km` del 01-11 al 16-11 (de 2.304
posibles) y se leyeron cuadro a cuadro. Horas de Chile:
- **Pulsos anclados al cráter:** 08-11 de 11:00 a 18:30 (27 cuadros, 1 a 4 km; los
  primeros objetos ya desprendidos a 11 a 20 km), 10-11 de 12:00 a 12:10 y de 18:30 a
  20:30 (13, 3 a 5 km), 11-11 de 14:50 a 15:10 (3, 3 a 5 km) y 14-11 de 13:40 a 20:30
  (38, 3 a 5 km, con cuadros sueltos de hasta 12 km). El objeto más grande de esos días
  mide 67 píxeles (~270 km²). Para el paso 3 suman 10-11, 11-11 y 14-11 a Chillán 08-11.
- **16-11 (y 15-11 desde las 23:30): un sistema que NO es pluma pasa el filtro.** Aparece a
  ~110 km del cráter, se acerca y lo cubre de 05:20 a 09:00. `volcat_object_heights`, el
  código de producción, corrido sobre esos cuadros, devuelve **tope 16 a 18 km** para
  Chillán (06:50, 07:30, 08:50 y 09:00): el objeto es el 3,0 a 4,1 % del sector, bajo el
  `MAX_SECTOR_FRAC` de 5 %, y mide hasta ~31.000 píxeles (~126.000 km²), unas 470 veces
  la pluma más grande del período.
- **Causa:** una fracción del sector no es una medida física. Los mantos que fijaron el
  5 % (68, 49 y 29 %) eran de sectores de 250 m, chicos; `Chile_Central_2_km` es tan
  grande que un sistema de escala sinóptica cabe en un 4 %. Es el mismo error que tenía
  `TOP_MIN_PX` (contar en el PNG en vez de medir en el terreno) y el mismo tipo de caso que
  Cotopaxi 25-10: un objeto que nace lejos y pasa por encima del cráter.
- **Alcance:** `volcat_height_at` sólo la llaman `scripts/validate_fase3b.py` y esta
  validación; la app no la usa. No hay altura falsa en pantalla, pero el paso 3 la
  heredaría si se comparan cuadros del 16-11.
- **Decisión pendiente de Nicolás (no se cambió código):** (a) límite en km² del objeto
  anclado, que también rechazaría la nube de una erupción grande horas después del inicio;
  (b) criterio temporal, el objeto tiene que existir anclado al cráter antes de crecer
  (atrapa este caso y Cotopaxi, pero exige varios cuadros y no cabe en la función de un
  cuadro); (c) dejar la función como está y excluir a mano los cuadros con sistemas que
  entran desde lejos, como se hizo con Cotopaxi. Recomendación: (c) para el paso 3, que
  usa casos ya revisados a ojo, y (b) si alguna vez la lectura VOLCAT llega a la app.

**3.5 Chillán 14-11: VOLCAT da 8 a 12 km donde las cámaras no ven nada sobre 6 km (17-11-2026).**
Las cámaras del observatorio no vieron nada sobre 6 km sobre el nivel del mar (unos 3 km sobre
el cráter de 3.212 m). VOLCAT da tope firme de 3 a 5 km casi todo el día, pero de 16:20 a 16:50
y de 18:00 a 18:20 (hora de Chile) pinta píxeles de 8 a 12 km. Revisado sobre los nueve scans
(seis altos y tres de control):
- **Los píxeles altos están sobre la pluma**, en el eje que sale al SE del cráter, en el mismo
  lugar que los de 3 a 5 km de los controles. No están sobre las líneas finas de hielo N-S que se
  ven en Ash RGB a 10 a 15 km al oeste y al este. La pluma pasa del naranja (3 a 5 km) a amarillo,
  verde y azul en esas horas, y a las 19:20 vuelve al naranja.
- **Nada en el IR está tan frío.** Dentro de 25 km del cráter ningún píxel de 2 km baja de
  271 K en BT 11,2 µm. Con el GFS archivado, una nube opaca a 8 km estaría a 249 K y a 12 km a
  216 K. El píxel más frío es la cumbre nevada. VOLCAT llega a 8 a 12 km solo si trata esos
  píxeles tibios como nube delgada y fría: es la solución semitransparente del retrieval, no un
  tope real.
- **Coincide en el tiempo con cirros delgados** que cruzan cerca del cráter de 16:20 a 18:20
  (también hay uno a las 19:20, en el control). Pueden perturbar el retrieval, pero no está
  probado.
- **Nuestros métodos no detectan esta pluma**: `detect_ash_enhanced` da 0 píxeles en los nueve
  scans, controles incluidos (BTD 11-12 nunca baja de -1 K dentro de 25 km). La firma de esta
  ceniza es más débil que nuestro umbral; VOLCAT la detecta con otras pruebas.
- **Consecuencia para el paso 3**: Chillán 14-11 entra solo con los cuadros de tope 3 a 5 km.
  Los de 8 a 12 km son un caso documentado de sobreestimación del retrieval semitransparente,
  útil para el paper y para la regla de no reportar alturas altas con BT11 tibia.

**3.6 Un detector más sensible para las plumas chicas de Chillán: ninguna variante sirve (17-11-2026).**
La pregunta era si un detector distinto de `detect_ash_enhanced` ve las emisiones de Chillán de
noviembre que VOLCAT sí ve (§3.4), sin llenar los Andes de falsas alarmas. La hipótesis: sobre la
cordillera la BTD 11-12 de cielo despejado es positiva (vapor de agua), así que una pluma que la baja
1 a 2 K nunca cruza el umbral absoluto de -1 K; una anomalía respecto del cielo despejado propio de
cada píxel sí la vería. **No se cambió código.**

- **Criterio, declarado antes de ver números.** Unidad: scan de 10 min, ventana de ±1° alrededor del
  cráter. Positivo: cuadro VOLCAT con objeto anclado al cráter los días 08, 10, 11 y 14-11. Negativo:
  días sin ceniza (01 a 06, 09, 12, 13 y 15-11), de 11:00 a 20:50 hora de Chile; aparte, el sistema
  meteorológico del 16-11 (05:20 a 09:00), que no debe detectarse. Detección: objeto conexo de 2 o
  más píxeles ABI con uno a 10 km o menos del cráter. Umbrales elegidos con 08 y 10-11 más negativos
  01 a 06, congelados y evaluados en 11 y 14-11 más negativos 09, 12, 13 y 15. Cumple si en la prueba:
  (1) detecta 50 % o más de los cuadros VOLCAT; (2) falsa alarma en 2 % o menos de los scans
  negativos y ningún día con más de 3; (3) 10 % o menos en el 16-11; (4) 50 % o más de los píxeles
  marcados a 30 km o menos del cráter caen en la huella VOLCAT dilatada 1 píxel (para no premiar
  cirros o nieve que coinciden en la hora).
- **Datos.** 978 scans GOES-19 L1b (C11, C14, C15), leídos solo en la ventana. Positivos: 57 cuadros
  VOLCAT anclados (el criterio decía 59 por un conteo previo; la tabla de cuadros da 57). Faltó el L1b
  de 08-11 21:00 UTC, así que quedaron 21 de ajuste y 35 de prueba. Días negativos con un scan cada
  20 min (30 por día): el tope de 3 por día se aplicó sobre esa cadencia, el doble de exigente que a
  10 min. Huellas VOLCAT llevadas a la grilla ABI desde los PNG de `Chile_Central_2_km`.

| Variante | Detecta (prueba) | Falsa alarma (prueba, peor día) | 16-11 | En la huella VOLCAT |
|---|---|---|---|---|
| `detect_ash_enhanced` (BTD < -1 K + tri-espectral) | 0 de 35 | 0 de 120 | 0 de 23 | sin píxeles |
| BTD < -0,5 K | 0 de 35 | 0 de 120 | 0 de 23 | sin píxeles |
| BTD < 0 K, sin tri-espectral | 3 de 35 | 4 de 120 (3) | 3 de 23 | 73 % (26 px) |
| Anomalía respecto del cielo despejado del píxel | **27 de 35 (77 %)** | **18 de 120 = 15 % (9)** | 0 de 23 | **25 %** |
| β(12,11) con fondo compuesto, T_ref 215 K | 21 de 35 (60 %) | 7 de 120 = 5,8 % (5) | 0 de 23 | 26 % |

  La anomalía elegida con el ajuste: referencia por píxel = mediana de BT8,4, BT11,2 y BT12,3 de los
  3 días más tibios en BT11,2 entre los 10 previos, mismo slot (±10 min); marca si BT11 > 200 K y
  ΔBTD < min(-0,4 K; 0,3·ΔBT11). Cumple (1) y (3), falla (2) (9 falsas alarmas el 12-11 y 9 el 13-11,
  con ~160 píxeles marcados por scan en los días negativos de la prueba) y (4). β(12,11) usa
  `beta_ratios.cloud_emissivity` con el compuesto como cielo despejado; con T_ref ±10 K su
  sensibilidad va de 60 a 66 %. Ninguna de las 2.592 combinaciones de la anomalía ni de las 540 de β
  cumple los cuatro criterios, ni siquiera eligiéndola con la prueba: con sensibilidad de 50 % o más,
  la mejor coincidencia espacial es 27 %.
- **Por qué (la física).** Dentro de la huella VOLCAT la BTD casi no cambia respecto del cielo
  despejado: la mediana de ΔBTD es +0,31 K (ajuste) y +0,02 K (prueba), con percentil 5 de -0,6 y
  -1,0 K. En los 10 km alrededor del cráter, los días sin ceniza tienen percentil 5 de -1,4 y -1,6 K
  (vapor, nieve, nubes). La pluma no baja la BTD más que un día normal, y el 14-11 la huella está
  incluso 1 K más tibia que la referencia en BT11. No hay firma split-window que separar en un
  píxel de 2 km: si hay ceniza es poca o muy delgada, y VOLCAT la marca con pruebas que no tenemos.
  Corrige la lectura de §3.5: no es que la firma quede justo bajo nuestro umbral, es que no se
  distingue del fondo. Lo que la anomalía marca el 14-11 es una franja de ~45 km hacia el SSE, y el
  12-11, día sin ceniza, aparece una franja parecida. Los cirros lineales del 14-11 (16:20 a 18:20)
  no sirven para separar cirro de pluma: 11 de esos 13 scans también son positivos VOLCAT.
- **Sin probar:** β(8,5/11) y la banda de 10,3 µm; negativos a 10 min; GFS archivado para la T_ref
  de β (se usó una constante); otros volcanes y plumas más cargadas de ceniza. Scripts y huellas
  quedaron fuera del repo (dependen de ~60 MB de ventanas L1b cacheadas fuera del repo).

**3.7 Resultado de los pasos 3 a 6 (18-11-2026): no hay magnitud que validar, falla la detección.**
Criterio de aplicación y lista de exclusión commiteados antes de correr nuestros métodos
(`docs/own_volcat/validacion_magnitud/CRITERIO.md` y `exclusiones.json`). Script reproducible
`scripts/validate_magnitud.py` (etapas `volcat`, `recortes`, `propios`, `comparar`); resultados
por scan en `docs/own_volcat/validacion_magnitud/propios_parte*.json` y tabla en `tabla.md`.

- **Datos.** 122 cuadros VOLCAT con tope anclado en 9 eventos; 12 excluidos a ojo (Cotopaxi 25-10
  entero, Sabancaya 17-10 entero, Sabancaya 26-10 12:20 a 12:40, Reventador 03-11 20:40); quedan
  **110 scans**. Mismo scan GOES-19, caja de ±0,75° (la de la app), GFS archivado inyectado
  (ningún scan quedó sin perfil). Cada escena bajó ~98 MB de L1b, borrados tras cada scan.
- **Resultado por método** (criterio de Nicolás del 16-11: cruce de intervalos, sin margen):

  | Método | Scans con tope propio | Se cruzan con VOLCAT | Sin tope propio |
  |---|---|---|---|
  | BT-matching | 1 de 110 | 0 de 1 | 109 `no_plume` |
  | Wen-Rose (banda β) | 1 de 110 | 0 de 1 | 109 `no_plume` |
  | ACHA ∩ ceniza | 1 de 110 | 0 de 1 | 107 `no_plume`, 2 `no_data` (sin gránulo ACHA) |

  Por evento, los scans sin tope propio son: Sabancaya 01-11 46 de 46, Sabancaya 28-10 19 de 19,
  Sabancaya 26-10 20 de 20, Chillán 08-11 13 de 13, Reventador 26-10 6 de 6, Reventador 03-11
  3 de 3 y Reventador 07-11 2 de 3.
- **El único scan con tope propio** (Reventador 07-11 20:40, VOLCAT 7 a 8 km) tiene **1 píxel** en
  la máscara dentro de la caja de ±83 km: BT-matching 11,2 km, Wen-Rose 11,3 km con banda β 11,2 a
  13,1 km (confianza "muy baja"), ACHA 14,8 km. Ninguno se cruza; los tres quedan sobre VOLCAT. Un
  píxel no es una pluma y no se revisó si cae sobre ella: no se lee como sesgo.
- **Por qué (comprobado, no supuesto).** Los tres métodos parten de la misma máscara
  `detect_ash_enhanced` (BTD 11-12 < -1 K más tri-espectral); si está vacía, ninguno tiene píxel
  que medir. En 109 de 110 scans la máscara tiene 0 píxeles. En Sabancaya 01-11 05:00, con VOLCAT
  dibujando una pluma de 7 a 8 km que nace en el cráter, dentro de 15 km del volcán la BT 11,2 µm
  mínima es 264,1 K (mediana 267,9 K) y la BTD 11-12 mínima es -0,56 K (percentil 5: -0,48 K;
  lejos del volcán, percentil 5: -0,42 K). La pluma no tiene firma split-window que nuestro umbral
  pueda separar y tampoco es fría: no es una nube opaca. Es lo mismo que §3.5 y §3.6 midieron en
  Chillán, ahora en las plumas más densas de la ventana de 30 días de VOLCAT en Perú y Ecuador.
- **Consecuencia.** La pregunta de este plan (¿es correcta la temperatura del tope que leemos?) no
  se puede responder con estas plumas: nuestra cadena se detiene antes, en la detección. VOLCAT
  asigna 6 a 8 km a plumas tibias y semitransparentes con pruebas que no tenemos (§3.6). Para
  validar la magnitud hace falta una pluma que nuestra máscara sí vea (BTD bajo -1 K, ceniza densa
  y opaca), dentro de los 30 días que guarda el API de VOLCAT, o el paso 7 (cosecha continua) para
  no perderla. No se cambió lógica de la app ni la ficha SDA.
- **Límites.** Un scan cada 10 min dentro de cada evento no son muestras independientes; el
  resultado es por scan, como pide el criterio. La lista de exclusión es juicio a ojo, declarado y
  commiteado antes de medir.

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
