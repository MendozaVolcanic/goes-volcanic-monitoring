# Criterio, vuelta 2: por qué nuestro β(12/11) sale 0,30 bajo el de VOLCAT en nube tenue. 21-11-2026

Escrito y subido antes de medir los cuadros 6 a 10. Variantes elegidas sólo con los cuadros 1 a 5. Base: la
variante elegida en la vuelta 1 (`criterio_2026-11-21.md`): ε llevado al nadir (V1), nube negra en el punto frío
del perfil GFS (N1), cielo `geocatRTM` (S0 es la base de esta vuelta; la G M2 p75 de la vuelta 1 no mejoró en
6 a 10).

## Qué se vio en los cuadros 1 a 5 antes de escribir esto (`scripts/explorar_beta_1a5.py`)

1. **El β de VOLCAT en nube tenue no está reemplazado por una constante.** Con 0,05 ≤ εtot < 0,2 (111.801
   píxeles): p5/p50/p95 = 0,91 / 1,27 / 1,53, contra 0,71 / 0,93 / 1,05 el nuestro; ningún valor concentra más de
   0,3 % de los píxeles. Correlación de rangos con el sesgo de BTD (despejado − observado): −0,88 el de VOLCAT,
   −0,96 el nuestro. Es nuestro mismo β desplazado, no una función nueva.
2. **El desplazamiento salta en εtot = 0,25.** Δβ (VOLCAT − nuestro), mediana por franja de 0,02: +0,279 en 0,23
   a 0,25 y +0,072 en 0,25 a 0,27; se mantiene en +0,28 a +0,30 por debajo y baja suave de +0,07 a +0,03 por encima.
   El salto es de 0,21.
3. **La tabla de píxel lo dice** (atributos leídos, `resultados/lut_atributos_beta.txt` y
   `resultados/lut_datasets_fct.txt`): `X_COND_BETA1112_TOT_H20_CORRECTION_FCT` = (−999; 1,5; 2,5),
   `SLOPE_..._FCT` = (0; 0; 0), `INTERCEPT_..._FCT` = (0; 0,05; 0,2), `MAX_EMISS14_TOT_H20_CORRECTION` = 0,25, y el
   archivo de origen `modis_beta1112_tot_h20_correction_Jul16_2012_194821.idl`. Lectura: con εtot < 0,25, a
   β(12/11) total se le suma 0,05 si X > 1,5 y 0,2 si X > 2,5. X: candidata el agua precipitable, que VOLCAT
   guarda por píxel en su paso de píxel (`total_precipitable_water`, en cm). En este caso vale 4,1 a 5,7 cm en
   todo el dominio (`scripts/extraer_tpw.py`), así que el escalón de 1,5 cm no se puede probar aquí: sólo el de
   +0,2. Por qué físico (inferido): con mucho vapor entre la nube y el satélite, la absorción del vapor en 12 µm
   baja la β aparente de una nube tenue; VOLCAT la devuelve hacia el valor de una atmósfera seca, como las de su
   entrenamiento con MODIS.
4. Otras relaciones de la tabla, leídas, que NO explican este tramo: `COEFF_BETA1112_TOT_FCT1` = (0,8896;
   −0,2046) con sesgo de BTD 0,5 a 2 K da β de 0,48 a 0,79 (`ACTUAL_BETA_RANGE`), inferior a 1, y
   `BETA1112_FROM_BTD_BIAS_LB_EMISS14_WATER` = 0,02 la pone bajo εtot 0,02 en agua (fuera de este tramo);
   `SLOPE/INTERCEPT_BETA1112_FCT2` = (−0,70; 0,031) y `FCT3` = (−1,19; 1,14) son las ecuaciones 8 y 7 de SECO Parte 1
   (prefiltros); `FCT4` es el tope de β opaco 1,36. `EMISS_UNCERTAINTY_*` son umbrales de membresía a objeto.
5. **Ángulo a la altura de la nube (punto 3 del encargo): descartado por geometría, sin datos.** A 16 km de altura,
   sen θ_h = sen θ · R/(R + h) con R = 6.371 km: a θ = 31°, cos θ pasa de 0,8572 a 0,8577 (0,06 %). El residuo
   visto en la vuelta 1 (k/cos θ de 0,88 a 1,02) es 200 veces mayor. No se prueba.

## Variantes

**H, corrección por vapor** (fija, leída de la tabla; no se ajusta): H0 sin corrección; H1 β(12/11) total +0,2
si TPW > 2,5 cm, +0,05 si 1,5 < TPW ≤ 2,5, sólo donde nuestro εtot (al nadir) < 0,25.

**S, cielo despejado para β** (se elige con H1, en los cuadros 1 a 5, sobre los píxeles 0,25 ≤ ε_VOLCAT < 0,5,
donde H no actúa: así H y S no se ajustan sobre los mismos píxeles). Mismas definiciones que la vuelta 1 (sesgo =
despejado − observado, por banda, corrección = BT_geocatRTM − Per_q):
S0; G con M1 o M2, q ∈ {25, 50, 75}, bandas B2 (C14 y C15); L (±12 px, ≥ 5 despejados) con M1 o M2, q = 50, B2.
Total 9. Se elige la de mayor fracción de |Δβ(12/11)| ≤ 0,02; empate (≤ 0,002) a la más simple (S0, G, L).

## Reglas de éxito (cuadros 6 a 10, variante elegida, H1)

- **Principal de esta vuelta:** β(12/11) total dentro de 0,02 del de VOLCAT en ≥ 80 % de los píxeles con
  0,05 ≤ ε_VOLCAT < 0,2 y β finito en ambos. Cumple = la diferencia de 0,30 queda explicada.
- **De la vuelta 1, se vuelve a reportar:** con 0,05 ≤ ε_VOLCAT ≤ 0,9, ε dentro de 0,01 en ≥ 80 % y β dentro de
  0,02 en ≥ 80 %.
- Se informa, sin decidir: lo mismo por tramo (0,05 a 0,2; 0,2 a 0,25; 0,25 a 0,5; 0,5 a 0,9) y para H0.

## Nivel B (se reporta)

Con las reglas del frente 1 (PR 75, rama `analisis/h15-nube-tenue`, commit af0e8ca, `nt_regla.py`: R1 + R2 + R3,
copia de lectura en `D:\goes_cache\cielo_sesgo\nt\`), entradas como en H15 nivel B con nuestros ε14, β(12/11) y
β(7,3/11): κ a 0,5, |ΔP| ≤ 0,05, P_VOLCAT ≥ 0,5 recuperados, en conjunto y por tramo de εtot de VOLCAT
(< 0,2; 0,2 a 0,5; ≥ 0,5), para H1 con la S elegida y para H0 S0 (referencia). Regla de la etapa 2 como
referencia: ≥ 90 %, κ ≥ 0,90, ≥ 90 %.

## Si no cumple

Se informa cuánto falta y en qué tramo; la pregunta para el correo queda escrita con los números.
