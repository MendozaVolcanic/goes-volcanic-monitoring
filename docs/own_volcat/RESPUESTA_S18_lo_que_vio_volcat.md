# ¿Podemos detectar lo que VOLCAT vio esos días en Chillán? Respuesta de S18, 22-11-2026

Pregunta de Nicolás, textual: "crees que podamos lograr a detectar lo que vio volcat esos pocos dias en chillan?"

Escrita antes de correr la prueba de S18 (H24). Cada afirmación cita el informe de `docs/own_volcat/` del que
sale. Las probabilidades son estimaciones mías, no mediciones.

## Respuesta corta

**Lo que VOLCAT marcó en Chillán, tal como VOLCAT lo marcó, no creo que lo podamos reproducir con el infrarrojo de
GOES-19, y no porque nos falte una tabla: VOLCAT tampoco lo ve en el píxel.** Su propia probabilidad infrarroja en la
huella de Chillán es menor que 0,05 en 762 de 767 píxeles (H20a, §1). Lo que publica sale de una decisión sobre un
objeto pegado a un cráter caliente que sigue entre cuadros (H19, H20c), no de una medición de ceniza en la
radiancia. Reproducir esa decisión se puede; medir lo mismo que ella, no, porque no hay nada que medir en el píxel.

Lo que sí vale la pena es cambiar la pregunta: dejar de usar a VOLCAT como verdad y usar los pulsos que el OVDAS vio
con cámaras (REAV), que traen hora y altura. Eso dice si un satélite IR de 2 km puede ver estas plumas, con verdad
independiente y sin la circularidad de H23. Es la prueba que propongo para S18.

## Los tres caminos

### (a) Detección cuadro a cuadro con el IR de GOES-19

**Qué dicen los datos.**
- VOLCAT mismo no ve la pluma en el IR del píxel: P infrarroja < 0,05 en 762 de 767 píxeles, ninguno sobre 0,5
  (H20a §1). Lo que publica de día es casi siempre bajo (P < 20 % en la huella en 40 de 41 cuadros; sitio_volcat).
