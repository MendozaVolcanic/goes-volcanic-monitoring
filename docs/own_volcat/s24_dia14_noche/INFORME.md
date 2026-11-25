# S24: el 14-11 y la noche de 2026 contra 2025. Informe, 25-11-2026

Criterio `criterio_2026-11-25.md` (commit `5c83319`), empujado antes de medir. Código `scripts/s24_medir.py`
(regla S23b sin cambios: base y umbral de 2025, nublado de costumbre de 2026 congelado, hash `e0f093eb6e441cc4`).
Resultado completo en `resultados/s24_resultado.json`. Ninguna medida usa días posteriores al 24-11: la confirmación
de S23b sigue intacta.

**En una línea: la noche de 2026 no dispara menos que la de 2025; dispara diez veces más que una noche común de 2025.**
El 4 % de 2025 lo ponen siete noches con una condición atmosférica propia. La pregunta del 14-11 quedó INVÁLIDA por un
error de diseño del control, y lo que se ve después (post hoc) apunta a otra pista: el rumbo.

## 1. Para geólogo

**La noche.** S23 había anotado, como algo sin explicar, que 2026 disparaba menos que 2025 de noche (0,5 % contra
4 %). Si hay pluma todos los días, debería ser al revés. Resultado: en 2025 los disparos de noche no se reparten.
Cinco noches ponen el 85 % (17-11, 06-11, 28-10, 18-11 y 15-11-2025); con el 03-10 y el 30-09 son siete noches con 3 disparos o más. En las otras 55 noches el
detector dispara 2 veces en 1.409 cuadros (0,14 %). En 2026 dispara 12 veces en 858 cuadros (1,4 %), diez veces más
que una noche común de 2025 (Fisher p = 0,0003), y esos disparos caen el 29-10 (6, una noche con pluma de VOLCAT), el
05-11 (2, el día en que las cámaras vieron pluma hacia el E todo el día), el 11-11 (2), el 15-10 y el 17-10. Es lo que
se esperaría si la pluma diaria deja firma de noche.

**Qué tienen las noches que disparan en 2025.** No más nube marcada (la fracción de nube dinámica es igual), sino más
anillo "probablemente despejado" en la máscara de NOAA (40 % contra 29 %, p = 6e-11) y un anillo menos frío que el
control lejano (−0,75 K contra −1,54 K, p = 6e-7). Es la cara de una capa baja delgada o una inversión que la máscara
no alcanza a llamar nube. Esas noches no son pluma (2025 fue tranquilo): son la falsa alarma propia del método.

**Consecuencia para S23b.** El umbral y el azar por hora de noche salen de 2025 con esas siete noches adentro, así que
de noche el detector es más exigente y el azar más alto de lo que sería en una noche común: la prueba de confirmación
queda del lado conservador. Además, en 2026 sólo el 39 % de los cuadros de noche pasa la compuerta de nubes (65 % en
2025): las noches de 2026 se pierden más por nubes.

**El 14-11.** La huella de VOLCAT ese día es diminuta: de 4 a 31 píxeles a menos de 40 km, la mitad dentro de los
primeros 4 km (que el detector no mira), y su rumbo salta de un cuadro a otro hasta las 19 UTC (243°, 106°, 168°,
335°, 67°, 338°...). En los píxeles de la huella, la firma de 8 a 15 km queda DÉBIL (mediana del percentil 0,16) y la
de 4 a 8 km sin señal. El veredicto formal es INVÁLIDA (§2). Lo que sí se ve, post hoc: de 17:20 a 19:00 la tajada más
baja del detector se queda en el SE (120° a 150°) once cuadros seguidos, con el estadístico entre −0,49 y −0,68 K
contra un umbral de −0,53 a −0,60 K. Cruza el umbral en cuadros sueltos (17:20, 18:20) y la regla exige dos seguidos.
El detector ve algo hacia el SE ese día, débil pero firme de rumbo, que es donde VOLCAT termina dibujando la pluma
después de las 19 UTC (92° a 160°).

