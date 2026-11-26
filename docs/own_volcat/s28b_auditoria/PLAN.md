# S28b: auditoría de lo medido de S23 a S28a. Plan pre-registrado, 26-11-2026

Escrito, commiteado y empujado **antes** de lanzar un solo auditor. Cada verificador comprueba con
`git diff <commit de este plan> -- docs/own_volcat/s28b_auditoria/PLAN.md` que la vara no cambió. Lo que se agregue
después va en una enmienda fechada y rotulada.

- **Base medida**: `origin/main` = `8894722b0b2a4184dead88ea5fdfdec2618d3401` (26-11-2026 03:05 UTC, hora del servidor).
- **Pedido**: Nicolás, 26-11: "audita todo lo que hemos hecho últimamente". Encargo de la coordinadora S28.
- **Auditar no es arreglar**: ningún script, resultado ni informe de las carpetas auditadas se modifica. Lo que se
  encuentre va al informe con su reproducción.

## 0. Por qué esta auditoría

Entre el 24 y el 25-11 nueve sesiones en paralelo midieron con criterio previo y fusionaron nueve PR (125 a 134). De
esas medidas sale lo que se le va a mostrar a Nicolás y, si confirma, lo que entraría al dashboard como capa
experimental de un SDA en producción: el detector combinado S26a (zona del cráter O anillo) y tres confirmaciones
congeladas (S23b, S25a, S26a) que se miden **una sola vez** en días nuevos. Un error ahí no da error: da un veredicto
plausible. Un "ALCANZA" que en realidad es azar con tres chances, un pre-registro que se escribió después del dato o una
confirmación congelada que no se puede ejecutar tal cual se descubren el día de la medida única, cuando ya no hay
vuelta. Esta auditoría busca eso antes.

**Eje nuevo** (§4 de la guía): ninguna auditoría anterior del proyecto miró las pruebas propias del detector (las de
jun, jul, ago y nov-2026 miraron el dashboard, la física de altura y la cadena VOLCAT). Los cuatro frentes son eje nuevo.

## 1. Alcance

**Objeto** (todo en `docs/own_volcat/`): `s23_fondo_2025`, `s24_dia14_noche`, `s25a_crater`, `s25b_fondo_2024`,
`s26a_combinado`, `s26b_noche_crater`, `s27a_noche_causa`, `s27b_altura_desfase`, `s28a_vecinas`: criterios, scripts,
`resultados/` e `INFORME.md`; los bloques de `STATUS.md` de esas sesiones (0, 0-prev19 a 0-prev27) y la historia de git
de esas carpetas.

