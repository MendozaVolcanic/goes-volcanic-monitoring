# GOES Volcanic Monitoring Dashboard - Plan de Implementación

## Visión General

Dashboard NRT para monitoreo de volcanes chilenos usando imágenes GOES-19.
Repositorio público en GitHub. Sigue los patrones de VRP Chile y OpenVIS.

## Arquitectura Propuesta

```
goes-volcanic-dashboard/
├── .github/
│   └── workflows/
│       └── nrt.yml              # GitHub Actions: descarga cada 10-30 min
├── src/
│   ├── fetch/
│   │   ├── goes_download.py     # Descarga desde AWS S3 (goes2go o s3fs)
│   │   └── realearth_api.py     # Cliente RealEarth API (VOLCAT products)
│   ├── process/
│   │   ├── ash_rgb.py           # Generación Ash RGB (B15-B14, B14-B11, B13)
│   │   ├── so2_rgb.py           # Generación SO2 RGB
│   │   ├── thermal.py           # Anomalías térmicas (Band 7, 3.9um)
│   │   ├── btd.py               # Brightness Temperature Difference
│   │   └── crop_chile.py        # Recorte a región chilena
│   ├── volcanos.py              # Catálogo 43 volcanes chilenos (coords, ROI)
│   └── config.py                # Configuración centralizada
├── dashboard/
│   ├── app.py                   # Streamlit app principal
│   ├── pages/
│   │   ├── overview.py          # Mapa general + estado de volcanes
│   │   ├── volcano_detail.py    # Vista detallada por volcán
│   │   ├── ash_tracker.py       # Seguimiento de plumas de ceniza
│   │   └── gallery.py           # Galería de imágenes recientes
│   └── components/
│       ├── map.py               # Componente mapa (Folium/Plotly)
│       └── charts.py            # Componentes de gráficos
├── data/
│   ├── raw/                     # NetCDF descargados (gitignored)
│   ├── processed/               # Imágenes RGB generadas
│   └── alerts/                  # JSON de alertas detectadas
├── docs/                        # Documentación (ya creada)
├── tests/
├── requirements.txt
├── README.md
└── CLAUDE.md
```

## Fuentes de Datos (3 canales complementarios)

### Canal 1: AWS S3 - Datos brutos (PRIMARIO)
- **Bucket:** `noaa-goes19` (GOES-East, cubre Chile)
- **Productos:**
  - `ABI-L2-VAAF` → Ceniza volcánica (detección, altura, carga)
  - `ABI-L2-FDCF` → Hot spots (lava, flujos piroclásticos)
  - `ABI-L2-MCMIPF` → Multi-banda para Ash/SO2 RGB custom
  - `ABI-L1b-RadF` → Radiancias L1b para análisis custom
- **Cadencia:** Full Disk cada 10 min, 2 km IR
- **Librería:** goes2go + s3fs
- **Sin credenciales requeridas**

### Canal 2: RealEarth API - Productos VOLCAT
- **Base:** `https://realearth.ssec.wisc.edu/api/`
- **Productos:** Ash detection, SO2 probability, thermal anomalies
- **Formato:** PNG tiles, GeoJSON, GeoTIFF
- **Sin autenticación para productos públicos**
- **Uso:** Quick-look y thumbnails para el dashboard

### Canal 3: RAMMB SLIDER - Visual verification
- **Uso:** Solo para verificación visual manual
- **No es fuente de pipeline** (sin API oficial)

## Fases de Implementación

### Fase 1: Infraestructura Base (Semana 1)
- [ ] Crear repositorio GitHub público
- [ ] Setup Python project (pyproject.toml, requirements.txt)
- [ ] Catálogo de 43 volcanes chilenos (nombre, lat, lon, elevación, ROI)
- [ ] Módulo de descarga AWS S3 (goes2go wrapper)
- [ ] Crop/reproyección a región chilena con cartopy
- [ ] Tests básicos

