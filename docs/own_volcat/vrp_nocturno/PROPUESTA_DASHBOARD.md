# Propuesta: dónde y cómo mostrar el indicador nocturno de calor en el cráter

Fecha: 22-11-2026. Estado: **propuesta, nada cableado ni desplegado.** La lógica está en
`src/process/vrp_nocturno.py` (con cabecera FICHA SDA) y el criterio de presentación en
`dashboard/map_helpers.estado_calor_nocturno`; los dos con tests en `tests/test_vrp_nocturno.py`.
Validación: `docs/own_volcat/vrp_nocturno/INFORME.md` (PR 87). Ficha: `docs/FICHA_SDA_GOES.md` §C.1.

## 1. Qué le sirve al turno

Una línea por volcán que diga, para la noche en curso o la última noche: "calor en el cráter sobre
~10 MW (11 de 20 cuadros visibles, máximo 33 MW)", "sin calor sobre ~10 MW, no descarta actividad
débil", "sin dato (cráter cubierto)" o "sólo de noche". Es estado, no evento: cambia de una noche a
otra, no de un cuadro a otro. Por eso no va como capa del mapa ni como alarma.

## 2. Dónde

1. **Cabecera de la grilla de volcán** (`modo_guardia_volcan._grid_header`), debajo de la señal VOLCAT
   y con el mismo formato (`volcat_senal.html_senal` como modelo: punto de color, título, detalle entre
   paréntesis y el aviso de fuente `AVISO_CALOR_NOCTURNO` en letra chica). La grilla tiene tres
   llamadores (sub-tab Volcán del Modo Guardia, tab Volcán de Vista Operacional, slot `tv=volcan` del
   Modo Sala); la propuesta es mostrarlo en los dos primeros y **no en la pared del Modo Sala** al
   principio, igual que se hizo con VOLCAT: primero lo lee quien lo puede interpretar.
2. **Resumen nacional**, opcional y después: una tabla de los volcanes que no están en `bajo_limite`
   ni `sin_dato` (hoy, sólo Chillán), con el mismo patrón de `volcat_senal.resumen_nacional`.

No se dibuja nada sobre el mapa, así que no hay glifo nuevo que agregar a `render_compact_legend`. Si
algún día se dibuja (por ejemplo un anillo alrededor del cráter encendido), ese glifo entra a
`_LEGEND_ITEMS` y a `tests/test_legend_coverage.py` en el mismo cambio.

## 3. De dónde salen los números

Calcularlo dentro del dashboard en cada rerun no sirve: el estado de una noche necesita todos sus
cuadros y la referencia de cielo despejado necesita las 7 noches previas. Propuesta, con el patrón de
`frp_timeline.yml`:

- **Workflow nuevo** cada 10 min que baje C07 y C14 sólo en las ventanas de 25 × 25 píxeles de los
  volcanes del catálogo (`vrp_nocturno.ventana`), calcule `vrp_cuadro` por volcán y agregue una fila
  por cuadro a una ventana rodante de 8 noches en `data/calor_nocturno.json` (VRP, BT14 del cráter,
  hora del scan). En la validación, los 21 sitios caen en 28 bloques de 24 filas por banda
  (estimado, sin medir, unos 14 MB por cuadro) y la descarga rindió ~1,1 s por cuadro con 10 procesos.
- **Grupo de concurrency propio** y la misma regla de `gap-fill` que `frp_timeline`: GitHub atrasa
  los cron de repos poco activos y la serie va a tener huecos. Un hueco es `sin_dato`, nunca cero.
- El dashboard sólo lee el JSON y llama a `estado_noche` y `estado_calor_nocturno`. Si el JSON está
  atrasado más de 30 min respecto del último scan, el detalle lo dice (mismo criterio que
  `alerta_edad`), porque "encendido" o "bajo el límite" de hace seis horas no describe la noche de hoy.

## 4. Reglas que no se pueden romper al cablearlo

- `bajo_limite` no es verde. Villarrica y Láscar tienen calor y quedan siempre ahí.
- `sin_dato` y `de_dia` son grises y no se cuentan como "sin anomalía" en ningún resumen.
- La edad del dato va junto al estado.
- La regla de `src/process/vrp_nocturno.py` es la validada: cambiar un umbral, la zona, el anillo o
  la prueba de visibilidad exige volver a validar con el criterio del 22-11-2026, no sólo pasar los
  tests.
- Al cablearlo, la fila pasa de §C a §A en `docs/FICHA_SDA_GOES.md` y se agrega el workflow a
  `INTEGRATION.md`.

## 5. Qué decide Nicolás

1. Si se muestra y dónde (recomendación: cabecera de la grilla de volcán, no la pared del Modo Sala).
2. Si se crea el workflow de §3 (agrega un cron cada 10 min y un JSON más al repo).
