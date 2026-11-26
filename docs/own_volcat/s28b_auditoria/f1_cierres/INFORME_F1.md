# S28b, frente F1: cierres y pre-registro. Informe del auditor, 26-11-2026

**Un hallazgo (102) cambia un veredicto si se corrige un defecto de diseño del criterio: el B1 de S24 pasa de NO
EPISÓDICO a EPISÓDICO (p de 0,0003 a 0,057) al aplicar la misma selección de "noches comunes" a los dos años. Ningún
rótulo cambia aplicando la regla tal como está escrita: los 19 rótulos recalculados por `f1_reglas_censo.py`, las 16 bandas y el B1 de S24 coinciden. Cuatro hallazgos (101, 102, 103,
104) cambian la lectura de un veredicto.**

- Auditor F1 (IDs 101 a 199). Modelo Opus 5.5, esfuerzo del encargo. Base auditada `origin/main` 8894722. Vara:
  `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\Goes\.claude\worktrees\s28b-auditoria-s23-s28a-c1cff8\docs\own_volcat\s28b_auditoria\PLAN.md`
  (commit 002feff), §3 (definiciones, tolerancias, gravedad).
- Instrumento (va al repo), en
  `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\Goes\.claude\worktrees\s28b-auditoria-s23-s28a-c1cff8\docs\own_volcat\s28b_auditoria\f1_cierres\scripts\`:
  - `f1_s24_reglas.py`: la regla escrita del criterio de S24 aplicada a las filas por cuadro del JSON (línea base roja).
  - `f1_preregistro.py`: orden criterio, medida y empuje por medida (git log, git diff y el reflog `update by push` de
    las ramas remotas, que queda en el `.git` compartido por los worktrees).
  - `f1_reglas_censo.py`: reaplica la regla de cada criterio (copiada del texto del criterio, no del código de la
    sesión) a las cifras de `resultados/*.json` y compara con el rótulo guardado.
  - `f1_s24_comunes_simetrico.py`: recalcula la comparación B1 de S24 con la misma selección en los dos años, con el
    código de S24 sin cambios y sólo días hasta el 24-11-2026.
- Salidas crudas en `D:\goes_notas\s28\s28b\f1\` (`s24_reglas.txt`, `preregistro.txt`, `reglas_censo.txt`,
  `s24_comunes_simetrico.json` y su `.log`).
- No corrí ningún detector sobre días posteriores al 24-11-2026, ni `s23b_confirmar.py`, ni modifiqué nada fuera de
  esta carpeta y de `D:\goes_notas\s28\s28b\f1\`. D: con 25 GB libres al cerrar.

## 1. Línea base roja (S24, control positivo A)

Leí primero
`C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\Goes\.claude\worktrees\s28b-auditoria-s23-s28a-c1cff8\docs\own_volcat\s24_dia14_noche\criterio_2026-11-25.md`
(§2: "Si el 08-11 no da SEÑAL en todo el anillo, la medida no sirve: INVÁLIDA"; SEÑAL si mediana de q ≤ 0,05 y la mitad
con q ≤ 0,10, mínimo 5 cuadros) y `resultados/s24_resultado.json`, sin abrir el INFORME. `f1_s24_reglas.py` recalcula
cada banda desde los q por cuadro. Salida (`D:\goes_notas\s28\s28b\f1\s24_reglas.txt`):

```
huella anillo    recomputado SIN SENAL n=11 med=0.2488  | json SIN SEÑAL n=11 med=0.2488
CONTROL POSITIVO 08-11 todo el anillo: SIN SENAL -> A INVALIDA | json A_valida = False
```

**El instrumento encontró solo que A es INVÁLIDA.** No es ciego. La misma corrida reproduce las 16 bandas (14-11 y
08-11, huella y giro) y el B1 (top 5 = 66 de 78 = 0,8462; Fisher 0,00032; NO EPISÓDICO).

## 2. Censo de veredictos (una fila por rótulo, también los limpios)

Columnas: (a) criterio commiteado y empujado antes del commit y del empuje de la medida, y `git diff` del criterio entre
su commit y el de la medida vacío o con enmienda rotulada previa; (b) el código hace lo que el criterio escribe;
(c) las cifras del INFORME y de STATUS salen del JSON dentro de la tolerancia del plan; (d) el nombre no promete más que
la regla; (e) lo post hoc rotulado. "ok" = lo comprobé y está sano; el número remite al hallazgo.

Orden temporal (salida de `f1_preregistro.py`; hora local −03, empuje desde el reflog):

| Medida | Criterio: commit y empuje | Resultado: commit y empuje | diff del criterio hasta la medida | diff hasta la base |
|---|---|---|---|---|
| S23a | 1594187, 24-11 17:02:25, empuje 17:02:28 | 97bdec1, 25-11 02:53:15, empuje 02:53:18 | vacío | vacío |
| S23b candidata | 97bdec1 (el mismo commit que el resultado post hoc) | 97bdec1 | vacío | +6 líneas (§6, af46f12, 02:53:44, antes de bajar días nuevos) |
| S24 A y B | 5c83319, 25-11 07:43:09, empuje 07:43:12 | 6024f12, 07:50:53, empuje 07:50:55 | vacío | vacío |
| S24c | d11eab8, 07:51:35, empuje 07:51:38 | 979216c, 08:00:03, empuje 08:00:07 | vacío | vacío |
| S25a | 1306fb5, 09:08:34, empuje 09:08:37 | 08ba80a, 09:16:16, empuje 09:16:21 | vacío | vacío |
| S25b | b07cb58, 09:26:58, empuje 09:27:28 | 0ba961d, 18:00:31, empuje 18:00:34 | vacío | vacío |
| S26a | 28f963b, 12:02:18, empuje 12:02:23 | 5a35ea4, 12:12:41, empuje 12:12:45 | vacío | vacío |
| S26b | 2643ab0, 12:07:31, empuje 12:07:35 | 924d940, 12:45:46, empuje 12:46:26 | vacío | vacío |
| S27a | 2c7af2b, 14:22:32, empuje 14:22:44 | fa8bdd8, 14:44:46, empuje 14:44:49 | +9 líneas: enmienda 1 (85856a4, 14:29:42, empuje 14:29:46), rotulada "antes de medir" | igual |
| S27b | adace39, 14:25:26, empuje 14:26:17 | 1e4cf0b, 14:33:12, empuje 14:33:15 | vacío | vacío |
| S28a | 39da17b, 16:00:42, empuje 16:00:45 | 537f3b9, 17:52:11, empuje 17:52:15 | vacío | vacío |

En todos, fecha de autor igual a fecha de commit. Como segunda vara, independiente de git, comparé los mtimes de los
cachés de D: con la hora del criterio: S23a `r25_*.npy` 25-11 02:26 (criterio 24-11 17:02); S25a `r25_btd.npy`
09:12:21 (criterio 09:08:34); S26a `medir.log` 12:12:23 (12:02:18); S26b `bajar.log` 12:08:52, `noches_*.csv`
12:44:31 (12:07:31); S27a `viento_*.log` 14:34 y `medir.log` 14:40:44 (enmienda 14:29:42); S28a `m1_*.npy` 16:04 a
16:08 y `medir.log` 17:48:54 (16:00:42); S25b `cubo` 17:44:31 (09:26:58). Ningún caché de medida es anterior a su
criterio.

| # | Sesión | Rótulo (archivo) | (a) | (b) | (c) | (d) | (e) | Regla del criterio sobre el JSON |
|---|---|---|---|---|---|---|---|---|
| 1 | S23a | Instrumento I1 a I4 "pasa" (`instrumento_2025.json`) | ok | ok | ok | ok | n/a | cobertura 0,998 y 0,986; I4 0,985 |
| 2 | S23a | Ensayo en seco "aprobado" 0,0428 (`seco.json`) | ok | ok | ok | ok | n/a | ≤ 0,05 |
| 3 | S23a | Poder 0,01 y 0,585 (`poder.json`) | ok | ok | ok | ok | n/a | informativo |
| 4 | S23a | **PARCIAL** (`s23a_resultado.json`) | ok | ok | ok | ok | ok | PARCIAL, coincide |
| 5 | S23a | Etiqueta SEPARA VOLCAT | ok | ok | ok | seguimiento F2 | ok | coincide; EN_2026 = 0, pN = 0 (cola degenerada; el INFORME la rotula "débil") |
| 6 | S23 | Diagnóstico post hoc (`diagnostico_posthoc.json`) | n/a | ok | 109 | ok | ok | |
| 7 | S23 | **S23b candidata** 25 de 54 (`sensibilidad_costumbre_2026.json`) | post hoc, rotulado | ok | 106 | ok | ok | |
| 8 | S24 | **A INVÁLIDA** (control positivo) | ok | ok | ok | ok | n/a | INVÁLIDA, coincide (línea base roja) |
| 9 | S24 | A, bandas del 14-11 y del giro | ok | ok | ok | ok | ok | 16 de 16 coinciden |
| 10 | S24 | B1 **NO EPISÓDICO** | ok | ok | ok | 102 (simétrico: EPISÓDICO) | n/a | coincide |
| 11 | S24 | B2 ASOCIADO (acm1, contraste) | ok | ok | ok | 102 | n/a | p ≤ 0,01; cuadros dependientes (F2) |
| 12 | S24 | B3 (descriptivo) | ok | ok | ok | ok | n/a | |
| 13 | S24 | Post hoc "once cuadros seguidos al SE" (INFORME §1) | n/a | n/a | 105 | ok | ok | |
| 14 | S24c | **Abandonada** (`s24c_calibracion.json`) | ok | ok | ok | ok | n/a | ningún P_B con seco ≤ 0,05 (0,0562 el mejor) |
| 15 | S25a | Instrumento "pasa" | ok | ok | ok | ok | n/a | |
| 16 | S25a | Ensayo en seco 0,032 "pasa" | ok | ok | ok | ok | n/a | ≤ 0,05 |
| 17 | S25a | **ALCANZA** | ok | ok | ok | 103 | ok | ALCANZA, coincide |
| 18 | S25a | **14-11 ALCANZADO** | ok | ok | ok | 103 | ok | coincide |
| 19 | S25a | Post hoc día y noche, sin cada día | n/a | ok | 108, 112 | ok | ok | |
| 20 | S25b | (a) **COMPARABLE** | ok | ok | ok | ok | n/a | coincide |
| 21 | S25b | (b) S23a **AGUANTA**, MÁS ESTRICTO | ok | ok | 107 | ok | n/a | coincide |
| 22 | S25b | (b) S23b **AGUANTA**, MÁS ESTRICTO | ok | ok | 107 | ok | n/a | coincide |
| 23 | S25b | (c) **INTERMEDIO** | ok | ok | ok | ok | n/a | mediana 0,0975, máximo 0,2546: coincide |
| 24 | S25b | Post hoc azar 2024 | n/a | ok | ok | ok | ok | |
| 25 | S26a | Comprobación de código a percentil 5 | ok | ok | ok | ok | n/a | |
| 26 | S26a | Seco percentil 5 "no pasa"; **p* = 4,75** | ok | ok | ok | ok | n/a | 283 y 269 de 5.499; p* coincide |
| 27 | S26a | **ALCANZA (desarrollo)** 63 de 93 | ok | ok | ok | ok | ok | coincide |
| 28 | S26b | Reproducción | ok | ok | ok | ok | n/a | |
| 29 | S26b | E1, E2 sin asociación; E3 exceso; E5 sin huella | ok | ok | ok | ok | ok | |
| 30 | S26b | **EL CALOR NO EXPLICA** | ok | ok | ok | ok | ok | coincide |
| 31 | S27a | P **SIN PODER** | ok (enmienda previa) | ok | ok | seguimiento F2 | ok | coincide; piso 1/61 = 0,0164 > 0,01 |
| 32 | S27a | P "PLUMA NO" a 0,05 | n/a | n/a | ok | ok | ok (rotulado post hoc) | |
| 33 | S27a | N **NO DECIDIBLE** | ok | ok | ok | ok | n/a | coincide |
| 34 | S27a | D **DEPÓSITO NO** | ok | ok | ok | ok | n/a | coincide |
| 35 | S27b | Emparejamiento cambiado al ver el listado de pares | rotulado en el criterio §2.4 | ok | ok | ok | ok | |
| 36 | S27b | Prueba que decide **NO DECIDIBLE**; conjunto NO DECIDIBLE | ok | ok | ok | 113 | ok | coincide |
| 37 | S28a | Comprobación de código (con la corrección de `base` después de la primera corrida) | ok | ok | ok | ok | ok (dicho en el INFORME §2) | |
| 38 | S28a | Noche **NO CONCLUYENTE** | ok | ok | ok | ok | n/a | coincide |
| 39 | S28a | Día **MIXTO (sube Antuco)** | ok | ok | ok | 101, 114 | 104 | coincide |
| 40 | STATUS | Bloques 0, 0-prev19 a 0-prev27 | | | 101, 102, 104, 105, 106, 107, 108, 114, 116 | | | |

## 3. Hallazgos (lo peor primero)

### 101. S28a: el MIXTO de día se lee como si fuera NO SE SOSTIENE

- ARCHIVO:LÍNEA:
  `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\Goes\.claude\worktrees\s28b-auditoria-s23-s28a-c1cff8\docs\own_volcat\s28a_vecinas\criterio_2026-11-25.md:113-116`
  contra
  `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\Goes\.claude\worktrees\s28b-auditoria-s23-s28a-c1cff8\docs\own_volcat\s28a_vecinas\INFORME.md:9-11`
  y `:59-60`, y
  `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\Goes\.claude\worktrees\s28b-auditoria-s23-s28a-c1cff8\STATUS.md:81`,
  `:111-112`, `:122`.
- QUÉ PASA: el criterio fija qué quiere decir cada rótulo. MIXTO es "cambio local de una cumbre" (línea 115); la lectura
  "el exceso de Chillán no es sólo pluma" está reservada a **NO SE SOSTIENE** (línea 114, las dos vecinas suben). Salió
  MIXTO (Antuco R 2,64, IC 1,05 a 8,98; Longaví 0,80), y el INFORME titula con la lectura de NO SE SOSTIENE: "el exceso
  diurno de Chillán en 2026 no se puede atribuir sólo a la pluma" y "De día no hay exceso que se pueda atribuir sólo a la
  pluma"; STATUS lo sube a **CONFIRMADO:** "de día, en 2026, una cumbre sin pluma (Antuco) dispara tanto como Chillán".
  La lectura "tasa 2025 de Chillán × R de la vecina" sí está permitida (§5, "sólo como lectura"), pero el criterio no la
  convierte en conclusión con un MIXTO, y la otra vecina (Longaví, R 0,80) apunta al lado contrario.
- CÓMO SE VE EN EL VEREDICTO: no cambia el rótulo (MIXTO, recalculado por `f1_reglas_censo.py`); cambia su lectura.
  Lo que se le muestra a Nicolás como falsa alarma de S26a en 2026 de día pasa de "el 4,9 % de 2025 no vale; el exceso de
  Chillán cabe entero en lo que sube Antuco" a "una de dos cumbres sin pluma sube; no se sabe si es local o regional".
- CÓMO REPRODUCIRLO: `python -I <scripts>\f1_reglas_censo.py` da `S28a dia | MIXTO | MIXTO (sube antuco) | coincide`;
  leer las líneas citadas del criterio y del INFORME.
- CONFIANZA: CONFIRMADO (texto contra texto y rótulo recalculado).
- GRAVEDAD: 4 (lectura de un veredicto que decide qué falsa alarma se le muestra a Nicolás).

### 102. S24 B1: "2026 dispara diez veces más que una noche común de 2025" compara dos selecciones distintas

- ARCHIVO:LÍNEA:
  `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\Goes\.claude\worktrees\s28b-auditoria-s23-s28a-c1cff8\docs\own_volcat\s24_dia14_noche\criterio_2026-11-25.md:62-65`;
  `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\Goes\.claude\worktrees\s28b-auditoria-s23-s28a-c1cff8\docs\own_volcat\s24_dia14_noche\scripts\s24_medir.py:178-181`;
  `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\Goes\.claude\worktrees\s28b-auditoria-s23-s28a-c1cff8\docs\own_volcat\s24_dia14_noche\INFORME.md:8`, `:17-18`;
  `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\Goes\.claude\worktrees\s28b-auditoria-s23-s28a-c1cff8\STATUS.md:501`, `:523`.
- QUÉ PASA: la regla B1 compara la tasa nocturna de 2025 **sin** las noches con 3 disparos o más (una selección por el
  propio resultado, que baja la tasa por construcción) contra la tasa de **todo** 2026, que sí conserva su noche con 6
  disparos (29-10). El código hace exactamente lo escrito; el defecto es de diseño. El titular ("diez veces más",
  "CONFIRMADO: ... 2026 dispara más que una noche común de 2025") sale de esa comparación asimétrica. Además STATUS
  rotula "Era artefacto" y CONFIRMADO un resultado cuyo rótulo por la regla es NO EPISÓDICO.
- CÓMO SE VE EN EL VEREDICTO: **cambia, con el diseño corregido.** Recalculado con el código de S24 sin cambios y la misma
  selección en los dos años (2026 sin su única noche con 3 disparos o más, el 29-10, 6 de 49): 2025 comunes 2 de 1.409,
  2026 comunes 6 de 809; razón 5,2 (no 9,9); Fisher bilateral p = 0,057 > 0,05. Con top 5 = 0,846 ≥ 0,60, la regla de B1
  da **EPISÓDICO**, no NO EPISÓDICO. Por la regla tal como está escrita el rótulo no cambia (el código reproduce el p
  0,00032 del JSON). Lo que cae es el titular "2026 dispara diez veces más que una noche común de 2025" y el CONFIRMADO de
  STATUS: con las dos selecciones iguales la diferencia no alcanza el umbral que la propia regla fijó.
- CÓMO REPRODUCIRLO: `python -I <scripts>\f1_s24_comunes_simetrico.py` (unos 8 min; usa sólo días hasta el 24-11, lo
  asegura un `assert`); salida en `D:\goes_notas\s28\s28b\f1\s24_comunes_simetrico.json`:
  `"p_S24_tal_cual_comunes25_vs_todo26": 0.00032`, `"p_simetrico_comunes25_vs_comunes26": 0.0574`,
  `"razon_simetrica": 5.22`, `"noches_2026_excluidas": {"2026-10-29": [6, 49]}`.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 4 (cambia un veredicto de diagnóstico y una lectura que pasó a STATUS y a la memoria del
  proyecto: "la noche de 2026 dispara 10 veces más"; no decide lo que se muestra a Nicolás).

### 103. S25a: ALCANZA sin rótulo de desarrollo, con la zona elegida donde VOLCAT dibujó el 14-11

- ARCHIVO:LÍNEA:
  `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\Goes\.claude\worktrees\s28b-auditoria-s23-s28a-c1cff8\docs\own_volcat\s25a_crater\criterio_2026-11-25.md:8-11`, `:102-104`;
  `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\Goes\.claude\worktrees\s28b-auditoria-s23-s28a-c1cff8\docs\own_volcat\s25a_crater\INFORME.md:8`, `:44`;
  contra
  `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\Goes\.claude\worktrees\s28b-auditoria-s23-s28a-c1cff8\docs\own_volcat\s26a_combinado\criterio_2026-11-25.md:69-70`.
- QUÉ PASA: la zona de 0 a 4 km se eligió porque ahí cae la mitad de la huella de VOLCAT del 14-11 (S24), y el 14-11
  son 31 de los 93 P evaluados. El criterio lo dice (§0 y §5) y sube el umbral de p25 a 0,01. Pero el rótulo queda
  "ALCANZA" y "14-11 ALCANZADO", y el INFORME lo vende como "la primera vez que una regla propia, con criterio previo,
  alcanza el 14-11". S26a, con la misma situación (los P ya mirados y la regla armada por lo visto), se rotula
  "(desarrollo)". El 14-11 ALCANZADO prueba un día que eligió la región.
- CÓMO SE VE EN EL VEREDICTO: no cambia el rótulo por la regla; cambia su lectura: S25a es desarrollo como S26a y su
  confirmación congelada en días nuevos es la única prueba. No toca la confirmación.
- CÓMO REPRODUCIRLO: leer las líneas citadas; `s25a_resultado.json` `dia_14_11` = 31 evaluados, 20 alcanzados.
- CONFIANZA: CONFIRMADO (texto).
- GRAVEDAD: 3.

### 104. S28a post hoc: el 10-11 las cumbres no disparan "a la vez" que los aciertos de Chillán

- ARCHIVO:LÍNEA:
  `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\Goes\.claude\worktrees\s28b-auditoria-s23-s28a-c1cff8\docs\own_volcat\s28a_vecinas\INFORME.md:46-53`;
  `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\Goes\.claude\worktrees\s28b-auditoria-s23-s28a-c1cff8\STATUS.md:105`, `:126`.
- QUÉ PASA: el INFORME dice que el 10-11 "disparan las tres cumbres a la vez por la tarde: Chillán (los 12 cuadros de
  VOLCAT de 15:00 a 23:20), Antuco (33 cuadros de 13:50 a 20:40) y Longaví (24 cuadros de 16:00 a 19:50)" y que una parte
  de los aciertos de la zona de Chillán esos días "puede ser regional". Los 8 aciertos de la zona el 10-11 son los P de
  21:30 a 23:20 (`s25a_P_por_cuadro.csv`); a esa hora Antuco y Longaví están evaluadas y ya no disparan (último disparo
  20:40 y 19:50). Lo que coincide con Antuco es la zona de Chillán disparando de 15:40 a 20:10 en cuadros que no son P.
  El placebo del propio S28a lo muestra: Antuco alcanza 1 de los P del 10-11 (`s28a_posthoc.json`). El 14-11 sí
  coincide (Antuco alcanza 11 P ese día).
- CÓMO SE VE EN EL VEREDICTO: no cambia ningún rótulo (es post hoc y está rotulado); debilita la SOSPECHA de STATUS
  (`:126`) para el 10-11 y la razón de la decisión 1 a Nicolás (`:105`).
- CÓMO REPRODUCIRLO: `grep 2026-11-10 <s25a>\resultados\s25a_P_por_cuadro.csv` (F = 1 en 21:30, 21:40, 22:10, 22:50,
  23:00, 23:20); en `D:\goes_notas\s28\s28a\cuadros_antuco_2026.csv`, F_u = 1 del 10-11 entre 13:50 y 20:40, evaluado
  hasta 23:50; Longaví 16:00 a 19:50; `s28a_posthoc.json` `placebo_de_chillan.antuco.por_dia` = {"2026-11-10": 1, ...,
  "2026-11-14": 11}.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 3.

### 105. S24: "once cuadros seguidos" al SE con S "entre −0,49 y −0,68 K" no es lo que dice el JSON

- ARCHIVO:LÍNEA:
  `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\Goes\.claude\worktrees\s28b-auditoria-s23-s28a-c1cff8\docs\own_volcat\s24_dia14_noche\INFORME.md:35-37`;
  `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\Goes\.claude\worktrees\s28b-auditoria-s23-s28a-c1cff8\docs\own_volcat\s24_dia14_noche\criterio_S24c_2026-11-25.md:12`;
  `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\Goes\.claude\worktrees\s28b-auditoria-s23-s28a-c1cff8\STATUS.md:510`.
- QUÉ PASA: de 17:20 a 19:00 el JSON tiene 10 cuadros evaluados (18:30 no pasa la compuerta), todos en la tajada 4, con S
  de −0,6002, −0,539, −0,5071, −0,4854, −0,486, −0,5353, −0,6838, −0,5062, −0,3398 y −0,2629: el rango es −0,26 a
  −0,68 K, no −0,49 a −0,68 (ese rango vale sólo hasta 18:40). Fue la motivación de S24c (abandonada) y de la decisión 2
  a Nicolás ("el detector apunta al SE once cuadros seguidos").
- CÓMO SE VE EN EL VEREDICTO: no cambia (post hoc rotulado; S24c se abandonó por su calibración).
- CÓMO REPRODUCIRLO: imprimir `A_14-11.cuadros[*].{hora,S,k}` de `s24_resultado.json`.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 3.

### 106. S23: "todos los disparos caen hacia el SE (120° a 180°)" en la candidata S23b; "4 de 5 días"

- ARCHIVO:LÍNEA:
  `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\Goes\.claude\worktrees\s28b-auditoria-s23-s28a-c1cff8\docs\own_volcat\s23_fondo_2025\INFORME.md:10`, `:37`;
  `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\Goes\.claude\worktrees\s28b-auditoria-s23-s28a-c1cff8\docs\own_volcat\s23_fondo_2025\criterio_S23b_2026-11-25.md:22`;
  `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\Goes\.claude\worktrees\s28b-auditoria-s23-s28a-c1cff8\STATUS.md:559`.
- QUÉ PASA: en `sensibilidad_costumbre_2026.json` los disparos de los días con P suman 38; 34 caen en las tajadas 4 y 5
  (120° a 180°) y 4 fuera: uno en la tajada 2 (60° a 90°, 28-10) y tres en la 6 (180° a 210°: 25-10 y dos el 11-11;
  tajada k = [30k, 30k + 30), `s22a_medir.py:92`). Y "en 4 de 5 días" choca con el mismo JSON y con el criterio S23b
  (§1), que listan 7 días con P evaluado (alcanzados en 4).
- CÓMO SE VE EN EL VEREDICTO: no cambia (la candidata es post hoc); el rumbo "exclusivo" al SE es lo que S25b (§3)
  después relativiza con 14 de 41 falsas alarmas de 2024 al SE.
- CÓMO REPRODUCIRLO: imprimir `por_dia[*].tajadas` de `sensibilidad_costumbre_2026.json`.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 3.

### 107. S25b: "ninguna franja de 3 horas pasa del 5 %" y tasas de métricas distintas en una misma frase

- ARCHIVO:LÍNEA:
  `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\Goes\.claude\worktrees\s28b-auditoria-s23-s28a-c1cff8\docs\own_volcat\s25b_fondo_2024\INFORME.md:9-10`, `:33-35`;
  `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\Goes\.claude\worktrees\s28b-auditoria-s23-s28a-c1cff8\STATUS.md:23`, `:36`.
- QUÉ PASA: la versión S23a tiene la franja 09-11 UTC en 0,0515 (`s25b_resultado.json`, `b.S23a.por_franja_2024`), sobre
  el 5 % (la tabla del mismo INFORME dice bien "0,052"). Y "dispara en 1,5 a 1,6 % de los cuadros, un tercio de ... 4,3 %"
  mezcla la media por día (FA24 0,0147 y 0,0161; 2025 0,0428) con "de los cuadros": la tasa por cuadro de S23b es 0,0167.
- CÓMO SE VE EN EL VEREDICTO: no cambia (el tope de franja del criterio es 0,10; AGUANTA y MÁS ESTRICTO recalculados
  coinciden).
- CÓMO REPRODUCIRLO: `f1_reglas_censo.py` imprime `S25b S23a: franja máxima 2024 = 0.0515 (> 0,05)`.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 2.

### 108. S25a: "24 % de noche contra 4 %" compara ventanas distintas, y la cifra viaja a S26a, S26b y STATUS

- ARCHIVO:LÍNEA:
  `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\Goes\.claude\worktrees\s28b-auditoria-s23-s28a-c1cff8\docs\own_volcat\s25a_crater\INFORME.md:10`, `:35-36`;
  `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\Goes\.claude\worktrees\s28b-auditoria-s23-s28a-c1cff8\docs\own_volcat\s26a_combinado\criterio_2026-11-25.md:131`;
  `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\Goes\.claude\worktrees\s28b-auditoria-s23-s28a-c1cff8\docs\own_volcat\s26b_noche_crater\criterio_2026-11-25.md:16`;
  `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\Goes\.claude\worktrees\s28b-auditoria-s23-s28a-c1cff8\STATUS.md:442`.
- QUÉ PASA: el 24 % es `s25a_posthoc.json` `tasa_disparo_2026.noche_00_12` (00:00 a 11:50 UTC); el 4 % (4,3 %) es
  `s25a_resultado.json` `seco.noche_03_09_UTC` (03:00 a 08:50 UTC, 63 de 1.453). Con la misma ventana de 03:00 a 08:50 y
  el percentil 4,75, S27a da 175 de 961 (18,2 %) contra 60 de 1.453 (4,1 %).
- CÓMO SE VE EN EL VEREDICTO: no cambia ninguno (es informativo); el exceso nocturno sigue grande (unas 4 veces) pero
  no "6 veces".
- CÓMO REPRODUCIRLO: claves citadas de los dos JSON; `s27a_resultado.json` `N.chillan_zona`.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 2.

### 109. S23, diagnóstico: tres cifras que no salen del JSON

- ARCHIVO:LÍNEA:
  `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\Goes\.claude\worktrees\s28b-auditoria-s23-s28a-c1cff8\docs\own_volcat\s23_fondo_2025\INFORME.md:41`, `:56`, `:62-64`.
- QUÉ PASA: (i) "30 evaluados, 10 fuera por la compuerta y 70 por tener menos de 9 tajadas" suma 110 de 100: los 10 de la
  compuerta están dentro de los 70 (los 70 no evaluados tienen todos menos de 9 tajadas; categorías que se solapan en
  `s23_diagnostico.py:87-89`). (ii) "0 de 2 a 23 cuadros N alrededor de cada P": el JSON da de 2 a 97 (los tres P
  nocturnos del 29-10 tienen 94 a 97 N alrededor). (iii) "Píxeles sin línea base de 2025: menos de 0,5 %": el máximo es
  0,6 %. Y "2026 dispara MENOS que 2025 de noche (0,5 % contra 4 %)": 5 de 853 = 0,59 %.
- CÓMO SE VE EN EL VEREDICTO: no cambia.
- CÓMO REPRODUCIRLO: contar `por_cuadro_P` y `N_2026_alrededor_de_P` de `diagnostico_posthoc.json`; sumar las franjas
  00 a 08 UTC de `s23a_resultado.json`.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 2.

### 112. S25a: "R va de 0,39 a 0,53" sacando cada día; el JSON y el §3 del mismo INFORME dicen 0,55

- ARCHIVO:LÍNEA:
  `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\Goes\.claude\worktrees\s28b-auditoria-s23-s28a-c1cff8\docs\own_volcat\s25a_crater\INFORME.md:33-34` contra `:72`.
- QUÉ PASA: sin el 08-11, R = 44 de 80 = 0,55 (`s25a_posthoc.json`, `sin_cada_dia`).
- CÓMO SE VE EN EL VEREDICTO: no cambia.
- CONFIANZA: CONFIRMADO. GRAVEDAD: 2.

### 113. S27b: el JSON rotula ACIERTA una llegada del 28-10 contra la sombra del 08-11

- ARCHIVO:LÍNEA:
  `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\Goes\.claude\worktrees\s28b-auditoria-s23-s28a-c1cff8\docs\own_volcat\s27b_altura_desfase\scripts\s27b_medir.py:192`;
  `resultados/s27b_resultado.json` `llegadas[1].veredicto_caso = "ACIERTA"`; criterio §3.7 y §5.
- QUÉ PASA: §3.7 define ACIERTA contra la sombra de 4,7 km, que es del 08-11; el 28-10 es informativo (§5) y no tiene
  verdad. El JSON le pone igual el rótulo. El INFORME (§2, "restringe por la regla, pero la precisión es falsa") lo lee
  bien.
- CÓMO SE VE EN EL VEREDICTO: no cambia (el conjunto es NO DECIDIBLE, recalculado).
- CONFIANZA: CONFIRMADO. GRAVEDAD: 2.

### 114. S28a STATUS: una sensibilidad que "no decide" queda como CONFIRMADO

- ARCHIVO:LÍNEA:
  `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\Goes\.claude\worktrees\s28b-auditoria-s23-s28a-c1cff8\STATUS.md:122-123`
  contra
  `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\Goes\.claude\worktrees\s28b-auditoria-s23-s28a-c1cff8\docs\own_volcat\s28a_vecinas\criterio_2026-11-25.md:122-128`.
- QUÉ PASA: "no es la pluma de Chillán llevada por el viento" sale de la sensibilidad de viento (§6, "no deciden"):
  Antuco de día R 3,10 (IC 1,20 a 10,6) sin los cuadros con viento desde Chillán. Está bien como lectura; el rótulo
  CONFIRMADO de STATUS promete más que una sensibilidad con GFS de 1° que el propio criterio llama "grueso" (§8).
- CONFIANZA: CONFIRMADO. GRAVEDAD: 2.

### 116. S25b STATUS: una lección general sacada de un solo año fuera de muestra

- ARCHIVO:LÍNEA:
  `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\Goes\.claude\worktrees\s28b-auditoria-s23-s28a-c1cff8\STATUS.md:51-52`, `:60`.
- QUÉ PASA: "el ensayo en seco dentro de la muestra sobreestima la falsa alarma de otro año tranquilo" y "CONFIRMADO: el
  umbral de 2025 no infla falsas alarmas en otro año tranquilo" generalizan desde 2024 solo (el INFORME de S25b, §4, sí
  dice "dos años no son una climatología"), con 46 a 51 % de cuadros que pasan la compuerta en 2024.
- CONFIANZA: CONFIRMADO. GRAVEDAD: 2.

### 117. S25a: la "zona de 0 a 4 km" llega a 5,2 km y la mitad de sus disparos viene de los píxeles de más de 4 km

- ARCHIVO:LÍNEA:
  `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\Goes\.claude\worktrees\s28b-auditoria-s23-s28a-c1cff8\docs\own_volcat\s25a_crater\criterio_2026-11-25.md:32-35`;
  `resultados/s25a_posthoc.json` `pixeles_en_disparos`.
- QUÉ PASA: el criterio lo dice (1,2 a 5,2 km), pero todos los títulos dicen "0 a 4 km". Los tres píxeles del bloque a
  más de 4 km ((43,47) 5,0; (43,46) 4,6; (43,45) 5,2) ponen 550 de 1.138 píxeles en disparo (48 %); con (40,46) a
  4,0 km, 580. Son los que S26b y S27a leen como cumbre aparente por paralaje.
- CONFIANZA: CONFIRMADO. GRAVEDAD: 2 (nombre). Seguimiento F4 (geometría).

## 4. VERIFICADO LIMPIO (y contra qué vara)

- **Pre-registro de las once medidas** (tabla de §2): criterio commiteado y empujado antes del commit y del empuje de la
  medida, diff del criterio vacío hasta la medida salvo la enmienda 1 de S27a (fechada 14:29, antes del viento y de la
  medida) y el §6 de S23b (antes de bajar días nuevos). Vara: `git log --all`, `git diff`, reflog `update by push` de
  cada rama remota y, aparte, mtimes de los cachés de D:. Una verificación sólo con fechas de commit no podía fallar si
  el dato se miró antes sin commitear; por eso la segunda vara de mtimes.
- **Rótulo recalculado desde el criterio** para S23a (PARCIAL y la etiqueta), S25a (ALCANZA y 14-11 ALCANZADO), S26a
  (p* = 4,75 y ALCANZA desarrollo), S25b (COMPARABLE, AGUANTA y MÁS ESTRICTO en las dos versiones, INTERMEDIO), S28a
  (NO CONCLUYENTE y MIXTO), S26b (NO EXPLICA), S27a (SIN PODER, N NO DECIDIBLE, DEPÓSITO NO), S27b (NO DECIDIBLE), S24
  (A INVÁLIDA, 16 bandas, B1). 19 de 19 rótulos del censo, más las 16 bandas y el B1 de S24, coinciden. Vara: las tablas de veredicto del texto de cada criterio, no el
  código de la sesión.
- **Código contra criterio** (b), leído línea a línea en lo que decide: `s23_medir.py` (costumbre, base, umbral,
  disparos, azar por hora, Poisson binomial, poder con rayo de 4 a 20 km, episodios ±30 min, orden de veredictos),
  `s24_medir.py` (bandas, mínimos 3 píxeles y 5 cuadros, nulo ±60 min con base sin el día, noche 00:00 a 08:50, comunes
  < 3), `s24c_rumbo.py` (ventana de 6, 4 en un arco de 3 tajadas que contiene la del cuadro, P_B 10 a 30), `s25a_medir.py`
  (11 píxeles, controles > 45 km y ±300 m con mínimo 20, dos más bajos con mínimo 6, persistencia sin vecindad, seco
  global, Fisher unilateral, 2 días, 14-11 con 3 y 0,01, INVÁLIDA al final pisa todo), `s26a_medir.py` (mismo percentil
  en las dos partes vía `PCT_U`, unión de evaluados y de disparos, p* el más alto con las dos medidas, 3 días),
  `s25b_medir.py` (AGUANTA, DEGRADA, MÁS ESTRICTO, ESTABLE, INTERMEDIO), `s26b_medir.py` (orden NO DECIDIBLE primero),
  `s28a_medir.py` (exclusión a 45 km de Chillán, mínimo ⌈0,75 × tajadas⌉, controles a 45 km de las dos cumbres,
  remuestreo por días con 2.000 réplicas y semilla 0, MIXTO), `s27b_comun.py`. Los cambios de código posteriores al
  primer commit de cada script los revisé con `git diff`: S25a (una línea `os.makedirs`), S26a (sólo `confirmar`, después
  de la medida: es de F3), S28a (la `base` con el largo del anillo propio, dicha en su INFORME; con el largo de Chillán
  el arreglo de 837 no recibe 552 valores, así que la primera corrida no pudo dar cifras de las vecinas).
- **Cifras de INFORME y STATUS** dentro de tolerancia, salvo los hallazgos: S23a (8 de 30, 1,51, 8e-5, 2 de 5, 0,043 de
  53 días y 3.668 cuadros, umbrales por hora 03 a 22 UTC contra S22b, 28-10 29 a 50 % y 4 a 47 %, 08-11 16 disparos de
  17:00 a 20:40, sin el 08-11 0 de 17), S23b candidata (25 de 54, 2,55, 3 de 234, por día), S24 (85 %, 55 noches, 2 de
  1.409, 12 de 858, p 0,0003, B2, B3, S24c 0,056 a 0,165), S25a (93, 44, 4,1, 1,8e-34, 116 de 649, 2,3e-9, por día, 14-11
  20 de 31, poder 0,14 y 0,785, seco 176 de 5.499, umbrales por hora, píxeles), S25b (cobertura, I4 0,987 con 892 noches,
  Planck, (c), 68 % en 16 a 18-11, 14 de 41 al SE, 13 nocturnos el 16 y 18-11, E24 1,19), S26a (283 y 269 de 5.499, 36 de
  319, 63 de 93, 5,9, 6e-53, 113 de 649, 1,8e-22, 6 de 9 días, 6 de 11 episodios, sin cada día 0,64 a 0,71, tasas), S26b
  (todas las de su tabla, y desde las tablas de D: 79 de 94 en 4 noches de 2025 y 28 de 41 noches de 2026 con 3 o más),
  S27a (todas las de su tabla), S27b (pares, bandas, avance), S28a (tabla principal, por parte, sensibilidades, lectura
  10,3 % y 7,7 %, concentración y placebo).
- **Lo post hoc está rotulado** en S23 (diagnóstico, sensibilidad), S24 (rumbo del 14-11), S25a (`s25a_posthoc.json`),
  S25b (azar 2024), S26b (concentración, píxeles), S27a ("PLUMA NO" a 0,05), S28a (`s28a_posthoc.json`). Lo que ya se
  sabía antes de un criterio está dicho en el criterio: S24 §1, S25a §5, S26b "Lo que ya sé", S27a §2, S28a §1 (la zona
  de las vecinas ya publicada por S27a), S27b (el listado de pares cambió la regla y lo dice §2.4).
- **Orden de las reglas** (INVÁLIDA o NO DECIDIBLE antes que todo) respetado en el código de S23a, S25a, S25b, S26a,
  S26b, S27a y S28a.

## 5. SIN DATO

- **Empuje de los criterios anteriores a la medida, para ramas sin reflog**: todas las medidas tienen reflog de empuje
  en este clon; si alguna sesión empujó desde otro clon, el reflog no lo vería. No encontré ninguna.
- **Que nadie miró el dato sin commitear antes del criterio**: lo que git y los mtimes pueden decir está en §2; lo que
  pasó en la conversación de cada sesión no deja rastro. En particular, la frase del criterio de S25b "lo único abierto
  de 2024 antes de este commit es un cuadro de prueba" no se puede comprobar.
- **Primera corrida de S28a** (la que falló en `base`): su `medir.log` fue reescrito; el fallo lo deduzco del tamaño de
  los arreglos, no lo vi.
- **Cifras que no están en ningún JSON**: el rumbo de la huella de VOLCAT del 14-11 (243°, 106°, ...) y el umbral cuadro
  a cuadro de S24 §1; "de 4 a 31 píxeles" de la huella del 14-11 (el JSON sólo trae el anillo, 0 a 30); los rumbos y
  velocidades de viento noche a noche de S27a (están en `D:\goes_notas\s27\s27a\cuadros_noche_2026.csv`, que no abrí).
- **Confirmaciones congeladas** (`s23b_confirmar.py`, `s26a_medir.py confirmar` y `confirmar_s25a`): no las leí como
  objeto; son de F3.

## 6. Seguimientos (fuera de F1, una línea cada uno)

- F2: la etiqueta SEPARA VOLCAT de S23a con EN_2026 = 0 y pN = 0 no puede fallar con un solo alcanzado (S23b ya lo
  corrigió con Fisher).
- F2: el SIN PODER de S27a es el piso 1/61 = 0,0164 de 60 corrimientos contra un umbral 0,01.
- F2: S28a descarta las réplicas con 0 disparos en 2025 (`replicas_validas` 1.998 y 1.999 en dos casos); el IC es
  condicional a eso.
- F2: B2 de S24 trata cuadros seguidos como independientes (Mann-Whitney sobre 1.754 cuadros).
- F3: `s26a_medir.py confirmar_s25a` usa el azar `X.seco(5)["z"]`; comprobar que es el r25 de S25a que su criterio de
  confirmación pide.
- F4: la zona de S25a incluye píxeles a 4,6 a 5,2 km (117) y es la cumbre aparente por paralaje según S26b y S27a.
