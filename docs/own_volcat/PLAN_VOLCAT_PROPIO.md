# Plan: VOLCAT propio — retrieval cuantitativo de altura de pluma desde GOES-19 ABI

**Fecha:** 2026-06-27 (plan) · **estado actualizado:** 2026-06-28
**Autor:** investigación asistida (Claude) para SERNAGEOMIN/OVDAS
**Objetivo:** evaluar y planificar generar **nuestro propio retrieval de altura de pluma
volcánica / ceniza** desde GOES-19 ABI L1b, para reducir la dependencia del único host
SSEC (`volcano.ssec.wisc.edu`), que tiene latencia ~30-50 min y caídas intermitentes.

> ## ESTADO DE IMPLEMENTACIÓN (2026-06-28)
> - **Fase 0 — HECHA y desplegada.** ACHA `HT` ∩ ceniza. `src/fetch/goes_acha.py` +
>   `src/process/acha_plume_height.py` + dashboard. Ver `FASE0_ARRANQUE.md`.
> - **Fase 2 — HECHA.** Perfil GFS T(z) + tropopausa vía Open-Meteo pressure levels:
>   `src/fetch/gfs_profile.py` (`fetch_gfs_profile`, `height_from_temp`). Cero deps.
> - **Fase 3a — HECHA.** BT-matching: `src/process/bt_matching_height.py`
>   (`bt_matching_top_height`). Altura propia **independiente de SSEC y de ACHA**.
>   Validado vs ACHA: Popocatépetl 26-jun BT 9.2 vs ACHA 10.3 km (Δ−1.1, cota
>   inferior ✓); Láscar 27-jun BT 6.2 km/15 px donde ACHA estaba en no_plume.
> - **Fase 3b — HECHA (2026-06-28).** Wen & Rose 1994: corrige emisividad con 2
>   canales (11/12 µm) → `Tc` corregido → altura. `src/process/wen_rose_height.py`
>   (`solve_tc_grid` puro + `clear_sky_bt` + `wen_rose_top_height`), Planck forward
>   en `brightness_temp.py`, skin-T GFS en `gfs_profile.py`. **Ts = BT de cielo
>   claro de la escena** (fallback GFS skin-T; **GOES LST rechazado**: NaN bajo la
>   pluma). Validado en Láscar real 27-jun: **BT-matching 6.8 km → Wen-Rose 10.4 km
>   (Δ+3.6 km)**, sube en semitransparente como se espera; ACHA=no_plume (Wen-Rose
>   rescata). 108 tests verde. Detalle en `FASE3B_WENROSE.md`.
> - **Hallazgo (Chillán 27-jun, pluma SO₂):** ni ACHA ni BT-matching ni Wen-Rose dan
>   altura a plumas de **gas/SO₂** (transparente en 11 µm → altura espuria bajo el
>   cráter). El dashboard lo explica con el contexto SO₂. Ver `reference_acha_so2_limit`.
> - **Pendiente:** Fase 1 (bandas C10/C16 + detección ATBD β-ratios — bloqueada por
>   el mismo gap RTM/clear-sky que la altura cuantitativa); Fase 4 (OE con pyCRTM —
>   NO salvo justificación).

> **TL;DR para el geólogo.** El producto de referencia (VOLCAT, Pavolonis 2013) NO se mide
> directo: la altura no es una variable de la ecuación de transferencia radiativa. Lo que
> realmente se "retrieva" es la **temperatura efectiva del tope de la nube (Teff)**, y luego
> se la convierte a kilómetros buscando ese Teff dentro de un **perfil vertical de temperatura
> T(z)** del modelo meteorológico (GFS). Todo lo demás del algoritmo (optimal estimation con 3
> canales IR, emisividad, radio efectivo, masa) existe para que ese Teff no esté sesgado cuando
> la pluma es semi-transparente. **La brecha real de nuestro proyecto no es la matemática: es el
> forward model radiativo + el perfil NWP vertical en NRT.** Sin esos dos, cualquier "altura"
> que calculemos es una cota, no un número VAAC. Hay un atajo honesto: leer el producto
> **ABI-L2-ACHAF** (Cloud Top Height de NOAA, ya calculado, está en el bucket `noaa-goes19`) y
> enmascararlo con nuestra detección de ceniza. Ese es el "VOLCAT-lite" de mejor relación
> esfuerzo/valor.

