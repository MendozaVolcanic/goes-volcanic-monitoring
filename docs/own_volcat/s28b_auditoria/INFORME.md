**Cambian un veredicto: 0 publicados por su regla escrita; 2 con la regla o el número corregido (102: S24 B1 pasa a EPISÓDICO; 203: S27a pasa de SIN PODER a PLUMA NO); 8 pueden cambiar el de las tres confirmaciones congeladas el día de la medida única (SIN DATO hasta entonces: 201, 961, 962, 301, 302, 306, 307, 981).**

# S28b: auditoría de lo medido de S23 a S28a. Informe, 26-11-2026

- **Hora del servidor al cerrar**: 26-11-2026 04:56 UTC.
- **Base auditada**: `origin/main` = `8894722` (26-11 03:05 UTC). **Plan pre-registrado**: `002feff`
  (`C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\Goes\docs\own_volcat\s28b_auditoria\PLAN.md`), empujado
  antes de lanzar auditores; los cinco verificadores comprobaron `git diff 002feff` vacío.
- **Rama**: `claude/s28b-auditoria-s23-s28a-c1cff8`. Carpeta:
  `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\Goes\docs\own_volcat\s28b_auditoria\`; lo pesado en
  `D:\goes_notas\s28\s28b\` (menos de 300 MB en total).
- **Agentes**: cuatro auditores (F1 a F4) con Opus 5.5, esfuerzo por defecto de la sesión; cinco verificadores de
  contexto limpio con Fable 5.2, esfuerzo `high` pedido (el esfuerzo con que corrieron no se leyó en sus transcriptos:
  SIN VERIFICAR). Consumo: F1 454 mil tokens y 23 min; F2 361 mil y 27 min; F3 344 mil y 40 min; F4 386 mil y 19 min;
  verificadores 223 mil (11 min), 224 mil (18 min), 342 mil (23 min), 325 mil (26 min) y 397 mil (64 min).
- **Qué NO se miró**: S29a y S29b (corrían; S29a se fusionó en `main` durante la auditoría, PR 136); el dashboard; S22
  salvo lo que S23 a S28a importan; la versión del algoritmo ACMF; ningún día posterior al 24-11-2026 (prohibido por
  plan); las cámaras del OVDAS (no hay verdad propia de pluma en cuadros sin VOLCAT); el cubo de 2024 con la zona.

## En una pantalla

1. **El pre-registro está sano.** Las once medidas de S23 a S28a commitearon y empujaron su criterio antes del dato, sin
   cambios hasta la medida salvo dos enmiendas fechadas antes del dato. 19 de 19 rótulos recalculados desde el texto de
   su criterio coinciden con lo publicado. Nadie miró el detector en días posteriores al 24-11, y el estado congelado
   `estat_2026.npy` es el declarado.
2. **El problema de fondo es estadístico y toca las tres confirmaciones congeladas.** Todos los p de estas pruebas tratan
   cada cuadro de 10 minutos como independiente, pero los disparos vienen en rachas dentro del día. En 2025 la
   correlación entre un cuadro y el siguiente es 0,87 a 0,90, y la varianza del conteo diario es 16 a 33 veces la que
   supone el Poisson binomial. En placebos sin VOLCAT, el p25 de las confirmaciones (S23b, S25a, S26a) da p ≤ 0,01 en el
   12 a 18 % de los casos, y la regla completa da un CONFIRMA falso en el 2 a 8 % (201, 961, 962). **No se debe correr la
   medida única con el p25 por cuadro tal como está** (la coordinadora S28 ya la retuvo). La corrección está en §4.
3. **Cuatro defectos de ejecución pueden torcer la medida única** (301, 302, 306, 307), los cuatro reproducidos sobre
   días ya vistos. Un día sin GOES o sin ACMF al final pasa en silencio y cambia el rótulo. S25a y S26a pueden medir otros
   días que S23b. El gatillo cuenta P aunque no sean evaluables. Además, S23b casi no puede llegar a CONFIRMA, porque
   cerca de los P casi no hay cuadros N (981). Ninguno toca los scripts congelados: se arreglan con una comprobación
   previa, un manifiesto y una enmienda (§4).
4. **Ningún rótulo publicado cae por su regla, pero varias lecturas sí.** Con el día como unidad, S23a PARCIAL queda en
   el umbral (p 0,04 a 0,12, todo en el 08-11). El ALCANZA de la zona S25a mide sobre todo "día encendido": dentro del
   día no separa P de N, con razón de odds 0,96. La unión S26a sí se sostiene por día (p25 por día ≤ 1e-7), y separa por
   el anillo. El MIXTO de día de S28a depende de un solo día (10-11) y de la semilla (8 a 11 %). En S24, "2026 dispara 10
   veces más que una noche común de 2025" sale de una selección asimétrica y no prueba un exceso.
5. **Las cuatro líneas base rojas salieron**, y por lo tanto los "limpios" de cada frente valen. F1 marcó inválido el
   control A de S24 sin leer su informe. F2 encontró solo el piso 1/61 de S27a. F3 vio fallar la guarda de hash por
   aserción con un byte mutado. F4 encontró por su cuenta la constante de Chillán `M.NA` en `s23_medir.py:207`.

## 1. Hallazgos que cambian o pueden cambiar un veredicto

Detalle, reproducción y salida cruda en el informe del frente y en el del verificador; tabla completa en
`C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\Goes\docs\own_volcat\s28b_auditoria\hallazgos.csv` (61
hallazgos: gravedad 5: 1, 4: 11, 3: 21, 2: 22, 1: 6).

### 1a. Confirmaciones congeladas (SIN DATO hasta la medida; arreglar antes)

| ID | Qué | Verificación | Efecto en la medida única |
|---|---|---|---|
| 301 (G5) | El gatillo cuenta P de días sin GOES; la cobertura I1 divide por el último cuadro presente | CONFIRMADO, reproducido | Sin GOES en el último día, la medida sale "válida" y S26a pasa de CONFIRMA a PARCIAL; con 6 h sin L1b sobre los P, S23b pasa a NO DECIDIBLE; un día faltante en medio da INVÁLIDA y ningún criterio dice si eso gasta la medida |
| 201 + 961 (G4) | El p25 por cuadro no tiene tamaño nominal en ninguna de las tres reglas | CONFIRMADO EN PARTE: el verificador da más que el auditor (2025: anillo 11,9 %, zona 12,7 %, unión 14,0 %; 2026 sin P: zona 18,1 %, unión 18,4 %) | Un PARCIAL o un CONFIRMA con p25 entre ~1e-9 y 0,01 no distingue un día con racha de un acierto. Corregir con el umbral de Bonferroni (0,0033) casi no cambia nada (10 a 12 %) |
| 962 (G4) | pN (Fisher por cuadro) no protege | Hallazgo del verificador | La regla completa da CONFIRMA falso en 2,1 a 3,4 % (2025) y en 0 a 5,6 % (2026 sin P) |
| 302 (G4) | "Misma ocasión y mismos datos" (S26a §5) no está implementado | CONFIRMADO, reproducido | S23b midió con 25 P y S25a y S26a con 28, sin aviso |
| 306 (G4) | No se comprueba la cobertura de ACMF | CONFIRMADO, reproducido | Sin ACMF un día, S23b pasa de PARCIAL a NO DECIDIBLE (de 18 a 5 P evaluados), sin rastro en S25a ni S26a |
| 307 (G4) | El gatillo cuenta P, no P evaluables | CONFIRMADO (diseño) | S23b NO DECIDIBLE en 3 de 9 arranques con los días del desarrollo |
| 981 (G4) | Con 2 cuadros N cerca de los P, el pN mínimo de S23b es 0,147 | Hallazgo del verificador | S23b no llega a CONFIRMA aunque acierte (12 de 18 con p25 2e-12 queda PARCIAL); la unión tuvo 56 N y pesa menos |

### 1b. Cambian un veredicto con la regla o el número corregido

- **102 (S24, regla B1), G3, CONFIRMADO EN PARTE.** La regla escrita excluye de 2025 sus noches con 3 o más disparos y
  deja 2026 entero; el código la cumple, así que el rótulo publicado (NO EPISÓDICO) es el de la regla. Con la misma
  selección en los dos años: 2 de 1.409 contra 6 de 809, razón 5,2, Fisher 0,057, **EPISÓDICO**. Pero depende de una
  sola noche (29-10-2026, que parece detección real, con VOLCAT P a las 01:10 y 01:20). Lo firme es otra cosa: la regla
  escrita aplicada a 2025 contra sí mismo da NO EPISÓDICO con razón 31. Por eso **el titular "la noche de 2026 dispara
  unas 10 veces más que una noche común de 2025" no prueba un exceso**, y viaja en `STATUS.md` (bloque 0-prev20, marcado
  CONFIRMADO) y en la memoria `project_s24_noche_y_14nov`.
- **203 (S27a, prueba P), G3, CONFIRMADO.** Pedir p ≤ 0,01 con 60 corrimientos es inalcanzable (piso 1/61 = 0,0164).
  Con un umbral alcanzable, la tabla del criterio da PLUMA NO (p de 2026 = 21/61 = 0,344). S27a ya lo había declarado en
  su informe (líneas 77 a 81), así que no es un defecto oculto. Es la línea base roja de F2.

### 1c. No cambian el rótulo, cambian su lectura (lo que decide qué se le muestra a Nicolás)

- **204 + 943 (S25a ALCANZA), G4.** Estratificada por día, la zona tiene razón de odds 0,96 (0,59 a 1,56). En el 14-11
  alcanza 44 de 60 N; en el 10-11, 24 de 25 N desde cinco horas antes del primer P. El 28-10 sí separa (15 de 26 P contra
  0 de 75 N). Con pN por día, S25a quedaría en PARCIAL (0,58; 0,084 de tarde). Límite: P y N casi nunca conviven a la
  misma hora del mismo día (9 N a 60 min de un P), así que "dentro del día" compara tarde con noche.
- **205 + 942 (S23a PARCIAL), G4.** Por día, el p25 de S23a da 0,04 a 0,12 si se cuentan sólo días evaluados (0,017 si
  se cuentan los 36 días de 2025 que el anillo no evalúa a esas horas), y 0,092 por episodio. Los 8 aciertos son del
  08-11. 963 (SOSPECHA): en placebo de dos días, 5 a 12 % iguala ese p25; si no fuera significativo, la regla daría SIN
  PODER.
- **202 + 941 (S25a, "14-11 ALCANZADO"), G3.** Los 20 alcanzados son 3 rachas de un solo episodio. Ningún día de 2025
  llega a 20 en esas horas (máximo 15, el 14-11-2025), pero por día el p queda entre 0,016 y 0,04, sobre el 0,01: con
  esa referencia la prueba por día **no podía pasar**. La lectura justa es "no decidible por día", no "no alcanzado".
- **206 + 921 (S28a, MIXTO de día), G3.** Con la semilla 0 escrita da MIXTO; con 1.000 semillas, 8,4 % daría NO
  CONCLUYENTE (11 % con 200). Sin el 10-11, Antuco da R 2,16 (0,87 a 6,92): NO CONCLUYENTE. El criterio dice que 2.000
  réplicas dan "resolución de sobra"; con este margen no es cierto.
- **101 + 104 + 114 (S28a, lectura), G3.** El criterio define MIXTO como "cambio local de una cumbre"; el INFORME y
  `STATUS.md` (0-prev27 §c) lo leen con la consecuencia que el criterio reservó a NO SE SOSTIENE. El 10-11 las tres
  cumbres disparan juntas de 15:40 a 19:40 UTC, pero en cuadros N; en los 8 aciertos de Chillán (21:30 a 23:20) ninguna
  vecina dispara. La decisión 1 que se le propone a Nicolás (placebo en las vecinas) tendría que contar también los
  cuadros sin VOLCAT: el 10-11 la cuenta que propone da 0.
- **401 + 117 (la "zona de 0 a 4 km"), G3.** Sus 11 píxeles van de 1,2 a 5,2 km del cráter; 5 quedan a más de 4 km de
  donde GOES ve la cumbre (2,99 km al SSE por paralaje y cota), y el 48 % de los píxeles en disparo está a más de 4 km.
  Una pluma sobre el cráter cae en (43,46) a 4,64 km. No cambia ningún conteo: cambia lo que el nombre promete.

## 2. El resto de los hallazgos (gravedad 1 a 3, en `hallazgos.csv`)

Verificados: 208 (clases de 34 días, no 21-09 a 24-11; el estat rehecho da idéntico), 211 (el poder no entra a ningún
veredicto; la unión sin poder medido), 303 (sin guarda de "una sola vez"), 305 (sólo el estat tiene hash; F3 dejó un
manifiesto de sha256 de las entradas en su anexo A), 304, 308, 309 (la bajada de S23b del 25-11 no bajó nada y lo
informa como "sin dato"), 312. Sin verificar, publicados con su conteo (gravedad 1 a 3, fuera del corte del plan §5):
**25**: 103, 105 a 109, 112, 113, 116, 207, 209, 210, 212 a 215, 310, 311, 403 a 408, 922 (y los propios de los
verificadores sin segunda pasada: 901 a 903, 944, 983). Cifras de informe que no salen del JSON: 105, 106, 107, 108,
109, 112, 113 (ninguna cruza un umbral).

## 3. VERIFICADO LIMPIO (con su vara)

- **Pre-registro de las 11 medidas**: criterio commiteado y empujado antes del commit y del empuje de la medida; diff
  vacío hasta la medida salvo la enmienda 1 de S27a y el §6 de S23b, ambas previas al dato. Vara: `git log --all`,
  `git diff`, reflog `update by push` de cada rama remota y, aparte, mtimes de los cachés de D: (una vara sólo de commits
  no podía fallar si el dato se miró sin commitear). F1.
- **Rótulos**: 19 de 19, más las 16 bandas y el B1 de S24, recalculados desde la tabla de veredictos del texto de cada
  criterio (no desde el código de la sesión). F1.
- **Reproducción**: 8 de 30, 44 de 93, 63 de 93 y 25 de 54, y los p25 y el seco publicados, exactos con dos
  reconstrucciones independientes (F2 y el verificador de 202, este con 0 diferencias en unas 15.000 filas). S24
  `pregunta_b()` y S28a `veredicto` reproducen sus JSON.
- **Congelamiento**: nada miró el detector después del 24-11-2026 23:50 UTC (barrido de literales, glob, contenido y
  mtimes; control positivo: encuentra `s23b_confirmar.py:36-37`); `D:\goes_notas\s23\s23b\l1b` y `acm` vacías; ningún
  archivo de vistazo ni de resultado de confirmación; `contar` no toca el detector; `estat_2026.npy` coincide con lo
  declarado (mtime 12 s antes del commit `97bdec1`) y la guarda falla por aserción con un byte mutado. Las tres
  confirmaciones corren de punta a punta sobre días ya vistos (08 a 11-11) y reproducen el desarrollo día por día. F3 y
  verificador.
- **Geometría**: 2024, 2025 y 2026 usan la misma grilla y el mismo recorte (mejor corrimiento (0,0), con control
  positivo); S27b convierte rapidez en altura con unidades coherentes; S28a corrigió `M.NA` en `s28a_medir.py:167-181`
  (sin esa corrección la función original lanza ValueError: el error habría sido ruidoso). F4.
- **Nulo por día de la unión S26a**: p25 por día ≤ 1e-7 y pN por día 5e-6 a 2,4e-3. El ALCANZA de desarrollo de S26a se
  sostiene con el día como unidad. Verificador de 202.
- **Fuga del día evaluado** (cada día sin sí mismo): existe pero mueve 1 a 3 disparos; p* = 4,75 no cambia. F2.

## 4. Recomendación: cómo corregir antes de la medida única (sin mirar días posteriores al 24-11)

Pedida por la coordinadora S28. Todo se decide con 2025 y 2024 y se escribe como **enmienda fechada, commiteada y
empujada antes de abrir un solo cuadro GOES de días nuevos**. Es pre-registro legítimo, porque la confirmación no se ha
medido; las reglas congeladas se conservan y se informan al lado, rotuladas.

**a. Nulo por días (reemplaza al p25 por cuadro como prueba que decide).**
1. Estadístico: R = P evaluados alcanzados / P evaluados de los días nuevos, con la misma `alcanzado`, la misma
   compuerta y la misma regla de cada confirmación.
2. Nulo: colocar las horas UTC de los P de cada día nuevo sobre días de 2025 (base y umbral sin esos días, como el
   ensayo en seco). Con k días nuevos, se sortean k-tuplas de días distintos de 2025: con 2 días hay 62 × 61 = 3.782
   pares (piso 2,6e-4). 2024 (GOES-16) va como segundo fondo, informativo.
3. Condicionar a la decidibilidad: sólo cuentan las colocaciones que cumplen el mismo mínimo que el criterio (al menos 10
   P evaluados y de al menos 2 días). Por qué: el 941 mostró que buena parte de 2025 no se evalúa a esas horas, y
   comparar contra días sin evaluar hace la prueba demasiado fácil o imposible según cómo se cuenten.
4. p_día = (1 + colocaciones con R ≥ R observado) / (1 + colocaciones válidas). CONFIRMA exige p_día ≤ 0,01 y R ≥ 0,40.
5. **Antes de escribir el umbral, calibrarlo con el placebo** (`verificacion/scripts/v201_placebo.py` y
   `f2_estadistica/scripts/f2_bloques.py` ya lo hacen): la regla nueva entera tiene que dar CONFIRMA falso en ≤ 1 % de
   los placebos de 2025 y de 2026 sin VOLCAT. F2 midió que un nulo por días da 0 % donde el p25 por cuadro da 7,8 %.
6. pN: reemplazarlo por una comparación estratificada por día (P contra N del mismo día a ≤ 3 h, Mantel-Haenszel), y
   dejarlo **informativo**. Por qué: P y N casi no conviven a la misma hora (204), y con el Fisher actual S23b no puede
   confirmar (981).

**b. Ejecución (sin tocar los scripts congelados), según el verificador de 301.**
1. Comprobación previa de cobertura: L1b C14, C15 y ACMF de cada cuadro de 10 min, del 25-11 00:00 al último cuadro del
   CSV de clases; si falta algo, se baja o el día se declara fuera **antes** de medir (301, 306, 309).
2. Manifiesto: sha256 del CSV de clases, de la lista de archivos del cubo y de los cachés de 2025 y las grillas (anexo A
   de F3), escrito al medir S23b y comparado antes de S25a y S26a (302, 305).
3. Envoltorio que se niegue si ya existe un resultado o un vistazo (303).
4. Enmienda que diga qué pasa tras una INVÁLIDA o una NO DECIDIBLE (¿gasta la medida?), y que el gatillo cuente **P
   evaluables** (307).
5. Correr `contar` desde una sola carpeta de trabajo (983): hoy `main` y la coordinadora tienen CSV distintos.

## 5. Decisiones que esperan a Nicolás (vía la coordinadora S28)

| # | Pregunta | Recomendación |
|---|---|---|
| 1 | ¿Se reemplaza el p25 por cuadro por el nulo por días de §4a en las tres confirmaciones, con enmienda antes del dato? | Sí. Con el p25 actual, un CONFIRMA o PARCIAL del día de la medida no se puede leer como evidencia |
| 2 | ¿Se agregan la comprobación de cobertura, el manifiesto y el envoltorio de §4b antes de medir? | Sí, y antes del primer LISTO PARA MEDIR |
| 3 | ¿Se corrigen las lecturas de §1b y §1c en `STATUS.md` y en la memoria (titular de S24, MIXTO de S28a, 14-11 de S25a), con marca al inicio del pasaje y el texto viejo conservado? | Sí, en un cambio aparte que propague la rebaja con `grep` del número y la frase |
| 4 | ¿S23b sigue como confirmación, sabiendo que casi no puede llegar a CONFIRMA (981)? | Que siga, pero con el pN informativo de §4a.6; si no, quitarla antes del dato, nunca después |

## 6. SIN DATO

- La versión del algoritmo ACMF dentro de las ventanas (F2). Cuánto tarda NOAA en publicar el ACMF de un día.
- El poder de la unión a p* = 4,75 (ningún criterio define la inyección conjunta).
- Si los disparos en cuadros N de 2026 son pluma real (falta verdad propia: cámaras del OVDAS).
- El análogo de cinco días de 963; la fuga de segunda mano del anillo; el pN de las confirmaciones con dependencia.
- S24 y S27b no se recomputaron enteros (F2); S24 B1 sí (verificador).
- El esfuerzo con que corrieron los verificadores (pedido `high`; no leído en el transcripto).

## 7. Seguimientos (fuera de eje, no perseguidos)

- Dos verificadores corrieron con `C:\Users\nmend\AppData\Local\Programs\Python\Python312\python.exe` (3.12.10) en vez
  del de Anaconda; reproducen lo publicado, así que no pesa.
- Los imports de los auditores dejaron `__pycache__` en las carpetas `scripts\` auditadas (ignoradas por git). Usar
  `python -I -B` en las próximas.
- Un verificador leyó por error la línea de título del bloque de S29a en `STATUS.md` de `origin/main`, y otro listó los
  nombres de archivo de `D:\goes_notas\s28\s28b\f2\` sin abrirlos. Ninguno de los dos efectos toca un veredicto.

## 8. Dónde está cada cosa

- Informes de los frentes: `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\Goes\docs\own_volcat\s28b_auditoria\f1_cierres\INFORME_F1.md`,
  `...\f2_estadistica\INFORME_F2.md`, `...\f3_congelamiento\INFORME_F3.md`, `...\f4_magnitudes\INFORME_F4.md`, cada uno
  con su `scripts\`.
- Verificaciones (con sus caminos de ruptura sellados por sha256 antes de abrir el objeto):
  `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\Goes\docs\own_volcat\s28b_auditoria\verificacion\` (V101_104,
  V102, V201_203_206, V202_204_205, V301_312, con `scripts\` y salidas).
- `hallazgos.csv` lo arma `scripts\armar_hallazgos_csv.py` con el módulo `csv`.
