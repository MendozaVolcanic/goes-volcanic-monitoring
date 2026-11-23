# H25 (S19): la explosión de 2.000 m del 27-10 (E6) medida hacia donde soplaba el GFS. Informe, 23-11-2026

**Veredicto con la regla escrita antes de medir: SIN SEÑAL.** Hacia el NNE (16,9°, viento GFS), E6 tampoco deja
firma en 11 y 12 µm: z +0,52 (la regla pide −2), con poder pleno para una capa que llena el sector (ε 0,10 y 0,15:
11 de 11 días) y 7,7 % de falsas alarmas (3 de 39). Junto con H24 (hacia el NO, z −0,15), **E6 no deja firma en
ninguna de las dos direcciones**: la sospecha de que H24 midió en el lugar equivocado queda cerrada para una capa
que cubra el sector. Para una pluma **angosta** la prueba no tiene poder (27 %), y la lectura que sí lo tiene quedó
inválida por falsas alarmas (15 %).

Criterio: `criterio_2026-11-23.md`, commit `0716d72` (empujado al remoto antes de medir). Resultados: `20df638`.
Enmienda exploratoria (escrita después del veredicto, antes de calcularla): `56fef4f`.

## 1. Para geólogo

**La duda.** El 27-10 a las 06:26 hora de Chile el OVDAS vio una columna gris oscura de 2.000 m, "asociada a
material piroclástico", y el REAV la dio hacia el NO. H24 la midió ahí y no encontró nada. Pero el viento del
modelo GFS a esa altura soplaba hacia el NNE, a 62° de esa dirección, con 6,9 m/s. Si la pluma se fue con el viento
del modelo, H24 miró al lado, y peor: la dejó dentro de su zona de referencia, que es la que se resta. Una pluma
ahí habría hecho parecer al sector más tibio, no más frío.

**Lo que se hizo.** Lo mismo que H24, con el sector de la pluma hacia el NNE: la diferencia 11 − 12 µm de cada
píxel contra su propia historia a esa hora en días despejados, comparada contra el viento cruzado en el mismo
cuadro y pareada por la temperatura esperada. Al viento cruzado se le sacaron los píxeles hacia el NO, para que una
pluma que sí se hubiera ido como dice el REAV no contaminara la referencia. Las falsas alarmas se midieron en cinco
ventanas de la mañana (de 04:20 a 09:10 hora de Chile) en los días sin actividad.

**Lo que salió.**

1. **Sin firma hacia el NNE.** El sector quedó 0,06 K *más alto* que el viento cruzado (z +0,52). Una capa de
   ε 0,10 sobre ese sector se habría visto en los 11 días de fondo; una de ε 0,05, en 4 de 11.
2. **El placebo (hacia el SSO) y Longaví tampoco detectan** (z −0,16 y −1,23). Antuco estuvo nublado en las seis
   escenas y no sirve de control ese amanecer.
3. **Las variantes informativas dicen lo mismo:** con la temperatura (BT11) en vez de la BTD, z −1,23; con el pareo
   por BT11 observada, +0,51; con la referencia de H24 sin sacar el NO, +0,61.
4. **Pluma angosta, sin respuesta formal.** Si la pluma era una franja de unos 6 km de ancho (22 de los 55 píxeles
   del sector), la mediana del sector no la ve: el poder es 27 % aun con ε 0,30. La lectura exploratoria con el
   percentil 20, que sí la ve (poder 100 %), da z +0,68, pero su tasa de falsas alarmas es 15 % y su propia regla la
   invalida. Lo que se puede decir, como lectura y no como prueba: una regla demasiado permisiva, que "detecta" en
   uno de cada siete días sin actividad, tampoco detecta E6.

