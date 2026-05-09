"""Fetch historico de tiles RAMMB para fechas fuera del archive estandar.

RAMMB-CIRA mantiene tiles PNG en su CDN para ~360 dias hacia atras (mucho
mas que la API `latest_times.json` que solo da las ultimas horas). Estos
tiles son archivos estaticos accesibles directamente por URL.

Limitacion descubierta: para fechas viejas, el ZOOM 4 solo esta disponible
para `geocolor`. Los productos IR (eumetsat_ash, jma_so2, BTD) solo tienen
zoom 3 (~3.4 km/px). Para zoom 4 (~1.7 km/px) hay que procesar L1b directo.

Tambien: el offset de segundos del scan varia por dia (ej. 8-feb-2026 = 21,
otros dias = 20). Detectamos por brute-force la primera vez y cacheamos.

Uso tipico:
    seconds_offset = detect_seconds_offset("2026-02-08", "geocolor")
    timestamps = generate_timestamps("2026-02-08", "10:36", "19:00",
                                     seconds_offset)
    for ts in timestamps:
        img = fetch_historic_frame_for_bounds("geocolor", ts, bounds, zoom=4)
"""

from __future__ import annotations

import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta

import numpy as np
import requests

from src.fetch.rammb_slider import (
    BASE_URL, SATELLITE, SECTOR, _get_session,
    fetch_stitched_frame, get_tiles_for_bounds, reproject_to_latlon,
    get_tile_size,
)

logger = logging.getLogger(__name__)

# Mapeo producto -> zoom maximo disponible para fechas archivo (feb 2026 +).
# Validado empiricamente. geocolor tiene zoom 4, IR products solo zoom 3.
HISTORIC_MAX_ZOOM = {
    "geocolor": 4,
    "eumetsat_ash": 3,
    "jma_so2": 3,
    "split_window_difference_10_3-12_3": 3,
}


def _date_to_path_parts(date_str: str) -> tuple[str, str, str]:
    """'2026-02-08' -> ('2026', '02', '08')."""
    yyyy, mm, dd = date_str.split("-")
    return yyyy, mm, dd


def detect_seconds_offset(date_str: str, product: str = "geocolor",
                          probe_hour: int = 12) -> int | None:
    """Detectar el offset de segundos del scan para una fecha dada.

    GOES-19 produce un Full Disk cada 10 min, pero el offset de segundos
    dentro del minuto varia por dia (operacionalmente). Esta funcion prueba
    los 60 segundos posibles para HH:00:SS hasta encontrar el correcto.

    Args:
        date_str: fecha en formato 'YYYY-MM-DD'.
        product: producto a probar (default geocolor por ser el mas confiable).
        probe_hour: hora UTC a usar para la prueba (default 12 = mediodia
                    cuando todos los productos suelen estar disponibles).

    Returns:
        offset 0-59 si encontrado, None si la fecha no esta en archive.
    """
    yyyy, mm, dd = _date_to_path_parts(date_str)
    # Tile arbitrario en zona Sudamerica (col=9 row=7 zoom 4 cubre Chile)
    # Para no depender de zoom 4, usamos zoom 3 que esta para todos los products.
    zoom_test = 3
    row, col = 3, 4  # cubre sur Sudamerica en zoom 3
    sess = _get_session()
    for ss in range(60):
        ts = f"{yyyy}{mm}{dd}{probe_hour:02d}00{ss:02d}"
        url = (f"{BASE_URL}/data/imagery/{yyyy}/{mm}/{dd}/{SATELLITE}---{SECTOR}"
               f"/{product}/{ts}/{zoom_test:02d}/{row:03d}_{col:03d}.png")
        try:
            r = sess.get(url, timeout=5)
            if r.status_code == 200 and len(r.content) > 1000:
                logger.info("Offset detectado para %s: %02d", date_str, ss)
                return ss
        except Exception:
            continue
    return None


