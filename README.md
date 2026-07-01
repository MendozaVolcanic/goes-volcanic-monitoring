---
title: GOES Volcanic Monitor Chile
emoji: 🌋
colorFrom: red
colorTo: yellow
sdk: docker
app_port: 7860
pinned: true
short_description: Monitoreo volcanico NRT con GOES-19 para SERNAGEOMIN
---

# GOES Volcanic Monitoring - Chile

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://goesvolcanic.streamlit.app)
[![Hugging Face Space](https://huggingface.co/datasets/huggingface/badges/resolve/main/open-in-hf-spaces-sm-dark.svg)](https://mendozavolcanic-goes-volcanic-monitoring.hf.space)

> El YAML al inicio de este README es metadata para [Hugging Face Spaces](https://huggingface.co/docs/hub/spaces-config-reference) (mirror del deploy primario). GitHub lo renderiza como texto plano arriba — no es bug.

Dashboard de monitoreo volcánico en tiempo casi-real usando imágenes del satélite geoestacionario **GOES-19** (GOES-East).

**Demos públicas (mismo código, dos hosts para redundancia):**

- 🎈 Streamlit Cloud: https://goesvolcanic.streamlit.app
- 🤗 Hugging Face Spaces: https://mendozavolcanic-goes-volcanic-monitoring.hf.space

Si una está caída (sleep mode, mantención), usar la otra. HF Spaces tiende a ser más estable (16 GB RAM, 48 h sleep) que Streamlit Cloud free (~6 h sleep, crashes intermitentes con Python 3.14).

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

- **Satélite**: GOES-19 (GOES-East, 75.0°W) - cubre toda Sudamérica
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

**Versiones públicas:**

- Streamlit Cloud — https://goesvolcanic.streamlit.app
- Hugging Face Spaces (mirror) — https://mendozavolcanic-goes-volcanic-monitoring.hf.space

Para correr localmente:

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

## Deploy en servidor SERNAGEOMIN (alternativa a Streamlit Cloud)

Para uptime garantizado y acceso desde la LAN del observatorio sin
depender de Streamlit Cloud free, ver guía completa:

📄 **[`docs/DEPLOY_LOCALHOST.md`](docs/DEPLOY_LOCALHOST.md)**

Setup automatizado en Windows (PowerShell):
```powershell
# Como administrador (si vas a registrar el servicio Windows)
.\scripts\setup_localhost.ps1 -InstallService
```

## Referencias

- Prata, A.J. (1989). *Observations of volcanic ash clouds in the 10–12 µm window using AVHRR/2 data*. Int. J. Remote Sensing, 10(4–5), 751–761. https://doi.org/10.1080/01431168908903916
- Pavolonis, M.J., Heidinger, A.K., Sieglaff, J. (2013). *Automated retrievals of volcanic ash and dust cloud properties from upwelling infrared measurements*. JGR Atmospheres, 118(3), 1436–1458. https://doi.org/10.1002/jgrd.50173
- Schmit, T.J. et al. (2017). *A Closer Look at the ABI on the GOES-R Series*. BAMS, 98(4), 681–698. https://doi.org/10.1175/BAMS-D-15-00230.1
- Miller, S.D. et al. (2016). *A Sight for Sore Eyes: The Return of True Color to Geostationary Satellites* (GeoColor). BAMS, 97(10), 1803–1816. https://doi.org/10.1175/BAMS-D-15-00154.1
- GOES-R ATBD Volcanic Ash v3.0 (NOAA/NESDIS)
- RAMMB/CIRA Ash RGB Quick Guide

## Licencia

[Apache-2.0](LICENSE) — código libre. Podés usarlo, modificarlo y redistribuirlo (incluso comercialmente) manteniendo la atribución y el aviso de licencia. Los datos satelitales consumidos (NOAA GOES) son de dominio público; los productos VOLCAT/SSEC requieren atribución a SSEC/CIMSS (Univ. Wisconsin–Madison).
