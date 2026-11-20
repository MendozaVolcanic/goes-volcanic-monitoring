# Criterio H9: ¿las detecciones VOLCAT ancladas al cráter de Chillán coinciden con calor a 3,9 µm o con rayos GLM?

Escrito y commiteado el 19-11-2026 **antes de calcular el primer número**. Las descargas (C07 y C14 por
ventana, historia GLM de Lightning-v1) corrieron en paralelo a la escritura, sin mirar valores.

## 1. Pregunta y física

VOLCAT tiene un módulo propio de actividad térmica en los volcanes conocidos, a 3,9 µm, y según su ATBD
(Pavolonis et al. 2025, v1.0, §2.2) "el monitoreo de la actividad térmica influye en los algoritmos de
detección de nubes volcánicas que vienen después". La presentación CDR de 2022 (diapositivas 82 y 83,
leídas por otro agente, no verificadas) agrega rayos GLM como contexto. Si VOLCAT afloja sus umbrales
cuando ve calor o rayos en Chillán, eso explicaría por qué dibuja plumas sin señal IR propia sólo ahí.
H9 pregunta si las detecciones coinciden con esas dos señales, medidas por nosotros.

**Calor.** Material incandescente, un domo o una colada que ocupan una fracción pequeña del píxel de 2 km
suben mucho más la BT de 3,9 µm (C07) que la de 11,2 µm (C14), porque a 3,9 µm la radiancia de Planck crece
mucho más rápido con la temperatura. La señal es BT7 − BT14 en el cráter **comparada con un anillo de
fondo en la misma escena**, no la BT7 sola: así se descuenta el estado de la atmósfera y del suelo de ese
cuadro. De día C07 suma reflexión solar, que depende del suelo (nieve o roca), así que la noche y el
crepúsculo deciden y el día va como extensión. Una nube sobre el cráter apaga la señal: esos cuadros se
cuentan aparte como "cráter no visible", no como fríos.

**Rayos.** GLM detecta destellos ópticos desde arriba de la nube. Una pluma chica (columnas de 0,4 a
2,4 km sobre el cráter según los REAV) rara vez electrifica lo bastante para que GLM la vea; un destello
cerca del cráter también puede ser tormenta. Se mide igual, porque la pregunta es si lo que VOLCAT pudo
usar estaba ahí.

**Dato de contexto leído antes de medir** (RAV-EAV3-26M10Q2 y REAV de SERNAGEOMIN, resumen en
`C:\Users\nmend\AppData\Local\Claude-Data\claude_pzs8sxrjxfjjc\side-session-notes\local_1055cba6-2c2f-4aa4-9119-82691ee2ed22\busqueda_2026-11-19_D_cronologia_chillan.md`):
incandescencia y piroclastos incandescentes la madrugada del 27-10; al 30-10, colada de lava de ~880 m que
avanza ~20 m/día desde el costado occidental del cráter Nuevo. Es decir, **es esperable una fuente de calor
casi permanente**. Por eso el criterio separa dos preguntas: (a) si el calor marca **el momento** de cada
detección (nivel cuadro) y (b) si el calor está presente como **contexto** durante el periodo (nivel
volcán), que es lo que haría que VOLCAT tratara distinto al cráter todo el tiempo.

## 2. Datos

- **Cuadros VOLCAT**: inventario ya hecho por la prueba β(7,3/11) (`docs/own_volcat/beta73/scripts/inventario.py`,
  regla de anclaje de `paso4_analisis.py`), 4.184 cuadros del sector `Chile_Central_2_km` del 20-10 11:50 UTC
  al 19-11 12:00 UTC. Caché: `C:\Users\nmend\AppData\Local\Temp\claude\f4710304fa6a9a5b\6cc950d4-5fd7-4e45-a0af-882008093b90\scratchpad\b73\inv_local.json` e `inv_new.json`.
  - **Positivo**: cuadro con barra de colores legible, al menos un objeto de 4 a 500 px del PNG que toca el
    disco de 10 km del cráter, y sin manto (ningún objeto > 5 % del mapa ni sistema > 500 px a ≤ 50 km).
    Se incluyen el 28 y el 29-10: H9 no nació en esos días.
  - **Negativo limpio**: barra legible, sin manto, ningún píxel de ceniza a ≤ 50 km, y ningún cuadro con
    ceniza a ≤ 50 km o manto en ±60 min (misma regla `_limpio` de β73).
- **C07 y C14**: ABI L1b RadF de GOES-19 leídos por ventana (83 × 94 píxeles de 2 km, la del caché del
  detector, `window.json`), un scan por cuadro del inventario. BT con los coeficientes Planck de cada NetCDF.
  Se descartan píxeles con DQF > 1. Script: `scripts/fetch_c07.py`.
