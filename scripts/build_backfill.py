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
from datetime import datetime, timezone
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
               out_dir: Path, l1b_fallback: bool = False
               ) -> tuple[str, str, bool, int]:
    """Devuelve (ts, scope_id, ok, bytes).

    Si RAMMB no tiene el frame y `l1b_fallback` esta activo, regenera el
    producto desde las bandas L1b crudas de S3 (cobertura indefinida, vs
    los ~9-10 meses de RAMMB). Ver src/process/historic_l1b_rgb.py.
    """
    zoom = HISTORIC_MAX_ZOOM.get(product, 3)
    img = fetch_historic_frame_for_bounds(product, ts, bounds, zoom=zoom)
    if img is None and l1b_fallback:
        try:
            from src.process.historic_l1b_rgb import fetch_l1b_rgb
            dt = datetime.strptime(ts, "%Y%m%d%H%M%S").replace(
                tzinfo=timezone.utc)
            img = fetch_l1b_rgb(product, dt, bounds)
            if img is not None:
                log.info("[l1b-fallback] %s %s %s OK", product, scope_id, ts)
        except Exception as e:
            log.warning("[l1b-fallback] %s %s %s: %s", product, scope_id, ts, e)
    if img is None:
        return ts, scope_id, False, 0
    fname = f"{scope_id}__{product}__{ts}.png"
    nbytes = _save_png(img, out_dir / fname)
    return ts, scope_id, True, nbytes


