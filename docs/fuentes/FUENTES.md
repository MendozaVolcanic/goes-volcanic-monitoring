# Catálogo de fuentes de datos

Inventario completo de fuentes consideradas/usadas en el proyecto.
Para el registro específico de fuentes pagadas o con restricción, ver
`REGISTRO_PAGO.md`.

## Leyenda de estado

- ✅ **En uso** — ya integrado en el dashboard
- 🔜 **A integrar** — planificado
- ⏸️ **Disponible** — descartado por ahora pero viable técnicamente
- ❌ **Descartado** — no sirve o está descontinuado

## Datos satelitales GOES

| Fuente | Contenido | Acceso | Costo | Estado |
|--------|-----------|--------|-------|--------|
| AWS S3 `noaa-goes19` | L1b bandas (NetCDF) | HTTPS/s3fs sin credenciales | **Gratis** | ✅ |
| AWS S3 `noaa-goes19` ABI-L2-ACHAF | Cloud Top Height | HTTPS/s3fs sin credenciales | **Gratis** | 🔜 |
| AWS S3 `noaa-goes19` ABI-L2-FDCF | Hot Spots (fuego/volcanes) | HTTPS/s3fs sin credenciales | **Gratis** | ⏸️ |
| AWS S3 `noaa-goes19` ABI-L2-AODF | Aerosol Optical Depth | HTTPS/s3fs sin credenciales | **Gratis** | ⏸️ |
| ~~ABI-L2-VAAF~~ | Ash Detection + Height | — | — | ❌ descontinuado en GOES-19 |
| RAMMB/CIRA SLIDER | Tiles RGB pre-compuestos (GeoColor, Ash, SO2) | HTTPS tile XYZ | **Gratis** | ✅ |
| VOLCAT CIMSS/SSEC | Ash Height, Loading, Probability, Reff, BT11, BTD | REST JSON + PNG directo | **Gratis** | 🔜 |
| NOAA STAR GOES viewer | Ejemplos de producto | Visual solamente | **Gratis** | ⏸️ (no API) |

## Datos meteorológicos

| Fuente | Contenido | Acceso | Costo | Estado |
|--------|-----------|--------|-------|--------|
| Open-Meteo | Viento GFS a niveles de presión | REST sin auth | **Gratis** (10k req/día) | ✅ |
| NOMADS NOAA | GFS grib2 raw | HTTPS directo | **Gratis** | ⏸️ |
| ECMWF Open Data | IFS open-data grib2 | HTTPS directo | **Gratis** | ⏸️ |
| Copernicus ERA5 | Reanálisis atmosférico | CDS API (requiere registro) | Gratis / requiere cuenta | ⏸️ |

## Advisories / alerts

| Fuente | Contenido | Acceso | Costo | Estado |
|--------|-----------|--------|-------|--------|
| Washington VAAC | Ash advisories XML/texto | HTTPS pull | **Gratis** | 🔜 |
| Buenos Aires VAAC (SMN AR) | Ash advisories cubriendo Chile | HTTPS (portal) | **Gratis** | 🔜 |
| VOLCAT alerts feed | Detección automática de eruption | Documentado pero path cambia | **Gratis** | ⏸️ |
| Smithsonian GVP | Actividad volcánica semanal | RSS | **Gratis** | ⏸️ |

## Datos de SO2 adicionales (UV / hiperespectral)

| Fuente | Contenido | Acceso | Costo | Estado |
|--------|-----------|--------|-------|--------|
| TROPOMI/Sentinel-5P | SO2 columnar diario (UV) | Copernicus Hub API | **Gratis** (requiere cuenta) | ⏸️ |
| OMPS/NPP | SO2 columnar | NASA Earthdata | **Gratis** (requiere cuenta) | ⏸️ |
| GOME-2 | SO2 columnar | EUMETSAT Data Store | **Gratis** (requiere cuenta) | ⏸️ |

## Catálogos y metadata de volcanes

| Fuente | Contenido | Acceso | Costo | Estado |
|--------|-----------|--------|-------|--------|
| SERNAGEOMIN RNVV | Catálogo 43 volcanes Chile, ranking 2019 | Papers + scraping | **Gratis** | ✅ (embebido en `src/volcanos.py`) |
| Smithsonian GVP | Volcanes mundiales con metadata | CSV/JSON libre | **Gratis** | ⏸️ |

## Datos térmicos complementarios

| Fuente | Contenido | Acceso | Costo | Estado |
|--------|-----------|--------|-------|--------|
| MODIS MOD14 / MYD14 | Thermal anomalies globales | NASA LAADS / Earthdata | **Gratis** (requiere cuenta) | ⏸️ |
| VIIRS VNP14IMG | Thermal anomalies 375 m | NASA LAADS / Earthdata | **Gratis** (requiere cuenta) | ⏸️ |
| MIROVA | Thermal Volcanic Radiative Power | Portal web | Uso libre; para Chile usamos VRP Chile | ⏸️ (relacionado a otro proyecto) |
| ASTER | High-res térmico e SWIR | NASA Earthdata | **Gratis** (requiere cuenta) | ⏸️ |
| Sentinel-2 MSI | Multiespectral 10-60 m | Copernicus Hub | **Gratis** (requiere cuenta) | ⏸️ |
| Sentinel-3 SLSTR | Térmico 1 km | Copernicus Hub | **Gratis** (requiere cuenta) | ⏸️ |

## Conclusión

**Todas las fuentes que necesitamos para el dashboard son gratuitas y la
mayoría no requieren registro.** Las que requieren cuenta
(Copernicus, Earthdata, CDS) son todas "free tier" sin costo.

No se identificaron fuentes de pago imprescindibles.

Ver detalle en `REGISTRO_PAGO.md`.
