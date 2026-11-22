# Auditoría corta de la cadena S15 (PR 75 a 83): supuestos de régimen, observable y controles

Fecha: 22-11-2026, 03:00 a 03:36 (hora del servidor, UTC-3). Base medida: `origin/main` = `2699b20`.
Auditor: Claude Opus 5.5 (esfuerzo bajo, tarea 4c de S16). Verificador con contexto limpio: Claude Sonnet (subagente
que recibió sólo títulos y ubicaciones, no el razonamiento; escribió sus caminos de error antes de releer, 03:28).
Informe del verificador (fuera del repo): `D:\goes_notas\s16\auditoria\verificador.md`
(sha256 `1af7dfc71fe8fbe6eb89a837c52ea9d50655bfaa8aa355b36bea4f40f78431f6`); lista que recibió:
`D:\goes_notas\s16\auditoria\lista_para_verificador.md`. Línea de tiempo de commits:
`D:\goes_notas\s16\auditoria\timeline.txt`.

**Qué no miró esta auditoría.** No se relanzó ninguna cadena pesada (S3, GFS, RT). No se leyeron `nt_regla.py` ni
`N.contrib` línea a línea. No se comprobaron las rutas de `D:` que cita `INVENTARIO_REPRODUCIBILIDAD.md` (el intento
quedó mal parseado: SIN DATO). PR 78, 80 y 81 son de infraestructura y no tienen veredictos que auditar.

## En una pantalla

1. **Ningún veredicto de la cadena cambia** con lo que sobrevivió a la verificación: la huella de Chillán queda en
   probabilidades del orden del prior en la etapa 3 y unas diez décadas bajo el umbral en H16, y H17 no llega a las
   varas de su criterio. Lo que cambia es **qué dicen esos "no separa"**: son "no separa en IR, tierra, de día, con
   nuestro ε y β", no "las tablas de VOLCAT no ven esto".
2. **Supuesto de régimen nuevo y más grave que el de día:** el cielo despejado. Los desfases S1 y S2 que dan el
   "robusto" se midieron sobre mar y contra `geocatRTM`, pero se suman a nuestro cielo de cordillera; son todos hacia
   el frío, así que el test de robustez no podía fallar en esa dirección; y la etapa 3 y H17 discrepan sobre si la
   huella tiene nube (H-2, H-3).
3. **Nivel B nunca aprobado y presentado como "cadena validada".** La etapa 3 y H16 aplican a Chillán nuestro ε y β,
   que en Mauna Loa reprodujo a VOLCAT con κ 0,31 (H-4).
4. **Sin control positivo en el régimen de Chillán** en ninguna prueba; en H16 ni siquiera en Mauna Loa hubo un objeto
   en el umbral que decide (P ≥ 0,8) (H-5).
5. Criterio antes del resultado: **cumple en las seis carpetas** (verificado limpio, con un matiz).

## 1. Censo de cobertura

Régimen del instrumento validado (lo que valió para todas las pruebas sobre tablas): Mauna Loa, GOES-17, 28-11-2022,
de noche, 98,7 % mar, cenit satelital 20 a 37° (casi todo 20 a 31°), VOLCAT v3.9.16, nivel A (ε y β de VOLCAT).
Régimen de Chillán: GOES-19, VOLCAT v3r4 (config 2025), 13 a 18-11-2026, cordillera con nieve, cenit satelital ~43°,
cenit solar 18,8 a 82,7° en los cuatro cuadros de arranque (todos "día" para VOLCAT, que corta en 85°).

