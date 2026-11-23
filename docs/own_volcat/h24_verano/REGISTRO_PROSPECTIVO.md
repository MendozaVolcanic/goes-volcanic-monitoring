# H24 en verano: registro prospectivo, 23-11-2026 (S19)

Escrito **antes** de que existan los datos: los REAV de diciembre de 2026 a febrero de 2027 todavía no se publican.
Sirve para que la prueba de verano no se pueda ajustar mirando los resultados.

## Por qué

H24 (`../h24_pulsos_reav/INFORME.md`) dejó sin responder la única pregunta que importa para "ver lo que vio VOLCAT":
si los pulsos **de tarde** que VOLCAT marcó (E10 a E13, del 28-10 y del 10-11) tienen firma en 11 y 12 µm. No se
pudieron medir porque entre el 21-09 y el 21-11 casi no hubo tardes despejadas sin actividad para armar el fondo
(15 a 19 % de los cuadros de 14 a 23 UTC despejados; 0 a 3 días útiles por episodio). El verano en la cordillera
del Biobío trae más tardes despejadas. La misma prueba, sin cambios, sobre los pulsos de tarde del verano, lo decide.

## Qué se corre (sin cambiar nada)

- **Criterio:** `../h24_pulsos_reav/criterio_2026-11-22.md`, commit `f2094f7`, con la enmienda 1 (`620b5a0`: excluir
  también los días con objetos VOLCAT del catálogo por cuadro). Mismo estadístico, misma regla (z ≤ −2), mismo
  nulo de ±21 días, mismo poder, mismas cumbres de control, mismo umbral de falsas alarmas (10 %).
- **Motor:** `../h24_pulsos_reav/scripts/h24_medir.py`. Sólo cambian los datos de entrada: la lista `EPISODIOS`, la
  ventana de días (`T0`, `NDIAS`) y la lista `EXCLUIDOS`, armadas con las reglas de abajo.
- **Episodios:** todo pulso de Nevados de Chillán con hora y altura en un REAV del 01-12-2026 al 28-02-2027. Dirección:
  la del REAV; si el REAV no la da, la del GFS de la capa de la columna (método de H10,
  `../direccion_pluma/scripts/fetch_gfs_viento_h10.py`). Ventana de cada episodio: regla de H24 §4.
- **Días excluidos:** días con REAV, días con marca VOLCAT y días con objetos VOLCAT en el catálogo por cuadro (que
  hay que regenerar para el verano con el método de H9, `../calor_rayos/`).
- **Decide:** el grupo de pulsos altos (≥ 1.800 m) con el veredicto global de H24 §8. **Lectura principal anotada
  ahora:** los pulsos altos de tarde (14 a 23 UTC) que VOLCAT marque en ≥ 50 % de los cuadros de su ventana. Si hay
  al menos 3 decidibles, eso responde la pregunta de la tarde.

## Secundarias anotadas ahora (no deciden)

1. **La lección de H25:** cuando la dirección del REAV y la del GFS difieren más de 45°, repetir el episodio con la
   otra dirección y con la referencia R sin los píxeles a ≤ 30° de la primera (método de `../h25_e6_gfs/`).
2. Fracción de tardes despejadas por mes, para saber si el verano resolvió el hueco de fondo.

## Cuándo y con qué

- **Cuándo:** primera corrida con diciembre y enero al cierre de enero de 2027; corrida final al cierre de febrero.
  La corrida de enero sólo informa; decide la de febrero.
- **Datos:** L1b C14 y C15 de la ventana de 83 × 94 píxeles, ACMF y GFS de diciembre a febrero (unos 3 a 5 GB por
  mes, como H23), a `D:\goes_notas\verano_2027\`. Revisar el espacio de D: antes de bajar (al 23-11 quedaban ~15 GB).
- **REAV:** los publica SERNAGEOMIN. Si no están en línea, Nicolás decide si se piden al OVDAS.
- Nada de esto toca `src/` ni el dashboard. Ningún archivo de SSEC entra al repo.
