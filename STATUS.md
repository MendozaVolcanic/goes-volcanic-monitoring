# STATUS — Goes Dashboard

**Última actualización:** 2026-11-17 (cierre de sesión, bloque "## 0." abajo). Roadmap curado: 2026-08-30 (auditoría adversarial)
**Repo:** https://github.com/MendozaVolcanic/goes-volcanic-monitoring
**Deploy en producción:** 🤗 Hugging Face Spaces —
https://mendozavolcanic-goes-volcanic-monitoring.hf.space

> Este archivo es el **roadmap curado por humanos**. Es corto a propósito: el
> detalle técnico vive en `CLAUDE.md`, la integración con otros proyectos en
> `INTEGRATION.md`, y la guía de turno en `docs/GUIA_REVISION_DASHBOARD.md`.

> **El mirror de Streamlit Cloud (`goesvolcanic.streamlit.app`) está muerto** y
> no se actualiza desde jun-2026 (sleep ~6 h + `KeyError` intermitentes de
> Python 3.14). No enlazarlo. HF Spaces es el único deploy oficial; lo mantiene
> despierto `keepalive_hf.yml`.

> **`STATUS_NRT.md` ya no existe.** El workflow que lo escribía (`goes.yml`)
> tiene el cron desactivado desde 2026-05-15 — fallaba en cada corrida y nadie
> consumía el archivo. Quedó como `workflow_dispatch` manual.

---

## 0. 2026-11-17 cierre de noche (PR 43 en main, Chillán a 10 min, umbral de manto)

> Reemplaza como estado vigente al bloque "## 0-prev. 2026-11-17 noche" de abajo,
> que se conserva. Verificado contra GitHub y la API de Hugging Face al escribir esto.

