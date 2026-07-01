# Guía de revisión del dashboard GOES — qué mirar y cómo interpretarlo

> Para el geólogo de guardia (OVDAS/SERNAGEOMIN). Objetivo: saber **qué revisar**
> en cada vista, **cómo interpretarlo** y **qué NO sobre-leer**. Última actualización:
> 2026-07-01. App: https://mendozavolcanic-goes-volcanic-monitoring.hf.space

## Regla de oro (leer siempre)

- **VOLCAT/SSEC es el número cuantitativo de referencia.** Todo lo etiquetado
  **INDICATIVO** (altura propia, β-ratios) es cross-check, NO reemplaza a VOLCAT.
- **Resolución máxima del sensor:** ceniza/altura = **2 km** (IR de GOES-19, es el
  máximo físico); imagen visible/GeoColor = **0.5 km**. No hay ceniza IR más fina.
- **Ceniza ≠ gas.** Una pluma de SO₂/gas es transparente en 11 µm → NO da altura
  válida. Si el dashboard dice "pluma de SO₂/gas sin ceniza", es correcto, no un bug.

---

## Vista por vista — qué revisar

### 1. 🔴 En Vivo (auto-refresh 60 s)
Sub-tabs Nacional / Zona / Volcán.
- **Ash RGB**: buscar tonos **rojo/rosa** (receta CIRA) = ceniza probable. OJO: cirros
  y nieve dan falsos positivos 30-60% en invierno chileno — cruzar con BTD/SO₂.
- **SO₂**: realce del indicador BT(8.4−11.2). Muy negativo (< −3 K) = SO₂ fuerte.
- **GeoColor 0.5 km**: contexto visible diurno; de noche pasa a IR pseudo-color.
- Toggles: viento GFS (vectores) y hot spots FDCF (FRP).
- **Qué revisar:** ¿hay señal de ceniza (rojo Ash RGB + BTD negativo) o solo SO₂?
  ¿coincide un hot spot con actividad reportada?

### 2. Mapa General
Overview de los 43 volcanes. Revisar dónde hay señal activa para ir al detalle.

### 3. Ash RGB Viewer / 4. Detalle Volcán
Versión propia desde L1b + 3 productos + altura VOLCAT por volcán.

### 5. VOLCAT (SSEC) — el corazón cuantitativo
- **Altura de pluma** (4 productos SSEC con cheat-sheet): Ash_Height (km AMSL),
  Loading (g/m²), Probability (%), Reff (µm). **Filtrar por Probability > 60%.**
- **VAA**: Volcanic Ash Advisories activos (overlay).
- **⬇ Altura del tope · propia (INDICATIVO)** — ver sección dedicada abajo. Está
  en **modo Volcán, debajo del VOLCAT primario, tras el botón "Calcular tope propio"**.

### 6. Animación (RAMMB) · 7. Series de tiempo · 8. Backfill histórico
- Series: tendencia de % píxeles con firma de ceniza/SO₂ por volcán (1-24 h).
- Backfill: revisión de eventos pasados con slider temporal (usa L1b crudo fuera
  del archive RAMMB).

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
