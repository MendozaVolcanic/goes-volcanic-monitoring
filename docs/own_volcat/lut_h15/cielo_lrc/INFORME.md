# Centro radiativo local (LRC) y vecindad en el ε(11 µm) de VOLCAT. Informe, 21-11-2026

Frente cielo_lrc de H15 nivel B (Mauna Loa, GOES-17, 28-11-2022, noche, mar). Sigue a
`C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\Goes\.claude\worktrees\h15-lrc\docs\own_volcat\lut_h15\cielo_sesgo\INFORME.md`
(vueltas 1 a 6).

## Veredicto

**Ninguna cantidad del LRC ni de la vecindad explica el ε(11) de VOLCAT en nube tenue.** Se probaron las cuatro
familias del encargo en los cuadros 1 a 5; ninguna aplana el desfase ni su gradiente con la distancia a la nube
espesa, y ninguna sigue la variación píxel a píxel del exceso. Por el método vinculante se para aquí: **no se
escribió criterio, no se tocaron los cuadros 6 a 10 y no se corrió el nivel B**, porque no había candidata que
validar. Eso es el resultado.

## Para geólogo

**El fenómeno.** En una nube muy tenue el satélite ve casi todo el calor del mar a través de ella, así que la
emisividad que se calcula depende casi entera del "cielo despejado" que uno espera ver sin nube. Para reproducir el
ε(11 µm) que publica VOLCAT hay que suponer un mar ~0,9 K más frío que el que da su propio modelo de transferencia
radiativa (`geocatRTM`), y ~1,6 K más frío junto a la nube espesa (`cielo_sesgo/resultados/vuelta5_forma.txt`). En 12 µm no hace falta ningún ajuste. La vuelta 5
ya había mostrado que el desfase tiene forma de "efecto de vecindad de la nube".

**La pista.** VOLCAT calcula centros radiativos locales: desde cada píxel tenue sube por la emisividad hasta el
centro opaco de su nube (Pavolonis 2010; ATBD de la máscara de nubes de GOES-R, sección LRC, que da la receta de
VOLCAT: emisividad al nadir con mediana 3 × 3 y parada en 0,7). Si VOLCAT tomara del LRC o de los vecinos algo que
entra a la emisividad de un píxel tenue, explicaría por qué el desfase crece junto a la nube espesa.

**Qué se probó.** Primero, qué publica VOLCAT del LRC: una sola variable, `ref_rat_nir_lrc`, que es una razón de
reflectancias del infrarrojo cercano y por lo tanto vale relleno de noche (0 píxeles válidos en los 10 cuadros). No
hay índices del LRC ni ε del LRC en los archivos. Así que el LRC se reconstruyó con la receta del ATBD, y se probaron
diez variantes:

| Familia | Variante | Signo esperado | Qué pasó |
|---|---|---|---|
| (a) cielo o temperatura del LRC | cielo despejado de 11 µm tomado en el LRC | correcto | no cambia nada: el cielo despejado del modelo es suave a esa escala (el LRC está a 4 px de mediana) |
| | nube negra = BT del LRC | al revés | el LRC es más tibio que el punto frío del GFS: sube ε en +0,41 |
| (b) ε del LRC propagado | ε del LRC | al revés | por construcción ε(LRC) ≥ ε(píxel): sube ε en +0,10 |
| (c) BT máxima vecina como observación | máxima 3 × 3 y 5 × 5 | correcto | se pasa de largo, sobre todo junto a la nube: invierte el gradiente |
| (d) vecindad suavizada o despejados vecinos | mediana 3 × 3 de ε | neutro | empeora junto a la nube |
| | cielo despejado suavizado 25 × 25 | correcto | no cambia nada |
| | cielo despejado desde los despejados de VOLCAT a 12 px | correcto | casi nada (ya descartado en cielo_sesgo, repetido como referencia) |
| | cielo despejado = píxel más tibio en 21 × 21 (NWC del ACM) | correcto | lejos de la nube casi calza, junto a ella se pasa de largo y en 0,2 a 0,5 destroza ε |

Además se midió si alguna variante **sigue** el exceso píxel a píxel (si una explicara el fenómeno, el exceso
crecería uno a uno con lo que ella cambia). Ninguna: la correlación más alta es 0,24 y la pendiente 0,04.