| Qué | Estado | Evidencia |
|---|---|---|
| Mínimo del tope VOLCAT como área del sensor | **En `main`**, CI de main verde | PR 43, merge `d62753a`; ficha SDA v2.7 |
| Hugging Face | **RUNNING con `main` @ `d62753a`** (sha del Space `fd8d8ff`), desplegado con el sí de Nicolás | API de HF y rótulo `build-20261117-1737-d62753a` en la página pública |
| PR abiertos | ninguno | `gh pr list` |
| VOLCAT Chillán 01 a 16-11 a 10 min | analizado, entregado | plan de validación §3.4; MP4 en `C:\Users\nmend\Downloads\` |
| Umbral de manto `MAX_SECTOR_FRAC` (5 % del sector) | **falla reproducida, sin cambio de código** | plan §3.4: el 16-11 da tope 16 a 18 km sobre Chillán con el código de producción |
| Volcanes VOLCAT faltantes con coordenadas GVP | no empezado | sin rama |
| Validación VOLCAT pasos 3 a 6 | no empezados | criterio ya decidido (cruce de intervalos) |

Chillán, días con ceniza anclada al cráter (hora de Chile): 08-11 (11:00 a 18:30,
1 a 4 km), 10-11 (12:00 a 12:10 y 18:30 a 20:30, 3 a 5 km), 11-11 (14:50 a 15:10,
3 a 5 km) y 14-11 (13:40 a 20:30, 3 a 5 km). El 16-11 es un sistema que entra desde
~110 km, no pluma. El loop de una imagen por hora se saltaba el pulso del 10-11 al
mediodía: para eventos cortos, cadencia completa.

Decisiones que esperan a Nicolás:

| # | Pregunta | Recomendación |
|---|---|---|
| 1 | Umbral de manto: (a) km² del objeto, (b) criterio temporal, (c) exclusión a ojo | (c) para el paso 3; (b) si la lectura VOLCAT llega a la app (plan §3.4) |

Prompt para la próxima sesión: "/retomar en Goes. Lee STATUS.md ## 0. Si Nicolás ya
respondió la decisión 1, ejecútala; después sigue con los volcanes VOLCAT con
coordenadas GVP (Olca, Aucanquilcha, Putana, Ojos del Salado, Cerro Azul/Quizapu,
Lautaro) o con el paso 3 de la validación, lo que él elija."

---

## 0-prev. 2026-11-17 noche (TOP_MIN_PX como área del sensor, PR abierto)

> Reemplaza como estado vigente al bloque "## 0-prev. Cierre 2026-11-17 tarde"
> de abajo, que se conserva. El PR 42 ya está en `main` (088fb72).

| Qué | Estado | Evidencia |
|---|---|---|
| Mínimo del tope VOLCAT como área del sensor | **PR abierto, sin merge** | rama `fix/top-min-area-sensor`; ficha SDA v2.7; plan de validación §3.3 |
| Volcanes VOLCAT faltantes con coordenadas GVP | **No empezado** | sin rama; se traspasa a una sesión nueva por contexto |
| Validación VOLCAT pasos 3 a 6 | No empezados | ya no los bloquea el umbral; falta el criterio ya decidido aplicado |

Hallazgos del cambio (detalle en el plan §3.3):
- Sabancaya 01-11: 03:00 y 03:20 bajan de 7 a 8 km a 6 a 7 km; 03:10 queda en
  7 a 8 km con 12,5 km² (borde); desde 03:30 el tope de 7 a 8 km es firme.
- Sabancaya 26-10: sin los 16 a 18 km, pero 12:20 a 12:40 dan 12 a 14 km con
  3 a 4 píxeles IR. **Decisión de Nicolás**: ¿subir el umbral? Recomendación:
  no por ahora; el evento ya está excluido a ojo y subirlo costaría 03:10 del 01-11.
- Los cuadros cosechados viven sólo en el worktree `volcat-propio-continuar-79dff8`
  (`data/raw/volcat_validacion/`, gitignored): no borrar ese worktree.

---

## 0-prev. Cierre 2026-11-17 tarde (miniatura de Series arreglada en PR 42)

> Reemplaza como estado vigente al bloque "## 0-prev. Cierre 2026-11-17"
> de abajo, que se conserva. Sesión cerrada al aviso de contexto (150 mil
> tokens) tras terminar el primero de los tres PR pedidos. Todo verificado
> contra GitHub, sin trabajo en segundo plano al escribir esto (sólo el CI
> del PR 42 en curso).

### a. Todo en una pantalla

| Qué | Estado | Evidencia |
|---|---|---|
| Miniatura de Series cortada (0-prev d.1) | **PR abierto, sin merge**, CI en curso al cerrar | [PR 42](https://github.com/MendozaVolcanic/goes-volcanic-monitoring/pull/42), rama `fix/miniatura-series-ancho` @ `656d28a`; `tests/test_hora_chile.py` 26 pasan en local |
| `TOP_MIN_PX` como área del sensor | **No empezado** | sin rama |
| Volcanes VOLCAT faltantes con coordenadas GVP | **No empezado** | sin rama |
| `main` | sin cambios de esta sesión | `2dddda7` (bot FRP sobre `3084b22`) |
| Hugging Face | RUNNING con `main` @ `54f2528` (sigue con la miniatura cortada) | API de HF consultada al empezar |

### b. Decisiones que esperan a Nicolás

| # | Pregunta | Opciones | Recomendación |
|---|---|---|---|
| 1 | ¿Mergear el PR 42 y desplegar? | ahora / tras mirarlo en local | **Mergear con CI verde y desplegar**, y mirar la vista Series en la página pública (Láscar, radio 1°): es lo único que falta verificar. |
| 2 | Criterio de consistencia de los pasos 3 a 6 de VOLCAT | ver 0-prev (16-11) b.1 | sigue sin respuesta; (a) cruce de intervalos |

### c. Lo aprendido

- **Causa de la miniatura cortada** (patrón de defecto, propuesto para
  `CLAUDE.md` Patrones de código): la prueba de ancho medía contra 320 a
  800 px, pero el frame real sale de `reproject_to_latlon` a 60 px por grado
  (zoom 3) y mide **80 a 240 px**. Una prueba de render tiene que construir
  su entrada por el mismo camino de tamaño que producción, no con un ancho
  supuesto. Arreglo: ampliar por factor entero con vecino más cercano
  (`THUMB_MIN_W = 480`) y escalar el marcador con el mismo factor.
- **Medir tinta en un PNG** (trampa de medición): con letra de 8 px el corte
  puede caer en un píxel de antialiasing tenue y un umbral de "blanco > 200"
  da verde falso (pasó con radio 1°). Medir la tinta como diferencia contra
  el color de la propia banda.

### d. Problemas abiertos e hipótesis

1. **SOSPECHA**: el arreglo se ve bien en la app. Verificado sólo sobre el PNG
   generado en local (captura en scratchpad), no en Streamlit corriendo.
2. **CONFIRMADO**: `C_ASH` y `C_SO2` importados sin uso en
   `dashboard/views/timeseries_viewer.py` (pyflakes), anteriores a esta sesión,
   no tocados.

### e. Ya cerrado, no rehacer

- Diagnóstico de la miniatura: no era la fuente ni el sistema operativo, era
  el ancho del frame. No volver a ajustar `_fuente_rotulo`.

### f. Prompt para la próxima sesión

```text
Retomo el dashboard GOES. Usa /retomar. Trabaja desde origin/main actualizado
(git fetch; cada rama nueva cortada de origin/main).
Verifica antes de creer: gh pr list --state open (esperado: PR 42);
gh pr checks 42; git ls-remote origin -h refs/heads/main;
curl https://huggingface.co/api/spaces/mendozavolcanic/goes-volcanic-monitoring.
Lee en orden: CLAUDE.md del repo, STATUS.md "## 0.", docs/FICHA_SDA_GOES.md (v2.6).
Trabajo, cada uno en su rama y PR propio hacia main, SIN fusionar ni desplegar:
  1. TOP_MIN_PX (src/process/volcat_colorbar.py) como área del sensor según
     docs/own_volcat/PLAN_VALIDACION_MAGNITUD.md §3.3: hoy cuenta píxeles del PNG
     (0,2 km² en sector de 250 m); pasarlo a un área en píxeles IR (p. ej. 3 de
     2 km, ~12 km²) convertida con px_km. TDD, mutación, ficha SDA en el mismo commit.
  2. Volcanes del mapeo VOLCAT que faltan en el catálogo (Olca, Aucanquilcha,
     Putana, Ojos del Salado, Cerro Azul/Quizapu, Lautaro) con coordenadas del
     WFS del Smithsonian GVP (volcano.si.edu da 403 a bots), nunca adivinadas,
     como se hizo con Lastarria.
  3. Actualizar STATUS.md con los enlaces de los PR nuevos.
