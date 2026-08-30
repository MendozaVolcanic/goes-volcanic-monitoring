# AUDIT REPORT — 30 agosto 2026 (4ª auditoría)

> **Qué la distingue de las tres anteriores:** además del análisis estático multi-agente,
> esta vuelta **se levantó el dashboard y se lo usó**, y varios hallazgos se verificaron
> **también contra el deploy de producción** en Hugging Face. Tres de los cuatro bugs de
> la §1 son invisibles leyendo el código: aparecen sólo cuando el navegador dibuja.
>
> **Método**: 6 finders paralelos con lentes distintas (cobertura primero, filtrado
> aguas abajo) + verificación adversarial con mandato de refutar, sobre la metodología
> de `feedback_auditoria_multiagente`. Los ejes de brecha operacional (A–K) salen del
> `PROMPT_CAZA_DE_BRECHAS` del workspace.
>
> **Resultado**: 119 hallazgos de los finders (31 high · 55 medium · 33 low) + 5 propios
> de la prueba en vivo, contra 69 verificaciones que dieron limpio.
> Detalle completo en [`AUDIT_2026-08-30_ANEXO.md`](AUDIT_2026-08-30_ANEXO.md).
>
> Alcance: 23.6k LOC, 11 vistas, 312 tests. Estado previo en `AUDIT_REPORT_2026-08.md`.

---

## §1 · Lo que apareció al USAR la app (no al leerla)

### 1.1 — El mapa de Chile de la vista principal está roto en producción

**`dashboard/views/live_viewer.py:1021-1027` · high · CONFIRMADO en producción**

La Vista Operacional → Nacional es la pantalla de aterrizaje del dashboard. En el deploy
real (`mendozavolcanic-goes-volcanic-monitoring.hf.space`, build `20260807-1015-a6ac7e1`)
el mapa **no se ve**: el plot aparece vacío, con los ejes rotulados "Latitud/Longitud"
yendo de −3000 a 3000 y los 43 volcanes aplastados en una línea sobre el origen.

Lo que pasa, medido en el navegador:

| | rango que pide el código | rango efectivo | veredicto |
|---|---|---|---|
| Ventana angosta / primer render | lon −79…−64 (15°) | −415…272 (688°) | mapa invisible |
| Ventana 1920 px | lon −79…−64 (15°) | −112.6…−30.4 (82°) | imagen comprimida 5.5×, ~70% negro |

La causa **no** es el dato: la imagen (`x=-79, sizex=15`) y las trazas (volcanes en
−67.7, −23.4; borde de Chile en −73.2, −54.1) están en grados correctos. Es que el eje `y`
lleva `scaleanchor="x"` **sin `constrain`**, y el default de Plotly en ese caso es
`constrain="range"`: para respetar la razón de aspecto, Plotly **ensancha el rango** e
ignora el `range=[...]` explícito que el código pide con `autorange=False`. Cuando
Streamlit dibuja el plot su contenedor mide 16 px de ancho, así que la expansión es brutal
— y **no se recupera** cuando el contenedor crece a 810 px: el rango queda congelado.
Se comprobó pidiéndole a Plotly `xaxis.constrain='domain'` en vivo: el rango vuelve
inmediatamente a −79…−64 y Chile aparece.

Lo notable es que **el repo ya sabe esto**. `zonas_fullscreen.py:167-173` lo documenta
con fecha (2026-06-08) y lo resuelve:

> `constrain="domain"`: CLAVE para llenar el espacio. Con scaleanchor (aspecto bloqueado)
> + un contenedor de otra proporción, el solver de Plotly por default ENCOGE el área de
> datos y la centra […] Con `constrain="domain"` Plotly llena el 100% de la dimensión mayor.

El fix se aplicó en **2 de 13** archivos con `scaleanchor` (`zonas_fullscreen`, `volcat_viewer`
— y son justamente los que en la prueba se vieron perfectos). Los otros 11 quedaron sin él.
Es el patrón recurrente que la memoria del proyecto ya tiene fichado: *un fix aplicado a un
solo call-site cuando el patrón estaba copiado en varios*.

**Matiz importante, verificado:** el daño es proporcional al desajuste entre el aspecto de
la escena y el del contenedor. Chile completo (15° × 43°, casi 1:3) en un contenedor ancho
es el peor caso y queda roto de forma **persistente**. En los paneles cuadrados del Modo
Evento medí una expansión de 16× durante la carga, pero **al asentarse volvieron a 1.0**:
ahí es transitorio, no un bug. No conviene reportarlos juntos.

*Fix:* agregar `constrain="domain"` a los dos ejes en los 11 archivos; empezar por
`live_viewer.py:1021-1027` (Nacional) y `live_viewer.py:263` (`_make_fig`, compartido).

