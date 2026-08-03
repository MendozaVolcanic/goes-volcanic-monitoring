# AUDIT REPORT — agosto 2026 (3ª auditoría multi-agente)
> Generado por un workflow de 6 finders paralelos + verificación adversarial de los
> bugs med/high. **La ola 1 ya está desplegada** (PR #16, commit 8356ae8, 211 tests,
> HF RUNNING) — los ítems marcados ✅ están arreglados; el resto es el backlog de la
> ola 2. Prioridades y contexto en la memoria `project_pending_ola2`.
>
> **Ola 2 en curso** (ago-2026): hechos los dos ítems estructurales de mayor
> valor — el preámbulo de adquisición triplicado (ahora `src/process/scene.py`)
> y el recorte por bbox del FDCF (`goes_fdcf.extract_hotspots`, compartido por
> los 3 lectores). 231 tests (+19).

**96 hallazgos únicos** — 33 bugs, 63 mejoras.

Veredictos adversariales de la ronda: 3 CONFIRMED (Calbuco sin precalentar, CSS 100vh, hires 2-tupla), 1 PLAUSIBLE (datum del parallax), 1 REFUTED (bloqueo serial de las 4 zonas VOLCAT — ya neutralizado por el hilo productor; la refutación reveló que el hueco real estaba en el sub-tab interactivo).

## Bugs

### ✅ `dashboard/views/heatmap_actividad.py:36` — high/conf=high · cicd-arquitectura

**El cron frp_timeline.yml commitea data/frp_timeline.json a main cada 10 min, pero el dashboard deployado en HF lee SOLO el archivo local congelado en el snapshot del deploy — producción nunca ve las actualizaciones del bot**

heatmap_actividad.py:36 define FRP_TIMELINE_PATH como ruta local (Path(__file__)...) y _load_frp_timeline (líneas 80-88) solo lee disco; no existe ningún fetch remoto del JSON en todo el repo (grep de raw.githubusercontent/api.github.com en *.py = 0 matches; los caches hires/animation SÍ se bajan de releases, src/fetch/hires_loop_cache.py:24). deploy_hf.sh:76 incluye data/frp_timeline.json en el orphan branch, o sea el Space sirve el JSON del momento del deploy manual. Mientras tanto frp_timeline.yml (cron */10, verificado vivo en el remote: último commit bot 2026-08-02T11:52Z) quema Actions produciendo datos que ningún consumidor deployado lee. Escenario de fallo: semanas sin redeploy → la vista 'Pulso térmico intradía — GOES cada ~10 min' muestra una ventana de 48h vieja; con actividad nueva real, el panel puede decir 'Calma térmica: 0 MW en las últimas ~48 h' (heatmap_actividad.py:188-194) basado en datos congelados — número silenciosamente incorrecto en un SDA de alerta. El caption con last_updated_utc (línea 196) es el único indicio y no hay guard de staleness.

*Fix sugerido:* Que _load_frp_timeline haga fetch del JSON desde el repo GitHub (raw main o un release rolling, patrón ya usado en hires_loop_cache) con fallback al archivo local, y agregar guard: si last_updated_utc > N horas, st.warning de dato vencido en vez de 'Calma térmica'.

### ✅ `src/fetch/goes_s3.py:129` — high/conf=medium · degradacion-silenciosa

**Los 5 call-sites de granule_select seleccionan sobre un listado S3 CACHEADO sin expiración: en el dashboard NRT el "scan más reciente" puede congelarse hasta ~1 h sin ningún aviso.**

Verificado en el entorno real (s3fs 2026.3.0 / fsspec 2026.3.0): (a) `s3fs.S3FileSystem(anon=True)` es cacheable — dos construcciones devuelven la MISMA instancia (`a is b` → True), así que goes_s3, goes_fdcf, goes_acha, goes_lvtp y frp_timeline comparten un único `dircache`; (b) `S3FileSystem._lsdir` sólo consulta S3 si `path not in self.dircache`, y el `DirCache` se crea con `listings_expiry_time=None` (sin expiración). Consecuencia: la PRIMERA vez que se lista la carpeta de la hora en curso (`.../YYYY/DDD/HH/`) el resultado queda congelado para todo el proceso. `nearest_granule_key` (granule_select.py:60) elige el mínimo |Δt| sobre ese conjunto congelado, de modo que devuelve siempre el mismo gránulo hasta que el reloj cruza a la hora siguiente. Sólo los listados VACÍOS no se cachean (`if delimiter and files ...`), por lo que el modo de falla se dispara justo cuando ya hay al menos un gránulo en la hora — el caso normal. Blast radius verificado: dashboard/views/volcat_viewer.py:774 llama `wen_rose_top_height(datetime.now(utc), ...)` desde un `@st.cache_data(ttl=TTL_VOLCAT)` cuyo `bucket` de 10 min invalida el cache de Streamlit — o sea, el panel re-consulta cada 10 min y recibe el MISMO scan viejo, presentando una altura de pluma de hasta 55 min de antigüedad como si fuera actual. Igual afecta a `fetch_latest_acha_height` (goes_acha.py:287), `fetch_latest_lvtp_profile` (goes_lvtp.py:324) y a `goes_fdcf._list_recent_files` (goes_fdcf.py:136, usado por modo_guardia/modo_evento/live_viewer). En GitHub Actions (proceso efímero) no se ve; en el deploy Streamlit/HF de larga vida sí. Para un SDA que apoya decisiones de alerta, un dato viejo presentado como vigente es exactamente el fallo peor-que-crash.

*Fix sugerido:* Refrescar el listado de la hora objetivo: `fs.ls(path, refresh=True)` en `goes_s3.list_files` y en `_list_files_at_hour` / `_list_lvtp_files` / `_list_recent_files` (o al menos para la carpeta que contiene `dt` cuando `dt` está a menos de ~2 h de `now`). Alternativa más limpia y global: construir el filesystem con `s3fs.S3FileSystem(anon=True, listings_expiry_time=60)` en un único helper compartido, para que el dircache caduque a los 60 s. Agregar un test que llame dos veces al lister con un objeto nuevo entre medio y verifique que la segunda llamada lo ve.

### ✅ `INTEGRATION.md:8` — medium/conf=high · doc-drift

**INTEGRATION.md declara deploy_url=goesvolcanic.streamlit.app y Stack 'Deploy: Streamlit Community Cloud + GitHub Actions' — el deploy es HF Spaces desde jun-2026**

INTEGRATION.md:8 (frontmatter deploy_url) y :31 (Stack). Este archivo es la ficha que consumen los otros proyectos del ecosistema (sync a Integracion_Plataformas), así que el drift se propaga: cualquier integración que use deploy_url apunta a una app dormida de Streamlit Cloud en vez de https://mendozavolcanic-goes-volcanic-monitoring.hf.space (keepalive_hf.yml:21). Frontmatter last_updated=2026-07-03 quedó un mes atrás de cambios mayores (PR #15 con vistas nuevas).

*Fix sugerido:* deploy_url → URL del HF Space; Stack → 'Deploy: Hugging Face Spaces (Docker) + GitHub Actions'; actualizar last_updated/last_commit.

### ✅ `INTEGRATION.md:84` — medium/conf=high · doc-drift

**La sección 'Vistas del dashboard' de INTEGRATION.md lista 8 vistas que ya no existen con esos nombres; la app real tiene 11 páginas distintas**

INTEGRATION.md:84-97 lista: 'En Vivo', 'Mapa General', 'Ash RGB Viewer', 'Detalle Volcán', 'VOLCAT (SSEC)', 'Animación (RAMMB)', 'Series de tiempo', 'Backfill histórico'. dashboard/app.py:138-145 (PAGE_OPTIONS) tiene: Vista Operacional, Modo Guardia, Comparador, Modo Evento, Heatmap actividad, Replay reciente, Backfill historico, Ash + BTD, VOLCAT, Loops descargables, Series de tiempo. 'Mapa General', 'Ash RGB Viewer' y 'Detalle Volcán' no existen como páginas; los slugs viejos 'live'/'zonas'/'animacion' son redirects de compatibilidad (app.py:160-163), confirmando el renombre. Faltan por documentar Modo Guardia, Modo Evento, Comparador, Heatmap y Replay — vistas que otros proyectos podrían querer enlazar por permalink ?vista=.

*Fix sugerido:* Reescribir la sección con las 11 páginas actuales y sus slugs de permalink (operacional, guardia, comparador, evento, heatmap, replay, backfill, ash, volcat, loops, series).

### ✅ `README.md:50` — medium/conf=high · doc-drift

**URL de clone del README apunta a una org equivocada: github.com/nmendozam/goes-volcanic-monitoring, cuando el repo real es MendozaVolcanic/goes-volcanic-monitoring**

README.md:50 dice `git clone https://github.com/nmendozam/goes-volcanic-monitoring.git`. El remote real es https://github.com/MendozaVolcanic/goes-volcanic-monitoring.git (git remote -v; también INTEGRATION.md:9 y REGISTRO_PAPER.md:136 usan MendozaVolcanic). Cualquiera que siga la sección Instalación obtiene 404 (o clona un repo ajeno si esa cuenta existiera) — doc que engaña activamente en la instrucción de reproducibilidad que el REGISTRO_PAPER (§6) declara como parte de la contribución.

*Fix sugerido:* Cambiar a https://github.com/MendozaVolcanic/goes-volcanic-monitoring.git

### ✅ `README.md:21` — medium/conf=high · doc-drift

**README promociona Streamlit Cloud como deploy activo ('dos hosts para redundancia', badge primero) cuando el deploy es SOLO Hugging Face desde jun-2026**

README.md:14 (badge Streamlit primero), 21-26 ('Demos públicas (mismo código, dos hosts para redundancia)... Si una está caída, usar la otra'), 79-82 y 116-121 (sección 'alternativa a Streamlit Cloud'). Contradice keepalive_hf.yml:3-7 ('el deploy es SOLO Hugging Face desde jun-2026' — el keepalive de Streamlit fue eliminado como zombie en el audit W2) y la memoria del proyecto (Streamlit Cloud deprecado). Un usuario OVDAS que siga el primer link llega a una app dormida/muerta y concluye que el monitoreo está caído. deploy_hf.sh:2 arrastra el mismo drift ('mirror de Streamlit Cloud') invertido: hoy HF es el primario, no el mirror.

*Fix sugerido:* Quitar el badge y los links a goesvolcanic.streamlit.app (o marcarlos como deprecado histórico), dejar HF Spaces como único deploy oficial, y actualizar el comentario de deploy_hf.sh:2.

### ✅ `dashboard/views/modo_guardia.py:796` — medium/conf=medium · layout-css

**El CSS del TV fuerza cada stPlotlyChart a 100vh: anula el cell_h de la fila de 5 VOLCAT y produce overflow vertical (scrollbar en pantalla 24/7)**

En tv=zonas el CSS (modo_guardia.py:793-798) aplica height: calc(100vh - 6px) !important a TODO [data-testid=stPlotlyChart] y su iframe. _render_volcat_zoom_row_tv calcula cell_h = max(320, int(height*0.62)) ~558px con el comentario 'fila mas baja que un slot fullscreen para que entren los N' (zonas_fullscreen.py:662), pero el !important del CSS pisa la altura python: los 5 charts quedan a ~100vh. Ademas cada columna agrega el div del nombre del volcan EN FLUJO (~25px, lineas 665-669; no usa la clase .tv-legend que se saca del flujo como overlay), asi que la altura total de cada columna supera el viewport -> aparece scrollbar y el borde inferior queda cortado en una pantalla de sala que nadie scrollea. Efecto visual adicional: con columnas de ~19vw de ancho y scaleanchor+constrain=domain, el mapa util ocupa ~470px centrados verticalmente en una columna negra de ~1070px, y los colorbars verticales (anclados a paper con sizey=0.94, zonas_fullscreen.py:424-432) sobresalen ~300px por encima y debajo del mapa flotando en el vacio. La intencion declarada del cell_h esta silenciosamente derrotada.

*Fix sugerido:* Excluir la fila volcat_row del override 100vh (ej. envolver el slot en un contenedor con clase propia y usar :has() para limitar el selector de 100vh a los slots de chart unico), o anclar los colorbars al dominio de datos y aceptar 100vh. Mover el div del nombre del volcan a un overlay (clase tv-legend) o dentro de la figura como annotation para eliminar el overflow.

### ✅ `dashboard/views/zonas_fullscreen.py:1135` — medium/conf=high · concurrencia-productor-consumidor

**El productor TV no calienta el sector dedicado Calbuco_1_km que usa el slot nuevo volcat_row: la celda Calbuco hace red sincrónica dentro del fragment de la sala 24/7**

El hilo productor (_produce_once, lineas 1131-1148) solo calienta _volcat_latest_cached/_volcat_map_only para los sectores de _volcat_zone_specs() (Chile_North/Central/South_2_km). El slot volcat_row (_render_volcat_zoom_row_tv -> _render_volcat_zoom_tv, lineas 650-670 y 601-647) resuelve sector por volcan via resolve_volcat_sector: Villarrica/Chillan/Puyehue/Llaima caen en Chile_Central_2_km (caliente), pero Calbuco resuelve a Calbuco_1_km (src/fetch/volcat_api.py:30 y 181-183), sector que el productor NUNCA toca. Escenario concreto: cada vez que expira _volcat_latest_cached (TTL 300s) o llega un frame nuevo (~10 min, image_url nueva), el render del slot volcat_row ejecuta EN EL FOREGROUND del fragment: API get_list (timeout 20s) + descarga imagen+latlon en _volcat_map_only_cached (timeout 30s c/u) + descarga COMPLETA de la misma imagen otra vez para el colorbar (_volcat_image_bytes, timeout 30s) — todo serial dentro de la ventana de 12s del slot. Tipico 3-8s de bloqueo por ciclo; peor caso con SSEC lento ~80s congelando la rotacion (el clamp +1 evita saltos pero la pantalla previa queda congelada, que es exactamente el sintoma 'queda mucho tiempo en la misma escena' que el patron productor-consumidor vino a resolver). Ademas el docstring de _render_volcat_zoom_tv (lineas 604-606) sigue afirmando 'Sirve plotly desde el cache que mantiene caliente el productor (ambos resuelven a Chile_Central -> un solo frame)' — era cierto con 2 volcanes (jun-2026), es falso desde que el PR agrego Calbuco.

*Fix sugerido:* En _produce_once, ademas del loop sobre _volcat_zone_specs(), iterar sobre {resolve_volcat_sector(get_volcano(n)) for n in zooms} y calentar _volcat_latest_cached + _volcat_map_only + _volcat_colorbar_strip para cada sector unico resultante. Actualizar el docstring de _render_volcat_zoom_tv.

### ✅ `dashboard/views/zonas_fullscreen.py:516` — medium/conf=medium · bloqueo-fragment-cold-start

**El slot volcat_zonas compone las 4 zonas serialmente en el fragment: tras un restart con cache frio puede bloquear minutos (antes el peor caso era 1 zona por slot)**

El PR cambio de 'una zona VOLCAT por slot' a 'las 4 zonas en un slot' (_render_volcat_zonas_tv, lineas 504-519), pero el render sigue siendo foreground: 4 llamadas seriales a _render_volcat_zone_cell, cada una con _volcat_latest_cached (API, timeout 20s) + _volcat_map_only (2 descargas, timeout 30s c/u) + reproyeccion. Escenario: tras un restart del servidor, el productor calienta primero los RGB (linea 1126: geocolor/jma_so2, que con cache frio tardan ~10-30s) y recien despues VOLCAT; si la rotacion cae en volcat_zonas (o volcat_row) en los primeros ~60s, el fragment bloquea con 3 sectores unicos x (20s API + 30s descargas) en el peor caso de SSEC caido — varios minutos de pantalla congelada en una sala sin supervision, cuando antes del PR el peor caso por slot era un solo sector. El clamp de indice evita saltar slots pero no evita el congelamiento. Los slots volcat_zonas/volcat_row son los UNICOS de la rotacion que no tienen entrada en _TV_PRODUCED (solo existen claves 'rgb:*' y 'volcan:*').

