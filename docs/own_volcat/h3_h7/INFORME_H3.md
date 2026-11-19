# H3: ¿el cielo despejado modelado y las razones β explican por qué VOLCAT ve Chillán y nosotros no?

Corrida del 19-11-2026. Criterio escrito antes de medir:
`C:\Users\nmend\AppData\Local\Claude-Data\claude_pzs8sxrjxfjjc\side-session-notes\local_f3a7d295-ddde-4b7c-b258-25e760c44266\criterio_H3_cielo_modelado_2026-11-19.md`.
Salida cruda con todas las tablas:
`C:\Users\nmend\AppData\Local\Claude-Data\claude_pzs8sxrjxfjjc\side-session-notes\local_f3a7d295-ddde-4b7c-b258-25e760c44266\h3_resultado.txt`.

**Veredicto según el criterio: NO CONCLUYENTE.** La versión modelada (M) es válida (sesgo en C14 de
−0,29 K), pero la compuerta de VOLCAT deja pasar casi todo, en la huella y en el control por igual
(G = 0,90 contra 0,88), y ninguna razón β separa la huella del control. La falsación formal (b) no se
cumple sólo porque β(12/11) queda en |AUC − 0,5| = 0,113, apenas sobre el umbral de 0,10. En la práctica,
ni M ni E separan la pluma.

## 1. La física: qué mide VOLCAT y por qué podría ver lo que el BTD no ve

Una nube de ceniza delgada deja pasar parte de la radiación que sube desde el suelo y agrega la suya,
emitida a la temperatura de la nube. Si se conoce cuánto llegaría sin nube (el cielo despejado, R_clr) y a
qué temperatura emite la nube (VOLCAT usa la tropopausa como referencia), se puede despejar una
emisividad efectiva ε para cada canal: cuánto "pesa" la nube en esa longitud de onda. La razón
β = ln(1 − ε_λ) / ln(1 − ε_11) depende de la microfísica (silicato, hielo o agua) y no del espesor, así que
una pluma muy delgada todavía tiene la "firma" de la ceniza aunque su BTD 11 − 12 µm sea positiva.

Eso hace que el método dependa entero de R_clr. Si el cielo despejado está mal, ε está mal, y en un
píxel de cordillera eso pasa fácil: el modelo no conoce la altura real del terreno ni su temperatura de
piel. H3 propone que VOLCAT ve Chillán porque su R_clr modelado (GFS más modelo radiativo) y la β de
7,3/11 µm (canal C10, vapor de agua) detectan algo que nuestro cielo empírico y el BTD no ven.

## 2. Método

**Casos y huella.** 28-10 22:40 a 23:40 UTC (4 cuadros, crepúsculo), 29-10 01:00 a 01:20 UTC (3, noche
cerrada) y 14-11 16:40 a 22:40 UTC (32 cuadros con `toca_crater_10km == 1`, de día). Huella = píxeles
VOLCAT con ceniza a ≤ 50 km del cráter, llevados a la grilla ABI 83 × 94 con la decodificación de
`pruebaA_28oct.py`, sin dilatar. Ningún cuadro quedó con menos de 3 píxeles (mínimo 4, máximo 43).

**Control pareado por BT11.** Para cada positivo, el día candidato (26, 27, 30, 31-10 y 01 a 06-11 en los
casos 1 y 2; 01 a 06, 09, 12, 13 y 15-11 en el caso 3) a la misma hora cuya mediana de BT11 (C14) sobre la
huella queda más cerca, mirando sólo C14. Quedaron 37 pares con |ΔBT11| ≤ 3 K; dos cuadros del 14-11
quedaron sin control y se informan aparte (19:30, +3,27 K; 22:40, +3,06 K). Controles elegidos: 27-10 para
el caso 1, 31-10 para el caso 2, 12-11 y 13-11 para el caso 3. Dato a notar: en los casos 1 y 3 casi todos
los días candidatos son varios kelvin más fríos que el positivo sobre la huella (nubosidad); el positivo
suele ser la escena más tibia de su minuto.

**Datos.** L1b GOES-19 C10, C11, C14 y C15 leídos por ventana desde S3 anónimo (423 escenas), coeficientes
Planck de cada NetCDF. GFS 0,25 grados archivado (S3 `noaa-gfs-bdp-pds` por rango de bytes, y para 12-11
y 13-11 el filtro GRIB de NOMADS, verificado idéntico a S3 con diferencia máxima de 2e-5 K): T, humedad
específica y ozono en 33 niveles, temperatura de piel, presión y altura de superficie, temperatura de
tropopausa. Archivo por escena: hora del scan redondeada, último ciclo con plazo f000 a f005.

