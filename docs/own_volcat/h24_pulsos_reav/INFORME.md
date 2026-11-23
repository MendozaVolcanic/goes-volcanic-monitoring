# H24 (S18): ¿los pulsos que el OVDAS vio con cámaras dejan firma en el IR de GOES-19 a favor del viento? Informe, 23-11-2026

**Veredicto con la regla escrita antes de medir: NO CONCLUYENTE.** De los 6 pulsos altos (≥ 1.800 m sobre el
cráter), sólo uno se pudo decidir: E6, la explosión de columna gris oscura de 2.000 m del 27-10 al amanecer, **SIN
SEÑAL** con poder pleno. Los otros cinco altos, que incluyen los tres que VOLCAT marcó casi en cada cuadro (E11,
E12 y E13), quedaron sin dato porque **no hay tardes despejadas para armar el fondo**, no porque el episodio
estuviera nublado. Un pulso medio (E8, 27-10) dio SEÑAL con el criterio, pero no sobrevive a la revisión
exploratoria: una cumbre sin actividad (Antuco) "detecta" lo mismo a esas horas.

Criterio: `criterio_2026-11-22.md`, commit `f2094f7`. Enmienda 1 (más días excluidos, antes de medir): commit
`620b5a0`. Resultados del criterio: commit `e260476`. Enmienda 2 (exploratoria, después del veredicto y antes de
calcularla): commit `7c138fa`. Por qué se hizo esta prueba: `../RESPUESTA_S18_lo_que_vio_volcat.md`.

## 1. Para geólogo

**La pregunta.** Todas las pruebas anteriores usaron a VOLCAT como verdad y fallaron: VOLCAT mismo no ve la
pluma de Chillán en el píxel (H20a). Esta vez la verdad fue el OVDAS: 14 pulsos de REAV del 25-10 al 12-11, con
hora, altura y dirección. Si ni los pulsos altos documentados con cámara dejan firma infrarroja, "ver lo que
VOLCAT vio" no se puede lograr por la radiancia de 11 y 12 µm.

**El método, en palabras.** En cada cuadro de 10 minutos se comparó la diferencia 11 − 12 µm (la firma de la
ceniza) en el sector hacia donde iba la pluma, de 4 a 25 km del cráter, contra el sector de viento cruzado, en
el mismo cuadro. Cada píxel se comparó contra su propia historia a la misma hora en días despejados, y contra
píxeles de la misma temperatura esperada (pareo por BT11). Comparar dentro del mismo cuadro cancela el
corrimiento de todo el día que arruinó las pruebas de promediar (H23, H22). Después se hizo lo mismo en días sin
pulso documentado (el nulo y las falsas alarmas), se pintó una capa de ceniza conocida en esos días para saber si
la prueba podía verla (el poder), y se repitió en Antuco y Longaví, dos cumbres sin actividad.

**Lo que salió.**

1. **La explosión del 27-10 (E6, 2.000 m, columna "gris oscura, asociada a material piroclástico" según el
   REAV) no deja firma.** z −0,15 (la regla pide −2). La prueba tenía poder: una capa de ε 0,05 sobre el sector
   se habría detectado en 82 % de los días nulos, y en la revisión exploratoria una pluma **angosta** (franja de
   ±3 km) de ε 0,15 en 100 %. VOLCAT tampoco la marcó (0 de 8 cuadros, H10).
2. **Los pulsos del 25-10 en la mañana y del 27-10 a media mañana (E1, E7) tampoco**, con poder pleno.
3. **E8 (27-10, 11:00 a 16:00 UTC, pulsos de hasta 1.640 m hacia el N) dio SEÑAL con el criterio** (BTD del
   sector 0,15 K más baja que el viento cruzado, z −2,26, placebo y cumbres de control pasan). **No sobrevive:**
   con la línea base de toda la ventana, Antuco da −2,06 y −2,19 a esas mismas horas. Lo más probable es tiempo
   regional. Es el mismo día en que H10 vio la BTD bajar 0,2 a 0,4 K en el sector del REAV (AUC 0,70); los dos
   resultados vienen de los mismos datos y no se confirman entre sí.
