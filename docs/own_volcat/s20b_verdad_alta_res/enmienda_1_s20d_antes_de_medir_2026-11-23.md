# S20d: enmienda 1 a la prueba 2 del criterio de S20b, escrita el 23-11-2026 antes de medir

Se commitea y empuja antes de leer cualquier banda térmica de Landsat o ECOSTRESS **de los días del evento** (25-10 y
08-11). Lo leído antes: metadatos y capas de calidad de todos los archivos, y el térmico de dos días sin evento
(17-10 de Landsat 9 y de ECOSTRESS) en el ensayo en seco (§6). Script: `scripts/s20d_ventana_partida.py`, modo `seco`
(salida `resultados/s20d_seco.json`) y modo `medir`.

Por qué hace falta: el criterio §3 dejó abiertas cosas que sólo se podían fijar mirando los archivos (qué bandas trae
ECOSTRESS, en qué unidades viene HLS, qué escena sirve de referencia) y el ensayo en seco mostró que el lugar de la
máscara del 08-11 tiene un sesgo propio en la BTD pareada aunque no haya pluma. Nada de lo que sigue mira el evento.

## 1. Qué traen los archivos (comprobado, no supuesto)

- **HLS L30 v2.0, 25-10 14:34:31 UTC (Landsat 8).** B10 y B11: entero de 16 bits, escala 0,01, en grados Celsius
  (temperatura de brillo al tope de la atmósfera), sin dato = −9999, grilla de 30 m en UTM 19 S (la misma proyección de
  la grilla local de S20b). Se pasan a kelvin (+273,15) y a la grilla local por vecino más cercano.
- **ECOSTRESS L1CT_RAD.** Las cinco bandas traen dato. Ninguna es una combinación de las otras cuatro: ajustando cada
  una con las demás, el residuo es de 0,03 a 0,08 W m⁻² sr⁻¹ µm⁻¹ contra una desviación propia de 0,9 a 1,4 (si una
  banda estuviera rellenada por interpolación espectral, el residuo sería casi cero). El archivo declara
  `BandSpecification` 8,2 / 8,7 / 9,0 / 10,5 / 12,0 µm. Se usan **la banda 4 (10,5 µm) y la 5 (12,0 µm)**, con la
  radiancia pasada a temperatura de brillo por Planck con esas longitudes de onda del propio archivo.
- **Celda válida de ECOSTRESS:** `data_quality` 0 en las bandas 4 y 5, `cloud` 0, `water` 0.
- **Versión.** Regla: la versión con más celdas de calidad 0 en las bandas 4 y 5 cerca del cráter. La 002 gana en las
  dos pasadas (25-10: la 003 marca calidad 1 en 74 % de la banda 5 alrededor del cráter, la 002 en 4 %). Decide la 002;
  la 003 del 08-11 se informa como sensibilidad.
- **08-11:** se usa la escena 030 (19:28:03). La 031 tiene 52 celdas válidas en 15 km.
- **Cota para ECOSTRESS:** la capa `height` del ECO_L2T_LSTE (misma grilla de 70 m, comprobado).

## 2. Landsat 25-10 (decide): lo que el criterio dejó abierto

- **Máscara:** `pluma` de `mascara_2026-10-25.npz` (la que ve OLI; TIRS mira a la vez y desde el mismo satélite, así
  que ve la pluma en el mismo lugar; la versión corregida por paralaje es para ponerla en el suelo, no aplica aquí).
  Erosionada 3 celdas: **283 celdas (0,25 km²)** de 1.771.
- **Control:** nieve de referencia de la preparación, a 2 a 15 km del cráter, a más de 300 m de la máscara entera.
  260.638 celdas.
- **Anillo:** celdas control a más de 300 m y hasta 1.000 m de la máscara erosionada (como el control ya excluye 300 m
  alrededor de la máscara entera, el anillo nunca toca pluma). Cada celda de pluma se compara con las celdas del anillo
  de su cota ±150 m (mínimo 20).
- **Pareo de T2 en tabla:** BT10 redondeada a 0,1 K y cota a 25 m (error en el borde de la ventana: 0,05 K y 12,5 m).
  Una celda sin 20 pares se descarta; T1 y T2 piden al menos 10 celdas con par.
- **Nulo:** la máscara erosionada corrida en pasos de 300 m (10 celdas) por toda la grilla, con todas sus celdas dentro
  del disco de 2 a 15 km, al menos la mitad sobre control y todas a más de 1 km de la máscara entera. En el corrimiento
  se usan sus celdas que caen en control; el control del pareo queda fijo (las celdas corridas son menos del 0,2 % de
  él). Con menos de 30 corrimientos válidos el veredicto es NO CONCLUYENTE (sin nulo).
- **BTD de ceniza esperada:** T_tope del GFS (el de H24) a 4.267 m en el cuadro de 14:30 del 25-10; T_superficie, la
  mediana de BT10 del anillo; ε11 se topa en 1.
- **Informativo:** la misma prueba con erosión de 2 celdas.

### 2.1 Control de sitio (nuevo; sólo puede bajar el veredicto)

La misma prueba, con la misma máscara, sobre **HLS L30 del 17-10 a las 14:34:36 UTC** (Landsat 9, misma órbita y
hora). Es el día sin evento más cercano con la máscara despejada: Fmask marca 0 % de nube o sombra en la máscara y
1,2 % en la nieve del disco. El 02-11 se descarta (Fmask marca nube en 99 % de la máscara). Los días 09-10 y 10-11
tienen 77 % y 93 % de nube en la tesela.

