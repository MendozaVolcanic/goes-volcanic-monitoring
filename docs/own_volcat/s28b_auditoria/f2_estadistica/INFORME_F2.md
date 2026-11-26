# S28b, frente F2: estadística e instrumento. Informe del auditor, 26-11-2026

**Hallazgos que cambian un veredicto por su propia regla con el nulo corregido: 2** (ID 202, "14-11 ALCANZADO" de
S25a pasa a "14-11 no alcanzado" con el día como unidad; ID 203, prueba P de S27a pasa de SIN PODER a PLUMA NO con un
umbral de poder alcanzable). **Uno más cambia: SIN DATO** (ID 201, el p25 por cuadro de las confirmaciones congeladas
S25a y S26a). Ninguno de los veredictos que deciden (S23a PARCIAL, S25a ALCANZA, S26a ALCANZA de desarrollo y p* = 4,75,
S25b AGUANTA, S28a MIXTO) cambia de rótulo; varios cambian de lectura (ID 204, 205, 206).

- Auditor: Opus 5.5 (este agente), esfuerzo de la sesión. Base: `origin/main` 8894722. Plan: `PLAN.md` en 002feff;
  `git diff 002feff -- docs/own_volcat/s28b_auditoria/PLAN.md` da 0 líneas (comprobado en esta sesión).
