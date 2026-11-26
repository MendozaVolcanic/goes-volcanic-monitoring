**Veredicto: RUIDO FIJO POR PÍXEL (terreno o pareo). El anillo prefiere el SE en 2025, sin pluma, porque los píxeles de la cordillera alta al SE, a 23 a 33 km del cráter, tienen por sí solos colas bajas de BTD: basta sortear cada píxel de sus propios valores de la temporada, uno por uno y sin nube ni coherencia entre ellos, para reproducir el 63 % de disparos al SE (observado 64,5 %). El método solo (cuántos píxeles válidos tiene cada tajada) no da nada (21 %). El viento no se pudo probar (SIN PODER); post hoc, la cola de esos píxeles no cambia con el viento, y en 2024 se repite igual.**

# S31d: ¿por qué el anillo dispara hacia el SE en oct-nov 2025, sin pluma? Informe, 26-11-2026

Criterio `criterio_2026-11-26.md` (commit `8872a7a`, empujado antes de cruzar un disparo con una covariable). Código
`scripts/s31d_medir.py` (commits `aac882b` y `4179b3d`, antes de medir; `f28c9b5` sólo arregla la escritura del JSON,
ver §4). Post hoc `scripts/s31d_posthoc.py`. Cifras en `resultados/s31d_resultado.json` y
`resultados/s31d_posthoc.json`. Viento GFS y registros en `D:\goes_notas\s31\s31d\`. Sólo días de oct-nov 2025 (y 2024
como réplica); ningún día de 2026; nada de `s23b_confirmar.py`, `s30a_confirmar.py` ni del CSV de días nuevos.

## 1. Para geólogo

**La pregunta.** El anillo del detector S26a (4 a 40 km de Nevados de Chillán, 12 tajadas de 30°) marca la tajada cuya
cola baja de BTD 11 − 12 µm, ya restada la línea base de cada píxel a esa hora, es la más baja del cuadro. En oct-nov
2025, un año sin pluma, 89 de sus 138 disparos (64 %) cayeron entre el SE y el SSO (120° a 210°), que es justo hacia
donde el viento de primavera lleva la pluma. Mientras eso no se entienda, que el anillo coincida en rumbo con VOLCAT no
dice si ve la pluma. Había tres sospechosos: el método, el terreno y la atmósfera de sotavento.

**Lo que hace cada sospechoso, y cómo se le reconoce.**

- **El método** elige la tajada más baja de doce. Sin ninguna señal, gana más seguido la que tiene más píxeles
  válidos, porque entre más píxeles la cola sale más extrema. Para verlo basta llenar cada cuadro real (su máscara de
  nubes y bordes) con ruido igual en todos los píxeles.
- **El terreno** no cambia el promedio de cada píxel (la línea base lo resta), pero sí cuánto se aleja ese píxel de su
  promedio de un día a otro. Si los píxeles altos del SE tienen colas propias más hondas, la preferencia aparece aunque
  cada píxel se sortee por separado de sus propios valores de la temporada, sin coherencia entre vecinos.
- **El sotavento** (nube tenue a sotavento de la cordillera o aire que baja seco) es un fenómeno de toda la ladera a la
  vez y tiene que seguir al viento de ese día.

**Lo que salió.**

- **El método solo no explica nada.** Con la máscara real de cada cuadro y ruido igual, el SE sale en el 21 % de los
  disparos, menos que un cuarto del círculo, porque la tajada de 120° a 150° es la que más seguido queda a medias tras
  borrar nubes y bordes (válida en el 82 % de los cuadros, contra 92 a 98 % las demás). La preferencia no es un
  artefacto de contar píxeles.
- **La distribución propia de cada píxel lo explica entero.** Si cada píxel válido del cuadro se reemplaza por un valor
  sorteado de sus propios residuos de 2025 (otros días, misma hora a ±90 min), cada uno por su lado, el SE sale en el
  63 % de los disparos, contra 64,5 % observado. No hace falta que los píxeles se muevan juntos: la preferencia viaja en
  lo que cada píxel del SE hace por sí mismo a lo largo de la temporada. En 2024 (GOES-16, 38 disparos en 8 días) sale lo
  mismo: método 22 %, píxel por píxel 71 %, observado 74 %.
- **Qué tienen esos píxeles.** Todas las tajadas de cordillera (de 330° a 240°) tienen colas propias hondas (percentil 2
  de los residuos de sus píxeles entre −0,51 y −0,59 K, la más honda la de 120° a 150°), y las tres del W, sobre la
  depresión intermedia y la precordillera baja (cota mediana 765 a 923 m), mucho menos (−0,36 a −0,37 K). La cola más
  honda va con la cota: entre píxeles, Spearman −0,54 entre el percentil 2 y la cota. Que entre las tajadas de
  cordillera gane el SE sale de cómo se combinan dispersión, asimetría y número de píxeles en la cola de 8; eso lo hace
  M2 y la tabla por tajada no alcanza a mostrarlo sola. No va con tener pocos píxeles de control con la misma cota (Spearman −0,41, al revés de lo que
  daría un pareo ruidoso): apunta más al terreno que al método de pareo, sin decidirlo.
- **El viento no se pudo probar.** A 700 hPa (unos 3 km, la cota de la cumbre) sólo 3 días con disparos tuvieron el
  sotavento claramente fuera del SE y 5 claramente al SE; con 7 días de viento débil fuera de la prueba, el p más chico
  posible era 0,018, sobre el tope de 0,01 que fijé. Rótulo SIN PODER. Lo que se ve, sin valor de prueba: los días con
  el sotavento hacia otro lado siguieron disparando al SE (34 de 44 disparos, 77 %). El 17-11-2025, con viento del SW de
  10 m/s que lleva el sotavento al NE, el anillo disparó 21 veces, todas al SE.

**Lectura honesta.** El sesgo SE del anillo está en el suelo y no en el aire: los píxeles altos de la cordillera al SE
del cráter, a 23 a 33 km, alcanzan valores bajos de BTD más a menudo que los del valle, cada uno por su cuenta, y el
anillo, que busca la cola más baja, los encuentra. Lo que no puedo afirmar es qué del terreno lo hace (nieve que se
calienta y enfría distinto que la roca, emisividad de la roca, inversiones nocturnas sobre la cordillera): la prueba sólo
separa "propiedad de cada píxel" de "fenómeno coherente que sigue al viento". Y "propiedad de cada píxel" incluye todo lo
que ese píxel vive en la temporada; si una estela de sotavento visitara esos píxeles casi todos los días, también
quedaría en su distribución. El post hoc (§3) la descarta en lo que puede: la cola de esos píxeles es la misma con
viento que lleva el sotavento al SE que con viento que lo lleva a otro lado, y con el entorno del cráter despejado.

**Por qué importa para 2026.** S31c encontró que, a la hora de las plumas de VOLCAT, el anillo marca hacia el lado de
la pluma pero a 22 a 33 km del cráter, no en el tramo de 4 a 15 km donde VOLCAT la dibuja. En 2025, sin pluma, los 8
píxeles de la cola de cada disparo están a 23 a 33 km (mediana 27,6 km; sólo 4 % entre 4 y 15 km, contra 13 % del
anillo). Es el mismo lugar. Post hoc y sin prueba: lo que el anillo marca en 2026 al SE lejano puede ser esta propiedad
del terreno encendida a la hora de la pluma, y no la pluma.

## 2. Cifras del criterio

| Medida | Valor | Rótulo |
|---|---|---|
| Reproducción | 138 disparos de 2025 en 15 días, tajadas idénticas a S30b | válida |
| Cuota SE observada | 89 / 138 = 0,645 | |
| E₀, geometría pura (todos los píxeles válidos, ruido igual) | 0,222 | descripción |
| M1, máscara real y ruido igual | E₁ 0,206; exceso 0,44 (IC 95 % por días 0,15 a 0,67) | NO EXPLICA |
| M2, cada píxel de sus propios residuos | E₂ 0,634; exceso 0,01 (IC −0,28 a 0,28) | EXPLICA |
| Fracción del exceso sobre E₀ explicada | M1 −0,04; M2 0,97 | informa |
| M3, 700 hPa | 5 días sotavento SE, 3 fuera, 7 débiles; Δ −0,03, p 0,64, piso 0,018; poder del medio oráculo 0,65 | SIN PODER |
| M3, cuota SE por clase (descripción) | sotavento SE 35 / 36 (0,97); fuera 34 / 44 (0,77) | |
| M3 a 500 hPa (sensibilidad, no decide) | 4 SE, 10 fuera, 1 débil; Δ +0,45, p 0,13, piso 0,001; cuota fuera 0,49 | no decide |
| Distancia angular tajada contra sotavento (secundaria) | 700 hPa: 60°, p 0,36; 500 hPa: 83°, p 0,75 | no decide |
| M4 fecha | 21-09 a 21-10: 4 días, 0,75; 22-10 a 21-11: 11 días, 0,59; p 0,87 | no decide |
| M4 hora | 00 a 12 UTC: 68 de 86 al SE (0,79); 12 a 24 UTC: 21 de 52 (0,40); sólo 2 días tienen las dos mitades | no decide |
| Réplica 2024 | 38 disparos, 8 días; observado 0,74; E₁ 0,22 (NO EXPLICA); E₂ 0,71 (EXPLICA) | réplica |
| **Veredicto (§3 del criterio)** | M1 NO EXPLICA y M2 EXPLICA | **RUIDO FIJO POR PÍXEL (terreno o pareo)** |

La sensibilidad a 500 hPa (unos 5,5 km) no va en la misma dirección que 700 hPa: ahí los 4 días con sotavento al SE
dispararon todo al SE y los 10 de sotavento fuera, la mitad. Con p 0,13 no dice nada, pero deja abierto que una parte
dependa del viento de altura. A 700 hPa, que es la cota de la cumbre y la que fijé antes, no aparece.

Por tajada (descripción, `descripcion_tajadas` del JSON): la de 120° a 150° tiene la cota mediana más alta (2.140 m),
los menos controles con su cota (1.061), la menor fracción de cuadros válida (0,82) y el percentil 5 de Q_k − mediana
más hondo (−0,33 K, contra −0,07 a −0,12 K al W). Es la que el umbral único trata como la menos exigente.

## 3. Post hoc (no decide; escrito después de ver M1 y M2)

M2 sortea de toda la temporada; aquí se parte el pozo del que se sortea, para ver qué parte de la distribución de cada
píxel lleva la preferencia:

| Pozo de M2 | Cuota SE esperada |
|---|---|
| Todos los cuadros (criterio) | 0,634 |
| Sólo cuadros con el entorno del cráter despejado (E1) | 0,630 |
| Sólo cuadros no despejados | 0,485 |
| Sólo cuadros con sotavento a 700 hPa al SE (≥ 5 m/s) | 0,684 |
| Sólo cuadros con sotavento a 700 hPa fuera del SE (≥ 5 m/s) | 0,658 |

La preferencia no necesita nubes (con cielo despejado sale igual) y cambia poco con el viento (0,68 contra 0,66). Lo
que el sotavento no hace en la distribución de esos píxeles, no puede hacerlo en el anillo. Distancia de los 8 píxeles
de la cola en los disparos de 2025: mediana 27,6 km, cuartiles 23,4 y 33,3 km.

## 4. Cómo se corrió

La primera corrida calculó la reproducción, M1, M2 y M3 y se cayó al escribir el JSON (un entero de numpy), antes de
la réplica 2024 (registro guardado en `D:\goes_notas\s31\s31d\medir_corrida1_falla_json.log`). Arreglé sólo la
escritura (`f28c9b5`) y la corrí de nuevo completa; todo es determinista (semillas fijas) y las cifras de M1 a M3 de las
dos corridas son idénticas. El viento GFS 1,0° de 2025 (311 horas nuevas, 1 MB) se bajó con el descargador de S27a sin
cambios; ninguna hora faltó.

## 5. Lo que no puede decir

- Qué del terreno hace la cola honda (nieve, roca, inversión nocturna). La mitad nocturna dispara más al SE (79 %) que
  la diurna (40 %), lo que calza con un efecto de superficie fría de noche en la cordillera, pero sólo 2 días tienen
  disparos en las dos mitades: no hay prueba por días.
- Si el anillo ve la pluma en 2026: esto sólo dice que su lado preferido es un rasgo del terreno, y que el tramo que
  marca en 2026 (S31c) es el mismo que marca en 2025 sin pluma.
- Nada de días posteriores al 24-11-2026.

## 6. Qué sigue (para la coordinadora y Nicolás)

1. **Normalizar cada píxel por su propia dispersión** (residuo dividido por la dispersión robusta de ese píxel a esa
   hora en el año de referencia) antes de buscar la cola. Es lo que M2 indica: el anillo compara colas de píxeles que
   no tienen la misma escala. Como desarrollo, con criterio nuevo, sobre 2025 y 2024, sin tocar la regla congelada de la
   confirmación. Si con eso el sesgo SE desaparece en 2025 y en 2026 el anillo sigue marcando hacia la pluma, recién ahí
   el rumbo diría algo.
2. Leer los disparos de 2026 del anillo al SE lejano con cuidado: S30b y S31c ya los rebajaron; este resultado agrega que
   el lugar exacto que marcan es el lugar que el terreno favorece.
