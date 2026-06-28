# Fase 0 — Altura de pluma propia con ACHA (arranque)

> Objetivo: producto de **altura del tope de pluma cuantitativa, propio y más
> rápido que VOLCAT/SSEC**, con CERO dependencias nuevas. Etiquetado como
> **INDICATIVO** (no reemplaza al VOLCAT de SSEC; lo complementa con menor
> latencia). Esfuerzo estimado: **1–2 días**. Ver el plan completo en
> [`PLAN_VOLCAT_PROPIO.md`](PLAN_VOLCAT_PROPIO.md).

## Qué es y por qué funciona

NOAA publica su producto **Cloud Top Height (ACHA, algoritmo Heidinger optimal
estimation)** en el mismo bucket `noaa-goes19` que ya usamos. ACHA da la altura
del tope de *cualquier* nube; si la **enmascaramos con nuestra detección de
ceniza tri-espectral** (que ya tenemos), aislamos el tope de la **pluma
volcánica**. No es el VOLCAT completo (no hace microfísica ni masa/reff), pero da
una **altura del tope defendible** a ~13 min de latencia (vs 30–50 de SSEC).

## Datos (VERIFICADO 2026-06-28)

| Producto S3 | Resolución | Variable | Para qué |
|---|---|---|---|
| **`ABI-L2-ACHA2KMF`** | **2 km** (5424×5424 full disk) | `HT` (m, 0–17.6 km), `DQF` | **altura del tope — usar este** |
| `ABI-L2-ACHTF` | 2 km | `TEMP` (K) | temperatura del tope (para Fase 2: Teff→z) |
| `ABI-L2-ACHAF` | **10 km** (1086×1086) | `HT` | NO usar — demasiado grueso |

- Bucket: `noaa-goes19/ABI-L2-ACHA2KMF/<YYYY>/<DOY>/<HH>/OR_ABI-L2-ACHA2KMF-M6_G19_s..._e..._c....nc`
- Cadencia: 10 min. Latencia: ~13 min (timestamp `c` = creación). Tamaño: ~varios MB.
- Proyección: **GOES-R ABI fixed grid (geos)**, `goes_imager_projection`
  (lon_origin=−75.0, H=35786023.0) — **idéntica a FDCF**. Georef con pyproj geos
  (ya implementado).
- Acceso: `s3fs(anon=True)` + `xarray` — **ya son deps del proyecto**.

## El atajo: clonar `goes_fdcf.py`

`ABI-L2-ACHA2KMF` tiene la MISMA estructura que `ABI-L2-FDCF` (hot spots), que ya
fetcheamos y georeferenciamos en [`src/fetch/goes_fdcf.py`](../../src/fetch/goes_fdcf.py).
El fetcher + georef de ACHA es ~copiar ese módulo, cambiar producto a
`ABI-L2-ACHA2KMF` y leer la variable `HT` (en vez de los flags FDC).

## Piezas que YA existen (reusar, no reescribir)

- `src/process/ash_detection.py`: `compute_btd_split_window`, `detect_ash_basic`,
  **`detect_ash_enhanced`** (tri-espectral, ESTE es el que da la máscara de
  ceniza), `compute_ash_confidence`.
- `src/fetch/goes_s3.py`: `download_band_at(dt, band)`, `download_volcanic_bands(dt)`
  (baja las bandas volcánicas), `_time_to_s3_path(product, dt)`, `list_files`,
  `get_latest_time`, `open_band`. Las bandas para la máscara: **C11 (8.4µm),
  C14 (11.2µm), C15 (12.3µm)** — ya las bajamos para el Ash RGB.
- `src/fetch/goes_fdcf.py`: patrón fetch+georef de un L2 geos full-disk (TEMPLATE).
- Coeficientes Planck: del NetCDF L1b (ya se usan en `src/process/`).

## Plan de implementación (TDD)

1. **Test primero** (`tests/test_acha.py`): bajar un gránulo ACHA2KMF reciente,
   abrir con xarray, assert `HT` existe, dims 5424×5424, units `m`, rango 0–18000.
   (Smoke contra la red, como otros tests de fetch.)
2. **`src/fetch/goes_acha.py`** (clonar `goes_fdcf.py`):
   `fetch_acha_height_at(dt, bounds) -> {"height_m": np.ndarray, "bounds": ...}`
   — baja el gránulo más cercano a `dt`, recorta a `bounds` del volcán (geos→latlon),
   aplica `DQF` (quedarse con calidad buena/aceptable).
