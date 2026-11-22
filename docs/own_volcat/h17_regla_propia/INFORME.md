# H17: una regla propia "calor en el cráter, luego objeto chico anclado" contra VOLCAT en Nevados de Chillán. Informe, 21-11-2026

**Veredicto (reglas del criterio): las dos etapas fallan.** Etapa 1 (calor): **no recupera**, 0 de los 3 cuadros en
que VOLCAT marca 10 MW o más. Etapa 2 (pluma): **no separa del fondo**, detecta 13 % de los cuadros con pluma VOLCAT
y da falsa alarma en 7 % de los cuadros limpios, con un intervalo de confianza que cruza el cero.

Lo que sí deja: con el fondo bien planteado (informativo, no decide), el calor nocturno a 3,9 µm separa Chillán de
dos cumbres sin actividad (48 % de los cuadros nocturnos con 10 MW o más desde el 24-10, contra ~1 % en Antuco y
Longaví), en unidades de potencia comparables a las de VOLCAT. Y la pluma, en el píxel, no tiene señal: los píxeles
que VOLCAT publica están a la temperatura del suelo despejado en 11 µm, no más fríos.

Criterio escrito y subido antes de medir: commit `e1cf1dd`,
`C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\Goes\docs\own_volcat\h17_regla_propia\criterio_H17_2026-11-21.md`
(mientras no se fusione, en
`C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\Goes\.claude\worktrees\nervous-nobel-fced9a\docs\own_volcat\h17_regla_propia\`).
Investigación: nada de esto toca el dashboard ni `src/`.

## 1. Para geólogo

**La idea que se quiso imitar.** VOLCAT publica las emisiones chicas de Chillán por una vía no pública
(`ASHPLUMEPUFF`, H16) que, según su presentación de 2022, se vuelve más sensible cuando el volcán tiene actividad
térmica. La lógica es volcanológica, no espectral: si el conducto está caliente y abierto, una nube chica que sale del
cráter tiene más probabilidad de ser emisión que nube orográfica. Se armó una regla nuestra con esa lógica: primero
medir calor en el cráter con el canal de 3,9 µm de GOES-19 (sin FDCF, sin VIIRS) y expresarlo en megawatts como
VOLCAT; después, con calor presente, buscar objetos chicos pegados al cráter con umbrales relajados.

**Por qué 3,9 µm y por qué en megawatts.** A 3,9 µm la radiancia de Planck crece con la temperatura mucho más rápido
que a 11 µm: una superficie incandescente que cubre una fracción mínima del píxel sube mucho la temperatura de brillo
de 3,9 µm y casi nada la de 11 µm. El exceso de radiancia a 3,9 µm, multiplicado por el área del píxel, da la
potencia radiativa volcánica (VRP) por el método del infrarrojo medio (Wooster y otros 2003). El dato clave de la
calibración: en un píxel ABI de 5,9 km² sobre Chillán, **10 MW equivalen a unos 8,5 K de subida a 3,9 µm de noche y a
unos 4 K de día**. El calor que H9 midió en las noches de Chillán (~7 K) queda en el orden de 5 a 10 MW: justo en el
umbral que usa VOLCAT.

**Etapa 1, lo que pasó.** La regla del criterio no recupera ninguno de los tres cuadros VOLCAT con 10 MW. Al revisar
por qué apareció un defecto de la propia regla: el píxel caliente se elegía por la anomalía *relativa* BT7 − BT14
contra el anillo, pero la potencia se calculaba contra la radiancia *absoluta* del anillo. De día la cumbre nevada es
más fría que el anillo en las dos bandas, así que su anomalía relativa es real y su exceso absoluto sale cero o
negativo. Además, el umbral de 3 desviaciones del anillo, en terreno de montaña, sube a ~7 K por píxel. Las dos cosas
juntas apagan la señal. El veredicto queda como está (el criterio no se ajusta después de ver los números).

**Etapa 1 con el fondo coherente (informativo).** Si el fondo de cada píxel se toma como la radiancia que tendría con
su propia BT14 y la diferencia BT7 − BT14 típica del anillo, la potencia y el test calzan. Así:
- **De noche funciona**: Chillán pasa de 0,5 % de cuadros con 10 MW o más (20 al 23-10) a **48 %** desde el 24-10
  (mediana 8,8 MW), mientras Antuco y Longaví quedan en ~1 %. Es el mismo encendido que H9 vio en kelvin, ahora en las
  unidades de VOLCAT, y calza con la incandescencia nocturna que informa el SERNAGEOMIN desde fines de octubre.
- **De día no sirve**: las cumbres de control dan 12 % de cuadros con 10 MW (sol reflejado, nieve y bordes de nube a
  3,9 µm), y contra VOLCAT el resultado es al revés de lo esperado: recupera 1 de sus 3 cuadros con 10 MW
  (14-11 12:40, 11,6 MW) y da 126 MW en el 14-11 16:30, el cuadro en que VOLCAT no registra calor. Los tres cuadros de
  verdad térmica de VOLCAT son de día o de amanecer, así que lo único que sale bien (la noche) no se puede comparar
  con VOLCAT.

**Etapa 2, lo que pasó.** Con la compuerta de calor de 24 horas (encendida en 98 % de los cuadros con pluma VOLCAT y en
72 % de los limpios), la regla detecta 17 de 127 cuadros con pluma (13 %) y da falsa alarma en 91 de 1.380 cuadros
limpios (7 %). Por día: detecta algo en 6 de los 12 días con pluma VOLCAT, pero también en 13 de 17 días sin pluma.
La compuerta baja la falsa alarma de 9 % a 7 % sin cambiar la detección: filtra, pero no hay qué filtrar.

**La física de por qué no se ve.** Cada píxel se comparó contra sí mismo en los seis días previos a la misma hora (lo
más despejado), justamente para sacar el terreno, que es lo que hundió las pruebas anteriores. Resultado: los píxeles de
la huella VOLCAT están **1,3 K más tibios** que su base despejada en 11 µm (mediana) y su diferencia 11 − 12 µm baja
apenas 0,2 K. Los píxeles de control con la misma BT11 en el mismo cuadro están 12,5 K bajo su base: son nube. Dicho de
otra forma, el píxel que VOLCAT publica se ve en el infrarrojo como suelo despejado. Sólo 1,7 % de los píxeles de huella
pasa los umbrales relajados, contra 32 % de los controles. No hay umbral que aflojar: la pluma tenue de estos días es
transparente a 2 km en 11 y 12 µm. Calza con todo lo anterior (pruebas del 17-11, H11, H15, H16).

**Qué significa para el dashboard.** Para ceniza, nada nuevo que mostrar: una regla propia que imite la idea de VOLCAT
no alcanza a ver estas emisiones con la L1b infrarroja. Lo que ve VOLCAT, si no está en el infrarrojo, tiene que venir
de su clasificador con tiempo o de canales de día que acá no se probaron (0,64 µm y 3,9 µm reflejado, ver §5). Para
calor, en cambio, queda un candidato concreto: **un indicador nocturno de VRP a 3,9 µm desde la L1b**, que ve un
encendido que el FDCF de NOAA no vio. Antes de mostrarlo hace falta su propio criterio, validación fuera de muestra y
ficha SDA (CPLT 372).

## 2. Etapa 1: calor (H17-T)

Datos: 2.445 cuadros con C07 y C14 del 20-10 al 19-11 (732 de noche, 1.488 de día, 225 de crepúsculo). Constante del
método `a = 4,18 × 10⁻⁹` (Planck del NetCDF), área del píxel del cráter 5,94 km².

| Cuadro VOLCAT | `time_since_10MW` | VRP regla (MW) | Anomalía máx. BT7 − BT14 | Umbral por píxel | VRP con fondo coherente (informativo) |
|---|---|---|---|---|---|
| 13-11 19:00 | 0 | 0,0 | 6,5 K | 7,6 K | 0,0 |
| 14-11 12:40 | 0 | 0,0 | 6,0 K | 4,0 K | 11,6 |
| 18-11 10:10 | 0 | 0,0 | 6,3 K | 6,7 K | 0,0 |
| 14-11 16:30 | relleno (sin calor) | 0,0 | 8,5 K | 3,5 K | 125,6 |

| Prueba | Pide | Da | Resultado |
|---|---|---|---|
| C1, consistencia con VOLCAT | ≥ 10 MW en ≥ 2 de 3 | 0 de 3 (también ± 1 scan) | **no cumple** |
| C2, controles de noche | ≤ 2 % | 0,07 % | cumple |
| C2, controles de día | ≤ 5 % | 4,5 % (Antuco 7,1 %, Longaví 2,0 %) | cumple |
| **Veredicto** | | | **no recupera** |

Por día UTC, la regla da 10 MW en 0 de 83 cuadros del 13-11, 3 de 88 del 14-11 y 1 de 58 del 18-11.

Informativo (agregado tras la primera corrida, **no decide**), fracción de cuadros con la potencia sobre el corte:

| Variante | Cuadros VOLCAT 10 MW detectados | Controles noche | Controles día | Chillán noche | Chillán día |
|---|---|---|---|---|---|
| Regla, corte 5 MW | 0 de 3 | 0,5 % | 5,9 % | 5,9 % | 4,2 % |
| Umbral fijo 2 K, 10 MW | 0 de 3 | 1,9 % | 44 % | 2,0 % | 19 % |
| **Fondo coherente, 10 MW** | 1 de 3 | **0,95 %** | 11,8 % | **35 %** | 33 % |
| Fondo coherente, 5 MW | 1 de 3 | 2,0 % | 14 % | 41 % | 34 % |
| Fondo coherente + umbral fijo 2 K, 10 MW | 3 de 3 | 5,0 % | 73 % | 41 % | 75 % |

Fondo coherente, noche, por tramo: Chillán 0,5 % (199 cuadros, 20 al 23-10) y **48 %** (533, desde el 24-10, mediana
8,8 MW, p90 24,9 MW); Antuco 1,5 % y 0,9 %; Longaví 0,0 % y 1,1 %. La única variante que recupera los tres cuadros
VOLCAT lo hace porque de día casi todo pasa (73 % en los controles).

## 3. Etapa 2: objeto chico anclado con compuerta de calor (H17-P)

1.916 cuadros con C14 y C15; 1.833 con línea base temporal (≥ 5 cuadros en los seis días previos a ± 90 min).
Positivos: 127 (100 de los PNG VOLCAT anclados de H9 más los 60 cuadros de evento, 33 en común), todos con base.
Negativos limpios: 1.380 con base.

| Variante | POD | FAR | IC 95 % de POD − FAR (por días) | Días con pluma VOLCAT detectados | Días sin pluma con falsa alarma |
|---|---|---|---|---|---|
| **Decide** (−1 K, −0,5 K, compuerta 24 h) | 0,134 (17/127) | 0,066 (91/1.380) | −0,079 a 0,195 | 6 de 12 | 13 de 17 |
| Sin compuerta | 0,134 | 0,091 | −0,107 a 0,163 | 7 de 12 | 15 de 17 |
| Estricta (−2 K, −1 K) | 0,000 | 0,022 | −0,038 a −0,009 | 1 de 12 | 9 de 17 |
| Compuerta en el mismo scan | 0,000 | 0,004 | −0,007 a −0,001 | 2 de 12 | 3 de 17 |

Por periodo (decide): día POD 0,136 / FAR 0,072; crepúsculo 0,143 / 0,088; noche 0,100 / 0,026 (sólo 10 positivos
nocturnos). Veredicto: **no separa del fondo** (POD < 0,5, FAR > 0,05 y el IC cruza el cero).

Huella `event_idx` de los 60 cuadros de evento:

| Medida | Huella | Controles pareados por BT11 (± 0,5 K, mismo cuadro) |
|---|---|---|
| Píxeles candidatos | **1,7 %** (768 píxeles) | 31,7 % (3.835) |
| Mediana ΔBT11 contra su base | **+1,28 K** | −12,52 K |
| Mediana ΔBTD contra su base | −0,19 K | −0,11 K |

17 de los 60 cuadros de evento tienen un objeto anclado de 1 a 70 píxeles; en 9 toca la huella dilatada 1 píxel.
Fracción media de la huella que es candidata: 5 %.

## 4. Límites

- **Verdad térmica mínima.** `volcano_thermal_activity` viene lleno sólo en el primer cuadro de cada evento: tres
  positivos, todos de día o amanecer, y un "sin calor" de día. No hay verdad térmica VOLCAT nocturna. Tampoco se sabe
  si `time_since_10MW = 0` habla del scan o del día, ni con qué fondo y corrección atmosférica calcula VOLCAT su VRP.
- **VRP sin corrección atmosférica** a 3,9 µm (subestima del orden del 10 % en una cumbre de 3 km, sin medir aquí) y
  con la aproximación de Wooster, que en este rango de temperatura tiene hasta 24 % de error.
- **El defecto de la regla de calor se vio después de medir.** Por eso el fondo coherente queda como informativo: su
  buen resultado nocturno es una hipótesis, no una validación.
- La línea base temporal usa sólo el pasado y no mira etiquetas VOLCAT; si los días previos estaban nublados, el
  percentil 75 queda frío y la anomalía sale tibia. Ese sesgo existe, pero no explica la huella: sus controles con la
  misma BT11 tienen la misma base y salen 12,5 K bajo ella.
- Positivos nocturnos de pluma: 10. La noche no está evaluada para la pluma.

## 5. Lo que queda abierto

1. **Indicador térmico nocturno propio** (fondo coherente). Necesita criterio nuevo y validación fuera de muestra,
   por ejemplo con noches posteriores al 19-11 y contra otra fuente térmica independiente, antes de pensar en una ficha
   SDA. Es la parte útil de H17.
2. **Canales de día.** La etapa 2 sólo usó 11 y 12 µm. VOLCAT tiene tablas de día con 0,65 µm y 3,9 µm reflejado
   (H16 no las midió) y 49 de los 60 cuadros de evento son de día. Una pluma ópticamente delgada en el infrarrojo
   térmico puede verse en el visible. Si se prueba, va con criterio propio.
3. **La pregunta a Pavolonis** sigue siendo la misma de H16: cómo decide `ASHPLUMEPUFF` y cómo el calor relaja los
   umbrales. H17 agrega una: con qué fondo y corrección calcula la VRP que dispara `time_since_10MW`.

## 6. Archivos

- Criterio: `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\Goes\docs\own_volcat\h17_regla_propia\criterio_H17_2026-11-21.md`
- Scripts: `...\h17_regla_propia\scripts\` (`h17_comun.py`, `h17_bajar.py`, `h17_calor.py`, `h17_pluma.py`).
- Salidas crudas: `...\h17_regla_propia\resultados\` (`h17_calor_resultado.txt`, `calor_por_cuadro.csv`,
  `h17_pluma_resultado.txt`, `pluma_por_cuadro.csv`; sin posiciones de huella ni datos de SSEC).
- Fuera del repo: `D:\goes_cache\h17\` (`l1b\` con 715 cuadros bajados de NOAA S3, `calor.pkl`, `pluma_pixeles.pkl`,
  `bajar.log`, `calor.log`, `pluma.log`).
- Reproducir (Git Bash, desde `scripts\`): `python -I h17_bajar.py 10`, luego `python -I h17_calor.py`, luego
  `python -I h17_pluma.py` (~20 min). Necesita los cachés de H9, H13 y etapa 3 en `D:` (ver
  `INVENTARIO_REPRODUCIBILIDAD.md`) y los archivos de evento VOLCAT de
  `D:\goes_notas\busqueda_2026-11-20\volcat_eventos_357070\` (licencia restringida, sólo uso interno).
