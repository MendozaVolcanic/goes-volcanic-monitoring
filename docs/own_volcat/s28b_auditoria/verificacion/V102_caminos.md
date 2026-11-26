# V102: caminos por los que el hallazgo 102 podría estar mal

Escrito ANTES de abrir `criterio_2026-11-25.md`, `s24_medir.py`, `s24_resultado.json`, `INFORME.md` y `STATUS.md`.
Lo único que conozco del hallazgo es su título y el lugar.

Afirmación a verificar: "La regla B1 de S24 compara las noches de 2025 sin sus noches de 3 o más disparos contra las
noches de 2026 enteras: la selección se aplica a un solo año. Con la misma selección en los dos años, B1 pasa de
NO EPISÓDICO a EPISÓDICO, y cae el titular de que la noche de 2026 dispara unas 10 veces más que una noche común de 2025."

## A. La regla no dice lo que el hallazgo dice que dice

1. B1 puede no comparar tasas entre años. Puede ser una regla sobre la CONCENTRACIÓN de los disparos de 2025 (qué
   fracción cae en pocas noches) y el rótulo EPISÓDICO / NO EPISÓDICO puede describir sólo a 2025. En ese caso "aplicar
   la selección a 2026" no es una corrección sino otra pregunta.
2. El umbral "3 o más disparos" puede no ser de B1 sino de otra regla (B2, B3) o de una descripción del informe. El
   hallazgo puede estar mezclando dos reglas.
3. La asimetría puede ser el DISEÑO declarado: "noche común de 2025" = 2025 sin sus episodios, como línea de base, y la
   pregunta escrita es justamente si 2026 entero supera a esa base. Si el criterio lo escribe con su razón física
   (por ejemplo: las noches episódicas de 2025 son capa baja meteorológica identificada con otro dato), la asimetría
   no es un defecto de pre-registro sino una definición. Hay que ver si la razón está escrita ANTES del dato.
4. La selección podría estar aplicada a los dos años en el criterio y el hallazgo leyó mal una frase.

## B. La implementación no coincide con la regla escrita

5. El criterio puede ser simétrico (o ambiguo) y la asimetría nacer sólo en `s24_medir.py`. O al revés: el criterio
   asimétrico y el código simétrico. El hallazgo dice "la regla", hay que separar texto de código.
6. El código puede calcular las dos versiones y el informe elegir una. O calcular la simétrica en otra función que el
   hallazgo no vio.
7. La unidad puede ser distinta de la que supongo: "disparos" puede ser cuadros, píxeles-cuadro o noches; "3 o más"
   puede contar cuadros por noche o píxeles por cuadro. Una selección simétrica con la unidad equivocada da otro número.
8. El caller puede transformar el argumento: filtro por horas de noche, por nubosidad (ACM), por cobertura mínima de
   cuadros por noche, por lista de días. La selección simétrica tiene que pasar por los mismos filtros.

## C. El recálculo simétrico no da lo que el hallazgo dice

9. Con la selección simétrica (quitar de 2026 sus noches de 3 o más disparos), el cociente puede seguir sobre el
   umbral de B1: entonces el rótulo no cambia y el hallazgo es REFUTADO en su consecuencia.
10. "La misma selección" admite más de una lectura y pueden dar rótulos distintos:
    (a) quitar noches de 3 o más disparos en los dos años;
    (b) no quitar nada en ninguno (2025 entero contra 2026 entero);
    (c) quitar el mismo percentil de noches en cada año.
    Si el rótulo cambia sólo bajo una lectura, el hallazgo es CONFIRMADO EN PARTE.
11. Si 2026 tiene pocas noches y casi todas tienen 3 o más disparos, la selección simétrica deja 2026 vacío o con un
    puñado de noches: el resultado sería SIN DATO o inestable, no "EPISÓDICO". Hay que mirar los n.
12. El rótulo puede depender de otra cifra además del cociente (un mínimo de noches, un intervalo, una segunda
    condición). Cambiar el cociente no basta para cambiar el rótulo.
13. El hallazgo puede haber tomado "EPISÓDICO" y "NO EPISÓDICO" al revés respecto de lo que el criterio define.

## D. El dato de hoy no es el dato del informe

14. El JSON de resultados puede no ser el que produce el script de hoy (script cambiado después, caché regenerado,
    S25b agregó 2024 al mismo directorio). Hay que re-correr y comparar con el JSON commiteado.
15. Los cachés de `D:\goes_notas\s22` y `D:\goes_notas\s23` pueden haber cambiado (más días de 2026 agregados después
    del 24-11). Mi recálculo tiene que cortar en el 24-11-2026 y comprobar que el script original también lo hacía.
16. El worktree puede estar atrasado respecto de `main`: verificar que los archivos de S24 son los del PR fusionado.
17. La lista de noches de 2026 puede incluir días que el criterio excluye (14-11 marcada INVÁLIDA, días con VOLCAT,
    días placebo), y la cifra "10 veces" depender de cuáles entran.

## E. El titular no depende de B1

18. El "unas 10 veces más" puede salir de otra cuenta (tasa por cuadro de noche, no B1), y entonces aunque B1 cambie
    de rótulo el titular no cae, o cae por otra razón.
19. El INFORME puede ya declarar la asimetría como límite y dar la cifra simétrica al lado. Entonces no hay nada
    oculto y la gravedad baja.
20. STATUS.md puede citar la cifra con otra redacción ("frente a la noche común") que sigue siendo cierta en su
    literalidad aunque la comparación sea asimétrica. Cierto en la letra y engañoso en la lectura son cosas distintas
    y hay que decir cuál.
21. Sesiones posteriores (S25a, S26b, S27a) pueden haber remedido la noche de 2026 con otro método; si lo hicieron,
    la consecuencia práctica del defecto de B1 es menor aunque el defecto exista.

## F. Trampas mías

22. Puedo confirmar por construcción si elijo yo el umbral simétrico después de ver el dato. Regla: uso el umbral
    que está escrito en el criterio (el "3 o más" si es ese) y reporto todas las lecturas de 10, no la que confirma.
23. Puedo contaminar una confirmación congelada si mi recálculo abre días posteriores al 24-11-2026. Regla: filtro
    explícito por fecha y compruebo en la salida la fecha máxima usada.
24. La vara del plan (§3 de PLAN.md) define qué es "cambia un veredicto". Tengo que aplicar esa vara y no la mía.