**Un techo útil.** Incluso con el mejor cielo despejado constante (−0,86 K en 11 µm, medido lejos de la nube espesa
en estos mismos cuadros), sólo 73 % de la nube tenue de 0,05 a 0,2 cae dentro de 0,01, y 42 % de la de 0,2 a 0,5. El
umbral pedido es 80 %. O sea: aun conociendo el desfase medio, queda una parte que varía píxel a píxel y que ninguna
cantidad de vecindad sigue.

**Qué significa.** El efecto de vecindad que se ve en el mapa no sale del LRC ni de un filtro espacial simple sobre
la BT o el cielo despejado. Lo que falta es la receta del cielo despejado de 11 µm que entra a εtot dentro de
GEOCAT, y no la encontramos en los archivos del caso, en la configuración pública de VOLCAT ni en los ATBD y papers revisados (búsqueda de "LRC", "radiative center", "warmest", "median filter" y ajustes de cielo despejado). Esto refuerza la pregunta para el correo al
autor (la de la vuelta 5 del frente cielo_sesgo), con dos candidatos menos.

**Para Chillán.** Sin esa receta, nuestro ε(11) de una pluma tenue junto a nubes saldrá más alto que el de VOLCAT y,
por la sensibilidad de la vuelta 3 de cielo_sesgo, más "de ceniza". La pieza sigue abierta.

## Números

Todos de los cuadros 1 a 5 (09:16 a 09:36 UTC). Nube tenue = εtot de VOLCAT entre 0,05 y 0,3 (151.349 píxeles con
desfase calculable). Nube espesa = εtot ≥ 0,5. Base = ε al nadir 1 − (1 − ε)^cos θ, nube negra en el punto frío del
GFS, cielo despejado de `geocatRTM` (V1, N1, S0 de cielo_sesgo).

### Variables LRC publicadas (`resultados/lrc_hdf.json`, 10 cuadros)

Única variable con "lrc" en el nombre en `geocatDIAGS1`: `vcat_ashdet_pix_2_7_10_11_13_14_15_ref_rat_nir_lrc`, 0
píxeles válidos en los 10 cuadros (noche). En `geocatASHOBJ` sólo hay latitud, longitud y altura del centro
radiativo **por objeto**, y la vuelta 4 de cielo_sesgo mostró que 99,6 % de la nube tenue está fuera de los objetos.

### LRC reconstruido

Filtro de gradiente (subida al vecino mayor de 8) sobre nuestro ε nadir con mediana 3 × 3, parada 0,7, válido en
(0, 1). En nube tenue, distancia al LRC p5/p50/p95 = 1,0 / 4,1 / 11,4 px; 3,3 % son su propio LRC
(`resultados/lrc_explorar_1a5.json`).

### Δε = nuestro − VOLCAT (`resultados/lrc_explorar_1a5.json`)

| Variante | ε 0,05 a 0,2: dentro de 0,01 | Δε mediana | ε 0,2 a 0,5: dentro de 0,01 | Δε mediana |
|---|---|---|---|---|
| base | 36,4 % | +0,0126 | 40,9 % | +0,0036 |
| a_lrc_clr | 37,8 % | +0,0124 | 39,1 % | +0,0037 |
| a_lrc_tcld | 0,0 % | +0,406 | 0,0 % | +0,311 |
| b_lrc_eps | 5,1 % | +0,095 | 4,8 % | +0,134 |
| c_max3 | 33,6 % | −0,0148 | 11,6 % | −0,037 |
| c_max5 | 19,5 % | −0,031 | 5,5 % | −0,064 |
| d_med3 | 33,6 % | +0,0123 | 33,1 % | +0,0027 |
| d_clr_suave | 37,0 % | +0,0126 | 39,3 % | +0,0037 |
| d_clr_vec | 41,3 % | +0,0116 | 41,1 % | +0,0035 |
| d_nwc21 | 37,9 % | −0,0036 | 5,8 % | −0,133 |
| d_nwc21_min | 43,2 % | −0,0040 | 6,0 % | −0,133 |

Gradiente: Δε mediana en nube tenue (0,05 a 0,3) por distancia a nube espesa, en px.

