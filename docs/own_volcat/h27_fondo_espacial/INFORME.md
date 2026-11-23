# H27 (S19c): ¿los pulsos de tarde que VOLCAT marcó dejan firma IR, medidos contra cumbres sin actividad? Informe, 23-11-2026

**Veredicto con la regla escrita antes de medir: INVÁLIDO (el nulo de cumbres no representa a Chillán).** La
prueba de transferencia de la mañana (T1) falla en E7: la dispersión del estadístico en Chillán es 1,54 veces la de
las cumbres, y el criterio aceptaba hasta 1,5. Las falsas alarmas (3,0 %), la transferencia de tarde (T2, 2 de 17)
y el control grande (100 %) pasan. Aun si T1 hubiera pasado, el veredicto habría sido NO CONCLUYENTE (sólo 2
episodios decidibles, 0 SEÑAL): la conclusión no depende del borde de 1,5.

Criterio: `criterio_2026-11-23.md`, commit `a82c540` (con el conteo de fondo hecho antes de diseñar). Script:
commit `7d89ad6`. Por qué se hizo: H24 (`../h24_pulsos_reav/INFORME.md` §6) dejó sin fondo la tarde.

## 1. Para geólogo

**La pregunta.** H24 midió los pulsos que el OVDAS vio en Chillán contra la historia del propio volcán en días
despejados sin actividad, a la misma hora. De mañana funcionó; de tarde no, porque en primavera casi no hay tardes
despejadas sin actividad en Chillán. Justo de tarde están los pulsos que VOLCAT sí marcó: E10 (28-10 17:38 UTC,
2.200 m), E11 (28-10 20:32, 2.440 m), E12 (28-10 21:49, 2.020 m) y E13 (10-11 21:54 a 22:36, 2.400 m). Esta vez el
fondo se tomó de Antuco y Longaví, dos cumbres sin actividad de la misma ventana, que pueden aportar fondo todos los
días porque no hay nada que excluirles.

**Cuánto fondo había (contado antes de diseñar).** De tarde, Chillán tiene 3 a 5 días despejados sin actividad a la
hora exacta de cada episodio (4 a 7 con ±1 h). Las cumbres juntas: 16 a 25 sitio-día con dato. El cuello de botella
era Chillán, no el cielo del episodio (los 7 cuadros de cada pulso de tarde estaban despejados).

**El problema de fondo.** Cada cumbre tiene otro terreno: otra nieve, otras laderas al sol de la tarde, otro valle.
La línea base del propio píxel quita la parte fija del terreno, pero lo que importa es si el estadístico, sin pluma,
**se mueve lo mismo** en Antuco y Longaví que en Chillán. Eso se midió de mañana, donde Chillán tiene 10 a 13 días
propios: el centro coincide (corrimiento 0,02 a 0,47 MAD), pero **Chillán es más ruidoso**: 1,49 y 1,54 veces la
dispersión de las cumbres en E1 y E7. Con un nulo más angosto que el de Chillán, cualquier corrimiento de Chillán se
lee como más extremo de lo que es: el error va hacia **falsas detecciones**, no hacia perderlas. La regla escrita
antes ponía el tope en 1,5 y E7 lo pasa.

**Lo que salió en los pulsos que VOLCAT marcó (lectura, la prueba no decide):**

1. **E11 (2.440 m) y E13 (2.400 m): sin señal.** z −1,30 y −1,06 (la regla pide −2). Una capa de ε 0,15 sobre el
   sector se habría visto en 100 % de los sitio-día del nulo, y una pluma angosta (franja de ±3 km) de ε 0,30 en 86
   y 92 %. Con el nulo propio de Chillán (2 y 4 días, muy pocos) la franja se vería en 50 y 100 %.
2. **E12 (2.020 m): z −2,44, el único bajo −2, pero SIN PODER** para una pluma angosta (77 %, pide 80 %). Es además
   el episodio en que los 3 días propios de Chillán tienen el doble de dispersión que las cumbres (razón 1,99): justo
   el caso en que el nulo de cumbres exagera. El placebo contra el viento no detecta (z +4,9), ni Antuco (−0,62) ni
   Longaví (+1,81) en el mismo cuadro.
3. **E10 (2.200 m): z −1,86, SIN PODER** para la franja (63 %).
4. **El 10-11, Antuco "detecta" en el mismo cuadro de E13** (z −4,04, con 4 cuadros): una cumbre sin actividad da
   una anomalía mayor que cualquier cosa que haya dado Chillán. Es el mismo aviso de E8 en H24: el tiempo regional
   de la tarde mueve el estadístico tanto como una pluma.