3. **`src/process/acha_plume_height.py`**:
   `plume_top_height(dt, volcano, radius_deg) -> {"top_km", "mask_px", "field"}`
   — baja C11/C14/C15 (`download_volcanic_bands`), arma la máscara con
   `detect_ash_enhanced`, baja ACHA `HT`, intersecta máscara ∩ HT, reporta el tope
   (p95 o max de HT sobre los píxeles de ceniza) + el campo para mapear. Si la
   máscara está vacía → "sin pluma detectada".
4. **Dashboard**: producto/overlay nuevo en la vista de altura, **etiquetado
   "INDICATIVO · ACHA NOAA enmascarado por ceniza · no es VOLCAT"**. Latencia y
   fuente visibles. Mantener VOLCAT/SSEC como primario.
5. **Validación**: caso reciente con pluma (revisar blog SSEC o un evento Chillán/
   Villarrica/Láscar del archivo ~28 días). Sanity: HT razonable (km), máscara
   no vacía, latencia < VOLCAT. Comparar el tope ACHA-enmascarado vs el VOLCAT
   altura del mismo scan (deberían quedar en el mismo orden).

## Honestidad / límites

- ACHA es altura de tope de NUBE genérica (Heidinger OE), no ceniza-específica.
  La máscara de ceniza la aporta nuestra detección tri-espectral. Si hay nube
  meteo sobre/junto a la pluma, puede contaminar → reportar como INDICATIVO.
- Resolución térmica = 2 km nativa de ABI (igual que VOLCAT regional; el límite
  físico no baja por usar ACHA).
- No da masa ni reff (eso es Fase ≥1 con C10/C16 + microfísica).

## Estado de implementación — HECHO (2026-06-28)

Implementado con TDD (`tests/test_acha.py`, 6 tests; suite total 72 → **80 verde**):

- **`src/fetch/goes_acha.py`** — `fetch_acha_height_at(dt, bounds, keep_dqf={0,1,4})`.
  Clona el patrón geos de `goes_fdcf.py`. Recorta por índices geos (sin meshgrid
  full-disk) → baja memoria. DQF: conserva good+marginal+**opaque** (4 es fiable
  para plumas densas, emisividad ≈ 1). Verificado: grilla x/y IDÉNTICA a RadF 2 km
  (`max_abs_diff=0.0`) → intersección pixel a pixel sin remuestrear.
- **`src/process/acha_plume_height.py`** — `plume_top_height(dt, volcano, radius)`.
  Baja C11/C14/C15 del MISMO scan (`download_band_at`), máscara
  `detect_ash_enhanced`, intersecta con HT, reporta tope **p95** (robusto) + max +
  campo. `_plume_top_stats` es función pura unit-testeada. Status: `ok` /
  `no_plume` / `no_data`.
- **Dashboard** — sección INDICATIVA en la vista de altura (`volcat_viewer.py`,
  modo Volcán), detrás de botón + cache 10 min. KPIs (p95/max/px/latencia) +
  heatmap georef del tope sobre píxeles de ceniza. Etiqueta explícita "ACHA NOAA
  enmascarado por ceniza · **no es VOLCAT**". VOLCAT/SSEC sigue de primario.

**Validación** (`scripts/validate_acha_fase0.py`, reutilizable):
1. *Cross-check de altura*: la HT recortada cae dentro del rango full-disk que el
   propio gránulo documenta (`min/max/mean_cloud_top_height`) — valida fetch +
   georef + DQF. **PASS**.
2. *Render path*: el campo real alimenta `_fig_acha_field` sin error. **PASS**.
3. *Ceniza real + VOLCAT*: Popocatépetl 2026-06-26 21:40 UTC → tope **10.3 km**
   AMSL (cráter 5.4 km, físicamente sano); VOLCAT Ash_Height tiene frame del MISMO
   scan (gap 1 min). **PASS** (orden de magnitud / co-ocurrencia).
4. *Contexto*: **0 VAA activos** globalmente → fin de junio 2026 es período
   tranquilo; las detecciones escasas (Chillán/Villarrica/Sangay = `no_plume`) son
   la realidad, no un bug. La detección usa el umbral conservador ya probado del
   codebase (BTD < −1 K) — NO se aflojó para forzar hits.

**Límite del número VOLCAT**: SSEC sirve el km QUEMADO en el PNG, no a nivel de
pixel → la comparación es de orden de magnitud, no diferencia km exacta (Fase 0).
El script vuelve a comparar automáticamente cuando reaparezca actividad de ceniza.

## Contactos / refs
- ATBD local: `docs/ATBD_GOES-R_VolAsh_v3.0_July2012.pdf`. Plan: `PLAN_VOLCAT_PROPIO.md`.
- ACHA ATBD (NOAA enterprise Cloud Height): pendiente de bajar (browser, ver plan §6).
