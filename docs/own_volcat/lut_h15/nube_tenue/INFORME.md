# H15, frente 1: la regla de nube tenue de VOLCAT. Informe, 21-11-2026

**Veredicto.** Encontrada y validada en Mauna Loa. Con tres reglas, todas escritas en los atributos de la propia
tabla de VOLCAT, nuestra lectura reproduce la probabilidad de ceniza de VOLCAT en nube tenue: en los cuadros de
validación (6 a 10) sale exacta en el 99,96 % de los píxeles con εtot < 0,2 y en el 99,98 % entre 0,2 y 0,5, y pasa
las tres condiciones del criterio en ambos tramos. **La lectura de las tablas queda validada en nube tenue, en el
nivel A (con el ε y los β de VOLCAT) y sobre mar.** No queda lista para aplicarla a Chillán: falta lo mismo que
antes en el nivel B (nuestro ε) y falta comprobarla en tierra (§4).

Criterio subido antes de validar: `criterio_2026-11-21.md` (commit f5f97d5, empujado al remoto antes de correr
`nt_validar.py`). Rutas completas en §6.

## 1. Para geólogo

**El fenómeno.** VOLCAT decide si un píxel es ceniza comparando cómo se ve la nube en varias bandas infrarrojas
(11, 12, 8,5 y 7,3 µm) contra dos álbumes de referencia, uno de ceniza y otro de nube meteorológica. Con nube
espesa, todas las bandas "ven" la nube y basta con multiplicar lo que dice cada álbum: eso ya lo reproducíamos.
Con nube tenue (una pluma delgada, como las de Chillán) algunas bandas casi no ven la nube, y la pregunta era qué
hace VOLCAT entonces.

**Lo que hace (tres reglas, una sola idea: un predictor sólo vale si la nube se ve en esa banda).**

1. **La banda de vapor (7,3 µm) se descarta si la nube casi no aparece en ella.** Si la emisividad de la nube en
   7,3 µm es menor que 0,1, VOLCAT no usa la comparación 7,3/11. Una pluma baja queda bajo casi todo el vapor de
   agua de la atmósfera, y en 7,3 µm su señal es ruido. El umbral está escrito en la tabla (`MIN_73EMISS_TOT`).
2. **"No hay nube debajo" es un dato, no un hueco.** VOLCAT calcula también la razón de emisividades suponiendo que
   bajo la pluma hay una nube baja o media. Cuando no encuentra esa nube inferior, no descarta esas dos
   comparaciones: las evalúa en el primer casillero de la tabla (el valor de relleno, que queda en el borde). En
   nube muy tenue sobre mar eso suma a favor de ceniza: multiplica la razón de probabilidades por 11 con emisividad
   entre 0,03 y 0,10.
3. **La banda de 8,5 µm se descarta con nube tenue y β ambiguo.** Con emisividad total bajo 0,1 y razón β(8,5/11)
   entre 1,05 y 2,0, VOLCAT no usa las dos comparaciones de 8,5 µm. En esa franja el valor no distingue ceniza de
   SO₂ o de la superficie. Ambos números están en la tabla (`BETA8511_TOT_MAX_8511_PREDICTORS`, `_MIN_`).
   Hallazgo adicional, posterior a la validación: en el **primer** cuadro de la serie la regla de 8,5 µm es otra
   (se descarta si la emisividad en 7,3 µm es menor que 0,05, otro umbral de la tabla). La configuración de VOLCAT
   tiene justamente una opción "uso restringido de 8,5 µm cuando no hay datos temporales", y el primer cuadro no
   tiene cuadro anterior.

**Lo que se probó.** Las reglas se buscaron mirando sólo los cuadros 1 a 5 (09:16 a 09:36 UTC) del caso público de
Mauna Loa (GOES-17, 28-11-2022, de noche, sobre mar), donde VOLCAT publica su probabilidad píxel a píxel. Se
fijaron por escrito y se midieron en los cuadros 6 a 10 (09:41 a 10:01), que no se habían mirado.

**Veredicto y qué significa.** Las reglas pasan con holgura en los dos tramos de nube tenue: ahí la parte
"tablas" de VOLCAT ya no es una caja negra. Para la pregunta de fondo (por qué VOLCAT ve plumas de Chillán que
nosotros no) esto deja una pista concreta, todavía sin probar: en tierra, con emisividad entre 0,10 y 0,20 (la
huella de Chillán tenía mediana 0,16), la regla 2 multiplica la razón de probabilidades de ceniza por 5,2 cuando
VOLCAT no encuentra nube debajo. Nuestras quince pruebas no tenían nada parecido. Pero ese número sale de la tabla
de tierra, que en Mauna Loa no se pudo validar (98,7 % del dominio es mar), y aplicarlo a Chillán requiere además
nuestro propio ε, que todavía no coincide con el de VOLCAT (frente 2).

## 2. Cómo se encontró (cuadros 1 a 5, nivel A)

