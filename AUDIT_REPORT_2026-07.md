# Auditoría completa — julio 2026 (VOLCAT propio + proyecto)

**Fecha:** 2026-07-01 · **Método:** 6 auditores especializados en paralelo (física,
código nuevo, tests, docs+compliance, fuentes de datos, CI/CD) + salud de producción
+ **verificación adversarial independiente** de los hallazgos ALTA (2 verificadores
con mandato de refutar). Scope: todo lo nuevo desde la auditoría de jun-2026
(`AUDIT_REPORT.md`) — la cadena VOLCAT propia completa — más compliance y fuentes.

**Veredicto global:** la física base del retrieval propio es **defendible como
producto INDICATIVO** (signos, convenciones, Planck, rama monótona, guards de
honestidad: todos verificados OK). Se confirmaron **2 defectos físicos ALTA que
engañan activamente** (árbitro CO₂ y β de microfísica), 1 MEDIUM de código, deuda
vinculante de compliance CPLT, y varios problemas de CI/CD. Producción sana
(HF RUNNING, app 200 OK, crons frescos).

---

## HALLAZGOS CONFIRMADOS (verificación adversarial superada)

### Física (los 2 que engañan activamente)

**F1 [ALTA · CONFIRMADO] Árbitro CO₂ degenerado — `wen_rose_height.py`**
BTD(11−13.3) con umbral absoluto 0.5 K NO distingue "fina y alta" (+10…+15 K) de
"OPACA y BAJA" (+8…+14 K a 4 km). El umbral es tan bajo que hasta una opaca a 10 km
(+1…+3 K) pasa como "semitransparente" → el badge "CO₂ ✓" del dashboard aparece casi
siempre (sin valor discriminante) y el flag "el tope real puede ser MAYOR" + extensión
de `top_hi` a la tropopausa se emiten rutinariamente en el modo dominante chileno
(emisión débil 2-5 km) siendo falsos. El docstring ("opaca ⇒ BTD≈0") solo vale cerca
de la tropopausa. **Nota retroactiva:** debilita el "CO₂ ✓" de las validaciones
previas (confirmador que confirma casi todo); no invalida los topes headline (cota
conservadora).
**Fix corto plazo:** gate por altura + reescribir el flag a lenguaje ambiguo ("el CO₂
no distingue fina-alta de opaca-baja"), nunca "confirma". **Mediano plazo (Fase 3d
candidata):** cociente CO₂-slicing ΔR₁₃.₃/ΔR₁₁ (Menzel 1983) — cancela emisividad,
método heritage de altura; o comparar contra BTD esperado para opaca a la altura de
la cota.

