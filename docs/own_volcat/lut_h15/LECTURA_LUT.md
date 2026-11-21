# Lectura de las tablas de probabilidad de VOLCAT para ABI (C3, etapa 1), 21-11-2026

Criterio subido antes de abrir las tablas: `criterio_etapa1_lectura_2026-11-21.md` (commit 287e3cb). Estructura
cruda: `resultados/lut_pixel_estructura.txt` y `resultados/lut_objeto_estructura.txt` (nombres, formas, atributos y
estadísticas; no las tablas). Scripts: `scripts/lut_estructura.py` (volcado) y `scripts/lut_exportar.py` (exporta
las densidades de la tabla de píxel a `D:\goes_cache\lut_h15\lut_pixel.npz`, fuera del repo). Ambos corren con
`D:\goes_notas\busqueda_2026-11-20\venv_hdf4\Scripts\python.exe -I`. No se ejecutó nada del paquete de SSEC.

Cada afirmación lleva su grado: **LEÍDO** (escrito en la tabla o en el `.config`), **INFERIDO** (de la forma de los
arreglos o de una fuente publicada, sin contradicción con lo leído) o **SUPUESTO** (sin apoyo escrito; lo valida o
lo descarta la etapa 2).

## 1. Para geólogo: qué son estas tablas

VOLCAT decide si un píxel tiene ceniza comparando cómo se ve ese píxel en el infrarrojo con cómo se veían miles de
píxeles de ceniza y miles de píxeles de nube (o de cielo despejado) en escenas de entrenamiento. Las tablas son esos
dos "álbumes de referencia": para cada combinación de emisividad de la nube a 11 µm (εtot, cuánto tapa la nube) y de
razones β entre canales (la forma del espectro), cuántos píxeles de ceniza y cuántos de nube cayeron ahí. Si en esa
casilla había 200 veces más ceniza que nube (relativo a cada álbum), el píxel suma evidencia a favor de ceniza.

Tres cosas que se leen directo en la tabla y que importan para Chillán:

1. **El prior es 0,1 %** (`PIXEL_ASH_PROB_CLIMO = 0.001`, LEÍDO). Antes de mirar el píxel, VOLCAT supone que uno de
   cada mil píxeles es ceniza; la evidencia espectral tiene que levantar eso. Es el mismo prior que usó nuestro SECO
   propio de la etapa 2.
2. **Las tablas se entrenaron sólo dentro de β(12/11) entre 0 y 1,05** (más allá las dos densidades valen el piso,
   ~1e-9, y la razón es 1). Un píxel con β fuera de ese rango no aporta evidencia, ni a favor ni en contra.
3. **Cuánta evidencia da una sola tabla.** En la tabla IR de εtot × β(12/11) sobre tierra, un píxel con εtot entre
   0,2 y 0,5 y β entre 0,70 y 0,75 tiene una razón ceniza/nube de 205; con β entre 0,95 y 1,0 (lo típico de una nube
   de agua o hielo, y de una pluma sin firma) la razón es 0,11, es decir, evidencia en contra. Con εtot bajo
   (0,03 a 0,10) la tabla es casi neutra en todo el rango de β (0,06 a 28). Para pasar del 0,1 % al 80 % hacen falta
   unas 4.000 veces de evidencia combinada.

## 2. Archivos y qué contienen

| | Tabla de píxel (`..._142740.hdf`) | Tabla de objeto (`..._142742.hdf`) |
|---|---|---|
| Creada | 11-01-2017 14:27:40 (LEÍDO, `CREATION_DATE`) | 11-01-2017 14:27:42 |
| Sensor | `SENSOR_SERIES = goesr` | igual |
| Entrenamiento | MODIS: `modis_pixel_training_ASH_v1` / `_NOASH_v1`, histogramas `modis_merged_pixel_histograms_Apr26_2013` (LEÍDO) | MODIS, `..._Apr30_2013` |
| Prior | `PIXEL_ASH_PROB_CLIMO = 0.001`, `PIXEL_CLD_PROB_CLIMO = 0.999` | `OBJECT_ASH_PROB_CLIMO = 0.001` |
| Contenido | 322 conjuntos: densidades por clase (`_ASH_` y `_CLD_`), superficie (`LAND`, `WATER`, `SNOW`) y régimen (`DAY`, `NIGHT`, `IR`), ejes, umbrales de pertenencia al objeto | densidades por clase de rasgos del OBJETO, por régimen, en 9 clases de área; tablas de robustez |

