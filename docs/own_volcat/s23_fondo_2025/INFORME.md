# S23: el detector de S22b con fondo sin pluma de oct-nov 2025. Informe, 25-11-2026

Criterio S23a `criterio_2026-11-24.md` (commit `1594187`), empujado antes de abrir un solo cuadro de 2025. Código en
`C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\Goes\.claude\worktrees\s23-fondo-2025-68f1e1\docs\own_volcat\s23_fondo_2025\scripts\` (en main desde el merge de S23) (`s23_medir.py`;
con la referencia de S22b reproduce su ensayo en seco exacto, 0,031693). Resultados en `resultados/`. Criterio de la
confirmación S23b `criterio_S23b_2026-11-25.md` (commits `97bdec1` y `af46f12`), escrito antes de tocar días nuevos.

**En una línea: S23a da PARCIAL por su regla (8 de 30 cuadros de VOLCAT, todos del 08-11).** El diagnóstico muestra
que el fondo de 2025 sirve pero que el "nublado de costumbre" no se puede traer de otro año, porque borra la nieve de
2026. Cambiando sólo eso (post hoc) el detector alcanza 25 de 54 cuadros de VOLCAT en 4 de 5 días, casi sin disparar
en los otros cuadros de 2026. Eso es una hipótesis (S23b), con su criterio congelado para confirmarla en días nuevos.

## 1. Para geólogo

**El fenómeno.** Desde julio de 2026 Chillán tiene pluma todos los días (Nicolás, cámaras del OVDAS). S22b armaba su
referencia (lo "normal" de cada píxel y el umbral de alarma) con cuadros de 2026 en que VOLCAT no dibujó nada, pero
esos cuadros tenían pluma. Una referencia con pluma la resta de sí misma y sube el umbral. S23 trae la referencia de
oct-nov 2025, un año tranquilo, con el mismo satélite, la misma grilla y la misma estación.

**Lo que salió.**

- **El fondo de 2025 es limpio y comparable.** La bajada quedó completa (C14 y C15 en 8.911 de 8.928 cuadros, máscara
  de nubes en 8.803; lo que falta no existe en NOAA). Los mapas de noches despejadas de 2025 y 2026 calzan con
  correlación 0,985 (la misma grilla), y los coeficientes de calibración son idénticos.
- **Con la regla escrita, el detector ve muy bien el 08-11 y casi nada más.** El 08-11 marca la pluma hacia el SSE
  (tajada de 150° a 180°) de 17:00 a 20:40 UTC, 16 disparos, y alcanza 8 de los 13 cuadros en que VOLCAT la dibuja
  (S22b: 4 de 13). Pero el 28-10 (26 cuadros de VOLCAT) no se evalúa ni una vez, y el 14-11 (11 evaluados) no
  dispara.
- **Por qué se pierde el 28-10: la nieve, no las nubes.** De día la máscara de NOAA confunde nieve con nube. El
  detector ya lo sabía (S22b): un píxel que la máscara marca "nublado" la mayoría de los cuadros despejados de esa hora
  es nieve "de costumbre" y no se borra. Pero la nieve de 2025 no es la de 2026: con la costumbre de 2025, la tarde
  del 28-10 borra del 29 al 50 % del anillo como "nube nueva" (con la de 2026, del 4 al 47 %), y quedan menos de 9
  tajadas para medir. Así se perdieron 70 de los 100 cuadros de VOLCAT.
- **Con la costumbre de cada año (post hoc), el detector llega mucho más cerca de VOLCAT.** Base y umbral de 2025,
  costumbre de 2026 para mirar 2026: alcanza 25 de 54 cuadros de VOLCAT (28-10 10 de 17, 29-10 3 de 3, 08-11 9 de 13,
  11-11 3 de 3), contra 2,6 esperados por azar. En los cuadros de 2026 sin dibujo de VOLCAT a la misma hora dispara en
  3 de 234. Todos los disparos caen hacia el SE (120° a 180°), donde VOLCAT dibuja la pluma. Sacando cualquier día
  sigue firme. **Pero esta regla la elegí mirando estos mismos días**: no está probada.
- **El 14-11 sigue en cero en todas las versiones.** Ese día VOLCAT pinta la pluma pegada al cráter (0 a 15 km): el
  detector no mira los primeros 4 km y la firma en la tajada queda cerca del umbral sin cruzarlo.
- **Contra lo que esperaba, 2026 dispara MENOS que 2025 de noche** (0,5 % contra 4 % de los cuadros). Si la pluma
  diaria o el depósito de ceniza dieran una firma permanente, debería ser al revés. Sin explicar.

**Lectura honesta.** El fondo limpio ayuda: con la misma regla, el umbral de tarde queda menos exigente que el de S22b
(a las 18 UTC −0,55 K contra −0,69 K) y el 08-11 pasa de 4 a 8 cuadros. Lo que falta es una costumbre del año en
curso, y esa versión hay que confirmarla en días que nadie haya mirado.

## 2. Veredicto por la regla (S23a)

| Prueba | Resultado | Veredicto |
|---|---|---|
| Instrumento I1 a I4 | cobertura L1B 99,8 %, ACMF 98,6 %; 0 scans distintos, 0 congelados; BT11 en rango 100 %; I4 0,985 | pasa |
| Ensayo en seco (2025, cada día sin sí mismo) | media 0,043 por cuadro (53 días, 3.668 cuadros evaluados) | aprobado (≤ 0,05) |
| Poder por inyección (2025) | 0,01 a 0,33 K; 0,585 a 0,97 K (S22b: 0,045 y 0,735) | |
| R contra VOLCAT 2026 | 8 de 30 P evaluados (0,27); esperado por azar 1,51; p25 = 8e-5; episodios 2 de 5 | **PARCIAL** |
| Contra los N de 2026 | 0 de 2 a 23 cuadros N alrededor de cada P alcanzados; pN = 0 (degenerado: azar estimado en 0) | etiqueta **SEPARA VOLCAT** (débil) |

Sin el 08-11: 0 de 17 (p25 = 1). El resultado es un día.

## 3. Diagnóstico y sensibilidad (post hoc, no cambian el veredicto)

- `resultados/diagnostico_posthoc.json`: de los 100 cuadros P, 30 evaluados, 10 fuera por la compuerta de nubes y
  70 por tener menos de 9 tajadas válidas. Fracción del anillo borrada por nube dinámica y su borde en los P del 28-10:
  0,29 a 0,50 con la costumbre de 2025, 0,04 a 0,47 con la de 2026. Píxeles sin línea base de 2025: menos de 0,5 %.
- `resultados/sensibilidad_costumbre_2026.json`: la versión S23b en los mismos días (cifras en §1).
- Umbral por hora, 2025 contra S22b: 03 UTC −0,26 / −0,28; 09 UTC −0,31 / −0,29; 14 UTC −0,48 / −0,55; 16 UTC −0,66 /
  −0,68; 18 UTC −0,55 / −0,69; 20 UTC −0,47 / −0,56; 22 UTC −0,51 / −0,40.

## 4. Lo que sigue: S23b (criterio congelado)

`criterio_S23b_2026-11-25.md`: la versión de §3 con el nublado de costumbre de 2026 guardado en
`D:\goes_notas\s23\s23b\estat_2026.npy` (hash en el criterio) y base y umbral de 2025, medida **una sola vez** cuando
VOLCAT sume 20 cuadros P en 2 días nuevos (desde el 25-11). CONFIRMA si R ≥ 0,40, p25 ≤ 0,01 y pN ≤ 0,05. Script:
`scripts/s23b_confirmar.py` (`contar` sólo clasifica VOLCAT y no gasta la prueba; `bajar` baja GOES; `medir`).
Al 25-11 05:30 UTC: 0 P en el día nuevo.

## 5. Videos (fuera del repo, licencia SSEC)

En `C:\Users\nmend\Downloads\`: `s23a_lado_a_lado_volcat_vs_detector_fondo2025_chillan_<día>_10min.mp4` (regla del
criterio: 08-11, 14-11, 28-10, 11-11, 10-11, 05-11) y `s23b_lado_a_lado_...` (candidata post hoc: 28-10, 29-10, 08-11,
11-11, 14-11, 05-11). Izquierda VOLCAT tal cual; derecha el IR de 11 µm en gris con la cola de la tajada que dispara
en rojo lleno y la nube que el detector no usa en celeste. Para comprobar con las cámaras: la dirección de la pluma del
28-10, 29-10 y 11-11 por la tarde.

## 6. Lo que puede estar mal

- Un año de fondo: si 2025 tuvo una primavera rara, la base no representa a 2026. La correlación de noches (0,985) dice
  que la geometría calza, no que la superficie sea igual.
- El poder a 0,33 K es casi nulo (0,01): el detector sólo ve firmas de casi 1 K. Las plumas chicas que Nicolás ve en
  cámaras y VOLCAT no dibuja quedan fuera.
- Los cuadros seguidos no son independientes; por episodio, S23a alcanza 2 de 5.
- La regla S22b se eligió mirando estos mismos días de 2026; S23 sólo cambia la referencia.
- No dice si lo detectado es ceniza, ni su altura.
