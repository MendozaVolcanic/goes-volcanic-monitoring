"""Sincroniza el menú lateral con el parámetro ``?vista=`` de la URL.

Hay dos fuentes de verdad que compiten: el clic del operador en el menú y la
URL (enlace directo, atrás/adelante del navegador). Para decidir cuál manda se
recuerda la última URL conocida: si la URL no coincide, cambió desde afuera.

Son funciones sobre mapeos para poder probar la secuencia de reruns completa
sin levantar Streamlit, que es donde vive este tipo de error.
"""

from __future__ import annotations

from collections.abc import Mapping, MutableMapping

CLAVE_MENU = "nav_page"
CLAVE_ULTIMA_URL = "__last_url_vista"


def adoptar_vista_de_url(
    estado: MutableMapping,
    url_vista: str,
    slugs: Mapping[str, str],
) -> None:
    """Si la URL cambió desde afuera, el menú la sigue. Va antes del widget."""
    url = url_vista.lower()
    if url != estado.get(CLAVE_ULTIMA_URL, "") and url in slugs:
        estado[CLAVE_MENU] = slugs[url]
    estado[CLAVE_ULTIMA_URL] = url


def publicar_vista_en_url(
    estado: MutableMapping,
    query_params: MutableMapping,
    slug: str | None,
) -> None:
    """Escribe en la URL la vista elegida en el menú. Va después del widget."""
    if slug and query_params.get("vista") != slug:
        query_params["vista"] = slug
        # Sin esto, el rerun siguiente confunde nuestra propia escritura con un
        # cambio externo y le gana al clic: el menú pedía dos clics por cambio.
        estado[CLAVE_ULTIMA_URL] = slug