*Fix sugerido:* Paralelizar los fetches de las 4 zonas con ThreadPoolExecutor ANTES de abrir las columnas (mismo patron que _compose_4_zonas_png linea 1400), o mejor: producir tambien estos slots en background y que el fragment solo lea (mostrar _tv_placeholder si aun no estan, como hacen los slots rgb/volcan).

### `src/fetch/gfs_archive.py:262` — medium/conf=medium · aritmetica-de-indices

**`dict(zip(got, vals))` desalinea silenciosamente valores y (var, nivel) si eccodes decodifica una cantidad de mensajes distinta de los registros pedidos.**

`_collect_raw` devuelve `got` (claves en orden de pedido) y `raw` (mensajes GRIB2 concatenados en ese mismo orden); `_decode_values_at_point` devuelve `vals` en orden de archivo. La correspondencia se asume 1:1 y se materializa con `vmap = dict(zip(got, vals))` (gfs_archive.py:262 para T(z) y :320 para viento). `zip` TRUNCA en silencio: si un byte-range devuelve datos truncados/corruptos —o, al revés, contiene más de un mensaje— todo lo posterior se corre un lugar y la temperatura de 500 hPa se asigna a 400 hPa, el HGT de un nivel al de otro, etc. El perfil resultante pasa las validaciones existentes (`150 < T_K < 330`, `len(levels) >= 3`, orden por z), o sea que sale un T(z) plausible pero incorrecto → altura de pluma incorrecta en la validación histórica, sin ningún error. Verifiqué contra el `.idx` real (gfs.20260731/00/atmos/gfs.t00z.pgrb2.0p25.f000.idx, 696 registros): offsets ascendentes, sin duplicados (var, nivel), todos los niveles de GFS_LEVELS_HPA presentes y `TMP:surface` presente — o sea que el parseo es correcto hoy; el problema es que no hay ninguna red de contención si el supuesto se rompe (range parcial, .idx desincronizado del GRIB tras un re-post de NCEP).

*Fix sugerido:* Antes del `zip`, verificar `if len(vals) != len(got): logger.error(...); return None`. Mejor aún, hacer que `_decode_values_at_point` devuelva `(shortName, level, valor)` leyendo `eccodes.codes_get(gid, 'shortName')` y `'level'`, y construir `vmap` por coincidencia explícita en vez de por posición. Test con un `raw` sintético de N-1 mensajes para N claves pedidas → debe devolver None, no un perfil corrido.

### `src/fetch/gfs_archive.py:113` — medium/conf=low · aritmetica-de-indices

**`_grid_index` no valida rango ni el modo de barrido del mensaje GRIB: un índice negativo se indexa hacia atrás en numpy y devuelve el valor de otro punto del planeta.**

`_grid_index` calcula `j = round((lat0 - tlat) / dy)` y devuelve `int(j * ni + i)` sin comprobar `0 <= j < nj` ni `0 <= idx < vals.size` (gfs_archive.py:111-113). El resultado se usa directamente como `vals[_grid_index(...)]` en `_decode_values_at_point` (gfs_archive.py:196-197). El helper hardcodea el barrido norte→sur que hoy usa GFS 0.25° (lat0 = 90, jScansNegatively), supuesto correcto para `pgrb2.0p25.f000` pero NO leído del mensaje: `scanningMode`/`jScansPositively` se ignoran. Si NCEP publicara un mensaje con barrido sur→norte (lat0 = -90), para Láscar (-23.37) daría j = round((-90+23.37)/0.25) = -267 → índice plano negativo → numpy indexa desde el final del array y devuelve la temperatura de un punto arbitrario del hemisferio opuesto, sin excepción ni warning. Igual pasaría si `tlat` llegara fuera de [-90, 90] por un bug aguas arriba. Los tests (tests/test_gfs_archive.py:83-101) sólo ejercitan el caso nominal y el wrap de longitud. Probabilidad baja hoy, consecuencia máxima (perfil T(z) de otro lugar → altura de pluma inventada) y coste de la guarda casi nulo.

*Fix sugerido:* Leer `jScansPositively` (o `scanningMode`) con eccodes y calcular `j` según el signo; y en `_decode_values_at_point`, validar `if not (0 <= idx < vals.size): raise ValueError(...)` antes de `vals[idx]` (o hacer que `_grid_index` acepte `nj` y devuelva None fuera de rango). Test: `_grid_index(-90.0, 0.0, 0.25, 0.25, 1440, -23.37, -67.73)` no debe devolver un índice negativo silencioso.

### `src/fetch/goes_s3.py:188` — medium/conf=high · contrato-entre-modulos

**`download_band_at` documenta `-> Path | None` pero PROPAGA cualquier error S3 que no sea FileNotFoundError; sus call-sites en la cadena de altura no lo envuelven.**

`list_files` (goes_s3.py:128-132) sólo atrapa `FileNotFoundError`; `_retry_s3` re-lanza la última excepción transitoria tras agotar los 4 intentos (goes_s3.py:65), y `_download_cached` hace lo mismo con `.get` (goes_s3.py:107). Así, un `EndpointConnectionError`/`ReadTimeout`/503 SlowDown sostenido sale como excepción desde `download_band_at`, no como `None`. Los consumidores llaman fuera de try/except y sólo chequean `is None`: src/process/wen_rose_height.py:438 (`p14 = download_band_at(dt, BT11_BAND)` seguido de `if p14 is None`), src/process/wind_shear_height.py:157 y :181, src/process/bt_matching_height.py:98. Y `wen_rose_top_height` se invoca desde el dashboard en dashboard/views/volcat_viewer.py:774, donde el `try/except` sólo cubre el IMPORT (líneas 769-773), no la llamada. Resultado: una caída transitoria de S3 rompe el render de la vista con traceback en vez de degradar a la tarjeta `{'status': 'no_data'}` que toda la función promete devolver. La adición de `_retry_s3` empeora la ilusión: da la impresión de que el path de red ya está manejado cuando el error sigue escapando.

*Fix sugerido:* En `list_files` y `_download_cached`, atrapar `Exception` tras agotar los reintentos y devolver `[]` / `None` con log de error (dejando `FileNotFoundError` como hoy), de modo que `download_band_at` cumpla su firma `Path | None`. O, si se prefiere que el error suba, envolver las llamadas en `wen_rose_height.py:438`, `wind_shear_height.py:157/181` y `bt_matching_height.py:98` para devolver el dict `no_data` con `reason='S3 no disponible'`. Test: monkeypatchear `_get_fs` con un fs que lanza `ConnectionError` y afirmar que `download_band_at` devuelve None.

### `src/fetch/goes_s3.py:56` — medium/conf=high · semantica-de-retry

**`_retry_s3` reintenta 4 veces SIN backoff ni jitter: los 4 intentos se consumen en milisegundos y no sobreviven a un corte transitorio real.**

El bucle `for attempt in range(_S3_RETRIES): try: return fn(...) except Exception: ...` (goes_s3.py:56-65) no tiene `time.sleep` en ninguna rama. La docstring y el comentario de diseño (goes_s3.py:40-44) justifican el retry por 'EndpointConnectionError, read timeout' — fallos que típicamente tardan segundos en resolverse. Con reintento inmediato, los 4 intentos se agotan dentro de la misma ventana de falla (los errores de conexión fallan rápido, sin esperar al timeout de socket) y el retry sólo enmascara un blip de microsegundos. Peor: contra un 503 SlowDown de S3 (throttling), 4 requests inmediatos empeoran el throttle en vez de aliviarlo — el patrón obligatorio de AWS es backoff exponencial. El mismo defecto está en `gfs_archive._read_range` (src/fetch/gfs_archive.py:138-145), que bajará decenas de MB por byte-range y es aún más expuesto. El test tests/test_s3_retry.py sólo pinea el conteo de llamadas, nunca el espaciado, así que el contrato temporal no está cubierto.

*Fix sugerido:* Agregar backoff exponencial con jitter entre intentos: `if attempt < _S3_RETRIES - 1: time.sleep(min(8.0, 0.5 * 2**attempt) * (0.5 + random.random()))`. Aplicar lo mismo en `gfs_archive._read_range`. Añadir un test que monkeypatchee `time.sleep` y verifique que se llamó `_S3_RETRIES - 1` veces con duraciones crecientes.

### `src/fetch/granule_select.py:71` — medium/conf=high · validacion-de-datos

**`nearest_granule_key` no tiene tope de |Δt|: ante un hueco de datos NOAA devuelve un gránulo de hasta ~60 min de distancia como si fuera el scan de `dt`.**

El helper devuelve `min(keys, key=_delta)` sin comparar `_delta(best)` contra ninguna tolerancia (granule_select.py:71-73); el único filtro es `inf` (key inparseable). Como se listan tres carpetas horarias, el gránulo elegido puede estar a casi 60 min de `dt` (y, entre extremos, el conjunto candidato abarca ~2 h). El patrón viejo (hora de `dt` + previa como fallback) tenía el mismo agujero, así que no es una regresión, pero el helper era el lugar natural para cerrarlo y no lo hace. Impacto por call-site: en `download_band_at` (goes_s3.py:184) la cadena Wen-Rose / BT-matching / wind-shear pide bandas 'en dt' y recibe un scan de otra decena de minutos — el guard de mismo-scan sigue valiendo (las 3 bandas se piden contra `ref = _scan_start(p14)`), así que el número es físicamente consistente, pero está fechado en otro instante que el pedido; en `wind_shear_top_height` eso además altera el `prev_gap_min` efectivo entre los dos scans usados para la advección. Los tests de tests/test_granule_select.py cubren los bordes de hora pero ninguno cubre el caso 'no hay nada cerca' — sólo `test_no_granules_returns_none`, que es 'no hay NADA'.

*Fix sugerido:* Agregar un parámetro `max_gap_s: float | None = None` (p.ej. 900 s, ~1.5 scans de RadF) y devolver `None` si `_delta(best) > max_gap_s`; o al menos devolver `(key, delta_s)` para que cada call-site decida. Pasar el tope explícito desde `download_band_at`, `fetch_hotspots_at_time`, `fetch_acha_height_at` y `fetch_lvtp_profile`. Test nuevo: gránulos sólo a 45 min de `dt` → None (o rechazo) con el tope puesto.

### `src/fetch/viirs_firms.py:146` — medium/conf=medium · parseo-de-formato-externo

**`fetch_viirs_firms_hotspots` devuelve el resultado del parser sin verificar que la respuesta sea CSV: cualquier cuerpo de texto con HTTP 200 se convierte en `[]` = "sin anomalías térmicas".**

La función hace `return _parse_firms_csv(r.text)` (viirs_firms.py:146) tras un `raise_for_status()`. `_parse_firms_csv` devuelve `[]` cuando el header no trae `latitude`/`longitude` (viirs_firms.py:84-85), comportamiento pineado por tests/test_viirs_firms.py:56-59. Pero la docstring del fetcher (viirs_firms.py:124-125) promete explícitamente que `[]` significa 'sin detecciones' y `None` significa 'falla' — es decir, un cuerpo no-CSV servido con 200 (mensajes de cuota/transaction-limit excedido, ventana de mantenimiento, página de error del CDN) se reporta como 'este volcán no tiene hot spots'. Verifiqué en vivo que FIRMS sí usa códigos HTTP para el caso de clave inválida (400 + 'Invalid MAP_KEY.'), que sí es atrapado; el hueco queda para las respuestas 200 con texto. Nótese la inconsistencia con el fetcher hermano viirs_gibs.py:125, que SÍ valida `content-type` antes de decodificar. En un producto de vigilancia térmica, 'sin calor' es la peor forma de fallar en silencio.

*Fix sugerido:* Antes de parsear, validar la respuesta: `ctype = r.headers.get('content-type',''); first = (r.text or '').split('\n',1)[0]` y devolver `None` (no `[]`) si `'csv' not in ctype` o si `'latitude' not in first`, con `logger.warning` incluyendo los primeros ~120 chars del cuerpo. Test: monkeypatchear `requests.get` para devolver 200 + 'You have exceeded your transaction limit' y afirmar `is None`.

### `src/fetch/viirs_firms.py:118` — medium/conf=high · parseo-de-formato-externo

**La docstring documenta `days` en 1-10, pero la API de FIRMS sólo acepta [1..5]: con days>5 el fetcher devuelve None y lo loguea como falla de red.**

Verificado en vivo contra el endpoint real: `GET /api/area/csv/<key>/VIIRS_SNPP_NRT/-76,-56,-66,-17/40` responde HTTP 400 con el cuerpo 'Invalid day range. Expects [1..5].'. La docstring de `fetch_viirs_firms_hotspots` dice 'days: ventana hacia atrás (1-10)' (viirs_firms.py:118) y `_build_area_url` inserta `{int(days)}` sin ningún clamp ni validación (viirs_firms.py:57). Un llamador que siga la documentación con `days=7` recibe `None` y en el log ve 'FIRMS area (VIIRS_SNPP_NRT): 400 Client Error' (viirs_firms.py:144), indistinguible de una caída de red — se diagnostica como problema de conectividad cuando en realidad es un parámetro fuera de rango. Además `days=0` o negativo tampoco se validan. tests/test_viirs_firms.py:74 ejercita `days=2` y `days=1`, nunca el borde.

*Fix sugerido:* Corregir la docstring a 1-5 y validar en `_build_area_url` (o en el fetcher): `d = int(days); if not 1 <= d <= 10: raise ValueError(...)` — o clampear con warning explícito. Agregar la constante `FIRMS_MAX_DAYS = 5` junto a `VIIRS_SOURCES` y un test que afirme el rechazo de `days=7` con un mensaje distinguible de un fallo de red.

### ✅ `src/process/hires_pipeline.py:184` — medium/conf=high · contrato-de-retorno-inconsistente

**build_hires_for_scopes devuelve un dict desnudo en el error path de banda 2 faltante, pero su contrato (y todos sus callers) es una 2-tupla (images, meta)**

Si S3 no tiene la banda 2 (corte transitorio, latencia), la línea 184 hace `return {sid: None for sid in scopes}` — un solo dict. Todos los callers desempacan tupla: scripts/build_hires_cache.py:89 `results, results_meta = build_hires_for_scopes(...)` y scripts/build_hires_loop_cache.py:99 `images, meta = ...`. Con 8 scopes el unpack lanza ValueError y el run del workflow de cache hi-res crashea en vez de degradar; con exactamente 2 scopes desempacaría silenciosamente las KEYS (strings) en images/meta. Es la misma clase de bug que el `_query_frames` corregido en el audit de jun-2026 (volcat_api.py:186-194). El otro error path (línea 211) sí devuelve la 2-tupla correcta.

*Fix sugerido:* Cambiar la línea 184 por `return ({sid: None for sid in scopes}, {sid: {"render": "no_data", "sun_alt": None} for sid in scopes})`, consistente con el error path de la línea 211. Agregar un test que simule band_paths sin banda 2.

### ✅ `src/process/parallax.py:77` — medium/conf=high · fisica-datum

**El contrato pide altura 'sobre el terreno' pero la fisica del parallax requiere altura sobre el elipsoide (AMSL): sobre los Andes esto subcorrige hasta ~50%**

La navegacion ABI proyecta la linea de vision sobre el elipsoide GRS80, asi que el corrimiento aparente de un tope de pluma es Delta = h_elipsoide * tan(theta), con h medida desde el ELIPSOIDE (~AMSL), no desde el terreno local. El docstring de parallax_shift (linea 77: 'altura del tope sobre el terreno (m)') y la cabecera FICHA (linea 6) instruyen pasar altura sobre terreno. Escenario concreto: pluma de Lascar con tope a 10.6 km AMSL sobre terreno de 5.6 km; un caller obediente pasa h=5000 m y la correccion aplicada es 5000*tan(28.6 deg)=2.7 km en vez de 10600*tan(28.6 deg)=5.8 km — queda ~3.1 km de corrimiento sin corregir (>1.5 pixeles ABI), silenciosamente. La cadena propia (Wen-Rose/BT-matching/VOLCAT) reporta alturas AMSL, asi que un caller que pase esas alturas directo seria correcto y el docstring lo induciria a restar el terreno (empeorando). El modulo aun no esta cableado a produccion (solo tests), por eso no es high, pero el contrato quedaria mal al cablearlo.