5. **Los pulsos de la mañana (E1, E6, E7) no contradicen a H24:** z −0,60, −0,70 y −0,13, sin señal, aunque aquí
   quedan SIN PODER para la franja (46 a 72 %), porque el nulo de cumbres de mañana es más ancho.

**Qué significa para la pregunta de Nicolás** ("¿podemos detectar lo que vio VOLCAT?"):

- Tomar el fondo de otras cumbres no resuelve la tarde: Chillán sin pluma es más ruidoso que Antuco y Longaví, y la
  prueba lo detectó antes de que se pudiera leer un número como detección. Lo que sí se ve, como lectura: en los dos
  pulsos de tarde que VOLCAT marcó con más poder (E11, E13), el IR de Chillán no se aparta de lo que hacen las
  cumbres quietas; el único número bajo el umbral (E12) cae justo donde el método exagera.
- La puerta abierta sigue siendo la de H24 §7: repetir la prueba en verano con el fondo propio de Chillán, o un fondo
  que no dependa de otras cumbres.

## 2. Comprobaciones de instrumento y controles

| | Pide | Medido |
|---|---|---|
| Cubos (I1 a I3 de H23/H24, Planck igual en los tres) | asserts de `cargar()` | pasan (los mismos cubos de H24, sin copiar) |
| Pruebas numéricas del script | todas | H24 8 de 8 más H27 (z con mínimo 12, franja, línea base de ±1 h) |
| Las pruebas de H27 atrapan su rotura | mutación falla por aserción | 4 de 4 (sin exclusión de días, ventana ancha por arriba y por abajo, sin dejar el día afuera) |
| Control grande (ε 0,9 a 10 km) | ≥ 95 % | 100 % en los 9 episodios con nulo |
| Nulo no degenerado | MAD > 0,01 K | 0,043 a 0,095 K |
| Falsas alarmas (sitio-día de cumbres como falsos episodios, E9 a E14) | ≤ 10 % | 4 de 133 (3,0 %) |
| T1, transferencia de mañana | \|Δmediana\| ≤ 0,5 MAD y razón de MAD 0,67 a 1,5 en E1, E6 y E7 | E1 0,20 y 1,49; E6 0,47 y 0,81; **E7 0,02 y 1,54: falla** |
| T2, transferencia de tarde | ≤ 20 % (o < 2) de los días propios de Chillán detectan | 2 de 17 (11,8 %): pasa |

Las dos preguntas del instrumento (criterio §4): un D2 ciego habría dado SIN PODER (el poder de la capa dio 97 a 100
% en las cumbres y en Chillán, así que el detector no está ciego a una capa); un instrumento muerto habría dado nulo
degenerado o fallado el control grande. Ninguna de las dos pasó. Lo que falló es otra cosa, y estaba previsto: que la
cumbre de control no sea un buen sustituto de Chillán.

## 3. Resultados por episodio (`resultados/h27_episodios.csv`)

E = mediana de las diferencias de BTD del sector a favor del viento contra el viento cruzado (K). z contra el nulo de
cumbres. Poder: capa sobre todo el sector (ε 0,15) y franja angosta (ε 0,30), en las cumbres; entre paréntesis, la
franja ε 0,30 en los días propios de Chillán (n).

| Ep | H (m) | Hora UTC | Cuadros | Sitio-día nulo | E (K) | z | Poder capa 0,15 | Poder franja 0,30 (Chillán) | Placebo z | Antuco z | Longaví z | Clase |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| E10 | 2.200 | 17:38 | 7 | 16 | −0,18 | −1,86 | 1,00 | 0,63 (0,67, n 3) | −1,77 | 0,42 | 0,96 | SIN PODER |
| E11 | 2.440 | 20:32 | 7 | 22 | −0,13 | −1,30 | 1,00 | 0,86 (0,50, n 2) | 4,25 | −0,58 | 1,74 | SIN SEÑAL |
| E12 | 2.020 | 21:49 | 7 | 22 | −0,17 | **−2,44** | 1,00 | 0,77 (0,67, n 3) | 4,93 | −0,62 | 1,81 | SIN PODER |
| E13 | 2.400 | 21:54 | 7 | 25 | −0,04 | −1,06 | 1,00 | 0,92 (1,00, n 4) | 3,07 | **−4,04** | 0,77 | SIN SEÑAL |
| E9 | 1.320 | 15:34 | 7 | 27 | −0,19 | −1,58 | 1,00 | 0,52 (0,20, n 5) | 0,01 | 0,16 | 0,51 | SIN PODER (informa) |
| E14 | 400 | 20:03 | 0 | 21 | | | 1,00 | 0,71 | | −0,27 | 1,05 | SIN DATO (cielo) (informa) |
| E1 | 1.320 | 10:41 | 4 | 38 | −0,07 | −0,60 | 1,00 | 0,55 (0,20, n 10) | −1,39 | 0,29 | | SIN PODER (informa) |
| E6 | 2.000 | 09:26 | 6 | 46 | −0,04 | −0,70 | 1,00 | 0,46 (0,23, n 13) | −0,57 | | 0,63 | SIN PODER (informa) |
| E7 | 960 | 10:26 | 4 | 36 | 0,02 | −0,13 | 0,97 | 0,72 (0,73, n 11) | −0,31 | | −2,06 | SIN PODER (informa) |

