# S22c: altura propia para los píxeles del detector S22a. Informe, 24-11-2026

Criterio `criterio_2026-11-24.md`, commit `bdd73e7` (16:04 UTC), empujado antes de bajar el viento y de calcular
cualquier altura. Código en
`C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\Goes\.claude\worktrees\agent-a574eb91fb7c2f8fe\docs\own_volcat\s22c_altura_propia\scripts\`
(`s22c_viento.py` baja el viento, `s22c_medir.py` mide, 10 de 10 pruebas; `s22c_lado_a_lado.py` hace el video).
Salidas en
`C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\Goes\.claude\worktrees\agent-a574eb91fb7c2f8fe\docs\own_volcat\s22c_altura_propia\resultados\s22c_resultado.json`
y los logs de la misma carpeta. Viento GFS (sólo la caja chica, sin GRIB) en `D:\goes_notas\s22\s22c\gfs\`.

**Resultado en una línea: NO SIRVE por la regla.** Contra la única altura medida por sombra (bocanada del 08-11 a las
14:53 UTC, 4,7 km), el viento del GFS no explica hacia dónde iba la bocanada: a 4,7 km soplaba hacia 150° con 2 a 3
m/s y la bocanada iba hacia 207°. En la tarde del 08-11 la altura que mejor calza con el viento tiene mediana 5,1 km
(20 de 23 disparos entre 4,8 y 5,4 km), muy cerca de los 4,7 km, pero la misma dirección es compatible con casi toda la columna (3,4 a 14
km) y la regla no la acepta. La corrección de emisividad no encuentra solución en el píxel de la verdad.

## 1. Para geólogo

**El fenómeno.** Una pluma tenue (ceniza diluida con vapor, f·ε cerca de 0,12) casi no cambia la temperatura que ve
el satélite: lo que deja es una baja de 1 K en la diferencia 11 − 12 µm. Las alturas de VOLCAT, de ACHA o de un
BT-matching salen de la temperatura de la nube, y en una nube casi transparente esa temperatura no se puede separar
de la transparencia: una nube fría y muy tenue y una nube tibia y algo más densa dejan la misma huella. Por eso
buscamos un camino que no use la temperatura: **una pluma pasiva viaja con el viento de su altura**. Si el viento
gira con la altura, la dirección en que la pluma se aleja del cráter dice en qué capa está.

**El mecanismo.** Para cada altura de 3,2 a 14 km: (1) se corrige la posición de los 8 píxeles por paralaje
(GOES-19 ve algo a 4,7 km sobre Chillán unos 4,3 km más al sur de donde está, porque lo mira desde el norte y el
oeste con 43° de cenit); (2) se mide hacia dónde quedan desde el cráter; (3) se compara con la dirección del viento
GFS a esa altura. Las alturas donde las dos direcciones difieren 30° o menos, con viento de 3 m/s o más, son las
compatibles. Si cubren 3 km o menos, el método "restringe".

**Lo que salió.**

- **En la verdad de la mañana el viento del modelo no sirve.** A las 14:53 del 08-11 el GFS da entre 4 y 6 km un
  viento casi en calma (1,7 a 2,8 m/s) que va hacia el SSE (146° a 164°); la bocanada que fotografió Sentinel-2 iba
  hacia el SSO (207°). El VAAC de las 13:40 la describe "MOV SW 05KT", o sea, el viento real iba hacia donde iba la
  bocanada y el modelo no. La única altura que el método acepta es la del cráter (3,2 km, donde hay 4,1 m/s hacia
  179°, a 28° de la bocanada). Es lo mismo que vio H10: con calma, la dirección del GFS no significa nada.
- **En la tarde, la altura que mejor calza está cerca de la verdad, pero no queda fija.** De 16:30 a 20:50 UTC el
  viento a 4 a 5 km va hacia el SE (123° a 152° a las 18:30, 4 a 6 m/s) y el detector marca hacia 134° a 164°. La
  altura de mejor ajuste es 5,0 a 5,2 km en 15 de 23 disparos y 4,8 a 5,4 km en 20 (mediana 5,1; los otros tres dan
  3,6, 4,0 y 14 km), con desajuste de 0 a 8°. Calza con la sombra
  (4,7 km) y con el VAAC de las 19:30 (SFC/FL150, 4,6 km, "MOV SE 10KT"). **Pero no excluye nada más arriba**: entre
  8 y 14 km el viento va hacia el E (85° a 95°), y si uno supone la pluma así de alta, la corrección de paralaje
  sube los píxeles hacia el norte 7 a 13 km y su rumbo gira hacia el E. Paralaje y viento se compensan: la dirección
  sola no distingue entre 5 km y 12 km. Ningún disparo restringe (banda mediana de 10,2 km).
- **VOLCAT en esos mismos cuadros** pinta la pluma entre 1,5 y 3,5 km (mediana 3,25 km), es decir, en o bajo el
  cráter, 1,4 km bajo la sombra. Nuestra mejor altura queda 1,9 km sobre VOLCAT. No es verdad de VOLCAT: es una
  referencia, y la sombra está más cerca de nuestro número que del suyo.
- **El 14-11 (sin verdad) la mejor altura queda arriba, y eso muestra la trampa.** Los 8 disparos (17:30 a 19:20
  UTC) apuntan a 135° a 141°. El GFS da entre 4 y 6,5 km viento hacia el S (159° a 182°, 7 a 9 m/s) y de 7,5 a 14
  km hacia el SE (116° a 129°, 11 a 32 m/s). La mejor coincidencia cae en 8,2 a 10,2 km (mediana 9,5) porque allí el
  viento y el rumbo corregido por paralaje coinciden casi exacto; pero la capa baja también está dentro de los 30° y
  las bandas van de unos 3,6 a 14 km: NO RESTRINGE. El VAAC de las 17:00 dice SFC/FL120 (3,7 km) "MOV S 15KT"
  (7,7 m/s): rapidez de la capa baja, no de los 16 m/s que el GFS tiene a 9,5 km. VOLCAT pinta 3,5 a 5,5 km
  (mediana 3,75; un píxel a 7,5 km a las 19:20).
- **La corrección de emisividad (Wen-Rose con f·ε) en el píxel de la verdad no tiene solución.** El píxel de la
  bocanada (44, 46) estaba a 283,8 K a las 14:40, más tibio que en los 6 días despejados que sirven de fondo
  (266,6 a 280,5 K). Una capa fría no puede calentar el píxel, así que ninguna combinación de emisividad y
  temperatura de la pluma reproduce lo observado (residuo de 0,43 a 2,9 K, contra 0,2 K pedidos), con β de 0,6, 0,7
  y 0,8. El fondo de un píxel de cumbre en primavera no se conoce mejor que unos 10 K (el 12-11 despejado da 291,9 K),
  y la pluma lo baja unos pocos K.

**Lectura honesta.** El viento podría dar altura a nuestros píxeles en una tarde con viento firme, pero no con el
viento de un modelo de 25 km que falla en las calmas, y no sin otra cosa que corte la degeneración con el paralaje.
Lo que cortaría esa degeneración es la **rapidez**: la pluma se mueve a 5 m/s si está a 5 km y a 20 a 35 m/s si
está a 10 a 12 km (§4). Eso requiere seguir la pluma de cuadro a cuadro, que este detector no hace.

## 2. Veredicto por la regla

| Prueba | Resultado | Veredicto |
|---|---|---|
| 2.1 Método (a) contra la sombra, 08-11 14:53 (decide) | Dirección de Sentinel-2 207°. Única altura compatible 3,2 km (desajuste 27,8°, 4,1 m/s); a 4,7 km el viento va hacia ~150° a 2,3 m/s. τ = 20°: ninguna; τ = 45°: 3,2 a 4,1 km | **FALLA** (h\* 3,2 km, error 1,5 km) |
| 2.1 informativo, 25-10 14:34 (Landsat, 253°, VAAC 4,3 km) | Ninguna altura compatible con ningún τ: de 3,5 a 5 km el viento va hacia 116° a 199° a 2,5 a 3 m/s | NO RESTRINGE |
| 2.2 Píxeles del detector, tarde del 08-11 (23 disparos) | h\* mediana 5,1 km (P25 a P75: 5,0 a 5,2); los 23 con altura y con banda que toca 3,7 a 5,7 km; ancho mediano 10,2 km, 0 de 23 restringen | **NO RESTRINGE** |
| 2.3 informativo, 14-11 (8 disparos) | h\* mediana 9,5 km (8,2 a 10,2), 0 de 8 restringen, ancho mediano 9,7 km; VAAC FL120, VOLCAT mediana 3,75 km | NO RESTRINGE |
| (b) Emisividad en el píxel (44, 46), 14:40 y 14:50 | 0 de 12 soluciones con β 0,7 (y 0 con 0,6 y 0,8) | NO RESTRINGE (esperado) |
| **Conjunto** | (a) FALLA en 2.1 | **NO SIRVE** |

Con una sola verdad, es un caso, no una estadística.

## 3. Informativo

Por cuadro (08-11, τ = 30°): `resultados/s22c_resultado.json`, `dias/2026-11-08/cuadros`. Rumbo aparente del
detector 134° a 164° (dos disparos en la tajada 150° a 180°), mediana de distancia 16 a 28 km del cráter; corregido
a h\*, 126° a 161° (98° en el disparo de 16:40). Viento GFS en h\*: 3,1 a 6,1 m/s salvo 16:40 (35 m/s a 14 km);
VAAC 19:30: 10 KT ≈ 5 m/s. El disparo de 16:40 da h\* = 14 km (la mejor
coincidencia queda arriba, donde la corrección de paralaje lleva el rumbo a 98°): es el mismo efecto de
compensación, visto en un cuadro.

14-11 (8 disparos, todos en la tajada 120° a 150°, a 16 a 31 km): h\* 8,2 a 10,2 km (P25 a P75: 9,0 a 9,7),
desajuste 0 a 10,7°, viento en h\* 14 a 18 m/s; 0 de 8 restringen (ancho mediano 9,7 km); 5 de 8 con banda que toca
3,7 a 5,7 km. VOLCAT con ceniza a 50 km en los 8; h\* queda 5,4 km sobre VOLCAT (mediana de la diferencia).
Detalle en `dias/2026-11-14/cuadros` del mismo json.

## 4. Post hoc (mirado después del veredicto; no lo cambia)

- **La rapidez rompería la degeneración.** Con el viento de la tarde del 08-11, la capa de 4 a 6 km va a 4 a 6 m/s
  y la de 9 a 12 km a 11 a 33 m/s. En 10 min una pluma a 5 km avanza 2 a 4 km (uno o dos píxeles); a 11 km, 15 a 20
  km. El VAAC dice 10 KT. El 14-11 es más claro: la mejor coincidencia de dirección está a 9,5 km con 16 m/s, y el
  VAAC dice 15 KT (7,7 m/s), la rapidez de la capa de 4 a 6 km. Una regla que además pidiera rapidez compatible
  dejaría sólo la capa baja los dos días. No se probó: necesita seguir la pluma entre cuadros, y eso es un criterio
  nuevo. Por lo mismo, **el color del video del 14-11 (9 a 10 km, azul) no se debe leer como altura**: es el mínimo
  de una curva casi plana.
- **La falla de la mañana es del viento, no de la geometría.** La bocanada de Sentinel-2 iba a 207° y el VAAC
  también la vio ir al SO; el GFS a esa hora tenía calma y otra dirección. Una pluma pegada al cráter (1,6 km) en
  calma la mueve también la dinámica de la emisión y el flujo de ladera, que el modelo no tiene.

## 5. Lo que puede estar mal

- **Una sola verdad**, de la mañana, y una bocanada a 1,6 km del cráter: una dirección muy corta y sensible al punto
  de emisión. La tarde se compara contra esa altura suponiendo que la columna no cambió.
- **La dirección del detector está atada a su tajada de 30°**, y sus 8 píxeles son los más bajos en M1, no
  necesariamente la pluma (el 15-11 dispara igual al SE sin VOLCAT, S22a).
- **GFS de 0,25°** (unos 25 km) no resuelve los flujos de valle y de ladera de la cordillera; H10 midió 3 a 36° de
  error de dirección con viento, y nada con calma.
- **El método (b) usó el fondo del mismo cuadro en otros días despejados** (el criterio lo fijó así): en primavera,
  con la nieve en retroceso, ese fondo se calienta día a día y lo vuelve inútil. Un fondo modelado (temperatura de
  superficie) cambiaría eso, pero agrega su propio error de varios K.
- **Estéreo GOES-18 no se hizo** (criterio §1 c): no hay objeto que emparejar.

## 6. Video

`C:\Users\nmend\Downloads\s22c_lado_a_lado_altura_volcat_vs_detector_chillan_2026-11-08_10min.mp4` y
`C:\Users\nmend\Downloads\s22c_lado_a_lado_altura_volcat_vs_detector_chillan_2026-11-14_10min.mp4` (fuera del repo
por la licencia de SSEC). Izquierda, VOLCAT tal cual; derecha, los 8 píxeles del detector con el color de h\* en los
bloques de la barra de VOLCAT (0 a 20 km, leída del PNG en D:), donde los ve GOES-19 (sin corregir paralaje, como el
fondo y como VOLCAT). Bajo el panel van h\* y la banda compatible, para que no se lea el color como una altura
segura: el 08-11 la banda va de unos 3,5 a 14 km en todos los cuadros.
