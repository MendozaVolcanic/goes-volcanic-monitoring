# STATUS — Goes Dashboard

**Última actualización:** 2026-11-23 (cierre de la sesión S19, bloque "## 0." abajo). Roadmap curado: 2026-08-30 (auditoría adversarial)
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

## 0. S19, cierre final 2026-11-23 (PR 100 a 105 en main; indicador nocturno desplegado a HF; H29 y "qué nos falta" CORRIENDO al cerrar)

> **Estado fijado con trabajo en curso:** dos sesiones hijas seguían trabajando, sin PR, al cerrar. Revisa
> `gh pr list` antes de creerle a esta tabla:
> - H29, la pluma del 08-11 lejos del cráter (`local_02c35abe`, rama `claude/charming-napier-13552c`): criterio y enmienda `52597bc` ya subidos, la medición estaba corriendo.
> - S19i "qué nos falta", en Fable 5.2 (`local_d641d4f9`, rama `claude/busy-robinson-07a98a`): cinco revisores por perspectiva, entrega `docs/own_volcat/QUE_NOS_FALTA_S19.md`.
>
> El detalle de H25 a H28 y de la revisión de H13 y H17 está en "## 0-prev13." (el bloque de S19 escrito antes de las fusiones).

### a. Todo en una pantalla

| Qué | Estado | Evidencia |
|---|---|---|
| PR 100 a 104 | **Fusionados** con el sí de Nicolás y `--match-head-commit`; el 103 con squash (las tablas transcritas de SSEC no entraron a la historia de main) | merges `b02d69c`, `7f26466`, `e7cd78e`, `70085fa`, `a5ab46f` |
| PR 105, indicador nocturno de calor en el cráter cableado (cabecera de la grilla de volcán, ficha SDA v2.10 §A.8) | **Fusionado y desplegado a HF** | merge `a1def2c`; Space en `4174fd6`, build `build-20261123-1532-a1def2c` |
| Verificación en la app desplegada (Modo Guardia, sub-tab Volcán) | Chillán: "Calor en el cráter sobre ~10 MW, 19 de 19 cuadros, máximo 38 MW", en rojo. Villarrica: "Sin calor sobre ~10 MW", en azul, no verde | capturas de Chrome del 23-11 a las 15:34 UTC |
| Workflow `calor_nocturno.yml` | Primera corrida manual en verde; commiteó la serie | run `45206521273`, commit `b1aa332` |
| Worktrees | Quitados 11, todos limpios y sin commits fuera de main (`git cherry`). Las carpetas de `s16-ef991e` y `s18-80ee17` quedaron en disco, bloqueadas por sesiones abiertas | `git worktree list` |
| H29 y S19i | **Corriendo, sin PR** | ver aviso arriba |
| main | `b1aa332` al cerrar | `git ls-remote` |

### b. Decisiones que esperan a Nicolás

| # | Pregunta | Recomendación |
|---|---|---|
| 1 | Fusionar los PR de H29 y de "qué nos falta" cuando lleguen | Revisarlos contra sus archivos antes, como se hizo con 101 a 104 |
| 2 | Borrar las 26 tablas transcritas de SSEC también de los commits viejos de la rama del PR 103 (pública) | Si la licencia te preocupa, hazlo tú: el force-push lo bloquea el modo automático. Para purgarlas del todo, soporte de GitHub |
| 3 | Paquete de Fuego, 16 GB en `D:\goes_notas\s16\modo_dia\` | **Mantenerlo**: su L2 (8 GB) y su diagnóstico (2,6 GB) son el único material para estudiar la puerta de nacimiento de VOLCAT. Si hace falta espacio, borrar sólo `l1_data` (0,9 GB) y `rtm_data` (0,7 GB) |
| 4 | Correo a Pavolonis | Nicolás lo excluyó el 23-11 ("todo menos el correo"); no proponerlo de nuevo sin que él lo traiga |
| 5 | Copiar `data/calor_nocturno.json` en `scripts/deploy_hf.sh` como respaldo local | Sí, en un cambio chico: hoy HF lo lee sólo de GitHub raw y, si eso falla, muestra sin dato |

### c. Lo aprendido

- **Desplegar desde un worktree** (propio del proyecto): `scripts/deploy_hf.sh` hace `git checkout main`, así que la rama
  local `main` tiene que estar al día con el remoto (`git branch -f main origin/main` si ningún worktree la tiene
  tomada). Al terminar, el worktree queda en `main`: vuélvelo a su rama.
- **Lanzar en Fable** (propio del entorno; ya en memoria `feedback_lanzar_sesion_fable.md`): `set_session_model`,
  `stop_session` y reenviar el encargo. Funcionó dos veces en S19.

### d. Problemas abiertos e hipótesis

- **CONFIRMADO:** no hemos visto lo mismo que VOLCAT en los pulsos de noviembre. Del 13 al 18-11 no hay firma en sus
  píxeles. De mañana, ni VOLCAT ni nosotros vemos los pulsos del OVDAS. De tarde no hay fondo para medir (H24 a H27).
- **SOSPECHA, sin probar:** la escala. Una pluma de ~1 km llena una fracción chica de un píxel de 2 a 3 km y diluye su
  firma. H29 mide su poder con fracción de píxel; S19i lo revisa desde la física y el instrumento.
- **Pregunta de Nicolás sin respuesta completa:** "encuentro extraño que no podamos ver que está sucediendo". La
  responde S19i.

### e. Cerrado, no rehacer

Todo lo de "## 0-prev13 e." más: el indicador nocturno ya está cableado y desplegado (no reabrir la propuesta).

### f. Prompt para la próxima sesión (S20)

```
Retoma el proyecto Goes (C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\Goes,
repo MendozaVolcanic/goes-volcanic-monitoring, deploy sólo HF). Sesión S20; titúlala "Goes S20: ..."
y numera su traspaso como S20. Usa /retomar.

1. Verifica antes de creer: git fetch; gh pr list (al cerrar S19 venían en camino los PR de H29,
   rama claude/charming-napier-13552c, y de "qué nos falta", rama claude/busy-robinson-07a98a);
   git ls-remote origin -h refs/heads/main (era b1aa332 o posterior, el bot commitea cada 10 min).
   Mira el estado de las sesiones local_02c35abe (H29) y local_d641d4f9 (S19i).
2. Lee CLAUDE.md, STATUS.md "## 0." y "## 0-prev13." (S19), docs/own_volcat/POR_QUE_VOLCAT_VE_Y_NOSOTROS_NO.md §1
   y §3.9, y, si ya existen, docs/own_volcat/h29_pluma_0811/INFORME.md y docs/own_volcat/QUE_NOS_FALTA_S19.md.
3. Revisa los PR de H29 y de S19i contra sus archivos; pide a Nicolás el sí para fusionar cada uno; suma sus
   resultados a POR_QUE §3.9 y responde la pregunta de Nicolás ("encuentro extraño que no podamos ver").
4. Decisiones de "## 0. b.". Correo a Pavolonis: sólo si Nicolás lo trae.
5. Reglas: español de Chile sin voseo ni guiones largos; rutas absolutas; no VIIRS; la carpeta principal (rama
   audit/2026-11-previa-local) no se toca; docs/auditoria_2026-11 no se sube; nada de SSEC al repo ni al Space
   (tampoco transcripciones de sus logs); criterio commiteado antes de medir; control pareado por BT11; líneas
   base sólo con cuadros despejados por ACMF; lo grande a D:; fusionar sólo con el sí de Nicolás para ESE PR y
   con --match-head-commit; cambio de lógica = ficha SDA en el mismo commit; desplegar a HF con la rama local
   main al día.
```

---

## 0-prev13. S19, cierre 2026-11-23 (PR 100 a 104 abiertos sin fusionar: VOLCAT publica Chillán por nacimiento y seguimiento del objeto; la regla de seguimiento quedó leída; ninguna prueba encontró firma IR)

> Sesión coordinadora S19 (`local_ad43daee` la lanzó). Nicolás pidió correr todas las pruebas a la vez. S19 hizo H25
> y el registro de verano. Lanzó cuatro sesiones hijas con PR propio: S19b (H26, `local_a96445ff`), S19c (H27,
> `local_88505056`), S19e (revisión de H13 y H17, `local_be25e0dd`) y S19f (H28 en Fable 5.2, `local_07a4fffe`).
> **Corrección del traspaso S18:** el PR 99 de H24 SÍ quedó fusionado el 23-11 a las 10:42 UTC (merge `4a6fdef`);
> la tabla de S18 de abajo lo da como abierto porque se escribió antes de fusionar.

### a. Todo en una pantalla

| Qué | Estado | Evidencia |
|---|---|---|
| H25: E6 (explosión de 2 km del 27-10) hacia el NNE, viento GFS 16,9° | **SIN SEÑAL** (z +0,52; poder de capa ε 0,10 100 %; falsas alarmas 3 de 39). Pluma angosta sin poder (27 %); la lectura con percentil 20 da z +0,68 pero es INVÁLIDA (falsas alarmas 15 %) | PR 100, `docs/own_volcat/h25_e6_gfs/INFORME.md`; criterio `0716d72` empujado antes de medir |
| H24 de verano | **Registrada** antes de existir los datos: mismo criterio `f2094f7` + `620b5a0`; primera corrida al cierre de enero de 2027, decide la de febrero | PR 100, `docs/own_volcat/h24_verano/REGISTRO_PROSPECTIVO.md` |
| H26: copiar la decisión de VOLCAT (seguidor anclado a cráter caliente + criterio temporal) | **SIN PODER** por la regla (control positivo 10 de 20 tramos). Recupera 12 de 769 píxeles de VOLCAT; dispara en 7,7 % de los cuadros sin VOLCAT. Lo único que coincide es la cercanía al cráter | PR 102, `docs/own_volcat/h26_seguidor_volcat/` |
| H27: fondo de cumbres de control (Antuco, Longaví) para los pulsos de tarde | **INVÁLIDO**: Chillán sin pluma es 1,54 veces más ruidoso (tope 1,5). Lectura: E11 y E13 sin señal; E12 z −2,44 sin poder; Antuco "detecta" z −4,04 el 10-11 | PR 101, `docs/own_volcat/h27_fondo_espacial/` |
| H28 (Fable): regla de seguimiento de VOLCAT leída de sus logs | **Se sostiene en parte**: radio 0,05 km/s × Δt (3 km por minuto) exacto en 3.969 de 3.969 comparaciones, tres satélites; el parecido propuesto no. Chillán: 56 de 60 cuadros son continuaciones, 51 explicadas (**compatible**); 4 nacimientos con puerta no leída | PR 103, `docs/own_volcat/h28_regla_seguimiento/` |
| Revisión H13 y H17 contra la ACMF | **H13 sigue en pie** (AUC 0,604 = azar). **H17 se debilita en la física**: la base tenía 62 % de cuadros nublados; con base despejada la huella queda 0,81 K más FRÍA, no 1,28 K más tibia. El veredicto no cambia | PR 104, `docs/own_volcat/revision_h13_h17_nube/` |
| `POR_QUE_VOLCAT_VE_Y_NOSOTROS_NO.md` | Al día: respuesta vigente al comienzo de §1 y tabla de H17 a H28 con la revisión, en §3.9 | PR 100 |
| Tablas del PR 103 que transcriben logs y eventos de SSEC (26) | Movidas a `D:\goes_notas\s19\h28\resultados\` (verificadas byte a byte), quitadas en commit nuevo (cabeza `ecafbcf`). **Siguen en los commits viejos de la rama, que es pública**: el force-push lo bloqueó el modo automático | PR 103 |
| main | `4a6fdef`; PR 100 a 104 abiertos | `git ls-remote`, `gh pr list` |
| Disco | C: 18 GB libres, D: 13 GB. 16 worktrees además del principal | `df`, `git worktree list` |

### b. Decisiones que esperan a Nicolás

| # | Pregunta | Opciones | Recomendación |
|---|---|---|---|
| 1 | Fusionar PR 100, 101, 102 y 104 (sólo docs y scripts de investigación) | sí / no, cada uno | Sí, los cuatro, con `--match-head-commit` |
| 2 | Fusionar PR 103 (H28) | squash / merge / no | **Squash**: así las tablas transcritas no entran a la historia de main |
| 3 | Borrar las tablas transcritas también de los commits viejos del PR 103 | force-push en la rama / dejarlo | Si la licencia de SSEC te preocupa, hazlo tú en una sesión que tenga el permiso (`git reset --soft` + `git push --force-with-lease` en la rama del PR, nunca en main). GitHub puede seguir mostrando los commits viejos en el historial del PR; para purgarlos del todo hay que pedirlo al soporte de GitHub |
| 4 | Correo a Pavolonis | enviar / esperar | Ahora hay una pregunta chica y exacta: qué pide la puerta de nacimiento `ASHPLUMEPUFF` (contraste con el entorno) y qué distingue los subcriterios "(1)" y "(2)" del seguimiento. Sólo si tú lo pides |
| 5 | Las decisiones de S17 que siguen abiertas: cablear el indicador nocturno, desplegar el PR 88 a HF, borrar el paquete de Fuego (16 GB) | | Igual que en "## 0-prev12 b." y "## 0-prev11 b."; el paquete de Fuego lo usó H28, mantenerlo hasta la respuesta de Pavolonis |
| 6 | Limpiar worktrees viejos (s16, s17, s18 y los de agentes, ya integrados) | sí / no | Sí, después de fusionar; comprobar cada uno con `git cherry` antes de quitarlo |

### c. Lo aprendido

- **VOLCAT sigue por distancia y con los filtros apagados** (propio del proyecto, H28): una vez publicado un objeto,
  hereda cualquier objeto a ≤ 0,05 km/s × Δt del rasgo anterior, aunque sea de un píxel y sin superponerse. En disco
  completo (10 min) eso son 30 km. La decisión real está en el nacimiento.
- **Un fondo prestado de otra cumbre no representa al volcán activo** (propio del proyecto, H27): el centro del nulo
  coincide pero la dispersión no; el error va hacia falsas detecciones. Antes de prestar un nulo, medir la razón de
  dispersiones donde ambos tienen dato.
- **La referencia de viento cruzado puede contener la dirección alternativa de la pluma** (regla de método, H25): si
  dos fuentes de dirección difieren más de 45°, sacar de R los píxeles a ≤ 30° de la otra.
- **Una línea base "despejada" por percentil puede estar nublada** (confirmado de nuevo, revisión S19e, ya sabido
  desde H23): la base de H17 tenía 62 % de cuadros nublados y eso invirtió el signo de su número físico. Toda línea
  base se arma con cuadros que la ACMF da despejados en el terreno bajo (≥ 80 %).
- **`start_session` ignora un `model` más caro que el de la sesión madre** (propio del entorno): la sesión arranca con
  el modelo de la madre. Para correrla en Fable hay que `set_session_model`, detener su primer turno y reenviarle el
  encargo. Comprobar el modelo con `get_session` después de lanzarla.

### d. Problemas abiertos e hipótesis

- **CONFIRMADO (H28):** la ley de distancia del seguimiento de VOLCAT, en cuatro casos y tres satélites.
- **CONFIRMADO (H24, H25):** E6 sin firma IR ni hacia el NO ni hacia el NNE, para una capa que cubre el sector.
- **SIN DATO:** la puerta de nacimiento de VOLCAT (qué contraste pide; por qué dos nacimientos de Chillán están a 8,5
  y 12,5 km del cráter).
- **SIN DATO:** si los pulsos de tarde que VOLCAT marcó tienen firma IR (espera al verano).
- **SIN DATO:** una pluma angosta (≤ 6 km) en E6.
- **SOSPECHA (H23, sigue):** la pluma de Chillán queda bajo la emisividad mínima detectable, o tiene β cercano a 1.
- **Seguimiento:** el informe de H26 (PR 102) cita "la huella 1,3 K más tibia" de H17, que la revisión S19e dejó
  superada; corregir esa frase si se toca H26.

### e. Cerrado, no rehacer

Todo lo de "## 0-prev12 e." (S18) más: "E6 se fue hacia el NNE y por eso H24 no la vio" (H25); "un fondo de cumbres
de control resuelve la tarde" (H27); "copiar el seguidor de VOLCAT con nuestras radiancias da sus píxeles" (H26);
"la huella de H17 está más tibia que el suelo despejado" (revisión S19e).

### f. Prompt para la próxima sesión (S20)

```
Retoma el proyecto Goes (C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\Goes,
repo MendozaVolcanic/goes-volcanic-monitoring, deploy sólo HF). Esta es la sesión S20; titúlala
"Goes S20: ..." y numera su traspaso como S20. Usa /retomar.