4. **Los pulsos que VOLCAT sí marcó no se pudieron medir.** E11 (28-10, 2.440 m), E12 (28-10, 2.020 m) y E13
   (10-11, 2.400 m) son de tarde o anochecer. Los cuadros del episodio estaban despejados (el 28-10 el terreno
   bajo estuvo despejado casi al 100 % de 12 a 22 UTC), pero del 21-09 al 21-11 hubo 0 a 3 tardes despejadas sin
   actividad para armar el fondo. Sin fondo no hay comparación. Es el mismo hueco de tarde que dejó H23.
5. **Falsas alarmas medidas:** 3 de 39 días nulos (7,7 %) con la regla del criterio, dentro del límite (10 %).

**Qué significa para la pregunta de Nicolás** ("¿podemos detectar lo que vio VOLCAT?"):

- Con verdad del terreno, en las horas en que se puede medir (mañana), los pulsos documentados por el OVDAS, uno
  de ellos una explosión de ceniza de 2 km, **no dejan firma infrarroja medible** en GOES-19, ni siquiera con una
  prueba capaz de ver una pluma angosta de ε 0,15. VOLCAT tampoco marcó esos pulsos.
- **Lo que VOLCAT sí marcó (tardes del 28-10 y del 10-11) queda sin responder**, por falta de fondo y no por
  falta de dato del episodio. Esa es hoy la única puerta abierta: no se sabe si esos pulsos tenían firma IR.
- Esto no cambia lo que dicen H20a, H22 y H23 sobre los eventos del 13 al 18-11; los complementa con verdad
  independiente.

## 2. Comprobaciones de instrumento y controles

| | Pide | Medido |
|---|---|---|
| Cubo nuevo 24 a 31-10: I1 cobertura | ≥ 95 % | 1.152 de 1.152 cuadros; ACMF 1.151 (falta 28-10 09:10) |
| I2 mismo scan C14 y C15 | 0 distintos | 0 |
| I3 rango y congelados | 180 a 330 K; 0 congelados | 215,4 a 316,3 K; 0 congelados; Planck igual en los tres cubos (assert < 1e-5) |
| Pruebas numéricas del script | todas | 8 de 8 (Planck ida y vuelta, inyección ε 0 y 1, sectores disjuntos, ventanas, z robusto, paralaje hacia 173,6°) |
| Control positivo grande (ε 0,9 a 10 km) | ≥ 95 % en cada episodio con nulo | 100 % en E1, E6, E7 y E8 |
| Nulo no degenerado | MAD > 0,01 K | 0,04 a 0,13 K |
| Falsas alarmas (días nulos como falsos episodios) | ≤ 10 % | 3 de 39 (7,7 %) |
| Placebo contra el viento | no detecta | no detecta en ningún episodio decidible (z −1,46 a +0,74) |

Las dos preguntas del instrumento (criterio §3): un D2 ciego habría dado SIN PODER, no SIN SEÑAL, y el control
grande pasó en todos los episodios medibles; un instrumento muerto habría dado nulo degenerado o fallado I1 a I3.

## 3. Resultados por episodio (criterio, `resultados/h24_episodios.csv`)

E = mediana de las diferencias de BTD del sector contra el viento cruzado (K). z robusto contra el nulo. Poder =
fracción de días nulos en que una capa sobre todo el sector se detecta.