Si el PR 42 ya se mergeó y desplegó: mirar la vista Series en la página pública
(Láscar, radio 1°) y confirmar que la hora de Chile se ve entera.
No empezar los pasos 3 a 6 de la validación VOLCAT sin el criterio de Nicolás.
Reglas duras: la carpeta principal está en audit/2026-11-previa-local y no se toca;
docs/auditoria_2026-11 nunca se sube ni se citan sus números de hallazgo; no borrar
worktrees viejos; español de Chile sin voseo y sin guiones largos (grep); rutas
absolutas; nada de VIIRS; ausencia de dato nunca es calma; SDA (CPLT 372).
Si llegas al ~50 % de contexto, cierra con /cierre.
```

---

## 0-prev. Cierre 2026-11-17 (merges 36 a 40, deploy y lo que sigue)

> Reemplaza como estado vigente a los dos bloques "## 0-prev." de abajo (16-11),
> que se conservan como histórico. Todo lo de la tabla se verificó hoy contra
> GitHub y la API de Hugging Face, no de memoria.

### a. Todo en una pantalla

| Qué | Estado | Evidencia |
|---|---|---|
| PR 36 (guard de perfil GFS, ficha v2.4) | **En `main`** | merge `094f798` |
| PR 38 (validación VOLCAT pasos 0 a 2, ficha v2.5) | **En `main`** | merge `c1b5141` |
| PR 39 (loop VOLCAT de 1, 3, 10 y 16 días) | **En `main`** | merge `e520c9e`; ficha sube a v2.6 en este PR para registrarlo |
| PR 40 (Comparador con todo el catálogo) | **En `main`** | merge `5910de4` |
| PR 37 (hora de Chile sin sigla, miniatura en dos líneas) | **En `main`**, pero ver d.1 | merge `54f2528`; CI de main verde: 592 pasan, 4 saltadas |
| Deploy Hugging Face | **RUNNING** | Space sha `4d59609` (snapshot huérfano de `main` @ `54f2528`); cartel del sidebar `build-20261117-0444-54f2528`; página pública abierta: vista Series carga y calcula, vista VOLCAT ofrece "1, 3, 10 o 16 días" |
| Validación VOLCAT pasos 3 a 6 | No empezados | requiere antes el arreglo de `TOP_MIN_PX` (pendiente 1) |

### b. Lo que sigue, priorizado

1. **Miniatura de Series cortada en producción** (d.1): arreglar con TDD y
   mutación; la prueba actual dio verde y el defecto se ve igual.
2. **`TOP_MIN_PX` como área del sensor** (`docs/own_volcat/PLAN_VALIDACION_MAGNITUD.md`
   §3.3): hoy cuenta píxeles del PNG; en un sector de 250 m eso es 0,2 km².
   Pasarlo a un área en píxeles IR (p. ej. 3 de 2 km, ~12 km²) convertida con
   `px_km`, con ficha SDA en el mismo commit. Es el paso previo a los pasos 3 a 6.
3. **Volcanes del mapeo VOLCAT que faltan en el catálogo**: Olca, Aucanquilcha,
   Putana, Ojos del Salado, Cerro Azul/Quizapu, Lautaro, con coordenadas del
   Smithsonian GVP (WFS, como Lastarria), nunca adivinadas.
4. **Validación VOLCAT pasos 3 a 6** (plan §3), con el criterio de consistencia
   decidido por Nicolás ANTES de ver números (ver 0-prev, validación, b.1).
5. **Decisiones de Nicolás que tocan cifras del paper**: máscara FDCF 30 a 35
   con etiquetas de confianza; el verde del Ash RGB (SO₂ o cirros); altura
   propia marcada INDICATIVO y con paralaje.
6. **Coherencia entre vistas**: distorsión E-O del 31 % en la vista Zona; rumbo
   y paralaje en la regla; rótulos de anillos que se pisan.
7. **Migración a servidor local** y auditoría de rendimiento.

### c. Lo aprendido

- **El script de deploy hace `git checkout main`**: no corre desde un worktree
  si `main` está tomado por otro. Se desplegó desde el worktree que tenía `main`
  (limpio, avanzado con `--ff-only`). El sha del Space nunca es el de `main`
  (es un commit huérfano); la prueba de qué build corre es el cartel
  `build-<fecha>-<sha de main>` del sidebar.
- **Una prueba de ancho de texto no prueba que se vea**: la del PR 37 pasa en
  CI y la miniatura igual sale cortada en producción (d.1). Verificar en la
  página pública, no sólo en la suite.

### d. Problemas abiertos e hipótesis

1. **CONFIRMADO** (visto en la página pública, 17-11 04:4x UTC, Láscar, Ash
   RGB, 6 h): en las dos miniaturas de Series ("PICO" y "ÚLTIMO") la segunda
   línea `2026-11-17 04:20 UTC · …` se corta en el borde derecho y la hora de
   Chile no se ve. Captura:
   `C:\Users\nmend\AppData\Local\Claude-Data\claude_pzs8sxrjxfjjc\side-session-notes\local_f3a7d295-ddde-4b7c-b258-25e760c44266\miniatura_series_cortada_2026-11-17.jpg`.
   Causa: SOSPECHA, la prueba `test_rotulo_de_miniatura_de_series_cabe` mide
   otra línea, otra fuente o otro ancho que el que se dibuja en el servidor.
2. Pendiente heredado sin tocar: avisos de `pyflakes` preexistentes
   (`used_sat` en `volcat_api.py`, imports sin uso en `volcat_viewer.py` y
   `comparador.py`).

### e. Prompt para la próxima sesión

```text
Retomo el dashboard GOES (C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\Goes).
Usa /retomar. Verifica antes de creer: gh pr list --state open; git ls-remote origin -h
refs/heads/main; curl https://huggingface.co/api/spaces/mendozavolcanic/goes-volcanic-monitoring.
Lee en orden: CLAUDE.md del repo, STATUS.md "## 0.", docs/FICHA_SDA_GOES.md (v2.6).
Trabajo, cada uno en su rama y PR propio hacia main, SIN fusionar ni desplegar:
  1. Miniatura de Series cortada (STATUS.md 0.d.1): reproducir con una prueba que falle
     sobre el PNG real, arreglar, mutación.
  2. TOP_MIN_PX como área del sensor (plan §3.3), TDD, mutación, ficha SDA en el mismo commit.
  3. Volcanes VOLCAT faltantes con coordenadas GVP (WFS), nunca adivinadas.
