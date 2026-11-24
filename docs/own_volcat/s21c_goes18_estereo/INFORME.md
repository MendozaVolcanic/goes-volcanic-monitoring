# S21c: GOES-18 en estéreo con GOES-19 sobre los pulsos de Nevados de Chillán. Informe, 24-11-2026

Criterio: `criterio_2026-11-24.md`, commit `6989f32`, empujado antes de bajar ni mirar una sola imagen C02. Scripts en
`scripts/`, salidas en `resultados/`, figuras en `figuras/`. Datos (524 ventanas de 81 × 81 px, 5 MB) en
`D:\goes_notas\s21\c\`. Prueba 3 de `docs/own_volcat/QUE_NOS_FALTA_S19.md` §5.

- **Paso 0, navegación contra el terreno: VERIFICADA en los dos satélites.** El C02 simulado desde Sentinel-2 con
  el modelo de elevación calza con el real con r = 0,93 a 0,97; sesgo de GOES-18 de un cuarto a tres cuartos de píxel.
  La maquinaria del estéreo funciona y su error esperado (±0,26 km de altura) es realista.
- **Prueba A (decide), ¿asoma algo nuevo sobre la cumbre en GOES-18 en los pulsos de la tarde del 28-10?: NO
  CONCLUYENTE.** Los tres pulsos altos salen SIN PODER: el estadístico escrito no detecta ni una columna sintética de
  contraste 0,20. Es un defecto del estadístico, no de los datos (§4).
- **Prueba B, altura por estéreo: no corre** (ningún pulso con SEÑAL).
- **Prueba C, franja de Landsat del 25-10: SIN SEÑAL** en GOES-18 (p 0,069) y en GOES-19 (p 0,38) a la altura del
  VAAC; en GOES-18 la franja sobre nieve cabe en un solo píxel.
- **Post hoc (no cambia el veredicto):** con un filtro adaptado a la columna, que sí tiene poder (una columna de 1 px
  de ancho con contraste 0,10 se ve en el 80 % de los casos), ningún pulso se separa del nulo (p 0,45 a 0,98). A la
  vista tampoco asoma columna alguna en toda la tarde.

## 1. El fenómeno, antes de los números

Desde GOES-18, que mira Chillán casi de lado (79° del cenit, desde el oeste noroeste), una columna eruptiva vertical
debería verse como un rasgo que sale de la cumbre hacia el limbo: 1,74 píxeles de C02 por cada km de altura, unos 4
píxeles para las columnas de 2,0 a 2,4 km que el OVDAS registró el 28-10. Con GOES-19 mirando desde el norte, las dos
líneas de vista se cruzan y dan la altura sin usar temperatura.

Lo que se vio: **la tarde del 28-10, en los cuadros de GOES-18 que miraron Chillán entre 15 s y 19 min después del
inicio de cada pulso, no asoma nada nuevo sobre la cumbre.** El cambio entre cuadros en el entorno del cráter en esos
momentos es igual o menor que en los cuadros sin pulso del mismo día. En GOES-19 hay manchas oscuras chicas junto al
cráter que aparecen y desaparecen durante toda la tarde (`figuras/hoja_28-10_g19.png`), sin relación con las horas
del REAV; son compatibles con la actividad menor que el propio REAV del 28-10 menciona ("columnas menores"), pero esta
prueba no las puede atribuir.

Lo que esto significa para el geólogo: **las columnas de 2 km que vieron las cámaras no quedaron, en el visible de
0,5 km, en el instante en que pasó el barrido**. Las explosiones duran segundos a minutos y el barrido es cada 10 min:
el primer cuadro de E10 miró a los 15 s del inicio (la columna recién nace), el de E11 a los 6 min y el de E12 a los
9 min (la columna ya se inclinó y se diluyó). No descarta que la columna haya existido: dice que el disco completo
cada 10 min no la alcanza a ver de lado, ni siquiera con un píxel de 0,57 km.

## 2. Geometría y paso 0 (navegación)

Geometría (`resultados/geometria.txt`, criterio §1): GOES-18 a 79,26° de cenit (azimut 285°), GOES-19 a 42,91°
(azimut 354°). GOES-18 mira Chillán unos 23 s antes que GOES-19 (franjas 17 y 18 de 22; ±30 s), así que el
movimiento de la pluma entre los dos barridos (0,2 a 0,5 km a 10 m/s) cae casi entero en el error horizontal.

Registro contra el terreno (`resultados/registro.txt`, `figuras/registro.png`):

| Satélite, cuadro | r con modelo de elevación | Corrimiento (filas, columnas) | r con terreno plano a 3,2 km | Corrimiento plano |
|---|---|---|---|---|
| GOES-18, 16-10 14:40 | 0,943 | −0,25; +0,50 | 0,928 | −1,50; −1,50 |
| GOES-18, 28-10 14:40 | 0,927 | −0,25; +0,75 | 0,910 | −1,50; −1,25 |
| GOES-19, 16-10 14:40 | 0,975 | −0,25; 0,00 | 0,969 | −1,75; 0,00 |
| GOES-19, 28-10 14:40 | 0,946 | 0,00; 0,00 | 0,942 | −1,75; 0,00 |

Por la regla (r ≥ 0,6 y diferencia entre cuadros ≤ 1 px): **navegación verificada** en los dos (diferencia 0,25 px
en ambos). Con el terreno a su altura real el corrimiento residual cae bajo un píxel; con el terreno plano queda en
1,5 a 1,75 px. Eso confirma que la paralaje del terreno está bien modelada también a 79°, donde NOAA no evalúa la
navegación, y que el estéreo con estos dos satélites mide alturas con el error que el criterio declaró.

## 3. Resultado por la regla del criterio

### Prueba A (decide)

Nulo: 125 pares de cuadros sin pulso, 34 del 28-10 y 91 de los días de control 21-09, 15, 16 y 17-10 (sólo pares con
los dos cuadros despejados por E1). M = suma de |ΔR| del mayor componente anómalo en la región S (reflectancia, en
unidades de píxel). En GOES-18 el nulo del 28-10 tiene mediana 1,87 y máximo 5,45; el de los controles, mediana 1,68
y máximo 16,2.

| Pulso | Previo: M, p | Post 1 (mirada G18, desde el inicio): M, p | Post 2: M, p | p_pulso | c80 | Veredicto |
|---|---|---|---|---|---|---|
| E10 (2.200 m) | 4,13; 0,21 | 17:38:15 (+0,3 min): 1,74; 0,50 | 17:48:15: 1,35; 0,57 | 1,0 | > 0,20 | **SIN PODER** |
| E11 (2.440 m) | 0,36; 0,78 | 20:38:15 (+6,3 min): 0,75; 0,67 | 20:48:15: 0,35; 0,79 | 1,0 | > 0,20 | **SIN PODER** |
| E12 (2.020 m) | 0,36; 0,79 | 21:58:15 (+9,3 min): 0,21; 0,90 | 22:08:15: 0,26; 0,86 | 1,0 | > 0,20 | **SIN PODER** |
| E9 (1.320 m, informativo) | 4,78; 0,15 | 15:38:15 (+4,3 min): 3,63; 0,22 | 15:48:15: 1,68; 0,50 | 0,44 | > 0,20 | SIN PODER |

**Veredicto global: NO CONCLUYENTE** (0 SEÑAL, 0 SIN SEÑAL, 3 SIN PODER). GOES-19, sin veredicto: p de 0,24 a 0,83 en
todos los cuadros previos y post.

### Prueba B

No corre: el criterio la condiciona a SEÑAL en GOES-18.

### Prueba C (franja de Landsat del 25-10 a 4,27 km)

| Satélite | Píxeles de la franja (f ≥ 0,25) | A (14:30) | Corrimientos del nulo | p | Veredicto |
|---|---|---|---|---|---|
| GOES-18 | 1 | −0,057 | 305 | 0,069 | **SIN SEÑAL** |
| GOES-19 | 6 | −0,014 | 462 | 0,38 | **SIN SEÑAL** |

La altura por posición conocida no informa: en GOES-18 el máximo de |A| cae en 3,2 km (el suelo) y en GOES-19 en
3,4 km, con un segundo máximo de signo contrario entre 5,0 y 5,6 km. Con un píxel (GOES-18) o seis (GOES-19) no hay
con qué medir altura. Lectura: la franja translúcida que Landsat vio sobre la nieve (1,6 km² sobre nieve) no oscurece
la nieve lo bastante en 0,64 µm a 0,5 km como para salir del fondo; S20b sí la vio en el infrarrojo de 2 km
(−1 K en 11 − 12 µm), que es la firma de la ceniza y no del brillo.

## 4. Por qué la prueba A quedó sin poder

El estadístico suma |ΔR| sobre el mayor grupo de píxeles que cambian más de 4 sigma entre dos cuadros. En 10 min, al
mediodía y con 61 a 65° de sol, la cumbre nevada de Chillán cambia de brillo en grupos de 100 a 170 píxeles (sombras
y nieve que reflejan distinto a medida que el sol gira; posiblemente también la actividad menor). Una columna de 4 a
5 píxeles con contraste 0,20 suma 1 en M, cuando el percentil 95 del nulo es 8. El umbral de 4 sigma se calcula con
el fondo de toda la ventana (σ 0,003), mucho más quieto que la cumbre (0,02 por píxel en S). El criterio debió
normalizar cada píxel contra su propia historia o usar un filtro adaptado a la columna. Eso se hace en §5, post hoc.

## 5. Post hoc (escrito después de ver SIN PODER; no cambia el veredicto)

Script `scripts/s21c_posthoc.py`, salida `resultados/posthoc.txt`. Mismos pares nulos, misma inyección, misma regla de
p. Cada píxel de S se normaliza con la mediana y la MAD de su ΔR en los 125 pares nulos (σ por píxel, mediana 0,021).

- **Zcol**, media de z sobre los píxeles de la columna vertical del REAV (filtro adaptado): **c80 = 0,10 en GOES-18**
  (0,15 en GOES-19), es decir, tiene el poder que el criterio pedía. Pulsos en GOES-18: p de Zcol 0,82 a 0,87 (E10),
  0,45 a 0,98 (E11), 0,64 a 0,67 (E12). Nada.
- **Z4**, media de los 4 |z| mayores de S (cualquier rasgo chico): sigue sin poder (el nulo tiene colas de |z| > 30).
- **A la vista** (`figuras/hoja_28-10_g18.png`, 46 cuadros de 15:00 a 22:30): la cumbre en GOES-18 se ve igual en
  todos; ningún rasgo sale hacia abajo a la derecha (la dirección de la columna en la imagen).

Si la prueba hubiera tenido este estadístico, los tres pulsos habrían salido SIN SEÑAL. Lectura cautelosa: **en los
momentos en que GOES-18 miró, no había sobre la cumbre una columna vertical de 1 px de ancho con contraste de 0,10 o
más.** No dice nada de los minutos entre barridos, ni de una columna inclinada por el viento (el filtro mira la vertical).

## 6. Qué significa

1. **El estéreo GOES-18 con GOES-19 funciona sobre Chillán** y su error es el declarado: la navegación de los dos
   satélites calza con el terreno a menos de un píxel, incluido GOES-18 a 79°. Esto es lo que se lleva de esta prueba:
   la herramienta está lista y validada para el día en que haya un rasgo que medir.
2. **Lo que falta es el rasgo, no la geometría.** En disco completo cada 10 min, las columnas de 2 km del 28-10 no
   quedaron a la vista de GOES-18 cuando pasó el barrido. Es coherente con explosiones de segundos a minutos (QUE_NOS_FALTA
   §3.2) y con lo que mostró H24 en el infrarrojo: el pulso no deja nada estable que un barrido cada 10 min alcance.
3. **Para medir altura por estéreo hace falta un sector de mesoescala (1 min) sobre Chillán**, que no hubo entre el
   25-10 y el 18-11 (S19i, INS-11). Con un cuadro por minuto, la columna nace en uno o dos cuadros; con 0,26 km de
   error por estéreo se podría comparar directamente con la altura del REAV y con la de VOLCAT. Es la gestión pendiente
   del §6 de QUE_NOS_FALTA.
4. **Contexto VOLCAT (no entra en ninguna regla).** H24 encontró objeto de VOLCAT anclado al cráter en 8 de 8 cuadros
   de E11, 7 de 7 de E12 y 1 de 8 de E10 (`h24_pulsos_reav/resultados/h24_volcat_por_episodio.json`). En esos mismos
   cuadros, desde el costado, no asoma columna en el visible. Cuadra con que VOLCAT publique por seguimiento (H28) y
   no por una columna que se vea en ese instante, pero esta prueba no lo demuestra.

## 7. Lo que puede estar mal

- **El estadístico del criterio fue mal elegido** (§4). El veredicto queda NO CONCLUYENTE por eso; el post hoc con poder
  dice "nada", pero es post hoc.
- **La columna inclinada no se buscó con filtro adaptado.** Con viento de 10 a 20 m/s, a los 6 y 9 min (E11, E12) la
  columna ya se inclinó varios km; el filtro vertical no la sigue. Z4 la buscaría, pero no tiene poder.
- **Nulo del mismo día con el volcán activo** y controles de otras fechas con otra nieve y otro sol; ninguna tarde
  despejada entera antes del 22-10 (`resultados/controles.txt`).
- **Prueba C con un solo píxel en GOES-18**: la máscara de Landsat sólo marca la franja sobre nieve (1,6 km²) y el píxel
  de GOES-18 mide 1,7 km² en el suelo. Sin poder real; se informa por la regla.
- **Hora de barrido de GOES-18 estimada** (±30 s, interpolando franjas del modo 6A); no cambia ninguna conclusión.
- **Sin oclusión en la simulación del paso 0** (laderas escondidas a 11° de elevación); aun así r ≥ 0,93.
- **E6 (27-10, explosión de 2 km) quedó fuera por física**: el sol estaba 4,3° bajo el horizonte al barrido.

## 8. Archivos

- Criterio: `criterio_2026-11-24.md` (commit `6989f32`).
- Scripts: `s21c_comun.py` (geometría), `s21c_geometria.py`, `s21c_controles.py` y `s21c_controles_lib.py` (ACMF),
  `s21c_bajar.py`, `s21c_registro.py` (paso 0), `s21c_medir.py` (A, B, C), `s21c_posthoc.py`, `s21c_figuras.py`,
  `s21c_hoja.py` (hojas de contacto, post hoc).
- Resultados: `geometria.txt`, `controles.txt/json`, `registro.txt/json`, `medir.txt/json/log`, `posthoc.txt/json/log`.
- Figuras: `registro.png`, `pulsos_g18.png`, `pulsos_g19.png`, `hoja_28-10_g18.png`, `hoja_28-10_g19.png`,
  `landsat_25-10.png`.
- Cambio de código después del criterio (no de regla): `desplazar` en `s21c_comun.py` pasó de `math.cos` a `np.cos`
  para aceptar arreglos (la prueba C se caía), y la prueba C guarda en caché la proyección de la grilla por altura
  (mismo cálculo, más rápido).
