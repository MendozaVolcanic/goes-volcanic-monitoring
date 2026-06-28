"""Altura del tope de pluma volcánica — producto propio **INDICATIVO**.

Idea (Fase 0 del "VOLCAT propio", ver ``docs/own_volcat/FASE0_ARRANQUE.md``):

    altura del tope de pluma  ≈  HT(ACHA NOAA)  ∩  máscara de ceniza propia

ACHA (``ABI-L2-ACHA2KMF``) da la altura del tope de **cualquier** nube. Nuestra
detección tri-espectral (``detect_ash_enhanced``: BTD split-window 11–12 µm +
test tri-espectral con 8.4 µm) marca dónde hay **firma de ceniza**. La
intersección da la altura del tope donde hay ceniza → el **tope de la pluma**.

Por qué es INDICATIVO y no VOLCAT:
- ACHA es retrieval de nube genérica (Heidinger OE), no afinado a la microfísica
  de la ceniza. En plumas semi-transparentes o con nube meteo debajo subestima,
  igual que cualquier matching IR. El número cuantitativo "VAAC-grade" sigue
  siendo el VOLCAT de SSEC (Pavolonis 2013). Esto lo complementa con MENOR
  latencia (~13 min vs 30–50) y de forma independiente del host SSEC.
- Resolución térmica = 2 km nativa de ABI (igual que el VOLCAT regional). No da
  masa ni radio efectivo (eso es Fase ≥1, con C10/C16 + microfísica).

Clave de implementación: ``ABI-L2-ACHA2KMF`` y ``ABI-L1b-RadF`` 2 km comparten
la MISMA grilla geos (x/y idénticos, verificado). Recortamos ambos a la misma
ventana de índices que devuelve el fetcher ACHA → intersección pixel a pixel,
sin remuestrear.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional, Union

import numpy as np

logger = logging.getLogger(__name__)

# Bandas L1b para la máscara de ceniza tri-espectral:
#   C11 (8.4 µm), C14 (11.2 µm), C15 (12.3 µm). Todas 2 km nativas → misma
#   grilla que ACHA2KMF.
ASH_BANDS = (11, 14, 15)


def _plume_top_stats(
    height_m: np.ndarray,
    mask: np.ndarray,
    percentile: float = 95,
) -> dict:
    """Resumir el tope de la pluma sobre los píxeles de ceniza.

    Función PURA (sin red) — el corazón cuantitativo, testeable determinístico.

    Args:
        height_m:   campo de altura del tope (m), NaN donde no hay retrieval/DQF.
        mask:       booleano, True donde NUESTRA detección marcó ceniza.
        percentile: percentil del tope a reportar (default 95 — robusto a
                    outliers de un par de píxeles ruidosos vs el máximo crudo).

    Returns:
        dict con ``mask_px`` (nº de píxeles de ceniza con HT válida), ``top_km``
        (percentil, km), ``top_max_km`` (máximo, km) y ``field_km`` (HT en km,
        NaN salvo en píxeles de ceniza válidos — para mapear). Si no hay píxeles
        válidos: ``mask_px=0`` y topes ``None``.
    """
    mask = np.asarray(mask, dtype=bool)
    height_m = np.asarray(height_m, dtype="float64")
    # Alinear shapes defensivamente (la grilla es idéntica, pero un off-by-one
    # de un recorte no debe tirar el producto entero).
    if mask.shape != height_m.shape:
        h = min(mask.shape[0], height_m.shape[0])
        w = min(mask.shape[1], height_m.shape[1])
        mask = mask[:h, :w]
        height_m = height_m[:h, :w]
        logger.warning("ACHA/máscara con shapes distintos; recortado a %s", (h, w))

    valid = mask & np.isfinite(height_m)
    field_km = np.where(valid, height_m / 1000.0, np.nan)
    n = int(valid.sum())
    if n == 0:
        return {"mask_px": 0, "top_km": None, "top_max_km": None,
                "field_km": field_km}

    vals_km = height_m[valid] / 1000.0
    return {
        "mask_px": n,
        "top_km": float(np.percentile(vals_km, percentile)),
        "top_max_km": float(vals_km.max()),
        "field_km": field_km,
    }


def _bounds_for(volcano, radius_deg: float) -> dict:
    return {
        "lat_min": volcano.lat - radius_deg, "lat_max": volcano.lat + radius_deg,
        "lon_min": volcano.lon - radius_deg, "lon_max": volcano.lon + radius_deg,
    }


def plume_top_height(
    dt: datetime,
    volcano: Union[str, object],
    radius_deg: float = 0.75,
    keep_dqf=None,
    percentile: float = 95,
) -> dict:
    """Altura del tope de pluma INDICATIVA para un volcán en un instante.

    Pipeline:
      1. ``fetch_acha_height_at`` → HT recortado al bbox + ventana de índices.
      2. Bajar C11/C14/C15 del MISMO scan (``download_band_at``), recortar a la
         misma ventana y armar la máscara con ``detect_ash_enhanced``.
      3. Intersectar máscara ∩ HT y resumir el tope (``_plume_top_stats``).

    Args:
        dt:         datetime UTC objetivo (NRT: ``now``).
        volcano:    objeto Volcano o nombre (se resuelve en el CATALOG).
        radius_deg: medio-lado del bbox alrededor del volcán (default ±0.75°
                    ≈ ±83 km).
        keep_dqf:   conjunto DQF a conservar (default del fetcher: {0,1,4}).
        percentile: percentil del tope a reportar (default 95).

    Returns:
        dict con ``status`` ∈ {"ok","no_plume","no_data"} y, según el caso:
        ``top_km`` (p95, km AMSL), ``top_max_km``, ``mask_px``, ``field_km``,
        ``lat``/``lon`` (georef), ``bounds``, ``scan_dt``, ``latency_min``,
        ``source``, ``volcano``. ``no_plume`` = ACHA OK pero sin píxeles de
        ceniza en el encuadre; ``no_data`` = sin gránulo / banda / volcán.
    """
    # Imports perezosos — evita cadenas frágiles en hot-reload de Streamlit y
    # mantiene este módulo importable sin red (para los tests puros).
    from src.fetch.goes_acha import DQF_KEEP_DEFAULT, fetch_acha_height_at
    from src.fetch.goes_s3 import download_band_at, open_band
    from src.process.ash_detection import detect_ash_enhanced
    from src.process.brightness_temp import rad_to_bt

    if keep_dqf is None:
        keep_dqf = DQF_KEEP_DEFAULT

    if isinstance(volcano, str):
        from src.volcanos import get_volcano
        v = get_volcano(volcano)
    else:
        v = volcano
    if v is None:
        return {"status": "no_data", "reason": "volcán no encontrado",
                "volcano": str(volcano)}

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    bounds = _bounds_for(v, radius_deg)
    source = ("ACHA NOAA (ABI-L2-ACHA2KMF) enmascarado por detección de ceniza "
              "tri-espectral · INDICATIVO, no es VOLCAT")

    acha = fetch_acha_height_at(dt, bounds, keep_dqf=keep_dqf)
    if acha is None:
        return {"status": "no_data", "reason": "sin gránulo ACHA accesible",
                "volcano": v.name, "bounds": bounds, "source": source}

    from src.fetch.goes_s3 import _scan_start

    y0, y1, x0, x1 = acha["window"]
    height_m = acha["height_m"]
    acha_dt = acha["scan_dt"]
    # Sin timestamp del gránulo ACHA no podemos garantizar que las bandas caigan
    # en el MISMO scan → mejor no reportar que reportar desalineado.
    if acha_dt is None:
        return {"status": "no_data",
                "reason": "no pude datar el gránulo ACHA (alineación de bandas "
                          "no garantizada)",
                "volcano": v.name, "bounds": bounds, "source": source}
    ref_dt = acha_dt   # alinear las bandas al MISMO scan que ACHA

    # ── Máscara de ceniza en la misma ventana (grilla idéntica) ──────────
    bts = {}
    band_scans = {}
    for b in ASH_BANDS:
        path = download_band_at(ref_dt, b)
        if path is None:
            return {"status": "no_data", "reason": f"sin banda C{b:02d}",
                    "volcano": v.name, "bounds": bounds, "scan_dt": acha_dt,
                    "source": source}
        band_scans[b] = _scan_start(path.name)
        try:
            # context manager → cierra el handle HDF5; .load() materializa la BT
            # antes de cerrar el dataset.
            with open_band(path) as ds:
                ds_win = ds.isel(y=slice(y0, y1), x=slice(x0, x1))
                bts[b] = rad_to_bt(ds_win).load()
        except Exception as e:
            logger.exception("Error BT banda C%02d: %s", b, e)
            return {"status": "no_data", "reason": f"error procesando C{b:02d}",
                    "volcano": v.name, "bounds": bounds, "scan_dt": acha_dt,
                    "source": source}

    # Las 3 bandas deben ser del MISMO scan; si S3 tenía un hueco y alguna cayó
    # en un scan vecino (±10 min), la máscara mezclaría tiempos → degradar a
    # no_data en vez de un misregistro silencioso. (review jun 2026)
    scans = {s for s in band_scans.values() if s is not None}
    if len(scans) > 1:
        logger.warning("Bandas de ceniza de scans distintos: %s", band_scans)
        return {"status": "no_data",
                "reason": "bandas C11/C14/C15 de scans distintos (S3 incompleto)",
                "volcano": v.name, "bounds": bounds, "scan_dt": acha_dt,
                "source": source}

    mask = detect_ash_enhanced(bts[11], bts[14], bts[15]).values
    stats = _plume_top_stats(height_m, mask, percentile=percentile)

    now = datetime.now(timezone.utc)
    latency_min = (now - acha_dt).total_seconds() / 60.0 if acha_dt else None

    out = {
        "volcano": v.name,
        "bounds": bounds,
        "lat": acha["lat"],
        "lon": acha["lon"],
        "scan_dt": acha_dt,
        "latency_min": latency_min,
        "percentile": percentile,
        "source": source,
        "product": acha["product"],
        **stats,
    }
    out["status"] = "ok" if stats["mask_px"] > 0 else "no_plume"
    return out