---

### 1.2 — El semáforo de frescura del Modo Guardia nunca funcionó

**`dashboard/views/zonas_fullscreen.py:1639` · high · CONFIRMADO en vivo, causa raíz exacta**

En Modo Guardia → Vigilancia diaria (la landing de la vista de sala), el banner de estado
dice **"Sin scan disponible"** en gris, de forma permanente, mientras las cuatro zonas
muestran imágenes fechadas 07:30 UTC. Persiste tras cambiar de sub-tab y tras recargar.

Instrumentando la función en vivo salió el motivo:

```
UnboundLocalError: cannot access local variable 'parse_rammb_ts'
                   where it is not associated with a value
```

`_render_4_zonas_inner` usa `parse_rammb_ts` en la línea 1639, pero **más abajo, en la
1712, la re-importa localmente** (`from dashboard.utils import fmt_chile, parse_rammb_ts`).
Python decide el ámbito en tiempo de compilación: ese import local convierte el nombre en
variable local **de toda la función**, así que el uso previo no ve el import global de la
línea 29 y revienta. El `except Exception` de la línea 1640 se traga el `UnboundLocalError`
y lo convierte en `age_min = -1`, que la línea 1645 renderiza como "Sin scan disponible".

Es un barrido AST del repo entero: **este es el único caso**, pero está en la vista de sala.

Por qué importa más de lo que parece: ese banner es el **único** indicador de edad de esa
vista, y está muerto en la única dirección que importa. No puede ponerse rojo. Si RAMMB se
atrasa tres horas, la sala seguirá viendo un gris neutro idéntico al de ahora. Es
exactamente el modo de falla que este proyecto declara como el peor —*dato viejo
presentado como todo tranquilo*— y encima disfrazado: un error de programación se
presenta al operador como un estado del dato.

*Fix:* borrar el import redundante de la línea 1712 (el global ya está). Y como regla,
no capturar `Exception` alrededor de un parseo: capturar `ValueError`, para que un bug de
código falle ruidosamente en vez de disfrazarse de "sin dato".

---

### 1.3 — Una API de Streamlit vencida en producción

**`dashboard/style.py:482`, `live_viewer.py:584`, `modo_guardia.py:395` · medium**

El server escupe en cada carga:

> `Please replace st.components.v1.html with st.iframe.`
> `st.components.v1.html will be removed after 2026-06-01.`

La fecha de remoción **ya pasó hace casi tres meses**. Corre con Streamlit 1.56.0; la
próxima actualización del runtime de HF Spaces puede llevarse los tres call-sites por
delante — uno de ellos es el helper de navegación del Modo Guardia.

---

### 1.4 — Dos literales de UI que envejecieron

**medium** — Mismo patrón que el rótulo "(3 productos)" corregido hoy:

- `ROTATION_SECONDS = 15` en `zonas_fullscreen.py:46` y `modo_guardia.py:50`, pero
  **cuatro textos** prometen "cada 10s": `modo_guardia.py:428`, `:447`, `:462` y
  `manuals.py:81`. El botón de Modo Sala dice 10 s y rota cada 15. (Sólo
  `mosaico_chile.py` tiene 10 de verdad, así que no es un simple find-and-replace.)
- `dashboard/app.py:201`: el widget `nav_page` se crea con `index=` **y** se le escribe
  el valor por Session State. Streamlit lo advierte en cada arranque; es el antipatrón
  que produce que el sidebar y la URL discrepen tras un rerun.

---

### 1.5 — Confirmación visual del negativo silencioso

En Modo Evento con Villarrica, el KPI **"HOT SPOTS NOAA ≤50 KM"** muestra **`0` en verde**
mientras el panel de al lado dice "GFS no respondió". Cuatro finders independientes
llegaron por caminos distintos al mismo sitio (§2.1). Verlo en pantalla cierra el caso.

---

## ✅ Estado de implementación — 30 agosto 2026 (misma sesión)

Se implementaron las olas A, B, D y E completas, y la parte de C que no cambia
números del paper. **Todo verificado en la app corriendo, no sólo con tests.**

