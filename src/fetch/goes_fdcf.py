"""Cliente para producto NOAA L2 FDCF (Fire/Hot spot Characterization, Full Disk).

FDCF es producto pre-procesado por NOAA del Advanced Baseline Imager (ABI) que
identifica píxeles calientes (incendios + actividad volcánica) usando algoritmo
multi-banda (3.9 µm, 11 µm, 12 µm) con calibración dinámica.

Variables clave del NetCDF:
- ``Mask``  (5424×5424 uint8): clasificación de píxel
    - 10/11 = fuego de buena calidad, alta confianza
    - 12/13 = fuego con saturación
    - 14/15 = fuego de baja confianza
    - 30+   = nube / sin datos / fuera del disco
- ``Power`` (float32): potencia radiativa del fuego en MW
- ``Temp``  (float32): temperatura de brillo del píxel caliente, K
- ``Area``  (float32): área de superficie afectada, km² (sub-pixel)
- ``DQF``   (uint8): flag de calidad del dato

Cadencia FDCF Full Disk: cada 10 min (sigue al scan de GOES-19).
Latencia: ~6-8 min después del fin del scan (más que RAMMB).

Para volcanes chilenos los hotspots típicos son **muy pocos por scan** (0-3
en todo Chile). El algoritmo FDCF está optimizado para incendios forestales —
algunas erupciones efusivas como Villarrica las detecta bien (cuando hay
lava expuesta), pero erupciones explosivas con cenizas frías NO disparan
hotspots térmicos.

Cross-check con VRP (MODIS/VIIRS) sigue siendo necesario para validar.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional

import numpy as np

from src.fetch.granule_select import nearest_granule_key, get_s3 as _get_s3

# Constantes fisicas canonical desde src/config (con try/except fallback,
# mismo patron que MOSAICO_RADIUS_DEG en dashboard/views/).
try:
    from src.config import GOES19_SAT_LON as _SAT_LON_DEFAULT
    from src.config import GOES19_PERSPECTIVE_POINT_HEIGHT as _H_DEFAULT
except Exception:
    _SAT_LON_DEFAULT = -75.0
    _H_DEFAULT = 35786023.0

logger = logging.getLogger(__name__)

# Cuál es el archivo S3 para FDCF Full Disk
S3_BUCKET = "noaa-goes19"
S3_PRODUCT = "ABI-L2-FDCF"

# Categorías de Mask que consideramos "hotspot real"
# (10-15 son detecciones; 30+ son nube/no-fire/sin-datos)
HOTSPOT_MASK_VALUES = {10, 11, 12, 13, 14, 15}

# Subset de mask values con alta confianza operacional.
# (ABI L2 Fires ReadMe NOAA — categorías 10/11 = processed,
#  30/31 = processed temporally filtered). Las temporally filtered ya
# pasaron un test de persistencia en scans previos, por lo que son al
# menos tan confiables como las processed simples — incluirlas evita
# perder hotspots reales que se reportan en categoria 30/31.
HIGH_CONF_MASK = {10, 11, 30, 31}


@dataclass
class HotSpot:
    """Un punto detectado como caliente en un scan FDCF."""
    lat: float
    lon: float
    frp_mw: float            # Fire Radiative Power, MW
    temp_k: float            # Temperatura de brillo, K
    area_km2: float          # Sub-pixel area
    mask: int                # categoria FDCF
    confidence: str          # 'high' | 'medium' | 'low' | 'saturated'

    def to_dict(self) -> dict:
        return {
            "lat": self.lat, "lon": self.lon,
            "frp_mw": self.frp_mw, "temp_k": self.temp_k,
            "area_km2": self.area_km2,
            "mask": self.mask, "confidence": self.confidence,
        }


def _parse_scan_time(s3_path: str) -> Optional[datetime]:
    """Extraer datetime UTC del nombre del archivo NOAA.

    Nombre tipico:
        OR_ABI-L2-FDCF-M6_G19_s20261151200216_e20261151209524_c20261151210037.nc
                                 ^^^^^^^^^^^^^^^
                                 s = start time
                                 yyyy=2026 doy=115 hh=12 mm=00 ss=21
    """
    try:
        name = s3_path.split("/")[-1]
        token = [t for t in name.split("_") if t.startswith("s") and len(t) >= 14][0]
        yyyy = int(token[1:5])
        doy  = int(token[5:8])
        hh   = int(token[8:10])
        mm   = int(token[10:12])
        ss   = int(token[12:14])
        # 1 enero del año + (doy - 1) dias da el dia correcto.
        # Ej: 2026 doy=115 -> 25 abril 2026
        base = datetime(yyyy, 1, 1, hh, mm, ss, tzinfo=timezone.utc)
        return base + timedelta(days=doy - 1)
    except Exception as e:
        logger.warning("No pude parsear timestamp de %s: %s", s3_path, e)
        return None


def _confidence_from_mask(mask: int) -> str:
    if mask in (10, 11):
        return "high"
    if mask in (12, 13):
        return "saturated"
    if mask in (14, 15):
        return "low"
    return "unknown"


def _list_recent_files(s3, hours_back: int = 1) -> tuple[list[str], int]:
    """Listar archivos FDCF recientes (ultimas N horas).

    Devuelve ``(keys, n_fallos)``. Qué es ``n_fallos`` y por qué existe: una
    carpeta horaria que **no existe** (FileNotFoundError) y una que **no se
    pudo consultar** (timeout/red/permiso) producen las dos una lista vacía,
    pero significan cosas opuestas — "NOAA todavía no publicó" contra "S3 no
    contestó". El llamador necesita el conteo para loguear con el nivel
    correcto; el contrato de salida no cambia (ver ``fetch_latest_hotspots``).
    """
    now = datetime.now(timezone.utc)
    keys: list[str] = []
    n_fallos = 0
    for h in range(hours_back + 1):
        t = now - timedelta(hours=h)
        prefix = (
            f"{S3_BUCKET}/{S3_PRODUCT}/"
            f"{t.year}/{t.timetuple().tm_yday:03d}/{t.hour:02d}/"
        )
        try:
            keys.extend(s3.ls(prefix))
        except FileNotFoundError:
            continue
        except Exception as e:
            n_fallos += 1
            logger.warning("FDCF: no pude listar %s: %s", prefix, e)
    # Ordenar por nombre (los archivos NOAA llevan timestamp en el nombre)
    keys.sort(reverse=True)
    return keys, n_fallos


def _abi_to_latlon(
    x_rad: np.ndarray, y_rad: np.ndarray, sat_lon: float = _SAT_LON_DEFAULT,
) -> tuple[np.ndarray, np.ndarray]:
    """Convertir coords ABI fixed grid (radianes) a lat/lon.

    Las coords x/y del ABI son angulos visto desde el satelite (sweep mode 'x').
    Usamos pyproj GEOS para reproyectar.
    """
    try:
        from pyproj import Proj
    except ImportError:
        logger.error("pyproj requerido para reproyectar FDCF")
        return np.zeros_like(x_rad), np.zeros_like(y_rad)

    h = _H_DEFAULT
    p = Proj(proj="geos", lon_0=sat_lon, h=h, ellps="GRS80", sweep="x")

    # x/y radianes → metros
    x_m = x_rad * h
    y_m = y_rad * h
    lon, lat = p(x_m, y_m, inverse=True)
    return lat, lon


def xy_index_range(
    x_rad: np.ndarray, y_rad: np.ndarray, sat_lon: float,
    bbox: dict, margin_rad: float = 0.003,
) -> Optional[tuple[int, int, int, int]]:
    """Índices ``(c0, c1, r0, r1)`` del sub-bloque ABI que cubre ``bbox``.

    Por qué: el grid fijo del ABI es 5424×5424, pero un bbox de un volcán son
    unas decenas de píxeles. Proyectando las esquinas del bbox a coords
    fixed-grid (radianes) se obtiene el rango de columnas (x) y filas (y) que lo
    contienen, con un margen generoso (0.003 rad ≈ 50 px de 2 km) para absorber
    la curvatura del bbox lat/lon en la grilla geos.

    Devuelve None si el bbox cae fuera del disco visible (el caller lee full).
    """
    try:
        from pyproj import Proj
    except ImportError:
        logger.error("pyproj requerido para recorte de región")
        return None

    p = Proj(proj="geos", lon_0=sat_lon, h=_H_DEFAULT, ellps="GRS80", sweep="x")
    lon_grid, lat_grid = np.meshgrid(
        np.linspace(bbox["lon_min"], bbox["lon_max"], 6),
        np.linspace(bbox["lat_min"], bbox["lat_max"], 6),
    )
    x_m, y_m = p(lon_grid.ravel(), lat_grid.ravel())
    x_r = np.asarray(x_m) / _H_DEFAULT
    y_r = np.asarray(y_m) / _H_DEFAULT
    finite = np.isfinite(x_r) & np.isfinite(y_r)
    if not finite.any():
        return None
    x_r, y_r = x_r[finite], y_r[finite]
    xmin, xmax = x_r.min() - margin_rad, x_r.max() + margin_rad
    ymin, ymax = y_r.min() - margin_rad, y_r.max() + margin_rad

    c_idx = np.where((x_rad >= xmin) & (x_rad <= xmax))[0]
    r_idx = np.where((y_rad >= ymin) & (y_rad <= ymax))[0]
    if c_idx.size == 0 or r_idx.size == 0:
        return None
    return int(c_idx[0]), int(c_idx[-1]), int(r_idx[0]), int(r_idx[-1])


def _read_block(ds, name: str, rng: Optional[tuple]) -> np.ndarray:
    """Materializar una variable 2D del FDCF, recortada al sub-bloque si lo hay.

    Punto único donde se pasa de lazy a numpy: con ``rng`` se evita traer los
    5424² valores. (Los tests espían esta función para verificar el recorte.)
    """
    if rng is None:
        return ds[name].values
    c0, c1, r0, r1 = rng
    return ds[name][r0:r1 + 1, c0:c1 + 1].values


def extract_hotspots(
    ds,
    bounds: Optional[dict] = None,
    high_conf_only: bool = False,
    allow_slice: bool = True,
) -> list[HotSpot]:
    """Extraer los hotspots de un dataset FDCF ya abierto, filtrados por bbox.

    Camino ÚNICO compartido por los tres lectores (NRT, histórico y timeline):
    antes cada uno repetía este bloque y sólo la timeline recortaba. Con
    ``bounds`` se lee sólo el sub-bloque que cubre el bbox (~15× más rápido y
    sin el pico de RAM del full-disk, que importa en el Space de HF).

    Args:
        ds:              Dataset FDCF abierto (Mask/Power/Temp/Area + x/y).
        bounds:          bbox lat/lon; None = disco entero, sin filtrar.
        high_conf_only:  sólo Mask ∈ HIGH_CONF_MASK.
        allow_slice:     False fuerza el camino full-disk (para comparar).

    Returns:
        lista de HotSpot ordenada por FRP descendente ([] si no hay).
    """
    x_rad = ds["x"].values
    y_rad = ds["y"].values
    sat_lon = float(
        ds["goes_imager_projection"].attrs.get(
            "longitude_of_projection_origin", _SAT_LON_DEFAULT
        )
    )

    rng = None
    if bounds is not None and allow_slice:
        rng = xy_index_range(x_rad, y_rad, sat_lon, bounds)

    mask = _read_block(ds, "Mask", rng)
    power = _read_block(ds, "Power", rng)
    if rng is None:
        xs, ys = x_rad, y_rad
    else:
        c0, c1, r0, r1 = rng
        xs, ys = x_rad[c0:c1 + 1], y_rad[r0:r1 + 1]

    valid_mask_set = HIGH_CONF_MASK if high_conf_only else HOTSPOT_MASK_VALUES
    hot_idx = np.isin(mask, list(valid_mask_set)) & np.isfinite(power)
    if not hot_idx.any():
        return []

    rows, cols = np.where(hot_idx)
    # x_rad indexa columnas, y_rad filas: se proyectan SOLO los índices
    # calientes (mucho más barato que reconstruir la grilla completa).
    lats, lons = _abi_to_latlon(xs[cols], ys[rows], sat_lon=sat_lon)

    if bounds is not None:
        keep = (
            (lats >= bounds["lat_min"]) & (lats <= bounds["lat_max"]) &
            (lons >= bounds["lon_min"]) & (lons <= bounds["lon_max"])
        )
        if not keep.any():
            return []
        rows, cols = rows[keep], cols[keep]
        lats, lons = lats[keep], lons[keep]

    # Temp/Area sólo se materializan si HAY hotspots que describir.
    temp = _read_block(ds, "Temp", rng)
    area = _read_block(ds, "Area", rng)

    hotspots = []
    for i in range(len(rows)):
        r, c = int(rows[i]), int(cols[i])
        m_v = int(mask[r, c])
        hotspots.append(HotSpot(
            lat=float(lats[i]), lon=float(lons[i]),
            frp_mw=float(power[r, c]) if np.isfinite(power[r, c]) else 0.0,
            temp_k=float(temp[r, c]) if np.isfinite(temp[r, c]) else 0.0,
            area_km2=float(area[r, c]) if np.isfinite(area[r, c]) else 0.0,
            mask=m_v, confidence=_confidence_from_mask(m_v),
        ))
    hotspots.sort(key=lambda h: h.frp_mw, reverse=True)
    return hotspots


def fetch_latest_hotspots(
    bounds: Optional[dict] = None,
    high_conf_only: bool = False,
    hours_back: int = 1,
) -> tuple[list[HotSpot], Optional[datetime]]:
    """Bajar el FDCF más reciente y devolver hotspots filtrados por bbox.

    CONTRATO DE SALIDA — leer antes de tocar un call-site (esto es un SDA):

        ``scan_dt`` es el testigo de que el dato FUE CONSULTADO.

        - ``scan_dt`` **no es None** → hubo un scan FDCF real, leído y filtrado.
          ``hotspots`` es entonces la verdad de ese scan, y ``[]`` significa
          **"NOAA miró y no detectó nada"** — es el estado normal de un volcán
          en calma y se puede presentar como tal, siempre junto a la hora del
          scan (un conteo sin hora no dice si es de hace 8 min o de ayer).
        - ``scan_dt is None`` → **NO se pudo verificar**: falta la dependencia,
          S3 no contestó, no hay gránulo publicado, el NetCDF no abrió, o el
          nombre del archivo no permitió fechar el scan. En este caso
          ``hotspots`` es SIEMPRE ``[]``, y ese cero **es ausencia de
          información, no ausencia de anomalía térmica**. Presentarlo como
          calma (KPI en verde, "0 hot spots") es el peor modo de falla posible
          en un sistema de alerta volcánica: el volcán puede estar en erupción
          y la vista mostraría lo mismo que en un día tranquilo. Los
          consumidores deben pintar "FDCF no consultable" y nunca un cero.

        Invariante, en las dos direcciones:
            ``scan_dt is None``  ⟺  ``hotspots == []`` **por falta de dato**.
        Nunca se devuelve ``(hotspots_no_vacíos, None)`` ni un ``scan_dt``
        válido en un camino de error (un timestamp válido afirmaría que el
        scan se leyó completo, que es justo lo que no pasó).

    Args:
        bounds:           dict con lat_min/lat_max/lon_min/lon_max para filtrar.
                          None = no filtra (devuelve hotspots globales).
        high_conf_only:   Si True, solo Mask ∈ HIGH_CONF_MASK. Default False
                          (incluye baja confianza y saturados, marcados aparte).
        hours_back:       Cuántas horas atrás buscar si no encuentra archivos
                          en la hora actual. Default 1.

    Returns:
        ``(hotspots, scan_dt)`` según el contrato de arriba.
    """
    # (1) Dependencias. Sin s3fs/xarray no se consultó nada: no verificable.
    try:
        import s3fs  # noqa: F401  (se usa vía _get_s3; el import valida presencia)
        import xarray as xr
    except ImportError as e:
        logger.error("FDCF NO CONSULTABLE: s3fs/xarray no disponible: %s", e)
        return [], None

    # (2) Cliente S3. Iba fuera del try y una falla de construcción (credencial,
    # botocore roto) escapaba como excepción al dashboard en vez de degradar.
    try:
        s3 = _get_s3()
    except Exception as e:
        logger.exception("FDCF NO CONSULTABLE: no pude construir el cliente S3: %s", e)
        return [], None

    # (3) Listado. Distinguimos en el LOG "S3 no contestó" de "no hay gránulo
    # publicado todavía" — para la salida ambos son igual de no verificables.
    keys, n_fallos = _list_recent_files(s3, hours_back=hours_back)
    if not keys:
        if n_fallos:
            logger.error(
                "FDCF NO CONSULTABLE: %d listado(s) de S3 fallaron en las "
                "ultimas %dh; no hay gránulo que leer", n_fallos, hours_back)
        else:
            logger.warning(
                "FDCF NO CONSULTABLE: S3 respondió pero NOAA no publicó "
                "gránulos en las ultimas %dh", hours_back)
        return [], None

    latest = keys[0]
    logger.info("FDCF: leyendo %s", latest)

    # (4) Lectura del NetCDF. Cualquier excepción (red, h5netcdf, variable
    # ausente, pyproj) invalida el scan entero: no hay lectura parcial creíble.
    try:
        with s3.open(latest, "rb") as f:
            ds = xr.open_dataset(f, engine="h5netcdf")
            # Time del scan — parsear del nombre del archivo (mas robusto que
            # decodificar variable 't' en J2000 segundos)
            scan_dt = _parse_scan_time(latest)
            hotspots = extract_hotspots(ds, bounds=bounds,
                                        high_conf_only=high_conf_only)
    except Exception as e:
        logger.exception("FDCF NO CONSULTABLE: error leyendo %s: %s", latest, e)
        return [], None

    # (5) Un scan sin hora no se puede presentar. Devolver los hotspots con
    # scan_dt=None rompería el invariante y el consumidor los pintaría sin
    # poder decir de cuándo son (o peor: el que chequea `scan_dt is None`
    # tiraría las detecciones a la basura mostrando "0"). Se degrada entero.
    if scan_dt is None:
        logger.error(
            "FDCF NO CONSULTABLE: no pude fechar el scan %s "
            "(descarto %d hotspot(s) que no puedo timestampear)",
            latest, len(hotspots))
        return [], None

    return hotspots, scan_dt


def _list_files_at_hour(s3, dt: datetime, errores: Optional[list] = None) -> list[str]:
    """Listar archivos FDCF disponibles para una hora UTC especifica.

    ``errores``: lista donde se anotan los fallos de consulta (no los
    FileNotFoundError, que son "esa hora no existe"). Sirve para que el
    llamador sepa si el vacío vino de S3 caído o de que no hay dato — la firma
    de retorno tiene que seguir siendo ``list[str]`` porque
    ``nearest_granule_key`` la invoca como callback de listado.
    """
    prefix = (
        f"{S3_BUCKET}/{S3_PRODUCT}/"
        f"{dt.year}/{dt.timetuple().tm_yday:03d}/{dt.hour:02d}/"
    )
    try:
        return sorted(s3.ls(prefix))
    except FileNotFoundError:
        return []
    except Exception as e:
        logger.warning("FDCF: no pude listar %s: %s", prefix, e)
        if errores is not None:
            errores.append((prefix, repr(e)))
        return []


def fetch_hotspots_at_time(
    dt: datetime,
    bounds: Optional[dict] = None,
    high_conf_only: bool = False,
) -> tuple[list[HotSpot], Optional[datetime]]:
    """Bajar el FDCF mas cercano a `dt` y devolver hotspots filtrados.

    Para backfill historico: dt en cualquier momento desde 2017 (GOES-16) o
    abril 2025 (GOES-19). Busca en la hora exacta + hora previa por si el
    scan que matcha cae en el borde.

    MISMO CONTRATO que ``fetch_latest_hotspots`` (ver su docstring, que es la
    referencia): ``scan_dt is None`` significa **no verificable** y trae
    ``hotspots == []``; con ``scan_dt`` no-None el ``[]`` es un cero real,
    verificado contra ese scan. Vale para el backfill igual que para NRT: un
    bucket de la timeline con 0 MW porque S3 falló no es un bucket en calma.

    Args:
        dt:               datetime UTC del scan deseado.
        bounds:           bbox para filtrar.
        high_conf_only:   solo Mask ∈ HIGH_CONF_MASK.

    Returns:
        ``(hotspots, scan_dt_real)`` con scan_dt_real = ts del archivo elegido
        (puede diferir de `dt` por ±5 min), o ``([], None)`` si no verificable.
    """
    # (1) Dependencias.
    try:
        import s3fs  # noqa: F401  (se usa vía _get_s3; el import valida presencia)
        import xarray as xr
    except ImportError as e:
        logger.error("FDCF NO CONSULTABLE: s3fs/xarray no disponible: %s", e)
        return [], None

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    # (2) Cliente S3 (mismo motivo que en el camino NRT: no dejar escapar).
    try:
        s3 = _get_s3()
    except Exception as e:
        logger.exception("FDCF NO CONSULTABLE: no pude construir el cliente S3: %s", e)
        return [], None

    # (3) Unión [dt-1h, dt, dt+1h]: el scan más cercano al borde de hora puede
    # caer en la hora adyacente (el comentario viejo prometía esto pero solo
    # hacía fallback a la previa). Elige la key de menor |Δt| sobre las tres.
    errores: list = []
    chosen = nearest_granule_key(lambda h: _list_files_at_hour(s3, h, errores),
                                 _parse_scan_time, dt)
    if chosen is None:
        if errores:
            logger.error("FDCF NO CONSULTABLE: %d listado(s) de S3 fallaron "
                         "cerca de %s", len(errores), dt.isoformat())
        else:
            logger.warning("FDCF NO CONSULTABLE: no hay archivos cerca de %s",
                           dt.isoformat())
        return [], None

    logger.info("FDCF: ts=%s, archivo elegido: %s",
                dt.isoformat(), chosen.split("/")[-1])

    # (4) Lectura del NetCDF: cualquier excepción invalida el scan entero.
    try:
        with s3.open(chosen, "rb") as f:
            ds = xr.open_dataset(f, engine="h5netcdf")
            scan_dt = _parse_scan_time(chosen)
            hotspots = extract_hotspots(ds, bounds=bounds,
                                        high_conf_only=high_conf_only)
    except Exception as e:
        logger.exception("FDCF NO CONSULTABLE: error leyendo histórico %s: %s",
                         chosen, e)
        return [], None

    # (5) Sin hora no hay bucket al cual atribuir el FRP: se degrada entero.
    # (En la práctica `chosen` salió de nearest_granule_key, que ya lo fechó;
    #  el guard queda por si la selección cambia de criterio.)
    if scan_dt is None:
        logger.error(
            "FDCF NO CONSULTABLE: no pude fechar el scan histórico %s "
            "(descarto %d hotspot(s) que no puedo timestampear)",
            chosen, len(hotspots))
        return [], None

    return hotspots, scan_dt