No empezar los pasos 3 a 6 de la validación sin el criterio de Nicolás.
Reglas duras: la carpeta principal está en audit/2026-11-previa-local y no se toca;
docs/auditoria_2026-11 nunca se sube ni se citan sus números de hallazgo; español de
Chile sin voseo y sin guiones largos; rutas absolutas; nada de VIIRS; SDA (CPLT 372).
```

---

## 0-prev. Cierre 2026-11-16 (sesión Replay + loop VOLCAT + Comparador)

> Actualizado tras el cierre: la sesión "Validación de magnitud" terminó su
> turno sin empezar los pasos 3 a 6. Sólo alcanzó la revisión a ojo de los
> anclajes (`c99338a` en el PR 38) y encontró un umbral mal dimensionado que
> hay que corregir antes de comparar contra nuestras alturas; está escrito en
> `docs/own_volcat/PLAN_VALIDACION_MAGNITUD.md` de esa rama. El PR 38 trae
> además su propio bloque "## 0." en este archivo (`8703435`, pasos 0 a 2):
> al mergear, el más reciente queda como "## 0." y el otro pasa a "## 0-prev.",
> sin borrar ninguno.

### a. Todo en una pantalla

| Qué | Estado | Evidencia |
|---|---|---|
| Replay por fecha: 4 productos lado a lado (GeoColor, Ash RGB, SO₂, VOLCAT) y botón Play del día | **En `main`** | PR 35, merge 2026-11-15 16:09 UTC |
| Loop animado VOLCAT (GIF, MP4 y en pantalla) | **En `main`** | PR 32 |
| Menos descargas por ciclo (caché de tiles y pestañas perezosas) | **En `main`** | PR 34 |
| Lastarria en el catálogo | **En `main`** | PR 33 |
| Deploy Hugging Face | RUNNING, `lastModified` 2026-11-15 16:09 UTC (coincide con el merge del PR 35) | API de HF consultada hoy |
| Bot FRP | Produce: último commit de `data/frp_timeline.json` 2026-11-16 17:57 UTC | `gh api .../commits?path=` |
| Loop VOLCAT de 1, 3, 10 y 16 días (evolución de Chillán) | **Rama sin mergear**, CI verde | PR 39, `feat/volcat-loop-dias`; suite local 542 pasan, 2 saltadas |
| Comparador con todo el catálogo (prioritarios primero, con ★) | **Rama sin mergear**, CI verde | PR 40, `feat/comparador-catalogo` @ `fefd751` |
| Guard de perfil GFS en la altura (no convertir con T(z) de otro momento) | **Rama sin mergear**, CI verde | PR 36 |
| Validación de magnitud VOLCAT, pasos 0 a 2 | **Rama sin mergear**, apilada sobre PR 36, sin CI (su base no es `main`) | PR 38 |
| Validación VOLCAT, pasos 3 a 6 | **No empezados**; revisión previa de anclajes hecha, con un umbral a corregir | PR 38, `c99338a`; plan en `docs/own_volcat/PLAN_VALIDACION_MAGNITUD.md` de esa rama |
| Hora de Chile con desfase numérico (sin "-03") | **Rama sin mergear, CI ROJO** | PR 37; ver d.1 |
| Loops de Chillán en archivo | Entregados, fuera del repo | `C:\Users\nmend\Downloads\volcat_nevados_chillan_2026-11-08_r1.5deg.mp4` y `.gif`; `C:\Users\nmend\Downloads\volcat_nevados_chillan_16dias_2026-10-31_a_2026-11-16_r1deg.mp4` (9,8 MB) y `.gif` (25 MB) |

### b. Decisiones que esperan a Nicolás

| # | Pregunta | Opciones | Recomendación |
|---|---|---|---|
| 1 | ¿Mergear PR 39 y PR 40? | ahora / después de probarlos en local | **Ahora**: ambos con CI verde, tocan sólo vistas (no lógica de decisión del SDA) y traen pruebas propias. |
| 2 | Orden de merge de 36, 38 y 39 (los tres tocan `docs/FICHA_SDA_GOES.md`) | cualquiera / 36, 38, 39 | **36, luego 38, luego 39**: 36 sube la ficha a v2.4, 38 a v2.5, y 39 edita B.9 sin subir versión. En ese orden, 39 sólo resuelve el conflicto de texto en B.9 y anota el cambio como v2.6. |
| 3 | PR 37 con CI rojo | relajar la prueba / achicar el rótulo / cerrar el PR | **Achicar el rótulo** (o fuente más chica en miniaturas de 320 px): la prueba hace bien en fallar, el texto no cabe con la fuente del runner Linux. |
| 4 | ¿Deploy a HF después de mergear? | sí / esperar | **Sí, tras 39 y 40**, para que el loop de 16 días de Chillán quede en la app pública. |

### c. Lo aprendido

- **Animación Plotly con `layout.images`** (patrón del proyecto, quedó en
  `CLAUDE.md`, Gotchas): cada frame necesita `redraw: True`, y un frame que
  fija `annotations` o `images` **reemplaza la lista entera**: lo estático
  (rótulos de la barra de escala, barra de color de VOLCAT) se repite en cada
  frame o desaparece en el segundo cuadro.
- **Loop de días: un cuadro real por paso, nunca relleno** (regla de método,
  vive en el código del PR 39, `volcat_api.submuestrear`): el más cercano a
  cada punto de la grilla a menos de medio paso, sin repetir uno, con su propia
  hora; un punto sin cuadro se lista como faltante y el salto se mide contra el
  paso, no contra los 10 min nativos. Proponer un bullet en `CLAUDE.md` cuando
  entre el PR 39.
- **Costo por cuadro** (trampa de medición, en memoria
  `reference_rammb_retencion.md`): un tile RAMMB es un PNG de 678 px de hasta
  ~0,7 MB y un recuadro de 0,4° cae en 1 a 4 tiles; un cuadro VOLCAT de sector
  completo pesa 0,37 a 0,55 MB. Cargar un día entero de 4 productos con la red
  saturada tomó ~20 min; por eso la carga en dos etapas con ETA.
- **Probar en el navegador del panel** (trampa de prueba, vale para todo el
  workspace): un panel oculto pausa `requestAnimationFrame`, así que una
  animación "se pega" sin ser bug (verificar los frames por `relayout`). Una
  fecha escrita a mano en `st.date_input` no se confirma: elegirla en el
  calendario.
- **VOLCAT**: SSEC guarda ~30 días; para "el mes en curso" la ventana útil más
  larga es 16 días.

### d. Problemas abiertos e hipótesis

1. **CONFIRMADO**: PR 37 falla en CI en
   `tests/test_hora_chile.py::test_rotulo_de_miniatura_de_series_cabe[320]`,
   `327.89 <= 310` (1 falla, 556 pasan). El rótulo de hora nuevo no cabe en la
   miniatura de 320 px con la fuente del runner Linux.
2. **CONFIRMADO**: la FICHA SDA tendrá conflicto de versión al mergear 36, 38 y
   39 (ver b.2). Lo mismo `STATUS.md` entre este PR y el 38: ambos agregan un
   bloque "## 0." en el mismo lugar.
3. **SOSPECHA**: el deploy de HF contiene exactamente `main` al merge del PR
   35; sólo coincide la hora, no comparé el sha del Space con el del repo.
4. **SOSPECHA**: con la red normal (no saturada) la carga del día completo del
   Replay debería bajar bastante de los ~20 min medidos; no lo medí.
5. **CONFIRMADO** que existen, no son de esta sesión: avisos de `pyflakes`
   preexistentes (`used_sat` y unos imports sin uso en `volcat_viewer.py` y
   `comparador.py`). No tocados.

### e. Ya cerrado, no rehacer

- Replay por fecha con los 4 productos y Play: hecho y mergeado (PR 35). Los
  huecos se cuentan honestos (14-11 Lastarria: 9 scans SO₂ no publicados por
  RAMMB, 8 imágenes no descargadas, 8 cuadros VOLCAT no publicados por SSEC).
- Los textos de retención de RAMMB ya dicen lo medido (continuo desde
  01-09-2026 más días sueltos); no volver a "28 días" ni "9-10 meses".
- Loop de 16 días de Chillán: ya generado en archivo (383 cuadros, 1 descarga
  fallida anunciada); no hace falta volver a bajarlo para mostrarlo.
- Que `get_volcano` resuelva bien todo el catálogo (riesgo de coincidencia
  parcial): verificado, cada nombre se resuelve a sí mismo.
- Qué es VOLCAT y de dónde salen los datos: explicado; lo esencial ya vive en
  memoria (`reference_volcat_source.md`).

### f. Prompt para la próxima sesión

```text
Retomo el dashboard GOES (C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\Goes).
Usa /retomar. Antes de creerle al traspaso:
1. gh pr list --state open  (esperados al 16-11: 36, 37, 38, 39, 40)
   y gh pr checks <n> en cada uno; el 37 tenía CI rojo.