**Versión M (modelo propio, sin cuenta ni compilación).** No se usó PFAAST (el modelo de SECO): existe
sin login pero hay que compilar Fortran, y su instalación es decisión tuya. Se escribió un cálculo línea
por línea en Python: líneas HITRAN bajadas con HAPI 1.3 (sin cuenta) para H2O, CO2, O3, N2O y CH4; continuo
de vapor de agua MT_CKD 4.3 de AER (GitHub, licencia de uso científico sin registro); perfil Voigt
(Humlicek), rejilla de 0,01 cm⁻¹, ala de 25 cm⁻¹; tabla de coeficientes por capa y temperatura; funciones de
respuesta del ABI FM4 publicadas por CIMSS/STAR. La convolución de Planck con esas SRF reproduce los
coeficientes del L1b a ≤ 0,004 K en las cuatro bandas, o sea, las SRF y las unidades calzan. Por píxel:
perfil, temperatura de piel y presión de superficie GFS interpolados bilineal, columna cortada en esa
presión, camino oblicuo con el cenit satelital (unos 43 grados en el cráter). Emisividad de superficie fija
(C10 0,97; C11 0,95; C14 0,97; C15 0,97), supuesto sin fuente porque CAMEL pide cuenta; bajarla 0,03 enfría
el modelo 1,2 K en C11, 1,75 K en C14, 1,5 K en C15 y nada en C10. Lista completa de supuestos en
`h3_resultado.txt`.

**Versión E (sin modelo).** Por píxel, mediana de las 3 escenas más tibias en BT11 entre los días
candidatos al mismo minuto, con las cuatro bandas de esas mismas escenas.

**Señales.** ε(λ) sin recortar contra la tropopausa del GFS; compuerta ε11 ≥ 0,02; β(12/11), β(8,5/11) y
β(7,3/11) sólo en píxeles que pasan la compuerta en su escena. AUC = P(positivo > control).

## 3. Error del modelo (medido antes de mirar la huella)

Píxeles despejados de las 37 escenas de control (|BT11 − E11| < 2 K, a más de 5 píxeles de la huella, 60 al
azar por escena, n = 2200). Observado menos modelo, en K:

| | C10 | C11 | C14 | C15 |
|---|---|---|---|---|
| Sesgo mediano, todos | −0,48 | +0,63 | **−0,29** | −0,14 |
| Desviación estándar, todos | 2,13 | 6,94 | 7,60 | 7,28 |
| Caso 1 (crepúsculo), sesgo / desv. | +0,76 / 0,65 | +1,91 / 2,77 | +1,30 / 2,94 | +1,51 / 2,75 |
| Caso 2 (noche), sesgo / desv. | +0,33 / 1,01 | +0,01 / 2,05 | −0,39 / 2,42 | −0,75 / 2,37 |
| Caso 3 (día), sesgo / desv. | −0,93 / 2,19 | +0,52 / 7,56 | −0,59 / 8,23 | −0,48 / 7,88 |

El sesgo en C14 (−0,29 K) está muy por debajo de los 3 K del criterio: **M vale**. La dispersión, en cambio,
es grande de día (8 K en C14) y moderada de noche (2,4 K). Para ponerlo en contexto (cifras del informe de
la otra sesión, `C:\Users\nmend\AppData\Local\Claude-Data\claude_pzs8sxrjxfjjc\side-session-notes\local_1055cba6-2c2f-4aa4-9119-82691ee2ed22\busqueda_2026-11-19_C_cielo_despejado_rtm.md`):
Heidinger y Pavolonis (2009) suponen 4 K de incertidumbre en T11 sobre tierra; el ATBD GOES-R VolAsh v3.0,
Tabla 12, usa 5,0 K; Pavolonis (2010) reporta errores de hasta 15 K en desierto a mediodía; NOAA ACMF da
−0,35 ± 1,72 K en C14 a disco completo (mayoría océano). Con nubes delgadas, ε11 = 0,02 equivale a sólo
0,7 a 1,0 K de BT11, así que un error de cielo despejado de varios kelvin domina la compuerta. Por eso SECO
rescata la ceniza con ε11 negativa sobre tierra con un BTD_Bias empírico, no con mejor modelo.

## 4. Resultados

Agrupado (los tres casos, 37 pares, 458 píxeles de huella):

| Versión | G huella | G control | ΔG | AUC ε11 | AUC β12/11 | AUC β8,5/11 | AUC β7,3/11 |
|---|---|---|---|---|---|---|---|
| **M** | 0,902 | 0,876 | +0,026 | 0,541 | 0,387 | 0,452 | 0,536 |
| **E** | 0,035 | 0,009 | +0,026 | 0,483 | no medible (16/4 px) | no medible | no medible |

Por caso, versión M (AUC de β12/11, β8,5/11, β7,3/11):

| Caso | n | G huella | G control | AUC ε11 | β12/11 | β8,5/11 | β7,3/11 |
|---|---|---|---|---|---|---|---|
| 1 (28-10) | 75 | 0,947 | 0,920 | 0,684 | 0,461 | 0,627 | 0,912 |
| 2 (29-10) | 31 | 0,677 | 0,806 | 0,490 | 0,295 | 0,499 | 0,743 |
| 3 (14-11) | 352 | 0,912 | 0,872 | 0,518 | 0,376 | 0,419 | 0,407 |

