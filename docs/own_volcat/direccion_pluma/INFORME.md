# H10: ¿la huella VOLCAT de Chillán está donde el OVDAS vio la pluma?

Fecha: 19-11-2026. Criterio commiteado antes del primer número:
`docs/own_volcat/direccion_pluma/criterio_H10_direccion_pluma_2026-11-19.md` (commit 002640b).
Salidas crudas: `direccion_resultado.txt`, `senal_resultado.txt` y `resultados/` en esta carpeta.
Scripts: `scripts/` (orden de corrida: `direccion_volcat_h10.py`, `fetch_gfs_viento_h10.py`,
`tabla_direccion_h10.py`, `senal_h10.py`; `mosaico_h10.py` es sólo control visual).

## 1. Respuesta corta, para geólogo

**Veredicto de H10 según el criterio: no concluyente, con dos jornadas, y con un indicio a favor.**

- **El viento del modelo sí va hacia donde el OVDAS vio la pluma.** En los 7 REAV con viento de más de
  3 m/s, la dirección GFS al nivel de la columna queda a 3 a 36° de la que da el REAV (en uno, 62°).
  Sólo falla con calma (menos de 1,1 m/s, la mañana del 25-10). Esto importa porque deja al GFS como
  referencia creíble para los días sin dirección en el REAV.
- **La huella VOLCAT no sigue a esa pluma de manera clara.**
  - 25-10, la única jornada con 5 escenas comparables: el OVDAS vio la columna hacia el SE, el viento iba
    hacia el SE (136°) y la huella VOLCAT quedó **al sur** (181°), a 45 a 47° de ambos. Cae justo en el
    borde del umbral de coincidencia (45°): no concluyente.
  - 28-10 por la tarde: el OVDAS vio la columna hacia el **NO** y el viento iba hacia el N; el único
    cuadro VOLCAT anclado de esa ventana tiene la huella **al sur** (170°), a 143 a 170° de ambos. Es lo
    contrario, pero es un solo cuadro y el criterio pide dos.
  - 28-10 al anochecer y 10-11 (REAV sin dirección): el viento iba hacia el NNE y el NE, y la huella quedó
    al SE tal como está dibujada (133° y 115°), o al E si se corrige el paralaje (86° y 66°).
- **Lo que esto sugiere (lectura posterior, no decide).** En las cuatro jornadas la huella queda siempre
  entre el sur y el este del cráter, mientras el viento cambia del norte al sureste. Un objeto que no gira
  con el viento no se comporta como una pluma arrastrada. Parte de ese sesgo al sur sale del paralaje si
  SSEC no corrige su PNG (una pluma a ~5,5 km aparece ~5 km al sur), pero ni con la corrección la huella
  del 28-10 apunta hacia donde soplaba el viento.
- **Buscando donde el OVDAS vio la pluma, el infrarrojo casi tampoco la ve.** En el sector del REAV la
  diferencia 11,2 − 12,3 µm baja 0,2 a 0,4 K respecto del mismo lugar en un día sin pluma (AUC 0,68 el
  25-10 y 0,698 el 27-10; el criterio pedía 0,70) y en el sector opuesto no baja (0,56 y 0,57). Ningún
  píxel llega a −1 K. Según el criterio, **"tampoco ahí"**: la señal no aparece localizada en ninguna
  jornada, aunque en dos queda a menos de 0,02 del umbral.
- **VOLCAT no vio episodios que el OVDAS sí documentó.** El 27-10 (ocho pulsos de hasta 1.640 m hacia el
  N, más columnas de 2.000 m al NO y 960 m al NNE) VOLCAT no dibujó ningún objeto anclado en 42 cuadros.
  El 25-10, con pulsos de 10:41 a 21:16 UTC, dibujó objeto anclado en 5 de los 62 cuadros revisados
  dentro de las ventanas REAV. El
  12-11 (400 m), en ninguno.

**Qué significa para las pruebas anteriores.** No queda probado que hayan medido en el lugar equivocado:
H10 no se pudo decidir con dos jornadas. Pero hay dos señales de alerta: la huella no sigue el viento ni
la dirección vista desde las cámaras cuando esa dirección cambia, y VOLCAT no coincide en el tiempo con
los pulsos documentados. Y aun mirando donde el OVDAS vio la pluma, el split-window da apenas una
tendencia débil. Las dos cosas juntas dicen que el problema no es sólo dónde miramos: la pluma de
Chillán es casi transparente en el infrarrojo térmico también en su sector verdadero, y la huella VOLCAT
no es una buena guía de dónde está.

