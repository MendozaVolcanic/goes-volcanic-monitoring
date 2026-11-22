# H19: reglas congeladas antes de abrir el bloque de validación

Fecha: 22-11-2026. Criterio: `criterio_2026-11-22.md` (commit c62b60a). Este archivo se commitea antes de
calcular nada en los cuadros 20:31 a 23:31. Todo lo de abajo se eligió con los 13 cuadros de 17:16 a 20:16.
El código de las reglas está en `scripts/h19_reglas.py`.

## Lo que se vio en el bloque de elección (números de `resultados/eleccion_*.txt`)

1. La probabilidad publicada y `ash_probability_subset` sólo tienen valor dentro del grupo de nube
   convectiva volcánica (`Ice_Group_Id_2d` > 0): índice de Jaccard de 0,98 a 1,00 por cuadro. El grupo de
   ceniza (`Ash_Group_Id_2d` > 0) está siempre contenido en ese grupo.
2. Dentro del grupo, `ash_probability_subset` es alta (≥ 0,5; casi siempre 1,0) exactamente en los píxeles
   "oscuros y opacos": emisividad total a 11 µm ≥ 0,90 y reflectancia a 0,65 µm entre 10 % y 50 %.
   4.788 de 4.788 píxeles oscuros y opacos tienen subset alto; 0 de 6.406 de los demás lo tienen (máximo
   0,0015). Los umbrales no se ajustaron: 0,90 es el borde del último bin de emisividad de la tabla pública
   de píxel de VOLCAT y 10 y 50 son sus atributos `DARK_PIXEL_REF2_MIN` y `DARK_PIXEL_REF2_MAX`.
3. La tabla pública de emisividad por reflectancia (`EMISS14_TOT_VREF_DAY`) no da ese valor: con ella sola
   la probabilidad queda bajo 0,01 en esos píxeles.
4. La probabilidad publicada es igual a subset en el 95 % de los píxeles. En 569 píxeles oscuros y opacos
   la publicada queda por debajo de subset. Esos píxeles tienen β(12/11) más bajo. No se encontró la regla
   exacta de esa rebaja.
5. Los objetos de ceniza seleccionados (48 de 5.770) son los que caen dentro del grupo de nube convectiva.
   Su probabilidad de objeto (`Feature_Prob`) es casi cero (mediana 4·10⁻¹⁵): la tabla de objeto no los
   selecciona. Sus píxeles llevan el código 5 de `Ash_Object_Mask`, que casi no aparece fuera del grupo.
6. El objeto de nube convectiva de cada cuadro es el que más se solapa con el grupo del cuadro anterior
   (12 de 12 cuadros después del nacimiento).

## Reglas congeladas

**B (valor de subset, nivel 1).** Dentro del grupo: subset predicho = 1 si el píxel es oscuro y opaco, 0 si no.

**C (probabilidad publicada, nivel 1). Regla principal, la que decide:** dentro del grupo (píxeles con
probabilidad publicada válida), P alta si y sólo si el píxel es oscuro y opaco. En elección: sensibilidad
1,000, precisión 0,909, 7 de 8 cuadros con ambas ≥ 0,8.
Variante secundaria, declarada y que no decide: además β(12/11) opaco > 1,00 (elección: 0,980 y 0,925).

**D-nube (pertenencia del objeto convectivo, nivel 2).** En el cuadro t, el objeto de `geocatICEOBJ` con más
píxeles sobre el grupo de nube convectiva del cuadro t−1, si hay algún solape. Se mide un paso adelante
(con el grupo verdadero de t−1). El nacimiento del grupo no lo predice esta regla.

**D-ceniza (pertenencia de objetos de ceniza, nivel 2).** En el cuadro t, los objetos de `geocatASHOBJ` con
algún píxel dentro de la dilatación 3×3 del objeto convectivo. En elección: 41 aciertos, 0 falsos, 7
omitidos (objetos de 1 a 7 píxeles; 11 píxeles de 9.266). Se mide con el objeto convectivo verdadero y
también encadenada con D-nube.

**Cadena completa (nivel 2, secundaria).** D-nube, luego D-ceniza, luego C dentro de los píxeles de los
objetos predichos. Entradas: sólo objetos, emisividad, reflectancia y el grupo del cuadro anterior.

## Placebos (los del criterio, concretados)

- B y C: la misma regla con emisividad y reflectancia del cuadro anterior en el mismo píxel.
- D-ceniza: la marca "toca al objeto convectivo" barajada entre los objetos del mismo cuadro, 1.000 veces,
  semilla 19.
- D-nube: el grupo "anterior" tomado de 4 cuadros antes en vez de 1.

## Lo que queda fuera, dicho antes de validar

- El valor exacto de subset en los píxeles que no son oscuros y opacos (sólo se predice "bajo 0,01").
- Por qué VOLCAT asigna casi 1 a un píxel oscuro y opaco (qué tabla o qué prueba lo produce).
- La rebaja de la probabilidad publicada respecto de subset.
- El nacimiento del grupo de nube convectiva y todo el camino `ASHPLUMEPUFF` (se tratan con los logs).
