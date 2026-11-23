# S20c: enmienda 2, antes de medir (23-11-2026)

Se sube con el ensayo en seco final (`resultados/seco.json`, `seco.log`) y antes de leer la BTD, la BT11 o sus
cambios en los positivos y en los controles originales. Todo lo de esta enmienda se decidió mirando sólo la máscara
de nubes ACMF (regla E1) y los cuadros placebo, nunca un valor de los positivos.

## 1. Qué mostró el ensayo en seco del diseño 2 con E1 al 80 %

Salida: `resultados/seco_v2a_E1_80.json` y `.log`; diagnóstico `resultados/diag_acmf_v2.log`
(`scripts/s20c_diag_acmf_v2.py`).

- Unidades válidas: 0 a 3 por prueba. Por la tarde (15 a 21 UTC), la regla E1 da despejado en **4 a 7 % de los
  cuadros**, tanto en el pozo limpio (21-09 al 21-10) como en los días libres de noviembre; en los días positivos, en
  **57 a 67 %**. La fracción media de terreno bajo despejado a esas horas es 0,14 (limpio) y 0,15 (placebo).
- **Esto explica MET-01 de raíz:** los días con VOLCAT son los días despejados. Un control "sin pluma" que se parezca
  en BT11 a un positivo despejado sólo podía salir de los pocos días despejados, que en noviembre eran días activos.

## 2. Cambios (reemplazan los valores de la enmienda 1)

Elegidos como **la menor relajación que da 10 unidades o más y 2 días o más en las seis pruebas** (tabla en
`resultados/diag_acmf_ventana.log`, `scripts/s20c_diag_acmf_ventana.py`; con E1 al 80 % no alcanza ni a ±90 min, con
E1 al 60 % alcanza a ±60 min y no a ±30 min):

- **E1 al 60 %**: 60 % o más del terreno bajo (10 a 30 km, bajo 1.300 m) con ACMF 0 o 1, en vez de 80 %. Vale para el
  positivo, el placebo, el control original y la línea base.
- **Línea base a ±60 min** (s − 6 a s + 6) y **placebo a ±60 min**. La ventana está centrada en el minuto del cuadro,
  así que una deriva lineal del ciclo diario se cancela, y es la misma para positivo y placebo.
- **Nulo degenerado = INVÁLIDA** (regla nueva, por lo visto en el paso 2): si el nulo tiene menos de 1.000 réplicas
  válidas o menos de 50 valores distintos, la prueba no recibe veredicto. Pasa cuando los días positivos casi no
  tienen días libres despejados cerca de la misma hora: la permutación sortea siempre el mismo día y el "poder" sale
  1,0 por construcción.

## 3. Ensayo en seco final (decide validez antes de medir)

| Prueba | Unidades válidas (de) | Días | Falsa alarma | Nulo: válidas / distintos | Poder ε 0,05 / 0,10 / 0,15 / 0,30 | Estado |
|---|---|---|---|---|---|---|
| Paso 2 | 11 (38) | 3 | 0,000 | 283 / 2 | 1,00 / 1,00 / 1,00 / 1,00 (artefacto) | **INVÁLIDA**, nulo degenerado |
| H3 | 12 (34) | 3 | 0,038 | 1.411 / 72 | 0,10 / 0,06 / 0,14 / 0,95 | válida |
| β73 | 13 (43) | 3 | 0,000 | 967 / 13 | 0,18 / 0,43 / 0,92 / 1,00 | **INVÁLIDA**, nulo degenerado |
| VAAC de Londres | 11 (40) | 3 | 0,000 | 967 / 13 | 0,18 / 0,57 / 0,92 / 1,00 | **INVÁLIDA**, nulo degenerado |
| H13 | 30 (66) | 5 | 0,000 | 1.431 / 88 | 0,06 / 0,07 / 0,18 / 1,00 | válida |
| H11 y H12 (H3 ∪ β73) | 24 (60) | 5 | 0,059 | 1.587 / 136 | 0,11 / 0,16 / 0,65 / 1,00 | válida |

(Unidades de "de": cuadros con huella de 3 píxeles o más fuera del cráter.)

**Lo que se sabe antes de medir:** ninguna prueba válida tiene poder 0,80 para la capa de referencia (ε 0,10). Si no
sale p ≤ 0,05, el veredicto será SIN PODER, no NO ERA ESO. El poder a ε 0,30 (0,95 a 1,00) sí permite decir que una
capa gruesa no pasó desapercibida, y se informa así, como lectura secundaria y no como veredicto.

Las tres inválidas se informan igual (S, E_orig, AUC, chequeo C) como descripción, sin veredicto.