| Ep | H (m) | Grupo | Cuadros | Días nulos | E (K) | z | Poder ε 0,05 · 0,10 · 0,15 | Placebo z | Antuco z | Longaví z | VOLCAT anclado (H10) | Clase |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| E1 | 1.320 | medio | 4 | 9 | −0,02 | 0,04 | 0,22 · 0,89 · 1,00 | −1,46 | 0,48 | | 0 de 8 | SIN SEÑAL |
| E2 | 920 | medio | 6 | 6 | 0,03 | 1,30 | sin dato (ver §5) | −0,50 | 0,50 | −0,30 | 0 de 9 | SIN PODER |
| E3 | 1.540 | medio | 7 | 5 | 0,04 | | | | | −0,42 | 0 de 8 | SIN PODER |
| E4 | 1.740 | medio | 10 | 5 | 0,03 | | | | | | 4 de 18 | SIN PODER |
| E5 | 2.300 | alto | 1 | 0 | | | | | | | 4 de 32 | SIN DATO |
| E6 | 2.000 | alto | 6 | 11 | −0,04 | −0,15 | 0,82 · 1,00 · 1,00 | 0,15 | | 0,39 | 0 de 8 | **SIN SEÑAL** |
| E7 | 960 | medio | 4 | 10 | 0,01 | 0,16 | 0,60 · 1,00 · 1,00 | 0,27 | | −1,00 | 0 de 8 | SIN SEÑAL |
| E8 | 1.640 | medio | 22 | 9 | −0,15 | **−2,26** | 1,00 · 1,00 · 1,00 | 0,74 | −1,06 | 0,12 | 0 de 32 | SEÑAL (no sobrevive, §4) |
| E9 | 1.320 | medio | 6 | 4 | −0,20 | | | | | | 0 de 8 | SIN PODER |
| E10 | 2.200 | alto | 0 | 0 | | | | | | | 1 de 8 | SIN DATO (sin fondo de tarde) |
| E11 | 2.440 | alto | 0 | 0 | | | | | | | **8 de 8** | SIN DATO (sin fondo de tarde) |
| E12 | 2.020 | alto | 0 | 0 | | | | | | | **7 de 7** | SIN DATO (sin fondo de tarde) |
| E13 | 2.400 | alto | 0 | 0 | | | | | | | **10 de 11** | SIN DATO (sin fondo de tarde) |
| E14 | 400 | bajo | 0 | 0 | | | | | | | 0 de 8 | SIN DATO (cielo) |

Secundarias de E8: D1 (BT11) z −1,27; pareo por BT11 observada z −2,69. Veredicto global (criterio §8): 1 alto
decidible, 0 SEÑAL: **NO CONCLUYENTE**. Columna VOLCAT: `resultados/h24_volcat_por_episodio.json`, con las
ventanas de H10 (desde 20 min antes del inicio), no exactamente las de esta prueba.

## 4. Revisión exploratoria (enmienda 2, no decide)

Ventana de fondo de dos meses en vez de ±21 días, percentil 20 en vez de la mediana (para ver plumas que cubren
parte del sector), y poder con una pluma angosta (franja de ±3 km, 21 a 23 de los 53 a 58 píxeles del sector).
`resultados/h24_explorar.csv`, `h24_explorar_resumen.json`.

| Ep | Cuadros | Días nulos | z (p20) | Poder franja ε 0,15 · 0,30 · 0,50 | Antuco z | Clase (p20) |
|---|---|---|---|---|---|---|
| E1 | 4 | 10 | 0,01 | 0,30 · 0,80 · 0,80 | 0,38 | SIN SEÑAL |
| E2 | 6 | 8 | 0,28 | 0,50 · 0,88 · 1,00 | 0,82 | SIN SEÑAL |
| E3 | 7 | 7 | 0,58 | 0,86 · 0,86 · 0,86 | 1,34 | SIN SEÑAL |
| E6 | 6 | 13 | −0,19 | 1,00 · 1,00 · 1,00 | | SIN SEÑAL |
| E7 | 4 | 11 | 0,28 | 1,00 · 1,00 · 1,00 | | SIN SEÑAL |
| E8 | 22 | 12 | −2,37 | 1,00 · 1,00 · 1,00 | **−2,19** | DUDOSO |
| E10 a E13 | 5 a 7 | 0 a 3 | | | | SIN PODER (sin fondo de tarde) |

**Las dos variantes quedan INVÁLIDAS por su propia regla**: falsas alarmas 8 de 61 (13,1 %, mediana) y 7 de 61
(11,5 %, percentil 20), sobre el 10 %. Ampliar el fondo a dos meses mezcla septiembre con noviembre y ensancha
las falsas alarmas. Lo que sí queda a la vista, como lectura: con la ventana larga, E8 lo "detecta" también
Antuco, y los SIN SEÑAL de la mañana se sostienen con un estadístico que ve plumas angostas.

## 5. Lo que podría estar equivocado

- **Dirección de la pluma.** E6 usa la dirección del REAV (NO, 315°); el GFS daba NNE (17°, 6,9 m/s), a 62°. Si la
  pluma se fue hacia el NNE, el sector de ±30° la pierde en buena parte. E1 a E3 usan la del REAV con el GFS en
  calma. Para E6 vale la pena repetir con la dirección del GFS (no se hizo: sería otra prueba).
