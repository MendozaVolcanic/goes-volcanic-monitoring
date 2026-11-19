# Criterio declarado ANTES de medir: H3 (cielo despejado modelado y razones β con C10), 19-11-2026

Escrito antes de bajar C10 y antes de calcular cualquier ε o β. Ningún número de esta prueba existe
al escribir esto.

## Pregunta

VOLCAT (SECO, Pavolonis et al. 2015) no usa un umbral de BTD: convierte radiancias en emisividad
efectiva ε contra una radiancia de cielo despejado MODELADA (perfil GFS + modelo radiativo) y mira las
razones β(12/11), β(8,5/11) y β(7,3/11). ¿Hace eso visible, dentro de la huella VOLCAT, una pluma que
en BTD no existe? Si sí, H3 explica por qué VOLCAT ve Chillán y nosotros no.

## Casos (prioridad en este orden)

1. 28-10 22:40, 23:00, 23:20 y 23:40 UTC (C11, C14, C15 en el caché; falta C10).
2. 29-10 01:00, 01:10 y 01:20 UTC (noche cerrada, cenit solar 110 a 113°; hay que bajar todo).
3. 14-11, todos los cuadros con `toca_crater_10km == 1` (16:40 a 22:40 UTC, de día).

Huella = píxeles VOLCAT con ceniza a ≤ 50 km del cráter llevados a la grilla ABI de la ventana
(83 × 94, misma decodificación que `huellas.py` y `pruebaA_28oct.py`), sin dilatar. Cuadros con menos
de 3 píxeles de huella en la ventana se descartan antes de medir.

## Control (pareado por BT11)

- Días candidatos sin pluma VOLCAT anclada: 26, 27, 30 y 31-10 y 01 a 06-11 para los casos 1 y 2;
  01 a 06, 09, 12, 13 y 15-11 para el caso 3. Mismo minuto UTC.
- Para cada cuadro positivo, el control es el día candidato cuya mediana de BT11 sobre los píxeles de
  la huella queda más cerca de la del positivo, elegido mirando SÓLO C14. Si la diferencia supera 3 K,
  ese cuadro queda sin control y se informa aparte (no se fuerza).
- Mismos píxeles en el control (misma huella, mismo lugar, misma hora).

## Señales por píxel

ε(λ) = [R_obs(λ) − R_clr(λ)] / [B_λ(T_tropo) − R_clr(λ)] (ε de tropopausa, SECO/ATBD), con T_tropo del
perfil GFS del ciclo más cercano. β(λ/11) = ln[1 − ε(λ)] / ln[1 − ε(11)] para λ = 12,3 (C15),
8,4 (C11) y 7,3 µm (C10). Coeficientes Planck del NetCDF L1b de cada banda, nunca escritos a mano.

Dos versiones de R_clr:
- **M (modelada)**: perfil GFS archivado (T, humedad, altura geopotencial, temperatura de piel y
  presión de superficie) más un cálculo radiativo de cielo despejado con las funciones de respuesta
  espectral del ABI de GOES-19. El error del modelo se declara midiéndolo contra píxeles despejados
  de las escenas de control (sesgo y desviación por banda) ANTES de mirar la huella.
- **E (empírica, sin modelo)**: por píxel, la mediana de las 3 escenas más tibias en BT11 entre los
  días candidatos al mismo minuto (las cuatro bandas tomadas de esas mismas escenas).

## Métricas

1. Compuerta: G = fracción de píxeles de huella con ε(11) ≥ 0,02 (regla 1 del ATBD §3.4.2.4.1), en el
   positivo y en el control.
2. Separación: AUC de ε(11) y de cada β entre píxeles de huella del positivo y los mismos píxeles del
   control. Para los β, sólo píxeles que pasan la compuerta en su escena; con menos de 20 píxeles en
   cualquiera de los dos grupos, ese β es "no medible".
3. Secundaria (no decide): AUC huella contra anillo de 2 a 6 píxeles alrededor, misma escena.

Se informa por caso y agrupado (los tres casos juntos).

## Decisión (sobre la versión M, agrupada)

- **H3 se sostiene** si G_huella ≥ 0,5, G_huella − G_control ≥ 0,25 y al menos un β tiene
  |AUC − 0,5| ≥ 0,20, con la misma dirección en al menos 2 de los 3 casos.
- **H3 se falsa** si (a) G_huella < 0,10 (la compuerta de VOLCAT, con nuestro mejor modelo, no deja
  pasar la pluma), o (b) G_huella − G_control < 0,10 y los cuatro AUC (ε11 y los tres β) quedan con
  |AUC − 0,5| < 0,10.
- **No concluyente** en cualquier otro caso, y también si el error del modelo en C14 (sesgo medido en
  píxeles despejados de control) supera 3 K: entonces la versión M no vale y se dice.

Atribución (paso 4, no cambia el veredicto): si M separa y E no, lo que hace la diferencia es el
modelo; si ambas separan, son las razones β; si ninguna, H3 cae en las dos formas.

## Lo que no se hace

No se cambia `detect_ash_enhanced` ni ningún código de la app. Sin VIIRS. Si el modelo radiativo
exige cuenta, registro o licencia, se detiene y se pregunta.
