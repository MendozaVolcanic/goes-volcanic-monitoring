---
slug: goes
title: GOES Volcanic Monitoring
last_updated: 2026-04-25
last_commit: 1fc74f0
status: producción
tier: 1
deploy_url: "https://goesvolcanic.streamlit.app"
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
- Deploy: Streamlit Community Cloud + GitHub Actions

## Datos

| Campo | Detalle |
|---|---|
| Fuente primaria | RAMMB/CIRA Slider (`slider.cira.colostate.edu`) |
| Fuente secundaria | NOAA AWS S3 (`noaa-goes19` bucket) |
| Fuente VOLCAT | SSEC/CIMSS portal (`volcano.ssec.wisc.edu`) |
| Fuente vientos | Open-Meteo API (modelo GFS, niveles 300/500/850 hPa) |
| Cadencia GOES-19 ABI | 10 min Full Disk |
| Latencia RAMMB | 3-5 min después del scan |
| Latencia detección | ≤ 60 s desde publicación RAMMB |
| Latencia total user-visible | 4-7 min después del scan real |
| Formato output | PNG con timestamp + GeoTIFF (EPSG:4326) + GIF/MP4 (animación) + ZIP frames |
| Retención RAMMB | ~28 días |

## Productos disponibles

- **Ash RGB** — composite RAMMB/CIRA (B15-B14, B14-B11, B13)
- **SO2 indicator** — receta JMA basada en B07-B09 / B09-B11
- **GeoColor** — color real mejorado (CIRA)
- **BTD split-window** — BT(11.2) - BT(12.3); negativo = ceniza (Prata 1989)
- **Hot spots NOAA FDCF** — producto L2 ABI con FRP, T_brightness, área sub-pixel
- **VOLCAT** — Ash Height, Ash Loading, Ash Probability, Ash Reff (Pavolonis 2013)
- **VAA** — Volcanic Ash Advisories como GeoJSON
- **Series de tiempo** — % píxeles con firma de ceniza/SO2 por volcán, ventanas 1-24h

## Vistas del dashboard

1. **🔴 En Vivo** — último scan, auto-refresh 60s. Tres tabs principales:
   - **Nacional**: sub-tabs GeoColor / Ash RGB / SO2 (3 productos lado a lado).
   - **Por Zona Volcánica**: sub-tabs por producto, cada uno mostrando grid 4-zonas (Norte/Centro/Sur/Austral) en paralelo.
   - **Volcán**: selector + botón Cargar + sub-tabs por producto (zoom=4).
   - Toggles globales: viento GFS, hot spots FDCF.
2. **Mapa General** — overview con todos los volcanes.
3. **Ash RGB Viewer** — versión propia desde L1b.
4. **Detalle Volcán** — vista detallada con 3 productos + altura VOLCAT.
5. **VOLCAT (SSEC)** — Ash RGB / SO2 RGB pre-procesados + 📏 **Altura de pluma** (4 productos VOLCAT con cheat-sheet visual) + VAA.
6. **Animación (RAMMB)** — loops 1-3h con scope Nacional/Zona/Volcán. Export GIF/MP4/ZIP.
7. **📈 Series de tiempo** — tendencia por volcán con KPIs + **thumbnails contextuales** (PICO + ÚLTIMO con triángulo rojo en el volcán).

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
| Animación MP4 | binary MP4 H.264 | `dashboard/views/rammb_viewer.py::_build_mp4(frames)` | on-demand |
| Animación GIF | binary GIF | `dashboard/views/rammb_viewer.py::_build_gif(frames)` | on-demand |
| Frame estático con georef | GeoTIFF EPSG:4326 | `src/export/geotiff.py::build_geotiff_bytes(img, bounds)` | on-demand |

### Lo que este proyecto CONSUME

| Dato | Formato | Origen | Si falla |
|---|---|---|---|
| Tiles GOES Ash RGB | PNG | RAMMB/CIRA Slider | "RAMMB no disponible" en banner |
| FDCF L2 NetCDF | xarray.Dataset | `noaa-goes19/ABI-L2-FDCF/...` (S3) | Hot spots no se muestran |
| Vientos GFS | JSON | Open-Meteo `api.open-meteo.com/v1/forecast` | Vectores de viento ocultos |
| VOLCAT productos | PNG + JSON metadata | `volcano.ssec.wisc.edu/imagery/get_list/json/...` | Tab "sin datos disponibles" |
| Volcanic Ash Advisories | GeoJSON | `realearth.ssec.wisc.edu/api/shapes` | Tab VAA vacía |

### Pares con integración natural ALTA

- **Lightning-v1** (GLM) → mostrar rayos en cráter en vista "Por Volcán" — alta sinergia operacional. Ver `propuestas/goes_lightning/` en Integracion_Plataformas.
- **VolcPlume-v1** (TROPOMI SO2) → reemplaza el Tier 2 #1 del roadmap GOES. Cuantitativo en DU vs cualitativo del JMA RGB.
- **VRP Chile** → cross-check térmico de eventos GOES (VRP detecta, GOES sigue minuto a minuto).
- **Valles** → si GOES detecta pluma yendo en dirección X, Valles responde qué cuencas/poblaciones quedan aguas abajo.

## Limitaciones conocidas

- **Parallax GOES**: volcanes altos (>4000 m) aparecen ~1-3 km al este de su coord real WGS84.
- **No hay datos históricos**: RAMMB retiene ~28 días, NOAA S3 más pero requiere fetch desde L1b.
- **SO2 RGB es cualitativo**: para cuantificar usar TROPOMI Sentinel-5P (vía VolcPlume-v1).
- **Altura VOLCAT solo PNG**: API pública sirve imagen con colorbar, no NetCDF con valores numéricos. Para uso cuantitativo gestionar feed con CIMSS.
- **No funciona offline**: depende de RAMMB y AWS S3.

## Contactos

- Algoritmo Ash RGB / GeoColor: RAMMB/CIRA, Colorado State University.
- Algoritmo VOLCAT (Ash Height): SSEC/CIMSS, U. Wisconsin–Madison. Mike Pavolonis (mike.pavolonis@noaa.gov).
- FDCF L2: NOAA NESDIS.
- Open-Meteo: tier público, sin auth (https://open-meteo.com/).
