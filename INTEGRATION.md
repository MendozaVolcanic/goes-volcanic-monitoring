---
slug: goes
title: GOES Volcanic Monitoring
last_updated: 2026-08-29
last_commit: 4eafc38
status: producción
tier: 1
deploy_url: "https://mendozavolcanic-goes-volcanic-monitoring.hf.space"
repo_url: "https://github.com/MendozaVolcanic/goes-volcanic-monitoring"
---

# Proyecto: GOES Volcanic Monitoring

**Path local:** `..\..\Goes\`
**Estado:** Operacional, NRT en producción.

## Qué hace

Dashboard NRT de monitoreo volcánico para Chile usando GOES-19 (GOES-East).
Genera Ash RGB, indicador SO2, BTD split-window, hot spots NOAA FDCF, series
de tiempo por volcán y altura de pluma VOLCAT (Pavolonis 2013) para los
43 volcanes chilenos.

## Stack

- Python 3.11+
- Datos: AWS S3 `noaa-goes19` (sin credenciales) + RAMMB/CIRA Slider tile server
- Procesamiento: xarray + numpy (Planck conversion, BTD, RGB compositing, reproject)
- Frontend: Streamlit + Plotly (`@st.fragment` para auto-refresh, `@st.cache_data`)
- Otros: pyproj, scipy, rasterio (GeoTIFF), Pillow, imageio-ffmpeg (MP4)
- Deploy: Hugging Face Spaces (Docker) + GitHub Actions

## Datos

| Campo | Detalle |
|---|---|
| Fuente primaria | RAMMB/CIRA Slider (`slider.cira.colostate.edu`) |
| Fuente secundaria | NOAA AWS S3 (`noaa-goes19` bucket) |
| Fuente VOLCAT | SSEC/CIMSS portal (`volcano.ssec.wisc.edu`) |
| Fuente vientos | Open-Meteo API (modelo GFS) + GFS archivado GRIB2 (`noaa-gfs-bdp-pds`, byte-range, validación histórica) |
| Fuente VIIRS | NASA GIBS WMS (`gibs.earthdata.nasa.gov`) — imagen 375 m + anomalías térmicas para volcanes australes sin monitoreo GOES dedicado (complemento, no NRT) |
| Cadencia GOES-19 ABI | 10 min Full Disk |
| Latencia RAMMB | 3-5 min después del scan |
| Latencia detección | ≤ 60 s desde publicación RAMMB |
| Latencia total user-visible | 4-7 min después del scan real |
| Formato output | PNG con timestamp + GeoTIFF (EPSG:4326) + GIF/MP4 (animación) + ZIP frames |
| Retención RAMMB | ~9-10 meses (medido jun-2026: frame OK a 270d; era GOES-19, desde abr-2025) |

## Productos disponibles

- **Ash RGB** — composite RAMMB/CIRA (B15-B14, B14-B11, B13)
- **SO2 indicator** — receta JMA basada en B07-B09 / B09-B11
- **GeoColor** — color real mejorado (CIRA)
- **BTD split-window** — BT(11.2) - BT(12.3); negativo = ceniza (Prata 1989)
- **Hot spots NOAA FDCF** — producto L2 ABI con FRP, T_brightness, área sub-pixel
- **Pulso térmico intradía (FRP timeline)** — serie de FRP (MW) por volcán a
  cadencia GOES (~10 min), pre-cocinada incremental en `data/frp_timeline.json`
  (ventana rodante 48h, workflow `frp_timeline.yml`). Aporta la dimensión
  *temporal* que MODIS/VIIRS no dan; COMPLEMENTA, no sustituye, la plataforma
  VRP MODIS/VIIRS (que gana en magnitud/sensibilidad)
- **VOLCAT** — Ash Height, Ash Loading, Ash Probability, Ash Reff (Pavolonis 2013)
- **Altura de tope propia (INDICATIVO) — 3 métodos** sobre los píxeles de ceniza:
  - **ACHA** (Fase 0): `HT` del producto NOAA `ABI-L2-ACHA2KMF` (Cloud Top
    Height 2 km, Heidinger OE) enmascarado por nuestra detección tri-espectral.
    ~13 min de latencia (vs 30-50 del VOLCAT SSEC).
  - **BT-matching** (Fase 3a): BT(11 µm) del tope opaco → perfil GFS T(z)
    (Open-Meteo) → altitud. **Independiente de SSEC y de la L2 de NOAA**; cota
    inferior. Rescata casos donde ACHA no tiene retrieval (validado: Láscar 27-jun
    6.2 km/15 px con ACHA en no_plume; Popocatépetl BT 9.2 vs ACHA 10.3 km).
  - **Wen-Rose** (Fase 3b, *Wen & Rose 1994*): corrige emisividad con la diferencia
    espectral 11/12 µm → temperatura de tope corregida → **sube** la altura sobre el
    BT-matching en plumas semitransparentes. Ts = BT de cielo claro de la escena
    (fallback GFS skin-T). Independiente de SSEC/NOAA. Validado: Láscar 27-jun
    BT-matching 6.8 → Wen-Rose 10.4 km (Δ+3.6, 8/8 px corregidos). **No se reporta
    pelado**: banda de incertidumbre por β, confianza indicativa (nunca "alta"),
    guards (Δ implausible, Ts de fallback) y árbitro independiente CO₂ 13.3 µm
    (confirma/desmiente la semi-transparencia).
  Los tres cruzan resultados en el dashboard. **No miden gas/SO₂** (transparente en
  11 µm → daría altura espuria; validado vs la pluma SO₂ de Chillán 27-jun). **No
  reemplazan** al VOLCAT cuantitativo. Fases en `docs/own_volcat/`.
- **VAA** — Volcanic Ash Advisories como GeoJSON
- **Series de tiempo** — % píxeles con firma de ceniza/SO2 por volcán, ventanas 1-24h

## Vistas del dashboard

Permalink: `?vista=<slug>` (los slugs viejos `live`/`zonas`/`animacion` redirigen por
compatibilidad). Fuente de verdad: `PAGE_OPTIONS`/`PAGE_SLUGS` en `dashboard/app.py`.

1. **🌎 Vista Operacional** (`operacional`) — último scan, auto-refresh 60s. Tabs Nacional / Por Zona Volcánica (grid 4-zonas) / Volcán. El tab **Volcán** muestra los 4 productos a la vez en grilla 2×2 (GeoColor · Ash RGB · SO₂ · VOLCAT), cada panel con su propia cadencia de refresco (RAMMB 60 s, VOLCAT 120 s), radio ajustable 0.35–3° y toggles de viento GFS y anillos. Comparte implementación con Modo Guardia vía `modo_guardia_volcan.volcan_grid`.
2. **🛡 Modo Guardia** (`guardia`) — vista de turno de sala: sub-tabs Vigilancia diaria (4 zonas RGB), Chile, VOLCAT por zona (4 zonas lado a lado), Mosaico, Volcán (grilla 2×2 de 4 productos) y Loop 2h. Con `?tv=1` entra en **Modo Sala TV** (rotación fullscreen sin controles, pensada para monitor 24/7).
3. **🔀 Comparador** (`comparador`) — dos frames lado a lado (baseline histórico vs actual, o dos productos).
4. **🚨 Modo Evento** (`evento`) — foco en un volcán en crisis, con productos y altura.
5. **📅 Heatmap actividad** (`heatmap`) — pulso térmico intradía de FRP (serie pre-cocinada `data/frp_timeline.json`) + heatmap semanal día × volcán.
6. **🔁 Replay reciente** (`replay`) — repetición de las últimas horas.
7. **📅 Backfill histórico** (`backfill`) — revisión día/hora de eventos pasados desde GitHub Releases (`backfill-<fecha>-<volcán>`). Slider temporal + grid de productos + hot spots + altura VOLCAT. Generado por `scripts/build_backfill.py`. Con `--l1b-fallback` los productos se regeneran desde bandas L1b crudas cuando la fecha cae fuera del archive RAMMB (~9-10 meses) — `src/process/historic_l1b_rgb.py`.
8. **🌡 Ash + BTD (temperaturas K)** (`ash`) — versión propia desde L1b con temperaturas de brillo.
9. **📏 VOLCAT (altura pluma)** (`volcat`) — productos SSEC (Ash Height/Loading/Probability/Reff) con cheat-sheet visual + VAA + cruce con la altura propia.
10. **🎞 Loops descargables** (`loops`) — animaciones 1-3h por scope. Export GIF/MP4/ZIP.
11. **📈 Series de tiempo** (`series`) — tendencia por volcán con KPIs + thumbnails contextuales (PICO y ÚLTIMO).

## Volcanes monitoreados

`src/volcanos.py` — **43 volcanes** chilenos con `(lat, lon, elevación, prioridad)`.
Lista de prioridad (8): Villarrica, Lascar, Calbuco, Copahue, Lonquimay, Llaima, Chaitén, Hudson.

## Cómo se ejecuta

```bash
cd Goes
pip install -r requirements.txt
streamlit run dashboard/app.py
```

## Puntos de integración

### Lo que este proyecto PRODUCE

| Dato | Formato | Endpoint / archivo | Cadencia |
|---|---|---|---|
| Frame Ash RGB / SO2 / GeoColor por volcán | PNG + GeoTIFF | función `fetch_frame_for_bounds(prod, ts, bounds, zoom=4)` en `src/fetch/rammb_slider.py` | 10 min |
| Hot spots FDCF | List[HotSpot] con (lat, lon, FRP_MW, T_K, area_km², confidence) | `src/fetch/goes_fdcf.py::fetch_latest_hotspots(bounds)` | 10 min |
| Series de tiempo por volcán | List[TimeSeriesPoint] / CSV | `src/fetch/timeseries.py::fetch_volcano_timeseries(lat, lon, product)` | on-demand |
| Altura de pluma VOLCAT | PNG con colorbar (no NetCDF) | `src/fetch/volcat_api.py::volcat_latest(sector, ...)` | 10 min |
| Altura de tope ACHA (INDICATIVO) | dict {top_km p95, top_max_km, field_km, lat/lon, latency} | `src/process/acha_plume_height.py::plume_top_height(dt, volcano, radius)` | 10 min |
| HT ACHA recortada a bbox | dict {height_m, dqf, lat/lon, window, scan_dt} | `src/fetch/goes_acha.py::fetch_acha_height_at(dt, bounds)` | 10 min |
| Altura de tope BT-matching (INDICATIVO, propio) | dict {top_km p95, top_max_km, field_km, tropopause_km, lat/lon} | `src/process/bt_matching_height.py::bt_matching_top_height(dt, volcano, radius)` | 10 min |
| Altura de tope Wen-Rose (INDICATIVO, propio) | dict {top_km, top_km_lo/hi (banda β), confidence, flags, n_reverted, co2_semitransp_btd, co2_verdict, composition, bg_spread_k, top_bt_matching_km, delta_km, n_corrected, ts_k/ts_source, field_km} | `src/process/wen_rose_height.py::wen_rose_top_height(dt, volcano, radius)` | 10 min |
| Composición de pluma β-ratios (INDICATIVO) | dict {beta_12_11, beta_85_11, composition, is_ash, n_px} | `src/process/beta_ratios.py::beta_composition(...)` (integrado en wen_rose) | 10 min |
| Altura por cizalla de viento (Fase 3c, NO en dashboard aún) | dict {top_km, band_lo/hi_km, adv_speed_ms, shear_ms} | `src/process/wind_shear_height.py::wind_shear_top_height(dt, volcano)` | on-demand |
| Perfil GFS T(z) + tropopausa + skin-T | dict {levels[{p_hPa,z_m,T_K}], tropopause, skin_temp_K} | `src/fetch/gfs_profile.py::fetch_gfs_profile(lat, lon, dt)` | 6 h (GFS) |
| Perfil T(z) LVTPF del propio GOES (cross-check) | dict {levels[{p_hPa,z_m,T_K}], tropopause, n_clear_px, scan_dt, source} — MISMA forma que GFS | `src/fetch/goes_lvtp.py::fetch_lvtp_profile(lat, lon, dt)` | 10 min |
| Perfil GFS ARCHIVADO (T(z) + viento, validación histórica) | dict MISMA forma que gfs_profile | `src/fetch/gfs_archive.py::fetch_gfs_profile_archive / fetch_gfs_wind_profile_archive` (GRIB2 byte-range; dep opcional `eccodes`) | 6 h (archivo ≥2021) |
| Imagen VIIRS georreferenciada (complemento australes) | dict {image HxWx3, bounds, layer, date, coverage_frac} | `src/fetch/viirs_gibs.py::fetch_viirs_image(lat, lon, when, layer)` (True Color / térmico 375 m / Day-Night, vía NASA GIBS) | ~2 pasadas/día |
| Hot spots térmicos VIIRS 375 m (complemento australes) | List[dict {lat, lon, frp_mw, bright_ti4/5_k, confidence, acq_date, satellite}] | `src/fetch/viirs_firms.py::fetch_viirs_firms_hotspots(bounds, days)` (NASA FIRMS; requiere MAP_KEY gratis en env `FIRMS_MAP_KEY`) | ~2 pasadas/día |
| Animación MP4 | binary MP4 H.264 | `dashboard/views/rammb_viewer.py::_build_mp4(frames)` | on-demand |
| Animación GIF | binary GIF | `dashboard/views/rammb_viewer.py::_build_gif(frames)` | on-demand |
| Frame estático con georef | GeoTIFF EPSG:4326 | `src/export/geotiff.py::build_geotiff_bytes(img, bounds)` | on-demand |

### Lo que este proyecto CONSUME

| Dato | Formato | Origen | Si falla |
|---|---|---|---|
| Tiles GOES Ash RGB | PNG | RAMMB/CIRA Slider | "RAMMB no disponible" en banner |
| FDCF L2 NetCDF | xarray.Dataset | `noaa-goes19/ABI-L2-FDCF/...` (S3) | Hot spots no se muestran |
| ACHA2KMF L2 NetCDF (Cloud Top Height) | xarray.Dataset (var `HT`, `DQF`) | `noaa-goes19/ABI-L2-ACHA2KMF/...` (S3) | Altura propia no se calcula (VOLCAT sigue) |
| LVTPF L2 NetCDF (perfil vertical de T) | xarray.Dataset (var `LVT(y,x,pressure)`, `DQF_Overall/Retrieval`) | `noaa-goes19/ABI-L2-LVTPF/...` (S3) | Cross-check de perfil no disponible (GFS sigue) |
| Vientos GFS | JSON | Open-Meteo `api.open-meteo.com/v1/forecast` | Vectores de viento ocultos |
| Perfil GFS T(z) (pressure levels) | JSON | Open-Meteo `api.open-meteo.com/v1/forecast` (temperature/geopotential_height por nivel) | Altura BT-matching no se calcula |
| VOLCAT productos | PNG + JSON metadata | `volcano.ssec.wisc.edu/imagery/get_list/json/...` | Tab "sin datos disponibles" |
| Volcanic Ash Advisories | GeoJSON | `realearth.ssec.wisc.edu/api/shapes` | Tab VAA vacía |

### Pares con integración natural ALTA

- **Lightning-v1** (GLM) → mostrar rayos en cráter en vista "Por Volcán" — alta sinergia operacional. Ver `propuestas/goes_lightning/` en Integracion_Plataformas.
- **VolcPlume-v1** (TROPOMI SO2) → reemplaza el Tier 2 #1 del roadmap GOES. Cuantitativo en DU vs cualitativo del JMA RGB.
- **VRP Chile** → cross-check térmico de eventos GOES (VRP detecta, GOES sigue minuto a minuto).
- **Valles** → si GOES detecta pluma yendo en dirección X, Valles responde qué cuencas/poblaciones quedan aguas abajo.

## Limitaciones conocidas

- **Parallax GOES**: volcanes altos (>4000 m) aparecen ~1-3 km al este de su coord real WGS84.
- **Profundidad histórica por fuente** (medido jun-2026): RAMMB RGB ~9-10 meses
  (era GOES-19, desde abr-2025); hot spots FDCF en S3 desde el inicio de
  GOES-19 (OK a feb-2025); RealEarth VOLCAT/ash_rgb ≥5 meses. Para ir más atrás
  hay que computar las RGB desde L1b (S3 `noaa-goes19`, indefinido). Pre-abr-2025
  es GOES-16 (no soportado).
- **SO2 RGB es cualitativo**: para cuantificar usar TROPOMI Sentinel-5P (vía VolcPlume-v1).
- **Altura VOLCAT solo PNG**: API pública sirve imagen con colorbar, no NetCDF con valores numéricos. Para uso cuantitativo gestionar feed con CIMSS.
- **No funciona offline**: depende de RAMMB y AWS S3.

## Contactos

- Algoritmo Ash RGB / GeoColor: RAMMB/CIRA, Colorado State University.
- Algoritmo VOLCAT (Ash Height): SSEC/CIMSS, U. Wisconsin–Madison. Mike Pavolonis (mike.pavolonis@noaa.gov).
- FDCF L2: NOAA NESDIS.
- Open-Meteo: tier público, sin auth (https://open-meteo.com/).
