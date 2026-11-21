# Plan del 21-11-2026: ver con ABI las plumas chicas de Chillán, ahora con las tablas reales de VOLCAT

> Plan de investigación, no de código de la app. Cada camino se ejecuta con su criterio escrito y subido antes del
> primer número, control pareado por BT11 y umbrales leídos en la fuente original. Nada pasa al dashboard sin
> criterio cumplido, decisión de Nicolás y ficha SDA en el mismo commit.

**Objetivo:** ver con GOES-19 ABI las plumas chicas de gas y ceniza de Nevados de Chillán (oct-nov 2026) que VOLCAT
publica, y después mejorarlo.

**Qué cambió el 20-11 en la noche.** Hasta ayer la conclusión era que lo que decide VOLCAT "no es público". La
búsqueda del 20-11 encontró en el servidor abierto de SSEC (`https://bin.ssec.wisc.edu/pub/volcat/`):

1. **Las tablas de probabilidad que VOLCAT usa con ABI** (`GOESR_ASH_pixel_probability_LUT_Jan11_2017_142740.hdf`,
   12,9 MB, y `GOESR_ASH_object_probability_LUT_Jan11_2017_142742.hdf`, 74,8 MB) y el archivo de configuración que
   las nombra (`volcat_ash_detection_GOESR.config`). Traen las dos densidades por clase, ceniza y nube, por
   superficie (tierra, agua, nieve) y régimen (día, noche, sólo IR), entrenadas con MODIS. La tesis de 2014 sólo
   mostraba razones a la década y para un bin de εtot; esto es la tabla entera. SHA-512 verificado contra el
   `checksums` del paquete. Copia en `D:\goes_notas\busqueda_2026-11-20\volcat_static_anc\volcat-ancillary\`.
2. **La configuración dice cómo decide con ABI:** sin historia temporal (`0 !history flag`), sin 8,5 µm en la
   probabilidad de píxel cuando no hay datos temporales, **sesgo local del cielo despejado con una ventana de 12
   píxeles** (`1 !use local clear bias analysis`, `12 !clear bias dpix window`) y contraste del Ash RGB a 10 px.
   El sesgo local es lo más parecido a una corrección de terreno que hemos visto, y es empírica, no por cota.
3. **Archivos de evento GOES-19 de Chillán** (`events/Buenos Aires/357070/`, retención ~7 días) en la grilla ABI
   nativa: BT de 3,9 a 12 µm, huella exacta (`event_idx`), indicador de firma espectral por píxel, edad del píxel
   en el objeto, calor y rayos. Los 60 que había (13, 14 y 18-11) se bajaron con el sí de Nicolás a
   `D:\goes_notas\busqueda_2026-11-20\volcat_eventos_357070\` (LEEME con la condición de uso).
4. En el único cuadro medido (14-11 23:00 UTC, objeto ya desprendido del cráter) VOLCAT mismo da **firma espectral
   ~0** en los 67 píxeles publicados, y en la muestra VIIRS de NCCF los píxeles "rellenados" del objeto también
   tienen firma ~0. Indicio de que parte de lo publicado entra por pertenencia al objeto y seguimiento, no por
   firma.

**Lo que no está:** la base de volcanes de alertas (`Volcat_Alert_Volcano_Database_Oct8_2021_145852.txt`), los
bordes de los bins de las dos primeras dimensiones de cada tabla (por buscar en atributos de cada SDS) y la
definición de `NRAT`.

**Lo que se perdió y hay que reponer:** la carpeta `dl/` del modelo radiativo de H3 (continuo MT_CKD 4.3 y SRF de
ABI) se borró con el scratchpad de H3 el 20-11. Hoy el modelo radiativo propio no corre.

---

## Caminos, en el orden propuesto

### C1. Anatomía de los 60 eventos VOLCAT de Chillán (barato, datos ya en D:)

- **Pregunta:** ¿con qué firma arranca VOLCAT un objeto en Chillán? En cada evento, los píxeles con
  `feature_age` = 0 (primera detección) y los del cráter (≤ 10 km): ¿tienen `ash_spectral_signature_strength` alto
  o ~0? ¿Cuántos píxeles publicados tienen firma ~0 y dónde están (borde, interior, lejos del cráter)?
- **Además:** georreferencia de nuestras huellas decodificadas del PNG contra `event_idx` en los cuadros que
  coinciden (13, 14 y 18-11): desplazamiento en filas y columnas, coincidencia de píxeles.
- **Costo:** medio día, sin descarga.
- **Éxito (informativo, no decide un detector):** una tabla por cuadro con firma en el arranque y en el resto, y el
  desfase PNG contra NetCDF.
- **Qué cambia según el resultado:** si el arranque tiene firma > 0 y el resto ~0, VOLCAT detecta un núcleo con
  señal y arrastra el resto por pertenencia: nuestro blanco es el núcleo, no la huella entera, y todas las pruebas
  anteriores (que promediaron la huella) quedan sesgadas hacia abajo. Si el arranque también tiene firma ~0, la
  decisión de VOLCAT en Chillán no es espectral por píxel.
- **Límite:** sólo 3 jornadas (13, 14 y 18-11) y retención de 7 días; los episodios de octubre no tienen archivo.

### C2. Reponer el modelo radiativo (prerrequisito de C3)

- Bajar de nuevo MT_CKD 4.3 (AER, público) y las SRF de ABI GOES-19 (NOAA/STAR, públicas) a `D:\goes_cache\rt\`,
  anunciando nombre, fuente y tamaño. Comprobar que el modelo reproduce, en 5 escenas de H3, la BT despejada
  guardada en la caché rescatada (error p95 ≤ 0,3 K en C14, la vara de la etapa 2).
- Fijar las rutas por variable de entorno (como ya hizo H12 con `H11_H3`, `H11_B73`) y escribir en
  `docs/own_volcat/README.md` qué insumo vive dónde.
- **Costo:** 2 a 3 h.

### C3. H14 con las tablas reales: probabilidad de píxel y de objeto de VOLCAT sobre la huella de Chillán

- **Pregunta:** con las LUT y la configuración reales de VOLCAT para ABI, y nuestro cielo despejado corregido por
  el sesgo local de 12 píxeles, ¿la huella de Chillán llega a la probabilidad que exige SECO y el mismo lugar sin
  pluma no? Es la etapa 2 con lo único que le faltaba: las tablas.
- **Pasos:** (a) leer la estructura de la LUT (bordes de bins, orden de ejes, cómo se combinan los clasificadores
  activados en la config) y documentarla; (b) validar la lectura con un caso que no sea Chillán: un evento con
  ceniza clara (de los 7 VAAC hay carpetas activas) donde la probabilidad debe salir alta; (c) recién entonces el
  criterio de Chillán.
- **Datos:** los 66 pares de H11 (decide) y las 795 escenas de la etapa 2 (réplica), más los 60 eventos de C1
  como verdad exacta de la huella.
- **Éxito (a fijar en el criterio, propuesta):** mediana de probabilidad de píxel en la huella ≥ 0,5 con AUC
  contra el control ≥ 0,70; y, a nivel de escena, objeto con probabilidad ≥ 0,8 en ≥ 50 % de los cuadros VOLCAT con
  ≤ 2 % de falsas alarmas (la vara del 17-11).
- **Qué la falsa:** con las tablas reales la huella queda en el mismo rango que el control (AUC < 0,60). Entonces
  la diferencia con VOLCAT no está en las tablas sino en el cielo despejado que les entra (NWP, RTM o el sesgo
  local) o en la pertenencia al objeto y el seguimiento (C1).
- **Costo:** 2 a 3 días (lectura de la LUT 1 día, validación medio día, prueba 1 día).
- **Ojo:** el sesgo local de 12 px es pariente de la "anomalía de fondo" falsada el 17-11 y del anillo
  secundario de H3. No se prueba solo: entra como corrección del cielo despejado antes de las tablas, que es como
  lo usa VOLCAT.

### C4. Correo a Pavolonis, versión 5 (en paralelo)

- Reescribir el v4 (`C:\Users\nmend\AppData\Local\Claude-Data\claude_pzs8sxrjxfjjc\side-session-notes\local_1055cba6-2c2f-4aa4-9119-82691ee2ed22\Correo_VOLCAT_Pavolonis_v4.docx`):
  ya no hay que pedir las tablas. Preguntas nuevas: (1) autorización para usar los archivos de evento bajados y
  las LUT del `static_ancillary` en investigación interna, con cita; (2) si la LUT GOESR Jan11_2017 es la vigente
  en el VOLCAT operativo de GOES-19 (los eventos dicen v3r4); (3) definición de `NRAT` y bordes de bins; (4) cómo
  calcula el sesgo local de 12 px; (5) la base de volcanes de alertas para Chillán; se mantiene la pregunta de
  terreno.
- **Costo:** 1 a 2 h de redacción. Lo envía Nicolás.

### C5. Archivo diario de eventos VOLCAT de Chillán (sólo si Pavolonis autoriza)

- Con 7 días de retención, cada evento nuevo se pierde si nadie lo baja. Un script que liste
  `events/Buenos Aires/357070/` una vez al día y baje lo nuevo a D:. **No se activa** hasta tener autorización,
  porque el archivo declara acceso restringido.
- **Costo:** 1 h.

### C6. Capa térmica propia a 3,9 µm en el dashboard (después)

- H9 la falsó como gatillo del momento, pero la configuración de VOLCAT usa calor (`NRAT_HOT_SPOT_MIN = 2`,
  `BTD3911_HOT_SPOT_MIN = 15`). Como capa de contexto (volcán activo sí o no), no como detector. Requiere
  criterio, ficha SDA y decisión de Nicolás. **Se deja para después de C3.**

### Lo que queda fuera o se cierra

- **Digitalizar las Fig. 4.13 y 4.14 de la tesis:** innecesario, están las tablas reales.
- **Corrección de terreno del cielo despejado por cota (GFS a la altura real):** VOLCAT no la hace; usa el sesgo
  local. Se retoma sólo si C3 muestra que el sesgo local no basta, o si la búsqueda (tema 3, aún en curso) trae un
  método probado.
- **Auditoría multiagente de `docs/own_volcat/`:** no se justifica completa. Sí conviene un inventario de
  reproducibilidad acotado (cada resultado, qué insumos usa y si existen hoy), porque el 20-11 se perdieron
  scratchpads y el modelo radiativo dejó de correr. Propuesta: tarea de una sesión, sin agentes auditores,
  alcance a acordar con Nicolás.

### Pendiente de la búsqueda

Tres agentes de la sesión de búsqueda (publicaciones VOLCAT 2023 a 2026, corrección de terreno, plumas débiles en
GEO) no habían terminado al escribir esto. Su informe final queda en
`C:\Users\nmend\AppData\Local\Claude-Data\claude_pzs8sxrjxfjjc\side-session-notes\local_a7c21f45-ef62-4270-9e3a-c053b95c331e\BUSQUEDA_2026-11-20.md`
y este plan se actualiza si cambia el orden.

## Orden y paralelismo

1. C1 y C2 a la vez (sesiones separadas: C1 lee los eventos, C2 repone el modelo radiativo). C4 en paralelo, lo
   redacta la sesión coordinadora.
2. C3 cuando C2 pase su validación, con lo que C1 diga sobre núcleo contra huella entera.
3. C5 y C6 según la respuesta de Pavolonis y el resultado de C3.
