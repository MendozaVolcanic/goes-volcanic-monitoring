# Librerías Python para Datos GOES

## 1. goes2go (Recomendada para descarga)

- **Repo:** https://github.com/blaylockbk/goes2go
- **Docs:** https://goes2go.readthedocs.io/
- **Instalación:**
  ```bash
  conda install -c conda-forge goes2go
  # o
  pip install goes2go
  ```

### Uso básico
```python
from goes2go import GOES

# Ceniza volcánica - Full Disk
G = GOES(satellite=19, product="ABI-L2-VAAF", domain='F')

# Último dato disponible
ds = G.latest()

# Dato más cercano a una hora
ds = G.nearesttime('2026-04-05 18:00')

# Descarga batch por rango de tiempo
G.timerange(start='2026-04-05 00:00', end='2026-04-05 06:00')

# Últimos 30 minutos
G.timerange(recent='30min')

# Listar archivos como DataFrame
df = G.df(start='2026-04-05', end='2026-04-06')
```

### Notas
- Soporta satélites 16, 17, 18 (GOES-19 puede requerir actualización)
- Dominios: 'F' (Full Disk), 'C' (CONUS), 'M' (Mesoscale)
- Retorna xarray Datasets (NetCDF4)

---

## 2. Satpy (Recomendada para procesamiento)

- **Repo:** https://github.com/pytroll/satpy
- **Docs:** https://satpy.readthedocs.io/
- **Framework:** PyTroll (https://pytroll.github.io/)
- **Instalación:**
  ```bash
  conda install -c conda-forge satpy
  # o
  pip install satpy
  ```

### Composites volcánicos incorporados
- `ash` - Ash RGB
- `so2` - SO2 RGB
- `dust` - Dust RGB
- `airmass` - Airmass RGB

### Uso básico
```python
from satpy import Scene

# Cargar datos GOES ABI
scn = Scene(reader='abi_l1b', filenames=glob('*.nc'))

# Cargar composite de ceniza
scn.load(['ash'])

# Reproyectar a zona de interés
local_scn = scn.resample('chile_area')

# Guardar imagen
scn.save_dataset('ash', 'ash_rgb.png')
```

---

## 3. GOES (joaohenry23)

- **Repo:** https://github.com/joaohenry23/GOES
- **Instalación:** `pip install GOES`
- Soporta GOES-16/17/18/19
- Incluye helpers de plotting

---

## 4. GOES-DL (Más completa para históricos)

- **Repo:** https://github.com/wvenialbo/GOES-DL
- **Instalación:** `pip install goes-dl`
- Soporta GOES-8 hasta GOES-19 + GridSat
- Interfaz unificada AWS + NCEI
- Requiere Python 3.10+

---

## 5. Acceso directo S3 (s3fs / boto3)

```python
import s3fs
import xarray as xr

fs = s3fs.S3FileSystem(anon=True)

# Listar archivos
files = fs.ls('noaa-goes19/ABI-L2-VAAF/2026/095/18/')

# Abrir con xarray
ds = xr.open_dataset(fs.open(files[0]))
```

---

## Stack Recomendado para el Proyecto

| Componente | Librería | Rol |
|-----------|---------|-----|
| Descarga | goes2go o s3fs | Obtener datos de AWS S3 |
| Procesamiento | satpy + xarray | Composites RGB, reproyección |
| Visualización | matplotlib + cartopy | Mapas estáticos |
| Dashboard | Streamlit + Plotly | Dashboard interactivo web |
| Scheduling | GitHub Actions | Automatización NRT |

---

## Documentos de no pude descargar directamente

Los siguientes PDFs son referenciados pero requieren descarga manual:

1. **Ash RGB Quick Guide (PDF):** https://rammb.cira.colostate.edu/training/visit/quick_guides/GOES_Ash_RGB.pdf
2. **SO2 RGB Quick Guide (PDF):** https://rammb.cira.colostate.edu/training/visit/quick_guides/Quick_Guide_SO2_RGB.pdf
3. **Volcanic Ash ATBD v3.0 (PDF):** https://www.star.nesdis.noaa.gov/goesr/documents/ATBDs/Baseline/ATBD_GOES-R_VolAsh_v3.0_July2012.pdf
4. **SO2 ATBD (PDF):** https://www.goes-r.gov/products/ATBDs/option2/Aviation_SO2_v1.0_no_color.pdf
5. **Beginner's Guide to GOES-R (PDF):** https://noaa-goes16.s3.amazonaws.com/Version1.1_Beginners_Guide_to_GOES-R_Series_Data.pdf

Estos se pueden descargar manualmente desde el navegador.
