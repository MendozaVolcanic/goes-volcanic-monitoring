# H16: la etapa de objeto de VOLCAT sobre la huella de Nevados de Chillán. Informe, 21-11-2026

**Veredicto (regla del criterio): no separa.** Reprodujimos la probabilidad de objeto de VOLCAT con su tabla pública
y la validamos contra lo que VOLCAT publica en Mauna Loa (error mediano 0,03 décadas en las odds). Aplicada a los 60
cuadros de Chillán, la huella nunca pasa de 0,002 de probabilidad de objeto (mediana 2 × 10⁻¹⁰); VOLCAT pide 0,8.
Lo que publica Chillán no es la probabilidad de objeto: sus archivos de evento dicen que entra por otra vía,
`ASHPLUMEPUFF` (49 de 60 cuadros) y `VCB` (11 de 60), y tres de los cuatro eventos parten con actividad térmica
VOLCAT de 10 MW o más en el cráter en ese mismo momento.

Criterio escrito y subido antes de validar y antes de Chillán:
`C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\Goes\docs\own_volcat\h16_objeto\criterio_2026-11-21.md`
(commits 22c46b1 y fcbe3a7 en la rama `claude/h16-objeto-volcat-24a78e`; mientras no se fusione, en
`C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\Goes\.claude\worktrees\h16-objeto-volcat-24a78e\docs\own_volcat\h16_objeto\`).

## 1. Para geólogo

**Qué es la etapa de objeto.** VOLCAT no decide píxel por píxel. Primero junta píxeles vecinos con alguna firma en
un "objeto" y después se pregunta si ese conjunto, como un todo, se parece más a una nube de ceniza o a una nube
meteorológica. La idea física es la del cirro tenue: un píxel aislado no se distingue del cielo despejado, pero un
manchón coherente con la misma firma débil sí. Para eso VOLCAT clasifica cada píxel del objeto en casillas
(combinaciones de emisividad a 11 µm y de las razones β entre canales), mira qué casillas ocupan más área dentro del
objeto y compara esa mezcla con la de miles de nubes de ceniza y de nubes comunes vistas por MODIS. El resultado es
una probabilidad de objeto. Según SECO Parte 2 (Tabla 4), un objeto se publica si esa probabilidad, o la mediana de
sus píxeles, supera 80 %, también en las filas que relajan el tamaño junto a un volcán.

**Qué se hizo.** La tabla de objeto de VOLCAT es pública, pero no dice cómo se arma una "muestra". El caso de prueba
de Mauna Loa (noviembre 2022) trae, por objeto, los dos términos que VOLCAT multiplica (ceniza y nube) y su
probabilidad final. Con los objetos de un píxel se descifró la mecánica exacta (qué casilla, qué rango, qué tablas
entran) y con los objetos más grandes de la segunda mitad del caso se validó: en 126 objetos de 2 a 117 píxeles el
error mediano es 0,03 décadas y el 97 % queda dentro de una década. Después se aplicó a Chillán: la huella que VOLCAT
publicó en cada cuadro como un objeto, contra cinco objetos de control del mismo tamaño, armados con píxeles del
mismo cuadro y la misma temperatura a 11 µm.

**Lo que salió.** A nivel de objeto la huella sí se ve "más ceniza" que sus controles: le gana al control en el 78 %
de las comparaciones, y su evidencia acumulada es unas 6 décadas menos mala (mediana de la razón ceniza/nube 10⁻⁶·⁷
contra 10⁻¹²·⁹). Lo que la acerca a ceniza es la razón β(12/11) de 0,87 a 0,91, que en las tablas es típica de
ceniza tenue. Pero para publicar hace falta que esa razón llegue a unas 10³·⁶ a favor, y la huella queda unos diez
órdenes de magnitud abajo. No es un umbral que se roce: el objeto de Chillán, mirado como VOLCAT mira objetos en el
infrarrojo, es una nube común con un leve sesgo hacia ceniza.

**Por qué queda tan abajo (la física).** Dos rasgos la hunden:
1. **La rugosidad térmica de la cumbre.** La tabla de desviación estándar de BT11 (en 3 × 3 píxeles) resta 2,0
   décadas en la huella y apenas 0,2 en los controles. Una nube de ceniza extensa es térmicamente lisa; un píxel junto
   al cráter mezcla roca fría de altura, nieve, valles y el borde de una pluma de 1 o 2 píxeles de ancho, y eso da
   BT11 muy variable de un píxel al vecino. Para la tabla, entrenada con nubes grandes, eso es firma de nube
   fragmentada o de terreno. Es justo lo que tiene una emisión chica pegada a una cumbre de más de 3.000 m.
2. **Objetos chicos y tenues.** Con 1 a 67 píxeles y emisividad mediana 0,13, el objeto ocupa pocas casillas y en la
   clase de área más baja. La probabilidad de objeto suma evidencia por casilla: con pocas casillas no hay de dónde
   juntar las diez décadas que faltan.

**Entonces, ¿por qué VOLCAT la publica?** Sus archivos de evento lo dicen: 49 de los 60 cuadros son
`ASHPLUMEPUFF` y 11 son `VCB` (crecimiento vertical). Ninguno sale por la selección básica de objeto que acabamos
de reproducir. La vía "pluma/puff" está descrita en la presentación CDR de VOLCAT (2022) como una combinación de
aprendizaje automático e ingeniería de rasgos, con dimensión temporal, pensada para "emisiones de ceniza de muy
pocos píxeles" atribuibles a un volcán. La misma presentación dice que, cuando VOLCAT observa actividad térmica
intensa en un volcán, ajusta solo sus umbrales de detección de erupción para ser más sensible. Los archivos de
Chillán calzan con eso: en el primer cuadro de los eventos del 13-11 19:00, 14-11 12:40 y 18-11 10:10, el campo
`volcano_thermal_activity` marca 0,0 días desde la última detección de 10 MW o más (el del 14-11 16:30 no lo marca).

**El punto caliente, contado como geólogo.** El canal de 3,9 µm es mucho más sensible que el de 11 µm a una fuente
muy caliente que ocupa una fracción mínima del píxel: por la ley de Planck, una superficie a 1.000 K que cubre una
diezmilésima de un píxel a 270 K sube la temperatura de brillo a 3,9 µm en unos 25 K y la de 11 µm en 0,2 K (cálculo
de cuerpo negro, sin atmósfera). Por eso VOLCAT
mide la potencia radiativa volcánica (VRP) en ese canal. La lógica de usarla como permiso para bajar umbrales es
volcanológica, no espectral: si el conducto está caliente y abierto, una nube chica que sale del cráter tiene mucha
más probabilidad de ser una emisión que una nube orográfica. No mira la pluma; cambia cuánto se le exige a la pluma.
La tabla de objeto no tiene eje de 3,9 µm: los umbrales `BTD3911_HOT_SPOT_MIN/MAX` (15 y 500 K) de su cabecera son
del detector térmico, que corre aparte (producto HOTOBJ).

**Qué significa para nuestro dashboard.** La parte pública de VOLCAT (probabilidad por píxel, PR 79, y probabilidad
de objeto, este informe) ya está reproducida y validada, y ninguna de las dos ve estas plumas. Lo que las ve es la vía
`ASHPLUMEPUFF`, cuyo clasificador no es público, gatillada o relajada por calor en el cráter. Nuestro dashboard puede
imitar la idea, no el algoritmo: (a) medir calor en el cráter a 3,9 µm con la sensibilidad de VOLCAT (el FDCF de NOAA
es menos sensible; en H9 dio 0 % en estos cuadros mientras VOLCAT marcaba 10 MW; VRP Chile ya hace este cálculo con
MODIS/VIIRS, pero en Goes no se usa VIIRS); (b) con calor presente, mirar objetos chicos anclados al cráter con
criterios relajados. Eso sería una regla nuestra, que habría que validar contra VOLCAT antes de mostrarla, y no una
copia. Lo que falta para reproducir lo de ellos es exactamente lo que hay que preguntarle a Pavolonis (§6).

## 2. Lectura: qué es LEÍDO y qué INFERIDO

| Afirmación | Fuente | Estado |
|---|---|---|
| Bayes ingenuo por objeto, prior 0,1 %; 10 casillas de más área por tabla; densidad casilla × área; casilla con εtot < 0,03 vale 1 | SECO Parte 2 §4.2.1 y §4.2.2 | LEÍDO |
| Tablas por modo (día, noche, IR) para ABI | SECO Parte 2 Tabla 1 | LEÍDO |
| `Feature_Prob = 0,001·T_c / (0,001·T_c + 0,999·T_n)` | ASHOBJ Mauna Loa, 1.948 objetos de los 10 cuadros (versión completa e IR), diferencia 0,0 | LEÍDO y VERIFICADO |
| El tercer eje de la tabla es el rango de la casilla (1.ª a 10.ª por área) | SECO 2 + coincidencia exacta en rango 1 | VERIFICADO |
| Casilla = iβ + 7(iβ85 + 5 iε) en las tablas de 8,5 µm y 7,3 µm; iε + 4 i(otra) en las de dos variables | pares de objetos de un píxel, error 0 | VERIFICADO |
| La tabla "β opaco × β(8,5) opaco" usa β(12/11) **total** en su primer eje | 63 de 63 casos que fallaban se arreglan así, 0 con β opaco | VERIFICADO (rareza de VOLCAT) |
| BTD(11-12) no entra en el término IR; β(7,3/11) entra si existe | coincidencia exacta 98,3 % con esto | VERIFICADO |
| Desviación de BT11 = 3 × 3 sobre BT11 | coincide en ~64 % de los píxeles; el resto no se reproduce | INFERIDO, parcial |
| Clase de área en km² | `pixel_area` de VOLCAT en km² y coincidencia exacta | VERIFICADO |
| Criterios de alerta pluma/puff (mínimo 1 píxel, umbrales de ruido 0,25, εtot mediana ≤ 0,5, contraste opción 2) | logs `geocatASHOBJ.*.log` de Mauna Loa | LEÍDO (sólo los parámetros; el método no) |
| Pluma/puff usa aprendizaje automático y tiempo; la actividad térmica relaja umbrales | CDR VOLCAT 2022, diapositivas 80 y 82 | LEÍDO (sin detalle) |

## 3. Validación en Mauna Loa (cuadros 6 a 10)

| Conjunto | n | Mediana \|Δ log10 odds\| | Dentro de 1 década | Exacto (< 0,01) | Pide |
|---|---|---|---|---|---|
| Objetos de ≥ 2 píxeles | 126 | 0,026 | 96,8 % | 47,6 % | ≤ 0,3 y ≥ 80 % → **valida** |
| Objetos de 1 píxel (informa) | 434 | 0,000 | 98,8 % | 77,6 % | |
| Elección, cuadros 1 a 5 (≥ 2 px) | 324 | 0,000 | 97,2 % | 55,9 % | |

Variante elegida en los cuadros 1 a 5: desviación de BT11 3 × 3 con ddof 0, bordes tal cual, desempate por casilla
menor, β(7,3/11) cuando existe. En Mauna Loa sólo 1 objeto de los cuadros 6 a 10 pasa 0,5 según VOLCAT (0,545; el
nuestro da 0,484), así que la concordancia sobre 0,5 no decide. Lo que no es exacto viene casi todo de la desviación de
BT11. Fuente: `resultados/validacion_mauna_loa.json` y `resultados/validacion_objetos.csv`.

## 4. Chillán (banda S0 decide)

| Banda | F_h (P ≥ 0,8) | F_c | AUC por cuadro | IC 95 % AUC | P mediana huella | P máxima huella | Categoría |
|---|---|---|---|---|---|---|---|
| **S0** | 0,000 | 0,000 | 0,783 | 0,706 a 0,982 | 1,9e-10 | 0,0022 | **no separa** |
| S0, desviación BT11 en bin 0 | 0,000 | 0,000 | 0,873 | 0,705 a 0,988 | 2,9e-6 | 0,0031 | no separa |
| S1 (−0,86 K) | 0,000 | 0,000 | 0,280 | 0,163 a 0,375 | 1,6e-20 | 1,3e-6 | no separa |
| S2 (más frío junto a nube espesa) | 0,000 | 0,000 | 0,457 | 0,200 a 0,567 | 8,9e-15 | 4,3e-4 | no separa |

60 cuadros (11 del 13-11, 7 del 14-11 mañana, 41 del 14-11 tarde, 1 del 18-11), cinco controles por cuadro.
"No separa" sale por F_h = 0. El AUC de S0 (0,78) dice que la huella queda sobre su control en el ranking de objeto,
pero en probabilidades del orden de 10⁻¹⁰; con el cielo despejado más frío (S1, S2) hasta eso se pierde.

Aporte por tabla en S0 (mediana del log10 de la razón ceniza/nube sumada sobre las casillas del objeto):

| Tabla | Huella | Control |
|---|---|---|
| εtot × β(12/11) | −0,09 | −2,14 |
| εtot × β(12/11) × β(7,3/11) | −0,24 | −2,33 |
| εtot × β(12/11) × β(8,5/11) opaco | −0,50 | −3,15 |
| εtot × β(12/11) × β(8,5/11) | −0,54 | −2,58 |
| εtot × β opaco | −0,96 | −1,04 |
| εtot × desviación de BT11 | **−2,02** | −0,22 |
| Total (sin prior) | −6,7 | −12,9 |

Fuente: `resultados/chillan_metricas.txt`, `chillan_metricas.json`, `chillan_objetos.csv`, `chillan_tablas.csv`.

## 5. Límites

- **Día.** Casi todos los cuadros de Chillán son de día y VOLCAT, de día, agrega tablas con 0,65 y 3,9 µm. No las
  calculamos (la cadena de la etapa 3 no trae esas bandas) ni podríamos validarlas (Mauna Loa es de noche). A nivel de
  píxel los canales solares no separaban (AUC 0,50 pareado, 18-11), así que es poco probable que sumen diez décadas,
  pero no está medido.
- **Desviación de BT11.** Reproducimos ~64 % de los bins de VOLCAT. Es justo la tabla que más hunde la huella; con el
  supuesto más favorable (bin 0, mínima variabilidad) la huella sube a 0,003 como máximo. No cambia el veredicto.
- **Objeto huella.** Usamos como objeto los píxeles que VOLCAT publicó (`event_idx`). El objeto con que VOLCAT
  calculó pudo ser algo distinto; con una diferencia de diez décadas eso no alcanza a cambiar la conclusión.
- **Mauna Loa es una nube espesa y alta;** la validación prueba la mecánica de la tabla, no su comportamiento en
  nubes tenues de cumbre. Para eso no hay verdad pública.

## 6. Qué sigue

1. **Escribir a Pavolonis (decisión de Nicolás, lunes 23-11).** La pregunta ya es precisa: cómo decide la vía
   `ASHPLUMEPUFF` (la "weak plume option 4" de su configuración) y cómo la actividad térmica (VRP ≥ 10 MW) relaja sus
   umbrales para objetos de pocos píxeles junto a un volcán. Todo lo público (píxel, objeto, Tabla 4) ya lo
   reprodujimos y no ve estas plumas.
2. **Si se quiere algo propio:** probar una regla "calor en el cráter + objeto chico anclado" contra la detección
   VOLCAT de Chillán, con criterio escrito antes. Requiere primero una VRP a 3,9 µm de ABI más sensible que el FDCF.

## 7. Archivos

- Scripts: `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\Goes\docs\own_volcat\h16_objeto\scripts\`
  (`h16_objeto.py` motor, `h16_validar.py` Mauna Loa, `h16_chillan.py`, `h16_medir.py`).
- Exploración y extracción (HDF4, fuera del repo): `D:\goes_cache\h16_objeto\scripts\` (`h16_extraer.py`,
  `h16_extraer_area.py`, `explora*.py`) (copias de los dos extractores en scripts/ del repo) y sus salidas en `D:\goes_cache\h16_objeto\ml\`.
- Tabla de SSEC y archivos de evento de Chillán: no se suben (licencia); la tabla exportada está en
  `D:\goes_cache\h16_objeto\ml\lut_objeto.npz`.
