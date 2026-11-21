# H15 (camino C3): las tablas reales de VOLCAT sobre la huella de Chillán. Informe, 21-11-2026

**Veredictos.** Etapa 1 (lectura de las tablas): **suficiente**, cordura cumple. Etapa 2 (validación contra VOLCAT
en Mauna Loa): **no aprobada**; ni con las entradas de VOLCAT (nivel A) ni con nuestro ε y β (nivel B) se llega a la
tolerancia fijada. Etapa 3 (Chillán): **no se ejecutó**, como manda el criterio y el encargo. H15 queda sin probar.

Criterios subidos antes de cada primer número: etapa 1 `criterio_etapa1_lectura_2026-11-21.md` (commit 287e3cb),
etapa 2 `criterio_etapa2_validacion_2026-11-21.md` (commit a0d29ea). Lectura: `LECTURA_LUT.md`. Plan:
`docs/own_volcat/PLAN_2026-11-21_LUT_VOLCAT.md`, C3.

## 1. Para geólogo

**Qué se quería saber.** VOLCAT publica plumas chicas de Nevados de Chillán que nuestras quince pruebas no ven. Desde
el 20-11 tenemos las tablas con que VOLCAT decide si un píxel es ceniza (dos "álbumes de referencia", uno de píxeles
de ceniza y otro de nube, entrenados con MODIS). La idea de C3 era aplicar esas tablas a la huella de Chillán y ver
si dan la probabilidad alta que VOLCAT necesita para publicar. Antes había que comprobar que sabemos usarlas, con un
caso donde VOLCAT sí publica su probabilidad por píxel: la erupción de Mauna Loa del 28-11-2022, de noche.

**Lo que salió bien.** Las tablas se leen completas: bordes de cada eje, prior de 0,1 % y las dos densidades de cada
clasificador. Y la regla de combinación más simple (multiplicar las razones ceniza/nube de cada tabla, Bayes
ingenuo) **reproduce al decimal lo que calcula VOLCAT en los píxeles de nube espesa** (εtot ≥ 0,5), si se le dan los
mismos ε y β que usó VOLCAT. Es decir: las tablas son las que VOLCAT usa y las sabemos leer, al menos en ese régimen.

**Lo que no.** Dos cosas impiden llevar esto a Chillán:

1. **Con nubes tenues VOLCAT hace algo que las tablas no dicen.** Bajo εtot 0,5 nuestra probabilidad se aparta de la
   de VOLCAT, y con εtot bajo 0,2 no coincide en ningún píxel. La diferencia cambia de forma suave con εtot (no es un
   umbral), así que no es un error de eje: es una regla adicional del código (candidatas en los atributos de la
   tabla: β reemplazado por una relación con la BTD cuando la nube es tenue, o un peso por incertidumbre de ε).
   **Las plumas de Chillán viven justo ahí**: en H11 la huella tenía εtot mediana 0,16. Es el tramo donde la
   lectura está menos validada.
2. **Nuestro ε no es el de VOLCAT, ni siquiera con su cielo despejado.** Calculando εtot con el cielo despejado que
   publica VOLCAT (`geocatRTM`) y una nube negra en la tropopausa, nuestro ε sale 0,05 más alto en la mediana, y la
   probabilidad cae lejos (κ 0,25). Despejando al revés, la "nube negra" que hace calzar el εtot de VOLCAT queda 25 K
   más fría que la tropopausa del GFS, y en 8 % de los píxeles no tiene solución física. Lo más probable: VOLCAT no
   usa el cielo despejado de `geocatRTM` tal cual, sino uno corregido por el sesgo local de 12 píxeles que activa su
   configuración, y ese campo viene vacío en el paquete (C2b ya lo había visto: un cielo despejado efectivo ~3 K más
   frío).

**Qué significa para la pregunta de fondo.** No sabemos todavía si las tablas reales darían probabilidad alta en la
huella de Chillán: medirlo con una lectura que falla justo en εtot bajo, y con un ε que no es el de VOLCAT, no
significaría nada en ninguna dirección. Lo que sí queda: (a) la parte "tablas" de VOLCAT está identificada y
reproducida en nube espesa; (b) lo que falta para Chillán son dos piezas concretas y preguntables (la regla de nube
tenue y el cielo despejado corregido), no "lo que VOLCAT no publica" en general.

