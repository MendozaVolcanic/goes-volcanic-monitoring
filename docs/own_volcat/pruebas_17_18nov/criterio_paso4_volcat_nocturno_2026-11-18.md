# Criterio declarado ANTES de medir: paso 4 (H1 a, VOLCAT de noche en Chillán), 18-11-2026

Pregunta: ¿VOLCAT dibuja alguna vez un objeto anclado al cráter de Chillán **de noche**? Si lo hace,
los canales solares no son necesarios para que VOLCAT vea estas plumas y H1 cae como explicación
completa.

## Datos

- PNG Ash_Height del sector `Chile_Central_2_km` que SSEC todavía publica y que no se habían revisado:
  25 al 31-10-2026 y 17 y 18-11-2026 (hasta la hora de la consulta). SSEC ya no lista el 01-10 (404).
  Tamaño medido antes de bajar: ~0,49 MB por cuadro según el manifiesto anterior, 144 cuadros por día,
  ~0,6 GB en total. Disco libre al empezar: 20 GB; si baja de 5 GB, se para.
- Decodificación igual que `huellas.py` y que el paso 3 (zona útil sin título, globo ni logos).

## Medición

- Objeto anclado = objeto de 8 vecinos, > 3 px del PNG, no manto (≤ 5 % del mapa), con al menos un
  píxel a ≤ 10 km de Nevados de Chillán (mismo criterio que `toca_crater_10km`).
- Noche = cenit solar en Chillán ≥ 90°. Día = cenit < 80°. Entre medio, crepúsculo (se informa aparte).

## Decisión

- **Falsa H1 como explicación completa** si hay al menos **2 cuadros nocturnos consecutivos** (20 min de
  persistencia) con objeto anclado al cráter, fuera de un día con manto sinóptico (objeto > 5 % del
  mapa en el mismo cuadro).
- Un cuadro nocturno aislado: se informa con su imagen recortada y queda no concluyente.
- Si hay detecciones diurnas en esos días y ninguna nocturna: se suman los episodios nuevos al conteo de
  "sólo de día" y se recalcula la probabilidad de azar (0,6 elevado al número de episodios).
- Si no hay detecciones ni de día ni de noche: no informa sobre H1.
- Episodio = día con al menos un cuadro anclado.

## Enmienda, escrita ANTES de analizar los días nuevos (sólo se había corrido la validación del 01 al 16-11)

La validación del decodificador sobre los días ya conocidos dio 62 cuadros anclados de día fuera del
16-11 (la tabla original dice 58; la diferencia es la máscara de título y logos) y **7 nocturnos el
16-11 entre 08:20 y 09:30 UTC**. Esos 7 son el sistema grande del 16-11: el objeto que toca el cráter
mide de 16.000 a 27.000 px del PNG (2 a 3,6 % del mapa, bajo el umbral de manto del 5 %), y los objetos
chicos de esa madrugada (5 a 26 px) son fragmentos en su borde. La regla de manto no lo atrapa.

Regla corregida, que vale para los días nuevos:
- Sólo cuenta un objeto anclado **de 4 a 500 px** (el mayor de los objetos de Chillán del 07 al 14-11
  midió 49 px; 500 es diez veces eso).
- Y sólo en un cuadro **sin ningún objeto de más de 500 px a menos de 50 km del cráter** (si lo hay,
  los objetos chicos pueden ser fragmentos de un sistema grande).
- Los cuadros con un sistema grande cerca se informan aparte, sin contar para la decisión.

Con esta regla, la validación del 01 al 16-11 tiene que dar 0 nocturnos; se comprueba antes de mirar
los días nuevos.
