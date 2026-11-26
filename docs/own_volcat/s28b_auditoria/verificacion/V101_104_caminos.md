# V101 y V104: caminos de ruptura, escritos antes de abrir los archivos de S28a

Escrito por el verificador antes de leer `docs/own_volcat/s28a_vecinas/` y el bloque `## 0-prev27.` de
`STATUS.md`. Sólo conozco el título de cada hallazgo y el lugar. Cada camino es una forma en que la
afirmación del hallazgo podría estar mal.

## Hallazgo 101 (rótulo de día MIXTO leído como otro rótulo y marcado CONFIRMADO)

C101-1. La regla no da MIXTO. El criterio puede tener umbrales que, aplicados a las cifras del JSON, den
        otro rótulo (el que el INFORME dice). Comprobar recalculando el rótulo desde `s28a_resultado.json`
        con la regla escrita, sin fiarme del campo "veredicto" del JSON.
C101-2. El script aplica una regla distinta a la del criterio. El rótulo del JSON saldría de un código que
        no coincide con el texto pre-registrado, y entonces el defecto sería otro (script contra criterio).
C101-3. El criterio define MIXTO con una lectura permitida. Si el propio criterio dice que MIXTO se
        interpreta como "el exceso diurno no se sostiene como pluma", el INFORME no promete más.
C101-4. El INFORME y STATUS sí dicen MIXTO y sólo agregan una lectura rotulada como interpretación o post
        hoc. En ese caso el hallazgo exagera: habría que ver la frase exacta y su rótulo.
C101-5. El CONFIRMADO de STATUS califica otra frase (por ejemplo la cifra de la noche o un hecho medido) y
        no la lectura del día. Leer el alcance gramatical del CONFIRMADO.
C101-6. Hay más de un rótulo de día (por cumbre, por año, por tramo horario) y el hallazgo mezcla dos.
        MIXTO podría ser el de una cumbre y el otro rótulo el del conjunto.
C101-7. El criterio cambió después del dato. Si el archivo del criterio se editó después de medir, la
        "regla escrita" que uso no es la pre-registrada. Comprobar con `git log` del criterio y de los JSON.
C101-8. La copia que leo está atrasada o el bloque de STATUS fue corregido después. Comprobar contra HEAD y
        contra `origin/main` si está disponible sin bajar nada.
C101-9. El rótulo reservado "para otro caso" y MIXTO llevan a la misma decisión práctica. Entonces el
        defecto sería de lectura y no cambia un veredicto. Medir contra la vara de PLAN.md §3.
C101-10. La memoria del proyecto o el INFORME ya declaran el límite (que MIXTO no decide) en otro párrafo,
        y el hallazgo cita una frase fuera de contexto.

## Hallazgo 104 (el 10-11 las vecinas no disparan a la hora de los aciertos de Chillán)

C104-1. Zona horaria. Las horas del JSON pueden estar en UTC y la frase "de tarde" en hora de Chile
        (UTC-3 en noviembre). Un desfase de 3 h puede crear o borrar la coincidencia. Fijar la convención
        leyendo el código, no suponerla.
C104-2. La frase no afirma simultaneidad. "Disparan de tarde las tres cumbres" puede ser cierta como tramo
        del día aunque no coincidan cuadro a cuadro. Hay que separar dos afirmaciones: mismo tramo, misma
        hora.
C104-3. Definición de "tarde". El criterio o el script pueden definir tramos (mañana, tarde, noche) con
        cortes propios. Usar esos cortes y no los míos.
C104-4. El JSON del post hoc no guarda horas por cuadro, sólo conteos por día o por tramo. Entonces el
        hallazgo sólo se puede comprobar recalculando con el código de S28a sobre el caché, o queda SIN DATO.
C104-5. Los cuadros P de Chillán que usa el hallazgo no son los que usa el post hoc (otra lista de VOLCAT,
        otro día, otra definición de acierto). Identificar de dónde salen los P del 10-11.
C104-6. Disparo de cumbre contra disparo de píxel. Una cumbre puede "disparar" con cualquier píxel de su
        zona o con una regla combinada (S26a). Usar la misma definición que el script.
C104-7. Cuadros sin dato. Si a la hora de los aciertos de Chillán las vecinas no tienen cuadro válido
        (nube, hueco del caché), "no disparan" sería "no se pudo medir", que es otra cosa.
C104-8. El 10-11 puede no ser el día de la frase. STATUS podría hablar de otro día (08-11, 14-11) y el
        hallazgo confundir la fecha, o fecha UTC contra fecha local cerca de medianoche.
C104-9. Una de las dos vecinas sí coincide y la otra no. Entonces "las tres" es falso pero "dos de tres"
        se sostiene: sería CONFIRMADO EN PARTE.
C104-10. La SOSPECHA de STATUS y la decisión propuesta pueden apoyarse en otra evidencia además de esa
        frase. Si es así, quitar la frase no las tumba. Leer qué sostiene a qué.
C104-11. El caché que leo no es el que produjo el JSON (se regeneró). Comparar mi recuento con el JSON.
C104-12. Tolerancia de emparejamiento. "A la misma hora" depende de la ventana (mismo cuadro de 10 min,
        30 min, 1 h). Reportar el resultado para varias ventanas, no para una elegida después.

## Qué cuenta como resultado

Para cada camino: evidencia archivo:línea o salida de comando de esta sesión, y si el camino rompe o no la
afirmación. No abro cuadros GOES posteriores al 24-11-2026 ni corro el detector en días nuevos.