1. Verifica antes de creer: git fetch; gh pr list (al cerrar S19 quedaban abiertos los PR 100 a 104);
   git ls-remote origin -h refs/heads/main (era 4a6fdef).
2. Lee CLAUDE.md, STATUS.md "## 0." (S19) y docs/own_volcat/POR_QUE_VOLCAT_VE_Y_NOSOTROS_NO.md §1 y §3.9.
3. Pregunta a Nicolás las decisiones de "## 0. b." (fusiones; squash del 103; force-push de las tablas
   transcritas; correo a Pavolonis; decisiones de S17; limpieza de worktrees).
4. Lo que queda por probar: la puerta de nacimiento de VOLCAT (sólo con el correo o con más logs de SSEC); H24 de
   verano (enero de 2027, registro en docs/own_volcat/h24_verano/). No repetir lo de "## 0. e.".
5. Reglas: español de Chile sin voseo ni guiones largos; rutas absolutas; no VIIRS; la carpeta principal (rama
   audit/2026-11-previa-local) no se toca; docs/auditoria_2026-11 no se sube; nada de SSEC al repo ni al Space
   (tampoco transcripciones fila por fila de sus logs o eventos); criterio commiteado antes de medir; control pareado
   por BT11; huella = event_idx cuando hay archivo de evento; líneas base sólo con cuadros despejados por ACMF; lo
   grande a D: (13 GB libres al cerrar S19); fusionar sólo con el sí de Nicolás para ESE PR y con
   --match-head-commit; cambio de lógica = ficha SDA en el mismo commit.
```

---

## 0-prev12. S18, cierre 2026-11-23 (H24 en la rama `claude/s18-h24-pulsos-reav`, PR abierto sin fusionar: con verdad del OVDAS, los pulsos medibles no dejan firma IR; los que VOLCAT marcó de tarde quedan sin fondo)

> Sesión hija de "Goes S16: modo día VOLCAT y sitio SSEC" (`local_298f6e00`). Nicolás preguntó: "¿crees que podamos
> lograr detectar lo que vio VOLCAT esos pocos días en Chillán?". Respuesta escrita en
> `docs/own_volcat/RESPUESTA_S18_lo_que_vio_volcat.md` (con el resultado de H24 al final).

### a. Todo en una pantalla

| Qué | Estado | Evidencia |
|---|---|---|
| Respuesta a la pregunta de Nicolás, tres caminos con probabilidad estimada | Escrita y commiteada antes de medir | `docs/own_volcat/RESPUESTA_S18_lo_que_vio_volcat.md` |
| H24: pulsos REAV del OVDAS contra el IR de GOES-19 (sector a favor del viento contra viento cruzado, pareado por BT11) | **NO CONCLUYENTE** (criterio `f2094f7`, enmienda 1 `620b5a0`, resultados `e260476`) | `docs/own_volcat/h24_pulsos_reav/INFORME.md` |
| E6, explosión gris oscura de 2.000 m del 27-10 (amanecer) | **SIN SEÑAL con poder** (z −0,15; capa ε 0,05 en todo el sector 82 %; franja angosta ε 0,15 100 %); VOLCAT 0 de 8 | INFORME §3 y §4 |
| E8, 27-10 a media mañana | SEÑAL con el criterio (z −2,26) pero **no sobrevive**: Antuco da −2,06 y −2,19 con la ventana larga | INFORME §4 |
| E11 a E13, los pulsos que VOLCAT marcó (8 de 8, 7 de 7, 10 de 11) | **SIN DATO**: episodio despejado, pero 0 a 3 tardes despejadas sin actividad para el fondo (21-09 a 21-11) | INFORME §6 |
| Falsas alarmas medidas | criterio 3 de 39 (7,7 %); exploratorio 13,1 % y 11,5 %, INVÁLIDO | `resultados/h24_resumen.json`, `h24_explorar_resumen.json` |
| Hueco 24 a 31-10 (L1b C14/C15, ACMF, GFS) | Bajado y verificado (I1 a I3 pasan) | `D:\goes_notas\s18\h24\`; `resultados/h24_instrumento_cubo_oct.json` |
| main | `c1b2cd0` al abrir S18; el PR de H24 no está fusionado | `git ls-remote` |

### b. Decisiones que esperan a Nicolás

| # | Pregunta | Opciones | Recomendación |
|---|---|---|---|
| 1 | Fusionar el PR de H24 (sólo docs y scripts de investigación, no toca `src/` ni la app) | sí / no | Sí: deja escrito, con verdad del OVDAS, que los pulsos medibles no tienen firma IR |
| 2 | Prueba prospectiva de verano: la misma H24 sin cambios sobre los REAV de diciembre a febrero | sí / no | Sí: es la única forma limpia de saber si los pulsos de tarde que VOLCAT marca tienen firma IR |
| 3 | E6 con la dirección del GFS (17°, a 62° de la del REAV) como prueba nueva | sí / no | Sí, barata (datos ya en D:), con criterio propio |
| 4 | Las decisiones de S17 (POR_QUE con H19 a H24, correo a Pavolonis, cableado del indicador nocturno) | | Siguen abiertas, ver "## 0-prev11 b." |

### c. Lo aprendido

- **Las 30 marcas del Grafana de VOLCAT no son todos los días con VOLCAT** (propio del proyecto, en memoria
  `project_loops_volcat_chillan_nov2026.md`): el 11-11 y el 16-11 tienen objetos en el catálogo por cuadro del PNG
  (`calor_rayos/resultados/frames_calor.csv`) y no están en las marcas. Nicolás lo recordó por los loops que pidió.
- **Una línea base "a la misma hora en días despejados" deja sin fondo a la tarde de primavera en la cordillera**
  (propio del proyecto): 15 a 19 % de los cuadros de 14 a 23 UTC tienen escena despejada, y al excluir los días con
  actividad quedan 0 a 3. Antes de diseñar una prueba de tarde, contar los días de fondo disponibles.
- **Una mediana sobre un sector no ve una pluma angosta** (regla de método, para `GUIA_MAESTRA_AUDITORIAS.md` §3b):
  el control positivo tiene que tener la forma del fenómeno; una capa que llena el sector da poder 100 % y esconde
  que la mediana no se mueve si la pluma cubre menos de la mitad.
- **Contrastar el sector de la pluma contra el viento cruzado en el mismo cuadro** cancela el corrimiento de todo el
  día que hundió las pruebas de promediar; el nulo resultante tuvo 7,7 % de falsas alarmas con z ≤ −2.

### d. Problemas abiertos e hipótesis

- **CONFIRMADO (H24, E6, E1, E7):** pulsos documentados por el OVDAS en la mañana, incluida una explosión de ceniza
  de 2 km, no dejan firma IR medible a favor del viento, con poder para una pluma angosta de ε 0,15.
- **SIN DATO:** si los pulsos de tarde que VOLCAT marcó (28-10, 10-11) tienen firma IR.
- **SOSPECHA:** E6 pudo irse hacia el NNE (GFS) y no hacia el NO (REAV); el sector de ±30° la perdería en parte.
- **SOSPECHA (H23, sigue):** la pluma de Chillán está bajo la emisividad mínima detectable o tiene β cercano a 1.

### e. Cerrado, no rehacer

Todo lo de "## 0-prev11 e." (S17) más: "E8 del 27-10 es una detección" (Antuco da lo mismo); "ampliar el fondo a
dos meses resuelve la tarde" (falsas alarmas 11 a 13 %, inválido, y siguen 0 a 3 días de fondo).

### f. Prompt para la próxima sesión (S19)

```
Retoma el proyecto Goes (C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\Goes,
repo MendozaVolcanic/goes-volcanic-monitoring, deploy sólo HF). Esta es la sesión S19; titúlala
"Goes S19: ..." y numera su traspaso como S19. Usa /retomar.

1. Verifica antes de creer: git fetch; gh pr list (al cerrar S18 quedaba abierto el PR de H24,
   rama claude/s18-h24-pulsos-reav); git ls-remote origin -h refs/heads/main.
2. Lee CLAUDE.md, STATUS.md "## 0." (S18), docs/own_volcat/RESPUESTA_S18_lo_que_vio_volcat.md y
   docs/own_volcat/h24_pulsos_reav/INFORME.md.
3. Pregunta a Nicolás las decisiones de "## 0. b." (fusionar H24, prueba de verano, E6 con GFS) y las de S17.
4. Antes de cada prueba, por escrito: el régimen (día/noche, mar/tierra, sensor, versión), las dos preguntas de
   C:\Users\nmend\OneDrive\Escritorio\claude\GUIA_MAESTRA_AUDITORIAS.md §3, y cuántos días de fondo hay.
5. Reglas: español de Chile sin voseo ni guiones largos; rutas absolutas; no VIIRS; la carpeta principal
   (rama audit/2026-11-previa-local) no se toca; docs/auditoria_2026-11 no se sube; nada de SSEC al repo ni al
   Space; criterio commiteado antes de medir; control pareado por BT11; huella = event_idx cuando hay archivo de
   evento; días con VOLCAT desde frames_calor.csv y no sólo las 30 marcas; lo grande a D:; fusionar sólo con el sí
   de Nicolás para ESE PR y con --match-head-commit; cambio de lógica = ficha SDA en el mismo commit.