---

## 1. Síntesis del algoritmo VOLCAT (desde el ATBD GOES-R VolAsh v3.0 + papers)

Fuente primaria: `../ATBD_GOES-R_VolAsh_v3.0_July2012.pdf` (NOAA/NESDIS/STAR, secciones
3.4.2–3.4.5). Papers de respaldo descargados en esta carpeta (ver §6).

El producto baseline GOES-R se llama **"Volcanic Ash: Detection and Height" (ABI-VAA)**.
Tiene dos etapas encadenadas:

### 1.1 Etapa A — Detección (umbral + tri-espectral)

Usa **4 canales ABI**: 10 (7.4 µm), 11 (8.5 µm), 14 (11 µm), 15 (12 µm).
- Construye la firma de ceniza con **β-ratios** (cocientes de absorción espectral escalada):
  `β(8.5/11µm)` y `β(12/11µm)`, comparados contra los valores teóricos de ceniza dados por la
  dispersión simple (single-scatter) de partículas de silicato.
- Hace dos hipótesis de capa: *single-layer tropopause* (pluma sola) y *multilayered tropopause*
  (pluma sobre nube meteorológica más baja) — esto es lo que evita el sesgo de cirros debajo.
- Esto es, conceptualmente, **lo que ya hacemos** en `src/process/ash_detection.py` con BTD<-1
  + test tri-espectral, pero la versión ATBD es más fina (β-ratios + dos hipótesis de capa +
  confianza 2-D contra la curva teórica).

### 1.2 Etapa B — Retrieval cuantitativo (Optimal Estimation / 1DVAR)

Esto es **lo que NO tenemos**. A cada pixel marcado como posible ceniza se le corre una
inversión de optimal estimation (Rodgers 1976, también llamada 1DVAR). Detalle exacto del ATBD:

**Canales del retrieval: 14 (11 µm), 15 (12 µm), 16 (13.3 µm).** La 13.3 µm (canal de absorción
de CO₂) es la que aporta sensibilidad a la **altura** — es el corazón de por qué necesitamos una
banda que hoy NO descargamos.

**Vector de observaciones** `y` (3 elementos):
- BT(11 µm)
- BTD(11 − 12 µm)
- BTD(11 − 13.3 µm)

**Vector de estado retrieved** `x` (3 parámetros):
- `Teff` — temperatura efectiva de la nube
- `ε(11µm)` — emisividad de nube a 11 µm
- `β(12/11µm)` — razón de profundidad óptica de absorción efectiva 12/11 (lleva la microfísica)

> Nota clave del ATBD (línea textual): *"The ash height and mass loading cannot be retrieved
> directly because they are not variables in the cloudy infrared radiative transfer equation."*
> Por eso el state vector es Teff/ε/β y la altura es un **post-proceso**.

**Función de costo minimizada** (Eq. 24): `φ = (y − f(x))ᵀ Sy⁻¹ (y − f(x)) + (x − xa)ᵀ Sa⁻¹ (x − xa)`
- `f(x)` = **forward model** radiativo (Eqs. 27-31): predice las radiancias de los 3 canales dado
  el estado, usando radiancia de nube negra `Rcld(λ)`, transmitancia clara y radiancia de cielo
  claro provenientes del **RTM + perfil NWP**.
- `Sy` = covarianza de error del forward model (Table 12). `Sa` = covarianza a priori (diagonal).
- `xa` (a priori, Table 11): `Teff_ap = BT(11µm) − 15 K`; `ε(11µm)_ap = 1 − exp(−0.5/cos θsat)`;
  `β(12/11µm)_ap = 0.8`. Incertidumbres a priori: σTeff=40 K, σε=0.5, σβ=0.3.
- Iteración Newton-Gauss (Eq. 45) con Jacobiano `K`, máximo **10 iteraciones**, paso `δx`
  acotado (ΔTeff≤20 K, Δε≤0.3, Δβ≤0.2), parámetros recortados a rango físico (Table 13:
  Teff∈[160,330]K, ε∈[0,1], β∈[0.20,1.05]).

