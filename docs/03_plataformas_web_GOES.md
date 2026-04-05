# Plataformas Web para Visualización GOES

## 1. SSEC/CIMSS Volcanic Cloud Monitoring (VOLCAT)

**URL:** https://volcano.ssec.wisc.edu/

### Productos
- **VOLCAT (VOLcanic Cloud Analysis Toolkit)**: Detección automatizada de erupciones con IA
- **Imagery Viewer** (`/imagery/view/`): 100+ dominios espaciales organizados por región VAAC
- **Event Dashboard** (`/event-dashboard/`): Seguimiento NRT de eventos eruptivos
- **Thermal Monitoring** (`/thermal/`): Dashboard térmico por volcán
- **Alertas**: Email/SMS (restringido a VAACs y observatorios vulcanológicos)

### Satélites Procesados
- GOES-East/West, MSG SEVIRI, Himawari, MODIS, VIIRS, CrIS

### Acceso Programático: RealEarth API

**Base URL:** `https://realearth.ssec.wisc.edu/api/`
**Sin autenticación requerida para productos públicos.**

| Endpoint | Propósito | Retorna |
|----------|----------|---------|
| `/api/products?search=volcano` | Buscar productos | JSON |
| `/api/times?products=ID` | Timestamps disponibles | JSON |
| `/api/latest?products=ID` | Último timestamp | JSON |
| `/api/image?products=ID&bounds=S,W,N,E&width=W&height=H` | Imagen por bounds | PNG/GIF/JPEG/GeoTIFF |
| `/api/data?products=ID&lat=LAT&lon=LON` | Valor en punto | JSON |
| `/api/shapes?products=ID` | Features vectoriales | GeoJSON |

### Tile Server
```
https://realearth.ssec.wisc.edu/tiles/{productID}/{zoom}/{col}/{row}.png
https://realearth.ssec.wisc.edu/tiles/{productID}/{YYYYMMDD}/{HHMMSS}/{zoom}/{col}/{row}.png
```

### WMS (compatible GIS)
```
https://realearth.ssec.wisc.edu/cgi-bin/mapserv?map={PRODUCT_ID}.map&service=wms&version=1.3.0&request=GetCapabilities
```

### Otros formatos
- **KML:** `https://realearth.ssec.wisc.edu/kml/?products=PRODUCT_ID`
- **THREDDS:** `https://realearth.ssec.wisc.edu/thredds/catalog.xml`

### Notas
- Datos retenidos ~28 días en el portal
- Imágenes vía API con bounds llevan watermark
- VOLCAT NetCDF en Zenodo: CC-BY-4.0
- GitLab VOLCAT: https://gitlab.ssec.wisc.edu/volcat
- Contacto: realearth@ssec.wisc.edu

---

## 2. RAMMB/CIRA SLIDER

**URL:** https://slider.cira.colostate.edu/

### Características
- Visor web basado en tiles PNG
- Satélites: GOES-19, GOES-18, Himawari-9, Meteosat-9, GEO-KOMPSAT-2A, JPSS
- Sectores: Full Disk, CONUS/PACUS, Mesoscale 1 & 2
- Productos: 16 bandas ABI + composites RGB (GeoColor, Ash RGB, SO2 RGB, Dust RGB, etc.)

### URLs no documentadas (reverse-engineered)

**Tiles:**
```
https://rammb-slider.cira.colostate.edu/data/imagery/{DATE}/{SATELLITE}---{SECTOR}/{PRODUCT}/{TIMESTAMP}/{ZOOM}/{TILE_Y}_{TILE_X}.png
```

**JSON API:**
```
# Fechas disponibles
https://rammb-slider.cira.colostate.edu/data/json/{SATELLITE}/{SECTOR}/{PRODUCT}/available_dates.json

# Últimos tiempos
https://rammb-slider.cira.colostate.edu/data/json/{SATELLITE}/{SECTOR}/{PRODUCT}/latest_times.json
```

### Herramienta CLI
- **SLIDER-cli**: https://github.com/colinmcintosh/SLIDER-cli (Go)
- Automatiza descarga de tiles y stitching

### Nota
El SLIDER NO tiene API oficial pública. Para acceso programático/bulk, usar AWS S3.

---

## 3. NESDIS STAR GOES

**URL:** https://www.star.nesdis.noaa.gov/goes/

### Características
- Imágenes de GOES-East (GOES-19) y GOES-West (GOES-18)
- 16 bandas ABI + composites RGB
- Cobertura: CONUS, PACUS, Alaska, Caribe, México, regiones
- Animaciones hasta 12-24 horas
- Datos experimentales, no operacionales 24/7

### Productos Volcánicos Operacionales
- **ABI-VAA (Volcanic Ash Algorithm)**: Usa 5 canales IR (7.3, 8.5, 11, 12, 13.3 um)
  - Altura de nube de ceniza
  - Carga másica de ceniza
  - Confianza de detección
- **SO2 Algorithm**: Usa bandas 10 (7.34um) y 11 (8.5um)
  - Umbral detección: ≥10 Dobson Units
  - Capacidad NUEVA de serie GOES-R (GOES anteriores no tenían 7.3um ni 8.5um)

### ATBDs (Algorithm Theoretical Basis Documents)
- Volcanic Ash ATBD v3.0: https://www.star.nesdis.noaa.gov/goesr/documents/ATBDs/Baseline/ATBD_GOES-R_VolAsh_v3.0_July2012.pdf
- SO2 ATBD: https://www.goes-r.gov/products/ATBDs/option2/Aviation_SO2_v1.0_no_color.pdf

---

## 4. GeoSphere (SSEC)

**URL:** https://geosphere.ssec.wisc.edu/

Visor 3D en tiempo real de datos GOES.

---

## Resumen: Mejor fuente por caso de uso

| Caso de Uso | Fuente Recomendada |
|-------------|-------------------|
| **Pipeline NRT automatizado** | AWS S3 (`noaa-goes19`) |
| **Visualización rápida** | RAMMB SLIDER o NESDIS STAR |
| **API web para dashboard** | RealEarth API (SSEC) |
| **Alertas volcánicas** | VOLCAT (requiere registro de observatorio) |
| **Datos históricos** | AWS S3 + Google Cloud |
| **Integración GIS** | RealEarth WMS |
| **Análisis científico** | AWS S3 + Satpy |
