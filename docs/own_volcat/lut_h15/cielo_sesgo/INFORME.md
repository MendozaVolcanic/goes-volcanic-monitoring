# Cielo despejado y nube negra de VOLCAT en εtot y β (H15, nivel B). Informe, 21-11-2026

## Vuelta 5 (21-11, noche): la forma del desfase de 11 µm

**Veredicto.** El desfase tiene forma de **efecto de vecindad de la nube**, no de ancilar ni de calibración. Es de
mesoescala (se parece entre celdas vecinas de 0,25° y nada a 1°), es estable entre cuadros, no salta en los bordes
de celda del GFS, no sigue a la SST y **crece cerca de la nube espesa**: −1,60 K a menos de 2 px, −0,86 K a más de
20 px. Lo que usamos como observación es idéntico a la L1b de NOAA (100 % de los píxeles dentro de 0,01 K), y GOES-17
no marca problema de plano focal esa noche. No apareció ninguna variante que decida, así que no hubo criterio ni
cuadros 6 a 10 en esta vuelta: se para con el mapa, como pedía el encargo.

Salidas crudas: `resultados/vuelta5_l1b.json` (prueba 1, 10 cuadros), `resultados/vuelta5_forma.txt` y
`resultados/vuelta5_mapa_desfase_c14.png` (pruebas 2 y 3, cuadros 1 a 5), `resultados/vuelta5_fpt.json` (prueba 4,
10 cuadros).

### Para geólogo

Sólo podemos ver el desfase donde la nube es tenue. Lo que importa es cómo se reparte. Si viniera de un dato de
entrada distinto (la temperatura del mar, el modelo atmosférico), sería un campo amplio y suave, con saltos en la
grilla del modelo. Si viniera del sensor, aparecería también en 12 µm o como ruido sin estructura. No es ninguna de
esas cosas: aparece en manchas del tamaño de los sistemas nubosos (decenas de km), se mueve poco entre cuadros de 5
minutos y es más fuerte junto a la nube espesa y donde la escena es más rugosa. Es como si VOLCAT, cerca de una nube,
esperara un mar más frío que el del modelo, sólo en 11 µm. Eso encaja con un cielo despejado estimado de los
alrededores, un poco contaminado por la nube, más que con el cielo despejado del modelo. Pero no encontramos en el
paquete ese campo ni su receta.

**Para Chillán:** si VOLCAT estima el cielo despejado de 11 µm desde la vecindad de la nube, nuestro ε(11) de
cualquier pluma junto a nubes saldrá más alto que el suyo, y por la sensibilidad de la vuelta 3, más "de ceniza".
Medirlo exige saber la receta.

### Números

**Prueba 1, ¿la BT que usamos es la de VOLCAT?** (`vuelta5_l1b.json`, 10 cuadros). Cada píxel de `geocatL1` se
ubicó en la grilla fija de la L1b de NOAA (lat/lon a ángulos de barrido):

| | BT(L1b con coeficientes de NOAA) − BT `geocatL1`, mediana | BT(L1b con coeficientes de `geocatL1`) − BT `geocatL1` | Píxeles dentro de 0,01 K (coef. `geocatL1`) |
|---|---|---|---|
| C14 | +0,081 K | 0,000 K | 100 % |
| C15 | +0,090 K | 0,000 K | 100 % |

GEOCAT convierte con sus propios coeficientes de Planck (C14: fk1 8496,11, bc1 0,3376, bc2 0,99908; NOAA: 8495,35,
0,2178, 0,99922). Corre la BT casi lo mismo en las dos bandas y no toca ε, que se calcula en radiancia: la radiancia
que recuperamos es la de NOAA.

**Pruebas 2 y 3, forma** (`vuelta5_forma.txt`, cuadros 1 a 5, 151.349 píxeles con 0,05 ≤ ε < 0,3):

| Forma que se buscó | Lo que dice | Medido |
|---|---|---|
| Campo suave de escala grande | ancilar distinto | autocorrelación entre celdas de 0,25° vecinas +0,63, a 1° −0,05: no es de escala grande |
| Saltos en bordes de celda GFS | resolución del ancilar | \|Δ\| entre vecinos 0,263 K dentro de la celda, 0,276 K cruzando el borde: no hay salto |
| SST / superficie | otro ancilar de superficie | ρ con SST CMC −0,19, con superficie GFS −0,11, con SST − GFS −0,14; la SST de CMC es +0,42 K más tibia que el GFS (mediana), o sea, enfriaría al revés |
| Ruido píxel a píxel | otra BT observada | descartado por la prueba 1; la vuelta 3 ya vio que es en parte suave |
| Vecindad | efecto de la nube cercana | por distancia a nube espesa (ε ≥ 0,5): −1,60 K (0 a 2 px), −1,50 (2 a 5), −1,27 (5 a 10), −1,04 (10 a 20), −0,86 (> 20); por textura de BT14: −0,80 a −0,92 K con sd 3 × 3 < 2 K, −1,21 K con > 2 K |

Estabilidad del mapa de 0,25° entre cuadros consecutivos: ρ 0,967 a 0,972 (329 a 339 celdas). Desfase de C15 en los
mismos píxeles: p5/p50/p95 = −0,01 / +0,01 / +0,09 K. Mapa: `resultados/vuelta5_mapa_desfase_c14.png` (cuadros 09:16
y 09:36).

**Prueba 4, calibración GOES-17** (`vuelta5_fpt.json`, C13, C14 y C15, 10 cuadros): `focal_plane_temperature_threshold_exceeded_count`
= 0 en todos, temperatura máxima del plano focal 84,0 a 84,9 K con umbral de 93 K (C14, C15) y 100 K (C13), DQF = 0
en todo el dominio. Además C14 y C15 comparten umbral, así que un efecto del loop heat pipe tocaría las dos bandas.
No hay evidencia en los archivos de una corrección de calibración que no tengamos.

### Pregunta para el correo (precisa la 3)

