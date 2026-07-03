"""Descarga de gránulos VIIRS L1b banda M (750 m) desde NASA Earthdata.

Por qué (pipeline): para el retrieval de altura de pluma a 750 m (3× más fino que
los 2 km del ABI) necesitamos las radiancias VIIRS crudas M15/M16. NASA las publica
como NetCDF (VNP02MOD radiancia + VNP03MOD geolocalización) vía Earthdata; el
acceso se hace con la librería ``earthaccess`` (búsqueda CMR + descarga LAADS/LANCE).

Requiere credenciales NASA Earthdata (gratis, urs.earthdata.nasa.gov): variable de
entorno ``EARTHDATA_TOKEN`` o ``EARTHDATA_USERNAME``+``EARTHDATA_PASSWORD``, o un
``.env`` (se busca el de Goes y, como cortesía para desarrollo, el de VRP Chile que
ya las tiene configuradas — mismo dueño, mismos secretos).

Versión LEAN a propósito: VRP Chile tiene un fetch endurecido para su cron NRT
(circuit-breakers, IPv4-force, budgets de reintento). Acá es on-demand para
validación/retrieval, así que basta ``earthaccess.login`` + ``search_data`` +
``download``. Si esto se cablea a un cron, migrar a la infra robusta de VRP Chile.

Dependencia opcional: ``earthaccess`` (extra ``viirs`` en pyproject). El import va
guardado dentro de las funciones para que importar el módulo no falle sin ella.
"""

from __future__ import annotations

import logging
import os
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Productos M-band (750 m) por satélite: (short_name L1b, short_name GEO). El sufijo
# _NRT es el fallback near-real-time (cierra el gap de 3-5 días de calibración std).
MOD_PRODUCTS = {
    "SNPP":   ("VNP02MOD", "VNP03MOD"),
    "NOAA20": ("VJ102MOD", "VJ103MOD"),
    "NOAA21": ("VJ202MOD", "VJ203MOD"),
}

# Token de fecha/hora del nombre de gránulo VIIRS: ``.A{YYYYDDD}.{HHMM}.`` — común a
# L1b y GEO del mismo scan, así que sirve para emparejarlos.
_ATOKEN = re.compile(r"\.A(\d{7})\.(\d{4})\.")


def _load_earthdata_env() -> None:
    """Cargar credenciales Earthdata al entorno si no están: busca un .env en Goes
    y, en su defecto, en VRP Chile (mismo dueño). No pisa variables ya seteadas."""
    if os.environ.get("EARTHDATA_TOKEN") or (
            os.environ.get("EARTHDATA_USERNAME") and os.environ.get("EARTHDATA_PASSWORD")):
        return
    here = Path(__file__).resolve()
    candidates = [
        here.parents[2] / ".env",                               # Goes/.env
        here.parents[3] / "VRP Chile" / ".env",                 # ../VRP Chile/.env
    ]
    for env in candidates:
        if not env.exists():
            continue
        for line in env.read_text(encoding="utf-8", errors="ignore").splitlines():
            line = line.strip()
            if line.startswith("EARTHDATA_") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
        if os.environ.get("EARTHDATA_TOKEN") or os.environ.get("EARTHDATA_USERNAME"):
            logger.info("Credenciales Earthdata cargadas de %s", env)
            return


def viirs_login() -> bool:
    """Autenticar con NASA Earthdata vía earthaccess (estrategia environment).
    Devuelve True si autenticó. Carga el .env si hace falta."""
    try:
        import earthaccess
    except ImportError as e:
        logger.error("earthaccess no disponible (pip install earthaccess): %s", e)
        return False
    _load_earthdata_env()
    try:
        auth = earthaccess.login(strategy="environment", persist=False)
        return bool(getattr(auth, "authenticated", False))
    except Exception as e:
        logger.warning("Earthdata login falló: %s", e)
        return False


def _granule_name(g) -> str:
    """Nombre de archivo de un resultado earthaccess (de su primer data link)."""
    try:
        links = g.data_links()
        return links[0].split("/")[-1] if links else ""
    except Exception:
        return ""


