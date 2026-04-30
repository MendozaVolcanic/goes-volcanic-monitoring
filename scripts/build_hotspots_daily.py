"""Pre-cocinar conteo diario de hot spots NOAA FDCF por volcán.

Output: data/hotspots_daily.json con estructura:
  {
    "last_updated_utc": "2026-04-30T03:00:00Z",
    "days": {
      "2026-04-30": {
        "Villarrica": 0,
        "Lascar": 2,
        ...
      },
      "2026-04-29": { ... },
      ...
    }
  }

Pensado para correr diario via GitHub Action. Mergea con archivo
existente: agrega el dia actual + 7 dias atras (rolling window 30 dias
si quisieramos ir mas lejos).

Cada dia escanea hasta ~24 archivos FDCF S3 (1 por hora). Usa el helper
de fetch_latest_hotspots con hours_back. Por simplicidad, agregamos los
ultimos 24h como "hoy" — no es perfecto cronologicamente (no respeta
exactamente el dia UTC 00:00-23:59) pero es buena aproximacion.

Uso:
    python scripts/build_hotspots_daily.py
"""

import json
import logging
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.fetch.goes_fdcf import fetch_latest_hotspots
from src.volcanos import PRIORITY_VOLCANOES, get_volcano

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("hotspots_daily")

OUTPUT_PATH = Path(__file__).parent.parent / "data" / "hotspots_daily.json"
RADIUS_KM = 50

# Bbox Chile + paises vecinos cubiertos por GOES-19
CHILE_BBOX = {
    "lat_min": -56, "lat_max": -17,
    "lon_min": -76, "lon_max": -66,
}


def fetch_hotspots_for_day(day: datetime, lookback_hours: int = 24) -> list:
    """Hot spots NOAA FDCF — usa hours_back para aproximar el dia."""
    try:
        hs, _ = fetch_latest_hotspots(
            bounds=CHILE_BBOX, hours_back=lookback_hours,
        )
        return hs
    except Exception as e:
        log.warning("Error fetching hotspots: %s", e)
        return []


def count_per_volcano(hotspots: list) -> dict[str, int]:
    counts = {}
    for name in PRIORITY_VOLCANOES:
        v = get_volcano(name)
        if v is None:
            continue
        n = 0
        for h in hotspots:
            dlat = (h.lat - v.lat) * 111.0
            dlon = (h.lon - v.lon) * 111.0 * float(np.cos(np.radians(v.lat)))
            d = float(np.hypot(dlat, dlon))
            if d <= RADIUS_KM:
                n += 1
        counts[name] = n
    return counts


def load_existing() -> dict:
    if not OUTPUT_PATH.exists():
        return {"last_updated_utc": None, "days": {}}
    try:
        return json.loads(OUTPUT_PATH.read_text())
    except Exception as e:
        log.warning("Archivo existente corrupto, regenerando: %s", e)
        return {"last_updated_utc": None, "days": {}}


def save(data: dict) -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    log.info("Guardado: %s", OUTPUT_PATH)


def prune_old(data: dict, keep_days: int = 30) -> dict:
    """Mantener solo los ultimos N dias en el archivo (rolling window)."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=keep_days)
    data["days"] = {
        day: counts for day, counts in data["days"].items()
        if datetime.strptime(day, "%Y-%m-%d").replace(tzinfo=timezone.utc) >= cutoff
    }
    return data


def main():
    log.info("Iniciando build de hotspots_daily.json")
    data = load_existing()

    today_utc = datetime.now(timezone.utc)
    today_key = today_utc.strftime("%Y-%m-%d")

    log.info("Bajando hot spots ultimas 24h...")
    hotspots = fetch_hotspots_for_day(today_utc, lookback_hours=24)
    log.info("Total hot spots: %d", len(hotspots))

    counts = count_per_volcano(hotspots)
    log.info("Por volcan: %s", counts)

    data["days"][today_key] = counts
    data["last_updated_utc"] = today_utc.strftime("%Y-%m-%dT%H:%M:%SZ")

    data = prune_old(data, keep_days=30)
    save(data)
    log.info("Done. %d dias en archivo.", len(data["days"]))


if __name__ == "__main__":
    main()
