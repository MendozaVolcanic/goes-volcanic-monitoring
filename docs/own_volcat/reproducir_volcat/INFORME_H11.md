# H11: terreno del cielo despejado, filas de volcán y atajo de SO₂. Informe, 20-11-2026

Criterio commiteado antes del primer número: `criterio_H11_2026-11-19.md` (commit 97e0a4b, en la rama
`claude/reproducir-volcat-h11`). Salida cruda: `resultados/h11_resultado.txt`. Scripts: `scripts/`.
Lectura de la CDR 2022 (etapa 0): `LECTURA_CDR_2022.md`.

## 1. Para geólogo

**La pregunta.** VOLCAT calcula cómo se vería cada píxel sin nubes (temperatura de superficie del GFS más
un modelo radiativo) y mide cuánto se aparta la observación. El GFS pone la cumbre de Chillán a 1.500 a
1.900 m en vez de ~3.200 m, así que su "cielo despejado" sale demasiado tibio sobre el cráter. H11
proponía que ese error, sumado a los criterios relajados que SECO aplica cerca de un volcán y a un atajo
para píxeles con SO₂, explicaba por qué VOLCAT publica estas plumas chicas.

**Lo que salió.** De día, el error de terreno hace que el cráter parezca "confiadamente nublado"
(bandera CF = 3) **con pluma o sin pluma**: 83 % de los controles y 71 % de los positivos. Esa parte de
H11 se cumple de día: la bandera que exigen las filas de volcán no distingue nada en el cráter. De noche
no: el error baja a ~3 K y sólo 4 de 14 cuadros con pluma (y 0 de 13 controles) llegan a CF = 3. Y
ninguna compuerta espectral pública separa la pluma del mismo lugar sin pluma: el atajo de SO₂ (A5) **no
se enciende nunca** (0 de 733 píxeles), y la firma de ceniza βtot(12/11) se corre apenas hacia la ceniza
(AUC 0,58).

**Veredicto según el criterio: no concluyente.** No se sostiene (CF ≥ 3 no llega a 80 % ni en positivos ni
en controles agrupados, y nada separa). No se falsa por (a), porque 62 % de los positivos pasa la bandera,
ni por (b), que pedía CF ≥ 3 en el 80 % de los controles y salió 66 %.

**Lectura.** H11 queda partida en dos. La pieza del terreno es real de día y explica que la bandera no
estorbe; la pieza del SO₂ no aparece (βtot(7,3/11) queda cerca de 0,15, lejos del 1,0 que pide A5, como
anticipaba SECO Parte 1). Lo que decide en VOLCAT, entonces, no está en ninguna compuerta pública que
podamos reproducir: está en las PDF del Bayes ingenuo y en la robustez de su Tabla 3, que no son públicas.
Eso es lo que intenta aprender la etapa 2, usando a VOLCAT como etiqueta.

## 2. Método (resumen; detalle en el criterio)

- **Pares**: 66 (37 de H3: 28-10, 29-10 y 14-11; 29 de β73: 22-10 al 14-11), 10 días UTC, 14 de noche o
  crepúsculo (cenit solar ≥ 80°), 733 píxeles de huella. Control = mismo minuto en un día sin pluma,
  elegido antes por BT11 de la huella (pares de H3 y β73 tal como estaban).
- **Modelo radiativo**: el de H3 sin cambiar su física (líneas HITRAN, MT_CKD, SRF del ABI de GOES-19,
  emisividad fija, GFS 0,25°), extendido para dar la radiancia de una nube negra en cada nivel con la
  atmósfera de arriba (SECO 1, ec. 2). Calculado directo en cada píxel usado (huella, anillo de 2 a 6
  píxeles y anillo de 12 píxeles para la bandera): 120.944 píxeles, sin la rejilla que el criterio
  permitía, así que la comprobación de rejilla no hizo falta.
- **Ventana**: `window.json` y `latlon.npz` del detector del 17-11 ya no estaban; `scripts/ventana.py`
  la reconstruyó calzando la radiancia del caché contra el L1b (diferencia máxima 4e-6) y el cielo
  despejado recalculado coincide exacto (diferencia relativa 0) con el guardado por H3 y β73 en 14 píxeles.

## 3. Resultados

### (A) Bandera CF ≥ 3 (SECO 2 §4.3; objeto = huella)

| Estrato | Positivos | Controles | BTbias_obj pos / ctrl (mediana) | Diferencia obj − entorno pos / ctrl |
|---|---|---|---|---|
| Agrupado (decide) | 0,621 (41 de 66) | 0,662 (43 de 65) | +9,7 / +8,4 K | +8,1 / +7,3 K |
| Noche y crepúsculo | 0,286 (4 de 14) | 0,000 (0 de 13) | +5,1 / +3,3 K | +4,6 / +3,8 K |
| Día | 0,712 (37 de 52) | 0,827 (43 de 52) | +10,5 / +8,9 K | +8,6 / +8,8 K |

