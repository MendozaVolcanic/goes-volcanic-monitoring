# S31i: por qué la cumbre de Antuco dispara de día. Informe, 27-11-2026

Sesión S31i (worktree `s31i-antuco-dia-dbaaf8`, rama `claude/s31i-antuco-dia-dbaaf8`), lanzada por la coordinadora S31.
Criterio: `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\Goes\docs\own_volcat\s31i_antuco_dia\criterio_2026-11-27.md`,
commit `097b10d` (27-11 04:24 UTC), empujado antes de cruzar un solo disparo con cualquier covariable. Medida única:
commit `ed3e511` (27-11 13:53 UTC). Ningún día GOES posterior al 21-11 de cada año (todos antes del 24-11-2026), nada de
las confirmaciones, el detector sin tocar, nada de VIIRS.

## 1. En una frase

**La cumbre de Antuco no dispara de día por nubes ni por los controles lejanos: cuando dispara es un día común, y lo
que cambia de un año a otro es la nieve. En 2024 y 2026 la cumbre tiene más nieve que en 2025, el año de la base, y su
BTD de día queda corrida hacia abajo todo el día, más al mediodía; el umbral de 2025 se cruza entonces con cualquier
vaivén.** Por la regla escrita las tres candidatas quedan NO SE SOSTIENE; la lectura de la nieve es post hoc, sin
probar con criterio previo, pero las cinco parejas cumbre y año (Antuco, Longaví y Chillán) la siguen sin excepción.

## 2. El fenómeno, antes que los números

Una cumbre despejada al sol tiene BTD (11,2 menos 12,3 µm) positiva, y más grande mientras más caliente esté la
superficie respecto del aire de arriba, porque el vapor de agua absorbe más a 12 µm. La roca volcánica descubierta se
calienta mucho al mediodía; la nieve no pasa de 0 °C y refleja casi todo el sol. Por eso una cumbre más nevada tiene,
a la misma hora, menos contraste térmico y una BTD más baja que la misma cumbre a medio descubrir.

La zona del cráter compara cada píxel de la cumbre consigo mismo en oct-nov 2025. En Antuco y Longaví 2025 fue un año
de poca nieve (S29a lo vio con Sentinel-2 y Landsat; aquí GOES da lo mismo con 0,86 y 1,6 µm). En 2024 y 2026 las dos
cumbres tienen más nieve: su BTD de día queda bajo la de 2025 todo el día, y la regla, que pide quedar bajo el
percentil 4,75 de 2025 dos cuadros seguidos, lo consigue con las fluctuaciones de siempre. No hace falta ningún evento:
basta con que el piso esté más abajo. Chillán tiene la cumbre casi entera nevada todos los años (91 a 95 %), así que su
zona no se corre, y en 2024 dispara menos, no más.

## 3. Datos y comprobaciones

- Disparos: zona de Antuco de S27a (`s27a_medir.zona_de`, 9 píxeles de 2 km), percentil 4,75, base y umbral de 2025,
  nublado de costumbre de cada año. **Comprobación de código: reproduce exacto** los conteos de día publicados: 2026
  138 de 1.467 (S28a), 2024 176 de 2.273 y 2025 62 de 2.410 (S29b) (`resultados/s31i_resultado.json`, `comprobacion`).
