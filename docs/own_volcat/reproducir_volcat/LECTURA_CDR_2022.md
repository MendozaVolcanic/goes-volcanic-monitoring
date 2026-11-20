# Lectura de la presentación CDR de VOLCAT (Pavolonis, 12-07-2022)

Fuente: `C:\Users\nmend\AppData\Local\Claude-Data\claude_pzs8sxrjxfjjc\side-session-notes\local_1055cba6-2c2f-4aa4-9119-82691ee2ed22\pdfs\Pavolonis_2022_VOLCAT_CDR.pptx`
(177 MB, 105 diapositivas; original público en `https://bin.ssec.wisc.edu/pub/volcat/VOLCAT_CDR_ATB_July2022.pptx`).
Leída el 19-11-2026 entera: texto de cada forma, tablas y notas del orador, extraídos con python-pptx
(19.000 palabras aprox.); las figuras de las diapositivas 79, 80, 82, 83, 99, 100 y 101 se miraron como imagen.
La mayor parte de la presentación es sobre usuarios, requisitos OACI y operación; la ciencia está en las
diapositivas 64 a 84 y 98 a 104. Copia de esta nota en la carpeta de notas de la sesión
(`C:\Users\nmend\AppData\Local\Claude-Data\claude_pzs8sxrjxfjjc\side-session-notes\local_f3a7d295-ddde-4b7c-b258-25e760c44266\LECTURA_CDR_2022.md`).

## 1. Lo que se pidió buscar

| Tema | Qué dice la CDR | Diapositiva |
|---|---|---|
| Umbrales que se aflojan con calor | "When intense thermal activity is observed at a volcano, the VOLCAT eruption detection thresholds are automatically adjusted to increase sensitivity." Notas: "Thermal output justifies loosening of detection thresholds"; "6.8 sdev anomaly". La figura es Ulawun (26-06-2019): potencia radiativa de 1 a 30 GW (eje de 10⁵ a 10¹¹ W) | 82 (verificado) |
| Umbrales que se aflojan con rayos | "When lightning is observed, the VOLCAT detection thresholds are automatically adjusted to enhance sensitivity." Figura: rayo temprano en la evolución de la nube | 83 (verificado) |
| Cuánto se aflojan | **No lo dice**: ni el umbral de calor, ni cuánto bajan los umbrales, ni qué umbrales | 82 y 83 |
| Lista de volcanes activos | Insumo **dinámico** de texto: "Active volcano list (text)". Aparte, insumo semiestático: "Global Volcanism Program volcanoes and feature selection thresholds (text)", o sea, umbrales de selección **por volcán** en un archivo de configuración | 68 |
| Qué decide entrar a la lista | No lo dice | 68 |
| Aprendizaje automático por píxel | Módulos "Pixel based machine learning for ash detection" y "Object based machine learning for ash detection" (y los mismos para SO₂); "LUTs for machine learning and associated constants (hdf4)" como insumo semiestático. Notas de la 79: "Machine learning + feature engineering", "sensor agnostic" | 65, 68, 79 |
| Qué variables y qué entrenamiento | **No lo dice.** Remite a SECO Parte 1 y 2 (2015) para el método de pluma o puff (79). El ATBD de 2025 (§ trabajo futuro) dice que un bosque aleatorio entrenado con casos clasificados por expertos está **en investigación**, primero para VIIRS; o sea, en 2022 a 2025 lo operativo sigue siendo el Bayes ingenuo de SECO | 79; ATBD 2025 |
| Seguimiento con a priori del cuadro anterior | Dos cosas distintas. (a) Detección: el seguidor busca, para cada píxel del cuadro actual, sus N vecinos espectrales y espaciales más cercanos en el cuadro anterior con un árbol k-d, y cuenta cuántos de ellos eran parte de la nube volcánica (mapa de 1 a 5 coincidencias en la figura de la 101). "Ash/SO2 detection should take advantage of previous detections where possible" (99). "Previous results influence current results" (64). (b) Propiedades: la altura, carga y radio del cuadro anterior se usan como **a priori de la recuperación** del cuadro actual (84) | 64, 99, 100, 101, 84 |
| Objetos chicos cerca de un cráter | Lo único: notas de la 80, método pluma o puff: "Temporal dimension allows for early detection of ash emissions composed of very few pixels (source volcano is assigned based on volcano close to emission origin)". Con ABI el método es "Spectral, spatial, and temporal"; con VIIRS sólo "Spectral and spatial". **Ningún umbral numérico** | 80 |
| Umbral o criterio numérico para objetos chicos | No hay. Los únicos números de selección de objetos siguen siendo la Tabla 4 de SECO Parte 2 (filas V50, V10 y V5) | ninguna |

