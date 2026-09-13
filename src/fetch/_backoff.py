"""Espera exponencial con jitter entre reintentos de operaciones S3.

Por qué existe: `goes_s3._retry_s3` y `gfs_archive._read_range` reintentaban en
ráfaga, sin pausa. Ante un corte de red de un par de segundos, cuatro intentos
en milisegundos caen todos dentro del mismo corte, y ante un 503 SlowDown (S3
pidiendo explícitamente bajar el ritmo) la ráfaga agrava el throttle. El patrón
que recomienda AWS es backoff exponencial con *full jitter*: esperar un tiempo
aleatorio uniforme entre 0 y un techo que se duplica en cada intento, para que
varios hilos o procesos que fallaron juntos no vuelvan a chocar sincronizados.

Qué NO hace: decidir qué excepción es transitoria. Eso lo sigue resolviendo cada
llamador (FileNotFoundError nunca se reintenta: es "el objeto no existe").

`_sleep` y `_rng` son atributos de módulo a propósito: los tests los parchean
para no dormir de verdad y para fijar el jitter.
"""

from __future__ import annotations

import random
import time

# Primer techo de espera y techo absoluto, en segundos. Con 4 intentos hay 3
# esperas de a lo más 1 + 2 + 4 = 7 s: suficiente para salir de un corte breve o
# de un SlowDown, y acotado porque el llamador puede ser una vista de Streamlit.
BACKOFF_BASE_S = 1.0
BACKOFF_CAP_S = 20.0

_sleep = time.sleep
_rng = random.random


def backoff_delay(attempt: int, base_s: float = BACKOFF_BASE_S,
                  cap_s: float = BACKOFF_CAP_S, rng=None) -> float:
    """Segundos a esperar tras el intento fallido número ``attempt`` (0-based).

    Full jitter: ``rng() * min(cap_s, base_s * 2**attempt)``. Función pura si se
    le pasa ``rng``.
    """
    r = (rng or _rng)()
    return r * min(cap_s, base_s * (2 ** attempt))


def pause_before_retry(attempt: int) -> None:
    """Dormir el backoff correspondiente al intento fallido ``attempt``."""
    _sleep(backoff_delay(attempt))
