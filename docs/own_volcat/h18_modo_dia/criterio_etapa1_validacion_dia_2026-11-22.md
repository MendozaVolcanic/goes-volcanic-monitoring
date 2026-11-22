# H18 (S16b), etapa 1: ¿sabemos leer las tablas de DÍA de VOLCAT? Criterio, 22-11-2026

Escrito y commiteado antes de abrir ninguna salida del caso de día y antes de calcular ninguna probabilidad de día.
Lo único hecho antes: la lista de conjuntos `_DAY_` del volcado de estructura ya commiteado
(`docs/own_volcat/lut_h15/resultados/lut_pixel_estructura.txt`) y el listado público de
`https://bin.ssec.wisc.edu/pub/volcat/test_cases/` (22-11-2026).

## Por qué esta etapa existe

Los 60 cuadros de eventos VOLCAT de Nevados de Chillán son 56 de día y 4 de crepúsculo, ninguno de noche
(`mean_feature_solar_zenith_angle`, S15). Todas las pruebas de S15 usaron las tablas IR, validadas en Mauna Loa, que
es de noche y sobre mar. De día VOLCAT agrega tablas con 0,65 µm y con la razón de reflectancias `NRAT`. Antes de
mirar Chillán con esas tablas hay que demostrar que las sabemos leer, contra un caso de día en que VOLCAT publique su
propia probabilidad por píxel.

## La pregunta del crítico (régimen)

**¿El régimen (día/noche, mar/tierra/nieve, versión de tabla) es el mismo en que se validó el instrumento?**

| Eje | Instrumento validado hasta hoy | Caso de validación de esta etapa | Chillán |
|---|---|---|---|
| Día/noche | noche (Mauna Loa) | **día** (Fuego, GOES-16, junio de 2018; horas de los cuadros se leen del archivo) | día 56, crepúsculo 4 |
| Superficie | mar (98,7 %) | **tierra** (Guatemala) y mar del Pacífico | tierra, con nieve en la cumbre |
| Sensor y tabla | ABI GOES-17, tabla `GOESR_..._Jan11_2017` | ABI GOES-16, tabla `goesr` (la misma que leímos, SUPUESTO hasta ver los atributos del caso) | ABI GOES-19, VOLCAT v3r4 |
| Versión de VOLCAT | v3.9.16 | la del paquete r20260709 (se lee del archivo) | v3r4 operativa |

Desajustes que quedan aunque esta etapa apruebe, y que se declaran: **nieve** (Fuego no tiene; las tablas `_SNOW_`
quedarán sin validar), **cota** (Fuego 3,8 km, Chillán 3,2 km: parecido) y **versión** (la del paquete contra la
operativa de GOES-19).

## Caso de validación

