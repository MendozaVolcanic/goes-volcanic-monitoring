# S28b, frente F3 (congelamiento): informe del auditor

**Ningún hallazgo cambia hoy un veredicto. De los 12 hallazgos, 8 tocan una confirmación congelada (301 a 308); cinco
(301, 302, 303, 305, 306) pueden cambiar su veredicto el día de la medida única (SIN DATO hasta que se corra) y dos son
de gravedad 4 (301, 302).** Las dos líneas base rojas salieron.
Nadie miró el detector en días posteriores al 24-11-2026 23:50 UTC, el estado congelado es el que dicen los criterios
y los tres confirmadores corren de punta a punta sobre días ya vistos y reproducen el desarrollo cuadro por día.

- Base auditada: `origin/main` 8894722; vara: `docs/own_volcat/s28b_auditoria/PLAN.md` (commit 002feff), sin tocar.
- Auditor: Opus 5.5 (esfuerzo de la sesión). Fecha: 26-11-2026, desde ~03:15 UTC.
- Instrumento (repo):
  `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\Goes\.claude\worktrees\s28b-auditoria-s23-s28a-c1cff8\docs\own_volcat\s28b_auditoria\f3_congelamiento\scripts\f3_barrido_fechas.py`,
  `...\f3_hashes_entradas.py` y `...\f3_ensayo_confirmaciones.py` (misma carpeta).
