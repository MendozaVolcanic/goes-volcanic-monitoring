# S20c: enmienda 1, antes de medir (23-11-2026)

Se sube junto con el ensayo en seco del diseño 2 y antes de leer la BTD, la BT11 o sus cambios en los cuadros
positivos y en los controles originales. Cambia los §4, §6 y §8 del criterio (`criterio_2026-11-23.md`, commit
`b06c711`); lo demás queda igual (pozos de días, huellas, variable principal, control positivo, umbrales del
veredicto).

## 1. Qué mostró el ensayo en seco del diseño 1

Diseño 1 = la regla de pareo de las pruebas viejas (control = día del pozo limpio con la mediana de BT11 de la huella
más parecida, a 3 K o menos) con el pozo cambiado. Salidas: `resultados/seco_v1_pareo.json`, `seco_v1_pareo.log`,
`diag_cobertura_v1.log`; script `scripts/s20c_medir_v1_pareo.py` y `scripts/s20c_diag_cobertura_v1.py`.

- **Cobertura de 3 a 27 %**, muy bajo el 50 % que pedía el criterio, con la condición ACMF en el control y sin ella
  (la vía de reemplazo del §6.3 tampoco alcanza). Ninguna prueba se habría podido medir.
- La causa: el mejor control limpio queda, en mediana, **a 9 K de BT11 de la huella del positivo** (cuartiles 8 y
  12 K), y es **más frío**: −9,1 K, control menos positivo. Los positivos son tardes despejadas de fines de octubre y
  noviembre; los cuadros despejados del 21-09 al 21-10 a la misma hora tienen la cumbre más nevada y menos sol. Es la
  temporada, no la pluma (9 K es de 5 a 20 veces lo que hace una capa de ε 0,10 a 0,15, H23).
- Los días placebo están **despejados (regla E1) en sólo 3 a 9 % de los minutos de los positivos**, contra 57 a 80 %
  de los positivos. Sin la condición ACMF el placebo encuentra control a 0,4 K: son cuadros nublados contra cuadros
  nublados del pozo limpio. Ese placebo mediría nubes, no temporada.

**Lectura que ya se puede escribir** (no usa la variable de resultado): la regla de pareo de las pruebas viejas no
podía encontrar controles limpios. Con "BT11 parecida a 3 K" al mismo minuto, los únicos candidatos tibios y
despejados eran días de noviembre, y los días de noviembre despejados eran justo los días con el volcán activo. La
contaminación de MET-01 no fue mala suerte: la regla la imponía.

**Aviso de honestidad.** El diagnóstico de cobertura leyó la BT11 mediana de la huella de los positivos (variable de
pareo, permitido por el §6.3) y con eso se vio que el pozo limpio está 9 K más frío. La BT11 queda en este informe
como variable secundaria, informativa y leída en parte; no decide nada.

## 2. Diseño 2 (reemplaza el §4 del criterio)

- **Todo cuadro que hace de "x" tiene que estar despejado** (regla E1 de H23 y H24, `h24_medir.despejada("chillan")`):
  el positivo, cada cuadro placebo y cada control original del chequeo C. Es lo que pedía MET-02 ("sin pareo y con
  escena despejada por ACMF en los dos lados"). Un positivo nublado queda fuera.
- **Sin pareo por BT11.** El control es la **línea base limpia del propio píxel**: mediana, píxel a píxel, de la
  variable en los cuadros despejados (E1) del pozo limpio (21-09 al 21-10) en s − 1, s y s + 1, con 3 o más días con
  dato en el píxel (la línea base D2 de H23 y H24, pero sólo con días anteriores a toda actividad).
  Anomalía de un cuadro: Δv(x, s) = mediana sobre F de [v(x, s, p) − base(s, p)].
- **Placebo**: los cuadros despejados de los 14 días libres a ±30 min del minuto del positivo (s − 3 a s + 3), cada uno
  contra la línea base de su propio minuto. Referencia del positivo = mediana de esas anomalías, con 3 cuadros o más
  de 2 días o más. Se amplía de 7 días al mismo minuto a 14 días y ±30 min porque sólo 3 a 9 % de esos cuadros están
  despejados.
- **Señal**: d = Δv(positivo) − referencia; S_T = mediana de d sobre las unidades válidas.
- **Nulo de bloques de día** (2.000 réplicas, semilla 20261123): para cada día positivo se sortea un día libre j*;
  cada cuadro de ese día se reemplaza por el cuadro despejado de j* más cercano en minuto (si j* no tiene ninguno a
  ±30 min, ese cuadro sale de la réplica), contra la referencia sin j*. p de una cola como en el criterio.
- **Control positivo**: la misma capa del §5, pintada en el cuadro de j* que entra a la réplica.
- **E_orig**: como en el criterio, pero sobre las mismas unidades válidas que S_T (para que las dos cifras hablen de
  los mismos cuadros).
- **Chequeo C**: el control original de la prueba vieja (si cae en un día excluido por actividad), despejado, con la
  misma huella, contra la línea base limpia y su placebo.
- **AUC**: positivo contra línea base, placebo contra línea base, AUC_orig contra el control original; descriptivas.

## 3. Cobertura y validez (reemplaza el §6.3)

Una prueba con **menos de 10 unidades válidas o menos de 2 días positivos válidos** queda **SIN COBERTURA** y no
recibe veredicto. Sin vía de reemplazo: el ensayo en seco del diseño 1 mostró que el placebo sin condición ACMF mide
nubes. La falsa alarma y el poder se leen en `resultados/seco.json` como dice el §6 del criterio.

## 4. Sensibilidades (reemplaza el §8)

- **S1, anillo**: la anomalía de F menos la anomalía del anillo (2 a 5 píxeles de F), en el mismo cuadro. Resta lo
  común a la zona (humedad, temporada del entorno). Para BTD y para BT11.
- **S2, sin condición ACMF** en el cuadro x (placebo de los 14 días al mismo minuto, sin despejado): se informa sólo
  para mostrar cuánto mueve; por el §1, no es una medición válida de temporada.
- **S3** huellas guardadas de H3 y β73; **S4** con el bloque del cráter; **S5** BT11, ΔBTD y ΔBT11 (ΔBTD y ΔBT11 con p
  de dos colas).

## 5. Lo que cambia en la lectura

Con línea base en vez de pareo, la diferencia ya no está atada a la BT11 del positivo (MET-02 deja de aplicar) y la
BT11 deja de estar anulada. El precio: el resultado depende de que el placebo (cuadros despejados de días libres de
fines de octubre y noviembre) represente bien la temporada de los positivos. Si los días libres tuvieran pluma no
documentada, S_T se achica hacia cero (el sesgo va contra encontrar señal, no a favor).