```

## 0-prev11. S17, cierre 2026-11-22 (PR 85 a 97 en main: VOLCAT sostiene Chillán por seguimiento del objeto, no por firma; la pluma queda bajo lo que el IR de GOES-19 ve; ningún paquete de SSEC trae código)

> **Estado fijado con trabajo ajeno en curso:** al cerrar corría un proceso Python lanzado a las 14:29 que S17 no
> lanzó (probablemente de la sesión coordinadora S16 o de otro proyecto). S17 no tiene subagentes ni descargas
> vivas. Revisa `gh pr list` antes de creerle a esta tabla.
>
> Sesiones: S17 fue sesión hija de "Goes S16: modo día VOLCAT y sitio SSEC" (`local_298f6e00`), que hizo las
> fusiones con el sí explícito de Nicolás y lanzó H21 (VAAC). S17 lanzó 4 subagentes Fable (H19, H20a, H22, H23) e
> hizo H20b y H20c directo. Notas de estado en la carpeta de notas compartida de `local_298f6e00`, `s17_estado.md`.

### a. Todo en una pantalla

| Qué | Estado | Evidencia |
|---|---|---|
| PR 85, 86, 89, 90 (S16) | En main (fusionados por S16 con el sí de Nicolás) | main `9cb0121` |
| PR 89 (H18 modo día), revisión S17 contra HDF4 crudos | Reproducida: 25.432 / 2.260 px; la P con tablas de día de VOLCAT (`ash_probability_SW_IR`) llega a 0,5 en 0 de 2.260, así que NO VALIDA se sostiene sin depender de nuestro motor. Observación: horas de las mitades del texto ≠ JSON (13/13) | comentario en PR 89; `D:\goes_notas\s17\revision_pr89.md` |
| PR 88 (indicador nocturno fase B), revisión S17 | 744 de 744 noches con la misma decisión y referencia que la fase A; 677 tests pasan; no cableado. Fusionado por S16; **no desplegado a HF** (no cambia nada al operador: ninguna vista lo llama) | main `c9ee470`; `D:\goes_notas\s17\revision_pr88.md` |
| Paquetes de prueba de SSEC: ¿traen código? | **No.** Fuego (listado completo, 1.425 entradas), Etna, Mauna Loa, Fukutoku y Kirishima (r20260709): sólo `ancillary/`, `input/`, `reference_data/` | `D:\goes_notas\s17\fuego_tar_lista.txt`, `etna10_tar_lista.txt`, `paquetes\kirsh\lista_completa.txt` |
| H19, paso de objeto en Fuego (Fable) | Reproduce EN PARTE: `ash_probability_subset` ≈ 1 en píxel opaco y oscuro del grupo (εtot ≥ 0,90, ρ0,65 10 a 50 %) 99,97 % (S17 recontó 99,96 % de 18.132 px); con pertenencia a objeto recupera 2.187 de 2.260 px altos; la pertenencia misma NO se reproduce (59,5 %); no llega a εtot bajo | PR 91, `docs/own_volcat/h19_objeto_fuego/` |
| H20a, campos de los archivos de evento (Fable) | `ash_spectral_signature_strength` = P publicada, `..._lwir_only` = P infrarroja de píxel (diferencia 0; S17 recontó en 4.728 px). Chillán: P_IR < 0,05 en 762 de 767 px; publicada ≥ 0,5 en 94, sube en 5 de 60 cuadros | PR 92, `docs/own_volcat/h20a_campos_evento/` |
| H20b, pluma de Kirishima | Descriptivo: nace con P publicada baja y VOLCAT la sube a 0,60 a 0,97 con P_IR 0,02 a 0,08 | PR 93, `docs/own_volcat/h20b_kirishima/` |
| H20c, luz o seguimiento en Kirishima | **SEGUIMIENTO 4 de 4 cuadros**: P con tablas de día 0,05 a 0,08 = IR; la subida empieza con "Temporal selection criteria met for ash"; P publicada = `subset` 75 a 100 % | PR 94, `docs/own_volcat/h20c_kirishima_luz/` |
| H21, VAAC Buenos Aires (lanzado por S16) | NO COINCIDE: 3 de 30 marcas VOLCAT con aviso VAAC de ceniza visible a ≤ 1 h (6 con "WEAK") | PR 95, `docs/own_volcat/h21_vaac/` |
| H22, pluma desprendida del 14-11 (Fable) | **Sin señal IR medible a > 30 km**: ΔBT11 +1,44 K (más tibio, AUC 0,33), ΔBTD +0,08 K en 70 px; control positivo pasa (ε 0,10 a 0,15); ruido dominado por nubes (28 % despejado) | PR 96, `docs/own_volcat/h22_pluma_desprendida/` |
| H23, inyección y recuperación (Fable), COTA | Con cielo despejado, ε 0,15 a 5 km sobre la cumbre AUC 0,91 a 0,95; a 3 km no (máx. 0,68). ε mínimo con BTD contra línea base: 0,07 a 0,09 (5 km), 0,10 a 0,25 (4 km), ≥ 0,34 (3 km). Chillán: BTD de cumbre −0,12 a +0,12 K, bajo el límite (SOSPECHA). Integrar 1 a 3 h no mejora | PR 97, `docs/own_volcat/h23_inyeccion/` |
| main | `3fbbc64`, sin PR abiertos | `git ls-remote` al cerrar |
| Disco | C: 31 GB libres, D: 19 GB. D: llegó a 0 bytes a media mañana (extracción de Kirishima); resuelto, sin archivos truncados encontrados | `df` al cerrar |

### b. Decisiones que esperan a Nicolás

| # | Pregunta | Opciones | Recomendación |
|---|---|---|---|
| 1 | Actualizar `docs/own_volcat/POR_QUE_VOLCAT_VE_Y_NOSOTROS_NO.md` con H19 a H23 | sí / no | Sí: es el documento que se le mostraría a OVDAS o a Pavolonis, y hoy no tiene la respuesta del día (seguimiento, no firma; pluma bajo el límite IR) |
| 2 | Correo a Pavolonis | enviar / esperar | Enviar ahora con preguntas más chicas: qué regla sube `ash_probability_subset` en objetos seguidos ("Temporal selection criteria"), por qué en Chillán casi no sube, y la carga de 7,2 g/m² que VOLCAT publica donde H22 no mide nada. Esta sesión no lo redactó (instrucción) |
| 3 | Desplegar a HF el PR 88 | ahora / al cablearlo | Al cablearlo: hoy no cambia nada visible |
| 4 | Cablear el indicador nocturno al dashboard (propuesta en `docs/own_volcat/vrp_nocturno/PROPUESTA_DASHBOARD.md`) | sí / esperar | Sí, en la grilla de volcán y no en el Modo Sala, con ficha SDA §C.1 pasada a §A en el mismo PR |
| 5 | Borrar el paquete de Fuego (16 GB en `D:\goes_notas\s16\modo_dia\`) | sí / no | Esperar a la respuesta de Pavolonis: es el único caso con L2 completa y objeto convectivo |

### c. Lo aprendido

- **VOLCAT publica Chillán sin firma espectral, por seguimiento del objeto** (propio del proyecto, CONFIRMADO en
  Kirishima, H20c): la probabilidad publicada se separa de la de píxel en el cuadro en que el log dice "Temporal
  selection criteria met", y el valor publicado es `ash_probability_subset`, la probabilidad del objeto.
- **Medir el tamaño de un paquete antes de extraerlo** (regla general del workspace, en memoria
  `feedback_paquetes_ssec_tamano.md`): un `.tar.gz` de HDF se infla 2 a 3 veces; Kirishima (6,6 GB) llenó D: con
  13 GB y dejó a otras sesiones escribiendo en un disco lleno. Listar en flujo con `tar -tzvf -`, extraer sólo las
  carpetas que se usan, dejar ≥ 5 GB de margen.
- **Una identidad no es un nulo** (regla de método, para `GUIA_MAESTRA_AUDITORIAS.md` §3): en H23 la inyección de
  ε = 0 da AUC 0,5 exacto porque las dos clases son la misma escena; el nulo medido es el placebo (24 de 24).
- **Revisar un PR ajeno con una prueba que no dependa de su motor** (regla de método, ya aplicada en PR 87 y ahora
  en 89): la salida intermedia del propio sistema (`ash_probability_SW_IR`) acotó el veredicto sin rehacer la
  lectura de tablas.
- **En una sesión hija, el clasificador de permisos bloquea `gh pr merge` y `gh pr comment`** aunque el encargo
  diga que hay autorización: las fusiones las hace la sesión que tiene el sí textual de Nicolás (propio del
  entorno; S16 tuvo el mismo bloqueo hasta pedir el sí explícito).

### d. Problemas abiertos e hipótesis

- **CONFIRMADO:** ningún paquete de prueba de SSEC del release r20260709 revisado trae código de VOLCAT.
- **CONFIRMADO (Kirishima, un evento):** la subida de la P publicada la hace el seguimiento, no las tablas de día.
- **CONFIRMADO:** en Chillán la P infrarroja de píxel publicada por VOLCAT es < 0,05 en 762 de 767 píxeles.
- **CONFIRMADO (H22):** la pluma desprendida del 14-11 no tiene señal IR medible a > 30 km con el control usado.
- **SOSPECHA (H23, cota circular):** la pluma de Chillán está bajo la emisividad mínima detectable por GOES-19.
- **SOSPECHA:** que en Chillán la vía de seguimiento casi no suba la P (5 de 60 cuadros) por otro peso o regla;
  sin la L2 de VOLCAT de Chillán no se puede ver.
- **SOSPECHA (H22):** la carga de 7,2 g/m² que VOLCAT publica en la pluma lejana es incompatible con lo medido.
- **SOSPECHA (H23, seguimiento):** la máscara de nubes de NOAA marca nublada la cumbre nevada casi siempre; las
  líneas base de H13 y H17 pudieron caer en nube.
- **SOSPECHA débil (H22, post hoc):** BTD(8,4 − 11,2) 0,20 K más baja en la pluma; casi desaparece con control
  igual de tibio.

### e. Cerrado, no rehacer

Todo lo de "## 0-prev10 e." (S16) más: buscar código de VOLCAT en los paquetes de SSEC (5 paquetes, ninguno lo
trae); "la subida de la P publicada la hace la luz rasante" (H20c, 4 de 4 SEGUIMIENTO); "fuera de la cumbre la
pluma sí tiene firma IR" (H22, +1,44 K a > 30 km); "integrar en el tiempo hará aparecer la pluma" (H23, 1 a 3 h no
mejora el AUC); qué son `ash_spectral_signature_strength` y `..._lwir_only` (H20a, diferencia 0); VAAC Buenos Aires
como verdad independiente de las marcas de VOLCAT (H21, 3 de 30); "el 77 % de P = subset" del PR 89 (es 96,5 % con
tolerancia 0,01, H19).

### f. Prompt para la próxima sesión (S18)

```
Retoma el proyecto Goes (C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\Goes,
repo MendozaVolcanic/goes-volcanic-monitoring, deploy sólo HF). Esta es la sesión S18; titúlala
"Goes S18: ..." y numera su traspaso como S18. Usa /retomar.

1. Verifica antes de creer: git fetch; git ls-remote origin -h refs/heads/main (3fbbc64 o posterior);
   gh pr list (al cerrar S17 no había PR abiertos).
2. Lee CLAUDE.md, STATUS.md "## 0." (S17), y los INFORME de docs/own_volcat/ h20c_kirishima_luz,
   h22_pluma_desprendida, h23_inyeccion y h19_objeto_fuego, en ese orden.
3. Antes de cada prueba, por escrito: ¿el régimen (día/noche, mar/tierra, sensor, versión) es el del
   instrumento? y las dos preguntas de C:\Users\nmend\OneDrive\Escritorio\claude\GUIA_MAESTRA_AUDITORIAS.md §3.
4. Trabajo, en orden:
   a. Preguntar a Nicolás las decisiones de STATUS.md "## 0. b." (POR_QUE, correo a Pavolonis, cableado del
      indicador nocturno).
   b. Si dice sí: actualizar docs/own_volcat/POR_QUE_VOLCAT_VE_Y_NOSOTROS_NO.md con H19 a H23.
   c. Revisar si las líneas base de H13 y H17 cayeron en nube (seguimiento de H23).
   d. Correo a Pavolonis: sólo si Nicolás lo pide.
5. Reglas: español de Chile sin voseo ni guiones largos; rutas absolutas; no VIIRS; la carpeta principal
   (rama audit/2026-11-previa-local) no se toca; docs/auditoria_2026-11 no se sube; eventos, tablas,
   paquetes y código de SSEC no van al repo ni al Space; criterio commiteado antes de medir; control pareado
   por BT11; huella = event_idx; lo grande a D: midiendo antes con tar -tzvf - y dejando 5 GB de margen;
   fusionar sólo con el sí de Nicolás para ESE PR y con --match-head-commit; cambio de lógica = ficha SDA en
   el mismo commit.
6. Si la sesión no alcanza: /cierre al llegar a base + 250 mil tokens de contexto.
```

## 0-prev10. S16, cierre 2026-11-22 (PR 84 y 87 en main; PR 85, 86, 88 y 89 abiertos: VOLCAT publica P baja en Chillán, las tablas de día no validan, la pieza que falta es el paso de objeto o pluma)

> **Estado fijado con trabajo ajeno en curso:** al cerrar seguían vivos dos `pytest` lanzados a las 03:43 y 03:49
> (probablemente de la sesión del indicador nocturno, `local_cb5a3f1e`, que abrió el PR 88) y procesos de otros
> proyectos. S16 no los lanzó ni los tocó. Revisa `gh pr list` y el PR 88 antes de creerle a esta tabla.
>
> Sesiones de S16: coordinadora "Goes S16: modo día VOLCAT y sitio SSEC" (sacada de "Goes v12" a pedido de
> Nicolás); hijas S16b `local_29b52d40` (modo día, PR 89) y S16c `local_0b11c3d0` (auditoría, PR 86).
> Notas y traspasos de las hijas en `D:\goes_notas\s16\`.

### a. Todo en una pantalla

| Qué | Estado | Evidencia |
|---|---|---|
| Traspaso S15 | En main | PR 84, `2699b20` |
| 4a, sitio de VOLCAT: imagen `Ash_Probability` en la huella `event_idx` de los 60 cuadros | **BAJA** (pre-registrado, nominal y desfasado): VOLCAT colorea su huella (0,91 contra 0,00 del control BT11) pero de día pleno 0 de 30 cuadros con P ≥ 20 %; P de 90 a 100 % sólo al atardecer del 14-11. Georreferencia a 3,07 px del triángulo del volcán (umbral pre-registrado 2 px, no cumple, declarado) | **PR 85 abierto**, `docs/own_volcat/sitio_volcat/` (criterio `8f9190e` antes de medir) |
| Panel térmico público de VOLCAT (Grafana, "Chillan, Nevados de") | CSV bajados con el sí de Nicolás: VRP GOES-Este mediana 8,3 MW, **43 % de cuadros ≥ 10 MW**; **30 marcas de ceniza** del 24-10 al 18-11 (los NetCDF sólo cubren 3); 67 % con salto de VRP a ≤ 1 h contra 51 % por azar a igual hora (p 0,03) | PR 85, `D:\goes_notas\s16\sitio\grafana\` |
| 4b, modo día (S16b, H18) | Tablas de día **NO VALIDAN** contra Fuego 2018 (κ 0,002; 2 de 2.260 píxeles altos); no se aplicaron a Chillán. Tablas IR **validadas de día sobre tierra** (κ 1,000). La P alta de Fuego viene del objeto (99,8 %) y de `ash_probability_subset` (77 %) | **PR 89 abierto**, `docs/own_volcat/h18_modo_dia/`; paquete de Fuego 16 GB en `D:\goes_notas\s16\modo_dia\` |
| 4c, auditoría PR 75 a 83 (S16c) | Ningún veredicto cambia; los "no separa" valen sólo en IR, de día, en tierra y con nuestro ε y β; "robusto" de la etapa 3 no podía fallar (cielos todos hacia el frío); ningún control positivo en régimen Chillán; nivel B nunca aprobado (κ 0,31) | **PR 86 abierto**, `docs/own_volcat/AUDITORIA_S15_CADENA.md`, `D:\goes_notas\s16\auditoria_s15_traspaso.md` |
| 4d, indicador nocturno de calor 3,9 µm, fase A | **VALIDA** (V1 5/6, V2 0/144, V3 0/19, V4 retardo 1; Sangay 15/22). Revisado contra crudos por S16: `noches.csv` sale exacto de `cuadros.csv`; V3 da 0/21 recontado (no cambia) | **PR 87 fusionado** con `--match-head-commit 1f29e86`, merge `7972a82` |
| Indicador nocturno, fase B (función, ficha SDA, tests, sin cablear) | **Abierto, sin revisar por S16**. Toca `src/process/vrp_nocturno.py`, `dashboard/map_helpers.py`, `docs/FICHA_SDA_GOES.md`, tests | PR 88, cabeza `98cb3c0` |
| Worktrees de S15 | Quitados 7 (todos en main y limpios) y sus ramas locales; ~1 GB. Quedan 8 carpetas vacías bloqueadas por sesiones viejas | `git worktree list` |
| main | `7972a82` en el remoto | `git ls-remote` al cerrar |
| Disco | C: 15 GB libres, D: 20 GB | `df` al cerrar |

### b. Decisiones que esperan a Nicolás

| # | Pregunta | Opciones | Recomendación |
|---|---|---|---|
| 1 | Fusionar PR 85 (sitio VOLCAT) | sí / no | Sí: sólo docs y un script de análisis |
| 2 | Fusionar PR 86 (auditoría) | sí / no | Sí: sólo un informe |
| 3 | Fusionar PR 89 (modo día) | sí / no | Sí, después de que una sesión lo revise contra sus crudos como se hizo con el 87 |
| 4 | PR 88 (indicador nocturno al código, con ficha SDA) | revisar y fusionar / esperar | Revisarlo en S17 antes de fusionar: es el único de la tanda que toca `src/` y `dashboard/` |
| 5 | Correo a Pavolonis (plazo que fijaste: lunes 23-11) | enviar / esperar | Decidiste **esperar** el 22-11. Cuando se envíe, con las preguntas de §d |
| 6 | ¿Probar con Fable el paso de objeto en Fuego? (pregunta tuya, §c) | sesión S17 con Fable / no | Sí, pero acotado: con el paquete de Fuego, que trae entradas y salidas intermedias, no con Chillán |
| 7 | Archivar las sesiones terminadas de S15 y S16 (libera las 8 carpetas vacías) | sí / no | Sí |
| 8 | Borrar el paquete de Fuego (16 GB en D:) | sí / no | No mientras siga la línea del paso de objeto (decisión 6) |

### c. Lo aprendido

- **Respuesta a tu pregunta "¿cómo es posible que no podamos lograr lo mismo que VOLCAT?"** (registrada aquí
  para que no se pierda). Porque lo que decide en Chillán no es la física de píxel, que sí reprodujimos (tablas IR
  exactas de noche sobre mar y de día sobre tierra), sino un paso que no está publicado: el objeto y la vía pluma.
  Tres evidencias de S16: VOLCAT mismo publica P de píxel baja en la huella de Chillán (PR 85); en Fuego la P alta
  viene del objeto y de `ash_probability_subset`, no de las tablas (PR 89); y el calor del cráter se asocia sólo de
  forma moderada a las marcas de ceniza (p 0,03). Ese paso usa **estado entre cuadros** (seguimiento kd-tree,
  `feature_age`, historial `volcat_history.hdf`), umbrales relajados por calor y posiblemente un clasificador
  entrenado. Con entradas y salidas de un solo cuadro no se puede invertir: faltan observables, no inteligencia.
- **¿Fable encontraría la pieza?** No por ser más capaz: si los datos no restringen la regla, ningún modelo la
  deduce. Sí puede servir en un problema bien planteado: el paquete de Fuego trae, para 40 cuadros, entradas,
  `diag_data`, `events`, `l2_data` con `Ash_Group_Id_2d` y `ash_probability_subset`, `history/volcat_history.hdf`
  y `logs`. Ahí sí se puede intentar inferir cuándo un objeto pasa a P ≈ 1 y qué es `ash_probability_subset`,
  con criterio pre-registrado y validación cruzada entre cuadros. Además el paquete se llama `...-volcat-code-ancil`:
  **S16b sólo extrajo `reference_data/`; no se miró si el tar trae código** (SOSPECHA, ver §d). Si lo trae, se
  lee, no se ejecuta, y eso vale más que cualquier inferencia.
- **Antes de inferir la regla de un sistema ajeno, mirar si el autor publica su propia salida intermedia**
  (regla general del workspace): la imagen `Ash_Probability` del sitio y el CSV del Grafana público respondieron
  en horas lo que nueve PR intentaron reconstruir.
- **Grafana público:** la API (`/api/ds/query`) la bloquea el clasificador de permisos; la vía que funciona es el
  inspector del panel en Chrome ("Series joined by time", datos sin formato, Download CSV). Los archivos bajan como
  `<panel>-data-as-joinbyfield-<fecha>.csv` (propio del proyecto).
- **Un control "≤ 2 px de la georreferencia" contra un glifo con texto** se contamina con las letras: usar sólo la
  componente conexa del triángulo (propio del proyecto).

### d. Problemas abiertos e hipótesis

- **CONFIRMADO:** VOLCAT publica P de píxel baja en la huella de Chillán de día (PR 85).
- **CONFIRMADO:** las tablas de día, leídas por nosotros, no reproducen Fuego 2018 (PR 89); las IR sí, de día y en tierra.
- **CONFIRMADO:** 30 marcas de ceniza de VOLCAT en Chillán del 24-10 al 18-11; 67 % con salto de VRP a ≤ 1 h
  (51 % por azar a igual hora, p 0,03).
- **CONFIRMADO:** el VRP de VOLCAT en Chillán tiene 43 % de cuadros ≥ 10 MW, del orden del 48 % nocturno propio de
  H17. **SOSPECHA:** que el "0 de 3 cuadros de 10 MW" de H17 venga de leer `volcano_thermal_activity` del NetCDF,
  que no sería la misma serie.
- **SOSPECHA:** que el tar de Fuego (`...-volcat-code-ancil.tar.gz`, 40 GB) traiga código de VOLCAT además de
  `reference_data/`. No verificado: el tar ya no está en disco.
- **SOSPECHA:** que el pico de saltos de VRP a las 05 y 18 UTC sea en parte efecto del cambio día-noche del
  algoritmo térmico.
- **SOSPECHA (auditoría H-3):** que la "nube" de la etapa 3 en la huella (εtot 0,109, β 0,88) sea residuo de un cielo
  de cumbre ~9 K más tibio.
- Preguntas para Pavolonis cuando se envíe: (1) cómo decide `ASHPLUMEPUFF` y qué peso tiene el calor; (2) qué
  asigna P ≈ 1 a una columna sin firma y qué es `ash_probability_subset`; (3) qué regla suma log-odds de día con
  εtot ≥ 0,5; (4) permiso para archivar los eventos de Chillán.

### e. Cerrado, no rehacer

Todo lo de "## 0-prev9 e." más: "el hueco está en las tablas de día" (VOLCAT publica P baja, PR 85; tablas de día no
validan en Fuego, κ 0,002, PR 89); la API de Grafana por script (bloqueada; usar el inspector en Chrome);
el resultado provisorio "NO VALIDA" del indicador nocturno de las 03:14 (era caché a medias; el definitivo VALIDA).

### f. Prompt para la próxima sesión (S17)

```
Retoma el proyecto Goes (C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\Goes,
repo MendozaVolcanic/goes-volcanic-monitoring, deploy sólo HF). Esta es la sesión S17; titúlala
"Goes S17: ..." y numera su traspaso como S17. Usa /retomar.

