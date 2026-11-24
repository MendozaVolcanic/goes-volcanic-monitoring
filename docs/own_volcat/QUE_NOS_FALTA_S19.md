# Qué nos falta para entender lo que pasa en Nevados de Chillán (S19i, 23-11-2026)

Este documento no mide una hipótesis. Es un diagnóstico: después de 28 pruebas sin firma infrarroja, qué nos está
faltando para entender por qué una pluma de ceniza que el OVDAS ve con cámaras no aparece en nuestro GOES-19.
Lo pidió Nicolás: "encuentro extraño que no podamos ver que esta sucediendo".

- **Base:** commit `a5ab46f` de `main`. No cambia código ni otros informes.
- **Cómo se hizo:** cinco revisores independientes, uno por perspectiva (física radiativa, instrumento, documentación
  de VOLCAT, método de nuestras pruebas, verdad de terreno y otros datos), y un verificador que no vio el
  razonamiento de los otros y trató de refutar 22 afirmaciones (§7). Más dos cálculos chicos de geometría y de señal
  (`docs/own_volcat/que_nos_falta_s19/calculos/`).
- **Qué no es:** no se corrió ninguna prueba nueva. Las miradas a imágenes de Sentinel-2 y Landsat son exploratorias,
  sin criterio escrito antes: sirven para decidir qué probar, no como resultado.
- **Cómo leer la confianza:** CONFIRMADO quiere decir que la fuente se leyó en esta sesión y el verificador no la
  refutó. SOSPECHA es inferencia o cuenta propia. SIN DATO es lo que se buscó y no se encontró.

> **Actualización S20 (24-11-2026), agregada al revisar este PR. El diagnóstico se escribió antes de H29, S20b, S20c
> y S20d.** Lo que cambió desde entonces (detalle en `POR_QUE_VOLCAT_VE_Y_NOSOTROS_NO.md` §1 y §3.9):
> - **MET-01 (§3.4) quedó confirmado** número por número en S20 y medido en S20c (`s20c_controles_limpios/`): con
>   controles previos a la actividad, la BTD de la huella queda 0,23 a 0,42 K hacia la ceniza en las seis pruebas,
>   sin poder para la regla. Es la prueba 5 de §5, hecha.
> - **La prueba 1 de §5 está hecha en su parte infrarroja** (S20b, `s20b_verdad_alta_res/`): con la huella de
>   Landsat (25-10) y Sentinel-2 (08-11) en la grilla de ABI con paralaje, el píxel junto al cráter da SEÑAL (unos
>   1 K más bajo en 11 menos 12 µm). La parte en reflejado (C02, C05, C06) sigue sin hacer.
> - **La prueba 10 de §5 está en curso** en S20d (`s20d`): Landsat a 100 m sin firma de ventana partida en la franja
>   del 25-10, según su medición todavía sin PR ni revisión.
> - **H29 y su revisión** encontraron una firma débil lejos del cráter el 08-11 que se mueve con la huella de VOLCAT.
> - Por eso la frase de §1 "con el infrarrojo de 2 km solo no habrá un detector confiable" sigue en pie, pero "las
>   28 pruebas sin firma" ya no: hay firma de un píxel y de un kelvin cuando se sabe dónde mirar.
> - Siguen abiertas, y son lo más nuevo de este documento: las bandas reflejadas de GOES-19 (prueba 2), GOES-18 en
>   estéreo (prueba 3), el sector de mesoescala y la serie de las cámaras del OVDAS con hora al segundo (§6).

## 1. Para geólogo

**En una frase:** lo más probable es que estas plumas, vistas desde arriba, sean bocanadas más chicas que un píxel
infrarrojo, casi a la temperatura de la nieve que tapan. Las buscamos sólo en el infrarrojo, en el lugar que marcaba
VOLCAT, y sin una verdad propia de dónde y cuándo estaba la pluma.

**El fenómeno.** Hay una imagen que muestra lo que ve la cámara. Landsat 8 pasó el 25-10 a las 11:34 de Chile, entre
dos pulsos del REAV y con cielo despejado. A 30 m se ve una franja gris de 1,1 a 1,3 km de ancho que oscurece la
nieve, de 3 a 9 km del cráter, hacia el oeste-suroeste. En el térmico de 100 m de la misma escena, esa franja no se
distingue sobre la nieve (§3.5).

GOES-19 en el infrarrojo no ve el color de la franja. Ve cuánto más fría es que el suelo que tapa, promediado en un
píxel de 2,1 por 2,8 km. Tres factores se multiplican:

1. **Tamaño.** Una franja de 1 km llena a lo más un tercio a la mitad del píxel.
2. **Temperatura.** Sale a 1 a 2,5 km sobre una cumbre nevada. La nieve no pasa de 0 °C y el aire a esa altura
   está entre −4 y −16 °C: de noche y en la mañana casi no hay contraste.
3. **Edad.** A menos de una hora de la boca la ceniza es gruesa y viene con agua, y la firma de 11 menos 12 µm da
   cero o positivo aunque haya mucha ceniza.

De noche y en la mañana eso basta: quedan unas décimas de kelvin, lo que la cumbre varía sola de un día a otro. Que
la cámara vea la columna y el satélite térmico no, es lo esperable en una erupción chica, y está publicado (§3.1).

**De tarde no basta, y ahí está lo que no entendemos.** De tarde el suelo está a 280 a 288 K y una pluma de 1 km
enfriaría el píxel entre 1 y 7 K. Lo medido en la huella exacta de VOLCAT es 0,8 K. O la pluma de tarde es además
tenue o muy baja, o la huella de VOLCAT no está donde está la pluma. La tarde es cuando VOLCAT más dibuja y donde no
tenemos imagen fina, ni fondo limpio, ni duración de los pulsos (§3.2).

**Lo que más probablemente nos falta, en orden:**

1. **Una verdad propia de dónde y cuándo está la pluma.** Dieciocho de 34 mediciones buscaron dentro de la huella de
   VOLCAT, que se sostiene por seguimiento. Las que usaron el REAV confiaron en una dirección leída desde una
   cámara: el 25-10 dice sureste y la franja de Landsat va al oeste-suroeste, fuera del sector medido. Falta la
   serie de las cámaras con hora al segundo (§3.4, §3.5).
2. **Mirar con luz reflejada, a la escala de la pluma.** GOES-19 tiene un visible de 0,5 km y una banda de 1,6 µm
   de 1 km, donde la nieve se ve oscura y una nube de ceniza o de gotas, clara. GOES-18 ve la cumbre casi de lado.
   Ninguna prueba las usó así. El VAAC Buenos Aires dijo ver ceniza en satélite en 16 de 30 avisos, casi siempre
   "leve" o "tenue" (§3.2, §3.5).
3. **La tarde.** Un sector de 1 minuto de GOES-19 sobre Chillán, que se puede pedir, o la prueba de verano, son las
   formas de ver un pulso de tarde entero (§3.2).
4. **Saber cuánto vale cada "no separa".** Hasta el 21-11 ninguna prueba demostró antes que podía ver una pluma, y
   las de verdad del OVDAS demostraron poder para una capa ancha y sostenida, no para una bocanada. Eso no esconde
   una señal grande, pero las 28 pruebas son cuatro familias, no 28 mediciones (§3.4).
5. **Tres cosas de VOLCAT leídas a medias.** Su puerta de nacimiento compara el espectro del objeto con su entorno,
   no sólo forma y borde. Sus criterios son públicos e iguales para casi todos los volcanes. Y la altura que publica
   en Chillán puede ser un valor de partida y no una medición (§3.3).

**Lo que no cambia.** Con el infrarrojo de 2 km solo no habrá un detector confiable de estas plumas, y VOLCAT sigue
bien como capa externa. Cambia dónde buscar: de día, en reflejado, junto al cráter y a la hora del pulso.

**Qué haría primero.** Las pruebas 1 y 2 de §5 (horas de trabajo): el visible de 0,5 km y la banda de 1,6 µm de
GOES-19 sobre la franja del 25-10 y sobre el cráter en los pulsos de la tarde del 28-10. Y pedir al OVDAS la serie
de las cámaras.

## 2. Qué se revisó

