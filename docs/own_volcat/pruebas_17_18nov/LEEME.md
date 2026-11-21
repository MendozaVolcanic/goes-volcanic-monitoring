# Pruebas del 17 y 18-11-2026 (POR_QUE §3 y §3.1): código y criterios, INSUMOS PERDIDOS

**Por qué está esta carpeta.** Estas pruebas (paralaje y 8,5 µm, canales solares, objetos lejos de volcanes,
VOLCAT nocturno, paralaje del 28-10) se hicieron con scripts que nunca entraron al repo: vivían en la carpeta de
notas de la sesión de rescate (`local_f3a7d295`), que se puede borrar sin aviso. Se copiaron aquí el 21-11 para
que el código y los criterios no se pierdan. Los resultados y su lectura están en
`docs/own_volcat/POR_QUE_VOLCAT_VE_Y_NOSOTROS_NO.md` §3 y §3.1.

**No corren tal cual: los insumos están perdidos.** Los scripts leen tres scratchpads de `AppData\Local\Temp`
que ya no existen:

- caché del detector del 17-11 (`...\d6ea8719dcf88502\...\scratchpad\det`: ventana 83 × 94 con C11, C14, C15,
  `window.json`, `latlon.npz`, `planck.json`);
- PNG VOLCAT de Chillán cada 10 min (`...\58c6c65788fdfd96\...\volcat_chillan_10min\png` y
  `frecuencia_pixel_clasificado.npy`);
- PNG VOLCAT extra (`...\3960f3d64983ed82\...\volcat_extra\png`).

Además, uno apunta como `REPO` a un worktree borrado (`investigacion-volcat-deteccion-f4df71`). Se dejaron sin
tocar para que sean el registro fiel de lo que se corrió.

**Qué se podría rehacer.** Las escenas L1b de GOES-19 de oct-nov siguen en S3 de NOAA y la ventana se reconstruye
con `docs/own_volcat/reproducir_volcat/scripts/ventana.py` (y0 = 4497, x0 = 2820). Los PNG VOLCAT de oct-nov no:
SSEC no los guarda; sólo hay los que quedaron en `data\raw\volcat_validacion\` (carpeta principal) y en
`D:\goes_notas\local_f3a7d295\cache_rescatada\`.

| Archivo | Qué es |
|---|---|
| `criterio_corrimiento_y_8p5_2026-11-17.md`, `scripts/prueba_AB.py` | pruebas A (paralaje) y B (8,5 µm); su salida está en POR_QUE §3 |
| `criterio_paso2_canales_solares_2026-11-18.md`, `scripts/fetch_solar.py`, `scripts/paso2_analisis.py`, `resultados/paso2_resultado.txt` | paso 2, canales solares (H1 b) |
| `criterio_paso3_objetos_lejos_2026-11-18.md`, `scripts/paso3_objetos.py`, `scripts/paso3_analisis.py`, `resultados/paso3_resultado.txt` | paso 3, objetos lejos de volcanes (H2) |
| `criterio_paso4_volcat_nocturno_2026-11-18.md`, `scripts/paso4_bajar.py`, `scripts/paso4_analisis.py`, `resultados/paso4_resultado.txt`, `paso4_validacion.txt`, `paso4_mosaico_28-29oct.png` | paso 4, VOLCAT de noche (H1 a) |
| `criterio_pruebaA_28oct_2026-11-18.md`, `scripts/pruebaA_28oct.py`, `resultados/pruebaA_28oct_resultado.txt` | prueba A repetida sobre el 28-10 (H4) |

**Copia completa** (con el resto de las notas de esa sesión): `D:\goes_notas\local_f3a7d295\`. Original en
`C:\Users\nmend\AppData\Local\Claude-Data\claude_pzs8sxrjxfjjc\side-session-notes\local_f3a7d295-ddde-4b7c-b258-25e760c44266\`.
