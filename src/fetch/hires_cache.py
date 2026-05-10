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
MANIFEST_URL = f"{CDN_BASE}/manifest.json"
TIMEOUT = 12


_session: requests.Session | None = None


def _get_session() -> requests.Session:
    global _session
    if _session is None:
        _session = requests.Session()
        _session.headers.update({"User-Agent": "GOES-VolcanicMonitor/1.0"})
    return _session


def _slugify(name: str) -> str:
    return "".join(c if c.isalnum() else "_" for c in name.lower())


def fetch_manifest() -> dict | None:
    """Descargar manifest.json. Devuelve None si no existe (cron nunca corrio)."""
    try:
        import time as _t
        url = f"{MANIFEST_URL}?_={int(_t.time())}"
        r = _get_session().get(url, timeout=TIMEOUT)
        if r.status_code == 404:
            return None
        r.raise_for_status()
        return r.json()
    except Exception as e:
        logger.warning("hires manifest: %s", e)
        return None


def fetch_hires_for_volcano(volcano_name: str) -> tuple[np.ndarray | None, dict | None]:
    """Bajar PNG hi-res del volcan. Devuelve (array, info) o (None, None).

    info incluye scan_ts, scan_dt_iso, lat, lon — util para badges/labels.
    """
    manifest = fetch_manifest()
    if manifest is None:
        return None, None
    sid = _slugify(volcano_name)
    scopes = manifest.get("scopes", {})
    if sid not in scopes or not scopes[sid].get("available"):
        return None, None
    ts = manifest.get("scan_ts")
    if not ts:
        return None, None
    asset = f"{sid}__hires__{ts}.png"
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
        }
    except Exception as e:
        logger.warning("hires fetch %s: %s", asset, e)
        return None, None