| Ola | Ítem | Estado |
|---|---|---|
| A1 | `constrain="domain"` en los ejes con `scaleanchor` | ✅ **12 sitios en 12 archivos** (los 11 del audit + uno más que apareció en `volcat_viewer.py:216`). Verificado en vivo: la vista Nacional pasó de un rango de 82° a los **15° exactos** que pide el código. |
| A2 | Import redundante de `parse_rammb_ts` | ✅ Borrado. El banner pasó de "Sin scan disponible" permanente a **"Scan hace 21 min · RAMMB lento"** en ámbar. Barrido AST del repo: no queda ningún otro `UnboundLocalError` latente. |
| A3 | `PyYAML` en requirements | ✅ `test_workflow_concurrency` corre: **7 passed** (antes se auto-salteaba). |
| A4 | Manual de SO₂ | ✅ Corregido con la física explícita (absorción a 8.6 µm → sube el verde). |
| B1 | Ausencia de dato ≠ ausencia de fenómeno | ✅ Contrato explícito en `goes_fdcf` + helper único `estado_hotspots`/`hotspots_verificados` en `map_helpers.py`, aplicado a **los 5 consumidores**. El fallo ya **no se cachea** (una función `@st.cache_data` que lanza no guarda resultado). Verificado en vivo: el KPI muestra `0 · sin detecciones · scan hace 27 min`. |
| B2 | Criterio de frescura único | ✅ Centralizado en `map_helpers.estado_hotspots`. |
| C | Honestidad del retrieval | ✅ Piso de terreno (`below_summit`, **marca — no clampea**), `profile_gap_min` pintado en la tira de altura, y los dos riesgos latentes refutados documentados en el código. |
| D | Ficha SDA y docs | ✅ Ficha **v2.0**: saca los componentes no cableados, agrega el indicador SO₂ y el filtro de hot spots, y declara los 7 límites (incluido el uso aeronáutico excluido). `STATUS.md` y la guía de turno actualizadas. |
| E | Falsos verdes | ✅ Los seis corregidos y **validados por mutación**. Suite: **~357 tests** verdes (antes 312). |

### Lo que NO se hizo, y por qué

- **El guard de opacidad de los β-ratios (§3.1) queda pendiente a propósito.** Es
  el único hallazgo científico que sobrevivió a la verificación, pero cambiar el
  umbral de clasificación **cambia números que van al paper**, y la verificación
  además descubrió que el disparador dominante es β(8.5,11) y no β(12,11) — o
  sea que el fix correcto no es el que decía el hallazgo original. Eso se decide
  con criterio volcanológico, no de programación.
- Los otros dos hallazgos de física **no se tocaron porque fueron refutados**:
  quedaron documentados en el código como riesgo latente para el día que se
  cablee otro proveedor de perfil.

### Nota de proceso

Un test escrito por un agente y un renombre hecho por otro **colisionaron**: el
test exigía que el disparo de la altura dependiera de `_hotspots_volcan`, y el
wrapper nuevo se llama `_hotspots_volcan_seguro`. El test se puso rojo, que es
exactamente lo que tenía que pasar. Se corrigió comparando por **prefijo** en vez
de por igualdad —lo que se vigila es que el disparo dependa del hot spot, no de
qué puerta se use— y se **revalidó por mutación** que sigue matando los tres
mutantes originales.

---

## §2 · Los cinco patrones que explican casi todo

Los 119 hallazgos no son 119 problemas. Se agrupan en cinco familias, y las familias
importan más que los ítems sueltos: **arreglar la familia previene los que todavía no
aparecieron.**

### 2.1 — El silencio se pinta de verde (la familia más grande)

Cuatro finders con lentes distintas —fetchers, estado, tests y usuario— cayeron
independientemente sobre lo mismo, que es la señal más fuerte de toda la auditoría:

`src/fetch/goes_fdcf.py:348-350` devuelve `([], None)` **tanto si el scan no tenía hot
spots como si S3 falló**. Los cuatro consumidores tratan ese resultado como "no hay
anomalía térmica":

| Vista | Línea | Cómo lo pinta |
|---|---|---|
| Modo Guardia (KPI) | `modo_guardia.py:249` | `0` en **verde** (`#44dd88`) |
| Modo Evento (crisis) | `modo_evento.py:266` | `0` en **verde** |
| Modo Sala (pared) | `zonas_fullscreen.py:79` | sin hot spots dibujados |
| Grilla de volcán | `modo_guardia_volcan.py:976` | sin hot spots dibujados |

Los cuatro **reciben el `scan_dt`** que permitiría distinguir los dos casos, y los cuatro
lo descartan. Peor: el resultado de fallo **se cachea 5 minutos** (`@st.cache_data(ttl=300)`),
así que un blip de 2 segundos de AWS congela "sin hot spots" en la pared de la sala
durante cinco minutos y se saltea el scan siguiente.

La misma forma reaparece en toda la app: `_hotspots_volcan` y `_hotspots_zone` convierten
cualquier excepción en cero; la tira de altura presenta cualquier fallo de adquisición
como "Es el estado esperado sin pluma activa" (`modo_guardia_volcan.py:903`) ignorando el
campo `reason` **que la vista hermana sí lee** (`volcat_viewer.py:877`); y el panorama
semanal del Heatmap afirma "✅ Calma operacional" sin el guard de frescura que existe 90
líneas más arriba en el mismo archivo (`heatmap_actividad.py:321`).

