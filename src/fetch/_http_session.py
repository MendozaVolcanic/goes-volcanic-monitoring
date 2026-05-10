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

DEFAULT_USER_AGENT = "GOES-VolcanicMonitor/1.0 (SERNAGEOMIN)"

_session: requests.Session | None = None


def get_session(user_agent: str = DEFAULT_USER_AGENT) -> requests.Session:
    """Devolver la session global. Crea si no existe.

    El `user_agent` solo se aplica la primera vez; mantener el default a
    menos que un cliente especifico necesite otro identifier.
    """
    global _session
    if _session is None:
        _session = requests.Session()
        _session.headers.update({"User-Agent": user_agent})
    return _session
