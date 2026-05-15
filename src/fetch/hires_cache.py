"""Cliente del cache hi-res visible (release `hires-rolling`).

Lee el manifest + PNGs hi-res que el GH Action `hires_visible_cache.yml`
publica cada 30 min. Patron identico a `animation_cache.py`.

Uso desde el dashboard:
    from src.fetch.hires_cache import fetch_hires_for_volcano
    arr = fetch_hires_for_volcano("Villarrica")
    if arr is not None:
        # mostrar en el mosaico en lugar del RAMMB normal
        ...
"""

from __future__ import annotations

import io
import json
import logging
from typing import Optional

import numpy as np
import requests
from PIL import Image

logger = logging.getLogger(__name__)

RELEASE_OWNER = "MendozaVolcanic"
RELEASE_REPO = "goes-volcanic-monitoring"
RELEASE_TAG = "hires-rolling"

CDN_BASE = (
    f"https://github.com/{RELEASE_OWNER}/{RELEASE_REPO}"
    f"/releases/download/{RELEASE_TAG}"
)
MANIFEST_URL = f"{CDN_BASE}/manifest.json"          # mode=color (default)
MANIFEST_MONO_URL = f"{CDN_BASE}/manifest_mono.json" # mode=mono_05km
TIMEOUT = 12


# Session HTTP compartida — definicion en src/fetch/_http_session
from src.fetch._http_session import get_session as _get_session



def _slugify(name: str) -> str:
    return "".join(c if c.isalnum() else "_" for c in name.lower())


def fetch_manifest(mode: str = "color") -> dict | None:
    """Descargar manifest.json del cache hi-res.

    mode='color' -> manifest.json (TrueColor + IR night)
    mode='mono_05km' -> manifest_mono.json (banda 2 sola, 0.5 km/px sepia)
    """
    url_base = MANIFEST_MONO_URL if mode == "mono_05km" else MANIFEST_URL
    try:
        import time as _t
        url = f"{url_base}?_={int(_t.time())}"
        r = _get_session().get(url, timeout=TIMEOUT)
        if r.status_code == 404:
            return None
        r.raise_for_status()
        return r.json()
    except Exception as e:
        logger.warning("hires manifest (mode=%s): %s", mode, e)
        return None


def fetch_hires_for_volcano(volcano_name: str, mode: str = "color"
                            ) -> tuple[np.ndarray | None, dict | None]:
    """Bajar PNG hi-res del volcan. Devuelve (array, info) o (None, None).

    Args:
        volcano_name: nombre exacto del volcan (matchea CATALOG).
        mode: 'color' o 'mono_05km'.

    info incluye scan_ts, scan_dt_iso, lat, lon, mode — util para badges.
    """
    manifest = fetch_manifest(mode=mode)
    if manifest is None:
        return None, None
    sid = _slugify(volcano_name)
    scopes = manifest.get("scopes", {})
    if sid not in scopes or not scopes[sid].get("available"):
        return None, None
    ts = manifest.get("scan_ts")
    if not ts:
        return None, None
    suffix = "hires_mono" if mode == "mono_05km" else "hires"
    asset = f"{sid}__{suffix}__{ts}.png"
    try:
        r = _get_session().get(f"{CDN_BASE}/{asset}", timeout=TIMEOUT)
        if r.status_code != 200:
            return None, None
        img = Image.open(io.BytesIO(r.content)).convert("RGB")
        return np.array(img), {
            "scan_ts": ts,
            "scan_dt_iso": manifest.get("scan_dt_iso"),
            "lat": scopes[sid].get("lat"),
            "lon": scopes[sid].get("lon"),
            "mode": mode,
            # Render metadata (None si manifest viejo no la tiene)
            "sun_alt": scopes[sid].get("sun_alt"),
            "render": scopes[sid].get("render"),
        }
    except Exception as e:
        logger.warning("hires fetch %s: %s", asset, e)
        return None, None
