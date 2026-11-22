# Sitio de VOLCAT: la probabilidad de ceniza que el propio VOLCAT publica en Chillán (S16, tarea 4a)

Criterio: `criterio_2026-11-22.md` (commit `8f9190e`, antes de medir). Script: `scripts/prob_sitio.py`.
Resultados: `resultados/resumen.json` y `resultados/por_cuadro.csv`. Insumos fuera del repo: PNG en
`D:\goes_notas\s16\sitio\png\` (60 cuadros públicos del sitio) y NetCDF de evento en
`D:\goes_notas\busqueda_2026-11-20\volcat_eventos_357070\` (licencia restringida).

## Veredicto: BAJA (en la posición nominal y en la desfasada)

VOLCAT pinta en su imagen de probabilidad justo los píxeles de su propia detección de Chillán, pero con
probabilidad baja. De día pleno no publica en ningún cuadro una probabilidad de 20 % o más en la huella.

| | nominal | desfasada (1 fila S, 1 col E) |
|---|---|---|
| Cuadros con huella ≥ 5 px y color en la imagen | 41 | 41 |
| Cuadros con P ≥ 20 % en ≤ 10 % de la huella (regla BAJA) | 40 | 36 |
| Cuadros que cumplen la regla ALTA | 0 | 0 |
| Mediana de la huella con color decodificado | 0,22 | 0,47 |
| Lo mismo en el control pareado por BT11 | 0,00 | 0,00 |
| Máximo de la huella con P ≥ 50 % | 0,11 | 0,23 |

## Lo que se ve, como fenómeno

1. **El color marca la detección, el valor es bajo.** Contando también los píxeles de borde mezclados con el
   gris, la mediana de la huella con color es 0,91 de día y 0,96 al atardecer. El control pareado por BT11
   tiene 0,00 en todos los cuadros: la imagen no colorea el resto de la escena con la misma temperatura. Pero
   los bloques que aparecen en la huella son B0 a B5, de 0,001 % a menos de 20 %, casi siempre el extremo
   bajo de la escala logarítmica.
2. **De día pleno no hay probabilidad alta ni cerca del cráter.** En 27 cuadros con el sol a menos de 65° del
   cenit (14-11 13:00 a 21:10), el bloque más alto dentro de 50 km del cráter llega a B10 o más en uno solo
   (19:10, B11). El valor máximo no queda escondido en los píxeles mezclados: un píxel puro de 50 % o más se
   habría decodificado.
3. **Al atardecer aparece probabilidad alta.** En 14 cuadros con el sol entre 65° y 93° del cenit
   (14-11 21:20 a 23:40), 9 tienen píxeles de 90 a 100 % (B14) dentro de 50 km del cráter. Ocupan hasta un
   23 % de la huella (22:40 y 22:50), siempre menos que la regla ALTA. Una sola noche, sin repetición.
4. **13-11 (VCB, 1 px) y dos cuadros del 14-11 temprano no tienen ningún píxel de color en toda la imagen.**
   Son SIN DATO, no "baja": la huella de 1 px no se dibujó.

## Qué significa para la pregunta de S15

- La hipótesis "el hueco está en las tablas de día" queda **muy debilitada**: el propio VOLCAT, con sus
  tablas y su cielo despejado, publica de día una probabilidad por píxel de 0,001 a 10 % en Chillán. Nuestras
  reproducciones IR (etapa 3: P ≥ 0,5 en ≤ 2,1 % de la huella) ya daban lo mismo.
- Se **refuerza la vía `ASHPLUMEPUFF`**: VOLCAT publica el evento aunque la probabilidad por píxel sea baja.
  El objeto entra por otro camino (seguimiento en el tiempo, calor en el cráter, umbrales relajados), que es
  lo que hay que preguntarle a Pavolonis.
- **Advertencia:** no sabemos qué etapa del cálculo pinta la imagen `Ash_Probability` (probabilidad de píxel
  final, después del paso de objeto, o ya mezclada con otra máscara). Que sólo se coloree la huella sugiere
  que la imagen está recortada por la detección. No está documentado en el sitio; va en el correo.
- Sirve a la tarea 4b (S16b) como caso de DÍA sobre TIERRA para validar por bloque la lectura de las tablas
  DAY: deberían dar P baja en la huella de día y alta en parte de la huella al atardecer.

## Las dos preguntas del instrumento, contestadas con los datos

- **Régimen:** el mismo por construcción (salida de VOLCAT v3r4 sobre los mismos cuadros).
- **Barra:** los 15 bloques son idénticos en los 60 PNG (diferencia máxima 0,0) y van en orden de amarillo a
  rojo muy oscuro.
- **Georreferencia: no cumple el umbral pre-registrado.** El centro del triángulo del volcán (capa
  `VOLCANOES.CYAN`, componente conexa más cercana, 27 px) queda a 3,07 px (unos 6 km) de la posición
  calculada del cráter; el criterio pedía 2 px o menos. Una primera versión del control tomaba también las
  letras del nombre y daba 16 px; se corrigió para usar sólo el triángulo. El triángulo puede estar anclado en
  un vértice y no en su centro, cosa que no se comprobó. Con el desfase medido en H14 el
  veredicto es el mismo.
- **Control positivo:** sí. Hay 10 cuadros con bloques de 50 % o más decodificados dentro de 50 km del
  cráter, así que el decodificador lee valores altos cuando los hay.
- **¿Un instrumento muerto se vería distinto?** Sí. Los 12 cuadros sin ningún píxel de color se cuentan
  aparte como SIN DATO, y el control da 0,00 mientras la huella da 0,91. Un PNG en blanco no daría eso.

## Otras partes del sitio (tarea 4a, resto)

- **Alertas (`/alert/`):** piden usuario registrado (redirige a `/auth/login`). No se creó cuenta.
- **Panel térmico (`/thermal/`):** es un Grafana público por volcán (Chillán figura como
  "Chillan, Nevados de"). Guarda VRP total, z-score, marcas de evento (salto de VRP, SO₂, ceniza, VCB), máximo
  de BT a 3,9 µm, fondo a 11 µm y ángulos. La consulta programática a su API fue bloqueada por permisos; con
  el sí de Nicolás se miró en el navegador el 22-11, sin bajar archivos. Leído en pantalla:
  - **VRP de GOES-Este, 20-10 a 22-11:** entre ~1 y ~30 MW casi sin cortes, de día y de noche; los puntos LEO
    van de ~10 a ~200 MW. VOLCAT tiene calor en el cráter de forma continua en todo el periodo.
  - **Marcas de ceniza ("Ash Event"):** en muchos días, no sólo en los tres de los NetCDF bajados: 25, 26, 28,
    29 y 30-10; 6, 7, 8, 10, 12, 13, 14, 15 y 18-11 (lectura del gráfico, días aproximados).
  - **13 y 14-11, horas leídas en la ayuda emergente:** 13-11 06:17:31 ceniza con salto de VRP = 1 (no está en
    los 60 NetCDF, que en el 13-11 empiezan a las 19:00); 13-11 19:21:17 ceniza y VCB con salto de VRP = 1;
    14-11 12:48:36 ceniza con salto de VRP = 0. Dos de tres marcas de ceniza coinciden con un salto de VRP.
  - **Salto de VRP ("VRP Jump Event")** aparece casi a diario en el periodo, así que no basta como gatillo por
    sí solo.
  - **CSV del VRP de GOES-Este** (bajado del inspector del panel con el sí de Nicolás, copia en
    `D:\goes_notas\s16\sitio\grafana\chillan_vrp_goeseste_2026-10-20_11-22.csv`, no va al repo): 4.320 valores
    cada 10 min del 19-10 23:58 al 22-11 06:28 UTC, de día y de noche. Mediana 8,3 MW, p10 1,0, p90 25,4,
    máximo 187 MW; **43 % de los cuadros con 10 MW o más**. Es del mismo orden que el 48 % de cuadros
    nocturnos con 10 MW o más que dio nuestra potencia propia en H17, lo que no calza con que H17 recuperara 0
    de 3 cuadros de 10 MW de VOLCAT: esas tres marcas venían de `volcano_thermal_activity` del NetCDF de
    evento, que puede no ser la misma serie. Queda por revisar con el CSV de eventos.
  - **CSV de eventos** (`D:\goes_notas\s16\sitio\grafana\chillan_eventos_2026-10-20_11-22.csv`, 4.560 filas):
    **30 marcas de ceniza** del 24-10 17:38 al 18-11 10:18 UTC, 2 de VCB (22-10 y 13-11), 0 de SO₂ y 220
    saltos de VRP (4,8 % de los cuadros). Por fecha: 24-10 (2), 25-10 (4), 27-10 (3), 28-10 (3), 29-10 (2), 30-10, 06-11, 07-11 (2), 08-11 (2),
    10-11 (4), 12-11 (2), 13-11 (2), 14-11 12:48 y 18-11 10:18. Los 60 NetCDF de evento cubren sólo 4 de estas
    30 marcas (13-11 19:21, 14-11 12:48, 18-11 10:18 y el VCB): el resto ya salió de la ventana de ~7 días.
  - **Ceniza y calor:** 20 de 30 marcas de ceniza (67 %) tienen un salto de VRP a 1 h o menos. Los saltos se
    juntan al amanecer y al atardecer (picos a las 05 y 18 UTC), igual que las marcas de ceniza (13 de 30 entre
    las 17 y las 19 UTC), así que el azar se midió sorteando horas con la misma hora del día: 51 % en promedio,
    p = 0,03 (2.000 sorteos). Asociación moderada, no un gatillo: un tercio de las marcas no tiene salto, y
    el pico de saltos al terminador solar puede ser en parte un efecto del cambio día-noche en el algoritmo
    térmico, no del volcán.
  - El CSV de temperaturas de brillo no se bajó (secundario).
- **Altura, carga y radio:** las imágenes `Ash_Height`, `Ash_Loading` y `Ash_Reff` existen para los mismos
  cuadros (lista del sitio, desde el 22-10). Los NetCDF de evento ya traen sus percentiles, así que no se
  bajaron.
