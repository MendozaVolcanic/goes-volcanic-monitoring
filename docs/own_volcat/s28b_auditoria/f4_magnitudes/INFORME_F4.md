# S28b, frente F4: magnitudes y geometría. Informe del auditor, 26-11-2026

**Ningún hallazgo de F4 cambia un veredicto.** 8 hallazgos (IDs 401 a 408): 0 de gravedad 4 o 5, 2 de gravedad 3, 4 de
gravedad 2, 2 de gravedad 1. Uno (402) toca las confirmaciones congeladas y pasa al verificador por la regla del §5 del
plan aunque su gravedad sea 3. **Línea base roja: salió** (ver §1).

- Base auditada: `origin/main` 8894722; plan `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\Goes\.claude\worktrees\s28b-auditoria-s23-s28a-c1cff8\docs\own_volcat\s28b_auditoria\PLAN.md` (commit 002feff), leído entero antes de empezar.
- Auditor: Claude Opus 5.5, esfuerzo de la sesión. Python usado: `C:\Users\nmend\AppData\Local\Programs\Python\Python312\python.exe -I` (el `python` del PATH de la sesión; no es el de Anaconda, pero trae numpy, scipy y pyproj 3.7.2).
- Qué corrí: sólo geometría (latlon de la ventana, DEM, paralaje), máscaras ACM de días hasta el 24-11-2026 y la función
  `Detector.base` original con datos sintéticos. No corrí el detector, no abrí cuadros posteriores al 24-11, no bajé
  nada, no toqué ningún fuente fuera de mi carpeta y de `D:\goes_notas\s28\s28b\f4\`. D: con 24 GB libres al empezar.
  Salvedad: al importar los módulos auditados, Python dejó bytecode en carpetas `__pycache__` de sus `scripts\` y de
  `src\` (ignoradas por git; `git status` sólo muestra las carpetas `s28b_auditoria\f*`). Otros frentes corren en el
  mismo worktree y también importan, así que no los borré. Para la próxima: `python -I -B`.
- Scripts (todos en `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\Goes\.claude\worktrees\s28b-auditoria-s23-s28a-c1cff8\docs\own_volcat\s28b_auditoria\f4_magnitudes\scripts\`):
  `f4_geometria.py`, `f4_zona_paralaje.py`, `f4_costumbre_vecinas.py`, `f4_registro_anios.py`, `f4_controles_cota.py`,
  `f4_linea_base_roja.py`. Salidas en `D:\goes_notas\s28\s28b\f4\` (`f4_geometria.json`, `f4_zona_paralaje.json`,
  `f4_costumbre_vecinas.json`, `f4_registro_anios.json`, `f4_controles_cota.json`).
- Cada script se corre con `python -I <ruta absoluta del script>` desde cualquier carpeta.

## 0. Cómo mide distancias y rumbos el detector (la respuesta corta a las preguntas del encargo)

- **Georreferencia**: `latlon.npz` (`D:\goes_notas\local_f3a7d295\cache_rescatada\reproducir_volcat\latlon.npz`, hecho
  por `docs/own_volcat/reproducir_volcat/scripts/ventana.py`) es la grilla fija del ABI de 2 km proyectada al
  **elipsoide GRS80, sin terreno**, con origen de proyección −75,0°. La reproduje sola con pyproj: diferencia máxima
  1,3e-5° en latitud y 7e-6° en longitud con −75,0°; con −75,2° la longitud se va 0,2° (`f4_geometria.json`,
  `latlon_vs_grilla_fija_*`).
- **Distancia**: haversine en esfera de 6.371 km entre el **centro** de cada píxel (posición elipsoidal) y la coordenada
  **verdadera** del cráter (-36,863; -71,377) (`h29_pluma_0811/scripts/h29_comun.py:36,48-54`). No usa terreno ni
  paralaje. Contra la distancia geodésica GRS80: error máximo 0,23 %, 2 píxeles cambian de anillo y 0 de zona.
- **Acimut y tajadas**: plano local `x = Δlon·111,32·cos(lat del cráter)`, `y = Δlat·110,57`, acimut desde el N hacia el
  E, tajada k = [30k, 30k+30) (`s22a_medir.py:84-86,92`). Contra el acimut geodésico: diferencia máxima 0,21°, 2 de 837
  píxeles cambian de tajada. En las vecinas, `cos` de la latitud de la vecina (`s28a_medir.py:74`): bien.
- **Cota**: `dem_ventana.npz` (`D:\goes_cache\etapa3_chillan\dem_ventana.npz`, de
  `lut_h15/etapa3_chillan/scripts/e3_dem.py`) proyecta cada celda del DEM **con su altura** sobre la grilla fija: es la
  cota del terreno que cada píxel VE (geometría aparente). Es lo correcto para el pareo de ±300 m.
- **Píxel ABI de 2 km** (distancia entre centros vecinos, `f4_geometria.json`): Chillán 2,849 km N-S × 2,088 km E-O
  (5,95 km²), Antuco 2,882 × 2,090 (6,02 km²), Longaví 2,812 × 2,086 (5,87 km²). Igual para GOES-16 (2024) y GOES-19:
  la grilla fija es la misma (I5 de S25b: mismos atributos de proyección).
- **Paralaje** (ángulo cenital del satélite en 75,0° y 75,2° O): Chillán 42,93° (tan 0,930), Antuco 43,54° (0,950),
  Longaví 42,20° (0,907). La cumbre de Chillán (3,21 km) se ve 2,99 km al rumbo 174° (línea de vista exacta de
  `src/process/vrp_nocturno.cumbre_aparente`); una pluma a 4,2 y 5,2 km sobre el mar, 3,92 y 4,85 km al mismo rumbo.

## 1. Línea base roja: salió

Encontré la constante de Chillán leyendo `s23_medir.Detector.base`, **antes de abrir `s28a_medir.py` y sin leer el
INFORME de S28a** (que no leí en ningún momento):
`C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\Goes\.claude\worktrees\s28b-auditoria-s23-s28a-c1cff8\docs\own_volcat\s23_fondo_2025\scripts\s23_medir.py:207`
`Bs = np.full((144, M.NA), np.nan, np.float32)`. El mismo `M.NA` (837, el anillo de Chillán) aparece en
`s23_medir.py:50` (`_m1_dia`) y `:172` (blanco de `Detector.__init__`), que S28a no usa para las vecinas.

S28a la corrigió en `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\Goes\.claude\worktrees\s28b-auditoria-s23-s28a-c1cff8\docs\own_volcat\s28a_vecinas\scripts\s28a_medir.py:167-181`
(`Anillo.base` con `self.geo.NA`). Comprobé además cómo habría fallado sin la corrección
(`f4_linea_base_roja.py`): la función original con el largo de cada geometría de S28a lanza
`ValueError: could not broadcast input array from shape (552,) into shape (837,)` (y lo mismo con 831, 641 y 851); con
837 corre. La versión de S28a devuelve (144, 552), (144, 831), (144, 641), (144, 851). **El error habría sido ruidoso,
no silencioso**: no hay forma de que un `s28a_resultado.json` exista con la base de largo equivocado. Busqué el resto de
`M.*` y `C29.*` de Chillán en el código generalizado (`grep` de `M.NA|AP|SEC|NPS|CTRL|...`, `C29.DIST|CRATER`,
`"chillan"` en s23, s25a, s26a, s27a, s28a): lo que queda está en 404, 405 y 407.

## 2. Hallazgos (lo peor primero)

### 401. La "zona de 0 a 4 km del cráter" no está centrada donde GOES ve el cráter ni cabe en 4 km

- ARCHIVO:LÍNEA: `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\Goes\.claude\worktrees\s28b-auditoria-s23-s28a-c1cff8\docs\own_volcat\s25a_crater\scripts\s25a_medir.py:43`
  (`ZONA = (C29.DIST < 4.0) | M.BLOQUE`); `s22a_medir.py:36,87-88` (`CRATER_PX = (42, 46)`, bloque 3 × 3);
  `h29_comun.py:36,54`. Rótulo en `s25a_crater/INFORME.md:1`, `s26a_combinado/INFORME.md:15`,
  `s27a_noche_causa/INFORME.md:16`, `s28a_vecinas/INFORME.md:15`, `s24_dia14_noche/INFORME.md:83`, `STATUS.md:429,439`.
- QUÉ PASA: el radio se mide desde la coordenada verdadera sobre la georreferencia del elipsoide. Sólo 8 de los 11
  píxeles tienen centro a menos de 4 km; los 3 de la fila 43 entran por el bloque, a 4,64, 4,99 y 5,18 km. El bloque
  está centrado en (42,46), una fila al S del píxel más cercano a la coordenada verdadera (41,46): (42,46) es justo donde
  GOES ve la cumbre. Respecto de la cumbre aparente (línea de vista exacta) 5 de los 11 píxeles quedan a más de 4 km
  ((40,46) a 6,95 km) y una pluma a 1 a 2 km sobre el cráter se ve en (43,46), a 4,64 km de la coordenada verdadera:
  fuera del radio, dentro sólo por el bloque. El criterio de S25a (§1) lista los 11 píxeles y dice "de 1,2 a 5,2 km":
  la regla es honesta; lo que engaña es el nombre que viaja a los informes y a `STATUS.md`. No falta cobertura: zona y
  anillo juntos cubren todo píxel a 40 km o menos (por construcción), y los píxeles a menos de 4 km de la cumbre
  aparente que no están en la zona ((42,48), (43,48); con pluma (44,46), (44,47)) están en el anillo.
- CÓMO SE VE EN EL VEREDICTO: no cambia ningún veredicto (S25a ALCANZA y S26a se midieron sobre esos 11 píxeles tal
  cual). Cambia su lectura: "zona de 0 a 4 km del cráter" se lee como distancia física al cráter y no lo es; los píxeles
  del N de la zona ven terreno a 4 a 7 km del punto donde GOES ve la cumbre, y una pluma sobre el cráter cae en el borde
  S de la zona. S27a ya lo había visto (`s27a_noche_causa/INFORME.md:25`, "la zona está centrada en el cráter real y,
  corregida por paralaje, mira casi sólo al norte"); el criterio de S25a no menciona el paralaje.
- CÓMO REPRODUCIRLO: `python -I ...\scripts\f4_geometria.py` y `python -I ...\scripts\f4_zona_paralaje.py`; ver
  `D:\goes_notas\s28\s28b\f4\f4_geometria.json` (`zona_S25a`: n 11, n_dist_lt4 8, n_solo_bloque 3, CRATER_PX [42,46],
  argmin_DIST [41,46]) y `f4_zona_paralaje.json` (`chillan_S25a.h_3.21_km`: corrimiento 2,99 km, rumbo 174,0, píxel
  (42,46), 5 píxeles de la zona a más de 4 km del aparente; `h_4.21_km` y `h_5.21_km`: píxel (43,46)).
- CONFIANZA: CONFIRMADO. GRAVEDAD: 3.

### 402. La geometría de las tres confirmaciones congeladas se lee de D: sin guarda

- ARCHIVO:LÍNEA: `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\Goes\.claude\worktrees\s28b-auditoria-s23-s28a-c1cff8\docs\own_volcat\h29_pluma_0811\scripts\h29_comun.py:31-35`
  (`LATLON`, `DEM`, `np.load` al importar) y `h24_pulsos_reav/scripts/h24_medir.py:27-33` (las mismas rutas);
  `s23_fondo_2025/scripts/s23b_confirmar.py:39,160-162` y `s26a_combinado/scripts/s26a_medir.py:71` (sólo se hashea
  `estat_2026.npy`).
- QUÉ PASA: ZONA, anillo, tajadas, controles, controles por cota y el M1 de los días nuevos salen de `latlon.npz` y de
  `dem_ventana.npz` en el momento de importar. Ninguno de los dos tiene hash, y `latlon.npz` ya se perdió una vez y se
  reconstruyó (docstring de `reproducir_volcat/scripts/ventana.py:1-4`); vive en una carpeta llamada
  `cache_rescatada`. Si alguien los regenera antes de la medida única, el M1 de los días nuevos queda calculado con otra
  geometría que la base y el umbral de 2025 (`r25_m1.npy`), sin que nada falle.
- CÓMO SE VE EN EL VEREDICTO: hoy no cambia nada: los archivos son anteriores a toda medida de S22a en adelante
  (`latlon.npz` 20-11-2026 11:55, `dem_ventana.npz` 21-11-2026 16:10; `r25_m1.npy` 25-11 02:26). Cambia: SIN DATO, para
  el día de la medida única de S23b, S25a y S26a. Huellas de hoy (primeros 16 hex del SHA-256 de los bytes del archivo):
  `latlon.npz` 79350e4b01cc86be, `window.json` e208534e10914c0d, `dem_ventana.npz` 409e9cce836788c5.
- CÓMO REPRODUCIRLO: `stat -c "%y %s %n" <archivo>` y `sha256sum <archivo>` sobre
  `D:\goes_notas\local_f3a7d295\cache_rescatada\reproducir_volcat\latlon.npz`,
  `D:\goes_notas\local_f3a7d295\cache_rescatada\reproducir_volcat\window.json` y
  `D:\goes_cache\etapa3_chillan\dem_ventana.npz`; `grep -n "sha\|hashlib" s23b_confirmar.py s26a_medir.py`.
- CONFIANZA: CONFIRMADO (la ausencia de guarda); el riesgo es SOSPECHA. GRAVEDAD: 3. **Toca una confirmación congelada:
  va al verificador** (plan §5). Seguimiento F3.

### 403. Rumbos y distancias de S24 en geometría aparente, leídos como físicos

- ARCHIVO:LÍNEA: `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\Goes\.claude\worktrees\s28b-auditoria-s23-s28a-c1cff8\docs\own_volcat\s24_dia14_noche\scripts\s24_medir.py:33,43-47`
  (bandas de distancia desde el cráter verdadero y giro de 180° alrededor de él, `M.AX`, `M.AY`);
  `s24_dia14_noche/INFORME.md:31-38` (huella del 14-11 "la mitad dentro de los primeros 4 km"; tajada SE 120° a 150°
  "donde VOLCAT termina dibujando la pluma").
- QUÉ PASA: la huella de VOLCAT y las tajadas del detector están en la misma geometría aparente (bien para compararlas
  entre sí), pero distancia y rumbo se miden desde la coordenada verdadera. Algo a 4,2 o 5,2 km sobre el mar se ve 3,9 a
  4,9 km al SSE: su rumbo aparente gira, de media, 31° a 42° a 5 km, 14° a 18° a 10 km y 7° a 9° a 20 km, y cambia de
  tajada en 78 a 83 %, 47 a 59 % y 24 a 29 % de los rumbos. El giro de 180° alrededor del cráter verdadero en vez del
  punto de emisión aparente corre el control unos 2 × 3,9 = 7,8 km. Una pluma que va al S se ve unos 4 km más lejos de
  lo que está; una que va al N, unos 4 km más cerca.
- CÓMO SE VE EN EL VEREDICTO: no cambia ninguno (A de S24 es INVÁLIDA por su regla; S24c se abandonó). Cambia la lectura
  de la pista "rumbo SE persistente" del 14-11 (el rumbo físico de una pluma a 4 a 5 km queda girado hacia el E respecto
  del aparente) y de "la mitad de la huella dentro de 4 km". S27a, S27b y S22c sí corrigen por paralaje.
- CÓMO REPRODUCIRLO: `python -I ...\scripts\f4_zona_paralaje.py`; `D:\goes_notas\s28\s28b\f4\f4_zona_paralaje.json`,
  bloque `giro_tajada_por_paralaje`.
- CONFIANZA: CONFIRMADO (la geometría); su efecto en la lectura del 14-11 es SOSPECHA. GRAVEDAD: 2.

### 404. La zona de las vecinas no es "como Chillán": otro centrado del bloque, 9 y 10 píxeles, medio km más baja

- ARCHIVO:LÍNEA: `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\Goes\.claude\worktrees\s28b-auditoria-s23-s28a-c1cff8\docs\own_volcat\s27a_noche_causa\scripts\s27a_medir.py:268-276`
  (`zona_de`: bloque en el píxel más cercano); `s27a_noche_causa/criterio_2026-11-25.md:82-83` ("bloque de 3 × 3
  alrededor del píxel más cercano (como Chillán: distancia más `BLOQUE`)"); `s28a_vecinas/criterio_2026-11-25.md:47-48`;
  `s25a_medir.py:45` (`MIN_ZONA, NBAJOS = 6, 2`, fijos).
- QUÉ PASA: el bloque de Chillán NO está en el píxel más cercano (está en (42,46), el más cercano es (41,46)); el de las
  vecinas sí. Resultado: Chillán 11 píxeles, Antuco 9, Longaví 10, y el mínimo de 6 píxeles con dato (6 de 11 en
  Chillán) pasa a 6 de 9. La cota media de la zona: mediana 2.495 m en Chillán, 1.962 m en Antuco y 2.022 m en Longaví
  (anillos parecidos: medianas 1.513, 1.589, 1.459 m). En las tres la cumbre aparente cae dentro de la zona ((42,46),
  (64,46), (16,57)); en Longaví una pluma a 2 km sobre la cumbre caería fuera ((17,57)), sin efecto porque no hay pluma.
- CÓMO SE VE EN EL VEREDICTO: no cambia (S27a N es NO DECIDIBLE; S28a compara cada vecina consigo misma entre años).
  Cambia la lectura de la prueba de nieve: la zona de las vecinas mira terreno medio kilómetro más bajo que la de
  Chillán, así que "la misma regla en una cumbre sin pluma" no es el mismo terreno. Efecto sobre las tasas: SIN DATO.
- CÓMO REPRODUCIRLO: `python -I ...\scripts\f4_controles_cota.py` (`D:\goes_notas\s28\s28b\f4\f4_controles_cota.json`,
  `zona.cotas_m`) y `python -I ...\scripts\f4_zona_paralaje.py` (`bloque_centrado_en`, `pixel_que_la_contiene`).
- CONFIANZA: CONFIRMADO. GRAVEDAD: 2.

### 405. El nublado de costumbre de las vecinas sale de Chillán (E1 de Chillán; en 2026, además, cuadros N de VOLCAT de Chillán)

- ARCHIVO:LÍNEA: `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\Goes\.claude\worktrees\s28b-auditoria-s23-s28a-c1cff8\docs\own_volcat\s28a_vecinas\scripts\s28a_medir.py:350,396`
  (`est25_anillo = X.A.ESTAT`, `est25_zona = Z.costumbre(...)`), `s25a_medir.py:119` (`despejada("chillan")`),
  `s23_medir.py:141-156` (E1 de Chillán), `s23_lado_a_lado.py:123` (el congelado de 2026 sale de `Detector(ref="2026N")`:
  cuadros N de VOLCAT de Chillán). Declarado en `s28a_vecinas/criterio_2026-11-25.md:59-60`.
- QUÉ PASA: qué píxel es "nube de costumbre" (y por eso qué nube es dinámica, qué cuadro pasa la compuerta y qué píxel
  se borra) se decide con los cuadros despejados sobre el terreno bajo de Chillán, no de la vecina. Medí la compuerta
  del anillo completo de cada vecina con esos mapas y con uno propio construido igual en los dos años (E1 de la vecina,
  todos los cuadros con dato): de noche da lo mismo (Antuco 0,486 contra 0,487; Longaví 0,422 contra 0,422); de día, en
  2026, Antuco 0,274 contra 0,259 y Longaví 0,322 contra 0,292; en 2025, idéntico. Cambian de compuerta 116 y 92 cuadros
  de 2026 (y 4 y 9 de 2025).
- CÓMO SE VE EN EL VEREDICTO: no cambia lo que medí (la razón 2026/2025 de cuadros que pasan la compuerta de día pasa de
  0,515 a 0,487 en Antuco y de 0,480 a 0,436 en Longaví). El efecto sobre los disparos y sobre R de S28a no lo medí: SIN
  DATO. Informativo para F2: en los cuatro mapas de 2026 (usado y propio) la costumbre marca de 4 a 7 veces más píxeles
  del anillo que en 2025 (Antuco 83,9 contra 12,2 por hora), así que la asimetría entre años de la compuerta es del cielo
  o la nieve de 2026, no de la construcción.
- CÓMO REPRODUCIRLO: `python -I ...\scripts\f4_costumbre_vecinas.py`; `D:\goes_notas\s28\s28b\f4\f4_costumbre_vecinas.json`.
- CONFIANZA: CONFIRMADO. GRAVEDAD: 2.

### 406. La frontera de 45 km (controles y exclusión de tajadas de S28a) es distancia aparente

- ARCHIVO:LÍNEA: `s22a_medir.py:37,94` (`R_CTRL`, `CTRL = DIST > 45`), `s25a_medir.py:51`, `s28a_medir.py:80,89`.
- QUÉ PASA: "lo que está a más de 45 km del cráter no ve su pluma" se mide sobre la posición aparente. Una pluma de
  Chillán a 1 a 2 km sobre la cumbre se ve 3,9 a 4,9 km más al SSE: hacia el S (Antuco) la frontera física queda en
  unos 40 a 41 km; hacia el N (Longaví), en unos 49 a 50 km.
- CÓMO SE VE EN EL VEREDICTO: no cambia (los 45 km son una convención y S28a comprobó que la exclusión no cambia con 40
  ni 50 km en Antuco, `s28a_vecinas/criterio_2026-11-25.md:71-72`). Lectura: la frontera no es simétrica en kilómetros
  físicos.
- CÓMO REPRODUCIRLO: corrimiento y rumbo en `f4_zona_paralaje.json` (`h_4.21_km`, `h_5.21_km`).
- CONFIANZA: CONFIRMADO (la geometría). GRAVEDAD: 2.

### 407. `despejada` corre el centro del anillo de E1 con el paralaje de Chillán y la cota de la cumbre

- ARCHIVO:LÍNEA: `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\Goes\.claude\worktrees\s28b-auditoria-s23-s28a-c1cff8\docs\own_volcat\h24_pulsos_reav\scripts\h24_medir.py:179-184`
  (`hav(LAT, LON, la - 0.93 * h / 1000.0 / 111.2, lo)`), `h24_medir.py:40` (`PARALAJE = 0.93`).
- QUÉ PASA: el terreno bajo (< 1.300 m) se mide en un anillo de 10 a 30 km centrado 0,93 × cota de la cumbre al S (2,8
  a 3,0 km), aunque ese terreno tiene a lo más 1,2 km de paralaje; y el 0,93 es el de Chillán (Antuco 0,950, Longaví
  0,907, diferencia ≤ 0,07 km).
- CÓMO SE VE EN EL VEREDICTO: no cambia (2 a 3 km sobre un anillo de 20 km de ancho).
- CÓMO REPRODUCIRLO: lectura de código; tangentes en `f4_geometria.json` (`paralaje_km_por_km_*`).
- CONFIANZA: CONFIRMADO. GRAVEDAD: 1.

### 408. El poder por inyección traza la pluma recta desde el cráter verdadero

- ARCHIVO:LÍNEA: `s22a_medir.py:296-302` (`pixeles_rayo`), usado por `s23_medir.py:383` (poder de S23a).
- QUÉ PASA: la pluma sintética son los 8 píxeles del anillo a 20 km o menos más cercanos a una recta que sale del cráter
  verdadero. Una pluma real a 4 a 5 km sale de la cumbre aparente, 3,9 a 4,9 km al SSE, y su rumbo aparente gira (403):
  sus píxeles pueden repartirse en dos tajadas, lo que bajaría la cola de cada una.
- CÓMO SE VE EN EL VEREDICTO: ninguno de S23 a S28a usa el poder en la rama que decidió (S23a PARCIAL no llega a la rama
  SIN PODER; `s23b_confirmar.py` no tiene rama SIN PODER; S26a lo informa). Efecto en la cifra de poder: SIN DATO.
- CÓMO REPRODUCIRLO: lectura de código; el giro en `f4_zona_paralaje.json`.
- CONFIANZA: SOSPECHA (el efecto); CONFIRMADO (la recta desde el cráter verdadero). GRAVEDAD: 1.

## 3. Censo de constantes (las que deciden)

| Constante | Valor y unidades | Dónde se define | Dónde se lee de verdad | ¿Vale fuera de Chillán? |
|---|---|---|---|---|
| Cráter de Chillán | (-36,863; -71,377), WGS84 | `h29_comun.py:36` | `DIST` (`h29_comun.py:54`), AZ (`s22a_medir.py:84-85`), S27a/S27b/S22c | otras copias: `VENT` (-36,8677; -71,3793), `SITIOS` (-36,86; -71,38); a menos de 0,6 km entre sí |
| Cota de la cumbre | 3.212 m (Chillán), 2.979 (Antuco), 3.242 (Longaví) | `h24_medir.py:37`, `h23_comun.py:20`, `src/volcanos.py:47,48,51` | `despejada` (centro de E1), `cumbre_aparente` de S26b | sí, cada sitio con la suya |
| Antuco, Longaví | (-37,41; -71,35), (-36,19; -71,16) | `h23_comun.py:20` = `h24_medir.py:37` = `s28a_medir.py:47` = `s27a_medir.py:51` = `src/volcanos.py` | `Geo`, `zona_de` | sí |
| Grilla | 83 × 94, filas 4497 a 4579, columnas 2820 a 2913 de la grilla fija FD 2 km, origen −75,0° | `h23_comun.py:14`, `window.json` | toda la cadena; 2024, 2025 y 2026 con el mismo `WIN` | sí; mismo registro en los tres años (§4) |
| Zona | `DIST < 4 km` o bloque 3 × 3 en `CRATER_PX` (42,46): 11 píxeles, 1,18 a 5,18 km, cota 1.952 a 2.874 m | `s25a_medir.py:43`, `s22a_medir.py:36,87-88` | S25a, S26a, S26b, S27a | vecinas: bloque en el píxel más cercano (404) |
| Anillo | 4 a 40 km sin bloque; 837 píxeles, 66 a 74 por tajada | `s22a_medir.py:37,89` | M1, S, compuerta | vecinas: 831 y 851 completos, 552 y 641 usados |
| Controles | `DIST > 45 km`; 6.728 en Chillán; en vecinas > 45 km de las dos: 5.893 y 5.714 | `s22a_medir.py:37,94`; `s28a_medir.py:89` | M1, corrección regional de la zona | sí (406) |
| Pareo de M1 | cota ±300 m (m, DEM visto), BT11 ±0,5 K, mínimo 20 | `s22a_medir.py:38,97,110-111` | M1 | sí: todo píxel de anillo tiene ≥ 97 controles de cota (≥ 438 en Chillán y Antuco); toda zona ≥ 273 |
| Tajadas | 12 de 30°, acimut desde el N hacia el E, origen en el cráter verdadero | `s22a_medir.py:39,86,92` | `estadistico`, `vecinos`, S24c | sí; giro por paralaje (403) |
| Cola | 8 píxeles (≈ 48 km²) | `s22a_medir.py:39` | `estadistico` | el píxel mide lo mismo en los tres sitios (5,87 a 6,02 km²) |
| km por grado | 111,32·cos(lat del sitio) E-O; 110,57 N-S | `s22a_medir.py:84-85`, `s28a_medir.py:74-75`, `s27a_medir.py:45`, `s22c_medir.py:51-52` | acimut, plano local | sí, con la latitud de cada sitio; error ≤ 0,4 % |
| Píxel en km | 2,85 × 2,09 km (Chillán) | `s27b_comun.py:33` (`DELTA_KM = 2.8`), `s26b_fisica.py:11` (A_pix 4,5 a 7,5 km²) | S27b rapidez, S26b fracción caliente | sí |
| Paralaje | tan(cenital) 0,930 / 0,950 / 0,907; subsatélite −75,2° en S27a/S27b/S22c (−75,0° en la grilla) | `h24_medir.py:40-41`, `s27a_medir.py:42`, `s22c_medir.py:37` | S27a (h_ref 4,5 km), S27b, S22c, `despejada` | diferencia −75,2 contra −75,0: 0,0006 en tan (despreciable) |
| BTD y umbrales | K (BT11 − BT12, Planck del NetCDF, C14 → 11,2 µm, C15 → 12,3 µm) | `h29_comun.py:131-134`, `s22b_medir.py:76-77` | todo | GOES-16 con sus propios coeficientes (instrumento_2024.json) |
| Viento | rumbo "hacia donde sopla" = atan2(u, v); m/s; capas en km sobre el mar (HGT del GFS) | `s22c_medir.py:125`, `s27a_medir.py:127` | S27a P, S28a viento, S27b | rumbos fijos de S28a 178° y 15° contra geodésico 177,75° y 14,65° |
| Rapidez (S27b) | d km × 1000 / (Δt min × 60) en m/s contra GFS en m/s; Δt de 20 a 120 min | `s27b_comun.py:76-81`, `s27b_medir.py:87` | S27b | coherente; `DT_MIN = 10` no se usa |

## 4. VERIFICADO LIMPIO (y contra qué vara)

- **Georreferencia de la ventana**: reproducida de forma independiente con la definición de la grilla fija FD 2 km
  (pyproj, GRS80, h 35.786.023 m, origen −75,0°): diferencia máxima 1,3e-5°. Vara: fórmula pública de la grilla fija,
  no el propio archivo.
- **2024 contra 2025 y 2026, misma grilla y mismo recorte**: los tres años bajan con `h23_comun.WIN` (= `window.json`);
  `instrumento_2024.json` registra los atributos de proyección de GOES-16 y GOES-19 iguales (I5) y coeficientes de
  Planck propios de cada satélite. Además medí el registro píxel a píxel con el relieve fino de las noches despejadas
  (campo menos su promedio móvil de 7 × 7): el mejor corrimiento es (0, 0) en 2024 contra 2025 (r 0,977; con una fila
  de corrimiento cae a 0,58 a 0,65), 2026 contra 2025 (0,960) y 2024 contra 2026 (0,978). Control positivo: 2025 contra
  sí mismo corrido una fila da el corrimiento (1, 0). Vara: el relieve, que no se mueve entre años
  (`f4_registro_anios.json`). Una correlación de campos suaves como I4 no podía ver un píxel de corrimiento; ésta sí.
- **Tamaño del píxel**: 2,849 × 2,088 km en Chillán; `DELTA_KM = 2,8` (S27b) y A_pix de 4,5 a 7,5 km² (S26b, contiene
  5,95) están bien. Vara: distancia entre centros vecinos de la grilla.
- **Paralaje**: 0,93 km por km en Chillán (`PARALAJE` de H24) coincide con tan(42,93°) = 0,930; la prueba de S27b
  ("4,7 km se ve 4,0 a 4,6 km al sur") coincide (4,37 km); primer orden contra línea de vista exacta: 2,979 contra
  2,99 km. Vara: dos métodos independientes (`src/process/parallax.py` y `src/process/vrp_nocturno.py`).
- **Lista de la zona de S25a**: los 11 píxeles, "1,2 a 5,2 km" y "1.950 a 2.870 m" del criterio §1 coinciden exactos con
  lo recalculado (`f4_geometria.json`).
- **Geometría de S28a**: anillos 831 y 851 (552 y 641 usados), controles 5.893 y 5.714, zonas 9 y 10, píxeles por tajada,
  tajadas excluidas (0, 1, 10, 11 y 5, 6, 7) con 59, 22, 29, 58 y 3, 24, 4 píxeles bajo 45 km, bordes de la ventana a
  56,1 km de Antuco y 41,6 km de Longaví (el anillo cabe), rumbos y distancias desde Chillán: todo coincide con
  `s28a_resultado.json` y con el criterio. Vara: recálculo propio desde latlon.npz.
- **Las vecinas usan lo suyo**: coordenadas, cota (en `despejada`), anillo, tajadas, acimut con su latitud, controles a
  45 km de ellas y de Chillán, E1 de la base y del umbral. Lo que queda de Chillán está en 404, 405 y 407.
- **DEM**: proyectado con la altura de cada celda (geometría vista), así que el pareo por cota compara lo que el píxel ve.
  Vara: lectura de `e3_dem.py` y comprobación de que el máximo del DEM de Longaví cae en su píxel aparente (16,57).
- **Controles suficientes**: ningún píxel de anillo ni de zona tiene menos de 97 controles de su cota (mínimo exigido 20).
- **Distancias y acimut**: haversine (6.371 km) y plano local contra GRS80: 2 píxeles cambian de anillo, 0 de zona, 2 de
  tajada (diferencia de acimut ≤ 0,21°).
- **Unidades**: BT y BTD en K con la fórmula de Planck del ABI; umbrales de S, U, ±0,5 K y diferencias de umbral de S25b
  en K; cotas en m; distancias en km; S26b mezcla radiancias con VRP en MW → W y área en km² → m²; S27b rapidez en m/s;
  alturas sobre el mar en ZS, en la sombra de 4,7 km (`s22c_altura_propia/criterio_2026-11-24.md:13`) y en el GFS.
- **Rumbos del viento**: todos "hacia donde sopla" y comparados contra rumbos "desde el cráter hacia" (S27a C y
  exposición, S28a quitar por viento, S22c/S27b).
- **Zona más anillo cubren todo píxel a 40 km o menos**: no hay hueco entre las dos regiones.

## 5. SIN DATO

- Efecto de 405 (costumbre de Chillán en las vecinas) sobre disparos y R de S28a: medí sólo la compuerta.
- Efecto del paralaje sobre la cifra de poder por inyección (408).
- Si (-36,863; -71,377) y 3.212 m son el cráter activo (Nicanor) o la cumbre del macizo: no consulté fuente externa. Un
  error de 0,1 km de cota mueve la cumbre aparente 0,09 km.
- IFOV y función de dispersión del ABI a 11 y 12 µm (el píxel "ve" más que la distancia entre centros): no medido.
- Longitud real del subsatélite de GOES-16 en 2024 (`nominal_satellite_subpoint_lon`): no hay NetCDF de 2024 en disco y
  no se podía bajar; sólo cambia el paralaje en menos de 0,001 de tangente por cada 0,1°.
- Diferencia espectral C14/C15 entre GOES-16 y GOES-19 (sesgo de BTD entre satélites): es régimen (F2 g).

## 6. Seguimientos (una línea cada uno)

- F1: el rótulo "zona de 0 a 4 km" del INFORME de S25a, de S26a, S27a, S28a y `STATUS.md` contra "1,2 a 5,2 km" del criterio (401).
- F2: la fracción de cuadros que pasa la compuerta del anillo baja de 2025 a 2026 a 0,62 de noche y 0,46 de día en Chillán (0,61 a 0,72 y 0,48 a 0,52 en las vecinas), con la costumbre de 2026 marcando 4 a 7 veces más píxeles; régimen entre años (`f4_costumbre_vecinas.json`).
- F3: fijar con hash `latlon.npz`, `window.json` y `dem_ventana.npz` en las confirmaciones congeladas (402).
