# S25b: el detector de S23 en oct-nov 2024, otro año tranquilo y otro satélite. Informe, 25-11-2026

Criterio `criterio_2026-11-25.md` (commit `b07cb58`), empujado antes de armar el cubo de 2024. Código en
`C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\Goes\docs\own_volcat\s25b_fondo_2024\scripts\` (en main desde el
merge de S25b): `s25b_bajar_2024.py` (bajada GOES-16), `s25b_vigia.py` (relanza la bajada si se estanca),
`s25b_medir.py` (`pruebas`, `cubo`, `medir`), `s25b_posthoc.py`. Resultados en `resultados/`. Datos en
`D:\goes_notas\s25\s25b_2024\` (L1B, ACMF y cubos; 0,7 GB).

**En una línea: el umbral de 2025 aguanta otro año.** Aplicado a oct-nov 2024 sin recalibrar nada, el detector dispara
en 1,5 a 1,6 % de los cuadros, un tercio de lo que dispara 2025 contra sí mismo (4,3 %). No inventa alarmas al cambiar de
año ni de satélite; si algo, se vuelve más exigente. El umbral propio de cada año difiere en ~0,1 K, del orden de su
propio ruido de muestreo, pero con un patrón por hora que no es azar.

## 1. Para geólogo

**El fenómeno y la duda.** El detector busca, alrededor del cráter, una tajada donde la diferencia entre 11 y 12 µm
(BTD) cae bajo lo normal: la ceniza fina absorbe más a 11 µm que a 12 µm y deja esa firma negativa. "Lo normal" (la línea
base de cada píxel a cada hora, y el umbral de alarma, el 5 % más bajo de lo que se ve sin pluma) sale de oct-nov 2025,
el único año tranquilo que se había bajado, porque en 2026 Chillán tiene pluma todos los días. La duda era si ese "normal"
es de Chillán en primavera o sólo de la primavera de 2025: otro año trae otra nieve, otras nubes bajas, otras
inversiones. Si el umbral sólo vale en 2025, lo que el detector marca en 2026 podría ser "2026 no es 2025" y no pluma.

**El año de prueba.** Oct-nov 2024: Chillán en alerta técnica verde, sin actividad superficial reportada (el único
reporte especial de la ventana, el REAV del 15-11-2024, es un sismo volcano-tectónico de ML 3,0 a 4,6 km, "alerta técnica
VERDE se mantiene"). El satélite de entonces era GOES-16, en la misma posición que GOES-19 hoy (75,2° O) y con la misma
grilla: un cambio de año y de instrumento a la vez, la prueba más dura que se podía hacer con datos públicos.

**Lo que salió.**

- **La geometría calza.** Los mapas de noches despejadas de 2024 y 2025 correlacionan 0,987 y la proyección de los dos
  satélites es idéntica. Bajó el 99 % de los cuadros de 11 y 12 µm y el 98 % de la máscara de nubes (lo que falta no
  existe en NOAA).
- **Fuera de su año, el detector dispara menos, no más.** Con línea base y umbral de 2025, en 2024 dispara en 1,6 % de
  los cuadros evaluados (versión S23a) y 1,5 % (versión S23b, con el nublado de costumbre de 2024). En 2025, medido
  contra sí mismo, disparaba 4,3 %. Ninguna franja de 3 horas pasa del 5 % (la más alta, 09 a 11 UTC, la madrugada local).
  En las noches comunes (las que no tienen un episodio de capa baja) dispara 0 de 917 cuadros, como el 0,14 % de 2025.
- **Las falsas alarmas siguen viniendo en racimos.** El 68 % de los disparos de 2024 (versión S23b) cae en tres días
  seguidos, 16 a 18-11-2024, y el resto en cinco días sueltos. Lo mismo que en 2025, donde cinco noches ponían el 85 %:
  el fondo no dispara parejo, dispara en episodios de tiempo. Qué tiempo hubo esos días no lo sé; ver §4.
- **El umbral de cada año es parecido, pero no igual.** Si a 2024 se le saca su propio umbral, difiere del de 2025 en
  0,10 K de mediana (2024 menos exigente de noche, en +0,1 a +0,2 K, y más exigente de madrugada, 09 a 11 UTC). Partir
  2025 en días pares e impares da diferencias del mismo tamaño (0,09 K), así que la diferencia entre años es del orden
  del ruido del propio umbral; pero el patrón por hora es sistemático, no azar: las noches de 2025 fueron más variables
  que las de 2024 y las madrugadas de 2024 más que las de 2025.

**Lectura honesta.** Que el detector dispare menos fuera de su año tiene dos caras. La buena: los 25 de 54 cuadros de
VOLCAT que la candidata S23b alcanza en 2026 no se explican por "el umbral se descalibra en otro año"; con el azar de
2024 en vez del de 2025, esos 54 cuadros esperarían 1,2 alcances en vez de 2,6 (post hoc, §3). La mala: un umbral más
exigente que lo necesario cuesta poder; las plumas débiles que el detector ya no ve (poder 0,01 a 0,33 K, S23) serán aún
más difíciles en un año cuyo fondo sea más tranquilo que 2025.

## 2. Veredictos por el criterio

| Pregunta | Resultado | Veredicto |
|---|---|---|
| (a) Instrumento I1 a I5 | L1B 99,0 %, ACMF 98,3 %; 0 scans distintos, 0 congelados; BT11 en rango 100 %; I4 0,987 (892 cuadros nocturnos despejados de 2024 contra 1.255 de 2025); I5 proyección igual (−75,0°, 35.786.023 m) | **COMPARABLE** |
| (a) Calibración (informativa) | Planck de GOES-16 y GOES-19 difieren (filtros distintos: fk1 de C15 −0,5 %, bc1 de C14 +7 %), cada año con los suyos. Noches despejadas, 2024 menos 2025: BT11 −0,55 K, BTD +0,10 K (mezcla instrumento y tiempo); M1 del anillo +0,015 K de mediana, correlación 0,69 | no decide |
| (b) S23a en 2024 (base, umbral y costumbre de 2025) | FA24 0,016 (1.667 cuadros evaluados, 46 % pasan la compuerta de nubes); franja máxima 09-11 UTC 0,052; noche 0,006, noches comunes 1 de 905 | **AGUANTA**, MÁS ESTRICTO |
| (b) S23b en 2024 (base y umbral de 2025, costumbre de 2024) | FA24 0,015 (2.448 evaluados, 51 % pasan); franja máxima 09-11 UTC 0,049; noche 0,013 (13 disparos, todos 16 y 18-11), noches comunes 0 de 917 (Fisher contra 2025, p 0,52) | **AGUANTA**, MÁS ESTRICTO |
| (c) U24 contra U25, 144 cuadros del día | mediana \|ΔU\| 0,098 K; máximo 0,255 K (23:20 UTC); con signo, U24 − U25 = +0,08 K de mediana. Ruido de muestreo (2025 pares contra impares): mediana 0,093, máximo 0,31 | **INTERMEDIO** (la mediana cumple ESTABLE; el máximo pasa el 0,25 por 0,005 K) |

La versión S23b es la que cuenta para su confirmación pendiente en días nuevos: aguanta.

Comprobación de código antes de abrir 2024 (`s25b_medir.py pruebas`): el camino "fuera de muestra" de este script,
aplicado a 2025 con la base de cada día sin sí mismo, reproduce exacto el S, las tajadas y el ensayo en seco de S23
(0,042791).

## 3. Post hoc (mirado después de los veredictos; no los cambia)

`resultados/posthoc_azar_2024.json` (`s25b_posthoc.py`). El p25 de S23b estima el azar por hora con el ensayo en seco
de 2025, que es dentro de la muestra. Con el azar por hora de 2024 (versión S23b), los mismos 54 cuadros P de VOLCAT que
S23b evalúa en 2026 esperan 1,19 alcances en vez de 2,55, y el detector alcanza 25 (reproduce S23 exacto). La fracción de
cuadros alcanzados por azar es 2,8 % en 2024 contra 5,2 % en 2025. El p25 de S23b era conservador. Sigue siendo post hoc:
la regla S23b se eligió mirando esos días; la prueba de verdad es la confirmación en días nuevos.

Los disparos de 2024 por día y tajada están en el mismo JSON (`disparos_2024_S23b_por_dia`). **14 de los 41 caen al
SE (120° a 150°)**, el rumbo donde S23b dispara en 2026 y VOLCAT dibuja la pluma: la noche del 16-11-2024 (07:00 a
08:30 UTC, ocho cuadros) y cuadros sueltos del 21-10, 08-11, 12-11 y 20-11. Los otros racimos van al S (180° a 210°: 05-10
y 17-11 de madrugada, 09:50 a 11:10 UTC) y al N (0° a 30°: 18-11). El rumbo SE no es exclusivo de la pluma, como ya
había visto S24 con la persistencia de rumbo del fondo de 2025.

## 4. Lo que puede estar mal

- **2024 tranquilo lo dice un REAV y la alerta verde, no las cámaras.** Los RAV mensuales de Ñuble de sep a nov 2024 no se
  pudieron recuperar (el sitio nuevo de RNVV no lista reportes viejos y Wayback no los guardó). Si Nicolás confirma con el
  OVDAS que hubo pulsos o desgasificación visible en la ventana, esta prueba pasa a ser "año con pluma conocida" y se
  relee: un año con pluma que dispara menos que 2025 sería otra cosa.
- **Los racimos de 16 a 18-11-2024 no están explicados.** Puede ser tiempo (capa baja, inversión, como las noches de
  2025 en S24) o algo del volcán (el sismo VT del 15-11 es la noche anterior). No se miró el tiempo ni las cámaras.
- **Dos años no son una climatología.** 2024 y 2025 difieren en el patrón horario del umbral; un tercer año podría
  diferir más. La prueba dice que el umbral de 2025 no es anómalo hacia el lado peligroso, no que sea el de todos los años.
- **El cambio de satélite y el de año van juntos.** No se pueden separar con estos datos: GOES-19 no miraba desde 75,2° O
  en 2024.
- **Sólo se probó S23a y S23b.** El mejor detector de hoy es el combinado S26a (zona del cráter S25a O anillo S23b); su
  zona del cráter no se aplicó a 2024 (ver traspaso).
