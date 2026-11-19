# Informe H7: ¿VOLCAT sigue la nube de Chillán desde un cuadro con señal propia? (19-11-2026)

## 1. El fenómeno y la pregunta

VOLCAT (SSEC/CIMSS) dibuja plumas de Nevados de Chillán en cuadros donde nuestro infrarrojo no ve nada:
la diferencia split-window (BT 11,2 µm menos BT 12,3 µm) sigue positiva y el canal de 11,2 µm no muestra una
nube fría. El ATBD VOLCAT v1.0 (Pavolonis et al., enero 2025, §2.2) describe un seguidor que lleva un objeto
de un cuadro al siguiente "from emission to dissipation", un detector por crecimiento de nube y umbrales que
dependen del calor en el cráter. De ahí sale H7: los cuadros sin señal IR no serían detecciones nuevas, sino
la continuación de un objeto que VOLCAT detectó antes, en un cuadro que sí tenía señal propia (ceniza
split-window, calor en el cráter o una columna que se enfría porque sube).

Si H7 fuera cierta, nuestro detector no tendría que "ver" cada cuadro: bastaría con encontrar el primero y
seguirlo. Para eso, el primer cuadro de cada tramo tiene que tener alguna señal que nosotros también podamos
medir.

## 2. Qué se midió y cómo

El criterio se escribió antes de medir:
`C:\Users\nmend\AppData\Local\Claude-Data\claude_pzs8sxrjxfjjc\side-session-notes\local_f3a7d295-ddde-4b7c-b258-25e760c44266\criterio_H7_seguimiento_2026-11-19.md`.

- **Objetos VOLCAT.** Se decodificaron todos los PNG Ash_Height del sector Chile_Central_2_km de 28-10,
  29-10, 10-11 y 14-11 (556 cuadros) con el método de las pruebas anteriores: píxel con ceniza según la barra
  de colores (`src.process.volcat_colorbar`), objetos de 8 vecinos, fuera ruido (≤ 3 px) y manto (> 5 % del
  mapa), distancia al cráter por haversine. Cuadro con objeto: objeto a ≤ 50 km. Anclado: un píxel a ≤ 10 km.
  Ningún cuadro de esos días tuvo manto ni objetos de más de 500 px cerca.
- **Tramos.** Un cuadro anclado es "primero de tramo" si el cuadro anterior publicado (10 min, o 20 min si
  SSEC no publicó el de 10) no tiene objeto a ≤ 50 km. Si lo tiene, es continuación (tiene antecesor).
- **Señal propia**, con datos del mismo scan ABI de GOES-19:
  - (a) ceniza split-window: algún píxel de la huella VOLCAT (dilatada 1 px) con BTD < −1 K;
  - (b) calor: hot spot FDCF a ≤ 10 km del cráter en ese scan o en los dos anteriores;
  - (c) crecimiento: al menos 2 píxeles a ≤ 10 km con BT 11,2 µm 2 K o más fría que 10 min antes.
  Las temperaturas de brillo salen de la radiancia L1b con los coeficientes Planck de cada NetCDF. Los hot
  spots salen de las funciones del repo (`src/fetch/goes_fdcf.py`: `nearest_granule_key`, `_abrir_granulo`,
  `extract_hotspots`, Mask 10-15).
- **Línea base.** La misma señal en los scans del mismo día sin objeto VOLCAT a ≤ 50 km.

## 3. Resultado

**H7 se falsa.** En los tres episodios, el primer cuadro del primer tramo no tiene ninguna señal propia.
Lo que sí se ve es que VOLCAT mantiene los objetos de un cuadro al siguiente (la mayoría de los cuadros sin
señal tienen antecesor), pero la semilla de cada cadena tampoco tiene señal en nuestros datos. El seguimiento,
entonces, no explica por qué VOLCAT ve lo que nosotros no: el problema está ya en el primer cuadro.

| Episodio | Primer cuadro del primer tramo | Señal propia | Cuadros anclados | Sin señal | Sin señal con antecesor |
|---|---|---|---|---|---|
| E1 (28-10 21:50 a 29-10 01:40) | 28-10 19:20 UTC | no | 15 | 9 | 9 |
| E2 (10-11) | 10-11 15:00 UTC | no | 12 | 5 | 2 |
| E3 (14-11, 16:40 a 22:40) | 14-11 16:40 UTC | no | 33 | 9 | 8 |
| Total | 0 de 3 con señal | | 60 | 23 | 19 (82,6 %) |

Regla que decide: "H7 se falsa si en al menos 2 de los 3 episodios el primer cuadro del primer tramo NO tiene
señal". Se cumple en 3 de 3. La otra cláusula de falsación (más del 30 % de los cuadros sin señal son
primeros de tramo) no se cumple: son 4 de 23 (17,4 %). Hay 23 cuadros sin señal, por sobre el mínimo de 5.

Detalle por señal:

- **(a) split-window:** ningún cuadro anclado de los 60 llega a BTD < −1 K en su huella; el mínimo fue
  −0,73 K (28-10 22:50). Tampoco con la huella ampliada a todos los objetos a ≤ 50 km.