- **Rayos**: salida publicada de Lightning-v1 (repo público `MendozaVolcanic/Lightning-v1`). Su archivo
  `docs/data/glm_latest.json` se reescribe y commitea cada ~5 min con los destellos GLM-L2-LCFA de los
  últimos 15 min a ≤ 100 km de cada volcán; la historia del archivo en git es la serie. Su historial mensual
  `datos/alert_history_*.csv` es sólo WWLLN y termina en octubre, y los `docs/datos/scan_*.json` se purgan a
  los 14 días, por eso se usa la historia de `glm_latest.json`. Script: `scripts/fetch_glm_lightning_v1.py`.
  - Dos rarezas vistas en esa salida **antes de medir**, que el método rodea: (1) Lightning-v1 ubica
    "Nevados de Chillan" en −37,411, −71,352, que son las coordenadas de Antuco, ~61 km al sur del cráter.
    Un destello a ≤ 30 km del cráter real queda a ≤ 91 km de ese centro, dentro de su radio de 100 km, así
    que se recalcula la distancia al cráter real y no se usan sus conteos "inner/outer". (2) El campo `time`
    de cada destello no cuadra con la hora del scan (horas de diferencia; parece el desfase entero sin
    escalar), así que **no se usa**: cada destello se fecha con la intersección de las ventanas
    [scan − 15 min, scan] de todas las versiones que lo listan. Un destello se identifica por (lat, lon,
    energía, área).

## 3. Geometría y medidas

- Coordenadas y alturas del catálogo del proyecto (`src/volcanos.py`): cráter de Chillán −36,86, −71,38,
  3.212 m (el mismo punto de toda la serie). Controles: **Antuco** (−37,41, −71,35, 2.979 m) y **Nevado de
  Longaví** (−36,19, −71,16, 3.242 m), cumbres altas dentro de la misma ventana y sin actividad reportada en
  el periodo.
- **Paralaje**: ABI L1b está navegado al elipsoide, así que una cumbre de h km aparece 0,93·h km más al sur.
  El centro de cada zona se corre 0,93 × altura de cumbre hacia el sur (alturas de arriba).
- Zona de cráter Z: píxeles a ≤ 6 km del centro corrido. Anillo R: píxeles a 8 a 14 km (≈ 4 a 7 píxeles).
- **Anomalía térmica A** (K) = máx sobre Z de (BT7 − BT14) − mediana sobre R de (BT7 − BT14).
  Secundaria (no decide): A7 = máx_Z BT7 − mediana_R BT7.
- **Cráter visible**: mediana de BT14 en Z ≥ Vref − 4 K, con Vref = mediana de los 3 valores más altos de
  esa misma mediana entre los cuadros del mismo minuto UTC en ±7 días (cielo despejado empírico, como en
  las pruebas anteriores). Sensibilidad (no decide): 2 K y 8 K. Cada sitio (Chillán, Antuco, Longaví) tiene
  su propia visibilidad.
- **Estratos** por cenit solar en Chillán: **N** (noche y crepúsculo, cenit ≥ 80°) decide; **D** (cenit < 80°)
  es extensión.

## 4. Pruebas y umbrales

### H9a, calor y momento de la detección (decide la parte "calor")

Para cada positivo con cráter visible, los controles son **todos** los negativos limpios con cráter visible
del **mismo minuto UTC** en otros días dentro de ±10 días (así quedan pareados por hora del día y estado del
cielo). AUC = promedio, sobre los positivos, de la fracción de sus controles con A menor (empates cuentan
0,5). IC 95 % por remuestreo de **días** de positivos con reemplazo (2.000 réplicas). El mismo cálculo, con
los mismos pares de minuto y día, se repite con A medido en Antuco y en Longaví (control: el efecto no debe
aparecer ahí).

En el estrato N:
- **Apoya**: AUC ≥ 0,70, límite inferior del IC ≥ 0,55, AUC por día > 0,5 en al menos dos tercios de los
  días con positivos visibles, y en los dos controles AUC ≤ 0,60 con AUC de Chillán − máx(AUC control) ≥ 0,15.
- **Se falsa**: AUC ≤ 0,60, o el efecto aparece igual en un control (máx(AUC control) ≥ AUC de Chillán − 0,05).
- **No concluyente**: todo lo demás, y siempre que haya menos de 8 positivos visibles o menos de 3 días.

El estrato D se informa con las mismas reglas, rotulado como extensión; no cambia el veredicto.

### H9b, calor como contexto (descriptivo, no cambia el veredicto de H9a)

Umbral T99 = percentil 99 de A en Antuco y Longaví juntos, sobre todos sus cuadros N visibles del periodo
(nivel de falsa alarma de una cumbre sin actividad). F = fracción de cuadros N visibles de Chillán con
A > T99, por noche. **Contexto encendido** si F ≥ 0,5 en al menos el 75 % de las noches con ≥ 6 cuadros N
visibles. Se informa además F en noches que preceden un día con positivos contra las demás.

