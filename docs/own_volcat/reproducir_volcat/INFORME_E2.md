# Etapa 2: SECO propio entrenado con VOLCAT como etiqueta. Informe, 20-11-2026

Criterio commiteado antes del primer número: `criterio_E2_2026-11-20.md` (commit 3808223, rama
`claude/reproducir-volcat-e2`). Salida cruda: `resultados/e2_resultado.txt`; validación de la rejilla del
modelo radiativo: `resultados/e2_validacion_rejilla.txt`; diagnóstico posterior de objetos:
`resultados/e2_diagnostico_objetos.txt`. Scripts en `scripts/` (`rt_e2.py`, `e2_features.py`,
`e2_clasificador.py`, `huella_png.py`, bajadas en `fetch_e2.py` y `fetch_gfs_e2.py`).

## 1. Para geólogo

**Qué se hizo.** Se armó un VOLCAT casero con todo lo que SECO publica (emisividad y razones β contra un
cielo despejado modelado, los prefiltros, la probabilidad por Bayes ingenuo con los tres clasificadores
que ABI tiene siempre, los objetos, la bandera de nube, la robustez y la Tabla 4 con sus filas de volcán)
y se entrenó la parte que VOLCAT no publica, la probabilidad por píxel, usando las detecciones VOLCAT de
Chillán como etiqueta. Se probó jornada por jornada, sin dejar que el modelo viera la jornada que juzga:
795 scans (100 cuadros VOLCAT anclados al cráter en 10 jornadas, 655 scans sin pluma, 40 del manto del 16-11).

**Resultado: no cumple.** El SECO propio no reproduce **ninguno** de los 100 cuadros VOLCAT, y tampoco da
falsas alarmas (0 de 655, 0 de 40 en el manto). En todos los cuadros con pluma sí arma un objeto en el
cráter, y en el 73 % de ellos la bandera de nube ya vale 3, pero la probabilidad de ceniza de esos objetos
queda en 1,6 % de mediana (máximo 34 %), muy lejos del 80 % que exige la Tabla 4 en cualquier fila de
volcán.

**Por qué.** Con el prior de SECO (0,1 %), para llegar a 80 % la evidencia espectral tiene que ser unas
4.000 veces más probable en ceniza que en no ceniza. Nuestras variables, entrenadas con las mismas plumas
de Chillán, sólo llegan a unas 16 veces en la mediana. La señal infrarroja de estas plumas es demasiado
parecida a la del cráter sin pluma, lo mismo que vienen diciendo H3, β73 y H11 con controles pareados. Que
VOLCAT sí las publique implica que sus PDF (entrenadas con 344 escenas MODIS de ceniza y polvo, no con
Chillán) le dan a estos estados espectrales razones mucho más altas que las que justifican los datos de
Chillán, o que decide con algo que no está en SECO 2015 (la dimensión temporal que nombra la CDR 2022 para
emisiones de "muy pocos píxeles", diapositiva 80).

**El techo de nuestras variables (informativo).** Un bosque aleatorio con todas las variables por píxel y
la distancia al cráter, con la misma validación, reproduce 38 de 100 cuadros con 4,3 % de falsa alarma (28
de 655; una jornada con 15) y 0 en el manto; el 64 % de sus píxeles cae en la huella VOLCAT. Tampoco cumple
(pide ≥ 50 % y ≤ 2 %). Acierta sobre todo el 08-11 (11 de 13) y casi nada el 10-11 (1 de 12). Como los
controles pareados del mismo lugar no separan (H3, β73, H11), lo más probable es que el bosque esté
aprendiendo en parte las condiciones de los días con pluma (humedad, hora, nubosidad) y no sólo la pluma.

## 2. Números (salida cruda en `resultados/e2_resultado.txt`)

| Vara del 17-11 | SECO propio (decide) | Bosque aleatorio (informativo) |
|---|---|---|
| 1. Sensibilidad (≥ 50 %) | 0 de 100 = 0 % | 38 de 100 = 38 % |
| 2. Falsa alarma (≤ 2 %, ≤ 3 por jornada) | 0 de 655, máximo 0 | 28 de 655 = 4,3 %, máximo 15 |
| 3. Manto del 16-11 (≤ 10 %) | 0 de 40 | 0 de 40 |
| 4. Coincidencia con la huella (≥ 50 %) | sin píxeles seleccionados | 232 de 361 = 64 % |
| Cumple | **no** | no |

