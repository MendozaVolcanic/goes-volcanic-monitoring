# S31j: enmienda 2, escrita antes de calcular un solo cuadro del espejo (27-11-2026)

**Qué pasó.** La corrida 1 de `s31j_medir.py medir` (commit `e93e928`) paró en la comprobación de código, como manda el
criterio, antes de calibrar c y antes de correr el espejo en ningún año. Registro:
`D:\goes_notas\s31\s31j\medir_corrida1_paro_en_comprobacion.log`. Pasaron la 1 (S del congelado, 0 distintos), la 3
(calor: 15 de 15 noches con el mismo `enc` y el mismo `n10`; faltan 3 cuadros en S3 de 3.408) y la 4 (sintéticas). Falló
la 2: la z de la corona difiere de la que guardó S31h, con las mismas posiciones finitas, diferencia máxima 0,79.

**Por qué no es un error de código.** La comprobación estaba mal escrita. S31e y S31h calculan la z igual cuando el píxel
tiene 20 valores o más en su propio pozo de 2025; cuando tiene menos, S31e usa el pozo de su tajada entera (4 a 40 km) y
S31h el de los píxeles de la corona de esa tajada (criterio de S31h, §2; su propia comprobación 3 comparaba sólo píxeles
con pozo propio). Mirado antes de cambiar nada: las celdas distintas son 34 de 351.451 en 2025, 550 de 186.020 en 2026 y
588 de 264.552 en 2024, en sólo 6 a 8 píxeles de la corona y sólo entre las 15 y las 20 UTC, las tardes en que el borde
de nube dinámica deja pozos chicos. El espejo usa la z de S31e (criterio §2), que es la que S31e midió.

**Qué cambia.** La comprobación 2 pasa a ser: (a) en toda celda de la corona cuyo píxel tiene 20 valores o más en su
pozo propio, la z es idéntica a la de S31h (diferencia ≤ 1e-6); y (b) toda celda donde difieren tiene menos de 20
valores en su pozo propio. Si falla (a) o (b), INVÁLIDA. Nada más cambia. La corrida 2 recalcula todo desde cero con el
mismo código y la misma semilla: es la misma cuenta, porque nada del espejo se había calculado.
