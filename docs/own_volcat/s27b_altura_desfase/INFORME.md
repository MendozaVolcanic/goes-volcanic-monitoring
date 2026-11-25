# S27b: altura de la pluma por la rapidez del pulso, del cráter al anillo. Informe, 25-11-2026

Criterio `criterio_2026-11-25.md`, commit `adace39`, empujado a las 17:26 UTC antes de bajar el viento que faltaba y
antes de calcular una altura con datos de pluma. Código en `scripts/` (`s27b_comun.py` reglas, `s27b_resolucion.py`
estimación previa, `s27b_medir.py` emparejamiento y medida, `s27b_lado_a_lado.py` video). Resultados en `resultados/`
(`s27b_resolucion.json`, `s27b_pares.json`, `s27b_resultado.json`); log en `D:\goes_notas\s27b_medir.log`. Viento GFS
en `D:\goes_notas\s22\s22c\gfs\` (se agregaron 28-10 18 y 19 UTC). **Es desarrollo**: días ya mirados.

**En una línea: NO DECIDIBLE por la regla. A la hora de la sombra no hay pulso que seguir, y la única llegada de esa
tarde tiene dos pulsos candidatos que dan la misma banda (de la cumbre a 7,5 km). La rapidez sí corta la ambigüedad
de S22c entre capa baja y capa alta, pero no fija la altura dentro de la capa baja.**

## 1. Para geólogo

**El fenómeno.** Una pluma pasiva viaja con el viento de su altura. Con el rumbo solo (S22c) no se podía decir si la
pluma del 08-11 iba a 5 km o a 12 km: el viento gira con la altura y el paralaje de GOES-19 gira el rumbo aparente de
la misma manera. La rapidez no se compensa así: esa tarde el viento sopla a 3 a 6 m/s hasta 8 km y a 10 a 35 m/s más
arriba. Si un pulso sale del cráter y se ve llegar a 16 km una hora y media después, viajó a 3 m/s: va bajo. Si
llega en media hora, viajó a 9 m/s: va alto.

**Lo que se puede esperar con este instrumento (antes de medir).** El cuadro es de 10 min y el píxel de 2,8 km en
sentido N-S. Con plumas sintéticas que viajan con el viento GFS exacto: la rapidez sola deja bandas de 4 a 5,5 km de
ancho en la capa baja, porque en ella el viento casi no cambia con la altura. Sí separa capa baja de capa alta casi
siempre. Junto con el rumbo restringe a 2 km sólo en una tarde con viento firme; en la calma de la hora de la sombra
(14:53 del 08-11) la banda ideal mide 4 a 5 km. Esa estimación también mostró un defecto que se corrigió antes de
medir: la regla de rumbo de S22c excluía las capas en calma, y la sombra estaba justo en una capa en calma.

**El problema real: casi no hay pulsos que seguir.** En los seis días mirados, con 20 min de quietud exigidos antes
del pulso y antes de la llegada, hay 5 llegadas al anillo y sólo 2 con un pulso del cráter antes:

- **28-10, llegada 19:20 UTC, pulso único 18:10 (70 min).** Las otras dos llegadas del día empiezan junto con la zona
  (18:10, no hay tránsito que medir) o ya no tienen pulso propio (20:00).
- **08-11, llegada 17:30 UTC, dos pulsos posibles: 15:50 (100 min) o 17:00 (30 min).** La zona del cráter está quieta
  de 11:10 a 15:50, así que a la hora de la sombra no hay nada que seguir.
- 11-11 17:00 empieza junto con la zona; 29-10, 10-11 y 14-11 no tienen llegada con quietud previa (el 10-11 y el 14-11
  el anillo no dispara: la pluma quedó pegada al cráter).

**Lo que salió.**

- **08-11 (la prueba que decide): NO DECIDIBLE.** Los dos pulsos candidatos dan banda: 3,2 a 7,6 km (pulso 15:50,
  rapidez 2,0 a 3,2 m/s) y 3,3 a 7,5 km (pulso 17:00, 5,6 a 10,6 m/s). La regla resuelve la ambigüedad sólo si uno
  de los dos no tiene altura compatible, y los dos la tienen. **Mirado después (no cambia el veredicto)**: las dos
  bandas son casi iguales, tocan los 4,7 km de la sombra y excluyen todo lo que está sobre 7,6 km. O sea, la rapidez
  dice lo que el rumbo no decía: la pluma de esa tarde va en la capa baja y no a 9 a 14 km. No dice más que eso.
- **Esa llegada no es un pulso que viaja.** En los 6 cuadros siguientes a la llegada, los píxeles del anillo están a
  20,6, 22,6, 21,8, 21,3, 25,2 y 24,5 km del cráter: avanzan 1,3 m/s, mucho menos que cualquiera de las dos rapideces.
  Es una pluma continua estirada al SSE que el anillo empieza a ver a las 17:20, no una bocanada que llega. El
  supuesto del método (lo que llega es lo que salió) no se cumple.
- **28-10 19:20 (informativo, sin verdad ese día): restringe por la regla, pero la precisión es falsa.** La banda es
  4,1 a 4,2 km (h* 4,2; VOLCAT pinta 3,5 km en ese cuadro). Sale así porque el GFS sopla hacia el N de 5 a 11 km y la
  pluma iba hacia el S (tajada de 150° a 180°): sobre 4,2 km el rumbo la excluye, y bajo 4,1 km el modelo está en calma
  (menos de 2 m/s) y la rapidez la excluye. Los 0,1 km son el borde de la capa en calma del modelo, no una medida. Lo
  que sí dice es que la pluma iba contra el viento del modelo en toda la columna sobre 4,2 km: o va baja y la mueve un
  flujo de valle que el GFS no tiene, o el GFS está mal esa tarde. La llegada de las 20:00 tampoco avanza (2,2 m/s).

**Lectura honesta.** La idea física es correcta y el caso ideal lo muestra: la rapidez distingue capa baja de capa alta.
Pero el instrumento no ve pulsos: el detector marca la pluma cuando está, y en Chillán la pluma es casi siempre
continua; los "pulsos" de la zona son cuadros sueltos que no se pueden unir con seguridad a una llegada. Con eso, el
método da como mucho "la pluma va bajo 8 km" en una tarde con viento firme, y nada a la hora de la sombra.

## 2. Veredicto por la regla

| Prueba | Resultado | Veredicto |
|---|---|---|
| Resolución esperable (§1 del criterio) | Rapidez sola: 3 de 169 casos restringen (pluma a 10 km). Con rumbo: 1,7 a 2,3 km sólo la tarde del 08-11 a 3,6 a 4,7 km. En calma, 4 a 5 km | estimación previa |
| Emparejamiento (§2) | 5 llegadas, 1 par único (28-10 19:20), 1 ambiguo (08-11 17:30), 3 sin pulso | `s27b_pares.json` |
| **Sombra 08-11 (decide)**: pares con pulso de 11:53 a 17:53 | Llegada 17:30, pulsos 15:50 y 17:00, los dos con banda (3,2 a 7,6 y 3,3 a 7,5 km): ambigua sin resolver | **NO DECIDIBLE** |
| 28-10 19:20 (informativo) | Banda 4,1 a 4,2 km, h* 4,2; VOLCAT 3,5 km | restringe (borde de calma del GFS) |
| Avance dentro del anillo (informativo) | 08-11 17:30: 1,3 m/s en 6 cuadros; 28-10 20:00: 2,2 m/s | pluma continua, no pulso |
| **Conjunto** | | **NO DECIDIBLE** |

## 3. Expectativa escrita antes contra lo que salió

Esperaba que el pulso de las 17:00 del 08-11 quedara sin altura (rapidez de capa alta, rumbo al S) y que la regla
resolviera hacia el de las 15:50, con veredicto SÓLO SEPARA CAPAS. **Me equivoqué en el mecanismo**: la rapidez del
pulso de las 17:00 (5,6 a 10,6 m/s, con el error del GFS 3,6 a 13 m/s) también calza con la capa baja, donde el GFS
tiene 3 a 6 m/s. Con 30 min de viaje la rapidez es poco precisa y no excluye nada. El resultado práctico (banda bajo
8 km) es el que esperaba; el veredicto por la regla no.

## 4. Lo que puede estar mal

- **Dos casos.** Nada de esto es estadística.
- **La suposición de fondo falla**: lo que llega al anillo no es necesariamente lo que salió del cráter. El avance
  dentro del anillo dice que en los dos días es pluma continua.
- **Los pulsos de la zona son de un solo cuadro** (a propósito: un pulso rápido sale de 4 km en un cuadro), y la zona
  dispara de más en 2026 (S25a, S26b); varios "pulsos" pueden ser ruido.
- **GFS de 25 km**: falla en calma y en los flujos de valle (H10, S22c); el 28-10 sopla al N mientras la pluma va al S.
- **La sombra es de la mañana** y la llegada de la tarde (2,5 h después); se supone que la columna no cambió.

## 5. Video

`C:\Users\nmend\Downloads\s27b_lado_a_lado_altura_por_rapidez_chillan_2026-10-28_1730-2030UTC_10min.mp4` y
`C:\Users\nmend\Downloads\s27b_lado_a_lado_altura_por_rapidez_chillan_2026-11-08_1530-1830UTC_10min.mp4` (fuera del
repo por la licencia de SSEC). Izquierda VOLCAT tal cual; derecha el IR de 11 µm con rojo = anillo y amarillo = zona
del cráter (como S26a). En el cuadro del pulso y en el de la llegada se detienen 1,5 s y llevan escrito Δt, la
distancia, la rapidez y la banda de alturas. El 08-11 a las 17:30 VOLCAT pinta la pluma en 1,5 a 3,5 km a 15 a 20 km
al SSE, donde marca el anillo.

## 6. Lo que sigue

Para que la rapidez sirva hay que **seguir la pluma** y no emparejar disparos: medir cuánto se corre el borde de la
pluma entre cuadros dentro del anillo (el método B de aquí, con un criterio propio), en tardes con una bocanada aislada.
Con pluma continua, lo que se mueve es el frente al empezar una emisión nueva; eso pide un día con pausa larga y
reanudación, que en sep-nov 2026 casi no hay (todos los días tienen pluma). Y una verdad de altura en una tarde con
viento firme, no en calma.
