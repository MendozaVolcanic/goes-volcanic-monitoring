"""Tests del guard de frescura de la serie FRP pre-cocinada (audit ago-2026).

Por qué importa (SDA): el cron `frp_timeline.yml` actualiza data/frp_timeline.json
cada 10 min en `main`, pero el deploy de HF es un snapshot. Antes de este fix la
vista leía SOLO el archivo local congelado, así que el panel mostraba el pulso
térmico del día del último deploy — y una serie de semanas atrás con 0 MW se
presentaba como "✅ Calma térmica", que para un guardia significa "no hay actividad".

`_frp_age_hours` es la pieza que decide si el dato sirve para afirmar calma. Es
pura (solo lee `last_updated_utc` del dict) y se testea sin red.
"""

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dashboard.views.heatmap_actividad import FRP_STALE_HOURS, _frp_age_hours


def _iso(hours_ago: float, suffix: str = "Z") -> str:
    ts = datetime.now(timezone.utc) - timedelta(hours=hours_ago)
    return ts.replace(microsecond=0).isoformat().replace("+00:00", "") + suffix


def test_age_reciente_no_es_stale():
    """Serie de hace 10 min → edad ~0.17 h, por debajo del umbral."""
    age = _frp_age_hours({"last_updated_utc": _iso(10 / 60)})
    assert age is not None
    assert 0 <= age < 0.5
    assert age <= FRP_STALE_HOURS


def test_age_vieja_supera_el_umbral():
    """Serie de hace 30 h (deploy viejo sin refresh) → stale."""
    age = _frp_age_hours({"last_updated_utc": _iso(30)})
    assert age is not None
    assert age > FRP_STALE_HOURS
    assert 29 < age < 31


def test_age_acepta_offset_explicito():
    """`+00:00` en vez de `Z` también parsea (formato isoformat de Python)."""
    ts = (datetime.now(timezone.utc) - timedelta(hours=5)).replace(microsecond=0)
    age = _frp_age_hours({"last_updated_utc": ts.isoformat()})
    assert age is not None and 4.5 < age < 5.5


def test_age_naive_se_asume_utc():
    """Timestamp sin tz no debe romper: se interpreta como UTC."""
    ts = (datetime.now(timezone.utc) - timedelta(hours=2)).replace(
        microsecond=0, tzinfo=None)
    age = _frp_age_hours({"last_updated_utc": ts.isoformat()})
    assert age is not None and 1.5 < age < 2.5


def test_age_none_cuando_falta_o_no_parsea():
    """Sin campo, dict vacío, None o basura → None (la vista no afirma nada)."""
    assert _frp_age_hours({}) is None
    assert _frp_age_hours(None) is None
    assert _frp_age_hours({"last_updated_utc": ""}) is None
    assert _frp_age_hours({"last_updated_utc": "no-es-fecha"}) is None


def test_umbral_es_coherente_con_la_cadencia_del_cron():
    """El umbral debe ser holgado vs la cadencia de 10 min pero detectar el
    escenario real (snapshot de días/semanas)."""
    assert 1.0 <= FRP_STALE_HOURS <= 12.0


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-q"]))