Lectura declarada de antemano: si H9a se falsa y el contexto está encendido, el calor puede explicar a lo
más un trato especial permanente del cráter, no el momento de cada detección. Si el contexto está apagado
con nuestra medida, sólo queda que el módulo térmico de VOLCAT sea más sensible que el nuestro, cosa que no
podemos probar.

### H9c, arranque de cada tramo (secundaria, no decide sola)

Tramo = positivos consecutivos con huecos ≤ 30 min. A' = A − mediana de A en los negativos limpios
visibles del mismo minuto UTC en ±7 días (quita el ciclo diario). Hay "subida de calor" en un arranque t0
si el máximo de A' en los cuadros visibles de [t0 − 60 min, t0] supera el percentil 95 de A' en todos los
negativos limpios visibles de Chillán. Tasa base: la misma regla aplicada a cada negativo limpio visible
como si fuera un arranque. Se dice que los arranques coinciden con calor si la fracción con subida es
≥ 50 % y ≥ 2 veces la tasa base; que no coinciden si queda a ≤ 10 puntos de la tasa base.

### H9d, rayos (decide la parte "rayos")

Ventana de cada cuadro: [t − 30 min, t + 10 min], es decir el cuadro de 10 min y los tres anteriores. Un
cuadro tiene rayo si al menos un destello a **≤ 30 km del cráter real** tiene su intervalo de hora dentro
de la ventana. Sensibilidad: ≤ 20 km. **Cobertura**: la ventana está cubierta si la unión de las ventanas
[scan − 15, scan] de las versiones sin `error` la cubre sin huecos de más de 2 min. Sólo cuentan cuadros
cubiertos. Controles: negativos limpios cubiertos del mismo minuto UTC en ±10 días; IC por remuestreo de días.

- **Apoya**: ≥ 30 % de los positivos cubiertos con rayo, tasa en positivos ≥ 3 veces la de los controles, y
  límite inferior del IC de la diferencia > 0.
- **Se falsa**: < 5 % de los positivos cubiertos con rayo.
- **No concluyente**: lo demás, o cobertura < 80 % de los positivos.

El día no se separa: GLM no depende del sol para detectar (sí baja algo su eficiencia de día).

**Contraste contra la salida cruda (obligatorio antes de usar los conteos).** En al menos dos horas
(una con destellos a ≤ 100 km de Chillán según la serie, si la hay, y una de un tramo con positivos) se
bajan los archivos GLM-L2-LCFA de `noaa-goes19` y se cuentan los destellos a ≤ 100 km del cráter real. Si
la serie de Lightning-v1 difiere en más del 10 % en alguna de esas horas, no se usa: se rehace H9d desde S3
dentro de las ventanas de positivos y controles.

## 5. Qué se informa siempre

- Escenas resueltas: cuadros con C07 y C14 leídos, cuántos con cráter visible por estrato, positivos y
  controles efectivos por estrato y por día. Cuadros sin scan en S3 o con falla de lectura, aparte.
- Que las coordenadas de control y las alturas de cumbre son aproximadas (zona de 6 km para tolerarlo).
- Que nuestra medida de calor a 2 km no es el módulo térmico de VOLCAT, cuyo umbral no es público.

## 6. Lo que no se toca

Sólo docs y scripts de análisis en `docs/own_volcat/calor_rayos/` y una fila en `docs/paper/REGISTRO_PAPER.md`
§3. Nada de código de la app, ni `POR_QUE_VOLCAT_VE_Y_NOSOTROS_NO.md`, ni `docs/own_volcat/direccion_pluma/`.

## 7. Enmienda 1 (19-11, antes del primer número): orden de descarga y corte

La descarga de C07 y C14 resultó limitada por el enlace hacia S3 (unos 0,7 MB/s sumando conexiones, 34 KB/s
y 8 s de latencia por conexión medidos con `curl`), y los NetCDF de ABI vienen en tiras comprimidas de 24
filas por 5.424 columnas, así que cada cuadro cuesta ~2,6 MB aunque la ventana sea chica. Se baja por
prioridad, sin mirar valores:

0. Los 100 positivos y los seis cuadros de la hora previa a cada uno (199 cuadros).
1. Los cuadros del mismo minuto UTC de los positivos nocturnos y de crepúsculo, en ±10 días (259).
2. Lo mismo para los positivos de día (727).
3. El resto: primero noche y crepúsculo, después día (2.931).

H9a se calcula cuando terminan los niveles 0 y 1 (estrato N) y 0 a 2 (estrato D). Si el nivel 3 no termina,
**H9b y la tasa base de H9c usan los cuadros disponibles a la hora del corte**, que es una muestra fijada por
el orden de descarga (por fecha dentro de cada nivel), no por los valores; el informe dice cuántas noches
quedaron completas. Ningún umbral cambia.
