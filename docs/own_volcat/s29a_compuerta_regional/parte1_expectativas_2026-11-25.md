# S29a, parte 1: qué ve la zona de cumbre de Antuco de día. Expectativas escritas antes de mirar, 25-11-2026

Escrito, commiteado y empujado **antes** de buscar o abrir una sola escena Sentinel-2 o Landsat de Antuco, Longaví o
Chillán en 2025 o 2026. Esto **sólo comprueba**: nada de lo que salga entra al detector (regla de Nicolás del 24-11).

## 0. La pregunta

S28a midió que la zona de 0 a 4 km de la cumbre de Antuco, que no tiene pluma, dispara de día 2,6 % de los cuadros
en oct-nov 2025 y 9,4 % en 2026 (×3,7). Longaví casi no cambia (2,5 % a 3,2 %). Los días fuertes de Antuco en 2026
son 10-11 (33 cuadros, 13:50 a 20:40 UTC), 04-10 (25), 14-11 (14), 04-11 (11), 13-11 (10), 11-11 (9) y 12-11 (8);
en 2025, el 14-11 (40 cuadros, todo el día) concentra casi la mitad. La zona dispara cuando la BTD 11 a 12 µm de la
cumbre baja respecto de controles a la misma cota y la misma BT11.

Tres explicaciones físicas compiten:

1. **Menos nieve en la cumbre en 2026 (roca o escoria al sol).** La nieve tiene emisividad casi igual a 11 y 12 µm;
   la roca volcánica descubierta tiene emisividad algo menor a 11 µm que a 12 µm y, caliente al sol, abre una BTD
   negativa que no es pluma. Si 2026 trae menos nieve que 2025 en la misma fecha, la zona dispara más y sólo de día.
2. **Ceniza o polvo sobre la nieve.** Nieve sucia: sigue siendo nieve (NDSI alto) pero refleja menos en el visible,
   absorbe más sol y se calienta; si la capa es gruesa se comporta como roca. Antuco no tiene erupción; la fuente
   posible es la ceniza de Chillán (61 km al N, rumbo dominante de la pluma al SE) o polvo.
3. **Nube baja o cúmulo de tarde sobre la cumbre que la máscara ACMF de GOES no marca.** Un cúmulo sobre una cumbre
   caliente nace a media mañana y crece de tarde, como los disparos (13:00 a 22:00 UTC). Una nube de agua delgada y
   fragmentada en un píxel de 2 km cambia la BTD sin que ACMF la llame nube.

## 1. Qué esperaría ver en cada caso y cómo lo distingo

Medidas en la zona: los píxeles de 20 a 30 m a menos de 4 km de la cumbre (Antuco -37,41; -71,35, 2.979 m). Lo mismo
en Longaví (-36,19; -71,16) como control, porque su zona no subió, y en Chillán (-36,863; -71,377) sólo como
referencia (tiene pluma y ceniza en 2026).

- **Nieve**: NDSI = (verde − SWIR1)/(verde + SWIR1) > 0,4 y verde > 0,3, fuera de nube. **Nieve limpia** si además
  verde > 0,6. **Nieve oscurecida** (ceniza o polvo) si NDSI > 0,4 y verde entre 0,3 y 0,6. **Suelo descubierto**:
  NDSI < 0,2 y fuera de nube. **Nube**: SCL 8, 9 o 10 en Sentinel-2; bits de nube o nube dilatada del QA en Landsat;
  y, porque esas máscaras confunden nube con nieve en cumbres, lo miro también en la imagen (SWIR1 alto con NDSI bajo y
  textura de nube, o sombra proyectada).

Lo que esperaría según la explicación:

| Explicación | Fracción de nieve 2026 contra 2025 en fechas equivalentes | Nieve oscurecida | Nube sobre la zona en el día de disparo, a la hora del paso | Longaví (control) |
|---|---|---|---|---|
| 1. Menos nieve | 2026 menor en la mayoría de los pares (diferencia ≥ 0,15 en la fracción de la zona) | sin cambio | despejado | sin la misma pérdida de nieve, o la pérdida no se acompaña de disparos |
| 2. Ceniza o polvo | parecida | 2026 mayor (fracción de nieve oscurecida ≥ 0,15 más que en 2025) | despejado | sin oscurecer (más lejos del rumbo de la pluma) |
| 3. Nube baja | parecida | sin cambio | nube que cubre ≥ 20 % de la zona en la mayoría de los días de disparo con paso a menos de 1 h de un cuadro que disparó | indistinto |

Cómo leo una combinación: si 2026 pierde nieve **y** hay nube en los días de disparo, digo las dos cosas y no elijo.
Si nada cambia y los días de disparo están despejados en el óptico, la explicación no es ninguna de las tres que el
óptico puede ver (podría ser humedad de capa baja o un calentamiento de la superficie que no cambia su color).

**Límite que ya sé**: Sentinel-2 y Landsat pasan cerca de las 14:30 a 14:50 UTC (10:30 a 10:50 hora de Chile, UTC-3).
Los disparos de la zona van de 12:00 a 22:40 UTC y la mayoría es de tarde. Una nube de tarde no se ve en una imagen de
media mañana: un día despejado a las 14:40 no descarta una nube de las 18:00. Sólo cuento como prueba de nube un paso
a menos de 1 h de un cuadro que disparó; los demás días sirven para la nieve, que cambia lento. Y como el paso de un
satélite cae en el día de disparo sólo a veces, la comparación de nieve se hace con todas las escenas útiles de
21-09 a 21-11-2025 y de 21-09 a 24-11-2026, en pares por fecha del año (±10 días).

**Lo que espero, antes de mirar**: la explicación 1 (menos nieve en 2026 en Antuco), porque la subida es sólo de día,
se concentra en noviembre (deshielo) y se reparte en varios días seguidos (04, 10 a 14-11), lo que encaja mejor con un
estado de la superficie que con nubes de un día. Espero que alguno de los días fuertes muestre además cúmulos.

## 2. Reglas

- Fuentes sin cuenta: Sentinel-2 L2A en Element 84 y Landsat C2 L2 en Planetary Computer (las mismas lecturas de
  `docs/own_volcat/s20b_verdad_alta_res/scripts/s20b_comun.py`, que sólo importo). Sin VIIRS. Ningún día posterior al
  24-11-2026.
- Caché de las ventanas recortadas en `D:\goes_notas\s29\s29a\optico\`; al repo sólo tablas y figuras chicas.
- Esto no cambia ninguna regla del detector ni ninguna confirmación congelada.