1. Verifica antes de creer: git fetch; git ls-remote origin -h refs/heads/main (7972a82 o posterior);
   gh pr list (al cerrar S16: 85, 86, 88, 89 abiertos y este traspaso).
2. Lee CLAUDE.md, STATUS.md "## 0." (S16), docs/own_volcat/sitio_volcat/INFORME.md (PR 85),
   docs/own_volcat/h18_modo_dia/INFORME.md (PR 89) y docs/own_volcat/AUDITORIA_S15_CADENA.md (PR 86).
3. Antes de cada prueba, por escrito: ¿el régimen (día/noche, mar/tierra, versión) es el del instrumento?
   y las dos preguntas de C:\Users\nmend\OneDrive\Escritorio\claude\GUIA_MAESTRA_AUDITORIAS.md §3.
4. Trabajo, en orden:
   a. Preguntar a Nicolás por las fusiones pendientes (85, 86, 89) y revisar el PR 88 contra sus crudos y
      su ficha SDA antes de proponer fusionarlo (toca src/ y dashboard/).
   b. Listar el contenido del tar de Fuego en SSEC
      (bin.ssec.wisc.edu/pub/volcat/test_cases/fuego_goes16-fulldisk_june2018_r20260709-volcat-code-ancil.tar.gz)
      sin bajarlo entero (tar -tz en flujo): ¿trae código? Si lo trae, leerlo (no ejecutarlo) buscando el
      paso de objeto, ASHPLUMEPUFF y ash_probability_subset.
   c. Si no hay código y Nicolás aprueba (decisión 6): sesión con Fable para inferir el paso de objeto en
      Fuego con criterio pre-registrado y validación cruzada entre cuadros. Leer antes
      C:\Users\nmend\OneDrive\Escritorio\claude\GUIA_PROMPTING_prompting-claude-fable-5-1.md.
   d. Correo a Pavolonis: sólo si Nicolás lo pide (decidió esperar el 22-11).
5. Reglas: español de Chile sin voseo ni guiones largos; rutas absolutas; no VIIRS; la carpeta principal
   (rama audit/2026-11-previa-local) no se toca; docs/auditoria_2026-11 no se sube; eventos, tablas y
   paquetes de SSEC no van al repo ni al Space; criterio commiteado antes de medir; control pareado por
   BT11; huella = event_idx; todo lo grande y los temporales a D: (quedan 20 GB); fusionar sólo con el sí
   de Nicolás para ESE PR y con --match-head-commit; cambio de lógica = ficha SDA en el mismo commit.
6. Si la sesión no alcanza: /cierre al llegar a base + 250 mil tokens de contexto.
```

## 0-prev9. S15, cierre 2026-11-22 (PR 74 a 83 en main: la parte pública de VOLCAT, por píxel y por objeto, reproducida y validada en Mauna Loa; ninguna ve Chillán en modo IR; el modo día quedó SIN probar)

> **Convención nueva (desde S15):** cada traspaso lleva el número de sesión en su encabezado y la sesión de
> Claude se titula igual ("Goes S16: ..."). Este bloque es S15 (los 14 bloques anteriores no tenían número;
> S15 es el 15.º). La próxima es **S16**.
>
> **Estado fijado con trabajo en curso:** la sesión hija "Goes: indicador nocturno de calor en cráter 3,9 µm"
> (`local_cb5a3f1e-d91d-4da3-bce2-d48401acf249`, worktree `.claude\worktrees\vrp-nocturno-59a4a2`, rama
> `claude/vrp-nocturno-59a4a2`) seguía trabajando al cerrar. Abre PR sin fusionar. Revisa `gh pr list` antes de
> creerle a esta tabla.

### a. Todo en una pantalla

| Qué | Estado | Evidencia |
|---|---|---|
| Traspaso del 21-11 | En main | PR 74 |
| H15 frente 1, reglas de nube tenue (R1 β7,3 sólo si ε(7,3) ≥ 0,1; R2 relleno multicapa; R3 sin 8,5 µm en nube muy tenue) | **Valida nivel A** en Mauna Loa (κ 1,000 en εtot < 0,2 y 0,2 a 0,5) | PR 75, `docs/own_volcat/lut_h15/nube_tenue/` |
| H15 frente 2, nuestro ε y β (nivel B) | ε al nadir 1 − (1 − ε)^cos θ, nube negra en el punto frío del GFS, β12/11 + 0,2 con εtot < 0,25 y TPW > 2,5 cm. **No cumple**: falta un cielo despejado de 11 µm ~1 K más frío (−0,86 K lejos de nube espesa, −1,6 K junto a ella), sólo en 11 µm, receta no pública | PR 76 (6 vueltas), `lut_h15/cielo_sesgo/INFORME.md` |
| LRC y vecindad | Descartados (techo 73,5 % dentro de 0,01, pide 80 %) | PR 77, `lut_h15/cielo_lrc/` |
| Inventario de reproducibilidad de `docs/own_volcat/` | **13 reproducibles, 1 frágil (H14), 6 rotos**; H11, C2, H15 etapa 2, nube tenue y H9 rehechos con cifras idénticas; ~1,2 GB rescatados a `D:\goes_notas\` | PR 78, 80, 81; `docs/own_volcat/INVENTARIO_REPRODUCIBILIDAD.md` |
| H15 etapa 3, tablas IR sobre Chillán (769 px de `event_idx`, 4 eventos) | **No separa**, robusto en S0/S1/S2 del cielo despejado (P ≥ 0,5 en 2,1 / 0,0 / 1,6 % de la huella) | PR 79, `lut_h15/etapa3_chillan/resultados/e3_metricas.txt` |
| H16, tabla de OBJETO de VOLCAT | Reproducida y validada en Mauna Loa (126 objetos, mediana 0,026 décadas). Chillán: P_obj máx 0,002 (pide 0,8). Los 60 cuadros son `ASHPLUMEPUFF` (49) y `VCB` (11) | PR 82, `docs/own_volcat/h16_objeto/` |
| H17, regla propia (calor 3,9 µm + pluma anclada) | **Falla**: calor 0 de 3 cuadros VOLCAT ≥ 10 MW; pluma POD 0,13 / FAR 0,07. La huella está 1,3 K MÁS TIBIA que su base despejada de 6 días. Informativo: VRP nocturno separa Chillán (48 % ≥ 10 MW desde 24-10) de Antuco y Longaví (~1 %) | PR 83, `docs/own_volcat/h17_regla_propia/` |
| **Modo día de VOLCAT** | **SIN PROBAR.** De los 60 cuadros de eventos, 56 son de día y 4 de crepúsculo, 0 de noche (`mean_feature_solar_zenith_angle`, leído el 22-11). Etapa 3 y H16 usaron sólo tablas IR | Hallazgo de Nicolás, verificado en los NetCDF de `D:\goes_notas\busqueda_2026-11-20\volcat_eventos_357070\` |
| Sitio de VOLCAT (`volcano.ssec.wisc.edu`) | **No revisado en S15.** Publica imagen de probabilidad de ceniza, altura, carga, radio (memoria `reference_volcat_source.md`); alertas por evento | pendiente S16 |
| Indicador nocturno de calor 3,9 µm | Corriendo (fase A validación fuera de muestra; fase B sólo si pasa) | sesión `local_cb5a3f1e` |
| Worktrees integrados de S14 | Borrados 10 de 11; `volcat-capa-deteccion-0bda14` dio "permiso denegado" (git ya no lo registra, la carpeta sigue) | `git worktree list` |
| main | `b0b174c` en el remoto | `git ls-remote` al cerrar |
| Carpeta principal (rama local `audit/2026-11-previa-local`, 340d73a) | Sin cambios de S15. Sin commitear, de antes: `data/borders/V4_limite_Internacional_Recuadro_CHS.zip`, `docs/Correo_VOLCAT_Pavolonis.docx`, `docs/Correo_VOLCAT_Pavolonis_v2.docx` y 23 archivos de `docs/auditoria_2026-11/instrumentos/salida_B/` (no se suben) | `git status --porcelain` |
| Disco | C: 13 GB libres, D: 23 GB | `df` al cerrar |

### b. Decisiones que esperan a Nicolás

| # | Pregunta | Opciones | Recomendación |
|---|---|---|---|
| 1 | ¿Fusionar este traspaso? | sí / no | Sí: sólo STATUS.md |
| 2 | ¿Enviar el correo a Pavolonis el lunes 23-11 (plazo que fijaste)? | enviar / esperar S16 | Esperar a que S16 pruebe el modo día y revise el sitio; si eso no lo explica, enviar con la pregunta reducida a: cómo decide la vía `ASHPLUMEPUFF` y cómo entra el calor del cráter |
| 3 | ¿Auditoría corta de la cadena PR 75 a 83 con verificador de contexto limpio? | sí / no | Sí: el supuesto "tablas IR sobre eventos de día" pasó por nueve PR sin que nadie lo viera; es el patrón 7 de `GUIA_MAESTRA_AUDITORIAS.md` |
| 4 | ¿Indicador nocturno de calor al dashboard? | según la fase A | Sólo si la validación fuera de muestra pasa, con ficha SDA en el mismo PR |
| 5 | Archivo diario de eventos VOLCAT de Chillán (vencen a ~7 días en SSEC) | esperar autorización / bajar igual | Esperar: licencia restringida |

### c. Lo aprendido

- **Antes de cada prueba, la pregunta del crítico despiadado** (regla general del workspace, propuesta para
  `C:\Users\nmend\OneDrive\Escritorio\claude\GUIA_MAESTRA_AUDITORIAS.md` §3): "¿el régimen de los datos
  (día/noche, mar/tierra, versión) es el mismo en que se validó el instrumento?". S15 validó en Mauna Loa (noche,
  mar) y aplicó a Chillán (día, cordillera) con las tablas IR: nueve PR verdes sobre un supuesto que Nicolás vio en
  una frase. Los prompts "crítico despiadado" e "ingeniería inversa" sirven como disciplina antes de cada prueba.
- **Validar la lectura de una tabla ajena contra la salida del propio sistema funciona** (propio del proyecto):
  píxel y objeto de VOLCAT se reprodujeron al decimal en Mauna Loa. Lo que no se reproduce queda acotado a una
  pieza nombrable (el cielo despejado de 11 µm), que es lo que se le pregunta al autor.
- **"Proceso no aparece" no es "proceso muerto"** (regla general): buscar por nombre de script falló porque los
  workers de `multiprocessing` se lanzan como `python -c from multiprocessing.spawn`; mirar escritura reciente en
  disco o el log antes de dar una alarma.
- **Fusionar con `gh pr merge --match-head-commit <sha revisado>`** se aplicó a los PR 75 a 83 sin incidentes.
- **No se puede abrir una sesión desde un aviso automático**: en ese turno, subagente en worktree propio
  (así se hizo el PR 77).

### d. Problemas abiertos e hipótesis

- **CONFIRMADO:** los 60 cuadros de eventos de Chillán son de día o crepúsculo; ninguna prueba de S15 usó las
  tablas de día de VOLCAT.
- **CONFIRMADO:** con tablas IR, ni la probabilidad de píxel ni la de objeto de VOLCAT separan la huella de Chillán.
- **CONFIRMADO:** los archivos de evento declaran `ASHPLUMEPUFF` (49) y `VCB` (11).
- **SOSPECHA:** que VOLCAT publique Chillán por la vía pluma/puff (aprendizaje automático y tiempo, umbrales
  relajados por calor). Leído en la presentación CDR 2022, sin detalle; podría ser también el modo día.
- **SOSPECHA:** que la imagen de probabilidad de ceniza de `volcano.ssec.wisc.edu` muestre la probabilidad por
  píxel de VOLCAT en esos cuadros y decida entre las dos explicaciones anteriores.
- **SOSPECHA:** que el cielo despejado de 11 µm ~1 K más frío venga de código GEOCAT no publicado.
- **SOSPECHA:** que la huella 1,3 K más tibia que su base despejada sea calor o gas caliente en el píxel o base
  fría por nieve (H17, no separado).

### e. Cerrado, no rehacer (con el número que lo cerró)

Todo lo de "## 0-prev8 e." más: sesgo local de 12 px como corrección de ε (vive en el paso de objeto), sesgo BT14
por objeto (VOLCAT no lo calculó en ningún objeto), ángulo de normalización (β reconstruido exacto), nube negra con
atmósfera encima (exigiría 18 K más fría), SST y calibración GOES-17 (BT = L1b NOAA, 100 % dentro de 0,01 K),
curvas de Heidinger y Pavolonis 2009 (signo al revés), LRC y vecindad (techo 73,5 %), probabilidad IR de píxel en
Chillán (P ≥ 0,5 en ≤ 2,1 %), probabilidad IR de objeto en Chillán (máx 0,002), regla propia calor + pluma
anclada (POD 0,13 / FAR 0,07). **No cerrado:** todo lo anterior en modo día.

### f. Prompt para la próxima sesión (S16)

```
Retoma el proyecto Goes (C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\Goes,
repo MendozaVolcanic/goes-volcanic-monitoring, deploy sólo HF). Esta es la sesión S16; titúlala
"Goes S16: ..." y numera su traspaso como S16. Usa /retomar.

