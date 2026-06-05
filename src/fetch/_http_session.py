"""Session HTTP compartida para todos los clientes de src/fetch.

Antes cada modulo (rammb_slider, hires_cache, animation_cache, realearth_api)
tenia su propio `_get_session()` singleton — codigo duplicado. Ahora todos
piden su sesion aca.

Por que un singleton: requests.Session reusa connection pooling
HTTP keep-alive entre requests, ahorra ~50ms de TLS handshake por call.
Para fetch masivo (animation_cache baja 200+ tiles por run) la diferencia
es grande.
"""

from __future__ import annotations

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

DEFAULT_USER_AGENT = "GOES-VolcanicMonitor/1.0 (SERNAGEOMIN)"

_session: requests.Session | None = None


def get_session(user_agent: str = DEFAULT_USER_AGENT) -> requests.Session:
    """Devolver la session global. Crea si no existe.

    El `user_agent` solo se aplica la primera vez; mantener el default a
    menos que un cliente especifico necesite otro identifier.

    REINTENTOS (jun 2026): la session monta un HTTPAdapter con Retry para
    que un proveedor lento o un 5xx transitorio (RAMMB/CIRA, SSEC, AWS) no
    rompa un fetch al primer intento. 3 reintentos con backoff exponencial
    (0.5s, 1s, 2s) ante 429/500/502/503/504 y errores de conexion. Cubre
    de una a todos los clientes que usan esta session compartida.
    """
    global _session
    if _session is None:
        _session = requests.Session()
        _session.headers.update({"User-Agent": user_agent})
        retry = Retry(
            total=3,
            connect=3,
            read=3,
            backoff_factor=0.5,  # 0.5s, 1s, 2s entre reintentos
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=("GET", "HEAD"),
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retry, pool_maxsize=16)
        _session.mount("http://", adapter)
        _session.mount("https://", adapter)
    return _session
