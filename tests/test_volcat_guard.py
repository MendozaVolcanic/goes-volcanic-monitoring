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


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-q"]))
