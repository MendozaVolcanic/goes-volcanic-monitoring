# Guía de revisión del dashboard GOES — qué mirar y cómo interpretarlo

> Para el geólogo de guardia (OVDAS/SERNAGEOMIN). Objetivo: saber **qué revisar**
> en cada vista, **cómo interpretarlo** y **qué NO sobre-leer**. Última actualización:
> 2026-08-30. App: https://mendozavolcanic-goes-volcanic-monitoring.hf.space

## Regla de oro (leer siempre)

- **VOLCAT/SSEC es el número cuantitativo de referencia.** Todo lo etiquetado
  **INDICATIVO** (altura propia, β-ratios) es cross-check, NO reemplaza a VOLCAT.
- **Resolución máxima del sensor:** ceniza/altura = **2 km** (IR de GOES-19, es el
  máximo físico); imagen visible/GeoColor = **0.5 km**. No hay ceniza IR más fina.
- **Ceniza ≠ gas.** Una pluma de SO₂/gas es transparente en 11 µm → NO da altura
  válida. Si el dashboard dice "pluma de SO₂/gas sin ceniza", es correcto, no un bug.

---

## Vista por vista — qué revisar

Son **11 vistas**, todas con permalink `?vista=<slug>` (se puede pegar el link en
el chat del turno y cae en la misma pantalla). Cada una tiene su expander
"📖 Cómo interpretar" arriba; esto es el resumen de guardia.

### 1. 🌎 Vista Operacional — `?vista=operacional`
El visor en vivo, auto-refresh 60 s. Sub-tabs Nacional / Zona / Volcán, más el
tab 🔬 Volcán con los 4 productos a la vez.
- **Ash RGB**: tonos **rojo/rosa** = ceniza probable. Cirros y nieve dan falsos
  positivos 30-60 % en invierno chileno — cruzar con BTD y SO₂.
- **SO₂ (JMA)**: **verde intenso = SO₂ denso**; verde-amarillo = SO₂ con ceniza;
  **rosado/magenta = ceniza**, no gas. (El magenta acá engaña: es la misma firma
  térmica del Ash RGB.)
- **GeoColor 0.5 km**: contexto visible diurno; de noche pasa a IR pseudo-color.
- Toggles: viento GFS (vectores 300/500/850 hPa) y hot spots FDCF (diamantes, FRP).
- **Qué revisar:** ¿hay ceniza (rojo Ash + BTD negativo) o sólo SO₂? ¿coincide un
  hot spot con actividad reportada?
- **Qué NO sobre-leer:** el rojo del Ash RGB solo. Sin BTD negativo ni movimiento
  desde el cráter en el loop, es cirro hasta que se demuestre lo contrario.

### 2. 🛡 Modo Guardia — `?vista=guardia`
Vista de sala, pensada para proyectar. Tres sub-tabs:
- **Por Zona Volcánica** — las 4 zonas (Norte, Centro, Sur, Austral) lado a lado,
  mismo producto y mismo timestamp.
- **Mosaico** — los prioritarios con sus 3 productos en la misma fila.
- **Volcán (4 productos)** — GeoColor, Ash RGB, SO₂ y VOLCAT juntos, en orden de
  lectura de emergencia: ¿hay columna? → ¿es ceniza? → ¿es gas fresco? → ¿qué altura?
- El botón rojo **Modo Sala** entra a fullscreen y rota productos cada 10 s.
- **Qué NO sobre-leer:** el **panel VOLCAT vacío es el estado normal**. VOLCAT
  sólo dibuja cuando detecta ceniza; su ausencia no es una falla del sistema.

### 3. 🔀 Comparador — `?vista=comparador`
Dos productos lado a lado (mismo volcán y timestamp) o modo **sustracción** RGB−RGB.
- **Uso clásico:** descartar cirro. Si la señal roja del Ash aparece también en
  GeoColor como pluma que se mueve desde el cráter, es ceniza; si está sólo en
  Ash, muy probablemente es cirro o nieve.