En nube tenue sobre mar, el ε(11) de VOLCAT se reproduce con un cielo despejado de 11 µm más frío que el de
`geocatRTM`: −0,86 K lejos de la nube espesa y −1,6 K junto a ella, en manchas de decenas de km. En 12 µm no hay
desfase, y la radiancia observada es la de la L1b. ¿El cielo despejado del canal 14 que entra a εtot se ajusta
empíricamente con los píxeles vecinos (por ejemplo, desde los más tibios alrededor), y por qué sólo en 11 µm?

### Archivos de la vuelta 5

`scripts/vuelta5_l1b.py`, `scripts/vuelta5_gfs_sfc.py` (venv_hdf4; superficie y TPW del GFS a
`D:\goes_cache\cielo_sesgo\gfs_sfc.npz`), `scripts/vuelta5_forma.py`, `scripts/vuelta5_fpt.py`.

---

## Vuelta 4 (21-11, noche): ¿el desfase de 11 µm es el sesgo de BT14 por objeto? No

**Veredicto.** Descartado con la salida del propio VOLCAT, y se paró antes de las pruebas 2 y 3, como pedía el
encargo. En los 10 cuadros, **ningún objeto de VOLCAT tiene sesgo de BT14 calculado**: los 108 a 588 objetos por
cuadro traen todos los resúmenes de sesgo de BT14 en relleno (−999) y 0 píxeles válidos o elegibles para el sesgo.
Además, sólo el 0,4 % de los píxeles de nube tenue cae dentro de un objeto, y el desfase de −1,05 K está **fuera**
de los objetos. Dentro de ellos, el desfase mediano es incluso positivo (+0,54 K).

Criterio subido antes de medir: `criterio_vuelta4_sesgo_objeto_2026-11-21.md` (commit b0b519e). Salidas crudas:
`resultados/vuelta4_ashobj.json` (conteos de `geocatASHOBJ`, leídos en venv_hdf4) y
`resultados/vuelta4_sesgo_objeto.json`.

### Para geólogo

La idea era buena por la firma: sólo en 11 µm, dispersa, sin relación con el vapor ni el ángulo, como una cantidad
medida en la vecindad. Pero para que el ε publicado llevara un sesgo calculado por objeto harían falta dos cosas:
que VOLCAT hubiera calculado ese sesgo, y que los píxeles con desfase estuvieran dentro de los objetos. No pasa
ninguna de las dos. VOLCAT sí calculó, para todos sus objetos, el sesgo de la diferencia 11 − 12 µm
(`Btd1112_Bias_Per50`), pero no el de BT14. Y los objetos son chicos: suman de 207 a 1.530 píxeles por cuadro,
contra unos 30 mil píxeles de nube tenue. El desfase de 1 K de 11 µm vive en toda la nube tenue, sin objeto.

### Números (10 cuadros)

| Cuadro | Objetos | Píxeles en objetos | Objetos con sesgo BT14 válido | Objetos con `Btd1112_Bias_Per50` | Píxeles tenues | Tenues en objeto | Desfase C14 fuera (mediana) | Desfase C14 dentro |
|---|---|---|---|---|---|---|---|---|
| 09:16 | 588 | 1.530 | 0 | 588 | 29.865 | 62 | −0,96 K | +0,54 K |
| 09:21 | 137 | 222 | 0 | 137 | 30.017 | 125 | −0,94 | +0,72 |
| 09:26 | 193 | 302 | 0 | 193 | 30.199 | 170 | −0,99 | +0,56 |
| 09:31 | 122 | 213 | 0 | 122 | 30.503 | 146 | −1,00 | +0,65 |
| 09:36 | 198 | 305 | 0 | 198 | 30.765 | 191 | −1,02 | +0,49 |
| 09:41 | 139 | 207 | 0 | 139 | 30.562 | 122 | −1,04 | +0,61 |
| 09:46 | 159 | 254 | 0 | 159 | 30.517 | 138 | −1,13 | +0,45 |
| 09:51 | 108 | 215 | 0 | 108 | 30.517 | 90 | −1,12 | +0,54 |
| 09:56 | 133 | 263 | 0 | 133 | 30.866 | 95 | −1,19 | +0,40 |
| 10:01 | 171 | 359 | 0 | 171 | 30.631 | 115 | −1,10 | +0,42 |
| **Total** | | | **0** | | **304.442** | **1.254 (0,4 %)** | **−1,05 K** | **+0,54 K** |

"Píxeles tenues": 0,05 ≤ εtot < 0,3, con desfase implícito calculable. "En objeto": `Ash_Object_Mask` > 0 de
`geocatDIAGS1`. `Ash_Group_Id_2d` sólo tiene píxeles válidos desde 09:46 (30 a 118). Condición (a) del criterio,
ningún objeto con sesgo de BT14: cumplida. Condición (b), menos de 10 % de los tenues en objeto con desfase fuera
≤ −0,5 K: cumplida. Cualquiera de las dos descarta.

### Requisito para Chillán (anotado, no resuelto)

En este caso el ε no depende de los objetos. Si en otra versión de VOLCAT o en otro caso sí dependiera, aplicarlo a
Chillán exigiría formar los objetos nosotros o usar `event_idx`.

### Qué queda para el correo

La pregunta de la vuelta 3 sigue igual, con un candidato menos: el cielo despejado de 11 µm que entra a εtot es ~1 K
más frío que el de `geocatRTM` en toda la nube tenue, también fuera de los objetos, y en 12 µm no hay desfase.
**No es el sesgo de BT14 por objeto**, que en esta corrida no se calculó para ningún objeto. Quedan sin probar una
corrección de calibración o de cielo despejado sólo de la banda 14 en GEOCAT, o un `geocatRTM` publicado distinto
del que usó VOLCAT.

### Archivos de la vuelta 4

`scripts/vuelta4_ashobj_hdf.py` (venv_hdf4), `scripts/vuelta4_sesgo_objeto.py`; `resultados/vuelta4_ashobj.json`,
`resultados/vuelta4_sesgo_objeto.json`.

```powershell
D:\goes_notas\busqueda_2026-11-20\venv_hdf4\Scripts\python.exe -I docs/own_volcat/lut_h15/cielo_sesgo/scripts/vuelta4_ashobj_hdf.py
```

