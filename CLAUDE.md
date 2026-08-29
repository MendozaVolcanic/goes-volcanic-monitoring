# GOES Volcanic Monitoring Dashboard

> ⚖️ **Este proyecto es un SDA en producción bajo Resolución CPLT N°372**: al crear
> o editar código que clasifique/prediga/decida, aplicar la convención de la
> `GUIA_MAESTRA_TRANSPARENCIA_ALGORITMICA.md` (cabecera "FICHA SDA" Nivel 1 +
> comentarios qué+por qué) y mantener `docs/FICHA_SDA_GOES.md` al día (mismo
> commit que el cambio de lógica).

## Qué es este proyecto
Dashboard NRT de monitoreo volcánico para Chile usando GOES-19 (GOES-East).
Genera Ash RGB, detección de ceniza (BTD split-window), indicador SO2, y visualiza
hot spots y color real para 43 volcanes chilenos. **Licencia Apache-2.0** (código
libre); registro pre-paper en `docs/paper/REGISTRO_PAPER.md`.

## Stack técnico
- **Datos**: AWS S3 `noaa-goes19` (sin credenciales)
- **Procesamiento**: xarray + numpy (conversión Planck, BTD, Ash RGB)
- **Dashboard**: Streamlit + Plotly (el frontend es Plotly puro + PNG; Folium se
  quitó del stack en el audit ago-2026 — no había un solo import)
- **Automatización**: GitHub Actions

## Productos volcánicos
- **Ash RGB**: Composite B15-B14, B14-B11, B13 (receta RAMMB/CIRA)
- **BTD Split-Window**: BT(11.2um) - BT(12.3um). Negativo = ceniza
- **Detección tri-espectral**: BTD + (BT8.4-BT11.2)+(BT12.3-BT11.2) < 0
- **SO2 indicator**: BT(8.4um) - BT(11.2um). Muy negativo = SO2
- **Hot spots**: Producto FDCF L2 (NOAA pre-procesado) — NRT vía `fetch_latest_hotspots`, histórico vía `fetch_hotspots_at_time(dt, bounds)` (S3 NOAA L2 indefinido). Ambos comparten `goes_fdcf.extract_hotspots`, que con `bounds` recorta el grid ABI al sub-bloque (~15× más rápido, sin el pico de RAM del full-disk); `frp_timeline.fetch_scan_sliced` quedó como alias con default `CHILE_BBOX`.
- **VOLCAT**: Producto SSEC con altura de pluma cuantitativa — vía RealEarth API (`fetch_image(time=...)` acepta histórico).
- **GeoColor hi-res NOAA L1b**: 0.5 km/px banda 2 (4× zoom vs RAMMB). Pipeline `src/process/hires_pipeline.py` con day/night switch (visible diurno + IR pseudo-color nocturno). Modos `color` (1km/px aligned) y `mono_05km` (0.5km/px nativo sepia).

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
- **Leyenda de producto**: toda vista que pinte un producto satelital llama a `dashboard.map_helpers.render_compact_legend(product, symbols=…, tv=…)` — una tira arriba del mapa con los swatches del RGB **y** la simbología que el dashboard dibuja encima (`volcano`, `hotspot`, `hotspot_frp`, `rings`, `wind`). Pasar SÓLO los glifos que esa vista dibuja de verdad. GeoColor y VOLCAT no llevan swatches (color real / barra propia): llevan una nota de `_PRODUCT_NOTES`. `tv=True` sólo en Modo Sala (clase `tv-legend` = overlay). `tests/test_legend_coverage.py` falla si una vista nueva pinta un producto sin leyenda.
- **Marcador de volcán — HAY TRES CAMINOS DE DIBUJO, los tres huecos**: Plotly `dashboard.style.volcano_marker(level)` · PIL `map_helpers.draw_volcano_marker_pil(draw, cx, cy, size)` · matplotlib `markerfacecolor="none"`. Nunca armarlo a mano. Es hueco a propósito: el glifo se centra en la coordenada, así que relleno tapa justo el píxel del cráter, que es donde aparece la lava. Niveles Plotly: `wide` (país) · `region` · `zone` (mosaico/4 zonas) · `focus` (zoom de un volcán). **El camino PIL es fácil de olvidar** (Modo Sala en modo imagen, GIF de loops, thumbnail de Series componen PNG del lado servidor, no Plotly) y es justo el que se proyecta en la sala — se quedó relleno una versión entera. Los diamantes de hot spot SÍ van rellenos: son el dato, no una referencia. `tests/test_marker_sizes.py` cubre los tres caminos.
- **Hueco ≠ `-open`: el hueco tiene que MEDIR algo.** Plotly dibuja `triangle-up` con alto `0.75·size`, así que el alto útil es `0.75·size − 2·trazo`; por debajo de ~2 px el antialiasing lo cierra y el glifo vuelve a leerse RELLENO aunque el SVG diga `fill: none`. Fue el bug de la 3ª pasada (ago-2026): `wide` valía 3 con trazo 0.7 → 0.85 px, y Ash RGB / Live / RAMMB se veían con punto sólido mientras VOLCAT (`focus`/`zone`) se veía bien. **Regla para cualquier nivel nuevo: `0.75·size − 2·trazo >= VOLCANO_HOLE_MIN_PX` (2.0)**, pineada en `test_el_hueco_es_visible_en_pantalla`. Lo que importa es el CENTRO, no el área total: la anomalía nace en el cráter y el glifo se centra ahí, así que conviene un triángulo más grande con lo opaco en el borde antes que uno chico y macizo encima del vent.
- **Adquisición de escena única (SDA)**: los 3 retrievals de altura (wen_rose / bt_matching / acha) NO bajan bandas por su cuenta — llaman a `acquire_ash_scene()` en `src/process/scene.py`, que devuelve `AshScene` o un dict de error listo para retornar. **Todo guard de "no reportar" (banda ausente, bbox fuera del disco, bandas de scans distintos, sin perfil GFS) va ahí y en ningún otro lado**: estaba triplicado y por eso ninguna copia tenía test. Tests en `tests/test_scene.py`, escena sintética compartida en `tests/conftest.py`.
- **Releases rolling = snapshot completo, con dos reglas**: todo workflow que publique vía `.github/actions/gh-release-snapshot` reemplaza el contenido entero del tag. (1) **Un tag, un grupo de concurrency**, compartido por TODOS sus escritores — si un manual y un cron escriben el mismo tag con grupos distintos, el manual borra lo que el cron llevaba acumulado (le pasó a `hires-loop-rolling`: se perdía la ventana rodante de 8 h y tardaba otras 8 h en rehacerse). (2) La acción **sube con `--clobber` primero y poda huérfanos después**, nunca al revés: entre borrar y terminar de subir en batches pasan minutos en que el dashboard ve el release vacío. (3) **todo publicador declara grupo, incluso con tag dinámico** — `backfill_build` arma su tag con los inputs del run, así que dos runs sólo chocan si alguien pide el mismo evento dos veces, pero cuando chocan se borran los assets igual. `tests/test_workflow_concurrency.py` falla si se rompe cualquiera de las tres.

