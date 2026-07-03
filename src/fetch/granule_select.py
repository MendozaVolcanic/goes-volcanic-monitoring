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

from datetime import datetime, timedelta, timezone
from typing import Callable, Optional


def nearest_granule_key(
    list_hour: Callable[[datetime], list],
    parse_ts: Callable[[str], Optional[datetime]],
    dt: datetime,
) -> Optional[str]:
    """Key del gránulo cuyo timestamp de inicio de scan está más cerca de ``dt``.

    Args:
        list_hour: ``fn(hour_dt) -> [keys]`` que lista los gránulos de la carpeta
                   horaria de ``hour_dt`` (la E/S — S3 — vive acá).
        parse_ts:  ``fn(key) -> datetime`` con el inicio de scan, o ``None`` si la
                   key no parsea.
        dt:        instante objetivo (UTC; naive se asume UTC).

    Returns:
        La key más cercana entre la unión de ``[dt-1h, dt, dt+1h]``, o ``None`` si
        ninguna de las tres horas tiene gránulos con timestamp parseable.
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
    # Si TODAS las keys eran inparseables, min() devuelve una con Δ=inf → None.
    return best if _delta(best) != float("inf") else None
