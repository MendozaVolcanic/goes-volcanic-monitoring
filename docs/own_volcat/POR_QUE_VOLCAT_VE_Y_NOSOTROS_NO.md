# Por qué VOLCAT ve ceniza en Nevados de Chillán (nov-2026) y nuestro detector no

Fecha: 17-11-2026, actualizado el 18-11 (pasos 2, 3 y 4 del plan, §3.1), el 19-11 (H3 y H7, §3.2; H6 cerrada) el 19-11 en la tarde (β(7,3/11) fuera de muestra y prueba tolerante del VAAC de Londres, §3.3), el 19-11 en la noche (calor a 3,9 µm, rayos GLM y dirección de la pluma, §3.4) el 20-11 (H11 y SECO propio entrenado con VOLCAT, §3.5; corrección del alcance de H8) y el 20-11 en la noche (Test 3 original de Francis 2012 y cambio entre cuadros consecutivos, §3.6) y el 21-11 (tablas, configuración y eventos públicos de VOLCAT: H14, C2, C2b y H15, §3.7) y el 23-11 (H16 a H28, §3.9, con la respuesta vigente al comienzo de §1). Estado: **informe con diecinueve pruebas y lecturas medidas y un plan; no cambia código de detección.** Desde el 19-11 el dashboard muestra la detección VOLCAT por volcán como capa externa (ficha SDA v2.8, §A.7).
Antecedentes: plan de validación §3.4 a §3.6 (`docs/own_volcat/PLAN_VALIDACION_MAGNITUD.md`) y el informe
del detector (`C:\Users\nmend\AppData\Local\Claude-Data\claude_pzs8sxrjxfjjc\side-session-notes\local_f3a7d295-ddde-4b7c-b258-25e760c44266\INFORME_variantes.md`).

## 1. Respuesta corta, para geólogo

**Respuesta vigente (23-11-2026, después de H17 a H29 y la revisión S20; detalle en §3.9).** Lo que sigue en esta sección después de
este bloque es la historia de cómo se llegó, desde el 17-11.

**Lo nuevo de S20 (24-11-2026), en cuatro líneas.** (1) Cuando un satélite fino dice dónde está la pluma, GOES-19 la
ve: el píxel junto al cráter baja cerca de 1 K en 11 − 12 µm (S20b, dos mañanas). (2) A 100 m la pluma del 25-10 tiene
firma de ceniza de unos −1,5 K (S20d, post hoc: por la regla salió SIN FIRMA porque el control tenía pluma). (3) Lejos
del cráter hay una firma débil que se mueve con el objeto de VOLCAT (H29 y su revisión). (4) Las pruebas viejas "sin
firma" usaban controles con el volcán activo y no valen como ausencia (S20c, sin poder para afirmar lo contrario). En
una frase: GOES ve la ceniza de Chillán, diluida en un píxel que la pluma llena sólo en parte; no hay todavía un
detector.

- **VOLCAT no ve la pluma de Chillán en el píxel.** Su propia probabilidad infrarroja es menor que 0,05 en 762 de
  767 píxeles de la huella (H20a), y la probabilidad que publica de día es baja (sitio de VOLCAT).
- **La publica por seguimiento.** De los 60 cuadros con archivo de evento, 56 son continuaciones de un objeto que
  nació antes. La regla de seguimiento, leída de los registros de VOLCAT y probada en datos que no se usaron para
  deducirla, es un radio de 3 km por minuto entre imágenes alrededor de lo último publicado (30 km con 10 min), con
  los filtros de ruido y de tamaño apagados. Se cumplió en 3.969 de 3.969 comparaciones, en tres satélites (H28).
  Explica 51 de las 56 continuaciones de Chillán; las otras 5 siguen a cuadros que VOLCAT se saltó por atraso.
- **Lo que decide es el nacimiento, y no lo conocemos.** Cuatro cadenas nacen el 13, 14 (dos) y 18-11. La puerta de
  nacimiento mide contraste de forma y borde contra el entorno, no firma de ceniza, y su regla completa no está en
  ningún registro público (H28).
- **Con verdad del OVDAS, los pulsos de la mañana no dejan firma IR.** La explosión de 2.000 m del 27-10 no deja
  firma ni hacia el NO (dirección del REAV, H24) ni hacia el NNE (viento GFS, H25), con una prueba que habría visto
  una capa de ε 0,10 sobre el sector. Una pluma angosta (6 km) queda sin probar.
- **Los pulsos de tarde que VOLCAT marcó siguen sin respuesta.** No hay tardes despejadas sin actividad para el fondo
  en primavera (H24); el fondo prestado de Antuco y Longaví no sirve porque Chillán es 1,5 veces más ruidoso (H27,
  inválido). Queda la prueba de verano, ya registrada (`h24_verano/REGISTRO_PROSPECTIVO.md`).
- **Copiar la decisión con nuestras radiancias no da los mismos píxeles** (H26): un seguidor anclado al cráter
  caliente recupera 12 de 769 píxeles de VOLCAT y dispara en 7,7 % de los cuadros sin VOLCAT. Lo único que coincide
  es la cercanía al cráter.
- **Lejos del cráter apareció la primera firma, débil** (H29, revisión S20). El 08-11, en los píxeles que VOLCAT
  marca a más de 30 km, la BTD (11 − 12 µm) queda 0,37 K bajo la de píxeles del mismo cuadro con igual BT11 y cota,
  fuera de lo que dan los días sin evento. Entre 15 y 60 km esa BTD baja se mueve con la huella de VOLCAT cuadro a
  cuadro (p < 0,0001); a más de 30 km solo, la tendencia no alcanza (p 0,095). Equivale a una pluma tenue o angosta
  (f·ε ≈ 0,12). Atribución a ceniza: SOSPECHA reforzada, porque una nube que VOLCAT siga desde el cráter daría lo mismo.
- **Con la huella medida por un satélite fino, la pluma de la mañana sí deja firma** (S20b, §3.9). En dos mañanas
  despejadas (25-10 y 08-11) Landsat 8 y Sentinel-2 dan la huella, la dirección y la altura (por la sombra) de la
  pluma; llevada a la grilla de GOES, llena 18 y 43 % de un píxel, y ese píxel queda cerca de 1 K más bajo en
  11 − 12 µm y 4 a 7 K más frío que su anillo, comparado con su propia historia despejada (SEÑAL por la regla, con
  controles post hoc favorables). El 25-10 la pluma iba al OSO, no al SE del REAV, que es donde buscó H24. Son dos
  eventos y un píxel cada uno: no es un detector todavía.
- **Varias pruebas "sin firma" comparaban pluma contra pluma** (MET-01, §3.9): sus controles "sin pluma" caían casi
  todos en días con actividad, y en el paso 2, H3 y Londres además con un objeto de VOLCAT cerca. Esas pruebas no
  demuestran ausencia de firma.

**En una frase:** VOLCAT publica Chillán por una decisión de objeto (nacimiento por contraste y seguimiento por
distancia), no por una medición de ceniza en 11 y 12 µm; nuestro IR ve, en el mejor caso medido, una firma débil que
acompaña a su objeto, y parte de las pruebas que no vieron nada usaban controles con el volcán activo.
Para el dashboard, VOLCAT sigue como capa externa (ficha SDA §A.7).

**El fenómeno.** Las plumas de Chillán de noviembre son chicas (3 a 5 km de altura, unos 8 km de largo)
y casi transparentes en el infrarrojo térmico. Dentro de la zona donde VOLCAT dibuja ceniza, la
temperatura de brillo a 11 µm queda igual o **más tibia** que el cielo despejado del mismo píxel, y la
diferencia 11 − 12 µm no se mueve. En el infrarrojo, la pluma prácticamente no está.

**Lo que se creía el 17-11 y ya no se sostiene.** La sospecha principal era que VOLCAT ve estas plumas
con la luz del sol (visible de 0,65 µm y reflectancia de 3,9 µm, SECO, Pavolonis et al. 2015), porque
las 58 detecciones de noviembre ancladas al cráter eran de día. Las pruebas del 18-11 la descartan:
- De noche también: el 28 y 29-10 VOLCAT siguió una pluma de Chillán de día y **de noche** (tres cuadros
  seguidos a las 22:00 a 22:20 de Chile, con el sol 110° bajo el cenit). Dentro de esa huella, el IR
  tampoco muestra frío ni BTD negativa.
- De día, los canales solares no distinguen la huella del mismo lugar en un día sin pluma con el mismo
  estado térmico (AUC 0,50 en las tres señales).

**Es ceniza (19-11).** Nicolás, geólogo del OVDAS, cerró H6: "el volcán lleva muchos días con pulsos y
columnas de gas y ceniza en cantidades variables". VOLCAT dibuja ceniza real; el problema es nuestro.

**Lo medido el 19-11 (§3.2).** Ni el cielo despejado modelado ni el seguimiento entre cuadros
explican la diferencia:
- H3, cielo modelado y razones β con la banda de vapor de agua de 7,3 µm: **no concluyente, y en la
  práctica no separa**. Con un cálculo radiativo propio (perfil GFS, líneas HITRAN, sesgo medido de
  −0,29 K en 11,2 µm) la compuerta de VOLCAT deja pasar casi todo, huella y día sin pluma por igual
  (90 % contra 88 %): sobre el volcán el modelo queda unos 7 K más tibio que lo observado porque el GFS
  pone ese terreno a ~1.700 m y no a ~3.200 m. La compuerta mide el error del terreno, no la pluma.
  Con el cielo despejado empírico, la huella casi no pasa la compuerta (3,5 %).
- H7, VOLCAT sigue un objeto detectado antes con señal: **falsada**. En los tres episodios (28-10,
  10-11, 14-11) el primer cuadro tampoco tiene señal propia: ni BTD, ni hot spot FDCF, ni enfriamiento
  rápido.

**Lo que queda.** H2 (trato especial cerca de volcanes) sigue abierta, ahora con un mecanismo concreto
para probar: si el cielo modelado de VOLCAT comete el mismo error de terreno en la cumbre, el cráter pasa
siempre su primera compuerta y la decisión cae en los criterios relajados del objeto chico anclado.

**Lo medido el 19-11 en la tarde (§3.3).** Las dos vías que quedaban con señal publicada tampoco cumplen:
- El indicio nocturno de β(7,3/11) (28 y 29-10) **no se repite fuera de muestra**: de noche no es
  concluyente porque el anillo sin ceniza alrededor de la huella separa más que la huella misma, y de día
  se falsa. Lo que mide la banda de 7,3 µm es la humedad de toda la escena, no la pluma.
- La prueba tolerante del VAAC de Londres (Francis et al. 2012) **no cumple**: el método completo ve 2 de
  35 cuadros y 0 de 82 píxeles dentro de la huella VOLCAT. Sin sus filtros marca uno de cada cinco
  píxeles de la huella, pero dispara en más de la mitad de los scans sin pluma.

Con esto se agotan los mecanismos espectrales publicados que podemos reproducir. Lo que queda sin probar
son los umbrales por volcán y el clasificador de VOLCAT, que no son públicos.

**Lo medido el 19-11 en la noche (§3.4).** Tampoco es el contexto ni el lugar:
- **Calor y rayos (H9).** El cráter está caliente a 3,9 µm casi todas las noches desde el 24-10 (71 % de
  las noches despejadas sobre el p99 de dos volcanes de control), así que VOLCAT probablemente tiene a
  Chillán marcado como activo todo el periodo. Pero el calor no dice **cuándo** dibuja la pluma (AUC
  0,46 de noche) ni marca el arranque de los tramos, y ningún cuadro con pluma tiene rayos GLM cerca.
  Puede explicar un trato especial permanente del cráter, no el momento.
- **Dirección (H10).** No concluyente con dos jornadas comparables. El viento GFS reproduce la dirección
  del REAV, pero la huella VOLCAT queda entre el S y el E del cráter casi siempre. Y donde el OVDAS vio
  la pluma, la split-window tampoco pasa el umbral: la pluma es casi transparente en el IR también ahí.

**Lo medido el 20-11 (§3.5).** Se reprodujo la cadena pública de VOLCAT (SECO 2015) con nuestro propio
cielo despejado modelado, y no alcanza:
- **Terreno y filas de volcán (H11): no concluyente.** De día el GFS pone la cumbre a 1,5 a 1,9 km y el
  cielo despejado queda tan tibio que el cráter sale "confiadamente nublado" con pluma o sin pluma (71 % de
  los cuadros con pluma, 83 % de los controles): la bandera que piden las filas de volcán de SECO no
  distingue nada ahí. De noche no (29 % contra 0 %). El atajo de SO₂ no se enciende nunca y la firma de
  ceniza apenas se mueve.
