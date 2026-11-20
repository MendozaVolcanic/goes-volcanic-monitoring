# H13: el cambio entre cuadros consecutivos de 10 min. Informe, 20-11-2026

Criterio commiteado antes del primer número: `criterio_H13_2026-11-20.md` (commit def9a2c, rama
`claude/temporal-h13`, subido a GitHub antes de medir). Salida cruda en `resultados/`:
`h13_resultado.txt` (principal y sensibilidades) y `h13_diag_sin_control.txt` (diagnóstico posterior de los cuadros sin control). Scripts en `scripts/`.

## 1. Para geólogo

**La pregunta.** VOLCAT dibuja plumas chicas de gas y ceniza en Nevados de Chillán que nuestro infrarrojo no
distingue del cráter sin pluma cuando se mira un solo cuadro (H3, β73, H11, etapa 2). La presentación CDR de
VOLCAT de 2022 nombra un único mecanismo para emisiones de "muy pocos píxeles" con ABI: la dimensión
temporal. La idea física es simple. El cráter sin pluma tiene una firma propia y estable (terreno, nieve,
error del cielo modelado en la cumbre) que se resta sola si se compara un cuadro con el anterior; una pluma
que sale, en cambio, debería enfriar el 11 µm, subir la emisividad y mover las razones β en minutos.

**Qué se hizo.** Se bajaron las secuencias completas de 10 min de los 12 tramos con pluma VOLCAT anclada al
cráter (21-10 al 14-11, incluidos 28-10 tarde y noche, 29-10, 08-11, 10-11 y 14-11), desde una hora antes
hasta una hora después, y la historia de 30 min de todos los días candidatos a control (1.527 escenas por
ventana en total). En cada píxel se midió cuánto cambiaron BT11, BTD(11−12), la emisividad ε(11) y las razones
β(12/11), β(8,5/11) y β(7,3/11) respecto del cuadro anterior y de la mediana de los tres anteriores, y si el
cambio venía repitiéndose en el mismo sentido (18 variables). Se comparó la huella VOLCAT con el mismo píxel,
a la misma hora, en un día sin pluma con BT11 parecido (72 pares en 9 jornadas).

**Resultado: H13 se falsa.** Ninguna de las 18 variables de cambio separa la pluma del mismo lugar sin pluma.
La mejor llega a AUC 0,58 (0,5 es azar; la vara pide 0,70 y la falsación es no llegar a 0,60), y en el
anillo sin ceniza alrededor da casi lo mismo (0,54 a 0,55), o sea, lo poco que hay es del día y no de la
pluma. Con el pareo hecho media hora antes (para no favorecer al enfriamiento) la mejor baja a 0,52. Los
cambios que produce la pluma en 10 a 30 min son del mismo tamaño que los que ocurren solos en el cráter a esa
hora: respecto de la mediana de los tres cuadros anteriores, BT11 baja 0,43 K con pluma y 0,29 K sin pluma
(medianas), y la emisividad ε(11) cambia menos de 0,005 en la mediana de los dos.

**Dos lecturas que salen de aquí.**
1. Lo temporal no rescata lo que lo espectral no ve. Si la pluma no deja una marca IR distinguible en un
   cuadro, tampoco la deja como diferencia entre dos cuadros, porque la diferencia la hereda. Con ABI a 2 km y
   cada 10 min, estas plumas tibias y delgadas no tienen señal propia ni quieta ni en movimiento.
2. Los cuadros con pluma VOLCAT caen en condiciones más tibias que los días sin pluma a la misma hora: en 23
   de los 26 cuadros que quedaron sin control, **todos** los días candidatos estaban más fríos en la cumbre
   (de 3 a 10 K), sobre todo la tarde y la noche del 14-11 y del 08-11. No se midió si eso es cielo más
   despejado o suelo más tibio; sí calza con que el bosque de la etapa 2 aprendiera condiciones del día más que
   la pluma.

**Bosque aleatorio (informativo).** Quedó sin correr: se detuvo tras 2 de unos 60 pliegues porque el
computador se quedó sin memoria ni disco (§3). No cambia el veredicto, que sale sólo de las 18 variables.

**Para el dashboard: nada que llevar.** La capa VOLCAT externa (ficha SDA v2.8, §A.7) sigue siendo la mejor
información disponible para estas plumas.

## 2. Números (salida cruda en `resultados/h13_resultado.txt`)

