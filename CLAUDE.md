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
- **Exportar un frame a archivo**: `dashboard/exports.py` (`download_buttons` = par PNG + GeoTIFF, `png_download_button`, `img_to_png_bytes`). Lo usan `live_viewer` (Nacional/Zona) y la grilla de volcán; vivían dentro de `live_viewer` y una vista terminaba importando de otra vista sólo para bajar un archivo. El **PNG lleva timestamp y encuadre sobre-impresos** (el archivo se explica solo meses después); el **GeoTIFF va limpio**, EPSG:4326 — texto encima arruinaría el análisis del píxel. Con radio ajustable, el radio va SIEMPRE en el nombre y en el label (`sufijo_encuadre` / `etiqueta_encuadre` en `modo_guardia_volcan.py`). **VOLCAT no exporta GeoTIFF**: es un PNG compuesto por SSEC, sin array georreferenciado propio. `tests/test_exports_volcan.py`.
- **Leyenda de producto**: toda vista que pinte un producto satelital llama a `dashboard.map_helpers.render_compact_legend(product, symbols=…, tv=…)` — una tira arriba del mapa con los swatches del RGB **y** la simbología que el dashboard dibuja encima (`volcano`, `hotspot`, `hotspot_frp`, `rings`, `wind`). Pasar SÓLO los glifos que esa vista dibuja de verdad. GeoColor y VOLCAT no llevan swatches (color real / barra propia): llevan una nota de `_PRODUCT_NOTES`. `tv=True` sólo en Modo Sala (clase `tv-legend` = overlay). `tests/test_legend_coverage.py` falla si una vista nueva pinta un producto sin leyenda. **Un panel puede apagarla con `show_legend=False`, pero sólo si su llamador pone la suya** — es el caso del slot `tv=volcan`, que dibuja la fila de 3 leyendas como overlay antes del grid; sin el flag la pared mostraba la tira dos veces. Ojo con el límite: `test_legend_coverage` es AST estático y le basta con que la llamada EXISTA en el fuente, aunque en runtime viva bajo un `if` que nunca se cumple. No se puede cerrar sin renderizar Streamlit headless; lo que sí está pineado (`test_apagar_la_leyenda_solo_vale_si_el_llamador_pone_la_suya`) es que quien pasa `show_legend=False` llame a `render_compact_legend` él mismo.
- **Marcador de volcán — HAY TRES CAMINOS DE DIBUJO, los tres huecos**: Plotly `dashboard.style.volcano_marker(level)` · PIL `map_helpers.draw_volcano_marker_pil(draw, cx, cy, size)` · matplotlib `markerfacecolor="none"`. Nunca armarlo a mano. Es hueco a propósito: el glifo se centra en la coordenada, así que relleno tapa justo el píxel del cráter, que es donde aparece la lava. Niveles Plotly: `wide` (país) · `region` · `zone` (mosaico/4 zonas) · `focus` (zoom de un volcán). **El camino PIL es fácil de olvidar** (Modo Sala en modo imagen, GIF de loops, thumbnail de Series componen PNG del lado servidor, no Plotly) y es justo el que se proyecta en la sala — se quedó relleno una versión entera. Los diamantes de hot spot SÍ van rellenos: son el dato, no una referencia. `tests/test_marker_sizes.py` cubre los tres caminos.
- **Grilla de volcán: UNA implementación, un fragment por panel.** `modo_guardia_volcan.volcan_grid(volcan, …)` es la fuente única de la vista "todos los productos de un volcán a la vez" — la usan **tres** llamadores: el sub-tab Volcán del Modo Guardia, el tab 🔬 Volcán de Vista Operacional y el slot `tv=volcan` del Modo Sala. Los paneles y su orden de lectura salen de `GRID_PANELS`. Tres reglas la sostienen: (1) **el compositor NO lleva `@st.fragment`** — Streamlit no permite fragments anidados y los paneles de adentro ya lo son; (2) **ningún panel recibe timestamp ni imagen por argumento**, porque los args de un fragment con `run_every` quedan congelados en el último full-rerun (`live_viewer.py:564-575`) y nunca verían un scan nuevo; (3) **el radio va como parámetro y llega a las CINCO funciones que arman bbox** (`volcan_grid`, `_grid_header`, `_panel_rammb`, `_panel_volcat`, `_capture_button`) — si una queda con la constante, ese panel encuadra distinto y la grilla deja de leerse como una escena. `tests/test_volcan_grid.py` falla si se rompe cualquiera de las tres (verificado por mutación, ago-2026: el test de la regla (3) leía `modo_guardia.py`, que no tiene ni un `RADIUS_DEG`, así que el bucle quedaba vacío y pasaba por construcción).
- **El layout de la grilla lo decide el ENCUADRE, no el gusto** (`_resolve_per_row`): **4 en una fila en fullscreen, 2×2 en modo normal**, y un `per_row` explícito manda (el slot de sala pide 3). La escena es CUADRADA (±radio en lat y lon), así que en 16:9 lo que escasea es el **alto**: apilar dos filas parte justo esa dimensión y deja la imagen en ~245 px de lado con ~700 px de ancho vacío al costado de cada panel; cuatro columnas gastan el ancho, que sobra, y la imagen sube a **465 px de lado — 2.1×**, medido a 1920×1080. En modo normal hay sidebar, el ancho baja y ahí el 2×2 vuelve a ganar (352 contra ~330). El plan original argumentaba el 2×2 al revés («cuatro columnas dejan cada mapa angosto») y estaba equivocado: lo angosto no importa si la altura es el cuello de botella.
- **En fullscreen la grilla se mide sola, y el alto NO se manda con `height`.** Un alto en px no puede "ocupar la ventana": el servidor no sabe si enfrente hay un portátil o la pared de la sala. `_inject_fullscreen_css(filas)` reparte `calc((100vh − cromo)/filas)`, igual que el grid de 4 zonas, con **dos** cromos: la página arrastra tabs y toolbars (primer plot en y≈505), la sala no tiene nada arriba (y=165) y descontarle el de la página le sacaría ~350 px de imagen a la pared. Dos gotchas que costaron una pasada cada uno: (a) **no alcanza con achicar el `stPlotlyChart`** — Streamlit le pone `flex: 0 0 <alto>px` al contenedor con key, y en una columna flex el **flex-basis gana sobre `height`**, así que queda el hueco del alto viejo y la segunda fila sigue bajo el fold; hay que pisar `flex` en el contenedor; (b) el selector va acotado a `st-key-vgrid_*` / `st-key-tvvolcatzoom_*` y nunca a todo `stPlotlyChart`: en Vista Operacional los tabs Nacional y Zona están en el DOM aunque estén ocultos. El `height=` de Python queda sólo como alto inicial, y **una fila (el slot de sala) no es lo mismo que dos**: pasarle el alto de 2 filas le sacó 39% a la pared que se proyecta 24/7.
- **El orden de la grilla y el de la sala son DISTINTOS a propósito.** `GRID_PANELS` va en orden de lectura de emergencia (GeoColor: ¿hay columna? → Ash RGB: ¿es ceniza? → SO₂: ¿es gas fresco? → VOLCAT: ¿qué altura?). `GRID_PANELS_TV` conserva el orden histórico de `PRODUCTS` (Ash primero) porque la pared del Modo Sala se proyecta y la gente de turno ya la tiene interiorizada. Son los MISMOS objetos, no copias. La leyenda de 3 columnas de `modo_guardia.py` se deriva de `GRID_PANELS_TV`: si volviera a ser un literal aparte, rotularía un producto encima de otro (bug atrapado en la revisión ago-2026, antes de llegar a la sala).
- **VOLCAT vacío es el estado NORMAL.** Sólo dibuja cuando detecta ceniza, y sólo Copahue, Calbuco y Planchón-Peteroa tienen sector dedicado (250-500 m) — los otros 40 caen en un regional de 2 km vía `resolve_volcat_sector`. Todo panel VOLCAT tiene que decir qué sector usa y que la ausencia de dibujo no es una falla. El rótulo sale de `etiqueta_sector_volcat`, que deriva la resolución del NOMBRE del sector: con un literal "2 km" clavado, `Argentina_5_km` mentía.
- **El hi-res de GeoColor sólo cubre ~0.5° de radio.** `fetch_volcan_product` cae a RAMMB si la vista pide más (`r_view <= r`). Sin ese guard, `_crop_centered` clampea la fracción a 1.0 y devuelve la imagen de 0.5° entera, que el llamador pinta sobre el bbox pedido: a radio 2° la pluma quedaría dibujada a 4× de donde está. Es una mentira de georreferencia, no un problema de estética.
- **Altura de pluma propia: cara, va disparada por condición.** Medido ago-2026 contra S3 con caché frío: ~78 MB y ~90 s por escena (C11+C14+C15), más GFS y ACHA. No va en un panel con `run_every`. Cuando entre a la grilla, el disparador es `_ash_red_fraction_v2` (`src/fetch/timeseries.py:63`) sobre el Ash RGB que el panel vecino ya tiene en memoria. Ese uso como **gatillo** no contradice la regla de "no inventar métricas de color": un falso positivo por cirros cuesta una descarga, no un número equivocado en pantalla. No convertirlo nunca en un "% de ceniza" mostrado.
- **Adquisición de escena única (SDA)**: los 3 retrievals de altura (wen_rose / bt_matching / acha) NO bajan bandas por su cuenta — llaman a `acquire_ash_scene()` en `src/process/scene.py`, que devuelve `AshScene` o un dict de error listo para retornar. **Todo guard de "no reportar" (banda ausente, bbox fuera del disco, bandas de scans distintos, sin perfil GFS) va ahí y en ningún otro lado**: estaba triplicado y por eso ninguna copia tenía test. Tests en `tests/test_scene.py`, escena sintética compartida en `tests/conftest.py`.

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
