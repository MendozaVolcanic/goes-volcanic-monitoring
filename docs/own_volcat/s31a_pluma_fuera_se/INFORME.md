**Veredicto: SIN PODER. En oct-nov 2026 VOLCAT casi nunca dibuja la pluma de Chillán fuera del SE de forma que dure: de 30 cuadros "fuera del SE" en 7 días, casi todos son pedazos de 1 a 4 píxeles pegados al cráter que diez minutos después vuelven al SE, y la única pluma que gira de verdad (10-11, 22:20 a 23:20 UTC, hacia el NE y E) cae en un día en que el anillo no disparó. Con 4 días posibles como máximo, el nulo contra el SE habitual no puede bajar de p 0,0625, y ni VOLCAT contra sí mismo un cuadro antes pasa un nulo a 0,01. No se cruzó ningún disparo.**

# S31a: ¿el anillo del detector sigue la pluma cuando el viento la lleva fuera del SE? Informe, 26-11-2026

Criterio y decisión previa `criterio_2026-11-26.md` (commit `a3fa424`, empujado antes de cualquier cruce; en esta
sesión no se abrió la tabla de disparos de S26a ni la tabla por cuadro de S30b). Código `scripts/s31a_inventario.py`
(inventario sólo de VOLCAT) y `scripts/s31a_poder.py` (piso del p y control positivo). Cifras en `resultados/`. Las
huellas en la grilla ABI (derivadas de PNG de SSEC) quedan en `D:\goes_notas\s31\s31a\huellas_P.npz`, fuera del repo.
Ningún día posterior al 24-11; nada de `s23b_confirmar.py`, `s30a_confirmar.py` ni del CSV de días nuevos.

## 1. Para geólogo

**La pregunta.** S30b mostró que el anillo del detector S26a (4 a 40 km del cráter, tajadas de 30°) dispara hacia el
lado donde VOLCAT dibuja la pluma, pero no más que hacia donde va la pluma de cualquier otro día. Con el viento de
primavera, la pluma de Chillán va al SE casi siempre, y el anillo ya prefería el SE en 2025, sin pluma. Para saber si el
anillo ve **esta** pluma o sólo apunta al SE por costumbre, hay que mirar los momentos en que el viento la llevó hacia
otro lado.

**Lo que dibuja VOLCAT fuera del SE.** De los 100 cuadros con pluma anclada al cráter (20-10 a 24-11; no hay clases de
VOLCAT antes del 20-10), 90 tienen rumbo y 30 lo tienen fuera de 90° a 180°, en 7 días. Pero mirados uno a uno no son
lo que la pregunta necesita:

- La mayoría son huellas de 1 a 4 píxeles de 2 km que apenas salen del bloque del cráter (llegan a 4 a 8 km). En el
  cuadro anterior y en el siguiente la pluma está al SE: 14 de los 30 no tienen ningún vecino también fuera del SE. El
  14-11, por ejemplo, la pluma va al SE toda la tarde y diez veces aparece un pedacito al N o al NW que dura un cuadro.
- Un mismo píxel, a 325° y 4,8 km del cráter, aparece solo en tres cuadros de dos días (08-11 18:10 y 19:30, 11-11
  18:00). Parece un borde fijo del dibujo o de la georreferencia, no ceniza que se fue al NW.
- **La única pluma que gira de verdad** es la del 10-11 entre 22:20 y 23:20 UTC: seis cuadros seguidos, de 5 a 10
  píxeles en el anillo, hacia el NE y el E (40° a 90°), hasta 9 km. Fuera de eso hay un cuadro al W el 07-11 a las 19:50
  y dos en la franja vecina del SE (28-10 a 190°, 29-10 a 77°), donde una tajada puede coincidir a la vez con la pluma y
  con el SE habitual.

**Por qué no se puede decidir.** Se publicó en S30b en qué días el anillo tuvo algún cuadro con pluma a la hora de un
disparo: 28-10, 29-10, 08-11 y 11-11. Esos son los únicos días en que la prueba podría evaluar algo, y en ninguno la
pluma giró de forma que dure: el 08-11 y el 11-11 sólo tienen los pedacitos de 1 a 2 píxeles, y el 28-10 y el 29-10 los
cuadros de la franja vecina más pedacitos. En el 10-11 y el 07-11, los dos días con la pluma girada de verdad, el anillo
no disparó a la hora de ningún cuadro con pluma.

