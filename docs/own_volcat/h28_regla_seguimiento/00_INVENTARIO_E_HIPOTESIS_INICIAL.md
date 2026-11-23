# H28, paso 0: inventario propio e hipótesis inicial

Escrito el 23-11-2026 por la sesión S19f, **antes** de leer los informes de `docs/own_volcat/`
(`h20a_campos_evento/`, `h20c_kirishima_luz/`, `h19_objeto_fuego/`, `eventos_h14/`, `h16_objeto/`).
Este archivo se commitea antes de abrirlos. Lo que diga aquí puede repetir o contradecir lo que
ellos ya midieron: la comparación va en el informe final.

## 1. Qué hay en disco (visto con herramienta, no supuesto)

| Caso | Carpeta | Qué trae | Qué no trae |
|---|---|---|---|
| Chillán, 13 al 18-11-2026 (GOES-19 disco completo, 10 min) | `D:\goes_notas\busqueda_2026-11-20\volcat_eventos_357070\` | 60 NetCDF de evento y 60 JSON | logs, alertas, objetos L2 |
| Kirishima, 02-07-2025 (Himawari-9 sector Japón, 2,5 min) | `D:\goes_notas\s17\paquetes\kirsh\...\reference_data\` | 25 logs de alertas, 25 logs de eventos, 25 alertas (txt y xml), 7 eventos por volcán, 25 NetCDF de cuadro | L2 (borrada), `volcat_diag` vacía |
| Fuego, 03-06-2018 (GOES-16 disco completo, 15 min) | `D:\goes_notas\s16\modo_dia\fuego\...\reference_data\` | 40 logs de alertas, 40 de eventos, alertas, eventos (52 archivos de vid342090, 2 de vid344020), L1, L2, RTM, `diag_data`, historia (963 MB), serie térmica | `volcat_diag` vacía |
| Mauna Loa, 28-11-2022 (GOES-17 CONUS, 5 min) | `D:\goes_cache\volcat_test_mauna_loa\` (`paquete.tar.gz` y `ext\`) | 10 logs de alertas, 10 de eventos, alertas, eventos, L2 | |
| Fukutoku, 12-08-2021 | `D:\goes_notas\s17\paquetes\fuku\` | sólo listados (`extraidos.txt`, `resumen_eventos.txt`); los archivos ya no están | todo lo demás |
| Etna, 14-08-2024 | sólo el listado del tar (`D:\goes_notas\s17\etna10_tar_lista.txt`) | nada extraído | todo |

Ningún paquete trae código. Los logs sí traen el encabezado de versión de las rutinas
(`volcat_alerts.f90`, `volcat_history_utils.f90`, `volcat_plume_utils.f90`, `volcat_grouping_utils.f90`).

### 1.1 Variables del NetCDF de evento de Chillán (un archivo abierto: 14-11 19:00 UTC)

Las que hablan de tiempo o de identidad del objeto, que son las que importan para esta prueba:

- `event_type` (`ASHPLUMEPUFF` en ese archivo), `feature_id`, `first_detection_feature_id`,
  `feature_age` (minutos; 150,0 en ese archivo), `time_coverage_start_first_detection`,
  `event_observation_time_first_detection`, `first_detection_full_image_start_time`,
  `first_detection_mean_feature_time`.
- `minimum_volcano_distance`, `maximum_volcano_distance`, `feature_area`, polígono del rasgo.
- `volcano_thermal_activity` con atributos `time_since_0MW`, `time_since_10MW`, `time_since_100MW`,
  `time_since_1000MW` (en ese archivo los cuatro valen el relleno, -2,1e9).
- Por píxel: `event_idx` (qué píxeles son el evento), `ash_spectral_signature_strength`,
  `ash_spectral_signature_strength_lwir_only`, `distance_traveled`, `residence_time`,
  temperaturas de brillo de 4, 8, 10, 11 y 12 µm, altura, carga, radio efectivo.
- El JSON repite la cadena del evento: un identificador `ID-<hora de nacimiento>_0001` y la lista de
  cuadros que le pertenecen, cada uno con `FEATURE_ID`, `EVENT_STATUS` y hora.

No hay en el archivo de evento una variable que se llame probabilidad, ni el método de
identificación, ni los conteos que el log imprime.

### 1.2 Qué imprime el log de alertas (censo de plantillas de línea, 25 logs de Kirishima)

404 plantillas distintas (`D:\goes_notas\s19\h28\kirsh_plantillas.txt`). Los bloques donde VOLCAT
decide algo sobre un objeto de ceniza son cinco:

1. **Configuración** (encabezado). Cuatro juegos de umbrales de objeto: `basic`, `plume/puff`,
   `neighbor` y `temporal`. En el juego `temporal` los filtros están apagados: ruido 1,01,
   emisividad mínima 1,00, emisividad máxima 1,01, no uniformidad 1,01, conteo mínimo 0.
   También: `History grid resolution (detection): .10`, `Ash history usage: 1`,
   `Minimum number of fractional days between ash alerts: 0.50`.
2. **Construcción de plumas ancladas a un volcán** (`CONSTRUCT_VOLCANIC_PLUMES`, "strong plumes" y
   "weak plumes"): por cada par volcán y objeto, líneas `Overlap=`, `Overlap(YES)=`, `Overlap(NO)=`,
   `FINAL:` y dos filas de banderas; al final `MATCH:` o `NO MATCH:` por volcán.
3. **Prueba de la pluma candidata** (`OBJECT_GROUPING_CONTRAST_ASH`, "Processing plume"): contraste
   en bloque, contraste detallado (RGB1, RGB2, "with/without distance check"), ruido de nube, y un
   veredicto `KEEPING plume with robust space and/or time pattern` o `ELIMINATING plume lacking
   robust space and/or time pattern`, seguido de conteos: `Time Trend Count`, `Robust Time Trend
   Count`, `New Emission Count`, `BTD Bullseye Count`, `Dynamic Corr Count`,
   `Spatial/Spectral Corr Count`, `BTD Stripe Count`, etc.
4. **Seguimiento contra la historia** (`HISTORY_GROUP2OBJECT`): por cada objeto del cuadro, distancia
   al rasgo publicado antes, umbral de distancia, distancia refinada y su umbral, y, si califica,
   `Overlap Frac`, `Emiss Sim`, `Reff Sim`, `Beta85 Sim` y la línea
   `Temporal selection criteria met for ash (n)`. Después, filtros de vecino más cercano y de
   polígono, y `***SELECTED object (with polygon fit)***`.
5. **Clasificación y alerta**: `Group Index / History Index / Time Diff(s)`, `Always Alert Flag`,
   `Missing History Count`, `Time Trend Count`, `K-d Overlap Count`, `Group classification`
   (New u Old Volcanic Feature), número de alertas y de grupos válidos sin alerta,
   `Identification Method`, `Median Probability of Pixels`.

Tablas propias sacadas de esos bloques con `scripts/h28_parse_logs.py`:
`D:\goes_notas\s19\h28\tablas\kirishima_{cuadros,plumas,historia,grupos}.csv`.

### 1.3 Lo que ya vi de cada caso al escribir esto (para que el orden sea comprobable)

- **Kirishima:** todo (25 logs, tablas completas, JSON de los 7 eventos).
- **Chillán:** la lista de nombres de archivo (las horas publicadas y sus huecos), las variables y
  los valores escalares de **un** archivo (14-11 19:00 UTC) y la estructura de su JSON, donde vi que
  el evento `ID-2026-11-14T16:30:30Z_0001` lleva 15 cuadros (o sea, la cadena que nace a las 16:30
  sigue viva a las 19:00 aunque falte el cuadro de las 17:10). No abrí ningún otro archivo.
- **Fuego:** nombres de archivo (incluidos los sufijos `AN/AY`, `IN/IY`, `HN/HY` de los logs y los
  tipos `VCB` y `ASHPLUMEPUFF` de los eventos) y el listado de variables de un L1. Ningún log.
- **Mauna Loa:** el listado del tar (nombres y tamaños). Ningún log.

## 2. Lo que se ve en Kirishima (hechos, con cuadro y valor)

1. De 13 plumas candidatas ancladas a un volcán, VOLCAT aceptó 2 (20:17:30 y 20:47:30, las dos
   de Kirishima) y eliminó 11. Las dos aceptadas tienen probabilidad mediana de píxel 2,40 % y
   0,01 % (`Median Probability of Pixels` del bloque de alerta) y aun así salen con
   `Alert Confidence: HIGH` e `Identification Method: Plume/Puff Extraction (SECO+)`.
2. Las dos aceptadas pasan el contraste detallado "without distance check", tienen
   `Spatial/Spectral Corr Count` = 1 y `Time Trend Count` igual a su número de píxeles (8 y 9).
   La candidata de las 20:45:00 pasa el mismo contraste, tiene `Spatial/Spectral Corr Count` = 1 y
   `Time Trend Count` = 7 con 7 píxeles, y fue eliminada. Las otras 10 eliminadas fallan el
   contraste "without distance check". Con 13 casos no se puede fijar qué separa 7 de 8.
3. Después de las 20:47:30, los cinco cuadros siguientes (20:50:00 a 21:00:00) no pasan por la
   prueba de pluma. Salen por el bloque 4: un objeto del cuadro queda a 0,0 a 2,1 km del rasgo
   publicado 143 a 156 s antes, se imprime `Temporal selection criteria met for ash` y el objeto
   se publica como "spectral feature" con `Group classification: Old Volcanic Feature`. No cuenta
   como alerta (`NUMBER OF ASH CLOUD ALERTS: 0`, `NUMBER OF VALID NON-ALERT ASH GROUPS: 1`) pero sí
   se escribe su archivo de evento.
4. En esos cinco cuadros, los objetos no elegidos (26 de 31 comparados) están a 26 km o más del
   rasgo. No hay ningún caso intermedio, así que Kirishima no dice si las similitudes
   (`Overlap Frac`, `Emiss Sim`, `Reff Sim`, `Beta85 Sim`) tienen umbral: se aceptó uno con
   `Overlap Frac` .00 y `Beta85 Sim` .15, y otro con `Beta85 Sim` .00.
5. El umbral de distancia no depende del área del rasgo sino del tiempo entre cuadros:
   `Refined Dist Threshold(km)` / `Time diff(s)` = 2,55/153, 2,60/156, 2,47/148, 2,38/143, 2,53/152,
   todos 0,0166 a 0,0167 km/s (1 km por minuto), y `Dist Thresh(km)` es el triple (7,7; 7,8; 7,4;
   7,2; 7,6): 0,050 km/s, o sea 3 km por minuto (180 km/h).
6. La comparación con la historia sólo aparece en el cuadro que sigue a uno con rasgo publicado.
   A las 20:20:00 (el cuadro siguiente a la primera detección) hay dos objetos comparados, a 28,5 y
   29,9 km, ninguno califica, y de 20:22:30 a 20:45:00 no hay ninguna comparación impresa. La
   cadena se cortó con un solo cuadro sin objeto cercano. La detección de las 20:47:30 es un
   nacimiento nuevo en los archivos de evento (`ID-2025-07-02T20:47:43Z_0001`), aunque la alerta la
   clasifica `Old Volcanic Feature` con `History Index: 1, Time Diff(s): 1800`.

## 3. Hipótesis inicial (H28-0)

VOLCAT publica un objeto que su píxel no ve por dos puertas que no miran la probabilidad del píxel:

- **Puerta de nacimiento (pluma o bocanada anclada):** un objeto pegado a un volcán de la base
  (a uno o dos píxeles del cráter) se publica si su contraste espacial contra el entorno pasa la
  prueba detallada y si todos sus píxeles muestran tendencia temporal respecto de los cuadros
  anteriores. Es una regla de forma, lugar y cambio en el tiempo, no de firma espectral de ceniza.
- **Puerta de seguimiento:** en el cuadro siguiente a uno con rasgo publicado, cualquier objeto
  espectral que esté a menos de 3 km por minuto transcurrido del rasgo anterior hereda la
  publicación, con los filtros de ruido, emisividad y tamaño apagados. Si en un cuadro no hay
  objeto dentro de esa distancia, la cadena se corta y hay que volver a pasar por la puerta de
  nacimiento.

Para Chillán la hipótesis predice que la gran mayoría de los 60 cuadros son de seguimiento (su hora
de primera detección es anterior a la propia) y que sólo unos pocos son nacimientos. Lo que no
cuadra desde ya: la cadena de Chillán del 14-11 que nace a las 16:30 sigue viva a las 19:00 con un
cuadro faltante a las 17:10, y en Kirishima un cuadro sin objeto cercano cortó la cadena. O el
cuadro de las 17:10 existió y no está en el listado del servidor, o hay un mecanismo de relleno
(`FILL_MISSING_CLD_ANALYSIS`) que Kirishima no ejercitó.

## 4. Elección de datos de ajuste y de prueba (antes de mirar las salidas de prueba)

- **Ajuste (donde se deduce la regla):** Kirishima completo (25 cuadros) y Fuego de 14:01 a 18:46 UTC
  (los primeros 20 cuadros).
- **Prueba 1 (logs con la decisión impresa):** Fuego de 19:01 a 23:46 UTC (los últimos 20 cuadros) y
  Mauna Loa completo (10 cuadros, otro volcán, otro satélite, otra cadencia).
- **Prueba 2 (sólo archivos de evento):** Chillán, los 60 cuadros. De Chillán ya vi lo que dice 1.3.

El criterio de éxito se escribe en `01_REGLA_Y_CRITERIO.md` y se commitea antes de abrir un solo log
de la prueba 1 o un segundo archivo de Chillán.
