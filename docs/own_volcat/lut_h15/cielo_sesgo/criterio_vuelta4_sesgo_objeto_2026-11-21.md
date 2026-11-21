# Criterio, vuelta 4: ¿el desfase de ~1,1 K del cielo despejado de 11 µm es el sesgo de BT14 por objeto? 21-11-2026

Escrito y subido antes de medir los cuadros 6 a 10.

## Hipótesis (del encargo)

VOLCAT calcula por objeto el sesgo de BT14 del ambiente (`Bt14_Bias_Env_Per75`; anillo de 1 a 12 px según SECO
Parte 2 §4.3) y lo aplica de vuelta al cielo despejado de ε(11), así que el εtot publicado lleva el sesgo del
objeto.

## Lo que se vio antes de escribir esto (sondeo, cuadros 1 y 6; se repite en los 10 con el script)

- `geocatASHOBJ`, cuadro 1 (09:16): 588 objetos; en todos, `ASHOBJ_Mean_Bt14_Bias_Obj`, `_Env` y
  `ASHOBJ_Maximum_Bt14_Bias_Env` valen −999 (relleno), y `ASHOBJ_Total_Bias_Valid_Pixels` y `_Eligible_Pixels`
  valen 0. Cuadro 6 (09:41): 139 objetos, lo mismo.
- `geocatL2` `Ash_Group_Id_2d`: todo −999 en los cuadros 1 y 6. `geocatDIAGS1` `Ash_Object_Mask` (valores 0, 1, 2):
  con valor > 0 cubre 1,0 % del dominio en el cuadro 1 y 0,2 % en el 5, y 0,2 % y 0,6 % de los píxeles con
  0,05 ≤ ε < 0,3.

## Predicciones de la hipótesis, y cuándo se descarta

Si la hipótesis fuera cierta, en los 10 cuadros:
- **P1.** Habría objetos con sesgo de BT14 válido (`Total_Bias_Valid_Pixels` > 0 o algún resumen de sesgo distinto
  de −999) cuyo conjunto cubra la mayoría de los píxeles tenues.
- **P2.** El desfase implícito de C14 (vuelta 3) sería distinto de cero sólo dentro de los objetos y ~0 fuera.

**Se descarta, y se para (lo pide el encargo), si** en los 10 cuadros (a) ningún objeto tiene sesgo válido, o
(b) menos del 10 % de los píxeles con 0,05 ≤ ε < 0,3 cae dentro de un objeto (`Ash_Object_Mask` > 0), y además el
desfase implícito mediano fuera de los objetos es ≤ −0,5 K (es decir, el desfase existe donde no hay objeto). Con
(a) o (b) la prueba 1 del encargo (desfase constante por objeto) no se puede hacer sobre los píxeles que importan,
y las pruebas 2 y 3 no corren.

Se informa igual: por cuadro, número de objetos, objetos con sesgo válido, fracción de píxeles tenues en objeto, y
la mediana del desfase implícito de C14 dentro y fuera de objeto.

## Requisito para Chillán (se anota, no se resuelve)

Si en otro caso el ε dependiera de los objetos, aplicarlo a Chillán exigiría formar los objetos nosotros o usar
`event_idx`.
