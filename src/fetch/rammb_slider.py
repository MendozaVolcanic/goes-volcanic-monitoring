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


def reproject_to_latlon(
    img: np.ndarray,
    col_start: int,
    row_start: int,
    out_bounds: dict | None = None,
    out_size: tuple[int, int] | None = None,
    sat_lon: float = -75.2,
    zoom: int = 2,
) -> np.ndarray:
    """Reprojectar imagen de tiles RAMMB (proyección ABI geoestacionaria)
    a una grilla lat/lon regular usando pyproj + scipy.

    El mapa geoestacionario tiene distorsión no-lineal fuerte en el eje y
    (el error en latitud llega a 23° con bounds afines). Esta función
    corrige eso remapeando cada pixel de salida a su pixel fuente correcto.

    Args:
        img:       Imagen de tiles (H, W, 3) uint8 en proyección GOES ABI.
        col_start: Columna inicial de los tiles en la imagen full-disk zoom-2.
        row_start: Fila inicial de los tiles en la imagen full-disk zoom-2.
        out_bounds: Bounds geográficos de salida {lat_min, lat_max, lon_min, lon_max}.
                    Default: CHILE_REPROJECTED_BOUNDS.
        out_size:  (height, width) de la imagen de salida.
                    Default: REPROJECT_SIZE.
        sat_lon:   Longitud del satélite en grados (GOES-19 = -75.2).
        zoom:      Nivel de zoom RAMMB (2 para Chile).

    Returns:
        Array (out_h, out_w, 3) uint8 correctamente georeferenciado.
    """
    try:
        from pyproj import Proj
        from scipy.ndimage import map_coordinates
    except ImportError as e:
        logger.warning("reproject_to_latlon requiere pyproj y scipy: %s", e)
        return img

    if out_bounds is None:
        out_bounds = CHILE_REPROJECTED_BOUNDS
    if out_size is None:
        out_size = REPROJECT_SIZE

    # Parámetros ABI para el nivel de zoom
    n_tiles = 2 ** zoom
    cfac_z = 10762.0 / n_tiles    # scan angles por radián (columnas)
    lfac_z = 10762.0 / n_tiles    # scan angles por radián (filas)
    center  = 5423.0 / n_tiles    # pixel central (0-indexado)
    h_m     = 35786023.0          # altura orbital sobre superficie (m)

    out_h, out_w = out_size
    lat_max = out_bounds["lat_max"]
    lat_min = out_bounds["lat_min"]
    lon_min = out_bounds["lon_min"]
    lon_max = out_bounds["lon_max"]

    # ── Grilla de salida en lat/lon ──────────────────────────────────────
    # lat decreciente (N→S), lon creciente (W→E)
    lats_out = np.linspace(lat_max, lat_min, out_h)
    lons_out = np.linspace(lon_min, lon_max, out_w)
    LON, LAT = np.meshgrid(lons_out, lats_out)

    # ── lat/lon → metros en proyección GEOS ─────────────────────────────
    p = Proj(proj="geos", lon_0=sat_lon, h=h_m, ellps="GRS80", sweep="x")
    x_m_flat, y_m_flat = p(LON.ravel(), LAT.ravel())
    x_m = np.asarray(x_m_flat, dtype=np.float64)
    y_m = np.asarray(y_m_flat, dtype=np.float64)

    # ── metros → scan angles → pixel en imagen full-disk ────────────────
    x_rad = x_m / h_m
    y_rad = y_m / h_m
    pix_col_full = center + x_rad * cfac_z
    pix_row_full = center - y_rad * lfac_z   # y positivo = Norte = filas pequeñas

    # ── pixel full-disk → pixel en imagen de tiles (coords locales) ──────
    src_col = pix_col_full - col_start
    src_row = pix_row_full - row_start

    img_h, img_w = img.shape[:2]

    # Puntos fuera del disco terrestre (pyproj devuelve ~1e30) o del tile
    valid = (
        np.isfinite(x_m) & np.isfinite(y_m) &
        (np.abs(x_m) < 1e10) &          # dentro del disco terrestre
        (src_col >= 0) & (src_col < img_w) &
        (src_row >= 0) & (src_row < img_h)
    )
    invalid = ~valid

    # ── Interpolar cada canal ────────────────────────────────────────────
    coords = np.array([src_row, src_col])   # shape (2, N)
    out_img = np.zeros((out_h, out_w, 3), dtype=np.uint8)

    for c in range(3):
        vals = map_coordinates(
            img[:, :, c].astype(np.float32),
            coords,
            order=1,
            mode="constant",
            cval=0.0,
            prefilter=False,
        )
        ch = vals.reshape(out_h, out_w)
        ch[invalid.reshape(out_h, out_w)] = 0
        out_img[:, :, c] = np.clip(ch, 0, 255).astype(np.uint8)

    return out_img