Con el día como unidad (las rachas de S28b), la comparación que importa ("¿marca hacia la pluma de ese momento o hacia
el SE?") se hace día por día y se le asignan signos al azar: con 4 días hay 16 maneras, y el p más chico posible es
1/16 = 0,0625. Para llegar a 0,01 hacen falta 7 días.

Y aun con más días, el estrato no sirve: el control positivo de S30b (un "detector" perfecto que marca donde VOLCAT
dibujó la pluma un cuadro antes) coincide en 13 de 27 cuadros fuera del SE y no pasa ningún nulo a 0,01 (girada p 0,038;
otro día fuera del SE p 0,16; contra el SE habitual p 0,75). Lo que VOLCAT dibuja fuera del SE no mantiene su rumbo
diez minutos, así que ningún detector podría mostrar que lo sigue.

**Lectura honesta.** La pregunta sigue abierta, y con los datos de oct-nov no tiene respuesta: no es que el anillo
falle, es que VOLCAT no ofrece momentos en que la pluma vaya con claridad a otro lado y el anillo esté mirando. Que el
anillo no disparara durante el giro del 10-11 no dice nada por sí solo: no disparó en ningún cuadro con pluma ese día,
tampoco cuando la pluma iba al SE (S30b).

## 2. Cifras (sólo VOLCAT)

| Qué | Valor |
|---|---|
| Cuadros P (20-10 a 24-11), con PNG, con rumbo | 100, 94, 90 |
| Con rumbo fuera de 90° a 180° | 30 en 7 días: 28-10 (6), 29-10 (2), 07-11 (1), 08-11 (4), 10-11 (6), 11-11 (1), 14-11 (10) |
| Con algún cuadro vecino también fuera del SE | 16 de 30 (6 de ellos el 10-11) |
| Que llegan a 8 km o más del cráter | 8 de 30: 28-10 18:30, 28-10 19:50 (píxeles repartidos alrededor del cráter, concentración circular 0,08, sin rumbo real), 29-10 01:00, 07-11 19:50 y cuatro del 10-11 |
| Días del estrato con anillo evaluable (publicado por S30b) | 4: 28-10, 29-10, 08-11, 11-11 |
| Piso del p, contra el SE habitual (2^n) | 0,0625 con n = 4 |
| Piso del p, huella girada (12^n) y otro día fuera del SE (6^n) | 0,00005 y 0,0008 con n = 4 (no responden la pregunta o no tienen poder) |
| Oráculo (VOLCAT un cuadro antes) en el estrato | 13 de 27 coinciden, 16 de 27 caen en el SE habitual; p girada 0,038, otro día 0,16, contra SE 0,75 |
| Cuadros "otro" con huella anclada fuera del SE (no P, informativo) | 27, 13 de ellos el 16-11 (sistema meteorológico grande, manto) |

## 3. Lo que sigue

- **Verdad propia de dirección**: las cámaras del OVDAS (decisión 3 de S28) dicen hacia dónde fue la pluma sin depender
  de que VOLCAT la dibuje. Nicolás ya vio el 05-11 una pluma hacia el E todo el día que VOLCAT no marcó. Con las
  cámaras se podrían juntar días con pluma fuera del SE, con criterio antes de mirar el detector (sería desarrollo para
  días hasta el 24-11).
- **Días nuevos**: si se quiere repetir con VOLCAT (decisión 2 de S30b), fijar antes de mirar qué es una pluma fuera del
  SE que dure (por ejemplo, 3 cuadros seguidos o más con 3 píxeles o más en el anillo) y exigir 7 días así con el
  anillo evaluable. Con el ritmo de oct-nov (un solo día así en los 34 días con clase de VOLCAT) tomaría muchos meses. El criterio §5 dice "35 días" por un error de conteo (20-10 a 19-11 más 22 a 24-11 son 34); no cambia nada.

## 4. Lo que no puede decir

Nada sobre si el anillo sigue o no la pluma: la prueba no se hizo porque no podía decidir. Nada de días posteriores al
24-11. Los días mirados ya los había visto el desarrollo (S26a, S30b): aunque se hubiera medido, sería desarrollo, no
confirmación. VOLCAT no es verdad de terreno: que no dibuje la pluma fuera del SE no prueba que no haya ido para allá.
