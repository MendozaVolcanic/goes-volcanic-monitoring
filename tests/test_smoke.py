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
    "dashboard.views.overview",
    "dashboard.views.ash_viewer",
    "dashboard.views.volcat_viewer",
    "dashboard.views.rammb_viewer",
    "dashboard.views.timeseries_viewer",
    "dashboard.views.modo_guardia",
    # modo_guardia_volcan y mosaico_chile son submodulos privados:
    # ya no se invocan como tabs sueltas, se llaman desde modo_guardia
    "dashboard.views.modo_guardia_volcan",
    "dashboard.views.mosaico_chile",
]

FETCHERS = [
    "src.fetch.goes_s3",
    "src.fetch.goes_fdcf",
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


if __name__ == "__main__":
    for m in VIEWS + FETCHERS + PROCESSORS + EXPORTERS:
        test_module_imports(m)
    test_views_have_render()
    test_style_has_required_helpers()
    print("OK — smoke tests passed")
