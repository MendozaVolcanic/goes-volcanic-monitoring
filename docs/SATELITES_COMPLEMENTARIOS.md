# Satélites complementarios para monitoreo volcánico en Chile

> Evaluación de sensores más allá de GOES-19 (el workhorse de este proyecto) para
> la vigilancia volcánica de SERNAGEOMIN/OVDAS. Investigación jul-2026 (incluye dos
> deep-dives con fuentes: Lemu Nge y FASat-Delta). Regla: cada afirmación de spec
> lleva fuente; lo no verificado se marca.

## 1. Panorama por clase

| Clase | Satélite | Aporte a volcanes | Estado en el ecosistema |
|---|---|---|---|
| **Geo (NRT)** | GOES-19 East | 2 km, 10 min — Ash RGB, BTD, SO₂, FRP, altura propia | ✅ este proyecto |
| Geo | GOES-18 West | Muy oblicuo sobre Chile, pero habilita **altura por estéreo** (parallax entre 2 vistas, sin NWP) | futuro |
| Geo | Himawari-9 / Meteosat-MTG | **No sirven** para Chile (del otro lado del globo / limbo extremo) | — |
| **Polar (alta-res)** | **VIIRS** SNPP/NOAA-20/21 | 375 m térmico + imagen, ~2 ventanas/día | ✅ **ingerido** (GIBS + FIRMS) |
| Polar | MODIS Terra/Aqua | 250 m–1 km, herencia MIROVA/VRP | VRP Chile |
| Polar | Sentinel-2 MSI | 10–20 m óptico/**SWIR** (lava/hotspots excelente) | VegStress-v1 |
| Polar | Sentinel-5P TROPOMI | **SO₂**/aerosol ~5.5 km (UV) | VolcPlume-v1 |
| Polar | Landsat 8/9 | 30 m óptico, 100 m **térmico** | Landsat-v1 |
| Polar | Sentinel-1 SAR | InSAR **deformación** (precursor) | LiCSAR-v1 |
| Rayos | GOES GLM | Rayos volcánicos (indicador de erupción) | Lightning-v1 |
| Hiperesp. | EMIT / PRISMA / EnMAP | SO₂, mineralogía, composición (tasking, VNIR-SWIR-TIR según cual) | futuro |
| Futuro | NISAR (2024+) | InSAR banda L gratis, deformación | futuro |

**Huecos reales del ecosistema:** VIIRS (ya cubierto, ver §2) y el **estéreo GOES-19+18** (altura sin modelo, futuro). El resto ya está en repos hermanos.

## 2. VIIRS — INGERIDO (vía liviana, jul-2026)

Decisión: **NO** construimos un pipeline de retrieval cuantitativo sobre gránulos
polares crudos (geometría polar = 2º pipeline, y el retrieval ya existe tuneado en
SSEC/VOLCAT). **SÍ** ingerimos imagen/térmico por servicios que ya reproyectan:

- **Imagen** — `src/fetch/viirs_gibs.py`: NASA GIBS WMS, un GetMap por bbox+fecha
  → PNG georreferenciado (True Color, anomalías térmicas 375 m, Day-Night Band).
- **Térmico** — `src/fetch/viirs_firms.py`: NASA FIRMS, hot spots 375 m como puntos
  (FRP, T_brillo, confianza) — el análogo polar de nuestros FDCF de GOES. Requiere
  un MAP_KEY gratis (env `FIRMS_MAP_KEY`).
- Uso: **complemento para volcanes australes sin monitoreo GOES dedicado**
  (patagónicos: Hudson, Macá, Cay, Mentolat, Melimoyu…), separado del dashboard ABI.
- Detalle físico/cadencia en `docs/paper/REGISTRO_PAPER.md §9`.

## 3. Lemu Nge (2024) — nanosat hiperespectral chileno

**Qué es.** Primer satélite del mundo dedicado a biodiversidad; de la startup chilena
**Lemu** (privada/comercial). Bus 6U de NanoAvionics (Lituania), cámara hiperespectral
de Simera Sense (Sudáfrica), propulsión Enpulsion (Austria). Lanzado **16-ago-2024**
en Falcon 9 Transporter-11 desde Vandenberg. Órbita SSO ~500 km.

**Sensor.** Hiperespectral **32 bandas VNIR (~420/450–900 nm)**, GSD **~4.75 m**.
**Sin SWIR, sin térmico, sin UV.** Modelo comercial B2B (plataforma "Atlas"), **sin
API abierta**; revisita 3–7 días, tasking bajo demanda (demostrado nov-2025, cliente
Codelco). Activo y operacional (2025-2026), vida útil 3–5 años.

