"""Cliente para el tile server de RAMMB/CIRA Slider.

Accede a imágenes GOES-19 pre-procesadas en tiempo real desde
slider.cira.colostate.edu (Colorado State University / CIRA).

Productos disponibles para GOES-19 Full Disk:
  geocolor        → GeoColor (color real mejorado)
  eumetsat_ash    → Ash RGB (EUMETSAT)
  jma_so2         → SO2 indicator (JMA)
  split_window_difference_10_3-12_3 → BTD 10.3-12.3 um

Tile URL format:
  https://slider.cira.colostate.edu/data/imagery/
    YYYY/MM/DD/goes-19---full_disk/{product}/{timestamp}/{ZZ}/{RRR}_{CCC}.png

Cadencia Full Disk: cada 10 minutos.
"""

import io
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

import numpy as np
import requests
from PIL import Image

logger = logging.getLogger(__name__)

BASE_URL = "https://slider.cira.colostate.edu"
SATELLITE = "goes-19"
SECTOR = "full_disk"
TILE_SIZE = 678        # Todos los tiles son 678×678 px
TIMEOUT = 20

# Productos volcánicos disponibles y sus nombres para mostrar
PRODUCTS = {
    "geocolor":    "GeoColor (color real)",
    "eumetsat_ash": "Ash RGB (EUMETSAT/CIRA)",
    "jma_so2":     "SO2 (JMA)",
    "split_window_difference_10_3-12_3": "BTD 10.3-12.3 um",
}

# Tiles que cubren Chile y Sudamérica meridional en zoom nivel 2
# Full disk 10848×10848 nativa → zoom 2 = 4×4 tiles de 2712 px c/u
# Chile (lat -56 a -17.5, lon -76 a -66):
#   rows nativas ~6600-9200 → tiles fila 2 y 3
#   cols nativas ~4600-6100 → tiles col 1 y 2
CHILE_TILES_Z2 = {"rows": [2, 3], "cols": [1, 2]}

# Zoom 1 (2×2 tiles) cubre toda Sudamérica — más contexto, menor resolución
SOUTH_AMERICA_TILES_Z1 = {"rows": [1], "cols": [0, 1]}

_session = None


def _get_session():
    global _session
    if _session is None:
        _session = requests.Session()
        _session.headers.update({"User-Agent": "GOES-VolcanicMonitor/1.0"})
    return _session


