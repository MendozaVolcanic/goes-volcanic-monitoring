# H24, enmienda post hoc 1 (22-11-2026): más días excluidos del nulo y de la línea base

Escrita y commiteada **antes** de calcular cualquier número de H24 (las descargas del hueco 24 al 31-10 seguían
corriendo; ningún estadístico, nulo ni poder se había calculado).

**Qué la motivó.** Nicolás recordó los píxeles rojos, amarillos y naranjos de VOLCAT de los loops de Chillán (los
archivos en `C:\Users\nmend\Downloads\` son de noviembre: `volcat_nevados_chillan_dias_con_pluma_08-10-11-14_nov_10min_r1deg.mp4`
y los diarios del 07, 08, 10, 11, 12, 14 y 16-11). La lista de exclusión del criterio §7 salió sólo de las 30 marcas
del Grafana (H21, `Ash Event` > 0), que **no incluye el 11-11 ni el 16-11**, y los dos tienen objetos VOLCAT en el
catálogo por cuadro del PNG (`calor_rayos/resultados/frames_calor.csv`, clases de H9: `P` = objeto anclado, `otro`
= ceniza a ≤ 50 km o a ±60 min de un objeto): 11-11 con 3 `P` y 14 `otro`; 16-11 con 40 `otro`. Usarlos como días
"sin pulso" contaminaría el nulo de E13 y E14.

**Cambio.** Días excluidos de línea base y de nulo = los del criterio §7 **más** todo día del 20-10 al 18-11 con
algún cuadro `P` u `otro` en ese catálogo. Eso agrega el **11-11 y el 16-11** (los demás días con `P` u `otro` ya
estaban: 22-10, 24-10, 25-10, 28-10, 29-10, 07-11, 08-11, 10-11, 13-11, 14-11, 18-11).

**Qué no cambia.** Estadístico, regla, poder, controles, episodios y veredicto global, sin cambios.

**Riesgo que queda.** No hay catálogo VOLCAT del 21-09 al 19-10 ni del 19 al 21-11 (SIN DATO: SSEC guarda unas tres
semanas). Si hubo pulsos esos días, están en el nulo y lo ensanchan (empuja hacia SIN SEÑAL). Las cumbres de control
no tienen ese problema. Si Nicolás confirma pulsos en octubre (por ejemplo del 8 al 14-10), se excluyen en otra
enmienda antes de leer los resultados de los episodios de octubre.

**Dirección del sesgo.** Sacar días contaminados del nulo lo angosta: favorece encontrar señal. Se informa así.
