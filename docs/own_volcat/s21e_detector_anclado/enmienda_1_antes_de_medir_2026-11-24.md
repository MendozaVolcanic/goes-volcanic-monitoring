# S21e, enmienda 1 (antes de medir), 24-11-2026

Escrita, commiteada y empujada antes de correr el ensayo en seco y antes de calcular M1, D o S en un solo cuadro de
los días con actividad (incluidos los cuatro positivos). Lo único leído hasta aquí: la grilla, la cota, los cubos
para comprobar que M1 vectorizado reproduce `h29_medir.Medidor.medir` (cinco cuadros de días sin pluma), y la
regla E1 (ACMF) en el pozo, en los días placebo y en los cuatro cuadros positivos.

## 1. Comprobaciones contra el criterio (calzan)

- Píxeles de verdad, cuadros y firmas: `s20b_verdad_alta_res/resultados/s20b_resultado.json` da (43, 44) con f 0,181
  el 25-10 en 14:20 y 14:30, y (44, 46) con f 0,427 el 08-11 en 14:40 y 14:50. La firma M1 menos su base es
  −1,388 − (−0,421) = −0,967 K (25-10 14:30), −2,030 − (−0,570) = −1,460 K (08-11 14:50) y −1,323 − (−0,480) =
  −0,843 K (08-11 14:40). Calza con la tabla del §4.
- Los cuatro cuadros positivos existen en los cubos y están despejados por E1 (80 %).
- Días placebo: los 14 de S20c (`s20c_medir.PLACEBO`), ninguno en `H24.EXCLUIDOS` ni en el pozo. Días con actividad:
  `h24_medir.py` L68 a L72, iguales a la lista del §3.
- Los 60 cuadros de VOLCAT (`hora` de `eventos_chillan_cuadros.csv`) tienen 4 nacimientos (`nacimiento` = True):
  13-11 19:00, 14-11 12:40, 14-11 16:30 y 18-11 10:10, los del §0.

## 2. Diferencias con el texto del criterio (no cambian la regla; se dejan escritas)

1. **Cráter.** El criterio dice cráter en (42, 46), igual que `s20c_medir.CRATER_PX`. El píxel más cercano a la
   coordenada del cráter en `latlon.npz` es (41, 46) a 1,18 km; (42, 46) está a 1,82 km. Los dos quedan dentro del
   bloque de 3 × 3 centrado en (42, 46). Se usa (42, 46) como está escrito, y la distancia de Z y del control se mide
   desde la coordenada del cráter de H29 (−36,863, −71,377), en el suelo con `latlon.npz`.
2. **Tamaño de Z.** Z tiene **65 píxeles**, no "unos 100" (§0 era una estimación). El control a más de 15 km tiene
   7.684 píxeles.
3. **Ventana de U.** A las horas de los positivos hay 15 a 19 cuadros placebo despejados por E1 a ±60 min (antes de
   exigir que el cuadro se pueda evaluar). Por la regla del §3, U se abre a ±120 min. No es un cambio: es la regla.

## 3. Precisiones de lo que el criterio no fija

1. **M1.** Se calcula con un código vectorizado que reproduce `Medidor.medir` con la exclusión del pareo igual a
   "píxeles a 15 km o menos del cráter" y mínimo de 20 pares (verificado igual a 1e−9 en 75 píxeles-cuadro).
   Inyectar −a K en la BTD de un píxel de Z baja su M1 en a exacto y no cambia el de los demás (el control está a
   más de 15 km), así que la inyección del poder se hace restando a en D.
2. **Hora.** "±10 min" son los cuadros s − 1, s y s + 1 del mismo día (sin cruzar medianoche); "±60" y "±120 min" de
   U comparan la hora del día en forma circular (sólo importa de noche, en lo informativo).
3. **Nulo del evento.** Pares (x, x + 1) del mismo día placebo, los dos despejados por E1 y evaluados, con los dos
   cuadros entre s1 − w y s2 + w, donde s1 y s2 son los cuadros del evento y w la ventana usada para U (6 o 12
   cuadros; si los dos cuadros del evento usan ventanas distintas, la mayor). Si sólo uno de los dos cuadros del
   evento se puede evaluar, el estadístico del evento es el S de ese cuadro.
4. **Poder.** Por cada cuadro positivo, con su U y el mismo grupo de cuadros placebo que dio ese U: 200 inyecciones
   con semilla 0 (`numpy.random.default_rng(0)`), cuadro al azar **con reposición** (hay menos de 200 cuadros) y
   píxel al azar entre los 65 de Z. Si el píxel sorteado no tiene D en ese cuadro, la inyección se pierde (cuenta
   como no detectada salvo que el mínimo caiga a un píxel de él por azar) y se informa cuántas fueron. Las dos
   firmas (−0,97 y −1,46 K) usan los mismos sorteos. **El veredicto usa el menor poder a −0,97 K de los cuatro
   cuadros positivos** (lo más conservador para declarar NO DETECTA).
5. **Ensayo en seco.** Cuadros del día excluido despejados por E1 y evaluados, dentro de la unión de las ventanas
   de U de los cuatro positivos (se fija con el conteo de placebo, sin leer los positivos); U(h) de cada cuadro con
   los otros 13 días por la misma regla (±60, ±120 o sin nulo). Falsa alarma del día = disparos / cuadros; la media
   es sobre los días con al menos un cuadro. La misma cuenta en todas las horas va como informativo.
6. **Tasa por hora (§7).** Con U sin el propio día (como en el seco), en los cuadros placebo evaluados, despejados y
   en todos.
7. **Pulsos del OVDAS (§7).** Los 14 episodios de `h24_medir.EPISODIOS` con los cuadros de `h24_medir.ventanas()`.
   Mañana: inicio antes de las 15:00 UTC (mediodía en Chile, UTC−3); tarde: desde las 15:00 UTC. U de todos los
   placebo; un cuadro sin U se cuenta aparte.
8. **INVÁLIDA y sin nulo.** Si algún cuadro positivo no tiene U (menos de 20 cuadros a ±120 min), la prueba es NO
   CONCLUYENTE (sin nulo), como dice el §3. Si el seco da falsa alarma media mayor que 0,10, INVÁLIDA, antes que todo.
