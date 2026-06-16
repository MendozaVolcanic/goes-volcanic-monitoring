"""Cliente del cache ROLLING de loops hi-res GeoColor 0.5 km.

Lee el `manifest_loop.json` + los ZIP que el GH Action `hires_visible_cache.yml`
publica en el release `hires-loop-rolling` (ventana rodante ~8 h de frames
0.5 km pan-sharpened para los 8 volcanes prioritarios).

Uso desde el dashboard (vista loops, modo volcan + GeoColor + prioritario):
    frames, info = fetch_hires_loop_frames("Villarrica", max_frames=24)
    if frames:
        # cada frame: {"ts", "image" (np uint8), "bounds", "label"}
"""
from __future__ import annotations

import io
import logging
import zipfile

import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)

RELEASE_TAG = "hires-loop-rolling"
CDN_BASE = ("https://github.com/MendozaVolcanic/goes-volcanic-monitoring"
            f"/releases/download/{RELEASE_TAG}")
TIMEOUT = 30

from src.fetch._http_session import get_session as _get_session


def _slug(name: str) -> str:
    return "".join(c if c.isalnum() else "_" for c in name.lower())


def fetch_loop_manifest() -> dict | None:
    """Descargar manifest_loop.json del release. None si no existe aun."""
    try:
        import time as _t
        url = f"{CDN_BASE}/manifest_loop.json?_={int(_t.time())}"
        r = _get_session().get(url, timeout=12)
        if r.status_code == 404:
            return None
        r.raise_for_status()
        return r.json()
    except Exception as e:
        logger.warning("hires loop manifest: %s", e)
        return None


def loop_available_volcanoes() -> set[str]:
    """Nombres de volcanes con loop hi-res disponible (≥2 frames)."""
    man = fetch_loop_manifest()
    if not man:
        return set()
    return {sc.get("name", "") for sc in man.get("scopes", {}).values()
            if len(sc.get("ts", [])) >= 2}


def fetch_hires_loop_frames(volcano_name: str, max_frames: int | None = None
                            ) -> tuple[list[dict] | None, dict | None]:
    """Frames del loop hi-res 0.5 km para un volcan, ordenados por ts.

    Devuelve (frames, info) o (None, None) si no hay cache. Cada frame:
    {"ts", "image" (np uint8 HxWx3), "bounds", "label"}. info trae radius_deg.
    """
    man = fetch_loop_manifest()
    if not man:
        return None, None
    slug = _slug(volcano_name)
    sc = man.get("scopes", {}).get(slug)
    if not sc or not sc.get("ts"):
        return None, None
    ts_list = list(sc["ts"])
    if max_frames and len(ts_list) > max_frames:
        ts_list = ts_list[-max_frames:]
    r_deg = float(man.get("radius_deg", 0.5))
    lat, lon = sc.get("lat"), sc.get("lon")
    bounds = {"lat_min": lat - r_deg, "lat_max": lat + r_deg,
              "lon_min": lon - r_deg, "lon_max": lon + r_deg}
    try:
        from dashboard.utils import fmt_both_long, parse_rammb_ts
    except Exception:
        parse_rammb_ts = fmt_both_long = None
    try:
        r = _get_session().get(f"{CDN_BASE}/{slug}__geocolor05.zip",
                               timeout=TIMEOUT)
        if r.status_code != 200:
            return None, None
        frames: list[dict] = []
        with zipfile.ZipFile(io.BytesIO(r.content)) as zf:
            names = set(zf.namelist())
            for ts in ts_list:
                fn = f"{ts}.png"
                if fn not in names:
                    continue
                img = Image.open(io.BytesIO(zf.read(fn))).convert("RGB")
                label = ts
                if parse_rammb_ts is not None:
                    try:
                        label = fmt_both_long(parse_rammb_ts(ts))
                    except Exception:
                        label = ts
                frames.append({"ts": ts, "image": np.array(img),
                               "bounds": bounds, "label": f"{label} · hi-res 0.5 km"})
        if not frames:
            return None, None
        return frames, {"radius_deg": r_deg, "n": len(frames),
                        "updated_utc": man.get("updated_utc")}
    except Exception as e:
        logger.warning("hires loop fetch %s: %s", volcano_name, e)
        return None, None
