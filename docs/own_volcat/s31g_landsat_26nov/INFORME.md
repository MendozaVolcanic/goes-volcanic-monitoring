# S31g: Landsat 8 del 26-11 y pasadas finas nuevas. Informe, 27-11-2026

Criterio: `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\Goes\docs\own_volcat\s31g_landsat_26nov\criterio_2026-11-27.md`,
commit `d88869a` (27-11 04:15 UTC), empujado antes de abrir un solo píxel. Catálogo:
`scripts/s31g_catalogo.py` y `resultados/catalogo_2026-11-27.json` (consulta de las 04:14 UTC). Sentinel-2:
`scripts/s31g_s2_25nov.py`, `scripts/s31g_s2_forma.py`, `scripts/s31g_s2_zoom.py`, `resultados/s2_2026-11-25*.json`,
figuras `figuras/s2_2026-11-25_{color,swir,zoom}.png`. Datos en `D:\goes_notas\s31\s31g\` (reflectancia del 25-11;
las referencias ya estaban en las cachés de S20b y S21). No se miró GOES de ningún día posterior al 24-11, ni la
confirmación retenida, ni VIIRS, ni SSEC.

- **Landsat 8 del 26-11: PENDIENTE, ni elegida ni descartada.** Al 27-11 04:14 UTC no está en USGS (C2 L1 ni L2),
  Planetary Computer ni HLS. La última Landsat 8 de todo Chile publicada es del 17-11; en el path 233, USGS demora 5 a
  14 días en procesarla. La regla de S21a1 no se aplicó porque no hay escena a la que aplicarla, y no se midió nada.
  Los parámetros de esa medida quedaron fijados en el criterio (§1.1) para cuando aparezca, esperable entre el 01 y
  el 10-12.
- **Sentinel-2C del 25-11, 14:43 UTC (0,24 % de nube): nube volcánica sobre el cráter, sin pluma alargada.** Sin
  térmico, no entra en la prueba de S21a1. Se suma a la hoja de ruta de verdad fina como verdad de presencia a esa
  hora, con dirección poco definida (norte) y altura por sombra de unos 3,2 km sobre el nivel del mar.

## 1. Landsat 8 del 26-11

La pasada existe en la órbita (path 233, ciclo de 16 días: 25-10, 10-11, 26-11), pero todavía no en ningún archivo:

| Fuente | Del 19 al 27-11 sobre el cráter |
|---|---|
| USGS LandsatLook, C2 L1 y L2 SR | sólo Landsat 9 de noche (path 119, 20-11); nada del path 233 |
| Planetary Computer, C2 L2 | nada |
| CMR, HLS L30 | nada |
| USGS, Landsat 8 en todo Chile | 97 escenas desde el 10-11; la más reciente adquirida el 17-11 |
| USGS, Landsat 9 en todo Chile | 100 escenas; la más reciente el 26-11 |

Demora de proceso de Landsat 8 en el path 233 (fecha de proceso menos fecha de adquisición, de los ids C2 L1):
07-09 y 23-09 a los 8 días, 09-10 a los 6, 25-10 a los 5, 10-11 a los 14. Landsat 9 sale en 0 a 1 día. HLS L30 llega
después de la C2 (S21a1 encontró la del 10-11 sólo en HLS el 24-11).

Por la regla, el paso 0 (nube de catálogo) no se puede aplicar a una escena no publicada. No se buscó otra regla ni
otro sensor que la reemplace. La próxima Landsat del path 233 después del 26-11 es Landsat 9 el 04-12.

## 2. Sentinel-2C del 25-11, 14:43 UTC

### 2.1 Qué se ve, para geólogo

Mañana despejada en toda la tesela (0,24 % de nube; la escena corta al oeste del cráter, a unos 3 km, por el borde de
la franja). La nieve ya se retiró de buena parte del cono: en la referencia compuesta, la nieve cubre el 24 % del
círculo de 5 km y el 5 % del de 15 km.

Sobre el cráter hay una nube blanca de unos 1,7 por 1,0 km, centrada 0,7 km al norte del cráter y pegada a él (empieza
a 0,28 km). En color verdadero casi no se distingue de la nieve que tiene debajo; en el compuesto SWIR2, SWIR1, rojo
resalta como una mancha blanca sobre la nieve azul oscura, que es lo que hace una nube de gotas o de partículas sobre
nieve: la nieve absorbe a 1,6 µm y la nube no. La clasificación de escena de Sentinel-2 (SCL) la marca como nube:
2,9 km² en un objeto que nace en el cráter (a 0,01 km) con centroide al norte. En el acercamiento de 10 m se ven,
además, hebras grises translúcidas que salen del cráter hacia el oeste, a menos de 1,2 km. A 4,8 km al norte hay otra
nube de 1,0 km² (SCL) con un borde gris difuso en color verdadero; la máscara marca sus bordes sobre la nieve
(componentes de 5 a 148 celdas a 4,6 a 5,7 km, azimut 354 a 4°). Fuera del volcán, en 15 km a la redonda, la SCL sólo
marca manchas de menos de 0,25 km² al oeste y noroeste.

La sombra de la nube cae 300 m hacia el suroeste (azimut 244°): por la regla de S20b la altura vale (mediana del rojo
relativo 0,47, ángulo eje y sombra 75°) y da 546 m sobre el terreno de la sombra, 3.163 m sobre el nivel del mar. Es
una nube baja, apenas sobre la cumbre (el DEM de 30 m da 2.856 m en la celda del cráter).

### 2.2 Máscara de S20b sin cambios (criterio §2.1 a)

| Qué | Valor |
|---|---|
| Referencias (primero anteriores) | Sentinel-2B 23-11 (706.102 celdas) y Landsat 9 18-11 (165.066) |
| Máscara | 1.893 celdas, 1,70 km², 17 componentes; 1,57 km² a 6 km o menos del cráter |
| Componente que nace en el cráter | 1.502 celdas, 1,35 km²; 1,71 km de largo por 1,02 de ancho; centroide a 0,7 km, azimut 0,5° |
| Altura por sombra | válida: H = 3.163 m (546 m sobre el terreno de la sombra) |

Al contrario de lo que vio S21a2 el 29-10 y el 13-11 (máscara dominada por borde de nieve en fusión lejos del cráter),
aquí el 92 % del área está a 6 km o menos del cráter y el 79 % es una sola componente pegada a él.

### 2.3 Rótulo (criterio §2.1, leído en las figuras)

Por la letra del criterio no calza limpio en ninguno de los dos rótulos positivos: no es **PLUMA VISIBLE** porque no se
alarga en una dirección (1,7 por 1,0 km, cociente 1,7); no es **BOCANADA CHICA** porque mide 1,35 km² en la máscara y
2,9 km² en la SCL, más que el límite de 0,5 km² que escribí. Tampoco es SIN PLUMA VISIBLE (nace en el cráter) ni NO
DECIDIBLE (la cumbre está despejada y no hay nubes parecidas fuera del volcán). **Lo rotulo BOCANADA, mayor que el
límite**, que es como S20b llamó a la del 08-11 (compacta, de unos 2,5 km, pegada al cráter). Para la hoja de ruta
cuenta como verdad de presencia de nube volcánica sobre el cráter a las 14:43 UTC, no como verdad de dirección.

Lo que no puedo separar con esta imagen: una nube de capuchón orográfico sobre la cumbre se vería parecida. Lo hacen
menos probable que sea la única nube de ese tamaño en 15 km a la redonda, que nazca justo en el cráter activo y las
hebras grises que salen de él. No revisé si el otro cono del complejo, al noroeste, tiene nube: la franja de la
escena lo corta. La cámara del OVDAS en ese minuto lo cerraría.

## 3. Qué significa

1. La primera repetición independiente de la firma de ceniza a 100 m (S21a1, 25-10) sigue sin hacerse. No es que la
   pasada del 26-11 haya fallado: no está publicada. Con la nieve retirándose, aunque llegue despejada puede que la
   regla no encuentre pluma sobre nieve (el 25-11 la nieve ya cubría sólo el 24 % del círculo de 5 km).
2. La Sentinel-2C del 25-11 agrega una mañana más con nube volcánica sobre el cráter vista a 10 m, a la hora de pasada
   de media mañana. Es verdad de presencia para el futuro; no se cruzó con el detector GOES.

## 4. Lo que puede estar mal

- El rótulo es juicio visual mío sobre tres figuras; Nicolás lo puede revisar en
  `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\Goes\docs\own_volcat\s31g_landsat_26nov\figuras\s2_2026-11-25_zoom.png`.
- El criterio no previó una nube compacta mayor que 0,5 km²; la llamé bocanada después de verla. Eso no cambia nada
  que dependa de GOES (no se cruzó), pero queda dicho.
- La referencia compuesta se apoya en una Sentinel-2B del 23-11 con 58 % de nube; la máscara usa sólo las celdas que
  ese día no estaban nubladas (SCL dilatada 3 celdas), y lo que sobra lo pone la Landsat 9 del 18-11.
- La altura por sombra mide la parte baja y más densa de la nube; la hebra gris del oeste puede estar a otra altura.

## 5. Siguiente paso

- Cuando USGS publique la Landsat 8 del 26-11 (esperable 01 a 10-12): agregarla a `CAND` de
  `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\Goes\docs\own_volcat\s21a1_ventana_partida\scripts\s21a1_seleccion.py`,
  aplicar la regla sin cambios, commitear la elección y sólo entonces medir con los parámetros del criterio §1.1.
- Lo mismo para la Landsat 9 del 04-12.