### Fase 2: Procesamiento de Imágenes (Semana 2)
- [ ] Ash RGB generator (B15-B14, B14-B11, B13)
- [ ] SO2 RGB generator
- [ ] BTD calculator (B14-B15 split-window)
- [ ] Thermal anomaly detector (Band 7)
- [ ] Generación de thumbnails por volcán
- [ ] Validación contra eventos conocidos (Calbuco 2015, Puyehue 2011)

### Fase 3: Dashboard Streamlit (Semana 3)
- [ ] Página Overview: mapa Chile con 43 volcanes + estado
- [ ] Página Detalle: imágenes RGB + time-lapse por volcán
- [ ] Página Ash Tracker: seguimiento de plumas en tiempo real
- [ ] Galería de imágenes recientes
- [ ] KPIs: volcanes activos, últimas detecciones, cobertura

### Fase 4: Automatización NRT (Semana 4)
- [ ] GitHub Actions workflow (cada 30 min o configurable)
- [ ] Pipeline: fetch → process → generate images → update dashboard
- [ ] Sistema de alertas (JSON + potencial email)
- [ ] GitHub Pages o Streamlit Cloud para hosting
- [ ] Documentación completa

### Fase 5: Integración Ecosistema (Futuro)
- [ ] Integrar datos VRP Chile (térmico MODIS/VIIRS)
- [ ] Integrar datos OpenVIS (infrasonido)
- [ ] Dashboard unificado multi-sensor
- [ ] Contactar VOLCAT para acceso a alertas de observatorio

## Decisiones Técnicas

### ¿Por qué Streamlit?
- Consistente con OpenVIS (ya usa Streamlit + Plotly)
- Deploy gratuito en Streamlit Community Cloud
- Rápido de desarrollar, interactivo
- Python nativo (mismo stack que procesamiento)

### ¿Por qué goes2go + AWS S3?
- Sin credenciales (a diferencia de NASA Earthdata en VRP Chile)
- Datos disponibles ~10-30 min post-adquisición
- Full Disk cada 10 min = cobertura continua de Chile
- Librería madura con xarray integration

### ¿Por qué no Satpy inicialmente?
- Heavyweight (muchas dependencias)
- goes2go + numpy/xarray suficiente para RGB custom
- Se puede agregar Satpy después para composites avanzados

### Complementariedad con VRP Chile
- VRP Chile: MODIS/VIIRS, órbita polar, 1km/375m, cada 6h → detección de anomalías TÉRMICAS
- GOES: Geoestacionario, 2km, cada 10 min → seguimiento de PLUMAS (ceniza/SO2) en tiempo real
- Son complementarios, no redundantes

## Volcanes Prioritarios (matching VRP Chile)

1. Villarrica (-39.42, -71.93) - actividad persistente
2. Láscar (-23.37, -67.73) - desgasificación activa
3. Copahue (-37.85, -71.17) - actividad freática recurrente
4. Puyehue-Cordón Caulle (-40.59, -72.12) - última erupción 2011

Luego expandir a los 43 volcanes del catálogo SERNAGEOMIN.

## Documentos que NO pude descargar (requieren descarga manual)

1. Ash RGB Quick Guide (PDF): https://rammb.cira.colostate.edu/training/visit/quick_guides/GOES_Ash_RGB.pdf
2. SO2 RGB Quick Guide (PDF): https://rammb.cira.colostate.edu/training/visit/quick_guides/Quick_Guide_SO2_RGB.pdf
3. Volcanic Ash ATBD v3.0 (PDF): https://www.star.nesdis.noaa.gov/goesr/documents/ATBDs/Baseline/ATBD_GOES-R_VolAsh_v3.0_July2012.pdf
4. SO2 ATBD (PDF): https://www.goes-r.gov/products/ATBDs/option2/Aviation_SO2_v1.0_no_color.pdf
5. Beginner's Guide to GOES-R (PDF): https://noaa-goes16.s3.amazonaws.com/Version1.1_Beginners_Guide_to_GOES-R_Series_Data.pdf