1. Verifica antes de creer: git fetch; git ls-remote origin -h refs/heads/main (b0b174c o posterior);
   gh pr list (puede estar el PR del indicador nocturno de calor y este traspaso).
2. Lee CLAUDE.md, STATUS.md "## 0." (S15), docs/own_volcat/h16_objeto/INFORME.md,
   docs/own_volcat/h17_regla_propia/INFORME.md y docs/own_volcat/INVENTARIO_REPRODUCIBILIDAD.md.
3. Antes de cada prueba, responde por escrito: "¿el régimen (día/noche, mar/tierra, versión) es el
   mismo en que se validó el instrumento?" y las dos preguntas del instrumento de
   C:\Users\nmend\OneDrive\Escritorio\claude\GUIA_MAESTRA_AUDITORIAS.md §3.
4. Trabajo, en orden:
   a. Recorrer volcano.ssec.wisc.edu para Nevados de Chillán (vid 357070) del 13 al 18-11-2026: imagen de
      probabilidad de ceniza de VOLCAT, opciones de visualización (altura, carga, radio), detalle de cada
      alerta. Agotar lo local primero (src/fetch/volcat_api.py, memoria reference_volcat_*).
   b. Modo día de VOLCAT: leer las tablas DAY de la LUT de píxel y de objeto, buscar un caso de DÍA para
      validar la lectura (Mauna Loa es de noche) y sólo si valida, aplicarlas a la huella event_idx con
      control pareado por BT11.
   c. Auditoría corta de la cadena PR 75 a 83 con verificador de contexto limpio (guía §3 y patrón 7).
   d. Revisar el PR del indicador nocturno de calor contra sus salidas crudas.
5. Preguntar a Nicolás por el correo a Pavolonis (plazo lunes 23-11) con lo que salga de 4a y 4b.
6. Reglas: español de Chile sin voseo ni guiones largos; rutas absolutas; no VIIRS; la carpeta principal
   (rama audit/2026-11-previa-local) no se toca; docs/auditoria_2026-11 no se sube; eventos y tablas de
   SSEC no van al repo ni al Space; criterio commiteado antes de medir; control pareado por BT11; huella =
   event_idx; todo lo grande y los temporales a D:; fusionar sólo con el sí de Nicolás para ESE PR y con
   --match-head-commit; cambio de lógica = ficha SDA en el mismo commit.
7. Si la sesión no alcanza: /cierre al llegar a base + 250 mil tokens de contexto.
```

## 0-prev8. Cierre 2026-11-21 (PR 65 a 73 en main: H12 no concluyente, H13 falsada, fuga GFS arreglada; tablas y eventos de VOLCAT públicos; H14 compatible, H15 sin probar; correo v5 sin enviar)

> Estado fijado sin trabajo en curso: las siete sesiones hijas de esta coordinación terminaron y no quedan PR
> abiertos (`gh pr list` vacío al cerrar). Sesión coordinadora `local_a7c21f45`; notas de coordinación en
> `C:\Users\nmend\AppData\Local\Claude-Data\claude_pzs8sxrjxfjjc\side-session-notes\local_a7c21f45-ef62-4270-9e3a-c053b95c331e\COORDINACION_2026-11-20.md`.

### a. Todo en una pantalla

| Qué | Estado | Evidencia |
|---|---|---|
| H12, Test 3 original de Francis 2012 | **No concluyente** (AUC 0,581; cuadros 0,758 / 0,515; cumbres 0,348 < 0,50) | PR 65, merge `237f905`; corrección del conjunto B (655 negativos limpios) en `h12_resultado_correccionB.txt` |
| H13, cambio entre cuadros de 10 min | **Falsada** (máximo 0,582 < 0,60 de 18 variables) | PR 66, merge `a1563fe` |
| Fuga de temporales GFS (12,1 GB en C: el 20-11) | **Arreglada de raíz** en 4 scripts: `codes_new_from_message`, 0 temporales, perfiles idénticos byte a byte | PR 67, merge `e2f2edc` |
| POR_QUE al día (§3.6 H12 y H13; §3.7 H14, C2, C2b, H15) | En main | PR 68 `28c5966`, PR 73 `cd82cb8` |
| Búsqueda 2023 a 2026 | Tablas de probabilidad y configuración de VOLCAT para ABI **públicas** en SSEC; eventos por volcán; caso de prueba de Mauna Loa; ninguna publicación nueva del grupo sobre detección | `...\local_a7c21f45-...\BUSQUEDA_2026-11-20.md`; copias en `D:\goes_notas\busqueda_2026-11-20\` (SHA-512 verificado) |
| 60 eventos VOLCAT de Chillán (13, 14 y 18-11) | Bajados con el sí de Nicolás, sólo uso interno, a reserva de autorización | `D:\goes_notas\busqueda_2026-11-20\volcat_eventos_357070\LEEME.md` |
| Plan del 21-11 | En main | PR 69 `a4e60c5`, `docs/own_volcat/PLAN_2026-11-21_LUT_VOLCAT.md` |
| H14, anatomía de los eventos | **Compatible, sin fuerza** (4 eventos; pide ≥ 10). Firma de onda larga < 0,05 en 99,35 % de 767 px, también en el arranque | PR 70 `9152c60`, `docs/own_volcat/eventos_h14/` |
| Huella decodificada del PNG VOLCAT | **Corrida 1 fila al S y 1 columna al E** de `event_idx` (IoU 0,19 → 0,42), medido el 14-11 | `eventos_h14/resultados/georef_resumen.json` |
| C2, modelo radiativo propio | **Repuesto**: error 0,0 K contra H11 (una mutación de la SRF da 7,24 K). Insumos en `D:\goes_cache\rt\` (`H3_RT_DL`, `H3_RT_LBL`) | PR 71 `70ae49c` |
| C2b, cielo despejado de VOLCAT en Mauna Loa | No concluyente por nubes; análisis posterior: **sigue la cota fina** (−3,75 K/km dentro de la celda GFS) | PR 71, `docs/own_volcat/mauna_loa_c2b/` |
| H15, tablas reales sobre Chillán | **Sin probar**: lectura suficiente; validación no aprobada (κ 0,795 con ε y β de VOLCAT, 0,245 con los nuestros); falla en nube tenue (εtot < 0,5), donde está la huella (0,16) | PR 72 `0f729c0`, `docs/own_volcat/lut_h15/` |
| Correo v5 a Pavolonis | Redactado (inglés y español), **sin enviar**; faltan [cargo], [correo institucional], [teléfono] | `...\local_a7c21f45-...\Correo_VOLCAT_Pavolonis_v5.docx` |
| main | `cd82cb8` en el remoto (más el bot de FRP) | `git ls-remote` |
| Disco | C: 23 GB libres, D: 29 GB libres (Mauna Loa y cachés de C2 y C3 en D:) | `df` al cerrar |

### b. Decisiones que esperan a Nicolás

| # | Pregunta | Opciones | Recomendación |
|---|---|---|---|
| 1 | ¿Fusionar este traspaso? | sí / no | Sí: sólo STATUS.md |
| 2 | ¿Enviar el correo v5? | ya / esperar | Ya. Es lo único que destraba H15 (regla de nube tenue y cielo despejado que entra a ε) y regulariza los eventos bajados. Completar cargo, correo y teléfono |
| 3 | ¿Archivar a diario los eventos VOLCAT de Chillán mientras Pavolonis no conteste? | esperar autorización / bajar igual | Esperar: el archivo declara acceso restringido y ya se pide permiso. Costo: se pierde lo que ocurra esa semana |
| 4 | ¿Inventario de reproducibilidad de `docs/own_volcat/` (cada resultado, qué insumos usa, si existen hoy)? | sí, sesión aparte / no | Sí, barato y sin agentes auditores: el 20-11 se perdieron scratchpads y el modelo radiativo dejó de correr sin que nada avisara |
| 5 | ¿Archivar las sesiones hijas terminadas (fuga-gfs, búsqueda, C1, C2, C3, H12, H13)? | sí / no | Sí: todo está en main o en las notas |
| 6 | ¿Borrar los scratchpads viejos de Temp y el worktree `pr39`? (del traspaso anterior) | sí / no | Sí |
| 7 | Capa térmica a 3,9 µm en el dashboard (C6) | ahora / después | Después de la respuesta de Pavolonis, con criterio y ficha SDA |

### c. Lo aprendido

- **Antes de concluir "no es público", recorrer el servidor del autor** (regla general del workspace, propuesta para
  `C:\Users\nmend\OneDrive\Escritorio\claude\GUIA_MAESTRA_INVESTIGACION.md`): durante cuatro días se dijo que las
  tablas de VOLCAT no eran públicas y estaban en un directorio HTTP abierto de SSEC (`bin.ssec.wisc.edu/pub/volcat/`).
  Mirar directorios `pub/`, `test_cases/`, `static_ancillary/` y los `EVENT_URL` de los propios archivos.
- **Validar la huella contra la fuente exacta antes de medir** (propio del proyecto): la huella decodificada del PNG
  estaba corrida un píxel y diluyó quince pruebas. Desde ahora, `event_idx` donde exista; el PNG corregido para octubre.
- **Validar la lectura de una tabla ajena contra la salida del propio sistema antes de aplicarla** (método general):
  C3 eligió la variante en los cuadros 1 a 5, validó en los 6 a 10 y se detuvo al no aprobar. Así un "no" en
  Chillán no se confunde con un error de lectura.
- **Fusionar con `gh pr merge --match-head-commit <sha revisado>`** (regla general): garantiza que lo fusionado es lo
  revisado. Dos PR que agregan una fila al final del mismo archivo chocan: se resuelve conservando ambas.
- **eccodes vía cffi retiene el archivo en Windows** aunque Python lo cierre (memoria `reference_eccodes_cffi_file_leak.md`).
- **Coordinar en paralelo funcionó**: cada sesión hija con criterio propio y PR sin fusionar; la coordinadora revisa
  el criterio contra el registro de actividad de GitHub (`gh api repos/.../activity`) y los números contra la salida cruda.

### d. Problemas abiertos e hipótesis

- **CONFIRMADO:** VOLCAT informa firma de onda larga ~0 en los 60 cuadros de Chillán (H14), bajo el supuesto de que
  1 = firma fuerte.
- **SOSPECHA:** el sentido de la escala de `ash_spectral_signature_strength` (1 = firma fuerte); no documentado,
  pregunta (a) del correo v5.
- **CONFIRMADO:** el corrimiento de 1 px de la huella PNG el 14-11. **SOSPECHA:** que valga igual en octubre y en
  otros días.
- **CONFIRMADO (sólo en Mauna Loa, GOES-17, v3.9.16):** el cielo despejado de VOLCAT sigue la cota fina.
  **SOSPECHA:** que haga lo mismo con GOES-19 sobre los Andes.
- **CONFIRMADO:** con las tablas reales, la probabilidad de VOLCAT se reproduce exacta con εtot ≥ 0,5 y no bajo 0,5
  (posterior de C3). **SOSPECHA:** que la diferencia sea la relación `BETA1112_FROM_BTD_BIAS` / `FCT1` de los atributos.
- **SOSPECHA:** los eventos del 13-11 ya vencieron en SSEC (retención ~7 días, inferida de los listados).
- **SOSPECHA:** la causa de la baja de C: entre el 20-11 (33,5 GB) y el inicio de esta sesión (18 GB); no
  identificada (Temp pesaba 1 GB y no tenía GRIB).

### e. Cerrado, no rehacer (con el número que lo cerró)

Todo lo de "## 0-prev7 e." más: H12 Test 3 original (AUC 0,581; cumbres 0,348), H13 cambio entre cuadros (máximo
0,582), la fuga GFS (PR 67), digitalizar las Fig. 4.13 y 4.14 de la tesis (innecesario: están las tablas reales),
buscar publicaciones del grupo VOLCAT 2023 a 2026 sobre detección (no hay), un núcleo con firma junto al cráter
(H14: mediana 0,0008 a ≤ 10 km), aplicar las tablas a Chillán sin validar la lectura en nube tenue (C3 lo prohíbe).

### f. Prompt para la próxima sesión

```
Retoma el proyecto Goes (C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\Goes,
repo MendozaVolcanic/goes-volcanic-monitoring, deploy sólo HF). Usa /retomar.

1. Verifica antes de creer: git fetch; git ls-remote origin -h refs/heads/main (cd82cb8 o posterior
   con commits del bot de FRP); gh pr list (vacío salvo, quizás, este traspaso).
2. Lee CLAUDE.md, este STATUS.md "## 0.", docs/own_volcat/POR_QUE_VOLCAT_VE_Y_NOSOTROS_NO.md (§1 y §3.7)
   y docs/own_volcat/PLAN_2026-11-21_LUT_VOLCAT.md.
3. Pregunta a Nicolás si envió el correo v5 a Pavolonis y si hubo respuesta
   (C:\Users\nmend\AppData\Local\Claude-Data\claude_pzs8sxrjxfjjc\side-session-notes\local_a7c21f45-ef62-4270-9e3a-c053b95c331e\Correo_VOLCAT_Pavolonis_v5.docx).
   - Si respondió con la regla de nube tenue y el cielo despejado: retomar C3 en la etapa 2 (validación
     contra Mauna Loa, D:\goes_cache\volcat_test_mauna_loa) y sólo si aprueba, la etapa 3 en Chillán con
     event_idx y las dos correcciones del cielo despejado.
   - Si autorizó los eventos: C5, archivo diario de events/Buenos Aires/357070 a D:, para llegar a >= 10
     eventos y volver a medir H14.
   - Si no hay respuesta: decisiones b.4 a b.7 de este bloque.
4. Reglas: español de Chile sin voseo ni guiones largos; rutas absolutas; no VIIRS; la carpeta principal
   (rama audit/2026-11-previa-local) no se toca y su data/raw/volcat_validacion sólo se lee;
   docs/auditoria_2026-11 no se sube; eventos y tablas de SSEC no van al repo ni al Space; token HF sin
   imprimir; cambio de lógica = ficha SDA en el mismo commit; fusionar sólo con el sí de Nicolás para ESE
   PR y con --match-head-commit; criterio antes de medir y control pareado por BT11; huella = event_idx
   o PNG corregido 1 px; todo lo grande a D:.
