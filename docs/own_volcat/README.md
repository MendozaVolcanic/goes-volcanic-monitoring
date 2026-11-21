# own_volcat: VOLCAT propio (altura de pluma desde GOES-19 ABI)

Investigación y planificación para **generar nuestro propio retrieval cuantitativo de altura de
pluma volcánica / ceniza** desde GOES-19 ABI L1b, reduciendo la dependencia del único host SSEC
(`volcano.ssec.wisc.edu`, latencia ~30-50 min + caídas).

## Contenido

| Archivo | Qué es |
|---|---|
| **`PLAN_VOLCAT_PROPIO.md`** | Documento principal: síntesis del algoritmo VOLCAT (desde el ATBD), gap analysis (tenemos vs. falta), investigación de código open-source, y **plan por fases** con esfuerzo. **Empezar acá.** |
| `INVENTARIO_REPRODUCIBILIDAD.md` | Qué necesita cada resultado (H3 a H15, C2, C2b) para rehacerse, si existe hoy y qué está roto (21-11-2026). Copia de la carpeta de notas en `D:\goes_notas\local_f3a7d295\`. |
| `POR_QUE_VOLCAT_VE_Y_NOSOTROS_NO.md` | Por qué VOLCAT ve las plumas chicas de Chillán (nov-2026) y nuestro detector no: fuentes SECO, pruebas medidas, hipótesis y plan. |
| `Pavolonis_2010_CloudCompositionTheory.pdf` | Paper base teórico (β-ratios, emisividad efectiva). OA AMS. |
| `HeidingerPavolonis_2009_SplitWindowCirrus.pdf` | Base del ACHA y de las a priori del optimal estimation. OA AMS. |

## Resumen en 4 líneas

- **Algoritmo de referencia:** optimal estimation (1DVAR, Rodgers 1976) sobre 3 canales IR ABI
  (11, 12, **13.3 µm**) → retrieva Teff, ε(11µm), β(12/11µm); la **altura** sale de mapear Teff a un
  **perfil NWP T(z)** (GFS). Detalle completo en `PLAN_VOLCAT_PROPIO.md` §1.
- **Brecha principal:** nos falta el **forward model radiativo + perfil NWP vertical en NRT** y el
  **esquema OE** (la matemática es fácil; estos dos son caros). Tenemos bandas 11/12/8.5, Planck, BTD
  y detección; faltan bandas 7.4 (C10) y 13.3 µm (C16).
- **Código reutilizable:** NO hay módulo Python liviano. ORAC/CLAVR-x lo hacen pero son Fortran +
  RTM + NWP pesados. Atajo real: **leer `ABI-L2-ACHAF` (Cloud Top Height NOAA, ya en el bucket) +
  enmascarar con ceniza** = VOLCAT-lite con cero deps nuevas.
- **Camino recomendado:** Fase 0 (ACHA, 1-2 días) → C10/C16 + perfil GFS → Wen-Rose como respaldo
  independiente. Mantener VOLCAT/RealEarth como primario cuantitativo. **Saltar el OE propio** salvo
  justificación fuerte.

## Insumos de las pruebas H3 a C3: qué vive dónde (actualizado 21-11-2026, inventario)

Los datos no van al repo; el código sí. Desde el 20-11 los scratchpads de H3, β73 y H11/E2 ya no existen y
lo que queda está en estas carpetas. Lo rescatado estaba en la carpeta de notas de sesión `local_f3a7d295`
(`AppData\Local\Claude-Data\...\side-session-notes\`), que se puede borrar sin aviso; desde el 21-11 se usa la
copia `D:\goes_notas\local_f3a7d295\` (mismos archivos, junctions recreados dentro de la copia). Detalle por
resultado en `INVENTARIO_REPRODUCIBILIDAD.md`. Si una prueba "no corre", lo primero es revisar estas variables de entorno.

| Insumo | Dónde está | Cómo lo encuentra el código |
|---|---|---|
| Código del modelo radiativo (`rt.py`, `lbl.py`) | repo, `h3_h7/scripts_h3/` | `comun_h11.py` lo importa desde el repo (idéntico a la copia que había en H3) |
| Continuo MT_CKD 4.3 (`mtckd/absco-ref_wv-mt-ckd.nc`) y SRF del ABI FM4, bandas 10, 11, 14 y 15 (`srf/ABI_FM4_10Mar2016_CHxx.SRF`) | `D:\goes_cache\rt\` (bajado de nuevo el 21-11; fuentes y SHA-256 en `mauna_loa_c2b/resultados/insumos_rt.txt`) | variable `H3_RT_DL`; sin ella, `<H11_H3>\dl` (o `scripts_h3\dl` si se corre H3 suelto) |
| Tabla de coeficientes línea por línea (`lut.npz`, `lineas.npz`, HITRAN) | `D:\goes_notas\local_f3a7d295\h12_datos\extra\h3_meta\lbl\` | variable `H3_RT_LBL`; sin ella, `<H11_H3>\lbl` |
| Escenas L1b y GFS de H3 y β73, huellas, pareos | `D:\goes_notas\local_f3a7d295\cache_rescatada\` y `h12_datos\extra\` (ver `h12_datos\LEEME_rescate_2026-11-20.md`) | `H11_H3`, `H11_B73` (las carpetas `h12_datos\trabajo\h3` y `\b73` arman la estructura con junctions) |
| Cielo despejado y nube negra por píxel de H11 (`rt_h11`), rejilla de E2 (`rt_e2`), rasgos de E2 (`feat_e2`) | `D:\goes_notas\local_f3a7d295\h12_datos\` | `H11_TRABAJO` (= `h12_datos\trabajo\rv`) |
| Caso de prueba VOLCAT de Mauna Loa (GOES-17, 28-11-2022) y su extracción | `D:\goes_cache\volcat_test_mauna_loa\` | argumentos de `mauna_loa_c2b/scripts/` |
| Tablas de probabilidad (LUT) y configuración de VOLCAT para ABI | `D:\goes_notas\busqueda_2026-11-20\volcat_static_anc\volcat-ancillary\` | se leen con `D:\goes_notas\busqueda_2026-11-20\venv_hdf4\Scripts\python.exe` |

Ejemplo (Git Bash) para correr cualquier script de `reproducir_volcat/` con lo rescatado:

    N=D:/goes_notas/local_f3a7d295/h12_datos/trabajo
    H11_H3=$N/h3 H11_B73=$N/b73 H11_TRABAJO=$N/rv H3_RT_DL=D:/goes_cache/rt python -I <script>.py

Validado el 21-11 (C2): con estos insumos el modelo reproduce el cielo despejado guardado por H11 (detalle en
`mauna_loa_c2b/INFORME_C2_C2b.md`). Los scripts de H3 en `h3_h7/scripts_h3/` usan el `rt.py`
de su misma carpeta, que ya lee `H3_RT_DL` y `H3_RT_LBL`. Pendiente: β73 (`beta73/scripts/metricas_b73.py`)
importa `rt` desde la carpeta H3 de `comun_b73`; con la copia rescatada (sin `dl`) no corre hasta apuntarlo
al código del repo. No se tocó en C2 porque nada de C3 lo usa.

## Notas

- Papers **no descargables** (Pavolonis 2013 canónico, Pavolonis 2015, Wen&Rose 1994) están detrás
  de anti-bot Cloudflare/WAF pero son OA legales: bajar con navegador real (URLs en
  `PLAN_VOLCAT_PROPIO.md` §6). Prata 1989 es paywall puro.
- Material previo relacionado: `../ALTURA_COLUMNA_INVESTIGACION.md`, `../VOLCAT_LATENCIA_Y_ALTERNATIVAS.md`,
  `../altura_pluma/`.
