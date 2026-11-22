# H18 (S16b): el modo DÍA de VOLCAT. Informe, 22-11-2026

**Veredicto pre-registrado: NO VALIDA.** Nuestra lectura de las tablas de día de VOLCAT no reproduce la
probabilidad de ceniza que VOLCAT publica en un caso de día sobre tierra (Fuego, GOES-16, 03-06-2018). Como manda
el criterio, **no se aplicaron a Chillán**. La lectura de día queda **sin validar**.

Criterio: `criterio_etapa1_validacion_dia_2026-11-22.md`, commit f966a08 (antes de abrir el caso) y su adenda, commit
b7f8f7a (antes de calcular ninguna probabilidad nuestra). Lectura de las tablas: `LECTURA_DIA.md` (ecaf960).

## 1. Para geólogo

**Qué se quería saber.** Los 60 cuadros en que VOLCAT publicó plumas de Nevados de Chillán son de día. En S15 sólo
probamos sus tablas infrarrojas, validadas de noche sobre el mar (Mauna Loa). De día VOLCAT agrega tablas con la luz
solar reflejada a 0,65 y 3,9 µm, y en el papel esas tablas separan muy bien la ceniza de la nube. Antes de mirar
Chillán con ellas había que comprobar que las sabemos usar, contra un caso de día en que VOLCAT publique su propia
probabilidad por píxel.

**El caso.** En el servidor abierto de SSEC el único caso de prueba de día con el sensor ABI (mismo instrumento y
misma tabla que GOES-19) es la erupción de Fuego, Guatemala, del 3 de junio de 2018: 40 cuadros, 26 con píxeles de
día evaluables, casi todo sobre tierra, con la probabilidad por píxel que calculó VOLCAT. Los registros del paquete
confirman que VOLCAT leyó exactamente nuestra tabla.

**Lo que salió.**

1. **Las tablas infrarrojas quedan validadas también de día y sobre tierra.** Nuestra lectura reproduce la
   probabilidad IR de VOLCAT en el 100 % de los píxeles (κ 1,000). Hasta hoy sólo estaba validada de noche y sobre
   el mar.
2. **La probabilidad alta que VOLCAT publica en la pluma de Fuego no sale de ninguna tabla de píxel.** En la
   columna de Fuego VOLCAT publica P de 0,6 a 1,0 en 6.621 píxeles; 6.548 de ellos, entre 18:01 y 22:16 UTC, son
   nube espesa (εtot mediano de 0,90 a 0,97 por cuadro). Su propia
   probabilidad IR ahí es casi cero y nuestras tablas de día casi no aportan, porque esos píxeles no tienen la firma
   de ceniza: la diferencia 11 − 12 µm es positiva (+1,2 a +2,4 K) y la razón de reflectancias es la de una nube
   (`NRAT_LRC` de 0,04 a 0,11). En casi todos esos píxeles (99,8 %) VOLCAT los tiene agrupados en un objeto de
   ceniza, y en el 77 % la P publicada es igual a otra variable suya, `ash_probability_subset`. Lo más probable: a
   esa columna convectiva VOLCAT le asigna la probabilidad por otra vía (objeto, columna convectiva o pluma), no por
   el producto de tablas de píxel.
3. **Donde la P sí sale de las tablas, la lectura de día acierta a medias, y cuando acierta lo hace exacto.** En
   los píxeles de P baja (bajo 0,5 y no saturada), una combinación de tablas de día reproduce el log-odds de VOLCAT
   al octavo decimal en el 53 al 65 % de los píxeles. En el resto falla por saltos grandes, todos en nube espesa,
   y ningún cambio de una sola pieza lo arregla. Falta una regla, igual que pasó de noche.

**Qué significa para Chillán.** La pregunta de S16 era si el hueco entre VOLCAT y nosotros estaba en las tablas
de día. Dos resultados independientes de hoy apuntan a que no:

- aquí, en Fuego, la probabilidad alta que VOLCAT publica en una pluma real no sale de las tablas de píxel, ni de
  día ni IR;
- la sesión hermana S16 (4a) leyó la imagen de probabilidad del sitio de VOLCAT para Chillán a la hora de los 60
  cuadros: en la huella, la probabilidad es baja (≥ 20 % en 0 de 30 cuadros de día pleno; sólo al atardecer aparecen
  píxeles altos).

Las dos cosas encajan con la sospecha de S15: VOLCAT publica Chillán por una vía de objeto o pluma
(`ASHPLUMEPUFF`, `VCB`), no por la probabilidad de píxel. Esa vía no está en las tablas públicas.

## 2. Comprobaciones previas (cumplen las tres)

Fuente: `resultados/fu_comprobaciones.json`.

