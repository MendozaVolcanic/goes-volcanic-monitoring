"""Configuración centralizada del proyecto GOES Volcanic Monitoring."""

from pathlib import Path

# ── Directorios ──────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
CACHE_DIR = DATA_DIR / "cache"

for d in [RAW_DIR, PROCESSED_DIR, CACHE_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# ── GOES S3 ──────────────────────────────────────────────────────
GOES_SATELLITE = 19          # GOES-East (cubre Sudamérica)
GOES_BUCKET = f"noaa-goes{GOES_SATELLITE}"
S3_REGION = "us-east-1"

# Productos que usamos
PRODUCTS = {
    "L1b_rad": "ABI-L1b-RadF",     # Radiancias Full Disk (para Ash RGB custom)
    "mcmip":   "ABI-L2-MCMIPF",    # Multi-Channel CMI (GeoColor, multi-banda)
    "fdc":     "ABI-L2-FDCF",      # Fire/Hot Spot Detection
}

# ── Bandas volcánicas ────────────────────────────────────────────
# Bandas ABI necesarias para productos volcánicos
VOLCANIC_BANDS = {
    7:  {"wavelength": 3.9,  "name": "shortwave_ir", "use": "hot spots"},
    11: {"wavelength": 8.4,  "name": "cloud_top",    "use": "SO2 + ceniza/hielo"},
    13: {"wavelength": 10.35,"name": "clean_window",  "use": "Ash RGB azul"},
    14: {"wavelength": 11.2, "name": "longwave_ir",   "use": "split-window ceniza"},
    15: {"wavelength": 12.3, "name": "dirty_window",  "use": "split-window ceniza"},
}

# ── Ash RGB Recipe (RAMMB/CIRA) ─────────────────────────────────
# Ref: https://rammb.cira.colostate.edu/training/visit/quick_guides/GOES_Ash_RGB.pdf
ASH_RGB = {
    "red":   {"calc": "B15 - B14", "range": (-6.7, 2.6)},   # 12.3 - 11.2 um
    "green": {"calc": "B14 - B11", "range": (-6.0, 6.3)},   # 11.2 - 8.4 um
    "blue":  {"calc": "B13",       "range": (243.6, 302.4)}, # 10.35 um (BT)
}

# ── Ash/SO2 RGB Recipe (8.5-11-12, EUMETSAT-adapted) ───────────
# Optimizado para separar ceniza de SO2 usando 8.4 um
# Ref: EUMETSAT Ash RGB technical guide
ASH_SO2_RGB = {
    "red":   {"calc": "B14 - B15", "range": (-4.0, 2.0)},   # 11.2 - 12.3 um
    "green": {"calc": "B11 - B14", "range": (-4.0, 5.0)},   # 8.4 - 11.2 um
    "blue":  {"calc": "B14",       "range": (243.0, 303.0)}, # 11.2 um (BT)
}

# ── BTD Split-Window thresholds ──────────────────────────────────
# Ref: Prata (1989), GOES-R ATBD Volcanic Ash v3.0
BTD_ASH_THRESHOLD = -1.0      # BT(11.2) - BT(12.3) < threshold → posible ceniza
BTD_MIN_TEMP = 200.0           # Mínimo BT(11.2) para filtrar pixeles fríos
BTD_TRI_THRESHOLD = 0.0       # (BT8.4-BT11.2) + (BT12.3-BT11.2) < 0 → ceniza mejorada

# ── Región Chile ─────────────────────────────────────────────────
CHILE_BOUNDS = {
    "lat_min": -56.0,   # Cabo de Hornos
    "lat_max": -17.5,   # Frontera norte
    "lon_min": -76.0,   # Costa Pacífico
    "lon_max": -66.0,   # Frontera este
}

# Subregiones volcánicas
VOLCANIC_ZONES = {
    "norte": {"lat_min": -28.0, "lat_max": -17.5, "lon_min": -71.0, "lon_max": -66.0},
    "centro": {"lat_min": -39.0, "lat_max": -28.0, "lon_min": -73.0, "lon_max": -68.0},
    "sur": {"lat_min": -46.0, "lat_max": -39.0, "lon_min": -74.0, "lon_max": -70.0},
    "austral": {"lat_min": -56.0, "lat_max": -46.0, "lon_min": -76.0, "lon_max": -70.0},
}
