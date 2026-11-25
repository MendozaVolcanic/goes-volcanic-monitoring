# S25a: la zona de 0 a 4 km del cráter. Informe, 25-11-2026

Criterio `criterio_2026-11-25.md` (commit `1306fb5`), empujado antes de calcular un solo valor de BTD en la zona.
Código `scripts/s25a_medir.py` (commit `52fba40`, más una línea que crea la carpeta de resultados), revisión post hoc
`scripts/s25a_posthoc.py`, videos `scripts/s25a_lado_a_lado.py`. Resultados en `resultados/`; la tabla por cuadro
de 2026 en `D:\goes_notas\s25\s25a\tabla_2026.csv`. Ningún día desde el 25-11 (reservados para S23b).

**En una línea: por su regla, la zona del cráter ALCANZA (44 de 93 cuadros de VOLCAT; 14-11 ALCANZADO, 20 de 31).**
Es lo que ningún detector veía: el 14-11 daba 0 en todas las versiones. Pero en 2026 la zona dispara también fuera de
VOLCAT mucho más que en 2025 (de noche, 24 % de los cuadros contra 4 %), y eso no lo sé explicar.

## 1. Para geólogo

**El fenómeno.** Cuando Chillán emite un pulso de ceniza, la pluma está primero encima del cráter. VOLCAT la dibuja
ahí (el 14-11, la mitad de su huella cae dentro de 4 km). Nuestros detectores no miraban esa zona porque la cumbre
es un mal lugar para comparar: tiene relieve propio (frío por altura, nieve) y, desde el 24-10, calor en el cráter.

**Lo que se hizo.** Cada uno de los 11 píxeles de la zona se compara **consigo mismo** a la misma hora en oct-nov de
2025, un año tranquilo, y se le resta lo que cambió ese día en toda la región (píxeles lejanos de su misma cota). Así
el relieve se cancela solo. El cuadro se resume con los **dos píxeles más bajos** de la BTD (11 menos 12 µm, la firma
de la ceniza): el calor del cráter sube la BTD, así que el píxel caliente nunca es el mínimo y no puede fabricar un
disparo. Dispara con dos cuadros seguidos bajo el umbral, que es el percentil 5 de 2025 a esa hora.

**Lo que salió.**

- **En el año tranquilo casi no dispara**: 3,2 % de los cuadros de 2025 (tope del criterio 5 %). Ve una firma de
  1 K en 2 píxeles el 79 % de las veces y una de 0,33 K el 14 % (el anillo: 59 % y 1 %).
- **Alcanza a VOLCAT donde la pluma está pegada al cráter.** 14-11: 20 de 31 cuadros. 10-11: 8 de 8. 28-10: 15 de 26.
  Esperado por azar en 2025: 4,1 cuadros en total; alcanzados 44 (p25 = 2e-34).
- **No alcanza donde la pluma está lejos**: el 08-11 (pluma de 15 a 40 km al SSE) da 0 de 13, y ese es justamente el
  día que mejor ve el anillo de S23. Las dos reglas se complementan (§3).
- **Separa los cuadros de VOLCAT de los otros cuadros de 2026, de día.** De 12 a 24 UTC alcanza el 49 % de los P y
  el 13 % de los N de 2026 a la misma hora (Fisher p = 8e-13). Sacando cualquier día, el peor pN es 1e-4 (sin el
  14-11) y R va de 0,39 a 0,53.
- **Pero en 2026 la zona está "encendida" mucho más que en 2025.** Dispara en el 8,6 % de los cuadros de día y el
  24 % de los de noche, contra 3,2 % en 2025 (4,3 % de noche). Pasa desde el 21-09, antes del calor del 24-10. VOLCAT
  casi no tiene cuadros de noche (6 de 100), así que de noche no hay con qué comparar.

**Qué puede ser lo de la noche.** Tres candidatos, sin prueba para ninguno: (a) la pluma diaria que Nicolás ve en
cámaras, que de noche no dibuja VOLCAT; (b) el depósito de ceniza alrededor del cráter, que baja la BTD del suelo
(los silicatos emiten menos a 11 que a 12 µm); (c) diferencia de nieve en la cumbre entre 2025 y 2026. Los píxeles que
más disparan son los de la fila sur del bloque (4,6 a 5,2 km al S y SE del cráter) y el del cráter mismo (1,2 km).

**Lectura honesta.** Es la primera vez que una regla propia, con criterio previo, alcanza el 14-11. La regla es
simple y sale entera de 2025. Lo que la debilita: los 100 cuadros P ya se habían mirado con otras reglas (no esta
zona), los cuadros seguidos no son independientes (por episodio: 5 de 11), y la zona responde también a algo
permanente de 2026 que no es VOLCAT. Hay que confirmarla en días nuevos (§4).

## 2. Veredicto por la regla

