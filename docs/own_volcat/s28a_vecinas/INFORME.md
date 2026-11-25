# S28a: falsa alarma del detector S26a en volcanes tranquilos de la misma ventana, 2026 contra 2025. Informe, 25-11-2026

Criterio `criterio_2026-11-25.md` (commit `39da17b`), empujado antes de calcular un disparo del anillo o de la unión
en las vecinas. Código `scripts/s28a_medir.py` (`089c45d` más la corrección de `base` de §4); lecturas post hoc en
`scripts/s28a_posthoc.py`. Resultados en `resultados/s28a_resultado.json` y `resultados/s28a_posthoc.json`; los
cuadros de cada vecina en `D:\goes_notas\s28\s28a\cuadros_<vecina>_<año>.csv`. Días hasta el 24-11-2026; ninguno
posterior.

**En una línea: de noche las vecinas no suben (Antuco baja, Longaví casi igual), pero los intervalos no alcanzan para
decirlo (NO CONCLUYENTE); de día Antuco, sin pluma, sube tanto como Chillán (×2,6 contra ×2,7) y Longaví no (MIXTO):
el exceso diurno de Chillán en 2026 no se puede atribuir sólo a la pluma.**

## 1. Para geólogo

**La pregunta.** El detector S26a mira dos lugares: la zona de 0 a 4 km del cráter y un anillo de 4 a 40 km. Su
falsa alarma se midió en oct-nov 2025, un año sin pluma: 4,9 %. En 2026 Chillán tiene pluma todos los días, así que
ahí no se puede medir cuánto se equivoca. Antuco (61 km al S) y Longaví (77 km al N) están en la misma imagen, con el
mismo satélite y la misma máscara de nubes, y no tuvieron pluma ningún año. Si con la misma regla, cada una con su
propio fondo de 2025, disparan en 2026 igual que en 2025, el 4,9 % vale para 2026. Si suben, el año 2026 trae por sí
solo más disparos.

**Cuidado con la pluma de Chillán.** El anillo de 40 km de cada vecina llega a 21 km (Antuco) y 34 km (Longaví) del
cráter de Chillán. Se sacaron las tajadas del anillo que miran a Chillán (las que tienen algún píxel a menos de 45 km
de su cráter, la misma frontera que el método ya usa para sus controles): Antuco quedó con 8 de 12 tajadas y Longaví
con 9. Las zonas de las vecinas están a 61 y 77 km y quedaron enteras. Sacar o no esas tajadas cambia poco el
resultado (§2).

**De noche.** Antuco dispara la mitad que en 2025 (3,3 % contra 6,2 %) y Longaví casi lo mismo (6,7 % contra 5,9 %).
Chillán, en cambio, pasa de 6,7 % a 18,6 %. Lo que se ve apunta a que el exceso nocturno de Chillán no es un cambio de
año en toda la zona. Pero los disparos de 2025 se concentran en pocas noches (las de capa baja que ya vio S24), y al
remuestrear por días el intervalo de Longaví llega hasta ×3,2, por encima del ×2,8 de Chillán. Por la regla escrita
antes: **NO CONCLUYENTE**.

**De día.** Aquí está lo importante. **Antuco sube de 4,0 % a 10,6 %** (×2,6, intervalo 1,05 a 9,0), y casi todo lo
pone la zona de la cumbre (de 2,6 % a 9,4 %), no el anillo. Chillán sube de 3,9 % a 10,4 %: lo mismo que Antuco.
Longaví no sube (de 4,0 % a 3,2 %). Antuco no tiene pluma, así que **en Antuco algo de la superficie o de la atmósfera
de 2026 hace disparar la zona de día**. Y no es la pluma de Chillán llevada por el viento: sacando los cuadros con
viento de 3 a 6 km soplando desde Chillán hacia Antuco, la subida queda igual o mayor (×3,1). Por la regla:
**MIXTO (sube Antuco)**.

**Qué puede ser, sin probarlo.** Que dispare de día y no de noche apunta a la superficie al sol: roca o ceniza
descubierta que se calienta y baja la BTD 11 a 12 µm, o nubes bajas de tarde que la máscara no marca. Una temporada
con menos nieve en la cumbre de Antuco en 2026 encajaría. GOES no lo separa; una imagen Sentinel-2 o Landsat de Antuco
en un día de disparo (10-11 o 04-10-2026) lo diría.