- Salidas (D:): `D:\goes_notas\s28\s28b\f3\` (`barrido_fechas.json` y `.txt`, `hashes_entradas.json`, `mutacion.json`,
  `seco\*.json`, `seco_*.log`, `hueco_*.log`, copias `hueco_final\`, `hueco_medio\` y `estat_2026_mutado.npy`).
- Qué no se miró: ningún cuadro GOES ni salida del detector de días nuevos (prohibido); no se corrió `contar` ni
  `medir`; S29a y S29b no se abrieron (el `origin/main` actual ya trae commits de S29a posteriores a la base; no se leyeron).
- Cómo se ensayaron los confirmadores sin días nuevos: el script importa los módulos originales sin copiarlos ni
  editarlos y cambia en memoria sólo las rutas: `s23b_confirmar.TRAB` a `D:\goes_notas\s17\h23` (npz de H23 ya mirados),
  `ARRANQUE` al 07-11-2026, clases de VOLCAT del 08 al 11-11 sacadas de `calor_rayos/resultados/frames_calor.csv`, y las
  salidas (`s23_medir.RES`, `s26a_medir.RES`, `RES_S25A`) a `D:\goes_notas\s28\s28b\f3\seco\`. `estat_2026.npy` se lee
  del original sin tocarlo. Todas las corridas son `vistazo`, que no exige el gatillo.

- Efecto colateral declarado: al importar los módulos originales, Python escribió `__pycache__\*.cpython-312.pyc` en
  las carpetas `scripts\` de s22a, s22b, s23, s25a, s26a, h24 y h29 (ignorados por `.gitignore:8`, no son contenido
  auditado; otros frentes importan los mismos módulos y también los generan). No se borraron para no interferir con
  ellos. Nada más se escribió fuera de mi carpeta del repo y de `D:\goes_notas\s28\s28b\f3\` (`git status`: sólo
  carpetas nuevas de S28b).

## Líneas base rojas

1. **Mutación del estado congelado: SALIÓ.** Copia en `D:\goes_notas\s28\s28b\f3\estat_2026_mutado.npy` con el byte
   5128 (dato, tras la cabecera de 128) cambiado de 0 a 1. `s23b_confirmar.medir` corre hasta la guarda y se corta en la
   línea siguiente (`_cubo` reemplazado por una excepción centinela): con la copia, `AssertionError: estat_2026 cambió:
   no es el congelado`; con el original, pasa la guarda y llega a `_cubo`. Salida: `D:\goes_notas\s28\s28b\f3\mutacion.json`.
   El original sigue con SHA-256 de archivo `8e0768bf...e9fe8233` antes y después (sha256sum).
2. **Control positivo del barrido de fechas: SALIÓ.** `f3_barrido_fechas.py` encuentra el manejo legítimo de días nuevos
   en `s23b_confirmar.py:36` (`NUEVO0 = datetime(2026, 11, 25)`) y `:37` (`volcat_clases_desde_25nov.csv`), además de
   `s26a_medir.py:17` y `:308` (confirmar desde el 25-11) y `s24c_rumbo.py:11` (medir de S24c, abandonada).

## Hallazgos (lo peor primero)

### 301. El gatillo cuenta P de días sin GOES y la medida no avisa: la medida única puede correr con días que no mide
- ARCHIVO:LÍNEA: `docs/own_volcat/s23_fondo_2025/scripts/s23b_confirmar.py:149-159` (días y gatillo salen sólo de
  `CLASES`), `:132-137` (I1 = cobertura hasta el último cuadro PRESENTE); igual en
  `docs/own_volcat/s26a_combinado/scripts/s26a_medir.py:358-366` y `:340-344` (S25a y S26a).
- QUÉ PASA: `contar` y `bajar` son pasos separados, y `medir` no comprueba que la bajada de GOES y ACMF llegue hasta el
  último día de `volcat_clases_desde_25nov.csv`. Si `bajar` quedó antes que `contar` (o se cortó, ver 309), los P de los
  días sin GOES cuentan para el gatillo (20 P en 2 días) pero quedan sin evaluar, y la cobertura I1 se mide sólo hasta el
  último cuadro bajado, así que no hay falla de instrumento: la medida "vale" y se gasta.
- CÓMO SE VE EN EL VEREDICTO: con el 11-11 sin GOES, el confirmador de S23b informa `"falla": []`, `cobertura 1.0`,
  `P_total 28` en `3` días (gatillo) y `P_evaluados 15` en `2` días: el 11-11 queda con 3 P y 0 evaluados, y el veredicto
  sale igual (PARCIAL en el ensayo). Con días nuevos reales, un caso así puede dar NO DECIDIBLE o un R de menos días en la
  única corrida. Cambia el veredicto: SIN DATO (depende del día de la medida). El rótulo `"ultimo"` sí queda escrito en
  el JSON, pero ninguna regla lo mira. La asimetría es la otra cara: si el mismo día falta en el medio (10-11) la
  cobertura baja a 0,8 y la medida sale INVÁLIDA (`"falla": ["I1"]`), y ningún criterio dice si una INVÁLIDA por una
  bajada incompleta gasta la medida única o permite completar `bajar` y volver a medir. Ninguno de los tres
  confirmadores revisa, antes de medir, que haya L1b y ACMF de todos los días del CSV.
- CÓMO REPRODUCIRLO: `python -I f3_ensayo_confirmaciones.py hueco_final` (copia a `D:\goes_notas\s28\s28b\f3\hueco_final\`
  los npz de H23 del 07 al 10-11, sin el 11-11). Salida cruda en `D:\goes_notas\s28\s28b\f3\hueco_final.log`:
  `{"veredicto": "VISTAZO (no decide): PARCIAL", "instrumento": {"cuadros_hasta_el_ultimo": 576, "presentes": 576,
  "cobertura": 1.0, "ultimo": "2026-11-10 23:50", ... "falla": []}, "P_total": 28, "dias_con_P": 3, "P_evaluados": 15,
  "dias_con_P_evaluado": 2}` y `2026-11-11 P 3 P_eval 0 P_alc 0 disparos 0`. Variante del medio:
  `python -I f3_ensayo_confirmaciones.py hueco_medio`, salida `D:\goes_notas\s28\s28b\f3\hueco_medio.log`:
  `"presentes": 576, "cobertura": 0.8, "ultimo": "2026-11-11 23:50", ... "falla": ["I1"]`, veredicto INVÁLIDA.
- CONFIANZA: CONFIRMADO. GRAVEDAD: 4 (toca las tres confirmaciones congeladas; no cambia nada medido hasta hoy).

### 302. "En esa misma ocasión y con los mismos datos" no está implementado: S25a y S26a pueden medir otros días que S23b
- ARCHIVO:LÍNEA: `docs/own_volcat/s26a_combinado/criterio_2026-11-25.md:99` (orden, misma ocasión, mismos datos) y
  `docs/own_volcat/s25a_crater/criterio_confirmacion_2026-11-25.md:18`; código en
  `docs/own_volcat/s26a_combinado/scripts/s26a_medir.py:356-370`.
- QUÉ PASA: `confirmar` relee `volcat_clases_desde_25nov.csv` y vuelve a armar el cubo desde `D:\goes_notas\s23\s23b\`
  en cada corrida, y como prueba de orden sólo exige que EXISTA `s23b_resultado.json` (y `s25a_confirmacion.json` para la
  unión). No compara días, número de P ni un hash de las clases o del cubo con lo que usó S23b. Si entre la medida de
  S23b y la de S25a o S26a alguien corre `contar` (lo hace la coordinadora a diario) o `bajar`, las tres confirmaciones
  se miden sobre conjuntos distintos sin que nada lo diga.
- CÓMO SE VE EN EL VEREDICTO: el titular del día de la medida (S26a, §5) se lee al lado de S23b y S25a "para explicar
  por qué"; con días distintos esa explicación no vale. Cambia el veredicto: SIN DATO.
- CÓMO REPRODUCIRLO: lectura de `s26a_medir.py:356-370` (no hay otra comprobación entre `previos` y `Partes()`);
  `s23b_resultado.json` guarda `por_dia` pero ningún código lo vuelve a leer (grep de `s23b_resultado` en el repo: sólo
  `s23b_confirmar.py:219` lo escribe y `s26a_medir.py:367` comprueba que exista).
- CONFIANZA: CONFIRMADO (lectura de código). GRAVEDAD: 4.

### 303. "Una sola vez" y la regla del vistazo no tienen guarda en el código
- ARCHIVO:LÍNEA: `docs/own_volcat/s23_fondo_2025/criterio_S23b_2026-11-25.md:78-80`; código
  `docs/own_volcat/s23_fondo_2025/scripts/s23b_confirmar.py:157-159` y `:219-220`;
  `docs/own_volcat/s26a_combinado/scripts/s26a_medir.py:364-366` y `:434-438`.
- QUÉ PASA: (a) `medir` y `confirmar` sobrescriben `s23b_resultado.json`, `s25a_confirmacion.json` y
  `s26a_confirmacion.json` sin mirar si ya existen: una segunda corrida "decisiva" pisa la primera. (b) El criterio dice
  que un vistazo "obliga a esperar 2 días nuevos más con P antes de la medida"; el código no busca `s23b_vistazo.json`
  ni cuenta días después de él: con un vistazo hecho, `medir` corre igual apenas se cumpla el gatillo.
- CÓMO SE VE EN EL VEREDICTO: ninguno hoy (no hay vistazo ni resultado: barrido de `git log --all` y de todos los
  checkouts del proyecto, vacío). Si ocurre, la medida única deja de ser única sin rastro. Cambia el veredicto: SIN DATO.
- CÓMO REPRODUCIRLO: lectura; `git log --all --` con las rutas de `s23b_vistazo.json`, `s23b_resultado.json`,
  `s25a_confirmacion.json`, `s25a_confirmacion_vistazo.json`, `s26a_confirmacion.json`, `s26a_confirmacion_vistazo.json`,
  `s24c_resultado.json` y `s24c_vistazo.json` en sus carpetas `resultados\`: salida vacía; `find` de esos nombres bajo
  `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\Goes`: vacío (fuera de mi carpeta de D:).
- CONFIANZA: CONFIRMADO. GRAVEDAD: 3.

### 304. El rótulo "confirma con un umbral sin corregir por tres pruebas" falta en S23b y sobra en PARCIAL
- ARCHIVO:LÍNEA: `docs/own_volcat/s26a_combinado/criterio_2026-11-25.md:108-109` ("si alguna confirma con p25 entre
  0,0033 y 0,01"); `docs/own_volcat/s26a_combinado/scripts/s26a_medir.py:414-415`;
  `docs/own_volcat/s23_fondo_2025/scripts/s23b_confirmar.py:204-213` (sin el rótulo).
- QUÉ PASA: "alguna" son las tres. `s23b_confirmar.py` (que el criterio manda correr "sin tocar") nunca escribe el rótulo,
  así que un CONFIRMA de S23b con p25 entre 0,0033 y 0,01 saldría sin él. En S25a y S26a el código lo agrega también a
  PARCIAL, que el criterio no nombra.
- CÓMO SE VE EN EL VEREDICTO: no cambia el rótulo principal; cambia su lectura (en S23b, un CONFIRMA de umbral sin
  corregir se leería como corregido). Cambia el veredicto: no.
- CÓMO REPRODUCIRLO: lectura; `grep -n "sin corregir" s23_fondo_2025/scripts/*.py` sin resultados; `s26a_medir.py:414`
  dice `if ver in ("CONFIRMA", "PARCIAL") and ru["p25"] > P25_SIN_CORREGIR`.
- CONFIANZA: CONFIRMADO. GRAVEDAD: 3 (toca una confirmación congelada).

### 305. Sólo `estat_2026.npy` tiene guarda: base, umbral, costumbre de 2025, r25, azar de la unión y p* se recalculan sin hash
- ARCHIVO:LÍNEA: `docs/own_volcat/s23_fondo_2025/scripts/s23b_confirmar.py:164-176` (`Detector`, `base(None)`,
  `umbral(None)`, `_seco_2025` desde `D:\goes_notas\s23\s23a\r25_*.npy`); `docs/own_volcat/s26a_combinado/scripts/s26a_medir.py:68-101`
  (`Partes`, desde `D:\goes_notas\s25\s25a\r25_*.npy` y `D:\goes_notas\s22\s22b\dev_*.npy`, `nuevo_*.npy`), `:374-376`
  (p* leído de `resultados/s26a_seco.json`, sólo `assert p is not None`).
- QUÉ PASA: lo que el criterio llama "fijo" (base, umbral y nublado de costumbre de 2025 de los 62 días, r25 de S23a y de
  S25a, azar de la unión, p*) no está guardado: se recalcula en la medida desde cachés de D: que ningún código verifica, y
  `confirmar` no corre la comprobación de reproducción (25 de 54, 44 de 93, secos 0,04279 y 176/5499) que sí corre
  `s26a_medir.py medir` (`:205-214`). No hay ningún indicio de que hayan cambiado: los mtimes son anteriores a los commits
  que los congelaron (r25 de S23a 05:26:52 UTC del 25-11, antes de 97bdec1; r25 de S25a 12:12:21 UTC, antes de 08ba80a;
  dev y nuevo de S22b del 24-11) y los ensayos de abajo reproducen el desarrollo cuadro por día. Pero si `s23_medir.py cubo`
  o `s25a_medir.py cubo` se vuelven a correr, o un caché se pierde (D: anda justo de espacio), la confirmación usa otra
  regla sin avisar.
- CÓMO SE VE EN EL VEREDICTO: hoy ninguno. Cambia el veredicto: SIN DATO (sólo si un caché cambia).
- CÓMO REPRODUCIRLO: `python -I f3_hashes_entradas.py`; línea base de hoy en `D:\goes_notas\s28\s28b\f3\hashes_entradas.json`
  (tabla en el anexo A). Para cerrar el hallazgo basta comparar esa tabla el día de la medida.
- CONFIANZA: CONFIRMADO (que no hay guarda); SOSPECHA de riesgo, sin evidencia de cambio. GRAVEDAD: 3.

### 306. La cobertura de ACMF de los días nuevos no se comprueba
- ARCHIVO:LÍNEA: `docs/own_volcat/s23_fondo_2025/scripts/s23b_confirmar.py:135-137` (`acm_presentes` se informa, no entra
  a `falla`); `docs/own_volcat/s26a_combinado/scripts/s26a_medir.py:343-344`.
- QUÉ PASA: un cuadro con L1b y sin ACMF queda con `acm = 255`, `_nubes` lo salta (FD NaN) y el cuadro sale "no evaluado"
  sin falla de instrumento. Es lo que escribe el criterio (I1 de `cubo_nuevo` de S22b, sólo L1b), pero S23a sí exigía
  ACMF ≥ 0,90 (`s23_medir.py:104`), y la bajada de ACMF se cuelga más que la de L1b (S25b, `s25b_vigia.py:4`).
- CÓMO SE VE EN EL VEREDICTO: menos P evaluados en silencio; puede llevar a NO DECIDIBLE. Cambia el veredicto: SIN DATO.
- CÓMO REPRODUCIRLO: lectura de código.
- CONFIANZA: CONFIRMADO (lectura). GRAVEDAD: 3.

### 307. El gatillo cuenta cuadros P, no P evaluables: puede gastar la medida en días nublados
- ARCHIVO:LÍNEA: `docs/own_volcat/s23_fondo_2025/scripts/s23b_confirmar.py:155-159`; criterio
  `criterio_S23b_2026-11-25.md:79`.
- QUÉ PASA: es la letra del criterio ("20 cuadros P en 2 días"), pero el ensayo muestra el costo: el 10-11, 12 P y sólo 2
  evaluados por el anillo. Con días nuevos nublados el gatillo se cumple y la única medida sale NO DECIDIBLE (el propio
  criterio lo espera en §5, línea 74). Lo anoto porque decide cuándo se gasta la prueba.
- CÓMO SE VE EN EL VEREDICTO: no cambia una regla escrita; cambia cuánto cuesta. Cambia el veredicto: no.
- CÓMO REPRODUCIRLO: `D:\goes_notas\s28\s28b\f3\seco\s23b_vistazo.json`, día 2026-11-10: `"P": 12, "P_evaluados": 2`.
- CONFIANZA: CONFIRMADO. GRAVEDAD: 2.

### 308. El criterio dice "SHA-256 de los bytes", pero el hash es el del arreglo; y sólo se comparan 16 hexadecimales
- ARCHIVO:LÍNEA: `docs/own_volcat/s23_fondo_2025/criterio_S23b_2026-11-25.md:30-31`; `s23b_confirmar.py:39` y `:162`;
  igual en `s25a_medir.py:40,312`, `s26a_medir.py:71`, `s24_medir.py:216`, `s24c_rumbo.py:235,263`.
- QUÉ PASA: `e0f093eb6e441cc4...` es `sha256(np.load(f).tobytes())`; el SHA-256 de los bytes del archivo es
  `8e0768bfbe6d310a652dd624281c5692fc6137a65639e12fe24c12a0e9fe8233`. Quien verifique con `sha256sum` como dice el
  criterio verá otro número y creerá que el congelado cambió. Además la guarda no ve la cabecera (dtype, forma, orden):
  un arreglo `uint8` 0/1 con los mismos valores da el mismo hash, y en este código daría el mismo resultado (`dinamica`
  con `~` sobre `uint8` 0/1 deja el mismo bit bajo), así que no tiene efecto práctico. Probado en memoria con un arreglo
  aleatorio de 7.802 píxeles: hash igual (`True`) y `dinamica` igual (`True`); no lo escribí a disco.
- CÓMO SE VE EN EL VEREDICTO: ninguno. Cambia el veredicto: no.
- CÓMO REPRODUCIRLO: `python -I -c "import hashlib,numpy as np;p=r'D:\goes_notas\s23\s23b\estat_2026.npy';print(hashlib.sha256(open(p,'rb').read()).hexdigest());print(hashlib.sha256(np.load(p).tobytes()).hexdigest())"`
  da `8e0768bf...e9fe8233` y `e0f093eb6e441cc4c043325c0d7b5ce84e5c9e45acd92c36c5de1781e5c72120`.
- CONFIANZA: CONFIRMADO. GRAVEDAD: 2.

### 309. La bajada de S23b del 25-11 no bajó nada (corte por disco) y su log dice "29 sin dato"
- ARCHIVO:LÍNEA: `D:\goes_notas\s23\s23b\bajar.log` (`FIN l1b: 0 cuadros, 29 sin dato, 4 s` y lo mismo para acm);
  `docs/own_volcat/h23_inyeccion/scripts/h23_bajar.py:67-68`.
- QUÉ PASA: 29 horas pedidas (24-11 00 UTC a 25-11 04 UTC) y exactamente una "falta" por hora: es la rama de disco
  (`("DISCO", [])`, D: bajo 6 GB), porque una hora sin archivos da 6 faltas. Las carpetas `l1b\` y `acm\` de
  `D:\goes_notas\s23\s23b\` están vacías. Consecuencia buena: no hay GOES de días nuevos en disco. Consecuencias a vigilar:
  (a) `bajar` informa un corte de disco como "sin dato", y (b) el 24-11, día de arranque, tampoco está bajado.
  Además `contar` y `bajar` corrieron hacia las 05:55 UTC del 25-11 (mtimes de `listado_20261125_0555.json` y
  `bajar.log`), unos 18 minutos antes del commit que trae `s23b_confirmar.py` (d1ba329, 06:14:33 UTC): el código que
  corrió no está probado que sea el commiteado (para `contar` no importa: no usa el detector).
- CÓMO SE VE EN EL VEREDICTO: ninguno hoy. Cambia el veredicto: no.
- CÓMO REPRODUCIRLO: `cat D:/goes_notas/s23/s23b/bajar.log`; `ls -la D:/goes_notas/s23/s23b/l1b D:/goes_notas/s23/s23b/acm`.
- CONFIANZA: CONFIRMADO (log, código y carpetas vacías); la rama DISCO es deducción de código y conteo. GRAVEDAD: 2.

### 310. El código que generó `estat_2026.npy` no está en el repo
- ARCHIVO:LÍNEA: `git log --all -S "estat_2026"` (primera aparición en 97bdec1, en el criterio); ningún `np.save` de esa
  ruta en ningún script de `docs/own_volcat/`.
- QUÉ PASA: el archivo congelado se escribió a mano (o con código no commiteado) 12 s antes del commit que lo declara.
  Lo recalculé con `s23_medir.Detector(ref="2026N").ESTAT` (cuadros N despejados por E1 del 21-09 al 21-11-2026, enmienda
  1 de S22b) y es idéntico: 0 píxeles-hora distintos, 81.205 de costumbre, mismo hash de arreglo. Así que el contenido es
  el que el criterio describe; lo que falta es la receta en el repo.
- CÓMO SE VE EN EL VEREDICTO: ninguno. Cambia el veredicto: no.
- CÓMO REPRODUCIRLO: `python -I f3_ensayo_confirmaciones.py estat`; salida `D:\goes_notas\s28\s28b\f3\seco\estat_recalculo.json`
  (`"igual": true, "dif_pixeles_hora": 0`).
- CONFIANZA: CONFIRMADO. GRAVEDAD: 2.

### 311. Cuatro lectores de `estat_2026.npy` sin guarda de hash
- ARCHIVO:LÍNEA: `docs/own_volcat/s26b_noche_crater/scripts/s26b_medir.py:111`, `s26a_combinado/scripts/s26a_lado_a_lado.py:145`,
  `s27a_noche_causa/scripts/s27a_lado_a_lado.py:123`, `s27b_altura_desfase/scripts/s27b_lado_a_lado.py:127`.
- QUÉ PASA: leen el congelado sin comprobarlo. Sin efecto: el mtime del archivo (05:53:03 UTC del 25-11) es anterior a
  todas esas corridas y su hash de hoy es el declarado. Ninguno escribe.
- CONFIANZA: CONFIRMADO. GRAVEDAD: 1.

### 312. `contar` reescribe el CSV entero: el conteo del gatillo no es monótono
- ARCHIVO:LÍNEA: `docs/own_volcat/s23_fondo_2025/scripts/s23b_confirmar.py:54-63`; regla de N en
  `docs/own_volcat/s22b_pluma_vs_nubes/scripts/s22b_volcat_clases.py:84-91`.
- QUÉ PASA: cada `contar` reclasifica todos los días desde el 25-11. La clase N mira ±60 min; los cuadros de las últimas
  horas del último día se clasifican sin sus vecinos futuros y pueden pasar de N a "otro" en la corrida siguiente. Un PNG
  que SSEC publica tarde también cambia el pasado. "La primera vez que sumen 20 P" depende de cuándo se corre `contar`.
- CÓMO SE VE EN EL VEREDICTO: no cambia una regla; puede mover el día de la medida. Cambia el veredicto: no.
- CONFIANZA: SOSPECHA (lectura de código; no lo vi ocurrir). GRAVEDAD: 2.

## VERIFICADO LIMPIO (con su vara)

- **Nadie miró el detector en días nuevos (vara: §2.1 del plan y S23b §6).** `f3_barrido_fechas.py` sobre todos los
  `scripts\*.py` de las nueve carpetas y de S22a y S22b: las únicas fechas ≥ 25-11-2026 son nombres de criterio en
  docstrings, el manejo legítimo de `s23b_confirmar.py:36-37`, `s26a_medir.py` (confirmar) y `s24c_rumbo.py` (medir de
  S24c, que no puede correr: `_pb()` exige `P_B` congelado y `s24c_calibracion.json` dice `"P_B": null, "abandonada": true`).
  Resultados: la única fecha nueva en `resultados\` es `s23_fondo_2025\resultados\volcat_clases_desde_25nov.csv` (clases
  de VOLCAT, permitido); las demás menciones son el nombre del criterio. Cachés de D: (s22, s23, s25, s26, s27, s28a):
  los únicos archivos con fecha nueva son PNG de VOLCAT y listados de SSEC en `D:\goes_notas\s23\volcat_png\` (149 PNG
  del 25 y 26-11, permitido); `D:\goes_notas\s23\s23b\l1b\` y `acm\` vacías; el máximo de fecha en carpetas de npz GOES es
  24-11 (`D:\goes_notas\s22\s22b\l1b` y `acm`, 22 a 24-11); todo cubo de 2026 en `.npy` tiene 65 días (21-09 a 24-11) o
  3 (22 a 24-11). No existe `s23b_vistazo.json`, `s23b_resultado.json`, `s25a_confirmacion*.json`,
  `s26a_confirmacion*.json`, `s24c_resultado.json` ni `s24c_vistazo.json` en ningún checkout bajo
  `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\Goes` ni en `git log --all`.
- **`contar` no toca el detector (vara: S23b §6, "contar no gasta la prueba").** Lectura de `s23b_confirmar.py:45-73`,
  `s23_volcat_respaldo.py` y `s22b_volcat_clases.py`: sólo baja PNG de SSEC, los decodifica y escribe la clase. Las
  importaciones de nivel de módulo (`s23_medir`, `s22b_medir`, `s22a_medir`, `h24_medir`, `h29_comun`) sólo cargan grillas
  fijas (latlon, DEM); no hay llamada a `Detector`, `m1_cuadro`, `disparos` ni a cubos GOES. `B.clases()` del desarrollo
  corta en `ND` = 65 días (`s22b_medir.py:160`), así que el CSV de días nuevos no entra a ningún análisis de desarrollo.
- **El estado congelado es el declarado (vara: S23b §2, S25a conf §1, S26a §1; los dos hashes, como pide el plan).**
  `sha256(tobytes)` = `e0f093eb6e441cc4...` = `SHA_ESTAT` de `s23b_confirmar.py:39` y de los criterios; forma 144 × 7.802,
  `bool`, 81.205 verdaderos (criterio S23b línea 30). mtime 2026-11-25 05:53:03 UTC, 12 s antes del commit 97bdec1
  (02:53:15 -03) y nunca reescrito; ningún script lo escribe; recalculado desde el desarrollo es idéntico (310).
- **Criterios y código de las confirmaciones no cambiaron desde que se congelaron (vara: commit que los declara).**
  `git diff d1ba329 8894722 --stat` sobre `s23_fondo_2025/scripts`, `s22a`, `s22b`, `h23`, `h24`, `h29`: vacío;
  `git diff 677c232 8894722` sobre `s26a` y `s25a` scripts: vacío; `git diff 08ba80a` (criterio de confirmación S25a) y
  `28f963b` (criterio S26a): vacíos; el criterio S23b sólo suma las 6 líneas de §6 (af46f12) desde 97bdec1.
- **Los tres confirmadores corren de punta a punta y reproducen el desarrollo (vara: cifras por día de los resultados de
  desarrollo, misma regla).** Sobre 08 a 11-11 (arranque 07-11), con `s23b_confirmar.medir` y `s26a_medir.confirmar`
  originales:
  - S23b contra `s23_fondo_2025/resultados/sensibilidad_costumbre_2026.json` (misma regla, costumbre de 2026): 08-11
    13 P, 13 evaluados, 9 alcanzados, 18 disparos, tajadas `[0,0,0,0,13,5,0,...]`; 10-11 12, 2, 0, 0; 11-11 3, 3, 3, 4,
    tajadas `[0,0,0,0,2,0,2,...]`: idénticos. Instrumento sin falla (720 de 720 cuadros).
  - S25a contra `s25a_crater/resultados/s25a_resultado.json`: 08-11 13, 13, 0, 52; 09-11 0, 0, 0, 4; 10-11 12, 8, 8,
    35; 11-11 3, 3, 0, 19: idénticos (pese a que el cubo de la confirmación usa la mediana de Planck de los días que lee y
    el de desarrollo la del desarrollo).
  - S26a (unión a p* = 4,75) contra `s26a_combinado/resultados/s26a_desarrollo.json`: anillo, zona y unión idénticos
    los cuatro días (anexo B).
- **Veredictos implementados en el orden escrito (vara: S23b §4, S25a conf §3, S26a §5).** `s23b_confirmar.py:204-213` y
  `s26a_medir.py:404-413`: INVÁLIDA (instrumento) antes que NO DECIDIBLE (menos de 10 P evaluados o de un solo día) antes
  que CONFIRMA (p25 ≤ 0,01, R ≥ 0,40 o 0,25 en S25a, pN ≤ 0,05) antes que PARCIAL (p25 ≤ 0,01) antes que NO CONFIRMA. El
  día 0 (24-11) sólo da persistencia (`s23b_confirmar.py:178`, `s26a_medir.py:402`). pN con N a ±60 min de algún P
  evaluado (S23b §4). Azar r25 de S25a = el de su medida (mismo `azar` sobre el seco por día; el ensayo da los mismos
  disparos). p* = 4,75 leído de `s26a_seco.json` (S26a §2). Orden S23b, S25a, S26a exigido por existencia de archivos
  (`s26a_medir.py:367-370`).
- **Gatillo implementado como se escribió (vara: S23b §6, S26a §5).** `MIN_P, MIN_DIAS_P = 20, 2`
  (`s23b_confirmar.py:41`), contados sobre los días del CSV desde el 25-11 (el 24-11 no se escribe en el CSV:
  `s23b_confirmar.py:60`); el mismo gatillo en `s26a_medir.py:363-366` con las constantes de `s23b_confirmar`.

## SIN DATO

- Qué hacen los confirmadores con días nuevos reales (prohibido correrlos).
- Si los commits de los criterios se empujaron antes de los datos (F1; git no lo registra).
- Si la costumbre de VOLCAT "otro" y "N" del CSV de días nuevos está bien clasificada (es de la regla de H9; F2).
- El efecto exacto de 301 a 306 sobre el veredicto: depende de los días de la medida.

## SEGUIMIENTO (fuera de F3, una línea cada uno)

- F2: en el ensayo sobre 08 a 11-11, S23b tiene sólo 2 N a ±60 min de sus P (pN 0,147 sin poder) y la zona da pN 0,95;
  el pN de las confirmaciones va a depender de cuántos N haya a ±60 min de los P (poder de pN no declarado).
- F1: `contar` y `bajar` de S23b corrieron unos 18 min antes del commit de `s23b_confirmar.py` (309).

## Anexo A. Línea base de hashes de las entradas sin guarda (26-11-2026, `f3_hashes_entradas.py`)

Ver `D:\goes_notas\s28\s28b\f3\hashes_entradas.json` (SHA-256 completo). Prefijos:

| Archivo | mtime UTC | SHA-256 (16) |
|---|---|---|
| `D:\goes_notas\s23\s23b\estat_2026.npy` (bytes del archivo) | 2026-11-25 05:53:03 | 8e0768bfbe6d310a |
| `D:\goes_notas\s23\s23a\r25_acm.npy` | 2026-11-25 05:26:52 | 50403642870dc634 |
| `D:\goes_notas\s23\s23a\r25_m1.npy` | 2026-11-25 05:26:52 | 89183a5d88ebfff6 |
| `D:\goes_notas\s23\s23a\r25_bt11.npy` | 2026-11-25 05:26:52 | 3647637ef38f2843 |
| `D:\goes_notas\s25\s25a\r25_acm.npy` | 2026-11-25 12:12:21 | 50403642870dc634 |
| `D:\goes_notas\s25\s25a\r25_btd.npy` | 2026-11-25 12:12:21 | b1d8c1134ba1a89d |
| `D:\goes_notas\s25\s25a\n26_btd.npy` | 2026-11-25 12:12:27 | 092aa4e1a8dbdc6a |
| `D:\goes_notas\s22\s22b\dev_acm.npy` | 2026-11-24 16:04:37 | 2a910dfbbe6e1e52 |
| `D:\goes_notas\s22\s22b\dev_bt11.npy` | 2026-11-24 16:04:37 | 31a65b96e6410828 |
| `D:\goes_notas\s22\s22b\dev_btd.npy` | 2026-11-24 16:04:37 | 85bef60f2e5cdd0a |
| `D:\goes_notas\s22\s22b\dev_co.npy` | 2026-11-24 16:04:37 | 52472c33b992ce90 |
| `D:\goes_notas\s22\s22b\dev_m1.npy` | 2026-11-24 16:14:10 | cda62352b252b320 |
| `D:\goes_notas\s22\s22b\nuevo_acm.npy` | 2026-11-24 16:52:47 | 5a9b135eebb9eda3 |
| `D:\goes_notas\s22\s22b\nuevo_bt11.npy` | 2026-11-24 16:52:47 | 2786e5fef21713e0 |
| `D:\goes_notas\s22\s22b\nuevo_m1.npy` | 2026-11-24 16:52:47 | 24be9096f82ba4e4 |
| `D:\goes_notas\local_f3a7d295\cache_rescatada\reproducir_volcat\latlon.npz` | 2026-11-20 14:55:29 | 79350e4b01cc86be |
| `D:\goes_cache\etapa3_chillan\dem_ventana.npz` | 2026-11-21 19:10:15 | 409e9cce836788c5 |
| `docs/own_volcat/s26a_combinado/resultados/s26a_seco.json` (p* = 4,75) | (checkout) | b7955c2e9501cd24 |
| `docs/own_volcat/calor_rayos/resultados/frames_calor.csv` | (checkout) | 1824ed18dfdfd6da |
| `docs/own_volcat/s22b_pluma_vs_nubes/resultados/volcat_clases_22a24nov.csv` | (checkout) | 53e0135cd3c4667a |
| `docs/own_volcat/s22b_pluma_vs_nubes/resultados/seco.json` | (checkout) | c190111672f273df |

## Anexo B. Ensayo de S26a (unión a p* = 4,75) contra `s26a_combinado/resultados/s26a_desarrollo.json`

`python -I f3_ensayo_confirmaciones.py s26a`; salida `D:\goes_notas\s28\s28b\f3\seco\s26a_comparacion.json`. Por día:
P evaluados, P alcanzados y disparos de anillo, zona y unión.

| Día | Anillo | Zona | Unión | ¿Igual al desarrollo? |
|---|---|---|---|---|
| 08-11 | 13, 9, 18 | 13, 0, 52 | 13, 9, 70 | sí |
| 09-11 | 0, 0, 0 | 0, 0, 4 | 0, 0, 4 | sí |
| 10-11 | 2, 0, 0 | 8, 8, 33 | 8, 8, 33 | sí |
| 11-11 | 3, 3, 4 | 3, 0, 19 | 3, 3, 22 | sí |

Instrumento sin falla. Rótulo del vistazo sobre estos días ya vistos (no decide nada): CONFIRMA, 20 de 24, p25 8,6e-21,
pN 0,0012 con 56 N cerca. El de S25a sobre los mismos días: PARCIAL, 8 de 24, p25 4,1e-6, pN 0,95. El de S23b: PARCIAL,
12 de 18, p25 2,3e-12, pN 0,147 con 2 N cerca.
