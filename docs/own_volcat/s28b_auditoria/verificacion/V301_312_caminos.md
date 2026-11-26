# V301 a V312: caminos de ruptura, escritos antes de abrir el código

Verificador de los hallazgos 301, 302, 303, 304, 305, 306, 307, 308 y 312 (código de las tres confirmaciones
congeladas: S23b, S25a, S26a). Esta lista se escribe antes de leer los criterios y los scripts. Sólo conozco el título
de cada hallazgo. Cada camino es una forma en que la afirmación podría estar mal; después se comprueba uno por uno.

## Caminos comunes a todos

- C0a. La copia del worktree puede estar atrasada frente a `main` o frente a lo que la coordinadora corre de verdad
  (otra carpeta, otra rama). Comprobar qué archivo se ejecuta cada día y desde dónde.
- C0b. El criterio escrito puede tener una versión posterior (enmienda, anexo, otro .md) que ya cubre el punto.
- C0c. Puede haber un segundo guion (envoltorio, tarea programada, coordinadora) que agrega la guarda que al script
  le falta. La guarda puede vivir fuera del script.
- C0d. El hallazgo puede describir una rama del código que no se alcanza con los datos reales.
- C0e. El PLAN.md puede haber cambiado desde su commit, y con él la vara.

## 301: gatillo cuenta P de días sin GOES; I1 llega sólo hasta el último cuadro bajado

- C301a. El gatillo puede contar P sólo en días que ya tienen cubo GOES (intersección), y entonces la primera mitad
  es falsa.
- C301b. I1 puede comparar contra el calendario esperado (cada 10 min hasta el último P de VOLCAT), no contra el
  último cuadro bajado; entonces un último día sin GOES sí invalida.
- C301c. Puede existir otra comprobación (I2, I3, conteo de P evaluados contra P del gatillo) que detecte los P sin
  evaluar aunque I1 no lo haga.
- C301d. El día faltante en medio puede no dar INVÁLIDA sino otra cosa (se salta, se rellena con NaN, falla con
  excepción). Hay que ensayarlo con días ya vistos.
- C301e. El criterio puede decir de forma explícita qué pasa con una medida INVÁLIDA (se repite o se gasta). Leer los
  tres criterios completos y no sólo el párrafo de la regla.
- C301f. "Medir" puede bajar el GOES que falta por su cuenta antes de evaluar, y entonces no hay día sin datos.

## 302: "en esa misma ocasión y con los mismos datos" sin implementar

- C302a. S25a y S26a pueden leer del resultado de S23b la lista de días o de cuadros medidos y restringirse a ella.
- C302b. Pueden compartir el mismo cubo en disco, escrito una sola vez por S23b, y eso equivale en la práctica a
  "los mismos datos" si nadie vuelve a bajar. Comprobar si el cubo se puede regenerar o ampliar entre corridas.
- C302c. El resultado de S23b puede guardar un hash del cubo y del CSV de clases, y los otros dos compararlo.
- C302d. La frase del criterio puede querer decir otra cosa (misma ocasión = mismo gatillo), no identidad de bytes.
- C302e. Puede haber un script único que corre las tres seguidas y entonces no hay ventana para que cambien los datos.

## 303: "una sola vez" y la regla del vistazo, sin guarda

- C303a. El script puede negarse a correr si ya existe su archivo de resultado.
- C303b. Puede escribir una bitácora de corridas (fecha, días, conteo) y comparar contra ella.
- C303c. La regla del vistazo puede no estar en el criterio con esas palabras; comprobar el texto exacto.
- C303d. La guarda puede existir pero ser evitable (bandera `--forzar`, borrar un archivo). Eso sería "en parte".
- C303e. Puede existir guarda en S23b y no en S25a o S26a, o al revés.

## 304: rótulo del umbral sin corregir (p25 entre 0,0033 y 0,01) falta en S23b y se aplica a PARCIAL

- C304a. El rótulo puede estar exigido sólo para S25a o S26a según el criterio, y entonces que falte en S23b no es
  defecto.
- C304b. S23b puede no usar p25 ni ese tipo de umbral; el rótulo no le correspondería.
- C304c. El código puede aplicar el rótulo sólo cuando el veredicto es ALCANZA o CONFIRMA; comprobar la condición.
- C304d. Los valores 0,0033 y 0,01 pueden no ser los que el criterio escribe (0,01/3). Comprobar las constantes.
- C304e. El criterio puede decir de forma expresa que el rótulo acompaña cualquier veredicto, y entonces PARCIAL con
  rótulo no es un defecto.

