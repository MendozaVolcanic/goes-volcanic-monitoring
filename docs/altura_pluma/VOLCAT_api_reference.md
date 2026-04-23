# VOLCAT API Reference (CIMSS/SSEC)

Base URL: `https://volcano.ssec.wisc.edu`

**Autenticación: ninguna. Costo: gratis. Rate limit: no documentado, razonable.**

## El endpoint único

```
GET {BASE}/imagery/get_list/json/sector:{S}::instr:{I}::sat:{SAT}::image_type:{T}::endtime:{E}::daterange:{D}
```

Los parámetros van **separados por `::` como segmentos de URL**, NO como query
string (query string devuelve lista vacía — comprobado).

## Parámetros válidos (todos verificados en vivo)

### `sector` — región geográfica pre-definida

172 sectores en total. Relevantes para Chile y volcanes de test:

| Sector | Volcán / región | Resolución | Instrumentos disponibles |
|--------|-----------------|------------|--------------------------|
| `Villarrica_250_m` | Villarrica | 250 m | VIIRS (NOAA-20, NOAA-21, S-NPP) |
| `Copahue_250_m` | Copahue | 250 m | **ABI GOES-19 + GOES-18**, VIIRS |
| `Calbuco_1_km` | Calbuco | 1 km | ABI GOES-19, VIIRS |
| `Planchon-Peteroa_500_m` | Planchón-Peteroa | 500 m | ABI GOES-19 + GOES-18, VIIRS |
| `Chile_North_2_km` | Zona norte (Láscar, etc) | 2 km | ABI GOES-19 |
| `Chile_Central_2_km` | Zona centro | 2 km | ABI GOES-19 |
| `Chile_South_2_km` | Zona sur (cubre Villarrica con ABI) | 2 km | ABI GOES-19 |
| `Argentina_5_km` | Argentina | 5 km | ABI + VIIRS |
| `Popocatepetl_250_m` | Popocatépetl (test) | 250 m | ABI GOES-19 |
| `Popocatepetl_750_m` | Popocatépetl (test) | 750 m | ABI GOES-19 |
| `Kilauea_250_m` | Kīlauea (test) | 250 m | ABI GOES-18 (West) |

**Nota importante**: Villarrica en 250 m **solo tiene VIIRS** (cadencia ~12 h).
Para seguimiento continuo con GOES-19 usar `Chile_South_2_km`, o `Copahue_250_m`
para Copahue (que sí tiene ABI nativo).

### `instr` — instrumento

Valores aceptados: `ABI`, `VIIRS`, `SEVIRI`, `MODIS` (deprecado), `AHI`.
Se pueden combinar: `instr:ABI::instr:VIIRS`.

### `sat` — satélite

`GOES-18`, `GOES-19`, `NOAA-20`, `NOAA-21`, `S-NPP`, `MET-10`, o `all`.

### `image_type` — producto (11 opciones exactas)

| image_type | Qué es | Color-codificado |
|------------|--------|------------------|
| **`Ash_Height`** | **Altura de ceniza (km)** | **SÍ — el que queremos** |
| `Ash_Loading` | Masa de ceniza (g/m²) | SÍ |
| `Ash_Probability` | Probabilidad de ceniza (0-1) | SÍ |
| `Ash_Reff` | Radio efectivo (µm) | SÍ |
| `BT11um` | Temperatura de brillo 11 µm | SÍ (B/N) |
| `BTD1112um` | BTD split-window | SÍ |
| `REF065um` | Reflectancia banda 0.65 µm (día) | SÍ (B/N) |
| `RGB1112or13um_3911um_11um` | RGB composite ash variante | NO (true-color-ish) |
| `RGB1112or13um_3911um_11um_Ash_Retv` | RGB con mask de retrieval | NO |
| `RGB1112um_8511um_11um` | RGB Ash RGB estándar (como Dust RGB) | NO |
| `RGB1112um_8511um_11um_Ash_Retv` | RGB Ash con mask de retrieval | NO |

NOTA: **NO hay `Cloud_Top_Height` genérico aquí, ni `SO2_Mass_Loading`**.
Para SO2 usamos el SO2 RGB de RAMMB.

### `endtime`

- `latest` — trae el listado completo hasta el presente
- `YYYY-MM-DD_HH-MM-SS` — trae hasta esa fecha

### `daterange`

Minutos de ventana **pero es filtrado client-side**: el servidor siempre
devuelve la lista completa disponible. Para la imagen más reciente basta
con tomar `endtime[-1]`.

## Formato de respuesta

