"""Cache ROLLING de loops hi-res GeoColor 0.5 km (release `hires-loop-rolling`).

A diferencia de build_hires_cache.py (snapshot: solo el ultimo scan), este
mantiene una VENTANA RODANTE de ~8 h de frames GeoColor 0.5 km pan-sharpened
para los 8 volcanes prioritarios -> permite armar LOOPS hi-res, no solo el
still del Modo Guardia.

INCREMENTAL (clave): NO re-genera toda la ventana cada corrida — cada frame
0.5 km cuesta ~330 MB de L1b. Genera SOLO el frame del scan mas reciente (1
descarga de bandas sirve a los 8 volcanes), lo agrega al ZIP rodante (bajado
del release), poda lo > ROLL_HOURS, y re-sube el set completo (la action
gh-release-snapshot borra+sube todo, por eso el ZIP debe traer la ventana
entera).

Cadencia: cada ~30 min (junto con build_hires_cache.py). En ~8 h el loop se
llena (~16 frames a 30 min).

Salida: out_hires_loop/<slug>__geocolor05.zip (frames {ts}.png) + manifest_loop.json
"""
from __future__ import annotations

import io
import json
import logging
import sys
import zipfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import requests
from PIL import Image

from src.fetch.goes_s3 import get_latest_time
from src.process.hires_pipeline import build_hires_for_scopes
from src.volcanos import get_priority

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("hires_loop_cache")

OUT_DIR = ROOT / "out_hires_loop"
RADIUS_DEG = 0.5            # mismo radio que el still hi-res (0.5° ≈ 55 km)
ROLL_HOURS = 8             # retencion de la ventana rodante
RELEASE_TAG = "hires-loop-rolling"
CDN_BASE = ("https://github.com/MendozaVolcanic/goes-volcanic-monitoring"
            f"/releases/download/{RELEASE_TAG}")


def _slug(name: str) -> str:
    return "".join(c if c.isalnum() else "_" for c in name.lower())


def _zip_name(slug: str) -> str:
    return f"{slug}__geocolor05.zip"


def _download_existing(slug: str) -> dict[str, bytes]:
    """{ts: png_bytes} del ZIP rodante actual del release (vacio si 404)."""
    try:
        r = requests.get(f"{CDN_BASE}/{_zip_name(slug)}", timeout=40)
        if r.status_code != 200:
            return {}
        out = {}
        with zipfile.ZipFile(io.BytesIO(r.content)) as zf:
            for n in zf.namelist():
                if n.endswith(".png"):
                    out[n[:-4]] = zf.read(n)
        return out
    except Exception as e:
        log.warning("no pude bajar ZIP existente de %s: %s", slug, e)
        return {}


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for p in OUT_DIR.glob("*"):
        p.unlink()

    dt = get_latest_time()
    if dt is None:
        dt = datetime.now(timezone.utc) - timedelta(minutes=15)
        log.warning("get_latest_time fallo, uso %s", dt)
    ts_str = dt.strftime("%Y%m%d%H%M%S")
    log.info("Scan mas reciente: %s", dt.isoformat())

    priority = get_priority()
    scopes = {_slug(v.name): {"lat": v.lat, "lon": v.lon, "name": v.name}
              for v in priority}

    # Genera el frame 0.5 km del scan actual para los 8 (UNA descarga de bandas).
    log.info("Generando frame 0.5km para %d volcanes...", len(scopes))
    images, meta = build_hires_for_scopes(dt, scopes, radius_deg=RADIUS_DEG,
                                          mode="color")

    cutoff = (dt - timedelta(hours=ROLL_HOURS)).strftime("%Y%m%d%H%M%S")
    manifest_scopes: dict[str, dict] = {}
    total_frames = 0
    for slug, sinfo in scopes.items():
        frames = _download_existing(slug)            # ventana rodante actual
        arr = images.get(slug)
        m = meta.get(slug, {})
        # Solo sumamos frames VISIBLES diurnos (el loop hi-res es visible; de
        # noche el modo color cae a IR 2km que no es lo que queremos en el loop).
        if arr is not None and m.get("render") == "visible_color":
            buf = io.BytesIO()
            Image.fromarray(arr).save(buf, format="PNG")
            frames[ts_str] = buf.getvalue()
        # Podar lo mas viejo que la ventana.
        frames = {ts: b for ts, b in frames.items() if ts >= cutoff}
        if not frames:
            continue
        with zipfile.ZipFile(OUT_DIR / _zip_name(slug), "w",
                             zipfile.ZIP_STORED) as zf:
            for ts, b in sorted(frames.items()):
                zf.writestr(f"{ts}.png", b)
        manifest_scopes[slug] = {
            "name": sinfo["name"], "lat": sinfo["lat"], "lon": sinfo["lon"],
            "ts": sorted(frames.keys()),
        }
        total_frames += len(frames)

    manifest = {
        "updated_utc": datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"),
        "scan_ts": ts_str,
        "radius_deg": RADIUS_DEG,
        "roll_hours": ROLL_HOURS,
        "scopes": manifest_scopes,
    }
    (OUT_DIR / "manifest_loop.json").write_text(json.dumps(manifest, indent=2))
    log.info("DONE. %d volcanes, %d frames totales en la ventana de %dh",
             len(manifest_scopes), total_frames, ROLL_HOURS)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