Punto de partida: las 7 tablas IR sin la de εtot × BTD (etapa 2). "Exacto" es |logit nuestro − logit VOLCAT| < 0,001
en píxeles no saturados.

- **Tramo 0,2 a 0,5.** De los no exactos, el 95,5 % se arregla sólo con omitir β(12/11) × β(7,3/11)
  (`nt_explorar1.txt`). ε73 = 1 − (1 − εtot)^β(7,3/11) separa sin error: los evaluados con esa tabla tienen ε73 de
  0,1000 a 0,379, los evaluados sin ella de 0,0296 a 0,1000 (`nt_explorar2.txt`). Con R1, el tramo pasa de 72,9 % a
  98,8 % exacto (`nt_explorar8.txt`).
- **Tramo < 0,2.** Agrupando los píxeles por valor de P_VOLCAT, dentro de cada grupo εtot, β total, β opaco y β
  multicapa caen en un solo casillero y β(8,5/11) recorre 8 a 15: ahí no entran las tablas de 8,5 µm
  (`nt_explorar4.txt`). Sin ellas, VOLCAT menos nuestra suma es constante por casillero de εtot: +2,4089 en 0,03 a
  0,10 y −0,0985 en 0,01 a 0,03, igual para cualquier β (`nt_explorar5.txt`). Esa constante es la suma de las dos
  tablas multicapa en su primer casillero de β: 1,205 + 1,204 y −0,071 − 0,028 (`nt_explorar7.txt`). Lo que no
  funcionó en este tramo: correr el casillero de εtot (0 % exacto) o el de β de una tabla (0 %), omitir subconjuntos
  de tablas (0,5 %), reemplazar β por la relación lineal con el sesgo de BTD (`COEFF_BETA1112_TOT_FCT1`; su
  casillero no sirve en ningún píxel) (`nt_explorar1.txt`, `nt_explorar3.txt`). La búsqueda bruta combinada (εtot ×
  β total × subconjunto) llega a 24,7 %, pero sólo llevando εtot al casillero 0,5 a 0,9, sin sentido físico
  (`nt_explorar2.txt`).
- **Tablas de 8,5 µm.** Con εtot < 0,1 y 1,05 < β(8,5/11) < 2,0: 19.286 píxeles evaluados sin 8,5 contra 8 con
  (`nt_explorar11.txt`). Quedaba una mezcla sin separar (2.526 con / 864 sin fuera de la franja; 1.444 con / 722
  sin entre 0,1 y 0,2), declarada como residuo en el criterio. Después de validar se vio que está toda en el cuadro
  09:16 (§3).

## 3. Validación (cuadros 6 a 10, nivel A)

Regla NT = R1 + R2 + R3, idéntica a la del criterio. 502.234 píxeles con probabilidad válida (`nt_validacion.txt`).

| Tramo de εtot | Píxeles | P_VOLCAT ≥ 0,5 | \|ΔP\| ≤ 0,05 (pide ≥ 90 %) | κ (pide ≥ 0,90) | Recuperados (pide ≥ 90 %), IC 95 % | Exacto | Cumple |
|---|---|---|---|---|---|---|---|
| **< 0,2** | 29.674 | 494 | 100,00 % | 1,0000 | 100 % (99,2 a 100) | 99,96 % | **sí** |
| **0,2 a 0,5** | 147.709 | 5.150 | 100,00 % | 1,0000 | 100 % (99,9 a 100) | 99,98 % | **sí** |
| ≥ 0,5 (no decide) | 324.851 | 21.431 | 99,96 % | 0,9987 | 99,99 % | 99,00 % | sí |
| todo (no decide) | 502.234 | 27.075 | 99,98 % | 0,9989 | 99,99 % | 99,38 % | sí |

Comparación en los mismos cuadros (`nt_validacion.txt`):

| Variante | < 0,2: \|ΔP\| / κ / recuperados | 0,2 a 0,5: \|ΔP\| / κ / recuperados |
|---|---|---|
| base, 7 tablas | 96,9 % / 0,844 / 94,9 % | 95,6 % / 0,724 / 100 % |
| sólo R1 | 96,9 % / 0,844 / 94,9 % | 100 % / 1,000 / 100 % |
| sólo R2 | 96,6 % / 0,620 / 100 % | 95,6 % / 0,724 / 100 % |
| R1 + R2 | 96,6 % / 0,620 / 100 % | 100 % / 1,000 / 100 % |
| **NT = R1 + R2 + R3** | **100 % / 1,000 / 100 %** | **100 % / 1,000 / 100 %** |

R1 resuelve el tramo 0,2 a 0,5 por sí sola; en < 0,2 hacen falta R2 y R3 juntas (R2 sola empeora κ porque deja
dentro las tablas de 8,5 µm que VOLCAT no usa ahí).

