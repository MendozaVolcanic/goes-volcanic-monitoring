# Por qué VOLCAT ve ceniza en Nevados de Chillán (nov-2026) y nuestro detector no

Fecha: 17-11-2026, actualizado el 18-11 (pasos 2, 3 y 4 del plan, §3.1) y el 19-11 (H3 y H7, §3.2; H6 cerrada). Estado: **informe con siete pruebas medidas y un plan; no cambia código de detección.**
Antecedentes: plan de validación §3.4 a §3.6 (`docs/own_volcat/PLAN_VALIDACION_MAGNITUD.md`) y el informe
del detector (`C:\Users\nmend\AppData\Local\Claude-Data\claude_pzs8sxrjxfjjc\side-session-notes\local_f3a7d295-ddde-4b7c-b258-25e760c44266\INFORME_variantes.md`).

## 1. Respuesta corta, para geólogo

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
siempre su primera compuerta y la decisión cae en los criterios relajados del objeto chico anclado. Un
indicio sin validar: en el episodio nocturno del 28 y 29-10, β(7,3/11) sí sale más alta en la huella
(AUC 0,91 y 0,74), y de día (14-11) no.

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

## 4. Hipótesis ordenadas por evidencia

| # | Hipótesis | A favor | En contra o abierto | Qué la falsaría con datos que ya hay o casi |
|---|---|---|---|---|
| H1 | ~~VOLCAT ve estas plumas por los canales solares de día~~ **Falsada el 18-11** | SECO los usa con ABI; las 58 detecciones de noviembre eran de día | Paso 4: el 29-10 VOLCAT sigue una pluma anclada al cráter de noche (3 cuadros seguidos, cenit 110 a 113°) sin señal IR en la huella. Paso 2: los canales solares no separan la huella del control pareado (AUC 0,50) | Hecho (§3.1) |
| H2 | **El trato especial al cráter** (objetos de 0 a 25 píxeles aceptados a menos de 5, 10 o 50 km de un volcán) deja pasar objetos que en otra parte se descartarían | SECO Part 2 Tabla 4; los objetos de Chillán son chicos (mediana 10 px del PNG) y todos anclados al cráter | Paso 3 no concluyente (R = 3,2, dominado por el 16-11); sin el 16-11, VOLCAT publica objetos chicos lejos de volcanes (R = 0,52), probablemente polvo de Cuyo con señal IR propia | Sigue abierta: haría falta comparar objetos chicos lejos de volcanes **sin** señal IR, que no se pueden separar sólo con el PNG |
| H3 | El **fondo modelado** (cielo despejado con GFS y modelo radiativo) y las razones β, incluida β(7,3/11), bastan para ver la pluma en el IR | Es la diferencia de diseño más conocida; β(7,3/11) más alta en la huella en el episodio nocturno de octubre (AUC 0,91 y 0,74, indicio posterior al criterio) | 19-11 (§3.2): con cielo modelado la compuerta pasa igual en la huella y en el control (0,90 contra 0,88) porque el GFS pone la cumbre 1,5 km más abajo y el modelo queda ~7 K más tibio; con cielo empírico la huella casi no pasa (3,5 %); ningún β separa con |AUC − 0,5| ≥ 0,20 agrupado | **No concluyente según el criterio** (β(12/11) quedó a 0,013 del umbral de falsación); en la práctica no separa. Sólo una prueba nueva de β(7,3/11) en noches con pluma, con criterio propio, podría reabrirla |
| H4 | La huella está **corrida por paralaje** y medimos en el lugar equivocado | Plausible en geometría (0,93 km por km de altura) | Noviembre: no hay señal fría en ningún corrimiento hasta 5 px. 28-10 (18-11): BTD < −1 K en ningún corrimiento; el frío de BT11 crece hacia el SO, no hacia donde predice el paralaje (1,1 filas al sur para 3,5 km) | Falsada, también en el episodio del 28-10 |
| H5 | La señal está en la **banda de 8,5 µm** | Es una banda que VOLCAT usa y el detector no probó en anomalía | Prueba B: AUC 0,26 | Falsada hoy, con la salvedad del nulo nublado |
| H6 | ~~Parte de lo que VOLCAT dibuja **no es ceniza**~~ **Cerrada el 19-11 por Nicolás (OVDAS)** | | "El volcán lleva muchos días con pulsos y columnas de gas y ceniza en cantidades variables" | Cerrada: VOLCAT dibuja ceniza real |
| H7 | VOLCAT **sigue** un objeto detectado antes con señal (seguidor kd-tree del ATBD 2025) y los cuadros sin señal son continuación | ATBD VOLCAT v1.0 §2.2; 19 de 23 cuadros sin señal tienen antecesor | 19-11 (§3.2): el primer cuadro de cada tramo tampoco tiene señal (0 de 3 episodios con BTD, hot spot FDCF o enfriamiento rápido) | **Falsada el 19-11** |

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

## 6. Plan con costo (cada paso con criterio escrito antes de medir; estado al 18-11)

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
| 9 | β(7,3/11) en todas las noches con pluma VOLCAT (criterio nuevo, escrito antes) | ~medio día con el caché de C10 | Indicio de H3 |

Pasos que **no** conviene repetir: bajar el umbral BTD, anomalía de fondo, β(12/11) con temperatura de
referencia fija y la banda de 8,5 µm sola. Están medidos.

## 7. Advertencias de método

- Las secciones de SECO se leyeron en el HTML de AGU, no en PDF; no quedan copias locales (Cloudflare
  bloquea la descarga). El ATBD es de 2012 y describe el algoritmo GOES-R, que no es exactamente el
  VOLCAT operativo de 2026.
- El nulo de las pruebas A y B mezcla días nublados. Una repetición con un nulo despejado sería post hoc y
  no se hizo.
- Error de cita encontrado de paso: `docs/altura_pluma/metodos_fisicos.md:125` y `docs/papers_links/LINKS.md:8`
  fechaban SECO Part 1 en 2013 con el DOI del paper de altura de 2013 (doi:10.1002/jgrd.50173).
  Corregido el 18-11 en esta rama: ahora citan las dos obras por separado, cada una con su DOI.
