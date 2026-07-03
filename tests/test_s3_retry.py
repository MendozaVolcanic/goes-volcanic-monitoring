"""Tests del retry de S3 en goes_s3 (robustez a caídas transitorias de red).

La conexión a noaa-goes19 se cae intermitentemente al bajar/listar muchos objetos;
sin retry un corte transitorio tumbaba una descarga NRT o un barrido histórico
entero. `_retry_s3` reintenta fallos transitorios pero NO `FileNotFoundError` (que
significa "el objeto no existe", no un fallo de red). Todo PURO (fn falso).
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.fetch.goes_s3 import _retry_s3, _S3_RETRIES


def test_retry_succeeds_after_transient_failures():
    """Falla las primeras 2 veces (red), luego OK → devuelve el resultado."""
    calls = {"n": 0}

    def flaky():
        calls["n"] += 1
        if calls["n"] < 3:
            raise ConnectionError("EndpointConnectionError simulado")
        return "ok"

    assert _retry_s3(flaky, what="test") == "ok"
    assert calls["n"] == 3


def test_retry_does_not_retry_file_not_found():
    """FileNotFoundError se propaga SIN reintentar (no es transitorio)."""
    calls = {"n": 0}

    def missing():
        calls["n"] += 1
        raise FileNotFoundError("no existe")

    with pytest.raises(FileNotFoundError):
        _retry_s3(missing, what="test")
    assert calls["n"] == 1, "no debe reintentar un 404"


def test_retry_reraises_last_after_exhausting():
    """Agotados los reintentos, relanza la última excepción transitoria."""
    calls = {"n": 0}

    def always_fails():
        calls["n"] += 1
        raise TimeoutError("read timeout")

    with pytest.raises(TimeoutError):
        _retry_s3(always_fails, what="test")
    assert calls["n"] == _S3_RETRIES


def test_retry_passes_args():
    """Pasa args/kwargs al fn envuelto."""
    assert _retry_s3(lambda a, b=0: a + b, 3, b=4) == 7


if __name__ == "__main__":
    test_retry_succeeds_after_transient_failures()
    test_retry_does_not_retry_file_not_found()
    test_retry_reraises_last_after_exhausting()
    test_retry_passes_args()
    print("OK — s3 retry")