5. Si la sesión no alcanza: /cierre al llegar a base + 250 mil tokens de contexto.
```

## 0-prev7. Cierre 2026-11-20 (PR 60 a 63 en main: H11 no concluyente, SECO propio no cumple; tesis de Pavolonis leída; H12 y H13 corriendo; limpieza de disco)

> **Estado fijado con trabajo en curso.** Al cerrar seguían vivas dos sesiones hijas, sin rama subida:
> H12 "Goes: H12, Test 3 original de Francis 2012 en Chillán" (`local_45e706c6-ebec-46c0-a547-4c7136a2428a`,
> rama `claude/competent-raman-259e42`, corriendo) y H13 "Goes: H13, dimensión temporal de la pluma de
> Chillán" (`local_6d39c8ff-7bbe-4a6a-9d73-546147fe9854`, rama `claude/intelligent-volhard-0a6fe2`, detenida
> esperando). Ambas abren PR sin fusionar. Revisa `gh pr list` antes de creerle a esta tabla.

### a. Todo en una pantalla

| Qué | Estado | Evidencia |
|---|---|---|
| Traspaso del 19-11 noche | En main | PR 60, merge `bacae60` |
| H11 (terreno del cielo despejado, filas de volcán, atajo de SO₂) | **No concluyente** | PR 61, merge `014cfd1`. CF ≥ 3 de día 0,71 con pluma y 0,83 sin pluma; de noche 0,29 y 0,00; A5 en 0 de 733 píxeles; βtot(12/11) AUC 0,58 [0,54; 0,64] (`docs/own_volcat/reproducir_volcat/resultados/h11_resultado.txt`) |
| Etapa 2, SECO propio entrenado con VOLCAT | **No cumple** | PR 62, merge `ffa13d1`. 0 de 100 cuadros, 0 de 655 falsas alarmas; mediana de probabilidad por píxel 1,6 % (máx. 34 %) contra 80 %; bosque aleatorio informativo 38 de 100 con 4,3 % de falsa alarma (`e2_resultado.txt`, `e2_diagnostico_objetos.txt`) |
| `POR_QUE_VOLCAT_VE_Y_NOSOTROS_NO.md` al día (§3.5 nueva, filas H11 y E2, corrección de H8) | En main | PR 63, merge `b9f3f19` |
| Lectura completa de 8 documentos (Francis 2012, Saint 2023, Watson 2004, Doutriaux-Boucher 2009, Seemann 2008, Pavolonis 2013, Heidinger 2012, ATBD SO₂) | Hecha | `C:\Users\nmend\AppData\Local\Claude-Data\claude_pzs8sxrjxfjjc\side-session-notes\local_f3a7d295-ddde-4b7c-b258-25e760c44266\SINTESIS_lecturas_2026-11-20.md` y `LECTURA_*.md` en la misma carpeta |
| Tesis de Pavolonis 2014 | Bajada (191.259.165 bytes, 307 pp) y leída (cap. 1 a 6, 8 y apéndices C y E) | `...\local_1055cba6-2c2f-4aa4-9119-82691ee2ed22\pdfs\Pavolonis_2014_tesis_doctoral.pdf`; lecturas `LECTURA_tesis_Pavolonis_A_cap3-4.md`, `_B_cap4-6.md`, `_C_cap1-2-5-8.md` en la carpeta de notas `local_f3a7d295-...`; Fig. 4.12 digitalizada en `fig4_12_tierra_razones_digitizadas.csv` (aproximada, por década) |
| Correo v4 a Pavolonis (3 preguntas: terreno, tablas para ABI, tiempo) | Redactado, **sin enviar** | `C:\Users\nmend\AppData\Local\Claude-Data\claude_pzs8sxrjxfjjc\side-session-notes\local_1055cba6-2c2f-4aa4-9119-82691ee2ed22\Correo_VOLCAT_Pavolonis_v4.docx` |
| Lightning-v1: Chillán en sus coordenadas GVP y hora GLM con decodificación CF | Fusionado en ese repo | PR 1 de Lightning-v1, merge `2108b02` (14:23 UTC). Datos publicados desde el 24-04 siguen con los dos defectos |
| Limpieza de disco | Hecha: 24 → 33,5 GB libres | 437 L1b de `data/raw` borrados (siguen en S3); 21 sesiones archivadas; `volcat_validacion` rescatado a `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\Goes\data\raw\volcat_validacion` (989 sha256 verificados); cachés de oct-nov en `...\local_f3a7d295-...\cache_rescatada\` y `h12_datos\` |
| H12 y H13 | **Corriendo** en sesiones hijas | ver aviso arriba |
| main | `53a8aae` en el remoto (bot de FRP sobre `b9f3f19`) | `git ls-remote` |

### b. Decisiones que esperan a Nicolás

| # | Pregunta | Opciones | Recomendación |
|---|---|---|---|
| 1 | ¿Fusionar este traspaso? | sí / no | Sí: sólo STATUS.md |
| 2 | ¿Enviar el correo v4 a Pavolonis? | ya / después de H12 y H13 | Ya: las tres preguntas valen con cualquier resultado; completa los campos [cargo], [correo institucional] y [teléfono] |
| 3 | ¿H14: SECO con las razones de verosimilitud de la tesis (Fig. 4.12 a 4.14, digitalizadas) sobre huella y control? | sí / no | Sí, en sesión aparte y con criterio antes de medir: dice si las tablas de VOLCAT bastan para ver la pluma. Advertencia: lectura por década, ±1 bin, y los clasificadores 3D sólo están para εtot 0,10 a 0,20 |
| 4 | ¿Borrar los 4 scratchpads de Temp (1,7 GB) y el worktree `pr39` (0,14 GB)? | sí / no | Sí: lo que servía ya está rescatado y verificado |
| 5 | ¿Capa térmica propia a 3,9 µm en el dashboard? | ahora / después | Después de H12 y H13, con criterio y ficha SDA |
| 6 | ¿Regenerar los datos históricos de Lightning-v1 desde el 24-04? | sí / no | Sí, si alguien usa los conteos históricos de Chillán; decidir en ese repo |

### c. Lo aprendido

- **Umbral desde la fuente primaria** (regla general del workspace, ya en `POR_QUE` §7): el Test 3 de Francis
  2012 es BTD < **+0,7 K** y BTD < BTD_clr − 1 K; Falconieri 2018 lo resumió como −2 ≤ BTD ≤ −0,7 K y la prueba
  del 19-11 siguió el resumen. Todo umbral se mira en la imagen del PDF original antes de escribir el criterio.
- **Leer la tesis antes que los papers que la resumen**: SECO Parte 1 dice "not shown" para las razones sobre
  tierra; la tesis las publica (Fig. 4.12 a 4.14). También trae σ_clr = 5 K en BT11 sobre tierra (Tabla 5.2).
- **Datos irreemplazables en carpetas ignoradas de un worktree** (regla general): `volcat_validacion` vivía
  sólo en `data/raw` de dos worktrees y la API de VOLCAT guarda 30 días. Antes de archivar una sesión, mirar
  `git status --ignored` de su worktree. Ya está en la memoria del proyecto.
- **Archivar no libera el disco al tiro**: la app deja los worktrees en una reserva y los reutiliza (H12 y H13
  tomaron dos). Lo que sí libera de inmediato es borrar datos.
- **Brief de sesión hija**: la de Lightning-v1 fusionó su PR sin pasar por la revisión de esta sesión. En los
  briefs, escribir que la fusión la pide la sesión coordinadora con el sí de Nicolás para ese PR.
- `python -I` ignora `PYTHONIOENCODING`: usar `sys.stdout.reconfigure(encoding="utf-8")`.

### d. Problemas abiertos e hipótesis

- **CONFIRMADO:** la etapa 2 ya midió la mediana de probabilidad por píxel (`np.nanmedian(pv)` en
  `e2_clasificador.py`) e implementó las filas "mediana > 80 %, objeto > 0" de la Tabla 4 (= Tabla 6.3 de la
  tesis). El cuello de botella es la probabilidad por píxel, no la del objeto.
- **CONFIRMADO:** la tesis (t195, t241 y t242) deja el uso de varios tiempos como trabajo futuro y lo propone
  justo para plumas sin contraste con el cielo despejado. Pasado a H13.
- **CONFIRMADO:** ninguna de las fuentes leídas (SECO 1 y 2, ATBD 2025, CDR 2022, Pavolonis 2013, Heidinger
  2012, ATBD SO₂, tesis 2014) corrige el terreno del cielo despejado.
- **SOSPECHA:** con las razones de la tesis multiplicadas (5 a 8 clasificadores) la huella llegaría a 80 %
  mientras el control no; no medido (decisión b.3).
- **SOSPECHA:** VOLCAT ABI usa hoy las tablas entrenadas con MODIS de la tesis; no verificado (pregunta b del
  correo v4).
- **SOSPECHA:** quién autorizó la fusión del PR 1 de Lightning-v1 (cuenta MendozaVolcanic, desde su sesión).
- **SOSPECHA:** los PNG VOLCAT de Chillán del 08-11 vencen en SSEC hacia el 08-12 (30 días rodantes, dicho por
  la sesión de validación de magnitud, no leído de la fuente).

### e. Cerrado, no rehacer (con el número que lo cerró)

Todo lo de la lista "## 0-prev6 e." más: H11 (CF ≥ 3 sin distinguir de día, 0,71 contra 0,83; A5 0 de 733;
βtot(12/11) AUC 0,58), SECO propio con variables públicas (0 de 100; mediana por píxel 1,6 %), la probabilidad
del objeto como cuello de botella (ya cubierta), atajo de SO₂ en pluma baja (Doutriaux-Boucher 2009: ~1,2 K con
150 DU a 600 hPa), Saint 2023 (en GOES nada con BTD > −0,29 K es ceniza), ATBD SO₂ v1.0 (no usa εtot ni βtot) y
la prueba de Londres en la versión de Falconieri (2 de 35). El Test 3 original de Francis está en H12, no cerrado.

### f. Prompt para la próxima sesión

```
Retoma el proyecto Goes (C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\Goes,
repo MendozaVolcanic/goes-volcanic-monitoring, deploy sólo HF).

1. Verifica antes de creer: git fetch; git ls-remote origin -h refs/heads/main; gh pr list.
   Lista las sesiones vinculadas: H12 (local_45e706c6-ebec-46c0-a547-4c7136a2428a) y H13
   (local_6d39c8ff-7bbe-4a6a-9d73-546147fe9854) pueden haber abierto PR. Revisa cada uno (criterio
   commiteado antes de medir y sin cambios después, números contra la salida cruda, sin guiones
   largos, sin referencias a la auditoría, ficha SDA si toca código) y pide el sí de Nicolás.
2. Lee CLAUDE.md, este STATUS.md "## 0.", docs/own_volcat/POR_QUE_VOLCAT_VE_Y_NOSOTROS_NO.md
   (§1, §3.5, §4, §6) y, en C:\Users\nmend\AppData\Local\Claude-Data\claude_pzs8sxrjxfjjc\side-session-notes\local_f3a7d295-ddde-4b7c-b258-25e760c44266\ :
   SINTESIS_lecturas_2026-11-20.md y LECTURA_tesis_Pavolonis_A_cap3-4.md.
3. Orden: (a) integrar H12 y H13 en POR_QUE (PR aparte, con sí); (b) decisiones b.2 a b.6 de este
   bloque, sobre todo el correo v4 y H14; (c) si H13 o H14 dan un detector que cumpla la vara del
   17-11, diseñarlo con Nicolás con ficha SDA en el mismo commit.
4. Reglas: español de Chile sin voseo ni guiones largos; rutas absolutas; no VIIRS; la carpeta
   principal (rama audit/2026-11-previa-local) no se toca, salvo data/raw/volcat_validacion que no
   se modifica nunca; docs/auditoria_2026-11 no se sube; token HF sin imprimir; cambio de lógica =
   ficha SDA en el mismo commit; fusionar o desplegar sólo con el sí de Nicolás para ESE PR;
   criterio antes de medir y control pareado por BT11; umbrales leídos en la imagen del PDF original.
5. Si la sesión no alcanza: /cierre al llegar a base + 250 mil tokens de contexto.
```

## 0-prev6. Cierre 2026-11-19 noche (PR 53 a 59 en main: capa VOLCAT desplegada; H8, H9, H10 cerradas; lectura completa de SECO; H11 abierta)

> **Estado fijado con trabajo en curso.** La sesión "Goes: reproducir la detección VOLCAT en Chillán
> (H11 y SECO)" (id `local_debe03b3-3cc8-4666-9ecf-fd396b031db4`, rama `claude/reproducir-volcat-*`)
> seguía corriendo al cerrar: etapa 0 (leer la presentación CDR 2022), etapa 1 (H11) y etapa 2 (SECO
> propio calibrado contra VOLCAT). Puede haber abierto PR después de este commit: revisa `gh pr list`
> antes de creerle a esta tabla.

### a. Todo en una pantalla

| Qué | Estado | Evidencia |
|---|---|---|
| Capa VOLCAT por volcán en el dashboard (cabecera de la grilla y resumen de 44 en "VOLCAT por zona"; ficha SDA v2.8 §A.7) | **En main y desplegada en HF** | PR 53, merge `2d730d1`; Space sha `34607e1` RUNNING 14:10 UTC, health ok; no revisada en navegador |
| β(7,3/11) fuera de muestra | Cerrada: noche no concluyente (anillo 0,90 > huella 0,82), día falsada (AUC 0,41); mide humedad | PR 55, `docs/own_volcat/beta73/` |
| Prueba tolerante del VAAC de Londres (H8) | Cerrada: no cumple (2 de 35 cuadros, 0 de 82 px en huella) | PR 54; implementación comprobada contra Falconieri 2018 completo (5 pruebas, coherencia 6 de 9) |
| Dirección de la pluma (H10) | No concluyente (2 jornadas comparables); BTD en el sector REAV AUC 0,68 y 0,70, bajo umbral | PR 57, `docs/own_volcat/direccion_pluma/` |
| Calor 3,9 µm y rayos GLM (H9) | Falsada como gatillo del momento (noche AUC 0,46; 0 de 100 cuadros con rayos); cráter caliente el 71 % de las noches desde el 24-10 | PR 58, `docs/own_volcat/calor_rayos/` |
| Documento de conjunto | Al día con H8, H9, H10 (§3.3, §3.4) | PR 56 y 59, `docs/own_volcat/POR_QUE_VOLCAT_VE_Y_NOSOTROS_NO.md` |
| Lectura completa de papers | SECO 1 y 2, Pavolonis 2018, Mackie 2014, Falconieri 2018, Piscini 2011 | `C:\Users\nmend\AppData\Local\Claude-Data\claude_pzs8sxrjxfjjc\side-session-notes\local_1055cba6-2c2f-4aa4-9119-82691ee2ed22\LECTURA_PAPERS_2026-11-19.md` y `LECTURA_SECO_PARTE1.md` |
| Referencias faltantes | 60 revisadas, 10 priorizadas; Nicolás bajó 7 (copiadas a `pdfs\`, sin leer aún); faltan Prata y Kerkmann 2007, Lucas y Majewski 2015 (lo bajado fue otro PDF del BoM) y la tesis de Pavolonis 2014 | `REFERENCIAS_FALTANTES_2026-11-19.md` en la misma carpeta de notas |
| Reproducir VOLCAT (H11 + SECO propio) | **Corriendo** en otra sesión | ver aviso arriba |
| main | `aa05502` en el remoto; sin PR abiertos al cerrar salvo el de este traspaso | `git ls-remote` |

### b. Decisiones que esperan a Nicolás

| # | Pregunta | Opciones | Recomendación |
|---|---|---|---|
| 1 | ¿Fusionar este traspaso? | sí / no | Sí: sólo STATUS.md |
| 2 | Correo v3 a Pavolonis (`Correo_VOLCAT_Pavolonis_v3.docx` en la carpeta de notas) | enviar ya / esperar H11 | Esperar el veredicto de la etapa 1 de H11 y agregar una línea concreta (¿corrigen el terreno en el cielo despejado?); pedir también la tesis 2014 y el paper térmico "en preparación" |
| 3 | Defectos de Lightning-v1 (Chillán con coordenadas de Antuco; hora de destello sin factor de escala, hasta ~9 h corrida) | arreglar en ese repo / dejar | Arreglar en una sesión en ese repo: el sitio público muestra datos de Antuco como si fueran de Chillán |
| 4 | Capa térmica propia a 3,9 µm (H9 mostró un indicador que el FDCF no ve) | proponer como capa / no | Esperar a cerrar H11; después evaluarla con criterio y ficha SDA |

### c. Lo aprendido

- **Leer completo antes de diseñar una prueba** (regla general del workspace): la Tabla 4 y el Apéndice A
  de SECO Parte 2 traen las filas de volcán (objetos de 0 a 25 px con bandera de nube CF ≥ 3) y la
  compuerta de SO2 (ec. A5) que ninguna prueba había usado; se habían leído "por secciones" en HTML.
  Las tablas y ecuaciones de los PDF de AGU salen desordenadas al convertir: leerlas como imagen
  (PyMuPDF, `get_pixmap`).
- **Subagentes de lectura**: rinden con preguntas cerradas, citas cortas y "último título leído" como
  prueba de cobertura; contrastar una tabla clave contra el PDF (se hizo con la Tabla 7 de Pavolonis 2018).
- **Cierre por contexto** (CLAUDE.md global): esta sesión pasó el umbral por pedidos encadenados; lo
  pesado se movió a sesiones hijas.

### d. Problemas abiertos e hipótesis

- **SOSPECHA (H11):** VOLCAT calcula el cielo despejado con el GFS sin corregir el terreno (SECO 1 §4.1,
  CONFIRMADO en el texto), así que en la cumbre de Chillán su despejado saldría tibio (nuestro GFS da ~7 K,
  CONFIRMADO en H3) y la bandera CF ≥ 3 de las filas de volcán pasaría siempre. SECO 1 la debilita: exige
  firma de ceniza en βtot(12/11), y un error sólo de superficie deja βtot(7,3/11) cerca de 0, así que el
  atajo de SO2 no se abriría solo. Variante: emisividad SeeBor a 8,5 µm mal en la cumbre (subiría
  β(8,5/11) sin SO2). En prueba (etapa 1).
- **SOSPECHA:** que la huella VOLCAT quede casi siempre al S o SE del cráter es paralaje y no "ignorar el
  viento" (H10); depende de la altura supuesta.
- **CONFIRMADO:** Lightning-v1 ubica "Nevados de Chillán" en -37,411, -71,352 (Antuco) (PR 58, contraste
  contra GLM de NOAA).
- **CONFIRMADO:** VOLCAT no dibujó objeto anclado en 42 cuadros del 27-10, con columnas en el REAV (PR 57).

### e. Cerrado, no rehacer (con el número que lo cerró)

Canales solares (AUC 0,50 pareado), paralaje (sin señal hasta 5 px), 8,5 µm sola (AUC 0,26), umbral BTD
y anomalía de fondo (17-11), cielo GFS como compuerta (90 % huella contra 88 % control), seguimiento H7
(0 de 3 primeros cuadros con señal), β(7,3/11) (noche 0,82 con anillo 0,90; día 0,41), prueba de Londres
(2 de 35), RSTASH (sólo anomalía bajo -2σ), BTD corregida por vapor (constante por escena), calor como
gatillo (AUC 0,46), rayos (0 de 100), crecimiento vertical de Pavolonis 2018 (pide dBT < -10 K; nuestra
prueba de 2 K tampoco se cumplió), bayesiano de Mackie 2014 (ruido de despejado 1,6 a 2,4 K sobre tierra,
prior sin volcán). H6 cerrada por Nicolás (es ceniza).

### f. Prompt para la próxima sesión

```
Retoma el proyecto Goes (C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\Goes,
repo MendozaVolcanic/goes-volcanic-monitoring, deploy sólo HF).

