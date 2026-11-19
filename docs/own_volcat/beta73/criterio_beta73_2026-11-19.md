# Criterio declarado ANTES de medir: β(7,3/11) en episodios nuevos de Chillán, 19-11-2026

Escrito y commiteado antes de bajar una sola escena L1b de esta prueba y antes de calcular cualquier ε,
τ o β. Lo único que existe al escribir esto es el inventario de cuadros VOLCAT (sólo PNG, sección 2).

## 1. Pregunta y por qué

En H3 (`docs/own_volcat/h3_h7/INFORME_H3.md`) apareció, después del criterio y por eso sin valor de
prueba, un indicio: con el cielo despejado modelado, la razón β(7,3/11) salió más alta en la huella
VOLCAT que en el control pareado en las dos tandas nocturnas o de crepúsculo (28-10 22:40 a 23:40 UTC,
AUC 0,912; 29-10 01:00 a 01:20 UTC, AUC 0,743), y no de día (14-11, AUC 0,407).

La física que lo haría real: la banda C10 (7,3 µm) está en el borde de la banda de rotación-vibración del
vapor de agua y encima de la banda ν3 del SO2. Una pluma de Chillán sube vapor de agua magmático y de
origen freático, y SO2, a una altura donde el perfil GFS no los tiene. Ambos absorben mucho a 7,3 µm y
casi nada a 11,2 µm. Si la pluma está ahí, la radiancia de C10 cae más (relativo a su cielo despejado)
que la de C14, y la profundidad óptica efectiva τ(7,3) supera a τ(11): β(7,3/11) = τ(7,3)/τ(11) > 1, o
Δτ = τ(7,3) − τ(11) > 0. Esto no distingue vapor de SO2; para detectar la pluma no hace falta.

La confusión que hay que descartar: un día más húmedo en la troposfera media enfría C10 en toda la
escena, haya pluma o no. Por eso la prueba exige que el efecto esté en la huella y NO en el anillo que la
rodea en la misma escena (sección 6).

La pregunta es si el indicio se repite en episodios que no se usaron para encontrarlo.

## 2. Episodios (inventario de PNG, sin L1b)

Fuente: PNG `Ash_Height` del sector `Chile_Central_2_km` de SSEC. SSEC lista días desde 03-10, pero sólo
hay cuadros desde el 20-10 (20-10 parcial) hasta el 19-11 (parcial, al momento de bajar). Todos los
cuadros de ese tramo están bajados.

Cuadro positivo = cuadro con un objeto anclado al cráter según la regla de `paso4_analisis.py`
(componente conexa de 8 vecinos con ceniza, de 4 a 500 px, que toca el disco de 10 km del cráter de
Nevados de Chillán), sin manto ni sistema de más de 500 px a 50 km o menos. Script:
`docs/own_volcat/beta73/scripts/inventario.py`.

Fuera de muestra: se excluyen los días 28-10 y 29-10 COMPLETOS (no sólo las noches): son la misma
secuencia eruptiva y el mismo tiempo meteorológico que dio el indicio, así que sus cuadros diurnos no son
independientes. También queda fuera el 16-11 (40 cuadros con manto, ninguno anclado sin manto).

Estratos por ángulo cenital solar en el cráter (el indicio fue nocturno o de crepúsculo):

- **Estrato N (noche y crepúsculo, cenit ≥ 80°), el que decide**: 22-10 01:50; 10-11 22:30, 22:40, 22:50,
  23:00, 23:20; 14-11 22:40. Siete cuadros, tres días.
- **Estrato D (día, cenit < 80°), extensión**: 24-10 19:10; 25-10 14:40, 16:20, 17:00, 18:00; 07-11 19:50;
  08-11 13 cuadros (17:40 a 21:30); 10-11 15:00, 15:10, 21:30, 21:40, 21:50, 22:10, 22:20; 11-11 17:50,
  18:00, 18:10; 14-11 32 cuadros (16:40 a 22:30). 61 cuadros, siete días.

Los cuadros del 14-11 diurnos ya entraron en H3 (no en el indicio). Se incluyen; además se informa el
estrato D sin el 14-11, como sensibilidad que no decide.

Huella = píxeles VOLCAT con ceniza a 50 km o menos del cráter, llevados a la grilla ABI de la ventana
83 × 94 con la decodificación de `huellas_h3.py` (la de `pruebaA_28oct.py`), sin dilatar. Cuadro con
menos de 3 píxeles de huella: se descarta antes de medir.

## 3. Control pareado por BT11

- Días candidatos para un cuadro positivo en el minuto HH:MM del día D: los días D' con |D' − D| ≤ 10,
  dentro del tramo con PNG (20-10 a 19-11), con cuadro VOLCAT publicado en ese minuto, sin ningún píxel
  de ceniza a 50 km o menos del cráter en ese cuadro NI en ninguno publicado a ±60 min, y sin manto. Se
  excluyen 28-10 y 29-10 también como candidatos.
