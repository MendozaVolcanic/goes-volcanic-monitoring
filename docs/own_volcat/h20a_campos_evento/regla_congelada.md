# H20a (S17): reglas congeladas con el bloque de elección, antes de abrir la validación

Fecha: 22-11-2026. Criterio previo: `criterio_2026-11-22.md`, commit cb03f34.

Bloque de elección: evento `VCB` de Fuego, 13 cuadros de 17:16 a 20:16 UTC, 11.220 píxeles de huella.
Salidas: `resultados/alineacion.csv`, `resultados/eleccion_medir.json`, `resultados/eleccion_explora.txt`.
La validación (Fuego 20:31 a 23:31 y San Cristóbal 23:31) no se ha abierto: los scripts se niegan a
leerla mientras este archivo no exista.

## Lo que dio la elección

Alineación: los 26 recortes de evento de Fuego, el de San Cristóbal y los 40 archivos de gránulo calzan
con la grilla del L2 con diferencia de latitud y longitud igual a 0. Control positivo: la temperatura de
brillo de 11 µm del evento coincide con la del canal 14 del L1 en 100 % de los píxeles (n mínimo 41.412);
corrida un píxel, coincide en 1,6 % o menos.

| Campo del evento | Candidato | n | Acuerdo a 0,01 | Nulo corrido (máx.) | Nulo cuadro previo | Soporte (Jaccard) |
|---|---|---|---|---|---|---|
| S | P | 11.194 | 100 % (diferencia máxima 0) | 88,8 % | 70,9 % | 1,000 |
| S | P_sub | 11.194 | 94,9 % | 88,8 % | 73,8 % | 1,000 |
| S | P_IR | 11.162 | 60,0 % | 60,1 % | 59,1 % | 0,022 |
| SL | P_IR | 11.162 | 100 % (diferencia máxima 0) | 99,3 % | 98,7 % | 0,022 |
| SL | P_SWIR | 11.162 | 99,4 % | 99,4 % | 99,4 % | 0,022 |
| SL | P | 11.162 | 60,0 % | 58,2 % | 56,2 % | 0,997 |

Píxeles discordantes (donde dos candidatos difieren en más de 0,05):

- S entre P y P_sub: 513 píxeles; S coincide con P en 513 y con P_sub en 0.
- SL entre P_IR y P_SWIR: 58 píxeles; SL coincide con P_IR en 58 y con P_SWIR en 0.
- SL entre P_IR y P: 4.455 píxeles; con P_IR en 4.455 y con P en 0.

## Reglas que se validan (sin cambios posibles después de este commit)

- **R1. S es la probabilidad de ceniza publicada, P.** Cumple los puntos 1 a 4 del criterio en elección.
  Los candidatos "1 menos P" quedan descartados (acuerdo 0 %).
- **R2. SL es la probabilidad de píxel infrarroja, P_IR.** Cumple el punto 1 (100 %) y el 4 (58
  discordantes contra P_SWIR). **No cumple el 3**: el nulo también pasa, porque en la columna espesa P_IR
  vale casi 0 en todas partes (sólo 64 píxeles sobre 0,01). **No cumple el 2 tal como lo escribí**: P_IR
  tiene valor en toda la grilla y SL sólo en la huella, así que el Jaccard de soportes no puede llegar a
  0,99 aunque la identidad sea exacta. Por el criterio, en elección R2 queda "no discrimina". En
  validación se mide igual, y se agrega la medida de la sección "post hoc" de abajo.
- **R3. La huella del evento es el grupo de alerta.** En el evento `VCB` de Fuego, `event_idx` mayor o
  igual a 0 es exactamente el grupo de nube convectiva (`Ice_Group_Id_2d` mayor que 0; Jaccard 1,000 en los
  13 cuadros). Es una identidad por construcción. Predicción para San Cristóbal (`ASHPLUMEPUFF`): la
  huella es el grupo de ceniza (`Ash_Group_Id_2d`) de ese objeto.
- **R4. `residence_time`** toma valores múltiplos del intervalo entre imágenes (0,25 h en Fuego), nunca
  supera la edad del rasgo (`feature_age`), y su máximo en cada cuadro es la edad del rasgo. En elección:
  100 % de los píxeles con tiempo menor o igual a la edad, 97,6 % con tiempo igual a la edad, 13 de 13
  cuadros con máximo igual a la edad. Se valida con esos tres números (umbral: 99 % o más con tiempo menor
  o igual a la edad, y máximo igual a la edad en todos los cuadros con edad mayor que 0).
- **R5. `distance_traveled`** es la distancia al volcán con posición corregida por paralaje en los
  píxeles con `residence_time` igual a 0 (elección: 39 de 39 a menos del mayor entre 1 km y 2 %), y es
  mayor o igual que esa distancia en los demás (elección: 100 % de 11.181). Los candidatos D1 (posición
  nominal) y D3 (`displacement_distance`) quedan descartados (0,3 % y 0,0 %). No se identificó la fórmula
  de acumulación para tiempo mayor que 0: queda SIN DATO.
- **R6. El salto de log-odds (C11).** En elección el salto del L2 entre P y P_sub vale 0,11 en los 805
  píxeles donde P supera a P_sub; los valores de H19 (12,74 y siguientes) son de la fase tardía, que está
  en validación. El archivo de evento no trae P_sub. Si R1 y R2 valen, logit(S) menos logit(SL) es
  logit(P) menos logit(P_IR), y sólo equivale al salto de H19 donde P_sub es igual a P_IR en log-odds.
  Prueba congelada para validación: en los píxeles con salto del L2 mayor que 5, contar en cuántos el
  salto del evento queda a menos de 0,05 del salto del L2. C11 se da por cumplida con 99 % o más y 30
  píxeles o más.
- **R7. Controles adicionales.** `ash_mass_loading` del evento es igual al del L2 (100 %, nulo 1,3 %).
  `ash_cloud_height` del evento es la altura del L2 **truncada** a 0,01 km: la diferencia cae entre
  menos 0,01 y 0 en 100 % de los píxeles. El criterio usaba una tolerancia de 0,0051 (redondeo) y por eso
  ese control dio 48 %: era un error de mi tolerancia, no de la lectura. `effective_radius_of_ash` no
  coincide con `ash_effective_radius` del L2 (8 %) y no se investigó.

## Post hoc (decidido después de ver la elección, antes de abrir la validación)

1. **Nulo informativo.** El nulo del criterio no sirve donde el campo es casi constante. Se agrega: en
   los píxeles donde el candidato cambia más de 0,05 respecto del cuadro anterior, medir el acuerdo del
   campo del evento con el candidato actual y con el del cuadro anterior. En elección: S, 2.333 píxeles,
   100 % con P actual y 0 % con el previo; SL, 119 píxeles, 100 % con P_IR actual y 0 % con el previo.
   Esta medida no reemplaza el punto 3 del criterio: se informa al lado.
2. **Soporte de SL.** Para SL el punto 2 se informa como "píxeles de huella sin SL" y "SL fuera de la
   huella", porque el Jaccard contra un campo definido en toda la grilla no mide lo que quería medir.
3. **Tolerancia de altura** corregida a truncamiento (R7).

## Lo que la elección no puede decir

- Qué vale SL cuando P_IR es alta: en elección hay 6 píxeles con P_IR de 0,5 o más.
- Nada de noche ni de crepúsculo.
- Nada de un evento `ASHPLUMEPUFF`.