| PR | Prueba | Datos (régimen) | Instrumento validado en | Control + medido | Control − medido | Criterio antes (commit → resultado) | Huella `event_idx` / pareo BT11 |
|---|---|---|---|---|---|---|---|
| 75 | Reglas de nube tenue R1 a R3 | Mauna Loa, cuadros 6 a 10 | mismo régimen, cuadros 1 a 5 | sí (494 y 5.150 píxeles con P_VOLCAT ≥ 0,5) | sí (línea base de 7 tablas, falla) | sí, f5f97d5 11:49 → af0e8ca 11:52 | no aplica |
| 76 | Cielo despejado y nube negra, vueltas 1 a 6 | Mauna Loa | mismo | nivel A sí | sí | vueltas 1 a 4 sí; 5 y 6 sin criterio (declaradas exploración) | no aplica |
| 77 | LRC y vecindad | Mauna Loa, cuadros 1 a 5 | no hubo candidata | no aplica | no aplica | sin criterio por diseño (declarado) | no aplica |
| 78 | Inventario | sin prueba | | | | | |
| 79 | Etapa 3: tablas sobre la huella | Chillán, día, tierra, ~43°, v3r4 | Mauna Loa nivel A; nivel B no aprobado | **no** | controles pareados por BT11 (a otra altura) | sí, 617f531 16:13 → cadena.log 16:37 → 4ef2635 16:41 | sí / sí |
| 80, 81 | Rutas de import y de insumos | sin prueba | | | | | |
| 82 | H16: probabilidad de objeto | Chillán, 60 cuadros, día | Mauna Loa nivel A (DIAGS1), 126 objetos | **no** (máximo VOLCAT 0,545; ninguno ≥ 0,8) | controles pareados por BT11 | sí, 22c46b1 21:26:03 → 4a5252b 21:27:47 → 6564649 21:32 | sí / sí |
| 83 | H17 etapa 1: calor 3,9 µm | 20-10 a 19-11, día y noche | sin validación previa | 3 cuadros VOLCAT, todos de día o amanecer | Antuco y Longaví | sí, e1cf1dd 21:50 → logs 22:39 a 22:55 → 75ed843 22:57 | no aplica |
| 83 | H17 etapa 2: objeto anclado | 127 positivos (60 de evento, 67 de PNG), 1.380 negativos | sin validación previa | sí (por cuadro) | sí (cuadros limpios) | sí (mismo) | por píxel sí / sí; por cuadro mezcla PNG |

## 2. Hallazgos verificados (lo peor primero)

Gravedad 1 a 5 (5 = el veredicto científico de la prueba podría cambiar), la del verificador. Ninguno llegó a 5.

### H-1. "Robusto a la pieza que falta": las bandas que deciden sólo pueden bajar, y salen de mar · CONFIRMADO · 4

- `docs/own_volcat/lut_h15/etapa3_chillan/criterio_2026-11-21.md:65-76` y `:98-104`;
  `docs/own_volcat/lut_h15/etapa3_chillan/INFORME.md:3-6` y `:40-46`;
  `docs/own_volcat/lut_h15/etapa3_chillan/resultados/e3_metricas.txt:13`; `docs/own_volcat/h3_h7/scripts_h3/rt.py:31`.
- **Qué pasa.** S0 (δ = 0), S1 (−0,86 K) y S2 (−0,86 a −1,6 K) son todas hacia el frío, medidas en Mauna Loa sobre
  mar. Como S0 ya daba "no separa" y un cielo más frío baja la probabilidad, la regla "las tres en la misma categoría"
  no podía fallar. La única banda tibia, +5 K (la incertidumbre de cielo despejado que VOLCAT se asigna sobre tierra),
  quedó como informativa y sí cambia de categoría (V0: F_h 0,694, F_c 0,576, "no concluyente"). Además sólo se mueve
  C14: el cielo de 12, 8,5 y 7,3 µm usa emisividad de superficie fija (0,97 / 0,95 / 0,97) para mar, roca y nieve, y
  ninguna banda la varía.
- **Qué significa.** El veredicto "no separa" de S0 sigue en pie; lo que no está probado es que "no depende del cielo
  despejado". En tierra la incertidumbre de ese cielo es simétrica y de 5 K, y el lado tibio no decide.
- **Cómo reproducir.** Leer `e3_metricas.txt` línea 13 contra `INFORME.md:3` y `:41-42`.

