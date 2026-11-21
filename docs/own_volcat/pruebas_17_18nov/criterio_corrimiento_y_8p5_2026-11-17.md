# Criterio declarado ANTES de medir (sesión investigación VOLCAT vs detector, 17-11-2026)

Datos: los mismos del informe del detector (cache 83x94 de C11/C14/C15, huellas VOLCAT sin dilatar en
`volcat/huellas.npz`, referencia de cielo despejado N=10, k=3 de `variantes_mascara.referencia`). Sólo
lectura; nada nuevo bajado.

## Prueba A: ¿la huella VOLCAT está corrida respecto de donde ABI ve la pluma? (paralaje u otra causa)

Geometría (src/process/parallax.py): en Chillán el ángulo cenital de GOES-19 es 42,9°, tan = 0,93. Una
nube a h km sobre el elipsoide aparece en la imagen ABI nativa ~0,93·h km más al SUR (casi sin
componente E-O) de su posición real. Un píxel de la ventana mide 2,84 km N-S y 2,09 km E-O.
Si SSEC dibuja la ceniza ya corregida por paralaje, la señal en la grilla ABI nativa debe estar al sur de
la huella: 1 a 2 filas para 3 a 5 km, 3 a 4 filas para 8 a 12 km.

Medición: para cada cuadro positivo (57, toca_crater_10km = 1), mover la huella (sin dilatar) dy filas y
dx columnas, dy, dx en -5..5, y promediar ΔBT11 dentro. Agregar con la mediana de los cuadros.
Nulo: la misma huella aplicada a escenas de días negativos (01-06, 09, 12, 13, 15-11) en el mismo slot
UTC (el primer día negativo con dato y referencia), mismo procedimiento.

- **Confirma corrimiento** si el mínimo agregado de ΔBT11 (positivos menos nulo) está a 1 o más filas al
  SUR del origen (dy ≥ +1, |dx| ≤ 2) y es al menos 1 K más negativo que en (0, 0).
- **Falsa** si el mínimo está en (0, 0) o a menos de 1 K de él, o si está al norte (dy < 0).
- Cualquier otro resultado (mínimo lejos en E-O) se informa como "corrimiento no explicado por
  paralaje", sin forzar la lectura.

## Prueba B: ¿la banda de 8,5 µm separa la huella del nulo mejor que la BTD 11-12?

Señales por píxel, como anomalía respecto de la referencia del propio píxel: ΔBTD (11-12), ΔD85 =
Δ(BT8,5 − BT11) y ΔBT11. Comparar los píxeles de la huella en positivos contra los mismos píxeles
(misma huella) en el nulo. Métrica: AUC (probabilidad de que un píxel de huella tenga la anomalía más
negativa que uno del nulo). Se mide en la huella sin corrimiento y, si la prueba A confirma, también en
la huella corrida.

- **Apoya que VOLCAT usa la información de 8,5 µm** si AUC(ΔD85) ≥ 0,70 y supera a AUC(ΔBTD) en al
  menos 0,10.
- **Falsa** si AUC(ΔD85) < 0,60.
- Entre 0,60 y 0,70: no concluyente.

Ninguna de las dos pruebas cambia código de detección. Son diagnósticos para ordenar hipótesis.
