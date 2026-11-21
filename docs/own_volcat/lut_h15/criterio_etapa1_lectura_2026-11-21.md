# Criterio de la etapa 1 de C3 (H15): lectura de las tablas de probabilidad de VOLCAT para ABI, 21-11-2026

Escrito y subido antes de abrir las tablas en esta sesión. Plan: `docs/own_volcat/PLAN_2026-11-21_LUT_VOLCAT.md`,
camino C3, paso (a). La etapa 1 no decide H15: fija qué se puede usar en las etapas 2 y 3 y con qué grado de
certeza.

## Insumos (sólo lectura)

- `D:\goes_notas\busqueda_2026-11-20\volcat_static_anc\volcat-ancillary\luts\GOESR_ASH_pixel_probability_LUT_Jan11_2017_142740.hdf`
- `D:\goes_notas\busqueda_2026-11-20\volcat_static_anc\volcat-ancillary\luts\GOESR_ASH_object_probability_LUT_Jan11_2017_142742.hdf`
- `D:\goes_notas\busqueda_2026-11-20\volcat_static_anc\volcat-ancillary\config\volcat_ash_detection_GOESR.config`

HDF4, leídas con `pyhdf` desde `D:\goes_notas\busqueda_2026-11-20\venv_hdf4\Scripts\python.exe -I`. No se ejecuta
ningún código del paquete de SSEC. Al repo van la estructura (nombres, formas, atributos) y números derivados, no
las tablas.

## Qué tiene que salir

Para cada clasificador que el `.config` activa (bandera 1), y por superficie (tierra, agua, nieve) y régimen
(día, noche, sólo IR):

1. el conjunto de datos de ceniza y el de nube, con su forma;
2. el significado y los **bordes** de cada eje, leídos de la tabla (atributo del conjunto, conjunto `*_BINS_*` o
   atributo global);
3. si cada densidad está normalizada (suma 1 por clase y por bin de las dimensiones de condición) o no;
4. el prior y cualquier constante que entre a la combinación, si está escrita en la tabla;
5. qué es `NRAT`.

Y para la combinación: qué clasificadores entran de noche, de día y en sólo IR con ABI, y cómo se combinan.

## Cómo se clasifica cada afirmación

- **LEÍDO**: está escrito en la tabla o en el `.config` (atributo, nombre de conjunto, valor).
- **INFERIDO**: sale de una fuente publicada (tesis de Pavolonis 2014, SECO 1 y 2 de 2015, ATBD) o de la forma de
  los arreglos, y no contradice lo leído. Se dice de dónde.
- **SUPUESTO**: no tiene apoyo escrito; se elige para poder seguir y se dice qué lo validaría.

En particular, la regla de combinación (Bayes ingenuo sobre varios clasificadores, como SECO 1) será INFERIDA o
SUPUESTA salvo que la tabla traiga un atributo que la describa: el paquete no trae código. La etapa 2 es la que la
valida.

## Regla de la etapa

- **Lectura suficiente para seguir a la etapa 2** si los clasificadores de **noche** con onda larga (los que se
  pueden comparar contra `ash_probability_IR` de Mauna Loa, que es todo de noche) tienen sus ejes con bordes
  LEÍDOS o INFERIDOS con comprobación de forma, y las densidades de ceniza y nube están identificadas.
- **No suficiente** si algún eje de esos clasificadores queda como SUPUESTO sin comprobación de forma. En ese caso
  la etapa 2 se corre igual, pero cada eje supuesto se prueba en sus variantes razonables y el informe lo dice.
- Se agrega una comprobación de cordura: con la lectura elegida, la razón de densidades ceniza/nube en un estado
  típico de ceniza (εtot 0,3 a 0,6, β(12/11) < 0,9) tiene que ser > 1 y en un estado típico de nube de hielo
  (β(12/11) ≥ 1,05) < 1. Si sale al revés, algún eje está invertido y se informa.

## Entrega

`docs/own_volcat/lut_h15/LECTURA_LUT.md` y la estructura cruda en `docs/own_volcat/lut_h15/resultados/`
(`lut_pixel_estructura.txt`, `lut_objeto_estructura.txt`), script en `docs/own_volcat/lut_h15/scripts/`.