**Post-proceso → productos finales:**
- **Ash cloud height [km]** (Eq. 49): se localiza `Teff` dentro del **perfil T(z) del NWP**
  (recortado entre superficie y tropopausa) y se interpola linealmente a altura. *Esta es la
  conversión Teff→altura, y depende enteramente de tener el perfil vertical de GFS.*
- **Ash mass loading [tons/km²]** (Eqs. 50-54): de `ε(11µm)`→τ(11µm), `β`→reff y σ_ext, asumiendo
  distribución lognormal (σ=0.74, Wen & Rose 1994), densidad ρash=2.6 g/cm³.
- **Effective radius reff [µm]**: de `β(12/11µm)` por regresión (Eqs. 22-23).
- **Ash probability / confidence**: de la etapa de detección.

**Inputs ancillary obligatorios** (sección 3.3 del ATBD):
1. Radiancias/BT calibradas canales 10, 11, 14, 15, 16 + flags de calidad L1b. *(tenemos 11,14,15;
   faltan 10 y 16)*
2. Ángulo cenital del satélite. *(derivable de geometría, ya tenemos `geo.py`)*
3. **Emisividad de superficie IR** canales 14 y 15 (base de datos climatológica mensual, Seemann
   et al. 2008). *(no tenemos)*
4. **Perfiles NWP** de presión, temperatura y altura geopotencial (GFS) + nivel de tropopausa.
   *(tenemos solo viento de Open-Meteo, NO el perfil T(z) completo)*
5. **Perfiles de radiancia de nube negra** y **transmitancia de cielo claro** por canal,
   precalculados con un **RTM** (PFAAST en NOAA) como función de la celda NWP y la geometría.
   *(no tenemos — este es el forward model)*

**Precisión publicada (Table 21 + validación CALIOP):** altura ±1-2 km en plumas opacas, peor
(±3-4 km, sesgo negativo) en plumas ópticamente delgadas (τ<0.5) o con cirros debajo.

---

## 2. Gap analysis — qué tenemos vs. qué falta

| Componente del algoritmo | ¿Lo tenemos? | Dónde / qué falta |
|---|---|---|
| Acceso L1b GOES-19 sin credenciales | ✅ | `src/fetch/goes_s3.py` (s3fs anon, bucket `noaa-goes19`) |
| Coeficientes Planck (Rad→BT) | ✅ | `src/process/brightness_temp.py` lee `planck_fk1/fk2/bc1/bc2` del NetCDF |
| Banda 11 µm (C14) | ✅ | `VOLCANIC_BANDS` en `src/config.py` |
| Banda 12 µm (C15) | ✅ | idem |
| Banda 8.5 µm (C11) | ✅ | idem (la usamos como 8.4 en SO2/ash) |
| **Banda 7.4 µm (C10)** | ❌ | **falta descargar** (detección multilayer) |
| **Banda 13.3 µm (C16)** | ❌ | **falta descargar — es la que da la ALTURA** |
| BTD split-window 11-12 | ✅ | `src/process/ash_detection.py::compute_btd_split_window` |
| Detección tri-espectral | ✅ (versión simple) | `detect_ash_enhanced` — falta β-ratios + 2 hipótesis de capa del ATBD |
| Confianza de detección 0-3 | ✅ (heurística) | `compute_ash_confidence` — no es la confianza 2-D contra curva teórica |
| Geometría / ángulo cenital satélite | ✅ (parcial) | `src/process/geo.py`, `GOES19_SAT_LON`, pyproj GEOS |
| **Perfil vertical T(z) de NWP (GFS)** | ❌ | tenemos solo **viento** de Open-Meteo; falta el perfil T/altura completo + tropopausa |
| **Emisividad de superficie IR (clim. mensual)** | ❌ | base SeeBor/Seemann 2008 no integrada |
| **Forward radiative transfer model (RTM)** | ❌ | núcleo ausente (NOAA usa PFAAST; alternativas: CRTM, RTTOV, LUT propia) |
| **Esquema de optimal estimation (1DVAR)** | ❌ | hay que escribirlo (cost function, Jacobiano, Newton, Sa/Sy) |
| **Microfísica de ceniza (índices refracción, σ_ext, β↔reff)** | ❌ | tablas de Pavolonis/Newman/Prata no integradas |
| **Validación contra ground truth** | ❌ parcial | tenemos eventos benchmark identificados (Calbuco 2015, Puyehue 2011) pero sin pipeline de validación |
| Producto **ACHA Cloud Top Height** de NOAA (atajo) | ⏸️ disponible, no integrado | `ABI-L2-ACHAF` **SÍ está** en el bucket `noaa-goes19` (verificado); variable `HT` en km |