Pares: 72 de 100 cuadros anclados (26 sin control a ≤ 3 K de BT11, 2 con huella de menos de 3 píxeles en el
disco de 40 km), 9 jornadas, 54 de día y 18 de noche, 865 píxeles de huella (7 quedaron fuera del disco de
40 km). Diferencia de BT11 control menos positivo en los pares: mediana −0,98 K; 12 días candidatos con
historia completa por cuadro (mediana).

Las seis métricas, en sus tres formas (Δ1 = contra el cuadro anterior; Δ3 = contra la mediana de los tres
anteriores; P = fracción de los tres últimos cambios del lado de la pluma). AUC agrupado de la huella, IC 95 %
por jornadas y anillo:

| Métrica | Δ1 | Δ3 | P | Un solo cuadro X(t) (referencia) |
|---|---|---|---|---|
| BT11 (baja) | 0,544 [0,510; 0,567], anillo 0,519 | **0,582** [0,523; 0,631], anillo 0,547 | 0,490 | 0,462 |
| BTD 11−12 (baja) | 0,462 | 0,445 | 0,480 | 0,612 [0,507; 0,692], anillo 0,490 |
| ε(11) (sube) | 0,550 [0,527; 0,566], anillo 0,515 | **0,582** [0,541; 0,650], anillo 0,543 | 0,514 | 0,597 |
| β(12/11) (baja) | 0,457 | 0,444 | 0,476 | 0,585 |
| β(8,5/11) (sube) | 0,494 | 0,512 | 0,466 | 0,494 |
| β(7,3/11) (sube) | 0,539 | 0,562 [0,499; 0,651], anillo 0,508 | 0,514 | 0,540 |

- **Veredicto según el criterio: H13 SE FALSA** (AUC máximo de las 18 temporales = 0,582 < 0,60). Ninguna
  cumple siquiera la condición del anillo (huella − anillo ≥ 0,10; la mejor, +0,061 en Δ1 β(7,3/11)).
- Por estrato, ninguna temporal pasa de 0,61 (Δ3 ε(11) de noche, 18 pares).
- Sensibilidad (a), pareo por BT11 en t − 30 min (74 pares): máximo 0,521 (P β(12/11)); falsaría igual.
- Sensibilidad (b), sólo cuadros de arranque y sus 2 siguientes: 14 pares, por debajo del mínimo de 30 que
  pide el criterio. Informativo: el máximo es 0,624 (Δ3 ε(11)) con IC [0,505; 0,745] y anillo 0,575; no separa.
- En BTD y β(12/11) los cambios quedan bajo 0,5 (AUC 0,44 a 0,46): la huella se mueve un poco **menos** hacia
  el lado de la ceniza que el control. Es el reflejo de que el valor de un solo cuadro sí está algo más del
  lado de la ceniza (BTD 0,61, β(12/11) 0,59, coherente con H3, β73 y H11): una pluma que ya estaba antes no
  cambia, y el control vuelve hacia su media.

## 3. Bosque aleatorio (informativo): no se completó

El criterio pedía, como variante que no decide, el bosque de la etapa 2 con y sin las 18 variables temporales,
dejando una jornada afuera. El conjunto se armó (940 scans: 100 cuadros anclados, 771 cuadros candidatos a
control limpios y 69 del mismo día sin objeto VOLCAT, 29 jornadas con negativos), pero la corrida se detuvo
después de 2 pliegues (jornadas 20-10 y 21-10, sin detecciones; no se pueden leer como resultado). El
entrenamiento con ~400.000 píxeles por pliegue llevó a Windows a agrandar el archivo de paginación hasta dejar
el disco C: en 0 bytes, y se paró para no comprometer el resto de las sesiones. No hay `resultados/h13_rf.txt`.