### H-2. Los desfases S1 y S2 se midieron contra `geocatRTM` y se suman a nuestro cielo · CONFIRMADO · 4

- `docs/own_volcat/lut_h15/cielo_sesgo/scripts/vuelta5_forma.py:118`; `docs/own_volcat/lut_h15/cielo_sesgo/INFORME.md:96-100`;
  `docs/own_volcat/lut_h15/cielo_lrc/INFORME.md:14-17`; `docs/own_volcat/lut_h15/etapa3_chillan/scripts/e3_cadena.py:105-117`;
  `docs/own_volcat/lut_h15/etapa3_chillan/INFORME.md:25-26`.
- **Qué pasa.** El desfase de Mauna Loa es "cielo de 11 µm que usa VOLCAT menos `geocatRTM`". En Chillán se suma a
  nuestro modelo de H3 llevado a la cota, que nunca se comparó con `geocatRTM` en Chillán (C2b no concluyente). El
  INFORME presenta S1 y S2 como "lo que VOLCAT hace en Mauna Loa". La forma de S2 depende además de nuestra
  εtot ≥ 0,5, no de la de VOLCAT.
- **Qué significa.** S1 y S2 no son "el cielo de VOLCAT": son nuestro cielo corrido una cantidad medida contra otro
  modelo y otra superficie.

### H-3. La etapa 3 y H17 discrepan sobre si la huella tiene nube · números CONFIRMADOS, lectura PLAUSIBLE · 4

- `docs/own_volcat/lut_h15/etapa3_chillan/INFORME.md:80-94` y `resultados/e3_pixeles.csv.gz`;
  `docs/own_volcat/h17_regla_propia/INFORME.md:58-64`; `docs/own_volcat/h17_regla_propia/resultados/h17_pluma_resultado.txt:38-39`.
- **Qué pasa.** Con el cielo modelado, la etapa 3 le da a la huella εtot mediano 0,109 (ε11 oblicuo 0,146, BT11
  280,45 K, recalculado por el verificador desde el CSV), es decir, nube. Con una línea base temporal del mismo píxel,
  H17 la encuentra 1,28 K **más tibia** que su cielo despejado, es decir, sin nube. Ninguno de los dos informes lo
  reconcilia (H17 dice que "calza con todo lo anterior").
- **Lectura (PLAUSIBLE, estimación a mano del verificador con nube a ~210 K).** Si las dos cosas valen, el cielo
  modelado de la cumbre está unos 9 K tibio, y el εtot de 0,06 a 0,16 y el β(12/11) de 0,88 "de ceniza" de la huella
  serían en buena parte residuo de cielo y no medición de pluma. Es coherente con el error de terreno de H11 y con que
  C2b no validó la corrección por cota. Entonces la frase "la huella vive en εtot 0,06 a 0,16, justo el tramo validado
  en Mauna Loa" (`INFORME.md:81`) empareja el régimen por el número, no por el fenómeno (patrón 7 de la guía), y la
  banda que faltaba probar era más fría que −1,6 K, no +5 K.
- **Qué no cambia.** El "no separa" de la etapa 3 sobrevive: con o sin nube, P queda en el prior.

### H-4. Nivel B no aprobado, llamado "cadena validada en Mauna Loa" · CONFIRMADO · 3

