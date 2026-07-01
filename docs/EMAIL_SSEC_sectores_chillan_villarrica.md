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
frequent Strombolian activity), **could this sector be reactivated?** It looks like
it may only need to be switched on for GOES‑19.

**2 — A new dedicated sector for Nevados de Chillán.**
Nevados de Chillán (−36.86, −71.38) is currently in eruption and under active
surveillance, but it has **no dedicated sector** — it is only covered by the
regional `Chile_Central_2_km` (2 km/pixel). Its plumes are typically crater‑scale
and low‑altitude (lava‑dome degassing, modest ash columns), so at 2 km the plume
occupies only a few mixed pixels, near the effective detection scale of the regional
product. A dedicated **250 m (or 500 m)** sector — like those you already produce for
comparable volcanoes — would let us resolve the incipient, low‑altitude plumes we
currently miss. We would gladly provide preferred bounds and event history.

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
**gridded values (NetCDF / data feed)** would be far more reliable. Could you tell us
whether such access is available to a national volcano observatory — for example
through the operational‑partner feed, or the forthcoming NCCF distribution as VOLCAT
transitions to NOAA operations — and what the process would be?

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
