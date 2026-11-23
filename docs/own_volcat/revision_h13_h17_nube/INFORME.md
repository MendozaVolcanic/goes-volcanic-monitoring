# ¿Las líneas base de H13 y H17 cayeron en nube? Informe S19e, 23-11-2026

**Veredicto con la regla escrita antes de medir:**

- **H13 (cambio entre cuadros): sigue en pie.** Con sólo los pares en que positivo y control están despejados en
  los cuatro tiempos (30 pares, 6 jornadas), la mejor de las 18 variables llega a AUC 0,604. Eso es lo que da el azar
  en una muestra de ese tamaño (mediana de subconjuntos al azar 0,605, p95 0,679), y ninguna variable separa.
- **H17 (regla propia de calor más pluma): la conclusión física se debilita; la etapa 2 no cambia.** Contra una
  línea base de cuadros despejados, la huella VOLCAT ya no está 1,28 K más tibia que el suelo: está **0,81 K más
  fría**. No llega al umbral relajado de −1 K, y la regla sigue sin separar del fondo (POD 0,19, FAR 0,07).

Criterio: `criterio_2026-11-23.md`, commit `6ed8d38`, subido antes de leer la máscara. Salidas crudas en
`resultados\`.

## 1. Para geólogo

**La pregunta.** H23 descubrió dos cosas incómodas. Una línea base armada por percentil en un periodo nublado cae en
nube y queda fría. Y la máscara de nubes de NOAA (ACMF) marca nublada la cumbre nevada de Chillán casi siempre. En
S17 quedó la duda de si les pasó lo mismo a dos pruebas anteriores:

- **H17** comparó cada píxel contra su propia historia de los 6 días previos. Concluyó que la huella de VOLCAT
  estaba 1,3 K **más tibia** que el suelo despejado, o sea, que "se ve como suelo".
- **H13** comparó cada cuadro con pluma con el mismo minuto de otro día sin pluma y con BT11 parecida.

**Cómo se midió.** Con la misma definición de H23 y H24: una escena es despejada si al menos 80 % del terreno bajo
que rodea al volcán (10 a 30 km, bajo 1.300 m) sale despejado en la máscara de NOAA. La cumbre no se usa para
decidir, porque ahí la máscara confunde nieve con nube. Antes de confiar en la máscara se comprobó que separa algo
físico. En los mismos cuadros, el terreno bajo está 17 K más tibio en las escenas que la máscara llama despejadas
(mediana por hora; la regla pedía 3 K). Una máscara muerta o al azar no daría eso.

**H17: la base sí tenía nube, y sacarla mueve el número 2 K.** En la mediana de los 60 cuadros de evento, 62 % de
los cuadros de su línea base eran escenas no despejadas. Con sólo los cuadros despejados (al menos 5 por cuadro, de
4 días distintos en la mediana), la huella queda **0,81 K más fría** que su base, y no 1,28 K más tibia. Dos
controles muestran que el cambio viene de sacar la nube:

- con una base sólo de cuadros nublados, la huella sale 3,84 K más tibia;
- con una base del mismo tamaño elegida al azar, sale 1,19 K más tibia, casi lo mismo que H17.

Qué cambia y qué no:

- **Se cae la frase "la huella está más tibia que el suelo despejado"** (H17 §1, "la física de por qué no se ve"),
  y con ella el "1,3 K más tibia" que se repitió en `STATUS.md` y en otros informes.
- **No se cae lo central.** Con base limpia la huella se enfría menos de 1 K, sólo 5,6 % de sus píxeles pasa los
  umbrales relajados, y los píxeles de control con la misma BT11 pasan en 26 %. La pluma de esos días sigue sin
  dejar en 11 y 12 µm una señal que la distinga del resto del cuadro.
- **La regla de H17 tampoco cambia de clase.** Con base despejada detecta 19 % de los cuadros con pluma VOLCAT y da
  falsa alarma en 7 %, con un intervalo de confianza que cruza el cero. Sigue en "no separa del fondo".

**H13: el control estaba más nublado que el positivo, pero eso no rescata la señal.** Los cuadros con pluma VOLCAT
caen en escena despejada el 81 % de las veces; sus controles, el 56 %. En la mitad de los pares (37 de 72), positivo
y control estaban en cielos distintos en al menos uno de los cuatro tiempos. Aun así, al quedarse sólo con pares
despejados en los ocho cuadros, ninguna de las 18 variables de cambio separa. La mejor (el cambio de β(7,3/11) en
10 min) da 0,604, que es justo lo que se espera por azar al tomar la mejor de 18 en 30 pares.

**Una respuesta que H13 había dejado abierta.** H13 vio que en 23 de sus 26 cuadros sin control todos los días
candidatos estaban más fríos en la cumbre (3 a 10 K), y no midió si era nube o suelo. Era sobre todo nube. En 15 de
esos 26 cuadros el positivo estaba despejado, mientras que en el mismo minuto de los ±10 días sólo 20 a 40 % de las
escenas lo estaban.

**Lo que sale de paso.** VOLCAT marca sus objetos de Chillán sobre todo en cielo despejado: 81 % de los positivos de
H13 y 48 % de los cuadros de evento de H17 están en escena despejada, contra 20 % de los negativos de H17 y 20 a 40 %
del mismo minuto en otros días. Es esperable (bajo
nube no hay pluma que ver), pero tiene una consecuencia de método: **un negativo elegido sin mirar el cielo es casi
siempre un cuadro nublado**, y la falsa alarma de una regla se mide entonces en otro régimen que su detección. Leído
después de medir, sin decidir: en H17, restringida a cuadros despejados, la regla detecta 6 % con 2 % de falsa
alarma, y sigue sin separar.

**Para el dashboard: nada que cambiar.** Ninguna de las dos pruebas había llevado nada a `src/`.

## 2. Comprobaciones del instrumento

| | Pide | Medido |
|---|---|---|
| ACMF en disco para los cuadros usados | informar | H17: 1.915 de 1.916; H13: 576 de 576 |
| Pregunta 2: la máscara separa la temperatura del terreno bajo | ≥ +3 K (mediana por hora UTC) | **+16,9 K** en 17 horas (10,8 a 30,2 K) |
| Línea base roja H17 (base original) | reproducir H17 | +1,28 K, −12,52 K, POD 0,134, FAR 0,066 (idénticos) |
| Línea base roja H13 (todos los pares) | reproducir H13 | AUC máximo 0,582 (idéntico) |
| Pregunta 1, control positivo H17 (base sólo nublada menos sólo despejada, mismos 60 cuadros) | ≥ +1 K | **+4,64 K** |
| Nulo medido H17 (base al azar del mismo tamaño que la despejada) | a ≤ 0,3 K de +1,28 K | +1,19 K (0,09 K) |
| Nulo medido H13 (2.000 subconjuntos al azar de 30 pares) | se informa | máximo de las 18: mediana 0,605, p95 0,679 |

La primera corrida de `rev_h17.py` dio NaN en la pregunta 2 por un error de código mío: `np.median` sobre un cuadro
sin BT11 en el terreno bajo. Se corrigió a `nanmedian` en `rev_h17.py` y la comprobación se calculó aparte con
`rev_q2.py`, sobre los mismos cuadros. El resto de los números de esa corrida no pasa por esa línea.

## 3. Números

### 3.1 H17 (`resultados/rev_h17_resultado.txt`, `rev_q2_resultado.txt`, `rev_h17_por_cuadro.csv`)

Fracción de la base en escena no despejada (F17):

- todos los cuadros con base (1.833): mediana 0,70, p90 1,00; 41 % con F17 > 0,75;
- 60 cuadros de evento: mediana 0,62, p90 0,68; 1 de 60 con F17 > 0,75.

Los 60 tienen base despejada de ≥ 5 cuadros (no es SIN DATO). En la huella misma, la máscara da despejado sólo
11 % de los píxeles en el cuadro t y 7 % en los de la base: es la cumbre nevada.

Huella `event_idx` de los 60 cuadros de evento (768 píxeles), contra controles del mismo cuadro con BT11 ± 0,5 K
(3.835):

| Base | Candidatos huella | ΔBT11 huella | ΔBTD huella | Candidatos control | ΔBT11 control |
|---|---|---|---|---|---|
| H17 original | 1,7 % | +1,28 K | −0,19 K | 31,7 % | −12,52 K |
| **Sólo despejados (decide)** | 5,6 % | **−0,81 K** | −0,22 K | 26,4 % | −14,87 K |
| Sólo nublados (control positivo) | 0,7 % | +3,84 K | −0,30 K | 36,9 % | −8,18 K |
| Al azar, mismo tamaño (nulo) | 3,3 % | +1,19 K | −0,21 K | 30,7 % | −12,90 K |

Etapa 2, variante "decide" (−1 K, −0,5 K, compuerta de calor de 24 h):

| Base | POD | FAR | IC 95 % de POD − FAR | Clase |
|---|---|---|---|---|
| H17 original | 0,134 (127) | 0,066 (1.380) | −0,078 a 0,193 | no separa del fondo |
| **Sólo despejados (decide)** | 0,190 (121) | 0,067 (1.127) | −0,069 a 0,289 | **no separa del fondo** |
| Al azar | 0,124 (121) | 0,075 (1.127) | −0,090 a 0,163 | no separa del fondo |
| Lectura post hoc: despejada y sólo cuadros t despejados | 0,060 (83) | 0,020 (253) | −0,029 a 0,157 | no decide |

### 3.2 H13 (`resultados/rev_h13_resultado.txt`)

- Escena despejada en t: positivos 0,81, controles 0,56. Fracción del terreno bajo despejada en t (mediana): 0,99
  y 0,85.
- F13, pares con cielos distintos en algún tiempo: 37 de 72 (0,51).
- Pares "despejado" (los ocho cuadros despejados): 30, en 6 jornadas (26 de día, 4 de noche). Cumple el mínimo de
  H13 (30 pares, 4 jornadas).
- AUC máximo de las 18 variables: **0,604** (Δ1 β(7,3/11), IC [0,482; 0,668], anillo 0,396). Le siguen Δ3
  β(7,3/11) con 0,568, y Δ3 BT11 con 0,531. Ninguna separa.
- Con la regla original de H13 aplicada a este subconjunto saldría "no concluyente", porque 0,604 pasa 0,60 por
  0,004. El criterio de esta revisión lo previó: el máximo de 18 en una muestra chica sube solo. Con el nulo medido
  (mediana 0,605), 0,604 es exactamente lo esperado por azar, y por eso la regla escrita antes lo lee "sigue en pie".
- Lectura, pares "mismo cielo" (35, 9 jornadas): máximo 0,565 (falsa con la regla de H13), dentro del p95 al azar
  (0,662).
- Los 26 sin control: el positivo despejado en 15. En el mismo minuto de los ±10 días hay 20 a 40 % de escenas
  despejadas (por cuadro, en `rev_h13_resultado.txt`).

## 4. Lo que podría estar equivocado

- **"Escena despejada" mira el terreno bajo, no la cumbre.** Una nube orográfica pegada a la cumbre con el valle
  despejado pasa como despejada. Es lo más probable detrás de que el tamizado de §3.1 del criterio fallara: con 38 %
  de la base despejada, el percentil 75 debería haber caído en lo despejado (1 de 60 cuadros sospechosos), y aun así
  sacar la nube movió la huella 2,1 K. Si quedó nube en la cumbre dentro de la base "despejada", el −0,81 K está
  todavía algo sesgado hacia lo tibio. Hacia lo frío no puede estarlo por esta causa. SOSPECHA, no medida: la máscara
  no sirve en la cumbre nevada para comprobarlo.
- **La regla del 75 % del criterio era un razonamiento, no una medición, y no anticipó el efecto.** Decidió la
  remedición, como estaba escrito; el tamizado queda informado y no se usa para nada.
- **La remedición de H17 sólo cambia la base, no los controles de píxel ni la compuerta de calor.** Los controles
  pareados por BT11 en el cuadro t siguen siendo mayormente nube (ΔBT11 −14,9 K), así que la comparación huella
  contra control sigue mezclando suelo con nube. Eso favorece a la huella y no cambia la lectura.
- **En H13 la muestra despejada es de día casi entera** (26 de 30). La noche despejada no queda evaluada.
- Mismos límites de H13 y H17 que sus informes declaran (ventana de 83 × 94, Chillán solo, ABI a 10 min).

## 5. Qué hacer con esto (para S19, que actualiza los documentos)

1. En `STATUS.md` y en `POR_QUE_VOLCAT_VE_Y_NOSOTROS_NO.md`, cambiar "la huella está 1,3 K más tibia que su base
   despejada" por "contra una base de cuadros despejados según NOAA, la huella está 0,8 K más fría que su suelo, sin
   pasar el umbral relajado de −1 K; con la base original de H17, que tenía 62 % de cuadros nublados, salía 1,3 K más
   tibia".
2. H13 queda falsada como estaba. Agregar que los controles estaban más nublados que los positivos (56 % contra 81 %
   despejados) y que con pares despejados tampoco separa.
3. **Regla de método** (para `GUIA_MAESTRA_AUDITORIAS.md` §3b o §7, lo decide S19): cuando la verdad (VOLCAT) sólo
   marca en cielo despejado, **el negativo y la línea base tienen que elegirse en el mismo cielo**. Si no, el negativo
   es un cuadro nublado y la base cae en nube, y las dos cosas mueven el resultado más que la pluma.

## 6. Archivos

- Criterio: `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\Goes\docs\own_volcat\revision_h13_h17_nube\criterio_2026-11-23.md`
- Scripts (`...\revision_h13_h17_nube\scripts\`): `rev_comun.py` (máscara, terreno bajo y cumbre de H23), `rev_h17.py`
  (reusa sin cambios las funciones de `h17_pluma.py`), `rev_q2.py` (pregunta 2 y lectura post hoc), `rev_h13.py`
  (funciones de AUC y veredicto copiadas sin cambios de `h13_analisis.py`).
- Resultados (`...\revision_h13_h17_nube\resultados\`): `rev_h17_resultado.txt`, `rev_h17_por_cuadro.csv`,
  `rev_q2_resultado.txt`, `rev_h13_resultado.txt`. Sin posiciones de huella ni datos de SSEC.
- Fuera del repo: `D:\goes_notas\s19\revision_h13_h17\` (`rev_h17_pixeles.pkl`, `rev_h17.log`, `rev_h13.log`). Sólo
  lectura: ACMF de `D:\goes_notas\s17\h23\acm\` y `D:\goes_notas\s18\h24\acm\`, cachés de H13 y H17 en
  `D:\goes_cache\`. No se bajó nada.
- Reproducir, desde `docs\own_volcat\revision_h13_h17_nube\scripts\` (H17 tarda unos 80 min):

```powershell
python -I rev_h17.py
```

```powershell
python -I rev_q2.py
```

```powershell
python -I rev_h13.py
```

No se tocaron los informes de H13 ni de H17, ni `STATUS.md`, ni `POR_QUE_VOLCAT_VE_Y_NOSOTROS_NO.md`, ni `src/`.
