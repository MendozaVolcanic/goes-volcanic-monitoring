# Altura de Columna Eruptiva — Investigación y Decisión

**Fecha:** 2026-04-25
**Estado:** Decisión tomada — VOLCAT primero, Wen-Rose como fallback en Fase 3.

---

## TL;DR

| Opción | Veredicto |
|---|---|
| **A. VOLCAT vía RealEarth API** | ✅ **CAMINO PRIMARIO** — gratis, NRT, ya cubre los 43 volcanes |
| **B. Wen-Rose 1994 propio** | ⚠ Solo como **fallback/validación** y para reanálisis histórico (pre-2018) |
| **TROPOMI L2_SO2** | Complemento, no reemplaza altura de **ceniza** (es altura de SO2) |
| **CALIPSO/EarthCARE** | Solo validación a posteriori (pasajes esporádicos) |

**Por qué VOLCAT le gana a Wen-Rose**: VOLCAT corre **Pavolonis 2013**, que es Wen-Rose moderno con optimal estimation + RTM acoplado + tracking 4D. Reimplementar Wen-Rose 1994 daría producto **inferior** al que SSEC entrega gratis.

---

## 1. VOLCAT (SSEC/CIMSS, U. Wisconsin–Madison)

### Qué es

Sistema operacional de NOAA/NESDIS + FAA + CIMSS, integrado a los flujos de los **VAACs** (Washington, Anchorage, Buenos Aires). Sirve productos casi NRT vía RealEarth.

URLs base:
- Portal: https://volcano.ssec.wisc.edu/
- API REST: https://realearth.ssec.wisc.edu/
- Doc API: https://realearth.ssec.wisc.edu/doc/api.php

### Productos disponibles para Chile

Sectores chilenos confirmados en el viewer:
- **Villarrica 250 m** (alta resolución VIIRS/MODIS)
- **Calbuco 1 km**
- **Copahue 250 m**
- **Planchón-Peteroa 500 m**
- **Chile North 2 km** (mosaico GOES)
- **Chile Central 2 km**
- **Chile South 2 km**
- **VAAC Buenos Aires** (full domain)

Productos por sector (de las imágenes que el usuario pasó):
- **Ash_Height** ← lo que necesitamos
- Ash_Loading
- Ash_Probability
- Ash_Reff (radio efectivo)
- BT11um
- BTD1112um
- REF065um
- RGB1112or13um 3911um 11um (incluye versión "Ash Retv")
- RGB1112um 8511um 11um (incluye versión "Ash Retv")

### Algoritmo Ash_Height

VOLCAT corre el **AWG Cloud Height Algorithm (ACHA)** extendido con módulo volcánico, basado en:

1. **Pavolonis M.J. (2010)**, "Advances in extracting cloud composition information from spaceborne infrared radiances—A robust alternative to brightness temperatures. Part I: Theory", *J. Appl. Meteor. Climatol.* 49: 1992–2012.
2. **Pavolonis M.J., Heidinger A.K., Sieglaff J. (2013)**, "Automated retrievals of volcanic ash and dust cloud properties from upwelling infrared measurements", *JGR Atmospheres* 118: 1436–1458, https://doi.org/10.1002/jgrd.50173.
3. **Pavolonis, Sieglaff, Cintineo (2018)**, "Spectrally Enhanced Cloud Objects (SECO)" — el motor de tracking 4D.

**Núcleo técnico**: inversión radiativa óptima (optimal estimation) que ajusta simultáneamente:
- Temperatura del tope (Tc)
- Espesor óptico (τ)
- Radio efectivo (Reff)

usando 3 canales IR (típicamente 11, 12 y 8.5 µm) contra un *forward model* RTM con perfil atmosférico (NWP, GFS). Luego mapea Tc → altura usando ese mismo perfil T(z).

Es **Wen-Rose moderno + retrieval bayesiano**, no un único umbral BTD.

### Precisión, cadencia, unidades

| Aspecto | Valor |
|---|---|
| Precisión Ash_Height | **±1–2 km** (plumas opacas) · ±3–4 km (τ<0.5 o cirrus debajo) |
| Sesgo | ~0.5 km cuando el tope está bien definido |
| Cadencia GOES-16/19 ABI | **10 min** full-disk · 5 min CONUS/Meso |
| Cadencia MODIS | 2 pasajes/día |
| Cadencia VIIRS (S-NPP, NOAA-20/21) | 1–2/día |
| Unidades | **km AMSL** (sobre nivel del mar), no AGL |

Validaciones publicadas: errores ±1.5–3 km vs CALIPSO en plumas medianas. Degrada en plumas ópticamente delgadas o sobre cirrus.

### Acceso técnico — RealEarth