| Variante | 0 a 2 | 2 a 5 | 5 a 10 | 10 a 20 | > 20 |
|---|---|---|---|---|---|
| base | +0,0185 | +0,0180 | +0,0159 | +0,0137 | +0,0121 |
| a_lrc_clr | +0,0186 | +0,0182 | +0,0156 | +0,0131 | +0,0120 |
| c_max3 | −0,058 | −0,031 | −0,025 | −0,021 | −0,015 |
| d_med3 | +0,041 | +0,030 | +0,019 | +0,013 | +0,011 |
| d_clr_vec | +0,0184 | +0,0179 | +0,0157 | +0,0134 | +0,0108 |
| d_nwc21 | −0,054 | −0,057 | −0,048 | −0,022 | +0,0018 |

(Las filas que faltan están en el JSON; no cambian la lectura.)

### Exceso píxel a píxel (`resultados/lrc_explorar_1a5_b.json`)

Regresión del exceso (nuestro − VOLCAT, mediana +0,0133) sobre lo que cambia cada variante (nuestro − variante), en
los 151.349 píxeles tenues:

| Variante | ρ Spearman | Pendiente | Cambio mediano |
|---|---|---|---|
| a_lrc_clr | +0,003 | −0,02 | 0,000 |
| c_max3 | +0,064 | +0,044 | +0,030 |
| c_max5 | +0,060 | +0,032 | +0,048 |
| d_med3 | −0,048 | −0,016 | 0,000 |
| d_clr_suave | +0,046 | +0,029 | 0,000 |
| d_clr_vec | −0,099 | −0,34 | 0,000 |
| d_nwc21 | +0,238 | +0,038 | +0,022 |
| d_nwc21_min | +0,237 | +0,038 | +0,022 |

### Techo con cielo despejado constante (`resultados/lrc_explorar_1a5_b.json`)

Desfase aplicado: −0,862 K en C14 (mediana del desfase implícito en nube tenue a más de 20 px de nube espesa, igual
al −0,86 K de la vuelta 5 de cielo_sesgo). ε 0,05 a 0,2: 73,5 % dentro de 0,01, Δε mediana +0,0005. ε 0,2 a 0,5:
42,0 %, −0,0047. Gradiente residual: +0,0087 (0 a 2 px), +0,0078 (2 a 5), +0,0052 (5 a 10), +0,0023 (10 a 20),
0,0000 (> 20).

## Por qué no hubo criterio ni validación

El método pedía commitear un criterio sólo si una candidata daba una predicción numérica que aplanara el desfase y
su gradiente. Las de signo correcto o no mueven nada (a_lrc_clr, d_clr_suave, d_clr_vec), o se pasan de largo e
invierten el gradiente (c_max3, c_max5, d_nwc21). Las de LRC que mueven mucho tienen el signo al revés (a_lrc_tcld,
b_lrc_eps). Ninguna sigue el exceso píxel a píxel. Los cuadros 6 a 10 quedan intactos para una próxima candidata.

## Archivos

Scripts (`C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\Goes\.claude\worktrees\h15-lrc\docs\own_volcat\lut_h15\cielo_lrc\scripts\`):
`lrc_hdf.py` (venv_hdf4; inventario de `geocatDIAGS1`, campos 2D a `D:\goes_cache\cielo_lrc\diags_extra_<hora>.npz`),
`comun.py` (LRC por filtro de gradiente y ε recalculado), `lrc_explorar_1a5.py`, `lrc_explorar_1a5_b.py`. Las reglas
del frente 1 (`nt_regla.py`, commit af0e8ca) se exportaron a `D:\goes_cache\cielo_lrc\nt\` y no se copiaron al repo.
Textos de los ATBD y papers usados: `D:\goes_cache\cielo_lrc\txt\` (la receta del LRC está en
`Heidinger_2012_GOESR_ACM_ATBD_v3.0.txt`, sección 9 y tabla 1; el filtro de mediana de la detección de ceniza vale 0
en `volcat_ash_detection_GOESR.config`, línea 14, y por eso d_med3 era candidata débil).

```powershell
D:\goes_notas\busqueda_2026-11-20\venv_hdf4\Scripts\python.exe -I docs/own_volcat/lut_h15/cielo_lrc/scripts/lrc_hdf.py
python -I docs/own_volcat/lut_h15/cielo_lrc/scripts/lrc_explorar_1a5.py
python -I docs/own_volcat/lut_h15/cielo_lrc/scripts/lrc_explorar_1a5_b.py
```