- Si el 17-10 da T2 ≤ −0,3 K con p_bajo ≤ 0,05, el lugar tiene firma de ceniza sin pluma: un FIRMA DE CENIZA del 25-10
  baja a NO CONCLUYENTE. Igual para FIRMA DE AGUA O HIELO con T2 ≥ +0,3 K y p_alto ≤ 0,05.
- Se informa además D = T(25-10) − T(17-10) en la máscara y en cada corrimiento válido los dos días, con su p. No
  decide: la nieve del 17-10 es otra (más extensa, más fría) y el sensor es otro (TIRS-2).

## 3. ECOSTRESS 08-11 19:28 (lectura, sin veredicto)

- **Máscara:** huella del PNG de VOLCAT de 19:20 leída como en H29 (corrida 1 fila al N y 1 columna al O, según H14):
  10 píxeles, alturas VOLCAT de 2,5 y 3,5 km (centro del bloque de la barra, tomado sobre el elipsoide). Cada píxel con
  su altura y con su bloque de 3 × 3 píxeles ABI alrededor; al suelo van las celdas de 70 m cuya posición a esa altura
  cae en el bloque (paralaje exacta con la geometría del ABI de S20b). Resultado: **267 km² en dos manchas, de 2,9 a
  30 km del cráter.**
- **Grilla:** la nativa de 70 m de ECOSTRESS, ±42 km alrededor del cráter. Disco de 2 a 40 km.
- **Sin condición de nieve:** la máscara no sale de la nieve y la huella de la tarde cae sobre el valle y el pie de la
  cordillera; la superficie se controla sólo por la cota (±150 m) y la BT (±0,5 K), como en H29.
- **Control:** celdas válidas del disco a más de 300 m de la máscara. Anillo: 300 a 1.000 m.
- **Nulo:** corrimientos de 980 m (14 celdas), todas las celdas dentro del disco, al menos la mitad sobre control, todas
  a más de 300 m de la máscara.
- **Referencia (nuevo):** el ensayo en seco (§6) mostró que el lugar de la máscara da BTD pareada más baja que todo el
  disco en un día sin pluma (17-10 20:42: T2 = −0,09 K, más bajo que los 91 corrimientos). Por eso la lectura del 08-11
  se informa como **D = T(08-11) − T(17-10 20:42)** en la máscara y en cada corrimiento, sobre las celdas válidas los
  dos días, con su p. También se informa T1 y T2 crudos.

## 4. ECOSTRESS 25-10 17:35 (descriptivo)

- Mapa de BTD pareada en el disco de 2 a 25 km: cada celda válida menos la mediana de la BTD de las celdas válidas del
  disco con su BT a ±0,5 K y su cota a ±150 m (tabla de §2, mínimo 20 pares).
- Regiones: conexas por 8 vecinos, BTD pareada < −1 K, 0,1 km² o más (21 celdas de 70 m). Se informa cuántas, su área,
  distancia, azimut y cuántas caen en el sector de la pluma de la mañana (OSO, 225 a 270°). El viento del GFS no está
  en el caché (sólo T y Z), así que no se compara con él.
- **Referencia:** la escena diurna (12 a 22 UTC) más cercana en fecha, fuera de los días excluidos de H24 (REAV, marcas
  y objetos VOLCAT, VCB), con 5 % de nube o menos a 25 km según la capa `cloud` del propio producto: 21-10 19:09 (86 %
  de nube) y 20-10 19:56 (100 %) no sirven; 01-11 15:16 tiene 28 a 47 %; **17-10 20:42 tiene 0,7 % y es la
  referencia.** Bajada para esto: bandas 4 y 5, calidad, nube y agua de cinco escenas candidatas (unos 60 MB).

## 5. Qué no cambia

Las medidas T1 y T2, sus umbrales y la tabla de veredicto de §3.2 del criterio. ECOSTRESS no decide.

## 6. Ensayo en seco (antes de medir; `resultados/s20d_seco.json`)

Sintético sobre la geometría real de Landsat (BT10 con gradiente de cota y ruido espacial de 1 K, BTD con ruido de
0,15 K; 2.077 corrimientos):

| Caso | T1 | T2 | p_bajo(T1) | p_bajo(T2) | Veredicto |
|---|---|---|---|---|---|
| Sin pluma | +0,64 K | +0,05 K | 0,89 | 0,78 | SIN CONTRASTE |
| Pluma −2 K, BTD −0,6 K | −1,36 K | −0,54 K | 0,006 | 0,000 | FIRMA DE CENIZA |
| Pluma −2 K, BTD +0,6 K | −1,36 K | +0,66 K | 0,006 | 1,000 | FIRMA DE AGUA O HIELO |
| Pluma −2 K, BTD 0 (gris) | −1,36 K | +0,06 K | 0,006 | 0,82 | SIN FIRMA |

Datos reales de días sin evento:

- **Landsat 9, 17-10, con la máscara del 25-10:** T1 −0,36 K (p_bajo 0,26), T2 +0,21 K (p_bajo 0,85), 2.073
  corrimientos; el nulo de T2 va de −0,25 a +0,31 K (percentiles 5 y 95). Habría dado SIN CONTRASTE: el lugar no tiene
  firma de ceniza propia.
- **ECOSTRESS, 17-10 20:42, con la máscara del 08-11:** T1 −0,11 K (p_bajo 0,29), T2 −0,09 K con p_bajo 0 de 91
  corrimientos (el nulo de T2 va de −0,05 a +0,14 K). El lugar tiene un sesgo propio: de ahí la referencia de §3. Sólo
  28.052 de las 54.579 celdas de la máscara son válidas ese día.
