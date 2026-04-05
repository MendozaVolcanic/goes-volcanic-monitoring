# Acceso a Datos GOES via AWS S3

## Buckets Disponibles (sin autenticación)

| Bucket | Satélite | Estado |
|--------|----------|--------|
| `s3://noaa-goes19` | **GOES-19 (GOES-East desde abril 2025)** | **Activo - cubre Sudamérica/Chile** |
| `s3://noaa-goes18` | GOES-18 (GOES-West) | Activo |
| `s3://noaa-goes16` | GOES-16 | Archivo histórico (2018-2024) |
| `s3://noaa-goes17` | GOES-17 | Offline |

**Región AWS:** `us-east-1`

## Estructura de Rutas

```
s3://noaa-goes19/<Producto>/<Año>/<DíaDelAño>/<Hora>/<archivo>.nc
```

### Convención de nombres de archivo
```
OR_ABI-L2-VAAF-M6_G19_s20260095180034_e20260095189412_c20260095190053.nc
```
- `OR` = Operational Real-time
- `ABI-L2-VAAF` = sensor-nivel-producto
- `M6` = modo de escaneo 6
- `G19` = GOES-19
- `s` = inicio de escaneo (YYYYDDDHHMMSSx)
- `e` = fin de escaneo
- `c` = creación del archivo

## Productos L2 para Monitoreo Volcánico

| Código | Nombre | Relevancia |
|--------|--------|-----------|
| **ABI-L2-VAAF** | **Volcanic Ash Detection & Height** | **Producto primario: detección ceniza, altura, carga másica** |
| **ABI-L2-FDCF** | **Fire/Hot Spot Characterization** | **Anomalías térmicas - flujos de lava, respiraderos** |
| ABI-L2-ADPF | Aerosol Detection | Clasificación tipo aerosol (humo, polvo, ceniza) |
| ABI-L2-AODF | Aerosol Optical Depth | Carga cuantitativa de aerosoles |
| ABI-L2-ACHAF | Cloud Top Height | Estimación altura de columna eruptiva |
| ABI-L2-ACHTF | Cloud Top Temperature | Discriminación nubes volcánicas |
| ABI-L2-ACTPF | Cloud Top Phase | Discriminación hielo vs ceniza |
| ABI-L2-MCMIPF | Multi-Channel CMI | Imágenes multi-banda para análisis visual |
| ABI-L1b-RadF | Level 1b Radiances | Radiancias calibradas para algoritmos custom |

**Sufijos de dominio:** F=Full Disk, C=CONUS, M=Mesoscale

## Acceso CLI (sin credenciales)

```bash
# Listar productos de ceniza volcánica
aws s3 ls --no-sign-request s3://noaa-goes19/ABI-L2-VAAF/2026/095/

# Descargar un archivo
aws s3 cp --no-sign-request s3://noaa-goes19/ABI-L2-VAAF/2026/095/18/archivo.nc ./
```

## Acceso Python

### Con goes2go (recomendado)
```python
from goes2go import GOES

# Ceniza volcánica - Full Disk
G = GOES(satellite=19, product="ABI-L2-VAAF", domain='F')
ds = G.latest()                                    # último disponible
ds = G.nearesttime('2026-04-05 18:00')            # más cercano a hora
G.timerange(start='2026-04-05', end='2026-04-06') # rango de tiempo
```

### Con s3fs (acceso directo)
```python
import s3fs
import xarray as xr

fs = s3fs.S3FileSystem(anon=True)
files = fs.ls('noaa-goes19/ABI-L2-VAAF/2026/095/18/')
ds = xr.open_dataset(fs.open(files[0]))
```

## Latencia de Datos

- **AWS S3**: ~10-30 minutos después de adquisición
- **Full Disk**: cada 10 minutos
- **CONUS**: cada 5 minutos
- **Mesoscale**: cada 30-60 segundos

## Notificaciones SNS (para pipelines event-driven)

- GOES-19: `arn:aws:sns:us-east-1:123901341784:NewGOES19Object`
- GOES-18: `arn:aws:sns:us-east-1:123901341784:NewGOES18Object`

## Google Cloud (alternativa)

| Bucket | Contenido |
|--------|-----------|
| `gcp-public-data-goes-16` | Archivo completo GOES-16 |

También disponible en Google Earth Engine: `NOAA/GOES/16/MCMIPF`

## Referencias
- AWS Open Data Registry: https://registry.opendata.aws/noaa-goes/
- Beginner's Guide to GOES-R: https://noaa-goes16.s3.amazonaws.com/Version1.1_Beginners_Guide_to_GOES-R_Series_Data.pdf
- NOAA STAR Python tutorials: https://www.star.nesdis.noaa.gov/atmospheric-composition-training/python_abi_level2_download.php
