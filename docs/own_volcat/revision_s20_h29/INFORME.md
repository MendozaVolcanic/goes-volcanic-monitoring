# Revisión S20 de H29 (PR 107): la BTD baja del 08-11 ¿sigue a la huella de VOLCAT? Informe, 23-11-2026

Criterio: `criterio_2026-11-23.md`, commit `1b430f0`, empujado antes de medir. Script propio (no importa nada de
H29): `scripts/s20_h29_seguimiento.py`. Salida: `resultados/s20_h29_seguimiento.json` y `resultados/s20_h29.log`.

## Resultado en corto

1. **H29 se reproduce con código propio.** M1 (BTD pareada por BT11 y cota) de los 17 píxeles-cuadro lejanos da
   −0,3725 K, contra −0,372 K de H29. La huella que usó H29 coincide píxel a píxel con mi decodificación del PNG en
   los cuadros de 20:10 y 21:30 (2 y 4 píxeles lejanos), con el corrimiento de H14 (1 fila al N, 1 columna al O),
   que H14 midió contra los archivos de evento del 14-11 (IoU mediano 0,19 sin corregir, 0,42 corregido).
2. **Prueba que decide esta revisión, más de 30 km: NO CONCLUYENTE.** Dentro de cada cuadro, los píxeles que VOLCAT
   marca en ese cuadro tienen una BTD pareada 0,23 K más baja que las otras posiciones lejanas que VOLCAT marca en
   otros cuadros (mediana de 10 cuadros; 6 de 10 negativos). Si se reparten las huellas al azar entre los cuadros,
   eso sale igual o más bajo el 9,5 % de las veces (p = 0,095). La prueba tenía poder: una baja de 0,33 K inyectada
   justo en los píxeles marcados da p = 0,000 en las 200 réplicas.
3. **Sensibilidad, más de 15 km (no decide por el criterio): la firma SÍ sigue a la huella.** Con 35 cuadros (15:20
   a 22:00) y 46 posiciones, los píxeles marcados en cada cuadro quedan 0,48 K bajo las demás posiciones que VOLCAT
   marca en otros cuadros, y ninguna de 10.000 reparticiones al azar llega a eso (p < 0,0001).

| Población | Cuadros | Posiciones | T (K) | p | Lectura por el criterio |
|---|---|---|---|---|---|
| Más de 30 km (decide) | 10 | 14 | −0,23 | 0,095 | NO CONCLUYENTE |
| Más de 15 km (sensibilidad) | 35 | 46 | −0,48 | < 0,0001 | (sería SIGUE A LA HUELLA) |
| Control positivo, más de 30 km, −0,33 K inyectados | 10 | 14 | | 0,000 (200 de 200) | potencia 1,0 |

D por cuadro a más de 30 km (K): 20:10 +0,06; 20:20 +0,12; 20:30 −0,83; 20:40 −0,20; 20:50 −0,26; 21:00 +0,34;
21:10 +0,09; 21:30 −0,63; 21:40 −0,41; 22:00 −0,44.

## Qué significa

- La SEÑAL de H29 es un número correcto: el cálculo se reproduce y la huella está bien leída.
- Este nulo controla lo que los de H29 no controlaban: una estructura del campo de BTD que esté quieta en la zona
  lejana durante la tarde (una banda que no se mueve con la pluma) afecta por igual a la huella verdadera y a las
  repartidas, y se cancela. Lo que queda es si la BTD baja se mueve **con** el objeto de VOLCAT.
- Entre 15 y 60 km se mueve con él, con mucha claridad. Más allá de 30 km, con sólo 10 cuadros y 1 a 4 píxeles por
  cuadro, la tendencia es la misma pero no alcanza (p 0,095). Eso no es "sin firma": el control positivo muestra que
  una firma de 0,33 K pegada a la huella se habría visto.
- **Límite de la lectura:** "sigue a la huella" dice que la BTD baja y el objeto de VOLCAT se mueven juntos. No dice
  por sí solo que sea ceniza: si VOLCAT estuviera siguiendo una estructura meteorológica que nace en el cráter,
  también se moverían juntos. Lo que sí descarta, en la población de más de 15 km, es una banda quieta o una
  coincidencia de lugar.
- Lectura conjunta con H29: la atribución de la firma a la pluma pasa de SOSPECHA a **SOSPECHA reforzada**: el
  criterio de esta revisión no llega a decidir, y la sensibilidad, que sí es clara, no decide por regla.

## Lo que puede salir mal

- Los 46 lugares de la sensibilidad no son independientes (vecinos, cuadros seguidos); la permutación reparte
  huellas enteras entre cuadros, así que respeta la forma de cada huella, pero no la autocorrelación en el tiempo.
- Las posiciones de referencia son lugares que VOLCAT marca en otros cuadros: si la pluma real es más ancha que la
  huella, la referencia también tiene pluma y la prueba pierde fuerza (sesgo hacia cero, no hacia señal).
- Un solo evento.