**Qué significa.** El único pulso alto que H24 pudo decidir sigue sin firma infrarroja aunque se le cambie la
dirección. Esto refuerza lo que dejó H24: con verdad del OVDAS y donde se puede medir, estas plumas no tienen firma
en el IR de GOES-19. Lo que sigue abierto son los pulsos de tarde que VOLCAT marcó (H27 en curso, H24 de verano).

## 2. Las dos preguntas del instrumento y los controles

| | Pide | Medido |
|---|---|---|
| Control grande (ε 0,9 a 10 km) | ≥ 95 % | 11 de 11 (100 %) |
| Poder ε 0,15 sobre el sector | ≥ 80 % | 11 de 11 (100 %); ε 0,10 100 %; ε 0,05 36 % |
| Nulo no degenerado | MAD > 0,01 K | 0,13 K; 11 días nulos |
| Falsas alarmas, cinco ventanas | ≤ 10 % | 3 de 39 (7,7 %): 1/9, 0/9, 1/11, 1/10, 0/0 |
| Placebo contra el viento | no detecta | z −0,16 |
| Cumbre de control | no detecta | Longaví z −1,23; Antuco sin cuadros despejados |
| Pruebas del script | todas | 8 de 8 de H24 más las de geometría de H25 (R sin los píxeles a ≤ 30° de 315°, franja dentro del sector) |

1. Si D2 estuviera ciego, el poder habría caído y la clase sería SIN PODER: el poder fue 100 % con ε 0,10.
2. Si el instrumento estuviera muerto, el control grande y el MAD del nulo lo mostrarían: pasan.

La ventana +2 h (11:20 a 12:10 UTC) no aportó casos de falsa alarma (0 de 0): había 7 días con dos cuadros
despejados, pero ninguno con línea base de 3 días por píxel a esa hora. Se informa tal cual.

## 3. Lo que podría estar equivocado

- **Pluma angosta.** Es la limitación principal (§1, punto 4). El criterio decide para una capa que llena un sector
  de ±30° entre 4 y 25 km; una pluma de 6 km de ancho queda sin probar.
- **Ni el REAV ni el GFS.** La pluma pudo irse en otra dirección (por ejemplo, entre las dos). Entre H24 y H25 están
  cubiertos 285° a 345° y 347° a 47°; el hueco de 345° a 347° es despreciable, pero lo que esté fuera de esos dos
  sectores no se miró.
- **Dos miradas a E6.** Es la segunda dirección que se prueba. Como el resultado es SIN SEÑAL, la corrección por
  mirar dos veces no cambia nada (iría en contra de detectar).
- **β y tamaño de partícula.** Como en H24: la capa inyectada tiene β 0,70. Si la ceniza de Chillán tiene β cercano
  a 1, la BTD no la ve aunque sea espesa; BT11 (D1) tampoco detectó (z −1,23).
- **El campo `dia` de `h25_resultado.json` guarda el índice del día (36 = 27-10 desde el 21-09), no la fecha.** Es
  sólo un rótulo; no cambia ningún número.

## 4. Archivos

- `criterio_2026-11-23.md`, `enmienda_posthoc_1_exploratoria_2026-11-23.md`.
- `scripts\h25_medir.py` (criterio; importa `..\..\h24_pulsos_reav\scripts\h24_medir.py` sin cambios) y
  `scripts\h25_explorar.py` (enmienda).
- `resultados\`: `h25_conteo_fondo.json` y `h25_conteo.log` (antes de medir), `h25_resultado.json` y `.csv`,
  `h25_corrida.log`, `h25_explorar.json` y `h25_explorar.log`.
- Insumos de sólo lectura: `D:\goes_notas\s17\h23\` y `D:\goes_notas\s18\h24\`. No se bajó nada. Ningún archivo de
  SSEC. Nada toca `src/` ni el dashboard.

Reproducir, desde `docs\own_volcat\h25_e6_gfs\scripts\`:

```powershell
python -I h25_medir.py conteo
```

```powershell
python -I h25_medir.py
```

```powershell
python -I h25_explorar.py
```
