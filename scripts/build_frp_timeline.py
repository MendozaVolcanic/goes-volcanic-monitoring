"""Pre-cocinar la serie temporal intradía de FRP por volcán (cadencia GOES).

Por qué: GOES ve el mismo punto cada 10 min. Esta serie es la fortaleza
ÚNICA de GOES frente a MODIS/VIIRS — captura la EVOLUCIÓN intradía de un
evento efusivo. Ver docstring de src/fetch/frp_timeline.py.

Diseño INCREMENTAL (barato y auto-sanante): cada corrida baja sólo los scans
nuevos de las últimas ``--backfill-hours`` (default 3h ≈ 18 scans), los agrega
a la ventana rodante de ``--window-hours`` (default 48h) y poda lo viejo. Si
una corrida del workflow se saltea, la siguiente cubre el hueco (mientras el
gap < backfill). La ventana se llena sola con el correr de las corridas.

Cada scan se lee RECORTADO a la región de Chile (~2 s/scan vs ~15 s del
lector full-disk) vía fetch_scan_sliced.

Output: data/frp_timeline.json
  {
    "last_updated_utc": "2026-06-08T18:00:00Z",
    "window_hours": 48, "radius_km": 50, "step_min": 10,
    "scans": [
      {"t": "2026-06-08T17:50:00Z",
       "frp": {"Villarrica": 12.3, "Lascar": 0.0, ...},
       "n":   {"Villarrica": 1,    "Lascar": 0,   ...}},
      ...
    ]
  }

Uso:
    python scripts/build_frp_timeline.py                       # incremental 3h
    python scripts/build_frp_timeline.py --backfill-hours 12   # bootstrap
    python scripts/build_frp_timeline.py --step-min 20         # muestreo ralo
"""

import argparse
import json
import logging
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.fetch.frp_timeline import (
    CHILE_BBOX,
    daily_rollup,
    fetch_scan_sliced,
    sum_frp_per_volcano,
)
from src.volcanos import get_priority

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("frp_timeline")

OUTPUT_PATH = Path(__file__).parent.parent / "data" / "frp_timeline.json"
ISO = "%Y-%m-%dT%H:%M:%SZ"


def load_existing() -> dict:
    if not OUTPUT_PATH.exists():
        return {"scans": []}
    try:
        d = json.loads(OUTPUT_PATH.read_text())
        d.setdefault("scans", [])
        return d
    except Exception as e:
        log.warning("Archivo existente corrupto, regenerando: %s", e)
        return {"scans": []}


def save(data: dict) -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    log.info("Guardado: %s (%d scans)", OUTPUT_PATH, len(data["scans"]))


def _round_to_step(dt: datetime, step_min: int) -> datetime:
    """Redondea al múltiplo de step más cercano (para dedupe estable)."""
    m = round(dt.minute / step_min) * step_min
    return dt.replace(minute=0, second=0, microsecond=0) + timedelta(minutes=m)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--backfill-hours", type=float, default=3.0)
    ap.add_argument("--window-hours", type=float, default=48.0)
    ap.add_argument("--step-min", type=int, default=10)
    ap.add_argument("--radius-km", type=float, default=50.0)
    args = ap.parse_args()

    volcanoes = get_priority()
    log.info("Volcanes prioritarios: %s", [v.name for v in volcanoes])

    data = load_existing()
    existing = {s["t"]: s for s in data["scans"]}

    now = datetime.now(timezone.utc).replace(second=0, microsecond=0)
    start = now - timedelta(hours=args.backfill_hours)

    # Construir lista de timestamps objetivo (paso step_min) en la ventana de
    # backfill. Saltear los que ya están en el archivo.
    n_steps = int((now - start).total_seconds() // (args.step_min * 60)) + 1
    fetched = 0
    for i in range(n_steps):
        target = start + timedelta(minutes=i * args.step_min)
        try:
            hs, scan_dt = fetch_scan_sliced(target, bounds=CHILE_BBOX)
        except Exception as e:
            log.warning("scan %s falló: %s", target.isoformat(), e)
            continue
        if scan_dt is None:
            continue
        key = _round_to_step(scan_dt, args.step_min).strftime(ISO)
        if key in existing:
            continue  # ya lo teníamos
        frp, counts = sum_frp_per_volcano(hs, volcanoes, radius_km=args.radius_km)
        existing[key] = {"t": key, "frp": frp, "n": counts}
        fetched += 1
        total = sum(frp.values())
        if total > 0:
            log.info("  %s  FRP_total=%.1f MW  %s", key, total,
                     {k: v for k, v in frp.items() if v > 0})

    # Podar ventana rodante de scans (para la curva intradía)
    cutoff = (now - timedelta(hours=args.window_hours)).strftime(ISO)
    scans = sorted(
        (s for s in existing.values() if s["t"] >= cutoff),
        key=lambda s: s["t"],
    )

    # ── Roll-up diario (para el heatmap semanal) ─────────────────────────
    # Fuente ÚNICA: derivamos el conteo diario de los mismos scans de 10 min,
    # NO de un solo scan. Sólo refrescamos HOY y AYER: son los únicos días que
    # la ventana de 48h cubre por completo (días más viejos quedaron fijados
    # cuando fueron "ayer" en corridas previas; no los pisamos con datos
    # parciales). Ventana persistente: 30 días.
    daily = dict(data.get("daily", {}))
    window_daily = daily_rollup(scans)
    today_str = now.strftime("%Y-%m-%d")
    yesterday_str = (now - timedelta(days=1)).strftime("%Y-%m-%d")
    for day in (today_str, yesterday_str):
        if day in window_daily:
            daily[day] = window_daily[day]
        elif day == today_str:
            daily.setdefault(day, {})  # hoy sin actividad → registrado vacío
    cutoff_day = (now - timedelta(days=30)).strftime("%Y-%m-%d")
    daily = {k: v for k, v in sorted(daily.items()) if k >= cutoff_day}

    out = {
        "last_updated_utc": now.strftime(ISO),
        "window_hours": args.window_hours,
        "radius_km": args.radius_km,
        "step_min": args.step_min,
        "scans": scans,
        "daily": daily,
    }
    save(out)
    log.info("Done. %d scans nuevos, %d en ventana, %d días en roll-up.",
             fetched, len(scans), len(daily))


if __name__ == "__main__":
    main()