- **SECO propio entrenado con VOLCAT (etapa 2): no cumple.** Arma el objeto en el cráter en todos los
  cuadros con pluma, pero su probabilidad de ceniza queda en 1,6 % de mediana contra el 80 % que exige SECO:
  0 de 100 cuadros VOLCAT reproducidos. Con las variables públicas, la pluma de Chillán se parece demasiado
  al cráter sin pluma.

**Lo medido el 20-11 en la noche (§3.6).** Las dos últimas vías publicadas tampoco alcanzan:
- **Test 3 original del VAAC de Londres (H12): no concluyente.** Es la única compuerta publicada que admite
  diferencias 11 − 12 µm positivas, justo donde viven estas plumas, porque compara contra el cielo despejado
  modelado. Marca la huella en 76 % de los cuadros con pluma, pero también en 52 % del mismo lugar sin pluma,
  y en el píxel apenas distingue (AUC 0,58). La razón es el terreno otra vez: sin pluma, el cielo modelado ya
  espera 0,6 K más de lo observado sobre el cráter, y la pluma agrega sólo ~0,25 K. El control de cumbres
  (Antuco y Longaví) no tuvo el error de Chillán y no pudo cerrar la prueba como "mide el terreno".
- **Cambio entre cuadros de 10 min (H13): se falsa.** Restar el cuadro anterior no limpia el cráter: los
  cambios con pluma son del mismo tamaño que los del cráter sin pluma a esa hora (mejor AUC 0,58 de 18
  variables). Lo que no deja marca en un cuadro tampoco la deja en la diferencia entre dos.

**Lo hallado y medido el 21-11 (§3.7).** Las tablas de probabilidad y la configuración de VOLCAT para ABI
resultaron estar en el servidor público de SSEC, junto con archivos de evento de Chillán en la grilla ABI:
- **VOLCAT mismo dice que estas plumas no tienen firma IR (H14).** En sus 60 archivos de evento de Chillán, su
  indicador de firma de onda larga queda bajo 0,05 en el 99,35 % de los píxeles, también en el primer cuadro de
  cada evento y junto al cráter. Lo que publica entra por el objeto, el seguimiento o el detector de crecimiento,
  no por la firma del píxel. Compatible con H14, sin fuerza todavía (4 eventos).
- **Nuestras huellas estaban corridas un píxel.** Las decodificadas del PNG caen 1 fila al S y 1 columna al E de
  los píxeles que VOLCAT publica; con objetos de 1 a 2 píxeles de ancho, eso diluyó cada comparación desde el 17-11.
- **El cielo despejado de VOLCAT sigue la cota fina del terreno** (caso de prueba de Mauna Loa, análisis
  posterior); el nuestro no, y por eso queda 7 a 9 K más tibio en la cumbre de Chillán.
- **Las tablas reales se leen y reproducen a VOLCAT en nube espesa, no en nube tenue** (H15), justo donde viven
  estas plumas. Faltan dos piezas que no están en lo público: la regla para nube tenue y el cielo despejado
  corregido que entra a la emisividad. Son las preguntas del correo v5 a Pavolonis.

Lo que hace que VOLCAT publique estas plumas ya no es "lo que no es público" en general: es su lógica de objeto y
seguimiento sobre píxeles sin firma IR, más dos reglas concretas de nube tenue y cielo despejado que sólo el autor
puede confirmar.

**Qué no es.** No es un problema de umbral (cuatro variantes lo descartaron) ni un corrimiento de la
huella por paralaje (prueba A, abajo), ni una señal escondida en la banda de 8,5 µm (prueba B), ni la luz solar (pasos 2 y 4, §3.1).

## 2. Qué hace VOLCAT para detectar, según sus fuentes

| Hecho | Fuente | Cómo se leyó |
|---|---|---|
| No usa BT ni BTD: convierte radiancias en emisividad efectiva y razones β contra una radiancia de **cielo despejado modelada** (GFS + emisividad de superficie + modelo radiativo) | ATBD GOES-R VolAsh v3.0 (2012) §3.4.1 y §3.4.2.1; SECO Part 1 §4.1 | ATBD leído local; SECO leído en HTML |
| Pares de bandas: β(12/11), β(8,5/11) y β(7,3/11); el 10,3 y el 13,3 µm no se usan con ABI para detectar | ATBD §3.4.1.2; SECO Part 1 §2, Tabla 1 | idem |
| Un píxel sólo es candidato si ε(11 µm) ≥ 0,02 respecto del cielo despejado modelado | ATBD §3.4.2.4.1 regla 1; SECO Part 1 §4.2 | idem |
| De día suma la razón de reflectancias ρ(3,9/0,65): ceniza y polvo tienden a dar más de 0,5 si la profundidad óptica visible supera ~0,1; las nubes de agua o hielo, menos | SECO Part 1 §4.1 | HTML |
| La probabilidad por píxel es Bayes ingenuo entrenado con 344 gránulos MODIS; después agrupa píxeles en objetos con umbrales que bajan por contraste espacial | SECO Part 1 §4.2; Part 2 §4.1 | HTML |
| "Muchos" píxeles retenidos en objetos tienen BTD 11−12 **positiva** | SECO Part 2 §4.1 | HTML |
| **Criterios relajados por cercanía a volcán**: con el centro del objeto a menos de 50, 10 o 5 km de un volcán se aceptan objetos de 0 a 25 píxeles | SECO Part 2 §4.4, Tabla 4 | HTML |
| En 2015 SECO **no detectó** plumas débiles de Kizimen y Karymsky con BT11 muy parecida al cielo despejado calculado; propone seguimiento temporal y forma de pluma como mejora | SECO Part 2 §6 y §8 | HTML |
| El split-window solo, con umbral −1,25 K, da POD ~0,30 en su conjunto de entrenamiento | SECO Part 1 §4.2, Fig. 7 | HTML |
| Pavolonis et al. 2006 detectaban nubes volcánicas de día con 0,65, 3,75, 11 y 12 µm aun con BTD mayor que +2 K | Pavolonis et al. 2006, JTECH | sólo el abstract |

Referencias (DOI verificados en Crossref):
- Pavolonis, Sieglaff y Cintineo (2015a), JGR Atmos 120, 7813-7841, doi:10.1002/2014JD022968 (SECO Part 1).
- Pavolonis, Sieglaff y Cintineo (2015b), JGR Atmos 120, 7842-7870, doi:10.1002/2014JD022969 (SECO Part 2).
- Pavolonis, Sieglaff y Cintineo (2018), Earth Space Sci., doi:10.1029/2018EA000410 (crecimiento vertical; leído abstract y §6).
- Pavolonis, Heidinger y Sieglaff (2013), JGR Atmos 118, 1436-1458, doi:10.1002/jgrd.50173 (altura; sólo abstract).
- Pavolonis, Feltz, Heidinger y Gallina (2006), JTECH 23, 1422-1444, doi:10.1175/JTECH1926.1 (sólo abstract).
- ATBD GOES-R Volcanic Ash v3.0 (julio 2012), copia local en `docs/` de los worktrees (no versionada).

**Lo que no sabemos de VOLCAT hoy.** Los papers son de 2015 y 2018. La versión operativa de 2026 puede
haber agregado seguimiento temporal u otras pruebas; no hay documentación pública leída que lo diga.

## 3. Lo medido en esta sesión

Criterio declarado antes de medir: `C:\Users\nmend\AppData\Local\Claude-Data\claude_pzs8sxrjxfjjc\side-session-notes\local_f3a7d295-ddde-4b7c-b258-25e760c44266\criterio_corrimiento_y_8p5_2026-11-17.md`.
Script: `prueba_AB.py`, en la misma carpeta. Datos: cache del detector (ventana de 83 × 94 píxeles con
C11, C14 y C15) y huellas VOLCAT sin dilatar, sin bajar nada nuevo. 56 cuadros positivos, 520 píxeles de huella.

**Prueba A, corrimiento de la huella (paralaje).** En Chillán GOES-19 mira con 42,9° de ángulo cenital,
así que una nube a h km aparece ~0,93·h km más al sur en la imagen ABI. Si SSEC dibujara la ceniza ya
corregida, la señal fría estaría 1 a 4 filas al sur de la huella.
- Resultado: corriendo la huella hasta 5 píxeles en cualquier dirección, la mediana de ΔBT11 en los
  positivos nunca baja de −0,5 K dentro de ±2 píxeles; en (0, 0) es +0,73 K, y 1 a 2 filas al sur es
  +0,8 y +0,6 K. **No hay señal fría desplazada en ninguna dirección.**
- Según el criterio: el mínimo de "positivos menos nulo" quedó en dy = −1, dx = −1 (al norte), a 0,5 K
  del origen. **Falsada.**
- Advertencia: el nulo (misma huella en días negativos) salió dominado por días nublados (ΔBT11 de −9 a
  −25 K), así que la resta no vale como comparación fina. La conclusión se sostiene igual con los positivos
  solos: no hay frío que buscar.

**Prueba B, banda de 8,5 µm.** AUC (huella contra la misma huella en el nulo):
ΔBTD 0,50; Δ(BT8,5 − BT11) 0,26; ΔBT11 0,05. Según el criterio (AUC de 8,5 µm < 0,60): **falsada**. El
mismo nulo nublado afecta esta prueba: una nube de agua o hielo también mueve el 8,5 µm. Con el nulo
nublado, el resultado dice que la huella se parece más a cielo despejado que a nube, no que la
banda de 8,5 µm vea ceniza.

**Hora de las detecciones VOLCAT** (`cuadros_10min.csv`, 2.304 slots del 01 al 16-11, 85 a 95 cuadros
publicados por hora UTC): fuera del 16-11, los 58 cuadros anclados al cráter caen entre las 15:00 y las
23:20 UTC (12:00 a 20:20 de Chile). Entre 00 y 08 UTC (21:00 a 05:00 de Chile) hay 0 en 16 noches. Los
objetos miden de 4 a 49 píxeles del PNG (mediana 10).

### 3.1 Segunda tanda (18-11): pasos 3, 2 y 4 del plan

