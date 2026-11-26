# V208 y V211: caminos de ruptura, escritos antes de abrir los criterios y los datos

Verificador de los hallazgos 208 y 211, agregados por la coordinadora a la tanda 301 a 312. Esta lista se escribe
antes de leer los criterios, los CSV de clases y el código. Sólo conozco el título y el lugar de cada hallazgo.

## 208: las clases de VOLCAT cubren 20-10 a 19-11 más 22 a 24-11, no 21-09 a 24-11; estat_2026.npy sale de 31 días

- C208a. Los criterios pueden distinguir dos ventanas: la de las clases de VOLCAT (días con cuadros P o N) y la del
  nublado de costumbre de 2026 (que se calcula con ACMF y no necesita VOLCAT). Si es así, "21-09 a 24-11" puede
  referirse al fondo o al cubo GOES, y no a las clases.
- C208b. El estat_2026.npy puede calcularse sobre todos los cuadros del cubo de 2026 y no sólo sobre los cuadros que
  tienen clase de VOLCAT. Hay que leer el código que lo escribe y ver qué máscara de días usa.
- C208c. Puede haber un tercer CSV de clases (otra carpeta, otra corrida) que cubra del 21-09 al 19-10 y que el
  hallazgo no vio. Buscar todos los CSV de clases y lo que de verdad lee el script.
- C208d. `frames_calor.csv` puede tener filas desde el 21-09 con una clase que el hallazgo no contó (por ejemplo,
  días sin detección rotulados de otra forma). Contar días y fechas extremas con un comando.
- C208e. El número 31 puede estar mal contado: 20-10 a 19-11 son 31 días, y 22 a 24-11 son 3 más (34). Comprobar
  cuántos días distintos entran de verdad al estat y cuántos dicen los criterios (62 o 65).
- C208f. El estat congelado puede no depender de las clases de VOLCAT en absoluto (si es el nublado de costumbre por
  hora del día de todo el cubo). En ese caso la segunda mitad del hallazgo es falsa aunque la primera sea cierta.
- C208g. El cubo GOES de 2026 en D: puede cubrir menos días que la ventana declarada. Medir las fechas del cubo.
- C208h. El criterio puede haber sido enmendado después (anexo, nota) con la ventana real.
- C208i. Efecto: aunque el texto esté mal, el estat congelado es un archivo fijo con hash. La confirmación corre con
  el archivo, no con el texto. Hay que separar "el criterio describe mal su insumo" de "el veredicto cambia".
- C208j. Si el estat sale de menos días, el nublado de costumbre es más ruidoso y puede cambiar qué píxeles y horas
  se consideran evaluables en los días nuevos. Medir, si se puede, cuánto cambia el estat con 31 contra 62 días
  usando sólo días ya vistos.

## 211: el poder se declara pero ningún veredicto lo usa; el poder de la unión a p* = 4,75 no se midió

- C211a. El código puede tener una rama SIN PODER o un mínimo de cuadros evaluables que sí usa el poder declarado.
- C211b. El criterio puede usar el poder sólo para fijar el gatillo (20 P en 2 días) y decir de forma expresa que el
  veredicto no depende de él. En ese caso "no lo usa" es diseño y no defecto.
- C211c. El poder de la unión a p* = 4,75 puede estar medido en otro documento (resultados de S26a, un anexo, una
  salida en D:\goes_notas\s26). Buscar "4,75" y "4.75" en el repo y en las notas.
- C211d. p* = 4,75 puede no ser el umbral de la unión sino otra cosa (porcentaje de azar, percentil). Leer la
  definición exacta.
- C211e. El poder puede ser calculable hoy con días ya vistos (simulación sobre el cubo hasta el 24-11) sin tocar
  días nuevos. Si es barato, medirlo y decir cuánto es.
- C211f. Si con 20 P el poder es bajo, un NO CONFIRMA no distingue "no hay señal" de "no alcanzaba". Comprobar qué
  rótulos puede dar cada confirmación y si alguno separa esos dos casos.
- C211g. El poder declarado puede venir de un cálculo con otro n o con otra tasa que la del gatillo. Comprobar que
  el número declarado corresponda al n = 20 del gatillo.

## Qué cuenta como resultado

Para cada uno: CONFIRMADO, CONFIRMADO EN PARTE (con la parte), REFUTADO o SIN DATO, gravedad propia 1 a 5, evidencia
de esta sesión, y si cambia o puede cambiar el veredicto de una confirmación. No se corre nada sobre días posteriores
al 24-11-2026.
