# Correo a VOLCAT (NOAA/CIMSS): datos en grilla, ABI en Villarrica y sector Chillán

> **Versión 2, 13-sep-2026.** Reescrita tras verificar en vivo contra la API de VOLCAT y
> SERNAGEOMIN. La versión 1 (jul-2026) está en el historial de git de este archivo.
>
> **Verificado hoy (13-sep-2026):**
> - `Villarrica_250_m` **NO está dormido**: produce VIIRS (NOAA-20 y NOAA-21, Ash_Height,
>   Ash_Loading, Ash_Reff, Ash_Probability y cuatro más; último cuadro 13-sep 06:00 UTC).
>   Lo que le falta es **GOES-19 ABI** (0 cuadros). La v1 pedía "reactivarlo" y afirmaba
>   "listas de satélite y productos vacías": era falso y habría restado credibilidad.
>   Causa del error de julio: la consulta `get_list/json/sector:X` sin los demás campos
>   devuelve `sat:[]` también para Copahue, que está activo.
> - `Copahue_250_m`, `Calbuco_1_km`, `Planchon-Peteroa_500_m`: ABI al día (11:10 UTC).
> - Nevados de Chillán: **sigue sin sector** dedicado (búsqueda en los 346 nombres del listado).
> - Alertas SERNAGEOMIN: **Villarrica amarilla desde el 4-sep-2026** (ascenso del lago de
>   lava, explosiones menores, balísticos, aumento de temperatura satelital);
>   **Nevados de Chillán amarilla desde el 15-jun-2026** (explosiones menores, columnas
>   iniciales bajo 200 m sobre el centro de emisión).
> - Transición de VOLCAT a operaciones NOAA en NCCF: anunciada por NESDIS/STAR (feb-2026).
> - Pavolonis es el POC para *sector coverage requests* (NESDIS). **La ficha SSEC de Justin
>   Sieglaff no publica correo** (solo formulario), por eso ya no va en copia.

**Para:** Michael Pavolonis, mike.pavolonis@noaa.gov
**Asunto:** VOLCAT and Chile: gridded data access, GOES-19 for Villarrica_250_m, and a Nevados de Chillán sector

---

Dear Dr. Pavolonis,

My name is Nicolás Mendoza, and I am a geologist at the Southern Andes Volcano
Observatory (OVDAS) of SERNAGEOMIN, the agency responsible for Chile's National Volcano
Surveillance Network. Our GOES-19 near real time dashboard uses VOLCAT every day,
including your Copahue_250_m, Calbuco_1_km and Planchon-Peteroa_500_m sectors, and more
recently the VIIRS imagery on Villarrica_250_m. Thank you for all of it.

I am writing with one question about data access and two coverage requests, listed in
order of how much they would help us.

**1. Access to the gridded values.** The public portal serves ash height, loading,
effective radius and probability as PNG images. We currently recover heights by reverse
mapping the colour bar, which adds roughly 1 to 2 km of error that has nothing to do with
the retrieval itself. Is access to the underlying gridded fields (NetCDF or a data feed)
available to a national volcano observatory, for example through the operational partner
feed or the NCCF distribution as VOLCAT transitions to NOAA operations? We are interested
in the VOLCAT volcanic cloud fields rather than the baseline full disk product, which tends
to over-detect over Andean terrain. This would improve every sector we already use, not
just one volcano.

**2. GOES-19 ABI on Villarrica_250_m.** The sector now produces VIIRS imagery from NOAA-20
and NOAA-21, but no ABI frames. SERNAGEOMIN raised Villarrica to Yellow technical alert on
4 September 2026, as the lava lake rose toward shallower levels, with minor crater
explosions, ballistic ejecta and increased satellite-detected temperatures. At this stage
the 10 minute ABI cadence matters more to us than spatial resolution, because it covers
the hours between polar overpasses. We understand that on ABI the sector stays at about
2 km native IR resolution, whatever the output grid.

