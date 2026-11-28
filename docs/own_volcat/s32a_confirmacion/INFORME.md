# S32a: medida única de las tres confirmaciones congeladas (S23b anillo, S25a zona, S26a unión). 28-11-2026

Sesión S32a, lanzada por la coordinadora S32 a pedido de Nicolás ("lanza la medida", 28-11). Una sola corrida del
envoltorio, sin tocar nada antes ni después de ver el resultado:

`python -I docs/own_volcat/s30a_enmienda/scripts/s30a_confirmar.py medir --hasta 2026-11-27`

Regla que decide: `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\Goes\docs\own_volcat\s30a_enmienda\enmienda_2026-11-26.md`
(v1, nulo por días, alfa 0,001, decide el fondo de 2025) con el gatillo de
`C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\Goes\docs\own_volcat\s30a_enmienda\enmienda_v2_2026-11-26.md`.

## 1. Qué se preguntó

En tres tardes nuevas, que nadie había mirado con el detector, VOLCAT (SSEC) dibujó pluma de Nevados de Chillán en
**20 cuadros de 10 minutos**: 8 el 25-11, 1 el 26-11 y 11 el 27-11, todos entre las 16:50 y las 21:00 UTC (13:50 a
18:00 Chile (UTC-3)). Los tres detectores propios, sólo con GOES-19 y congelados antes de estos días, miran la diferencia
de temperatura 11 menos 12 µm (la firma de ceniza silicatada) contra lo que ese píxel hacía a esa hora en 2025:

- **S23b, anillo**: un anillo alrededor del cráter, a decenas de km.
- **S25a, zona del cráter**: 11 píxeles a menos de 4 km del cráter.
- **S26a, unión** (el titular): dispara si dispara cualquiera de los dos.

La pregunta: **¿disparan donde VOLCAT dibuja más de lo que dispararían, a esas mismas horas, en un día cualquiera de
2025?** "Alcanzado" es un cuadro de VOLCAT con disparo en él, en el anterior o en el siguiente; R es la fracción de los
cuadros evaluados (anillo con nube de no más de la mitad) que quedan alcanzados.

## 2. Resultado en una línea

**Ninguno confirma.** Con la regla de la enmienda los tres escriben **NO CONFIRMA** (p_día contra 2025: anillo 0,055,
zona 0,015, unión 0,010; hacía falta 0,001 o menos). Las reglas congeladas del 25-11 escriben CONFIRMA (anillo) y
PARCIAL (zona y unión), pero esas cuentan cada cuadro como una tirada independiente, no tienen tamaño nominal (S28b) y
sólo se informan.

## 3. Los dos rótulos, lado a lado

20 cuadros P de VOLCAT en 3 días; los 20 evaluados por los tres detectores (cielo abierto en todos).

| Detector | Alcanzados / evaluados (R) | Por día: 25-11, 26-11, 27-11 | Cuadros con disparo en el día (de 144) | **Enmienda**: p_día contra 2025 (decide) | 2026 sin VOLCAT y 2024 (informan) | **Rótulo de la enmienda (decide)** | Congelado: p25 por cuadro, pN de Fisher | Rótulo congelado (informa) |
|---|---|---|---|---|---|---|---|---|
| S23b anillo | 10 / 20 (0,50) | 0/8, 0/1, 10/11 | 0, 13, 44 | 0,055 (3.221 de 58.364 colocaciones) | 0,233; 0,075 | **NO CONFIRMA** | 3,8e-9; 0,0014 (0 de 14 N cercanos alcanzados) | CONFIRMA |
| S25a zona | 14 / 20 (0,70) | 6/8, 1/1, 7/11 | 65, 112, 108 | 0,015 (2.207 de 147.226) | 0,113; 0,024 | **NO CONFIRMA** | 1,9e-14; 0,83 (11 de 14 N cercanos) | PARCIAL |
| S26a unión | 17 / 20 (0,85) | 6/8, 1/1, 10/11 | 58, 111, 122 | 0,010 (1.534 de 147.226) | 0,063; 0,012 | **NO CONFIRMA** | 3,9e-18; 0,48 (11 de 14 N cercanos) | PARCIAL |

Resolución: el piso del nulo de 2025 es 1,7e-5 (anillo) y 6,8e-6 (zona y unión), muy bajo alfa; ninguna regla queda NO
DECIDIBLE. Nulo con k = 3 días con P, 262.079 colocaciones posibles, enumeradas todas. pN estratificado por día
(Mantel-Haenszel, informativo): razón de odds 0 en el anillo (p 0,79) y 0,75 en zona y unión (p 0,60). La nota de
"confirma con umbral sin corregir por tres pruebas" no aplica: ninguna confirma.

## 4. Cómo se lee, para geólogo

**El anillo vio una tarde, no dos.** El 27-11 alcanzó 10 de los 11 cuadros de VOLCAT, seguidos de 18:10 a 19:50 UTC; el
25-11 no alcanzó ninguno de 8, y ese día no disparó ni una sola vez en 24 horas. Es exactamente el caso que la enmienda
quiso atajar: una tarde "encendida" a esas horas se parece a una tarde de tiempo encendida. Si se ponen las horas de
VOLCAT de estos tres días sobre tres días cualquiera de 2025, en el 5,5 % de los casos el anillo alcanza la mitad o más.
La regla congelada lo leía CONFIRMA porque contaba los 10 aciertos del 27-11 como 10 tiradas sueltas, cuando son una
racha de una tarde.