**Lo que se vio después y pesa (post hoc).** Los disparos diurnos de las vecinas se juntan en pocos días, y **el
10-11-2026 disparan las tres cumbres a la vez por la tarde**: Chillán (los 12 cuadros de VOLCAT de 15:00 a 23:20),
Antuco (33 cuadros de 13:50 a 20:40) y Longaví (24 cuadros de 16:00 a 19:50). El 14-11 Antuco también dispara
mientras VOLCAT dibuja Chillán. Ésos son justo los dos días en que la zona de Chillán puso sus aciertos de desarrollo
(10-11: 8 de 8; 14-11: 20 de 31). Eso no prueba que en Chillán no hubiera pluma esos días (VOLCAT la vio), pero sí que
la zona de una cumbre sin pluma reacciona a la misma tarde: una parte de lo que la zona "ve" en Chillán esos días puede
ser regional. Como placebo, la unión puesta en Antuco "alcanza" 20 de 88 cuadros de VOLCAT de Chillán y la de Longaví
5 de 93, contra 63 de 93 en Chillán: la mayor parte del recuerdo de S26a sigue siendo propia de Chillán, pero no toda.

**Lectura para S26a.**

- La falsa alarma de desarrollo (4,9 %) **no se puede dar por buena para 2026 de día**: en una cumbre sin pluma de la
  misma imagen, 2026 dispara 10,6 % de día. De noche no hay señal de que suba, pero tampoco se puede descartar.
- El exceso diurno de Chillán en 2026 (10,4 %, 7,7 % sin los cuadros de VOLCAT) cabe entero en lo que subió Antuco:
  2025 de Chillán × R de Antuco da 10,3 %. **De día no hay exceso que se pueda atribuir sólo a la pluma.**
- El de noche (18,6 % contra el 7,7 % que daría Longaví, la vecina que más sube) sí es mayor que el de las vecinas en
  lo que se ve, aunque sin intervalo que lo respalde.

## 2. Cifras por el criterio

Unión a percentil 4,75, tajadas que miran a Chillán excluidas. Disparos / cuadros evaluados; R = tasa 2026 / tasa 2025;
intervalo de 95 % por remuestreo de días (2.000 réplicas).

| Periodo | Volcán | 2025 | 2026 | R | IC 95 % |
|---|---|---|---|---|---|
| Noche (03:00 a 08:50 UTC) | Antuco | 92 / 1.476 (6,2 %) | 37 / 1.128 (3,3 %) | 0,53 | 0,09 a 2,13 |
| | Longaví | 90 / 1.518 (5,9 %) | 66 / 979 (6,7 %) | 1,14 | 0,42 a 3,16 |
| | Chillán (todos los cuadros) | 98 / 1.453 (6,7 %) | 179 / 961 (18,6 %) | 2,76 | 1,24 a 9,49 |
| Día (12:00 a 23:50 UTC) | Antuco | 97 / 2.410 (4,0 %) | 156 / 1.467 (10,6 %) | 2,64 | 1,05 a 8,98 |
| | Longaví | 117 / 2.889 (4,0 %) | 54 / 1.665 (3,2 %) | 0,80 | 0,22 a 2,18 |
| | Chillán (todos) | 105 / 2.704 (3,9 %) | 146 / 1.409 (10,4 %) | 2,67 | 1,01 a 8,48 |
| | Chillán (sin cuadros P) | 105 / 2.704 (3,9 %) | 102 / 1.321 (7,7 %) | 1,99 | 0,73 a 6,36 |

**Veredictos**: noche **NO CONCLUYENTE** (las dos vecinas con R ≤ 1,5, pero el límite superior de Longaví, 3,16,
pasa el R de Chillán, 2,76); día **MIXTO (sube Antuco)** (Antuco R 2,64 con límite inferior 1,05; Longaví 0,80).

Por parte (R; IC 95 %):

