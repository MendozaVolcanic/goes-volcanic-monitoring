# Ficha de Transparencia Algorítmica — Monitoreo Volcánico GOES-19 (dashboard + retrieval de altura de pluma)

**Identificador interno:** SDA-GOES-01   **Versión:** v2.0 — 2026-08-30
*(Resolución CPLT N°372; ver `GUIA_MAESTRA_TRANSPARENCIA_ALGORITMICA.md` del workspace)*

> **Qué cambió respecto de la v1.0 (2026-07-01):** ver §"Historial de versiones" al final.
> En resumen: se sacaron de la lista de componentes activos dos módulos que **no están
> cableados a producción**, se incorporaron dos clasificadores que sí corren y no
> figuraban (indicador SO₂ y filtro de hot spots FDCF), se documentó el **disparo
> automático** del retrieval de altura y se explicitaron los límites conocidos,
> incluido el **no-uso aeronáutico**.

## Subítem 1 — Identificación (CPLT 6.5)

- **Canal de consulta/reclamación:** sí — issues del repositorio público
  (github.com/MendozaVolcanic/goes-volcanic-monitoring) y canales institucionales
  SERNAGEOMIN.
- **¿Permite oposición a decisión automatizada?:** No aplica — el sistema NO toma
  decisiones automatizadas sobre personas; produce indicadores geofísicos que un
  geólogo interpreta. La decisión de alerta volcánica es siempre humana.
- **Titularidad:** desarrollo abierto (licencia **Apache-2.0**), uso operacional
  por SERNAGEOMIN/OVDAS (organismo del Estado de Chile).
- **Proveedor:** No aplica (desarrollo propio, código abierto).
- **Más información:** README.md del repositorio + `docs/GUIA_REVISION_DASHBOARD.md`.

## Subítem 2 — Servicios/procedimientos (CPLT 6.6)

- **Servicio/trámite donde se usa:** apoyo a la vigilancia volcánica de la Red
  Nacional de Vigilancia Volcánica (RNVV) — insumo para la evaluación del nivel
  de alerta técnica volcánica.
- **Unidad que lo usa:** OVDAS (Observatorio Volcanológico de los Andes del Sur),
  SERNAGEOMIN.
- **Acto que lo estableció:** sin acto administrativo específico (herramienta de
  apoyo técnico interno; el procedimiento de alerta se rige por la normativa
  general de SERNAGEOMIN).

## Subítem 3 — Especificaciones (CPLT 6.7)

- **Objetivo:** detectar ceniza volcánica y SO₂ en imágenes del satélite GOES-19
  y estimar la altura del tope de la pluma en tiempo casi-real (~13 min), como
  complemento INDICATIVO del producto de referencia (VOLCAT, NOAA/CIMSS), para
  apoyar — nunca reemplazar — la decisión humana de alerta.
- **Funcionamiento/lógica (lenguaje claro):** la ceniza silicatada absorbe la
  radiación infrarroja de forma distinta en 11 y 12 µm ("absorción inversa");
  el sistema detecta esa firma, estima la temperatura del tope de la pluma y la
  convierte a altura buscándola en un perfil vertical de temperatura del modelo
  meteorológico GFS. Métodos encadenados: detección BTD/tri-espectral (Prata
  1989), cota por BT-matching, corrección de emisividad de 2 canales (Wen &
  Rose 1994), composición por β-ratios (Pavolonis 2010), árbitro CO₂ 13.3 µm
  con gate de altura, y cruce con el producto ACHA de NOAA.
- **¿Categoriza/perfila individuos?:** **No** (sistema geofísico).
- **Método/modelo:** reglas determinísticas + umbrales físicos publicados +
  inversión radiativa simple (búsqueda en grilla). **Sin machine learning, sin
  caja negra** — todo el código es abierto y auditable.
- **Efecto de las variables principales:** BTD(11−12 µm) < −1 K dispara la
  detección de ceniza; BT(11 µm) y el perfil GFS T(z) fijan la altura; β
  (microfísica, barrido 0.55–0.95) fija el ancho de la banda de incertidumbre;
  BT(8.4−11.2) < −3 K indica SO₂ (sin altura válida).