- **Qué NO sobre-leer:** la sustracción se hace en RGB normalizado, **no en
  Kelvin**. Para diferencias cuantitativas ir a "Ash + BTD".

### 4. 🚨 Modo Evento — `?vista=evento`
Pantalla focalizada para **crisis activa**: todo sobre un volcán sin navegar tabs.
Header con countdown desde el inicio marcado, grid de 3 productos, y **tabla de
hot spots FDCF dentro de 50 km ordenados por FRP (MW)** — la magnitud cuantitativa
de la anomalía térmica.
- **Qué revisar:** que el FRP suba o baje entre scans, no su valor absoluto.
- **Qué NO sobre-leer:** el FRP no es tasa de emisión de ceniza. Una explosiva con
  ceniza fría puede no calentar el píxel y dar FRP cero con columna de 10 km.

### 5. 📅 Heatmap actividad — `?vista=heatmap`
Dos escalas del mismo dato FDCF: el **pulso térmico intradía** (curva de FRP a
cadencia ~10 min — el aporte único de un geoestacionario) y el **panorama semanal**
(nº de scans con detección por volcán y día = persistencia).
- **Qué NO sobre-leer:** este panel está en **cero la mayor parte del tiempo** y
  eso es correcto. FDCF se enciende con lava expuesta, no con ceniza. Celdas
  aisladas suelen ser incendios cercanos o reflejo solar especular.

### 6. 🔁 Replay reciente — `?vista=replay`
Animación pre-cocinada de las últimas horas de un volcán, con slider frame a frame.
Es la vista de **entrega de turno**: qué pasó mientras no mirabas.

### 7. 📅 Backfill histórico — `?vista=backfill`
Reconstrucción de eventos pasados desde L1b crudo, fuera de la ventana del archive
de RAMMB (~28 días). Se alimenta del workflow manual `backfill_build.yml`.
- **Qué NO sobre-leer:** el perfil GFS que usa el retrieval de altura es NRT, no de
  archivo, así que **la altura propia sobre un evento viejo no es confiable**.

### 8. 🌡 Ash + BTD (temperaturas K) — `?vista=ash`
La versión **cuantitativa**: números físicos desde bandas L1b, no composite.
BT(11,2 µm), BTD split-window (**< −1,0 K** = ceniza, umbral Prata 1989) y BTD
tri-espectral (**< 0 K**, filtra parte de los cirros). El hover da el valor exacto
en Kelvin. Es acá donde se resuelve la duda que el Ash RGB deja abierta.

### 9. 📏 VOLCAT (altura pluma) — `?vista=volcat`
El corazón cuantitativo. Productos SSEC: Ash_Height (km AMSL), Loading (g/m²),
Probability (%), Reff (µm). **Filtrar por Probability > 60 %.** Incluye el overlay
de VAA activos y, debajo, la sección de altura propia (ver más abajo).
- **Qué NO sobre-leer:** lo que se muestra es el **render PNG** del producto, no el
  dato gridded certificado; y sólo 3 volcanes chilenos tienen sector dedicado — el
  resto cae en un regional de 2 km.

### 10. 🎞 Loops descargables — `?vista=loops`
Genera MP4 / GIF / ZIP de frames por volcán, producto y ventana. Para informes,
presentación de turno o comunicación pública. Loops > 6 h: generar por tramos.

### 11. 📈 Series de tiempo — `?vista=series`
Tendencia por volcán de la fracción de píxeles con firma de ceniza/SO₂ (1-24 h),
con thumbnails del PICO y del ÚLTIMO scan.
- **Qué NO sobre-leer — importante:** el "% ash" es un indicador **de color**, no
  un retrieval radiativo. Medido sobre los 8 prioritarios **sin actividad** da
  entre 10 % y 95 %. Sirve para mirar la **variación** de una curva; **ningún
  umbral absoluto sobre este número significa nada**.

> **Slugs viejos que siguen funcionando** (redirigen solos, no rompen bookmarks):
> `?vista=live` → operacional · `?vista=zonas` → guardia · `?vista=animacion` → loops.

---

## La sección "Altura del tope · propia (INDICATIVO)" — cómo leerla