- Nuestras tablas reproducidas dan lo mismo: probabilidades del orden del prior en la huella (auditoría S15 §"En una
  pantalla", punto 1).
- Con cielo despejado, GOES-19 ve sobre la cumbre una capa de ε 0,15 si su tope está a 5 km; a 3 km no la ve ni casi
  opaca, y a 4 km sólo en la mañana (H23 §1 y §4). En las horas de los eventos de noviembre la BTD de cumbre quedó
  entre −0,12 y +0,12 K, dentro del fondo; una capa de ε 0,15 a 5 km la habría bajado 0,45 a 0,60 K (H23 §7). La
  pluma real queda bajo el límite (SOSPECHA en H23, porque la cota es en parte circular).
- Lejos de la cumbre tampoco: la pluma desprendida del 14-11 está 1,4 K más tibia que su control a más de 30 km, sin
  firma de BTD (H22 §1).

**Qué lo decidiría.** Una pluma de verdad conocida, alta y con cielo despejado, que el detector no vea. Eso es H24
(abajo): si ni los pulsos de 2 km sobre el cráter documentados por el OVDAS dejan firma, el camino queda cerrado
con verdad independiente.

**Costo.** Lo que queda por probar en este camino es H24 (unas horas, < 1 GB).

**Probabilidad estimada de reproducir las marcas de VOLCAT así: 5 % o menos.**

### (b) Integración en el tiempo o seguimiento, como VOLCAT

**Qué dicen los datos.**
- En Kirishima, lo que sube la probabilidad publicada es el seguimiento del objeto: empieza en el cuadro en que el
  log dice "Temporal selection criteria met for ash", con la P de las tablas de día igual a la infrarroja (0,05 a
  0,08) (H20c §1 y §2). Es una regla del objeto, no una firma más débil que se acumule.
- En Chillán esa vía casi no actúa: la P publicada sube sobre 0,5 sólo en 5 de 60 cuadros (H20a §1; H20c §1).
- El cambio entre cuadros de 10 min no separa la pluma: mejor AUC 0,58 y el anillo sin ceniza da 0,54 a 0,55
  (H13 §1, falsada).
- Promediar 1 o 3 horas no baja el límite de detección (H23 §6, S1): el fondo no es ruido que se cancele, es un
  corrimiento que dura horas.
- El residuo del fondo con cielo despejado es coherente entre vecinos hasta 15 a 20 km y entre cuadros hasta media
  hora (H22 §1, punto 3). La lista de ideas de S16 ya ponía esa condición para abortar el apilado a lo largo del
  viento (`ideas_s16_chillan.md`, idea 4): se cumple.
- Nuestra regla "calor en el cráter y objeto chico anclado" detecta 13 % de los cuadros con pluma VOLCAT con 7 % de
  falsas alarmas en cuadros limpios (H17, veredicto).

**El riesgo que manda.** Un seguimiento sobre un fondo coherente encuentra "plumas" en el ruido de la cumbre: el
fondo tiene justo la forma (manchas de 15 a 20 km que duran media hora o más) que un seguidor premia. Con lo medido
en H13, H17, H22 y H23, espero que cualquier seguidor nuestro tenga una tasa de falsas alarmas del mismo orden que
su tasa de detección.

**Qué lo decidiría.** Correr un seguidor y medir su tasa de falsas alarmas en días sin marca y en Antuco y Longaví.
Hoy los datos ya anticipan la respuesta, por eso no lo pongo primero.

**Costo.** Un día de trabajo, ~5 GB.

**Probabilidad estimada de un seguidor útil (detección clara sobre falsas alarmas): 5 % o menos.** Podríamos copiar
la decisión de VOLCAT (objeto anclado a un cráter caliente, seguido), pero sería copiar una regla, no detectar
ceniza.

### (c) Cambiar la pregunta: ¿lo que VOLCAT marcó era ceniza visible desde satélite?

**Qué dicen los datos.**
- El VAAC Buenos Aires confirma 3 de 30 marcas de VOLCAT, ninguna con fuente independiente, y en noviembre repite
  que el OVDAS, pilotos o cámaras reportan emisión mientras la imagen satelital no muestra ceniza (H21 §1).
- La huella de VOLCAT no sigue a la pluma que vio el OVDAS ni al viento: queda siempre entre el S y el E del
  cráter; el 27-10 VOLCAT no dibujó ningún objeto anclado en 42 cuadros con ocho pulsos documentados de hasta
  1.640 m (H10 §1). El REAV de ese día dice en su información satelital "Sin actividad destacable".
- En el sector donde el OVDAS vio la pluma, la BTD baja 0,2 a 0,4 K respecto del mismo lugar en un día sin pluma
  (AUC 0,68 el 25-10 y 0,70 el 27-10) y no baja en el sector opuesto (0,56 y 0,57) (H10 §1). Quedó a menos de
  0,02 del umbral: es el único indicio a favor que tiene el proyecto, y vino de usar la pluma vista y no la huella
  de VOLCAT.
- Para los días clave de VOLCAT (13 al 18-11) no hay REAV publicados (cronología del 19-11, `busqueda_2026-11-19_D_cronologia_chillan.md` en la carpeta de notas de la sesión
  `local_1055cba6`, tabla de cobertura: "13-11 a 19-11: Nada").
  Para esos días la verdad independiente sería el registro de cámaras del OVDAS, que decides tú si se pide.

**Qué lo decidiría (H24).** Los 14 episodios REAV del 25-10 al 12-11, con hora, altura y dirección (viento GFS
cuando el REAV no la da). Con el mejor detector de H23 (BTD contra la línea base del propio píxel, escena
despejada) se mide el sector a favor del viento contra el resto del anillo en el mismo cuadro, se compara con el
mismo cálculo en días sin REAV y sin marca de VOLCAT (falsas alarmas), y se inyecta una capa conocida a la altura y
hora de cada episodio para saber si había poder. Decide sobre los pulsos altos (≥ 1.800 m sobre el cráter, tope
≈ 5 km), que son los que H23 dice que deberían verse.

**Costo.** 8 días de L1b de dos bandas en la ventana (≈ 15 min de descarga, < 1 GB), máscara de nubes y GFS de esos
días; análisis reutilizando el código de H23. Unas 4 a 6 horas.

**Probabilidad estimada.** De que la prueba dé una respuesta clara (sí o no): 60 %. De que los pulsos altos sí
dejen firma IR: 25 a 30 %. Si la dejan, se abre un camino nuevo (un detector propio de pulsos altos, validado
contra el OVDAS y no contra VOLCAT). Si no la dejan, la respuesta a tu pregunta queda en "no", con verdad del
terreno y no por una cota circular.

## Qué haría yo

1. H24 hoy (esta sesión).
2. Según salga: si los pulsos altos se ven, aplicar el mismo detector a las marcas de VOLCAT del 13 al 18-11 y al
   resto de octubre; si no se ven, cerrar la línea "reproducir VOLCAT" y dejar a VOLCAT como capa externa
   (como está hoy en el dashboard, ficha SDA §A.7).
3. En los dos casos, el correo a Pavolonis se vuelve más corto y más preciso, pero eso sigue siendo decisión tuya.
