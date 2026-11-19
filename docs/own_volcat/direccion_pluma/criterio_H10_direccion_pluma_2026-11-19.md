# Criterio H10: ¿la huella VOLCAT de Chillán está donde el OVDAS vio la pluma?

Fecha: 19-11-2026. Escrito y commiteado **antes de calcular el primer número** de esta prueba (dirección
de huella, viento GFS o señal espectral). Lo único medido antes de escribirlo son los datos de entrada:
la lista de episodios de los REAV y RAV (sección 2) y qué escenas hay en disco.

## 1. Pregunta y por qué importa

Todas las pruebas de la serie (umbral, paralaje, 8,5 µm, canales solares, cielo modelado H3, β(7,3/11),
seguimiento H7, VAAC de Londres) midieron la señal **dentro de la huella VOLCAT** y supusieron que la
huella está donde está la pluma. Si la huella apunta a otro lado que la columna que vio el OVDAS desde
sus cámaras, esas pruebas midieron píxeles donde no había pluma, y la señal hay que buscarla en otra
parte. H10: **la huella VOLCAT anclada al cráter no coincide en dirección con la pluma observada por el
OVDAS.**

Física. Una columna de 1 a 2,5 km sobre un cráter de ~3,2 km (cota de referencia, no verificada; se
prueba ±0,3 km como sensibilidad) queda entre ~4,2 y ~5,7 km s.n.m. y la arrastra el viento de ese
nivel. GOES-19 (75,2° O) ve Chillán con ~43° de ángulo cenital, así que una pluma a h km s.n.m. aparece
en la imagen corrida ~0,93·h km hacia el sur y algo al este (alejándose del satélite). Ese corrimiento
puede rotar la dirección aparente de una pluma corta, pero no invierte NO en SE.

## 2. Episodios de entrada (REAV y RAV, leídos completos)