def generate_timestamps(date_str: str, start_hhmm: str, end_hhmm: str,
                        seconds_offset: int,
                        cadence_min: int = 10) -> list[str]:
    """Generar lista de timestamps RAMMB para un rango horario.

    Args:
        date_str: 'YYYY-MM-DD'.
        start_hhmm: 'HH:MM' inclusive.
        end_hhmm:   'HH:MM' inclusive (puede caer fuera del ultimo scan).
        seconds_offset: detectado con detect_seconds_offset().
        cadence_min: cadencia GOES Full Disk (10 min).

    Returns:
        Lista de timestamps str 'YYYYMMDDHHmmss'.
    """
    yyyy, mm, dd = _date_to_path_parts(date_str)
    start_h, start_m = map(int, start_hhmm.split(":"))
    end_h, end_m = map(int, end_hhmm.split(":"))

    # Redondear start hacia ARRIBA al multiplo de cadence_min mas cercano,
    # end hacia ABAJO. Asi el rango contiene scans existentes.
    base = datetime(int(yyyy), int(mm), int(dd))
    start_dt = base + timedelta(hours=start_h, minutes=start_m)
    end_dt = base + timedelta(hours=end_h, minutes=end_m)

    # Primer scan >= start
    first_min = ((start_m + cadence_min - 1) // cadence_min) * cadence_min
    if first_min == 60:
        cur = base + timedelta(hours=start_h + 1)
    else:
        cur = base + timedelta(hours=start_h, minutes=first_min)

    out = []
    while cur <= end_dt:
        ts = cur.strftime("%Y%m%d%H%M") + f"{seconds_offset:02d}"
        out.append(ts)
        cur += timedelta(minutes=cadence_min)
    return out


def fetch_historic_tile(product: str, ts: str, zoom: int,
                        row: int, col: int) -> np.ndarray | None:
    """Bajar 1 tile RAMMB historico. Devuelve None si 404."""
    yyyy, mm, dd = ts[:4], ts[4:6], ts[6:8]
    url = (f"{BASE_URL}/data/imagery/{yyyy}/{mm}/{dd}/{SATELLITE}---{SECTOR}"
           f"/{product}/{ts}/{zoom:02d}/{row:03d}_{col:03d}.png")
    try:
        r = _get_session().get(url, timeout=15)
        if r.status_code != 200 or len(r.content) < 500:
            return None
        from PIL import Image
        import io
        img = Image.open(io.BytesIO(r.content)).convert("RGB")
        return np.array(img)
    except Exception as e:
        logger.warning("tile %s %s z%d r%d c%d: %s", product, ts, zoom, row, col, e)
        return None


def fetch_historic_stitched(product: str, ts: str, zoom: int,
                            tile_rows: list[int],
                            tile_cols: list[int]) -> np.ndarray | None:
    """Bajar y unir multiples tiles historicos en una sola imagen."""
    n_rows = len(tile_rows)
    n_cols = len(tile_cols)
    coords = [(r, c) for r in tile_rows for c in tile_cols]
    tiles: dict = {}
    with ThreadPoolExecutor(max_workers=8) as ex:
        futures = {ex.submit(fetch_historic_tile, product, ts, zoom, r, c): (r, c)
                   for r, c in coords}
        for fut in as_completed(futures):
            r, c = futures[fut]
            arr = fut.result()
            if arr is not None:
                tiles[(r, c)] = arr
    if not tiles:
        return None
    sample = next(iter(tiles.values()))
    tile_sz = int(sample.shape[0])
    canvas = np.zeros((n_rows * tile_sz, n_cols * tile_sz, 3), dtype=np.uint8)
    for i, r in enumerate(tile_rows):
        for j, c in enumerate(tile_cols):
            if (r, c) in tiles:
                canvas[i * tile_sz:(i + 1) * tile_sz,
                       j * tile_sz:(j + 1) * tile_sz] = tiles[(r, c)]
    return canvas


def fetch_historic_frame_for_bounds(product: str, ts: str, bounds: dict,
                                    zoom: int = 3,
                                    sat_lon: float = -75.0
                                    ) -> np.ndarray | None:
    """Equivalente a `fetch_frame_for_bounds` pero para tiles historicos.

    Calcula tiles necesarios + stitchea + reproyecta a lat/lon regular
    en `bounds`. Devuelve numpy (H, W, 3) uint8 o None.
    """
    tile_rows, tile_cols = get_tiles_for_bounds(bounds, zoom, sat_lon)
    img = fetch_historic_stitched(product, ts, zoom, tile_rows, tile_cols)
    if img is None:
        return None
    tile_sz = int(img.shape[0] // len(tile_rows))
    col_start = min(tile_cols) * tile_sz
    row_start = min(tile_rows) * tile_sz
    return reproject_to_latlon(
        img, col_start=col_start, row_start=row_start,
        out_bounds=bounds, sat_lon=sat_lon, zoom=zoom, tile_sz=tile_sz,
    )