- **Sin login** para imágenes públicas. Productos restringidos requieren `?appid=<token>`.
- **CORS habilitado**.
- **Endpoints**:
  - `/api/products` — lista productos
  - `/api/times?products=<id>` — timestamps disponibles
  - `/api/image?products=<id>&time=<UTC>&center=<lat,lon>&zoom=<z>` — PNG renderizado
  - `/tiles/...` — tiles WMTS estilo XYZ

### Punto crítico: PNG vs NetCDF

⚠ La API pública de RealEarth sirve **PNG/tiles renderizados con colorbar aplicado**, no NetCDF crudo con `ash_top_height` como float32. Dos caminos para obtener números:

1. **Reverse-mapping de colorbar PNG**: extraer pixel→valor con ~±0.5 km extra de incertidumbre. Frágil si SSEC cambia paleta. **Funciona pero quebradizo.**
2. **THREDDS/data feed institucional**: SSEC mantiene feed NetCDF para socios operacionales (VAACs, agencias). **Hay que solicitarlo** a CIMSS.
   - Contacto: Mike Pavolonis (mike.pavolonis@noaa.gov)
   - Helpdesk: helpdesk@ssec.wisc.edu
   - Argumento para SERNAGEOMIN: agencia volcanológica nacional de Chile, 43 volcanes activos, complementariedad con VAAC Buenos Aires.

### Restricciones

- Atribución obligatoria: "SSEC/CIMSS, University of Wisconsin–Madison".
- Política de datos: https://www.ssec.wisc.edu/data/data-policy/
- Rate limit no documentado; ≤ 1 req/s razonable.
- No comercial sin permiso.

---

## 2. Wen-Rose 1994 — implementación propia

### Fundamento físico

Wen S. & Rose W.I. (1994), *JGR* 99(D3): 5421–5431, https://doi.org/10.1029/93JD03340.

Asume nube **semitransparente** sobre fondo cálido. Resuelve simultáneamente:

```
BT11_obs = (1-t11)·B11(Tc) + t11·B11(Tsfc)
BT12_obs = (1-t12)·B12(Tc) + t12·B12(Tsfc)
```

con `t12 = t11^β` donde β depende del Reff (silicato típico β=0.85–0.95). Una vez obtenido **Tc**, se busca en el **perfil T(z)** la altitud → **Ash Height (km AMSL)**.

### Limitaciones

1. **Una sola capa, sin nubes meteorológicas debajo**. Cirrus subyacente sobreestima Tc.
2. **Tsfc conocida** (GOES SST/LST o GFS skin T).
3. **Pluma ópticamente delgada (τ<2)**. Plumas opacas (Calbuco 22-abr-2015 primeras horas) **subestiman 2–4 km**.
4. **Inversiones de T** crean ambigüedad (mismo Tc puede mapear a 2 alturas).
5. **Sobre estratopausa**: T(z) casi isotérmica → error grande.

Errores típicos vs CALIPSO: ±1.5–3 km en plumas medianas.

### Esfuerzo de implementación

**Factible** con la infra actual del repo:

- Inputs disponibles: bt11 (B14), bt12 (B15), máscara ash desde BTD<-1 ✅
- Faltaría sumar: Tsfc (GOES LST `ABI-L2-LSTC` o GFS surface T) y perfil T(z) de GFS via NOMADS/herbie
- Estimación: ~600–800 LOC Python, ~3 días de código + 1 semana de validación

Validación contra eventos conocidos:
- Calbuco 22-abr-2015 21:04 UTC (columna confirmada ~21 km)
- Hudson 1991
- Chaitén 2008

---

## 3. Alternativas evaluadas

| Fuente | Cobertura | Cadencia | Precisión | Veredicto |
|---|---|---|---|---|
| **CALIPSO/CALIOP** (LIDAR) | Swath 70 m | 16 días repaso, pasajes esporádicos | <100 m vertical (gold standard) | Solo validación posteriori. Misión activa cerró ago-2023 |
| **EarthCARE/ATLID** (sucesor CALIPSO) | Similar | Similar | Similar | Operacional desde may-2024. Mismo uso: validación |
| **IASI** (MetOp-A/B/C) | Global 2x/día | ~10:30 + 21:30 LT en Chile | Excelente para SO2 + altura SO2 | Complemento, no NRT GOES-style |
| **TROPOMI** (Sentinel-5P) | Global 1x/día (~13:30 LT) | 5.5×3.5 km | Altura SO2 ≠ altura ceniza | Útil para SO2 cuantitativo (DU) |
| **VAACs (Buenos Aires)** | Reportes texto WMO | 15-60 min latencia | Subjetiva (analista + piloto) | Ground truth operacional, no automatizable |
| **HYSPLIT / FALL3D / Ash3D** | — | — | Toman altura como **input** | Próximo eslabón, no fuente |

