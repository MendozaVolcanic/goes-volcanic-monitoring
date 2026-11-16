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
    pintar(img, 286, 480)
    buf = io.BytesIO()
    Image.fromarray(img).save(buf, format="PNG")
    return buf.getvalue()


# Georef tal cual la entrega SSEC para Chile_Central_2_km (listado del 16-11-2026).
# OJO: EQ_RADIUS = 206264,8 son SEGUNDOS DE ARCO por radián, así que SCALE_FACTOR
# (72,8) es el píxel en segundos de arco (0,0202°), NO en km. Con esta georef
# Chillán (-36,86; -71,38) cae en la fila 286, columna 480.
_COORDS = {"PROJECTION": "CE", "REF_LON": 289, "ORIGIN_LAT": -31.8007698059082,
           "ORIGIN_LON": 278.9210815429688, "EQ_RADIUS": 206264.796875,
           "SCALE_FACTOR": 72.80000305175781, "OFFSET_X": 0, "OFFSET_Y": 36}


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


def test_el_radio_de_anclaje_va_en_km_reales(monkeypatch):
    """Pluma que empieza 3 píxeles (~6,7 km) al sur del volcán, como Chillán
    08-11 16:30 por paralaje. Con el radio de 10 km se ancla. El bug era tomar
    SCALE_FACTOR (segundos de arco) como km: 72,8 km por píxel dejaba el radio
    en 1 píxel y la pluma no se anclaba."""
    def pluma_corrida(img, r, c):
        img[r + 3:r + 6, c:c + 8] = (255, 160, 1)
    v = _con_png(monkeypatch, _png_volcat(pluma_corrida))
    r = va.volcat_height_at(v, datetime.now(timezone.utc))
    assert (r.get("top_lo_km"), r.get("top_hi_km")) == (3, 4), r


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-q"]))
