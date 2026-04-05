# GOES Volcanic Monitoring - Chile

Dashboard de monitoreo volcánico en tiempo casi-real usando imágenes del satélite geoestacionario **GOES-19** (GOES-East).

Genera productos **Ash RGB**, **detección de ceniza** (BTD split-window) y **SO2** para los **43 volcanes activos de Chile** monitoreados por SERNAGEOMIN.

## Productos

| Producto | Método | Bandas ABI | Funciona |
|----------|--------|-----------|----------|
| **Ash RGB** | Composite RAMMB/CIRA | B11, B13, B14, B15 | Día y noche |
| **Detección de ceniza** | BTD split-window + tri-espectral | B11, B14, B15 | Día y noche |
| **Indicador SO2** | BTD 8.4-11.2 um | B11, B14 | Día y noche |
| **Hot spots** | Producto FDCF L2 | B7 | Día y noche |
| **Color real** | GeoColor (MCMIPF) | Multi-banda | Solo día |

## Fuente de datos

- **Satélite**: GOES-19 (GOES-East, 75.2°W) - cubre toda Sudamérica
- **Datos**: AWS S3 bucket `noaa-goes19` (sin credenciales, gratuito)
- **Cadencia**: Full Disk cada 10 minutos, resolución 2 km IR
- **Latencia**: ~10-30 minutos post-adquisición

## Instalación

```bash
git clone https://github.com/nmendozam/goes-volcanic-monitoring.git
cd goes-volcanic-monitoring
pip install -r requirements.txt
```

## Uso rápido

```python
from src.fetch.goes_s3 import download_volcanic_bands, open_band
from src.process.brightness_temp import rad_to_bt
from src.process.ash_rgb import generate_ash_rgb
from datetime import datetime, timezone

# Descargar bandas volcánicas
dt = datetime(2026, 4, 5, 18, 0, tzinfo=timezone.utc)
bands = download_volcanic_bands(dt)

# Convertir a temperatura de brillo
bt11 = rad_to_bt(open_band(bands[11]))
bt13 = rad_to_bt(open_band(bands[13]))
bt14 = rad_to_bt(open_band(bands[14]))
bt15 = rad_to_bt(open_band(bands[15]))

# Generar Ash RGB
rgb = generate_ash_rgb(bt11, bt13, bt14, bt15)
```

## Dashboard

```bash
streamlit run dashboard/app.py
```

## Estructura

```
src/
├── config.py              # Configuración centralizada
├── volcanos.py            # Catálogo 43 volcanes chilenos
├── fetch/
│   └── goes_s3.py         # Descarga desde AWS S3
└── process/
    ├── brightness_temp.py # Radiancias → temperatura de brillo
    ├── ash_rgb.py         # Composite Ash RGB (RAMMB/CIRA)
    ├── ash_detection.py   # Detección ceniza BTD split-window
    └── geo.py             # Geolocalización y recorte
dashboard/
└── app.py                 # Streamlit dashboard
```

## Complementariedad con VRP Chile

| | VRP Chile | GOES Dashboard |
|---|---|---|
| Satélite | MODIS/VIIRS (polar) | GOES-19 (geoestacionario) |
| Resolución | 375m - 1km | 2km |
| Cadencia | ~6 horas | **10 minutos** |
| Detecta | Anomalías térmicas (lava, fumarolas) | **Plumas de ceniza y SO2** |

## Referencias

- Prata, A.J. (1989). Observations of volcanic ash clouds using AVHRR-2
- GOES-R ATBD Volcanic Ash v3.0 (NOAA/NESDIS)
- RAMMB/CIRA Ash RGB Quick Guide

## Licencia

MIT
