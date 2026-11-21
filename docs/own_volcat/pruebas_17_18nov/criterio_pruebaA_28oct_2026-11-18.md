# Criterio declarado ANTES de medir: prueba A (paralaje) sobre el episodio del 28-10, 18-11-2026

Pregunta: el 28-10 sí hay una nube fría al SE de la huella VOLCAT. ¿Está corrida hacia el sur lo que
predice el paralaje para la altura que da VOLCAT? Si es así, SSEC dibuja la huella corregida y nosotros
medimos en la grilla ABI sin corregir.

## Datos (nada nuevo)

- Cuadros del caché del detector con escena: 28-10 22:40, 23:00, 23:20 y 23:40 UTC (C11, C14, C15).
- Huella: todos los píxeles VOLCAT con ceniza a ≤ 50 km de Chillán en el PNG del mismo minuto, llevados
  a la grilla ABI de la ventana como en `huellas.py` (píxel ABI = píxel VOLCAT más cercano).
- Altura VOLCAT: mediana del punto medio del bloque de la barra (lo_km + hi_km) / 2 de los píxeles de esa
  huella, por cuadro.
- Referencia de cielo despejado: `referencia(dt, 10, 3)`, la misma de las pruebas A y B de noviembre.

## Medición

Para cada corrimiento (dy, dx) en −5..5 (dy positivo = filas al SUR, 2,84 km cada una; dx positivo =
columnas al ESTE, 2,09 km), mover la huella y medir dos fracciones: con BTD (11 − 12 µm) < −1 K y con
ΔBT11 < −2 K respecto de la referencia. Promediar las fracciones sobre los cuatro cuadros.

Corrimiento esperado por paralaje: dy_esp = 0,93 · h / 2,84 filas (h = altura VOLCAT en km sobre el
nivel del mar, mediana de los cuatro cuadros), dx_esp ≈ 0.

## Decisión (se evalúa por separado para cada métrica; basta una)

- **Reabre H4 sólo para este episodio** si el máximo de la fracción fría está en dy ≥ +1 y |dx| ≤ 2,
  vale al menos 0,30, es al menos el doble que en (0, 0), y |dy − dy_esp| ≤ 1 fila.
- **Corrimiento no explicado por paralaje** si el máximo cumple valor ≥ 0,30 y el doble de (0, 0), pero
  falla la dirección o la magnitud (|dx| > 2, dy < +1, o lejos de dy_esp). Puede ser el viento que
  arrastra la nube, u otra cosa; no se fuerza la lectura.
- **Falsa H4 en este episodio** si el máximo no llega a 0,30 o no dobla el valor en (0, 0).

No cambia código de detección.
