# Inventario de reproducibilidad de `docs/own_volcat/` (21-11-2026)

**Por qué existe.** El 20-11 se borraron los scratchpads de H3, β73 y H11/E2, y con ellos la carpeta `dl\` del
modelo radiativo. Nada avisó: los scripts siguieron en el repo, compilando, pero sin insumos. Este inventario
dice, para cada resultado, qué hace falta para rehacerlo y si eso existe hoy en disco. Es barato a propósito:
búsqueda estática de rutas en los scripts, comprobación con `ls`/`du`, `py_compile`, y reproducción completa
sólo de cuatro resultados clave.

**Método.**
- Rutas absolutas y variables de entorno sacadas de los `.py` con una expresión regular (rutas `C:\`, `D:\`,
  `os.environ`), comprobadas una por una en disco el 21-11 a las 16 h. Las rutas que arma el código con
  `os.path.join` desde una base se cuentan por su base.
- `python -m py_compile` sobre los 86 scripts de main y los de los PR 75, 76 y 77: **todos compilan**.
  "Compila" no quiere decir "corre": el problema de este árbol nunca fue la sintaxis, fueron los insumos.
- Los PR 75, 76 y 77 están **sin fusionar**: sus scripts se leyeron con `git archive origin/<rama>`.

**Estados.**
- **Reproducible**: script en el repo, insumos en `D:\` o en el repo, comprobado o con ruta correcta.
- **Frágil**: corre hoy, pero algún insumo vive en un lugar que se puede borrar sin aviso (scratchpad de
  `AppData\Local\Temp`, carpeta de notas de sesión, datos de SSEC con plazo o licencia restringida) o sólo en
  la carpeta principal del repo, que no se toca.
- **Roto**: falta un insumo sin copia, o el script apunta a una ruta que ya no existe y no hay sustituto
  directo. "Reparable" = el insumo existe en otra parte y basta cambiar una ruta.

## 0. Lo que se salvó en esta sesión (copias, nada movido ni borrado)

| Qué | Origen (sigue intacto) | Copia | Tamaño |
|---|---|---|---|
| Carpeta de notas de la sesión de rescate: insumos de H11, E2, H12, H13, tablas línea por línea del modelo radiativo (`lbl\`), cachés L1b y GFS de H3 y β73, scripts de las pruebas del 17 y 18-11 (`prueba_AB.py`, `paso2..4`, `pruebaA_28oct.py`) | `C:\Users\nmend\AppData\Local\Claude-Data\claude_pzs8sxrjxfjjc\side-session-notes\local_f3a7d295-ddde-4b7c-b258-25e760c44266\` | `D:\goes_notas\local_f3a7d295\` (los 11 junctions de `h12_datos\trabajo\` recreados apuntando dentro de la copia; registro en `D:\goes_notas\local_f3a7d295_robocopy.log`) | 960 MB, 4.659 archivos, 0 errores |
| Scratchpad de H9 (caché C07 `c07cache\`, historia GLM `glm\`, `glm_s3\`) | `C:\Users\nmend\AppData\Local\Temp\claude\11c46882e3e16008\ea70ca80-5f81-4c66-8568-aa962b07902e\scratchpad\` | `D:\goes_notas\scratch_rescate_2026-11-21\h9_calor_rayos_11c46882\` | 78 MB |
| Scratchpad de H10 (`h10\`: GFS de viento, huellas, salidas) | `C:\Users\nmend\AppData\Local\Temp\claude\3eed1f0fb6f1d795\70cd3716-38bb-4bad-9d2f-cd60906a40d4\scratchpad\` | `D:\goes_notas\scratch_rescate_2026-11-21\h10_direccion_3eed1f0f\` | 2,5 MB |
| Scratchpad del VAAC de Londres (`vaac\`: caché C13, Planck) | `C:\Users\nmend\AppData\Local\Temp\claude\470cdb238f003f8e\1985b7fb-c655-4e72-b95c-8d201d1a842a\scratchpad\` | `D:\goes_notas\scratch_rescate_2026-11-21\vaac_470cdb23\` | 19 MB |
| Resto del scratchpad de H11 (`rv\latlon.npz`) | `C:\Users\nmend\AppData\Local\Temp\claude\a2570b18d9d77a03\d3ce10df-b230-48d8-900a-293980f29716\scratchpad\` | `D:\goes_notas\scratch_rescate_2026-11-21\rv_h11_a2570b18\` | 0,1 MB |
| Cuadros VOLCAT de validación de magnitud y H14 (`volcat_validacion\`, memoria: "irreemplazable") | `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\Goes\data\raw\volcat_validacion\` | `D:\goes_notas\volcat_validacion_copia_2026-11-21\` | 119 MB, 998 archivos |

| Carpeta de notas de la búsqueda del 20-11 (`BUSQUEDA_2026-11-20.md`, que da el nombre exacto del paquete de tablas de SSEC; correo a Pavolonis v5) | `C:\Users\nmend\AppData\Local\Claude-Data\claude_pzs8sxrjxfjjc\side-session-notes\local_a7c21f45-ef62-4270-9e3a-c053b95c331e\` | `D:\goes_notas\local_a7c21f45_busqueda\` | 0,2 MB, 10 archivos |

`D:\goes_notas\scratch_rescate_2026-11-21\ORIGEN.txt` registra de qué scratchpad salió cada carpeta.

**Segunda vuelta (21-11, a pedido de la sesión coordinadora), en este mismo PR:**
- README de `own_volcat` y valor por defecto de `H12_OUT` (`reproducir_volcat\scripts\comun_h12.py`) apuntan
  ahora a `D:\goes_notas\local_f3a7d295\...`, no a la carpeta de notas.
- LEEME con URL exactas de SSEC y sumas MD5 (fuera del repo): `D:\goes_cache\volcat_test_mauna_loa\LEEME.md`
  (paquete del caso de Mauna Loa) y `D:\goes_notas\busqueda_2026-11-20\volcat_static_anc\LEEME.md` (paquete
  `volcat-geocat-static-anc-g3e7f2a3d38.tar.xz`, tablas y configuración).
- Scripts, criterios y salidas de las pruebas del 17 y 18-11 copiados al repo en `pruebas_17_18nov\` (con LEEME
  que dice que los insumos están perdidos). Siguen sin correr: sus scratchpads no existen.
- Las 4 constantes `REPO` de abajo resuelven la raíz del repo desde el propio archivo
  (`Path(__file__).resolve().parents[4]`). Comprobado: compilan, `REPO` cae en la raíz y los módulos de `src`
  que importan (`gfs_archive`, `goes_fdcf`, `volcat_colorbar`) cargan con todos los nombres que usan.
- `scripts\validate_magnitud.py` y `scripts\harvest_volcat_validacion.py` aceptan `--raw <carpeta>` o la
  variable `VOLCAT_VALIDACION_RAW`; sin ellas, el defecto sigue siendo `data\raw\volcat_validacion`. Probado:
  `validate_magnitud.py --raw D:\goes_notas\volcat_validacion_copia_2026-11-21 volcat` corre en un worktree
  (3 min 23 s) y rehace `volcat_lecturas.json` con **los mismos 824 valores**; la única diferencia es una clave
  nueva `motivo` por lectura, que agrega el código actual de `src` (commit 6d876d3, posterior a la medición). El
  archivo commiteado no se tocó.

> **26-11-2026 (S28, liberar D:):** se borraron, con el sí de Nicolás, `D:\goes_cache\volcat_test_mauna_loa\ext\` (2,9 GB) y `l2_data\` más `diag_data\` de `D:\goes_notas\s16\modo_dia\fuego\...\reference_data\` (10,5 GB). Ningún código de S22 en adelante los leía. Quedan `paquete.tar.gz` y `npz\` de Mauna Loa (para C2b, PR 76 y PR 77 hay que volver a extraer `ext\` desde el paquete, con `tar -xzf`) y, de Fuego, `npz\`, `events\`, `logs\`, `history\`, `l1_data\`, `rtm_data\` y `time_series\`. Para rehacer `fu_extraer.py` (H18) o H16 sobre Fuego hay que volver a bajar el paquete de SSEC (versión r20260709, mientras se publique).
eference_data\` (10,5 GB). Ningún código de S22 en adelante los leía. Quedan `paquete.tar.gz` y `npz\` de Mauna Loa (para C2b, PR 76 y PR 77 hay que volver a extraer `ext\` desde el paquete, con `tar -xzf`) y, de Fuego, `npz\`, `events\`, `logs\`, `history\`, `l1_data\`, `rtm_data\` y `time_series\`. Para rehacer `fu_extraer.py` (H18) o H16 sobre Fuego hay que volver a bajar el paquete de SSEC (versión r20260709, mientras se publique).

**Worktrees que se van a limpiar** (busqueda-volcat, c1-eventos, c2-rt-mauna-loa, c3-h15-lut, continuacion-17 y
-20, distracted-hawking, fix-fuga-gfs, pr39, volcat-capa-deteccion): revisados con
`git status --porcelain --ignored` y `git rev-list origin/main..HEAD`. **Ninguno tiene commits fuera de main ni
archivos propios** (sólo `.claude\settings.local.json` y dos HTML vacíos de 0 bytes en busqueda-volcat). El PDF
de Heidinger y Pavolonis 2009 ya está versionado en main
(`docs/own_volcat/HeidingerPavolonis_2009_SplitWindowCirrus.pdf`, con los otros seis PDF de la carpeta). Se pueden limpiar sin perder nada de `own_volcat`.

Sí hay scripts que **citan** worktrees que ya no existen, como constante `REPO`:
`h3_h7\scripts_h3\fetch_gfs.py`, `h3_h7\scripts_h7\h7_fetch_fdcf.py`, `h3_h7\scripts_h7\h7_volcat_obj.py`
(worktree `h3-cielo-modelado-beta-114fd5`) y `beta73\scripts\fetch_gfs_b73.py` (`beta73-episodios-nuevos-f566cb`).
Usan esa ruta sólo para importar `src\` del repo. **Arreglado en la segunda vuelta** (ver arriba).

## 1. Tabla por resultado

Rutas cortas: `<R>` = `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\Goes\docs\own_volcat`,
`<F3>` = `D:\goes_notas\local_f3a7d295`, `<T>` = `C:\Users\nmend\AppData\Local\Temp\claude`.

| Resultado | Script(s) | Insumos | Existe hoy | Corre hoy | Riesgo |
|---|---|---|---|---|---|
| Pruebas A y B (paralaje y 8,5 µm, 17-11), pasos 2, 3 y 4 (18-11), prueba A del 28-10 (POR_QUE §3 y §3.1) | `prueba_AB.py`, `paso2_analisis.py`, `paso3_objetos.py`, `paso3_analisis.py`, `paso4_bajar.py`, `paso4_analisis.py`, `pruebaA_28oct.py`, `fetch_solar.py`: desde el 21-11 en `<R>\pruebas_17_18nov\scripts\` (antes sólo en la carpeta de notas; copia también en `<F3>`) | caché del detector `<T>\d6ea8719dcf88502\...\scratchpad\det` (ventana 83 × 94, `window.json`, `latlon.npz`, `planck.json`), PNG VOLCAT `<T>\58c6c65788fdfd96\...\volcat_chillan_10min\png` y `<T>\3960f3d64983ed82\...\volcat_extra\png` | **No**: los tres scratchpads ya no existen. Las salidas `.txt` sí, en `<F3>` | **No** | **Roto.** Sólo quedan los resultados y los scripts. El caché del detector se puede rehacer desde S3 (L1b de oct-nov sigue en NOAA), los PNG VOLCAT de oct-nov no (SSEC no los guarda) salvo lo que haya en `volcat_validacion` y `cache_rescatada` |
| H3 cielo modelado y β con C10 (`h3_h7\INFORME_H3.md`) | `h3_h7\scripts_h3\*` (`fetch_h3`, `fetch_gfs`, `huellas_h3`, `h3_pareo`, `h3_metricas`, `rt.py`, `lbl.py`) | escenas L1b y GFS (`<F3>\cache_rescatada\h3\`, 52 MB), huellas y pareo (`<F3>\h12_datos\extra\h3_meta\`), tablas línea por línea (`<F3>\h12_datos\extra\h3_meta\lbl\`, 178 MB), continuo MT_CKD y SRF (`D:\goes_cache\rt\`), caché del detector (`det`, perdido), PNG VOLCAT (perdidos) | parcial | **No en su forma original**: `comun_h3.py` y `huellas_h3.py` apuntan a `det` y a PNG borrados (`fetch_gfs.py` ya no apunta a un worktree) | **Roto como prueba entera; reparable la parte de métricas** (huellas y pareo existen, el modelo radiativo corre: lo usa H11) |
| H7 seguimiento (`h3_h7\INFORME_H7.md`) | `h3_h7\scripts_h7\*` | `det\window.json`, `det\latlon.npz`, `volcat_chillan_10min\frecuencia_pixel_clasificado.npy` y PNG (la ruta al worktree borrado ya se corrigió) | **No** | **No** | **Roto** (falsada; el informe trae los números, no hay cómo rehacerla sin rehacer el caché del detector y los PNG) |
| β(7,3/11) fuera de muestra (`beta73\INFORME_beta73.md`) | `beta73\scripts\*` | `comun_b73.py` apunta a `h3`, `det`, dos carpetas de PNG y `b73` en scratchpads borrados; lo rescatado: `<F3>\cache_rescatada\b73\` (46 MB) e inventarios y huellas en `<F3>\h12_datos\extra\b73_meta\` y `D:\goes_cache\h13\shim\b73\`. PNG `b73\png_new` (380 MB) **perdidos** | parcial | **No** | **Roto como prueba entera**; el README ya lo anotaba ("no corre hasta apuntarlo al código del repo") |
| VAAC de Londres (`vaac_londres\INFORME.md`) | `vaac_londres\scripts\rutas.py`, `fetch_c13.py`, `analisis.py`, `verificar.py` | `PREV` = caché del detector `det` (perdido: `window.json`, `planck.json`, `latlon.npz`, `cache\`, huellas); `VAAC_TRABAJO` = scratchpad `vaac` (vivo, copiado a `D:\goes_notas\scratch_rescate_2026-11-21\vaac_470cdb23\`) | parcial | **No** (`rutas.py` falla al no encontrar `det`) | **Roto**; el informe dice que `fetch_c13.py` y "los scripts del 17-11" rehacen los cachés desde S3, pero esos scripts del 17-11 no están en el repo |
| H9 calor 3,9 µm y rayos GLM (`calor_rayos\INFORME.md`) | `calor_rayos\scripts\*` | `SCR` = scratchpad `11c46882` (vivo, **copiado**: `c07cache`, `glm`, `glm_s3`); `det\latlon.npz` y `det\window.json` (perdidos); `b73\inv_local.json` e `inv_new.json` (perdidos en el scratchpad, **existen** en `<F3>\h12_datos\extra\b73_meta\` y `D:\goes_cache\h13\shim\b73\`) | **Sí** (21-11) | **Sí**: rutas apuntadas a `D:` el 21-11 (§3, punto 8); `analisis_calor.py` y `analisis_rayos.py` rehechos con salida idéntica salvo la línea de fecha | **Reproducible** (el análisis; `fetch_c07.py` y los de GLM compilan, no re-ejecutados) |
| H10 dirección de la pluma (`direccion_pluma\INFORME.md`) | `direccion_pluma\scripts\*` | `WORK` = scratchpad `3eed1f0f` (vivo, **copiado**), `det` (perdido: `latlon.npz`, `cache\`), `b73` (perdido; inventarios en `<F3>`), PNG VOLCAT (perdidos) | parcial | **No** | **Roto** (necesita PNG de oct-nov y el caché del detector); las salidas JSON están en el repo |
| H11 terreno, filas de volcán y SO₂ (`reproducir_volcat\INFORME_H11.md`) | `reproducir_volcat\scripts\comun_h11.py`, `ventana.py`, `rt_niveles.py`, `h11_analisis.py` | `H11_H3`, `H11_B73`, `H11_TRABAJO` en `<F3>\h12_datos\trabajo\` (cielo despejado y nube negra por píxel `rt_h11`, 164 MB), `H3_RT_DL=D:\goes_cache\rt` | **Sí** (copia en D de hoy) | ver §2 | **Reproducible** con la copia de `D:`; antes de hoy, frágil (sólo en la carpeta de notas) |
| E2, SECO propio entrenado con VOLCAT (`reproducir_volcat\INFORME_E2.md`) | `fetch_e2.py`, `fetch_gfs_e2.py`, `rt_e2.py`, `e2_features.py`, `e2_clasificador.py`, `huella_png.py` | `<F3>\h12_datos\extra\cache_e2`, `gfs_e2`, `png_e2`, `rt_e2` (171 MB), `<F3>\h12_datos\feat_e2` (73 MB, md5 comprobado el 20-11) | **Sí** | compila, insumos presentes (no re-ejecutado) | **Reproducible** con la copia de `D:` |
| H12 Test 3 original de Francis (`reproducir_volcat\INFORME_H12.md`) | `comun_h12.py`, `h12_rt_sitios.py`, `h12_analisis.py`, `h12_posterior_69.py` | lo de E2 más `H12_OUT` (desde el 21-11 su defecto es `<F3>\h12_datos\h12\`, 25 MB; antes era la carpeta de notas) | **Sí** | compila, insumos presentes (no re-ejecutado) | **Reproducible** con la copia de `D:` (era frágil hasta corregir el defecto de `H12_OUT`) |
| H13 cambio entre cuadros (`temporal_h13\INFORME_H13.md`) | `temporal_h13\scripts\h13_comun.py`, `fetch_h13.py`, `h13_rt.py`, `h13_feat.py`, `h13_analisis.py`, `h13_rf.py` | `H13_DIR=D:\goes_cache\h13` (1,2 GB: L1b, GFS, PNG, `feat\` 136 MB, `shim\` 293 MB con copia de H3, β73 y E2). `shim\h3` trae `rt.py` y `lbl.py` pero **no** `lbl\` ni `dl\`: `h13_rt.py` necesita `H3_RT_DL=D:\goes_cache\rt` y `H3_RT_LBL=<F3>\h12_datos\extra\h3_meta\lbl` | **Sí** | compila, insumos presentes (no re-ejecutado; el informe trae el orden de corrida) | **Reproducible** (el análisis); recalcular el modelo radiativo pide las dos variables |
| H14 eventos VOLCAT por volcán (`eventos_h14\INFORME_H14.md`) | `eventos_h14\scripts\h14_eventos.py`, `h14_georef.py`, `h14_tablas.py` | `H14_EVENTOS=D:\goes_notas\busqueda_2026-11-20\volcat_eventos_357070` (69 MB, 60 NetCDF + 60 JSON de SSEC); `H14_PNG` = `...\Goes\data\raw\volcat_validacion\Chile_Central_2_km\frames` + `D:\goes_cache\h13\png` | **Sí** | compila, insumos presentes (no re-ejecutado) | **Frágil**: los eventos son de SSEC con licencia "access restricted to approved users", el servidor guarda ~7 días, y se borran si Pavolonis dice que no. `frames` sólo vive en la carpeta principal (copia de hoy en `D:\goes_notas\volcat_validacion_copia_2026-11-21\`) |
| C2, el modelo radiativo con insumos bajados de nuevo (`mauna_loa_c2b\INFORME_C2_C2b.md`) | `mauna_loa_c2b\scripts\c2_validar_rt.py` | `rt_h11` y escenas H3 en `<F3>`, `D:\goes_cache\rt` (MT_CKD + SRF, SHA-256 en `mauna_loa_c2b\resultados\insumos_rt.txt`), tablas `lbl\` en `<F3>` | **Sí** | ver §2 | **Reproducible** con la copia de `D:` |
| C2b, VOLCAT de Mauna Loa (cota RTM) | `c2b_estructura.py`, `c2b_extraer.py` (venv_hdf4), `c2b_medir.py`, `c2b_rtm_cota.py` | `D:\goes_cache\volcat_test_mauna_loa\` (4,3 GB: paquete de SSEC `paquete.tar.gz` + `paquete.md5`, extraído en `ext\`, `npz\`), `D:\goes_notas\busqueda_2026-11-20\venv_hdf4\` (pyhdf 2.5.5 importa) | **Sí** | compila, insumos presentes (no re-ejecutado) | **Reproducible**; el caso de prueba de SSEC no tiene otra copia (paquete público del código VOLCAT, se puede volver a bajar mientras SSEC lo publique) |
| H15 etapa 1, lectura de las tablas (`lut_h15\LECTURA_LUT.md`) | `lut_estructura.py`, `lut_exportar.py` (venv_hdf4), `lut_cordura.py` | `D:\goes_notas\busqueda_2026-11-20\volcat_static_anc\volcat-ancillary\luts` (84 MB), salida `D:\goes_cache\lut_h15\lut_pixel.npz` (1,7 MB) | **Sí** | compila, insumos presentes | **Reproducible**; tablas de SSEC sin otra copia (públicas en `static_ancillary`) |
| H15 etapa 2, validación en Mauna Loa (`lut_h15\INFORME_H15.md`) | `ml_extraer.py` (venv_hdf4), `lut_volcat.py`, `etapa2_validar.py`, `etapa2_diag*.py`, `etapa2_posterior.py` | `D:\goes_cache\lut_h15\ml\` (10 `ml_*.npz` + `gfs_ttropo.npz`), `D:\goes_cache\volcat_test_mauna_loa\npz\` (10 `c2b_*.npz`), `lut_pixel.npz` | **Sí** | ver §2 | **Reproducible** |
| H15 frente 1, nube tenue (PR 75, **no fusionado**) | `lut_h15\nube_tenue\scripts\nt_comun.py`, `nt_regla.py`, `nt_validar.py`, `nt_explorar*.py` | los mismos de la etapa 2 (importa `lut_volcat` y `etapa2_validar`) | **Sí** | ver §2 | **Reproducible**, pero el código sólo vive en la rama `analisis/h15-nube-tenue` (en GitHub) |
| H15 nivel B, cielo despejado (PR 76, fusionado 21-11) | `lut_h15\cielo_sesgo\scripts\*` (vueltas 1 a 5) | `D:\goes_cache\lut_h15\cielo_sesgo\gfs_punto_frio.npz`, `D:\goes_cache\cielo_sesgo\` (`tpw.npz`, `gfs_sfc.npz`), `ext\` de Mauna Loa | **Sí** | vuelta 2 re-ejecutada el 21-11: `vuelta2_beta.json` idéntico | **Reproducible** desde el 21-11: importa nube tenue del repo (§3, punto 4) |
| H15 LRC y vecindad (PR 77, fusionado 21-11) | `lut_h15\cielo_lrc\scripts\*` | `D:\goes_cache\cielo_lrc\` (53 MB, con su propia copia de los scripts de PR 75 en `nt\`), `ext\` de Mauna Loa | **Sí** | compila, insumos presentes (no re-ejecutado) | **Reproducible** desde el 21-11, igual que PR 76 |
| Validación de magnitud VOLCAT (`validacion_magnitud\`, `PLAN_VALIDACION_MAGNITUD.md`) | `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\Goes\scripts\harvest_volcat_validacion.py`, `scripts\validate_magnitud.py` | `ROOT\data\raw\volcat_validacion\` (122 MB, gitignored), o la carpeta que diga `--raw` / `VOLCAT_VALIDACION_RAW` | **Sí**: carpeta principal y copia `D:\goes_notas\volcat_validacion_copia_2026-11-21\` | **Sí**: la etapa `volcat` corrió con `--raw` en un worktree y rehízo los 824 valores (§0) | **Reproducible** con la copia de `D:` (era frágil: sólo corría desde la carpeta principal) |

La etapa 3 de H15 (Chillán) la corre otra sesión ahora y no se inventarió.

## 2. Reproducción completa de cuatro resultados clave

Corridas el 21-11 entre 16:10 y 16:18 h, las cuatro en paralelo, **leyendo sólo la copia de `D:`** (no la carpeta
de notas), con el código de main `5be5e1c` y, para nube tenue, la rama `analisis/h15-nube-tenue` (PR 75).

| Resultado | Tiempo | Comparación con lo commiteado | Veredicto |
|---|---|---|---|
| H11 (`h11_analisis.py`) | 8 min 38 s | `h11_resultado.txt` **idéntico** (116 líneas, sin contar fin de línea), "VEREDICTO H11: NO CONCLUYENTE". El `h11_pares.pkl` que escribe en `H11_TRABAJO` sale idéntico byte a byte al rescatado en `D:\goes_notas\local_f3a7d295\h12_datos\extra\h11_pares.pkl` | reproduce |
| C2 (`c2_validar_rt.py`) | 8 min 47 s | mismas 5 escenas, 1.500 píxeles; todas las cifras por escena y banda iguales al JSON commiteado (error 0,0 K en C10, C11, C14 y C15; cumple la vara de 0,3 K). Sólo cambian el tiempo por escena y las rutas de `insumos` (ahora `D:\goes_notas\...` y este worktree) | reproduce |
| H15 etapa 2 (`etapa2_validar.py`) | 40 s | `etapa2_validacion.json` y `etapa2_variantes.csv` **idénticos byte a byte** (`git diff` vacío tras reescribirlos) | reproduce |
| H15 frente 1, nube tenue (`nt_validar.py`, PR 75) | 16 s | `nt_validacion.json` y `nt_validacion.txt` idénticos salvo fin de línea (CRLF del Windows contra LF de `git archive`); R1 + R2 + R3 cumplen en los tramos < 0,2 y 0,2 a 0,5 (exacto 0,9996 y 0,9998) | reproduce |

Lo que esto prueba: con lo que hay hoy en `D:` (MT_CKD y SRF bajados de nuevo el 21-11, tablas línea por
línea y cielo despejado por píxel copiados de la carpeta de notas) la cadena del modelo radiativo, el análisis de
H11 y el motor de tablas de H15 rehacen lo publicado sin diferencias. Lo que no prueba: que E2, H12 y H13 corran
completos (sólo se comprobó que compilan y que sus insumos existen).

## 3. Frágil: salvar ya

Hecho en esta sesión (ver §0): carpetas de notas `local_f3a7d295` y `local_a7c21f45`, cuatro scratchpads vivos y
`volcat_validacion`, todo a `D:\goes_notas\`; y en la segunda vuelta, los puntos 1, 3, 5, 6 y el `--raw`.
Estado de cada punto:

1. **HECHO.** README de `own_volcat` y defecto de `H12_OUT` apuntan a `D:\goes_notas\local_f3a7d295\...`.
2. **Eventos VOLCAT de Chillán (`D:\goes_notas\busqueda_2026-11-20\volcat_eventos_357070`)**: única copia, SSEC
   los borra a los ~7 días y la licencia es restringida. No se pueden subir. Acción: dejarlos donde están, no
   redistribuirlos, y si se necesitan más cuadros bajarlos esta semana (el correo a Pavolonis decide si se
   conservan).
3. **HECHO (LEEME).** Caso de prueba de Mauna Loa y tablas de VOLCAT: siguen siendo única copia en un solo
   disco, pero ya tienen URL exactas y MD5 para volver a bajarlos y comprobarlos:
   `D:\goes_cache\volcat_test_mauna_loa\LEEME.md` y `D:\goes_notas\busqueda_2026-11-20\volcat_static_anc\LEEME.md`
   (fuera del repo, como todo lo de SSEC).
4. **HECHO (21-11, tras fusionar PR 75 a 79).** `cielo_sesgo\scripts\vuelta2_beta.py` y `cielo_lrc\scripts\comun.py`
   importan `nt_regla` de `<R>\lut_h15\nube_tenue\scripts` y ya no de las copias en `D:\goes_cache\cielo_sesgo\nt\` y
   `D:\goes_cache\cielo_lrc\nt\` (idénticas archivo por archivo al código fusionado, comprobado con `diff`).
   `vuelta2_beta.py` re-ejecutado: `vuelta2_beta.json` sale idéntico byte a byte. Las copias de `D:` quedan, sin uso.
5. **HECHO.** Scripts, criterios y salidas de las pruebas del 17 y 18-11 en `<R>\pruebas_17_18nov\`, con LEEME
   "insumos perdidos".
6. **HECHO.** Las 4 constantes `REPO` resuelven la raíz desde el propio archivo.
7. **HECHO (`--raw`).** `validate_magnitud.py` y `harvest_volcat_validacion.py` aceptan `--raw` o
   `VOLCAT_VALIDACION_RAW`, defecto sin cambios.
8. **HECHO (21-11). H9**: en los cinco scripts de `calor_rayos\scripts\`, `DET` apunta a
   `D:\goes_notas\local_f3a7d295\cache_rescatada\reproducir_volcat` (ahí sí está `window.json`, y0 = 4497, x0 = 2820,
   y su `latlon.npz` es idéntico al de `h12_datos\trabajo\rv`), `B73` a `D:\goes_cache\h13\shim\b73` y `SCR` a
   `D:\goes_notas\scratch_rescate_2026-11-21\h9_calor_rayos_11c46882`. `h9_calor_resultado.txt` y
   `h9_rayos_resultado.txt` rehechos: idénticos salvo la línea con la fecha de ejecución.

**Perdido sin copia** (no hay nada que salvar, sólo saberlo): el caché del detector del 17-11 (`det`), los PNG
VOLCAT de oct-nov de las sesiones `58c6c657` y `3960f3d6`, y los PNG de β73 (`b73\png_new`, 380 MB). Por eso
pruebas A/B, pasos 2 a 4, H7, β73, VAAC de Londres y H10 no se pueden rehacer tal como se hicieron.

## 4. Comandos para reproducir los resultados clave (Git Bash)

    N=D:/goes_notas/local_f3a7d295/h12_datos/trabajo
    export H11_H3=$N/h3 H11_B73=$N/b73 H11_TRABAJO=$N/rv H3_RT_DL=D:/goes_cache/rt PYTHONIOENCODING=utf-8
    R=C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/Goes/docs/own_volcat

    # H11 (ojo: reescribe $N/rv/h11_pares.pkl; respaldarlo antes)
    python -I $R/reproducir_volcat/scripts/h11_analisis.py /ruta/salida/h11_resultado.txt

    # C2 (modelo radiativo contra el cielo despejado guardado por H11)
    python -I $R/mauna_loa_c2b/scripts/c2_validar_rt.py /ruta/salida/c2

    # H15 etapa 2 (escribe en $R/lut_h15/resultados/; comparar con git diff)
    python -I $R/lut_h15/scripts/etapa2_validar.py

    # Validación de magnitud desde un worktree (lee la copia de D:; escribe en $R/validacion_magnitud/)
    python scripts/validate_magnitud.py --raw D:/goes_notas/volcat_validacion_copia_2026-11-21 volcat

    # H15 frente 1, nube tenue (rama analisis/h15-nube-tenue, PR 75; escribe en nube_tenue/resultados/)
    git worktree add /ruta/nt origin/analisis/h15-nube-tenue
    python -I /ruta/nt/docs/own_volcat/lut_h15/nube_tenue/scripts/nt_validar.py

    # H13 (si hay que recalcular el modelo radiativo)
    export H13_DIR=D:/goes_cache/h13 H3_RT_LBL=D:/goes_notas/local_f3a7d295/h12_datos/extra/h3_meta/lbl

    # Tablas de VOLCAT (HDF4)
    D:/goes_notas/busqueda_2026-11-20/venv_hdf4/Scripts/python.exe -I $R/lut_h15/scripts/lut_exportar.py

## 5. Cifra

De **20 resultados** inventariados (incluye los tres PR sin fusionar; excluye la etapa 3 de H15, en curso):

- **10 reproducibles**: H11, E2, H12, H13, C2, C2b, H15 etapa 1, H15 etapa 2, H15 nube tenue (PR 75) y
  validación de magnitud. Cinco reproducidos completos con cifras iguales (H11, C2, etapa 2, nube tenue y la etapa
  `volcat` de magnitud). H11, E2, H12 y C2 lo son **desde hoy**: hasta esta sesión sus insumos vivían sólo en la
  carpeta de notas de sesión. H12 y magnitud pasaron de frágiles a reproducibles en la segunda vuelta.
- **3 frágiles** al cerrar el inventario: H14 (eventos SSEC restringidos y con plazo), PR 76 y PR 77 (importaban
  copias de scripts desde `D:`). **Actualización 21-11:** PR 76 y 77 pasan a reproducibles (punto 4 de §3; la
  vuelta 2 de PR 76 se rehízo con cifras idénticas), así que quedan **12 reproducibles, 1 frágil (H14), 7 rotos**.
  **Actualización 21-11, noche:** H9 pasa a reproducible (punto 8 de §3): **13 reproducibles, 1 frágil, 6 rotos**.
- **Rotos** (7 al cerrar el inventario, 6 desde que H9 se reparó): pruebas A/B y pasos 2 a 4 del 17 y 18-11, H3,
  H7, β73, VAAC de Londres y H10. H3 es reparable en su parte de métricas. Los demás perdieron el caché del detector
  o los PNG VOLCAT de oct-nov, que no tienen copia.

Todos los scripts compilan (86 en main más los de los tres PR).