- **(b) hot spot FDCF:** ningún hot spot a ≤ 10 km en ningún cuadro anclado ni en sus dos scans previos.
  Línea base: 0 % en los tres episodios (E1 0 de 240 scans sin objeto, E2 0 de 127, E3 0 de 98), así que la
  señal entra al veredicto, pero no se encendió nunca. Con las detecciones de filtro temporal (Mask 30-35)
  tampoco aparece nada a ≤ 10 km en los cuadros anclados.
- **(c) crecimiento:** se enciende en 6 de 15 cuadros anclados de E1, 7 de 12 de E2 y 24 de 33 de E3,
  pero nunca en un primer cuadro del primer tramo. Ojo con su línea base: aparece también en el 19,3 % (E1),
  34,3 % (E2) y 61,0 % (E3) de los scans sin objeto. Es una señal poco discriminante (nubes que pasan sobre
  el cráter, enfriamiento del suelo al atardecer). Sin ella, los 60 cuadros quedarían sin señal y el veredicto
  sería el mismo.

Los tramos encontrados:

- E1: un solo tramo en la ventana, 28-10 21:50 a 29-10 01:20 (15 anclados), que en realidad empieza a las
  19:20 del 28-10. Antes hubo dos tramos de un cuadro (18:30 y 19:00), también sin señal.
- E2: 15:00 a 15:10 (2), 21:30 a 23:00 (9) y 23:20 (1). Los tres primeros cuadros, sin señal.
- E3: 16:40 a 21:20 (26) y 21:40 a 22:40 (7). El primero del segundo tramo (21:40) sí tiene (c), con 13 px.

## 4. Desviaciones del criterio

1. **E1 empieza antes de su ventana.** El criterio pone E1 desde 21:50, pero SSEC no publicó el cuadro de
   21:40 y el de 21:30 tiene objeto anclado: 21:50 es continuación. La cadena sin cortes llega hasta las 19:20
   (19:10 está publicado y sin objeto), y ese es el cuadro que usé como primero. Los totales cuentan sólo los
   15 cuadros anclados de la ventana. Con 18:30, 19:00 o 21:50 como primer cuadro el resultado es el mismo:
   ninguno tiene señal.
2. **"Anclado" sale de mi decodificación con haversine**, no de la columna `toca_crater_10km` del CSV.
   Coinciden salvo 14-11 21:00 (8,8 km por haversine; el CSV calcula 9,5 km con distancia de grilla isótropa).
   Es continuación y tiene (c): no cambia los conteos sin señal.
3. **Huella de (a):** objetos anclados enteros llevados a la grilla ABI con dos mapeos de vecino más cercano
   (ABI hacia VOLCAT, como `huellas.py`, y VOLCAT hacia ABI, para no perder objetos chicos).
4. **Línea base de (a):** como un scan sin objeto no tiene huella, cada huella anclada del episodio se
   trasplantó a cada scan sin objeto (0 de 1275, 0 de 864 y 0 de 1419 pares con BTD < −1 K).
5. **Horas de la línea base:** (a) y (c) sólo en las horas con L1b en caché (28-10 14:00 a 23:50; 29-10
   00:00 a 01:40 y 14:00 a 23:50; 10-11 y 14-11 08:00 a 12:30 y 14:00 a 23:50). (b) cubre los días completos.
   En E1, "mismo día" es 28-10 y 29-10 juntos.
6. **Hot spots:** conjunto por defecto del repo (Mask 10-15). Mask 30-35 va como sensibilidad.
7. **BT11 de (c)** es la banda de 11,2 µm (C14; en la caché se llama `b14`, porque `b11` es la de 8,4 µm).
8. **β no entra**, como dice el criterio.

## 5. Archivos

- Resultado cuadro por cuadro:
  `C:\Users\nmend\AppData\Local\Claude-Data\claude_pzs8sxrjxfjjc\side-session-notes\local_f3a7d295-ddde-4b7c-b258-25e760c44266\h7_resultado.txt`
- Scripts finales (copias):
  `C:\Users\nmend\AppData\Local\Claude-Data\claude_pzs8sxrjxfjjc\side-session-notes\local_f3a7d295-ddde-4b7c-b258-25e760c44266\h7_volcat_obj.py`,
  `C:\Users\nmend\AppData\Local\Claude-Data\claude_pzs8sxrjxfjjc\side-session-notes\local_f3a7d295-ddde-4b7c-b258-25e760c44266\h7_fetch_fdcf.py`,
  `C:\Users\nmend\AppData\Local\Claude-Data\claude_pzs8sxrjxfjjc\side-session-notes\local_f3a7d295-ddde-4b7c-b258-25e760c44266\h7_fetch_l1b.py`,
  `C:\Users\nmend\AppData\Local\Claude-Data\claude_pzs8sxrjxfjjc\side-session-notes\local_f3a7d295-ddde-4b7c-b258-25e760c44266\h7_analisis.py`
- Carpeta de trabajo (originales, objetos VOLCAT, huellas, FDCF por scan, L1b nuevo):
  `C:\Users\nmend\AppData\Local\Temp\claude\caac88451b34493f\bd33fd70-a478-403d-be84-fcf2fda5792e\scratchpad\h7\`
  (`objetos.json`, `huellas_h7.npz`, `fdcf.jsonl` con 582 scans sin fallas, `cache\20261029_0000.npz` a
  `cache\20261029_0140.npz`).

No se tocó código de la app ni se hizo commit. Sin VIIRS.