- **Categorías de datos:** imágenes satelitales GOES-19 (NOAA, dominio público),
  perfiles meteorológicos GFS (Open-Meteo), productos L2 de NOAA (ACHA, FDCF) y
  CIMSS (VOLCAT). **¿Datos personales?: No. ¿Sensibles?: No.**
- **Datos de entrenamiento/validación/prueba:** No aplica (sin ML). Validación
  física: >200 tests automatizados en CI (round-trips con coeficientes reales del
  sensor) + casos reales documentados (Láscar 27-jun-2026, Popocatépetl
  26-jun-2026, Chillán 27-jun-2026) en `docs/paper/REGISTRO_PAPER.md` §3.
- **Política de privacidad:** No aplica (sin datos personales).
- **Si es caja negra (5.5):** No aplica — código 100% abierto (Apache-2.0).

---

## A. Componentes que clasifican y **están cableados a producción**

Esta lista es la que debe leerse como "lo que el sistema hace hoy". Cada entrada
declara qué decide, con qué umbral, con qué fuente y cuál es su límite conocido.

### A.1 Detección de ceniza (BTD split-window + test tri-espectral)
- **Archivo:** `src/process/ash_detection.py` (umbrales) y
  `src/process/ash_rgb.py` (Ash RGB / Ash-SO₂ RGB).
- **Qué decide:** si un píxel es candidato a ceniza silicatada.
- **Umbral:** BTD(11,2 − 12,3 µm) < **−1,0 K** (Prata 1989); el test tri-espectral
  exige además (BT8,4 − BT11,2) + (BT12,3 − BT11,2) < 0.
- **Fuente:** bandas L1b GOES-19 C11/C13/C14/C15 (AWS S3 `noaa-goes19`).
- **Límite conocido:** cirros delgados y nieve producen firmas parecidas; el
  proyecto NO deriva ninguna métrica automática de "% de ceniza" a partir del
  color del Ash RGB (ver §B.5).

### A.2 Indicador de SO₂ — BTD(8,4 − 11,2 µm)
- **Archivo:** `src/process/ash_rgb.py:105` (`generate_so2_indicator`), invocado
  desde `src/process/pipeline.py:115`; se muestra en
  `dashboard/views/ash_viewer.py` (panel "SO₂" + conteo de píxeles).
- **Qué decide:** clasifica cada píxel como "sugiere presencia de SO₂" o no.
- **Umbral:** BT(8,4 µm) − BT(11,2 µm) < **−3 K** sugiere SO₂ (el SO₂ absorbe
  fuertemente en 8,4 µm, lo que enfría esa banda respecto de la ventana de
  11,2 µm). El viewer cuenta los píxeles bajo ese umbral y muestra el campo
  continuo con signo invertido (más intenso = más SO₂).
- **Fuente:** bandas L1b GOES-19 C11 (8,4 µm) y C14 (11,2 µm).
- **Límites conocidos:**
  - Es un **indicador cualitativo, no una columna de SO₂** (no hay unidades de
    Dobson ni retrieval radiativo): sirve para ver *dónde* y *si*, no *cuánto*.
  - La banda de 8,4 µm también responde a vapor de agua y a la emisividad de la
    superficie; sobre desierto y sobre nubes altas hay falsos positivos.
  - **No tiene altura asociada**: una pluma de gas sin ceniza es prácticamente
    transparente en 11 µm y ningún retrieval de altura del sistema le aplica
    (ver §B.4).
  - El panel de SO₂ que se ve en la vista de volcán es un producto **externo**
    (RAMMB/SLIDER `jma_so2`), distinto de este indicador propio; los dos
    coexisten y no deben confundirse.

### A.3 Filtro de hot spots FDCF (NOAA L2) + filtro de proximidad a volcán
- **Archivos:** `src/fetch/goes_fdcf.py:66` (`HOTSPOT_MASK_VALUES`),
  `:72` (`HIGH_CONF_MASK`), `extract_hotspots`; y
  `dashboard/map_helpers.py:98` (`filter_hotspots_near_volcanoes`).
- **Qué decide:** qué píxeles calientes del producto FDCF de NOAA se muestran
  como "hot spot volcánico" en el dashboard — y, desde ago-2026, cuáles
  **disparan automáticamente** el retrieval de altura (ver §A.4).
