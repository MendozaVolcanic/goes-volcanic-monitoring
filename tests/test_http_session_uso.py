"""Los fetchers de Open-Meteo usan la sesión HTTP con reintentos.

Por qué importa: `src/fetch/_http_session.get_session()` monta un `Retry` (3
reintentos con backoff ante 429/5xx y errores de conexión). `gfs_profile` y
`wind_data` lo saltaban con `requests.get` crudo, así que un 503 transitorio de
Open-Meteo al primer intento terminaba en `None`. En `gfs_profile` eso es grave:
sin perfil GFS el retrieval de altura no reporta, y en pantalla se lee como "no
hay dato" algo que era un parpadeo de red.

Los tests reemplazan la sesión por un fake que registra las llamadas y hacen
explotar `requests.get`: como los módulos atrapan toda excepción y devuelven
`None`, sólo mirar el resultado no bastaría; por eso se exige que la llamada
haya pasado por la sesión. Sin red.
"""
import ast
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

RAIZ = Path(__file__).parent.parent
MODULOS = ["gfs_profile", "wind_data"]


class _Resp:
    def __init__(self, json_data=None, text="", status=200):
        self._json = json_data
        self.text = text
        self.status_code = status

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(self.status_code)

    def json(self):
        return self._json


class _Sesion:
    def __init__(self, resp):
        self.resp = resp
        self.urls: list = []

    def get(self, url, **kw):
        self.urls.append(url)
        return self.resp


@pytest.fixture()
def sesion(monkeypatch):
    """Instala una sesión falsa en todos los caminos por los que se pide."""
    import requests

    import src.fetch._http_session as hs

    def _crudo(*a, **k):
        raise AssertionError("requests.get crudo: no pasa por la sesión con Retry")

    monkeypatch.setattr(requests, "get", _crudo)

    def instalar(resp):
        s = _Sesion(resp)
        monkeypatch.setattr(hs, "get_session", lambda *a, **k: s)
        for nombre in MODULOS:
            mod = __import__(f"src.fetch.{nombre}", fromlist=["x"])
            if hasattr(mod, "_get_session"):
                monkeypatch.setattr(mod, "_get_session", lambda *a, **k: s)
        return s

    return instalar


def _hourly_gfs(extra_prefixes):
    from src.fetch.gfs_profile import GFS_LEVELS_HPA
    h = {"time": ["2026-09-13T12:00"]}
    for i, p in enumerate(GFS_LEVELS_HPA):
        h[f"temperature_{p}hPa"] = [20.0 - 4.0 * i]
        h[f"geopotential_height_{p}hPa"] = [100.0 + 1000.0 * i]
        for pref in extra_prefixes:
            h[f"{pref}_{p}hPa"] = [10.0]
    return {"hourly": h}


def test_gfs_profile_usa_la_sesion(sesion):
    from datetime import datetime, timezone

    from src.fetch import gfs_profile
    s = sesion(_Resp(json_data=_hourly_gfs([])))
    prof = gfs_profile.fetch_gfs_profile(
        -23.37, -67.73, datetime(2026, 9, 13, 12, tzinfo=timezone.utc))
    assert s.urls == [gfs_profile.OPENMETEO_URL]
    assert prof is not None and len(prof["levels"]) >= 3


def test_gfs_wind_profile_usa_la_sesion(sesion):
    from datetime import datetime, timezone

    from src.fetch import gfs_profile
    s = sesion(_Resp(json_data=_hourly_gfs(["wind_speed", "wind_direction"])))
    prof = gfs_profile.fetch_gfs_wind_profile(
        -23.37, -67.73, datetime(2026, 9, 13, 12, tzinfo=timezone.utc))
    assert s.urls == [gfs_profile.OPENMETEO_URL]
    assert prof is not None


def test_wind_point_usa_la_sesion(sesion):
    from src.fetch import wind_data
    lvl = wind_data.DEFAULT_LEVEL
    s = sesion(_Resp(json_data={"hourly": {f"wind_speed_{lvl}": [30.0] * 24,
                                           f"wind_direction_{lvl}": [270.0] * 24}}))
    out = wind_data.fetch_wind_point(-33.0, -71.0)
    assert s.urls == [wind_data.OPENMETEO_URL]
    assert out is not None and out["speed"] == 30.0


def test_wind_diagnostic_usa_la_sesion(sesion):
    from src.fetch import wind_data
    s = sesion(_Resp(status=200, text="{}"))
    out = wind_data.fetch_wind_diagnostic()
    assert s.urls == [wind_data.OPENMETEO_URL]
    assert out["ok"] is True


@pytest.mark.parametrize("nombre", MODULOS)
def test_ningun_requests_get_crudo_en_el_fuente(nombre):
    """Guard de fuente para llamadas nuevas que los tests de arriba no ejerzan."""
    py = RAIZ / "src" / "fetch" / f"{nombre}.py"
    culpables = []
    for nodo in ast.walk(ast.parse(py.read_text(encoding="utf-8"))):
        if (isinstance(nodo, ast.Call) and isinstance(nodo.func, ast.Attribute)
                and nodo.func.attr == "get"
                and isinstance(nodo.func.value, ast.Name)
                and nodo.func.value.id == "requests"):
            culpables.append(nodo.lineno)
    assert not culpables, f"{py.name}: requests.get crudo en líneas {culpables}"