## 2. Episodios y datos

Episodios: criterio §2 (14 entradas de 15 REAV y el RAV del 06-11, todos públicos). Cinco jornadas con
cuadros VOLCAT revisados: 25-10 (SE), 27-10 (N a NO), 28-10 tarde (NO), y como secundarias 28-10 al
anochecer y 10-11 (sin dirección en el REAV). Cuadros VOLCAT del sector `Chile_Central_2_km` ya bajados
por las pruebas anteriores (inventario de β73 del 20-10 al 19-11). Viento: GFS 0,25° del archivo
`noaa-gfs-bdp-pds`, plazos horarios, 20 horas bajadas en esta prueba.

## 3. Dirección de la huella VOLCAT, del REAV y del viento GFS

Huella = unión de los objetos anclados al cráter (4 a 500 px del PNG, algún píxel a ≤ 10 km); dirección
= azimut del centroide. P1 = PNG tal cual; P0 = PNG corregido por paralaje con h = 3,2 km + altura REAV.
Viento GFS hacia donde sopla, media de la capa de 3,2 + H/2 a 3,2 + H km s.n.m.

| Jornada | Escenas resueltas (de slots) | Huella P1 | Huella P0 | REAV | Viento GFS | Huella contra REAV | Huella contra GFS | REAV contra GFS |
|---|---|---|---|---|---|---|---|---|
| 25-10 (SE) | 5 de 68 | 181° (R = 0,97), ~10 km | 182°, ~5 km | 135° | 136°, 5,0 m/s | 45,5 y 47,4°: **no concluyente** | 44,7 y 46,6°: no concluyente | 1°: coincide |
| 27-10 (N a NO) | 0 de 42 | sin objeto anclado | | 315°, 22,5° y 0° | 17°, 6° y 3° | sin escenas | | 3 a 62° |
| 28-10 tarde (NO) | 1 de 16 | 172°, 9,6 km | 168°, 4,6 km | 315° | 2°, 5,8 m/s (18:30) | 143 a 147°, pero 1 escena: **no concluyente** | 166 a 170°: discrepa | 47°: no concluyente |
| 28-10 anochecer (sin dirección) | 14 de 15 | 133° (R = 1,00) | 86° (R = 0,93) | | 18°, 5,8 m/s | | 68 a 115°: no concluyente | |
| 10-11 (sin dirección) | 10 de 12 | 115° (R = 0,96) | 66° (R = 0,95) | | 42°, 6,6 m/s | | 24 a 73°: no concluyente | |
| 12-11 (sin dirección) | 0 de 8 | sin objeto anclado | | | 119°, 9,9 m/s | | | |

R = largo del vector medio de los cuadros (1 = todos iguales). Detalle por cuadro en
`direccion_resultado.txt`.

**REAV contra GFS, uno por uno** (explica, no decide): E4 8°, E5 8°, E7 16°, E8 3°, E9 3°, E10 36°, E6
62°; con calma (0,5 a 1,1 m/s) E1, E2 y E3 dan 38 a 169°, que con ese viento no significa nada. Cambiar la
cota del cráter a 2,9 o 3,5 km mueve el viento menos de 25° salvo en las calmas.

**Veredicto H10 (criterio §7): no concluyente.** Jornadas que deciden: 25-10 no concluyente por 0,5 a
2,4° sobre el umbral de 45°; 28-10 no concluyente porque tiene una sola escena resuelta. Con N = 2, ni
siquiera un resultado limpio habría sido más que un indicio.

**Control visual** (`mosaico_h10.png`): los objetos decodificados coinciden con los píxeles de color del
PNG; los píxeles rojos pegados al cráter que no entran en la huella son objetos de menos de 4 px, que la
regla del paso 4 excluye. En la BT11,2 del mismo instante se ve el cordón frío y nevado de la cordillera
que pasa por el cráter de NO a SE; la huella VOLCAT del 25-10 y del 28-10 a las 18:30 cae al oeste de
ese cordón, unos 10 km al sur del cráter.

## 4. Señal espectral: sector REAV (R), huella VOLCAT (V) y sector opuesto (O)

AUC = probabilidad de que un píxel de la región, en la escena, sea más "ceniza" (más bajo) que el mismo
píxel en el control pareado por BT11. IC 95 % por bootstrap de escenas.

