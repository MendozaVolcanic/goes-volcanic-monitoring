# Registro de fuentes de pago / con restricción

Archivo de control para el proyecto GOES Volcanic Monitoring. Aquí se
registra cualquier fuente de datos que tenga costo monetario, paywall,
licencia restrictiva, o requisito de registro obligatorio.

**Fecha del último barrido:** 2026-04-23
**Responsable:** Nicolás (SERNAGEOMIN) / asistencia Claude

## Resumen ejecutivo

**No hay fuentes de pago imprescindibles para el dashboard.**

Todas las fuentes usadas actualmente (AWS S3 `noaa-goes19`, RAMMB/CIRA
SLIDER, Open-Meteo, VOLCAT CIMSS/SSEC) son **gratuitas y sin registro**.

Las fuentes "planificadas / viables" que requieren registro son **free tier
gratuitas sin costo monetario** — solo hay que crear una cuenta.

## Fuentes en uso activo (sin costo, sin registro)

| Fuente | URL | Uso en proyecto |
|--------|-----|-----------------|
| AWS S3 `noaa-goes19` | `s3://noaa-goes19/` | Bandas L1b NetCDF |
| RAMMB/CIRA SLIDER | https://rammb-slider.cira.colostate.edu/ | Tiles RGB (GeoColor, Ash, SO2) |
| Open-Meteo | https://api.open-meteo.com/ | Viento GFS a presión |
| VOLCAT CIMSS/SSEC | https://volcano.ssec.wisc.edu/ | Ash Height PNG + API JSON |
| Smithsonian GVP | https://volcano.si.edu/ | Metadata volcanes (consulta) |

Rate limits relevantes:
- **Open-Meteo**: 10 000 requests/día sin API key. Para el dashboard con 60s
  de cache y ~9 puntos de grilla = muy por debajo del límite.
- **AWS S3 NOAA**: sin rate limit documentado. Requestor-pays OFF (no cobra
  egress a quien descarga).
- **VOLCAT**: sin rate limit documentado. Cadencia ABI 10 min ⇒ trivial.

## Fuentes que requieren **cuenta gratuita**

Son "free tier" — sin costo monetario, pero requieren registro. No las
usamos hoy; quedan como opciones si subimos de nivel.

| Fuente | Qué pedirían si se usara | Esfuerzo de registro |
|--------|-------------------------|----------------------|
| NASA Earthdata (MODIS MOD14, VIIRS VNP14, ASTER) | email + acepto de EULA | 5 min, gratis |
| Copernicus Data Space (Sentinel-5P TROPOMI, Sentinel-2, Sentinel-3) | email + confirmar | 5 min, gratis |
| Copernicus CDS (ERA5 reanálisis) | cuenta CDS + token API | 10 min, gratis |
| EUMETSAT Data Store (GOME-2) | cuenta + aceptar licencia | 10 min, gratis |

Todas son **free for scientific and operational use**. Ninguna de estas
es imprescindible para el scope actual del dashboard.

## Fuentes con paywall o licencia restrictiva consideradas y descartadas

**Ninguna.** No se identificó ninguna fuente necesaria para el scope del
proyecto que esté detrás de paywall.

Se revisaron explícitamente (y se descartaron por no ser necesarios, NO
por tema económico):

| Fuente | Estado | Motivo de descarte |
|--------|--------|--------------------|
| Planet Labs (imagen comercial alta resolución) | Pago | No aporta a monitoreo volcánico operacional desde geo-estacionario |
| Maxar (WorldView sub-metro) | Pago | Ídem anterior |
| ECMWF MARS (reanálisis histórico completo) | Licencia institucional | Para NRT usamos open-data + GFS libre |

## ¿Qué pasa si en el futuro necesitamos algo de pago?

Procedimiento sugerido:
1. Agregarlo a este archivo antes de gastar.
2. Documentar: **qué se gana** que no se tiene con la versión libre.
3. Documentar **costo mensual/anual y quién lo paga**.
4. Documentar **cómo se guarda la credencial** (Streamlit secrets,
   variable de entorno, etc — nunca en el repo).

## Checklist de verificación

- [x] Ningún archivo en `src/` o `dashboard/` requiere API key de pago
- [x] Ninguna credencial en `.env` o `st.secrets` para el dashboard actual
- [x] `requirements.txt` no contiene paquetes con licencia comercial
- [x] Todas las URLs del proyecto son de dominio `.noaa.gov`, `.nasa.gov`,
      `.colostate.edu`, `.wisc.edu`, `.open-meteo.com`, `aws.amazon.com`
      o equivalente público

**Conclusión:** el proyecto opera 100% sobre infraestructura gratuita.
