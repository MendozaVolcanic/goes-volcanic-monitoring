"""Pipeline hi-res NOAA: descarga bandas L1b -> recorte por scope -> RGB.

Genera composites a 0.5 km/px (4× mejor que RAMMB zoom 4 = 1.7 km/px).

Uso:
    result = build_hires_for_scopes(
        dt=datetime(2026, 5, 9, 18, 0, tzinfo=timezone.utc),
        scopes={"villarrica": {"lat": -39.42, "lon": -71.93}, ...},
        radius_deg=0.5,
    )
    # result["villarrica"] = numpy (H, W, 3) uint8 listo para guardar/mostrar

Decisiones clave:
- Todas las bandas se descargan UNA vez por scan (~330 MB total). Despues
  recortamos por scope sin re-descargar.
- Banda 2 (0.5 km/px) se downsamplea 2x para alinear con bandas 1/3
  (1 km/px). Pierdo el factor 2 ahi pero el RGB queda balanceado en 1 km/px.
  Si quiero los 0.5 km/px reales, uso solo banda 2 como grayscale (Phase 2).
- De noche (sun < 5°) genero pseudo-color desde banda 13 IR.

Performance esperado en runner GH:
- Descarga 4 bandas: ~30s (S3 NOAA paralelo)
- Procesar bandas (BT/refl, lat/lon una vez): ~10s
- Recorte + RGB para 8 scopes: ~10s
- Total: ~50-60s por scan.
"""

from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

import numpy as np
import xarray as xr

from src.fetch.goes_s3 import download_band, open_band
from src.process.brightness_temp import rad_to_bt
from src.process.geo import crop_to_bounds, get_lat_lon
from src.process.geocolor_lite import (
    band2_monochrome_05km, bt_to_pseudo_color_ir, rad_to_reflectance,
    solar_elevation, true_color_rgb,
)

logger = logging.getLogger(__name__)

# Constantes fisicas canonical desde src/config (con try/except fallback,
# mismo patron que MOSAICO_RADIUS_DEG en dashboard/views/).
try:
    from src.config import GOES19_SAT_LON as _SAT_LON_DEFAULT
    from src.config import GOES19_PERSPECTIVE_POINT_HEIGHT as _H_DEFAULT
except Exception:
    _SAT_LON_DEFAULT = -75.0
    _H_DEFAULT = 35786023.0

# Bandas a descargar:
#   1 = azul visible 0.47um, 1km/px
#   2 = rojo visible 0.64um, 0.5km/px (la "hi-res" que da el x4)
#   3 = NIR vegetacion 0.86um, 1km/px
#   13 = clean IR window 10.3um, 2km/px (night fallback)
BANDS_HIRES = [1, 2, 3, 13]

# Umbral solar elevation para day/night switch
DAY_NIGHT_THRESHOLD_DEG = 5.0


def _downsample_2x(arr: np.ndarray) -> np.ndarray:
    """Downsample 2x usando block_reduce mean (anti-aliasing decente)."""
    h, w = arr.shape[:2]
    h2, w2 = h // 2, w // 2
    if arr.ndim == 2:
        return arr[:h2 * 2, :w2 * 2].reshape(h2, 2, w2, 2).mean(axis=(1, 3))
    else:
        return arr[:h2 * 2, :w2 * 2].reshape(h2, 2, w2, 2, -1).mean(axis=(1, 3))


def _scope_pixel_bounds(ds: "xr.Dataset", lat_c: float, lon_c: float,
                        radius_deg: float, sat_lon: float = _SAT_LON_DEFAULT
                        ) -> tuple[int, int, int, int] | None:
    """Devolver (r0, r1, c0, c1) en pixels del Dataset para cubrir el bbox.

    Sin allocar grids 2D. Usa solo los arrays 1D x/y del dataset (87 KB c/u
    vs 940 MB de un meshgrid full de 21696×21696). Critico para mono_05km
    en runner GH free que solo tiene 7 GB RAM.
    """
    try:
        from pyproj import Proj
    except ImportError:
        return None

    h = float(ds["goes_imager_projection"].attrs.get(
        "perspective_point_height", _H_DEFAULT))
    p = Proj(proj="geos", lon_0=sat_lon, h=h, ellps="GRS80", sweep="x")

    x_arr = ds["x"].values  # 1D, ~21696 elementos
    y_arr = ds["y"].values  # 1D, idem

    cols, rows = [], []
    # Probar 9 puntos (4 esquinas + 4 medios + centro) para asegurar cobertura
    test_pts = []
    for dlat in (-radius_deg, 0, radius_deg):
        for dlon in (-radius_deg, 0, radius_deg):
            test_pts.append((lat_c + dlat, lon_c + dlon))
    for lat, lon in test_pts:
        try:
            x_m, y_m = p(lon, lat)
        except Exception:
            continue
        if not (np.isfinite(x_m) and np.isfinite(y_m)):
            continue
        x_rad = x_m / h
        y_rad = y_m / h
        # argmin |array - target| funciona en arrays ascendentes o descendentes
        col = int(np.argmin(np.abs(x_arr - x_rad)))
        row = int(np.argmin(np.abs(y_arr - y_rad)))
        cols.append(col)
        rows.append(row)

    if not rows:
        return None

    # Margen de 5 pixels para no perder bordes
    margin = 5
    return (max(0, min(rows) - margin),
            min(len(y_arr), max(rows) + margin + 1),
            max(0, min(cols) - margin),
            min(len(x_arr), max(cols) + margin + 1))