**Brecha principal en una frase:** tenemos la mitad fácil (bandas, Planck, BTD, detección), pero
nos faltan las **dos piezas caras** del retrieval cuantitativo —(1) el **forward model radiativo
acoplado a un perfil NWP vertical en NRT** y (2) el **esquema de optimal estimation con microfísica
de ceniza**. Reimplementar el OE completo de NESDIS es un proyecto de meses, frágil, y daría un
producto *inferior* al VOLCAT que SSEC entrega gratis. Lo sensato es un **VOLCAT-lite** que entregue
altura aproximada con disclaimer, y reservar el número cuantitativo "VAAC-grade" para VOLCAT/RealEarth.

---

## 3. ¿Hay código open-source reutilizable? (investigación online, APIs gratis)

Respuesta corta: **no hay un módulo Python liviano que haga el retrieval OE de altura de ceniza.**
Todo el código serio es Fortran enterprise que exige RTM compilado + NWP operacional.

| Software | URL | Licencia | Lenguaje | ¿GOES ABI? | ¿Altura cuant. de ceniza? | Deps pesadas | Reusabilidad |
|---|---|---|---|---|---|---|---|
| **CSPP Geo / VOLCAT** | cimss.ssec.wisc.edu/csppgeo, volcano.ssec.wisc.edu | no distribuido | — | sí (operacional) | sí | es servicio, no código | **NULA** (solo consumir output, ya lo hacemos) |
| **CLAVR-x** (ACHA+PFAAST+ash) | svn.ssec.wisc.edu/repos/cloud_team_clavrx | US-gov de facto abierto | Fortran-90 | sí | sí | PFAAST RTM + NWP GFS GRIB + HDF4 | **BAJA** |
| **ORAC** | github.com/ORAC-CC/orac | GPL-3.0 | Fortran (+C) | sí | **sí** (OE completo: altura, reff, masa) | RTTOV v13 + ERA5 + netCDF-Fortran | **BAJA** |
| **pyCRTM / CRTM v3** | github.com/JCSDA/pycrtm, github.com/JCSDA/CRTMv3 | CC0 / Apache-2 | Fortran+Python | sí (trae coef. `abi_g19`) | no (solo forward RT) | un compile Fortran (cmake+gfortran) | **MEDIA** (mejor RTM libre, vos das perfiles) |
| **pyRTTOV / RTTOV** | nwpsaf.eu/site/software/rttov | libre c/ registro NWP-SAF | Fortran+f2py | sí | no | compilar + registro + coef. | **BAJA-MEDIA** |
| **satpy** | github.com/pytroll/satpy | GPLv3 | Python | sí | **no** (`ash` es solo RGB; `cloud_top_height` solo *visualiza* CTH pre-calculado) | xarray/dask (livianas) | **MEDIA-ALTA** como lector/visualizador, NULA como retrieval |
| **pyspectral** | github.com/pytroll/pyspectral | GPLv3/Apache | Python puro | sí | no | ninguna (pip) | **ALTA** para utilidades (SRF, Planck/BT), NULA como forward model |
| **NOAA enterprise VAA (GEOCAT)** | solo ATBD público | no abierto | Fortran/C | sí | sí | NWP+CRTM+HDF | **NULA** |
| Repos Python livianos (Wen&Rose, CO2-slicing, WV-intercept) | — | — | — | — | — | — | **no existen** (solo papers, cero implementaciones en GitHub/PyPI) |

