# Hoja de ruta: pasadas de alta resolución como verdad de terreno periódica para los 43 volcanes

Fecha: 23-11-2026 (S20b). Propuesta, no implementada. Se apoya en la prueba 1 de S20b
(`s20b_verdad_alta_res/INFORME.md`): con la huella de Sentinel-2 o Landsat puesta en la grilla de GOES-19 con su
paralaje, una pluma que llena 18 a 43 % de un píxel deja una firma medible en la diferencia 11 − 12 µm (cerca de
−1 K) y en la BT11 de ese píxel, en dos mañanas despejadas de Chillán. La prueba 2 (ventana partida a 100 y 70 m)
está pendiente de credenciales; esta hoja de ruta vale para la parte que no depende de ella.

## 1. Por qué vale la pena

Hasta S20 toda la verdad sobre dónde está una pluma venía de VOLCAT (que la publica por seguimiento, H28), de la
dirección del REAV (un octante leído desde una cámara, que el 25-10 apuntaba al lado equivocado) o del GFS. Una pasada
fina despejada da, sin ninguna de esas tres, **la huella, el ancho, la dirección y la altura** (por la sombra) de la
pluma a una hora conocida. Con eso se puede:

1. medir el límite real de GOES en cada volcán (qué fracción de píxel y qué contraste se ven), en vez de suponerlo;
2. juntar, volcán por volcán, una muestra de "pluma sí / pluma no" con hora exacta para validar cualquier detector
   propio o VOLCAT;
3. corregir direcciones de pluma de los boletines cuando el satélite fino dice otra cosa.

## 2. Qué hay disponible y cada cuánto

| Sensor | Resolución útil | Pasada sobre Chile central | Acceso |
|---|---|---|---|
| Sentinel-2 A, B, C | 10 a 20 m, reflectancia | cada 2 a 5 días, 14:40 a 14:55 UTC | Element 84 (sin cuenta) |
| Landsat 8 y 9 | 30 m reflectancia, 100 m térmico | cada 8 días combinados, 14:35 UTC | Planetary Computer (L2, sin cuenta); B11 de nivel 1 pide Earthdata (HLS) o USGS |
| ECOSTRESS | 70 m, 3 a 5 bandas térmicas | irregular (órbita de la estación espacial), a cualquier hora | Earthdata |

Todas son de media mañana salvo ECOSTRESS. La tarde, cuando VOLCAT más dibuja en Chillán, queda sin verdad fina.

## 3. Cómo se consume, respetando la regla del workspace

La regla: nunca leer el `data/` de otro proyecto por ruta; consumir su salida publicada.

- **Landsat-v1** publica por volcán `docs/landsat/<volcán>/<fecha>_{RGB,SWIR,THERMAL}.png` y el catálogo
  `docs/fechas_disponibles_landsat.json` (fechas con escena por volcán; para Chillán, 8 fechas del 01-10 al 18-11).
- **Copernicus-v1** publica `docs/fechas_disponibles_copernicus.json` (Sentinel-2 por volcán; para Chillán, 19
  fechas del 09-10 al 20-11, también con una entrada `Nevados_de_Chillan_Crater_Nicanor`).

Los PNG publicados son renders, no reflectancia: sirven para mirar, no para medir. Por eso la propuesta usa los dos
catálogos publicados **como disparador** (qué volcán tiene pasada nueva y en qué fecha) y lee la reflectancia de los
archivos públicos (Element 84 y Planetary Computer), como hace `s20b_preparar.py`. En CI se copia el patrón
`sparse-checkout` de `Copernicus-v1/.github/workflows/change_analysis.yml`, trayendo sólo los dos JSON.

## 4. Pasos, cada uno con criterio antes de medir

1. **Catálogo de verdad fina (sin GOES).** Un workflow diario que, para cada volcán con fecha nueva en los dos
   catálogos, corra la máscara de `s20b_preparar.py` (referencia compuesta anterior, NDSI, sombra) y guarde por
   volcán y fecha: área sobre nieve, centroide, azimut, ancho, altura por sombra y fracción de nieve observable. Sólo
   números, en un JSON publicado. Se lee por rangos HTTP sólo la ventana de 40 km, sin bajar escenas completas
   (el volumen por escena no lo medí). Riesgo conocido: la regla sólo ve pluma sobre nieve; en verano y en el norte, sin nieve, habrá que
   probar otra (contraste en 2,2 µm contra roca).
2. **Validación de la máscara.** Antes de usarla a escala, revisar a ojo 30 escenas de 5 volcanes (con y sin
   actividad) y anotar falsos positivos (borde de nieve, nubes orográficas) y falsos negativos. Criterio escrito: la
   máscara sirve si los falsos positivos son menos de 1 km² por escena despejada sin actividad.
3. **Firma GOES por pasada.** Repetir la prueba 1 de S20b en cada pasada con pluma: D y p de M1 y M2 en el cuadro más
   cercano, con días base despejados por E1 y el nulo espacio-temporal. Registrar también lo que VOLCAT dibujó en ese
   cuadro. Con 20 o más pasadas con pluma se puede estimar, por fracción de píxel, la probabilidad de ver la firma.
4. **Detector anclado al cráter, prospectivo.** Si el paso 3 confirma la firma en otros eventos, probar un detector
   que no necesite la huella: la anomalía de M1 de los píxeles del anillo de 2 a 8 km del cráter contra su propia
   línea base despejada, con registro prospectivo (como `h24_verano/REGISTRO_PROSPECTIVO.md`) y validado contra las
   pasadas finas siguientes.
5. **ECOSTRESS como verdad de tarde.** Con credenciales vigentes, agregar ECOSTRESS L1CT (70 m) cuando pase sobre un
   volcán activo, con la prueba 2 de S20b como plantilla.

## 5. Qué hace falta de Nicolás

- Un token de Earthdata vigente en una variable de entorno local (el `_netrc` tiene el par vencido) y decidir si se
  usa la cuenta USGS M2M de Landsat-v1 para el nivel 1.
- Decidir si el catálogo de verdad fina vive en este repo o en Copernicus-v1 (que ya publica por volcán y ya lee
  Landsat-v1).
- Las imágenes de cámara del OVDAS en los minutos de las pasadas (lista en TER-06 de S19i): amarrarían cámara,
  satélite fino y GOES en el mismo minuto.