- **Umbrales / reglas:**
  - Se aceptan las categorías de la variable `Mask` del FDCF
    `HOTSPOT_MASK_VALUES = {10, 11, 12, 13, 14, 15}` (10/11 = fuego de alta
    confianza; 12/13 = saturado; 14/15 = baja confianza). Las categorías 30+
    son nube / sin dato / fuera del disco.
  - Existe un modo restringido `high_conf_only` con
    `HIGH_CONF_MASK = {10, 11, 30, 31}` (30/31 = *processed temporally
    filtered*, que ya pasaron un test de persistencia en scans previos). **Está
    apagado por defecto** en todos los llamadores del dashboard, o sea que la
    vista operacional muestra también las detecciones de baja confianza,
    etiquetadas como tales (`confidence` = high/saturated/low).
  - Filtro geográfico: se descarta todo foco a más de **30 km**
    (`HOTSPOT_NEAR_KM`) de cualquier volcán del catálogo RNVV, para no
    contaminar la vista con incendios forestales e industria.
- **Fuente:** producto pre-procesado NOAA `ABI-L2-FDCF` (Full Disk, cada 10 min,
  latencia ~6–8 min), leído desde AWS S3 sin credenciales.
- **Límites conocidos:**
  - El algoritmo FDCF de NOAA está **optimizado para incendios forestales**.
    Detecta bien la lava expuesta (erupciones efusivas tipo Villarrica) y **no
    detecta erupciones explosivas con ceniza fría**: la ausencia de hot spot no
    es ausencia de erupción.
  - El filtro de 30 km es un radio fijo: un incendio forestal en el flanco de un
    volcán pasa el filtro y se muestra como hot spot. La discriminación
    incendio/volcán la hace la persona, no el sistema.
  - Con el modo de alta confianza apagado, entran detecciones `low` (Mask 14/15):
    ganamos sensibilidad a costa de falsos positivos.
  - Cruce con VRP (MODIS/VIIRS) sigue siendo necesario para validar.

### A.4 Retrieval propio de altura de tope + su disparador
- **Archivos:** `src/process/scene.py` (adquisición y guards),
  `src/process/wen_rose_height.py`, `src/process/acha_plume_height.py`,
  `src/process/beta_ratios.py`; vistas
  `dashboard/views/modo_guardia_volcan.py` (decide CUÁNDO se ejecuta) y
  `dashboard/views/volcat_viewer.py` (presenta el número y sus advertencias).
- **Qué decide:** la altura del tope de la pluma de ceniza (km s.n.m.), su banda
  de incertidumbre y su nivel de confianza; y si la detección es silicato,
  hielo o agua (β-ratios).
- **Cuándo se ejecuta (cambio de ago-2026):** NO corre en cada scan. Una escena
  cuesta ~78 MB y ~90 s (bandas L1b C11/C14/C15, medido contra S3 con caché
  frío), así que en la vista de volcán se dispara sólo en dos casos:
  (a) **automáticamente** cuando el producto FDCF de NOAA reporta un *hot spot*
  dentro del encuadre (`modo_guardia_volcan.py`, ~línea 854: `auto = bool(hotspots)`),
  y (b) **a pedido del operador**, con un botón siempre disponible que declara
  el costo antes de gastarlo. Cuando el disparo es automático, la interfaz lo
  dice explícitamente y recuerda que el hot spot marca anomalía térmica en el
  cráter, **no** pluma. La tira de altura está **apagada por defecto**
  (`mostrar_altura=False`) y nunca se enciende en la pared del Modo Sala.
- **Por qué NO hay un disparador por color:** se evaluó y **descartó** usar la
  fracción de rojo del Ash RGB (`_ash_red_fraction_v2`): medida sobre los 8
  volcanes prioritarios sin actividad da 9,9–95,5 % (mediana 76 %), o sea que
  con cualquier umbral absoluto dispara siempre o nunca.
- **Advertencia mostrada en pantalla junto al resultado:** los retrievals miden
  **sólo ceniza IR-opaca**. Si todos los topes quedan bajo la cota del volcán, la
  interfaz declara explícitamente que eso significa *"no se encontró ceniza
  IR-opaca"* y no *"la pluma es baja"* — es el comportamiento típico ante una
  pluma de gas/SO₂ (validado contra Chillán, 27-jun-2026).

