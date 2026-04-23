# Sectores VOLCAT relevantes para Chile

Inventario verificado contra el API de VOLCAT (23/abr/2026, 172 sectores
totales). Solo sectores pertinentes a monitoreo SERNAGEOMIN y los dos
volcanes de test (Popocatépetl, Kīlauea).

## Sectores con datos GOES-19 ABI (cadencia 10 min)

Estos son los más útiles para operación continua.

| Sector | Volcán / Región | Resolución | Satélites ABI | Uso sugerido |
|--------|-----------------|------------|---------------|--------------|
| `Copahue_250_m` | Copahue | 250 m | **GOES-19 + GOES-18** | Vista zoom Copahue. Doble cobertura paralaje potencial. |
| `Calbuco_1_km` | Calbuco | 1 km | GOES-19 | Vista zoom Calbuco. Resolución moderada. |
| `Planchon-Peteroa_500_m` | Planchón-Peteroa | 500 m | **GOES-19 + GOES-18** | Vista zoom. |
| `Chile_North_2_km` | Zona norte (Láscar, Parinacota, Isluga, Lastarria, Ojos del Salado) | 2 km | GOES-19 | Panorama zona norte. |
| `Chile_Central_2_km` | Zona centro (Nevados de Chillán, Copahue, Planchón-Peteroa, Laguna del Maule) | 2 km | GOES-19 | Panorama zona centro. |
| `Chile_South_2_km` | Zona sur (Villarrica, Llaima, Puyehue, Osorno, Calbuco, Chaitén) | 2 km | GOES-19 | **Única cobertura ABI para Villarrica.** |
| `Argentina_5_km` | Argentina completa | 5 km | GOES-19 | Vista general regional. |

## Sectores solo VIIRS (polar, ~12 h por satélite)

Mayor resolución espacial pero gap temporal alto. Útiles como "second
opinion" cuando pasa una órbita NOAA-20/NOAA-21/S-NPP encima.

| Sector | Volcán | Resolución | Nota |
|--------|--------|------------|------|
| `Villarrica_250_m` | Villarrica | 250 m | NO tiene ABI — para vista continua usar `Chile_South_2_km`. |

## Sectores de los volcanes de test

| Sector | Volcán | Resolución | ABI |
|--------|--------|------------|-----|
| `Popocatepetl_250_m` | Popocatépetl | 250 m | GOES-19 |
| `Popocatepetl_750_m` | Popocatépetl | 750 m | GOES-19 |
| `Popocatepetl_2_km` | Popocatépetl | 2 km | GOES-19 |
| `Kilauea_250_m` | Kīlauea | 250 m | **GOES-18** (West) |
| `Hawaii_500_m` | Hawaii | 500 m | GOES-18 |
| `Hawaii_2_km` | Hawaii | 2 km | GOES-18 |

Nota: Kīlauea es mejor visto desde GOES-**West** (GOES-18) porque está al
oeste del meridiano de 140°. GOES-19 (East, -75°) lo ve en el limbo
con geometría muy oblicua.

## Mapping volcán SERNAGEOMIN → sector VOLCAT

Para cada volcán en nuestro catálogo (`src/volcanos.py`), el sector VOLCAT
más apropiado:

| Volcán (nuestro catálogo) | Zona | Sector VOLCAT recomendado |
|--------------------------|------|---------------------------|
| Taapaca, Parinacota, Guallatiri, Isluga, Irruputuncu, Olca, Aucanquilcha, Ollagüe, San Pedro, Putana, Láscar, Lastarria, Ojos del Salado | norte | `Chile_North_2_km` |
| Nevado de Longaví, Descabezado Grande, Cerro Azul/Quizapu, Planchón-Peteroa, Laguna del Maule, Nevados de Chillán, Antuco, **Copahue**, Callaqui | centro | `Chile_Central_2_km`; para Copahue usar `Copahue_250_m`; para Planchón usar `Planchon-Peteroa_500_m` |
| Lonquimay, Llaima, Sollipulli, **Villarrica**, Quetrupillán, Lanín, Mocho-Choshuenco, Puyehue-Cordón Caulle, Casablanca, Osorno, **Calbuco**, Yate, Hornopirén, Huequi, Michinmahuida, Chaitén | sur | `Chile_South_2_km`; para Calbuco usar `Calbuco_1_km` |
| Corcovado, Melimoyu, Mentolat, Hudson, Lautaro | austral | `Chile_South_2_km` o `Argentina_5_km` (Lautaro queda lejos; Hudson viene en `Chile_South_2_km`) |
| **Kīlauea (test)** | test | `Kilauea_250_m` (usa GOES-18) |
| **Popocatépetl (test)** | test | `Popocatepetl_250_m` |

## Volcanes SIN sector VOLCAT dedicado

En Chile VOLCAT NO tiene sectores específicos para:
- Láscar, Parinacota (se ven en `Chile_North_2_km`)
- Llaima, Villarrica sólo en resolución 2 km (`Chile_South_2_km`)
- Puyehue-Cordón Caulle, Chaitén, Hudson, Corcovado — solo 2 km

**Posible pedido a SSEC**: solicitar sector `Villarrica_250_m_ABI` y
`Lascar_250_m` via formulario de contacto en https://cimss.ssec.wisc.edu/volcat/
cuando tengamos evento activo que justifique la petición.

## Cómo se vería en el dashboard

Propuesta de UI en la pestaña "Por Volcán" (a implementar):

```
┌───────────────────────────────────────────────┐
│ Volcán: ★ Villarrica              [cambiar]   │
│ ─────────────────────────────────────────────  │
│ Tab: [ GeoColor | Ash RGB | SO2 | Altura ]    │
│ ─ Altura (VOLCAT) ─────────────────────────── │
│  ┌─────────────────────────────┐              │
│  │  [PNG Ash_Height]           │  Sector:     │
│  │  color = altitud en km      │  Chile_South │
│  │  (leyenda overlay a la der) │  _2_km       │
│  └─────────────────────────────┘              │
│  Scan: 2026-04-23 12:50 UTC (GOES-19 ABI)     │
│  Fuente: CIMSS/SSEC VOLCAT                    │
└───────────────────────────────────────────────┘
```
