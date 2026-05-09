"""Backfill historico de un volcan + zona para una fecha y rango horario.

Genera un release `backfill-<DATE>-<VOLCAN>` con PNGs por (timestamp,
producto, scope), mas un manifest.json con todo el indice. La vista
`dashboard/views/backfill_viewer.py` lo lee directo del CDN del release.

Uso:
    python scripts/build_backfill.py \
        --date 2026-02-08 \
        --start 10:36 --end 19:00 \
        --volcan Lascar \
        --zone norte

Productos generados:
  - geocolor (zoom 4 si disponible para esa fecha, sino 3)
  - eumetsat_ash (zoom 3 — RAMMB historico no tiene IR a zoom 4)
  - jma_so2 (zoom 3)
  - split_window_difference_10_3-12_3 / BTD (zoom 3)
  - hotspots FDCF: lista JSON por timestamp con hot spots dentro del bbox
  - volcat: imagen RGBA via SSEC RealEarth (si disponible para esa fecha)

Tiempo de ejecucion: ~10-15 min para 51 timestamps × 4 productos × 2 scopes.
"""

from __future__ import annotations

import argparse
import io
import json
import logging
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import numpy as np
from PIL import Image

from src.config import VOLCANIC_ZONES
from src.fetch.historic_rammb import (
    HISTORIC_MAX_ZOOM, detect_seconds_offset,
    fetch_historic_frame_for_bounds, generate_timestamps,
)
from src.volcanos import get_volcano

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("backfill")

# Productos RAMMB y su zoom historico maximo
PRODUCTS_RAMMB = ["geocolor", "eumetsat_ash", "jma_so2",
                  "split_window_difference_10_3-12_3"]
VOLCAN_RADIUS_DEG = 0.5

OUT_DIR = ROOT / "out_backfill"


def _save_png(arr: np.ndarray, path: Path) -> int:
    img = Image.fromarray(arr)
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=False, compress_level=6)
    data = buf.getvalue()
    path.write_bytes(data)
    return len(data)


def _fetch_one(product: str, ts: str, bounds: dict, scope_id: str,
               out_dir: Path) -> tuple[str, str, bool, int]:
    """Devuelve (ts, scope_id, ok, bytes)."""
    zoom = HISTORIC_MAX_ZOOM.get(product, 3)
    img = fetch_historic_frame_for_bounds(product, ts, bounds, zoom=zoom)
    if img is None:
        return ts, scope_id, False, 0
    fname = f"{scope_id}__{product}__{ts}.png"
    nbytes = _save_png(img, out_dir / fname)
    return ts, scope_id, True, nbytes