El `.config` (`volcat_ash_detection_GOESR.config`, LEÍDO) nombra estas dos tablas en sus líneas 2 y 3.

## 3. Ejes y bordes (tabla de píxel)

**El orden de los ejes.** Cada densidad tiene un atributo global con su mismo nombre que la declara en IDL, por
ejemplo `BETA1112_TOT_BETA7311_TOT_IR_PIX = 'dblarr(h.nbins_cos_satzen,h.nbins_emiss14_tot,h.nbins_beta1112,h.nbins_beta7311)'`
(LEÍDO). IDL guarda en orden de columna, así que en numpy los ejes salen al revés: `(β7311, β1112, εtot, cos_satzen)`
= (21, 42, 6, 1). Las 59 formas de densidades no nulas calzan con esta regla sin excepción (INFERIDO por forma).

**Los bordes de los ejes de β, EMS7 y NRAT** están en atributos globales `<VAR>_MIN_PIX`, `<VAR>_MAX_PIX`,
`<VAR>_DB_PIX` (LEÍDO). El número de bins que trae cada tabla es exactamente el de la función `HISTOGRAM` de IDL con
esos parámetros, `floor((MAX − MIN)/DB) + 1`, en los seis ejes (42, 33, 21, 21, 25, 13). Por eso el bin `i` cubre
`[MIN + i·DB, MIN + (i+1)·DB)` (INFERIDO por conteo; el último bin es `[MAX, MAX + DB)`).

**Los ejes de εtot y de BT11 de cielo despejado** tienen conjuntos de bordes propios (LEÍDO):

| Eje | Fuente | Bins | Bordes |
|---|---|---|---|
| εtot(11) | `EMISS14_TOT_BINS_FULL_PIX` | 6 | 0,01 · 0,03 · 0,10 · 0,20 · 0,50 · 0,90 · 1,00 |
| BT11 cielo despejado | `BT14_CLR_BINS_FULL_PIX` | 5 | 160 · 255 · 260 · 265 · 270 · 400 K |
| β(12/11) total, multi bajo, multi medio | `BETA1112_MIN/MAX/DB_PIX` | 42 | −0,10 a 1,95 cada 0,05 |
| β(12/11) opaco | `BETA1112_OPAQUE_MIN/MAX/DB_PIX` | 33 | −0,10 a 1,50 cada 0,05 |
| β(8,5/11) | `BETA8511_..._PIX` | 21 | −0,10 a 1,90 cada 0,10 |
| β(7,3/11) | `BETA7311_..._PIX` | 21 | −0,10 a 1,90 cada 0,10 |
| εp(3,9) (`EMS7`) | `EMS7_..._PIX` | 25 | 0,80 a 2,00 cada 0,05 |
| `NRAT` | `NRAT_..._PIX` | 13 | 0,0 a 1,2 cada 0,1 |
| BTD 11 − 12 en las tablas `BTD1112_*` | ver abajo | 33 | −3,0 a 5,0 cada 0,25 |
| cos(cenital satelital) | `COS_SATZEN_BINS_FULL_PIX` | 1 | 0 a 1 (sin dependencia) |
| ángulo de dispersión (sólo día) | `SCATANG_BINS_FULL_PIX` | 2 | 0 · 90 · 180° |

**BTD 11 − 12, la única duda de eje.** La declaración IDL dice `h.nbins_btd1112` y el atributo
`NBINS_BTD1112_PIX` vale 6 (con `BTD1112_BINS_PIX` = −10, −1, −0,5, −0,25, −0,1, 0), pero el eje en las tablas mide
33. Treinta y tres es el conteo de `BTD1112_EB_MIN/MAX/DB_PIX` (−3 a 5 cada 0,25). Con ese eje las densidades tienen
la forma esperada: la ceniza concentra su masa entre −1,25 y −0,25 K (más un 11 % acumulado en el primer bin, BTD
< −2,75 K) y la nube tiene su máximo entre 0 y +0,25 K, sin masa sobre +2 K. INFERIDO por conteo y por forma; el
eje de 6 bins no se usa en ninguna tabla de píxel.

**Normalización (LEÍDO por cálculo).** Cada densidad suma 1 sobre el arreglo entero, εtot incluido: son
distribuciones conjuntas `P(x, y, εtot | clase)`, no condicionales por bin de εtot. No hay ceros: cada tabla tiene un
piso (1,6e-9 en tierra IR, 5,2e-10 en agua IR, 2,7e-9 en tierra de noche), INFERIDO como suavizado del histograma.
Fuera del dominio entrenado ambas clases valen el piso y la razón ceniza/nube es ~1.