def fetch_stitched_frame(
    product: str,
    ts: str,
    zoom: int = 2,
    tile_rows: list[int] | None = None,
    tile_cols: list[int] | None = None,
    reproject: bool = False,
) -> np.ndarray | None:
    """Descargar y unir tiles en una imagen compuesta.

    Args:
        product: ID del producto.
        ts: Timestamp (14 dígitos).
        zoom: Nivel de zoom (0-4).
        tile_rows: Lista de filas de tiles a incluir.
        tile_cols: Lista de columnas de tiles a incluir.
        reproject: Si True, reprojectar de geoestacionaria a lat/lon regular.

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

    if reproject:
        col_start = min(tile_cols) * TILE_SIZE
        row_start = min(tile_rows) * TILE_SIZE
        canvas = reproject_to_latlon(canvas, col_start=col_start, row_start=row_start)

    return canvas


def fetch_animation_frames(
    product: str,
    n_frames: int = 12,
    zoom: int = 2,
    tile_rows: list[int] | None = None,
    tile_cols: list[int] | None = None,
    reproject: bool = False,
) -> list[dict]:
    """Descargar N frames para animación.

    Args:
        product: ID del producto.
        n_frames: Número de frames (12 = 2 horas).
        zoom: Nivel de zoom.
        tile_rows / tile_cols: Tiles a incluir.
        reproject: Si True, reprojectar cada frame a lat/lon regular.

    Returns:
        Lista de dicts con 'ts', 'label', 'image' (numpy array), 'bounds'.
        Ordenados de más antiguo a más reciente (orden correcto para animación).
    """
    if tile_rows is None:
        tile_rows = CHILE_TILES_Z2["rows"]
    if tile_cols is None:
        tile_cols = CHILE_TILES_Z2["cols"]

    timestamps = get_latest_timestamps(product, n=n_frames)
    if not timestamps:
        return []

    bounds = CHILE_REPROJECTED_BOUNDS if reproject else CHILE_TILE_BOUNDS

    # Descargar frames más recientes (timestamps[0] es el más nuevo)
    frames = []
    for ts in timestamps:
        img = fetch_stitched_frame(product, ts, zoom, tile_rows, tile_cols, reproject=reproject)
        if img is not None:
            yyyy, mm, dd = ts_to_parts(ts)
            hh, mi = ts[8:10], ts[10:12]
            label_suffix = " [georef]" if reproject else ""
            frames.append({
                "ts": ts,
                "label": f"{yyyy}-{mm}-{dd} {hh}:{mi} UTC{label_suffix}",
                "image": img,
                "bounds": bounds,
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

# Bounds geográficos reales para la vista Chile reprojectada
CHILE_REPROJECTED_BOUNDS = {
    "lat_min": -57.0,
    "lat_max": -14.0,
    "lon_min": -82.0,
    "lon_max": -62.0,
}

# Tamaño de salida de la imagen reprojectada (height, width)
REPROJECT_SIZE = (800, 380)
