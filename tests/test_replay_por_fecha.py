"""Replay por fecha: cualquier volcan, cualquier dia que RAMMB conserve.

Por que existe (nov-2026): Nicolas quiso ver el SO2 de Lastarria del
14-11-2026 y no habia donde. La vista Replay pedia "los ultimos 200" scans a
`latest_times.json`, que en realidad entrega 100 como maximo (unas 16 h), y
solo ofrecia 6 volcanes fijos, aunque el texto prometia 28 dias.

RAMMB publica por producto `available_dates.json` (dias listados) y
`<YYYYMMDD>_by_hour.json` (scans de ese dia UTC). Medido el 15-11-2026: la
lista trae dias que ya no tienen imagenes (15-12-2025, 15-04-2026,
01-06-2026 devuelven 404 en todos los tiles). Por eso un dia listado no se da
por disponible sin probar una imagen, y un dia que no existe se dice, no se
reemplaza por otro.
"""

import sys
from datetime import date
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.fetch import historic_rammb as hr

CHILE = ZoneInfo("America/Santiago")


class _Resp:
    def __init__(self, status, payload=None, content=b""):
        self.status_code = status
        self._payload = payload
        self.content = content

    def json(self):
        return self._payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


class _Sesion:
    """Responde por sufijo de URL; lo no previsto es un error de red."""

    def __init__(self, rutas):
        self.rutas = rutas
        self.pedidas = []

    def get(self, url, timeout=None, headers=None):
        self.pedidas.append(url)
        for sufijo, resp in self.rutas.items():
            if sufijo in url:
                if isinstance(resp, Exception):
                    raise resp
                return resp
        raise ConnectionError("sin red")


def _por_hora(*ts):
    """Arma un payload `_by_hour.json` como el real (horas como claves,
    mas nuevo primero dentro de cada hora)."""
    horas: dict[str, list[int]] = {}
    for t in ts:
        horas.setdefault(t[8:10], []).append(int(t))
    for h in horas.values():
        h.sort(reverse=True)
    return {"timestamps_int": horas}


# ── Lectura de los JSON de RAMMB ─────────────────────────────────────

def test_fechas_listadas_se_leen_como_date_ordenadas():
    payload = {"dates_int": [20261115, 20261114, 20250716]}
    assert hr.parse_available_dates(payload) == [
        date(2025, 7, 16), date(2026, 11, 14), date(2026, 11, 15)]


def test_scans_de_un_dia_se_aplanan_en_orden_cronologico():
    payload = _por_hora("20261114235020", "20261114000020", "20261114234020",
                        "20261114001021")
    assert hr.parse_by_hour(payload) == [
        "20261114000020", "20261114001021",
        "20261114234020", "20261114235020"]


def test_dia_con_scans_responde_ok(monkeypatch):
    s = _Sesion({"/jma_so2/20261114_by_hour.json":
                 _Resp(200, _por_hora("20261114120020", "20261114121020"))})
    monkeypatch.setattr(hr, "_get_session", lambda: s)
    ts, estado = hr.fetch_day_timestamps("jma_so2", date(2026, 11, 14))
    assert estado == "ok"
    assert ts == ["20261114120020", "20261114121020"]


def test_dia_que_rammb_no_conserva_no_es_lo_mismo_que_sin_respuesta(monkeypatch):
    """404 = RAMMB dice que el dia no esta. Un error de red no dice nada del
    dia: mezclarlos haria que una caida se lea como 'no hubo datos'."""
    s = _Sesion({"/20260815_by_hour.json": _Resp(404)})
    monkeypatch.setattr(hr, "_get_session", lambda: s)
    assert hr.fetch_day_timestamps("jma_so2", date(2026, 8, 15)) == (
        [], "no_conservado")
    assert hr.fetch_day_timestamps("jma_so2", date(2026, 8, 16)) == (
        [], "sin_respuesta")


# ── Dia local de Chile ───────────────────────────────────────────────

def test_un_dia_local_de_chile_cruza_dos_dias_utc():
    """En noviembre Chile continental esta en UTC-3: el 14-11 local va de
    03:00 UTC del 14 a 02:59 UTC del 15."""
    assert hr.utc_dates_for_local_day(date(2026, 11, 14), CHILE) == [
        date(2026, 11, 14), date(2026, 11, 15)]


def test_ventana_horaria_local_filtra_en_hora_de_chile():
    dia = date(2026, 11, 14)
    todos = ["20261114025020",   # 23:50 del 13 en Chile: fuera
             "20261114030020",   # 00:00 del 14 en Chile
             "20261114125020",   # 09:50
             "20261114130020",   # 10:00
             "20261114165020",   # 13:50
             "20261114170020",   # 14:00: fuera de [10, 14)
             "20261115025020"]   # 23:50 del 14
    assert hr.timestamps_in_local_window(todos, dia, 0, 24, CHILE) == [
        "20261114030020", "20261114125020", "20261114130020",
        "20261114165020", "20261114170020", "20261115025020"]
    assert hr.timestamps_in_local_window(todos, dia, 10, 14, CHILE) == [
        "20261114130020", "20261114165020"]


