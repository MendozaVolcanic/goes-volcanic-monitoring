# S31j: espejo de la vía pluma/bocanada de VOLCAT. Informe, 27-11-2026

**Veredicto (por la regla): NO REPRODUCE** (Sens_P 0 de 100 y p_D 1,0). Con la falsa alarma que se le permitió (la del
detector congelado en 2025), el espejo no publica ninguno de los 100 cuadros en que VOLCAT dibujó la pluma de Chillán, ni
ningún N: en todo 2026 publica un solo cuadro (13-11 19:50, dentro del evento VCB de VOLCAT de esa tarde). La pieza que
falta es el **nacimiento**: la compuerta de calor estuvo abierta en todos los P y el seguimiento no tuvo qué seguir.

Criterio `e29dd33`, enmienda 1 `d82e697` y enmienda 2 `9d0383b`, todos empujados antes de calcular un solo cuadro del
espejo (§5 explica las dos corridas); guarda operativa `e93e928` (el calor se lee sólo con la bajada terminada).
**Desarrollo, no confirmación**: todos los días usados ya los vieron sesiones anteriores; ningún día GOES posterior al
24-11-2026.

Archivos (en el repositorio, `docs/own_volcat/s31j_espejo_via_pluma/`, y mientras no se fusione en
`C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\Goes\.claude\worktrees\s31j-espejo-via-pluma-382c61\docs\own_volcat\s31j_espejo_via_pluma\`):
`criterio_2026-11-27.md`, `enmienda_1_antes_de_medir_2026-11-27.md`, `enmienda_2_antes_de_medir_2026-11-27.md`,
`scripts\s31j_bajar_calor.py`, `scripts\s31j_medir.py`, `scripts\s31j_posthoc.py`, `resultados\s31j_resultado.json`,
`resultados\s31j_por_cuadro.csv`, `resultados\s31j_posthoc.json`. Fuera del repositorio: `D:\goes_notas\s31\s31j\`
(cubos de z, calor por cuadro y por noche, registros de la bajada y de las dos corridas; 44 MB).

## 1. Para geólogo

**La pregunta.** Nicolás preguntó si VOLCAT no estará usando un código más simple de lo que suponemos. Lo que ya se
sabía apuntaba a eso: VOLCAT publica la pluma de Nevados de Chillán sin firma de ceniza en el píxel, por su vía de
"pluma o bocanada", y casi siempre arrastrándola de un cuadro al siguiente. Se armó un espejo de esa vía con las piezas
públicas: el volcán tiene que haber mostrado calor en el cráter en las últimas dos semanas, algo débil tiene que aparecer
pegado al cráter (basta un píxel a 10 km o menos) y lo que aparece después a menos de 30 km por cada 10 min se toma como
la misma pluma.

**Lo nuevo de la lectura.** Los registros de VOLCAT que trae el paquete de prueba de SSEC imprimen los umbrales de la vía
pluma: objeto mínimo de **un píxel** (cinco en la vía normal), sólo para objetos **tenues** (emisividad mediana de 0,5 o
menos), y una anomalía térmica que queda en la memoria del sistema **15 días**. El nacimiento aceptado que se ve en esos
registros (Kirishima, 2025) tenía la BTD más alta que su entorno y probabilidad de ceniza de 2,4 %: no entró por firma.

**Lo que salió.**
- **El calor no es lo que falta.** El indicador de calor nocturno se encendió en 23 noches de 2026 desde el 12-10 y la
  compuerta estuvo abierta en todos los cuadros con clase, incluidos los 100 P. En 2025 no se encendió ninguna noche
  (52 con dato): con la compuerta, el espejo no publica nada en un año tranquilo, y eso sólo dice que el cráter estaba
  frío.
- **El nacimiento es lo que falta.** Para que el espejo, puesto sin compuerta sobre el Chillán tranquilo de 2025, no
  publique más que el detector congelado (4 % de los cuadros), el píxel tiene que ser más raro que todo lo que ese mismo
  píxel mostró a esa hora en la temporada de 2025. A ese nivel, en 2026 no nace nada a la hora de VOLCAT: en todo el
  periodo nace un solo objeto (13-11 19:50, a 6,2 km del cráter, en plena cadena "VCB" que VOLCAT abrió a las 19:00). De
  los cuatro nacimientos de VOLCAT, dos estaban bajo nube (no evaluables) y en los otros dos el píxel más raro a 10 km
  del cráter quedó en z −2,4 (13-11 19:00) y −3,0 (14-11 16:30), lejos del umbral.
- **El seguimiento no salva nada sin nacimiento.** Con un seguimiento laxo (sensibilidad S1: continuación con cualquier
  píxel en su 10 % más bajo), el único nacimiento se arrastra 14 horas, toda la noche del 13 al 14-11, y se apaga a las
  09:50 UTC del 14-11, antes de que VOLCAT abra sus cadenas de ese día. Cero P también, y 4 % de los N.

**Post hoc, lo que sí hay.** Si se afloja el umbral más allá de lo permitido, el espejo publica más en los P que en los N:
entre los cuadros despejados de la tarde (15 a 24 UTC), con c = −2,5 publica 78 % de los P, 30 % de los N de 2026 y 19 %
de las tardes de 2025; con c = −3,0, 17 %, 5 % y 6 %. El píxel más raro junto al cráter es algo más bajo cuando VOLCAT
dibuja (mediana z −1,76 contra −1,54 en N y −1,24 en 2025), pero cuadro a cuadro no separa (AUC 0,63, IC por días de
0,49 a 0,75). Es la misma conclusión de S20b a S31h con otra herramienta: junto al cráter hay una señal débil en el IR de
2 km, insuficiente para abrir una pluma sin abrir también una de cada cinco tardes tranquilas.

**Qué significa.** No es un código más simple con las piezas que conocemos. Con el calor, el anclaje, el objeto de un
píxel y el seguimiento de VOLCAT, nuestro IR no tiene con qué abrir la pluma de Chillán a la falsa alarma de un detector
honesto. VOLCAT la abre con algo que no está en ninguna fuente pública: las pruebas de contraste de color ("RGB1" y
"RGB2" del registro), la "time trend" y la lista de volcanes activos (un volcán en esa lista podría tener la puerta casi
abierta). Esas son preguntas para Pavolonis; para un VOLCAT propio, el nacimiento tiene que venir de otra medida
(cámaras del OVDAS, verdad fina, luz reflejada), no del IR de 2 km.

## 2. Qué se copió de VOLCAT y de dónde

Lo que hace VOLCAT con la pluma de Chillán ya estaba descrito por fuera: publica objetos cuyos píxeles tienen
probabilidad de ceniza casi nula (H15, H20a), por la vía `ASHPLUMEPUFF` y casi siempre como continuación de un objeto
anterior (H28). Faltaba la puerta de entrada. Esta sesión encontró sus umbrales en la cabecera de los registros
`geocatASHOBJ` de los paquetes de prueba de SSEC (Kirishima, versión de julio de 2026, en
`D:\goes_notas\s17\paquetes\kirsh\kirsh_h9-japan_july2025_r20260709-volcat-code-ancil\reference_data\logs\`), que
imprimen la configuración de cada vía de objeto:

| Parámetro (vía de ceniza) | básica | pluma/bocanada | temporal (seguimiento) |
|---|---|---|---|
| píxeles mínimos del objeto | 5 | **1** | 0 |
| emisividad total mediana máxima | 0,90 | **0,50** | apagado (1,01) |
| fracción ruidosa máxima | 0,25 | 0,25 | apagado (1,01) |
| no uniformidad máxima | 0,75 | 0,75 | apagado (1,01) |
| opción de contraste | 1 | 2 | no aplica |

Y para el calor: una anomalía térmica queda en la historia de VOLCAT **15 días** tras la última detección válida. El
registro del nacimiento aceptado de Kirishima (20:17:30) muestra el camino: "buscando plumas débiles", emparejada con el
volcán, "pasa el contraste espacial detallado", "se conserva por patrón robusto en espacio o tiempo", con 8 píxeles a
1 km del volcán y probabilidad mediana de píxel de 2,4 %. Esa pluma tenía la BTD mínima 0,74 K **más alta** que su
entorno: no entró por firma.

Dicho como geólogo: la vía pluma es para objetos **tenues**, basta **un píxel** si está pegado a un volcán que tuvo calor
en las últimas dos semanas, y después el seguimiento lo arrastra sin pedir nada. Lo que no se pudo leer (contraste de
opción 2, pruebas de color, "time trend", lista de volcanes activos) no se inventó.

## 3. La regla del espejo

- **Píxel candidato**: el residuo de BTD de cada píxel del anillo de 4 a 40 km (M1 menos su línea base de 2025),
  expresado como percentil de su propia temporada de 2025 a esa hora (z de S31e T1), bajo un umbral c.
- **Objeto**: píxeles candidatos conectados (8 vecinos).
- **Nace** si (1) el indicador VRP nocturno de 3,9 µm (validado en `vrp_nocturno/`) se encendió en Chillán en alguna de
  las 15 noches anteriores, (2) algún píxel del objeto está a 10 km o menos del cráter, (3) tiene 1 píxel o más.
- **Continúa** (H28 tal cual): cualquier objeto a 0,05 km/s × Δt de lo publicado en el cuadro evaluable anterior (30 km a
  10 min), sin calor, anclaje ni tamaño; se corta si pasan más de 30 min sin cuadro evaluable.
- **c**: el más laxo de −1,00 a −3,25 con el que el espejo, corrido en 2025 sin compuerta de calor, publica no más que
  la falsa alarma del anillo congelado (0,040 por día, 0,038 global); en 2025, cada día con c sin ese día.

## 4. Resultados (medida única, corrida 2)

Comprobación de código (§6 del criterio, con la enmienda 2): S del congelado 0 distintos; z de la corona idéntica a la de
S31h en toda celda con pozo propio (diferencia 0,0; las 34, 550 y 588 celdas distintas de 2025, 2026 y 2024 tienen todas
pozo propio menor de 20); indicador de calor con el mismo `enc` y `n10` que la validación en 15 de 15 noches; sintéticas
OK. Bajada de calor: 3.408 cuadros, faltan 3 en S3 (30-09 02:30, 06-10 00:30, 02-11 23:30 de 2026).

**Calor.** 2025: 84 noches, 52 con dato, 0 encendidas; compuerta abierta en 0 % de los cuadros evaluables. 2026: 58
noches, 35 con dato, 23 encendidas (12-10, 15 a 18-10, 25 a 31-10, 07 a 14-11, 22 a 24-11); compuerta abierta en 100 %
de los cuadros evaluables con clase; 0 P con la compuerta cerrada.

**Umbral c (§3).** Falsa alarma de 2025 sin compuerta, media por día (global): −2,50: 0,147 (0,175); −2,75: 0,090
(0,112); −3,00: 0,046 (0,058); −3,25: 0,0001 (0,0002). De −1,00 a −3,00 ninguno cumple 0,040 y 0,038: c = **−3,25**,
el mismo para los 62 días y para cada día sin sí mismo.

| Medida | Principal | S1 (seguimiento laxo) |
|---|---|---|
| P publicados (de 100; 93 evaluables en 9 días) | 0 | 0 |
| FA_N, media por día (IC 95 %) | 0,000 (0 a 0) | 0,042 (0 a 0,117) |
| FA otro, media por día | 0,003 | 0,041 |
| nulo D: T, T\* medio, p_D | 0; 0,16; 1,0 | 0; 2,38; 1,0 |
| solape de huella | sin P publicados | sin P publicados |
| FA 2025 con compuerta, media por día | 0,000 (0 de 5.500 cuadros) | no aplica |
| FA 2025 sin compuerta, media por día | 0,0001 (1 cuadro, 1 día) | 0,013 (54 cuadros, 2 días) |
| FA 2024 sin compuerta, media por día | 0,0024 (9 cuadros, 1 día) | 0,0030 (11 cuadros, 1 día) |

Arrastre (e): no hay P publicados que repartir. En 2026 el principal publica 1 cuadro (nacimiento, 13-11 19:50, clase
otro); S1, 85 cuadros, todos continuación de ese nacimiento, de 13-11 19:50 a 14-11 09:50 (69 N, 13 otro, 3 sin clase).
El nulo D decide (24 días donantes, 24 elevado a 10 configuraciones; piso 0,0001), pero con T = 0 no hay nada que
separar. Rótulo: **NO REPRODUCE**, por las dos condiciones (Sens_P < 0,50 y p_D > 0,01).

**Nacimientos de VOLCAT (descriptivo):** 13-11 19:00 evaluable, con calor, z mínima a 10 km −2,40, no publica; 14-11
12:40 no evaluable (nube); 14-11 16:30 evaluable, con calor, −2,98, no publica; 18-11 10:10 no evaluable. Los cuatro
tienen clase "otro" en la tabla de clases (su objeto del PNG no cae en la zona del cráter que define P).

## 5. Las dos corridas

La corrida 1 (`e93e928`) paró en la comprobación de código, como manda el criterio, antes de calibrar c y de correr el
espejo: la z de la corona difería de la de S31h (máximo 0,79). Mirado antes de cambiar nada, las diferencias caían en 6 a
8 píxeles y sólo de 15 a 20 UTC: S31e y S31h usan distinto pozo de respaldo cuando el píxel tiene menos de 20 valores
propios, y la comprobación lo había ignorado. La enmienda 2 (`9d0383b`) la restringe a las celdas con pozo propio y exige
que toda diferencia caiga fuera de ellas. La corrida 2 recalculó todo desde cero con el mismo código y la misma semilla;
es la misma cuenta, porque nada del espejo se había calculado. Registros: corrida 1 en
`D:\goes_notas\s31\s31j\medir_corrida1_paro_en_comprobacion.log`, corrida 2 en `D:\goes_notas\s31\s31j\medir.log`.

## 6. Post hoc (`scripts\s31j_posthoc.py`, `resultados\s31j_posthoc.json`; no decide)

**Curva del umbral en 2026, con compuerta y seguimiento del criterio:**

| c | P publicados (de 100) | de ellos con nacimiento | FA_N media por día | p_D | FA 2025 sin compuerta |
|---|---|---|---|---|---|
| −2,00 | 91 | 34 | 0,585 | 0,0001 | 0,311 |
| −2,25 | 84 | 22 | 0,433 | 0,0001 | 0,215 |
| −2,50 | 69 | 16 | 0,270 | 0,0001 | 0,147 |
| −2,75 | 33 | 10 | 0,138 | 0,0053 | 0,090 |
| −3,00 | 15 | 7 | 0,053 | 0,082 | 0,046 |
| −3,25 | 0 | 0 | 0,000 | 1,0 | 0,0001 |

El nulo D con c laxo se aparta mucho (T\* medio 7,5 contra 69 a −2,5), pero parte de eso es nube: los días sin VOLCAT
están más nublados a la hora de los P (S31f) y un cuadro nublado no se publica. Con sólo cuadros **evaluables de 15 a
24 UTC**: a −2,50, P 68 de 87 (78 %), N 30 % por día (16 días), 2025 19 % por día (49 días); a −2,75, 37 %, 16 % y 11 %;
a −3,00, 17 %, 5 % y 6 %. La mayoría de los P publicados con c laxo son arrastre (a −2,5, 53 de 69).

**z mínima a 10 km o menos del cráter:** P mediana −1,76 (p10 −2,78; 7,8 % bajo −3), N −1,54 (2,1 %), otro −1,71, 2025
a las horas de los P −1,24 (2,0 %). AUC de P más bajo que N a las horas de los P: 0,63, IC 95 % por días de 0,49 a 0,75.

**Lectura.** Junto al cráter, a la hora de VOLCAT, el píxel está algo más bajo en BTD que en los N y que en 2025, lo que
calza con la señal débil que vieron S20b, H29 y S31c. Pero la distancia entre P y N es chica frente al ruido del propio
píxel: el umbral que la separa algo (−2,5 a −2,75) cuesta 11 a 19 % de tardes tranquilas publicadas, y el que respeta la
falsa alarma no ve nada.

**Defecto del criterio, dicho.** La z de T1 se satura cerca de −3,3 (pozos de unos mil valores), así que el paso de
−3,00 a −3,25 cruza la saturación y la falsa alarma cae de 0,046 a 0,0001: la grilla no previó ese salto. No cambia el
rótulo: con −3,00, que se pasaba apenas del presupuesto, el espejo publica 15 P con p_D 0,08, también NO REPRODUCE.

## 7. Lo que podría estar equivocado

1. **La pieza no pública puede ser justamente la que importa.** Si un volcán de la lista de volcanes activos de VOLCAT
   tiene la puerta de nacimiento casi abierta, el espejo con un umbral de píxel nunca lo reproducirá; eso no se puede
   comprobar sin el código o sin preguntarle a Pavolonis.
2. **Nuestro "píxel candidato" no es el de VOLCAT.** Usamos BTD contra su línea base de 2025; VOLCAT agrupa con
   probabilidades de sus tablas y emisividades contra un cielo modelado. Una pluma tenue sin firma en BTD puede tener
   contraste en esas cantidades (las pruebas de color del registro).
3. **El calor es de noche y la pluma de día.** La compuerta mide un estado de días, no el calor del momento; VOLCAT ve
   calor también de día. Como la compuerta estuvo abierta en todos los P, esto no cambia el resultado de 2026.
4. **La falsa alarma de 2025 pone el presupuesto.** Un presupuesto más generoso (VOLCAT puede permitírselo porque sólo
   abre la vía con calor) daría más P; el post hoc muestra el precio.
5. **VOLCAT no es verdad de terreno** y en 2026 todos los días tienen pluma (Nicolás): un N publicado no es falsa alarma
   segura, y un P no publicado no prueba que no haya pluma en el IR.

## 8. Qué sigue (propuesto, no hecho)

- Correo a Pavolonis: agregar qué hacen la opción de contraste 2 y las pruebas "RGB1" y "RGB2" de la vía pluma, qué es la
  "time trend", y si Nevados de Chillán está en `active_volcano_list.txt` y qué cambia eso.
- No insistir con nacimientos por BTD a 2 km: S22 a S31h y este espejo dicen lo mismo. Si se quiere un VOLCAT propio para
  Chillán, el nacimiento debería venir de una medida independiente (cámaras del OVDAS o el REAV) y el seguimiento H28
  podría llevarlo; es otro diseño, con su propio criterio.

## 9. Cómo reproducirlo

```
cd C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\Goes\docs\own_volcat\s31j_espejo_via_pluma\scripts
python -I -B s31j_bajar_calor.py 10
python -I -B s31j_medir.py medir
python -I -B s31j_posthoc.py
```

Requiere los cubos de S22b, S23, S25b y S26a en `D:\goes_notas\` (los mismos de S31e y S31h), los PNG de VOLCAT y
`D:\goes_notas\s31\s31h\corona_T1.npz` para la comprobación 2. La bajada pesa 43 MB y tarda unos 35 min; la medida,
unos 13 min.