**Conclusión de reutilización:** no hay nada importable tal cual. ORAC y CLAVR-x hacen el retrieval
de verdad y bien (ORAC validado en Raikoke 2019), pero ambos son sistemas Fortran que exigen RTM
compilado + NWP operacional — exactamente el stack pesado que queremos evitar en un dashboard
Streamlit. El "VOLCAT-lite en Python" más honesto y cercano para equipo chico es:
**leer `ABI-L2-ACHAF` (variable HT, km) del bucket que ya consultamos + enmascarar con nuestra
detección BTD/Ash-RGB** (reusabilidad ALTA, cero deps nuevas), usando **satpy** como lector L2 y
**pyspectral** para utilidades BT/SRF. Si algún día se quiere el OE propio, la base más realista es
**pyCRTM** (CC0, trae coeficientes ABI, un solo compile) + ERA5/GFS vía xarray + escribir una
inversión OE de 1-3 parámetros nosotros.

---

## 4. Plan por fases (camino realista para este proyecto)

Filosofía (alineada con `CLAUDE.md`): **no inventar números VAAC**. Etiquetar todo lo propio como
*indicativo*, reservar el cuantitativo validado para VOLCAT/RealEarth, y construir de menor a mayor
esfuerzo, validando cada paso contra eventos conocidos.

### Fase 0 — Atajo ACHA (mejor relación esfuerzo/valor) · ~1-2 días
**Qué se construye:** fetcher de `ABI-L2-ACHAF` desde `noaa-goes19` (mismo patrón que `download_fdc`),
lectura de la variable de altura de tope de nube (`HT`, km) y reproyección con `geo.py` ya existente.
Enmascarar `HT` con nuestra máscara de ceniza (`detect_ash_enhanced`) para mostrar "altura del tope
donde hay firma de ceniza".
**Datos/deps que faltan:** ninguno nuevo (s3fs+xarray ya están).
**Riesgos/limitaciones:** ACHA es retrieval de **nube genérica**, no afinado a microfísica de ceniza
→ sesga en plumas semi-transparentes igual que BT-matching. Es **aproximación defendible, NO el
producto VAA**. Etiquetar claramente: "Cloud Top Height (NOAA ACHA) enmascarado por ceniza —
indicativo". Latencia ACHA ~5-15 min (mucho mejor que los 30-50 min de RealEarth).
**Win:** altura cuantitativa propia, independiente de SSEC, con cero stack nuevo, casi inmediata.

### Fase 1 — Descargar las bandas que faltan + detección ATBD-grade · ~2-3 días
**Qué se construye:** agregar **C10 (7.4 µm)** y **C16 (13.3 µm)** a `VOLCANIC_BANDS`. Refinar la
detección hacia la versión del ATBD: β-ratios `β(8.5/11)`/`β(12/11)`, las dos hipótesis de capa
(single/multilayer tropopause), y la confianza 2-D contra la curva teórica de ceniza.
**Datos/deps que faltan:** la 13.3 µm habilita CO₂-slicing/altura más adelante; ambas son L1b
gratis en S3.
**Riesgos:** más descargas por scan (2 bandas extra → +40% datos/scan). Manejable con el cache
existente. Sin perfil NWP la 13.3 µm aún no da altura cuantitativa; queda lista para Fase 3.

### Fase 2 — Perfil NWP vertical T(z) en NRT · ~3-4 días
**Qué se construye:** `src/fetch/gfs_profile.py` que baje el perfil vertical de **temperatura y
altura geopotencial** (no solo viento) de GFS, por (lat, lon, ciclo), con cache. Detectar nivel de
**tropopausa**. (Decisión ya precocinada en `ALTURA_COLUMNA_INVESTIGACION.md` §3.5: NOMADS HTTP con
byte-range GRIB2 para no agregar cfgrib+eccodes pesados; o Open-Meteo pressure levels como fallback
ligero.)
**Datos/deps que faltan:** acceso GFS T(z). Riesgo de peso de eccodes en deploy HF — mitigado con
byte-range o API REST de niveles de presión.
**Riesgos:** GFS tiene resolución vertical/horizontal gruesa; el perfil cerca de inversiones puede
dar mapeo Teff→altura ambiguo (tomar rama superior, warning si Δh>2 km).
**Habilita:** la conversión Teff→altura (Eq. 49) de cualquier método posterior.

### Fase 3 — Altura por método simple (BT-matching / Wen-Rose) · ~1-2 semanas código + validación
**Qué se construye:** retrieval de altura "VOLCAT-lite físico" sin OE completo:
- **3a (mínimo):** BT-matching directo — `Teff ≈ BT(11µm)` del tope opaco, mapeado al perfil GFS
  de Fase 2. Cota inferior, subestima en semi-transparente.