def _atoken_dt(name: str) -> Optional[datetime]:
    """datetime UTC del token ``.A{YYYYDDD}.{HHMM}.`` del nombre de gránulo."""
    m = _ATOKEN.search(name)
    if not m:
        return None
    yyyyddd, hhmm = m.group(1), m.group(2)
    try:
        base = datetime(int(yyyyddd[:4]), 1, 1, int(hhmm[:2]), int(hhmm[2:]),
                        tzinfo=timezone.utc)
        return base + timedelta(days=int(yyyyddd[4:]) - 1)
    except Exception:
        return None


def _atoken_key(name: str) -> Optional[str]:
    """Clave de emparejamiento L1b↔GEO: el token ``A{YYYYDDD}.{HHMM}``."""
    m = _ATOKEN.search(name)
    return f"{m.group(1)}.{m.group(2)}" if m else None


def fetch_viirs_mod(
    lat: float, lon: float, dt: datetime, sensor: str = "SNPP",
    window_min: int = 90, pad_deg: float = 0.6, out_dir=None,
) -> Optional[dict]:
    """Bajar el par (L1b M-band, GEO) VIIRS más cercano a ``dt`` sobre (lat,lon).

    Args:
        lat, lon:    centro (grados). ``dt``: instante objetivo (UTC).
        sensor:      SNPP / NOAA20 / NOAA21.
        window_min:  ventana ± alrededor de ``dt`` para buscar pasadas.
        pad_deg:     medio ancho del bbox de búsqueda.
        out_dir:     carpeta de descarga (default: data/raw/viirs).

    Returns:
        dict ``{l1b_path, geo_path, granule_dt, sensor, source}`` del par más
        cercano, o None si no autentica / no hay pasada / no matchea GEO.
    """
    try:
        import earthaccess
    except ImportError:
        logger.error("earthaccess no disponible")
        return None
    if sensor not in MOD_PRODUCTS:
        logger.error("sensor %s no válido (%s)", sensor, list(MOD_PRODUCTS))
        return None
    if not viirs_login():
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    l1b_sn, geo_sn = MOD_PRODUCTS[sensor]
    t0 = (dt - timedelta(minutes=window_min)).strftime("%Y-%m-%d %H:%M:%S")
    t1 = (dt + timedelta(minutes=window_min)).strftime("%Y-%m-%d %H:%M:%S")
    bbox = (lon - pad_deg, lat - pad_deg, lon + pad_deg, lat + pad_deg)

    def _search(short_name):
        for sn in (short_name, short_name + "_NRT"):
            try:
                res = earthaccess.search_data(short_name=sn, temporal=(t0, t1),
                                              bounding_box=bbox)
            except Exception as e:
                logger.warning("CMR search %s: %s", sn, e)
                res = []
            if res:
                return res
        return []

    l1b_res = _search(l1b_sn)
    geo_res = _search(geo_sn)
    if not l1b_res or not geo_res:
        logger.warning("VIIRS %s: sin gránulos L1b/GEO en ±%d min de %s",
                       sensor, window_min, dt.isoformat())
        return None

    # Emparejar por token A y elegir el par más cercano a dt.
    geo_by_key = {}
    for g in geo_res:
        k = _atoken_key(_granule_name(g))
        if k:
            geo_by_key.setdefault(k, g)
    best = None
    for l in l1b_res:
        name = _granule_name(l)
        k = _atoken_key(name)
        gdt = _atoken_dt(name)
        if k in geo_by_key and gdt is not None:
            gap = abs((gdt - dt).total_seconds())
            if best is None or gap < best[0]:
                best = (gap, l, geo_by_key[k], gdt)
    if best is None:
        logger.warning("VIIRS %s: ningún L1b matchea un GEO por token A", sensor)
        return None

    out_dir = Path(out_dir) if out_dir else Path("data/raw/viirs")
    out_dir.mkdir(parents=True, exist_ok=True)
    try:
        l1b_files = earthaccess.download([best[1]], str(out_dir))
        geo_files = earthaccess.download([best[2]], str(out_dir))
    except Exception as e:
        logger.exception("descarga VIIRS falló: %s", e)
        return None
    if not l1b_files or not geo_files:
        return None
    return {
        "l1b_path": Path(l1b_files[0]),
        "geo_path": Path(geo_files[0]),
        "granule_dt": best[3],
        "sensor": sensor,
        "source": f"VIIRS {sensor} M-band (NASA {l1b_sn} + {geo_sn} via earthaccess)",
    }
