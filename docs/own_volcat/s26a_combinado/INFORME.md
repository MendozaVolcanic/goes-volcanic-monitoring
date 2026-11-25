# S26a: un solo detector, zona del cráter O anillo. Informe, 25-11-2026

Criterio `criterio_2026-11-25.md` (commit `28f963b`), empujado antes de calcular un solo disparo de la unión. Código
`scripts/s26a_medir.py` (commit `2b82a91`), videos `scripts/s26a_lado_a_lado.py`. Resultados en `resultados/`
(`s26a_seco.json`, `s26a_desarrollo.json`); la tabla por cuadro de 2026 en `D:\goes_notas\s26\s26a\tabla_2026.csv`.
Ningún día desde el 25-11 (reservados para las confirmaciones).

**En una línea: la unión del cráter y el anillo es el primer detector propio que llega a dos de cada tres cuadros de
VOLCAT (63 de 93), con falsa alarma de 4,9 % en el año tranquilo. Es desarrollo: los días ya se habían mirado.**

## 1. Para geólogo

**El fenómeno.** Una pluma de Chillán vive en dos lugares según el momento y el viento: pegada al cráter (el pulso
recién salido, o una pluma débil que no se aleja) y lejos del cráter, a 10 o 40 km, cuando el viento la estira. Hasta
ahora teníamos una regla para cada lugar: la zona de 0 a 4 km (S25a) y el anillo de 4 a 40 km (S23b). Nicolás va a
mirar un solo detector contra VOLCAT, así que aquí se juntan: el detector marca pluma si marca cualquiera de las dos.

**El costo de juntar.** Cada regla, sola, se equivoca en cerca del 4 % de los cuadros de oct-nov 2025 (año sin
pluma). Juntas se equivocan donde se equivoca una u otra: 5,15 %, apenas sobre el tope de 5 %. El criterio decía de
antemano cómo corregirlo: bajar un poco el umbral de las dos por igual. Con el percentil 4,75 en vez de 5, la unión
queda en 4,9 % (media por día 4,3 %). El cambio es chico y sale sólo de 2025.

**Lo que salió (desarrollo).**

- **Llega a 63 de los 93 cuadros de VOLCAT** que se pueden evaluar (68 %). Por azar, con la falsa alarma de 2025 a esa
  hora, se esperarían 5,9. Cada parte sola llegaba a 23 y 42.
- **Las dos partes casi nunca marcan lo mismo.** En 63 cuadros alcanzados, sólo 2 los marcan las dos. Por día (P de
  VOLCAT alcanzados; anillo, zona, unión):

  | Día | Cuadros VOLCAT evaluados | Anillo | Zona | Unión | Lectura |
  |---|---|---|---|---|---|
  | 28-10 | 26 | 8 | 13 | **20** | pluma que pasa del cráter al SE; cada parte ve un tramo |
  | 29-10 (noche) | 6 | 3 | 1 | 3 | anillo |
  | 08-11 | 13 | 9 | 0 | 9 | pluma lejana, 15 a 40 km al SSE: sólo el anillo |
  | 10-11 | 8 | 0 | 8 | 8 | pluma sobre el cráter: sólo la zona |
  | 11-11 | 3 | 3 | 0 | 3 | anillo |
  | 14-11 | 31 | 0 | 20 | 20 | pluma pegada al cráter: sólo la zona |
  | 25-10, 24-10, 07-11 | 6 | 0 | 0 | 0 | ninguna (pocos cuadros, pluma tenue) |

  Es lo que se espera si las dos reglas miran de verdad lugares distintos de la misma pluma, y no la misma cosa dos
  veces.
- **Separa los cuadros de VOLCAT de los otros cuadros de 2026 a la misma hora.** De los cuadros sin VOLCAT a ±60 min
  de uno con VOLCAT, la unión marca el 17 % (113 de 649), contra el 68 % de los de VOLCAT (Fisher p = 2e-22).
- **Sacando cualquier día, se sostiene**: R entre 0,64 (sin el 28-10) y 0,71; p25 bajo 1e-34 y pN bajo 1e-14 en todos.
- **Por episodio** (cuadros de VOLCAT separados por menos de una hora): 6 de 11.

**Lo que hereda de la zona.** En 2026, fuera de VOLCAT, la unión marca el 5,4 % de los cuadros de día (2025: 3,9 %) y
el 19 % de los de noche (2025: 6,7 %). El exceso nocturno viene de la zona del cráter (S25a): de noche VOLCAT casi
no dibuja, así que no hay con qué decidir si es la pluma diaria que Nicolás ve en cámaras, depósito de ceniza o nieve.
Una marca del detector sin VOLCAT en 2026 no es falsa alarma segura.

