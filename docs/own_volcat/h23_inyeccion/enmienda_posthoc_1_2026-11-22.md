# Enmienda post hoc 1 al criterio H23 (22-11-2026)

**Rótulo: POST HOC.** Esta enmienda se escribió después de ver datos, y cambia el criterio
`criterio_2026-11-22.md` (commit b77a83c). Se commitea **antes** de calcular un solo número de detección.

## 1. Qué pasó

La primera corrida de `scripts/h23_medir.py` cortó en la comprobación de instrumento I5, como manda el criterio, y
no calculó ninguna inyección ni ningún AUC. Salida guardada en `resultados/h23_instrumento_corrida1_falla_I5.json`:

- I4 pasó: correlación entre BT11_ref de las 06 UTC y la cota −0,975; cumbre 8,2 K más fría que el terreno bajo.
- I6 pasó: BTD_ref mediana 1,10 K.
- **I5 falló:** en el terreno bajo, BT11_ref subía 3,9 K entre las 09 y las 18 UTC. El criterio pedía 8 K o más.

## 2. Qué se miró para entenderlo (sólo datos de instrumento)

Nada de lo que sigue usa inyección, detectores ni AUC.

1. **El instrumento está vivo.** En el día más tibio del bloque (17-10) la BT11 cruda del terreno bajo sube de
   277,4 K a las 09 UTC a 289,3 K a las 18 UTC: 11,9 K (`resultados/h23_diag_i5_corrida1.json`).
2. **La que estaba mal era la línea base.** Su mínimo en el terreno bajo caía a las 20:00 UTC (17 h de Chile) con
   270,7 K, más frío que antes del amanecer (275,0 K a las 09 UTC). Un suelo despejado no puede estar más frío a
   media tarde que al final de la noche: ese valor es nube.
3. **Por qué.** El periodo fue muy nublado, sobre todo de tarde. De los 23 días de prueba, los que están a 8 K o
   menos del día más tibio a cada hora son, en el terreno bajo: 8 a las 03 y a las 09 UTC, 5 a las 15, 4 a las
   18, 2 a las 20 y 1 a las 22 UTC. El percentil 90 de 30 muestras necesita al menos 3 muestras despejadas; con
   una o dos tardes despejadas en diez días, cae en nube.
4. **Agrandar la ventana no basta.** Se probó la referencia con todos los otros días del bloque (percentil 90 de
   hasta 96 muestras): I5 dio 7,86 K y el mínimo siguió a las 20:00 UTC, con 276,3 K
   (`resultados/h23_diag_i5_intento_p90_bloque.json`). No se adopta.
5. **La máscara de nubes de NOAA** (producto ABI-L2-ACMF de GOES-19, misma grilla de 2 km) se comprobó contra la
   BT11 cruda en 10 días (`resultados/h23_diag_acm.json`, `scripts/h23_diag_acm.py`):
   - En el **terreno bajo** funciona: los días despejados 15 y 16-10 da despejado el 87 a 100 % del grupo a las
     03, 09, 13 y 16 UTC, y 0 a 4 % cuando la BT11 cae a 238 a 256 K.
   - En la **cumbre no sirve**: en los cuatro días más despejados (15 al 18-10) marca nublados los 6 píxeles de
     cumbre casi siempre (a lo más 1 de 6 despejado), incluso con BT11 de 265 a 275 K y el terreno bajo despejado. Confunde
     la nieve con nube. Hallazgo aparte, anotado para seguimiento.

**Consecuencia si no se corregía.** La población B del criterio ("entorno despejado") se definía contra esa misma
línea base. Con una referencia que es nube, B habría dejado pasar escenas nubladas como despejadas, el fondo
habría quedado más ancho y la prueba se habría sesgado hacia "no se puede ver". La enmienda va en el sentido que
favorece a la falsación.

## 3. Qué cambia

**E1. Escena despejada, con un producto externo.** Para cada volcán y cuadro, la escena es *despejada* si al
menos 80 % de los píxeles del **terreno bajo de ese volcán** (la regla del criterio §3: 10 a 30 km de la cumbre,
cota media bajo 1.300 m) tienen la máscara de NOAA en "despejado" o "probablemente despejado" (ACM 0 o 1). Un
píxel sin dato cuenta como no despejado. Se usa el terreno bajo porque ahí la máscara se comprobó; la cumbre no
entra.

**E2. Línea base.** Para cada píxel y cuadro: mediana de la BT11 de ese píxel a la misma hora (cuadro anterior,
mismo y siguiente) en los **otros días del bloque en que la escena estaba despejada** (E1). Pide muestras de al
menos 3 días distintos. `BTD_ref` es la mediana de BT11 − BT12 en esas mismas muestras. No entra el mismo día ni
el 22-10. La referencia deja de ser causal (usa días posteriores): para una cota retrospectiva es el caso
favorable; un detector operando tendría que juntar historia.

**E3. Poblaciones.** A, todo cielo: toda muestra con referencia. **B, entorno despejado (decide): escena
despejada según E1 en ese cuadro.** C, oráculo: B y además el propio píxel con D1 ≥ −5 K antes de inyectar. La
condición anterior de B (80 % del anillo con D1 ≥ −5 K) se retira, porque dependía de la referencia defectuosa.

**E4. Días de prueba.** Como la referencia ya no reserva los primeros 10 días, son de prueba todos los días de
cada bloque: 21-09 al 23-10 (sin el 22-10 en Chillán) y 01-11 al 21-11 (sólo cumbres de control y eventos). Más
días despejados, menos celdas SIN DATO. Para Chillán, del 21-09 al 19-10 VOLCAT sigue SIN DATO (el panel parte
el 20-10).

**E5. Comprobaciones de instrumento.** I4, I5 e I6 quedan con los mismos umbrales y se calculan sobre la
referencia nueva, en los píxeles que la tienen (objetivos y sus entornos, no toda la ventana). I5 pasa a decir lo
que de verdad comprobó: que la **referencia** tiene ciclo diurno de cielo despejado. Si vuelve a fallar, no hay
veredicto.

## 4. Qué no cambia

Los cinco detectores y sus fórmulas, la física y la grilla de la inyección, los grupos de píxeles, los tramos
horarios, las métricas, el mínimo de 500 muestras y 8 días por celda, la regla de decisión y los controles
positivo y nulo. Las secundarias S1 a S5 quedan igual, con los días de E4.

## 5. Riesgos de la enmienda (para leer el resultado)

- **Pocas tardes despejadas.** Con una escena despejada bien definida, el tramo 18 a 24 UTC puede no juntar 8
  días y quedar SIN DATO. Eso sería un límite real de la muestra de primavera, no una falla.
- **La máscara de NOAA no es perfecta.** Puede dejar pasar cirros tenues o niebla baja de noche. Lo que deje
  pasar ensancha el fondo y juega contra la detección.
- **El propio píxel de cumbre puede tener nube** (gorro orográfico) con el terreno bajo despejado. En B eso queda
  dentro del fondo, a propósito: en operación no se sabe. La población C lo quita, como oráculo.
- **Referencia de pocos días.** Con 3 a 10 días despejados, la mediana arrastra la diferencia de masa de aire
  entre esos días y el de prueba. Eso es ruido real de cualquier línea base temporal y queda dentro de D1. D4
  (doble diferencia con el entorno) y D2 (BTD) lo cancelan en parte.
- **Más grados de libertad míos.** Elegí la definición de escena despejada después de ver BT11 y máscara de 10
  días. No vi ningún resultado de detección al elegirla.