Paquete público de SSEC `fuego_goes16-fulldisk_june2018_r20260709-volcat-code-ancil.tar.gz` (40 GB, sin clave),
bajado en flujo el 22-11-2026, extrayendo sólo `reference_data/` a `D:\goes_notas\s16\modo_dia\fuego\`. MD5
comprobado contra el `.md5` publicado. Sus salidas (`geocatDIAGS1`, `geocatL2`, `geocatL1`, `geocatRTM`) se usan
igual que en Mauna Loa. Nada del paquete va al repo.

Se eligió porque es el **único** caso público de ABI (misma tabla `goesr`) que puede ser de día: los otros de ABI son
Mauna Loa (noche) y los de fuego (NGFS, sin ceniza). Los de Himawari (AHI) usan otra tabla y no validan la nuestra.

## Comprobaciones antes de medir (si fallan, SIN DATO y se para)

1. **Que sea de día.** Píxeles con `pixel_solar_zenith_angle` < 85° y `ash_probability` válida: al menos 10.000 en
   el caso y al menos 100 con P_VOLCAT ≥ 0,5. Si no, el caso no sirve para el día.
2. **Que el día se use.** Fracción de píxeles de día con |`ash_probability` − `ash_probability_IR`| > 0,05. Si es
   menor que 1 %, la probabilidad que publica VOLCAT de día no depende de las tablas de día y validarlas sería
   vacío (la prueba no fallaría aunque las leyéramos mal): SIN DATO, y se informa que de día VOLCAT publica la IR.
3. **Que la tabla sea la nuestra.** Si el caso declara su tabla de píxel (atributo o nombre) y no es
   `GOESR_ASH_pixel_probability_LUT_Jan11_2017_142740`, se para.

## Las dos preguntas del instrumento (guía de auditorías §3)

1. *Si la lectura de las tablas de día estuviera rota, ¿esta prueba fallaría?* Sí, a condición de la comprobación
   2: si de día P_VOLCAT difiere de la IR, un eje mal leído de `NRAT`, de 0,65 µm o del ángulo de dispersión mueve
   nuestra P lejos de la de VOLCAT. **Placebo obligatorio:** permutar al azar `NRAT` y la reflectancia de 0,65 µm
   entre píxeles de día del mismo cuadro (semilla 20261122) y recalcular; la variante elegida **tiene que empeorar**
   (fracción dentro de 0,05 al menos 5 puntos menos, o κ al menos 0,10 menos). Si el placebo pasa igual, las tablas
   de día no deciden nada en este caso y el veredicto es SIN DATO.
2. *Si el instrumento estuviera muerto, ¿el resultado se vería distinto?* La verdad (`ash_probability`) se comprueba
   no vacía (comprobación 1) y no constante; las entradas de VOLCAT se comprueban con rango físico (ρ0,65 entre 0 y
   120 %, `NRAT` finito en al menos la mitad de los píxeles de día).

**Control positivo:** píxeles con P_VOLCAT ≥ 0,5 (la pluma de Fuego): se mide qué fracción recuperamos. **Control
negativo:** píxeles de día con P_VOLCAT < 0,01 lejos de la pluma: se mide la fracción que nosotros damos ≥ 0,5
(se espera ≈ 0 y se mide, no se razona).

## Nivel A (la lectura sola, con entradas de VOLCAT)

Entradas de `geocatDIAGS1` y `geocatL1` del propio caso: εtot, los β (12/11 total, opaco, multicapa bajo y medio;
7,3/11; 8,5/11 total y opaco), BTD(11 − 12), BT11 despejado (`geocatRTM`), superficie, `ref_rat_nir_lrc` (`NRAT_LRC`),
`NRAT` sin LRC = ρ(3,9)/ρ(0,65) de `channel_7_reflectance` y `channel_2_reflectance` si VOLCAT no lo publica
directo, ρ(0,65) = `channel_2_reflectance` (%). Ángulo de dispersión: de la variable de VOLCAT si existe; si no, lo
calculamos de la geometría sol y satélite con las lat/lon del archivo y la hora del cuadro, y se declara.

Ejes LEÍDOS de la tabla: `NRAT` 13 bins de 0 a 1,2 cada 0,1; ρ(0,65) 11 bins de 0 a 100 % cada 10
(`REF2_*_PIX`); ángulo de dispersión 2 bins (0 a 90, 90 a 180°). Las tablas `_DAY_` suman 2: una densidad por bin de
ángulo de dispersión (INFERIDO de la suma; se comprueba). Se indexa por el bin del píxel, sin factor extra.

## Variantes (elegidas en la primera mitad de los cuadros de día, validadas en la segunda)

Combinación conjunta tal cual (J), β fuera de eje recortado (modo b), prior 0,001, reglas de nube tenue R1 a R3 del
PR 75 encendidas: es la variante validada de noche y no se cambia. Lo que varía es qué tablas de día entran:

- `NRAT`: (n1) sólo las tablas con `NRAT`; (n2) sólo las `NRAT_LRC`; (n3) las dos.
- BTD × `NRAT`: (d0) fuera, como la BTD de noche; (d1) dentro.
- β(8,5/11) de día: (k0) fuera; (k1) dentro (de noche entraban).
- εtot × ρ(0,65) (`EMISS14_TOT_VREF`): (v0) fuera; (v1) dentro.
- Tablas IR además de las de día: (i0) sólo día; (i1) día más las 7 IR validadas.

48 variantes. Se elige la de mayor fracción de píxeles de día con |ΔP| ≤ 0,05 en la primera mitad de los cuadros;
empate, la más simple. Si el caso trae menos de 4 cuadros de día, se divide por píxeles pares e impares de columna y
se declara.

## Regla (segunda mitad, nivel A)

Sobre los píxeles de día (cenital solar < 85°) **de tierra** (Chillán es tierra; el mar se informa aparte):

1. ≥ 90 % con |P_nuestra − P_VOLCAT| ≤ 0,05;
2. κ de Cohen ≥ 0,90 a umbral 0,5;
3. ≥ 90 % de los P_VOLCAT ≥ 0,5 recuperados;
4. **tramo de Chillán:** en los píxeles de tierra con εtot < 0,5 (la huella de Chillán tiene mediana 0,16), las
   condiciones 1 y 3 también, siempre que haya al menos 30 píxeles con P_VOLCAT ≥ 0,5 en ese tramo; con menos, el
   tramo es SIN DATO y la etapa se declara **validada sólo en nube espesa**, que no alcanza para Chillán.
5. placebo (arriba) empeora.

**VALIDA** si cumple 1 a 5. **NO VALIDA** si falla alguna de 1 a 3 o el placebo. **VALIDADA SÓLO EN NUBE ESPESA** si
cumple 1 a 3 y 5 pero el tramo 4 es SIN DATO o falla. Sólo VALIDA abre la etapa 2.

## Nivel B de las entradas solares (necesario para Chillán, donde no hay entradas de VOLCAT)

En Chillán no tenemos `channel_2_reflectance` ni `ref_rat_nir_lrc` de VOLCAT: hay que calcularlos de la L1b. Si el
nivel A valida, con la L1b de GOES-16 de los mismos cuadros (AWS `noaa-goes16`, público) se calcula ρ(0,65) y ρ(3,9)
y se comparan con los de VOLCAT en los píxeles de día. Pide: ρ(0,65) dentro de 2 puntos de % en ≥ 90 % de los
píxeles, `NRAT` y `NRAT_LRC` dentro de 0,05 en ≥ 90 %. Si no cumple, la etapa 2 en Chillán no se hace con nuestras
entradas solares y se informa por qué. Las entradas IR (εtot, β) siguen con el problema conocido del cielo despejado
de 11 µm (PR 76); en la etapa 2 se tratan como la etapa 3 del 21-11: bandas S0, S1, S2.

## Lo que no se hace

No se ejecuta código del paquete de SSEC. Nada de VIIRS. Al repo van scripts, números derivados y figuras; ni tablas,
ni HDF, ni archivos de evento.
