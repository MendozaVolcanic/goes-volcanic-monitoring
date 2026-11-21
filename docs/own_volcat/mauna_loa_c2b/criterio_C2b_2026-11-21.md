# Criterio declarado ANTES de medir: C2 (modelo radiativo repuesto) y C2b (cielo despejado de VOLCAT en Mauna Loa), 21-11-2026

Escrito antes de calcular ninguna diferencia de esta prueba. Lo único hecho antes: bajar los insumos (abajo),
extraer el paquete de Mauna Loa, leer la **estructura** de sus archivos (nombres de variables, atributos,
longitudes de onda centrales de los canales, rango de latitud y longitud, `pixel_surface_type`) y cargar el
modelo radiativo de H3 sin correrlo sobre ninguna escena. Ningún BT despejado, ninguna diferencia y ninguna
probabilidad se miró todavía.

Plan del que salen: `docs/own_volcat/PLAN_2026-11-21_LUT_VOLCAT.md` (PR 69), caminos C2 y C2b.

---

## C2. ¿El modelo radiativo de H3 vuelve a dar lo mismo con los insumos bajados de nuevo?

**Por qué.** El 20-11 se borró la carpeta `dl\` de H3 con su scratchpad: continuo de vapor de agua MT_CKD 4.3
y funciones de respuesta espectral (SRF) del ABI. Sin ella el modelo no corre, y H11, la etapa 2, H12, H13 y C3
dependen de él. Se bajaron de nuevo de las mismas fuentes que usó H3 (leídas en el registro de esa sesión):

| Insumo | Fuente | Archivo | Tamaño | Huella |
|---|---|---|---|---|
| Continuo MT_CKD 4.3 | AER, `github.com/AER-RC/MT_CKD_H2O`, tag `4.3` (commit 3e043b4 del 17-04-2024, igual a `master`) | `absco-ref_wv-mt-ckd.nc` | 83.576 B | blob git ff75b0e (el mismo que H3 bajó de `master`) |
| SRF ABI FM4 (GOES-19), bandas 10, 11, 14 y 15 | CIMSS, `cimss.ssec.wisc.edu/goes/calibration/SRF/abiFM4/` | `ABI_FM4_10Mar2016_CHxx.SRF` | 15,9 a 25,5 KB | SHA-256 en `resultados/insumos_rt.txt` |

Copia en `D:\goes_cache\rt\mtckd\` y `D:\goes_cache\rt\srf\`. El código lee la carpeta de la variable
`H3_RT_DL` (y la tabla de coeficientes de `H3_RT_LBL`); sin ellas, la de siempre.

**Prueba.** Los archivos `rt_h11\<par>_<rol>.npz` de la caché rescatada guardan, por píxel, el cielo despejado
R_clr que calculó H11 con los insumos originales. De los archivos de pares con origen H3, ordenados por nombre,
se toman 5 a intervalos iguales; en cada uno, hasta 300 píxeles al azar (semilla 0). Se recalcula R_clr con el
mismo camino (`rt_niveles.radiancias_pixel`), desde la misma escena y el mismo GFS, y se pasa a BT con el
Planck del L1b de la escena.

**Regla.** Error |BT_clr nueva − BT_clr guardada| de C14, percentil 95 sobre todos los píxeles: **≤ 0,3 K =
el modelo está repuesto**; > 0,3 K = no lo está, y C3 no parte hasta encontrar la diferencia. Se informan
también C10, C11 y C15, el máximo, y la diferencia en presión y temperatura de superficie interpoladas (para
separar un cambio de insumo GFS de un cambio de modelo).

---

## C2b. ¿El cielo despejado de VOLCAT conoce la cota de una cumbre de 4 km?

### La física, antes que los números

VOLCAT decide si un píxel tiene ceniza comparando lo que ve el ABI con lo que vería sin nube ni ceniza (el
cielo despejado), calculado con un modelo numérico (GFS) y un modelo radiativo. En una cumbre, el modelo
numérico pone el terreno más bajo de lo real porque promedia el relieve en celdas de decenas de kilómetros.
Más abajo el aire es más tibio y hay más vapor; si nadie lo corrige, el cielo despejado modelado queda más
tibio que la cumbre real. Es lo que medimos en Chillán: nuestro cielo despejado con GFS queda 7 a 9 K más tibio
que lo observado en la cumbre, porque el GFS pone el terreno a ~1,7 km y no a ~3,2 km.

VOLCAT tiene dos formas posibles de evitarlo: (1) llevar la temperatura de superficie a la cota real con la tasa
de enfriamiento del perfil, como hace CLAVR-x según una copia no oficial de su código; o (2) no corregir la
cota y restar después el sesgo local medido en píxeles despejados vecinos (ventana de 12 píxeles, según su
configuración pública para ABI). El caso de prueba de Mauna Loa trae el cielo despejado **tal como sale del
modelo radiativo de VOLCAT** (`geocatRTM`, canal 14 = 11,2 µm), antes de cualquier sesgo local, y la
observación (`geocatL1`, mismo canal). Mauna Loa (4.169 m) y Mauna Kea (4.207 m) son cumbres de 4 km sobre
una isla en el océano: si el cielo despejado de `geocatRTM` sigue a la observación en la cumbre, VOLCAT corrige
la cota dentro del modelo radiativo; si queda muy tibio, depende del sesgo local.

### Datos

Paquete `mauna-loa_g17-conus_nov2022_r20260709-volcat-code-ancil.tar.gz` (1.356.717.163 B, MD5
79dc779f52012981c01ae46f194dbf16, igual al `.md5` publicado), de `https://bin.ssec.wisc.edu/pub/volcat/test_cases/`,
en `D:\goes_cache\volcat_test_mauna_loa\`. GOES-17, sector CONUS (PACUS), 28-11-2022, 10 cuadros de 09:16 a
10:01 UTC (23:16 a 00:01 hora de Hawái, **todos de noche**), subconjunto de 301 × 500 píxeles de 2 km.
VOLCAT v3.9.16, GEOCAT 3.4.5; `geocatRTM` dice `Imager_RTM_Source = pfaast`, GFS 0,5°, emisividad de
superficie SEEBOR. Numeración de canales GEOCAT = bandas ABI (longitudes centrales leídas: canal 7 = 3,9 µm,
canal 14 = 11,2 µm, canal 15 = 12,3 µm).

**Cuadros que deciden: 09:16, 09:21 y 09:26 UTC**, antes de que empezara la erupción (USGS/HVO la sitúa cerca
de las 23:30 hora de Hawái del 27-11 = 09:30 UTC; los nombres de los registros de VOLCAT dicen `HN` hasta 09:26 y
`HY` desde 09:31, que leo como "sin" y "con" objeto caliente, inferencia mía). Después de 09:30 la cumbre de
Mauna Loa tiene lava y pluma, y su BT ya no es la de una superficie despejada. Los 7 cuadros siguientes se
informan sólo como descripción, y sólo en Mauna Kea y el control.

**Elevación y tierra o mar.** `pixel_surface_type` viene vacío (0 en los 150.500 píxeles) y la navegación no
corrige terreno (`Terrain_Corrected_Nav_Option = 0`, `pixel_latitude_tc` igual a `pixel_latitude`). Se usa un
modelo de elevación externo: teselas Terrarium (AWS Open Data, Tilezen; en EE.UU. compiladas de USGS NED y
SRTM), zoom 9 (~290 m), en `D:\goes_cache\volcat_test_mauna_loa\dem\`. Cada celda del modelo de elevación se
proyecta con su altura sobre la grilla fija del ABI (paralaje: el satélite ve una cumbre de 4 km corrida
~1,5 km hacia el lado opuesto al satélite) y se asigna al píxel ABI donde cae. Por píxel: elevación media vista
y fracción de celdas con elevación > 0 (tierra). La asignación se comprueba antes de usar: proyectar las
lat/lon de los propios píxeles de `geocatL1` a altura 0 tiene que devolver su fila y columna.

### Sitios (fijados ahora)

- **Mauna Loa:** píxeles con fracción de tierra 1, elevación media vista ≥ 3.800 m y a ≤ 10 km de la cumbre
  (19,475 N; 155,608 O).
- **Mauna Kea:** igual, a ≤ 10 km de la cumbre (19,821 N; 155,468 O).
- **Control bajo:** píxeles con fracción de tierra 1 y elevación media vista ≤ 300 m, en cualquier isla del
  subconjunto, a > 15 km del cráter de Kīlauea (19,408 N; 155,283 O; lago de lava activo en nov-2022) y a
  > 15 km de la cumbre de Mauna Loa.
- **Descriptivo, no decide:** todos los píxeles de tierra pura por tramos de elevación de 500 m (sesgo contra
  cota), Haleakalā (3.055 m) y el océano a > 10 km de la costa.

### Píxel despejado (sin usar nada de la salida que se mide)

La salida que se mide es el cielo despejado de `geocatRTM`; ninguna prueba de despejado lo usa, ni usa el GFS,
ni las salidas de VOLCAT. Sólo la observación del ABI (`geocatL1`), en cada píxel y cuadro:

1. **Sin cirro semitransparente:** BT11 − BT12 (canal 14 − canal 15) entre −1,0 y +3,0 K. El cirro delgado
   da diferencias de 3 a 8 K; el aire seco de una cumbre de 4 km, menos de 1 K.
2. **Sin estrato bajo ni calor:** BT3,9 − BT11 (canal 7 − canal 14) entre −2,0 y +4,0 K. De noche, el estrato
   bajo y la niebla emiten menos a 3,9 µm y la dan bajo −2 K; la lava o un incendio la suben sobre +4 K.
3. **Estable en el tiempo:** la BT11 cambia ≤ 1,0 K en promedio contra los cuadros vecinos de ±5 min (los
   que existan entre los 10). Una nube que pasa cambia la BT11 varios kelvin en 5 minutos; la superficie
   despejada de noche se enfría unas décimas.
4. **Sin tope frío:** BT11 ≥ 250 K. De noche la cumbre despejada está cerca de 270 K, y las cumbres quedan
   sobre la inversión de los alisios, donde las nubes son raras.

### Lo que se mide

D = BT11 despejado de `geocatRTM` (canal 14) − BT11 observado (canal 14 de `geocatL1`), en kelvin, en cada
píxel y cuadro despejado. Por sitio: mediana de D, n de píxeles-cuadro, percentiles 10 y 90.

### Regla (fijada ahora)

- **Validez:** cada cumbre necesita ≥ 5 píxeles-cuadro despejados en los tres cuadros que deciden, y el
  control bajo necesita |mediana D| ≤ 2 K (si el cielo despejado de VOLCAT falla también en el llano, la
  diferencia en la cumbre no habla de la cota). Si no se cumple: **no concluyente**, y se dice por qué.
- **|mediana D| ≤ 2 K en las dos cumbres:** VOLCAT corrige la cota dentro de su modelo radiativo (o su GFS ya
  la trae). En C3, el cielo despejado propio se corrige por cota al estilo CLAVR-x.
- **|mediana D| ≥ 5 K en las dos cumbres:** el modelo radiativo de VOLCAT no corrige la cota y depende del sesgo
  local de 12 píxeles. En C3, el cielo despejado propio se corrige con sesgo local, como VOLCAT.
- **Cualquier otro caso** (entre 2 y 5 K, o las dos cumbres en lados distintos): **no concluyente**; en C3 se
  prueban las dos correcciones.

Se informa además, sin que decida: el signo de D (positivo = modelo más tibio que la cumbre, el caso de
Chillán), D contra elevación por tramos, la emisividad εtot de 11 µm que publica VOLCAT
(`geocatDIAGS1`, `cloud_emissivity_ch14_tot`) en esos mismos píxeles despejados comparada con la que daría
el cielo despejado de `geocatRTM` sin corregir (si VOLCAT publica ε ≈ 0 donde `geocatRTM` daría un valor lejos
de 0, el sesgo se corrige después del modelo radiativo), el sesgo de BT14 del entorno que publica VOLCAT
(`Bt14_Bias_Env_Per75`) donde exista, y la probabilidad de ceniza por píxel en esos píxeles.

### Inventario de variables (informa, no decide)

Qué traen `geocatL2`, `geocatL2S1`, `geocatASHOBJ`, `geocatDIAG` y `geocatDIAGS1`: probabilidad de ceniza por
píxel, sesgo local del cielo despejado, ε, β. Si traen probabilidad, es la verdad para validar la lectura de
las tablas en C3. Sale de `scripts/c2b_estructura.py`, leído antes de escribir este criterio.

### Condición de uso del paquete

Buscada antes de usarlo: el paquete no trae archivo de licencia, README ni código (sólo datos); ningún atributo
de los HDF ni de los NetCDF de evento menciona licencia, restricción ni usuarios aprobados (los eventos de
Chillán sí decían "Access is restricted to approved users only"); los eventos declaran como institución a
NOAA/NESDIS (`production_environment = dev`, NCCF). El servidor es anónimo y de sólo lectura ("read for
everyone"). Uso interno de investigación, con cita a SSEC/CIMSS y NOAA; nada de este paquete se sube al repo.
