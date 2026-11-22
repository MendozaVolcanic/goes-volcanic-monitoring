# H20c (S17): en la pluma de Kirishima, la probabilidad la sube el seguimiento, no la luz. Informe, 22-11-2026

**Veredicto pre-registrado: SEGUIMIENTO (4 de 4 cuadros).** En los cuadros en que VOLCAT publica la pluma de
Kirishima con probabilidad alta, la probabilidad que dan sus propias tablas de día es tan baja como la infrarroja.
Lo que sube la probabilidad es una regla del objeto que actúa desde que VOLCAT lo sigue entre cuadros.

Criterio: `criterio_2026-11-22.md`, commit `9d356ca` (antes de abrir la L2).

## 1. Para geólogo

**Qué se quería saber.** H20b (PR 93) vio que VOLCAT publica la pluma de Kirishima del 02-07-2025 con probabilidad
baja al nacer y alta después, sin que la firma infrarroja de ceniza aparezca. Todo ocurrió al amanecer, así que
quedaban dos explicaciones: que la subieran las tablas de día (luz solar reflejada, que pesa con sol rasante) o que
la subiera el seguimiento del objeto entre cuadros.

**Cómo se decidió.** VOLCAT guarda en su salida L2 tres probabilidades por píxel: la infrarroja, la que suma las
tablas de día y la publicada. Se bajaron sólo la L2 y los logs del objeto de esos cuadros (no el paquete entero) y se
compararon las tres en la huella de la pluma.

**Lo que salió.**

1. **Las tablas de día no suben nada.** En los 4 cuadros con probabilidad publicada alta (20:52 a 21:00 UTC), la
   probabilidad con tablas de día tiene mediana 0,05 a 0,08, igual a la infrarroja. La publicada tiene mediana
   0,64 a 1,00.
2. **La subida empieza cuando VOLCAT empieza a seguir el objeto.** Los dos nacimientos del objeto (20:17 y 20:47)
   aparecen en el log como "Plume/Puff Extraction (SECO+)". Desde 20:50, cada cuadro registra "Temporal selection
   criteria met for ash", y desde ese mismo cuadro la publicada supera a la de día.
3. **El valor publicado es el de `ash_probability_subset`** en 75 a 100 % de esos píxeles. En Fuego (H19) ese
   campo valía casi 1 en la nube convectiva opaca; aquí lleva la probabilidad subida de una pluma tenue. Es decir,
   `subset` es la probabilidad del objeto, no una regla sólo de nube opaca.

**Qué significa para Chillán.** La luz rasante queda descartada como causa de la subida en este evento. VOLCAT tiene
una vía que lleva a probabilidad alta píxeles sin firma espectral, y la activa el seguimiento del objeto. En Chillán,
la probabilidad publicada sube sólo en 5 de 60 cuadros (H20a): o esa vía casi no se activa allá, o se activa con
otro peso. Para saberlo haría falta la L2 de VOLCAT de Chillán, que no es pública; los archivos de evento no traen
`subset`.

## 2. Números (`resultados/por_cuadro.csv`, regla del criterio)

Huella: `event_idx` ≥ 0 del archivo de evento, ubicada en la L2 por latitud y longitud exactas.

| Cuadro (UTC) | Cenit solar | Píxeles | Con P ≥ 0,5 | P publicada | P tablas de día | P infrarroja | P = subset | Clase |
|---|---|---|---|---|---|---|---|---|
| 20:17 | 90,2° | 8 | 3 | 0,988 | 0,397 | 0,988 | 0 % | (de noche, informativo) |
| 20:47 | 84,4° | 9 | 0 | | | | | sin P ≥ 0,5 |
| 20:50 | 83,9° | 11 | 2 | 0,683 | 0,065 | 0,065 | 100 % | SEGUIMIENTO |
| 20:52 | 83,5° | 4 | 3 | 0,642 | 0,048 | 0,048 | 100 % | SEGUIMIENTO |
| 20:55 | 83,0° | 4 | 4 | 0,823 | 0,053 | 0,053 | 75 % | SEGUIMIENTO |
| 20:57 | 82,5° | 5 | 4 | 0,983 | 0,053 | 0,053 | 100 % | SEGUIMIENTO |
| 21:00 | 82,0° | 13 | 9 | 0,997 | 0,083 | 0,083 | 100 % | SEGUIMIENTO |

Medianas sobre los píxeles con P ≥ 0,5. En todos los cuadros con P ≥ 0,5 de día, la publicada supera a la de día
por más de 0,05 en el 100 % de esos píxeles y no es igual a ella en ninguno.

Controles: alineación 100 % en los 7 cuadros; la publicada de la L2 es igual a la del archivo de evento (diferencia
máxima 0); la de día es finita en todos los píxeles y no constante.

Logs (`resultados/logs_conteo.txt`, informativo): "Temporal selection criteria met for ash" 0 veces en 20:17 y
20:47, 1 vez en cada cuadro desde 20:50.

## 3. Lo que podría estar equivocado

- **Un solo evento, en otro sensor (AHI).** La comparación es interna a VOLCAT, así que las tablas de AHI no
  afectan la lectura. Sí impiden decir que en Chillán (ABI, v3r4) la regla pese igual.
- **El cuadro de noche (20:17) no encaja en el patrón simple:** ahí la publicada es igual a la infrarroja (0,988)
  y la de día vale otra cosa (0,397). De noche VOLCAT no usa la de día, como H20a vio en Chillán. No cambia el
  veredicto, que es sobre los cuadros de día.
- **No se identificó la regla de la subida**, sólo cuándo actúa. Los valores no siguen la edad de forma simple
  (0,68, 0,64, 0,82, 0,98, 1,00).
- **Qué log se contó:** el `AN_IN_HN_SN` de cada cuadro. Es un conteo de líneas, no una lectura de la regla.

## 4. Método

Scripts `scripts/h20c_eventos.py` (huella a npz, fuera del repo) y `scripts/h20c_medir.py` (regla del criterio).
Datos: `kirsh_h9-japan_july2025_r20260709-volcat-code-ancil.tar.gz` de `bin.ssec.wisc.edu/pub/volcat/test_cases/`.
Se extrajeron sólo `l2_data/geocatL2` de 20:10 a 21:00 UTC y los logs `geocatASHOBJ` (5,7 GB en
`D:\goes_notas\s17\paquetes\kirsh\`, con la lista completa del paquete en `lista_completa.txt`). Nada del paquete
está en el repo; los `.pkl` no se abrieron.
