# GOES Volcanic Monitoring Dashboard

## Qué es este proyecto
Dashboard NRT de monitoreo volcánico para Chile usando GOES-19 (GOES-East).
Genera Ash RGB, detección de ceniza (BTD split-window), indicador SO2, y visualiza
hot spots y color real para 43 volcanes chilenos.

## Stack técnico
- **Datos**: AWS S3 `noaa-goes19` (sin credenciales)
- **Procesamiento**: xarray + numpy (conversión Planck, BTD, Ash RGB)
- **Dashboard**: Streamlit + Plotly + Folium
- **Automatización**: GitHub Actions

## Productos volcánicos
- **Ash RGB**: Composite B15-B14, B14-B11, B13 (receta RAMMB/CIRA)
- **BTD Split-Window**: BT(11.2um) - BT(12.3um). Negativo = ceniza
- **Detección tri-espectral**: BTD + (BT8.4-BT11.2)+(BT12.3-BT11.2) < 0
- **SO2 indicator**: BT(8.4um) - BT(11.2um). Muy negativo = SO2
- **Hot spots**: Producto FDCF L2 (NOAA pre-procesado)

## Hallazgos importantes
- **ABI-L2-VAAF (ceniza pre-procesada) NO existe en GOES-19 ni GOES-18 S3**
  Solo existió brevemente en GOES-16 (2019-2020). Por eso implementamos
  detección propia desde bandas L1b.
- **GOES-19 es GOES-East desde abril 2025** (reemplazó a GOES-16)
- goes2go puede no soportar satellite=19 oficialmente; usamos s3fs directo como fallback

## Convenciones
- Temperaturas de brillo siempre en Kelvin
- Coordenadas WGS84 (lat, lon en grados decimales)
- Timestamps en UTC
- Datos raw en `data/raw/` (gitignored)
- Imágenes procesadas en `data/processed/`

## Constantes físicas
- Coeficientes Planck: **siempre** del NetCDF L1b (planck_fk1, fk2, bc1, bc2)
- Ash RGB ranges: Red [-6.7, 2.6]K, Green [-6.0, 6.3]K, Blue [243.6, 302.4]K
- BTD ash threshold: < -1.0 K (Prata 1989)
- SO2 indicator threshold: < -3 K

## Testing
- Verificar contra eventos conocidos: Calbuco 2015, Puyehue 2011
- Siempre verificar geolocalización con volcanes de coordenadas conocidas
