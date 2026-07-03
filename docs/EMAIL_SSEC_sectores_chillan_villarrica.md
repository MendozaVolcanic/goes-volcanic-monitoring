# Borrador de correo a VOLCAT (NOAA/CIMSS) — reactivar sector Villarrica + sector nuevo Chillán + acceso a datos

> **Verificado contra la API viva de VOLCAT (jul 2026, 172 sectores) + investigación de fuentes:**
> - **Cobertura VOLCAT de Sudamérica (estado real por sector, campo `sat`):** ACTIVOS en GOES‑19 →
>   Copahue_250_m, Calbuco_1_km, Planchon-Peteroa_500_m, Reventador_250_m, Sabancaya_250_m,
>   Ruiz_250_m, Ubinas_250_m, Tungurahua_250_m, Cotopaxi_150_m, Chiles_250_m, Purace_500_m,
>   Colombia_750_m, Ecuador_750_m, Peru_750_m + regionales Chile N/C/S y Argentina.
>   **DORMIDO → `Villarrica_250_m` es el ÚNICO sector sudamericano con `sat:[]` e `image_type:[]`**
>   (definido con coordenadas válidas, pero sin satélite asignado ni productos).
> - **NO existe** ningún sector para Nevados de Chillán (búsqueda "Chillan"/"Nevados" = 0) → crear es genuino.
> - **Fuente que valida el pedido:** NESDIS/CIMSS declara que *"for inquiries about VOLCAT, including
>   sector coverage requests, the VOLCAT Point of Contact is Mike.Pavolonis@noaa.gov"* y que los
>   observatorios volcánicos son usuarios previstos → pedir cobertura es un mecanismo real.
> - **El dato gridded que pedimos SÍ está documentado** (no es un invento): el output nativo del
>   algoritmo — altura de tope como *geopotential height* en metros, carga, radio efectivo, DQF —
>   está especificado en el **ATBD GOES‑R VolAsh v3.0 (2012, local)** y en Pavolonis et al. 2013. El
>   PNG del portal es el render con colorbar de esos float32; nosotros lo reverse-mapeamos (frágil).
> - **Ojo (no afirmar):** (a) **CSPP Geo NO tiene paquete VOLCAT/ceniza** (sus 9 paquetes son GRB,
>   AIT, GEOCAT, Geo2Grid, GLM, LightningCast, Flood, AXI, GVAR) → NO ofrecer "correlo local". (b) El
>   baseline **ABI‑L2‑VAAF es experimental, no operacional en GOES‑18/19** → NO citarlo como disponible.
>   El canal correcto es el feed de socios operacionales / la transición a **NCCF** (anuncio feb‑2026).

**Para:** **Michael Pavolonis — mike.pavolonis@noaa.gov** (POC de VOLCAT, NOAA/NESDIS/STAR;
confirmado por NESDIS como contacto para *sector coverage requests*).
**CC sugerido:** Justin Sieglaff (CIMSS/SSEC, equipo VOLCAT) — confirmar dirección en
people.ssec.wisc.edu antes de enviar. Opcional: contacto del VAAC Buenos Aires.
**De:** [tu nombre], OVDAS / SERNAGEOMIN, Chile
**Asunto:** VOLCAT sector coverage for Chile — reactivating Villarrica and adding Nevados de Chillán

---

Dear Dr. Pavolonis and the VOLCAT team,

I am [name], a geologist at the Southern Andes Volcano Observatory (OVDAS),
SERNAGEOMIN, the agency responsible for Chile's National Volcano Surveillance
Network (RNVV). We operate a near‑real‑time GOES‑19 monitoring dashboard that
routinely ingests your VOLCAT products (ash cloud height, loading, probability and
effective radius), including your active dedicated Chilean sectors —
`Copahue_250_m`, `Calbuco_1_km` and `Planchon-Peteroa_500_m`. They are a valuable
complement to our own ABI ash retrievals, and we are grateful for them.

I am writing with two coverage requests for Chile and one question about data access.

**1 — Reactivating the existing `Villarrica_250_m` sector.**
While reviewing your sector list we noticed that a `Villarrica_250_m` sector is
already defined (with valid coordinates), but it does not appear to be producing
imagery — its satellite and product lists are empty, and we find no BT11µm or
Ash_Height frames for it. As far as we can tell it is the **only South American
sector currently dormant**: every other major Andean volcano you cover — Copahue,
Reventador, Sabancaya, Nevado del Ruiz, Ubinas, Tungurahua, Cotopaxi, Chiles,
Puracé — has an active high‑resolution sector. Given that Villarrica is one of the
most persistently active volcanoes in the Andes (near‑continuous lava lake and
frequent Strombolian activity), **could this sector be reactivated?** We would value
it for the **VIIRS** retrievals (M‑band ash‑top‑height at 750 m, I‑band masking at
375 m), which genuinely resolve small, crater‑scale plumes at a native resolution
the 2 km GOES‑ABI cannot reach. Concretely, your validated, operational VIIRS
product would give us (a) a trusted reference to cross‑validate our own
ash‑top‑height retrievals — currently from GOES‑ABI, and a VIIRS 750 m retrieval we
are now developing in‑house — and (b) the mass‑loading, effective‑radius and
probability fields we do not compute. If GOES‑19 ABI can also be assigned to the
sector for continuity between polar overpasses, all the better, though we understand
that on ABI the sector remains at the ~2 km native IR resolution.

