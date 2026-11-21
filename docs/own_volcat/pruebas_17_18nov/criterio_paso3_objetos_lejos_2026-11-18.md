# Criterio declarado ANTES de medir: paso 3 (H2, trato especial al cráter), 18-11-2026

Pregunta: ¿VOLCAT dibuja objetos chicos sólo cerca de volcanes, o en cualquier parte del sector?
Si los dibuja en cualquier parte con densidad parecida, el trato especial al cráter (SECO Part 2,
Tabla 4) no hace falta para explicar los objetos de Chillán.

## Datos (nada nuevo salvo la lista de volcanes)

- Los 2.181 PNG Ash_Height del sector `Chile_Central_2_km`, 01 al 16-11-2026, ya bajados en
  `C:\Users\nmend\AppData\Local\Temp\claude\58c6c65788fdfd96\9c58fda3-6424-4269-8b61-4905a4c1d033\scratchpad\volcat_chillan_10min\png`.
  Grilla CE de 0,0202° (2,25 km N-S, ~1,8 km E-O a 37° S): un píxel del PNG es ~0,7 píxel ABI.
- Volcanes: lista Holocena del GVP (Smithsonian) por WFS, recortada a la caja del sector
  (58 volcanes, 121 KB, bajada el 18-11). VOLCAT puede usar otra lista; queda como salvedad.

## Medición

Decodificación igual que `huellas.py` del estudio del detector: píxel con ceniza = color de la barra
Ash_Height (saturación ≥ 0,2 y `classify_pixels` ok), objetos de 8 vecinos en todo el mapa, fuera el
ruido (≤ 3 px) y los mantos (> 5 % del mapa). Por objeto: tamaño, centroide, distancia del centroide al
volcán GVP más cercano, ángulo cenital solar en el centroide.

- Objeto chico = 4 a 36 px del PNG (≈ hasta 25 px ABI, el techo de la Tabla 4 de SECO).
- Se excluyen los objetos con centroide a ≤ 50 km de Nevados de Chillán (es el fenómeno en estudio).
- Bandas por distancia al volcán GVP más cercano (sin Chillán): A ≤ 10 km, B 10 a 50 km, C > 50 km.
- Densidad D = objetos chicos / (área de la banda en el mapa, km²) / número de cuadros.
- R = D(A ∪ B) / D(C).

## Decisión

- **Falsa H2 como explicación necesaria** si R ≤ 2: VOLCAT dibuja objetos chicos en cualquier parte
  con densidad parecida.
- **Compatible con H2** si R ≥ 5 y D(A) ≥ D(B). No la confirma: cerca de volcanes está la cordillera
  (nieve, nubes orográficas) y puede haber actividad real en otros volcanes. Ese sesgo empuja R hacia
  arriba, así que el criterio es asimétrico: un R bajo falsa con fuerza; un R alto sólo es compatible.
- Entre 2 y 5: no concluyente.
- Análisis principal: los 16 días. Sensibilidad (se informa, no decide): sin el 16-11, que tuvo un
  sistema sinóptico.
- Se informa además la fracción diurna (cenit solar < 80°) de los objetos chicos en la banda C, como
  dato para H1. No entra en la decisión de H2.

No cambia código de detección.