Para correrla después basta con `python h13_rf.py ../resultados/h13_rf.txt` desde `scripts/`, con espacio en
C: y en un momento sin otros cálculos pesados (lee todo desde `D:\goes_cache\h13\`). Antes conviene bajar el
submuestreo de negativos o `n_jobs`. No es prioritaria: si las variables temporales no separan la huella del
mismo lugar sin pluma, un bosque que las agrega puede aprender condiciones del día, no la pluma (la misma
advertencia de la etapa 2).

## 4. Desviaciones y advertencias

1. **Disco de 40 km.** La huella se recortó al disco de 40 km donde existe la rejilla del modelo radiativo
   (H11 usaba ≤ 50 km). Quedaron fuera 7 de 872 píxeles. Declarado en el criterio.
2. **Cielo despejado interpolado en el tiempo** entre las dos horas GFS que encierran cada scan (declarado).
   Las 1.527 escenas tuvieron las dos horas; ninguna quedó con una sola. En una escena del 14-11 a las 17:00
   (peso cero de la segunda hora) las variables coinciden con las de la etapa 2 hasta 1e-4 en ε(11).
3. **El modelo radiativo se corrió una vez por hora GFS** (348 horas: 224 reutilizadas de la etapa 2 y 124
   calculadas), porque depende del scan sólo por el perfil. No cambia la física.
4. **La mediana de los tres previos en las β** ignora los cuadros con β inválido (nanmediana); en BT11, BTD y
   ε se exige que los tres existan. La persistencia sólo toma valores 0, 1/3, 2/3 y 1, con muchos empates.
5. **26 cuadros sin control**, casi todos de la tarde y la noche del 14-11 (14) y del 08-11 (5). En 23 de ellos
   todos los candidatos estaban más fríos que el positivo (diagnóstico posterior, no decide). Eso saca de la
   muestra justo los cuadros más tibios; con la sensibilidad (a), que parea antes de la pluma, entran 74 pares y
   el resultado es aún más bajo.
6. **Incidentes de cómputo, sin efecto en los números.** (a) El disco C: se llenó a mitad de la bajada; se
   relanzó lo pendiente, se borraron los temporales a medio escribir y se comprobó que ningún npz quedara
   corrupto. (b) Por falta de espacio, todos los datos se movieron a `D:\goes_cache\h13\`. (c) Otra sesión
   borró los scratchpads de H3, β73 y la etapa 2 para liberar C:. Las copias rescatadas (inventario VOLCAT,
   huellas, pareos, `rt.py`, cachés L1b y GFS) se copiaron a `D:\goes_cache\h13\shim\` con la misma estructura,
   y `h13_comun.py` carga `comun_h11.py` cambiando sólo sus dos rutas escritas (el archivo de la etapa 2 no se
   editó). El modelo radiativo ya estaba calculado para las 348 horas antes del borrado. (d) El bosque
   aleatorio informativo se detuvo por memoria y disco (§3).
7. Sólo Chillán y sólo ABI a 10 min (disco completo). Los sectores de mesoescala de 1 min los asigna NOAA y
   normalmente no apuntan a Chile.

## 5. Qué queda

1. **Un "prior espacial"** (Pavolonis 2014, tesis, pp. 195 y 241 a 242: usar resultados previos como
   conocimiento a priori de dónde está la ceniza) no se probó aquí y no se puede probar con VOLCAT como prior,
   porque los controles se eligen sin objeto VOLCAT de t − 90 a t + 60 min y separaría por construcción. La
   versión honesta usaría como prior una señal propia de cuadros estrictamente anteriores; con lo medido en H7
   y H13 (no hay señal propia en el primer cuadro ni en los cambios), no hay de dónde sacarla.
2. La vía que queda abierta es la de siempre: las PDF y la configuración por volcán de VOLCAT, que no son
   públicas (correo a Pavolonis ya redactado).

## 6. Archivos

- Criterio: `docs/own_volcat/temporal_h13/criterio_H13_2026-11-20.md`.
- Resultados: `docs/own_volcat/temporal_h13/resultados/`.
- Scripts: `docs/own_volcat/temporal_h13/scripts/` (`h13_comun.py`, `fetch_h13.py`, `h13_rt.py`,
  `h13_feat.py`, `h13_analisis.py`, `h13_rf.py`).
- Datos (fuera del repo, en D: porque C: se llenó): `D:\goes_cache\h13\` (`cache` con las escenas L1b por
  ventana bajadas para H13, `gfs`, `rt_hora` con los nodos del modelo radiativo por hora, `feat` con las
  variables de las 1.527 escenas, `png` con los PNG VOLCAT de los 10 días con pluma, `pares_h13.pkl` con los
  72 pares y sus variables, `shim` con las copias de los cachés y metadatos rescatados).

No se tocó código de la app ni `POR_QUE_VOLCAT_VE_Y_NOSOTROS_NO.md`. Sin VIIRS. Nada en `data/raw`.
