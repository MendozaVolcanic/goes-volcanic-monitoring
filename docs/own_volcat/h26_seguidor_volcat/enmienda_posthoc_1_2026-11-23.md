# H26, enmienda post hoc 1 (23-11-2026): diagnóstico del control positivo

Escrita y commiteada **después** de la corrida del criterio (`95d6171`) y **antes** de calcular lo que aquí se
describe. No cambia el veredicto: con la regla del criterio §6, el control positivo pasó en 10 de 20 tramos (pide
18) y el veredicto es **SIN PODER**. La concordancia de R1 con `event_idx` salió IoU tolerante mediano 0,000 y
fracción recuperada 0,016 (12 de 769 píxeles).

## Qué se calcula (informativo, no decide)

1. Para cada uno de los 20 tramos del control positivo: si el seguidor dispara en los cuadros 3 y 4; el IoU
   tolerante contra la pluma inyectada; el tamaño del objeto que contiene la pluma inyectada; cuántos píxeles de la
   máscara quedan fuera de la pluma dilatada 1 píxel; y si el objeto de la pluma se fusionó con candidatos naturales
   (más de 6 píxeles) o superó los 70 píxeles del nacimiento.
2. La causa de cada tramo fallido en una de cuatro clases, definidas ahora: (a) no dispara; (b) dispara, pero la
   máscara arrastra otros objetos seguidos (pistas de ruido) que bajan el IoU; (c) la pluma se fusiona con candidatos
   naturales y el objeto crece; (d) otra.
3. Separar las dos partes de la exigencia del criterio: fracción de tramos que **disparan** en los cuadros 3 y 4
   (detección por cuadro), y fracción con IoU ≥ 0,5 (localización).
4. Repetir el control positivo, sólo como lectura, en Antuco y Longaví (misma pluma, misma semilla, compuerta
   forzada encendida), para ver si la falla es del seguidor o del fondo de Chillán.

## Cómo se va a leer

- Si la falla es (a), el seguidor no ve una pluma de −3 K: SIN PODER también para la detección por cuadro.
- Si es (b) o (c), el seguidor detecta pero no localiza en este fondo: el fondo de la cordillera produce objetos
  candidatos que se pegan a cualquier pluma o la siguen. Es el riesgo escrito en S18 (camino b), medido.
- En ningún caso esta enmienda convierte SIN PODER en otro veredicto. Lo que sí puede decir es si, con el poder que
  se midió, la concordancia observada (IoU 0,000) es compatible con un seguidor que funciona y una huella que no
  tiene nada que seguir.
