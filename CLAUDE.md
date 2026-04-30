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

## Filosofía operacional
- **NO inventar métricas automáticas** sobre Ash RGB color: cirros y nieve dan falsos positivos 30-60% en Chile invierno. Para `% ash` usar `_ash_red_fraction_v2` (filtra cirros + nieve). Para magnitud absoluta cuantitativa usar VOLCAT (Pavolonis 2013).
- Métricas validadas externas a privilegiar: hot spots NOAA FDCF, altura VOLCAT.
- `STATUS.md` es curado por humanos; `STATUS_NRT.md` lo regenera el bot cada 10 min — NO mezclar.

## Patrones de código
- **Auto-refresh**: `@st.fragment(run_every="60s")` para panel; selectores VAN AFUERA del fragment para preservar estado entre reruns.
- **Sidebar routing + permalinks**: `PAGE_OPTIONS` list + `PAGE_SLUGS` dict en `dashboard/app.py`. URL `?vista=<slug>` setea inicial, escribe el slug al cambiar.
- **Modo fullscreen global**: `?fullscreen=1` oculta sidebar via CSS, padding 0.4rem, max-width 100%.
- **RAMMB resiliente**: `fetch_frame_robust(product, timestamps, bounds, zoom_preferred, zoom_fallback)` en `src/fetch/rammb_slider.py` — RAMMB falla intermitente en `eumetsat_ash`/`jma_so2` zoom=4. Devuelve `(img, ts_usado, zoom_usado)`.

## Gotchas conocidos
- **Streamlit Cloud import errors**: `from src.X import Y` desde módulos en `dashboard/` puede romperse por cache stale entre deploys (aunque funcione local). Fix: inline el dato en `dashboard/` o usar lazy import dentro de funciones.
- **Plotly scaleratio en lat/lon**: con `scaleratio=1` los círculos geográficos se ven como óvalos. Usar `scaleratio = 1/cos(lat)` para 1 km vertical = 1 km horizontal visual.
- **Título Plotly largo achica el plot**: wrappea a 2 líneas si pasa de ~30 chars. Usar `title=""` y poner el label en `st.markdown` arriba del plot.
- **Calbuco 2015 NO sirve para test de plataforma**: RAMMB no archiva GOES-13. Usar eventos recientes (Sangay, Reventador, Sabancaya) del archive GOES-19 ~28 días.

## Comandos comunes
- `python -m pytest tests/ -q` — 44 tests (smoke imports, Planck round-trip, geo subsatélite)
- Workflow `goes.yml` corre cada 10 min, escribe `STATUS_NRT.md` (NO `STATUS.md`)
- Workflow `hotspots_daily.yml` corre 02:00 UTC, regenera `data/hotspots_daily.json` para Heatmap
- Workflow `lascar_pdf.yml` corre 11:00 UTC, genera reporte PDF en `reports/lascar/`

## Testing
- Verificar contra eventos conocidos: Calbuco 2015 (sólo para Wen-Rose con L1b GOES-13, no RAMMB), Puyehue 2011
- Siempre verificar geolocalización con volcanes de coordenadas conocidas

## Mantener INTEGRATION.md actualizado

Este proyecto tiene un archivo `INTEGRATION.md` en la raíz que documenta sus
puntos de integración con otros proyectos volcanológicos (VRP, Lightning,
VolcPlume, Valles, etc).

**Actualizá `INTEGRATION.md` cuando**:
- Agregues un producto nuevo (página, fetcher, formato de export).
- Cambie una API que consumimos (RAMMB, NOAA S3, VOLCAT, Open-Meteo).
- Cambie el stack mayor (deps nuevas, deploy, frontend).
- Hagas un release significativo.

**Cómo**:
- Editar `INTEGRATION.md`, actualizar `last_updated` en el frontmatter.
- (Opcional) desde `Integracion_Plataformas/` correr `python scripts/sync.py`
  para reflejar el cambio en el hub central.

El sync NO es bloqueante — si te olvidás, otra persona lo corre después y todo
funciona. Pero mantenerlo al día evita que la doc derive del código.