- Luz reflejada: C03 (0,86 µm) y C05 (1,6 µm) a 1 km, GOES-16 en 2024 y GOES-19 en 2025 y 2026, una franja de Longaví a
  Antuco, cada 20 min de 12:00 a 22:40 UTC, 21-09 a 21-11 de cada año: 6.094 de 6.138 cuadros (44 sin archivo en NOAA),
  0,2 GB en `D:\goes_notas\s31\s31i\l1b\`: 2.014 cuadros en 2024, 2.039 en 2025 y 2.041 en 2026.
- **La primera corrida se cortó.** La bajada murió el 27-11 a las 04:51 UTC (un proceso hijo terminó de golpe, con 2.415
  cuadros bajados) y la medida, lanzada en paralelo, murió sin escribir una sola línea; después el computador se reinició
  a las 12:34 UTC. **Esa corrida no dio ninguna cifra.** Se reanudó a las 12:40 UTC (la bajada sigue desde lo que había)
  y la medida corrió una sola vez completa. Logs: `D:\goes_notas\s31\s31i\bajar_corrida1.log`, `medir_corrida1_vacio.log`.

## 4. Medidas del criterio (deciden)

| Medida | Resultado | Lectura |
|---|---|---|
| M1, 1,6 µm en los cuadros que disparan contra la misma hora de otros días, 2024 más 2026 | T1 +0,064 en 38 días; nulo por días mediana +0,036 (p5 a p95: 0,00 a +0,07); p_alto 0,11, p_bajo 0,89 (piso 0,0005) | Los cuadros que disparan no brillan más ni menos a 1,6 µm que los de un día cualquiera a esa hora. 2024: +0,082 (p_alto 0,07); 2026: +0,042 (p_alto 0,40) |
| M2, clase del día | 23 despejados, 10 nublados, 5 mezclados (de 38) | La mayoría de los días que disparan están despejados en la cumbre, pero eso es lo común: los cuadros evaluados de día tienen 6 a 12 % de subpíxeles nube en promedio |
| M3, cuánto de la caída ponen los controles | share 0,15 (IC 0,04 a 0,41) en 46 días; 2024 0,20, 2026 0,08 | La cumbre pone 85 % de la caída; los controles casi nada |
| M4 (lectura), nieve de la cumbre | fs 0,81 en 2024, 0,63 en 2025, 0,81 en 2026; Δfs +0,17 en los dos años | Más nieve que en la base los dos años con exceso. Dentro de cada año la tasa diaria no sigue a Δfs (Spearman +0,20, p 0,20 en 2024; −0,05 en 2026) |
| M4 (lectura), BT11 en los disparos | −0,9 K (2024) y −2,0 K (2026) bajo su base, pero no más que a la misma hora de otros días (p_bajo 0,69 y 0,38) | Cumbre más fría que en 2025 a esa hora, como todo el año |
| M4 (lectura), máscara ACM en la zona | 61 % y 50 % de la zona marcada nube en los disparos, casi lo mismo que en otros días (anomalía +0,06 y 0,00) | La máscara de NOAA marca la cumbre nevada como nube siempre (ya visto en S20b); no dice nada del disparo |

**Veredictos por la regla (§5):** (a) nube baja **NO SE SOSTIENE**; (b) contraste nieve-roca **NO SE SOSTIENE** como
mecanismo de cada disparo (M1 no llega); (c) término regional **NO SE SOSTIENE** (share 0,15 < 0,5).

Informativos del criterio §6: el ensayo en seco de 2025 en Antuco da T1 +0,12 con 6 días (p_alto 0,03; no decide); en
Longaví 2024, −0,002 (p 0,14 y 0,86), 13 de 14 días despejados; en Chillán 2024, +0,046 con 6 días.

Expectativa escrita antes: que fuera nube de convección de tarde. **No lo es**: sólo 10 de 38 días con disparo están
nublados en la cumbre, y de ésos el 10-11-2026 (17 cuadros, los cúmulos de la tarde que vio S29a) es el único fuerte.

## 5. Post hoc (no decide; escrito después de leer la medida)

`scripts/s31i_posthoc.py`, `resultados/s31i_posthoc.json`. Si los días que disparan son días comunes, lo que cambia
tiene que ser el año entero. Se miró la mediana diaria de S de día (12:00 a 23:50 UTC) por cumbre y año.

| Cumbre y año | Nieve fs (año menos 2025) | S de día, mediana (año menos 2025, K) | Tasa de día (veces 2025) | Días con S menor que 2025 (Mann-Whitney) |
|---|---|---|---|---|
| Antuco 2026 | +0,18 | −0,10 | 3,9 | p 0,006 |
| Antuco 2024 | +0,18 | −0,27 | 3,0 | p < 0,0001 |
| Longaví 2024 | +0,17 | −0,23 | 2,9 | p < 0,0001 |
| Longaví 2026 | +0,13 | −0,06 | 1,4 | p 0,18 |
| Chillán 2024 | +0,03 | 0,00 | 0,26 | p 0,12 |

- **Las cinco parejas van en el mismo orden**: más nieve que en 2025, S más bajo todo el año y más disparos; la cumbre
  sin cambio de nieve (Chillán, siempre nevada) ni se corre ni sube. Con cinco puntos, el orden de nieve y el de tasa
  coinciden entero (la probabilidad de eso al azar es 1 en 120), pero es post hoc y son cinco puntos: es una pista, no
  una prueba.
- **El corrimiento crece con el sol.** En Antuco 2024, S por hora: −0,41 K a las 12 UTC (2025: −0,30), −1,0 K de 15 a
  19 UTC (2025: −0,50 a −0,59) y −0,31 K a las 23 UTC (2025: −0,17). En 2026 igual (−1,03 contra −0,50 a las 19 UTC).
  Es lo que se espera si la diferencia es cuánto se calienta la roca descubierta al mediodía: en 2025 había más roca al
  sol y la BTD subía más a esa hora.
- **Lo que pesa es el contraste térmico, no la emisividad de la nieve.** La nieve tiene emisividad algo mayor a 11 que a
  12 µm, lo que subiría la BTD; lo que se ve va al revés, así que domina que la cumbre nevada queda fría. Lectura, sin
  medir el balance por separado.
- **2026 corre menos que 2024 en la mediana pero dispara más.** Con 23 días evaluables en 2026 (la compuerta con el
  nublado congelado deja menos) y el 10-11, la tasa de 2026 depende de pocos días, como ya advirtió S28b.

## 6. Qué cambia para el proyecto

- La falsa alarma de día de la zona en una cumbre sin pluma **no es un evento meteorológico que se pueda filtrar por
  cuadro**: es la base de un solo año. Una cumbre con nieve que cambia de un año a otro (Antuco y Longaví, a medio
  descubrir en primavera) no tiene una BTD de día estable entre años. Esto explica la "variación sola de un año a otro"
  que vio S29b, y por qué S28a vio subir a Antuco en 2026 sin pluma.
- **Para Chillán la amenaza es menor**: su cumbre está 91 a 95 % nevada los tres años (Δfs +0,01 en 2026), así que su
  zona no tendría este corrimiento. S31f encontró más nieve que en 2025 en el flanco SE de Chillán, que no es la zona
  del cráter; si algún detector mira ese flanco de día, la misma trampa vale ahí.
- **Antuco y Longaví no sirven como placebo diurno de la zona** en un año con otra nieve que la base: su exceso diurno
  es nieve y no dice nada de lo que pase en Chillán.

## 7. Lo que no puede decir

- Una nube muy delgada que no sube 1,6 µm cae como despejado; un cirro tenue sobre la cumbre no se separa aquí.
- La clase NUBE usa umbrales fijos de la literatura (MODIS); la máscara de NOAA marca la cumbre nevada como nube, así
  que las clases no se pueden validar contra ACM. El lado a lado (`figuras/s31i_lado_a_lado.png`) muestra que separan
  bien nieve de roca en la cumbre.
- La relación nieve y corrimiento tiene cinco puntos y se vio después de medir. Para probarla falta un criterio previo
  y datos que nadie miró (otro año, u otras cumbres con nieve variable).
- Nada aquí mira días posteriores al 24-11-2026 ni toca el detector ni las confirmaciones.

## 8. Archivos

- Criterio: `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\Goes\docs\own_volcat\s31i_antuco_dia\criterio_2026-11-27.md`
- Scripts: `...\s31i_antuco_dia\scripts\s31i_bajar.py` (bajada C03 y C05), `s31i_medir.py` (pruebas, optica, medir),
  `s31i_posthoc.py`, `s31i_lado_a_lado.py`
- Resultados: `...\s31i_antuco_dia\resultados\s31i_resultado.json`, `s31i_posthoc.json`, `medir.log`
- Figura: `...\s31i_antuco_dia\figuras\s31i_lado_a_lado.png` (06-11-2024 y 10-11-2026 que disparan, contra la misma
  fecha y hora de 2025)
- En D: (no van al repo): `D:\goes_notas\s31\s31i\l1b\` (0,2 GB), `optica_2024.npz`, `optica_2025.npz`,
  `optica_2026.npz`, logs.
