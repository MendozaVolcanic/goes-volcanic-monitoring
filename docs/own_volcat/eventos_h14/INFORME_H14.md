# H14: anatomía de los 60 archivos de evento VOLCAT de Nevados de Chillán (camino C1), 21-11-2026

**Veredicto (regla del criterio): compatible con H14, sin fuerza para sostenerla.** Ninguno de los 4 primeros
cuadros de evento tiene firma total ≥ 0,5 en la mayoría de sus píxeles (0 de 4), y la firma de onda larga no llega a
0,5 en ninguno de los 767 píxeles publicados de los 60 cuadros. Con 4 eventos el resultado es descriptivo.

Criterio, subido antes de abrir ningún NetCDF (commit `b080124`):
`docs/own_volcat/eventos_h14/criterio_H14_2026-11-21.md`. Plan: `docs/own_volcat/PLAN_2026-11-21_LUT_VOLCAT.md`, C1.

## 1. Lo que muestran los archivos, en términos de volcán

**Qué publica VOLCAT de Chillán.** En las tres jornadas con archivo (13, 14 y 18-11) VOLCAT abrió 4 eventos:

| Evento (primera detección) | Tipo | Cuadros | Qué es |
|---|---|---|---|
| 13-11 19:00 UTC | `VCB` | 11 | 5 píxeles sobre el cráter en el primer cuadro; después, durante 2 h, **un solo píxel a 6,1 km del cráter**, con tope de 3,76 a 4,05 km (la cumbre está a 3,2 km) |
| 14-11 12:40 UTC | `ASHPLUMEPUFF` | 7 | 1 a 6 píxeles, del cráter a 46 km |
| 14-11 16:30 UTC | `ASHPLUMEPUFF` | 41 | Arranca con 3 píxeles a 2,8 a 6,2 km del cráter, crece hasta 67 píxeles y se desprende hacia el ESE; el último cuadro (23:40) está a 61 a 82 km |
| 18-11 10:10 UTC | `ASHPLUMEPUFF` | 1 | 4 píxeles a 15 a 20 km del cráter |

Son objetos muy chicos: mediana de 11 píxeles por cuadro (1 a 67), casi siempre de uno o dos píxeles de ancho.
Sólo 5 de los 60 cuadros tienen algún píxel interior (rodeado por otros del objeto).

**Lo que VOLCAT dice de su propia firma espectral.** El archivo trae, para cada píxel publicado, un indicador de
firma espectral de ceniza entre 0 y 1, calculado con todos los canales y otro sólo con los de onda larga (8,5 a
12 µm). Leído con el supuesto de que 1 es firma fuerte (la escala no está documentada):

- **En onda larga no hay firma en ningún lado.** De 767 píxeles, el 99,35 % queda bajo 0,05 y el máximo es 0,42.
  Eso incluye el arranque de cada evento, los píxeles pegados al cráter y la nube desprendida.
- **El arranque tampoco tiene firma.** En los cuatro primeros cuadros, la firma total máxima es 0,0004, 0,046, 0,020
  y 0,67 (este último, 1 de 4 píxeles del 18-11, al amanecer), y la de onda larga no pasa de 0,0032.
- **No hay un núcleo con firma.** Los 388 píxeles a ≤ 10 km del cráter tienen mediana 0,0008 y el 87 % está bajo
  0,05. VOLCAT no detecta un centro con señal para luego arrastrar el resto: el centro tampoco la tiene.
- **La firma total alta aparece sólo con sol bajo.** El 12 % de los píxeles tiene firma total ≥ 0,5, pero se
  concentra en el evento largo del 14-11 cuando el sol se pone: 3 % con el sol alto (cenital < 50°), 10 % entre 50 y
  70°, 29 % entre 70 y 85°, y **0 % de noche** (≥ 85°). La de onda larga es 0 % en los cuatro tramos.
  INFERENCIA: lo que agrega el indicador total sobre el de onda larga es un canal con componente solar
  (probablemente 3,9 µm de día), que no es firma de absorción de ceniza en el infrarrojo térmico.

**Calor y rayos.** Ningún rayo en los 60 cuadros, en ninguna de las cuatro redes (ENI, WWLLN, GLD360, GLM), ni en el
objeto, ni a 20 km del cráter, ni en el entorno. El campo de calor sólo viene lleno en tres cuadros, que son los
primeros de los eventos del 13, del 14 a las 12:40 y del 18-11: actividad térmica de ≥ 10 MW el mismo día. En los
otros 57, incluido el primero del evento de las 16:30, viene vacío. INFERENCIA: el campo se llena al abrir el
evento, y en 3 de 4 aperturas el volcán tenía calor detectado por satélite ese día.

