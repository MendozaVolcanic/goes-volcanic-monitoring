# S29b: la zona del cráter y el detector combinado S26a, fuera de muestra en oct-nov 2024. Informe, 26-11-2026

**Veredicto: la zona (S25a) y la unión (S26a) AGUANTAN fuera de muestra en oct-nov 2024, de noche y de día (unión
3,0 %, zona 2,3 %, contra 4,9 % y 3,2 % en 2025); de día la unión queda MÁS ESTRICTA (1,1 % contra 3,9 %). La lectura
(d) del criterio da "la subida diurna es de 2026", pero el post hoc la debilita: en 2024 las zonas de Antuco y Longaví,
sin pluma, disparan de día 7,7 y 7,3 %, tanto como Antuco en 2026. De día las cumbres cambian de un año a otro por sí
solas; 2025 fue un año bajo para las vecinas, no para Chillán.**

Ningún veredicto de aquí se apoya en un p por cuadro (S28b mostró que las rachas por día lo inflan): (b) usa tasas, y
(c) y (d) un intervalo por remuestreo de días, con el día como unidad.

Criterio `criterio_2026-11-25.md` (commit `afd2923`), empujado antes de calcular un disparo de la zona o de la unión en
2024. Código `scripts/s29b_cubo.py` (cubo de BTD de 2024 y atributos de geometría), `scripts/s29b_medir.py` (la medida)
y `scripts/s29b_posthoc.py` (las vecinas, post hoc). Resultados en `resultados/`. Lo grande en
`D:\goes_notas\s29\s29b\` (cubo de BTD de 2024, 0,35 GB). Ningún día de 2026 entra en esta medida.

## 1. Para geólogo

**La pregunta.** El detector que se va a confirmar con VOLCAT mira dos lugares: la zona de 0 a 4 km del cráter y un
anillo de 4 a 40 km. Las dos partes aprendieron qué es "normal" en oct-nov 2025, un año sin pluma. S25b ya mostró que el
anillo, puesto en oct-nov 2024 (otro año tranquilo, en alerta verde, visto por GOES-16), se equivoca menos que en 2025.
Faltaba la zona. La zona es más delicada: compara cada píxel de la cumbre consigo mismo a la misma hora de 2025, así que
si la cumbre cambia de un año a otro (otra nieve, roca descubierta) o si el satélite la ve un poco corrida, el cambio
entra entero.

**¿El satélite de 2024 ve la cumbre en el mismo lugar?** Sí. GOES-16 (2024) y GOES-19 (2025) estaban en el mismo punto
(75,2° O) y entregan la misma grilla fija, así que el relieve de la cumbre aparece corrido igual por paralaje en los
dos. Comprobado además con la imagen: el campo medio de temperatura de noches despejadas alrededor del cráter, donde el
relieve hace el dibujo, coincide entre años con correlación 0,997, y el mejor calce pide mover 2024 apenas 0,05 y 0,1
píxel (100 a 200 m). El píxel más frío de la zona es el mismo en los dos años.

**Qué se vio en la cumbre.** La cumbre de 2024 estuvo 1,3 K más fría que la de 2025 en noches despejadas (más nieve o
un año más frío), y su diferencia 11 a 12 µm subió 0,22 K. Pero los controles lejanos de la misma cota subieron lo
mismo (0,23 K): fue un cambio regional, y la corrección regional de la regla lo saca. Por eso la zona no se dispara de
más.

**La falsa alarma.** Con base y umbral de 2025, sin tocar nada:

- la **zona** dispara en el 2,3 % de los cuadros que mira (3,8 % en promedio por día), contra 3,2 % en 2025;
- la **unión** dispara en el 3,0 % (3,9 % por día), contra 4,9 % en 2025;
- el **anillo**, en el 1,6 %, como ya había visto S25b.

Las tres quedan bajo el 5 % prometido.

**De noche y de día.** De noche la unión dispara 3,4 % (6,7 % en 2025) y la zona 3,0 % (4,3 %). De día la unión baja
a 1,1 % (3,9 % en 2025) y la zona a 0,8 % (2,8 %). La hora débil es la **madrugada y el amanecer** (06:00 a 11:50 UTC,
03:00 a 08:50 hora de Chile): ahí la unión llega a 9,1 % entre 09:00 y 11:50 UTC, bajo el tope de 10 % del criterio.
Casi todo eso lo ponen dos mañanas, el 23-09 y el 25-10-2024, con rachas continuas de cinco horas (de 06:20 a 11:10
UTC el 25-10): un disparo que dura toda la madrugada es tiempo (capa baja o inversión, lo mismo que S24 vio en las
noches de 2025), no un pulso. El 16 a 18-11-2024, donde se juntan las falsas alarmas del anillo (S25b), la zona no
dispara ni una vez.

**Lo que dice del día de 2026.** S28a vio que en 2026, de día, la zona de la cumbre de Antuco (sin pluma) dispara
cuatro veces más que en 2025, igual que Chillán. Había dos explicaciones: que 2026 trae algo propio, o que 2025 fue un
año diurno bajo. La regla del criterio compara el día de Chillán en 2024 con la subida de Antuco: Chillán en 2024
dispara de día **menos** que en 2025 (unión ×0,28, intervalo 0,09 a 0,94), así que la lectura escrita antes es "la
subida diurna es de 2026".

**El post hoc la debilita, y pesa más que la regla.** Puse la misma zona en las cumbres de Antuco y Longaví en 2024
(§3). De día las dos disparan 7,7 y 7,3 %, tres veces más que en 2025 (2,6 y 2,5 %) y casi lo mismo que Antuco en 2026
(9,4 %). Ninguna de las dos tuvo pluma ningún año. Entonces, para las vecinas, **2025 fue el año bajo**, y lo de Antuco
en 2026 no es algo propio de 2026: es una cumbre que de día cambia mucho de un año a otro por sí sola. Chillán en 2024
hizo lo contrario (bajó). De día cada cumbre tiene su propio año, y la falsa alarma diurna no es una constante de la
regla. Lo que sí se sostiene: la de Chillán en sus dos años tranquilos fue 1,1 y 3,9 %, bajo el 5 %, y la de
desarrollo (2025) es la más alta de las dos.

Esto calza con S29a, que encontró **más** nieve en Antuco en 2026 que en 2025 y ninguna explicación de la subida
(`s29a_compuerta_regional/INFORME.md`), y con S28b, que vio que el MIXTO de S28a cuelga del 10-11 y de la semilla.

**Para la confirmación en días nuevos.** El 4,9 % de desarrollo de la unión S26a no era una cifra propia de 2025: en
otro año tranquilo, con otro satélite, la unión dispara menos. Lo que no se sabe es cuánto dispara Chillán de día en
2026 sin pluma: las vecinas muestran que de día una cumbre puede triplicar su tasa de un año a otro sin pluma, y Chillán
podría hacerlo en 2026. Y para la compuerta regional de S29a (anular un disparo de Chillán si una vecina dispara): en
2024 las vecinas disparan de día a menudo y Chillán casi nunca, así que "una vecina dispara" no es una señal propia de
2026.

## 2. Cifras por el criterio

### (a) Geometría: COMPARABLE

| Id | Resultado | Pasa si | |
|---|---|---|---|
| G1 | atributos del NetCDF iguales (subpunto −75,2°, misma altura, misma escala y origen de x e y) | iguales | pasa |
| G2 | correlación 0,997 (118 píxeles a < 15 km; 892 cuadros de noche despejada en 2024, 1.255 en 2025) | ≥ 0,90 | pasa |
| G3 | corrimiento dy 0,05, dx 0,10 píxel (error 0,221 contra 0,239 sin mover) | ≤ 0,25 | pasa |
| G4 | L1B 0,990, ACMF 0,983, BT11 en rango 1,0, 0 congelados, 0 de scan distinto | todo | pasa |

Informativo: BT11 de la zona 2024 menos 2025, mediana −1,26 K; BTD de la zona +0,22 K, de los controles de su cota
+0,23 K (de +0,13 a +0,31 K por píxel).

Comprobación de código (criterio §3), antes de leer 2024: el camino fuera de muestra reprodujo el S de 2025 exacto; el
seco de 2025 dio zona a 5 176 de 5.499 y unión a 4,75 269 de 5.499 (noche 98 de 1.453, día 105 de 2.704), lo publicado.

### (b) Falsa alarma total, nublado de costumbre de 2024 (la regla)

| Regla | 2024 global | 2024 media por día | 2025 global / media por día | Veredicto |
|---|---|---|---|---|
| Zona S25a (percentil 5) | 101 / 4.407 (2,29 %) | 3,84 % | 3,20 % / 2,59 % | **AGUANTA** |
| Unión S26a (4,75) | 131 / 4.407 (2,97 %) | 3,91 % | 4,89 % / 4,31 % | **AGUANTA** |
| Zona a 4,75 (parte) | 93 / 4.407 (2,11 %) | 3,22 % | 2,98 % / 2,40 % | AGUANTA |
| Anillo a 4,75 (parte) | 38 / 2.448 (1,55 %) | 1,42 % | 3,76 % / 4,00 % | AGUANTA |

Ninguna llega a la etiqueta MÁS ESTRICTO (< 2 % en las dos medidas): la media por día de la zona sube por días con
pocos cuadros evaluados y muchos disparos. La zona evalúa 52 de los 62 días y dispara en 20; la unión dispara en 24.

Franjas de 3 h de la unión, 2024 (2025): 00-02 3,3 % (5,6); 03-05 0,2 % (7,1); 06-08 6,4 % (6,4); **09-11 9,1 %
(4,2)**; 12-14 1,7 % (4,3); 15-17 0,5 % (3,6); 18-20 2,2 % (3,4); 21-23 0,0 % (4,1). Ninguna pasa el 10 %. Zona a 5:
la franja más alta es 09-11 con 6,5 % (2,8 en 2025).

Los 5 días con más disparos de la unión ponen el 58 % (25-10: 25; 23-09: 23; 09-10: 11; 18-11: 9; 16-11: 8); los de la
zona a 5, el 73 %. Racimo del 16 al 18-11-2024: unión 25 disparos, todos del anillo; zona 0.

Píxeles que hacen S en los disparos: en 2024 dominan (41,46) y (41,45), en el borde N de la zona (61 y 37 veces); en
2025 el reparto era más parejo, con (42,46) primero (52). Es una diferencia de pocos días (dos mañanas ponen la mitad).

Sensibilidad con el nublado de costumbre de 2025 (no decide): zona a 5 1,91 % (1,63 % por día), unión 2,30 % (1,93 %),
todas AGUANTA. El nublado de costumbre de 2024 que usa la zona es idéntico al del `Detector` de 2024 de S25b.

### (c) Día y noche (R = tasa 2024 / tasa 2025; IC 95 % por remuestreo de días, 2.000 réplicas)

| Regla | Periodo | 2024 | 2025 | R | IC 95 % | Veredicto |
|---|---|---|---|---|---|---|
| Zona S25a (5) | Noche 03:00 a 08:50 UTC | 30 / 996 (3,0 %) | 63 / 1.453 (4,3 %) | 0,69 | 0,07 a 4,14 | **AGUANTA** |
| | Día 12:00 a 23:50 UTC | 18 / 2.292 (0,8 %) | 76 / 2.704 (2,8 %) | 0,28 | 0,06 a 1,25 | **AGUANTA** |
| Unión S26a (4,75) | Noche | 34 / 996 (3,4 %) | 98 / 1.453 (6,7 %) | 0,51 | 0,08 a 2,17 | **AGUANTA** |
| | Día | 25 / 2.292 (1,1 %) | 105 / 2.704 (3,9 %) | 0,28 | 0,09 a 0,94 | **MÁS ESTRICTO** |
| Zona a 4,75 | Noche | 27 / 996 | 60 / 1.453 | 0,66 | 0,06 a 4,18 | AGUANTA |
| | Día | 15 / 2.292 | 69 / 2.704 | 0,26 | 0,05 a 1,27 | AGUANTA |
| Anillo a 4,75 | Noche | 7 / 668 | 52 / 1.179 | 0,24 | 0 a 1,78 | AGUANTA |
| | Día | 10 / 1.107 | 52 / 1.473 | 0,26 | 0,04 a 1,21 | AGUANTA |

Ninguna tasa de 2024 pasa el 5 % en ningún periodo. Con el nublado de costumbre de 2025, los mismos veredictos salvo el
anillo de noche, que queda MÁS ESTRICTO.

### (d) El día de 2024 contra la subida de Antuco en 2026

| Regla | R día 2024 (IC 95 %) | R Antuco 2026 (S28a) | Lectura |
|---|---|---|---|
| Unión a 4,75 | 0,28 (0,09 a 0,94) | 2,64 | **LA SUBIDA DIURNA ES DE 2026** |
| Zona a 4,75 | 0,26 (0,05 a 1,27) | 3,66 | **LA SUBIDA DIURNA ES DE 2026** |

La regla compara años de Chillán con años de Antuco. El post hoc (§3), que compara cada cumbre consigo misma, no la
respalda: la lectura vale como "Chillán no subió de día en 2024", no como "2026 tiene algo regional".

### Lo que esperaba (criterio §7) contra lo que salió

Acerté en la geometría y en que la unión aguanta. Me equivoqué en el riesgo: esperaba que la zona sufriera de día (la
nieve de la cumbre cambia de un año a otro) y fue al revés, el día es lo más tranquilo de 2024; el punto débil fue la
madrugada y el amanecer, por dos mañanas de tiempo. Para (d) apostaba NO CONCLUYENTE con R cerca de 1 y salió R 0,28.

## 3. Post hoc: tres cumbres de día (no decide)

La zona a percentil 4,75 puesta en las cumbres de Antuco y Longaví con la clase `Zona` de S27a sin cambio (base y
umbral de 2025 de cada cumbre), aplicada a 2024 (`resultados/s29b_posthoc.json`). Comprobación: la misma clase con la
geometría de Chillán da la zona a 4,75 de la medida principal (93 de 4.407; noche 27 de 996, día 15 de 2.292), y 2025
de Antuco da lo publicado por S27a (noche 62 de 1.476, día 62 de 2.410).

Zona de cada cumbre, de día (12:00 a 23:50 UTC), disparos sobre evaluados:

| Cumbre | 2024 | 2025 | 2026 (S27a) | R 2024 / 2025 (IC 95 %) |
|---|---|---|---|---|
| Chillán | 15 / 2.292 (0,7 %) | 69 / 2.704 (2,6 %) | con pluma, no se puede medir | 0,26 (0,05 a 1,27) |
| Antuco | 176 / 2.273 (7,7 %) | 62 / 2.410 (2,6 %) | 138 / 1.467 (9,4 %) | 3,01 (1,03 a 23,4) |
| Longaví | 167 / 2.287 (7,3 %) | 72 / 2.889 (2,5 %) | 53 / 1.665 (3,2 %) | 2,93 (1,10 a 7,28) |

De noche (03:00 a 08:50 UTC): Chillán 2,7 % (4,1 % en 2025), Antuco 2,0 % (4,2 %), Longaví 4,9 % (3,8 %); todas
AGUANTA por la regla de (c).

Lectura: de día, las dos vecinas sin pluma triplican en 2024 su tasa de 2025, y Antuco en 2024 queda cerca de Antuco
en 2026. La subida de Antuco en 2026 que S28a leyó como "algo regional de 2026" ya estaba en 2024: 2025 fue el año
bajo de las vecinas. Chillán va al revés (baja en 2024). De día cada cumbre tiene su propio año. Los días fuertes de
las vecinas son otros que los de Chillán: Longaví pone el 60 % en 5 días, entre ellos el 13, 17 y 18-11-2024 (las
mismas fechas del racimo del anillo de Chillán en S25b), y Antuco reparte más (47 % en 5 días: 06-11, 26-10, 20-11,
23-09, 09-10). Por qué disparan, GOES no lo dice.

Lo que esto no dice: que Chillán en 2026 dispare de día como las vecinas (no se puede medir con pluma); que la tasa
de las vecinas sea la de Chillán (otra cumbre, otra cota, otra nieve).

## 4. Lo que sigue

- **La confirmación en días nuevos no cambia**: S29b no toca ninguna regla congelada. Refuerza que la falsa alarma de
  la unión en años tranquilos está en o bajo el 5 %.
- **El día de las cumbres cambia entre años sin pluma**: tres años de Antuco y Longaví (2024, 2025, 2026) dan de 2,5
  a 9,4 %. Para leer el día de Chillán en 2026 hace falta otro año de fondo o una regla diurna que no dependa de la
  cumbre de un solo año (por ejemplo, base con 2024 y 2025 juntos), con criterio antes. S29a ya miró la nieve de 2026.
- **Las mañanas de tiempo** (23-09 y 25-10-2024, y las noches de capa baja de 2025 en S24): rachas de horas que la regla
  confunde con pluma. Una regla de duración (un pulso no dura cinco horas inmóvil sobre la cumbre) es candidata, pero se
  decide con criterio previo y no con estos días.
- Pendiente de antes: que el OVDAS confirme que Chillán no tuvo pulsos del 21-09 al 21-11-2024 (decisión 1 de S25b).

## 5. Lo que no puede decir

Que la zona o la unión detecten pluma (esto mide sólo falsa alarma); nada de 2026; por qué 2024 dispara menos de día
que 2025 (más nieve en la cumbre, otro tiempo; GOES no lo separa); si 2024 estuvo libre de toda desgasificación (alerta
verde no la excluye, igual que en 2025).