En E la compuerta casi nunca pasa (G de 0 a 0,13 por caso) y las β no son medibles en ningún caso: con el
cielo empírico la huella sale con ε11 negativa (más tibia que el cielo despejado), lo mismo que ya se
había visto con BTD.

Métrica secundaria (no decide), huella contra anillo de 2 a 6 píxeles en la misma escena, M: AUC ε11 =
0,837. Parece señal, pero el control da lo mismo en esos píxeles: la huella está sobre el volcán, terreno
más alto y más frío que su entorno, y eso el modelo no lo ve.

**Diagnóstico posterior (no decide, se calculó después de las tablas):** en los píxeles de huella de las
escenas de control, observado menos modelo en C14 da una mediana de −7,07 K (p10 −15,6; p90 −0,26). La
altura de superficie del GFS en esos píxeles es de 1537 a 1932 m (mediana 1737 m), contra unos 3200 m de la
cumbre. El modelo pone el suelo 1,5 km más abajo de lo que está, lo ve más caliente, y la ε11 sale
positiva (0,1 a 0,28) en el positivo y en el control. Ese es el origen de G ≈ 0,9 en ambos grupos: la
compuerta mide el error del terreno, no la pluma.

## 5. Veredicto según el criterio

- Validez de M: sesgo C14 = −0,29 K ≤ 3 K, la versión M cuenta.
- **Se sostiene** si G_huella ≥ 0,5 (0,902, cumple), ΔG ≥ 0,25 (+0,026, **no cumple**) y algún β con
  |AUC − 0,5| ≥ 0,20. No se sostiene.
- **Se falsa** si (a) G_huella < 0,10 (no) o (b) ΔG < 0,10 (sí, +0,026) y los cuatro AUC con
  |AUC − 0,5| < 0,10: ε11 0,041, β8,5/11 0,048 y β7,3/11 0,036 cumplen, pero β12/11 da 0,113. (b) no se cumple.
- Resultado: **NO CONCLUYENTE**, por la regla de "cualquier otro caso". No reinterpreto el umbral: β12/11
  sobrepasa la línea de falsación por 0,013, con la huella levemente más baja que el control (medianas 0,86
  contra 0,88; dirección "más ceniza" en los tres casos: 0,461, 0,295, 0,376).
- Atribución (paso 4, no cambia el veredicto): ninguna de las dos formas separa. M no, porque la compuerta
  pasa en todos lados; E no, porque la compuerta no pasa en ningún lado. Lo que el criterio llama "H3 cae en
  las dos formas" describe bien los datos, aunque la regla formal queda en no concluyente.

Lo que sí deja claro esta prueba: con un cielo despejado del GFS sobre un volcán de 3,2 km, el error del
terreno (unos 7 K en C14 en la cumbre) es diez veces mayor que la señal que la compuerta de VOLCAT necesita
(0,7 a 1 K). Ni el modelo ni la β de C10 hacen aparecer la pluma; si VOLCAT la ve, lo más probable es que
sea por otra pieza de su cadena (el BTD_Bias sobre tierra, o el seguimiento entre cuadros de la hipótesis
H7), no por el cielo modelado en sí.

## 6. Desviaciones del criterio

1. Huella con la decodificación de `pruebaA_28oct.py` en los tres casos (sin el filtro de objetos y de
   manto que `huellas.py` aplicaba en noviembre).
2. GFS: archivo de pronóstico f000 a f005 del último ciclo a la hora redondeada del scan, en vez del
   análisis del ciclo más cercano, para que la temperatura de piel siga el ciclo diurno; T_tropo del mismo
   archivo (campo de tropopausa del GFS).
3. GFS de 12-11 y 13-11 vía NOMADS (mismo dato, recorte espacial) por la red lenta; verificado idéntico.
4. Extrapolación lineal del GFS en las columnas más orientales de la ventana (lon −70,25 a −70,20).
5. Supuestos del modelo radiativo y emisividad fija listados en `h3_resultado.txt`, con su sensibilidad.
6. Error del modelo con una muestra de 60 píxeles por escena de control; anillo secundario con 40
   píxeles por cuadro.
7. E incluye al día de control entre sus candidatos, tal como está escrito.

## 7. Archivos

- Salida cruda: `C:\Users\nmend\AppData\Local\Claude-Data\claude_pzs8sxrjxfjjc\side-session-notes\local_f3a7d295-ddde-4b7c-b258-25e760c44266\h3_resultado.txt`
- Copia de los scripts: `C:\Users\nmend\AppData\Local\Claude-Data\claude_pzs8sxrjxfjjc\side-session-notes\local_f3a7d295-ddde-4b7c-b258-25e760c44266\h3_scripts\`
- Carpeta de trabajo (datos, caché L1b de 4 bandas, GFS, LUT, líneas HITRAN, caché del modelo):
  `C:\Users\nmend\AppData\Local\Temp\claude\caac88451b34493f\bd33fd70-a478-403d-be84-fcf2fda5792e\scratchpad\h3\`
  (está en el scratchpad temporal: si quieres conservar la LUT de 185 MB y el caché, hay que moverlos).