**El principio que falta, y es uno solo:** *ausencia de dato y ausencia de fenómeno son
estados distintos y tienen que verse distintos.* Hoy los dos se ven como calma. En un
sistema cuyo propósito es avisar, ese es el error que no se puede permitir; y nótese que
el proyecto ya tiene la disciplina en otro lado (el banner de latencia de la Vista
Operacional funciona muy bien, y `volcat_viewer` sí lee el `reason`). No es un problema
de criterio: es un principio aplicado en unos lugares y no en otros.

### 2.2 — Los guards de frescura existen, pero desparejos

El proyecto entiende el problema —de las tres auditorías previas salieron varios guards—
pero la cobertura tiene agujeros y **casi todos caen del lado inseguro**:

- El banner del Modo Guardia está roto de fábrica (§1.2).
- El semanal del Heatmap no aplica el guard que el intradía sí tiene.
- El Modo Sala proyecta el último PNG bueno indefinidamente, y mide su badge con **otro
  reloj** (el de RAMMB, que sigue vivo aunque el productor de imágenes muera).
- El GeoColor hi-res del Mosaico no muestra su hora ni tiene guard de edad, bajo un
  encabezado que anuncia el scan fresco de RAMMB.
- VOLCAT —el número cuantitativo de referencia del proyecto— se muestra **sin edad ni
  fecha** en el KPI y sin umbral de frescura.
- El manifest hi-res sella el timestamp **pedido**, no el del gránulo bajado, así que el
  guard de 90 minutos puede mentir hasta ~70.

### 2.3 — Los tests de análisis estático siguen dando falsos verdes

Es el problema conocido del repo y **no está contenido**. Seis casos nuevos, todos
confirmados corriendo la mutación:

- El grid puede **dejar de dibujar VOLCAT** —el único producto con altura cuantitativa— y
  los tres asserts de `test_la_grilla_recorre_los_paneles_declarados` los satisface el
  **docstring** de la función: 120 tests en verde.
- El guard del DirCache eterno declara cubrir "los 6 fetchers S3" y sólo mira `goes_s3`:
  darle a `goes_fdcf` un filesystem propio (que reintroduce scans de hasta 1 h presentados
  como vigentes) deja **15 passed**.
- Los dos tests del disparo de la altura son substrings que sobreviven a `auto = False` y
  a cambiar un `or` por un `and`.

Y el hueco de cobertura más caro: **nadie testea `scripts/build_frp_timeline.py`**, que
escribe `last_updated_utc = now` aunque no haya bajado un solo scan. El guard de frescura
del Heatmap lee exactamente ese campo. Con FDCF caído, el turno lee "Calma térmica" con
timestamp fresco durante 48 h — el modo de falla peor del sistema, servido por su propio
guard.

### 2.4 — La documentación describe otro sistema

El drift no es cosmético cuando la doc es el procedimiento de turno:

- `STATUS.md` (declarado "curado por humanos") lleva **4 meses** congelado, da como
  producción una URL muerta de Streamlit Cloud, y afirma que un bot escribe `STATUS_NRT.md`
  cada 10 min — el cron está apagado desde mayo y el archivo no existe.
- `docs/GUIA_REVISION_DASHBOARD.md`, **la que lee el geólogo de guardia**, nombra 4 vistas
  renombradas o eliminadas y no documenta 5 de las 11 activas, incluidas Modo Guardia y
  Modo Evento — las dos vistas de sala.
- El manual y la leyenda de la misma pantalla se contradicen sobre qué color es SO₂ y cuál
  ceniza en `jma_so2`.
- La vista Series promete "Hot spots NOAA FDCF + FRP" y no entrega ni un dato FDCF.

### 2.5 — La ficha SDA no describe el sistema que corre

Bajo Resolución CPLT N°372 esto no es documentación interna: es el instrumento de
transparencia del sistema.

- `docs/FICHA_SDA_GOES.md` declara `wind_shear_height.py` y `parallax.py` como componentes
  **y ninguno de los dos está cableado a producción**: la ficha describe capacidades que
  el sistema no tiene.
- Sigue en `v1.0 — 2026-07-01` pese a tres ediciones de lógica en agosto, incluido el
  disparo automático del retrieval de altura.
- Dos piezas que **sí clasifican** —el indicador SO₂ (`ash_rgb.py:105`) y el filtro de hot
  spots (`goes_fdcf.py:66`)— no llevan cabecera FICHA ni figuran en la ficha. Ningún test
  verifica esa cobertura, así que el drift es silencioso por construcción.
