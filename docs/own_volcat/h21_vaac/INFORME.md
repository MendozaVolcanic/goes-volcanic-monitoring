# H21: avisos del VAAC Buenos Aires contra las 30 marcas de ceniza de VOLCAT en Nevados de Chillán

Fecha: 22-11-2026. Criterio escrito y commiteado antes de leer ningún aviso del periodo (commit `80aed90`):
`C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\Goes\docs\own_volcat\h21_vaac\criterio_2026-11-22.md`.
Script: `scripts\h21_cruce.py`. Todo número de este informe sale de `resultados\analisis.log`,
`resultados\marcas.csv`, `resultados\control.csv`, `resultados\avisos.csv` y `resultados\resumen.json`
(misma carpeta). Textos de los avisos: `resultados\avisos_texto.txt`.

## 1. Respuesta corta

**Veredicto: NO COINCIDE.** En 3 de las 30 marcas de VOLCAT el VAAC Buenos Aires tenía, a una hora o menos, un
aviso que decía que la ceniza de Chillán se veía en el satélite (6 de 30 si se suman los "WEAK", que el criterio
cuenta como POSIBLE). El criterio pedía 10. En 23 de las 30 marcas el VAAC no emitió ningún aviso a esa hora, y
en 1 dijo que la ceniza no se identificaba en el satélite.

**Ninguna de las 3 coincidencias es verdad independiente.** Los tres avisos citan sólo satélite (GOES-Este) y el
modelo GFS para el viento. Ningún RMK de esos avisos describe una observación de cámara, de piloto o de OVDAS.

**Qué se ve, como fenómeno:**
1. El VAAC sí recibe y usa VOLCAT: 15 de los 35 avisos leídos (18-10 a 14-11) lo nombran en `INFO SOURCE`. Aun así, a la hora
   de 23 de las 30 marcas no emitió nada. El analista tenía la alerta de VOLCAT a mano y no la convirtió en aviso.
   Eso no prueba que no hubiera ceniza (SIN AVISO no es NO), pero dice que un humano mirando GOES-19 con esa alerta
   no vio, en la mayoría de los casos, algo que valiera un aviso para la aviación.
2. Cuando el VAAC sí vio ceniza en satélite, la describe casi siempre como débil: "LIGHT VA CLD", "A FAINT VA
   PLUME", "WEAK EMISSIONS", "SPORADIC AND FAINT VA PULSES". Es el mismo régimen que nos impide reproducir a VOLCAT:
   pluma tenue, de cumbre, que se disipa cerca del cráter.
3. Las fuentes en tierra dicen algo distinto del satélite. En noviembre los avisos repiten la misma fórmula:
   OVDAS, un piloto o la cámara reportan emisión o ceniza, y el VAAC escribe que en la imagen satelital no hay
   indicación de ceniza (05-11, 07-11, 10-11 22:30, 13-11 14:30, 13-11 20:30, 14-11 11:00, 14-11 23:00).

**Contra el control** (misma hora del día en los 19 días sin marca, 570 horas): 0 horas con aviso SI a ±1 h,
9 con NO y 1 con POSIBLE. Las marcas tienen más avisos SI que el control (sorteo pareado, p < 0,0001; con la tasa
de control medida bastaba 1 SI para p < 0,05). La diferencia es real pero chica en número absoluto, y en parte
se explica por selección: los días con marca de VOLCAT son los días de actividad, y en esos días el VAAC emite
más. Lo que decide el veredicto es el número absoluto (3 de 30), no la p.

## 2. Advertencia de independencia

El VAAC Buenos Aires recibe las alertas de VOLCAT y sus analistas miran el mismo GOES-19 de 2 km. Un aviso que
coincide con una marca puede ser la misma alerta reenviada, o la lectura humana del mismo píxel. Por eso, según
el criterio, sólo cuenta como verdad independiente un aviso que cita otra fuente (cámara, piloto, OVDAS o
SERNAGEOMIN, REAV, SEGEMAR u OAVV). En los tres avisos SI que coinciden con marcas no hay ninguna en el RMK. Uno
(2026/028) trae `SVO` en `INFO SOURCE`, pero su RMK sólo habla del satélite.

## 3. Tabla marca por marca