| Perspectiva | Qué se leyó | Informe de trabajo (fuera del repositorio) |
|---|---|---|
| Física radiativa | 12 papers locales, 4 bajados; H23 | `A_fisica_radiativa.md` |
| Instrumento y escala | PUG L1b, Kalluri 2018, Schmit 2005 y 2017, páginas de calibración de NOAA STAR, encabezados L1b, 1.200 encabezados de mesoescala | `B_instrumento_escala.md` |
| Documentación de VOLCAT | ATBD 2025, CDR 2022, SECO Parte 2, Pavolonis 2018, informe STAR 09-2026, servidor de SSEC y página del autor | `C_volcat_documentacion.md` |
| Método | informe madre entero, 13 scripts enteros y 12 en parte, salidas crudas de 11 pruebas | `D_auditoria_metodo.md` |
| Verdad de terreno y otros datos | 16 boletines del OVDAS, 35 avisos del VAAC, catálogos de Sentinel-2, Landsat, ECOSTRESS, EMIT y ASTER | `E_verdad_terreno_otros_datos.md` |
| Verificación adversarial | 22 afirmaciones, sin ver los informes anteriores | `F_verificacion.md` |

Los seis informes de trabajo, con cada cita y cada ruta, están en
`C:\Users\nmend\AppData\Local\Claude-Data\claude_pzs8sxrjxfjjc\side-session-notes\local_99449581-bcd8-40fc-b7a3-7dbf11ba7fc2\s19i\`.
No entran al repositorio porque uno de ellos describe archivos de SSEC. Este documento repite la fuente primaria de
cada afirmación que usa.

## 3. Revisión por perspectiva

### 3.1 Física radiativa de plumas chicas y diluidas

**La firma infrarroja es proporcional al contraste de temperatura entre la pluma y su fondo.** No lo descubrió H23:
está en la literatura desde 1994.

- Wen y Rose 1994 (JGR 99, p. 5430, conclusión 2): el método funciona mejor con gran diferencia de temperatura entre
  superficie y nube; TEXTO: «Our model works best when there is a large difference».
- Saint et al. 2024 (p. 2): la detección «relies on the temperature contrast between the surface and the cloud»; su
  éxito cae bajo 4 km. Ese estudio es sobre mar; sobre Chillán lo que cuenta es la altura sobre el terreno.
- Kylling et al. 2015 (AMT 8, p. 1941 y 1947, calculadas desde el PDF): con más de 1 g/m² y sin nubes, el método detecta 74,7 % de los
  píxeles con la ceniza a unos 6 km y 15,1 % con la ceniza a 2 o 3 km.
- Las columnas de Chillán llegan a 0,4 a 2,4 km sobre el cráter (REAV, §3.5): todas en el régimen malo.

**Hay casos publicados sobre fondo nevado.** Schneider y Rose 1994 (USGS Bull. 2047, p. 409), sobre Redoubt, TEXTO:
«the cloud is not apparent where it passes over the snow-covered mountains». Ellrod et al. 2003 (párrafo [8]) listan
el fondo frío (nieve, hielo) como condición que anula la técnica. SECO Parte 2 (p. 7863) no detectó las plumas
débiles de Kizimen y Karymsky por lo mismo. No se encontró un caso publicado así para Popocatépetl, Ubinas,
Villarrica, Etna ni Láscar (SIN DATO). El capítulo de Pavolonis y Sieglaff 2020 (p. 110) dice que los pulsos chicos
de Reventador sí se ven con ABI: no es regla que un pulso andino sea invisible. Lo que distingue a Chillán es la
combinación de tope bajo, nieve debajo y pluma angosta.

**Mezcla dentro del píxel: lo que no habíamos considerado bien (CONFIRMADO el mecanismo, SOSPECHA su peso).**
Heidinger y Pavolonis 2009 (JAMC 48, p. 1102 y 1103): lo observado es «the product of the true emissivities and
subpixel cloud fraction», con el efecto mayor para nube espesa que cubre poco. H23 concluyó que la pluma real "fue más tenue que el límite, o más baja, o las dos cosas" (§1 de su informe), y de
ahí salió la lectura "pluma tenue". Pero H23 pintó una capa que llena el píxel. Lo que el satélite mide es el
producto de dos cosas: cuán opaca es la pluma y qué parte del píxel llena. Las pruebas de "pluma angosta" (H24, H25, H27)
usaron una franja de 6 km, que son píxeles llenos. El caso de la pluma más angosta que el píxel no está probado.

**Pluma joven: ceniza gruesa, agua y núcleo opaco (CONFIRMADO en la literatura, SOSPECHA en Chillán).**

- Wen y Rose 1994 (p. 5430, conclusión 1): la firma aparece sólo con predominio de partículas de radio menor que
  5 µm. Saint 2024 (p. 14) y Pavolonis 2020 (p. 106): se anula hacia 10 µm.
- Schneider y Rose 1994 (p. 416 y 417): la técnica falla «for very young clouds with high water content»; en
  Redoubt funcionó en nubes de más de una hora y falló junto al cráter.
- Las huellas de Chillán miden unos 8 km: con cualquier viento, esa ceniza tiene minutos.
- No hay granulometría de la ceniza de 2026 en los boletines (SIN DATO).

**Con la pluma más tibia que la nieve la firma se invierte (SOSPECHA: derivación, no cita).** De noche, con nieve a
264 K y pluma a 269 K, la cuenta de `senal_subpixel.py` da la temperatura de 11 µm más alta y la diferencia positiva.
SECO Parte 1 (p. 7825) reconoce ceniza con emisividad «less than 0.02 or even negative» por inversiones sobre
tierra. Un detector que busca sólo el lado negativo es ciego ahí.

**La razón β de una nube baja mide su temperatura, no su partícula.** Pavolonis 2010 (JAMC 49, p. 2001): en una
nube de tropósfera baja, β referida a la tropopausa es «most sensitive to the effective cloud temperature and not
to cloud microphysics». Explica por qué H3, H11 y H15 terminaron "midiendo el terreno".

**El fondo de Chillán puede no ser estable durante la erupción (SOSPECHA).** En los recortes de Sentinel-2 del 29-10,
08-11 y 13-11 la nieve al sur y sureste del cráter se ve oscurecida, compatible con ceniza depositada. Nieve con
ceniza se calienta distinto y su emisividad en 11 y 12 µm no es la de la nieve limpia. Puede ser parte de por qué
Chillán sin pluma es 1,54 veces más ruidoso que las cumbres de control (H27) y de por qué las líneas base del propio
píxel (H23, H24, H25) no valen igual antes y después de fines de octubre.

**Verificado limpio.** La composición no es el problema (la ceniza silícea es el caso favorable). Los sulfatos
empujan la firma al mismo lado que la ceniza. El vapor de agua del aire pesa poco sobre una cumbre de 3 km (H23, S5).
Un cráter de 10 MW corre la diferencia sólo +0,03 K.

**Corrección menor al informe madre.** `POR_QUE_VOLCAT_VE_Y_NOSOTROS_NO.md` línea 139 dice que el 10,3 y el 13,3 µm
no se usan con ABI para detectar. El capítulo de 2020 (p. 114) dice que el algoritmo base de GOES-R usa razones β
con 10,3 µm. Son dos descripciones de fechas distintas (2012 y 2020) y la línea habla de VOLCAT, no del algoritmo
base: conviene revisarla. La prueba del VAAC de Londres ya probó el 10,3 µm sin cambio.

### 3.2 Escala e instrumento

**Geometría (cálculo propio, `calculos/geometria_pixel.py`, confirmado por el revisor con las fórmulas del PUG).**

| Magnitud | Valor |
|---|---|
| Ángulo cenital de vista en Chillán | 42,9° |
| Píxel infrarrojo (bandas de 2 km) | 2,09 km E-O por 2,84 km N-S (5,9 km²) |
| Píxel del visible C02 | 0,52 km E-O por 0,71 km N-S |
| Corrimiento de la cumbre de 3,2 km (la grilla va al elipsoide) | 2,99 km hacia el rumbo 174°: 1,04 filas al sur |
| Corrimiento por cada km de altura de la pluma | 0,93 km al sur |
| Fracción del píxel que llena una franja de 1 km que lo cruza | 0,35 (E-O) a 0,48 (N-S), hasta 0,52 en diagonal; es cota superior |

La fracción es cota superior porque el píxel no es una caja: cada valor de L1b es una suma ponderada de 4 por 4
muestras de detector (Kalluri et al. 2018, p. 18: «formed as a weighted combination of a 4 × 4 matrix of samples»),
repartidas en unos 6,6 por 7,7 km sobre Chillán. Los pesos no son públicos (SIN DATO).

**Señal esperada (cálculo propio, `calculos/senal_subpixel.py`).** Mezcla de radiancias de Planck sin atmósfera.
Columnas: cambio de la temperatura de 11 µm y de la diferencia 11 menos 12 µm, en kelvin.

| Caso | Pluma llena el píxel | Franja de 1 km (0,35) | Franja de 0,4 km (0,15) |
|---|---|---|---|
| Tope a 4 km (263 K), nieve a 264 K, pluma casi opaca | −0,95 y −0,07 | −0,33 y −0,03 | −0,14 y −0,01 |
| Tope a 5 km (257 K), nieve a 264 K, emisividad 0,30 | −2,04 y −0,54 | −0,71 y −0,18 | −0,30 y −0,08 |
| Tope a 5 km (257 K), suelo a 274 K, emisividad 0,30 | −4,78 y −1,25 | −1,65 y −0,42 | −0,70 y −0,18 |
| Tope a 3 km (269 K), nieve a 264 K, emisividad 0,30 | +1,53 y +0,40 | +0,54 y +0,14 | +0,23 y +0,06 |
| Tope a 4 km, suelo de tarde a 285 K, emisividad 0,15 | −3,01 y −0,83 | −1,04 y −0,29 | −0,45 y −0,12 |
| Tope a 4 km, suelo de tarde a 285 K, emisividad 0,30 | −6,11 y −1,59 | −2,10 y −0,54 | −0,89 y −0,23 |
| Tope a 4 km, terreno bajo a 290 K, emisividad 0,30 | −7,38 y −1,92 | −2,53 y −0,64 | −1,08 y −0,27 |

Para comparar: el fondo sin pluma de la diferencia 11 menos 12 µm en los píxeles de cumbre va de −0,3 a +0,4 K
(H23 §1). El verificador contrastó el modelo con la tabla de H23 §5: en la temperatura de 11 µm calza, y en la
diferencia 11 menos 12 µm el modelo subestima entre 1,2 y 1,6 veces.

Lectura, por hora del día:

- **Noche y mañana, suelo frío (264 a 274 K).** Una franja de 1 km queda dentro del fondo en casi todos los casos.
  El ancho y la falta de contraste bastan para explicar que no se vea.
- **Tarde, suelo tibio (280 a 288 K en las huellas que VOLCAT publicó, `h3_h7/h3_resultado.txt`).** La misma franja
  a 4 km enfriaría el píxel 1 K con emisividad 0,15, 2 K con 0,30 y casi 7 K si fuera opaca. Lo medido en la huella
  exacta de VOLCAT, contra base despejada, es −0,81 K (`revision_h13_h17_nube/resultados/rev_h17_resultado.txt:11`).
  Eso acota el producto de la fracción cubierta por la emisividad a menos de 0,04 a 0,05. De tarde, "la pluma es
  angosta" no alcanza: además tiene que ser tenue, o no subir de la cota de la cumbre, o no estar en esos píxeles.
- **Sobre terreno bajo y tibio** la misma franja sale del fondo. Por eso importa hacia dónde va la pluma, y por eso
  la prueba de verano tiene sentido físico: sin nieve, el suelo de la cumbre se calienta de día.

**El ruido del instrumento no es el límite (CONFIRMADO).** GOES-19 mide con unos 0,02 K de ruido en 11 y 12 µm
(gráfico de NOAA STAR del 13 y 14-11-2026), el paso de cuantización es 0,04 K a 270 K (encabezado L1b) y el
corregistro medio entre C14 y C15 es de unos 0,5 µrad, 0,01 píxel. Lo que limita es la escala y el fondo.

**La hora real de cada imagen (cálculo del revisor sobre fuentes leídas; SOSPECHA en el segundo exacto).** El L1b
sólo trae inicio y fin del barrido. El disco completo se barre de norte a sur en 22 franjas (Kalluri 2018, Tabla 2)
y Chillán cae en la franja 19: se observa unos 8 min 39 s después del minuto redondo del rótulo. El cuadro "09:20"
del 27-10 miró Chillán cerca de las 09:28:39 UTC. La explosión de 2.000 m empezó a las 09:23:17 UTC (REAV de las
06:40 HL). GOES-19 la miró 5 min 22 s después y otra vez 15 min 22 s después. Ninguna prueba ajustó la hora.

**Un pulso contra una mirada cada 10 minutos.** Las explosiones vulcanianas «characteristically last only seconds
to minutes» (Clarke 2013, resumen del capítulo). Cada pulso tiene a lo más un cuadro con la bocanada compacta cerca
del cráter y uno o dos con la bocanada ya diluida.

**No hubo sector de mesoescala sobre Chile (CONFIRMADO).** El revisor leyó el centro de los dos sectores de 1 minuto
en la primera imagen de cada hora del 25-10 al 18-11-2026 (1.200 encabezados del bucket público `noaa-goes19`).
Siempre estuvieron sobre Estados Unidos, salvo uno sobre Ecuador del 30-10 al 01-11. Los eventos volcánicos tienen
prioridad 2 en la lista de NOAA (blog de CIMSS del 11-04-2021) y existe un trámite para usuarios internacionales
(Mozer et al. 2019, resumen AMS). Para los pulsos que vienen se puede pedir.

**GOES-18 ve Chillán casi de lado (CONFIRMADO que hay dato; SOSPECHA que la columna se vea).** Desde 137° O lo mira
con 79° de ángulo cenital. En esa vista, una columna vertical de 1 a 2,5 km sobresale 1,7 a 4,3 píxeles del visible.
El revisor comprobó que la ventana de C02 de GOES-18 del 28-10-2026 18:30 UTC tiene dato válido. Horváth et al. 2021
(p. 12189) miden alturas así con ±500 m. Ninguna prueba usó GOES-18, ni la sombra, ni el estéreo.

**Paralaje del terreno.** Desde H9 las pruebas lo corrigen. Las del 17 al 20-11 no, pero comparan huella e imagen en
la misma grilla, así que no las invalida. Sí afecta al control de cumbres de H12: los píxeles de Antuco y Longaví
quedaron una fila al norte de donde la imagen muestra la cumbre, 580 a 680 m más abajo. Eso puede explicar por qué
ese control "no tuvo el error de Chillán" (SOSPECHA). El corrimiento de 1 fila y 1 columna entre el PNG de VOLCAT y
sus archivos de evento no calza con paralaje: la componente este observada es diez veces la esperada.

**Dos sospechas con prueba barata, sin medir.** El temblor de registro entre cuadros, multiplicado por el gradiente
térmico de la cumbre, puede dar 0,1 a 0,4 K en la temperatura de 11 µm sin que cambie la escena. Y las bandas de
3,9 a 9,6 µm usan detectores casi el doble de grandes que las de 10,3 a 13,3 µm (Kalluri 2018, Tabla 1), así que
toda resta entre los dos grupos puede llevar un residuo fijo en un borde térmico como la cumbre.

### 3.3 Lo que VOLCAT hace de verdad, según su documentación

**No existe documentación pública de la vía pluma o bocanada (`ASHPLUMEPUFF`).** El ATBD de 2025 (§2.3.1) remite a
los artículos de 2015, y esos artículos (SECO Parte 2, p. 7863 y 7868) declaran las plumas débiles sobre tierra como
no detectadas y dejan el seguimiento y la forma de pluma como mejora futura. La búsqueda web no devuelve nada para
`ASHPLUMEPUFF` ni "SECO+" fuera de los archivos de SSEC. La exactitud que el ATBD informa para esa clase se midió
en nubes con firma clásica y más de 1 g/m² (§2.5.3.1.2): no se le puede aplicar a Chillán.

**Lo que sí es público y no habíamos abierto (CONFIRMADO).** La base de criterios de alerta por volcán que nombran
los registros de VOLCAT está dentro de un paquete del servidor público de SSEC
(`https://bin.ssec.wisc.edu/pub/volcat/static_ancillary/`). El revisor leyó su estructura. Nevados de Chillán tiene
exactamente las mismas filas de criterios que casi todos los demás volcanes (1.558 de 1.561 entradas iguales). Hay
una familia de filas de ceniza que no exige probabilidad, con columnas sin rótulo: es la candidata a ser la vía
pluma. La copia de trabajo quedó en `D:\goes_notas\s19\s19i_ssec_config\` y no entra al repositorio.

Consecuencias para lo que hemos escrito:

- "Los umbrales por volcán no son públicos" (informe madre §3.3): son públicos y son generales.
- H2, "trato especial al cráter": no es un trato a Chillán. Es una regla general por tamaño de objeto y distancia.
- "La regla de nacimiento no está en ningún registro público" (informe madre §1): vale para la lógica del programa,
  no para los parámetros ni las tablas. Lo que no es público es el código, la lista dinámica de volcanes activos y
  los valores de la corrida de producción de GOES-19.

**La puerta de nacimiento sí mira el espectro, pero relativo al entorno (CONFIRMADO lo que dicen los rótulos;
SOSPECHA la interpretación).** Los rótulos del diagnóstico de una candidata a pluma en el registro del caso de
prueba de Kirishima indican que se comparan diferencias entre bandas (11 menos 12, 8,5 menos 11, 3,9 menos 11)
entre el objeto y su entorno, más tendencias temporales por píxel. No exige diferencia negativa ni probabilidad. El
informe madre dice que la puerta "mide contraste de forma y borde contra el entorno, no firma de ceniza": conviene
corregirlo. Y ese contraste está en nuestros números: H14 midió la diferencia 11 menos 12 µm de la huella menos la
de su anillo en −1,26 K en los 51 cuadros pegados al cráter (`eventos_h14/INFORME_H14.md` §3.3), y lo descartó como
terreno sin compararlo con el mismo lugar en días sin pluma. Hay tres lecturas y hoy no sabemos cuál vale:

1. El contraste es de la pluma: el infrarrojo sí lleva una señal, relativa y chica, y buscamos la equivocada.
2. El contraste es permanente y de la atmósfera: sobre una cumbre de 3,2 km hay menos vapor que sobre los valles.
3. El contraste es permanente y del suelo: ceniza depositada sobre nieve y roca junto al cráter. SECO Parte 2 §4.3
   (p. 7853) describe ese caso como falsa alarma posible.

En las lecturas 2 y 3, la puerta de VOLCAT pasaría en Chillán por el lugar y no por la pluma. El verificador
aporta un dato que inclina la balanza hacia esas dos: la revisión de H17 comparó los mismos píxeles de huella con su
propia historia sin evento y quedan −0,19 a −0,22 K, contra −0,02 a −0,13 K en los controles
(`revision_h13_h17_nube/resultados/rev_h17_resultado.txt:10-11`). De los −1,26 K, lo que no es permanente es del
orden de 0,1 a 0,2 K. Casi todo el contraste es la cumbre fría y seca contra el terreno bajo. Los umbrales de la
puerta no están en los registros, así que no sabemos si un contraste permanente de ese tamaño le basta.

**La cadena que nació por crecimiento vertical: medida en bruto por el verificador, y parece tiempo meteorológico.**
La cadena del 13-11 19:00 UTC nació por la vía `VCB`. Pavolonis et al. 2018 (Tabla 7, p. 921) pide que la
temperatura mínima de 11 µm del objeto baje al menos 10 K entre imágenes, y esa fila sólo vale para volcanes en
agitación. H7 midió el enfriamiento el 28-10, el 10-11 y el 14-11, no el 13-11. El verificador lo leyó en los cubos
de H23, por píxel y sin seguir objetos: en el cuadro de nacimiento la temperatura mínima a 10 km o menos del cráter
baja 3,6 K respecto de las 18:50, no 10 K. Media hora antes, una nube de 237 K cruzó la cumbre, y esa tarde hay
entre 330 y 600 píxeles bajo 260 K en la ventana: convección alrededor. El evento tiene 5 píxeles en el primer
cuadro y después un solo píxel a 6 km del cráter durante dos horas (`eventos_h14/INFORME_H14.md:16`). Lectura: ese
nacimiento puede ser una alerta por nubes convectivas junto a un volcán en agitación, no una columna eruptiva. Es
una lectura en bruto, sin criterio previo (SOSPECHA).

**La altura que VOLCAT publica en Chillán es compatible con ser el valor de partida y no una medición (SOSPECHA).**
El ATBD de 2025 (§2.3.2.4 y Tabla 2-1) dice que los valores de partida restringen el resultado cuando las medidas
traen «little or no information», y que la partida de la temperatura de la nube es la temperatura de 11 µm menos
15 K. Pavolonis et al. 2013 (p. 1449): con emisividad bajo 0,05 la recuperación «adds little to no value to the
first guess». Cuenta del verificador para el 13-11 19:00: los píxeles más fríos de la cumbre están a 273 a 277 K;
menos 10 a 15 K da 258 a 267 K, que en el perfil son 3,3 a 4,8 km; VOLCAT publicó 3,76 a 4,05 km. Compatible, no
demostrado: una nube real a 300 a 800 m sobre la cumbre daría la misma altura, y H14 tiene alturas de 2,8 a 11,4 km.
Si se confirma, afecta cómo rotular la altura VOLCAT en el dashboard y en la ficha SDA §A.7.

**VOLCAT acepta cerca de una falsa alarma por acierto.** ATBD 2025 §2.5.3.1.3: «54% of classifiable ash alerts were
correct detections». "VOLCAT lo publica, luego hay algo que ver" vale para el periodo, no cuadro a cuadro.

**VOLCAT trabaja todo a 2 km, también el visible** (comprobado en el paquete de prueba de Mauna Loa, no en
producción). No ve Chillán con más detalle que nosotros, pero sí con más bandas: su archivo de entrada trae a 2 km
los canales de 1,6 y 2,2 µm y una variable con el máximo del visible dentro del píxel. Son bandas que ninguna prueba
nuestra usó. El uso de mayor resolución figura como mejora futura en el ATBD (§3.2).

### 3.4 Método: lo que arrastramos

La auditoría leyó los scripts, no sólo los informes. Tabla completa de 34 filas en `D_auditoria_metodo.md`.

**Los controles "sin pluma" eran días con pluma (CONFIRMADO).** "Sin pluma" quería decir "VOLCAT no dibujó objeto",
nunca "el volcán estaba quieto". Como el control se elegía por la temperatura más parecida y los cuadros con pluma
eran los más despejados, el pareo fue a buscar los pocos días despejados de noviembre, que son los días con
actividad documentada.

| Prueba | Pares | Controles en días con actividad documentada | Días |
|---|---|---|---|
| Paso 2 (canales solares) | 46 | 45 | 13-11 (29), 12-11 (16) |
| H3 | 37 | 34 | 13-11 (20), 12-11 (10), 27-10 (4) |
| β(7,3/11) | 49 | 42 | 12-11 (17), 07-11 (10), 13-11 (8) |
| VAAC de Londres, pareado | 45 | 38 | 13-11 (23), 12-11 (15) |
| H13 | 72 | 62 | 12-11 (18), 27-10 (15) |

Trece controles del paso 2 y ocho de H3 caen el 13-11 entre las 19:00 y las 21:00 UTC, dentro de un evento de
Chillán que VOLCAT mismo publicó (`eventos_h14/resultados/por_evento.csv`). H11 y H12 heredan esos pares.

Cuánto pesa, según el verificador: los conteos son correctos, pero la contaminación real puede ser chica. El evento
del 13-11 es de un solo píxel después del primer cuadro y esa tarde había convección (§3.3). Los controles del 12-11
son anteriores al único pulso documentado ese día. Y el control mide la huella del día con pluma puesta sobre otro
día, no el lugar donde estaba la pluma del día de control. Lo que queda firme es más modesto: esas pruebas no tenían
un control que se supiera sin actividad, y un mes de fondo anterior al 24-10, ya bajado, nunca se usó para eso.

**El pareo por temperatura observada (CONFIRMADO EN PARTE).** El control era el día con la temperatura de 11 µm de
la huella más parecida, con 3 K de tolerancia (`h3_h7/scripts_h3/comun_h3.py:46`, `h3_pareo.py:12`; el paso 2, sin
tope). Con el cielo despejado empírico eso iguala por construcción la emisividad de 11 µm y la compuerta de H3. Con
el cielo modelado no: ahí lo que inutiliza la compuerta es el error del modelo (7 K). No iguala la diferencia 11
menos 12 µm ni las razones β. El verificador agrega dos cosas. En la práctica el pareo no elige un día parecido
entre muchos: elige el único despejado. Y el cuadro con pluma sale más tibio que su control en 26 de 37 pares, al
revés de lo que haría una pluma fría. Entonces el pareo no escondió un enfriamiento de 0,5 a 2 K: en esas huellas
no lo había. H24 parea por temperatura esperada desde el 22-11, que es lo correcto.

**La huella de VOLCAT como verdad de lugar.** Dos problemas distintos:

- La huella decodificada del PNG estaba corrida (1 fila al sur y 1 columna al este; sólo 30 % de los píxeles que
  VOLCAT publica caía dentro, `eventos_h14/resultados/georef_resumen.json`), y el desfase no es fijo. La usan once
  pruebas, y la etapa 2 la usó como etiqueta de entrenamiento. Ninguna se repitió con la huella corregida. La misma
  pregunta sí se volvió a medir después con la huella exacta de los archivos de evento (H14 §3.3, H17 y su
  revisión), y tampoco separó: el corrimiento diluyó las pruebas viejas, pero no escondía una señal grande.
- Aun corregida, si VOLCAT sostiene el objeto por distancia al cuadro anterior (H28), su huella dice dónde estaba el
  objeto, no dónde está la ceniza. No se puede decir a la vez "VOLCAT no ve la pluma en el píxel" y usar sus píxeles
  como el lugar donde buscarla.

**Con verdad del OVDAS, el poder demostrado es para una capa ancha y sostenida (CONFIRMADO).** En H24, H25 y H27 el
estadístico es la mediana sobre los 53 a 58 píxeles del sector y después la mediana sobre los cuadros
(`h24_pulsos_reav/scripts/h24_medir.py:275` y `:285`). El sector empieza a 4 km del cráter (`:41`). El control
positivo pinta la capa en todo el sector y en todos los cuadros (`:256-258`, `:363`). El único pulso alto que H24
pudo decidir, la explosión del 27-10, es puntual. "Sin señal, con poder" vale para una emisión ancha de decenas de
minutos, no para una bocanada.

**Casi nadie miró donde nace la pluma (CONFIRMADO EN PARTE).** Ninguna prueba midió el píxel del cráter y sus
vecinos a la hora de un pulso documentado con la diferencia 11 menos 12 µm ni contra una línea base. Lo más cercano
es H7, que buscó un enfriamiento de 2 K en 10 minutos a 10 km o menos del cráter en cuadros que coinciden con los
pulsos de la tarde del 28-10 y del 10-11, y H10, que midió una cuña de 2 a 15 km. La única prueba que usó el visible
(paso 2) lo promedió de 0,5 a 2 km (`pruebas_17_18nov/scripts/paso2_analisis.py:26-27`), guardó sólo su textura
dentro del bloque, lo midió en la huella VOLCAT corrida y lo comparó contra el 12 y el 13-11. Nadie buscó la pluma
ni su sombra en el visible a su resolución. Ninguna prueba usó las bandas de 1,6 ni 2,2 µm (0 lecturas de C05 y C06
en los scripts). Cautela del verificador: el visible a 2 km con su textura ya dio AUC 0,50 en la huella; puede que
a 0,5 km tampoco se vea una pluma tenue sobre nieve. Por eso importa la banda de 1,6 µm (§3.5).

**Hay corrimientos chicos hacia el lado de la ceniza, pero también hacia el otro lado (CONFIRMADO EN PARTE).** El
auditor de método juntó mediciones con un corrimiento chico y del mismo signo; el verificador comprobó los números y
encontró las que la lista omitía.

| Hacia ceniza | Valor | Fuente |
|---|---|---|
| Huella de evento contra base despejada | BT11 −0,81 K; diferencia −0,22 K | `revision_h13_h17_nube/resultados/rev_h17_resultado.txt:11` |
| H12, cielo despejado menos observado | +0,85 K con pluma, +0,61 K sin pluma | informe madre, líneas 583 y 584 |
| H10, sector del REAV, 25-10 y 27-10 | diferencia 0,2 a 0,4 K más baja | `direccion_pluma/senal_resultado.txt` |
| H24 y H27, E8 a E12 (27 y 28-10) | −0,13 a −0,20 K | `h24_pulsos_reav/resultados/h24_episodios.csv` |
| H3, diferencia del cuadro con pluma menor que la del control | 27 de 37 cuadros, mediana −0,12 K | `h3_h7/h3_resultado.txt` (recuento del verificador) |

| En contra o neutro | Valor | Fuente |
|---|---|---|
| H10, 28-10 | diferencia más alta con pulso (AUC 0,44) | `direccion_pluma/senal_resultado.txt` |
| H24, E2, E3 y E4 (25-10, el día de la franja de Landsat) | +0,03 a +0,04 K | `h24_episodios.csv` |
| H27, E13 (el pulso que VOLCAT marcó en 10 de 11 cuadros) | −0,04 K; Antuco, sin actividad, −0,17 K a esa hora | `h27_fondo_espacial/resultados/h27_episodios.csv` |
| H27, placebo de E10 | −0,29 K, más negativo que su sector (−0,18 K) | ídem |
| BT11 de la huella en varias pruebas | más tibia (prueba A +0,73 K; H17 original +1,28 K) | informe madre §3 y §3.9 |

Lectura: una diferencia 0,1 a 0,2 K más baja es lo que da un cambio chico de humedad entre días o un gradiente de
terreno, y aparece igual en cumbres sin actividad. Los valores "hacia ceniza" de H24 y H27 son de dos días. No hay
base para decir que el infrarrojo lleva una señal de la pluma. Tampoco para decir que no: nadie hizo la prueba de
existencia contra un fondo limpio, con el día como unidad y las cumbres de control al lado (prueba 4 de §5). Ojo con
el caso del 25-10: E2 a E4 se midieron hacia el sureste y la pluma iba al oeste-suroeste (§3.5).

**Las 28 pruebas no son 28 mediciones independientes.** Comparten siete eslabones (el decodificador del PNG, la
lista de días negativos del 17-11, el modelo radiativo de H3, los 60 archivos de evento, los cubos de H23, la lista
de REAV). Agrupadas por eslabón son cuatro familias: las del PNG, las de archivos de evento, las de verdad del OVDAS
y la inyección de H23. Los positivos se concentran en tres jornadas (28-10, 10-11, 14-11). Hasta el 21-11 ninguna
prueba tuvo control positivo: su "no separa" no distingue entre "no hay señal" y "la prueba no podía verla".

**Verificado limpio.** La máscara de nubes no saca la pluma (se aplica a nivel de escena sobre el terreno bajo). El
pareo y el nulo de H24, H25 y H27 están bien resueltos. La hora local del REAV está bien convertida. El PNG y el
L1b son el mismo barrido.

### 3.5 Verdad de terreno y otros datos

**Lo que documentó el OVDAS.** Catorce pulsos con hora y altura entre el 25-10 y el 12-11 (12 REAV de octubre, 2 de
noviembre), de 400 a 2.440 m sobre el cráter, vistos con la cámara Arauco. Los boletines no dan la duración del
pulso, el ancho de la columna, la proporción de ceniza ni hasta dónde se vio la pluma. Diez dan dirección, como
octante. No hay REAV del 01 al 09-11 ni después del 12-11. El RAV del 19-11 (01 al 15-11) es el primero que escribe
«columnas de ceniza». Los dos RAV dicen que el SO₂ es bajo por DOAS y que no hay anomalía satelital de SO₂: el gas
no sirve de trazador en este episodio.

**VOLCAT y el OVDAS coinciden poco.** De los 14 pulsos, 8 no tienen ningún cuadro VOLCAT con objeto, 3 tienen pocos
y 3 casi todos (los de la tarde del 28-10 y del 10-11). De los 108 cuadros con objeto del catálogo del PNG (que no
incluye el evento del 13-11), 66 caen en días sin ningún REAV (`h24_pulsos_reav/INFORME.md` §3; recuento del revisor sobre `calor_rayos/resultados/frames_calor.csv`).
El REAV del 25-10 de las 19:00 HL cita la plataforma de VOLCAT para la altura de columna: el REAV es independiente
de VOLCAT para la hora, no necesariamente para la altura.

**Imágenes de alta resolución en días con pluma (CONFIRMADO que existen; lo que muestran, según el caso).** Mirada
exploratoria, sin criterio previo. El verificador volvió a consultar el catálogo y miró las figuras por su cuenta.

| Escena | Hora UTC | Qué se ve | Lectura |
|---|---|---|---|
| Landsat 8, 25-10 | 14:34:31 | franja difusa gris de 1,1 a 1,3 km de ancho, de 2,9 a 8,8 km del cráter, azimut 254° a 257°; oscurece la nieve | **pluma con ceniza**: una nube de agua blanquearía, no oscurecería |
| Sentinel-2C, 29-10 | 14:53:03 | bocanada blanquecina de 1 a 1,3 km pegada al cráter por el este-noreste | columna de vapor o de gas y ceniza |
| Sentinel-2C, 08-11 | 14:53:02 | nube blanca y compacta de unos 2,6 km, 1 a 2 km al sur del cráter, con sombra; única nube de la escena | vapor, vapor con poca ceniza o cúmulo orográfico: no se decide |
| Sentinel-2B, 13-11 | 14:53:06 | dos bocanadas grises de unos 2 km, despegadas del cráter, a 2,3 a 7,6 km al noreste; hay otras nubes | pulsos arrastrados o cúmulos |

El 25-10 el paso de Landsat cae entre el pulso de las 13:15 UTC y la serie que empieza a las 14:44 UTC. El aviso del
VAAC de esa hora dice «LIGHT VA CLD OBS IN SATELLITE IMAGES MOV SW». El del 08-11 13:40Z dice «VA DETECTED IN VIS
SATELLITE IMAGERY». El del 13-11 14:30Z, con un piloto reportando ceniza, dice que no hay indicio en satélite.

Tres consecuencias, que valen sobre todo para el 25-10:

1. **Tamaño.** La franja mide medio píxel infrarrojo de GOES de ancho. Las otras escenas muestran nubes separadas
   de 1 a 2,5 km. Nada de eso llena un sector de ±30° ni una franja de 6 km.
2. **Contraste.** En el térmico de 100 m de Landsat la franja no se distingue sobre la nieve; sólo asoma como
   lengua fría sobre el terreno sin nieve del extremo (lectura visual del verificador). Los perfiles del revisor dan
   271,1 a 272,7 K dentro contra 273,3 a 276,8 K a los lados (SOSPECHA: es el producto de temperatura de superficie,
   sobre terreno no uniforme). En onda corta el contraste es mayor: la reflectancia de 2,2 µm sube de 0,02 a 0,04
   sobre la nieve a 0,10 a 0,11 dentro de la franja, y la del rojo baja de 0,57 a 0,48.
3. **Dirección.** El REAV dice sureste y la franja va al oeste-suroeste. El VAAC dijo suroeste a las 14:40 UTC y
   sur a las 20:40 UTC. H24 midió ese día el sector de 105° a 165°, con la referencia de viento cruzado entre 195° y
   255°: la pluma real cae sobre el borde de la zona que se resta, y nada de ella en el sector medido. Los pulsos
   E1 a E5 se midieron donde la pluma no estaba, al menos a esas dos horas. La dirección de un REAV es un octante
   leído desde una cámara y no es guía segura de dónde está la pluma vista desde arriba.

**Por qué importa la onda corta.** Schmit et al. 2005 (BAMS, sección de bandas): la banda de 1,6 µm de ABI sirve
para «daytime cloud/snow/ice discrimination», y la nieve es brillante en el visible y «darker (absorbing) in both
the 1.6- and 2.2-µm bands». Sobre la nieve de Chillán, una pluma es poco contraste en el visible (gris sobre blanco)
y mucho contraste en 1,6 µm (claro sobre oscuro). ABI tiene la banda de 1,6 µm (C05) a 1 km y la de 2,2 µm (C06) a
2 km. Ojo: una nube de gotas de agua también es clara ahí. Sirve para ver que algo sale del cráter, no para decir
que es ceniza.

**Lo que dijeron los analistas del VAAC Buenos Aires (CONFIRMADO, `h21_vaac/resultados/avisos_texto.txt`).** De 30
avisos para Chillán del 25-10 al 14-11, en 16 dicen ver ceniza en satélite y en 14 no la identifican. De los 16,
11 la califican de "LIGHT", "FAINT" o "WEAK" y sólo 5 no llevan calificativo. De los 14 sin ceniza, 7 tienen cámara,
piloto u OVDAS diciendo que había emisión. El 27 y el 28-10 dibujaron plumas de más de 120 km; H24 midió de 4 a
25 km. Sólo un aviso nombra la banda (el visible). Lectura: un analista entrenado, mirando la imagen, ve algo tenue
la mitad de las veces. Ninguna prueba nuestra reprodujo lo que el analista miró.

**Térmico fino sin mirar.** ECOSTRESS (70 m, con bandas en 8,8, 10,5 y 12,1 µm) pasó el 25-10 a las 17:35:55 UTC, 11
minutos después del máximo de 2.300 m, y el 08-11 a las 19:28 UTC. EMIT (espectrómetro de 60 m) pasó el 08-11 a las
19:28:49 UTC. Piden cuenta gratuita de Earthdata. Dirían si la ceniza tiene firma de ventana partida cuando el
píxel sí la resuelve. Eso separa "el problema es el tamaño del píxel" de "el problema es la ceniza".

**Literatura: que el observatorio vea lo que el satélite no, es la regla.** Carn y Krotkov (capítulo 12 de
*Volcanic Ash*, §1): sólo 31 de 227 erupciones reportadas (14 %) se identificaron después en la imagen
geoestacionaria. Engwell et al. 2021 (p. 13): para eventos chicos con nubes bajas, la observación desde tierra es la
más confiable. Pavolonis y Sieglaff 2020: el uso cuantitativo del visible y del infrarrojo cercano «thus far, is
underexplored».

**Sin dato.** Duración de los pulsos, ancho de la columna, granulometría, posición y rumbo de las cámaras, y si
alguien publicó que las plumas de Chillán de 2016 a 2022 se veían o no desde GOES.

## 4. Qué cambia y qué no de la explicación vigente

**Se sostiene:**
- VOLCAT no publica Chillán por una firma de ceniza absoluta en el píxel (H14, H20a).
- El seguimiento por distancia explica las continuaciones (H28).
- Con el infrarrojo de 2 km y el fondo de la cumbre, una pluma a ras de cumbre no se separa (H23), y la literatura
  lo respalda.

**Conviene corregir en `POR_QUE_VOLCAT_VE_Y_NOSOTROS_NO.md` (este PR no lo toca):**

| Dónde | Dice | Debería decir |
|---|---|---|
| §1, "el fenómeno" | la huella queda igual o más tibia que el cielo despejado | con base despejada queda 0,81 K más fría (revisión S19e, ya anotada en §3.9) |
| §1 | la puerta de nacimiento mide contraste de forma y borde, no firma de ceniza | mide contraste espectral contra el entorno, sin exigir diferencia negativa |
| §1 | la regla de nacimiento no está en ningún registro público | no está la lógica; los parámetros y la base de criterios sí |
| §1 | "con nuestro IR no hay señal que medir en esos píxeles" | con la huella exacta y base despejada se mide −0,2 K en la diferencia y −0,8 K en BT11; no está separado del tiempo regional |
| §2, línea 139 | el 10,3 y el 13,3 µm no se usan con ABI para detectar | revisar: el capítulo de 2020 dice que el algoritmo base de GOES-R usa razones β con 10,3 µm, y para VOLCAT lo dudoso es el 13,3 µm (el ATBD de 2012 y el capítulo de 2020 describen cosas distintas) |
| §3.3 | los umbrales por volcán no son públicos | son públicos y generales |
| §3.7, línea 650 | la etapa 3 de H15 no se ejecutó | sí se ejecutó (`lut_h15/etapa3_chillan/INFORME.md`) |
| en general | "van 28 pruebas" | son cuatro familias; hasta el 21-11, sin control positivo |

## 5. Pruebas propuestas, en orden

Ninguna se ejecutó. Cada una lleva criterio escrito antes de medir. El orden pondera cuánto decide contra cuánto
cuesta. H29 (otra sesión) mide la pluma del 08-11 lejos del cráter: las pruebas 1 y 2 no la duplican, porque miran junto
al cráter y otros días; la escena de Sentinel-2 del 08-11 14:53 UTC le puede servir a H29.

| # | Qué mide | Datos | Costo | Qué la confirma o la descarta |
|---|---|---|---|---|
| 1 | **Huella conocida.** Proyectar a la grilla de ABI (con paralaje) la franja de Landsat del 25-10 14:34 UTC y medir en el cuadro de GOES-19 de ese minuto: C02 a 0,5 km, C05 a 1 km, C06, C07 en reflectancia, y C13, C14, C15. Fondo: los mismos píxeles a la misma hora en días despejados anteriores al 24-10. Las tres escenas de Sentinel-2 (29-10, 08-11, 13-11) se miden igual, como apoyo: no se sabe si son ceniza | Ventanas de L1b desde S3 (decenas de MB); recortes de Landsat y Sentinel-2 ya hechos | 4 a 6 horas | Decide el 25-10. Confirma que GOES puede ver una pluma con ceniza si alguna banda reflejada separa la franja del fondo. Cierra la vía infrarroja de mañana, con verdad independiente, si ni C14 ni la diferencia se mueven |
| 2 | **El cráter a la hora del pulso, en reflejado y de tarde.** C02 y C05 de GOES-19 a resolución nativa sobre el cráter y 10 km a la redonda, en los pulsos de día con cielo despejado, con la hora de barrido corregida (+8 min 39 s). Primero la tarde del 28-10 (17:38, 20:32 y 21:49 UTC), que VOLCAT marcó en casi todos los cuadros y es el caso que no entendemos; después 25-10 y 27-10. Buscar franja hacia el rumbo 174° y sombra opuesta al sol. No necesita fondo de otros días: el contraste es espacial | Ventanas de L1b (menos de 200 MB) | 3 horas | Confirma: rasgo que sale del cráter en los cuadros del pulso y ausente en los cuadros previos. Descarta: nada en ningún pulso alto, ni a 0,5 km ni en 1,6 µm |
| 3 | **Lo mismo desde GOES-18.** C02 de GOES-18 en esos pulsos: una columna de 2 km debería sobresalir 3 a 4 píxeles de la cumbre. Con GOES-19 da altura por estéreo | Ventanas de L1b de `noaa-goes18` (menos de 300 MB) | 3 horas | Confirma: rasgo radial sobre la cumbre sólo en cuadros con pulso. Si no asoma, la columna es más angosta que 0,5 km o muy tenue |
| 4 | **Prueba de existencia en el infrarrojo, con fondo limpio.** Para las huellas de evento y para los sectores del REAV: diferencia 11 menos 12 µm y BT11 contra la distribución de esos mismos píxeles en días despejados anteriores al 24-10, a la misma hora. Unidad de decisión: el día. Lo mismo en Antuco y Longaví para descontar el tiempo regional | Cubos de H23 y archivos de evento, sin descarga | Medio día | Confirma: corrimiento negativo en Chillán que no está en las cumbres de control. Descarta: Antuco y Longaví se mueven igual |
| 5 | **Repetir H3, H12 y H13 sin los tres defectos.** Control de días anteriores al 24-10, pareo por temperatura esperada, huella de evento (14-11), estadístico de mínimo o percentil 10 en vez de mediana, y un control positivo que pinte una capa de emisividad 0,15 sobre la huella | Cachés de H13 y cubos de H23, sin descarga | Medio día | Si la capa pintada no se recupera con el método original, esos veredictos se retiran por falta de poder. Si con el método corregido tampoco hay señal, quedan firmes |
| 6 | **Serie cuadro por cuadro en el cráter.** BT11 y diferencia de los píxeles de cumbre y sus vecinos (0 a 4 km) para los 14 pulsos, con la hora real de barrido, y control positivo con una bocanada de 1 a 2 km en uno o dos cuadros | Cubos existentes | 2 a 3 horas | Dice si la explosión del 27-10 queda "sin firma" o "sin poder" |
| 7 | **Nacimiento por crecimiento vertical del 13-11, hecho bien.** El verificador ya lo leyó en bruto (3,6 K a 10 km o menos del cráter; nube de 237 K media hora antes). Falta medirlo como lo define el artículo: temperatura mínima del objeto, siguiendo el objeto entre cuadros, en la huella del archivo de evento | Cubos de H23 y archivo de evento, sin descarga | 1 a 2 horas | Si el objeto que VOLCAT siguió es la nube convectiva, ese nacimiento es tiempo meteorológico y el 13-11 sale de la lista de eventos de pluma |
| 8 | **La puerta de VOLCAT en los cuatro nacimientos.** Los estadísticos que nombran los registros (diferencias entre bandas del objeto contra su entorno) en los cuadros de nacimiento y en los mismos píxeles y minutos de días sin evento | Cachés de C07, C11, C14, C15 y archivos de evento | 2 a 4 horas | Dice cuál de las tres lecturas del −1,26 K se descarta. Con cuatro nacimientos no decide sola |
| 9 | **¿La altura VOLCAT es una medición?** Para cada píxel publicado: altura del nivel GFS cuya temperatura es la BT11 más el margen de la configuración, contra la altura publicada. Control: la nube espesa de Mauna Loa | Archivos de evento y GFS en caché | 1 a 2 horas | Si la dispersión es menor que 0,3 km, la altura es un termómetro del suelo y hay que rotularla así en el dashboard |
| 10 | **Térmico de 70 m.** Temperatura de brillo por banda y diferencia 10,5 menos 12,1 µm de ECOSTRESS del 25-10 17:35 y del 08-11 19:28 UTC, dentro y fuera de la pluma | Tres archivos con cuenta gratuita de Earthdata (registrar la credencial antes; revisar tamaño: quedan ~14 GB en D:) | Medio día | Diferencia negativa de más de 1 K dentro de la pluma: la ceniza tiene firma y el problema es el tamaño del píxel. Sin diferencia ni a 70 m: el problema es la ceniza (gruesa, húmeda o poca) |
| 11 | **Inyección con cobertura parcial.** Repetir la inyección de H23 con la pluma llenando 10, 20 y 50 % del píxel y emisividades de 0,5 y 0,9 | Cubos de H23 | Medio día | Da el límite real para una pluma densa y angosta |
| 12 | **Descifrar las columnas sin rótulo de la base de criterios** cruzándolas con lo que los registros imprimen por objeto en Kirishima, Fuego y Mauna Loa | En disco (`D:\goes_notas\`) | Medio día a un día | Una asignación vale si predice el veredicto de un caso que no se usó para deducirla |
| 13 | **¿Se corrió el fondo con la erupción?** Anomalía de BT11 y de la diferencia por píxel alrededor del cráter antes y después del 24-10, y albedo de Sentinel-2 por píxel de ABI | Cubos de H23, recortes de Sentinel-2 | Medio día | Si el albedo cambió más de 0,1 en los píxeles del sector, las líneas base de H24 para esos píxeles quedan en duda |
| 14 | **Verano** (ya registrada en `h24_verano/REGISTRO_PROSPECTIVO.md`): sin nieve el suelo se calienta de día y el contraste crece | Enero de 2027 | El ya previsto | Sin cambio; ahora tiene además razón física |

## 6. Gestiones que no son pruebas

**Al OVDAS (las puede pedir Nicolás):**
1. La serie de imágenes de las cámaras Arauco, Portezuelo y Andarivel con hora al segundo para los instantes con
   imagen fina desde el espacio: 24-10 14:53 y 18:24; 25-10 14:34 y 17:36; 28-10 16:51; 29-10 14:53 y 16:03; 08-11
   14:53 y 19:28; 13-11 14:53; 14-11 09:47 (UTC).
2. Posición, rumbo y campo de visión de cada cámara. Sin eso, la dirección del REAV no se puede pasar a azimut.
3. La lista interna de pulsos con hora de inicio y de término, sobre todo del 13 al 18-11.
4. Cómo se midió la altura en cada REAV (cámara con escala o VOLCAT).
5. Si hay muestras de caída de octubre y noviembre con granulometría.

**A Pavolonis (para el correo pendiente):**
1. Cuando un evento nace como `ASHPLUMEPUFF` con probabilidad de píxel casi nula, ¿qué prueba decide: el contraste
   espectral contra el entorno, la tendencia temporal, o las dos? ¿Con qué umbral?
2. ¿Qué significan las columnas posteriores a los pares de robustez en las filas de ceniza que no exigen
   probabilidad?
3. ¿Chillán estuvo en la lista de volcanes activos en octubre y noviembre de 2026? ¿Qué cambia esa lista para la vía
   pluma?
4. Con emisividad muy baja, ¿la altura publicada es en la práctica el valor de partida? ¿Hay una bandera que lo diga?
5. ¿Han visto que la prueba de contraste local pase de forma persistente sobre cumbres con nieve o con ceniza
   depositada?
6. ¿El flujo experimental v3r4 ya usa el bosque aleatorio nuevo para plumas de ceniza?
7. Permiso para usar los archivos de evento de Chillán y la configuración pública en un informe interno.

**Al VAAC Buenos Aires:** qué producto miraron en los avisos 2026/034, 035, 038 y 039 (27 y 28-10, plumas de más de
120 km) y en el 047.

**A NOAA, por el VAAC:** un sector de mesoescala de GOES-19 sobre Chillán durante unas horas de actividad. Daría el
visible de 0,5 km y el infrarrojo cada minuto: es la única forma de ver un pulso nacer, subir y diluirse desde
GOES-19.

## 7. Verificación adversarial

Un verificador que no leyó los informes de los revisores recibió 22 afirmaciones con su fuente, escribió primero por
dónde podía estar mal cada una y después las comprobó contra los archivos. Resultado: **12 confirmadas, 10
confirmadas en parte, ninguna refutada**. Este documento ya incorpora sus correcciones. Las que cambiaron el texto:

| Afirmación | Veredicto | Qué cambió |
|---|---|---|
| Señal de una pluma que llena parte del píxel | En parte | Las celdas que se destacaban eran de suelo frío. De tarde el suelo está a 280 a 288 K y "pluma angosta" no alcanza (§1 y §3.2) |
| Corrimientos chicos, todos hacia ceniza | En parte | Hay mediciones del mismo proyecto con el signo contrario, y las que coinciden comparten días (§3.4) |
| El evento del 13-11 nació por crecimiento vertical y nadie lo midió | Confirmada | El verificador lo midió en bruto: 3,6 K, no 10 K, con convección alrededor. Puede ser tiempo meteorológico (§3.3) |
| Controles "sin pluma" en días con actividad | Confirmada | Los conteos son exactos; la contaminación real puede ser chica (§3.4) |
| El pareo por temperatura borra la señal | En parte | Vale para el cielo empírico. El cuadro con pluma sale más tibio que su control en 26 de 37 pares: no había enfriamiento que borrar (§3.4) |
| La huella corrida alimenta once pruebas sin repetir | En parte | Cierto, pero la pregunta se volvió a medir con la huella exacta y tampoco separó (§3.4) |
| Cuatro escenas finas muestran la pluma | En parte | Sólo la del 25-10 tiene aspecto de pluma con ceniza; las otras pueden ser vapor o cúmulos (§3.5) |
| Reparto de los avisos del VAAC | En parte | De los 16 con ceniza vista, 11 la califican de leve, tenue o débil (§3.5) |
| El contraste de −1,26 K de la huella contra su anillo | En parte | Casi todo es permanente; lo que cambia con el evento es 0,1 a 0,2 K (§3.3) |
| La altura de VOLCAT como valor de partida | En parte | El margen documentado es de 15 K, no "chico"; compatible, no demostrado (§3.3) |
| El 10,3 µm y la línea 139 del informe madre | En parte | Son dos descripciones de fechas distintas; la línea se revisa, no se da por falsa (§3.1) |

Confirmadas sin cambio: el estadístico y el control positivo de H24, H25 y H27; la falta de control positivo hasta
H22; el mínimo de la prueba A en la posición corregida; la dirección de la pluma del 25-10 fuera del sector de H24;
los pulsos del OVDAS sin cuadro VOLCAT; lo que dan y no dan los REAV; la base de criterios pública e igual para
Chillán (recontada de forma independiente: 1.561 entradas, 1.558 iguales); VOLCAT a 2 km sin corrección de terreno;
las citas de literatura; y la geometría del píxel (recalculada con `pyproj`: 2,093 por 2,843 km).

Lo que el verificador no pudo comprobar: la salida cruda de la prueba A del 17-11 (insumos perdidos), registros de
VOLCAT de producción para Chillán (sólo hay de paquetes de prueba), si la lista de REAV en disco está completa (otro
revisor la contrastó contra los listados de SERNAGEOMIN), el contenido de las variables de visible del paquete de
Mauna Loa (escena nocturna) y las páginas exactas de Schneider y Rose 1994.

**Límite de este diagnóstico.** Las lecturas nuevas (imágenes finas, enfriamiento del 13-11, recuentos de signo) son
miradas sin criterio escrito antes. Sirven para elegir qué probar. Ninguna cuenta como resultado hasta que se mida
con criterio previo.

## 8. Fuentes

**Del proyecto (rutas desde `docs/own_volcat/`):** `POR_QUE_VOLCAT_VE_Y_NOSOTROS_NO.md`; `h23_inyeccion/INFORME.md`;
`h24_pulsos_reav/INFORME.md`, `criterio_2026-11-22.md` y `scripts/h24_medir.py`; `h25_e6_gfs/INFORME.md`;
`h27_fondo_espacial/INFORME.md`; `h28_regla_seguimiento/INFORME.md`; `eventos_h14/INFORME_H14.md` y `resultados/`;
`h20a_campos_evento/INFORME.md`; `h21_vaac/INFORME.md` y `resultados/avisos_texto.txt`;
`revision_h13_h17_nube/INFORME.md` y `resultados/rev_h17_resultado.txt`; `h3_h7/scripts_h3/`; `beta73/scripts/`;
`temporal_h13/scripts/`; `pruebas_17_18nov/`; `direccion_pluma/`; `vaac_londres/`; `calor_rayos/resultados/frames_calor.csv`;
`lut_h15/etapa3_chillan/INFORME.md`; `reproducir_volcat/`.

**Papers y manuales en el repositorio:** Wen y Rose 1994 (`WenRose_1994_VolcanicCloudParticles.pdf`); Pavolonis 2010
(`Pavolonis_2010_CloudCompositionTheory.pdf`); Heidinger y Pavolonis 2009 (`HeidingerPavolonis_2009_SplitWindowCirrus.pdf`);
Saint et al. 2024 (`Saint_2024_LimitsSatelliteAshRetrievals.pdf`); Pavolonis y Sieglaff 2020
(`Pavolonis_2020_RemoteSensingVolcanicAsh_GOESR_chapter.pdf`); Schmit et al. 2005, Horváth et al. 2021 y PUG L1b
vol. 3 (`docs/papers_links/`).

**En `D:\goes_notas\local_1055cba6\pdfs\`:** SECO Parte 1 y 2 (Pavolonis, Sieglaff y Cintineo 2015a y 2015b);
Pavolonis et al. 2013 y 2018; ATBD de VOLCAT 2025 y CDR 2022 (texto); Kylling et al. 2015; Engwell et al. 2021;
informe mensual de STAR de septiembre de 2026; los 14 REAV y el RAV del 06-11-2026 de SERNAGEOMIN.

**Bajados en esta sesión a `D:\goes_notas\s19\s19i_papers\`:** Schneider y Rose 1994 (USGS Bulletin 2047, p. 405);
Ellrod et al. 2003 (JGR 108, 4356); Pavolonis et al. 2006 (JTECH, manuscrito); Grainger et al. 2013; Kalluri et al.
2018; Schmit et al. 2017; Carn y Krotkov (NTRS 20170003367); RAV de SERNAGEOMIN del 19-11-2026; gráficos de
calibración de NOAA STAR (`star_png\`); página de modos de barrido de goes-r.gov.

**Catálogos y servidores públicos consultados:** STAC de Element 84 (`https://earth-search.aws.element84.com/v1`);
Planetary Computer; CMR de NASA (`https://cmr.earthdata.nasa.gov/search/`); buckets `noaa-goes19` y `noaa-goes18`;
servidor de SSEC (`https://bin.ssec.wisc.edu/pub/volcat/`) y página del autor (`https://www.ssec.wisc.edu/~mpav/`);
`https://rnvv.sernageomin.cl/eav`.

**De SSEC, fuera del repositorio:** `D:\goes_notas\s19\s19i_ssec_config\` (base de criterios y configuración; uso
interno, a reserva de la autorización pedida a Pavolonis).

## 9. Lo que no se miró

- Los boletines del Smithsonian GVP (el sitio pide verificación de navegador).
- El texto completo de Prata 1989, Prata y Grant 2001, Simpson et al. 2000, Tupper et al. 2004 y Rose et al. 1995
  (bloqueo de las editoriales); lo que se dice de ellos viene de quien los cita.
- La función de dispersión puntual de ABI con números y los pesos del remuestreo: no son públicos.
- Las presentaciones grandes de la página del autor de VOLCAT (2023 y 2024) y el material de capacitación.
- Las pasadas de MODIS y de SLSTR.
- Ninguna imagen de GOES-19 se comparó con las de Sentinel-2 y Landsat: esa es la prueba 1.
- Los scripts de H14 a H21, H26 y H28 no se leyeron línea por línea; lo que la tabla de método dice de ellos viene
  de sus informes.
