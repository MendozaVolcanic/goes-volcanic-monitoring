# STATUS — Goes Dashboard

**Última actualización:** 2026-08-30 (auditoría adversarial)
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

## 0. Cierre de sesión 16-11-2026: validación de magnitud contra VOLCAT (pasos 0 a 2)

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
