# S31j: enmienda 1, escrita antes de medir (27-11-2026)

Antes de calcular una sola VRP y un solo cuadro del espejo, al escribir el script se vio un defecto de la comprobación
§6.3 del criterio (`e29dd33`).

**Qué cambia.** La comparación del indicador de calor contra `docs/own_volcat/vrp_nocturno/resultados/noches.csv` se
hace sólo en las 15 noches del 05-10 al 19-10-2026, no en las del 20 al 22-11.

**Por qué.** El indicador decide "visible" con una referencia: el percentil 90 de la BT14 nocturna de las 7 noches
anteriores. En la validación, Chillán se bajó todas las noches del 26-08 al 19-10 (serie A), pero entre el 20-10 y el
19-11 sólo una noche de cada tres (serie B). La referencia de las noches del 20 al 22-11 salió de 2 a 4 noches en la
validación y sale de 7 aquí: pueden diferir sin que haya ningún error de código, y la comprobación quedaría
INVÁLIDA por una diferencia de muestreo. Del 05-10 al 19-10 las dos bajadas tienen las mismas 7 noches previas.

Nada más cambia: la regla, c, las medidas, los nulos y los rótulos son los del criterio. La misma tolerancia: `enc`
igual en las 15 noches y `n10` igual en al menos el 90 %.

Otra precisión, sin cambio de regla: en las pruebas sintéticas (§6.4) los radios de 60 y 90 km sólo se pueden probar por
el lado positivo (una continuación a 33 km pasa con un cuadro sin evaluar entre medio, y a 40 km con dos), porque el
anillo llega a 40 km del cráter y no hay pares de píxeles a más de unos 46 km del que nace a 6 km.
