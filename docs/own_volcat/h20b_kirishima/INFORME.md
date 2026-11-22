# H20b (S17): un evento de pluma de VOLCAT en Kirishima (Japón, 02-07-2025). Informe, 22-11-2026

**Resultado (descriptivo, un evento):** VOLCAT publicó la pluma de Kirishima con probabilidad baja en sus primeros
cuadros y la subió a alta en los siguientes, **sin que la probabilidad infrarroja de píxel subiera**. Es el mismo
patrón que el único evento de pluma de Fuego (San Cristóbal). Todo el evento ocurre con el sol bajo, así que no se
puede separar si lo que sube la probabilidad es la edad del objeto o la luz rasante.

Criterio: `criterio_2026-11-22.md`, commit `9b99364` (antes de leer ninguna probabilidad).

## 1. Para geólogo

**Qué se quería saber.** En Chillán, VOLCAT publica plumas (`ASHPLUMEPUFF`) aunque la probabilidad de ceniza de
cada píxel, en el infrarrojo, es casi cero. La pregunta era si eso es raro o si es la forma normal en que VOLCAT
publica una pluma. Para eso hacía falta otro evento de pluma con los archivos de evento completos.

**El caso.** SSEC publica un paquete de prueba de Kirishima (Himawari-9, sector Japón, un cuadro cada 2,5 minutos)
de julio de 2025. Trae un evento `ASHPLUMEPUFF` del volcán 282090 con 7 cuadros, de 20:17 a 21:00 UTC (05:17 a 06:00 hora
de Japón, al amanecer: el sol sube de 0,2° bajo el horizonte a 8° sobre él). H20a (PR 92) mostró que en estos archivos un campo es la probabilidad publicada y otro la
probabilidad infrarroja de píxel. Con eso se pueden leer sin la salida L2.

**Lo que salió.**

1. **La pluma nace con probabilidad baja.** En los 3 primeros cuadros la probabilidad publicada tiene mediana de
   0 a 0,05 en la huella del objeto.
2. **Después VOLCAT la sube, y el infrarrojo no acompaña.** En los 4 cuadros siguientes, con el objeto de 5 a 13
   minutos de edad, la mediana publicada es 0,60, 0,82, 0,97 y 0,72. La infrarroja queda entre 0,02 y 0,08.
3. **De noche las dos son iguales.** En el primer cuadro (sol 0,2° bajo el horizonte) la probabilidad publicada es
   idéntica a la infrarroja en los 8 píxeles. H20a vio lo mismo de noche en Chillán (112 de 127 píxeles).

**Qué significa para Chillán.** Publicar una pluma con probabilidad de píxel baja no es exclusivo de Chillán:
Kirishima arranca igual. La diferencia es que en Kirishima la probabilidad publicada sube después, como en
San Cristóbal, y en Chillán sube sólo en 5 de 60 cuadros (H20a). Esa subida ocurre, en los tres volcanes, con el sol
bajo. Con este único evento no se puede decir si la sube la edad del objeto (seguimiento entre cuadros) o una
tabla solar que pesa más con luz rasante.

## 2. Números (`resultados/por_cuadro.csv`, regla del criterio)

| Inicio (UTC) | Píxeles | P publicada, mediana | P infrarroja, mediana | Cenit solar | Edad (min) | Clase |
|---|---|---|---|---|---|---|
| 20:17 | 8 | 0,053 | 0,053 | 90,2° | 0 | INTERMEDIA |
| 20:47 | 9 | 0,000 | 0,024 | 84,4° | 0 | BAJA |
| 20:50 | 11 | 0,001 | 0,048 | 83,9° | 2,6 | BAJA |
| 20:52 | 4 | 0,605 | 0,036 | 83,5° | 5,2 | ALTA |
| 20:55 | 4 | 0,823 | 0,053 | 83,0° | 7,6 | ALTA |
| 20:57 | 5 | 0,966 | 0,024 | 82,5° | 10,0 | ALTA |
| 21:00 | 13 | 0,725 | 0,083 | 82,0° | 12,5 | ALTA |

Fracción de píxeles válidos: 100 % en los 7 cuadros. Los campos declaran el mismo `long_name` que en ABI.

**Análisis posterior (no estaba en el criterio, no decide):** el salto de log-odds entre la probabilidad
publicada y la infrarroja (`resultados/saltos_posthoc.txt`) es 0 exacto en el cuadro de noche. En los demás hay
saltos negativos (hasta −19,8) y positivos (hasta +24,4), con valores que se repiten entre cuadros (3,29; 3,37;
3,58; 3,99; 4,09; −15,26). No son los valores que H19 vio en la fase tardía de Fuego (12,74 a 18,96).

## 3. Lo que podría estar equivocado

- **Un solo evento, de otro sensor.** AHI usa otras tablas de píxel que ABI. La identidad de los campos se calibró
  en ABI (H20a); aquí sólo se comprobó que el `long_name` es el mismo. Si en AHI el campo significara otra cosa, la
  lectura cambia.
- **Edad y luz van juntas.** Todos los cuadros con probabilidad alta tienen cenit entre 82° y 84°. No hay un cuadro
  del mismo objeto con sol alto o de noche y edad grande para separarlas.
- **Dos nacimientos.** El cuadro de 20:17 y el de 20:47 tienen edad 0: el objeto se perdió y volvió a nacer. La
  "edad" es la del segundo nacimiento.
- **El paquete quedó incompleto.** La descarga se cortó por falta de disco; se conservaron completos `events/` y
  `alerts/` (los 41 archivos de evento abren bien), pero no la L2 ni los logs, que habrían dicho qué tabla o qué
  regla produce la subida.

## 4. Método

Script `scripts/h20b_medir.py` (regla del criterio) y `scripts/h20b_saltos_posthoc.py` (posterior). Datos:
`kirsh_h9-japan_july2025_r20260709-volcat-code-ancil.tar.gz` de `bin.ssec.wisc.edu/pub/volcat/test_cases/`,
`reference_data/events/` extraído a `D:\goes_notas\s17\paquetes\kirsh\`. Nada del paquete está en el repo; los
`.pkl` no se abrieron.