Fuentes: los 5 PDF de `C:\Users\nmend\AppData\Local\Claude-Data\claude_pzs8sxrjxfjjc\side-session-notes\local_1055cba6-2c2f-4aa4-9119-82691ee2ed22\pdfs\`
y 10 REAV de octubre más, públicos, bajados de sernageomin.cl con las URL de
`C:\Users\nmend\AppData\Local\Claude-Data\claude_pzs8sxrjxfjjc\side-session-notes\local_1055cba6-2c2f-4aa4-9119-82691ee2ed22\busqueda_2026-11-19_D_cronologia_chillan.md`
(todos empiezan con `%PDF-`; tabla de cada uno leída con markitdown). No se pide nada al OVDAS. En todos
los REAV de octubre HL = UTC − 3, y en los de noviembre se suma 3 h a la "hora Chile continental".
Alturas sobre el cráter o centro de emisión.

| Id | Fecha | Hora UTC | Altura sobre el cráter | Dirección REAV | Azimut REAV |
|---|---|---|---|---|---|
| E1 | 25-10 | 10:41 | 1.320 m | Sureste | 135° |
| E2 | 25-10 | 11:27 y 11:34 | 920 y 900 m | Sureste | 135° |
| E3 | 25-10 | 13:15 | 1.540 m | Sureste | 135° |
| E4 | 25-10 | 14:44 a 16:48 | 1.740 m (pulso mayor) | Sureste | 135° |
| E5 | 25-10 | 16:23 a 21:16, máximo 17:24 | 2.300 m | Sureste | 135° |
| E6 | 27-10 | 09:26 | 2.000 m | Noroeste | 315° |
| E7 | 27-10 | 10:26 | 960 m | Nor-noreste | 22,5° |
| E8 | 27-10 | 11:04 a 15:00, máximo 12:25 | 1.640 m | Norte | 0° |
| E9 | 28-10 | 15:34 | 1.320 m | Noroeste | 315° |
| E10 | 28-10 | 17:38 | 2.200 m | Noroeste | 315° |
| E11 | 28-10 | 20:32 | 2.440 m | sin dato | |
| E12 | 28-10 | 21:49 | 2.020 m | sin dato | |
| E13 | 10-11 | 21:54 y 22:36 | 2.340 y 2.400 m | sin dato | |
| E14 | 12-11 | 20:03 | 400 m (con flujo piroclástico proximal) | sin dato | |

El RAV del 06-11 resume la quincena: dispersión "predominante hacia el sureste". Corrección al contexto
recibido: el 28-10 sólo E9 y E10 (1.320 y 2.200 m) dicen noroeste; los de 2.440 y 2.020 m no dan
dirección.

Coordenadas del centro de emisión: 36,8677° S, 71,3793° O (RAV del 06-11).

## 3. Unidades y ventanas

- **Ventana de cada episodio**: desde 20 min antes del inicio hasta 60 min después del fin (una pluma
  sigue a la deriva después de la columna). Los episodios del mismo día con la misma dirección se juntan
  en una **jornada**: 25-10 SE (E1 a E5), 27-10 N a NO (E6 a E8, azimut por episodio), 28-10 NO (E9 y E10).
- **Escena resuelta (dirección)**: cuadro VOLCAT de 10 min, dentro de la ventana, con barra de colores
  decodificable, sin manto ni objeto de más de 500 px a menos de 50 km del cráter, con al menos un objeto
  anclado (4 a 500 px del PNG, algún píxel a ≤ 10 km del cráter; misma regla que el paso 4) y con el
  centroide de la huella a ≥ 2 km del cráter. Un cuadro que no cumple se cuenta aparte, no se descarta en
  silencio.
- **Escena resuelta (señal)**: scan L1b de 10 min dentro de la ventana con control pareado (sección 6).
- La unidad de decisión es la **jornada**, no el cuadro: los cuadros de una misma pluma no son
  independientes.

## 4. Dirección de la huella VOLCAT

- Huella = unión de los objetos anclados del cuadro, en el PNG del sector `Chile_Central_2_km`
  (georreferencia equirectangular de la lista SSEC, la misma de `paso3_objetos.py` y `huellas.py`).
- Dirección = azimut del vector cráter → centroide de la huella (plano tangente local en km). Por
  jornada: media circular de los cuadros, más la fracción de cuadros a ≤ 45° de esa media.
- **Paralaje, dos hipótesis**, porque no sabemos si SSEC dibuja la ceniza ya corregida (el ATBD VOLCAT
  2025 no lo dice): (P0) el PNG está en la geometría del ABI sin corregir, y la huella se lleva a su
  posición real moviendo cada píxel hacia el satélite en 0,93·h km con h = 3,2 km + altura REAV; (P1) el
  PNG ya está corregido y se usa tal cual.

## 5. Viento GFS al nivel de la columna

- GFS 0,25° del archivo `noaa-gfs-bdp-pds`, el plazo horario más cercano a cada cuadro (f000 a f005 del
  último ciclo), UGRD, VGRD y HGT en niveles de presión, interpolado bilineal al cráter.
- Capa: de 3,2 km + H/2 a 3,2 km + H s.n.m. (H = altura REAV), media vectorial de u y v interpolados en
  altura cada 100 m. Se informa la dirección **hacia donde sopla** y la rapidez. Sensibilidad (no decide):
  capa de 3,2 km a 3,2 km + H, y cráter a 2,9 y 3,5 km.

## 6. Señal espectral: sector REAV, huella VOLCAT y control pareado

- Datos: ventana ABI de 83 × 94 píxeles con C11 (8,4 µm), C14 (11,2 µm) y C15 (12,3 µm), cache del
  detector de plumas débiles; los scans que falten (25-10 antes de las 14:00 UTC, 27-10 antes de las
  14:00 UTC, y los controles de esas horas) se bajan por ventana con el mismo código. Todo en la geometría
  del ABI sin corregir.
- Regiones, en cada scan:
  - **R, sector REAV**: cuña de ±22,5° alrededor del azimut REAV, entre 2 y 15 km del cráter, corrida por
    paralaje a su posición aparente (0,93·h km alejándose del satélite, h = 3,2 km + altura REAV); se
    sacan los píxeles de la huella VOLCAT del mismo instante dilatada 1 píxel.
  - **V, huella VOLCAT**: píxeles de la huella anclada del cuadro VOLCAT del mismo instante, si existe.
  - **O, sector opuesto**: la misma cuña girada 180°, como control de escena (lección de β(7,3/11): un
    efecto que está en toda la escena no es pluma).
- Señales por píxel, orientadas de modo que "más ceniza" es más bajo: BTD = BT11,2 − BT12,3; suma de
  Londres S = (BT11,2 − BT12,3) + (BT11,2 − BT8,4); BT11,2 (más frío).
- **Control pareado por BT11**: para cada scan, el mismo minuto UTC en un día sin pluma entre −10 y +10
  días (dentro del 20-10 al 19-11), sin REAV ese día (fuera 25, 27 y 28-10, 10 y 12-11; también 29-10 y
  16-11), con el cuadro VOLCAT de ese minuto existente y sin ningún objeto a menos de 50 km del cráter
  entre −60 y +60 min (regla `_limpio` de β73). Se elige el día con la mediana de BT11,2 sobre R ∪ O ∪ V
  más cercana a la del scan, mirando sólo C14; si la diferencia pasa de 3 K, el scan queda sin control y se
  cuenta.
- Medida: AUC = probabilidad de que un píxel de la región en el scan sea más "ceniza" que el mismo píxel
  en el control, juntando los píxeles de todos los scans pareados de la jornada. IC 95 % por bootstrap de
  scans (1.000 réplicas). Se informa también la fracción de píxeles con BTD < −1 K y con S < +1,5 K.
- **Señal de ceniza en una región** = AUC ≥ 0,70 en BTD o en S. BT11,2 sola con AUC ≥ 0,70 se informa como
  "frío no específico" (una nube de agua también lo da) y no cuenta como ceniza.
- **Localizada en R** = señal de ceniza en R y, en la misma señal, AUC_R − AUC_O ≥ 0,10. Si O separa
  igual que R, es "efecto de escena" y no cuenta.

## 7. Reglas de decisión

**Por jornada (dirección).** Diferencia angular Δ entre la dirección de la huella (media circular) y el
azimut REAV:
- **coincide**: Δ ≤ 45° con P0 y con P1;
- **discrepa**: Δ ≥ 90° con P0 y con P1;
- **no concluyente**: cualquier otro caso, o menos de 2 escenas resueltas en la jornada.
Con la misma regla se compara huella contra viento GFS y REAV contra viento GFS (eso no decide H10, lo
explica).

**H10 (decide).** Sólo cuentan las jornadas con dirección REAV y con escenas VOLCAT resueltas.
- **H10 se falsa**: todas esas jornadas coinciden. La huella sí estaba donde la pluma, y las pruebas
  anteriores midieron en el lugar correcto.
- **H10 se sostiene**: todas discrepan.
- **No concluyente**: mezcla, o alguna no concluyente.
- Se espera N = 2 jornadas (25-10 y 28-10): el 27-10 VOLCAT no dibujó nada anclado. Con N = 2 cualquier
  resultado se informa como **indicio con dos jornadas**, no como regla general, y se dice así.

**Lectura de la combinación (pre-declarada, no decide).**
- Huella ≠ REAV, huella ≈ GFS, REAV ≠ GFS: la huella sigue al viento del modelo y no a la pluma vista.
- Huella ≠ REAV y REAV ≈ GFS: la huella no está ni donde la pluma ni donde el viento; el origen es otro.
- Huella ≈ REAV: lo esperado si la huella es la pluma.

**Señal espectral (veredicto aparte, S).** Jornadas 25-10, 27-10 y 28-10.
- **La señal está donde vio el OVDAS**: señal de ceniza localizada en R en al menos 2 de 3 jornadas.
- **Tampoco ahí**: en ninguna jornada hay señal de ceniza localizada en R.
- **No concluyente**: lo demás.

## 8. Lo que no se hace

- No se reinterpreta la dirección REAV (el texto manda; no se miran las fotos de las cámaras para sacar
  azimut, porque no conocemos la orientación de cada cámara).
- No se cambian ventanas, tolerancias ni regiones después de ver números. Todo cambio posterior va como
  sensibilidad marcada y no decide.
- No se toca código de la app ni `docs/own_volcat/POR_QUE_VOLCAT_VE_Y_NOSOTROS_NO.md`.