- **3b (mejor) — ✅ HECHA:** **Wen & Rose 1994** de 2 canales (11/12 µm) para despejar la emisividad
  y obtener un Teff corregido antes de mapear a altura (resuelve nube semitransparente sobre fondo
  cálido). **Tsfc decidido: BT de cielo claro de la propia escena** (= la "Ts" del paper, ya en el
  marco radiométrico de ABI), con **GFS skin-T** (`surface_temperature` de Open-Meteo) como fallback;
  **GOES LST `ABI-L2-LSTC` rechazado** (NaN justo bajo la pluma + sobre océano + fetcher nuevo). β=0.9
  fijo (andesita-dacita). Implementado en `src/process/wen_rose_height.py` con búsqueda en grilla del
  mínimo residuo (robusta a tangencia en plumas finas). Ver `FASE3B_WENROSE.md`.
**Datos/deps que faltan:** Tsfc (LST o GFS), tablas microfísicas mínimas.
**Riesgos:** sigue subestimando plumas opacas gruesas (Calbuco primeras horas); inversiones de T
crean ambigüedad. Es producto **research/respaldo**, etiquetado "fallback independiente", nunca
compite con VOLCAT como primario.
**Validación:** Calbuco 22-abr-2015 (~21 km, OJO era GOES-13 → bucket `noaa-goes13`),
Puyehue-Cordón Caulle 2011, contra reportes GVP / radar / cámaras térmicas SERNAGEOMIN.

### Fase 4 (opcional, ambiciosa) — Optimal Estimation propio con pyCRTM · meses, alto riesgo
**Qué se construye:** el OE 3-parámetros del ATBD (Teff, ε, β) con forward model vía **pyCRTM**
(CC0, trae coeficientes ABI g19) + perfil GFS de Fase 2 + microfísica de ceniza de Pavolonis 2010 /
Prata. Inversión Newton-Gauss propia (Eqs. 24-49).
**Datos/deps que faltan:** un compile Fortran de CRTM (gfortran+cmake+git-lfs) — rompe la promesa
"Python puro" del deploy; tablas de índices de refracción de ceniza; emisividad de superficie SeeBor.
**Riesgos:** alto. Es replicar trabajo de un equipo NESDIS completo; el producto será inferior al
VOLCAT operacional; el RTM Fortran no encaja en Streamlit Cloud/HF Spaces sin contenedor pesado.
**Recomendación:** **NO emprender salvo** que aparezca un caso de uso fuerte (reanálisis histórico
masivo pre-2018, o requisito operacional de número propio auditable). Para reanálisis histórico,
preferir Wen-Rose (Fase 3b) que ya cubre eventos pre-VOLCAT.

### Resumen de esfuerzo

| Fase | Entrega | Esfuerzo | Dependencia nueva | Recomendación |
|---|---|---|---|---|
| 0 | ACHA CTH enmascarado por ceniza | 1-2 días | ninguna | **HACER YA** |
| 1 | Bandas C10/C16 + detección ATBD-grade | 2-3 días | ninguna | hacer |
| 2 | Perfil NWP T(z) + tropopausa | 3-4 días | acceso GFS T(z) | hacer (habilita altura) |
| 3 | BT-matching / Wen-Rose (altura indicativa propia) | 1-2 sem | Tsfc (LST/GFS) | hacer como respaldo |
| 4 | OE completo con pyCRTM | meses | CRTM Fortran + microfísica | **NO salvo justificación fuerte** |

**Camino recomendado:** Fase 0 inmediata (gran win, cero riesgo) → Fases 1-2 → Fase 3b (Wen-Rose)
como producto de respaldo independiente. Mantener VOLCAT/RealEarth como primario cuantitativo.
**Saltar Fase 4** salvo aparición de un requisito que lo justifique.

---

## 5. Alternativas más simples ya esbozadas (no reinventar)

Mucho de esto ya está razonado en docs locales — leerlos antes de codear:
- `../altura_pluma/metodos_fisicos.md` — BT-matching, parallax GOES-East/West, CO₂-slicing, VOLCAT.
- `../ALTURA_COLUMNA_INVESTIGACION.md` — decisión VOLCAT-primero + Wen-Rose fallback, con stack de
  fetching, módulos (~820 LOC) y parámetros físicos ya precocinados (§3.5).