**Utilidad volcanológica — BAJA para NRT.** Al ser VNIR puro **no mide** temperatura
de superficie/lava (falta MIR/TIR), **ni SO₂** (falta UV o TIR ~7–8.7 µm), **ni
ceniza por BTD** (falta 11/12 µm) → no aporta señal a ninguno de los productos del
proyecto. Cadencia (días) + acceso comercial → estudios puntuales, no vigilancia.
**Nichos post-evento (no de alerta):** daño a vegetación por gases/ceniza (índices de
estrés fotosintético de alta resolución), mapeo de depósitos/uso de suelo. Alteración
hidrotermal: limitada (las arcillas/alunita diagnósticas están en SWIR ~2.0–2.3 µm que
NO cubre; en VNIR solo óxidos de hierro como *indicio*). Acceso = convenio comercial
con Lemu. **Veredicto: herramienta de ecología/estudio, no de monitoreo operacional.**

## 4. FASat-Delta (2023) — EO de la FACh · **CANCELADO**

**Corrección importante** (desmiente el supuesto común, incluido el nuestro previo):
FASat-Delta es la denominación chilena del satélite comercial **Runner-1** de la
israelí **ImageSat International (ISI)**, construido por **Tyvak/Terran Orbital** —
**NO** por SSTL ni Airbus (esos fueron los FASat previos: Bravo/SSTL 1998, Charlie/SSOT
por Astrium 2011). Chile **no es dueño**, era **cliente prioritario de un servicio**.

**Specs** (Terran Orbital / Gunter's): microsat **86 kg**, SSO **~500 km**, telescopio
35 cm, resolución **~71 cm** (submétrica), bandas **400–670 nm (visible/color puro,
sin TIR ni SWIR)**, swath 5.6 km. Lanzado **12-jun-2023**, Falcon 9 desde Vandenberg.

**Estado — DECISIVO:** nunca alcanzó operatividad (300 días sin operar a may-2024, por
calibración/validación del modo nocturno + antena de segmento terreno sin instalar).
**La FACh canceló el contrato el 24-nov-2024** por incumplimiento de ISI (sin
comprometer fondos del Estado — pago por hitos no cumplidos). A 2025-2026 está en
órbita pero **inutilizable por Chile**.

**Utilidad volcanológica — NULA**, por dos motivos independientes: (a) está cancelado,
no hay dato que consumir; (b) aun operativo, es **solo visible** → no detecta hot
spots/térmico (para eso ya están GOES/VIIRS/MODIS/Landsat), y su revisita+tasking es
incompatible con NRT. Solo habría servido **post-evento** (depósitos/morfología a 71
cm, como Planet/Sentinel-2). Para respuesta a desastres, Chile ya usa la **Carta
Internacional Espacio y Grandes Desastres** (~270 satélites) — vía más realista.
**Veredicto: no incorporar; monitorear el reemplazo prometido del SNSat.**

## 5. Conclusión operacional

Las fuentes que ya usás (GOES térmico/NRT, VIIRS/MODIS polar, Sentinel-5P para SO₂,
Sentinel-2/Landsat/Planet para post-evento, Sentinel-1 InSAR) son **estrictamente
superiores** a los dos satélites nacionales para vigilancia volcánica. Lemu Nge tiene
un nicho de estudio ambiental post-erupción (acceso comercial); FASat-Delta está
cancelado. El próximo salto de valor propio es **VIIRS** (hecho) y a futuro el
**estéreo GOES-19+18**.

---

### Fuentes

**Lemu Nge:** [ficha oficial](https://www.le.mu/lemu-nge/) · [primer año](https://www.le.mu/blog/the-first-year-of-lemu-nge/) · [tasking Codelco](https://www.le.mu/blog/lemu-nge-completes-first-tasking-first-monitoring-for-industrial-customer/) · [NanoAvionics/Transporter-11](https://nanoavionics.com/news/spacex-transporter-11-to-launch-worlds-first-satellite-exclusively-for-observing-biodiversity-built-by-nanoavionics/)

**FASat-Delta / Runner-1:** [FACh lanzamiento](https://fach.mil.cl/satelite-fasat-delta-es-puesto-en-orbita-luego-de-separarse-exitosamente) · [Gunter's Space Page — Runner-1](https://space.skyrocket.de/doc_sdat/runner-1.htm) · [Terran Orbital](https://terranorbital.com/missions/runner-1/) · [Infodefensa — cancelación nov-2024](https://www.infodefensa.com/texto-diario/mostrar/5082368/fach-cancela-satelite-fasat-delta-incumplir-imagesat-international-puesta-operacional) · [BioBioChile — 300 días sin operar](https://www.biobiochile.cl/noticias/ciencia-y-tecnologia/ciencia/2024/05/13/problemas-tecnicos-satelite-chileno-fasat-delta-cumple-300-dias-en-orbita-pero-no-esta-operativo.shtml)

**Notas de incertidumbre:** Lemu Nge — rango espectral 420 vs 450 nm según fuente;
LTAN/swath no publicados. FASat-Delta — prensa dice "~90–100 kg", specs técnicas dan
86 kg/500 km (priorizadas).
