# VOLCAT — latencia, fuentes y factibilidad de hacerlo nosotros

> Investigación 2026-06-08 (3 agentes web, fuentes oficiales NOAA/CIMSS/SSEC).
> Disparada por: el VOLCAT del dashboard aparece ~40-50 min atrasado.

## Qué es y de qué satélite sale

VOLCAT (**Volcanic Cloud Analysis Toolkit**) es software automático de
**NOAA/NESDIS + CIMSS/SSEC (U. Wisconsin-Madison)**, liderado por **Mike
Pavolonis**. Detecta, trackea y caracteriza nubes volcánicas y emite alertas.

- **Satélite/instrumento**: producto baseline GOES-R **"Volcanic Ash: Detection
  and Height" (ABI-VAA)** sobre el **ABI** (Advanced Baseline Imager) — el mismo
  GOES-19 que ya usamos. Es **multi-sensor**: corre además en Himawari (AHI),
  otros geo, y **5 polares incluyendo VIIRS** (375-750 m, mejor resolución pero
  pocas pasadas/día).
- **Bandas IR usadas (5)**: 7.3, 8.5, 11, 12, **13.3 µm**. La 11-12 µm
  (split-window BTD) es la firma clásica de ceniza; **la 13.3 µm da la ALTURA**;
  la 7.3 µm el SO2.
- **Productos**: altura de pluma, carga másica (mass loading), probabilidad de
  ceniza, anomalía térmica. Imagen día/noche.

## Por qué demora tanto (~30-50 min)

No es un solo paso; la latencia se apila:

| Etapa | Latencia | Comentario |
|---|---|---|
| Scan + downlink + retrieval L2 (NOAA) | **~50 s** (full disk) | El algoritmo NO es el cuello; el ATBD lo optimizó. |
| Cadencia de scan full-disk | **~10 min** | Un frame es tan fresco como el último scan completo. |
| Procesamiento NOAA + **re-tiling SSEC RealEarth** | **decenas de min** (dominante) | El CIMSS/SSEC corre downstream de NOAA y re-tila para RealEarth. *(este split NOAA vs tiling es inferido, no cuantificado en una fuente única)* |

**Conclusión**: el atraso NO es del algoritmo ni de nuestro cache (5 min). Es la
**diseminación + tiling de RealEarth**, y es inherente — no lo podemos acelerar.

## Fuentes más rápidas — qué hay y qué no

- ❌ **NO hay producto VAA en S3/NODD** para GOES-19/18 (confirma nuestra nota de
  CLAUDE.md). VAA existió brevemente solo en GOES-16 (2019-2020). El algoritmo
  corre en NOAA STAR pero su salida **no se disemina por NODD**.
- ❌ **`ABI-L2-ADPF` (Aerosol Detection)** existe en S3 pero es **solo humo/polvo
  diurno binario, SIN flag operacional de ceniza volcánica** en GOES-19. No sirve.
- ❌ **Alertas VOLCAT (email/SMS)**: latencia **2-3 h** (peor). Sirven como
  *ground truth / trigger de evento*, no como raster rápido. Sin API pública;
  hay que contactar a SSEC para suscribirse.
- ⚠️ **RealEarth API** (`realearth.ssec.wisc.edu/api/`): es REST (no WMS-T).
  Polear **`/api/latest?products=ID`** agarra el frame apenas se publica (no baja
  la latencia de ingest, pero elimina demora propia de polling).
- ➕ **SACS** (BIRA-IASB, ESA, `sacs.aeronomie.be`): SO2/ash polar (OMI, GOME-2,
  IASI), alertas a VAACs. Cross-check de SO2, baja resolución temporal.
- ➕ **VAACs Buenos Aires (SMN) / Washington**: avisos de texto (VAA/IWXXM), no
  raster. Ground truth humano autoritativo.

## ¿Podríamos hacerlo nosotros desde la data satelital?

**Sí para detección, no para altura cuantitativa.**

| Producto | Inputs | Dificultad |
|---|---|---|
| **Detección** (BTD reverse-absorption 11-12 < 0, Prata; + flags multi-banda) | solo BTs de L1b | **Baja — ya lo hacemos.** numpy puro. Latencia ~5-10 min desde S3 noaa-goes19. |
| **Altura + mass loading** | 11/12/13.3 µm **+ GFS + tropopausa + emisividad + RTM + 1DVAR** | **Research-grade.** Meses, frágil, necesita NWP operacional. **NO reimplementar.** |

**Por qué la altura necesita tanto**: detección solo pregunta "¿la firma 11-12 µm
es anómala?" (test de signo). Altura pregunta "¿a qué nivel atmosférico una nube
de esta emisividad reproduce las radiancias observadas?" — inversión no-única que
exige (a) un modelo de transferencia radiativa (RTM) y (b) un perfil T(z) de NWP
para convertir temperatura de nube → altitud.

**Reuso open-source**:
- **satpy** (`pytroll/satpy`): trae composites `ash`/`dust`/`volcanic_emissions`
  RGB para ABI listos. Solo RGB, **sin altura**. Vale migrar nuestro Ash RGB ahí.
- **CLAVR-x** (CIMSS, ACHA+PFAAST): ES el framework real de Pavolonis. Fortran
  pesado, necesita NWP — **no realista para equipo chico**.
- No existe librería Python liviana de ash-height. No hay atajo al RTM+NWP.

**Recomendación pragmática**:
1. **Construir capa propia de DETECCIÓN rápida** desde L1b cada scan → máscara +
   extensión de ceniza en **~1-3 min** (vs ~40 min de SSEC). Ese es el win real,
   como early-warning.
2. Mantener **VOLCAT/RealEarth para ALTURA** (validado) — no reimplementar el 1DVAR.
3. Opcional: **proxy de altura crudo** (BT 11µm sobre perfil GFS/Open-Meteo) →
   ±2-4 km, solo opaco, **etiquetado como indicativo, nunca número VAAC**.

## Fuentes
- ATBD GOES-R Volcanic Ash v3.0 (jul 2012): https://www.star.nesdis.noaa.gov/goesr/documents/ATBDs/Baseline/ATBD_GOES-R_VolAsh_v3.0_July2012.pdf
- GOES-R product: https://www.goes-r.gov/products/baseline-volcanic-ash.html
- STAR: https://www.star.nesdis.noaa.gov/goesr/product_aero_vol.php
- Pavolonis, Heidinger, Sieglaff 2013, JGR Atmos, doi:10.1002/jgrd.50173
- SSEC Volcanic Cloud Monitoring: https://volcano.ssec.wisc.edu/
- RealEarth API: https://realearth.ssec.wisc.edu/doc/api.php
- AWS noaa-goes: https://registry.opendata.aws/noaa-goes/
- satpy abi composites: https://github.com/pytroll/satpy/blob/main/satpy/etc/composites/abi.yaml
- SACS: https://sacs.aeronomie.be/
