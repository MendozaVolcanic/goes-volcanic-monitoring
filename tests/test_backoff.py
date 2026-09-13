"""Backoff exponencial con jitter en los reintentos S3 (goes_s3 y gfs_archive).

Por qué importa: los reintentos de `_retry_s3` y de `gfs_archive._read_range`
disparaban los 4 intentos en milisegundos. Contra un corte transitorio eso casi
no ayuda, y contra un 503 SlowDown de S3 lo empeora: S3 pide bajar el ritmo y
el cliente responde con tres pedidos más en ráfaga. AWS recomienda esperas
exponenciales con jitter ("full jitter"), para que muchos clientes que fallaron
a la vez no reintenten todos en el mismo instante.

Ningún test duerme de verdad: se parchea `_backoff._sleep` y se registra lo que
se habría esperado. `_backoff._rng` se fija para que las esperas sean exactas.
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.fetch import _backoff


@pytest.fixture()
def esperas(monkeypatch):
    """Registra las esperas en vez de dormir; jitter fijo al máximo (rng=1)."""
    registro: list = []
    monkeypatch.setattr(_backoff, "_sleep", registro.append)
    monkeypatch.setattr(_backoff, "_rng", lambda: 1.0)
    return registro


# ── La fórmula ──────────────────────────────────────────────────────────────

def test_la_espera_crece_exponencialmente():
    """Con jitter al máximo, cada intento duplica la espera del anterior."""
    d = [_backoff.backoff_delay(i, base_s=1.0, cap_s=100.0, rng=lambda: 1.0)
         for i in range(4)]
    assert d == [1.0, 2.0, 4.0, 8.0]


def test_la_espera_tiene_techo():
    """Un intento alto no puede dejar la app colgada minutos."""
    assert _backoff.backoff_delay(20, base_s=1.0, cap_s=5.0, rng=lambda: 1.0) == 5.0


def test_el_jitter_escala_la_espera():
    """Full jitter: la espera es uniforme en [0, techo]; rng=0.25 da un cuarto."""
    assert _backoff.backoff_delay(2, base_s=1.0, cap_s=100.0, rng=lambda: 0.25) == 1.0


# ── _retry_s3 ───────────────────────────────────────────────────────────────

def test_retry_s3_espera_entre_intentos_y_no_despues_del_ultimo(esperas):
    from src.fetch.goes_s3 import _S3_RETRIES, _retry_s3

    def siempre_falla():
        raise ConnectionError("SlowDown simulado")

    with pytest.raises(ConnectionError):
        _retry_s3(siempre_falla, what="test")
    # Una espera ENTRE cada par de intentos; dormir tras el último sólo atrasa
    # el error sin darle otra oportunidad a la operación.
    assert len(esperas) == _S3_RETRIES - 1
    assert esperas == sorted(esperas) and esperas[0] < esperas[-1], esperas


def test_retry_s3_no_espera_ante_file_not_found(esperas):
    """Un objeto inexistente no se reintenta, y tampoco se espera por él."""
    from src.fetch.goes_s3 import _retry_s3

    def no_existe():
        raise FileNotFoundError("no existe")

    with pytest.raises(FileNotFoundError):
        _retry_s3(no_existe, what="test")
    assert esperas == []


def test_retry_s3_exito_al_primer_intento_no_espera(esperas):
    from src.fetch.goes_s3 import _retry_s3
    assert _retry_s3(lambda: "ok") == "ok"
    assert esperas == []


# ── gfs_archive._read_range ─────────────────────────────────────────────────

class _S3Intermitente:
    def __init__(self, fallas: int):
        self.fallas = fallas
        self.llamadas = 0

    def cat_file(self, key, start=None, end=None):
        self.llamadas += 1
        if self.llamadas <= self.fallas:
            raise TimeoutError("read timeout simulado")
        return b"GRIB"


def test_read_range_espera_con_backoff_y_luego_lee(esperas):
    from src.fetch.gfs_archive import _read_range

    s3 = _S3Intermitente(fallas=2)
    assert _read_range(s3, "k", 0, 9) == b"GRIB"
    assert s3.llamadas == 3
    assert esperas == [_backoff.backoff_delay(0, rng=lambda: 1.0),
                       _backoff.backoff_delay(1, rng=lambda: 1.0)]


def test_read_range_agotado_relanza_sin_espera_final(esperas):
    from src.fetch.gfs_archive import _read_range

    s3 = _S3Intermitente(fallas=99)
    with pytest.raises(TimeoutError):
        _read_range(s3, "k", 0, 9, retries=4)
    assert s3.llamadas == 4
    assert len(esperas) == 3


def test_read_range_no_reintenta_file_not_found(esperas):
    """Mismo criterio que goes_s3: 'no existe' no es un fallo de red."""
    from src.fetch.gfs_archive import _read_range

    class _S3SinObjeto:
        llamadas = 0

        def cat_file(self, key, start=None, end=None):
            self.llamadas += 1
            raise FileNotFoundError(key)

    s3 = _S3SinObjeto()
    with pytest.raises(FileNotFoundError):
        _read_range(s3, "k", 0, 9)
    assert s3.llamadas == 1
    assert esperas == []