*Fix sugerido:* Cambiar el contrato (docstring de parallax_shift/parallax_correct_field y FICHA linea 6) a 'altura del tope sobre el elipsoide/AMSL (m)' y documentar explicitamente que NO se debe restar la elevacion del terreno. Agregar un test que fije la semantica (p.ej. tope 10.6 km AMSL en Lascar -> corrimiento ~5.7 km).

### ✅ `src/process/wind_shear_height.py:326` — medium/conf=high · degeneracion-sin-guard

**Sin guard sobre mismatch_ms: una adveccion inconsistente con TODO el perfil de viento igual devuelve status ok con altura puntual**

Verificado numericamente contra el codigo real: con niveles z=0..15 km, u lineal 0..20 m/s, v=0, y adveccion observada (35, 0) m/s (p.ej. centroide que salta por ruido de deteccion, bajo el MAX_ADV_MS=60), wind_implied_height devuelve best a 15 km con mismatch_ms=15, shear=20 (discriminates=True) y banda 9-15 km = 6 km <= MAX_BAND_KM=8. Resultado: wind_shear_top_height retorna {status: ok, top_km: 15.0} aunque NINGUN nivel del perfil explica el movimiento observado (la pluma 'se mueve' 15 m/s mas rapido que el viento maximo de toda la columna). Fisicamente el matching es invalido: el minimo de una funcion que no baja del piso de ruido no es una deteccion. El propio modulo definio AMB_TOL_MS=8 como piso de ruido vectorial del viento GFS, pero nunca compara best_mis contra ese piso ni contra un multiplo. mismatch_ms se reporta en el dict pero ningun consumidor esta obligado a mirarlo.

*Fix sugerido:* Agregar guard MAX_MISMATCH_MS (p.ej. = AMB_TOL_MS o 1.5x, con justificacion en el comentario): si wh['mismatch_ms'] > MAX_MISMATCH_MS, devolver un status tipo 'adv_inconsistent' sin top_km (la adveccion observada no es consistente con el perfil: tracking espurio o proceso no advectivo). Mismo espiritu de honestidad que band_unconstrained/adv_ambiguous.

### ✅ `.github/workflows/goes.yml:125` — low/conf=high · cicd

**goes.yml y lascar_pdf.yml conservan `git pull --rebase -X ours` — exactamente el bug W3 que el audit jul-2026 corrigió solo en frp_timeline.yml**

goes.yml:125 y lascar_pdf.yml:46 hacen `git pull origin main --rebase -X ours`. Como documenta el propio fix en frp_timeline.yml:63-66, en un rebase `-X ours` favorece al UPSTREAM y descarta lo recién commiteado. Escenario: run manual de lascar_pdf coincide con un commit del bot frp (cada ~10 min, alta probabilidad) → conflicto → el PDF/STATUS recién generado se descarta silenciosamente y el `|| true` de ambas líneas oculta el fallo (push de nada, run verde). Severidad baja porque ambos workflows son manuales hoy, pero es el patrón zombie exacto que ya mordió una vez.

*Fix sugerido:* Replicar el patrón de frp_timeline.yml: `--rebase -X theirs` con retry x3 y ::warning, en ambos workflows.

### `dashboard/views/volcat_viewer.py:373` — low/conf=high · eficiencia-red

**La imagen VOLCAT completa se descarga dos veces por frame: _volcat_map_only_cached usa su propio requests.get y _volcat_colorbar_strip la vuelve a bajar via _volcat_image_bytes**

_volcat_map_only_cached (lineas 591-605) descarga image_url con un requests.get propio dentro de su ThreadPool; _volcat_colorbar_strip (linea 373) baja LA MISMA image_url via _volcat_image_bytes (cache separada, lineas 348-358). Para los sectores que el productor precalienta el doble download ocurre en background (2x trafico contra SSEC, ~730KB extra por frame por sector), pero para sectores no precalentados (Calbuco_1_km en el slot volcat_row) ambas descargas ocurren en el foreground del fragment, duplicando el tiempo de bloqueo del hallazgo principal. Con 4-5 sectores x frames cada ~10 min, 24/7, es trafico y latencia evitables contra un host externo (SSEC) del que ya se documento fragilidad.

*Fix sugerido:* Hacer que _volcat_map_only_cached obtenga los bytes base via _volcat_image_bytes(image_url) (misma cache que el colorbar) en vez de su requests.get propio, manteniendo la semantica de _VolcatMapUnavailable cuando _volcat_image_bytes devuelve b''.

### `dashboard/views/zonas_fullscreen.py:935` — low/conf=low · logica-rotacion

**El clamp de rotacion trata un bloqueo de exactamente n ventanas (120s) como 'misma ventana' y re-renderiza el mismo slot lento, pudiendo re-bloquear en loop**

La condicion (clock_idx - prev_idx) % n == 0 (linea 935) no distingue 'el reloj no avanzo' de 'el reloj dio exactamente una (o k) vueltas completas'. Escenario: un slot VOLCAT con SSEC colgado bloquea el fragment ~120s (n=10 x 12s — plausible sumando timeouts de 20s+30s+30s del hallazgo principal); al terminar, clock_idx ≡ prev_idx (mod 10), el codigo toma idx = prev_idx y vuelve a renderizar EL MISMO slot lento, que vuelve a bloquear ~120s -> la sala puede quedar clavada en el slot VOLCAT indefinidamente mientras dure la degradacion de SSEC. Probabilidad baja (requiere bloqueos cercanos a multiplos de 120s) pero el modo de fallo es un freeze permanente en un sistema sin supervision. Pre-existente al PR, pero el slot volcat_row (5 fetches concentrados) hace mas probable alcanzar bloqueos de esa magnitud.

*Fix sugerido:* Guardar tambien el epoch del ultimo render en session_state y, si paso mas de ~2x TV_SLOT_SECONDS desde entonces, avanzar +1 aunque (clock_idx - prev_idx) % n == 0.

### `dashboard/views/zonas_fullscreen.py:1054` — low/conf=low · concurrencia-hot-reload

**En hot-reload del modulo se resetean _TV_PRODUCED y _TV_PRODUCER_STARTED: el productor viejo sigue escribiendo al dict huerfano y arranca un segundo hilo**

Los globals de modulo (lineas 1053-1056) se reinicializan cuando Streamlit re-ejecuta el modulo (hot-reload en dev, o el gotcha de re-import documentado en CLAUDE.md). El hilo daemon viejo sigue vivo con referencias al dict _TV_PRODUCED viejo (nunca se detiene: while True, linea 1165), asi que sus PNG no llegan al fragment nuevo -> placeholders 'Preparando...' hasta que el hilo NUEVO (el gate _TV_PRODUCER_STARTED tambien se reseteo) complete su primer ciclo, y desde ahi dos hilos productores duplican trafico contra RAMMB/SSEC y trabajo PIL/GIL. En HF el deploy hace restart completo asi que el impacto es principalmente dev/hot-reload; pre-existente al PR pero el PR agrando el costo por ciclo del productor (5 zooms).

*Fix sugerido:* Colgar el estado del productor de un singleton robusto a re-ejecucion del modulo (ej. st.cache_resource con una funcion que cree el hilo y el dict, o guardar el dict en un modulo que no se hot-reloadea) y/o darle al hilo una condicion de salida cuando su dict quede huerfano (comparar id(dict) contra el global actual).

### `scripts/build_frp_timeline.py:180` — low/conf=medium · correctitud-de-metrica

**El backfill del roll-up diario no deduplica por `scan_dt`: durante un hueco de datos, varios targets resuelven al MISMO gránulo y la persistencia diaria queda inflada.**

El bucle de backfill histórico barre de `sweep_start` a `sweep_end` cada `rollup_step_min` y por cada target hace `d[name] = d.get(name, 0) + 1` (scripts/build_frp_timeline.py:177-180) sin registrar qué `scan_dt` ya contó. Como `fetch_scan_sliced` → `nearest_granule_key` no tiene tope de distancia (ver hallazgo en granule_select.py:71), ante un corte de FDCF de ~1 h tres targets consecutivos separados por 20 min pueden resolver todos al mismo gránulo del borde, sumando +3 a una métrica cuya definición explícita es 'número de scans con detección' (docstring de `daily_rollup`, src/fetch/frp_timeline.py:100-104). El bucle principal SÍ deduplica (`if key in existing: continue`, línea 125), así que la inconsistencia es sólo del path de backfill — pero el heatmap semanal del dashboard se alimenta de `daily` (dashboard/views/heatmap_actividad.py:297), o sea que el sobreconteo se muestra como persistencia térmica real.

*Fix sugerido:* Llevar un `seen_scans: set[datetime]` en el bucle de backfill y saltear (`continue`) si `scan_dt` ya fue contabilizado, exactamente como hace el bucle principal con `key in existing`. Ideal: derivar la clave con `_round_to_step(scan_dt, args.rollup_step_min)` para que el criterio sea el mismo en ambos caminos.

### `src/fetch/gfs_archive.py:128` — low/conf=high · manejo-de-errores

**`_load_idx` llama a `_parse_idx` FUERA de su try/except: un `.idx` malformado lanza ValueError hasta el llamador en vez de devolver None.**

El `try` de `_load_idx` cubre sólo la descarga (`s3.cat` / `s3.info`, gfs_archive.py:123-127); el `return _parse_idx(txt), grib, size` está en la línea 128, fuera. `_parse_idx` hace `int(parts[0])` e `int(parts[1])` sin protección (gfs_archive.py:65-66), así que una línea con numeración de submensaje ('1.1:'), un offset no numérico o un cuerpo HTML de error servido con 200 lanzan `ValueError` que sube por `_resolve` (gfs_archive.py:214, también fuera de try) hasta `fetch_gfs_profile_archive` (gfs_archive.py:246, la llamada a `_resolve` no está en el try de las líneas 257-261) → crash del script de validación en vez del `None` que documenta la función. Verifiqué el `.idx` real de hoy (gfs.20260731, 696 líneas) y no usa numeración de submensaje, así que es robustez latente, no un fallo activo.

*Fix sugerido:* Mover `return _parse_idx(txt), grib, size` dentro del `try` de `_load_idx` (o envolver `_parse_idx` en su propio try que devuelva None), y hacer que `_parse_idx` saltee con `continue` las líneas cuyo `num`/`offset` no sean enteros en vez de propagar. Test: `_parse_idx('basura\n1.1:0:d=X:TMP:500 mb:anl:\n')` no debe lanzar.

### `src/fetch/goes_lvtp.py:125` — low/conf=high · fisica-humedad

**Integracion hipsometrica con T seca en vez de temperatura virtual: sesgo sistematico bajo de ~50-100 m frente al geopotencial GFS que pretende cross-checkear**

La ecuacion hipsometrica exacta usa la temperatura VIRTUAL Tv = T(1+0.61q); el codigo usa T seca con _RD=287.05 (lineas 124-125). En troposfera baja humeda Tv-T ~ 1-2 K, lo que acumula (Rd/g0)*dTv*ln(p0/p) ~ 60-100 m de deficit de altura hacia 250 hPa. Los geopotenciales de GFS/Open-Meteo SI incluyen humedad, asi que el cross-check LVTPF-vs-GFS (proposito declarado del modulo) llevara un sesgo sistematico de ~0.05-0.1 km que se leeria como divergencia entre fuentes cuando es un artefacto de la formula. Es menor que el sesgo IR documentado (-0.4..-0.8 km) pero es sistematico, tiene signo fijo, y no esta declarado: el docstring solo dice '(aire seco)' sin cuantificar la consecuencia. LVTPF tambien distribuye LVM (humedad) en el mismo granulo, asi que el dato para corregirlo esta disponible.

*Fix sugerido:* Minimo: documentar el sesgo seco (~-0.05..-0.1 km, signo negativo) en el docstring del modulo y en la comparacion compare_lvtp_vs_gfs. Mejor: leer LVM del mismo granulo y usar Tv en el integrador.

### `src/fetch/goes_lvtp.py:77` — low/conf=medium · dominio-terreno-alto

**El filtro p<=1013.25 conserva niveles bajo el TERRENO sobre el Altiplano: hasta ~4 km de capas ficticias entran a la integral de altura**

_P_MAX_HPA=1013.25 solo excluye niveles bajo el nivel del mar. Para volcanes del Altiplano (Lascar, superficie ~570 hPa; Parinacota ~550 hPa) los niveles 1013..600 hPa estan bajo tierra: LVTPF ahi entrega extrapolacion del first-guess NWP, no una medicion. Esos ~4 km de espesor ficticio entran a la integral hipsometrica que fija el absoluto de TODOS los niveles superiores (donde vive la pluma). Si la T extrapolada bajo tierra difiere ~3-5 K de la estructura real, el error de altura arrastrado a 5-15 km es ~60-150 m, por encima del '~0.1 km' que el docstring (lineas 32-34) atribuye al anclaje — esa cota solo considera el ancla ISA en MSL, no las capas bajo terreno. No corrompe el mapeo relativo Teff->altura (que depende de la estructura), pero si el absoluto AMSL comparado contra GFS.

*Fix sugerido:* Documentar que la cota de ~0.1 km del anclaje aplica a volcanes bajos y crece sobre el Altiplano; opcionalmente filtrar niveles con p > p_superficie(z_volcan) estimada (ISA del z del volcan) y anclar en el primer nivel sobre terreno.

### `src/fetch/goes_lvtp.py:97` — low/conf=medium · caso-borde-estratosfera

**_std_atm_height usa solo la rama troposferica ISA sin guard: si el nivel base quedara sobre ~226 hPa el ancla erra hasta ~1 km**

La formula z=(T0/L)(1-(p/p0)^(RL/g0)) es valida solo hasta 11 km (p>=226.32 hPa); por encima la ISA es isoterma. El codigo la evalua para cualquier p sin verificar la rama: a 100 hPa da 15795 m (ISA real ~16180, error ~385 m), a 50 hPa da 19323 m (ISA ~20576, error ~1.25 km). En uso normal p[0] es el nivel mas bajo conservado (troposferico) y no se alcanza, pero el caso degenerado existe: ventana donde la mediana clear-sky solo sobrevive el filtro en niveles altos (p.ej. contaminacion generalizada de niveles bajos que caiga fuera de 150-330 K) -> el perfil entero queda desplazado hasta ~1 km sin ninguna senal. La funcion es publica y su docstring dice 'nivel base near-surface, siempre troposferico' como supuesto no verificado en codigo.

*Fix sugerido:* Guard barato en _build_profile o _clear_sky_profile: exigir p[0] >= ~500 hPa para perfiles de volcanes (o >= 226.32 hPa como minimo duro y devolver None si no), convirtiendo el supuesto documentado en invariante verificado.

### `src/process/parallax.py:91` — low/conf=high · aproximacion-dominio

**El azimut al subsatelite usa aproximacion plate-carree que erra ~4.3 grados a -55S: ~1.5 km de error transversal para pluma de 10 km en la zona austral**

Las lineas 91-92 calculan la direccion al subsatelite como vector recto en coordenadas equirectangulares (north_m = dlat*R, east_m = dlon*R*cos(lat)), no como azimut de circulo maximo. Verificado numericamente: el error de azimut es 1.0 grados a -17S, 1.9 a -23S, 1.3 a -40.6S y 4.3 grados a -54.9S. La magnitud del corrimiento no cambia (es h*tan(theta)), pero la DIRECCION si: error transversal = d_h*sin(d_az) = 69 m (Parinacota), 180 m (Lascar), 251 m (Villarrica), 1482 m (zona austral -55) para un tope de 10 km. En -17..-45 queda muy por debajo del pixel de 2 km (consistente con '1er orden'), pero en la zona austral (-56, soportada explicitamente desde el audit) el error transversal se acerca a 1 pixel y no esta documentado en las limitaciones (la cabecera solo menciona 'curvatura fina y elipsoide').

