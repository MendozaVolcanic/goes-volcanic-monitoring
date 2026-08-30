# Anexo — hallazgos completos, 4ª auditoría (2026-08-30)

> Generado por 6 finders paralelos con lentes distintas. Cada hallazgo lleva
> `severity` y `confidence` **autoevaluados por el finder**: son su criterio, no un
> veredicto. Los que pasaron por verificación adversarial están marcados en el
> reporte principal. Orden: por dimensión, y dentro de cada una por severidad.


## Docs, CI/CD y cumplimiento SDA  ·  24 hallazgos

**Verificado y limpio** (un núcleo sano también es información):

- gh CLI autenticado como MendozaVolcanic: los hallazgos de remote son confidence high (gh run list, gh api commits, gh run view --log del run 33293474960).
- tests/test_workflow_concurrency.py cubre TODOS los workflows que hoy usan ./.github/actions/gh-release-snapshot (animation_cache, hires_visible_cache, hires_loop_backfill, backfill_build), incluido el caso de tag dinamico. Contenido correcto; el problema es que no corre en CI (D2).
- .github/actions/gh-release-snapshot/action.yml: sube con --clobber ANTES de podar huerfanos, guard duro de dir vacio, doble criterio (nombre + updatedAt) para no borrar de mas. Verificado leyendo el script.
- README.md: nota historica sobre Streamlit Cloud, URL HF, frontmatter YAML de HF Spaces y la tabla de 5 productos concuerdan con el codigo.
- Conteo '43 volcanes': CATALOG tiene 48 entradas = 43 chilenas + 5 de zona 'test' (Kilauea, Popocatepetl, Sangay, Reventador, Sabancaya). El conteo publicado es correcto.
- MOSAICO_VOLCANOES (config.py:100) = los 5 que manuals.py 'guardia' nombra. Sin drift.
- manuals.py 'evento': los 5 anillos 5/10/25/50/100 km coinciden con RING_RADII_KM (modo_evento.py:49).
- docs/paper/REGISTRO_PAPER.md esta al dia y es honesto: marca wind_shear_height.py como '(no en produccion aun)'.
- GUIA_REVISION_DASHBOARD.md acierta al declarar el arbitro de cizalla de viento 'no cableado aun' (grep: solo scripts/validate_fase3c.py lo importa).
- pyproject.toml + runtime.txt + .python-version pinean 3.12 de forma consistente; Dockerfile python:3.12-slim; tests.yml 3.12.
- streamlit==1.56.0 con pin exacto y justificacion escrita (chunks JS con hash por version).
- keepalive_hf.yml corre de verdad (runs cada 6 h en gh run list) y hace lo que dice.


### `.github/workflows/frp_timeline.yml:15` — **high**/conf=high

**El pulso intradia de FRP dice cadencia 10 min pero GitHub lo corre cada 2-12 h: falta el 46% de la serie y todos los runs son verdes**

El cron declarado es `- cron: '*/10 * * * *'` (frp_timeline.yml:15) y CLAUDE.md / INTEGRATION.md / manuals.py 'heatmap' repiten '~10 min'. Los runs REALES (gh run list -w frp_timeline.yml): 2026-08-30T02:00, 08-29T23:50, 21:57, 19:41, 17:08, 13:13, 07:24, 00:43, 08-28T16:49, 08-28T04:29 -> huecos de hasta 12.3 h, TODOS con conclusion=success. Los commits remotos de data/frp_timeline.json (gh api .../commits?path=data/frp_timeline.json) tienen exactamente esos timestamps. Contando el JSON commiteado: 156 scans de los 288 que caben en la ventana de 48 h, con huecos internos de 9.67 h (desde 2026-08-28 04:10), 5.17 h, 3.83 h y 3.0 h. Agravante: `--backfill-hours` default '3' (frp_timeline.yml:63; scripts/build_frp_timeline.py:85), asi que un hueco de 9.7 h NO se rellena nunca -- el comentario 'backfill de 3h da solape (auto-sanante si se saltea una corrida)' (frp_timeline.yml:17) es falso con la cadencia real. Nada en el repo mide esto.

*Escenario de fallo:* Villarrica sube FRP a las 05:00 UTC y vuelve a cero a las 13:00. El unico run del dia cae 14:00 y barre solo 3 h hacia atras: el episodio entero queda fuera del JSON para siempre. El geologo abre 'Heatmap actividad', ve la curva plana y el roll-up diario en 0, y concluye 'no paso nada' -- cuando lo que paso es que el cron no corrio. Es el modo de fallo del CONTEXTO: dato ausente leido como calma, con el workflow en verde.

*Fix sugerido:* (a) Subir --backfill-hours al ancho real observado (>=12 h): es barato porque el pre-check salta los scans ya presentes. (b) Escribir en el JSON la cobertura efectiva (scans presentes/esperados por dia) y pintarla en la vista Heatmap: una franja gris de 'sin dato' NO es lo mismo que un cero. (c) No prometer '10 min' en la doc; medir y documentar la cadencia real de GitHub.

### `tests/test_workflow_concurrency.py:21` — **high**/conf=high

**El test que protege los releases rolling NUNCA corre en CI: PyYAML no esta declarado y el modulo se auto-saltea**

El modulo abre con `yaml = pytest.importorskip("yaml")` (linea 21). PyYAML no aparece en requirements.txt, requirements_actions.txt ni pyproject.toml (grep -i yaml sobre los tres: 0 hits). tests.yml instala `pip install -r requirements.txt` + `pytest pytest-xdist`; el log del ultimo run verde (gh run view 33293474960 --log) lista los 'Installing collected packages' completos y PyYAML NO esta. En ese mismo log, `grep -ci concurrency` = 0: ni un test del archivo aparece. Local: 312 tests colectados, 7 en test_workflow_concurrency.py; CI reporta '298 passed, 5 skipped'. El archivo se escribio en el audit ago-2026 justo para impedir que un backfill manual borrara la ventana rodante de 8 h de `hires-loop-rolling`.

*Escenario de fallo:* Alguien agrega un workflow que publica a `animations-rolling` sin `concurrency.group`, o le cambia el grupo a hires_loop_backfill. El PR pasa en verde porque el guard esta salteado. En la primera colision cron-vs-manual el release queda con los assets del otro run borrados y la vista de loops muestra 'sin frames' durante horas. El invariante existe, esta bien escrito, y no protege nada.

*Fix sugerido:* Agregar `pyyaml` a requirements.txt (o a un requirements-dev.txt que tests.yml instale) y reemplazar el `importorskip` por un import duro: un guard que se puede saltear en silencio no es un guard. Auditar con el mismo criterio los otros importorskip de tests/.

### `STATUS.md:3` — **high**/conf=high

**STATUS.md -- el unico estado curado por humanos -- lleva 4 meses congelado y da como 'produccion' un deploy muerto**

Cabecera: '**Ultima actualizacion:** 2026-04-25 (sesion 2)' (linea 3) y '**Deploy en produccion:** https://goesvolcanic.streamlit.app' (linea 9), cuando README.md:22 declara ese mirror abandonado desde jun-2026 y HF como unico deploy oficial. Las lineas 6-8 dicen que STATUS_NRT.md 'lo auto-genera el workflow goes.yml cada 10 min': el cron de goes.yml esta comentado desde 2026-05-15 (goes.yml:11-12) y `ls STATUS_NRT.md` -> No such file. El bloque 'Pendiente' sigue listando como TODO cosas hechas hace meses: Wen-Rose Fase 3 (c802d9a, jun-2026), viento GFS overlay, anillos de distancia, permalinks, loops, comparador. CLAUDE.md declara este archivo 'curado por humanos', o sea que es la version supuestamente confiable.

*Escenario de fallo:* Un colega de OVDAS o un revisor externo abre STATUS.md como puerta de entrada y se va con tres cosas falsas: la URL del sistema (muerta), la creencia de que hay un bot NRT escribiendo cada 10 min (no existe), y una lista de pendientes ya hechos. Si comparte la URL streamlit.app a un turno, el turno se queda sin dashboard en una emergencia.

*Fix sugerido:* O se actualiza STATUS.md en la misma pasada (deploy = HF, borrar la nota de STATUS_NRT, mover a HECHO lo hecho), o se lo declara historico y se apunta la puerta de entrada a INTEGRATION.md, que si esta al dia (last_updated 2026-08-29).

### `docs/GUIA_REVISION_DASHBOARD.md:22` — **high**/conf=high

**La guia de turno describe un dashboard que ya no existe: 4 vistas renombradas o eliminadas y 5 vistas activas sin documentar**

La guia (fecha declarada 2026-07-01) enumera 'Vista por vista': 1. 'En Vivo', 2. 'Mapa General', 3. 'Ash RGB Viewer', 4. 'Detalle Volcan', 5. VOLCAT, 6. 'Animacion (RAMMB)', 7. Series, 8. Backfill. Contra dashboard/app.py:138-157, PAGE_OPTIONS son: Vista Operacional, Modo Guardia, Comparador, Modo Evento, Heatmap actividad, Replay reciente, Backfill historico, Ash + BTD, VOLCAT, Loops descargables, Series. Los propios _SLUG_REDIRECTS (app.py:160-164) confirman los renombres ('live'->'operacional', 'animacion'->'loops'). 'Mapa General' y 'Detalle Volcan' no existen en PAGE_OPTIONS (STATUS.md registra la eliminacion de Detalle Volcan). Quedan sin documentar 5 de 11 vistas: Modo Guardia (la de sala), Modo Evento (la de crisis), Heatmap actividad, Replay reciente y Comparador.

*Escenario de fallo:* Turno nuevo, capacitacion con esta guia. Busca 'En Vivo' en el sidebar y no esta; busca 'Mapa General' y no esta. Peor: nadie le enseña Modo Evento, la pantalla diseñada para 'llamar al jefe en <60 s'. Es el documento dirigido al geologo de guardia, donde el drift duele mas.

*Fix sugerido:* Regenerar la seccion vista-por-vista desde PAGE_OPTIONS/PAGE_SLUGS y agregar un test que falle si un slug de PAGE_SLUGS no aparece en la guia (hay precedente: tests/test_legend_coverage.py).

### `dashboard/manuals.py:62` — **medium**/conf=high

**El manual de Modo Guardia lista 3 sub-tabs de 6, y a dos les pone el nombre equivocado**

manuals.py 'guardia' (lineas 62-95) enumera tres sub-tabs: 'Por Zona Volcanica', 'Mosaico (5 prioritarios)' y 'Volcan (4 productos)'. Los reales son SEIS (modo_guardia.py:972-978): 'Vigilancia diaria', 'Chile (vista nacional)', 'VOLCAT por zona', 'Mosaico 5 prioritarios', 'Volcan (N productos)' y 'Loop 2h'. 'Por Zona Volcanica' ni siquiera es un tab de Modo Guardia: es el tab 2 de Vista Operacional (live_viewer.py:749-753). Faltan documentados el PRIMER tab (Vigilancia diaria, el que abre por default), Chile nacional, VOLCAT por zona y Loop 2h.

*Escenario de fallo:* El operador abre el expander 'Como interpretar' -- pensado para orientarlo en 30 s -- y lo primero que lee es el nombre de un tab que pertenece a otra vista. La mitad de la pantalla que tiene enfrente no esta descrita, incluido el tab por defecto.

*Fix sugerido:* Derivar la lista del manual de la misma tupla de st.tabs (o de una constante compartida), como ya se hizo con `f"Volcan ({len(GRID_PANELS)} productos)"`, para que nombres y conteo no puedan divergir.

### `dashboard/manuals.py:262` — **medium**/conf=high

**El manual de Backfill enseña un procedimiento que no existe: un diccionario de eventos y un flag --event que el script no acepta**

manuals.py 'backfill', seccion 'Como armar un nuevo backfill': '2. Editar scripts/build_backfill.py agregando entry al diccionario de eventos. 3. Correr python scripts/build_backfill.py --event=NombreEvento'. El script real (scripts/build_backfill.py:363-376) declara --date, --start, --end, --volcan, --zone, --include-volcat, --include-volcat-height, --include-hotspots, --l1b-fallback. No hay --event ni diccionario de eventos; el flujo real es el workflow_dispatch de .github/workflows/backfill_build.yml con esos mismos inputs.

*Escenario de fallo:* Alguien necesita reconstruir un evento para un informe, sigue el manual al pie de la letra y recibe `error: unrecognized arguments: --event=...` mas un `--date/--start/--end/--volcan is required`. Busca el diccionario de eventos y no existe. El camino correcto (lanzar el workflow desde la UI de GitHub) no esta escrito en ningun lado del manual.

*Fix sugerido:* Reemplazar los pasos 2-4 por el flujo real (Actions -> 'Backfill historico build' -> inputs date/start/end/volcan/zone) y, si se quiere el camino local, citar el comando con los flags que el argparse acepta.

### `docs/FICHA_SDA_GOES.md:92` — **medium**/conf=high

**La ficha SDA declara como componentes del sistema dos modulos que no estan cableados a nada que el operador vea**

El bloque 'Mantenimiento de esta ficha' lista entre los modulos del SDA a `src/process/wind_shear_height.py` y `src/process/parallax.py`. Grep sobre src/ y dashboard/: `wind_shear_height` solo lo importa scripts/validate_fase3c.py:23 (script de validacion, no produccion); `parallax` no lo importa nadie fuera de su propio archivo (el unico hit es la palabra en un comentario de src/fetch/volcat_api.py:223). docs/paper/REGISTRO_PAPER.md §2 si es honesto y anota 'wind_shear_height.py (no en produccion aun)'; docs/GUIA_REVISION_DASHBOARD.md tambien lo declara 'Pendiente (no cableado aun)'. Solo la ficha -- el documento publicable bajo CPLT 6.7 -- los presenta como parte del funcionamiento.

*Escenario de fallo:* Un fiscalizador o un revisor externo lee la ficha, entiende que la altura se arbitra tambien por cizalla de viento y que la georreferencia de la pluma esta corregida por parallax, y evalua el sistema como mas capaz de lo que es. Si alguien audita una decision de alerta pasada asumiendo correccion de parallax (~1 km de corrimiento por km de altura a -40 S), le atribuye al sistema una precision de georef que no tuvo.

*Fix sugerido:* Separar en la ficha 'componentes en produccion' de 'implementados, no cableados', copiando la redaccion que ya usa REGISTRO_PAPER.md. Cambio de una linea que cierra la brecha entre lo publicado y lo que corre.

### `docs/FICHA_SDA_GOES.md:3` — **medium**/conf=high

**La ficha sigue diciendo 'v1.0 -- 2026-07-01' despues de tres cambios en agosto, incluido el disparo AUTOMATICO del retrieval de altura**

Linea 3: '**Version:** v1.0 -- 2026-07-01'. `git log -- docs/FICHA_SDA_GOES.md` muestra ediciones posteriores en 7946a5f y 7c7f3dc (2026-08-02) y en 88f21f9 (2026-08-30); el cuerpo tiene secciones fechadas 'ago-2026'. La guia maestra (§4) pide refrescar la ficha cuando cambia la logica y el CLAUDE.md del proyecto exige 'mismo commit que el cambio de logica'. El cambio de agosto no es cosmetico: introduce que el sistema decide SOLO cuando calcular la altura (disparo automatico por hot spot FDCF dentro del encuadre), que es una decision automatizada nueva. Ademas la seccion de sesgos sigue citando solo 'auditoria adversarial jul-2026 (AUDIT_REPORT_2026-07.md)' cuando en el repo hay un AUDIT_REPORT_2026-08.md posterior.

*Escenario de fallo:* El campo 'Version' es el unico control de cambios que tiene un lector externo. Con v1.0 congelado, quien leyo la ficha en julio no tiene forma de saber que en agosto el sistema empezo a lanzar retrievals por su cuenta, ni que hubo una auditoria posterior con hallazgos. La ficha deja de servir como registro de trazabilidad.

*Fix sugerido:* Bumpear a v1.1 con fecha ago-2026 y una linea de changelog al pie; incorporar los hallazgos de sesgo del audit ago-2026 en 'Evaluaciones de impacto'. Idealmente un test que compare la fecha de la ficha contra el ultimo commit que toca src/process/ y falle si quedo atras.

### `src/process/ash_rgb.py:105` — **medium**/conf=high

**Dos componentes que clasifican no llevan cabecera FICHA SDA ni estan declarados en la ficha; nada en tests/ verifica esa cobertura**

Grep 'FICHA SDA' sobre *.py da 11 hits: 8 en src/process/ (acha_plume_height, ash_detection, beta_ratios, bt_matching_height, parallax, scene, wen_rose_height, wind_shear_height), 2 en scripts/validate_* y 1 mid-file en dashboard/views/modo_guardia_volcan.py:777. Quedan SIN cabecera dos piezas que si clasifican: (a) `generate_so2_indicator` (src/process/ash_rgb.py:105-127), que produce el indicador SO2 con el umbral '< -3 K suggests SO2 presence' en los attrs (config.py:142 SO2_INDICATOR_THRESHOLD = -3.0) -- el archivo entero no tiene cabecera; (b) el filtro de hot spots de src/fetch/goes_fdcf.py: HOTSPOT_MASK_VALUES (linea 58) y HIGH_CONF_MASK (linea 66) deciden que pixel se dibuja como hot spot y cual se descarta (extract_hotspots, linea 266). Ninguno de los dos aparece en la lista de modulos de docs/FICHA_SDA_GOES.md. Grep 'FICHA' sobre tests/: 0 hits -- no hay guard automatico de cobertura.

*Escenario de fallo:* La convencion se sostiene solo por memoria humana. Un modulo de decision nuevo (o estos dos) llega a produccion sin cabecera y la ficha publicable -- que segun la guia maestra 'sale casi sola' de las cabeceras -- queda incompleta sin que nada avise. Para el revisor externo, el sistema tiene componentes que deciden y no estan documentados.

*Fix sugerido:* Agregar cabecera Nivel 1 a ash_rgb.py y goes_fdcf.py (con Limitaciones reales: cirros/nieve para SO2; FDCF optimizado a incendios para hot spots), listarlos en la ficha, y escribir un test que exija cabecera sobre una lista explicita de modulos-de-decision: la lista misma es el contrato.

### `src/fetch/goes_fdcf.py:66` — **medium**/conf=medium

**Tres descripciones distintas y contradictorias del mismo filtro de hot spots (docstring, constante, manual), ninguna en la ficha**

En el mismo archivo: el docstring de cabecera dice '30+ = nube / sin datos / fuera del disco' (goes_fdcf.py:13) y HOTSPOT_MASK_VALUES = {10,11,12,13,14,15} con el comentario '(10-15 son detecciones; 30+ son nube/no-fire/sin-datos)' (lineas 56-58); doce lineas mas abajo HIGH_CONF_MASK = {10, 11, 30, 31} INCLUYE 30 y 31, justificado como 'processed temporally filtered' (lineas 60-66). Los mismos codigos son 'nube/sin datos' arriba y 'alta confianza' abajo. Y dashboard/manuals.py 'series' le cuenta al operador una tercera version: 'cuenta de detecciones FDCF con mask >= 10 (confianza alta + saturated)', que no describe a ninguno de los dos conjuntos.

*Escenario de fallo:* El operador cruza el conteo de hot spots de Series contra la tabla FDCF de Modo Evento y le dan numeros distintos; el manual no le permite reconstruir por que. Si alguien 'corrige' el docstring creyendo que HIGH_CONF_MASK tiene un bug y saca el 30/31, se pierden detecciones reales, que es justo lo que el comentario dice que se quiso evitar. El criterio que decide que se pinta como hot spot es el mas dificil de reconstruir del repo.

*Fix sugerido:* Un solo bloque en goes_fdcf.py que explique la taxonomia FDCF completa (10-15 processed, 30/31 processed temporally filtered) y de ahi deriven las dos constantes; alinear el texto de manuals.py 'series' con la constante que la vista usa de verdad; declarar el filtro en la ficha SDA (junto con D9).

### `dashboard/views/modo_guardia_volcan.py:631` — **medium**/conf=high

**El PNG que el operador exporta lleva impresa una URL de dashboard muerta**

El footer del PNG compuesto del lado servidor dice literalmente 'GOES-19 · RAMMB/CIRA · NOAA FDCF · Open-Meteo GFS · SERNAGEOMIN · goesvolcanic.streamlit.app' (modo_guardia_volcan.py:629-631). README.md:22 declara ese deploy abandonado desde jun-2026. Mismo problema en scripts/generate_lascar_report.py:44 (`DASHBOARD_URL = "https://goesvolcanic.streamlit.app"`), que va al PDF de reports/lascar/.

*Escenario de fallo:* El geologo captura la escena, la pega en un informe o en el chat de turno, y el destinatario clickea la URL del pie para 'ir a ver en vivo'. Cae en una app dormida o inexistente. La imagen es justamente el artefacto que sobrevive a la sesion y circula fuera del equipo -- el CLAUDE.md ya razona que 'el archivo se explica solo meses despues'.

*Fix sugerido:* Centralizar la URL publica en src/config.py (una constante, un solo lugar) y usarla en el footer del PNG, en el PDF de Lascar y en el template de STATUS_NRT de goes.yml.

### `docs/DEPLOY_HF_SPACES.md:1` — **medium**/conf=high

**La guia de deploy sigue tratando a HF como 'mirror de Streamlit Cloud' e instruye a pushear a los dos**

Titulo: '# Deploy en Hugging Face Spaces (mirror de Streamlit Cloud)'. Seccion 'Workflow post-deploy': '# Push a AMBOS deploys / git push origin main # Streamlit Cloud / git push hf main # HF Spaces'; mas abajo 'Si Streamlit Cloud sigue dando problemas: Compartí con SERNAGEOMIN la URL de HF Spaces como **primaria** ... Streamlit Cloud (goesvolcanic.streamlit.app) queda como respaldo' (linea 117). README.md declara HF como unico deploy oficial desde jun-2026. La guia tampoco menciona scripts/deploy_hf.sh, que existe en el repo. El paso 6 de verificacion pide ver el badge 'build-2026-05-19-defensive-geo-load'; hoy el sidebar pinta `st.caption(f"🔖 `{BUILD_SHA}`")` (dashboard/app.py:128), un SHA, no ese literal.

*Escenario de fallo:* Quien tenga que re-desplegar (o levantar el Space de cero tras un incidente) sigue la guia, hace `git push origin main` creyendo que publica 'el otro deploy', y ademas anuncia una URL de respaldo que no responde. El paso de verificacion nunca da OK porque busca un badge que ya no se emite, y no queda claro si el deploy funciono.

*Fix sugerido:* Reescribir titulo e intro (HF = unico deploy), borrar la seccion de doble push y la de 'Streamlit como respaldo', documentar scripts/deploy_hf.sh, y cambiar el paso 6 por 'el sidebar muestra el SHA del commit desplegado'.

### `.github/workflows/tests.yml:40` — **medium**/conf=high

**El step llamado 'dashboard.app importable' no importa dashboard.app, y el smoke de views se salteo backfill_viewer**

tests.yml:38-43: el step se llama 'Smoke check -- dashboard.app importable' y su comentario dice 'Si esto falla, el deploy a Streamlit Cloud queda con pantalla en blanco', pero el comando es `python -c "import dashboard.style; import dashboard.utils; print('OK')"` -- nunca toca dashboard.app, que es el entrypoint real del CMD del Dockerfile. En paralelo, tests/test_smoke.py:18-33 lista 15 vistas pero NO incluye `dashboard.views.backfill_viewer`, que existe (dashboard/views/backfill_viewer.py) y esta ruteada ('📅 Backfill historico' en PAGE_OPTIONS, app.py:142); tampoco cubre dashboard.app, dashboard.manuals, dashboard.exports ni dashboard.map_helpers. El comentario menciona Streamlit Cloud, deploy retirado hace dos meses.

*Escenario de fallo:* Un import roto en dashboard/app.py o en backfill_viewer.py -- justo el patron 'imports cross-package top-level son fragiles' que el CLAUDE.md marca como gotcha del proyecto -- pasa el CI en verde y llega a HF. El Space arranca, el contenedor levanta y la app sirve un traceback: el dashboard operacional cae sin que ningun check lo haya visto.

*Fix sugerido:* Que el smoke importe `dashboard.app` de verdad y que la lista VIEWS de test_smoke.py se derive de un glob de dashboard/views/*.py (o se cruce contra PAGE_SLUGS) para que una vista nueva no pueda quedar fuera. Actualizar el comentario a HF.

### `docs/GUIA_REVISION_DASHBOARD.md:3` — **medium**/conf=high

**La guia de turno no dice que el sistema dispara el retrieval de altura POR SU CUENTA cuando hay un hot spot**

La guia (ultima actualizacion declarada 2026-07-01) describe la altura propia como algo que 'Aparece tras apretar el botón', ubicada 'en modo Volcán, debajo del VOLCAT primario, tras el botón "Calcular tope propio"'. Desde 88f21f9 (2026-08-30) la tira de altura vive tambien en la grilla de volcan (modo_guardia_volcan.py:777 y ss.) y, segun declara la propia docs/FICHA_SDA_GOES.md ('Cuándo se ejecuta el cálculo de altura (ago-2026)'), se dispara **automaticamente** cuando FDCF reporta un hot spot en el encuadre. La guia dirigida al operador no menciona ni la ubicacion nueva ni el disparo automatico.

*Escenario de fallo:* El geologo ve aparecer un numero de altura que no pidio y no sabe que lo disparo un hot spot FDCF, que marca anomalia termica en el crater y NO pluma. Sin esa clave puede leer el numero como 'el sistema detecto una pluma de X km'. Es la advertencia contextual que la ficha si documenta y la guia de uso no -- al reves de lo que conviene.

*Fix sugerido:* Agregar a la guia el gatillo (hot spot FDCF en el encuadre + boton), que el hot spot no implica pluma, y que en Modo Sala la tira va apagada a proposito. La redaccion ya existe en la ficha; falta bajarla al documento que el turno lee.

### `docs/README.md:60` — **low**/conf=high

**El indice de documentacion declara 'A integrar' dos fuentes que ya estan integradas hace meses**

Tabla 'Estado de fuentes': 'VOLCAT (volcano.ssec.wisc.edu) | Gratis | **A integrar**' y 'NOAA ABI-L2-ACHAF S3 | Gratis | A integrar (opcional)'. En el repo: src/fetch/volcat_api.py y src/fetch/realearth_api.py sirven VOLCAT a una vista propia ('📏 VOLCAT (altura pluma)' en PAGE_OPTIONS) y src/fetch/goes_acha.py + src/process/acha_plume_height.py usan ACHA2KMF como referencia externa de la cadena de altura (declarado asi en FICHA_SDA y REGISTRO_PAPER §2). Arriba, la seccion 'Productos de GOES-19 que usamos hoy' ya se contradice marcando VOLCAT con estrella.