Cada paso con su criterio escrito antes de medir, en la carpeta de notas de la sesión
(`C:\Users\nmend\AppData\Local\Claude-Data\claude_pzs8sxrjxfjjc\side-session-notes\local_f3a7d295-ddde-4b7c-b258-25e760c44266\`):
`criterio_paso3_objetos_lejos_2026-11-18.md`, `criterio_paso2_canales_solares_2026-11-18.md` y
`criterio_paso4_volcat_nocturno_2026-11-18.md`. Los scripts quedaron en la misma carpeta.

**Paso 3: ¿VOLCAT dibuja objetos chicos sólo cerca de volcanes? (H2).** Se decodificaron los 2.181
cuadros del sector `Chile_Central_2_km` (01 al 16-11) y se contaron los objetos de 4 a 36 px del PNG
(hasta ~25 px ABI, el techo de la Tabla 4 de SECO) según su distancia al volcán Holoceno más cercano
(lista GVP del Smithsonian, 57 volcanes en el sector sin contar Chillán; se excluye todo lo que está a
menos de 50 km de Chillán). Antes de contar hubo que enmascarar el título, el globo y los logos del PNG,
que la decodificación tomaba por ceniza.

| Zona | Área útil | Objetos chicos, 16 días | Sin el 16-11 |
|---|---|---|---|
| A: a ≤ 10 km de un volcán | 17.438 km² | 139 | 11 |
| B: 10 a 50 km | 177.747 km² | 1.315 | 67 |
| C: a más de 50 km | 2.349.386 km² | 5.482 | 1.804 |
| R = densidad en A y B / densidad en C | | **3,2** | 0,52 |

- Según el criterio, R = 3,2 es **no concluyente** (entre 2 y 5). El 16-11 pesa el 73 % de los objetos
  chicos: ese día un sistema grande cubrió la cordillera y se partió en fragmentos cerca de muchos
  volcanes (Tromen, Resago, Laguna del Maule, Infiernillo, Payún Matrú, Antuco).
- Sin el 16-11 (sensibilidad, no decide) el cociente se invierte: R = 0,52. VOLCAT dibujó objetos
  chicos lejos de todo volcán en 373 de 2.050 cuadros, casi todos al norte de 34° S y al este de la
  cordillera (Cuyo), entre el 02 y el 06-11, y **tres de cada cuatro de noche** (454 de 1.804 con sol).
  El producto se llama "Ash/Dust Cloud Height": es probable que sea polvo, pero no está verificado.
- Lectura: **VOLCAT no necesita estar cerca de un volcán para publicar un objeto chico**. Eso no
  descarta que el trato especial al cráter sea lo que deja pasar los objetos de Chillán: el polvo de
  Cuyo trae una señal IR que la pluma de Chillán no tiene. La prueba era débil para H2 y H2 queda abierta.
- Dato para H1: VOLCAT sí publica objetos chicos de noche, y por montones. Que en Chillán no aparezca
  ninguno de noche no se explica porque VOLCAT nunca dibuje de noche, y por eso pesa algo más.

**Paso 2: canales solares (H1 b).** Se leyeron por ventana C02 (0,64 µm, 0,5 km), C07 (3,9 µm) y C14
(11,2 µm) de 366 escenas (61 MB): los 46 cuadros positivos con sol alto (cenit < 75°) y el mismo minuto
UTC en los 10 días sin pluma. Señales por píxel de 2 km: reflectancia de 0,64 µm (r065), su textura
dentro del píxel (sd065) y la razón ρ(3,9/0,65), con la reflectancia de 3,9 µm calculada restando la
emisión térmica estimada con BT11. El control de cada positivo es el día sin pluma con el BT11 de la
huella más parecido (diferencia mediana 1,5 K), elegido mirando sólo C14.

| Señal | AUC con control pareado (decide) | Mediana positivo / control | AUC con los 10 días juntos |
|---|---|---|---|
| ρ(3,9/0,65) | 0,498 | 0,44 / 0,41 | 0,70 |
| r065 | 0,509 | 0,155 / 0,155 | 0,29 |
| sd065 | 0,499 | 0,038 / 0,041 | 0,43 |

- Según el criterio (las tres con |AUC − 0,5| < 0,10): **falsada**. Por día, el AUC va de 0,34 a 0,60;
  ningún día separa.
- Con los 10 días juntos aparece una separación (ratio 0,70; r065 0,29), pero es la del nulo nublado ya
  vista en las pruebas A y B: los controles brillantes son nubes. Cuando el control tiene el mismo
  estado térmico, la diferencia desaparece.
- La fracción de píxeles con ρ(3,9/0,65) > 0,5, el umbral de SECO, es 0,44 en la huella y 0,41 en el
  control pareado. El suelo volcánico despejado ya pasa ese umbral, así que el umbral no sirve aquí.
- Salvedad: la irradiancia solar a 3,9 µm no viene en el archivo y se tomó de un cuerpo negro a 5.778 K.
  Ese error es multiplicativo, igual para la huella y el control, así que no cambia el AUC.

**Paso 4: VOLCAT de noche en otras fechas (H1 a).** SSEC todavía publica el sector desde el 25-10 (el
01-10 ya da 404). Se bajaron y decodificaron los 1.177 cuadros del 25 al 31-10 y del 17 y 18-11 (~0,5 GB).
Antes de mirarlos, la validación del decodificador sobre el 01 al 16-11 mostró que la regla de manto no
atrapaba el sistema grande del 16-11 (objeto de 16.000 a 27.000 px, bajo el 5 % del mapa) y sus
fragmentos de madrugada. Por eso se enmendó el criterio antes de ver los días nuevos: cuentan sólo objetos
de 4 a 500 px y sólo en cuadros sin un objeto de más de 500 px a menos de 50 km del cráter. Con esa regla,
el 01 al 16-11 da 0 nocturnos.

| Día | Cuadros anclados de día | Crepúsculo (cenit 80 a 90°) | Noche (cenit ≥ 90°) |
|---|---|---|---|
| 25-10 | 4 (14:40 a 18:00 UTC) | 0 | 0 |
| 28-10 | 19 (18:30 a 22:10) | 5 | 2 (23:10 y 23:20, recién puesto el sol) |
| 29-10 | 1 | 0 | **5 (00:10 a 01:20 UTC, cenit 101 a 113°)** |
| 26, 27, 30 y 31-10; 17 y 18-11 | 0 | 0 | 0 |

- **Según el criterio, H1 cae como explicación completa**: el 29-10 hay tres cuadros nocturnos
  consecutivos (01:00, 01:10 y 01:20 UTC, es decir, 22:00 a 22:20 del 28-10 en Chile) con objetos de 5 a
  10 px anclados al cráter, sin sistema grande cerca. En total hay 3 pares consecutivos.
- En la imagen (`paso4_mosaico_28-29oct.png`, carpeta de notas) se ve un episodio continuo. Desde las
  21:50 UTC del 28-10 hay un objeto en el cráter; a las 22:40 aparece una nube fría en el IR justo al SE.
  VOLCAT la sigue mientras deriva al SE, ya de noche, hasta la 01:20 UTC, y a las 01:40 ya no queda nada.
- Dato descriptivo que no estaba en el criterio. El caché del detector cubre el 28-10 hasta las 23:50
  UTC. Dentro de la huella VOLCAT, la BT11 está 1,4 a 1,6 K **más tibia** que la referencia y la BTD es
  positiva (mediana +0,4 a +0,7 K, mínimo −0,19 K, 0 píxeles bajo −1 K) en los cuatro cuadros con escena
  (22:40, 23:00, 23:20, 23:40). La nube fría queda al lado de la huella, no adentro.
- Lectura: VOLCAT ve las plumas de Chillán también **de noche, donde nuestro split-window no ve nada**.
  El sol no es lo que hace la diferencia, o al menos no es lo único. Vuelve al frente H3: el cielo
  despejado modelado y las razones β, incluida la β(7,3/11) con la banda de vapor de agua (C10), que
  ninguna prueba nuestra usó todavía.
- Con 7 episodios en total (25-10, 28-10, 07, 08, 10, 11 y 14-11), el patrón "sólo de día" ya no se
  sostiene: el 28-10 cruza la noche.

**Prueba A repetida sobre el 28-10 (paralaje, H4).** Criterio escrito antes de medir:
`criterio_pruebaA_28oct_2026-11-18.md` (carpeta de notas). Cuatro cuadros con escena en el caché (22:40,
23:00, 23:20 y 23:40 UTC), huella = píxeles VOLCAT a ≤ 50 km del cráter. La altura VOLCAT es de 3,5 km
en los cuatro cuadros, así que el paralaje predice una huella corrida 1,1 filas al sur (unos 3 km) y casi
nada en E-O.
- BTD < −1 K: no aparece en ningún corrimiento de hasta 5 píxeles (máximo 0,04). **Por el lado de la
  ceniza, falsada en este episodio.**
- ΔBT11 < −2 K: el máximo (0,61) queda en 2 filas al sur y **5 columnas al oeste**, en el borde del rango
  buscado, y la fracción sigue creciendo hacia el SO. En (0, 0) es 0,07. En el corrimiento que predice el
  paralaje (1 a 2 filas al sur, sin corrimiento E-O) es 0,15 a 0,32. Según el criterio, el resultado es
  **"corrimiento no explicado por paralaje"**. Lo que hay es una zona fría extensa al SO, no una nube con
  la forma de la huella movida unos pocos kilómetros. Corrige lo dicho más arriba: la nube fría no queda
  "al lado" de la huella como un objeto propio, sino que la huella está en el borde de algo más grande.
- H4 no se reabre ni para este episodio.

### 3.2 Tercera tanda (19-11): H3 (cielo modelado y β con C10) y H7 (seguimiento)

Criterios escritos y commiteados antes del primer número, informes completos, salidas crudas y
scripts en `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\Goes\docs\own_volcat\h3_h7\`
(`criterio_H3_cielo_modelado_2026-11-19.md`, `criterio_H7_seguimiento_2026-11-19.md`,
`INFORME_H3.md`, `INFORME_H7.md`, `h3_resultado.txt`, `h7_resultado.txt`, `scripts_h3\`, `scripts_h7\`).

**H3, la física.** VOLCAT no pregunta "¿la BTD es negativa?", sino "¿cuánto de la radiancia que debería
llegar del suelo despejado falta, y en qué proporción entre bandas?". Eso es la emisividad efectiva ε
contra un cielo despejado calculado, y las razones β entre bandas. Una pluma tibia y semitransparente
podría tener BTD positiva y aun así un β de ceniza. Para que eso funcione hace falta un cielo despejado
calculado con error menor que la señal: ε(11) = 0,02, la primera compuerta de VOLCAT, equivale a 0,7 a
1,0 K de BT11, mientras la literatura da 4 a 5 K de error del cielo modelado sobre tierra (Heidinger y
Pavolonis 2009; ATBD GOES-R VolAsh, Tabla 12), y SECO Part 1 §4.2 corrige la ε negativa sobre tierra
con un sesgo de BTD.

**H3, método.** No hay RTM en el repositorio, RTTOV pide registro, CRTM y PFAAST (el modelo de SECO)
piden compilar Fortran y CAMEL (emisividad de superficie) pide cuenta Earthdata. Se hizo un cálculo
línea por línea propio en Python, sin cuenta ni compilación: líneas HITRAN (HAPI 1.3: H2O, CO2, O3,
N2O, CH4), continuo de vapor de agua MT_CKD 4.3 (AER), funciones de respuesta espectral del ABI de
GOES-19 (reproducen el Planck de los coeficientes L1b a ≤ 0,004 K), perfil GFS 0,25° por píxel y
emisividad de superficie fija declarada. Se agregó C10 (7,3 µm) a la ventana. Casos: 28-10 22:40 a
23:40 UTC, 29-10 01:00 a 01:20 UTC (noche cerrada) y 14-11 (de día); 37 pares con control del mismo
lugar y minuto en un día sin pluma, elegido por BT11 (dos cuadros del 14-11 quedaron sin control por
diferencia > 3 K); 458 píxeles de huella.

**Error del modelo** (observado menos modelo, 2.200 píxeles despejados de los controles, medido antes
de mirar la huella): sesgo −0,48 / +0,63 / −0,29 / −0,14 K y dispersión 2,1 / 6,9 / 7,6 / 7,3 K en
C10 / C11 / C14 / C15. De noche la dispersión en C14 baja a 2,4 K; de día sube a 8,2 K. Bajar la
emisividad de superficie en 0,03 enfría el modelo 1,75 K en C14. El sesgo cumple el criterio (≤ 3 K);
la dispersión es la de la literatura.

| Cielo despejado | G huella | G control | AUC ε(11) | AUC β(12/11) | AUC β(8,5/11) | AUC β(7,3/11) |
|---|---|---|---|---|---|---|
| M, modelado (agrupado) | 0,902 | 0,876 | 0,541 | 0,387 | 0,452 | 0,536 |
| E, empírico (agrupado) | 0,035 | 0,009 | 0,483 | no medible | no medible | no medible |

G = fracción de píxeles que pasan la compuerta ε(11) ≥ 0,02. AUC = probabilidad de que un píxel de
huella supere al mismo píxel en el control. Con E, menos de 20 píxeles pasan la compuerta y los β no se
pueden medir.

- **Veredicto según el criterio: no concluyente.** No se sostiene (G huella − G control = +0,026, se
  pedía ≥ 0,25). No se falsa por (a) (G huella = 0,90) ni por (b), porque β(12/11) queda con
  |AUC − 0,5| = 0,113, apenas sobre el 0,10 del criterio; apunta hacia "más ceniza" en los tres casos
  (0,46, 0,30 y 0,38), con medianas casi iguales (0,86 contra 0,88).
- **Lectura física.** Con el cielo modelado, la compuerta pasa en el 90 % de la huella y en el 88 % del
  mismo lugar en un día sin pluma. Diagnóstico posterior a las tablas (no decide): en los controles, sobre
  la huella, el modelo queda 7,07 K más tibio que lo observado en C14, porque el GFS pone ese terreno a
  1.737 m de mediana contra unos 3.200 m de la cumbre. Un cielo modelado con terreno grueso hace que la
  cumbre parezca siempre cubierta por una nube tenue. La comparación huella contra anillo vecino en la
  misma escena (secundaria) da AUC ε(11) = 0,84 con el modelo y 0,52 sin él: lo que separa ahí es el
  terreno, no la pluma.
- **Atribución (paso 4).** Ninguna de las dos formas separa la huella del control: ni el modelo ni las
  razones β. Con el cielo empírico la compuerta casi no deja pasar la pluma (3,5 %).
- **Indicio sin validar.** β(7,3/11), la banda de vapor de agua, sale más alta en la huella en los dos
  casos nocturnos de octubre (AUC 0,91 el 28-10 y 0,74 el 29-10) y no de día (0,41 el 14-11). Coincide
  con lo que haría el vapor o el SO₂ de una pluma a 7,3 µm, pero las medianas de β(7,3/11) son cercanas a
  cero o negativas (el modelo de C10 queda más frío que lo observado), son 106 píxeles de un solo episodio
  y la lectura es posterior al criterio. Sirve para escribir el criterio de una prueba nueva, no como
  resultado.
- **Para `detect_ash_enhanced`: no se propone ningún cambio.** H3 no se sostuvo, y llevar un RTM a la
  app costaría una tabla de consulta de ~184 MB, descargas GFS por escena y un error de terreno que hoy
  haría saltar la compuerta en todas las cumbres.

**H7, la física y el método.** El ATBD VOLCAT v1.0 (Pavolonis et al., enero 2025, §2.2) describe un
seguidor que lleva cada nube de un cuadro al siguiente "desde la emisión hasta la disipación", un segundo
detector por crecimiento de nube (Pavolonis et al. 2018) y umbrales que dependen del calor en el cráter.
Si los cuadros sin señal IR fueran sólo continuación de un objeto detectado antes con señal, nuestro
detector no tendría por qué verlos. Se revisó cuadro por cuadro si el primer cuadro de cada tramo tenía
señal propia: (a) BTD < −1 K en la huella, (b) hot spot FDCF a ≤ 10 km del cráter en ese scan o en los
dos anteriores, (c) al menos 2 píxeles a ≤ 10 km con BT11 2 K más fría que 10 min antes.

| Episodio | Primer cuadro del tramo | ¿Señal propia? | Cuadros anclados | Sin señal | Sin señal con antecesor |
|---|---|---|---|---|---|
| 28-10 | 19:20 UTC | no | 15 | 9 | 9 |
| 10-11 | 15:00 UTC | no | 12 | 5 | 2 |
| 14-11 | 16:40 UTC | no | 33 | 9 | 8 |
| Total | 0 de 3 con señal | | 60 | 23 | 19 (83 %) |

- **Veredicto según el criterio: H7 se falsa.** El primer cuadro no tiene señal en 3 de 3 episodios (la
  regla pedía 2). VOLCAT sí sigue los objetos de un cuadro a otro, pero el cuadro con que parte cada
  tramo tampoco tiene señal en nuestros datos.
- Hot spot FDCF: 0 % en los cuadros anclados y 0 % en los 465 scans sin objeto de esos días. El calor
  del cráter que ve el FDCF no es lo que dispara VOLCAT aquí.
- BTD mínima en las huellas de los tres episodios: −0,73 K (28-10 22:50 UTC). Ningún cuadro llega a −1 K.
- El enfriamiento rápido (c) aparece también en el 19 al 61 % de los scans sin objeto; quitarlo no cambia
  el veredicto.
- Desviación declarada: el tramo del 28-10 empieza antes de la ventana del criterio (el cuadro de 21:30
  ya tenía objeto anclado y el de 21:40 no se publicó), así que el primer cuadro es el de 19:20. Con
  18:30, 19:00 o 21:50 como primer cuadro el resultado es el mismo.

**Contexto oficial (REAV SERNAGEOMIN, leído por la sesión que encargó esto).** El 28-10 hubo columnas de
1.320 a 2.440 m sobre el cráter, desviadas hacia el NW; el 10-11, de 2.340 a 2.400 m desde las 21:54 UTC.
La huella VOLCAT del 28-10 que se midió deriva al SE (§3.1). Queda anotado como discrepancia por
revisar, sin conclusión.

### 3.3 Cuarta tanda (19-11, tarde): β(7,3/11) fuera de muestra y prueba tolerante del VAAC de Londres

Dos pruebas, cada una con su criterio commiteado antes del primer número. Informes completos en el
repositorio: `docs/own_volcat/beta73/INFORME_beta73.md` y `docs/own_volcat/vaac_londres/INFORME.md`.

**β(7,3/11), la física.** La banda C10 (7,3 µm) absorbe vapor de agua y SO₂, que una pluma de Chillán
lleva a una altura donde el GFS no los pone; si la pluma está, C10 debería caer más que C14 respecto de
su cielo despejado. Pero C10 es ante todo un sensor de humedad de la troposfera media: un día húmedo la
enfría en toda la escena. Por eso el criterio exigió que el efecto estuviera en la huella VOLCAT y no en
el anillo de 2 a 6 píxeles que la rodea, sin ceniza, en la misma escena.

**β(7,3/11), método.** Todos los cuadros VOLCAT anclados al cráter del 20-10 al 19-11, excluidos el 28 y
el 29-10 (donde nació el indicio) y el 16-11 (manto). Control pareado por BT11 en un día sin pluma.
49 pares: 7 de noche o crepúsculo en 3 días (22-10, 10-11 y 14-11) y 42 de día en 7 días.

| Estrato | Pares (días) | AUC huella [IC 95 %] | AUC anillo sin ceniza | Veredicto |
|---|---|---|---|---|
| Noche y crepúsculo (decide) | 7 (3) | 0,82 [0,62; 0,97] | 0,90 | No concluyente: el anillo separa más que la huella y sólo 1 de 3 días va a favor |
| Día (extensión) | 42 (7) | 0,41 [0,15; 0,63] | 0,49 | Se falsa |

- El cielo modelado como sensibilidad da lo mismo.
- Diagnóstico posterior (no decide): la noche positiva del 10-11 tenía tres veces más vapor sobre
  600 hPa que la de control según el GFS, y C10 cae igual a 40 km de la pluma. En los 49 pares, la
  diferencia de humedad del GFS y BT10 − BT14 lejos de la huella tienen ρ = −0,58.
- **Lectura:** el indicio de octubre era humedad del día, no pluma. β(7,3/11) queda descartada como señal
  de estas plumas, y con ella la última vía abierta de H3.

**VAAC de Londres, la física.** El London VAAC (Francis et al. 2012; umbrales leídos en Falconieri et al.
2018, §3.2) acepta como ceniza tentativa una BTD positiva de hasta +1,5 K si la banda de 8,7 µm la
compensa: (BT10,8 − BT12) + (BT10,8 − BT8,7) < +1,5 K. Después filtra con razones β y coherencia 3 × 3.
Es la prueba publicada más tolerante a una pluma tibia, que es justo lo que tiene Chillán.

**VAAC de Londres, método.** Doce configuraciones declaradas antes de medir; decide el método completo
con 10,8 µm = C14 y T_ref 255 K, con la misma vara del detector de plumas débiles del 17-11 (35 cuadros
de prueba, 120 scans sin pluma, el 16-11 como caso de manto). 1.204 scans de C13 bajados para las
variantes.

- **Método completo: no cumple.** 2 de 35 cuadros (contra el 50 % pedido), 0 de 82 píxeles dentro de la
  huella y 3 de 120 falsas alarmas (2,5 % contra 2 %). Las dos "detecciones" son un sistema nuboso que
  pasa por el cráter, sin un solo píxel en la huella VOLCAT.
- **Ninguna de las 12 configuraciones cumple.** La más cercana (C13 conservando los píxeles sin β medible)
  ve 3 de 35 cuadros.
- **Sin filtros, la suma sí se mueve:** baja ~0,4 K dentro de la pluma, sobre todo por el 8,4 µm, y
  contra el control pareado marca 21 % de la huella y 8 % del mismo lugar sin pluma. Es de las pocas
  señales IR por píxel de esta serie que separa algo la huella del lugar. Pero dispara en 51 a 63 % de
  los scans sin pluma, porque la nieve y las nubes ya ponen la suma bajo +1,5 K. El filtro β no puede
  confirmar una pluma tan tibia como el cielo despejado, y la coherencia 3 × 3 borra huellas de pocos
  píxeles.
- **Lectura:** la pluma deja una huella débil en 8,4 µm que la prueba tolerante alcanza a tocar, pero no
  basta para separarla de la nieve y las nubes sin un criterio de lugar y tiempo como el de VOLCAT.
- **Corrección del alcance (20-11).** Al leer el original de Francis et al. 2012 (p. 3, ec. 3, comprobado
  en la imagen del PDF), su Test 3 no es la ventana −2,0 ≤ BTD ≤ −0,7 K de Falconieri 2018 que se probó
  aquí, sino BT10,8 − BT12,0 < **+0,7 K** y BT10,8 − BT12,0 < BTD_clr − 1,0 K, con BTD_clr de un cielo
  despejado modelado (NWP + RTTOV). El "no cumple" de esta prueba vale para la versión de Falconieri. El
  Test 3 original no se ha probado (paso 16 del §6); ojo que depende del mismo cielo modelado que falla en la
  cumbre de día (§3.5).

### 3.4 Quinta tanda (19-11, noche): calor a 3,9 µm, rayos GLM (H9) y dirección de la pluma (H10)

Dos pruebas, cada una con su criterio commiteado antes del primer número. Informes completos:
`docs/own_volcat/calor_rayos/INFORME.md` y `docs/own_volcat/direccion_pluma/INFORME.md`.

**H9, la física.** Según la presentación CDR de VOLCAT de 2022 (diapositivas 82 y 83, leídas por un agente,
no verificadas aquí) y el ATBD v1.0 §2.2, VOLCAT afloja sus umbrales cuando ve actividad térmica intensa o
rayos en un volcán. Un cráter con material incandescente subpíxel sube mucho más la BT de 3,9 µm que la de
11 µm, así que la señal es BT7 − BT14 en el cráter menos la de un anillo de fondo, con la noche como estrato
que decide (de día C07 lleva reflexión solar). Antuco y Longaví sirven de volcanes de control. Las pruebas
anteriores sólo miraron los hot spots FDCF, que son demasiado gruesos para esto.

| Parte | Resultado | Veredicto |
|---|---|---|
| Calor en el momento del cuadro, noche (decide) | AUC 0,46 [0,20; 0,64], 16 cuadros con pluma en 3 días; Antuco 0,34, Longaví 0,37 | Se falsa |
| Calor en el momento del cuadro, día | AUC 0,61 [0,44; 0,78]; Antuco 0,56, Longaví 0,58 | Se falsa: el efecto aparece igual en los controles |
| Calor de fondo | 71 % de 346 cuadros nocturnos despejados de Chillán sobre el p99 de los controles (5,56 K), contra 2 % y 0 %; encendido desde el 24-10 | El cráter está caliente casi siempre |
| Arranque de los tramos de VOLCAT | 1 de 7 tramos con subida de calor en la hora previa, contra 17 % de tasa base | No coinciden |
| Rayos GLM a ≤ 30 km | 0 de 100 cuadros con pluma, contra 8,8 % de los controles pareados | Se falsa |

- La serie GLM de Lightning-v1 se contrastó contra el GLM-L2-LCFA de NOAA en dos horas: 26 de 26
  destellos a ≤ 30 km coinciden.
- **Lectura:** el calor del cráter, que coincide con la colada activa que informa el RAV, puede tener a
  Chillán en la lista de volcanes activos de VOLCAT todo el periodo y explicar un trato especial
  permanente, pero no cuándo aparece la pluma. Un "modo volcán activo" gatillado por calor no le sirve a
  nuestro detector de ceniza: en Chillán estaría siempre encendido y no hay señal espectral que aflojar.
  Sí deja un indicador térmico propio a 3,9 µm que el FDCF no ve, candidato a capa térmica aparte.

**H10, la física.** Todas las pruebas anteriores midieron dentro de la huella VOLCAT. Si la huella no está
donde estuvo la pluma, midieron píxeles sin pluma. El REAV del 28-10 informa columnas desviadas al NO y la
huella de ese día deriva al S. Una pluma de 1 a 2,5 km sobre el cráter queda entre ~4,5 y ~5,7 km s.n.m.
y la lleva el viento de ese nivel; el paralaje de GOES-19 corre su imagen hacia el S y algo al E.

| Jornada | Dirección REAV | Viento GFS | Huella VOLCAT (sin / con paralaje) | Resultado |
|---|---|---|---|---|
| 25-10 | SE (135°) | 136° | 181° / 182°, 5 escenas | Diferencia de 45 a 47°: borde del criterio, no concluyente |
| 27-10 | N a NO | 3 a 17° | sin objeto anclado en 42 cuadros | Sin escenas |
| 28-10 tarde | NO (315°) | 2° | 172° / 168°, 1 escena | Discrepa, pero con una sola escena |
| 28-10 anochecer y 10-11 | sin dirección | 18° y 42° | SE y E | La huella se aparta del viento entre 24 y 115° |

- El GFS reproduce la dirección del REAV en 6 de 7 horas con viento definido.
- Señal en el sector hacia donde el REAV dice que fue la pluma, contra control pareado por BT11: AUC de la
  BTD 0,68 (25-10) y 0,70 (27-10), sector opuesto 0,56 a 0,57; ningún píxel con BTD < −1 K. Bajo el umbral
  del criterio por menos de 0,02.
- Desviación declarada: 726 escenas L1b no se alcanzaron a bajar (S3 lento); la prueba de señal usó las
  que ya estaban en disco.
- **Lectura:** no queda probado que las pruebas anteriores midieran en el lugar equivocado. Que la huella
  quede casi siempre entre el S y el E del cráter coincide con el sentido del paralaje, y la corrección
  depende de la altura que se suponga para la pluma; no se lee como "VOLCAT ignora el viento". Llama la
  atención que VOLCAT no dibujara nada el 27-10, con columnas documentadas por el OVDAS.

### 3.5 Sexta tanda (20-11): H11 (terreno, filas de volcán y SO₂) y SECO propio entrenado con VOLCAT

Dos pruebas con criterio commiteado antes del primer número, más la lectura entera de la presentación CDR de
VOLCAT de 2022. Informes completos: `docs/own_volcat/reproducir_volcat/INFORME_H11.md`,
`docs/own_volcat/reproducir_volcat/INFORME_E2.md` y `docs/own_volcat/reproducir_volcat/LECTURA_CDR_2022.md`.

**H11, la física.** VOLCAT calcula cómo se vería cada píxel sin nubes con la temperatura de superficie del
GFS y un modelo radiativo, y ninguna fuente pública dice que corrija el terreno (SECO Parte 1 §4.1, CDR 2022,
ATBD 2025; tampoco Pavolonis et al. 2013 ni la máscara de nubes de Heidinger et al. 2012, que probó una
categoría de superficie de montaña y la descartó). El GFS pone la cumbre de Chillán a 1,5 a 1,9 km y no a
~3,2 km, así que su cielo despejado sale demasiado tibio sobre el cráter. H11 sumaba tres piezas: ese error
pone el cráter "confiadamente nublado" (bandera CF = 3 de SECO Parte 2 §4.3); las filas de volcán de la
Tabla 4 de SECO Parte 2 aceptan entonces objetos de 0 a 25 píxeles; y un atajo para SO₂ (ec. A5) deja
entrar los píxeles.

**H11, método.** 66 pares de H3 y β73 (huella VOLCAT contra el mismo minuto en un día sin pluma, pareado por
BT11), 10 días, 733 píxeles de huella, 14 pares de noche o crepúsculo. El modelo radiativo de H3 sin cambiar
su física, extendido para dar la radiancia de una nube negra en cada nivel (SECO Parte 1, ec. 1 a 3).

| Señal | Resultado | Lectura |
|---|---|---|
| Bandera CF ≥ 3, agrupado (decide) | 0,62 con pluma, 0,66 sin pluma | Ni sostiene (pedía ≥ 0,80 en ambos) ni falsa (pedía < 0,50 con pluma) |
| Bandera CF ≥ 3, de día (52 pares, 7 días) | 0,71 con pluma, 0,83 sin pluma | El error de terreno basta para la bandera, con o sin pluma |
| Bandera CF ≥ 3, de noche (14 pares, 5 días) | 0,29 con pluma, 0,00 sin pluma | El error baja a ~3 K y la bandera ya no pasa sola |
| Atajo de SO₂ (A5) | 0 de 733 píxeles, con pluma y sin pluma | βtot(7,3/11) queda cerca de 0,15, lejos del 1,0 que pide |
| Firma de ceniza βtot(12/11) | AUC 0,58 [0,54; 0,64], anillo 0,51 | Se corre apenas hacia la ceniza; no separa |
| βtot(8,5/11) | Mediana 0,99 contra 1,01, AUC 0,45 | Nada |

- **Veredicto según el criterio: no concluyente.**
- Lo que dice la literatura sobre el atajo de SO₂ calza con el cero: con 150 DU a 600 hPa el SO₂ cambia la
  banda de 7,3 µm (canal 28 de MODIS) sólo ~1,2 K en una atmósfera de latitud media, y con 15 DU cerca de un
  sexto de eso (Doutriaux-Boucher y Dubuisson 2009, Tabla 2 y §4.5), y el
  método de 7,3 µm de Watson et al. 2004 pide SO₂ bien sobre ~3 km y falla cerca del cráter.
- **Lectura:** la pieza del terreno es real de día y explica que la bandera no estorbe a VOLCAT en el cráter;
  la del SO₂ no aparece. Ninguna compuerta espectral pública separa la pluma del mismo lugar sin pluma.

**Etapa 2, la idea.** Si lo público de SECO no alcanza, armar un SECO casero completo (emisividad y razones β
contra el cielo modelado, prefiltros, probabilidad por Bayes ingenuo con los tres clasificadores que ABI
tiene siempre, objetos, bandera de nube, robustez y Tabla 4) y entrenar la única parte que VOLCAT no
publica, la probabilidad por píxel, usando las propias detecciones VOLCAT de Chillán como etiqueta. Si así
tampoco llega, la diferencia no está en las variables que podemos calcular.

**Etapa 2, método.** 795 scans: 100 cuadros VOLCAT anclados al cráter en 10 jornadas, 655 scans sin pluma y
40 del manto del 16-11. Cada jornada se juzga con un modelo entrenado sin ella.

| Medida | SECO propio (decide) | Bosque aleatorio (informativo) | Pedido |
|---|---|---|---|
| Cuadros VOLCAT reproducidos | 0 de 100 | 38 de 100 | ≥ 50 % |
| Falsas alarmas | 0 de 655 | 28 de 655 (4,3 %), 15 en una jornada | ≤ 2 % y ≤ 3 por jornada |
| Manto del 16-11 | 0 de 40 | 0 de 40 | ≤ 10 % |

- **Veredicto: no cumple.**
- Diagnóstico posterior (no decide): en los 100 cuadros con pluma hay objeto en el cráter, y en el 73 % la
  bandera ya vale 3; pero la probabilidad de ceniza del objeto tiene mediana 1,6 % y máximo 34 %, contra el
  80 % de la Tabla 4. Con el prior de SECO (0,1 %), llegar a 80 % pide que la evidencia sea unas 4.000 veces
  más probable con ceniza que sin ella; nuestras variables, entrenadas con las mismas plumas, llegan a unas
  16 veces en la mediana.
- **Lectura:** las variables públicas no separan la pluma de Chillán del cráter sin pluma, igual que en H3,
  β73 y H11. Que VOLCAT sí la publique implica que sus tablas de probabilidad (entrenadas con 344 escenas
  MODIS de ceniza y polvo, no con Chillán) le dan a estos estados espectrales mucho más peso del que
  justifican los datos de Chillán, o que decide con algo que no está en SECO 2015: la CDR 2022 (diapositiva
  80) nombra la dimensión temporal como lo que permite detectar emisiones de "muy pocos píxeles". El
  bosque aleatorio marca el techo de nuestras variables: ve más de un tercio de los cuadros, pero con
  demasiadas falsas alarmas para una capa operativa.

### 3.6 Séptima tanda (20-11, noche): H12 (Test 3 original de Francis 2012) y H13 (cambio entre cuadros)

Dos pruebas en paralelo, cada una con su criterio subido a GitHub antes de medir (21:01 y 21:02 UTC; los
resultados, desde las 22:38 UTC) y sin cambios después. Informes completos:
`docs/own_volcat/reproducir_volcat/INFORME_H12.md` y `docs/own_volcat/temporal_h13/INFORME_H13.md`.

**H12, la física.** El Test 3 de Francis, Cooke y Saunders 2012 (ec. 3, p. 3, leído en la imagen de la
página) marca ceniza tentativa si BTD = BT10,8 − BT12,0 < +0,7 K **y** BTD < BTD_clr − 1,0 K, con el cielo
despejado de un modelo numérico. La segunda condición corrige el vapor: el cielo húmedo ya da BTD positiva y
una capa con firma de ceniza la baja. Admite BTD positivas, el tramo donde cae la huella de Chillán (−0,6 a
+0,5 K). La prueba del 19-11 (§3.3) había seguido el resumen de Falconieri 2018, que cambia el signo del
umbral. Riesgo dicho antes de medir: si el GFS pone la cumbre baja, BTD_clr sale inflada y la segunda
condición se cumple sin pluma; por eso la prueba llevó un control de terreno, la misma huella trasladada a
Antuco y Nevado de Longaví en las mismas escenas, y el llano como referencia.

**H12, método.** Los 66 pares de H11 deciden (733 píxeles, 10 días, cielo despejado directo por píxel); los
pares nuevos sobre las escenas de la etapa 2 replican. Margen continuo para el AUC y fracción de cuadros con
al menos un píxel T3.

| Lugar (conjunto A, medianas) | Altura GFS | BT11 despejado − observado | BTD_clr − BTD | T3 en cuadros |
|---|---|---|---|---|
| Huella con pluma | 1.727 m | +8,3 K | +0,85 K | 0,76 |
| Mismo lugar sin pluma | 1.727 m | +6,9 K | +0,61 K | 0,52 |
| Cumbres de Antuco y Longaví | 1.696 m | +2,1 K | +0,32 K | 0,35 |
| Llano | 216 m | −0,6 K | 0,00 K | 0,03 |

- AUC del margen 0,58 [0,54; 0,71], anillo 0,49; de día los cuadros pasan 0,87 con pluma y 0,64 sin pluma,
  de noche 0,36 y 0,07. El filtro β de la ec. 5 y la regla 6 de 9 no lo arreglan, y ningún píxel llega al
  Test 1 (BTD < −2 K).
- **Veredicto según el criterio: no concluyente.** No separa (pedía AUC ≥ 0,70 y 0,30 de diferencia en
  cuadros), y la falsación por terreno pedía que disparara en ≥ 50 % de las cumbres, que dieron 35 %.
- **Lectura:** la brecha que el test exige sobre 1 K ya es ~0,6 K sin pluma en el cráter y la pluma agrega
  ~0,25 K; pasar o no depende del error del modelo de ese día. Las cumbres de control tuvieron la misma altura
  GFS que Chillán pero un error de BT11 de 2 a 3 K, no de 8 a 9 K: el error no lo pone la altura del GFS sola,
  sino algo propio del macizo de Chillán (forma y extensión, nieve o gas permanente, sin medir). Un control de
  terreno nuevo tendría que elegir cumbres por su error de BT11, no por su altura.

**H13, la idea.** La CDR 2022 (diapositiva 80) nombra la dimensión temporal para emisiones de muy pocos
píxeles, y la tesis de Pavolonis 2014 la deja como trabajo futuro para plumas sin contraste con el cielo
despejado. Si el cráter sin pluma tiene una firma propia y estable, restar el cuadro anterior debería
borrarla y dejar sólo lo que cambió: una pluma que sale enfría el 11 µm, sube la emisividad y mueve las β.

**H13, método.** Secuencias completas de 10 min de los 12 tramos con pluma anclada (de una hora antes a una
hora después) y 30 min de historia de los días candidatos a control: 1.527 escenas. 18 variables por píxel
(cambio contra el cuadro anterior, contra la mediana de los tres anteriores y persistencia del signo, para
BT11, BTD, ε(11), β(12/11), β(8,5/11) y β(7,3/11)). 72 pares huella contra el mismo píxel y minuto en un día
sin pluma pareado por BT11, 9 jornadas, 865 píxeles.

- Mejor variable: AUC 0,582 (cambio de BT11 y de ε(11) contra la mediana de los tres anteriores), anillo
  0,54 a 0,55; ninguna cumple la condición del anillo. Con el pareo hecho 30 min antes, máximo 0,52.
- BT11 baja 0,43 K con pluma y 0,29 K sin pluma en 30 min (medianas); ε(11) cambia menos de 0,005 en ambos.
- **Veredicto según el criterio: se falsa** (ninguna de las 18 llega a 0,60).
- **Lectura:** la diferencia entre cuadros hereda lo que un cuadro no tiene. Con ABI a 2 km y cada 10 min,
  estas plumas no dejan señal propia ni quieta ni en movimiento. De paso: en 23 de los 26 cuadros sin control,
  **todos** los días candidatos estaban de 3 a 10 K más fríos en la cumbre; los cuadros con pluma VOLCAT caen
  en condiciones más tibias que los días sin pluma a la misma hora. No se midió si es cielo más despejado o
  suelo más tibio.
- El bosque aleatorio informativo (etapa 2 más las variables temporales) quedó sin correr: se detuvo tras 2
  pliegues por memoria y disco. No cambia el veredicto.

### 3.7 Octava tanda (21-11): lo público de VOLCAT (H14, C2, C2b y H15)

Plan: `docs/own_volcat/PLAN_2026-11-21_LUT_VOLCAT.md`. Búsqueda del 20-11 que lo originó: en
`https://bin.ssec.wisc.edu/pub/volcat/` hay archivos de evento por volcán (retención ~7 días, con cláusula de acceso
restringido; los 60 de Chillán se bajaron con el sí de Nicolás, sólo para uso interno y a reserva de autorización) y
el paquete auxiliar con las tablas y la configuración de VOLCAT para ABI. Informes:
`docs/own_volcat/eventos_h14/INFORME_H14.md`, `docs/own_volcat/mauna_loa_c2b/INFORME_C2_C2b.md` y
`docs/own_volcat/lut_h15/INFORME_H15.md`.

