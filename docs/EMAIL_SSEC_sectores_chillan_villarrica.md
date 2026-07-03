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

My name is [name] and I'm a geologist at the Southern Andes Volcano Observatory
(OVDAS), part of SERNAGEOMIN, the agency in charge of Chile's National Volcano
Surveillance Network (RNVV). We run a near real time GOES-19 monitoring dashboard
that uses your VOLCAT products every day (ash cloud height, loading, probability and
effective radius), among them your active Chilean sectors: Copahue_250_m,
Calbuco_1_km and Planchon-Peteroa_500_m. They work really well alongside our own ABI
ash retrievals, and we're grateful to have them.

I'd like to be candid about what "our own retrievals" actually are. We're a small
observatory team, and we build these pipelines as open source software, a lot of it
written with the help of AI coding assistants (large language models). We think of
the result as a modest, deliberately indicative complement to VOLCAT, not an
equivalent to it. Your group developed and refined an operational, physically
rigorous retrieval over more than a decade, and we're well aware of the distance
between that and what we do. Being able to check our numbers against VOLCAT is really
what keeps them honest. It's in that spirit, as grateful users and hopeful validators
of your work rather than peers reimplementing it, that I'm writing with two coverage
requests for Chile and one question about data access.

**1. Reactivating the existing Villarrica_250_m sector.**
Going through your sector list, we noticed that a Villarrica_250_m sector is already
defined, with valid coordinates, but it doesn't seem to be producing imagery. Its
satellite and product lists are empty, and we can't find any BT11µm or Ash_Height
frames for it. As far as we can tell, it's the only sector still dormant in South
America. Every other major Andean volcano you cover (Copahue, Reventador, Sabancaya,
Nevado del Ruiz, Ubinas, Tungurahua, Cotopaxi, Chiles, Puracé) has an active high
resolution sector. Villarrica is one of the most persistently active volcanoes in
the Andes, with a near continuous lava lake and frequent Strombolian activity, so we
wanted to ask whether it could be switched back on. What we'd value most is the VIIRS
side of it (M-band ash top height at 750 m, I-band masking at 375 m), which really
does resolve small, crater scale plumes at a native resolution the 2 km GOES-ABI
can't reach. Your validated, operational VIIRS product would give us two things: a
trusted reference to cross-check our own ash top height retrievals against (today
from GOES-ABI, and soon from a VIIRS 750 m retrieval we're developing in house), and
the mass loading, effective radius and probability fields that we don't compute
ourselves. If GOES-19 ABI could also be assigned to the sector to fill the gaps
between polar overpasses, so much the better, though we realise that on ABI the
sector stays at roughly 2 km native IR resolution.

**2. A new dedicated sector for Nevados de Chillán.**
Nevados de Chillán (−36.86, −71.38) is erupting at the moment and under active
surveillance, but it has no dedicated sector. It's only covered by the regional
Chile_Central_2_km product at 2 km/pixel. Its plumes tend to be crater scale and low
altitude (lava dome degassing, modest ash columns), so at 2 km the plume fills only a
handful of mixed pixels, close to the effective detection limit of the regional
product. A dedicated sector, like the ones you already run for comparable volcanoes,
would help here. To be clear about where the benefit actually comes from: for these
small plumes it would come from VIIRS coverage on the sector (375 m / 750 m, which
really does resolve incipient plumes), or from detection thresholds tuned for a
crater scale source, rather than from the output grid spacing on its own. We know
that an ABI-only sector stays at about 2 km native IR resolution no matter how fine
the output grid is. We'd gladly send preferred bounds and event history.

**3. Access to the gridded (NetCDF) values behind the imagery.**
As documented in the GOES-R Volcanic Ash ATBD (v3.0, 2012), in Pavolonis et al.
(2013), and in the GOES-R Series chapter "Remote Sensing of Volcanic Ash with the
GOES-R Series" (Pavolonis et al., 2020), the retrieval produces gridded per-pixel
fields: ash cloud top height (a geopotential height in metres), mass loading,
effective radius and quality flags. The public portal, though, serves these only as
PNGs with the value baked into a colour scale, so we currently recover approximate
numbers by reverse mapping the colour bar, which adds one to two kilometres of
avoidable error. For proper cross validation of our own ash top height retrieval, and
for our alert workflow, access to the underlying gridded values (NetCDF or a data
feed) would be far more reliable. Ideally we'd want the VOLCAT product fields, which
only populate inside detected volcanic clouds, rather than the baseline full disk
product, since automated detection over the complex Andean terrain tends to throw
false positives. Could you let us know whether that kind of access is available to a
national volcano observatory, for example through the operational partner feed or the
upcoming NCCF distribution as VOLCAT moves to NOAA operations, and what the process
would be? Of the three requests, this gridded data access is the one we'd put first.
As we build our own open source retrievals, a validated VOLCAT ground truth is
exactly what we need to benchmark them against, and it would help across every sector
you already run rather than just one volcano.

This work feeds directly into SERNAGEOMIN's volcanic alert decisions. Both Villarrica
and Nevados de Chillán are among Chile's highest hazard volcanoes, and both are at
elevated alert levels right now. We'd be glad to share event histories, typical plume
heights and preferred sector extents, and to coordinate on validation.

Thank you very much for considering this, and for keeping VOLCAT running. It's
genuinely valuable to us.

Best regards,
[name]
[role / e-mail / phone]
OVDAS, Observatorio Volcanológico de los Andes del Sur, SERNAGEOMIN, Chile

---

## Versión en español (mismo contenido)

Estimado Dr. Pavolonis y equipo de VOLCAT,

Mi nombre es [nombre] y soy geólogo del Observatorio Volcanológico de los Andes del
Sur (OVDAS), parte de SERNAGEOMIN, el organismo a cargo de la Red Nacional de
Vigilancia Volcánica (RNVV) de Chile. Operamos un panel de monitoreo GOES-19 en
tiempo casi real que usa sus productos VOLCAT todos los días (altura de la nube de
ceniza, carga, probabilidad y radio efectivo), entre ellos sus sectores chilenos
activos: Copahue_250_m, Calbuco_1_km y Planchon-Peteroa_500_m. Nos son de gran ayuda
junto a nuestros propios retrievals de ceniza con ABI, y estamos agradecidos de
contar con ellos.

Quisiera ser franco sobre qué son en realidad "nuestros propios retrievals". Somos un
equipo pequeño de observatorio, y construimos estos pipelines como software de código
abierto, buena parte escrito con ayuda de asistentes de código con IA (modelos de
lenguaje). Consideramos el resultado un complemento modesto y deliberadamente
indicativo de VOLCAT, no un equivalente. Su grupo desarrolló y refinó un retrieval
operacional y físicamente riguroso a lo largo de más de una década, y somos muy
conscientes de la distancia entre eso y lo que hacemos. Poder contrastar nuestros
números contra VOLCAT es justamente lo que los mantiene honestos. Es en ese espíritu,
como usuarios agradecidos y aspirantes a validadores de su trabajo, más que como
pares que lo reimplementan, que les escribo con dos pedidos de cobertura para Chile y
una consulta sobre acceso a datos.

**1. Reactivar el sector existente Villarrica_250_m.**
Revisando su lista de sectores, notamos que el sector Villarrica_250_m ya está
definido, con coordenadas válidas, pero no parece estar generando imágenes. Sus
listas de satélite y de productos están vacías, y no encontramos ningún cuadro de
BT11µm ni de Ash_Height. Hasta donde vemos, es el único sector aún dormido en
Sudamérica. Todos los demás volcanes andinos importantes que cubren (Copahue,
Reventador, Sabancaya, Nevado del Ruiz, Ubinas, Tungurahua, Cotopaxi, Chiles, Puracé)
tienen un sector de alta resolución activo. Villarrica es uno de los volcanes más
persistentemente activos de los Andes, con un lago de lava casi continuo y actividad
estromboliana frecuente, así que queríamos preguntar si se podría reactivar. Lo que
más valoraríamos es la parte VIIRS (altura de tope de ceniza con bandas M a 750 m,
enmascarado con bandas I a 375 m), que sí resuelve plumas pequeñas a escala de cráter
con una resolución nativa que los 2 km del GOES-ABI no alcanzan. Su producto VIIRS,
validado y operacional, nos daría dos cosas: una referencia confiable para contrastar
nuestros propios retrievals de altura de tope (hoy desde GOES-ABI, y pronto desde un
retrieval VIIRS 750 m que estamos desarrollando internamente), y los campos de carga,
radio efectivo y probabilidad que no calculamos. Si además se pudiera asignar GOES-19
ABI al sector para llenar los huecos entre pasadas polares, mejor aún, aunque
entendemos que en ABI el sector se mantiene en unos 2 km de resolución IR nativa.

**2. Un sector nuevo dedicado a Nevados de Chillán.**
Nevados de Chillán (-36.86, -71.38) está en erupción actualmente y bajo vigilancia
activa, pero no tiene sector dedicado. Solo lo cubre el producto regional
Chile_Central_2_km a 2 km/píxel. Sus plumas suelen ser de escala de cráter y baja
altura (desgasificación del domo, columnas de ceniza modestas), así que a 2 km la
pluma ocupa apenas unos pocos píxeles mezclados, cerca del límite efectivo de
detección del producto regional. Un sector dedicado, como los que ya operan para
volcanes comparables, ayudaría acá. Para ser claros sobre de dónde viene realmente el
beneficio: en estas plumas chicas vendría de la cobertura VIIRS del sector (375 m /
750 m, que sí resuelve plumas incipientes), o de umbrales de detección afinados para
una fuente a escala de cráter, más que del espaciado de la grilla de salida por sí
solo. Sabemos que un sector alimentado solo con ABI se mantiene en unos 2 km de
resolución IR nativa por más fina que sea la grilla. Con gusto enviaríamos los
límites preferidos y el historial de eventos.

**3. Acceso a los valores en grilla (NetCDF) detrás de las imágenes.**
Como se documenta en el ATBD de Ceniza Volcánica de GOES-R (v3.0, 2012), en Pavolonis
et al. (2013) y en el capítulo "Remote Sensing of Volcanic Ash with the GOES-R
Series" (Pavolonis et al., 2020), el retrieval produce campos en grilla por píxel:
altura de tope de ceniza (una altura geopotencial en metros), carga másica, radio
efectivo y flags de calidad. El portal público, sin embargo, sirve esto solo como PNG
con el valor incrustado en una escala de color, así que hoy recuperamos números
aproximados mapeando la barra de color al revés, lo que agrega uno a dos kilómetros
de error evitable. Para una validación cruzada seria de nuestro propio retrieval de
altura, y para nuestro flujo de alerta, el acceso a los valores en grilla subyacentes
(NetCDF o un feed de datos) sería mucho más confiable. Idealmente querríamos los
campos del producto VOLCAT, que solo se pueblan dentro de las nubes volcánicas
detectadas, en lugar del producto base de disco completo, ya que la detección
automática sobre el terreno andino complejo tiende a dar falsos positivos. ¿Podrían
indicarnos si ese tipo de acceso está disponible para un observatorio volcánico
nacional, por ejemplo a través del feed de socios operacionales o de la próxima
distribución NCCF cuando VOLCAT pase a operaciones de NOAA, y cuál sería el proceso?
De los tres pedidos, este acceso a los datos en grilla es el que pondríamos primero.
A medida que construimos nuestros propios retrievals de código abierto, un
ground-truth validado de VOLCAT es justo lo que necesitamos para compararlos, y
ayudaría en todos los sectores que ya operan, no en un solo volcán.

Este trabajo alimenta directamente las decisiones de alerta volcánica de SERNAGEOMIN.
Tanto Villarrica como Nevados de Chillán están entre los volcanes de mayor
peligrosidad de Chile, y ambos están en niveles de alerta elevados en este momento.
Con gusto compartiríamos historiales de eventos, alturas típicas de columna y
extensiones de sector preferidas, y coordinaríamos la validación.

Muchas gracias por considerar esto, y por mantener VOLCAT funcionando. Es
genuinamente valioso para nosotros.

Saludos cordiales,
[nombre]
[cargo / correo / teléfono]
OVDAS, Observatorio Volcanológico de los Andes del Sur, SERNAGEOMIN, Chile

---

### Notas para vos (no enviar)
- **Estructura:** 3 pedidos ordenados de más fácil/creíble a más grande — (1) Villarrica es un
  *switch on* de algo ya definido y es el ÚNICO dormido de Sudamérica (pedido quirúrgico, muestra
  que hicimos la tarea); (2) Chillán es un sector nuevo; (3) datos gridded como consulta. Abrir
  reconociendo que YA usamos sus sectores activos chilenos da credibilidad.
- **Transparencia IA + humildad (decisión de Nicolás, jul-2026):** el párrafo de la intro declara
  explícito que construimos los pipelines con desarrollo asistido por IA (LLMs) y que lo nuestro es
  un complemento INDICATIVO modesto, NO un par de su sistema operacional (que ellos maduraron una
  década sin esa ayuda). Doble propósito: honestidad + desarmar cualquier impresión de sobre-claim.
  Nos posiciona como usuarios/validadores agradecidos, no como pares reimplementando lo suyo — tono
  correcto para pedir un favor a un científico senior de NOAA.
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
