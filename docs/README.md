# Documentación GOES Volcanic Monitoring

Índice de toda la documentación técnica del proyecto.

## Estructura

```
docs/
├── README.md                          ← este archivo (índice)
├── 01_GOES_ABI_bandas_volcanicas.md   bandas ABI relevantes para ceniza/SO2
├── 02_acceso_datos_AWS_S3.md          cómo acceder a noaa-goes19
├── 03_plataformas_web_GOES.md         RAMMB, VOLCAT, CIMSS etc
├── 04_librerias_python_GOES.md        goes2go, satpy, xarray
│
├── altura_pluma/                      ★ NUEVO ★
│   ├── README.md                      resumen: cómo mide GOES la altura
│   ├── VOLCAT_api_reference.md        endpoint REST de VOLCAT (integrable)
│   ├── metodos_fisicos.md             BT-matching, parallax, CO2 slicing
│   └── sectores_VOLCAT_chile.md       lista de sectores VOLCAT para Chile
│
├── fuentes/                           catálogo de fuentes de datos
│   ├── FUENTES.md                     inventario completo
│   └── REGISTRO_PAGO.md               ★ fuentes con paywall / de pago ★
│
├── manuales_pdf/                      PDFs de libre acceso (descargados)
│   ├── ATBD_CloudHeight_ACHA_v3.0_Jul2012.pdf     algoritmo ACHA (altura)
│   ├── ATBD_GOES-R_VolAsh_v3.0_July2012.pdf       algoritmo VAAF (ya existía)
│   ├── RAMMB_CIRA_SO2_RGB_QuickGuide.pdf
│   ├── CIMSS_GOESR_VolcanicAsh_QuickGuide.pdf
│   ├── GOES-R_PUG_L2_Vol5_ProductUsersGuide.pdf
│   ├── Quick_Guide_SO2_RGB.pdf                    (ya existía)
│   ├── GOES_Ash_RGB.pdf                           (ya existía)
│   ├── Aviation_SO2_v1.0_no_color.pdf             (ya existía)
│   └── Version1.1_Beginners_Guide_to_GOES-R_Series_Data.pdf (ya existía)
│
└── papers_links/                      papers científicos (links, no PDFs)
    └── LINKS.md
```

## Qué está cubierto

### Productos de GOES-19 que usamos hoy
- **L1b bandas 8, 11, 13, 14, 15** (AWS S3) — cálculo propio de Ash RGB y BTD
- **RAMMB/CIRA SLIDER tiles** — GeoColor, Ash RGB, SO2 RGB pre-renderizados
- **VOLCAT (CIMSS/SSEC)** — ★ **Ash_Height** ★ y otros productos derivados

### Productos adicionales documentados
- **ABI-L2-ACHAF** (NOAA) — Cloud Top Height genérico desde S3
- **Wind GFS via Open-Meteo** — vectores de viento sobre los mapas
- **VAAC advisories** (Washington, Buenos Aires) — polígonos de advertencia

## Estado de fuentes

| Fuente | Costo | Uso en dashboard |
|--------|-------|------------------|
| AWS S3 `noaa-goes19` | **Gratis** | En uso |
| RAMMB/CIRA SLIDER | **Gratis** | En uso |
| VOLCAT (volcano.ssec.wisc.edu) | **Gratis** | **A integrar** |
| NOAA ABI-L2-ACHAF S3 | **Gratis** | A integrar (opcional) |
| Open-Meteo (viento GFS) | **Gratis** (tier 10k req/día) | En uso |
| NOAA-CLASS (NetCDF VOLCAT) | **Gratis pero requiere cuenta** | No integrado |
| TROPOMI/Sentinel-5P (SO2 UV) | **Gratis** (Copernicus Hub) | No integrado |
| Washington VAAC XML | **Gratis** | No integrado |
| Buenos Aires VAAC (cubre Chile) | **Gratis** | No integrado |

**Ver `fuentes/REGISTRO_PAGO.md`** para detalle de cada fuente paga/restringida
encontrada en la investigación (de momento: **ninguna de las que necesitamos**).