def _download_bands_parallel(dt: datetime, bands: list[int]) -> dict[int, str]:
    """Bajar todas las bandas en paralelo. Devuelve dict band -> path."""
    out = {}
    def _one(b):
        p = download_band(dt, b)
        return b, p

    with ThreadPoolExecutor(max_workers=4) as ex:
        for b, p in ex.map(_one, bands):
            if p is not None:
                out[b] = str(p)
            else:
                logger.warning("Band %d no descargado", b)
    return out


def build_hires_for_scopes(
    dt: datetime,
    scopes: dict[str, dict],
    radius_deg: float = 0.5,
    mode: str = "color",
) -> tuple[dict[str, np.ndarray | None], dict[str, dict]]:
    """Genera RGB hi-res para cada scope a partir del mismo scan L1b.

    Args:
        dt:           datetime UTC del scan deseado (NOAA elige el mas cercano).
        scopes:       dict scope_id -> {"lat": float, "lon": float}.
                      Por scope generamos un bbox cuadrado de ±radius_deg.
        radius_deg:   medio-tamanio del bbox en grados (default 0.5° ≈ 55 km).
        mode:         "color" (default): TrueColor 1km/px diurno + IR nocturno.
                      "mono_05km": SOLO banda 2 a 0.5 km/px (4× zoom real).
                                   No baja b1 ni b3. Diurno solamente.

    Returns:
        Tupla `(images, meta)`:
          - `images`: dict scope_id -> numpy (H,W,3) uint8 RGB (None si fallo)
          - `meta`:   dict scope_id -> {"sun_alt": float (deg),
                                         "render": str}
            donde render ∈ {"visible_color", "visible_mono", "ir_pseudo",
                           "skip_night", "no_data", "error"}.
    """
    # 1. Descargar bandas. En mono_05km solo necesitamos banda 2 (visible
    # rojo 0.5km/px) — ahorra ~130 MB de download skipping b1+b3.
    bands_to_download = [2] if mode == "mono_05km" else BANDS_HIRES
    logger.info("Descargando bandas %s para %s (mode=%s)...",
                bands_to_download, dt.strftime("%Y-%m-%d %H:%M UTC"), mode)
    band_paths = _download_bands_parallel(dt, bands_to_download)
    if 2 not in band_paths:
        logger.error("Banda 2 indispensable no disponible")
        return {sid: None for sid in scopes}

    # 2. Abrir y procesar bandas (radiance -> refl/BT).
    # En mono_05km NO preload banda 2 (es 21696x21696 = 1.9 GB float32).
    # Vamos a calcular el super-bbox que cubre todos los scopes y slice
    # ANTES de allocar reflectance. Eso evita OOM en runner GH free (7 GB).
    datasets: dict[int, xr.Dataset] = {}
    refls: dict[int, np.ndarray] = {}
    bts: dict[int, np.ndarray] = {}

    for b, p in band_paths.items():
        ds = open_band(p)
        datasets[b] = ds
        if mode == "mono_05km" and b == 2:
            # Skip preload — vamos a procesar sub-region solamente
            continue
        if b in (1, 2, 3):
            refls[b] = rad_to_reflectance(ds["Rad"], ds)
        elif b == 13:
            bts[b] = rad_to_bt(ds).values

    # 3. Geolocalizacion.
    # mode='mono_05km': lat/lon SOLO del super-bbox que cubre todos los scopes
    #                   (~5000×1300 px = ~25 MB vs 21696×21696 = 7 GB).
    # mode='color':     trabajamos en 1 km/px full grid. Banda 2 downsample 2x.
    if mode == "mono_05km":
        # Precompute pixel bounds de cada scope -> super-bbox
        all_bounds = []
        for sid, sinfo in scopes.items():
            pb = _scope_pixel_bounds(
                datasets[2], sinfo["lat"], sinfo["lon"], radius_deg,
            )
            if pb is not None:
                all_bounds.append(pb)
        if not all_bounds:
            logger.error("mono_05km: no pude calcular pixel bounds de ningun scope")
            for ds in datasets.values():
                ds.close()
            return {sid: None for sid in scopes}, {sid: {"render": "error", "sun_alt": None} for sid in scopes}
        super_r0 = min(b[0] for b in all_bounds)
        super_r1 = max(b[1] for b in all_bounds)
        super_c0 = min(b[2] for b in all_bounds)
        super_c1 = max(b[3] for b in all_bounds)
        logger.info("mono_05km super-bbox: rows[%d:%d] cols[%d:%d] = %d x %d px",
                    super_r0, super_r1, super_c0, super_c1,
                    super_r1 - super_r0, super_c1 - super_c0)
        # Slice + compute reflectance + lat/lon SOLO para sub-region
        ds_super = datasets[2].isel(y=slice(super_r0, super_r1),
                                     x=slice(super_c0, super_c1))
        refls[2] = rad_to_reflectance(ds_super["Rad"], ds_super)
        lat, lon = get_lat_lon(ds_super)
        ds_super.close()
    else:
        if 2 in refls:
            refls[2] = _downsample_2x(refls[2])
        ref_band = 1 if 1 in datasets else 2
        lat, lon = get_lat_lon(datasets[ref_band])

    # 4. Para banda 13 (2 km/px), upscale 2x via repeat para alinear a 1 km/px.
    # No aplica en mono_05km (no descargamos banda 13).
    bt13 = None
    if mode == "color" and 13 in bts:
        bt13_2km = bts[13]
        bt13 = np.repeat(np.repeat(bt13_2km, 2, axis=0), 2, axis=1)
        bt13 = bt13[:lat.shape[0], :lat.shape[1]]

    # 5. Por cada scope: decidir day/night + recortar + RGB.
    # `out_meta` registra qué modo se usó por scope (visible/IR) + sun_alt
    # para que el dashboard pueda mostrar al usuario QUÉ está viendo.
    out: dict[str, np.ndarray | None] = {}
    out_meta: dict[str, dict] = {}
    for sid, scope_info in scopes.items():
        lat_c = scope_info["lat"]
        lon_c = scope_info["lon"]
        bounds = {
            "lat_min": lat_c - radius_deg, "lat_max": lat_c + radius_deg,
            "lon_min": lon_c - radius_deg, "lon_max": lon_c + radius_deg,
        }
        sun_alt = solar_elevation(lat_c, lon_c, dt)
        is_day = sun_alt >= DAY_NIGHT_THRESHOLD_DEG

        out_meta[sid] = {"sun_alt": round(sun_alt, 1), "render": None}
        try:
            if mode == "mono_05km":
                # Modo 0.5 km/px: solo banda 2 monocromatica.
                # Solo tiene sentido de dia (visible necesita sol).
                if not is_day:
                    logger.info("[%s] mono_05km NOCHE (sun=%.1f°) -> skip",
                                sid, sun_alt)
                    out[sid] = None
                    out_meta[sid]["render"] = "skip_night"
                    continue
                b2_crop, _, _ = crop_to_bounds(
                    xr.DataArray(refls[2], dims=["y", "x"]), lat, lon, bounds)
                if b2_crop.size == 0:
                    out[sid] = None
                    out_meta[sid]["render"] = "no_data"
                    continue
                rgb = band2_monochrome_05km(b2_crop)
                out_meta[sid]["render"] = "visible_mono"
                logger.info("[%s] mono_05km DIA sun=%.1f° -> %s (0.5km/px)",
                            sid, sun_alt, rgb.shape)
            elif is_day and all(b in refls for b in (1, 2, 3)):
                # TrueColor diurno (1 km/px)
                b1_crop, _, _ = crop_to_bounds(
                    xr.DataArray(refls[1], dims=["y", "x"]), lat, lon, bounds)
                b2_crop, _, _ = crop_to_bounds(
                    xr.DataArray(refls[2], dims=["y", "x"]), lat, lon, bounds)
                b3_crop, _, _ = crop_to_bounds(
                    xr.DataArray(refls[3], dims=["y", "x"]), lat, lon, bounds)
                if b2_crop.size == 0:
                    out[sid] = None
                    out_meta[sid]["render"] = "no_data"
                    continue
                rgb = true_color_rgb(b1_crop, b2_crop, b3_crop)
                out_meta[sid]["render"] = "visible_color"
                logger.info("[%s] DIA sun=%.1f° -> TrueColor %s",
                            sid, sun_alt, rgb.shape)
            elif bt13 is not None:
                # Night IR pseudo-color
                bt_crop, _, _ = crop_to_bounds(
                    xr.DataArray(bt13, dims=["y", "x"]), lat, lon, bounds)
                if bt_crop.size == 0:
                    out[sid] = None
                    out_meta[sid]["render"] = "no_data"
                    continue
                rgb = bt_to_pseudo_color_ir(bt_crop)
                out_meta[sid]["render"] = "ir_pseudo"
                logger.info("[%s] NOCHE sun=%.1f° -> IR pseudo-color %s",
                            sid, sun_alt, rgb.shape)
            else:
                logger.warning("[%s] sin datos visible NI IR -> None", sid)
                out[sid] = None
                out_meta[sid]["render"] = "no_data"
                continue
            out[sid] = rgb
        except Exception as e:
            logger.exception("[%s] error: %s", sid, e)
            out[sid] = None
            out_meta[sid]["render"] = "error"

    # Cerrar datasets
    for ds in datasets.values():
        ds.close()
    # Devolver tupla (imagenes, metadata por scope) para que el caller
    # registre QUE TIPO de render salio (visible vs IR) y muestre al user.
    return out, out_meta