**Comprobación por cuadro** (posterior, `nt_por_cuadro.txt`): con NT, los nueve cuadros 09:21 a 10:01 dan de 99,91
a 100 % exacto en < 0,2 y de 99,97 a 100 % en 0,2 a 0,5. El cuadro 09:16 da 69,4 % y 94,0 %: ahí están los 1.586 +
584 píxeles no exactos que se arreglan quitando 8,5 µm. En ese cuadro la regla es "omitir 8,5 µm si ε73 < 0,05 o
falta" (`EMISS10_TOT_MIN_8511_PREDICTORS`): separa 100 % y 100 % (`nt_cuadro1.txt`). Es compatible con la opción de
configuración de 8,5 µm "cuando no hay datos temporales" (INFERIDO: es el primer cuadro de la corrida; con un solo
primer cuadro no se puede validar aparte).

**Lo que queda sin explicar.** Con εtot ≥ 0,5, el 1 % de los píxeles no saturados no sale exacto en ningún cuadro
(98,9 a 99,2 %, `nt_por_cuadro.txt`); no afecta las métricas (κ 0,9987) y no es nube tenue. Ya estaba en la etapa 2.

**Nivel B** (nuestro εtot y β con el cielo despejado de VOLCAT, informativo): con NT sigue sin reproducir, κ 0,166
en < 0,2 y 0,126 en 0,2 a 0,5 (`nt_validacion.txt`). La regla no arregla el ε; eso es el frente 2.

## 4. Qué falta para Chillán (la regla NO está lista para aplicar allá)

1. **Nuestro ε y β.** Chillán usaría nuestro εtot, β(12/11), β(7,3/11) y β(8,5/11). En Mauna Loa, con ellos, la
   probabilidad no se reproduce (nivel B, κ 0,13 a 0,17). Sin el cielo despejado corregido (frente 2), las reglas
   se aplicarían sobre entradas equivocadas.
2. **Tierra.** Las reglas se encontraron y validaron sobre mar (98,7 % del dominio). R1 y R3 son umbrales sobre
   ε y β, independientes de la superficie; R2 en cambio usa la tabla de tierra, que en tierra empuja distinto: con
   εtot entre 0,10 y 0,20, multiplica la razón de odds por 5,15 en tierra contra 1,40 en mar (`nt_r2_empuje.txt`).
   Sin un caso de validación en tierra, ese 5,15 es una lectura, no un resultado.
3. **β multicapa.** R2 depende de si VOLCAT encontró nube inferior (`lower_cloud_idx`). Nosotros no calculamos β
   multicapa; para Chillán habría que saber, píxel a píxel, si VOLCAT ve una nube baja bajo la pluma.
4. **Versión.** Mauna Loa es VOLCAT v3.9.16. El `.config` de 2025 (GOES-R) pone la restricción de 8,5 µm en
   "no usar en absoluto" y activa la tabla εtot × BTD, que v3.9.16 no usa. En GOES-19 operativo podrían variar R3 y
   la base.

## 5. Para el correo a Pavolonis (si se envía)

Las preguntas sobre la regla de nube tenue se reducen a confirmaciones: (a) que la tabla β(12/11) × β(7,3/11) se
omite con ε(7,3) < `MIN_73EMISS_TOT`; (b) que un β multicapa ausente entra como relleno en el primer casillero, y si
eso es intencional en tierra; (c) la regla de 8,5 µm con y sin datos temporales, y cuál rige hoy en GOES-19; (d) si
la tabla εtot × BTD entra en la versión operativa. Las del cielo despejado (sesgo local de 12 px) siguen abiertas y
son del frente 2.

## 6. Archivos

Carpeta: `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\Goes\docs\own_volcat\lut_h15\nube_tenue\`
(en esta rama; mientras no se fusione, en la copia de trabajo
`C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\Goes\.claude\worktrees\h15-nube-tenue-4e46a6\docs\own_volcat\lut_h15\nube_tenue\`).

- `criterio_2026-11-21.md`: criterio, subido antes de validar.
- `scripts\nt_comun.py` (entradas de nivel A, contribución por tabla), `scripts\nt_regla.py` (motor con R1, R2,
  R3), `scripts\nt_explorar1.py` a `nt_explorar11.py` (exploración, cuadros 1 a 5), `scripts\nt_validar.py`
  (decide), `scripts\nt_por_cuadro.py`, `scripts\nt_cuadro1.py`, `scripts\nt_r2_empuje.py` (posteriores).
  Usan `..\scripts\lut_volcat.py` y `..\scripts\etapa2_validar.py` de la etapa 2.
- `resultados\`: `nt_explorar1.txt` a `nt_explorar11.txt`, `nt_validacion.txt`, `nt_validacion.json`,
  `nt_por_cuadro.txt`, `nt_cuadro1.txt`, `nt_r2_empuje.txt`.
- Fuera del repo (sin cambios): `D:\goes_cache\lut_h15\lut_pixel.npz`, `D:\goes_cache\lut_h15\ml\`,
  `D:\goes_cache\volcat_test_mauna_loa\npz\`. Nada de SSEC al repo.

## Reproducir

```bash
python -I docs/own_volcat/lut_h15/nube_tenue/scripts/nt_validar.py
```