*Fix sugerido:* Usar el azimut esferico verdadero al subsatelite: un = -sin(lat_r)*cos(dlon_r), ue = sin(dlon_r) (con dlon = sat_lon - lon), normalizado — mismo costo computacional, sigue siendo puro y vectorizable. Como minimo, documentar el error direccional creciente hacia el sur en las limitaciones de la FICHA.

### `src/process/parallax.py:62` — low/conf=high · caso-borde-limbo

**Sin guard mas alla del limbo: arcsin pliega el angulo cenital y aplica corrimientos absurdos en silencio**

Para un punto fuera del disco visible (angulo central gamma > ~81.3 grados, satelite bajo el horizonte) el angulo cenital real supera 90 grados, pero arcsin (linea 63) devuelve el suplemento plegado (<90). Verificado: en (0, 10E) con sat_lon=-75 devuelve zen=86.3 grados, tan=15.5, y parallax_shift aplica un corrimiento de 8.6 grados de longitud (~950 km) para h=10 km, sin warning ni NaN. El dominio operativo (Chile, -17..-56, gamma<62) no lo alcanza, pero la funcion es publica, vectorizable, y un caller futuro con un campo lat/lon que incluya el limbo (recortes full-disk) obtendria pixeles teletransportados en vez de un error. Ademas, cerca del limbo (gamma 75-81) tan(theta) crece sin cota y el 1er orden ya no es valido, tampoco documentado como limite numerico.

*Fix sugerido:* En satellite_zenith_angle detectar el lado del triangulo: si d^2 > rs^2 - R^2 (equivalente cos(gamma) < R/rs) el punto esta mas alla del limbo -> devolver NaN (y que parallax_shift propague NaN o corrimiento 0 con warning). Documentar un umbral de validez (p.ej. theta < 80 grados) en la FICHA.

### `src/process/wind_shear_height.py:63` — low/conf=medium · umbral-ruido

**MIN_ADV_MS=3 esta por debajo del jitter de centroide de 1 pixel (~3.3 m/s a dt=10 min): el guard de pluma adjunta es evadible por ruido de deteccion**

Un salto de centroide de 1 pixel ABI (2 km) entre scans separados 600 s produce una adveccion espuria de 3.3 m/s, que ya supera MIN_ADV_MS=3.0. Escenario: pluma adjunta al crater (el caso F3 que el guard quiere atrapar) cuya mascara gana/pierde un pixel de borde entre scans -> adv_speed=3.3-7 m/s > MIN_ADV -> el guard adv_ambiguous NO se dispara y el matching asigna el nivel de viento mas parecido a un vector que es puro ruido de deteccion, potencialmente el nivel calmo bajo (altura baja falsa, exactamente lo que F3 documenta). El guard de banda puede o no atraparlo despues. El propio archivo documenta (lineas 74-77) que plumas chicas cambian pixeles entre scans, pero el umbral no se dimensiono contra ese jitter (2 km/600 s).

*Fix sugerido:* Subir MIN_ADV_MS a >= 2 pixeles/dt (6.7 m/s para dt=600 s) o, mejor, calcularlo dinamicamente: min_adv = k * pixel_m / dt_s con k=2 y comentario de procedencia; documentar en la FICHA que el umbral cubre el jitter de deteccion de 1 pixel.

### `tests/test_gfs_archive.py:128` — low/conf=high · test-fragil-entorno

**La aritmética de fechas de los tests live de gfs_archive (dt.replace(day=max(1, dt.day - back_days))) no cruza al mes anterior: los días 1-3 de cada mes prueba la misma fecha (o una futura) y termina en skip silencioso.**

En test_fetch_gfs_profile_archive_lascar (línea 128) y test_fetch_gfs_wind_profile_archive_lascar (línea 158), si hoy es día 1 del mes: max(1, 1-1)=1 → prueba hoy a las 12Z (posiblemente ciclo futuro aún no publicado) tres veces; si es día 2: back_days 2 y 3 colapsan ambos en day=1. El bucle 'probar 1-3 días atrás' no hace lo que dice cerca del inicio de mes y el test degrada a pytest.skip sin que nadie lo note — es un test frágil al calendario del host que reduce cobertura justo de forma intermitente. No produce falsos verdes (hace skip), por eso severidad baja, pero el patrón replace(day=...) también lanzaría ValueError si alguien lo copiara con day>28.

*Fix sugerido:* Usar timedelta: probe_dt = (datetime.now(timezone.utc) - timedelta(days=back_days)).replace(hour=12, minute=0, second=0, microsecond=0) dentro del bucle, que cruza meses y años correctamente.

### `tests/test_wind_shear.py:80` — low/conf=high · assert-tautologico

**test_wind_implied_height_ambiguity_band solo asserta z_lo_m <= z_m <= z_hi_m, que es verdadero POR CONSTRUCCIÓN (el mejor nivel siempre pertenece al conjunto 'near'): el test pasa con cualquier implementación de la banda.**

En wind_implied_height (src/process/wind_shear_height.py:128-132), near = mis <= best_mis + amb_tol siempre incluye al índice k del mínimo, así que z[near].min() <= z[k] <= z[near].max() es una tautología. Si la banda se calculara mal (p.ej. usando mis < best_mis - tol, o ignorando amb_tol por completo y devolviendo [z_m, z_m]), este test seguiría verde. La banda sí queda parcialmente pineada por test_amb_tol_recalibrado_ensancha_banda (línea 98), que verifica valores exactos, por eso la severidad es baja — pero el test de la línea 74 aporta falsa confianza y su docstring promete más de lo que verifica ('la banda cubre los niveles con mismatch cercano al mínimo').

*Fix sugerido:* Reemplazar el assert por expectativas concretas con el perfil _sheared_profile: para advección (5,15) calcular a mano qué niveles caen dentro de amb_tol y assertar z_lo_m y z_hi_m exactos (como hace test_amb_tol_recalibrado), o eliminar el test por redundante.

## Mejoras

### `src/fetch/gfs_archive.py:164` — high/conf=high · test-coverage

**El invariante got↔values de _collect_raw (orden de claves bajadas = orden de mensajes decodificados) no tiene test puro; es el mecanismo que asigna cada temperatura/viento a su nivel de presión.**

fetch_gfs_profile_archive hace vmap = dict(zip(got, vals)) (líneas 262 y 320): el i-ésimo valor decodificado se asigna a la i-ésima clave bajada. Si _collect_raw (148-164) apendeara la clave antes de verificar presencia en el idx, o no resolviera end=None con size-1, o _decode_values_at_point reordenara mensajes, las temperaturas se asignarían a niveles equivocados → perfil T(z) corrupto → altura de pluma silenciosamente errónea en la validación histórica. _collect_raw es testeable sin red (recibe s3 como parámetro, basta un fake con cat_file), pero no existe ningún test: los únicos que ejercitan el camino completo son los de red (test_gfs_archive.py:118, 148) que exigen eccodes y hacen skip permanente en CI. La pregunta explícita del encargo ('¿el decode tiene test del orden got↔values?') tiene respuesta: no.

*Fix sugerido:* Test puro de _collect_raw con un fake s3 cuyo cat_file registre (start,end) pedidos y devuelva payloads distinguibles: verificar (a) got preserva el orden de needed saltando claves ausentes, (b) el último registro usa end=size-1, (c) raw es la concatenación en el mismo orden que got. Complementar con un test de _decode_values_at_point usando 2-3 mensajes GRIB2 mínimos pregrabados si eccodes está disponible (skipif local).

### ✅ `src/fetch/goes_fdcf.py:208` — high/conf=high · eficiencia-memoria-cpu

**fetch_latest_hotspots y fetch_hotspots_at_time leen Mask/Power/Temp/Area del full disk (5424×5424) aunque el caller pida un bbox chico, cuando frp_timeline.fetch_scan_sliced ya demuestra la lectura recortada ~15× más rápida**

Las líneas 206-213 (y 329-336 en la variante histórica) hacen `.values` sobre 4 variables full-disk (~29 MB uint8 + 3×~118 MB float32 descomprimidos ≈ 380 MB de churn y ~15 s por llamada según el propio docstring de fetch_scan_sliced, frp_timeline.py:170-174). Los 6 consumidores del dashboard (live_viewer:429, modo_evento:73, modo_guardia:94, modo_guardia_volcan:120, zonas_fullscreen:78, scripts/generate_lascar_report:100) pasan bounds chicos y pagan el full disk igual, en el proceso Streamlit de HF con RAM acotada. frp_timeline._chile_xy_index_range + el slicing (frp_timeline.py:216-222) resuelven exactamente esto pero solo el timeline lo usa. Además el bloque de extracción (filtro de máscara → np.where → latlon → filtro bbox → armado de HotSpot → sort) está copiado 3 veces casi idéntico: goes_fdcf:227-267, goes_fdcf:347-381 y frp_timeline:228-258.

*Fix sugerido:* Unificar en UNA implementación en goes_fdcf: (1) helper `_extract_hotspots(mask, power, temp, area, xs, ys, sat_lon, bounds, high_conf_only)` compartido por las 3 funciones; (2) cuando bounds no es None, recortar con la ventana geos ANTES de `.values` (patrón fetch_scan_sliced/ACHA). fetch_scan_sliced puede quedar como alias delgado. Las 6 vistas se benefician sin tocarlas.

### ✅ `src/process/wen_rose_height.py:437` — high/conf=high · duplicacion-nucleo-cientifico

**El preámbulo de adquisición de escena (~100 líneas: C14→ventana geos→C11/C15→guard mismo-scan→máscara→contexto SO2→perfil GFS) está triplicado en wen_rose_height, bt_matching_height y acha_plume_height**

wen_rose_height.py:437-547, bt_matching_height.py:97-178 y acha_plume_height.py:181-246 repiten casi línea a línea: download_band_at + _geos_index_bbox + _window_latlon, el guard 'bandas de scans distintos' (wen_rose:490-496 vs bt_matching:147-153), la máscara detect_ash_enhanced, el bloque SO2 con el mismo `try: from src.config import SO2_INDICATOR_THRESHOLD except: -3.0` (wen_rose:522-529 vs bt_matching:164-171), el fetch del perfil GFS con dicts de error idénticos, y `_bounds_for` copiado 3 veces (wen_rose:335, bt_matching:52, acha_plume_height:102). Esto es el núcleo SDA: un fix a un guard de honestidad (como fue el mismo-scan en jun-2026) hay que aplicarlo 3 veces o queda inconsistente silenciosamente — el riesgo exacto que el proyecto dice querer evitar. Además wen_rose ya computa internamente el tope BT-matching (top_bt), por lo que la ruta compartida es natural.

*Fix sugerido:* Extraer un helper `_acquire_ash_scene(dt, volcano, radius_deg, bands, with_coefs) -> SceneData | error-dict` en un módulo compartido (p.ej. src/process/scene.py) que devuelva bts/coefs/mask/lat/lon/scan_dt/so2_px/profile o el dict de error estándar. Los 3 retrievals lo consumen; los guards viven en UN solo lugar y se testean una vez.

### `tests/test_granule_select.py:34` — high/conf=high · test-coverage

**Los tests de granule_select usan un parser local del test; los parse_ts de producción de los 5 call-sites (goes_s3._scan_start, goes_fdcf._parse_scan_time, goes_acha._parse_scan_time) no están pineados por ningún test, ni existe test del wiring call-site→helper.**

El helper nearest_granule_key es puro y bien testeado, pero contra un _parse definido en el propio test (tests/test_granule_select.py:34-43). Los parsers reales que cada fetcher inyecta — src/fetch/goes_s3.py:161 (_scan_start, usado por download_band_at:184 y por wen_rose/wind_shear), src/fetch/goes_fdcf.py:89 (_parse_scan_time, reusado por frp_timeline.py:45 y goes_lvtp.py:52) y src/fetch/goes_acha.py:87 — no tienen ningún test directo. El único test que toca _scan_start lo monkeypatchea a una constante (tests/test_orchestration_and_guards.py:117). Un off-by-one en el day-of-year, en el slicing del token _s, o un cambio de formato de nombre NOAA haría que parse_ts devuelva None o fecha corrida: nearest_granule_key degradaría silenciosamente (elige otro gránulo o devuelve None) y toda la suite seguiría verde. Para un SDA esto sesga el scan usado en detección de ceniza/altura/FRP sin ningún síntoma.

*Fix sugerido:* Agregar tests puros que llamen a cada parser de producción con nombres de archivo NOAA reales (p.ej. OR_ABI-L2-FDCF-M6_G19_s20261151200216_e..._c....nc) y verifiquen el datetime exacto, incluyendo doy de fin de año y key sin token _s → None. Opcional: un test de wiring por fetcher que monkeypatchee solo fs.ls y verifique que la key elegida es la de menor |Δt| usando el parser real.

### `../CLAUDE.md:14` — medium/conf=high · doc-drift

**El CLAUDE.md padre (Volcanologia/) todavía cataloga Goes/ como 'GOES (placeholder) | Vacío' — el proyecto es un SDA en producción con 202 tests y deploy HF**

Volcanologia/CLAUDE.md:14 (tabla de subproyectos): '| **Goes/** | GOES (placeholder) | Vacío |'. El mismo archivo, en el bloque de transparencia algorítmica, lista a Goes como SDA 'en scope (desplegados/producción)' — contradicción interna. Cualquier sesión que arranque en Volcanologia/ y lea la tabla asume que Goes no tiene nada y puede duplicar trabajo o ignorar dependencias. Nota: el archivo está un nivel arriba del repo Goes (no versionado en este git), por eso la ruta relativa ../CLAUDE.md.

*Fix sugerido:* Actualizar la fila: 'Goes/ | Dashboard NRT GOES-19 (Ash RGB, altura de pluma propia, FRP) | Producción · HF Spaces · GitHub: MendozaVolcanic/goes-volcanic-monitoring'.

### `dashboard/views/zonas_fullscreen.py:78` — medium/conf=high · eficiencia-red

**_hotspots_zone cachea por zone_key, así que la vista 4-zonas dispara 4 descargas full-disk FDCF del MISMO scan cada 5 min**

El cache `@st.cache_data(ttl=300)` de la línea 75 está keyed por zone_key y adentro llama `fetch_latest_hotspots(bounds=VOLCANIC_ZONES[zone_key])` (línea 78). Como fetch_latest_hotspots hoy lee el full disk (ver hallazgo goes_fdcf:208), la grilla 2×2 baja y procesa 4 veces el mismo archivo NetCDF por ciclo de cache. modo_guardia.py:94 ya usa el patrón correcto: una sola llamada con chile_bbox y filtrado posterior.

*Fix sugerido:* Cachear UNA llamada Chile-wide (bbox que una las 4 zonas) y derivar los hotspots por zona filtrando en memoria con los bounds de VOLCANIC_ZONES — mismo patrón que modo_guardia. Se elimina el 75% del tráfico S3 de esta vista.

### `dashboard/views/zonas_fullscreen.py:110` — medium/conf=high · duplicacion-views

**La receta de figura geo Plotly (layout_image + triángulos de volcanes + diamantes de hotspots + add_chile_border + scaleratio 1/cos(lat) + ejes ocultos + layout oscuro) está copiada ~11 veces en las vistas**

Instancias verificadas del mismo esqueleto con variaciones menores: zonas_fullscreen._zone_fig:110-180 y _render_volcat_zone_cell:400-501 (dos variantes en el mismo archivo), modo_evento._ash_fig:124-202, modo_guardia.py:168, mosaico_chile.py:155-164, replay_reciente.py:104-115, loop_volcan.py:118-157, modo_guardia_volcan.py:333-384, comparador.py:119-129, backfill_viewer.py:216, volcat_viewer.py:78-159 y :814. map_helpers ya centralizó las piezas chicas (array_to_data_url, add_chile_border, hotspot_distance_km) pero no el armado. Consecuencia real: mejoras aplicadas a una vista no llegan a las otras — p.ej. `constrain="domain"` (fix de encuadre 2026-06-08) existe en zonas_fullscreen y volcat_viewer pero no en modo_evento/comparador/mosaico; el clamp `max(0.1, cos_lat)` también está repetido con y sin clamp según la vista.

