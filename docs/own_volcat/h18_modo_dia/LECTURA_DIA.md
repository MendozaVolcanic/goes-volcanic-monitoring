# Lectura de las tablas de DÍA de VOLCAT para ABI (H18, etapa 1), 22-11-2026

Complementa `docs/own_volcat/lut_h15/LECTURA_LUT.md` (tablas IR y de noche). Mismos grados: **LEÍDO** (escrito en
la tabla), **INFERIDO** (de la forma o de una fuente, sin contradicción) y **SUPUESTO** (lo valida o descarta la
comparación contra el caso de día). Números: `resultados/dia_lectura.txt`, script `scripts/dia_lectura.py` (lee el
npz exportado fuera del repo; sólo escribe marginales y razones, no la tabla).

## 1. Para geólogo

De día VOLCAT tiene un dato que de noche no tiene: cuánta luz solar refleja el píxel a 0,65 µm (visible rojo) y a
3,9 µm (infrarrojo de onda corta). Su tabla de día usa sobre todo la **razón entre las dos** (`NRAT`). En la tabla,
los píxeles de ceniza de entrenamiento tienen `NRAT` alto (la masa está entre 0,4 y 1,2) y los de nube de agua o
hielo lo tienen bajo (entre 0 y 0,4). Es una separación fuerte: en el tramo de εtot de las plumas de Chillán (0,10 a
0,20), con β(12/11) de 0,80 a 0,85, pasar de `NRAT` 0,3 a 0,9 lleva la razón ceniza/nube de 2,2 a 193. Incluso
con β de 0,95 a 1,00 (sin firma de onda larga, como dice VOLCAT de los píxeles de Chillán), `NRAT` de 1,1 da una
razón de 3,4, contra 0,06 a 0,1 con `NRAT` bajo.

Por qué importa: en S15 la huella de Chillán no juntaba evidencia en el infrarrojo. Si de día su `NRAT` es alto, las
tablas de día podrían juntar las décadas que faltaban. Por eso vale la pena medirlo, pero sólo después de comprobar
que sabemos leerlas contra un caso de día.

## 2. Qué tablas hay de día (tabla de píxel `..._142740.hdf`)

LEÍDO en la declaración IDL de cada conjunto y en su forma. Orden numpy = inverso del `dblarr`.

| Tabla | Ejes (numpy) | Forma |
|---|---|---|
| `BETA1112_TOT_NRAT_DAY` (y `_OPAQUE_`, `_TOT_MULTI_LOW_`, `_TOT_MULTI_MID_`) | `NRAT`, β(12/11), εtot, ángulo de dispersión, cos cenit sat. | (13, 42, 6, 2, 1) |
| las mismas con `NRAT_LRC` | igual | (13, 42, 6, 2, 1) |
| `BTD1112_NRAT_DAY` y `_NRAT_LRC_` | `NRAT`, BTD(11 − 12), BT11 despejado, εtot, ángulo, cos | (13, 33, 6, 5, 2, 1) |
| `EMISS14_TOT_VREF_DAY` | ρ(0,65), εtot, ángulo, cos | (11, 6, 2, 1) |
| `BETA1112_TOT_BETA7311_TOT_DAY` | β(7,3/11), β(12/11), εtot, ángulo, cos | (21, 42, 6, 2, 1) |
| `BETA1112_TOT_BETA8511_TOT_DAY` y `_OPAQUE_` | β(8,5/11), β(12/11), εtot, ángulo, cos | (21, 42, 6, 2, 1) |
| las de β(11/13,3) | | todas en cero (no se usan con ABI, igual que de noche) |

Cada una en tres superficies: `LAND`, `WATER` y `SNOW` (la nieve sólo existe de día). Ojo con el eje de
`BTD1112_NRAT_DAY`: la declaración trae un `BT14_CLR` más que la de noche; la forma lo confirma (5 bins).

## 3. Ejes nuevos