```powershell
python -I docs/own_volcat/lut_h15/cielo_sesgo/scripts/vuelta4_sesgo_objeto.py
```

---

## Vuelta 3 (21-11, noche): el exceso de nuestro ε(11 µm) en nube tenue

**Veredicto.** Las tres candidatas físicas quedan descartadas en los cuadros 6 a 10, como pedía el criterio: el
ángulo de la normalización, la nube negra con atmósfera encima y el cielo despejado del mar por emisividad o vapor.
Por eso se para. Lo que queda: VOLCAT calcula ε(11) como si el cielo despejado de **sólo** 11 µm fuera ~1,1 K más
frío que `geocatRTM`. Ese desfase no sigue al vapor, ni al ángulo, ni a la celda del GFS, y en 12 µm no existe. **Y
el residuo importa:** con ε(11) 0,015 más alto, como el nuestro, 219 píxeles de nube tenue pasan a probabilidad
≥ 0,5 donde VOLCAT tiene 50; con 0,015 más bajo, se pierden 46 de esos 50.

Criterio subido antes de medir: `criterio_vuelta3_eps11_2026-11-21.md` (commit 1bd1d85). Salidas crudas:
`resultados/explorar_c14_1a5.txt` (cuadros 1 a 5) y `resultados/vuelta3_eps11.json` (cuadros 6 a 10).

### Para geólogo

Con una nube muy tenue (ε ~ 0,1), el satélite ve casi todo el calor del mar a través de ella. La emisividad que
se calcula depende entonces casi entera de cuánto calor se espera del mar sin nube (el cielo despejado), y casi nada
de la nube de referencia. Un exceso de 0,013 en ε equivale a esperar el mar 1 K más tibio que VOLCAT.

Se probaron las tres causas físicas sensatas, cada una con una predicción escrita antes de mirar los cuadros de
validación:

1. **Que VOLCAT lleve ε al nadir con otro ángulo** (el de la nube a su altura, o por camino óptico). No: si fuera
   así, el β que reconstruimos con su ε(11) saldría desplazado en la misma proporción, y sale exacto (diferencia
   mediana de 0,16 a 0,39 % en todos los tramos). Además, a 16 km de altura el ángulo cambia cos θ en 0,0012 como
   máximo. La forma de la normalización también es la misma: por camino óptico da la misma fórmula.
2. **Que la nube negra lleve la atmósfera de encima.** No: para explicar la nube tenue, la nube negra tendría que
   ser 18 K más fría que la que calza en nube espesa (180 contra 198 K, mediana), y en 36 % de los píxeles tenues no
   hay ninguna nube negra que sirva.
3. **Que el cielo despejado del mar sea otro** (emisividad del mar que cambia con el ángulo, u otra columna de
   vapor). No: las dos cosas moverían más la banda de 12 µm que la de 11, y en 12 µm el desfase es +0,02 K. El de
   11 µm no se ordena con el agua precipitable (ρ −0,05) ni casi con el ángulo (ρ −0,19).

La dependencia con el ángulo que se veía en la vuelta 1 (k/cos θ de 0,88 a 1,02) es compatible con una mezcla: la
nube tenue está casi toda bajo 31° de cenital, y la medida juntaba todos los tramos de ε. Separado por ángulo y sólo
en nube tenue, el exceso de ε es +0,013 a +0,016 entre 20 y 34°.

**Qué significa para Chillán.** Este residuo no es un detalle: en el tramo de ε de 0,1 a 0,2, un ε(11) 0,015 más
alto (lo que nos pasa) cambia de clase a 2,5 % de los píxeles y multiplica por cinco los de probabilidad alta. Antes
de aplicar las tablas a Chillán hay que resolver el cielo despejado de 11 µm. La pregunta para el correo queda
concreta: qué ajuste lleva el cielo despejado de 11 µm que entra a εtot y que no lleva el de 12 µm.

### Números (cuadros 6 a 10)

| Candidata | Prueba (criterio) | Medido | ¿Descartada? |
|---|---|---|---|
| C1 ángulo | mediana de (β reconstruido / β VOLCAT − 1) dentro de ±0,005 en todos los tramos, y Δcos θ a 16 km < 0,005 | −0,0016 (0,05 a 0,1), −0,0020 (0,1 a 0,2), −0,0030 (0,2 a 0,3), −0,0030 (0,3 a 0,5), −0,0039 (0,5 a 0,9); Δcos máx. 0,0012 | sí |
| C2 nube negra | nube negra implícita en tenue (0,05 a 0,3) y en espesa (0,85 a 0,98) difieren > 10 K | tenue p5/p50/p95 = 138 / 180 / 205 K (97.372 píxeles con solución, 55.721 sin solución); espesa 196 / 198 / 200 K; diferencia −18,0 K | sí |
| C3 cielo del mar | \|desfase C15\| < 0,2 K con desfase C14 ≤ −0,5 K; \|ρ con TPW\| < 0,2; \|ρ con θ\| < 0,3 | C14 p5/p50/p95 = −2,65 / −1,11 / +0,14 K; C15 −0,01 / +0,02 / +0,10 K; ρ TPW −0,045; ρ θ −0,186 | sí |

Base (V1, N1, S0, H1), por tramo de εtot de VOLCAT:

| Tramo | Píxeles | ε(11) dentro de 0,01 | Δε mediana | β(12/11) con H1 dentro de 0,02 | Δβ mediana |
|---|---|---|---|---|---|
| 0,05 a 0,1 | 59.214 | 30,7 % | +0,013 | 5,4 % | −0,18 |
| 0,1 a 0,2 | 53.699 | 31,3 % | +0,016 | 10,6 % | −0,11 |
| 0,2 a 0,3 | 40.180 | 22,0 % | +0,018 | 9,4 % | −0,09 |
| 0,3 a 0,5 | 153.181 | 45,4 % | +0,001 | 32,3 % | −0,006 |
| 0,5 a 0,9 | 316.017 | 62,6 % | −0,006 | 56,1 % | +0,011 |

