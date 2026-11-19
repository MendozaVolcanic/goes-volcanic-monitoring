# Prueba tolerante del London VAAC en Nevados de Chillán (nov-2026): no cumple

Fecha: 19-11-2026. Criterio escrito y commiteado antes del primer número (commit 3541ac9):
`C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\Goes\docs\own_volcat\vaac_londres\criterio_2026-11-19.md`.
No se cambió después de medir. Todo número de este informe sale de los archivos de
`C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\Goes\docs\own_volcat\vaac_londres\resultados\`
(`analisis.log`, `vara.csv`, `pareado.csv`, `pares.csv`, `diagnostico.csv`, `por_scan.csv`, `verificar.log`).

## 1. Respuesta corta, para geólogo

**Veredicto: no cumple.** El método del London VAAC completo (Francis et al. 2012, con los umbrales
publicados) detecta 2 de los 35 cuadros VOLCAT de prueba, y ninguno de sus píxeles cae dentro de la
huella VOLCAT. Ninguna de las otras 11 configuraciones declaradas cumple la vara del 17-11 tampoco.

**La física, en tres frases.**
1. La prueba tolerante (BT10,8 − BT12) + (BT10,8 − BT8,7) < +1,5 K sí "siente" algo dentro de la pluma:
   la suma baja unos 0,4 K respecto del mismo lugar en un día sin pluma, sobre todo por el término de
   8,4 µm, en la dirección que predice la ceniza. Sin filtros, la prueba marca la huella más que el mismo
   lugar en un día sin pluma (21 % contra 8 % de los píxeles).
2. Pero esa baja es chica frente a lo que hace el paisaje: en un día sin pluma, la nieve y las nubes del
   disco de 10 km ya ponen bajo +1,5 K a uno de cada cuatro píxeles. La prueba sola marca entre 250 y
   2.200 píxeles por escena negativa en promedio y da falsas alarmas en un tercio a dos tercios de los
   scans sin pluma.
3. Los dos filtros que el método trae para limpiar eso borran la pluma junto con las nubes. El filtro β
   necesita que la pluma esté más fría que el cielo despejado, y la de Chillán está igual o más tibia, así
   que su β no se puede medir. La coherencia 3 × 3 exige manchas de 3 × 3 píxeles, y la huella es más
   chica que eso.

**Qué no es.** No es la banda: con C13 (10,3 µm) en vez de C14 (11,2 µm) el resultado es el mismo. No es
la temperatura de referencia del filtro β: 255 K y 215 K dan lo mismo.

## 2. El método y la adaptación

Umbrales tomados del texto completo de Falconieri et al. 2018 (Sensors 18, 369, doi:10.3390/s18020369,
§3.2, Ec. 4 a 7; XML de Europe PMC PMC5855105), que describe las cinco pruebas de Francis, Cooke y
Saunders 2012 (JGR, doi:10.1029/2011JD016788). El paper de Francis no se pudo leer (editorial bloqueada,
sin copia abierta encontrada):

1. Definitiva: BT10,8 − BT12,0 < −2,0 K.
2. Tentativa: (BT10,8 − BT12,0) + (BT10,8 − BT8,7) < 1,5 K.
3. Tentativa: −2,0 ≤ BT10,8 − BT12,0 ≤ −0,7 K.
4. Filtro β sobre las tentativas: fuera si β(8,7/10,8) ≤ 0,7, o ≥ 1,2, o si
   β(12,0/10,8) > 4,2645 − 5,823·β(8,7/10,8) + 2,446·β(8,7/10,8)².
5. Coherencia 3 × 3: 6 o más de 9 píxeles con ceniza.

Bandas ABI: 8,7 → C11 (8,4 µm); 12,0 → C15 (12,3 µm); 10,8 → C14 (11,2 µm, principal) o C13 (10,3 µm).
Sin RTM ni GFS: cielo despejado empírico (mismo slot ±10 min en los 10 días previos, mediana de los 3
más tibios en C14), cubierto a T_ref fija (255 K principal, 215 K sensibilidad), ε y β con
`src/process/beta_ratios.py`, coeficientes Planck del NetCDF L1b (C13 bajada para esta prueba: 1.204
scans, 0 fallas). Detalle completo de la adaptación y de por qué cada elección, en el criterio.

## 3. Resultados contra la vara del 17-11

Mismos conjuntos y misma foto fija que el detector de plumas débiles: positivos 21 de ajuste (08 y
10-11) y 35 de prueba (11 y 14-11); negativos 180 de ajuste (01 a 06-11) y 120 de prueba (09, 12, 13 y
15-11), a 20 min; 23 scans del 16-11. El L1b de 08-11 21:00 UTC sigue faltando (igual que el 17-11).

Notación: "aj" = ajuste, "pr" = prueba. FA = scans negativos con objeto anclado, con el peor día entre
paréntesis. Coinc. = fracción de nuestros píxeles a ≤ 30 km del cráter que caen en la huella VOLCAT
dilatada (entre paréntesis, cuántos píxeles). Px/scan neg = píxeles marcados en toda la ventana
(83 × 94 = 7.802) por scan negativo, promedio. Cumple = criterios 1, 2, 3 y 4 (S sí, n no).

| Configuración | Sens. aj | Sens. pr | FA aj (peor día) | FA pr (peor día) | 16-11 | Coinc. aj | Coinc. pr | Px/scan neg aj / pr | Cumple aj / pr |
|---|---|---|---|---|---|---|---|---|---|
| L0 C14 (pruebas 1 a 3, sin filtros) | 18/21 (86 %) | 29/35 (83 %) | 91/180 (29) | 76/120 (27) | 19/23 | 23 % (446) | 23 % (902) | 1.092 / 2.224 | Snnn / Snnn |
| L1 C14 (L0 + coherencia) | 2/21 | 8/35 (23 %) | 57/180 (22) | 55/120 (25) | 18/23 | 26 % (80) | 8 % (437) | 681 / 1.862 | nnnn / nnnn |
| **L2 C14 T255 (principal)** | **0/21** | **2/35 (5,7 %)** | **1/180 (1)** | **3/120 = 2,5 % (2)** | **0/23** | **sin px** | **0 % (82)** | **4,6 / 15,3** | **nSSn / nnSn** |
| L3 C14 T255 (β no medible se conserva) | 0/21 | 2/35 | 1/180 (1) | 4/120 (3) | 0/23 | 0 % (1) | 1 % (83) | 4,6 / 16,9 | nSSn / nnSn |
| L2 C14 T215 | 0/21 | 1/35 | 0/180 (0) | 4/120 (4) | 0/23 | sin px | 0 % (32) | 2,8 / 8,2 | nSSn / nnSn |
| L3 C14 T215 | 0/21 | 1/35 | 0/180 (0) | 5/120 (5) | 0/23 | 0 % (1) | 3 % (33) | 2,9 / 9,7 | nSSn / nnSn |
| L0 C13 | 19/21 (90 %) | 17/35 (49 %) | 56/180 (30) | 40/120 (24) | 8/23 | 23 % (459) | 57 % (262) | 255 / 398 | Snnn / nnnS |
| L1 C13 | 5/21 (24 %) | 4/35 (11 %) | 17/180 (13) | 5/120 (2) | 0/23 | 21 % (99) | 94 % (33) | 85 / 161 | nnSn / nnSS |
| L2 C13 T255 | 0/21 | 0/35 | 0/180 | 0/120 | 0/23 | sin px | sin px | 1,9 / 0,7 | nSSn / nSSn |
| L3 C13 T255 | 1/21 | 3/35 (8,6 %) | 0/180 | 1/120 (1) | 0/23 | 20 % (80) | 100 % (20) | 2,0 / 43,1 | nSSn / nSSS |
| L2 C13 T215 | 0/21 | 0/35 | 0/180 | 0/120 | 0/23 | sin px | sin px | 2,8 / 0,9 | nSSn / nSSn |
| L3 C13 T215 | 1/21 | 3/35 (8,6 %) | 0/180 | 1/120 (1) | 0/23 | 20 % (80) | 100 % (24) | 3,2 / 43,5 | nSSn / nSSS |

**Según el criterio:**
- **Principal (L2, C14, 255 K): no cumple.** En prueba falla la sensibilidad (5,7 % contra 50 %), la falsa
  alarma por un scan (2,5 % contra 2 %; peor día 2, dentro del tope de 3) y la coincidencia (0 de 82
  píxeles en la huella). Cumple el 16-11. Las dos "detecciones" de prueba (14-11 22:30 y 22:40 UTC) son
  un sistema nuboso de 62 y 82 píxeles que pasa por el cráter, con 0 píxeles en la huella VOLCAT.
- **Ninguna otra configuración cumple las cuatro en prueba.** La más cercana, L3 con C13, cumple tres
  (falsa alarma, 16-11 y coincidencia del 100 %), pero ve 3 de 35 cuadros con 20 a 24 píxeles en total.
  Con eso no hay "variante que cumple, a confirmar".
- **Sin filtros (L0), la prueba es sensible pero ciega al lugar:** 83 a 86 % de los cuadros con C14,
  a cambio de falsas alarmas en 51 % (ajuste) y 63 % (prueba) de los scans sin pluma, días con 27 a 29, y
  19 de 23 scans del 16-11.

## 4. Control pareado por píxel: ¿marca la pluma o el lugar?

52 positivos con huella de 3 o más píxeles; 45 con control (426 píxeles de huella), 7 sin control porque
el día sin pluma más parecido en BT C14 quedó a más de 3 K (3,1 a 5,3 K). Diferencia mediana de BT C14
entre positivo y control: 0,84 K. Los controles salieron casi todos del 13-11 (23) y del 12-11 (15).

| Configuración | P (huella marcada, positivo) | C (mismos píxeles, control) | P − C |
|---|---|---|---|
| L0 C14 | 21,4 % | 8,5 % | **+0,13** |
| L1 C14 | 2,6 % | 0,7 % | +0,02 |
| L2 C14 T255 (principal) | 0 % | 0 % | 0,00 |
| L3 C14 T255 | 0 % | 0,2 % | 0,00 |
| L0 C13 | 20,0 % | 1,6 % | **+0,18** |
| L1 C13 | 5,2 % | 0 % | +0,05 |
| L3 C13 (T255 y T215) | 5,2 % | 0 % | +0,05 |
| L2 C13 (T255 y T215), L2 y L3 C14 T215 | 0 % | 0 a 0,2 % | 0,00 |

**Lectura según el criterio** (P − C < 0,10 = no distingue la pluma del lugar): sólo la prueba tolerante
sin filtros (L0) pasa ese umbral, con C14 (+0,13) y con C13 (+0,18). Es de las pocas señales IR por
píxel de esta serie que separan algo la huella del mismo lugar sin pluma: la ΔBTD sola daba AUC 0,50
(prueba B del 17-11), y la otra es el indicio nocturno de β(7,3/11) en H3, posterior a su criterio. Pero marca uno de cada cinco píxeles de la huella, y en cuanto entran la coherencia o el filtro β
la separación cae a 0,05 o menos.

## 5. La física: qué hay dentro de la huella

Percentiles 5 / 25 / 50 / 75 / 95 en K (`diagnostico.csv`). S = suma de la prueba 2; BTD = BT10,8 − BT12;
d87 = BT10,8 − BT8,7. "% S < 1,5" es la fracción que dispara la prueba 2.

| Conjunto | 10,8 µm | Px | S | % S < 1,5 | BTD | d87 |
|---|---|---|---|---|---|---|
| Huella, positivos | C14 | 520 | 0,58 / 1,64 / **2,32** / 2,92 / 4,23 | 21 % | 0,18 / 0,69 / 0,98 / 1,44 / 2,07 | −0,11 / 0,80 / **1,31** / 1,76 / 2,43 |
| Huella, control pareado | C14 | 426 | 1,24 / 2,12 / **2,74** / 3,49 / 4,67 | 8 % | 0,38 / 0,81 / 1,10 / 1,52 / 2,16 | 0,53 / 1,26 / **1,65** / 2,03 / 2,63 |
| Disco 10 km, negativos | C14 | 15.900 | −0,16 / 1,50 / 2,30 / 3,16 / 4,75 | 25 % | 0,34 / 0,64 / 1,12 / 1,69 / 2,73 | −1,65 / 0,60 / 1,38 / 1,84 / 2,55 |
| Huella, positivos | C13 | 520 | 0,99 / 1,61 / **2,11** / 2,86 / 3,88 | 19 % | 0,13 / 0,50 / 0,93 / 1,39 / 2,21 | 0,43 / 0,90 / 1,18 / 1,53 / 2,19 |
| Huella, control pareado | C13 | 426 | 1,65 / 2,18 / **2,66** / 3,35 / 4,50 | 2 % | 0,44 / 0,74 / 1,10 / 1,55 / 2,36 | 0,94 / 1,33 / 1,58 / 1,91 / 2,56 |
| Disco 10 km, negativos | C13 | 15.900 | 1,46 / 2,06 / 2,76 / 3,60 / 5,12 | 6 % | 0,29 / 0,72 / 1,33 / 2,07 / 3,95 | 0,06 / 1,02 / 1,44 / 1,81 / 2,41 |

1. **La pluma baja la suma, y la baja por el 8,4 µm.** Mediana de S en la huella 2,32 K contra 2,74 K
   en el control (C14): −0,42 K. Las medianas de sus dos términos bajan 0,34 K en d87 (1,31 contra 1,65)
   y 0,12 K en la BTD (0,98 contra 1,10). Es la dirección que predice la ceniza (absorbe menos a 8,4 µm que a 11 µm, así que
   la BT de 8,4 µm queda relativamente más tibia), pero también la de un aerosol o una nube delgada que
   tapa la caída de emisividad del suelo silicatado a 8,4 µm. Con estos datos no se puede separar.
2. **El suelo despejado ya da S de 2 a 3 K.** En el control, el 75 % de los píxeles tiene S > 2,1 K: el
   suelo volcánico emite menos a 8,4 µm que a 11 µm (lo anticipado en el criterio), así que el umbral de
   +1,5 K, calibrado sobre el Atlántico Norte, queda debajo del fondo. Una baja de 0,4 K sólo lleva bajo el
   umbral la cola de la huella (21 %).
3. **El disco sin pluma tiene una cola baja que la huella no tiene.** Con C14, el percentil 5 del disco
   en días negativos es −0,16 K y el de d87 es −1,65 K: nubes y nieve. Ahí está el 25 % de píxeles que
   dispara la prueba en días sin pluma, más que en la huella (21 %). Con C13 esa cola casi desaparece
   (6 %) y la huella queda igual (19 %); por eso L0 C13 separa mejor (P − C de +0,18) y tiene la mitad de
   falsas alarmas. A 10,3 µm el vapor de agua absorbe menos y el contraste de emisividad con el 8,4 µm del
   suelo y de las nubes cambia; cuál de los dos pesa más no está medido.
4. **El filtro β no confirma esta pluma.** Con C14 a 255 K, dentro de la huella hay 23 píxeles
   tentativos en ajuste y 84 en prueba. El β es medible en 20 y 29 de ellos, pasa el filtro en 8 y 12, y
   después de la coherencia quedan 0 y 0. En prueba (14-11, la pluma más tibia) dos de cada tres
   tentativos no tienen β medible: es lo mismo que vio H3, la pluma queda igual o más tibia que el cielo
   despejado empírico, ε(10,8) < 0,02, y sin nube medible no hay razón β. En los días negativos, en
   cambio, el β es medible en casi todos los tentativos (son nubes) y la rama del polinomio β(12/10,8)
   saca entre el 75 % y el 94 % de ellos según la configuración (83 a 84 % con C14 a 255 K;
   `analisis.log`, bloque "FILTRO BETA"). El filtro hace su trabajo con las nubes y no tiene con qué
   confirmar la pluma.
5. **La coherencia 3 × 3 borra lo que queda.** Pasar de L0 a L1 baja la fracción de huella marcada de
   21 % a 2,6 % (C14): las huellas son de pocos píxeles ABI de ancho y casi nunca juntan 6 de 9 marcados
   alrededor de un píxel. Esa prueba se pensó para nubes distales grandes.

## 6. Verificación

`verificar.py` rehace todo a mano y por píxel (Planck propio, cielo despejado propio, filtro β sin
`beta_ratios.py`, coherencia 3 × 3 y objetos 8-conexos con bucles) para L0, L2 y L3 con C14 a 255 K, en
los 56 positivos y en uno de cada tres scans negativos y del 16-11 (164 scans, 492 cotejos). Resultado
en `verificar.log`: **la detección por scan coincide en los 492; el número de píxeles difiere en 2**, el
mismo scan (13-11 19:00 UTC, negativo, sin objeto anclado) en L2 y L3: 34 contra 35 píxeles.

La causa está identificada y no es un error de lógica: la radiancia L1b viene cuantizada, así que dos
días candidatos pueden tener exactamente la misma BT C14 en un píxel (277,3634 K dos veces, por ejemplo).
"Los 3 más tibios" queda entonces empatado, y `argsort` de numpy y el `sort` de Python desempatan
distinto: en ese scan 17 de 7.802 píxeles toman otro candidato para C11 y C15. Uno de ellos cae en la
caja 3 × 3 de un píxel que queda con 5 vecinos marcados en un cálculo y 6 en el otro. No cambia ninguna
detección; en las tablas sólo movería el promedio de píxeles por scan negativo de prueba en menos de
0,01.

## 7. ¿Llevarlo a `detect_ash_enhanced`?

**No se propone.** El criterio pedía la propuesta sólo si cumplía, y no cumple. Dos notas para no perder
lo aprendido:
- La "tri-espectral" de `detect_ash_enhanced` es (BT8,4 − BT11,2) + (BT12,3 − BT11,2) < 0, o sea
  S > 0 con la notación de arriba. Es la misma suma que la prueba 2 del London VAAC con la desigualdad al
  revés: allá sirve para aceptar más (S < 1,5), acá para rechazar. No son equivalentes y no hay que
  citarlas como tales.
- Lo que sí vale como dato físico es el punto 1 de §5: dentro de la huella, la suma S baja ~0,4 K
  respecto del mismo lugar sin pluma, y casi todo viene del 8,4 µm. La prueba B del 17-11 miró
  Δ(BT8,5 − BT11) contra un nulo nublado y se dio por falsada (AUC 0,26, con la salvedad de ese nulo); aquí, con el control
  pareado por BT C14, el mismo término sí se mueve. Si alguien quiere seguir esa pista, necesita un
  criterio nuevo escrito antes, con el control pareado como referencia y no un umbral absoluto.

## 8. Qué no se midió

- Episodios de octubre (25, 28 y 29-10), incluido el nocturno del 29-10: sus huellas no están en la
  grilla del caché y la vara del 17-11 no los incluye.
- Un RTM y el GFS para el filtro β (como en el método original con RTTOV): H3 ya mostró que con cielo
  modelado el error de terreno en la cumbre domina la compuerta ε, así que no se esperaba ganancia.
- Recalibrar el +1,5 K a las bandas del ABI: sería ajustar el umbral a la verdad que se quiere medir.

## 9. Archivos

- Criterio: `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\Goes\docs\own_volcat\vaac_londres\criterio_2026-11-19.md`
- Scripts: `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\Goes\docs\own_volcat\vaac_londres\scripts\`
  (`rutas.py`, `fetch_c13.py`, `analisis.py`, `verificar.py`). Orden: `python fetch_c13.py 16`,
  `python analisis.py`, `python verificar.py`.
- Resultados: `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\Goes\docs\own_volcat\vaac_londres\resultados\`.
- Datos de entrada (no versionados): caché C11/C14/C15 y huellas del detector del 17-11 en
  `C:\Users\nmend\AppData\Local\Temp\claude\d6ea8719dcf88502\536a0873-47fb-4b33-9ee5-de0197c3f321\scratchpad\det\`;
  C13 de esta prueba en
  `C:\Users\nmend\AppData\Local\Temp\claude\470cdb238f003f8e\1985b7fb-c655-4e72-b95c-8d201d1a842a\scratchpad\vaac\cache13\`.
  Son carpetas temporales: si se borran, `fetch_c13.py` y los scripts del 17-11 los rehacen desde S3.