VAACs Buenos Aires URL: https://www.smn.gob.ar/vaac/buenosaires/inicio.php

---

## 4. Plan operativo decidido

### Fase 1 — Inmediata (1–2 días)

✅ **Extender el VOLCAT viewer existente del dashboard GOES** con nueva tab "Ash Height":

- Endpoint: `https://realearth.ssec.wisc.edu/api/image?products=ASH_HEIGHT_VILLARRICA_250M&time=latest` (y los demás sectores chilenos).
- Display: PNG renderizado con colorbar visible (sin extracción numérica todavía).
- Objetivo: consulta visual operacional NRT para los 4 volcanes prioritarios + los 3 mosaicos regionales.

### Fase 2 — Corto plazo (2 semanas)

⚠ **Solicitar formalmente a CIMSS** acceso al feed NetCDF VOLCAT.

- Email a mike.pavolonis@noaa.gov + cc helpdesk@ssec.wisc.edu
- Justificación: SERNAGEOMIN agencia volcanológica nacional, monitoreo de 43 volcanes activos.
- Mientras tanto: implementar **colorbar reverse-mapping** como fallback con disclaimer (+0.5 km incertidumbre extra).

### Fase 3 — Mediano plazo (1–2 meses)

⚠ **Implementar Wen-Rose 1994 propio como sistema de respaldo**:

- Razón 1: independencia operacional si SSEC se cae en momento crítico.
- Razón 2: reanálisis de eventos pre-2018 (VOLCAT operacional desde ~2018) — Calbuco 2015, Hudson 2011, Chaitén 2008.
- Razón 3: capacidad técnica del equipo (alineado con objetivo de independencia de mirovaweb.it).

Validar contra eventos conocidos antes de operacionalizar.

### Fase 3.5 — Decisiones técnicas precocinadas (sesión 2026-04-25, diferida)

Cuando se retome Wen-Rose, arrancar por estos puntos ya razonados:

**Orden de implementación (por qué)**: empezar por `gfs_profile.py` porque define la unidad de salida (sin T(z) no hay mapeo Tc→altura) y es lo más liviano de validar contra radiosonda Puerto Montt.

**Stack de fetching**:
- GFS T(z): NOMADS HTTP con byte-range GRIB2 (no herbie — agrega ~50 MB cfgrib+eccodes y Streamlit Cloud está apretado). Cache `@st.cache_data(ttl=3600)` por (lat, lon, ciclo_GFS). ~200 KB por perfil.
- Tsfc: GOES LST L2 (`ABI-L2-LSTC`) primario, GFS `tmpsfc` fallback cuando hay nubes met debajo (LST mete NaN). Flag de calidad en el output.

**Módulos previstos (~820 LOC total)**:
| Módulo | LOC |
|---|---|
| `src/fetch/gfs_profile.py` | ~150 |
| `src/fetch/goes_lst.py` | ~120 |
| `src/retrieval/wen_rose.py` | ~300 |
| `src/retrieval/validation.py` | ~100 |
| `tests/test_wen_rose.py` | ~150 |

**Parámetros físicos**:
- β = 0.9 fijo (silicato ácido típico Chile: andesita-dacita). No exponer en UI sin Reff retrieval — variarlo sin contexto es engañoso.
- Inversión térmica → tomar altura **superior** (pluma sobre PBL), warning si Δh > 2 km.

**Validación**: Calbuco 22-abr-2015 21:04 UTC (~21 km confirmado). En esa época era GOES-13, no GOES-19 → adaptar lector S3 al bucket `noaa-goes13`.

**UI**: sub-tab dentro de VOLCAT con label "Fallback Wen-Rose (independiente)", NO tab nueva. Deja claro que es plan B y no compite visualmente con el primario.

### Fase 4 — Largo plazo

Integrar altura H₀ con SO2 TROPOMI y forecast FALL3D para producto unificado tipo VAAC nacional. Esto cae en el proyecto `Pronostico_Cenizas/` ya scaffoldeado.

---

## Referencias bibliográficas

- Pavolonis (2010) Part I theory — *J. Appl. Meteor. Climatol.* 49:1992–2012
- Pavolonis et al. (2013) automated retrievals — *JGR Atmos* 118:1436–1458 doi:10.1002/jgrd.50173
- Pavolonis, Sieglaff, Cintineo (2018) SECO objects
- Wen & Rose (1994) — *JGR* 99(D3):5421–5431 doi:10.1029/93JD03340
- Clarisse et al. (2014) IASI SO2 LMD retrieval
- VAAC Buenos Aires — https://www.smn.gob.ar/vaac/buenosaires/inicio.php
- SSEC data policy — https://www.ssec.wisc.edu/data/data-policy/
- RealEarth API doc — https://realearth.ssec.wisc.edu/doc/api.php