2. Si vas a seguir la validación VOLCAT, lee primero
   docs/own_volcat/PLAN_VALIDACION_MAGNITUD.md en la rama del PR 38
   (revisión de anclajes en c99338a: hay un umbral mal dimensionado que se
   corrige antes del paso 3).
3. git ls-remote origin -h refs/heads/main contra lo que diga STATUS.md.
Lee en orden: CLAUDE.md del repo, STATUS.md sección "## 0.", docs/FICHA_SDA_GOES.md.
Trabajo sugerido, en orden:
  a. Con mi visto bueno, mergear 36, 38 y 39 en ese orden resolviendo la
     versión de la FICHA SDA (B.9), y el 40.
  b. Arreglar el PR 37 (rótulo que no cabe en la miniatura de 320 px).
  c. Deploy a HF (bash scripts/deploy_hf.sh) y verificar el loop de 16 días
     de Chillán en la app pública.
Reglas duras: ramas nuevas y PR a main SIN mergear ni desplegar salvo que yo
lo pida; no tocar ni subir docs/auditoria_2026-11; español de Chile sin voseo
y sin guiones largos; rutas absolutas; nada de VIIRS; SDA (CPLT 372): ficha
en el mismo commit que la lógica y ausencia de dato nunca se muestra como
calma; TDD.
Si la sesión no alcanza: deja el estado en STATUS.md con /cierre.
```

---

## 0-prev. Cierre de sesión 16-11-2026: validación de magnitud contra VOLCAT (pasos 0 a 2)

> **Estado fijado con trabajo en curso.** La sesión "Validación de magnitud
> VOLCAT: pasos 3 a 6" (local_f702bfa8) estaba trabajando en ESTE mismo
> worktree y rama cuando se escribió esto. Puede haber commits encima de
> 202ece9: mirar `git log` antes de creerle a esta tabla.

### a. Todo en una pantalla

| Qué | Estado | Evidencia |
|---|---|---|
| Paso 0: cosecha de cuadros VOLCAT | Terminado | a2d1dca; 989 archivos, 111,7 MB, 0 errores, sha256 en `data/raw/volcat_validacion/manifiesto.json` (gitignored, sólo en este worktree) |
| Paso 1: lectura por bloques + objeto anclado | Terminado | e05b722; `src/process/volcat_colorbar.py::volcat_object_heights`, `tests/test_volcat_colorbar.py` (15 pruebas, mutaciones atrapadas) |
| Paso 2: coordenadas GVP + fix de unidades | Terminado | 202ece9; `src/volcanos_validacion.py`, `tests/test_volcanos_validacion.py`, fix `SCALE_FACTOR` en `src/fetch/volcat_api.py` |
| Suite completa | Verde | 566 passed, 1 skipped (~4,5 min), corrida tras 202ece9 |
| Pasos 3 a 6 (métodos propios vs VOLCAT) | Corriendo en otra sesión | local_f702bfa8, misma rama |
| PR 38 (esta rama) | Abierto, sin merge | apilado sobre PR 36; título aún dice "paso 0 y 1" |
| PR 36 (base de esta rama) | Abierto, sin merge | `claude/volcat-propio-continuar-79dff8` -> main |
| Remoto | Al día | `git ls-remote` = `git rev-parse HEAD` = 202ece9 al escribir esto |

Plan vivo con todo lo medido: `docs/own_volcat/PLAN_VALIDACION_MAGNITUD.md` (§2, §3.1, §3.2).

### b. Decisiones que esperan a Nicolás

| # | Pregunta | Opciones | Recomendación |
|---|---|---|---|
| 1 | Criterio de "consistente" para el paso 5 (decidir ANTES de ver números) | (a) el intervalo VOLCAT se cruza con nuestra banda β; (b) diferencia de centros ≤ 1 km; (c) ≤ 2 km | (a): VOLCAT entrega un bloque de 1 a 2 km, no un número; exigirle más precisión al centro sería inventar resolución |
| 2 | Orden de merge de PR 36, 38 y 39 | 36 -> 38 -> 39, o 39 primero | 36 y 38 primero (38 es pila de 36); al rebasar 39 conservar sus `submuestrear`/`paso_min` y la ficha §B.9 de ambos lados |

### c. Lo aprendido

- **Regla general del workspace**: antes de interpretar una unidad de un
  producto externo, leer la memoria de referencia del proyecto. La memoria
  `reference_volcat_sectors.md` YA decía que `SCALE_FACTOR` de SSEC (proyección
  CE) va en segundos de arco; igual se programó como km y el radio de anclaje
  quedó en 1 píxel. Una prueba sintética escrita con la misma suposición dio
  verde falso: **las georef de prueba se copian del listado real**, no se
  inventan. (Destino: patrón ya anotado en memoria; propuesto para
  `CLAUDE.md` del proyecto, sección Patrones de código.)
- La barra de VOLCAT Ash_Height es **discreta**: 1 km por bloque hasta 10, luego
  2 km hasta 18; 18 a 20 es negro e ilegible. Leerla como gradiente lineal
  sobrelee hasta 10 % (el azul de 10-12 se leía 12,2).
- En sectores de 2 km el color se mezcla con el gris IR: rojo y salmón (1-2 y
  2-3 km) no se separan; un tope VOLCAT de 1 a 3 km en sector regional es
  ambiguo por construcción.
- El sitio volcano.si.edu responde 403 a bots; el WFS del GVP sí responde.

### d. Problemas abiertos e hipótesis

| Problema | Etiqueta |
|---|---|
| Reventador ancla en sólo 3 a 9 de ~35 cuadros por evento | CONFIRMADO (medido); causa SOSPECHA: pluma desprendida, radio de 10 km corto |
| Cotopaxi 25-10 y Sabancaya 26-10 dan topes de 12 a 18 km | CONFIRMADO (medido); que sean nubes meteorológicas y no ceniza: SOSPECHA, falta mirarlo a ojo |
| Chillán 08-11: tope firme 3-4 km en 13 de 64 cuadros; pulso de 5-6 km sólo en 1-2 px | CONFIRMADO |
| `used_sat` sin usar en `volcat_api.py:276` | CONFIRMADO, viene de main, no se tocó |

### e. Cerrado, no rehacer

- El "tope bajo el cráter" de Chillán 08-11 era artefacto de la lectura vieja,
  no física.
- La afirmación anterior del plan de que el azul se "sublee" era falsa (era
  sobrelectura) y ya se corrigió en el plan.
- Los mantos sinópticos del 16-11 (Sabancaya/Ubinas/Copahue) se rechazan con la
  regla de > 5 % del mapa.
- Los sectores PS (Chile_South) se omiten en `volcat_height_at` con nota; no
  hay que adaptar la conversión a km para ellos.

### f. Prompt para la próxima sesión

```
Proyecto Goes, worktree C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\Goes\.claude\worktrees\volcat-propio-continuar-79dff8,
rama claude/validacion-magnitud-volcat (PR 38, apilado sobre PR 36).
1. Verifica antes de creer: git status -sb; git log --oneline 202ece9..HEAD (puede haber
   commits de la sesión de pasos 3 a 6); git ls-remote origin -h refs/heads/claude/validacion-magnitud-volcat.