## 2. Etapa 1: lectura (resumen; detalle en `LECTURA_LUT.md`)

- Prior 0,001 (`PIXEL_ASH_PROB_CLIMO`), densidades conjuntas que suman 1 con εtot incluido, piso ~1e-9, bordes de
  β, εp(3,9) y `NRAT` en atributos con la convención `HISTOGRAM` de IDL, εtot en 6 bins (0,01 · 0,03 · 0,10 · 0,20 ·
  0,50 · 0,90 · 1,00), BT11 despejado en 5 bins (160 · 255 · 260 · 265 · 270 · 400 K). LEÍDO.
- `NRAT` = razón de reflectancia 3,9/0,65 µm (INFERIDO), sólo de día.
- Con ABI en sólo IR entran 6 tablas sin 8,5 µm según el `.config` de 2025.
- Cordura: razón ceniza/nube de 25 a 2.140 en estados típicos de ceniza y de 0,0006 a 0,11 con β cerca de 1; sin
  ejes invertidos. Desviación declarada: con β ≥ 1,05 las dos densidades están en el piso (fuera del dominio
  entrenado).
- Corrección posterior: la tabla de β opaco usa el eje de 42 bins del β total, no el de 33.

## 3. Etapa 2: validación contra VOLCAT en Mauna Loa

