# Cielo despejado y nube negra de VOLCAT en εtot y β (H15, nivel B). Informe, 21-11-2026

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