Por ángulo (ε 0,05 a 0,3): 20 a 28° (58.992 píxeles) Δε +0,013; 28 a 31° (92.702) +0,016; 31 a 34° (810) +0,014;
34 a 37° (589) +0,009.

Nivel B con las reglas del frente 1 (sin cambios respecto de la vuelta 2, misma configuración): κ 0,326, |ΔP| ≤ 0,05
en 91,6 %, recuperados 20,9 %; con εtot < 0,2: κ 0,641, 96,1 %, 82,2 %; 0,2 a 0,5: κ 0,054, 92,8 %, 2,9 %; ≥ 0,5:
κ 0,364, 90,7 %, 23,8 %.

### Sensibilidad a ±0,015 en ε(11), tramo 0,1 a 0,2

Nivel A (ε y β de VOLCAT) con las reglas del frente 1. Son 8.697 píxeles con probabilidad publicada; 50 tienen
P_VOLCAT ≥ 0,5. Sin perturbar, la reproducción es exacta (|ΔP| p95 = 5·10⁻¹²). (a) sólo ε cambia; (b) ε(12),
ε(7,3) y ε(8,5) oblicuos fijos, con los β recalculados (lo físico, que es lo que nos pasa).

| Perturbación | \|ΔP\| > 0,05 | Cruzan 0,5 | P ≥ 0,5 que se pierden | P < 0,5 que pasan a ≥ 0,5 | \|ΔP\| p95 |
|---|---|---|---|---|---|
| (a) +0,015 | 0,0 % | 0,0 % | 0 | 0 | 2·10⁻¹⁰ |
| (a) −0,015 | 0,3 % | 0,2 % | 20 | 0 | 0,0005 |
| **(b) +0,015** | 8,1 % | 2,5 % | 0 | **219** | 0,11 |
| **(b) −0,015** | 0,7 % | 0,5 % | **46** | 0 | 0,002 |

Lectura: la tabla casi no reacciona al eje εtot en sí (a). Reacciona a través de β (b): un ε(11) más alto baja β y
lo vuelve más "de ceniza". El nuestro sale 0,013 a 0,016 más alto, o sea, el caso (b) +0,015. En Mauna Loa eso
explica por qué en nivel B, con εtot < 0,2, damos 759 píxeles ≥ 0,5 contra 494 de VOLCAT (`nivelB` de
`vuelta3_eps11.json`).

### Pregunta para el correo (precisa la 3)

En nube tenue sobre mar, el ε(11) de VOLCAT se reproduce con un cielo despejado de 11 µm ~1,1 K más frío que el
que publica `geocatRTM` (mediana; p5 −2,7, p95 +0,1 K). El de 12 µm se reproduce sin cambio (+0,02 K). ¿El cielo
despejado del canal 14 que entra a εtot lleva un ajuste propio, por ejemplo el sesgo de BT14 (`Bt14_Bias_*`), una
corrección de calibración de GOES-17 o un promedio espacial, que el de 12 µm no lleva?

### Archivos de la vuelta 3

`scripts/explorar_c14_1a5.py` (exploración, cuadros 1 a 5), `scripts/vuelta3_eps11.py` (decide y sensibilidad);
`resultados/explorar_c14_1a5.txt`, `resultados/vuelta3_eps11.json`, `resultados/vuelta3_eps11_log.txt`.

```powershell
python -I docs/own_volcat/lut_h15/cielo_sesgo/scripts/vuelta3_eps11.py
```

---

## Vuelta 2 (21-11, tarde): por qué nuestro β(12/11) salía 0,30 bajo el de VOLCAT en nube tenue

**Veredicto.** Explicado en dos partes y reproducido, pero la regla principal del criterio no se cumple con
nuestro ε. (1) **La tabla de VOLCAT trae una corrección por vapor de agua:** con εtot < 0,25 y agua precipitable
> 2,5 cm, a β(12/11) se le suma 0,2. Explica 0,2 de los 0,30. (2) **El resto viene de nuestro ε de 11 µm, no del
cielo despejado de 12 µm:** si se toma el ε(11) de VOLCAT y se calcula el ε(12) nuestro (cielo `geocatRTM`, nube
negra en el punto frío del GFS) más la corrección, β coincide dentro de 0,02 en el 98,8 al 100 % de los píxeles de
todos los tramos (posterior). Con nuestro ε(11), en cambio, β queda dentro de 0,02 sólo en el 7,9 % de los píxeles
con εtot 0,05 a 0,2 (pide 80 %): **no cumple**. La pregunta pendiente se achica a una sola banda: cómo arma VOLCAT
el cielo despejado o la radiancia de 11 µm en nube tenue.

Criterio subido antes de medir: `criterio_vuelta2_beta_2026-11-21.md` (commit 2db5d46). Salidas crudas:
`resultados/vuelta2_beta.json`, `vuelta2_beta_log.txt`, `explorar_beta_1a5.txt`, `posterior_beta_residuo.txt`,
`lut_atributos_beta.txt`, `lut_datasets_fct.txt`.

### Para geólogo

β(12/11) compara cuánto tapa la nube a 12 µm contra cuánto tapa a 11 µm, y es lo que separa ceniza (β bajo 1)
de hielo o gotas (β sobre 1). En una nube tenue, el vapor de agua de la atmósfera entre la nube y el satélite
absorbe más a 12 µm que a 11 µm y deforma esa razón. Hawái esa noche tenía 4 a 6 cm de agua precipitable, una
atmósfera tropical muy húmeda. VOLCAT lo sabe: su tabla dice que, si la nube es tenue (εtot < 0,25) y el aire es
muy húmedo (más de 2,5 cm de agua precipitable), se suma 0,2 a β, y 0,05 si está entre 1,5 y 2,5 cm. El salto se ve
en los datos justo donde la tabla lo pone: la diferencia de β entre VOLCAT y nosotros cae de +0,28 a +0,07 al
cruzar εtot = 0,25.