*Fix sugerido:* Agregar a map_helpers un `build_geo_figure(bounds, img=None, volcanoes=..., hotspots=..., height=..., title=..., uniform_domain=True)` que devuelva la figura base; cada vista solo agrega sus trazas específicas (anillos, viento, colorbars). Migrar vista por vista empezando por las 4 que comparten el patrón exacto (zonas, modo_guardia, replay, mosaico).

### `data/frp_timeline.json:1` — medium/conf=high · cicd-historia

**El bot FRP infló la historia de main: 627 de 944 commits locales son 'frp: rolling intraday timeline' (~15-20/día en el remote), pack de 154 MiB**

git log local: 944 commits totales, 627 del autor GOESBot; remote verificado vivo (gh api: commits del bot hoy 2026-08-02 a las 11:52, 10:55, 09:22...). El JSON pesa ~150 KB por versión; a este ritmo main acumula ~500 commits-bot/mes y el pack ya está en 154 MiB (git count-objects). Consecuencias: git log/blame inutilizables sin filtros, clones cada vez más pesados, y deploy_hf.sh ya tuvo que inventar el orphan branch en parte por historia sucia. El propio proyecto ya usa el patrón correcto para datos rodantes: releases rolling (animations-rolling, hires-rolling). Nótese que migrar el JSON a release también habilita el fix del hallazgo #1 (fetch remoto desde el dashboard).

*Fix sugerido:* Publicar frp_timeline.json como asset de un release rolling (frp-rolling) igual que los caches hires, y que el dashboard lo baje de ahí; opcionalmente squash histórico de los commits-bot en una rama de datos huérfana.

### ✅ `docs/FICHA_SDA_GOES.md:57` — medium/conf=high · doc-drift

**Conteos de tests desactualizados en docs de compliance y paper: FICHA_SDA dice '132 tests', REGISTRO_PAPER dice '140 tests' — pytest recolecta 202 hoy**

docs/FICHA_SDA_GOES.md:56-57 ('Validación física: 132 tests automatizados') y docs/paper/REGISTRO_PAPER.md:57 ('Suite | 140 tests'). `python -m pytest tests/ --collect-only -q` → '202 tests collected'. La FICHA es el documento de transparencia CPLT 372 cuya regla de mantenimiento (CLAUDE.md del proyecto y la propia ficha línea 71-72) exige actualización en el mismo commit que los cambios de lógica; quedó en v1.0 2026-07-01 pese a que después entraron LVTPF (10 tests), gfs_archive (9), band_unconstrained, etc. No engaña sobre el método pero sí subreporta la evidencia de validación declarada ante compliance.

*Fix sugerido:* Actualizar ambos números a 202 (o usar redacción no-frágil: '>200 tests, ver CI') y bump de versión/fecha de la FICHA.

### ✅ `requirements.txt:12` — medium/conf=high · deps-no-usadas

**cartopy declarado pero jamás importado en el repo — infla el build Docker de HF y el CI; el Dockerfile justifica libgeos/gcc por cartopy**

requirements.txt:12 declara cartopy>=0.22.0; grep de 'import cartopy'/'from cartopy' en todos los *.py del repo = 0 matches. cartopy es de las deps más pesadas del stack geoespacial (arrastra shapely, compila si no hay wheel) y el Dockerfile:16-22 instala libgeos-dev/gcc/g++ citándolo como motivo. También alarga cada run de tests.yml:35 (instala requirements.txt completo). Quitarlo reduce build time del Space y superficie de fallos de resolución de deps.

*Fix sugerido:* Eliminar cartopy de requirements.txt; revisar si libgeos-dev sigue siendo necesario en el Dockerfile (pyproj y rasterio usan PROJ/GDAL, no GEOS directamente) y actualizar el comentario.

### ✅ `requirements.txt:28` — medium/conf=high · deps-no-usadas

**folium y streamlit-folium declarados sin un solo import; CLAUDE.md:18 documenta 'Streamlit + Plotly + Folium' como stack — drift doble (dep y doc)**

requirements.txt:28-29 (folium>=0.15.0, streamlit-folium>=0.17.0); grep de 'import folium|streamlit_folium|st_folium' en *.py = 0 matches. CLAUDE.md:18 afirma que el dashboard usa Folium (el frontend real es Plotly puro + PNG). Deps muertas en el deploy HF + doc de stack que despista a quien entre al proyecto.

*Fix sugerido:* Quitar folium/streamlit-folium de requirements.txt y corregir CLAUDE.md:18 a 'Streamlit + Plotly'.

### `requirements.txt:3` — medium/conf=medium · config-pins

**Salvo streamlit, todas las deps del deploy HF usan rangos abiertos >= — un rebuild del Space puede tomar majors con breaking changes (numpy 2.x, plotly 6.x) y romper producción**

requirements.txt: s3fs>=2024, xarray>=2024, numpy>=1.26 (admite 2.x con el cambio de copy-semantics y dtype promotion), plotly>=5.18 (admite 6.x que cambió defaults de template/JS), rasterio>=1.3, etc. El proyecto ya aprendió esta lección con streamlit y lo pineó exacto (líneas 16-27, 'PIN EXACTO... cada rebuild de HF/uv podia instalar otro patch'). Cada docker build de HF (deploy o restart con cache frío) re-resuelve deps frescas: el mismo commit puede producir dos entornos distintos, y una rotura llegaría silenciosa en el próximo redeploy. Para un SDA en producción, la reproducibilidad del entorno es parte de la honestidad del producto (REGISTRO_PAPER §6 la reivindica).

*Fix sugerido:* Congelar al menos majors (numpy>=1.26,<2 o probar y pinear 2.x; plotly>=5.18,<6; xarray con techo) o generar un requirements-lock.txt (pip-compile/uv lock) para el Dockerfile.

### `src/fetch/goes_acha.py:87` — medium/conf=high · duplicacion-fetchers-s3

**El parseo del timestamp NOAA `_sYYYYDDDHHMMSS` existe en 4 variantes y _list_files_at_hour en 3 copias que solo difieren en la constante de producto; además hay imports cross-módulo de helpers privados**

Copias verificadas: (a) _parse_scan_time idéntico en goes_fdcf.py:89 y goes_acha.py:87 (el propio docstring dice 'Idéntico a goes_fdcf._parse_scan_time'); goes_s3._scan_start:161 y el parseo inline de goes_s3.get_latest_time:240-248 son la 3ª y 4ª variante del mismo formato. (b) _list_files_at_hour idéntico salvo S3_PRODUCT en goes_fdcf.py:270, goes_acha.py:178 y goes_lvtp._list_lvtp_files:304. (c) Para reutilizar, goes_lvtp.py:50-53 importa `_geos_index_bbox`/`_parse_scan_time` privados de goes_acha, frp_timeline.py:37-47 importa 8 símbolos privados de goes_fdcf, y wen_rose/bt_matching importan `_geos_index_bbox`/`_window_latlon` de goes_acha — acoplamiento a underscore-privates de otros módulos que rompe la señal de 'esto es interno'.

*Fix sugerido:* Crear src/fetch/abi_common.py con API pública: parse_scan_time(key), list_product_hour(s3, bucket, product, dt), geos_index_bbox(), window_latlon(), abi_proj(). Los 5 módulos (goes_s3, goes_fdcf, goes_acha, goes_lvtp, frp_timeline) y los retrievals de altura importan de ahí. Un solo lugar para el formato de nombre NOAA y la matemática geos.

### `src/fetch/goes_fdcf.py:277` — medium/conf=high · resiliencia-inconsistente

**El retry S3 (_retry_s3) protege solo a goes_s3; los fetchers L2 (FDCF, ACHA, LVTPF, frp_timeline) hacen s3.ls y s3.open crudos sin reintento**

goes_s3._retry_s3 (goes_s3.py:48) existe precisamente porque 'la conexión a noaa-goes19 se cae de forma INTERMITENTE' (su comentario, líneas 40-44). Pero goes_fdcf (_list_files_at_hour:277, s3.open:206/329), goes_acha (:185, :243), goes_lvtp (:312, :269) y frp_timeline (vía el _list_files_at_hour importado) llaman s3fs sin retry: un timeout transitorio devuelve [] o None y el dashboard muestra 'sin hotspots'/'sin altura' cuando el dato SÍ existía — para un SDA, un negativo silencioso. Cada uno además crea su propio `s3fs.S3FileSystem(anon=True)` por llamada en vez de reusar el singleton _get_fs de goes_s3.

*Fix sugerido:* Mover _retry_s3 y _get_fs al módulo común de fetchers ABI (ver hallazgo abi_common) y envolver los s3.ls/s3.open de los 4 fetchers L2, propagando FileNotFoundError inmediato como ya hace goes_s3.

### `src/fetch/timeseries.py:63` — medium/conf=high · test-coverage

**_ash_red_fraction_v2 — la ÚNICA métrica automática sobre Ash RGB que la filosofía operacional del proyecto permite ('para % ash usar _ash_red_fraction_v2') — no tiene ningún test: los umbrales de los filtros de cirros y nieve no están pineados.**

CLAUDE.md la designa explícitamente como la métrica sancionada contra falsos positivos de cirros/nieve (30-60% en Chile invierno), pero tests/ no la referencia (solo el import del módulo en test_smoke.py:49). Los umbrales load-bearing (mask_red: r>100 & r>g+15 & r>b+15; cirros: b>130 & r>100; nieve: r,g,b>200) podrían cambiarse o invertirse sin que ningún test falle — y esta métrica alimenta la serie temporal que un guardia mira para evaluar actividad. Es lógica pura sobre un array RGB: trivial de testear determinísticamente.

*Fix sugerido:* Test puro con imágenes sintéticas 3×3: un píxel rojo-ceniza (p.ej. 150,80,90) cuenta; un píxel rosado-cirro (150,100,140) NO cuenta; un píxel blanco-nieve (220,220,220) NO cuenta; imagen None/vacía → 0.0. Verificar la fracción exacta.

### `src/fetch/timeseries.py:202` — medium/conf=high · arquitectura-capas

**Dependencia invertida: módulos de src/fetch importan de dashboard (parse_rammb_ts/fmt_both_long viven en dashboard.utils pero los consumen fetchers)**

src/fetch/timeseries.py:202 (`from dashboard.utils import parse_rammb_ts` dentro de _one, ejecutado por cada frame) y src/fetch/hires_loop_cache.py:81 (`from dashboard.utils import fmt_both_long, parse_rammb_ts`, con fallback a labels crudos si falla) hacen que la capa de datos dependa de la capa de UI. parse_rammb_ts es parsing de un formato de fuente (concern de fetch, no de presentación) y ya se usa desde ambos lados. Esto impide usar src/ standalone (scripts, tests, futuros consumidores del ecosistema documentados en INTEGRATION.md) sin arrastrar el árbol dashboard, y es exactamente el tipo de import cross-package que el propio CLAUDE.md marca como frágil en deploy.

*Fix sugerido:* Mover parse_rammb_ts (y ts_to_parts, que ya está en rammb_slider) a src/fetch/rammb_slider o a un src/timeutil.py; dashboard.utils lo re-exporta para no romper las vistas. hires_loop_cache devuelve el ts crudo y deja el formateo del label a la vista (el label bonito es presentación).

### `src/fetch/wind_data.py:65` — medium/conf=high · resiliencia-inconsistente

**5 módulos bypassean la session HTTP compartida (que monta Retry + connection pooling) usando requests.get crudo**

src/fetch/_http_session.py existe para centralizar retries ante 429/5xx y keep-alive ('cubre de una a todos los clientes', su docstring), pero wind_data.py:65 y :100, gfs_profile.py:110 y :267, viirs_firms.py:141, viirs_gibs.py:119 y volcat_api.volcat_height_at:396 usan `requests.get` directo: sin reintento y con TLS handshake nuevo por request. gfs_profile es insumo del retrieval de altura (SDA): un 502 transitorio de Open-Meteo hoy degrada el retrieval a no_data cuando un retry lo salvaría. La inconsistencia es puntual porque volcat_api SÍ usa _get_session en el resto del módulo (líneas 201, 340).

*Fix sugerido:* Reemplazar los requests.get crudos por `_get_session().get(...)` en los 5 módulos (import ya disponible en volcat_api; en los otros es 1 línea).

### `src/fetch/wind_data.py:142` — medium/conf=medium · eficiencia-red

**fetch_wind_grid dispara 50 requests HTTP separados a Open-Meteo cuando el API acepta múltiples coordenadas en una sola request**

Las líneas 139-150 lanzan un ThreadPoolExecutor de 12 workers para 50 puntos (WIND_LATS×WIND_LONS), un request por punto. Open-Meteo soporta `latitude=-17,-21,...&longitude=-79,-75,...` (listas separadas por coma) devolviendo un array de resultados: la grilla completa cabe en 1-2 requests. Menos latencia de la vista de vientos, menos presión de rate-limit sobre un API público sin key, y desaparece el executor. Además los puntos con error se omiten silenciosamente (líneas 148-150): la vista puede dibujar 30/50 flechas sin ninguna señal de degradación (fetch_wind_diagnostic existe como workaround aparte solo para el caso lista-vacía).

*Fix sugerido:* Reescribir fetch_wind_grid con requests batch de Open-Meteo (una llamada con las listas de coords) y devolver también un contador de puntos fallidos (o note) para que la vista pueda señalar grilla incompleta.

### `src/process/bt_matching_height.py:57` — medium/conf=high · test-coverage

**bt_matching_top_height (~170 líneas de orquestación) solo se testea con volcán inexistente — el mismo patrón 'gap T1' que el audit cerró para wen_rose_top_height pero no replicó aquí ni en plume_top_height de ACHA.**

tests/test_bt_matching.py tiene 3 tests: dos de la función pura altitudes_from_bt y uno de no_data con volcán inexistente (línea 57). Toda la orquestación de bt_matching_top_height (descarga C14, ventana geos, detección tri-espectral, mapeo BT→altura, ensamblado del dict de honestidad) no está cubierta: la escena sintética con mocks de S3/GFS que cerró el gap T1 (test_orchestration_and_guards.py) solo se aplicó a wen_rose. Lo mismo aplica a plume_top_height de acha_plume_height.py (solo unknown-volcano puro + tests de red con skip). Un swap de bandas o un error en la intersección máscara∩altura en estos dos caminos saldría verde. Es el producto que el dashboard SÍ muestra (BT-matching es parte de la cadena de altura desplegada), mientras wind_shear —que sí tiene tests ricos— aún no está cableado.

*Fix sugerido:* Reusar la fixture synthetic_s3 de test_orchestration_and_guards.py (parametrizándola o extrayéndola a conftest.py) para correr bt_matching_top_height end-to-end contra la escena sintética con Tc conocido, verificando status ok, mask_px y que top_km cae en la altura del perfil correspondiente al Tc; ídem un caso para plume_top_height de ACHA con campo HT sintético.

### `src/process/parallax.py:66` — medium/conf=medium · codigo-sin-integrar

**La corrección de parallax (hallazgo F4 del audit jul-2026) está implementada y testeada pero ningún pipeline ni vista la aplica: la georef de las plumas en altura sigue desplazada**

parallax_shift/parallax_correct_field solo se referencian desde tests/test_parallax.py; grep sobre dashboard/ y el resto de src/ no encuentra consumidores. Los campos field_km de bt_matching/wen_rose/acha_plume_height y los overlays de vista se dibujan con la lat/lon del pixel sin corregir — para una pluma a 10 km vista desde geoestacionario a lat -40 el corrimiento es del orden de varios km, que es justo lo que un operador compara contra la posición del cráter. El módulo tiene FICHA SDA y física validada; solo falta el cableado (la memoria del proyecto lo lista como pendiente).