| Comprobación | Pide | Resultado |
|---|---|---|
| 1. Que sea de día | ≥ 10.000 píxeles de día con P y ≥ 100 con P ≥ 0,5 | 36.787 y 6.621 (26 cuadros, 17:16 a 23:31 UTC) |
| 2. Que el día se use | ≥ 1 % de los píxeles de día con \|P − P_IR\| > 0,05 | 18,5 % |
| 3. Que la tabla sea la nuestra | `..._Jan11_2017_142740` | sí: el log de GEOCAT 3.4.5 dice `Reading ash LUT's from: .../GOESR_ASH_pixel_probability_LUT_Jan11_2017_142740.hdf` |
| Rango de entradas | ρ(0,65) en 0 a 120 %; `NRAT_LRC` finito en ≥ 50 % | 99,96 % y 99,86 % |

Superficie de los píxeles de día: 192 de agua (`pixel_surface_type` = 0), el resto tierra.

## 3. Validación (decide)

Fuente: `resultados/fu_validacion.json` y `resultados/fu_variantes_eleccion.csv`; script `scripts/fu_validar.py`
(motor `scripts/dia_motor.py`).

**Elección (13 primeros cuadros, 17:16 a 19:46 UTC).** Las 96 variantes empatan en la fracción dentro de 0,05
(0,607) con κ 0 y ningún píxel alto recuperado: ninguna combinación de tablas de día, con o sin las IR, da P ≥ 0,5
donde VOLCAT sí. Por la regla de desempate quedó la más simple (`c+ n1 d0 k0 v0 i0`: sólo las 4 tablas β × `NRAT`
y la de β(12/11) × β(7,3/11) de día).

**Regla (13 cuadros siguientes, 20:01 a 23:31 UTC), píxeles de día de tierra:**

| | Pide | Resultado |
|---|---|---|
| Píxeles | | 25.432 (2.260 con P_VOLCAT ≥ 0,5) |
| 1. \|ΔP\| ≤ 0,05 | ≥ 90 % | 91,0 % (lo llenan los píxeles con P ≈ 0 en los dos) |
| 2. κ a 0,5 | ≥ 0,90 | 0,002 |
| 3. P_VOLCAT ≥ 0,5 recuperados (control positivo) | ≥ 90 % | 0,09 % (2 de 2.260) |
| 4. Tramo εtot < 0,5 | ≥ 30 píxeles con P_VOLCAT ≥ 0,5 | 28 píxeles, 9 altos: SIN DATO |
| 5. Placebo (NRAT y ρ(0,65) permutados) empeora | 5 puntos o 0,10 de κ | no empeora (91,0 %, κ 0,010) |
| Control negativo: P_VOLCAT < 0,01, nuestra ≥ 0,5 | ≈ 0 | 0 de 23.118 |

**NO VALIDA**: fallan 2, 3 y 5. El placebo que no empeora dice que, medidas así, las tablas de día no deciden nada
en este caso: la P alta de VOLCAT está en otra parte. El tramo de Chillán (εtot < 0,5) casi no existe en Fuego, que
es una columna espesa: aunque hubiera validado, no habría alcanzado para Chillán.

**Validación de las tablas IR (positivo, primera mitad):** nuestras 7 tablas IR con las reglas R1 a R3 contra la
`ash_probability_IR` de VOLCAT: 11.162 píxeles, 100 % dentro de 0,05, κ 1,000, diferencia mediana 1e-18
(`referencia_primera_mitad` en `fu_validacion.json`). Es la primera validación de la lectura IR de día y sobre
tierra.

## 4. Diagnóstico posterior (no decide; se hizo después del veredicto)

1. **De dónde sale la P alta** (`resultados/fu_diag_posterior.json`). En los píxeles de día con P ≥ 0,5 de los
   cuadros de 18:01 a 22:16 UTC (6.548 de 6.621; los 73 de después tienen εtot mediano 0,27 a 0,57): εtot
   mediano de 0,90 a 0,97, BTD 11 − 12 de +1,2 a +2,4 K, `NRAT_LRC` de 0,04 a 0,11 (como los píxeles de P baja,
   0,04 a 0,09). Aporte mediano de nuestras tablas en esos píxeles, en décadas de razón ceniza/nube: IR −6,6; β ×
   `NRAT` −0,02; β × `NRAT_LRC` +0,16; ρ(0,65) +0,47. Hacen falta +3,0 para llegar a 0,5. Distribución de P de día:
   6.340 píxeles ≥ 0,999, 281 entre 0,5 y 0,999.
2. **No es la P IR ni una tabla** (`resultados/fu_diag_igualdad.json`). Con P ≥ 0,5: P igual a P_IR en 0 %, dentro
   de un objeto de ceniza (`Ash_Group_Id_2d` > 0) en 99,8 %, igual a `ash_probability_subset` en 76,8 %.
