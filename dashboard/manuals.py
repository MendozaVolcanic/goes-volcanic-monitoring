"""Manuales por vista — qué muestra y cómo interpretarlo.

Cada vista del dashboard tiene un manual breve (~150-200 palabras) que se
renderiza en un `st.expander` colapsado al INICIO de la sección. Incluye:
  - Qué muestra físicamente (radiancia, BTD, producto L2, etc.)
  - Cómo leer colores / features
  - Falsos positivos típicos (sobre todo Chile invierno: cirros, nieve)
  - Referencias bibliográficas / técnicas (link a paper o ATBD)

Filosofía: el operador de turno debería poder abrir el expander en 30s y
saber qué está mirando sin tener que conocer la receta RGB de memoria.

Para agregar/editar un manual: tocá solo este archivo. Cada vista importa
`render_manual` y lo invoca con su `view_key`.
"""

from __future__ import annotations

import streamlit as st


# ── Manuales por vista ───────────────────────────────────────────
# Estructura: view_key -> (titulo_expander, cuerpo_markdown)
# El titulo_expander aparece como "📖 Cómo interpretar — <titulo>".
# El cuerpo es markdown estandar; podes usar **bold**, listas, links.

_MANUALS: dict[str, tuple[str, str]] = {
    # ── Vista Operacional ─────────────────────────────────────────
    "operacional": (
        "Vista Operacional",
        """
**Qué muestra**: visor en vivo de los productos GOES-19 (GOES-East,
geoestacionario 75°W, cadencia ~10 min, resolución 2 km IR). Podés
elegir un volcán específico o una región amplia, y alternar entre Ash
RGB, GeoColor, SO2 RGB y otros productos satelitales.

**Cómo leerlo**:
- **Ash RGB** (receta RAMMB/CIRA): la ceniza volcánica aparece en
  tonos **rojo-magenta** (split-window BT11-BT12 negativo); SO2 en
  **verde-amarillo**; nubes meteorológicas en **azul/celeste**.
- **GeoColor**: imagen color real diurna útil para confirmar plumas
  visibles. De noche cambia a IR pseudo-color.
- **SO2 RGB** (JMA): plumas de SO2 en magenta brillante sobre fondo
  verdoso.
- **Toggle 💨 Viento GFS**: superpone vectores de viento a 300/500/850 hPa
  (Open-Meteo) para predecir dirección de pluma.

**Falsos positivos en Chile invierno** (mayo-septiembre): cirros altos
y nieve cordillerana dan señal Ash RGB roja similar a ceniza. Validá
siempre cruzando con hot spots NOAA FDCF y movimiento en loop.

**Referencias**:
- [RAMMB Ash RGB Quick Guide](https://rammb.cira.colostate.edu/training/visit/quick_guides/GOES_Ash_RGB.pdf)
- [GOES-R ABI ATBD Volcanic Ash v3.0](https://www.star.nesdis.noaa.gov/goesr/documents/ATBDs/Baseline/ATBD_GOES-R_VolAsh_v3.0_Jul2012.pdf)
- [Open-Meteo GFS wind API](https://open-meteo.com/en/docs/gfs-api)
""",
    ),

    # ── Modo Guardia ──────────────────────────────────────────────
    "guardia": (
        "Modo Guardia",
        """
**Qué muestra**: vista de monitoreo simultáneo de múltiples volcanes o
zonas, pensada para turno de sala. Sub-tabs:
- **Por Zona Volcánica** — grid de las 4 zonas (Norte, Centro, Sur,
  Austral) lado a lado, mismo producto, mismo timestamp.
- **Mosaico (8 prioritarios)** — Lascar, Villarrica, Lonquimay,
  Calbuco, Llaima, Copahue, Nevados de Chillán, Planchón-Peteroa.
- **Por Volcán** — 3 productos (Ash, GeoColor, SO2) lado a lado para
  un volcán con anillos de distancia y overlay de viento opcional.

**Cómo usarlo**:
- Comparar visualmente entre zonas o productos sin cambiar de vista.
- El **botón Modo Sala** (rojo, arriba) entra a fullscreen rotando
  productos cada 10 s — para proyectar en pared de sala 24/7.
- Hot spots NOAA FDCF (diamantes rojos) aparecen automáticamente
  cuando hay detecciones recientes.

**Tip operacional**: si Ash RGB muestra rojo en una zona, validá saltando
a "Por Volcán" sobre el volcán sospechoso — el grid de 3 productos
descarta cirros con más confianza que el composite solo.

**Referencias**:
- [NOAA FDCF (Fire/Hot Spots) product](https://www.star.nesdis.noaa.gov/goesr/product_fire_fhs.php)
- [VOLCAT operational system (SSEC)](https://volcano.ssec.wisc.edu/)
""",
    ),

    # ── Comparador ────────────────────────────────────────────────
    "comparador": (
        "Comparador",
        """
**Qué muestra**: 2 productos lado a lado para el mismo volcán y
timestamp, o **modo sustracción** RGB-RGB para resaltar diferencias.

**Cómo leerlo**:
- **Modo paralelo**: útil para comparar Ash RGB vs GeoColor (¿la
  señal roja se ve también en visible como pluma?), o Ash RGB vs SO2
  RGB (¿hay co-emisión gases + ceniza, típico de erupciones explosivas
  con magma profundo?).
- **Modo sustracción** (A − B por canal): píxeles donde los dos productos
  difieren mucho aparecen brillantes. Ayuda a aislar features que solo
  un producto detecta (ej. SO2 puro sin ceniza coincidente).

**Caso de uso clásico**: confirmar que una señal Ash RGB roja en
invierno chileno es ceniza real y no cirro — si en GeoColor visible
aparece una pluma que se mueve con el viento desde el cráter, es ceniza.
Si solo está en Ash y no en GeoColor o jma_so2, es muy probablemente
cirro o nieve.

**Nota técnica**: la sustracción se hace en espacio RGB normalizado
(0-1 por canal), no en temperatura de brillo. Para diferencias
cuantitativas en Kelvin usá la vista **Ash + BTD**.

**Referencias**:
- [EUMETSAT Volcanic Ash RGB Technical Guide](https://www-cdn.eumetsat.int/files/2020-04/pdf_rgb_quick_guide_ash.pdf)
""",
    ),

    # ── Modo Evento ───────────────────────────────────────────────
    "evento": (
        "Modo Evento",
        """
**Qué muestra**: vista **focalizada para crisis volcánica activa**.
Cuando hay erupción confirmada o alerta SERNAGEOMIN, esta pantalla
tiene TODO sobre ese volcán en una sola vista — sin navegar tabs.

**Componentes**:
- **Header grande** con nombre del volcán + countdown desde inicio
  del evento (botón "Marcar inicio" — guarda timestamp en URL).
- **Grid 3 productos**: Ash RGB, GeoColor, SO2 RGB lado a lado.
- **Tabla hot spots NOAA FDCF** dentro de 50 km, ordenados por FRP
  (Fire Radiative Power en MW) — la magnitud cuantitativa de la
  anomalía térmica.
- **Vectores de viento GFS** a 300, 500 y 850 hPa para predecir
  dirección de dispersión de pluma a distintas alturas.
- **Anillos de distancia** (5, 10, 25, 50, 100 km) desde el cráter
  para estimar largo visible de pluma en el plot.
- **Altura VOLCAT** si está disponible (SSEC RealEarth).

**Cómo compartirlo**: la URL `?vista=evento&volcan=Villarrica` es
permalink — pegala en mail/Slack y el equipo abre la misma vista
sincrónicamente.

**Filosofía**: cuando importa, importa rápido. Diseñado para que
el operador de turno tenga toda la info para llamar al jefe en <60 s.

**Referencias**:
- [NOAA FDCF — Fire Radiative Power](https://www.star.nesdis.noaa.gov/goesr/product_fire_fhs.php)
- [VOLCAT — altura cuantitativa de pluma](https://volcano.ssec.wisc.edu/)
- [Pavolonis et al. 2013 — Automated volcanic cloud detection](https://doi.org/10.1002/jgrd.50173)
""",
    ),

    # ── Heatmap actividad ─────────────────────────────────────────
    "heatmap": (
        "Pulso térmico y panorama de actividad",
        """
Esta vista tiene **dos secciones complementarias**, cada una explotando
una escala temporal distinta del producto NOAA FDCF de GOES-19.

---

**1) Pulso térmico intradía — la fortaleza ÚNICA de GOES**

**Qué muestra**: una curva de **FRP (Fire Radiative Power, en MW)** por
volcán a lo largo del tiempo, a la cadencia nativa de GOES (~10 min). Es
la *evolución temporal* de la emisión radiativa — el encendido y la
escalada de un evento efusivo.

**Por qué importa (y por qué MODIS/VIIRS no lo dan)**: GOES es
geoestacionario, ve el mismo punto cada 10 min (~144 scans/día). MODIS y
VIIRS son polares: 2-4 pasadas/día. Para *magnitud* y *sensibilidad* los
polares ganan (375 m–1 km vs ~2 km de GOES, peor en el sur de Chile por
el ángulo oblicuo). Pero para captar la *dinámica intradía* de una
erupción efusiva, GOES no tiene rival. Esta curva es ese aporte único.

**Cómo leerlo**: eje X = tiempo (UTC); eje Y = FRP sumado dentro de
50 km de cada volcán. Sólo se grafican volcanes con señal > 0; el resto
se listan como "calmos". Pre-cocinado incremental por el GitHub Action
`frp_timeline.yml` (ventana rodante de 48h).

**Limitación honesta**: FDCF rara vez dispara sobre volcanes chilenos
(0-3 hotspots en todo Chile por scan; las explosivas con ceniza fría NO
calientan el pixel). Así que este panel está en CERO la mayor parte del
tiempo y "se enciende" sólo en actividad efusiva con lava expuesta
(típico: Villarrica, Láscar, Nevados de Chillán). Eso es exactamente
cuando la cadencia de 10 min vale.

---

**2) Panorama semanal — conteo diario de hot spots**

**Qué muestra**: mapa de calor de **número de detecciones FDCF** por
volcán y por día (últimos 7). Vista de mediano plazo. Pre-procesado por
el cron `hotspots_daily.yml` (`data/hotspots_daily.json`, 02:00 UTC).

**Cómo leerlo**: eje Y = volcanes; eje X = días; color = nº de
detecciones (`mask >= 10`). Una fila consistentemente cálida durante
semanas indica actividad sostenida; picos aislados suelen ser falsos
positivos por incendios cercanos o reflejo solar especular.

**Limitación**: FDCF está optimizado para incendios; volcanes con
anomalías térmicas suaves (fumarolas < 200 K sobre fondo) pueden
no disparar el algoritmo. Para esos casos usar VRP MODIS/VIIRS.

**Referencias**:
- [NOAA FDCF ATBD](https://www.star.nesdis.noaa.gov/goesr/documents/ATBDs/Baseline/ATBD_GOES-R_FDC_v2.5_Jul2012.pdf)
- [MIROVA / VRP — térmico complementario para volcanes](https://www.mirovaweb.it/)
""",
    ),

    # ── Replay reciente ───────────────────────────────────────────
    "replay": (
        "Replay reciente",
        """
**Qué muestra**: animación pre-renderizada de las **últimas N horas**
(típicamente 2-6 h) para un volcán seleccionado. Pensado para revisión
post-evento o entrega de turno — "qué pasó mientras no estabas mirando".

**Cómo usarlo**:
- Selector de volcán → carga animación pre-cocinada del cache.
- Slider de tiempo para avanzar frame por frame.
- Botón ▶ para reproducir continuo.
- Productos disponibles: Ash RGB, GeoColor, SO2 RGB (los que el cron
  pre-renderiza cada hora).

**Diferencia con Loops descargables**:
- **Replay** = navegación interactiva frame-a-frame, sin descarga.
- **Loops descargables** = MP4/GIF generado en demanda, para guardar
  o pegar en informe.

**Nota histórica**: el caso Calbuco 2015 originalmente estaba aquí
pero RAMMB Slider no archiva GOES-13 (operacional en 2015), así que
fue reemplazado por eventos recientes con archivo GOES-19 (~28 días
hacia atrás).

**Referencias**:
- [RAMMB Slider — fuente de tiles](https://rammb-slider.cira.colostate.edu/)
""",
    ),

    # ── Backfill histórico ────────────────────────────────────────
    "backfill": (
        "Backfill histórico",
        """
**Qué muestra**: catálogo de **eventos volcánicos históricos
pre-cocinados** en formato animación + tabla de hot spots. Útil para
training, comparación con evento actual, o validación de productos
en eventos confirmados.

**Eventos disponibles** (ver tabla abajo): erupciones recientes con
archivo GOES-19 disponible (~últimos 28 días en RAMMB) más algunas
pre-procesadas y guardadas como assets permanentes en
`out_backfill/`.

**Cómo armar un nuevo backfill**:
1. Identificar evento con coordenadas + ventana temporal UTC.
2. Editar `scripts/build_backfill.py` agregando entry al diccionario
   de eventos.
3. Correr `python scripts/build_backfill.py --event=NombreEvento`.
4. El script descarga frames RAMMB, los compone, genera MP4 + JSON
   con hot spots, y guarda en `out_backfill/`.

**Limitación clave**: RAMMB Slider solo expone ~28 días de archivo
para GOES-19. Eventos más viejos requieren reprocesado desde L1b
NOAA S3 — no implementado en este dashboard (sería pipeline aparte).

**Referencias**:
- [GOES-19 archivo NOAA AWS S3](https://registry.opendata.aws/noaa-goes/)
- [RAMMB Slider archive policy](https://rammb-slider.cira.colostate.edu/)
""",
    ),

    # ── Ash + BTD ─────────────────────────────────────────────────
    "ash": (
        "Ash + BTD (temperaturas K)",
        """
**Qué muestra**: vista **cuantitativa** de detección de ceniza
volcánica usando temperaturas de brillo (BT) en Kelvin a partir de
bandas L1b GOES-19. NO es composite RGB — son números físicos.

**Productos disponibles**:
- **BT11.2 µm** (banda 14): temperatura observada de la cima de
  nube/pluma. Plumas frescas son frías (200-240 K).
- **BTD split-window** = BT(11.2) − BT(12.3). **< -1.0 K** indica
  ceniza (umbral Prata 1989). Es la métrica clásica de detección.
- **BTD tri-espectral** = (BT8.4 − BT11.2) + (BT12.3 − BT11.2).
  **< 0 K** mejora detección filtrando algunos cirros que pasan el
  filtro split-window.

**Cómo leerlo**:
- Colorbar negativa azul/violeta → ceniza probable.
- Filtro `BT11 < 200 K` aplicado para descartar superficie tibia.
- Hover muestra valor exacto en K para validar contra umbrales.

**Por qué importa la versión cuantitativa**: el Ash RGB es muy útil
para reconocer pluma de un vistazo, pero los falsos positivos en
Chile invierno (cirros 30-60 %) requieren cuantificar. Aquí ves el
**valor real** y podés decidir umbrales por evento.

**Referencias**:
- [Prata 1989 — Observations of volcanic ash clouds using AVHRR](https://doi.org/10.1080/01431168908903916)
- [GOES-R ABI ATBD Volcanic Ash v3.0](https://www.star.nesdis.noaa.gov/goesr/documents/ATBDs/Baseline/ATBD_GOES-R_VolAsh_v3.0_Jul2012.pdf)
""",
    ),

    # ── VOLCAT ────────────────────────────────────────────────────
    "volcat": (
        "VOLCAT (altura de pluma)",
        """
**Qué muestra**: producto **VOLCAT** del SSEC (University of Wisconsin)
que detecta automáticamente plumas volcánicas y estima su **altura
cuantitativa** (km sobre nivel del mar) y carga de ceniza (g/m²).

**Diferencia con Ash RGB**:
- Ash RGB = composite cualitativo (rojo = ceniza, verde = SO2, etc.).
- VOLCAT = números: **altura en km**, **carga en g/m²**, **radio
  efectivo de partícula en µm**.

**Cómo leerlo**:
- **Altura (km)**: usa diferencia entre BT observada y perfil
  atmosférico vertical (GFS) para resolver altura. Útil para alerta
  aeronáutica (FL flight levels).
- **Mass loading (g/m²)**: integral vertical de masa de ceniza por
  unidad de área. Para cuantificar emisión total combinar con área
  de pluma.
- **Effective radius (µm)**: tamaño promedio de partícula. Plumas
  jóvenes tienen partículas más grandes; con la edad sedimentan las
  grandes y queda solo lo fino.

**Limitación**: solo funciona cuando hay pluma claramente detectada
sobre fondo frío. Plumas finas o muy frías (>10 km alt) pueden ser
sub-detectadas.

**Referencias**:
- [Pavolonis et al. 2013 — Automated volcanic cloud detection (JGR)](https://doi.org/10.1002/jgrd.50173)
- [VOLCAT operational portal SSEC](https://volcano.ssec.wisc.edu/)
- [Pavolonis et al. 2018 — Volcanic ash height retrieval](https://doi.org/10.1029/2017JD027858)
""",
    ),

    # ── Loops descargables ────────────────────────────────────────
    "loops": (
        "Loops descargables",
        """
**Qué muestra**: generador on-demand de **animaciones MP4/GIF/ZIP**
para volcán + producto + ventana de tiempo elegidos. Pensado para
incluir en informes, presentaciones, o subir a redes/Twitter para
comunicar evento a público.

**Cómo usarlo**:
1. Elegí volcán y producto (Ash RGB, GeoColor, SO2 RGB).
2. Elegí ventana (últimas 2 h, 6 h, 24 h).
3. Click "Generar" → el backend descarga frames de RAMMB, los
   compone, y entrega:
   - **MP4** (h264) — compatible con todo, recomendado para informes.
   - **GIF** — para web, peso mayor.
   - **ZIP de PNGs** — frames individuales si querés post-procesar.

**Tip**: para erupciones largas (>6 h), generá varios loops de 2 h y
encadenalos en editor — un GIF/MP4 de 24 h pesa demasiado.

**Cache**: las animaciones se cachean por (volcán, producto, ventana,
hora-redondeada) — re-generar con mismos parámetros es instantáneo.

**Referencias**:
- [RAMMB Slider — fuente original GOES](https://rammb-slider.cira.colostate.edu/)
- [ffmpeg h264 encoding](https://trac.ffmpeg.org/wiki/Encode/H.264)
""",
    ),

    # ── Series de tiempo ──────────────────────────────────────────
    "series": (
        "Series de tiempo",
        """
**Qué muestra**: series temporales numéricas de métricas térmicas
sobre un volcán: número de hot spots NOAA FDCF, FRP total (Fire
Radiative Power, MW), y % de pixeles "ash-rojos" filtrados sobre la
zona del cráter.

**Cómo leerlo**:
- **N° hot spots / día**: cuenta de detecciones FDCF con
  `mask >= 10` (confianza alta + saturated). Pico claro = aumento de
  emisión térmica.
- **FRP total (MW)**: suma de potencia radiada de todos los hot
  spots del día. Métrica cuantitativa de magnitud — preferida sobre
  conteo crudo, igual que MIROVA usa VRP en VIIRS/MODIS.
- **% ash-rojo filtrado**: porcentaje de píxeles dentro del bbox del
  volcán que pasan el filtro `_ash_red_fraction_v2` (descarta cirros
  + nieve). Proxy cualitativo de pluma; **no es métrica absoluta**
  porque depende de iluminación y bbox.

**Limitaciones**:
- **% ash-rojo no es FRP**: no compares unidades. Para magnitud
  cuantitativa absoluta usá FRP o VOLCAT mass loading.
- Cirros invierno chileno (mayo-sept) pueden inflar el % ash-rojo
  sin actividad real. Validar con FRP en paralelo.

**Referencias**:
- [Coppola et al. 2013 — VRP / MIROVA approach](https://doi.org/10.1144/SP426.5)
- [NOAA FDCF — FRP product documentation](https://www.star.nesdis.noaa.gov/goesr/documents/ATBDs/Baseline/ATBD_GOES-R_FDC_v2.5_Jul2012.pdf)
""",
    ),
}


def render_manual(view_key: str) -> None:
    """Renderiza el manual de una vista como expander colapsado.

    Llamar al PRINCIPIO del `def render()` de cada vista, antes de
    cualquier toolbar/selector. Si la view_key no existe en _MANUALS,
    no renderiza nada (silent skip, evita romper la pagina).

    Args:
        view_key: slug de la vista. Ver _MANUALS keys arriba.
    """
    if view_key not in _MANUALS:
        return
    title, body = _MANUALS[view_key]
    with st.expander(f"📖 Cómo interpretar — {title}", expanded=False):
        st.markdown(body, unsafe_allow_html=False)
