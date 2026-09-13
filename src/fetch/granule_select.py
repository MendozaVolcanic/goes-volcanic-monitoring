"""Selección del gránulo S3 más cercano a un instante, robusta al borde de hora.

Por qué existe (pipeline → dato correcto): los productos ABI en S3 se particionan
por **hora UTC** (``.../YYYY/DDD/HH/``). El scan cuyo timestamp de inicio está
más cerca de un ``dt`` dado puede caer en la hora ANTERIOR o la SIGUIENTE:

- un scan de HH:56 tiene su vecino real en (HH+1):00 (4 min) — no HH:50 (6 min);
- un scan de HH:02 lo tiene en (HH-1):58;
- y el primer scan de la hora a veces llega tarde por latencia S3, con lo que el
  verdadero más cercano al borde queda en la hora previa.

Listar solo la carpeta de ``dt`` —o con la previa como mero *fallback* cuando la
de ``dt`` está vacía, que era el patrón repetido en los fetchers— elige en esos
bordes un gránulo temporalmente más lejano del objetivo. Para un producto NRT
esto sesga el frame usado (detección de ceniza / altura de pluma / FRP) hacia un
scan equivocado, o mal-atribuye el FRP a un bucket de 10 min adyacente.

Este helper lista la **unión** de ``[dt-1h, dt, dt+1h]`` y devuelve la key de
menor ``|Δt|``. Es PURO respecto a la red: toda la E/S entra por el callback
``list_hour``, así que se testea con un lister en memoria (ver
``tests/test_granule_select.py``). Cada fetcher lo invoca con su propio
``list_hour``/``parse_ts`` (distintos buckets, prefijos y formatos de nombre).

Nota de costo: para una llamada NRT (``dt``≈ahora) la carpeta de ``dt+1h`` está
en el futuro y la listada devuelve vacío — un round-trip S3 extra barato frente a
abrir un gránulo equivocado. Los usos de backfill (FDCF/ACHA/LVTPF) son
históricos, donde la latencia de una listada no importa.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Callable, Optional

logger = logging.getLogger(__name__)

# Expiración del cache de LISTADOS de s3fs, en segundos.
#
# Por qué existe (audit ago-2026, verificado en vivo): `s3fs.S3FileSystem(anon=True)`
# es *cacheable* — todas las construcciones con los mismos kwargs devuelven LA MISMA
# instancia — y su `DirCache` nace con `listings_expiry_time=None`, o sea NUNCA expira.
# Efecto: la primera vez que se lista la carpeta de la hora en curso
# (`.../YYYY/DDD/HH/`), ese listado queda congelado para todo el proceso; los gránulos
# que NOAA publica después en esa misma hora son invisibles hasta que el reloj cruza a
# la hora siguiente. En GitHub Actions (proceso efímero) no se nota, pero en el deploy
# de larga vida el "scan más reciente" podía quedar hasta ~1 h atrasado y presentarse
# como vigente — para un SDA de alerta, dato viejo disfrazado de actual.
#
# Pasar este kwarg en TODAS las construcciones mantiene la instancia compartida (mismo
# juego de kwargs) y además le da caducidad al listado.
S3_LISTINGS_EXPIRY_S = 60


def get_s3(anon: bool = True):
    """`s3fs.S3FileSystem` compartido con cache de listados que EXPIRA.

    Usar en vez de `s3fs.S3FileSystem(anon=True)` pelado: garantiza que todos los
    fetchers compartan una única instancia y que ningún listado horario quede
    congelado (ver ``S3_LISTINGS_EXPIRY_S``).
    """
    import s3fs
    return s3fs.S3FileSystem(anon=anon, listings_expiry_time=S3_LISTINGS_EXPIRY_S)


# Tope de desfase, en segundos, entre el instante pedido y el inicio de scan del
# gránulo elegido. Lógica del SDA: ver docs/FICHA_SDA_GOES.md §A.6.
#
# Qué: con ``max_gap_s=SCAN_MAX_GAP_S``, ``nearest_granule_key`` devuelve ``None``
# si el gránulo más cercano está más lejos que esto, en vez de entregarlo como si
# fuera el scan pedido. Antes, ante un hueco de datos NOAA, la unión de tres horas
# podía devolver un gránulo de hasta ~60 min y el llamador lo mostraba con la hora
# que había pedido (escena de ceniza, altura, FRP de otro momento).
#
# Por qué 30 min: en NRT el llamador pide ``dt=ahora`` y el scan más nuevo en S3
# empieza hasta cadencia + latencia antes. Medido el 13-sep-2026 sobre 24 h del
# bucket (LastModified menos inicio de scan): L1b C14 máx 10,1 min, FDCF 10,8,
# ACHA 12,4, LVTPF 13,1, con cadencia fija de 10 min, o sea desfase normal de hasta
# ~23 min. 30 min deja ~7 min de margen para que la latencia normal NUNCA se lea
# como "sin dato", que sería un negativo silencioso. En uso histórico (``dt`` sobre
# la grilla de scans) el desfase normal es de 0 a 5 min: el tope deja pasar un
# hueco de un par de scans y corta el caso de ~1 h.
SCAN_MAX_GAP_S = 30 * 60


def nearest_granule_key(
    list_hour: Callable[[datetime], list],
    parse_ts: Callable[[str], Optional[datetime]],
    dt: datetime,
    max_gap_s: Optional[float] = None,
) -> Optional[str]:
    """Key del gránulo cuyo timestamp de inicio de scan está más cerca de ``dt``.

    Args:
        list_hour: ``fn(hour_dt) -> [keys]`` que lista los gránulos de la carpeta
                   horaria de ``hour_dt`` (la E/S — S3 — vive acá).
        parse_ts:  ``fn(key) -> datetime`` con el inicio de scan, o ``None`` si la
                   key no parsea.
        dt:        instante objetivo (UTC; naive se asume UTC).
        max_gap_s: tope de ``|Δt|`` en segundos (inclusive). Si el más cercano lo
                   supera se devuelve ``None`` y se deja un warning con el desfase.
                   ``None`` = sin tope (comportamiento previo). Los fetchers que
                   tratan el resultado como "el scan de dt" pasan
                   ``SCAN_MAX_GAP_S``.

    Returns:
        La key más cercana entre la unión de ``[dt-1h, dt, dt+1h]``, o ``None`` si
        ninguna de las tres horas tiene gránulos con timestamp parseable o si el
        más cercano excede ``max_gap_s``.
    """
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    seen: set = set()
    keys: list = []
    for hour_dt in (dt - timedelta(hours=1), dt, dt + timedelta(hours=1)):
        for k in list_hour(hour_dt):
            if k not in seen:
                seen.add(k)
                keys.append(k)
    if not keys:
        return None

    def _delta(k: str) -> float:
        ts = parse_ts(k)
        return float("inf") if ts is None else abs((ts - dt).total_seconds())

    best = min(keys, key=_delta)
    gap = _delta(best)
    # Si TODAS las keys eran inparseables, min() devuelve una con Δ=inf → None.
    if gap == float("inf"):
        return None
    # Tope: un gránulo demasiado lejano no es "el scan de dt". Se deja registrado
    # el desfase para distinguir en los logs "hueco NOAA" de "no hay archivos" y
    # para detectar si la latencia de NOAA crece hasta rozar el tope.
    if max_gap_s is not None and gap > max_gap_s:
        logger.warning(
            "gránulo más cercano a %s está a %.1f min (tope %.1f min): no se usa "
            "como el scan pedido (%s)", dt.isoformat(), gap / 60.0,
            max_gap_s / 60.0, str(best).split("/")[-1])
        return None
    return best