*Escenario de fallo:* Quien llegue a evaluar el proyecto lee el indice de docs y concluye que la altura de pluma todavia no esta; o se pone a integrar VOLCAT de nuevo. Costo bajo, pero es ruido en el documento que se supone es el mapa de la documentacion.

*Fix sugerido:* Pasar ambas filas a 'En uso' y nombrar el modulo que las consume.

### `src/config.py:98` — **low**/conf=high

**Tercer lugar con el conteo viejo del sub-tab Volcan: config.py dice '3 productos'**

Comentario de MOSAICO_VOLCANOES: 'para cualquier otro esta el sub-tab "Volcán (3 productos)", que cubre el catálogo completo' (config.py:98). El tab real se rotula `f"🔬 Volcán ({len(GRID_PANELS)} productos)"` (modo_guardia.py:976) y GRID_PANELS tiene 4 paneles (GeoColor, Ash RGB, SO2, VOLCAT). El conteo ya se corrigio en manuals.py y modo_guardia.py; esta copia quedo.

*Escenario de fallo:* Quien lea el razonamiento de por que el mosaico son 5 y no 8 se lleva el numero equivocado del tab alternativo. Es el mismo drift que ya se cazo dos veces: mientras el conteo se escriba a mano en algun lado, va a volver.

*Fix sugerido:* Sacar el numero del comentario (decir 'el sub-tab Volcán') o derivarlo, ya que GRID_PANELS es importable.

### `.github/workflows/frp_timeline.yml:9` — **low**/conf=high

**Comentarios y release notes de los workflows anuncian cadencias que su propio cron desmiente**

frp_timeline.yml:9 'Corre cada 15 min para reflejar la anomalía casi en NRT', seis lineas antes de `cron: '*/10 * * * *'` (linea 15), que el comentario contiguo explica como 'Antes 15 min; subido a 10'. hires_visible_cache.yml:129 publica notes 'Actualizado por hires_visible_cache.yml cada 30 min' y la nota del loop dice 'Actualizado cada ~30 min; se llena en ~8h'; su cron es tambien `*/10` (linea 24). hires_loop_backfill.yml:98 repite 'cron cada 30 min'. Ademas hires_visible_cache.yml:19-23 describe un segundo cron 'Cada 60 min en :22 ... modo mono_05km' que NO existe: hay un solo `cron` en el bloque `on:`.

*Escenario de fallo:* Cualquiera que dimensione latencia, costo de Actions o frescura esperada leyendo los comentarios parte de numeros equivocados en los dos sentidos. El cron fantasma de 60 min es peor: describe un trigger que hay que buscar y no esta.

*Fix sugerido:* Pasada de sincronizacion de comentarios y release notes contra el cron real; borrar el parrafo del cron de 60 min que quedo huerfano.

### `.github/workflows/goes.yml:80` — **low**/conf=high

**El template de STATUS_NRT.md que goes.yml genera esta fosilizado: URL muerta, cron inexistente y rutas docs/goes/ ausentes**

El heredoc del step 'Actualizar STATUS_NRT' escribe '- **Dashboard**: https://goesvolcanic.streamlit.app' (linea 80), '## GitHub Actions / - Cron: cada 10 minutos' (el cron esta comentado desde 2026-05-15, lineas 11-12) y una seccion 'Arquitectura' con docs/goes/ash_rgb_latest.png, docs/goes/meta_latest.json y docs/goes/history/. `ls docs/goes` -> el directorio no existe. El print final dice 'STATUS.md actualizado' aunque escribe STATUS_NRT.md.

*Escenario de fallo:* Si algun dia se reactiva el workflow (el comentario deja la puerta abierta: 'si aparece consumidor'), el primer run commitea al repo un archivo de estado que afirma una cadencia inexistente y apunta al dashboard muerto. El bot volveria a ser una fuente de desinformacion con aspecto de dato fresco.

*Fix sugerido:* Si el workflow queda como opcion viva, actualizar el template (URL HF, 'ejecucion manual', quitar o crear docs/goes/). Si no, borrarlo: un manual que nadie corre desde mayo es mas costo de mantenimiento que opcion.

### `.github/workflows/frp_timeline.yml:43` — **low**/conf=high

**Los workflows de cron corren Python 3.11 contra un proyecto que declara requires-python == 3.12.***

pyproject.toml: `requires-python = "==3.12.*"`, con triple pin (runtime.txt, .python-version, pyproject). tests.yml usa 3.12 con el comentario '= produccion (fix audit W5)'; el Dockerfile usa python:3.12-slim. Pero animation_cache.yml:41, frp_timeline.yml:43, goes.yml:29 y lascar_pdf.yml:29 pinean `python-version: '3.11'`, mientras backfill_build.yml y los dos hires usan 3.12.

*Escenario de fallo:* El codigo que genera data/frp_timeline.json -- el que alimenta el Heatmap -- corre en un interprete que ni los tests ni el deploy ejercitan. Un comportamiento que difiera entre 3.11 y 3.12 se manifiesta solo en el dato commiteado, sin test que lo vea. Ademas `pip install` sobre 3.11 puede resolver otras wheels que las de produccion.

*Fix sugerido:* Unificar todos los workflows en 3.12. Si algo requiere 3.11, dejarlo escrito con la razon; hoy la asimetria parece inercia, no decision.

### `requirements.txt:1` — **low**/conf=high

**Tres dependencias usadas y no declaradas: PyYAML (tests), urllib3 (runtime) y geopandas (script)**

AST sobre src/, dashboard/, scripts/ y goes_export.py cruzado contra requirements*.txt: (a) `yaml` -- tests/test_workflow_concurrency.py:21, sin declarar en ningun requirements (consecuencia: D2); (b) `urllib3` -- src/fetch/_http_session.py, llega solo como transitiva de requests, asi que un cambio de resolucion lo puede dejar en otra major (urllib3 1.x vs 2.x tienen APIs de Retry distintas) sin que nada lo fije; (c) `geopandas` -- scripts/build_chile_coast.py, no declarado en requirements.txt ni en requirements_actions.txt (hoy ningun workflow lo corre, por eso es low).

*Escenario de fallo:* El caso vivo es (a), que ya tiene su hallazgo. Para (b): si urllib3 2.x cambia la firma de Retry, el rebuild de HF instala la nueva por transitividad y `_http_session` -- la sesion HTTP compartida de los fetchers -- revienta al importarse; como nada la pinea, el fallo aparece en un redeploy sin cambio de codigo.

*Fix sugerido:* Agregar pyyaml (o un requirements-dev.txt) y urllib3 con el rango que el codigo asume; documentar geopandas como extra opcional del script, igual que ya se hizo con el extra `archive` de cfgrib/eccodes en pyproject.

### `.github/workflows/backfill_build.yml:85` — **low**/conf=medium

**Inputs de workflow_dispatch interpolados dentro de bash, y acciones de terceros sin pin por SHA**

backfill_build.yml:80-96 arma el comando con `"${{ inputs.date }}"`, `"${{ inputs.volcan }}"`, etc. interpolados por GitHub ANTES de que corra el shell -- un valor con comillas o `$(...)` se ejecuta en el runner, que tiene `permissions: contents: write` y GITHUB_TOKEN. Lo mismo en el step 'Calcular tag y title' (linea 100) y en hires_loop_backfill.yml:80-87. Todos los workflows usan tags moviles: actions/checkout@v5, actions/setup-python@v6, actions/upload-artifact@v4 -- ningun SHA pineado. Severidad low porque workflow_dispatch requiere permiso de escritura, o sea que el atacante ya tendria acceso.

*Escenario de fallo:* El camino realista no es el input malicioso sino la accion de tercero: si una de esas refs se ve comprometida (patron ya visto en el ecosistema), el proximo cron corre codigo ajeno con contents:write sobre el repo que es fuente de un SDA en produccion, y puede reescribir data/frp_timeline.json o los releases rolling que el dashboard consume. Para un sistema que apoya decisiones de alerta, la integridad de la cadena de build importa.

*Fix sugerido:* Pasar los inputs por `env:` y referenciarlos como "$VOLCAN" dentro del script (bash los ve como datos, no como texto pegado). Pinear las acciones de terceros por SHA con comentario de version.

### `dashboard/manuals.py:344` — **low**/conf=high

**El manual de Loops ofrece una ventana de 24 h que el selector no tiene**

manuals.py 'loops': '2. Elegí ventana (últimas 2 h, 6 h, 24 h).' Las opciones reales son 2/3/6/8/10/12 horas (rammb_viewer.py:50-55: '2 horas (12 frames)' ... '12 horas (72 frames)'). No hay 24 h. El mismo manual lista los productos como 'Ash RGB, GeoColor, SO2 RGB' y omite BTD, que si esta en el selector (rammb_viewer.py:62).

*Escenario de fallo:* El operador busca la ventana de 24 h que el manual promete para un informe de evento largo y no la encuentra; el propio manual, dos parrafos mas abajo, ya se contradice recomendando encadenar loops de 2 h 'para erupciones >6 h'.

*Fix sugerido:* Listar las ventanas reales (o decir 'las que ofrece el selector') y agregar BTD a los productos.

### `docs/index.html:1` — **low**/conf=high

**docs/index.html no se publica en ningun lado: el repo no tiene GitHub Pages**

`gh api repos/MendozaVolcanic/goes-volcanic-monitoring/pages` -> 404 Not Found. docs/index.html (16 KB, <h1>GOES-19 Ceniza Volcánica) queda como pagina huerfana. Otros proyectos del ecosistema (VRP-chile, MOUNTS, NHI-v1) si publican por Pages, asi que la presencia del archivo sugiere que este tambien.

*Escenario de fallo:* Alguien la edita creyendo que actualiza una pagina publica, o la cita como 'la web del proyecto'. No hace daño operacional; es superficie de doc que aparenta estar viva.

*Fix sugerido:* O activar Pages sobre docs/ (y entonces auditarla como doc publica), o borrar el archivo. El estado intermedio es el peor.

### `INTEGRATION.md:27` — **low**/conf=high

**INTEGRATION.md declara 'Python 3.11+' contra un proyecto que exige == 3.12.***

Seccion Stack: '- Python 3.11+'. pyproject.toml declara `requires-python = "==3.12.*"`, con runtime.txt y .python-version en 3.12 y el Dockerfile en python:3.12-slim. INTEGRATION.md es el archivo que se sincroniza al hub Integracion_Plataformas, o sea que el dato viaja a otros proyectos.

*Escenario de fallo:* Otro proyecto del ecosistema (o el hub) consume la ficha y arma un entorno 3.11 para integrar; el `pip install` falla o, peor, resuelve otras wheels. Es el mismo desalineamiento que D18 pero publicado hacia afuera.

*Fix sugerido:* Cambiar a 'Python 3.12 (pin exacto: pyproject requires-python == 3.12.*)' y actualizar last_updated.

## Estado, caché y frescura  ·  14 hallazgos

**Verificado y limpio** (un núcleo sano también es información):

- Reloj: NO hay un solo datetime.now() naive ni datetime.utcnow() en dashboard/ ni src/ (grep exhaustivo). Todos son datetime.now(timezone.utc). _hires_age_min (modo_guardia_volcan.py:289-299) y _frp_age_hours (heatmap_actividad.py:132-147) normalizan tz antes de restar. dashboard/utils.py fmt_chile usa ZoneInfo(America/Santiago) -> DST correcto.
- Gotcha de fragments con run_every: verificados los 12 fragments. NINGUNO recibe timestamp, imagen ni bbox por argumento. _panel_rammb (modo_guardia_volcan.py:644-660) y _grid_header (:937-955) calculan now y consultan ts ADENTRO. Los args que si reciben (volcan_name, product, show_wind, radius_deg) vienen de selectores fuera del fragment, cuyo cambio dispara full-rerun -> se descongelan correctamente.
- Keys de cache con todos los parametros: _fetch_frame_for_ts(product, ts) y _fetch_zone_frame(product, ts, zone_key) en live_viewer; _frame(product, ts, lat_min..lon_max) en modo_guardia_volcan:181; _zone_frame_cached(product, timestamps_tuple, zone_key, uniform) en zonas_fullscreen:86; _fetch_bounds_frames(product, n, zoom, bounds_key, bounds_tuple) en rammb_viewer:708. No encontre ninguna key incompleta que pudiera servir la imagen de otro volcan/encuadre.
- Keys de st.plotly_chart incluyen el radio (vgrid_*, tvvolcatzoom_*) -> Plotly no reusa zoom/pan entre encuadres distintos.
- _volcat_map_only_cached (volcat_viewer.py:569-590) LANZA _VolcatMapUnavailable en vez de devolver {} para no envenenar el cache 2h con el negativo. El patron correcto ya existe en el repo.
- La seccion PRIMARIA del Heatmap (pulso intradia) si tiene guard de frescura completo (FRP_STALE_HOURS=3, heatmap_actividad.py:226-235 + 256-263), incluido el caso vencida-y-sin-senal que evita el mensaje verde.
- Arranque del hilo productor TV es exactamente-una-vez con lock (zonas_fullscreen.py:1161-1165); el indice de rotacion esta anclado al reloj con avance clampeado a +1 (zonas_fullscreen.py:985-995) -> no saltea slots.
- No hay keys duplicadas de widgets Streamlit entre las 16 vistas (grep de key= + uniq -d: vacio).
- get_latest_timestamps (rammb_slider.py:151-182) manda cache-buster ?_=epoch + headers no-cache; _load_frp_timeline y fetch_manifest hacen lo mismo -> ningun CDN intermedio puede servir un manifest viejo.
- Permalinks: ?fullscreen=abc degrada a no-fullscreen; ?vista=slug_inexistente cae al indice 0 sin crash; modo_evento valida ?volcan= contra PRIORITY_VOLCANOES (modo_evento.py:426-429); el escape URL de acentos en el boton Salir fullscreen esta puesto (app.py:96).


### `src/fetch/goes_fdcf.py:348` — **high**/conf=high · eje D

**Un fallo de S3 en FDCF devuelve ([], None) y las 4 vistas lo pintan como 'sin hot spots, es lo normal'**