**Lectura honesta.** Es el mejor resultado de todos los detectores propios desde S20, y la corrección del umbral se
fijó antes de mirar. Pero es **desarrollo**: los 100 cuadros de VOLCAT ya se habían mirado con el anillo y con la
zona, y la unión se armó justamente porque se vio que se complementan. Lo que vale como prueba es la confirmación en
días nuevos (§4), que espera a que VOLCAT dibuje 20 cuadros en 2 días desde el 25-11 (al 25-11 a las 14:30 UTC: 0).

## 2. Cifras por el criterio

| Prueba | Resultado | Por el criterio |
|---|---|---|
| Comprobación de código (percentil 5) | anillo solo 25 de 54, seco 0,04279; zona sola 44 de 93, seco 0,0320: idénticos a lo publicado | pasa |
| Seco de la unión a percentil 5 | global 0,0515 (283 de 5.499); media por día 0,0457 | no pasa |
| Seco de la unión a percentil 4,75 | global 0,0489 (269 de 5.499); media por día 0,0431 | **p* = 4,75** |
| Poder | no se recalcula; a percentil 5: anillo 0,01 / 0,585, zona 0,14 / 0,785 (0,33 / 0,97 K); a 4,75 algo menor | |
| R unión (2026, desarrollo) | 63 de 93 (0,68), alcanzados en 6 de 9 días con P evaluado | ≥ 0,40, ≥ 3 días |
| p25 | esperado 5,9; p = 6e-53 | ≤ 0,01 |
| pN | P 63 de 93 contra N cercanos 113 de 649; p = 1,8e-22 | ≤ 0,05 |
| **Rótulo** | | **ALCANZA (desarrollo)** |
| Anillo a 4,75 | 23 de 54 (a percentil 5 eran 25) | informativo |
| Zona a 4,75 | 42 de 93 (a percentil 5 eran 44) | informativo |

Expectativa escrita antes (criterio §6) contra lo que salió: el seco a percentil 5 fue 0,0515, menor que lo esperado
(0,06 a 0,075), porque las falsas alarmas de las dos partes en 2025 coinciden más de lo que supuse (36 de los 319
disparos de las partes); por eso p* quedó en 4,75 y no entre 3,5 y 4,5. R salió 0,68 (esperaba 0,55 a 0,65). **Me equivoqué en pN**:
esperaba que fuera más débil que el de cada parte y salió más fuerte (2e-22 contra 3e-16 del anillo y 6e-9 de la
zona), porque la unión gana muchos P y los N cercanos casi no suben (110 a 113).

## 3. Videos lado a lado (no deciden)

`C:\Users\nmend\Downloads\s26a_lado_a_lado_volcat_vs_crater_y_anillo_chillan_<día>_10min.mp4` para 28-10, 08-11,
10-11, 11-11 y 14-11 (12 a 24 UTC), y `..._2026-10-29_0000-0200UTC_10min.mp4`. Izquierda VOLCAT tal cual; derecha el
IR de 11 µm en gris con **rojo** = anillo (los 8 píxeles de la tajada) y **amarillo** = zona del cráter (los 2
píxeles más bajos); celeste translúcido = nube que el anillo no usa. Anillos de 10, 25 y 50 km; punteado blanco 4 km,
punteado naranjo 40 km. Los PNG de VOLCAT son de SSEC y no van al repo.

## 4. Lo que sigue

- **Confirmación en días nuevos** (criterio §5): cuando `s23b_confirmar.py contar <día>` diga LISTO PARA MEDIR (20 P en
  2 días desde el 25-11), en este orden y con los mismos datos: S23b (`s23b_confirmar.py medir`), S25a
  (`s26a_medir.py confirmar_s25a`: la zona sola a percentil 5 con su criterio congelado, agregada en esta sesión antes
  de bajar un solo cuadro nuevo), y `s26a_medir.py confirmar`. Los dos subcomandos se niegan a correr antes del
  gatillo y sin los resultados previos en el orden. Ninguna anula a otra; el titular es el de la unión.
- **Cámaras del OVDAS**: las noches en que la zona marca sin VOLCAT (S25a, decisión 1) son las que más pesan en la
  falsa alarma de la unión en 2026.

## 5. Lo que no puede decir

Que lo marcado sea ceniza y no gas, depósito o nieve; la altura; nada con más de la mitad del anillo nublado. Que la
unión funcione en días que nadie miró: eso lo dice la confirmación.