3. **Donde manda la tabla, la lectura de día es exacta a medias** (`resultados/fu_diag_logit.json`). Píxeles de
   tierra con P entre 1e-12 y 0,5. La mejor variante en log-odds (`NRAT` sin LRC + β(7,3/11) + β(8,5/11) + ρ(0,65) de
   día, sin BTD ni tablas IR) es exacta (|Δ logit| < 0,001, mediana 3e-8) en el 64,8 % de 2.614 píxeles de la
   primera mitad y en el 53,3 % de 8.001 de la segunda. La P IR de VOLCAT, en esos mismos píxeles, no coincide en
   ninguno (mediana de 10 a 13 log-odds de diferencia según la mitad): **de día VOLCAT sí cambia de tablas**, y las que usa son de día.
4. **El resto no se arregla con una pieza** (`resultados/fu_diag_resto.json`, todos los cuadros: 10.615 píxeles,
   5.962 exactos). Los 4.653 no exactos tienen todos εtot ≥ 0,5. VOLCAT les da más log-odds que nosotros (saltos
   más frecuentes +66,8, +9,9, +4,9, +25,0). Quitar cualquier tabla, cambiar `NRAT` por `NRAT_LRC`, apagar R1, R2 o
   R3, o agregar la BTD no arregla ninguno. No coincide con estar en un objeto (1.659 no exactos dentro de un
   objeto, 2.994 fuera).

## 5. Las dos preguntas del instrumento, contestadas

1. *¿La prueba habría fallado con la lectura rota?* Sí, en principio, y por eso la comprobación 2 se hizo antes. Pero
   el placebo mostró algo que la comprobación no vio: la diferencia entre P y P_IR está casi toda en píxeles cuya P
   no sale de tablas. La métrica |ΔP| ≤ 0,05 se satura con P ≈ 0 (91 % en el real y en el placebo). Por eso el
   veredicto es NO VALIDA y no "valida en lo que se pudo medir".
2. *¿Un instrumento muerto se vería distinto?* Sí: la verdad no está vacía ni es constante (6.621 píxeles altos), y
   el control negativo midió 0 de 23.118.

## 6. Qué cambia

- **Para Chillán:** no se aplica nada (lectura sin validar). La explicación "el hueco está en las tablas de día"
  queda debilitada por dos lados: VOLCAT mismo publica P de píxel baja en la huella de día (S16, 4a), y en Fuego su P
  alta de pluma no sale de tablas. La pieza que falta es la vía de objeto o pluma.
- **Para el correo a Pavolonis, dos preguntas concretas nuevas:** (1) en una columna espesa sin firma de ceniza
  (Fuego 2018, εtot ≈ 0,95, BTD > 0), ¿qué asigna la `ash_probability` ≈ 1 y qué es `ash_probability_subset`?;
  (2) de día, con εtot ≥ 0,5, ¿qué regla agrega log-odds a las tablas de píxel (saltos de +5 a +67)?
- **Para S15:** las tablas IR quedan validadas también de día y sobre tierra. La "probabilidad IR de píxel" que
  midió la etapa 3 en Chillán es entonces la de VOLCAT, salvo el cielo despejado de 11 µm.
- **Para el dashboard:** nada (sin cambio de lógica; sin ficha SDA).

## 7. Archivos

- Criterio y lectura: `criterio_etapa1_validacion_dia_2026-11-22.md`, `LECTURA_DIA.md`.
- Scripts (`scripts/`): `dia_lectura.py` (marginales de las tablas), `fu_extraer.py` (HDF4 a npz, con `venv_hdf4`),
  `fu_comprobaciones.py`, `dia_motor.py`, `fu_validar.py` (decide), `fu_diag_posterior.py`,
  `fu_diag_igualdad.py`, `fu_diag_logit.py`, `fu_diag_resto.py` (posteriores).
- Resultados (`resultados/`): `dia_lectura.txt`, `fu_comprobaciones.json`, `fu_variantes_eleccion.csv`,
  `fu_validacion.json`, `fu_diag_posterior.json`, `fu_diag_igualdad.json`, `fu_diag_logit.json`,
  `fu_diag_resto.json`.
- Fuera del repo (datos de SSEC, no se suben): `D:\goes_notas\s16\modo_dia\fuego\` (salidas de referencia del
  paquete, 15 GB, MD5 del paquete `a8eb502269865a61f81f11c794cb83af`, igual al publicado),
  `D:\goes_notas\s16\modo_dia\npz\` (40 cuadros extraídos), `D:\goes_notas\s16\modo_dia\estructura_fuego.txt`.
  Fuente: `https://bin.ssec.wisc.edu/pub/volcat/test_cases/fuego_goes16-fulldisk_june2018_r20260709-volcat-code-ancil.tar.gz`.

## Reproducir

```bash
D:\goes_notas\busqueda_2026-11-20\venv_hdf4\Scripts\python.exe -I docs/own_volcat/h18_modo_dia/scripts/fu_extraer.py <reference_data> D:\goes_notas\s16\modo_dia\npz
```

```bash
python -I docs/own_volcat/h18_modo_dia/scripts/fu_comprobaciones.py
```

```bash
python -I docs/own_volcat/h18_modo_dia/scripts/fu_validar.py
```