- `../VOLCAT_LATENCIA_Y_ALTERNATIVAS.md` — por qué la latencia de SSEC es inherente; recomendación
  pragmática (detección rápida propia + altura vía VOLCAT validado).
- `../altura_pluma/VOLCAT_api_reference.md` — el API REST de RealEarth que ya consumimos.

---

## 6. Referencias

**Documento maestro (la receta):**
- ATBD GOES-R Volcanic Ash v3.0 (NOAA/NESDIS/STAR, jul 2012) — `../ATBD_GOES-R_VolAsh_v3.0_July2012.pdf`
  (secciones 3.4.2 detección, 3.4.4 optimal estimation, 3.4.4.5 altura, 3.4.4.6 masa).

**Papers (PDFs OA descargados en esta carpeta):**
- Pavolonis (2010) *Advances in extracting cloud composition information from spaceborne infrared
  radiances. Part I: Theory.* J. Appl. Meteor. Climatol. 49:1992-2012. doi:10.1175/2010JAMC2433.1
  → `Pavolonis_2010_CloudCompositionTheory.pdf` (base teórica de β-ratios y emisividad efectiva)
- Heidinger & Pavolonis (2009) *Gazing at Cirrus Clouds for 25 Years through a Split Window. Part I:
  Methodology.* J. Appl. Meteor. Clim. 48:1100-1116. doi:10.1175/2008JAMC1882.1
  → `HeidingerPavolonis_2009_SplitWindowCirrus.pdf` (base del ACHA y de las a priori del OE)

**Papers clave NO descargables (anti-bot / paywall) — copia OA conocida:**
- Pavolonis, Heidinger, Sieglaff (2013) *Automated retrievals of volcanic ash and dust cloud
  properties from upwelling infrared measurements.* JGR Atmos 118:1436-1458. doi:10.1002/jgrd.50173
  → OA (bronze) en `onlinelibrary.wiley.com/doi/pdfdirect/10.1002/jgrd.50173` — bloqueado por
  Cloudflare JS; bajar con navegador real. **Es el paper canónico del retrieval.**
- Pavolonis et al. (2015) *SECO Part 2: Volcanic ash detection retrievals.* JGR Atmos 120:7842-7870.
  doi:10.1002/2014JD022969 → OA (hybrid CC-BY-NC-ND) en Wiley pdfdirect; mismo bloqueo.
- Wen & Rose (1994) *Retrieval of sizes and total masses of particles in volcanic clouds using AVHRR
  bands 4 and 5.* JGR 99(D3):5421-5431. doi:10.1029/93JD03340 → ✅ **DESCARGADO** (copia GREEN de
  `digitalcommons.mtu.edu/geo-fp/98`, tras AWS WAF JS challenge resuelto con navegador real):
  `WenRose_1994_VolcanicCloudParticles.pdf`. **Base del método Wen-Rose de Fase 3b** (Eq. 1-2 = modelo
  de radiancia de 2 canales; ver `FASE3B_WENROSE.md` §2).
- Prata (1989) *Infrared radiative transfer calculations for volcanic ash clouds.* GRL 16:1293-1296.
  doi:10.1029/GL016i011p01293 → **paywall puro**, sin OA. (Base teórica del BTD split-window.)

**Código open-source (investigado, ver §3):**
- ORAC — github.com/ORAC-CC/orac (GPL-3, Fortran, OE completo, requiere RTTOV+ERA5)
- CLAVR-x — svn.ssec.wisc.edu/repos/cloud_team_clavrx (Fortran, ACHA+PFAAST)
- pyCRTM / CRTM v3 — github.com/JCSDA/pycrtm (CC0/Apache, RTM con coef. ABI)
- satpy / pyspectral — github.com/pytroll (lectura/utilidades, NO retrieval de altura)

**Atajo de datos verificado:**
- `ABI-L2-ACHAF` (Cloud Top Height NOAA) **presente** en bucket `noaa-goes19` — variable de altura
  en km, leíble con s3fs+xarray sin deps nuevas. Base de la Fase 0.