2. Lee en orden: CLAUDE.md, STATUS.md §0, docs/own_volcat/PLAN_VALIDACION_MAGNITUD.md, y la nota
   C:\Users\nmend\AppData\Local\Claude-Data\claude_pzs8sxrjxfjjc\side-session-notes\local_514630c7-d36d-4bb5-b6c3-8a142112495e\validacion_magnitud_traspaso_2026-11-16.md
3. Si la sesión de pasos 3 a 6 ya terminó, revisa lo que dejó (diff, pruebas) antes de seguir; si no, no
   edites los mismos archivos.
4. Trabajo pendiente en orden: mirar a ojo Reventador/Cotopaxi y los topes 12-18 km; pedir a Nicolás el
   criterio de consistencia ANTES de ver números; BT-matching, Wen-Rose y ACHA en pocos scans (Sabancaya
   01-11 y 28-10, Chillán 08-11) con GFS archivado; scripts/validate_magnitud.py + tabla en
   docs/paper/REGISTRO_PAPER.md §3.
Reglas duras: TDD; ficha SDA (docs/FICHA_SDA_GOES.md) en el mismo commit que la lógica; sin merge ni deploy;
no tocar replay_reciente.py, replay_dia.py, historic_rammb.py ni docs/auditoria_2026-11; sin VIIRS; no
inventar valores físicos; sin guiones largos; rutas absolutas.
Si no alcanza: deja el avance commiteado y un bloque nuevo arriba en STATUS.md con /cierre.
```

---

## Qué corre de verdad (workflows, ago-2026)

| Workflow | Disparo declarado | Qué produce |
|---|---|---|
| `frp_timeline.yml` | cron `*/10 * * * *` | `data/frp_timeline.json` — pulso intradía de FRP + roll-up diario del Heatmap. **Fuente única** de hot spots agregados. |
| `hires_visible_cache.yml` | cron `*/10` (+ `:22` horario, modo `mono_05km`) | Cache rodante GeoColor hi-res 0.5 km/px (release `hires-loop-rolling`). |
| `animation_cache.yml` | cron `7 * * * *` | Cache de frames RAMMB para Replay / Loops. |
| `keepalive_hf.yml` | cron `23 */6 * * *` | Ping al Space para que no duerma. |
| `tests.yml` | push a `main` + PR | Suite pytest (Python 3.12) + smoke import del dashboard. |
| `backfill_build.yml` | manual | Reconstrucción de un evento histórico desde L1b. |
| `hires_loop_backfill.yml` | manual (pesado, GB de L1b) | Recuperación de loops hi-res hacia atrás. |
| `goes.yml` | **manual** (cron OFF desde 2026-05-15) | `STATUS_NRT.md`. Sin consumidor. |
| `lascar_pdf.yml` | **manual** (cron OFF desde 2026-05-10) | PDF diario Láscar en `reports/lascar/`. Sin consumidor validado. |

> **Ojo con las cadencias**: los crons de arriba son lo *declarado*. GitHub
> Actions estrangula los `schedule` de repos públicos: entre el 29 y el 30 de
> agosto, los tres crons de 10 min entregaron en la práctica **una corrida cada
> ~2 h**. Los datos siguen siendo auto-sanantes (cada corrida barre 3 h hacia
> atrás), pero no prometer "cada 10 minutos" a un turno.

---

## Estado del sistema

- **11 vistas activas** con permalink `?vista=<slug>` (lista en
  `dashboard/app.py`, `PAGE_OPTIONS`/`PAGE_SLUGS`; documentadas en
  `docs/GUIA_REVISION_DASHBOARD.md`).
- **Altura de tope propia** operativa por 3 métodos (BT-matching, Wen-Rose,
  ACHA) + árbitro CO₂ y β-ratios. Etiquetada **INDICATIVA**, apagada por
  defecto, disparada por hot spot FDCF o por botón del operador.
- **SDA declarado** bajo Resolución CPLT N°372 — ficha en
  `docs/FICHA_SDA_GOES.md`, obligatoria de actualizar en el mismo commit que
  cambie la lógica.
- **Licencia Apache-2.0**. Registro pre-paper en `docs/paper/REGISTRO_PAPER.md`.
- **Tests**: la suite corre en CI en cada push a `main` (ver `tests.yml`).

---

## Pendiente

1. **Validar la cizalla de viento (Fase 3c)** contra un evento real antes de
   cablearla como 4º método de altura. Hoy `src/process/wind_shear_height.py`
   existe con tests, pero **no está conectado a ninguna vista**.
2. **Parallax**: `src/process/parallax.py` corrige la georef de la pluma por su
   altura, tiene tests, y tampoco está cableado a producción. Decidir si entra o
   se archiva.
3. **GFS de archivo** para reanálisis histórico (hoy sólo perfil NRT vía
   Open-Meteo → el backfill de eventos viejos no tiene T(z) coetáneo).
4. **Sectores VOLCAT** de Chillán y Villarrica: pedido a SSEC pendiente de
   enviar (`docs/EMAIL_SSEC_sectores_chillan_villarrica.md`), junto con el
   acceso al dato gridded/NetCDF (hoy consumimos el render PNG).
5. **Integración con VRP Chile / Lightning-v1** — se trabaja desde
   `Volcanologia/Integracion_Plataformas/propuestas/goes_lightning/`.

---

## Comandos útiles

```bash
cd "C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\Goes"

python -m pytest tests/ -q          # suite completa
streamlit run dashboard/app.py      # dashboard local
gh run list --limit 20              # qué corrió de verdad en Actions
bash scripts/deploy_hf.sh           # deploy a Hugging Face Spaces
```

---

## Notas operacionales

- **Datos persistentes**: `data/raw/` y `data/processed/` están gitignored. Los
  caches de loops viven en GitHub Releases rodantes, no en el repo.
- **Catálogo de volcanes**: `src/volcanos.py` — 43 volcanes RNVV, 8 prioritarios.
- **Convenciones**: Kelvin para BT, WGS84 lat/lon, UTC. Coeficientes Planck
  siempre del NetCDF L1b (`planck_fk1/fk2/bc1/bc2`).
- **Sync de docs**: al cambiar un punto de integración, editar `INTEGRATION.md`
  (actualizar `last_updated`) y correr `python scripts/sync.py` desde
  `Volcanologia/Integracion_Plataformas/`. No es bloqueante.