```json
{
  "sector":      {"cat": [...], "name": [... 172 sectores ...]},
  "instr":       ["ABI", "VIIRS"],
  "sat":         ["GOES-18", "GOES-19"],
  "image_type":  [... 11 productos ...],
  "endtime":     [
    {
      "datetime": "2026-04-23_12-50-30",
      "filename": "/data/sector_imagery/Copahue_250_m/ABI/GOES-18/Ash_Height/2026-04-23/GOES-18.ABI.2026-04-23.12-50-30.Ash_Height.Copahue_250_m.png",
      "annot":    "/data/sector_imagery/Copahue_250_m/ABI/GOES-18/ANNOTATIONS/...",
      "track_calipso": null, "track_noaa20": null, "track_snpp": null
    },
    ...
  ],
  "coordinates": {
    "PROJECTION":   "CE",                  // Cylindrical Equidistant
    "REF_LON":      289.10,                // = 360 - 70.9 → -70.9°
    "ORIGIN_LAT":   -36.90,
    "ORIGIN_LON":   287.84,                // = -72.16°
    "EQ_RADIUS":    206264.80,
    "SCALE_FACTOR": 8.96,                  // pixeles/grado
    "OFFSET_X":     0,
    "OFFSET_Y":     36
  },
  "overlay_ll":         [...],
  "overlay_vaac":       [...],
  "overlay_volcanoes":  [...],
  "overlay_maps":       [...]
}
```

## Patrón de URL de la imagen PNG

```
{BASE}/data/sector_imagery/{SECTOR}/{INSTR}/{SAT}/{IMAGE_TYPE}/{YYYY-MM-DD}/{SAT}.{INSTR}.{YYYY-MM-DD}.{HH-MM-SS}.{IMAGE_TYPE}.{SECTOR}.png
```

**Ejemplo verificado (2026-04-23 12:50:30 UTC, HTTP 200):**
```
https://volcano.ssec.wisc.edu/data/sector_imagery/Copahue_250_m/ABI/GOES-18/Ash_Height/2026-04-23/GOES-18.ABI.2026-04-23.12-50-30.Ash_Height.Copahue_250_m.png
```

## Overlays (lat/lon, volcanes, VAACs, leyenda de colores)

URLs estáticas. Se componen por encima de la imagen del producto.

```
{BASE}/data/sector_imagery_config/overlays/latlon/{SECTOR}.LATLON.CYAN.png
{BASE}/data/sector_imagery_config/overlays/vaac/{SECTOR}.VAACS.CYAN.png
{BASE}/data/sector_imagery_config/overlays/volcanoes/{SECTOR}.VOLCANOES.CYAN.png
{BASE}/data/sector_imagery_config/overlays/maps/{SECTOR}.MAP.{LEGEND}.png
```

`{LEGEND}` según `image_type`:
- `Ash_Height`, `Ash_Loading` → `ASH_HGT-LOAD` (cyan)
- `Ash_Probability` → `ASH_PROB` (magenta)
- `Ash_Reff` → `ASH_REFF` (magenta)
- `BT11um` → `BT11um` (black)
- `BTD1112um` → `BTD1112um` (black)
- `REF065um` → `REF065um` (magenta)
- `RGB*` → `RGB` (black o magenta según variante)

## Georreferenciación

Dado `coordinates` de la respuesta, el bounding box del PNG (WxH pixeles) es:

```python
lon_min = (ORIGIN_LON - 360) - (W/2) / SCALE_FACTOR   # grados E
lon_max = (ORIGIN_LON - 360) + (W/2) / SCALE_FACTOR
lat_max = ORIGIN_LAT + (H/2) / SCALE_FACTOR           # grados N
lat_min = ORIGIN_LAT - (H/2) / SCALE_FACTOR
```

(restar 360 porque VOLCAT usa longitud 0-360; nuestra convención es -180 a +180)

Esto permite usarlo como `ImageOverlay` en Folium o `add_layout_image` en Plotly.

## Código mínimo de integración

```python
import requests
BASE = "https://volcano.ssec.wisc.edu"

def volcat_latest(sector, instr="ABI", image_type="Ash_Height"):
    url = (
        f"{BASE}/imagery/get_list/json/"
        f"sector:{sector}::instr:{instr}::sat:all"
        f"::image_type:{image_type}::endtime:latest::daterange:180"
    )
    d = requests.get(url, timeout=20).json()
    if not d.get("endtime"):
        return None
    last = d["endtime"][-1]
    return {
        "datetime":   last["datetime"],
        "image_url":  BASE + last["filename"],
        "legend_url": f"{BASE}/data/sector_imagery_config/overlays/maps/{sector}.MAP.ASH_HGT-LOAD.png",
        "coords":     d["coordinates"],
    }

# Uso
info = volcat_latest("Copahue_250_m", "ABI", "Ash_Height")
```

## Cadencia de publicación

- **ABI (GOES-19/18)**: scan cada 10 min, VOLCAT lo procesa en ~5 min.
  Latencia total desde el fenómeno: **~15 min**.
- **VIIRS (NOAA-20/21/S-NPP)**: pasadas polares cada ~12 h por satélite, 3-6 h
  combinando los 3 satélites. Mayor resolución espacial (250 m) pero peor
  temporal.

## Licencia y atribución

- **Datos libres, sin auth, sin API key.**
- **Licencia**: no hay CC explícita; pie de página del sitio dice
  "informational only, use at sole risk of end user". Citar como:
  *"CIMSS/SSEC VOLCAT, University of Wisconsin-Madison & NOAA."*
- **Estado**: operacional, usado por todos los VAAC.