## 2. Veredictos por la regla

| Pregunta | Resultado | Veredicto |
|---|---|---|
| A, control positivo 08-11 (huella, anillo entero) | mediana q 0,25 (11 cuadros) | **falla: A INVÁLIDA** |
| A, 14-11 huella 4-8 km / 8-15 km / 15-40 km / anillo | q 0,25 / 0,16 / sin dato / 0,24 | (SIN SEÑAL / DÉBIL / SIN DATO / SIN SEÑAL) |
| A, 14-11 giro 180° 8-15 km / anillo | q 0,048 (6) / 0,065 (12) | (SEÑAL / DÉBIL) |
| B1, concentración | 5 noches ponen 85 % de los disparos de 2025; noches comunes 0,14 % contra 2026 1,4 %, p = 0,0003 | **NO EPISÓDICO** (por la segunda condición, y en sentido contrario al esperado) |
| B2 | ACM "probablemente despejado" y contraste anillo-control: ASOCIADOS; nube dinámica y BT11 del control: no | |
| B3, S de noche p5 / p25 / p50 | 2025 −0,32 / −0,16 / −0,10; 2026 −0,30 / −0,21 / −0,14; pasan la compuerta 65 % / 39 % | |

**Por qué A es INVÁLIDA y qué enseña.** El control positivo promedia la huella del 08-11 en el anillo entero. Ese día
la pluma vive de 15 a 40 km (q 0,019, SEÑAL) y la huella tiene también píxeles cercanos sin firma; el promedio la
diluye. El mismo efecto que se quería medir en el 14-11 arruinó el control. Debió fijarse la banda del control (15 a
40 km) o el percentil de la cola, no la media. Por la regla, A no dice nada.

**Lo de "NO EPISÓDICO".** La regla pedía dos cosas: concentración (se cumple, 85 %) y que 2026 se pareciera a las noches
comunes de 2025 (no se cumple: 2026 dispara más). Lo que había que explicar ("2026 dispara menos") era un artefacto de
las siete noches de 2025.

## 3. Lo que puede estar mal

- B1 y B2 son 62 noches de un año; las siete noches con capa baja pueden ser de esa primavera.
- El giro de 180° del 14-11 da más señal que la huella (8 a 15 km). No sé si es pluma del otro lado, error de
  ubicación de VOLCAT o el día: con A inválida, no se interpreta.
- La persistencia de rumbo del 14-11 la vi después de medir: es una hipótesis, no un resultado.

## 4. S24c, persistencia de rumbo: abandonada por su criterio

Criterio `criterio_S24c_2026-11-25.md` (commit `d11eab8`, antes de calibrar). Idea: umbral más blando y que 4 de los
últimos 6 cuadros caigan en el mismo arco de 90°, porque la pluma sostiene su rumbo y el ruido no. La calibración en
2025 (año sin pluma) no encontró un percentil que cumpla la falsa alarma de 0,05: con P_B 10, 15, 20, 25 y 30 el
ensayo en seco da 0,056, 0,076, 0,109, 0,139 y 0,165 (`resultados/s24c_calibracion.json`). Por el §2, S24c se
abandona y no se mira 2026 con ella. No pruebo percentiles más bajos: sería ajustar la regla al resultado.

**Lo que enseña.** En el año tranquilo la tajada más baja también sostiene su rumbo: la estructura del suelo y de la
atmósfera (las noches de capa baja de §1, la nieve, el relieve) tiene dirección propia. El rumbo por sí solo no separa
pluma de fondo; habría que pedir un rumbo distinto del que el fondo prefiere a esa hora, y eso es otra regla.

## 5. Lo que sigue

S23b sigue esperando días nuevos con pluma de VOLCAT (al 25-11 10:30 UTC, 0 cuadros P). Pistas sin criterio todavía:
la zona de 0 a 4 km (donde vive la huella del 14-11, con el calor del cráter encima) y un rumbo contra el rumbo
preferido del fondo a esa hora.