| Eje | Atributos | Bins | Bordes |
|---|---|---|---|
| `NRAT` | `NRAT_MIN/MAX/DB_PIX` | 13 | 0,0 a 1,2 cada 0,1 (último `[1,2, 1,3)`) |
| ρ(0,65) (`REF2`) | `REF2_MIN/MAX/DB_PIX` | 11 | 0 a 100 % cada 10 (último `[100, 110)`); `REF2_MAX_VALID` = 120 |
| ángulo de dispersión | `SCATANG_BINS_FULL_PIX` | 2 | 0 · 90 · 180° |

LEÍDO los bordes; la convención `[MIN + i·DB, MIN + (i+1)·DB)` es la misma de las tablas IR (INFERIDO allá por
conteo, validado de noche). `REF2` en %: INFERIDO por el máximo de 100 y el `REF2_MAX_VALID` de 120, coherente con
`channel_2_reflectance` en % de los archivos de diagnóstico de VOLCAT (Mauna Loa).

## 4. Normalización (LEÍDO por cálculo)

De noche cada tabla sumaba 1 sobre el arreglo entero. **De día cada tabla suma 2, y cada rebanada de ángulo de
dispersión suma 1** (las 84 tablas no vacías, `dia_lectura.txt`). Es decir: son densidades conjuntas de los demás
ejes **condicionales al ángulo de dispersión**. Al usarlas, el píxel se busca en la rebanada de su ángulo y no hay
factor extra por ángulo (las dos clases están condicionadas igual).

## 5. Qué es `NRAT` (INFERIDO; lo comprueba el caso de día)

No está definido en texto. Lo que se lee: eje de 0 a 1,2; `NRAT_MAX_VALID` = 20; `NRAT_HOT_SPOT_MIN` = 2 junto a
`BTD3911_HOT_SPOT_MIN` = 15 K (un punto caliente lo dispara); sólo aparece de día; los diagnósticos de VOLCAT traen
`ref_rat_nir_lrc` y las reflectancias de los canales 2 (0,65 µm) y 7 (3,9 µm). Inferido: **ρ(3,9)/ρ(0,65)**. La
comparación del caso de día dirá si `ref_rat_nir_lrc` es esa razón (en el píxel de centro radiativo local) y si el
`NRAT` sin LRC se reconstruye de `channel_7_reflectance / channel_2_reflectance`.

Coherencia física de la tabla (no prueba la definición, sólo que no está invertida): las partículas de ceniza
fina reflejan relativamente más a 3,9 µm que las gotas grandes y el hielo, y la ceniza es más oscura en el visible;
ambas cosas suben ρ(3,9)/ρ(0,65). La masa de ceniza está en `NRAT` alto y la de nube en bajo en los 6 bins de εtot y
los 2 de ángulo.

## 6. εtot × ρ(0,65)

Es la tabla menos decisiva y la menos limpia: en tierra la razón ceniza/nube va de 0,004 a 497 sin un patrón
monótono simple (por ejemplo, con εtot 0,9 a 1,0 y ángulo menor de 90°, de 242 a 497 entre 50 y 70 % de
reflectancia y casi cero sobre 90 %). Que entre o no es una de las variantes del criterio.

## 7. Tabla de objeto de día (resumen)

La tabla de objeto (`..._142742.hdf`) también trae versiones `_DAY_OBJ`: εtot con β(12/11) y `NRAT`
(`EMISS14_BETASW1_TOT_NRAT_PDF_DAY_OBJ`), con BTD y `NRAT`, con ρ(0,65) y con su desviación estándar
(`EMISS14_REF2_SDEV_PDF_DAY_OBJ`), y las equivalentes de las IR. Misma estructura que las de noche que reprodujo
H16. **No se valida en esta etapa:** el criterio de H18 es de píxel; el objeto de día queda para después, y sólo si
el píxel de día valida (H16 usa las mismas entradas por píxel).

## 8. Veredicto de la lectura

**Lectura completa en forma y ejes; la definición de `NRAT` y la regla de qué tablas entran quedan como SUPUESTO**
hasta compararlas contra la probabilidad que publica VOLCAT en un caso de día (criterio
`criterio_etapa1_validacion_dia_2026-11-22.md`, commit f966a08).
