# Por qué VOLCAT ve ceniza en Nevados de Chillán (nov-2026) y nuestro detector no

Fecha: 17-11-2026. Estado: **informe con dos pruebas medidas y un plan; no cambia código de detección.**
Antecedentes: plan de validación §3.4 a §3.6 (`docs/own_volcat/PLAN_VALIDACION_MAGNITUD.md`) y el informe
del detector (`C:\Users\nmend\AppData\Local\Claude-Data\claude_pzs8sxrjxfjjc\side-session-notes\local_f3a7d295-ddde-4b7c-b258-25e760c44266\INFORME_variantes.md`).

## 1. Respuesta corta, para geólogo

**El fenómeno.** Las plumas de Chillán de noviembre son chicas (3 a 5 km de altura, unos 8 km de largo)
y casi transparentes en el infrarrojo térmico. Dentro de la zona donde VOLCAT dibuja ceniza, la
temperatura de brillo a 11 µm queda igual o **más tibia** que el cielo despejado del mismo píxel, y la
diferencia 11 − 12 µm no se mueve. En el infrarrojo, la pluma prácticamente no está.

**El mecanismo probable.** VOLCAT no es sólo infrarrojo. Según los papers del algoritmo (SECO,
Pavolonis et al. 2015), de día también usa luz solar reflejada (canal visible de 0,65 µm y la
reflectancia de 3,9 µm). Además acepta objetos muy chicos si nacen a menos de 5, 10 o 50 km de un volcán
conocido. Nuestro detector usa sólo el infrarrojo y no le da trato especial al cráter. Las dos
diferencias apuntan al mismo lado, y los datos de noviembre calzan: **las 58 detecciones de VOLCAT
ancladas al cráter (sin contar el sistema del 16-11) son todas de día**, entre las 12:00 y las 20:20 de
Chile, y en 16 noches no hay ninguna.

**Lo que no está probado.** Que VOLCAT detecte de día no prueba que use el visible en estos cuadros:
también puede ser que la actividad haya sido diurna por casualidad (son cinco episodios). Tampoco
sabemos si cada detección de VOLCAT es ceniza real o vapor con poca ceniza: para eso hace falta el
registro del OVDAS (cámaras, REAV), que no está en el repositorio.

**Qué no es.** No es un problema de umbral (cuatro variantes lo descartaron) ni un corrimiento de la
huella por paralaje (prueba A, abajo), ni una señal escondida en la banda de 8,5 µm (prueba B).

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

## 4. Hipótesis ordenadas por evidencia

| # | Hipótesis | A favor | En contra o abierto | Qué la falsaría con datos que ya hay o casi |
|---|---|---|---|---|
| H1 | **VOLCAT ve estas plumas por los canales solares de día** (ρ(3,9/0,65) y variabilidad del 0,65 µm) | SECO los usa con ABI; 58 de 58 detecciones de día y 0 de noche; en el IR la huella no tiene señal (pruebas A y B, diagnóstico del detector) | Son 5 episodios; con ~60 % del día iluminado, que todos caigan de día por azar tiene ~8 % de probabilidad (0,6⁵) | (a) Una detección VOLCAT anclada al cráter **de noche** en Chillán; (b) que ρ(3,9/0,65) en la huella no supere 0,5 ni se distinga del mismo lugar en días sin pluma |
| H2 | **El trato especial al cráter** (objetos de 0 a 25 píxeles aceptados a menos de 5, 10 o 50 km de un volcán) deja pasar objetos que en otra parte se descartarían | SECO Part 2 Tabla 4; los objetos de Chillán son chicos (mediana 10 px del PNG) y todos anclados al cráter | No sabemos qué tamaño exacto usa la versión 2026 | Objetos VOLCAT de tamaño y estado espectral parecidos lejos de volcanes en el mismo sector (se puede contar en los PNG ya bajados) |
| H3 | El **fondo modelado** (cielo despejado con GFS y modelo radiativo) basta para ver la pluma en el IR | Es la diferencia de diseño más conocida | La huella está igual o más tibia que nuestro cielo despejado empírico; con ε(11) ≥ 0,02 VOLCAT pediría que esté ~1,5 K más fría que el suyo. El caso Kizimen y Karymsky (SECO Part 2 §6) es justo este síntoma y SECO no los vio | Calcular el cielo despejado GFS + RTM del 08 y 10-11, cuando la huella sí está 2 a 5 K más fría: si ni así sale ε(11) ≥ 0,02 con β de ceniza, cae |
| H4 | La huella está **corrida por paralaje** y medimos en el lugar equivocado | Plausible en geometría (0,93 km por km de altura) | Prueba A: no hay señal fría en ningún corrimiento hasta 5 px | Falsada hoy |
| H5 | La señal está en la **banda de 8,5 µm** | Es una banda que VOLCAT usa y el detector no probó en anomalía | Prueba B: AUC 0,26 | Falsada hoy, con la salvedad del nulo nublado |
| H6 | Parte de lo que VOLCAT dibuja **no es ceniza**: vapor de agua de la pluma, nube orográfica o superficie (nieve recién teñida de ceniza) | El 14-11 VOLCAT da 8 a 12 km sin ningún píxel frío (§3.5): el retrieval trabaja con casi nada de señal; la franja SE del cráter aparece también el 12-11, día sin pluma | Las cámaras del observatorio fueron coherentes con alturas de 3 a 5 km | Registro OVDAS (hora de cada pulso en cámara y REAV) contra la hora de cada cuadro VOLCAT |

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

## 6. Plan con costo (nada de esto se hizo; cada paso con criterio escrito antes de medir)

| Paso | Qué | Costo | Falsa o apoya |
|---|---|---|---|
| 1 | Pedir al OVDAS la hora de cada pulso visto en cámara y el REAV del 08, 10, 11 y 14-11 (Nicolás) | 0 de cómputo | H6 |
| 2 | Agregar C02 y C07 a la ventana del cache para los 58 positivos y los días negativos a la misma hora; calcular ρ(3,9/0,65) restando la emisión térmica a 3,9 µm con BT11, y la variabilidad local del 0,65 µm | ~2 h; disco medido en ensayo antes de bajar (la ventana actual pesa 111 MB por 1.204 scans de 3 bandas; C02 es 4 veces más fino) | H1 (b) |
| 3 | Contar en los PNG VOLCAT ya bajados los objetos lejos de volcanes, por tamaño | ~30 min | H2 |
| 4 | Buscar detecciones VOLCAT nocturnas de Chillán en otras fechas (medir antes el tamaño: ~220 KB por cuadro) | ~1 h y hasta ~0,5 GB por mes | H1 (a) |
| 5 | Sólo si el paso 2 cumple su criterio: prototipo de "señal diurna de pluma" como capa aparte, con su ficha SDA en el mismo commit | 1 a 2 días | |

Pasos que **no** conviene repetir: bajar el umbral BTD, anomalía de fondo, β(12/11) con temperatura de
referencia fija y la banda de 8,5 µm sola. Están medidos.

## 7. Advertencias de método

- Las secciones de SECO se leyeron en el HTML de AGU, no en PDF; no quedan copias locales (Cloudflare
  bloquea la descarga). El ATBD es de 2012 y describe el algoritmo GOES-R, que no es exactamente el
  VOLCAT operativo de 2026.
- El nulo de las pruebas A y B mezcla días nublados. Una repetición con un nulo despejado sería post hoc y
  no se hizo.
- Error de cita encontrado de paso: `docs/altura_pluma/metodos_fisicos.md:125` y `docs/papers_links/LINKS.md:8`
  fechan SECO Part 1 en 2013; es de 2015. No se corrigió en esta rama.