def get_latest_timestamps(product: str, n: int = 24) -> list[str]:
    """Obtener los N timestamps más recientes para un producto.

    Args:
        product: ID del producto (e.g., 'geocolor', 'eumetsat_ash').
        n: Cantidad de timestamps a retornar (max 100).

    Returns:
        Lista de timestamps como strings (14 dígitos: YYYYMMDDHHmmss),
        ordenados de más reciente a más antiguo.
    """
    url = f"{BASE_URL}/data/json/{SATELLITE}/{SECTOR}/{product}/latest_times.json"
    try:
        resp = _get_session().get(url, timeout=TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        times = [str(t) for t in data.get("timestamps_int", [])]
        return times[:n]
    except Exception as e:
        logger.error("Error obteniendo timestamps para %s: %s", product, e)
        return []


def ts_to_parts(ts: str) -> tuple[str, str, str]:
    """Convertir timestamp 14-dígitos a (YYYY, MM, DD)."""
    return ts[:4], ts[4:6], ts[6:8]


def fetch_tile(product: str, ts: str, zoom: int, row: int, col: int) -> np.ndarray | None:
    """Descargar un tile individual.

    Returns:
        Array numpy (TILE_SIZE, TILE_SIZE, 3) uint8, o None si falla.
    """
    yyyy, mm, dd = ts_to_parts(ts)
    url = (
        f"{BASE_URL}/data/imagery/{yyyy}/{mm}/{dd}"
        f"/{SATELLITE}---{SECTOR}/{product}/{ts}"
        f"/{zoom:02d}/{row:03d}_{col:03d}.png"
    )
    try:
        resp = _get_session().get(url, timeout=TIMEOUT)
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        img = Image.open(io.BytesIO(resp.content)).convert("RGB")
        return np.array(img)
    except Exception as e:
        logger.warning("Tile %d_%d zoom%d ts=%s: %s", row, col, zoom, ts, e)
        return None


def fetch_stitched_frame(
    product: str,
    ts: str,
    zoom: int = 2,
    tile_rows: list[int] | None = None,
    tile_cols: list[int] | None = None,
) -> np.ndarray | None:
    """Descargar y unir tiles en una imagen compuesta.

    Args:
        product: ID del producto.
        ts: Timestamp (14 dígitos).
        zoom: Nivel de zoom (0-4).
        tile_rows: Lista de filas de tiles a incluir.
        tile_cols: Lista de columnas de tiles a incluir.

    Returns:
        Array numpy (H, W, 3) uint8 o None si fallan todos los tiles.
    """
    if tile_rows is None:
        tile_rows = CHILE_TILES_Z2["rows"]
    if tile_cols is None:
        tile_cols = CHILE_TILES_Z2["cols"]

    n_rows = len(tile_rows)
    n_cols = len(tile_cols)
    h = n_rows * TILE_SIZE
    w = n_cols * TILE_SIZE
    canvas = np.zeros((h, w, 3), dtype=np.uint8)

    # Descargar tiles en paralelo
    coords = [(r, c) for r in tile_rows for c in tile_cols]
    tiles: dict[tuple, np.ndarray] = {}

    with ThreadPoolExecutor(max_workers=8) as ex:
        futures = {
            ex.submit(fetch_tile, product, ts, zoom, r, c): (r, c)
            for r, c in coords
        }
        for fut in as_completed(futures):
            r, c = futures[fut]
            arr = fut.result()
            if arr is not None:
                tiles[(r, c)] = arr

    if not tiles:
        return None

    # Ubicar tiles en el canvas
    for i, r in enumerate(tile_rows):
        for j, c in enumerate(tile_cols):
            if (r, c) in tiles:
                y0 = i * TILE_SIZE
                x0 = j * TILE_SIZE
                canvas[y0:y0 + TILE_SIZE, x0:x0 + TILE_SIZE] = tiles[(r, c)]

    return canvas


def fetch_animation_frames(
    product: str,
    n_frames: int = 12,
    zoom: int = 2,
    tile_rows: list[int] | None = None,
    tile_cols: list[int] | None = None,
) -> list[dict]:
    """Descargar N frames para animación.

    Args:
        product: ID del producto.
        n_frames: Número de frames (12 = 2 horas).
        zoom: Nivel de zoom.
        tile_rows / tile_cols: Tiles a incluir.

    Returns:
        Lista de dicts con 'ts', 'label', 'image' (numpy array).
        Ordenados de más antiguo a más reciente (orden correcto para animación).
    """
    if tile_rows is None:
        tile_rows = CHILE_TILES_Z2["rows"]
    if tile_cols is None:
        tile_cols = CHILE_TILES_Z2["cols"]

    timestamps = get_latest_timestamps(product, n=n_frames)
    if not timestamps:
        return []

    # Descargar frames más recientes (timestamps[0] es el más nuevo)
    frames = []
    for ts in timestamps:
        img = fetch_stitched_frame(product, ts, zoom, tile_rows, tile_cols)
        if img is not None:
            yyyy, mm, dd = ts_to_parts(ts)
            hh, mi = ts[8:10], ts[10:12]
            frames.append({
                "ts": ts,
                "label": f"{yyyy}-{mm}-{dd} {hh}:{mi} UTC",
                "image": img,
            })

    # Invertir: del más antiguo al más reciente para animación correcta
    return list(reversed(frames))


# ── Bounds geográficas aproximadas del área cubierta ─────────────────────
# GOES-19 full disk zoom 2, tiles (2,1)+(2,2)+(3,1)+(3,2)
# Estos valores aproximan el área cubierta por los tiles de Chile
CHILE_TILE_BOUNDS = {
    "lat_min": -60.0,
    "lat_max": -10.0,
    "lon_min": -85.0,
    "lon_max": -50.0,
}
