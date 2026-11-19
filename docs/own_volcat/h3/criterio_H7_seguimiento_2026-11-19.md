# Criterio declarado ANTES de medir: H7 (VOLCAT sigue la nube entre cuadros), 19-11-2026

Escrito antes de calcular cualquier número de H7. Aprobado por Nicolás (vía la sesión que lanzó esta).

## Pregunta

El ATBD VOLCAT v1.0 (Pavolonis et al., enero 2025, §2.2) describe dos detectores (el multiespectral
de SECO 2015 y uno de anomalía de crecimiento de nube, Pavolonis 2018), dice que la actividad térmica
en el cráter influye en la detección y que un seguidor ("multi-spectral kd-tree") lleva la nube de un
cuadro al siguiente "from emission to dissipation". H7: los cuadros VOLCAT de Chillán sin señal IR
propia no son detecciones nuevas, sino la continuación de un objeto detectado antes con señal.

## Episodios

- E1: 28-10 desde 21:50 UTC hasta 29-10 01:40 UTC.
- E2: 10-11, cuadros con objeto anclado (`toca_crater_10km == 1` en `cuadros_10min.csv`).
- E3: 14-11, ídem (16:40 a 22:40 UTC).

Cuadro con objeto = hay un objeto VOLCAT (decodificación de `huellas.py` / `pruebaA_28oct.py`, no
manto, > 3 px) a ≤ 50 km del cráter. Anclado = con un píxel a ≤ 10 km del cráter.

**Primer cuadro de un tramo**: cuadro anclado cuyo cuadro anterior publicado (10 min antes; si ese no
se publicó, 20 min antes) no tiene objeto a ≤ 50 km del cráter. Los demás cuadros anclados del tramo
son "continuación". Un episodio puede tener varios tramos.

## Señal propia de un cuadro (con nuestros datos del mismo scan ABI)

- (a) Split-window: al menos 1 píxel de la huella (dilatada 1 px) con BTD 11,2 − 12,3 µm < −1 K.
- (b) Calor: hot spot FDCF a ≤ 10 km del cráter en ese scan o en los dos anteriores (20 min).
- (c) Crecimiento: al menos 2 píxeles a ≤ 10 km del cráter con BT11 al menos 2 K más fría que en el
  scan de 10 min antes (enfriamiento rápido, indicio de columna que sube).

El β anómalo no entra: no hay un umbral publicado para β (las anclas de Pavolonis 2010 son valores
representativos, no cortes) y sería inventarlo. Si H3 encuentra una separación en β, se informa aparte.

**Línea base**: misma señal en los scans del mismo día sin objeto VOLCAT a ≤ 50 km. Si (b) aparece en
≥ 80 % de esos scans sin objeto, el hot spot se declara no discriminante y el veredicto usa sólo (a) y (c).

## Decisión

- **H7 se sostiene** si en al menos 2 de los 3 episodios el primer cuadro del primer tramo tiene señal
  propia, y al menos el 70 % de los cuadros anclados SIN señal son continuación (tienen antecesor).
- **H7 se falsa** si en al menos 2 de los 3 episodios el primer cuadro del primer tramo NO tiene señal,
  o si más del 30 % de los cuadros anclados sin señal son primeros de tramo (objeto nuevo sin antecesor).
- **No concluyente** en cualquier otro caso, o si menos de 5 cuadros anclados quedan sin señal en total.

Se informa por episodio: lista de tramos, cuadro por cuadro con (a), (b), (c) y si tiene antecesor.

No cambia código de la app. Sin VIIRS.
