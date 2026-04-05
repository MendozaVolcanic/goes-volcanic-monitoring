# Bandas ABI Relevantes para Monitoreo Volcánico

## Tabla Completa de Bandas ABI (GOES-R Series)

| Banda | Longitud de onda (um) | Tipo | Resolución (km) | Uso Volcánico |
|-------|----------------------|------|-----------------|---------------|
| 1 | 0.47 | Vis | 1.0 | - |
| 2 | 0.64 | Vis | 0.5 | Seguimiento visual de pluma (día) |
| 3 | 0.86 | NIR | 1.0 | - |
| 4 | 1.37 | NIR | 2.0 | - |
| 5 | 1.6 | NIR | 1.0 | - |
| 6 | 2.2 | NIR | 2.0 | - |
| **7** | **3.9** | **IR** | **2.0** | **Hot spots (anomalías térmicas, lava)** |
| 8 | 6.2 | IR | 2.0 | Vapor de agua nivel alto |
| 9 | 6.9 | IR | 2.0 | Vapor de agua nivel medio, tracking de pluma |
| **10** | **7.34** | **IR** | **2.0** | **Detección de SO2 (absorción fuerte)** |
| **11** | **8.5** | **IR** | **2.0** | **SO2 + discriminación ceniza/hielo** |
| 12 | 9.6 | IR | 2.0 | Ozono |
| **13** | **10.35** | **IR** | **2.0** | **Ventana limpia IR - componente azul Ash RGB** |
| **14** | **11.2** | **IR** | **2.0** | **Ventana LW - detección de ceniza (split-window)** |
| **15** | **12.3** | **IR** | **2.0** | **Ventana "sucia" - discriminación ceniza/SO2** |
| **16** | **13.3** | **IR** | **2.0** | **Altura de nube de ceniza (absorción CO2)** |

## Receta Ash RGB (funciona día y noche)

| Componente | Cálculo | Rango | Significado Físico |
|-----------|---------|-------|-------------------|
| Rojo | Band 15 (12.3um) - Band 14 (11.2um) | -6.7 a 2.6 K | Espesor óptico / grosor de nube |
| Verde | Band 14 (11.2um) - Band 11 (8.4um) | -6.0 a 6.3 K | Fase / tamaño de partícula |
| Azul | Band 13 (10.3um) | 243.6 a 302.4 K | Temperatura de superficie/tope de nube |

### Interpretación de colores Ash RGB

| Color | Característica |
|-------|---------------|
| Rojos a magentas | **Ceniza volcánica pura** |
| Verdes brillantes | **Dióxido de azufre (SO2)** |
| Amarillos | Mezcla ceniza + SO2 |
| Verde claro a gris | Nubes bajas gruesas de agua |
| Marrón claro | Nubes medias gruesas |
| Verde oscuro | Nubes medias delgadas |
| Azul pálido | Superficie terrestre |
| Azul oscuro a negro | Cirrus alto delgado |

## Principio Físico: Split-Window

La técnica "split-window" explota la diferencia de temperatura de brillo (BTD) entre 11um y 12um:
- **Ceniza volcánica**: BTD negativo (BT11 - BT12 < 0) por propiedades de absorción de silicatos
- **Nubes de hielo/agua**: BTD positivo
- La banda 8.5um agrega discriminación por tamaño y fase de partícula

## Modos de Escaneo

| Modo | Full Disk | CONUS/PACUS | Mesoscale |
|------|-----------|-------------|-----------|
| Mode 6 (default) | 10 min | 5 min | 1 min (x2) o 30 seg (x1) |
| Mode 3 | 15 min | 5 min | 1 min |

## Referencias
- GOES-R ABI Technical Summary: https://www.goes-r.gov/spacesegment/ABI-tech-summary.html
- Ash RGB Quick Guide (RAMMB/CIRA): https://rammb.cira.colostate.edu/training/visit/quick_guides/GOES_Ash_RGB.pdf
- SO2 RGB Quick Guide: https://rammb.cira.colostate.edu/training/visit/quick_guides/Quick_Guide_SO2_RGB.pdf