**2 — A new dedicated sector for Nevados de Chillán.**
Nevados de Chillán (−36.86, −71.38) is currently in eruption and under active
surveillance, but it has **no dedicated sector** — it is only covered by the
regional `Chile_Central_2_km` (2 km/pixel). Its plumes are typically crater‑scale
and low‑altitude (lava‑dome degassing, modest ash columns), so at 2 km the plume
occupies only a few mixed pixels, near the effective detection scale of the regional
product. A dedicated sector — like those you already produce for comparable
volcanoes — would help, and to be concrete about where the benefit comes from: the
real gain for these small plumes would be **VIIRS coverage** on the sector (375 m /
750 m, which genuinely resolves incipient plumes) and/or **detection thresholds
tuned** for a crater‑scale source, rather than the sector grid spacing per se — we
recognise that an ABI‑only sector stays at the ~2 km native IR resolution regardless
of the output grid. We would gladly provide preferred bounds and event history.

**3 — Access to the gridded (NetCDF) values behind the imagery.**
As documented in the GOES‑R Volcanic Ash ATBD (v3.0, 2012), Pavolonis et al. (2013),
and the GOES‑R Series volume chapter "Remote Sensing of Volcanic Ash with the GOES‑R
Series" (Pavolonis et al., 2020), the retrieval produces per‑pixel gridded fields —
ash cloud top height (a geopotential height, in metres), mass loading, effective
radius and quality flags.
The public portal, however, serves these only as PNGs with the value baked into a
colour scale; we currently recover approximate numbers by reverse‑mapping the colour
bar, which adds ~1–2 km of avoidable error. For quantitative cross‑validation of our
own ash‑top‑height retrieval and for our alert workflow, access to the underlying
**gridded values (NetCDF / data feed)** would be far more reliable — ideally the
VOLCAT product fields (which populate only within detected volcanic clouds), rather
than the baseline full‑disk product, since automated detection over the complex
Andean terrain is prone to false positives. Could you tell us whether such access is
available to a national volcano observatory — for example
through the operational‑partner feed, or the forthcoming NCCF distribution as VOLCAT
transitions to NOAA operations — and what the process would be? **Of the three
requests, this gridded‑data access is the one we would prioritise:** as we develop
our own open‑source retrievals, a validated VOLCAT ground‑truth is what we most need
to benchmark them against, and it would benefit every sector you already run rather
than a single volcano.

This work supports SERNAGEOMIN's volcanic‑alert decision‑making. Both Villarrica and
Nevados de Chillán rank among Chile's highest‑hazard volcanoes and are currently at
elevated alert levels. We would be happy to share event histories, typical plume
heights and preferred sector extents, and to coordinate on validation.

Thank you very much for considering this, and for maintaining VOLCAT — it is a
genuinely valuable resource for us.

Best regards,
[name]
[role / e‑mail / phone]
OVDAS — Observatorio Volcanológico de los Andes del Sur, SERNAGEOMIN, Chile

---

### Notas para vos (no enviar)
- **Estructura:** 3 pedidos ordenados de más fácil/creíble a más grande — (1) Villarrica es un
  *switch on* de algo ya definido y es el ÚNICO dormido de Sudamérica (pedido quirúrgico, muestra
  que hicimos la tarea); (2) Chillán es un sector nuevo; (3) datos gridded como consulta. Abrir
  reconociendo que YA usamos sus sectores activos chilenos da credibilidad.
- **RANKING de valor real para nosotros (jul-2026, decidido):** el pedido de mayor impacto es el
  **#3 (datos gridded NetCDF)** — nos saca el error de ±1-2 km del reverse-mapping del PNG en TODOS
  los sectores y TODO el tiempo, no solo cuando pasa un satélite polar. Después #1 (VIIRS alta-res
  ocasional en Villarrica) ≈ #2 (Chillán, **solo si es VIIRS-enabled o con detección tuneada**). La
  carta mantiene el orden fácil→grande por retórica, pero si hay que priorizar en un follow-up, el
  gridded es el que mueve la aguja.
