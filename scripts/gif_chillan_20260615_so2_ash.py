"""GIF ad-hoc: SO2 RGB + Ash RGB de Nevados de Chillan, 2026-06-15 11:00-17:00 UTC.

Ventana de 37 frames (cada 10 min) del archivo RAMMB/CIRA (guarda ~28 dias).
Productos jma_so2 y eumetsat_ash NO tienen tiles zoom 4 -> techo zoom 3
(~3.4 km/px). El GeoColor 0.5 km va por otra via (cache hi-res / artifact).

Salida: GIF + MP4 anotados (mismo compositor que la vista loops del dashboard)
en C:\\Users\\nmend\\Downloads\\.

Uso:
    python scripts/gif_chillan_20260615_so2_ash.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

# raiz del repo en sys.path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.fetch import rammb_slider as R
from src.volcanos import get_volcano
from dashboard.views.rammb_viewer import _build_gif, _build_mp4

# ── Parametros ────────────────────────────────────────────────────────────
VOLCANO = "Nevados de Chillan"
DATE = "20260615"
SECONDS = "22"            # offset real del scan full-disk GOES-19 (verificado)
RADIUS_DEG = 0.5          # ±0.5° (igual encuadre que el hi-res, pedido Nicolas)
ZOOM = 3                  # maximo disponible para SO2/Ash (zoom 4 = 404)
START_HH, END_HH = 10, 17    # ventana UTC [inclusive..inclusive] cada 10 min
OUT_DIR = Path(r"C:\Users\nmend\Downloads")
WIN_TAG = f"{START_HH:02d}00-{END_HH:02d}00"   # para el nombre de archivo

# Productos: id RAMMB -> (etiqueta para el titulo, sufijo de archivo)
PRODUCTS = {
    "jma_so2":      ("SO2 RGB (JMA) · ~3.4 km/px",      "SO2_RGB"),
    "eumetsat_ash": ("Ash RGB (EUMETSAT) · ~3.4 km/px", "Ash_RGB"),
}


def minutes_grid() -> list[str]:
    """timestamps START_HH:00..END_HH:00 cada 10 min -> 'YYYYMMDDHHMM22'."""
    out = []
    for total in range(START_HH * 60, END_HH * 60 + 1, 10):
        hh, mm = divmod(total, 60)
        out.append(f"{DATE}{hh:02d}{mm:02d}{SECONDS}")
    return out


def fetch_hd(product: str, ts: str, bounds: dict, lat: float, retries: int = 3):
    """fetch_frame_for_bounds pero con out_size km-correcto (cos lat) y mas
    denso que el default (evita el floor 120x80 que distorsiona cajas chicas).

    RAMMB 404ea INTERMITENTEMENTE tiles del archivo (mismo ts a veces sirve, a
    veces no). Reintentamos el stitch hasta `retries` veces -> recupera esos
    huecos transitorios; los gaps REALES (ts ausente del archivo) agotan los
    reintentos y se saltan igual. (jun 2026)"""
    rows, cols = R.get_tiles_for_bounds(bounds, ZOOM)
    img = None
    for _ in range(max(1, retries)):
        img = R.fetch_stitched_frame(product, ts, zoom=ZOOM,
                                     tile_rows=rows, tile_cols=cols)
        if img is not None:
            break
    if img is None:
        return None
    tile_sz = int(img.shape[0] // len(rows))
    col_start = min(cols) * tile_sz
    row_start = min(rows) * tile_sz
    lat_span = bounds["lat_max"] - bounds["lat_min"]
    lon_span = bounds["lon_max"] - bounds["lon_min"]
    # aspecto km-correcto: ancho ∝ lon*cos(lat), alto ∝ lat
    out_h = 360
    out_w = max(80, round(out_h * (lon_span * np.cos(np.radians(lat)))
                          / lat_span))
    return R.reproject_to_latlon(
        img, col_start=col_start, row_start=row_start,
        out_bounds=bounds, zoom=ZOOM, tile_sz=tile_sz,
        out_size=(out_h, out_w),
    )


def main():
    v = get_volcano(VOLCANO)
    if v is None:
        raise SystemExit(f"volcan no encontrado: {VOLCANO}")
    bounds = {"lat_min": v.lat - RADIUS_DEG, "lat_max": v.lat + RADIUS_DEG,
              "lon_min": v.lon - RADIUS_DEG, "lon_max": v.lon + RADIUS_DEG}
    timestamps = minutes_grid()
    print(f"{v.name} ({v.lat},{v.lon}) ±{RADIUS_DEG}° · {len(timestamps)} ts "
          f"({timestamps[0]}..{timestamps[-1]}) zoom {ZOOM}")
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    for prod, (plabel, suffix) in PRODUCTS.items():
        print(f"\n=== {prod} ({plabel}) ===")
        frames = []
        for ts in timestamps:
            img = fetch_hd(prod, ts, bounds, v.lat)
            hh, mm = ts[8:10], ts[10:12]
            if img is None:
                print(f"  {hh}:{mm}  -> 404 (saltado)")
                continue
            frames.append({
                "ts": ts,
                "image": img,
                "bounds": bounds,
                "label": f"2026-06-15 {hh}:{mm} UTC",
            })
            print(f"  {hh}:{mm}  -> {img.shape[1]}x{img.shape[0]} px")
        if not frames:
            print(f"  SIN FRAMES para {prod} — se omite")
            continue

        meta = {
            "focus": v.name,
            "title": "Nevados de Chillán",
            "product_label": plabel,
        }
        base = OUT_DIR / f"chillan_20260615_{WIN_TAG}_{suffix}"
        gif = _build_gif(frames, meta, duration_ms=450)
        (base.with_suffix(".gif")).write_bytes(gif)
        print(f"  GIF  -> {base.with_suffix('.gif')}  ({len(gif)//1024} KB, "
              f"{len(frames)} frames)")
        try:
            mp4 = _build_mp4(frames, fps=3.0, meta=meta)
            if mp4:
                (base.with_suffix(".mp4")).write_bytes(mp4)
                print(f"  MP4  -> {base.with_suffix('.mp4')}  "
                      f"({len(mp4)//1024} KB)")
        except Exception as e:
            print(f"  MP4  -> fallo ({e})")


if __name__ == "__main__":
    main()
