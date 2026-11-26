**Veredicto: REDUCE EL SESGO Y EL TRAMO QUEDA NO DECIDIBLE. Medido cada píxel contra lo que él mismo vivió en la temporada de 2025, el anillo deja de preferir la cordillera alta del SE (64 % de los disparos al SE baja a 31 % en 2025 y a 19 % en 2024, cerca de lo que da el método solo), con la misma falsa alarma. Pero no por eso encuentra la pluma donde VOLCAT la dibuja: a la hora de los cuadros de VOLCAT dispara la mitad de veces (11 de 54 contra 23 de 54), sus píxeles siguen lejos del cráter, y con 11 cuadros en 3 días no marca ni el tramo de 4 a 15 km (1 de 11) ni el rumbo lejano (2 de 11). Post hoc, en 2026 el anillo nuevo se va a disparar de noche hacia el valle, al W y NW, en unas pocas noches sin VOLCAT.**

# S31e: el anillo con cada píxel medido contra su propia temporada. Informe, 26-11-2026

Criterio `criterio_2026-11-26.md` (commit `bc8bde2`, empujado a las 15:58 UTC antes de calcular un solo disparo del
anillo nuevo). Código `scripts/s31e_medir.py` (commit `5de8cf6`, antes de medir). Post hoc `scripts/s31e_posthoc.py`.
Cifras en `resultados/s31e_resultado.json`, `resultados/s31e_posthoc.json` y `resultados/s31e_por_cuadro.csv`. Tablas del
anillo nuevo, S y k* por cuadro y registros en `D:\goes_notas\s31\s31e\`. **Desarrollo, no confirmación:** los días de
2024, 2025 y 2026 (hasta el 24-11) ya los habían visto otras sesiones. Ningún día posterior al 24-11; nada de
`s23b_confirmar.py`, `s30a_confirmar.py` ni del CSV de días nuevos. El anillo congelado de S26a no se tocó.

## 1. Para geólogo

**La pregunta.** El anillo del detector S26a busca, en doce tajadas de 30° entre 4 y 40 km del cráter de Nevados de
Chillán, la tajada cuyos 8 píxeles de BTD 11 − 12 µm más bajos (ya restada la línea base de cada píxel) están más abajo
que el resto. S31d mostró que en 2025, sin pluma, ese anillo prefiere el SE porque los píxeles altos de la cordillera, a
23 a 33 km, se apartan de su promedio más que los del valle; y S31c, que en 2026 marca ese mismo tramo lejano y no el de
4 a 15 km donde VOLCAT dibuja la pluma. La pregunta de S31e: si a cada píxel se le pregunta "qué tan raro es hoy para ti"
en vez de "cuántos kelvin bajaste", ¿desaparece la preferencia por la cordillera, y aparece entonces la pluma junto al
cráter?

**La corrección.** Cada residuo se convirtió en su lugar dentro de la distribución propia de ese píxel en oct-nov 2025 a
la misma hora (±90 min), pasado a la escala de una normal (T1). Así, un píxel de cordillera que baja 0,6 K una vez por
semana pesa lo mismo que uno del valle que baja 0,3 K una vez por semana. El resto del detector quedó igual, y el umbral
se fijó para que en 2025 dispare igual o menos que el congelado (percentil 5,00: 3,2 % de los cuadros por día contra
4,0 %). Como sensibilidad, sólo dividir por la dispersión de cada píxel (T2).

**Lo que salió.**

- **La cordillera deja de ganar.** En 2025 los disparos al SE bajan de 64,5 % a 31 %, cuando el método solo daría 19 %:
  el exceso cae de 0,44 a 0,13 y su intervalo ya incluye cero (MEJORA PARCIAL por la regla, porque pasa el margen de
  0,10). En 2024, fuera de muestra, el SE queda en 19 % contra 23 % del método: sin sesgo (MEJORA). Los disparos de 2025
  se reparten en 22 días en vez de 15. La tajada de 120° a 150° sigue siendo la que más dispara (36 de 134), pero ahora
  la siguen el W y el NW (270° a 300°: 20) y el NE.
- **No cuesta falsa alarma.** En 2024 dispara 2,5 % de los cuadros por día contra 1,4 % del congelado; la diferencia no
  se separa de cero (IGUAL), y queda bajo el 5 %.
- **Pero tampoco ve mejor la pluma.** A la hora de los cuadros de VOLCAT alcanza 11 de 54 (el congelado 23 de 54); la
  diferencia toca justo el cero (IC −0,39 a 0,00, IGUAL por la regla, en el borde). Con esos 11 cuadros en 3 días, sólo
  1 tiene un píxel del disparo dentro del tramo de 4 a 15 km de la huella de VOLCAT, y sólo 2 apuntan a su rumbo lejos.
  Nada pasa ningún nulo: **el tramo queda NO DECIDIBLE**. No es falta de poder de la prueba: el oráculo (VOLCAT un cuadro
  antes) sigue pasando el nulo G con 41 de 87 (p 0,0001).
- **La cola se aleja todavía más del cráter.** En 2025 los 8 píxeles de la cola de cada disparo están a 34 km de mediana
  (el congelado 27,6 km), y sólo 1 % a menos de 15 km (el congelado 4,3 %).
- **Le cuesta a una pluma de libro.** Con una firma de 0,97 K inyectada a lo largo de un rayo, el anillo nuevo dispara
  en 34 % de los casos contra 57,5 % del congelado; hacia el SE, 15 % contra 40 %. Es el precio anunciado en el criterio:
  en la cordillera una pluma tiene que bajar más para verse rara.
- **T2 (sólo la escala) va en la misma dirección y peor:** sesgo SE 35 % en 2025 (MEJORA PARCIAL), pero en 2026 alcanza
  1 de 54 cuadros de VOLCAT (PIERDE ALCANCE) y el tramo no se puede evaluar.

**Lectura honesta.** La corrección hace lo que S31d predijo: la preferencia del anillo por la cordillera del SE era la
distribución propia de esos píxeles, y al medir cada píxel contra sí mismo se va. Lo que no aparece es la pluma junto al
cráter. Con la preferencia por la cordillera quitada, el anillo dispara menos a la hora de VOLCAT y, cuando dispara,
sigue mirando lejos; o sea, buena parte de lo que el congelado "alcanzaba" en 2026 venía de la cordillera encendida a esa
hora, y lo que queda no se distingue del azar con tan pocos cuadros. Esto calza con la hipótesis de S31c (junto al cráter
la pluma es opaca o muy chica para la firma 11 − 12 µm en píxeles de 2 km) y con S17 (H22 y H23) y S19i (la pluma diaria de
Chillán vive casi siempre bajo lo que el IR de GOES separa en 2 km), pero no lo prueba.

**Lo que apareció sin buscarlo (post hoc, §3).** El anillo nuevo dispara en 2026 en el 7,2 % de los cuadros sin VOLCAT
(el congelado 0,7 %), casi todo de noche y hacia el valle, al W y NW (72 de 94 disparos entre 210° y 360°, 57 de noche,
la mayoría la noche del 05-11 y la del 08-11). Los píxeles del valle tienen distribuciones angostas en 2025; cualquier
cosa que en 2026 los mueva un poco (humedad o inversión distinta, humo, un cambio de un año a otro) los vuelve "raros".
Es el costo de calibrar contra un solo año: T1 traslada el sesgo de la cordillera a los píxeles más tranquilos.

## 2. Cifras del criterio

| Medida | Congelado (p 4,75) | T1, principal | T2, sensibilidad |
|---|---|---|---|
| Comprobación de código | 138 disparos 2025, 38 en 2024, tabla de S26a sin una fila distinta, 23 de 54 P, E₁ 0,2059 de S31d, tramo de S31c con los mismos p hasta el cuarto decimal | válida | |
| Percentil fijado en 2025 (§3) | 4,75 | **5,00** | 4,50 |
| Falsa alarma 2025, media por día / global | 0,0400 / 0,0376 | 0,0316 / 0,0365 | 0,0393 / 0,0314 |
| (a) Falsa alarma 2024, media por día (45 días) | 0,0142 | 0,0247; dif +0,011 (IC −0,011 a 0,035): **IGUAL** | 0,0115; dif −0,003 (IC −0,009 a 0,004): IGUAL |
| (b) Sesgo 2025: disparos, días | 138, 15 | 134, 22 | 115, 18 |
| (b) Cuota SE 2025 / E₁ / exceso (IC 95 %) | 0,645 / 0,206 / 0,44 (0,15 a 0,67) | 0,313 / 0,185 / 0,13 (−0,07 a 0,29): **MEJORA PARCIAL** | 0,348 / 0,192 / 0,16 (−0,05 a 0,41): MEJORA PARCIAL |
| (b) Réplica 2024: cuota SE / E₁ / exceso | 0,737 / 0,222 / 0,51 (0,15 a 0,78) | 0,193 / 0,234 / −0,04 (−0,19 a 0,28), 57 disparos en 15 días: MEJORA | 0,357 / 0,187 / 0,17; 28 disparos: NO DECIDIBLE |
| (c) Alcance en P de VOLCAT 2026 (7 días) | 23 de 54 | 11 de 54; dif −0,22 (IC −0,39 a 0,00): **IGUAL** (en el borde) | 1 de 54; dif −0,41 (IC −0,69 a −0,14): PEOR |
| (d) Tramo, P evaluados (días) | 23 (4) | 11 (3: 29-10, 08-11, 11-11) | 1 (1) |
| (d) `px_cerca` | 6 de 23; p_G 0,94, p_R 0,0012 | 1 de 11; p_G 0,84, p_R 0,17, p_D 0,65 | 0 de 1 |
| (d) `rumbo_lejos` | 12 de 23; p_R 0,0068 | 2 de 11; p_R 0,41, p_D 0,73 | 0 de 1 |
| (d) Oráculo, `px_cerca` | 41 de 87; p_G 0,0001 | 41 de 87; p_G 0,0001 | 41 de 87; p_G 0,0001 |
| (d) Veredicto del tramo (regla de S31c) | SÓLO LEJOS | **NO DECIDIBLE** (nada pasa) | NO DECIDIBLE (pocos) |
| **Titular** | | **REDUCE EL SESGO Y EL TRAMO QUEDA NO DECIDIBLE** | REDUCE EL SESGO Y EL TRAMO QUEDA NO DECIDIBLE, PIERDE ALCANCE |

Descriptivos (no deciden):

| | Congelado | T1 | T2 |
|---|---|---|---|
| Cola de los disparos 2025: mediana (cuartiles) | 27,6 km (23,4 a 33,3) | 34,0 km (29,8 a 37,7) | 33,1 km (26,9 a 36,8) |
| Cola 2025 a 4 a 15 km | 4,3 % | 1,0 % | 2,8 % |
| Tajadas de los disparos 2025 (0° a 330°, de a 30°) | 9, 10, 1, 0, 41, 13, 35, 16, 6, 1, 4, 2 | 3, 17, 9, 14, 36, 6, 0, 3, 13, 20, 7, 6 | 8, 0, 0, 0, 14, 16, 10, 28, 19, 8, 6, 6 |
| Disparos 2026 hasta el 24-11 | 52 | 94 | 15 |
| Tasa de disparo en cuadros N de 2026 (1.010) | 0,7 % | 7,2 % | 0,6 % |
| Poder sintético, firma 0,97 K (rayo SE / fuera del SE) | 0,575 (0,40 / 0,64) | 0,34 (0,15 / 0,41) | 0,495 (0,35 / 0,55) |
| Poder sintético, firma 0,33 K | 0,010 | 0,025 | 0,015 |
| Píxeles que usaron el pozo de su tajada (menos de 20 valores) | | 34 de 3,4 millones en 2025; 550 de 1,7 millones en 2026; 588 de 2,5 millones en 2024 | igual |

Por qué el tramo de T1 cae en NO DECIDIBLE y no en SÓLO LEJOS: la regla de S31c pide para SÓLO LEJOS que el rumbo lejano
pase el nulo de la huella girada; con 2 de 11 no pasa (p_R 0,41). El anillo nuevo ya no apunta al lado de la pluma, que
era justamente lo que el congelado compartía con la cordillera del SE.

## 3. Post hoc (no decide; escrito después de ver la medida)

**Dónde dispara T1 en 2026.** 94 disparos en 14 días: 73 en cuadros N de VOLCAT, 6 en P, 8 sin clase, 7 de otra clase.
Tajadas: 210° a 360° (W y NW) 72, de ellos 57 de noche y en 7 días; la noche del 05-11 sola tiene 30 (todos N), la del
08-11 18, y el día del 07-11 12. El congelado, en cambio, tiene 16 de sus 52 disparos de 2026 en cuadros P y sólo 7 en N.
No sé qué pasa en el valle esas noches; lo que sí se ve es que el anillo nuevo responde a algo que en 2025 casi no ocurrió
en esos píxeles, sin pluma de VOLCAT encima. En 2024 sus disparos también se cargan al W y NW (tajadas de 240° a 360°: 35
de 57).

**La cola evita el tramo cercano también sin pluma.** En los disparos de 2025, un píxel cualquiera de la tajada del
disparo estaría a menos de 15 km el 10,3 % de las veces (congelado) o el 9,5 % (T1); la cola de 8 lo está el 4,3 % y el
1,0 %. O sea, el anillo aparta su cola del cráter **en un año sin pluma** a menos de la mitad de lo que daría el azar dentro
de la tajada, y con T1 más todavía. Esto toca a S31c: allí, con pluma, el tramo cercano cayó "menos que un píxel cualquiera
de la tajada" (p_G 0,94), y se leyó como que el detector no ve el tramo de VOLCAT. Esa lectura sigue en pie, pero ahora se
sabe que el nulo G de S31c no tenía en cuenta que la cola del anillo esquiva por sí sola los píxeles cercanos; el
resultado de S31c no cambia de rótulo (un p_G de 0,94 no se vuelve bajo con un nulo más justo), pero su expectativa al azar
(0,38) era optimista. Hipótesis sin medir: los valores bajos llegan en manchas de varios píxeles vecinos, y en el vértice
angosto de cada tajada (8 a 10 píxeles a menos de 15 km) no cabe una mancha; con T1, que quita la dispersión propia de los
píxeles altos del volcán, sólo queda esa geometría.

## 4. Cómo se corrió

Una sola corrida de `s31e_medir.py medir`, 1.135 s, sin caídas (registro en `D:\goes_notas\s31\s31e\medir.log`). La
comprobación de código, dentro del mismo script y antes de calcular nada con T1 o T2, reprodujo el anillo congelado por
completo con z = r: los 138 disparos de 2025 con sus tajadas y su falsa alarma (0,03998573), los 38 de 2024 con sus
tajadas, la tabla de S26a cuadro por cuadro (disparo, tajada, cola y evaluación, ninguna fila distinta), 23 de 54 P, el E₁
de S31d (0,2059 y su IC) y la prueba del tramo de S31c con los mismos p (6 de 23, p_G 0,9397; 12 de 23, p_R 0,0068; SÓLO
LEJOS; oráculo 41 de 87). El post hoc (`s31e_posthoc.py`) lee las tablas guardadas y rearma el detector de 2025; no cambia
ninguna cifra del criterio. Lo usado en D: es menos de 1 MB; quedan 24 GB libres.

## 5. Lo que no puede decir

- Que el anillo no vea la pluma: con 11 cuadros en 3 días el tramo es NO DECIDIBLE, no un "no". Tampoco que lo que el
  congelado alcanzaba fuera sólo terreno: el alcance baja a la mitad, pero la diferencia toca el cero.
- Qué mueve los píxeles del valle las noches del 05 y 08-11 de 2026 (post hoc, sin medir).
- Si una referencia de varios años (2024 más 2025) arreglaría el traslado del sesgo al valle: no se probó.
- Nada de días posteriores al 24-11, ni de ceniza ni de altura. Nada de esto es confirmación.

## 6. Qué sigue (para la coordinadora y Nicolás)

1. **No adoptar T1 como detector.** Quita el sesgo de la cordillera, pero pierde la mitad del alcance, pierde poder en el
   SE (donde va la pluma) y en 2026 se enciende sobre el valle. Como herramienta de diagnóstico sí sirve: dice que lo que
   el congelado marcaba al SE lejano a la hora de VOLCAT era, en buena parte, la cordillera.
2. **Leer el anillo congelado con eso en mente**: su coincidencia con VOLCAT en 2026 es de hora y rumbo, y el rumbo lo
   pone en buena parte el terreno. Esto pesa sobre cómo leer un CONFIRMA del anillo o de la unión en días nuevos (la
   confirmación congelada no se toca).
3. **Si se quiere seguir con el anillo**, lo que este resultado señala es que el problema no es sólo la escala de cada
   píxel sino la forma de la tajada: la cola de 8 esquiva el vértice cercano al cráter aun sin pluma (§3). Una corona
   cercana con su propia regla (la zona del cráter de S25a ya es eso, hasta 4 km) parece más prometedora que seguir
   ajustando el anillo de 40 km. Con criterio nuevo y como desarrollo.