**3. A dedicated sector for Nevados de Chillán (36.86°S, 71.38°W).** The volcano has been
at Yellow alert since 15 June 2026, with minor explosions producing low ash and gas columns.
Today it is covered only by Chile_Central_2_km, where plumes this small fill a few mixed
pixels. The benefit would come mainly from VIIRS coverage and, if feasible, detection tuned
for a crater scale source, rather than from a finer ABI grid. We can send preferred bounds
and an event history.

A word on our own work, so there is no ambiguity. We are a small team building open source
ash height retrievals from ABI, plus a VIIRS prototype not yet validated, with much of the
code written with AI coding assistants. We label all of it as indicative. It complements
VOLCAT rather than replacing it, and VOLCAT is the reference we validate against.

We would be glad to share event histories, observed plume heights and preferred sector
bounds, and to help with validation over Chile. Thank you for considering these requests.

Best regards,

Nicolás Mendoza
[cargo], Observatorio Volcanológico de los Andes del Sur (OVDAS)
Servicio Nacional de Geología y Minería (SERNAGEOMIN), Chile
[correo institucional] · [teléfono]

---

## Versión en español (para referencia interna, mismo contenido)

Estimado Dr. Pavolonis:

Mi nombre es Nicolás Mendoza y soy geólogo del Observatorio Volcanológico de los Andes del
Sur (OVDAS) de SERNAGEOMIN, el organismo a cargo de la Red Nacional de Vigilancia Volcánica
de Chile. Nuestro panel GOES-19 en tiempo casi real usa VOLCAT todos los días, incluidos sus
sectores Copahue_250_m, Calbuco_1_km y Planchon-Peteroa_500_m, y desde hace poco las
imágenes VIIRS de Villarrica_250_m. Muchas gracias por todo ello.

Le escribo con una consulta sobre acceso a datos y dos solicitudes de cobertura, ordenadas
según cuánto nos ayudarían.

**1. Acceso a los valores en grilla.** El portal público entrega altura de ceniza, carga,
radio efectivo y probabilidad como imágenes PNG. Hoy recuperamos las alturas leyendo la
barra de color al revés, lo que agrega entre 1 y 2 km de error que no tiene nada que ver con
el retrieval. ¿Está disponible el acceso a los campos en grilla (NetCDF o un feed de datos)
para un observatorio volcanológico nacional, por ejemplo mediante el feed de socios
operacionales o la distribución NCCF, ahora que VOLCAT pasa a operaciones de NOAA? Nos
interesan los campos de nubes volcánicas de VOLCAT y no el producto base de disco completo,
que tiende a sobredetectar sobre el terreno andino. Esto mejoraría todos los sectores que ya
usamos, no un solo volcán.

**2. GOES-19 ABI en Villarrica_250_m.** El sector ya genera imágenes VIIRS de NOAA-20 y
NOAA-21, pero ningún cuadro ABI. SERNAGEOMIN elevó al Villarrica a Alerta Técnica Amarilla
el 4 de septiembre de 2026, por el ascenso del lago de lava hacia niveles más someros, con
explosiones menores en el cráter, emisión de balísticos y aumento de temperatura detectado
por satélite. En esta etapa nos importa más la cadencia de 10 minutos de ABI que la
resolución espacial, porque cubre las horas entre pasadas polares. Entendemos que en ABI el
sector se mantiene en unos 2 km de resolución IR nativa, cualquiera sea la grilla de salida.

**3. Un sector dedicado a Nevados de Chillán (36,86°S, 71,38°W).** El volcán está en Alerta
Amarilla desde el 15 de junio de 2026, con explosiones menores que generan columnas bajas de
ceniza y gases. Hoy solo lo cubre Chile_Central_2_km, donde plumas tan pequeñas ocupan unos
pocos píxeles mezclados. El beneficio vendría sobre todo de la cobertura VIIRS y, si es
factible, de una detección ajustada a una fuente del tamaño de un cráter, más que de una
grilla ABI más fina. Podemos enviar los límites preferidos y un historial de eventos.