**La zona y la unión aciertan porque están encendidas casi todo el día.** Alcanzaron 14 y 17 de 20, en los tres días,
pero dispararon en 58 a 122 de los 144 cuadros de cada día, y en el 59 a 81 % de los cuadros evaluados en que VOLCAT no
dibujó nada (cuadros N; 59 a 61 % de día, 73 a 81 % de noche). Dentro del mismo día dispararon tanto o más donde VOLCAT no dibujó (razón de odds 0,75).
Acertar es barato cuando el detector está casi siempre prendido. Contra 2025 el acierto es raro (1,5 % y 1,0 % de las
colocaciones lo igualan) pero no al nivel que se fijó antes (0,1 %); contra un día de 2026 en que VOLCAT no dibujó
(informativo), lo iguala el 11 % y el 6 %. Es lo mismo que ya se veía en desarrollo: la zona dispara en 2026 4 a 5 veces
más que en 2025 fuera de VOLCAT (S28b V201), coherente con lo que dice Nicolás: Chillán tiene pluma todos los días, y la
cumbre tiene más nieve que en 2025 (S31i, S31f). La firma 11 menos 12 µm junto al cráter no separa la pluma que VOLCAT
dibuja de lo que la cumbre hace el resto del día.

**El poder calculado antes no prometía esto.** S31b daba a la unión 0,8 de poder con 7 de cada 10 cuadros alcanzados,
pero con días placebo cuyo disparo de fondo era el de 2025 o el de 2026 sin VOLCAT. Estos tres días dispararon mucho más
(la zona, 45 a 78 % de los cuadros del día), así que las colocaciones que caen sobre ellos también alcanzan, y el p sube.
Es la prueba haciendo su trabajo, no una falla de ejecución.

## 5. Qué es confirmación y qué no

- **Es confirmación**: sólo el rótulo de la enmienda, escrito y empujado antes de ver estos días. Los tres son **NO
  CONFIRMA**. Por la enmienda §7, la corrida gastó los días 25 a 27-11 para las tres reglas, y un NO CONFIRMA **cierra la
  regla**: ninguna de las tres se vuelve a medir con días posteriores (eso sólo valía para INVÁLIDA o NO DECIDIBLE).
- **No es confirmación**: el CONFIRMA del anillo y los PARCIAL de zona y unión de las reglas congeladas (su p25 rechaza
  12 a 18 % de las veces en días placebo, S28b 201); los fondos de 2026 sin VOLCAT y de 2024; el pN de Mantel-Haenszel.
- **No dice** que el detector no vea nada: el p contra 2025 de la unión (0,010) es bajo. Dice que con estas tres tardes
  no se distingue lo que VOLCAT dibuja de lo que el detector hace por su cuenta en la cumbre de Chillán en 2026. Tampoco
  dice nada de ceniza contra gas, de altura ni de lo que pasa con el anillo más de la mitad nublado (enmienda §8).

## 6. Ejecución y comprobaciones

- Antes de correr: ningún `MEDIDA_INICIADA.json`, ningún resultado en el checkout ni en `origin/main` (e824947), ningún
  python vivo. `cobertura` repetida el 28-11 06:36 UTC, idéntica a la de la coordinadora: L1b y ACMF 1,0 los cuatro días
  (24 a 27-11), P evaluables 8, 1 y 11, D\* = 2026-11-27 (log
  `D:\goes_notas\s30\confirmacion\cobertura_s32a_2026-11-28.log`).
- Medida: iniciada 2026-11-28 06:36:28 UTC, 827 s, salida 0, sin una aserción. Instrumento de los congelados sin falla
  (576 cuadros, cobertura 1,0, 0 scan distinto, 0 congelados). Manifiesto igual después de S23b, de S25a y de S26a; las
  tres midieron las mismas clases y el anillo de S25a es el de S23b día por día; el fondo de 2025 que recalcularon los
  congelados es idéntico al congelado del nulo. CSV de clases sha256 `0c0c286553f76c9f...`; cubo de 1.152 archivos (L1b y
  ACMF) sha256 `b008491c3125542c...`.
- Nada se ajustó después de ver el resultado. El envoltorio ya se niega a medir otra vez (existe
  `D:\goes_notas\s30\confirmacion\MEDIDA_INICIADA.json`).
- Archivos:
  - `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\Goes\docs\own_volcat\s30a_enmienda\resultados\s30a_confirmacion.json` (los dos rótulos, nulos y días; copia en `D:\goes_notas\s30\confirmacion\s30a_confirmacion.json`)
  - `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\Goes\docs\own_volcat\s23_fondo_2025\resultados\s23b_resultado.json`
  - `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\Goes\docs\own_volcat\s25a_crater\resultados\s25a_confirmacion.json`
  - `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\Goes\docs\own_volcat\s26a_combinado\resultados\s26a_confirmacion.json`
  - Log: `D:\goes_notas\s30\confirmacion\medir_s32a_2026-11-28.log`; copia del CSV medido:
    `D:\goes_notas\s30\confirmacion\medida\clases_medida.csv`.

## 7. Qué queda (recomendación, decide Nicolás por la coordinadora)

Las tres confirmaciones del detector propio por firma 11 menos 12 µm quedan cerradas con NO CONFIRMA. Recomiendo no
armar una cuarta regla con estos días (ya están vistos) y seguir lo que dejó S31j: el nacimiento de la pluma que VOLCAT
usa no sale del IR de 2 km, así que lo que más rinde ahora es el correo v6 a Pavolonis con las preguntas de S31j, y
cualquier detector nuevo tendría que partir de otra medida (cámaras del OVDAS, REAV) para el nacimiento.