## Gotchas conocidos
- **Python version pin en Streamlit Cloud — `runtime.txt` YA NO ALCANZA** (lección 2026-05-14): Desde que Streamlit Cloud migró a `uv` para instalar deps, **`runtime.txt` es ignorado en muchos deploys**. La doc oficial dice que la ÚNICA forma soportada es el UI Advanced Settings al momento del deploy (https://docs.streamlit.io/deploy/streamlit-community-cloud/manage-your-app/upgrade-python). Para cambiar versión hay que **borrar y re-deployar** la app. El log del 14-may confirma `Using Python 3.14.4 environment` aunque teníamos `runtime.txt` con `python-3.12`. Workaround triple (lo tenemos): `runtime.txt` + `.python-version` (pyenv format) + `pyproject.toml` con `requires-python="==3.12.*"`. Aún así, lo MÁS seguro es elegir Python 3.12 en el UI del Advanced Settings al primer deploy y nunca cambiar.
- **Python 3.14 es problemático con Streamlit**: el importlib de 3.14 tiene race condition en `_load_unlocked` que dispara `KeyError` intermitentes durante hot-reloads. Después de horas de acumulación, la app entra en estado dormant/auth-required y solo se reactiva con click manual del owner en `share.streamlit.io/-/manage`.
- **Imports cross-package top-level desde `dashboard/views/` son FRÁGILES en Streamlit Cloud**: cualquier `from dashboard.X import Y` o `from src.X import Y` top-level puede fallar durante hot-reload (no solo con Python 3.14). Patrón seguro: **lazy import dentro de la función** que lo usa, o **`try/except ImportError` con fallback hardcoded** para constantes. Aplicado en los 8 archivos refactor del 2026-05-09.
- **App dormant / HTTP 303 a auth no es bug, es sleep mode**: Streamlit Cloud free duerme apps sin tráfico ~12h. El endpoint sirve un shell HTML estático con redirect 303 a `share.streamlit.io/-/auth/app?redirect_uri=...`. `curl` NO la despierta (solo baja el shell). Se necesita browser real con JS+WebSocket que pulse "Yes, get this app back up!". Mitigación: workflow `keepalive_streamlit.yml` con Playwright cada 8h.
- **Plotly scaleratio en lat/lon**: con `scaleratio=1` los círculos geográficos se ven como óvalos. Usar `scaleratio = 1/cos(lat)` para 1 km vertical = 1 km horizontal visual.
- **Título Plotly largo achica el plot**: wrappea a 2 líneas si pasa de ~30 chars. Usar `title=""` y poner el label en `st.markdown` arriba del plot.
- **Calbuco 2015 NO sirve para test de plataforma**: RAMMB no archiva GOES-13. Usar eventos recientes (Sangay, Reventador, Sabancaya) del archive GOES-19 ~28 días.

## Comandos comunes
- `python -m pytest tests/ -q` — física round-trip (Planck, Wen-Rose, β, viento), geo, FRP rollup
- Workflow `goes.yml`: **cron DESACTIVADO desde 2026-05-15** (fallaba con "workflow
  file issue" y nadie consume `STATUS_NRT.md`); queda `workflow_dispatch` manual.
  Si se reactiva: escribe `STATUS_NRT.md`, NUNCA `STATUS.md` (curado por humanos)
- Workflow `frp_timeline.yml` corre **cada 10 min**, regenera `data/frp_timeline.json`
  (pulso intradía de FRP + roll-up diario para el Heatmap — FUENTE ÚNICA, reemplazó
  al viejo `hotspots_daily.yml` que tenía el bug de "conteo de 1 solo scan", jun 2026)
- Workflow `lascar_pdf.yml`: **manual** (`workflow_dispatch`), genera PDF en `reports/lascar/`

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