- Y del lado del usuario: **la app desplegada no dice en ninguna parte que es un SDA**, ni
  linkea la ficha, ni la guía del operador, ni declara sus límites.

---

## §3 · Crítica científica

Esta sección es la que más pesa para el paper. El núcleo se auditó ejecutando el
forward-model con las fixtures del repo, no leyéndolo.

**Lo que está limpio y conviene decirlo:** la conversión de Planck (coeficientes siempre
del NetCDF L1b), la proyección geoestacionaria contra el PUG, la magnitud y el signo del
parallax, y la rama monótona del perfil GFS se verificaron numéricamente **sin
hallazgos**. Ese es el mismo resultado que dio la 2ª auditoría y es un activo real de cara
a publicar.

Los tres problemas de fondo comparten una forma: **el retrieval no distingue "no pude
resolver" de "resolví, y da esto".** Es la §2.1 otra vez, un nivel más abajo.

### 3.1 — La ceniza opaca se clasifica como hielo  ·  **CONFIRMADO, y más ancho**

`src/process/beta_ratios.py:280`

Cuando la pluma es **ópticamente gruesa** —cerca del cráter, temprano en la erupción, o
sea el caso peligroso— la emisividad satura y β→1, que es la firma del hielo. Reproducido
con los coeficientes Planck reales: con `t11=0.001`, β(12,11)=0.896 → etiqueta `hielo`,
`is_ash=False`. Y esa etiqueta es la que dispara en el panel el aviso de *posible falso
positivo de ceniza*.

El resultado operativo es una **asimetría de consecuencias invertida**: el sistema le dice
al operador "desconfiá de esto" justo cuando la detección es más real. Los β-ratios de
Pavolonis discriminan composición en el régimen semitransparente; usarlos fuera de él sin
un guard de opacidad les pide algo que no pueden dar.

El verificador intentó refutarlo por tres vías y las tres fallaron: la máscara de ceniza
**no** excluye el píxel opaco (con Ts=292 K y Tc=228 K, el BTD todavía vale −1.78 K y pasa
el umbral de −1 K), no hay gate aguas abajo (`wen_rose_height.py:604-607` mira sólo
`is_ash`), y el flag **se le muestra al operador en ámbar** (`volcat_viewer.py:989-993`).
Lo reprodujo end-to-end sobre la escena de `conftest`.

**Y lo agrandó:** el disparador dominante no es β(12,11) sino **β(8.5,11)**. Como el test
tri-espectral exige que 8.4 µm esté más frío que 11.2 µm, *todo* píxel que entra por la
máscara tiene β₈₅ > 1, así que el flag de "no silicato" salta **incluso con plumas
semitransparentes bien modeladas** — no sólo con las opacas. El caso reportado
originalmente es un subconjunto del problema real.

### 3.2 — Sin tropopausa el guard se apaga  ·  **REFUTADO**

Reportado como high: si `_tropopause` devuelve `None`, el guard de runaway se desactiva y
`Tc = 180 K` (piso de la grilla) sale como `reliable=True`.

El verificador **reprodujo el mecanismo en código** (forzando `tropopause=None`: top 5.6 km,
confianza "media", cero flags) **pero demostró que el estado no es alcanzable**. El único
proveedor cableado es Open-Meteo (`scene.py:320`); consultó la API real para Láscar —72 h ×
19 niveles— y encontró **0 nulls** en T y Z, incluidos los nueve niveles 400–70 hPa que
harían falta para que `trop` quedara en `None`. El modo de falla realista es la caída total
del perfil, y **ya está cubierto** (`len < 3` → None → "sin perfil GFS").

Queda como **riesgo latente documentado**, no como bug: si alguna vez se cablea LVTP o GRIB
como proveedor alternativo, este guard hay que revisarlo antes.

### 3.3 — `well_constrained` no mide la calidad del ajuste  ·  **REFUTADO**

Reportado como high: `solve_tc_grid` sólo mide el ancho del mínimo, no el residual, así que
un ajuste malo de mínimo angosto pasa como bien condicionado.

El verificador reprodujo la saturación en `Tc = 180 K` con `well_constrained=True`, **pero
encontró el guard que lo neutraliza**: `_revert_unreliable` (`:350-366`) la anula en los
cuatro casos —la altura clampa en la tropopausa, `reliable` pasa a `False` y el resultado
vuelve a la cota inferior—. Hizo además un barrido de β_true 0.45–1.00 × t11 0.15–0.9:
**ningún caso produce un tope alto espurio marcado como confiable**, y con β > 0.7 el método
subestima, que es el lado conservador. `well_constrained` tampoco sale del módulo.

Es la misma clase de refutación que en la auditoría anterior salvó al bloqueo serial de las
zonas VOLCAT: el hallazgo era cierto **en la función** y falso **en el sistema**.

