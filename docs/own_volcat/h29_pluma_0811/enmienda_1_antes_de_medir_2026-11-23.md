# H29, enmienda 1: cambios tras el ensayo en seco, ANTES de leer temperaturas del 08-11

Escrita el 23-11-2026 después del ensayo en seco del criterio §7 (04-11 en el lugar del 08-11, huella del 08-11) y
antes de correr nada sobre el 08-11. No es post hoc respecto de la pluma: el 08-11 no se ha medido. Salida del
ensayo: `resultados/seco_0411.log`.

## Lo que mostró el ensayo en seco

1. **El z robusto no controla las falsas alarmas.** Con todo cielo el nulo A de M1 tiene colas pesadas: 16 días
   entre −0,33 y +0,12 K con la mayoría cerca de 0, así que la MAD queda chica y un día sin pluma cae a z ≤ −2 con
   −0,25 K. Dejando un día fuera, **5 de 16 días nulos dan z ≤ −2** (31 %, el criterio tolera 10 %): por la regla
   del criterio la prueba saldría INVÁLIDA. El propio 04-11 dio z = −2,02 y p = 0,052: sin pluma, casi SOSPECHA.
2. **La capa sintética se pintaba encima de nubes más altas.** En los días nulos con nube sobre el píxel (BT11
   observada bajo la temperatura de la capa a 2,5 o 3,5 km), la mezcla de radiancias calentaba el píxel hasta
   +25 K. Físicamente una capa a 3,5 km bajo una nube más alta no se ve. Por eso la potencia salía plana (M2: 0,06
   para cualquier f y ε) y no medía lo que dice.

## Cambios

1. **Nulo A por rango, no por z.** Lado de señal temporal: el estadístico del 08-11 queda **bajo el mínimo** de los
   días nulos válidos. Lado nulo temporal: queda **en o sobre el percentil 25** de los días nulos. Con n días nulos,
   dejar uno fuera da falsas alarmas = 1/n por construcción (6 % con 17), bajo el 10 % del criterio; se sigue
   calculando y se informa.
2. **Potencia por rango.** Un día nulo pintado cuenta como detectado si su estadístico queda bajo el mínimo de los
   otros días nulos sin pintar.
3. **Capa oculta bajo nube más fría.** Si la BT11 observada del píxel es menor o igual que T_tope, la capa no cambia
   el píxel (queda bajo algo más frío). En el resto se pinta como dice el criterio §5.
4. **La tabla de veredicto queda así** (M1 y M2 por separado):

| Veredicto | Condición |
|---|---|
| INVÁLIDO | falsas alarmas del nulo A (dejando uno fuera) > 10 % |
| SIN DATO | < 10 píxeles-cuadro válidos el 08-11, < 6 días nulos válidos o < 30 corrimientos válidos |
| SEÑAL | bajo el mínimo del nulo A y p ≤ 0,05 |
| SOSPECHA | sólo una de las dos |
| SIN FIRMA | en o sobre el percentil 25 del nulo A, p > 0,20 y potencia de la referencia ≥ 0,8 |
| SIN PODER | en o sobre el percentil 25 del nulo A y p > 0,20, pero potencia de la referencia < 0,8 |
| NO CONCLUYENTE | cualquier otro caso |

Nada más cambia: medidas, población, huella, nulo B, pluma de referencia (f = 0,4, ε11 = 0,5) y umbral de potencia
(0,8) son los del criterio. Se repite el ensayo en seco con estos cambios antes de medir el 08-11; si el 04-11 sale
SEÑAL o SOSPECHA, se dice y no se vuelve a cambiar la regla.