Sensibilidad del bosque por jornada (local de Chile): 21-10 0/1; 24-10 0/1; 25-10 2/4; 28-10 9/31; 29-10
1/1; 07-11 1/1; 08-11 11/13; 10-11 1/12; 11-11 2/3; 14-11 11/33. SECO propio: 0 en todas.

Diagnóstico de la cadena SECO (posterior al criterio, no decide):

| | Con pluma | Sin pluma | Manto |
|---|---|---|---|
| Objetos anclados (hasta 5 por scan) | 122 en 100 scans | 934 en 655 | 52 en 40 |
| Probabilidad mediana del objeto, mediana / máximo | 1,6 % / 34 % | 0,01 % / 87 % | 0 % / 7 % |
| Objetos con CF ≥ 3 | 73 % | 21 % | 52 % |
| Con al menos un píxel de robustez ≥ 2 | 50 % | 20 % | 13 % |

- Píxeles de ceniza VOLCAT en el disco de 40 km: 1.155; 631 (55 %) pasan los prefiltros de SECO 1 y
  reciben probabilidad. En los scans sin pluma pasa el 29 % de los píxeles.
- La cadena sí separa algo la pluma del resto del período (probabilidad 1,6 % contra 0,01 %, CF ≥ 3 73 %
  contra 21 %), pero muy lejos de los umbrales de la Tabla 4. Un objeto sin pluma llegó a 87 %: bajar el
  umbral para alcanzar a los positivos traería falsas alarmas.
- Ninguna fila de volcán exige menos de 80 % de probabilidad, así que ningún ajuste de CF o de robustez
  cambia el resultado.

## 3. Qué falta para igualar a VOLCAT y por dónde mejorarlo

1. **La probabilidad por píxel es lo que falta**, y no se puede aprender de Chillán: con sus propias plumas
   como entrenamiento la evidencia no pasa de 1,6 % en la mediana. Para igualar a VOLCAT hacen falta sus PDF
   (o el código, "disponible a pedido" según SECO 1). El correo a Pavolonis ya redactado
   (`Correo_VOLCAT_Pavolonis_v3.docx`, carpeta de notas del 19-11) es la vía directa.
2. **La dimensión temporal** es lo único que la CDR 2022 nombra para emisiones de pocos píxeles con ABI. No
   la probamos como variable del clasificador (los scans del caché no son consecutivos). Una etapa aparte
   podría bajar secuencias de 10 min continuas y medir el cambio de ε y β respecto del cuadro anterior en el
   mismo lugar, con control pareado.
3. **Corregir el terreno del cielo despejado**, la mejora propuesta en el criterio, no corresponde todavía:
   el criterio la condicionaba a que esta etapa cumpliera. H11 muestra además que, de día, el error de
   terreno es el que pone la bandera de nube en 3; corregirlo haría más difícil, no más fácil, pasar las
   filas de volcán.
4. **Para el dashboard**: nada que llevar. Ni el SECO propio ni el bosque cumplen la vara; la capa VOLCAT
   externa (ficha SDA v2.8, §A.7) sigue siendo la mejor información disponible.

## 4. Advertencias

- Sin canales solares ni 3,9 µm (no están en el caché; H1 y H9 ya los descartaron como separadores), así
  que faltan los clasificadores de día y de noche de SECO 1 Tabla 3. VOLCAT sí los usa.
- La "probabilidad de objeto" de SECO no es reproducible; las filas que la exigen se dieron por no cumplidas.
  Con la probabilidad mediana tan baja, eso no cambia nada: todas las filas de volcán piden 80 % en una u
  otra columna.
- Sólo Chillán: no hay otros volcanes con objetos VOLCAT anclados en la ventana.
- 10 scans negativos quedaron fuera por estar a menos de 60 min de un objeto VOLCAT (regla del criterio).
- El computador se suspendió unas 4,5 h durante el cálculo; los procesos retomaron solos y el cálculo es
  reanudable, sin efecto en los resultados.
