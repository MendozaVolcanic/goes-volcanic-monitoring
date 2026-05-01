"""Build del cache de animaciones para subir al release `animations-rolling`.

Corre desde GitHub Actions cada hora. Para cada combinacion (scope, producto):
  1. Pide los ultimos N timestamps a RAMMB.
  2. Descarga los frames georreferenciados (mismo proceso que el viewer).
  3. Guarda cada frame como PNG en `out/`.
  4. Genera `manifest.json` con el indice.

Despues el workflow sube todo el contenido de `out/` al release como assets.

Scopes incluidos:
  - Nacional (Chile completo, zoom=2 reproyectado)
  - 4 zonas volcanicas (norte/centro/sur/austral, zoom=3)
  - 8 volcanes prioritarios (zoom=4 con fallback a zoom=3)

Productos: geocolor, eumetsat_ash, jma_so2  (3 productos -> ~120 MB total)

Tiempo de ejecucion: ~6-8 min en runner GH (limitado por RAMMB throughput).
"""

from __future__ import annotations

import io
import json
import logging
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

# Permitir `python scripts/build_animation_cache.py` desde la raiz.
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import numpy as np
from PIL import Image

from src.config import VOLCANIC_ZONES
from src.fetch.animation_cache import (
    asset_name, scope_id_nacional, scope_id_volcan, scope_id_zona,
)
from src.fetch.rammb_slider import (
    CHILE_TILES_Z2, ZOOM_VOLCAN, ZOOM_ZONE, VOLCANO_RADIUS_DEG,
    fetch_animation_frames, fetch_frame_for_bounds, get_latest_timestamps,
    reproject_to_latlon,
)
from src.volcanos import get_priority

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("build_anim_cache")

# 12 horas de frames a 10 min cadencia = 72. Subimos a 78 por margen
# (RAMMB a veces tiene gaps).
N_FRAMES = 72
PRODUCTS = ["geocolor", "eumetsat_ash", "jma_so2"]
OUT_DIR = ROOT / "out_animation_cache"


def _save_frame(arr: np.ndarray, path: Path) -> int:
    """Guardar PNG. Devuelve bytes escritos."""
    img = Image.fromarray(arr)
    buf = io.BytesIO()
    # PNG con optimize moderado: balance tamanio/tiempo.
    img.save(buf, format="PNG", optimize=False, compress_level=6)
    data = buf.getvalue()
    path.write_bytes(data)
    return len(data)


def _build_nacional(product: str) -> list[str]:
    """Devuelve lista de ts cacheados para Nacional."""
    log.info("[nacional/%s] descargando %d frames...", product, N_FRAMES)
    frames = fetch_animation_frames(
        product=product, n_frames=N_FRAMES, zoom=2,
        tile_rows=CHILE_TILES_Z2["rows"], tile_cols=CHILE_TILES_Z2["cols"],
    )
    if not frames:
        log.warning("[nacional/%s] sin frames", product)
        return []
    sid = scope_id_nacional()
    saved = []
    total_bytes = 0
    for f in frames:
        # Mismo reproject que el viewer (`_fetch_chile_frames`).
        img = reproject_to_latlon(f["image"], col_start=678, row_start=1356)
        path = OUT_DIR / asset_name(sid, product, f["ts"])
        total_bytes += _save_frame(img, path)
        saved.append(f["ts"])
    log.info("[nacional/%s] %d frames, %.1f MB", product, len(saved),
             total_bytes / 1e6)
    return sorted(saved)


def _build_bounds(scope_id: str, product: str, bounds: dict, zoom: int,
                  fallback_zoom: int | None = None) -> list[str]:
    """Worker generico: bbox arbitrario (zona o volcan)."""
    log.info("[%s/%s] descargando %d frames zoom=%d...",
             scope_id, product, N_FRAMES, zoom)
    timestamps = get_latest_timestamps(product, n=N_FRAMES)
    if not timestamps:
        log.warning("[%s/%s] sin timestamps RAMMB", scope_id, product)
        return []

    def _one(ts: str):
        img = fetch_frame_for_bounds(product, ts, bounds, zoom=zoom)
        if img is None and fallback_zoom is not None:
            img = fetch_frame_for_bounds(product, ts, bounds, zoom=fallback_zoom)
        return ts, img

    saved = []
    total_bytes = 0
    with ThreadPoolExecutor(max_workers=6) as ex:
        for fut in as_completed([ex.submit(_one, ts) for ts in timestamps]):
            ts, img = fut.result()
            if img is None:
                continue
            path = OUT_DIR / asset_name(scope_id, product, ts)
            total_bytes += _save_frame(img, path)
            saved.append(ts)

    log.info("[%s/%s] %d frames, %.1f MB", scope_id, product, len(saved),
             total_bytes / 1e6)
    return sorted(saved)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    # Limpiar contenido viejo: cada build es un snapshot completo.
    for p in OUT_DIR.glob("*"):
        p.unlink()

    manifest: dict = {
        "updated_utc": datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"),
        "n_frames_target": N_FRAMES,
        "products": PRODUCTS,
        "scopes": {},
    }

    # ── Nacional ──────────────────────────────────────────────────────────
    sid = scope_id_nacional()
    manifest["scopes"][sid] = {}
    for prod in PRODUCTS:
        manifest["scopes"][sid][prod] = _build_nacional(prod)

    # ── 4 Zonas ───────────────────────────────────────────────────────────
    for zk, zb in VOLCANIC_ZONES.items():
        sid = scope_id_zona(zk)
        manifest["scopes"][sid] = {}
        bounds = {"lat_min": zb["lat_min"], "lat_max": zb["lat_max"],
                  "lon_min": zb["lon_min"], "lon_max": zb["lon_max"]}
        for prod in PRODUCTS:
            manifest["scopes"][sid][prod] = _build_bounds(
                sid, prod, bounds, zoom=ZOOM_ZONE,
            )

    # ── 8 Volcanes prioritarios ───────────────────────────────────────────
    r = VOLCANO_RADIUS_DEG
    for v in get_priority():
        sid = scope_id_volcan(v.name)
        manifest["scopes"][sid] = {}
        bounds = {"lat_min": v.lat - r, "lat_max": v.lat + r,
                  "lon_min": v.lon - r, "lon_max": v.lon + r}
        for prod in PRODUCTS:
            manifest["scopes"][sid][prod] = _build_bounds(
                sid, prod, bounds, zoom=ZOOM_VOLCAN, fallback_zoom=ZOOM_ZONE,
            )

    # ── Manifest ──────────────────────────────────────────────────────────
    manifest_path = OUT_DIR / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2))

    total_assets = sum(1 for _ in OUT_DIR.glob("*.png"))
    total_size = sum(p.stat().st_size for p in OUT_DIR.glob("*"))
    log.info("DONE. %d PNG + manifest. Total %.1f MB en %s",
             total_assets, total_size / 1e6, OUT_DIR)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