- **Estado VIIRS propio (ACTUALIZADO jul-2026):** SÍ estamos construyendo un retrieval de ALTURA
  VIIRS 750 m propio (`src/process/viirs_wen_rose.py`, Fases 1-2 hechas + testeadas, validación en
  vivo pendiente de un EARTHDATA_TOKEN). Resultó de días —no meses— porque **reusamos la infra de
  VRP Chile** (auth NASA, geolocalización de swath, calibración BT), que ya tenía resuelta la parte
  cara de la geometría polar. NO construimos VIIRS térmico (eso es VRP Chile). Entonces, ¿por qué
  seguir pidiéndole VIIRS a SSEC? Porque su producto está **validado y operacional** (el nuestro es
  prototipo), da **carga/reff/probabilidad/máscara 375 m** que no calculamos, y es el **ground-truth**
  para validar el nuestro. Por eso el correo ahora menciona el retrieval propio "en desarrollo" (nos
  posiciona como colaborador serio) y refuerza el #3 (gridded) como prioridad — es lo que más
  necesitamos para benchmarkear lo que construimos.
- **OJO — el 250 m ABI "pelado" NO ayuda:** la ganancia de resolución en un sector viene de VIIRS
  (375/750 m) o de detección tuneada, NO de la grilla del raster: un sector alimentado solo con ABI
  sigue siendo 2 km nativo re-muestreado (ver `REGISTRO_PAPER §9`). Por eso los pedidos #1 y #2 ahora
  dicen explícito "VIIRS / detección tuneada" — para no pedir algo que no nos serviría.
- **Todo verificado contra la API viva** (campo `sat`/`image_type` por sector). Villarrica_250_m
  tiene coordenadas válidas pero `sat:[]` → definido pero sin producción. Re-chequear antes de enviar:
  `python -c "from src.fetch.volcat_api import _query_frames; print(len(_query_frames('Villarrica_250_m','ABI','BT11um','all')[0]))"`
  (si pasa de 0, ya lo reactivaron → ajustar el punto 1).
- **NO es bug nuestro** usar 2 km para Villarrica: como el 250 m está apagado, apuntar ahí daría
  pantalla en blanco. Si SSEC lo reactiva, agregar `"Villarrica": ("Villarrica_250_m","ABI")` a
  `VOLCANO_TO_SECTOR` para que el dashboard use el 250 m.
- **NetCDF como consulta:** VOLCAT es producto operacional de NOAA usado por los VAACs, el dato base
  es gridded; el pedido es razonable pero NO afirmamos un endpoint que no verifiqué — que ellos confirmen.
- **Contacto verificado:** NESDIS/CIMSS nombra a mike.pavolonis@noaa.gov como POC para *sector
  coverage requests*. Sieglaff sigue en el equipo VOLCAT (autor en el blog volcano.ssec.wisc.edu).
- Ajustá nivel de alerta y datos de actividad del momento (columnas típicas en m, frecuencia de
  pulsos) — refuerza el pedido. Un sector 250 m cubre ~200×190 km; 500 m ~445×380 km.
- **Fuentes:** volcano.ssec.wisc.edu (portal + Coverage Map = mismo backend `get_list/json` que
  consultamos); NESDIS "Airlines, Observatories… VOLCAT"; **ATBD GOES‑R VolAsh v3.0 (2012, local
  `docs/ATBD_GOES-R_VolAsh_v3.0_July2012.pdf`)** = spec del producto gridded (altura en m, carga,
  reff, DQF); STAR GOES‑R Vol Ash product page (baseline ABI‑VAA "experimental, not 24/7 operational");
  cimss.ssec.wisc.edu/csppgeo/software.html (9 paquetes, sin VOLCAT); Pavolonis et al. 2013 (JGR,
  algoritmo); Pavolonis et al. 2018 (Earth & Space Science, alertas operacionales).
- **Referencias modernas (búsqueda jul‑2026):** Pavolonis et al. **2020**, "Remote Sensing of
  Volcanic Ash with the GOES‑R Series" (cap. en *The GOES‑R Series*, Elsevier, doi:10.1016/
  B978‑0‑12‑814327‑8.00010‑X) = la referencia actual del enfoque VOLCAT/GOES‑R (paywall Elsevier,
  bajar a mano); **Saint et al. 2024**, "Using Simulated Radiances to Understand the Limitations of
  Satellite‑Retrieved Volcanic Ash Data…" (JGR, doi:10.1029/2024JD041112, Open Access) — cuantifica la
  incertidumbre de altura/carga, respalda nuestro INDICATIVO. **Descargados a `docs/own_volcat/`:**
  Saint 2024, VADUGS (Bugliaro 2022, NN MSG/SEVIRI) y DL‑nowcasting (Sci. Rep. 2026). **Único pendiente
  de bajar a mano:** cap. Pavolonis 2020 (Elsevier, paywall cerrado — acceso institucional).
