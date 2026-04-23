# Altura de pluma / ceniza desde GOES

Resumen operativo de las formas de medir altitud de columna eruptiva con
GOES-19 ABI, ordenadas de más integrable a menos integrable en nuestro stack
(Streamlit + Python + xarray + S3).

## Resumen ejecutivo

GOES-19 NO publica un producto oficial "Altura de Ceniza" como NetCDF operacional
(el antiguo **ABI-L2-VAAF** existió solo en GOES-16 2019-2020 y fue
discontinuado). Las opciones reales para hoy son:

1. **VOLCAT (CIMSS/SSEC)** — producto operacional de **Ash Cloud Top Height**
   derivado de ABI/VIIRS/MODIS/AHI. Color-codificado. Lo usan todos los VAAC
   del mundo. **Expone un API REST público sin autenticación** (ver
   `VOLCAT_api_reference.md`). **Es la mejor opción para integrar ya.**
2. **ACHA (NOAA ABI-L2-ACHAF)** — Cloud Top Height genérico en NetCDF desde
   S3 `noaa-goes19`. No es específico de ceniza pero detecta la pluma como
   nube. Sirve como respaldo e independiente.
3. **Parallax GOES-East + GOES-West** — triangulación geométrica. Chile queda
   en el overlap de GOES-19 y GOES-18. Es un proyecto de investigación.
4. **BT-matching contra sondeo GFS** — algoritmo "old school" que ya podemos
   implementar con lo que tenemos (banda 13 + perfil GFS que usamos para viento).

## ¿Cuán precisa es la altura?

Tipicamente **±2 km RMSE** para plumas opacas y frías. Se vuelve peor (−2 a
−6 km de sub-estimación) cuando:
- La pluma es **semi-transparente** (ceniza fina, plumas dispersas)
- Hay **nube meteorológica fría encima** que domina la señal IR
- Las partículas son **<10 µm** (la emisividad IR baja)

Por eso VOLCAT reporta además "Ash Probability" y "Effective Radius" — en
conjunto dan una mejor interpretación que la altura sola.

## ¿Qué queremos integrar en el dashboard?

**Plan priorizado:**

1. **[HOY] Sector VOLCAT en vista por volcán**: cuando el usuario elige
   Villarrica/Copahue/Calbuco/Planchón-Peteroa, agregar una pestaña
   "Altura VOLCAT" que traiga el PNG más reciente del API VOLCAT
   (`get_list/json`), lo renderice con su leyenda, y muestre la hora UTC
   del scan. Cadencia típica: cada 5-10 min (ABI) o ~12 h (VIIRS/polar).

2. **[SIGUIENTE] Layer "Altura" en Ash RGB**: overlay semitransparente del
   ACHAF NetCDF de NOAA S3 enmascarado por nuestro BTD de ceniza, con
   colorscale de km.

3. **[FUTURO] BT-matching propio**: calcular altura pixel-a-pixel usando
   banda 13 + GFS. Expose en UI la incertidumbre.

## Referencias

- Pavolonis et al. 2013 — algoritmo VOLCAT: https://doi.org/10.1002/jgrd.50173
- Pavolonis et al. 2018 — deteccion de erupciones por growth rate: https://doi.org/10.1029/2018EA000410
- Sieglaff et al. 2009 — CO2 slicing para altura: https://doi.org/10.1175/2008JAMC1882.1
- Prata 1989 — BTD split-window 11-12 µm: https://www.nature.com/articles/340691a0
- ATBD ACHA (NOAA GOES-R): `../manuales_pdf/ATBD_CloudHeight_ACHA_v3.0_Jul2012.pdf`
- VOLCAT docs: https://cimss.ssec.wisc.edu/volcat/
- VOLCAT imagery viewer: https://volcano.ssec.wisc.edu/