## 305: sólo estat_2026.npy tiene hash

- C305a. Los cachés de 2025 (base, umbral, nublado de costumbre) pueden tener hash en otro archivo (manifiesto,
  estado.json) que el script compara.
- C305b. Pueden recalcularse de forma determinista desde un cubo que sí tiene hash, y entonces el hash del derivado
  sobra.
- C305c. r25, el azar de la unión y p* pueden ser constantes escritas en el código o en el criterio (congeladas por
  git) y no recalcularse.
- C305d. `latlon.npz` y `dem_ventana.npz` pueden estar en el repo (con historial git) y no en D:.
- C305e. El recálculo puede depender de una semilla fija y dar siempre lo mismo; comprobar si hay azar sin semilla.
- C305f. El hash de estat_2026 puede cubrir de hecho a los demás (si estat se derivó de ellos, un cambio aguas
  arriba no cambia el estat ya guardado, pero sí cambia lo que se compara contra él).

## 306: cobertura de ACMF de los días nuevos sin comprobar

- C306a. I1 puede contar también los archivos ACMF, no sólo las bandas.
- C306b. Un cuadro sin ACMF puede quedar fuera por construcción (NaN, no evaluable) y contarse como no evaluable, lo
  que deja rastro en el resultado.
- C306c. Un cuadro sin ACMF puede tratarse como despejado (el peor caso: cambia disparos) o como nublado (baja el
  denominador). Hay que ver cuál.
- C306d. El detector puede no usar ACMF en la confirmación (sólo el nublado de costumbre de 2025).
- C306e. La bajada puede fallar con ruido si falta ACMF, y entonces la cobertura queda comprobada aguas arriba.

## 307: el gatillo cuenta P y no P evaluables

- C307a. El criterio puede definir el gatillo como "20 cuadros P" a secas, y entonces el código cumple el criterio y
  el hallazgo es sobre el criterio, no sobre el código.
- C307b. El script puede tener un segundo umbral (mínimo de evaluables) que da SIN PODER o INVÁLIDA en vez de un
  veredicto.
- C307c. Si los evaluables son pocos, puede que el veredicto salga igual pero con un rótulo de poder bajo.
- C307d. "Gastar la medida" depende de 303 y de 301e: si una medida sin poder no se considera gastada por criterio,
  el efecto es menor.

## 308: SHA-256 "de los bytes" contra hash del arreglo, y sólo 16 hexadecimales

- C308a. El criterio puede decir "del arreglo" o dar el modo de cálculo; comprobar la frase exacta.
- C308b. El hash declarado puede coincidir con el del archivo .npy completo; calcular los dos sobre el archivo real.
- C308c. El código puede comparar los 64 hexadecimales y sólo imprimir 16.
- C308d. Efecto práctico: `tobytes()` no cubre dtype, forma ni orden. Comprobar si un arreglo con otra forma u otro
  dtype y los mismos bytes pasaría la guarda y cambiaría el resultado.

## 312: `contar` reescribe el CSV de clases entero y el conteo puede bajar

- C312a. `contar` puede escribir en modo de agregar, o fusionar con lo anterior, y no reescribir.
- C312b. Puede reescribir pero desde una fuente local que sólo crece (PNG ya bajados), y entonces el conteo no baja.
- C312c. La clasificación P puede depender de algo que cambia entre corridas (ventana rodante del sitio de SSEC,
  umbral, reclasificación de cuadros ya vistos). Comprobar de dónde sale cada fila.
- C312d. Puede haber respaldo del CSV anterior o una comprobación de monotonía.
- C312e. El gatillo puede leer otro archivo que no es ese CSV.

## Qué cuenta como resultado

Para cada hallazgo: CONFIRMADO, CONFIRMADO EN PARTE (con la parte), REFUTADO o SIN DATO, con gravedad propia 1 a 5 y
la evidencia de esta sesión. Además: si puede cambiar el veredicto de una confirmación el día de la medida, cuál y
cómo, y si el arreglo tiene que ir antes de la medida. Los ensayos van sobre copias en `D:\goes_notas\s28\s28b\v301\`
apuntadas a días ya vistos (hasta el 24-11-2026). No se corre `medir` ni `contar` sobre datos reales.