### 3.4 — Tres cosas que el retrieval sabe y no le dice al operador

Menores en código, importantes en interpretación:

- **Sin piso de terreno** en `altitudes_from_bt`: Láscar puede reportar topes **4 km bajo
  su propio cráter**. `Volcano.elevation` existe en el catálogo y no se usa nunca.
- El **`time_gap_min` del perfil GFS** se mide y se descarta antes de llegar a la
  pantalla: el operador no sabe si el perfil es de hace 20 minutos o de hace 5 horas.
- `solar_elevation` no aplica ecuación del tiempo: error medido de hasta **4.0°**, no los
  0.5° que declara, y gobierna el switch día/noche con umbral de 5°.

### 3.5 — Y el que el proyecto ya sabe

El sesgo conocido de −0.4 a −0.8 km de los retrievals IR está bien documentado en la guía
de turno. Pero se documenta **en la guía**, no en la pantalla donde aparece el número.

---

## §4 · Crítica de usuario: la pregunta para la que el dashboard está optimizado

Recorriendo los once ejes de brecha, el patrón que aparece una y otra vez no es un bug: es
una elección de diseño que quedó implícita.

**El dashboard contesta muy bien "¿qué se ve ahora?" y muy poco "¿esto está cambiando?".**
(eje B, *tarea equivocada*.) Casi todas las vistas son un instante: el último scan, los
cuatro productos, las cuatro zonas. Pero la pregunta del turno rara vez es qué se ve —es
si lo que se ve **es distinto de lo normal para ESE volcán**. Hoy la comparación con la
línea base la pone el operador de memoria. Las dos vistas temporales que existen (Series,
Heatmap) están fuera del camino de la crisis, y Series entrega el proxy de color que el
propio proyecto descalificó por sus falsos positivos con cirros y nieve.

De ahí se derivan las demás:

- **Eje D, escenario no contemplado.** Modo Evento —la pantalla de crisis— existe sólo
  para **8 de los 43 volcanes**, y un permalink a cualquier otro cae **en silencio a
  Villarrica**, con el header gigante mostrando el volcán equivocado. Un operador que
  llega por link compartido a las 3 AM mira el volcán que no es.
- **Eje E, supuesto no declarado.** La interfaz asume que el usuario sabe que un panel
  vacío puede ser cielo despejado, pluma inexistente, fuente caída o bug. VOLCAT vacío es
  el estado normal y está bien explicado; el resto de los vacíos, no.
- **Eje F, asimetría de consecuencias.** Todo el §2.1: el diseño se inclina
  sistemáticamente hacia el **falso silencio**, que es el error caro.
- **Eje H, contexto fuera del satélite.** El dashboard se presenta como autosuficiente. No
  hay un enlace, un recordatorio ni un campo hacia sismología, DOAS, cámaras, los REAV de
  SERNAGEOMIN ni los VAA del VAAC Buenos Aires. Para un producto cuyo output es "esto
  parece ceniza", no cruzar con la red terrestre es la brecha más barata de cerrar y de
  las más valiosas.
- **Eje K, la frontera.** Un SDA que no declara sus límites invita a usarlo fuera de
  ellos. Y acá hay un caso concreto y delicado: **el manual invita a usar la altura propia
  para alerta aeronáutica / flight levels**. El propio proyecto marca esa altura como
  INDICATIVA y la banda fiable como 3–12 km; la aviación es exactamente el uso que el
  sistema debería negarse explícitamente a cubrir.

**Lo que está muy bien resuelto** y conviene no romper: el banner de latencia de la Vista
Operacional (colores + minutos + "consultado hace 1 s") es el mejor indicador de frescura
del sistema y debería ser el molde de todos los demás; las 4 zonas del Modo Guardia se ven
excelentes y llenan la pantalla; los tres productos con su hora individual permiten notar
que SO₂ va un scan atrasado; y la disciplina de no inventar métricas de color está
sostenida en el código, no sólo en el README.

---

## §5 · Verificación adversarial

