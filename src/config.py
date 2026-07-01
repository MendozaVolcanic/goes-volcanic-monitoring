"""Configuración centralizada del proyecto GOES Volcanic Monitoring."""

import os
import tempfile
from pathlib import Path

# ── Directorios ──────────────────────────────────────────────────
# Estos directorios SOLO se usan en src/process/pipeline.py (Ash + BTD)
# y en src/fetch/goes_s3.py para procesar L1b crudo descargado de S3
# NOAA. El dashboard NRT principal NO los necesita.
#
# CASO DEPLOY HF SPACES (mayo 2026): el container Docker corre con user
# UID 1000 sin permisos sobre /app/data. Antes hacíamos `mkdir` con
# try/except — sobrevivía el import, pero CUALQUIER intento posterior
# de escribir tiraba `PermissionError: '/app/data'`, rompiendo la vista
# Ash + BTD entera con un mensaje feo al user.
#
# FIX: detectar si el path "ideal" es escribible. Si NO, redirigir a
# `$HF_HOME/goes-data` (HF Spaces) o `tempfile.gettempdir()/goes-data`
# (cualquier OS). Asi los consumidores siempre reciben un Path donde
# pueden escribir, sin tener que conocer el ambiente.
PROJECT_ROOT = Path(__file__).parent.parent
_DATA_DIR_IDEAL = PROJECT_ROOT / "data"


def _writable_data_root() -> Path:
    """Devuelve el primer dir escribible: ideal -> HF home -> /tmp.

    Se evalua una sola vez al importar config. Si el deploy es HF Spaces
    (read-only /app), cae automaticamente a un dir bajo /home/user o /tmp.
    """
    candidates = [_DATA_DIR_IDEAL]
    # HF Spaces convention: $HOME existe y es escribible para UID 1000
    home = os.environ.get("HOME")
    if home:
        candidates.append(Path(home) / "goes-data")
    candidates.append(Path(tempfile.gettempdir()) / "goes-data")
    for c in candidates:
        try:
            c.mkdir(parents=True, exist_ok=True)
            # Test real de escritura (mkdir puede pasar en dir read-only
            # que ya existia con perms abiertos en la jerarquia)
            test = c / ".write_test"
            test.touch()
            test.unlink()
            return c
        except (PermissionError, OSError):
            continue
    # Si todo falla, devolver tempdir sin chequeo (siempre escribible
    # en POSIX por definicion).
    return Path(tempfile.gettempdir()) / "goes-data"


DATA_DIR = _writable_data_root()
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
CACHE_DIR = DATA_DIR / "cache"

for d in [RAW_DIR, PROCESSED_DIR, CACHE_DIR]:
    try:
        d.mkdir(parents=True, exist_ok=True)
    except (PermissionError, OSError):
        # Backup defensivo: DATA_DIR ya fue validada escribible, pero
        # los subdirs pueden fallar en edge cases (UID mid-run change).
        pass

# ── GOES S3 ──────────────────────────────────────────────────────
GOES_SATELLITE = 19          # GOES-East (cubre Sudamérica)
GOES_BUCKET = f"noaa-goes{GOES_SATELLITE}"
S3_REGION = "us-east-1"

# Subsatellite point de GOES-19 (GOES-East operacional desde Apr 2025).
# Validado contra L1b oficial NOAA. El valor anterior -75.2 era de GOES-16
# y producía offset de ~17 km al sur de Chile en los mapas (bug histórico
# arreglado mayo 2026). Cualquier llamada a pyproj GEOS debe usar este valor.
GOES19_SAT_LON = -75.0

# Altura del satélite GOES geoestacionario en metros (canonical NOAA).
# Cualquier llamada a pyproj GEOS debe usar este valor como h=, salvo
# que se lea explícitamente del NetCDF (perspective_point_height) — eso
# es lo canónico del archivo y siempre prevalece.
GOES19_PERSPECTIVE_POINT_HEIGHT = 35786023.0  # metros