**H14, anatomía de los eventos.** 4 eventos (13-11 tipo `VCB`, 14-11 dos, 18-11 uno), 60 cuadros, 767 píxeles
publicados, mediana de 11 píxeles por cuadro. Firma de onda larga bajo 0,05 en el 99,35 % de los píxeles (máximo
0,42); 0 de 4 primeros cuadros con firma total ≥ 0,5 en la mayoría; sin núcleo con firma junto al cráter. La firma
total llega a 0,5 en el 12 % de los píxeles, sólo con sol y nunca de noche. **Veredicto: compatible con H14, sin
fuerza** (la regla pide ≥ 10 eventos). Georreferencia del 14-11: nuestra huella del PNG cae 1 fila al S y 1 columna
al E (IoU 0,19 sin corregir, 0,42 corregida).

**C2, modelo radiativo repuesto.** Los insumos perdidos (MT_CKD 4.3 y SRF de ABI) se bajaron de nuevo a
`D:\goes_cache\rt\`; el cielo despejado de H11 se reproduce con error 0,0 K (una mutación de la SRF da 7,24 K).

**C2b, cielo despejado de VOLCAT en Mauna Loa.** Según el criterio, **no concluyente**: esa noche Hawái estaba
nublado. Análisis posterior, sin usar la observación: dentro de una misma celda GFS de 0,5° el cielo despejado de
VOLCAT baja con la cota de cada píxel (−3,75 K/km agrupado); sobre el mar es constante. VOLCAT lleva la superficie a
la cota fina del terreno.

**H15, las tablas reales.** Etapa 1 (lectura): suficiente. Etapa 2 (validación contra la probabilidad por píxel de
VOLCAT en Mauna Loa): **no aprobada**; con los ε y β de VOLCAT κ 0,795 (pide 0,90), con los nuestros κ 0,245.
Diagnóstico posterior: sin la tabla εtot × BTD la probabilidad sale exacta con εtot ≥ 0,5 y falla bajo 0,5, y bajo
0,2 ningún píxel calza exacto; la huella de Chillán tiene εtot mediana 0,16. Nuestro εtot sale 0,05 más alto que el
de VOLCAT aun con su cielo despejado. Etapa 3 (Chillán): **no se ejecutó**, como manda la regla.

**Lectura.** Lo espectral de VOLCAT está identificado y es reproducible en nube espesa; lo que decide en Chillán no
es la firma del píxel, que VOLCAT mismo informa casi nula, sino el objeto y el seguimiento, más una regla de nube
tenue y un cielo despejado corregido que sólo el autor puede confirmar.

### 3.8 Novena tanda (21-11, noche): la etapa de objeto (H16)

Informe: `docs/own_volcat/h16_objeto/INFORME.md`. La probabilidad de OBJETO de VOLCAT se reprodujo con su tabla
pública y se validó contra Mauna Loa (error mediano 0,03 décadas en las odds, 97 % dentro de una década). En los 60
cuadros de Chillán la huella llega como máximo a 0,002 (VOLCAT pide 0,8): **no separa**. La tabla de desviación de
BT11 en 3 × 3 es la que más la hunde (la cumbre es térmicamente rugosa). Los archivos de evento dicen por dónde entra
Chillán: `ASHPLUMEPUFF` (49 de 60 cuadros) y `VCB` (11 de 60), no la selección básica de objeto; y tres de cuatro
eventos parten con actividad térmica VOLCAT de 10 MW o más (según el CDR 2022, el calor relaja los umbrales). Lo
público de VOLCAT (píxel y objeto) queda reproducido y no ve estas plumas; lo que falta es el clasificador de la
vía pluma/puff.

### 3.9 Décima a decimotercera tanda (22 y 23-11, S16 a S20): seguimiento, límite IR, verdad del OVDAS y primera firma (H17 a H29)

Cada prueba tiene su criterio commiteado antes de medir y su informe en `docs/own_volcat/<carpeta>/INFORME.md`.
Todas están en main (PR 100 a 107; H29 fusionado el 23-11 en S20, merge `7891563`).

| Prueba | Pregunta | Resultado | Carpeta |
|---|---|---|---|
| H17 | ¿Una regla propia (calor a 3,9 µm + pluma anclada) ve lo que VOLCAT? | **Falla.** Detecta 13 % de los cuadros con pluma con 7 % de falsas alarmas. Su "huella 1,3 K más tibia que el suelo" **no se sostiene**: la base tenía 62 % de cuadros nublados, y con base despejada la huella queda 0,81 K más fría, bajo el umbral de −1 K y sin separar (revisión S19e) | `h17_regla_propia/`, `revision_h13_h17_nube/` (PR 104) |
| H18 | ¿Las tablas de día de VOLCAT validan? | **No validan** contra Fuego 2018 (κ 0,002); las IR sí, de día y sobre tierra (κ 1,000) | `h18_modo_dia/` |
| Sitio | ¿Qué probabilidad publica VOLCAT en la huella? | **Baja**: de día 0 de 30 cuadros con P ≥ 20 %; alta sólo al atardecer del 14-11 | `sitio_volcat/` |
| H19 | ¿Se reproduce el paso de objeto en Fuego? | **En parte**: la P del objeto sí en píxel opaco; la pertenencia al objeto no (59,5 %) | `h19_objeto_fuego/` |
| H20a | ¿Qué son los campos de los archivos de evento? | P infrarroja de píxel < 0,05 en 762 de 767 píxeles de Chillán; la publicada sube sólo en 5 de 60 cuadros | `h20a_campos_evento/` |
| H20b, H20c | ¿Qué sube la P publicada en Kirishima? | **El seguimiento** (4 de 4 cuadros), desde "Temporal selection criteria met for ash" | `h20b_kirishima/`, `h20c_kirishima_luz/` |
| H21 | ¿El VAAC de Buenos Aires confirma las marcas de VOLCAT? | **No coincide**: 3 de 30 | `h21_vaac/` |
| H22 | ¿La pluma desprendida del 14-11 tiene señal IR lejos del cráter? | **Sin señal** a más de 30 km, con control positivo aprobado | `h22_pluma_desprendida/` |
| H23 | ¿Qué capa ve GOES-19 sobre la cumbre? | ε 0,15 a 5 km sí (AUC 0,91 a 0,95); a 3 km no. Chillán queda bajo el límite (sospecha, cota en parte circular) | `h23_inyeccion/` |
| H24 | ¿Los pulsos del OVDAS (REAV) dejan firma IR a favor del viento? | **No concluyente.** De mañana, sin firma con poder (incluida la explosión de 2 km, E6); de tarde, sin fondo | `h24_pulsos_reav/` |
| H25 | ¿E6 deja firma hacia donde soplaba el GFS (NNE)? | **Sin señal** (z +0,52; poder de capa 100 %); pluma angosta sin poder | `h25_e6_gfs/` |
| H26 | ¿Copiar la decisión de VOLCAT da sus píxeles? | **Sin poder** por la regla (control positivo 10 de 20); recupera 12 de 769 píxeles; 7,7 % de falsas alarmas | `h26_seguidor_volcat/` (PR 102) |
| H27 | ¿Un fondo de cumbres de control mide los pulsos de tarde? | **Inválido**: Chillán sin pluma es 1,54 veces más ruidoso que las cumbres; E12 z −2,44 sin poder | `h27_fondo_espacial/` (PR 101) |
| H28 | ¿Cuál es la regla de seguimiento de VOLCAT? | **Se sostiene en parte**: radio de 3 km por minuto exacto (3.969 de 3.969); el parecido propuesto no. Chillán: 56 de 60 continuaciones, 51 explicadas (**compatible**) | `h28_regla_seguimiento/` (PR 103) |
| H29 | ¿La pluma del 08-11 lejos del cráter (> 30 km, 17 píxeles-cuadro) tiene firma en 11 y 12 µm? | **SEÑAL por la regla** en la BTD pareada por BT11 y cota del mismo cuadro: −0,37 K, bajo los 17 días nulos y p 0,005 en 1.961 huellas corridas. Equivale a f·ε ≈ 0,12 (pluma tenue o angosta). Atribución a la pluma: SOSPECHA (bandas meteorológicas de igual amplitud esa tarde; la BTD baja empieza 50 min antes que VOLCAT en esas posiciones) | `h29_pluma_0811/` (PR 107) |
| S20b, prueba 1 | Con la huella de la pluma medida por Sentinel-2 (08-11 14:53) y Landsat 8 (25-10 14:34), llevada a la grilla ABI con su paralaje, ¿deja firma en el píxel de GOES-19? | **SEÑAL** los dos días en la BTD pareada (M1) y en la BT11 contra su anillo (M2), contra el mismo píxel en 6 días despejados y contra la huella corrida (p ≤ 0,012; ensayo en seco 0 de 6). La pluma llena 18 % (25-10) y 43 % (08-11) de un píxel; ese píxel queda 0,97 y 0,84 K más bajo en 11 − 12 µm y 3,8 y 7,3 K más frío que su anillo. El 08-11 calza con ceniza de ε11 ≈ 0,5. Post hoc: una capa gris no reproduce M1 (la firma es espectral), ningún otro día despejado deja el píxel tan bajo, y cumbres de igual cota tampoco (p ≤ 0,023). VOLCAT no dibujó la bocanada a las 14:40 ni a las 14:50; sí a las 15:00. Prueba 2 (ventana partida a 100 y 70 m) pendiente de credenciales | `s20b_verdad_alta_res/` |
| Revisión S20 de H29 | ¿La BTD baja se mueve con la huella de VOLCAT cuadro a cuadro? | Código propio: M1 se reproduce (−0,3725 K). Seguimiento: a > 30 km **no concluyente** (−0,23 K, p 0,095; potencia 1,0); a > 15 km, como sensibilidad, **sí sigue** (−0,48 K, p < 0,0001, 35 cuadros). Descarta una banda quieta; no separa ceniza de una nube que VOLCAT siga desde el cráter. Atribución: **SOSPECHA reforzada** | `revision_s20_h29/` |
| S20c | ¿Las pruebas pareadas viejas (paso 2, H3, β73, Londres, H13, H11/H12) salieron "sin firma" porque sus controles tenían pluma? | **SIN PODER** en H3, H13 y H11/H12; paso 2, β73 y Londres **inválidas** (nulo degenerado, decidido en seco). Antes de medir se vio la causa de MET-01: los días con VOLCAT son los despejados (ACMF de tarde: 57 a 67 % contra 4 a 7 % en días sin actividad) y el pozo limpio está 9 K más frío, así que la regla vieja no podía dar controles limpios. Con línea base limpia y placebo de días libres despejados, la BTD de la huella queda 0,23 a 0,42 K bajo el placebo en las seis, 0,15 a 0,25 K más que con el control viejo en las válidas (ε ≈ 0,13 a 0,16), pero p 0,054 a 0,072 con poder 0,06 a 0,16 a ε 0,10. Los controles viejos se comportan como positivos (huella contra anillo: p 0,001 en H3 y H11/H12). El cambio en 10 min (H13) sigue en el azar. Lectura: apunta a control contaminado, sin demostrarlo; el "sin firma" de esas pruebas no se lee como ausencia | `s20c_controles_limpios/` |
| S20d (prueba 2 de S20b) | Cuando el píxel resuelve la pluma (Landsat 8 a 100 m, 25-10 14:34; ECOSTRESS a 70 m), ¿tiene 11 − 12 µm negativa, firma de ceniza? | **SIN FIRMA por la regla** (T1 −3,3 K, p 0,003: la pluma se ve; T2 −0,09 K, p 0,23). **Artefacto del control, post hoc:** la máscara de reflectancia marca un tercio de la pluma y el núcleo se pareó con su propia cola no marcada; con el sector de la pluma fuera del control, T2 = −1,54 K (p 0 de 2.022) y el mismo lugar sin pluma el 17-10 da +0,23 K; en crudo, −2 a −3 K. La firma de GOES de la prueba 1 viene de la ceniza, no de la mezcla de superficies (falta confirmarlo con criterio previo). ECOSTRESS sin veredicto: 08-11 sobre la huella de VOLCAT, +0,20 K contra el 17-10 (máscara de 267 km², demasiado gruesa) | `s20b_verdad_alta_res/INFORME_S20d_prueba2.md` |
| S21a1 (repetición de S20d con el control escrito antes) | Con el control del pareo fuera de un sector fijo de ±45° alrededor del eje de la pluma (252,5°, del centroide de la máscara de reflectancia), de 2 a 15 km, ¿la pluma del 25-10 tiene 11 − 12 µm negativa a 100 m? | **FIRMA DE CENIZA por la regla, CONFIRMATORIA** (no independiente: por la regla de selección, ninguna otra pasada de Landsat entre el 15-09 y el 18-11 tuvo pluma sobre nieve con cumbre despejada, así que se repitió el 25-10). T1 −3,33 K (p 0,0035), T2 **−1,54 K** (p 0 de 1.985; nulo ±0,24 K), igual con erosión 2 (−1,52 K) y con el sector a 12 km. El mismo lugar sin pluma: 17-10 +0,23 K, 15-09 +0,04 K. La firma se mide en 107 de 283 celdas: el núcleo más frío no tiene pares fuera del camino de la pluma. Corrige S20d §3 (c): con su control post hoc T1 quedaba nulo y la regla habría dado NO CONCLUYENTE, no FIRMA | `s21a1_ventana_partida/` |
| S21b (bandas reflejadas) | ¿C02 (0,5 km), C05 (1,6 µm) y C06 (2,2 µm) separan del fondo la franja de Landsat del 25-10 14:34, y dejan rasgo los pulsos de la tarde del 28-10 (E10, E11, E12)? | **Prueba 1: SIN PODER** en las tres bandas (S 2,6 a 2,9 veces lo esperado, p 0,07 a 0,12; el nulo de toda la ventana se contaminó con nubes de los días base). Post hoc: a 1,6 µm la huella sube de 0,09 a 0,17 y baja a 0,12 en media hora el 25-10, con los días base planos: algo en el aire, no depósito. **Prueba 2: SIN SEÑAL en los tres pulsos, episodio NO CONCLUYENTE** (poder 0,03 a 0,05). Las tardes de control tienen cúmulos en la cumbre en 85 a 93 % de los pares: E1 no los ve | `s21b_reflejadas/` |

Lo que queda abierto: la puerta de nacimiento de VOLCAT (H28 §1), los pulsos de tarde con fondo propio (verano,
`h24_verano/REGISTRO_PROSPECTIVO.md`), una pluma angosta en E6 (H25), repetir H29 sin cambiar la regla en otro evento
con píxeles lejanos, repetir las pruebas pareadas con más días despejados en los dos lados (S20c quedó sin poder; el verano es la ocasión),
repetir la ventana partida a 100 m en otra pasada con pluma sobre nieve (S21a1 la confirmó sobre el 25-10 con el control escrito antes, pero no es independiente) y sumar pasadas finas como verdad periódica
(`HOJA_DE_RUTA_VERDAD_ALTA_RESOLUCION.md`).

**Los controles "sin pluma" de las pruebas pareadas eran, casi todos, días con actividad (MET-01, revisor de método de
S19i; cifras recontadas en S20 con scripts propios, todas exactas).** Controles en días que H24 excluye por actividad:
paso 2, 45 de 46; H3, 34 de 37; β73, 42 de 49; VAAC de Londres, 38 de 45; H13, 62 de 72. Trece controles del paso 2,
ocho de H3 y diez de Londres caen el 13-11 entre las 19:00 y las 21:00 UTC, dentro de una cadena que VOLCAT publicó.
El efecto es **parcial**: en el paso 2, H3 y Londres el control tiene además un objeto de VOLCAT cerca (contaminación
directa); β73 y H13 eligen controles sin VOLCAT a ± 60 min, así que su contaminación es sólo "día con actividad". La
causa es el pareo por BT11: los días sin actividad de noviembre estaban 8 a 9 K más fríos (mediana del mejor candidato
libre), así que no había alternativa dentro de 3 K. Consecuencia: los "sin firma" del paso 2, H3, Londres y de las que
heredan sus pares (H11, H12) compararon pluma contra un volcán que también emitía, y no pueden leerse como ausencia de
firma. La prueba que lo resuelve sin bajar nada: repetir las variables de 11 y 12 µm con controles del 21-09 al 23-10
(cubos de H23 en `D:\goes_notas\s17\h23\`), con criterio antes de medir.
**Hecho en S20c** (`s20c_controles_limpios/INFORME.md`): la regla de pareo no admite controles limpios (el pozo de
septiembre y octubre está 9 K más frío y los días sin actividad casi nunca están despejados de tarde); con línea base
limpia y placebo, la diferencia crece hacia la ceniza en las seis pruebas y los controles viejos se parecen a los
positivos, pero sin poder para afirmarlo con la regla escrita (p 0,054 a 0,072; tres pruebas inválidas por nulo degenerado).

**Revisión de las líneas base contra la máscara de nubes (S19e, PR 104).** H13 sigue en pie: con sólo pares
despejados en los ocho cuadros (30 pares), la mejor de 18 variables da AUC 0,604, lo que da el azar. H17 se debilita
en su física, no en su veredicto: la huella no está más tibia que el suelo despejado, sino 0,81 K más fría, y eso no
alcanza para separarla del resto del cuadro (POD 0,19, FAR 0,07). Toda cita de "la huella 1,3 K más tibia" en
informes anteriores queda superada por esta revisión.

## 4. Hipótesis ordenadas por evidencia

| # | Hipótesis | A favor | En contra o abierto | Qué la falsaría con datos que ya hay o casi |
|---|---|---|---|---|
| H1 | ~~VOLCAT ve estas plumas por los canales solares de día~~ **Falsada el 18-11** | SECO los usa con ABI; las 58 detecciones de noviembre eran de día | Paso 4: el 29-10 VOLCAT sigue una pluma anclada al cráter de noche (3 cuadros seguidos, cenit 110 a 113°) sin señal IR en la huella. Paso 2: los canales solares no separan la huella del control pareado (AUC 0,50) | Hecho (§3.1) |
| H2 | **El trato especial al cráter** (objetos de 0 a 25 píxeles aceptados a menos de 5, 10 o 50 km de un volcán) deja pasar objetos que en otra parte se descartarían | SECO Part 2 Tabla 4; los objetos de Chillán son chicos (mediana 10 px del PNG) y todos anclados al cráter | Paso 3 no concluyente (R = 3,2, dominado por el 16-11); sin el 16-11, VOLCAT publica objetos chicos lejos de volcanes (R = 0,52), probablemente polvo de Cuyo con señal IR propia | Sigue abierta. 20-11 (§3.5, H11): de día el error de terreno ya pone el cráter en CF = 3 con o sin pluma, así que la fila de volcán no estorba; lo que falta es la probabilidad > 80 %, que con las variables públicas no se alcanza (E2) |
| H3 | El **fondo modelado** (cielo despejado con GFS y modelo radiativo) y las razones β, incluida β(7,3/11), bastan para ver la pluma en el IR | Es la diferencia de diseño más conocida; β(7,3/11) más alta en la huella en el episodio nocturno de octubre (AUC 0,91 y 0,74, indicio posterior al criterio) | 19-11 (§3.2): con cielo modelado la compuerta pasa igual en la huella y en el control (0,90 contra 0,88) porque el GFS pone la cumbre 1,5 km más abajo y el modelo queda ~7 K más tibio; con cielo empírico la huella casi no pasa (3,5 %); ningún β separa con |AUC − 0,5| ≥ 0,20 agrupado | **No concluyente según el criterio** (β(12/11) quedó a 0,013 del umbral de falsación); en la práctica no separa. 19-11 tarde (§3.3): β(7,3/11) fuera de muestra no se repite (noche no concluyente porque el anillo sin ceniza separa más, día falsado); el indicio era humedad del día. Queda cerrada en la práctica |
| H4 | La huella está **corrida por paralaje** y medimos en el lugar equivocado | Plausible en geometría (0,93 km por km de altura) | Noviembre: no hay señal fría en ningún corrimiento hasta 5 px. 28-10 (18-11): BTD < −1 K en ningún corrimiento; el frío de BT11 crece hacia el SO, no hacia donde predice el paralaje (1,1 filas al sur para 3,5 km) | Falsada, también en el episodio del 28-10 |
| H5 | La señal está en la **banda de 8,5 µm** | Es una banda que VOLCAT usa y el detector no probó en anomalía | Prueba B: AUC 0,26 | Falsada hoy, con la salvedad del nulo nublado |
| H6 | ~~Parte de lo que VOLCAT dibuja **no es ceniza**~~ **Cerrada el 19-11 por Nicolás (OVDAS)** | | "El volcán lleva muchos días con pulsos y columnas de gas y ceniza en cantidades variables" | Cerrada: VOLCAT dibuja ceniza real |
| H7 | VOLCAT **sigue** un objeto detectado antes con señal (seguidor kd-tree del ATBD 2025) y los cuadros sin señal son continuación | ATBD VOLCAT v1.0 §2.2; 19 de 23 cuadros sin señal tienen antecesor | 19-11 (§3.2): el primer cuadro de cada tramo tampoco tiene señal (0 de 3 episodios con BTD, hot spot FDCF o enfriamiento rápido) | **Falsada el 19-11** |
| H8 | Una prueba espectral **más tolerante** que la nuestra (la del VAAC de Londres, que acepta BTD positiva compensada por 8,7 µm) alcanza a ver la pluma | Francis et al. 2012; Falconieri et al. 2018; sin filtros marca 21 % de la huella contra 8 % del mismo lugar sin pluma | 19-11 tarde (§3.3): el método completo ve 2 de 35 cuadros y 0 píxeles en la huella; sin filtros dispara en 51 a 63 % de los scans sin pluma | **No cumple el 19-11, en la versión de Falconieri.** El Test 3 original de Francis 2012 se probó el 20-11 como H12: no concluyente |
| H11 | El **error de terreno** del cielo despejado de VOLCAT pone el cráter "confiadamente nublado" y, con las filas de volcán de SECO Parte 2 y el atajo de SO₂ (ec. A5), deja pasar las plumas chicas | Ninguna fuente pública corrige el terreno; el GFS pone la cumbre a 1,5 a 1,9 km | 20-11 (§3.5): de día CF ≥ 3 en 71 % con pluma y 83 % sin pluma; de noche 29 % y 0 %; A5 en 0 de 733 píxeles; βtot(12/11) AUC 0,58 | **No concluyente el 20-11**: el terreno explica la bandera de día, pero ninguna compuerta pública separa la pluma |
| E2 | Un **SECO propio** entrenado con VOLCAT como etiqueta reproduce sus detecciones de Chillán | Todo lo público de SECO es reproducible con ABI L1b y GFS | 20-11 (§3.5): 0 de 100 cuadros; probabilidad del objeto 1,6 % de mediana contra 80 % pedido | **No cumple el 20-11**: lo que decide está en las tablas de probabilidad no públicas o en un criterio temporal |
| H9 | El **calor en el cráter** (3,9 µm) o los **rayos GLM** aflojan los umbrales de VOLCAT y marcan cuándo dibuja | CDR 2022 diapositivas 82 y 83 (vía agente); el cráter está caliente el 71 % de las noches despejadas desde el 24-10 | 19-11 noche (§3.4): el calor no separa los cuadros con pluma (AUC 0,46 de noche) ni marca el arranque de los tramos; 0 de 100 cuadros con rayos | **Falsada como gatillo del momento el 19-11**; queda posible como trato especial permanente (volcán activo) |
| H10 | La huella VOLCAT **no está donde estuvo la pluma**, y las pruebas midieron en el lugar equivocado | REAV 28-10 al NO contra huella al S | 19-11 noche (§3.4): dos jornadas comparables, ambas en el borde o con una escena; la huella sigue el sentido del paralaje; en el sector del REAV la BTD tampoco pasa el umbral (AUC 0,68 y 0,70) | **No concluyente el 19-11** |
| H12 | El **Test 3 original** del VAAC de Londres (BTD < +0,7 K y BTD < BTD_clr − 1 K, Francis et al. 2012) admite las BTD positivas de Chillán y separa la pluma | Es la única compuerta publicada que admite BTD positivas; marca 76 % de los cuadros con pluma | 20-11 noche (§3.6): 52 % del mismo lugar sin pluma; AUC 0,58; sin pluma la brecha BTD_clr − BTD ya es 0,6 K y la pluma agrega ~0,25 K; las cumbres de control dieron 35 % pero con un error de BT11 de 2 a 3 K, no de 8 a 9 K | **No concluyente el 20-11**: no separa; el control de terreno no tuvo el error de Chillán |
| H13 | El **cambio entre cuadros** de 10 min resta la firma estable del cráter y deja la pluma | CDR 2022 (diapositiva 80); la tesis de Pavolonis 2014 lo propone como trabajo futuro | 20-11 noche (§3.6): mejor AUC 0,582 de 18 variables, anillo 0,54 a 0,55; con pareo 30 min antes, 0,52 | **Falsada el 20-11** |
| H14 | VOLCAT publica estas plumas **sin firma IR**: entran por reglas de objeto o por el detector de crecimiento (`VCB`), y su propio campo de firma lo declara | Archivos de evento VOLCAT de Chillán hallados el 20-11 en SSEC | 21-11 (`docs/own_volcat/eventos_h14/INFORME_H14.md`): 0 de 4 primeros cuadros con firma total ≥ 0,5 en la mayoría; firma de onda larga bajo 0,05 en el 99,35 % de 767 píxeles, también en el cráter; nuestra huella del PNG corrida 1 fila al S y 1 columna al E | **Compatible, sin fuerza para sostenerla** (4 eventos, hacen falta ≥ 10) |
| H15 | Con las **tablas reales** de VOLCAT para ABI, la huella de Chillán llega a la probabilidad que exige SECO y el control no | Tablas y configuración públicas en SSEC desde el 20-11 | 21-11 (§3.7): la lectura reproduce a VOLCAT en nube espesa pero no en nube tenue (εtot < 0,5), donde está la huella (εtot mediana 0,16); nuestro εtot difiere 0,05 del de VOLCAT | **Sin probar**: la validación no se aprobó y Chillán no se midió. Pendiente de la regla de nube tenue y del cielo despejado corregido (correo v5) |

## 5. Perspectivas

- **Física radiativa.** Una pluma diluida y con vapor de agua en el IR se ve como una nube gris y
  delgada: baja un poco la BT11 y deja la BTD positiva, porque el agua y el hielo tapan la absorción
  inversa de la ceniza. El sol es otra cosa. La ceniza refleja la luz de 3,9 µm de un modo distinto que las
  gotas o el hielo, y sobre el suelo oscuro del volcán una pluma delgada se ve en el visible aunque en el IR
  no exista. Esa es la ventaja de VOLCAT de día, y de noche la pierde igual que nosotros.
- **Estadística.** VOLCAT no decide con un umbral por píxel: suma evidencia (Bayes ingenuo), arma
  objetos y relaja los requisitos cerca de volcanes. Con eso cambia sensibilidad por falsas alarmas *donde
  sabe que hay un volcán*. Nuestras variantes compararon píxel por píxel y en todo el disco de 10 km.
- **Operación.** En un observatorio, una falsa alarma de "ceniza" sobre un volcán ya en alerta cuesta
  poco: el turno mira la cámara. Una falsa alarma en el Modo Sala, que se proyecta 24/7, desgasta la
  confianza. Por eso conviene que una señal diurna nueva, si se construye, sea una **capa de apoyo marcada
  como "sólo de día"**, y que no se sume a `detect_ash_enhanced`.
- **Datos.** El cache del detector sólo tiene C11, C14 y C15. Para H1 faltan C02 (0,64 µm, 0,5 km) y
  C07 (3,9 µm), que se leen por ventana como las otras; para H3, el perfil GFS de esos días.
- **Abogado del diablo.** Quizás no hay que perseguir estas plumas con el IR: si son mayormente vapor y
  gas, el detector propio hace bien en no llamarlas ceniza. Lo que falta es saber cuántas de las 58
  detecciones VOLCAT confirma el OVDAS. Si fueran pocas, el problema sería de VOLCAT, no nuestro.

## 6. Plan con costo (cada paso con criterio escrito antes de medir; estado al 21-11)

| Paso | Qué | Costo | Falsa o apoya |
|---|---|---|---|
| 1 | ~~Pedir al OVDAS la hora de cada pulso visto en cámara y el REAV~~ | No hace falta: Nicolás cerró H6 el 19-11 | H6: cerrada |
| 2 | C02 y C07 en la ventana del cache, ρ(3,9/0,65) y textura del 0,65 µm | Hecho el 18-11: 366 escenas, 61 MB, ~1 h | H1 (b): falsada |
| 3 | Contar en los PNG VOLCAT los objetos lejos de volcanes, por tamaño | Hecho el 18-11: 2.181 cuadros, sin descarga | H2: no concluyente |
| 4 | Detecciones VOLCAT nocturnas de Chillán en otras fechas | Hecho el 18-11: 1.177 cuadros, ~0,5 GB | H1 (a): falsada (29-10) |
| 5 | ~~Prototipo de señal diurna~~: no corresponde, el paso 2 no cumplió | | |
| 6 | H3: ε(11) y β(12/11), β(8,5/11), β(7,3/11) contra cielo despejado GFS + cálculo línea por línea propio, y variante empírica | Hecho el 19-11: 37 pares, 458 píxeles, ~1 día de cómputo | H3: no concluyente, no separa |
| 7 | H7: ¿el primer cuadro de cada tramo VOLCAT tiene señal propia? | Hecho el 19-11: 3 episodios, 582 scans FDCF | H7: falsada |
| 8 | **Siguiente, si Nicolás lo aprueba:** ¿VOLCAT dibuja objetos anclados en cumbres altas de volcanes sin actividad, donde un cielo modelado con terreno grueso también fallaría? Separaría el error de terreno + criterios relajados (H2) de una señal real. Con los PNG ya bajados | ~medio día, sin descarga grande | H2 |
| 9 | β(7,3/11) en todos los episodios con pluma VOLCAT fuera del 28 y 29-10 (criterio nuevo, escrito antes) | Hecho el 19-11: 49 pares en 10 días | Indicio de H3: no se repite (noche no concluyente, día falsado) |
| 10 | Prueba tolerante del VAAC de Londres contra las huellas VOLCAT | Hecho el 19-11: 12 configuraciones, 1.204 scans de C13 | H8: no cumple |
| 11 | Usar VOLCAT como capa de detección por volcán en el dashboard, marcada como externa y no validada | Hecho el 19-11 (ficha SDA v2.8, §A.7) | No es prueba: es la decisión operativa mientras no tengamos detector propio |
| 12 | H9: calor a 3,9 µm en el cráter y rayos GLM contra los cuadros VOLCAT | Hecho el 19-11: C07 por ventana, GLM vía Lightning-v1 contrastado con NOAA | H9: falsada como gatillo del momento |
| 13 | H10: dirección de la huella VOLCAT contra REAV y viento GFS, y señal en el sector del REAV | Hecho el 19-11: 6 jornadas, 2 comparables; 726 escenas sin bajar | H10: no concluyente |
| 14 | H11: bandera CF, filas de volcán y atajo de SO₂ con cielo modelado y nube negra por nivel | Hecho el 20-11: 66 pares, 733 píxeles de huella | H11: no concluyente |
| 15 | Etapa 2: SECO propio con VOLCAT como etiqueta, validado dejando una jornada afuera | Hecho el 20-11: 795 scans | No cumple |
| 16 | H12, Test 3 original de Francis 2012 con el cielo modelado ya calculado, control pareado y cumbres sin actividad como prueba de terreno | Hecho el 20-11: 66 pares (decide) más réplica, 10.458 píxeles de cumbres y llano calculados, sin descarga | H12: no concluyente |
| 17 | Leer la tesis de Pavolonis 2014 buscando las tablas de probabilidad de SECO | Hecho el 20-11: capítulos 1 a 6, 8 y apéndices C y E; las razones sobre tierra están como figuras (Fig. 4.12 a 4.14), sin tabla numérica | Fig. 4.12 digitalizada aproximada; insumo de un SECO con esas razones |
| 18 | H13, cambio entre cuadros consecutivos de 10 min | Hecho el 20-11: 1.527 escenas, 72 pares; bosque aleatorio informativo sin completar | H13: falsada |

| 19 | Búsqueda 2023 a 2026 y acceso a VOLCAT en grilla | Hecho el 20-11: tablas, configuración, eventos y caso de Mauna Loa en el servidor público de SSEC | Abrió H14 y H15 |
| 20 | H14: anatomía de los 60 eventos VOLCAT de Chillán | Hecho el 21-11, sin descarga | Compatible, sin fuerza |
| 21 | C2 y C2b: reponer el modelo radiativo; cielo despejado de VOLCAT en Mauna Loa | Hecho el 21-11: ~170 KB de insumos y 1,3 GB a D: | C2 cumple; C2b no concluyente, el posterior muestra corrección por cota |
| 22 | H15: tablas reales, validación contra Mauna Loa | Hecho el 21-11 | Validación no aprobada; Chillán sin medir |
| 23 | **Siguiente:** correo v5 a Pavolonis (permiso de uso, regla de nube tenue, cielo despejado que entra a ε, escala de la firma) | Lo envía Nicolás | Destraba H15 y el archivo diario de eventos (que daría los ≥ 10 eventos que pide H14) |

Plan vigente: `docs/own_volcat/PLAN_2026-11-21_LUT_VOLCAT.md`.

Pasos que **no** conviene repetir: bajar el umbral BTD, anomalía de fondo, β(12/11) con temperatura de
referencia fija, la banda de 8,5 µm sola, β(7,3/11), la prueba tolerante del VAAC de Londres en la versión de
Falconieri y su Test 3 original con el cielo modelado sin corregir el terreno, el calor del cráter o los rayos
como gatillo del momento, la bandera CF y el atajo de SO₂ de SECO, un SECO propio con sólo las variables
públicas y el cambio entre cuadros de 10 min. Están medidos.

## 7. Advertencias de método

- Las secciones de SECO se leyeron en el HTML de AGU, no en PDF; no quedan copias locales (Cloudflare
  bloquea la descarga). El ATBD es de 2012 y describe el algoritmo GOES-R, que no es exactamente el
  VOLCAT operativo de 2026.
- El nulo de las pruebas A y B mezcla días nublados. Una repetición con un nulo despejado sería post hoc y
  no se hizo.
- Error de cita encontrado de paso: `docs/altura_pluma/metodos_fisicos.md:125` y `docs/papers_links/LINKS.md:8`
  fechaban SECO Part 1 en 2013 con el DOI del paper de altura de 2013 (doi:10.1002/jgrd.50173).
  Corregido el 18-11 en esta rama: ahora citan las dos obras por separado, cada una con su DOI.
- Un umbral leído en una fuente secundaria cambió de signo: la prueba de Londres del 19-11 siguió a
  Falconieri 2018 y no al original de Francis 2012 (§3.3). Desde el 20-11, los umbrales se comprueban en la
  imagen del PDF original antes de escribir el criterio.
- Etapa 2: después de commitear el criterio se corrigió una línea de `scripts/rt_e2.py` (la forma de un
  arreglo al interpolar la rejilla), antes del primer número y en el commit que valida la rejilla; la
  validación pasa (error p95 de BT despejada en C14 de 0,20 K contra 0,3 K pedido).
- H12: el control de cumbres se eligió por altura GFS y no por error de BT11, y resultó mucho más fácil para
  el modelo que el macizo de Chillán; la regla de falsación por terreno quedó sin poder. "Sin pluma" quiere
  decir sin objeto VOLCAT a ≤ 50 km: el cráter desgasifica y tiene calor desde el 24-10 (H9).
- H13: la muestra de pares pierde justo los cuadros más tibios (26 sin control, casi todos del 08-11 y del
  14-11 en la tarde y noche); la sensibilidad que parea 30 min antes los recupera en parte y da un resultado
  aún más bajo. El bosque aleatorio informativo no terminó (memoria y disco).