BTbias = BT11 de cielo despejado modelado menos BT11 observado. Sensibilidades: sin filtro de nube en el
anillo, 0,561 / 0,515; con el objeto sólo sobre píxeles que no pasan los prefiltros, 0,394 / 0,281.

- De día el modelo queda ~9 K más tibio que la cumbre observada y ~0 K en el entorno: la diferencia supera
  los 6 K de CF = 3 sin necesidad de pluma. Coincide con lo medido en H3 (7 K en los controles).
- De noche el error de terreno es de ~3 a 4 K y la diferencia con el entorno no llega a 6 K en los
  controles. Los positivos nocturnos quedan ~1,8 K más fríos respecto del modelo que sus controles
  (+5,1 contra +3,3 K): podría ser la pluma, pero son 14 pares en 5 días y el criterio no lo pregunta.

### (B) Compuertas espectrales (píxeles de huella, positivo contra el mismo píxel del control)

| Señal | AUC lado ceniza | IC 95 % por día | AUC anillo | Medianas pos / ctrl | ¿Separa? |
|---|---|---|---|---|---|
| A5 (SO₂) | 0,500 | 0,500 a 0,500 | 0,500 | 0 de 733 píxeles en los dos | no |
| βtot(12/11) | 0,582 | 0,542 a 0,641 | 0,514 | 0,871 / 0,896 | no (pide ≥ 0,70) |
| Prefiltros de SECO 1 | 0,515 | 0,500 a 0,557 | 0,498 | 50 % / 47 % de la huella | no |
| εtot(11) | 0,554 | 0,531 a 0,607 | 0,574 | 0,159 / 0,139 | no |
| βopaque(12/11) | 0,507 | 0,476 a 0,645 | 0,463 | 0,914 / 0,982 | no |
| βtot(8,5/11) | 0,453 | 0,418 a 0,555 | 0,429 | 0,988 / 1,006 | no |
| βopaque(8,5/11) | 0,412 | 0,386 a 0,468 | 0,411 | 0,629 / 0,707 | no |
| βtot(7,3/11) | 0,542 | 0,333 a 0,662 | 0,526 | 0,180 / 0,133 | no |

- **A5 nunca**: βtot(7,3/11) no pasa de ~0,2 en mediana y βtot(8,5/11) queda cerca de 1, lejos de 1,0 y
  1,5. Es lo que SECO Parte 1 hacía esperar: un error que es sobre todo de superficie mueve 11 y 12 µm casi
  igual y deja la emisividad a 7,3 µm cerca de 0.
- **βtot(12/11)** se corre hacia la ceniza en 7 de 10 días y el anillo no (0,51), pero el efecto es chico:
  0,87 contra 0,90 en mediana. Es la única señal con algo de dirección propia.
- Píxeles con β válido: 659 de 733 en la huella del positivo para βtot(12/11), 329 para βtot(7,3/11).
- De noche (informativo) εtot(11) da 0,67 y βtot(7,3/11) 0,83, pero con 14 pares, anillo que también
  separa (0,60 y 0,77) y 22 píxeles válidos en el control para β(7,3/11): no se puede leer como señal.

## 4. Qué cambia

- **Para el plan**: la etapa 2 sigue como estaba. H11 dice que la bandera CF no es lo que filtra de día y
  que el atajo de SO₂ no es lo que deja entrar a estos píxeles. Lo que queda por aprender es la probabilidad
  por píxel y la robustez, que es justo lo que la etapa 2 entrena con VOLCAT como etiqueta.
- **Para el dashboard**: nada. No hay compuerta que llevar a `detect_ash_enhanced`.
- **Límite principal**: nuestro cielo despejado no es el de VOLCAT. SECO usa SeeBor para la emisividad,
  otro modelo radiativo y quizá otra resolución del GFS. Si su error de terreno fuera distinto, la parte (A)
  cambiaría. El error de H3 en controles (7 K) y el de esta prueba (9 K de día) concuerdan entre sí, no con
  VOLCAT, que no publica el suyo.

## 5. Advertencias

- BTbias_obj sobre toda la huella, no sólo sobre los píxeles con probabilidad < 10 % (no calculable sin
  las PDF de VOLCAT). La sensibilidad con los píxeles sin prefiltro baja CF ≥ 3 a 0,39 / 0,28.
- La prueba de nube del anillo es nuestra (cielo empírico − 3 K), no la de Heidinger et al. 2012.
- La muestra está cargada al 14-11 (32 de 66 pares), un día de pluma continua por la tarde.