**F2 [ALTA · CONFIRMADO] β=0.9 inconsistente + cita fantasma — `wen_rose_height.py:51-52`**
`t12=t11^β` ⇒ β = τ12/τ11 = exactamente el β(12,11) de Pavolonis (verificado: el secθ
cancela en el ratio; el ancla 0.564 ya es el valor efectivo scattering-corregido).
β=0.9 corresponde a r_eff≈8-10 µm (ceniza gruesa proximal — justo donde el guard ya
revierte); la ceniza fina distal (r_eff~2 µm, el caso donde Wen-Rose importa) tiene
β≈0.56, FUERA de BETA_RANGE (0.85,0.95) → banda de microfísica subestimada ~4× y
**headline sesgado ALTO** para ceniza fina (β menor ⇒ menos corrección). Además la
cita "β=0.9 (Wen-Rose Fig.1)" es **fantasma**: el paper no define ningún β (la
parametrización es del linaje cirrus Inoue/Parol); ironía: el caso de validación del
propio paper (Spurr) retrievea r_eff=2-2.5 µm ⇒ β≈0.56.
**Fix:** BETA_RANGE=(0.55, 0.95) + β central ≈0.7 (r_eff~4-5 µm) + usar el
`beta_12_11` MEDIDO solo como flag cualitativo ("ceniza fina: mitad baja de la
banda"). **REFUTADO** el fix de alimentar β medido al solver: es circular exacto
(Tc=tropopausa se vuelve raíz exacta → atractor runaway). Aceptar que la banda ancha
degradará confianza casi siempre — ese ES el contenido de información real de un
retrieval IR 2-canales (consistente con Saint 2024).

### Física (media/baja, sin verificación extra — riesgo acotado)

- **F3 [MEDIA]** Wind-shear: pluma ADJUNTA en emisión continua (centroide quieto con
  viento fuerte → altura baja falsa). Guard faltante: rechazar adv < ~3 m/s /
  desplazamiento < 1-2 px; trackear leading edge a futuro. (Módulo NO cableado aún.)
- **F4 [MEDIA]** Parallax sin corregir: ~1.1-1.3 km de corrimiento por km de altura a
  −40°S. Afecta georef de la pluma en mapa (ubicación vs poblados) y mete 2-4 m/s
  espurios en wind-shear si la columna sube; NO afecta topes térmicos. Fix de 1er
  orden: Δ=h·tanθ hacia el subsatélite usando el propio top_km.
- **F5 [BAJA]** β-ratios: distancia euclídea sin normalizar (eje β12/11 pesa 2.3×) →
  ceniza gruesa proximal puede clasificar "hielo" → flag falso en fase eruptiva.
- **F6 [BAJA]** Wind-shear evalúa cizalla hasta 30 hPa (24 km): limitar a
  superficie-tropopausa.

### Código (nuevo desde jun-2026)

- **C1 [MEDIA · CONFIRMADO por mí]** `wind_shear._ash_mask_at` NO valida bandas del
  mismo scan (wen_rose sí) → máscara espuria con S3 a medio subir → altura falsa con
  status ok. Fix: replicar guard / extraer helper compartido.
- **C2 [BAJA]** `except → age_h=0` anula el guard de viento viejo si Open-Meteo cambia
  el formato de hora → rechazar en el except.
- **C3 [BAJA]** Título del mapa puede llevar timestamp de OTRO scan (usa `primary`
  ACHA, plotea `fld` Wen-Rose). Fix: `fld.get("scan_dt")`.
- **C4 [BAJA]** validate_fase3b crashea si tropopausa None (formateo defensivo).
- **C5 [BAJA]** `solve_tc_grid` pico ~300 MB con radius 1.5° ×3 por barrido β →
  float32/del intermedios.
- ✅ Verificados OK: sin cache_data anidado, picklabilidad, call sites 3-tupla,
  estados parciales del viewer, timezone, flujo ts_k=None.

### Compliance CPLT N°372 (VINCULANTE — Goes es SDA en producción)

- **P1 [ALTA]** NO existe `docs/FICHA_SDA_GOES.md` (guía §4). Crear.
- **P2 [ALTA]** Los 5 módulos del retrieval sin cabecera "FICHA SDA" Nivel 1 (§3).
- **P3 [MEDIA]** Falta trigger one-liner SDA en `Goes/CLAUDE.md` (§5.2).
- ✅ Nivel 2 (comentarios qué+por qué) cumplido de forma ejemplar — la ficha es tarea
  de FORMATO, el contenido ya existe en docstrings.

### CI/CD (verificados por mí contra los YAML)

- **W1 [ALTA]** `hires_visible_cache.yml`: cron */10 + timeout 15 + SIN `concurrency`
  → runs solapados corrompen releases rolling. Fix: concurrency group + timeout 9.
- **W2 [ALTA]** `keepalive_streamlit.yml` ZOMBIE (apunta a streamlit.app muerto).
  Fix: retarget a HF con curl liviano (HF despierta por HTTP) o borrar.
- **W3 [MEDIA]** Bots: `git pull --rebase -X ours` favorece a UPSTREAM en rebase
  (semántica invertida — descarta el JSON recién construido en conflicto) + `push ||
  true` silencioso. Fix: loop retry sin -X ours ni || true.
- **W4 [MEDIA]** `frp_timeline.yml` mismo race (cron */10, timeout 20, sin
  concurrency).
- **W5 [MEDIA]** tests.yml en Python 3.11 ≠ 3.12 de producción (CI nunca prueba el
  intérprete real). + paths no incluye scripts/**.
- **W6 [BAJA]** Releases backfill sin poda; ventana de 404 en delete-then-upload;
  inputs sin quote-hardening.

### Tests (suite verificada: 129 passed, 0 fallos)

- **T1 [ALTA]** Orquestación `wen_rose_top_height` (~300 líneas) solo testeada con
  volcán inexistente — "intercambiar coefs 14/15 pasaría la suite". Fix: test
  sintético con monkeypatch (viable sin red, receta en el informe del auditor).
- **T2 [MEDIA]** Guards del viento (MAX_ADV_MS, MAX_WIND_AGE_H — nacidos de fallo
  real) 0% cubiertos.
- **T3-T8**: _revert_unreliable, _top_stats capped, β con ash_mask de producción,
  ts_k fallbacks, interacción CO₂×revert, goes_s3 core sin test funcional.
- Limpieza: `_net_ok()` muerto en 2 archivos de test.

### Docs (drift)

- **D1** FASE3B §2: dice "bisección [tropopausa, BT11]" — código usa grid-argmin
  [180 K, BT11]. + cita fantasma β=0.9 Fig.1 (corregir con F2).
- **D2** FASE3B item 4: "β-ratios gated por RTM" — stale, ya implementado.
- **D3** PLAN_VOLCAT_PROPIO: falta Fase 3c + β-ratios + CO₂ en el estado.
- **D4** INTEGRATION.md: falta wind_shear_height y composition.
- **D5** CLAUDE.md stale: goes.yml "corre cada 10 min" (cron muerto 2026-05-15),
  frp "cada hora" (es cada 10 min), lascar_pdf "11:00 UTC" (manual).
- ✅ GUIA_REVISION_DASHBOARD: sin drift.
- AUDIT_REPORT.md jun: críticos arreglados de facto; ~50 low/medium vigentes como
  backlog; marcar ~10 resueltos.

### Fuentes de datos NUEVAS (verificadas con requests reales 2026-07-01)

| Fuente | Aporta | Prioridad |
|---|---|---|
| **ABI-L2-LVTPF/LVMPF** (mismo bucket S3, cada 10 min) | Perfil T(z) del PROPIO GOES — mejora directa del mapeo Tc→altura sin depender de GFS | **Alta** |
| **Radiosondas Wyoming** (Pto Montt 85799 etc.; endpoint NUEVO `/wsgi/` — el `/cgi-bin/` viejo da 404) | Verdad MEDIDA para validar T(z)+viento | **Alta** |
| **GFS archive AWS `noaa-gfs-bdp-pds`** (byte-range, ≥2021) | Destraba validación histórica (Open-Meteo da null en niveles pasados — verificado) | **Alta** |
| NUCAPS NOAA-21 (latencia ~37 min) | Sondeos satelitales T/q | Media |
| NOAA CLASS VAAF GOES-16 2019-20 (NetCDF) | Validación histórica de ceniza | Media |
| EarthCARE ATLID (cuenta gratuita) | Gold standard a posteriori | Baja |
| Descartados con evidencia: Himawari/MSG (geometría), VIIRS FIRMS (duplica VRP), VAAC estructurado (no existe), Open-Meteo histórico (null verificado) | | |

### Producción (verificada en vivo)

✅ HF Space RUNNING · app 200 OK 0.7 s · frp_timeline fresco (1 min) · sin tokens
hardcodeados. goes.yml cron desactivado deliberadamente (documentado en el YAML).

---

## PLAN DE FIXES POR OLAS (propuesto)

- **Ola 1 — Seguridad del mensaje (física confirmada):** F1 (CO₂: gate por altura +
  flag ambiguo + badge honesto) + F2 (BETA_RANGE 0.55-0.95, β central 0.7, β medido
  como flag, corregir cita fantasma) + C1 (guard mismo-scan en wind_shear) + C2/C3.
  Con TDD; redeploy.
- **Ola 2 — Compliance vinculante:** P1 (FICHA_SDA_GOES.md) + P2 (cabeceras Nivel 1
  en 5 módulos) + P3 (trigger en CLAUDE.md).
- **Ola 3 — CI/CD:** W1 (concurrency hires) + W2 (keepalive→HF curl) + W3/W4 (push
  de bots) + W5 (Python 3.12 + paths).
- **Ola 4 — Tests:** T1 (orquestación sintética) + T2 (guards viento) + T4/T5.
- **Ola 5 — Docs:** D1-D5 + marcar resueltos en AUDIT_REPORT jun.
- **Ola 6 — Fuentes (features nuevos):** LVTPF como perfil alternativo + validador
  de radiosondas Wyoming + fetcher GFS archive para validación histórica.
- **Fase 3d candidata (mediano plazo):** CO₂-slicing por cociente de radiancias
  (Menzel 1983) — el heritage method; cancela emisividad, daría altura directa.