**Lectura.** Los cuatro eventos se abren y se sostienen sin firma espectral de ceniza en onda larga, según el
propio VOLCAT. El del 13-11 es de tipo `VCB` (por inferencia de la búsqueda, el detector de crecimiento de nube
volcánica de Pavolonis 2018) y se sostiene dos horas en un único píxel junto al cráter. Lo que mantiene vivo el
objeto no es la firma del píxel: es el objeto, el seguimiento y, al abrir, el volcán con calor. Esto calza con las
quince pruebas espectrales nuestras que no separaron la pluma del mismo lugar sin pluma. **Para C3 cambia el
blanco:** no hay un núcleo con firma que buscar; si las tablas reales de VOLCAT dan probabilidad alta en estos
píxeles, tendrá que venir de otra parte del clasificador, no de la firma que VOLCAT mismo informa.

**Ojo con la georreferencia de nuestras huellas.** En el 14-11, la huella que decodificamos del PNG cae en la
mediana **1 fila al sur y 1 columna al este** de los píxeles que VOLCAT publica (≈ 2,8 km al S y 2,1 km al E, unos
3,5 km). Sin corregir ese desfase coinciden poco (IoU mediano 0,19; sólo el 30 % de los píxeles de VOLCAT cae en
nuestra huella); corrigiéndolo sube a 0,42. Además, el PNG y el archivo de evento no muestran lo mismo: en el primer
cuadro de cada uno de los dos eventos del 14-11 el PNG casi no tiene ceniza junto al cráter (1 y 0 píxeles en la
caja, contra 4 y 3 del evento). Para objetos de uno o
dos píxeles de ancho, un píxel de corrimiento significa que buena parte de lo que hemos llamado "huella" era el
terreno vecino. Eso no crea una firma que VOLCAT mismo no ve, pero sí diluyó cada comparación que hicimos.

## 2. Método