- Control = el candidato cuya mediana de BT11 (C14) sobre los píxeles de la huella queda más cerca de
  la del positivo, mirando SÓLO C14. Si la diferencia supera 3 K, el cuadro queda sin control y se
  informa aparte (no se fuerza). Mismos píxeles, mismo minuto.

## 4. Cielo de referencia

- **E (principal, empírico, sin modelo)**: por píxel, la mediana de las 3 escenas más tibias en BT11
  entre los días candidatos del mismo minuto, con las cuatro bandas tomadas de esas mismas escenas (la
  versión E de H3, `comun_h3.empirica`). Hacen falta al menos 5 candidatos con escena; si no, el cuadro
  se informa aparte sin medir.
- **M (sensibilidad, no decide)**: el cielo modelado de H3 (GFS 0,25° + `rt.py` + LUT de líneas HITRAN y
  MT_CKD + SRF ABI), con los mismos supuestos y la misma emisividad. No decide porque en H3 el GFS dejó
  la cumbre unos 1,5 km baja (ε11 positiva en la huella y en el control por igual). Se informan los
  recortes de temperatura fuera de la LUT, porque la LUT se armó con los perfiles de H3.

T de tropopausa del GFS (archivo f000 a f005 del último ciclo a la hora redondeada del scan, como H3),
en las dos versiones. Coeficientes Planck del NetCDF L1b de cada banda, nunca escritos a mano.

## 5. Señales y métricas

ε(λ) = [R_obs(λ) − R_clr(λ)] / [B_λ(T_tropo) − R_clr(λ)], sin recortar; τ(λ) = −ln[1 − ε(λ)].

- **β73** = τ(C10)/τ(C14), sólo en píxeles con ε(C14) ≥ 0,02 en su escena (compuerta del ATBD, como H3).
- **Δτ73** = τ(C10) − τ(C14), sin compuerta. Mismo signo que β73 − 1 cuando τ(C14) > 0, y definida aunque
  ε(C14) sea cero o negativa.

Por qué Δτ73: en H3, con el cielo E, la compuerta no pasó en la huella (G = 0,035) y β quedó "no
medible". Si se repite, la prueba moriría sin medir nada. Se declara AHORA la regla: **la métrica que
decide es β73 si es medible en el estrato (al menos 20 píxeles en cada grupo y al menos 3 pares que
aporten); si no, Δτ73.** No se elige después mirando cuál da mejor.

Métricas, por estrato y con el cielo E:

1. **AUC huella** = P(valor en el positivo > valor en el control), píxeles de huella del positivo contra
   los mismos píxeles del control, todos los pares del estrato juntos. AUC > 0,5 es la dirección del
   indicio.
2. **IC 95 % por bootstrap por escena**: 2000 remuestreos de pares (positivo, control) con reemplazo
   dentro del estrato, semilla 0, percentiles 2,5 y 97,5.
3. **AUC anillo**: lo mismo en los píxeles a 2 a 6 píxeles de la huella (dilatación 13 × 13 menos 3 × 3)
   que no tengan ceniza VOLCAT, positivo contra control. Mide el cambio de toda la escena (humedad del
   día). Para el anillo con β73 se usa su propia compuerta.
4. Dirección por día: AUC huella de cada día del estrato con al menos un par.
5. Informativo (no decide): bootstrap por día, la otra métrica (β73 o Δτ73), AUC de ε(C14), y la versión M.

## 6. Decisión (estrato N, cielo E, métrica que decide según la sección 5)

- **El indicio se SOSTIENE** si: AUC huella ≥ 0,70, el límite inferior del IC 95 % > 0,55,
  AUC huella − AUC anillo ≥ 0,10, y AUC huella > 0,5 en al menos 2 de los días del estrato con par.
- **El indicio se FALSA** si el límite superior del IC 95 % < 0,65: los episodios nuevos descartan un
  efecto del tamaño del indicio (0,74 a 0,91).
- **NO CONCLUYENTE** en cualquier otro caso, y también si el estrato N queda con menos de 5 pares con
  control o pares de menos de 2 días distintos.

El estrato D recibe su propio veredicto con las mismas reglas, rotulado "extensión diurna". No cambia el
veredicto del estrato N (el indicio fue nocturno) y se dice tal cual si los dos discrepan.

Atribución (no cambia el veredicto): si E separa y M también, el efecto no depende del cielo; si sólo uno,
se dice cuál.

## 7. Lo que no se hace

No se cambia código de la app (`detect_ash_enhanced` ni nada). Sin VIIRS. No se toca
`docs/own_volcat/POR_QUE_VOLCAT_VE_Y_NOSOTROS_NO.md`. Si algo exige cuenta, licencia o compilación, se
detiene y se pregunta.
