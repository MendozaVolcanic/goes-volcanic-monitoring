# C2 y C2b, 21-11-2026: el modelo radiativo vuelve a correr, y el cielo despejado de VOLCAT conoce la cota

Criterio escrito y subido antes de medir: `criterio_C2b_2026-11-21.md` (commit ac81069). Plan: PR 69,
`PLAN_2026-11-21_LUT_VOLCAT.md`, caminos C2 y C2b.

## Lo esencial, para geólogo

1. **C2, cumple.** El modelo radiativo propio (el de H3, que usan H11, la etapa 2, H12, H13 y C3) vuelve a
   correr con el continuo de vapor de agua y las funciones de respuesta del ABI bajados de nuevo a
   `D:\goes_cache\rt\`. En 5 escenas de H3 reproduce el cielo despejado que H11 había guardado con los
   insumos originales: **error p95 de C14 = 0,0 K** (vara ≤ 0,3 K), con 1.500 píxeles. Los archivos
   bajados son los mismos que tenía H3 (MT_CKD con la misma huella git; mismas SRF de CIMSS).
2. **C2b según el criterio: no concluyente.** La noche del caso de prueba (28-11-2022, 09:16 a 10:01 UTC)
   Hawái estaba cubierto de nube. En el océano alrededor de la isla la BT11 observada tiene mediana 248 K,
   contra 289 K de cielo despejado; la emisividad que publica VOLCAT en mis "píxeles despejados" vale 0,3 a
   0,5, o sea, nube. Mis pruebas de despejado dejaron pasar nube opaca y quieta; la condición de validez del
   criterio (control bajo a ≤ 2 K) la atrapó, que es para lo que estaba. Ninguna cumbre tuvo 5 píxeles
   despejados.
3. **Lo que sí se puede decir, con un análisis posterior (no estaba en el criterio): el cielo despejado de
   VOLCAT lleva la superficie a la cota fina del terreno.** El GFS de VOLCAT entra en celdas de 0,5° sin
   interpolar: sobre el océano el cielo despejado es constante dentro de cada celda (desviación 0,02 K). Sobre
   tierra, en cambio, baja con la cota de cada píxel de 2 km **dentro de la misma celda**, a −2,7 a −6,5 K por
   km (agrupado −3,75 K/km). En las cumbres, donde el GFS pone el terreno a 2.667 m (Mauna Loa) y 1.234 m
   (Mauna Kea), el cielo despejado de VOLCAT queda en 272,6 y 273,6 K: a 1,5 y 0,6 K de la temperatura del
   aire del propio GFS a la cota de la cumbre (274,1 y 274,2 K), y 11 a 15 K más frío que la temperatura de
   superficie del GFS en esa celda (283,9 y 288,4 K). Un modelo que usara la superficie del GFS, como el
   nuestro, habría dado una cumbre del orden de 10 a 15 K más tibia (estimado desde la temperatura de
   superficie del GFS, no calculado): es el mismo error que medimos en Chillán (7 a 9 K).
4. **Propuesta para C3 (decide Nicolás):** el cielo despejado propio se corrige por cota al estilo CLAVR-x (temperatura de superficie
   llevada a la cota del modelo de elevación con el perfil del GFS) **antes** de cualquier sesgo local. Que el
   sesgo local de 12 píxeles se aplique además no se pudo ver aquí: su campo por píxel viene vacío en los 10
   cuadros y no hay cielo despejado con qué medirlo. Lo que este caso no dice es **cuán bien** queda esa
   corrección contra la observación; eso exige una noche despejada.
5. **`geocatL2` trae la probabilidad de ceniza por píxel** (`ash_probability_IR`, definida en ~100 mil
   píxeles de cada cuadro, de noche). Sirve como verdad para validar la lectura de las tablas en C3, con un
   reparo: es GOES-17 y VOLCAT v3.9.16, y el paquete no trae la configuración ni dice qué tabla usó.

---

## C2. Modelo radiativo repuesto

**Qué se perdió.** El 20-11 se borró la carpeta `dl\` de H3. El código (`h3_h7/scripts_h3/rt.py` y
`lbl.py`) esperaba ahí dos insumos: `dl\mtckd\absco-ref_wv-mt-ckd.nc` (continuo de vapor de agua MT_CKD 4.3)
y `dl\srf\CH10.SRF`, `CH11.SRF`, `CH14.SRF`, `CH15.SRF` (funciones de respuesta del ABI FM4, el de GOES-19). La
tabla de coeficientes línea por línea (`lbl\lut.npz`) sí estaba rescatada.

**De dónde se bajaron.** Las fuentes exactas salen del registro de la sesión de H3: MT_CKD de
`github.com/AER-RC/MT_CKD_H2O` (H3 bajó `master`; hoy se bajó el tag `4.3`, que es el mismo commit, 3e043b4
del 17-04-2024, y el blob git del archivo es idéntico, ff75b0e); las SRF de
`cimss.ssec.wisc.edu/goes/calibration/SRF/abiFM4/ABI_FM4_10Mar2016_CHxx.SRF`. Total ~170 KB, en
`D:\goes_cache\rt\mtckd\` y `D:\goes_cache\rt\srf\` (con el `LICENSE.md` de AER). Huellas SHA-256 en
`resultados/insumos_rt.txt`.

**Rutas por variable de entorno (sin romper los defaults).**

- `lbl.py`: `DL = H3_RT_DL` o, si no existe, `<carpeta del script>\dl`, como antes. Acepta las SRF con su
  nombre original de CIMSS o con el corto que usaba H3.
- `rt.py`: `LBL = H3_RT_LBL` o `<carpeta del script>\lbl`; el continuo se busca en `lbl.DL`.
- `comun_h11.py` (que usan H11, E2, H12 y H13): el código del modelo sale ahora del repo
  (`h3_h7/scripts_h3`, idéntico a la copia que había en la carpeta H3; comprobado con `diff`). Si no se fijan
  `H3_RT_LBL` y `H3_RT_DL`, apuntan a `<H11_H3>\lbl` y `<H11_H3>\dl`, o sea, se comporta como antes.
- Qué insumo vive dónde, con el ejemplo de cómo correr: `docs/own_volcat/README.md`, sección nueva.

**Validación (regla del criterio).** De los 74 archivos `rt_h11` de pares con origen H3 se tomaron 5 a
intervalos iguales (`20261028_2240_ctrl`, `20261114_1700_ctrl`, `20261114_1850_ctrl`, `20261114_2040_pos`,
`20261114_2230_pos`), 300 píxeles al azar en cada uno (semilla 0). Se recalculó el cielo despejado con el
mismo camino de H11 (`rt_niveles.radiancias_pixel`), desde la misma escena y el mismo GFS.

| Escena (archivo `rt_h11`) | GFS | Píxeles | p95 C10 | p95 C11 | p95 C14 | p95 C15 | máx. C14 |
|---|---|---|---|---|---|---|---|
| 20261028_2240_ctrl | 2026102723 | 300 | 0,000 | 0,000 | 0,000 | 0,000 | 0,000 |
| 20261114_1700_ctrl | 2026111217 | 300 | 0,000 | 0,000 | 0,000 | 0,000 | 0,000 |
| 20261114_1850_ctrl | 2026111219 | 300 | 0,000 | 0,000 | 0,000 | 0,000 | 0,000 |
| 20261114_2040_pos | 2026111421 | 300 | 0,000 | 0,000 | 0,000 | 0,000 | 0,000 |
| 20261114_2230_pos | 2026111423 | 300 | 0,000 | 0,000 | 0,000 | 0,000 | 0,000 |
| **Total** | | **1500** | | | **0,000** | | 0,000 |

Diferencias absolutas en kelvin (BT despejada nueva menos guardada). **Prueba de que la prueba no es vacía (mutación):** con la SRF de C15 puesta en lugar de la de C14 en una copia de los insumos (`D:\goes_cache\rt_mutado`), la misma prueba sobre 40 píxeles de 2 escenas da p95 de C14 = 7,24 K y no cumple (`resultados/c2_mutacion_srf14_por_srf15.json`); eso confirma además que el código lee la carpeta de `H3_RT_DL`.

**Resultado: cumple, con diferencia exactamente cero en las cuatro bandas (C10, C11, C14 y C15).** La presión y la temperatura de superficie interpoladas coinciden exactamente
(diferencia máxima 0,0), así que el GFS de entrada es el mismo, y el modelo con los insumos nuevos da el mismo
número que con los originales. Salida cruda: `resultados/c2_validacion.json`.

**Tropiezo durante la corrida (no cambia el resultado).** La validación se cayó dos veces por falta de memoria
del sistema (Windows con 52,8 de 54,3 GB comprometidos por procesos de otras sesiones); el script quedó
reanudable por escena y se reintentó. La primera versión del script además tomaba la hora de la escena de
control desde el nombre del archivo (que lleva la hora del positivo); un `assert` contra el GFS guardado lo
atrapó antes de producir un número.

---

## C2b. ¿El cielo despejado de VOLCAT conoce la cota de una cumbre de 4 km?

### El caso de prueba

`mauna-loa_g17-conus_nov2022_r20260709-volcat-code-ancil.tar.gz` (1.356.717.163 B, MD5 igual al publicado),
en `D:\goes_cache\volcat_test_mauna_loa\`. GOES-17 sector CONUS, 28-11-2022 de 09:16 a 10:01 UTC, todo de
noche, 301 × 500 píxeles de 2 km sobre Hawái. VOLCAT v3.9.16, GEOCAT 3.4.5; el cielo despejado
(`geocatRTM`) sale de PFAAST con GFS 0,5° y emisividad de superficie SEEBOR. Pese al nombre, el paquete no
trae código: sólo datos de entrada, auxiliares (GFS, SST, nieve) y salidas de VOLCAT.

**Corrección a un dato del criterio.** El criterio fijó como cuadros previos a la erupción los de 09:16,
09:21 y 09:26 UTC, tomando la hora redondeada que publicó la USGS (23:30 HST = 09:30 UTC). Análisis
posteriores de la USGS sitúan el inicio a las 23:21 a 23:23 HST (09:21 a 09:23 UTC), por infrasonido y
cámaras. Los cuadros de 09:21 y 09:26 pueden tener ya lava en la caldera de Mauna Loa. No cambia el
veredicto (Mauna Loa no tuvo ningún píxel que pasara las pruebas de despejado en esos tres cuadros), pero el
dato del criterio estaba mal.

### Resultado según el criterio: no concluyente

| Sitio | Píxeles | Cota media vista | Píxeles-cuadro despejados (3 cuadros) | BT11 obs. mediana | BT11 despejado `geocatRTM` | D mediana |
|---|---|---|---|---|---|---|
| Mauna Loa (≥ 3.800 m, ≤ 10 km) | 12 | 3.944 m | 0 de 36 | | | |
| Mauna Kea (≥ 3.800 m, ≤ 10 km) | 4 | 3.910 m | 3 de 12 | 255,7 K | 273,6 K | +17,9 K |
| Control bajo (≤ 300 m) | 306 | 160 m | 22 de 918 | 251,1 K | 286,0 K | +35,0 K |
| Océano a > 10 km de la costa (desc.) | 9.157 | 0 | 2.128 de 27.471 | 257,7 K | 288,5 K | +30,8 K |

Las dos condiciones de validez fallan: Mauna Loa y Mauna Kea tienen menos de 5 píxeles-cuadro despejados, y el
control bajo da +35 K (la regla pedía ≤ 2 K). Lo que pasó: un "despejado" de 251 K en la costa y de 258 K en
el océano tropical, donde el mar está cerca de 299 K, es nube. Las cuatro pruebas del criterio (diferencia
11 − 12 µm, diferencia 3,9 − 11 µm, estabilidad en 5 min, BT11 ≥ 250 K) atajan cirro delgado, estrato bajo,
calor y nubes que se mueven, pero **no una capa de nube opaca y quieta con tope sobre 250 K**: se comporta como
superficie en las cuatro. La propia VOLCAT lo confirma: su emisividad εtot de 11 µm en esos píxeles vale 0,29
(Mauna Kea), 0,51 (control) y 0,44 (océano). Faltó una prueba de tibieza que no dependa del modelo (por ejemplo,
contra la SST del análisis CMC que trae el paquete, para el océano). No se agrega ahora porque no hay cielo
despejado que rescatar: en el océano cubierto por el modelo de elevación, el percentil 99 de la BT11 observada
es 277 K, 12 K bajo el cielo despejado.

### Lo que sí dice el caso: análisis posterior del campo de cielo despejado

**Declarado como posterior**: se escribió después de ver que la prueba del criterio no tenía cielo despejado,
y no decide nada por sí solo. No usa la observación, sólo la salida del modelo de VOLCAT, así que no puede
estar sesgado por qué píxeles estaban nublados. Script `scripts/c2b_rtm_cota.py`, salida
`resultados/c2b_rtm_cota.json`.

**La idea.** El GFS de VOLCAT viene en celdas de 0,5° (~55 km) y cada píxel dice en qué celda cae. Todo lo que
el modelo saca del GFS es igual para los ~600 píxeles de una celda. Si el cielo despejado cambia con la cota
**dentro de una celda**, el modelo usa una cota más fina que la del GFS.

1. **Océano: constante dentro de la celda.** Desviación del cielo despejado de C14 dentro de cada celda de
   mar: mediana 0,02 K (33 celdas junto a las islas; 0,02 K también en las 269 celdas de mar del dominio). El
   GFS entra al vecino más cercano, sin interpolar.
2. **Tierra: baja con la cota del píxel.** En las 7 celdas con tierra de Hawái (≥ 12 píxeles y ≥ 1 km de
   relieve), regresión del cielo despejado contra la cota del píxel con un plano en fila y columna:

   | Celda GFS | Píxeles | Cota del píxel | Cota GFS | Pendiente (K/km) | Residuo (K) |
   |---|---|---|---|---|---|
   | 218, 408 | 77 | 40 a 2.034 m | 1 m | −6,49 | 1,12 |
   | 218, 409 | 163 | 41 a 2.098 m | 77 m | −4,04 | 1,38 |
   | 219, 408 | 226 | 19 a 2.376 m | 143 m | −4,76 | 0,95 |
   | 219, 409 (Mauna Loa) | 590 | 132 a 4.018 m | 2.667 m | −3,36 | 1,32 |
   | 219, 410 | 330 | 14 a 1.168 m | 288 m | −2,65 | 0,50 |
   | 220, 408 | 167 | 31 a 1.276 m | 6 m | −3,52 | 1,40 |
   | 220, 409 (Mauna Kea) | 405 | 160 a 3.992 m | 1.234 m | −3,62 | 0,81 |

   Agrupado: −3,75 K/km. Es menos que el enfriamiento del aire (~6,5 K/km) porque arriba hay menos vapor de
   agua sobre la superficie, y el satélite ve la superficie más directo: la BT al tope baja menos que la
   temperatura del suelo. La emisividad (SEEBOR, 0,92 a 0,99) también varía de píxel en píxel y explica parte
   del residuo de ~1 K, no los 10 a 15 K de diferencia entre la costa y la cumbre.
3. **Cumbres.** El píxel más alto a ≤ 6 km de cada cumbre:

   | | Mauna Loa | Mauna Kea |
   |---|---|---|
   | Cota GVP | 4.169 m | 4.207 m |
   | Cota vista del píxel (media en 2 km, con paralaje) | 4.018 m | 3.992 m |
   | Cota del GFS en su celda | 2.667 m | 1.234 m |
   | Temperatura de superficie del GFS en la celda | 283,9 K | 288,4 K |
   | Temperatura del aire del GFS a la cota del píxel | 274,1 K | 274,2 K |
   | Cielo despejado de VOLCAT, C14 | 272,6 K | 273,6 K |
   | Emisividad de superficie que usa, C14 | 0,958 | 0,965 |

   El cielo despejado de la cumbre queda a 1,5 y 0,6 K de la temperatura del aire del GFS a esa cota, y 11 y
   15 K bajo la superficie del GFS. Es lo esperable si la temperatura de superficie se lleva a la cota del
   modelo de elevación con el perfil del GFS (lo que hace CLAVR-x según la copia no oficial de su código), y no
   lo es si se usara la superficie del GFS.

**Límites.** Un solo caso, una noche, un satélite (GOES-17) y una versión (v3.9.16). Dice cómo arma VOLCAT su
cielo despejado, no cuánto se equivoca contra la realidad. No separa si usa una tasa fija o la temperatura del
perfil a la cota (las dos dan casi lo mismo aquí), ni cómo trata el vapor de agua sobre la cumbre. La cota de
cada píxel sale del modelo de elevación Terrarium (USGS NED y SRTM, zoom 9), proyectado con paralaje sobre la
grilla del ABI; la proyección se comprobó con los propios píxeles (error de fila y columna < 0,001).

### Lo que VOLCAT hace después con ese cielo despejado (descriptivo)

- En los píxeles nublados que pasaron mis pruebas, la εtot que publica VOLCAT es coherente con usar el cielo
  despejado de `geocatRTM`: el cielo despejado "efectivo" que se despeja de su ε (con nube negra supuesta a
  195 K) queda ~3 K más frío que `geocatRTM` en Mauna Kea, el control y el océano (5 a 8 K con 210 K). No se puede atribuir
  esa diferencia al sesgo local, porque depende de mi supuesto de nube negra.
- El campo por píxel del sesgo de BT14 del entorno (`Bt14_Bias_Env_Per75`, en `geocatDIAGS1`) viene vacío en
  los 10 cuadros. `geocatASHOBJ` trae resúmenes del sesgo por objeto (máximo y media de sesgo de BT14 en el
  objeto y su entorno, píxeles elegibles y válidos para el sesgo); no los leí en valor.
- La probabilidad de ceniza IR por píxel es 0,0 (mediana) en los píxeles nublados de Mauna Kea y del control;
  en el océano va de 0 a 1 (percentil 90: 0,99).

---

## Inventario de variables (informa, no decide)

Estructura completa en `resultados/c2b_estructura_hdf.txt` y `resultados/c2b_estructura_nc.txt`. Numeración de
canales GEOCAT = bandas ABI (canal 14 = 11,2 µm, leído en `channel_central_wavelength`).

| Archivo | Qué trae | ¿Probabilidad de píxel? | ¿Sesgo local de cielo despejado? | ¿ε? | ¿β? |
|---|---|---|---|---|---|
| `geocatRTM` | Cielo despejado por canal (BT de C7, C10, C11, C13, C14, C15), emisividad de superficie por canal, índices de la celda GFS | no | no (cielo despejado sin corregir) | no | no |
| `geocatL2` | `ash_probability` (final; sólo dentro de objetos detectados: vacía hasta 09:36, 34 a 188 píxeles desde 09:41), **`ash_probability_IR`** (por píxel, ~100 mil válidos por cuadro), `_SW_IR`, `_subset`; propiedades: tope (T, P, altura), `ash_emissivity`, `Ash_Beta`, espesor óptico, carga de masa, radio efectivo y sus errores, `cloud_emissivity_ch14_tot`, `cloud_beta_8511_opaque`; térmico (VRP); máscara robusta de SO2; identificadores de grupo | **sí** | no | sí | sí |
| `geocatL2S1` | Seguimiento entre cuadros (vecinos, distancias, tiempo) y detector de crecimiento convectivo volcánico (`vcbdet`: probabilidad, CAPE, ε, BT14 mínima, objeto, nube alta) | sólo la del detector de crecimiento | no | sí (del detector) | no |
| `geocatASHOBJ` | Una fila por objeto (arreglos de 588 en el primer cuadro): probabilidades medias y términos de probabilidad (estricta, IR, laxa), **sesgo de BT14 en el objeto y en el entorno**, percentiles del sesgo de BTD 11−12 y 8,5−11, conteos robustos, NRAT medio, εtot, alturas, pareo con el cuadro anterior, emisiones nuevas, máscara de la base de volcanes de alertas | por objeto | **por objeto** | por objeto | por objeto (conteos) |
| `geocatDIAG` | Diferencias temporales (BTD, BT11, BT7,3, reflectancia), probabilidad IR del cuadro anterior, desplazamiento; ε y radio "base" | la del cuadro anterior | no | sí (base) | no |
| `geocatDIAGS1` | `Ash_Object_Mask`, `cloud_emissivity_ch14_tot`, **β 11/12, 11/13,3, 8,5/11 y 7,3/11** (total y opaco, con variantes por nivel), TPW, humedad de nube baja, `Robust_Pixel_Flag`, contrastes RGB, `Bt14_Bias_Env_Per75` (vacío aquí), banderas de historia | no | campo por píxel, **vacío en este caso** | sí | **sí** |

**Para C3.** La verdad para validar la lectura de las tablas es `ash_probability_IR` de `geocatL2` (de noche no
hay canales solares), con `cloud_emissivity_ch14_tot` y los β de `geocatDIAGS1` como entradas intermedias del
mismo píxel. Dos reparos: el paquete no trae `volcat_ash_detection_GOESR.config` ni dice qué tabla usó esta
corrida (podría no ser la de enero de 2017), y las entradas de la tabla incluyen cosas que no están aquí por
píxel (por ejemplo, el cielo despejado ya corregido por sesgo local).

---

## Condición de uso del paquete

Buscada antes de usarlo. No trae licencia, README ni condiciones; ningún atributo de los HDF ni de los NetCDF
de evento menciona licencia, restricción ni usuarios aprobados (los eventos de Chillán sí decían "Access is
restricted to approved users only"). Los NetCDF de evento declaran como institución a NOAA/NESDIS (NCCF,
entorno `dev`). El servidor de SSEC es anónimo y de sólo lectura. Uso interno de investigación con cita a
SSEC/CIMSS y NOAA; nada del paquete se sube al repo (sólo la lista de variables y números derivados). Vale
mencionarlo en el correo a Pavolonis (C4).

---

## Archivos

- Scripts (`scripts/`): `c2_validar_rt.py` (C2), `c2b_estructura.py` (inventario), `c2b_extraer.py` (HDF4 a
  npz, corre en `venv_hdf4`), `c2b_medir.py` (criterio), `c2b_rtm_cota.py` (análisis posterior).
- Salida cruda (`resultados/`): `insumos_rt.txt`, `c2_validacion.json`, `c2b_resultado.json`,
  `c2b_pixeles_sitios.csv` (cumbres, control y Haleakalā; el océano completo queda en D:), `c2b_rtm_cota.json`, `c2b_estructura_hdf.txt`, `c2b_estructura_nc.txt`.
- Fuera del repo: `D:\goes_cache\rt\` (insumos del modelo y validación), `D:\goes_cache\volcat_test_mauna_loa\`
  (paquete, extracción, npz, modelo de elevación, mapas).

Fuentes de la hora de la erupción: [USGS, Mauna Loa has begun erupting](https://www.usgs.gov/news/featured-story/mauna-loa-has-begun-erupting);
[USGS Volcano Watch, señales acústicas del inicio](https://www.usgs.gov/observatories/hvo/news/volcano-watch-using-acoustic-signals-identify-start-2022-mauna-loa-eruption);
[USGS Volcano Watch, las primeras horas](https://www.usgs.gov/observatories/hvo/news/volcano-watch-mauna-loa-2022-a-retrospective-early-hours-eruption).