**Las tablas con β(11/13,3)** (`BETA1113_*`) están en cero y `BETA1113_PIX_LUT = 'NO'` (LEÍDO): con ABI no se usan,
aunque el `.config` tenga sus banderas en 1.

## 4. Qué es `NRAT`

No está definido en ningún texto. Lo que se lee: eje de 0 a 1,2 cada 0,1; `NRAT_MAX_VALID = 20`;
`NRAT_HOT_SPOT_MIN = 2` (junto a `BTD3911_HOT_SPOT_MIN = 15`); `NRAT_MARINE_STRATUS_CHECK = 1`; aparece sólo en
tablas `_DAY_`, con una variante `_LRC_`; y el archivo `geocatDIAGS1` de Mauna Loa trae `ref_rat_nir_lrc` (LEÍDO). Lo
inferido: **razón de reflectancia del infrarrojo cercano**, ρ(3,9 µm)/ρ(0,65 µm), que es el eje de 13 bins de la
Tabla 4.5 de la tesis de 2014; un punto caliente la dispara sobre 2 porque 3,9 µm suma emisión. LRC es el "centro
radiativo local" de Pavolonis (el valor del píxel más opaco de la vecindad). Es canal solar: **de noche y en
sólo IR no entra**.

## 5. Qué clasificadores entran en cada régimen con ABI

Régimen (LEÍDO en atributos): día si cenital solar < 85° (`DAYTIME_SOLZEN`), noche si ≥ 91° (`NIGHTTIME_SOLZEN`);
entre 85 y 91° (terminador) INFERIDO sólo IR. El `.config` (LEÍDO) apaga el uso de 8,5 µm en la probabilidad de
píxel cuando no hay datos temporales (`2 !... do not use at all`, con `0 !history flag`): **las tablas con β(8,5/11)
quedan fuera**. Las de β(11/13,3) están vacías. Con eso:

| Régimen | Tablas que quedan (todas con εtot como eje) | Canales |
|---|---|---|
| **Sólo IR** (`ash_probability_IR` de `geocatL2`, INFERIDO por el nombre) | εtot × β(12/11) total; × β opaco; × β multicapa bajo; × β multicapa medio; εtot × BTD(11−12) × BT11 despejado; β(12/11) total × β(7,3/11) total | 7,3 · 11 · 12 |
| **Noche** (`ash_probability_SW_IR`, INFERIDO: "SW" = 3,9 µm) | β(12/11) total, opaco, multi bajo, multi medio, cada uno × εp(3,9); BTD(11−12) × εp(3,9) × BT11 despejado; β(12/11) × β(7,3/11) | 3,9 · 7,3 · 11 · 12 |
| **Día** | β(12/11) en sus 4 variantes × `NRAT` y × `NRAT_LRC`; BTD × `NRAT` (y LRC) × BT11 despejado; εtot × reflectancia 0,65 µm; β(12/11) × β(7,3/11) | 0,65 · 3,9 · 7,3 · 11 · 12 |

Las texturas que activa el `.config` (`EMISS14_TOT_BT14_SDEV_NIGHT` e `_IR`, `EMISS14_TOT_REF2_SDEV`) no tienen tabla
de píxel: están en la tabla de objeto (`EMISS14_BT14_SDEV_PDF_*_OBJ`). Superficie: tierra y agua en los tres
regímenes, nieve sólo de día.

**Los β "multicapa bajo" y "multicapa medio"** son β calculados suponiendo que bajo la pluma hay una nube baja o
media en vez de superficie (SECO 1). `geocatDIAGS1` los trae ya calculados (`cloud_beta_1112_tot_multi_low`,
`_multi_mid`, y además `_multi_nwp`), junto con `lower_cloud_idx`. Nosotros no tenemos cómo calcularlos sin el nivel
de nube baja que elige VOLCAT: es una entrada que la etapa 2 tendrá que tomar de VOLCAT o aproximar.

## 6. Cómo se combinan (SUPUESTO; lo decide la etapa 2)

Nada en las tablas ni en el `.config` describe la combinación. Lo publicado (SECO 1, Pavolonis et al. 2015, ec. 1 y
Tabla 3) es Bayes ingenuo: la probabilidad posterior es

`P = p·Π Aᵢ / (p·Π Aᵢ + (1 − p)·Π Cᵢ)`, con `p = 0,001` y `Aᵢ`, `Cᵢ` las densidades de ceniza y nube de cada
clasificador en la casilla del píxel.

