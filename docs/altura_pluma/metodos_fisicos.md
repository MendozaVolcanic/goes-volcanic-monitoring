# Métodos físicos para estimar altura de pluma volcánica

Resumen de los algoritmos usados por los productos operacionales
(VOLCAT, ACHA, VAAF legacy) y cómo funcionan. Orientado a entender qué estamos
viendo en el producto `Ash_Height` de VOLCAT y a decidir cuándo confiarlo.

## 1. Brightness Temperature matching a sondeo (BT-matching)

**Idea:** la pluma opaca irradia como cuerpo negro a la temperatura del aire
donde está el tope. Si mido BT(11 µm) del tope, y tengo un perfil vertical
T(z) del numerical weather prediction (GFS/ECMWF), la altitud es el nivel
donde `T_perfil(z) = BT_observado`.

**Ventajas:**
- Conceptualmente simple. Es lo primero que un volcanólogo probaría.
- Funciona bien para plumas **frías y opacas** (erupciones explosivas con
  topes > 10 km).

**Limitaciones:**
- **Sub-estimación 1-5 km para plumas semi-transparentes** (emisividad < 1):
  parte de la radiación viene de abajo de la pluma, baja la BT aparente.
- Si hay **nube meteorológica más fría** por encima, domina la señal.
- La inversión en estratosfera (T aumenta con altura) puede dar soluciones
  ambiguas.

**Implementable con nuestro stack:**
SÍ. Ya descargamos banda 13 (10.3 µm) y perfiles GFS vía Open-Meteo.
Costo: ~2 días de trabajo para un prototipo.

## 2. Parallax (GOES-East + GOES-West)

**Idea:** la misma pluma, observada desde dos posiciones geoestacionarias
distintas, aparece en lat/lon aparentes ligeramente diferentes. Esa
disparidad es proporcional a la altura geométrica del objeto (paralaje
fotogrametríca).

Para Chile, el overlap es entre GOES-19 (East, -75.2°) y GOES-18
(West, -137.2°). El baseline angular es grande → alturas con precisión
~1 km.

**Ventajas:**
- **Geométrico puro**, independiente de temperatura.
- Funciona con plumas delgadas donde BT-matching falla.

**Limitaciones:**
- Requiere **imágenes simultáneas** de dos satélites y correlación espacial
  robusta (matching de features entre imágenes con geometría distinta).
- Solo en la zona de overlap; aire-to-air lejos del nadir el error crece.
- No es operacional en VOLCAT (es research).

**Implementable con nuestro stack:**
Parcialmente. Tenemos acceso a ambos satélites vía S3, pero el algoritmo
de correlación espacial es complejo. **Es un proyecto de investigación
de ~2-4 semanas**, no una feature de 2 días.

## 3. CO2 slicing / Split-Window

**Idea:** razones entre bandas de absorción de CO2 (13.3 µm) y ventana
(11 µm) pesan diferentes capas atmosféricas. Ajustando radiativamente se
localiza el nivel de emisión efectivo, incluso para nubes semi-transparentes.

**Ventajas:**
- Funciona donde BT-matching subestima.
- Base del algoritmo **ACHA** (Algorithm for Cloud Height Assignment) que
  alimenta al producto ABI-L2-ACHAF de NOAA.

**Limitaciones:**
- Requiere modelo radiativo (CRTM o similar) y buena estimación de emisividad.
- Sensible a errores de calibración entre bandas.

**Integrable:**
Indirectamente vía ACHA — el NetCDF `ABI-L2-ACHAF` en S3 `noaa-goes19`
ya trae la altura procesada por NOAA usando este método. Tiempo de
integración: ~1 día (descarga + reproyección, patrón que ya tenemos).

## 4. VOLCAT (la cadena integrada)

**Qué hace VOLCAT internamente** (Pavolonis et al. 2013, 2015):

1. **Detección de ceniza**: combina BTD 11-12 µm (firma de Prata), BT 8.5-11
   (firma de SO2/ash), tests de textura, y modelos gaussianos multi-banda.
2. **Retrieval de propiedades**: para cada pixel detectado como ceniza,
   resuelve simultáneamente:
   - **Altura del tope** (z)
   - **Masa columnar** (g/m²)
   - **Radio efectivo** de partícula (µm)
   - **Emisividad IR**
3. **Inversión no-lineal**: optimización contra un forward model de radiancia
   que usa microfísica de ceniza (índices de refracción de Prata o Newman),
   perfil GFS, geometría de observación.

**Por qué es mejor que BT-matching:**
Resuelve los 4 parámetros a la vez, así que **no sub-estima cuando la pluma
es semi-transparente** — la emisividad < 1 entra como parámetro libre.

**RMSE típico:** ±2 km en altura, ±50% en masa, ±30% en radio.

## 5. ¿Qué pasa si los métodos dan distinto?

Es común. Un caso práctico:

- Puyehue-Cordón Caulle 2011, columna de 12 km observada visualmente.
- BT-matching sobre 11 µm: dio ~9 km (sub-estimó por semi-transparencia).
- VOLCAT: dio 11 km (usó retrieval 4-parámetros).
- Radar meteorológico argentino: 12 km.

**Lección:** confiar VOLCAT sobre BT-matching simple. En dashboard, si
mostramos ambos, usar VOLCAT como "altura referencia" y BT-matching como
"cota inferior".

## 6. Validación vs radar / LIDAR

Los VAAC validan altura satelital contra:
- **Radares aeroportuarios** (C o S band): ven la pluma como eco hasta ~30 km.
- **LIDAR**: perfiles verticales finos, pero pocas estaciones.
- **Pilot Reports (PIREPs)**: observaciones de aviación comercial.
- **Observatorios volcanológicos**: fotografía, termografía IR terrestre.

Para Chile, SERNAGEOMIN tiene cámaras térmicas y visuales en varios volcanes
prioritarios (Villarrica, Copahue, Nevados de Chillán). **Cruzar VOLCAT con
las cámaras cuando haya evento**.

## Referencias principales

- Pavolonis, Sieglaff, Cintineo (2013). *Spectrally Enhanced Cloud Objects – a
  generalized framework for automated detection of volcanic ash and dust clouds.*
  J. Geophys. Res. Atmos. 118, 2022-2043. https://doi.org/10.1002/jgrd.50173
- Pavolonis et al. (2015). *Spectrally Enhanced Cloud Objects Part 2:
  Volcanic ash detection retrievals.* J. Geophys. Res. Atmos. 120, 7842-7870.
  https://doi.org/10.1002/2014JD022969
- Heidinger & Pavolonis (2009). *Gazing at Cirrus Clouds for 25 years through
  a Split Window. Part I: Methodology.* J. Appl. Meteor. Clim. 48, 1100-1116.
  (base de ACHA)
- Prata (1989). *Infrared radiative transfer calculations for volcanic ash
  clouds.* Geophys. Res. Lett. 16, 1293-1296.
- Sieglaff et al. (2009). *A satellite-based hail and severe thunderstorm
  climatology using GOES CO2-slicing cloud heights.* J. Appl. Meteor. Clim.
  48, 1562-1574. https://doi.org/10.1175/2008JAMC1882.1
- ATBD Cloud Top Height (ACHA), NOAA GOES-R: `../manuales_pdf/ATBD_CloudHeight_ACHA_v3.0_Jul2012.pdf`
- ATBD Volcanic Ash (VAAF, legacy GOES-16): `../manuales_pdf/ATBD_GOES-R_VolAsh_v3.0_July2012.pdf`
