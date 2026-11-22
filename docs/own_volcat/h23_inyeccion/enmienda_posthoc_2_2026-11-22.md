# Enmienda post hoc 2 al criterio H23 (22-11-2026)

**Rótulo: POST HOC.** Segunda y última enmienda antes de medir. Se commitea **antes** de calcular un solo número
de detección. Sólo toca la comprobación de instrumento I5.

## 1. Qué pasó

Con la línea base de la enmienda 1, la corrida de sólo instrumento (`python -I h23_medir.py --solo-instrumento`)
volvió a cortar en I5, esta vez porque I5 **no se pudo calcular** (salida en
`resultados/h23_instrumento_corrida2_falla_I5_sin_referencia.json`):

- I4 pasó: correlación −0,935 en los 864 píxeles con referencia; cumbre 11,5 K más fría que el terreno bajo.
- I6 pasó: BTD_ref mediana 0,83 K.
- I5 dio "sin número": no hay referencia a las 18 UTC. La línea base nueva pide 3 días distintos con la escena
  despejada a esa hora, y a las 18 UTC hay 2 (`resultados/h23_diag_ref_oct_chillan.json`).

## 2. Qué se miró (sólo datos de instrumento)

El ciclo de la referencia nueva hora por hora (`scripts/h23_diag_ref.py`). Ahora sí es un ciclo de cielo
despejado: en el terreno bajo sube de 277,8 K a las 09 UTC a 291,0 K a las 16 UTC (13,2 K), y en la cumbre de
266,5 K a 274,2 K (7,7 K). El defecto de la primera corrida (mínimo a media tarde) desapareció. Lo que falta es
dato: **de las 17 a las 22 UTC no hay referencia**, porque en los 33 días del bloque hay entre 0 y 2 días con la
escena despejada a esas horas. Días con escena despejada por hora: 5 a 7 de noche (01 a 10 UTC), 5 a 6 en la
mañana (11 a 13 UTC), 4 a las 14, 3 a las 15, 2 a las 16 UTC.

## 3. Qué cambia

**I5 se evalúa en la última hora, entre las 12 y las 18 UTC, en que al menos la mitad del terreno bajo tiene
referencia**, contra las 09 UTC, con el mismo umbral (8 K o más). Se informa qué hora fue. La intención de I5 no
cambia: comprobar que la referencia tiene el ciclo diurno de un suelo despejado.

Nada más cambia.

## 4. Consecuencia para leer el resultado (se sabe antes de medir)

- El tramo **18 a 24 UTC (15 a 21 h de Chile) va a quedar SIN DATO** en Chillán, en las tres poblaciones: no
  hay línea base. La mayoría de los eventos reales de noviembre fue a esas horas. Lo más cercano que esta prueba
  puede medir es el tramo 12 a 18 UTC, que en la práctica cubre de las 12 a las 17 UTC (09 a 14 h de Chile) y
  contiene el mediodía solar (16:30 UTC), cuando el suelo está más caliente.
- El tramo 12 a 18 UTC se sostiene en pocos días (2 a 6 por hora). Puede no llegar al mínimo de 8 días por
  celda. Si no llega, es SIN DATO.
- Esto es un límite de la muestra: octubre de 2026 tuvo muy pocas tardes despejadas sobre la cordillera a esta
  latitud, según la máscara de NOAA.
