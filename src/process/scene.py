# ════════════════════════════════════════════════════════════════════
# FICHA SDA · scene.py  ·  SDA: Monitoreo Volcánico GOES-19 · ID: SDA-GOES-01
# Objetivo      : adquirir UNA escena de ceniza (bandas + máscara + contexto) para los 3 retrievals de altura
# Lógica        : baja las bandas IR del MISMO scan, recorta al entorno del volcán y marca dónde hay firma de ceniza
# Modelo/método : reglas determinísticas: ventana geos + guard de mismo-scan + detección tri-espectral
# Datos entrada : ABI-L1b C11/C14/C15 (GOES-19) + perfil GFS (Open-Meteo) — SIN datos personales
# Variables     : bandas requeridas, radio del encuadre, umbral SO₂ de contexto
# Limitaciones  : si S3 tiene un hueco y las bandas caen en scans distintos NO se reporta (mejor nada que misregistro)
# Refs/datos    : guard de mismo-scan (review jun-2026); unificación de los 3 preámbulos (audit ago-2026, ola 2)
# Ficha completa: docs/FICHA_SDA_GOES.md
# ════════════════════════════════════════════════════════════════════
"""Adquisición común de la **escena de ceniza** para los retrievals de altura.

Por qué existe (el "por qué" antes que el "cómo"): los tres métodos propios de
altura de tope —BT-matching (Fase 3a), Wen-Rose (Fase 3b) y el cruce con ACHA
(Fase 0)— parten **exactamente del mismo dato**: las bandas IR del mismo scan,
recortadas al entorno del volcán, con la máscara de ceniza tri-espectral y el
contexto de SO₂. Lo que cambia entre ellos es la *física posterior*, no la
adquisición.

Hasta el audit ago-2026 ese preámbulo estaba escrito **tres veces**. Eso no es
solo repetición: los **guards de honestidad** viven ahí (mismo-scan, bbox fuera
del disco, banda faltante). Un fix a un guard había que aplicarlo tres veces o
quedaba inconsistente — ya pasó con el guard de mismo-scan en jun-2026, que
nació en ACHA y hubo que replicar a mano en los otros dos. Con la escena
unificada el guard vive en UN lugar y se testea una sola vez.

Uso::

    scene = acquire_ash_scene(dt, "Lascar", radius_deg=0.75, source=SOURCE)
    if isinstance(scene, dict):      # error → dict listo para devolver
        return scene
    bt14 = scene.bts[14]             # numpy 2D, ya recortado

El caso de ACHA es distinto: la ventana la fija el gránulo L2 (grilla idéntica),
así que se pasa ``window=``/``ref_dt=``/``latlon=`` y la escena no baja la banda
ancla para derivarla.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, Sequence, Union

import numpy as np

logger = logging.getLogger(__name__)

# Bandas IR de la máscara tri-espectral: C11 (8.4 µm), C14 (11.2 µm, ventana),
# C15 (12.3 µm). Las tres son 2 km nativas → misma grilla que ACHA2KMF.
ASH_BANDS = (11, 14, 15)
ANCHOR_BAND = 14           # de su grilla salen la ventana geos y la georef

# Umbral del indicador SO₂ (BT 8.4 − BT 11.2). Fallback si src.config no carga.
_SO2_THR_FALLBACK = -3.0


def bounds_for(volcano, radius_deg: float) -> dict:
    """Bbox cuadrado (en grados) centrado en el volcán. PURA."""
    return {"lat_min": volcano.lat - radius_deg,
            "lat_max": volcano.lat + radius_deg,
            "lon_min": volcano.lon - radius_deg,
            "lon_max": volcano.lon + radius_deg}


def planck_coefs(ds) -> tuple:
    """Coeficientes Planck (fk1, fk2, bc1, bc2) del NetCDF L1b — **nunca**
    hardcodeados: son por banda y por satélite. PURA."""
    return (float(ds["planck_fk1"].values), float(ds["planck_fk2"].values),
            float(ds["planck_bc1"].values), float(ds["planck_bc2"].values))


def resolve_volcano(volcano: Union[str, object]):
    """Nombre → objeto Volcano del catálogo; un objeto pasa derecho. None si no
    existe (short-circuit ANTES de tocar la red)."""
    if isinstance(volcano, str):
        from src.volcanos import get_volcano
        return get_volcano(volcano)
    return volcano


def so2_context(bt85: np.ndarray, bt11: np.ndarray) -> tuple[int, Optional[float]]:
    """Contexto SO₂ = BT(8.4 µm) − BT(11.2 µm); muy negativo ⇒ SO₂.

    No es una altura: sirve para que el dashboard **explique** un ``no_plume``
    (pluma de gas sin ceniza silicatada, caso típico en Chile — Chillán 27-jun)
    en vez de quedarse mudo. Devuelve (píxeles bajo el umbral, mínimo). PURA.
    """
    try:
        from src.config import SO2_INDICATOR_THRESHOLD as thr
    except Exception:
        thr = _SO2_THR_FALLBACK
    so2 = np.asarray(bt85) - np.asarray(bt11)
    finite = np.isfinite(so2)
    n = int(np.sum(finite & (so2 < thr)))
    lo = float(np.nanmin(so2)) if finite.any() else None
    return n, lo


@dataclass
class AshScene:
    """Escena de ceniza lista para el retrieval: bandas recortadas al mismo
    scan, máscara, georef y (opcional) perfil GFS."""

    volcano: object
    bounds: dict
    window: tuple                       # (y0, y1, x0, x1) en índices geos
    bts: dict                           # banda → BT (numpy 2D, K)
    mask: np.ndarray                    # True donde hay firma de ceniza
    lat: np.ndarray
    lon: np.ndarray
    scan_dt: Optional[datetime]
    latency_min: Optional[float]
    so2_px: int
    so2_min: Optional[float]
    coefs: dict = field(default_factory=dict)     # banda → (fk1, fk2, bc1, bc2)
    profile: Optional[dict] = None                # perfil GFS T(z)
    sat_lon: Optional[float] = None
    perspective_h: Optional[float] = None
    ref_dt: Optional[datetime] = None             # scan de referencia usado

    @property
    def name(self) -> str:
        return self.volcano.name

    def base_out(self, percentile: float, source: str) -> dict:
        """Campos comunes del dict de salida de los tres retrievals."""
        trop = (self.profile or {}).get("tropopause")
        out = {
            "volcano": self.name, "bounds": self.bounds,
            "lat": self.lat, "lon": self.lon,
            "scan_dt": self.scan_dt, "latency_min": self.latency_min,
            "percentile": percentile, "source": source,
            "so2_px": self.so2_px, "so2_min": self.so2_min,
        }
        if self.profile is not None:
            out["tropopause_km"] = trop["z_m"] / 1000.0 if trop else None
            out["profile_time"] = self.profile.get("valid_time")
            # QUÉ: minutos entre la hora del perfil GFS y el scan GOES.
            # POR QUÉ: el mapeo BT→altitud SÓLO vale si el T(z) es el de ese
            # momento. Open-Meteo da el perfil horario más cercano y puede quedar
            # a horas de distancia (dt fuera de la ventana past_days/forecast_days,
            # o un hueco del modelo): con un perfil viejo la MISMA BT se traduce a
            # otra altitud. El fetcher ya lo mide (gfs_profile.py, gap_min) y sólo
            # lo logueaba; acá lo hacemos viajar hasta la pantalla para que el
            # turno sepa si el número descansa en un perfil de hace 20 min o de
            # hace 5 h. Informativo: NO degrada la confianza ni mueve el tope.
            # None si el proveedor no lo reporta (contrato aún desparejo entre
            # fetch_gfs_profile y fetch_gfs_wind_profile).
            out["profile_gap_min"] = self.profile.get("time_gap_min")
        return out


def _err(reason: str, *, source: str, volcano=None, bounds=None,
         scan_dt=None, **extra) -> dict:
    out = {"status": "no_data", "reason": reason, "source": source}
    if volcano is not None:
        out["volcano"] = volcano
    if bounds is not None:
        out["bounds"] = bounds
    if scan_dt is not None:
        out["scan_dt"] = scan_dt
    out.update(extra)
    return out


def acquire_ash_scene(
    dt: datetime,
    volcano: Union[str, object],
    radius_deg: float = 0.75,
    *,
    bands: Sequence[int] = ASH_BANDS,
    with_coefs: bool = False,
    with_profile: bool = True,
    source: str = "",
    label: str = "escena",
    window: Optional[tuple] = None,
    ref_dt: Optional[datetime] = None,
    latlon: Optional[tuple] = None,
    bounds: Optional[dict] = None,
) -> Union[AshScene, dict]:
    """Bajar y preparar la escena de ceniza para un volcán en un instante.

    Pipeline: resolver volcán → ventana geos desde la banda ancla (o la que
    imponga el caller) → bajar el resto de las bandas del **mismo scan** →
    guard de mismo-scan → máscara tri-espectral → contexto SO₂ → perfil GFS.

    Args:
        dt:           instante objetivo (UTC; naive se asume UTC).
        volcano:      nombre del catálogo u objeto Volcano.
        radius_deg:   medio-lado del bbox (default ±0.75° ≈ ±83 km).
        bands:        bandas a bajar (default C11/C14/C15).
        with_coefs:   además de la BT, guardar los coeficientes Planck de cada
                      banda (los necesita Wen-Rose para mezclar radiancias).
        with_profile: bajar el perfil GFS T(z) en el volcán.
        source:       string de procedencia, se copia en los dicts de error.
        label:        prefijo de los logs (nombre del retrieval que llama).
        window:       (y0, y1, x0, x1) impuesta por el caller (ACHA). Si se pasa,
                      NO se baja la banda ancla para derivarla y hay que pasar
                      también ``ref_dt`` y ``latlon``.
        ref_dt:       scan de referencia al que alinear las bandas.
        latlon:       (lat2d, lon2d) de la ventana, si el caller ya los tiene.
        bounds:       bbox explícito (default: el del volcán con ``radius_deg``).

    Returns:
        ``AshScene`` si todo salió bien, o un ``dict`` con ``status="no_data"``
        y ``reason`` listo para devolver al dashboard.
    """
    # Imports perezosos: evitan cadenas frágiles en el hot-reload de Streamlit y
    # dejan este módulo importable sin red (tests puros). También son el punto
    # que monkeypatchean los tests de orquestación.
    from src.config import (GOES19_PERSPECTIVE_POINT_HEIGHT as _H,
                            GOES19_SAT_LON as _SLON)
    from src.fetch.goes_acha import _geos_index_bbox, _window_latlon
    from src.fetch.goes_s3 import _scan_start, download_band_at, open_band
    from src.process.ash_detection import detect_ash_enhanced
    from src.process.brightness_temp import rad_to_bt

    v = resolve_volcano(volcano)
    if v is None:
        return _err("volcán no encontrado", source=source, volcano=str(volcano))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    if bounds is None:
        bounds = bounds_for(v, radius_deg)

    bts: dict = {}
    coefs: dict = {}
    band_scans: dict = {}
    sat_lon = perspective_h = None
    xw = yw = None

    # ── Ventana geos ─────────────────────────────────────────────────────
    # Sale de la grilla de la banda ancla, salvo que el caller la imponga
    # (ACHA: el gránulo L2 comparte la MISMA grilla, no hay que remuestrear).
    if window is None:
        anchor = bands[0] if ANCHOR_BAND not in bands else ANCHOR_BAND
        p_anchor = download_band_at(dt, anchor)
        if p_anchor is None:
            return _err(f"sin banda C{anchor:02d}", source=source,
                        volcano=v.name, bounds=bounds)
        try:
            with open_band(p_anchor) as ds:
                x = ds["x"].values
                y = ds["y"].values
                proj = ds["goes_imager_projection"].attrs
                sat_lon = float(proj.get("longitude_of_projection_origin", _SLON))
                perspective_h = float(proj.get("perspective_point_height", _H))
                win = _geos_index_bbox(x, y, bounds, sat_lon=sat_lon,
                                       H=perspective_h)
                if win is None:
                    return _err("bbox fuera del disco", source=source,
                                volcano=v.name, bounds=bounds)
                y0, y1, x0, x1 = win
                if with_coefs:
                    coefs[anchor] = planck_coefs(ds)
                bts[anchor] = rad_to_bt(
                    ds.isel(y=slice(y0, y1), x=slice(x0, x1))).load().values
                xw, yw = x[x0:x1], y[y0:y1]
        except Exception as e:
            logger.exception("%s C%02d: %s", label, anchor, e)
            return _err(f"error leyendo C{anchor:02d}", source=source,
                        volcano=v.name, bounds=bounds)
        scan_dt = _scan_start(p_anchor.name)
        band_scans[anchor] = scan_dt
        ref = ref_dt or scan_dt or dt
    else:
        y0, y1, x0, x1 = window
        scan_dt = ref_dt
        ref = ref_dt or dt

    # ── Resto de las bandas, alineadas al MISMO scan ──────────────────────
    for b in bands:
        if b in bts:
            continue
        pb = download_band_at(ref, b)
        if pb is None:
            return _err(f"sin banda C{b:02d}", source=source, volcano=v.name,
                        bounds=bounds, scan_dt=scan_dt)
        band_scans[b] = _scan_start(pb.name)
        try:
            with open_band(pb) as dsb:
                if with_coefs:
                    coefs[b] = planck_coefs(dsb)
                bts[b] = rad_to_bt(
                    dsb.isel(y=slice(y0, y1), x=slice(x0, x1))).load().values
        except Exception as e:
            logger.exception("%s C%02d: %s", label, b, e)
            return _err(f"error leyendo C{b:02d}", source=source, volcano=v.name,
                        bounds=bounds, scan_dt=scan_dt)

    # GUARD DE HONESTIDAD (review jun-2026, unificado ago-2026): las bandas
    # deben venir del MISMO scan. Si S3 tenía un hueco y alguna cayó en un scan
    # vecino (±10 min), la máscara mezclaría tiempos → un misregistro silencioso
    # que se vería como una pluma desplazada. Preferimos no reportar.
    scans = {s for s in band_scans.values() if s is not None}
    if len(scans) > 1:
        logger.warning("%s: bandas de scans distintos: %s", label, band_scans)
        return _err("bandas C11/C14/C15 de scans distintos (S3 incompleto)",
                    source=source, volcano=v.name, bounds=bounds,
                    scan_dt=scan_dt)

    # ── Georreferencia de la ventana ─────────────────────────────────────
    if latlon is not None:
        lat, lon = latlon
    else:
        lat, lon = _window_latlon(xw, yw, sat_lon=sat_lon, H=perspective_h)

    # ── Máscara de ceniza tri-espectral + contexto SO₂ ────────────────────
    import xarray as xr

    def _da(a):
        return xr.DataArray(np.asarray(a), dims=("y", "x"))

    mask = detect_ash_enhanced(_da(bts[11]), _da(bts[14]), _da(bts[15])).values
    so2_px, so2_min = so2_context(bts[11], bts[14])

    now = datetime.now(timezone.utc)
    latency_min = (now - scan_dt).total_seconds() / 60.0 if scan_dt else None

    scene = AshScene(
        volcano=v, bounds=bounds, window=(y0, y1, x0, x1), bts=bts, mask=mask,
        lat=lat, lon=lon, scan_dt=scan_dt, latency_min=latency_min,
        so2_px=so2_px, so2_min=so2_min, coefs=coefs, sat_lon=sat_lon,
        perspective_h=perspective_h, ref_dt=ref,
    )

    # ── Perfil GFS T(z) (insumo del mapeo BT→altitud) ────────────────────
    if with_profile:
        from src.fetch.gfs_profile import fetch_gfs_profile
        profile = fetch_gfs_profile(v.lat, v.lon, ref)
        if profile is None:
            # El SO₂ ya se midió: va en el error para que el dashboard pueda
            # explicar la escena aunque no haya perfil.
            return _err("sin perfil GFS (Open-Meteo)", source=source,
                        volcano=v.name, bounds=bounds, scan_dt=scan_dt,
                        so2_px=so2_px, so2_min=so2_min)
        scene.profile = profile

    return scene