Lo que queda después de esa corrección no es un problema de 12 µm. Nuestra emisividad de 11 µm en nube tenue sale
algo más alta que la de VOLCAT (+0,012 a +0,016, ver la vuelta 1), y como β es casi el cociente entre las dos
emisividades, un ε de 11 µm algo alto con una nube que tapa 5 % se convierte en un β 0,1 a 0,2 más bajo. Con el ε de
11 µm de VOLCAT, nuestro cálculo de 12 µm da su β casi exacto.

**Para Chillán:** la corrección por vapor sí se puede aplicar, pero en Chillán el aire es mucho más seco que en
Hawái. Con 1,5 a 2,5 cm de agua precipitable la tabla suma sólo 0,05, y bajo 1,5 cm no suma nada; ese escalón no se
pudo probar aquí, porque en todo el dominio de Mauna Loa el agua precipitable supera 4 cm (`vuelta2_beta.json`,
`tpw_cm_p1_p50_p99`). El ε de 11 µm sigue sin estar listo.

### Números

Qué se miró antes de escribir el criterio (cuadros 1 a 5, `explorar_beta_1a5.txt`): con εtot de 0,05 a 0,2 el β de
VOLCAT va de 0,91 a 1,53 (p5 y p95), con mediana 1,27, y el nuestro de 0,71 a 1,05, con mediana 0,93. El valor más
repetido del β de VOLCAT está en sólo el 0,32 % de los píxeles: **no es un β reemplazado por una constante**. Se
correlaciona con el sesgo de BTD igual que el nuestro (Spearman −0,88 contra −0,96).

Atributos de la tabla de píxel (leídos, `lut_datasets_fct.txt` y `lut_atributos_beta.txt`):

| Atributo | Valor | Lectura |
|---|---|---|
| `X_COND_BETA1112_TOT_H20_CORRECTION_FCT` | −999; 1,5; 2,5 | cortes de X; X = agua precipitable en cm (candidata; VOLCAT la guarda por píxel) |
| `INTERCEPT_BETA1112_TOT_H20_CORRECTION_FCT` | 0; 0,05; 0,2 | lo que se suma a β(12/11) |
| `MAX_EMISS14_TOT_H20_CORRECTION` | 0,25 | sólo con εtot menor |
| `COEFF_BETA1112_TOT_FCT1`, `ACTUAL_BETA_RANGE` | 0,8896; −0,2046 · 0,48 a 0,79 | β desde el sesgo de BTD; da β < 1, no explica este tramo |
| `BETA1112_FROM_BTD_BIAS_LB_EMISS14_WATER` | 0,02 | esa relación, bajo εtot 0,02 en agua |
| `SLOPE/INTERCEPT_BETA1112_FCT2`, `FCT3` | −0,70; 0,031 · −1,19; 1,14 | ecuaciones 8 y 7 de SECO Parte 1 (prefiltros) |

Ángulo a la altura de la nube (punto 3 del encargo): descartado por geometría. A 16 km de altura y θ = 31°, cos θ
cambia de 0,8572 a 0,8577, unas 200 veces menos que el residuo de la vuelta 1.

Elección del cielo despejado (cuadros 1 a 5, εtot 0,25 a 0,5, β dentro de 0,02): S0 28,9 %; la mejor local (L M1
p50) 29,1 %, empatada dentro de 0,002, así que gana S0 por ser la más simple; las de cuadro entero, 25,5 a 27,8 %.

Validación (cuadros 6 a 10, H1 = con corrección por vapor, S0):

| Tramo de εtot VOLCAT | Píxeles | β dentro de 0,02, H1 | Δβ p5 / p50 / p95, H1 | β dentro de 0,02, H0 | Δβ mediana, H0 | ε dentro de 0,01 |
|---|---|---|---|---|---|---|
| **0,05 a 0,2 (regla principal, pide 80 %)** | 112.913 | **7,9 %** | −0,34 / −0,145 / +0,009 | 0,0 % | −0,345 | 31,0 % |
| 0,2 a 0,25 | 19.582 | 8,1 % | −0,39 / −0,122 / +0,005 | 0,0 % | −0,292 | 20,6 % |
| 0,25 a 0,5 | 173.779 | 29,7 % | −0,12 / −0,013 / +0,043 | igual | igual | 42,8 % |
| 0,5 a 0,9 | 316.017 | 56,1 % | −0,035 / +0,011 / +0,039 | igual | igual | 62,6 % |
| 0,05 a 0,9 (regla de la vuelta 1) | 622.291 | 38,5 % | −0,23 / −0,003 / +0,039 | 36,8 % | | 50,0 % |

**No cumple** (`cumple_principal_beta_0.05_0.2` = false). Δβ es nuestro menos VOLCAT.

Posterior (no decide, `posterior_beta_residuo.txt`): β con el ε(11) de VOLCAT y nuestro ε(12), más H1:

| Tramo | Cuadros 1 a 5: dentro de 0,02 | Cuadros 6 a 10: dentro de 0,02 | Mediana 6 a 10 |
|---|---|---|---|
| 0,05 a 0,1 | 99,1 % | 98,9 % | −0,0016 |
| 0,1 a 0,2 | 99,9 % | 99,9 % | −0,0020 |
| 0,2 a 0,25 | 99,8 % | 98,8 % | −0,0029 |
| 0,25 a 0,5 | 100,0 % | 100,0 % | −0,0028 |
| 0,5 a 0,9 | 99,4 % | 98,8 % | −0,0035 |

En el mismo archivo, el desfase del cielo despejado de 12 µm que haría calzar el β de VOLCAT, dado su ε(11), es de
0,00 a 0,08 K en la mediana. El cielo despejado de 12 µm de `geocatRTM` es el que usa VOLCAT. Este resultado
también confirma la normalización al nadir de la vuelta 1: el ε(11) de VOLCAT, llevado de vuelta al oblicuo con
cos θ, da su β exacto.

Nivel B con las reglas del frente 1 (R1 + R2 + R3, `nt_regla.py` del PR 75, commit af0e8ca), cuadros 6 a 10:

| | Tramo | Píxeles | P_VOLCAT ≥ 0,5 | \|ΔP\| ≤ 0,05 | κ | Recuperados |
|---|---|---|---|---|---|---|
| H1, S0 | todo | 502.234 | 27.075 | 91,6 % | 0,326 | 20,9 % |
| | εtot < 0,2 | 29.674 | 494 | 96,1 % | 0,641 | 82,2 % |
| | 0,2 a 0,5 | 147.709 | 5.150 | 92,8 % | 0,054 | 2,9 % |
| | ≥ 0,5 | 324.851 | 21.431 | 90,7 % | 0,364 | 23,8 % |
| H0, S0 | todo | 502.234 | 27.075 | 90,1 % | 0,298 | 21,2 % |
| | εtot < 0,2 | 29.674 | 494 | 70,8 % | 0,217 | 98,6 % |
| Regla etapa 2 | | | | ≥ 90 % | ≥ 0,90 | ≥ 90 % |

La corrección por vapor ordena la nube tenue (κ de 0,22 a 0,64 bajo 0,2), pero el nivel B sigue lejos en conjunto.
Con εtot sobre 0,2, el error de ε(11) mueve el casillero de las tablas y la probabilidad.

### Pregunta para el correo (reemplaza la 4 de la vuelta 1 y precisa la 3)

- (4, contestada con la tabla) β(12/11) en nube tenue: ¿se aplica `BETA1112_TOT_H20_CORRECTION` (+0,05 / +0,2 con
  agua precipitable > 1,5 / 2,5 cm y εtot < 0,25)? ¿X es el agua precipitable del GFS en cm? En Mauna Loa el salto
  de +0,21 en εtot = 0,25 lo confirma.
- (3, nueva forma) Con nube tenue, nuestro ε(11) sale +0,012 a +0,016 sobre el suyo, mientras que ε(12) y la nube
  negra calzan. ¿El cielo despejado de 11 µm (canal 14) que entra a εtot tiene algún ajuste que no tenga el de
  12 µm, por ejemplo el sesgo de BT14 (`Bt14_Bias_*`), o una radiancia observada filtrada o promediada?

### Archivos de la vuelta 2

Scripts: `explorar_beta_1a5.py`, `extraer_tpw.py` (venv_hdf4; agua precipitable a `D:\goes_cache\cielo_sesgo\tpw.npz`),
`vuelta2_beta.py` (decide), `posterior_beta_residuo.py`. Reglas del frente 1: copia de lectura del commit af0e8ca
en `D:\goes_cache\cielo_sesgo\nt\` (no se sube a esta rama).

```powershell
D:\goes_notas\busqueda_2026-11-20\venv_hdf4\Scripts\python.exe -I docs/own_volcat/lut_h15/cielo_sesgo/scripts/extraer_tpw.py
```

```powershell
python -I docs/own_volcat/lut_h15/cielo_sesgo/scripts/vuelta2_beta.py
```

---

## Vuelta 1

**Veredicto.** La hipótesis del encargo (VOLCAT corrige el cielo despejado con el sesgo local de 12 px antes de
calcular ε y β) **no reproduce** y el material local no la apoya: el sesgo local vive en el paso de objeto, no en
el de píxel. Lo que sí apareció, mirando sólo los cuadros 1 a 5: **VOLCAT publica εtot llevado al nadir**, y con
eso la nube negra en el punto más frío del perfil GFS calza en nube espesa (91 % de los píxeles dentro de 0,01).
Aun así, en los cuadros 6 a 10 nuestro εtot queda dentro de 0,01 del de VOLCAT en el 48 % de los píxeles (pide
80 %) y β(12/11) dentro de 0,02 en el 34 % (pide 80 %): **no cumple**. El nivel B de la etapa 2 sigue lejos
(κ 0,21). **El cielo corregido no queda listo para aplicar a Chillán.**

Criterio subido antes de medir: `criterio_2026-11-21.md` (commit e88017d). Salida cruda: `resultados/cielo_sesgo.json`,
`resultados/cielo_sesgo_log.txt`, `resultados/posterior_residuo.txt`.

## 1. Para geólogo

**El fenómeno.** Para saber si una nube es ceniza, VOLCAT mira cuánto "tapa" la nube el calor que sube del mar o
del suelo (la emisividad ε, de 0 sin nube a 1 nube opaca) y cómo cambia esa transparencia entre 11 y 12 µm (β).
Para calcular ε hay que comparar lo que ve el satélite con dos extremos: lo que vería sin nube (cielo despejado,
lo calcula un modelo radiativo con el GFS) y lo que vería con una nube negra arriba de todo (en la tropopausa).
En H15 nuestro ε salía 0,05 más alto que el de VOLCAT en Mauna Loa, y eso arrastraba la probabilidad de ceniza.
La sospecha era que VOLCAT corrige su cielo despejado con lo que observa en los píxeles despejados vecinos
(±12 píxeles), porque así lo dice una línea de su configuración.

**Qué dice el material antes de medir.** Las tres líneas de la configuración sobre el sesgo local están en el
bloque que decide qué píxeles pertenecen a un objeto de ceniza, no en el cálculo por píxel. En los archivos del
caso, el campo del sesgo (`Bt14_Bias_Env_Per75`) es una variable del paso de objeto, mientras que ε y β son del
paso de píxel. SECO usa ese sesgo para la bandera de confianza del objeto. O sea: el sesgo local de 12 px es una
herramienta para agrupar y calificar objetos, no para corregir ε.

**Qué se encontró mirando los cuadros 1 a 5.** La diferencia entre nuestro ε y el de VOLCAT no tenía la forma de
un error de cielo despejado ni de nube negra, sino la de un **cambio de camino óptico**: el satélite mira Hawái
en oblicuo (31° de cenital), así que atraviesa más nube que si mirara en vertical. VOLCAT publica la emisividad
que tendría la nube vista desde arriba (al nadir). El exponente que relaciona su ε con el nuestro sigue al coseno
del ángulo: 0,889 contra 0,887, 0,853 contra 0,843, 0,819 contra 0,793 en tres franjas de ángulo. β no cambia con
esa operación, por eso en H15 β coincidía mucho mejor que ε.

**Qué se probó** (criterio fijo, variantes elegidas en los cuadros 1 a 5, juzgadas en 6 a 10):
1. Vista: ε oblicuo o llevado al nadir.
2. Nube negra, elegida en nube espesa (donde el cielo despejado casi no pesa): tropopausa del GFS o punto más
   frío de su perfil.
3. Cielo despejado, elegido en nube tenue (donde la nube negra casi no pesa): sin corrección, sesgo local en
   ±12 px o sesgo de todo el cuadro, con dos máscaras de despejado, percentiles 25, 50 y 75 y tres juegos de
   bandas (37 variantes).

**Veredicto, en palabras.** La normalización al nadir es la pieza grande: sin ella, ε dentro de 0,01 en el 8,5 %
de los píxeles; con ella, 50 %. El sesgo local casi no puede actuar: sólo 6 a 10 % de los píxeles nublados tienen
cinco o más píxeles despejados a ±12 px, porque esa noche Hawái estaba casi cubierto. La mejor corrección de cielo
despejado en los cuadros 1 a 5 fue una del cuadro entero, no local, y en los cuadros 6 a 10 no mejoró sobre no
corregir (48,1 % contra 50,0 %). Queda un residuo de ±0,02 en ε y, en nube tenue (ε 0,05 a 0,2), **nuestro
β(12/11) sale 0,30 más bajo que el de VOLCAT en la mediana: ni un píxel dentro de 0,02**. Esa diferencia en β es
la que pesa para Chillán, cuyas plumas tienen ε cerca de 0,16, y no se explica con un cielo despejado sensato:
es la regla de nube tenue (frente de la otra sesión) o algo del código que no vemos.

**Qué significa para Chillán.** No se puede llevar este cielo despejado a Chillán como "el de VOLCAT": no
reproduce. Sí queda algo utilizable y comprobable: si alguna prueba compara nuestro ε con el de VOLCAT, hay que
llevar el nuestro al nadir primero. En Chillán, visto desde GOES-19, el cenital ronda 43° (geometría, no medido
en datos), más que los 31° de Mauna Loa, así que esa corrección pesa más ahí.

## 2. Números

### Lectura del material (no decide)

| Fuente | Qué dice del sesgo de cielo despejado |
|---|---|
| `volcat_ash_detection_GOESR.config`, líneas 30 a 32 | `use local clear bias analysis = 1`, `12 !clear bias dpix window`, `Use BTD1112 and BTD8511 clear bias' in ash object membership`; dentro del bloque de membresía a objeto (líneas 18 a 32) |
| `geocatDIAGS1` del caso | `Bt14_Bias_Env_Per75` es `vcat_ashdet_obj_*` (objeto); `cloud_emissivity_ch14_tot` y los β son `vcat_ashdet_pix_*` (píxel) |
| `geocatASHOBJ` del caso | sesgo resumido por objeto: máximo y media de BT14 en objeto y ambiente, percentiles 1, 5 y 50 del sesgo de BTD 11-12 y 8,5-11 |
| SECO Parte 2 §4.3 (vía `criterio_H11_2026-11-19.md`) | BTbias = despejado modelado − observado; media en objeto y anillo de 1 a 12 px; bandera de confianza CF |

