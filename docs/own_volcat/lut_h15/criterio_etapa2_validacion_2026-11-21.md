# Criterio de la etapa 2 de C3 (H15): ¿nuestra lectura de las tablas reproduce la probabilidad de VOLCAT?, 21-11-2026

Escrito y subido antes de calcular ninguna probabilidad y antes de leer `ash_probability_IR`. Lo único hecho antes:
la lectura de las tablas (`LECTURA_LUT.md`, commit 734ac40) y la lista de variables del caso de Mauna Loa que ya
estaba en `docs/own_volcat/mauna_loa_c2b/resultados/c2b_estructura_hdf.txt`.

## Por qué esta etapa decide si se sigue

En Chillán no hay verdad de la probabilidad de píxel: VOLCAT no la publica. Si nuestra lectura de las tablas está
mal (un eje corrido, la combinación equivocada), un "sí" o un "no" en Chillán no significa nada. El caso de prueba de
Mauna Loa (`D:\goes_cache\volcat_test_mauna_loa\`, GOES-17, 28-11-2022, 10 cuadros de 09:16 a 10:01 UTC, todo de
noche) trae la probabilidad de ceniza por píxel que calculó VOLCAT (`geocatL2`,
`vcat_ashdet_pix_2_7_10_11_13_14_15_ash_probability_IR`, ~100 mil píxeles válidos por cuadro) y las entradas
intermedias del mismo píxel. Es la verdad contra la que se valida.

## Dos niveles

- **Nivel A, la lectura sola.** Entradas de VOLCAT mismo (`geocatDIAGS1`): εtot(11)
  (`cloud_emissivity_ch14_tot`), β(12/11) total, opaco, multicapa bajo y medio, β(7,3/11) total, β(8,5/11) total y
  opaco; BTD(11 − 12) de las BT de `geocatL1`; BT11 de cielo despejado de `geocatRTM`; superficie de
  `pixel_surface_type` (0 = agua, el resto tierra: SUPUESTO, se informa la fracción de tierra y que calce con las
  islas). Aísla la lectura de las tablas y la regla de combinación.
- **Nivel B, nuestro cálculo de ε y β con SU cielo despejado.** εtot y β total de 12/11 y 7,3/11 los calculamos
  nosotros, con las radiancias observadas de `geocatL1`, la radiancia de cielo despejado de `geocatRTM` (BT pasada a
  radiancia con los coeficientes de Planck del propio archivo) y una nube negra en la tropopausa, `B(T_tropo)`, con
  la temperatura de tropopausa del GFS del paquete (`ancillary\gfs_hdf`, celda que indica `nwp_x_index` y
  `nwp_y_index`, interpolada en el tiempo entre los dos archivos). Fórmulas de SECO 1 (ec. 1 y 2, las mismas de
  `reproducir_volcat/scripts/h11_analisis.py`): `ε = (R_obs − R_clr)/(R_cld − R_clr)`,
  `β = ln(1 − ε_a)/ln(1 − ε_11)`. β opaco y los β multicapa se toman de VOLCAT (no tenemos su nivel de nube baja);
  se declara. Si el GFS del paquete no trae temperatura de tropopausa, se calcula del perfil (primer mínimo de
  temperatura sobre 500 hPa con gradiente < 2 K/km, regla de la OMM simplificada) y se dice.

## Variantes (lo que la lectura dejó como SUPUESTO)

1. **Combinación** (Bayes ingenuo, prior 0,001 leído): (J) densidades conjuntas tal cual; (C1) cada densidad
   dividida por su marginal de εtot y el factor de εtot multiplicado una vez; (C0) condicional sin factor de εtot.
2. **β o BTD fuera del eje o inválido:** (a) al primer bin; (b) recortado al bin extremo; (c) se omite ese
   clasificador.
3. **Conjunto de tablas:** (S1) sólo IR sin 8,5 µm, como manda el `.config` de 2025 (6 tablas: εtot × β(12/11)
   total, opaco, multi bajo, multi medio; εtot × BTD × BT11 despejado; β(12/11) × β(7,3/11)); (S2) S1 más las dos IR
   con β(8,5/11) (el paquete de Mauna Loa es VOLCAT v3.9.16 y no trae su `.config`); (S3) las tablas de noche con
   εp(3,9) (por si `_IR` no fuera lo que el nombre dice), con εp(3,9) = R_obs(3,9)/R_clr(3,9).

27 variantes. Para no elegir con los mismos datos con que se valida: **la variante se elige con los cuadros 1 a 5
(09:16 a 09:36) y se valida con los cuadros 6 a 10 (09:41 a 10:01)**. Elección: la que da la mayor fracción de
píxeles con |P_nuestra − P_VOLCAT| ≤ 0,05 en los cuadros 1 a 5, en el nivel A. El nivel B usa la misma variante.

## Píxeles

Todos los píxeles de los 10 cuadros con `ash_probability_IR` válida (no relleno) y entradas válidas en el nivel
que se mide. Se informan aparte los píxeles con P_VOLCAT ≥ 0,5, que son pocos y son los que importan.

## Regla (en los cuadros 6 a 10)

Un nivel **reproduce** si cumple las tres:

1. ≥ 90 % de los píxeles con |P_nuestra − P_VOLCAT| ≤ 0,05;
2. a umbral 0,5, κ de Cohen ≥ 0,90 entre la clase nuestra y la de VOLCAT;
3. de los píxeles con P_VOLCAT ≥ 0,5, ≥ 90 % también ≥ 0,5 en la nuestra.

**La etapa 2 se aprueba sólo si reproducen A y B.** Si A reproduce y B no, la lectura está bien y el problema es
nuestro ε o β: no se sigue a Chillán (que usa nuestro ε y β) y se documenta dónde difieren ε y β de los de VOLCAT
(mediana y p95 de la diferencia). Si A no reproduce con ninguna variante, se informa la mejor y el diagnóstico
(¿en qué estados se separan?, ¿hay un factor constante en la razón?) y **se detiene**, como pide el encargo.

## Lo que se informa además (no decide)

- Las 27 variantes en los cuadros 1 a 5 y la elegida en los cuadros 6 a 10, con las tres métricas y la correlación
  de rangos.
- Diferencia de εtot y β total nuestros contra los de VOLCAT (nivel B).
- Mapa de diferencias de un cuadro (PNG en `resultados/`, sin datos crudos de SSEC).

## Lo que no se hace

No se ejecuta código del paquete de SSEC. Al repo van números derivados, scripts y figuras; nada de las tablas ni de
los HDF. Sin VIIRS.
