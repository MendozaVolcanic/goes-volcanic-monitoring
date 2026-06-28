# own_volcat — VOLCAT propio (altura de pluma desde GOES-19 ABI)

Investigación y planificación para **generar nuestro propio retrieval cuantitativo de altura de
pluma volcánica / ceniza** desde GOES-19 ABI L1b, reduciendo la dependencia del único host SSEC
(`volcano.ssec.wisc.edu`, latencia ~30-50 min + caídas).

## Contenido

| Archivo | Qué es |
|---|---|
| **`PLAN_VOLCAT_PROPIO.md`** | Documento principal: síntesis del algoritmo VOLCAT (desde el ATBD), gap analysis (tenemos vs. falta), investigación de código open-source, y **plan por fases** con esfuerzo. **Empezar acá.** |
| `Pavolonis_2010_CloudCompositionTheory.pdf` | Paper base teórico (β-ratios, emisividad efectiva). OA AMS. |
| `HeidingerPavolonis_2009_SplitWindowCirrus.pdf` | Base del ACHA y de las a priori del optimal estimation. OA AMS. |

## Resumen en 4 líneas

- **Algoritmo de referencia:** optimal estimation (1DVAR, Rodgers 1976) sobre 3 canales IR ABI
  (11, 12, **13.3 µm**) → retrieva Teff, ε(11µm), β(12/11µm); la **altura** sale de mapear Teff a un
  **perfil NWP T(z)** (GFS). Detalle completo en `PLAN_VOLCAT_PROPIO.md` §1.
- **Brecha principal:** nos falta el **forward model radiativo + perfil NWP vertical en NRT** y el
  **esquema OE** (la matemática es fácil; estos dos son caros). Tenemos bandas 11/12/8.5, Planck, BTD
  y detección; faltan bandas 7.4 (C10) y 13.3 µm (C16).
- **Código reutilizable:** NO hay módulo Python liviano. ORAC/CLAVR-x lo hacen pero son Fortran +
  RTM + NWP pesados. Atajo real: **leer `ABI-L2-ACHAF` (Cloud Top Height NOAA, ya en el bucket) +
  enmascarar con ceniza** = VOLCAT-lite con cero deps nuevas.
- **Camino recomendado:** Fase 0 (ACHA, 1-2 días) → C10/C16 + perfil GFS → Wen-Rose como respaldo
  independiente. Mantener VOLCAT/RealEarth como primario cuantitativo. **Saltar el OE propio** salvo
  justificación fuerte.

## Notas

- Papers **no descargables** (Pavolonis 2013 canónico, Pavolonis 2015, Wen&Rose 1994) están detrás
  de anti-bot Cloudflare/WAF pero son OA legales — bajar con navegador real (URLs en
  `PLAN_VOLCAT_PROPIO.md` §6). Prata 1989 es paywall puro.
- Material previo relacionado: `../ALTURA_COLUMNA_INVESTIGACION.md`, `../VOLCAT_LATENCIA_Y_ALTERNATIVAS.md`,
  `../altura_pluma/`.