Píxeles despejados en los cuadros 1 a 5 (sesgo = despejado modelado − observado, p25/p50/p75, K):

| Máscara | Fracción despejada | C14 | C15 | C10 |
|---|---|---|---|---|
| M1 (VOLCAT no calculó ε) | 4,5 % | −0,27 / +0,02 / +0,30 | −0,75 / −0,41 / −0,06 | −2,62 / −2,05 / −1,54 |
| M2 (prueba propia) | 6,1 % | −0,09 / +0,40 / +0,91 | −0,49 / +0,03 / +0,59 | −2,38 / −1,80 / −1,19 |

Cobertura de la corrección local (píxeles con 0,05 ≤ ε ≤ 0,9 y ≥ 5 despejados a ±12 px): M1 7,3 % (cuadros 1 a 5)
y 6,0 % (6 a 10); M2 10,2 % y 10,2 %.

### Paso 1: vista y nube negra (cuadros 1 a 5, 0,85 ≤ ε_VOLCAT ≤ 0,98, cielo `geocatRTM`)

| Variante | \|Δε\| ≤ 0,01 | Δε p5 / p50 / p95 |
|---|---|---|
| V0 oblicuo, N0 tropopausa | 0,0 % | +0,025 / +0,040 / +0,053 |
| V0 oblicuo, N1 punto frío | 0,0 % | +0,024 / +0,037 / +0,047 |
| V1 nadir, N0 tropopausa | 80,1 % | −0,011 / +0,003 / +0,014 |
| **V1 nadir, N1 punto frío (elegida)** | **91,4 %** | −0,011 / −0,002 / +0,007 |

### Paso 2: cielo despejado (cuadros 1 a 5, 0,05 ≤ ε_VOLCAT < 0,5, con V1 y N1)

| Variante | \|Δε\| ≤ 0,01 | \|Δβ(12/11)\| ≤ 0,02 |
|---|---|---|
| **G, M2, p75, C14 y C15 (elegida)** | **53,8 %** | 15,8 % |
| G, M2, p50 | 48,6 % | 15,2 % |
| G, M1, p75 | 46,5 % | 15,1 % |
| L (local ±12 px), M2, p50, mejor de las locales | 43,0 % | 17,1 % |
| L, M1, p25, peor de las locales | 39,6 % | 16,3 % |
| S0 sin corrección | 39,2 % | 16,3 % |

Las 37 en `cielo_sesgo.json`, clave `paso2_S_cuadros_1a5_eps_0.05_0.5`. Dentro de G, juntar C14 y C15 o sumar C10
no cambia ε (sólo C14 entra en ε14) y mueve β en ±0,01.

### Paso 3: validación (cuadros 6 a 10, 0,05 ≤ ε_VOLCAT ≤ 0,9, 622.291 píxeles)