Siguiendo la metodología del proyecto, los hallazgos más consecuentes se pasaron a
verificadores independientes **con mandato explícito de refutarlos** ("ante duda genuina,
inclinate por REFUTED"). En auditorías anteriores esto mató varios falsos positivos y una
refutación llegó a revelar dónde estaba el problema real. Esta vez **cayeron dos de los
tres hallazgos de física** —los dos que se habían reportado como high— y varios de los
demás volvieron mejorados:

| Hallazgo | Veredicto | Qué agregó la verificación |
|---|---|---|
| Serie FRP con huecos permanentes | **CONFIRMED** | El verificador bajó el JSON del remote y contó él mismo: 156 de 287 scans en 47.7 h, con 5 huecos, el mayor de **9.67 h** persistente tras ~20 corridas. Aceptó que el throttling de GitHub explica la cadencia, pero eso no cambia el efecto: `build_frp_timeline.py:107-130` sólo mira 3 h hacia atrás, así que **nada más viejo se rellena nunca** y el comentario "auto-sanante" del YAML es falso. |
| `test_workflow_concurrency` no corre en CI | **CONFIRMED** | Probó la hipótesis de rescate (¿PyYAML entra transitivamente?) contra el log del run verde: **0 hits** de yaml en las 1040 líneas, incluido el `Successfully installed` de pip. Conteo duro: **312 tests local, 303 en CI**. Que PyYAML esté instalado en la máquina de Nicolás es justamente lo que enmascara el problema. |
| Permalink de Modo Evento cae a Villarrica | **CONFIRMED en vivo** | `?vista=evento&volcan=Planchon-Peteroa` pinta la pantalla completa de Villarrica —header, KPIs, 3 mapas— sin un solo aviso, y el selector no ofrece el volcán pedido, así que el operador no puede corregirlo. |
| Series promete FDCF/FRP | **CONFIRMED, y peor** | No son dos promesas sino **tres**: subtítulo, manual, y un badge que además inventa cadencia ("un GitHub Action agrega los conteos 1 vez al día a las 02:00 UTC", `style.py:596`) de un workflow que el propio `CLAUDE.md` declara reemplazado. |
| Manual vs leyenda en `jma_so2` | **CONFIRMED** | Contradicción dentro de la misma pantalla: el manual dice "plumas de SO2 en **magenta** brillante"; la leyenda canónica dice `#44dd66 = SO2` y `#dd4488 = Ash+SO2`. **La física respalda a la leyenda** (la absorción de SO₂ a 8.6 µm sube el verde) → lo que hay que corregir es el manual, que además se contradice a sí mismo dos viñetas antes. |
| Tira de altura traga el `reason` | **CONFIRMED** | Los retrievals sí distinguen `ok`/`no_plume`/`no_data`+`reason`; `_render_altura` sólo testea `== "ok"`. Agravante: la tira **se dispara con hot spot FDCF**, o sea justo cuando un "no hay nada" falso es más caro. |
| Ceniza opaca clasificada como hielo | **CONFIRMED, y más ancho** | Falló al refutarlo por tres vías, y descubrió que el disparador dominante es β(8.5,11), no β(12,11): el flag salta **también con plumas semitransparentes**, no sólo opacas. |
| Guard de runaway sin tropopausa | **REFUTED** | El mecanismo existe, pero el estado **no es alcanzable**: consultó la API real de Open-Meteo (72 h × 19 niveles) y no hay un solo null. Queda como riesgo latente si se cablea otro proveedor. |
| `well_constrained` sin tolerancia | **REFUTED** | `_revert_unreliable` neutraliza los 4 casos. Barrido β_true × t11 completo: **ningún tope alto espurio marcado como confiable**. Cierto en la función, falso en el sistema. |

**Un matiz que corrige a la baja un hallazgo, y vale registrarlo:** el verificador defendió
al pulso **intradía** del Heatmap, que sí tiene guard (`FRP_STALE_HOURS=3.0`) y dice
explícitamente que ausencia de señal no es calma. El problema está acotado al **semanal**
— y ahí encontró algo mejor que el reporte original: `daily_rollup` guarda sólo el
numerador (scans con detección) **sin el denominador de scans disponibles**, así que un día
con 60 de 144 scans es pixel a pixel idéntico a un día completo en calma. El caption de
`covered_days` tampoco salva, porque cuenta claves de día y el build crea la clave de hoy
aunque no haya barrido nada.

---

## §6 · Por dónde empezar

Ordenado por **impacto × frecuencia ÷ costo**, no por severidad nominal. Los primeros
cuatro son de una línea cada uno y arreglan cosas que hoy están rotas en producción.

### Ola A — una línea, impacto inmediato (hacer ya)

| # | Qué | Dónde | Por qué primero |
|---|---|---|---|
| A1 | `constrain="domain"` en ambos ejes | `live_viewer.py:1021-1027` | El mapa de la pantalla de aterrizaje se ve vacío **en producción**. Después propagarlo a los otros 10 archivos. |
| A2 | Borrar el import redundante de `parse_rammb_ts` | `zonas_fullscreen.py:1712` | Resucita el semáforo de frescura de la vista de sala, hoy muerto en la dirección que importa. |
| A3 | Declarar `PyYAML` en requirements | `requirements.txt` | Reactiva 7 tests que llevan meses salteándose en CI, incluido el guard de los releases rolling. |
| A4 | Corregir "magenta" → verde en el manual de `jma_so2` | `manuals.py:43` | El manual contradice a la leyenda **y a la física**, en la misma pantalla. |

### Ola B — el principio, no los síntomas (la que más previene)

**B1. Que la ausencia de dato se vea distinta de la ausencia de fenómeno.** Es una sola
decisión de diseño con muchos call-sites:

- `fetch_latest_hotspots` debe devolver un estado distinguible en el camino de error
  (una excepción propia, o un `status` explícito) en vez de `([], None)`.
- Los cuatro consumidores ya reciben el `scan_dt`: usarlo. Un `0` sin scan **no puede ser
  verde**; el estado correcto es gris con "no se pudo consultar".
- No cachear resultados de fallo (`ttl=300` sobre un error congela la pared 5 minutos).
- `_render_altura` debe leer el `reason` que ya existe, como hace `volcat_viewer.py:877`.
- El semanal del Heatmap necesita el guard del intradía **y** el denominador de scans en
  `daily_rollup`: sin él, "poco dato" y "calma" son el mismo píxel.

**B2. Un solo componente de frescura, reutilizado.** El banner de la Vista Operacional ya
es el diseño correcto (color + minutos + "consultado hace N"). Extraerlo y usarlo en
Modo Sala, Mosaico, VOLCAT y la grilla de volcán, en vez de seis implementaciones con
seis criterios.

### Ola C — científico (bloqueante para el paper)

C1. Guard de opacidad antes de clasificar con β-ratios: fuera del régimen semitransparente
el método no aplica, y hoy devuelve "hielo" justo en la pluma más peligrosa.
C2. ~~Tolerancia absoluta en `solve_tc_grid` y guard de tropopausa~~ — **los dos cayeron en
verificación**: `_revert_unreliable` ya cubre el primero y el segundo no es alcanzable con
Open-Meteo. Anotarlos como riesgo latente para el día que se cablee LVTP o GRIB, y seguir.
C3. Piso de terreno con `Volcano.elevation` en `altitudes_from_bt` — hoy Láscar puede
reportar un tope bajo su propio cráter.
C4. Propagar a la pantalla el `time_gap_min` del perfil GFS y el sesgo IR conocido de
−0.4/−0.8 km: hoy viven en la guía de turno, no donde aparece el número.

### Ola D — legal y documental (CPLT N°372)

D1. `FICHA_SDA_GOES.md`: sacar los dos componentes que declara y no están cableados,
agregar el indicador SO₂ y el filtro de hot spots, y subir la versión. Un test que compare
los módulos con cabecera FICHA contra la lista de la ficha evita que vuelva a derivar.
D2. Que la app **diga que es un SDA** y linkee ficha, guía y límites.
D3. `STATUS.md` y `GUIA_REVISION_DASHBOARD.md`: cuatro meses de atraso en el documento que
lee el turno.
D4. Declarar la frontera aeronáutica: el manual hoy invita a usar la altura propia para
flight levels, y el propio sistema la marca como indicativa.

### Ola E — la deuda de siempre

E1. Los seis falsos verdes nuevos (§2.3). **La regla operativa ya existe en la memoria del
proyecto y no se está cumpliendo**: todo test de análisis estático se valida mutando el
código de producción hasta verlo rojo. Si el aserto se satisface con un docstring, no
prueba nada.
E2. Tests para `build_frp_timeline.py` y para `rammb_slider.py` — el productor del dato del
Heatmap y el módulo que georreferencia **toda** imagen RAMMB, ambos sin un solo test.
E3. `st.components.v1.html` → `st.iframe` (fecha de remoción vencida).
E4. Los literales "cada 10s" contra `ROTATION_SECONDS = 15`.

---

## Nota de método

Vale registrar tres cosas para la próxima vuelta:

1. **Probar la app encontró lo que leer el código no.** Los dos bugs de la §1 son
   invisibles en revisión estática: uno vive en el solver de layout de Plotly y el otro
   estaba disfrazado de mensaje de estado. Ningún finder los reportó.
2. **Verificar contra producción cambia la severidad.** El bug del mapa podría haberse
   descartado como artefacto del entorno de prueba; abrir el HF Space lo convirtió en un
   hallazgo confirmado.
3. **La verificación adversarial se pagó sola otra vez.** Tumbó los dos hallazgos de
   física reportados como high —el mecanismo era real en la función y falso en el sistema,
   el mismo patrón que en la auditoría anterior salvó al bloqueo serial de las zonas
   VOLCAT—, acotó a la baja el guard del Heatmap intradía, y de paso **agrandó** el
   hallazgo de los β-ratios al encontrar que el disparador real era otro canal. Sin esta
   etapa, dos de las cuatro prioridades científicas habrían sido trabajo perdido.
