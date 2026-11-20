# H12: Test 3 original del VAAC de Londres (Francis et al. 2012) en Nevados de Chillán. Informe, 20-11-2026

Criterio commiteado y subido antes del primer número: `criterio_H12_2026-11-20.md` (commit ae954b0, rama
`claude/h12-francis-test3`). Salida cruda: `resultados/h12_resultado.txt`; diagnóstico posterior (no decide):
`resultados/h12_posterior_6de9.txt`. Scripts: `scripts/comun_h12.py`, `scripts/h12_rt_sitios.py`,
`scripts/h12_analisis.py`, `scripts/h12_posterior_69.py`. Datos derivados (no se suben):
`C:\Users\nmend\AppData\Local\Claude-Data\claude_pzs8sxrjxfjjc\side-session-notes\local_f3a7d295-ddde-4b7c-b258-25e760c44266\h12_datos\`.

## 1. Para geólogo

**La pregunta.** El VAAC de Londres marca ceniza "tentativa" cuando la diferencia 11 − 12 µm queda bajo
+0,7 K **y** al menos 1 K por debajo de lo que un modelo dice que tendría ese mismo píxel con cielo
despejado (Francis et al. 2012, ec. 3, p. 3, comprobada en la imagen de la página). La segunda condición
corrige el vapor de agua: el cielo húmedo ya da una diferencia positiva, y una capa con firma de ceniza la
baja. Es el único test publicado que admite diferencias positivas, justo donde caen las plumas de Chillán
(−0,6 a +0,5 K). La versión que probamos el 19-11 (PR 54) era otra, la resumida por Falconieri 2018.

**Lo que salió.** El Test 3 marca más la huella con pluma que el mismo lugar sin pluma, pero no lo bastante:
76 % de los cuadros con pluma contra 52 % de los controles (66 pares, 10 días), y en el píxel la pluma
apenas se distingue (AUC 0,58). De día dispara en el cráter sin pluma en 64 % de los cuadros; de noche casi
no dispara, con o sin pluma. La física lo explica: sobre la huella, el cielo despejado modelado espera una
diferencia 11 − 12 de ~1,8 K y la observada es ~0,9 K **también sin pluma**; la pluma agrega sólo ~0,25 K
a esa brecha. El umbral de 1 K cae en medio del error del modelo, así que pasar o no pasar depende sobre
todo del error del día.

**Veredicto según el criterio: no concluyente.** No separa (AUC bajo 0,70 y diferencia de cuadros 0,24 bajo
0,30). Tampoco se pudo cerrar como "mide el terreno": el control de cumbres (Antuco y Nevado de Longaví)
dio 35 % de cuadros, bajo el 50 % exigido. La razón es que el control no tuvo el error que buscaba: el GFS
pone las tres cumbres a la misma altura (~1.700 m), pero el cielo despejado queda sólo 2 a 3 K más tibio
que lo observado en Antuco y Longaví, contra 8 a 9 K en la huella de Chillán. Las cumbres de control
salieron mucho más "fáciles" para el modelo que el macizo de Chillán.

**Lectura.** Dos cosas apuntan a que el Test 3 mide el lugar y no la pluma, aunque el criterio no permita
decirlo como veredicto: (1) en las 795 escenas de E2 encuentra un objeto anclado al cráter en 83 % de los
cuadros VOLCAT, pero también en 60 % de las escenas sin pluma (68 % de día) y en 75 % del manto del 16-11;
(2) en el llano, donde el GFS acierta la altura, la brecha es 0,0 K y el test casi no dispara (3 %). El test
reacciona a donde el cielo despejado modelado está más equivocado, y en esta ventana ese lugar es el macizo
de Chillán. Con esto no queda una compuerta infrarroja publicada de VOLCAT o del VAAC de Londres que pueda
admitir estas plumas y no se haya probado (la versión 2023 de Londres corta en BTD ≤ −0,29 K para GOES).

## 2. Método (detalle en el criterio)

- **Test 3 por píxel**: BTD = BT C14 − BT C15 < 0,7 K y BTD < BTD_clr − 1,0 K, con BTD_clr del modelo
  radiativo de H3 (HITRAN, MT_CKD, SRF de ABI, GFS 0,25°). 10,8 µm → C14, 12,0 µm → C15, 8,7 µm → C11,
  umbrales de SEVIRI sin recalibrar. **Por cuadro**: al menos un píxel de la huella.
- **Conjunto A (decide)**: los 66 pares de H11 tal cual (control = mismo minuto UTC en día sin pluma, pareado
  por BT11), cielo despejado directo por píxel.
- **Conjunto B (réplica)**: las 795 escenas de E2; pareo nuevo fijado en el criterio (mismo minuto ±10 min,
  otra jornada, BT11 de la huella más cercana, máximo 3 K): 89 pares, 9 sin control a menos de 3 K, 2 sin
  candidatos. Cielo despejado de la rejilla de E2.
- **Control de terreno**: la huella de cada par trasladada a Antuco y a Nevado de Longaví (misma forma y
  tamaño), en las mismas dos escenas del par, con cielo despejado directo (10.458 píxeles más). Llano
  (Valle Central) como referencia informativa.
- **Variantes**: filtro β de la ec. 5 con la nube negra a la altura donde el GFS vale BT10,8 − 5 K; ruido
  6 de 9 en caja 3 × 3; Test 1 (BTD < −2 K).

## 3. Resultados

### Conjunto A (decide), agrupado: 66 pares, 10 días, 733 píxeles de huella

| Medida | Valor | Pide la regla 1 |
|---|---|---|
| AUC del margen, huella | 0,581, IC 95 % por días [0,543; 0,710] | ≥ 0,70 y límite > 0,55 |
| AUC del margen, anillo de 2 a 6 px | 0,491 (huella − anillo +0,09) | diferencia ≥ 0,10 |
| Días con AUC > 0,5 | 7 de 10 | ≥ 2 |
| Cuadros con T3: pluma / control | 0,758 / 0,515 (diferencia +0,24) | diferencia ≥ 0,30 |
| Píxeles de huella con T3: pluma / control | 0,216 / 0,106 | |
| Cumbres (Antuco y Longaví, 264 cuadros) | 0,348 (Antuco 0,386; Longaví 0,311) | regla 2 pide ≥ 0,50 |
| Llano (132 cuadros) | 0,030 | |

Por estrato (informativo):

| Estrato | Pares (días) | AUC | Cuadros pluma / control | Cumbres | Llano |
|---|---|---|---|---|---|
| Noche y crepúsculo | 14 (5) | 0,586 [0,463; 0,678] | 0,357 / 0,071 | 0,089 | 0,071 |
| Día | 52 (7) | 0,592 [0,547; 0,773] | 0,865 / 0,635 | 0,418 | 0,019 |

La física (medianas sobre los píxeles, conjunto A agrupado):

| Lugar | Altura GFS | BT11 despejado − observado | BTD obs | BTD_clr | BTD_clr − BTD | T3 en píxeles |
|---|---|---|---|---|---|---|
| Huella con pluma | 1.727 m | +8,3 K | +0,90 K | +1,84 K | +0,85 K | 22 % |
| Huella, control | 1.727 m | +6,9 K | +0,93 K | +1,82 K | +0,61 K | 11 % |
| Cumbres trasladadas | 1.696 m | +2,1 K | +1,38 K | +1,86 K | +0,32 K | 5 % |
| Llano | 216 m | −0,6 K | +1,94 K | +2,10 K | +0,00 K | 1 % |

- La brecha BTD_clr − BTD que el test exige sobre 1 K ya es ~0,6 K en el control (0,78 K de día) y la pluma
  la sube ~0,25 K. De noche la brecha es ~0,3 a 0,4 K y casi nadie llega a 1 K (3 % de los píxeles con
  pluma). Es el mismo patrón del error de BT11 de H11 (mayor de día).
- En las cumbres la brecha es 0,3 K y en el llano 0. El error de terreno que infla BTD_clr no es una
  propiedad de "cualquier cumbre con GFS bajo": es grande donde BT11 despejado se aleja mucho de lo
  observado, y eso pasa en la huella de Chillán, no en el entorno de Antuco ni de Longaví.

Variantes (conjunto A agrupado, cuadros pluma / control / cumbres):

| Variante | Pluma | Control | Cumbres |
|---|---|---|---|
| T3 | 0,758 | 0,515 | 0,348 |
| T3 + β (β no medible borra) | 0,682 | 0,424 | 0,227 |
| T3 + β (β no medible queda) | 0,712 | 0,455 | 0,265 |
| T3 + 6 de 9 | 0,227 | 0,030 | 0,000 |
| Test 1 (BTD < −2 K) | 0 | 0 | 0 |

El filtro β saca un poco de todo por igual (β medible en ~95 % de los píxeles T3 de la huella con pluma). Ningún píxel llega a
ceniza definitiva (Test 1).

### Conjunto B (réplica): 89 pares, 10 días, 1.010 píxeles

AUC 0,659 [0,543; 0,756], 7 de 10 días > 0,5; cuadros pluma / control 0,764 / 0,517 (+0,25); cumbres
0,382; llano 0,062. Día 0,684 y 0,847 / 0,597; noche 0,618 y 0,412 / 0,176. La regla 1 pedía en B AUC
≥ 0,65 y diferencia ≥ 0,20, que se cumplen, pero sólo valen si A cumple, y A no cumple.

### Escenas de E2 enteras (informativo): objeto T3 anclado al cráter

| | Día | Noche | Todas |
|---|---|---|---|
| Con pluma (100) | 78 de 81 = 0,96 | 5 de 19 = 0,26 | 0,83 |
| Sin pluma (665) | 363 de 538 = 0,67 | 37 de 127 = 0,29 | 0,60 |
| Manto 16-11 (40) | 18 de 22 = 0,82 | 12 de 18 = 0,67 | 0,75 |

Con la vara del 17-11 (falsa alarma ≤ 2 %) el Test 3 queda a 30 veces del límite.

### Diagnóstico posterior: T3 + 6 de 9 por escena (escrito después de ver lo anterior; no decide)

En los pares, el 6 de 9 se veía limpio (23 % y 37 % de los cuadros con pluma contra 3 % de los controles,
0 % en cumbres y llano). Antes de proponerlo se miró la escena entera con la vara del 17-11: objeto anclado
en 35 de 100 cuadros con pluma, 228 de 665 escenas sin pluma (34 %; 16 jornadas con más de 3) y 17 de 40 del
manto. Coincidencia con la huella VOLCAT 79 %. La limpieza en los pares era de los píxeles de la huella; en
el resto del disco a ≤ 10 km del cráter el 6 de 9 se enciende igual sin pluma. **No es candidato.**

## 4. Qué cambia

- **Para la serie de hipótesis**: el Test 3 original queda probado. Reacciona algo a la pluma (+0,25 K de
  brecha, cuadros +24 puntos) pero se enciende sin pluma en la mitad de los cuadros y en 60 % de las escenas,
  así que no sirve como detector en Chillán. Con esto, las compuertas IR publicadas de VOLCAT (SECO 1 y 2) y
  del VAAC de Londres (Francis 2012, Falconieri 2018) están probadas contra control pareado; Saint 2023
  no admite BTD sobre −0,29 K en GOES (Tabla 1, p. 10), así que no aplica a estas plumas.
- **Para `POR_QUE_VOLCAT_VE_Y_NOSOTROS_NO.md`** (lo corrige la sesión de continuación, no este PR): la fila
  H8 debe decir que "no cumple" vale para la versión de Falconieri, y agregar H12 como no concluyente con
  la lectura de arriba.
- **Para la etapa siguiente (no hecha)**: lo único que podría cambiar este resultado es corregir el terreno
  del cielo despejado (temperatura y vapor del GFS llevados a la altura real con el gradiente del perfil y un
  modelo de elevación). Si con eso la brecha del control baja a ~0 como en el llano y la de la pluma queda en
  ~0,25 K, el umbral de 1 K tampoco la vería, pero un umbral propio sí podría; eso es otra hipótesis con su
  criterio. El control de terreno de esta prueba debería repetirse con cumbres de error comparable (por
  ejemplo, elegidas por BT11 despejado − observado y no por altura GFS).
- **Para el dashboard**: nada.

## 5. Advertencias

- El control de cumbres no tuvo el error que debía tener (2 a 3 K contra 8 a 9 K en BT11): la regla 2 quedó
  sin poder. Por qué el macizo de Chillán tiene más error que Antuco y Longaví con la misma altura GFS no se
  midió aquí (forma y extensión del macizo, nieve, o gas permanente del cráter son candidatos, sin prueba).
- "Sin pluma" quiere decir sin objeto VOLCAT a ≤ 50 km. El cráter desgasifica y tiene calor desde el 24-10
  (H9); parte de la brecha del control podría ser gas que VOLCAT no dibuja.
- En 155 de 310 escenas de los pares no había PNG VOLCAT ni máscara para excluir ceniza en las cumbres. Donde
  sí había, no excluyó ningún píxel.
- Umbrales de SEVIRI aplicados a C14 y C15 sin recalibrar; Francis no corrige terreno ni dice si usa
  corrección de sesgo en el Test 3. El modelo radiativo no es RTTOV ni el GFS es el UM-NAE.
- El conjunto A está cargado al 14-11 (32 de 66 pares) y la noche tiene 14 pares en 5 días.
- La corrida del modelo en las cumbres se cortó una vez por disco lleno (el disco C quedó con ~10 GB libres);
  se reanudó y las 930 tareas terminaron completas.
