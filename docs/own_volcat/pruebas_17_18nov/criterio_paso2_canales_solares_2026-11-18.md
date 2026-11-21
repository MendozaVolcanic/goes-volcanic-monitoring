# Criterio declarado ANTES de medir: paso 2 (H1 b, canales solares de día), 18-11-2026

Pregunta: dentro de la huella VOLCAT anclada al cráter de Chillán, ¿los canales solares (0,64 µm y la
reflectancia de 3,9 µm) distinguen la escena con pluma del mismo lugar a la misma hora en días sin pluma?
Si no la distinguen, la hipótesis de que VOLCAT ve estas plumas por los canales solares pierde su apoyo
principal.

## Datos

- Bandas nuevas por ventana, leídas de `noaa-goes19/ABI-L1b-RadF` como en `fetch_mp.py`: C02 (0,64 µm,
  0,5 km, ventana 4 veces más fina, promediada a bloques de 4 × 4 para volver a la grilla de 2 km),
  C07 (3,9 µm, 2 km) y C14 (11,2 µm, 2 km). Ensayo de disco antes de bajar todo; si el libre baja de
  5 GB, se para.
- Positivos: los cuadros VOLCAT anclados al cráter con huella (`volcat/huellas.npz`, sin dilatar) de
  los días 08, 10, 11 y 14-11, **con sol alto: cenit solar en Chillán < 75°**. Con el sol más bajo la
  reflectancia de 3,9 µm es ruido.
- Controles: el mismo minuto UTC en cada uno de los 10 días negativos (01 a 06, 09, 12, 13 y 15-11),
  la misma huella.

## Señales por píxel (grilla de 2 km)

- r065: factor de reflectancia de C02 (kappa0 × radiancia, del propio archivo), promedio 4 × 4.
- sd065: desviación estándar de r065 a 0,5 km dentro del bloque de 4 × 4 (textura subpíxel).
- r39: reflectancia de 3,9 µm = (L7 − B7(BT11)) / (S7 · cos θ0 / π − B7(BT11)), con B7 la emisión
  térmica a 3,9 µm de un cuerpo a BT11 (Planck con los coeficientes del archivo C07) y S7 la irradiancia
  solar en la banda. **S7 no está en el archivo**: se usa la de un cuerpo negro a 5.778 K a 1 UA
  convertida a número de onda. Esto puede tener un error del orden de 10 a 20 %, así que el umbral
  absoluto de SECO (ρ(3,9/0,65) > 0,5) sólo se informa y no decide.
- ratio = r39 / r065.

## Comparación

- **Control pareado (principal):** para cada positivo, el día negativo cuyo BT11 mediano en la huella
  esté más cerca del BT11 mediano del positivo (mismo lugar, misma hora, estado térmico más parecido).
  Se elige mirando sólo C14, antes de calcular cualquier señal solar.
- Sensibilidad (se informa, no decide): los 10 días negativos juntos.
- Métrica: AUC por píxel (probabilidad de que un píxel de huella con pluma tenga el valor más alto que
  uno del control). Separación = |AUC − 0,5|.

## Decisión

- **Apoya H1 (b)** si al menos una de las tres señales (ratio, r065, sd065) tiene |AUC − 0,5| ≥ 0,20
  con el control pareado. Si el AUC es menor que 0,5 cuenta igual: la pluma puede oscurecer la nieve.
- **Falsa H1 (b)** si las tres tienen |AUC − 0,5| < 0,10.
- Entre medio: no concluyente.
- Se informa por día (08, 10, 11, 14) y la fracción de píxeles con ratio > 0,5 en positivos y controles.
- Tres señales significan tres oportunidades de acertar por azar; por eso el umbral de apoyo es 0,20 y
  no 0,10.

Si cumple, **no se construye el prototipo (paso 5)**: eso lo decide Nicolás. No cambia código de detección.