*Fix sugerido:* Aplicar parallax_correct_field(lat, lon, field_m) en la salida de los 3 retrievals de altura (donde ya se tiene lat/lon/height por pixel) antes de exponer field_km al dashboard, con un flag en el dict de salida ('parallax_corrected': True) para trazabilidad.

### `src/process/wen_rose_height.py:490` — medium/conf=high · test-coverage

**El guard de 'bandas del mismo scan' (fix C1 del audit jul-2026) no tiene test ni en wen_rose_height (línea 490) ni en wind_shear_height (_ash_mask_at, línea 189): ningún test construye bandas C11/C14/C15 de scans distintos.**

El fix C1 evita que con S3 a medio subir se mezclen bandas de scans distintos (máscara de ceniza espuria → centroide falso → advección inventada). En el fixture synthetic_s3 (tests/test_orchestration_and_guards.py:117) _scan_start se monkeypatchea a una constante, así que las 3 bandas siempre comparten scan y la rama del guard (return None / status no_data con reason 'scans distintos') jamás se ejecuta. Si una regresión invirtiera la condición (len(scans) > 1 → >= 1) o la eliminara, la suite seguiría verde y el modo de fallo real que motivó el fix volvería sin síntomas.

*Fix sugerido:* En test_orchestration_and_guards.py, agregar un test que monkeypatchee _scan_start para devolver timestamps distintos según la banda del filename (p.ej. C14→12:00, C15→12:10) y verifique que wen_rose_top_height devuelve status no_data con reason de scans distintos, y que wind_shear _ash_mask_at devuelve None.

### `src/process/wen_rose_height.py:392` — medium/conf=high · funcion-monolitica

**wen_rose_top_height son ~330 líneas con ~10 responsabilidades; los guards de honestidad (el corazón del SDA) solo son testeables vía integración**

La función (líneas 392-724) encadena: resolución de volcán, descarga de 4 bandas, ventana geos, guard mismo-scan, máscara, contexto SO2, perfil GFS, estimación de Ts con 3 fallbacks, β-ratios de composición, solve, reversión de no-confiables, banda de incertidumbre por β, veredicto CO₂, construcción de ~8 flags de honestidad y el score de confianza. Los helpers puros existen (solve_tc_grid, _top_stats, co2_verdict...) pero el ENSAMBLE de flags (líneas 662-709) — que es lo que el operador lee para decidir cuánto creerle al número — está inline y solo se ejercita descargando datos reales. Un cambio en un flag no tiene test unitario que lo proteja.

*Fix sugerido:* Tras extraer la adquisición compartida (hallazgo del preámbulo triplicado), extraer también `_assemble_flags(...) -> list[str]` y `_uncertainty_band(...)` como funciones puras con tests directos de cada rama (n_reverted>0 × veredicto CO₂ × ts_source). La función principal queda como orquestador de ~80 líneas.

### `tests/test_gfs_archive.py:117` — medium/conf=high · test-red-nunca-corre-en-ci

**Los tests de contrato del dato real de gfs_archive y de FIRMS hacen skip PERMANENTE en CI: eccodes solo está en el extra opcional [archive] (tests.yml instala requirements.txt) y FIRMS_MAP_KEY no está seteado en ningún workflow.**

tests.yml (líneas 33-39) instala requirements.txt + pytest; eccodes/cfgrib viven solo en pyproject.toml extra 'archive' (pyproject.toml:29), así que _deps_ok() siempre da False en CI → test_fetch_gfs_profile_archive_lascar y test_fetch_gfs_wind_profile_archive_lascar (tests/test_gfs_archive.py:117,147) jamás corren ahí. test_fetch_viirs_firms_live (tests/test_viirs_firms.py:87) requiere FIRMS_MAP_KEY, que no aparece en ningún workflow de .github/workflows/. Estos tests solo corren si alguien los ejecuta a mano en la máquina de validación — el contrato del dato real (formato .idx, grilla 0.25°, esquema CSV FIRMS) puede romperse aguas arriba sin que CI lo detecte, y el skip verde da sensación de cobertura que no existe.

*Fix sugerido:* Opción mínima: job semanal (schedule) en tests.yml que instale '.[archive]' y exporte FIRMS_MAP_KEY desde un secret, corriendo solo los tests marcados de red (pytest -m red). Opción alternativa: documentar explícitamente en los docstrings que solo corren en la máquina de validación y agregar un reporte de skips al summary del workflow para que el skip permanente sea visible.

### `tests/test_smoke.py:20` — medium/conf=high · test-coverage

**El smoke test de imports (cuyo propósito declarado es atrapar ImportError que dejan el deploy en pantalla blanca) omite la vista backfill_viewer —usada en app.py:304— y todos los módulos nuevos de jun-jul 2026 (goes_lvtp, gfs_archive, viirs_firms, viirs_gibs, granule_select, wen_rose_height, wind_shear_height, parallax, beta_ratios, geocolor_lite, hires_pipeline).**

VIEWS (tests/test_smoke.py:20-37) lista 14 vistas pero dashboard/views/ tiene 15: falta dashboard.views.backfill_viewer, que app.py importa en runtime (dashboard/app.py:304) — un ImportError ahí rompe esa página en producción sin que CI lo vea, exactamente el modo de fallo que el docstring del test dice prevenir (imports cross-package top-level frágiles en deploy, gotcha documentado del proyecto). FETCHERS y PROCESSORS tampoco incluyen los módulos nuevos: src.fetch.goes_lvtp, gfs_archive, viirs_firms, viirs_gibs, granule_select, historic_rammb, animation_cache y src.process.wen_rose_height, wind_shear_height, parallax, beta_ratios, geocolor_lite, hires_pipeline, historic_l1b_rgb. Varios se importan lazy desde vistas, así que un error de import solo aparecería al click del usuario.

*Fix sugerido:* Generar las listas dinámicamente (pkgutil.iter_modules sobre dashboard/views, src/fetch, src/process) en vez de mantenerlas a mano, con una lista corta de exclusiones explícitas si algún módulo requiere deps opcionales (gfs_archive importa eccodes solo dentro de función, así que importa limpio).

### `.github/workflows/frp_timeline.yml:7` — low/conf=high · doc-drift

**Comentario de cabecera de frp_timeline.yml dice 'Corre cada 15 min' mientras el cron es cada 10 min**

frp_timeline.yml:7 ('Corre cada 15 min para reflejar la anomalía casi en NRT') vs línea 14 cron '*/10 * * * *' (y el comentario de la línea 13 que sí documenta el cambio a 10). Cabecera interna inconsistente tras el bump de cadencia de jun-2026.

*Fix sugerido:* Corregir la línea 7 a 'cada 10 min'.

### `.github/workflows/frp_timeline.yml:41` — low/conf=high · cicd-consistencia

**Tres workflows corren Python 3.11 (frp_timeline, goes, lascar_pdf) mientras producción y tests pinean 3.12 — el fix del audit W5 quedó a medias**

frp_timeline.yml:41, goes.yml:29 y lascar_pdf.yml:27 usan python-version '3.11'; tests.yml:30 usa '3.12' con comentario '= produccion (pyproject requires-python ==3.12.*; fix audit W5)'; hires_visible_cache.yml:54, backfill_build.yml:55 y hires_loop_backfill.yml:60 también 3.12; Dockerfile:12 python:3.12-slim; INTEGRATION.md:26 dice además 'Python 3.11+' (excluido por pyproject ==3.12.*). Los crons que generan datos de producción (frp_timeline es EL productor del JSON del dashboard) corren en una versión distinta de la validada por CI/deploy — divergencia sutil de comportamiento posible (p.ej. cambios de stdlib/redondeo).

*Fix sugerido:* Unificar los tres workflows a '3.12' y corregir INTEGRATION.md:26 a 'Python 3.12 (pin)'.

### `.github/workflows/goes.yml:90` — low/conf=high · doc-drift

**Si goes.yml se dispara manualmente, genera un STATUS_NRT.md que miente: 'Cron: cada 10 minutos' y 'Dashboard: goesvolcanic.streamlit.app'**

El template embebido escribe 'Cron: cada 10 minutos' (goes.yml:90) y '- **Dashboard**: https://goesvolcanic.streamlit.app' (goes.yml:80), pero el cron está desactivado desde 2026-05-15 (goes.yml:3-11) y el deploy es HF. Un dispatch manual publicaría en main un archivo de estado con cadencia y URL falsas. STATUS_NRT.md ni siquiera existe hoy en el repo, así que el primer run manual lo crearía ya desactualizado.

*Fix sugerido:* Actualizar el template: 'Generado manualmente (cron desactivado 2026-05-15)' y URL del HF Space.

### `.github/workflows/hires_visible_cache.yml:95` — low/conf=high · doc-drift

**Notas de release y comentarios de hires_visible_cache.yml dicen 'cada 30 min' cuando el cron es cada 10 min; además describen un segundo cron a :22 que no existe**

hires_visible_cache.yml:19 cron '*/10 * * * *', pero las notes publicadas en los releases dicen 'Actualizado por hires_visible_cache.yml cada 30 min' (línea 95) y 'Actualizado cada ~30 min' (línea 108); el comentario del paso loop (líneas 79-81) dice '~16 frames a 30 min'. Las líneas 21-23 describen 'Cada 60 min en :22 (offset distinto), modo mono_05km' — ese cron no existe (el schedule único corre ambos modos, líneas 66-70). hires_loop_backfill.yml:101 repite 'cron cada 30 min'. Es texto visible en los releases públicos del repo.

*Fix sugerido:* Unificar todos los textos a 'cada 10 min' y borrar el comentario del cron :22 fantasma.

### `.github/workflows/tests.yml:41` — low/conf=high · doc-drift

**El smoke check de tests.yml se llama 'dashboard.app importable' pero importa dashboard.style/dashboard.utils, y su comentario aún habla del deploy a Streamlit Cloud**

tests.yml:41-44: name 'Smoke check — dashboard.app importable' pero el comando es `python -c "import dashboard.style; import dashboard.utils"` — nunca importa dashboard.app, así que un error de sintaxis/import top-level en app.py pasa el smoke check con nombre engañoso. El comentario (línea 43) dice 'Si esto falla, el deploy a Streamlit Cloud queda con pantalla en blanco' — plataforma deprecada. Además el job instala requirements.txt completo (con cartopy no usado) alargando cada push a main.

*Fix sugerido:* Renombrar el step (o importar realmente dashboard.app si es seguro fuera del runtime Streamlit), actualizar el comentario a HF, y depurar requirements tras resolver las deps muertas.

### `.gitignore:39` — low/conf=high · config

**.gitignore y .dockerignore excluyen out_backfill/, out_hires/ y out_animation_cache/ pero no out_hires_loop/, que también generan los scripts**

.gitignore:39-43 y .dockerignore:13-16 listan los tres primeros output dirs; build_hires_loop_cache.py (usado por hires_visible_cache.yml:81 y hires_loop_backfill.yml:68) escribe out_hires_loop/, que al correr local quedaría como untracked (riesgo de commit accidental de PNGs pesados) y entraría al build context de Docker.

*Fix sugerido:* Agregar out_hires_loop/ a ambos archivos.

### `CLAUDE.md:53` — low/conf=high · doc-drift

**CLAUDE.md se contradice: línea 53 dice 'STATUS_NRT.md lo regenera el bot cada 10 min' pero líneas 71-74 documentan el cron desactivado desde 2026-05-15 (y STATUS_NRT.md no existe)**

CLAUDE.md:53 (Filosofía operacional: 'STATUS_NRT.md lo regenera el bot cada 10 min — NO mezclar') vs CLAUDE.md:71-74 (goes.yml 'cron DESACTIVADO desde 2026-05-15... nadie consume STATUS_NRT.md'). `ls STATUS_NRT.md` confirma que el archivo no está en el repo. Instrucción vinculante para el agente que describe un pipeline muerto como activo — puede inducir decisiones erradas en sesiones futuras (p.ej. 'no tocar STATUS_NRT porque lo pisa el bot').

*Fix sugerido:* Reescribir la línea 53: 'STATUS.md es curado por humanos; STATUS_NRT.md solo lo generaría goes.yml en dispatch manual (cron desactivado 2026-05-15)'.

### `INTEGRATION.md:47` — low/conf=medium · doc-drift

**Retención RAMMB inconsistente entre docs: INTEGRATION.md dice '~9-10 meses (medido)' y backfill_build.yml dice '~360 dias'**

INTEGRATION.md:47 y :161-162 ('RAMMB RGB ~9-10 meses, medido jun-2026: frame OK a 270d') vs .github/workflows/backfill_build.yml:5 ('RAMMB archive ~360 dias'). 270 días ≈ 9 meses ≠ 360 días; un operador que planifique un backfill confiando en el comentario del workflow puede pedir una fecha fuera del archive real y obtener un run vacío (el flag --l1b-fallback existe justamente para eso pero el workflow no lo menciona).

*Fix sugerido:* Unificar a la cifra medida (~270 días / 9-10 meses) en el comentario del workflow y mencionar el fallback L1b.

### `README.md:92` — low/conf=high · doc-drift

**La sección 'Estructura' del README muestra un árbol de 1 fetcher y 4 módulos de proceso; el repo real tiene 20 fetchers, 15 módulos de proceso y 16 vistas**

README.md:92-105 lista solo src/fetch/goes_s3.py y process/{brightness_temp,ash_rgb,ash_detection,geo}.py + dashboard/app.py. El árbol real: src/fetch/ con 20 módulos (rammb_slider, volcat_api, gfs_profile, goes_acha, goes_lvtp, gfs_archive, viirs_*, etc.), src/process/ con 15 (wen_rose_height, bt_matching_height, beta_ratios, parallax, hires_pipeline...), dashboard/views/ con 16 vistas, src/export/. Para un repo que se presenta como reproducible/auditables (paper §6), el mapa de entrada está 10x desactualizado — quien busque dónde vive la altura de pluma no la encuentra desde el README.

*Fix sugerido:* Regenerar el árbol (aunque sea resumido por carpeta con conteos) o linkear a INTEGRATION.md como mapa canónico.

### `dashboard/views/modo_evento.py:271` — low/conf=high · duplicacion-views