def _build_rammb(timestamps: list[str], scopes: dict[str, dict],
                 out_dir: Path, l1b_fallback: bool = False
                 ) -> dict[str, dict[str, list[str]]]:
    """Baja RAMMB para todas las combos (ts × producto × scope) en paralelo.

    Si `l1b_fallback` esta activo, cada frame que RAMMB no tenga se regenera
    desde L1b crudo. En modo L1b-only (fecha fuera del archive RAMMB) TODOS
    los frames caen a L1b.

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

    # Con fallback L1b activo bajamos full-disks pesados de S3 — menos workers
    # para no saturar memoria/red (cada banda full-disk son decenas de MB).
    n_workers = 3 if l1b_fallback else 6
    with ThreadPoolExecutor(max_workers=n_workers) as ex:
        futures = [ex.submit(_fetch_one, p, t, b, sid, out_dir, l1b_fallback)
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
        # nombre: {scope}__{producto}__{ts}.png — OJO: scope_id CONTIENE '__'
        # (ej. 'volcan__villarrica'), asi que hay que partir desde la DERECHA.
        # Con split() normal, sid quedaba 'volcan' y no matcheaba -> RGB en 0
        # en el manifest aunque los PNG estuvieran en disco. (fix jun 2026)
        try:
            sid, prod, ts_with_ext = png.name.rsplit("__", 2)
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
    """Por cada ts y scope, baja FDCF L2 historico de S3 y guarda hotspots."""
    from datetime import timezone as _tz
    from src.fetch.goes_fdcf import fetch_hotspots_at_time

    available: dict[str, list[str]] = {sid: [] for sid in scopes}
    # Cache por ts: el archivo FDCF cubre todo Chile, asi que UN download
    # alcanza para todos los scopes del mismo ts. Reutilizamos.
    for ts in timestamps:
        try:
            dt = datetime.strptime(ts, "%Y%m%d%H%M%S").replace(tzinfo=_tz.utc)
        except ValueError:
            continue
        # Bbox amplio (Chile entero) para una sola lectura S3
        chile_bbox = {"lat_min": -57.0, "lat_max": -17.0,
                      "lon_min": -76.0, "lon_max": -65.0}
        try:
            all_hs, scan_dt = fetch_hotspots_at_time(dt, bounds=chile_bbox)
        except Exception as e:
            log.warning("hotspots fetch %s: %s", ts, e)
            continue
        # Filtrar y guardar por scope
        for sid, bounds in scopes.items():
            scope_hs = [h for h in all_hs
                        if (bounds["lat_min"] <= h.lat <= bounds["lat_max"]
                            and bounds["lon_min"] <= h.lon <= bounds["lon_max"])]
            payload = {
                "ts": ts, "scope": sid,
                "scan_dt": scan_dt.isoformat() if scan_dt else None,
                "n_hotspots": len(scope_hs),
                "hotspots": [h.to_dict() for h in scope_hs],
            }
            fname = f"{sid}__hotspots__{ts}.json"
            (out_dir / fname).write_text(json.dumps(payload))
            available[sid].append(ts)
        if all_hs:
            log.info("[hotspots] ts=%s -> %d total Chile", ts, len(all_hs))
    return available


def _save_png_rgba(arr: np.ndarray, path: Path) -> int:
    """Guardar como PNG RGBA preservando transparencia."""
    img = Image.fromarray(arr, mode="RGBA")
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=False, compress_level=6)
    data = buf.getvalue()
    path.write_bytes(data)
    return len(data)


def _build_volcat(timestamps: list[str], scopes: dict[str, dict],
                  out_dir: Path) -> dict[str, list[str]]:
    """Intenta bajar VOLCAT via RealEarth para cada (ts, scope).

    Guarda como PNG RGBA preservando alpha — los pixels sin ceniza
    son transparentes (alpha=0). La vista compone sobre GeoColor para
    que se vea: VOLCAT solo es util como overlay, no como imagen
    standalone (sino los pixels sin ceniza salen negros).
    """
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
                # Asegurar RGBA y guardar con alpha
                if arr.shape[-1] == 3:
                    # Si vino RGB, agregar alpha=255
                    a = np.full((*arr.shape[:2], 1), 255, dtype=arr.dtype)
                    arr = np.concatenate([arr, a], axis=-1)
                fname = f"{sid}__volcat__{ts}.png"
                _save_png_rgba(arr, out_dir / fname)
                available[sid].append(ts)
            except Exception as e:
                log.warning("volcat %s %s: %s", sid, ts, e)
    return available


def _resolve_volcat_sector(v) -> tuple[str, str] | None:
    """Sector VOLCAT para un volcan del CATALOG.

    Prioriza el sector DEDICADO del volcan (mejor resolucion: Copahue_250_m,
    Calbuco_1_km, etc.). Si el volcan no tiene sector dedicado mapeado, cae al
    sector REGIONAL de su zona (Chile_North/Central/South_2_km).

    OJO acentos: VOLCANO_TO_SECTOR usa nombres acentuados ('Láscar') y el
    CATALOG no ('Lascar'), asi que el match exacto/substring falla para varios
    volcanes — por eso el fallback por zona es la red de seguridad real.
    """
    from src.fetch.volcat_api import ZONE_TO_SECTOR, get_sector_for_volcano
    info = get_sector_for_volcano(v.name)
    if info:
        return info
    # Fallback regional por zona. 'austral' cae bajo 'Sur' (Chile_South cubre
    # hasta el extremo sur — no existe sector austral en VOLCAT).
    zmap = {"norte": "Norte", "centro": "Centro", "sur": "Sur",
            "austral": "Sur"}
    z = zmap.get(getattr(v, "zone", None))
    if z and z in ZONE_TO_SECTOR:
        return ZONE_TO_SECTOR[z]
    return None


def _build_volcat_height(timestamps: list[str], sector: str, instr: str,
                         out_dir: Path) -> dict:
    """Baja la ALTURA de pluma VOLCAT (Ash_Height, km AMSL) por timestamp.

    A diferencia del overlay Ash RGB de RealEarth (_build_volcat), esto es el
    producto CUANTITATIVO de Pavolonis 2013: una imagen de SECTOR completo
    color-codificada por altura, con su propia colorbar. No se recorta al bbox
    del volcan — se muestra como en el VOLCAT viewer (imagen de sector + leyenda).

    Por cada ts busca el frame VOLCAT mas cercano (volcat_at_time, gap <=30 min).
    El archivo de Ash_Height del API tiene ~30 dias de profundidad, asi que para
    eventos mas viejos esto devuelve listas vacias (la altura no esta disponible).

    Asset por ts: `volcat_height__{ts}.png`. Leyenda unica: `volcat_height_legend.png`
    (la colorbar es estatica por sector/producto). Devuelve dict para el manifest.
    """
    from src.fetch._http_session import get_session
    from src.fetch.volcat_api import volcat_at_time

    sess = get_session()
    legend_asset = "volcat_height_legend.png"
    legend_saved = False
    avail_ts: list[str] = []
    frames_meta: dict[str, dict] = {}
    # Dedup de descargas: si dos ts objetivo mapean al MISMO frame VOLCAT
    # (cadencia objetivo mas fina que los 10 min de ABI), reusamos los bytes.
    frame_cache: dict[str, bytes] = {}

    for ts in timestamps:
        try:
            dt = datetime.strptime(ts, "%Y%m%d%H%M%S").replace(tzinfo=timezone.utc)
        except ValueError:
            continue
        try:
            meta = volcat_at_time(dt, sector, instr=instr,
                                  image_type="Ash_Height")
        except Exception as e:
            log.warning("[volcat_height] %s: %s", ts, e)
            continue
        if meta is None:
            continue

        frame_dt = meta.get("datetime")
        png_bytes = frame_cache.get(frame_dt) if frame_dt else None
        if png_bytes is None:
            try:
                r = sess.get(meta["image_url"], timeout=30)
                if r.status_code != 200 or not r.content:
                    log.warning("[volcat_height] %s img -> %s", ts, r.status_code)
                    continue
                png_bytes = r.content
                if frame_dt:
                    frame_cache[frame_dt] = png_bytes
            except Exception as e:
                log.warning("[volcat_height] %s download: %s", ts, e)
                continue

        (out_dir / f"volcat_height__{ts}.png").write_bytes(png_bytes)
        avail_ts.append(ts)
        frames_meta[ts] = {"frame_dt": frame_dt,
                           "gap_s": meta.get("gap_seconds")}

        # Colorbar: bajar una sola vez (estatica por sector/producto).
        if not legend_saved and meta.get("legend_url"):
            try:
                rl = sess.get(meta["legend_url"], timeout=30)
                if rl.status_code == 200 and rl.content:
                    (out_dir / legend_asset).write_bytes(rl.content)
                    legend_saved = True
            except Exception as e:
                log.warning("[volcat_height] legend: %s", e)

    log.info("[volcat_height] sector %s: %d/%d ts con altura",
             sector, len(avail_ts), len(timestamps))
    return {
        "sector": sector,
        "instr": instr,
        "image_type": "Ash_Height",
        "ts": avail_ts,
        "legend_asset": legend_asset if legend_saved else None,
        "frames": frames_meta,
    }


def main():
    ap = argparse.ArgumentParser(description="Build backfill release.")
    ap.add_argument("--date", required=True, help="YYYY-MM-DD")
    ap.add_argument("--start", required=True, help="HH:MM UTC")
    ap.add_argument("--end", required=True, help="HH:MM UTC")
    ap.add_argument("--volcan", required=True, help="Nombre exacto del volcan")
    ap.add_argument("--zone", required=False, help="Zona ('norte', 'centro', 'sur', 'austral'). Opcional.")
    ap.add_argument("--include-volcat", action="store_true",
                    help="Intentar VOLCAT Ash RGB overlay (RealEarth)")
    ap.add_argument("--include-volcat-height", action="store_true",
                    help="Intentar ALTURA de pluma VOLCAT (Ash_Height km AMSL, "
                         "Pavolonis 2013). Imagen de sector + colorbar. "
                         "Archivo ~30 dias — falla para eventos mas viejos.")
    ap.add_argument("--include-hotspots", action="store_true",
                    help="Intentar hotspots FDCF historicos desde S3 NOAA")
    ap.add_argument("--l1b-fallback", action="store_true",
                    help="Regenerar productos desde L1b crudo (S3 noaa-goes19) "
                         "cuando RAMMB no tenga el frame. Si la fecha esta fuera "
                         "del archive RAMMB (~9-10 meses), activa modo L1b-only. "
                         "GeoColor sale TrueColor aprox (no el de CIRA).")
    args = ap.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    # Limpiar
    for p in OUT_DIR.glob("*"):
        p.unlink()

    # 1. Detect offset
    log.info("Detectando offset segundos para %s...", args.date)
    offset = detect_seconds_offset(args.date)
    l1b_only = False
    if offset is None:
        if args.l1b_fallback:
            # Fecha fuera del archive RAMMB pero L1b S3 la tiene (cobertura
            # indefinida desde abr-2025). Generamos timestamps a cadencia fija
            # (offset=0: los segundos no importan, _download_band_nearest elige
            # el scan mas cercano) y regeneramos TODO desde L1b.
            log.warning("Fecha fuera de archive RAMMB — modo L1b-only "
                        "(regenerando productos desde S3 noaa-goes19).")
            offset = 0
            l1b_only = True
        else:
            log.error("No pude detectar offset — fecha fuera de archive RAMMB? "
                      "Proba --l1b-fallback para regenerar desde L1b crudo.")
            return 1
    else:
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

    # 4. RAMMB tiles (con fallback L1b por-frame si esta activo / es L1b-only)
    use_l1b = args.l1b_fallback or l1b_only
    rammb_avail = _build_rammb(timestamps, scopes, OUT_DIR,
                               l1b_fallback=use_l1b)

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

    # 6b. Altura de pluma VOLCAT (opcional) — producto cuantitativo de sector
    volcat_height = {}
    if args.include_volcat_height:
        sect = _resolve_volcat_sector(v)
        if sect is None:
            log.warning("Sin sector VOLCAT para '%s' (zona=%s) — salto altura",
                        v.name, getattr(v, "zone", "?"))
        else:
            sector, instr = sect
            log.info("Bajando altura de pluma VOLCAT (sector %s)...", sector)
            volcat_height = _build_volcat_height(timestamps, sector, instr,
                                                 OUT_DIR)

    # 7. Manifest
    manifest = {
        "date": args.date,
        "start": args.start,
        "end": args.end,
        "volcan": v.name,
        "zone": args.zone,
        "seconds_offset": offset,
        "l1b_fallback": use_l1b,
        "l1b_only": l1b_only,
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
        "volcat_height": volcat_height,
        "products_rammb": PRODUCTS_RAMMB,
        "historic_max_zoom": HISTORIC_MAX_ZOOM,
        "generated_utc": datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"),
    }
    (OUT_DIR / "manifest.json").write_text(json.dumps(manifest, indent=2))

    n_assets = len(list(OUT_DIR.glob("*")))
    total_size = sum(p.stat().st_size for p in OUT_DIR.glob("*"))
    log.info("DONE. %d assets, %.1f MB en %s", n_assets, total_size / 1e6, OUT_DIR)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
