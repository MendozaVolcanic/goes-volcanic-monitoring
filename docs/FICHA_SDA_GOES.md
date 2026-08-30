# Ficha de Transparencia Algorítmica — Monitoreo Volcánico GOES-19 (dashboard + retrieval de altura de pluma)

**Identificador interno:** SDA-GOES-01   **Versión:** v1.0 — 2026-07-01
*(Resolución CPLT N°372; ver `GUIA_MAESTRA_TRANSPARENCIA_ALGORITMICA.md` del workspace)*

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
- **Evaluaciones de impacto / sesgos y mitigaciones:** auditoría adversarial
  jul-2026 (`AUDIT_REPORT_2026-07.md`): sesgo IR sistemático de −0.4 a −0.8 km
  (documentado en UI), banda de altura fiable 3–12 km (fuera de ella la
  confianza se degrada automáticamente), falsos positivos de cirros/nieve
  (mitigados con test tri-espectral + β-ratios). Toda altura propia se etiqueta
  **INDICATIVO** con banda de incertidumbre y nivel de confianza que nunca es
  "alta"; el producto cuantitativo de referencia sigue siendo VOLCAT.
- **Cuándo se ejecuta el cálculo de altura (ago-2026):** NO corre en cada scan.
  Una escena cuesta ~78 MB y ~90 s (bandas L1b C11/C14/C15 medidas contra S3 con
  caché frío), así que en la vista de volcán se dispara sólo en dos casos:
  (a) **automáticamente** cuando el producto FDCF de NOAA reporta un *hot spot*
  dentro del encuadre, y (b) **a pedido del operador**, con un botón siempre
  disponible que declara el costo antes de gastarlo. El hot spot marca anomalía
  térmica en el cráter, **no** pluma: una erupción freática puede dar columna de
  ceniza sin ninguno, y ese caso lo dispara la persona. Se evaluó y **descartó**
  un disparador por fracción de color del Ash RGB: medido sobre los 8 volcanes
  prioritarios sin actividad da 9,9–95,5 % (mediana 76 %), o sea que con
  cualquier umbral absoluto dispara siempre o nunca.
- **Advertencia mostrada en pantalla junto al resultado:** los tres retrievals
  miden **sólo ceniza IR-opaca**. Si todos los topes quedan bajo la cota del
  volcán, la interfaz declara explícitamente que eso significa *"no se encontró
  ceniza IR-opaca"* y no *"la pluma es baja"* — es el comportamiento típico ante
  una pluma de gas/SO₂ (validado contra Chillán, 27-jun-2026).
- **Política de privacidad:** No aplica (sin datos personales).
- **Si es caja negra (5.5):** No aplica — código 100% abierto (Apache-2.0).

---

**Mantenimiento de esta ficha:** revisar cuando cambie la lógica/método (regla:
mismo commit que el cambio). Módulos con cabecera "FICHA SDA" (Nivel 1):
`src/process/ash_detection.py`, `scene.py`, `bt_matching_height.py`,
`wen_rose_height.py`, `beta_ratios.py`, `wind_shear_height.py`,
`acha_plume_height.py`, `parallax.py` (corrige la georef de la pluma por su
altura) y `dashboard/views/modo_guardia_volcan.py` (la vista que decide
CUÁNDO se ejecuta el retrieval y qué advertencias acompañan al número).

**Dónde viven los guards de adquisición (ago-2026):** los tres retrievals de
altura comparten `src/process/scene.py` (`acquire_ash_scene`). Ahí —y sólo ahí—
se decide *no reportar*: banda ausente, bbox fuera del disco, bandas de scans
distintos (misregistro) y falta de perfil GFS. Hasta la ola 2 del audit ago-2026
ese bloque estaba duplicado en los tres módulos, con el riesgo de que un fix a
un guard se aplicara sólo a uno. Cualquier cambio a un criterio de degradación
va en `scene.py` y en esta ficha, mismo commit.