**La tarjeta KPI HTML inline (background:#0f1418 + border-left de color) está copiada 14 veces en 8 vistas pese a existir style.kpi_card**

Grep verificado: modo_evento.py ×4 (líneas 271-324), modo_guardia.py ×4, y 1 copia en modo_guardia_volcan, comparador, backfill_viewer, mosaico_chile, replay_reciente y zonas_fullscreen. dashboard/style.py:482 define kpi_card pero las vistas re-arman el HTML a mano porque necesitan variantes (sub-label, color dinámico del borde). Cambiar el estilo de las tarjetas (petición típica de sala) hoy son 14 ediciones.

*Fix sugerido:* Extender style.kpi_card con parámetros `sublabel: str = ''` y `accent_color: str | None` y migrar las 14 instancias; es un cambio mecánico de bajo riesgo.

### `dashboard/views/zonas_fullscreen.py:1150` — low/conf=medium · carga-productor

**TV_VOLCAN_ZOOMS 2->5 multiplica x2.5 el trabajo del productor cada bucket de 5 min (15 fetches + 5 composiciones PIL que retienen el GIL)**

El loop del productor (lineas 1150-1158) compone _volcan_zoom_png para cada nombre de zooms; con 5 volcanes son 15 fetches RAMMB/hi-res (3 por volcan, _volcan_zoom_png lineas 795-796) y 5 composiciones PIL por cada bucket de 5 minutos. El propio archivo documenta (lineas 1166-1168) que las composiciones PIL retienen el GIL y trababan la navegacion en HF — ese costo ahora ocurre 2.5x mas seguido/mas largo. Ademas un ciclo frio completo de _produce_once (3 RGB + VOLCAT + 5 zooms + eumetsat_ash ~54s) puede superar largamente TV_PRODUCER_PERIOD_S=20s, retrasando el refresco de los primeros slots. Vale el esfuerzo porque la sala corre 24/7 en hardware compartido (HF free tier) donde los picos de GIL se traducen en jank visible para todos los usuarios del proceso.

*Fix sugerido:* Escalonar las composiciones (una por iteracion del loop del productor en round-robin) o insertar time.sleep(0) / pausas cortas entre volcanes para ceder el GIL; medir el tiempo de _produce_once y loguearlo si supera el periodo.

### `dashboard/views/zonas_fullscreen.py:605` — low/conf=high · documentacion-sda

**Docstring de _render_volcat_zoom_tv afirma que el productor mantiene caliente el cache porque 'ambos resuelven a Chile_Central' — falso desde que el PR sumo Calbuco (sector dedicado)**

Lineas 604-606: 'Sirve plotly desde el cache que mantiene caliente el productor (ambos resuelven a Chile_Central -> un solo frame)'. Escrito cuando TV_VOLCAN_ZOOMS eran solo Villarrica y Chillan (jun-2026). Con la lista de 5 (linea 843), Calbuco resuelve a Calbuco_1_km y el supuesto de diseño documentado ya no se cumple (ver hallazgo principal). En un proyecto SDA donde los comentarios que+por que son vinculantes (CPLT 372), un docstring que documenta una garantia de no-bloqueo inexistente puede hacer que la proxima sesion agregue mas volcanes con sectores dedicados (Copahue_250_m, Planchon-Peteroa_500_m estan mapeados) creyendo que el productor los cubre, agravando el bloqueo del fragment.

*Fix sugerido:* Reescribir el docstring: enumerar que sectores calienta el productor hoy y advertir explicitamente que agregar volcanes con sector dedicado a TV_VOLCAN_ZOOMS requiere sumar ese sector al warm-up de _produce_once (o aplicar el fix del hallazgo 1 y documentar que el warm-up deriva de la lista).

### `pyproject.toml:29` — low/conf=medium · deps-no-usadas

**El extra [archive] declara cfgrib>=0.9 pero el código solo importa eccodes — cfgrib parece quedar sin uso**

pyproject.toml:29 archive = ["cfgrib>=0.9", "eccodes>=2.40"]. Grep en src/ y scripts/: solo `import eccodes` (src/fetch/gfs_archive.py:177, tests/test_gfs_archive.py:108); ningún `import cfgrib` ni engine='cfgrib' en xarray. REGISTRO_PAPER.md:88-89 también menciona solo eccodes como decodificador. cfgrib arrastra su propia cadena y confunde sobre qué decodifica realmente el GRIB2. Confianza media: pudo dejarse a propósito como conveniencia para exploración manual.

*Fix sugerido:* Quitar cfgrib del extra archive (o comentar por qué se mantiene).

### `requirements.txt:11` — low/conf=medium · deps-no-usadas

**matplotlib en requirements.txt del deploy solo lo usa scripts/generate_lascar_report.py, que no se deploya al Space**

requirements.txt:11 (matplotlib>=3.8.0). Único consumidor en el repo: scripts/generate_lascar_report.py:28-30 (grep de import matplotlib en dashboard/ y src/ = 0 matches), que corre en lascar_pdf.yml con requirements_actions.txt (donde sí corresponde, línea 13). deploy_hf.sh:63-80 no incluye ese script en el orphan branch, así que el Space instala matplotlib sin usarlo. Confianza media por si algún import lazy no grep-eable lo usa (no encontré ninguno).

*Fix sugerido:* Mover matplotlib fuera de requirements.txt (queda solo en requirements_actions.txt).

### `scripts/build_frp_timeline.py:115` — low/conf=medium · eficiencia

**El pre-check usa el timestamp objetivo y el dedupe usa el timestamp real del scan: un hueco permanente de FDCF hace que ese target se re-descargue en cada corrida, para siempre.**

La línea 115 saltea la descarga si `target.strftime(ISO) in existing`, pero la clave que se guarda es `_round_to_step(scan_dt, step_min)` (línea 124), derivada del gránulo realmente elegido. Cuando NOAA no publicó el scan de un slot (hueco permanente en el archivo), `nearest_granule_key` devuelve el gránulo vecino, la clave resultante ya existe y el flujo cae en `continue` en la línea 126 — pero la descarga y el recorte del gránulo (línea 118) YA se pagaron. Como el `target` nunca llega a `existing`, esto se repite en las 144 corridas diarias del workflow `frp_timeline.yml` mientras ese slot esté dentro de `--backfill-hours`. No afecta la correctitud del dato, sólo el tiempo/ancho de banda de cada corrida.

*Fix sugerido:* Registrar los targets ya intentados (p.ej. una lista `misses` persistida en el JSON, o guardar un `{'t': target, 'alias_of': key}`) para que el pre-check barato los reconozca; o, más simple, apoyarse en un tope de |Δt| en `nearest_granule_key` y anotar el slot como 'sin dato' cuando el gránulo más cercano excede la tolerancia.

### `scripts/deploy_hf.sh:80` — low/conf=medium · config

**deploy_hf.sh empaqueta al Space archivos que el runtime no necesita (tests/, requirements_actions.txt, 4 scripts de build de CI)**

deploy_hf.sh:63-80 agrega tests/, requirements_actions.txt y scripts/build_{hires_cache,animation_cache,backfill,frp_timeline}.py al orphan branch del Space. Ninguno se ejecuta en el contenedor (el CMD del Dockerfile solo corre streamlit; los builds corren en Actions). No rompe nada, pero agranda el snapshot/imagen y contradice el espíritu del propio script ('SOLO archivos esenciales', línea 62). Confianza media: puede ser deliberado para debugging in-Space.

*Fix sugerido:* Quitar tests/, requirements_actions.txt y los scripts de build de la lista de git add (o comentar por qué se incluyen).

### `src/borders.py:1` — low/conf=high · codigo-muerto

**src/borders.py (164 líneas de coordenadas) no tiene ningún consumidor de código — fue reemplazado por dashboard/chile_geometry.json**

Verificado con grep sobre src/, dashboard/, scripts/, tests/ y .github/: las únicas menciones a src.borders son dos líneas de comentario en dashboard/map_helpers.py:7-8 ('El modulo src.borders sigue existiendo por si otro proyecto del ecosistema lo necesita'). Ningún import en ningún .py del repo. La geometría vigente (Natural Earth 10m, 4541 vértices) vive en chile_geometry.json con carga lazy (_load_geo, map_helpers.py:29-49); borders.py es la versión vieja de ~80 puntos. Mantener dos fuentes de la frontera invita a que un futuro consumidor use la desactualizada.

*Fix sugerido:* Borrar src/borders.py (git conserva la historia si otro proyecto lo necesitara) y actualizar el comentario de map_helpers. Si de verdad hay un consumidor externo, documentarlo en INTEGRATION.md en el mismo commit.

### `src/fetch/frp_timeline.py:199` — low/conf=medium · gestion-de-recursos

**Los Datasets abiertos con `xr.open_dataset(f)` nunca se cierran en los lectores nuevos; el barrido de ~144 scans/corrida los acumula.**

En `fetch_scan_sliced` el dataset se crea dentro del `with s3.open(chosen,'rb') as f:` (src/fetch/frp_timeline.py:198-199) y nunca se cierra: al salir del `with` se cierra el file-like de s3fs pero el objeto `Dataset` (y el handle h5netcdf que lo respalda) quedan vivos hasta que el GC los recoja. El mismo patrón está en src/fetch/goes_fdcf.py:330, src/fetch/goes_acha.py:244 y src/fetch/goes_lvtp.py:270. Correctitud del dato: OK — verifiqué que todas las lecturas (`.values`, `.isel(...).values`) ocurren DENTRO del `with`, así que no hay lectura sobre un archivo cerrado. El riesgo es de recursos: `scripts/build_frp_timeline.py` con `--rollup-days` puede abrir cientos de gránulos en un solo proceso, y en el dashboard de larga vida se acumula por cada refresco.

*Fix sugerido:* Usar `with s3.open(chosen,'rb') as f, xr.open_dataset(f, engine='h5netcdf') as ds:` en los cuatro lectores. Es un cambio de una línea por sitio y no altera la semántica, porque todas las materializaciones ya son internas al bloque.

### `src/fetch/gfs_archive.py:208` — low/conf=high · test-coverage

**El fallback de _resolve al ciclo GFS anterior y el retry de _read_range no tienen tests, pese a ser testeables con un fake s3 (mismo patrón que _retry_s3, que sí tiene 4 tests).**

_resolve (líneas 208-223) implementa 'si el idx del ciclo más cercano falta, usar el ciclo anterior y recalcular gap_min' — sin test, un error en el recálculo del gap (p.ej. usar el gap del ciclo original) reportaría time_gap_min engañoso en el perfil, dato que los scripts de validación usan para juzgar frescura. _read_range (131-145) reintenta byte-ranges 4 veces; su contrato (reintenta transitorio, relanza la última) es paralelo a goes_s3._retry_s3, que tiene test_s3_retry.py completo — la asimetría muestra que el patrón de test existe pero no se aplicó aquí.

*Fix sugerido:* Test de _resolve con un fake s3 cuyo cat lance Exception para el ciclo N y devuelva idx válido para N-1: verificar que cycle_dt retrocede 6 h y que gap_min se recalcula contra el ciclo usado. Test de _read_range con un fake que falle 2 veces y luego devuelva bytes.

### `src/fetch/gfs_archive.py:145` — low/conf=high · manejo-de-errores

**`raise last` puede lanzar `None` (TypeError enmascarando el error real) si el conteo de reintentos es 0.**

En `_read_range` (gfs_archive.py:137-145) `last` se inicializa en `None` y sólo se asigna dentro del `except`; si `retries` llega como 0 o negativo, el `for` no itera y se ejecuta `raise last` con `last is None` → `TypeError: exceptions must derive from BaseException`, que oculta por completo el problema real. Idéntico patrón en `_retry_s3` (src/fetch/goes_s3.py:55-65) si `_S3_RETRIES` se bajara a 0. `retries` es un parámetro público de `_read_range`, así que un llamador puede provocarlo hoy.

*Fix sugerido:* Reemplazar por `raise last if last is not None else RuntimeError(f'sin intentos de lectura para [{start},{end}]')`, o validar `retries = max(1, int(retries))` al entrar. Mismo tratamiento en `_retry_s3`.

### `src/fetch/goes_acha.py:111` — low/conf=high · duplicacion-geometria

**El cálculo bbox lat/lon → ventana de índices en la grilla fija ABI existe en 3 implementaciones paralelas con márgenes y muestreos distintos**

goes_acha._geos_index_bbox:111-154 (malla 25×25, margin_px=2, filtra por valor), frp_timeline._chile_xy_index_range:126-162 (malla 6×6, margin_rad=0.003, índices inclusivos) y hires_pipeline._scope_pixel_bounds:81-131 (9 puntos, margin=5 px, argmin) resuelven el mismo problema con la misma proyección geos. Las diferencias (densidad del borde muestreado, convención inclusivo/exclusivo) son accidentales, no de diseño, y ya obligaron a documentar en cada una por qué funciona. rammb_slider.get_tiles_for_bounds:88-143 es una 4ª variante en espacio de tiles. Si aparece un bug de encuadre (como los históricos de georef del proyecto) hay que cazarlo en 4 lugares.

*Fix sugerido:* Unificar el núcleo (proyectar malla del borde del bbox → rango de índices por valor, con margen configurable) en el módulo abi_common propuesto; cada caller conserva solo su envoltorio (snap a múltiplos de 4 en hires, conversión a tiles en rammb).

### `src/fetch/goes_acha.py:227` — low/conf=medium · contrato-errores-inconsistente

**Convenciones de error dispares entre fetchers: None vs ([], None) vs dict{note} vs lista parcial silenciosa — el caller debe memorizar el contrato de cada uno**

goes_acha/goes_lvtp devuelven None en todo fallo (goes_acha.py:227-239); goes_fdcf devuelve ([], None) (goes_fdcf.py:194-200) donde 'sin datos' y 'sin hotspots reales' solo se distinguen por scan_dt; volcat_height_at devuelve dict con 'note' explicativa o None según la clase de fallo (volcat_api.py:379-399); fetch_wind_grid omite puntos fallidos y devuelve lista parcial sin señal (wind_data.py:148-150); timeseries devuelve [] . Para un SDA cuya contribución es 'declinar honestamente', el patrón dict-con-note de volcat_height_at es el único que le llega al operador con el POR QUÉ; los None silenciosos se renderizan como 'sin datos' indistinguible de 'no hay pluma'.

*Fix sugerido:* No hace falta refactor masivo: documentar el contrato en el docstring de cada fetcher y, al tocar cada módulo por los otros hallazgos, migrar gradualmente a devolver una razón legible (patrón note) en los paths donde el dashboard hoy muestra un vacío ambiguo (p.ej. ACHA sin gránulo vs bbox fuera de disco).

### `src/fetch/goes_fdcf.py:43` — low/conf=high · constantes-duplicadas

**El fallback try/except con -75.0 y 35786023.0 hardcodeados está copiado en 6-7 módulos: un cambio de satélite exige tocar todos**

El patrón `try: from src.config import GOES19_SAT_LON... except: _SAT_LON_DEFAULT=-75.0; _H_DEFAULT=35786023.0` aparece en goes_fdcf.py:43-48, goes_acha.py:50-55, rammb_slider.py:55-62, historic_rammb.py:42-43, parallax.py:38-40, hires_pipeline.py:56-58, más el inline de goes_lvtp.py:272-273. El fallback nació como defensa del hot-reload de Streamlit Cloud (deploy hoy es HF, donde el problema documentado era otro), pero el efecto neto es que la posición del satélite vive en 8 lugares. El propio proyecto ya sufrió el costo de un sat_lon desactualizado (-75.2 de GOES-16 producía offset de ~17 km, comentario en rammb_slider.py:239-243). Cuando GOES-19 sea reemplazado, alcanza con olvidar UNA copia para reintroducir ese offset silencioso.

*Fix sugerido:* Crear un módulo hoja sin dependencias (src/abi_constants.py) con SAT_LON/H/ABI_MAX y que src/config lo re-exporte; los módulos importan de ahí SIN fallback (un módulo hoja no puede fallar por import cross-package). Los try/except desaparecen.

### `src/fetch/goes_fdcf.py:160` — low/conf=high · convencion-constantes

**_abi_to_latlon usa el H default hardcodeado en vez del perspective_point_height del NetCDF, mientras sat_lon sí se lee del archivo**

En goes_fdcf.py:160 `h = _H_DEFAULT` es fijo, pero las funciones caller sí extraen `longitude_of_projection_origin` del NetCDF (líneas 214-219, 337-341) y lo pasan como parámetro. Es una asimetría con la convención del proyecto ('coeficientes/parámetros siempre del NetCDF L1b') que goes_acha sí respeta (lee ambos, goes_acha.py:246-247). En la práctica H no varía para GOES-19, pero la convención existe justamente para que un cambio de plataforma no requiera memoria humana.

*Fix sugerido:* Agregar parámetro `H` a _abi_to_latlon y pasarle el leído del archivo en los 3 callers (los dos de goes_fdcf y el de frp_timeline).

### `src/fetch/goes_lvtp.py:283` — low/conf=high · contrato-dims

**El fetcher asume orden de dims LVT=(y,x,pressure) sin forzarlo; el contrato solo se verifica en un test de red que se skipea offline**

_clear_sky_profile indexa lvt[clear] con una mascara 2D (y,x) sobre los dos primeros ejes (linea 157-160), lo que requiere que el array llegue como (y,x,pressure). fetch_lvtp_profile lee ds['LVT'].isel(y=...,x=...).values sin transpose (linea 283-284), confiando en el orden del archivo. test_lvtp_granule_contract lo asserta pero es un test de red con skipif. Si NOAA reordenara dims en una version del producto (paso NCCF anunciado para 2026), el fallo seria un IndexError ruidoso en produccion (no silencioso, por eso mejora y no bug), pero un transpose explicito lo hace inmune y documenta la dependencia en el codigo, no solo en el comentario.

*Fix sugerido:* Usar ds['LVT'].isel(...).transpose('y','x','pressure').values en fetch_lvtp_profile: costo nulo (no-op si ya viene en orden) y convierte el supuesto en invariante.

### `src/fetch/goes_lvtp.py:159` — low/conf=medium · warnings-cosmetico

**np.errstate(invalid='ignore') no suprime el RuntimeWarning 'All-NaN slice' de nanmedian: la intencion de silenciar no se cumple**

En _clear_sky_profile, cuando TODOS los pixeles claros tienen NaN en algun nivel, np.nanmedian emite 'RuntimeWarning: All-NaN slice encountered' via el modulo warnings, que np.errstate no captura (errstate solo gobierna errores de punto flotante del FPU). El resultado (NaN, luego filtrado por isfinite en la linea 164) es correcto — solo queda ruido en logs/stderr en ventanas con niveles enteramente faltantes, contradiciendo la intencion evidente del with errstate.

*Fix sugerido:* Envolver con warnings.catch_warnings() + simplefilter('ignore', RuntimeWarning) acotado a la llamada a nanmedian, o quitar el errstate y comentar que el All-NaN esta manejado aguas abajo por el filtro isfinite.

### `src/fetch/hires_loop_cache.py:31` — low/conf=high · duplicacion-contrato-implicito

**La función slug que une productor y consumidor del cache hi-res está copiada 3 veces; si una copia diverge, los assets del release dejan de encontrarse silenciosamente**

`"".join(c if c.isalnum() else "_" for c in name.lower())` existe como hires_cache._slugify:45, hires_loop_cache._slug:31 y scripts/build_hires_loop_cache._slug:52. El script GENERA los nombres de asset del release (`{slug}__geocolor05.zip`) y los módulos de src los CONSUMEN: el slug es un contrato de datos, no un helper cosmético. Una edición en una sola copia (p.ej. manejar tildes distinto) rompería el matching sin error — el dashboard solo vería 'sin cache' para ese volcán.

*Fix sugerido:* Definir `slugify_volcano(name)` una sola vez (p.ej. en src/volcanos.py, junto al CATALOG cuyos nombres transforma) e importarla en los 3 sitios, con un test que fije el slug de los 8 volcanes prioritarios.

### `src/fetch/viirs_firms.py:110` — low/conf=medium · codigo-sin-integrar

**fetch_viirs_firms_hotspots no tiene ningún consumidor fuera de sus tests — el ingreso VIIRS 'liviano' para volcanes australes quedó a medio cablear**

Grep sobre dashboard/ y scripts/ no encuentra ningún uso de viirs_firms (solo tests/test_viirs_firms.py); viirs_gibs al menos tiene scripts/viirs_patagonia_snapshots.py. La memoria del proyecto documenta la intención ('VIIRS ingerido vía liviana (GIBS imagen + FIRMS térmico) para australes') pero ninguna vista muestra hoy los hotspots FIRMS. El costo es doble: código que se mantiene sin producir valor, y la cobertura térmica austral (donde FDCF es más débil por la vista oblicua) sigue sin la fuente complementaria que ya está implementada y testeada.

*Fix sugerido:* Decidir explícitamente: (a) cablear fetch_viirs_firms_hotspots a la vista de guardia/mosaico para volcanes con lat < -42 (el caso de uso documentado), o (b) marcar el módulo como experimental en su docstring y en INTEGRATION.md hasta que se integre.

### `src/fetch/viirs_gibs.py:131` — low/conf=medium · semantica-de-metrica

**`.convert('RGB')` descarta el canal alfa de GIBS, así que `coverage_frac` confunde "escena oscura" con "la pasada no cubrió la caja".**

Verifiqué contra GIBS en vivo: las respuestas llegan en modo RGBA (thermal 256x256 → todo transparente con RGB (0,0,0); truecolor → RGB válido). El código hace `Image.open(...).convert('RGB')` (viirs_gibs.py:131), tirando el alfa, y luego `_coverage_frac` mide 'fracción de píxeles cuya suma RGB > 10' (viirs_gibs.py:74-81), cuya docstring afirma 'para True Color, 0 = la pasada no cubrió la caja ese día'. Pero un píxel CUBIERTO y legítimamente oscuro —agua profunda, sombra de nube, terminador/noche, la capa DayNightBand sin luces— tiene alfa=255 y suma RGB baja, así que se cuenta como no-cubierto. El alfa es exactamente la señal de cobertura que GIBS ya provee y se está descartando. Impacto acotado (el producto es INDICATIVO y no entra a la cadena ABI), pero el número se usa para decidir si mostrar el snapshot en scripts/viirs_patagonia_snapshots.py:59-61.

*Fix sugerido:* Conservar RGBA: `im = Image.open(io.BytesIO(r.content)); rgba = np.asarray(im.convert('RGBA'))`, devolver `image` como RGB (compat) y calcular `coverage_frac` sobre `rgba[..., 3] > 0`. Si se quiere seguir midiendo 'píxeles con señal' para el overlay térmico, exponer las dos métricas por separado (`coverage_frac` desde alfa, `signal_frac` desde luminancia) y actualizar tests/test_viirs_gibs.py:55-63, que hoy pinea la semántica de luminancia.

### `src/fetch/viirs_gibs.py:68` — low/conf=medium · parseo-de-formato-externo

**Las coordenadas del BBOX se formatean con `:g`, que trunca a 6 cifras significativas y emite notación científica para |valor| < 1e-4.**

`_getmap_params` construye el BBOX con `f"{bbox['lat_min']:g},..."` (viirs_gibs.py:68-69) y `viirs_firms._bbox_to_area` hace lo mismo (src/fetch/viirs_firms.py:48-49). `%g` usa 6 cifras significativas: para las latitudes/longitudes chilenas (~-73.5683) el redondeo es de ~1e-5° (~1 m), irrelevante. El problema latente es la notación científica: un valor como 0.00005 se serializa como '5e-05', string que ni el parámetro BBOX de WMS ni el segmento 'area' de FIRMS aceptan → GetMap devuelve ServiceException y FIRMS un 400. Sólo se dispara cerca del ecuador o del meridiano de Greenwich, o sea nunca para el RNVV chileno; queda como trampa si estos fetchers se reutilizan para otro dominio (el módulo se presenta como genérico por lat/lon).

*Fix sugerido:* Usar un formato de punto fijo explícito y determinista, p.ej. `f"{v:.6f}"`, en ambos helpers. Los tests tests/test_viirs_gibs.py:37 y tests/test_viirs_firms.py:34 pinean la representación actual, así que hay que actualizarlos junto con el cambio.

### `src/fetch/volcat_api.py:318` — low/conf=high · duplicacion

**volcat_latest y volcat_at_time duplican el armado del dict de resultado (las 5 URLs de imagen/leyenda/overlays construidas dos veces)**

Las líneas 248-261 y 317-330 arman el mismo dict (image_url, annot_url, legend_url, latlon_url, volcanoes_url, coords, sector, instr, image_type) a partir de un frame; solo difieren en el campo extra (sat vs gap_seconds). Un cambio en el layout de URLs de SSEC (que ya cambió antes) hay que aplicarlo en 2 lugares. Además el mismo patrón de fallback `if not frames and sat != 'all'` está copiado en ambas (239-243 y 301-302).

*Fix sugerido:* Extraer `_frame_to_result(frame, sector, instr, image_type, coords) -> dict` y `_query_frames_with_fallback(sector, instr, image_type, sat)`; ambas funciones públicas quedan de ~10 líneas.

### `src/fetch/volcat_api.py:402` — low/conf=medium · eficiencia-memoria

**volcat_height_at convierte el PNG completo del sector a float64 antes de recortar el bbox del volcán**

La línea 402 hace `a = np.asarray(im).astype("float64")` sobre la imagen entera del sector (los sectores Chile 2 km son del orden de 2000×2500×3 → ~120 MB en float64) cuando después solo se usan el strip del colorbar (línea 404) y el box de ±radius_deg (línea 426, típicamente <300×300 px). En el proceso Streamlit compartido de HF, picos así por llamada suman presión de memoria evitable.

*Fix sugerido:* Mantener el array como uint8 y convertir a float64 solo los recortes (strip y box) después del slicing: `box = a_uint8[r0:r1, c0:c1].astype('float64')`. Cambio local de ~4 líneas.

### `src/process/wind_shear_height.py:46` — low/conf=high · constante-aproximada

**M_PER_DEG_LAT=111320 es el valor ecuatorial de LONGITUD; para latitud el valor correcto es ~111132-111694 (error <0.5%)**

111320 m/deg = 2*pi*a/360 con a el semieje mayor, que es metros por grado de LONGITUD en el ecuador. Los metros por grado de LATITUD en el elipsoide van de 110574 (ecuador) a 111694 (polos), ~111600 en -40S. advection_uv (lineas 101-102) usa la misma constante para ambos ejes. El error resultante en (u,v) es <0.5%, despreciable frente al RMSE de 8-17 m/s del viento GFS — lo reporto por cobertura y porque el comentario 'WGS84 aprox.' no aclara que es el valor de longitud aplicado a latitud.

*Fix sugerido:* Dejar constancia en el comentario ('valor ecuatorial de longitud; error <0.5% en el dominio, despreciable vs RMSE del viento') o usar 111132.0 (promedio de latitud) para el eje norte.

### `src/process/wind_shear_height.py:247` — low/conf=medium · robustez-signos

**abs() en dt_s ocultaria una inversion de orden temporal entre scans (adveccion con signo invertido)**

dt_s = abs((cur[3]-prev[3]).total_seconds()): si por un cambio futuro en la seleccion de granulos el scan 'prev' resultara posterior al 'cur', el abs mantiene dt_s>0 pero advection_uv se calcula prev->now con la direccion invertida -> (u,v) con signo opuesto -> el matching elige el nivel con viento OPUESTO al real. Hoy nearest_granule/download_band_at es monotono en el target (prev<=cur siempre, y el caso igual cae en el guard dt_s<=0 de la linea 249), asi que no hay bug activo — es una trampa latente: el abs convierte una violacion de invariante en resultado plausible en vez de en rechazo.

*Fix sugerido:* Reemplazar abs por el valor con signo y rechazar explicitamente si (cur[3]-prev[3]).total_seconds() <= 0 (status no_data, 'orden temporal de scans invertido'), preservando el fallback prev_gap_min*60 solo cuando falta algun scan_dt.

### `src/process/wind_shear_height.py:290` — low/conf=high · codigo-duplicado

**adv_speed se recalcula identicamente en la linea 290 (ya computado en la 253)**

math.hypot(u_obs, v_obs) se evalua en la linea 253 (para los guards MAX_ADV/edad de viento) y de nuevo en la 290 con los mismos operandos inmutables. Sin efecto en resultados (determinista); solo redundancia que invita a divergencia futura si una de las dos lineas cambia.

*Fix sugerido:* Eliminar la reasignacion de la linea 290 y reutilizar la variable ya calculada.

### `tests/test_gfs_archive.py:70` — low/conf=high · assert-debil

**El assert del empate 03:00 en test_cycle_for_nearest_6h acepta ambos resultados (h in ('00','06')) — no pinea el desempate determinista que el propio comentario del test y el docstring de _cycle_for prometen.**

El comentario dice 'round-half va a 00 (más temprano, determinista)' pero el assert pasa con cualquiera de los dos ciclos. Python round() usa banker's rounding sobre round(secs/21600), así que el resultado del empate depende de la paridad del múltiplo — si alguien cambiara round() por floor+0.5 o math.ceil, el comportamiento en el empate cambiaría silenciosamente y el test seguiría verde. Es un caso borde real: scans a las 03:00/09:00/15:00/21:00 UTC equidistan de dos ciclos y el gap_min reportado (180 min en ambos) es igual, por eso severidad baja — pero un assert que acepta ambas ramas documenta indecisión, no contrato.

*Fix sugerido:* Fijar el resultado real actual (calcularlo una vez: para 2026-06-27 03:00 UTC, round(secs/21600) con banker's rounding da un ciclo concreto) y assertarlo exacto, con comentario de por qué; o cambiar _cycle_for a un desempate explícito (p.ej. floor al ciclo anterior) y pinearlo.

### `tests/test_orchestration_and_guards.py:91` — low/conf=medium · test-infra

**No existe conftest.py: la fixture synthetic_s3 (la más valiosa de la suite) está encerrada en test_orchestration_and_guards.py y cada uno de los 22 archivos repite sys.path.insert(0, ...) a mano.**

La ausencia de tests/conftest.py tiene dos efectos: (a) la escena sintética con mocks de S3/GFS no es reusable desde test_bt_matching.py ni futuros tests de ACHA — lo que contribuye directamente al hueco de orquestación de bt_matching_top_height; (b) el boilerplate sys.path.insert duplicado 22 veces significa que un archivo nuevo que lo olvide funcionará o no según el cwd desde el que se invoque pytest (frágil al entorno de invocación). Un conftest.py en tests/ resuelve ambos con ~10 líneas.

*Fix sugerido:* Crear tests/conftest.py con el sys.path.insert único y mover allí synthetic_s3 (y los helpers _scene_bts/_band_ds/COEFS) como fixtures compartidas; eliminar gradualmente los inserts por archivo.

### `tests/test_viirs_gibs.py:74` — low/conf=high · test-fragil-entorno

**_net_ok() (viirs_gibs) y _deps_ok() (gfs_archive) hacen llamadas de red en tiempo de COLECCIÓN sin lru_cache — a diferencia de test_acha/test_lvtp que sí cachean — sumando hasta ~30 s y 3 round-trips por sesión de pytest, multiplicados por worker con xdist.**

El decorador skipif se evalúa al importar el módulo de test: tests/test_viirs_gibs.py:74-83 hace un GetCapabilities a GIBS (timeout 15 s) y tests/test_gfs_archive.py:106-114 hace un s3.ls a noaa-gfs-bdp-pds DOS veces (dos decoradores, líneas 117 y 147, sin functools.lru_cache). test_acha.py:38 y test_lvtp.py:33 documentan y resuelven exactamente este problema con lru_cache — la convención existe en la suite pero no se aplicó a los archivos nuevos. Efecto medido: la colección local tardó 17.7 s (pytest --collect-only). Con -n auto (tests.yml línea 39) cada worker de xdist recolecta y repite las llamadas. Además, correr un solo test puro (pytest tests/test_geo.py) no dispara esto, pero cualquier corrida completa offline espera los timeouts.

*Fix sugerido:* Agregar @functools.lru_cache(maxsize=1) a _deps_ok en test_gfs_archive.py y a _net_ok en test_viirs_gibs.py (mismo patrón que test_acha._s3_ok), y bajar el timeout de GIBS a ~8 s.

### `tests/test_viirs_gibs.py:48` — low/conf=medium · assert-debil

**test_default_date_is_a_date_string solo verifica el formato YYYY-MM-DD, no la semántica 'ayer UTC' que el docstring de _default_date declara como decisión de diseño (el mosaico de hoy puede no estar compuesto).**

src/fetch/viirs_gibs.py:44-47 devuelve deliberadamente ayer UTC porque pedir el mosaico de hoy a GIBS puede devolver tiles vacíos (coverage_frac≈0). Si alguien 'simplificara' a datetime.now().strftime(...) (hoy, y además hora local del host en vez de UTC), el test seguiría verde y el fetcher NRT degradaría a imágenes vacías intermitentes según la hora del día. El test es además la única cobertura de esa función.

*Fix sugerido:* Assertar la semántica: d == (datetime.now(timezone.utc) - timedelta(days=1)).strftime('%Y-%m-%d') (tolerando el borde de medianoche recalculando si no coincide), que pinea tanto el 'ayer' como el uso de UTC.