### A.5 Dónde viven los guards de adquisición
Los retrievals de altura comparten `src/process/scene.py` (`acquire_ash_scene`).
Ahí —y sólo ahí— se decide *no reportar*: banda ausente, bbox fuera del disco,
bandas de scans distintos (misregistro) y falta de perfil GFS. Hasta la ola 2 del
audit ago-2026 ese bloque estaba duplicado en tres módulos, con el riesgo de que
un fix a un guard se aplicara sólo a uno. Cualquier cambio a un criterio de
degradación va en `scene.py` y en esta ficha, mismo commit.

---

## B. Límites, sesgos y usos excluidos

Un SDA debe declarar su frontera. Estos son los límites verificados del sistema.

### B.1 Resolución espacial: 2 km es el techo físico
El infrarrojo del ABI (GOES-19) tiene **2 km/píxel en el nadir**, y peor en Chile
por el ángulo de vista oblicuo. Todos los productos de ceniza, SO₂ y altura
heredan esa resolución. Los sectores VOLCAT rotulados **"250 m" o "500 m" son la
grilla del ráster de salida, NO la resolución nativa del dato**: el remuestreo no
crea información. Una resolución realmente sub-kilométrica sólo la dan sensores
polares (VIIRS 375 m), con ~2 pasadas diarias en vez de una cada 10 minutos.

### B.2 Sesgo IR sistemático de −0,4 a −0,8 km
Los retrievals IR de altura **subestiman** el tope entre 0,4 y 0,8 km
(documentado en la auditoría jul-2026 y en la guía de turno). El número que se
muestra es una cota inferior en promedio, no un valor centrado.
*Brecha conocida (audit ago-2026 §3.5): este sesgo está documentado en la guía,
pero todavía no se muestra en la pantalla donde aparece el número.*

### B.3 Banda fiable de altura: 3–12 km
Fuera de ese rango la confianza se degrada automáticamente. Bajo ~3 km la pluma
se confunde con la superficie y con nubes bajas; sobre ~12 km el perfil GFS y el
guard de tropopausa dominan el resultado. Toda altura propia se etiqueta
**INDICATIVO**, con banda de incertidumbre y con un nivel de confianza que
**nunca es "alta"**; el producto cuantitativo de referencia sigue siendo VOLCAT.

### B.4 No hay altura válida sobre plumas de SO₂ / gas sin ceniza
Una pluma de gas es prácticamente **transparente en 11 µm**: el satélite ve a
través de ella y mide la superficie. Los tres métodos devuelven entonces topes
bajo la cota del volcán. Eso significa "no se encontró ceniza IR-opaca", no
"la pluma es baja". Validado contra Chillán, 27-jun-2026.

### B.5 La ceniza ópticamente gruesa puede etiquetarse "hielo" (limitación abierta)
Hallazgo confirmado en la auditoría del 30-ago-2026 sobre
`src/process/beta_ratios.py:280`. Cuando la pluma es **ópticamente gruesa** —cerca
del cráter, temprano en la erupción: el caso peligroso— la emisividad satura y
β → 1, que es la firma del hielo. Reproducido con los coeficientes Planck reales:
con `t11 = 0,001`, β(12,11) = 0,896 → etiqueta `hielo`, `is_ash = False`. Y esa
etiqueta es la que enciende en el panel el aviso de *posible falso positivo de
ceniza*. El efecto operativo es una **asimetría de consecuencias invertida**: el
sistema pide desconfiar justo cuando la detección es más real. La auditoría
verificó además que el disparador dominante no es β(12,11) sino **β(8,5;11)**:
como el test tri-espectral exige que 8,4 µm esté más frío que 11,2 µm, *todo*
píxel que entra por la máscara tiene β₈₅ > 1, así que el aviso de "no silicato"
puede saltar incluso con plumas semitransparentes bien modeladas. Los β-ratios de
Pavolonis discriminan composición en el régimen **semitransparente**; usarlos
fuera de él sin un guard de opacidad les pide algo que no pueden dar.
**Estado: limitación conocida, sin corregir a la fecha de esta versión.** Mientras
tanto, el aviso de posible falso positivo debe leerse como una señal débil y
nunca como razón para descartar una detección.

