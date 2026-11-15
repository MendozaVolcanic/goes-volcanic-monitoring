"""Fetch historico de tiles RAMMB para fechas fuera del archive estandar.

RAMMB-CIRA mantiene tiles PNG en su CDN mucho mas atras que la API
`latest_times.json` (que corta en 100 scans, unas 16 h). Medido el
15-11-2026: tramo continuo desde 01-09-2026 y dias sueltos hasta jul-2025,
algunos listados pero ya sin tiles (ver "Listado por fecha" mas abajo). Estos
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

# Constante fisica canonical desde src/config (con try/except fallback,
# mismo patron que MOSAICO_RADIUS_DEG en dashboard/views/).
try:
    from src.config import GOES19_SAT_LON as _SAT_LON_DEFAULT
except Exception:
    _SAT_LON_DEFAULT = -75.0

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
                                    sat_lon: float = _SAT_LON_DEFAULT
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


# ── Listado por fecha (vista Replay, nov-2026) ───────────────────────
#
# Por que: `latest_times.json` entrega como maximo los 100 scans mas nuevos
# (unas 16 h), asi que no sirve para revisar un dia elegido. RAMMB publica por
# producto dos JSON que si lo permiten:
#   - available_dates.json      -> {"dates_int": [20261115, ...]}
#   - <YYYYMMDD>_by_hour.json   -> {"timestamps_int": {"HH": [ts, ...]}}
# Medido el 15-11-2026 (jma_so2, eumetsat_ash, geocolor dan la misma lista):
# la lista trae un tramo continuo reciente (desde 01-09-2026) y dias sueltos
# hacia atras hasta jul-2025, y ALGUNOS de esos dias sueltos ya no tienen
# imagenes (todos los tiles dan 404). Por eso:
#   1. "no esta en la lista" (404 del JSON) se dice como tal, no como calma;
#   2. un error de red se distingue de un 404: no dice nada del dia;
#   3. un dia listado se confirma bajando un tile (`tile_available`).

_JSON_BASE = f"{BASE_URL}/data/json/{SATELLITE}/{SECTOR}"

# Estados de un listado. "parcial" = una de las dos fechas UTC del dia local
# no respondio: se muestra lo que llego, avisando que puede faltar un tramo.
ESTADO_OK = "ok"
ESTADO_NO_CONSERVADO = "no_conservado"
ESTADO_SIN_RESPUESTA = "sin_respuesta"
ESTADO_PARCIAL = "parcial"


def parse_available_dates(payload: dict) -> list:
    """`available_dates.json` -> lista de `date`, de la mas vieja a la mas nueva."""
    from datetime import date as _date
    out = []
    for d in payload.get("dates_int", []):
        d = int(d)
        out.append(_date(d // 10000, d // 100 % 100, d % 100))
    return sorted(out)


def parse_by_hour(payload: dict) -> list[str]:
    """`<fecha>_by_hour.json` -> timestamps de 14 digitos en orden cronologico.

    RAMMB agrupa por hora y deja lo mas nuevo primero dentro de cada hora;
    aca se aplana y se ordena, porque la vista recorre de izquierda a derecha.
    """
    horas = payload.get("timestamps_int", {}) or {}
    return sorted(str(t) for lista in horas.values() for t in lista)


def fetch_available_dates(product: str) -> list | None:
    """Dias que RAMMB lista para el producto. None = RAMMB no respondio."""
    url = f"{_JSON_BASE}/{product}/available_dates.json?_={int(time.time())}"
    try:
        r = _get_session().get(url, timeout=15,
                               headers={"Cache-Control": "no-cache"})
        r.raise_for_status()
        return parse_available_dates(r.json())
    except Exception as e:
        logger.warning("available_dates %s: %s", product, e)
        return None


def fetch_day_timestamps(product: str, utc_day) -> tuple[list[str], str]:
    """Scans de un dia UTC. Devuelve (timestamps, estado).

    estado: "ok", "no_conservado" (RAMMB respondio 404: ese dia no esta) o
    "sin_respuesta" (red caida o respuesta rara: no se sabe nada del dia).
    """
    url = f"{_JSON_BASE}/{product}/{utc_day:%Y%m%d}_by_hour.json"
    try:
        r = _get_session().get(url, timeout=15)
        if r.status_code == 404:
            return [], ESTADO_NO_CONSERVADO
        r.raise_for_status()
        return parse_by_hour(r.json()), ESTADO_OK
    except Exception as e:
        logger.warning("by_hour %s %s: %s", product, utc_day, e)
        return [], ESTADO_SIN_RESPUESTA


def local_window_utc(local_day, h_ini: int, h_fin: int, tz):
    """[inicio, fin) en UTC de la ventana local h_ini..h_fin (h_fin <= 24)."""
    from datetime import datetime as _dt, timezone as _tz
    base = _dt(local_day.year, local_day.month, local_day.day, tzinfo=tz)
    # Sumar horas en hora local "de pared" y recien despues pasar a UTC: asi
    # el dia del cambio de horario sigue cortando en la medianoche de Chile.
    ini = (base + timedelta(hours=h_ini)).astimezone(_tz.utc)
    fin_local = base + timedelta(hours=h_fin)
    if h_fin >= 24:
        sig = local_day + timedelta(days=1)
        fin_local = _dt(sig.year, sig.month, sig.day, tzinfo=tz)
    return ini, fin_local.astimezone(_tz.utc)


def utc_dates_for_local_day(local_day, tz) -> list:
    """Fechas UTC que cubre un dia local completo (una o dos)."""
    ini, fin = local_window_utc(local_day, 0, 24, tz)
    ultimo = fin - timedelta(seconds=1)
    fechas = [ini.date()]
    if ultimo.date() != ini.date():
        fechas.append(ultimo.date())
    return fechas


def timestamps_in_local_window(timestamps: list[str], local_day,
                               h_ini: int, h_fin: int, tz) -> list[str]:
    """Filtra timestamps UTC a la ventana local [h_ini, h_fin) del dia."""
    from datetime import datetime as _dt, timezone as _tz
    ini, fin = local_window_utc(local_day, h_ini, h_fin, tz)
    out = []
    for ts in timestamps:
        t = _dt.strptime(ts, "%Y%m%d%H%M%S").replace(tzinfo=_tz.utc)
        if ini <= t < fin:
            out.append(ts)
    return sorted(out)


def list_local_day(product: str, local_day, h_ini: int, h_fin: int,
                   tz) -> tuple[list[str], str]:
    """Scans de un dia LOCAL (Chile) en la ventana [h_ini, h_fin).

    Un dia local cruza dos dias UTC: se piden los dos. Nunca se completa con
    otro dia: si el pedido no existe, la lista vuelve vacia con su motivo.
    """
    todos: list[str] = []
    estados = []
    for d in utc_dates_for_local_day(local_day, tz):
        ts, est = fetch_day_timestamps(product, d)
        todos.extend(ts)
        estados.append(est)
    elegidos = timestamps_in_local_window(todos, local_day, h_ini, h_fin, tz)
    if ESTADO_SIN_RESPUESTA in estados:
        return elegidos, (ESTADO_PARCIAL if elegidos else ESTADO_SIN_RESPUESTA)
    if elegidos:
        return elegidos, ESTADO_OK
    if all(e == ESTADO_NO_CONSERVADO for e in estados):
        return [], ESTADO_NO_CONSERVADO
    # El dia existe pero no hay scans en esa ventana horaria.
    return [], ESTADO_OK


def archive_span(dates: list) -> dict | None:
    """Tramo continuo mas reciente y tramos sueltos anteriores.

    El tramo continuo es lo que se puede prometer; los sueltos son dias que
    RAMMB retuvo aparte y que pueden no tener imagenes (ver `tile_available`).
    """
    if not dates:
        return None
    ds = sorted(set(dates))
    tramos = []
    ini = prev = ds[0]
    for d in ds[1:]:
        if (d - prev).days != 1:
            tramos.append((ini, prev))
            ini = d
        prev = d
    tramos.append((ini, prev))
    desde, hasta = tramos[-1]
    return {
        "continuo_desde": desde,
        "continuo_hasta": hasta,
        "dias_continuos": (hasta - desde).days + 1,
        "sueltos": tramos[:-1],
    }


def tile_available(product: str, ts: str, bounds: dict,
                   zoom: int = 3) -> bool | None:
    """Un tile del encuadre existe para ese scan? True / False (404) / None.

    Zoom 3 porque es el maximo que RAMMB guarda para las bandas IR (Ash, SO2)
    y tambien existe para GeoColor. None = no se pudo saber (red).
    """
    rows, cols = get_tiles_for_bounds(bounds, zoom)
    r, c = rows[len(rows) // 2], cols[len(cols) // 2]
    url = (f"{BASE_URL}/data/imagery/{ts[:4]}/{ts[4:6]}/{ts[6:8]}"
           f"/{SATELLITE}---{SECTOR}/{product}/{ts}/{zoom:02d}"
           f"/{r:03d}_{c:03d}.png")
    try:
        resp = _get_session().get(url, timeout=15)
        if resp.status_code == 404:
            return False
        if resp.status_code == 200 and len(resp.content) > 500:
            return True
        return None
    except Exception as e:
        logger.warning("tile_available %s %s: %s", product, ts, e)
        return None
