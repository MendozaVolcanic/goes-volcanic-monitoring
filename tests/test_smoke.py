"""Smoke tests: importar todos los modulos del dashboard sin crash.

Si una vista tira ImportError o NameError al importarse, el deploy de
Streamlit Cloud falla con una pantalla en blanco. Estos tests se ejecutan
en CI antes de mergear y atrapan eso temprano.

NO ejecutamos render() — eso requiere contexto Streamlit corriendo.
Solo verificamos que el modulo carga limpio.
"""

import importlib
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))


VIEWS = [
    "dashboard.views.live_viewer",
    "dashboard.views.ash_viewer",
    "dashboard.views.volcat_viewer",
    "dashboard.views.rammb_viewer",
    "dashboard.views.timeseries_viewer",
    "dashboard.views.modo_guardia",
    # modo_guardia_volcan y mosaico_chile son submodulos privados:
    # ya no se invocan como tabs sueltas, se llaman desde modo_guardia
    "dashboard.views.modo_guardia_volcan",
    "dashboard.views.mosaico_chile",
    "dashboard.views.comparador",
    "dashboard.views.loop_volcan",
    "dashboard.views.replay_reciente",
    "dashboard.views.modo_evento",
    "dashboard.views.heatmap_actividad",
    "dashboard.views.zonas_fullscreen",
]

FETCHERS = [
    "src.fetch.goes_s3",
    "src.fetch.goes_fdcf",
    "src.fetch.frp_timeline",
    "src.fetch.rammb_slider",
    "src.fetch.realearth_api",
    "src.fetch.timeseries",
    "src.fetch.volcat_api",
    "src.fetch.wind_data",
]

PROCESSORS = [
    "src.process.ash_detection",
    "src.process.ash_rgb",
    "src.process.brightness_temp",
    "src.process.geo",
    "src.process.pipeline",
]

EXPORTERS = [
    "src.export.geotiff",
]


@pytest.mark.parametrize("module_name", VIEWS + FETCHERS + PROCESSORS + EXPORTERS)
def test_module_imports(module_name):
    """Cada modulo debe importarse sin excepcion."""
    mod = importlib.import_module(module_name)
    assert mod is not None


def test_views_have_render():
    """Cada vista del dashboard debe exponer una funcion render()."""
    for name in VIEWS:
        mod = importlib.import_module(name)
        assert hasattr(mod, "render"), f"{name} no tiene render()"
        assert callable(mod.render), f"{name}.render no es callable"


def test_style_has_required_helpers():
    """dashboard.style debe exponer los helpers que usan las vistas."""
    from dashboard import style

    required = ["inject_css", "header", "info_panel", "kpi_card", "C_ACCENT"]
    for name in required:
        assert hasattr(style, name), f"dashboard.style.{name} faltante"


def test_frp_sum_per_volcano():
    """sum_frp_per_volcano: suma FRP y cuenta hotspots dentro del radio."""
    from dataclasses import dataclass

    from src.fetch.frp_timeline import sum_frp_per_volcano

    @dataclass
    class _HS:
        lat: float
        lon: float
        frp_mw: float

    @dataclass
    class _Volc:
        name: str
        lat: float
        lon: float

    v = _Volc("Test", -39.42, -71.93)  # ~Villarrica
    # dos hotspots encima del volcán + uno a ~500 km (fuera del radio)
    hotspots = [
        _HS(v.lat, v.lon, 20.0),
        _HS(v.lat + 0.05, v.lon, 5.0),
        _HS(v.lat + 5.0, v.lon, 99.0),
    ]
    frp, counts = sum_frp_per_volcano(hotspots, [v], radius_km=50)
    assert frp["Test"] == 25.0, frp
    assert counts["Test"] == 2, counts

    # sin hotspots → cero, no excepción
    frp0, c0 = sum_frp_per_volcano([], [v], radius_km=50)
    assert frp0["Test"] == 0.0 and c0["Test"] == 0


