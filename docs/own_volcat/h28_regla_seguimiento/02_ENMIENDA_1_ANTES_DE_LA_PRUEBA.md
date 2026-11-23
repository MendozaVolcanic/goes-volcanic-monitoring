# H28, enmienda 1: un error de mi lector de logs, encontrado por el control de integridad

Escrita el 23-11-2026, **después** de commitear `01_REGLA_Y_CRITERIO.md` (commit `8f0ac51`) y
**antes** de abrir ningún dato de prueba. No cambia ningún umbral ni ningún criterio.

## Qué pasó

Al correr el evaluador sobre los datos de ajuste (el control positivo que el criterio exige), el
control de integridad dio distinto en Fuego: el log trae 12 líneas `Group classification` y mi tabla
tenía 7. El lector guardaba los grupos de ceniza y los de nube convectiva (hielo) en una misma lista
y, como los dos se numeran desde 1, el grupo de hielo 1 pisaba la clasificación del grupo de ceniza 1.
En Kirishima no hay grupos de hielo y por eso no se vio.

Corregido en `scripts/h28_parse_logs.py` (cada grupo lleva su tipo, tomado de la línea
`Classifying ash features` o `Classifying ice features` que cierra su bloque). El control de
integridad ahora da igual en los dos casos del ajuste.

## Qué cambia en lo ya escrito

**T5 queda refutada en el propio ajuste.** Con el lector corregido aparece el grupo de ceniza de
Fuego de las 17:46 UTC: `History Index: NA`, `K-d Overlap Count: 21` de 21 píxeles, y clasificado
`New Volcanic Feature`. Es el primer grupo de ceniza dentro de la nube convectiva que VOLCAT ya venía
siguiendo: sus píxeles están enlazados con el cuadro anterior (por la nube convectiva), pero no hay
un rasgo de ceniza anterior. O sea, `K-d Overlap Count` > 0 no implica `Old Volcanic Feature`.

T5 no se reescribe. En la prueba se informa tal como está en el criterio, y cuenta como una prueba
que no cumple. Lo que los 12 grupos de ceniza del ajuste sí muestran (12 de 12) es otra cosa:
`New Volcanic Feature` si y sólo si `History Index` es `NA`. Eso se informa en la prueba como
**post hoc** y no decide nada.

**Consecuencia para el veredicto.** El criterio pide T1, T2, T3, T5 y T6 para "LA REGLA DE
SEGUIMIENTO SE SOSTIENE". Con T5 caída antes de empezar, ese veredicto ya no se puede alcanzar. Lo
más que la prueba 1 puede dar es "T1, T2, T3 y T6 cumplen; T5 no", dicho con esas palabras.

## Lo demás del ajuste, recalculado con el lector corregido

Sin cambios: T1 (31 de 31 y 651 de 651 filas), T2 (31 de 31 y 651 de 651), T3 (Fuego: 11 de 11 que
cumplen y 34 de 34 que no; Kirishima: 5 de 5 que cumplen, sin filas que no cumplan), T6 (todas).
Placebo de T3 en Fuego: mediana 0,58, percentil 95 0,70 (la regla da 1,00).
Archivos: `resultados/ajuste/eval_kirishima.json`, `resultados/ajuste/eval_fuego_ajuste.json`.