| | Antuco anillo | Antuco zona | Longaví anillo | Longaví zona |
|---|---|---|---|---|
| Noche | 1,31; 0 a 5,9 (38 / 1.099 a 23 / 508) | 0,30; 0,04 a 3,0 | 0,17; 0 a 0,98 (33 / 1.157 a 3 / 613) | 1,68; 0,54 a 7,3 |
| Día | 1,20; 0,11 a 6,4 (35 / 1.165 a 18 / 501) | 3,66; 1,15 a 27 | 0,06; 0 a 0,34 (46 / 1.511 a 1 / 572) | 1,28; 0,32 a 3,8 |

Comprobación de código (§4 del criterio), antes de leer una vecina: el anillo generalizado con la geometría de Chillán
dio los mismos S y tajadas que `s23_medir.Detector` en 2025 y 2026, la unión 269 de 5.499 en el seco y 0 diferencias
con `tabla_2026.csv`; el M1 generalizado, idéntico al caché en los tres días; la zona de las dos vecinas, los conteos
de S27a. Una corrección después de la primera corrida: `Detector.base` fija el largo del anillo de Chillán (837
píxeles) y fallaba con el de Antuco (552). Se reemplazó por la misma función con el largo de cada anillo; con Chillán
es idéntica y la comprobación se repitió y pasó.

Sensibilidades (no deciden):

| | Antuco noche | Antuco día | Longaví noche | Longaví día |
|---|---|---|---|---|
| Sin excluir tajadas (12 de 12) | 0,60 (0,11 a 2,72) | 2,85 (1,11 a 10,4) | 1,24 (0,43 a 3,55) | 0,90 (0,23 a 2,51) |
| Sin viento desde Chillán hacia la vecina | 0,53 (0,07 a 2,47) | 3,10 (1,20 a 10,6) | 1,57 (0,53 a 6,25) | 0,51 (0,19 a 1,30) |

Día completo (00:00 a 23:50 UTC): Antuco 1,19 (0,58 a 2,98), Longaví 1,01 (0,48 a 2,02), Chillán 3,62 (2,03 a 7,31).

Lo que esperaba (criterio §7) contra lo que salió: día MIXTO por la zona de Antuco y noche NO CONCLUYENTE, como
esperaba; ningún NO SE SOSTIENE, como esperaba. **Me equivoqué en el anillo de Longaví**: esperaba R cerca de 1 y en
2026 casi no dispara (3 de 613 de noche, 1 de 572 de día). También salió algo que no anticipé: el anillo de las dos
vecinas se evalúa en 2026 menos de la mitad de las veces que en 2025 (14 a 18 % de los cuadros contra 36 a 41 %), por
más nube dinámica sobre el anillo con el nublado de costumbre congelado de 2026.

Post hoc (`resultados/s28a_posthoc.json`): los 3 días con más disparos diurnos ponen el 63 % (Antuco 2025), 46 %
(Antuco 2026), 37 % (Longaví 2025) y 69 % (Longaví 2026) del total. Antuco 2026: 10-11 (33, todos de la zona), 04-10
(25), 14-11 (14), 29-10 (14, del anillo). Longaví 2026: 10-11 (24) y 27-09 (10).

## 3. Lo que sigue

- **Para la confirmación en días nuevos** (decisión de la coordinadora S28 y de Nicolás, con criterio escrito antes de
  la medida): correr la unión también en Antuco y Longaví los mismos días, como placebo informativo, y anotar los
  cuadros de VOLCAT de Chillán en que también dispara una vecina. Hoy la confirmación congelada no lo pide.
- **Antuco de día**: mirar una imagen óptica (Sentinel-2 o Landsat) de la cumbre de Antuco el 10-11 o el 04-10-2026
  contra una de 2025: ¿menos nieve, roca descubierta, nube baja? Eso dice si el aumento es superficie o atmósfera.
- **Noche**: con estos intervalos no se decide con dos meses por año. Más años de fondo (S25b, oct-nov 2024) achicarían
  el intervalo de 2025.

## 4. Lo que no puede decir

Que las vecinas estén libres de toda pluma de Chillán (la exclusión es geométrica y el viento del GFS es grueso); que
la falsa alarma de Chillán en 2026 sea la de Antuco o la de Longaví (cumbre más alta, otra nieve); qué hace disparar a
Antuco de día; nada de días posteriores al 24-11.