| Jornada | Escenas pareadas (de slots) | R: BTD | R: suma de Londres | R: BT11,2 | O: BTD | O: suma | V |
|---|---|---|---|---|---|---|---|
| 25-10 (SE) | 19 de 68 | **0,684** [0,63; 0,74] | 0,603 [0,55; 0,66] | 0,518 | 0,561 | 0,652 | 5 píxeles de una sola escena: no medible |
| 27-10 (N) | 8 de 42 | **0,698** [0,64; 0,75] | 0,675 [0,61; 0,74] | 0,547 | 0,572 | 0,453 | sin huella |
| 28-10 (NO) | 3 de 16 | 0,441 [0,42; 0,49] | 0,429 | 0,447 | 0,502 | 0,560 | sin huella en escenas pareadas |

- Medianas de BTD en R, escena contra control: +0,82 contra +1,04 K (25-10), +1,46 contra +1,82 K
  (27-10), +1,26 contra +1,04 K (28-10). **Ningún píxel con BTD < −1 K**, ni en escena ni en control.
- Suma de Londres bajo +1,5 K en R: 20,5 % contra 15,5 % del control (25-10); 0 contra 0 (27-10);
  4 % contra 12,5 % (28-10).
- **Veredicto S (criterio §7): "tampoco ahí".** Ninguna jornada llega a AUC ≥ 0,70 en BTD o en la suma.
  En las dos que más se acercan (25-10 y 27-10) la diferencia con el sector opuesto sí pasa de 0,10, así
  que lo poco que hay está del lado del REAV y no en toda la escena. Es una tendencia de 0,2 a 0,4 K, del
  mismo orden que el ~0,4 K de la suma de Londres dentro de la huella (prueba del VAAC de Londres), y
  queda bajo el umbral declarado.

## 5. Desviaciones declaradas y límites

- **Escenas L1b: sólo las que ya estaban en disco.** El criterio pedía bajar lo que faltara (726 escenas:
  el 25-10 y el 27-10 antes de las 14:00 UTC y sus controles). La lectura por ventana tardó ~38 s por banda
  y la conexión a S3 quedó bajo ~170 KB/s, compartida con otra sesión; en 25 minutos no se completó
  ninguna escena. Se cortó y la prueba de señal usó el conjunto fijo de escenas de los caches del
  detector de plumas débiles y de β73. Quedan fuera E1, E2, E3, E6 y E7 y la mitad temprana de E8; por eso
  hay 30 slots del 25-10 y 13 del 28-10 sin control (ningún candidato a ≤ 3 K en lo que había en disco).
  El 28-10 queda con 3 escenas y no pesa.
- **Una corrida de prueba de `senal_h10.py`** se hizo para depurar el código antes de cortar la descarga, y
  mostró los primeros números del 25-10. Como no llegó ninguna escena nueva, la corrida final usó
  exactamente los mismos datos; no se cambió ninguna regla después de verla.
- **Regla de asignación de slots** (no estaba en el criterio, se fijó en el código antes de ver números
  de señal): un slot que cae en dos ventanas del mismo día se asigna a la columna más reciente. Afecta
  sólo la altura usada para el paralaje y el viento.
- **Paralaje.** Se usó la altura REAV, no la de VOLCAT. No sabemos si SSEC corrige su PNG; por eso cada
  dirección se informa con las dos hipótesis y el veredicto exige que ambas coincidan.
- **La dirección REAV es un octante leído desde una cámara.** No se miraron las fotos para refinarla.
- **Pocas jornadas.** Con dos jornadas decisivas, H10 no puede pasar de indicio en ningún sentido.

## 6. Qué queda y qué no conviene repetir

- Para decidir H10 haría falta más jornadas con dirección REAV y cuadros VOLCAT anclados a la vez. Con los
  REAV publicados hasta el 19-11 no hay más: el 27-10 VOLCAT no dibujó nada y los REAV de noviembre no dan
  dirección. Una alternativa sin pedir nada al OVDAS es usar el viento GFS como referencia (en esta prueba
  reprodujo al REAV en 6 de 7 casos con viento) en todos los cuadros VOLCAT anclados del 20-10 al 19-11;
  eso sería un criterio nuevo, escrito antes.
- La prueba de señal en el sector REAV del 25-10 y 27-10 temprano quedó sin hacer por ancho de banda; si se
  retoma, el script `bajar_l1b_h10.py` es reanudable.
- No repetir: buscar la señal dentro de la huella VOLCAT con otro índice espectral sin antes preguntar si
  la huella está donde va el viento.