def _build_rammb(timestamps: list[str], scopes: dict[str, dict],
                 out_dir: Path) -> dict[str, dict[str, list[str]]]:
    """Baja RAMMB para todas las combos (ts × producto × scope) en paralelo.

    Devuelve dict scope_id -> producto -> lista de ts disponibles.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    available: dict[str, dict[str, list[str]]] = {
        sid: {p: [] for p in PRODUCTS_RAMMB} for sid in scopes
    }
    total_bytes = 0
    total_ok = 0
    total = 0

    # Lanzamos en paralelo con throttling. Lascar zoom 4 baja muchos tiles
    # asi que 6 workers concurrentes es un buen balance.
    tasks = []
    for ts in timestamps:
        for prod in PRODUCTS_RAMMB:
            for sid, bounds in scopes.items():
                tasks.append((prod, ts, bounds, sid))

    log.info("RAMMB: %d tareas (%d ts × %d productos × %d scopes)",
             len(tasks), len(timestamps), len(PRODUCTS_RAMMB), len(scopes))

    with ThreadPoolExecutor(max_workers=6) as ex:
        futures = [ex.submit(_fetch_one, p, t, b, sid, out_dir)
                   for (p, t, b, sid) in tasks]
        # Mantener el mapeo task index -> producto
        for i, fut in enumerate(as_completed(futures)):
            ts, sid, ok, nb = fut.result()
            total += 1
            if ok:
                total_ok += 1
                total_bytes += nb
                # Buscar el producto desde el filename (el future no lo trae)
                # Mejor: rebuild lookups a partir de tasks
            if total % 50 == 0:
                log.info("  progreso %d/%d (%.0f%% ok)", total, len(tasks),
                         100 * total_ok / total)

    # Reconstruir 'available' escaneando el output (mas robusto que
    # tracking del future).
    for png in sorted(out_dir.glob("*.png")):
        # nombre: scope__producto__ts.png
        try:
            sid, prod, ts_with_ext = png.name.split("__", 2)
            ts = ts_with_ext.replace(".png", "")
            if sid in available and prod in available[sid]:
                available[sid][prod].append(ts)
        except ValueError:
            continue
    for sid in available:
        for p in available[sid]:
            available[sid][p].sort()

    log.info("RAMMB: %d/%d OK, %.1f MB", total_ok, total, total_bytes / 1e6)
    return available


def _build_hotspots(timestamps: list[str], scopes: dict[str, dict],
                    out_dir: Path) -> dict[str, list[str]]:
    """Por cada ts y scope, baja FDCF L2 de S3 y guarda hotspots filtrados."""
    from src.fetch.goes_fdcf import fetch_latest_hotspots
    available: dict[str, list[str]] = {sid: [] for sid in scopes}
    for ts in timestamps:
        # Convertir ts RAMMB (YYYYMMDDHHmmss) -> datetime
        try:
            dt = datetime.strptime(ts, "%Y%m%d%H%M%S")
        except ValueError:
            continue
        for sid, bounds in scopes.items():
            try:
                # fetch_latest_hotspots acepta dt? Si no, usar hours_back
                # apuntando al pasado. Por ahora simplificamos: solo si el
                # producto FDCF L2 esta en S3 para ese ts (lo esta).
                hs_list, hs_dt = fetch_latest_hotspots(
                    bounds=bounds, hours_back=1,
                )
                # Si fetch_latest_hotspots no acepta ts especifico,
                # esto traera los HS de ahora — DESDE el codigo actual
                # no podemos pedir un ts historico sin extender la funcion.
                # Para v1 del backfill grabamos lo que haya y marcamos.
                # TODO: extender goes_fdcf.fetch_at_time(dt, bounds).
                payload = {
                    "ts": ts, "scope": sid,
                    "n_hotspots": len(hs_list),
                    "warning": "fetch_at_time historico no implementado; "
                               "este JSON contiene hotspots ACTUALES, no del ts historico",
                    "hotspots": [],
                }
                fname = f"{sid}__hotspots__{ts}.json"
                (out_dir / fname).write_text(json.dumps(payload))
                available[sid].append(ts)
            except Exception as e:
                log.warning("hotspots %s %s: %s", sid, ts, e)
    return available


def _build_volcat(timestamps: list[str], scopes: dict[str, dict],
                  out_dir: Path) -> dict[str, list[str]]:
    """Intenta bajar VOLCAT via RealEarth para cada (ts, scope)."""
    from src.fetch.realearth_api import fetch_image
    available: dict[str, list[str]] = {sid: [] for sid in scopes}
    for ts in timestamps:
        # RealEarth time format: YYYYMMDD.HHMMSS
        re_time = f"{ts[:8]}.{ts[8:14]}"
        for sid, bounds in scopes.items():
            try:
                arr = fetch_image("ash_rgb", bounds=bounds,
                                  width=600, height=600, time=re_time)
                if arr is None:
                    continue
                # arr es RGBA, convertir a RGB
                if arr.shape[-1] == 4:
                    arr = arr[..., :3]
                fname = f"{sid}__volcat__{ts}.png"
                _save_png(arr, out_dir / fname)
                available[sid].append(ts)
            except Exception as e:
                log.warning("volcat %s %s: %s", sid, ts, e)
    return available


def main():
    ap = argparse.ArgumentParser(description="Build backfill release.")
    ap.add_argument("--date", required=True, help="YYYY-MM-DD")
    ap.add_argument("--start", required=True, help="HH:MM UTC")
    ap.add_argument("--end", required=True, help="HH:MM UTC")
    ap.add_argument("--volcan", required=True, help="Nombre exacto del volcan")
    ap.add_argument("--zone", required=False, help="Zona ('norte', 'centro', 'sur', 'austral'). Opcional.")
    ap.add_argument("--include-volcat", action="store_true",
                    help="Intentar VOLCAT (puede ser lento o fallar para fechas viejas)")
    ap.add_argument("--include-hotspots", action="store_true",
                    help="Intentar hotspots FDCF (placeholder, no historico aun)")
    args = ap.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    # Limpiar
    for p in OUT_DIR.glob("*"):
        p.unlink()

    # 1. Detect offset
    log.info("Detectando offset segundos para %s...", args.date)
    offset = detect_seconds_offset(args.date)
    if offset is None:
        log.error("No pude detectar offset — fecha fuera de archive RAMMB?")
        return 1
    log.info("Offset: %d", offset)

    # 2. Generar lista de timestamps
    timestamps = generate_timestamps(args.date, args.start, args.end, offset)
    log.info("Timestamps: %d (%s a %s)",
             len(timestamps), timestamps[0], timestamps[-1])

    # 3. Definir scopes
    v = get_volcano(args.volcan)
    if v is None:
        log.error("Volcan '%s' no encontrado en CATALOG", args.volcan)
        return 2
    safe_volc = "".join(c if c.isalnum() else "_" for c in v.name.lower())
    scopes: dict[str, dict] = {
        f"volcan__{safe_volc}": {
            "lat_min": v.lat - VOLCAN_RADIUS_DEG,
            "lat_max": v.lat + VOLCAN_RADIUS_DEG,
            "lon_min": v.lon - VOLCAN_RADIUS_DEG,
            "lon_max": v.lon + VOLCAN_RADIUS_DEG,
        }
    }
    if args.zone:
        zb = VOLCANIC_ZONES[args.zone]
        scopes[f"zona__{args.zone}"] = {
            "lat_min": zb["lat_min"], "lat_max": zb["lat_max"],
            "lon_min": zb["lon_min"], "lon_max": zb["lon_max"],
        }

    log.info("Scopes: %s", list(scopes.keys()))

    # 4. RAMMB tiles
    rammb_avail = _build_rammb(timestamps, scopes, OUT_DIR)

    # 5. Hotspots (opcional)
    hs_avail = {}
    if args.include_hotspots:
        log.info("Bajando hotspots FDCF...")
        hs_avail = _build_hotspots(timestamps, scopes, OUT_DIR)

    # 6. VOLCAT (opcional)
    volcat_avail = {}
    if args.include_volcat:
        log.info("Bajando VOLCAT desde RealEarth...")
        volcat_avail = _build_volcat(timestamps, scopes, OUT_DIR)

    # 7. Manifest
    manifest = {
        "date": args.date,
        "start": args.start,
        "end": args.end,
        "volcan": v.name,
        "zone": args.zone,
        "seconds_offset": offset,
        "timestamps_target": timestamps,
        "scopes": {
            sid: {
                "bounds": bounds,
                "products": rammb_avail.get(sid, {}),
                "hotspots_ts": hs_avail.get(sid, []),
                "volcat_ts": volcat_avail.get(sid, []),
            }
            for sid, bounds in scopes.items()
        },
        "products_rammb": PRODUCTS_RAMMB,
        "historic_max_zoom": HISTORIC_MAX_ZOOM,
        "generated_utc": datetime.utcnow().strftime("%Y%m%dT%H%M%SZ"),
    }
    (OUT_DIR / "manifest.json").write_text(json.dumps(manifest, indent=2))

    n_assets = len(list(OUT_DIR.glob("*")))
    total_size = sum(p.stat().st_size for p in OUT_DIR.glob("*"))
    log.info("DONE. %d assets, %.1f MB en %s", n_assets, total_size / 1e6, OUT_DIR)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