**Dependencias que se leen como objeto** (porque las importan): `s22a_detector_sectores/scripts/s22a_medir.py`,
`s22b_pluma_vs_nubes/scripts/s22b_medir.py` y `s22b_volcat_clases.py`, `calor_rayos/resultados/frames_calor.csv`
(regla H9), los cachés en `D:\goes_notas\s22\`, `D:\goes_notas\s23\`, `D:\goes_notas\s25\`, `D:\goes_notas\s26\`,
`D:\goes_notas\s27\`, `D:\goes_notas\s28\s28a\` (sólo lectura).

**Fuera de alcance**: S29a y S29b (corren; sus carpetas no se tocan ni se leen), el dashboard, H1 a H29, S22 salvo lo
que S23 a S28a importan, la carpeta principal del repo (rama `audit/2026-11-previa-local`).

## 2. Prohibiciones (valen para todo agente de esta auditoría)

1. No correr el detector (anillo, zona, unión, ni ningún `Detector`, `disparos`, `m1_cuadro` sobre cuadros) en días
   posteriores al 24-11-2026 23:50 UTC, ni `s23b_confirmar.py medir`, ni abrir cubos o cuadros GOES de esos días.
   Por qué: las tres confirmaciones se miden una vez; un vistazo las retrasa (S23b §6). `s23b_confirmar.py contar`
   tampoco se corre: lo corre la coordinadora.
2. No modificar nada fuera de `docs/own_volcat/s28b_auditoria/` (repo) y `D:\goes_notas\s28\s28b\` (pesado). Nada de
   commit, push, merge ni ramas: eso lo hace el orquestador.
3. No copiar al repo PNG ni datos de SSEC/VOLCAT.
4. Disco: no bajar datos nuevos de NOAA. Si `D:` baja de 8 GB libres, parar y escribirlo. Tope por agente: 2 GB en
   `D:\goes_notas\s28\s28b\<frente>\`.
5. Las copias para mutar (por ejemplo `estat_2026.npy`) se hacen en `D:\goes_notas\s28\s28b\<frente>\`, nunca sobre el
   original.

## 3. Definiciones comunes (la vara; idénticas para los cuatro frentes)

- **Hallazgo**: una diferencia comprobada con una herramienta propia en la sesión entre (a) lo que un criterio, informe o
  `STATUS.md` afirma y (b) lo que el código hace o lo que los datos dan, o un defecto de diseño estadístico o físico que
  hace que un veredicto no signifique lo que su nombre dice. Una opinión sin reproducción no es hallazgo: es SOSPECHA.
- **Veredicto**: cada rótulo que una sesión puso a su medida (PARCIAL, CONFIRMA, ALCANZA, INVÁLIDA, NO DECIDIBLE, SIN
  PODER, AGUANTA, COMPARABLE, INTERMEDIO, MIXTO, NO CONCLUYENTE, NO, NO DECIDIBLE, etc.), con su sección y su archivo.
- **Cambia un veredicto**: aplicando la regla escrita en el propio criterio, con el número o el código corregido, el rótulo
  pasa a otro. Se dice cuál y cómo. Si el rótulo no cambia pero lo que promete sí (por ejemplo un p que sube de 1e-19 a
  1e-3), es "no cambia el veredicto, cambia su lectura". Si depende de una medida que no se hizo, "cambia: SIN DATO".
- **Post hoc**: todo lo que entra a un resultado y no está en un criterio commiteado antes del commit de la medida.
- **Antes de la medida**: la fecha de autor y de commit del criterio es anterior a la del primer commit que trae
  `resultados/*.json` de esa medida, y el commit del criterio está en el remoto (rama de la sesión o main). Se comprueba
  con `git log --format="%H %ad %cd" --date=iso`. El empuje no deja rastro en git: si no se puede probar, se dice SIN DATO
  y no se da por malo.
- **Tolerancias** (para comparar cifras de un informe con `resultados/*.json` o con una recomputación): conteos, exactos;
  fracciones, ±0,001 absoluto o el redondeo con que el informe las imprime, lo mayor; valores p, mismo lado de todo umbral
  del criterio y dentro de un factor 2 si p ≥ 1e-4 (bajo 1e-4 basta el orden de magnitud). Por qué: los umbrales que
  deciden son 0,01, 0,05, 0,40 y 0,50; ninguna tolerancia puede mover una cifra al otro lado.
- **Gravedad 1 a 5** se mide por la decisión que sostiene: 5 cambia un veredicto que decide lo que se muestra a Nicolás o
  una confirmación congelada; 4 cambia un veredicto de desarrollo o la lectura de uno que decide; 3 cifra o rótulo
  equivocado sin cambio de decisión; 2 documentación que miente sin efecto; 1 estilo.
- **Confianza**: CONFIRMADO (lo reprodujo con una herramienta en su sesión) o SOSPECHA.

## 4. Frentes (disjuntos), qué cuenta como hallazgo y su línea base roja

Cada frente trae una **línea base roja**: un defecto ya conocido de su eje que su instrumento tiene que volver a
encontrar antes de que su cero valga. Si no lo encuentra, el frente informa su instrumento como ciego y su "limpio" no
cuenta.

### F1. Cierres y pre-registro (IDs 101 a 199)

Para cada veredicto de S23 a S28a: (a) el criterio se commiteó antes del commit de la medida (fechas y hash) y
`git diff <criterio>..<medida> -- <criterio>` está vacío o sus cambios están rotulados como enmienda previa; (b) el código
implementa lo que el criterio escribe (umbral, percentil, persistencia, días, franjas, mínimos de pozo, ventanas ±min,
compuerta, definición de evaluado); (c) cada cifra del `INFORME.md` y del bloque de `STATUS.md` sale de
`resultados/*.json` dentro de la tolerancia; (d) el nombre del veredicto no promete más que lo que la regla prueba;
(e) lo post hoc está rotulado; (f) el orden de las reglas de veredicto del criterio se respetó (INVÁLIDA antes que todo).
Censo completo: una fila por veredicto en una tabla, también los limpios.

**Línea base roja F1**: el control positivo A de S24 (`s24_dia14_noche`) es INVÁLIDO por su propia regla (huella del
08-11 diluida en el anillo entero). El instrumento de F1 (criterio contra resultado) tiene que marcar A como inválido sin
leer el informe de S24 primero.

### F2. Estadística e instrumento (IDs 201 a 299)

Por regla de §3b de la guía: (a) **mismo número de oportunidades**: "alcanzado" cuenta un cuadro si dispara él, el
anterior o el siguiente (`s22b_medir.alcanzado`); comprobar que el azar (r25, r24, el de la unión, el de S25a) se calcula
con la misma definición, los mismos bordes de día, los mismos cuadros evaluados y la misma compuerta que los P;
(b) **dependencia**: p25 y pN suponen cuadros independientes; los P vienen en episodios y en pocos días. Recomputar el
azar a nivel de día o de episodio (remuestreo o permutación por días) para cada veredicto que decide (S23a, S25a, S26a
desarrollo, S25b) y decir si el rótulo cambia; (c) **cobertura pareja**: cuadros evaluados por año (2024, 2025, 2026) y
franja de 3 h, y qué fracción de los P se evalúa contra la de los N; (d) **pisos de nulos por permutación**
(1/(n+1) contra el umbral) en todo criterio con permutación o remuestreo; (e) **poder declarado** y si el veredicto lo
usa; (f) **selección**: clases P de VOLCAT con la regla de H9 (cobertura de días de `frames_calor.csv` y del CSV de 22 a
24-11 contra la ventana 21-09 a 24-11 que los informes dicen usar); (g) **régimen**: GOES-16 (2024) contra GOES-19
(2025, 2026), versiones de ACMF, cambio de hora o de modo de escaneo dentro de las ventanas; (h) **fuga de desarrollo a
prueba**: que el ensayo en seco "cada día sin sí mismo" saque de verdad ese día de la base, del umbral y del nublado de
costumbre, y que ninguna confirmación congelada use números elegidos con los días que dice no haber visto.

**Línea base roja F2**: el umbral de poder de S27a (p ≤ 0,01 con 60 corrimientos, piso 1/61 = 0,0164) es inalcanzable.
El instrumento de pisos de F2 tiene que encontrarlo solo. Segunda: el pN por hora de S23a con cola degenerada (azar
estimado 0 en horas con pocos N), que S23b reconoce en su §4.

### F3. Congelamiento (IDs 301 a 399)

(a) Ningún script ni resultado de S23 a S28a mira el detector en días posteriores al 24-11-2026 23:50 UTC (barrido de
literales de fecha, rangos de días, `glob` de carpetas, mtimes y contenido de `resultados/` y de los cachés de `D:`);
(b) el estado congelado `D:\goes_notas\s23\s23b\estat_2026.npy` coincide con el SHA declarado en `s23b_confirmar.py` y en
los criterios (comprobar qué se hashea: los bytes del archivo o `estat.tobytes()`; los dos), y nada lo reescribió después
de su commit (mtime); (c) las tres confirmaciones (S23b, S25a, S26a) y su orden fijado en
`s26a_combinado/criterio_2026-11-25.md` §5 son ejecutables tal cual: existe el código de cada una, sus entradas existen,
la base, el umbral y p* que usan están fijados en archivos y no se recalculan con los días nuevos, y el gatillo
(20 P en 2 días) está implementado como se escribió. **Sin correr `medir`**: lectura de código, dry run sobre días ya
vistos sólo si el script lo permite sin tocar días nuevos, o una copia del script en `D:` con las rutas de entrada
apuntando a días ya vistos.

**Línea base roja F3**: mutación. Copiar `estat_2026.npy` a `D:\goes_notas\s28\s28b\f3\`, cambiar un byte y comprobar
que la guarda de `s23b_confirmar.py` (la línea del `assert hashlib.sha256(...)`) falla por aserción sobre la copia y pasa
sobre el original. Segunda: el barrido de fechas tiene que encontrar el manejo legítimo de días nuevos dentro de
`s23b_confirmar.py` (control positivo de que el barrido ve fechas posteriores al 24-11).

### F4. Magnitudes y geometría (IDs 401 a 499)

Censo de toda constante física o geométrica que decide (radios de la zona y del anillo, 45 km del control, ±300 m de
cota, ±0,5 K de BT11, tajadas de 30°, bloque 3 × 3, km por grado, tamaño de píxel ABI en Chillán, Antuco y Longaví,
coordenadas de las cumbres, unidades de BTD y de los umbrales, paralaje y cota) con su espacio de unidades, dónde se
define y si vale fuera de Chillán (S27a, S28a generalizan a Antuco y Longaví). Preguntas: ¿el radio de 4 km de la zona
contiene 11 píxeles con la geometría real del píxel en Chillán?; ¿el paralaje de una pluma de 1 a 2 km sobre una cumbre de
~3,2 km la saca de la zona o la cambia de tajada?; ¿las cumbres de Antuco y Longaví y sus anillos usan sus coordenadas
y cotas, no las de Chillán?; ¿km por grado depende de la latitud donde debe?; ¿2024 (GOES-16) usa la misma grilla y la
misma georreferencia?

**Línea base roja F4**: la constante de Chillán escondida en `Detector.base` (largo del anillo `M.NA`) que S28a encontró
al generalizar. El censo de F4 tiene que volver a encontrarla, o encontrar que S28a la corrigió y dónde.

## 5. Corte de verificación (fijado ahora)

Pasa por un verificador de contexto limpio todo hallazgo con gravedad ≥ 4, todo el que el auditor marque como "cambia un
veredicto" (sí o SIN DATO) y todo el que toque una confirmación congelada, aunque su gravedad sea baja. Los de gravedad
1 a 3 que no cumplen eso se publican con su conteo y rotulados "sin verificar". El verificador recibe sólo el título,
el archivo:línea o script:salida y la pregunta; no el razonamiento del auditor. Escribe sus caminos de ruptura antes de
releer. Un verificador por hallazgo grave, o uno por frente si los graves de un frente comparten archivo; IDs 901 en
adelante para lo que encuentre de nuevo.

**Modelos**: auditores con el modelo de esta sesión (Opus 5.5); verificadores con otro modelo (Fable), para no heredar el
mismo sesgo de lectura. Se declara en el informe el modelo y el esfuerzo de cada agente.

## 6. Entregables

- `docs/own_volcat/s28b_auditoria/fN_*/INFORME_FN.md` de cada auditor y sus scripts de medición (el instrumento va al
  repo, regla 7 de la guía); lo pesado en `D:\goes_notas\s28\s28b\fN\`.
- `docs/own_volcat/s28b_auditoria/INFORME.md` (forma de §5 de la guía: encabezado con commit, modelos, qué no se miró;
  en una pantalla; hallazgos con ID final; VERIFICADO LIMPIO con su vara; SIN DATO; seguimientos) y `hallazgos.csv`
  (escrito con el módulo `csv`).
- Primera línea del informe: cuántos hallazgos cambian un veredicto.
- Bloque S28b en `STATUS.md`; PR contra `main` sin fusionar (lo revisa S28).

## 7. Preámbulo del auditor (se pega entero en cada prompt; adaptado de `ARSAND\docs\_prompts\PREAMBULO-AUDITOR.md`)

```text
Contexto: esto es el detector propio de plumas de Nevados de Chillán del proyecto Goes (SERNAGEOMIN, OVDAS), un
Sistema de Decisiones Automatizadas bajo la Resolución CPLT 372. De estas pruebas sale qué detector se le muestra a
Nicolás (geólogo del OVDAS) contra VOLCAT y, si confirma en días nuevos, qué entra al dashboard que mira el turno de
vigilancia volcánica. Un error aquí no da error: da un veredicto plausible. Un ALCANZA que es azar, un pre-registro
escrito después del dato o una confirmación congelada que no corre tal cual se descubren el día de la medida única,
cuando ya no hay vuelta. No estás revisando código de laboratorio: estás revisando lo que decide si un detector se cree.

