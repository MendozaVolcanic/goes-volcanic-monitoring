"""Build hi-res visible cache: 8 priority volcanoes desde NOAA L1b.

mode 'color' (default): true-color PAN-SHARPENED a 0.5 km/px (color de
bandas 1+2+3 a 1 km + detalle de banda 2 nativa 0.5 km via High-Pass
Modulation) = 4× RAMMB zoom 4 efectivo. mode 'mono_05km': banda 2 sola
sepia a 0.5 km/px.

Cron sugerido: cada 30 min (cron '17,47 * * * *').

Salida: out_hires/<volcan_slug>__hires__<ts>.png + manifest.json.
Despues sube como assets a release rolling `hires-rolling`.

Cada miniatura ~150-300 KB PNG -> 8 scopes × 1 timestamp = ~2 MB por run.
Rolling 12h × 24 runs = ~50 MB. Cabe holgado.
"""

from __future__ import annotations

import io
import json
import logging
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from PIL import Image

from src.fetch.goes_s3 import get_latest_time
from src.process.hires_pipeline import build_hires_for_scopes
from src.volcanos import get_priority

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("hires_cache")

OUT_DIR = ROOT / "out_hires"
RADIUS_DEG = 0.5  # ±55 km bbox por volcan


def _save_png(arr, path: Path) -> int:
    img = Image.fromarray(arr)
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=False, compress_level=6)
    data = buf.getvalue()
    path.write_bytes(data)
    return len(data)


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["color", "mono_05km"], default="color",
                    help="color: TrueColor 1km/px (day) + IR (night). "
                         "mono_05km: banda 2 sola a 0.5km/px sepia (4× zoom real, solo dia).")
    ap.add_argument("--no-clean", action="store_true",
                    help="No borrar out_hires/ al inicio. Util para chainear modes "
                         "(corre color, despues mono, ambos terminan en el mismo dir).")
    args = ap.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    # Limpiar — cada build es snapshot completo (a menos que --no-clean)
    if not args.no_clean:
        for p in OUT_DIR.glob("*"):
            p.unlink()

    # 1. Determinar el scan mas reciente disponible en S3
    dt = get_latest_time()
    if dt is None:
        # Fallback: ahora -1h (S3 publica con ~3-5 min latencia)
        dt = datetime.now(timezone.utc) - timedelta(minutes=15)
        log.warning("get_latest_time fallo, usando %s", dt)
    else:
        log.info("Scan mas reciente disponible S3: %s", dt.isoformat())

    # 2. Construir scopes para los 8 prioritarios
    priority = get_priority()
    if len(priority) != 8:
        log.warning("Esperaba 8 prioritarios, hay %d", len(priority))
    scopes = {
        "".join(c if c.isalnum() else "_" for c in v.name.lower()):
            {"lat": v.lat, "lon": v.lon, "name": v.name}
        for v in priority
    }

    # 3. Build (devuelve imagenes + metadata por scope con sun_alt + render type)
    log.info("Procesando hi-res para %d scopes mode=%s...", len(scopes), args.mode)
    results, results_meta = build_hires_for_scopes(
        dt, scopes, radius_deg=RADIUS_DEG, mode=args.mode,
    )

    # 4. Guardar — sufijo del filename indica el mode
    ts_str = dt.strftime("%Y%m%d%H%M%S")
    suffix = "hires_mono" if args.mode == "mono_05km" else "hires"
    available = []
    total_bytes = 0
    for sid, arr in results.items():
        if arr is None:
            meta = results_meta.get(sid, {})
            log.warning("[%s] sin imagen (sun=%s, render=%s)", sid,
                        meta.get("sun_alt"), meta.get("render"))
            continue
        fname = f"{sid}__{suffix}__{ts_str}.png"
        nb = _save_png(arr, OUT_DIR / fname)
        total_bytes += nb
        available.append(sid)

    # 5. Manifest (key segun mode para no pisar el otro cache)
    manifest = {
        "generated_utc": datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"),
        "mode": args.mode,
        "scan_ts": ts_str,
        "scan_dt_iso": dt.isoformat(),
        "radius_deg": RADIUS_DEG,
        "scopes": {
            sid: {
                "lat": scopes[sid]["lat"],
                "lon": scopes[sid]["lon"],
                "name": scopes[sid]["name"],
                "available": sid in available,
                # Metadata del render: sun_alt + tipo (visible_color, ir_pseudo,
                # visible_mono, skip_night, no_data, error). El dashboard usa
                # esto para mostrar al usuario QUE tipo de imagen esta viendo.
                "sun_alt": results_meta.get(sid, {}).get("sun_alt"),
                "render": results_meta.get(sid, {}).get("render"),
            }
            for sid in scopes
        },
    }
    # Manifest filename: manifest.json para color (compat), manifest_mono.json
    # para mono_05km. Asi cohabitan ambos modos en el mismo release.
    manifest_name = "manifest_mono.json" if args.mode == "mono_05km" else "manifest.json"
    (OUT_DIR / manifest_name).write_text(json.dumps(manifest, indent=2))

    log.info("DONE. %d/%d scopes OK, %.1f MB total",
             len(available), len(scopes), total_bytes / 1e6)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
