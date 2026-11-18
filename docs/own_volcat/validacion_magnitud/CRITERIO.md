# Validación de magnitud contra VOLCAT: criterio y exclusiones (declarado antes de medir)

Escrito y commiteado el 18-11-2026, **antes de correr ningún método propio** sobre estos
scans. Plan: `docs/own_volcat/PLAN_VALIDACION_MAGNITUD.md`, pasos 3 a 6.

## Criterio (decidido por Nicolás el 16-11-2026, no se cambia)

Un scan es consistente si el intervalo del tope VOLCAT (`top_lo_km` a `top_hi_km`, el
bloque de la barra) **se cruza** con nuestro intervalo. Sin margen. Por método
(BT-matching, Wen-Rose, ACHA ∩ ceniza). Se reporta cuántos scans cumplen, no un promedio.

## Precisiones de aplicación (no cambian el criterio, lo hacen ejecutable)

1. **Intervalo propio.** Sólo Wen-Rose declara banda β (`top_km_lo` a `top_km_hi`).
   BT-matching y ACHA devuelven un p95 sin banda: su intervalo es ese punto (intervalo
   degenerado), así que cruzar significa que el p95 cae dentro del bloque VOLCAT. No se
   inventa una banda para ellos.
2. **Misma caja.** Nuestros tres métodos corren con `radius_deg = 0.75` (±83 km), el valor
   por defecto de la app: se valida el número que vería el operador. El objeto VOLCAT
   anclado se recorta a esa misma caja antes de leer el tope. Sobre los 122 cuadros con
   tope, recortar no cambió ningún tope (medido al escribir esto).
3. **Mismo scan.** El instante del cuadro VOLCAT (`AAAA-MM-DD_HH-MM-30`) se pasa a
   `download_band_at`, que elige el scan full disk más cercano; el guard de mismo scan de
   `acquire_ash_scene` sigue activo.
4. **Perfil.** GFS archivado (`gfs_archive.fetch_gfs_profile_archive`) inyectado como
   `profile_fn`, ciclo de 6 h más cercano; el guard de edad del perfil (3 h) sigue activo.
5. **Unidad.** Un scan entra a la cuenta si VOLCAT fija tope en la caja y el scan no está
   excluido. Si nuestro método no da tope (`no_plume` o `no_data`), el scan se informa
   aparte con su motivo y no cuenta como cruce ni como fallo.
6. **Cumbre.** No se usa para filtrar: el bloque VOLCAT y el número propio se comparan tal
   como salen.

## Exclusiones (plan §3.4, opción c: a ojo, mirando sólo los cuadros VOLCAT)

Lista con motivo por cuadro en `exclusiones.json`. Mosaicos de 80 x 80 km alrededor del
volcán con el disco de anclaje de 10 km, de todos los cuadros con objeto anclado.

| Evento | Cuadros con tope VOLCAT | Excluidos | Motivo |
|---|---|---|---|
| Cotopaxi 25-10 | 5 (19:40 a 20:20) | 5 | probable convección: el objeto nace al NE y cruza sobre el volcán (plan §3.3) |
| Sabancaya 26-10 | 23 | 3 (12:20 a 12:40) | 1 a 2 píxeles IR sueltos de 12 a 14 km sobre fondo cálido, sin continuidad con la pluma de 6 a 7 km (plan §3.3) |
| Sabancaya 17-10 | 3 | 3 | objetos de 1 a 2 píxeles IR en el borde del disco, sin pluma del cráter, bloque 4 a 5 km entero bajo la cumbre de 5,96 km |
| Reventador 03-11 | 4 | 1 (20:40) | objeto casi entero fuera del disco, al NNO, sin continuidad desde el cráter |
| Sabancaya 01-11 | 46 | 0 | pluma que nace en el cráter y crece sin cortarse |
| Sabancaya 28-10 | 19 | 0 | pluma anclada de 09:10 a 11:20; los cuadros sueltos de 5 a 6 km quedan (bloque que contiene la cumbre) |
| Reventador 07-11 | 3 | 0 | pulso compacto de 20:40 a 21:00 (plan §3.3) |
| Reventador 26-10 | 6 | 0 | objetos chicos dentro del disco, 4 a 5 km sobre una cumbre de 3,56 km |
| Chillán 08-11 | 13 | 0 | pulsos anclados que derivan al SE (plan §3.4) |

Total: 122 cuadros con tope VOLCAT, 12 excluidos, **110 a correr**.

Los eventos "trampa" del 16-11 (mantos de Sabancaya, Ubinas y Copahue) y Ruiz 23-10 (un
solo píxel, descartado en el paso 2) no entran. Chillán 10, 11 y 14-11 tampoco: sus PNG no
están en la cosecha del paso 0 de este conjunto.
