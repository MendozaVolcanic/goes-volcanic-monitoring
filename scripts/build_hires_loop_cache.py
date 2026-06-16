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
ROLL_HOURS = 12            # retencion (≈ presets max RAMMB). 24 frames a 30 min
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


def _clean_raw() -> None:
    """Borrar las bandas L1b descargadas (liberar disco entre scans en backfill)."""
    try:
        from src.config import RAW_DIR
        for p in Path(RAW_DIR).glob("OR_ABI-L1b-RadF-*"):
            try:
                p.unlink()
            except OSError:
                pass
    except Exception:
        pass


def _any_daylight(dt: datetime, priority) -> bool:
    """True si ALGUN volcan prioritario tiene sol >= 5° (habria frame visible)."""
    from src.process.geocolor_lite import solar_elevation
    return any(solar_elevation(v.lat, v.lon, dt) >= 5.0 for v in priority)


def _generate_scan(dt: datetime, scopes: dict) -> tuple[str, dict[str, bytes]]:
    """Frames 0.5km VISIBLES de un scan -> (ts_str, {slug: png_bytes})."""
    ts_str = dt.strftime("%Y%m%d%H%M%S")
    images, meta = build_hires_for_scopes(dt, scopes, radius_deg=RADIUS_DEG,
                                          mode="color")
    out = {}
    for slug, arr in images.items():
        if arr is not None and meta.get(slug, {}).get("render") == "visible_color":
            buf = io.BytesIO()
            Image.fromarray(arr).save(buf, format="PNG")
            out[slug] = buf.getvalue()
    return ts_str, out


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--backfill-hours", type=float, default=0.0,
                    help="Si >0, regenera frames cada 30 min de las ultimas N "
                         "horas (no solo el scan actual) -> recupera el "
                         "historico del dia. ~330 MB de L1b por scan diurno.")
    ap.add_argument("--volcano", default="",
                    help="Backfillear SOLO este volcan (nombre del CATALOG). "
                         "Los demas prioritarios se PRESERVAN del cache (no se "
                         "borran). Vacio = los 8.")
    args = ap.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for p in OUT_DIR.glob("*"):
        p.unlink()

    base = get_latest_time()
    if base is None:
        base = datetime.now(timezone.utc) - timedelta(minutes=15)
        log.warning("get_latest_time fallo, uso %s", base)

    priority = get_priority()
    scopes = {_slug(v.name): {"lat": v.lat, "lon": v.lon, "name": v.name}
              for v in priority}

    # --volcano: generar SOLO ese (los demas se preservan al mergear el ZIP
    # existente en la fase de escritura -> no se borran del release).
    gen_scopes = scopes
    day_volcs = list(priority)
    if args.volcano:
        tslug = _slug(args.volcano)
        if tslug not in scopes:
            log.error("'%s' (slug %s) no es prioritario. Opciones: %s",
                      args.volcano, tslug, list(scopes))
            return 1
        gen_scopes = {tslug: scopes[tslug]}
        day_volcs = [v for v in priority if _slug(v.name) == tslug]
        log.info("Backfill SOLO %s — los otros 7 se preservan del cache",
                 args.volcano)

    # Scans a generar (mas reciente -> atras), cada 30 min.
    if args.backfill_hours > 0:
        n = int(args.backfill_hours * 2)
        dts = [base - timedelta(minutes=30 * k) for k in range(n + 1)]
        log.info("BACKFILL %g h -> %d scans candidatos", args.backfill_hours,
                 len(dts))
    else:
        dts = [base]

    # Acumular frames nuevos por volcan: {slug: {ts: png_bytes}}.
    new_frames: dict[str, dict[str, bytes]] = {s: {} for s in scopes}
    for i, dt in enumerate(dts):
        if not _any_daylight(dt, day_volcs):
            log.info("[%d/%d] %s noche -> skip (sin descarga)", i + 1, len(dts),
                     dt.strftime("%H:%M"))
            continue
        log.info("[%d/%d] %s -> generando...", i + 1, len(dts),
                 dt.strftime("%H:%M UTC"))
        try:
            ts_str, gen = _generate_scan(dt, gen_scopes)
            for slug, b in gen.items():
                new_frames[slug][ts_str] = b
        except Exception as e:
            log.warning("scan %s fallo: %s", dt.isoformat(), e)
        if args.backfill_hours > 0:
            _clean_raw()   # liberar disco entre scans

    cutoff = (base - timedelta(hours=ROLL_HOURS)).strftime("%Y%m%d%H%M%S")
    manifest_scopes: dict[str, dict] = {}
    total_frames = 0
    for slug, sinfo in scopes.items():
        frames = _download_existing(slug)        # ventana rodante actual
        frames.update(new_frames[slug])          # + nuevos / backfilleados
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
        "scan_ts": base.strftime("%Y%m%d%H%M%S"),
        "radius_deg": RADIUS_DEG,
        "roll_hours": ROLL_HOURS,
        "scopes": manifest_scopes,
    }
    (OUT_DIR / "manifest_loop.json").write_text(json.dumps(manifest, indent=2))
    log.info("DONE. %d volcanes, %d frames en la ventana de %dh",
             len(manifest_scopes), total_frames, ROLL_HOURS)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