1. Verifica antes de creer: git fetch, git ls-remote origin -h refs/heads/main, gh pr list.
   Lista las sesiones vinculadas y su estado; la de "reproducir la detección VOLCAT en Chillán
   (H11 y SECO)" (local_debe03b3-3cc8-4666-9ecf-fd396b031db4) puede haber abierto PR. Revisa
   cada PR (criterio commiteado antes de medir, números contra salida cruda, sin guiones largos,
   sin referencias a la auditoría, ficha SDA si toca código) y pide el sí de Nicolás antes de
   fusionar.
2. Lee CLAUDE.md, este STATUS.md "## 0." y docs/own_volcat/POR_QUE_VOLCAT_VE_Y_NOSOTROS_NO.md,
   y en la carpeta de notas local_1055cba6-...: LECTURA_PAPERS_2026-11-19.md,
   LECTURA_SECO_PARTE1.md, REFERENCIAS_FALTANTES_2026-11-19.md.
3. Objetivo de Nicolás: conseguir lo mismo que VOLCAT en Chillán y luego mejorarlo. Orden:
   (a) leer con agentes y preguntas cerradas los 7 papers nuevos de pdfs\ (Francis 2012,
   Saint 2023, Watson 2004, Doutriaux-Boucher 2009, Seemann 2008, Pavolonis 2013,
   Heidinger 2012) y el ATBD de SO2 del repo (docs/Aviation_SO2_v1.0_no_color.pdf); pasar lo
   que sirva a la sesión de reproducir VOLCAT. (b) Buscar la tesis de Pavolonis 2014
   (UW-Madison) con la skill investigacion. (c) Integrar los veredictos de H11 y del SECO
   propio en POR_QUE (PR aparte, con sí). (d) Decisiones b.2 a b.4 de este bloque.
4. Reglas: español de Chile sin voseo ni guiones largos; rutas absolutas; no VIIRS; la carpeta
   principal (rama audit/2026-11-previa-local) no se toca; docs/auditoria_2026-11 no se sube;
   token HF de ~/.hf_token sin imprimir; cambio de lógica = ficha SDA en el mismo commit;
   fusionar o desplegar sólo con el sí explícito de Nicolás para ESE PR.
5. Si la sesión no alcanza: cierra con /cierre al llegar a base + 250 mil tokens.
```

## 0-prev5. Cierre 2026-11-19 (PR 51 en main: H3 no separa, H7 falsada, búsqueda bibliográfica nueva)

> Reemplaza como estado vigente al bloque "## 0-prev4" de abajo, que se conserva. Verificado al
> escribir: `main` remoto = `601dc4c` (`git ls-remote`), sin PR abiertos fuera del de este traspaso
> (`gh pr list`), Space de HF `fd8d8ff` RUNNING (sigue sin el texto del PR 45).

| Qué | Estado | Evidencia |
|---|---|---|
| H6 (¿es ceniza?) | **Cerrada por Nicolás el 19-11**: sí, Chillán lleva muchos días con pulsos y columnas de gas y ceniza | `docs/own_volcat/POR_QUE_VOLCAT_VE_Y_NOSOTROS_NO.md` |
| H3 (cielo despejado modelado + β con C10) | **No concluyente por la regla; en la práctica no separa** (PR 51, merge `601dc4c`) | `docs/own_volcat/h3_h7/INFORME_H3.md`. Modelo LBL propio (HITRAN + MT_CKD + SRF ABI + GFS 0,25°). GFS pone la cumbre ~1,5 km más abajo y el cielo modelado queda ~7 K más tibio: la compuerta ε(11) ≥ 0,02 pasa en 90 % de la huella y 88 % del control. Ningún β separa; β(12/11) queda 0,013 sobre la línea de falsación |
| H7 (VOLCAT sigue la nube desde un cuadro con señal) | **Falsada** (PR 51) | `docs/own_volcat/h3_h7/INFORME_H7.md`. En 3 de 3 episodios el primer cuadro de la cadena no tiene BTD < -1 K, hot spot FDCF ni enfriamiento rápido. VOLCAT sí arrastra objetos (19 de 23 cuadros sin señal tienen antecesor), pero la semilla tampoco tiene señal en nuestros datos |
| Búsqueda bibliográfica 19-11 (4 frentes) | **Hecha**, fuera del repo | síntesis `C:\Users\nmend\AppData\Local\Claude-Data\claude_pzs8sxrjxfjjc\side-session-notes\local_1055cba6-2c2f-4aa4-9119-82691ee2ed22\SINTESIS_busqueda_2026-11-19.md`, PDF en `pdfs\` |
| Hugging Face | build `d62753a`, sin el PR 45 (sólo texto) | desplegar con el próximo cambio de código |

**Lectura de conjunto.** Falsadas: umbral más bajo, paralaje, 8,5 µm, luz solar, seguimiento desde una
semilla con señal. H3 no separa. Lo que VOLCAT usa y no podemos reproducir son sus umbrales por volcán y su
aprendizaje automático, que no son públicos (ATBD VOLCAT v1.0, enero 2025, y presentación CDR 2022 en
https://bin.ssec.wisc.edu/pub/volcat/). Ningún método publicado demuestra detectar una pluma con BTD más
alta que su entorno, que es el caso de Chillán. Dato de la búsqueda: el OVDAS ya usa VOLCAT para la altura
(REAV Chillán 25-10-2026).

**Indicio sin validar (posterior al criterio):** β(7,3/11) más alta en la huella las noches del 28 y 29-10.
No cuenta como resultado; sólo vale si se prueba con criterio nuevo en episodios nuevos.

**Lo aprendido**

- Un cielo despejado modelado con GFS 0,25° sobre un volcán de alta montaña mide el error del terreno,
  no la pluma: la cumbre del modelo queda ~1,5 km más baja. Comparar siempre contra el cielo empírico de la
  escena y contra un control pareado antes de atribuirle sensibilidad.
- La documentación de un algoritmo (seguimiento kd-tree del ATBD) sugería H7 y los datos la falsaron en una
  hora: probar barato antes de construir.
- Un reinicio del PC mata subagentes y procesos en segundo plano de las sesiones laterales; lo que sobrevive
  es lo commiteado y lo escrito a disco. Pedir siempre resultados parciales a disco.

**Decisiones que esperan a Nicolás**

| # | Pregunta | Opciones | Recomendación |
|---|---|---|---|
| 1 | ¿Cómo seguir con la detección de plumas débiles? | (a) usar VOLCAT como capa de detección, como ya hace el OVDAS; (b) escribir a Pavolonis por Chillán; (c) probar β(7,3/11) con criterio nuevo; (d) prueba tolerante del VAAC de Londres (Francis 2012, 2 a 4 días) | (a) y (b) juntas; (c) sólo con episodios nuevos |
| 2 | ¿Instalar gfortran o WSL para PFAAST (el modelo de SECO)? | sí / no | No por ahora: H3 ya no separa con un modelo LBL propio |
| 3 | ¿Desplegar `main` a HF? | ahora / con el próximo cambio | Con el próximo cambio de código |

**Prompt para la próxima sesión**

```
/retomar en Goes (C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\Goes).
1. Verifica: git fetch; git ls-remote origin -h refs/heads/main; gh pr list; API de HF (sha y stage).
2. Lee STATUS.md "## 0.", docs/own_volcat/POR_QUE_VOLCAT_VE_Y_NOSOTROS_NO.md (§1, §3.2, §4, §6) y la síntesis
   C:\Users\nmend\AppData\Local\Claude-Data\claude_pzs8sxrjxfjjc\side-session-notes\local_1055cba6-2c2f-4aa4-9119-82691ee2ed22\SINTESIS_busqueda_2026-11-19.md
3. Pregunta a Nicolás la decisión #1 antes de tocar código. Si elige (b), redacta el correo a Pavolonis para
   que él lo envíe (no lo envíes tú). Si elige (c) o (d), escribe el criterio antes de medir.
Sin VIIRS, sin guiones largos, ficha SDA en el mismo commit si cambia lógica, fusionar o desplegar sólo con
el sí de Nicolás por PR, docs/auditoria_2026-11 no se sube.
```

---

## 0-prev4. Cierre 2026-11-18 tarde (PR 48 y 49 en main: la detección falla antes que la altura)

> Reemplaza como estado vigente al bloque "## 0-prev3" de abajo, que se conserva. Verificado al
> escribir: `main` remoto = `a9f2819` (`git ls-remote`), sin PR abiertos fuera del de este traspaso
> (`gh pr list`), Space de HF `fd8d8ff` RUNNING (API de HF: sigue sin el texto del PR 45).

| Qué | Estado | Evidencia |
|---|---|---|
| Por qué VOLCAT ve Chillán y nosotros no | **En `main`** (PR 48, merge `effd4eb`) | `docs/own_volcat/POR_QUE_VOLCAT_VE_Y_NOSOTROS_NO.md`. Falsadas: umbral más bajo, paralaje (también el 28-10), 8,5 µm, luz solar. Abiertas: H3 (cielo despejado GFS + RTM y β con C10), H2 (trato especial cerca de volcanes), H6 (¿es ceniza?) |
| Validación de magnitud, pasos 3 a 6 | **En `main`** (PR 49, merge `a9f2819`) | plan §3.7 y `docs/own_volcat/validacion_magnitud/`. 122 escenas VOLCAT ancladas, 12 excluidas a ojo antes de medir, quedan 110. Altura propia en **1 de 110** (Reventador 07-11 20:40 UTC, 1 píxel: 11,2 a 14,8 km contra 7 a 8 km de VOLCAT, no se cruzan). En 109 la máscara `detect_ash_enhanced` queda vacía |
| Volcanes VOLCAT fuera de la RNVV (Olca, Aucanquilcha, Putana, Ojos del Salado, Cerro Azul, Lautaro) | **Cerrado: quedan fuera** (decisión de Nicolás 18-11) | catálogo = 43 RNVV + Lastarria. No reproponer |
| Hugging Face | build `d62753a`, sin el PR 45 (sólo texto) | desplegar con el próximo cambio de código |

**Lectura de conjunto.** La altura propia no se puede validar contra VOLCAT porque falla antes la
detección: en Sabancaya 01-11, a 15 km del volcán, BT11 mínima 264,1 K y BTD mínima -0,56 K. Es la
misma pluma tibia y semitransparente sin firma split-window que se midió en Chillán. El siguiente paso
de la magnitud depende de la detección, es decir de H3.

**Lo aprendido**

- Al contar resultados de un lote partido, contar escenas **resueltas**, no entradas en los archivos:
  dije "109 de 109" cuando había 72 y el resto se relanzó. El total salió de las partes más
  `propios.json` (110), comprobado contra `volcat_lecturas.json` y `exclusiones.json`.
- Una sesión lateral que se cae por red (ENOTFOUND) deja el cálculo en disco: revisar los archivos
  y reanudarla, no relanzar desde cero.

**Decisiones que esperan a Nicolás**

| # | Pregunta | Recomendación |
|---|---|---|
| 1 | ¿Pedir al OVDAS horas de pulsos en cámara y REAV del 25 y 28-10 y del 08, 10, 11 y 14-11? | Sí: es lo único que dice si VOLCAT acierta (H6) |
| 2 | ¿Atacar H3 (β con GFS + RTM y C10, 1 a 2 días)? | Sí, empezando por el 28-10 nocturno, que descarta lo solar |
| 3 | ¿Desplegar `main` a HF? | Con el próximo cambio de código: lo pendiente es sólo texto |

**Prompt para la próxima sesión**

```
/retomar en Goes (C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\Goes).
1. Verifica: git fetch; git ls-remote origin -h refs/heads/main; gh pr list; API de HF (sha y stage).
2. Lee STATUS.md "## 0.", docs/own_volcat/POR_QUE_VOLCAT_VE_Y_NOSOTROS_NO.md §3.1 y §6 y
   docs/own_volcat/PLAN_VALIDACION_MAGNITUD.md §3.7.
3. Si Nicolás aprobó H3: escribe el criterio antes de medir; agrega C10 (7,3 µm) a la ventana del cache
   para la huella VOLCAT del 28-10 22:40 a 23:40 UTC y del 14-11; calcula ε(11), β(12/11), β(8,5/11) y
   β(7,3/11) contra un cielo despejado con perfil GFS y un modelo radiativo (no hay RTM en el repo:
   evaluar opciones antes de instalar nada). Scripts previos en
   C:\Users\nmend\AppData\Local\Claude-Data\claude_pzs8sxrjxfjjc\side-session-notes\local_f3a7d295-ddde-4b7c-b258-25e760c44266
