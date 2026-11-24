# S21a1: ventana partida a 100 m con el control escrito antes. Informe, 24-11-2026

Criterio: `criterio_2026-11-24.md`, versión 1 (regla de selección, commit `d91f2eb`, 24-11 00:21 hora de Chile) y
versión 2 (control, veredictos y ensayo en seco, commit `d7fe440`, 00:33), las dos empujadas antes de medir. Medida:
`scripts/s21a1_medir.py medir` corrida después del push del criterio (resultado escrito a las 00:37), salidas `resultados/s21a1_resultado.json` y `s21a1_medir.log`,
figura `figuras/s21a1_btd.png`. Selección: `scripts/s21a1_seleccion.py`, `resultados/seleccion.json`. Ensayo en seco:
`resultados/s21a1_seco.json`. Datos: `D:\goes_notas\s20b\` (máscara y HLS del 25-10 y 17-10) y
`D:\goes_notas\s21\a1\` (Fmask de las candidatas, HLS del 15-09, reflectancia nueva).

- **Ninguna pasada de Landsat distinta del 25-10 sirvió** por la regla escrita (nube sobre la cumbre en cinco, sin pluma
  sobre la nieve el 15-09, nube dentro de la máscara el 17-10). La prueba se repitió sobre el 25-10 y es
  **CONFIRMATORIA de lo ya visto, no independiente.**
- **Veredicto por la regla: FIRMA DE CENIZA.** T1 = −3,33 K (p_bajo 0,0035), T2 = **−1,54 K** con p_bajo 0 de 1.985
  corrimientos (nulo de −0,24 a +0,23 K). El mismo lugar sin pluma: 17-10 T2 = +0,23 K (p_bajo 0,87), 15-09 T2 =
  +0,04 K (p_bajo 0,64). El control de sitio no baja el veredicto.
- **Lectura:** la conclusión post hoc de S20d (la pluma del 25-10 tiene ventana partida negativa a 100 m) no dependía
  del sector elegido mirando la figura. Sigue siendo una sola pluma, y la firma se mide en la parte menos fría de la
  máscara (107 de 283 celdas tienen par).

## 1. El fenómeno, para geólogo

La mañana del 25-10 la pluma de Chillán salía hacia el oeste-suroeste como una franja translúcida sobre la nieve.
Desde arriba se ve de dos maneras. En reflectancia, la ceniza ensucia la nieve en 1,6 µm, pero sólo donde la capa es lo
bastante densa: la máscara de reflectancia marca 1,6 km². En el térmico, la pluma enfría la nieve unos 3 K en 10,9 µm
y, sobre todo, baja la diferencia 10,9 menos 12,0 µm a −2 a −3 K en una mancha unas tres veces más grande que la
máscara (S20d §3 d). Esa diferencia negativa es la huella de los silicatos: absorben más a 11 µm que a 12 µm. Una nube
de agua o de hielo común hace lo contrario.

Para medir esa diferencia hay que compararla con nieve de la misma temperatura y altura, porque la diferencia de la
nieve sola cambia con su temperatura y con el vapor sobre ella. La trampa de S20d fue que la nieve más fría a esa
altura estaba, justamente, bajo la parte de la pluma que la reflectancia no marcó: el núcleo de la pluma se comparó
con su propia cola. Esta prueba saca del control, con una regla geométrica fijada antes, un sector de ±45° alrededor
de la dirección de la pluma (252,5°, desde el centroide de la máscara de reflectancia), de 2 a 15 km del cráter.

En la figura (`figuras/s21a1_btd.png`), la mancha roja del 25-10 al oeste-suroeste del cráter queda dentro del sector
(trazos); el 17-10, sin pluma, ese lugar no tiene nada parecido.

## 2. Elección de la pasada (criterio §1, aplicado sólo con reflectancia y Fmask)

Sólo el path 233 contiene el cráter. De las ocho pasadas candidatas entre el 15-09 y el 18-11:

| Pasada | Por qué no |
|---|---|
| 15-09, L9 | despejada, pero la regla de reflectancia no encuentra pluma: 800 celdas sueltas, ninguna tras erosionar, la más cercana a 8,1 km |
| 23-09, L8 | 100 % de nube en el catálogo, sin gránulo HLS |
| 01-10, 09-10, 02-11, 10-11, 18-11 | Fmask marca nube o sombra en 55 a 100 % del disco de 2 a 15 km (o en la cumbre) |
| 17-10, L9 | despejada en la cumbre, pero su máscara (5,45 km², repartida en todas direcciones) está 38 % marcada nube por Fmask |

La del 26-11 aún no existe. El respaldo previsto en §1 fue repetir el 25-10 con el control nuevo, rotulado
confirmatorio.

## 3. Resultado por la regla (criterio §3 a §5)

| | 25-10 (decide) | 17-10, mismo lugar sin pluma (control de sitio) | 15-09, sin pluma (informativo) |
|---|---|---|---|
| T1 (p_bajo; nulo p5 a p95) | **−3,33 K** (0,0035; −1,32 a +2,09) | −0,36 K (0,26) | −0,13 K (0,37) |
| T2 (p_bajo; nulo p5 a p95) | **−1,54 K** (0 de 1.985; −0,24 a +0,23) | +0,23 K (0,87; −0,23 a +0,33) | +0,04 K (0,64; −0,15 a +0,14) |
| Celdas con par en T2 | 107 de 283 | 283 de 283 | 283 de 283 |
| BTD cruda, máscara / control (medianas) | −1,94 / −0,35 K | +0,05 / −0,10 K | −0,02 / −0,05 K |
| ε11 desde T1; BTD de ceniza esperada | 0,38; −0,84 K (T_tope GFS 265,45 K a 4.267 m) | | |
| Fmask en la máscara | 100 % nieve, 0 % nube | | |
| Veredicto | **FIRMA DE CENIZA** | sin firma propia (no baja el veredicto) | SIN CONTRASTE |

- D = 25-10 menos 17-10, en la máscara y en 1.981 corrimientos comunes: D(T1) = −2,97 K (p_bajo 0), D(T2) = −1,77 K
  (p_bajo 0; nulo −0,48 a +0,36 K). Contra el 15-09: D(T2) = −1,58 K (p_bajo 0).
- Informativo, erosión 2 (535 celdas): T1 −3,23 K, T2 −1,52 K (p_bajo 0 de 1.762), FIRMA DE CENIZA.
- Informativo, sector cortado a 12 km: idéntico al de 15 km (T2 −1,54 K, mismas 107 celdas).
- El ensayo en seco comprobó antes de medir que, con el sector vacío, el código da exactamente lo de S20d, y que el
  control de sitio con el sector no tiene firma propia (§6 del criterio).

Lo esperado (criterio §7): FIRMA DE CENIZA con T2 cerca de −1,5 K y T1 cerca de −3,3 K. Se cumplió.

## 4. Qué significa

1. **La firma de ceniza de la pluma del 25-10 a 100 m queda confirmada por una regla escrita antes**, no sólo por el
   sector elegido a ojo. El valor es el mismo del post hoc (−1,54 K) y no se mueve con el borde del sector (12 o
   15 km), ni con la erosión (−1,52 K). La BTD de ceniza que predecía el modelo simple de capa con β = 0,7 era −0,84 K;
   la medida casi la duplica, como en S20d.
2. **El veredicto formal de S20d (SIN FIRMA) se explica por el control, no por la pluma.** Con el control de S20d y la
   misma máscara, T2 era −0,09 K; sacando el camino de la pluma por regla, −1,54 K.
3. **No es una segunda observación.** Es el mismo caso, el mismo térmico y la misma BTD que S20d ya miró; lo único
   nuevo es que el control quedó fijado antes. La generalización ("la ceniza de Chillán da ventana partida negativa
   cuando el píxel la resuelve") sigue apoyada en una pluma.

## 5. Post hoc (después de ver el resultado; no cambia el veredicto)

- **Corrección al informe de S20d.** Su §3 (c) dice que con el sector fuera la regla "habría dado FIRMA DE CENIZA".
  Por el código no: en ese control post hoc el anillo de T1 quedaba dentro del sector y `s20d_posthoc.json` da
  `T1_K: null`, con lo que la regla habría dado NO CONCLUYENTE (sin T1). Esto se vio al escribir el criterio, antes de
  medir, y la prueba de hoy lo resolvió manteniendo el anillo de T1 de S20d (criterio §3, punto 3).
- **En la figura,** el lado oeste de la escena del 25-10 tiene una BTD algo negativa también fuera del sector, al
  noroeste (hasta unos 10 km al O y 8 km al N del cráter). Puede ser pluma más ancha que ±45° o el residuo de luz
  parásita de la banda 11 de Landsat 8, que crece hacia un borde. Si es pluma dentro del control, empuja T2 hacia
  cero, no hacia la firma.

## 6. Lo que puede estar mal

- **La firma se mide en la parte menos fría de la máscara, no en su núcleo.** 176 de las 283 celdas no tienen 20 pares fuera del sector: a
  su temperatura y cota no hay nieve fuera del camino de la pluma (en S20d §3 a, el pareo se perdía en las capas con
  BT10 bajo unos 271,5 K, las más frías del núcleo). T2 sale de las 107 restantes. Una superficie que fuera más fría y con BTD baja sólo en el sector daría lo
  mismo; el control de sitio (17-10 y 15-09, sin pluma, +0,23 y +0,04 K en el mismo lugar) es lo que lo descarta.
- **Una pluma, una mañana.** 283 celdas de 30 m son unas 25 celdas independientes del TIRS de 100 m, y la medida usa
  107. La señal es grande frente al nulo (−1,54 contra ±0,24 K), pero es un caso. Ninguna otra pasada de Landsat entre
  el 15-09 y el 18-11 tuvo pluma sobre nieve con cumbre despejada.
- **El ensayo en seco no reproduce la trampa de S20d** (criterio §6.3): con nieve sintética de todas las temperaturas
  en todo el disco, el control viejo y el nuevo dan lo mismo. Que el control nuevo corrija la trampa lo muestra el
  dato real, no el sintético.
- **Hielo muy fino** puede dar 11 − 12 µm levemente negativa; con dos bandas no se separa del todo (S20d §6). −1,5 K
  es más de lo que se suele atribuir a hielo, pero no lo descarto con este dato.
- **Banda 11 de Landsat 8:** residuo de luz parásita de gran escala; se mide en pares dentro de 15 km, y los dos días
  de referencia son de Landsat 9, otro sensor, que no muestran nada en el lugar.

## 7. Siguiente paso

Una prueba independiente necesita otra pasada con pluma sobre nieve y cumbre despejada (próximas de Landsat por el
path 233: 26-11 con L8 y luego cada 8 días alternando L9 y L8), con esta misma regla y este mismo código sin tocar.
Con la nieve en retirada desde noviembre, la máscara de reflectancia verá cada vez menos pluma.