# Maximo scan angle del ABI Full Disk (radianes). Es la "media-anchura"
# del fixed grid; CFAC = (full_disk_pixels/2) / ABI_MAX_SCAN_ANGLE.
ABI_MAX_SCAN_ANGLE = 0.151872  # radianes

# ── Bboxes default por scope (centralizados para que un cambio aplique
# consistentemente a todos los pipelines). Antes estaban dispersos en
# rammb_slider, mosaico_chile, replay_reciente, hires_pipeline. ────────
VOLCANO_RADIUS_DEG_FULL = 1.5      # Vista volcán amplia (rammb_viewer)
MOSAICO_RADIUS_DEG = 0.5           # Mosaico Modo Guardia (~55 km)
HIRES_RADIUS_DEG = 0.5             # Hi-res NOAA por volcán
REPLAY_RADIUS_DEG = 0.4            # Replay reciente

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

# ── Bandas IR extendidas (VOLCAT propio Fase 1+) ─────────────────
# C10 (7.4µm) y C16 (13.3µm) NO van en VOLCANIC_BANDS para no hacer que el
# pipeline Ash RGB (download_volcanic_bands) baje 2 bandas que no usa (+40%
# datos/scan). Las baja directo el código de altura propia (ACHA/BT-matching/
# CO2-slicing) vía download_band_at cuando las necesita.
#   - C10 (7.4µm): vapor de agua bajo / discriminación multicapa (ATBD detección).
#   - C16 (13.3µm): banda de absorción de CO2 → sensibilidad a ALTURA (CO2-slicing).
EXTENDED_IR_BANDS = {
    10: {"wavelength": 7.4,  "name": "lower_water_vapor", "use": "multicapa ATBD"},
    16: {"wavelength": 13.3, "name": "co2",               "use": "altura (CO2-slicing)"},
}

# ── SO2 indicator threshold ──────────────────────────────────────
# BT(8.4µm) - BT(11.2µm) = C11 - C14. Muy negativo = absorción de SO2.
# Ref: CLAUDE.md / receta SO2. Umbral indicativo, NO cuantitativo.
SO2_INDICATOR_THRESHOLD = -3.0

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
    # Bboxes uniformizados: 5° lon × ~10-11° lat para que en grid 1x4
    # los 4 paneles tengan aspect ratio similar y la imagen llene
    # consistentemente.
    # OJO (fix audit jun 2026): el boundary sur/austral estaba ~5° corrido al
    # sur — los 13 volcanes 'austral' (Osorno -41.1 … Hudson -45.9) caían DENTRO
    # del bbox 'sur' y el bbox 'austral' (-56…-46) quedaba VACÍO (solo fiordos).
    # Corregido para que cada bbox CONTENGA los volcanes de su zona (validado en
    # tests/test_smoke.py::test_zone_bboxes_contain_their_volcanoes).
    # AUSTRAL (pedido jul-2026): el bbox anterior cortaba en -46.5 y dejaba
    # afuera el TERRITORIO de Aysén sur + Magallanes (Chile llega a ~-56),
    # aunque no haya volcanes monitoreados al sur de Hudson (-45.9). Se
    # extiende lat a -56 y se ensancha lon a 10°: a ~-50° el cos(lat)
    # comprime la longitud, así que el aspect VISUAL del panel (~2.3) queda
    # igual al de Norte y el grid 1x4 no se deforma. Los 13 volcanes
    # australes siguen contenidos (test_zone_bboxes_contain_their_volcanoes).
    "norte":   {"lat_min": -28.0, "lat_max": -17.5, "lon_min": -71.5, "lon_max": -66.5},
    "centro":  {"lat_min": -39.0, "lat_max": -28.0, "lon_min": -73.0, "lon_max": -68.0},
    "sur":     {"lat_min": -41.5, "lat_max": -36.0, "lon_min": -75.0, "lon_max": -70.0},
    "austral": {"lat_min": -56.0, "lat_max": -41.0, "lon_min": -76.0, "lon_max": -66.0},
}
