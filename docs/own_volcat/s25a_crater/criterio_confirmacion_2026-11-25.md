# S25a: confirmar en días nuevos la regla de la zona del cráter. Criterio, 25-11-2026

Escrito, commiteado y empujado **antes** de mirar un solo cuadro de GOES posterior al 24-11-2026 en la zona. La regla
S25a (`criterio_2026-11-25.md`) se eligió antes de medir, pero los 100 cuadros P de VOLCAT de 21-09 a 24-11 ya se
habían mirado con otras reglas, y la zona dispara en 2026 mucho más que en 2025 (`INFORME.md` §1). Por eso se
confirma una vez en días que nadie miró.

## 1. La regla (congelada)

La de `criterio_2026-11-25.md` §2 sin ningún cambio: zona de 11 píxeles, base por píxel y umbral de 2025 con los 62
días, corrección regional con los controles de su cota, dos píxeles más bajos, dos cuadros seguidos, compuerta del
anillo con el nublado de costumbre de 2026 congelado (`estat_2026.npy`, SHA-256 `e0f093eb6e441cc4...`).

## 2. Días, datos y cuándo se mide

Los de S23b (`s23_fondo_2025/criterio_S23b_2026-11-25.md` §3 y §6): desde el 25-11-2026 00:00 UTC, con el 24-11 como
arranque; C14, C15 y ACMF bajados por `s23b_confirmar.py bajar` a `D:\goes_notas\s23\s23b\`; clases de VOLCAT de
`s23_fondo_2025/resultados/volcat_clases_desde_25nov.csv`. Se mide **una sola vez**, en la misma ocasión que S23b (al
menos 20 P en al menos 2 días nuevos). Una corrida anterior es "vistazo" y no decide.

## 3. Veredictos, en este orden

- **INVÁLIDA:** falla de instrumento de los días nuevos (I1 cobertura ≥ 0,95, I2, I3, como S23b).
- **NO DECIDIBLE:** menos de 10 P evaluados, o de un solo día.
- **CONFIRMA:** p25 ≤ 0,01 (azar por hora de 2025, el de la medida S25a), pN ≤ 0,05 (Fisher contra los N de los días
  nuevos a ±60 min de algún P evaluado) y R ≥ 0,25.
- **PARCIAL:** p25 ≤ 0,01 sin lo demás.
- **NO CONFIRMA:** p25 > 0,01.

Se informa además la tasa de disparo de los N nuevos, de día y de noche, contra 2025 (3,2 %; noche 4,3 %).

## 4. Expectativa escrita antes de mirar

Que dependa del tipo de pluma: si VOLCAT la dibuja pegada al cráter (como el 14-11 o el 10-11), CONFIRMA; si la dibuja
lejos (como el 08-11), la zona no llega y queda en NO CONFIRMA aunque S23b confirme. Que los N disparen más que en
2025, como en oct-nov.
