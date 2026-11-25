# S26b: ¿los disparos nocturnos de la zona del cráter son pluma o son el calor del cráter? Informe, 25-11-2026

Criterio `criterio_2026-11-25.md` (commit `2643ab0`), empujado antes de cruzar un solo disparo con el calor. Física
`scripts/s26b_fisica.py` (`resultados/s26b_fisica.json`), serie de calor `scripts/s26b_calor.py` (regla validada tal
cual, en `D:\goes_notas\s26\s26b\`), medida `scripts/s26b_medir.py` (`resultados/s26b_resultado.json`; tablas por
noche en `D:\goes_notas\s26\s26b\noches_2026.csv` y `noches_2025.csv`).

**En una línea: EL CALOR NO EXPLICA los disparos nocturnos de la zona del cráter.** Las noches de 2026 sin calor sobre
10 MW disparan más (34 %) que las encendidas (21 %), dentro de una misma noche los cuadros calientes no disparan más
que los fríos, y los píxeles que disparan no están más tibios que en 2025. La física dice además que el material
incandescente no puede fabricar disparos: sólo sube la BTD.

## 1. Para geólogo

**El fenómeno.** La firma de ceniza que usa la regla de S25a es una BTD (11 menos 12 µm) más baja de lo normal: los
silicatos absorben más a 11 que a 12 µm. Desde el 24-10 el cráter de Chillán tiene material incandescente casi todas
las noches (VRP de 16 a 79 MW de máximo por noche). La pregunta era si ese calor podía estar bajando la BTD de la zona
y haciéndola disparar de noche, que es cuando la zona dispara de más en 2026 (24 % de los cuadros contra 4 % en 2025).

**Lo que dice la física (antes de mirar datos).** Una fuente caliente que cubre una fracción mínima del píxel sube más
la BT a 11 µm que a 12 µm (la radiancia crece más rápido con la temperatura a longitud de onda más corta). Con la VRP
que mide la regla (1 a 80 MW, 600 a 1.200 K, píxel de 4,5 a 7,5 km²), la BTD sube entre +0,001 y +0,36 K; nunca baja.
Para que bajara, el material caliente tendría que emitir a 11 µm 0,15 menos que a 12 µm. El único caso en que el calor
baja la BTD es un **suelo tibio extenso con material silicatado** (un depósito caliente): ahí el calor amplifica la
BTD negativa que el depósito ya tiene. Pero para llegar al umbral nocturno de S25a (−0,37 a −0,49 K) ese suelo tendría
que calentar el píxel a 11 µm en 19 K o más. Eso deja una huella medible.

**Lo que salió.**

- **Sin calor se dispara más, no menos.** 11 noches de 2026 con el cráter visible y sin calor sobre 10 MW (26-09 a
  22-10): 107 disparos en 310 cuadros nocturnos evaluados (34 %). 23 noches encendidas: 228 en 1.092 (21 %). 2025: 94 en
  2.562 (3,7 %). La época del 21-09 al 11-10, antes de la primera noche encendida, ya dispara en el 39 % (118 de 303).
- **Dentro de la noche, el calor no cambia nada.** En 19 noches con cuadros calientes y fríos visibles, la razón de
  odds de disparar en un cuadro sobre 10 MW contra uno bajo 10 MW es 0,71 (p = 0,51).
- **Los píxeles que disparan no están tibios.** De noche, su BT11 está en mediana +0,6 K sobre su propio valor de 2025
  a la misma hora (corregido por la región), igual que los cuadros sin disparo (+0,6 K). Sólo el 6 % pasa de +3 K. La
  vía del suelo tibio pide +19 K.
- **Con cielo despejado (E1) en los dos años el resultado se mantiene**: sin calor 22 % (37 de 168), encendidas 22 %,
  2025 3,7 % (83 de 2.218).
- **El exceso de 2026 no es de pocas noches.** En 2025, 4 noches ponen 79 de los 94 disparos y la mediana por noche es
  0; en 2026, 28 de 41 noches tienen 3 disparos o más y la mediana por noche es 21 % (post hoc).

**Qué significa.** El calor del cráter, que es lo que cambió en la cumbre desde octubre, no está detrás de los
disparos nocturnos. La zona ya disparaba de noche el 26 y el 27-09 (10 de 24 y 42 de 55 cuadros), con 0 MW en la regla
y en MIROVA. Lo
que queda son las otras candidatas de S25a: la pluma diaria (que de noche VOLCAT no dibuja), el depósito de ceniza
alrededor del cráter (que baja la BTD del suelo sin calentarlo) o una cumbre con distinta nieve que en 2025. Las tres
son compatibles con una BT11 casi igual a la de 2025. Separarlas pide otra firma o las cámaras del OVDAS.

**Un detalle que no decide (post hoc).** En las noches encendidas disparan sobre todo los píxeles (43,46) y (43,47),
a 1,8 y 2,3 km de la cumbre aparente (con paralaje, la cumbre de 3,2 km se ve unos 3 km al sur); en las otras noches,
el (41,46), a 1,2 km del cráter real y 4,1 km de la cumbre aparente. Una pluma sobre el cráter también se ve corrida al
sur por paralaje, más cuanto más alta. Pero las noches encendidas son las de octubre y noviembre y las otras las de
septiembre: el cambio puede ser de la época (nieve, depósito) y no del calor. No lo interpreto.

## 2. Veredicto por la regla

| Prueba | Resultado | Lectura |
|---|---|---|
| Reproducción | Ensayo en seco 2025 176 de 5.499 (igual a S25a); disparos de 2026 idénticos a `tabla_2026.csv` cuadro a cuadro; estado de calor igual a la validación en 41 de 42 noches comparables | pasa |
| E1, por noche | Encendidas 23 noches, mediana 0,21; bajo el límite 11 noches, mediana 0,36; Mann-Whitney (encendidas mayor) p = 0,68 | sin asociación |
| E2, por cuadro dentro de la noche | 19 noches; OR de Mantel-Haenszel 0,71; p = 0,51 | sin asociación |
| E3, sin calor contra 2025 | Bajo el límite 107/310 contra 94/2.562, p = 2e-56; época 21-09 a 11-10 118/303, p = 3e-67; con E1 37/168 contra 83/2.218, p = 5e-16; contra 2025 sin las 7 noches de capa baja de S24, p = 3e-68 | exceso sin calor |
| E3, encendidas contra 2025 | 228/1.092, p = 4e-57 | exceso igual |
| E4, sin dato de calor | 26/201 (13 %); con E1 9/148 (6 %), p = 0,12 | informativo |
| E5, BT11 de los píxeles que disparan de noche | 361 cuadros; mediana +0,60 K (p10 −1,7, p90 +2,5), 6 % ≥ +3 K; sin disparo +0,62 K | sin huella de suelo tibio |
| **Veredicto** | | **EL CALOR NO EXPLICA** |

Una noche no coincide con la validación: el 20-11 la validación dice "bajo el límite" y la serie nueva "sin dato". La
validación sólo tenía una noche de cada tres después del 19-10, así que su referencia de cielo despejado para esa noche
salió de menos cuadros; la serie nueva es la que corre en producción. Esa noche no tiene cuadros evaluados por la zona.

## 3. Lo que puede estar mal

- "Bajo el límite" no es "frío": la regla no ve calor bajo ~10 MW. Tres noches de esa clase tienen 4,6 a 6,1 MW de
  máximo (01-10, 05-10, 14-10). Pero 26-09, 27-09, 07-10 y 08-10 tienen 0 MW en todos sus cuadros visibles y disparan
  en el 42 %, 76 %, 53 % y 36 % de sus cuadros evaluados.
- Las noches sin calor son casi todas de septiembre y octubre, y las encendidas de octubre y noviembre: E1 compara
  épocas además de calor. E2 (dentro de la misma noche) no tiene ese problema y tampoco da asociación.
- E5 mide la BT11 con la base de 2025 de cada píxel: si la cumbre de 2025 tenía más nieve, la anomalía sale positiva
  sin calor. Va en contra de la conclusión, no a favor, y aun así queda lejos de +19 K.
- La física usa emisividades supuestas en la sensibilidad (barrido de ε12 − ε11 de 0 a 0,20), no un espectro medido
  del material de Chillán.

## 4. Lo que sigue

- **Separar pluma, depósito y nieve** en las noches que disparan. Las cámaras del OVDAS en noches sin calor que
  disparan mucho (27-09, 26-09, 07-10, 05-10) y en noches encendidas (08-11, 27-10, 14-11) dirían si hay pluma.
- Una firma que distinga depósito de pluma: el depósito está fijo (mismo píxel, toda la noche, varios días); la pluma
  se mueve de cuadro a cuadro. Es una pregunta para su propio criterio.
- El calor no invalida la zona del cráter de noche: el píxel caliente nunca es el mínimo. Lo que la zona ve de noche
  sigue sin explicar.