**Datos.** `D:\goes_cache\volcat_test_mauna_loa\` (GOES-17, CONUS, 28-11-2022, 10 cuadros de 09:16 a 10:01 UTC, todo
de noche, 301 × 500 píxeles; VOLCAT v3.9.16). Verdad: `ash_probability_IR` de `geocatL2` (~100 mil píxeles por
cuadro). 98,7 % de los píxeles son mar (máscara: emisividad de superficie de C14 constante, que es como VOLCAT trata
el mar; `pixel_surface_type` vino en 0 en todo el dominio, desviación del criterio que la usaba).

**Regla del criterio** (cuadros 6 a 10, variante elegida en 1 a 5): reproduce si ≥ 90 % de píxeles con |ΔP| ≤ 0,05,
κ ≥ 0,90 a umbral 0,5 y ≥ 90 % de los píxeles con P_VOLCAT ≥ 0,5 recuperados. La etapa se aprueba si reproducen el
nivel A (ε y β de VOLCAT) y el nivel B (ε y β nuestros con su cielo despejado).

**Variante elegida en los cuadros 1 a 5:** S2 (las 8 tablas IR, con las dos de 8,5 µm), β fuera de eje recortado,
densidades conjuntas (93,5 % de píxeles dentro de 0,05). Las 27 variantes en `resultados/etapa2_variantes.csv`: con
las tablas IR (S1, S2) las condicionales por εtot (C1, C0) quedan en 73,6 a 78,8 %; las de noche con 3,9 µm (S3)
dan probabilidad casi nula en todo el dominio (de 2 a 5.266 píxeles ≥ 0,5, contra 30.628 de VOLCAT) y quedan en 65,9
a 88,4 %.

| Cuadros 6 a 10 (502.234 píxeles, 27.075 con P_VOLCAT ≥ 0,5) | Nivel A | Nivel B |
|---|---|---|
| Píxeles con \|ΔP\| ≤ 0,05 (pide ≥ 90 %) | 93,9 % | 87,2 % |
| κ a 0,5 (pide ≥ 0,90) | 0,795 | 0,245 |
| P_VOLCAT ≥ 0,5 recuperados (pide ≥ 90 %) | 75,3 % | 21,5 % |
| Diferencia absoluta mediana / p95 | 6e-10 / 0,090 | 1e-8 / 0,60 |
| Correlación de rangos | 0,957 | 0,788 |
| **Reproduce** | **no** | **no** |

Nivel B menos VOLCAT (cuadros 6 a 10): εtot +0,048 en la mediana (p5 +0,012, p95 +0,078; sólo 2,9 % dentro de
0,01); β(12/11) total −0,012 (p5 −0,63); β(7,3/11) −0,005. Salida cruda: `resultados/etapa2_validacion.json`.

### Por qué no reproduce (diagnóstico posterior, sólo cuadros 1 a 5, no decide)

Scripts `scripts/etapa2_diag*.py`, salida en `resultados/etapa2_diag*.txt`.

1. **La diferencia de log-odds cae en valores discretos** (−3,37, −2,86, −3,81...): un clasificador entra distinto.
   Probando todas las combinaciones de las 8 tablas, la que reproduce exacto (|Δ logit| < 0,001) más píxeles no
   saturados es **la de 7 tablas, sin la de BTD**: 79 % exacto contra 18 % con ella. En los píxeles con BTD < 0, sin
   esa tabla sale exacto el 95,3 %; con ella, sea cual sea el eje probado (4 ejes, compuerta de BTD en −5 a 0 K), no
   más del 87,7 %. **VOLCAT v3.9.16 no usa la
   tabla εtot × BTD en su probabilidad IR** en este caso. Las dos tablas de β(8,5/11) sí entran (el `.config` de 2025
   las apagaría; este caso es una versión que no trae `.config`).
2. **Lo que sigue sin calzar depende de εtot.** Con las 7 tablas, los píxeles no exactos son el 100 % con εtot < 0,2,
   el 27 % entre 0,2 y 0,5 y el 1 % sobre 0,5. Entre 0,2 y 0,5, con todos los β válidos, la fracción no exacta baja
   suave: 93 % en 0,24 a 0,26, 66 % en 0,38 a 0,40, 11 % en 0,42 a 0,44, 0 % sobre 0,48. No es un borde de bin ni
   un β inválido: es una regla continua en ε que las tablas no describen.
3. **El ε de VOLCAT no sale de `geocatRTM` y una nube negra en la tropopausa.** Despejando la nube negra de su εtot
   (εtot entre 0,3 y 0,9): mediana 174,9 K contra 198,9 K de la tropopausa del GFS (diferencia p5/p50/p95 = −52 /
   −25 / −12 K), y 39.243 de 474.178 píxeles sin solución (radiancia negativa). Con dos incógnitas (nube negra y
   cielo despejado efectivo) no se puede separar cuál difiere; lo compatible con todo lo visto (C2b y la
   configuración) es un cielo despejado corregido por el sesgo local de 12 px, que el paquete no trae
   (`Bt14_Bias_Env_Per75` vacío).

**Variante posterior sin la tabla de BTD, en los cuadros 6 a 10** (`resultados/etapa2_posterior_sin_btd.json`; no
decide, la elección se hizo mirando los datos):

| Nivel A, tramo de εtot | Píxeles | P_VOLCAT ≥ 0,5 | \|ΔP\| ≤ 0,05 | κ | Recuperados |
|---|---|---|---|---|---|
| todo | 502.234 | 27.075 | 98,5 % | 0,928 | 99,9 % |
| < 0,2 | 29.674 | 494 | 96,9 % | 0,844 | 94,9 % |
| 0,2 a 0,5 | 147.709 | 5.150 | 95,6 % | 0,724 | 100 % |
| ≥ 0,5 | 324.851 | 21.431 | 100 % | 0,999 | 100 % |

Con esa variante el nivel A pasaría la regla en conjunto, pero no en los tramos de εtot de una pluma tenue (κ 0,84 y
0,72: sobra probabilidad alta donde VOLCAT da baja). El nivel B, con la misma variante, sigue en κ 0,27. Figura del
cuadro 09:41: `resultados/etapa2_mapa_094100.png`.

## 4. Etapa 3: no ejecutada

El criterio de la etapa 3 no se escribió: el encargo y el criterio de la etapa 2 piden detenerse si la lectura no se
valida. Tampoco se bajó el modelo de elevación para la corrección de cota (no hacía falta sin etapa 3). Lo que la
etapa 3 necesitaría, en orden:

1. **La regla de nube tenue** (εtot < 0,5): cómo trata VOLCAT β cuando la nube es delgada. Pistas leídas en la tabla:
   `BETA1112_FROM_BTD_BIAS_*` (límites de εtot 0,05 en tierra y 0,02 en agua, entrenamiento 0,05 a 0,10),
   coeficientes `COEFF_BETA1112_TOT_FCT1` = (0,890; −0,205) con rango de sesgo de BTD 0,5 a 2 K, y
   `EMISS_UNCERTAINTY_*`. Probarlas sin el código es adivinar con 9 parámetros.
2. **El cielo despejado que entra a ε**, con el sesgo local de 12 px. Sin él, nuestro ε no es el de VOLCAT aun con
   su mismo modelo radiativo.
3. Recién entonces, Chillán, con `event_idx` como huella y control pareado por BT11.

Ambas piezas son preguntas concretas para el correo a Pavolonis (C4), mejores que las de la versión 4.

## 5. Qué cambia

- **Para el plan:** C3 queda detenido en la etapa 2, con la causa localizada. No se recomienda seguir adivinando la
  regla de nube tenue: el único caso de validación es de noche, sobre mar y de otra versión de VOLCAT.
- **Para el correo a Pavolonis (C4), tres preguntas nuevas:** (1) cómo se calcula el cielo despejado que entra a
  εtot (¿con el sesgo local de 12 px?, ¿y la nube negra de referencia?); (2) qué hace VOLCAT con β cuando εtot es
  bajo (las relaciones `FCT1` de la tabla); (3) si la tabla εtot × BTD se usa en la versión operativa de GOES-19
  (en v3.9.16 no entra) y si las de β(8,5/11) se apagan, como dice el `.config`.
- **Para H14:** compatible. La parte de VOLCAT que reproducimos (nube espesa) no es la que decide en Chillán; la que
  decide (nube tenue) depende de reglas fuera de las tablas.
- **Para el dashboard:** nada.

## 6. Archivos

- Scripts (`scripts/`): `lut_estructura.py`, `lut_exportar.py`, `lut_cordura.py` (etapa 1, los dos primeros con
  `venv_hdf4`); `ml_extraer.py` (HDF4 a npz, `venv_hdf4`); `lut_volcat.py` (motor de probabilidad);
  `etapa2_validar.py` (decide); `etapa2_diagnostico.py`, `etapa2_diag_subconjuntos.py`, `etapa2_diag_btd.py`,
  `etapa2_diag_resto.py`, `etapa2_diag_nube_negra.py`, `etapa2_posterior.py` (posteriores).
- Salida cruda (`resultados/`): `lut_pixel_estructura.txt`, `lut_objeto_estructura.txt`, `lut_cordura.txt`,
  `etapa2_validacion.json`, `etapa2_variantes.csv`, `etapa2_diagnostico.txt`, `etapa2_diag_subconjuntos.txt`,
  `etapa2_diag_btd.txt`, `etapa2_diag_resto.txt`, `etapa2_diag_nube_negra.txt`, `etapa2_posterior_sin_btd.json`,
  `etapa2_mapa_094100.png`.
- Fuera del repo: `D:\goes_cache\lut_h15\lut_pixel.npz` (densidades exportadas), `D:\goes_cache\lut_h15\ml\`
  (entradas y verdad de Mauna Loa en npz).

## Reproducir

```bash
D:\goes_notas\busqueda_2026-11-20\venv_hdf4\Scripts\python.exe -I docs/own_volcat/lut_h15/scripts/lut_exportar.py
```

```bash
D:\goes_notas\busqueda_2026-11-20\venv_hdf4\Scripts\python.exe -I docs/own_volcat/lut_h15/scripts/ml_extraer.py D:\goes_cache\volcat_test_mauna_loa\ext\mauna-loa_g17-conus_nov2022_r20260709-volcat-code-ancil D:\goes_cache\lut_h15\ml
```

```bash
python -I docs/own_volcat/lut_h15/scripts/etapa2_validar.py
```
