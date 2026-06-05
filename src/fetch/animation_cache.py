"""Cache de frames de animacion en GitHub Releases.

Estrategia: un GitHub Action corre cada hora, baja los ultimos 12h de frames
RAMMB para los scopes mas usados (Nacional + 4 zonas + 8 volcanes prioritarios)
x 3 productos, y sube cada frame como asset PNG al release `animations-rolling`.
Junto sube `manifest.json` con la lista de timestamps disponibles por
(scope, product).

El dashboard llama `fetch_cached_or_delta(...)`:
  1. Lee `manifest.json` (~2 KB).
  2. Pide los ultimos N timestamps a RAMMB.
  3. De esos N, descarga del release los que estan cacheados (paralelo, CDN
     rapido) y de RAMMB solo los faltantes (suelen ser 0-6, los del ultima
     hora que el cron todavia no pesco).
  4. Devuelve la lista de frames en formato compatible con `_build_mp4`.

Si el manifest no existe (cron nunca corrio, o release fue borrado) la
funcion devuelve `None` y el llamador debe caer al flujo on-demand puro.

Por que asi y no MP4 pre-rendereados:
  Pre-rendereando el MP4, los ultimos ~60 min nunca estan incluidos. Cacheando
  *frames*, hacemos delta-fetch de lo que falta y siempre mostramos lo mas
  reciente. Mismo tamanio de almacenamiento, mejor UX.
"""

from __future__ import annotations

import io
import json
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional

import numpy as np
import requests
from PIL import Image

logger = logging.getLogger(__name__)

# Release publico que publica el GH Action `animation_cache.yml`.
# Apunta al repo en el que corre el Action (no requiere auth para GET).
RELEASE_OWNER = "MendozaVolcanic"
RELEASE_REPO = "goes-volcanic-monitoring"
RELEASE_TAG = "animations-rolling"

CDN_BASE = (
    f"https://github.com/{RELEASE_OWNER}/{RELEASE_REPO}"
    f"/releases/download/{RELEASE_TAG}"
)

MANIFEST_URL = f"{CDN_BASE}/manifest.json"
TIMEOUT = 15


# ── Identificadores de scope canonicos ────────────────────────────────────
# Estos strings DEBEN ser estables: forman parte del nombre de cada asset
# en el release. Cambiarlos invalida todo el cache.

def scope_id_nacional() -> str:
    return "nacional"


def scope_id_zona(zone_key: str) -> str:
    return f"zona__{zone_key}"


def scope_id_volcan(volcano_name: str) -> str:
    # Slug ASCII simple (matchea los nombres del CATALOG sin tildes).
    safe = "".join(c if c.isalnum() else "_" for c in volcano_name.lower())
    return f"volcan__{safe}"


def asset_name(scope_id: str, product: str, ts: str) -> str:
    """Nombre de archivo PNG (legacy, dentro del ZIP es solo `{ts}.png`)."""
    # producto puede tener guiones y underscores -> dejar tal cual
    return f"{scope_id}__{product}__{ts}.png"


def zip_name(scope_id: str, product: str) -> str:
    """Nombre del ZIP en el release que agrupa TODOS los frames de un
    (scope, producto). Pasamos de ~2800 PNGs sueltos a ~39 ZIPs porque
    GitHub limita 1000 assets por release. Dentro del ZIP cada frame es
    `{ts}.png`."""
    return f"{scope_id}__{product}.zip"


# ── Lectura del manifest ──────────────────────────────────────────────────

# Session HTTP compartida — definicion en src/fetch/_http_session
from src.fetch._http_session import get_session as _get_session



def fetch_manifest() -> dict | None:
    """Descargar `manifest.json` del release. Devuelve None si no existe.

    Estructura esperada:
      {
        "updated_utc": "20260501T140000Z",
        "scopes": {
          "nacional": {
            "geocolor": ["20260501013000", "20260501014000", ...],
            "eumetsat_ash": [...],
            ...
          },
          "zona__sur": {...},
          "volcan__villarrica": {...},
          ...
        }
      }
    """
    try:
        # Cache-buster: el asset no cambia de URL pero el contenido si.
        import time as _t
        url = f"{MANIFEST_URL}?_={int(_t.time())}"
        r = _get_session().get(url, timeout=TIMEOUT)
        if r.status_code == 404:
            logger.info("manifest no encontrado en release (probablemente cron no corrio aun)")
            return None
        r.raise_for_status()
        return r.json()
    except Exception as e:
        logger.warning("error leyendo manifest: %s", e)
        return None


# ── Descarga de frames cacheados (desde el ZIP del scope/producto) ─────────

# Cache de modulo del ZIP descargado (bytes), con TTL. Evita re-bajar el ZIP
# completo (~3-7 MB) en cada rerun de Streamlit. El contenido del release
# cambia cada hora (cron), por eso TTL corto.
import time as _time

_zip_cache: dict[tuple[str, str], tuple[float, bytes]] = {}
_ZIP_TTL = 600  # 10 min


def _download_zip_bytes(scope_id: str, product: str) -> bytes | None:
    """Baja (o reusa de cache) el ZIP del (scope, producto) del release."""
    key = (scope_id, product)
    now = _time.time()
    hit = _zip_cache.get(key)
    if hit is not None and now - hit[0] < _ZIP_TTL:
        return hit[1]
    url = f"{CDN_BASE}/{zip_name(scope_id, product)}"
    try:
        r = _get_session().get(url, timeout=TIMEOUT * 3)
        if r.status_code != 200:
            return None
        _zip_cache[key] = (now, r.content)
        return r.content
    except Exception as e:
        logger.debug("fallo bajar zip %s: %s", url, e)
        return None


def fetch_cached_frames(
    scope_id: str,
    product: str,
    timestamps: list[str],
    max_workers: int = 8,  # ignorado ahora (1 ZIP en vez de N PNGs)
) -> dict[str, np.ndarray]:
    """Devolver los frames cacheados para los timestamps dados.

    Baja el ZIP del (scope, producto) una sola vez y extrae de el los
    frames pedidos. Devuelve dict ts -> array; los que no estan no aparecen.
    """
    import zipfile

    out: dict[str, np.ndarray] = {}
    if not timestamps:
        return out
    data = _download_zip_bytes(scope_id, product)
    if data is None:
        return out
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            names = set(zf.namelist())
            for ts in timestamps:
                fn = f"{ts}.png"
                if fn in names:
                    img = Image.open(io.BytesIO(zf.read(fn))).convert("RGB")
                    out[ts] = np.array(img)
    except Exception as e:
        logger.warning("error leyendo zip %s/%s: %s", scope_id, product, e)
    return out


def cache_status(scope_id: str, product: str) -> dict:
    """Resumen del cache para mostrar en UI: cuantos frames, cuan viejo el ultimo build.

    Devuelve {"available": bool, "n_frames": int, "updated_utc": str|None,
              "latest_ts": str|None}.
    """
    manifest = fetch_manifest()
    if manifest is None:
        return {"available": False, "n_frames": 0, "updated_utc": None,
                "latest_ts": None}
    scopes = manifest.get("scopes", {})
    ts_list = scopes.get(scope_id, {}).get(product, [])
    return {
        "available": bool(ts_list),
        "n_frames": len(ts_list),
        "updated_utc": manifest.get("updated_utc"),
        "latest_ts": ts_list[-1] if ts_list else None,
    }
