# H15 etapa 3: las tablas de VOLCAT sobre la huella de Nevados de Chillán. Informe, 21-11-2026

**Veredicto (regla del criterio): no separa, y es robusto a la pieza que falta.** Con las tablas de probabilidad de
VOLCAT y la cadena validada en Mauna Loa, la probabilidad IR de ceniza en los 769 píxeles que VOLCAT publicó de
Chillán llega a 0,5 en el 2,1 % (S0), 0,0 % (S1) y 1,6 % (S2) de la huella. Las tres bandas del cielo despejado de
11 µm caen en "no separa". La banda de tierra (±5 K) no lo cambia hacia "separa".

Criterio escrito y subido antes del primer número de la huella:
`C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\Goes\docs\own_volcat\lut_h15\etapa3_chillan\criterio_2026-11-21.md`
(commit 617f531; mientras no se fusione, en la copia de trabajo
`C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\Goes\.claude\worktrees\h15-etapa3-chillan-4cf4a6\docs\own_volcat\lut_h15\etapa3_chillan\`).

## 1. Para geólogo

**El fenómeno.** Entre el 13 y el 18-11 VOLCAT publicó cuatro eventos de Nevados de Chillán: objetos chicos, de 1 a
67 píxeles, casi siempre de uno o dos de ancho, pegados al cráter o derivando al ESE (H14). Nuestras quince pruebas
espectrales no los distinguían del mismo lugar sin pluma. Desde el 20-11 tenemos las tablas con que VOLCAT decide si
un píxel es ceniza, y entre el PR 75 y el PR 76 aprendimos a usarlas como VOLCAT en el caso público de Mauna Loa
(nube tenue, ε al nadir, nube negra en el punto frío, corrección de vapor). Faltaba aplicarlas a Chillán.

**Qué se midió.** En cada píxel publicado (`event_idx`) y en cinco controles del mismo cuadro con la misma BT11
(±0,5 K), lejos de la huella, se calculó la probabilidad de ceniza IR con esa cadena, agregándole lo que Chillán
pide y Mauna Loa no tenía: el cielo despejado llevado a la cota fina del terreno (la cumbre está a ~2,3 km en el
píxel; el GFS la pone a 1,5 a 1,9 km, H11) y superficie de tierra. Como el cielo despejado de 11 µm de VOLCAT no es público,
se repitió con tres versiones: el nuestro (S0), 0,86 K más frío (S1) y más frío junto a nube espesa (S2), que es lo
que VOLCAT hace en Mauna Loa.

**Lo que salió.** En las tres versiones, la probabilidad de la huella se queda pegada al valor de partida de VOLCAT.
VOLCAT parte suponiendo que sólo 1 de cada 1.000 píxeles es ceniza, y cada tabla multiplica esa apuesta según lo que
ve. Para llegar a 0,5 las tablas tienen que sumar unas mil veces a favor. En la huella de Chillán suman, en la
mediana, casi nada (factor 0,94): algunas empujan a ceniza (β(12/11) de 0,88, que sí es "de ceniza", y la ausencia
de nube inferior) y otras empujan en contra (β opaco y β(8,5/11)), y se anulan. La banda de vapor de 7,3 µm casi
no entra: en el 96 % de la huella la pluma es demasiado baja y tenue para verse en ella (regla R1). La mediana de
probabilidad en la huella es 0,0004 (S0), es decir, la apuesta inicial.

**Qué significa para la pregunta de fondo.** Las tablas reales de VOLCAT, usadas como VOLCAT en el único caso donde
pudimos comprobarlo, **tampoco ven estas plumas en el infrarrojo**. Eso cierra por el lado de las tablas lo que
nuestras quince pruebas venían diciendo, y calza con lo que el propio VOLCAT informa en sus archivos (firma de onda
larga ~0 en el 99 % de estos píxeles, H14). La decisión de publicar en Chillán no sale de la probabilidad IR por
píxel: sale de algo que estas tablas no tienen, que por lo visto hasta ahora es el objeto, el seguimiento entre
cuadros y, de día, los canales solares. Y no depende del cielo despejado de 11 µm que no pudimos reproducir: con
cielo despejado más frío la probabilidad baja todavía más.

Lo único que la levanta es un cielo despejado 5 K **más tibio** (banda de tierra, informativa): ahí la huella sube a
69 % sobre 0,5, pero los controles también suben, a 58 %. Es la sensibilidad conocida (cielo_sesgo vuelta 3: un ε(11)
más alto baja β y lo vuelve "de ceniza"), no una separación.

## 2. Comprobaciones previas

| Comprobación | Pide | Medido | Fuente |
|---|---|---|---|
| Huella en la ventana L1b | todos los píxeles | 769 de 769, a < 0,001 km de un píxel de la grilla | `resultados/inventario_cuadros.csv` |
| Georreferencia: BT11 nuestra − BT11 del archivo de evento | \|Δ\| mediano <= 0,2 K | +0,050 K (p5 +0,045, p95 +0,055) | `resultados/e3_georef.json` |
| Geometría del modelo de elevación | lat/lon a altura 0 vuelven a su píxel | error máximo 0,0006 px | `resultados/dem_ventana.json` |
| Probabilidad definida (punto 9) | informar | huella 98,6 % (S0), 97,9 % (S1), 98,3 % (S2), 76,9 % (−5 K), 100 % (+5 K) | `resultados/e3_metricas.json` |
| Pareo | informar | 769 de 769 con control; 768 a ±0,5 K, 1 a ±1,0 K; 3.836 controles | `resultados/e3_metricas.txt` |

La diferencia de 0,05 K es la esperada: GEOCAT convierte radiancia a BT con sus propios coeficientes (en Mauna Loa,
+0,08 K). La huella de `event_idx` está donde la L1b dice.

## 3. Números (variante V0, la que decide)

| Banda | F_h (P >= 0,5) | F_c | AUC pareado | IC 95 % del AUC | P mediana huella | Categoría |
|---|---|---|---|---|---|---|
| **S0** sin desfase | 0,021 | 0,006 | 0,662 | 0,627 a 0,873 | 4,5e-4 | no separa |
| **S1** −0,86 K | 0,000 | 0,001 | 0,419 | 0,386 a 0,521 | 1,8e-4 | no separa |
| **S2** −0,86 a −1,6 K | 0,016 | 0,003 | 0,489 | 0,348 a 0,547 | 2,6e-4 | no separa |
| tierra −5 K (informa) | 0,000 | 0,000 | 0,312 | 0,251 a 0,424 | 1,5e-3 | no separa |
| tierra +5 K (informa) | 0,694 | 0,576 | 0,601 | 0,301 a 0,637 | 0,83 | no concluyente |

Fuente: `resultados/e3_metricas.txt` y `e3_metricas.json`. "No separa" sale en las tres bandas por F_h < 0,20. El
AUC de S0 (0,66) indica que la huella queda algo más arriba que su control en el ranking, pero en probabilidades del
orden del prior: no llega nunca a lo que VOLCAT necesitaría para publicar. El IC del AUC es ancho y asimétrico
porque el evento del 14-11 16:30 aporta 728 de los 769 píxeles y el bootstrap remuestrea cuatro eventos.

**Por evento (S0):** 13-11 19:00 (15 píxeles con control) F_h 0, AUC 0,79; 14-11 12:40 (22) F_h 0, AUC 0,80; 14-11
16:30 (728) F_h 0,022, AUC 0,65; 18-11 10:10 (4) F_h 0, AUC 0,95. En S1 y S2 el AUC de los cuatro eventos baja a
0,40 a 0,50.

**Por tramo de εtot de la huella (S0):** < 0,1: 301 píxeles, F_h 0,010; 0,1 a 0,2: 464, F_h 0,028; 0,2 a 0,5: 4,
F_h 0. La huella vive en εtot 0,06 a 0,16 (p10 a p90), justo el tramo validado en Mauna Loa por el frente 1.

**Variantes informativas** (no deciden): V1 (más la tabla εtot × BTD del `.config` de 2025): F_h 0,016 / 0,001 /
0,013 en S0 / S1 / S2, AUC 0,72 / 0,55 / 0,59. V2 (sin 8,5 µm): F_h 0 en las tres. Ninguna cambia la categoría.

**Qué frena la probabilidad** (posterior, banda S0, `resultados/e3_diag_tablas.txt`; aproximación: sin la tabla de
β(8,5/11) opaco, que no se guardó). El prior vale −6,91 en log-odds; para llegar a 0,5 las tablas deben sumar
+6,91. Contribución mediana por tabla en la huella: εtot × β(12/11) −0,28; εtot × β opaco −0,61; multicapa bajo
+1,00 y medio +0,64 (R2, nube inferior ausente); β(12/11) × β(7,3/11) 0 (fuera por R1 en el 96 % de la huella);
β(12/11) × β(8,5/11) −0,60. Suma mediana −0,06. En los controles la suma mediana es −1,07.

**Entradas de la huella y del control (S0, mediana):** εtot 0,109 contra 0,165; β(12/11) 0,88 contra 0,98; cota
2.299 m contra 611 m; agua precipitable 0,91 cm contra 1,92 cm (corrección de vapor de β: ninguna en la huella,
+0,05 en parte de los controles). Fuente: `resultados/e3_pixeles.csv.gz`.

## 4. Advertencias

- **El control está más abajo.** Parear por BT11 en el mismo cuadro elige controles a 611 m de mediana para una
  huella a 2.299 m: a igual BT11, un píxel del valle es más nuboso que uno de la cumbre. Esto afecta al AUC, no al
  veredicto, que sale de que la huella misma casi nunca pasa 0,5.
- **Validación sólo de noche y sobre mar.** La cadena se reprodujo en Mauna Loa (GOES-17, VOLCAT v3.9.16, de noche,
  98,7 % mar). Chillán es GOES-19 operativo (v3r4), cordillera y casi todo de día. De día VOLCAT usa además tablas
  con canales solares (`IR only pixel level predictors` = 0 en el `.config`) que no reproducimos: el resultado habla
  de la probabilidad IR.
- **R2 en tierra empuja distinto** (×5,15 contra ×1,40 en mar, frente 1) y no se validó en tierra. Aquí aporta
  +1,64 en log-odds a la huella, a favor de ceniza, y aun así no alcanza.
- **β opaco y β multicapa son nuestros o supuestos.** β opaco como H11, no validado contra VOLCAT; β multicapa
  ausente en todo píxel. Si VOLCAT viera una nube inferior bajo la pluma, esas tablas entrarían distinto.
- **Cielo despejado en cordillera.** La corrección por cota se hizo con el perfil del GFS (como CLAVR-x), pero C2b no
  pudo validarla con cielo despejado, y H11 ya había visto error de terreno aquí. Por eso la banda de ±5 K: sólo
  un cielo 5 K más tibio sube la probabilidad, y la sube en la huella y en el control a la vez.
- **Cuatro eventos.** El evento del 14-11 16:30 pesa el 95 % de la huella.
- La huella son 769 píxeles; H14 contó 767 con el mismo `event_idx` (diferencia de conteo no revisada, 0,3 %).

## 5. Qué cambia

- **Para H15:** cerrada con resultado negativo robusto. Las tablas IR de VOLCAT, con la cadena de Mauna Loa, no dan
  probabilidad alta en la huella de Chillán, con cualquiera de los cielos despejados probados.
- **Para H14:** la refuerza. La parte espectral IR de VOLCAT no publica estos píxeles por sí sola; lo que decide está
  fuera de la probabilidad IR por píxel (objeto, seguimiento, canales solares de día).
- **Para el correo a Pavolonis:** la pregunta del cielo despejado de 11 µm pierde peso para Chillán (el veredicto no
  depende de ella). Gana la de qué hace publicar un objeto con probabilidad IR de píxel ~prior: la probabilidad de
  objeto, el seguimiento o las tablas de día.
- **Para el dashboard:** nada. No se tocó `src/` ni la app.

## 6. Archivos

Carpeta: `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\Goes\docs\own_volcat\lut_h15\etapa3_chillan\`.

- Scripts (`scripts\`): `e3_comun.py` (rutas), `e3_inventario.py` (huella en la ventana), `e3_bajar.py` (L1b y GFS),
  `e3_dem.py` (cota con paralaje), `e3_rt.py` (cielo despejado por cota, punto frío, agua precipitable),
  `e3_cadena.py` (pareo y probabilidad), `e3_medir.py` (métricas y veredicto), `e3_diag_tablas.py` (posterior).
- Salidas (`resultados\`): `inventario_cuadros.csv`, `dem_ventana.json`, `e3_georef.json`, `e3_pixeles.csv.gz` (una
  fila por píxel y banda, sin fila ni columna: la posición de la huella sale de archivos de acceso restringido), `e3_metricas.json`, `e3_metricas.txt`, `e3_diag_tablas.txt`.
- Fuera del repo: `D:\goes_cache\etapa3_chillan\` (L1b, GFS, nodos del modelo, modelo de elevación, inventario con
  datos de evento, `e3_pixeles_completo.csv` con posiciones). Los archivos de evento de VOLCAT se leyeron sin copiarlos.

## Reproducir

```powershell
python -I docs/own_volcat/lut_h15/etapa3_chillan/scripts/e3_inventario.py
```

```powershell
python -I docs/own_volcat/lut_h15/etapa3_chillan/scripts/e3_bajar.py gfs
```

```powershell
python -I docs/own_volcat/lut_h15/etapa3_chillan/scripts/e3_bajar.py l1b
```

```powershell
python -I docs/own_volcat/lut_h15/etapa3_chillan/scripts/e3_dem.py
```

```powershell
python -I docs/own_volcat/lut_h15/etapa3_chillan/scripts/e3_rt.py 10
```

```powershell
python -I docs/own_volcat/lut_h15/etapa3_chillan/scripts/e3_cadena.py
```

```powershell
python -I docs/own_volcat/lut_h15/etapa3_chillan/scripts/e3_medir.py
```