Aparece tras apretar el botón (baja bandas + ACHA + perfil GFS). Muestra **3 métodos
sobre los MISMOS píxeles de ceniza** de un scan:

| KPI | Qué es | Cómo leerlo |
|---|---|---|
| **ACHA NOAA** | Altura de tope de nube de NOAA (L2, Heidinger OE), 2 km | Referencia externa; puede decir "sin retrieval" sobre ceniza fina |
| **BT-matching · cota** | BT(11µm) del tope → perfil GFS T(z) | **Cota inferior** — subestima plumas semitransparentes |
| **Wen-Rose · corregido** | Corrige emisividad con 11/12 µm → tope más frío | **El número propio de referencia**; sube sobre la cota |

**Línea de confianza** (debajo de los KPI): `baja / media` (nunca "alta" — es
indicativo) + confirmaciones y avisos:
- **`CO₂ 13.3µm ✓ semitransp.`** → un canal INDEPENDIENTE confirma que la pluma es
  semitransparente ⇒ la corrección Wen-Rose es real (buena señal).
- **`β-ratios ✓ silicato`** → la composición (Pavolonis 2010, canales 8.5/11/12)
  confirma **ceniza silicatada**, no hielo/agua (buena señal). Si dice
  **"β-ratios sugieren 'hielo'/'agua' (no silicato)"** → posible **falso positivo**
  (cirros), desconfiar del tope.
- **Avisos ⚠ (flags)** a vigilar:
  - `tope < 3 km` o `> 12 km`: fuera de la **banda fiable** (Saint 2024) → confianza baja.
  - `régimen opaco+alto`: ceniza gruesa/espesa → el tope es **cota inferior**, puede
    subestimar plumas altas.
  - `Ts de fallback` / `fondo heterogéneo`: el fondo cálido se estimó mal → corrección
    menos confiable.
  - `detección chica (N px)`: pocas muestras → estadístico ruidoso.

**Sesgo conocido a tener en cuenta:** los retrievals IR de altura **subestiman
sistemáticamente ~0.4–0.8 km** (el IR recibe emisión de toda la capa, no solo del
tope). Wen-Rose corrige parte de eso; aun así, tratá el número como **piso indicativo**.

**Cuándo confiar más:** los 3 métodos concuerdan (|Δ| ≤ 2.5 km) + CO₂ ✓ + β-ratios ✓
silicato + tope en 3–12 km + varios píxeles. **Cuándo desconfiar:** β dice no-silicato,
tope fuera de 3–12 km, pocos píxeles, o solo SO₂ sin ceniza.

---

## Checklist rápido de guardia

1. ¿Hay ceniza (Ash RGB rojo **y** BTD negativo) o solo SO₂/gas?
2. Si hay ceniza: ¿qué dice VOLCAT Ash_Height (Probability > 60%)? Ese es el número.
3. Cross-check propio (INDICATIVO): ¿Wen-Rose y ACHA concuerdan? ¿CO₂ y β-ratios
   confirman (semitransp. + silicato)? ¿el tope cae en 3–12 km?
4. ¿Algún flag ⚠ activo? Ajustar la confianza en consecuencia.
5. ¿Hay VAA activo o hot spot que corrobore?
6. Recordar: número cuantitativo = **VOLCAT**; lo propio = respaldo indicativo.

---

## Notas de resolución y límites (para no sobre-vender)

- Ceniza/altura = **2 km** (máximo IR de GOES-19). Para 250 m hay que pedir sectores
  a SSEC (ver `docs/EMAIL_SSEC_sectores_chillan_villarrica.md`: reactivar
  `Villarrica_250_m` + crear Chillán + acceso al dato gridded/NetCDF).
- La altura propia es **INDICATIVA** — método térmico de 2 canales, sin optimal
  estimation ni RTM (eso lo tiene VOLCAT). Detalle técnico: `docs/own_volcat/`.
- **Pendiente (no cableado aún):** árbitro de altura por **cizalla de viento**
  (Fase 3c) — se activará como 4º método cuando se valide en un evento real.
