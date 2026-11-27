# S31f: la pluma de Chillán en luz reflejada junto al cráter. Informe, 27-11-2026

Criterio: `criterio_2026-11-27.md`, commit `741acb4` y anexo `c6df303`, los dos empujados antes de calcular una sola
reflectancia; script de medida `6e2a940`, empujado antes de correrlo. Corrección del cálculo de poder, después de medir:
`57d1c4c` (§6). Desarrollo sobre días ya vistos (hasta el 24-11-2026), no confirmación. Ventanas de L1b (C02, C05 y C14,
4.249 cuadros, 172 MB) en `D:\goes_notas\s31\s31f\l1b\`; registros y matrices de nulos en `D:\goes_notas\s31\s31f\`.

**Veredictos por la regla escrita:**

- **Huella anclada de VOLCAT (titular): SIN PODER.** La prueba no podía ver una pluma como la del modelo de S21b, ni
  pintada sobre una cuarta parte de cada píxel de la huella: de 200 réplicas sintéticas sólo 3 tuvieron dato suficiente y
  ninguna rechazó. Con lo medido, además, la huella no se aparta hacia la ceniza: T_U = −0,06, p_R 0,84 (giros), p_N 0,49
  (días sin VOLCAT de 2026).
- **Zona de 0 a 15 km (secundaria): SIN PODER.** p_25 0,067, p_N 0,48, p_Y 0,46.
- **Control positivo del 08-11: NO PASA**, y no podía pasar: sólo 3 días sin VOLCAT tenían la cumbre despejada a esas
  horas (piso del p 0,25 contra 0,05 pedido). El 08-11 fue, de hecho, el valor más bajo de los cuatro.

Lo principal no es la cifra sino la razón del SIN PODER (§3), y lo que muestra el post hoc (§5): en la huella el rojo se
aclara y 1,6 µm se oscurece respecto de 2025, al revés de una pluma con ceniza sobre nieve, y el mismo lugar hace lo mismo
las tardes despejadas sin VOLCAT. Esa pareja es la firma de **más nieve que en 2025**, no de ceniza.

## 1. El fenómeno, antes de los números

Sobre nieve, una pluma con ceniza cambia la luz reflejada de una manera reconocible: oscurece el rojo (0,64 µm), donde
la nieve es muy clara, y aclara 1,6 µm, donde el hielo absorbe y la nieve es oscura pero la ceniza no. Sobre roca, la
misma pluma oscurece las dos. La pregunta era si GOES-19, con su visible de 0,5 km y su 1,6 µm de 1 km, ve ese cambio
dentro de la huella que VOLCAT dibuja pegada al cráter (anclada a menos de 10 km), comparando cada píxel con sí mismo a la
misma fecha y hora de 2025 para sacar el relieve y el sol.

Lo que se encontró es otro cambio, más grande que el de una pluma delgada: la ladera donde VOLCAT dibuja la pluma (el
flanco SE pegado al cráter) está, a 1,6 µm, más oscura que en 2025, y en el rojo un poco más clara. Es lo que hace una
cubierta de nieve más extensa o más fresca (la nieve es clara en el visible y oscura a 1,6 µm; la roca, al revés a
1,6 µm). Y lo hace igual los días con VOLCAT que los pocos días sin VOLCAT despejados. La pluma, si está, queda debajo de
ese cambio de superficie.

Y apareció un hecho de selección que pesa sobre todas las pruebas con controles de 2026: **en oct-nov 2026, casi toda
tarde con la cumbre despejada es una tarde en que VOLCAT dibujó la pluma.** De los 20 días sin ningún cuadro de VOLCAT,
sólo 41 de 640 cuadros diurnos (6 %) tienen la zona del cráter despejada; las nubes son de verdad (BT11 entre 10 y 55 K
bajo lo normal de esa hora). En los días con VOLCAT, la zona se pudo evaluar en 54 de 63 cuadros (86 %). "Día sin VOLCAT"
es, en esta temporada, sobre todo "día nublado en la cumbre".

## 2. Lo que se midió (la regla)

- **Cuadros P**: 63 cuadros de VOLCAT de día (sol a menos de 70° del cenit en el cráter) con huella anclada, en 7 días.
  Evaluados en la huella (zona despejada 70 % y huella 50 %): **39 en 5 días** (28-10: 15; 07-11: 1; 08-11: 12; 11-11: 2;
  14-11: 9). En la zona: 54 en 5 días. El 29-10 y el 10-11 no tuvieron ningún cuadro evaluable (nubes).
- **Reflectancia** dividida por el coseno del cenit solar de cada píxel; **base** de cada píxel: mediana de 2025 en la
  misma fecha ±7 días y la misma hora ±20 min, sin nubes; **u** = cuánto se apartó cada sub-píxel, en unidades de su propia
  dispersión de 2025, con el signo que daría la ceniza según el modelo de S21b sobre esa base (positivo = cambió como lo
  cambiaría una pluma con ceniza).
- Faltan en el bucket 3 cuadros de 2025, ninguno de 2026 y 21 de 2024 (18 del 15-11-2024).

| Estadístico | Valor | p_R (giros) | p_N (días sin VOLCAT 2026) | p_D (huella de otro día) | p_Y (2024) |
|---|---|---|---|---|---|
| T_U huella (promedio de días) | −0,060 | 0,84 | 0,49 | 0,47 | 0,073 |
| T_Z zona (10 % más alto de u) | 3,19 | | 0,48 | | 0,46 (p_25 0,067) |

Por día, T_U: 28-10 −0,40; 07-11 +0,56; 08-11 −0,49; 11-11 −0,27; 14-11 +0,31. Ningún día se aparta hacia la ceniza
más que sus giros o que el mismo lugar otro día.

## 3. Por qué SIN PODER

El poder se midió pintando la pluma del modelo de S21b (f = 0,25 y 0,10) sobre los cuadros de un día sin VOLCAT elegido
al azar, a las mismas horas. Como esos días están casi siempre nublados en la cumbre, en 197 de 200 réplicas no quedaron
10 cuadros en 3 días para evaluar, y en las 3 que sí, la pluma pintada no superó a sus giros. La lectura conservadora
(réplica sin dato = no rechaza) da 0 en la huella y 0,13 en la zona; la de réplicas evaluables, 0 de 3 en las dos.

El mismo hecho le quita poder al nulo N: con 1 a 4 días sin VOLCAT evaluables por cada día P, el nulo tiene unas cien
combinaciones distintas, no 20^7 como contó el criterio. Ese conteo estaba mal: supuso que todo día N sería evaluable.

## 4. Lo que el criterio esperaba y lo que no se cumplió

Esperaba que C05 fuera la banda que se apartara, con el signo de la ceniza sobre nieve: se apartó, pero con el signo
contrario y lo mismo los días sin VOLCAT. Esperaba que el 08-11 pasara: no pudo. Esperaba el nulo N como punto débil por el
depósito y la pluma diaria: fue el punto débil, pero por las nubes. Esperaba que 2024 se apartara de 2025: sí, sobre todo
en C02 (§5).

## 5. Post hoc (escrito después de ver la medida; no cambia ningún veredicto)

Script `scripts/s31f_posthoc.py`, salida `resultados/s31f_posthoc.json` (semilla 2, B = 99.999).

**(a) Cada banda por separado, en la huella.**

| Banda | T (u medio) | p_R arriba / abajo | p_N arriba / abajo | p_Y arriba / abajo |
|---|---|---|---|---|
| C02 (0,64 µm) | +0,97 | 0,35 / 0,65 | 0,45 / 0,55 | 0,007 / 0,99 |
| C05 (1,6 µm) | −1,09 | 0,95 / 0,055 | 0,42 / 0,58 | 0,23 / 0,77 |

Los días sin VOLCAT despejados dan en la misma huella y a la misma hora C02 de +0,34 a +1,41 y C05 de −0,45 a −1,64: el
mismo cambio. C02 "hacia la ceniza" sobre roca y mezcla quiere decir más claro (u positivo con e = +1 donde la base es
oscura); C05 negativo quiere decir más oscuro donde la ceniza lo aclararía. Rojo más claro y 1,6 µm más oscuro es nieve.

**(b) Cambio de toda la zona despejada de 0 a 15 km, ρ − B sin estandarizar (mediana por cuadro):**

| | C02 | C05 |
|---|---|---|
| 2026, días con VOLCAT (129 cuadros) | +0,005 | −0,004 |
| 2026, días sin VOLCAT (41) | 0,000 | −0,002 |
| 2024 (255) | +0,032 | −0,018 |

En 2026 la zona entera casi no cambió respecto de 2025; el cambio está en la huella, el flanco pegado al cráter. En 2024
la zona entera es más clara en el rojo y más oscura a 1,6 µm (otra nieve o la calibración de GOES-16; no se separan).

**(c) Lectura.** En el lugar donde VOLCAT dibuja la pluma, la superficie de 2026 a la misma fecha tiene más nieve, o nieve
más fresca, que en 2025, y eso se ve igual con o sin VOLCAT. No hay rastro de la ceniza en el aire con este método, pero
tampoco podía haberlo: la prueba no tenía poder. Que el flanco cercano tenga más nieve que el resto de la zona es raro si
hay depósito de ceniza ahí todos los días; puede ser nieve nueva de los temporales de noviembre que cae más en la cumbre,
o un efecto de sombra o de ángulo que la base de ±7 días no saca. No se sabe.

## 6. Corridas y correcciones de implementación

- **Corrida 1** (27-11, 04:40 UTC) cortada por el reinicio del PC a las 09:34 hora de Chile, mientras armaba las matrices de
  nulos. Alcanzó a imprimir T_U −0,0597 (39 P en 5 días) y T_Z 3,19 (54 en 5 días); registro en
  `D:\goes_notas\s31\s31f\medir_corrida1_cortada_reinicio.log`.
- **Corrida 2**, el mismo script y las mismas semillas: repitió esas cifras al cuarto decimal (la cuenta hasta ahí no tiene
  azar y los nulos usan generadores con semilla fija), y terminó. Su poder salió con p_R mediano 1,0 y p_N mediano 0,0002,
  imposible a la vez. Causa: cuando ningún día N sorteado era evaluable, el estadístico sintético quedaba vacío (NaN) y
  `pval` devolvía p_R = 1 (nulo vacío) y p_N = 1/(n+1) (toda comparación con NaN es falsa); en la zona, una réplica vacía
  contaba como rechazo. Registro y resultado guardados en `D:\goes_notas\s31\s31f\medir_corrida2_poder_defectuoso.log` y
  `s31f_resultado_corrida2_poder_defectuoso.json`.
- **Corrección** (`57d1c4c`, después de medir): una réplica sin dato no rechaza; el poder que decide se cuenta sobre las
  réplicas evaluables con la regla 1 de §7 (10 P y 3 días), y se informa también la lectura conservadora. Mismo generador y
  mismo orden de sorteos. **Corrida 3**: valores reales y p idénticos a la 2; poder 3 réplicas evaluables de 200, 0
  rechazos. El veredicto SIN PODER es el mismo con las dos lecturas y con la corrida defectuosa.
- El post hoc se cayó dos veces por un detalle de mi script (cuadros de días P fuera de las casillas P no tienen cenit en
  `frames_calor.csv`; se calcula como en los nulos). La parte (a) se repitió igual en las tres corridas.

## 7. Qué significa

1. **La luz reflejada con fondo por píxel de 2025 no ve la pluma en la huella de VOLCAT, y en esta temporada no puede
   decir si está.** El cambio de superficie del flanco SE entre 2025 y 2026 (más nieve) es mayor que la pluma del modelo,
   y no hay días sin VOLCAT despejados con qué separarlo.
2. **Comparar días con VOLCAT contra días sin VOLCAT de oct-nov 2026 es comparar cielo despejado contra cielo nublado.**
   Vale para cualquier prueba futura con controles N de esta temporada, en IR o en reflejado: antes de escribir el criterio,
   contar cuántos N están despejados en la cumbre a la hora de los P.
3. **Lo de S21b no se repite en el promedio.** La mancha clara a 1,6 µm del 25-10 (una franja vista por Landsat) no aparece
   como tendencia en la huella de VOLCAT de 5 tardes; la huella de VOLCAT y la franja de Landsat no son lo mismo, y el 25-10
   no entró (sin huella anclada de día).

## 8. Lo que puede estar mal

- **El signo esperado viene del modelo de S21b** (ρ de pluma 0,109, transmisión 0,47), fijado con un solo Landsat. Si la
  pluma diaria es más gas que ceniza, aclara las dos bandas como una nube tenue y el signo esperado en C05 sobre roca sería
  otro. El post hoc por banda no depende del signo: ninguna banda se separa de los días sin VOLCAT.
- **"Más nieve" es una lectura post hoc** de un par de signos; no la comprobé con Sentinel-2 ni con NDSI.
- **La base de ±7 días y ±20 min** no corrige la pendiente: una ladera al SE iluminada distinto entre fechas puede dar parte
  del cambio.
- **Las nubes**: la regla de §4.1 marca nube de agua y nube fría; un cirro delgado que no baje 6 K la BT11 pasa.

## 9. Lo siguiente

- Para luz reflejada en la cumbre, el fondo tiene que ser del **mismo año y de la misma nieve**: comparar el cuadro con los
  cuadros despejados de la misma tarde o del día anterior, no con otro año. Es la variante que S21b llamó "nulo del mismo
  día"; aquí no se probó.
- Para cualquier control N de oct-nov 2026: contar antes los N despejados en la cumbre a la hora de los P.
- La temporada de verano (ene-mar), con más tardes despejadas sin VOLCAT y nieve más estable, es la ocasión natural para
  repetir esta medida con poder.