| | Elegida (V1, N1, G M2 p75) | Pide | Sin corregir cielo (V1, N1, S0) | Oblicua (V0, N1, G M2 p75) |
|---|---|---|---|---|
| \|Δε\| ≤ 0,01 | **48,1 %** | ≥ 80 % | 50,0 % | 8,5 % |
| Δε p5 / p50 / p95 | −0,025 / −0,008 / +0,015 | | −0,017 / −0,000 / +0,027 | +0,004 / +0,043 / +0,067 |
| \|Δβ(12/11)\| ≤ 0,02 | **34,3 %** | ≥ 80 % | 36,8 % | 34,3 % |
| Δβ(12/11) p5 / p50 / p95 | −0,36 / +0,000 / +0,044 | | | |
| \|Δβ(7,3/11)\| ≤ 0,02 (informa) | 69,2 % | | | |
| **Cumple** | **no** | | | |

Por tramo de ε_VOLCAT, variante elegida:

| Tramo | Píxeles | \|Δε\| ≤ 0,01 | \|Δβ(12/11)\| ≤ 0,02 | Δβ(12/11) mediana | \|Δβ(7,3/11)\| ≤ 0,02 |
|---|---|---|---|---|---|
| 0,05 a 0,2 | 112.913 | 70,7 % | 0,0 % | −0,30 | 36,9 % |
| 0,2 a 0,5 | 193.361 | 42,3 % | 26,5 % | −0,01 | 70,0 % |
| 0,5 a 0,9 | 316.017 | 43,6 % | 51,4 % | +0,01 | 74,3 % |

### Paso 4: nivel B de la etapa 2 (7 tablas sin εtot × BTD, cuadros 6 a 10)

| | Píxeles | P_VOLCAT ≥ 0,5 | \|ΔP\| ≤ 0,05 | κ a 0,5 | Recuperados |
|---|---|---|---|---|---|
| Esta variante, todo | 502.234 | 27.075 | 89,4 % | 0,213 | 15,7 % |
| εtot < 0,2 | 29.674 | 494 | 75,5 % | 0,085 | 57,3 % |
| εtot 0,2 a 0,5 | 147.709 | 5.150 | 91,8 % | 0,092 | 5,6 % |
| εtot ≥ 0,5 | 324.851 | 21.431 | 89,5 % | 0,275 | 17,1 % |
| Referencia H15 (V0, N0, S0), todo | 502.234 | 27.075 | 86,9 % | 0,266 | 27,6 % |
| Regla de la etapa 2 | | | ≥ 90 % | ≥ 0,90 | ≥ 90 % |

El nivel B no mejora: acercar ε no basta mientras β(12/11) en nube tenue siga 0,3 bajo el de VOLCAT y ε conserve
±0,02 de dispersión, que en los bordes de bin de las tablas cambia de celda.

### Posterior (no decide, cuadros 1 a 5, `posterior_residuo.txt`)

Con V1, N1 y sin corregir el cielo, el residuo de ε es positivo en nube tenue (+0,012 a +0,016 entre 0,05 y 0,3)
y negativo en nube media (−0,008 entre 0,5 y 0,6). Depende además del ángulo: el exponente efectivo dividido por
cos θ vale 0,88 con θ de 20 a 28° y 1,02 con θ de 34 a 45°. Puede ser que VOLCAT use otro ángulo (por ejemplo, el
de la nube a su altura y no el del píxel) o que el ángulo esté confundido con la posición en la escena (el cielo
despejado cambia de oeste a este). No se separa con un solo caso.

## 3. La pregunta exacta para el correo a Pavolonis

1. ¿`cloud_emissivity_ch14_tot` está normalizada al nadir como 1 − (1 − ε)^cos θ? ¿Con qué ángulo (cenital del
   píxel o a la altura de la nube)?
2. La nube negra de referencia de εtot: ¿la tropopausa del GFS, el punto más frío del perfil o el nivel de la
   tropopausa calculado por GEOCAT? ¿Con la atmósfera de encima (transmitancia y emisión) o sólo B(T)?
3. El cielo despejado que entra a εtot y β: ¿`geocatRTM` tal cual? El sesgo local de 12 px
   (`use local clear bias analysis`), ¿sólo entra en la membresía y la confianza del objeto, o también corrige el
   cielo despejado de ε?
4. En nube tenue (εtot < 0,2), ¿β(12/11) se calcula de las emisividades o se reemplaza (las relaciones
   `BETA1112_FROM_BTD_BIAS_*` y `COEFF_BETA1112_TOT_FCT1` de la tabla)? Medimos nuestro β 0,30 más bajo que el
   suyo en ese tramo.

## 4. Qué cambia

- **Para H15:** el nivel B sigue sin aprobar. La causa de la diferencia de ε quedó en buena parte identificada
  (nadir), pero no la de β en nube tenue.
- **Para Chillán:** el cielo corregido no está listo. Si se usa ε propio contra el de VOLCAT, llevarlo al nadir.
- **Para la otra sesión (nube tenue):** nota en la carpeta compartida (`cielo_sesgo_hallazgo_nadir.md`); su
  comparación de β en nube tenue no depende de la normalización al nadir, la de ε sí.
- **Para el dashboard:** nada.

## 5. Archivos

- Scripts (`scripts/`): `explorar_1a5.py` (exploración previa al criterio), `gfs_punto_frio.py` (punto frío del
  GFS, corre en `venv_hdf4`), `cielo_sesgo.py` (aplica el criterio), `posterior_residuo.py` (posterior).
- Salida cruda (`resultados/`): `cielo_sesgo.json`, `cielo_sesgo_log.txt`, `posterior_residuo.txt`.
- Fuera del repo: `D:\goes_cache\lut_h15\cielo_sesgo\gfs_punto_frio.npz`. Nada de SSEC se sube al repo.

## Reproducir

```powershell
D:\goes_notas\busqueda_2026-11-20\venv_hdf4\Scripts\python.exe -I docs/own_volcat/lut_h15/cielo_sesgo/scripts/gfs_punto_frio.py
```

```powershell
python -I docs/own_volcat/lut_h15/cielo_sesgo/scripts/cielo_sesgo.py
```

```powershell
python -I docs/own_volcat/lut_h15/cielo_sesgo/scripts/posterior_residuo.py
```