fetch_latest_hotspots captura toda excepcion de s3.open/xr.open_dataset y retorna [], None (goes_fdcf.py:348-350), igual que cuando no hay archivos (:333-335). Los 4 consumidores del dashboard no distinguen los dos casos: live_viewer.py:972-976 imprime literalmente 'Sin hot spots FDCF en Chile en este scan. Es lo normal'; modo_guardia.py:249-256 pinta el KPI 'Hot spots Chile (NOAA FDCF)' en VERDE (#44dd88) cuando n_hs==0 y descarta el _hs_dt que recibio (:214); modo_guardia_volcan.py:976 escribe 'Hot spots 0 · Render HH:MM:SS UTC' donde el unico reloj mostrado es el del servidor, no el del scan FDCF; zonas_fullscreen.py:75-83 (_hotspots_zone) traga la excepcion con except Exception: return [], None.

*Escenario de fallo:* 3 AM, AWS S3 noaa-goes19 tiene un incidente regional (o el bucket L2 cambia de prefijo). El geologo de turno abre Modo Guardia y ve el KPI 'Hot spots Chile: 0' en verde y 'Sin hot spots en este scan, es lo normal'. Villarrica lleva 40 min con lava expuesta y FRP creciente. El turno concluye calma y no escala.

*Fix sugerido:* Hacer que fetch_latest_hotspots distinga fallo de vacio (tercer valor status, o excepcion propia tipo _VolcatMapUnavailable, que ya es el patron del repo en volcat_viewer.py:569). En los 4 call sites: si status != ok pintar el KPI en gris/ambar con 'FDCF no consultable', nunca en verde, y mostrar SIEMPRE la hora del scan FDCF junto al conteo (hoy scan_dt se descarta en modo_guardia y modo_guardia_volcan).

### `dashboard/views/heatmap_actividad.py:320` — **high**/conf=high · eje G

**El panorama semanal del Heatmap NO aplica el guard de frescura que si tiene el pulso intradia**

render() vuelve a llamar _load_frp_timeline() (:302) para el roll-up diario pero NUNCA consulta _frp_age_hours. Con daily vacio o sin la clave de hoy, :320-327 escribe 'Hoy (30-ago): sin deteccion FDCF en los 8 volcanes prioritarios (aun). Calma operacional.' con st.info. El unico rastro del problema es el caption de :330 'covered_days/7 dias cubiertos', que no dice nada de la edad. El guard equivalente si existe 90 lineas mas arriba (:226-235) para la seccion primaria.

*Escenario de fallo:* El workflow frp_timeline.yml se cae (secret ausente resuelto a string vacio -> el run reporta success, patron ya documentado en CLAUDE.md). Pasan 3 dias. El heatmap semanal se pinta todo en negro (0 scans) y abajo dice 'Calma operacional'. El turno lee 3 dias de calma termica que nunca se midieron. La curva intradia de arriba si avisa 'serie vencida', pero el heatmap es lo que se mira para el panorama.

*Fix sugerido:* Calcular age_h una sola vez en render(), pasarlo a ambas secciones y, si stale, (a) reemplazar el st.info verde por el mismo st.warning de vencimiento y (b) rayar/atenuar la grilla del heatmap para los dias posteriores a last_updated_utc en vez de dibujarlos como ceros.

### `dashboard/views/zonas_fullscreen.py:1594` — **high**/conf=high · eje D

**Modo Sala: el PNG del ultimo exito se proyecta indefinidamente y el badge de estado mide OTRO reloj (el de RAMMB), no el de la imagen**

_rgb_png (:1167-1175) y el bloque de zoom (:1231-1239) solo escriben _TV_PRODUCED cuando png es truthy; nunca borran ni marcan la entrada. _render_4_zonas_image_tv (:1594-1605) y _render_volcan_zoom_tv (:876-881) SOLO leen ese dict, sin ninguna comprobacion de edad. Mientras tanto el overlay de estado se calcula aparte: _rotating_tv_zonas:1003-1005 hace ts_for_status = _recent_ts(val, n=1) (latest_times.json de RAMMB, que sigue vivo) y se lo pasa a _render_tv_status, que pinta VERDE si age<15 min. El unico timestamp de la imagen real esta quemado dentro del PNG por _compose_4_zonas_png:1571-1580 como 'HH:MM UTC · HH:MM CLT', SIN fecha y SIN 'hace N min'.

*Escenario de fallo:* Los tiles de RAMMB empiezan a dar 502 pero latest_times.json sigue respondiendo (falla parcial tipica de RAMMB, ya documentada en CLAUDE.md para eumetsat_ash/jma_so2 zoom=4). El productor deja de refrescar _TV_PRODUCED. A las 03:20 la pared proyecta el compuesto de las 15:10 del dia anterior, rotulado '15:10 UTC' (plausible a simple vista, sin fecha) mientras el badge arriba a la derecha dice en VERDE 'scan hace 6 min'. Nadie lo nota hasta el cambio de turno.

*Fix sugerido:* Guardar en _TV_PRODUCED (png, produced_at, scan_ts) en vez de bytes pelados; que _emit_tv_png reciba esa edad y (a) enmarque en rojo / atenue la imagen si supera un umbral, (b) alimente _render_tv_status con el scan_ts DEL PNG mostrado, no con _recent_ts. Y quemar fecha + 'hace N min' en el header de zona de _compose_4_zonas_png, no solo HH:MM.

### `dashboard/views/mosaico_chile.py:341` — **high**/conf=high · eje G

**El panel GeoColor hi-res del Mosaico no tiene guard de edad ni muestra su hora, bajo un encabezado que anuncia el scan FRESCO de RAMMB**

_one() (:340-343) usa arr, info = _hires_for_volcano_cached(name, mode=hires_mode) y si arr no es None lo devuelve sin mirar info['scan_dt_iso'] ni info['render']. Comparese con fetch_volcan_product (modo_guardia_volcan.py:352-355), que si exige age <= HIRES_MAX_AGE_MIN (90) y render == 'visible_color'. El badge que dibuja _render_mini (:210-236) rotula 'HI-RES VIS · 1km/px · sol 40' pero NO lleva hora ni edad. El encabezado del grid (:306-308) muestra 'Scan HH:MM UTC (hace N min)' derivado de _recent_timestamps('eumetsat_ash'), o sea del producto RAMMB, no del cache hi-res.

*Escenario de fallo:* El GH Action hires_visible_cache.yml deja de correr (cuota, OOM; ya pasa con el modo mono segun el propio comentario de :393-399). El release hires-rolling congela su manifest. El turno abre el Mosaico, ve 'Scan 14:20 UTC (hace 6 min)' arriba y cinco paneles GeoColor de ayer con el badge azul 'HI-RES VIS'. Compara la pluma de Villarrica contra el Ash RGB de al lado (ese si fresco) y concluye que la pluma se disipo.

*Fix sugerido:* Reusar el guard de fetch_volcan_product: descartar el hi-res si age > HIRES_MAX_AGE_MIN o render != visible_color, y en cualquier caso incluir la hora del scan hi-res en el badge (el info ya trae scan_ts y scan_dt_iso, hoy se descartan).

### `dashboard/views/zonas_fullscreen.py:691` — **high**/conf=medium · eje G

**Los paneles VOLCAT de la grilla y del sub-tab por zona rotulan solo la HORA (fmt_both), sin fecha ni edad**

_render_volcat_zoom_tv:687-691 hace dt = _volcat_dt_obj(meta.get('datetime')) y pasa fmt_both(dt) if dt else '' como label de la figura; fmt_both (dashboard/utils.py:41-45) devuelve 'HH:MM UTC (HH:MM CLT)', sin fecha. Idem _render_volcat_zone_cell:337-338. Si dt no parsea, el label queda VACIO (sin ningun timestamp). Esas dos funciones alimentan _panel_volcat (modo_guardia_volcan.py:736-767, el 4o panel de volcan_grid, usado por los TRES llamadores incluida la pared tv=volcan) y el sub-tab 'VOLCAT por zona' (modo_guardia.py:506+), ninguno de los cuales tiene el overlay _render_tv_status que si calcula la edad en los slots rotatorios. La pagina VOLCAT completa si usa _parse_volcat_dt (volcat_viewer.py:726-731), que incluye la fecha: la inconsistencia es interna.

*Escenario de fallo:* SSEC/CIMSS deja de publicar Ash_Height para Chile_Central, o volcat_latest (volcat_api.py:246 frames[-1]) devuelve el ultimo frame disponible, que es de la crisis anterior. El panel VOLCAT de la grilla del volcan muestra una pluma con su barra de altura y el rotulo '14:20 UTC (10:20 CLT)'. El turno anota una altura de tope de una pluma que ya no existe, o de otro dia, en un informe de alerta.

*Fix sugerido:* Usar el mismo formato de la pagina VOLCAT (_parse_volcat_dt, con fecha) y agregar 'hace N min' con el semaforo ok=60/warn=120 que ya define _render_tv_status. Cuando dt es None, escribir explicitamente 'timestamp VOLCAT ilegible' en vez de dejar el label vacio.

### `dashboard/views/live_viewer.py:78` — **medium**/conf=high · eje D

**Cacheo NEGATIVO de 2 horas: un fallo transitorio deja ese scan/imagen inaccesible hasta que expire el TTL**

_fetch_frame_for_ts esta decorado @st.cache_data(ttl=7200) y hace 'if img is None: return None' (:85-87) -> el None queda cacheado 2 h bajo la clave (product, ts). Igual _fetch_zone_frame (:128-135). En volcat_viewer.py:347-359 _volcat_image_bytes devuelve b'' en el except y esta cacheada con TTL_FRAME_IMAGE=7200; _volcat_colorbar_strip (:360) hereda el vacio. El propio repo ya identifico y arreglo este patron para _volcat_map_only_cached (comentario en volcat_viewer.py:569-573: 'st.cache_data NO cachea excepciones -> la proxima llamada reintenta hasta exito, en lugar de dejar la zona en blanco las 2h del TTL'), pero no lo propago a estos cuatro.

*Escenario de fallo:* RAMMB da un 502 momentaneo justo en el scan de las 03:10 durante un pulso eruptivo. Todos los reruns de las 2 horas siguientes devuelven None para ese ts: el panel dice 'No se pudo descargar Ash RGB' aunque RAMMB se recupero en 30 s, y el frame del pulso no se puede recuperar ni forzando refresh. Con VOLCAT, la celda queda 'sin frame disponible' 2 h despues de que SSEC volvio.

*Fix sugerido:* Aplicar el patron ya existente: que el core cacheado lance una excepcion propia en fallo y un wrapper fino la convierta en None/b'' para el llamador. Solo los exitos entran al cache.

### `dashboard/views/ash_viewer.py:222` — **medium**/conf=medium · eje D

**El selector 'Region' se ignora cuando 'Usar cache' esta activo (que es el default)**

bounds = ZONE_OPTIONS[zone_key] (:208) solo se usa en la rama fetch_new (:216). La rama 'elif use_cached:' (:222-228) llama get_latest_processed(), que en src/process/pipeline.py:181-185 hace sorted(PROCESSED_DIR.glob('meta_*.json'), reverse=True)[0], el mas reciente por nombre, sin filtrar por bbox. use_cached es un checkbox con value=True (:202), o sea el estado por defecto de la pagina.

*Escenario de fallo:* El operador selecciona 'Zona Norte' para mirar Lascar. La ultima escena procesada en disco era 'Zona Sur'. La pagina muestra el Ash RGB de la Zona Sur bajo el rotulo Zona Norte y los KPIs ('Pixeles validos', 'BTD < -1K: 3.421', 'Confianza alta: 12') se calculan sobre esa otra region. El mapa si esta georeferenciado con su propio geo, asi que solo lo delatan los ejes de latitud.

*Fix sugerido:* Pasar bounds a get_latest_processed (o filtrar los meta_*.json por el bbox guardado en el meta) y, si no hay cache para la region pedida, decirlo explicitamente en vez de mostrar otra. Mientras tanto, imprimir el bbox del archivo cacheado junto al timestamp en el status banner.

### `dashboard/views/zonas_fullscreen.py:876` — **medium**/conf=high · eje D

**_TV_PRODUCED es estado global de PROCESO: los toggles del Modo Sala son inertes y, si se cablearan, se filtrarian entre sesiones**

_render_volcan_zoom_tv(volcano_name, show_hotspots, height) declara show_hotspots pero su cuerpo (:876-881) solo hace png = _TV_PRODUCED.get('volcan:'+volcano_name): el argumento no se usa. Idem _render_4_zonas_image_tv(product, show_volcanoes, show_hotspots) (:1594-1605). Las claves de _TV_PRODUCED no incluyen ningun flag. Ademas prewarm_tv_caches (:1149-1165) congela show_hotspots y volcan_zooms de la PRIMERA llamada del proceso via el gate _TV_PRODUCER_STARTED; llamadas posteriores con otros argumentos retornan sin efecto. Hoy no explota porque el unico llamador (modo_guardia.py:925) pasa siempre show_hotspots=True, pero la firma promete lo contrario.

*Escenario de fallo:* Dos volcanes en crisis y dos operadores: uno abre el Modo Sala en la pared y otro en su puesto. Si manana alguien cablea el toggle de hot spots (la firma invita a hacerlo), el segundo operador apaga los hot spots y la pared se los apaga tambien, o al reves, porque el PNG es uno solo para todo el proceso de HF Spaces. Hoy el sintoma visible es menor: mover el toggle no cambia nada y no se explica por que.

*Fix sugerido:* Incluir los flags en la clave de _TV_PRODUCED (rgb:{product}:{int(show_volcanoes)}{int(show_hotspots)}) y hacer que prewarm_tv_caches lea los flags de una variable de modulo actualizable, o borrar los argumentos que no se usan para que la firma no mienta.

### `dashboard/views/zonas_fullscreen.py:1161` — **medium**/conf=medium · eje D

**El hilo productor del Modo Sala no se puede reiniciar: _TV_PRODUCER_STARTED se pone en True y nunca se limpia**

prewarm_tv_caches:1161-1165 setea _TV_PRODUCER_STARTED=True dentro del lock y retorna en toda llamada posterior. El thread se crea a continuacion (:1262-1268) con try: t.start() except Exception: pass; si el start falla, el flag YA quedo en True y ningun rerun volvera a intentarlo. Del mismo modo, si _producer() muere el while True desaparece sin dejar rastro y _TV_PRODUCED queda congelado; el foreground no tiene forma de saberlo porque solo lee el dict (ver E3).

*Escenario de fallo:* Tras un pico de memoria en HF Spaces el hilo productor muere. La pared sigue rotando slots y mostrando los ultimos PNG, cada vez mas viejos, sin placeholder ni error, hasta que alguien reinicia el Space a mano. El fragment foreground nunca bloquea, asi que no hay ningun sintoma de UI.

*Fix sugerido:* Guardar un heartbeat del productor (_TV_PRODUCER_ALIVE_AT actualizado al final de cada _produce_once) y, si el foreground ve un heartbeat viejo, resetear el flag bajo el lock y relanzar el hilo, ademas de mostrar el aviso en el overlay de estado.

### `dashboard/views/modo_guardia.py:783` — **medium**/conf=high · eje D

**El permalink ?volcan= de los modos TV no se valida: la pared 24/7 muestra un st.error o un mapa sin marcador**

modo_guardia.py:783 volcan_name = st.query_params.get('volcan', 'Villarrica') para tv=volcan y :773 lo mismo para tv=chile, sin comprobar contra CATALOG (comparese con modo_evento.py:426-429, que si valida contra PRIORITY_VOLCANOES). Aguas abajo: _panel_rammb (modo_guardia_volcan.py:665-668) y _panel_volcat (:759-762) hacen 'if v is None: st.error(...)', y _render_chile_with_hotspots (modo_guardia.py:163-173) simplemente omite el marcador sin decir nada.

*Escenario de fallo:* Un permalink pegado en la sala con la tilde perdida por copiado ('Nevados de Chillan' vs el nombre real del catalogo) deja la pared proyectando cuatro cajas rojas 'Volcan X no esta en el catalogo' toda la noche; o peor, en tv=chile, un mapa de Chile aparentemente normal donde el volcan que se cree estar vigilando simplemente no tiene marcador.

*Fix sugerido:* Validar contra CATALOG con normalizacion de acentos y caer al default con un st.warning visible una sola vez ('?volcan=X no existe, mostrando Villarrica'), nunca en silencio.

### `dashboard/views/modo_guardia.py:334` — **low**/conf=high · eje D

**_rotating_chile_tv avanza el indice en CADA rerun del fragment; no se le aplico el clamp por reloj que arreglo _rotating_tv_zonas**

modo_guardia.py:334-337 hace idx = st.session_state[key] % N; st.session_state[key] = (idx+1) % N: el avance depende del numero de ejecuciones, no del tiempo. zonas_fullscreen.py:985-995 documenta explicitamente por que eso salta slots y usa en cambio un indice anclado al reloj con avance clampeado a +1. La correccion no se propago a esta rotacion.

*Escenario de fallo:* Cualquier rerun extra de la app (el watchdog de reconexion de style.py:512-520, un click, un scan nuevo) hace avanzar la rotacion Chile fuera de tiempo: un producto se muestra dos veces seguidas y otro se saltea. En la sala se lee como 'el SO2 casi nunca aparece'.

*Fix sugerido:* Reusar el patron de _rotating_tv_zonas (clock_idx anclado a epoch//ROTATION_SECONDS con avance clampeado a +1).

### `dashboard/views/modo_guardia.py:96` — **low**/conf=high · eje G

**hours_back de FDCF inconsistente entre vistas: la vista Nacional y la del volcan pueden discrepar sobre si hay hot spot**

live_viewer.py:290 y modo_evento.py:70 usan hours_back=2; modo_guardia.py:96, modo_guardia_volcan.py:216 y zonas_fullscreen.py:79 usan hours_back=1. _list_recent_files solo retrocede si la hora actual no tiene archivos, asi que en el borde de hora (o con un hueco de publicacion de NOAA) una vista encuentra el granulo y la otra no.

*Escenario de fallo:* A las 03:02 UTC NOAA todavia no publico nada en la carpeta de la hora 03. La Vista Operacional (hours_back=2) muestra 1 hot spot en Villarrica; el operador cambia a Modo Guardia (hours_back=1) y ve 'Hot spots Chile: 0' en verde. Dos numeros contradictorios del mismo producto en la misma pantalla, sin explicacion.

*Fix sugerido:* Centralizar hours_back en una constante (mismo espiritu que src/cache_ttl.py) y usar 2 en todos lados.

### `dashboard/app.py:165` — **low**/conf=high · eje G

**El redirect de slugs viejos es case-sensitive mientras el resto del routing no lo es**

app.py:165 _curr = qp.get('vista') sin .lower(), y el dict _SLUG_REDIRECTS solo tiene claves en minuscula. Cuatro lineas mas abajo, :191, si normaliza: _url_vista = qp.get('vista','').lower(). Con ?vista=ZONAS el redirect no dispara y 'zonas' tampoco esta en PAGE_SLUGS -> initial_idx=0.

*Escenario de fallo:* Un bookmark viejo con el slug en mayusculas (o mal normalizado al pasarlo por un chat) abre la Vista Operacional en vez del Modo Guardia, sin ningun aviso. El turno cree estar en Guardia.

*Fix sugerido:* _curr = qp.get('vista', '').lower() y escribir el slug normalizado de vuelta a la URL.

### `dashboard/views/live_viewer.py:1228` — **low**/conf=high · eje G

**Deriva entre TTLs reales y lo que dicen los textos/docstrings de la misma vista**

El pie de la Vista Operacional (live_viewer.py:1228) dice 'Auto-refresh cada 10 min' mientras _health_banner corre run_every=60s (:425). El docstring de _get_latest_ts dice 'cache 15s' (:63) pero el paso 1 del render lo comenta como 'liviano, cache 90s' (:983) y el docstring de _live_content lo llama 'TTL=30s' (:568). src/cache_ttl.py define TTL_TIMESTAMPS_LIST_FAST=15 pero live_viewer no lo importa: usa el literal 15 en dos decoradores (:62, :138).

*Escenario de fallo:* Deriva pura: quien ajuste la cadencia en cache_ttl.py cree haberla cambiado en la vista principal y no cambio nada; y el operador que lee el pie asume que la pantalla no se refresca sola en 10 minutos y recarga a mano.

*Fix sugerido:* Importar TTL_TIMESTAMPS_LIST_FAST en live_viewer (como ya hacen comparador.py y volcat_viewer.py), corregir los 3 docstrings y el texto del pie.

## Fetchers y degradación silenciosa  ·  20 hallazgos

**Verificado y limpio** (un núcleo sano también es información):

- Timeouts explicitos: TODA llamada de red que abri lleva timeout (rammb_slider TIMEOUT=20, volcat_api 20, realearth 30, wind_data 12, gfs_profile 15, viirs_firms/gibs 30, hires_cache 12, hires_loop 12/30, animation_cache 15/45, historic_rammb 5/15, volcat_height_at requests.get(...,timeout=30)). No encontre un requests.get sin timeout.
- _http_session.get_session (lineas 40-51): Retry(total=3, backoff_factor=0.5, status_forcelist 429/5xx, allowed_methods GET/HEAD) montado en http y https. Los clientes que la usan SI tienen backoff exponencial (el backlog 'los que hay no tienen backoff' aplica a _retry_s3 y gfs_archive._read_range, no a esta).
- granule_select.nearest_granule_key: puro respecto a la red, normaliza dt naive a UTC (l.81-82), une [dt-1h, dt, dt+1h] deduplicando, y devuelve None si todas las keys son inparseables (l.99-100). Correcto.
- Parsers de timestamp DOY: goes_fdcf._parse_scan_time (l.98-112), goes_acha._parse_scan_time (l.88-100) y goes_s3._scan_start (l.167-177) construyen datetime(yyyy,1,1,...)+timedelta(days=doy-1) — correcto en bisiestos y sin problema de cambio de hora (todo UTC). El cruce de borde de hora lo cubre nearest_granule_key.
- src/export/geotiff.py: from_bounds(west,south,east,north) produce transform NORTE-ARRIBA y coincide con el orden de filas de reproject_to_latlon (lats_out = linspace(lat_max, lat_min) -> fila 0 = norte, rammb_slider l.291). El GeoTIFF NO sale espejado. CRS EPSG:4326 correcto para la grilla ya reproyectada.
- dashboard/exports.py:126-149: maneja el b'' que devuelve build_geotiff_bytes en el error path y muestra 'GeoTIFF no disponible' en vez de ofrecer un boton de 0 KB.
- viirs_gibs.fetch_viirs_image l.270-274: chequea content-type antes de decodificar (GIBS devuelve XML de ServiceException con HTTP 200). Es el UNICO fetcher del repo que valida el tipo de respuesta; es el patron correcto.
- viirs_firms.fetch_viirs_firms_hotspots: distingue explicitamente None (=fallo/sin MAP_KEY) de [] (=sin detecciones) y lo documenta (l.123-125). Es el contrato que le falta al resto.
- goes_s3._download_cached (l.94-121): lock por filename + descarga a tmp unico + os.replace atomico. Sin corrupcion con descargas concurrentes.
- timeseries.fetch_volcano_timeseries marca available=False en vez de fabricar un punto, y dashboard/views/timeseries_viewer.py l.160/227/396 filtra por available antes de graficar y de calcular KPIs -> un frame caido NO se dibuja como caida de la senal a 0%.
- modo_guardia_volcan.py l.348-356: el guard r_view <= r del hi-res GeoColor esta puesto y usa el radio EFECTIVO de los bounds, no la constante.
- modo_guardia_volcan._hires_age_min + HIRES_MAX_AGE_MIN=90 (l.67, 289-300, 354): hay guard de frescura sobre el hi-res (limitado por el hallazgo D3, que ataca la validez del timestamp mismo).
- hires_pipeline l.234-247: chequea el anidamiento ABI (B2 0.5km = 2x B1/B3 = 4x B13) y desactiva el pan-sharpen si no se cumple, en vez de producir una imagen corrida. Buen ejemplo del criterio correcto.
- volcat_api._query_frames (l.186-209): devuelve SIEMPRE 2-tupla en todos los error paths — el contrato inconsistente que mordio en jun-2026 esta cerrado. Revise el resto de src/fetch buscando el mismo patron (funcion que devuelve tupla en el happy path y escalar en el error) y no encontre otro caso vivo.


### `src/fetch/goes_fdcf.py:350` — **high**/conf=high · eje F

**fetch_latest_hotspots colapsa 'no pude consultar S3' en ([], None) y el KPI de Modo Guardia lo pinta VERDE**

goes_fdcf.py:348-350 `except Exception: logger.exception(...); return [], None` cubre el s3.open + open_dataset. goes_fdcf.py:332-335: si `_list_recent_files` vuelve vacio (y esa funcion, l.139-140, se traga cualquier excepcion de red con solo un warning) tambien devuelve `[], None`. Rio abajo, dashboard/views/modo_guardia.py:247-256 hace `n_hs = len(hotspots)`; `hs_color = '#ff4444' if n_hs > 0 else '#44dd88'` y pinta el KPI 'Hot spots Chile (NOAA FDCF): 0' en VERDE. modo_guardia.py:266-268 hace lo mismo con 'sin hotspots' en verde para el volcan seleccionado. Ningun consumidor mira el `scan_dt=None` que es la unica senal de fallo.

*Escenario de fallo:* 03:00 AM, AWS S3 responde 503 durante dos minutos (o el DNS del endpoint falla). El geologo de turno abre el Modo Guardia con Villarrica en alerta amarilla: el KPI dice 0 hot spots en VERDE y el KPI del volcan dice 'sin hotspots' en VERDE. Lee calma. Lo mismo pasaria si en ese scan hubiera 3 hot spots de FRP alto: el dato nunca se consulto.

*Fix sugerido:* Cambiar el contrato a tri-estado: devolver `(None, None)` (o un `HotspotResult(hotspots, scan_dt, error)`) cuando la consulta FALLA, reservando `([], scan_dt)` para 'el scan se leyo y no habia nada'. En los KPI, con error -> gris/ambar y texto 'FDCF no consultable'. Nunca verde sin scan_dt.

### `dashboard/views/zonas_fullscreen.py:76` — **high**/conf=high · eje F

**El resultado de FALLO de hot spots se cachea 5 minutos con st.cache_data — un blip de 2 s congela 'sin hot spots' en toda la pared**

zonas_fullscreen.py:75-84 `@st.cache_data(ttl=300)` sobre `_hotspots_zone`, cuyo `except Exception: return [], None` guarda el fallo en la cache. Identico en dashboard/views/modo_guardia_volcan.py:210-223 (`_hotspots_volcan`, ttl=300), dashboard/views/modo_guardia.py:85-98 (`_hotspots_chile`, ttl=300) y dashboard/views/live_viewer.py:281-292 (`_fetch_hotspots_cached`, ttl=300). Streamlit no distingue 'resultado valido' de 'resultado de error': cachea el valor de retorno.

*Escenario de fallo:* Un timeout transitorio de S3 de 2 segundos durante el render de la zona Sur. Los 300 s siguientes, TODA aparicion de esa zona en la rotacion del Modo Sala (que rota cada ~30 s) reusa el ([], None) cacheado sin volver a intentar. Cinco minutos de pared proyectada diciendo 'sin hot spots' por un corte de dos segundos, y los scans FDCF de esos 5 min (uno cada 10 min) no se releen.

*Fix sugerido:* No cachear los fallos: con el tri-estado de D1, hacer que el wrapper cacheado levante la excepcion (Streamlit no cachea excepciones) o que el llamador chequee el flag de error y llame a `.clear()` sobre esa entrada. Como minimo, TTL distinto (p.ej. 20 s) para el camino de error.

### `scripts/build_hires_cache.py:113` — **high**/conf=high · eje F

**El manifest hi-res sella el timestamp del `dt` PEDIDO, no el del granulo que realmente se bajo — el guard de frescura de 90 min puede mentir por ~70 min**

build_hires_cache.py:93 `ts_str = dt.strftime('%Y%m%d%H%M%S')` y l.113-114 `"scan_ts": ts_str, "scan_dt_iso": dt.isoformat()`, donde `dt` es el instante que pidio el workflow. La imagen sale de src/process/hires_pipeline.py:138 `download_band(dt, b)`, y goes_s3.download_band:154-164 hace `files = list_band_files(dt, band); if not files: files = list_band_files(dt - timedelta(hours=1), band)` y luego toma `files[-1]` — devuelve un granulo de la hora ANTERIOR sin avisar y sin que nadie parsee su `_sYYYYDDDHHMMSS` (el helper `_scan_start` existe en el mismo modulo, l.167, pero este camino no lo usa). El dashboard consume ese sello: modo_guardia_volcan.py:289-300 `_hires_age_min` lee `scan_dt_iso`, y l.354 lo compara contra HIRES_MAX_AGE_MIN=90 antes de aceptar la imagen; l.364 imprime 'hace {age} min'.

*Escenario de fallo:* La publicacion de RadF en noaa-goes19 se atrasa y la carpeta de la hora en curso esta vacia cuando corre el cron. `download_band` cae a la hora previa y devuelve un scan de HH-1:50. El manifest lo etiqueta con la hora del cron. El operador ve el panel GeoColor del volcan con el badge 'hace 5 min · hi-res L1b ~0.5 km/px' sobre una imagen de hace ~65 min: una columna que ya se levanto no aparece, y el guard de 90 min la deja pasar como fresca.

*Fix sugerido:* Que `download_band` devuelva (path, scan_dt) o que hires_pipeline aplique `goes_s3._scan_start(path.name)` sobre el archivo efectivamente bajado y propague ESE datetime al manifest. Ademas registrar en el manifest si hubo fallback de hora.

### `src/process/hires_pipeline.py:134` — **medium**/conf=high · eje F

**El hi-res mezcla bandas sin verificar que vengan del MISMO scan (scene.py si tiene ese guard)**

hires_pipeline.py:134-145 `_download_bands_parallel` llama `download_band(dt, b)` por banda de forma INDEPENDIENTE; cada llamada puede caer a la hora previa por su cuenta (goes_s3.py:154-160) o tomar un `files[-1]` distinto si la listada de una banda llego antes que la de otra. No hay ninguna comparacion de los timestamps de los archivos resultantes. Contraste directo: src/process/scene.py:287-291 SI corta con `_err('bandas C11/C14/C15 de scans distintos (S3 incompleto)')`.

*Escenario de fallo:* Al filo de la hora, B2 (0.5 km, el pancromatico) sale del scan HH:00 y B1/B3 (1 km, el color) todavia no estan publicados y caen al scan (HH-1):50. El pan-sharpen fusiona la luminancia de un scan con la crominancia de otro 10-60 min anterior: las nubes quedan desplazadas respecto de la textura, y una columna en movimiento se ve como un artefacto de color corrido. Se publica al cache y se proyecta como GeoColor 0.5 km.

*Fix sugerido:* Aplicar el mismo guard de scene.py: parsear `_scan_start` de cada path devuelto y abortar (o degradar a sin pan-sharpen) si difieren mas que la tolerancia del scan.

### `src/fetch/goes_fdcf.py:58` — **medium**/conf=medium · eje F

**El camino POR DEFECTO descarta las categorias FDCF 30/31 (temporally filtered) que el camino 'alta confianza' SI incluye — los conjuntos no estan anidados**

goes_fdcf.py:58 `HOTSPOT_MASK_VALUES = {10,11,12,13,14,15}` frente a l.66 `HIGH_CONF_MASK = {10,11,30,31}`. En extract_hotspots l.266 `valid_mask_set = HIGH_CONF_MASK if high_conf_only else HOTSPOT_MASK_VALUES`: con high_conf_only=False (el default) los mask 30/31 NUNCA pasan. El comentario del propio repo (l.60-65) dice que 30/31 son 'processed temporally filtered' y que 'ya pasaron un test de persistencia... son al menos tan confiables como las processed simples'. Grepeando el repo, NINGUN llamador de produccion pasa high_conf_only=True (live_viewer:290, modo_evento:70, modo_guardia:95, modo_guardia_volcan:218, zonas_fullscreen:79, frp_timeline:136 — todos con el default). Ademas el docstring del modulo se contradice a si mismo: l.12 afirma '30+ = nube / sin datos / fuera del disco'.

*Escenario de fallo:* Villarrica con lava expuesta persistente scan tras scan: el algoritmo FDCF la reporta en la categoria temporalmente filtrada (30/31) justamente por ser persistente. Todo el dashboard —KPI de Modo Guardia, panel de volcan, serie intradia de FRP, roll-up del heatmap— muestra 0 hot spots y FRP 0 MW mientras el producto NOAA la esta detectando. El operador cruza con VRP (MODIS/VIIRS) y no entiende la discrepancia.

*Fix sugerido:* Verificar la tabla de mask del ABI L2 Fire ReadMe y, si 30/31 (y sus pares 32-35) son las contrapartes temporalmente filtradas de 10-15, incluirlas en HOTSPOT_MASK_VALUES para que el conjunto permisivo CONTENGA al restrictivo; extender `_confidence_from_mask` (hoy devuelve 'unknown' para 30/31, l.122) y corregir el docstring l.12. Test que asserte HIGH_CONF_MASK subconjunto de HOTSPOT_MASK_VALUES.

### `src/fetch/volcat_api.py:246` — **medium**/conf=high · eje F

**VOLCAT sin guard de antiguedad: `daterange:180` + `frames[-1]` puede pintar un frame de hace dias, y la caida de SSEC se lee igual que 'sin ceniza'**

volcat_api.py:196-199 arma la URL con `endtime:latest::daterange:180` (180 dias de ventana) y l.246 toma `last = frames[-1]` sin comparar su datetime contra ahora. `_query_frames` (l.203-208) devuelve `[], None` tanto ante HTTP != 200 como ante excepcion, y `volcat_latest` l.244-245 lo convierte en `None`. Rio abajo, zonas_fullscreen.py:593-597 `if not meta: _placeholder('sin frame disponible')` — y el placeholder es exactamente el estado que la doctrina del proyecto declara NORMAL. Grepeando 'edad|stale|max_age' en dashboard/ y src/: hay guard de frescura para el scan RAMMB (live_viewer.py:427-449), para el hi-res (HIRES_MAX_AGE_MIN) y para la serie FRP (heatmap_actividad.py:226-233), pero NINGUNO para VOLCAT.

*Escenario de fallo:* (a) SSEC saca de servicio el sector Chile_South por mantenimiento. La pared del Modo Sala sigue mostrando el ultimo frame publicado —con su nube de ceniza y su barra de altura— con la etiqueta de su fecha real en texto chico y sin color de alerta; en el turno se lee como situacion actual. (b) SSEC responde 502 durante la ventana: el panel dice 'sin frame disponible', que el manual del proyecto ensena a leer como 'VOLCAT no detecta ceniza' = calma.

*Fix sugerido:* En `volcat_latest`, calcular la edad del frame elegido y devolverla en el dict (`age_min`); en el panel, colorear/rotular si supera ~30-40 min (2-4 scans ABI). Y separar el mensaje: 'SSEC no respondio' != 'VOLCAT sin deteccion'.

### `src/fetch/rammb_slider.py:252` — **medium**/conf=high · eje F

**reproject_to_latlon devuelve el mosaico ABI CRUDO si falta pyproj/scipy — el llamador lo pinta sobre el bbox lat/lon igual**

rammb_slider.py:249-254 `except ImportError as e: logger.warning(...); return img`. `img` esta en proyeccion geoestacionaria ABI. Los llamadores lo dibujan sobre `bounds`: fetch_frame_for_bounds l.452-460 devuelve ese resultado y modo_guardia_volcan.py:415-416 lo pone como layout.image con `x=bounds['lon_min'], sizex=bounds['lon_max']-bounds['lon_min']`. Mismo patron en goes_fdcf._abi_to_latlon l.154-158, que ante ImportError de pyproj devuelve `np.zeros_like` -> todos los hot spots en lat=0, lon=0 (con bounds no-None el filtro l.276-282 los descarta y se lee como 'sin hot spots'; con bounds=None se dibujan en el Golfo de Guinea).

*Escenario de fallo:* Un rebuild del Space de HF instala una rueda de scipy/pyproj incompatible con el Python del runtime. La app NO falla: pinta la imagen geoestacionaria estirada sobre el bbox del volcan. El marcador del volcan, los anillos de 10/30 km y los hot spots quedan en un sistema de coordenadas distinto al de los pixeles: la pluma se ve decenas de km corrida del crater y el operador estima mal la direccion de dispersion. Es una mentira de georreferencia, no un problema estetico.

*Fix sugerido:* Ante ImportError devolver None (o lanzar), nunca la imagen sin reproyectar. pyproj y scipy son dependencias DURAS del render georreferenciado (estan en requirements.txt): un fallo de import es un bug de deploy y debe romper ruidoso. Idem `_abi_to_latlon`.

### `src/fetch/rammb_slider.py:137` — **medium**/conf=high · eje F

**get_tiles_for_bounds cae a los tiles de Chile de ZOOM 2 ignorando el zoom pedido -> frame todo negro que se lee como 'sin dato'**

rammb_slider.py:98-102 (ImportError de pyproj) y l.137-138 (ninguna esquina proyectable) devuelven `CHILE_TILES_Z2['rows'], CHILE_TILES_Z2['cols']` = rows [2,3] cols [1,2], SIN mirar el parametro `zoom`. Con zoom=3 o 4 esos indices apuntan a otra parte del disco (a zoom 4 la grilla es 16x16). fetch_frame_for_bounds l.442-460 baja esos tiles y luego reproyecta con `out_bounds=bounds`: en reproject_to_latlon l.314-319 la mascara `valid` exige (src_col, src_row) dentro del canvas, que no se cumple para ningun pixel -> l.336 pone todo a 0.

*Escenario de fallo:* Se pide la vista de volcan (zoom 4) para un bbox cuyas 4 esquinas caen fuera del disco visible o en un borde donde pyproj devuelve 1e30 (volcan austral con la vista abierta a radio grande). El panel Ash RGB del volcan sale NEGRO. En un producto IR de noche el negro es un estado plausible, asi que el operador lo lee como 'sin senal', no como 'la seleccion de tiles fallo'.

*Fix sugerido:* Devolver None (y que fetch_frame_for_bounds devuelva None, que la UI ya sabe rotular) en vez de tiles de otro nivel de zoom. Si se quiere conservar un fallback, calcularlo para el zoom pedido.

### `src/fetch/rammb_slider.py:386` — **medium**/conf=high · eje F

**fetch_stitched_frame rellena con NEGRO los tiles que fallaron y devuelve la imagen como exitosa, sin decir cuantos faltan**

rammb_slider.py:375-408: se descargan los tiles en paralelo, los que devuelven None (404, 5xx tras los reintentos, PNG corrupto — fetch_tile l.209-211) simplemente no entran a `tiles`, el canvas nace en `np.zeros` (l.396) y solo se rellenan las celdas presentes. La unica condicion de fallo es que fallen TODOS (l.386-387). Mismo patron en historic_rammb.fetch_historic_stitched l.175-185. El valor de retorno no lleva ninguna cuenta de tiles perdidos.

*Escenario de fallo:* A las 3 AM el CDN de RAMMB devuelve 500 para 1 de los 12 tiles de la vista de zona. El cuadrante que contiene al volcan sale negro; el resto del mapa se ve normal, con su timestamp fresco y su leyenda. El operador lee 'no hay nada ahi'. Ademas ese frame alimenta timeseries.fetch_volcano_timeseries (_one, l.204-208), que lo marca available=True y calcula la metrica sobre los pixeles restantes.

*Fix sugerido:* Devolver tambien la fraccion de tiles obtenidos (o una mascara de cobertura) y que la vista rotule 'imagen parcial: N/M tiles' — o descartar el frame si falta el tile que contiene el punto de interes.

### `src/fetch/wind_data.py:70` — **medium**/conf=medium · eje F

**fetch_wind_point indexa el array horario con datetime.now().hour sin verificar el array 'time' que devolvio Open-Meteo**

wind_data.py:70-72 `now_hour = datetime.now(timezone.utc).hour` y `hourly.get(f'wind_speed_{level}', [None]*24)[now_hour]`. Nunca se lee `hourly['time']` ni se comprueba que el elemento now_hour corresponda a la hora actual — el codigo asume que el array arranca en 00:00 UTC de hoy y tiene 24 entradas. Contraste dentro del mismo repo: src/fetch/gfs_profile.py:117-133 SI lee `times`, busca el indice por match exacto o por menor gap, y expone `time_gap_min` en la salida (l.159).

*Escenario de fallo:* Open-Meteo agrega past_days por defecto a la respuesta (o cambia el origen del array, como ya cambio la convencion de nombres de variable en 2025 segun el comentario de l.34-35). El indice `now_hour` pasa a apuntar a una hora de ayer. Las flechas de viento del mapa nacional y el resumen '500 hPa 45 km/h@280°' del encabezado del volcan muestran un viento de otro momento, sin ninguna senal de error. El operador comunica una direccion de dispersion equivocada.

*Fix sugerido:* Reusar la logica de gfs_profile: buscar el indice en `hourly['time']` por el timestamp objetivo, y devolver el gap junto con el dato (o None si supera un umbral).

### `src/fetch/viirs_firms.py:85` — **medium**/conf=high · eje F

**_parse_firms_csv convierte un error del servicio FIRMS (MAP_KEY invalida, cuota agotada) en lista vacia = 'sin anomalia termica', rompiendo el contrato del propio modulo**

viirs_firms.py:84-85 `if 'latitude' not in header or 'longitude' not in header: return []` con el comentario 'no es el CSV esperado (error del servicio)', y el docstring l.77-78 dice explicitamente que respuestas como 'Invalid MAP_KEY.' devuelven lista vacia. Pero el contrato declarado de la funcion publica (l.123-125) es 'None si falta el MAP_KEY o falla la red (distinto de "vacia" = sin calor)'. FIRMS devuelve estos errores con HTTP 200 y cuerpo de texto plano, asi que el `raise_for_status()` de l.142 no los atrapa.

*Escenario de fallo:* La MAP_KEY de FIRMS caduca o se pasa de la cuota horaria (FIRMS limita transacciones). El servicio responde 200 con 'Invalid MAP_KEY.'. La vista de complemento VIIRS informa 0 hot spots 375 m sobre un volcan austral sin cobertura VOLCAT — el unico chequeo termico independiente de GOES para esos volcanes — y se lee como ausencia de calor.

*Fix sugerido:* Que `_parse_firms_csv` devuelva None (o levante) cuando el cuerpo no es el CSV esperado, y que `fetch_viirs_firms_hotspots` lo propague como None, cumpliendo su docstring. Un test con el cuerpo literal 'Invalid MAP_KEY.'.

### `src/fetch/gfs_archive.py:262` — **medium**/conf=medium · eje F

**dict(zip(got, vals)) sin verificar longitudes: si eccodes decodifica un numero de mensajes distinto al de rangos pedidos, el perfil queda DESALINEADO en silencio**

gfs_archive.py:260-263 `got, raw = _collect_raw(...)`; `vals = _decode_values_at_point(raw, lat, lon)`; `vmap = dict(zip(got, vals))`. `got` es la lista de claves (var, nivel) en el orden en que se pidieron (l.158-166) y `vals` sale de iterar los mensajes GRIB2 del buffer concatenado (l.186-201). `zip` trunca silenciosamente en la mas corta y desplaza todo el resto si alguno no coincide. No hay `assert len(vals) == len(got)` ni ninguna verificacion de que el mensaje decodificado sea la variable/nivel esperados (eccodes expone shortName/level y no se consultan). Identico en el camino de viento, l.318. Los rangos vienen del `.idx` con `end = start_del_siguiente - 1` (l.74-75) y el ultimo registro usa `size-1` (l.163) — cualquier registro que contenga mas de un mensaje GRIB2, o un `.idx` con una linea saltada, desplaza el mapeo.

*Escenario de fallo:* Validacion historica del Lascar: se pide el perfil T(z) del ciclo GFS del evento. Un registro trae dos mensajes; `vals` sale con un elemento de mas y a partir de ahi cada temperatura se atribuye al nivel de presion equivocado. El perfil se ve plausible (monotono, con tropopausa), `altitudes_from_bt` lo consume sin quejarse y la altura de pluma validada sale sistematicamente corrida en kilometros. Como se usa para VALIDAR el retrieval propio, el error se propaga al veredicto del metodo.

*Fix sugerido:* Verificar `len(vals) == len(got)` y abortar si no; mejor aun, leer `shortName` y `level` de cada mensaje con eccodes y construir el vmap con la clave LEIDA del mensaje en vez de asumir el orden.

### `src/export/geotiff.py:31` — **medium**/conf=medium

**El GeoTIFF marca nodata=0, que en un RGB enmascara pixeles VALIDOS — en Ash RGB, justamente los topes de nube mas frios**

geotiff.py:31 `nodata: Optional[int] = 0` y l.83 `'nodata': nodata` en el profile, con el argumento (l.41-42) de que 0 son 'pixeles negros del relleno de tile que no cubre'. Pero GDAL aplica el nodata POR BANDA: cualquier pixel cuyo valor en una banda sea 0 se lee como sin-dato en esa banda. En la receta Ash RGB del proyecto (CLAUDE.md: Blue = BT13 estirado en [243.6, 302.4] K), todo tope de nube mas frio que 243.6 K se satura a 0 en el canal azul, que es exactamente la firma de una columna alta.

*Escenario de fallo:* El geologo exporta el GeoTIFF de la vista de volcan durante un evento y lo abre en QGIS meses despues para el informe. Los pixeles del tope mas alto y frio de la columna aparecen con el canal azul enmascarado: la composicion RGB se rinde distinta a la que se vio en el dashboard, y una estadistica zonal sobre el raster excluye justamente los pixeles del nucleo de la pluma. El PNG y el GeoTIFF del mismo frame no coinciden y nadie sabe cual creer.

*Fix sugerido:* Default `nodata=None` (dejar el negro como valor valido) y, si hace falta marcar el relleno, escribir una 4a banda de mascara alpha o un dataset mask explicito. Como minimo documentar la trampa en el help del boton de descarga.

### `src/fetch/gfs_profile.py:288` — **medium**/conf=high · eje F

**fetch_gfs_wind_profile elige la hora mas cercana sin medir ni reportar el gap — asimetrico con fetch_gfs_profile, que si lo hace**

gfs_profile.py:277-293: si el timestamp objetivo no esta en `times`, toma `min(range(len(times)), key=_gap)` y devuelve el dict SIN `time_gap_min` y SIN el warning de gap>180 min. La funcion hermana `fetch_gfs_profile` (misma API, mismo modulo) si mide el gap (l.133), avisa si supera 180 min (l.138-140) y lo publica en la salida (l.159). Los perfiles archivados (`gfs_archive.fetch_gfs_wind_profile_archive`, l.332) tambien devuelven time_gap_min: el unico camino sin gap es este.

*Escenario de fallo:* Se corre el arbitro de altura por cizalla (Fase 3c) sobre un evento de hace 4 dias. `past_days=2` no cubre esa fecha, asi que Open-Meteo devuelve su ventana y la funcion elige el extremo mas cercano, a ~48 h del scan. El perfil de viento u(z), v(z) es de otro dia. La altura por cizalla sale con una precision aparente y no hay ningun campo en la salida que permita al llamador (ni al lector del informe) darse cuenta.

*Fix sugerido:* Factorizar la seleccion de indice + medicion de gap en un helper compartido por las dos funciones y devolver `time_gap_min` tambien en el perfil de viento.

### `src/fetch/goes_s3.py:242` — **low**/conf=high

**get_latest_time usa fs.ls crudo (sin _retry_s3) y su parseo puede levantar ValueError no atrapado**

goes_s3.py:231-258: a diferencia de `list_files` (l.135, que si envuelve con `_retry_s3`), aca la listada es `files = fs.ls(path)` pelada dentro de un `try/except FileNotFoundError` (l.256). Cualquier otra excepcion (EndpointConnectionError, ReadTimeout) sale de la funcion; y el bloque de parseo (l.246-254, `fname.index('_s')`, `int(...)`) esta DENTRO del mismo try pero solo captura FileNotFoundError, asi que un nombre de archivo inesperado propaga ValueError. Nota: grepeando el repo, esta funcion no tiene llamadores vivos hoy (los pipelines usan download_band/download_band_at), pero es la primitiva de 'ultimo scan disponible'.

*Escenario de fallo:* Si se vuelve a cablear (p.ej. para un badge de 'ultimo L1b disponible'), un corte transitorio de S3 revienta la pagina en vez de degradar, y NOAA cambiando el patron de nombre tumba la vista entera.

*Fix sugerido:* Envolver con `_retry_s3`, o directamente reimplementarla sobre `nearest_granule_key` + `_scan_start`, que ya resuelven el borde de hora y el parseo. Encaja con el pendiente de `abi_common.py`.

### `src/fetch/historic_rammb.py:92` — **low**/conf=high · eje F

**detect_seconds_offset valida un tile por TAMANO (>1000 bytes) y confunde 'red caida' con 'fecha fuera del archivo'**

historic_rammb.py:90-97: `if r.status_code == 200 and len(r.content) > 1000: return ss`, sin magic bytes PNG ni content-type — una pagina de error HTML de mas de 1 KB servida con 200 se acepta como tile valido y fija un offset de segundos falso. Y el `except Exception: continue` de l.95-96 hace que 60 fallos de red seguidos terminen en el mismo `return None` (l.97) que significa, segun el docstring l.78, 'la fecha no esta en archive'.

*Escenario de fallo:* Se prepara un caso historico para un informe y RAMMB esta caido: la herramienta informa que la fecha no esta archivada. Se descarta el evento como no reconstruible cuando en realidad los tiles existen.

*Fix sugerido:* Validar los 8 bytes de firma PNG (o content-type) en vez del tamano, y separar el retorno: None = fecha ausente, excepcion/sentinela distinta = no pude consultar (contar cuantas de las 60 sondas fallaron por red).

### `src/fetch/hires_loop_cache.py:188` — **low**/conf=high

**fetch_hires_loop_frames calcula el bbox con lat/lon del manifest FUERA del try — un scope sin coords levanta TypeError y tumba la vista**

hires_loop_cache.py:186-189: `lat, lon = sc.get('lat'), sc.get('lon')` y acto seguido `bounds = {'lat_min': lat - r_deg, ...}`. El `try/except Exception` de la funcion empieza recien en l.190. Si el manifest trae un scope sin lat/lon (bug del builder, formato viejo), `None - 0.5` levanta TypeError sin capturar.

*Escenario de fallo:* Un manifest_loop.json escrito por una version del builder que no serializa lat/lon deja la vista de loops del volcan con un stack trace de Streamlit en vez de degradar a 'sin loop hi-res'.

*Fix sugerido:* `if lat is None or lon is None: return None, None` antes de armar los bounds.

### `src/fetch/volcat_api.py:311` — **low**/conf=medium

**volcat_at_time resta un datetime aware (del frame) menos target_dt sin normalizar tz — un target naive levanta TypeError**

volcat_api.py:308-311: `fdt = _parse_volcat_frame_dt(...)` devuelve siempre tz-aware (l.273 `tzinfo=timezone.utc`) y la linea 311 hace `abs((fdt - target_dt).total_seconds())` sin ningun `if target_dt.tzinfo is None`. Los demas fetchers del repo si normalizan (goes_fdcf.py:397-398, goes_acha.py:232-233, gfs_profile.py:89-90). Los llamadores actuales pasan aware (build_backfill.py:307 usa `.replace(tzinfo=timezone.utc)`), por eso no se ve hoy.

*Escenario de fallo:* Un script de validacion o un llamador nuevo pasa un datetime naive (lo mas facil de escribir): TypeError 'can't subtract offset-naive and offset-aware datetimes' en medio del backfill, en vez de resolver la hora asumiendo UTC como hace todo el resto del codigo.

*Fix sugerido:* Normalizar `target_dt` a UTC al entrar, igual que goes_fdcf/goes_acha.

### `dashboard/views/modo_guardia_volcan.py:957` — **low**/conf=high · eje F

**El encabezado de la grilla de volcan hace DESAPARECER la linea de viento cuando Open-Meteo falla; la vista nacional si tiene diagnostico**

modo_guardia_volcan.py:227-234 `_wind_at_volcano` arma `out` solo con los niveles que devolvieron dato (y esta cacheado 1 h, ttl=3600, asi que un fallo se congela una hora); l.955-965 `if wind:` / `if bits:` -> con dict vacio `wind_summary` queda en cadena vacia y el encabezado se renderiza sin ninguna mencion al viento. En cambio live_viewer.py:951-953 detecta la grilla vacia y llama a `fetch_wind_diagnostic` para mostrar el motivo.

*Escenario de fallo:* Open-Meteo cae. En la vista de volcan el encabezado se ve completo y normal, solo que sin el fragmento de viento — nada indica que falta un dato, y el operador puede no notar la ausencia justo cuando necesita la direccion de dispersion.

*Fix sugerido:* Rotular explicitamente 'viento GFS no disponible' cuando `_wind_at_volcano` vuelve vacio, y no cachear 1 h el resultado vacio.

### `src/fetch/volcat_api.py:251` — **low**/conf=high

**volcat_latest accede a last['filename'] con corchetes mientras todo el resto del dict usa .get -> KeyError si SSEC devuelve un frame parcial**

volcat_api.py:250-260: `'datetime': last.get('datetime')`, `'annot_url': ... if last.get('annot')`, `'sat': ... if last.get('filename')` — pero l.251 `'image_url': BASE + last['filename']` es acceso directo. Mismo caso en volcat_at_time l.320. El repo ya vivio el caso de respuesta parcial de SSEC (frames sin 'coordinates'), documentado en tests/test_volcat_guard.py.

*Escenario de fallo:* SSEC devuelve una entrada de frame sin 'filename' (respuesta parcial, sector recien creado): KeyError sin atrapar dentro de una funcion cacheada de Streamlit -> excepcion visible en el panel VOLCAT en vez de 'sin frame disponible'.

*Fix sugerido:* `fn = last.get('filename'); if not fn: return None` antes de armar el dict, en las dos funciones.

## Física y retrievals  ·  19 hallazgos

**Verificado y limpio** (un núcleo sano también es información):

- Planck: rad_to_bt (brightness_temp.py:33-34) usa EXCLUSIVAMENTE fk1/fk2/bc1/bc2 leidos del NetCDF L1b (lineas 26-29); scene.planck_coefs (scene.py:71-72) idem. Ninguna constante Planck hardcodeada en todo src/process. Verificado numericamente: planck_rad_from_bt compuesta con la inversa da error maximo 5.7e-14 K sobre 180-340 K con los 3 juegos de coeficientes reales (C11/C14/C15 de tests/conftest.py).
- Unidades: BT siempre en K; gfs_profile._parse_profile (linea 53) suma 273.15 porque Open-Meteo entrega degC, y gfs_archive (linea 275) NO lo hace porque GRIB2 TMP ya viene en K. Correcto en ambos, con fuentes distintas.
- Proyeccion geoestacionaria: geo.get_lat_lon (lineas 386-409) reproduce exactamente las formulas del GOES-R PUG Vol.3 §4.2.8 (coeficientes a/b/c, s_x=r_s cos x cos y, s_y=-r_s sin x, s_z=r_s cos x sin y, lat con (r_eq/r_pol)^2, lon = lambda_0 - atan(s_y/(H-s_x))); H se arma sumando perspective_point_height + semi_major_axis (lineas 372-374), correcto. Pixeles fuera del disco quedan NaN via discriminante<0 (linea 395).
- Parallax: verificado numericamente. satellite_zenith_angle(-40,-72) = 46.38 deg, tan = 1.0494, coincide con el ~1 km por km de altura que declara el docstring. parallax_shift(-40,-72,10 km) desplaza 10.49 km HACIA el subsatelite (lat +0.094 hacia el ecuador, lon -0.007 hacia -75). Signo y magnitud correctos; el docstring advierte bien que la altura debe ser AMSL.
- gfs_profile._monotone_tropo_branch (lineas 183-189): la envolvente fria produce una T estrictamente decreciente, asi que np.interp recibe xp ascendente tras el reverse (linea 209) y el mapeo BT->z queda monotono. Resuelve correctamente el caso de inversion termica (verificado con el PROFILE sintetico).
- Guard de mismo-scan unificado en scene.acquire_ash_scene (lineas 286-291): las 3 bandas deben venir del mismo scan o se devuelve no_data. Correcto y en un solo lugar.
- co2_verdict (wen_rose_height.py:233-252): el gate CO2_ARBITER_MIN_COTA_KM=7.0 esta bien planteado — reconoce la degeneracion fina-alta / opaca-baja y devuelve 'no_discrimina' en vez de un falso verde.
- _parse_wind_profile (gfs_profile.py:309-312): convencion meteorologica correcta (direccion = de donde viene), u=-s sin(dir), v=-s cos(dir).
- gfs_archive._grid_index (lineas 100-112): normaliza lon a [0,360) en ambos extremos, asi que Chile (lon negativa) cae en el indice correcto de la grilla GFS 0.25 deg.
- Receta Ash RGB (ash_rgb.py:49-55 + config.py:146-150) coincide con el quick guide RAMMB/CIRA: R=B15-B14 [-6.7,2.6], G=B14-B11 [-6.0,6.3], B=B13 [243.6,302.4].
- hires_pipeline: el pan-sharpening deriva el grid 0.5 km como EXACTAMENTE 2x los indices del recorte 1 km (lineas 349-352), aprovechando el anidamiento nativo del ABI. Sin ghosting por recortes independientes; el razonamiento del comentario es correcto.


### `src/process/beta_ratios.py:280` — **high**/conf=high · eje F

**Una pluma de ceniza OPACA se clasifica como 'hielo' y dispara la alerta de falso positivo — justo el caso mas peligroso**

cloud_emissivity (beta_ratios.py:280) recorta epsilon a [1e-4, 1-1e-6] SIN declarar invalido el retrieval cuando epsilon sale del rango util. El beta-ratio de Pavolonis 2010 solo discrimina composicion en nubes semi-transparentes: al hacerse opaca la nube, eps(11), eps(12) y eps(8.5) tienden juntos al mismo valor y beta -> 1, que es el ancla del HIELO (BETA_ANCHORS, linea 258). No hay ningun gate de epsilon antes de classify_composition. Reproducido numericamente con el forward-model y los coeficientes Planck reales del propio repo (tests/conftest.py COEF11/14/15, Ts=292 K, Tc=228 K, T_ref=tropopausa 220 K): t11=0.35 -> beta12_11=0.575, label 'ceniza' OK; t11=0.001 -> beta12_11=0.896, beta85_11=1.010, label 'hielo', is_ash=False; t11=0 (opaca total) -> beta12_11=0.976, label 'hielo'. Mismo resultado con un pixel mas calido que el cielo claro (eps<0 recortado al piso): beta=1.0 exacto -> 'hielo'.

*Escenario de fallo:* Erupcion con pluma densa proxima al crater (Villarrica o Llaima con columna sostenida). detect_ash_enhanced la marca bien y Wen-Rose reporta un tope. Pero como la pluma es opaca, beta_composition devuelve 'hielo' con is_ash=False, y wen_rose_height.py:605-607 agrega al panel el flag 'beta-ratios sugieren composicion hielo (no silicato): posible falso positivo de ceniza'. El geologo de turno lee, en el momento de mayor peligro, que su deteccion probablemente sea un cirro. Es asimetria de consecuencias pura: el retrieval falla precisamente hacia el lado que resta urgencia.

*Fix sugerido:* Devolver None (no clasificar) cuando eps(11) queda fuera de una banda utilizable — p.ej. eps<0.05 (nube no detectable) o eps>0.85 (opaca: beta degenera a 1). Propagar ese estado como 'opaca: beta no discrimina' en vez de un veredicto de composicion, y NO emitir el flag de falso positivo en ese regimen. Ademas nunca recortar un eps NEGATIVO al piso: eso significa que el modelo (obs mas frio que el cielo claro) no se cumple -> NaN, no 1e-4.

### `src/process/wen_rose_height.py:363` — **high**/conf=high · eje E

**Sin tropopausa en el perfil GFS, el guard de runaway de Wen-Rose se apaga entero y el piso arbitrario de la grilla (180 K) se reporta como tope confiable**

_revert_unreliable (wen_rose_height.py:363) hace 'z_trop = trop["z_m"] if trop else np.inf'. Con trop=None la condicion alt < z_trop-1 es SIEMPRE verdadera -> reliable=True para todo pixel bien-condicionado. _tropopause (gfs_profile.py:66-69) devuelve None si NINGUN nivel cae en 6000-20000 m, y _parse_profile (lineas 48-52) descarta silenciosamente los niveles con datos faltantes mientras que fetch_gfs_profile solo exige len(levels)>=3 (linea 143) — o sea que un perfil truncado en la troposfera baja pasa el filtro. Reproducido: con el PROFILE de conftest recortado a z<6000 m y un pixel forward-modelado (Tc=228 K, t11=0.35, beta_true=0.564), solve_tc_grid con beta=0.7 satura en Tc=180.0 K (= tc_floor_k, linea 256) con well_constrained=True; _revert_unreliable devuelve reliable=True y altitudes_from_bt clampea al tope del perfil truncado (5600 m). Con el perfil completo el mismo pixel SI se revierte (reliable=False). Ademas _top_stats (linea 339) pone capped=zeros cuando trop es None, asi que n_capped=0 y all_capped=False: no sale ni un solo aviso.

*Escenario de fallo:* Open-Meteo devuelve nulls en los niveles altos (pasa de forma intermitente en la API pressure-level). El perfil llega con 4 niveles bajo 6 km, tropopause=None. El panel de altura de volcan muestra un tope numerico (el techo del perfil truncado) con confianza 'media', sin flag de tropopausa, sin n_capped y sin banda que avise. El operador lee un tope de pluma que es un artefacto del piso de la grilla del solver, no una medicion.

*Fix sugerido:* Tratar profile['tropopause'] is None como condicion de no-reporte (o al menos como flag duro + confianza 'muy baja') en los tres retrievals. En _revert_unreliable, ademas del cap por tropopausa, revertir tambien cuando Tc toca el borde de la grilla (Tc <= tc_floor_k + paso) o cuando la altitud queda clampeada al ultimo nivel del perfil. Y exigir en fetch_gfs_profile que haya al menos un nivel sobre 6 km antes de devolver el perfil.

### `src/process/wen_rose_height.py:314` — **high**/conf=high · eje E

**solve_tc_grid no mide la BONDAD del ajuste, solo el ancho del minimo: con beta equivocado el argmin cae en el borde de la grilla y sale 'well_constrained=True'**

Lineas 314-327: se toma idx=argmin(resid) y luego well_constrained se decide SOLO por tc_span (ancho del intervalo dentro de RES_TOL del minimo). min_res nunca se compara contra una tolerancia absoluta. Cuando el beta supuesto no es el real no existe ningun Tc que satisfaga t12 = t11^beta, el residuo es monotono y el minimo cae en el extremo de la grilla, donde el span es estrecho -> well_constrained=True. Reproducido con el forward-model del repo (Tc=228 K, Ts=292 K, beta_solver=0.7): con beta_true=0.564 — que es justamente el ancla de CENIZA de Pavolonis 2010 Tabla 2, r_eff 2 um, citada en el propio modulo linea 72 — el solver satura en Tc=180.00 K (tc_floor_k) con well_constrained=True para t11=0.20, 0.35, 0.60 y 0.80. Con beta_true=0.95 devuelve Tc=BT11 (sin correccion). Solo con beta_true=0.7 recupera Tc=228.0 correctamente.

*Escenario de fallo:* Pluma distal de ceniza fina (r_eff ~2 um, beta real ~0.56, el caso mas frecuente lejos del crater). El solver satura en 180 K en la mayoria de los pixeles. Hoy eso se salva de rebote porque _revert_unreliable clampea contra la tropopausa (ver D2) — pero es una red secundaria: si el perfil no trae tropopausa (D2), o si el piso tc_floor_k se bajara, el tope reportado seria el borde de una grilla numerica presentado como medicion fisica. Incluso funcionando, la etiqueta well_constrained=True es falsa y contamina wen_rose_confidence.

*Fix sugerido:* Agregar un umbral absoluto de residuo: si min_res supera el ruido esperado del acople (derivable del NEdT de ~0.1 K de C14/C15 propagado a t12), marcar solved=False. Y tratar explicitamente el borde: si idx==0 o idx==n_grid-1, el minimo esta en el limite de busqueda -> no es una solucion, es una saturacion.

### `src/fetch/gfs_profile.py:209` — **medium**/conf=high · eje E

**El mapeo BT->altitud no tiene piso de terreno: sobre el Altiplano puede devolver topes de pluma kilometros POR DEBAJO del crater**

altitudes_from_bt (linea 209) usa np.interp, que clampea al extremo calido del perfil = kept[0], el nivel de presion mas bajo disponible (1000 hPa). Sobre los Andes ese nivel es una extrapolacion bajo tierra. Ningun retrieval consulta la elevacion del volcan: Volcano.elevation existe (src/volcanos.py:16, Lascar=5592 m) y grep confirma que NO se usa en src/process ni en dashboard/views/volcat_viewer.py. Verificado con el PROFILE de tests/conftest.py (que es el perfil sintetico DE LASCAR y tiene su nivel mas bajo en z=100 m): BT=295 K -> 100 m; BT=290 K -> 800 m; BT=285 K -> 1500 m. El crater de Lascar esta a 5592 m: un pixel de ceniza a 285 K se mapea 4.1 km BAJO el vent.

*Escenario de fallo:* Pluma tenue y calida sobre Lascar, Guallatiri o Parinacota (crateres a 5.5-6.3 km). Los pixeles marcados como ceniza mapean a 0.8-1.5 km AMSL. El p95 puede quedar por debajo de la elevacion del volcan y el panel muestra 'tope 1.5 km' con confianza media. El operador lee una pluma que no despega, cuando la geometria hace imposible que un tope este bajo su propio crater. Ademas in_reliable_band (3-12 km) marca el caso como 'fuera de banda' por la razon equivocada, ensuciando el diagnostico.

*Fix sugerido:* Pasar volcano.elevation a los retrievals y (a) descartar del campo los pixeles cuya altitud queda bajo la elevacion del vent (menos un margen de ~500 m por la resolucion de 2 km), o (b) al menos emitir un flag duro y no reportar top_km cuando el p95 cae bajo el crater. Complementariamente, recortar el perfil GFS a los niveles con z >= elevacion del terreno antes de construir la rama monotona.

### `src/process/scene.py:138` — **medium**/conf=high · eje B

**El desfase temporal del perfil GFS se mide y se tira: un perfil viejo se presenta igual que uno fresco**

fetch_gfs_profile calcula gap_min y lo devuelve como 'time_gap_min' (gfs_profile.py:133,159) y solo escribe un logger.warning si supera 180 min (linea 138-140), pero DEVUELVE el perfil igual. scene.base_out (scene.py:138-141) copia unicamente 'profile_time' (el string valid_time) y NO 'time_gap_min'. grep sobre todo el repo confirma que time_gap_min solo aparece en scripts/ (compare_lvtp_vs_gfs.py:70, validate_gfs_archive.py:95) y en gfs_archive.py; ninguna vista del dashboard ni ningun retrieval lo lee ni lo umbraliza. Lo mismo con latency_min, que scene.py:309 calcula y volcat_viewer.py:956 muestra solo como caption informativa sin umbral.

*Escenario de fallo:* Open-Meteo sirve un forecast truncado o desfasado (pasa cuando el ciclo GFS se atrasa). El perfil elegido queda a horas del scan. La conversion Teff->altura usa un T(z) del momento equivocado — sobre Chile un frente puede mover la isoterma varios cientos de metros en altura — y el panel de altura muestra el numero con la misma confianza 'media' y sin ningun aviso. Es el modo de fallo canonico del SDA: dato viejo leido como dato bueno. El contraste es que wind_shear_height.py:287-291 SI implementa este guard (MAX_WIND_AGE_H) y rechaza; el camino termico, que es el que esta en produccion, no.

*Fix sugerido:* Propagar time_gap_min a AshScene y a base_out; agregar un flag ('perfil GFS a N min del scan') sobre un umbral (p.ej. 90 min) y degradar la confianza. Reusar el mismo criterio de MAX_WIND_AGE_H que ya existe en el modulo de cizalla.

### `src/process/wen_rose_height.py:294` — **medium**/conf=high · eje E

**'Sin contraste termico' se reporta al operador como 'todos los pixeles opacos'**

El gate de elegibilidad de solve_tc_grid es 'elig = finite & (ts > bt11 + 0.5) & (btd < 0.0)' (linea 294). Si Ts sale mal estimado o si el fondo es genuinamente mas frio que la pluma (noche sobre nieve/altiplano, pluma sobre mar frio), elig=False para todo el bloque, Tc cae al fallback opaco Tc=BT11 (linea 328) y n_corrected=0. Verificado: con Ts=250 K y bt14=256.2 K el solver devuelve solved=False y Tc=BT11 sin distinguir el caso. En el panel, volcat_viewer.py rama else (bloque de captions ~lineas 985-991) escribe literalmente 'Todos los pixeles resultaron opacos -> Wen-Rose = BT-matching (sin correccion de emisividad que aplicar)'. No hay ninguna rama para 'no se pudo evaluar por falta de contraste'.

*Escenario de fallo:* Escena nocturna de invierno con nieve fresca alrededor del volcan: clear_sky_bt devuelve un Ts frio, ningun pixel es elegible, y el dashboard afirma que la pluma es opaca — una conclusion FISICA que el codigo no midio. Como 'opaca' implica que la cota BT-matching es cercana al tope real, el operador confia en un numero que en realidad no tiene correccion evaluada y que en una pluma semitransparente subestima el tope.

*Fix sugerido:* Devolver desde solve_tc_grid el conteo de pixeles NO elegibles por falta de contraste (elig False con btd<0) separado del de opacos genuinos, y en el panel distinguir 'sin contraste termico suficiente: la correccion no pudo evaluarse' de 'pluma opaca'. Agregar flag cuando la fraccion no-elegible sea alta.

### `src/process/geocolor_lite.py:324` — **medium**/conf=high · eje E

**solar_elevation omite la ecuacion del tiempo: error medido de hasta 4.0 grados, no los 0.5 que declara el docstring**

La linea 324 calcula el angulo horario como 'ha = (hour + lon/15 - 12)*15', es decir hora solar MEDIA sin ecuacion del tiempo; la declinacion usa la formula de Cooper (linea 322), que ya tiene ~0.5 deg de error propio. El docstring (linea 313) afirma 'Precision ~0.5 grados'. Verificado contra el algoritmo solar NOAA implementado en el momento, en Lascar (-23.37,-67.73) sobre 5 fechas x 24 h: diferencias de +3.44 deg (11-feb), -3.42 y +3.98 deg (3-nov), 1.46 deg (26-jul); maximo absoluto de la muestra 4.0 deg. En agosto el error casi se anula (0.3 deg) — de ahi que no se note en pruebas hechas hoy.

*Escenario de fallo:* hires_pipeline.py:68 usa DAY_NIGHT_THRESHOLD_DEG = 5.0 con esta funcion (linea 309). Cerca de los equinoccios/principios de noviembre el error de 4 deg equivale a ~16-20 min de reloj: un scope se declara NOCHE cuando el sol ya esta a 9 deg (se pierde el frame visible de 0.5 km, el mas util para ver el crater, y el loop queda con un hueco o con IR) o se declara DIA con el sol bajo 1 deg y el TrueColor sale casi negro y el contrast_stretch lo amplifica a ruido. En un loop rodante de 8 h el borde del terminador queda inconsistente entre frames.

*Fix sugerido:* Agregar la ecuacion del tiempo (formula de Spencer o la de NOAA, ~8 lineas, sin dependencias) al angulo horario, y corregir el docstring a la precision real. Alternativamente subir el umbral a 8-10 deg para que el error no cruce el switch.

### `src/process/beta_ratios.py:301` — **medium**/conf=high · eje A

**classify_composition no tiene distancia maxima al ancla: cualquier par (beta12, beta85), por absurdo que sea, recibe una etiqueta de composicion**

Lineas 301-306: se recorre BETA_ANCHORS quedandose con el minimo de la distancia euclidea y se devuelve siempre un label, sin comparar best_d contra ningun umbral. El docstring del modulo (linea 218 de la ficha SDA) reconoce 'distancia sin normalizar (audit F5)' pero el problema separado es que no hay rechazo. Medido con el forward-model del repo: una pluma opaca da distancia 0.23-0.246 y se etiqueta 'hielo' con la misma autoridad que una semitransparente a distancia 0.008. Los callers (wen_rose_height.py:593-607) usan comp['beta_12_11'] y comp['is_ash'] sin mirar comp['distance'] ni una sola vez.

*Escenario de fallo:* Escena con fondo mal estimado o con pluma parcialmente opaca: los beta salen fuera de la nube de los tres anclas, pero classify_composition devuelve el ancla mas cercana igual. Si es 'hielo' o 'agua', wen_rose_height.py:605 dispara 'posible falso positivo de ceniza' sobre una deteccion valida; si es 'ceniza', el panel muestra la confirmacion positiva de composicion (volcat_viewer, bloque comp_html) sobre un par de betas sin sustento. En ambos sentidos el operador recibe una confirmacion de composicion que el dato no soporta.

*Fix sugerido:* Devolver label=None (o 'indeterminado') cuando best_d supere un umbral calibrado (la separacion entre anclas ceniza-hielo es ~0.52 en beta12_11, asi que algo del orden de 0.15-0.2 es defendible), y no emitir ningun flag de composicion en ese caso. Normalizar la distancia por la dispersion de cada eje.

### `src/process/ash_detection.py:165` — **medium**/conf=medium · eje E

**El test tri-espectral queda dominado por el termino de SO2 y deja de filtrar cirros justo sobre plumas volcanicas de gas**

detect_ash_enhanced calcula 'btd_tri = (bt11 - bt14) + (bt15 - bt14)' y exige < 0 (lineas 165, 170). El primer sumando es exactamente el indicador de SO2 del proyecto (generate_so2_indicator, ash_rgb.py:121, y so2_context, scene.py:95), que sobre una pluma con SO2 vale -3 a -15 K. Con un solo pixel de SO2 el termino domina y la condicion 3 se cumple trivialmente sin importar el signo de (bt15-bt14): el filtro anti-cirro deja de aportar discriminacion. Evidencia adicional en el propio fixture del proyecto: tests/conftest.py:69-71 construye C11 como 'bt[14] - 10.0' con el comentario explicito 'para pasar el test tri-espectral: (-10)+(+7.55) = -2.45 < 0' — la escena sintetica de referencia pasa el test tri-espectral por un offset tipo SO2, no por microfisica de ceniza.

*Escenario de fallo:* Nevados de Chillan o Copahue con emision sostenida de SO2 y cirros finos encima (invierno chileno). Los cirros que caigan del lado negativo del split-window BTD ya no son filtrados por la condicion 3, porque el SO2 la satisface sola. La mascara de ceniza se infla, mask_px sube y los tres retrievals de altura miden sobre pixeles de cirro. Como el proyecto ya documenta 30-60% de falsos positivos por cirro/nieve, esto ataca justo la mitigacion declarada. Nota: el propio pipeline ya reconoce el caso inverso (SO2 sin ceniza) en volcat_viewer.py, pero via so2_px, no via el tri-espectral.

*Fix sugerido:* Separar los dos terminos en vez de sumarlos: exigir (bt15-bt14) > 0 (el termino anti-cirro real de Pavolonis) como condicion propia, y usar (bt11-bt14) como indicador de SO2 aparte, no como parte de la misma suma. Y agregar un fixture sintetico donde C11 NO tenga el offset de SO2, para que el test tri-espectral se ejercite por la razon correcta.

### `dashboard/views/volcat_viewer.py:920` — **medium**/conf=high · eje F

**Los KPI de altura se muestran con 0.1 km de precision y, salvo Wen-Rose, sin ninguna banda de incertidumbre**

Lineas 920 y 926: kpi_card(f"{acha['top_km']:.1f} km", 'ACHA NOAA - p95') y kpi_card(f'{bt_cota:.1f} km', 'BT-matching - cota'). Ninguno de los dos lleva banda. Solo Wen-Rose la lleva, y condicionada a que (hi-lo) > 0.3 (linea 934). Las fuentes de error declaradas por el propio proyecto son mucho mayores que 0.1 km: la ficha SDA de wen_rose_height.py:8 dice 'sesgo IR -0.4..-0.8 km'; la resolucion vertical del perfil GFS entre 300 y 200 hPa (conftest PROFILE: 9200 -> 12000 m) es de ~2.8 km por nivel, y entre 200 y 150 hPa reales ronda 1.6 km; la resolucion horizontal del ABI IR es 2 km.

*Escenario de fallo:* El panel muestra 'ACHA 8.3 km' y 'BT-matching 7.9 km' uno al lado del otro. El operador lee una diferencia de 0.4 km entre metodos como informacion — cuando esta muy por debajo de la incertidumbre de cualquiera de los dos, y por debajo incluso del espaciado de los niveles GFS que sostienen el BT-matching. Si esa diferencia se traslada a un informe o a una decision de nivel de alerta, se le esta dando peso a ruido.

*Fix sugerido:* Reportar los topes redondeados a 0.5 km, o mostrar la cifra con una banda explicita (+/-1 km es honesto dado el sesgo IR declarado). Como minimo, agregar bajo los KPI de ACHA y BT-matching la misma nota de incertidumbre que ya lleva Wen-Rose.

### `src/process/brightness_temp.py:32` — **medium**/conf=medium · eje E

**rad_to_bt nunca consulta el DQF del L1b: pixeles marcados como no usables entran a la mascara de ceniza como BT validas**

rad_to_bt (lineas 25-34) solo filtra rad<=0 ('rad_safe = rad.where(rad > 0, np.nan)'). No lee ds['DQF'], que en ABI L1b marca pixeles no usables, saturados o fuera de rango. scene.acquire_ash_scene (lineas 247-248 y 275-276) llama rad_to_bt directamente sobre el recorte sin tocar DQF. El contraste es que el camino ACHA SI lo hace: goes_acha._apply_quality filtra por DQF con DQF_KEEP_DEFAULT (acha_plume_height.py:137,141).

*Escenario de fallo:* Un pixel con detector degradado o saturado en C15 devuelve una radiancia fisicamente valida pero incorrecta. El BTD 11-12 de ese pixel puede caer bajo -1 K y sumarse a la mascara de ceniza. Con pocos pixeles (mask_px < 15 degrada la confianza, pero 5-14 sigue reportando) un puñado de pixeles malos puede generar un no_plume falso-positivo o desplazar el p95 del tope. Como no hay traza de DQF, el geologo no tiene forma de saber que la deteccion venia de pixeles marcados como no usables por NOAA.

*Fix sugerido:* Leer ds['DQF'] en scene.acquire_ash_scene junto con la BT y enmascarar a NaN los pixeles fuera del conjunto usable, siguiendo el mismo patron que goes_acha._apply_quality. Reportar cuantos pixeles se descartaron por DQF en el dict de salida.

### `src/process/wind_shear_height.py:133` — **low**/conf=high · eje A

**La cizalla se mide contra TODA la columna incluida la estratosfera, asi que 'discriminates' da True casi siempre**

Linea 133: 'shear = float(np.hypot(u - u[k], v - v[k]).max())' sobre todos los niveles de GFS_LEVELS_HPA, que llegan hasta 30 hPa (~24 km). El chorro estratosferico siempre difiere del viento troposferico en mucho mas de MIN_SHEAR_MS=8 m/s, asi que discriminates=True es casi automatico independientemente de si hay cizalla EN EL RANGO donde puede estar la pluma. El propio docstring del modulo (lineas 66-72) documenta que en Lascar 27-jun 'discriminates daba True' mientras la banda cubria 0.2-23.9 km.

*Escenario de fallo:* Modulo aun no cableado al dashboard, asi que hoy no llega al operador. Pero si se cablea, un caso de viento troposferico uniforme (donde el metodo NO discrimina, la limitacion central de Pavolonis 2020) pasa el test discriminates y solo lo frena el guard secundario MAX_BAND_KM. El indicador que el docstring vende como el criterio fisico esta midiendo otra cosa.

*Fix sugerido:* Calcular la cizalla solo sobre los niveles plausibles para el tope (p.ej. entre la elevacion del volcan y la tropopausa), o mejor sobre los niveles dentro de la banda de ambiguedad. Documentar en el docstring que discriminates es necesario pero no suficiente (ya lo dice un comentario, pero el nombre y el retorno sugieren lo contrario).

### `src/fetch/gfs_profile.py:292` — **low**/conf=high

**fetch_gfs_wind_profile (NRT) no devuelve time_gap_min, a diferencia de su gemelo de archivo**

El dict de retorno (lineas 292-293) trae levels/lat/lon/valid_time/source pero NO time_gap_min, mientras que fetch_gfs_wind_profile_archive (gfs_archive.py:340) SI lo devuelve, y el docstring de esta ultima (linea 294) afirma 'Salida identica a fetch_gfs_wind_profile'. Ademas el bloque de seleccion de indice (lineas 277-288) no emite ni el logger.warning de gap que si tiene fetch_gfs_profile (linea 138).

*Escenario de fallo:* Contrato roto entre las dos implementaciones: cualquier consumidor que confie en el docstring y lea wp['time_gap_min'] obtiene KeyError con el proveedor NRT y funciona con el de archivo. Hoy wind_shear_top_height se salva porque recalcula la edad desde valid_time (lineas 275-291), pero el guard de frescura queda duplicado en vez de venir del fetcher.

*Fix sugerido:* Agregar time_gap_min (y el warning de gap) a fetch_gfs_wind_profile para que las dos implementaciones cumplan el mismo contrato, y hacer que wind_shear lea ese campo en vez de reparsear valid_time.

### `src/process/ash_rgb.py:59` — **low**/conf=high

**Los composites RGB solo enmascaran donde C14 es NaN: un NaN de C11/C13/C15 se propaga a la imagen**

generate_ash_rgb linea 59: 'mask = np.isnan(bt14.values)' y luego rgb[mask]=0. Los canales rojo y verde dependen de bt15 y bt11 (lineas 49,52) y el azul de bt13 (linea 55). normalize (linea 29) es np.clip sobre NaN, que devuelve NaN. Mismo patron en generate_ash_so2_rgb linea 99. Si C14 esta bien pero C15 tiene un pixel de fill, el rojo de ese pixel queda NaN y sobrevive al mask.

*Escenario de fallo:* Un hueco de fill en C15 (borde de disco, pixel degradado) genera pixeles NaN en el canal rojo. Al castear a uint8 aguas abajo, NaN pasa a un entero indefinido — tipicamente 0 o 255. Un 255 en el canal rojo del Ash RGB es exactamente el color de la ceniza: un pixel de dato faltante se dibuja como ceniza en el mapa que se proyecta en la sala.

*Fix sugerido:* Construir la mascara como el OR de np.isnan sobre TODAS las bandas que entran al composite, y aplicar np.nan_to_num antes del cast a uint8 aguas abajo.

### `src/process/geocolor_lite.py:43` — **low**/conf=high · eje E

**rad_to_reflectance no normaliza por el coseno del angulo cenital solar: el brillo del GeoColor propio no es comparable entre scans**

Linea 43: 'refl = rad.values * kappa0'. kappa0 del L1b convierte radiancia a factor de reflectancia TOA con geometria solar NOMINAL; la receta estandar (CIRA/RAMMB, satpy sunz_corrected) divide ademas por cos(SZA). El docstring (lineas 36-38) dice que kappa0 'considera flujo solar y geometria sat-sol nominal', lo que sugiere que la correccion ya esta hecha — no lo esta. Se compensa a ciegas con gamma 0.5 y contrast_stretch percentil 2-98 (linea 215), que son por-imagen y por-canal.

*Escenario de fallo:* En Chile a -40 en invierno el SZA a mediodia local ronda 57 grados (cos ~0.54): la imagen sale ~2x mas oscura de lo que corresponde y el stretch por percentil la reescala de forma distinta en cada frame. En un loop rodante de 8 h el brillo del terreno late frame a frame y el borde del terminador se mueve de forma inconsistente; dos frames del mismo loop no se pueden comparar visualmente. Es un producto de visualizacion, no cuantitativo, asi que no afecta ningun numero — pero la nota del docstring induce a creer lo contrario.

*Fix sugerido:* Dividir por cos(SZA) con un clamp (p.ej. cos >= 0.15) antes del gamma, o al menos corregir el docstring para decir explicitamente que la reflectancia NO esta normalizada por angulo solar y que el brillo no es comparable entre scans ni entre scopes.

### `src/process/parallax.py:566` — **low**/conf=high

**El azimut de la correccion de parallax usa una aproximacion de plano tangente sobre 40 grados de latitud**

Lineas 566-567: 'north_m = np.radians(0.0 - lat) * R_EARTH' y 'east_m = np.radians(sat_lon - lon) * R_EARTH * np.cos(lat_r)'. Eso es una diferencia rectangular en el plano, no el azimut de circulo maximo hacia el subsatelite. Calculado para (-40,-72) hacia (0,-75): el azimut esferico correcto es -4.66 grados desde el norte; la aproximacion plana da -3.29 grados, 1.4 grados de diferencia. La MAGNITUD del desplazamiento si esta bien (verificado: 10.49 km para 10 km de altura, tan(theta)=1.0494).

*Escenario de fallo:* Para una pluma a 10 km de altura el error lateral es 10.49 km * sin(1.4 deg) = 0.26 km, bastante por debajo del pixel de 2 km del ABI — no es operacionalmente relevante hoy. Importa si el modulo se cablea a alturas mayores o si en el futuro se usa para co-registrar con un producto de mayor resolucion. Lo registro por completitud, no por urgencia; el docstring declara ser de 1er orden pero atribuye el error residual a 'curvatura y elipsoide', no al azimut.

*Fix sugerido:* Usar el azimut inicial de circulo maximo: atan2(sin(dlon)*cos(lat_sat), cos(lat)*sin(lat_sat) - sin(lat)*cos(lat_sat)*cos(dlon)) con lat_sat=0. Son dos lineas y elimina la aproximacion. Mencionar el azimut en la lista de limitaciones de la ficha SDA.

### `src/process/volcat_colorbar.py:24` — **low**/conf=medium · eje B

**El reverse-mapping del colorbar VOLCAT clava vmin/vmax y la orientacion sin ninguna verificacion: un cambio de paleta invierte las alturas en silencio**

Lineas 24-25 fijan VOLCAT_HEIGHT_VMIN=0 y VMAX=20 km, y build_height_lut (linea 47) tiene low_at_left=True por defecto. No hay ninguna comprobacion de que la barra extraida por extract_rainbow_bar sea efectivamente el arcoiris de altura (podria ser el colorbar de BT, que el propio dashboard separa aparte con _volcat_colorbar_split_vertical), ni de que la orientacion sea la asumida. reverse_map_heights (linea 70) usa argmin de distancia RGB, que sobre una paleta arcoiris no es inyectivo en los extremos.

*Escenario de fallo:* Camino hoy usado SOLO en validacion (grep confirma que dashboard/views/volcat_viewer.py y zonas_fullscreen.py solo usan _volcat_colorbar_strip para mostrar la barra, no este modulo), asi que el operador no lo ve. Pero si SSEC cambia la paleta o el orden, heights_from_plume seguiria devolviendo numeros con la misma forma — un p95 de 3 km cuando el real es 17 km — sin lanzar excepcion. Como el modulo existe justamente para servir de ground truth contra el retrieval propio, una inversion silenciosa validaria conclusiones al reves en el registro del paper.

*Fix sugerido:* Validar la LUT antes de usarla: comprobar que el color del extremo izquierdo y del derecho coinciden (dentro de una tolerancia) con los colores esperados de vmin y vmax, y que el gradiente de hue es monotono. Si no, devolver None. Documentar vmin/vmax como parametros a verificar contra el label del strip, no como constantes.

### `dashboard/views/volcat_viewer.py:216` — **low**/conf=high

**Varias vistas con zoom usan scaleratio=1 en ejes lat/lon, contra el gotcha documentado del propio proyecto**

CLAUDE.md documenta explicitamente 'Plotly scaleratio en lat/lon: con scaleratio=1 los circulos geograficos se ven como ovalos. Usar scaleratio = 1/cos(lat)'. Doce vistas lo cumplen (modo_guardia_volcan.py:491, mosaico_chile.py:190, zonas_fullscreen.py:179 y 482, loop_volcan.py:157, comparador.py:129, backfill_viewer.py:216, replay_reciente.py:114, modo_evento.py:188, volcat_viewer.py:158 y 813). Cuatro no: volcat_viewer.py:216 (_fig del RGB regional), modo_guardia.py:194 (mapa de zona con hot spots), ash_viewer.py:63 (_base_layout) y live_viewer.py:1026.

*Escenario de fallo:* En modo_guardia.py:194 el mapa de zona lleva encima los diamantes de hot spot NOAA con posiciones lat/lon. A -40 grados el factor es 1/cos(40)=1.31: la escena se ve comprimida 31% en vertical. El geologo que estima a ojo la distancia de un hot spot al crater, o la orientacion del eje de dispersion de la pluma (que es la informacion operacional que da esa vista), la lee sesgada. En las 4 zonas australes el efecto crece: a -56 el factor es 1.79.

*Fix sugerido:* Aplicar scaleratio = 1/cos(lat_centro) en las cuatro vistas, igual que en las otras doce. Si en live_viewer.py:1026 el mapa es nacional (-17.5 a -56) y no hay un cos unico defendible, dejarlo pero documentarlo en el codigo como decision consciente.

### `src/process/acha_plume_height.py:96` — **low**/conf=high · eje A

**El camino ACHA no aplica el tratamiento de pixeles 'capped' en la tropopausa que si tienen los otros dos retrievals**

_plume_top_stats (lineas 89-102) calcula el p95 y el max sobre TODOS los pixeles validos, sin excluir los pegados a la tropopausa. bt_matching_height.py:101-121 y wen_rose_height._top_stats (lineas 335-347) si lo hacen, con el razonamiento explicito 'o overshooting real (raro) o cirros mal detectados pegados al tope frio (comun en Chile). NO deben fijar el tope'. El dict de salida de ACHA tampoco trae n_capped ni all_capped, y volcat_viewer._capped_txt (linea 946-950) los lee con .get() devolviendo 0 — asi que la columna ACHA del panel nunca muestra el aviso.

*Escenario de fallo:* Cirros altos mal detectados como ceniza sobre Villarrica en invierno. El p95 de ACHA se fija en el tope del cirro (~11-12 km) mientras BT-matching y Wen-Rose, que si excluyen los capped, reportan 6-7 km. El panel de cross-validacion 3-vias muestra ACHA 11.5 km vs Wen-Rose 6.8 km y el operador no tiene el aviso de 'N px en la tropopausa excluidos' que explicaria la discrepancia — la lee como desacuerdo entre metodos fisicos.

*Fix sugerido:* Mover _top_stats de wen_rose_height a un helper compartido y usarlo tambien en _plume_top_stats, pasandole la tropopausa. Requiere que el camino ACHA baje el perfil GFS (hoy va con with_profile=False, acha_plume_height.py:174), o al menos aplicar un cap absoluto y reportar n_capped.

## Suite de tests  ·  16 hallazgos

**Verificado y limpio** (un núcleo sano también es información):

- tests/test_orchestration_and_guards.py - escena sintetica forward-modelada con verdad conocida, y un test que INTERCAMBIA C14/C15 y exige status no_plume. No es analisis estatico; no encontre mutacion plausible que sobreviva.
- tests/test_comparador_window.py - invariante fuerte (monotonia de |dt| real) sobre la SALIDA de la funcion, no sobre el fuente.
- tests/test_s3_retry.py - cuenta llamadas de un fn falso y distingue FileNotFoundError de fallo transitorio. Correcto.
- tests/test_fdcf_slicing.py - compara sliced vs full-disk elemento a elemento y espia _read_block para exigir que el bloque leido sea <1/4 del grid; restaura el atributo en finally.
- tests/test_exports_volcan.py - compara PNG pixel a pixel con/sin overlay, abre el GeoTIFF con rasterio verificando CRS y bounds, y exige 54 sufijos distintos para 54 pasos del slider. Comportamiento, no texto.
- tests/test_hires_nesting.py Layer 2 - el shape de salida se compara contra bbox_indices de la grilla 1km real; una regresion en el //2 o el *2 rompe la igualdad.
- tests/test_marker_sizes.py - la regla 0.75*size - 2*trazo >= VOLCANO_HOLE_MIN_PX se computa desde las constantes de produccion; los barridos de fuente ya excluyen comentarios (falso verde documentado y cerrado). Verifique con grep repo-wide que no hay triangle-up ni .polygon de 3 vertices fuera de dashboard/views/, ni matplotlib fuera de scripts/.
- tests/test_granule_select.py - los casos de borde de hora son puros y correctos (el hueco esta en otra parte, ver T4).
- tests/test_volcat_guard.py - mockea volcat_at_time a proposito porque lo que prueba es el guard corriente abajo; correcto.
- tests/test_volcan_grid.py::test_modo_sala_conserva_su_fila_de_tres - usa `p is q` (identidad) y no `in`; el falso verde documentado esta cerrado.
- tests/test_altura_en_grilla.py::_texto_en_pantalla - el helper que excluye el docstring y sustituye constantes de modulo funciona: los 3 tests que lo usan resisten mover el aviso al docstring.


### `tests/test_altura_en_grilla.py:137` — **high**/conf=high

**El unico test del disparo automatico de la altura es un substring: auto = False lo deja verde**

test_el_disparo_automatico_es_por_hot_spot hace cuerpo = _func_source(VIEW, '_tira_altura_propia') y luego assert '_hotspots_volcan' in cuerpo. Solo exige que el NOMBRE aparezca en el fuente, no que el resultado gobierne nada. Mutacion corrida sobre dashboard/views/modo_guardia_volcan.py:849 (auto = bool(hotspots) -> auto = False): 1 passed con -k, y 74 passed corriendo test_altura_en_grilla + test_volcan_grid + test_exports_volcan + test_legend_coverage + test_marker_sizes + test_mosaico_layout.

*Escenario de fallo:* Un refactor deja auto en False (o lo cablea a un flag que nunca se prende). Villarrica entra en actividad efusiva, FDCF marca hot spot en el crater, el geologo abre la grilla del volcan: la tira de altura NO se dispara sola y muestra 'Sin hot spot en el encuadre' - la misma frase que en calma. Nadie mide la altura del tope salvo que a alguien se le ocurra apretar el boton. CI verde.

*Fix sugerido:* Testear la CONDICION, no el nombre: extraer auto = bool(hotspots) a un helper puro (_debe_disparar(hotspots) -> bool) y testearlo con lista vacia y con 1 hot spot. Alternativa estatica: exigir por AST que exista un ast.Assign a `auto` cuyo valor contenga el ast.Name que recibio el retorno de _hotspots_volcan, y que `correr` dependa de `auto`.

### `tests/test_altura_en_grilla.py:148` — **high**/conf=high

**El test del caso freatico (assert 'st.button' in cuerpo) sobrevive a que el boton quede dentro del camino con hot spot**

test_el_boton_queda_disponible_sin_hot_spot solo hace assert 'st.button' in cuerpo. En produccion el boton vive en `correr = auto or st.button(...)` (dashboard/views/modo_guardia_volcan.py:857). Mutacion corrida: `or` -> `and`. Con eso, sin hot spot auto es False, Python corta el and y st.button NUNCA se renderiza. Resultado: 1 passed con -k y 74 passed en el bloque completo de 6 archivos.

*Escenario de fallo:* Erupcion freatica en Villarrica o Chillan: columna de ceniza SIN anomalia termica en el crater, o sea sin hot spot FDCF (es el caso que el propio docstring del test dice cubrir). El operador ve la columna en GeoColor y Ash RGB, baja a la tira de altura y NO hay boton, solo la leyenda 'Sin hot spot en el encuadre'. Se queda sin la unica via de medir el tope propio, justo en el caso que la tira existe para atender.

*Fix sugerido:* El estado 'sin hot spot' tiene que ser observable: extraer la decision a un helper puro (_modo_disparo(hotspots) -> 'auto'|'boton') y testear que sin hot spots devuelve 'boton'. O renderizar con un stub de st (patron _StubSt de test_exports_volcan) y afirmar que se registro un button con hotspots=[].

### `tests/test_volcan_grid.py:200` — **high**/conf=high

**El grid puede dejar de dibujar VOLCAT y los 3 asserts de test_la_grilla_recorre_los_paneles_declarados los satisface el DOCSTRING**

El test hace cuerpo = _func_source(VIEW, 'volcan_grid') y pide 'GRID_PANELS' in cuerpo, '_panel_rammb' in cuerpo, '_panel_volcat' in cuerpo. _func_source devuelve el segmento COMPLETO, docstring incluido, y el docstring de volcan_grid (dashboard/views/modo_guardia_volcan.py:1235-1245) ya menciona GRID_PANELS_TV (que contiene 'GRID_PANELS' como substring), _panel_rammb y _panel_volcat. Los tres asserts pasan sin una sola linea de codigo. Mutacion corrida en modo_guardia_volcan.py:1265 (panels = GRID_PANELS if panels is None else panels -> panels = [p for p in GRID_PANELS_TV] if panels is None else panels): 120 passed sobre 7 archivos de test, test_smoke incluido.

*Escenario de fallo:* Con esa mutacion la grilla de un volcan pinta 3 paneles (Ash, GeoColor, SO2) y pierde VOLCAT, el unico producto que da ALTURA de pluma cuantitativa. Al mismo tiempo el rotulo del sub-tab sigue diciendo 'Volcan (4 productos)' porque se deriva de len(GRID_PANELS), y el manual tambien. El turno cuenta 3 paneles, cree que le falta uno por cargar y busca un problema de red que no existe; o peor, da por hecho que VOLCAT no detecto nada. Toda la suite verde.

*Fix sugerido:* Mismo patron que _texto_en_pantalla de test_altura_en_grilla: recortar el docstring antes de afirmar sobre el cuerpo (quitar node.body[0] si es un Expr/Constant). Mejor todavia: renderizar con _StubSt (ya existe en test_exports_volcan) y contar cuantas veces se llamo a _panel_rammb/_panel_volcat con panels=None.

### `tests/test_granule_select.py:148` — **high**/conf=high

**El guard del DirCache eterno dice cubrir 'los 6 fetchers S3' y solo verifica goes_s3**

test_todos_los_fetchers_comparten_el_mismo_filesystem tiene un solo assert: goes_s3._get_fs() is get_s3(). Los otros cinco consumidores (src/fetch/goes_fdcf.py:39, goes_acha.py:46, goes_lvtp.py:54, gfs_archive.py:34, y el camino de src/process/historic_l1b_rgb.py:37) no se tocan. Mutacion corrida en goes_fdcf.py:39: reemplace el import de get_s3 por un _get_s3() local que devuelve s3fs.S3FileSystem(anon=True) pelado: 15 passed (test_granule_select + test_fdcf_slicing).

*Escenario de fallo:* Vuelve el bug ya documentado del audit ago-2026 por la puerta de FDCF: el DirCache de la instancia nueva nace sin listings_expiry_time, asi que el listado de la carpeta .../HH/ queda congelado para todo el proceso. Los granulos que NOAA publica despues en esa misma hora son invisibles: el conteo de hot spots del encabezado de volcan, el Modo Sala y el disparo automatico de la altura se atrasan hasta ~1 h presentandose como vigentes. Un hot spot nuevo simplemente no aparece. Suite verde.

*Fix sugerido:* Parametrizar el test sobre los modulos: for mod in (goes_s3, goes_fdcf, goes_acha, goes_lvtp, gfs_archive): assert mod._get_s3() is get_s3(). Y sumar un guard de fuente repo-wide: ningun archivo de src/ fuera de granule_select.py puede contener 'S3FileSystem(' - hoy solo lo tiene scripts/validate_acha_fase0.py:57, que es un one-shot de validacion.

### `scripts/build_frp_timeline.py:186` — **high**/conf=high

**HUECO: nada testea el productor de frp_timeline.json, y escribe last_updated_utc = now aunque no haya bajado un solo scan**

Ningun test importa scripts.build_frp_timeline (grep sobre tests/*.py: solo aparece src.fetch.frp_timeline). En main(), cada fetch_scan_sliced fallido cae en except Exception: log.warning(...); continue (scripts/build_frp_timeline.py:118-120) y el bloque final arma out = {'last_updated_utc': now.strftime(ISO), ...} sin mirar la variable `fetched`. Ademas daily.setdefault(today_str, {}) (linea 154) registra HOY como dia vacio aunque no se haya leido nada. Del otro lado, dashboard/views/heatmap_actividad.py:229 calcula la frescura EXCLUSIVAMENTE de ese campo via _frp_age_hours, y tests/test_frp_freshness.py prueba el lector pero nunca al escritor.

*Escenario de fallo:* S3/FDCF se rompe (cambio de formato, red, excepcion en extract_hotspots). El cron de 10 min sigue corriendo VERDE, escribe el JSON con last_updated_utc de hace 10 minutos y una ventana que se va vaciando por poda. El geologo de turno abre el Pulso Termico, NO ve el aviso de 'Serie vencida' (edad = 10 min) y lee el cartel verde 'Calma termica: 0 MW en los N volcanes prioritarios'. Hasta 48 h de ceguera termica presentadas como calma: el modo de falla que el contexto del audit declara como el que mas importa en este SDA.

*Fix sugerido:* (a) Que last_updated_utc refleje el ultimo scan efectivamente incorporado, o agregar last_success_utc / n_fetch_errors al JSON y que la vista los use para el guard de frescura. (b) No registrar daily[hoy] = {} cuando no se leyo ningun scan. (c) Test del script con fetch_scan_sliced monkeypatcheado a raise: afirmar que el archivo resultante NO se presenta como fresco; y otro con exito parcial afirmando el roll-up.

### `dashboard/views/modo_guardia_volcan.py:221` — **high**/conf=high

**HUECO: _hotspots_volcan y _hotspots_zone convierten cualquier excepcion en 'cero hot spots', y ningun test lo cubre**

dashboard/views/modo_guardia_volcan.py:217-223: try: ... except Exception as e: logger.warning('hotspots fallo: %s', e); return [], None. Identico en dashboard/views/zonas_fullscreen.py:78-83, ahi sin siquiera loguear. Los consumidores no distinguen los dos casos: _grid_header imprime 'Hot spots {len(hotspots)}' y _tira_altura_propia hace auto = bool(hotspots). Ningun test de tests/ ejercita el camino de excepcion: en tests/ _hotspots_volcan solo aparece monkeypatcheado a lambda: ([], None) en test_exports_volcan, que asume el caso normal.

*Escenario de fallo:* S3 devuelve 403, el granulo FDCF cambia de esquema o pyproj no resuelve el bbox. El encabezado del volcan dice 'Hot spots 0', identico a un volcan en calma, y en el Modo Sala proyectado no aparece ni un diamante. Ademas el disparo automatico de la altura de tope queda muerto en silencio (auto=False). Un negativo silencioso doble, en la unica metrica que CLAUDE.md declara valida y validada externamente (FDCF NOAA).

*Fix sugerido:* Devolver un tercer estado ('sin dato' vs 'cero detecciones'): por ejemplo (None, None) en el except, y que el encabezado pinte 'Hot spots - (FDCF no disponible)'. Tests: monkeypatchear fetch_latest_hotspots a raise y afirmar que el texto emitido NO dice '0' y que la tira de altura no afirma 'Sin hot spot en el encuadre'.

### `src/fetch/rammb_slider.py:214` — **high**/conf=medium

**HUECO: el modulo que georreferencia TODA imagen RAMMB no tiene un solo test, y su docstring dice estar validado por uno que prueba otra cosa**

Ningun archivo de tests/ importa src.fetch.rammb_slider (grep sobre tests/*.py). El modulo contiene get_tiles_for_bounds (rammb_slider.py:88, proyeccion geos -> indices de tile) y reproject_to_latlon (linea 214, remapeo geos -> grilla lat/lon regular), que producen el encuadre de cada panel de Modo Guardia, Modo Sala, Vista Operacional y los mosaicos. El docstring del parametro sat_lon (rammb_slider.py:240-247) afirma que el valor -75.0 fue 'Validado contra L1b oficial NOAA y tests/test_geo.py'; tests/test_geo.py importa src.process.geo (bbox_indices, crop_to_bounds, get_lat_lon) y no menciona rammb_slider. La validacion afirmada no la respalda ningun test.

*Escenario de fallo:* Una regresion de signo o eje en pix_row = center - (y_m/h_m)*cfac, o un sat_lon que vuelva a -75.2, desplaza todas las imagenes RAMMB. El bug historico documentado eran ~17 km de offset al sur de Chile: el triangulo del crater cae al lado del pixel caliente y el operador atribuye una anomalia termica al volcan equivocado, o la descarta por 'esta corrida'. La suite sigue verde porque nadie prueba esta reproyeccion.

*Fix sugerido:* Test de round-trip sin red (mismo patron que tests/test_geo.py): construir un canvas de tiles sintetico con un pixel marcado en la posicion geos de un volcan conocido, correr reproject_to_latlon sobre su bbox y afirmar que el pixel marcado sale a menos de una celda de la coordenada del volcan. Y un test de get_tiles_for_bounds para el bbox de Chile a zoom 2/3/4 contra las constantes CHILE_TILES_Z2 / CHILE_TILES_Z3 que ya estan escritas en el modulo.

### `tests/test_workflow_concurrency.py:60` — **medium**/conf=high

**El invariante de concurrency de los releases rolling nunca mira cancel-in-progress**

_release_writers y los cuatro tests solo leen wf['concurrency']['group']. La cadena 'cancel-in-progress' no aparece en el archivo de test. Mutacion corrida en .github/workflows/hires_visible_cache.yml:37 (cancel-in-progress: false -> true): 7 passed.

*Escenario de fallo:* Con cancel-in-progress: true compartido en el grupo hires-cache, lanzar el backfill manual (hires_loop_backfill.yml) CANCELA el cron que esta a mitad de gh release upload del snapshot. La accion sube con --clobber y poda huerfanos DESPUES; cancelada entre las dos fases, el release hires-loop-rolling queda a medio poblar y con assets huerfanos. El dashboard sirve una ventana rodante incompleta (loops con huecos) sin nada que lo declare. Es exactamente el modo de falla que el archivo dice impedir, y la serializacion que el grupo promete no ocurre.

*Fix sugerido:* Extender _release_writers a (workflow, group, cancel_in_progress) y afirmar que todo publicador de un release snapshot lleva cancel-in-progress: false explicito. El default de GitHub tambien es false, pero un default implicito no documenta la decision y se pierde en el proximo copy-paste.

### `tests/test_volcan_grid.py:202` — **medium**/conf=high

**test_el_panel_volcat_usa_la_etiqueta_de_sector lo satisface la mencion en el docstring**

El assert es 'etiqueta_sector_volcat' in cuerpo sobre _func_source(VIEW, '_panel_volcat'), y el docstring de _panel_volcat (dashboard/views/modo_guardia_volcan.py:747) ya dice literalmente '(via etiqueta_sector_volcat)'. Mutacion corrida en la linea 766: f"Sector <b>{etiqueta_sector_volcat(sector)}</b>" -> f"Sector <b>regional 2 km</b>": 1 passed con -k y 74 passed en el bloque de 6 archivos.

*Escenario de fallo:* El rotulo del panel VOLCAT queda clavado en 'regional 2 km'. Copahue tiene sector dedicado de 250 m y Calbuco de 1 km; el operador que mira Copahue lee '2 km' y le baja confianza a una altura que en realidad es la mas fina que hay. Y al reves, un volcan que cae en Argentina_5_km se rotula '2 km' y una altura gruesa se lee con confianza de 2 km. Es la misma clase de mentira que el test hermano test_la_etiqueta_de_sector_distingue_dedicado_de_regional cerro del lado de la funcion pura.

*Fix sugerido:* Recortar el docstring antes de afirmar (ver fix de T3), o mejor, renderizar _panel_volcat con un _StubSt y verificar que el markdown emitido contiene etiqueta_sector_volcat(sector) calculado, para dos volcanes de sector distinto (Copahue vs uno regional).

### `tests/test_legend_coverage.py:55` — **medium**/conf=medium

**El guard de leyendas solo ve funciones TOP-LEVEL: una funcion de render anidada es invisible**

_render_functions itera [n for n in tree.body if isinstance(n, ast.FunctionDef)] - solo el nivel superior del modulo. Un barrido AST propio sobre dashboard/views/*.py encuentra hoy una funcion anidada que llama a plotly_chart/image: volcat_viewer._render_map_block (dashboard/views/volcat_viewer.py:1242), definida dentro de _render_height_section. Hoy no hay agujero real porque el padre esta en la lista DELEGATED, pero el guard nunca la miro.

*Escenario de fallo:* Alguien agrega una vista nueva y define el render dentro de render() (patron ya presente en volcat_viewer). Esa vista pinta Ash RGB sin leyenda y test_every_product_view_has_a_legend pasa. El turno mira un composite donde el rojo puede ser ceniza, cirro o nieve, sin la tira que dice cual es cual: exactamente el agujero que el archivo dice tapar, en la vista nueva que nadie reviso.

*Fix sugerido:* Cambiar tree.body por ast.walk(tree) para juntar todas las FunctionDef, nombrando las anidadas como padre.hija para que DELEGATED las pueda direccionar. Sumar un guard-del-guard: la cantidad de funciones de render detectadas no puede bajar de la actual sin decision explicita.

### `dashboard/views/modo_guardia_volcan.py:470` — **medium**/conf=high

**HUECO: la rama RAMMB de fetch_volcan_product - la que produce el 'hace N min' y los avisos de scan previo - no tiene test**

El unico test de fetch_volcan_product es tests/test_volcan_grid.py::test_el_hires_solo_se_usa_si_cubre_el_bbox_pedido, que mockea _frame_with_fallback y solo mira el guard del hi-res. La rama RAMMB (bloque '# 2) RAMMB' de dashboard/views/modo_guardia_volcan.py) calcula age = int((now - ts_dt).total_seconds()/60) y agrega los flags 'scan previo' y 'zoom reducido' comparando used_ts != timestamps[0] y used_zoom < ZOOM_VOLCAN; su except Exception: ts_label = used_ts deja al operador con un timestamp crudo de 14 digitos y SIN edad. Nada de eso se ejercita. Tampoco se testea src/fetch/rammb_slider.py:463 fetch_frame_robust, que puede devolver un ts arbitrariamente viejo de la lista sin tope de |dt|.

*Escenario de fallo:* RAMMB deja de publicar. _recent_timestamps devuelve los 3 ultimos ts disponibles (viejos), fetch_frame_robust sirve el primero que cargue y el panel muestra la imagen con 'hace 240 min': correcto pero facil de pasar por alto en una pared de 4 paneles, sin cambio de color ni aviso. Y si parse_rammb_ts falla, el label queda como '20260830201000' pelado: el operador no tiene ninguna edad que leer y la imagen vieja pasa por actual.

*Fix sugerido:* Test puro del armado de etiqueta: extraer _ts_label(used_ts, timestamps, used_zoom, now) y afirmar (a) que con ts de hace 4 h el label lleva la edad, (b) que used_ts != timestamps[0] produce el aviso 'scan previo', (c) que un ts no parseable NO devuelve algo que parezca fresco. Sumar un umbral de edad que degrade el panel visualmente.

### `dashboard/views/modo_guardia_volcan.py:975` — **medium**/conf=high

**HUECO: el encabezado de la grilla imprime 'Render HH:MM:SS UTC' (reloj de pared) en el lugar donde se lee frescura del dato, sin test**

En _grid_header el unico timestamp del encabezado sale de now = datetime.now(timezone.utc) y se rotula 'Hot spots {len(hotspots)} - Render {now:%H:%M:%S} UTC / {fmt_chile(now)}'. La hora del scan FDCF que _hotspots_volcan si devuelve se descarta en el sitio (hotspots, _ = _hotspots_volcan(...)). No hay ningun test sobre la SALIDA de _grid_header: en tests/ aparece solo en test_volcan_grid.py::test_el_radio_es_ajustable_y_llega_a_todos_los_paneles, que verifica la FIRMA.

*Escenario de fallo:* El encabezado es lo primero y mas grande que se lee de la vista de volcan. 'Render 20:13:02 UTC' junto a 'Hot spots 0' se lee como 'a las 20:13 no habia hot spots'. Si RAMMB, FDCF o VOLCAT estan congelados, el encabezado igual se refresca cada 60 s con la hora actual: la vista se ve viva mientras ningun dato lo esta. Combinado con T12 (excepcion -> 0 hot spots) da la lectura completa de 'todo tranquilo a las 20:13' sobre datos que no llegaron.

*Fix sugerido:* Mostrar junto a 'Hot spots N' la hora del SCAN FDCF (el dt que _hotspots_volcan ya devuelve y hoy se tira) y su edad, dejando 'Render' claramente separado como reloj. Test con _StubSt afirmando que el encabezado contiene la hora del scan y no solo la de render.

### `dashboard/views/zonas_fullscreen.py:687` — **medium**/conf=medium

**HUECO: el panel VOLCAT dibuja el frame sin edad, y el aviso 'sin dibujo = no detecta ceniza' no distingue frame viejo de frame vacio**

_render_volcat_zoom_tv (dashboard/views/zonas_fullscreen.py:648-693) obtiene dt = _volcat_dt_obj(meta.get('datetime')) y lo pasa a la figura como fmt_both(dt): hora absoluta, sin 'hace N min' ni umbral. El placeholder _ph('sin frame disponible') solo cubre el caso en que _volcat_latest_cached levanta o devuelve None; un frame cacheado y viejo pasa derecho. Del lado del grid, _panel_volcat (dashboard/views/modo_guardia_volcan.py:764-769) rotula 'sin dibujo = VOLCAT no detecta ceniza, no es una falla'. Ningun test cubre la edad del frame VOLCAT: tests/test_smoke.py::test_volcat_frame_dt_parser solo prueba el parser de la cadena.

*Escenario de fallo:* SSEC deja de publicar el sector, o el cache de 10 min queda pegado. El panel muestra un frame de hace horas (o el ultimo frame vacio) con su hora absoluta al pie, y el rotulo de al lado le dice al operador que la ausencia de dibujo es normal. La altura de pluma que CLAUDE.md privilegia como metrica validada externamente pasa de 'no hay dato' a 'no hay ceniza' sin que nada lo declare.

*Fix sugerido:* Calcular la edad del frame y degradar el rotulo por encima de un umbral (por ejemplo >30 min: 'frame VOLCAT de hace N min - la ausencia de dibujo NO se puede leer como ausencia de ceniza'). Testear con meta['datetime'] de hace 3 h que el texto emitido cambia.

### `tests/test_hires_nesting.py:41` — **low**/conf=high

**test_nesting_arithmetic_contract es una tautologia: no toca una sola linea de produccion**

El test solo opera sobre r0, r1 literales locales: a1, b1 = r0//2, r1//2 y despues assert 2*a1 == r0. Para r0 multiplo de 4 esas identidades son ciertas por aritmetica, siempre. No importa ningun simbolo de src/process/hires_pipeline.py. No hace falta correr una mutacion: no existe cambio de produccion que lo ponga rojo. El docstring del archivo afirma que este layer bloquea 'cambiar //4 por //2, soltar el *2', y no bloquea nada.

*Escenario de fallo:* Riesgo real bajo porque el Layer 2 (test_color_output_is_exactly_2x_the_1km_crop) si compara contra bbox_indices de la grilla 1km. El costo es de confianza: el archivo declara dos capas de proteccion sobre el co-registro del pan-sharpening y solo tiene una. Si el Layer 2 se skipea (el fixture hace pytest.importorskip('pyproj')), queda una capa que siempre pasa y la suite reporta verde sobre el contrato de anidamiento sin haberlo probado.

*Fix sugerido:* Reescribirlo contra las funciones reales de hires_pipeline que hacen el mapeo de indices, o borrarlo y dejar el contrato como docstring del Layer 2. Y cambiar el importorskip por un fallo duro en CI: pyproj esta en requirements, y un skip silencioso deja el modulo entero sin cobertura real.

### `tests/test_exports_volcan.py:300` — **low**/conf=medium

**split('if enable_capture:')[1] no acota al bloque: cualquier cosa DESPUES del if lo satisface**

test_la_grilla_engancha_el_expander_donde_el_boton_de_captura hace bloque = cuerpo.split('if enable_capture:')[1] y luego pide que '_capture_button(' y '_download_expander(' esten ahi. Ese slice llega hasta el final de la funcion, no hasta el final del bloque indentado: _download_expander sacado del if (a nivel de volcan_grid) sigue cayendo dentro del slice.

*Escenario de fallo:* El expander de descargas por producto se desengancha de enable_capture y aparece tambien en el slot tv=volcan del Modo Sala. En la pared proyectada 24/7 se suma un expander con 6 botones de descarga que nadie va a apretar, comiendo alto de imagen: el mismo tipo de regresion (leyenda duplicada, alto perdido) que otros tests del repo si vigilan.

*Fix sugerido:* Usar AST como ya hace test_la_grilla_dibuja_la_tira_cuando_se_la_piden en test_altura_en_grilla.py: buscar el ast.If cuyo test menciona enable_capture y exigir que ambas llamadas esten en su .body.

### `tests/test_workflow_concurrency.py:28` — **low**/conf=high

**_load_workflows globea solo *.yml: un workflow .yaml sale del barrido entero**

WORKFLOWS.glob('*.yml'). GitHub Actions acepta tambien .yaml. Hoy los 9 workflows son .yml (verificado con ls .github/workflows/), asi que no hay agujero abierto, pero el guard depende de una convencion que nada mas sostiene.

*Escenario de fallo:* Alguien agrega hires_loop_backfill_v2.yaml que publica al mismo tag rolling sin grupo de concurrency. Los cuatro tests pasan porque el archivo ni se lee, y vuelve el borrado de la ventana rodante de 8 h que este archivo existe para impedir.

*Fix sugerido:* sorted(list(WORKFLOWS.glob('*.yml')) + list(WORKFLOWS.glob('*.yaml'))), y afirmar que la cantidad de workflows leidos coincide con la cantidad de archivos del directorio.

## Crítica operacional (usuario)  ·  26 hallazgos

**Verificado y limpio** (un núcleo sano también es información):

- live_viewer.py:424-540 — el health banner de Vista Operacional es ejemplar: 3 umbrales de edad de scan (15/30 min), atribuye la culpa a RAMMB y no a la app, y ademas distingue 'RAMMB no publico' de 'mi sesion esta dormida' con el campo _polled_at ('consultado hace Ns' + '⚠ sesion dormida'). Es el patron que el resto del dashboard deberia copiar.
- heatmap_actividad.py:229-236 — el guard de frescura del pulso intradia (FRP_STALE_HOURS=3) esta bien hecho: avisa ANTES del grafico, y en la rama sin senal (l.265-267) evita repetir el mensaje verde que afirmaria calma. La logica de las tres ramas (activo / calmo-fresco / calmo-vencido) es correcta.
- comparador.py:489-495 — el modo baseline DECLARA su supuesto en pantalla ('Asumimos que ese dia NO habia actividad anomala — si la habia, esta vista no sirve'). Es la mejor frase de honestidad del dashboard.
- modo_guardia_volcan.py:925-931 — el aviso de 'todos los topes quedan bajo la cima => el retrieval NO encontro ceniza IR-opaca, no significa que la pluma sea baja' esta correctamente redactado y validado contra Chillan 27-jun-2026.
- modo_guardia_volcan.py:794, 855-863 — el costo (~78 MB y ~90 s) se declara ANTES de gastarlo, en el help del boton y en el spinner. Ningun otro proyecto del workspace hace esto.
- modo_guardia_volcan.py:762-769 — el panel VOLCAT declara que sector usa (etiqueta_sector_volcat, derivada del nombre) y que 'sin dibujo = VOLCAT no detecta ceniza, no es una falla'.
- modo_guardia_volcan.py:376-396 — las etiquetas de panel de la grilla marcan 'scan previo', 'zoom reducido' y la resolucion efectiva; el operador ve cuando el panel esta degradado.
- exports.py:1-19 y modo_guardia_volcan.py:983-995 — trazabilidad del encuadre: el radio y el timestamp van sobre-impresos en el PNG y en el nombre del archivo, y el GeoTIFF va limpio. Correcto para un SDA cuyas imagenes terminan en informes.
- map_helpers.py:299 render_scan_status_badge + modo_guardia.py:220-230 + zonas_fullscreen.py:1639-1650 — Modo Guardia y Modo Sala si tienen banda de edad de scan con codigo de color.
- live_viewer.py:726-733 — el help del toggle de hot spots advierte explicitamente que 'erupciones con cenizas frias pueden NO disparar hot spots'. La limitacion fisica esta donde el operador la ve.
- volcat_viewer.py:874-881 — la pagina VOLCAT SI distingue no_data (con reason) de no_plume y muestra el porque al operador. Es el contra-ejemplo que hace visible el hueco U1.


### `dashboard/views/modo_guardia_volcan.py:903` — **high**/conf=high · eje F

**La tira de altura de la grilla presenta CUALQUIER fallo de adquisicion como 'estado esperado sin pluma activa'**

_render_altura (l.888-931) calcula wr_ok/acha_ok = (status == 'ok') y en el else unico hace st.info('Sin firma de ceniza IR-opaca en el encuadre (±R°) -> no hay tope que reportar. **Es el estado esperado sin pluma activa.**') (l.903-908). Pero acquire_ash_scene (src/process/scene.py:144-146, _err) devuelve status='no_data' + 'reason' para banda ausente, bbox fuera del disco, bandas de scans distintos y falta de perfil GFS; y ademas wr/acha pueden ser None por excepcion. El campo 'reason' NUNCA se lee en este archivo (grep 'reason' en modo_guardia_volcan.py = 0 matches). La vista hermana volcat_viewer.py:877-881 SI lo lee: 'No pude calcular la altura propia: {reason}. Puede ser scan ABI atrasado o S3/Open-Meteo intermitente — reintenta.' La FICHA_SDA (docs/FICHA_SDA_GOES.md, seccion 'Donde viven los guards') dice que scene.py existe precisamente para que los guards de 'no reportar' lleguen al operador; en el camino mas usado no llegan.

*Escenario de fallo:* 03:00 AM, hot spot FDCF en Villarrica dispara la tira automaticamente. S3 esta intermitente y falta C15 (o Open-Meteo no devuelve el perfil GFS). acquire_ash_scene devuelve no_data con reason='banda C15 ausente'. El geologo lee literalmente 'Es el estado esperado sin pluma activa' en la vista de un volcan que acaba de encender un hot spot, no reintenta, y concluye que no hay ceniza. El mismo minuto, en la pagina VOLCAT, el mismo calculo le habria dicho 'S3/Open-Meteo intermitente, reintenta'. Impacto alto x frecuencia media (S3/Open-Meteo fallan de a ratos) x accionabilidad alta x costo de cierre trivial (leer reason, ya existe) = el hallazgo mas rentable de esta dimension.

*Fix sugerido:* En _render_altura, separar las tres ramas como hace volcat_viewer: (a) ambos status=='no_data' -> st.warning con el reason y 'reintenta'; (b) ambos 'no_plume' -> el st.info actual; (c) wr/acha None -> warning de excepcion. Test: pasar wr={'status':'no_data','reason':'banda C15 ausente'} y assert que el texto NO contiene 'estado esperado'.

### `dashboard/views/modo_evento.py:427` — **high**/conf=high · eje D

**Modo Evento solo existe para 8 de 43 volcanes, y un permalink a otro volcan cae SILENCIOSAMENTE a Villarrica**

render(): `initial = qp.get('volcan', 'Villarrica')`; `if initial not in PRIORITY_VOLCANOES: initial = 'Villarrica'` (l.426-428) y el selectbox usa `options=PRIORITY_VOLCANOES` (l.434). PRIORITY_VOLCANOES (src/volcanos.py:90-93) son 8: Villarrica, Lascar, Copahue, Puyehue-Cordon Caulle, Calbuco, Nevados de Chillan, Llaima, Hudson. CATALOG tiene 43 volcanes chilenos (verificado: len(CATALOG)=48, 5 con zone=='test'). No hay ningun mensaje ante el fallback; la URL tampoco se corrige (l.446-447 solo escribe si difiere, o sea que reescribe 'volcan' a Villarrica sin avisar).

*Escenario de fallo:* Planchon-Peteroa (ranking SERNAGEOMIN 12) entra en erupcion. El turno saliente manda por WhatsApp el permalink '?vista=evento&volcan=Planchon-Peteroa'. El turno entrante lo abre y ve la pantalla '🚨 MODO EVENTO' con encabezado gigante VILLARRICA, sus hot spots, su viento y sus anillos, y ningun cartel que diga que el volcan pedido no existe en esta vista. En el mejor caso pierde minutos; en el peor reporta ausencia de anomalia del volcan equivocado. Impacto alto x frecuencia baja-media (35 de 43 volcanes) x accionabilidad alta x costo bajo = alto.

*Fix sugerido:* Abrir el selector a `[v.name for v in CATALOG if v.zone != 'test']` (Modo Evento no depende de nada exclusivo de los prioritarios: hot spots, viento y RAMMB funcionan para los 43). Como minimo, si el volcan pedido no esta en la lista, mostrar st.error('X no esta disponible en Modo Evento; mostrando Villarrica') en vez de sustituirlo en silencio. Mismo patron en comparador.py:204/293/400/503 y loop_volcan.py:190.

### `dashboard/views/modo_evento.py:266` — **high**/conf=high · eje F

**En la pantalla de crisis, cero hot spots se pinta VERDE — y la excepcion de red produce el mismo cero verde**

KPI 1: `n_hs = len(hotspots_with_d); kc = '#ff4444' if n_hs > 0 else '#3fb950'` (l.265-266) — el borde queda verde cuando no hay detecciones. KPI 2: `kc = '#888'; label='—'; sub='sin hot spot'` (l.283). La fuente es _hotspots_volcan (l.62-79), que envuelve fetch_latest_hotspots en `try/except: return [], None` — o sea que un timeout de s3fs, un FDCF no publicado o un error de xarray producen exactamente el mismo cero verde que 'el volcan no tiene anomalia termica'. fetch_latest_hotspots ya devuelve ([], None) en todos sus error paths (src/fetch/goes_fdcf.py:329, 335, 350), asi que ni siquiera hay excepcion que atrapar la mayoria de las veces. Ademas, hs_dt solo se muestra si HAY hot spots (l.386-390): cuando el conteo es 0 no se ve ni la hora del scan FDCF.

*Escenario de fallo:* Erupcion explosiva de Calbuco con ceniza fria (no dispara FDCF, cosa que el propio dashboard documenta en live_viewer.py:731). El operador abre Modo Evento, ve un KPI verde con un 0 grande y 'FRP maximo —', y el resto de la pantalla son tres imagenes que a las 3 AM son casi negras. La unica senal de color de la pantalla de crisis es verde. Peor variante: FDCF esta caido; el operador ve el mismo verde y no puede distinguirlo. Impacto alto x frecuencia alta (FDCF esta en 0 casi siempre en Chile, lo dice el propio manual) x accionabilidad alta x costo bajo = alto.

*Fix sugerido:* (1) Nunca verde en Modo Evento: 0 hot spots = gris neutro con la leyenda 'FDCF no detecta ceniza fria — la ausencia no descarta erupcion'. (2) Mostrar SIEMPRE la hora del scan FDCF y su edad, tambien con 0 detecciones. (3) Propagar un estado de error distinguible desde _hotspots_volcan (devolver un sentinel, no [] ) y pintarlo ambar con 'FDCF no accesible'.

### `dashboard/views/heatmap_actividad.py:321` — **high**/conf=high · eje F

**El panorama semanal afirma 'Calma operacional' sin ningun guard de frescura — el guard existe 90 lineas mas arriba y no se reusa**

render() carga `daily = _load_frp_timeline().get('daily', {})` (l.290) y si counts_today esta vacio imprime st.info('✅ **Hoy (dd-mmm)**: sin deteccion FDCF en los 8 volcanes prioritarios (aun). Calma operacional.') (l.320-324). `_frp_age_hours` (definida en l.133) se invoca UNA sola vez en todo el archivo, en la l.229, dentro de _render_frp_timeline_section. La seccion semanal usa el MISMO dict y no consulta la edad. El caption de l.326-330 solo dice cuantos dias estan cubiertos, no hace cuantos que el JSON no se actualiza. Es exactamente el modo de fallo que el audit ago-2026 corrigio para la seccion intradia (AUDIT_REPORT_2026-08.md:22) y que quedo abierto en la de abajo.

*Escenario de fallo:* El workflow frp_timeline.yml se rompe un viernes (o el secret desaparece y resuelve a string vacio: el patron zombie que el propio CLAUDE.md documenta). El lunes el operador entra al Heatmap: arriba ve el warning ambar 'Serie vencida' — bien. Baja 200 px y lee, en verde institucional, '✅ Hoy: sin deteccion FDCF en los 8 volcanes prioritarios. Calma operacional.' Dos afirmaciones contradictorias en la misma pagina; la de abajo es la que tiene forma de conclusion. Impacto alto x frecuencia media x accionabilidad alta x costo trivial = alto.

*Fix sugerido:* Calcular `stale` una vez en render() y pasarlo a ambas secciones; con stale=True reemplazar el mensaje verde por el mismo st.info neutro que ya usa la seccion intradia ('dato vencido, ver aviso arriba') y teñir el heatmap (opacity o marca de agua). Test de regresion: JSON con last_updated_utc de hace 10 h -> el texto renderizado no debe contener 'Calma operacional'.

### `dashboard/app.py:296` — **high**/conf=high · eje K

**La app desplegada no declara en ningun lado que es un SDA bajo CPLT N°372, ni linkea la ficha, ni la guia del operador, ni sus limites**

grep -rn 'no reemplaza|decision humana|SDA|CPLT|transparencia|responsabilidad' sobre dashboard/*.py y dashboard/views/*.py devuelve SOLO comentarios de codigo (modo_guardia_volcan.py:777, 789, 987; rammb_viewer.py:914) y una frase suelta en un docstring (volcat_viewer.py:834). Nada renderizado. grep 'GUIA_REVISION|FICHA_SDA|docs/' sobre los mismos archivos: 0 links en la UI. El footer del sidebar (app.py:296-306) trae 'GitHub · SERNAGEOMIN · v1.0 · GOES-19 ABI L1b' y nada mas. docs/FICHA_SDA_GOES.md declara como canal de consulta 'issues del repositorio publico', pero el operador que entra al Space no tiene forma de llegar ni a la ficha ni a docs/GUIA_REVISION_DASHBOARD.md, que es el documento escrito PARA el.

*Escenario de fallo:* Fiscalizacion CPLT, o simplemente un operador nuevo que entra por permalink en su primer turno. La pagina no dice que es un sistema de apoyo, que la decision de alerta es humana, que la altura propia es indicativa, ni donde esta la documentacion del metodo. El unico lugar donde eso esta escrito es un .md del repo. Para un SDA en produccion, la trazabilidad de lo que el sistema afirma es requisito legal, no cosmetica (CONTEXTO). Impacto alto (legal + induccion) x frecuencia alta (todas las sesiones) x accionabilidad alta x costo bajo (un bloque de sidebar con 3 links) = alto.

*Fix sugerido:* Bloque fijo en el sidebar, siempre visible: 'Sistema de apoyo a la decision (SDA-GOES-01, Res. CPLT N°372). No emite alertas ni advisories: la decision de alerta volcanica es humana.' + link a la ficha publicada y a la guia de revision. Renderizar la ficha como una vista mas del menu (leyendo el .md) para que viaje con el deploy.

### `dashboard/views/timeseries_viewer.py:255` — **high**/conf=high · eje E

**La vista Series promete 'Hot spots NOAA FDCF + FRP' en su subtitulo y en su manual, y no tiene ni un solo dato FDCF/FRP**

header('Series de tiempo por volcan', 'Hot spots NOAA FDCF + FRP, con % ash-rojo de apoyo · GOES-19') en l.253-256. grep 'FDCF|FRP' en timeseries_viewer.py devuelve exactamente 2 lineas: esa y el consejo de l.272 ('cruzar con hot spots NOAA FDCF'). PRODUCTS (l.49-52) tiene solo 'eumetsat_ash' y 'jma_so2', ambos calculados con _ash_red_fraction_v2 (src/fetch/timeseries.py:63). El manual de la vista es peor: manuals.py:387-402 describe tres series — 'N° hot spots / dia', 'FRP total (MW)' y '% ash-rojo' — y remata con 'Validar con FRP en paralelo'. Ninguna de las dos primeras existe. Los KPI de la vista muestran '%' en los cinco recuadros.

*Escenario de fallo:* El operador quiere la magnitud cuantitativa validada. Lee el subtitulo, entra a Series, elige Villarrica y 24 h, y obtiene una curva de % de pixeles rojos. Como el manual le dijo que ahi hay FRP en MW, interpreta los numeros del eje Y como si fueran la metrica validada, o busca durante minutos el selector de FRP que no existe (esta en otra vista, Heatmap). El proyecto tiene medido y documentado que esa metrica de color da 9.9-95.5% en volcanes SIN actividad (CLAUDE.md, 'El gatillo por color NO sirve, y esta medido') — o sea que el subtitulo vende como validado justo lo que el propio proyecto descalifico. Impacto alto x frecuencia alta x accionabilidad alta x costo trivial = alto.

*Fix sugerido:* Corregir el subtitulo a '% de pixeles con firma de color (proxy, NO cuantitativo)' y reescribir el manual 'series' para que describa la vista real, apuntando a Heatmap actividad para FRP. Si se quiere cumplir la promesa, agregar la serie FRP leyendo data/frp_timeline.json (ya esta cargado y remoto en heatmap_actividad).

### `dashboard/manuals.py:43` — **high**/conf=medium · eje E

**El manual y la leyenda de la misma vista dicen COLORES OPUESTOS para SO2 y ceniza en el producto jma_so2**

manuals.py:42-44 (manual 'operacional', el expander que abre la Vista Operacional): '**SO2 RGB** (JMA): plumas de SO2 en magenta brillante sobre fondo verdoso.' La leyenda compacta canonica dice lo contrario: map_helpers._LEGEND_ITEMS['jma_so2'] = [('#44dd66','SO2'), ('#bbff44','Cirros'), ('#dd4488','Ash + SO2'), ...] (l.258-264) — verde = SO2, magenta = ceniza+SO2. Y la leyenda desplegable de la misma pagina (live_viewer.py:869-901) es explicita: 'Verde intenso -> Nube de SO2 densa' y 'Rojo/rosado -> **Ceniza** (misma firma termica que Ash RGB)'. El color del producto en LIVE_PRODUCTS es '#44dd88' (verde). Marco como confidence medium porque no adjudique la fisica contra el Quick Guide de RAMMB; lo que es seguro es que la app se contradice a si misma en la misma pantalla.

*Escenario de fallo:* Operador nuevo (o cansado) abre el expander '📖 Como interpretar' — que es lo que el proyecto le pide hacer en 30 s — y aprende 'magenta = SO2'. Cierra el expander, mira el panel SO2 y ve una mancha magenta creciendo sobre el crater. Reporta 'pluma de SO2', cuando segun la leyenda del propio dashboard esa mancha es CENIZA. Es la inversion de diagnostico mas cara posible: gas pasivo vs columna eruptiva. Impacto alto x frecuencia media x accionabilidad alta x costo trivial = alto.

*Fix sugerido:* Adjudicar contra docs/Quick_Guide_SO2_RGB.pdf (ya esta en el repo) y hacer que el manual DERIVE los colores de _LEGEND_ITEMS en vez de repetirlos en prosa (mismo principio que ya se aplico a la leyenda de 3 columnas de modo_guardia, derivada de GRID_PANELS_TV). Revisar de paso el mismo choque en Ash RGB: _LEGEND_ITEMS['eumetsat_ash'] pone '#bbff44 = Cirros / nubes altas' mientras live_viewer.py:812-826 dice 'Verde = SO2' y 'Cyan = nubes de hielo (cirrus)'.

### `dashboard/manuals.py:333` — **high**/conf=medium · eje K

**El manual invita a usar la altura para alerta aeronautica — una frontera que el sistema deberia negarse explicitamente a cruzar**

manual 'volcat', l.331-333: '**Altura (km)**: usa diferencia entre BT observada y perfil atmosferico vertical (GFS) para resolver altura. Util para **alerta aeronautica (FL flight levels)**.' No hay en ninguna parte de la UI una frase que diga que el dashboard NO emite advisories y que el unico organismo habilitado para Chile es el VAAC Buenos Aires. El unico texto que menciona a los VAAC (volcat_viewer.py:1402-1405) los describe en pasado y sin link, dentro del mismo panel que afirma 'La ausencia de VAA indica condiciones normales'.

*Escenario de fallo:* Un operador con presion de tiempo lee una altura VOLCAT de 9,2 km, la traduce a FL300 siguiendo la instruccion del manual y la pasa por telefono a la torre / a la aerolinea que llamo. El numero no viene de un producto certificado para aviacion, no tiene correccion de paralaje cableada (backlog abierto), y la propia guia advierte del sesgo IR de -0.4 a -0.8 km. Impacto muy alto (seguridad aerea + responsabilidad institucional) x frecuencia baja x accionabilidad alta x costo trivial = alto.

*Fix sugerido:* Borrar 'Util para alerta aeronautica (FL flight levels)' y sustituir por: 'Referencia tecnica interna. Este sistema NO emite Volcanic Ash Advisories; para aviacion el producto oficial es el VAA del VAAC Buenos Aires (link).' Agregar una seccion 'Lo que este dashboard NO hace' al manual/sidebar (no emite alertas, no reemplaza REAV/RAV, no ve bajo nube, no mide gas con los retrievals de altura, no cubre los 43 volcanes en los productos cuantitativos).

### `dashboard/views/volcat_viewer.py:1237` — **high**/conf=high · eje F

**VOLCAT — el 'numero cuantitativo de referencia' — se muestra sin edad, sin fecha en el KPI y sin ningun umbral de frescura**

El KPI 'Hora del scan' hace `short_ts = meta.get('datetime','—').split('_')[-1].replace('-',':')` y muestra `short_ts[:5] + ' UTC'` (l.1238-1240): HH:MM pelado, sin fecha y sin edad. No hay comparacion contra now() en ningun punto del bloque. Aguas arriba, volcat_api.volcat_latest (l.234-246) toma `frames[-1]` sin ningun tope de antiguedad y devuelve None solo si la lista viene vacia. El panel VOLCAT de la grilla (zonas_fullscreen._render_volcat_zoom_tv, l.688-699) pone `fmt_both(dt)` en el titulo — fecha y hora, pero tampoco edad ni color. Contraste: TODO camino RAMMB tiene banda de edad con 3 umbrales (live_viewer.py:459-490, modo_guardia.py:220-230, map_helpers.render_scan_status_badge). El producto declarado primario es el unico sin guard de frescura.

*Escenario de fallo:* SSEC deja de publicar el sector Chile_Central a las 18:00. A las 04:00 del dia siguiente el operador abre la pagina VOLCAT: el KPI dice '18:20 UTC', que a simple vista parece una hora del dia en curso, y el mapa muestra el campo de ayer sin pluma. El operador concluye 'VOLCAT no ve ceniza' — que es justo lo que la Regla de Oro de la guia le dice que es el numero de referencia. Peor aun en la grilla de volcan, donde el caption fijo afirma 'sin dibujo = VOLCAT no detecta ceniza, no es una falla': con el feed congelado esa frase pasa a ser falsa. Impacto alto x frecuencia media x accionabilidad alta x costo bajo = alto.

*Fix sugerido:* Reusar map_helpers.render_scan_status_badge (o su logica) para VOLCAT con umbrales propios: la latencia normal SSEC es 30-50 min (documentado en zonas_fullscreen.py:909), asi que verde <60 min, ambar 60-120, rojo >120 con 'SSEC no publica desde ...'. Mostrar fecha completa en el KPI. En el panel de la grilla, condicionar la frase 'sin dibujo = no detecta ceniza' a que el frame sea fresco.

### `src/fetch/volcat_api.py:239` — **medium**/conf=high · eje E

**El fallback a sat='all' puede servir un frame de GOES-18 sobre Chile y la UI nunca dice que satelite esta mirando**

volcat_latest: `if not frames and sat != 'all': frames, coords = _query_frames(sector, instr, image_type, 'all'); used_sat = 'all'` (l.239-243). El docstring de la propia funcion (l.220-228) explica por que eso importa: 'el API VOLCAT devuelve frames de GOES-18 (West) Y GOES-19 (East) MEZCLADOS... GOES-18 ve Chile desde el Pacifico con angulo MUY oblicuo (peor parallax, peor geolocalizacion, pluma tumbada)'. La variable `used_sat` se asigna y NUNCA se usa. El dict devuelto SI trae una clave 'sat' derivada del nombre de archivo (l.260), pero grep de '"sat"' / "'sat'" en dashboard/views/*.py = 0 matches: ninguna vista la lee ni la muestra.

*Escenario de fallo:* Sector Chile_South sin frames GOES-19 por una hora (cobertura intermitente, lo que el propio st.warning de l.1219-1227 admite que pasa). El fallback trae un frame GOES-18. El operador mide la posicion y la altura del tope de una pluma sobre Hudson a partir de una imagen tomada con ~30-40° mas de angulo cenital, sin ningun indicio en pantalla. La pluma aparece corrida y 'tumbada' respecto de la realidad, y el numero que se toma como referencia cuantitativa es el peor de los dos disponibles. Impacto medio-alto x frecuencia baja x accionabilidad media x costo trivial = medio.

*Fix sugerido:* Devolver `used_sat` en el dict y pintar un badge cuando no sea GOES-19: 'frame GOES-18 (West) — vista oblicua, georreferencia y altura degradadas'. Es informacion que ya se calcula y se tira.

### `dashboard/views/comparador.py:110` — **medium**/conf=high · eje F

**Panel roto y panel legitimamente oscuro son indistinguibles: _plot_frame no anota nada cuando la imagen es None**

comparador._plot_frame (l.103-136): `if img is not None: fig.add_layout_image(...)` y no hay ninguna rama else — el resto de la funcion dibuja el triangulo, los ejes y `paper_bgcolor='#0a0e14'`. Resultado: un panel negro con el marcador y el titulo, identico a una escena real oscura. La leyenda del propio dashboard define negro como un estado FISICO valido: live_viewer.py:829 'Negro / gris oscuro -> Superficie caliente sin nubes (noche despejada)'. El guard de l.443-448 solo aborta si fallan LOS DOS frames; con uno solo caido, se renderiza el negro. Las vistas hermanas si anotan: modo_guardia_volcan.py:497-501 ('Sin imagen disponible') y modo_evento.py:194-197 ('Sin imagen'). Caso emparentado: modo_evento.py:341-342 hace `if not timestamps: continue` — la columna entera desaparece del grid de 3 productos sin decir cual falta.

*Escenario de fallo:* Modo baseline, Villarrica, hace 7 dias: RAMMB no tiene ese tile (poda de archivo, hueco de publicacion). El operador ve BASELINE completamente negro y AHORA con nubes. Lee 'hace 7 dias no habia nada, hoy hay senal' — o sea, interpreta un fallo de descarga como evidencia de cambio, que es exactamente la pregunta que el modo baseline existe para responder. Impacto medio-alto x frecuencia media (RAMMB falla de forma intermitente, es un gotcha conocido del proyecto) x accionabilidad alta x costo trivial = medio.

*Fix sugerido:* Agregar la misma anotacion 'Sin imagen disponible (fallo de descarga, no es una escena oscura)' en comparador._plot_frame cuando img is None, y en modo_evento renderizar el panel con la anotacion en vez de `continue`. Un test AST/render que verifique que toda funcion que acepta `img: np.ndarray | None` tiene rama de anotacion.

### `dashboard/map_helpers.py:95` — **medium**/conf=high · eje E

**Tres radios de atribucion de hot spots coexisten con sesgos opuestos y ninguno se declara en pantalla**

(1) HOTSPOT_NEAR_KM = 30.0 y filter_hotspots_near_volcanoes (map_helpers.py:95-110) BORRA todo foco a mas de 30 km de cualquier volcan; lo aplican modo_guardia_volcan.py:219-220 (la grilla y el disparador de la altura propia) y zonas_fullscreen.py:80-81. (2) 50 km de atribucion en src/fetch/frp_timeline.sum_frp_per_volcano (l.57, radius_km=50.0) y en modo_evento.EVENT_BBOX_KM=50 (l.45). (3) Vista Nacional de live_viewer (l.960-964): sin filtro alguno, dibuja el FDCF crudo. Ningun caption, help ni leyenda menciona ninguno de los tres numeros.

*Escenario de fallo:* (a) Enero, incendios forestales en la Araucania. La curva de Pulso termico marca 400 MW en Llaima porque un foco a 45 km entra en el radio de 50 km, y la vista Heatmap NO tiene mapa: el operador no puede ver donde esta el foco sin cambiar de vista. (b) Al reves: el turno prende hot spots en Nacional y cuenta 12 diamantes; abre la grilla del mismo volcan en el mismo scan y la cabecera dice 'Hot spots 0' — porque uno filtra a 30 km y el otro no. Sin explicacion, el operador desconfia de las dos. (c) Un flujo de lava o una fisura distal a >30 km del cono catalogado se BORRA de la grilla y ademas no dispara el retrieval automatico de altura. Impacto medio-alto x frecuencia alta (verano) x accionabilidad media x costo bajo = medio-alto.

*Fix sugerido:* Unificar el radio en src/config.py y declararlo en el caption de cada vista que muestre hot spots ('focos a <=30 km de un volcan del catalogo; los mas lejanos — incendios, industria — se ocultan'). En el Heatmap, agregar la distancia y las coordenadas del foco que aporta el FRP, o un mini-mapa, para poder descartar incendio sin salir de la vista.

### `dashboard/views/heatmap_actividad.py:67` — **medium**/conf=high · eje B

**Ninguna vista responde '¿cual de los 43 necesita mi atencion ahora?': todo lo cuantitativo esta restringido a 8 volcanes**

Heatmap: filas = PRIORITY_VOLCANOES (l.67, 74, 253, 322, 336). Pulso intradia: scripts/build_frp_timeline.py:97 usa get_priority(), o sea que el JSON solo contiene los 8 — un foco junto a un volcan no prioritario no existe en el dato, no hay bucket 'otros'. Modo Evento, Comparador (4 modos) y Loops: options=PRIORITY_VOLCANOES. Mosaico: 5. Solo la grilla de volcan (via live_viewer.py:1187-1192) y VOLCAT ofrecen los 43, y ambas son de a UN volcan por vez. La unica vista panoramica real (zonas / mosaico) es de imagenes: hay que mirarlas con el ojo, no ordena ni prioriza nada.

*Escenario de fallo:* Turno de noche, un operador, 43 volcanes. La pregunta operativa es 'que se movio en las ultimas 6 h', y el dashboard esta optimizado para 'que se ve ahora en el volcan que ya elegi'. Para barrer los 43 hay que abrir la grilla 43 veces (4 descargas RAMMB cada una). En la practica nadie lo hace, asi que la vigilancia efectiva son 8 volcanes y los otros 35 dependen de que alguien sospeche primero. Un despertar de un volcan sin ranking (Tupungatito, Sollipulli, Descabezado) no tiene ningun camino en esta app que lo haga aparecer solo. Impacto alto x frecuencia alta x accionabilidad media (requiere diseño) x costo alto = medio-alto.

*Fix sugerido:* Extender build_frp_timeline a los 43 (el costo marginal es CPU sobre hotspots ya descargados: sum_frp_per_volcano itera volcanes, no scans) y agregar una tabla de triage ordenable en el Heatmap: volcan | FRP 6h | Δ vs su propia mediana de 7 d | ultimo scan | edad. Ordenar por Δ, no por valor absoluto — la pregunta es 'cambio', no 'cuanto'.

### `dashboard/views/timeseries_viewer.py:372` — **medium**/conf=high · eje A

**El KPI 'Tendencia' convierte una metrica de color descalificada en un veredicto direccional, y los frames caidos se dibujan como linea continua**

_kpis_from_points (l.344-367) calcula `trend = (media del ultimo cuarto - media del primer cuarto)/primero*100` sobre `valid = [p for p in points if p['available']]`, y el KPI lo rotula 'Tendencia (1° vs 4° cuarto)' con delta textual 'ascendente' / 'descendente' / 'estable' y semaforo (l.369-378). La metrica de base es _ash_red_fraction_v2, de la que el propio proyecto tiene medido que da 9.9-95.5% (mediana 76%) en los 8 prioritarios SIN actividad (CLAUDE.md, 'El gatillo por color NO sirve, y esta medido'). Ademas: (a) el guard `if first > 0.01` deja pasar denominadores de 0.02% -> tendencias de +5000%; (b) _plot_series (l.170-199) grafica solo los `valid` con mode='lines+markers', asi que 3 puntos utiles de 144 se ven como una serie continua; el unico indicio del faltante es el delta del primer KPI ('de N pts disponibles'), y 'Ventana real' (l.380-385) se calcula con points[0]/points[-1] aunque esos frames hayan fallado.

*Escenario de fallo:* Villarrica, ventana 24 h, invierno: pasa un frente de cirros en la segunda mitad. La metrica sube de 20% a 45% por nubosidad. El KPI muestra '+125%' en rojo con la palabra 'ascendente'. El operador, que ya viene anclado por el nivel de alerta amarilla vigente, lo lee como escalada. Variante inversa igual de mala: 'estable' en verde cuando la ventana perdio el 80% de los frames por caida de RAMMB. Impacto medio-alto x frecuencia alta (mayo-septiembre) x accionabilidad alta x costo bajo = medio-alto.

*Fix sugerido:* (1) Suprimir el veredicto textual cuando la cobertura de la ventana < ~80% o cuando el denominador es chico, y mostrar 'insuficiente'. (2) Dibujar los huecos como gap (insertar None en la serie) para que la discontinuidad se vea. (3) Rotular el KPI como 'variacion del proxy de color', no 'Tendencia', y repetir ahi mismo que el proxy no admite umbral absoluto.

### `dashboard/map_helpers.py:284` — **medium**/conf=high · eje D

**GeoColor nunca dice si el frame que estas viendo AHORA es visible o IR nocturno — la nota es estatica y el dato existe**

_PRODUCT_NOTES['geocolor'] = 'color real de dia · IR + luces de ciudad de noche' (l.284): una nota fija, valida para las dos situaciones, que no resuelve cual es la actual. El calculo existe en el repo: src/process/geocolor_lite.solar_elevation(lat, lon, dt) (l.310), usado por hires_pipeline.py:309-310 con DAY_NIGHT_THRESHOLD_DEG. Y mosaico_chile.py:214-226 YA pinta el badge '☀{sun_alt}° (noche/twilight)' con color de alerta... pero SOLO en modo hi-res (zoom_used == -1/-2). Los paneles GeoColor de RAMMB — Vista Operacional (Nacional/Zona/Volcan), la grilla de volcan y Modo Evento — no muestran nada.

*Escenario de fallo:* 04:30 hora Chile (07:30 UTC). El operador abre la grilla del volcan; el orden de lectura que el proyecto definio empieza por GeoColor ('¿hay columna?'). Ve una imagen oscura sin columna visible y pasa a Ash RGB con la impresion de que no hay pluma. En realidad el panel es IR pseudo-color y las luces de ciudad: la columna visible no existe como observable a esa hora, no como resultado. Impacto medio x frecuencia MUY alta (la mitad de las horas del turno son de noche) x accionabilidad alta x costo bajo (la funcion ya existe) = medio-alto.

*Fix sugerido:* Calcular solar_elevation(v.lat, v.lon, ts_del_frame) en el rotulo del panel GeoColor de todas las vistas y mostrar '☀ -12° · NOCHE: no es color real, es IR + luces de ciudad' en ambar. Es la misma linea que ya se usa en mosaico_chile.

### `docs/GUIA_REVISION_DASHBOARD.md:20` — **medium**/conf=high · eje G

**La guia del geologo de turno describe un menu que ya no existe y omite las vistas que hoy son las principales**

La guia (actualizada 2026-07-01) numera las vistas asi: '1. 🔴 En Vivo', '2. Mapa General', '3. Ash RGB Viewer / 4. Detalle Volcan', '5. VOLCAT', '6. Animacion (RAMMB) · 7. Series · 8. Backfill'. El menu real (app.py:139-150 PAGE_OPTIONS) es: Vista Operacional, Modo Guardia, Comparador, Modo Evento, Heatmap actividad, Replay reciente, Backfill historico, Ash + BTD, VOLCAT, Loops descargables, Series de tiempo. 'En Vivo' y 'Animacion' son redirects de compatibilidad (app.py:157-161 _SLUG_REDIRECTS); 'Mapa General' y 'Detalle Volcan' no existen ni como slug. La guia NO menciona Modo Guardia, Modo Sala, la grilla de 4 productos del volcan, Modo Evento, Heatmap, Replay ni Comparador — o sea, ninguna de las vistas que el CLAUDE.md describe como el nucleo del diseño actual. Ademas ubica la altura propia 'en modo Volcan, debajo del VOLCAT primario', cuando desde el PR #27 tambien vive en la grilla.

*Escenario de fallo:* Operador nuevo en su primer turno de noche con la guia impresa al lado. Busca 'Mapa General' para el panorama de los 43 y no lo encuentra; nadie le explica que hoy eso es 'Modo Guardia -> Por Zona Volcanica'. Peor: la guia es el documento que sostiene la Regla de Oro (VOLCAT primario, lo propio INDICATIVO) — si el operador la descarta por desactualizada, se pierde tambien esa regla. Impacto medio x frecuencia alta x accionabilidad alta x costo bajo = medio.

*Fix sugerido:* Reescribir la guia contra PAGE_OPTIONS y linkearla desde el sidebar (ver U5). Test barato de deriva: un test que compare los titulos de seccion de la guia contra PAGE_SLUGS y falle si aparece una vista sin seccion.

### `dashboard/views/modo_evento.py:211` — **medium**/conf=high · eje D

**'Marcar inicio del evento' vive solo en session_state — el manual dice que va en la URL, y la app se auto-recarga**

`event_start_key = f'event_start_{volcan_name}'; event_started = st.session_state.get(event_start_key)` (l.211-212) y el boton hace `st.session_state[event_start_key] = now` (l.253). No hay ninguna escritura a st.query_params del timestamp (la unica es `st.query_params['volcan'] = volcan`, l.447). El manual afirma lo contrario: manuals.py:135-136 'countdown desde inicio del evento (boton "Marcar inicio" — guarda timestamp en URL)'. Agravante: la app instala un watchdog que RECARGA el frame ante 'Connection error' (app.py:31, style.inject_reconnect_watchdog) — cada reconexion se lleva puesto el session_state.

*Escenario de fallo:* Erupcion a las 23:40. El operador marca el inicio; el header cuenta '⏱ Evento marcado hace 3h 12min'. A las 03:00 el servidor se reinicia o el watchdog recarga el frame: el countdown desaparece y el boton vuelve a decir 'Marcar inicio'. Si lo aprieta otra vez, el evento pasa a haber empezado hace 0 minutos, y ese numero es el que se lee en voz alta en la llamada al jefe de turno. Y el permalink que se mando por Slack — el que segun el manual llevaba el timestamp — abre con el countdown vacio para todo el resto del equipo. Impacto medio-alto x frecuencia media x accionabilidad alta x costo bajo = medio.

*Fix sugerido:* Persistir el inicio en la query string (?t0=ISO8601) como promete el manual: sobrevive al reload, al watchdog y al traspaso de turno, y hace el permalink genuinamente compartible. Corregir el manual si se decide no hacerlo.

### `src/volcanos.py:11` — **medium**/conf=high · eje H

**El dashboard se presenta como autosuficiente: no muestra el nivel de alerta vigente ni linkea a ninguna fuente no satelital**

La dataclass Volcano (l.11-19) tiene name/lat/lon/elevation/region/zone/ranking. NO tiene nivel de alerta tecnica, y grep de 'alerta' en dashboard/ no devuelve ninguna vista que lo muestre (dashboard.style.volcano_marker(level) usa 'level' para el TAMAÑO del glifo: wide/region/zone/focus, no para el color de alerta). grep de 'sernageomin.cl|REAV|RAV|VAAC|Buenos Aires|mirova|MOUNTS' sobre dashboard/ devuelve exactamente 2 links utiles, ambos en manuals.py y ambos genericos (mirovaweb.it, volcano.ssec.wisc.edu). No hay ni un link a: el nivel de alerta vigente de SERNAGEOMIN, el ultimo REAV/RAV, el VAAC Buenos Aires (el responsable de Chile), sismologia/OVDAS, DOAS, deformacion, camaras, ni al proyecto hermano VRP Chile — que el propio README presenta en una tabla como complementario.

*Escenario de fallo:* El operador ve una mancha roja en Ash RGB sobre Nevados de Chillan. Para decidir si eso es algo, necesita: ¿que alerta esta vigente? ¿que dice el sismico? ¿la camara ve columna? ¿hay VAA emitido? Ninguna de esas preguntas tiene un camino desde esta pantalla; hay que salir a otras herramientas de memoria. En sentido inverso, el riesgo es peor: una pantalla que muestra 4 productos satelitales de un volcan y nada mas invita a concluir 'no pasa nada' con evidencia de una sola familia de sensores, justo cuando GOES no ve bajo nube ni ve nada de lo que ocurre bajo la superficie. Impacto medio-alto x frecuencia alta x accionabilidad media x costo bajo (son links) = medio-alto.

*Fix sugerido:* Barra de contexto por volcan en la cabecera de la grilla y de Modo Evento con links directos (aunque sean estaticos): SERNAGEOMIN alerta/REAV del volcan, VAAC Buenos Aires, VRP Chile, camara del volcan si existe. Agregar campo de nivel de alerta al catalogo (editable a mano) y usarlo como color del marcador, con la fecha de la ultima actualizacion visible para que se note cuando envejece.

### `dashboard/views/volcat_viewer.py:1405` — **medium**/conf=high · eje F

**'La ausencia de VAA indica condiciones normales' se imprime tambien cuando la consulta de VAA fallo**

_render_vaa_block (l.1380-1406): `vaa = _fetch_vaa_cached(); feats = vaa.get('features', []) if vaa else []` — si vaa es None, feats queda [] y cae en el else, que dice 'Sin Volcanic Ash Advisories activos... La ausencia de VAA indica condiciones normales.' El fetcher devuelve None en cualquier excepcion: src/fetch/realearth_api.fetch_vaa_geojson l.147-149 (`except Exception: logger.error(...); return None`). No se muestra en ningun caso la hora de la consulta ni la ventana de validez de los advisories, y el feed es GLOBAL sin filtro para Chile ni referencia al VAAC responsable.

*Escenario de fallo:* RealEarth timeoutea (o SSEC esta en mantenimiento). El operador abre el bloque VAA para el paso 5 del checklist de la guia ('¿Hay VAA activo?') y lee una afirmacion positiva sobre el estado del mundo — 'condiciones normales' — construida sobre una respuesta que nunca llego. Es el modo de fallo canonico de este SDA: dato ausente presentado como calma. Impacto medio-alto x frecuencia media x accionabilidad alta x costo trivial = medio.

*Fix sugerido:* Distinguir None de lista vacia: con None, st.warning('No se pudo consultar el feed de VAA (RealEarth). Esto NO significa que no haya advisories — verificar en el VAAC Buenos Aires: link'). Con lista vacia, decir 'sin VAA activos al {hora de consulta} UTC' y bajar el tono de 'condiciones normales'. Filtrar o resaltar los advisories de la region Sudamerica.

### `dashboard/app.py:249` — **medium**/conf=high · eje G

**El sidebar visible al operador sigue diciendo que el deploy es Streamlit Cloud y propone HF como pendiente — cuando HF ES el deploy**

Expander '📋 Por hacer' (app.py:245-262): '**Mirror en otro proveedor** (prioridad alta). Levantar copia del dashboard en HuggingFace Spaces o Render para redundancia. Si Streamlit Cloud cae, el mirror sigue... Costo: $0 en HF Spaces'. El README (l.20-22) y la memoria del proyecto dicen que Streamlit Cloud se abandono en jun-2026 y que HF Spaces es hoy el UNICO deploy oficial. El texto tambien menciona el bug de Python 3.14 de Streamlit Cloud como si fuera vigente. El drift de README/INTEGRATION ya se cerro en el audit ago-2026; esta copia, que es la unica que el operador ve, quedo.

*Escenario de fallo:* Cae el Space de HF durante un evento. El operador (o quien lo asista) lee en el sidebar que el deploy es Streamlit Cloud y que el mirror HF esta pendiente, y pierde tiempo buscando/creando la infraestructura equivocada. En frio, el efecto es mas corrosivo: un panel de la app que afirma algo verificablemente falso sobre la app misma erosiona la confianza en el resto de sus afirmaciones. Impacto bajo-medio x frecuencia alta (esta siempre en pantalla) x accionabilidad alta x costo trivial = medio.

*Fix sugerido:* Reescribir el expander contra el estado real (deploy = HF Spaces; el pendiente de redundancia, si sigue vigente, es un segundo proveedor). O sacar el 'Por hacer' del sidebar operativo: el backlog del desarrollador no pertenece a la pantalla de turno.

### `dashboard/views/heatmap_actividad.py:75` — **medium**/conf=medium · eje I

**El verde significa cosas opuestas en la misma pagina: 'hay deteccion termica' en el heatmap y 'calmo' en todo el resto**

colorscale del heatmap (l.75-77): [0,'#0f1418'], [0.01,'#1a3322'], [0.3,'#3fb950'], [0.6,'#d29922'], [1.0,'#ff4444'] con zmax=12 — o sea que ~3-4 scans con deteccion en el dia pintan la celda de VERDE BRILLANTE (#3fb950). En la misma pagina, la tabla de detalle usa '✅ Activo/Calmo' donde el verde es calmo (l.345), el mensaje de calma usa st.success verde (l.257-262) y '#3fb950' es literalmente el color de 'Sistema operativo' del health banner (live_viewer.py:468) y de 'Scan OK' en Modo Guardia (modo_guardia.py:224). Marco confidence medium porque es una convencion, no un bug funcional; el choque semantico si es verificable.

*Escenario de fallo:* Barrido rapido a las 4 AM: el operador escanea el heatmap buscando algo que le llame la atencion. La fila de Villarrica esta verde tres dias seguidos. Verde = tranquilo en todos los demas widgets de esta misma app, asi que sigue de largo — cuando lo que esa fila dice es 'hubo deteccion FDCF en 3-4 intervalos de 10 min por dia', que es precisamente el inicio de una actividad efusiva sostenida. Impacto medio x frecuencia media x accionabilidad alta x costo trivial = medio.

*Fix sugerido:* Escala monocroma ascendente (por ej. azul->amarillo->rojo, o negro->naranja->rojo) donde el color frio sea siempre 'sin senal' y ningun nivel de deteccion sea verde. Reservar el verde en toda la app para 'sistema sano / sin senal'.

### `dashboard/views/modo_evento.py:356` — **medium**/conf=high · eje F

**La pantalla de crisis no tiene banda de estado ni umbral de edad de scan: la antiguedad viaja como texto gris dentro del titulo del panel**

En el grid de 3 productos, la edad se compone como `ts_label = f"{dt.strftime('%H:%M UTC')} (hace {age}m)"` y se concatena al titulo del plot (l.352-360), en gris #e0e0e0 tamaño 12 (l.189). No hay umbral, ni color, ni banner: comparar con live_viewer._health_banner (l.459-490, 3 umbrales + tip) y con modo_guardia.py:220-230. Ademas fetch_frame_robust puede caer a un timestamp anterior y a zoom reducido, y eso se marca solo con un '⚠z3' pegado al final del mismo texto gris.

*Escenario de fallo:* RAMMB se atrasa 90 minutos durante la crisis (escenario documentado como frecuente por el propio proyecto). Los tres paneles de Modo Evento siguen mostrando imagenes plausibles con '(hace 92m)' en gris chico dentro del titulo, mientras el resto de la pantalla se ve normal y el reloj del KPI 4 marca la hora actual con borde ambar. El operador reporta la extension de la pluma de hace hora y media como si fuera actual. La vista mas critica del dashboard es la unica sin semaforo de frescura. Impacto alto x frecuencia media x accionabilidad alta x costo bajo (reusar render_scan_status_badge) = medio-alto.

*Fix sugerido:* Reusar la banda de _health_banner (o render_scan_status_badge) arriba de la grilla de Modo Evento, con los mismos umbrales que el resto de la app (15/30 min), y sacar el KPI 'Render UTC/Chile' que hoy es lo unico grande con hora y que puede leerse como si fuera la hora del dato.

### `dashboard/views/modo_evento.py:446` — **medium**/conf=high · eje D

**Dos volcanes en crisis simultanea no tienen camino: Modo Evento es de a uno y el estado va en la URL**

El volcan es un unico query param (`st.query_params['volcan'] = volcan`, l.446-447) y el layout es de un solo volcan (header, KPIs, grid de 3, tabla de hot spots). No existe ningun modo de 2 volcanes en crisis: comparador._mode_dos_volcanes (l.293-297) compara 2 volcanes pero con UN producto y sin hot spots, viento, anillos ni tabla. El mosaico de Modo Guardia muestra 5 volcanes fijos (los del sub-tab, no elegibles). Cada cambio de volcan en Modo Evento re-dispara descargas (_recent_ts ttl=30 s, fetch_frame_robust sin cache propio).

*Escenario de fallo:* Enjambre regional: Villarrica y Llaima se activan la misma madrugada. El operador tiene que alternar la vista cada pocos minutos; cada ida y vuelta re-descarga 3 frames y pierde el foco visual del otro volcan. El estado de 'Marcar inicio' es por volcan (bien) pero vive en session_state (ver U17), asi que la alternancia sumada a un reconnect se lleva los dos relojes. Impacto medio-alto x frecuencia baja x accionabilidad media x costo medio = medio.

*Fix sugerido:* Aceptar `?volcan=A,B` en Modo Evento y renderizar dos columnas reducidas (header + KPIs + Ash RGB + hot spots por volcan), o al menos permitir abrir Modo Evento en dos pestañas sin que el escritor de query params de una pise a la otra.

### `dashboard/views/live_viewer.py:972` — **medium**/conf=high · eje F

**'Sin hot spots FDCF en Chile en este scan. Es lo normal' se imprime igual cuando la consulta a FDCF fallo**

l.967-977: si hotspots_nacional esta vacio, se imprime 'Sin hot spots FDCF en Chile en este scan ({ts}). Es lo normal: el algoritmo solo detecta superficies muy calientes...'. La unica diferencia entre 'no hay focos' y 'FDCF no respondio' es que hotspots_scan_ts es None y el ts se renderiza como '—' en medio de la frase. _fetch_hotspots_cached (l.280-292) devuelve `[h.to_dict() for h in hotspots], ts_str`, y fetch_latest_hotspots devuelve ([], None) en TODOS sus error paths: s3fs/xarray ausente (goes_fdcf.py:329), sin archivos en la ventana (l.335) y excepcion al leer el granulo (l.350). El contrato ([], None) ya fue reportado en el audit ago-2026 como mejora; lo nuevo es que la UI, encima, tranquiliza activamente al operador con 'Es lo normal'.

*Escenario de fallo:* S3 intermitente (el motivo por el que existe _retry_s3, que este fetcher no usa). El geologo prende el toggle de hot spots durante un episodio efusivo en Villarrica, lee 'Sin hot spots FDCF en Chile en este scan (—). Es lo normal' y toma la ausencia como dato. El '—' donde deberia ir una hora es la unica pista, y es exactamente el tipo de detalle que se pierde a las 3 AM. Impacto medio-alto x frecuencia media x accionabilidad alta x costo trivial = medio.

*Fix sugerido:* Cuando hotspots_scan_ts es None, cambiar el mensaje a st.warning('No se pudo leer el producto FDCF en este ciclo (S3/NOAA). La ausencia de focos NO esta confirmada.'). Reservar 'Es lo normal' para el caso en que hay scan y no hay focos. El fix de raiz es el sentinel de error en el fetcher (backlog abierto), pero la rama de UI se puede cerrar sola.

### `dashboard/views/live_viewer.py:1187` — **low**/conf=high · eje G

**Volcanes de prueba extranjeros (Kilauea, Popocatepetl, Sangay, Reventador, Sabancaya) aparecen en los selectores operativos de Chile**

src/volcanos.CATALOG tiene 48 entradas: 43 chilenas + 5 con zone=='test' (l.76-84: Kīlauea (Hawái), Popocatépetl (México), Sangay, Reventador, Sabancaya). El selector de la tab '🔬 Volcán' de Vista Operacional arma `other_names = [v.name for v in CATALOG if v.name not in priority_names]` (live_viewer.py:1189-1190) sin filtrar zone; idem timeseries_viewer.py:1188-1191. La pagina VOLCAT SI filtra: `_cat = [v for v in CATALOG if v.zone != 'test']` (volcat_viewer.py:1134), y filter_hotspots_near_volcanoes tambien (map_helpers.py:107) — o sea que el filtro existe y esta aplicado de forma inconsistente. El sidebar rotula 'Chile · 43 volcanes' y el layer se llama 'Todos (43+)'.

*Escenario de fallo:* En un dashboard rotulado 'Chile · 43 volcanes' y usado para vigilancia de la RNVV, el desplegable ofrece 'Popocatépetl (México)' entre Osorno y Puyehue. Un operador nuevo no sabe si es un volcan chileno que no conocia o un error, y una captura generada desde ahi (con timestamp y encuadre impresos, lista para un informe) queda etiquetada como producto de un sistema de la RNVV. Impacto bajo x frecuencia media x accionabilidad alta x costo trivial = bajo-medio.

*Fix sugerido:* Aplicar `v.zone != 'test'` en los dos selectores (o mejor: mover los 5 de prueba fuera de CATALOG, a un TEST_CATALOG que solo importen los tests y el backfill). Test de regresion: ninguna opcion de selector operativo con zone=='test'.

### `dashboard/manuals.py:145` — **low**/conf=high · eje B

**El manual de Modo Evento promete altura VOLCAT y una mini animacion que la vista no tiene**

manuals.py:145 ('**Altura VOLCAT** si esta disponible (SSEC RealEarth).') y el docstring del modulo (modo_evento.py:9-10, 'mini animacion, estado VOLCAT si hay altura'). grep 'VOLCAT|volcat' en modo_evento.py devuelve UNICAMENTE esa linea de docstring: no hay import de volcat_api, ni de _volcat_latest_cached, ni panel alguno. Tampoco hay animacion. Y no hay ningun boton de exportacion en toda la vista (grep 'download' = 0), pese a que el manual la describe como la pantalla para 'llamar al jefe en <60 s' y a que dashboard/exports.py ya provee download_buttons.

*Escenario de fallo:* El operador abre el manual de Modo Evento buscando la altura de la pluma — el numero que la guia declara como la referencia cuantitativa — y baja por la pantalla buscandolo. No esta. Pierde tiempo en el peor momento y despues tiene que ir a la pagina VOLCAT igual. Cuando finalmente tiene la evidencia en pantalla, no hay ni un boton para capturarla: para el informe hay que hacer captura de pantalla del navegador, sin timestamp ni encuadre impresos (justo la trazabilidad que el proyecto se tomo el trabajo de construir en exports.py). Impacto bajo-medio x frecuencia baja x accionabilidad alta x costo bajo = bajo-medio.

*Fix sugerido:* O agregar el panel VOLCAT (reusando _panel_volcat de modo_guardia_volcan, ya parametrizado) y los download_buttons de exports.py, o corregir manual y docstring. Dado que Modo Evento es la vista de crisis, la primera opcion es la correcta: es la unica pantalla que se va a proyectar y a adjuntar a un informe.