- Instrumento (todo en `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\Goes\.claude\worktrees\s28b-auditoria-s23-s28a-c1cff8\docs\own_volcat\s28b_auditoria\f2_estadistica\scripts\`):
  `f2_pisos.py` (barrido de pisos), `f2_cubos.py` (F, ev y alcanzado por cuadro de 2025 y 2026 de las cuatro reglas),
  `f2_bloques.py` (nulos por día), `f2_dia14.py`, `f2_mismo_dia.py`, `f2_placebo_confirmacion.py`,
  `f2_cobertura.py`, `f2_regimen.py`, `f2_fuga_costumbre.py`, `f2_fuga_base_zona.py`, `f2_s26b_noches.py`,
  `f2_s25b_dias.py`, `f2_s28a_semillas.py`. Salidas en `D:\goes_notas\s28\s28b\f2\` (cerca de 1 MB).
- Control de código del instrumento: `f2_cubos.py` reproduce exacto 8/30 (S23a), 44/93 (S25a), 63/93 (S26a a 4,75) y
  25/54 (S23b desarrollo) (`D:\goes_notas\s28\s28b\f2\cubos.log`); `f2_bloques.py` reproduce los p25 publicados
  (7,912e-5, 1,775e-34, 6,158e-53); `f2_fuga_costumbre.py` reproduce el seco publicado (unión 283/5.499 = 0,05146 a
  percentil 5, 269/5.499 = 0,04892 a 4,75; anillo media por día 0,04279; zona 176/5.499).
- No se corrió nada sobre días posteriores al 24-11-2026; no se corrió `s23b_confirmar.py`; no se tocó nada fuera de
  esta carpeta y de `D:\goes_notas\s28\s28b\f2\`. D: tenía 24 GB libres al empezar.
- Efecto lateral declarado: importar los módulos auditados con `python -I` (sin `-B`) escribe `__pycache__\*.pyc` en
  sus carpetas `scripts\` (s22a, s22b, s23, s25a, s26a, h24, h29). Están en `.gitignore` (`.gitignore:8`) y `git
  status` no los muestra; otros frentes escribieron otros en paralelo (por ejemplo `s23b_confirmar.cpython-312.pyc` a
  las 00:16, que yo no importé), así que no los borré. Para una próxima corrida: `python -I -B`.

## Líneas base rojas

1. **Piso inalcanzable de S27a: ENCONTRADA por el instrumento, a ciegas.** `f2_pisos.py` recorre todo
   `resultados/*.json` de las nueve carpetas buscando conteos de réplicas y todo `criterio*.md` buscando umbrales de p,
   sin leer informes. Marcó sola `s27a_resultado.json /P/poder_pluma_ideal/n_corrimientos: n=60 piso=0.01639 <==
   INALCANZABLE [0.01]` (y los demás corrimientos de S27a, 57 y 60). No había leído el `INFORME.md` de S27a cuando
   corrió (lo leí después, sólo para comprobar si estaba rotulado: lo está, ID 203).
2. **pN por hora degenerado de S23a: ENCONTRADA, pero no a ciegas.** `s23a_resultado.json` trae `EN_2026: 0.0` y
   `pN: 0.0`; con `rN(h) = 0` en todas las horas de los P, `s23_medir.py:422` da una cola Poisson binomial exactamente 0.
   La vi en el json después de haber leído `criterio_S23b_2026-11-25.md` §4, que ya lo cuenta. Mi instrumento la
   reproduce (ID 207), pero no puedo afirmar que la habría visto sin esa lectura.

## Hallazgos (de más grave a menos)

### 201. El p25 por cuadro de las confirmaciones congeladas de la zona y la unión cumple con días de 2026 sin VOLCAT 5 a 7 veces más de lo nominal
- ARCHIVO:LÍNEA: `s25a_crater\criterio_confirmacion_2026-11-25.md:25-28` (CONFIRMA y PARCIAL piden p25 ≤ 0,01);
  `s26a_combinado\criterio_2026-11-25.md:119-122`; código `s26a_combinado\scripts\s26a_medir.py:157-158` (p25
  Poisson binomial por cuadro) y `:403-413`.
- QUÉ PASA: el p25 de la confirmación trata cada cuadro P como un sorteo independiente. Con el gatillo de 20 P en 2 días,
  todo lo que pasa en el día (pluma diaria, depósito, nieve) entra 20 veces. Placebo: patrones de horas de P reales de
  dos días del desarrollo (pares con 20 P evaluados o más) puestos en 2 días de 2026 sin P de VOLCAT: el p25 por cuadro
  queda ≤ 0,01 en **7,45 %** de 4.000 placebo con la zona (4,25 % además con R ≥ 0,25) y en **5,17 %** con la unión
  (0,7 % con R ≥ 0,40). Con el anillo S23b, 0 %. Con 9 días en vez de 2 (`f2_bloques.py`, placebo de 500), el p25 por
  cuadro cumple ≤ 0,01 en 7,8 % (zona) y 5,6 % (unión); el mismo placebo contra el nulo por días, 0 %.
- CÓMO SE VE EN EL VEREDICTO: un PARCIAL de S25a o S26a el día de la medida única no tiene la tasa de error de 1 % que su
  umbral sugiere, sino del orden de 5 a 7 % contra un día cualquiera de 2026 (que según Nicolás tiene pluma; el placebo
  mide "sin VOLCAT", no "sin pluma"). CONFIRMA exige además pN ≤ 0,05 contra los N de los días nuevos, que este placebo
  no simula. Cambia un veredicto: **SIN DATO** (la confirmación no se ha medido).
- CÓMO REPRODUCIRLO: `python -I f2_cubos.py` (9 min) y `python -I f2_placebo_confirmacion.py`. Salida:
  `S25a_conf {... 'frac_p25_le_0.01': 0.0745, 'frac_p25_le_0.01_y_R_ok': 0.0425}`,
  `S26a_conf {... 'frac_p25_le_0.01': 0.0517, 'frac_p25_le_0.01_y_R_ok': 0.007}`, `S23b {... 0.0, 0.0}`
  (`D:\goes_notas\s28\s28b\f2\placebo_confirmacion.json`).
- CONFIANZA: CONFIRMADO (la cifra); que esto sea "error" depende de si se acepta que los días sin VOLCAT tienen pluma.
- GRAVEDAD: 4 (toca dos confirmaciones congeladas; pasa al verificador por §5 del plan).

### 202. "14-11 ALCANZADO" (S25a) sólo existe con cuadros independientes: con el día como unidad su umbral es inalcanzable
- ARCHIVO:LÍNEA: `s25a_crater\criterio_2026-11-25.md` §4 ("14-11 ALCANZADO" si 3 P alcanzados o más y su p25 ≤ 0,01);
  `s25a_crater\scripts\s25a_medir.py:367-371`.
- QUÉ PASA: los 31 P evaluados del 14-11 son un solo día. p14 = 8,3e-20 sale de tratarlos como 31 sorteos. Con el día
  como unidad (cada día de 2025 con su base y umbral sin sí mismo, el P toma el alcanzado del cuadro evaluado más
  cercano a ±60 min), ningún día de 2025 alcanza 20 en esas horas (máximo 15; luego 13, 11, 8), pero el p mínimo posible
  con 59 días de 2025 con evaluados es 1/60 = 0,0167 > 0,01. Además, dentro del propio 14-11 los N disparan igual o
  más que los P: P 20 de 31 alcanzados, N del mismo día 44 de 60 (ID 204), y no hay ningún N a menos de 3 h de un P ese
  día.
- CÓMO SE VE EN EL VEREDICTO: con el nulo por día, "14-11 ALCANZADO" pasa a "14-11 no alcanzado" (p = 0,0167 > 0,01).
  Cambia: **sí** (rótulo aparte de S25a; S26a §0 y la elección de la unión se apoyan en él).
- CÓMO REPRODUCIRLO: `python -I f2_dia14.py` → `14-11: P evaluados 31, alcanzados 20` / `días de 2025 con algún
  evaluado: 59; piso del p por día 1/(n+1) = 0.0167` / `días de 2025 con >= 20 alcanzados en esas horas: 0; máximo 15`.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 4.

### 203. Prueba P de S27a: el umbral de poder (p ≤ 0,01 con 60 corrimientos) no se puede cumplir, y con uno alcanzable el veredicto sería PLUMA NO
- ARCHIVO:LÍNEA: `s27a_noche_causa\criterio_2026-11-25.md:53-56` (p = (1 + #) / (1 + número de k), k de 3 a N − 3) y
  `:59-63` y `:69` (poder sin p ≤ 0,01 ⇒ SIN PODER); `s27a_noche_causa\scripts\s27a_medir.py:49` (`KMIN = 3`),
  `:159-161`, `:359`.
- QUÉ PASA: con 65 noches de 2026 hay 60 corrimientos y el p mínimo es 1/61 = 0,0164 > 0,01. La pluma ideal da C = 0,77
  y 0 de 60 corrimientos la igualan: p = 0,01639, el piso. SIN PODER estaba fijado antes del dato.
- CÓMO SE VE EN EL VEREDICTO: P quedó "SIN PODER (no decidible)". Con cualquier umbral alcanzable (por ejemplo 0,05 o
  el piso), el poder pasa; 2026 tiene 96 cuadros y 21 noches (pasa los mínimos) y p(2026) = 0,344 > 0,20: por la tabla
  del criterio, **PLUMA NO**. Cambia: **sí** (SIN PODER → PLUMA NO). El propio `INFORME.md` de S27a:64 y :80 lo dice y
  lo deja rotulado fuera del veredicto: el hallazgo es el diseño, no un ocultamiento.
- CÓMO REPRODUCIRLO: `python -I f2_pisos.py` (salida citada arriba, `D:\goes_notas\s28\s28b\f2\pisos.json`); y leer
  `s27a_resultado.json` P: `poder_pluma_ideal p_corrimiento 0.01639…, n_corrimientos 60`, `2026 p_corrimiento 0.3443,
  cuadros 96, noches 21`.
- CONFIANZA: CONFIRMADO. Línea base roja 1.
- GRAVEDAD: 4 (veredicto de desarrollo).

### 204. La zona (S25a) no separa los cuadros de VOLCAT de los otros cuadros del mismo día: su ALCANZA mide "día encendido", no "cuadro con VOLCAT"
- ARCHIVO:LÍNEA: `s25a_crater\scripts\s25a_medir.py:350-353` (pN: N de todos los días a ±60 min de la hora de algún P);
  criterio `s25a_crater\criterio_2026-11-25.md` §4.
- QUÉ PASA: dentro de cada día con P, los N del mismo día se alcanzan tanto como los P. Zona: Mantel-Haenszel por día,
  OR = 0,96, p = 0,96 (todo el día); con sólo los N a 3 h o menos de un P, OR = 1,6, p = 0,55. Por día: 08-11 P 0/13,
  N 59/82; 10-11 P 8/8, N 31/32; 14-11 P 20/31, N 44/60; 28-10 P 15/26, N 0/75. El pN publicado (2,3e-9) compara P de
  unos días con N de otros días a la misma hora: lo que separa es el día. La unión sí separa dentro del día (OR 2,8,
  p 3,7e-6; a 3 h, OR 9,5, p 1,1e-6), por el anillo (S23b: 0 N alcanzados en el mismo día salvo 11-11, 4 de 33).
- CÓMO SE VE EN EL VEREDICTO: ALCANZA de S25a no cambia (su regla es pN agrupado por hora), pero no significa "la zona
  dispara cuando VOLCAT dibuja": significa "los días en que VOLCAT dibuja cerca del cráter, la zona está encendida",
  que es lo mismo que daría una pluma diaria o un depósito con días buenos y malos. Esta prueba no está en ningún
  criterio (informativa). No cambia el veredicto, cambia su lectura.
- CÓMO REPRODUCIRLO: `python -I f2_mismo_dia.py` (`D:\goes_notas\s28\s28b\f2\mismo_dia.json`):
  `S25a_todo_el_dia OR_MH 0.958 p 0.9558…`, `S25a_N_a_3h_de_un_P OR_MH 1.617 p 0.5452…`,
  `S26a_desarrollo_todo_el_dia OR_MH 2.818 p 3.67e-06`.
- CONFIANZA: CONFIRMADO (las cifras). La hora de los N del mismo día no es la de los P (a 70 min o más): la variante a
  3 h lo acota sin eliminarlo.
- GRAVEDAD: 4 (lectura de un veredicto que decide qué se muestra a Nicolás).

### 205. Los p por cuadro sobrestiman la evidencia en órdenes de magnitud; con el día como unidad, ningún rótulo que decide cambia
- ARCHIVO:LÍNEA: `s23_fondo_2025\scripts\s23_medir.py:265-283, 421`; `s25a_crater\scripts\s25a_medir.py:349-353`;
  `s26a_combinado\scripts\s26a_medir.py:153-166`.
- QUÉ PASA: p25 y pN suponen cuadros independientes; los P son 100 cuadros en 10 días (33 el 14-11, 26 el 28-10) y los
  disparos vienen en rachas. Recalculado con el día como bloque (nulo D25: a cada día con P un día de 2025 al azar, cada
  P con el alcanzado del cuadro evaluado más cercano a ±60 min, base y umbral sin ese día; nulo DN: lo mismo con los N
  evaluados de un día de 2026; 20.000 réplicas, piso 5,0e-5):

  | Veredicto | p25 por cuadro | p25 por día | umbral | pN publicado | pN por día | umbral | rótulo |
  |---|---|---|---|---|---|---|---|
  | S23a PARCIAL (8/30) | 7,9e-5 | **0,020** | 0,05 | 0 (degenerado) | piso | 0,05 | no cambia |
  | S23b desarrollo (25/54) | 1,0e-19 | piso | 0,01 | 5,8e-18 | piso | 0,05 | no cambia |
  | S25a ALCANZA (44/93) | 1,8e-34 | piso | 0,01 | 2,3e-9 | **0,0020** | 0,05 | no cambia |
  | S26a ALCANZA desarrollo (63/93) | 6,2e-53 | piso | 0,01 | 1,8e-22 | piso | 0,05 | no cambia |

  El S23a es un día (08-11: 8 de 13); su p por día queda en 0,02, a 2,5 veces del umbral 0,05 y 250 veces más alto que
  el publicado. Placebo de población (días de 2026 sin P, 500 réplicas): el p por día da ≤ 0,01 en 0 % para zona, unión
  y anillo (el nulo por día no es trivialmente permisivo); control positivo de que el instrumento no está pegado al
  piso: S23a da 0,020.
- CÓMO SE VE EN EL VEREDICTO: no cambia ninguno; cambia la lectura de S23a ("p25 = 8e-5" promete mucho más de lo que es:
  un día) y de S25a pN.
- CÓMO REPRODUCIRLO: `python -I f2_bloques.py` (`D:\goes_notas\s28\s28b\f2\bloques.json`, `bloques.log`): por ejemplo
  `S23a {... "p25_por_cuadro": 7.912e-05, ..., "p25_bloque_dias_2025": 0.02014899255037248, ...}`,
  `S25a {... "pN_bloque_dias_N_2026": 0.00199990000499975 ...}`.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 3.

### 206. S28a, MIXTO de día: el límite inferior que lo decide (1,0495) cae bajo 1 con una de cada nueve semillas
- ARCHIVO:LÍNEA: `s28a_vecinas\scripts\s28a_medir.py:277-292` (2.000 réplicas, semilla 0); criterio
  `s28a_vecinas\criterio_2026-11-25.md:100-103` y tabla de §5.
- QUÉ PASA: MIXTO de día exige Antuco con límite inferior del IC95 de R > 1. Con la semilla 0 da 1,04952 (reproducido
  exacto). Con las semillas 0 a 199, el límite inferior va de 0,968 a 1,131 y queda ≤ 1 en **11 %** de ellas: entonces
  ninguna vecina cumple "R ≥ 1,5 y límite inferior > 1" y el día sería NO CONCLUYENTE. El error de Monte Carlo del
  percentil 2,5 es del orden de la distancia al umbral.
- CÓMO SE VE EN EL VEREDICTO: con la semilla fijada en el criterio, MIXTO se mantiene; su lectura es "en el borde",
  no "Antuco sube". No cambia el veredicto, cambia su lectura. La noche (NO CONCLUYENTE) no depende de la semilla.
- CÓMO REPRODUCIRLO: `python -I f2_s28a_semillas.py` → `antuco dia {"2025": [97, 2410], "2026": [156, 1467], "R":
  2.64204, "IC_semilla0": [1.04952, 8.98006], ..., "lo_min": 0.9678, "lo_max": 1.1308, "frac_semillas_lo_menor_que_1":
  0.11}` (`D:\goes_notas\s28\s28b\f2\s28a_semillas.json`). Ojo: hay que remuestrear los 62 y 65 días de la ventana,
  también los sin evaluados, como hace s28a; con sólo los días con filas en el CSV el IC no reproduce.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 3.

### 207. S23a: la etiqueta SEPARA VOLCAT salió de un pN exactamente 0 (azar estimado 0 en las horas de los P)
- ARCHIVO:LÍNEA: `s23_fondo_2025\scripts\s23_medir.py:419` (rN por hora con los N) y `:422` (pN Poisson binomial con
  rN); `s23_fondo_2025\resultados\s23a_resultado.json` (`EN_2026: 0.0`, `pN: 0.0`).
- QUÉ PASA: con rN(h) = 0 en todas las horas de los P (los N de la tarde casi no se evalúan con la costumbre de 2025:
  29, 34, 7 y 51 N evaluados en las franjas de 12 a 24 UTC), la cola es 0 por construcción, no por evidencia. Rehecho
  como lo harían S23b, S25a y S26a (Fisher contra N a ±60 min): 0 de 156 N alcanzados, p = 1,9e-7; por día, piso.
- CÓMO SE VE EN EL VEREDICTO: la etiqueta SEPARA VOLCAT se mantiene con la prueba bien hecha; el INFORME ya dice
  "pN = 0 (degenerado ...)" y S23b §4 cambió el método. No cambia.
- CÓMO REPRODUCIRLO: leer el json; `python -I f2_bloques.py` → `S23a {... "pN_por_cuadro_fisher": 1.9189e-07,
  "N_cerca": [0, 156], ... "pN_bloque_dias_N_2026": 4.9997e-05}`; `python -I f2_cobertura.py` para los N evaluados.
- CONFIANZA: CONFIRMADO. Línea base roja 2.
- GRAVEDAD: 2 (ya rotulado).

### 208. Las clases de VOLCAT no cubren la ventana "21-09 a 24-11" que dicen los criterios; el nublado de costumbre congelado de 2026 sale de 31 días, no de 62
- ARCHIVO:LÍNEA: `s23_fondo_2025\criterio_S23b_2026-11-25.md:28-29` ("cuadros N ... del 21-09 al 21-11-2026");
  `s25a_crater\criterio_2026-11-25.md:11` y `:70`; `s25a_crater\criterio_confirmacion_2026-11-25.md:4`;
  `s26a_combinado\criterio_2026-11-25.md:69` y `:73`. Código: `s22b_pluma_vs_nubes\scripts\s22b_medir.py:154`
  (clases de `frames_calor.csv` y del CSV de 22-24-11) y `:182` (`DEV` = días con clase);
  `s23_fondo_2025\scripts\s23_sensibilidad.py:25-26` (`estat_2026` = `Detector(ref="2026N").ESTAT`).
- QUÉ PASA: `frames_calor.csv` cubre del 20-10 al 19-11 (31 días, 4.116 cuadros, 53 a 144 por día) y
  `volcat_clases_22a24nov.csv` del 22 al 24-11 (0 P). Del 21-09 al 19-10 y el 20 y 21-11 no hay clase. Los 100 P son de
  10 días entre el 22-10 y el 14-11. La costumbre de 2026 congelada (`estat_2026.npy`) usa los N despejados de esos 31
  días, no del 21-09 al 21-11. Las cifras (100 P, 3.863 N) sí están bien.
- CÓMO SE VE EN EL VEREDICTO: ninguno cambia; la descripción del estado congelado de S23b no es la del archivo cuyo hash
  se congela (el hash manda, la frase no). Documentación que no calza.
- CÓMO REPRODUCIRLO: conteo por día de los dos CSV (comando de esta sesión: `dias 31 2026-10-20 2026-11-19`, `faltan
  []`, `P por dia {'2026-10-22': 1, ..., '2026-11-14': 33}`; `dias 3 2026-11-22 2026-11-24`, `P por dia {}`).
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 2 (toca la descripción de un estado congelado: pasa al verificador).

### 209. El criterio S23a define mal P: "ceniza dibujada a 50 km o menos en ±60 min"; la regla H9 que se usa es "objeto anclado en ese mismo cuadro"
- ARCHIVO:LÍNEA: `s23_fondo_2025\criterio_2026-11-24.md:70`; código `calor_rayos\scripts\analisis_calor.py:61-62`
  (`es_pos`: barra leída, objeto anclado, sin manto) y `:65-73` (el ±60 min sólo entra en `limpio`, que define N);
  igual en `s22b_pluma_vs_nubes\scripts\s22b_volcat_clases.py:77-91`.
- QUÉ PASA: P es el cuadro con un objeto que toca el disco de 10 km del cráter (4 a 500 píxeles); el ±60 min y los 50 km
  definen N (nada a 50 km en el cuadro ni en los guardados a ±60 min). Por eso un N nunca está a menos de 70 min de un
  P del mismo día.
- CÓMO SE VE EN EL VEREDICTO: ninguno; la frase del criterio describe otra población de P (más ancha) que la medida.
- CÓMO REPRODUCIRLO: leer las líneas citadas.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 2.

### 210. Cobertura: 2026 se evalúa la mitad que 2025, y en 2026 los cuadros con algo de nube disparan más que los despejados (en 2025 al revés)
- SCRIPT:SALIDA: `f2_cobertura.py` y la comparación de cielo de esta sesión (sobre `cubos_f2.npz`).
- QUÉ PASA: fracción de cuadros con ACM que pasan la compuerta: 2025 0,617, 2026 0,348 (E1 despejado: 0,528 contra
  0,254). Zona, cuadros evaluados por franja: 2025 0,59 a 0,67, 2026 0,27 a 0,42. P y N de 2026 sí son parejos en cielo
  (E1 en evaluados 0,81 y 0,78; nube dinámica mediana 0,059 los dos), así que pN compara poblaciones comparables. Pero P
  se evalúa 93 % y N 43 % (18 a 20 UTC: 42 de 42 contra 91 de 386). Y en la zona de 2026, los cuadros evaluados no
  despejados por E1 disparan 22,5 % contra 15,6 % los despejados; en 2025, 2,4 % contra 3,3 %.
- CÓMO SE VE EN EL VEREDICTO: no cambia ninguno. La segunda parte es una SOSPECHA física (dentro de la zona no se borra
  nada por ACM, `s25a_crater\criterio_2026-11-25.md` §2.4): parte del exceso de 2026 podría ser nube parcial sobre la
  cumbre. Seguimiento para F4.
- CÓMO REPRODUCIRLO: `python -I f2_cobertura.py` (`D:\goes_notas\s28\s28b\f2\cobertura.json`); la tasa por cielo con
  el bloque de esta sesión sobre `FD26_est26`, `E1_26`, `ev26_z500`, `F26_z500` de `cubos_f2.npz`
  (`z500 2026 ... tasa F eval E1 0.1558 tasa F eval noE1 0.2252`; `z500 2025 ... 0.0334 ... 0.024`).
- CONFIANZA: CONFIRMADO (cifras); SOSPECHA (la causa).
- GRAVEDAD: 3.

### 211. El poder se declara pero ningún veredicto de confirmación lo usa; el de la unión a p* no se midió
- ARCHIVO:LÍNEA: `s23_fondo_2025\criterio_S23b_2026-11-25.md:61`, `s25a_crater\criterio_confirmacion_2026-11-25.md:28`,
  `s26a_combinado\criterio_2026-11-25.md:64-65` y `:122` (NO CONFIRMA: p25 > 0,01, sin rama SIN PODER).
- QUÉ PASA: el poder a 0,33 K es 0,01 (anillo) y 0,14 (zona); el de la unión a 4,75 no se calculó ("a p* < 5 es
  menor"). S23a sí distinguía NO LLEGA de SIN PODER (`s23_medir.py:451-452`); las confirmaciones no: un NO CONFIRMA no
  separa "no hay señal" de "el detector no ve plumas de 0,33 K".
- CÓMO SE VE EN EL VEREDICTO: ninguno cambia hoy; un NO CONFIRMA futuro se leería más fuerte de lo que es. SIN DATO.
- CONFIANZA: CONFIRMADO (lectura de los criterios).
- GRAVEDAD: 2 (toca confirmaciones congeladas: pasa al verificador).

### 212. Fuga del día evaluado al nublado de costumbre del ensayo en seco: existe, pero mueve un disparo y p* no cambia
- ARCHIVO:LÍNEA: `s22b_pluma_vs_nubes\scripts\s22b_medir.py:187-198`, `s23_fondo_2025\scripts\s23_medir.py:141-156`,
  `s25a_crater\scripts\s25a_medir.py:254-255`: la costumbre de 2025 se calcula una vez con los 62 días, incluido el que
  se evalúa; los criterios sólo prometen sacar el día de la base y del umbral (`s23_fondo_2025\criterio_2026-11-24.md`
  §2, último párrafo), así que el código cumple su criterio.
- QUÉ PASA: rehecho con la costumbre sin el día (primer orden: S del día evaluado; base y umbral los de la regla):
  unión a 5: 284 contra 283 disparos (0,05165 contra 0,05146); a 4,75: 270 contra 269 (0,04910 contra 0,04892, sigue
  ≤ 0,05); a 4,5: idéntico. Anillo: 143 de 3.667 contra 143 de 3.668.
- CÓMO SE VE EN EL VEREDICTO: p* sigue en 4,75 (margen 0,0009 contra el tope). No cambia.
- CÓMO REPRODUCIRLO: `python -I f2_fuga_costumbre.py` (9 min; `D:\goes_notas\s28\s28b\f2\fuga_costumbre.json`).
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 1.

### 213. Fuga de segunda mano a través de la base de los otros días (zona)
- ARCHIVO:LÍNEA: `s25a_crater\scripts\s25a_medir.py:267-269`: el umbral del día d es el percentil de S de los otros
  días, y el S de cada otro día d'' usa una base sin d'' pero CON d.
- QUÉ PASA: rehecho con el día fuera de verdad (la base de cada d'' sin {d, d''}, 62 × 61 bases). Control: con la
  base de la regla da 176 de 5.499 a percentil 5 (el publicado). Con el día fuera: a 5, 176 (media por día 0,02589
  contra 0,02586); a 4,75, 161 contra 164; a 4,5, 153 igual. El efecto es de pocos disparos y va hacia menos.
- CÓMO SE VE EN EL VEREDICTO: el seco de la zona no cambia de lado de 0,05; p* de la unión no se mueve por la zona. No
  cambia. La del anillo no la medí (SIN DATO).
- CÓMO REPRODUCIRLO: `python -I f2_fuga_base_zona.py` (6,5 min; `D:\goes_notas\s28\s28b\f2\fuga_base_zona.json`).
- CONFIANZA: CONFIRMADO (zona).
- GRAVEDAD: 1.

### 214. S28a: el remuestreo descarta las réplicas sin disparos en 2025
- ARCHIVO:LÍNEA: `s28a_vecinas\scripts\s28a_medir.py:288` (`if a[1] and b[1] and a[0]:`).
- QUÉ PASA: una réplica cuyo 2025 no tiene disparos (R infinito) se descarta en vez de contarse como R grande: el
  percentil 97,5 queda sesgado hacia abajo. Pasa en partes, no en la unión (`replicas_validas` 1.987 a 1.999 en Longaví
  anillo día, zona noche; 2.000 en todas las uniones).
- CÓMO SE VE EN EL VEREDICTO: ninguno (el veredicto usa la unión).
- CONFIANZA: CONFIRMADO (código y json).
- GRAVEDAD: 1.

### 215. S25b, versión S23a: la falsa alarma de 2024 habla casi sólo de la noche
- ARCHIVO:LÍNEA: `s25b_fondo_2024\resultados\s25b_resultado.json` (`b.S23a.por_franja_2024`).
- QUÉ PASA: con la costumbre de 2025, en 2024 se evalúan 106, 65 y 86 cuadros de 12 a 21 UTC (2025: 363, 355, 365), y
  957 de 1.667 son de 00 a 12 UTC. FA24 = 0,016 de S23a es sobre todo nocturna; la versión S23b (la que cuenta para la
  confirmación, criterio §5) sí está repartida (236 a 344 por franja).
- CÓMO SE VE EN EL VEREDICTO: AGUANTA no cambia; con remuestreo de días el IC95 de FA24 es 0,002 a 0,038 (S23a) y
  0,004 a 0,031 (S23b): lejos de 0,05.
- CÓMO REPRODUCIRLO: `python -I f2_s25b_dias.py` y `f2_cobertura.py` (bloque 2024).
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 1.

## VERIFICADO LIMPIO (con su vara)

- **Mismo número de oportunidades (vara: §3b fila 12).** P, N y el azar de 2025 usan la misma función
  `s22b_medir.alcanzado` (`s22b_medir.py:301-302`: F en el cuadro, el anterior o el siguiente, sin cruzar la
  medianoche), sobre cuadros evaluados con la misma regla de evaluado y la misma persistencia que cruza la medianoche:
  `s23_medir.py:338` y `:413`, `s25a_medir.py:280` y `:332`, `s26a_medir.py:149` y `:175`. Mismos bordes de día en los
  dos años (el primer cuadro de la ventana no puede disparar en ninguno). La compuerta difiere por año a propósito y por
  criterio (costumbre de cada año). Lo comprobé reproduciendo los p25 publicados desde los arreglos propios de
  `f2_cubos.py` (que llaman a esas funciones) y leyendo que r25 se arma con el alcanzado y no con F.
- **Régimen (vara: §3b fila 10).** `f2_regimen.py` sobre los nombres NOAA guardados en cada npz: 2025 todo G19, 2024
  todo G16, 2026 (cachés H23, H24 y 22-24-11) todo G19; modo M6 salvo un cuadro M4 cada dos semanas (2025: 30-09,
  13-10, 27-10, 11-11; 2024: 30-09, 14-10, 28-10, 11-11; 2026: 12-10, 26-10, 09-11, 23-11), un cuadro de 144 en esos
  días. El ACM es ABI-L2-ACMF del mismo satélite en todo el tramo. No hay cambio de satélite ni de modo dentro de una
  ventana.
- **S26b, EL CALOR NO EXPLICA con la noche como unidad (vara: la regla E3 (i) p ≤ 0,01).** Permutación de etiquetas de
  año entre noches (20.000): p en el piso (5e-5) para noches bajo el límite (11 noches, tasa 0,345) y para la época
  21-09 a 11-10; Mann-Whitney de tasas por noche 2,2e-5 y 4,8e-8. Totales reproducidos (107/310, 118/303, 94/2.562).
  El rótulo aguanta; el p de 2e-56 era de cuadros.
- **S25b AGUANTA (vara: FA24 ≤ 0,05 de su criterio).** IC95 por días bajo 0,04 en las dos versiones (ID 215).
- **Pisos (vara: 1/(n+1) contra cada umbral del criterio).** S28a no tiene p (sólo IC con 2.000 réplicas); S27a
  nulo 2 (57 corrimientos, piso 0,0172) contra 0,05: alcanzable. Mis propios nulos por día tienen piso 5e-5.
- **p* de S26a.** Elegido sólo con 2025 (`s26a_medir.py:215-225`), y no se mueve con la fuga de costumbre (ID 212).
- **Selección de los P de S23b, S25a y S26a en la medida decisiva**: las clases que entran son las de los dos CSV, con
  la regla H9 del código; los conteos 100 P y 3.863 N coinciden con los criterios (sólo la ventana escrita no, ID 208).
- **Ensayo en seco "sin el día" para base y umbral**: el código saca el día de la base (`s23_medir.py:208`,
  `s25a_medir.py:155-157`) y del umbral (`s23_medir.py:224`, `s25a_medir.py:208-210`), como dicen los criterios.

## SIN DATO

- **Fuga de segunda mano del anillo** (la base de los otros días incluye el día evaluado, como ID 213 para la zona): no
  la medí; rehacer 62 × 61 bases del anillo pesa horas. Si la de la zona es despreciable, es razonable esperar lo mismo,
  pero no está medido.
- **pN de las confirmaciones con dependencia**: no se puede simular sin días nuevos (los N serían de los mismos 2 días).
- **Versión del algoritmo ACMF**: los npz guardan sólo el nombre del archivo, no el atributo de versión del NetCDF.
- **S24 y S27b**: S24 declara sus veredictos descriptivos y no independientes (criterio :83-84); S27b no tiene p ni
  nulo por permutación. No recomputé nada de los dos.
- **Poder de la unión a p* = 4,75**: no medido por S26a ni por mí.
