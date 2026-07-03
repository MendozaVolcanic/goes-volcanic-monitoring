"""Test del orden por proximidad temporal de la ventana baseline del comparador.

Bug hunt jul-2026: ``_build_target_ts_window`` ordenaba por
``abs(int(ts)-int(target))`` sobre cadenas ``YYYYMMDDHHMMSS``. Esa distancia NO
es proporcional al tiempo real cuando la ventana cruza un límite de hora/día/mes
(p.ej. medianoche de fin de mes): un frame 10 min ANTES podía rankear detrás de
uno 2 h después. El fix compara segundos reales vía ``datetime``.
"""

import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dashboard.views.comparador import _build_target_ts_window


def _dist_real_s(ts: str, target: datetime) -> float:
    return abs((datetime.strptime(ts, "%Y%m%d%H%M%S") - target).total_seconds())


def test_orden_por_tiempo_real_cruzando_fin_de_mes():
    """target = medianoche del 1-jul (fin de mes previo): el frame -10 min
    (30-jun 23:50) debe rankear ANTES que cualquier frame +horas del mismo día."""
    target = datetime(2026, 7, 1, 0, 0, 0)
    ordered = _build_target_ts_window(target, window_hours=2)

    # El primer elemento es el target exacto (dist 0).
    assert ordered[0] == "20260701000000"
    # El segundo/tercero deben ser los ±10 min reales (23:50 del 30-jun y 00:10),
    # NO un frame de +1/+2 h que el int-sort ponía delante.
    near = set(ordered[1:3])
    assert "20260630235000" in near, ordered[:5]  # 10 min antes, cruza el mes
    assert "20260701001000" in near, ordered[:5]  # 10 min después

    # Invariante fuerte: la lista queda monótona en distancia temporal real.
    dists = [_dist_real_s(ts, target) for ts in ordered]
    assert dists == sorted(dists), list(zip(ordered, dists))[:6]


def test_orden_dentro_del_dia_sigue_bien():
    """Sanity: lejos de bordes el orden también es monótono."""
    target = datetime(2026, 6, 15, 12, 0, 0)
    ordered = _build_target_ts_window(target, window_hours=2)
    dists = [_dist_real_s(ts, target) for ts in ordered]
    assert dists == sorted(dists)
    assert ordered[0] == "20260615120000"


if __name__ == "__main__":
    test_orden_por_tiempo_real_cruzando_fin_de_mes()
    test_orden_dentro_del_dia_sigue_bien()
    print("OK — comparador window")