Límite: auditar no es arreglar. No modifiques ningún archivo de las carpetas auditadas. Tu entregable es tu evaluación.
Los arreglos los decide quien orquesta, en tareas aparte.

Regla obligatoria: antes de reportar, audita cada afirmación contra un resultado de herramienta de TU propia sesión.
Sólo reporta lo que puedas respaldar con evidencia archivo:línea que leíste o con la salida de un comando que corriste;
si algo no lo verificaste, dilo. Nada de citar de memoria: si escribes un número de línea o una cifra, tienes que haberla
visto en la salida de una herramienta tuya en esta sesión. Si una afirmación te parece obvia pero no la comprobaste,
márcala SOSPECHA sin ninguna vergüenza. Reporta todo lo que encuentres, con su confianza y su gravedad: el filtrado lo
hace otro después; no te autocensures por gravedad.

Formato de cada hallazgo:
- ID (en tu rango) y TÍTULO en una línea
- ARCHIVO:LÍNEA (ruta exacta) o SCRIPT:SALIDA
- QUÉ PASA: el defecto, en una o dos frases
- CÓMO SE VE EN EL VEREDICTO: qué rótulo o cifra queda mal, y si cambia un veredicto (sí, no, SIN DATO), cuál y cómo
- CÓMO REPRODUCIRLO: los comandos exactos, con la salida cruda o la ruta de la salida
- CONFIANZA: CONFIRMADO (lo reprodujiste) o SOSPECHA
- GRAVEDAD 1 a 5 (5 cambia un veredicto que decide lo que se muestra a Nicolás o una confirmación congelada)

Ordena por gravedad, lo peor primero.

Cierra siempre con una sección VERIFICADO LIMPIO: qué miraste y está sano, y contra qué vara lo verificaste (una
verificación contra la vara equivocada no podía fallar). Y una sección SIN DATO: lo que no pudiste medir y por qué. En
este proyecto saber qué no hay que volver a mirar vale tanto como los hallazgos.
```