Una aclaración sobre nuestro propio trabajo, para evitar ambigüedades. Somos un equipo
pequeño que construye retrievals de altura de ceniza de código abierto a partir de ABI,
además de un prototipo VIIRS aún no validado, con buena parte del código escrito con
asistentes de programación con IA. Todo lo etiquetamos como indicativo. Complementa a VOLCAT,
no lo reemplaza, y VOLCAT es la referencia contra la que validamos.

Con gusto compartiremos historiales de eventos, alturas de columna observadas y límites de
sector preferidos, y colaboraremos en la validación sobre Chile. Muchas gracias por
considerar estas solicitudes.

Saludos cordiales,

Nicolás Mendoza
[cargo], Observatorio Volcanológico de los Andes del Sur (OVDAS)
Servicio Nacional de Geología y Minería (SERNAGEOMIN), Chile
[correo institucional] · [teléfono]

---

## Notas para Nicolás (no enviar)

**Qué cambió respecto de la v1 y por qué**

- **Pedido de Villarrica corregido.** La v1 pedía reactivar un sector "dormido" y ofrecía la
  parte VIIRS como lo más valioso. Hoy el sector ya tiene VIIRS; lo único que falta es ABI.
  Un correo que afirma algo que el destinatario puede refutar con un clic pierde la
  credibilidad que necesitan los otros dos pedidos.
- **Orden por valor, no por retórica.** El dato en grilla va primero porque es el que más
  mueve la aguja (quita el error del reverse-mapping en todos los sectores y en todo
  momento). La v1 lo dejaba al final y después decía que era el primero, lo que confunde.
- **La coyuntura como argumento.** Las dos alertas amarillas, con fecha y fuente oficial,
  justifican el pedido mejor que "uno de los volcanes más activos de los Andes".
- **Chillán: "erupting" era exagerado.** La alerta amarilla con explosiones menores no se
  describe como erupción en curso ante un especialista. Quedó "minor explosions producing
  low ash and gas columns".
- **Largo: de ~1.000 a ~530 palabras** en inglés. El párrafo de transparencia sobre IA se
  mantiene (decisión tuya de jul-2026), pero en tres frases y al final, para que el correo
  abra con los pedidos.
- **El retrieval VIIRS propio se nombra como prototipo no validado.** Existe en la rama
  `feat/viirs-ash-height` (Fases 1 y 2, jul-2026), **no está en `main`** ni validado en vivo.
  La v1 decía "soon", que prometía más de lo que hay.
- **Sin Cc a Sieglaff.** Su ficha SSEC no publica correo; poner una dirección adivinada es
  peor que no ponerla.

**Antes de enviar**

1. Completar cargo, correo institucional y teléfono.
2. Si hay datos recientes de Chillán (alturas de columna de las últimas semanas), agregar
   una frase con el valor: un número concreto pesa más que "low columns".
3. Re-verificar la cobertura justo antes (tarda segundos):
   `python -c "from src.fetch.volcat_api import _query_frames as q; print(len(q('Villarrica_250_m','ABI','Ash_Height','GOES-19')[0]), len(q('Villarrica_250_m','VIIRS','Ash_Height','NOAA-20')[0]))"`
   Si el primer número pasa de 0, ya asignaron ABI: quitar el punto 2.
4. Comprobar que no queden guiones largos ni medios en el texto final (el conteo debe dar 0).

**Fuentes verificadas el 13-sep-2026**

- API VOLCAT: `volcano.ssec.wisc.edu/imagery/get_list/json/` (formato completo de consulta,
  el mismo de `src/fetch/volcat_api.py::_query_frames`).
- SERNAGEOMIN, alertas vigentes: sernageomin.cl/alertas-volcanicas/ y los comunicados de
  elevación de alerta de Villarrica (4-sep-2026) y Nevados de Chillán (15-jun-2026).
- NESDIS, "Airlines, Observatories, and Others Keep Tabs on Volcanic Activity with VOLCAT"
  (POC para cobertura) y STAR JPSS (transición a NCCF, feb-2026).
- Dato en grilla documentado: ATBD GOES-R VolAsh v3.0 (2012, local en `docs/`), Pavolonis
  et al. 2013 y cap. Pavolonis et al. 2020.