### B.6 Otras cosas que el retrieval sabe y todavía no muestra (audit ago-2026 §3.4)
- **Sin piso de terreno** en `altitudes_from_bt`: Láscar puede reportar topes
  varios km bajo su propio cráter. `Volcano.elevation` existe en el catálogo y
  no se usa.
- El **desfase temporal del perfil GFS** (`time_gap_min`) se mide y se descarta
  antes de llegar a la pantalla: el operador no sabe si el perfil es de hace 20
  minutos o de hace 5 horas.
- `solar_elevation` no aplica ecuación del tiempo (error medido de hasta 4,0°),
  y gobierna el switch día/noche con umbral de 5°.

### B.7 Uso EXCLUIDO: alerta aeronáutica / flight levels
**Este sistema no sirve para decidir niveles de vuelo ni para emitir avisos
aeronáuticos.** Su altura es INDICATIVA, con banda fiable 3–12 km, sesgo negativo
conocido y sin corrección de parallax cableada (§C.1). La autoridad para avisos de
ceniza a la aviación es el **VAAC Buenos Aires**; el producto cuantitativo de
referencia es **VOLCAT (NOAA/CIMSS)**. Cualquier documentación interna que sugiera
lo contrario debe corregirse.

### B.8 Riesgos latentes registrados (verificados como seguros HOY)
Dos hallazgos que la verificación adversarial del 30-ago-2026 **refutó como bug**
pero que dependen de una condición del entorno, y por eso quedan registrados:

1. **Guard de tropopausa** — `src/process/wen_rose_height.py` (comentario en
   `_revert_unreliable`, ~línea 363/415): si `_tropopause` devolviera `None`, el
   umbral pasa a `+inf` y el guard de *runaway* se apaga entero. Se refutó porque
   el **único proveedor de perfil cableado es Open-Meteo** (`scene.acquire_ash_scene`)
   y su API no devuelve nulls: verificado sobre Láscar, 72 h × 19 niveles, 0 nulls
   en T y Z, incluidos los nueve niveles 400–70 hPa necesarios. El modo de falla
   realista (perfil caído entero) ya lo corta el guard "sin perfil GFS".
   **Condición de seguridad: un solo proveedor de perfil. El día que se cablee
   LVTP, GRIB o cualquier otro, revisar este guard ANTES de conectarlo.**
2. **`well_constrained` no mide la calidad del ajuste** — mide el ancho del mínimo
   de residuo, no su valor. Se refutó porque `_revert_unreliable` neutraliza los
   casos malos (la altura clampa en la tropopausa, `reliable` pasa a `False` y el
   resultado vuelve a la cota BT-matching), y porque `well_constrained` **no sale
   del módulo**. Un barrido β_true 0,45–1,00 × t11 0,15–0,9 no produjo ningún tope
   alto espurio marcado como confiable. **Condición de seguridad: `well_constrained`
   se consume siempre a través de `_revert_unreliable`. Si algún consumidor futuro
   lo lee directo, el guard deja de existir.**

---

## C. Implementado pero **NO cableado a producción**

Código presente en el repositorio, con tests y cabecera FICHA SDA, que **ningún
camino del dashboard ejecuta**. Se lista para que la ficha no atribuya al sistema
capacidades que no tiene, y para que la revisión de un cambio futuro sepa que
conectarlos exige actualizar esta ficha.

| Módulo | Qué haría | Quién lo usa hoy |
|---|---|---|
| `src/process/parallax.py` | Corregir la georreferencia de la pluma por su altura (desplazamiento geoestacionario, Vicente et al. 2002) | sólo sus tests. `parallax_correct_field` no se llama desde ninguna vista. **Consecuencia: la pluma se dibuja sin corrección de parallax; a 10 km de altura y ángulo oblicuo el error de posición es de varios km.** |
| `src/process/wind_shear_height.py` | Estimar altura por deriva/cizalle del viento (árbitro independiente del IR) | `scripts/validate_fase3c.py` (validación offline) |
| `src/process/bt_matching_height.py` | Módulo autónomo de cota por BT-matching | scripts de validación y tests. *(El **método** BT-matching sí está en producción, calculado dentro de `wen_rose_height.py` como `top_bt_matching_km`; lo no cableado es el módulo separado.)* |
| `src/fetch/goes_lvtp.py` | Perfil T(z) del propio GOES-19 (LVTPF) como cross-check del GFS | `scripts/compare_lvtp_vs_gfs.py`. Ver §B.8.1: cablearlo obliga a revisar el guard de tropopausa. |
| `src/fetch/viirs_firms.py`, `src/fetch/viirs_gibs.py` | Hot spots térmicos VIIRS 375 m e imagen VIIRS para volcanes australes | `scripts/viirs_patagonia_snapshots.py` (uso manual) |