def test_frp_daily_rollup():
    """daily_rollup: cuenta scans con detección por día y volcán."""
    from src.fetch.frp_timeline import daily_rollup

    scans = [
        {"t": "2026-06-08T10:00:00Z", "n": {"Lascar": 1, "Llaima": 0}},
        {"t": "2026-06-08T10:10:00Z", "n": {"Lascar": 2, "Llaima": 0}},
        {"t": "2026-06-08T10:20:00Z", "n": {"Lascar": 0, "Llaima": 0}},
        {"t": "2026-06-07T23:50:00Z", "n": {"Lascar": 1}},
    ]
    roll = daily_rollup(scans)
    # 08: Lascar detectado en 2 scans (10:00 y 10:10); Llaima nunca → ausente
    assert roll["2026-06-08"]["Lascar"] == 2, roll
    assert "Llaima" not in roll["2026-06-08"], roll
    # 07: Lascar 1 scan
    assert roll["2026-06-07"]["Lascar"] == 1, roll
    # vacío no rompe
    assert daily_rollup([]) == {}


def test_frp_timeline_view_builds_with_empty():
    """La sección de timeline no debe romper con lista de scans vacía."""
    import dashboard.views.heatmap_actividad as H

    # _load_frp_timeline tolera ausencia de archivo
    assert isinstance(H._load_frp_timeline(), dict)


def test_hires_crop_centered_aligns():
    """_crop_centered: recorte central por fracción lineal (hi-res → vista)."""
    import numpy as np

    import dashboard.views.modo_guardia_volcan as MGV

    arr = np.zeros((100, 80, 3), dtype="uint8")
    out = MGV._crop_centered(arr, 0.7)
    assert out.shape == (70, 56, 3), out.shape
    # frac=1 devuelve igual; frac fuera de rango se clampa sin romper
    assert MGV._crop_centered(arr, 1.0).shape == (100, 80, 3)
    assert MGV._crop_centered(arr, 5.0).shape == (100, 80, 3)
    assert MGV._crop_centered(arr, 0.0).shape[0] >= 1  # clamp inferior


def test_volcat_frame_dt_parser():
    """_parse_volcat_frame_dt: '2026-05-11_12-00-30' -> datetime UTC."""
    from datetime import timezone

    from src.fetch.volcat_api import _parse_volcat_frame_dt

    dt = _parse_volcat_frame_dt("2026-06-07_07-50-30")
    assert dt is not None
    assert (dt.year, dt.month, dt.day, dt.hour, dt.minute) == (2026, 6, 7, 7, 50)
    assert dt.tzinfo == timezone.utc
    assert _parse_volcat_frame_dt(None) is None
    assert _parse_volcat_frame_dt("basura") is None


def test_compose_volcan_panels():
    """_compose_volcan_panels: 3 paneles -> 1 imagen PIL, aspecto ~2.2, tolera
    panel sin imagen."""
    import numpy as np

    import dashboard.views.zonas_fullscreen as Z
    from src.volcanos import get_volcano

    v = get_volcano("Villarrica")
    img = np.zeros((60, 46, 3), dtype="uint8")
    panels = [("Ash RGB", img, "22:30 UTC", []),
              ("GeoColor", img, "22:30 UTC ✨ hi-res", []),
              ("SO2 RGB", None, "sin scan", [])]
    out = Z._compose_volcan_panels(v, 0.35, panels)
    w, h = out.size
    assert out.mode == "RGB"
    assert 1.8 < (w / h) < 2.6, (w, h)  # ~2.2, ancho para el TV


def test_hires_age_min():
    """_hires_age_min: edad en minutos, robusto a iso sin tz / ausente."""
    from datetime import datetime, timezone

    import dashboard.views.modo_guardia_volcan as MGV

    now = datetime(2026, 6, 8, 21, 40, tzinfo=timezone.utc)
    assert MGV._hires_age_min(
        {"scan_dt_iso": "2026-06-08T21:00:00+00:00"}, now) == 40
    assert MGV._hires_age_min({}, now) is None
    assert MGV._hires_age_min({"scan_dt_iso": "basura"}, now) is None


if __name__ == "__main__":
    for m in VIEWS + FETCHERS + PROCESSORS + EXPORTERS:
        test_module_imports(m)
    test_views_have_render()
    test_style_has_required_helpers()
    test_frp_sum_per_volcano()
    test_frp_daily_rollup()
    test_frp_timeline_view_builds_with_empty()
    print("OK — smoke tests passed")