- **Datos:** los 60 NetCDF y JSON de evento VOLCAT GOES-19 v3r4 de `D:\goes_notas\busqueda_2026-11-20\volcat_eventos_357070\`
  (sólo lectura; condición de uso del `LEEME.md`: investigación interna, no se suben). En el repo van sólo números
  derivados por cuadro, sin grillas.
- **Píxel publicado:** `event_idx` ≥ 0. Todos los cuadros traen un solo objeto. Evento = `event_id` del JSON
  (lleva la hora de primera detección); primer cuadro = el que empieza a la hora de primera detección (los 4
  eventos lo tienen en disco).
- **Firma:** `ash_spectral_signature_strength` y `..._lwir_only`; "~0" < 0,05, "alta" ≥ 0,5.
- **Cráter:** (−36,863; −71,377), distancia por haversine desde la posición nominal del píxel.
- **Borde e interior:** distancia de tablero al píxel no publicado más cercano (1 = borde).
- **Anillo:** píxeles a 3 a 6 px de la huella, sin píxeles publicados.
- **Georreferencia:** el PNG Ash_Height de `Chile_Central_2_km` del mismo minuto, decodificado con la misma
  clasificación que `docs/own_volcat/reproducir_volcat/scripts/huella_png.py`, muestreado en la latitud y longitud
  de cada píxel del archivo de evento. Comparación en la caja de la huella ampliada en 10 px; desfase de −5 a +5
  filas y columnas que maximiza el IoU. PNG del 14-11 desde `D:\goes_cache\h13\png\` (sólo lectura).

### Desviaciones del criterio (dichas, no escondidas)

1. **`feature_age` es un escalar por objeto, no por píxel** (lo supe al abrir el primer archivo). "Píxeles nuevos"
   no se puede definir por píxel: el único conjunto con `feature_age` = 0 es el primer cuadro entero, que es lo
   que ya mide la regla. Probé `residence_time` (por píxel) como sustituto y no sirve: su mínimo crece con la edad
   del evento (0,17 h a los 10 min, 9,3 h al final), así que no marca incorporaciones; sólo un píxel fuera del
   primer cuadro tiene 0 (14-11 22:40, firma total 0,999, onda larga baja). Va en el CSV (`sig_rtmin_*`), no decide.
2. **Borde contra interior no se puede leer:** los objetos son de 1 a 2 píxeles de ancho y sólo 5 cuadros tienen
   interior. Va en el CSV.
3. **Contraste contra el anillo, separado por posición** (exploratorio, `h14_tablas.py`): un objeto en la cumbre
   tiene el anillo sobre terreno más bajo y tibio, y la diferencia mide la altura del terreno, no la pluma.
4. **Del 13 y del 18-11 no hay PNG en disco** (ni en
   `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\Goes\data\raw\volcat_validacion\`, que sólo tiene el
   08-11, ni en las cachés). La georreferencia es sólo del 14-11. No se bajó nada.

## 3. Números

Salida cruda en `docs/own_volcat/eventos_h14/resultados/`: `por_cuadro.csv` (60 filas, 99 columnas),
`por_evento.csv`, `resumen.json`, `georef.csv`, `georef_resumen.json`, `tablas_informe.json`.

### 3.1 Primer cuadro de cada evento (decide)

| Evento | Tipo | Píxeles | A ≤ 10 km | Firma total: mediana / máx / fracción ≥ 0,5 | Onda larga: máx |
|---|---|---|---|---|---|
| 13-11 19:00 | VCB | 5 | 5 | 0,0000 / 0,00036 / 0 | 0,00003 |
| 14-11 12:40 | ASHPLUMEPUFF | 4 | 2 | 0,00102 / 0,04568 / 0 | 0,00033 |
| 14-11 16:30 | ASHPLUMEPUFF | 3 | 3 | 0,00026 / 0,01998 / 0 | 0,00322 |
| 18-11 10:10 | ASHPLUMEPUFF | 4 | 0 | 0,06772 / 0,66529 / 0,25 | 0,00248 |

Primeros cuadros con firma total ≥ 0,5 en la mayoría de los píxeles: **0 de 4**. Condición de falsación: no se
cumple. Núcleo con firma (mediana a ≤ 10 km ≥ 0,5 y resto < 0,05): en 0 de 4.

Resto de cada evento (cuadros siguientes juntos): 13-11, 10 píxeles, firma total máxima 0,051; 14-11 12:40, 18
píxeles, máxima 0,0022; 14-11 16:30, 725 píxeles, mediana 0,0017, p90 0,770, fracción ≥ 0,5 = 0,128, onda larga
máxima 0,417 y fracción ≥ 0,5 = 0.

### 3.2 Todos los píxeles publicados (60 cuadros)

| Conjunto | Píxeles | Mediana | p90 | Máximo | ≥ 0,5 | < 0,05 |
|---|---|---|---|---|---|---|
| Firma total | 769 | 0,00134 | 0,749 | 1,0 | 12,2 % | 78,3 % |
| Firma de onda larga | 767 | 0,00045 | 0,0033 | 0,417 | 0 % | 99,35 % |
| Firma total a ≤ 10 km del cráter | 388 | 0,00079 | 0,121 | 1,0 | 5,2 % | 86,6 % |

Firma total ≥ 0,5 según el cenital solar del objeto (onda larga: 0 % en todos):

| Cenital solar | Cuadros | Píxeles | Firma total ≥ 0,5 |
|---|---|---|---|
| < 50° | 32 | 260 | 3,5 % |
| 50 a 70° | 16 | 133 | 9,8 % |
| 70 a 85° | 8 | 247 | 29,2 % |
| ≥ 85° (noche) | 4 | 129 | 0 % |

### 3.3 BT11 y BTD 11 − 12, huella contra anillo de 3 a 6 px

| Objeto | Cuadros | BTD huella − anillo, mediana (rango) | BT11 huella − anillo, mediana (rango) |
|---|---|---|---|
| Pegado al cráter (distancia mínima ≤ 10 km) | 51 | −1,26 K (−2,25 a −0,68) | −15,8 K (−22,4 a −2,4) |
| Desprendido (distancia mínima ≥ 20 km) | 7 | −0,86 K (−1,19 a −0,76) | +0,85 K (−7,5 a +3,6) |

La BTD de la huella nunca es negativa en la mediana de ningún cuadro (fracción de píxeles con BTD < 0: mediana 0).
En el cráter, los 16 K de BT11 más fría son la cumbre (3,2 km) contra el terreno más bajo del anillo: ese contraste
no aísla la pluma. En la nube desprendida, con BT11 igual al entorno, la BTD baja ~0,9 K sin llegar a negativa; es
lo mismo que midió la búsqueda en el cuadro del 14-11 23:00, ahora en 7 cuadros.

### 3.4 Calor, rayos, altura

- Rayos: 0 en los 60 cuadros, en las 4 redes y en los 3 ámbitos (objeto, 20 km del cráter, entorno).
- Calor: `time_since_0MW` = `time_since_10MW` = 0 días, y 100 y 1.000 MW sin dato, en 13-11 19:00, 14-11 12:40 y
  18-11 10:10; vacío en los otros 57.
- Altura mediana del objeto: 2,8 a 11,4 km en los 55 cuadros con altura; 44 de ellos entre 3,2 y 4,5 km (de 0 a
  1,3 km sobre la cumbre).

### 3.5 Georreferencia (14-11, 48 cuadros con PNG; 40 con huella de ≥ 5 píxeles)

| Medida (mediana en los 40 cuadros) | Valor |
|---|---|
| Desfase que maximiza el IoU (PNG respecto del evento) | 1 fila al sur, 1 columna al este |
| IoU a desfase 0 | 0,19 |
| IoU en el mejor desfase | 0,42 |
| Píxeles del evento que caen en ceniza del PNG, posición nominal | 30 % |
| Lo mismo con la posición corregida por paralaje del archivo | 16 % |
| Píxeles del PNG (en la caja) que son del evento, desfase 0 | 40 % |

Reparto del desfase (filas, columnas) en los 40 cuadros: (1, 1) en 18, (1, 2) en 10, (0, 1) en 5, (2, 2) en 3,
(0, 0) en 2, (2, 1) y (1, 3) en 1 cada uno. Cerca del cráter una fila mide 2,8 km (N-S) y una columna 2,1 km
(E-O); el píxel del PNG mide 2,2 × 1,8 km. 5 cuadros con PNG no tienen ceniza en la caja (12:50, 13:10, 13:20,
13:30 y 16:30). Que la posición corregida por paralaje calce peor indica que el PNG se dibuja en la posición
nominal; el desfase es del sentido contrario al de la paralaje (que movería la nube hacia el norte), así que es más
probable que venga de nuestra proyección del PNG que de VOLCAT. **No está resuelto.**

## 4. Límites

- **Escala de la firma sin documentar.** Todo lo de arriba supone 1 = firma fuerte. Lo apoyan la BTD positiva de la
  huella y que en la muestra NCCF de Kamchatka los píxeles `invalid_filled` caen bajo 0,05. Si el autor dijera que
  la escala va al revés, H14 se falsa.
- **4 eventos, 3 jornadas.** El 13-11 es en la práctica un píxel; el 18-11 es un cuadro. La retención de SSEC es de
  ~7 días; para sostener H14 hacen falta ≥ 10 eventos (C5, sólo con autorización de Pavolonis).
- **Firma no es probabilidad.** VOLCAT no publica la probabilidad de píxel ni de objeto. Esta prueba dice qué firma
  informa VOLCAT, no por qué regla decide; eso es C3 con las tablas.
- **El desfase de la georreferencia es de un solo día** (14-11) y de objetos chicos, donde un píxel pesa mucho.

## 5. Qué cambia

1. **C3:** el blanco no es un núcleo con firma. Usar `event_idx` como huella verdadera, no el PNG.
2. **Nuestras huellas del PNG:** revisar la proyección de `huella_png.py` (origen y convención de centro de píxel)
   contra `event_idx` antes de reutilizarla; es una tarea aparte, no se tocó aquí.
3. **Correo a Pavolonis (C4):** preguntar el sentido de la escala de `ash_spectral_signature_strength`, qué canales
   agrega la firma total sobre la de onda larga, y qué condición abre y sostiene un evento `VCB` y `ASHPLUMEPUFF`
   cuando la firma es ~0.

## Reproducir

```bash
python -I docs/own_volcat/eventos_h14/scripts/h14_eventos.py
```

```bash
python -I docs/own_volcat/eventos_h14/scripts/h14_georef.py
```

```bash
python -I docs/own_volcat/eventos_h14/scripts/h14_tablas.py
```

Rutas por variable de entorno: `H14_EVENTOS` (carpeta de eventos) y `H14_PNG` (carpetas de PNG separadas por `;`).
