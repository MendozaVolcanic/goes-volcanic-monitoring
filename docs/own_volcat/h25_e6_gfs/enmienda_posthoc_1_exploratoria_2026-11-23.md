# H25: enmienda post hoc 1 (exploratoria), 23-11-2026

Escrita **después** del veredicto del criterio (SIN SEÑAL, z +0,52; commit del resultado en esta misma rama) y
**antes** de calcular nada de lo que aquí se describe. **No cambia el veredicto.**

## Por qué

Con el criterio, el poder para una capa que llena el sector es pleno (ε 0,10 y 0,15: 11 de 11 días), pero para una
pluma **angosta** (franja de ±3 km del eje, 22 de los 55 píxeles del sector) es 3 de 11 (27 %) con ε 0,15 y con ε 0,30.
Es lo esperable: la mediana sobre el sector no se mueve si la pluma cubre menos de la mitad (lección de H24, §c de S18).
Una explosión de 2 km que viaja 20 km con 6,9 m/s puede ser una pluma así. El SIN SEÑAL del criterio vale para una
capa que llena el sector, no para una pluma angosta.

## Qué se calcula (lo mismo que la enmienda 2 de H24, pero sin ampliar el fondo)

- Estimador por cuadro: **percentil 20** de las diferencias pareadas del sector, en vez de la mediana. Todo lo demás
  como el criterio: dirección 16,9°, R sin los píxeles cerca de 315°, fondo de ±21 días, regla z ≤ −2.
  (La enmienda 2 de H24 además amplió el fondo a dos meses, y eso fue lo que la invalidó: 11 a 13 % de falsas alarmas.
  Aquí no se amplía.)
- Falsas alarmas con el percentil 20 en las mismas cinco ventanas. **Si superan 10 %, esta lectura es INVÁLIDA.**
- Poder con el percentil 20: capa en el sector ε 0,05 y 0,15; franja ε 0,15, 0,30 y 0,50; control grande.
- Placebo y Longaví con el percentil 20 (Antuco no tiene cuadros despejados en E6).

## Cómo se lee

Sólo como lectura: si con el percentil 20 E6 sigue sin firma, las falsas alarmas quedan ≤ 10 % y el poder de franja
con ε 0,15 llega a ≥ 80 %, se puede decir que E6 tampoco dejó una pluma angosta hacia el NNE. Si alguna de esas
condiciones falla, se dice cuál, y la pluma angosta queda sin probar.
