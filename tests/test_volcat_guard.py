"""Test del guard de coordenadas ausentes en ``volcat_height_at`` (bug hunt jul-2026).

Contexto: el API VOLCAT (get_list/json) puede devolver frames (``endtime``) pero
sin la clave ``coordinates`` — respuesta parcial de SSEC o sector recién creado.
``volcat_at_time`` propaga entonces ``coords=None``. Antes del fix,
``volcat_height_at`` hacía ``coords.get("PROJECTION")`` sobre None → AttributeError
que subía y rompía la vista/validación, en vez de degradar a ``{"note": ...}``
como TODOS los demás caminos de error de la función. Este test pinea que ahora
degrada limpio.
"""

import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import src.fetch.volcat_api as va


def test_volcat_height_at_coords_none_degrada_a_note(monkeypatch):
    """coords=None (API sin 'coordinates') → dict con 'note', NO AttributeError."""
    monkeypatch.setattr(va, "resolve_volcat_sector", lambda v: ("Chile_Central_2km", "ABI"))
    # Frame presente pero sin coords (el estado que dispara el bug).
    monkeypatch.setattr(
        va, "volcat_at_time",
        lambda *a, **k: {"coords": None, "image_url": "http://x/y.png", "gap_min": 0},
    )

    r = va.volcat_height_at("Nevados de Chillan", datetime.now(timezone.utc))
    assert isinstance(r, dict)
    assert "note" in r, r
    assert "coordenadas" in r["note"].lower()


def test_volcat_height_at_no_frame_sigue_dando_note(monkeypatch):
    """Regresión del camino ya existente: sin frame → note (no None ni crash)."""
    monkeypatch.setattr(va, "resolve_volcat_sector", lambda v: ("Chile_Central_2km", "ABI"))
    monkeypatch.setattr(va, "volcat_at_time", lambda *a, **k: None)

    r = va.volcat_height_at("Nevados de Chillan", datetime.now(timezone.utc))
    assert isinstance(r, dict) and "note" in r


def _png_volcat(pintar):
    """PNG VOLCAT sintético 1000x850: mapa gris, leyenda real abajo; ``pintar``
    recibe el array y la (fila, col) de Chillán con la georef de ``_COORDS``."""
    import io

    import numpy as np
    from PIL import Image
    strip = np.asarray(Image.open(Path(__file__).parent / "fixtures"
                                  / "volcat_ash_height_strip.png").convert("RGB"))
    img = np.full((850, 1000, 3), 90, dtype=np.uint8)
    img[850 - strip.shape[0]:] = strip
    pintar(img, 343, 181)
    buf = io.BytesIO()
    Image.fromarray(img).save(buf, format="PNG")
    return buf.getvalue()


# Georef CE: 0,02° por píxel, esquina en (-30, -75): Chillán cae en (343, 181).
_COORDS = {"PROJECTION": "CE", "EQ_RADIUS": 6378.137,
           "SCALE_FACTOR": 6378.137 * 0.02 * 3.141592653589793 / 180.0,
           "ORIGIN_LON": 285.0, "ORIGIN_LAT": -30.0}


def _con_png(monkeypatch, png):
    import requests

    from src.volcanos import get_volcano

    class _R:
        content = png
    monkeypatch.setattr(va, "resolve_volcat_sector", lambda v: ("Chile_Central_2_km", "ABI"))
    monkeypatch.setattr(va, "volcat_at_time", lambda *a, **k: {
        "coords": _COORDS, "image_url": "http://x/y.png",
        "datetime": "2026-11-08_20-30-30", "gap_seconds": 0})
    monkeypatch.setattr(requests, "get", lambda *a, **k: _R())
    return get_volcano("Nevados de Chillan")


def test_volcat_height_at_rechaza_el_manto_sinoptico(monkeypatch):
    """Antes contaba los píxeles de color en una caja de ±0,6°: un manto que
    cubre el sector (Sabancaya/Ubinas/Copahue 16-11) daba una 'altura'."""
    def manto(img, r, c):
        img[50:700, 50:950] = (3, 0, 255)
    v = _con_png(monkeypatch, _png_volcat(manto))
    r = va.volcat_height_at(v, datetime.now(timezone.utc))
    assert r.get("sector_wide") is True and "note" in r


def test_volcat_height_at_da_el_intervalo_del_objeto_anclado(monkeypatch):
    def pluma(img, r, c):
        img[r:r + 3, c:c + 8] = (255, 160, 1)      # 3-4 km, nace en el volcán
        img[100:103, 600:620] = (3, 0, 255)        # nube lejana de 10-12 km
    v = _con_png(monkeypatch, _png_volcat(pluma))
    r = va.volcat_height_at(v, datetime.now(timezone.utc))
    assert (r["top_lo_km"], r["top_hi_km"]) == (3, 4), r
    assert r["frame"] == "2026-11-08_20-30-30"


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-q"]))