Sin VIIRS, sin guiones largos, ficha SDA en el mismo commit si cambia lógica, fusionar o desplegar
sólo con el sí de Nicolás por PR, docs/auditoria_2026-11 no se sube.
```

---

## 0-prev3. Cierre 2026-11-18 (pasos 2, 3 y 4: el sol NO explica por qué VOLCAT ve Chillán)

> Reemplaza como estado vigente al bloque "## 0-prev2" de abajo, que se conserva. Todo en la rama
> `docs/por-que-volcat-ve-chillan` (PR 48, sólo docs, sin fusionar). Detalle en
> `docs/own_volcat/POR_QUE_VOLCAT_VE_Y_NOSOTROS_NO.md` §3.1; criterios y scripts en la carpeta de notas.

- **Paso 4 (H1 a): falsada.** El 29-10, de 01:00 a 01:20 UTC (cenit 110 a 113°), VOLCAT dibuja objetos
  anclados al cráter en tres cuadros seguidos; es un episodio continuo desde las 21:50 UTC del 28-10.
  En la huella, el IR no tiene frío ni BTD negativa (mínimo −0,19 K). SSEC sólo publica desde el 25-10.
- **Paso 2 (H1 b): falsada.** C02, C07 y C14 en 46 positivos con sol alto: ρ(3,9/0,65), r065 y sd065
  dan AUC 0,50 contra control pareado por BT11 (mismo lugar y hora, día sin pluma).
- **Paso 3 (H2): no concluyente.** R = 3,2 por el 16-11; sin él, R = 0,52 (objetos chicos nocturnos
  lejos de volcanes en Cuyo, probable polvo).
- **Vigente:** H3 (cielo despejado modelado con GFS + RTM y razones β, incluida β(7,3/11) con C10, que
  nunca probamos). Paso 5 (prototipo diurno) descartado. Cita SECO Part 1 corregida a 2015.

**Decisiones que esperan a Nicolás**

| # | Pregunta | Recomendación |
|---|---|---|
| 1 | ¿Fusionar el PR 48 (sólo docs)? | Sí |
| 2 | ¿Pedir al OVDAS horas de pulsos en cámara y REAV del 25 y 28-10 y del 08, 10, 11 y 14-11? | Sí: sigue siendo lo único que dice si VOLCAT acierta (H6) |
| 3 | ¿Atacar H3 (paso 6: β con GFS + RTM, 1 a 2 días)? | Sí, empezando por el 28-10 nocturno, que descarta lo solar |

**Prompt para la próxima sesión**

```
/retomar en Goes (C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\Goes).
Lee STATUS.md "## 0." y docs/own_volcat/POR_QUE_VOLCAT_VE_Y_NOSOTROS_NO.md §3.1 y §6. Si Nicolás aprobó el
paso 6 (H3): escribe el criterio antes de medir; agrega C10 (7,3 µm) a la ventana del cache para la huella
VOLCAT del 28-10 22:40 a 23:40 UTC y del 14-11; calcula ε(11) y β(12/11), β(8,5/11), β(7,3/11) contra un
cielo despejado con perfil GFS y un modelo radiativo (no hay RTM en el repo: evaluar opciones antes de
instalar nada). Scripts y criterios de esta tanda en
C:\Users\nmend\AppData\Local\Claude-Data\claude_pzs8sxrjxfjjc\side-session-notes\local_f3a7d295-ddde-4b7c-b258-25e760c44266
Sin VIIRS, sin guiones largos, ficha SDA en el mismo commit si cambia lógica.
```

---

## 0-prev2. Cierre 2026-11-17 noche tarde (por qué VOLCAT ve las plumas de Chillán y nosotros no)

> Reemplaza como estado vigente al bloque "## 0-prev. Cierre 2026-11-17 final" de abajo, que se
> conserva. Verificado al empezar: `main` remoto = `4a2d617`, sin PR abiertos, Space de HF `fd8d8ff`
> RUNNING (build de `d62753a`, sin el texto del PR 45). Disco: 20 GB libres.

**Entregable:** `docs/own_volcat/POR_QUE_VOLCAT_VE_Y_NOSOTROS_NO.md` (rama
`claude/investigacion-volcat-deteccion-f4df71`, PR de sólo documentación). Sin cambio de código.

- **Hallazgo principal (de los papers, DOI verificados):** VOLCAT/SECO no es sólo IR. De día usa
  ρ(3,9/0,65) y el visible de 0,65 µm, y acepta objetos de 0 a 25 píxeles a menos de 5, 10 o 50 km de
  un volcán (SECO Part 2, Tabla 4). En 2015 SECO no vio plumas de Kizimen y Karymsky con BT11 igual al
  cielo despejado: el mismo síntoma de Chillán.
- **Medido hoy:** las 58 detecciones VOLCAT ancladas al cráter (sin el 16-11) son de día (15:00 a
  23:20 UTC), 0 en 16 noches. Prueba A (huella corrida por paralaje): falsada, no hay señal fría en
  ningún corrimiento de hasta 5 px. Prueba B (8,5 µm): falsada, AUC 0,26. Ambas con nulo de días
  nublados, dicho en el informe. Criterio y script en la carpeta de notas de la sesión
  (`criterio_corrimiento_y_8p5_2026-11-17.md`, `prueba_AB.py`).
- **Hipótesis vigente (SOSPECHA, no confirmada):** VOLCAT ve estas plumas por los canales solares
  más el trato especial al cráter. Son 5 episodios; que todos caigan de día por azar tiene ~8 %.

**Decisiones que esperan a Nicolás**

| # | Pregunta | Recomendación |
|---|---|---|
| 1 | ¿Fusionar el PR de docs de esta sesión? | Sí: sólo agrega el informe, una fila del README y este traspaso |
| 2 | ¿Pedir al OVDAS horas de pulsos en cámara y REAV del 08, 10, 11 y 14-11? | Sí: es lo único que dice si VOLCAT acierta (H6) |
| 3 | ¿Siguiente medición? | Paso 2 del plan: C02 + C07 en la ventana del cache y ρ(3,9/0,65), con criterio escrito antes |

**Prompt para la próxima sesión**

```
/retomar en Goes (C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\Goes).
Lee STATUS.md "## 0." y docs/own_volcat/POR_QUE_VOLCAT_VE_Y_NOSOTROS_NO.md. Si Nicolás aprobó,
ejecuta el paso 2 del plan (§6): agrega C02 (0,64 µm) y C07 (3,9 µm) a la ventana del cache del
detector para los 58 positivos y días negativos a la misma hora (mide el disco con un ensayo antes),
escribe el criterio antes de medir y calcula ρ(3,9/0,65) restando la emisión térmica con BT11.
Cache y scripts: C:\Users\nmend\AppData\Local\Temp\claude\d6ea8719dcf88502\536a0873-47fb-4b33-9ee5-de0197c3f321\scratchpad\det
(es scratch y puede haberse borrado; si no está, rehacer con fetch_mp.py, ver INFORME_variantes.md).
Sin VIIRS, sin guiones largos, ficha SDA en el mismo commit si cambia lógica.
```

---

## 0-prev. Cierre 2026-11-17 final (PR 45 en main, detector propio medido, próxima: por qué VOLCAT ve y nosotros no)

> Reemplaza como estado vigente al bloque "## 0-prev. 2026-11-17 cierre de noche" de abajo, que
> se conserva. Verificado al escribir: `main` local = remoto = `8b4f3c1` (`git ls-remote`), sin PR
> abiertos (`gh pr list`), Space de HF `fd8d8ff` RUNNING. **Estado fijado con trabajo en curso:**
> la sesión "Goes: detector propio que vea plumas débiles (Chillán)" estaba abriendo un PR solo de
> documentación (resultado del detector en `docs/own_volcat/PLAN_VALIDACION_MAGNITUD.md`). Revisar
> `gh pr list` antes de creerle a la fila de PR abiertos.

### a. Todo en una pantalla

| Qué | Estado | Evidencia |
|---|---|---|
| Texto de atraso de SSEC en la página VOLCAT (decía 3 a 6 min) | **En `main`**, sin desplegar | PR 45, merge `8b4f3c1`; medido 34,6 min el 17-11 |
| Traspaso + hallazgos Chillán §3.4 y §3.5 | **En `main`** | PR 44, merge `a8f493c` |
| Hugging Face | RUNNING con el build de `d62753a`: **sin el PR 45** (sólo texto) | API de HF; desplegar espera el sí de Nicolás |
| Detector propio para plumas débiles | **Medido, ninguna variante cumple el criterio**; sin PR de código | informe `C:\Users\nmend\AppData\Local\Claude-Data\claude_pzs8sxrjxfjjc\side-session-notes\local_f3a7d295-ddde-4b7c-b258-25e760c44266\INFORME_variantes.md`; rama `claude/detector-plumas-debiles-a13f64` |
| PR de docs del detector | **En curso** al cerrar (otra sesión) | ver aviso arriba |
| Chillán 14-11: VOLCAT 8 a 12 km | explicado: sobreestimación semitransparente, BT11 nunca bajo 271 K | plan §3.5 |
| Umbral de manto `MAX_SECTOR_FRAC` | falla reproducida, sin cambio | plan §3.4 |
| Volcanes VOLCAT con coordenadas GVP | no empezado | sin rama |
| Validación VOLCAT pasos 3 a 6 | no empezados | criterio decidido (cruce de intervalos) |

### b. Decisiones que esperan a Nicolás

| # | Pregunta | Opciones | Recomendación |
|---|---|---|---|
| 1 | ¿Desplegar `main` (PR 45) a HF? | ahora / con el próximo cambio | Con el próximo cambio de código: es sólo texto |
| 2 | Umbral de manto (plan §3.4) | (a) km² del objeto, (b) nacer en el cráter, (c) exclusión a ojo | (c) para el paso 3; (b) si la lectura VOLCAT llega a la app |
| 3 | ¿Fusionar el PR de docs del detector cuando llegue? | sí / revisar antes | Sí, si sólo toca el plan y cada número tiene fuente |

### c. Lo aprendido

- **Patrón de defecto (propuesto para `CLAUDE.md`, Filosofía operacional):** nuestro detector
  (BTD < -1 K, Prata 1989) no ve plumas chicas de Chillán que VOLCAT sí ve. Dentro de la huella
  VOLCAT la BTD mediana queda en +0,02 a +0,31 K respecto del cielo despejado; bajar el umbral o
  usar anomalía temporal da 15 % de falsas alarmas y sólo 25 % de coincidencia espacial. **No
  volver a proponer "bajar el umbral BTD" sin leer antes el informe del detector.**
- **Trampa de medición:** "píxeles altos de VOLCAT = ceniza alta" es falso cuando la escena no tiene
  nada frío: el 14-11 la BT11 mínima fue 271 K y una nube opaca a 8 km estaría a 249 K. Antes de
  usar una altura VOLCAT, comparar con la BT11 mínima del entorno.
- **Regla de método (vale para todo el workspace):** un umbral en fracción de imagen (5 % del
  sector, 3 píxeles del PNG) no es una medida física; dos veces en esta semana el mismo error dio
  topes falsos. Medir en km o km² del terreno.
- **CI:** un fallo por timeout del checkout no es una prueba roja; mirar qué paso falló
  (`gh run view --json jobs`) antes de diagnosticar, y relanzar.

### d. Problemas abiertos e hipótesis

- **CONFIRMADO:** `detect_ash_enhanced` da 0 píxeles de ceniza en los 9 scans revisados del 14-11 y
  en los cuadros VOLCAT de prueba del detector.
- **CONFIRMADO:** VOLCAT da 8 a 12 km el 14-11 de 16:20 a 18:20 (hora de Chile) sobre la pluma, sin
  ningún píxel IR bajo 271 K en 25 km.
- **CONFIRMADO:** `volcat_object_heights` da 16 a 18 km para Chillán el 16-11 por un sistema
  meteorológico (3 a 4 % del sector).
- **SOSPECHA:** VOLCAT detecta estas plumas porque usa un fondo de cielo despejado modelado
  (transferencia radiativa) y razones β con 8,5, 11 y 12 µm (quizás 10,3 µm), no un umbral de BTD.
  Es lo que la próxima sesión tiene que comprobar en los papers.
- **SOSPECHA:** los cirros delgados del 14-11 influyen en las alturas altas de VOLCAT (coinciden en
  hora, pero también hay uno a las 19:20 sin altura alta).
- **SOSPECHA:** la franja que sale al SE del cráter en Ash RGB y en la anomalía de fondo es nieve de
  la cresta (aparece también el 12-11, día sin ceniza).

### e. Cerrado, no rehacer

- PR 36 a 45 en `main`. Mínimo del tope = 12 km² del sensor (PR 43). Texto de atraso (PR 45).
- VOLCAT Chillán 01 a 16-11 leído a 10 min: pulsos 08, 10, 11 y 14-11. MP4 en `C:\Users\nmend\Downloads\`
  (16 días, 4 días con pluma, mosaico de los 4 pulsos con anillos de 10, 25 y 50 km).
- Variantes de detector V0 a V3 medidas con criterio previo: ninguna cumple. No repetir sin una idea
  nueva (bandas 8,5 y 10,3 µm, fondo modelado, GFS archivado).
- La Regla 📏 ya existe en la grilla del volcán, en el loop VOLCAT ("Medir sobre un cuadro del
  loop") y en Replay: no es un pendiente.

### f. Prompt para la próxima sesión

```
/retomar en Goes (C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\Goes).
1. Verifica antes de creer: git fetch; git ls-remote origin -h refs/heads/main; gh pr list;
   API de HF (sha y stage). Si hay un PR de docs del detector abierto, revísalo y pide el sí.
2. Lee en orden: CLAUDE.md del proyecto, STATUS.md "## 0.", docs/own_volcat/PLAN_VALIDACION_MAGNITUD.md
   §3.4 y §3.5 (y la sección del detector si ya entró), y el informe
   C:\Users\nmend\AppData\Local\Claude-Data\claude_pzs8sxrjxfjjc\side-session-notes\local_f3a7d295-ddde-4b7c-b258-25e760c44266\INFORME_variantes.md
3. Tarea: entender por qué VOLCAT ve ceniza en Chillán (nov-2026) que nuestro detector no ve, y
   cómo atacarlo. Usa la skill `investigacion` (agotar lo local primero: docs/own_volcat/ tiene el
   ATBD GOES-R VolAsh v3.0, Pavolonis 2020, Saint 2024, VADUGS) y busca Pavolonis 2010 (β-ratios),
   2013 (altura) y 2015 (detección automática SECO). Varias perspectivas: física radiativa (fondo
   de cielo despejado modelado vs umbral), estadística (pruebas de VOLCAT), operación (qué falso
   positivo tolera un observatorio) y datos (bandas ABI 8,5, 10,3, 11, 12 y 13,3 µm). Usa
   `multi-perspective`, `devils-advocate` y `deep-research` si sirven.
4. Entregable: informe con hipótesis ordenadas por evidencia, qué prueba falsaría cada una con los
   datos que ya hay (huellas VOLCAT en grilla ABI, ~978 scans en cache de la sesión del detector) y
   un plan con costo. No cambies código de detección sin criterio declarado antes de medir.
Reglas: SDA CPLT 372 (ficha en el mismo commit que la lógica); sin VIIRS; sin guiones largos;
fusionar o desplegar sólo con el sí de Nicolás por PR; rutas absolutas; docs/auditoria_2026-11 no
se sube. Si la sesión no alcanza: deja el informe parcial en docs/own_volcat/ y cierra con /cierre.
```

---

## 0-prev. 2026-11-17 cierre de noche (PR 43 en main, Chillán a 10 min, umbral de manto)

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