`Δt` = hora del aviso (`OBS VA DTG`) menos hora de la marca, en minutos. Clase a ±1 h: SI, POSIBLE, NO o SIN AVISO
(el aviso más cercano queda a más de 60 min). Fuentes: las que nombran `INFO SOURCE` y `RMK` del aviso que coincide.

| # | Marca VOLCAT (UTC) | Aviso más cercano | Hora obs. aviso | Δt (min) | Clase a ±1 h | Fuentes que cita | Independiente | Lo que dice el aviso |
|---|---|---|---|---|---|---|---|---|
| 1 | 24-10 17:38 | 2026/028 | 25-10 14:40 | +1.261 | SIN AVISO | | | |
| 2 | 24-10 18:12 | 2026/028 | 25-10 14:40 | +1.227 | SIN AVISO | | | |
| 3 | 25-10 04:36 | 2026/028 | 25-10 14:40 | +603 | SIN AVISO | | | |
| 4 | 25-10 05:33 | 2026/028 | 25-10 14:40 | +547 | SIN AVISO | | | |
| 5 | 25-10 14:38 | 2026/028 | 25-10 14:40 | +1 | **SI** | SAT, SVO (sólo en INFO SOURCE), GFS | no (sí por lista) | LIGHT VA CLD OBS IN SATELLITE IMAGES |
| 6 | 25-10 18:37 | 2026/029 | 25-10 20:40 | +122 | SIN AVISO | | | (a ±3 h: SI) |
| 7 | 27-10 05:38 | 2026/033 | 27-10 06:10 | +31 | **SI** | SAT, GFS | no | VA EMISSION DETECTED IN SATELLITE DATA |
| 8 | 27-10 11:08 | 2026/034 | 27-10 12:10 | +61 | SIN AVISO | | | (a ±3 h: SI; ver §5) |
| 9 | 27-10 18:37 | 2026/035 | 27-10 18:10 | −27 | **SI** | SAT, GFS | no | A FAINT VA PLUME ... CAN BE SEEN IN STLT IMAGERY |
| 10 | 28-10 12:48 | 2026/038 | 28-10 12:00 | −49 | POSIBLE | SAT, GFS | no | WEAK AND CONTINUOUS EMISSIONS OF STEAM AND LIG VA |
| 11 | 28-10 18:18 | 2026/039 | 28-10 18:00 | −18 | POSIBLE | SAT, SVO (sólo en INFO SOURCE), GFS | no (sí por lista) | WEAK AND CONTINUOUS EMISSIONS OF STEAM AND LIG VA |
| 12 | 28-10 18:38 | 2026/039 | 28-10 18:00 | −39 | POSIBLE | SAT, SVO (sólo en INFO SOURCE), GFS | no (sí por lista) | ídem |
| 13 | 29-10 19:39 | 2026/043 | 29-10 18:20 | −80 | SIN AVISO | | | (a ±3 h: SI) |
| 14 | 29-10 19:58 | 2026/043 | 29-10 18:20 | −99 | SIN AVISO | | | (a ±3 h: SI) |
| 15 | 30-10 06:23 | 2026/044 | 30-10 00:30 | −353 | SIN AVISO | | | |
| 16 | 06-11 21:58 | 2026/046 | 07-11 13:30 | +931 | SIN AVISO | | | |
| 17 | 07-11 12:18 | 2026/046 | 07-11 13:30 | +71 | SIN AVISO | | | (a ±3 h: NO, "ARS/SIGMET report VA, no indication in satellite") |
| 18 | 07-11 18:18 | 2026/046 | 07-11 13:30 | −289 | SIN AVISO | | | |
| 19 | 08-11 12:08 | 2026/047 | 08-11 13:40 | +91 | SIN AVISO | | | (a ±3 h: SI; altura por reporte de piloto) |
| 20 | 08-11 17:34 | 2026/048 | 08-11 19:30 | +116 | SIN AVISO | | | (a ±3 h: SI) |
| 21 | 10-11 15:08 | 2026/050 | 10-11 22:30 | +441 | SIN AVISO | | | |
| 22 | 10-11 17:53 | 2026/050 | 10-11 22:30 | +276 | SIN AVISO | | | |
| 23 | 10-11 18:37 | 2026/050 | 10-11 22:30 | +232 | SIN AVISO | | | |
| 24 | 10-11 21:38 | 2026/050 | 10-11 22:30 | +51 | **NO** | SVO, SAT | **sí** | SVO REPORT MINOR ERUPTION AT 2151Z TL FL190. VA NOT DETECTED IN SATELLITE IMAGERY |
| 25 | 12-11 02:18 | 2026/052 | 11-11 06:20 | −1.199 | SIN AVISO | | | |
| 26 | 12-11 18:56 | 2026/053 | 13-11 14:30 | +1.173 | SIN AVISO | | | |
| 27 | 13-11 06:17 | 2026/053 | 13-11 14:30 | +492 | SIN AVISO | | | |
| 28 | 13-11 19:21 | 2026/054 | 13-11 20:30 | +69 | SIN AVISO | | | (a ±3 h: NO; cámara OVDAS "PSBL LGT ASH", no en satélite) |
| 29 | 14-11 12:48 | 2026/055 | 14-11 11:00 | −109 | SIN AVISO | | | (a ±3 h: NO; cámaras "PSBL LGT ASH", satélite no lo revela) |
| 30 | 18-11 10:18 | 2026/057 | 14-11 23:00 | −4.999 | SIN AVISO | | | (15 al 22-11 el VAAC sólo emitió un mensaje de PRUEBA) |