## 2. Otros datos que importan para Chillán

- **Canales de entrada por defecto con ABI** (67): 0,64; 3,9; 7,0; 7,4; 8,5; **10,3**; 11,2; 12,3 y 13,3 µm, más GLM L2.
  El módulo de seguimiento k-d (74) lista ocho combinaciones de canales, y el mínimo utilizable es
  **10,3 y 11,2 µm**. El ATBD GOES-R de 2012 decía que 10,3 µm no se usaba para detectar con ABI; en 2022 la
  banda C13 entra al sistema al menos por el seguidor. La prueba de Londres usó C13 como banda de referencia en
  una variante (β(8,7/10,3) y β(12/10,3)), pero ninguna prueba calculó β(10,3/11,2). Es un dato,
  no una hipótesis: la presentación no dice que C13 entre a la probabilidad de ceniza.
- **Insumos dinámicos** (68 y ATBD 2025 §2.1): pronóstico GFS de 12 h, máscara global de nieve y SST. El cielo
  despejado lo calcula un modelo radiativo propio dentro de VOLCAT (ATBD 2025). **Ninguna de las dos fuentes
  menciona corrección de terreno ni de altura de superficie.**
- **Tasa de aciertos de las alertas** (88): sin GOES-17, sólo el **54 %** de las alertas de ceniza clasificables
  fueron detecciones correctas (requisito 50 %). VOLCAT acepta, por diseño, casi una falsa alarma por cada acierto
  en sus alertas automáticas; el requisito es "más aciertos que falsas alarmas al día" (notas de la 82 y 88).
- **Validación de exactitud de detección** (90): 99,5 a 99,7 % según tipo de nube, contra análisis humano. No
  dice cuántos casos ni si incluyen plumas chicas cerca del cráter.
- **Dominios de proceso** (72 y 73): el disco completo se parte en subdominios elegidos para que pocos volcanes
  queden en un borde; para GOES se eligieron con el VAAC de Washington.
- **Crecimiento vertical** (79 y 81): el segundo detector exige un enfriamiento de varios K entre cuadros
  (ejemplo de Raikoke: −14,5 K en 10 min = 5,8 desviaciones). Ya descartado para Chillán (H7 y lectura de
  Pavolonis 2018).

## 3. Qué cambia para H11 y para la etapa 2

1. **No contradice H11.** Ni la CDR ni el ATBD 2025 dicen que el cielo despejado corrija el terreno, y la
   presentación confirma que la selección de objetos usa umbrales por volcán guardados en archivos que no son
   públicos. La prueba de la etapa 1 sigue como estaba planeada.
2. **El aflojamiento por calor es para actividad intensa.** El ejemplo es de 1 a 30 GW y habla de "intense
   thermal activity". El calor de Chillán no lo ve ni el FDCF (H9: 0 hot spots en los cuadros con pluma), así
   que es dudoso que llegue al umbral de VOLCAT, que además no se conoce. Queda como posible trato permanente
   (H9), no se mide de nuevo.
3. **La dimensión temporal es el único mecanismo nombrado para objetos de "muy pocos píxeles" con ABI** (80).
   H7 descartó que el primer cuadro de cada tramo herede una detección anterior, y midió el enfriamiento de
   BT11 entre cuadros, pero no el **cambio de las métricas espectrales** (ε y β) respecto del cuadro anterior en
   el mismo lugar. La etapa 2 incluye ese cambio como variable candidata del clasificador, declarada antes de
   medir.
4. **El árbol k-d compara espectros con el cuadro anterior** (100): un píxel nuevo se parece a un píxel que ya era
   pluma. Eso explica la continuidad de los tramos, no su arranque (H7).
5. **C13 (10,3 µm)** se agrega a la etapa 2 como variable candidata (β(10,3/11) contra el mismo cielo despejado)
   sólo si el caché de C13 de la prueba de Londres cubre los cuadros; si no, queda anotado y no se baja.

## 4. Lo que la CDR no tiene

Variables y entrenamiento del aprendizaje automático, contenido de la lista de volcanes activos y de los
umbrales por volcán, cuánto bajan los umbrales con calor o rayos, y cualquier criterio numérico para objetos
cerca de un cráter fuera de la Tabla 4 de SECO Parte 2.