Dos preguntas que las tablas no contestan y que la etapa 2 tiene que probar como variantes:

1. **Densidad conjunta o condicional por εtot.** Las tablas son conjuntas (suman 1 con εtot incluido). Si se usan
   tal cual, el factor `P(εtot | ceniza)/P(εtot | nube)` entra una vez por cada clasificador (6 veces en sólo IR). La
   alternativa es dividir cada tabla por su marginal de εtot (condicional) y multiplicar el factor de εtot una sola
   vez, o ninguna.
2. **Qué hacer con un β inválido** (fuera de [MIN, MAX + DB) o sin cálculo): al primer bin (como en la tesis),
   recortado al bin extremo, o el clasificador se omite.

## 7. Comprobación de cordura (regla del criterio)

Razón de densidades ceniza/nube en la tabla IR de εtot × β(12/11) total (todos los bins en
`resultados/lut_cordura.txt`, script `scripts/lut_cordura.py`):

| Estado | Tierra, εtot 0,2 a 0,5 | Tierra, εtot 0,5 a 0,9 | Agua, εtot 0,2 a 0,5 | Agua, εtot 0,5 a 0,9 |
|---|---|---|---|---|
| Ceniza típica: β 0,70 a 0,75 | 205 | 196 | 1.970 | 2.140 |
| Ceniza típica: β 0,80 a 0,85 | 25 | 149 | 16 | 669 |
| Nube: β 0,95 a 1,00 | 0,11 | 0,11 | 0,024 | 0,046 |
| Nube: β 1,00 a 1,05 | 0,0030 | 0,0011 | 0,0050 | 0,00063 |
| β ≥ 1,05 | 0,997 (piso) | 0,997 | 1,0 | 1,0 |

**Cumple**: la ceniza típica da razón > 1 y la nube con β cerca de 1 da razón < 1; ningún eje está invertido.
**Desviación declarada**: el criterio pedía razón < 1 para "nube de hielo con β ≥ 1,05", y ahí las dos densidades
están en el piso (razón ~1): ese estado está fuera del dominio de entrenamiento (`BETA1112_TOT_MAX_VALID = 1.05`),
no al revés. En el bin inmediatamente inferior (1,00 a 1,05) la razón es de 0,0006 a 0,005.

## 8. Tabla de objeto (resumen; no se usa para validar)

- Densidades `EMISS14_BETASW1_TOT_PDF_<régimen>_<clase>_OBJ` y similares, de forma (9, n, 10): 9 clases de área del
  objeto (`AREA_BINS_FULL_OBJ` de 0,01 a 10.000, unidad no escrita; INFERIDO km²), `n` predictores = producto de bins
  gruesos (εtot en 4 bins 0 · 0,05 · 0,1 · 0,3 · 1; β(12/11) en 7; β(8,5/11) y β(7,3/11) en 5; desviación estándar
  de BT11 en 11) y `NBINS_SAMPLE_OBJ = 10` "muestras". Cada una suma 10 (una por muestra). Declaradas
  `dblarr(n_samples, n_predictors, n_area)`.
- Qué es una "muestra" y cómo se arma el vector de predictores de un objeto no está escrito. INFERIDO: el objeto se
  resume en 10 muestras (quizá percentiles o sorteos de sus píxeles) y cada una se busca en la tabla de su clase de
  área. Hay además versiones por fracción de área (`_FRAC_`) y tablas de robustez (`ROBUST_BT14CLR*`, enteros 0 a 4,
  7 dimensiones).
- **Consecuencia para la etapa 3:** la probabilidad de OBJETO no se puede reconstruir con lo leído sin suponer qué es
  una muestra, y el caso de Mauna Loa no la publica por píxel. La vara de escena de H15 (objeto ≥ 0,8) se informará
  con la probabilidad de píxel resumida por objeto y se dirá que no es la de VOLCAT.

## 9. Veredicto de la etapa 1

**Lectura suficiente para seguir a la etapa 2.** Los clasificadores de sólo IR (los que se comparan contra
`ash_probability_IR`, todo de noche en Mauna Loa) tienen todos sus ejes LEÍDOS, salvo el eje de BTD de una tabla,
INFERIDO con comprobación de conteo y forma. Densidades de ceniza y nube identificadas. Quedan como SUPUESTO la regla
de combinación y el manejo de β inválido; la etapa 2 los prueba como variantes en una mitad de los cuadros y los
valida en la otra.