| Prueba | Resultado | Veredicto |
|---|---|---|
| Instrumento 2025 | L1B 99,8 %, ACMF 98,6 %, 0 scans distintos, 0 congelados, BT11 en rango 100 % | pasa |
| Ensayo en seco 2025 (cada día sin sí mismo) | 176 de 5.499 cuadros (0,032); media por día 0,026; noche 03 a 09 UTC 63 de 1.453 | pasa (≤ 0,05) |
| Poder (2 píxeles, 200 pares) | 0,33 K: 0,14; 0,97 K: 0,785 | |
| R contra VOLCAT 2026 | 44 de 93 P evaluados (0,47), en 4 de 9 días con P evaluado | |
| p25 | esperado 4,1; p = 1,8e-34 | ≤ 0,01 |
| pN | P 44 de 93 contra N cercanos 116 de 649 (0,18); p = 2,3e-9 | ≤ 0,05 |
| **Veredicto** | | **ALCANZA** |
| 14-11 solo | 20 de 31; p25 = 8e-20 | **14-11 ALCANZADO** |

Umbral por hora (2025): de noche −0,37 a −0,49 K; de tarde −0,90 a −0,98 K (14 a 20 UTC).

Por día (P evaluados / alcanzados; N de ese día evaluados / con disparo): 25-10 4/0, 84/26 · 28-10 26/15, 75/0 ·
29-10 6/1, 112/1 · 07-11 1/0, 100/5 · 08-11 13/0, 82/52 · 10-11 8/8, 32/20 · 11-11 3/0, 61/14 · 14-11 31/20, 60/28.

## 3. Revisión post hoc (no cambia el veredicto)

`resultados/s25a_posthoc.json`:

- De día (12 a 24 UTC): R 0,49 (43 de 88), N cercanos 0,13, pN 8e-13. De noche: 1 de 5 P, N cercanos 0,30, pN 0,83.
- Sin cada día: R de 0,39 (sin 14-11) a 0,55 (sin 08-11); pN entre 3e-13 y 1,3e-4.
- **Complemento con el anillo (S23b, también post hoc)**, P alcanzados por día, anillo / zona: 28-10 10 de 17 / 15 de 26;
  29-10 3 de 3 / 1 de 6; 08-11 9 de 13 / 0 de 13; 10-11 0 de 2 / 8 de 8; 11-11 3 de 3 / 0 de 3; 14-11 0 de 15 / 20 de
  31. Donde uno no llega, llega el otro. La unión cuadro a cuadro no está calculada.
- Disparos por píxel: (43,47) 5,0 km 239, (43,46) 4,6 km 214, (41,46) 1,2 km 196; los demás 20 a 97.

## 4. Lo que sigue

- **Confirmar en días nuevos**, junto con S23b y con el mismo gatillo (20 P en 2 días desde el 25-11):
  `criterio_confirmacion_2026-11-25.md`, escrito antes de abrir un solo cuadro de esos días. Falta extender
  `s25a_medir.py` para leer los días nuevos que baja `s23b_confirmar.py bajar` (`D:\goes_notas\s23\s23b\`).
- **La noche de 2026**: comprobar con cámaras del OVDAS si hay pluma en las noches que la zona dispara (por ejemplo
  27-09, 04-10, 05-10, 27-10, 12-11, todos con 25 disparos o más en el día y sin P de VOLCAT).
- **Unión con el anillo**: un detector con las dos piezas (anillo para la pluma lejana, zona para la pegada al cráter)
  necesita su propio criterio y su propio ensayo en seco (la falsa alarma de la unión es mayor que la de cada una).

## 5. Videos (fuera del repo, licencia SSEC)

En `C:\Users\nmend\Downloads\`: `s25a_lado_a_lado_volcat_vs_zona_crater_chillan_<día>_10min.mp4` para 14-11, 28-10,
10-11 y 08-11 (de 09:00 a 20:50 hora de Chile). Izquierda VOLCAT tal cual (±0,7°); derecha el IR de 11 µm en gris, mismo
encuadre, anillos de 10, 25 y 50 km y la zona de 4 km en punteado amarillo. Píxeles llenos: rojo cuando la regla
dispara (los dos píxeles que hacen S), naranjo cuando S queda bajo el umbral en un cuadro suelto.

## 6. Lo que puede estar mal

- La base de cada píxel es de un año: la nieve de la cumbre en 2025 no es la de 2026, y dentro de la zona no se borra
  nada por la máscara de nubes. Una cumbre con menos nieve o con ceniza encima puede bajar la BTD todo el día.
- p25 trata los cuadros seguidos como independientes: exagera. Por episodio, 5 de 11.
- pN usa cuadros N de 2026 que tienen pluma (Nicolás, cámaras): sólo puede hacer el resultado más débil, no más fuerte.
- No dice si lo detectado es ceniza, ni su altura, ni su dirección (la zona es casi un punto para píxeles de 2 km).