def test_listar_dia_local_junta_los_dos_dias_utc(monkeypatch):
    s = _Sesion({
        "/20261114_by_hour.json": _Resp(200, _por_hora(
            "20261114025020", "20261114030020", "20261114235020")),
        "/20261115_by_hour.json": _Resp(200, _por_hora(
            "20261115025020", "20261115030020")),
    })
    monkeypatch.setattr(hr, "_get_session", lambda: s)
    ts, estado = hr.list_local_day("jma_so2", date(2026, 11, 14), 0, 24, CHILE)
    assert estado == "ok"
    assert ts == ["20261114030020", "20261114235020", "20261115025020"]


def test_dia_local_fuera_del_archivo_no_se_reemplaza_por_otro(monkeypatch):
    s = _Sesion({"_by_hour.json": _Resp(404)})
    monkeypatch.setattr(hr, "_get_session", lambda: s)
    assert hr.list_local_day("jma_so2", date(2026, 8, 15), 0, 24, CHILE) == (
        [], "no_conservado")


def test_si_rammb_no_responde_no_se_afirma_que_el_dia_no_existe(monkeypatch):
    s = _Sesion({"/20261114_by_hour.json": ConnectionError("caido"),
                 "/20261115_by_hour.json": _Resp(404)})
    monkeypatch.setattr(hr, "_get_session", lambda: s)
    ts, estado = hr.list_local_day("jma_so2", date(2026, 11, 14), 0, 24, CHILE)
    assert ts == []
    assert estado == "sin_respuesta"


def test_respuesta_parcial_se_marca(monkeypatch):
    """Uno de los dos dias UTC llego y el otro no respondio: se muestra lo
    que hay, pero avisando que puede faltar una parte del dia."""
    s = _Sesion({"/20261114_by_hour.json": _Resp(200, _por_hora(
                     "20261114120020")),
                 "/20261115_by_hour.json": ConnectionError("caido")})
    monkeypatch.setattr(hr, "_get_session", lambda: s)
    ts, estado = hr.list_local_day("jma_so2", date(2026, 11, 14), 0, 24, CHILE)
    assert ts == ["20261114120020"]
    assert estado == "parcial"


# ── Limite real del archivo ──────────────────────────────────────────

def test_tramo_continuo_y_dias_sueltos():
    fechas = ([date(2025, 7, d) for d in range(16, 29)]
              + [date(2026, 6, d) for d in range(1, 26)]
              + [date(2026, 9, 1) + (date(2026, 9, 2) - date(2026, 9, 1)) * i
                 for i in range(76)])
    span = hr.archive_span(fechas)
    assert span["continuo_desde"] == date(2026, 9, 1)
    assert span["continuo_hasta"] == date(2026, 11, 15)
    assert span["dias_continuos"] == 76
    assert span["sueltos"] == [(date(2025, 7, 16), date(2025, 7, 28)),
                               (date(2026, 6, 1), date(2026, 6, 25))]


def test_tramo_de_lista_vacia():
    assert hr.archive_span([]) is None


def test_dia_listado_sin_imagenes_se_detecta(monkeypatch):
    """La lista de RAMMB trae dias cuyos tiles ya se borraron. Un 404 en el
    tile del scan elegido dice 'no hay imagen'; un error de red, 'no se'."""
    b = {"lat_min": -25.6, "lat_max": -24.8, "lon_min": -68.9, "lon_max": -68.1}
    s = _Sesion({"/20260415125020/": _Resp(404),
                 "/20261114125021/": _Resp(200, content=b"x" * 2000)})
    monkeypatch.setattr(hr, "_get_session", lambda: s)
    assert hr.tile_available("jma_so2", "20260415125020", b) is False
    assert hr.tile_available("jma_so2", "20261114125021", b) is True
    assert hr.tile_available("jma_so2", "20261101125021", b) is None


# ── La vista ─────────────────────────────────────────────────────────

def test_selector_ofrece_todo_el_catalogo_con_sugerencias_primero():
    from dashboard.views.replay_reciente import ACTIVE_VOLCANOES, volcan_options
    from src.volcanos import CATALOG
    opciones = volcan_options()
    nombres = [n for n, _ in opciones]
    assert set(nombres) == {v.name for v in CATALOG}
    assert len(nombres) == len(set(nombres))
    assert "Lastarria" in nombres
    sugeridos = [a["name"] for a in ACTIVE_VOLCANOES]
    assert nombres[:len(sugeridos)] == sugeridos


def test_la_vista_no_pide_los_ultimos_n_scans():
    """`latest_times.json` corta en 100 scans (unas 16 h): no sirve para
    revisar un dia elegido. La vista lista por fecha."""
    fuente = (Path(__file__).parent.parent / "dashboard" / "views"
              / "replay_reciente.py").read_text(encoding="utf-8")
    assert "get_latest_timestamps(" not in fuente
    assert "list_local_day(" in fuente
