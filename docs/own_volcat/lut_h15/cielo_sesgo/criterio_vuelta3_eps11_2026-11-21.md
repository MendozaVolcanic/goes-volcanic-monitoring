# Criterio, vuelta 3: el exceso de nuestro ε(11 µm) en nube tenue. 21-11-2026

Escrito y subido antes de medir los cuadros 6 a 10. Base: V1 (ε al nadir con cos θ del píxel), N1 (punto frío
del GFS), S0 (`geocatRTM`), H1 (corrección por vapor de β). Nada se ajusta en esta vuelta: cada candidata hace
una predicción y los cuadros 6 a 10 la confirman o la descartan.

## Qué se sabe antes (cuadros 1 a 5 y vuelta 2)

- Los archivos del caso (`ext\`: logs, alertas, configuración, estructura de los HDF) no dicen qué ángulo usa la
  normalización al nadir. Sólo traen ángulos máximos de detección (80° y 90°), `Maximum_Valid_Viewing_Zenith_Angle`
  = 85, `ASHOBJ_Cos_Satzen_Mean` y `Large viewing angle correction = 0`. Las tablas tienen un eje `cos_satzen`.
- `explorar_c14_1a5.txt`: el desfase del cielo despejado de C14 que haría coincidir nuestro ε(11) con el de VOLCAT
  vale −0,98 K en la mediana (p5 −2,45, p95 +0,27; 151.349 píxeles con 0,05 ≤ ε < 0,3). El de C15, dado el ε(11) de
  VOLCAT, vale +0,01 K. No se ordena con el agua precipitable (ρ +0,006) y apenas con el ángulo (ρ −0,155), la BT
  despejada (−0,008) o la posición (fila −0,13, columna +0,19). Se ordena algo con la BT observada (+0,335) y con ε
  (−0,255). Varía tanto dentro de una celda GFS (sd 0,63 K) como entre celdas (0,61 K). Es en parte un campo suave:
  la diferencia entre vecinos vale 0,32 de su dispersión. Es igual en los 5 cuadros (−0,94 a −1,01 K).
- `posterior_beta_residuo.txt` (vuelta 2, también en los cuadros 6 a 10): el ε(11) de VOLCAT, llevado al oblicuo
  con el cos θ del píxel, y nuestro ε(12) dan su β con mediana −0,0016 a −0,0035.

## Las tres candidatas y lo que predice cada una

**C1, ángulo de la normalización** (cenital a la altura de la nube o de la tropopausa, o normalización por camino
óptico). La normalización por τ es idéntica a la usada: τ = −ln(1 − ε), τ·cos θ da 1 − (1 − ε)^cos θ. Si VOLCAT
normalizara con μ' ≠ μ, el ε(11) oblicuo reconstruido con μ estaría escalado en ln(1 − ε) por μ'/μ, y el β
reconstruido en la vuelta 2 saldría escalado por μ/μ' en todos los tramos. **Se descarta si** en los cuadros 6 a
10 la mediana de (β reconstruido / β de VOLCAT − 1), con β sin la corrección de vapor, queda dentro de ±0,005 en
todos los tramos de ε, y si el cenital a 16 km cambia cos θ menos de 0,005 (geometría; a 31°, 0,0005).

**C2, nube negra con la atmósfera de encima.** Con ε ~ 0,1 el término de la nube pesa poco: Δε ≈ −ε·ΔR_cld /
(R_cld − R_clr). Para dar −0,013 a ε = 0,1 haría falta una radiancia de nube negra un 13 % de (R_cld − R_clr) más
alta, es decir, decenas de kelvin. La nube espesa la fija mucho mejor (vuelta 1: 91 % dentro de 0,01 con
0,85 ≤ ε ≤ 0,98). **Se descarta si** en los cuadros 6 a 10 la nube negra que haría coincidir el ε de VOLCAT en nube
tenue (0,05 a 0,3, con cielo `geocatRTM`) difiere en más de 10 K, en la mediana, de la que lo hace en nube espesa
(0,85 a 0,98). Si una sola nube negra sirviera para los dos regímenes, C2 sigue en pie.

**C3, cielo despejado del mar por emisividad dependiente del ángulo o por otra columna de vapor.** Las dos cosas
mueven 11 y 12 µm en el mismo sentido, y más a 12 µm, que absorbe más vapor y cuya emisividad de mar cae más con el
ángulo. **Se descarta si** en los cuadros 6 a 10 el desfase implícito de C15 (dado el ε(11) de VOLCAT) es menor que
0,2 K en valor absoluto en la mediana mientras el de C14 es ≤ −0,5 K, y si |ρ(desfase C14, agua precipitable)| < 0,2
y |ρ(desfase C14, θ)| < 0,3.

**Si las tres se descartan, se para** (lo pide el encargo) y queda como pregunta para el correo.

## Lo que se reporta igual (no decide)

Con la base (V1, N1, S0, H1), en los cuadros 6 a 10: ε(11) dentro de 0,01 por tramo (0,05 a 0,1; 0,1 a 0,2; 0,2 a
0,3; 0,3 a 0,5; 0,5 a 0,9) y por franja de θ; β(12/11) con H1 por tramo; nivel B con las reglas del frente 1 (κ,
|ΔP| ≤ 0,05, recuperados, por tramo de εtot de VOLCAT).

## Sensibilidad a ±0,015 en ε(11) (no decide; para saber si el residuo importa en Chillán)

Cuadros 6 a 10, píxeles con 0,1 ≤ ε_VOLCAT < 0,2, nivel A (entradas de VOLCAT) con las reglas del frente 1. ε(11)
al nadir ± 0,015, de dos maneras: (a) sólo ε, los β quedan como están; (b) físicamente consistente: ε(12), ε(7,3) y
ε(8,5) oblicuos fijos, y β(12/11), β(7,3/11) y β(8,5/11) recalculados con el ε(11) nuevo (la corrección de vapor se
quita y se vuelve a poner). Métricas contra la P de VOLCAT sin perturbar: mediana y p95 de |ΔP|, fracción con
|ΔP| > 0,05, fracción que cruza 0,5, P_VOLCAT ≥ 0,5 que se pierden y P < 0,5 que pasan a ≥ 0,5.
