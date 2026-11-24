# S21a2, enmienda 1: lo que marca la máscara, escrito antes de leer GOES (24-11-2026)

Escrita después de correr `s21a2_correr.py preparar` (máscara, sombra y paralaje: sólo reflectancia y geometría) y
`s21a2_componentes.py` (descripción de la máscara), y **antes** de correr `esperado`, `medir` o `posthoc`, o de leer
cualquier BT11, BT12 o BTD de GOES-19 de estas pasadas. No cambia la regla ni el veredicto de `criterio_2026-11-24.md`
(commit `50b534e`); agrega una lectura escrita antes y una variante informativa.

## 1. Qué dio la preparación

Salidas: `resultados/preparar_resumen.json`, `resultados/preparar.log`, `resultados/estado_huella.json`,
`resultados/componentes.json`, figuras `figuras/mascara_2026-10-29.png` y `figuras/mascara_2026-11-13.png`.

| | 29-10, S2C 14:53:03 | 13-11, S2B 14:53:06 |
|---|---|---|
| Estado por §3 del criterio | huella (Σ f = 1,08) | huella (Σ f = 2,93) |
| Área marcada | 8,96 km² en 393 componentes, hasta 16 km del cráter | 19,14 km² en 380 componentes, hasta 16 km |
| Altura | sombra **no válida** (mediana 0,78 > 0,5); se usa la del VAAC, 4,27 km | sombra **no válida** (0,75 > 0,5); VAAC/PIREP, 4,27 km |
| Población (f ≥ 0,15 fuera del bloque) | 1 píxel, (41, 53), f 0,17, cota 1.376 m | 6 píxeles, f 0,16 a 0,27, cotas 1.809 a 2.393 m |
| Lo que se ve en color | una bocanada blanca chica pegada al cráter por el ESE (0,3 km² marcados, a 0,4 a 1,1 km) | una nube blanca a 2 a 5 km al NE del cráter, marcada sólo en su parte sobre nieve (0,8 km²), que sigue sobre el bosque sin marca |
| Σ f de la población que viene de componentes a ≤ 6 km del cráter | 0,033 de 1,08 (**3 %**) | 0,159 de 2,93 (**5 %**) |

Para comparar, con el mismo cálculo en las máscaras de S20b: 25-10, 0,228 de 0,242 (94 %); 08-11, 0,514 de 0,596
(86 %).

**Lectura (reflectancia, sin GOES).** En las dos pasadas nuevas, la población de la regla viene casi entera de
componentes a 7 a 16 km del cráter, angostas y pegadas al borde de la nieve de referencia (en las mayores, de 14 a
98 % de sus celdas a 90 m o menos de terreno sin nieve; mediana 72 % el 29-10 y 54 % el 13-11). Son cambios del borde
de la nieve entre la referencia (3 a 5 días antes, en plena fusión de primavera) y la pasada, y el 13-11 quizás
también nubes tenues (nubosidad de catálogo 27,5 %); no se ven como pluma en color. La pluma que se ve en color es chica: el 29-10 cae
entera en el bloque del cráter, que la regla excluye; el 13-11 aporta un píxel con f ≈ 0,12 a 0,14. La regla de
máscara de S20b tenía el mismo defecto (su aviso lo dice: una versión anterior marcaba cambios de nieve), pero en sus
dos eventos la pluma dominaba la suma.

## 2. Qué se hace (sin cambiar la regla)

- Se corre `esperado`, `medir` y `posthoc` **tal como dice el criterio**, y el veredicto por la regla se informa tal
  cual.
- **Lectura escrita ahora:** como la población es borde de nieve y no pluma, ningún veredicto por la regla en estas
  pasadas se atribuye a la pluma.
  - Si da **SEÑAL** (M1 o M2), se lee como **alerta sobre la regla**: un cambio de superficie (nieve que se derrite
    entre los días base de octubre y la pasada) basta para dar D significativo, y eso obliga a revisar si parte de la
    señal de S20b puede venir de lo mismo. No cuenta como repetición de S20b.
  - Si da **SIN SEÑAL** o NO CONCLUYENTE, no dice nada de la pluma (no se midió la pluma), y como control dice que el
    borde de nieve no produce SEÑAL por sí solo en estos píxeles.
  - En los dos casos, la repetición de S20b queda **no decidida** por estas pasadas.
- **Variante informativa "núcleo" (no decide):** la misma f pero sólo con las componentes cuya celda más cercana está
  a ≤ 6 km del cráter (en S20b, la franja del 25-10 empezaba a 3,6 km y la bocanada del 08-11 a ~1 km). Resultado,
  ya calculado de la máscara: Σ f = 0,033 (29-10) y 0,159 (13-11), las dos bajo el mínimo de 0,20 de S20b: **SIN DATO**
  por la regla de S20b. Con 4 y 5 km también queda bajo 0,20; con 8 km pasa el mínimo pero ya entra borde de nieve.
  No se corre `medir` sobre la variante: el umbral de Σ f es de la regla y no se baja.

## 3. Qué queda para el informe

Por la regla: el veredicto de M1 y M2 en cada pasada. Por la enmienda: la pluma visible del 29-10 y del 13-11 es
demasiado chica o está demasiado pegada al cráter para la prueba 1 de S20b, así que **estas dos pasadas no repiten ni
contradicen S20b**. Para repetirla hace falta una pasada con pluma sobre nieve a más de 1 a 2 km del cráter (fuera del
bloque) y una referencia sin retroceso de nieve entre medio, o una máscara que no confunda las dos cosas (cambiar la
máscara es otra prueba, con su propio criterio).