Resumen a ±1 h: SI 3, POSIBLE 3, NO 1, SIN AVISO 23. A ±3 h (sólo descriptivo): SI 9, POSIBLE 3, NO 4,
SIN AVISO 14. Con un aviso de Chillán emitido en las 6 h previas a la marca: 13 de 30.

## 4. Las dos preguntas del instrumento, contestadas con los datos

1. **Si lo que se mide estuviera roto, ¿la prueba fallaría?** Sólo en parte, como anticipó el criterio. Si VOLCAT
   marcara al azar y el VAAC fuera independiente, las marcas tendrían avisos SI a la tasa del control (0 de 570
   horas) y el resultado sería el mismo veredicto. Si el VAAC copiara a VOLCAT, la coincidencia sería alta aunque
   VOLCAT se equivocara. Que la coincidencia sea baja (3 de 30) aunque el VAAC recibe VOLCAT dice que el VAAC no
   copia sus alertas: las filtra con su propia lectura de la imagen.
2. **Si el instrumento estuviera muerto, ¿se vería distinto?** Sí, y se comprobó:
   - **Completitud.** La numeración de avisos resultó ser **por volcán**, no global (Chillán va de 2026/001 a
     2026/057; Sabancaya pasa de 500). El criterio suponía una numeración global; se aplicó por volcán. Chillán
     2026/024 a 2026/057 no tiene huecos (las correcciones CCA y CCB del 2026/051 cuentan como el mismo aviso).
     Del 2026/027 (18-10) al 2026/028 (25-10) no hay avisos de Chillán, y después del 2026/057 (14-11 23:30) el
     VAAC sólo emitió un mensaje de PRUEBA el 18-11 17:45: lo registraron por separado NOAA
     (`tgftp.nws.noaa.gov/data/raw/fv/fvag01.sabm..txt`) y la BOM de Australia (avisos de los últimos 7 días),
     copias en `D:\goes_notas\h21_vaac\crudo\`. El listado del SMN cubre las 30 marcas.
   - **Transcripción.** Los 37 textos del repo se compararon por hash SHA-256 contra lo que el sitio del SMN sirvió
     al navegador (`resultados\hash_navegador.json`): 37 de 37 iguales.
   - **Control positivo del lector.** El lector por expresiones regulares, con el léxico literal del criterio,
     coincide con la clasificación manual en 32 de 35 avisos y en **8 de 10** en la muestra al azar (semilla
     20261122). **No pasa** el 10 de 10, así que el veredicto usa la clasificación manual, que aplica las
     definiciones del criterio leyendo cada texto (la frase que decide cada caso está en `CLASIF_MANUAL` del
     script). Diferencias: 2026/055 (el polígono viene de las cámaras y el RMK dice "SATELLITE IMAGERY DOES NOT
     REVEAL THE PRESENCE OF ASH"; el léxico no tenía "DOES NOT REVEAL") y 2026/038 y 039 ("WEAK" a más de 60
     caracteres de "STLT"). Ninguna de las tres cambia el veredicto: con el lector, SI subiría a 6 y seguiría
     bajo 10.
   - **Hay SI y NO entre los avisos leídos** (13 SI, 5 POSIBLE, 17 NO), así que el lector se probó en las dos clases.
   - **Control negativo medido.** El 0 de SI en 570 horas de control no es un instrumento ciego: las mismas horas
     de control encontraron 9 avisos NO y 1 POSIBLE (26-10, 05-11, 09-11 y 11-11 son días de control con avisos).

## 5. Fuentes independientes con hora, mirado después (post hoc, no entra en el veredicto)

Los avisos traen tres reportes de tierra o aire con hora exacta. Se miran al revés: ¿había marca de VOLCAT cerca?

| Reporte independiente | Hora (UTC) | Marca VOLCAT más cercana | Δt | Qué dice el VAAC del satélite |
|---|---|---|---|---|
| OVDAS/SVO: "PUFF EMISSION" (aviso 2026/034) | 27-10 10:25 | 27-10 11:08 | +43 min | pluma vista en satélite a las 12:10, bajo cielo parcialmente cubierto |
| OVDAS/SVO: "MINOR ERUPTION ... TL FL190" (aviso 2026/050) | 10-11 21:51 | 10-11 21:38 | −13 min | no detectada a las 22:30; "faint VA plume" a las 23:40 (2026/051) |
| Piloto: "ASH BTN FL130/140" (aviso 2026/053) | 13-11 14:29 | 13-11 19:21 | +4 h 52 min | sin indicación de ceniza en satélite |

Dos de los tres reportes con hora tienen una marca de VOLCAT a menos de una hora. El del 10-11 es el más claro:
OVDAS reporta una erupción menor con columna hasta FL190 (unos 5,8 km), VOLCAT marca ceniza 13 minutos antes de
esa hora, y el analista del VAAC no la ve en el satélite hasta una hora y media después, y como "faint". El tercer
reporte, el del piloto, no tiene marca de VOLCAT. Con tres casos esto no es estadística. Los reportes de
05-11 y 07-11 ("ARS/SIGMET REPORT VA EMS") no tienen hora en el texto y no se cuentan.

## 6. Qué significa para la pregunta de fondo

- La idea 2 de S16 no da una verdad independiente de que VOLCAT acierte: casi no hay avisos a la hora de las
  marcas, y los que coinciden son del mismo satélite.
- Sí deja un dato útil: el analista del VAAC, con la alerta de VOLCAT a mano, rara vez ve en GOES-19 algo que
  valga un aviso. Cuando lo ve, lo llama débil. Es coherente con todo lo que dio H3 a H20: la ceniza de Chillán de
  oct-nov 2026 está en el borde de lo que un IR de 2 km muestra, para un humano y para nuestras reglas.
- Lo que sí es independiente son los reportes de OVDAS y de pilotos que los propios avisos citan (§5). Para usarlos
  como verdad hace falta la lista completa con hora (REAV de OVDAS, pedido de Nicolás) y no sólo los tres que los
  avisos mencionan: es la idea 7 de S16.

## 7. Desviaciones del criterio (todas declaradas aquí)

1. Numeración por volcán, no global (§4). La prueba de completitud se hizo por volcán.
2. El lector automático no pasó su control positivo; manda la clasificación manual, como prevé el criterio.
3. "Independiente" se leyó estricto: el RMK describe una observación no satelital. La variante por lista (una
   fuente no satelital en `INFO SOURCE` o `RMK`) se reporta al lado: 1 marca SI en vez de 0. Ninguna de las dos
   llega a 5.
4. Fuente: el archivo del SMN (`vaac.smn.gob.ar`, listado `productos.php`), leído desde el navegador de Nicolás
   después de que él pasó la verificación de Cloudflare. La descarga por línea de comandos quedó bloqueada a
   propósito y no se intentó esquivar.

## Fuentes

- [VAAC Buenos Aires, listado de avisos (SMN)](https://vaac.smn.gob.ar/vaac/buenosaires/productos.php?lang=es)
- [NOAA, último boletín FVAG01 SABM](https://tgftp.nws.noaa.gov/data/raw/fv/)
- [BOM, avisos de ceniza de los últimos 7 días](https://www.bom.gov.au/products/Volc_ash_recent.shtml)
- [IEM, archivo AFOS (FVAG01 llega sólo a 2008)](https://mesonet.agron.iastate.edu/cgi-bin/afos/retrieve.py?pil=FVAG01)
