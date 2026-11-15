"""Secuencias de reruns del menú lateral contra la URL ``?vista=``.

Si la sincronización estuviera rota, estas pruebas fallan: cada una afirma qué
vista queda activa después de cada interacción. La línea base roja se obtuvo
sobre la lógica anterior, donde el segundo clic seguido no cambiaba de vista.
"""

from dashboard.navegacion import (
    CLAVE_MENU,
    adoptar_vista_de_url,
    publicar_vista_en_url,
)

OPERACIONAL = "Vista Operacional"
GUARDIA = "Modo Guardia"
SLUGS = {"operacional": OPERACIONAL, "guardia": GUARDIA}
POR_VISTA = {v: k for k, v in SLUGS.items()}


def _rerun(estado, url, clic=None):
    """Un rerun completo de app.py: clic, URL, widget y escritura de la URL."""
    if clic is not None:
        # Streamlit aplica el valor del widget antes de correr el script.
        estado[CLAVE_MENU] = clic
    adoptar_vista_de_url(estado, url.get("vista", ""), SLUGS)
    estado.setdefault(CLAVE_MENU, OPERACIONAL)
    publicar_vista_en_url(estado, url, POR_VISTA[estado[CLAVE_MENU]])
    return estado[CLAVE_MENU]


def test_cada_clic_seguido_cambia_de_vista_a_la_primera():
    estado, url = {}, {"vista": "operacional"}
    assert _rerun(estado, url) == OPERACIONAL

    for destino in (GUARDIA, OPERACIONAL, GUARDIA, OPERACIONAL):
        assert _rerun(estado, url, clic=destino) == destino
        assert url["vista"] == POR_VISTA[destino]


def test_el_enlace_directo_abre_la_vista_pedida():
    estado, url = {}, {"vista": "guardia"}
    assert _rerun(estado, url) == GUARDIA


def test_una_url_cambiada_desde_afuera_manda_en_el_rerun_siguiente():
    """No cubre el botón atrás real: el navegador cambia la URL sin rerun."""
    estado, url = {}, {"vista": "operacional"}
    _rerun(estado, url)
    _rerun(estado, url, clic=GUARDIA)

    url["vista"] = "operacional"

    assert _rerun(estado, url) == OPERACIONAL


def test_un_clic_despues_de_un_cambio_externo_entra_a_la_primera():
    estado, url = {}, {"vista": "operacional"}
    _rerun(estado, url)
    _rerun(estado, url, clic=GUARDIA)
    url["vista"] = "operacional"
    _rerun(estado, url)

    assert _rerun(estado, url, clic=GUARDIA) == GUARDIA


def test_un_slug_desconocido_no_mueve_el_menu():
    estado, url = {}, {"vista": "operacional"}
    _rerun(estado, url)
    url["vista"] = "no-existe"

    assert _rerun(estado, url) == OPERACIONAL