---

## Historial de versiones

### v2.0 — 2026-08-30 (auditoría adversarial del 30-ago-2026, §2.5)
**Sacado / corregido**
- `wind_shear_height.py` y `parallax.py` dejaron de figurar como componentes
  activos: verificado por grep que ningún módulo de `dashboard/` ni de `src/`
  los importa. Se movieron a §C con lo que su ausencia implica (en particular:
  **la georreferencia de la pluma NO está corregida por parallax**).
- La lista de "módulos con cabecera FICHA SDA" ya no se presenta como lista de
  componentes en producción; §A y §C separan lo cableado de lo que no lo está.

**Agregado**
- §A.2 — indicador de SO₂ propio (`ash_rgb.py:105`, umbral −3 K), que clasificaba
  en producción sin figurar en la ficha, con sus límites (cualitativo, falsos
  positivos por vapor de agua y emisividad de superficie, sin altura asociada) y
  la aclaración de que el panel SO₂ de la vista de volcán es RAMMB, no éste.
- §A.3 — filtro de hot spots FDCF (`goes_fdcf.py:66/72`) y filtro de proximidad de
  30 km (`map_helpers.py:98`), con las categorías `Mask` aceptadas, el modo
  `high_conf_only` apagado por defecto, y el límite mayor: el algoritmo de NOAA
  está optimizado para incendios y **no detecta erupciones explosivas con ceniza
  fría**.
- §A.4 — **disparo automático** del retrieval de altura por hot spot FDCF, además
  del botón manual (cambio de ago-2026 no reflejado en la v1.0).
- §B completo — límites y sesgos explícitos: resolución IR 2 km y qué significan
  de verdad los sectores VOLCAT "250 m/500 m"; sesgo IR −0,4 a −0,8 km; banda
  fiable 3–12 km; sin altura sobre plumas de gas; **ceniza opaca clasificada como
  hielo** (`beta_ratios.py:280`, confirmado hoy, sin corregir); brechas del §3.4
  del audit; y el **uso excluido: alerta aeronáutica / flight levels**.
- §B.8 — dos riesgos latentes que la verificación adversarial refutó (guard de
  tropopausa de `wen_rose_height.py` y dependencia de `well_constrained` respecto
  de `_revert_unreliable`), con la condición de entorno que hoy los hace seguros:
  Open-Meteo como único proveedor de perfil.

**Pendiente de verificar / fuera del alcance de esta edición**
- No se auditó si la app desplegada declara al usuario que es un SDA ni si
  enlaza esta ficha (hallazgo abierto del audit §2.5).

### v1.0 — 2026-07-01
Primera ficha publicable del SDA-GOES-01.

---

**Mantenimiento de esta ficha:** revisar cuando cambie la lógica, el método, las
variables o las fuentes de datos (regla: **mismo commit** que el cambio). Módulos
con cabecera "FICHA SDA" (Nivel 1): `src/process/ash_detection.py`, `scene.py`,
`bt_matching_height.py`, `wen_rose_height.py`, `beta_ratios.py`,
`wind_shear_height.py`, `acha_plume_height.py`, `parallax.py` y
`dashboard/views/modo_guardia_volcan.py`. **Ojo:** llevar cabecera FICHA no
implica estar en producción — el mapa de qué corre y qué no es §A vs §C.
`src/process/ash_rgb.py` (indicador SO₂) y `src/fetch/goes_fdcf.py` (filtro de
hot spots) clasifican y **todavía no llevan cabecera FICHA**; agregarla es tarea
pendiente en `src/`, fuera del alcance de esta edición de la ficha.