- `docs/own_volcat/lut_h15/etapa3_chillan/INFORME.md:3-4` y `:36-37`; `docs/own_volcat/lut_h15/etapa3_chillan/criterio_2026-11-21.md:5`;
  `docs/own_volcat/lut_h15/nube_tenue/resultados/nt_validacion.txt` (filas "nivel B, NT": κ 0,166 / 0,126 / 0,413 /
  0,310, los cuatro tramos "no"); `docs/own_volcat/lut_h15/cielo_sesgo/INFORME.md:528-541` y `:565-567` ("Para
  Chillán: el cielo corregido no está listo"); `docs/own_volcat/h16_objeto/scripts/h16_validar.py:1-4` y `:38-40`.
- **Qué pasa.** Lo validado en Mauna Loa es la lectura de las tablas con el ε y los β **de VOLCAT** (nivel A). Con los
  nuestros (nivel B, lo que se aplica en Chillán) no se reprodujo. La etapa 3 no menciona el nivel B en ninguna parte
  (0 coincidencias de "nivel B" y "no aprob" en su INFORME y criterio). H16 validó su motor con DIAGS1 de VOLCAT y lo
  aplicó a la cadena propia.
- **Atenuante (SOSPECHA, signo neto sin medir).** Sobre mar, nuestro β en nube tenue sale más bajo que el de VOLCAT,
  lo que empuja a ceniza y haría más fuerte un "no separa"; pero un ε(11) 0,015 más alto multiplica los píxeles de P
  alta (`cielo_sesgo/INFORME.md:251-261`).

### H-5. Ningún control positivo en el régimen de Chillán · CONFIRMADO · 4 (atenuado a 3 por el margen de H16)

- `docs/own_volcat/lut_h15/etapa3_chillan/criterio_2026-11-21.md` (sin "positivo"); `docs/own_volcat/h16_objeto/INFORME.md:95-106`;
  `docs/own_volcat/h16_objeto/resultados/validacion_objetos.csv`; `docs/own_volcat/h16_objeto/criterio_2026-11-21.md:62-67`.
- **Qué pasa.** Ninguna prueba midió que la cadena dé probabilidad alta sobre ceniza real en tierra, de día, a ~43° y
  2 km. En H16, entre los 126 objetos de validación, el máximo de VOLCAT es 0,545 y ninguno llega a 0,8, que es el
  umbral con que se decide Chillán: se validó la mecánica en log-odds (mediana 0,026 décadas), no la sensibilidad en
  el umbral. El INFORME declara lo del 0,5 pero no que el 0,8 nunca se alcanzó.
- **Atenuante.** En H16 la huella queda unas diez décadas bajo el umbral; un error de una década no lo cierra.

### H-6. El control pareado por BT11 está en el valle; H16 y H17 no lo declaran · CONFIRMADO EN PARTE · 3

- `docs/own_volcat/lut_h15/etapa3_chillan/INFORME.md:92-100` (sí declara: 2.299 m contra 611 m, agua precipitable 0,91
  contra 1,92 cm); `docs/own_volcat/h16_objeto/INFORME.md:41-46` y `:121-131`; `docs/own_volcat/h17_regla_propia/INFORME.md:58-64`.
- **Qué pasa.** A igual BT11, un píxel del valle tiene que ser más nuboso que uno de la cumbre. H16 atribuye a la
  rugosidad de la cumbre el −2,02 de la tabla de desviación de BT11 contra −0,22 del control; H17 lee el −12,5 K de sus
  controles como "son nube". Las dos cosas las produce en parte el pareo mismo. Además la corrección de vapor de β entra
  en parte de los controles y no en la huella (cambia β por altura, no por pluma).
- **Qué no cambia.** Los veredictos (salen de la huella sola: F_h, P máxima, ΔBT11 de la huella). Lo que queda
  ininterpretable son los AUC (0,66 en la etapa 3, 0,78 en H16) como "la huella se ve algo más ceniza que su control".

### H-7. La variante operativa de 2025 no se calculó; la celda V1 × +5 K no está en el INFORME · CONFIRMADO EN PARTE · 2

- `docs/own_volcat/lut_h15/etapa3_chillan/scripts/e3_cadena.py:130-141`; `resultados/e3_metricas.txt:14`;
  `docs/own_volcat/lut_h15/etapa3_chillan/INFORME.md:83-84`; `docs/own_volcat/lut_h15/LECTURA_LUT.md:74-81` y `:103-106`.
- **Qué pasa.** V0 (la que decide) reproduce v3.9.16. El `.config` de 2025 corresponde a V1 y V2 **juntas** (tabla
  εtot × BTD encendida y 8,5 µm fuera), combinación que el script no calcula. V1 × +5 K da F_h 0,497 contra F_c 0,149
  (IC de ΔF 0,055 a 0,388), a 0,003 del 0,50 de "separa", y el INFORME sólo informa V1 en S0 a S2.
- **Recalculado por el verificador** (suma en logit sobre `e3_pixeles.csv.gz`; reproduce los F_h de V0 y V1 del
  archivo): la combinación operativa da F_h 0 en S0, S1 y S2, y 0,005 contra 0,011 en +5 K. El veredicto no cambia; el
  hueco es de transparencia. Ojo: el eje de BTD de esa tabla está sin validar (`LECTURA_LUT.md:74-81`).

### H-8. H17: el POD titular mezcla dos clases de positivo, y una no aporta ninguna detección · CONFIRMADO · 2 (nuevo del verificador)

- `docs/own_volcat/h17_regla_propia/resultados/pluma_por_cuadro.csv` (columnas `pos`, `evento`, `det_decide`);
  `docs/own_volcat/h17_regla_propia/INFORME.md:110-116`; `docs/own_volcat/eventos_h14/INFORME_H14.md:179-190`.
- **Qué pasa.** De 127 positivos, 60 son cuadros de evento (`event_idx`) y 67 vienen sólo del PNG de H9, que H14
  pidió no reutilizar sin revisar su proyección. Las 17 detecciones están todas en los 60 de evento; los 67 de PNG dan
  0 (comprobado también por el auditor). Con positivos `event_idx` el POD es 17/60 = 0,28, no 0,134.
- **Qué no cambia.** Sigue bajo 0,5 y el FAR (0,066) sobre 0,05: "no separa del fondo" se mantiene.

### H-9. Normalización al nadir aplicada a ~43°, fuera de lo medido en Mauna Loa · CONFIRMADO EN PARTE · 2

- `docs/own_volcat/lut_h15/cielo_sesgo/INFORME.md:238-239` y `:542-548`; `docs/own_volcat/lut_h15/etapa3_chillan/criterio_2026-11-21.md:36`.
- **Qué pasa.** En Mauna Loa los píxeles tenues van de 20 a 37° (589 entre 34 y 37°), y el exponente efectivo depende
  del ángulo (0,88 a 20-28°; el texto dice 1,02 a "34 a 45°", inconsistente con la tabla, que llega a 37°). Chillán
  está a ~43° (cálculo geométrico del auditor y del verificador). La etapa 3 no declara la extrapolación.
  Sensibilidad medida por el verificador: εtot mediano de la huella 0,096 / 0,108 / 0,118 con exponente 0,88 / 1,0 /
  1,1. No cambia el veredicto.

### H-10. H16 apoya "las tablas de día no sumarían diez décadas" en un AUC de señal cruda por píxel · CONFIRMADO EN PARTE · 2

- `docs/own_volcat/h16_objeto/INFORME.md:137-140`; origen en `docs/own_volcat/POR_QUE_VOLCAT_VE_Y_NOSOTROS_NO.md:194-216`.
- **Qué pasa.** El AUC 0,50 viene de tres señales crudas por píxel sobre huella de PNG, no de las tablas de día de
  VOLCAT ni a nivel de objeto. El propio INFORME agrega "pero no está medido"; el hallazgo es que el argumento no sirve
  de apoyo, no que el informe lo oculte.

## 3. Lo que esto suma al supuesto del día

El supuesto ya conocido (validar de noche y aplicar de día) tiene, según esta auditoría, tres hermanos con la misma
forma, todos del tipo "se validó en un régimen y se aplicó en otro sin decirlo en el titular":

1. **Cielo despejado de mar a cordillera** (H-1, H-2, H-3): la pieza que más mueve el resultado. Es el de más peso.
2. **Nivel A a nivel B** (H-4): se validó la lectura de las tablas con las entradas de VOLCAT y se aplicó con las
   nuestras.
3. **Ángulo y versión** (H-7, H-9): de 31° a 43° y de v3.9.16 a v3r4; medidos, pesan poco.

## 4. Pruebas de campo que salen de aquí (no se hicieron)

| ID | Qué mirar | Qué decide | Qué desbloquea |
|---|---|---|---|
| C-1 | Cielo despejado modelado de la cumbre contra la base temporal de H17, en los mismos píxeles y cuadros | Si la εtot de la huella es pluma o residuo de cielo (H-3) | Leer bien todo lo hecho sobre tablas en Chillán |
| C-2 | Un control positivo en régimen Chillán: un evento GOES-19 con ceniza clara sobre los Andes, de día, que VOLCAT publique | Si la cadena puede dar P alta en ese régimen (H-5) | Que un "no separa" signifique algo |
| C-3 | Banda de cielo despejado simétrica (±) y también en 12 µm, decidiendo | Si "robusto" vale (H-1) | Reescribir el titular de la etapa 3 o no |

## 5. Verificado limpio

- **Criterio antes del resultado** en las seis carpetas (contra `git log` de cada carpeta y mtimes de `D:\goes_cache`):
  ningún criterio se modificó después de su commit. Matiz: la fecha de commit prueba orden de publicación, no de
  cálculo; en nube_tenue hay 3,5 min entre criterio y resultado y en H16 1 min 44 s, con exploración previa declarada;
  en la etapa 3 las bajadas y el inventario (16:08 a 16:10) son anteriores al criterio, la cadena (16:37) posterior;
  H17 declara las variantes informativas agregadas después de la primera corrida.
- **Huella = `event_idx` y pareo por BT11** en las tres pruebas por píxel sobre Chillán (etapa 3, H16, H17 por píxel),
  contra los criterios respectivos. La excepción es la parte por cuadro de H17 (H-8).
- **Cifras ancladas.** Etapa 3: la tabla de §3 contra `e3_metricas.txt` (coincide). H16: tabla §4 contra
  `chillan_metricas.txt` (coincide). Nube tenue: tablas §3 contra `nt_validacion.txt` (coinciden). H17: tablas contra
  `h17_calor_resultado.txt` y `h17_pluma_resultado.txt` (coinciden); el "48 % desde el 24-10" y el "0,5 % del 20 al
  23-10" no están en el `.txt` pero se reproducen desde `calor_por_cuadro.csv` (0,4803 en 533 cuadros; 0,005 en 199).
- **Georreferencia de la huella en la etapa 3**: BT11 nuestra menos la del archivo de evento, +0,050 K
  (`e3_georef.json`), declarado y coherente.

## 6. Sin dato y seguimientos

- SIN DATO: existencia de las rutas de `D:` del inventario; contenido de `N.contrib` (la suma en logit de H-7 se
  apoya en que reproduce V0 y V1).
- SEGUIMIENTO (visto, no perseguido): nieve sólo existe como superficie en el régimen de día de las tablas de píxel
  (`LECTURA_LUT.md:115-116`); de día VOLCAT podría tratar la cumbre como nieve, y todas nuestras pruebas usan tierra.
  Cae dentro del supuesto de día ya conocido.

## Reproducir

Las cifras nuevas de esta auditoría salen de archivos del repo:

```powershell
python -I -c "import pandas as pd; d=pd.read_csv(r'docs/own_volcat/h17_regla_propia/resultados/pluma_por_cuadro.csv'); p=d[(d.pos==True)&(d.con_base==True)]; print(p.groupby('evento').det_decide.agg(['size','sum']))"
```

```powershell
python -I -c "import pandas as pd; d=pd.read_csv(r'docs/own_volcat/h17_regla_propia/resultados/calor_por_cuadro.csv'); n=d[(d.periodo=='noche')&(d.sitio=='chillan')]; b=n[n.cuadro.str[:8]>='20261024']; print(len(b),(b.vrp_ctx>=10).mean())"
```
