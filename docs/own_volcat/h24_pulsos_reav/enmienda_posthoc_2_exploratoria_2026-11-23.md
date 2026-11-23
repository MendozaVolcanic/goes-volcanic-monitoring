# H24, enmienda post hoc 2 (23-11-2026): análisis EXPLORATORIO, no decide

Escrita y commiteada **después** de ver el veredicto del criterio (NO CONCLUYENTE, commit `e260476`) y **antes** de
calcular cualquier número de lo que aquí se define. El veredicto oficial de H24 es el del criterio y no cambia.
Todo lo de esta enmienda se informa como exploratorio.

## Por qué

La corrida del criterio dejó dos limitaciones a la vista, ninguna de las dos por el cielo del episodio:

1. **Tarde sin línea base.** E10 a E13 (los pulsos altos que VOLCAT sí marcó: E11, E12 y E13 en 8 de 8, 7 de 7 y
   10 de 11 cuadros) tenían la escena despejada (el 28-10, terreno bajo despejado ≈ 100 % de 12 a 22 UTC), pero la
   línea base pedía 3 días despejados a la misma hora en ±21 días sin días excluidos, y de tarde había 1 o 2. El
   rótulo "SIN DATO (cielo)" del script corresponde a "sin línea base de tarde".
2. **La mediana no ve una pluma angosta.** El poder se midió con una capa que llena el sector entero (53 píxeles), y
   dio 100 % ya con ε 0,05. Una pluma real cubre una fracción del sector; si cubre menos de la mitad, la mediana no
   se mueve. Los SIN SEÑAL del criterio dicen "no hubo capa de ε ≥ 0,05 a 0,10 sobre todo el sector", no "no hubo
   pluma".

## Qué se calcula (todo lo demás, igual al criterio y a la enmienda 1)

- **X1, ventana larga:** línea base y días nulos con **todos** los días no excluidos del 21-09 al 21-11, no ±21.
  Riesgo: mezcla septiembre con noviembre (más tibio); la BTD se corre menos que la BT11 con la estación, y el nulo
  sale de la misma ventana, así que el corrimiento entra también en el nulo.
- **X2, estadístico de cola:** percentil 20 de las diferencias pareadas (D2 del píxel − su control) sobre W, en vez
  de la mediana. Cuadro válido igual (≥ 10 píxeles de W con control). Se calcula con X1.
- **Se informan las dos piezas por separado:** mediana con X1 (sólo cambia la ventana) y percentil 20 con X1.
- **Poder angosto:** además de la capa en todo W, una capa sólo en la **franja de ±3 km alrededor del eje** del
  sector (pluma angosta), con ε 0,15, 0,30 y 0,50, a la temperatura GFS del tope. Mismo método de inyección.
- **Clase del episodio:** la tabla del criterio §6, con "poder" = poder de la franja con ε 0,30 ≥ 0,80. La regla
  (z ≤ −2), las falsas alarmas medidas, el placebo contra el viento y las cumbres de control, iguales.
- **Veredicto exploratorio:** la misma regla del criterio §8, con el rótulo "exploratorio".

## Lo que esto agrega y lo que no

Son dos intentos más sobre los mismos episodios: suben la probabilidad de un SEÑAL por azar. Por eso cada variante
informa su propia tasa de falsas alarmas medida, y un SEÑAL exploratorio se lee como hipótesis para una prueba
nueva con criterio propio, no como resultado.