- **β.** La capa inyectada tiene β 0,70. Si la ceniza de Chillán es gruesa o muy húmeda (β cerca de 1), la BTD no
  la ve aunque sea espesa (H23 S3); D1 (BT11) tampoco detectó E6 (z −1,37).
- **El poder supone una capa que llena el sector o una franja de 6 km de ancho a lo largo de 21 km.** Un pulso
  que se disipa en 5 a 10 km cubre menos y la prueba puede no verlo.
- **E2 y E4: con exactamente 5 o 6 días nulos el poder queda indefinido**, porque el poder deja uno afuera y
  pide 6. Es una consecuencia del criterio tal como se escribió; no se cambió después de ver datos.
- **El rótulo "SIN DATO (cielo)" del script** cubre también "sin línea base": en E10 a E13 el episodio estaba
  despejado y lo que faltaba eran días de fondo despejados de tarde (diagnóstico en §6).
- **Días nulos con pulsos chicos.** El volcán emitió casi a diario desde el 24-10. La enmienda 1 sacó los días
  con objetos VOLCAT (incluidos el 11-11 y el 16-11, que Nicolás recordó por los loops), pero un pulso chico sin
  VOLCAT queda en el nulo y lo ensancha. Las cumbres de control no tienen ese problema.

## 6. Diagnóstico del hueco de tarde (después del veredicto, informativo)

Fracción de cuadros con escena despejada (≥ 80 % del terreno bajo según ACMF), Chillán, 21-09 al 21-11: 0,26 a
0,35 entre 01 y 10 UTC; 0,15 a 0,19 entre 14 y 23 UTC. El día 28-10 estuvo despejado de 12 a 22 UTC (0,99 a 1,00),
pero en los cuadros de E10 la línea base tenía 2 días despejados a esa hora en ±21 días (pide 3), y en E13, 1.
Las tardes despejadas existen, pero caen en días excluidos por actividad o son demasiado pocas.

## 7. Qué sigue (propuesta, no hecho)

1. **Prueba prospectiva en verano.** Diciembre a febrero trae más tardes despejadas en la cordillera. Con los
   REAV que vengan y con el mismo criterio (sin cambiar nada), los pulsos de tarde que VOLCAT marque serían
   decidibles. Es la única forma limpia de responder si lo que VOLCAT marca de tarde tiene firma IR.
2. **E6 con la dirección del GFS**, como prueba nueva con criterio propio.
3. **Un fondo que no dependa de tardes despejadas** (por ejemplo, las cumbres de control en el mismo cuadro como
   nulo espacial) necesita su propio criterio: las cumbres tienen otro terreno y el pareo por BT11 no lo cancela
   del todo.

## 8. Archivos

- `criterio_2026-11-22.md`, `enmienda_posthoc_1_2026-11-22.md`, `enmienda_posthoc_2_exploratoria_2026-11-23.md`.
- `scripts\`: `h24_medir.py` (criterio), `h24_explorar.py` (enmienda 2), copias de descarga de H23 con otra
  carpeta y otro bloque (`h24_comun.py`, `h24_bajar.py`, `h24_bajar_acm.py`, `h24_gfs.py`, `h24_cubo.py`).
- `resultados\`: `h24_episodios.csv`, `h24_resumen.json`, `h24_corrida.log`, `h24_explorar.csv`,
  `h24_explorar_resumen.json`, `h24_explorar.log`, `h24_volcat_por_episodio.json`, `h24_instrumento_cubo_oct.json`.
- Fuera del repo: `D:\goes_notas\s18\h24\` (L1b C14 y C15, ACMF y GFS del 24 al 31-10, cubo). Insumos de sólo
  lectura: cubos, ACMF y GFS de H23 en `D:\goes_notas\s17\h23\`. Ningún archivo de SSEC.
- Nada toca `src/` ni el dashboard.

Reproducir, desde `docs\own_volcat\h24_pulsos_reav\scripts\`:

```powershell
python -I h24_bajar.py 10 oct
```

```powershell
python -I h24_bajar_acm.py 10 oct
```

```powershell
python -I h24_gfs.py
```

```powershell
python -I h24_cubo.py oct
```

```powershell
python -I h24_medir.py
```

```powershell
python -I h24_explorar.py
```