Veredicto global (criterio §9): T1 falla, **INVÁLIDO**. Decidibles entre E10 y E13: 2 (E11, E13), SEÑAL 0.

Secundarias (`h27_episodios.csv`): pareo por BT11 y cota, z −2,04 (E10), −1,60 (E11), −1,94 (E12), −0,91 (E13);
nulo de una sola cumbre en E12, Antuco −1,45 y Longaví −3,79 (el nulo de Longaví es el más angosto); nulo propio de
Chillán, sólo calculable de mañana (≥ 6 días): z −0,27, −0,29 y −0,07 en E1, E6 y E7.

## 4. Lo que podría estar equivocado

- **El borde de T1.** E7 falla por 0,04 sobre 1,5. Lectura post hoc, no resultado: con T1 aprobado el veredicto
  sería NO CONCLUYENTE (2 decidibles), no "no se ven". Y la dirección del desajuste (Chillán más ruidoso) es la que
  fabrica detecciones, así que aflojar el borde no ayuda a la pregunta.
- **El poder medido en las cumbres sobreestima el de Chillán para plumas angostas:** en los días propios de Chillán
  la franja ε 0,30 se ve en 20 a 73 % de mañana y en 20 a 100 % de tarde (2 a 5 días), contra 46 a 92 % en las
  cumbres. Para una capa sobre todo el sector, el poder es pleno en los dos sitios.
- **E10, E11 y E12 son del mismo día (28-10):** no son tres pruebas independientes.
- **Dirección:** E11 a E13 usan la del GFS (H10); E10, la del REAV. Si la pluma fue hacia otro lado, el sector la
  pierde en parte (el placebo positivo de +3 a +5 en E11 a E13 dice que el lado contrario tenía la BTD más alta que lo
  normal respecto del viento cruzado, no que la pluma estuviera ahí).
- **β:** la capa inyectada tiene β 0,70, como en H24. Con β cerca de 1 la BTD no ve la ceniza aunque sea espesa.
- **Las cumbres de control son sólo dos:** la regla sobre el DEM no encontró una tercera cumbre dentro de la ventana.

## 5. Qué sigue (propuesta, no hecho)

1. **El fondo propio de Chillán en verano** (H24 §7.1), con el criterio de H24 sin cambios. Sigue siendo la única vía
   limpia: H27 muestra que el sustituto de cumbres no sirve para Chillán.
2. **Ventana de cubo más grande** para tener más cumbres de control y poder elegir las que pasen T1 (necesita bajar
   L1b; criterio propio y conteo antes).

## 6. Archivos

- `criterio_2026-11-23.md` (commit `a82c540`).
- `scripts\`: `h27_contar.py` y `h27_contar2.py` (conteo de fondo, antes del criterio), `h27_medir.py` (criterio;
  importa `..\..\h24_pulsos_reav\scripts\h24_medir.py` sin modificarlo).
- `resultados\`: `h27_conteo_fondo.json`, `h27_conteo_fondo_2.json`, `h27_episodios.csv`, `h27_resumen.json`,
  `h27_corrida.log`.
- Insumos de sólo lectura: `D:\goes_notas\s17\h23\` y `D:\goes_notas\s18\h24\`. No se bajó nada. Ningún archivo de
  SSEC. Nada toca `src/` ni el dashboard.

Reproducir, desde `docs\own_volcat\h27_fondo_espacial\scripts\` del repositorio:

```powershell
python -I h27_contar.py
```

```powershell
python -I h27_contar2.py
```

```powershell
python -I h27_medir.py
```
